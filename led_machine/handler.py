from typing import Optional, List

from led_machine.alter import Alter, AlterSolid, AlterNothing, AlterSpeedOfAlter
from led_machine.block import AlterBlock
from led_machine.color import ColorConstants
from led_machine.color_parse import parse_colors
from led_machine.fade import AlterFade
from led_machine.northern_lights import AlterNorthernLights
from led_machine.partition import AlterPartition
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterTimeMultiplier
from led_machine.rainbow import AlterRainbow
from led_machine.stars import AlterStar
from led_machine.twinkle import AlterTwinkle

START_PIXELS_TO_HIDE = 21


# DIM = 0.8 * 0.01  # good for really dim
# DIM = 0.8 * 0.12  # good for movie


def get_time_multiplier(text) -> Optional[float]:

    speed = get_number_before(text, "speed")
    if speed is not None:
        return speed

    if "hyper" in text:
        return 4.0
    elif "sonic" in text:
        return 2.0
    elif "fast" in text:
        return 1.5
    elif "medium" in text:
        return 1.0
    elif "slow" in text:
        return 0.5
    elif "crawl" in text:
        return 0.25
    elif "limp" in text:
        return 0.1
    elif "still" in text:
        return 0.001
    elif "stop" in text:
        return 0.000000001
    return None


def get_string_after(text: str, target_text: str) -> Optional[str]:
    split = text.split()
    previous_element: Optional[str] = None
    for element in split:
        if previous_element == target_text:
            return element
        previous_element = element
    return None


def get_number_before(text: str, target_text: str) -> Optional[float]:
    split = text.split()
    previous_element: Optional[str] = None
    for element in split:
        if previous_element is not None and element == target_text:
            try:
                return float(previous_element)
            except ValueError:
                pass
        previous_element = element
    return None


class LedConstants:
    default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)
    quick_bounce_percent_getter = BouncePercentGetter(12.0)
    slow_default_percent_getter = ReversingPercentGetter(4.0, 10.0 * 60, 4.0)
    # josh_lamp_partition_list = [(START_PIXELS_TO_HIDE, 17), (NUMBER_OF_PIXELS - 19, 19)]


