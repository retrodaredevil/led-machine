import sys
import time
import tkinter
from typing import List, Optional

from led_machine import ColorConstants, LedState, MessageContext, AlterMultiplexer, LedMetadata, handle_message
from led_machine.color import Color

'''
sudo apt install python3-tk
'''

NUMBER_OF_PIXELS = 450
PIXEL_SIZE = 3


def init_no_block():
    import fcntl
    import os
    import sys

    # make stdin a non-blocking file
    fd = sys.stdin.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    # thanks https://stackoverflow.com/a/1810703


def get_lines() -> List[str]:
    data = sys.stdin
    return data.readlines()


def main():
    init_no_block()
    top = tkinter.Tk()
    canvas = tkinter.Canvas(top)
    canvas.rowconfigure(0, weight=1)  # for making canvas resize with window https://stackoverflow.com/a/62440928
    canvas.columnconfigure(0, weight=1)

    main_led_state = LedState(NUMBER_OF_PIXELS)
    main_led_state.main_alter = main_led_state.parse_color_setting("rainbow")

    spots = [canvas.create_rectangle(i * PIXEL_SIZE, 0, (i + 1) * PIXEL_SIZE, PIXEL_SIZE * 6, fill="black") for i in range(NUMBER_OF_PIXELS)]
    old_colors: List[Optional[Color]] = [None] * NUMBER_OF_PIXELS

    canvas.pack(fill="both", expand=True)

    while True:

        for message in get_lines():
            text: str = message.lower()
            print(f"Got text: {repr(text)}")
            context = MessageContext()

            handle_message(text, main_led_state, False, context)

        seconds = time.time()

        setting = AlterMultiplexer([
            main_led_state.main_alter,
            main_led_state.pattern_alter,
        ])
        metadata = LedMetadata()

        for i, spot in enumerate(spots):
            color = setting.alter_pixel(seconds, i, None, metadata) or ColorConstants.BLACK
            old_color = old_colors[i]
            if old_color is None or old_color.tuple != color.tuple:
                new_color = f"#{color.tuple[0]:02x}{color.tuple[1]:02x}{color.tuple[2]:02x}"
                canvas.itemconfig(spot, fill=new_color)
                old_colors[i] = color

        top.update()


if __name__ == '__main__':
    main()
