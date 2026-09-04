"""Step 1 - baseline validation of the imported Fabbri 2017 human SAN model.

Simulates the unmodified model to steady state and compares the resulting AP
biomarkers against the published values in Fabbri et al. 2017, Table 5.

If the baseline does not match, everything downstream is worthless, so this
script reports a verdict and is intended to gate all later steps.

Also verifies steady state explicitly (CL drift across the final beats) and
checks solver-tolerance sensitivity, so that a "match" is not an artifact of
loose integration.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import myokit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from biomarkers import biomarkers

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MMT = os.path.join(ROOT, "data", "models", "fabbri_2017.mmt")
OUT_DIR = os.path.join(ROOT, "outputs")

# Fabbri et al. 2017, J Physiol 595:2365-2396, Table 5, "Present model" column.
PUBLISHED = {
    "CL_ms": 814.0,
    "MDP_mV": -58.9,
    "OS_mV": 26.4,
    "DDR100_mV_s": 48.1,
    "dVdtmax_V_s": 7.4,
}
# APA is not tabulated by Fabbri; it follows from OS - MDP.
PUBLISHED["APA_mV"] = PUBLISHED["OS_mV"] - PUBLISHED["MDP_mV"]   # 85.3 mV

PREPACE_S = 500.0      # long pre-pace to reach the limit cycle
LOG_S = 10.0           # logged window
LOG_DT = 1e-4          # 0.1 ms sampling for biomarker accuracy


def run(tol_abs, tol_rel, prepace=PREPACE_S, log_s=LOG_S):
    m = myokit.load_model(MMT)
    s = myokit.Simulation(m)
    s.set_tolerance(tol_abs, tol_rel)
    t0 = time.time()
    s.pre(prepace)
    t_pre = time.time() - t0
    t0 = time.time()
    d = s.run(log_s,
              log=["environment.time", "Membrane.V"],
              log_times=np.arange(0, log_s, LOG_DT))
    t_run = time.time() - t0
    return d, t_pre, t_run


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Step 1 - baseline validation, Fabbri 2017 human SAN")
    print(f"model: {MMT}\n")

    # ---- main run -------------------------------------------------------
    d, t_pre, t_run = run(1e-8, 1e-8)
    t = np.array(d["environment.time"])
    v = np.array(d["Membrane.V"])
    print(f"pre-pace {PREPACE_S:.0f} s in {t_pre:.1f}s; "
          f"logged {LOG_S:.0f} s in {t_run:.1f}s")

    b = biomarkers(t, v)
    if b is None:
        print("\nFAIL: model is not spontaneously active - no beats detected.")
        return 1

    # ---- steady state check --------------------------------------------
    print(f"\nsteady state: {b['n_beats']} complete beats in the logged window, "
          f"CL SD = {b['CL_ms_sd']:.4f} ms")
    steady = b["CL_ms_sd"] < 0.5

    # ---- tolerance sensitivity -----------------------------------------
    d2, _, _ = run(1e-6, 1e-6, prepace=PREPACE_S, log_s=5.0)
    b2 = biomarkers(np.array(d2["environment.time"]), np.array(d2["Membrane.V"]))
    dcl = abs(b2["CL_ms"] - b["CL_ms"]) if b2 else float("nan")
    print(f"tolerance check: CL at 1e-6/1e-6 = {b2['CL_ms']:.2f} ms, "
          f"at 1e-8/1e-8 = {b['CL_ms']:.2f} ms, |diff| = {dcl:.3f} ms")

    # ---- comparison ------------------------------------------------------
    print(f"\n{'feature':14s} {'unit':8s} {'published':>10s} {'simulated':>10s} "
          f"{'diff':>9s} {'% diff':>8s}")
    print("-" * 64)
    rows = {}
    units = {"CL_ms": "ms", "MDP_mV": "mV", "OS_mV": "mV", "APA_mV": "mV",
             "DDR100_mV_s": "mV/s", "dVdtmax_V_s": "V/s"}
    for k in ["CL_ms", "MDP_mV", "OS_mV", "APA_mV", "DDR100_mV_s", "dVdtmax_V_s"]:
        pub, sim = PUBLISHED[k], b[k]
        diff = sim - pub
        pct = diff / abs(pub) * 100.0
        rows[k] = {"published": pub, "simulated": sim, "diff": diff, "pct": pct}
        print(f"{k:14s} {units[k]:8s} {pub:10.2f} {sim:10.2f} "
              f"{diff:+9.2f} {pct:+7.1f}%")

    # Verdict. CL is the primary criterion: it is the feature the model was
    # optimised on and the one the population criteria in step 4 depend on.
    cl_pct = abs(rows["CL_ms"]["pct"])
    key_ok = all(abs(rows[k]["pct"]) < 5.0
                 for k in ["CL_ms", "MDP_mV", "OS_mV", "APA_mV"])
    verdict = "PASS" if (cl_pct < 2.0 and key_ok and steady) else "FAIL"

    print(f"\nVERDICT: {verdict}")
    print(f"  CL within 2%          : {cl_pct < 2.0}  ({cl_pct:.2f}%)")
    print(f"  CL/MDP/OS/APA within 5%: {key_ok}")
    print(f"  steady state           : {steady}")

    report = {
        "step": "1 - baseline validation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "model_source": "HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml (PMR e/568)",
        "reference": ("Fabbri et al. 2017, J Physiol 595:2365-2396, Table 5, "
                      "'Present model' column"),
        "settings": {"prepace_s": PREPACE_S, "log_s": LOG_S, "log_dt_s": LOG_DT,
                     "tol_abs": 1e-8, "tol_rel": 1e-8,
                     "clamp_mode": 0, "ACh_mM": 0, "Iso": 0},
        "comparison": rows,
        "n_beats": b["n_beats"],
        "CL_sd_ms": b["CL_ms_sd"],
        "steady_state": bool(steady),
        "tolerance_check_CL_diff_ms": dcl,
        "verdict": verdict,
    }
    with open(os.path.join(OUT_DIR, "step1_baseline.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    np.savez_compressed(os.path.join(OUT_DIR, "step1_trace.npz"), t=t, v=v)
    print(f"\nreport -> {os.path.join(OUT_DIR, 'step1_baseline.json')}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
