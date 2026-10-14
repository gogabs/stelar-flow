import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stelar.board import parent, ring_size
from stelar.names import at, cell_name, of, the


class NamesTest(unittest.TestCase):
    def test_every_name_is_unique(self):
        names = [cell_name(r, i) for r in range(4) for i in range(ring_size(r))]
        self.assertEqual(len(names), len(set(names)))

    def test_name_says_where_the_cell_falls(self):
        for r in (2, 3):
            for i in range(ring_size(r)):
                self.assertTrue(cell_name(r, i).startswith(cell_name(*parent(r, i)) + " "))

    def test_examples(self):
        self.assertEqual(cell_name(1, 0), "Órion")
        self.assertEqual(cell_name(2, 1), "Órion Rigel")
        self.assertEqual(cell_name(3, 1), "Órion Betelgeuse beta")
        self.assertEqual(cell_name(3, 2), "Órion Rigel alfa")

    def test_prepositions(self):
        self.assertEqual(at((0, 0)), "no núcleo")
        self.assertEqual(at((1, 2)), "em Lira")
        self.assertEqual(of((0, 0)), "do núcleo")
        self.assertEqual(of((2, 3)), "de Escorpião Sargas")
        self.assertEqual(the((0, 0)), "o núcleo")


if __name__ == "__main__":
    unittest.main()
