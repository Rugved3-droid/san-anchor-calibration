"""Task L2, part 2 - is the graded beta-AR axis actually drivable?

The first verification run found Iso_cas inert: 0, 100 and 1000 nM all gave
813.42 ms, byte-identical to ISO = 0. Diagnosis: `Simulation.set_constant()`
cannot propagate through a DERIVED constant. `cAMP.kiso` depends on Iso_cas:

    kiso = K_iso + 0.1181 * Iso_cas^niso / (K_05iso^niso + Iso_cas^niso)

Myokit folds that to a number when the simulation is compiled, so changing
Iso_cas afterwards leaves kiso at its baseline 0.007. This is a TOOLING
limitation, not a model defect - and it is exactly the kind of thing that would
have silently produced a null result if the migration had been attempted without
this check.

Correct method: set the value on the MODEL and compile a fresh Simulation for
each ISO level. Slower (one compile per level) but unambiguous.

Reports the graded dose-response, and whether the top of the range reproduces
the published Fabbri Iso 1 uM state of 93.94 bpm.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

from common import use_local_tmp                    # noqa: E402
use_local_tmp()
import numpy as np                                  # noqa: E402
import myokit                                       # noqa: E402
import myokit.formats.cellml                        # noqa: E402
from biomarkers import biomarkers                   # noqa: E402

MODEL = os.path.join(ROOT, "data", "models", "linder2025",
                     "Linder2025_FabbriExtended_REPAIRED.cellml")
OUT = os.path.join(ROOT, "outputs", "taskL2_graded_axis.json")
PUBLISHED_ISO_BPM = 93.94
PREPACE_S = 500.0


def measure(iso_nM, binary=0):
    """Fresh model + fresh Simulation per level - no constant folding."""
    m = myokit.formats.importer("cellml").model(MODEL)
    m.get("Rate_modulation_experiments.Iso_cas").set_rhs(float(iso_nM))
    m.get("Rate_modulation_experiments.Iso_1_uM").set_rhs(float(binary))
    m.get("Rate_modulation_experiments.ACh").set_rhs(0.0)
    m.get("Rate_modulation_experiments.ACh_cas").set_rhs(0.0)
    kiso = m.get("cAMP.kiso").eval()
    sim = myokit.Simulation(m)
    sim.set_tolerance(1e-8, 1e-8)
    try:
        sim.pre(PREPACE_S)
        d = sim.run(10.0, log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, 10.0, 1e-4))
        bm = biomarkers(np.array(d["environment.time"]),
                        np.array(d["Membrane.V"]))
    except Exception as e:
        print(f"  ISO {iso_nM:>7} nM (binary {binary}): FAILED "
              f"{type(e).__name__}", flush=True)
        return None
    if bm is None:
        print(f"  ISO {iso_nM:>7} nM (binary {binary}): NO PACING", flush=True)
        return None
    bpm = 60000.0 / bm["CL_ms"]
    print(f"  ISO {iso_nM:>7} nM (binary {binary}): kiso={kiso:.6f}  "
          f"{bpm:7.2f} bpm  (CL {bm['CL_ms']:8.2f} ms)  "
          f"vs published Iso 1uM {bpm - PUBLISHED_ISO_BPM:+7.2f}", flush=True)
    return {"iso_nM": iso_nM, "binary": binary, "kiso": kiso, "bpm": bpm,
            "CL_ms": bm["CL_ms"], "diff_vs_published": bpm - PUBLISHED_ISO_BPM}


def main():
    print("GRADED beta-AR AXIS - set on the MODEL, fresh compile per level")
    print(f"published Fabbri Iso 1 uM reference = {PUBLISHED_ISO_BPM} bpm\n",
          flush=True)
    rows = []
    for iso in (0.0, 10.0, 30.0, 58.57, 100.0, 300.0, 1000.0):
        r = measure(iso)
        if r:
            rows.append(r)
    print("\nbinary switch for comparison:", flush=True)
    b = measure(0.0, binary=1)
    json.dump({"published_iso_bpm": PUBLISHED_ISO_BPM,
               "graded": rows, "binary_Iso_1_uM": b},
              open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
