"""A grade hexagonal da estrela, sem som nem fala (testável no PC).

O anel 0 é o núcleo, com uma casa. O anel r tem 6*r casas, numeradas no
sentido horário a partir da frente. A posição de uma casa é um ângulo de 0
a 1 (0 = frente, 0,25 = direita), igual em todos os anéis, o que permite
casar cada casa com a de dentro e a de fora.
"""
import random

from . import elements as E


def ring_size(r):
    return 1 if r == 0 else 6 * r


def angle_of(r, i):
    return 0.0 if r == 0 else i / float(ring_size(r))


def index_at(r, angle):
    """A casa do anel r mais perto do ângulo."""
    n = ring_size(r)
    return int(angle * n + 0.5) % n


def parent(r, i):
    """A casa do anel de dentro para onde (r, i) cai no colapso."""
    if r == 1:
        return 0, 0
    return r - 1, (i * (r - 1)) // r


def children(r, j, rings):
    """As casas do anel de fora que caem em (r, j)."""
    if r >= rings:
        return []
    return [(r + 1, i) for i in range(ring_size(r + 1)) if parent(r + 1, i) == (r, j)]


def angular_gap(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1.0 - d)


def order_from(r, angle):
    """Índices do anel r começando pelo mais perto do ângulo, seguindo no sentido horário."""
    n = ring_size(r)
    start = index_at(r, angle)
    return [(start + k) % n for k in range(n)]


