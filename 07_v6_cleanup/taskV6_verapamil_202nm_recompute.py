"""Task 4 - verapamil IC50 sensitivity: 198.7 nM (refit) vs 202 nM (author).

Recomputes every exposure-dependent downstream quantity under both IC50 values.
Reads the frozen simulation store only; NO cellular simulation is re-run, since
the simulated block ladder is independent of the exposure->block mapping.

Writes 07_v6_cleanup/verapamil_202nm_recompute.json (old vs new).
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "07_v6_cleanup")
os.makedirs(DEST, exist_ok=True)

MW, FU, HILL = 454.6, 0.104, 1.09
IC50_OLD, IC50_NEW = 198.7, 202.0
BANDS = {"240 mg/day": (35.0, 164.0), "480 mg/day": (125.0, 400.0)}
ANCH = {"Doesch 2007  (PRIMARY)": "Doesch (primary)",
        "10-year cohort": "10-year",
        "36-month (superseded)": "36-month (superseded)"}
ARMS = ["1x", "2x", "3x"]

tl = json.load(open(os.path.join(OUT, "taskL_three_anchor_EAR.json"),
                    encoding="utf-8"))


def blk(c, ic):
    x = (c / ic) ** HILL
    return x / (1 + x)


def free(ng):
    return ng / MW * 1000 * FU


rep = {"note": "No simulation re-run; the block ladder is independent of the "
                "exposure->block mapping. Only the mapping and any "
                "band-membership decision it drives are affected.",
       "ic50_old_nM": IC50_OLD, "ic50_new_nM": IC50_NEW,
       "hill": HILL, "f_unbound": FU, "bands": {}, "emqf": {}}

print("=" * 92)
print("BAND MAPPING")
print("=" * 92)
for k, (lo, hi) in BANDS.items():
    f = (free(lo), free(hi))
    o = (blk(f[0], IC50_OLD), blk(f[1], IC50_OLD))
    n = (blk(f[0], IC50_NEW), blk(f[1], IC50_NEW))
    rep["bands"][k] = {"free_nM": list(f),
                       "block_old": list(o), "block_new": list(n),
                       "delta_pp": [(n[0] - o[0]) * 100, (n[1] - o[1]) * 100]}
    print(f"  {k}: free {f[0]:.2f}-{f[1]:.2f} nM")
    print(f"    198.7 nM -> {o[0]:.2%} - {o[1]:.2%}")
    print(f"    202.0 nM -> {n[0]:.2%} - {n[1]:.2%}   "
          f"(delta {(n[0]-o[0])*100:+.3f} / {(n[1]-o[1])*100:+.3f} pp)")

print()
print("=" * 92)
print("EMQF MAXIMA INSIDE EACH BAND - does the band-membership change move a maximum?")
print("=" * 92)
changed = []
for state in ("control", "iso"):
    st = tl["states"][state]
    n_pop = st["n"]
    for akey, alab in ANCH.items():
        rows = [r for r in st["rows"] if r["anchor"] == akey]
        for band, (lo, hi) in BANDS.items():
            bo = (blk(free(lo), IC50_OLD), blk(free(hi), IC50_OLD))
            bn = (blk(free(lo), IC50_NEW), blk(free(hi), IC50_NEW))
            for arm in ARMS:
                ino = [r for r in rows if bo[0] <= r["block"] <= bo[1]]
                inn = [r for r in rows if bn[0] <= r["block"] <= bn[1]]
                if not ino or not inn:
                    continue
                mo = max(ino, key=lambda r: r["arms"][arm]["EAR"])
                mn = max(inn, key=lambda r: r["arms"][arm]["EAR"])
                eo, en = mo["arms"][arm]["EAR"], mn["arms"][arm]["EAR"]
                key = f"{state}|{alab}|{band}|{arm}"
                rec = {"max_old": eo, "at_block_old": mo["block"],
                       "ci_old": mo["arms"][arm]["EAR_ci"],
                       "max_new": en, "at_block_new": mn["block"],
                       "ci_new": mn["arms"][arm]["EAR_ci"],
                       "changed": abs(eo - en) > 1e-12,
                       "rungs_old": [r["block"] for r in ino],
                       "rungs_new": [r["block"] for r in inn]}
                rep["emqf"][key] = rec
                if rec["changed"]:
                    changed.append((key, eo, mo["block"], en, mn["block"]))

print(f"  band-membership changes that move a maximum: {len(changed)}")
for k, eo, bo_, en, bn_ in changed:
    print(f"    {k}")
    print(f"      198.7 nM: {eo:.1%} at {bo_:.1%} block")
    print(f"      202.0 nM: {en:.1%} at {bn_:.1%} block   <-- HEADLINE CHANGE")

rep["n_headline_changes"] = len(changed)
rep["headline_changes"] = [
    {"key": k, "old_max": eo, "old_block": bo_, "new_max": en,
     "new_block": bn_} for k, eo, bo_, en, bn_ in changed]

json.dump(rep, open(os.path.join(DEST, "verapamil_202nm_recompute.json"), "w",
                    encoding="utf-8"), indent=2)
print(f"\n-> {os.path.join(DEST, 'verapamil_202nm_recompute.json')}")
