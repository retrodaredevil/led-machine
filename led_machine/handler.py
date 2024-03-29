from typing import Optional, List

from led_machine.alter import Alter, AlterSolid, AlterNothing, AlterSpeedOfAlter
from led_machine.block import AlterBlock
from led_machine.color import ColorConstants
from led_machine.color_parse import parse_colors
from led_machine.fade import AlterFade
from led_machine.northern_lights import AlterNorthernLights
from led_machine.parse import parse_to_tokens, COMMENT_PARSE_PAIR, SINGLE_LINE_COMMENT_PARSE_PAIR, PARENTHESIS_PARSE_PAIR
from led_machine.parsing import get_number_before, get_string_after, tokens_to_creator, PARTITION_TOKEN, BLEND_TOKEN, CreatorSettings, AlterCreator
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterTimeMultiplier
from led_machine.rainbow import AlterRainbow
from led_machine.stars import AlterStar
from led_machine.twinkle import AlterTwinkle
from led_machine.types import TimeMultiplierGetter

START_PIXELS_TO_HIDE = 21


# DIM = 0.8 * 0.01  # good for really dim
# DIM = 0.8 * 0.12  # good for movie

STORM1 = """orange orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple orange orange orange orange
orange orange  orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple orange
orange orange orange orange orange orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple deep
purple orange orange orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple  Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple  Dupree Dupree Dupree Dupree Dupree Dupree Dupree Red red red red red red
red red red red Red red red purple red red red red red red red Red purple red red red red red red red red red Red red red red red red red red red red purple
Red red red red red red red red red red Red red red red red purple red red red red red Red red purple red red red red red red red red Red red purple red red
red red red red red red Red red red red red red red red red red Red red red red red red red red red purple #000 #000 #100 #200 #300 #400 #500 #600 #700 #800
#900 #900 purple #900 #900 #900 #900 #900 #900 purple #900 #900 #900 #900 purple purple #900 purple #900 #900 #900 #900 #900 #900 #900 #900 #900 #900 purple
#900 #900 #900 #900 #900 #900 purple #900 #900 #900 #900 #900 #900 #900 #900 #900 #900 purple #900 #900 #900 #900 #900 #900 #900 Purple #900 purple #900
purple purple Dupree Dupree Dupree Dupree Dupree orange orange orange orange orange orange orange orange orange deep purple deep purple deep purple  orange
deep purple orange orange orange orange orange orange orange orange orange orange Dupree Dupree Dupree Dupree Dupree #900 purple white purple #900 purple
#900 #900 #900 #900 purple purple #900 #900 #900 #900 purple #900 purple #000 #000 #000 purple #900 #900 #900 #900 purple #900 #900 #900 #900 purple #900
purple #900 #900 #000 #900 purple #900 #900 #900 #900 deep purple deep purple deep purple  #900 deep purple deep purple #900 #900 purple #900 purple #900
purple #900 #900 purple #900 purple Red red red red red red orange red red red red Red red deep purple red red red red red red red red Red red red red red
red red red red red Red red red red red purple red red red red red Red red red red red red red red red red Red orange orange red red red red red red red red
red Red red red red red red red red red red Red red deep purple deep purple red  deep purple red red red red red red red Red red red deep purple red red red
red red purple red red Red red red red red red red red red red Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree orange orange orange Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree deep purple deep purple Dupree Dupree Dupree Dupree Dupree Dupree deep purple Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange orange orange orange orange  orange orange orange orange deep purple deep purple deep purple orange orange orange orange orange orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange purple orange orange orange red red red red orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange deep purple orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange red red red red red red orange orange orange orange orange orange orange orange orange yellow yellow yellow yellow white yellow stillSolid orange
orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple orange orange orange orange orange orange  orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple orange orange orange orange
orange orange orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange deep purple deep purple orange orange
orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple  Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple  Dupree Dupree Dupree Dupree Dupree Dupree Dupree Red red red red red red red red red red Red
red red purple red red red red red red red Red purple red red red red red red red red red Red red red red red red red red red red purple Red red red red red
red red red red red Red red red red red purple red red red red red Red red purple red red red red red red red red Red red purple red red red red red red red
red Red red red red red red red red red red Red red red red red red red red red purple #000 #000 #100 #200 #300 #400 #500 #600 #700 #800 #900 #900 purple
#900 #900 #900 #900 #900 #900 purple #900 #900 #900 #900 purple purple #900 purple #900 #900 #900 #900 #900 #900 #900 #900 #900 #900 purple #900 #900 #900
#900 #900 #900 purple #900 #900 #900 #900 #900 #900 #900 #900 #900 #900 purple #900 #900 #900 #900 #900 #900 #900 Purple #900 purple #900 purple purple
Dupree Dupree Dupree Dupree Dupree orange orange orange orange orange orange orange orange orange deep purple deep purple deep purple  orange deep purple
orange orange orange orange orange orange orange orange orange orange Dupree Dupree Dupree Dupree Dupree #900 purple white purple #900 purple #900 #900 #900
#900 purple purple #900 #900 #900 #900 purple #900 purple #000 #000 #000 purple #900 #900 #900 #900 purple #900 #900 #900 #900 purple #900 purple #900 #900
#000 #900 purple #900 #900 #900 #900 deep purple deep purple deep purple  #900 deep purple deep purple #900 #900 purple #900 purple #900 purple #900 #900
purple #900 purple Red red red red red red orange red red red red Red red deep purple red red red red red red red red Red red red red red red red red red red
Red red red red red purple red red red red red Red red red red red red red red red red Red orange orange red red red red red red red red red Red red red red
red red red red red red Red red deep purple deep purple red  deep purple red red red red red red red Red red red deep purple red red red red red purple red
red Red red red red red red red red red red Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree orange orange orange Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree purple Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree deep purple deep purple Dupree Dupree Dupree Dupree Dupree Dupree deep purple Dupree Dupree Dupree Dupree Dupree Dupree Dupree
Dupree Dupree Dupree Dupree Dupree Dupree orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
orange orange orange orange  orange orange orange orange deep purple deep purple deep purple orange orange orange orange orange orange orange orange orange
orange orange orange orange orange orange orange orange orange orange orange orange purple orange orange orange red red red red orange orange orange orange
orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange
deep purple orange deep purple orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange orange red red red
red red red orange orange orange orange orange orange orange orange orange yellow yellow yellow yellow white yellow"""

