#!/usr/bin/env python3
"""Gera os sons provisórios do Stelar Flow, só com a biblioteca padrão.

Cada elemento tem um tom: quanto mais pesado, mais grave e mais rico em
harmônicos; o ferro é um zumbido dissonante. Para trocar um som, ponha um
arquivo com o mesmo nome em sounds/ (WAV ou OGG) e apague o provisório.

    python3 tools/gerar_sons.py
"""
import math
import os
import random
import struct
import sys
import wave

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stelar import elements as E  # noqa: E402

RATE = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
rng = random.Random(7)

TONE = {E.H: 1046.5, E.HE: 880.0, E.C: 698.5, E.O: 587.3, E.NE: 523.3,
        E.MG: 440.0, E.SI: 370.0, E.S: 311.1, E.FE: 110.0}


def n(sec):
    return int(RATE * sec)


def tone(freq, sec, harmonics=1, decay=0.15, glide=0.0):
    out = []
    phase = 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = freq * (1 + glide * t / sec)
        phase += 2 * math.pi * f / RATE
        v = sum(math.sin(phase * h) / h for h in range(1, harmonics + 1))
        out.append(v * math.exp(-t / decay))
    return out


def noise(sec, decay=0.1, rise=False):
    out = []
    last = 0.0
    for k in range(n(sec)):
        t = k / RATE
        last = 0.7 * last + 0.3 * rng.uniform(-1, 1)   # ruído mais grave
        env = (t / sec) if rise else math.exp(-t / decay)
        out.append(last * env)
    return out


def sweep(f0, f1, sec, harmonics=3):
    out, phase = [], 0.0
    for k in range(n(sec)):
        t = k / RATE
        f = f0 * (f1 / f0) ** (t / sec)
        phase += 2 * math.pi * f / RATE
        env = min(1.0, t / 0.02) * (1 - t / sec)
        out.append(env * sum(math.sin(phase * h) / h for h in range(1, harmonics + 1)))
    return out


def mix(*parts, offsets=None):
    offsets = offsets or [0.0] * len(parts)
    length = max(n(o) + len(p) for p, o in zip(parts, offsets))
    out = [0.0] * length
    for p, o in zip(parts, offsets):
        start = n(o)
        for k, v in enumerate(p):
            out[start + k] += v
    return out


def write(name, samples, gain=0.8):
    peak = max(1e-9, max(abs(v) for v in samples))
    fade = min(len(samples), n(0.01))
    data = bytearray()
    for k, v in enumerate(samples):
        if k >= len(samples) - fade:
            v *= (len(samples) - k) / float(fade)
        data += struct.pack("<h", int(max(-1, min(1, v / peak * gain)) * 32767))
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(bytes(data))


def element_sound(sym, sec=0.22):
    if sym == E.FE:
        return mix(tone(110, 0.3, 6, 0.2), tone(117, 0.3, 6, 0.2), noise(0.3, 0.15))
    rank = E.mass_rank(sym)
    return tone(TONE[sym], sec, harmonics=1 + rank, decay=0.08 + 0.015 * rank)


def main():
    os.makedirs(OUT, exist_ok=True)
    for sym in E.ORDER:
        write("elem_" + sym.lower(), element_sound(sym), gain=0.7)
    write("elem_vazio", noise(0.08, 0.02), gain=0.35)
    for sym in E.ORDER[1:]:
        base = TONE[sym]
        notes = [tone(base * r, 0.25, 2, 0.12) for r in (0.5, 0.75, 1.0)]
        write("fusao_" + sym.lower(), mix(*notes, offsets=[0.0, 0.06, 0.12]), gain=0.75)
    for sym in (E.H, E.HE, E.C):
        write("entrada_" + sym.lower(), tone(TONE[sym] * 0.8, 0.18, 2, 0.1, glide=0.25), gain=0.5)
    write("colapso", mix(sweep(700, 110, 0.45), noise(0.45, 0.3)), gain=0.7)
    write("pressao", mix(sweep(150, 900, 0.5, 2), noise(0.5, rise=True)), gain=0.6)
    write("rotacao", mix(noise(0.04, 0.008), noise(0.04, 0.008), offsets=[0.0, 0.07]), gain=0.6)
    write("borda", tone(90, 0.14, 3, 0.05), gain=0.7)
    write("infeccao", mix(tone(110, 0.6, 8, 0.25), tone(116.5, 0.6, 8, 0.25),
                          tone(233, 0.6, 4, 0.2)), gain=0.8)
    write("inicio", mix(*[tone(f, 0.7, 2, 0.35) for f in (262, 330, 392, 523)],
                        offsets=[0.0, 0.1, 0.2, 0.3]), gain=0.7)
    write("fim", mix(sweep(300, 40, 1.6, 5), noise(1.6, 0.8)), gain=0.85)
    write("menu_mover", tone(660, 0.06, 2, 0.03), gain=0.4)
    write("menu_confirmar", mix(tone(660, 0.12, 2, 0.06), tone(990, 0.12, 2, 0.06),
                                offsets=[0.0, 0.05]), gain=0.5)
    print("sons gerados em %s" % os.path.normpath(OUT))


if __name__ == "__main__":
    main()
