"""Gráficos opcionais do Stelar Flow: a estrela em hexágonos, o foco e os menus.

Nada aqui é necessário para jogar: tudo o que aparece na tela também é falado
(regra do contrato). A barra de cima mostra a casa em foco, como a navegação
fala; o painel do lado mostra o mesmo que o Y; a legenda embaixo é a última
fala. A tela segue a opção do sistema (SCREEN=0 desliga) e a economia de
energia (menos quadros por segundo), como no Campo Minado e na Paciência.

`draw_frame(gfx, ...)` só usa a API de desenho do SDK, então roda com o SDK de
verdade, com o gráfico de mentira dos testes e com o do gerador de prévias.

A grade é a de um favo de mel com hexágonos de lado reto em cima: o anel r tem
6*r casas, a casa 0 fica bem em cima do núcleo (a frente) e a numeração segue
no sentido horário, igual à de stelar/board.py. Assim a casa da direita na tela
é a casa da direita no som 3D, e cada casa encosta na casa onde cai.

Cores pensadas para contraste (veja docs/graficos.md): cada elemento tem a
sua, sempre com o símbolo escrito em negrito por cima (a cor nunca é a única
pista); o ferro é escuro e riscado; o foco é uma moldura amarela grossa com
contorno preto.
"""
import math
import os
import time

from . import config as C
from . import elements as E
from .board import ring_size
from .names import cell_name

W, H = 640, 480
TOP_BAR = 34
CAPTION_Y = 430
SIDE = 31                        # raio do hexágono (centro ao canto), em pixels
SQ3 = math.sqrt(3)
CENTER = (236, (TOP_BAR + CAPTION_Y) // 2)
PANEL_X = 436                    # painel do lado direito, até W - 10

# Cada quadro da folha graficos/casas.png tem esta caixa; o hexágono fica no meio.
TILE_W = 2 * SIDE + 12
TILE_H = int(SQ3 * SIDE) + 12

BG = "#070b18"
STAR = "#3b4766"
EMPTY = "#141c2e"
EMPTY_LINE = "#5b6f94"
CORE_GLOW = "#ffd27a"
COLORS = {
    E.H: "#8ec9ff", E.HE: "#f2f2f2", E.C: "#ffa94d", E.O: "#6fdc8c", E.NE: "#ff85c0",
    E.MG: "#b79cff", E.SI: "#4fd1d9", E.S: "#e9d758", E.FE: "#d0603f",
}
INK = {sym: "#000000" for sym in COLORS}
INK[E.FE] = "#ffffff"
IRON_HATCH = "#5c2116"
FOCUS = "#ffd60a"
OUTLINE = "#000000"
BAR = "#000000"
TEXT = "#ffffff"
TEXT_DIM = "#c8d3de"
LINE = "#5b6f94"

# ordem dos quadros na folha
TILES = (None, "nucleo") + E.ORDER + ("foco",)


def tile_index(sym, core=False):
    if sym is None:
        return 1 if core else 0
    return TILES.index(sym)


T_FOCUS = TILES.index("foco")


def tile_src(k):
    return (k * TILE_W, 0, TILE_W, TILE_H)


# --- geometria ------------------------------------------------------------------
# Passos no favo (coordenadas axiais q, r) para andar por um anel no sentido
# horário, saindo da casa de cima: desce pela direita, desce, desce pela
# esquerda, sobe pela esquerda, sobe, sobe pela direita.
_STEPS = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))


def axial(ring, i):
    """Coordenadas axiais (q, r) da casa i do anel."""
    if ring == 0:
        return 0, 0
    side, k = divmod(i, ring)
    q, r = 0, -ring
    for s in range(side):
        q += _STEPS[s][0] * ring
        r += _STEPS[s][1] * ring
    return q + _STEPS[side][0] * k, r + _STEPS[side][1] * k


def cell_center(ring, i, center=CENTER, side=SIDE):
    q, r = axial(ring, i)
    return center[0] + side * 1.5 * q, center[1] + side * SQ3 * (r + q / 2.0)


def hex_points(cx, cy, radius):
    return [(cx + radius * math.cos(math.pi / 3 * k), cy + radius * math.sin(math.pi / 3 * k))
            for k in range(6)]


def stars(seed=7, count=70):
    """Estrelinhas fixas do fundo, longe da grade."""
    out, x = [], seed
    while len(out) < count:
        x = (x * 1103515245 + 12345) % (1 << 31)
        px = x % W
        x = (x * 1103515245 + 12345) % (1 << 31)
        py = TOP_BAR + 4 + x % (CAPTION_Y - TOP_BAR - 8)
        if math.hypot(px - CENTER[0], py - CENTER[1]) > SIDE * 6.6:
            out.append((px, py))
    return out


STARS = stars()


