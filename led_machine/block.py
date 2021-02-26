from typing import Tuple, List, Optional

from led_machine.percent import PercentGetter
from led_machine.settings import LedSetting, AlterPixelSetting


class BlockSetting(AlterPixelSetting):
    def __init__(self, setting: Optional[LedSetting], block_list: List[Tuple[Optional[Tuple], int]],
                 percent_getter: PercentGetter):
        super().__init__(setting)
        self.block_list = block_list
        self.percent_getter = percent_getter
        self.total_width = sum(width for _, width in block_list)

    def _get_color(self, pixel: int) -> Optional[Tuple]:
        offset = 0
        for block in self.block_list:
            color, width = block
            if pixel < width + offset:
                return color
            offset += width
        raise AssertionError("This shouldn't happen! pixel must be out of bounds! pixel: {}".format(pixel))

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels,
              pixel_color: Optional) -> Optional[Tuple[int, int, int]]:
        percent = self.percent_getter.get_percent(seconds)
        offset = percent * self.total_width
        pixel_to_get = (pixel_index + offset) % self.total_width
        low_pixel = int(pixel_to_get)
        high_pixel = (low_pixel + 1) % self.total_width
        lerp_percent = pixel_to_get % 1  # 0 is full low_pixel, 1.0, is full high_pixel

        low_pixel_color = self._get_color(low_pixel) or pixel_color
        high_pixel_color = self._get_color(high_pixel) or pixel_color

        if low_pixel_color is None and high_pixel_color is None:
            return None
        if low_pixel_color is None:
            low_pixel_color = (0, 0, 0)
        if high_pixel_color is None:
            high_pixel_color = (0, 0, 0)

        return (int(low_pixel_color[0] * (1 - lerp_percent) + high_pixel_color[0] * lerp_percent),
                int(low_pixel_color[1] * (1 - lerp_percent) + high_pixel_color[1] * lerp_percent),
                int(low_pixel_color[2] * (1 - lerp_percent) + high_pixel_color[2] * lerp_percent),
                )
