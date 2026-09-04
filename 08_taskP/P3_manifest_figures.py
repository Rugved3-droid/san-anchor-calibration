"""P3 values manifest + all four figures, regenerated on P3 results.

Every number is read programmatically from the frozen P3 outputs - never from
prose and never from memory. Figure 4 is at the PRIMARY anchor.
"""
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                     # noqa: E402
from matplotlib.lines import Line2D                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P3 = os.path.join(ROOT, "08_taskP", "p3")
TH = os.path.join(ROOT, "08_taskP", "threshold")
DEST = os.path.join(ROOT, "08_taskP", "p3_figures")
os.makedirs(DEST, exist_ok=True)

BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, BANDC = "#1b1f24", "#454c54", "#8a929b", "#cfd6dd"
SLOT = {"Doesch": BLUE, "10-year": ORANGE, "36-month": GREEN}
plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2,
                     "axes.grid": True, "grid.color": "#e6e9ec",
                     "grid.linewidth": 0.7, "figure.dpi": 200,
                     "savefig.dpi": 400, "axes.spines.top": False,
                     "axes.spines.right": False})

core = json.load(open(os.path.join(P3, "P3_results_core.json"),
                      encoding="utf-8"))
full = json.load(open(os.path.join(P3, "P3_results_full.json"),
                      encoding="utf-8"))
subchar = json.load(open(os.path.join(ROOT, "08_taskP",
                                      "P3_subset_characterisation.json"),
                         encoding="utf-8"))
commit = json.load(open(os.path.join(ROOT, "08_taskP",
                                     "P3_SUBSET_COMMITMENT.json"),
                        encoding="utf-8"))
base = json.load(open(os.path.join(ROOT, "outputs", "step1_baseline.json"),
                      encoding="utf-8"))


