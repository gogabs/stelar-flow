# Stelar Flow

Jogo de áudio de nucleossíntese estelar para o R36S acessível. Você é uma
estrela: hidrogênio entra pelo anel de fora de uma grade hexagonal e você
funde os elementos, do hidrogênio até o ferro, com colapso gravitacional,
pressão de radiação e rotação orbital. O ferro não funde e contamina quem
cai nele; quando o interior vira ferro, a estrela colapsa, e o final
(anã branca, estrela de nêutrons, pulsar, buraco negro) depende de até onde
a fusão chegou. Por turnos: nada acontece enquanto você pensa.

Regras, fusões, finais e equilíbrio: [docs/design.md](docs/design.md).

Feito em Python com a biblioteca do
[r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk).

## Controles

| Botão | O quê |
|---|---|
| Cima / baixo | Anel de fora / de dentro |
| Esquerda / direita | Anda pelo anel |
| B | Colapso gravitacional |
| X | Pressão de radiação (3 de energia) |
| L1 / R1 | Gira o anel em foco |
| Select | Elemento em foco e com o que funde |
| A | Lê o anel inteiro |
| Y | Pontos, energia, ferro, turno |
| Start | Pausa |

## Rodar

No PC (Windows, com o SDK clonado ao lado ou a cópia em `r36s_a11y/`):

```bat
python main.py
```

No console, com o SDK clonado ao lado deste repositório:

```bash
./instalar.sh
```

## Desenvolvimento

```bash
python3 -m unittest discover -s tests   # testes
python3 tools/simular.py 20 2           # equilíbrio com jogadores automáticos
python3 tools/gerar_sons.py             # sons provisórios
```

Os números do equilíbrio ficam em `stelar/config.py`. A lógica em `stelar/`
não toca som nem fala; `main.py` liga a partida ao SDK.
