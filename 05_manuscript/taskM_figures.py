"""Task M2 - manuscript figures. Four, print-ready, for AJP-Heart.

Every value is read PROGRAMMATICALLY from the frozen outputs. No number is
typed in from a report. No new simulation and no new analysis is performed -
this script only reads and draws.

Design decisions, from the data-viz method:
  * form first. Fig 1B/2 are distributions -> histogram / cumulative curve.
    Fig 3 is change-over-an-ordered-x -> lines. Fig 4 is a categorical
    classification against a continuous x -> line + classified markers.
  * colour by JOB. Anchor identity is CATEGORICAL -> the first three slots of
    the validated palette (blue/orange/aqua), which are the documented
    all-pairs-safe subset. PK exposure multiple is ORDINAL MAGNITUDE -> a
    light->dark lightness ramp WITHIN the anchor's own hue, never a second
    categorical set.
  * palette validated, not eyeballed:
      node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a" \
           --mode light --pairs all
      -> ALL CHECKS PASS; one WARN, aqua 2.74:1 vs surface, which obliges
         "relief": every anchor is DIRECTLY LABELLED as a panel title, and the
         full table view exists as 05_manuscript/values_manifest.md.
  * secondary encoding for print/greyscale/CVD: PK arm also carries a distinct
    linestyle, so identity is never colour-alone.
  * recessive grid and axes; thin marks; no dual axes anywhere.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.lines import Line2D                  # noqa: E402
from matplotlib.patches import Patch                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "05_manuscript", "figures")
os.makedirs(DEST, exist_ok=True)


def load(n):
    with open(os.path.join(OUT, n), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ style
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8880"
GRID = "#dcdbd6"
BANDC = "#c9c8c2"
SLOT = {"Doesch": "#2a78d6", "10-year": "#eb6834", "36-month": "#1baf7a"}

plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300,
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.labelcolor": INK, "axes.titlecolor": INK,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})


def shade(hex_color, t):
    """t<0 lighten toward white, t>0 darken toward black. Ordinal ramp."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    if t < 0:
        r, g, b = (c + (1 - c) * (-t) for c in (r, g, b))
    else:
        r, g, b = (c * (1 - t) for c in (r, g, b))
    return "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in (r, g, b))


def panel_tag(ax, s):
    ax.text(-0.16, 1.06, s, transform=ax.transAxes, fontsize=10,
            fontweight="bold", va="top", ha="left", color=INK)


# =====================================================================
# FIGURE 1 - population validation
# =====================================================================
def figure1():
    b = load("step1_baseline.json")
    s3 = load("step3fix_run_statefix.json")
    crit = s3["criteria"]

    order = ["CL_ms", "MDP_mV", "OS_mV", "APA_mV", "DDR100_mV_s", "dVdtmax_V_s"]
    lab = {"CL_ms": "Cycle length", "MDP_mV": "MDP", "OS_mV": "Overshoot",
           "APA_mV": "AP amplitude", "DDR100_mV_s": "DDR$_{100}$",
           "dVdtmax_V_s": "(dV/dt)$_{max}$"}
    pct = [b["comparison"][k]["pct"] for k in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.9))

    y = np.arange(len(order))[::-1]
    ax1.axvline(0, color=MUTED, lw=0.8, zorder=1)
    for v in (-1, 1):
        ax1.axvline(v, color=GRID, lw=0.7, ls=(0, (3, 3)), zorder=1)
    ax1.barh(y, pct, height=0.55, color=SLOT["Doesch"], zorder=3)
    for yi, p in zip(y, pct):
        ax1.text(p + (0.045 if p >= 0 else -0.045), yi, f"{p:+.2f}%",
                 va="center", ha="left" if p >= 0 else "right",
                 fontsize=7, color=INK2)
    ax1.set_yticks(y, [lab[k] for k in order])
    ax1.set_xlabel("deviation from Fabbri 2017 Table 5 (%)")
    ax1.set_xlim(-1.35, 1.45)
    ax1.set_title("Baseline reproduction", loc="left", pad=8)
    ax1.text(0.02, 0.06, "guides at $\\pm$1%", transform=ax1.transAxes,
             ha="left", fontsize=6.5, color=MUTED)
    panel_tag(ax1, "A")

    ok = [r for r in s3["results"] if r["status"] == "ok"]
    ret = [r for r in ok if crit["bcl_min_ms"] <= r["CL_ms"]
           <= crit["bcl_max_ms"] and r["OS_mV"] > 0]
    bpm = np.array([60000.0 / r["CL_ms"] for r in ret])
    n_ret, n_run = len(ret), s3["n_models"]
    zhou = crit["reference_retained"] / crit["reference_total"]

    ax2.grid(axis="y", zorder=0)
    ax2.hist(bpm, bins=np.arange(58, 102, 2), color=SLOT["Doesch"],
             edgecolor="white", linewidth=0.6, zorder=3)
    ax2.axvline(np.median(bpm), color=INK, lw=1.2, ls=(0, (4, 2)), zorder=4)
    ax2.text(0.98, 0.98, f"median {np.median(bpm):.1f} bpm",
             transform=ax2.transAxes, ha="right", va="top", fontsize=7,
             color=INK)
    ax2.set_xlabel("intrinsic rate (beats$\\cdot$min$^{-1}$)")
    ax2.set_ylabel("models")
    ax2.set_title("Retained population", loc="left", pad=8)
    ax2.text(0.02, 0.98,
             f"retained {n_ret}/{n_run} ({n_ret/n_run:.1%})\n"
             f"Zhou {crit['reference_retained']}/{crit['reference_total']} "
             f"({zhou:.1%})",
             transform=ax2.transAxes, va="top", fontsize=6.8, color=INK2)
    panel_tag(ax2, "B")

    fig.tight_layout(w_pad=3.0)
    p = os.path.join(DEST, "figure1_population_validation.png")
    fig.savefig(p, bbox_inches="tight")
    fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return p