# STORM2 = STORM1.lower().replace("purple orange orange orange", "purple purple dupree #909")\
#     .replace("purple dupree dupree dupree", "purple purple red #909")\
#     .replace("purple red red red ", "purple #909 purple purple")\
#     .replace("purple #909 #909 ", "purple #000 purple")
STORM2 = STORM1.lower().replace("purple orange", "purple purple") \
    .replace("purple dupree", "purple purple") \
    .replace("purple red", "purple purple")


def get_time_multiplier(text: str) -> Optional[float]:

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

        # color_percent_getter = SumPercentGetter([LedConstants.default_percent_getter, color_percent_getter_push])
        self.color_percent_getter = LedConstants.default_percent_getter  # when we had volume stuff, we used to use the above line
        """The percent getter that should be used for all color settings except for solid"""
        # self.solid_color_percent_getter = SumPercentGetter([ReversingPercentGetter(10.0, 15.0 * 60, 10.0), color_percent_getter_push])
        self.solid_color_percent_getter = ReversingPercentGetter(10.0, 15.0 * 60, 10.0)
        """The percent getter that should be used for solid color settings"""

        simple_rainbow = self.parse_color_setting("rainbow", lambda: self.color_time_multiplier)
        if simple_rainbow is None:
            raise AssertionError("Should not get None for string 'rainbow'!")
        self.main_alter: Alter = simple_rainbow
        self.pattern_alter: Alter = AlterNothing()  # TODO think about making this a list of alters

    def reset(self):
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0
        self.pattern_alter = AlterNothing()

    def parse_color_setting(self, text: str, time_multiplier_getter: TimeMultiplierGetter) -> Optional[Alter]:
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
                PercentGetterTimeMultiplier(self.color_percent_getter, time_multiplier_getter),
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
                return AlterRainbow(PercentGetterTimeMultiplier(percent_getter, time_multiplier_getter), pattern_size)
            else:
                return AlterFade(
                    PercentGetterTimeMultiplier(percent_getter, time_multiplier_getter),
                    requested_colors,
                    pattern_size
                )
        elif requested_colors:
            return AlterSolid(requested_colors[0])
        elif "random":
            pass  # TODO

        return None

    def parse_pattern_setting(self, text: str, time_multiplier_getter: TimeMultiplierGetter) -> Optional[Alter]:
        if "carnival" in text:
            block_list = [(None, 5), ((0, 0, 0), 3)]
            if "short" in text or "tiny" in text:
                block_list = [(None, 3), ((0, 0, 0), 2)]
            elif "long" in text:
                block_list = [(None, 10), ((0, 0, 0), 6)]

            return AlterBlock(
                block_list,
                PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, time_multiplier_getter)
            )
        elif "single" in text:
            return AlterBlock(
                [(None, 5), ((0, 0, 0), self.virtual_pixels)],
                PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, time_multiplier_getter)
            )
        elif "bounce" in text:
            return AlterBlock(
                [(None, 5), ((0, 0, 0), self.virtual_pixels - 5)],
                PercentGetterTimeMultiplier(
                    MultiplierPercentGetter(LedConstants.quick_bounce_percent_getter, (self.virtual_pixels - 5) / self.virtual_pixels),
                    time_multiplier_getter
                )
            )
        elif "reverse" in text and "star" in text:
            return AlterStar(
                self.total_number_of_pixels, 300, time_multiplier_getter, reverse=True
            )
        elif "star" in text:
            return AlterStar(self.total_number_of_pixels, 300, time_multiplier_getter)
        elif "twinkle" in text:
            number: Optional[float] = get_number_before(text, "twinkle")  # number will either be None, or we should expect a value between 0 and 100
            twinkle_percent = 0.5
            if number is not None and 0 <= number <= 100:
                twinkle_percent = number / 100.0
            min_percent = max(0.0, twinkle_percent ** 2 - 0.1)
            max_percent = min(1.0, twinkle_percent ** 0.5 + 0.1)
            return AlterSpeedOfAlter(
                AlterTwinkle(self.total_number_of_pixels, min_percent, max_percent),
                time_multiplier_getter
            )
        return None


