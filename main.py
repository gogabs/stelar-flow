#!/usr/bin/env python3
"""Stelar Flow: funda elementos numa estrela antes que o ferro tome conta."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Durante o desenvolvimento, usa a biblioteca do repositório vizinho se não houver cópia aqui.
if not os.path.isdir(os.path.join(HERE, "r36s_a11y")):
    sys.path.insert(1, os.path.join(HERE, "..", "r36s-a11y-sdk", "python"))

import r36s_a11y as a11y

from stelar import config as C
from stelar import elements as E
from stelar import texts as T
from stelar.fates import BY_ID, FATES
from stelar.run import Run

game = a11y.Game(repeat=True, axes=True)
SAVE_FILE = os.path.join(game.save_dir, "progresso.json")
sounds = {}
for f in sorted(os.listdir(os.path.join(game.dir, "sounds"))):
    base, ext = os.path.splitext(f)
    if ext.lower() in (".wav", ".ogg"):
        sounds[base] = game.sound.load(base, os.path.join("sounds", f))
menu_sounds = {"move": sounds.get("menu_mover"), "select": sounds.get("menu_confirmar")}

state = {"run": None, "rings": C.RINGS, "stick": None}


# --- progresso -------------------------------------------------------------
def load_progress():
    try:
        with open(SAVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault("recordes", {})
    data.setdefault("finais", [])
    data.setdefault("aneis", C.RINGS)
    return data


def save_progress(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# --- som e fala --------------------------------------------------------------
class UI:
    """Ponte entre a partida e o áudio: ângulo e anel viram posição 3D."""

    def say(self, text, queue=False):
        game.say(text, queue=queue)

    def play(self, name, ring=None, angle=None, pitch=1.0):
        sound = sounds.get(name)
        if sound is None:
            return
        if angle is None or not ring:
            sound.play(pitch=pitch)
            return
        d = C.RING_DISTANCE[min(ring, len(C.RING_DISTANCE) - 1)]
        a = 2 * math.pi * angle
        sound.play(pitch=pitch, pos=(math.sin(a) * d, 0.0, -math.cos(a) * d))


ui = UI()


# --- fluxo -------------------------------------------------------------------
def start_run():
    main_menu.close()
    run = Run(ui, rings=state["rings"], on_over=game_over)
    state["run"] = run
    run.start()


def game_over(summary):
    data = load_progress()
    key = str(summary["rings"])
    best = data["recordes"].get(key, 0)
    fate = BY_ID[summary["fate"]]
    new_fate = fate[0] not in data["finais"]
    if new_fate:
        data["finais"].append(fate[0])
    text = T.game_over(summary, fate, best, new_fate)
    if summary["score"] > best:
        data["recordes"][key] = summary["score"]
    save_progress(data)
    state["run"] = None
    game.after(1.2, lambda: game.say(text, on_done=lambda done: main_menu.open(announce_help=False)))


def ring_item():
    return "Tamanho da estrela: %d anéis" % state["rings"]


def progress_text():
    data = load_progress()
    parts = []
    for rings in C.RING_CHOICES:
        best = data["recordes"].get(str(rings))
        parts.append("Recorde com %d anéis: %s." % (rings, "%d pontos" % best if best else "nenhum"))
    found = [f[1] for f in FATES if f[0] in data["finais"]]
    parts.append("Finais descobertos: %d de %d." % (len(found), len(FATES)))
    if found:
        parts.append(", ".join(found) + ".")
    return " ".join(parts)


def on_main(index, item):
    if item == "Jogar":
        start_run()
    elif item.startswith("Tamanho"):
        choices = C.RING_CHOICES
        state["rings"] = choices[(choices.index(state["rings"]) + 1) % len(choices)]
        data = load_progress()
        data["aneis"] = state["rings"]
        save_progress(data)
        main_menu.items[index] = ring_item()
        game.say(main_menu.items[index])
    elif item == "Como jogar":
        main_menu.close()
        help_menu.open()
    elif item == "Recordes e finais":
        game.say(progress_text())
    else:
        game.quit()


main_menu = a11y.Menu(game, "Stelar Flow",
                      ["Jogar", ring_item(), "Como jogar", "Recordes e finais", "Sair"],
                      on_select=on_main, on_back=game.quit, sounds=menu_sounds)


def close_help():
    help_menu.close()
    main_menu.open(index=2, announce_help=False)


help_menu = a11y.Menu(game, "Como jogar", [t for t, _ in T.HELP] + ["Voltar"],
                      on_select=lambda i, item: close_help() if item == "Voltar" else game.say(T.HELP[i][1]),
                      on_back=close_help, sounds=menu_sounds)


def on_pause(index, item):
    pause_menu.close()
    run = state["run"]
    if item == "Continuar":
        run.announce_focus(with_ring=True)
        return
    state["run"] = None
    main_menu.open(announce_help=False)


pause_menu = a11y.Menu(game, "Pausa", ["Continuar", "Sair para o menu"],
                       on_select=on_pause, on_back=lambda: on_pause(0, "Continuar"),
                       sounds=menu_sounds)


# --- controles ----------------------------------------------------------------
NAVIGATION = {"up": lambda r: r.ring_out(), "down": lambda r: r.ring_in(),
              "left": lambda r: r.step(-1), "right": lambda r: r.step(1)}


@game.on_button
def button(b, st, ms):
    run = state["run"]
    if run is None or run.over:
        return
    if st == a11y.REPEAT:
        if b in ("left", "right"):
            NAVIGATION[b](run)
        return
    if st != a11y.DOWN:
        return
    if b in NAVIGATION:
        NAVIGATION[b](run)
    elif b == "b":
        run.collapse()
    elif b == "x":
        run.pressure()
    elif b == "l1":
        run.rotate(-1)
    elif b == "r1":
        run.rotate(1)
    elif b == "y":
        game.say(run.status_text())
    elif b == "a":
        game.say(run.ring_text())
    elif b == "select":
        game.say(run.focus_text())
    elif b == "start":
        pause_menu.open()


@game.on_axis
def axis(name, value, ms):
    """O analógico esquerdo vale como direcional: um passo cada vez que sai do centro."""
    run = state["run"]
    # game._focus: um menu aberto (pausa) recebe os botões, mas não os eixos.
    if run is None or run.over or name not in ("lx", "ly") or game._focus:
        return
    x, y = game.input.axis_value.get("lx", 0.0), game.input.axis_value.get("ly", 0.0)
    if max(abs(x), abs(y)) < C.AXIS_THRESHOLD:
        if max(abs(x), abs(y)) < C.AXIS_THRESHOLD / 2:
            state["stick"] = None
        return
    if abs(x) > abs(y):
        direction = "right" if x > 0 else "left"
    else:
        direction = "down" if y > 0 else "up"
    if direction != state["stick"]:
        state["stick"] = direction
        NAVIGATION[direction](run)


@game.on_start
def start():
    state["rings"] = load_progress().get("aneis", C.RINGS)
    if state["rings"] not in C.RING_CHOICES:
        state["rings"] = C.RINGS
    main_menu.items[1] = ring_item()
    main_menu.open()


game.run()
