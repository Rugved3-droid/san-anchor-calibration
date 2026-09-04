"""P1 threshold sweep across the completed 1028-model retained population.

DEFINITIONS ARE NOT REDEFINED HERE. This module imports
04_pharmacology/population_block_sweep.py and reuses its BLOCKS, PREPACE_S,
WINDOW_S, LOG_DT, _one(), run_model() and _pool_init() verbatim. The only thing
that changes is WHICH model indices are fed in and WHERE the checkpoint lives:

  * indices come from the completed population npz (1028 retained) instead of
    the historical 940-model json (188 retained);
  * checkpoints are written under 08_taskP/threshold/ so the frozen historical
    outputs/taskA_*_checkpoint.jsonl are never modified.

The historical 188 records are copied in as a starting checkpoint, exactly as
the P1 population run reused the historical 940. That reuse is justified by the
same evidence: re-running models in the current environment reproduces the
frozen values bit-identically (08_taskP/P1_verification.json, and the --recheck
mode below re-verifies it for the sweep specifically).

Usage:
    python 08_taskP/P1_threshold_sweep.py --current G_CaL --workers 8
    python 08_taskP/P1_threshold_sweep.py --current G_f   --workers 8
    python 08_taskP/P1_threshold_sweep.py --current G_CaL --recheck 5
"""
import argparse
import json
import os
import shutil
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "04_pharmacology"))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

import population_block_sweep as pbs                                  # noqa: E402

NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
DEST = os.path.join(ROOT, "08_taskP", "threshold")
os.makedirs(DEST, exist_ok=True)


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
    ap.add_argument("--recheck", type=int, default=0,
                    help="re-run N already-done models and verify identity")
    args = ap.parse_args()

    # ---- the definitions actually in force, echoed for the record ----------
    print(f"definitions imported from {pbs.__file__}")
    print(f"  BLOCKS    : {pbs.BLOCKS[0]:.2f}..{pbs.BLOCKS[-1]:.2f} "
          f"({len(pbs.BLOCKS)} levels, step "
          f"{pbs.BLOCKS[1]-pbs.BLOCKS[0]:.2f})")
    print(f"  PREPACE_S : {pbs.PREPACE_S}")
    print(f"  WINDOW_S  : {pbs.WINDOW_S}")
    print(f"  LOG_DT    : {pbs.LOG_DT}")

    z = np.load(NPZ, allow_pickle=True)
    retained = [int(i) for i in z["model_index"]]
    print(f"\npopulation: {os.path.basename(NPZ)}  n_retained={len(retained)}")

    ck = os.path.join(DEST, f"taskP_{args.current}_checkpoint.jsonl")
    hist_ck = os.path.join(ROOT, "outputs",
                           f"taskA_{args.current}_checkpoint.jsonl")
    if not os.path.exists(ck) and os.path.exists(hist_ck):
        shutil.copyfile(hist_ck, ck)
        print(f"  seeded checkpoint from frozen {os.path.basename(hist_ck)} "
              f"({len(load_jsonl(ck))} records); original untouched")

    done = load_jsonl(ck)

    # ---- recheck mode: prove the seeded records still reproduce ------------
    if args.recheck:
        pbs._init(args.current, pbs.PREPACE_S)
        ii = [i for i in sorted(done) if done[i]["status"] == "ok"][:args.recheck]
        print(f"\nRECHECK: re-running {len(ii)} seeded models")
        allok = True
        for i in ii:
            t = time.time()
            r = pbs.run_model(i)
            o = done[i]
            same = (r["threshold"] == o["threshold"]
                    and r["monotone_ok"] == o["monotone_ok"]
                    and r["levels"] == o["levels"])
            allok &= same
            print(f"  {i:5d}  threshold {str(r['threshold']):>6} vs "
                  f"{str(o['threshold']):>6}  levels identical: {same}  "
                  f"({time.time()-t:.1f} s)")
        print(f"  ALL IDENTICAL: {allok}")
        return 0 if allok else 1

    todo = [i for i in retained if i not in done]
    print(f"  checkpoint: {len(done)} done, {len(todo)} to run", flush=True)
    # any done-but-not-retained records are historical leftovers; keep, ignore
    extra = [i for i in done if i not in set(retained)]
    if extra:
        print(f"  note: {len(extra)} checkpoint records not in this "
              f"population; ignored in the summary")

    t0 = time.time()
    if todo:
        with open(ck, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=pbs._pool_init,
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
    unc = [t for t in th if t is not None]
    out = {"current": args.current,
           "population_file": os.path.basename(NPZ),
           "population_sha256_manifest": "see population_manifest",
           "n_models": len(recs),
           "definitions_source": os.path.relpath(pbs.__file__, ROOT),
           "blocks": len(pbs.BLOCKS), "prepace_s": pbs.PREPACE_S,
           "window_s": pbs.WINDOW_S,
           "n_never_quiescent": sum(1 for t in th if t is None),
           "n_non_monotone": sum(1 for r in recs if not r["monotone_ok"]),
           "n_error": sum(1 for r in recs if r["status"] != "ok"),
           "threshold_median_uncensored": (float(np.median(unc)) if unc
                                           else None),
           "records": [{"index": r["index"], "status": r["status"],
                        "threshold": r["threshold"],
                        "monotone_ok": r["monotone_ok"],
                        "levels": r["levels"]} for r in recs]}
    op = os.path.join(DEST, f"taskP_{args.current}_population_sweep.json")
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\n  n={out['n_models']}  never-quiescent={out['n_never_quiescent']}"
          f"  non-monotone={out['n_non_monotone']}  errors={out['n_error']}")
    print(f"  -> {op}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