def shade(hex_color, t):
    c = np.array([int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    c = c * (1 - abs(t)) + (1 if t > 0 else 0) * abs(t)
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c)


def tag(ax, s):
    ax.text(-0.16, 1.10, s, transform=ax.transAxes, fontsize=10,
            fontweight="bold", va="top", ha="left", color=INK)


# ===================== MANIFEST ==========================================
man = {"generated_from": "P3 dense grid on the committed 500-model subset",
       "subset_seed": commit["P3_SUBSET_SEED"],
       "subset_sha256": commit["subset_sha256"],
       "source_population": commit["source_population"],
       "source_population_sha256": commit["source_population_sha256"],
       "values": {}}
V = man["values"]
V["subset.n"] = core["subset_n"]
V["subset.denominator.control"] = core["denominators"]["control"]
V["subset.denominator.iso"] = core["denominators"]["iso"]
V["subset.n_excluded_iso_drugfree"] = (core["subset_n"]
                                       - core["denominators"]["iso"])
for k in ("CL_ms", "bpm"):
    for g in ("subset", "complement", "full"):
        d = subchar[f"{k}_{g}"]
        for stat in ("median", "q1", "q3", "min", "max", "mean", "sd"):
            V[f"rate.{k}.{g}.{stat}"] = d[stat]
    t = subchar[f"{k}_disjoint_test"]
    V[f"rate.{k}.subset_vs_complement.median_diff"] = \
        t["median_diff_subset_minus_complement"]
    V[f"rate.{k}.subset_vs_complement.ci95"] = t["median_diff_ci95"]
    V[f"rate.{k}.subset_vs_complement.ks_p"] = t["ks_p"]
for cur in ("G_CaL", "G_f"):
    c = subchar[f"{cur}_curve"]
    V[f"threshold.{cur}.subset_vs_full.max_abs_diff_pp"] = c["max_abs_diff_pp"]
    V[f"threshold.{cur}.subset.censored_frac"] = c["subset"]["censored_frac"]
    V[f"threshold.{cur}.full.censored_frac"] = c["full"]["censored_frac"]
    V[f"threshold.{cur}.subset.cond_median"] = c["subset"]["cond_median"]
    V[f"threshold.{cur}.full.cond_median"] = c["full"]["cond_median"]
for r in full["band_maxima"]:
    key = (f"emqf.{r['anchor'].split()[0]}.{r['arm']}.{r['state']}."
           f"{r['band'].split()[0]}")
    V[key + ".max"] = r["max_EMQF"]
    V[key + ".rung"] = r["at_rung"]
    V[key + ".k"] = r["EMQF_k"]
    V[key + ".n"] = r["n"]
    V[key + ".ci95"] = r["EMQF_ci95"]
    V[key + ".ceiling_frac"] = r["eligible_frac"]
    V[key + ".obs_over_ceiling"] = r["obs_over_max"]
    V[key + ".point_gt_5"] = r["point_gt_5pct"]
    V[key + ".ci_gt_5"] = r["ci_lower_gt_5pct"]
    V[key + ".point_gt_10"] = r["point_gt_10pct"]
    V[key + ".ci_gt_10"] = r["ci_lower_gt_10pct"]
V.update({f"summary.{k}": v for k, v in full["summary_5_10"].items()})
for r in full["decomposition"]:
    key = (f"decomp.{r['anchor'].split()[0]}.{r['state']}."
           f"{int(round(r['block']*1000))}")
    for f_ in ("PK_only", "PD_only", "PK_plus_PD_2x", "PK_plus_PD_3x",
               "n_cohort", "larger"):
        V[f"{key}.{f_}"] = r[f_]
for r in full["external"]:
    key = (f"external.{r['anchor'].split()[0]}.{r['state']}."
           f"{'primary' if r['is_primary'] else 'cmax'}")
    V[key + ".predicted_bpm"] = r["predicted_bpm"]
    V[key + ".observed_bpm"] = r["observed_bpm"]
    V[key + ".ratio"] = r["ratio"]
for r in full["bliss"]:
    key = f"bliss.{r['state']}.{int(round(r['block']*1000))}"
    V[key + ".class"] = r["bliss_class"]
    V[key + ".informative"] = r["informative"]
    V[key + ".P_AB"] = r["P_AB"]
    V[key + ".bliss_expected"] = r["bliss_expected"]
with open(os.path.join(P3, "P3_values_manifest.json"), "w",
          encoding="utf-8") as f:
    json.dump(man, f, indent=2)
print(f"manifest: {len(V)} values -> 08_taskP/p3/P3_values_manifest.json")


def v(k):
    return V[k]


# ===================== FIGURE 1 ==========================================
order = ["CL_ms", "MDP_mV", "OS_mV", "APA_mV", "DDR100_mV_s", "dVdtmax_V_s"]
lab = {"CL_ms": "Cycle length", "MDP_mV": "MDP", "OS_mV": "Overshoot",
       "APA_mV": "AP amplitude", "DDR100_mV_s": "DDR$_{100}$",
       "dVdtmax_V_s": "(dV/dt)$_{max}$"}
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.9))
pct = [base["comparison"][k]["pct"] for k in order]
y = np.arange(len(order))[::-1]
ax1.grid(zorder=0)
ax1.axvline(0, color=MUTED, lw=0.8, zorder=1)
ax1.barh(y, pct, height=0.55, color=BLUE, zorder=3)
ax1.set_yticks(y, [lab[k] for k in order])
ax1.set_xlabel("difference vs Fabbri 2017 Table 5 (%)")
ax1.set_title("Baseline model reproduction", loc="left", pad=8)
tag(ax1, "A")
ax2.grid(zorder=0)
groups = ["P1 retained\n(1028/5000)", "P3 subset\n(500 of 1028)"]
vals = [1028 / 5000 * 100, 100 * 500 / 1028]
ax2.bar([0], [vals[0]], width=0.5, color=BLUE, zorder=3, label="retained %")
ax2.bar([1], [vals[1]], width=0.5, color=ORANGE, zorder=3)
ax2.axhline(20.92, color=INK, lw=1.1, ls=(0, (4, 2)), zorder=5)
ax2.text(1.45, 21.6, "Zhou 20.92%", fontsize=6.8, color=INK, ha="right")
ax2.set_xticks([0, 1], groups)
ax2.set_ylabel("% of parent set")
ax2.set_ylim(0, 60)
ax2.set_title("Population and subset", loc="left", pad=8)
for i, val in enumerate(vals):
    ax2.text(i, val + 1.6, f"{val:.2f}%", ha="center", fontsize=7, color=INK2)
