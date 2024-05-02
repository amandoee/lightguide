import Cep2Eveman
from DBmodels import LogEntry, Settings
import datetime
import threading
import time



class DBController:
    db = None 
    
    #queue of logs
    logs = []

    def __init__(self):
        self.db = Cep2Eveman.DB(
            host="192.168.32.97",
            database="group1lightguide",
            user="sodeChristian",
            password="1234"
        )
    

    #connect to db and start posting logs
    def start(self): 
        self.db.connect()
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
            if self.logs:
                if len(self.logs) > 200:
                    raise Exception("buffer is full")
                try:
                    self.db.InsertLog(self.logs[0])
                    self.logs.pop(0)
                except:
                    pass
            
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

    for i in range(4):
        controller.queueLog(log)
    controller.start()


if __name__ == "__main__":
    main()
