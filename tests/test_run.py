import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stelar import config as C
from stelar import elements as E
from stelar.board import ring_size
from stelar.fates import fate_for
from stelar.run import Run


class FakeUI:
    def __init__(self):
        self.said, self.played = [], []

    def say(self, text, queue=False):
        self.said.append(text)

    def play(self, name, ring=None, angle=None, pitch=1.0):
        self.played.append((name, ring, angle))


def new_run(rings=2, seed=1):
    ui = FakeUI()
    over = []
    run = Run(ui, rings=rings, rng=random.Random(seed), on_over=over.append)
    return run, ui, over


def clear(run):
    for r, i in run.board.all_cells():
        run.board.set(r, i, None)


class NavigationTest(unittest.TestCase):
    def test_start_places_matter_and_speaks(self):
        run, ui, _ = new_run()
        run.start()
        self.assertEqual(run.board.count(E.H), C.START_MATTER)
        self.assertIn("núcleo", ui.said[-1])

    def test_up_goes_out_and_announces_ring_and_element(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(1, 0, E.HE)
        run.ring_out()
        self.assertEqual(ui.said[-1], "Anel 1. Hélio")
        self.assertEqual(ui.played[-1], ("elem_he", 1, 0.0))

    def test_edges(self):
        run, ui, _ = new_run()
        run.ring_in()
        self.assertEqual(ui.played[-1][0], "borda")
        run.ring_out()
        run.ring_out()
        run.ring_out()
        self.assertEqual(run.ring, 2)
        self.assertEqual(ui.played[-1][0], "borda")

    def test_left_right_walk_and_wrap(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(1, 5, E.C)
        run.ring_out()
        run.step(-1)
        self.assertEqual(run.index, 5)
        self.assertEqual(ui.said[-1], "Carbono")
        run.step(1)
        self.assertEqual(run.index, 0)

    def test_direction_is_kept_between_rings(self):
        run, ui, _ = new_run()
        run.ring_out()
        run.step(1)          # anel 1, casa 1 (1/6 de volta)
        run.ring_out()
        self.assertEqual(run.index, 2)
        run.ring_in()
        run.ring_in()
        run.ring_out()
        self.assertEqual(run.index, 1)

    def test_navigation_spends_no_turn(self):
        run, ui, _ = new_run()
        run.ring_out()
        run.step(1)
        self.assertEqual(run.turn, 0)


class ActionTest(unittest.TestCase):
    def test_collapse_scores_and_reports(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(0, 0, E.H)
        run.board.set(1, 0, E.H)
        self.assertTrue(run.collapse())
        self.assertEqual(run.score, E.POINTS[E.HE])
        self.assertEqual(run.turn, 1)
        self.assertIn("Fusão: 1 hélio. Mais 4 pontos.", ui.said[-1])
        self.assertIn(("fusao_he", 0, 0.0), ui.played)

    def test_combo_bonus(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(0, 0, E.H)
        run.board.set(1, 0, E.H)
        run.board.set(1, 3, E.HE)
        run.board.set(2, 6, E.HE)
        run.collapse()
        self.assertEqual(run.score, int((4 + 12) * (1 + C.COMBO_STEP)))
        self.assertIn("1 hélio e 1 carbono", ui.said[-1])

    def test_collapse_that_moves_nothing_is_not_a_turn(self):
        run, ui, _ = new_run()
        clear(run)
        self.assertFalse(run.collapse())
        self.assertEqual(run.turn, 0)

    def test_pressure_costs_energy_and_blows_outer_ring(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(2, 4, E.C)
        self.assertTrue(run.pressure())
        self.assertEqual(run.energy, C.START_ENERGY - C.PRESSURE_COST)
        self.assertIn("Vento estelar levou 1 carbono.", ui.said[-1])
        self.assertFalse(run.pressure())
        self.assertIn("Energia insuficiente", ui.said[-1])

    def test_energy_is_capped(self):
        run, ui, _ = new_run()
        clear(run)
        run.energy = C.MAX_ENERGY
        run.board.set(0, 0, E.C)
        run.board.set(1, 0, E.HE)
        run.collapse()
        self.assertEqual(run.energy, C.MAX_ENERGY)

    def test_core_does_not_rotate(self):
        run, ui, _ = new_run()
        self.assertFalse(run.rotate(1))
        self.assertEqual(run.turn, 0)

    def test_rotation_is_a_turn(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(1, 0, E.H)
        run.ring_out()
        run.rotate(1)
        self.assertEqual(run.board.get(1, 1), E.H)
        self.assertEqual(run.turn, 1)
        self.assertEqual(sum(1 for c in run.board.cells[2] if c), 1)   # matéria nova

    def test_full_star_chokes_into_iron(self):
        run, ui, _ = new_run()
        for r, i in run.board.all_cells():
            run.board.set(r, i, E.S if r else E.O)
        run.ring_out()
        run.rotate(1)
        self.assertEqual(run.board.count(E.FE), 1)
        self.assertIn("engasgou", ui.said[-1])


class EndTest(unittest.TestCase):
    def test_game_ends_when_inside_is_iron(self):
        run, ui, over = new_run()
        clear(run)
        for r in (0, 1):
            for i in range(ring_size(r)):
                run.board.set(r, i, E.FE)
        run.board.set(2, 0, E.H)
        run.ring_out()
        run.ring_out()
        run.rotate(1)
        self.assertTrue(run.over)
        self.assertEqual(over[0]["fate"], "ana-helio")

    def test_fates(self):
        self.assertEqual(fate_for(None, 0)[0], "ana-helio")
        self.assertEqual(fate_for(E.O, 100)[0], "ana-carbono")
        self.assertEqual(fate_for(E.MG, 100)[0], "ana-neonio")
        self.assertEqual(fate_for(E.S, 100)[0], "estrela-neutrons")
        self.assertEqual(fate_for(E.FE, 100)[0], "pulsar")
        self.assertEqual(fate_for(E.FE, C.BLACK_HOLE_SCORE)[0], "buraco-negro")

    def test_random_games_always_end(self):
        for rings in (2, 3):
            for seed in range(5):
                run, ui, over = new_run(rings, seed)
                run.start()
                rng = random.Random(seed)
                actions = [run.collapse, run.pressure, lambda: run.rotate(1),
                           run.ring_out, run.ring_in, lambda: run.step(1)]
                for _ in range(5000):
                    if run.over:
                        break
                    rng.choice(actions)()
                self.assertTrue(run.over)
                self.assertEqual(len(over), 1)


class TextTest(unittest.TestCase):
    def test_ring_text_groups_empty_cells(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(1, 0, E.H)
        run.board.set(1, 3, E.HE)
        run.ring_out()
        self.assertEqual(run.ring_text(),
                         "Anel 1, do foco para a direita: hidrogênio, 2 vazios, hélio, 2 vazios.")

    def test_focus_text_lists_partners(self):
        run, ui, _ = new_run()
        clear(run)
        run.board.set(0, 0, E.C)
        text = run.focus_text()
        self.assertIn("com hélio vira oxigênio", text)
        self.assertIn("com carbono vira neônio", text)

    def test_status_text(self):
        run, ui, _ = new_run()
        self.assertIn("Energia %d de %d" % (C.START_ENERGY, C.MAX_ENERGY), run.status_text())


if __name__ == "__main__":
    unittest.main()
