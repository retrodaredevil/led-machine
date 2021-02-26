import time
import json
from pathlib import Path

from led_machine.block import BlockSetting
from led_machine.percent import ReversingPercentGetter
from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting, LedSettingHolder
from led_machine.slack import SlackHelper

DIM = 1.0
# DIM = 0.8 * 0.01  # good for really dim
# DIM = 0.8 * 0.12  # good for movie


def main():
    import RPi.GPIO as GPIO
    import board
    import neopixel
    # GPIO.setwarnings(False)
    GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_on():
        return GPIO.input(23) == GPIO.LOW

    pixels_list = [
        neopixel.NeoPixel(board.D18, 300),  # AKA GPIO 18
    ]
    pixels_list[0].auto_write = False

    on_start = None
    off_start = None

    with Path("config.json").open() as file:
        config = json.load(file)

    slack_token = config["slack_token"]
    slack_channel = config["slack_channel"]
    slack_helper = SlackHelper(slack_token, slack_channel)

    default_percent_getter = ReversingPercentGetter(2.0, 10.0 * 60, 2.0)
    quick_default_percent_getter = ReversingPercentGetter(1.0, 10.0 * 60, 2.0)
    rainbow_setting = RainbowSetting(default_percent_getter, 50)
    long_rainbow_setting = RainbowSetting(default_percent_getter, 300)
    solid_rainbow_setting = RainbowSetting(ReversingPercentGetter(6.0, 10.0 * 60, 6.0), 30000000000)

    main_setting_holder = LedSettingHolder(rainbow_setting)
    pattern_setting_holder = LedSettingHolder(main_setting_holder)
    rear_dimmer = DimSetting(FrontDimSetting(pattern_setting_holder), 1, (300 - 47, 300))
    setting = DimSetting(rear_dimmer, DIM)
    dim_setting = 0.8
    while True:
        slack_helper.update()
        for message in slack_helper.new_messages():
            text: str = message["text"].lower()
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
            elif "long" in text and "rainbow" in text:
                main_setting_holder.setting = long_rainbow_setting
            elif "solid" in text and "rainbow" in text:
                main_setting_holder.setting = solid_rainbow_setting
            elif "rainbow" in text:
                main_setting_holder.setting = rainbow_setting

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

            if "reset" in text:
                pattern_setting_holder.setting = main_setting_holder
            elif "carnival" in text:
                pattern_setting_holder.setting = BlockSetting(main_setting_holder, [(None, 5), ((0, 0, 0), 3)],
                                                              quick_default_percent_getter)
            elif "single" in text:
                pattern_setting_holder.setting = BlockSetting(main_setting_holder, [(None, 5), ((0, 0, 0), 295)],
                                                              quick_default_percent_getter)
        seconds = time.time()
        if is_on():
            if on_start is None:
                on_start = seconds
            off_start = None
        else:
            if off_start is None:
                off_start = seconds
            on_start = None

        on_off_dim = 1.0
        if on_start is not None:
            on_off_dim = min(1.0, seconds - on_start)
        elif off_start is not None:
            on_off_dim = max(0.0, 1.0 - seconds + off_start)

        setting.dim = DIM * on_off_dim * dim_setting
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.02)


if __name__ == '__main__':
    main()
