"""Textos falados mais longos: ajuda e fim de partida."""
from . import config as C
from . import elements as E

HELP = (
    ("Objetivo",
     "Você é uma estrela. Hidrogênio entra pelo anel de fora a cada turno. Funda os elementos "
     "para ganhar pontos e energia, do hidrogênio até o ferro. O ferro não funde com nada e "
     "contamina quem cai nele. Quando o núcleo e os anéis de dentro viram ferro, a estrela "
     "colapsa e a partida acaba. O final depende do elemento mais pesado que você criou."),
    ("Navegar",
     "A grade é um hexágono: o núcleo no centro e anéis em volta. Cima vai para o anel de fora, "
     "baixo para o de dentro. Esquerda e direita andam pelo anel. O analógico esquerdo faz o "
     "mesmo. Ao andar, você ouve o elemento e o nome da casa. As casas do anel 1 são "
     "constelações, no sentido horário a partir da frente: Órion, Escorpião, Lira, Touro, "
     "Cisne e Gêmeos. No anel 2, cada casa tem o nome da constelação onde ela cai mais uma "
     "estrela, como Órion Betelgeuse e Órion Rigel. No anel 3, o nome da estrela onde ela cai "
     "mais uma letra grega, como Órion Rigel alfa. O nome diz para onde a casa cai no colapso: "
     "Órion Rigel alfa cai em Órion Rigel, que cai em Órion, que cai no núcleo. Navegar não gasta turno. O som de cada elemento vem da direção da casa: frente, "
     "direita, trás ou esquerda, e fica mais longe nos anéis de fora."),
    ("Ações",
     "B: colapso gravitacional. Tudo cai uma casa para dentro, e quem cai num parceiro funde. "
     "O núcleo vai primeiro, depois o anel 1, depois o 2; no mesmo anel, quem está mais perto "
     "do foco cai primeiro. "
     "X: pressão de radiação. Gasta %d de energia; o anel de fora é soprado para fora da estrela "
     "e o resto sobe uma casa, abrindo espaço. L1 e R1: rotação orbital. Como no 2048, "
     "os elementos do anel em foco deslizam e se juntam, sem vazios entre eles. R1 desliza para "
     "a direita e eles param na casa em foco, um atrás do outro; L1 desliza para a esquerda e "
     "eles começam na casa em foco. Se já estão juntos, o anel só gira uma casa. A ordem dos "
     "elementos não muda e nada funde. Cada ação é um turno e traz matéria nova."
     % C.PRESSURE_COST),
    ("Informações",
     "A diz o que o próximo colapso faria com a casa em foco: para onde o elemento cai, com "
     "quem funde e o que cai em cima dela. Select lê o anel em foco inteiro, do foco para a "
     "direita. Y fala pontos, energia, quanto ferro há e o turno. Start pausa."),
    ("Fusões",
     "Iguais fundem: hidrogênio com hidrogênio dá hélio; hélio com hélio, carbono; carbono com "
     "carbono, neônio; oxigênio com oxigênio, silício; silício com silício ou enxofre com "
     "enxofre, ferro. A partir do carbono, um hélio também se gruda e sobe um degrau: carbono, "
     "oxigênio, neônio, magnésio, silício, enxofre. Várias fusões no mesmo colapso dão bônus."),
    ("Ferro",
     "Ferro não se move nem funde. Um elemento que cai numa casa de ferro vira ferro. Se não "
     "houver casa livre para a matéria nova, a estrela engasga e uma casa vira ferro. Fazer "
     "ferro dá muitos pontos, mas ele fica na estrela para sempre: crie longe do núcleo."),
    ("Finais",
     "A estrela termina conforme o elemento mais pesado que você criou: anã branca de hélio; "
     "anã branca de carbono e oxigênio; anã branca de oxigênio e neônio; supernova com estrela "
     "de nêutrons; supernova com pulsar, se você fez ferro; e buraco negro, se fez ferro e "
     "passou de %d pontos." % C.BLACK_HOLE_SCORE),
)


def game_over(summary, fate, best, new_fate):
    heaviest = E.name(summary["heaviest"]).lower() if summary["heaviest"] else "nenhum"
    text = "A estrela colapsou. %s. %s %d pontos em %d turnos. Elemento mais pesado: %s." % (
        fate[1], fate[2], summary["score"], summary["turns"], heaviest)
    if new_fate:
        text += " Final novo descoberto!"
    if summary["score"] > best:
        text += " Novo recorde!"
    elif best:
        text += " Recorde: %d." % best
    return text
