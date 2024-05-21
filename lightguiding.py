import datetime
import re
import time
from enum import Enum
import threading
import DatabaseController as DBC
from DBmodels import LogEntry, Settings
from grandyLightController import MQTTController



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
    typeRoom: roomType
    forwardRoom: None
    backwardRoom: None

    def __init__(self,roomID) -> None:
        self.typeRoom = roomID
        self.forwardRoom:room
        self.backwardRoom:room
    def __str__(self) -> str:
        return self.typeRoom.name
    
    def __eq__(self, value) -> bool:
        return self.typeRoom == value.typeRoom

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
    bedroom = room(roomType.BEDROOM)
    kitchen = room(roomType.KITCHEN)
    living_room = room(roomType.LIVINGROOM)
    guest_room = room(roomType.GUESTROOM)
    bathroom = room(roomType.BATHROOM)
    
    roomSetupList = [] 
    
    with open("roomSetup.txt") as roomList:
        roomString = ""
        for room_i in roomList:
            if room_i == "bathroom":
                roomString += room_i
                break
            else:
                roomString += room_i + ","
        
        roomSetupList = eval("[" + roomString + "]")
   
    # Creates a link between all connected rooms to map the path
    for i in range(len(roomSetupList)-1):
        roomSetupList[i].backwardRoom = roomSetupList[i-1]
        roomSetupList[i].forwardRoom = roomSetupList[i+1]
        if i == 0:
            roomSetupList[i].backwardRoom = roomSetupList[i]

    roomSetupList[-1].backwardRoom = roomSetupList[-2]
    roomSetupList[-1].forwardRoom =roomSetupList[-1]
        
    rooms = {roomType.BEDROOM:bedroom, roomType.KITCHEN:kitchen, roomType.BATHROOM:bathroom, roomType.LIVINGROOM:living_room,roomType.GUESTROOM:guest_room}

    return rooms


