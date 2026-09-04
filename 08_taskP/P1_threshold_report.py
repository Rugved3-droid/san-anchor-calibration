"""P1 threshold-geometry comparison: historical 188 vs new 840 vs pooled 1028.

Consumes the sweeps written by P1_threshold_sweep.py (which reuses the frozen
definitions from 04_pharmacology/population_block_sweep.py verbatim).

Censoring is handled explicitly. A model that still paces at the top block
level (0.90) has NO threshold in the observed range - it is RIGHT-CENSORED at
0.90, not "threshold = 0.90". For I_CaL censoring was nil historically; for
I_f it was 176/188, so the I_f threshold distribution is mostly censored and
its median is conditional on the minority that stop. Accordingly:

  * quantiles are reported BOTH conditionally (uncensored only) and via
    Kaplan-Meier on the full group, which is the estimator that uses the
    censored models correctly;
  * the group comparison is a LOG-RANK test on right-censored data, not a
    rank test on the uncensored subset;
  * the primary display is the quiescent-fraction-vs-block curve with Wilson
    intervals, which is censoring-free by construction and is the quantity
    the prespecified Figure 2 already plots.

Generates figure P1_threshold_geometry.png/.pdf (Figure 2 layout, overlaid).
"""
import json
import os

import numpy as np
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TH = os.path.join(ROOT, "08_taskP", "threshold")
DEST = os.path.join(ROOT, "08_taskP")
TOP = 0.90

import matplotlib                                                   # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                     # noqa: E402

BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#1b1f24", "#454c54", "#8a929b"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2,
                     "axes.grid": True, "grid.color": "#e6e9ec",
                     "grid.linewidth": 0.7, "figure.dpi": 200,
                     "savefig.dpi": 400, "axes.spines.top": False,
                     "axes.spines.right": False})


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def km(times, events, grid):
    """Kaplan-Meier survival (= fraction still pacing) on a discrete grid."""
    s, out = 1.0, []
    for g in grid:
        at_risk = np.sum(times >= g - 1e-12)
        died = np.sum((np.abs(times - g) < 1e-12) & events)
        if at_risk > 0 and died > 0:
            s *= (1 - died / at_risk)
        out.append(s)
    return np.array(out)


def logrank(t1, e1, t2, e2):
    """Two-group log-rank test with right-censoring."""
    t = np.concatenate([t1, t2])
    e = np.concatenate([e1, e2])
    g = np.concatenate([np.zeros(t1.size), np.ones(t2.size)])
    O1 = E1 = V = 0.0
    for u in np.unique(t[e]):
        at = t >= u - 1e-12
        n, n1 = at.sum(), (at & (g == 0)).sum()
        d = ((np.abs(t - u) < 1e-12) & e).sum()
        d1 = ((np.abs(t - u) < 1e-12) & e & (g == 0)).sum()
        if n > 1 and d > 0:
            O1 += d1
            E1 += d * n1 / n
            V += d * (n1 / n) * (1 - n1 / n) * (n - d) / (n - 1)
    chi2 = (O1 - E1) ** 2 / V if V > 0 else 0.0
    return {"observed_g1": float(O1), "expected_g1": float(E1),
            "chi2": float(chi2), "p": float(stats.chi2.sf(chi2, 1))}


def quant(x, qs=(0, 5, 25, 50, 75, 95, 100)):
    if len(x) == 0:
        return {f"p{q}": None for q in qs}
    v = np.percentile(x, qs)
    return {f"p{q}": float(vv) for q, vv in zip(qs, v)}


report = {}
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))

