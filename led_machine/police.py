from typing import List, Optional

from led_machine.color import Color
from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting


class PoliceSetting(LedSetting):
    def __init__(self, percent_getter: PercentGetter):
        self.percent_getter: PercentGetter = percent_getter
        self.blue = Color.from_bytes(0, 0, 190)
        self.red = Color.from_bytes(255, 0, 0)
        self.white = Color.from_bytes(180, 180, 180)

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        percent = self.percent_getter.get_percent(seconds)

        if percent < .5:
            left = self.blue
            right = self.white
        else:
            left = self.white
            right = self.red

        for pixels in pixels_list:
            length = len(pixels)
            half_index = length // 2
            for i in range(0, half_index):
                pixels[i] = left
            for i in range(half_index, length):
                pixels[i] = right