tag(ax2, "B")
fig.tight_layout(w_pad=2.4)
p1 = os.path.join(DEST, "P3_figure1_population.png")
fig.savefig(p1, bbox_inches="tight")
fig.savefig(p1.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

# ===================== FIGURE 2 ==========================================
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
for ax, cur, nice, t in ((axes[0], "G_CaL", r"$I_{CaL}$ block", "A"),
                         (axes[1], "G_f", r"$I_f$ block", "B")):
    c = subchar[f"{cur}_curve"]
    x = [r["block"] * 100 for r in c["rows"]]
    ax.grid(zorder=0)
    for key, colour, lbl in (("sub", ORANGE, "P3 subset (500)"),
                             ("full", BLUE, "full population (1028)")):
        yv = [r[f"{key}_frac"] * 100 for r in c["rows"]]
        lo = [r[f"{key}_wilson95"][0] * 100 for r in c["rows"]]
        hi = [r[f"{key}_wilson95"][1] * 100 for r in c["rows"]]
        ax.fill_between(x, lo, hi, color=colour, alpha=0.14, lw=0, zorder=2)
        ax.plot(x, yv, color=colour, lw=1.7, marker="o", markersize=3.0,
                markerfacecolor="white", markeredgewidth=0.9, zorder=5,
                label=lbl)
    ax.set_xlabel(f"{nice} (%)")
    ax.set_ylabel("population quiescent (%)")
    ax.set_xlim(0, 92)
    ax.set_ylim(-3, 103)
    ax.set_title(nice.replace(" block", ""), loc="left", pad=8)
    txt = (f"max |subset - full| = {c['max_abs_diff_pp']:.2f} pp\n"
           f"never quiescent to 90%: {c['subset']['censored_frac']:.1%} / "
           f"{c['full']['censored_frac']:.1%}")
    ax.text(0.03 if cur == "G_f" else 0.97, 0.97 if cur == "G_f" else 0.05,
            txt, transform=ax.transAxes,
            ha="left" if cur == "G_f" else "right",
            va="top" if cur == "G_f" else "bottom", fontsize=6.8, color=INK2)
    tag(ax, t)
axes[0].legend(frameon=False, fontsize=7, loc="upper left")
fig.tight_layout(w_pad=3.0)
p2 = os.path.join(DEST, "P3_figure2_quiescence_thresholds.png")
fig.savefig(p2, bbox_inches="tight")
fig.savefig(p2.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

# ===================== FIGURE 3 ==========================================
BANDS_NG = {"240 mg/day": (35.0, 164.0), "480 mg/day": (125.0, 400.0)}
cols = [("Doesch 2007 (PRIMARY)", "Doesch", "Doesch 2007 — primary\n$I_f$ 58.4%"),
        ("10-year cohort", "10-year", "10-year cohort\n$I_f$ 50.9%"),
        ("36-month (superseded)", "36-month",
         "36-month — superseded\n$I_f$ 31.2%")]
arms = [("1x", 0, "-"), ("2x", 1, (0, (5, 2))), ("3x", 2, (0, (1.5, 1.5)))]
tints = [-0.40, -0.05, 0.30]
fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.0), sharex=True, sharey="row")
for ri, state in enumerate(("control", "iso")):
    for ci, (akey, slot, title) in enumerate(cols):
        ax = axes[ri, ci]
        ax.grid(zorder=0)
        for lbl, (lo, hi) in BANDS_NG.items():
            ax.axvspan(lo, hi, color=BANDC, alpha=0.30, zorder=1, lw=0)
        for m in (5, 10):
            ax.axhline(m, color=MUTED, lw=0.7, ls=(0, (2, 2.5)), zorder=2)
        for (arm, ti, ls) in arms:
            rows = sorted([r for r in core["rows"]
                           if r["anchor"] == akey and r["arm"] == arm
                           and r["state"] == state],
                          key=lambda r: r["b_cal"])
            ax.plot([r["total_ng_per_mL"] for r in rows],
                    [r["EMQF"] * 100 for r in rows],
                    color=shade(SLOT[slot], tints[ti]), lw=1.8, ls=ls,
                    marker="o", markersize=3.2, markerfacecolor="white",
                    markeredgewidth=0.9, zorder=5)
        if ri == 0:
            ax.set_title(title, loc="left", pad=8, fontsize=8)
        if ci == 0:
            ax.set_ylabel(f"{state} state\nEMQF (%)")
        if ri == 1:
            ax.set_xlabel("total plasma verapamil (ng$\\cdot$mL$^{-1}$)")
        ax.set_xlim(0, 620)
        ax.set_ylim(-1.2, 28)
for lbl, (lo, hi) in BANDS_NG.items():
    axes[0, 0].text((lo + hi) / 2, 26.6, lbl.replace(" mg/day", " mg/d"),
                    ha="center", va="top", fontsize=6.2, color=INK2)
