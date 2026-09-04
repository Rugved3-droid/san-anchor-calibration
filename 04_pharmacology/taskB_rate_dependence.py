"""Task B - ivabradine I_f sweep at elevated rate.

IMPORTANT SCOPE NOTE. There is no graded beta-adrenergic implementation in this
project or in the Fabbri model. Fabbri implements isoprenaline as a BINARY
1 uM switch: every effect is piecewise(Iso_1_uM > 0, X, Y). The eight affected
quantities are

    i_CaL.Iso_increase          1 -> 1.23
    i_CaL_dL_gate.Iso_shift_dL  0 -> -8 mV
    i_CaL_dL_gate.Iso_slope_dL  0 -> -27
    i_Ks.g_Ks                   g_Ks_ -> 1.2 * g_Ks_
    i_Ks_n_gate.Iso_shift       0 -> -14 mV
    i_NaK.Iso_increase          1 -> 1.2
    i_f_y_gate.Iso_shift        0 -> +7.5 mV
    Ca_intracellular_fluxes.b_up 0 -> -0.25

(ACh, by contrast, IS graded in Fabbri.) Building a graded beta-AR axis would
mean choosing an interpolation for all eight - a modelling decision, not an
implementation detail, so it is NOT done here.

What this script does instead: uses Fabbri's own published, validated
Iso = 1 uM condition as a defined elevated-rate state, and repeats the I_f
block ladder and the block-needed-for-target calculation there. That answers
how much of the ivabradine gap is rate/protocol mismatch, using only published
model states.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

from common import load_config, make_sim, reset_pristine   # noqa: E402
import numpy as np                                          # noqa: E402
from biomarkers import biomarkers                           # noqa: E402

OUT = os.path.join(ROOT, "outputs", "taskB_rate_dependence.json")
FREE_CMAX_NM = 12.2
BLOCKS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
          0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
PREPACE_S = 500.0
WINDOW_S = 10.0


def ladder(sim, pristine, g_f_var, g_f_base, iso):
    rows = []
    for b in BLOCKS:
        reset_pristine(sim, pristine)
        sim.set_constant("Rate_modulation_experiments.Iso_1_uM", iso)
        sim.set_constant(g_f_var, g_f_base * (1.0 - b))
        try:
            sim.pre(PREPACE_S)
            d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                        log_times=np.arange(0, WINDOW_S, 1e-4))
            bm = biomarkers(np.array(d["environment.time"]),
                           np.array(d["Membrane.V"]))
        except Exception:
            bm = None
        if bm is None:
            rows.append({"block": b, "status": "no_pacing"})
            print(f"    block {b:5.0%} -> QUIESCENT", flush=True)
        else:
            bpm = 60000.0 / bm["CL_ms"]
            rows.append({"block": b, "status": "ok", "CL_ms": bm["CL_ms"],
                         "bpm": bpm})
            print(f"    block {b:5.0%} -> CL {bm['CL_ms']:8.2f} ms  "
                  f"{bpm:6.2f} bpm", flush=True)
    return rows


def analyse(rows, label, target_drop_bpm=10.0, target_frac=None):
    ok = [r for r in rows if r["status"] == "ok"]
    base = ok[0]["bpm"]
    for r in ok:
        r["delta_bpm"] = r["bpm"] - base
    drop = target_drop_bpm if target_frac is None else base * target_frac
    xs = [r["block"] for r in ok]
    ys = [r["delta_bpm"] for r in ok]
    need = None
    for i in range(len(ys) - 1):
        if ys[i] >= -drop >= ys[i + 1]:
            f = (-drop - ys[i]) / (ys[i + 1] - ys[i])
            need = xs[i] + f * (xs[i + 1] - xs[i])
            break
    out = {"label": label, "baseline_bpm": base,
           "max_drop_bpm": ok[-1]["delta_bpm"], "target_drop_bpm": drop,
           "block_needed": need}
    if need is not None and need > 0:
        ic50 = FREE_CMAX_NM * (1 - need) / need
        out["implied_ic50_nM"] = ic50
        out["fold_vs_2000nM"] = 2000.0 / ic50
    return out


def main():
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    g_f_var = g_f_base = None
    for p in cfg["parameters"]:
        if p["zhou_symbol"] == "G_f":
            g_f_var, g_f_base = p["variable"], float(p["baseline"])

    res = {}
    for iso, name in ((0, "control (Iso 0)"), (1, "Iso 1 uM (Fabbri binary)")):
        print(f"\n  === {name} ===", flush=True)
        rows = ladder(sim, pristine, g_f_var, g_f_base, iso)
        res[name] = {"curve": rows}
        # absolute -10 bpm, and the same FRACTIONAL drop as -10 bpm at control
        res[name]["absolute_10bpm"] = analyse(rows, name, 10.0)
        res[name]["fractional_13_6pct"] = analyse(rows, name, target_frac=10.0 / 73.76)

    print("\n" + "=" * 66)
    for name, r in res.items():
        a = r["absolute_10bpm"]
        f = r["fractional_13_6pct"]
        print(f"\n{name}")
        print(f"  intrinsic rate            : {a['baseline_bpm']:.2f} bpm")
        print(f"  max drop at 100% If block : {a['max_drop_bpm']:+.2f} bpm")
        print(f"  block for -10 bpm         : "
              + (f"{a['block_needed']*100:.1f}%" if a['block_needed'] else "unreachable"))
        if a.get("implied_ic50_nM"):
            print(f"    implied IC50            : {a['implied_ic50_nM']:.2f} nM "
                  f"({a['fold_vs_2000nM']:.0f}x below 2000 nM)")
        print(f"  block for -13.6% rate     : "
              + (f"{f['block_needed']*100:.1f}%" if f['block_needed'] else "unreachable"))
        if f.get("implied_ic50_nM"):
            print(f"    implied IC50            : {f['implied_ic50_nM']:.2f} nM "
                  f"({f['fold_vs_2000nM']:.0f}x below 2000 nM)")

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
