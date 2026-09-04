"""SIM-0E diagnosis, part 2: where does I_CaL block abolish firing in Fabbri?

Diagnostic only. Same conventional pore-block mapping as the current pipeline:
    P_CaL_effective = P_CaL_baseline * (1 - block_fraction)
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

OUT = os.path.join(ROOT, "outputs", "sim0e_ical_block_sweep.json")
BLOCKS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45,
          0.50, 0.53, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.83, 0.90]


def main():
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    base = var = None
    for p in cfg["parameters"]:
        if p["zhou_symbol"] == "G_CaL":
            base, var = float(p["baseline"]), p["variable"]

    rows = []
    for b in BLOCKS:
        reset_pristine(sim, pristine)
        sim.set_constant(var, base * (1.0 - b))
        try:
            sim.pre(500.0)
            d = sim.run(10.0, log=["environment.time", "Membrane.V"],
                        log_times=np.arange(0, 10.0, 1e-4))
            bm = biomarkers(np.array(d["environment.time"]),
                           np.array(d["Membrane.V"]))
        except Exception as e:
            bm = None
        if bm is None:
            rows.append({"block": b, "status": "no_pacing"})
            print(f"  ICaL block {b:5.1%}  ->  NO PACING (quiescent)", flush=True)
        else:
            rows.append({"block": b, "status": "ok", "CL_ms": bm["CL_ms"],
                         "bpm": 60000.0 / bm["CL_ms"], "OS_mV": bm["OS_mV"],
                         "MDP_mV": bm["MDP_mV"], "APA_mV": bm["APA_mV"]})
            print(f"  ICaL block {b:5.1%}  ->  CL {bm['CL_ms']:7.2f} ms  "
                  f"{60000.0/bm['CL_ms']:6.2f} bpm  OS {bm['OS_mV']:+6.2f} mV",
                  flush=True)

    ok = [r for r in rows if r["status"] == "ok"]
    dead = [r["block"] for r in rows if r["status"] != "ok"]
    out = {"curve": rows,
           "baseline_bpm": ok[0]["bpm"] if ok else None,
           "lowest_block_abolishing_firing": min(dead) if dead else None,
           "crumb_2016": {
               "source": ("Crumb WJ et al. 2016, J Pharmacol Toxicol Methods "
                          "81:251-262, doi:10.1016/j.vascn.2016.03.009"),
               "charge_carrier": "4 mM BaCl2 replacing 1.8 mM CaCl2",
               "temperature_C": 36,
               "diltiazem": {"ic50_nM": 112, "free_cmax_nM": 128},
               "verapamil": {"ic50_nM": 202, "free_cmax_nM": 45}},
           }
    for drug, ic50, cmax in (("diltiazem", 112.0, 128.0),
                             ("verapamil", 202.0, 45.0)):
        b_ba = cmax / (cmax + ic50)
        ic50_ca = ic50 / 4.20      # Nawrath & Wegener 1997 verapamil Ba/Ca ratio
        b_ca = cmax / (cmax + ic50_ca)
        out[drug] = {"ic50_Ba_nM": ic50, "free_cmax_nM": cmax,
                     "block_with_Ba_ic50": b_ba,
                     "implied_ic50_Ca_nM": ic50_ca,
                     "block_with_Ca_ic50": b_ca,
                     "delta_block_pp": (b_ca - b_ba) * 100}
        print(f"\n  {drug}: Ba IC50 {ic50:.0f} nM -> block {b_ba*100:.1f}% ; "
              f"Ca-implied IC50 {ic50_ca:.1f} nM -> block {b_ca*100:.1f}% "
              f"({(b_ca-b_ba)*100:+.1f} pp)")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  lowest block abolishing firing: "
          f"{out['lowest_block_abolishing_firing']}")
    print(f"  -> {OUT}")


if __name__ == "__main__":
    main()
