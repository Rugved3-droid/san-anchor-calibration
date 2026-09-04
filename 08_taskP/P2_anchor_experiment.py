"""P2 - decisive full-population anchor experiment.

SIMULATION CODE IS NOT REDEFINED HERE. This module imports
04_pharmacology/taskL_anchor_switch.py and reuses its `_init()`, `_job()`,
PREPACE_S, WINDOW_S and LOG_DT verbatim. `_job((model, state, b_cal, b_f))`
resets the pristine state, scales G_CaL and G_f, pre-paces, runs, and returns
bpm (None = quiescent). That is the frozen automaticity definition.

What differs from Task L, and only this:
  * population = the 1028 retained models of the completed P1 population
    (their ORIGINAL indices index the same frozen 5000-row LHS that
    taskL._init() loads, so no remapping is involved);
  * control state only;
  * ivabradine 1x only, three anchors;
  * verapamil restricted to the frozen rungs inside the 480 mg/day band;
  * jobs are ordered model-major so an interrupted run yields COMPLETE data
    for a prefix of models rather than partial data for all of them. Ordering
    cannot affect values - P1 gate 1 established state isolation.

Nothing here fits, calibrates, interpolates or refines anything.
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

NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
MAN = os.path.join(ROOT, "zhou_san_run",
                   "population_manifest_20260823T094616Z.json")
DEST = os.path.join(ROOT, "08_taskP", "p2")
os.makedirs(DEST, exist_ok=True)
CKPT = os.path.join(DEST, "P2_checkpoint.jsonl")

STATE = "control"

# --- FROZEN INPUTS, copied from the frozen sources, not recomputed ---------
# taskL_anchor_switch.VER, restricted to the 480 mg/day band (10.8%-30.0%).
BAND_LO, BAND_HI = 0.108, 0.300
VER_BAND = [b for b in tl.VER if BAND_LO - 1e-9 <= b <= BAND_HI + 1e-9]

# 1x effective model-equivalent I_f block for each anchor. Doesch and 10-year
# are taskL_anchor_switch.NEW_BF[0] and [3]; the 36-month value is the frozen
# taskG_analyse.B_IVAB.
ANCHORS = [("Doesch 2007 (PRIMARY)", 0.5840, "taskL_anchor_switch.NEW_BF[0]"),
           ("10-year cohort",        0.5090, "taskL_anchor_switch.NEW_BF[3]"),
           ("36-month (superseded)", 0.3120, "taskG_analyse.B_IVAB")]

B_F_VALUES = [0.0] + [a[1] for a in ANCHORS]
B_CAL_VALUES = [0.0] + VER_BAND


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
                    done.add((r["model"], r["state"],
                              round(r["b_cal"], 6), round(r["b_f"], 6)))
                except json.JSONDecodeError:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    man = json.load(open(MAN, encoding="utf-8"))
    z = np.load(NPZ, allow_pickle=True)
    models = [int(i) for i in z["model_index"]]

    print(f"simulation code : {tl.__file__}")
    print(f"  PREPACE_S {tl.PREPACE_S}  WINDOW_S {tl.WINDOW_S}  "
          f"LOG_DT {tl.LOG_DT}")
    print(f"population      : {os.path.basename(NPZ)}")
    print(f"  n_retained {man['n_retained']}  sha256 "
          f"{man['population_sha256'][:16]}...")
    print(f"state           : {STATE} only")
    print(f"verapamil rungs : {VER_BAND}   (480 mg/day band "
          f"{BAND_LO:.1%}-{BAND_HI:.1%}, from taskL_anchor_switch.VER)")
    print(f"ivabradine 1x   : {[(a[0], a[1]) for a in ANCHORS]}")

    grid = [(round(bc, 6), round(bf, 6))
            for bc in B_CAL_VALUES for bf in B_F_VALUES]
    print(f"grid            : {len(grid)} conditions x {len(models)} models "
          f"= {len(grid)*len(models)} sims")

    done = load_done()
    # model-major ordering: finish whole models before starting new ones
    todo = [(mi, STATE, bc, bf) for mi in models for (bc, bf) in grid
            if (mi, STATE, bc, bf) not in done]
    print(f"checkpoint      : {len(done)} done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(CKPT, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=tl._init) as pool:
                for k, r in enumerate(pool.imap(tl._job, todo, chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    if k % 500 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min  "
                              f"[{k/el:.2f} sims/s]", flush=True)
        el = time.time() - t0
        with open(os.path.join(DEST, "P2_throughput.json"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps({
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sims": len(todo), "wall_s": el, "workers": args.workers,
                "sims_per_s": len(todo) / el,
                "cpu_s_per_sim": el * args.workers / len(todo)}) + "\n")
    print("P2 SIMULATION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
