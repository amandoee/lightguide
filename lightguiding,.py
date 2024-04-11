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
    roomID: roomType
    forwardRoom: None
    backwardRoom: None
    light : Light
    sensor: Sensor
    isCurrent : bool = False

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
    bedroom = room(2)
    kitchen = room(0)
    living_room = room(0)
    guest_room = room(0)
    bathroom = room(1)

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



        now = time.time()
        #Check if timer is over threshold. Depending on room, do something
        if (self.lasttimerecorded - now > 10*60):
            #



            pass


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
            #Handle case where user has not moved. Depends on current room.


            pass
        
        if (self.state == States.FAILERE):
            pass
        
        else:
            #report unexpected shit
            pass

