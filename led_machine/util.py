from typing import Tuple, Optional, List


def copy_pixels_list(pixels_list: list) -> List[List[Optional[Tuple[int, int, int]]]]:
    return [[None] * len(pixels) for pixels in pixels_list]
