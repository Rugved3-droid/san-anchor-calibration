"""P1 representativeness: historical 188 vs the completed 1028-model population.

Intrinsic rate here; thresholds are added by P1_threshold_report.py once the
sweeps finish.

STATISTICAL NOTE, stated up front because it governs every test below.
The 188 are a SUBSET of the 1028 (verified: they are exactly the retained
members of indices 0-939). A two-sample test between 188 and 1028 compares
nested samples and its p-value is not interpretable. The valid comparison for
representativeness is:

        188 (retained among 0-939)   vs   840 (retained among 940-4999)

which are DISJOINT. That is the primary comparison. The 188-vs-1028 contrast is
reported only descriptively, never as a test.

Read-only except for its own outputs.
"""
import json
import os

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
DEST = os.path.join(ROOT, "08_taskP")

z = np.load(NPZ, allow_pickle=True)
idx = z["model_index"]
cl = z["CL_ms"]
bpm = 60000.0 / cl

hist_mask = idx < 940
new_mask = ~hist_mask
out = {"population_file": os.path.basename(NPZ),
       "n_total": int(idx.size),
       "n_historical_188": int(hist_mask.sum()),
       "n_new_840": int(new_mask.sum())}

print("=" * 74)
print("INTRINSIC RATE — historical 188 vs new 840 vs pooled 1028")
print("=" * 74)
print(f"  n: historical={hist_mask.sum()}  new={new_mask.sum()}  "
       f"pooled={idx.size}")
print("\n  NOTE: retention forces CL into [600, 1000] ms, i.e. bpm into")
print("  [60.0, 100.0]. Both groups are truncated to the same interval by")
print("  construction, so location differences can only arise from the shape")
print("  of the distribution inside it.")


def desc(x, label):
    q = np.percentile(x, [0, 5, 25, 50, 75, 95, 100])
    d = {"n": int(x.size), "mean": float(x.mean()), "sd": float(x.std(ddof=1)),
         "min": float(q[0]), "p5": float(q[1]), "q1": float(q[2]),
         "median": float(q[3]), "q3": float(q[4]), "p95": float(q[5]),
         "max": float(q[6]), "iqr": float(q[4] - q[2])}
    print(f"\n  {label}")
    print(f"    median {d['median']:8.3f}   IQR {d['q1']:.3f}-{d['q3']:.3f} "
          f"(width {d['iqr']:.3f})")
    print(f"    mean   {d['mean']:8.3f}   SD  {d['sd']:.3f}")
    print(f"    range  {d['min']:.3f} - {d['max']:.3f}   "
          f"5th-95th {d['p5']:.3f}-{d['p95']:.3f}")
    return d


for name, arr in (("CL_ms", cl), ("bpm", bpm)):
    print(f"\n{'-'*74}\n  {name}\n{'-'*74}")
    a, b, p = arr[hist_mask], arr[new_mask], arr
    out[f"{name}_historical"] = desc(a, "historical 188")
    out[f"{name}_new"] = desc(b, "new 840")
    out[f"{name}_pooled"] = desc(p, "pooled 1028 (descriptive only)")

    # ---- disjoint comparison: 188 vs 840 -------------------------------
    ks = stats.ks_2samp(a, b)
    mw = stats.mannwhitneyu(a, b, alternative="two-sided")
    # Hodges-Lehmann shift + distribution-free 95% CI via bootstrap
    rng = np.random.default_rng(20260816)
    boot = np.array([np.median(rng.choice(a, a.size)) -
                     np.median(rng.choice(b, b.size)) for _ in range(10000)])
    ci = np.percentile(boot, [2.5, 97.5])
    ci90 = np.percentile(boot, [5, 95])
    d = {"ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
         "mw_u": float(mw.statistic), "mw_p": float(mw.pvalue),
         "median_diff_hist_minus_new": float(np.median(a) - np.median(b)),
         "median_diff_ci95": [float(ci[0]), float(ci[1])],
         "median_diff_ci90": [float(ci90[0]), float(ci90[1])],
         "cohens_d": float((a.mean() - b.mean()) /
                           np.sqrt(((a.size-1)*a.var(ddof=1) +
                                    (b.size-1)*b.var(ddof=1)) /
                                   (a.size + b.size - 2)))}
    out[f"{name}_test_188_vs_840"] = d
    print(f"\n  DISJOINT TEST  188 vs 840")
    print(f"    Kolmogorov-Smirnov D = {d['ks_stat']:.4f}   p = {d['ks_p']:.4f}")
    print(f"    Mann-Whitney U       = {d['mw_u']:.0f}   p = {d['mw_p']:.4f}")
    print(f"    median difference    = {d['median_diff_hist_minus_new']:+.3f}")
    print(f"      95% CI  [{ci[0]:+.3f}, {ci[1]:+.3f}]")
    print(f"      90% CI  [{ci90[0]:+.3f}, {ci90[1]:+.3f}]")
    print(f"    Cohen's d            = {d['cohens_d']:+.4f}")

# ---- conductance-space check: are the 12 scale factors comparable? -------
print()
print("=" * 74)
print("PARAMETER-SPACE COMPARISON (12 conductance scale factors)")
print("=" * 74)
names = [str(v) for v in z["names"]]
sc = z["scales"]
rows = []
for j, nm in enumerate(names):
    a, b = sc[hist_mask, j], sc[new_mask, j]
    ks = stats.ks_2samp(a, b)
    rows.append({"parameter": nm, "hist_median": float(np.median(a)),
                 "new_median": float(np.median(b)),
                 "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue)})
    print(f"  {nm:8s} median hist {np.median(a):.4f}  new {np.median(b):.4f}"
          f"   KS D={ks.statistic:.4f}  p={ks.pvalue:.4f}")
out["parameter_space"] = rows
nsig = sum(1 for r in rows if r["ks_p"] < 0.05)
out["n_parameters_ks_p_lt_0.05"] = nsig
print(f"\n  parameters with KS p < 0.05 (uncorrected): {nsig}/12")
print(f"  Bonferroni threshold at 12 tests: p < {0.05/12:.5f}")

with open(os.path.join(DEST, "P1_rate_comparison.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"\n-> 08_taskP/P1_rate_comparison.json")
