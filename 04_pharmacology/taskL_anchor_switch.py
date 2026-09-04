"""Task L1 - re-run the Task I EAR ladder under all three ivabradine anchors.

ANCHOR SWITCH. The primary ivabradine anchor moves from the 36-month transplant
cohort to Doesch 2007 (Transplantation 84(8):988-96, PMID 17989604).

SELECTION RULE - DESIGN QUALITY, EXPLICITLY NOT GAP MAGNITUDE:
  1. within-patient crossover, so each subject is their own control;
  2. a DRUG-FREE baseline measured in the same patients (96.5 +- 7.0 bpm),
     rather than a between-cohort comparison;
  3. prospective, not retrospective/observational;
  4. earliest post-transplant (8-week treatment periods), therefore the least
     sympathetically reinnervated and the purest open-loop measurement - which
     is the criterion the project already stated when it preferred the 36-month
     cohort over the 10-year one. Applied consistently, that same criterion
     selects Doesch over both.
  The switch is made DESPITE increasing the unexplained in-vitro discrepancy
  from 61x to 250x. Gap magnitude is not a selection criterion and was not used
  as one; if it had been, the 36-month anchor would have been retained.

Exposure scaling identical in form to Task I: keep the in vitro Hill slope
n = 0.80 and re-solve IC50 through each anchor at the clinical free Cmax
12.2 nM, then evaluate at 1x, 2x, 3x CYP3A4-inhibited exposure.

  anchor                     IC50      1x       2x       3x
  Doesch 2007 (PRIMARY)    7.984 nM  0.5840   0.7097   0.7717
  10-year cohort          11.663 nM  0.5090   0.6435   0.7140
  36-month (previous)     32.783 nM  0.3120   0.4412   0.5220   <- already run

Verapamil: Ba2+ mapping only, on the chronic-oral rungs of Task I. Rungs cover
both clinical bands exactly (240 mg/day 2.9-14.0%, 480 mg/day 10.8-30.0%) plus
40% as an out-of-band headroom marker.

HARD RULE (config study_integrity.no_pair_feedback): the anchors are single-drug
open-loop monotherapy observations. No pair outcome informs any of them.
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

# New I_f blocks only; the 36-month arm is already in the checkpoint.
NEW_BF = [0.5840, 0.7097, 0.7717,      # Doesch 2007  1x, 2x, 3x
          0.5090, 0.6435, 0.7140]      # 10-year      1x, 2x, 3x

VER = [0.0, 0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25, 0.275, 0.30, 0.40]
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
            for st in STATES for bf in NEW_BF for bc in VER]
    print(f"grid points: {len(grid)} -> {len(grid)*len(models)} sims", flush=True)

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
    print(f"checkpoint: {len(done)} already done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_init) as pool:
                for k, r in enumerate(pool.imap(_job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    if k % 500 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)
    print("SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
