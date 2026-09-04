"""Task N - PK/PD decomposition and external comparison under the PRIMARY anchor.

The manuscript reports EAR under the Doesch primary anchor but still carries the
beats/min decomposition and the SmPC comparison from the superseded 36-month
anchor. This brings the latter two onto the primary anchor.

ANALYSIS ONLY. Every condition required already exists in
taskG_pair_checkpoint.jsonl (verified in N1); no simulation is run, nothing is
fitted, and no pair result informs any parameter.

Anchors, all three reported as a band wherever the manuscript reports one.
Exposure scaling: keep the in vitro Hill slope n = 0.80 and re-solve the IC50
through the empirical anchor at the clinical free Cmax of 12.2 nM (N4).

The comparison point for chronic steady-state dosing is the PRE-SPECIFIED
time-average free concentration (config comparison_point). Cmax is reported as
a labelled sensitivity and is never promoted to primary.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

HILL_IVAB, CMAX_IVAB, IC50_INVITRO = 0.80, 12.2, 2000.0
IC50_V, HILL_V, MW_V, FU_V = 198.7, 1.09, 454.6, 0.104

ANCHORS = [("Doesch 2007 (PRIMARY)", 0.584),
           ("10-year cohort", 0.509),
           ("36-month (superseded)", 0.312)]

# Verapamil rungs, matched to Task I so the two decompositions are directly
# comparable. Block -> total plasma via the Hill inverse and f_unbound.
RUNGS = [0.0, 0.029, 0.05, 0.10, 0.14, 0.20, 0.30]

# 240 mg/day comparison points (FDA label, via Task H).
#   time-average  35 ng/mL -> free  8.01 nM -> 2.9% block   <- PRE-SPECIFIED
#   Cmax         164 ng/mL -> free 37.52 nM -> 14.0% block  <- sensitivity
CMP_240 = {"time-average (PRIMARY)": 0.029, "Cmax (sensitivity)": 0.14}
SMPC_OBSERVED_BPM = -5.0


def ic50_from_anchor(b1, n=HILL_IVAB, c1=CMAX_IVAB):
    return c1 / ((b1 / (1.0 - b1)) ** (1.0 / n))


def block_at(c, ic50, n=HILL_IVAB):
    x = (c / ic50) ** n
    return x / (1.0 + x)


def total_ng(block):
    if block <= 0:
        return 0.0
    free = IC50_V * (block / (1.0 - block)) ** (1.0 / HILL_V)
    return free / FU_V * MW_V / 1000.0


# ------------------------------------------------------------------ load
res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    res.setdefault((r["state"], round(r["b_cal"], 6),
                    round(r["b_f"], 6)), {})[r["model"]] = r["bpm"]
pops = {st: sorted(m for m, v in res[(st, 0.0, 0.0)].items() if v is not None)
        for st in ("control", "iso")}

report = {"hill_slope": HILL_IVAB, "cmax_free_nM": CMAX_IVAB,
          "smpc_observed_bpm": SMPC_OBSERVED_BPM, "anchors": {},
          "N4_hill": {}, "N2_decomposition": {}, "N3_external": {}}

# =====================================================================
# N4 - re-derive the IC50 through the primary anchor; consistency check
# =====================================================================
print("=" * 100)
print("N4 - Hill-shape assumption, re-derived at the PRIMARY anchor")
print("=" * 100)
print("Construction: keep the IN VITRO Hill slope n = 0.80; discard the in "
      "vitro potency;")
print("re-solve IC50 so the curve passes through the EMPIRICAL anchor at free "
      f"Cmax {CMAX_IVAB} nM.")
print("ASSUMPTION CARRIED FORWARD: this treats the empirical and in vitro "
      "curves as differing")
print("by a HORIZONTAL SHIFT ONLY. The 250x gap is unexplained, so the true "
      "shape is unknown.")
print()
arms = {}
for label, b1 in ANCHORS:
    ic = ic50_from_anchor(b1)
    back = block_at(CMAX_IVAB, ic)          # consistency check
    # Snap to the 4-dp grid the simulations were actually run on. The runners
    # rounded the derived block to 4 decimals before use, so the store is keyed
    # on e.g. 0.7097 while the closed form gives 0.70966. The discrepancy is
    # < 1e-4 in block; snapping guarantees we read the condition that was run
    # rather than silently missing it.
    a = {f"{f}x": round(block_at(CMAX_IVAB * f, ic), 4) for f in (1, 2, 3)}
    arms[label] = a
    fold = IC50_INVITRO / ic
    report["anchors"][label] = {"block_1x": b1, "ic50_resolved_nM": ic,
                                "consistency_recovered_block": back,
                                "abs_error": abs(back - b1),
                                "fold_gap_vs_invitro": fold, "arms": a}
    print(f"  {label}")
    print(f"    IC50 = {CMAX_IVAB} / ({b1:.4f}/{1-b1:.4f})^(1/{HILL_IVAB}) "
          f"= {ic:.4f} nM   ({fold:.0f}x below in vitro {IC50_INVITRO:.0f} nM)")
    print(f"    consistency: b({CMAX_IVAB} nM) = {back:.6f} vs anchor "
          f"{b1:.6f}  ->  |error| {abs(back-b1):.2e}")
    print(f"    arms: 1x {a['1x']:.4f}   2x {a['2x']:.4f}   3x {a['3x']:.4f}")
print()
print("  Hill sensitivity at the PRIMARY anchor (same anchor, different slope):")
print(f"  {'n':>5s} {'IC50 (nM)':>11s} {'1x':>8s} {'2x':>8s} {'3x':>8s}")
hs = {}
for n in (0.6, 0.8, 1.0, 1.2):
    ic = ic50_from_anchor(0.584, n=n)
    row = {f"{f}x": block_at(CMAX_IVAB * f, ic, n=n) for f in (1, 2, 3)}
    hs[n] = {"ic50_nM": ic, **row}
    mark = "  <- used" if abs(n - HILL_IVAB) < 1e-9 else ""
    print(f"  {n:5.1f} {ic:11.3f} {row['1x']:8.4f} {row['2x']:8.4f} "
          f"{row['3x']:8.4f}{mark}")
report["N4_hill"]["sensitivity_primary_anchor"] = hs
print()
print("  The 1x column is invariant by construction (the curve is re-solved "
      "through the anchor);")
print("  the slope choice moves only the EXTRAPOLATED 2x and 3x arms.")

# =====================================================================
# N2 - decomposition, referenced to ivabradine alone at 1x
# =====================================================================
print()
print("=" * 100)
print("N2 - PK/PD decomposition under each anchor (bpm, vs ivabradine alone "
      "at 1x)")
print("=" * 100)

for state in ("control", "iso"):
    pop = pops[state]
    base = {m: res[(state, 0.0, 0.0)][m] for m in pop}
    print(f"\nSTATE = {state.upper()}  (n = {len(pop)} drug-free pacing)")
    for label, b1 in ANCHORS:
        a = arms[label]
        keys = [(0.0, a["1x"]), (0.0, a["2x"]), (0.0, a["3x"])]
        print(f"\n  --- {label}   I_f arms "
              f"{a['1x']:.1%} / {a['2x']:.1%} / {a['3x']:.1%} ---")
        print(f"  {'verap':>7s} {'ng/mL':>8s} {'n':>4s} | {'PK only':>9s} "
              f"{'PD only':>9s} | {'PK+PD 2x':>9s} {'PK+PD 3x':>9s}")
        rows = []
        for bc in RUNGS:
            need = keys + [(bc, a["1x"]), (bc, a["2x"]), (bc, a["3x"])]
            cohort = [m for m in pop
                      if all(res[(state, round(x, 6), round(y, 6))].get(m)
                             for x, y in need)]
            if not cohort:
                continue

            def med(x, y):
                d = res[(state, round(x, 6), round(y, 6))]
                return float(np.median([d[m] - base[m] for m in cohort]))

            ref = med(0.0, a["1x"])
            row = {"block": bc, "total_ng_per_mL": total_ng(bc),
                   "n_cohort": len(cohort), "dHR_ref_ivab_1x": ref,
                   "PK_only": med(0.0, a["2x"]) - ref,
                   "PD_only": med(bc, a["1x"]) - ref,
                   "PK_plus_PD_2x": med(bc, a["2x"]) - ref,
                   "PK_plus_PD_3x": med(bc, a["3x"]) - ref}
            rows.append(row)
            print(f"  {bc:7.1%} {total_ng(bc):8.1f} {len(cohort):4d} | "
                  f"{row['PK_only']:+9.2f} {row['PD_only']:+9.2f} | "
                  f"{row['PK_plus_PD_2x']:+9.2f} {row['PK_plus_PD_3x']:+9.2f}")
        report["N2_decomposition"].setdefault(state, {})[label] = rows

        # rank swap across the licensed dose range
        lo = next(r for r in rows if abs(r["block"] - 0.029) < 1e-9)
        hi = next(r for r in rows if abs(r["block"] - 0.30) < 1e-9)
        s_lo = "PK" if abs(lo["PK_only"]) > abs(lo["PD_only"]) else "PD"
        s_hi = "PK" if abs(hi["PK_only"]) > abs(hi["PD_only"]) else "PD"
        print(f"    at 240 mg/day time-average (2.9% block): PK "
              f"{lo['PK_only']:+.2f} vs PD {lo['PD_only']:+.2f}  -> "
              f"{s_lo} larger")
        print(f"    at 480 mg/day peak       (30.0% block): PK "
              f"{hi['PK_only']:+.2f} vs PD {hi['PD_only']:+.2f}  -> "
              f"{s_hi} larger")
        print(f"    RANK SWAP across the licensed range: "
              f"{'YES' if s_lo != s_hi else 'NO'}")
        report["N2_decomposition"][state][label + "__ranks"] = {
            "low_dose_larger": s_lo, "high_dose_larger": s_hi,
            "rank_swap": s_lo != s_hi,
            "low": {"PK": lo["PK_only"], "PD": lo["PD_only"]},
            "high": {"PK": hi["PK_only"], "PD": hi["PD_only"]}}

# =====================================================================
# N3 - external comparison vs the SmPC -5 bpm
# =====================================================================
print()
print("=" * 100)
print("N3 - external comparison: verapamil 240 mg/day + ivabradine vs the "
      "reported -5 bpm")
print("=" * 100)
print("Observed: verapamil 120 mg bid (= 240 mg/day) raises ivabradine "
      "exposure ~2-fold and the")
print("combination gives an ADDITIONAL heart-rate reduction of "
      f"{SMPC_OBSERVED_BPM:+.0f} bpm vs ivabradine alone.")
print("Matching model contrast: PK+PD 2x  (it contains both the exposure rise "
      "and verapamil's own")
print("PD effect, exactly as the clinical study did).")
print()
for state in ("control", "iso"):
    print(f"  STATE = {state.upper()}")
    print(f"  {'anchor':24s} {'comparison point':22s} {'block':>7s} "
          f"{'predicted':>10s} {'observed':>9s} {'ratio':>7s}")
    for label, b1 in ANCHORS:
        rows = report["N2_decomposition"][state][label]
        for cname, bc in CMP_240.items():
            r = next((x for x in rows if abs(x["block"] - bc) < 1e-9), None)
            if r is None:
                continue
            pred = r["PK_plus_PD_2x"]
            ratio = pred / SMPC_OBSERVED_BPM
            print(f"  {label:24s} {cname:22s} {bc:7.1%} {pred:+10.2f} "
                  f"{SMPC_OBSERVED_BPM:+9.1f} {ratio:7.2f}")
            report["N3_external"].setdefault(state, {}).setdefault(
                label, {})[cname] = {"block": bc, "predicted_bpm": pred,
                                     "observed_bpm": SMPC_OBSERVED_BPM,
                                     "ratio_pred_over_obs": ratio}
    print()
print("  Trough is NOT a third point here: the label publishes no 24-h trough "
      "for 240 mg, so the")
print("  band's lower edge IS the AUC-derived time-average. Labelled "
      "EXPOSURE-STATISTIC-LIMITED.")

with open(os.path.join(OUT, "taskN_primary_anchor.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskN_primary_anchor.json')}")