class Board:
    def __init__(self, rings=2, rng=None):
        self.rings = rings
        self.rng = rng or random.Random()
        self.cells = [[None] * ring_size(r) for r in range(rings + 1)]

    # --- consulta ------------------------------------------------------
    def get(self, r, i):
        return self.cells[r][i]

    def set(self, r, i, sym):
        self.cells[r][i] = sym

    def all_cells(self):
        return [(r, i) for r in range(self.rings + 1) for i in range(ring_size(r))]

    def empty_cells(self, r=None):
        rings = [r] if r is not None else range(self.rings + 1)
        return [(q, i) for q in rings for i in range(ring_size(q)) if self.cells[q][i] is None]

    def count(self, sym):
        return sum(row.count(sym) for row in self.cells)

    def inner_all_iron(self):
        """Núcleo e anéis internos (todos menos o de fora) inteiros de ferro."""
        return all(c == E.FE for r in range(self.rings) for c in self.cells[r])

    def all_iron(self):
        return all(c == E.FE for row in self.cells for c in row)

    def is_dead(self):
        return self.inner_all_iron() or self.all_iron()

    # --- ações ---------------------------------------------------------
    def collapse(self, angle=0.0):
        """Puxa cada elemento uma casa para dentro, do núcleo para fora.

        Cai na casa vazia; funde se a casa de dentro tem um parceiro (cada
        casa funde no máximo uma vez por colapso); vira ferro se a casa de
        dentro é ferro. Ferro não se move. No mesmo anel, quem está mais
        perto do foco cai primeiro.

        Devolve {"moves": [...], "fusions": [(r, i, produto)], "infected": [(r, i)],
        "events": [...]}. "events" tem tudo na ordem em que aconteceu:
        ("cai", origem, destino, elemento), ("funde", origem, destino, elemento,
        quem estava lá, produto), ("ferro", origem, destino, elemento) e
        ("fica", origem, destino, elemento, quem estava lá, já tinha fundido).
        """
        moves, fusions, infected, events = [], [], [], []
        fused = set()
        for r in range(1, self.rings + 1):
            for i in order_from(r, angle):
                sym = self.cells[r][i]
                if sym is None or sym == E.FE:
                    continue
                pr, pj = parent(r, i)
                target = self.cells[pr][pj]
                if target is None:
                    self.cells[pr][pj], self.cells[r][i] = sym, None
                    moves.append(((r, i), (pr, pj)))
                    events.append(("cai", (r, i), (pr, pj), sym))
                elif target == E.FE:
                    self.cells[r][i] = E.FE
                    infected.append((r, i))
                    events.append(("ferro", (r, i), (pr, pj), sym))
                elif (pr, pj) not in fused and E.fuse(target, sym):
                    product = E.fuse(target, sym)
                    self.cells[pr][pj], self.cells[r][i] = product, None
                    fused.add((pr, pj))
                    fusions.append((pr, pj, product))
                    events.append(("funde", (r, i), (pr, pj), sym, target, product))
                else:
                    events.append(("fica", (r, i), (pr, pj), sym, target, (pr, pj) in fused))
        return {"moves": moves, "fusions": fusions, "infected": infected, "events": events}

    def pressure(self, angle=0.0):
        """Empurra cada elemento uma casa para fora, se houver casa vazia.

        O anel de fora é soprado para fora da estrela (vento estelar). Depois,
        de fora para dentro, cada elemento sobe para uma casa vazia, e quem
        está dentro ocupa as casas que acabaram de vagar. O núcleo sai para a
        casa vazia do anel 1 mais perto do foco. Não funde nada; ferro não se
        move nem é soprado.

        Devolve {"moves": [...], "ejected": [(r, i, elemento)]}.
        """
        moves, ejected = [], []
        outer = self.rings
        for i, sym in enumerate(self.cells[outer]):
            if sym is not None and sym != E.FE:
                ejected.append((outer, i, sym))
                self.cells[outer][i] = None
        for r in range(self.rings - 1, -1, -1):
            for i in order_from(r, angle):
                sym = self.cells[r][i]
                if sym is None or sym == E.FE:
                    continue
                if r == 0:
                    targets = [(1, j) for j in order_from(1, angle)]
                else:
                    targets = sorted(children(r, i, self.rings),
                                     key=lambda c: angular_gap(angle_of(*c), angle))
                for tr, tj in targets:
                    if self.cells[tr][tj] is None:
                        self.cells[tr][tj], self.cells[r][i] = sym, None
                        moves.append(((r, i), (tr, tj)))
                        break
        return {"moves": moves, "ejected": ejected}

    def rotate(self, r, step):
        """Gira o anel r uma casa; step=1 no sentido horário, -1 no anti-horário."""
        if r == 0:
            return False
        row = self.cells[r]
        step %= len(row)
        self.cells[r] = row[-step:] + row[:-step]
        return True

    def slide(self, r, step, anchor):
        """Desliza os elementos do anel r no sentido de step até a casa anchor, como no 2048.

        Com step=1 (horário) tudo anda no sentido horário e para ao bater na
        casa anchor ou num elemento já parado: os elementos ficam juntos,
        terminando em anchor. Com step=-1 é o espelho: começam em anchor e
        seguem no sentido horário. A ordem dos elementos não muda e ninguém
        funde. Devolve True se algo se moveu.
        """
        if r == 0:
            return False
        row = self.cells[r]
        n = len(row)
        if step > 0:   # sequência no sentido anti-horário a partir de anchor
            order = [(anchor - k) % n for k in range(n)]
        else:          # sequência no sentido horário a partir de anchor
            order = [(anchor + k) % n for k in range(n)]
        items = [row[i] for i in order if row[i] is not None]
        new = list(row)
        for k, i in enumerate(order):
            new[i] = items[k] if k < len(items) else None
        if new == row:
            return False
        self.cells[r] = new
        return True

    def spawn(self, sym):
        """Põe sym numa casa vazia do anel de fora. Devolve a casa ou None se não couber."""
        free = self.empty_cells(self.rings)
        if not free:
            return None
        r, i = self.rng.choice(free)
        self.cells[r][i] = sym
        return r, i

    def choke(self):
        """Sem espaço para matéria nova: uma casa vira ferro, de fora para dentro."""
        for r in range(self.rings, -1, -1):
            options = [(r, i) for i, c in enumerate(self.cells[r]) if c != E.FE]
            if options:
                r, i = self.rng.choice(options)
                self.cells[r][i] = E.FE
                return r, i
        return None