class EventHandler:

    rooms : dict
    state : States
    currentRoom : room
    timer : int
    lastTimeRecorded : float
    model : DBC.DBController
    timeout : bool
    mqttController : MQTTController
    trackingTimer : float
    hasJustVisitedBathroom : bool
    
    STARTTIME = datetime.time(22,0,0)
    ENDTIME = datetime.time(9,0,0)



    def createInfoLog(self,room, now : float, log_type: str = "movement"):
        log = LogEntry(
                        device_id = str(room),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-now),
                        device_type="sensor",
                        type_= log_type
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
                
                if (self.currentRoom.typeRoom==roomType.BATHROOM):
                    X=SystemSettings.bathroom_timeout*60
                    
                elif (self.currentRoom.typeRoom==roomType.BEDROOM):
                    
                    X=SystemSettings.bedroom_timeout*60
                    print("from settings:" , SystemSettings.bedroom_timeout)
                else:
                    X=SystemSettings.default_timeout*60
                    

                if (time.time() > self.lastTimeRecorded + X and self.currentRoom.typeRoom == roomType.BEDROOM):
                    self.state = States.IDLE
                    self.TurnOffAllLights()
                    self.timeout=True
                
                elif (time.time() > self.lastTimeRecorded + X and self.currentRoom.typeRoom != roomType.BEDROOM):
                    #Create timeout event
                    print("Timeout")
                    
                    log = LogEntry(
                        device_id = str(self.currentRoom),
                        loglevel = "warning",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lastTimeRecorded),
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
        self.lastTimeRecorded = time.time()
        #Start timeout thread
        timeoutThread.start()
        self.timeout=False
        self.hasJustVisitedBathroom=False
        
        self.currentRoom = self.rooms.get(roomType.BEDROOM)

        listenEventThread = threading.Thread(target=self.listenForEvents)
        listenEventThread.start()

    def TurnOffAllLights(self):
        for _, room_i in self.rooms.items():
            self.mqttController.turnOffLight(room_i)
    
    def TurnOnAllLights(self, color=""):
        for _, room_i in self.rooms.items():
            self.mqttController.turnOnLight(room_i,color=color)
            
    def Warning(self):
        colors = ["red","green",""]
        for i in range(5):
            for j in colors:
                self.TurnOffAllLights()
                time.sleep(1)
                self.TurnOnAllLights(color=j)
                time.sleep(1)
        

    def doMovementLogic(self, event:lightEvent, dir): 
        nextRoom = self.currentRoom.forwardRoom if (dir == "forward") else self.currentRoom.backwardRoom
        previousRoom = self.currentRoom.backwardRoom if (dir == "forward") else self.currentRoom.forwardRoom 
        if event.type == EventType.MOVEMENT and event.place == nextRoom:
                    #turn of light and update current room
                    self.mqttController.turnOffLight(self.currentRoom)
                    self.currentRoom = self.rooms.get(event.place.typeRoom)
                    
                    #move "pointer" to next link
                    nextRoom = nextRoom.forwardRoom if (dir == "forward") else nextRoom.backwardRoom
                    
                    #send log to database controller
                    log = self.createInfoLog(self.currentRoom,self.lastTimeRecorded)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(nextRoom,color="green")
                    self.mqttController.turnOnLight(self.currentRoom,color="red")


        elif(event.type == EventType.MOVEMENT and event.place == previousRoom):
                    #turn of light in previous room
                    self.mqttController.turnOffLight(nextRoom)
                    self.mqttController.turnOffLight(self.currentRoom)
                    

                    #flip state and update current room
                    self.state=States.BACKWARD if(States.FORWARD) else States.FORWARD
                    self.currentRoom = self.rooms.get(event.place.typeRoom)
                    
                    #move "pointer" to next link
                    previousRoom = previousRoom.backwardRoom if (dir == "forward") else previousRoom.forwardRoom
                    
                    #log event
                    log = self.createInfoLog(self.currentRoom,self.lastTimeRecorded)
                    self.model.queueLog(log=log)
                    
                    #turn on current room and next room
                    self.mqttController.turnOnLight(previousRoom,color="green")
                    self.mqttController.turnOnLight(self.currentRoom,color="red")

        else:
            #Teleport. Guide back to bedroom
            self.state=States.BACKWARD
            
                
            self.mqttController.turnOffLight(self.currentRoom)
            
            print(event.place)
            
            #Set new room and turn on that rooms next room (backward room)
            self.currentRoom = self.rooms.get(event.place.typeRoom)
            
            #Turn off light in old room.
            for roomkey, roomval in self.rooms.items():
                if (roomkey!=self.currentRoom.typeRoom and roomkey!=self.currentRoom.backwardRoom.typeRoom):
                    self.mqttController.turnOffLight(roomval)
            self.mqttController.turnOnLight(self.currentRoom,color="red")
            self.mqttController.turnOnLight(self.currentRoom.backwardRoom,color="green")
            
            log = self.createInfoLog(self.currentRoom,self.lastTimeRecorded)
            self.model.queueLog(log=log)
             
 
    
    def handleEvent(self, event : lightEvent):

        #check if event is deactivate/active or error


        now = time.time()
        self.lastTimeRecorded = now
        self.timeout=False
  
        if (self.state == States.IDLE):
            if(event.place.typeRoom == roomType.BEDROOM):
                self.state = States.FORWARD
                self.currentRoom = self.rooms.get(roomType.BEDROOM)
                self.mqttController.turnOnLight("BEDROOM",color="red")
                self.mqttController.turnOnLight(self.currentRoom.forwardRoom,color="green")
                
                #Start tracking timer for when next endpoint is reached
                self.trackingTimer = now
                print("Starting trackingtimer")
                return

        #Detecting from same room, ignore sensor movement
        if (event.type == EventType.MOVEMENT and event.place == self.currentRoom):
                    return
                
        #If the event is movement, and user just was in bathroom, log the time he was in bathroom:
        if (event.type == EventType.MOVEMENT and self.hasJustVisitedBathroom is True):
            print("Person was in bathroom for: ", now-self.trackingTimer)
            self.model.queueLog(log=self.createInfoLog(self.currentRoom,self.trackingTimer, log_type="ToiletDuration"))
            #Set timer back to 0 to track travel time back to bedroom.
            self.trackingTimer = now
            self.hasJustVisitedBathroom=False

        if (self.state == States.FORWARD):
            #reached the bathroom
            if event.place.typeRoom == roomType.BATHROOM:
                self.state = States.BACKWARD
                self.currentRoom=self.rooms.get(roomType.BATHROOM)
                self.mqttController.turnOnLight(self.currentRoom,"red")
                self.mqttController.turnOnLight(self.currentRoom.backwardRoom,"green")
                
                #Log time from last endpoint
                print("Time since last endpoint was reached: ", now-self.trackingTimer)
                self.model.queueLog(log=self.createInfoLog(self.currentRoom,self.trackingTimer))
                #Set timer to 0 and flag to true
                self.trackingTimer=now
                self.hasJustVisitedBathroom=True
                
                
            else:
                #continued forward
                self.doMovementLogic(event=event,dir="forward")
                return
            

        elif (self.state == States.BACKWARD):
            #check for arrival in bedroom
            if event.place.typeRoom == "BEDROOM":
            
                self.currentRoom=self.rooms.get(roomType.BEDROOM)
                self.mqttController.turnOffLight(self.currentRoom)
                
                #Log the time since last endpoint. Can either be bedroom, if he decided to go back, or bathroom from a 'succesful trip'
                self.model.queueLog(log=self.createInfoLog(self.currentRoom,self.timeoutCounter))
                #LIGE HER
                

                
            else:
                #continued backwards:
                self.doMovementLogic(event=event,dir="backward")
                return
                


        else:
            log = LogEntry(
                        device_id = str(self.currentRoom),
                        loglevel = "error",
                        timestamp = datetime.datetime.now(),
                        measurement = str(0),
                        device_type="none",
                        type_= "Unexpected event"
                    )
                    
            self.model.queueLog(log=log)
            self.Warning()
