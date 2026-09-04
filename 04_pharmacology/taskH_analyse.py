"""Task H analysis - verapamil x ivabradine across CHRONIC ORAL exposure.

Calibration exposure != evaluation exposure. Schulman's 4 mg IV anchors the
concentration-block relationship (Task G); chronic oral dosing is the clinical
question and reaches far higher free concentrations.

Ivabradine stays FIXED at its 31.2% monotherapy anchor. Nothing is
retro-calibrated. Task D's 3.5x over-block figure is NOT used - it was derived
against closed-loop data and is retired.

Axis construction
-----------------
Simulated rungs are BLOCK fractions. The Hill equation is inverted to report
which free verapamil concentration produces each simulated block, under each of
the two IC50 choices. Every endpoint therefore sits on a simulated rung and no
bpm curve is interpolated across a quiescence threshold.

    b = (c/IC50)^n / (1 + (c/IC50)^n)   ->   c = IC50 * (b/(1-b))^(1/n)

IC50 choices
    Ba2+-derived  198.7 nM   Crumb 2016 (J Pharmacol Toxicol Methods 81:251-262,
                             doi 10.1016/j.vascn.2016.03.009); Cav1.2 measured
                             with 1.8 mM CaCl2 replaced by 4 mM BaCl2.
    Ca2+-corrected 47.3 nM   Ba2+ removes Ca2+-dependent inactivation and so
                             depletes the high-affinity inactivated state that
                             verapamil prefers (Kanaya 1983, PMID 6304329).
                             Nawrath & Wegener 1997 (PMID 9007846) measured the
                             gap directly: 3 uM verapamil cut ICa by 57+-6% but
                             IBa by only 24+-4%, giving IC50(Ba)/IC50(Ca) ~ 4.2.
                             198.7 / 4.2 = 47.3 nM.
    The Ba2+ value is the one the whole project has used; the Ca2+-corrected
    value is the more physiological charge carrier. Both are reported because
    the choice determines where chronic dosing lands on the failure curve.

Clinical exposure bands (FDA label, verapamil HCl extended-release tablets USP,
DailyMed; ~90% protein bound, consistent with Keefe 1981 PMID 6970111 f_u 10.4%)
    240 mg/day : AUC(0-24) 841 ng.hr/mL fed -> 35 ng/mL time-average;
                 Cmax 164 ng/mL fasting.  Band taken as 35-164 ng/mL.
                 The label publishes no 24-h trough for 240 mg; the true trough
                 is BELOW the 35 ng/mL time-average, so this band's lower end is
                 an over-estimate - conservative in the direction of
                 over-predicting risk.
    480 mg/day : "Chronic oral administration of 120 mg of verapamil
                 hydrochloride every 6 hours resulted in plasma levels of
                 verapamil ranging from 125 to 400 ng/mL." Band = 125-400 ng/mL.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

B_IVAB = 0.312
HILL = 1.09
MW = 454.6
FU = 0.104

IC50S = {"Ba2+-derived (198.7 nM)": 198.7,
         "Ca2+-corrected (47.3 nM)": 198.7 / 4.2}

BANDS = {"240 mg/day": (35.0, 164.0), "480 mg/day": (125.0, 400.0)}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def conc_from_block(b, ic50):
    if b <= 0:
        return 0.0
    if b >= 1:
        return float("inf")
    return ic50 * (b / (1.0 - b)) ** (1.0 / HILL)


def free_band(tot_lo, tot_hi):
    return (tot_lo / MW * 1000 * FU, tot_hi / MW * 1000 * FU)


# --------------------------------------------------------------------- load
res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    k = (r["state"], round(r["b_cal"], 6), round(r["b_f"], 6))
    res.setdefault(k, {})[r["model"]] = r["bpm"]


def _complete(state, b, bf, models):
    """A rung counts only if EVERY model has a checkpoint entry.

    This distinguishes 'absent from the checkpoint' from 'present with
    bpm = None'. Absent means not yet simulated; None means simulated and
    quiescent. Reading absent as quiescent would silently invent failures in a
    rung that is still being written, which is exactly what a partially
    completed background run looks like.
    """
    d = res.get((state, b, bf))
    return d is not None and all(m in d for m in models)


# Population identity comes from the drug-free arm of each state, which is
# always complete before anything else is analysed.
_pops = {}
for _st in ("control", "iso"):
    _free = res[(_st, 0.0, 0.0)]
    _pops[_st] = sorted(m for m, v in _free.items() if v is not None)

_all_b = sorted({k[1] for k in res})
rungs_by_state = {
    st: [b for b in _all_b
         if _complete(st, b, 0.0, _pops[st]) and _complete(st, b, B_IVAB, _pops[st])]
    for st in ("control", "iso")}
rungs = sorted(set(rungs_by_state["control"]) & set(rungs_by_state["iso"]))
_skipped = sorted(set(_all_b) - set(rungs))
if _skipped:
    print(f"[incomplete rungs skipped: "
          f"{', '.join(f'{b:.1%}' for b in _skipped)}]")

print("=" * 108)
print("TASK H - verapamil x ivabradine across the chronic oral exposure range")
print("=" * 108)
print(f"ivabradine FIXED at I_f block {B_IVAB:.1%} (36-month transplant anchor)")
print(f"human f_unbound {FU:.1%};  Hill n = {HILL};  simulated rungs: "
      f"{len(rungs)} I_CaL block levels, {rungs[0]:.1%} - {rungs[-1]:.1%}")
print("\nClinical free-concentration bands (FDA label total x f_u):")
for lbl, (lo, hi) in BANDS.items():
    f = free_band(lo, hi)
    print(f"  {lbl:12s} total {lo:6.0f} - {hi:6.0f} ng/mL "
          f"-> free {f[0]:6.2f} - {f[1]:6.2f} nM")
print("\nI_CaL block reached by each band, per IC50 choice:")
band_blocks = {}
for name, ic50 in IC50S.items():
    for lbl, (lo, hi) in BANDS.items():
        f = free_band(lo, hi)
        b = [(x / ic50) ** HILL / (1 + (x / ic50) ** HILL) for x in f]
        band_blocks[(name, lbl)] = b
        print(f"  {name:26s} {lbl:12s} block {b[0]:6.1%} - {b[1]:6.1%}")

report = {"B_ivabradine": B_IVAB, "hill": HILL, "f_unbound": FU,
          "ic50_nM": IC50S, "bands_total_ng_per_mL": BANDS,
          "bands_free_nM": {k: list(free_band(*v)) for k, v in BANDS.items()},
          "band_blocks": {f"{a}|{b}": v for (a, b), v in band_blocks.items()},
          "states": {}}

for state in ("control", "iso"):
    free = res[(state, 0.0, 0.0)]
    pop = _pops[state]
    n = len(pop)
    base = {m: free[m] for m in pop}

    print("\n" + "=" * 108)
    print(f"STATE = {state.upper()}   "
          f"(n = {n}/188 pacing drug-free, median "
          f"{np.median(list(base.values())):.1f} bpm)")
    print("=" * 108)
    hdr_ic = "".join(f"{'free nM ' + k.split()[0]:>16s}" for k in IC50S)
    print(f"  {'block':>6s} {'P_A':>6s} {'P_B':>6s} {'P_AB':>6s} "
          f"{'EAR':>7s} {'EAR 95% CI':>16s} {'dHR':>8s} |{hdr_ic}")

    def fails(key):
        d = res[key]
        return {m for m in pop if d.get(m) is None}

    B_only = fails((state, 0.0, B_IVAB))
    PB = len(B_only) / n
    rows = []
    for b in rungs:
        A_only = fails((state, b, 0.0))
        AB = fails((state, b, B_IVAB))
        PA, PAB = len(A_only) / n, len(AB) / n
        surv_both = {m for m in pop if m not in A_only and m not in B_only}
        k_ear = len(AB & surv_both)
        ear = k_ear / n
        lo_e, hi_e = wilson(k_ear, n)
        surv = [m for m in pop if res[(state, b, B_IVAB)].get(m)]
        dhr = (float(np.median([res[(state, b, B_IVAB)][m] - base[m]
                                for m in surv])) if surv else None)
        cs = {name: conc_from_block(b, ic50) for name, ic50 in IC50S.items()}
        marks = []
        for (name, lbl), bb in band_blocks.items():
            if bb[0] <= b <= bb[1]:
                marks.append(f"{lbl.split()[0]}/{name.split('-')[0][:2]}")
        cstr = "".join(f"{cs[k]:16.2f}" for k in IC50S)
        print(f"  {b:6.1%} {PA:6.3f} {PB:6.3f} {PAB:6.3f} {ear:7.3f} "
              f"[{lo_e:5.3f},{hi_e:5.3f}] "
              f"{(f'{dhr:+8.2f}' if dhr is not None else '     n/a')} |{cstr}"
              + (("  <- " + ", ".join(marks)) if marks else ""))
        rows.append({"block": b, "P_A": PA, "P_B": PB, "P_AB": PAB,
                     "EAR_paired": ear, "EAR_ci": [lo_e, hi_e],
                     "EAR_k": k_ear, "median_dHR_pair": dhr,
                     "free_nM": {k: cs[k] for k in IC50S},
                     "in_bands": marks})

    # ---- thresholds -----------------------------------------------------
    print(f"\n  EAR thresholds ({state}):")
    th = {}
    for mark in (0.05, 0.10):
        pt = next((r for r in rows if r["EAR_paired"] > mark), None)
        ci = next((r for r in rows if r["EAR_ci"][0] > mark), None)
        th[f"{mark:.0%}"] = {}
        for tag, r in (("point estimate", pt), ("95% CI lower bound", ci)):
            if r is None:
                print(f"    EAR > {mark:.0%} ({tag:19s}): NOT REACHED up to "
                      f"{rungs[-1]:.0%} block")
                th[f"{mark:.0%}"][tag] = None
                continue
            cs = r["free_nM"]
            print(f"    EAR > {mark:.0%} ({tag:19s}): first at "
                  f"{r['block']:.1%} block, EAR {r['EAR_paired']:.1%}")
            for name in IC50S:
                tot = cs[name] / FU * MW / 1000
                inb = [lbl for lbl, (lo, hi) in BANDS.items()
                       if free_band(lo, hi)[1] >= cs[name]]
                print(f"        -> free {cs[name]:7.2f} nM "
                      f"({tot:7.1f} ng/mL total) under {name:26s}"
                      f"  reached by: "
                      + (", ".join(inb) if inb else "NEITHER regimen"))
            th[f"{mark:.0%}"][tag] = {
                "block": r["block"], "EAR": r["EAR_paired"],
                "free_nM": cs,
                "total_ng_per_mL": {k: cs[k] / FU * MW / 1000 for k in cs},
                "regimens_reaching": {
                    k: [lbl for lbl, (lo, hi) in BANDS.items()
                        if free_band(lo, hi)[1] >= cs[k]] for k in cs}}
    report["states"][state] = {"n": n, "rows": rows, "thresholds": th,
                               "median_bpm_drugfree":
                                   float(np.median(list(base.values())))}

with open(os.path.join(OUT, "taskH_exposure.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskH_exposure.json')}")
