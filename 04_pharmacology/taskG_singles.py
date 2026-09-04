"""Task G1 + G2 - the two single-drug anchors. NO PAIR DATA IS READ HERE.

G1  Dog plasma protein binding for verapamil - the one number the Task F
    verdict turned on.
      Keefe DL, Yee YG, Kates RE. Verapamil protein binding in patients and in
      normal subjects. Clin Pharmacol Ther 1981;29(1):21-6. PMID 6970111.
      "Plasma protein binding of verapamil in mongrel dogs (mean = 90.7%)"
      measured in the SAME assay that gave 89.6 +/- 0.17% in normal humans.
      -> dog f_unbound = 9.3%     human f_unbound = 10.4%
    Cross-check: Belpaire FM et al., J Pharm Pharmacol 1990;42(1):45-9,
      PMID 1969949: "The binding of verapamil was ca 85%" in dogs
      -> f_unbound 15%. Belpaire is the looser of the two; Keefe is the
      purpose-built binding study and measures dog and human side by side.

G2  Verapamil recalibrated against Schulman (human, denervated, n=13) and
    ivabradine against the 36-month transplant anchor.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")

IC50, HILL, MW = 198.7, 1.09, 454.6
QI_PLASMA = (98.0, 204.0)          # dog, Qi 0.2 mg/kg IV + infusion

FU_DOG_KEEFE = 0.093               # 1 - 0.907   PMID 6970111
FU_DOG_BELPAIRE = 0.15             # 1 - 0.85    PMID 1969949
FU_HUMAN = 0.104                   # 1 - 0.896   PMID 6970111

with open(os.path.join(OUT, "taskA_G_CaL_population_sweep.json"),
          encoding="utf-8") as f:
    cal = json.load(f)
recs, n = cal["records"], len(cal["records"])
grid = sorted(float(k) for k in recs[0]["levels"])
frac = {b: sum(1 for r in recs if r["levels"].get(str(b)) is None) / n
        for b in grid}


def wilson(k, nn, z=1.96):
    p = k / nn
    d = 1 + z * z / nn
    c = (p + z * z / (2 * nn)) / d
    h = z * np.sqrt(p * (1 - p) / nn + z * z / (4 * nn * nn)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def block(c_free):
    x = (c_free / IC50) ** HILL
    return x / (1 + x)


def failure(b):
    if b <= grid[0]:
        return frac[grid[0]]
    if b >= grid[-1]:
        return frac[grid[-1]]
    lo = max(g for g in grid if g <= b)
    hi = min(g for g in grid if g >= b)
    f = 0 if hi == lo else (b - lo) / (hi - lo)
    return frac[lo] + f * (frac[hi] - frac[lo])


def free_nM(total_ng_ml, fu):
    return total_ng_ml / MW * 1000 * fu


print("=" * 88)
print("G1 - DOG PLASMA PROTEIN BINDING FOR VERAPAMIL")
print("=" * 88)
print("  MEASURED, Keefe 1981 (PMID 6970111), mongrel dogs : 90.7% bound"
      f"  -> f_u = {FU_DOG_KEEFE:.1%}")
print("  same paper, normal humans, same assay             : 89.6% bound"
      f"  -> f_u = {FU_HUMAN:.1%}")
print("  cross-check, Belpaire 1990 (PMID 1969949), dogs   : ~85%  bound"
      f"  -> f_u = {FU_DOG_BELPAIRE:.1%}")
print("")
print("  Task F required f_u >= 20% to bring the model inside the 20-40%")
print("  pre-specified window. The measured dog value is 9.3%.")
print("")

print(f"  {'source':>28s} {'f_u':>6s} {'free nM':>15s} {'I_CaL block':>16s} "
      f"{'failure fraction':>18s} {'in 20-40%?':>11s}")
g1 = []
for lbl, fu in (("Keefe 1981 dog (MEASURED)", FU_DOG_KEEFE),
                ("Keefe 1981 human", FU_HUMAN),
                ("Belpaire 1990 dog", FU_DOG_BELPAIRE),
                ("what Task F needed", 0.20)):
    c = [free_nM(p, fu) for p in QI_PLASMA]
    b = [block(x) for x in c]
    fr = [failure(x) for x in b]
    hit = fr[1] >= 0.20 and fr[0] <= 0.40
    print(f"  {lbl:>28s} {fu:6.1%} {c[0]:6.1f}-{c[1]:6.1f} "
          f"{b[0]:7.1%}-{b[1]:6.1%} {fr[0]:8.1%}-{fr[1]:7.1%} "
          f"{'YES' if hit else 'no':>11s}")
    g1.append({"source": lbl, "f_unbound": fu, "free_nM": c,
               "block": b, "failure_fraction": fr, "in_window": bool(hit)})

lo10, hi10 = wilson(2, 10)
lo5, hi5 = wilson(2, 5)
fr_dog = [failure(block(free_nM(p, FU_DOG_KEEFE))) for p in QI_PLASMA]
print("")
print(f"  AT THE MEASURED DOG VALUE the model predicts "
      f"{fr_dog[0]:.1%} - {fr_dog[1]:.1%} automaticity failure.")
print(f"  Observed: 2/10 blockade = 20% (95% CI [{lo10:.1%}, {hi10:.1%}]);"
      f"  2/5 transplant = 40% (95% CI [{lo5:.1%}, {hi5:.1%}]).")
print(f"  Model upper prediction {fr_dog[1]:.1%} inside the 2/10 CI? "
      f"{lo10 <= fr_dog[1] <= hi10}")
print("  -> The free-fraction rescue is CLOSED. Task F stays INCONCLUSIVE on")
print("     the strength of n=10/n=5, not PASS.")

print("")
print("=" * 88)
print("G2 - VERAPAMIL vs SCHULMAN 1993 (PMID 7681901), human, denervated, n=13")
print("=" * 88)
print("  IV verapamil, median dose 4 mg, 13 recent heart-transplant recipients.")
print("  Reported: BP and HR both fell. Per-patient bpm magnitudes are")
print("  PAYWALLED and were not recoverable, so verapamil is carried as an")
print("  EXPOSURE LADDER rather than collapsed to one fitted block.")
print("")
print("  PK frame: Reiter 1982 (PMID 7124631) - 10 mg IV bolus over 2 min in a")
print("  regimen targeting 150 ng/mL; trough after the bolus 67 ng/mL;")
print("  maintenance 77-156 ng/mL. Dose-proportional scaling to 4 mg gives a")
print("  working window of roughly 25-80 ng/mL total over the measurement")
print(f"  period. Human f_u = {FU_HUMAN:.1%} (Keefe, MEASURED).")
print("")
print(f"  {'total ng/mL':>12s} {'free nM':>9s} {'I_CaL block':>12s} "
      f"{'pop. failure':>13s}")
g2 = []
for tot in (10, 25, 40, 60, 80, 120, 160, 200):
    cf = free_nM(tot, FU_HUMAN)
    b = block(cf)
    print(f"  {tot:12.0f} {cf:9.2f} {b:12.1%} {failure(b):13.1%}")
    g2.append({"total_ng_per_mL": tot, "free_nM": cf, "block": b,
               "failure_fraction": failure(b)})

b4 = [block(free_nM(t, FU_HUMAN)) for t in (25, 80)]
print("")
print(f"  => Schulman 4 mg IV maps to I_CaL block {b4[0]:.1%} - {b4[1]:.1%},")
print(f"     population automaticity failure "
      f"{failure(b4[0]):.1%} - {failure(b4[1]):.1%}.")
print("")
print("  ONE-SIDED OBSERVED CONSTRAINT. Schulman reports hemodynamics and")
print("  radionuclide angiograms after verapamil in all 13 patients, and the")
print("  systolic pressure-volume analysis in 11 of 13. No sinus arrest is")
print("  reported. Read as 0/13 automaticity failures, that bounds the")
print(f"  observed rate at 95% CI [{wilson(0,13)[0]:.1%}, {wilson(0,13)[1]:.1%}].")
print("  This is an inference from ABSENCE of a reported event, not a stated")
print("  result, and is labelled as such. The model prediction at this")
print(f"  exposure ({failure(b4[0]):.1%}-{failure(b4[1]):.1%}) is inside it.")

print("")
print("  IVABRADINE - 36-month transplant anchor (fixed input, Task F)")
print("  91.0 -> 81.2 bpm = 10.8% fractional reduction -> I_f block 31.2%")
print("  implied IC50 32.8 nM vs in vitro 2000 nM -> 61x, UNEXPLAINED.")
print("  Not a baroreflex artifact (survives the open-loop comparison); not")
print("  closed by rate alone (Task B accounts for ~3.8x). Trapped /")
print("  use-dependent block is the plausible mechanism and is NOT implemented.")
print("  Recorded as a stated limitation, not a blocker.")

json.dump({"G1_dog_binding": {
               "measured_dog_f_unbound": FU_DOG_KEEFE,
               "measured_dog_bound_pct": 90.7,
               "source": "Keefe DL, Yee YG, Kates RE. Clin Pharmacol Ther "
                         "1981;29(1):21-6. PMID 6970111",
               "human_f_unbound_same_assay": FU_HUMAN,
               "crosscheck_belpaire_f_unbound": FU_DOG_BELPAIRE,
               "crosscheck_source": "Belpaire FM et al. J Pharm Pharmacol "
                                    "1990;42(1):45-9. PMID 1969949",
               "f_unbound_needed_for_taskF_pass": 0.20,
               "rescue_available": False,
               "rows": g1},
           "G2_verapamil_schulman": {
               "anchor": "Schulman DS et al. J Cardiovasc Pharmacol "
                         "1993;21(4):567-72. PMID 7681901",
               "n": 13, "dose_mg_iv_median": 4,
               "magnitude_recoverable": False,
               "pk_frame": "Reiter MJ et al. Am J Cardiol 1982;50(4):716-21. "
                           "PMID 7124631",
               "assumed_total_ng_per_mL": [25, 80],
               "implied_block_range": b4,
               "implied_failure_range": [failure(b4[0]), failure(b4[1])],
               "observed_bound_0_of_13_ci": list(wilson(0, 13)),
               "ladder": g2},
           "G2_ivabradine": {"block": 0.312, "anchor": "36-month transplant "
                             "91.0 -> 81.2 bpm", "implied_ic50_nM": 32.8,
                             "invitro_ic50_nM": 2000.0, "fold_gap": 61,
                             "status": "stated limitation, not a blocker"}},
          open(os.path.join(OUT, "taskG_singles.json"), "w", encoding="utf-8"),
          indent=2)
print("")
print(f"-> {os.path.join(OUT, 'taskG_singles.json')}")
