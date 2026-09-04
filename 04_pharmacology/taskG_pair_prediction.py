"""Task G3 - FIRST PAIR: verapamil x ivabradine, predicted across the population.

HARD RULE (also written into 00_config/config.yaml):
    No pair result may ever inform a parameter. Singles are calibrated to
    open-loop monotherapy anchors ONLY; pairs are PREDICTED. If a combination
    outcome feeds back into any conductance or block value, the endpoint is
    fitted and the study is void.

This script therefore takes the two single-drug block fractions as FIXED INPUTS
and does nothing but forward-simulate. It contains no optimiser, no target and
no inversion of any pair quantity.

Design
------
Both open-loop anchors are ~90 bpm denervated/blocked hearts, so the pair is
predicted in TWO states and the conclusion is required to hold in both:

  control  Fabbri ACh=0, Iso=0.  The true "no autonomic input" state (73.8 bpm).
  iso      Fabbri Iso 1 uM (93.94 bpm). Matches the anchor RATE (91.0, 88.8 bpm)
           but by a mechanism - beta-AR stimulation - that a denervated heart
           does not have. This is a rate match, not a mechanism match, and is
           reported as such.

Grid is run as a full factorial with NO interpolation anywhere. The endpoint is
a threshold crossing, and interpolating a bpm curve across a quiescence
threshold is exactly the artifact Task E warned about.

Endpoint (primary): EXCESS ABSOLUTE RISK
    EAR = P(fail | A+B) - max( P(fail | A), P(fail | B) )
and the full triple (P_A, P_B, P_AB) is always reported so the reader can form
any other contrast. Bliss is computed but is a SECONDARY ARTIFACT
DEMONSTRATION only, per Task E: any endpoint defined as "fraction crossing a
steep threshold" manufactures super-additivity from additive target occupancy.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

from common import load_config, make_sim, reset_pristine, use_local_tmp  # noqa
import numpy as np                                                        # noqa

OUT_DIR = os.path.join(ROOT, "outputs")
SAMPLE = os.path.join(OUT_DIR, "step2_lhs_sample.npz")
LAD_CAL = os.path.join(OUT_DIR, "taskA_G_CaL_population_sweep.json")
LAD_F = os.path.join(OUT_DIR, "taskA_G_f_population_sweep.json")
CKPT = os.path.join(OUT_DIR, "taskG_pair_checkpoint.jsonl")

PREPACE_S = 300.0
WINDOW_S = 6.0
LOG_DT = 1e-4

# ---------------------------------------------------------------- FIXED INPUTS
# Ivabradine: calibrated to the 36-month transplant anchor 91.0 -> 81.2 bpm
# (Task F). Logged limitation: the implied IC50 sits 61x below the in vitro
# value, unexplained, plausibly trapped/use-dependent block.
IVAB_BLOCK_ANCHOR = 0.312
IVAB_BLOCK_10YR = 0.509        # 10-year anchor 88.8 -> 72.7 bpm, sensitivity only

# Verapamil: block grid. Schulman's per-patient HR magnitudes are paywalled, so
# verapamil is carried as a RANGE spanning every plausible clinical exposure
# rather than a single fitted number. Nothing downstream selects a value.
VER_GRID = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]

STATES = ["control", "iso"]


# ---------------------------------------------------------------- simulation
_S = {}


def _init():
    use_local_tmp()
    from biomarkers import biomarkers as _bm
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    z = np.load(SAMPLE, allow_pickle=True)
    variables = [str(v) for v in z["variables"]]
    idx = {}
    for p in cfg["parameters"]:
        if p["zhou_symbol"] in ("G_CaL", "G_f"):
            idx[p["zhou_symbol"]] = variables.index(p["variable"])
    _S.update(sim=sim, pristine=pristine, bm=_bm, variables=variables,
              values=z["values"], idx=idx)


def _job(args):
    """One model, one state, one (I_CaL block, I_f block)."""
    model_idx, state, b_cal, b_f = args
    S = _S
    sim = S["sim"]
    try:
        reset_pristine(sim, S["pristine"])
        vals = list(S["values"][model_idx])
        vals[S["idx"]["G_CaL"]] *= (1.0 - b_cal)
        vals[S["idx"]["G_f"]] *= (1.0 - b_f)
        for var, val in zip(S["variables"], vals):
            sim.set_constant(var, float(val))
        # State is set AFTER the sampled constants so it is never overwritten.
        sim.set_constant("Rate_modulation_experiments.Iso_1_uM",
                         1 if state == "iso" else 0)
        sim.pre(PREPACE_S)
        d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, WINDOW_S, LOG_DT))
        bm = S["bm"](np.array(d["environment.time"]), np.array(d["Membrane.V"]))
    except Exception:
        bm = None
    return {"model": int(model_idx), "state": state,
            "b_cal": round(b_cal, 6), "b_f": round(b_f, 6),
            "bpm": (60000.0 / bm["CL_ms"]) if bm else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    with open(LAD_CAL, encoding="utf-8") as f:
        cal = json.load(f)
    with open(LAD_F, encoding="utf-8") as f:
        lf = json.load(f)
    models = sorted({r["index"] for r in cal["records"]}
                    & {r["index"] for r in lf["records"]})
    print(f"population: {len(models)} retained models", flush=True)

    # ---- grid, primary points FIRST so an interrupted run still answers G3 --
    points = []
    for st in STATES:                                   # primary factorial
        for bc in VER_GRID:
            for bf in (0.0, IVAB_BLOCK_ANCHOR):
                points.append((st, round(bc, 6), round(bf, 6)))
    for st in STATES:                                   # ivabradine sensitivity
        for bc in (0.0, 0.10, 0.20, 0.30):
            points.append((st, round(bc, 6), round(IVAB_BLOCK_10YR, 6)))
    seen, grid = set(), []
    for p in points:
        if p not in seen:
            seen.add(p)
            grid.append(p)
    print(f"grid points: {len(grid)} -> {len(grid)*len(models)} simulations",
          flush=True)

    done = {}
    if os.path.exists(CKPT):
        with open(CKPT, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done[(r["model"], r["state"], r["b_cal"], r["b_f"])] = r["bpm"]
                except json.JSONDecodeError:
                    pass
    todo = [(mi, st, bc, bf) for (st, bc, bf) in grid for mi in models
            if (mi, st, bc, bf) not in done]
    print(f"checkpoint: {len(done)} done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_init) as pool:
                for k, r in enumerate(pool.imap(_job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    done[(r["model"], r["state"], r["b_cal"], r["b_f"])] = r["bpm"]
                    if k % 200 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)
    print("SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
