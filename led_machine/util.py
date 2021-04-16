from typing import Optional, List

from led_machine.color import Color


def copy_pixels_list(pixels_list: List[List[Optional[Color]]]) -> List[List[Optional[Color]]]:
    return [[None] * len(pixels) for pixels in pixels_list]
