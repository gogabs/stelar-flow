# Stelar Flow: documento de design

Versão 0 (14/10/2026). O que está marcado **[decidir]** é sugestão minha e
depende do Gabs; o resto já está no protótipo e pode mudar.

## 1. Ideia

Você é uma estrela. A grade é hexagonal: o núcleo (anel 0) no centro e
anéis em volta. Hidrogênio entra pelo anel de fora a cada turno; o jogador
funde os elementos para ganhar pontos, do hidrogênio até o ferro. O ferro
não funde e contamina a estrela. Quando o interior todo vira ferro, a
estrela colapsa, e o **final** depende de até onde a fusão chegou.

O jogo é **por turnos**: nada acontece enquanto o jogador pensa, então não
há pressa nem fala atropelada. Isso combina com um jogo para quem joga
ouvindo.

## 2. Grade

| Anel | Casas |
|---|---|
| 0 (núcleo) | 1 |
| 1 | 6 |
| 2 | 12 |
| 3 (o de fora) | 18 |
| **Total** | **37** |

As casas de cada anel são numeradas no sentido horário a partir da frente.
Cada casa tem um nome, falado ao navegar ("Hélio, Órion Rigel"), e **o
nome diz para onde ela cai no colapso** (ideia do Gabs, 14/10):

- **Anel 1:** constelações, no sentido horário a partir da frente: Órion,
  Escorpião, Lira, Touro, Cisne, Gêmeos.
- **Anel 2:** a constelação onde a casa cai mais uma estrela dela: Órion
  Betelgeuse, Órion Rigel, Escorpião Antares, Escorpião Sargas, Lira Vega,
  Lira Sulafat, Touro Aldebarã, Touro Alcione, Cisne Deneb, Cisne Albireo,
  Gêmeos Castor, Gêmeos Pólux.
- **Anel 3:** a estrela onde a casa cai mais uma letra grega: Órion
  Betelgeuse alfa, Órion Betelgeuse beta, Órion Rigel alfa, Escorpião
  Antares alfa... Como 18 casas caem em 12, metade das estrelas recebe duas
  casas (alfa e beta) e a outra metade, uma (só alfa).

Órion Rigel alfa cai em Órion Rigel, que cai em Órion, que cai no núcleo.
Os nomes ficam nas casas; quando o anel desliza, os elementos mudam de casa.

Cada casa tem uma direção (frente, direita, trás, esquerda e as do meio),
igual em todos os anéis. No colapso, cada casa cai na casa do anel de
dentro na mesma direção.

**Tamanho:** a estrela tem sempre 3 anéis (decidido em 14/10). A de 2 anéis
(19 casas) era pequena demais e permitia partidas infinitas: dava para
juntar energia e soprar até o núcleo para fora de uma vez.

## 3. Controles

| Botão | O quê | Gasta turno |
|---|---|---|
| Cima / baixo (ou analógico) | Anel de fora / anel de dentro | não |
| Esquerda / direita (ou analógico) | Anda pelo anel; segurar repete | não |
| B | Colapso gravitacional | sim |
| X | Pressão de radiação | sim |
| L1 / R1 | Rotação orbital: desliza o anel em foco para a esquerda / direita, juntando os elementos | sim |
| A | Prévia do colapso: para onde o elemento em foco cai, com quem funde e o que cai em cima da casa | não |
| Select | Lê o anel em foco inteiro, da casa em foco para a direita | não |
| Y | Pontos, energia, quanto ferro há, turno | não |
| Start | Pausa (continuar, salvar e sair, sair sem salvar) | — |

B e X ficam em cima e embaixo de propósito: o botão de baixo puxa para
dentro, o de cima empurra para fora.

**Partida salva.** Um espaço só, em `partida.json` na pasta de saves (ao
lado de `progresso.json`). A pausa tem "Salvar e sair para o menu"; fechar
o jogo no meio de uma partida também salva. Com save, o menu principal
abre em "Continuar partida salva", seguido de "Novo jogo". O save guarda a
grade, o foco, os pontos, a energia, o turno e o estado do sorteio, então
a matéria nova é a mesma que viria sem sair. Ele é consumido ao continuar,
para não dar para voltar atrás numa jogada ruim.

## 4. Ações

**Colapso gravitacional (B).** Do núcleo para fora, cada elemento cai uma
casa para dentro:

- casa de dentro vazia: o elemento cai;
- casa de dentro com um parceiro de fusão: fundem lá dentro. Cada casa
  funde no máximo uma vez por colapso;
- casa de dentro com ferro: o elemento vira ferro ("engolido pelo ferro");
- qualquer outra coisa: fica onde está.

