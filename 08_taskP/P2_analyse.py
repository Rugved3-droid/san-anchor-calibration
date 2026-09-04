"""P2 analysis - EMQF, single-agent quiescence, and ceiling headroom.

ENDPOINT DEFINITIONS ARE THE FROZEN ONES (04_pharmacology/taskG_analyse.py):

  automaticity      _job returns bpm; bpm is None  <=>  quiescent.
  EMQF (EAR_paired) fraction of models that PACE under verapamil alone AND
                    PACE under ivabradine alone but FAIL under the pair.
                    Per-model and paired.
  EAR_marginal      P_AB - max(P_A, P_B).
  rescue            fraction failing a single but pacing under the pair.
  denominator       models that pace DRUG-FREE in that state.
  interval          Wilson 95%.

CEILING (P2 requirement): N_eligible = number of models automatic under
verapamil alone AND automatic under ivabradine alone, evaluated PER MODEL at
that exact (rung, anchor) pair - not reconstructed from marginal percentages.
Max possible EMQF = N_eligible / denominator.

Nothing is fitted, interpolated, or refined. Maxima are taken over simulated
frozen rungs only.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "04_pharmacology"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

DEST = os.path.join(ROOT, "08_taskP", "p2")
CKPT = os.path.join(DEST, "P2_checkpoint.jsonl")
NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
MAN = os.path.join(ROOT, "zhou_san_run",
                   "population_manifest_20260823T094616Z.json")

VER_BAND = [0.108, 0.14, 0.15, 0.2, 0.25, 0.275, 0.3]
ANCHORS = [("Doesch 2007 (PRIMARY)", 0.584), ("10-year cohort", 0.509),
           ("36-month (superseded)", 0.312)]
HISTORICAL = {"Doesch 2007 (PRIMARY)": 16.0, "10-year cohort": 12.8,
              "36-month (superseded)": 6.9}


def wilson(k, n, z=1.96):
    """Frozen Wilson interval, identical to taskG_analyse.wilson."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


man = json.load(open(MAN, encoding="utf-8"))
zz = np.load(NPZ, allow_pickle=True)
models = [int(i) for i in zz["model_index"]]

paces = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    paces[(r["model"], round(r["b_cal"], 6), round(r["b_f"], 6))] = \
        r["bpm"] is not None

need = [(bc, bf) for bc in [0.0] + VER_BAND for bf in [0.0] + [a[1] for a in ANCHORS]]
complete = [m for m in models if all((m, bc, bf) in paces for bc, bf in need)]
print(f"models with a COMPLETE 32-condition set : {len(complete)} / {len(models)}")
if len(complete) < len(models):
    print(f"  P2 IS INCOMPLETE - {len(models)-len(complete)} models unfinished")

# ---- denominator: models pacing drug-free at control ---------------------
free_pacing = [m for m in complete if paces[(m, 0.0, 0.0)]]
N = len(free_pacing)
print(f"drug-free pacing at control (denominator): {N} / {len(complete)}")
if N < len(complete):
    print(f"  NOTE: {len(complete)-N} retained models do not pace drug-free at "
          f"the 300 s pre-pace used by the pair protocol; excluded from the "
          f"denominator per the frozen definition.")

out = {"population_file": os.path.basename(NPZ),
       "population_sha256": man["population_sha256"],
       "n_retained": man["n_retained"],
       "n_complete": len(complete), "denominator": N,
       "state": "control", "ver_band_rungs": VER_BAND,
       "anchors": [{"anchor": a, "b_f_1x": b} for a, b in ANCHORS],
       "historical_comparison_only": HISTORICAL, "rows": []}

print()
print("=" * 108)
print("RUNG-LEVEL RESULTS  (control, ivabradine 1x)")
print("=" * 108)
hdr = (f"{'anchor':22s} {'bCaL':>6s} {'bIf':>6s} | {'VerAlone':>13s} "
       f"{'IvabAlone':>13s} {'Combo':>13s} | {'EMQF k':>7s} {'EMQF %':>7s} "
       f"{'95% CI':>15s} | {'elig':>5s} {'maxEMQF%':>9s} {'obs/max':>8s}")
print(hdr)
print("-" * 108)