class LedState:
    def __init__(self, total_number_of_pixels: int):
        self.total_number_of_pixels = total_number_of_pixels
        self.virtual_pixels = self.total_number_of_pixels - START_PIXELS_TO_HIDE
        self.pixel_offsets = {
            "side_half": 49,
            "front_back": 49 + (self.virtual_pixels // 4)
        }

        # Values that are directly mutated
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0

        # Values that remain unchanged, but are based on the state defined above
        self.color_time_multiplier_getter = lambda: self.color_time_multiplier
        self.pattern_time_multiplier_getter = lambda: self.pattern_time_multiplier

        # color_percent_getter = SumPercentGetter([LedConstants.default_percent_getter, color_percent_getter_push])
        self.color_percent_getter = LedConstants.default_percent_getter  # when we had volume stuff, we used to use the above line
        """The percent getter that should be used for all color settings except for solid"""
        # self.solid_color_percent_getter = SumPercentGetter([ReversingPercentGetter(10.0, 15.0 * 60, 10.0), color_percent_getter_push])
        self.solid_color_percent_getter = ReversingPercentGetter(10.0, 15.0 * 60, 10.0)
        """The percent getter that should be used for solid color settings"""

        simple_rainbow = self.parse_color_setting("rainbow")
        if simple_rainbow is None:
            raise AssertionError("Should not get None for string 'rainbow'!")
        self.main_alter: Alter = simple_rainbow
        self.pattern_alter: Alter = AlterNothing()  # TODO think about making this a list of alters

    def reset(self):
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0
        self.pattern_alter = AlterNothing()

    def parse_color_setting(self, text: str) -> Optional[Alter]:
        """
        Does NOT mutate this. This is a member function because the returned LedSetting may contain references to the state defined in this class,
        so mutating the state of this instance could affect the different settings returned by this method
        """
        requested_colors = parse_colors(text)
        if "north" in text and len(requested_colors) >= 2:
            return AlterNorthernLights(requested_colors, self.virtual_pixels)
        elif "pixel" in text and len(requested_colors) >= 2:
            return AlterBlock(
                [(color, 1) for color in requested_colors],
                PercentGetterTimeMultiplier(self.color_percent_getter, self.color_time_multiplier_getter),
                fade=False
            )
        elif "rainbow" in text or len(requested_colors) >= 2:
            pattern_size: float = self.virtual_pixels / 8  # gets to be about 50
            percent_getter = self.color_percent_getter
            if "double" in text and "long" in text:
                pattern_size = self.virtual_pixels * 2
            elif "long" in text:
                pattern_size = self.virtual_pixels
            elif "fat" in text:
                pattern_size = self.virtual_pixels / 4  # gets to be about 100
            elif "tiny" in text:
                pattern_size = self.virtual_pixels / 16  # gets to be about 25
            elif "solid" in text:
                pattern_size = 30000000000
                percent_getter = self.solid_color_percent_getter

            if "rainbow" in text:
                return AlterRainbow(PercentGetterTimeMultiplier(percent_getter, self.color_time_multiplier_getter), pattern_size)
            else:
                return AlterFade(
                    PercentGetterTimeMultiplier(percent_getter, self.color_time_multiplier_getter),
                    requested_colors,
                    pattern_size
                )
        elif requested_colors:
            return AlterSolid(requested_colors[0])
        elif "random":
            pass  # TODO

        return None


class MessageContext:
    def __init__(self):
        self.reset: bool = False


def handle_message(text: str, led_state: LedState, is_lamp: bool, context: MessageContext):
    split_text = text.split("|")
    requested_settings: List[Alter] = [setting for setting in (led_state.parse_color_setting(split) for split in split_text) if setting is not None]

    is_off = "off" in text

    if not requested_settings and is_lamp and not is_off:
        requested_settings = [AlterSolid(ColorConstants.WHITE)]

    if requested_settings:
        if len(requested_settings) == 1:
            led_state.main_alter = requested_settings[0]
        else:
            offset_string = get_string_after(text, "offset")
            try:
                if offset_string is None:
                    raise ValueError()
                offset_pixels = int(offset_string)
            except ValueError:
                offset_pixels = offset_string is not None and led_state.pixel_offsets.get(offset_string) or led_state.pixel_offsets["side_half"]
            pixels_per_partition = led_state.virtual_pixels // len(requested_settings)
            extra_pixels = led_state.virtual_pixels % len(requested_settings)
            start_pixel = START_PIXELS_TO_HIDE + offset_pixels
            override_list = []
            for i, requested_setting in enumerate(requested_settings):
                length = pixels_per_partition + (1 if i < extra_pixels else 0)
                end_pixel = start_pixel + length - 1  # The index of the last pixel in this partition
                partitions = []
                if end_pixel >= led_state.total_number_of_pixels:
                    end_length = led_state.total_number_of_pixels - start_pixel
                    leftover_length = length - end_length
                    partitions.append((start_pixel, end_length))
                    partitions.append((START_PIXELS_TO_HIDE, leftover_length))
                    start_pixel = START_PIXELS_TO_HIDE + leftover_length
                else:
                    partitions.append((start_pixel, length))
                    start_pixel += length
                    if start_pixel >= led_state.total_number_of_pixels:
                        start_pixel -= led_state.total_number_of_pixels
                        start_pixel += START_PIXELS_TO_HIDE
                override_list.append((requested_setting, partitions))

            led_state.main_alter = AlterPartition(override_list)
    elif is_off:
        if is_lamp:
            led_state.main_alter = AlterNothing()
        else:
            context.reset = True
            led_state.main_alter = AlterSolid(ColorConstants.BLACK)

    indicates_pattern = "pattern" in text
    # TODO pulse in and out
    if context.reset or "reset" in text:
        led_state.reset()
    elif "carnival" in text:
        indicates_pattern = True
        block_list = [(None, 5), ((0, 0, 0), 3)]
        if "short" in text or "tiny" in text:
            block_list = [(None, 3), ((0, 0, 0), 2)]
        elif "long" in text:
            block_list = [(None, 10), ((0, 0, 0), 6)]

        led_state.pattern_alter = AlterBlock(
            block_list,
            PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
        )
    elif "single" in text:
        indicates_pattern = True
        led_state.pattern_alter = AlterBlock(
            [(None, 5), ((0, 0, 0), led_state.virtual_pixels)],
            PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
        )
    elif "bounce" in text:
        indicates_pattern = True
        led_state.pattern_alter = AlterBlock(
            [(None, 5), ((0, 0, 0), led_state.virtual_pixels - 5)],
            PercentGetterTimeMultiplier(
                MultiplierPercentGetter(LedConstants.quick_bounce_percent_getter, (led_state.virtual_pixels - 5) / led_state.virtual_pixels),
                led_state.pattern_time_multiplier_getter
            )
        )
    elif "reverse" in text and "star" in text:
        indicates_pattern = True
        led_state.pattern_alter = AlterStar(
            led_state.total_number_of_pixels, 300, led_state.pattern_time_multiplier_getter, reverse=True
        )
    elif "star" in text:
        indicates_pattern = True
        led_state.pattern_alter = AlterStar(led_state.total_number_of_pixels, 300, led_state.pattern_time_multiplier_getter)
    elif "twinkle" in text:
        indicates_pattern = True
        number: Optional[float] = get_number_before(text, "twinkle")  # number will either be None, or we should expect a value between 0 and 100
        twinkle_percent = 0.5
        if number is not None and 0 <= number <= 100:
            twinkle_percent = number / 100.0
        min_percent = max(0.0, twinkle_percent ** 2 - 0.1)
        max_percent = min(1.0, twinkle_percent ** 0.5 + 0.1)
        led_state.pattern_alter = AlterSpeedOfAlter(
            AlterTwinkle(led_state.total_number_of_pixels, min_percent, max_percent),
            led_state.pattern_time_multiplier_getter
        )

    time_multiplier = get_time_multiplier(text)
    if time_multiplier is not None:
        if indicates_pattern:
            # Pattern speed
            led_state.pattern_time_multiplier = time_multiplier
        else:
            # Color speed
            led_state.color_time_multiplier = time_multiplier
