from __future__ import annotations
import json
import signal
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any, Dict, List, Union
from mysql.connector import (connect as mysql_connect,
                             errorcode as mysql_errorcode,
                             Error as MySqlError)
#from paho.mqtt.client import Client as MqttClient, MQTTMessage
#from paho.mqtt import publish

@dataclass
class LogEntry:
    """ Sensor events to be stored in the database. """
    device_id: str #device name
    device_type: str #device type (light, sensor)
    measurement: str #durations
    timestamp_: datetime #"timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    loglevel : str #Informational, Warning, Error
    type_ : str # Movement, Toilet, ToiletDuration

    def __init__(self, device_id: str, device_type: str, measurement: str, timestamp:datetime,loglevel:str,type_:str ) -> None:
        self.device_id = device_id
        self.device_type = device_type
        self.measurement = measurement
        self.timestamp = timestamp
        self.loglevel = loglevel
        self.type_ = type_

class DB:

    def __init__(self, host, database: str, user: str, password: str) -> None:
        self.__database = database
        self.__host = host
        self.__mysql_connection = None
        self.__user = user
        self.__password = password


    def connect(self):
        """ Connect to database given in the initializer. The connection is left open and must be
        closed explicitly by the user using disconnect().
        """

        # If the connection is already open, then don't do anything.
        if self.__mysql_connection:
            return

        try:
            self.__mysql_connection = mysql_connect(host=self.__host,
                                                    user=self.__user,
                                                    password=self.__password)
            # Select the database given in the initalizer. If it fails, an exception is raised, that
            # can be used to create the database.
            self.__mysql_connection.cursor().execute(f"USE {self.__database}")
            print("succes")

        except MySqlError as err:
            # If the database doesn't exist, then create it.
            if err.errno == mysql_errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist. Will be created.")
                self.__create_database()
                print(f"Database {self.__database} created successfully.")
                self.__mysql_connection.database = self.__database
            else:
                print(f"Database error = {err}")


    def disconnect(self):
        """ Disconnect from the database.
        """
        self.__mysql_connection.close()
        self.__mysql_connection = None


    def InsertLog(self, log: LogEntry) -> None:
        if not self.__mysql_connection:
            raise RuntimeError(f"Not connected to database {self.__database}.")

        # timestamp - loglevel message
        query = ("INSERT INTO EVENT (timestamp_,loglevel,type_,measurement,device_id,device_type)"
                 "VALUES(%s, %s, %s, %s,%s,%s);")
        cursor = self.__mysql_connection.cursor()

        # If the value is a boolean, then convert it to a string in the format "true" or "false".
        # Other value types will be automatically converted to a string, once the query is executed.

        cursor.execute(query, (log.timestamp.strftime("%Y-%m-%d %H:%M:%S"), log.loglevel, log.type_, log.measurement, log.device_id, log.device_type))
        self.__mysql_connection.commit()

        cursor.close()

    def getSettings(self) -> Dict[str, int]:
        """ Retrieve settings from the database. """
        if not self.__mysql_connection:
            raise RuntimeError(f"Not connected to database {self.__database}.")

        #get all settings
        query = ("SELECT * FROM settings;")
        cursor = self.__mysql_connection.cursor()
        cursor.execute(query)

        #format data to dict
        desc = cursor.description
        column_names = [col[0] for col in desc]
        settings = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        cursor.close()

        return settings




#for future use
# class Cep2EvemanController:
#     """ Listen for MQTT messages that contain sensor events and store them into the model. """

#     TOPIC_MAIN_LEVEL = "cep2"
#     ALL_TOPICS = f"{TOPIC_MAIN_LEVEL}/#"
#     GET_EVENTS_REQUEST_TOPIC = f"{TOPIC_MAIN_LEVEL}/request/get_events"
#     GET_EVENTS_RESPONSE_TOPIC = f"{TOPIC_MAIN_LEVEL}/response/get_events"
#     STORE_EVENTS_TOPIC = f"{TOPIC_MAIN_LEVEL}/request/store_event"

#     def __init__(self, mqtt_host: str, model: Cep2EvemanModel, mqtt_port: int = 1883) -> None:
#         self.__connected = False
#         self.__events_queue = Queue()
#         self.__model = model
#         self.__mqtt_client = MqttClient()
#         self.__mqtt_client.on_connect = self.__on_connect
#         self.__mqtt_client.on_disconnect = self.__on_disconnect
#         self.__mqtt_client.on_message = self.__on_message
#         self.__mqtt_host = mqtt_host
#         self.__mqtt_port = mqtt_port
#         self.__subscriber_thread = Thread(target=self.__worker,
#                                           daemon=True)
#         self.__stop_worker = Event()

#     def start_listening(self) -> None:
#         """ Start listening for published events.
#         """
#         # Connect to the database
#         self.__model.connect()

#         # In the client is already connected then stop here.
#         if self.__connected:
#             return

#         # Connect to the host given in initializer.
#         self.__mqtt_client.connect(self.__mqtt_host,
#                                    self.__mqtt_port)
#         self.__mqtt_client.loop_start()
#         # Subscribe to all topics given in the initializer.
#         self.__mqtt_client.subscribe(self.ALL_TOPICS)
#         # Start the subscriber thread.
#         self.__subscriber_thread.start()

