import Database
from DBmodels import LogEntry, Settings
import datetime
import threading
import time



class DBController:
    db : Database.DB 
    
    #queue of logs
    logs = []

    def __init__(self):
        self.db = Database.DB(
            host="192.168.89.97",
            database="group1lightguide",
            user="sodeChristian",
            password="1234"
        )
    
    def tryconnect(self):
        while (not self.db.get_status()):
            try:
                self.db.connect()
                
            except Exception as e:
                pass
                #print(e)

            time.sleep(2)
        return
    #connect to db and start posting logs
    def start(self):
        connectThread = threading.Thread(target=self.tryconnect)
        connectThread.start()
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
            print(self.logs)
            if self.logs:
                if len(self.logs) > 200:
                    raise Exception("buffer is full")
                try:
                    log = self.logs.pop(0)
                    self.db.InsertLog(log)
                    print("posted log")
                except Exception as e:
                        print(e)
            
            time.sleep(2)


#create a main function to test the controller
def main():
    controller = DBController()
    log = LogEntry(
        device_id = "dbtester",
        loglevel = "test",
        timestamp = datetime.datetime.now(),
        measurement = "120",
        device_type="sensor",
        type_= "Movement"
    )

    controller.start()
    for i in range(30):
        controller.queueLog(log)
        print("IM NOT STUCK")
        time.sleep(2)
   




if __name__ == "__main__":
    main()
