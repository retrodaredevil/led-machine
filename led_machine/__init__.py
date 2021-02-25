import time
import json
from pathlib import Path


from led_machine.rainbow import RainbowSetting
from led_machine.settings import DimSetting, FrontDimSetting, SolidSetting
from led_machine.slack import SlackHelper

DIM = 0.8
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
    slack = SlackHelper(slack_token, slack_channel)

    main_setting_holder = FrontDimSetting(RainbowSetting())
    setting = DimSetting(main_setting_holder, DIM)
    while True:
        slack.update()
        for message in slack.new_messages():
            text: str = message["text"].lower()
            if "purple" in text:
                main_setting_holder.setting = SolidSetting((255, 0, 180))
            elif "red" in text:
                main_setting_holder.setting = SolidSetting((255, 0, 0))
            elif "rainbow" in text:
                main_setting_holder.setting = RainbowSetting()
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

        setting.dim = DIM * on_off_dim
        setting.apply(seconds, pixels_list)
        for pixels in pixels_list:
            pixels.show()

        time.sleep(.02)


if __name__ == '__main__':
    main()
