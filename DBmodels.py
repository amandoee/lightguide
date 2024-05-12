import datetime

class Settings:
    start : str
    end : str
    default_timeout : int
    bathroom_timeout : int

    def __init__(self, start:str, end:str, default_timeout:int, bathroom_timeout:int, bedroom_timeout:int) -> None:
        self.start = start
        self.end = end
        self.default_timeout = default_timeout
        self.bathroom_timeout = bathroom_timeout
        self.bedroom_timeout = bedroom_timeout



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