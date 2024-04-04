import time
from enum import Enum
#enum states
class States(Enum):
    IDLE = 1
    FORWARD = 2
    BACKWARD = 3
    TIMEOUT = 4
    FAILERE = 5

class Light:
    lightID: str
    status : bool

    def turn_on(self):
        pass

class Sensor:
    sensorID: str
    status : bool 

class room:
    roomID: str
    forwardRoom: None
    backwardRoom: None
    light : Light
    sensor: Sensor

    def __init__(self,roomID) -> None:
        self.roomID = roomID
        self.forwardRoom:room
        self.backwardRoom:room


class Event:
    eventtype : str
    sourceid : str
    message : str

    def __init__(self, EventType:str, sourceID:str, msg:str) -> None:
        self.eventtype = EventType
        self.sourceid = sourceID
        self.message = msg

def initRooms():
    #hardcoded
    bedroom = room("bedroom")
    kitchen = room("kitchen")
    bathroom = room("bathroom")
    kitchen.backwardRoom = bedroom
    kitchen.forwardRoom = bathroom
    bedroom.forwardRoom = kitchen
    bedroom.backwardRoom = bedroom
    bathroom.backwardRoom = kitchen
    bathroom.forwardRoom = bathroom
    rooms = {"bedroom":bedroom, "kitchen":kitchen, "bathroom":bathroom}

    return rooms


class EventHandler:
    #hardcoded lst of rooms
    rooms : dict
    state : States
    current_room : room
    timer : int
    lasttimerecorded : float

    def __init__(self) -> None:
        self.state = States.IDLE
        self.rooms = initRooms()
        self.timer = 0
        self.lasttimerecorded = time.time()
    
    def handleEvent(self, event : Event):
        #check if event is deactivate/active or error


        if (self.state == States.IDLE):
            if(Event.sourceid == "bedroom"):
                #activate system
                self.state = States.FORWARD
                self.current_room.roomID = self.rooms.get("bedroom")
                pass

        if (self.state == States.FORWARD):
            if self.current_room.roomID == "WC":
                self.state = States.BACKWARD
            else:

                if (self.current_room.roomID == event.sourceid):
                    #increment timer
                    now = time.time()
                    timer += (now - self.lasttimerecorded)
                    self.lasttimerecorded = now
                    if (timer > 10*60):
                        self.state = States.FAILERE


                # possibly advance room
                if event.sourceid == self.current_room.forwardRoom.sensor.sensorID:
                    self.current_room = self.current_room.forwardRoom
                
                self.current_room.light.turn_on()
                self.current_room.forwardRoom.light.turn_on()

        if (self.state == States.BACKWARD):
            #check for arrival in bedroom
            if self.current_room.roomID == "BEDROOM":
                self.state = States.IDLE
            else:
                #check if source id from event is the expected
                self.current_room.light.turn_on()
                self.current_room.backwardRoom.light.turn_on()
                self.current_room = self.current_room.backwardRoom
        
        if (self.state == States.TIMEOUT):
            pass
        
        if (self.state == States.FAILERE):
            pass
        
        else:
            #report unexpected shit
            pass