for aname, bf in ANCHORS:
    # ivabradine alone is the same condition at every rung; compute once
    ivab_q = [m for m in free_pacing if not paces[(m, 0.0, bf)]]
    for bc in VER_BAND:
        ver_q = [m for m in free_pacing if not paces[(m, bc, 0.0)]]
        comb_q = [m for m in free_pacing if not paces[(m, bc, bf)]]
        # paired EMQF: paces under BOTH singles, fails the pair
        k = sum(1 for m in free_pacing
                if paces[(m, bc, 0.0)] and paces[(m, 0.0, bf)]
                and not paces[(m, bc, bf)])
        # rescue: fails a single but paces under the pair
        resc = sum(1 for m in free_pacing
                   if (not paces[(m, bc, 0.0)] or not paces[(m, 0.0, bf)])
                   and paces[(m, bc, bf)])
        # ceiling: eligible = automatic under BOTH singles (per-model, paired)
        elig = sum(1 for m in free_pacing
                   if paces[(m, bc, 0.0)] and paces[(m, 0.0, bf)])
        pA, pB, pAB = len(ver_q)/N, len(ivab_q)/N, len(comb_q)/N
        lo, hi = wilson(k, N)
        max_emqf = elig / N
        row = {"anchor": aname, "b_cal": bc, "b_f": bf,
               "ver_alone_k": len(ver_q), "ver_alone_frac": pA,
               "ivab_alone_k": len(ivab_q), "ivab_alone_frac": pB,
               "combo_k": len(comb_q), "combo_frac": pAB,
               "EMQF_k": k, "EMQF_n": N, "EMQF": k/N,
               "EMQF_ci95": [lo, hi],
               "EAR_marginal": pAB - max(pA, pB),
               "rescue_k": resc, "rescue_frac": resc/N,
               "eligible_k": elig, "eligible_frac": elig/N,
               "max_possible_EMQF": max_emqf,
               "obs_over_max": (k/N)/max_emqf if max_emqf > 0 else None}
        out["rows"].append(row)
        print(f"{aname:22s} {bc:6.3f} {bf:6.4f} | "
              f"{len(ver_q):5d} {pA:6.1%} {len(ivab_q):5d} {pB:6.1%} "
              f"{len(comb_q):5d} {pAB:6.1%} | {k:7d} {k/N:7.2%} "
              f"[{lo:6.2%},{hi:6.2%}] | {elig:5d} {max_emqf:9.1%} "
              f"{(k/N)/max_emqf if max_emqf>0 else float('nan'):8.3f}")
    print("-" * 108)

print()
print("=" * 78)
print("MAXIMUM EMQF WITHIN THE 480 mg/day BAND (simulated frozen rungs only)")
print("=" * 78)
out["maxima"] = []
for aname, bf in ANCHORS:
    rows = [r for r in out["rows"] if r["anchor"] == aname]
    best = max(rows, key=lambda r: r["EMQF"])
    ties = [r["b_cal"] for r in rows if r["EMQF_k"] == best["EMQF_k"]]
    m = {"anchor": aname, "b_f_1x": bf, "max_EMQF": best["EMQF"],
         "at_rung": best["b_cal"], "tied_rungs": ties,
         "EMQF_k": best["EMQF_k"], "EMQF_n": best["EMQF_n"],
         "EMQF_ci95": best["EMQF_ci95"],
         "eligible_k": best["eligible_k"],
         "max_possible_EMQF": best["max_possible_EMQF"],
         "obs_over_max": best["obs_over_max"],
         "historical_188_pct": HISTORICAL[aname]}
    out["maxima"].append(m)
    print(f"  {aname:22s} max EMQF {best['EMQF']:6.2%} at b_CaL="
          f"{best['b_cal']:.3f}  k={best['EMQF_k']}/{best['EMQF_n']}  "
          f"95% CI [{best['EMQF_ci95'][0]:.2%}, {best['EMQF_ci95'][1]:.2%}]")
    print(f"  {'':22s} ceiling: eligible {best['eligible_k']} "
          f"({best['eligible_frac']:.1%}), max possible EMQF "
          f"{best['max_possible_EMQF']:.1%}, observed/max "
          f"{best['obs_over_max']:.3f}")
    print(f"  {'':22s} historical 188-model value (comparison only): "
          f"{HISTORICAL[aname]:.1f}%")
    if len(ties) > 1:
        print(f"  {'':22s} NOTE tied maximum at rungs {ties}")
    print()

# ---- anchor separation --------------------------------------------------
mx = {m["anchor"]: m["max_EMQF"] for m in out["maxima"]}
d_pri = mx["Doesch 2007 (PRIMARY)"]
d_sup = mx["36-month (superseded)"]
out["separation"] = {
    "max_EMQF_by_anchor": mx,
    "ordering_preserved_Doesch_gt_10yr_gt_36mo": (
        mx["Doesch 2007 (PRIMARY)"] >= mx["10-year cohort"] >=
        mx["36-month (superseded)"]),
    "absolute_separation_pp_primary_minus_superseded": (d_pri - d_sup) * 100,
    "relative_ratio_primary_over_superseded": (d_pri / d_sup
                                               if d_sup > 0 else None),
    "historical_absolute_pp": 16.0 - 6.9,
    "historical_ratio": 16.0 / 6.9}
print("=" * 78)
print("ANCHOR SEPARATION (maxima within band)")
print("=" * 78)
for a in ("Doesch 2007 (PRIMARY)", "10-year cohort", "36-month (superseded)"):
    print(f"  {a:22s} {mx[a]:7.2%}   (historical {HISTORICAL[a]:.1f}%)")
print(f"  ordering preserved: "
      f"{out['separation']['ordering_preserved_Doesch_gt_10yr_gt_36mo']}")
print(f"  absolute separation primary-superseded: "
      f"{out['separation']['absolute_separation_pp_primary_minus_superseded']:+.2f} pp"
      f"   (historical {out['separation']['historical_absolute_pp']:+.1f} pp)")
if out["separation"]["relative_ratio_primary_over_superseded"]:
    print(f"  relative ratio primary/superseded: "
          f"{out['separation']['relative_ratio_primary_over_superseded']:.2f}x"
          f"   (historical {out['separation']['historical_ratio']:.2f}x)")

with open(os.path.join(DEST, "P2_results.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"\n-> 08_taskP/p2/P2_results.json")
