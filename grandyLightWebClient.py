import json
from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class grandyLightWebDeviceEvent:
    device_id: str
    device_type: str
    measurement: Any

    def to_json(self) -> str:
        # The dumps() function serializes an object to a JSON string. In this case, it serializes a
        # dictionary.
        return json.dumps({"deviceId": self.device_id,
                           "deviceType": self.device_type,
                           "measurement": self.measurement})


class grandyLightWebClient:

    def __init__(self, host: str) -> None:
        self.__host = host

    def send_event(self, event: str) -> int:
        
        try:
            response = requests.post(self.__host, data=event)

            return response.status_code
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Error connecting to {self.__host}")