Ferro não se move. No mesmo anel, quem está **mais perto do foco cai
primeiro**: isso decide, por exemplo, qual dos seis vizinhos chega ao
núcleo vazio. Um colapso que não muda nada não gasta turno.

**Pressão de radiação (X).** Custa 3 de energia. O anel de fora é soprado
para fora da estrela (vento estelar) e todo o resto sobe uma casa, se
houver espaço. O núcleo sai na direção do foco. Não funde nada; ferro não
se move nem é soprado. É a válvula de escape: sem ela, o núcleo entope com
um elemento sem parceiro e a estrela morre cedo (testei isso nas
simulações, seção 8).

**Rotação orbital (L1/R1).** Como no 2048: os elementos do anel em foco
deslizam e se juntam, sem vazios entre eles, usando a casa em foco como
parede. Com R1 tudo desliza no sentido horário e para na casa em foco,
um atrás do outro; com L1 desliza no sentido anti-horário e começa na
casa em foco. A ordem dos elementos no anel não muda, nada funde e o
ferro desliza junto. Se os elementos já estão juntos (ou o anel está
cheio), o anel só gira uma casa. Serve para juntar elementos em cima de um
alvo antes do colapso e para tirar elementos de cima do ferro. O núcleo não
gira.

**Depois de cada ação** entra matéria nova numa casa vazia do anel de fora:
hidrogênio (80%), hélio (15%) ou carbono (5%), os três elementos básicos.
Se não há casa vazia, **a estrela engasga**: uma casa do anel de fora vira
ferro.

## 5. Fusões

Duas famílias, como numa estrela de verdade:

**Queima (iguais fundem)**

| Par | Produto | Pontos | Energia |
|---|---|---|---|
| H + H | He | 4 | +1 |
| He + He | C | 12 | +1 |
| C + C | Ne | 20 | +2 |
| O + O | Si | 28 | +2 |
| Si + Si | **Fe** | 56 | 0 |
| S + S | **Fe** | 56 | 0 |

**Captura de hélio (a partir do carbono, um hélio sobe um degrau)**

| Par | Produto | Pontos | Energia |
|---|---|---|---|
| C + He | O | 16 | +2 |
| O + He | Ne | 20 | +2 |
| Ne + He | Mg | 24 | +2 |
| Mg + He | Si | 28 | +2 |
| Si + He | S | 32 | +2 |

Pontos são o número de massa do produto. Várias fusões no mesmo colapso
dão +25% por fusão além da primeira. Energia começa em 3, máximo 9.
Fazer ferro não dá energia (na física, fundir até o ferro já não libera
energia).

### A cadeia do carbono

Do carbono saem dois caminhos, e é aí que o jogador escolhe:

```
            + He        + He        + He        + He
  C ─────────► O ─────────► Ne ────────► Mg ────────► Si ──+He──► S
  │            │                                     │           │
  │ C + C      │ O + O                               │ Si + Si   │ S + S
  ▼            ▼                                     ▼           ▼
  Ne           Si                                    Fe          Fe
```

- **Guardar hélio** e subir a escada degrau por degrau: mais seguro, pontos
  constantes, mas cada degrau gasta um hélio.
- **Queimar pares** (C+C, O+O): pula degraus e dá mais pontos de uma vez,
  mas exige dois iguais alinhados.
- **Fazer ferro** (Si+Si, S+S): 56 pontos, o maior prêmio, mas o ferro fica
  na estrela para sempre e contamina quem cai nele. Feito longe do núcleo,
  é um risco calculado; no núcleo, é o fim.

## 6. Ferro e fim da partida

- Ferro não se move, não funde e não é soprado pela pressão.
- Quem cai numa casa de ferro vira ferro.
- Sem espaço para matéria nova, uma casa vira ferro.
- **Fim:** quando o núcleo e todos os anéis menos o de fora são ferro (ou a
  estrela inteira). Isso é o "infectada pelo ferro" da ideia original: com
  o interior de ferro nada mais consegue fundir.

## 7. Finais

O final depende do **elemento mais pesado criado por fusão** na partida,
como o destino de uma estrela depende da massa dela:

| Mais pesado | Final |
|---|---|
| H ou He | Anã branca de hélio |
| C ou O | Anã branca de carbono e oxigênio (o destino do Sol) |
| Ne ou Mg | Anã branca de oxigênio e neônio |
| Si ou S | Supernova e estrela de nêutrons |
| Fe | Supernova e pulsar |
| Fe e 4000 pontos ou mais | Buraco negro |

