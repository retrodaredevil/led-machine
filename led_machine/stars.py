from random import randint, uniform
from typing import Optional, List, Callable

from led_machine.alter import Alter, Position, LedMetadata
from led_machine.color import Color
from led_machine.types import TimeMultiplierGetter

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


class AlterStar(Alter):

    def __init__(self, expected_pixels: int, padding: int, time_multiplier_getter: TimeMultiplierGetter, reverse: bool = False):
        self.reverse = reverse
        self.time_multiplier_getter = time_multiplier_getter

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
            star.velocity = (randint(0, 1) * 2 - 1) * uniform(0.3, 1.5)
            if reverse:
                star.thickness = 2.0
            else:
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

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        delta = 0.0
        if self.last_seconds is not None:
            delta = seconds - self.last_seconds
        self.last_seconds = seconds

        if delta > 0:
            for star in self.stars:
                star.position += star.velocity * delta * self.time_multiplier_getter()  # instead of altering seconds, just increase the speed by this multiplier
                if star.position > self.spawn_upper:
                    star.position = self.spawn_lower + (star.position - self.spawn_upper)
                elif star.position < self.spawn_lower:
                    star.position = self.spawn_upper - (self.spawn_lower - star.position)

        if not current_color:
            return None

        brightness = 0.0
        for star in self.stars:
            lower = star.position - star.thickness / 2
            upper = star.position + star.thickness / 2
            if lower <= pixel_position <= upper:
                brightness = max(brightness, star.brightness)
            elif lower - star.fade_distance_left <= pixel_position < lower:  # 3.5 to 4
                brightness = max(brightness, (pixel_position - (lower - star.fade_distance_left)) / star.fade_distance_left * star.brightness_left)
            elif upper < pixel_position <= upper + star.fade_distance_right:
                brightness = max(brightness, ((upper + star.fade_distance_right) - pixel_position) / star.fade_distance_right * star.brightness_right)

        assert 0.0 <= brightness <= 1.0, f"Brightness is {brightness}"
        if self.reverse:
            brightness = 1 - brightness
        return current_color.scale(brightness)
