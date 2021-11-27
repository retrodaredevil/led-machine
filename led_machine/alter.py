from abc import abstractmethod, ABC
from typing import Optional, List, Union, Callable

from led_machine.color import Color, ColorAlias

Position = Union[int, float]


class LedMetadata:
    """
    This may be used in the future
    """
    pass


class Alter(ABC):
    @abstractmethod
    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        """

        :param seconds: Can be treated as the number of seconds since the epoch. May be altered by the caller to make patterns appear slower or faster
        :param pixel_position: The position of the pixel.
        :param current_color:
        :param metadata:
        :return:
        """
        pass


class AlterNothing(Alter):
    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        return current_color


class AlterDim(Alter):
    def __init__(self, dim: float):
        self.dim = dim

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        if current_color is None:
            return None
        return current_color.scale(self.dim)


class AlterSolid(Alter):
    def __init__(self, color: ColorAlias):
        self.color = Color.from_alias(color)

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        return self.color


class AlterSpeedOfAlter(Alter):
    def __init__(self, alter: Alter, time_multiplier_getter: Callable[[], float]):
        self.alter = alter
        self.time_multiplier_getter = time_multiplier_getter

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        return self.alter.alter_pixel(seconds * self.time_multiplier_getter(), pixel_position, current_color, metadata)


class AlterMultiplexer(Alter):
    def __init__(self, alters: List[Alter]):
        self.alters = alters

    def alter_pixel(self, seconds: float, pixel_position: Position, current_color: Optional[Color], metadata: LedMetadata) -> Optional[Color]:
        for alter in self.alters:
            current_color = alter.alter_pixel(seconds, pixel_position, current_color, metadata)
        return current_color

    def __str__(self):
        return f"AlterMultiplexer(alters={self.alters})"

    def __repr__(self):
        return str(self)