Cada final tem um texto curto falado no fim. Os finais descobertos ficam
salvos e aparecem em "Recordes e finais", para dar vontade de buscar os
outros.

**[decidir]** Outras ideias de finais e caminhos, se quiser mais variedade:

1. **Ciclo CNO**: hidrogênio também gruda em carbono, nitrogênio e oxigênio
   (C → N → O → C, devolvendo hélio). Um caminho alternativo de queimar
   hidrogênio, útil quando o anel de fora entope de H.
2. **Processo s (elementos pesados)**: em vez de morrer no ferro, uma
   "captura de nêutrons" lenta transforma ferro em elementos raros
   (estrôncio, bário, chumbo) que valem pontos e limpam casas. Seria uma
   quarta ação, cara em energia.
3. **Kilonova (ouro)**: final secreto se a partida fizer dois núcleos de
   ferro seguidos; "seu ouro vai parar num planeta daqui a bilhões de anos".
4. **Final escolhido**: em vez de só morrer, uma ação "Supernova" que o
   jogador aciona quando quiser, encerrando a partida com bônus pelos
   elementos pesados na grade. Dá um final de vitória, não só de derrota.

## 8. Equilíbrio

`tools/simular.py` joga partidas com dois robôs: um que aperta qualquer
coisa e um guloso, que testa cada ação e escolhe a que deixa a grade
melhor. Resultado com os números atuais (20 partidas, 3 anéis, rotação
que desliza):

| Robô | Turnos (mediana) | Pontos (mediana) | Finais |
|---|---|---|---|
| Aleatório | 58 | 0 | anã branca de hélio 18, de carbono 2 |
| Guloso | 265 (146 a 509) | 1636 (760 a 3109) | pulsar 20 |

Antes de existir o vento estelar o guloso morria com uns 50 turnos: o
núcleo entupia com um elemento sem parceiro (enxofre, por exemplo) e o anel
de fora enchia de hidrogênio sem par. O guloso só olha uma jogada à frente
e não chega aos 4000 pontos do buraco negro; se no console também ficar
inalcançável, baixamos esse limite.

Uma pessoa deve ficar entre os dois robôs no começo. Números para ajustar
depois de jogar no console, todos em `stelar/config.py`: custo da pressão,
energia máxima, sorteio da matéria nova, bônus de combo e o limite do
buraco negro.

## 9. Áudio e falas

- **Cada elemento tem um tom**: quanto mais pesado, mais grave e mais rico
  em harmônicos; o ferro é um zumbido dissonante; casa vazia é um sopro
  curto. Com o tempo dá para navegar quase sem fala.
- **Som 3D**: o tom vem da direção da casa (frente, direita, trás,
  esquerda), mais longe nos anéis de fora. A matéria nova toca um blip de
  onde entrou; cada fusão toca um arpejo de onde aconteceu.
- **Falas curtas**:
  - navegar: "Anel 2. Hélio, Órion Rigel" ao trocar de anel; "Hélio,
    Órion Rigel" ao andar;
  - prévia (A): "Colapso: Hélio cai em Escorpião e funde com o carbono de
    lá: vira oxigênio.";
  - colapso, até 3 fusões: "Fusão: hélio no núcleo e carbono em Touro.
    Mais 20 pontos."; com mais, conta: "Fusão: 4 hélios e 1 carbono. Mais
    44 pontos. No foco, carbono, Lira.";
  - ferro: "1 elemento engolido pelo ferro."; "Cuidado, isso é ferro.";
  - pressão: "Pressão de radiação. Vento estelar levou 3 hidrogênios.
    Energia 2.";
  - matéria nova só é falada se não for hidrogênio ("Entrou hélio.");
  - engasgo: "A estrela engasgou: sem espaço para matéria nova, uma casa
    virou ferro.";
  - fim: "A estrela colapsou. Supernova e pulsar. (texto do final) 1240
    pontos em 210 turnos. Elemento mais pesado: ferro. Novo recorde!"
- Os sons atuais são **provisórios**, sintetizados por
  `tools/gerar_sons.py`. Trocar um som é pôr um arquivo com o mesmo nome em
  `sounds/`. **[decidir]** se quer sons de verdade (CC0) ou da sua coleção.

## 10. Em aberto

- **[decidir]** rotação gastar turno (hoje gasta). Sem gastar, o jogo vira
  um quebra-cabeça mais calmo e as partidas ficam bem mais longas.
- **[decidir]** quais ideias da seção 7 entram.
- Tutorial guiado (como o do Dead vs. Alive), depois que as regras
  firmarem.
- Gráficos opcionais (a grade hexagonal desenhada, com cores por elemento).
