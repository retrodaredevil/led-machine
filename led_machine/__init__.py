import json
import time
from pathlib import Path

from led_machine.alter import AlterDim, AlterMultiplexer, LedMetadata
from led_machine.block import AlterBlock
from led_machine.color import ColorConstants
from led_machine.color_parse import parse_colors
from led_machine.handler import LedState, handle_message, MessageContext, LedConstants, START_PIXELS_TO_HIDE
from led_machine.partition import AlterPartition
from led_machine.percent import ReversingPercentGetter, BouncePercentGetter, MultiplierPercentGetter, \
    PercentGetterHolder, PercentGetterTimeMultiplier, ConstantPercentGetter, SumPercentGetter, SmoothPercentGetter
from led_machine.slack import SlackHelper

NUMBER_OF_PIXELS = 450
# VIRTUAL_PIXELS = NUMBER_OF_PIXELS - START_PIXELS_TO_HIDE

# TODO most of these imports are used in main. They pollute the namespace and confuse people. Do something about it eventually


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

    main_led_state = LedState(NUMBER_OF_PIXELS)
    main_led_state.main_alter = main_led_state.parse_color_setting("rainbow")

    josh_lamp_led_state = LedState(NUMBER_OF_PIXELS)
    alter_dim = AlterDim(0.8)
    # dimmer_percent_getter = PercentGetterHolder(ConstantPercentGetter(1.0))
    # """A percent getter which stores a percent getter that dynamically controls the brightness of the lights."""
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

            dim_setting = None
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
            if dim_setting is not None:
                alter_dim.dim = dim_setting

        seconds = time.time()

        setting = AlterMultiplexer([
            main_led_state.main_alter,
            main_led_state.pattern_alter,
            AlterPartition([(AlterMultiplexer([
                josh_lamp_led_state.main_alter, josh_lamp_led_state.pattern_alter
            ]), [(START_PIXELS_TO_HIDE, 17), (NUMBER_OF_PIXELS - 19, 19)])]),
            AlterBlock([(ColorConstants.BLACK, START_PIXELS_TO_HIDE), (None, NUMBER_OF_PIXELS - START_PIXELS_TO_HIDE)], ConstantPercentGetter(0.0), fade=False),
            alter_dim
        ])
        # setting.dim = DIM * dim_setting * dimmer_percent_getter.get_percent(seconds)
        metadata = LedMetadata()
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = setting.alter_pixel(seconds, i, None, metadata) or ColorConstants.BLACK

        for pixels in pixels_list:
            pixels.show()

        time.sleep(.001)


if __name__ == '__main__':
    main()
