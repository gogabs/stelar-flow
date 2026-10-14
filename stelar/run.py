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
from .names import at, cell_name, of, the


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

    def focus_label(self):
        """ "Hélio, Órion Rigel": o elemento e o nome da casa (o núcleo não tem nome)."""
        text = E.name(self.focused())
        if self.ring:
            text += ", " + cell_name(self.ring, self.index)
        return text

    def announce_focus(self, with_ring=False):
        self._play_cell(self.ring, self.index)
        text = self.focus_label()
        if with_ring:
            text = "%s. %s" % (ring_name(self.ring), text)
        self.ui.say(text)

    def ring_out(self):
        if self.ring >= self.rings:
            self.ui.play("borda")
            self.ui.say("Anel de fora. " + self.focus_label())
            return
        self.ring += 1
        self.announce_focus(with_ring=True)

    def ring_in(self):
        if self.ring == 0:
            self.ui.play("borda")
            self.ui.say("Núcleo. " + self.focus_label())
            return
        self.ring -= 1
        self.announce_focus(with_ring=True)

    def step(self, delta):
        """Esquerda (-1) e direita (+1): anda pelo anel."""
        if self.ring == 0:
            self.ui.play("borda")
            self.ui.say("Núcleo. " + self.focus_label())
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
            if len(fusions) <= 3:   # poucas: diz onde cada uma aconteceu
                made = ["%s %s" % (E.name(p).lower(), at((r, i))) for r, i, p in fusions]
            else:
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
        side = "direita" if step > 0 else "esquerda"
        if self.board.slide(self.ring, step, self.index):
            text = "%s deslizou para a %s: os elementos se juntaram %s %s." % (
                ring_name(self.ring), side, "até" if step > 0 else "a partir de",
                cell_name(self.ring, self.index))
        else:   # já estavam juntos (ou o anel está cheio): gira uma casa
            self.board.rotate(self.ring, step)
            text = "%s girou para a %s." % (ring_name(self.ring), side)
        self.ui.play("rotacao")
        self._end_turn([text])
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
        parts.append("No foco, %s." % self.focus_label().lower())
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
        return "%s, de %s para a direita: %s." % (
            ring_name(self.ring), cell_name(self.ring, self.index), ", ".join(items))

    def collapse_preview(self):
        """O que um colapso agora faria com a casa em foco: para onde o elemento cai,
        com quem funde, e o que cai em cima dela.

        Simula o colapso numa cópia da grade, com a mesma ordem do colapso de verdade.
        """
        cell = (self.ring, self.index)
        sym = self.focused()
        sim = Board(self.rings, random.Random(0))
        sim.cells = [list(row) for row in self.board.cells]
        events = sim.collapse(self.angle)["events"]
        parts = []
        if sym == E.FE:
            parts.append("Ferro não se move.")
        elif sym is not None and self.ring == 0:
            parts.append("%s fica no núcleo." % E.name(sym))
        for ev in events:
            kind, src, dst = ev[0], ev[1], ev[2]
            name = E.name(ev[3]).lower()
            if src == cell:
                if kind == "cai":
                    parts.append("%s cai %s, que está vazio." % (E.name(sym), at(dst)))
                elif kind == "funde":
                    parts.append("%s cai %s e funde com o %s de lá: vira %s." % (
                        E.name(sym), at(dst), E.name(ev[4]).lower(), E.name(ev[5]).lower()))
                elif kind == "ferro":
                    parts.append("%s cai no ferro %s e vira ferro." % (E.name(sym), of(dst)))
                elif ev[5]:
                    parts.append("%s fica: %s já fundiu neste colapso." % (E.name(sym), the(dst)))
                else:
                    parts.append("%s fica: %s tem %s, que não funde com %s." % (
                        E.name(sym), the(dst), E.name(ev[4]).lower(), name))
            elif dst == cell:
                if kind == "cai":
                    parts.append("Aqui cai o %s %s." % (name, of(src)))
                elif kind == "funde":
                    parts.append("O %s %s cai aqui e funde com o %s: vira %s." % (
                        name, of(src), E.name(ev[4]).lower(), E.name(ev[5]).lower()))
                elif kind == "ferro":
                    parts.append("O %s %s cai aqui e vira ferro." % (name, of(src)))
        if not parts:
            return "Colapso: nada acontece aqui."
        return "Colapso: " + " ".join(parts)