for ax, cur, nice, tag in ((axes[0], "G_CaL", r"$I_{CaL}$ block", "A"),
                           (axes[1], "G_f", r"$I_f$ block", "B")):
    p = os.path.join(TH, f"taskP_{cur}_population_sweep.json")
    if not os.path.exists(p):
        print(f"MISSING {p} - sweep not finished; skipping {cur}")
        report[cur] = {"status": "sweep_not_finished"}
        continue
    blob = json.load(open(p, encoding="utf-8"))
    recs = [r for r in blob["records"] if r["status"] == "ok"]
    grid = sorted(float(k) for k in recs[0]["levels"])

    hist = [r for r in recs if r["index"] < 940]
    new = [r for r in recs if r["index"] >= 940]
    groups = {"historical_188": hist, "new_840": new, "pooled_1028": recs}

    d = {"n_records": len(recs), "grid": grid,
         "definitions_source": blob["definitions_source"],
         "prepace_s": blob["prepace_s"], "blocks": blob["blocks"]}

    for gname, G in groups.items():
        n = len(G)
        thr = [r["threshold"] for r in G]
        unc = np.array([t for t in thr if t is not None], float)
        ncen = sum(1 for t in thr if t is None)
        # survival encoding: event = reached quiescence
        times = np.array([t if t is not None else TOP for t in thr], float)
        events = np.array([t is not None for t in thr], bool)
        surv = km(times, events, grid)
        # quiescent fraction directly from the ladder (censoring-free)
        qf, qci = [], []
        for g in grid:
            k = sum(1 for r in G if r["levels"].get(str(g), "MISSING") is None)
            qf.append(k / n)
            qci.append(wilson(k, n))
        d[gname] = {
            "n": n, "n_censored_at_0.90": int(ncen),
            "censored_fraction": ncen / n,
            "n_non_monotone": sum(1 for r in G if not r["monotone_ok"]),
            "threshold_conditional_quantiles": quant(unc),
            "threshold_conditional_median": (float(np.median(unc))
                                             if unc.size else None),
            "threshold_conditional_iqr": (
                [float(np.percentile(unc, 25)),
                 float(np.percentile(unc, 75))] if unc.size else None),
            "km_median": (float(min([g for g, s in zip(grid, surv)
                                     if s <= 0.5], default=float("nan")))
                          if (surv <= 0.5).any() else None),
            "km_survival": [float(s) for s in surv],
            "quiescent_fraction": qf,
            "quiescent_fraction_wilson95": [[float(a), float(b)]
                                            for a, b in qci]}

    # ---- disjoint comparison 188 vs 840 --------------------------------
    def surv_arrays(G):
        thr = [r["threshold"] for r in G]
        return (np.array([t if t is not None else TOP for t in thr], float),
                np.array([t is not None for t in thr], bool))

    t1, e1 = surv_arrays(hist)
    t2, e2 = surv_arrays(new)
    lr = logrank(t1, e1, t2, e2)
    u1 = t1[e1]
    u2 = t2[e2]
    cmp_ = {"logrank": lr,
            "n_hist": len(hist), "n_new": len(new),
            "censored_hist": int((~e1).sum()), "censored_new": int((~e2).sum())}
    if u1.size and u2.size:
        ks = stats.ks_2samp(u1, u2)
        mw = stats.mannwhitneyu(u1, u2, alternative="two-sided")
        rng = np.random.default_rng(20260816)
        boot = np.array([np.median(rng.choice(u1, u1.size)) -
                         np.median(rng.choice(u2, u2.size))
                         for _ in range(10000)])
        cmp_["uncensored_only"] = {
            "note": ("conditional on reaching quiescence; ignores censored "
                     "models, so it is NOT a test of the full distribution"),
            "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
            "mw_p": float(mw.pvalue),
            "median_diff_hist_minus_new": float(np.median(u1)-np.median(u2)),
            "median_diff_ci95": [float(np.percentile(boot, 2.5)),
                                 float(np.percentile(boot, 97.5))]}
    # per-level quiescent-fraction difference with Wilson CIs on each arm
    lv = []
    for g in grid:
        k1 = sum(1 for r in hist if r["levels"].get(str(g), "M") is None)
        k2 = sum(1 for r in new if r["levels"].get(str(g), "M") is None)
        lv.append({"block": g,
                   "hist_k": k1, "hist_n": len(hist),
                   "hist_frac": k1/len(hist),
                   "hist_wilson95": list(wilson(k1, len(hist))),
                   "new_k": k2, "new_n": len(new), "new_frac": k2/len(new),
                   "new_wilson95": list(wilson(k2, len(new))),
                   "diff_pp": (k1/len(hist) - k2/len(new)) * 100})
    cmp_["per_level"] = lv
    cmp_["max_abs_level_diff_pp"] = float(max(abs(r["diff_pp"]) for r in lv))
    d["comparison_188_vs_840"] = cmp_
    report[cur] = d

    # ---------------- plot: prespecified Figure 2 layout, overlaid ------
    x = [g * 100 for g in grid]
    for gname, colour, lbl in (("historical_188", ORANGE, "historical 188"),
                               ("new_840", BLUE, "new 840"),
                               ("pooled_1028", INK, "pooled 1028")):
        gg = d[gname]
        y = [f * 100 for f in gg["quiescent_fraction"]]
        lo = [c[0] * 100 for c in gg["quiescent_fraction_wilson95"]]
        hi = [c[1] * 100 for c in gg["quiescent_fraction_wilson95"]]
        if gname != "pooled_1028":
            ax.fill_between(x, lo, hi, color=colour, alpha=0.13, lw=0,
                            zorder=2)
        ax.plot(x, y, color=colour, lw=1.6 if gname != "pooled_1028" else 1.1,
                ls="-" if gname != "pooled_1028" else (0, (4, 2)),
                marker="o" if gname != "pooled_1028" else None,
                markersize=3.0, markerfacecolor="white", markeredgewidth=0.9,
                zorder=5, label=lbl)
    ax.set_xlabel(f"{nice} (%)")
    ax.set_ylabel("population quiescent (%)")
    ax.set_xlim(0, 92)
    ax.set_ylim(-3, 103)
    ax.set_title(nice.replace(" block", ""), loc="left", pad=8)
    ax.text(-0.16, 1.10, tag, transform=ax.transAxes, fontsize=10,
            fontweight="bold", va="top", ha="left", color=INK)
    ch = d["historical_188"]["censored_fraction"]
    cn = d["new_840"]["censored_fraction"]
    # Place the annotation away from the curve: the I_CaL curve is high on the
    # right, the I_f curve hugs the bottom, so they need opposite corners.
    if cur == "G_CaL":
        tx, ty, hha, vva = 0.97, 0.05, "right", "bottom"
    else:
        tx, ty, hha, vva = 0.03, 0.97, "left", "top"
    ax.text(tx, ty, f"never quiescent to 90%\nhist {ch:.1%}   new {cn:.1%}",
            transform=ax.transAxes, ha=hha, va=vva, fontsize=6.8,
            color=INK2)

