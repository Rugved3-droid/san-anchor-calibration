"""Task H - extend the I_CaL block ladder to cover CHRONIC ORAL verapamil.

Task G evaluated the pair at Schulman's 4 mg IV calibration exposure. That
exposure anchors the concentration-block relationship; it is NOT the clinical
question. Chronic oral dosing reaches much higher free concentrations, and under
the Ca2+-corrected IC50 it reaches I_CaL block up to ~67% - far above the 40%
ceiling of the Task G grid.

DESIGN NOTE - why a BLOCK ladder and not a CONCENTRATION ladder.
    The two IC50 choices (Ba2+-derived and Ca2+-corrected) only relabel the
    concentration axis; they do not change the model. Simulating a block ladder
    and then inverting the Hill equation to report which free concentration
    produces each simulated block is therefore EXACT: every reported endpoint
    sits on a simulated rung, and no bpm curve is ever interpolated across a
    quiescence threshold. Simulating a concentration ladder instead would force
    interpolation between block rungs, which is the artifact Task E warned about.

Appends to the SAME checkpoint as Task G (key = model, state, b_cal, b_f), so
the two runs form one dataset and nothing is recomputed.

HARD RULE (00_config/config.yaml, study_integrity.no_pair_feedback): no pair
result may inform a parameter. Ivabradine stays FIXED at its 31.2% monotherapy
anchor. Nothing here is retro-calibrated. Task D's 3.5x over-block figure is
NOT used anywhere - it was derived against closed-loop data and is retired.
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

B_IVAB = 0.312          # FIXED monotherapy anchor - never re-fitted

# Task G already ran 0, .05, .10, .15, .20, .25, .30, .40 at b_f in {0, .312}.
# These are the additional rungs chronic oral exposure requires, plus extra
# resolution where EAR is expected to cross the 5% and 10% marks.
NEW_VER = [0.275, 0.325, 0.35, 0.375, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
STATES = ["control", "iso"]

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

    grid = [(st, round(bc, 6), round(bf, 6))
            for st in STATES for bc in NEW_VER for bf in (0.0, B_IVAB)]
    print(f"new grid points: {len(grid)} -> {len(grid)*len(models)} sims",
          flush=True)

    done = set()
    if os.path.exists(CKPT):
        with open(CKPT, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done.add((r["model"], r["state"],
                              round(r["b_cal"], 6), round(r["b_f"], 6)))
                except json.JSONDecodeError:
                    pass
    todo = [(mi, st, bc, bf) for (st, bc, bf) in grid for mi in models
            if (mi, st, bc, bf) not in done]
    print(f"checkpoint: {len(done)} already done, {len(todo)} to run",
          flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_init) as pool:
                for k, r in enumerate(pool.imap(_job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    if k % 200 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)
    print("SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
