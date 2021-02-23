from typing import Tuple

import board
import neopixel
import time

DIM = 0.8


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
        percent = (time.time() / 6) % 1
        for pixels in pixels_list:
            for i in range(len(pixels)):
                color = get_rainbow((percent + i * 0.02) % 1)
                r = color[0] / 255
                g = color[1] / 255
                b = color[2] / 255

                if i >= 240:
                    r **= 1.8
                    g **= 1.7
                    b **= 0.1
                elif i >= 200:
                    r **= 1.4
                    g **= 1.2
                    b **= 0.2
                elif i >= 150:
                    r **= 1.2
                    g **= 1.1
                    b **= 0.3
                pixels[i] = (DIM * r * 255, DIM * g * 255, DIM * b * 255)
            pixels.show()
        time.sleep(.1)


if __name__ == '__main__':
    main()
