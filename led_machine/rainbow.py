from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting
from typing import Tuple


class RainbowSetting(LedSetting):
    def __init__(self, percent_getter: PercentGetter, led_spread: int):
        self.percent_getter: PercentGetter = percent_getter
        self.led_spread = led_spread

    def apply(self, seconds: float, pixels_list: list):
        percent = self.percent_getter.get_percent(seconds)

        for pixels in pixels_list:
            for i in range(len(pixels)):
                color = get_rainbow((percent + i / self.led_spread) % 1)
                r = color[0] / 255
                g = color[1] / 255
                b = color[2] / 255
                dim_amount = 1
                pixels[i] = (int(dim_amount * r * 255), int(dim_amount * g * 255), int(dim_amount * b * 255))


def get_rainbow(percent: float) -> Tuple:
    spot = int(percent * 6)
    sub = (percent * 6) % 1
    amount = int(256 * sub)
    if spot == 0:  # add red
        return amount, 255, 0
    elif spot == 1:  # remove green
        return 255, 255 - amount, 0
    elif spot == 2:  # add blue
        return 255, 0, amount
    elif spot == 3:  # remove red
        return 255 - amount, 0, 255
    elif spot == 4:  # add green
        return 0, amount, 255
    else:  # remove blue
        return 0, 255, 255 - amount
