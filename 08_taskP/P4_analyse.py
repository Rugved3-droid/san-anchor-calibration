"""P4 anchor-replication analysis.

Endpoint definitions are the frozen ones (taskG_analyse / P2_analyse):
  automaticity = _job returns bpm; None => quiescent
  EMQF         = paces under verapamil alone AND under ivabradine alone,
                 but fails the pair (per-model, paired)
  denominator  = models pacing drug-free at control
  interval     = Wilson 95%
  ceiling      = per-model eligibility: automatic under BOTH singles

Adds, per the P4 brief:
  * explicit interval-supported 5% and 10% classification at EVERY anchor x rung
  * exact paired McNemar between anchors, with effect sizes in pp
"""
import json
import os
import sys

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "08_taskP", "p4")
CKPT = os.path.join(DEST, "P4_pair_checkpoint.jsonl")
NPZ = os.path.join(ROOT, "zhou_san_run_p4",
                   "population_retained_20260824T232853Z.npz")

VER_BAND = [0.108, 0.14, 0.15, 0.2, 0.25, 0.275, 0.3]
ANCHORS = [("Doesch 2007 (PRIMARY)", 0.584), ("10-year cohort", 0.509),
           ("36-month (superseded)", 0.312)]
P2_REF = {"Doesch 2007 (PRIMARY)": 11.28, "10-year cohort": 10.02,
          "36-month (superseded)": 5.74}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


P = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    P[(r["model"], round(r["b_cal"], 6), round(r["b_f"], 6))] = \
        r["bpm"] is not None

models = [int(i) for i in np.load(NPZ, allow_pickle=True)["model_index"]]
need = [(bc, bf) for bc in [0.0] + VER_BAND
        for bf in [0.0] + [a[1] for a in ANCHORS]]
complete = [m for m in models if all((m, bc, bf) in P for bc, bf in need)]
print(f"complete 32-condition models: {len(complete)} / {len(models)}")
if len(complete) < len(models):
    print(f"  INCOMPLETE - {len(models)-len(complete)} models unfinished")
    sys.exit(0)

free = [m for m in complete if P[(m, 0.0, 0.0)]]
N = len(free)
print(f"denominator (drug-free pacing at control): {N} / {len(complete)}")

out = {"population_file": os.path.basename(NPZ), "seed": 788156539,
       "n_retained": len(models), "denominator": N, "state": "control",
       "ver_band_rungs": VER_BAND,
       "anchors": [{"anchor": a, "b_f_1x": b} for a, b in ANCHORS],
       "P2_comparison_only": P2_REF, "rows": []}


def emqf_set(bc, bf):
    return {m for m in free
            if P[(m, bc, 0.0)] and P[(m, 0.0, bf)] and not P[(m, bc, bf)]}


print()
print("=" * 122)
print("P4 RUNG-LEVEL RESULTS (control, ivabradine 1x)  + interval-supported "
      "5%/10% classification")
print("=" * 122)
print(f"{'anchor':22s} {'bCaL':>6s} {'bIf':>6s} | {'VerA':>11s} {'IvabA':>11s} "
      f"{'Combo':>11s} | {'k':>5s} {'EMQF%':>7s} {'95% CI':>16s} | "
      f"{'elig':>5s} {'max%':>6s} {'o/m':>6s} | {'>5 pt':>5s} {'>5 CI':>5s} "
      f"{'>10 pt':>6s} {'>10 CI':>6s}")
print("-" * 122)
for aname, bf in ANCHORS:
    ivab_q = sum(1 for m in free if not P[(m, 0.0, bf)])
    for bc in VER_BAND:
        ver_q = sum(1 for m in free if not P[(m, bc, 0.0)])
        comb_q = sum(1 for m in free if not P[(m, bc, bf)])
        k = len(emqf_set(bc, bf))
        elig = sum(1 for m in free if P[(m, bc, 0.0)] and P[(m, 0.0, bf)])
        lo, hi = wilson(k, N)
        e = k / N
        row = {"anchor": aname, "b_cal": bc, "b_f": bf,
               "ver_alone_k": ver_q, "ver_alone_frac": ver_q / N,
               "ivab_alone_k": ivab_q, "ivab_alone_frac": ivab_q / N,
               "combo_k": comb_q, "combo_frac": comb_q / N,
               "EMQF_k": k, "EMQF_n": N, "EMQF": e, "EMQF_ci95": [float(lo), float(hi)],
               "eligible_k": elig, "eligible_frac": elig / N,
               "max_possible_EMQF": elig / N,
               "obs_over_max": e / (elig / N) if elig else None,
               "point_gt_5pct": bool(e > 0.05),
               "ci_lower_gt_5pct": bool(lo > 0.05),
               "point_gt_10pct": bool(e > 0.10),
               "ci_lower_gt_10pct": bool(lo > 0.10)}
        out["rows"].append(row)
        print(f"{aname:22s} {bc:6.3f} {bf:6.4f} | {ver_q:4d} {ver_q/N:6.1%} "
              f"{ivab_q:4d} {ivab_q/N:6.1%} {comb_q:4d} {comb_q/N:6.1%} | "
              f"{k:5d} {e:7.2%} [{lo:6.2%},{hi:6.2%}] | {elig:5d} "
              f"{elig/N:6.1%} {e/(elig/N) if elig else float('nan'):6.3f} | "
              f"{'YES' if row['point_gt_5pct'] else 'no':>5s} "
              f"{'YES' if row['ci_lower_gt_5pct'] else 'no':>5s} "
              f"{'YES' if row['point_gt_10pct'] else 'no':>6s} "
              f"{'YES' if row['ci_lower_gt_10pct'] else 'no':>6s}")
    print("-" * 122)

