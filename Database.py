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
from DBmodels import LogEntry, Settings


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

        # Try to connect to the database. If the connection fails, then raise an exception.
        
        
        self.__mysql_connection = mysql_connect(
                host=self.__host,
                database=self.__database,
                user=self.__user,
                password=self.__password,
                connect_timeout=1
            )
        

    def get_status(self):
        return self.__mysql_connection
        

    def disconnect(self):
        """ Disconnect from the database.
        """
        self.__mysql_connection.close()
        self.__mysql_connection = None


    def InsertLog(self, log: LogEntry) -> None:
        if not self.__mysql_connection:
            raise RuntimeError(f"Not connected to database {self.__database}.")

        # timestamp - loglevel message
        query = ("INSERT INTO event (timestamp_,loglevel,type_,measurement,device_id,device_type)"
                 "VALUES(%s, %s, %s, %s,%s,%s);")
        cursor = self.__mysql_connection.cursor()

        cursor.execute(query, (log.timestamp, log.loglevel, log.type_, log.measurement, log.device_id, log.device_type))
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
        obj = Settings(start=settings[-1][0], end=settings[-1][1], default_timeout=settings[-1][4], bathroom_timeout=settings[-1][3], bedroom_timeout=settings[-1][2])
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
