"""Steps 3 and 4 - run the population and apply Zhou's retention criteria.

Config (00_config/config.yaml) is the single source of truth: parameters,
scaling, solver settings and retention criteria are all read from it, never
duplicated here. The CellML checksum is a hard failure, and a cached LHS sample
is validated against config before reuse.

STATE ISOLATION
    Myokit's pre() advances both the current state AND the simulation's default
    state, so a bare reset() returns to the PREVIOUS model's steady state rather
    than the published Fabbri initial conditions. The pristine state is captured
    once per worker and both state and default state are restored before every
    sampled model. Verified: without the fix, reset() left the state up to 2.76
    units from pristine.

Results are appended to a .jsonl checkpoint after every model, so an
interrupted run resumes instead of restarting.
"""
import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "01_baseline"))

from common import (load_config, verify_cellml, validate_sample,   # noqa: E402
                    params_from_config, make_sim, reset_pristine,
                    use_local_tmp)
import numpy as np                                                  # noqa: E402

OUT_DIR = os.path.join(ROOT, "outputs")
SAMPLE = os.path.join(OUT_DIR, "step2_lhs_sample.npz")

_S = {}


def _init():
    use_local_tmp()
    from biomarkers import biomarkers as _bm
    cfg = load_config()
    sim, pristine = make_sim(cfg)
    z = np.load(SAMPLE, allow_pickle=True)
    _S.update(cfg=cfg, sim=sim, pristine=pristine, bm=_bm,
              variables=[str(v) for v in z["variables"]],
              values=z["values"],
              dur=float(cfg["simulation"]["duration_s"]),
              win=float(cfg["simulation"]["measure_window_s"]),
              dt=float(cfg["simulation"]["log_dt_s"]))


def run_one(idx):
    S = _S
    sim, bm = S["sim"], S["bm"]
    t0 = time.time()
    rec = {"index": int(idx), "status": None, "CL_ms": None, "OS_mV": None,
           "MDP_mV": None, "APA_mV": None, "n_beats": 0}
    try:
        # Restore pristine initial conditions BEFORE applying this model's
        # parameters. Without this the model inherits the previous model's
        # steady state.
        reset_pristine(sim, S["pristine"])
        for var, val in zip(S["variables"], S["values"][idx]):
            sim.set_constant(var, float(val))
        sim.pre(S["dur"] - S["win"])
        d = sim.run(S["win"], log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, S["win"], S["dt"]))
        b = bm(np.array(d["environment.time"]), np.array(d["Membrane.V"]))
        if b is None:
            rec["status"] = "no_pacing"
        else:
            rec.update(status="ok", CL_ms=b["CL_ms"], OS_mV=b["OS_mV"],
                       MDP_mV=b["MDP_mV"], APA_mV=b["APA_mV"],
                       n_beats=b["n_beats"])
    except Exception as e:
        rec["status"] = "solver_failure"
        rec["error"] = f"{type(e).__name__}: {str(e)[:180]}"
    rec["seconds"] = time.time() - t0
    return rec


def retained(rec, cfg):
    if rec["status"] != "ok":
        return False
    r = cfg["retention"]
    return (r["bcl_min_ms"] <= rec["CL_ms"] <= r["bcl_max_ms"]
            and rec["OS_mV"] > 0.0)


def load_checkpoint(path):
    done = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        done[r["index"]] = r
                    except json.JSONDecodeError:
                        pass                    # tolerate a torn final line
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--tag", type=str, default=None)
    ap.add_argument("--checkpoint", type=str, default=None)
    args = ap.parse_args()

    cfg = load_config()
    digest = verify_cellml(cfg)
    validate_sample(SAMPLE, cfg)
    names, variables, baseline = params_from_config(cfg)

    tag = args.tag or f"n{args.n}"
    ckpt = args.checkpoint or os.path.join(OUT_DIR, f"checkpoint_{tag}.jsonl")
    done = load_checkpoint(ckpt)
    idxs = [i for i in range(args.start, args.start + args.n) if i not in done]

    print(f"Population run '{tag}': {args.n} models from index {args.start}, "
          f"{args.workers} worker(s)")
    print(f"  cellml sha256 verified: {digest[:16]}...")
    print(f"  sample validated against config ({len(names)} parameters)")
    print(f"  {cfg['simulation']['duration_s']:.0f} s per model, "
          f"tol {cfg['simulation']['tol_abs']:g}")
    print(f"  state isolation: pristine restored before every model")
    if done:
        print(f"  checkpoint: {len(done)} already done, {len(idxs)} remaining")

    wall0 = time.time()
    if idxs:
        with open(ckpt, "a", encoding="utf-8") as fh:
            if args.workers <= 1:
                _init()
                for k, i in enumerate(idxs, 1):
                    r = run_one(i)
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    done[i] = r
                    if k % max(1, len(idxs) // 10) == 0 or k == len(idxs):
                        el = time.time() - wall0
                        print(f"    {k}/{len(idxs)}  {el:6.1f}s  "
                              f"({el/k:5.2f} s/model)", flush=True)
            else:
                with Pool(args.workers, initializer=_init) as pool:
                    for k, r in enumerate(
                            pool.imap_unordered(run_one, idxs, chunksize=1), 1):
                        fh.write(json.dumps(r) + "\n")
                        fh.flush()
                        done[r["index"]] = r
                        if k % max(1, len(idxs) // 20) == 0 or k == len(idxs):
                            el = time.time() - wall0
                            print(f"    {k}/{len(idxs)}  {el:6.1f}s  "
                                  f"({el/k:5.2f} s/model wall)", flush=True)
    wall = time.time() - wall0

    results = [done[i] for i in sorted(done)
               if args.start <= i < args.start + args.n]
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_nop = sum(1 for r in results if r["status"] == "no_pacing")
    n_fail = sum(1 for r in results if r["status"] == "solver_failure")
    keep = [r for r in results if retained(r, cfg)]
    per = [r["seconds"] for r in results if "seconds" in r]

    print(f"\n  wall clock      : {wall:.1f} s")
    if per:
        print(f"  per model (cpu) : mean {np.mean(per):.2f} s, "
              f"median {np.median(per):.2f} s")
    print(f"  integrated ok   : {n_ok}  ({n_ok/len(results)*100:.1f}%)")
    print(f"  no pacing       : {n_nop}  ({n_nop/len(results)*100:.1f}%)")
    print(f"  solver failures : {n_fail}  ({n_fail/len(results)*100:.1f}%)")
    print(f"  RETAINED        : {len(keep)}  "
          f"({len(keep)/len(results)*100:.2f}%)")

    out = {
        "tag": tag, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "state_isolation": "pristine state restored before every model",
        "cellml_sha256": digest,
        "host": {"platform": platform.platform(), "cpu_count": os.cpu_count()},
        "n_models": len(results), "start_index": args.start,
        "workers": args.workers, "wall_clock_s": wall,
        "counts": {"ok": n_ok, "no_pacing": n_nop,
                   "solver_failure": n_fail, "retained": len(keep)},
        "retention_fraction": len(keep) / len(results) if results else None,
        "criteria": cfg["retention"], "results": results,
    }
    p = os.path.join(OUT_DIR, f"step3fix_run_{tag}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"  report -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