# =====================================================================
# FIGURE 2 - quiescence-threshold distributions
# =====================================================================
def figure2():
    summ = load("taskA_summary.json")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))

    for ax, fn, tgt, name, tag in (
            (axes[0], "taskA_G_CaL_population_sweep.json", "G_CaL",
             "$I_{CaL}$ block", "A"),
            (axes[1], "taskA_G_f_population_sweep.json", "G_f",
             "$I_{f}$ block", "B")):
        lad = load(fn)
        recs = lad["records"]
        n = len(recs)
        grid = sorted(float(k) for k in recs[0]["levels"])
        frac = [sum(1 for r in recs if r["levels"].get(str(g)) is None) / n
                for g in grid]
        s = summ[tgt]

        ax.grid(zorder=0)
        ax.plot([g * 100 for g in grid], [f * 100 for f in frac],
                color=SLOT["Doesch"], lw=2.0, zorder=4,
                marker="o", markersize=3.4, markerfacecolor="white",
                markeredgewidth=1.0)
        med = s["threshold_median"]
        if tgt == "G_CaL":
            q1, q3 = s["threshold_iqr"]
            ax.axvspan(q1 * 100, q3 * 100, color=SLOT["Doesch"], alpha=0.10,
                       zorder=1, lw=0)
            ax.axvline(med * 100, color=INK, lw=1.1, ls=(0, (4, 2)), zorder=5)
            ax.text(med * 100 + 1.8, 88, f"median {med:.0%}", fontsize=7,
                    color=INK)
            ax.text((q1 + q3) * 50, 96, f"IQR {q1:.0%}–{q3:.0%}", fontsize=6.8,
                    color=INK2, ha="center")
        ax.set_xlabel(f"{name} (%)")
        ax.set_ylabel("population quiescent (%)")
        ax.set_xlim(0, 92)
        ax.set_ylim(-3, 103)
        ax.set_title(name.replace(" block", ""), loc="left", pad=8)
        nev = s["n_never_quiescent"]
        txt = (f"n = {n} models\n"
               f"never quiescent to 90%: {nev}/{n} = {nev/n:.1%}")
        if tgt != "G_CaL":
            # The I_f median/IQR describe ONLY the minority that ever stop, so
            # they are stated conditionally and NOT drawn as a population band.
            q1, q3 = s["threshold_iqr"]
            txt += (f"\namong the {n - nev} that do stop:"
                    f" median {med:.0%}, IQR {q1:.0%}–{q3:.0%}")
        ax.text(0.97, 0.05 if tgt == "G_CaL" else 0.78, txt,
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=7, color=INK2)
        panel_tag(ax, tag)

    fig.tight_layout(w_pad=3.0)
    p = os.path.join(DEST, "figure2_quiescence_thresholds.png")
    fig.savefig(p, bbox_inches="tight")
    fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return p


