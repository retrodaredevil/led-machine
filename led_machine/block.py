from typing import Tuple, List, Optional

from led_machine.color import ColorAlias, Color, ColorConstants
from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting, AlterPixelSetting


class BlockSetting(AlterPixelSetting):
    def __init__(self, setting: Optional[LedSetting], block_list: List[Tuple[Optional[ColorAlias], int]],
                 percent_getter: PercentGetter):
        super().__init__(setting)
        self.block_list: List[Tuple[Optional[Color], int]] = [(None if alias is None else Color.from_alias(alias), width) for alias, width in block_list]
        self.percent_getter = percent_getter
        self.total_width = sum(width for _, width in block_list)

    def _get_color(self, pixel: int) -> Optional[Color]:
        offset = 0
        for block in self.block_list:
            color, width = block
            if pixel < width + offset:
                return color
            offset += width
        raise AssertionError("This shouldn't happen! pixel must be out of bounds! pixel: {}".format(pixel))

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels,
              pixel_color: Optional[Color]) -> Optional[Color]:
        percent = self.percent_getter.get_percent(seconds)
        offset = percent * self.total_width
        pixel_to_get = (pixel_index + offset) % self.total_width
        low_pixel = int(pixel_to_get)
        high_pixel = (low_pixel + 1) % self.total_width
        lerp_percent = pixel_to_get % 1  # 0 is full low_pixel, 1.0, is full high_pixel

        low_pixel_color: Optional[Color] = self._get_color(low_pixel) or pixel_color
        high_pixel_color: Optional[Color] = self._get_color(high_pixel) or pixel_color

        if low_pixel_color is None and high_pixel_color is None:
            return None
        if low_pixel_color is None:
            low_pixel_color = ColorConstants.BLACK
        if high_pixel_color is None:
            high_pixel_color = ColorConstants.BLACK

        return low_pixel_color.lerp(high_pixel_color, lerp_percent)
