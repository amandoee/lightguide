import datetime
import time
from enum import Enum
import threading
import DatabaseController as DBC
from DBmodels import LogEntry, Settings
from Cep2Controller import MQTTController



#enum states
class States(Enum):
    IDLE = 1
    FORWARD = 2
    BACKWARD = 3
    FAILURE = 5
    UNACTIVE = 6

class roomType(Enum):
    GUESTROOM = 4
    BATHROOM = 2
    BEDROOM = 0
    LIVINGROOM = 3
    KITCHEN = 1

def getRoomType(roomstr : str):
    if (roomstr=="GUESTROOM"):
        return roomType.GUESTROOM
    if (roomstr=="BATHROOM"):
        return roomType.BATHROOM
    if (roomstr=="BEDROOM"):
        return roomType.BEDROOM
    if (roomstr=="LIVINGROOM"):
        return roomType.LIVINGROOM
    if (roomstr=="KITCHEN"):
        return roomType.KITCHEN



class room:
    typeroom: roomType
    forwardRoom: None
    backwardRoom: None

    def __init__(self,roomID) -> None:
        self.typeroom = roomID
        self.forwardRoom:room
        self.backwardRoom:room

class EventType(Enum):
    TIMEOUT_EVENT=0
    MOVEMENT=1
    FAILURE_EVENT=2
    BUTTON_PRESS=3
    INIT=4


class lightEvent:
    type : EventType
    place : room

    def __init__(self, type:EventType, place:room) -> None:
        self.type = type
        self.place = place

def initRooms():
    #hardcoded
    bedroom = room(roomType.BEDROOM)
    kitchen = room(roomType.KITCHEN)
    living_room = room(roomType.LIVINGROOM)
    guest_room = room(roomType.GUESTROOM)
    bathroom = room(roomType.BATHROOM)

    #Map
    bedroom.backwardRoom=bedroom
    
    bedroom.forwardRoom= living_room
    living_room.backwardRoom=bedroom
    
    living_room.forwardRoom=kitchen
    kitchen.backwardRoom=living_room
    
    
    #kitchen.forwardRoom=bathroom
    #bathroom.backwardRoom=kitchen
    
    #bathroom.forwardRoom=bathroom
    
    kitchen.forwardRoom=guest_room
    guest_room.backwardRoom=kitchen
    
    guest_room.forwardRoom=bathroom
    bathroom.backwardRoom=guest_room
    
    bathroom.forwardRoom=bathroom
    
    rooms = {roomType.BEDROOM:bedroom, roomType.KITCHEN:kitchen, roomType.BATHROOM:bathroom, roomType.LIVINGROOM:living_room,roomType.GUESTROOM:guest_room}

    return rooms


