"""SIM-0E diagnosis, part 1: how much I_f block does ~10 bpm actually require?

Sweeps fractional block of G_f in the validated Fabbri baseline and reports the
rate-response curve. Diagnostic only - nothing is fixed or re-parameterised.

Block is applied as the simple pore-block scaling the current pipeline uses:
    g_f_effective = g_f_baseline * (1 - block_fraction)
This is deliberately the SAME conventional mapping the audit used, so the
question asked is "what block fraction does this model need?", not "what does a
better drug model give?".
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

OUT = os.path.join(ROOT, "outputs", "sim0e_if_block_sweep.json")

# Free Cmax used by the audit, and the heterologous steady-state IC50 it used.
FREE_CMAX_NM = 12.2
AUDIT_IC50_NM = 2000.0

PREPACE_S = 500.0
WINDOW_S = 10.0
LOG_DT = 1e-4

BLOCKS = [0.0, 0.01, 0.02, 0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20,
          0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]


def main():
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    g_f_base = None
    for p in cfg["parameters"]:
        if p["zhou_symbol"] == "G_f":
            g_f_base = float(p["baseline"])
            var = p["variable"]
    assert g_f_base is not None

    rows = []
    for b in BLOCKS:
        reset_pristine(sim, pristine)
        sim.set_constant(var, g_f_base * (1.0 - b))
        try:
            sim.pre(PREPACE_S)
            d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                        log_times=np.arange(0, WINDOW_S, LOG_DT))
            bm = biomarkers(np.array(d["environment.time"]),
                           np.array(d["Membrane.V"]))
        except Exception as e:
            bm = None
            print(f"  block {b:5.1%}  solver failure: {type(e).__name__}")
        if bm is None:
            rows.append({"block": b, "CL_ms": None, "bpm": None,
                         "status": "no_pacing"})
            print(f"  block {b:5.1%}  ->  NO PACING")
        else:
            bpm = 60000.0 / bm["CL_ms"]
            rows.append({"block": b, "CL_ms": bm["CL_ms"], "bpm": bpm,
                         "MDP_mV": bm["MDP_mV"], "OS_mV": bm["OS_mV"],
                         "status": "ok"})
            print(f"  block {b:5.1%}  ->  CL {bm['CL_ms']:7.2f} ms   "
                  f"{bpm:6.2f} bpm", flush=True)

    ok = [r for r in rows if r["status"] == "ok"]
    base_bpm = ok[0]["bpm"]
    for r in ok:
        r["delta_bpm"] = r["bpm"] - base_bpm
        r["pct_rate_change"] = (r["bpm"] - base_bpm) / base_bpm * 100.0

    # block fraction needed for -10 bpm, by interpolation on the monotone part
    xs = [r["block"] for r in ok]
    ys = [r["delta_bpm"] for r in ok]
    target = -10.0
    need = None
    for i in range(len(ys) - 1):
        if ys[i] >= target >= ys[i + 1]:
            f = (target - ys[i]) / (ys[i + 1] - ys[i])
            need = xs[i] + f * (xs[i + 1] - xs[i])
            break

    print(f"\n  baseline               : {base_bpm:.2f} bpm "
          f"({ok[0]['CL_ms']:.2f} ms)")
    out = {"baseline_bpm": base_bpm, "baseline_CL_ms": ok[0]["CL_ms"],
           "curve": rows, "free_cmax_nM": FREE_CMAX_NM,
           "audit_ic50_nM": AUDIT_IC50_NM}

    ab = FREE_CMAX_NM / (FREE_CMAX_NM + AUDIT_IC50_NM)
    out["audit_block_fraction"] = ab
    print(f"  audit block at 12.2 nM : {ab*100:.3f}%  "
          f"(IC50 {AUDIT_IC50_NM:.0f} nM, Hill 1)")

    if need is not None:
        out["block_needed_for_-10bpm"] = need
        # Hill-1 inversion: b = C/(C+IC50)  =>  IC50 = C(1-b)/b
        ic50 = FREE_CMAX_NM * (1 - need) / need
        out["implied_ic50_nM_at_free_cmax"] = ic50
        out["fold_vs_audit_ic50"] = AUDIT_IC50_NM / ic50
        print(f"  block needed for -10bpm: {need*100:.2f}%")
        print(f"  implied IC50 at 12.2 nM: {ic50:.2f} nM")
        print(f"  fold below audit IC50  : {AUDIT_IC50_NM/ic50:.0f}x")
    else:
        print("  -10 bpm not reached within the swept range")
        out["block_needed_for_-10bpm"] = None

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
