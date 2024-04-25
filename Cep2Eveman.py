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

class Settings:
    start : str
    end : str
    default_timeout : int
    bathroom_timeout : int

    def __init__(self, start:str, end:str, default_timeout:int, bathroom_timeout:int) -> None:
        self.start = start
        self.end = end
        self.default_timeout = default_timeout
        self.bathroom_timeout = bathroom_timeout



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

    
    def getSettings(self) -> Settings:
        """ Retrieve settings from the database. """
        if not self.__mysql_connection:
            raise RuntimeError(f"Not connected to database {self.__database}.")

        #get all settings
        query = ("SELECT * FROM settings;")
        cursor = self.__mysql_connection.cursor()
        cursor.execute(query)

        settings = cursor.fetchall()
        #print(settings)
        #create settings object
        obj = Settings(start=settings[-1][0], end=settings[-1][1], default_timeout=settings[-1][2], bathroom_timeout=settings[-1][3])
        cursor.close()

        return obj





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
    SystemSettings = model.getSettings() #needs conversion into correct format for use
    print(SystemSettings.start)

    model.disconnect()

    print("done")


if __name__ == "__main__":
    main()