# --- peças comuns ---------------------------------------------------------------
class Fonts:
    def __init__(self, gfx):
        self.gfx = gfx
        self.cache = {}

    def __call__(self, size):
        if size not in self.cache:
            self.cache[size] = self.gfx.font(None, size)
        return self.cache[size]


def wrap(gfx, text, font, width, lines=2):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if gfx.measure(trial, font)[0] <= width or not line:
            line = trial
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    if len(out) > lines:   # a fala mais nova fica no fim: mostra o fim
        out = out[-lines:]
        out[0] = "… " + out[0]
    return out


def draw_caption(gfx, fonts, caption):
    gfx.rect(0, CAPTION_Y, W, H - CAPTION_Y, color=BAR)
    gfx.line(0, CAPTION_Y, W, CAPTION_Y, color=LINE, width=2)
    for k, line in enumerate(wrap(gfx, caption or "", fonts(18), W - 20)):
        gfx.text(line, 10, CAPTION_Y + 4 + k * 23, font=fonts(18), color=TEXT)


def top_bar(gfx, fonts, left, right):
    gfx.rect(0, 0, W, TOP_BAR, color=BAR)
    gfx.text(left, 10, 5, font=fonts(20), color=TEXT)
    gfx.text(right, W - 10, 5, font=fonts(20), color=TEXT, align="right")


def background(gfx):
    gfx.clear(BG)
    for x, y in STARS:
        gfx.rect(x, y, 2, 2, color=STAR)


def put_tile(gfx, sheet, k, cx, cy):
    gfx.draw(sheet, int(round(cx - TILE_W / 2.0)), int(round(cy - TILE_H / 2.0)), src=tile_src(k))


# --- a estrela ------------------------------------------------------------------
def focus_text(run):
    """ "Anel 2 · Órion Rigel" ou "Núcleo", como a navegação fala."""
    if run.ring == 0:
        return "Núcleo"
    return "Anel %d  ·  %s" % (run.ring, cell_name(run.ring, run.index))


def draw_panel(gfx, fonts, run):
    """O mesmo que o Y fala: pontos, energia, ferro, turno e o mais pesado."""
    x, w = PANEL_X, W - 10 - PANEL_X
    y = TOP_BAR + 14
    gfx.text("Pontos", x, y, font=fonts(18), color=TEXT_DIM)
    gfx.text("%d" % run.score, x, y + 22, font=fonts(34), color=TEXT)
    y += 74
    gfx.text("Energia %d de %d" % (run.energy, C.MAX_ENERGY), x, y, font=fonts(18), color=TEXT_DIM)
    pip = (w - 2 * (C.MAX_ENERGY - 1)) // C.MAX_ENERGY
    for k in range(C.MAX_ENERGY):
        px = x + k * (pip + 2)
        if k < run.energy:
            gfx.rect(px, y + 26, pip, 16, color=FOCUS)
        else:
            gfx.rect(px, y + 26, pip, 16, color=LINE, fill=False)
    # marca do custo da pressão de radiação
    cost_x = x + C.PRESSURE_COST * (pip + 2) - 1
    gfx.line(cost_x, y + 22, cost_x, y + 46, color=TEXT, width=2)
    gfx.text("pressão: %d" % C.PRESSURE_COST, x, y + 50, font=fonts(16), color=TEXT_DIM)
    y += 92
    iron = run.board.count(E.FE)
    gfx.text("Ferro %d de %d" % (iron, len(run.board.all_cells())), x, y, font=fonts(18), color=TEXT)
    y += 30
    gfx.text("Turno %d" % run.turn, x, y, font=fonts(18), color=TEXT)
    y += 40
    gfx.text("Mais pesado", x, y, font=fonts(18), color=TEXT_DIM)
    heaviest = E.name(run.heaviest) if run.heaviest else "nenhum ainda"
    gfx.text(heaviest, x, y + 24, font=fonts(22), color=TEXT)


def draw_star(gfx, sheet, fonts, run):
    background(gfx)
    top_bar(gfx, fonts, focus_text(run), E.name(run.focused()))
    b = run.board
    for r in range(b.rings + 1):
        for i in range(ring_size(r)):
            cx, cy = cell_center(r, i)
            put_tile(gfx, sheet, tile_index(b.get(r, i), core=(r == 0)), cx, cy)
    if not run.over:
        put_tile(gfx, sheet, T_FOCUS, *cell_center(run.ring, run.index))
    draw_panel(gfx, fonts, run)


# --- menus ----------------------------------------------------------------------
MENU_ROW = (E.H, E.HE, E.C, E.O, E.NE, E.MG, E.SI)


