from typing import List

from led_machine.color import Color


def parse_colors(text: str) -> List[Color]:
    text = text.lower()
    result: List[Color] = []
    word_list = text.split()
    for i, word in enumerate(word_list):
        previous_word = None if i == 0 else word_list[i - 1]
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
        elif "brown" in word:
            result.append(Color.from_bytes(165, 42, 23))
        elif "purple" in word and ("deep" in word or (previous_word is not None and "deep" in previous_word)):
            result.append(Color.from_bytes(255, 0, 70))
        elif "purple" in word and ("hot" in word or (previous_word is not None and "hot" in previous_word)):
            result.append(Color(r=1.0, g=0.0, b=0.9642934927623834))
        elif "purple" in word:
            result.append(Color.from_bytes(255, 0, 255))
        elif "pink" in word:
            result.append(Color.from_bytes(255, 100, 120))
        elif "red" in word:
            result.append(Color.from_bytes(255, 0, 0))
        elif "green" in word:
            result.append(Color.from_bytes(0, 255, 0))
        elif "blue" in word:
            result.append(Color.from_bytes(0, 0, 255))
        elif "orange" in word:
            result.append(Color.from_bytes(255, 45, 0))
        elif "tiger" in word:
            result.append(Color(r=1.0, g=0.7072935145244612, b=0.0))
        elif "yellow" in word:
            result.append(Color.from_bytes(255, 170, 0))
        elif "teal" in word or "cyan" in word:
            result.append(Color.from_bytes(0, 255, 255))
        elif "white" in word:
            result.append(Color.from_bytes(255, 255, 255))

    return result