print()
print("=" * 78)
print("MAXIMUM EMQF WITHIN THE 480 mg/day BAND (simulated frozen rungs only)")
print("=" * 78)
out["maxima"] = []
for aname, bf in ANCHORS:
    rows = [r for r in out["rows"] if r["anchor"] == aname]
    best = max(rows, key=lambda r: r["EMQF"])
    m = {"anchor": aname, "b_f_1x": bf, "max_EMQF": best["EMQF"],
         "at_rung": best["b_cal"], "EMQF_k": best["EMQF_k"],
         "EMQF_n": best["EMQF_n"], "EMQF_ci95": best["EMQF_ci95"],
         "eligible_k": best["eligible_k"],
         "eligible_frac": best["eligible_frac"],
         "max_possible_EMQF": best["max_possible_EMQF"],
         "obs_over_max": best["obs_over_max"],
         "crosses_5pct_with_interval_support": bool(best["ci_lower_gt_5pct"]),
         "crosses_10pct_with_interval_support": bool(best["ci_lower_gt_10pct"]),
         "point_gt_5pct": bool(best["point_gt_5pct"]),
         "point_gt_10pct": bool(best["point_gt_10pct"]),
         "P2_value_comparison_only": P2_REF[aname],
         "tied_rungs": [r["b_cal"] for r in rows
                        if r["EMQF_k"] == best["EMQF_k"]]}
    out["maxima"].append(m)
    print(f"  {aname:22s} max EMQF {best['EMQF']:6.2%} at rung "
          f"{best['b_cal']:.3f}  k={best['EMQF_k']}/{N}  "
          f"CI [{best['EMQF_ci95'][0]:.2%}, {best['EMQF_ci95'][1]:.2%}]")
    print(f"  {'':22s} ceiling {best['eligible_k']} ({best['eligible_frac']:.1%})"
          f"  obs/max {best['obs_over_max']:.3f}")
    print(f"  {'':22s} >5%: point {m['point_gt_5pct']}, INTERVAL-SUPPORTED "
          f"{m['crosses_5pct_with_interval_support']}")
    print(f"  {'':22s} >10%: point {m['point_gt_10pct']}, INTERVAL-SUPPORTED "
          f"{m['crosses_10pct_with_interval_support']}")
    print(f"  {'':22s} P2 comparison only: {P2_REF[aname]:.2f}%")
    if len(m["tied_rungs"]) > 1:
        print(f"  {'':22s} TIED maximum at rungs {m['tied_rungs']}")
    print()

# ---------------- paired McNemar ----------------------------------------
print("=" * 78)
print("PAIRED McNEMAR (same models; effect sizes in pp)")
print("=" * 78)
rungs = sorted({0.275} | {m["at_rung"] for m in out["maxima"]})
out["mcnemar"] = []
for bc in rungs:
    S = {a: emqf_set(bc, b) for a, b in ANCHORS}
    print(f"  rung b_CaL = {bc:.3f}")
    for i in range(len(ANCHORS)):
        for j in range(i + 1, len(ANCHORS)):
            a, b = ANCHORS[i][0], ANCHORS[j][0]
            n01, n10 = len(S[a] - S[b]), len(S[b] - S[a])
            p = (stats.binomtest(n01, n01 + n10, 0.5).pvalue
                 if n01 + n10 else 1.0)
            dpp = (len(S[a]) - len(S[b])) / N * 100
            out["mcnemar"].append({"rung": bc, "A": a, "B": b,
                                   "A_pos_B_neg": n01, "A_neg_B_pos": n10,
                                   "exact_p": p, "abs_diff_pp": dpp})
            print(f"    {a:22s} vs {b:22s}  {n01:4d}/{n10:4d}  "
                  f"p={p:.3e}  diff {dpp:+.2f} pp")
    print()

mx = {m["anchor"]: m["max_EMQF"] for m in out["maxima"]}
d_pri, d_sup = mx["Doesch 2007 (PRIMARY)"], mx["36-month (superseded)"]
out["separation"] = {
    "max_EMQF_by_anchor": mx,
    "ordering_preserved": bool(mx["Doesch 2007 (PRIMARY)"] >= mx["10-year cohort"]
                              >= mx["36-month (superseded)"]),
    "absolute_pp": (d_pri - d_sup) * 100,
    "ratio": d_pri / d_sup if d_sup else None,
    "P2_absolute_pp": 11.28 - 5.74, "P2_ratio": 11.28 / 5.74}
print("=" * 78)
print("ANCHOR SEPARATION")
print("=" * 78)
for a, _ in ANCHORS:
    print(f"  {a:22s} {mx[a]:7.2%}   (P2 comparison {P2_REF[a]:.2f}%)")
print(f"  ordering preserved: {out['separation']['ordering_preserved']}")
print(f"  absolute primary-superseded: {out['separation']['absolute_pp']:+.2f} pp"
      f"   (P2 {out['separation']['P2_absolute_pp']:+.2f} pp)")
print(f"  ratio primary/superseded  : {out['separation']['ratio']:.2f}x"
      f"   (P2 {out['separation']['P2_ratio']:.2f}x)")

with open(os.path.join(DEST, "P4_results.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\n-> 08_taskP/p4/P4_results.json")
