from time import sleep
import datetime
from grandyLightModel import grandyLightModel, grandyLightZigbeeDevice
from DatabaseController import DBController
import lightguiding as lg
import grandyLightController

STARTTIME=datetime.time(22,0,0)
ENDTIME=datetime.time(6,0,0)

if __name__ == "__main__":
    # Create a data model and add a list of known Zigbee devices.
    dbctrl = DBController()
    ctrl = grandyLightController.MQTTController()

    handler = lg.EventHandler(ctrl=ctrl, dbctrl=dbctrl )
    handler.TurnOffAllLights()

    sleep(2)

    

    #MOVEMENTS
    bedroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BEDROOM))
    livingroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.LIVINGROOM))
    kitchen = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.KITCHEN))
    guest_room = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.GUESTROOM))
    bathroom = lg.lightEvent(lg.EventType.MOVEMENT,lg.room(lg.roomType.BATHROOM))
    
    
    # handler.handleEvent(bedroom)
    # sleep(4)
    # handler.handleEvent(livingroom)
    # sleep(4)
    # handler.handleEvent(kitchen)
    # # sleep(4)
    # # handler.handleEvent(guest_room)
    # sleep(4)
    # handler.handleEvent(bathroom)
    # # sleep(4)
    # # handler.handleEvent(guest_room)
    # sleep(4)
    # handler.handleEvent(kitchen)
    # sleep(4)
    # handler.handleEvent(livingroom)
    # sleep(4)
    # handler.handleEvent(bedroom)
    # sleep(4)
    
    
    #print("Waiting for events...")

    while True:
                
        if (datetime.datetime.now().hour<STARTTIME.hour and datetime.datetime.now().hour>=ENDTIME.hour):
             handler.state=lg.States.UNACTIVE
        elif handler.state is lg.States.UNACTIVE:
             handler.state=lg.States.IDLE 

    controller.stop()
