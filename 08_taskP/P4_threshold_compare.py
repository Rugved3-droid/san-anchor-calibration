"""P1 vs P4 threshold geometry - bounded differences across the whole curve.

P1 and P4 are INDEPENDENT populations (different seeds), so unlike the P1
internal comparison these are two independent samples. The primary quantities,
per the brief, are the fixed-block quiescent-fraction curve and the censoring
fraction - not the conditional median.

Reports, per current:
  * full quiescent-fraction curve with Wilson 95% at every frozen level;
  * the LARGEST absolute percentage-point difference between the P1 and P4
    curves across all frozen block levels, and where it occurs;
  * median/IQR/range only to the 5%-grid resolution;
  * censoring fraction and fraction still pacing at 90% block;
  * conditional summaries flagged as censored where they are.
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P1 = os.path.join(ROOT, "08_taskP", "threshold")
P4 = os.path.join(ROOT, "08_taskP", "p4_threshold")
DEST = os.path.join(ROOT, "08_taskP")
TOP = 0.90


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def curve(recs, grid):
    n = len(recs)
    out = []
    for g in grid:
        k = sum(1 for r in recs if r["levels"].get(str(g), "M") is None)
        lo, hi = wilson(k, n)
        out.append({"block": g, "k": k, "n": n, "frac": k / n,
                    "wilson95": [lo, hi]})
    return out


def summarise(recs, label):
    n = len(recs)
    thr = [r["threshold"] for r in recs]
    unc = np.array([t for t in thr if t is not None], float)
    ncen = sum(1 for t in thr if t is None)
    d = {"label": label, "n": n,
         "n_censored_at_0.90": ncen, "censored_fraction": ncen / n,
         "still_pacing_at_90pct": ncen, "still_pacing_frac": ncen / n,
         "n_non_monotone": sum(1 for r in recs if not r["monotone_ok"]),
         "n_uncensored": int(unc.size)}
    if unc.size:
        d.update({
            "cond_median": float(np.median(unc)),
            "cond_iqr": [float(np.percentile(unc, 25)),
                         float(np.percentile(unc, 75))],
            "cond_range": [float(unc.min()), float(unc.max())]})
    else:
        d.update({"cond_median": None, "cond_iqr": None, "cond_range": None})
    return d


report = {}
for cur in ("G_CaL", "G_f"):
    p1p = os.path.join(P1, f"taskP_{cur}_population_sweep.json")
    p4p = os.path.join(P4, f"P4_{cur}_population_sweep.json")
    if not (os.path.exists(p1p) and os.path.exists(p4p)):
        print(f"{cur}: sweep missing (P1 {os.path.exists(p1p)}, "
              f"P4 {os.path.exists(p4p)}) - skipping")
        report[cur] = {"status": "incomplete"}
        continue
    r1 = [r for r in json.load(open(p1p, encoding="utf-8"))["records"]
          if r["status"] == "ok"]
    r4 = [r for r in json.load(open(p4p, encoding="utf-8"))["records"]
          if r["status"] == "ok"]
    grid = sorted(float(k) for k in r1[0]["levels"])
    c1, c4 = curve(r1, grid), curve(r4, grid)
    diffs = [{"block": a["block"],
              "p1_frac": a["frac"], "p1_wilson95": a["wilson95"],
              "p4_frac": b["frac"], "p4_wilson95": b["wilson95"],
              "diff_pp": (a["frac"] - b["frac"]) * 100,
              "wilson_overlap": not (a["wilson95"][1] < b["wilson95"][0]
                                     or b["wilson95"][1] < a["wilson95"][0])}
             for a, b in zip(c1, c4)]
    worst = max(diffs, key=lambda r: abs(r["diff_pp"]))
    report[cur] = {
        "P1": summarise(r1, "P1 (1028)"), "P4": summarise(r4, "P4 (1044)"),
        "grid": grid, "per_level": diffs,
        "max_abs_diff_pp": abs(worst["diff_pp"]),
        "max_abs_diff_at_block": worst["block"],
        "n_levels_with_overlapping_wilson": sum(1 for d in diffs
                                                if d["wilson_overlap"]),
        "n_levels": len(diffs)}

    print("=" * 96)
    print(f"{cur}")
    print("=" * 96)
    for s in (report[cur]["P1"], report[cur]["P4"]):
        print(f"  {s['label']:12s} n={s['n']:5d}  censored@90%={s['n_censored_at_0.90']:5d}"
              f" ({s['censored_fraction']:6.1%})  uncensored={s['n_uncensored']:4d}"
              f"  non-monotone={s['n_non_monotone']}")
        print(f"      conditional median {s['cond_median']}  IQR {s['cond_iqr']}"
              f"  range {s['cond_range']}")
    print(f"\n  {'block':>6} {'P1 %':>7} {'P1 95% CI':>16} {'P4 %':>7} "
          f"{'P4 95% CI':>16} {'diff pp':>8} {'CI overlap':>11}")
    for d in diffs:
        print(f"  {d['block']:6.2f} {d['p1_frac']*100:7.2f} "
              f"[{d['p1_wilson95'][0]*100:6.2f},{d['p1_wilson95'][1]*100:6.2f}] "
              f"{d['p4_frac']*100:7.2f} "
              f"[{d['p4_wilson95'][0]*100:6.2f},{d['p4_wilson95'][1]*100:6.2f}] "
              f"{d['diff_pp']:+8.2f} {str(d['wilson_overlap']):>11}")
    print(f"\n  LARGEST |P1-P4| difference across the frozen ladder: "
          f"{report[cur]['max_abs_diff_pp']:.2f} pp at block "
          f"{report[cur]['max_abs_diff_at_block']:.2f}")
    print(f"  Wilson intervals overlap at "
          f"{report[cur]['n_levels_with_overlapping_wilson']}/"
          f"{report[cur]['n_levels']} levels")
    print()

with open(os.path.join(DEST, "P4_threshold_comparison.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print("-> 08_taskP/P4_threshold_comparison.json")
