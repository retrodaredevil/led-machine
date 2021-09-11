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
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterHolder, PercentGetterTimeMultiplier, ConstantPercentGetter, SumPercentGetter, SmoothPercentGetter
from led_machine.police import PoliceSetting
from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting, LedSettingHolder, LedSetting
from led_machine.slack import SlackHelper
from led_machine.stars import StarSetting
from led_machine.twinkle import TwinkleSetting

DIM = 1.0
NUMBER_OF_PIXELS = 450
START_PIXELS_TO_HIDE = 21
VIRTUAL_PIXELS = NUMBER_OF_PIXELS - START_PIXELS_TO_HIDE


# DIM = 0.8 * 0.01  # good for really dim
# DIM = 0.8 * 0.12  # good for movie


def get_time_multiplier(text) -> Optional[float]:
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


def get_number_before(text: str, target_text: str) -> Optional[int]:
    split = text.split()
    previous_element: Optional[str] = None
    for element in split:
        if previous_element is not None and element == target_text:
            try:
                return int(previous_element)
            except ValueError:
                pass
        previous_element = element
    return None


class LedConstants:
    default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)
    quick_bounce_percent_getter = BouncePercentGetter(12.0)
    slow_default_percent_getter = ReversingPercentGetter(4.0, 10.0 * 60, 4.0)


class LedState:
    def __init__(self):
        self.color_time_multiplier = 1.0
        self.color_time_multiplier_getter = lambda: self.color_time_multiplier
        # by default, don't "push" the color's percent getter at all
        self.pattern_time_multiplier = 1.0
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
        self.police_setting = PoliceSetting(  # there is not really a reason to add color_percent_getter_push to this
            PercentGetterTimeMultiplier(ReversingPercentGetter(1.0, 60.0 * 60, 1.0), self.color_time_multiplier_getter)
        )

    def reset(self):
        self.color_time_multiplier = 1.0
        self.pattern_time_multiplier = 1.0

    def parse_color_setting(self, text: str) -> Optional[LedSetting]:
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

    led_state = LedState()

    main_setting_holder = LedSettingHolder(led_state.rainbow_setting)
    pattern_setting_holder = LedSettingHolder(main_setting_holder)
    setting = DimSetting(
        BlockSetting(pattern_setting_holder, [(ColorConstants.BLACK, START_PIXELS_TO_HIDE), (None, VIRTUAL_PIXELS)], ConstantPercentGetter(0.0), fade=False),
        DIM
    )
    dimmer_percent_getter = PercentGetterHolder(ConstantPercentGetter(1.0))
    """A percent getter which stores a percent getter that dynamically controls the brightness of the lights."""
    dim_setting = 0.8
    """A value that is changed when requested by the user"""
    while True:
        for message in slack_helper.new_messages():
            text: str = message["text"].lower()
            print(f"Got text: {repr(text)}")
            reset = False

            requested_color_setting = led_state.parse_color_setting(text)
            if requested_color_setting is not None:
                main_setting_holder.setting = requested_color_setting
            elif "off" in text:
                reset = True
                main_setting_holder.setting = SolidSetting((0, 0, 0))

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
                if reset:
                    dim_setting = 0.8

            indicates_pattern = "pattern" in text
            # TODO pulse in and out
            if reset or "reset" in text:
                pattern_setting_holder.setting = main_setting_holder
                led_state.reset()
                dimmer_percent_getter.percent_getter = ConstantPercentGetter(1.0)
            elif "carnival" in text:
                indicates_pattern = True
                block_list = [(None, 5), ((0, 0, 0), 3)]
                if "short" in text:
                    block_list = [(None, 3), ((0, 0, 0), 2)]
                elif "long" in text:
                    block_list = [(None, 10), ((0, 0, 0), 6)]

                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, block_list,
                    PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
                )
            elif "single" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, [(None, 5), ((0, 0, 0), VIRTUAL_PIXELS)],
                    PercentGetterTimeMultiplier(LedConstants.slow_default_percent_getter, led_state.pattern_time_multiplier_getter)
                )
            elif "bounce" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, [(None, 5), ((0, 0, 0), VIRTUAL_PIXELS - 5)],
                    PercentGetterTimeMultiplier(
                        MultiplierPercentGetter(LedConstants.quick_bounce_percent_getter, (VIRTUAL_PIXELS - 5) / VIRTUAL_PIXELS),
                        led_state.pattern_time_multiplier_getter
                    )
                )
            elif "reverse" in text and "star" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = StarSetting(main_setting_holder, NUMBER_OF_PIXELS, 300, led_state.pattern_time_multiplier_getter, reverse=True)
            elif "star" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = StarSetting(main_setting_holder, NUMBER_OF_PIXELS, 300, led_state.pattern_time_multiplier_getter)
            elif "twinkle" in text:
                indicates_pattern = True
                number = get_number_before(text, "twinkle")  # number will either be None, or we should expect a value between 0 and 100
                twinkle_percent = 0.5
                if number is not None and 0 <= number <= 100:
                    twinkle_percent = number / 100.0
                min_percent = max(0.0, twinkle_percent ** 2 - 0.1)
                max_percent = min(1.0, twinkle_percent ** 0.5 + 0.1)
                pattern_setting_holder.setting = TwinkleSetting(main_setting_holder, min_percent, max_percent, led_state.pattern_time_multiplier_getter)

            time_multiplier = get_time_multiplier(text)
            if time_multiplier is not None:
                if indicates_pattern:
                    # Pattern speed
                    led_state.pattern_time_multiplier = time_multiplier
                else:
                    # Color speed
                    led_state.color_time_multiplier = time_multiplier

        seconds = time.time()

        setting.dim = DIM * dim_setting * dimmer_percent_getter.get_percent(seconds)
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.001)


if __name__ == '__main__':
    main()
