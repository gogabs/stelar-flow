"""Uma partida: a grade, o foco, os turnos, os pontos e o que é anunciado.

Não toca som nem fala direto: tudo passa por `ui`, que tem
    ui.say(texto, queue=False)
    ui.play(nome, ring=None, angle=None, pitch=1.0)
Assim a partida inteira roda nos testes sem áudio.
"""
import random

from . import config as C
from . import elements as E
from .board import Board, angle_of, index_at, ring_size
from .fates import fate_for


def ring_name(r):
    return "Núcleo" if r == 0 else "Anel %d" % r


def plural(n, sym):
    word = E.name(sym).lower()
    return "%d %s" % (n, word if n == 1 else word + "s")


def join(parts):
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " e " + parts[-1]


class Run:
    def __init__(self, ui, rings=C.RINGS, rng=None, on_over=None):
        self.ui = ui
        self.rng = rng or random.Random()
        self.board = Board(rings, self.rng)
        self.rings = rings
        self.on_over = on_over
        self.ring = 0
        self.angle = 0.0
        self.score = 0
        self.energy = C.START_ENERGY
        self.turn = 0
        self.heaviest = None
        self.made = {}
        self.ejected = {}
        self.over = False

    def start(self):
        for _ in range(C.START_MATTER):
            self.board.spawn(E.H)
        self.ui.play("inicio")
        self.ui.say("A estrela acendeu, com %d anéis em volta do núcleo. Hidrogênio entrando "
                    "pelo anel de fora. Você está no núcleo, vazio." % self.rings)

    # --- foco ------------------------------------------------------------
    @property
    def index(self):
        return index_at(self.ring, self.angle)

    def focused(self):
        return self.board.get(self.ring, self.index)

    def _play_cell(self, r, i, prefix="elem"):
        sym = self.board.get(r, i)
        self.ui.play("%s_%s" % (prefix, sym.lower() if sym else "vazio"),
                     ring=r, angle=angle_of(r, i))

    def announce_focus(self, with_ring=False):
        self._play_cell(self.ring, self.index)
        text = E.name(self.focused())
        if with_ring:
            text = "%s. %s" % (ring_name(self.ring), text)
        self.ui.say(text)

    def ring_out(self):
        if self.ring >= self.rings:
            self.ui.play("borda")
            self.ui.say("Anel de fora. " + E.name(self.focused()))
            return
        self.ring += 1
        self.announce_focus(with_ring=True)

    def ring_in(self):
        if self.ring == 0:
            self.ui.play("borda")
            self.ui.say("Núcleo. " + E.name(self.focused()))
            return
        self.ring -= 1
        self.announce_focus(with_ring=True)

    def step(self, delta):
        """Esquerda (-1) e direita (+1): anda pelo anel."""
        if self.ring == 0:
            self.ui.play("borda")
            self.ui.say("Núcleo. " + E.name(self.focused()))
            return
        n = ring_size(self.ring)
        self.angle = ((self.index + delta) % n) / float(n)
        self.announce_focus()

    # --- ações (cada uma é um turno) ------------------------------------
    def collapse(self):
        result = self.board.collapse(self.angle)
        if not (result["moves"] or result["fusions"] or result["infected"]):
            self.ui.play("borda")
            self.ui.say("Colapso: nada se moveu.")
            return False
        self.ui.play("colapso")
        parts = []
        fusions = result["fusions"]
        if fusions:
            gained, energy = 0, 0
            counts = {}
            for r, i, product in fusions:
                gained += E.POINTS[product]
                energy += E.ENERGY_GAIN[product]
                counts[product] = counts.get(product, 0) + 1
                self.made[product] = self.made.get(product, 0) + 1
                if self.heaviest is None or E.mass_rank(product) > E.mass_rank(self.heaviest):
                    self.heaviest = product
                self.ui.play("fusao_%s" % product.lower(), ring=r, angle=angle_of(r, i))
            gained = int(gained * (1 + C.COMBO_STEP * (len(fusions) - 1)))
            self.score += gained
            self.energy = min(C.MAX_ENERGY, self.energy + energy)
            made = [plural(n, sym) for sym, n in sorted(counts.items(), key=lambda t: E.mass_rank(t[0]))]
            parts.append("Fusão: %s. Mais %d pontos." % (join(made), gained))
            if E.FE in counts:
                parts.append("Cuidado, isso é ferro.")
        else:
            parts.append("Colapso sem fusão.")
        infected = result["infected"]
        if infected:
            for r, i in infected:
                self.ui.play("infeccao", ring=r, angle=angle_of(r, i))
            parts.append("%s engolido%s pelo ferro." % (
                "1 elemento" if len(infected) == 1 else "%d elementos" % len(infected),
                "" if len(infected) == 1 else "s"))
        self._end_turn(parts)
        return True

    def pressure(self):
        if self.energy < C.PRESSURE_COST:
            self.ui.play("borda")
            self.ui.say("Energia insuficiente: %d de %d." % (self.energy, C.PRESSURE_COST))
            return False
        result = self.board.pressure(self.angle)
        if not (result["moves"] or result["ejected"]):
            self.ui.play("borda")
            self.ui.say("Pressão: não há espaço para empurrar nada.")
            return False
        self.energy -= C.PRESSURE_COST
        self.ui.play("pressao")
        parts = ["Pressão de radiação."]
        if result["ejected"]:
            counts = {}
            for r, i, sym in result["ejected"]:
                counts[sym] = counts.get(sym, 0) + 1
                self.ejected[sym] = self.ejected.get(sym, 0) + 1
            blown = [plural(n, sym) for sym, n in sorted(counts.items(), key=lambda t: E.mass_rank(t[0]))]
            parts.append("Vento estelar levou %s." % join(blown))
        parts.append("Energia %d." % self.energy)
        self._end_turn(parts)
        return True

    def rotate(self, step):
        if self.ring == 0:
            self.ui.play("borda")
            self.ui.say("O núcleo não gira. Suba para um anel.")
            return False
        self.board.rotate(self.ring, step)
        self.ui.play("rotacao")
        self._end_turn(["%s girou para a %s." % (ring_name(self.ring),
                                                  "direita" if step > 0 else "esquerda")])
        return True

    def _end_turn(self, parts):
        self.turn += 1
        sym = self.rng.choices([s for s, _ in C.SPAWN_TABLE], [w for _, w in C.SPAWN_TABLE])[0]
        cell = self.board.spawn(sym)
        if cell is not None:
            self.ui.play("entrada_%s" % sym.lower(), ring=cell[0], angle=angle_of(*cell))
            if sym != E.H:
                parts.append("Entrou %s." % E.name(sym).lower())
        else:
            choked = self.board.choke()
            if choked is not None:
                self.ui.play("infeccao", ring=choked[0], angle=angle_of(*choked))
            parts.append("A estrela engasgou: sem espaço para matéria nova, uma casa virou ferro.")
        if self.board.is_dead():
            self.ui.say(" ".join(parts))
            self.finish()
            return
        parts.append("No foco, %s." % E.name(self.focused()).lower())
        self.ui.say(" ".join(parts))

    def finish(self):
        self.over = True
        fate = fate_for(self.heaviest, self.score)
        self.ui.play("fim")
        if self.on_over:
            self.on_over({"score": self.score, "turns": self.turn, "heaviest": self.heaviest,
                          "fate": fate[0], "rings": self.rings, "made": dict(self.made)})

    # --- informação (não gasta turno) ------------------------------------
    def status_text(self):
        iron = self.board.count(E.FE)
        heaviest = E.name(self.heaviest).lower() if self.heaviest else "nenhum ainda"
        return ("%d pontos. Energia %d de %d. Ferro em %d de %d casas. Turno %d. "
                "Elemento mais pesado: %s." % (
                    self.score, self.energy, C.MAX_ENERGY, iron, len(self.board.all_cells()),
                    self.turn, heaviest))

    def ring_text(self):
        """O anel em foco inteiro, começando pelo foco e seguindo para a direita."""
        if self.ring == 0:
            return "Núcleo: %s." % E.name(self.focused())
        n = ring_size(self.ring)
        items, empties = [], 0
        for k in range(n):
            sym = self.board.get(self.ring, (self.index + k) % n)
            if sym is None:
                empties += 1
                continue
            if empties:
                items.append("vazio" if empties == 1 else "%d vazios" % empties)
                empties = 0
            items.append(E.name(sym).lower())
        if empties:
            items.append("vazio" if empties == 1 else "%d vazios" % empties)
        return "%s, do foco para a direita: %s." % (ring_name(self.ring), ", ".join(items))

    def focus_text(self):
        """Onde está o foco e com o que o elemento funde."""
        sym = self.focused()
        where = ring_name(self.ring)
        if self.ring:
            where += ", posição %d de %d" % (self.index + 1, ring_size(self.ring))
        if sym is None:
            return "Vazio. %s." % where
        if sym == E.FE:
            return "Ferro. %s. Não se move nem funde; quem cair nele vira ferro." % where
        fuses = ["com %s vira %s" % (E.name(b).lower(), E.name(p).lower()) for b, p in E.partners(sym)]
        return "%s. %s. Funde: %s." % (E.name(sym), where, join(fuses))
