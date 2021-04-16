from typing import Tuple, TypeVar, Generic, Union

T = TypeVar('T', 'RawColor', 'Color')


class RawColor(Generic[T]):
    def __init__(self, r: float, g: float, b: float):
        self.__r = float(r)
        self.__g = float(g)
        self.__b = float(b)

    @property
    def r(self) -> float:
        return self.__r

    @property
    def g(self) -> float:
        return self.__r

    @property
    def b(self) -> float:
        return self.__r

    def __mul__(self, other) -> 'RawColor':
        scalar = float(other)  # only support numeric types
        return RawColor(self.r * scalar, self.g * scalar, self.b * scalar)

    def __add__(self, other) -> 'RawColor':
        if not isinstance(other, RawColor):
            raise ValueError("other must be a RawColor!")
        return RawColor(self.r + other.r, self.g + other.g, self.b + other.b)

    def __rdiv__(self, other):
        scalar = float(other)  # only support numeric types
        return RawColor(self.r / scalar, self.g / scalar, self.b / scalar)

    def clamped(self) -> 'Color':
        return Color(max(0.0, min(1.0, self.r)), max(0.0, min(1.0, self.g)), max(0.0, min(1.0, self.b)))

    def color(self) -> 'Color':
        return Color(self.r, self.g, self.b)

    def lerp(self, other: 'RawColor', percent: float) -> 'RawColor':
        return self * (1 - percent) + other * percent


ColorAlias = Union['Color', Tuple[int, int, int]]


class Color(RawColor):
    def __init__(self, r: float, g: float, b: float):
        if r < 0 or r > 1:
            raise ValueError(f"r out of range! r: {r}")
        if g < 0 or g > 1:
            raise ValueError(f"g out of range! r: {r}")
        if b < 0 or b > 1:
            raise ValueError(f"b out of range! r: {r}")
        super().__init__(r, g, b)

    def tuple(self):
        return int(255 * self.r), int(255 * self.g), int(255 * self.b)

    def lerp(self, other: T, percent: float) -> T:
        if isinstance(other, Color):
            return super().lerp(other, percent).color()
        return super().lerp(other, percent)

    @classmethod
    def from_tuple(cls, t: Tuple[int, int, int]):
        return cls.from_bytes(*t)

    @classmethod
    def from_bytes(cls, r, g, b):
        return Color(r / 255, g / 255, b / 255)

    @classmethod
    def from_alias(cls, alias: ColorAlias) -> 'Color':
        if isinstance(alias, Color):
            return alias
        return cls.from_tuple(alias)

    @classmethod
    def from_24bit(cls, number: int):
        return cls.from_tuple((number >> 16, (number >> 8) & 0xFF, number & 0xFF))


class ColorConstants:
    BLACK = Color(0.0, 0.0, 0.0)

