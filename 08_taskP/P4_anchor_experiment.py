"""P4 decisive anchor replication - the exact P2 experiment on the P4 population.

SIMULATION CODE IS NOT REDEFINED. Imports 04_pharmacology/taskL_anchor_switch.py
and reuses its _init(), _job(), PREPACE_S, WINDOW_S, LOG_DT verbatim - the same
code P2 used.

Only differences from P2:
  * the LHS read is the P4 sample (seed 788156539);
  * models are the 1044 retained P4 models;
  * checkpoint lives in 08_taskP/p4/.

Everything else is identical to P2: control state only, the same seven frozen
I_CaL rungs, ivabradine 1x only, the same three frozen anchor mappings.

WINDOWS SPAWN SAFETY
  Workers re-import this module as __mp_main__, so the SAMPLE rebinding is at
  MODULE level and each worker asserts the sample seed before simulating.
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "04_pharmacology"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

import taskL_anchor_switch as tl                                    # noqa: E402

P4_SEED = 788156539
P4_WORK = os.path.join(ROOT, "zhou_san_run_p4")
NPZ = os.path.join(P4_WORK, "population_retained_20260824T232853Z.npz")
DEST = os.path.join(ROOT, "08_taskP", "p4")
os.makedirs(DEST, exist_ok=True)
CKPT = os.path.join(DEST, "P4_pair_checkpoint.jsonl")

# ---- the only sampling difference, at MODULE level -----------------------
tl.SAMPLE = os.path.join(P4_WORK, "lhs_sample.npz")

STATE = "control"
BAND_LO, BAND_HI = 0.108, 0.300
VER_BAND = [b for b in tl.VER if BAND_LO - 1e-9 <= b <= BAND_HI + 1e-9]
ANCHORS = [("Doesch 2007 (PRIMARY)", 0.5840), ("10-year cohort", 0.5090),
           ("36-month (superseded)", 0.3120)]
B_F_VALUES = [0.0] + [a[1] for a in ANCHORS]
B_CAL_VALUES = [0.0] + VER_BAND

_orig_init = tl._init


def _p4_init():
    z = np.load(tl.SAMPLE, allow_pickle=True)
    if int(z["seed"]) != P4_SEED:
        raise SystemExit(f"FATAL: worker sample seed {int(z['seed'])} "
                         f"!= {P4_SEED}")
    _orig_init()


def load_done():
    done = set()
    if os.path.exists(CKPT):
        with open(CKPT, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done.add((r["model"], r["state"], round(r["b_cal"], 6),
                              round(r["b_f"], 6)))
                except json.JSONDecodeError:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    z = np.load(tl.SAMPLE, allow_pickle=True)
    zz = np.load(NPZ, allow_pickle=True)
    models = [int(i) for i in zz["model_index"]]
    print(f"simulation code : {tl.__file__}")
    print(f"  PREPACE_S {tl.PREPACE_S}  WINDOW_S {tl.WINDOW_S}  "
          f"LOG_DT {tl.LOG_DT}")
    print(f"sample          : {tl.SAMPLE}  seed {int(z['seed'])}")
    print(f"population      : {os.path.basename(NPZ)}  n={len(models)}")
    print(f"state           : {STATE} only")
    print(f"verapamil rungs : {VER_BAND}")
    print(f"ivabradine 1x   : {[(a, b) for a, b in ANCHORS]}")

    grid = [(round(bc, 6), round(bf, 6))
            for bc in B_CAL_VALUES for bf in B_F_VALUES]
    print(f"grid            : {len(grid)} conditions x {len(models)} models "
          f"= {len(grid)*len(models)} sims")

    done = load_done()
    todo = [(mi, STATE, bc, bf) for mi in models for (bc, bf) in grid
            if (mi, STATE, bc, bf) not in done]
    print(f"checkpoint      : {len(done)} done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_p4_init) as pool:
                for k, r in enumerate(pool.imap(tl._job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    if k % 500 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min  "
                              f"[{k/el:.2f} sims/s]", flush=True)
    print("P4 PAIR SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
