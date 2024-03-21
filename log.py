import time

class LogEntry:

    def __init__(self, msg, log) -> None:
        self.timestamp = time.time()
        self.loglevel = log
        self.message = msg

    timestamp : str
    loglevel : str
    message : str








