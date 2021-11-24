from typing import Tuple, List, Optional, Sequence

from led_machine.alter import Alter, Position, LedMetadata
from led_machine.color import ColorAlias, Color, ColorConstants
from led_machine.percent import PercentGetter


class AlterBlock(Alter):
    def __init__(self, block_list: Sequence[Tuple[Optional[ColorAlias], int]], percent_getter: PercentGetter, fade: bool = True):
        self.block_list: List[Tuple[Optional[Color], int]] = [(None if alias is None else Color.from_alias(alias), width) for alias, width in block_list]
        self.percent_getter = percent_getter
        self.total_width = sum(width for _, width in block_list)
        self.fade = fade

    def _get_color(self, pixel: int) -> Optional[Color]:
        offset = 0
        for block in self.block_list:
            color, width = block
            if pixel < width + offset:
                return color
            offset += width
        raise AssertionError("This shouldn't happen! pixel must be out of bounds! pixel: {}".format(pixel))

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        percent = self.percent_getter.get_percent(seconds)
        offset = percent * self.total_width
        pixel_to_get = (pixel_position + offset) % self.total_width
        low_pixel = int(pixel_to_get)
        high_pixel = (low_pixel + 1) % self.total_width
        lerp_percent = pixel_to_get % 1  # 0 is full low_pixel, 1.0, is full high_pixel

        low_pixel_color: Optional[Color] = self._get_color(low_pixel) or current_color
        high_pixel_color: Optional[Color] = self._get_color(high_pixel) or current_color

        if low_pixel_color is None and high_pixel_color is None:
            return None
        if low_pixel_color is None:
            low_pixel_color = ColorConstants.BLACK
        if high_pixel_color is None:
            high_pixel_color = ColorConstants.BLACK

        if not self.fade:
            if round(lerp_percent) == 1:
                return high_pixel_color
            return low_pixel_color
        return low_pixel_color.lerp(high_pixel_color, lerp_percent)
