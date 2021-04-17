import math
import random
from typing import List, Optional

from led_machine.color import Color
from led_machine.settings import LedSetting


OFFSET_TRANSLATE_SPEED = 3.0
"""Offset translate speed in pixels per second"""


class Chunk:
    def __init__(self, color: Color):
        self.color = color
        self.width = 0.0
        """Width in pixels"""
        self.fade_spot = 0.5
        """The percent spot for the fade focal point."""
        self.fade_oscillate_speed = 1.0
        self.fade_oscillate_magnitude = 0.1

    def get_focal_point(self, seconds: float) -> float:
        return self.fade_spot + math.sin(seconds * self.fade_oscillate_speed) * self.fade_oscillate_magnitude


class NorthernLightsSetting(LedSetting):
    def __init__(self, colors: List[Color], pixel_span: int):
        self.chunks = [Chunk(color) for color in colors]
        self.pixel_span = pixel_span
        self.offset = 0.0
        self.desired_offset = 0.0
        # normally we'd set last_xxx to None, but setting to 0 makes it just work out nicely
        self.last_seconds = 0.0
        self.last_random = 0.0

        self.reset()

    def reset(self):
        full_chunk_width = self.pixel_span / len(self.chunks)
        for chunk in self.chunks:
            chunk.fade_spot = 0.5
            chunk.width = full_chunk_width / 3

    def set_desired_offset(self, desired_offset: float):
        result = (desired_offset - self.offset) % self.pixel_span
        if result > self.pixel_span / 2:
            result -= self.pixel_span
        self.desired_offset = self.offset + result

    def apply(self, seconds: float, pixels_list: List[List[Optional[Color]]]):
        delta = seconds - self.last_seconds
        self.last_seconds = seconds
        if delta > 1.0:
            self.reset()
        if abs(self.offset - self.desired_offset) < 1:
            self.offset = self.desired_offset
        else:
            self.offset += math.copysign(delta * OFFSET_TRANSLATE_SPEED, self.desired_offset - self.offset)

        if seconds - self.last_random >= 5:
            self.last_random = seconds
            choice = random.randint(0, 1)
            if choice == 0:
                self.set_desired_offset(random.randint(0, self.pixel_span))
            elif choice == 1:
                chunk = random.choice(self.chunks)
                chunk.fade_spot = random.uniform(0.3, 0.7)
                chunk.fade_oscillate_speed = random.uniform(0.9, 1.1)
                chunk.fade_oscillate_magnitude = random.uniform(0.05, 0.2)

        full_chunk_width = self.pixel_span / len(self.chunks)
        for pixels in pixels_list:
            for pixel_index in range(len(pixels)):
                pixel_spot = (pixel_index + self.offset) % self.pixel_span
                for chunk_index, chunk in enumerate(self.chunks):
                    if pixel_spot <= chunk_index * full_chunk_width + chunk.width:
                        pixels[pixel_index] = chunk.color
                        break
                    if pixel_spot < (chunk_index + 1) * full_chunk_width:
                        left_color = chunk.color
                        right_color = self.chunks[(chunk_index + 1) % len(self.chunks)].color
                        middle_color = left_color.lerp(right_color, 0.5)
                        fade_divisor = full_chunk_width - chunk.width
                        percent_distance = (pixel_spot - chunk_index * full_chunk_width - chunk.width) / fade_divisor
                        focal_point = chunk.get_focal_point(seconds)
                        assert 0 <= focal_point <= 1, f"Focal point is {focal_point}"
                        if percent_distance <= focal_point:
                            pixels[pixel_index] = left_color.lerp(middle_color, percent_distance / focal_point)
                        else:
                            percent_lerp = (percent_distance - focal_point) / (1 - focal_point)
                            pixels[pixel_index] = middle_color.lerp(right_color, percent_lerp)
                        break
