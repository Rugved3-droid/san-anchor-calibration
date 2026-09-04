"""Task F addendum: how load-bearing is the free-fraction assumption?

The verapamil verdict depends on converting Qi's total plasma concentration to a
free concentration. Human verapamil is ~90% protein bound; the dog value was not
located. This sweeps the assumption instead of hiding it.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")

with open(os.path.join(OUT, "taskA_G_CaL_population_sweep.json"),
          encoding="utf-8") as f:
    cal = json.load(f)
recs = cal["records"]
n = len(recs)
grid = sorted(float(k) for k in recs[0]["levels"])
frac = {b: sum(1 for r in recs if r["levels"].get(str(b)) is None) / n
        for b in grid}

IC50, HILL, MW = 198.7, 1.09, 454.6
PLASMA = (98.0, 204.0)


def wilson(k, nn, z=1.96):
    p = k / nn
    d = 1 + z * z / nn
    c = (p + z * z / (2 * nn)) / d
    h = z * np.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def block(cf):
    x = (cf / IC50) ** HILL
    return x / (1 + x)


def failure(b):
    if b <= grid[0]:
        return frac[grid[0]]
    if b >= grid[-1]:
        return frac[grid[-1]]
    lo = max(g for g in grid if g <= b)
    hi = min(g for g in grid if g >= b)
    f = 0 if hi == lo else (b - lo) / (hi - lo)
    return frac[lo] + f * (frac[hi] - frac[lo])


print("Verapamil free-fraction sensitivity (Qi 0.2 mg/kg IV, dog)")
print(f"  total plasma {PLASMA[0]:.0f}-{PLASMA[1]:.0f} ng/mL, "
      f"IC50 {IC50} nM, Hill {HILL}\n")
print(f"{'f_u':>6s} {'free nM':>14s} {'I_CaL block':>16s} "
      f"{'failure fraction':>18s} {'in 20-40%?':>11s}")
rows = []
for fu in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50):
    c = [p / MW * 1000 * fu for p in PLASMA]
    b = [block(x) for x in c]
    fr = [failure(x) for x in b]
    hit = (fr[1] >= 0.20 and fr[0] <= 0.40) or (0.20 <= fr[1] <= 0.40)
    print(f"{fu:6.0%} {c[0]:6.1f}-{c[1]:6.1f} {b[0]:7.1%}-{b[1]:6.1%} "
          f"{fr[0]:8.1%}-{fr[1]:7.1%} {'YES' if hit else 'no':>11s}")
    rows.append({"f_unbound": fu, "free_nM": c, "block": b,
                 "failure_fraction": fr, "in_window": bool(hit)})

print("\nObserved (Qi):")
for k, nn, lbl in ((2, 10, "autonomic blockade"), (2, 5, "transplant")):
    lo, hi = wilson(k, nn)
    print(f"  {lbl:20s} {k}/{nn} = {k/nn:.0%}  95% CI [{lo:.1%}, {hi:.1%}]")

print("\nModel prediction at f_u = 10% (human-derived): "
      f"{failure(block(PLASMA[0]/MW*1000*0.10)):.1%} - "
      f"{failure(block(PLASMA[1]/MW*1000*0.10)):.1%}")
lo10, hi10 = wilson(2, 10)
pred_hi = failure(block(PLASMA[1] / MW * 1000 * 0.10))
print(f"  inside the 2/10 observed CI [{lo10:.1%}, {hi10:.1%}]? "
      f"{lo10 <= pred_hi <= hi10}")

json.dump(rows, open(os.path.join(OUT, "taskF_sensitivity.json"), "w",
                     encoding="utf-8"), indent=2)
print(f"\n-> {os.path.join(OUT, 'taskF_sensitivity.json')}")
