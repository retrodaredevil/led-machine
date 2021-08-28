import time
import json
from pathlib import Path
from typing import Optional

from led_machine.block import BlockSetting
from led_machine.centered_bar import CenteredBarSetting
from led_machine.color_parse import parse_colors
from led_machine.fade import FadeSetting
from led_machine.northern_lights import NorthernLightsSetting
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterHolder, PercentGetterTimeMultiplier, ConstantPercentGetter, SumPercentGetter, SmoothPercentGetter
from led_machine.police import PoliceSetting
from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting, LedSettingHolder
from led_machine.slack import SlackHelper
from led_machine.stars import StarSetting
from led_machine.volume import VolumePercentGetter, MeterHelper, HighFrequencyPercentGetter

DIM = 1.0


# DIM = 0.8 * 0.01  # good for really dim
# DIM = 0.8 * 0.12  # good for movie


def get_time_multiplier(text) -> Optional[float]:
    if "sonic" in text:
        return 2.0
    elif "fast" in text:
        return 1.5
    elif "medium" in text:
        return 1.0
    elif "slow" in text:
        return 0.5
    elif "crawl" in text:
        return 0.25
    elif "still" in text:
        return 0.001
    return None


def main():
    import board
    import neopixel

    pixels_list = [
        neopixel.NeoPixel(board.D18, 450),  # AKA GPIO 18
    ]
    pixels_list[0].auto_write = False

    with Path("config.json").open() as file:
        config = json.load(file)

    slack_bot_token = config["slack_bot_token"]  # xoxb-***
    slack_app_token = config["slack_app_token"]  # xapp-***
    slack_channel = config["slack_channel"]
    slack_helper = SlackHelper(slack_bot_token, slack_app_token, slack_channel)

    color_time_multiplier = 1.0
    color_time_multiplier_getter = lambda: color_time_multiplier
    # by default, don't "push" the color's percent getter at all
    color_percent_getter_push = PercentGetterHolder(ConstantPercentGetter(0.0))  # TODO do the same thing for patterns
    pattern_time_multiplier = 1.0
    pattern_time_multiplier_getter = lambda: pattern_time_multiplier

    default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)
    quick_bounce_percent_getter = BouncePercentGetter(12.0)
    slow_default_percent_getter = ReversingPercentGetter(4.0, 10.0 * 60, 4.0)
    meter_helper = MeterHelper()
    volume_percent_getter = SmoothPercentGetter(VolumePercentGetter(meter_helper))
    high_frequency_percent_getter = HighFrequencyPercentGetter(meter_helper)

    color_percent_getter = SumPercentGetter([default_percent_getter, color_percent_getter_push])
    """The percent getter that should be used for all color settings except for solid"""
    solid_color_percent_getter = SumPercentGetter([ReversingPercentGetter(10.0, 15.0 * 60, 10.0), color_percent_getter_push])
    """The percent getter that should be used for solid color settings"""
    rainbow_setting = RainbowSetting(
        PercentGetterTimeMultiplier(color_percent_getter, color_time_multiplier_getter), 50
    )
    bpr_setting = BlockSetting(
        None,
        [((0, 0, 255), 2), ((255, 0, 70), 4), ((255, 0, 0), 2)],
        PercentGetterTimeMultiplier(SumPercentGetter([default_percent_getter, color_percent_getter_push]), color_time_multiplier_getter)
    )
    police_setting = PoliceSetting(  # there is not really a reason to add color_percent_getter_push to this
        PercentGetterTimeMultiplier(ReversingPercentGetter(1.0, 60.0 * 60, 1.0), color_time_multiplier_getter)
    )

    main_setting_holder = LedSettingHolder(rainbow_setting)
    pattern_setting_holder = LedSettingHolder(main_setting_holder)
    setting = DimSetting(pattern_setting_holder, DIM)
    dimmer_percent_getter = PercentGetterHolder(ConstantPercentGetter(1.0))
    """A percent getter which stores a percent getter that dynamically controls the brightness of the lights."""
    dim_setting = 0.8
    """A value that is changed when requested by the user"""
    while True:
        for message in slack_helper.new_messages():
            text: str = message["text"].lower()
            print(f"Got text: {repr(text)}")
            reset = False
            requested_colors = parse_colors(text)
            if "north" in text and len(requested_colors) >= 2:
                main_setting_holder.setting = NorthernLightsSetting(requested_colors, 300)
            elif "pixel" in text and len(requested_colors) >= 2:
                main_setting_holder.setting = BlockSetting(
                    None,
                    [(color, 1) for color in requested_colors],
                    PercentGetterTimeMultiplier(color_percent_getter, color_time_multiplier_getter),
                    fade=False
                )
            elif "rainbow" in text or len(requested_colors) >= 2:
                pattern_size = 50
                percent_getter = color_percent_getter
                if "long" in text:
                    pattern_size = 300
                elif "fat" in text:
                    pattern_size = 100
                elif "tiny" in text:
                    pattern_size = 25
                elif "solid" in text:
                    pattern_size = 30000000000
                    percent_getter = solid_color_percent_getter

                if "rainbow" in text:
                    main_setting_holder.setting = RainbowSetting(PercentGetterTimeMultiplier(percent_getter, color_time_multiplier_getter), pattern_size)
                else:
                    main_setting_holder.setting = FadeSetting(
                        PercentGetterTimeMultiplier(percent_getter, color_time_multiplier_getter),
                        requested_colors,
                        pattern_size
                    )

            elif requested_colors:
                main_setting_holder.setting = SolidSetting(requested_colors[0])
            elif "off" in text:
                main_setting_holder.setting = SolidSetting((0, 0, 0))
                reset = True
            elif "bpr" in text:
                main_setting_holder.setting = bpr_setting
            elif "police" in text or "siren" in text:
                main_setting_holder.setting = police_setting

            if "skyline" in text or "sky line" in text or "sky-line" in text:
                dim_setting = 0.005
            else:
                unknown = False
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
                else:
                    if reset:
                        dim_setting = 0.8
                    unknown = True
                if not unknown:
                    # rear_dimmer.dim = 1.0
                    pass

            indicates_pattern = "pattern" in text
            # TODO pulse in and out
            if reset or "reset" in text:
                pattern_setting_holder.setting = main_setting_holder
                color_time_multiplier = 1.0
                pattern_time_multiplier = 1.0
                dimmer_percent_getter.percent_getter = ConstantPercentGetter(1.0)
                color_percent_getter_push.percent_getter = ConstantPercentGetter(0.0)
            elif "carnival" in text:  # TODO short and long carnival
                indicates_pattern = True
                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, [(None, 5), ((0, 0, 0), 3)],
                    PercentGetterTimeMultiplier(slow_default_percent_getter, pattern_time_multiplier_getter)
                )
            elif "single" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, [(None, 5), ((0, 0, 0), 295)],
                    PercentGetterTimeMultiplier(slow_default_percent_getter, pattern_time_multiplier_getter)
                )
            elif "bounce" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = BlockSetting(
                    main_setting_holder, [(None, 5), ((0, 0, 0), 295)],
                    PercentGetterTimeMultiplier(
                        MultiplierPercentGetter(quick_bounce_percent_getter, 295 / 300),
                        pattern_time_multiplier_getter
                    )
                )
            elif "reverse" in text and "star" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = StarSetting(main_setting_holder, 300, 300, reverse=True)
            elif "star" in text:
                indicates_pattern = True
                pattern_setting_holder.setting = StarSetting(main_setting_holder, 300, 300)
            elif "sound" in text and "bar" in text:
                pattern_setting_holder.setting = CenteredBarSetting(main_setting_holder, volume_percent_getter, 75)

            if "pulse" in text and "loud" in text:
                dimmer_percent_getter.percent_getter = volume_percent_getter
            elif "pulse" in text and ("freq" in text or "pitch" in text):
                dimmer_percent_getter.percent_getter = high_frequency_percent_getter
            elif "pulse" in text:
                pass  # TODO pulse

            time_multiplier = get_time_multiplier(text)
            if time_multiplier is not None:
                if indicates_pattern:
                    # Pattern speed
                    pattern_time_multiplier = time_multiplier
                else:
                    # Color speed
                    color_time_multiplier = time_multiplier
            if "push" in text:
                if "loud" in text:
                    if indicates_pattern:
                        pass
                    else:
                        color_percent_getter_push.percent_getter = volume_percent_getter
                elif "freq" in text or "pitch" in text:
                    if indicates_pattern:
                        pass
                    else:
                        color_percent_getter_push.percent_getter = high_frequency_percent_getter

        seconds = time.time()

        setting.dim = DIM * dim_setting * dimmer_percent_getter.get_percent(seconds)
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.001)


if __name__ == '__main__':
    main()
