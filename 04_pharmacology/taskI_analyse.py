"""Task I analysis - does the CYP3A4 PK interaction account for the hazard?

Task H measured the PD convergence at the SAN with ivabradine held at its 31.2%
monotherapy anchor, and found the excess absolute risk small across the whole
chronic oral verapamil range. Task I raises ivabradine's effective I_f block to
reflect the CYP3A4-mediated exposure increase and re-runs the same ladder, so
the PK and PD contributions can be read separately.

Ivabradine arms (derivation in taskI_pk_interaction.py docstring):
    b(c) = (c/32.78)^0.80 / (1 + (c/32.78)^0.80)
    where IC50 = 32.78 nM is re-solved so the curve passes through the
    EMPIRICAL anchor (31.2% block at free 12.2 nM), keeping the in vitro
    Hill slope n = 0.80. Reproduces Task F's implied IC50 of 32.8 nM.

    1x  12.2 nM -> 31.20%   anchor, = Task H
    2x  24.4 nM -> 44.12%   verapamil/diltiazem, MODERATE CYP3A4 inhibitor
    3x  36.6 nM -> 52.20%   upper end of the labelled 2-3x range
    7x  85.4 nM -> 68.27%   ketoconazole-equivalent STRONG inhibitor.
                            BOUNDING ARM ONLY - not verapamil. Included to test
                            whether the model reproduces the regulatory gradient
                            between "avoid" (moderate) and "contraindicated"
                            (strong).

Verapamil: Ba2+-derived mapping ONLY (IC50 198.7 nM, Hill 1.09, f_u 10.4%).
The Ca2+-corrected arm is retired - Task H showed it self-falsifies at the
monotherapy level.

Chronic oral Ba2+ bands (FDA label totals x f_u), from Task H:
    240 mg/day   35-164 ng/mL  ->  free  8.0-37.5 nM  ->  I_CaL block  2.9-14.0%
    480 mg/day  125-400 ng/mL  ->  free 28.6-91.5 nM  ->  I_CaL block 10.8-30.0%
Both band edges are simulated rungs, so the "does it cross inside the band"
question is answered without interpolation.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

ARMS = [(0.312, "1x  (31.20%)  Task H anchor"),
        (0.4412, "2x  (44.12%)  moderate CYP3A4 inh."),
        (0.5220, "3x  (52.20%)  moderate, upper end"),
        (0.6827, "7x  (68.27%)  STRONG inh., bounding")]

IC50_V, HILL_V, MW, FU = 198.7, 1.09, 454.6, 0.104
BANDS = {"240 mg/day": (0.029, 0.140), "480 mg/day": (0.108, 0.300)}
BAND_NG = {"240 mg/day": (35.0, 164.0), "480 mg/day": (125.0, 400.0)}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def conc_from_block(b):
    if b <= 0:
        return 0.0
    return IC50_V * (b / (1.0 - b)) ** (1.0 / HILL_V)


res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    res.setdefault((r["state"], round(r["b_cal"], 6),
                    round(r["b_f"], 6)), {})[r["model"]] = r["bpm"]

pops = {}
for st in ("control", "iso"):
    free = res[(st, 0.0, 0.0)]
    pops[st] = sorted(m for m, v in free.items() if v is not None)


def complete(st, bc, bf):
    d = res.get((st, round(bc, 6), round(bf, 6)))
    return d is not None and all(m in d for m in pops[st])


# Drop any arm that is not yet fully simulated across every rung it needs,
# rather than silently scoring unwritten rows as quiescent.
_ver_rungs = sorted({k[1] for k in res if k[0] == "control"})
_ARMS = []
for _a, _l in ARMS:
    _ok = [b for b in _ver_rungs
           if all(complete(s, b, _a) for s in ("control", "iso"))]
    if len(_ok) >= 5:
        _ARMS.append((_a, _l))
    else:
        print(f"[arm not yet complete, excluded: {_l}  "
              f"({len(_ok)} rungs ready)]")
ARMS = _ARMS

print("=" * 112)
print("TASK I - PK/PD decomposition of the verapamil x ivabradine interaction")
print("=" * 112)
print("Ba2+ mapping only.  Ivabradine I_f block scaled by CYP3A4-mediated "
      "exposure increase.")
print("Chronic oral verapamil Ba2+ bands:")
for k, (lo, hi) in BANDS.items():
    print(f"  {k:12s} total {BAND_NG[k][0]:5.0f}-{BAND_NG[k][1]:5.0f} ng/mL "
          f"-> I_CaL block {lo:.1%} - {hi:.1%}")

report = {"arms": [{"b_f": a, "label": l} for a, l in ARMS],
          "bands_block": BANDS, "bands_ng_per_mL": BAND_NG, "states": {}}

for state in ("control", "iso"):
    pop = pops[state]
    n = len(pop)
    base = {m: res[(state, 0.0, 0.0)][m] for m in pop}
    rungs = sorted({k[1] for k in res if k[0] == state and complete(state, k[1], 0.0)
                    and all(complete(state, k[1], a) for a, _ in ARMS)})

    print("\n" + "=" * 112)
    print(f"STATE = {state.upper()}   (n = {n}/188 drug-free pacing, median "
          f"{np.median(list(base.values())):.1f} bpm)")
    print("=" * 112)

    def fails(bc, bf):
        d = res[(state, round(bc, 6), round(bf, 6))]
        return {m for m in pop if d.get(m) is None}

    # ---- EAR matrix -----------------------------------------------------
    print("\nEXCESS ABSOLUTE RISK  (paces under each single, fails the pair)")
    print(f"  {'verap':>7s} {'free nM':>8s} {'P_A':>6s} |"
          + "".join(f"{l.split()[0]:>22s}" for _, l in ARMS) + "   band")
    print(f"  {'block':>7s} {'(Ba2+)':>8s} {'alone':>6s} |"
          + "".join(f"{'EAR   [95% CI]':>22s}" for _ in ARMS))
    rows = []
    for bc in rungs:
        A_only = fails(bc, 0.0)
        PA = len(A_only) / n
        cells, rec = [], {"block": bc, "free_nM": conc_from_block(bc),
                          "total_ng_per_mL": conc_from_block(bc) / FU * MW / 1000,
                          "P_A": PA, "arms": {}}
        for bf, lab in ARMS:
            B_only = fails(0.0, bf)
            AB = fails(bc, bf)
            surv = {m for m in pop if m not in A_only and m not in B_only}
            k_e = len(AB & surv)
            ear = k_e / n
            lo, hi = wilson(k_e, n)
            cells.append(f"{ear:8.3f} [{lo:5.3f},{hi:5.3f}]")
            rec["arms"][lab] = {"b_f": bf, "P_B": len(B_only) / n,
                                "P_AB": len(AB) / n, "EAR": ear,
                                "EAR_ci": [lo, hi], "EAR_k": k_e}
        inb = [k for k, (lo_, hi_) in BANDS.items() if lo_ <= bc <= hi_]
        rec["in_bands"] = inb
        rows.append(rec)
        print(f"  {bc:7.1%} {conc_from_block(bc):8.1f} {PA:6.3f} |"
              + "".join(f"{c:>22s}" for c in cells)
              + ("   " + ",".join(x.split()[0] for x in inb) if inb else ""))

    print(f"\n  ivabradine ALONE (verapamil block 0):")
    for bf, lab in ARMS:
        B_only = fails(0.0, bf)
        lo, hi = wilson(len(B_only), n)
        print(f"    {lab:34s} P_B = {len(B_only)/n:6.3f} "
              f"[{lo:.3f}, {hi:.3f}]")

    # ---- threshold crossings WITHIN each band ---------------------------
    print(f"\n  Threshold crossings INSIDE the clinical bands ({state}):")
    th = {}
    for band, (blo, bhi) in BANDS.items():
        th[band] = {}
        inband = [r for r in rows if blo <= r["block"] <= bhi]
        for bf, lab in ARMS:
            arm_key = lab
            best = max(inband, key=lambda r: r["arms"][arm_key]["EAR"])
            e = best["arms"][arm_key]
            c5 = [r for r in inband if r["arms"][arm_key]["EAR"] > 0.05]
            c10 = [r for r in inband if r["arms"][arm_key]["EAR"] > 0.10]
            c5ci = [r for r in inband if r["arms"][arm_key]["EAR_ci"][0] > 0.05]
            c10ci = [r for r in inband if r["arms"][arm_key]["EAR_ci"][0] > 0.10]
            th[band][arm_key] = {
                "max_EAR": e["EAR"], "max_EAR_ci": e["EAR_ci"],
                "at_block": best["block"],
                "at_total_ng_per_mL": best["total_ng_per_mL"],
                "crosses_5pct": bool(c5), "crosses_10pct": bool(c10),
                "crosses_5pct_ci": bool(c5ci), "crosses_10pct_ci": bool(c10ci)}
            print(f"    {band:12s} {lab:34s} max EAR {e['EAR']:6.1%} "
                  f"[{e['EAR_ci'][0]:.3f},{e['EAR_ci'][1]:.3f}] at "
                  f"{best['block']:5.1%} block | >5%: "
                  f"{'YES' if c5 else 'no':>3s} (CI {'YES' if c5ci else 'no':>3s})"
                  f" | >10%: {'YES' if c10 else 'no':>3s} "
                  f"(CI {'YES' if c10ci else 'no':>3s})")

    # ---- HR decomposition: PK contribution vs PD contribution -----------
    # EXTERNAL VALIDATION TARGET (Procoralan SmPC, EMA/MHRA):
    #   "the combination of ivabradine with the heart rate reducing agents
    #    diltiazem or verapamil resulted in an increase in ivabradine exposure
    #    (2 to 3 fold increase in AUC) and an additional heart rate reduction
    #    of 5 bpm."
    # That 5 bpm is measured against ivabradine ALONE and already contains BOTH
    # the PK effect (ivabradine exposure up 2-3x) and verapamil's own PD effect,
    # because the clinical study simply added the two drugs together. The
    # matching model contrast is therefore
    #     dHR(verapamil + ivabradine@2-3x)  -  dHR(ivabradine@1x)
    #
    # HARD RULE: this is a COMPARISON of a prediction against an observation.
    # No parameter is adjusted to it. Using a pair observation to VALIDATE is
    # exactly what the study design intends; using it to CALIBRATE would void
    # the endpoint, and nothing here does that.
    print(f"\n  HEART-RATE DECOMPOSITION ({state}), medians over models pacing "
          f"in every arm compared")
    print(f"    reference: ivabradine alone at 1x (31.20% I_f block)")
    print(f"  {'verap':>7s} | {'PK only':>9s} {'PD only':>9s} | "
          f"{'PK+PD 2x':>9s} {'PK+PD 3x':>9s}   (bpm vs ivabradine 1x alone)")
    dec = []
    for bc in rungs:
        def med(bcx, bfx, cohort):
            d = res[(state, round(bcx, 6), round(bfx, 6))]
            v = [d[m] - base[m] for m in cohort]
            return float(np.median(v)) if v else None
        # cohort = models pacing in every arm entering the comparison
        keys = [(0.0, 0.312), (0.0, 0.4412), (0.0, 0.5220),
                (bc, 0.312), (bc, 0.4412), (bc, 0.5220)]
        cohort = [m for m in pop
                  if all(res[(state, round(a, 6), round(b, 6))].get(m)
                         for a, b in keys)]
        if not cohort:
            continue
        ref = med(0.0, 0.312, cohort)
        pk2 = med(0.0, 0.4412, cohort) - ref
        pd_ = med(bc, 0.312, cohort) - ref
        both2 = med(bc, 0.4412, cohort) - ref
        both3 = med(bc, 0.5220, cohort) - ref
        print(f"  {bc:7.1%} | {pk2:+9.2f} {pd_:+9.2f} | "
              f"{both2:+9.2f} {both3:+9.2f}")
        dec.append({"block": bc, "n_cohort": len(cohort),
                    "dHR_ref_ivab1x": ref, "PK_only_2x": pk2, "PD_only": pd_,
                    "PK_plus_PD_2x": both2, "PK_plus_PD_3x": both3})

    report["states"][state] = {"n": n, "rows": rows, "band_thresholds": th,
                               "hr_decomposition": dec,
                               "smpc_observed_additional_bpm": -5.0}

with open(os.path.join(OUT, "taskI_pk_interaction.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskI_pk_interaction.json')}")
