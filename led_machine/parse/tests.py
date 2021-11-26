import unittest

from led_machine.parse import StaticToken, PARENTHESIS_PARSE_PAIR, parse_to_tokens, StringToken, OrganizerToken

TIMES_TOKEN = StaticToken("times", "*")
PLUS_TOKEN = StaticToken("plus", "+")


class ParseTest(unittest.TestCase):
    static_tokens = [TIMES_TOKEN, PLUS_TOKEN]
    parse_pairs = [PARENTHESIS_PARSE_PAIR]

    def test_parse(self):
        text = "3 * 5 + 4 * 5"
        tokens = parse_to_tokens(text, self.static_tokens, self.parse_pairs)
        self.assertEqual([StringToken("3 "), TIMES_TOKEN, StringToken(" 5 "), PLUS_TOKEN, StringToken(" 4 "), TIMES_TOKEN, StringToken(" 5")], tokens)

    def test_parse_complex(self):
        text = "3 *( 5 + 4 )* 5"
        tokens = parse_to_tokens(text, self.static_tokens, self.parse_pairs)
        self.assertEqual(
            [StringToken("3 "), TIMES_TOKEN, OrganizerToken([StringToken(" 5 "), PLUS_TOKEN, StringToken(" 4 ")]), TIMES_TOKEN, StringToken(" 5")],
            tokens
        )

    def test_parse_super_complex(self):
        text = "3 *( 5 +(3 + 4))* 5"
        tokens = parse_to_tokens(text, self.static_tokens, self.parse_pairs)
        self.assertEqual(
            [
                StringToken("3 "), TIMES_TOKEN,
                OrganizerToken([StringToken(" 5 "), PLUS_TOKEN, OrganizerToken([StringToken("3 "), PLUS_TOKEN, StringToken(" 4")])]),
                TIMES_TOKEN, StringToken(" 5")
            ],
            tokens
        )


if __name__ == '__main__':
    unittest.main()
