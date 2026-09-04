"""P3 dense-grid analysis on the committed 500-model subset.

ALL DEFINITIONS ARE THE FROZEN ONES, reused not restated:
  automaticity   _job returns bpm; None => quiescent
  EMQF           per-model paired: paces under verapamil alone AND under
                 ivabradine alone, but fails the pair          (taskG_analyse)
  denominator    models pacing DRUG-FREE in that state         (taskG_analyse)
  interval       Wilson 95%                                    (taskG_analyse)
  ceiling        per-model eligibility: automatic under BOTH singles
  Bliss          Pexp = PA + PB - PA*PB, with the frozen 5-way class ladder
                 (no events / ceiling / SUPER-ADDITIVE / SUB-ADDITIVE /
                 additive); "no events" and "ceiling" are the NON-INFORMATIVE
                 rungs and are excluded from interpretation    (taskG_analyse)
  bands          240 mg/day 2.9-14.0% block, 480 mg/day 10.8-30.0% block
                                                               (taskL/taskH)
  comparison pt  240 mg/day time-average = 2.9% block (PRIMARY);
                 Cmax = 14.0% (sensitivity)                    (taskN CMP_240)
  SmPC           observed additional -5 bpm                    (taskN)
  decomposition  PK_only / PD_only / PK+PD, in bpm vs ivabradine alone at 1x
                                                               (taskN N2)
Nothing fitted; no pair result informs any parameter.
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "08_taskP", "p3")
CKPT = os.path.join(DEST, "P3_dense_checkpoint.jsonl")

ANCHORS = [("Doesch 2007 (PRIMARY)", {"1x": 0.5840, "2x": 0.7097, "3x": 0.7717}),
           ("10-year cohort",        {"1x": 0.5090, "2x": 0.6435, "3x": 0.7140}),
           ("36-month (superseded)", {"1x": 0.3120, "2x": 0.4412, "3x": 0.5220})]
B_7X = 0.6827
VER = [0.0, 0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25, 0.275, 0.30, 0.40]
BAND = {"240 mg/day": (0.029, 0.140), "480 mg/day": (0.108, 0.300)}
IC50_V, HILL_V, MW_V, FU_V = 198.7, 1.09, 454.6, 0.104
CMP_240 = {"time-average (PRIMARY)": 0.029, "Cmax (sensitivity)": 0.14}
SMPC_OBSERVED_BPM = -5.0


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def total_ng(block):
    if block <= 0:
        return 0.0
    free = IC50_V * (block / (1.0 - block)) ** (1.0 / HILL_V)
    return free / FU_V * MW_V / 1000.0


bpm = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    bpm[(r["model"], r["state"], round(r["b_cal"], 6),
         round(r["b_f"], 6))] = r["bpm"]

models = sorted({k[0] for k in bpm})
print(f"models: {len(models)}   records: {len(bpm)}")
pops = {st: [m for m in models if bpm.get((m, st, 0.0, 0.0)) is not None]
        for st in ("control", "iso")}
for st in pops:
    print(f"  {st:8s} drug-free pacing (denominator): {len(pops[st])} / "
          f"{len(models)}   excluded {len(models)-len(pops[st])}")

out = {"subset_n": len(models), "denominators":
       {st: len(pops[st]) for st in pops}, "rows": [], "bands": BAND}


def paces(m, st, bc, bf):
    return bpm.get((m, st, round(bc, 6), round(bf, 6))) is not None


print()
print("=" * 138)
print("RUNG-LEVEL RESULTS - every anchor x arm x state x rung")
print("=" * 138)
hdr = (f"{'anchor':22s} {'arm':3s} {'state':7s} {'bCaL':>6s} {'bIf':>6s} "
       f"{'ng/mL':>7s} | {'VerA':>11s} {'IvabA':>11s} {'Combo':>11s} | "
       f"{'k':>4s} {'EMQF%':>7s} {'95% CI':>15s} | {'elig':>4s} {'max%':>6s} "
       f"{'o/m':>5s} | {'>5p':>3s} {'>5c':>3s} {'>10p':>4s} {'>10c':>4s}")
for aname, arms in ANCHORS:
    for arm in ("1x", "2x", "3x"):
        bf = arms[arm]
        for st in ("control", "iso"):
            pop = pops[st]
            N = len(pop)
            ivab_q = sum(1 for m in pop if not paces(m, st, 0.0, bf))
            for bc in VER:
                if bc == 0.0:
                    continue
                ver_q = sum(1 for m in pop if not paces(m, st, bc, 0.0))
                comb_q = sum(1 for m in pop if not paces(m, st, bc, bf))
                k = sum(1 for m in pop if paces(m, st, bc, 0.0)
                        and paces(m, st, 0.0, bf) and not paces(m, st, bc, bf))
                elig = sum(1 for m in pop if paces(m, st, bc, 0.0)
                           and paces(m, st, 0.0, bf))
                lo, hi = wilson(k, N)
                e = k / N
                bands = [b for b, (l, h) in BAND.items()
                         if l - 1e-9 <= bc <= h + 1e-9]
                out["rows"].append({
                    "anchor": aname, "arm": arm, "state": st, "b_cal": bc,
                    "b_f": bf, "total_ng_per_mL": total_ng(bc),
                    "bands": bands, "n": N,
                    "ver_alone_k": ver_q, "ver_alone_frac": ver_q / N,
                    "ivab_alone_k": ivab_q, "ivab_alone_frac": ivab_q / N,
                    "combo_k": comb_q, "combo_frac": comb_q / N,
                    "EMQF_k": k, "EMQF": e,
                    "EMQF_ci95": [float(lo), float(hi)],
                    "eligible_k": elig, "eligible_frac": elig / N,
                    "max_possible_EMQF": elig / N,
                    "obs_over_max": e / (elig / N) if elig else None,
                    "point_gt_5pct": bool(e > 0.05),
                    "ci_lower_gt_5pct": bool(lo > 0.05),
                    "point_gt_10pct": bool(e > 0.10),
                    "ci_lower_gt_10pct": bool(lo > 0.10)})

for aname, _ in ANCHORS:
    for st in ("control", "iso"):
        print(f"\n--- {aname}  |  {st} ---")
        print(hdr)
        for r in out["rows"]:
            if r["anchor"] != aname or r["state"] != st:
                continue
            print(f"{r['anchor']:22s} {r['arm']:3s} {r['state']:7s} "
                  f"{r['b_cal']:6.3f} {r['b_f']:6.4f} "
                  f"{r['total_ng_per_mL']:7.1f} | "
                  f"{r['ver_alone_k']:4d} {r['ver_alone_frac']:6.1%} "
                  f"{r['ivab_alone_k']:4d} {r['ivab_alone_frac']:6.1%} "
                  f"{r['combo_k']:4d} {r['combo_frac']:6.1%} | "
                  f"{r['EMQF_k']:4d} {r['EMQF']:7.2%} "
                  f"[{r['EMQF_ci95'][0]:5.2%},{r['EMQF_ci95'][1]:5.2%}] | "
                  f"{r['eligible_k']:4d} {r['eligible_frac']:6.1%} "
                  f"{r['obs_over_max'] if r['obs_over_max'] else 0:5.3f} | "
                  f"{'Y' if r['point_gt_5pct'] else '.':>3s} "
                  f"{'Y' if r['ci_lower_gt_5pct'] else '.':>3s} "
                  f"{'Y' if r['point_gt_10pct'] else '.':>4s} "
                  f"{'Y' if r['ci_lower_gt_10pct'] else '.':>4s}")

with open(os.path.join(DEST, "P3_results_core.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"\n-> 08_taskP/p3/P3_results_core.json  ({len(out['rows'])} rows)")
