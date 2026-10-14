"""Os finais: o destino da estrela depende de até onde a fusão chegou."""
from . import config as C
from . import elements as E

# (id, título, texto). A ordem é a da massa da estrela.
FATES = (
    ("ana-helio", "Anã branca de hélio",
     "Sua estrela nunca acendeu o hélio. Ela esfria devagar, uma brasa de hélio que vai durar bilhões de anos."),
    ("ana-carbono", "Anã branca de carbono e oxigênio",
     "Sua estrela soltou as camadas de fora numa nebulosa planetária. Sobrou um núcleo de carbono e oxigênio, o destino do Sol."),
    ("ana-neonio", "Anã branca de oxigênio e neônio",
     "Sua estrela queimou o carbono, mas não teve massa para ir além. Sobrou uma anã branca rara, de oxigênio, neônio e magnésio."),
    ("estrela-neutrons", "Supernova e estrela de nêutrons",
     "O núcleo desabou e a estrela explodiu numa supernova. Sobrou uma estrela de nêutrons, do tamanho de uma cidade."),
    ("pulsar", "Supernova e pulsar",
     "O núcleo de ferro desabou e a estrela explodiu. Sobrou um pulsar, girando centenas de vezes por segundo."),
    ("buraco-negro", "Buraco negro",
     "Sua estrela era tão massiva que nem a explosão conseguiu pará-la. O núcleo desabou num buraco negro."),
)
BY_ID = {f[0]: f for f in FATES}


def fate_for(heaviest, score):
    """O final para o elemento mais pesado criado por fusão (ou None) e os pontos."""
    if heaviest is None or E.mass_rank(heaviest) <= E.mass_rank(E.HE):
        return BY_ID["ana-helio"]
    if heaviest in (E.C, E.O):
        return BY_ID["ana-carbono"]
    if heaviest in (E.NE, E.MG):
        return BY_ID["ana-neonio"]
    if heaviest in (E.SI, E.S):
        return BY_ID["estrela-neutrons"]
    if score >= C.BLACK_HOLE_SCORE:
        return BY_ID["buraco-negro"]
    return BY_ID["pulsar"]
