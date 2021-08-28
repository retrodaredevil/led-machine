import math
import time
import random
from typing import List, Optional, Tuple, Dict

from led_machine.color import Color, ColorConstants
from led_machine.settings import AlterPixelSetting, LedSetting


class Twinkle:
    def __init__(self, peak_point_seconds: float, fade_duration_seconds: float):
        self.peak_point_seconds = peak_point_seconds
        self.fade_duration_seconds = fade_duration_seconds

    def get_brightness(self, seconds: float) -> float:
        distance = abs(seconds - self.peak_point_seconds)
        return max(0.0, 1 - distance / self.fade_duration_seconds)

    def is_stale(self, seconds: float) -> bool:
        return self.peak_point_seconds + self.fade_duration_seconds < seconds


class TwinkleSetting(AlterPixelSetting):
    SECTION_LENGTH = 20

    def __init__(self, setting: LedSetting, min_percent_to_light_up: float, max_percent_to_light_up: float):
        super().__init__(setting)
        self.min_percent_to_light_up = min_percent_to_light_up
        self.max_percent_to_light_up = max_percent_to_light_up
        self.twinkle_map: Dict[Tuple[int, int], List[Twinkle]] = {}
        self.last_update: Optional[float] = None

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        now = time.time()
        if self.last_update is not None and self.last_update > now:  # someone changed the speed on us, so just reset and update no matter what
            self.last_update = None
        if self.last_update is None or self.last_update + 1 < now:
            self.last_update = now
            for list_index in range(len(pixels_list)):
                number_of_pixels = len(pixels_list[list_index])
                number_of_sections = int(math.ceil(number_of_pixels / self.__class__.SECTION_LENGTH))
                for section_index in range(number_of_sections):
                    pixel_index_start = section_index * self.__class__.SECTION_LENGTH
                    pixel_index_end = pixel_index_start + self.__class__.SECTION_LENGTH  # (Exclusive)
                    indices = list(range(pixel_index_end, pixel_index_end))
                    random.shuffle(indices)
                    number_to_light_up = random.randint(
                        round(self.__class__.SECTION_LENGTH * self.min_percent_to_light_up),
                        round(self.__class__.SECTION_LENGTH * self.max_percent_to_light_up)
                    )
                    for pixel_index in indices[0:number_to_light_up]:
                        key = (list_index, pixel_index)
                        time_offset = random.uniform(0.5, 1.5)
                        peak_point_seconds = now + time_offset
                        if key in self.twinkle_map:
                            twinkle_list = self.twinkle_map[key]
                        else:
                            twinkle_list = []
                            self.twinkle_map[key] = twinkle_list
                        twinkle_list.append(Twinkle(peak_point_seconds, 0.3))
        super().apply(seconds, pixels_list)

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels: List[Optional[Color]], pixel_color: Optional[Color]) -> Optional[Color]:
        key = (list_index, pixel_index)
        twinkle_list = self.twinkle_map.get(key)
        if twinkle_list is None:
            return ColorConstants.BLACK
        to_remove = []
        max_brightness = 0.0
        for twinkle in twinkle_list:
            if twinkle.is_stale(seconds):
                to_remove.append(twinkle)
            brightness = twinkle.get_brightness(seconds)
            max_brightness = max(max_brightness, brightness)

        return pixel_color * max_brightness

