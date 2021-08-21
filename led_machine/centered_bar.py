from typing import Optional

from led_machine.color import Color, ColorConstants
from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting, AlterPixelSetting


class CenteredBarSetting(AlterPixelSetting):
    def __init__(self, setting: Optional[LedSetting], percent_getter: PercentGetter, half_bar_width: int):
        super().__init__(setting)
        self.percent_getter = percent_getter
        self.half_bar_width = half_bar_width

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels, pixel_color: Optional[Color]) -> Optional[Color]:
        if pixel_color is None:
            return None
        percent = self.percent_getter.get_percent(seconds)
        index_modded = pixel_index % (self.half_bar_width * 2)
        index = abs(self.half_bar_width - index_modded)
        pixel_percent = index / self.half_bar_width
        if pixel_percent > percent:
            return ColorConstants.BLACK
        return pixel_color
