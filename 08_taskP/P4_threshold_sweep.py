"""P4 threshold sweep - frozen definitions, independent P4 population.

DEFINITIONS ARE NOT REDEFINED. Imports
04_pharmacology/population_block_sweep.py and reuses BLOCKS, PREPACE_S,
WINDOW_S, LOG_DT, _one(), run_model() and _init() verbatim - the same code and
the same ladder used for P1.

Only two things change:
  * the LHS the sweep reads is the P4 sample (seed 788156539), not P1's;
  * indices come from the P4 retained population, and checkpoints live in
    08_taskP/p4_threshold/.

No historical seeding: P4 is an independent population, so every model is
simulated fresh.

WINDOWS SPAWN SAFETY
  Workers re-import this module as __mp_main__, so the SAMPLE rebinding is at
  MODULE level and each worker re-asserts the loaded sample's seed before
  simulating. Rebinding inside main() would leave workers silently reading the
  P1 sample.
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

import population_block_sweep as pbs                                # noqa: E402

P4_SEED = 788156539
P4_WORK = os.path.join(ROOT, "zhou_san_run_p4")
NPZ = os.path.join(P4_WORK, "population_retained_20260824T232853Z.npz")
DEST = os.path.join(ROOT, "08_taskP", "p4_threshold")
os.makedirs(DEST, exist_ok=True)

# ---- the only sampling difference, applied at MODULE level ---------------
pbs.SAMPLE = os.path.join(P4_WORK, "lhs_sample.npz")

_orig_init = pbs._init


def _p4_init(current, prepace):
    z = np.load(pbs.SAMPLE, allow_pickle=True)
    if int(z["seed"]) != P4_SEED:
        raise SystemExit(f"FATAL: worker sample seed {int(z['seed'])} "
                         f"!= {P4_SEED}")
    _orig_init(current, prepace)


def _pool_init(current, prepace):
    _p4_init(current, prepace)


def load_jsonl(p):
    d = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        d[r["index"]] = r
                    except json.JSONDecodeError:
                        pass
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default="G_CaL", choices=["G_CaL", "G_f"])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    print(f"definitions : {pbs.__file__}")
    print(f"  BLOCKS {pbs.BLOCKS[0]:.2f}..{pbs.BLOCKS[-1]:.2f} "
          f"({len(pbs.BLOCKS)} levels)  PREPACE_S {pbs.PREPACE_S}  "
          f"WINDOW_S {pbs.WINDOW_S}")
    print(f"sample      : {pbs.SAMPLE}")
    z = np.load(pbs.SAMPLE, allow_pickle=True)
    print(f"  seed {int(z['seed'])}  shape {z['scales'].shape}")
    zz = np.load(NPZ, allow_pickle=True)
    retained = [int(i) for i in zz["model_index"]]
    print(f"population  : {os.path.basename(NPZ)}  n={len(retained)}")

    ck = os.path.join(DEST, f"P4_{args.current}_checkpoint.jsonl")
    done = load_jsonl(ck)
    todo = [i for i in retained if i not in done]
    print(f"checkpoint  : {len(done)} done, {len(todo)} to run", flush=True)

    t0 = time.time()
    if todo:
        with open(ck, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_pool_init,
                      initargs=(args.current, pbs.PREPACE_S)) as pool:
                for k, rec in enumerate(
                        pool.imap_unordered(pbs.run_model, todo, chunksize=1),
                        1):
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    done[rec["index"]] = rec
                    if k % 10 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"    {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min",
                              flush=True)

    recs = [done[i] for i in retained if i in done]
    th = [r["threshold"] for r in recs if r["status"] == "ok"]
    out = {"current": args.current, "population_file": os.path.basename(NPZ),
           "seed": P4_SEED, "n_models": len(recs),
           "definitions_source": os.path.relpath(pbs.__file__, ROOT),
           "blocks": len(pbs.BLOCKS), "prepace_s": pbs.PREPACE_S,
           "window_s": pbs.WINDOW_S,
           "n_never_quiescent": sum(1 for t in th if t is None),
           "n_non_monotone": sum(1 for r in recs if not r["monotone_ok"]),
           "n_error": sum(1 for r in recs if r["status"] != "ok"),
           "records": [{"index": r["index"], "status": r["status"],
                        "threshold": r["threshold"],
                        "monotone_ok": r["monotone_ok"],
                        "levels": r["levels"]} for r in recs]}
    op = os.path.join(DEST, f"P4_{args.current}_population_sweep.json")
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  n={out['n_models']}  never-quiescent="
          f"{out['n_never_quiescent']}  non-monotone={out['n_non_monotone']}"
          f"  errors={out['n_error']}")
    print(f"  -> {op}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
