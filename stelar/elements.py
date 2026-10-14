"""Elementos, fusões, pontos e energia.

Duas famílias de fusão, como numa estrela de verdade:
  - queima: dois elementos iguais se fundem (H+H, He+He, C+C, O+O, Si+Si, S+S);
  - captura de hélio: a partir do carbono, um hélio se gruda no elemento e
    sobe um degrau (C, O, Ne, Mg, Si).
Ferro não funde com nada: é o fim da linha.
"""

H, HE, C, O, NE, MG, SI, S, FE = "H", "He", "C", "O", "Ne", "Mg", "Si", "S", "Fe"

ORDER = (H, HE, C, O, NE, MG, SI, S, FE)

NAMES = {
    H: "Hidrogênio", HE: "Hélio", C: "Carbono", O: "Oxigênio", NE: "Neônio",
    MG: "Magnésio", SI: "Silício", S: "Enxofre", FE: "Ferro",
}

# Pontos ao criar o elemento por fusão: o número de massa (aproximado).
POINTS = {HE: 4, C: 12, O: 16, NE: 20, MG: 24, SI: 28, S: 32, FE: 56}

# Energia ganha ao criar o elemento. Fazer ferro consome energia em vez de dar.
ENERGY_GAIN = {HE: 1, C: 1, O: 2, NE: 2, MG: 2, SI: 2, S: 2, FE: 0}

_PAIRS = {
    (H, H): HE,
    (HE, HE): C,
    (C, C): NE,     # queima do carbono
    (O, O): SI,     # queima do oxigênio
    (SI, SI): FE,   # queima do silício: dá muitos pontos, mas é ferro
    (S, S): FE,
    (C, HE): O,     # capturas de hélio
    (O, HE): NE,
    (NE, HE): MG,
    (MG, HE): SI,
    (SI, HE): S,
}
FUSIONS = {}
for (a, b), product in _PAIRS.items():
    FUSIONS[(a, b)] = product
    FUSIONS[(b, a)] = product


def fuse(a, b):
    """O produto da fusão de a com b, ou None se não fundem."""
    return FUSIONS.get((a, b))


def name(sym):
    return NAMES[sym] if sym else "Vazio"


def mass_rank(sym):
    return ORDER.index(sym)


def partners(sym):
    """[(parceiro, produto)] em ordem de massa do parceiro."""
    out = [(b, p) for (a, b), p in FUSIONS.items() if a == sym]
    return sorted(out, key=lambda t: mass_rank(t[0]))