class EventHandler:

    rooms : dict
    state : States
    current_room : room
    timer : int
    lasttimerecorded : float
    model : DBC.DBController
    timeout : bool
    mqttController : MQTTController
    trackingTimer : float
    hasJustVisitedBathroom : bool
    
    STARTTIME = datetime.time(22,0,0)
    ENDTIME = datetime.time(9,0,0)



    def createInfoLog(self,room, now : float):
        log = LogEntry(
                        device_id = str(room),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-now),
                        device_type="sensor",
                        type_= "movement"
                    )
        return log
    
    def createToiletLog(self,room, now : float):
        log = LogEntry(
                        device_id = str(room),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-now),
                        device_type="sensor",
                        type_= "ToiletDuration"
                    )
        return log



    #Define thread for class

    def timeoutCounter(self):
        
        SystemSettings = self.model.getSettings()
        
        #Start string: HH:MM
        self.STARTTIME = datetime.datetime.strptime(SystemSettings.start,"%H:%M")
        self.ENDTIME = datetime.datetime.strptime(SystemSettings.end,"%H:%M")
        
        #timeout in seconds
        X=SystemSettings.bathroom_timeout*60
        while True and self.state is not States.UNACTIVE:
            
            #if (time.time() > self.lasttimerecorded + X):
                #self.state=States.TIMEOUT

            if (self.state==States.IDLE or self.state==States.FAILURE):
                
                continue
            
            elif (self.timeout == False):
                
                if (self.current_room.typeroom==roomType.BATHROOM):
                    X=SystemSettings.bathroom_timeout*60
                    
                elif (self.current_room.typeroom==roomType.BEDROOM):
                    
                    X=SystemSettings.bedroom_timeout*60
                    print("from settings:" , SystemSettings.bedroom_timeout)
                else:
                    X=SystemSettings.default_timeout*60
                    

                if (time.time() > self.lasttimerecorded + X and self.current_room.typeroom == roomType.BEDROOM):
                    self.state = States.IDLE
                    self.TurnOffAllLights()
                    self.timeout=True
                
                elif (time.time() > self.lasttimerecorded + X and self.current_room.typeroom != roomType.BEDROOM):
                    #Create timeout event
                    print("Timeout")
                    
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "warning",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "Timeout"
                    )
                    
                    self.model.queueLog(log=log)
                    self.Warning()
                    
                    self.timeout=True
                    
                time.sleep(1)
                print(self.timeout)
                    

    def listenForEvents(self):
        while True:
            if (self.mqttController.getQueueLength()>0):
                
                
                #Create event from Queue
                queueMessage = self.mqttController.popQueue()
                
                queuePlace = room(roomID=getRoomType(queueMessage.topic.split("/")[1]))
                queueEvent = lightEvent(type=EventType(EventType.MOVEMENT),place=queuePlace)
                
                print(getRoomType(queueMessage.topic.split("/")[1]))
                
                self.handleEvent(queueEvent)
            

    def __init__(self, ctrl, dbctrl) -> None:
        self.model = dbctrl
        self.model.start()
        
        # Create a controller and give it the data model that was instantiated.
        self.mqttController = ctrl
        self.mqttController.start()
        
        timeoutThread = threading.Thread(target=self.timeoutCounter)
        self.state = States.IDLE
        self.rooms = initRooms()
        self.timer = 0
        self.lasttimerecorded = time.time()
        #Start timeout thread
        timeoutThread.start()
        self.timeout=False
        self.hasJustVisitedBathroom=False
        
        self.current_room = self.rooms.get(roomType.BEDROOM)

        listenEventThread = threading.Thread(target=self.listenForEvents)
        listenEventThread.start()

    def TurnOffAllLights(self):
        for _, roomval in self.rooms.items():
            self.mqttController.turnOffLight(roomval.typeroom.name)
    
    def TurnOnAllLights(self, color=""):
        for _, roomval in self.rooms.items():
            self.mqttController.turnOnLight(roomval.typeroom.name,color=color)
            
    def Warning(self):
        colors = ["red","green",""]
        for i in range(5):
            for j in colors:
                self.TurnOffAllLights()
                time.sleep(1)
                self.TurnOnAllLights(color=j)
                time.sleep(1)
        

    def doMovementLogic(self, event:lightEvent, dir): 
        next = self.current_room.forwardRoom if (dir == "forward") else self.current_room.backwardRoom
        pre = self.current_room.backwardRoom if (dir == "forward") else self.current_room.forwardRoom 
        if event.type == EventType.MOVEMENT and event.place.typeroom == next.typeroom:
                    #turn of light and update current room
                    self.mqttController.turnOffLight(self.current_room.typeroom.name)
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #move "pointer" to next link
                    next = next.forwardRoom if (dir == "forward") else next.backwardRoom
                    
                    #send log to database controller
                    log = self.createInfoLog(self.current_room.typeroom.name,self.lasttimerecorded)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(next.typeroom.name,color="green")
                    self.mqttController.turnOnLight(lightID=self.current_room.typeroom.name,color="red")


        elif(event.type == EventType.MOVEMENT and event.place.typeroom == pre.typeroom):
                    #turn of light in previous room
                    self.mqttController.turnOffLight(next.typeroom.name)
                    self.mqttController.turnOffLight(self.current_room.typeroom.name)
                    

                    #flip state and update current room
                    self.state=States.BACKWARD if(States.FORWARD) else States.FORWARD
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #move "pointer" to next link
                    pre = pre.backwardRoom if (dir == "forward") else pre.forwardRoom
                    
                    #log event
                    log = self.createInfoLog(self.current_room.typeroom.name,self.lasttimerecorded)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(pre.typeroom.name,color="green")
                    self.mqttController.turnOnLight(self.current_room.typeroom.name,color="red")

        else:
            #Teleport. Guide back to bedroom
            self.state=States.BACKWARD
            
                
            self.mqttController.turnOffLight(self.current_room.typeroom.name)
            
            print(event.place.typeroom.name)
            
            #Set new room and turn on that rooms next room (backward room)
            self.current_room = self.rooms.get(event.place.typeroom)
            
            #Turn off light in old room.
            for roomkey, roomval in self.rooms.items():
                if (roomkey!=self.current_room.typeroom and roomkey!=self.current_room.backwardRoom.typeroom):
                    self.mqttController.turnOffLight(roomval.typeroom.name)
            self.mqttController.turnOnLight(self.current_room.typeroom.name,color="red")
            self.mqttController.turnOnLight(self.current_room.backwardRoom.typeroom.name,color="green")
            
            log = self.createInfoLog(self.current_room.typeroom.name,self.lasttimerecorded)
            self.model.queueLog(log=log)
             
 
    
    def handleEvent(self, event : lightEvent):

        #check if event is deactivate/active or error


        now = time.time()
        self.lasttimerecorded = now
        self.timeout=False
        #self.current_room = self.rooms.get(event.place.typeroom)
  
        if (self.state == States.IDLE):
            if(event.place.typeroom == roomType.BEDROOM):
                self.state = States.FORWARD
                self.current_room = self.rooms.get(roomType.BEDROOM)
                self.mqttController.turnOnLight("BEDROOM",color="red")
                self.mqttController.turnOnLight(self.current_room.forwardRoom.typeroom.name,color="green")
                
                #Start tracking timer for when next endpoint is reached
                self.trackingTimer = time.time()
                print("Starting trackingtimer")
                return

        #Detecting from same room, ignore sensor movement
        if (event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.typeroom):
                    return
                
        #If the event is movement, and user just was in bathroom, log the time he was in bathroom:
        if (event.type == EventType.MOVEMENT and self.hasJustVisitedBathroom is True):
            print("Person was in bathroom for: ", time.time()-self.trackingTimer)
            self.model.queueLog(log=self.createToiletLog(self.current_room.typeroom.name,self.trackingTimer))
            #Set timer back to 0 to track travel time back to bedroom.
            self.trackingTimer = time.time()
            self.hasJustVisitedBathroom=False

        if (self.state == States.FORWARD):
            #reached the bathroom
            if event.place.typeroom == roomType.BATHROOM:
                self.state = States.BACKWARD
                self.current_room=self.rooms.get(roomType.BATHROOM)
                self.mqttController.turnOnLight(self.current_room.typeroom.name,"red")
                self.mqttController.turnOnLight(self.current_room.backwardRoom.typeroom.name,"green")
                
                #Log time from last endpoint
                print("Time since last endpoint was reached: ", time.time()-self.trackingTimer)
                self.model.queueLog(log=self.createInfoLog(self.current_room.typeroom.name,self.trackingTimer))
                #Set timer to 0 and flag to true
                self.trackingTimer=time.time()
                self.hasJustVisitedBathroom=True
                
                
            else:
                #continued forward
                self.doMovementLogic(event=event,dir="forward")
                return
            

        elif (self.state == States.BACKWARD):
            #check for arrival in bedroom
            if event.place.typeroom == "BEDROOM":
            
                self.current_room=self.rooms.get(roomType.BEDROOM)
                self.mqttController.turnOffLight(self.current_room.typeroom.name)
                
                #Log the time since last endpoint. Can either be bedroom, if he decided to go back, or bathroom from a 'succesful trip'
                self.model.queueLog(log=self.createInfoLog(self.current_room.typeroom.name,self.timeoutCounter))
                #LIGE HER
                

                
            else:
                #continued backwards:
                self.doMovementLogic(event=event,dir="backward")
                return
                


        else:
            #TODO report unexpected shit
            pass