"""Task D addendum: stratify the control-state prediction by baseline rate.

Boden 2001's resting anchor is specifically "no significant HR reduction at
baseline HR <= 74 beats/min". The retained population spans 61-99.6 bpm, so the
directly comparable subgroup is the models whose own control rate is <= 74 bpm.
The elevated stratum (>= 85 bpm) is also reported, since that is the category
the Iso state sits in and where the drug IS effective clinically.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
POP = os.path.join(OUT, "taskA_G_CaL_population_sweep.json")
TD = os.path.join(OUT, "taskD_state_transfer.json")

with open(POP, encoding="utf-8") as f:
    pop = json.load(f)
with open(TD, encoding="utf-8") as f:
    td = json.load(f)

grid = sorted(float(k) for k in pop["records"][0]["levels"])


def response(rec, block):
    lo = max([g for g in grid if g <= block], default=grid[0])
    hi = min([g for g in grid if g >= block], default=grid[-1])
    fr = 0.0 if hi == lo else (block - lo) / (hi - lo)
    a, b = rec["levels"].get(str(lo)), rec["levels"].get(str(hi))
    if a is None or b is None:
        return None
    return a["bpm"] + fr * (b["bpm"] - a["bpm"])


STRATA = [("<=74 bpm  (Boden: NO effect)", lambda x: x <= 74),
          ("74-84 bpm (Boden: effect)", lambda x: 74 < x < 85),
          (">=85 bpm  (Boden: effect)", lambda x: x >= 85)]

print("Control-state prediction, stratified by each model's own baseline rate")
print("Calibrated at Iso 1 uM to reproduce diltiazem's elevated-rate effect.\n")

out = {}
for res in td["results"]:
    b = res.get("block")
    if b is None:
        continue
    tgt = res["target_drop_bpm"]
    print(f"=== calibrated to {-tgt:.0f} bpm at Iso  ->  block* = {b*100:.2f}% ===")
    row = {}
    for label, sel in STRATA:
        drops, quiet, n = [], 0, 0
        for r in pop["records"]:
            b0 = r["levels"].get("0.0")
            if not b0 or not sel(b0["bpm"]):
                continue
            n += 1
            v = response(r, b)
            if v is None:
                quiet += 1
            else:
                drops.append(v - b0["bpm"])
        if n == 0:
            continue
        med = float(np.median(drops)) if drops else None
        pctq = quiet / n * 100
        row[label] = {"n": n, "median_drop_bpm": med,
                      "quiescent_pct": pctq,
                      "n_quiescent": quiet}
        ms = f"{med:+7.2f}" if med is not None else "   n/a "
        print(f"   {label:32s} n={n:3d}  median dHR {ms} bpm   "
              f"quiescent {pctq:5.1f}%")
    out[str(tgt)] = row
    print()

with open(os.path.join(OUT, "taskD_strata.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"-> {os.path.join(OUT, 'taskD_strata.json')}")
