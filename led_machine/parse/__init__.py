from dataclasses import dataclass
from typing import List, Callable, Tuple, Optional

from led_machine.parse.token import Token, StaticToken, NothingToken, OrganizerToken, StringToken


@dataclass
class ParsePair:
    start_pattern: str
    end_pattern: str
    condense_tokens: Callable[[List[Token]], Token]


COMMENT_PARSE_PAIR = ParsePair("/*", "*/", lambda tokens: NothingToken())
SINGLE_LINE_COMMENT_PARSE_PAIR = ParsePair("//", "\n", lambda tokens: NothingToken())
PARENTHESIS_PARSE_PAIR = ParsePair("(", ")", lambda tokens: OrganizerToken(tokens))


def __select_token(subtext: str, static_tokens: List[StaticToken]) -> Optional[StaticToken]:
    for static_token in static_tokens:
        if subtext.startswith(static_token.pattern):
            return static_token
    return None


def __select_start_parse_pair(subtext: str, parse_pairs: List[ParsePair]) -> Optional[ParsePair]:
    for parse_pair in parse_pairs:
        if subtext.startswith(parse_pair.start_pattern):
            return parse_pair
    return None


def __parse_to_tokens(
    start: int, current_parse_pair: Optional[ParsePair], text: str, static_tokens: List[StaticToken], parse_pairs: List[ParsePair]
) -> Tuple[int, bool, List[Token]]:
    def reset():
        nonlocal string_data
        if string_data:
            tokens.append(StringToken(string_data))
            string_data = ""
    string_data = ""
    tokens: List[Token] = []
    position = start
    while position < len(text):
        subtext = text[position:]
        if current_parse_pair is not None and subtext.startswith(current_parse_pair.end_pattern):
            reset()
            position += len(current_parse_pair.end_pattern)
            return position, True, tokens
        static_token = __select_token(subtext, static_tokens)
        if static_token is not None:
            reset()
            position += len(static_token.pattern)
            tokens.append(static_token)
            continue
        parse_pair = __select_start_parse_pair(subtext, parse_pairs)
        if parse_pair is not None:
            reset()
            position += len(parse_pair.start_pattern)
            new_position, ended_parse_pair, inner_tokens = __parse_to_tokens(position, parse_pair, text, static_tokens, parse_pairs)
            position = new_position
            if not ended_parse_pair:
                print(f"TODO make this an exception! ended_parse_pair=False! Someone didn't end with a {parse_pair.end_pattern}")
            # If you are getting a mypy error here, ignore it and update your mypy. https://github.com/python/mypy/issues/9975
            tokens.append(parse_pair.condense_tokens(inner_tokens))
            continue
        string_data += text[position]
        position += 1
    reset()
    return position, False, tokens


def parse_to_tokens(text: str, static_tokens: List[StaticToken], parse_pairs: List[ParsePair]) -> List[Token]:
    ended, ended_parse_pair, tokens = __parse_to_tokens(0, None, text, static_tokens, parse_pairs)
    if ended > len(text):
        raise AssertionError(f"ended should be <= len(text). ended={ended}")
    if ended < len(text):
        print(f"Did not exhaust text. ended={ended}")
    # We don't care about the value of ended_parse_pair. It should always be False since we didn't give it a ParsePair
    return tokens