axes[0].legend(frameon=False, fontsize=7, loc="upper left")
fig.tight_layout(w_pad=3.0)
op = os.path.join(DEST, "P1_threshold_geometry.png")
fig.savefig(op, bbox_inches="tight")
fig.savefig(op.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

with open(os.path.join(DEST, "P1_threshold_comparison.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)

for cur in ("G_CaL", "G_f"):
    d = report.get(cur, {})
    if d.get("status") == "sweep_not_finished":
        print(f"\n{cur}: SWEEP NOT FINISHED")
        continue
    print(f"\n{'='*74}\n{cur}\n{'='*74}")
    for g in ("historical_188", "new_840", "pooled_1028"):
        gg = d[g]
        q = gg["threshold_conditional_quantiles"]
        print(f"  {g:16s} n={gg['n']:5d}  censored@90%={gg['n_censored_at_0.90']:4d}"
              f" ({gg['censored_fraction']:.1%})  non-monotone="
              f"{gg['n_non_monotone']}")
        print(f"      cond. median {gg['threshold_conditional_median']}  "
              f"IQR {gg['threshold_conditional_iqr']}  "
              f"range {q['p0']}-{q['p100']}")
        print(f"      KM median   {gg['km_median']}")
    c = d["comparison_188_vs_840"]
    print(f"  LOG-RANK 188 vs 840: chi2={c['logrank']['chi2']:.3f}  "
          f"p={c['logrank']['p']:.4f}")
    print(f"  max |level difference| = {c['max_abs_level_diff_pp']:.2f} pp")
print(f"\n-> {op}")
print("-> 08_taskP/P1_threshold_comparison.json")