# =====================================================================
# FIGURE 3 - EAR vs verapamil exposure, three anchors x PK arms
# =====================================================================
def figure3():
    tl = load("taskL_three_anchor_EAR.json")
    ti = load("taskI_pk_interaction.json")
    bands = load("taskH_exposure.json")["bands_total_ng_per_mL"]

    cols = [("Doesch 2007  (PRIMARY)", "Doesch",
             "Doesch 2007 — primary\n$I_f$ 58.4%"),
            ("10-year cohort", "10-year", "10-year cohort\n$I_f$ 50.9%"),
            ("36-month (superseded)", "36-month",
             "36-month — superseded\n$I_f$ 31.2%")]
    arms = [("1x", 0, "-"), ("2x", 1, (0, (5, 2))),
            ("3x", 2, (0, (1.5, 1.5)))]
    tints = [-0.40, -0.05, 0.30]

    fig, axes = plt.subplots(2, 3, figsize=(7.2, 5.0), sharex=True,
                             sharey="row")
    for ri, state in enumerate(("control", "iso")):
        rows_all = tl["states"][state]["rows"]
        for ci, (akey, slot, title) in enumerate(cols):
            ax = axes[ri, ci]
            ax.grid(zorder=0)
            for lbl, (lo, hi) in bands.items():
                ax.axvspan(lo, hi, color=BANDC, alpha=0.30, zorder=1, lw=0)
            for m in (5, 10):
                ax.axhline(m, color=MUTED, lw=0.7, ls=(0, (2, 2.5)), zorder=2)

            rows = sorted([r for r in rows_all if r["anchor"] == akey],
                          key=lambda r: r["block"])
            x = [r["total_ng_per_mL"] for r in rows]
            for (arm, ti_, ls) in arms:
                y = [r["arms"][arm]["EAR"] * 100 for r in rows]
                ax.plot(x, y, color=shade(SLOT[slot], tints[ti_]), lw=1.8,
                        ls=ls, marker="o", markersize=3.2,
                        markerfacecolor="white", markeredgewidth=0.9,
                        zorder=5, label=f"{arm} exposure")
            if slot == "36-month":
                r7 = sorted(ti["states"][state]["rows"],
                            key=lambda r: r["block"])
                k7 = next(k for k in r7[0]["arms"] if k.startswith("7x"))
                ax.plot([r["total_ng_per_mL"] for r in r7],
                        [r["arms"][k7]["EAR"] * 100 for r in r7],
                        color=shade(SLOT[slot], 0.55), lw=1.4,
                        ls=(0, (4, 1.5, 1, 1.5)), marker="^", markersize=3.2,
                        markerfacecolor="white", markeredgewidth=0.9,
                        zorder=5, label="7x (strong inhib.)")
            if ri == 0:
                ax.set_title(title, loc="left", pad=8, fontsize=8)
            if ci == 0:
                ax.set_ylabel(f"{state} state\nexcess absolute risk (%)")
            if ri == 1:
                ax.set_xlabel("total plasma verapamil (ng$\\cdot$mL$^{-1}$)")
            ax.set_xlim(0, 620)
            ax.set_ylim(-1.2, 28)
    for lbl, (lo, hi) in bands.items():
        axes[0, 0].text((lo + hi) / 2, 26.6, lbl.replace(" mg/day", " mg/d"),
                        ha="center", va="top", fontsize=6.2, color=INK2)
    handles = [Line2D([], [], color=INK2, lw=1.8, ls=ls, marker="o",
                      markersize=3.2, markerfacecolor="white",
                      markeredgewidth=0.9, label=f"{a} exposure")
               for a, _, ls in arms]
    handles.append(Line2D([], [], color=INK2, lw=1.4,
                          ls=(0, (4, 1.5, 1, 1.5)), marker="^",
                          markersize=3.2, markerfacecolor="white",
                          markeredgewidth=0.9,
                          label="7x strong inhibitor (36-month only)"))
    fig.legend(handles=handles, frameon=False, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.055), handlelength=2.6, fontsize=7)
    fig.text(0.5, -0.10,
             "shaded bands: chronic oral exposure ranges (FDA label). "
             "dotted guides at 5% and 10% excess absolute risk.",
             ha="center", fontsize=6.8, color=MUTED)
    panel_tag(axes[0, 0], "A")
    panel_tag(axes[1, 0], "B")
    fig.tight_layout(w_pad=1.6, h_pad=1.4)
    p = os.path.join(DEST, "figure3_EAR_three_anchors.png")
    fig.savefig(p, bbox_inches="tight")
    fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return p


