"""Task F - open-loop calibration and external validation.

REFRAME (applied throughout): Fabbri is an open-loop plant. Intact-patient
resting HR is a closed-loop output containing the baroreflex, which Fabbri does
not model. Boden's resting null is therefore a measurement of the reflex, not a
contradiction of the model, and is NOT used here. Only open-loop comparators are
used: autonomic blockade, and denervated (transplanted) hearts. Fabbri control
(ACh = 0, Iso = 0) is the open-loop state.

Anchors
  VERAPAMIL   Qi et al., Circulation 1987;75(4):888-893, PMID 3549045,
              doi:10.1161/01.cir.75.4.888. Awake dogs, IV 0.2 mg/kg.
              Group 1 intact: SCL 494+-72 -> 379+-50 ms (reflex tachycardia).
              Group 2 autonomic blockade (n=10) and group 3 orthotopic
              transplant (n=5): transient shortening ABSENT, SCL prolonged
              promptly, SINUS ARREST in 2/10 and 2/5.
              -> observed automaticity-failure frequency 20% and 40%.
  IVABRADINE  denervated human hearts: 91.0 -> 81.2 bpm at 36 months
              (p = 0.0006); 88.8 -> 72.7 bpm at 10 years. Baseline ~90 bpm,
              closest published Fabbri state is Iso 1 uM = 93.94 bpm.

Everything below is computed from simulations already run (Task A control-state
I_CaL ladder, Task B Iso-state I_f ladder). No new simulation, no fitting.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
LAD_CAL = os.path.join(OUT, "taskA_G_CaL_population_sweep.json")
TASKB = os.path.join(OUT, "taskB_rate_dependence.json")

VERAP = {"ic50": 198.7, "hill": 1.09, "cmax_free": 45.0}
IVAB = {"ic50": 2000.0, "hill": 0.80, "cmax_free": 12.2}
MW_VERAPAMIL = 454.6
QI_PLASMA_NG_ML = (98.0, 204.0)      # dog, 0.2 mg/kg IV + infusion
VERAP_FREE_FRACTION = 0.10           # ~90% plasma protein bound


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def block_from_conc(drug, c_free):
    x = (c_free / drug["ic50"]) ** drug["hill"]
    return x / (1.0 + x)


def conc_from_block(drug, b):
    return drug["ic50"] * (b / (1.0 - b)) ** (1.0 / drug["hill"])


# ---------------------------------------------------------------- population
with open(LAD_CAL, encoding="utf-8") as f:
    cal = json.load(f)
recs = cal["records"]
n = len(recs)
grid = sorted(float(k) for k in recs[0]["levels"])

print("=" * 74)
print("VERAPAMIL - open-loop validation against Qi 1987")
print("=" * 74)
print(f"population: {n} retained models, Fabbri CONTROL state (open loop)\n")

print(f"{'I_CaL block':>12s} {'quiescent':>10s} {'95% CI (Wilson)':>20s} "
      f"{'median dHR':>12s}")
curve = []
for b in grid:
    k = sum(1 for r in recs if r["levels"].get(str(b)) is None)
    lo, hi = wilson(k, n)
    drops = [r["levels"][str(b)]["bpm"] - r["levels"]["0.0"]["bpm"]
             for r in recs if r["levels"].get(str(b)) is not None]
    med = float(np.median(drops)) if drops else float("nan")
    curve.append({"block": b, "k": k, "frac": k / n, "ci": [lo, hi],
                  "median_dHR": med})
    flag = "  <-- 20-40% window" if 0.20 <= k / n <= 0.40 else ""
    print(f"{b:11.0%} {k/n:10.3f} {f'[{lo:.3f}, {hi:.3f}]':>20s} "
          f"{med:+11.2f}{flag}")

win = [c for c in curve if 0.20 <= c["frac"] <= 0.40]
print(f"\nblock range giving 20-40% automaticity failure: "
      + (f"{win[0]['block']:.0%} - {win[-1]['block']:.0%}" if win else "none"))

# ---- map that block range back to verapamil exposure -------------------
print(f"\nExposure mapping (Hill: IC50 {VERAP['ic50']} nM, n = {VERAP['hill']}):")
if win:
    for c in (win[0], win[-1]):
        cf = conc_from_block(VERAP, c["block"])
        print(f"  {c['block']:.0%} block  <-  free verapamil {cf:7.1f} nM "
              f"({cf * MW_VERAPAMIL / 1000:6.1f} ng/mL free)")

lo_ng, hi_ng = QI_PLASMA_NG_ML
qi_free_lo = lo_ng / MW_VERAPAMIL * 1000 * VERAP_FREE_FRACTION
qi_free_hi = hi_ng / MW_VERAPAMIL * 1000 * VERAP_FREE_FRACTION
b_lo = block_from_conc(VERAP, qi_free_lo)
b_hi = block_from_conc(VERAP, qi_free_hi)
print(f"\nQi dosing (0.2 mg/kg IV + infusion, dog): plasma "
      f"{lo_ng:.0f}-{hi_ng:.0f} ng/mL total")
print(f"  -> free (assuming {VERAP_FREE_FRACTION:.0%} unbound): "
      f"{qi_free_lo:.1f}-{qi_free_hi:.1f} nM")
print(f"  -> predicted I_CaL block: {b_lo:.1%} - {b_hi:.1%}")


def frac_at(b):
    if b <= grid[0]:
        return curve[0]
    if b >= grid[-1]:
        return curve[-1]
    lo_g = max(g for g in grid if g <= b)
    hi_g = min(g for g in grid if g >= b)
    c0 = next(c for c in curve if c["block"] == lo_g)
    c1 = next(c for c in curve if c["block"] == hi_g)
    f = 0.0 if hi_g == lo_g else (b - lo_g) / (hi_g - lo_g)
    return {"frac": c0["frac"] + f * (c1["frac"] - c0["frac"]),
            "k": None, "ci": None}


p_lo, p_hi = frac_at(b_lo)["frac"], frac_at(b_hi)["frac"]
# exact CI at the nearest simulated grid points
k_lo = min(curve, key=lambda c: abs(c["block"] - b_lo))
k_hi = min(curve, key=lambda c: abs(c["block"] - b_hi))

print(f"\n  PREDICTED automaticity-failure fraction at the Qi exposure:")
print(f"    at {b_lo:.1%} block : {p_lo:.1%}   "
      f"(nearest simulated {k_lo['block']:.0%}: {k_lo['frac']:.1%}, "
      f"95% CI [{k_lo['ci'][0]:.1%}, {k_lo['ci'][1]:.1%}])")
print(f"    at {b_hi:.1%} block : {p_hi:.1%}   "
      f"(nearest simulated {k_hi['block']:.0%}: {k_hi['frac']:.1%}, "
      f"95% CI [{k_hi['ci'][0]:.1%}, {k_hi['ci'][1]:.1%}])")
print(f"\n  OBSERVED (Qi): 2/10 blocked = 20%  "
      f"(95% CI [{wilson(2,10)[0]:.1%}, {wilson(2,10)[1]:.1%}])")
print(f"                 2/5 transplant = 40% "
      f"(95% CI [{wilson(2,5)[0]:.1%}, {wilson(2,5)[1]:.1%}])")

verdict = "PASS" if (0.20 <= p_hi <= 0.40 or 0.20 <= p_lo <= 0.40) else "FAIL"
print(f"\n  PRE-SPECIFIED PASS CONDITION (20-40%): {verdict}")

# ---------------------------------------------------------------- ivabradine
print("\n" + "=" * 74)
print("IVABRADINE - calibration at Iso 1 uM against denervated human hearts")
print("=" * 74)
with open(TASKB, encoding="utf-8") as f:
    tb = json.load(f)
iso = tb["Iso 1 uM (Fabbri binary)"]["curve"]
ok = [r for r in iso if r["status"] == "ok"]
base = ok[0]["bpm"]
xs = [r["block"] for r in ok]
ys = [r["bpm"] for r in ok]


def block_for_bpm(target):
    for i in range(len(ys) - 1):
        if ys[i] >= target >= ys[i + 1]:
            f = (target - ys[i]) / (ys[i + 1] - ys[i])
            return xs[i] + f * (xs[i + 1] - xs[i])
    return None


print(f"  Fabbri Iso 1 uM baseline: {base:.2f} bpm "
      f"(anchor baselines 91.0 and 88.8 bpm)")
iv = {}
for label, b0, b1 in (("36 months", 91.0, 81.2), ("10 years", 88.8, 72.7)):
    drop_frac = (b0 - b1) / b0
    target = base * (1 - drop_frac)
    bl = block_for_bpm(target)
    row = {"anchor": label, "obs_from": b0, "obs_to": b1,
           "fractional_drop": drop_frac, "model_target_bpm": target,
           "block_required": bl}
    if bl:
        ic50 = conc_from_block(IVAB, bl) if bl < 1 else None
        # implied IC50 at the clinical free Cmax
        implied = IVAB["cmax_free"] * ((1 - bl) / bl) ** (1 / IVAB["hill"])
        row["implied_ic50_nM"] = implied
        row["fold_below_invitro"] = IVAB["ic50"] / implied
        print(f"  {label:10s}: {b0:.1f} -> {b1:.1f} bpm "
              f"({drop_frac*100:.1f}%)  =>  I_f block {bl*100:.1f}%  "
              f"=> implied IC50 {implied:.1f} nM "
              f"({IVAB['ic50']/implied:.0f}x below in vitro)")
    iv[label] = row
b_invitro = block_from_conc(IVAB, IVAB["cmax_free"])
print(f"\n  in vitro block at free Cmax {IVAB['cmax_free']} nM: "
      f"{b_invitro*100:.2f}%  -> model dHR at Iso: ", end="")
bpm_at = np.interp(b_invitro, xs, ys)
print(f"{bpm_at - base:+.2f} bpm (observed {81.2-91.0:+.1f} / {72.7-88.8:+.1f})")

json.dump({"verapamil": {"curve": curve, "qi_free_nM": [qi_free_lo, qi_free_hi],
                         "predicted_block": [b_lo, b_hi],
                         "predicted_failure_fraction": [p_lo, p_hi],
                         "observed": {"blocked": [2, 10], "transplant": [2, 5]},
                         "pass_condition": "20-40%", "verdict": verdict},
           "ivabradine": iv},
          open(os.path.join(OUT, "taskF_openloop.json"), "w",
               encoding="utf-8"), indent=2)
print(f"\n-> {os.path.join(OUT, 'taskF_openloop.json')}")
