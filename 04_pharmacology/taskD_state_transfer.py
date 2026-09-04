"""Task D - state-transfer validation for diltiazem.

Design (investigator-specified): calibrate one fixed I_CaL block fraction at the
Iso 1 uM state, where diltiazem's HR effect is measurable, then apply that SAME
fraction at control across the retained population and see what it predicts.

Two anchors:
  ELEVATED  Boden 2001 (PMID 11195610, doi 10.1002/clc.4960240112): SR diltiazem
            200-300 mg od significantly lowers HR for baseline >= 85 bpm.
            The Fabbri Iso 1 uM state is 93.94 bpm, inside that category.
            The paper's per-category bpm magnitudes are behind a paywall, so the
            calibration is run across a RANGE of plausible targets rather than a
            single number. The conclusion is then independent of the exact value.
  RESTING   Boden 2001: NO significant HR reduction at baseline <= 74 bpm.
            Fabbri control is 73.76 bpm. Predicted resting effect should
            therefore be ~0 and must not abolish firing.

Efficiency: the control-state population response is already computed for all
188 retained models in taskA_G_CaL_population_sweep.json (0-90% in 5% steps),
so no population re-simulation is needed. Only the Iso-state calibration ladder
is new.
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

OUT = os.path.join(ROOT, "outputs", "taskD_state_transfer.json")
POP = os.path.join(ROOT, "outputs", "taskA_G_CaL_population_sweep.json")

ISO_LADDER = [round(0.02 * i, 2) for i in range(31)]   # 0..60% in 2% steps
TARGET_DROPS_BPM = [3.0, 5.0, 8.0, 10.0, 12.0, 15.0]
PREPACE_S = 500.0
WINDOW_S = 10.0


def ladder_at_iso(sim, pristine, var, base):
    rows = []
    for b in ISO_LADDER:
        reset_pristine(sim, pristine)
        sim.set_constant("Rate_modulation_experiments.Iso_1_uM", 1)
        sim.set_constant(var, base * (1.0 - b))
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
            print(f"    Iso, block {b:5.0%} -> QUIESCENT", flush=True)
        else:
            rows.append({"block": b, "status": "ok",
                         "bpm": 60000.0 / bm["CL_ms"], "CL_ms": bm["CL_ms"]})
            print(f"    Iso, block {b:5.0%} -> {60000.0/bm['CL_ms']:6.2f} bpm",
                  flush=True)
    return rows


def invert(rows, drop):
    """Block fraction giving `drop` bpm reduction, by linear interpolation."""
    ok = [r for r in rows if r["status"] == "ok"]
    base = ok[0]["bpm"]
    xs = [r["block"] for r in ok]
    ys = [r["bpm"] - base for r in ok]
    for i in range(len(ys) - 1):
        if ys[i] >= -drop >= ys[i + 1]:
            f = (-drop - ys[i]) / (ys[i + 1] - ys[i])
            return xs[i] + f * (xs[i + 1] - xs[i])
    return None


def population_at(block, pop):
    """Control-state population response at an arbitrary block fraction,
    interpolated between the 5% grid points already simulated."""
    grid = sorted(float(k) for k in pop["records"][0]["levels"])
    lo = max([g for g in grid if g <= block], default=grid[0])
    hi = min([g for g in grid if g >= block], default=grid[-1])
    frac = 0.0 if hi == lo else (block - lo) / (hi - lo)

    drops, alive, dead = [], 0, 0
    for r in pop["records"]:
        b0 = r["levels"].get("0.0")
        if not b0:
            continue
        base = b0["bpm"]
        a, b = r["levels"].get(str(lo)), r["levels"].get(str(hi))
        if a is None or b is None:
            dead += 1                      # quiescent at or below this block
            continue
        alive += 1
        bpm = a["bpm"] + frac * (b["bpm"] - a["bpm"])
        drops.append(bpm - base)
    n = alive + dead
    return {"n": n, "n_pacing": alive, "n_quiescent": dead,
            "quiescent_fraction": dead / n if n else None,
            "median_drop_bpm": float(np.median(drops)) if drops else None,
            "iqr_drop_bpm": [float(np.percentile(drops, 25)),
                             float(np.percentile(drops, 75))] if drops else None,
            "worst_drop_bpm": float(np.min(drops)) if drops else None}


def main():
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    var = base = None
    for p in cfg["parameters"]:
        if p["zhou_symbol"] == "G_CaL":
            var, base = p["variable"], float(p["baseline"])

    print("  calibration ladder at Iso 1 uM:", flush=True)
    iso_rows = ladder_at_iso(sim, pristine, var, base)
    iso_base = [r for r in iso_rows if r["status"] == "ok"][0]["bpm"]

    with open(POP, encoding="utf-8") as f:
        pop = json.load(f)

    # control-state single-cell ladder, for reference
    ctrl_base = pop["records"][0]["levels"]["0.0"]["bpm"]

    print(f"\n  Iso 1 uM baseline    : {iso_base:.2f} bpm")
    print(f"  retained population  : {len(pop['records'])} models "
          f"(control state)")

    results = []
    print(f"\n{'target @Iso':>12s} {'block*':>8s} | "
          f"{'control median dHR':>19s} {'quiescent':>10s} {'worst dHR':>10s}")
    print("-" * 68)
    for drop in TARGET_DROPS_BPM:
        b = invert(iso_rows, drop)
        if b is None:
            print(f"{-drop:11.1f}  {'unreachable':>8s}")
            results.append({"target_drop_bpm": drop, "block": None})
            continue
        pr = population_at(b, pop)
        results.append({"target_drop_bpm": drop, "block": b,
                        "control_prediction": pr})
        print(f"{-drop:11.1f}  {b*100:7.2f}% | "
              f"{pr['median_drop_bpm']:+18.2f} "
              f"{pr['quiescent_fraction']*100:9.1f}% "
              f"{pr['worst_drop_bpm']:+10.2f}")

    out = {"iso_baseline_bpm": iso_base, "control_baseline_bpm": ctrl_base,
           "iso_ladder": iso_rows,
           "population_n": len(pop["records"]),
           "anchors": {
               "elevated": ("Boden 2001 PMID 11195610: SR diltiazem 200-300 mg od "
                            "significantly lowers HR for baseline >=85 bpm "
                            "(n=771, 6 double-blind studies). Per-category bpm "
                            "magnitude paywalled; swept as a range."),
               "resting": ("Boden 2001: NO significant HR reduction at baseline "
                           "<=74 bpm. Fabbri control = 73.76 bpm, so the "
                           "predicted resting effect should be ~0.")},
           "results": results}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
