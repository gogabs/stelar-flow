#!/usr/bin/env python3
"""Gera a folha de casas do Stelar Flow (graficos/casas.png). Precisa do Pillow,
mas só aqui, no PC: o console só carrega o PNG pronto.

    python3 tools/gerar_graficos.py

Uma fileira só, na ordem de stelar/desenho.py: casa vazia, núcleo vazio, os
nove elementos do hidrogênio ao ferro e a moldura do foco. Tudo é desenhado em
4x e reduzido, para as bordas ficarem suaves.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from stelar import desenho as D  # noqa: E402
from stelar import elements as E  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graficos")
SS = 4
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
GAP = 1.6          # meia folga entre hexágonos vizinhos, em pixels


def rgb(hexcolor, alpha=255):
    h = hexcolor.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def canvas():
    img = Image.new("RGBA", (D.TILE_W * SS, D.TILE_H * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), (D.TILE_W * SS / 2.0, D.TILE_H * SS / 2.0)


def hexagon(d, c, radius, **kw):
    d.polygon(D.hex_points(c[0], c[1], radius), **kw)


def hex_ring(d, c, outer, inner, fill):
    """Faixa entre dois hexágonos (desenhada como seis trapézios)."""
    po, pi = D.hex_points(c[0], c[1], outer), D.hex_points(c[0], c[1], inner)
    for k in range(6):
        j = (k + 1) % 6
        d.polygon([po[k], po[j], pi[j], pi[k]], fill=fill)


def symbol(d, c, text, color, size):
    font = ImageFont.truetype(FONT_BOLD, size)
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text((c[0] - w / 2.0 - box[0], c[1] - h / 2.0 - box[1]), text, font=font, fill=color)


def shrink(img):
    return img.resize((D.TILE_W, D.TILE_H), Image.LANCZOS)


def empty(core=False):
    img, d, c = canvas()
    r = (D.SIDE - GAP) * SS
    hexagon(d, c, r, fill=rgb(D.EMPTY_LINE))
    hexagon(d, c, r - 2 * SS, fill=rgb(D.EMPTY))
    if core:   # o núcleo vazio: um sol apagado, para achar o centro
        rr = D.SIDE * 0.42 * SS
        d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], outline=rgb(D.CORE_GLOW), width=2 * SS)
        for k in range(8):
            a = math.pi / 4 * k
            d.line([(c[0] + math.cos(a) * rr * 1.25, c[1] + math.sin(a) * rr * 1.25),
                    (c[0] + math.cos(a) * rr * 1.6, c[1] + math.sin(a) * rr * 1.6)],
                   fill=rgb(D.CORE_GLOW), width=2 * SS)
    return shrink(img)


def element(sym):
    img, d, c = canvas()
    r = (D.SIDE - GAP) * SS
    hexagon(d, c, r, fill=rgb(D.OUTLINE))
    hexagon(d, c, r - 1.5 * SS, fill=rgb(D.COLORS[sym]))
    if sym == E.FE:   # ferro: riscado na diagonal, para não depender da cor
        mask = Image.new("L", img.size, 0)
        hexagon(ImageDraw.Draw(mask), c, r - 1.5 * SS, fill=255)
        hatch = Image.new("RGBA", img.size, (0, 0, 0, 0))
        hd = ImageDraw.Draw(hatch)
        step = 7 * SS
        for k in range(-img.size[1], img.size[0] + img.size[1], step):
            hd.line([(k, 0), (k + img.size[1], img.size[1])], fill=rgb(D.IRON_HATCH), width=2 * SS)
        img.alpha_composite(Image.composite(hatch, Image.new("RGBA", img.size), mask))
        d = ImageDraw.Draw(img)
        # o símbolo numa plaquinha preta, legível por cima dos riscos
        pw, ph = D.SIDE * 0.95 * SS, D.SIDE * 0.72 * SS
        d.rounded_rectangle([c[0] - pw / 2, c[1] - ph / 2, c[0] + pw / 2, c[1] + ph / 2],
                            radius=4 * SS, fill=rgb(D.OUTLINE))
    size = int(D.SIDE * (0.78 if len(sym) == 1 else 0.66) * SS)
    symbol(d, c, sym, rgb(D.INK[sym]), size)
    return shrink(img)


def focus():
    """Moldura amarela grossa com contorno preto por dentro e por fora."""
    img, d, c = canvas()
    outer = (D.SIDE + 5) * SS
    hex_ring(d, c, outer, outer - 1.5 * SS, rgb(D.OUTLINE))
    hex_ring(d, c, outer - 1.5 * SS, outer - 6 * SS, rgb(D.FOCUS))
    hex_ring(d, c, outer - 6 * SS, outer - 7.5 * SS, rgb(D.OUTLINE))
    return shrink(img)


def main():
    os.makedirs(OUT, exist_ok=True)
    tiles = []
    for name in D.TILES:
        if name is None:
            tiles.append(empty())
        elif name == "nucleo":
            tiles.append(empty(core=True))
        elif name == "foco":
            tiles.append(focus())
        else:
            tiles.append(element(name))
    sheet = Image.new("RGBA", (D.TILE_W * len(tiles), D.TILE_H), (0, 0, 0, 0))
    for k, tile in enumerate(tiles):
        sheet.paste(tile, (k * D.TILE_W, 0))
    path = os.path.join(OUT, "casas.png")
    sheet.save(path, optimize=True)
    print(path)


if __name__ == "__main__":
    main()
