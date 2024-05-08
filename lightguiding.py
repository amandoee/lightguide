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

class Light:
    lightID: str
    status : bool

    def turn_on(self,placement):
        #TODO
        #Color is dependent on the room being next or current.
        if placement=="current_color":
            #Turn current room color
            pass
        else:
            #Turn next room color
            pass

        pass

    def turn_off(self):
        pass

class Sensor:
    sensorID: str
    status : bool 

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
    light : Light
    sensor: Sensor

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

    #Define thread for class

    def timeoutCounter(self):
        
        SystemSettings = self.model.getSettings()

        #timeout in seconds
        X=SystemSettings.bathroom_timeout*60
     
        while True:
            
            #if (time.time() > self.lasttimerecorded + X):
                #self.state=States.TIMEOUT

            if (self.state==States.IDLE or self.state==States.FAILURE):
                
                continue
            
               
            
            elif (self.timeout == False):
                
                if (self.current_room.typeroom==roomType.BATHROOM):
                    X=SystemSettings.bathroom_timeout*60
                elif (self.current_room==roomType.BEDROOM):
                    X=3
                else:
                    X=SystemSettings.default_timeout


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
            

    def __init__(self) -> None:
        self.model = DBC.DBController()
        self.model.start()
        
        # Create a controller and give it the data model that was instantiated.
        self.mqttController = MQTTController()
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
        
        
        
        
        
    #TODO: Light guide turns off after inactivity in bedroom.
    
    def handleEvent(self, event : lightEvent):
        #check if event is deactivate/active or error


        now = time.time()
        self.lasttimerecorded = now
        self.timeout=False
        #self.current_room = self.rooms.get(event.place.typeroom)
  

        if (self.state == States.IDLE):
            print("here")
            if(event.place.typeroom == roomType.BEDROOM):
                print("in bedroom")
                #activate system
                self.state = States.FORWARD
                self.current_room = self.rooms.get(roomType.BEDROOM)
                print("WE HAVE WOKEN")
                return

        print("---")
        print(event.type)
        print(self.current_room.typeroom)
        print(self.current_room.forwardRoom.typeroom)
        
        if (event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.typeroom):
                    print("Movement in same room detected")


        elif (self.state == States.FORWARD):
            if self.current_room.typeroom == roomType.BATHROOM:
                self.state = States.BACKWARD
                print(self.state)
                
            else:
                print(self.state)
                # possibly advance room
                print(event.place.typeroom)
                print(self.rooms.get(self.current_room.forwardRoom.typeroom).typeroom)
                
                
                if event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.forwardRoom.typeroom:
                    print("Moved to next room. Turning off old room light")
                    #self.current_room.light.turn_off()
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                    
                    self.mqttController.turnOnLight(self.current_room.typeroom.name)

                    
                    
                    
                elif(event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.backwardRoom.typeroom): #If room is the opposite direction of expected, flip direction state
                    print("Went opposite. Flipping direction")
                    self.state=States.BACKWARD
                    
                    print("opposite room than expected. Flipping direction")
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                    #Logic for unexpected spawn/teleports
                
                else: #TELEPORT. Set room as current and assume direction for bedroom
                    self.current_room = self.rooms.get(event.place.typeroom)
                    print("Teleport to", self.current_room.typeroom.name)

                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                    print("Setting direction towards bed")
                    self.state=States.BACKWARD
                    
                    
                print("Init new current room")
                #self.current_room.light.turn_on("current")
                #self.current_room.forwardRoom.light.turn_on("next")
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
                #check if source id from event is the expected
                #self.current_room.light.turn_on("current_color")
                #self.current_room.backwardRoom.light.turn_on("next_color")
                
                
                if event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.backwardRoom.typeroom:
                    print("Moved to previous room. Turning off old room light")
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                
                elif(event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.forwardRoom.typeroom): #If room is the opposite direction of expected, flip direction state
                    self.state=States.FORWARD
                    
                    print("opposite room than expected. Flipping direction")
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                    
                    #Logic for unexpected spawn/teleports
                
                else: #TELEPORT. Set room as current and assume direction for bedroom
                    self.current_room = self.rooms.get(event.place.typeroom)
                    print("Teleport to", self.current_room.typeroom.name)
                    log = LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.queueLog(log=log)
                    print("Setting direction towards bed")
                    self.state=States.BACKWARD
        
        
        
        if (self.state == States.FAILURE):
            #TODO hanfle failure
            pass
        
        if (self.state == States.UNACTIVE):
            pass


        else:
            #TODO report unexpected shit
            pass