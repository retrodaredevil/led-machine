from typing import List, Optional, Sequence

from led_machine.alter import Alter, Position, LedMetadata
from led_machine.color import ColorAlias, Color
from led_machine.percent import PercentGetter


class AlterFade(Alter):

    def __init__(self, percent_getter: PercentGetter, colors: Sequence[ColorAlias], led_spread: float):
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

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        percent = self.percent_getter.get_percent(seconds)
        return self._get_color((percent + pixel_position / self.led_spread) % 1)
