import unittest

from led_machine.color import Color


class ColorTest(unittest.TestCase):
    def test_color(self):
        for t in [(200, 100, 50), (0, 0, 0), (255, 255, 255)]:
            r, g, b = t
            nr, ng, nb = (r / 255, g / 255, b / 255)
            color1 = Color.from_tuple(t)
            color2 = Color.from_bytes(r, g, b)
            print(color2)
            self.assertEqual(color1, color2)
            self.assertEqual(r, color1[0])
            self.assertEqual(g, color1[1])
            self.assertEqual(b, color1[2])
            self.assertEqual(nr, color1._r)
            self.assertEqual(ng, color1._g)
            self.assertEqual(nb, color1._b)


if __name__ == '__main__':
    unittest.main()