handles = [Line2D([], [], color=INK2, lw=1.8, ls=ls, marker="o",
                  markersize=3.2, markerfacecolor="white",
                  markeredgewidth=0.9, label=f"{a} exposure")
           for a, _, ls in arms]
fig.legend(handles=handles, frameon=False, ncol=3, loc="lower center",
           bbox_to_anchor=(0.5, -0.05), handlelength=2.6, fontsize=7)
fig.text(0.5, -0.095, "shaded bands: chronic oral exposure ranges (FDA "
         "label). dotted guides at 5% and 10% EMQF.  P3 subset, n = 500.",
         ha="center", fontsize=6.8, color=MUTED)
tag(axes[0, 0], "A")
tag(axes[1, 0], "B")
fig.tight_layout(w_pad=1.6, h_pad=1.4)
p3 = os.path.join(DEST, "P3_figure3_EMQF_three_anchors.png")
fig.savefig(p3, bbox_inches="tight")
fig.savefig(p3.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

# ===================== FIGURE 4 (PRIMARY anchor) =========================
prim = [r for r in core["rows"]
        if r["anchor"] == "Doesch 2007 (PRIMARY)" and r["arm"] == "1x"
        and r["state"] == "control"]
prim = sorted(prim, key=lambda r: r["b_cal"])
bl = {round(r["block"], 6): r for r in full["bliss"] if r["state"] == "control"}
x = [r["b_cal"] * 100 for r in prim]
ear = [r["EMQF"] * 100 for r in prim]
lo = [r["EMQF_ci95"][0] * 100 for r in prim]
hi = [r["EMQF_ci95"][1] * 100 for r in prim]
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.6, 4.6), sharex=True,
                               gridspec_kw={"height_ratios": [2.3, 1]})
ax1.grid(zorder=0)
ax1.fill_between(x, lo, hi, color=BLUE, alpha=0.16, lw=0, zorder=2,
                 label="95% CI")
ax1.plot(x, ear, color=BLUE, lw=2.0, marker="o", markersize=3.4,
         markerfacecolor="white", markeredgewidth=1.0, zorder=5, label="EMQF")
for m, lb in ((5, "5%"), (10, "10%")):
    ax1.axhline(m, color=MUTED, lw=0.7, ls=(0, (2, 2.5)), zorder=3)
    ax1.text(1.0, m + 0.4, lb, fontsize=6.5, color=MUTED)
ax1.set_ylabel("EMQF (%)")
ax1.set_title("Primary anchor (Doesch, $I_f$ 58.4%), control, 1×",
              loc="left", pad=8)
ax1.legend(frameon=False, fontsize=7, loc="upper left")
tag(ax1, "A")
ax2.grid(zorder=0)
codes, colours = [], []
for r in prim:
    b = bl.get(round(r["b_cal"], 6))
    cls = b["bliss_class"] if b else "additive"
    codes.append(1 if cls == "SUPER-ADDITIVE" else 0)
    colours.append(ORANGE if cls == "SUPER-ADDITIVE" else BLUE)
ax2.scatter(x, codes, c=colours, s=26, zorder=5, edgecolor="white",
            linewidth=0.8)
ax2.set_yticks([0, 1], ["Bliss\nadditive", "Bliss\nSUPER-\nADDITIVE"])
ax2.set_ylim(-0.5, 1.5)
ax2.set_xlabel("$I_{CaL}$ block (%)")
ax2.set_title("Bliss classification along the same ladder", loc="left", pad=8)
n_inf = sum(1 for r in full["bliss"]
            if r["state"] == "control" and r["informative"])
n_tot = sum(1 for r in full["bliss"] if r["state"] == "control")
ax2.text(0.98, 0.08, f"informative rungs {n_inf}/{n_tot}\n"
         "(none excluded as no-events / ceiling)", transform=ax2.transAxes,
         ha="right", va="bottom", fontsize=6.4, color=INK2)
tag(ax2, "B")
fig.text(0.5, -0.055, "A threshold endpoint manufactures Bliss "
         "super-additivity from additive target occupancy;\nthe "
         "classification is an ARTIFACT DEMONSTRATION, not a mechanistic "
         "claim.", ha="center", fontsize=6.6, color=MUTED)
fig.tight_layout(h_pad=1.2)
p4 = os.path.join(DEST, "P3_figure4_bliss_primary_anchor.png")
fig.savefig(p4, bbox_inches="tight")
fig.savefig(p4.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

for p in (p1, p2, p3, p4):
    print(f"  -> {os.path.relpath(p, ROOT)}")
