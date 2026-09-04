"""Task 8 - regenerate Figure 2 so the printed I_CaL IQR matches the verified
value 30.0-51.25%. The published figure printed "51%" (0 dp).

Only the IQR label formatting changes. No other redesign. Written to a NEW file.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "07_v6_cleanup")

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8880", "#dcdbd6"
BLUE = "#2a78d6"
plt.rcParams.update({
    "figure.dpi": 300, "savefig.dpi": 300, "font.size": 8,
    "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.labelcolor": INK, "axes.titlecolor": INK,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white"})


def load(n):
    with open(os.path.join(OUT, n), encoding="utf-8") as f:
        return json.load(f)


def fmt(x):
    """Print a fraction as a percentage with the minimum digits that are
    exact: 0.30 -> '30.0', 0.5125 -> '51.25'."""
    v = x * 100
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if "." in s else f"{v:.1f}"


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
            color=BLUE, lw=2.0, zorder=4, marker="o", markersize=3.4,
            markerfacecolor="white", markeredgewidth=1.0)
    med = s["threshold_median"]
    if tgt == "G_CaL":
        q1, q3 = s["threshold_iqr"]
        ax.axvspan(q1 * 100, q3 * 100, color=BLUE, alpha=0.10, zorder=1, lw=0)
        ax.axvline(med * 100, color=INK, lw=1.1, ls=(0, (4, 2)), zorder=5)
        ax.text(med * 100 + 2.5, 84, f"median {fmt(med)}%", fontsize=7,
                color=INK)
        # CORRECTED: 2-dp where needed, so the figure prints 51.25 not 51
        ax.text((q1 + q3) * 50, 96, f"IQR {fmt(q1)}–{fmt(q3)}%",
                fontsize=6.8, color=INK2, ha="center")
    ax.set_xlabel(f"{name} (%)")
    ax.set_ylabel("population quiescent (%)")
    ax.set_xlim(0, 92)
    ax.set_ylim(-3, 103)
    ax.set_title(name.replace(" block", ""), loc="left", pad=8)
    nev = s["n_never_quiescent"]
    txt = (f"n = {n} models\n"
           f"never quiescent to 90%: {nev}/{n} = {nev/n:.1%}")
    if tgt != "G_CaL":
        q1, q3 = s["threshold_iqr"]
        txt += (f"\namong the {n - nev} that do stop:"
                f"\nmedian {fmt(med)}%, IQR {fmt(q1)}–{fmt(q3)}%")
    ax.text(0.97, 0.05 if tgt == "G_CaL" else 0.74, txt,
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
            color=INK2)
    ax.text(-0.16, 1.06, tag, transform=ax.transAxes, fontsize=10,
            fontweight="bold", va="top", ha="left", color=INK)

fig.tight_layout(w_pad=3.0)
p = os.path.join(DEST, "Figure2_corrected.png")
fig.savefig(p, bbox_inches="tight")
fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)
g = summ["G_CaL"]
print(f"I_CaL median {fmt(g['threshold_median'])}%  "
      f"IQR {fmt(g['threshold_iqr'][0])}-{fmt(g['threshold_iqr'][1])}%  "
      f"range {fmt(g['threshold_range'][0])}-{fmt(g['threshold_range'][1])}%")
print(f"-> {p}")
