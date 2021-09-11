from abc import abstractmethod, ABC
from typing import Tuple, Optional, List

from led_machine.color import Color, ColorAlias
from led_machine.util import copy_pixels_list


class LedSetting(ABC):
    @abstractmethod
    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        pass


class DoNothingLedSetting(LedSetting):
    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        pass


class LedSettingHolder(LedSetting):
    def __init__(self, setting: LedSetting):
        self.setting: LedSetting = setting

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        self.setting.apply(seconds, pixels_list)


class AlterPixelSetting(LedSetting, ABC):
    def __init__(self, setting: Optional[LedSetting]):
        self.setting: Optional[LedSetting] = setting

    @abstractmethod
    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels: List[Optional[Color]],
              pixel_color: Optional[Color]) -> Optional[Color]:
        pass

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        pixels_list_copy = copy_pixels_list(pixels_list)
        if self.setting is not None:
            self.setting.apply(seconds, pixels_list_copy)
        for list_index, (pixels, pixels_copy) in enumerate(zip(pixels_list, pixels_list_copy)):
            for i in range(len(pixels)):
                copied = pixels_copy[i]
                pixels[i] = self.alter(seconds, list_index, i, pixels, copied)


class DimSetting(AlterPixelSetting):
    def __init__(self, setting: LedSetting, dim: float, pixel_range: Optional[Tuple[int, int]] = None):
        super().__init__(setting)
        self.dim = float(dim)
        self.pixel_range = pixel_range

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels,
              pixel_color: Optional[Color]) -> Optional[Color]:
        if pixel_color is None:
            return None
        dim_setting = 1.0
        if self.pixel_range is None or self.pixel_range[0] <= pixel_index <= self.pixel_range[1]:
            dim_setting = self.dim
        return pixel_color.scale(dim_setting)


class FrontDimSetting(AlterPixelSetting):
    def __init__(self, setting: LedSetting):
        super().__init__(setting)

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels,
              pixel_color: Optional[Color]) -> Optional[Color]:
        if pixel_color is None:
            return None
        dim_amount = 1.0
        if pixel_index < 50:
            dim_amount *= pixel_index / 50
        return pixel_color.scale(dim_amount)


class SolidSetting(LedSetting):
    def __init__(self, color: ColorAlias):
        self.color = Color.from_alias(color)

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = self.color

