"""Forensic audit - regenerate Figure 4 at the PRIMARY (Doesch, 58.4% I_f) anchor.

The published Figure 4 was drawn at the SUPERSEDED 31.2% anchor. Every condition
needed at 58.4% already exists in taskG_pair_checkpoint.jsonl (laid down by the
Task L1 grid), so this is a pure re-read: NO new simulation is performed.

Writes NEW files; does not overwrite the existing figure.
  -> 06_audit/Figure4_primary_anchor.png / .pdf
  -> 06_audit/figure4_primary_anchor_values.json

Style follows 05_manuscript/taskM_figures.py (validated palette, print-safe).
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "06_audit")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

B_PRIMARY = 0.584          # Doesch 2007, design-selected primary anchor
B_SUPERSEDED = 0.312       # what the published Figure 4 used
STATE = "control"

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8880", "#dcdbd6"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
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


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    res.setdefault((r["state"], round(r["b_cal"], 6),
                    round(r["b_f"], 6)), {})[r["model"]] = r["bpm"]

pop = sorted(m for m, v in res[(STATE, 0.0, 0.0)].items() if v is not None)
n = len(pop)


def complete(bc, bf):
    d = res.get((STATE, round(bc, 6), round(bf, 6)))
    return d is not None and all(m in d for m in pop)


def fails(bc, bf):
    d = res[(STATE, round(bc, 6), round(bf, 6))]
    return {m for m in pop if d.get(m) is None}


def series(bf):
    rungs = sorted({k[1] for k in res if k[0] == STATE
                    and complete(k[1], bf) and complete(k[1], 0.0)})
    B = fails(0.0, bf)
    PB = len(B) / n
    rows = []
    for bc in rungs:
        A = fails(bc, 0.0)
        AB = fails(bc, bf)
        surv = {m for m in pop if m not in A and m not in B}
        k = len(AB & surv)
        PA, PAB = len(A) / n, len(AB) / n
        Pexp = PA + PB - PA * PB
        lo, hi = wilson(len(AB), n)
        EPS = 1e-9
        if len(AB) == 0 and PA < EPS and PB < EPS:
            cls = "no events"
        elif Pexp > 0.95 or PAB > 0.95:
            cls = "ceiling"
        elif Pexp < lo - EPS:
            cls = "SUPER-ADDITIVE"
        elif Pexp > hi + EPS:
            cls = "SUB-ADDITIVE"
        else:
            cls = "additive"
        elo, ehi = wilson(k, n)
        resc = len((A | B) - AB) / n
        rows.append({"block": bc, "P_A": PA, "P_B": PB, "P_AB": PAB,
                     "EAR": k / n, "EAR_ci": [elo, ehi], "EAR_k": k,
                     "bliss_expected": Pexp, "bliss_class": cls,
                     "rescue": resc})
    return rows


prim = series(B_PRIMARY)
supe = series(B_SUPERSEDED)
supe = [r for r in supe if r["block"] <= max(x["block"] for x in prim)]

x = [r["block"] * 100 for r in prim]
ear = [r["EAR"] * 100 for r in prim]
lo = [r["EAR_ci"][0] * 100 for r in prim]
hi = [r["EAR_ci"][1] * 100 for r in prim]
cls = [r["bliss_class"] for r in prim]
resc = max(r["rescue"] for r in prim)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.4, 4.5), sharex=True,
                               gridspec_kw={"height_ratios": [2.3, 1]})
ax1.grid(zorder=0)
ax1.fill_between(x, lo, hi, color=BLUE, alpha=0.16, lw=0, zorder=2,
                 label="95% CI")
ax1.plot(x, ear, color=BLUE, lw=2.0, marker="o", markersize=4,
         markerfacecolor="white", markeredgewidth=1.0, zorder=4,
         label="primary anchor, $I_f$ 58.4%")
ax1.plot([r["block"] * 100 for r in supe], [r["EAR"] * 100 for r in supe],
         color=MUTED, lw=1.3, ls=(0, (4, 2)), marker="s", markersize=3,
         markerfacecolor="white", markeredgewidth=0.8, zorder=3,
         label="superseded anchor, $I_f$ 31.2%")
ax1.set_ylabel("excess absolute risk (%)")
ax1.set_title("Paired EAR is well behaved", loc="left", pad=8)
ax1.text(0.03, 0.62, f"rescue fraction = {resc:.3f}\nat every rung\n"
                     "(endpoint is monotone)", transform=ax1.transAxes,
         ha="left", va="top", fontsize=7, color=INK2)
ax1.legend(frameon=False, loc="upper left", handlelength=2.2)
ax1.text(-0.15, 1.06, "A", transform=ax1.transAxes, fontsize=10,
         fontweight="bold", va="top", color=INK)

ymap = {"additive": 0, "SUPER-ADDITIVE": 1, "SUB-ADDITIVE": -1,
        "no events": 0, "ceiling": 0}
yv = [ymap.get(c, 0) for c in cls]
ax2.grid(axis="x", zorder=0)
ax2.axhline(0, color=MUTED, lw=0.8, zorder=1)
ax2.plot(x, yv, color=INK2, lw=1.0, ls=(0, (2, 2)), zorder=3)
for xi, yi, c in zip(x, yv, cls):
    sup = (c == "SUPER-ADDITIVE")
    ax2.plot(xi, yi, marker="s" if sup else "o", markersize=7,
             color=ORANGE if sup else AQUA, markeredgecolor="white",
             markeredgewidth=0.9, zorder=5)
ax2.set_yticks([0, 1], ["Bliss\nadditive", "Bliss\nSUPER-\nADDITIVE"])
ax2.set_ylim(-0.55, 1.55)
ax2.set_xlabel("verapamil $I_{CaL}$ block (%)")
ax2.set_title("Bliss classification along the same ladder", loc="left", pad=8)
ax2.text(-0.15, 1.10, "B", transform=ax2.transAxes, fontsize=10,
         fontweight="bold", va="top", color=INK)

fig.text(0.5, -0.115,
         "verapamil $\\times$ ivabradine act on DIFFERENT channels: the model "
         "contains\nno mechanistic interaction, so every departure from Bliss "
         "is threshold geometry.\nIvabradine fixed at the PRIMARY 58.4% anchor; "
         "verapamil laddered.",
         ha="center", fontsize=6.8, color=MUTED)
fig.tight_layout(h_pad=1.6)
p = os.path.join(DEST, "Figure4_primary_anchor.png")
fig.savefig(p, bbox_inches="tight")
fig.savefig(p.replace(".png", ".pdf"), bbox_inches="tight")
plt.close(fig)

json.dump({"state": STATE, "n": n, "primary_block": B_PRIMARY,
           "superseded_block": B_SUPERSEDED,
           "primary_rows": prim, "superseded_rows": supe},
          open(os.path.join(DEST, "figure4_primary_anchor_values.json"), "w",
               encoding="utf-8"), indent=2)

print(f"n = {n}, rungs = {len(prim)}")
print(f"{'block':>7s} {'P_A':>6s} {'P_B':>6s} {'P_AB':>6s} {'EAR':>6s} "
      f"{'class PRIMARY':>16s} | {'class SUPERSEDED':>16s}")
sup_map = {r["block"]: r for r in supe}
for r in prim:
    s = sup_map.get(r["block"])
    print(f"{r['block']:7.1%} {r['P_A']:6.3f} {r['P_B']:6.3f} {r['P_AB']:6.3f} "
          f"{r['EAR']:6.3f} {r['bliss_class']:>16s} | "
          f"{(s['bliss_class'] if s else '-'):>16s}")
print(f"\nrescue fraction max = {resc:.4f}")
print(f"-> {p}")
