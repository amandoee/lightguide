from time import sleep
import datetime
from Cep2Model import Cep2Model, Cep2ZigbeeDevice
import lightguiding as lg
import Cep2Controller
import DatabaseController
STARTTIME=datetime.time(22,0,0)
ENDTIME=datetime.time(6,0,0)


# TODAY=datetime.datetime.now()

# STARTTIME=datetime.time(year=TODAY.year,month=TODAY.month,day=TODAY.day,hour=22,minute=0)
# ENDTIME=datetime.time(year=TODAY.year,month=TODAY.month,day=TODAY,hour=9,minute=0)

if __name__ == "__main__":
    # Create a data model and add a list of known Zigbee devices.
    dbctrl = DatabaseController()
    ctrl = Cep2Controller()
    handler = lg.EventHandler(ctrl=ctrl, dbctrl=dbctrl )

    sleep(4)

    

    #MOVEMENTS
    bedroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BEDROOM))
    livingroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.LIVINGROOM))
    kitchen = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.KITCHEN))
    guest_room = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.GUESTROOM))
    bathroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BATHROOM))
    
    
    
    

    # handler.handleEvent(bedroom)
    # print("test")

    # sleep(3)
    
    # handler.handleEvent(livingroom)

    # sleep(3)
    
    # handler.handleEvent(kitchen)
    
    # sleep(3)
    
    # #Going back to living room
    
    
   
    
    # sleep(3)

    
    
    # handler.handleEvent(Movedto4)
    # sleep(3)

    # handler.handleEvent(Movedto2)
    # sleep(3)
    # handler.handleEvent(Movedto4)
    # sleep(3)

    # #sleep(2)
    
    # handler.handleEvent(Movedto5)
    # print("Taking a piss...")
    # sleep(2)
    
    # Movedto6 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.GUESTROOM))
    # #handler.handleEvent(Movedto6)
    
    # #sleep(2)
    
    # Movedto7 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.KITCHEN))
    # #handler.handleEvent(Movedto7)

    # #sleep(2)
    
    # Movedto8 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.LIVINGROOM))
    # #handler.handleEvent(Movedto8)
    
    # #sleep(2)
    
    # Movedto9 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BEDROOM))
    # #handler.handleEvent(Movedto9)
    
    

    #print("Waiting for events...")

    #TODO: For system time periods activate again

    while True:
        pass
    #    
    #    if (datetime.datetime.now().hour<STARTTIME.hour and datetime.datetime.now().hour>=ENDTIME.hour):
    #        handler.state=lg.States.UNACTIVE

    controller.stop()
