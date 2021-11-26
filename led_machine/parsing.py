from abc import ABC, abstractmethod
from typing import Final, List

from led_machine.alter import Alter
from led_machine.parse import StaticToken

PARTITION_TOKEN = StaticToken("partition", "|")
BLEND_TOKEN = StaticToken("blend", "~")


class AlterCreator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create(self, start_pixel: int, pixel_count: int) -> Alter:
        pass