def draw_menu(gfx, sheet, fonts, menu, overlay=False):
    items = menu.items
    if overlay:
        # cobre a estrela inteira, que é mais alta que a caixa dos outros jogos
        gfx.rect(0, TOP_BAR, W, CAPTION_Y - TOP_BAR, color=(0, 0, 0, 235))
        gfx.rect(60, 70, W - 120, 3, color=FOCUS)
        top = 86
    else:
        background(gfx)
        # uma fileira de elementos em zigue-zague, do mais leve ao mais pesado
        n = len(MENU_ROW)
        for k, sym in enumerate(MENU_ROW):
            cx = W // 2 + (k - (n - 1) / 2.0) * SIDE * 1.5
            cy = 82 + (SQ3 * SIDE / 2.0 if k % 2 else 0)
            put_tile(gfx, sheet, tile_index(sym), cx, cy)
        top = 160
    gfx.text(menu.title, W // 2, top, font=fonts(30), color=TEXT, align="center")
    row_h = 32
    first = top + 46
    visible = max(1, (CAPTION_Y - 12 - first) // row_h)
    start = min(max(0, menu.index - visible + 1), max(0, len(items) - visible))
    for k in range(start, min(len(items), start + visible)):
        y = first + (k - start) * row_h
        if k == menu.index:
            gfx.rect(90, y - 2, W - 180, row_h - 4, color=FOCUS)
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=OUTLINE, align="center")
        else:
            gfx.text(items[k], W // 2, y + 2, font=fonts(22), color=TEXT_DIM, align="center")


def draw_frame(gfx, sheet, fonts, run, menu, caption):
    if run is not None:
        draw_star(gfx, sheet, fonts, run)
        if menu is not None:
            draw_menu(gfx, sheet, fonts, menu, overlay=True)
    elif menu is not None:
        draw_menu(gfx, sheet, fonts, menu)
    else:
        background(gfx)
    draw_caption(gfx, fonts, caption)


# --- ligação com o jogo ----------------------------------------------------------
def read_setting(key):
    try:
        with open(os.environ.get("A11Y_SISTEMA_CONF", "/opt/a11y/etc/sistema.conf")) as f:
            for line in f:
                k, sep, value = line.strip().partition("=")
                if sep and k == key:
                    return value.strip("'\"")
    except OSError:
        pass
    return None


def screen_on():
    if os.environ.get("A11Y_GRAPHICS") == "0":
        return False
    return read_setting("SCREEN") != "0"


def frame_interval():
    """15 quadros por segundo; menos na economia de energia. O jogo é por
    turnos e a tela só muda com um botão, então isso basta."""
    return {"moderate": 0.1, "aggressive": 0.2}.get(read_setting("ENERGY"), 1 / 15.0)


class Renderer:
    """Desenha em on_update, no ritmo de frame_interval. Uma falha de vídeo só
    desliga os gráficos: o jogo segue pelo som."""

    def __init__(self, game, get_run):
        self.game = game
        self.get_run = get_run
        self.caption = ""
        self.shown = None
        self._say = game.say
        game.say = self.say   # a legenda é sempre a última fala
        self.gfx = None
        self.sheet = None
        self.fonts = None
        self.failed = False
        self.enabled = False
        self.interval = 1 / 15.0
        self.due = 0.0
        self.checked = -1.0
        game.on_update(self.update)
        game.on_quit(self.close)

    def say(self, text, queue=False, on_done=None):
        self.caption = (self.caption + " " + text) if queue and self.caption else text
        self.caption = self.caption[-400:]
        self._say(text, queue=queue, on_done=on_done)

    def menu(self):
        focus = getattr(self.game, "_focus", [])
        return focus[-1] if focus else None

    def scene(self):
        """(partida, menu). Uma partida que acabou continua na tela enquanto o
        jogo fala o final, até o menu abrir."""
        run, menu = self.get_run(), self.menu()
        if run is not None:
            self.shown = run
        elif menu is not None:
            self.shown = None
        return self.shown, menu

    def open(self):
        from r36s_a11y.graphics import Graphics
        gfx = Graphics("Stelar Flow", self.game.dir)
        if not gfx.open():
            self.failed = True
            return False
        self.gfx = gfx
        self.sheet = gfx.image("graficos/casas.png")
        self.fonts = Fonts(gfx)
        return True

    def close(self):
        if self.gfx is not None and self.gfx.available:
            self.gfx.close()
        self.gfx = None

    def update(self, dt):
        now = time.monotonic()
        if now - self.checked >= 0.5:
            self.checked = now
            self.enabled = screen_on()
            self.interval = frame_interval()
            if not self.enabled:
                self.close()
        if not self.enabled or self.failed:
            return
        self.due += dt
        if self.due < self.interval:
            return
        self.due = 0.0
        try:
            if self.gfx is None and not self.open():
                return
            run, menu = self.scene()
            self.gfx.begin()
            draw_frame(self.gfx, self.sheet, self.fonts, run, menu, self.caption)
            self.gfx.end()
        except Exception as exc:   # gráfico com defeito não pode derrubar o jogo
            print("[stelar] gráficos desligados: %s" % exc)
            self.failed = True
            self.close()
