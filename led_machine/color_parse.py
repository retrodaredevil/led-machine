from typing import List

from led_machine.color import Color


def parse_colors(text: str) -> List[Color]:
    text = text.lower()
    result: List[Color] = []
    for word in text.split():
        if word.startswith("#"):
            word = word[1:]
            if len(word) == 3:
                word = "".join(a * 2 for a in word)
            if len(word) == 6:
                try:
                    value = int(word[0:6], 16)
                    result.append(Color.from_24bit(value))
                except ValueError:
                    print(f"Couldn't parse: {repr(word)}")
            else:
                print(f"Cannot parse word: {repr(word)}")
    if "brown" in text or ("shallow" in text and "purple" in text):
        result.append(Color.from_bytes(165, 42, 23))
    if "purple" in text and "deep" in text:
        result.append(Color.from_bytes(255, 0, 70))
    if "purple" in text:
        result.append(Color.from_bytes(255, 0, 255))
    if "pink" in text:
        result.append(Color.from_bytes(255, 100, 120))
    if "red" in text:
        result.append(Color.from_bytes(255, 0, 0))
    if "green" in text:
        result.append(Color.from_bytes(0, 255, 0))
    if "blue" in text:
        result.append(Color.from_bytes(0, 0, 255))
    if "orange" in text:
        result.append(Color.from_bytes(255, 45, 0))
    if "yellow" in text:
        result.append(Color.from_bytes(255, 170, 0))
    if "teal" in text or "cyan" in text:
        result.append(Color.from_bytes(0, 255, 255))
    if "white" in text:
        result.append(Color.from_bytes(255, 255, 255))

    return result

