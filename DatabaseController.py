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
            host="192.168.181.4",
            database="grandyLightProjectAdminG1",
            user="Thomas",
            password="1234"
        )
    
    def tryconnect(self):
        counter : int
        counter = 5
        while (not self.db.get_status() and counter >= 0):
            print("Attempting to connect to Database...")
            counter-=1

            try:
                self.db.connect()
            
                
            except Exception as e:
                pass
               
        return
    #connect to db and start posting logs
    def start(self):
        connectThread = threading.Thread(target=self.tryconnect)
        connectThread.start()
        connectThread.join()
        postThread = threading.Thread(target=self.postLogs)
        postThread.start()

    def disconnect(self):
        self.db.disconnect()

    def getSettings(self):
        
        if (self.db.get_status()):
            return self.db.getSettings()
        else:
            print("No Connection to Database. Standard Settings applied.")
            #Timeout values given in minutes
            return Settings(bathroom_timeout=2,bedroom_timeout=0.5,default_timeout=1,start="22:00",end="09:00")
    
    def queueLog(self, log):
        self.logs.append(log)
    
    def postLogs(self):
        while True:
            if self.logs and self.db.get_status():
                if len(self.logs) > 200:
                    raise Exception("buffer is full")
                try:
                    log = self.logs.pop(0)
                    self.db.InsertLog(log)
                    print("posted log")
                except Exception as e:
                        print(e)
            else:
                self.tryconnect()
            
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
