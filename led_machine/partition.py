from typing import Optional, List, Tuple

from led_machine.color import Color
from led_machine.settings import LedSetting
from led_machine.util import copy_pixels_list, clear_pixels_list


class PartitionSetting(LedSetting):
    def __init__(self, setting: Optional[LedSetting], override_list: List[Tuple[LedSetting, List[Tuple[int, int]]]]):
        """
        :param setting: The base setting
        :param override_list: A list of tuples where tuple[0] is the setting, and tuple[1] is a list of tuples of (int, int),
        where the first int is the start, and the second is the length of the partition
        """
        self.setting: Optional[LedSetting] = setting
        self.override_list = override_list

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        # This is going to be similar code to AlterPixelSetting
        # Note that this code isn't the best. This code right here shows that the LedSetting abstraction doesn't work well in some cases
        pixels_list_base_copy = copy_pixels_list(pixels_list)
        pixels_list_partition_copy = copy_pixels_list(pixels_list)
        if self.setting is not None:
            # Apply the base setting directly to the real pixels
            self.setting.apply(seconds, pixels_list_base_copy)
        for list_index, (pixels, pixels_base_copy, pixels_partition_copy) in enumerate(zip(pixels_list, pixels_list_base_copy, pixels_list_partition_copy)):
            last_override_setting: Optional[LedSetting] = None
            for i in range(len(pixels)):
                override_setting: Optional[LedSetting] = None
                for setting, partitions in self.override_list:
                    if any(start <= i < start + length for start, length in partitions):
                        override_setting = setting
                        break

                override_color: Optional[Color] = None
                if override_setting is not None and last_override_setting != override_setting:
                    clear_pixels_list(pixels_list_partition_copy)
                    override_setting.apply(seconds, pixels_list_partition_copy)  # This will affect pixels_partition_copy
                    override_color = pixels_partition_copy[i]
                base_color = override_color or pixels_base_copy[i]
                pixels[i] = base_color
