from abc import ABC
from typing import Final, List


class Token(ABC):
    def __init__(self):
        pass


class StaticToken(Token):
    def __init__(self, name: str, pattern: str):
        super().__init__()
        self.name: Final[str] = name
        self.pattern: Final[str] = pattern

    def __str__(self):
        return f"StaticToken(name={self.name})"

    def __repr__(self):
        return str(self)


class NothingToken(Token):
    def __init__(self):
        super().__init__()


class StringToken(Token):
    def __init__(self, data: str):
        super().__init__()
        self.data = data

    def __eq__(self, other):
        return isinstance(other, StringToken) and other.data == self.data

    def __str__(self):
        return f"StringToken(data={self.data})"

    def __repr__(self):
        return str(self)


class OrganizerToken(Token):
    def __init__(self, tokens: List[Token]):
        super().__init__()
        self.tokens = tokens

    def __str__(self):
        return f"OrganizerToken(tokens={self.tokens})"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, OrganizerToken) and other.tokens == self.tokens

