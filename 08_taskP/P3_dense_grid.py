"""P3 Option B - full Task-L1 dense grid on the committed 500-model subset.

SIMULATION CODE IS NOT REDEFINED. Imports 04_pharmacology/taskL_anchor_switch.py
and reuses _init(), _job(), PREPACE_S, WINDOW_S, LOG_DT verbatim - the same code
used for Task L1, P2 and P4.

GRID (all values frozen, copied from the frozen sources, none recomputed):

  states   : control, iso                        taskL_anchor_switch.STATES
  b_cal    : the full 12-rung VER ladder         taskL_anchor_switch.VER
             [0.0, 0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25,
              0.275, 0.30, 0.40]
  b_f      : 0.0 (no ivabradine) plus the three anchors at 1x/2x/3x:
               Doesch    0.5840 / 0.7097 / 0.7717   NEW_BF[0..2]
               10-year   0.5090 / 0.6435 / 0.7140   NEW_BF[3..5]
               36-month  0.3120 / 0.4412 / 0.5220   taskI B_IVAB_1X/2X/3X
             plus 36-month 7x = 0.6827             taskI B_IVAB_7X

The 7x arm is NOT one of the three specified PK arms. It is included ONLY so
that the existing Figure 3 "strong inhibitor" trace can be regenerated on P3
data instead of silently dropped or silently carried over from the historical
188-model run. It is flagged as such everywhere and is excluded from the
1x/2x/3x analyses.

  conditions = 2 states x 11 b_f x 12 b_cal = 264
  simulations = 264 x 500 = 132,000

Model-major ordering so an interrupted run yields COMPLETE condition sets for a
prefix of models. Ordering cannot affect values (P1 gate 1: state isolation).

Nothing is fitted; no pair result informs any parameter.
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

SUBSET = os.path.join(ROOT, "08_taskP", "P3_subset_500.json")
COMMIT = os.path.join(ROOT, "08_taskP", "P3_SUBSET_COMMITMENT.json")
DEST = os.path.join(ROOT, "08_taskP", "p3")
os.makedirs(DEST, exist_ok=True)
CKPT = os.path.join(DEST, "P3_dense_checkpoint.jsonl")

# --- frozen anchor x arm mappings ----------------------------------------
ARMS = [
    ("Doesch 2007 (PRIMARY)", "1x", 0.5840), ("Doesch 2007 (PRIMARY)", "2x", 0.7097),
    ("Doesch 2007 (PRIMARY)", "3x", 0.7717),
    ("10-year cohort", "1x", 0.5090), ("10-year cohort", "2x", 0.6435),
    ("10-year cohort", "3x", 0.7140),
    ("36-month (superseded)", "1x", 0.3120), ("36-month (superseded)", "2x", 0.4412),
    ("36-month (superseded)", "3x", 0.5220),
    ("36-month (superseded)", "7x_bounding_NOT_a_specified_arm", 0.6827),
]
B_F_VALUES = [0.0] + [a[2] for a in ARMS]
VER = list(tl.VER)
STATES = list(tl.STATES)


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

    commit = json.load(open(COMMIT, encoding="utf-8"))
    models = json.load(open(SUBSET, encoding="utf-8"))
    import hashlib
    sub_sha = hashlib.sha256(
        json.dumps(models, separators=(",", ":")).encode("utf-8")).hexdigest()
    if sub_sha != commit["subset_sha256"]:
        raise SystemExit(f"FATAL: subset hash mismatch\n  file {sub_sha}\n"
                         f"  commitment {commit['subset_sha256']}")

    print(f"simulation code : {tl.__file__}")
    print(f"  PREPACE_S {tl.PREPACE_S}  WINDOW_S {tl.WINDOW_S}  "
          f"LOG_DT {tl.LOG_DT}")
    print(f"subset          : {len(models)} models, sha256 {sub_sha[:16]}... "
          f"VERIFIED against commitment")
    print(f"  seed {commit['P3_SUBSET_SEED']}  from "
          f"{commit['source_population']}")
    print(f"states          : {STATES}")
    print(f"b_cal ladder    : {VER}")
    print(f"b_f values      : {B_F_VALUES}")

    grid = [(st, round(bc, 6), round(bf, 6))
            for st in STATES for bf in B_F_VALUES for bc in VER]
    print(f"grid            : {len(grid)} conditions x {len(models)} models "
          f"= {len(grid)*len(models)} sims")

    done = load_done()
    todo = [(mi, st, bc, bf) for mi in models for (st, bc, bf) in grid
            if (mi, st, bc, bf) not in done]
    print(f"checkpoint      : {len(done)} done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=tl._init) as pool:
                for k, r in enumerate(pool.imap(tl._job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    if k % 1000 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min  "
                              f"[{k/el:.2f} sims/s]", flush=True)
    print("P3 DENSE GRID COMPLETE", flush=True)


if __name__ == "__main__":
    main()
