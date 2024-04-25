import datetime
import time
from enum import Enum
import threading
import Cep2Eveman as CE



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
    
    



class room:
    typeroom: roomType
    forwardRoom: None
    backwardRoom: None
    light : Light
    sensor: Sensor
    isCurrent : bool = False

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
    bedroom.isCurrent=True
    bedroom.forwardRoom= living_room
    living_room.backwardRoom=bedroom
    
    living_room.forwardRoom=kitchen
    kitchen.backwardRoom=living_room
    
    kitchen.forwardRoom=guest_room
    guest_room.backwardRoom=kitchen
    
    guest_room.forwardRoom=bathroom
    bathroom.backwardRoom=guest_room
    
    rooms = {roomType.BEDROOM:bedroom, roomType.KITCHEN:kitchen, roomType.BATHROOM:bathroom, roomType.LIVINGROOM:living_room,roomType.GUESTROOM:guest_room}

    return rooms


class EventHandler:

    rooms : dict
    state : States
    current_room : room
    timer : int
    lasttimerecorded : float
    model : CE.DB
    timeout : bool

    #Define thread for class

    def timeoutCounter(self):
        
        
        #Connect to db
        self.model = CE.DB(host="192.168.32.97",
                                        database="group1lightguide",
                                        user="sodeChristian",
                                        password="1234")
        self.model.connect()
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
                    X=99999999999
                else:
                    X=SystemSettings.default_timeout


                if (time.time() > self.lasttimerecorded + X):
                    #Create timeout event
                    timoutEvent = lightEvent(EventType.TIMEOUT_EVENT)
                    
                    
                    log = CE.LogEntry(
                        device_id = self.current_room.sensor.sensorID,
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(datetime.datetime.now()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "Movement"
                    )
                    
                    self.model.InsertLog(log=log)

                    #self.state=States.TIMEOUT
                    self.timeout=True
                    
                    return  timoutEvent# or raise TimeoutException()




    def __init__(self) -> None:
        timeoutThread = threading.Thread(target=self.timeoutCounter)
        self.state = States.IDLE
        self.rooms = initRooms()
        self.timer = 0
        self.lasttimerecorded = time.time()
        #Start timeout thread
        timeoutThread.start()
        self.timeout=False
        
        
        
        
        

    
    def handleEvent(self, event : lightEvent):
        #check if event is deactivate/active or error


        now = time.time()
        self.lasttimerecorded = now
        self.timeout=False
        #self.current_room = self.rooms.get(event.place.typeroom)

        self.model = CE.DB(host="192.168.32.97",
                                        database="group1lightguide",
                                        user="sodeChristian",
                                        password="1234")
        self.model.connect()
        SystemSettings = self.model.getSettings()
        
        
                    

        if (self.state == States.IDLE):
            print("here")
            if(event.place.typeroom == roomType.BEDROOM):
                print("in bedroom")
                #activate system
                self.state = States.FORWARD
                self.current_room = self.rooms.get(roomType.BEDROOM)
                print("WE HAVE WOKEN")
                return



        if (self.state == States.FORWARD):
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
                    log = CE.LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.InsertLog(log=log)

                    
                    
                    
                else:
                    print("UNEXPECTED ROOM HANDLE PLEASE")
                    #Logic for unexpected spawn/teleports
                    
                print("Init new current room")
                #self.current_room.light.turn_on("current")
                #self.current_room.forwardRoom.light.turn_on("next")
                return
            

        if (self.state == States.BACKWARD):
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
                
                print(event.place.typeroom,self.current_room.backwardRoom.typeroom)
                
                
                if event.type == EventType.MOVEMENT and event.place.typeroom == self.current_room.backwardRoom.typeroom:
                    print("Moved to previous room. Turning off old room light")
                    self.current_room = self.rooms.get(event.place.typeroom)
                    log = CE.LogEntry(
                        device_id = str(self.current_room.typeroom.name),
                        loglevel = "Informational",
                        timestamp = datetime.datetime.now(),
                        measurement = str(time.time()-self.lasttimerecorded),
                        device_type="sensor",
                        type_= "movement"
                    )
                    self.model.InsertLog(log=log)
                
                else:
                    print("UNEXPECTED ROOM HANDLE PLEASE")
                    #Logic for unexpected spawn/teleports
                
                print("Init new current room")
        
        
        
        if (self.state == States.FAILURE):
            #TODO hanfle failure
            pass
        
        if (self.state == States.UNACTIVE):
            pass


        else:
            #TODO report unexpected shit
            pass

