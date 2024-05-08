import json
from Cep2Model import Cep2Model
from Cep2WebClient import Cep2WebClient, Cep2WebDeviceEvent
from Cep2Zigbee2mqttClient import (Cep2Zigbee2mqttClient,
                                   Cep2Zigbee2mqttMessage, Cep2Zigbee2mqttMessageType)
class MQTTController:
    HTTP_HOST = "http://localhost:8000"
    MQTT_BROKER_HOST = "localhost"
    MQTT_BROKER_PORT = 1883
    
    queue = []
    

    """ The controller is responsible for managing events received from zigbee2mqtt and handle them.
    By handle them it can be process, store and communicate with other parts of the system. In this
    case, the class listens for zigbee2mqtt events, processes them (turn on another Zigbee device)
    and send an event to a remote HTTP server.
    """
    
    def popQueue(self):        
        return self.queue.pop(0)
    
    def getQueueLength(self):
        return len(self.queue)

    def enqueue(self,event : Cep2Zigbee2mqttMessage):
        self.queue.append(event)

    def __init__(self, devices_model: Cep2Model) -> None:
        """ Class initializer. The actuator and monitor devices are loaded (filtered) only when the
        class is instantiated. If the database changes, this is not reflected.

        Args:
            devices_model (Cep2Model): the model that represents the data of this application
        """
        self.__devices_model = devices_model
        self.__z2m_client = Cep2Zigbee2mqttClient(host=self.MQTT_BROKER_HOST,
                                                  port=self.MQTT_BROKER_PORT,
                                                  on_message_clbk=self.__zigbee2mqtt_event_received)

    def start(self) -> None:
        """ Start listening for zigbee2mqtt events.
        """
        self.__z2m_client.connect()
        print(f"Zigbee2Mqtt is {self.__z2m_client.check_health()}")

    def stop(self) -> None:
        """ Stop listening for zigbee2mqtt events.
        """
        self.__z2m_client.disconnect()
        
    def turnOnLight(lightID : str):
        print("turn on")

    def __zigbee2mqtt_event_received(self, message: Cep2Zigbee2mqttMessage) -> None:
        """ Process an event received from zigbee2mqtt. This function given as callback to
        Cep2Zigbee2mqttClient, which is then called when a message from zigbee2mqtt is received.

        Args:
            message (Cep2Zigbee2mqttMessage): an object with the message received from zigbee2mqtt
        """
        # If message is None (it wasn't parsed), then don't do anything.
        if not message:
            return
        if message.event != None and message.event != [] and False:
            print(
                f"zigbee2mqtt event received on topic {message}: {message.event}")

        # If the message is not a device event, then don't do anything.
        if message.type_ != Cep2Zigbee2mqttMessageType.DEVICE_EVENT:
            return

        # Parse the topic to retreive the device ID. If the topic only has one level, don't do
        # anything.
        tokens = message.topic.split("/")

        if len(tokens) <= 1:
            return

        # Retrieve the device ID from the topic.
        device_id = tokens[1]
        

        #Create event for event handler
        
        #Set event in queue
        
        
        
        if not ("strip" in device_id):
            self.enqueue(message)
        
        

        if (device_id=='pir1'):
            print(device_id)
            occupancy = message.event["occupancy"]
            new_state = "ON" if occupancy else "OFF"
            print(new_state)
            self.__z2m_client.change_state("strip",new_state)
            self.__z2m_client.publish_event("","pir")
            self.__z2m_client.change_state("strip2","OFF")


        
        if (device_id=='pir2'):
            print(device_id)
            occupancy = message.event["occupancy"]
            new_state = "ON" if occupancy else "OFF"
            print(new_state)
            self.__z2m_client.change_state("strip2",new_state)
            self.__z2m_client.publish_event("","pir2")
            self.__z2m_client.change_state("strip","OFF")


