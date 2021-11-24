from typing import Optional, List, Tuple, Sequence

from led_machine.alter import Alter, Position, LedMetadata
from led_machine.color import Color


class AlterPartition(Alter):
    def __init__(self, override_list: Sequence[Tuple[Alter, Sequence[Tuple[Position, Position]]]]):
        """
        :param setting: The base setting
        :param override_list: A list of tuples where tuple[0] is the setting, and tuple[1] is a list of tuples of (int, int),
        where the first int is the start, and the second is the length of the partition
        """
        self.override_list = override_list

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        override_setting: Optional[Alter] = None
        for setting, partitions in self.override_list:
            if any(start <= pixel_position < start + length for start, length in partitions):
                override_setting = setting
                break

        if override_setting is not None:
            return override_setting.alter_pixel(seconds, pixel_position, current_color, metadata)
        return current_color
