import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stelar import elements as E
from stelar.board import Board, children, index_at, parent, ring_size


class GeometryTest(unittest.TestCase):
    def test_ring_sizes(self):
        self.assertEqual([ring_size(r) for r in range(4)], [1, 6, 12, 18])

    def test_every_cell_has_a_parent_inside(self):
        for rings in (2, 3):
            for r in range(1, rings + 1):
                for i in range(ring_size(r)):
                    pr, pj = parent(r, i)
                    self.assertEqual(pr, r - 1)
                    self.assertIn((r, i), children(pr, pj, rings))

    def test_children_cover_outer_ring(self):
        kids = [c for j in range(6) for c in children(1, j, 2)]
        self.assertEqual(sorted(kids), [(2, i) for i in range(12)])
        self.assertEqual(children(1, 0, 2), [(2, 0), (2, 1)])

    def test_index_keeps_direction_between_rings(self):
        self.assertEqual(index_at(2, 0.25), 3)   # direita
        self.assertEqual(index_at(1, 0.25), 2)   # 0,25 * 6 = 1,5 -> casa 2
        self.assertEqual(index_at(1, 0.5), 3)    # trás


class FusionTableTest(unittest.TestCase):
    def test_basic_chain(self):
        self.assertEqual(E.fuse(E.H, E.H), E.HE)
        self.assertEqual(E.fuse(E.HE, E.HE), E.C)

    def test_helium_capture_is_symmetric(self):
        self.assertEqual(E.fuse(E.C, E.HE), E.O)
        self.assertEqual(E.fuse(E.HE, E.C), E.O)

    def test_iron_never_fuses(self):
        for sym in E.ORDER:
            self.assertIsNone(E.fuse(E.FE, sym))

    def test_everything_but_iron_scores(self):
        for product in set(E.FUSIONS.values()):
            self.assertGreater(E.POINTS[product], 0)


class CollapseTest(unittest.TestCase):
    def setUp(self):
        self.b = Board(2, random.Random(1))

    def test_falls_into_empty_core(self):
        self.b.set(1, 2, E.H)
        result = self.b.collapse()
        self.assertEqual(self.b.get(0, 0), E.H)
        self.assertIsNone(self.b.get(1, 2))
        self.assertEqual(result["moves"], [((1, 2), (0, 0))])

    def test_pair_fuses_in_the_inner_cell(self):
        self.b.set(0, 0, E.H)
        self.b.set(1, 4, E.H)
        result = self.b.collapse()
        self.assertEqual(self.b.get(0, 0), E.HE)
        self.assertEqual(result["fusions"], [(0, 0, E.HE)])

    def test_cell_fuses_only_once_per_collapse(self):
        self.b.set(0, 0, E.H)
        self.b.set(1, 0, E.H)
        self.b.set(1, 1, E.H)
        self.b.collapse()
        self.assertEqual(self.b.get(0, 0), E.HE)
        self.assertEqual(self.b.get(1, 1), E.H)

    def test_focus_decides_who_falls_first(self):
        self.b.set(1, 1, E.HE)
        self.b.set(1, 4, E.C)
        self.b.collapse(angle=4 / 6.0)
        self.assertEqual(self.b.get(0, 0), E.O)   # carbono caiu, hélio grudou
        self.b = Board(2, random.Random(1))
        self.b.set(1, 1, E.HE)
        self.b.set(1, 4, E.H)
        self.b.collapse(angle=4 / 6.0)
        self.assertEqual(self.b.get(0, 0), E.H)
        self.assertEqual(self.b.get(1, 1), E.HE)

    def test_outer_ring_fills_the_gap_left_inside(self):
        self.b.set(1, 0, E.H)
        self.b.set(2, 0, E.HE)
        self.b.collapse()
        self.assertEqual(self.b.get(0, 0), E.H)
        self.assertEqual(self.b.get(1, 0), E.HE)

    def test_falling_on_iron_becomes_iron(self):
        self.b.set(1, 0, E.FE)
        self.b.set(2, 1, E.C)
        result = self.b.collapse()
        self.assertEqual(self.b.get(1, 0), E.FE)
        self.assertEqual(self.b.get(2, 1), E.FE)
        self.assertEqual(result["infected"], [(2, 1)])

    def test_iron_does_not_move(self):
        self.b.set(1, 3, E.FE)
        self.b.collapse()
        self.assertEqual(self.b.get(1, 3), E.FE)
        self.assertIsNone(self.b.get(0, 0))


class PressureAndRotationTest(unittest.TestCase):
    def setUp(self):
        self.b = Board(2, random.Random(1))

    def test_outer_ring_is_blown_away_but_not_iron(self):
        self.b.set(2, 5, E.SI)
        self.b.set(2, 6, E.FE)
        result = self.b.pressure()
        self.assertEqual(result["ejected"], [(2, 5, E.SI)])
        self.assertIsNone(self.b.get(2, 5))
        self.assertEqual(self.b.get(2, 6), E.FE)

    def test_everything_moves_one_ring_out(self):
        self.b.set(0, 0, E.C)
        self.b.set(1, 0, E.HE)
        self.b.pressure()
        self.assertEqual(self.b.get(2, 0), E.HE)
        self.assertEqual(self.b.get(1, 0), E.C)
        self.assertIsNone(self.b.get(0, 0))

    def test_core_goes_toward_the_focus(self):
        self.b.set(0, 0, E.C)
        self.b.pressure(angle=0.5)
        self.assertEqual(self.b.get(1, 3), E.C)

    def test_rotation(self):
        self.b.set(1, 0, E.H)
        self.b.rotate(1, 1)
        self.assertEqual(self.b.get(1, 1), E.H)
        self.b.rotate(1, -1)
        self.b.rotate(1, -1)
        self.assertEqual(self.b.get(1, 5), E.H)
        self.assertFalse(self.b.rotate(0, 1))


class SpawnAndDeathTest(unittest.TestCase):
    def test_spawn_goes_to_outer_ring(self):
        b = Board(3, random.Random(2))
        for _ in range(18):
            r, i = b.spawn(E.H)
            self.assertEqual(r, 3)
        self.assertIsNone(b.spawn(E.H))

    def test_choke_turns_outer_cell_to_iron_first(self):
        b = Board(2, random.Random(2))
        r, i = b.choke()
        self.assertEqual(r, 2)
        self.assertEqual(b.get(r, i), E.FE)

    def test_dead_when_inside_is_all_iron(self):
        b = Board(2, random.Random(2))
        for r in (0, 1):
            for i in range(ring_size(r)):
                b.set(r, i, E.FE)
        self.assertTrue(b.is_dead())
        b.set(1, 3, E.H)
        self.assertFalse(b.is_dead())


if __name__ == "__main__":
    unittest.main()
