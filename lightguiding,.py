import time
from enum import Enum
import threading



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
        if placement=="current":
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
    HALL = 0
    BATHROOM = 1
    BEDROOM = 2



class room:
    roomType: roomType
    forwardRoom: None
    backwardRoom: None
    light : Light
    sensor: Sensor
    isCurrent : bool = False

    def __init__(self,roomID) -> None:
        self.roomID = roomID
        self.forwardRoom:room
        self.backwardRoom:room

class EventType(Enum):
    TIMEOUT_EVENT=0
    MOVEMENT=1
    FAILURE_EVENT=2
    BUTTON_PRESS=3


class Event:
    eventtype : EventType
    Room : room

    def __init__(self, EventType:EventType, Room:room) -> None:
        self.eventtype = EventType
        self.room = Room

def initRooms():
    #hardcoded
    bedroom = room(2)
    kitchen = room(0)
    living_room = room(0)
    guest_room = room(0)
    bathroom = room(1)

    #Map
    bedroom.isCurrent=True
    bedroom.forwardRoom= living_room
    living_room.backwardRoom=bedroom
    living_room.forwardRoom=kitchen
    kitchen.backwardRoom=living_room
    kitchen.forwardRoom=guest_room
    guest_room.backwardRoom=kitchen
    guest_room=bathroom
    bathroom.backwardRoom=guest_room
    
    rooms = {"bedroom":bedroom, "kitchen":kitchen, "bathroom":bathroom, "living_room":living_room,"guest_room":guest_room}

    return rooms


class EventHandler:

    rooms : dict
    state : States
    current_room : room
    timer : int
    lasttimerecorded : float

    #Define thread for class

    def timeoutCounter(self,eventtype : Event):
        if (eventtype.room.roomType=="bathroom"):
            X=600 #TODO: Determine bathroom normal time etc.
        else:
            X=60
     
        while True:

            if (self.state==States.IDLE or self.state==States.FAILURE or self.state==States.TIMEOUT):
                pass
            
            else:

                if (time.time() > self.lasttimerecorded + X):
                    #Create timeout event
                    timoutEvent = Event(EventType.TIMEOUT_EVENT,eventtype.room)
                    return  timoutEvent# or raise TimeoutException()
            print("a") # do whatever you need to do


    timeoutThread = threading.Thread(target=timeoutCounter(Event()))

    def __init__(self) -> None:
        self.state = States.IDLE
        self.rooms = initRooms()
        self.timer = 0
        self.lasttimerecorded = time.time()
        #Start timeout thread
        self.timeoutThread.start()

    
    def handleEvent(self, event : Event):
        #check if event is deactivate/active or error


        now = time.time()
        self.lasttimerecorded = now


        if (self.state == States.IDLE):
            if(Event.sourceid == "bedroom"):
                #activate system
                self.state = States.FORWARD
                self.current_room.roomID = self.rooms.get("bedroom")
                pass



        if (self.state == States.FORWARD):
            if self.current_room.roomID == "bathroom":
                self.state = States.BACKWARD
            else:

                # possibly advance room
                if event.sourceid == self.current_room.forwardRoom.sensor.sensorID:
                    self.current_room.light.turn_off()
                    self.current_room = self.current_room.forwardRoom
                
                self.current_room.light.turn_on("current")
                self.current_room.forwardRoom.light.turn_on("next")

        if (self.state == States.BACKWARD):
            #check for arrival in bedroom
            if self.current_room.roomID == "BEDROOM":
                #User has arrived back in bed succesfully. Start timer for setting idle. Timer can be overwritten by new signal
                #increment timer
                now = time.time()
                timer += (now - self.lasttimerecorded)
                self.lasttimerecorded = now
                if (timer > 10*60):
                    self.state = States.IDLE
                
            else:
                #check if source id from event is the expected
                self.current_room.light.turn_on("current")
                self.current_room.backwardRoom.light.turn_on("next")
                self.current_room = self.current_room.backwardRoom
        
        if (self.state == States.TIMEOUT):
            #TODO Handle case where user has not moved. Depends on current room.


            pass
        
        if (self.state == States.FAILURE):
            #TODO hanfle failure
            pass
        
        if (self.state == States.UNACTIVE):
            pass


        else:
            #TODO report unexpected shit
            pass