#     def stop_listening(self) -> None:
#         """ Stop listening for published events.
#         """
#         self.__stop_worker.set()
#         self.__mqtt_client.loop_stop()
#         self.__mqtt_client.unsubscribe(self.ALL_TOPICS)
#         self.__mqtt_client.disconnect()

#         # Disconnect from the database
#         self.__model.disconnect()

#     def __on_connect(self, client, userdata, flags, rc) -> None:
#         """ Callback invoked when a connection with the MQTT broker is established.

#         Refer to paho-mqtt documentation for more information on this callback:
#         https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#callbacks
#         """

#         # Set connected flag to true. This is later used if multiple calls to connect are made. This
#         # way the user does not need to very if the client is connected.
#         self.__connected = True
#         print("MQTT client connected")

#     def __on_disconnect(self, client, userdata, rc) -> None:
#         """ Callback invoked when the client disconnects from the MQTT broker occurs.

#         Refer to paho-mqtt documentation for more information on this callback:
#         https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#callbacks
#         """

#         # Set connected flag to false. This is later used if multiple calls to connect are made.
#         # This way the user does not need to very if the client is connected.
#         self.__connected = False
#         print("MQTT client disconnected")

#     def __on_message(self, client, userdata, message: MQTTMessage) -> None:
#         """ Callback invoked when a message has been received on a topic that the client subscribed.

#         Refer to paho-mqtt documentation for more information on this callback:
#         https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#callbacks
#         """

#         # Push a message to the queue. This will later be processed by the worker.
#         self.__events_queue.put(message)

#     def __worker(self) -> None:
#         """ This method pulls zigbee2mqtt messages from the queue of received messages, pushed when
#         a message is received, i.e. by the __on_message() callback. This method will be stopped when
#         the instance of zigbee2mqttClient disconnects, i.e. disconnect() is called and sets the
#         __stop_worker event.
#         """
#         while not self.__stop_worker.is_set():
#             try:
#                 # Pull a message from the queue.
#                 message = self.__events_queue.get(timeout=1)
#             except Empty:
#                 # This exception is raised when the queue pull times out. Ignore it and retry a new
#                 # pull.
#                 pass
#             else:
#                 # If a message was successfully pulled from the queue, then process it.
#                 # NOTE: this else condition is part of the try and it is executed when the action
#                 # inside the try does not throws and exception.
#                 # The decode() transforms a byte array into a string, following the utf-8 encoding.
#                 if not message:
#                     return

#                 if message.topic == self.STORE_EVENTS_TOPIC:
#                     try:
#                         event = Cep2EvemanEvent.from_json(message.payload.decode("utf-8"))
#                         print(f"Storing event {event}")

#                         #her blir den gemt i db
#                         self.__model.store(event)


#                     except KeyError:
#                         print(f"Malformed JSON event: {message}")
#                 elif message.topic == self.GET_EVENTS_REQUEST_TOPIC:
#                     # Try to parse a json message with a payload of such as
#                     # {"deviceId": "0x588e81fffe"}
#                     # If a JSON payload is found, then it is parsed and the deviceId is used to
#                     # retrive the events for this device. Other filter arugmetns can be addded here.
#                     # If the payload has unknown keys, then the deviceId is None and all events are
#                     # returned.
#                     try:
#                         json_obj = json.loads(message.payload.decode("utf-8"))
#                     except json.JSONDecodeError as ex:
#                         if message.payload:
#                             print(f"Couldn't parse the JSON payload: {ex}")
#                         device_id = None
#                     else:
#                         device_id = json_obj.get("deviceId")
#                     # A get_events was received. thus retrieve the values from the database and
#                     # publish them to the response topic.
#                     events = [e.to_json() for e in self.__model.get_events(device_id)]

#                     publish.single(hostname=self.__mqtt_host,
#                                    port=self.__mqtt_port,
#                                    topic=self.GET_EVENTS_RESPONSE_TOPIC,
#                                    payload=json.dumps(events))



def main():
    #stop_daemon = Event()

    #def shutdown(signal, frame):
    #    stop_daemon.set()

    # Subscribe to signals sent from the terminal, so that the application is shutdown properly.
    # When one of the trapped signals is captured, the function shutdown() will be execute. This
    # will set the stop_daemon event that will then stop the loop that keeps the application running.
    #signal.signal(signal.SIGHUP, shutdown)
    #signal.signal(signal.SIGINT, shutdown)
    #signal.signal(signal.SIGTERM, shutdown)

    # Instantiate the model to connect to a database running in the same machine (localhost).
    model = DB(host="192.168.32.97",
                            database="group1lightguide",
                            user="sodeChristian",
                            password="1234")
    # The controller will connect to a MQTT broker running in the same machine.
    #controller = Cep2EvemanController(model=model,
    #                                  mqtt_host="localhost")

    #controller.start_listening()
    #while not stop_daemon.is_set():
        # The event times out evey 60 seconds, or when the event is set. If it is set, then the loop
        # will stop and the application will exit.
    #    stop_daemon.wait(60)

    #controller.stop_listening()


    #example usage
    log = LogEntry(
        device_id = "Kitchen",
        loglevel = "Informational",
        timestamp = datetime.now(),
        measurement = "120",
        device_type="sensor",
        type_= "Movement"
    )
    

    model.connect()
    model.InsertLog(log=log)
    settings = model.getSettings()
    print(settings)


    model.disconnect()

    print("done")


if __name__ == "__main__":
    main()
