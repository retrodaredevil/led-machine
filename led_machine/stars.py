from random import randint, uniform
from typing import Optional, Tuple, List

from led_machine.settings import LedSetting, AlterPixelSetting

MAX_DELTA = 0.3
STAR_PER_PIXEL = 1 / 12


class Star:
    def __init__(self):
        self.position: float = 0.0
        self.velocity: float = 0.0
        self.brightness: float = 1.0
        self.thickness: float = 0.0
        self.fade_distance_left: float = 1.5
        self.fade_distance_right: float = 1.5
        self.brightness_left: float = 0.9
        self.brightness_right: float = 0.9


class StarSetting(AlterPixelSetting):

    def __init__(self, setting: LedSetting, expected_pixels: int, padding: int, reverse: bool = False):
        super().__init__(setting)
        self.reverse = reverse

        self.spawn_lower = -padding
        self.spawn_upper = expected_pixels + padding
        self.stars: List[Star] = []
        self.last_seconds: Optional[float] = None

        total_distance = expected_pixels + padding * 2
        total_stars = int(total_distance * STAR_PER_PIXEL)
        for i in range(total_stars):
            star = Star()
            self.stars.append(star)
            star.position = randint(self.spawn_lower, self.spawn_upper)
            star.velocity = (randint(0, 1) * 2 - 1) * uniform(0.4, 2.0)
            if not reverse:
                # only have a random brightness if we aren't doing reverse
                star.brightness = uniform(0.2, 0.8)
            star.brightness_left = star.brightness
            star.brightness_right = star.brightness

        shooting_star = Star()
        self.stars.append(shooting_star)
        shooting_star.thickness = 1.0
        shooting_star.fade_distance_right = 4.0
        shooting_star.fade_distance_left = 1.0
        shooting_star.brightness_right = 0.1
        shooting_star.velocity = -10.0

    def apply(self, seconds: float, pixels_list: list):
        delta = 0.0
        if self.last_seconds is not None:
            delta = seconds - self.last_seconds
        self.last_seconds = seconds

        for star in self.stars:
            star.position += star.velocity * delta
            if star.position > self.spawn_upper:
                star.position = self.spawn_lower + (star.position - self.spawn_upper)
            elif star.position < self.spawn_lower:
                star.position = self.spawn_upper - (self.spawn_lower - star.position)
        super().apply(seconds, pixels_list)

    def alter(self, seconds: float, list_index: int, pixel_index: int, pixels, pixel_color: Optional) -> Optional[Tuple[int, int, int]]:
        if not pixel_color:
            return None

        brightness = 0.0
        for star in self.stars:
            lower = star.position - star.thickness / 2
            upper = star.position - star.thickness / 2
            if lower <= pixel_index <= upper:
                brightness = max(brightness, star.brightness)
            elif lower - star.fade_distance_left <= pixel_index < lower:  # 3.5 to 4
                brightness = max(brightness, (pixel_index - (lower - star.fade_distance_left)) / star.fade_distance_left * star.brightness_left)
            elif upper < pixel_index <= upper + star.fade_distance_right:
                brightness = max(brightness, ((upper + star.fade_distance_right) - pixel_index) / star.fade_distance_right * star.brightness_right)

        assert 0.0 <= brightness <= 1.0, f"Brightness is {brightness}"
        if self.reverse:
            brightness = 1 - brightness
        return int(pixel_color[0] * brightness), int(pixel_color[1] * brightness), int(pixel_color[2] * brightness)
