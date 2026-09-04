"""Task I - PK/PD decomposition of the verapamil-ivabradine contraindication.

Question: verapamil inhibits CYP3A4, which clears ivabradine. The ivabradine
label warns against co-prescription on that basis, citing an ~2-3x exposure
increase. Task H showed the PD convergence at the SAN is small at FIXED
ivabradine exposure. Does the PK interaction account for the hazard?

DERIVATION OF THE EXPOSURE-SCALED I_f BLOCK  (stated explicitly)
---------------------------------------------------------------
The 31.2% anchor is empirical: it is the I_f block that reproduces the 36-month
transplant observation 91.0 -> 81.2 bpm. To extrapolate it to higher exposure a
concentration-response SHAPE is needed. The construction used here:

  1. Keep the in vitro Hill SLOPE  n = 0.80  (SIM-0 table, Crumb-derived).
  2. Discard the in vitro POTENCY (IC50 2000 nM) and re-solve the IC50 so the
     curve passes through the empirical anchor at the clinical free Cmax:

         b1 = 0.312  at  c1 = 12.2 nM free
         x1 = b1/(1-b1) = 0.453488
         IC50 = c1 / x1^(1/n) = 12.2 / 0.453488^1.25 = 32.78 nM

     This reproduces Task F's implied IC50 of 32.8 nM exactly, which is the
     consistency check that the re-solve is the same object Task F reported.
  3. Evaluate the same curve at 2x and 3x the free concentration:

         b(c) = (c/32.78)^0.8 / (1 + (c/32.78)^0.8)

         1x   free 12.2 nM  ->  31.20%   (the anchor itself)
         2x   free 24.4 nM  ->  44.12%
         3x   free 36.6 nM  ->  52.20%

WHAT THIS ASSUMES, AND IT IS NOT SMALL
    Re-scaling potency while keeping the in vitro slope assumes the empirical
    anchor and the in vitro curve differ by a horizontal shift only. The 61x gap
    between them is unexplained (Task F/G), so the true shape is not known. If
    the real mechanism is trapped / use-dependent block the slope need not be
    0.80 at all. Hill sensitivity on the SAME anchor:
         n = 0.6 -> 2x = 40.7%, 3x = 46.7%
         n = 0.8 -> 2x = 44.1%, 3x = 52.2%   <- used
         n = 1.0 -> 2x = 47.6%, 3x = 57.6%
         n = 1.2 -> 2x = 51.0%, 3x = 62.9%
    n = 0.80 is neither the most nor the least conservative choice in that span.

Verapamil: Ba2+-derived mapping ONLY. The Ca2+-corrected arm is retired here -
Task H showed it is self-falsifying at the monotherapy level (it predicts 94-98%
of the population loses automaticity on verapamil alone at 480 mg/day peak).

Only ivabradine's exposure rises. Verapamil is the inhibitor; its own clearance
is not altered by itself.

HARD RULE (config study_integrity.no_pair_feedback): the 31.2% anchor is
untouched. The 2x/3x values are derived from it by PK scaling alone - no pair
outcome informs them. Task D's retired 3.5x over-block figure is not used.
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

B_IVAB_1X = 0.312       # empirical anchor, untouched
B_IVAB_2X = 0.4412      # derived above
B_IVAB_3X = 0.5220      # derived above
B_IVAB_7X = 0.6827      # ketoconazole-equivalent (~7x AUC), BOUNDING ARM only:
                        # a STRONG CYP3A4 inhibitor, which the label
                        # CONTRAINDICATES. Verapamil is a MODERATE inhibitor
                        # ("avoid concomitant use"). Included so the model can
                        # be asked whether it reproduces the regulatory
                        # gradient between "avoid" and "contraindicated".

# Verapamil rungs. Includes the exact Ba2+ chronic-oral band edges so the
# "does it cross inside the band" question is answered on simulated rungs
# rather than by interpolation:
#   240 mg/day  2.9% - 14.0%      480 mg/day  10.8% - 30.0%
VER = [0.0, 0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25,
       0.275, 0.30, 0.325, 0.35, 0.375, 0.40]
BAND_EDGES = [0.029, 0.108, 0.14]     # need the 0x and 1x arms too
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

    grid = []
    for st in STATES:
        for bc in VER:                                  # 2x and 3x arms
            for bf in (B_IVAB_2X, B_IVAB_3X, B_IVAB_7X):
                grid.append((st, round(bc, 6), round(bf, 6)))
        for bc in BAND_EDGES:                           # 0x and 1x at new rungs
            for bf in (0.0, B_IVAB_1X):
                grid.append((st, round(bc, 6), round(bf, 6)))
    seen, g2 = set(), []
    for p in grid:
        if p not in seen:
            seen.add(p)
            g2.append(p)
    grid = g2
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
                    if k % 400 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)
    print("SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
