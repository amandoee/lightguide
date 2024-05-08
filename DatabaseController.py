import Database
from DBmodels import LogEntry, Settings
import datetime
import threading
import time



class DBController:
    db = None 
    
    #queue of logs
    logs = []

    def __init__(self):
        self.db = Database.DB(
            host="192.168.89.97",
            database="group1lightguide",
            user="sodeChristian",
            password="1234"
        )
    
    
    def reconnect(self):
        while True:
            print("Trying to connect to database")
            try:
                self.db.connect()
                return
            except Exception as e:
                if "2003" in str(e):
                    print("Connection refused, trying again in 5 seconds")
                    time.sleep(5)

    #connect to db and start posting logs
    def start(self):
        self.reconnect()
        postThread = threading.Thread(target=self.postLogs)
        postThread.start()
    
    def disconnect(self):
        self.db.disconnect()

    def getSettings(self):
        return self.db.getSettings()
    
    def queueLog(self, log):
        self.logs.append(log)
    
    def postLogs(self):
        while True:
            print("test")
            if self.logs:
                if len(self.logs) > 200:
                    raise Exception("buffer is full")
                try:
                    log = self.logs.pop(0)
                    self.db.InsertLog(log)
                    print("posted log")
                except Exception as e:
                        print("Lost connection to database, trying to reconnect")
                        self.reconnect()
            
            time.sleep(10)


#create a main function to test the controller
def main():
    controller = DBController()
    log = LogEntry(
        device_id = "test",
        loglevel = "test",
        timestamp = datetime.datetime.now(),
        measurement = "120",
        device_type="sensor",
        type_= "Movement"
    )

    controller.start()
    for i in range(4):
        controller.queueLog(log)
   


if __name__ == "__main__":
    main()
