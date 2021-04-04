from abc import abstractmethod, ABC
from typing import List, Callable


class PercentGetter(ABC):
    @abstractmethod
    def get_percent(self, seconds: float) -> float:
        pass


class ReversingPercentGetter(PercentGetter):
    def __init__(self, period: float, direction_period: float, reverse_period: float):
        self.period = period
        self.direction_period = direction_period
        self.reverse_period = reverse_period
        if direction_period % period != 0:
            raise ValueError("The direction period must be a multiple of period!")
        if reverse_period % period != 0:
            raise ValueError("The reverse period must be a multiple of period!")

    def get_percent(self, seconds: float) -> float:
        spot = seconds % (self.direction_period * 2)
        percent = (seconds / self.period) % 1
        if spot <= self.reverse_period:
            a = self.period / self.reverse_period
            x = (spot - self.reverse_period / 2) / self.period
            height = self.reverse_period / 4 / self.period
            percent = a * x * x + 1 - height
        elif self.direction_period <= spot <= (self.direction_period + self.reverse_period):
            a = self.period / self.reverse_period
            x = (spot - self.direction_period - self.reverse_period / 2) / self.period
            height = self.reverse_period / 4 / self.period
            percent = 1 - (a * x * x + 1 - height)
        elif spot > self.direction_period + self.reverse_period:
            percent = 1 - percent

        return percent


class ConstantPercentGetter(PercentGetter):
    def __init__(self, percent):
        self.percent = percent

    def get_percent(self, seconds: float) -> float:
        return self.percent


class SumPercentGetter(PercentGetter):
    def __init__(self, percent_getter_list: List[PercentGetter]):
        self.percent_getter_list = percent_getter_list

    def get_percent(self, seconds: float) -> float:
        return sum(percent_getter.get_percent(seconds) for percent_getter in self.percent_getter_list) % 1.0


class MultiplierPercentGetter(PercentGetter):
    def __init__(self, percent_getter: PercentGetter, multiplier: float):
        self.percent_getter = percent_getter
        self.multiplier = multiplier

    def get_percent(self, seconds: float) -> float:
        return (self.percent_getter.get_percent(seconds) * self.multiplier) % 1.0


class PercentGetterHolder(PercentGetter):
    def __init__(self, percent_getter: PercentGetter, time_multiplier: float = 1.0):
        self.percent_getter: PercentGetter = percent_getter
        self.time_multiplier: float = time_multiplier

    def get_percent(self, seconds: float) -> float:
        return self.percent_getter.get_percent(seconds * self.time_multiplier)


class PercentGetterTimeMultiplier(PercentGetter):
    def __init__(self, percent_getter: PercentGetter, time_multiplier_getter: Callable[[], float]):
        self.percent_getter: PercentGetter = percent_getter
        self.time_multiplier_getter: Callable = time_multiplier_getter

    def get_percent(self, seconds: float) -> float:
        return self.percent_getter.get_percent(seconds * self.time_multiplier_getter())


class BouncePercentGetter(PercentGetter):
    def __init__(self, total_period: float):
        self.total_period = total_period

    def get_percent(self, seconds: float) -> float:
        spot = seconds % self.total_period
        if spot > self.total_period / 2:
            spot = self.total_period - spot
        return spot / self.total_period * 2
