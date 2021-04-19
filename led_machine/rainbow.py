import math
from typing import List, Optional

from led_machine.color import Color
from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting


class RainbowSetting(LedSetting):
    def __init__(self, percent_getter: PercentGetter, led_spread: int):
        self.percent_getter: PercentGetter = percent_getter
        self.led_spread = led_spread

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        percent = self.percent_getter.get_percent(seconds)

        led_spread = self.led_spread
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = get_rainbow((percent + i / led_spread) % 1)


def get_rainbow(percent: float) -> Color:
    spot = int(percent * 6)
    sub = (percent * 6) % 1
    cosine_adjust = 1 - (math.cos(sub * math.pi) + 1) / 2
    amount = (sub + cosine_adjust) / 2.0
    if spot == 0:  # add red
        return Color(amount, 1.0, 0.0)
    elif spot == 1:  # remove green
        return Color(1.0, 1.0 - amount, 0.0)
    elif spot == 2:  # add blue
        return Color(1.0, 0.0, amount)
    elif spot == 3:  # remove red
        return Color(1 - amount, 0.0, 1.0)
    elif spot == 4:  # add green
        return Color(0.0, amount, 1.0)
    else:  # remove blue
        return Color(0.0, 1.0, 1.0 - amount)


if __name__ == '__main__':
    # Just some code to get the exact color of solid rainbow at a given time.
    millis = 1618793494672 - 5000
    print(get_rainbow((millis / 1000 * 0.001) % 1))
