"""Números do equilíbrio do jogo, num lugar só."""
from . import elements as E

RINGS = 2                 # anéis em volta do núcleo (2 ou 3)
RING_CHOICES = (2, 3)

START_ENERGY = 3
MAX_ENERGY = 9
PRESSURE_COST = 3

START_MATTER = 4          # hidrogênios no anel de fora ao começar

# Matéria nova que entra a cada turno: (elemento, peso do sorteio).
SPAWN_TABLE = ((E.H, 80), (E.HE, 15), (E.C, 5))

# Bônus por várias fusões no mesmo colapso: +25% por fusão além da primeira.
COMBO_STEP = 0.25

# Finais: o elemento mais pesado criado por fusão decide; com ferro, os pontos.
BLACK_HOLE_SCORE = 4000

# Distância (metros) dos sons de cada anel, para o áudio 3D.
RING_DISTANCE = (0.6, 1.6, 2.6, 3.6)

AXIS_THRESHOLD = 0.6      # analógico conta como direcional a partir daqui
