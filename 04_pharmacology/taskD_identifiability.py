"""Task D addendum 2: is the proposed 2-parameter state-dependent scheme
IDENTIFIABLE from two states?

The proposal is: block fraction as a function of time spent in the
blocked-preferred state, with two parameters per drug (affinity, state
preference), calibrated against control and Iso.

That is only identifiable if the state occupancy actually DIFFERS between the
two calibration states. If control and Iso give the same occupancy, the two
anchors collapse to one equation and the two parameters cannot be separated.

This measures, over one steady-state cycle in each state, the time-average
occupancy of the I_CaL gates:
    dL  activation
    fL  voltage-dependent inactivation (availability; 1-fL = inactivated)
    fCa Ca-dependent inactivation (availability)
and the same for the I_f activation gate y, for the ivabradine case.

Nothing is fitted. This is a feasibility measurement only.
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

OUT = os.path.join(ROOT, "outputs", "taskD_identifiability.json")
VARS = ["i_CaL_dL_gate.dL", "i_CaL_fL_gate.fL", "i_CaL_fCa_gate.fCa",
        "i_f_y_gate.y", "Membrane.V"]


def measure(sim, pristine, iso):
    reset_pristine(sim, pristine)
    sim.set_constant("Rate_modulation_experiments.Iso_1_uM", iso)
    sim.pre(500.0)
    d = sim.run(6.0, log=["environment.time"] + VARS,
                log_times=np.arange(0, 6.0, 1e-4))
    t = np.array(d["environment.time"])
    v = np.array(d["Membrane.V"])
    bm = biomarkers(t, v)
    out = {"bpm": 60000.0 / bm["CL_ms"], "CL_ms": bm["CL_ms"]}
    for q in VARS:
        if q == "Membrane.V":
            continue
        x = np.array(d[q])
        out[q] = {"time_mean": float(np.mean(x)),
                  "min": float(np.min(x)), "max": float(np.max(x))}
    # inactivated-state occupancy proxies
    fL = np.array(d["i_CaL_fL_gate.fL"])
    fCa = np.array(d["i_CaL_fCa_gate.fCa"])
    dL = np.array(d["i_CaL_dL_gate.dL"])
    out["ICaL_inactivated_fraction_1_minus_fL"] = float(np.mean(1 - fL))
    out["ICaL_inactivated_fraction_1_minus_fLfCa"] = float(np.mean(1 - fL * fCa))
    out["ICaL_open_fraction_dL_fL_fCa"] = float(np.mean(dL * fL * fCa))
    return out


def main():
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    res = {}
    for iso, name in ((0, "control"), (1, "iso_1uM")):
        res[name] = measure(sim, pristine, iso)
        r = res[name]
        print(f"\n=== {name}: {r['bpm']:.2f} bpm (CL {r['CL_ms']:.1f} ms) ===")
        print(f"  I_CaL open fraction   <dL*fL*fCa>  = "
              f"{r['ICaL_open_fraction_dL_fL_fCa']:.5f}")
        print(f"  I_CaL inactivated     <1-fL>       = "
              f"{r['ICaL_inactivated_fraction_1_minus_fL']:.5f}")
        print(f"  I_CaL inactivated     <1-fL*fCa>   = "
              f"{r['ICaL_inactivated_fraction_1_minus_fLfCa']:.5f}")
        print(f"  I_f activation        <y>          = "
              f"{r['i_f_y_gate.y']['time_mean']:.5f}")

    c, i = res["control"], res["iso_1uM"]
    print("\n" + "=" * 62)
    print("IDENTIFIABILITY: ratio of state occupancy, Iso vs control")
    for key, label in (("ICaL_open_fraction_dL_fL_fCa", "I_CaL open"),
                       ("ICaL_inactivated_fraction_1_minus_fL", "I_CaL inact <1-fL>"),
                       ("ICaL_inactivated_fraction_1_minus_fLfCa",
                        "I_CaL inact <1-fL*fCa>")):
        ratio = i[key] / c[key] if c[key] else float("nan")
        print(f"  {label:26s} {c[key]:.5f} -> {i[key]:.5f}   ratio {ratio:.3f}")
    ry = i["i_f_y_gate.y"]["time_mean"] / c["i_f_y_gate.y"]["time_mean"]
    print(f"  {'I_f activation <y>':26s} "
          f"{c['i_f_y_gate.y']['time_mean']:.5f} -> "
          f"{i['i_f_y_gate.y']['time_mean']:.5f}   ratio {ry:.3f}")

    res["identifiability"] = {
        "ICaL_open_ratio": i["ICaL_open_fraction_dL_fL_fCa"] /
                           c["ICaL_open_fraction_dL_fL_fCa"],
        "ICaL_inact_ratio": i["ICaL_inactivated_fraction_1_minus_fL"] /
                            c["ICaL_inactivated_fraction_1_minus_fL"],
        "If_y_ratio": ry,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\n  -> {OUT}")


if __name__ == "__main__":
    main()
