from abc import abstractmethod, ABC
from typing import Tuple, Optional

from led_machine.util import copy_pixels_list


class LedSetting(ABC):
    @abstractmethod
    def apply(self, seconds: float, pixels_list: list):
        pass


class LedSettingHolder(LedSetting):
    def __init__(self, setting: LedSetting):
        self.setting: LedSetting = setting

    def apply(self, seconds: float, pixels_list: list):
        self.setting.apply(seconds, pixels_list)


class AlterPixelSetting(LedSetting, ABC):
    def __init__(self, setting: LedSetting):
        self.setting = setting

    @abstractmethod
    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels, pixel_color) -> Tuple[int, int, int]:
        pass

    def apply(self, seconds: float, pixels_list: list):
        pixels_list_copy = copy_pixels_list(pixels_list)
        self.setting.apply(seconds, pixels_list_copy)
        for list_index, (pixels, pixels_copy) in enumerate(zip(pixels_list, pixels_list_copy)):
            for i in range(len(pixels)):
                copied = pixels_copy[i]
                if copied is not None:
                    pixels[i] = self.alter(seconds, list_index, i, pixels, copied)


class DimSetting(AlterPixelSetting):
    def __init__(self, setting: LedSetting, dim: float, pixel_range: Optional[Tuple[int, int]] = None):
        super().__init__(setting)
        self.dim = dim
        self.pixel_range = pixel_range

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels, pixel_color) -> Tuple[int, int, int]:
        dim_setting = 1
        if self.pixel_range is None or self.pixel_range[0] <= pixel_index <= self.pixel_range[1]:
            dim_setting = self.dim
        return pixel_color[0] * dim_setting, pixel_color[1] * dim_setting, pixel_color[2] * dim_setting


class FrontDimSetting(AlterPixelSetting):
    def __init__(self, setting: LedSetting):
        super().__init__(setting)

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels, pixel_color) -> Tuple[int, int, int]:
        dim_amount = 1
        if pixel_index < 50:
            dim_amount *= pixel_index / 50
        return pixel_color[0] * dim_amount, pixel_color[1] * dim_amount, pixel_color[2] * dim_amount


class SolidSetting(LedSetting):
    def __init__(self, color):
        self.color = color

    def apply(self, seconds: float, pixels_list: list):
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = self.color

