import time
import json
from pathlib import Path
from typing import Optional

from led_machine.block import BlockSetting
from led_machine.centered_bar import CenteredBarSetting
from led_machine.color import ColorConstants
from led_machine.color_parse import parse_colors
from led_machine.fade import FadeSetting
from led_machine.northern_lights import NorthernLightsSetting
from led_machine.partition import PartitionSetting
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterHolder, PercentGetterTimeMultiplier, ConstantPercentGetter, SumPercentGetter, SmoothPercentGetter
from led_machine.police import PoliceSetting
from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting, LedSettingHolder, LedSetting, DoNothingLedSetting
from led_machine.slack import SlackHelper
from led_machine.stars import StarSetting
from led_machine.twinkle import TwinkleSetting

DIM = 1.0
NUMBER_OF_PIXELS = 450
START_PIXELS_TO_HIDE = 21
VIRTUAL_PIXELS = NUMBER_OF_PIXELS - START_PIXELS_TO_HIDE
PIXEL_OFFSETS = {
    "side_half": 49,
    "front_back": 49 + (VIRTUAL_PIXELS // 4)
}


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
    josh_lamp_partition_list = [(START_PIXELS_TO_HIDE, 17), (NUMBER_OF_PIXELS - 19, 19)]


class LedState:
    def __init__(self):
        # Values that are directly mutated
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0

        # Values whose data is mutated
        self.main_setting_holder = LedSettingHolder(DoNothingLedSetting())  # default to the "do nothing" setting.
        self.pattern_setting_holder = LedSettingHolder(self.main_setting_holder)

        # Values that remain unchanged, but are based on the state defined above
        self.color_time_multiplier_getter = lambda: self.color_time_multiplier
        self.pattern_time_multiplier_getter = lambda: self.pattern_time_multiplier

        # color_percent_getter = SumPercentGetter([LedConstants.default_percent_getter, color_percent_getter_push])
        self.color_percent_getter = LedConstants.default_percent_getter  # when we had volume stuff, we used to use the above line
        """The percent getter that should be used for all color settings except for solid"""
        # self.solid_color_percent_getter = SumPercentGetter([ReversingPercentGetter(10.0, 15.0 * 60, 10.0), color_percent_getter_push])
        self.solid_color_percent_getter = ReversingPercentGetter(10.0, 15.0 * 60, 10.0)
        """The percent getter that should be used for solid color settings"""
        self.rainbow_setting = RainbowSetting(
            PercentGetterTimeMultiplier(self.color_percent_getter, self.color_time_multiplier_getter), 50
        )
        self.bpr_setting = BlockSetting(
            None,
            [((0, 0, 255), 2), ((255, 0, 70), 4), ((255, 0, 0), 2)],
            PercentGetterTimeMultiplier(LedConstants.default_percent_getter, self.color_time_multiplier_getter)
        )
        self.police_setting = PoliceSetting(
            PercentGetterTimeMultiplier(ReversingPercentGetter(1.0, 60.0 * 60, 1.0), self.color_time_multiplier_getter)
        )

    def reset(self):
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0
        self.pattern_setting_holder.setting = self.main_setting_holder

    def parse_color_setting(self, text: str) -> Optional[LedSetting]:
        """
        Does NOT mutate this. This is a member function because the returned LedSetting may contain references to the state defined in this class,
        so mutating the state of this instance could affect the different settings returned by this method
        """
        requested_colors = parse_colors(text)
        if "north" in text and len(requested_colors) >= 2:
            return NorthernLightsSetting(requested_colors, VIRTUAL_PIXELS)
        elif "pixel" in text and len(requested_colors) >= 2:
            return BlockSetting(
                None,
                [(color, 1) for color in requested_colors],
                PercentGetterTimeMultiplier(self.color_percent_getter, self.color_time_multiplier_getter),
                fade=False
            )
        elif "rainbow" in text or len(requested_colors) >= 2:
            pattern_size = 50
            percent_getter = self.color_percent_getter
            if "double" in text and "long" in text:
                pattern_size = VIRTUAL_PIXELS * 2
            elif "long" in text:
                pattern_size = VIRTUAL_PIXELS
            elif "fat" in text:
                pattern_size = 100
            elif "tiny" in text:
                pattern_size = 25
            elif "solid" in text:
                pattern_size = 30000000000
                percent_getter = self.solid_color_percent_getter

            if "rainbow" in text:
                return RainbowSetting(PercentGetterTimeMultiplier(percent_getter, self.color_time_multiplier_getter), pattern_size)
            else:
                return FadeSetting(
                    PercentGetterTimeMultiplier(percent_getter, self.color_time_multiplier_getter),
                    requested_colors,
                    pattern_size
                )
        elif requested_colors:
            return SolidSetting(requested_colors[0])
        elif "bpr" in text:
            return self.bpr_setting
        elif "police" in text or "siren" in text:
            return self.police_setting
        elif "random":
            pass  # TODO

        return None


class MessageContext:
    def __init__(self):
        self.reset: bool = False


def handle_message(text: str, led_state: LedState, is_lamp: bool, context: MessageContext):
    split_text = text.split("|")
    requested_settings = [setting for setting in (led_state.parse_color_setting(split) for split in split_text) if setting is not None]

    is_off = "off" in text

    if not requested_settings and is_lamp and not is_off:
        requested_settings = [SolidSetting(ColorConstants.WHITE)]

    if requested_settings:
        if len(requested_settings) == 1:
            led_state.main_setting_holder.setting = requested_settings[0]
        else:
            offset_string = get_string_after(text, "offset")
            try:
                offset_pixels = int(offset_string)
            except ValueError:
                offset_pixels = PIXEL_OFFSETS.get(offset_string) or PIXEL_OFFSETS["side_half"]
            pixels_per_partition = VIRTUAL_PIXELS // len(requested_settings)
            extra_pixels = VIRTUAL_PIXELS % len(requested_settings)
            start_pixel = START_PIXELS_TO_HIDE + offset_pixels
            override_list = []
            for i, requested_setting in enumerate(requested_settings):
                length = pixels_per_partition + (1 if i < extra_pixels else 0)
                end_pixel = start_pixel + length - 1  # The index of the last pixel in this partition
                partitions = []
                if end_pixel >= NUMBER_OF_PIXELS:
                    end_length = NUMBER_OF_PIXELS - start_pixel
                    leftover_length = length - end_length
                    partitions.append((start_pixel, end_length))
                    partitions.append((START_PIXELS_TO_HIDE, leftover_length))
                    start_pixel = START_PIXELS_TO_HIDE + leftover_length
                else:
                    partitions.append((start_pixel, length))
                    start_pixel += length
                    if start_pixel >= NUMBER_OF_PIXELS:
                        start_pixel -= NUMBER_OF_PIXELS
                        start_pixel += START_PIXELS_TO_HIDE
                override_list.append((requested_setting, partitions))

            led_state.main_setting_holder.setting = PartitionSetting(None, override_list)
    elif is_off:
        if is_lamp:
            led_state.main_setting_holder.setting = DoNothingLedSetting()
        else:
            context.reset = True
            led_state.main_setting_holder.setting = SolidSetting(ColorConstants.BLACK)

    indicates_pattern = "pattern" in text
    # TODO pulse in and out
    if context.reset or "reset" in text:
        led_state.pattern_setting_holder.setting = led_state.main_setting_holder
        led_state.reset()
    elif "carnival" in text:
        indicates_pattern = True
        block_list = [(None, 5), ((0, 0, 0), 3)]
        if "short" in text:
            block_list = [(None, 3), ((0, 0, 0), 2)]
        elif "long" in text:
            block_list = [(None, 10), ((0, 0, 0), 6)]

        led_state.pattern_setting_holder.setting = BlockSetting(
            led_state.main_setting_holder, block_list,
            PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
        )
    elif "single" in text:
        indicates_pattern = True
        led_state.pattern_setting_holder.setting = BlockSetting(
            led_state.main_setting_holder, [(None, 5), ((0, 0, 0), VIRTUAL_PIXELS)],
            PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
        )
    elif "bounce" in text:
        indicates_pattern = True
        led_state.pattern_setting_holder.setting = BlockSetting(
            led_state.main_setting_holder, [(None, 5), ((0, 0, 0), VIRTUAL_PIXELS - 5)],
            PercentGetterTimeMultiplier(
                MultiplierPercentGetter(LedConstants.quick_bounce_percent_getter, (VIRTUAL_PIXELS - 5) / VIRTUAL_PIXELS),
                led_state.pattern_time_multiplier_getter
            )
        )
    elif "reverse" in text and "star" in text:
        indicates_pattern = True
        led_state.pattern_setting_holder.setting = StarSetting(
            led_state.main_setting_holder, NUMBER_OF_PIXELS, 300, led_state.pattern_time_multiplier_getter, reverse=True
        )
    elif "star" in text:
        indicates_pattern = True
        led_state.pattern_setting_holder.setting = StarSetting(led_state.main_setting_holder, NUMBER_OF_PIXELS, 300, led_state.pattern_time_multiplier_getter)
    elif "twinkle" in text:
        indicates_pattern = True
        number: Optional[float] = get_number_before(text, "twinkle")  # number will either be None, or we should expect a value between 0 and 100
        twinkle_percent = 0.5
        if number is not None and 0 <= number <= 100:
            twinkle_percent = number / 100.0
        min_percent = max(0.0, twinkle_percent ** 2 - 0.1)
        max_percent = min(1.0, twinkle_percent ** 0.5 + 0.1)
        led_state.pattern_setting_holder.setting = TwinkleSetting(led_state.main_setting_holder, min_percent, max_percent, led_state.pattern_time_multiplier_getter)

    time_multiplier = get_time_multiplier(text)
    if time_multiplier is not None:
        if indicates_pattern:
            # Pattern speed
            led_state.pattern_time_multiplier = time_multiplier
        else:
            # Color speed
            led_state.color_time_multiplier = time_multiplier


def main():
    import board
    import neopixel

    pixels_list = [
        neopixel.NeoPixel(board.D18, NUMBER_OF_PIXELS),  # AKA GPIO 18
    ]
    pixels_list[0].auto_write = False

    with Path("config.json").open() as file:
        config = json.load(file)

    slack_bot_token = config["slack_bot_token"]  # xoxb-***
    slack_app_token = config["slack_app_token"]  # xapp-***
    slack_channel = config["slack_channel"]
    slack_helper = SlackHelper(slack_bot_token, slack_app_token, slack_channel)

    main_led_state = LedState()
    main_led_state.main_setting_holder.setting = main_led_state.rainbow_setting

    josh_lamp_led_state = LedState()
    setting = DimSetting(
        PartitionSetting(
            BlockSetting(main_led_state.pattern_setting_holder, [(ColorConstants.BLACK, START_PIXELS_TO_HIDE), (None, VIRTUAL_PIXELS)], ConstantPercentGetter(0.0), fade=False),
            [(josh_lamp_led_state.pattern_setting_holder, LedConstants.josh_lamp_partition_list)]
        ),
        DIM
    )
    # dimmer_percent_getter = PercentGetterHolder(ConstantPercentGetter(1.0))
    # """A percent getter which stores a percent getter that dynamically controls the brightness of the lights."""
    dim_setting = 0.8
    """A value that is changed when requested by the user"""
    while True:
        for message in slack_helper.new_messages():
            text: str = message["text"].lower()
            print(f"Got text: {repr(text)}")
            context = MessageContext()

            used_led_state = main_led_state
            is_lamp = "lamp" in text
            if is_lamp:
                if "josh" in text:
                    used_led_state = josh_lamp_led_state
            handle_message(text, used_led_state, is_lamp, context)

            if "bright" in text:
                dim_setting = 1.0
            elif "normal" in text:
                dim_setting = 0.8
            elif "dim" in text:
                dim_setting = 0.3 * 0.8
            elif "dark" in text:
                dim_setting = 0.07 * 0.8
            elif "sleep" in text:
                dim_setting = 0.01 * 0.8
            elif "skyline" in text or "sky line" in text or "sky-line" in text:
                dim_setting = 0.005
            else:
                if context.reset and not is_lamp:
                    dim_setting = 0.8


        seconds = time.time()

        # setting.dim = DIM * dim_setting * dimmer_percent_getter.get_percent(seconds)
        setting.dim = DIM * dim_setting
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.001)


if __name__ == '__main__':
    main()