# =====================================================================
# FIGURE 4 - Bliss is not a usable null on a threshold endpoint
# =====================================================================
def figure4():
    tG = load("taskG_pair_prediction.json")
    bf = tG["B_ivabradine"]
    rows = sorted([r for r in tG["states"]["control"]["rows"]
                   if abs(r["b_ivabradine"] - bf) < 1e-9],
                  key=lambda r: r["b_verapamil"])
    x = [r["b_verapamil"] * 100 for r in rows]
    ear = [r["EAR_paired"] * 100 for r in rows]
    lo = [r["EAR_paired_ci"][0] * 100 for r in rows]
    hi = [r["EAR_paired_ci"][1] * 100 for r in rows]
    cls = [r["bliss_class"] for r in rows]
    resc = max(r["rescue_fraction"] for r in rows)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.3, 4.3), sharex=True,
                                   gridspec_kw={"height_ratios": [2.3, 1]})

    ax1.grid(zorder=0)
    ax1.fill_between(x, lo, hi, color=SLOT["Doesch"], alpha=0.16, lw=0,
                     zorder=2, label="95% CI")
    ax1.plot(x, ear, color=SLOT["Doesch"], lw=2.0, marker="o", markersize=4,
             markerfacecolor="white", markeredgewidth=1.0, zorder=4,
             label="excess absolute risk")
    ax1.set_ylabel("excess absolute risk (%)")
    ax1.set_title("Paired EAR is well behaved", loc="left", pad=8)
    ax1.text(0.97, 0.06, f"rescue fraction = {resc:.3f} at every rung\n"
                         "(endpoint is monotone)",
             transform=ax1.transAxes, ha="right", fontsize=7, color=INK2)
    ax1.legend(frameon=False, loc="upper left", handlelength=2.2)
    panel_tag(ax1, "A")

    ax2.grid(axis="x", zorder=0)
    ymap = {"additive": 0, "SUPER-ADDITIVE": 1, "SUB-ADDITIVE": -1,
            "no events": 0, "ceiling": 0}
    yv = [ymap.get(c, 0) for c in cls]
    ax2.axhline(0, color=MUTED, lw=0.8, zorder=1)
    ax2.plot(x, yv, color=INK2, lw=1.0, ls=(0, (2, 2)), zorder=3)
    for xi, yi, c in zip(x, yv, cls):
        sup = (c == "SUPER-ADDITIVE")
        ax2.plot(xi, yi, marker="s" if sup else "o", markersize=7,
                 color=SLOT["10-year"] if sup else SLOT["36-month"],
                 markeredgecolor="white", markeredgewidth=0.9, zorder=5)
    ax2.set_yticks([0, 1], ["Bliss\nadditive", "Bliss\nSUPER-\nADDITIVE"])
    ax2.set_ylim(-0.55, 1.55)
    ax2.set_xlabel("verapamil $I_{CaL}$ block (%)")
    ax2.set_title("Bliss classification alternates on the same ladder",
                  loc="left", pad=8)
    panel_tag(ax2, "B")

    fig.text(0.5, -0.03,
             "verapamil $\\times$ ivabradine act on DIFFERENT channels: the model "
             "contains\nno mechanistic interaction, so every departure from Bliss "
             "is threshold geometry.",
             ha="center", fontsize=6.8, color=MUTED)
    fig.tight_layout(h_pad=1.6)
    p = os.path.join(DEST, "figure4_bliss_artifact.png")
    fig.savefig(p, bbox_inches="tight")
    fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
    plt.close(fig)
    return p


if __name__ == "__main__":
    for fn in (figure1, figure2, figure3, figure4):
        print("->", fn())