class MessageContext:
    def __init__(self):
        self.reset: bool = False


def handle_message(text: str, led_state: LedState, is_lamp: bool, context: MessageContext):
    text = text.replace("storm1", STORM1).replace("storm2", STORM2)
    tokens = parse_to_tokens(text, [PARTITION_TOKEN, BLEND_TOKEN], [COMMENT_PARSE_PAIR, SINGLE_LINE_COMMENT_PARSE_PAIR, PARENTHESIS_PARSE_PAIR])
    creator: Optional[AlterCreator] = None

    def virtual_time_multiplier_getter() -> float:
        if creator is None or creator.creator_data.has_color:
            return led_state.color_time_multiplier
        return led_state.pattern_time_multiplier

    creator = tokens_to_creator(
        tokens,
        led_state.parse_color_setting,
        led_state.parse_pattern_setting,
        get_time_multiplier,
        CreatorSettings(led_state.pixel_offsets, led_state.pixel_offsets["front_back"], virtual_time_multiplier_getter),
        use_provided_time_multiplier=True
    )

    is_off = "off" in text

    color_present = creator is not None and creator.creator_data.has_color
    pattern_present = creator is not None and creator.creator_data.has_pattern
    if color_present:
        led_state.main_alter = creator.create(START_PIXELS_TO_HIDE, led_state.virtual_pixels, led_state.total_number_of_pixels, START_PIXELS_TO_HIDE)
    elif pattern_present:
        led_state.pattern_alter = creator.create(START_PIXELS_TO_HIDE, led_state.virtual_pixels, led_state.total_number_of_pixels, START_PIXELS_TO_HIDE)
    elif is_lamp and not is_off:
        pass  # TODO lamp stuff
    elif is_off:
        if is_lamp:
            led_state.main_alter = AlterNothing()
        else:
            context.reset = True
            led_state.main_alter = AlterSolid(ColorConstants.BLACK)

    # TODO pulse in and out
    if context.reset or "reset" in text:
        led_state.reset()

    time_multiplier: Optional[float] = None
    if creator is not None and creator.creator_data.directly_nested_time_multiplier is not None:
        time_multiplier = creator.creator_data.directly_nested_time_multiplier
    elif not color_present and not pattern_present:
        time_multiplier = get_time_multiplier(text)
    if time_multiplier is not None:
        if not color_present and pattern_present or "pattern" in text:
            # Pattern speed
            led_state.pattern_time_multiplier = time_multiplier
        else:
            # Color speed
            led_state.color_time_multiplier = time_multiplier
