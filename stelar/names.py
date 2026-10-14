"""Nomes das casas: o nome diz para onde ela cai no colapso.

Anel 1: uma constelação por casa. Anel 2: a constelação de baixo mais uma
estrela dela. Anel 3: a estrela de baixo mais uma letra grega. Assim
"Órion Rigel beta" cai em "Órion Rigel", que cai em "Órion", que cai no
núcleo.
"""
from .board import parent, ring_size

# No sentido horário a partir da frente. Cada constelação com duas estrelas,
# na ordem em que aparecem no anel 2.
CONSTELLATIONS = (
    ("Órion", ("Betelgeuse", "Rigel")),
    ("Escorpião", ("Antares", "Sargas")),
    ("Lira", ("Vega", "Sulafat")),
    ("Touro", ("Aldebarã", "Alcione")),
    ("Cisne", ("Deneb", "Albireo")),
    ("Gêmeos", ("Castor", "Pólux")),
)
GREEK = ("alfa", "beta", "gama")


def _children(r, j):
    return [i for i in range(ring_size(r + 1)) if parent(r + 1, i) == (r, j)]


def cell_name(r, i):
    """O nome da casa (r, i); o núcleo é "núcleo"."""
    if r == 0:
        return "núcleo"
    if r == 1:
        return CONSTELLATIONS[i][0]
    pr, pj = parent(r, i)
    rank = _children(pr, pj).index(i)
    if r == 2:
        return "%s %s" % (cell_name(pr, pj), CONSTELLATIONS[pj][1][rank])
    return "%s %s" % (cell_name(pr, pj), GREEK[rank])


def the(cell):
    """ "o núcleo" ou "Órion Rigel"."""
    return "o núcleo" if cell[0] == 0 else cell_name(*cell)


def at(cell):
    """ "no núcleo" ou "em Órion Rigel"."""
    return "no núcleo" if cell[0] == 0 else "em " + cell_name(*cell)


def of(cell):
    """ "do núcleo" ou "de Órion Rigel"."""
    return "do núcleo" if cell[0] == 0 else "de " + cell_name(*cell)
