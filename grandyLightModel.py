from dataclasses import dataclass
from typing import List, Optional, Union

@dataclass
class grandyLightZigbeeDevice:
    id_: str
    type_: str


class grandyLightModel:
    def __init__(self):
        self.__devices = {}

    @property
    def actuators_list(self) -> List[grandyLightZigbeeDevice]:
        return list(filter(lambda s: s.type_ in {"led", "power plug"},
                           self.__devices.values()))

    @property
    def devices_list(self) -> List[grandyLightZigbeeDevice]:
        return list(self.__devices.values())

    @property
    def sensors_list(self) -> List[grandyLightZigbeeDevice]:
        return list(filter(lambda s: s.type_ in {"pir"},
                           self.__devices.values()))

    def add(self, device: Union[grandyLightZigbeeDevice, List[grandyLightZigbeeDevice]]) -> None:
        list_devices = [device] if isinstance(device, grandyLightZigbeeDevice)\
            else device

        for s in list_devices:
            self.__devices[s.id_] = s

    def find(self, device_id: str) -> Optional[grandyLightZigbeeDevice]:
        
        devices = list(filter(lambda kv: kv[0] == device_id,
                              self.__devices.items()))
        return devices[0][1] if len(devices) >= 1 else None