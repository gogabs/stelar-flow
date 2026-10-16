# Tela do Stelar Flow

A tela é um extra: tudo o que ela mostra também é falado, e o jogo inteiro
funciona com ela desligada. Ela segue as opções do sistema: `SCREEN=0`
desliga, e a economia de energia baixa os quadros por segundo (15, 10 ou 5).
Se o vídeo falhar, só os gráficos desligam.

## O que aparece

- **Barra de cima**: o anel e o nome da casa em foco, e o elemento dela,
  como a navegação fala.
- **Estrela**: a grade hexagonal, com o núcleo no meio. A casa 0 de cada
  anel fica em cima (a frente) e a numeração segue no sentido horário, então
  a direita da tela é a direita do som 3D. Cada casa encosta na casa onde
  cai no colapso. O núcleo vazio tem um sol apagado desenhado, para achar o
  centro.
- **Foco**: moldura amarela grossa com contorno preto. Some quando a
  partida acaba.
- **Painel da direita**: o mesmo que o Y fala: pontos, energia (com uma
  marca no custo da pressão de radiação), ferro, turno e o elemento mais
  pesado.
- **Legenda**: a última fala, em duas linhas, embaixo.
- **Menus**: os do jogo, com uma fileira de elementos de enfeite; a pausa
  aparece por cima da estrela.

## Cores e contraste

Cada elemento tem uma cor, mas a cor só ajuda: o símbolo químico está
sempre escrito em negrito. O ferro, além da cor, é riscado na diagonal, com
o símbolo numa plaquinha preta. Contrastes pela fórmula da WCAG (texto pede
4,5 para 1; formas, 3 para 1):

| Elemento | Cor | Símbolo preto | Contra a casa vazia |
|---|---|---|---|
| H | `#8ec9ff` | 11,9 | 9,7 |
| He | `#f2f2f2` | 18,8 | 15,2 |
| C | `#ffa94d` | 11,0 | 8,9 |
| O | `#6fdc8c` | 12,3 | 10,0 |
| Ne | `#ff85c0` | 9,4 | 7,6 |
| Mg | `#b79cff` | 9,2 | 7,5 |
| Si | `#4fd1d9` | 11,5 | 9,3 |
| S | `#e9d758` | 14,3 | 11,6 |
| Fe | `#d0603f` | branco na plaquinha preta, 21 | 4,4 |

| Par | Cores | Contraste |
|---|---|---|
| Riscos do ferro sobre o ferro | `#5c2116` / `#d0603f` | 3,2 |
| Borda da casa vazia contra o fundo | `#5b6f94` / `#070b18` | 3,9 |
| Cursor sobre a casa vazia | `#ffd60a` / `#141c2e` | 12,0 |
| Texto na faixa amarela do menu | `#000000` / `#ffd60a` | 14,9 |

## Gerar de novo

As casas são um PNG pronto em `graficos/casas.png`; o console não precisa do
Pillow. No PC, com o Pillow:

```bash
python3 tools/gerar_graficos.py     # graficos/casas.png
python3 tools/previa.py prévias     # telas de exemplo em PNG
```
