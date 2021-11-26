from typing import Optional, Sequence, Tuple

from led_machine.alter import Alter, Position, LedMetadata
from led_machine.color import Color, ColorConstants
from led_machine.percent import PercentGetter


class AlterBlend(Alter):

    def __init__(self, percent_getter: PercentGetter, alters: Sequence[Alter]):
        self.percent_getter: PercentGetter = percent_getter
        self.alters = alters

    def _get_alter(self, percent: float) -> Tuple[Alter, Alter, float]:
        # a value of 0.0 should give exactly self.colors[0]
        offset = percent * len(self.alters)
        left_index = int(offset)
        right_index = (left_index + 1) % len(self.alters)
        lerp_percent = offset % 1.0
        # return self.alters[left_index].lerp(self.colors[right_index], lerp_percent)
        return self.alters[left_index], self.alters[right_index], lerp_percent

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        percent = self.percent_getter.get_percent(seconds)
        left_alter, right_alter, lerp_percent = self._get_alter(percent)
        left_color = left_alter.alter_pixel(seconds, pixel_position, current_color, metadata) or current_color or ColorConstants.BLACK
        right_color = right_alter.alter_pixel(seconds, pixel_position, current_color, metadata) or current_color or ColorConstants.BLACK
        return left_color.lerp(right_color, lerp_percent)
