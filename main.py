from typing import Tuple

import board
import neopixel
import time


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

    while True:
        percent = (time.time() / 6) % 1
        for pixels in pixels_list:
            for i in range(len(pixels)):
                pixels[i] = get_rainbow((percent + i * 0.02) % 1)
        time.sleep(0.1)


if __name__ == '__main__':
    main()
