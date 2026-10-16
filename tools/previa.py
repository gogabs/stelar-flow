#!/usr/bin/env python3
"""Gera prévias das telas do Stelar Flow em PNG, sem console (precisa do Pillow).

    python3 tools/previa.py [pasta-de-saída]
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from pilgfx import PilGfx  # noqa: E402

from stelar import desenho as D  # noqa: E402
from stelar import elements as E  # noqa: E402
from stelar.run import Run  # noqa: E402


class UI:
    def __init__(self):
        self.last = ""

    def say(self, text, queue=False):
        self.last = (self.last + " " + text) if queue else text

    def play(self, *a, **kw):
        pass


class FakeMenu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


def shot(name, run=None, menu=None, caption="", out="."):
    gfx = PilGfx(ROOT)
    D.draw_frame(gfx, gfx.image("graficos/casas.png"), D.Fonts(gfx), run, menu, caption)
    path = os.path.join(out, name + ".png")
    gfx.save(path)
    print(path)


def play(run, rng, turns):
    """Joga como o robô guloso de tools/simular.py, só que mais simples:
    colapsa quando dá, usa a pressão quando o anel de fora enche."""
    for _ in range(turns):
        if run.over:
            break
        outer = run.board.empty_cells(run.rings)
        if not outer and run.energy >= 3:
            run.pressure()
        elif not run.collapse():
            run.ring = rng.randrange(1, run.rings + 1)
            run.rotate(rng.choice((-1, 1)))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    shot("1-menu", menu=FakeMenu("Stelar Flow", ["Continuar partida salva", "Novo jogo",
                                                 "Como jogar", "Recordes e finais", "Sair"], 1),
         caption="Stelar Flow. Novo jogo, 2 de 5.", out=out)
    ui = UI()
    run = Run(ui, rng=random.Random(3))
    run.start()
    shot("2-inicio", run=run, caption=ui.last, out=out)
    ui = UI()
    run = Run(ui, rng=random.Random(11))
    run.start()
    play(run, random.Random(5), 60)
    run.ring, run.angle = 2, 4 / 12.0
    run.announce_focus(with_ring=True)
    shot("3-meio", run=run, caption=ui.last, out=out)
    # uma estrela mais velha, com todos os elementos e ferro
    ui = UI()
    run = Run(ui, rng=random.Random(4))
    rng = random.Random(8)
    pool = list(E.ORDER) + [None] * 4
    for r, i in run.board.all_cells():
        run.board.set(r, i, rng.choice(pool))
    run.board.set(0, 0, E.FE)
    run.score, run.energy, run.turn, run.heaviest = 1840, 5, 212, E.FE
    run.ring, run.angle = 1, 2 / 6.0
    run.say = ui.say
    ui.say(run.collapse_preview())
    shot("4-ferro", run=run, caption=ui.last, out=out)
    shot("5-pausa", run=run, menu=FakeMenu("Pausa", ["Continuar", "Salvar e sair para o menu",
                                                     "Sair sem salvar"], 0),
         caption="Pausa. Continuar, 1 de 3.", out=out)


if __name__ == "__main__":
    main()
