from typing import Tuple, TypeVar, Generic, Union

T = TypeVar('T', 'RawColor', 'Color')


class RawColor(Generic[T]):
    def __init__(self, r: float, g: float, b: float):
        self._r = float(r)
        self._g = float(g)
        self._b = float(b)

    def __mul__(self, other) -> 'RawColor':
        scalar = float(other)  # only support numeric types
        return RawColor(self._r * scalar, self._g * scalar, self._b * scalar)

    def __add__(self, other) -> 'RawColor':
        if not isinstance(other, RawColor):
            raise ValueError("other must be a RawColor!")
        return RawColor(self._r + other._r, self._g + other._g, self._b + other._b)

    def __rdiv__(self, other):
        scalar = float(other)  # only support numeric types
        return RawColor(self._r / scalar, self._g / scalar, self._b / scalar)

    def clamped(self) -> 'Color':
        return Color(max(0.0, min(1.0, self._r)), max(0.0, min(1.0, self._g)), max(0.0, min(1.0, self._b)))

    def color(self) -> 'Color':
        return Color(self._r, self._g, self._b)

    def lerp(self, other: 'RawColor', percent: float) -> 'RawColor':
        return self * (1 - percent) + other * percent

    def __eq__(self, other):
        return isinstance(other, RawColor) and self._r == other._r and self._g == other._g and self._b == other._b

    def __str__(self):
        return f"Color(r={self._r}, g={self._g}, b={self._b})"


ColorAlias = Union['Color', Tuple[int, int, int]]


class Color(RawColor):
    def __init__(self, r: float, g: float, b: float):
        if r < 0 or r > 1:
            raise ValueError(f"r out of range! r: {r}")
        if g < 0 or g > 1:
            raise ValueError(f"g out of range! r: {g}")
        if b < 0 or b > 1:
            raise ValueError(f"b out of range! r: {b}")
        super().__init__(r, g, b)
        self.tuple = (int(self._r * 255), int(self._g * 255), int(self._b * 255))

    def __len__(self):
        return 3

    def __getitem__(self, item):
        return self.tuple[item]

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

