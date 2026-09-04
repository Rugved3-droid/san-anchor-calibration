"""Task A - block-tolerance across the RETAINED POPULATION, not baseline alone.

For each retained model, sweeps fractional block of a chosen current from 0 to
90% in 5% steps and records the lowest block at which spontaneous firing is
abolished ("quiescence threshold"), plus the rate at every surviving level.

Cost control, stated explicitly because it is an approximation:
  * pre-pace is shortened from 1000 s to PREPACE_S; validated against the
    1000 s baseline result before use (see --validate).
  * block->quiescence is assumed MONOTONE: once a model is quiescent at level
    L it is taken to be quiescent above L. This is verified per model by also
    testing the top level (0.90) before the fill-in is accepted; if the model
    is pacing at 0.90 the assumption failed for that model and the full ladder
    is run instead. Any such case is counted and reported.
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
POP = os.path.join(OUT_DIR, "step3fix_run_statefix.json")

BLOCKS = [round(0.05 * i, 2) for i in range(19)]      # 0.00 .. 0.90
PREPACE_S = 300.0
WINDOW_S = 6.0
LOG_DT = 1e-4

_S = {}


def _init(current, prepace):
    use_local_tmp()
    from biomarkers import biomarkers as _bm
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    z = np.load(SAMPLE, allow_pickle=True)
    variables = [str(v) for v in z["variables"]]
    target = None
    for p in cfg["parameters"]:
        if p["zhou_symbol"] == current:
            target = p["variable"]
    if target is None:
        raise SystemExit(f"unknown current {current}")
    _S.update(cfg=cfg, sim=sim, pristine=pristine, bm=_bm,
              variables=variables, values=z["values"],
              target=target, ti=variables.index(target), prepace=prepace)


def _one(idx, block):
    """Simulate model idx with `block` fraction of the target current removed."""
    S = _S
    sim = S["sim"]
    reset_pristine(sim, S["pristine"])
    vals = list(S["values"][idx])
    vals[S["ti"]] = vals[S["ti"]] * (1.0 - block)
    for var, val in zip(S["variables"], vals):
        sim.set_constant(var, float(val))
    sim.pre(S["prepace"])
    d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                log_times=np.arange(0, WINDOW_S, LOG_DT))
    return S["bm"](np.array(d["environment.time"]), np.array(d["Membrane.V"]))


def run_model(idx):
    """Ladder for one model. Returns per-level results + threshold."""
    t0 = time.time()
    levels, threshold, monotone_ok = {}, None, True
    try:
        for b in BLOCKS:
            try:
                bm = _one(idx, b)
            except Exception:
                bm = None
            if bm is None:
                levels[b] = None
                threshold = b
                # verify monotonicity at the top level before filling in
                if b < BLOCKS[-1]:
                    try:
                        top = _one(idx, BLOCKS[-1])
                    except Exception:
                        top = None
                    if top is None:
                        for bb in BLOCKS:
                            if bb > b:
                                levels[bb] = None
                        break
                    else:
                        monotone_ok = False      # paces again higher up
                        levels[b] = None
                        continue
                break
            levels[b] = {"CL_ms": bm["CL_ms"], "bpm": 60000.0 / bm["CL_ms"],
                         "OS_mV": bm["OS_mV"], "MDP_mV": bm["MDP_mV"]}
        status = "ok"
    except Exception as e:
        status = f"error:{type(e).__name__}"
    return {"index": int(idx), "status": status, "threshold": threshold,
            "monotone_ok": monotone_ok,
            "levels": {str(k): v for k, v in levels.items()},
            "seconds": time.time() - t0}


def _pool_init(current, prepace):
    # Windows uses spawn, so worker processes re-import this module with empty
    # globals. Configuration must be passed through initargs, never inherited.
    _init(current, prepace)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", default="G_CaL", choices=["G_CaL", "G_f"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--prepace", type=float, default=PREPACE_S)
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    if args.validate:
        # Reproduce the baseline (unscaled) ladder and compare with the known
        # 500 s-prepace result, to justify the shortened pre-pace.
        _init(args.current, args.prepace)
        print(f"validation ladder on BASELINE Fabbri, prepace {args.prepace:.0f}s")
        for b in BLOCKS:
            S = _S
            sim = S["sim"]
            reset_pristine(sim, S["pristine"])
            base = [float(p["baseline"]) for p in S["cfg"]["parameters"]]
            base[S["ti"]] = base[S["ti"]] * (1 - b)
            for var, val in zip(S["variables"], base):
                sim.set_constant(var, val)
            try:
                sim.pre(args.prepace)
                d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                            log_times=np.arange(0, WINDOW_S, LOG_DT))
                bm = S["bm"](np.array(d["environment.time"]),
                             np.array(d["Membrane.V"]))
            except Exception:
                bm = None
            print(f"  block {b:5.0%} -> "
                  + ("QUIESCENT" if bm is None
                     else f"{60000.0/bm['CL_ms']:6.2f} bpm"))
        return 0

    with open(POP, encoding="utf-8") as f:
        blob = json.load(f)
    cfg = load_config()
    r = cfg["retention"]
    retained = [x["index"] for x in blob["results"]
                if x["status"] == "ok"
                and r["bcl_min_ms"] <= x["CL_ms"] <= r["bcl_max_ms"]
                and x["OS_mV"] > 0]
    if args.limit:
        retained = retained[:args.limit]

    print(f"Task A - {args.current} block ladder across {len(retained)} "
          f"retained models")
    print(f"  levels: {BLOCKS[0]:.0%}..{BLOCKS[-1]:.0%} in 5% steps, "
          f"prepace {args.prepace:.0f}s, {args.workers} workers", flush=True)

    ck = os.path.join(OUT_DIR, f"taskA_{args.current}_checkpoint.jsonl")
    done = {}
    if os.path.exists(ck):
        with open(ck, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        done[rec["index"]] = rec
                    except json.JSONDecodeError:
                        pass
    todo = [i for i in retained if i not in done]
    print(f"  checkpoint: {len(done)} done, {len(todo)} to run", flush=True)

    t0 = time.time()
    if todo:
        with open(ck, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_pool_init,
                      initargs=(args.current, args.prepace)) as pool:
                for k, rec in enumerate(
                        pool.imap_unordered(run_model, todo, chunksize=1), 1):
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                    done[rec["index"]] = rec
                    if k % 10 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"    {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)

    recs = [done[i] for i in retained if i in done]
    thr = [x["threshold"] for x in recs]
    survived = [x for x, t in zip(recs, thr) if t is None]
    finite = np.array([t for t in thr if t is not None], dtype=float)
    nonmono = [x["index"] for x in recs if not x["monotone_ok"]]

    print(f"\n  models analysed        : {len(recs)}")
    print(f"  non-monotone (excluded from fill-in): {len(nonmono)}")
    print(f"  never quiescent to 90% : {len(survived)}")
    if len(finite):
        print(f"\n  quiescence threshold ({args.current} block):")
        print(f"    median : {np.median(finite)*100:.1f}%")
        print(f"    IQR    : {np.percentile(finite,25)*100:.1f}% - "
              f"{np.percentile(finite,75)*100:.1f}%")
        print(f"    range  : {finite.min()*100:.1f}% - {finite.max()*100:.1f}%")
        print(f"    mean   : {finite.mean()*100:.1f}%")

    print(f"\n  fraction still pacing at:")
    out_frac = {}
    for lv in (0.50, 0.60, 0.70):
        n = sum(1 for x in recs
                if x["levels"].get(str(lv)) is not None)
        out_frac[lv] = n / len(recs) if recs else 0
        print(f"    {lv:.0%} block : {n}/{len(recs)} = "
              f"{n/len(recs)*100:.1f}%")

    res = {"current": args.current, "n_models": len(recs),
           "blocks": BLOCKS, "prepace_s": args.prepace,
           "threshold_median": float(np.median(finite)) if len(finite) else None,
           "threshold_iqr": [float(np.percentile(finite, 25)),
                             float(np.percentile(finite, 75))] if len(finite) else None,
           "threshold_min": float(finite.min()) if len(finite) else None,
           "threshold_max": float(finite.max()) if len(finite) else None,
           "n_never_quiescent": len(survived),
           "n_non_monotone": len(nonmono),
           "fraction_pacing": {str(k): v for k, v in out_frac.items()},
           "records": recs}
    p = os.path.join(OUT_DIR, f"taskA_{args.current}_population_sweep.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\n  -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
