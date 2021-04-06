from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting


class PoliceSetting(LedSetting):
    def __init__(self, percent_getter: PercentGetter):
        self.percent_getter: PercentGetter = percent_getter
        self.blue = (0, 0, 255)
        self.red = (190, 0, 0)
        self.white = (180, 180, 180)

    def apply(self, seconds: float, pixels_list: list):
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
