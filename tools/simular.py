#!/usr/bin/env python3
"""Simula partidas com jogadores automáticos para medir o equilíbrio.

    python3 tools/simular.py [partidas] [anéis]

"aleatório" aperta qualquer ação; "guloso" testa cada ação numa cópia da
partida e escolhe a que dá mais pontos, evitando ferro.
"""
import copy
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stelar import elements as E  # noqa: E402
from stelar.board import ring_size  # noqa: E402
from stelar.run import Run  # noqa: E402


class Mute:
    def say(self, text, queue=False):
        pass

    def play(self, name, **kw):
        pass


def actions(run):
    acts = [("collapse",), ("pressure",)]
    for r in range(1, run.rings + 1):
        for i in range(ring_size(r)):
            for d in (-1, 1):
                acts.append(("rotate", r, i, d))
    return acts


def apply(run, act):
    if act[0] == "collapse":
        return run.collapse()
    if act[0] == "pressure":
        return run.pressure()
    run.ring, run.angle = act[1], act[2] / float(ring_size(act[1]))
    return run.rotate(act[3])


def value(run):
    """Pontos, mais o quanto a grade está boa para os próximos colapsos."""
    from stelar.board import parent
    b = run.board
    good = 0
    for r, i in b.all_cells():
        sym = b.get(r, i)
        if r == 0 or sym is None or sym == E.FE:
            continue
        target = b.get(*parent(r, i))
        if target is None or E.fuse(target, sym):
            good += 1
    return (run.score + 4 * run.energy - 60 * b.count(E.FE)
            + 3 * len(b.empty_cells()) + 4 * good)


def greedy(run, rng):
    best, best_v = None, None
    for act in actions(run):
        trial = copy.deepcopy(run)
        trial.rng = random.Random(rng.random())
        trial.board.rng = trial.rng
        if not apply(trial, act):
            continue
        v = value(trial) - (10000 if trial.over else 0)
        if best_v is None or v > best_v:
            best, best_v = act, v
    return best


def rand(run, rng):
    return rng.choice(actions(run))


def play(policy, rings, seed, max_turns=2000):
    rng = random.Random(seed)
    result = {}
    run = Run(Mute(), rings=rings, rng=random.Random(seed), on_over=result.update)
    run.start()
    while not run.over and run.turn < max_turns:
        act = policy(run, rng)
        if act is None or not apply(run, act):
            apply(run, ("rotate", run.rings, 0, 1))
    return result or {"score": run.score, "turns": run.turn, "fate": "limite", "heaviest": run.heaviest}


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    rings = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    for name, policy in (("aleatório", rand), ("guloso", greedy)):
        results = [play(policy, rings, s) for s in range(games)]
        turns = [r["turns"] for r in results]
        scores = [r["score"] for r in results]
        fates = {}
        for r in results:
            fates[r["fate"]] = fates.get(r["fate"], 0) + 1
        print("%s, %d anéis: turnos mediana %d (%d-%d), pontos mediana %d (%d-%d)" % (
            name, rings, statistics.median(turns), min(turns), max(turns),
            statistics.median(scores), min(scores), max(scores)))
        print("   finais: %s" % ", ".join("%s %d" % kv for kv in sorted(fates.items())))


if __name__ == "__main__":
    main()
