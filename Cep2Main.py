from time import sleep
import datetime
from Cep2Controller import Cep2Controller
from Cep2Model import Cep2Model, Cep2ZigbeeDevice
import lightguiding as lg

STARTTIME=datetime.datetime()
ENDTIME=datetime.datetime()
STARTTIME.hour=22
ENDTIME.hour=9

if __name__ == "__main__":
    # Create a data model and add a list of known Zigbee devices.
    #devices_model = Cep2Model()
    
    # Create a controller and give it the data model that was instantiated.
    #controller = Cep2Controller(devices_model)
    #controller.start()


    handler = lg.EventHandler()

    #sleep(4)

    wakeywakey = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BEDROOM))
    handler.handleEvent(wakeywakey)
    
    #sleep(2)
    
    Movedto2 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.LIVINGROOM))
    handler.handleEvent(Movedto2)

    #sleep(2)
    
    Movedto3 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.KITCHEN))
    handler.handleEvent(Movedto3)
    
    #sleep(2)
    
    Movedto4 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.GUESTROOM))
    handler.handleEvent(Movedto4)

    #sleep(2)
    
    Movedto5 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BATHROOM))
    handler.handleEvent(Movedto5)
    print("Taking a piss...")
    sleep(2)
    
    Movedto6 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.GUESTROOM))
    handler.handleEvent(Movedto6)
    
    #sleep(2)
    
    Movedto7 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.KITCHEN))
    handler.handleEvent(Movedto7)

    #sleep(2)
    
    Movedto8 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.LIVINGROOM))
    handler.handleEvent(Movedto8)
    
    #sleep(2)
    
    Movedto9 = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BEDROOM))
    handler.handleEvent(Movedto9)
    
    

    #print("Waiting for events...")

    while True:
        
        if (datetime.datetime.now().hour<STARTTIME.hour and datetime.datetime.now().hour>=ENDTIME.hour):
            handler.state=lg.States.UNACTIVE

    controller.stop()
