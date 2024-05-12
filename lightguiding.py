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
    TIMEOUT = 4
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



    def createInfoLog(self,room):
        log = LogEntry(
                        device_id = str(room),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
        return log


    #Define thread for class

    def timeoutCounter(self):
        
        #SystemSettings = self.model.getSettings()

        #timeout in seconds
        #X=SystemSettings.bathroom_timeout*60
        X=60*2
        while True:
            
            #if (time.time() > self.lasttimerecorded + X):
                #self.state=States.TIMEOUT

            if (self.state==States.IDLE or self.state==States.FAILURE):
                
                continue
            
               
            
            elif (self.timeout == False):
                
                if (self.current_room.typeroom==roomType.BATHROOM):
                    #X=SystemSettings.bathroom_timeout*60
                    X=60*2
                elif (self.current_room==roomType.BEDROOM):
                    X=3
                else:
                    X=60
                    #X=SystemSettings.default_timeout


                if (time.time() > self.lasttimerecorded + X):
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

                    #self.state=States.TIMEOUT
                    self.timeout=True
                    

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
        #self.model.start()
        
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
        
        self.current_room = self.rooms.get(roomType.BEDROOM)

        listenEventThread = threading.Thread(target=self.listenForEvents)
        listenEventThread.start()


    def doMovementLogic(self, event:lightEvent, dir): 
        next = self.current_room.forwardRoom.typeroom if (dir == "forward") else self.current_room.backwardRoom.typeroom
        pre = self.current_room.backwardRoom.typeroom if (dir == "forward") else self.current_room.forwardRoom.typeroom 
        if event.type == EventType.MOVEMENT and event.place.typeroom == next:
                    #turn of light and update current room
                    self.mqttController.turnOffLight(self.current_room.typeroom.name)
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #send log to database controller
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(self.current_room.typeroom.name)
                    self.mqttController.turnOnLight(next.name)

        elif(event.type == EventType.MOVEMENT and event.place.typeroom == pre):
                    self.state=States.BACKWARD if(States.FORWARD) else States.FORWARD
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #log event
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
        else:
            self.current_room = self.rooms.get(event.place.typeroom)        
            log = self.createInfoLog(self.current_room.typeroom.name)
            self.model.queueLog(log=log)
            self.state=States.BACKWARD
             
    
    def doForwardLogic(self, event:lightEvent):
                if event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.forwardRoom.typeroom:
                    #turn of light and update current room
                    self.mqttController.turnOffLight(self.current_room.typeroom.name)
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #send log to database controller
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(self.current_room.typeroom.name)
                    self.mqttController.turnOnLight(self.current_room.forwardRoom.typeroom.name)

                #user decided to turn around
                elif(event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.backwardRoom.typeroom):
                    self.state=States.BACKWARD
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    #log event
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)


                    
                #unexpected event
                else: #TELEPORT. Set room as current and assume direction for bedroom
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                    self.state=States.BACKWARD
                    
                #self.current_room.light.turn_on("current")
                #self.current_room.forwardRoom.light.turn_on("next")
                return


    def doBackwardLogic(self, event:lightEvent):
        #check if source id from event is the expected
                #self.current_room.light.turn_on("current_color")
                #self.current_room.backwardRoom.light.turn_on("next_color") 
                if event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.backwardRoom.typeroom:
                    
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                
                #If room is the opposite direction of expected, flip direction state
                elif(event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.forwardRoom.typeroom): 
                    self.state=States.FORWARD
                    
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                    
                    #Logic for unexpected spawn/teleports
                
                else: #TELEPORT. Set room as current and assume direction for bedroom
                    self.current_room = self.rooms.get(event.place.typeroom)
                    
                    log = self.createInfoLog(self.current_room.typeroom.name)
                    self.model.queueLog(log=log)
                    self.state=States.BACKWARD
                return
        
    #TODO: Light guide turns off after inactivity in bedroom.
    
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
                self.mqttController.turnOnLight("BEDROOM")
                return

        
        if (event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.typeroom):
                    return


        elif (self.state == States.FORWARD):
            #reached the bathroom
            if self.current_room.typeroom == roomType.BATHROOM:
                self.state = States.BACKWARD
                
            else:
                #continued forward
                self.doForwardLogic(event=event)
                return
            

        elif (self.state == States.BACKWARD):
            #check for arrival in bedroom
            if self.current_room.typeroom == "BEDROOM":
                #User has arrived back in bed succesfully. Start timer for setting idle. Timer can be overwritten by new signal
                #increment timer
                now = time.time()
                timer += (now - self.lasttimerecorded)
                self.lasttimerecorded = now
                if (timer > 10*60):
                    self.state = States.IDLE
                
            else:
                #continued backwards:
                self.doBackwardLogic(event=event)
                return
                
        
        
        if (self.state == States.UNACTIVE):
            pass


        else:
            #TODO report unexpected shit
            pass