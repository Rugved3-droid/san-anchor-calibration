"""P3 pre-grid characterisation of the committed 500-model subset.

Run BEFORE any dense-grid simulation. Uses only data that already exists:
the P1 retained population and the P1 frozen threshold sweeps.

STATISTICAL NOTE. The 500 are a SUBSET of the 1028, so a two-sample test
between them compares nested samples and its p-value is not interpretable.
The valid disjoint contrast is

    subset (500)   vs   complement (528)

and that is what is tested. Subset-vs-full is reported descriptively only.
Bounded differences throughout; non-significance is never read as equivalence.
"""
import json
import os

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
SUB = os.path.join(ROOT, "08_taskP", "P3_subset_500.json")
TH = os.path.join(ROOT, "08_taskP", "threshold")
DEST = os.path.join(ROOT, "08_taskP")


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


subset = set(json.load(open(SUB, encoding="utf-8")))
z = np.load(NPZ, allow_pickle=True)
idx = np.array([int(i) for i in z["model_index"]])
in_sub = np.array([i in subset for i in idx])
out = {"subset_n": int(in_sub.sum()), "complement_n": int((~in_sub).sum()),
       "full_n": int(idx.size)}
print(f"subset {out['subset_n']}  complement {out['complement_n']}  "
      f"full {out['full_n']}")


def desc(x):
    q = np.percentile(x, [0, 5, 25, 50, 75, 95, 100])
    return {"n": int(x.size), "mean": float(x.mean()),
            "sd": float(x.std(ddof=1)), "min": float(q[0]), "p5": float(q[1]),
            "q1": float(q[2]), "median": float(q[3]), "q3": float(q[4]),
            "p95": float(q[5]), "max": float(q[6])}


print()
print("=" * 78)
print("1. INTRINSIC RATE")
print("=" * 78)
cl, bpm = z["CL_ms"], 60000.0 / z["CL_ms"]
for nm, arr in (("CL_ms", cl), ("bpm", bpm)):
    a, b, f = arr[in_sub], arr[~in_sub], arr
    da, db, df = desc(a), desc(b), desc(f)
    out[f"{nm}_subset"], out[f"{nm}_complement"], out[f"{nm}_full"] = da, db, df
    print(f"\n  {nm}")
    for lbl, d in (("subset 500", da), ("complement 528", db),
                   ("full 1028 (descriptive)", df)):
        print(f"    {lbl:24s} median {d['median']:8.3f}  IQR "
              f"{d['q1']:8.3f}-{d['q3']:8.3f}  range {d['min']:8.3f}-"
              f"{d['max']:8.3f}  mean {d['mean']:8.3f} SD {d['sd']:7.3f}")
    ks = stats.ks_2samp(a, b)
    mw = stats.mannwhitneyu(a, b, alternative="two-sided")
    rng = np.random.default_rng(95429097)
    boot = np.array([np.median(rng.choice(a, a.size)) -
                     np.median(rng.choice(b, b.size)) for _ in range(10000)])
    ci = np.percentile(boot, [2.5, 97.5])
    out[f"{nm}_disjoint_test"] = {
        "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
        "mw_p": float(mw.pvalue),
        "median_diff_subset_minus_complement": float(np.median(a)-np.median(b)),
        "median_diff_ci95": [float(ci[0]), float(ci[1])]}
    print(f"    DISJOINT subset vs complement: KS D={ks.statistic:.4f} "
          f"p={ks.pvalue:.4f}   MW p={mw.pvalue:.4f}")
    print(f"      median difference {np.median(a)-np.median(b):+.3f}  "
          f"95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print(f"      subset - full (descriptive): "
          f"{da['median']-df['median']:+.3f}")

print()
print("=" * 78)
print("2. FIXED-BLOCK QUIESCENCE CURVES (frozen 5% ladder)")
print("=" * 78)
for cur, nice in (("G_CaL", "I_CaL"), ("G_f", "I_f")):
    p = os.path.join(TH, f"taskP_{cur}_population_sweep.json")
    recs = [r for r in json.load(open(p, encoding="utf-8"))["records"]
            if r["status"] == "ok"]
    grid = sorted(float(k) for k in recs[0]["levels"])
    sub = [r for r in recs if r["index"] in subset]
    comp = [r for r in recs if r["index"] not in subset]
    full = recs

    def cen(rs):
        return sum(1 for r in rs if r["threshold"] is None)

    def med(rs):
        u = [r["threshold"] for r in rs if r["threshold"] is not None]
        return float(np.median(u)) if u else None

    print(f"\n  {nice}")
    print(f"    {'group':16s} {'n':>5s} {'censored@90%':>13s} "
          f"{'cond. median':>13s}")
    for lbl, rs in (("subset 500", sub), ("complement 528", comp),
                    ("full 1028", full)):
        print(f"    {lbl:16s} {len(rs):5d} {cen(rs):6d} "
              f"({cen(rs)/len(rs):5.1%}) {str(med(rs)):>13s}")
    rows, worst = [], 0.0
    print(f"\n    {'block':>6} {'sub %':>7} {'sub 95% CI':>16} "
          f"{'full %':>7} {'full 95% CI':>16} {'diff pp':>8} {'overlap':>8}")
    for g in grid:
        ks_ = sum(1 for r in sub if r["levels"].get(str(g), "M") is None)
        kf = sum(1 for r in full if r["levels"].get(str(g), "M") is None)
        ls, hs = wilson(ks_, len(sub))
        lf, hf = wilson(kf, len(full))
        d = (ks_/len(sub) - kf/len(full)) * 100
        ov = not (hs < lf or hf < ls)
        worst = max(worst, abs(d))
        rows.append({"block": g, "sub_k": ks_, "sub_frac": ks_/len(sub),
                     "sub_wilson95": [ls, hs], "full_k": kf,
                     "full_frac": kf/len(full), "full_wilson95": [lf, hf],
                     "diff_pp": d, "wilson_overlap": ov})
        print(f"    {g:6.2f} {ks_/len(sub)*100:7.2f} "
              f"[{ls*100:6.2f},{hs*100:6.2f}] {kf/len(full)*100:7.2f} "
              f"[{lf*100:6.2f},{hf*100:6.2f}] {d:+8.2f} {str(ov):>8}")
    print(f"\n    LARGEST |subset - full| across the ladder: {worst:.2f} pp")
    out[f"{cur}_curve"] = {
        "grid": grid, "rows": rows, "max_abs_diff_pp": worst,
        "subset": {"n": len(sub), "censored": cen(sub),
                   "censored_frac": cen(sub)/len(sub),
                   "cond_median": med(sub)},
        "complement": {"n": len(comp), "censored": cen(comp),
                       "censored_frac": cen(comp)/len(comp),
                       "cond_median": med(comp)},
        "full": {"n": len(full), "censored": cen(full),
                 "censored_frac": cen(full)/len(full),
                 "cond_median": med(full)}}

with open(os.path.join(DEST, "P3_subset_characterisation.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\n-> 08_taskP/P3_subset_characterisation.json")
