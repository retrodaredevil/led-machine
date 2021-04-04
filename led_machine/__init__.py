import time
import json
from pathlib import Path
from typing import Optional

from led_machine.block import BlockSetting
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterHolder, PercentGetterTimeMultiplier
from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting, LedSettingHolder
from led_machine.slack import SlackHelper

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
    return None


def main():
    import board
    import neopixel

    pixels_list = [
        neopixel.NeoPixel(board.D18, 300),  # AKA GPIO 18
    ]
    pixels_list[0].auto_write = False

    with Path("config.json").open() as file:
        config = json.load(file)

    slack_bot_token = config["slack_bot_token"]
    slack_app_token = config["slack_app_token"]  # xapp-***
    slack_channel = config["slack_channel"]
    slack_helper = SlackHelper(slack_bot_token, slack_app_token, slack_channel)

    color_time_multiplier = 1.0
    color_time_multiplier_getter = lambda: color_time_multiplier
    pattern_time_multiplier = 1.0
    pattern_time_multiplier_getter = lambda: pattern_time_multiplier

    default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)
    quick_bounce_percent_getter = BouncePercentGetter(12.0)
    slow_default_percent_getter = ReversingPercentGetter(4.0, 10.0 * 60, 4.0)

    rainbow_setting = RainbowSetting(PercentGetterTimeMultiplier(default_percent_getter, color_time_multiplier_getter), 50)
    long_rainbow_setting = RainbowSetting(PercentGetterTimeMultiplier(default_percent_getter, color_time_multiplier_getter), 300)
    solid_rainbow_setting = RainbowSetting(PercentGetterTimeMultiplier(ReversingPercentGetter(10.0, 15.0 * 60, 10.0), color_time_multiplier_getter), 30000000000)
    bpr_setting = BlockSetting(
        None,
        [((0, 0, 255), 2), ((255, 0, 70), 4), ((255, 0, 0), 2)],
        PercentGetterTimeMultiplier(default_percent_getter, color_time_multiplier_getter)
    )

    main_setting_holder = LedSettingHolder(rainbow_setting)
    pattern_setting_holder = LedSettingHolder(main_setting_holder)
    rear_dimmer = DimSetting(FrontDimSetting(pattern_setting_holder), 1, (300 - 47, 300))
    setting = DimSetting(rear_dimmer, DIM)
    dim_setting = 0.8
    while True:
        for message in slack_helper.new_messages():
            text: str = message["text"].lower()
            reset = False
            if "brown" in text or ("shallow" in text and "purple" in text):
                main_setting_holder.setting = SolidSetting((165, 42, 23))
            elif "purple" in text and "deep" in text:
                main_setting_holder.setting = SolidSetting((255, 0, 70))
            elif "purple" in text:
                main_setting_holder.setting = SolidSetting((255, 0, 255))
            elif "pink" in text:
                main_setting_holder.setting = SolidSetting((255, 100, 120))
            elif "red" in text:
                main_setting_holder.setting = SolidSetting((255, 0, 0))
            elif "green" in text:
                main_setting_holder.setting = SolidSetting((0, 255, 0))
            elif "blue" in text:
                main_setting_holder.setting = SolidSetting((0, 0, 255))
            elif "orange" in text:
                main_setting_holder.setting = SolidSetting((255, 45, 0))
            elif "yellow" in text:
                main_setting_holder.setting = SolidSetting((255, 255, 0))
            elif "teal" in text:
                main_setting_holder.setting = SolidSetting((0, 255, 255))
            elif "white" in text:
                main_setting_holder.setting = SolidSetting((255, 255, 255))
            elif "off" in text:
                main_setting_holder.setting = SolidSetting((0, 0, 0))
                reset = True
            elif "long" in text and "rainbow" in text:
                main_setting_holder.setting = long_rainbow_setting
            elif "solid" in text and "rainbow" in text:
                main_setting_holder.setting = solid_rainbow_setting
            elif "rainbow" in text:
                main_setting_holder.setting = rainbow_setting
            elif "bpr" in text:
                main_setting_holder.setting = bpr_setting

            if "skyline" in text or "sky line" in text or "sky-line" in text:
                dim_setting = 0.005
                rear_dimmer.dim = 0.0
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
                    unknown = True
                if not unknown:
                    rear_dimmer.dim = 1.0

            indicates_pattern = False
            if reset or "reset" in text:
                pattern_setting_holder.setting = main_setting_holder
                color_time_multiplier = 1.0
                pattern_time_multiplier = 1.0
            elif "carnival" in text:
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

            if indicates_pattern or "pattern" in text:
                # Pattern speed
                time_multiplier = get_time_multiplier(text)
                if time_multiplier is not None:
                    pattern_time_multiplier = time_multiplier
            else:
                # Color speed
                time_multiplier = get_time_multiplier(text)
                if time_multiplier is not None:
                    color_time_multiplier = time_multiplier
        seconds = time.time()

        setting.dim = DIM * dim_setting
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.02)


if __name__ == '__main__':
    main()
