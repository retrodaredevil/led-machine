from typing import Tuple

import board
import neopixel
import time

DIM = 0.8
PERIOD = 2.0
DIRECTION_PERIOD = 20.0
REVERSE_PERIOD = 2.0
LED_SPREAD = 50

assert DIRECTION_PERIOD % PERIOD == 0, "The direction period must be a multiple of period!"
assert REVERSE_PERIOD % PERIOD == 0, "The reverse period must be a multiple of period!"


def get_rainbow(percent: float) -> Tuple:
    spot = int(percent * 6)
    sub = (percent * 6) % 1
    amount = int(256 * sub)
    if spot == 0:  # add red
        return amount, 255, 0
    elif spot == 1:  # remove green
        return 255, 255 - amount, 0
    elif spot == 2:  # add blue
        return 255, 0, amount
    elif spot == 3:  # remove red
        return 255 - amount, 0, 255
    elif spot == 4:  # add green
        return 0, amount, 255
    else:  # remove blue
        return 0, 255, 255 - amount


def main():
    pixels_list = [
        neopixel.NeoPixel(board.D18, 300),  # AKA GPIO 18
    ]
    pixels_list[0].auto_write = False

    while True:
        seconds = time.time()
        spot = seconds % (DIRECTION_PERIOD * 2)
        percent = (seconds / PERIOD) % 1
        if spot <= REVERSE_PERIOD:
            a = PERIOD / REVERSE_PERIOD
            x = (spot - REVERSE_PERIOD / 2) / PERIOD
            height = REVERSE_PERIOD / 4 / PERIOD
            percent = a * x * x + 1 - height
        elif DIRECTION_PERIOD <= spot <= (DIRECTION_PERIOD + REVERSE_PERIOD):
            # x = (spot - DIRECTION_PERIOD - PERIOD * 2) / (PERIOD * 2)

            a = PERIOD / REVERSE_PERIOD
            x = (spot - DIRECTION_PERIOD - REVERSE_PERIOD / 2) / PERIOD
            height = REVERSE_PERIOD / 4 / PERIOD
            # percent = 1 - (x * x)
            percent = 1 - (a * x * x + 1 - height)
        elif spot > DIRECTION_PERIOD + PERIOD:
            percent *= -1

        for pixels in pixels_list:
            for i in range(len(pixels)):
                color = get_rainbow((percent + i / LED_SPREAD) % 1)
                r = color[0] / 255
                g = color[1] / 255
                b = color[2] / 255
                if i < 50:
                    dim_amount = i / 50
                    r *= dim_amount
                    g *= dim_amount
                    b *= dim_amount
                pixels[i] = (DIM * r * 255, DIM * g * 255, DIM * b * 255)
            pixels.show()
        time.sleep(.02)


if __name__ == '__main__':
    main()
