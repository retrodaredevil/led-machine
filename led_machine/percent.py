import math
from abc import abstractmethod, ABC
from typing import List, Callable, Optional

from led_machine.types import TimeMultiplierGetter


class PercentGetter(ABC):
    @abstractmethod
    def get_percent(self, seconds: float) -> float:
        """
        Note: In almost all cases a returned value of 1.0 should be interpreted the same as 0, but depending on what you're doing, it is not required.
        :param seconds: The number of seconds since the epoch.
        :return: A number in range [0..1]
        """
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
    def __init__(self, percent_getter: PercentGetter, time_multiplier_getter: TimeMultiplierGetter):
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


class SmoothPercentGetter(PercentGetter):
    """
    Smooths a percentage from 0 to 1, but does not (yet) do any continuous smoothing. (0 and 1 are not the same)
    """
    PERCENT_MOVE_PER_SECOND = 5.0

    def __init__(self, percent_getter: PercentGetter):
        self.percent_getter = percent_getter
        self.current_percent = 0.0
        self.last_time: Optional[float] = None

    def get_percent(self, seconds: float) -> float:
        delta = seconds - self.last_time if self.last_time is not None else 0.01  # hard code a default delta
        self.last_time = seconds
        max_move = delta * self.__class__.PERCENT_MOVE_PER_SECOND
        desired_percent = self.percent_getter.get_percent(seconds)
        # print(desired_percent)
        # print(self.current_percent)
        # print()
        direction = math.copysign(1, desired_percent - self.current_percent)
        new_percent = self.current_percent + direction * max_move
        if direction > 0 and new_percent > desired_percent:
            new_percent = desired_percent
        elif direction < 0 and new_percent < desired_percent:
            new_percent = desired_percent
        self.current_percent = new_percent
        return new_percent
