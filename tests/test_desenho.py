"""A tela do Stelar Flow, com gráficos de mentira: a estrela cabe, cada casa
encosta na casa onde cai, cada uma usa o desenho do seu elemento, o painel
mostra o que o Y fala, e a tela nunca derruba o jogo."""
import math
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fakegfx import RecordingGfx  # noqa: E402

from stelar import desenho as D  # noqa: E402
from stelar import elements as E  # noqa: E402
from stelar.board import angle_of, parent, ring_size  # noqa: E402
from stelar.run import Run  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class UI:
    def __init__(self):
        self.said = []

    def say(self, text, queue=False):
        self.said.append(text)

    def play(self, *a, **kw):
        pass


class Menu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def frame(run=None, menu=None, caption=""):
    gfx = RecordingGfx(ROOT)
    D.draw_frame(gfx, gfx.image("graficos/casas.png"), D.Fonts(gfx), run, menu, caption)
    return gfx


def tiles(gfx):
    """[(x, y do centro, índice do quadro na folha)], lido do que foi desenhado."""
    return [(x + D.TILE_W // 2, y + D.TILE_H // 2, src[0] // D.TILE_W)
            for _, path, x, y, src in gfx.draws()]


def near(center, seen):
    cx, cy = center
    return [k for x, y, k in seen if abs(x - cx) <= 1 and abs(y - cy) <= 1]


class GeometryTest(unittest.TestCase):
    def test_cells_are_distinct_and_fit(self):
        for rings in (2, 3):
            centers = [D.cell_center(r, i) for r in range(rings + 1) for i in range(ring_size(r))]
            for cx, cy in centers:
                self.assertGreaterEqual(cx - D.TILE_W / 2.0, 0)
                self.assertLessEqual(cx + D.TILE_W / 2.0, D.PANEL_X - 4)
                self.assertGreaterEqual(cy - D.TILE_H / 2.0, D.TOP_BAR)
                self.assertLessEqual(cy + D.TILE_H / 2.0, D.CAPTION_Y)
            for a in range(len(centers)):
                for b in range(a):
                    gap = math.hypot(centers[a][0] - centers[b][0], centers[a][1] - centers[b][1])
                    self.assertGreater(gap, D.SIDE * D.SQ3 - 0.5)

    def test_each_cell_touches_where_it_falls(self):
        """Vizinhos no favo ficam a SIDE*sqrt(3) de distância."""
        for r in range(1, 4):
            for i in range(ring_size(r)):
                a, b = D.cell_center(r, i), D.cell_center(*parent(r, i))
                self.assertAlmostEqual(math.hypot(a[0] - b[0], a[1] - b[1]), D.SIDE * D.SQ3,
                                       delta=0.01, msg=(r, i))

    def test_direction_matches_the_3d_sound(self):
        """Frente em cima, direita à direita, como o som."""
        for r in range(1, 4):
            for i in range(ring_size(r)):
                x, y = D.cell_center(r, i)
                dx, dy = x - D.CENTER[0], y - D.CENTER[1]
                a = 2 * math.pi * angle_of(r, i)
                # mesma metade da tela que o som: seno para os lados, cosseno para a frente
                if abs(math.sin(a)) > 0.3:
                    self.assertEqual(dx > 0, math.sin(a) > 0, (r, i))
                if abs(math.cos(a)) > 0.3:
                    self.assertEqual(dy < 0, math.cos(a) > 0, (r, i))


class DrawTest(unittest.TestCase):
    def test_tiles_follow_the_board(self):
        rng = random.Random(4)
        run = Run(UI(), rng=rng)
        pool = list(E.ORDER) + [None, None]
        for r, i in run.board.all_cells():
            run.board.set(r, i, rng.choice(pool))
        seen = tiles(frame(run))
        for r, i in run.board.all_cells():
            hits = near(D.cell_center(r, i), seen)
            expected = D.tile_index(run.board.get(r, i), core=(r == 0))
            self.assertIn(expected, hits, (r, i))

    def test_focus_is_drawn_last_on_the_focused_cell(self):
        run = Run(UI(), rng=random.Random(1))
        run.ring, run.angle = 2, 5 / 12.0
        gfx = frame(run)
        last = gfx.draws()[-1]
        self.assertEqual(last[4][0] // D.TILE_W, D.T_FOCUS)
        cx, cy = D.cell_center(2, 5)
        self.assertLessEqual(abs(last[2] + D.TILE_W // 2 - cx), 1)
        self.assertLessEqual(abs(last[3] + D.TILE_H // 2 - cy), 1)

    def test_no_focus_after_the_end(self):
        run = Run(UI(), rng=random.Random(1))
        run.over = True
        kinds = [d[4][0] // D.TILE_W for d in frame(run).draws()]
        self.assertNotIn(D.T_FOCUS, kinds)

    def test_bar_and_panel(self):
        run = Run(UI(), rng=random.Random(1))
        run.ring, run.angle = 1, 0.0
        run.board.set(1, 0, E.HE)
        run.score, run.energy, run.turn, run.heaviest = 128, 4, 17, E.O
        run.board.set(2, 3, E.FE)
        texts = frame(run).texts()
        self.assertIn("Anel 1  ·  Órion", texts)
        self.assertIn("Hélio", texts)
        self.assertIn("128", texts)
        self.assertIn("Energia 4 de 9", texts)
        self.assertIn("Ferro 1 de 37", texts)
        self.assertIn("Turno 17", texts)
        self.assertIn("Oxigênio", texts)
        run.ring = 0
        self.assertIn("Núcleo", frame(run).texts())

    def test_menus(self):
        texts = frame(menu=Menu("Stelar Flow", ["Jogar", "Como jogar", "Sair"], 1)).texts()
        self.assertIn("Como jogar", texts)
        run = Run(UI(), rng=random.Random(1))
        texts = frame(run, Menu("Pausa", ["Continuar", "Sair sem salvar"])).texts()
        self.assertIn("Pausa", texts)

    def test_long_caption_shows_the_end(self):
        texts = frame(caption=" ".join(["palavra%d" % k for k in range(80)])).texts()
        self.assertTrue(any("palavra79" in t for t in texts))


class FakeGame:
    def __init__(self):
        self.dir = ROOT
        self._focus = []
        self.said = []
        self.updates, self.quits = [], []

    def on_update(self, fn):
        self.updates.append(fn)

    def on_quit(self, fn):
        self.quits.append(fn)

    def say(self, text, queue=False, on_done=None):
        self.said.append(text)


class TestRenderer(D.Renderer):
    def open(self):
        self.gfx = RecordingGfx(ROOT)
        self.gfx.fail = getattr(self, "broken", False)
        self.sheet = self.gfx.image("graficos/casas.png")
        self.fonts = D.Fonts(self.gfx)
        return True


class RendererTest(unittest.TestCase):
    def setUp(self):
        self.saved_env = dict(os.environ)
        fd, self.conf = tempfile.mkstemp()
        os.close(fd)
        os.environ["A11Y_SISTEMA_CONF"] = self.conf
        os.environ.pop("A11Y_GRAPHICS", None)
        with open(self.conf, "w") as f:
            f.write("SCREEN=1\n")

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved_env)
        os.remove(self.conf)

    def test_draws_with_caption_and_survives_failure(self):
        game = FakeGame()
        state = {"run": Run(UI(), rng=random.Random(1))}
        r = TestRenderer(game, lambda: state["run"])
        game.say("Hélio, Órion.")
        r.update(1.0)
        self.assertEqual(r.gfx.frames, 1)
        self.assertIn("Hélio, Órion.", r.gfx.texts())
        r.close()
        r.broken = True
        r.update(1.0)
        self.assertTrue(r.failed)
        game.say("O jogo segue.")
        self.assertEqual(game.said[-1], "O jogo segue.")

    def test_finished_run_stays_until_a_menu_opens(self):
        game = FakeGame()
        run = Run(UI(), rng=random.Random(1))
        state = {"run": run}
        r = TestRenderer(game, lambda: state["run"])
        self.assertIs(r.scene()[0], run)
        state["run"] = None
        self.assertIs(r.scene()[0], run)
        game._focus.append(Menu("Stelar Flow", ["Jogar"]))
        self.assertIsNone(r.scene()[0])

    def test_screen_off(self):
        os.environ["A11Y_GRAPHICS"] = "0"
        game = FakeGame()
        r = TestRenderer(game, lambda: None)
        r.update(1.0)
        self.assertIsNone(r.gfx)

    def test_power_saving_lowers_the_frame_rate(self):
        with open(self.conf, "w") as f:
            f.write("SCREEN=1\nENERGY=aggressive\n")
        self.assertEqual(D.frame_interval(), 0.2)


if __name__ == "__main__":
    unittest.main()
