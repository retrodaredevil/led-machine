from typing import Tuple

import board
import neopixel
import time
import RPi.GPIO as GPIO

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

    while True:
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
                dim_amount = DIM * on_off_dim
                if i < 50:
                    dim_amount *= i / 50
                pixels[i] = (int(dim_amount * r * 255), int(dim_amount * g * 255), int(dim_amount * b * 255))
            pixels.show()
        time.sleep(.02)


if __name__ == '__main__':
    main()
