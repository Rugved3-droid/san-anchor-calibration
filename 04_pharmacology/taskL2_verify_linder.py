"""Task L2 verification - TWO TESTS ONLY. No migration, no population, no ladders.

  TEST 1  ISO = 0 (Iso_cas = 0 and Iso_1_uM = 0) must reproduce the base Fabbri
          baseline within the tolerance this project already applies to its own
          baseline gate (Fabbri 2017 Table 5).

  TEST 2  the top of the graded range (Iso_cas = 1000 nM) must reproduce the
          published Iso 1 uM state, 93.94 bpm.

  Bonus, free: the extended model RETAINS the original binary switch
  Iso_1_uM, so that path is exercised too. If the binary path still gives
  93.94 bpm, every existing Iso-state result in this project is reproducible on
  the extended model, which is the single most important migration question.

Nothing here writes to any project artefact.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

from common import use_local_tmp                      # noqa: E402
use_local_tmp()
import numpy as np                                    # noqa: E402
import myokit                                         # noqa: E402
import myokit.formats.cellml                          # noqa: E402
from biomarkers import biomarkers                     # noqa: E402

MODEL = os.path.join(ROOT, "data", "models", "linder2025",
                     "Linder2025_FabbriExtended_REPAIRED.cellml")
OUT = os.path.join(ROOT, "outputs", "taskL2_linder_verification.json")

PREPACE_S = 500.0
WINDOW_S = 10.0

# Fabbri 2017 Table 5, as used by the project's own baseline gate.
TABLE5 = {"CL_ms": 814.0, "MDP_mV": -58.9, "OS_mV": 26.4,
          "APA_mV": 85.3, "DDR100_mV_s": 48.1, "dVdt_max_V_s": 7.4}
PUBLISHED_ISO_BPM = 93.94


def run(sim, pristine, settings, label):
    sim.set_default_state(pristine)
    sim.set_state(pristine)
    sim.set_time(0)
    for k, v in settings.items():
        sim.set_constant(k, v)
    try:
        sim.pre(PREPACE_S)
        d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, WINDOW_S, 1e-4))
        bm = biomarkers(np.array(d["environment.time"]),
                        np.array(d["Membrane.V"]))
    except Exception as e:
        print(f"  {label}: FAILED - {type(e).__name__}: {str(e)[:120]}")
        return None
    if bm is None:
        print(f"  {label}: NO PACING")
        return None
    bm["bpm"] = 60000.0 / bm["CL_ms"]
    print(f"  {label}: {bm['bpm']:.2f} bpm  (CL {bm['CL_ms']:.2f} ms)")
    return bm


def main():
    imp = myokit.formats.importer("cellml")
    m = imp.model(MODEL)
    print(f"model imported: {m.count_states()} states")
    sim = myokit.Simulation(m)
    sim.set_tolerance(1e-8, 1e-8)
    pristine = list(sim.state())
    res = {"model": os.path.basename(MODEL), "n_states": m.count_states(),
           "prepace_s": PREPACE_S}

    print("\n" + "=" * 78)
    print("TEST 1 - ISO = 0 must reproduce base Fabbri (Table 5)")
    print("=" * 78)
    bm0 = run(sim, pristine,
              {"Rate_modulation_experiments.Iso_1_uM": 0,
               "Rate_modulation_experiments.Iso_cas": 0,
               "Rate_modulation_experiments.ACh": 0,
               "Rate_modulation_experiments.ACh_cas": 0}, "ISO=0")
    if bm0:
        print(f"\n  {'feature':14s} {'Table 5':>10s} {'extended':>12s} "
              f"{'% diff':>9s}")
        rows = {}
        for k, ref in TABLE5.items():
            got = bm0.get(k)
            if got is None:
                continue
            pd = (got - ref) / abs(ref) * 100.0
            rows[k] = {"reference": ref, "extended": got, "pct_diff": pd}
            print(f"  {k:14s} {ref:10.2f} {got:12.2f} {pd:+8.2f}%")
        res["test1_iso_zero"] = {"biomarkers": rows,
                                 "bpm": bm0["bpm"],
                                 "base_fabbri_bpm": 60000.0 / TABLE5["CL_ms"]}
        worst = max(abs(v["pct_diff"]) for v in rows.values())
        res["test1_worst_abs_pct_diff"] = worst
        print(f"\n  worst absolute deviation: {worst:.2f}%")

    print("\n" + "=" * 78)
    print("TEST 2 - top of the graded range vs the published Iso 1 uM state")
    print("=" * 78)
    print(f"  published Fabbri Iso 1 uM = {PUBLISHED_ISO_BPM} bpm")
    arms = {}
    b = run(sim, pristine,
            {"Rate_modulation_experiments.Iso_1_uM": 1,
             "Rate_modulation_experiments.Iso_cas": 0,
             "Rate_modulation_experiments.ACh": 0,
             "Rate_modulation_experiments.ACh_cas": 0},
            "binary Iso_1_uM = 1 (original switch, retained)")
    if b:
        arms["binary_Iso_1_uM"] = {"bpm": b["bpm"],
                                   "diff_vs_published": b["bpm"] - PUBLISHED_ISO_BPM}
    for iso in (100.0, 1000.0):
        b = run(sim, pristine,
                {"Rate_modulation_experiments.Iso_1_uM": 0,
                 "Rate_modulation_experiments.Iso_cas": iso,
                 "Rate_modulation_experiments.ACh": 0,
                 "Rate_modulation_experiments.ACh_cas": 0},
                f"graded Iso_cas = {iso:.0f} nM")
        if b:
            arms[f"graded_{iso:.0f}nM"] = {
                "bpm": b["bpm"], "diff_vs_published": b["bpm"] - PUBLISHED_ISO_BPM}
    res["test2_iso_state"] = {"published_bpm": PUBLISHED_ISO_BPM, "arms": arms}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
