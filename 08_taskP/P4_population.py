"""P4 - independent 5000x12 population under the frozen, unused seed 788156539.

NOTHING IS REIMPLEMENTED. This module imports run_full_population.py and calls
its own main(), so the sampling, model build, solver, tolerances, duration,
pristine-state restoration, biomarkers, retention criteria and manifest writing
are byte-for-byte the code that produced the P1 population.

The ONLY differences are module-level rebindings applied before main() runs:

    rfp.SEED     20260816            -> 788156539   (the frozen P4 seed)
    rfp.WORK     zhou_san_run        -> zhou_san_run_p4
    rfp.CELLML / MMT / SAMPLE / RESULTS / _TMP  -> inside zhou_san_run_p4

Parameter ordering, bounds ([0,2]), scaling convention, N_MODELS, BCL band,
overshoot rule, DURATION_S, WINDOW_S, LOG_DT and tolerances are untouched -
they are read from the same 00_config/config.yaml.

WINDOWS SPAWN SAFETY
  Pool workers re-import this module as __mp_main__ and re-execute everything
  at module level, so the rebindings below are applied in every worker too.
  If they were done inside main() instead, workers would silently load the P1
  sample. _assert_seed() re-checks the loaded sample in each worker.
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import run_full_population as rfp                                   # noqa: E402

P4_SEED = 788156539
P4_WORK = os.path.join(ROOT, "zhou_san_run_p4")
os.makedirs(P4_WORK, exist_ok=True)

# ---- the only intended differences, applied at MODULE level ---------------
rfp.SEED = P4_SEED
rfp.WORK = P4_WORK
rfp.CELLML = os.path.join(P4_WORK, "fabbri_2017.cellml")
rfp.MMT = os.path.join(P4_WORK, "fabbri_2017.mmt")
rfp.SAMPLE = os.path.join(P4_WORK, "lhs_sample.npz")
rfp.RESULTS = os.path.join(P4_WORK, "results.jsonl")
rfp._TMP = os.path.join(P4_WORK, "tmp")
os.makedirs(rfp._TMP, exist_ok=True)
for _v in ("TMPDIR", "TEMP", "TMP"):
    os.environ[_v] = rfp._TMP

_orig_init = rfp._init


def _assert_seed():
    """Worker-side guard: refuse to run against the wrong sample."""
    import numpy as np
    z = np.load(rfp.SAMPLE, allow_pickle=True)
    if int(z["seed"]) != P4_SEED:
        raise SystemExit(f"FATAL: worker loaded sample with seed "
                         f"{int(z['seed'])}, expected {P4_SEED}")
    _orig_init()


rfp._init = _assert_seed


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def main():
    # seed the CellML from the verified P1 copy so the checksum gate can run
    src = os.path.join(ROOT, "zhou_san_run", "fabbri_2017.cellml")
    if not os.path.exists(rfp.CELLML) and os.path.exists(src):
        shutil.copyfile(src, rfp.CELLML)

    pre = {"P4_SEED": P4_SEED,
           "config_sha256": sha256(os.path.join(ROOT, "00_config",
                                                "config.yaml")),
           "cellml_sha256": sha256(rfp.CELLML),
           "seed_commitment_sha256": sha256(
               os.path.join(ROOT, "08_taskP", "P4_SEED_COMMITMENT.json")),
           "N_MODELS": rfp.N_MODELS,
           "scale_range": [rfp.SCALE_MIN, rfp.SCALE_MAX],
           "bcl_band_ms": [rfp.BCL_MIN, rfp.BCL_MAX],
           "duration_s": rfp.DURATION_S, "window_s": rfp.WINDOW_S,
           "tol_abs": rfp.TOL_ABS, "tol_rel": rfp.TOL_REL}
    print("=" * 70)
    print("P4 PRE-EXECUTION HASHES")
    print("=" * 70)
    for k, v in pre.items():
        print(f"  {k:24s} {v}")
    print("=" * 70)

    sys.argv = ["P4", "--workers", str(WORKERS), "--n", str(rfp.N_MODELS),
                "--resume"]
    rc = rfp.main()

    if os.path.exists(rfp.SAMPLE):
        pre["p4_lhs_sha256"] = sha256(rfp.SAMPLE)
    with open(os.path.join(ROOT, "08_taskP", "P4_hashes.json"), "w",
              encoding="utf-8") as f:
        json.dump(pre, f, indent=2)
    print(f"\n  P4 LHS sha256 : {pre.get('p4_lhs_sha256')}")
    return rc


WORKERS = int(os.environ.get("P4_WORKERS", "8"))

if __name__ == "__main__":
    sys.exit(main())
