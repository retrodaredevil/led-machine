from typing import List, Optional

from led_machine.color import ColorAlias, Color
from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting


class FadeSetting(LedSetting):
    def __init__(self, percent_getter: PercentGetter, colors: List[ColorAlias], led_spread: int):
        self.percent_getter: PercentGetter = percent_getter
        self.colors: List[Color] = [Color.from_alias(color) for color in colors]
        self.led_spread = led_spread

    def _get_color(self, percent: float) -> Color:
        # a value of 0.0 should give exactly self.colors[0]
        offset = percent * len(self.colors)
        left_index = int(offset)
        right_index = (left_index + 1) % len(self.colors)
        lerp_percent = offset % 1.0
        return self.colors[left_index].lerp(self.colors[right_index], lerp_percent)

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        percent = self.percent_getter.get_percent(seconds)

        led_spread = self.led_spread
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = self._get_color((percent + i / led_spread) % 1)
