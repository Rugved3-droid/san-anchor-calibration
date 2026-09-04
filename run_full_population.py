#!/usr/bin/env python3
"""
Self-contained reproduction of the Zhou et al. human sinoatrial node
population of models. Single file, no project imports.

    Zhou X, Bueno-Orovio A, Schilling RJ, Kirkby C, Denning C, Rajamohan D,
    Burrage K, Tinker A, Rodriguez B, Harmer SC (2019).
    Investigating the Complex Arrhythmic Phenotype Caused by the
    Gain-of-Function Mutation KCNQ1-G229D. Front Physiol 10:259.

    Baseline: Fabbri A, Fantini M, Wilders R, Severi S (2017).
    J Physiol 595:2365-2396. CellML from the Physiome Model Repository, e/568.

What it does
    1. Downloads and checksums the Fabbri 2017 CellML (or reuses a local copy).
    2. Imports it with Myokit. No equation is hand-translated.
    3. Validates the baseline against Fabbri Table 5 and STOPS if it fails.
    4. Latin hypercube sample, 5,000 models, +-100% on 12 mechanisms.
    5. Simulates 1,000 s per model, applies BCL 600-1,000 ms and positive
       overshoot, and freezes the retained parameter vectors.

Requirements
    pip install myokit numpy scipy pyyaml
    Myokit needs a C compiler and Sundials/CVODE. Check with:
        python -c "import myokit; print(myokit.system())"

    Ship 00_config/config.yaml alongside this script (same tree). Config is the
    single source of truth for the 12 mechanisms, the scaling convention, the
    solver settings and the retention criteria; nothing is duplicated here.

Usage
    python run_full_population.py                    # all 5,000, all cores
    python run_full_population.py --workers 8
    python run_full_population.py --n 200            # short trial run
    python run_full_population.py --resume           # continue after a stop

Checkpointing
    Results are appended to results.jsonl after every model. --resume skips
    indices already present, so an interrupted run continues where it stopped.
    A 5,000-model run takes roughly 5 h on 8 threads of an i5-10300H; plan for
    it to be interrupted at least once.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "zhou_san_run")
os.makedirs(WORK, exist_ok=True)

# Myokit compiles a C extension per Simulation into the system temp dir. If the
# system drive is short on space this surfaces as an opaque template error, so
# the temp dir is redirected next to this script BEFORE myokit is imported.
_TMP = os.path.join(WORK, "tmp")
os.makedirs(_TMP, exist_ok=True)
for _v in ("TMPDIR", "TEMP", "TMP"):
    os.environ[_v] = _TMP
import tempfile
tempfile.tempdir = _TMP

import numpy as np
import yaml

CONFIG = os.path.join(HERE, "00_config", "config.yaml")
if not os.path.exists(CONFIG):
    CONFIG = os.path.join(HERE, "config.yaml")
if not os.path.exists(CONFIG):
    raise SystemExit(
        "FATAL: config.yaml not found. Ship 00_config/config.yaml (or "
        "config.yaml) next to this script; it is the single source of truth "
        "for parameters, scaling and criteria.")

with open(CONFIG, encoding="utf-8") as _f:
    CFG = yaml.safe_load(_f)

CELLML_URL = ("https://models.physiomeproject.org/e/568/"
              "HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml")
CELLML_SHA = CFG["baseline_model"]["sha256"].lower()
CELLML = os.path.join(WORK, "fabbri_2017.cellml")
MMT = os.path.join(WORK, "fabbri_2017.mmt")
SAMPLE = os.path.join(WORK, "lhs_sample.npz")
RESULTS = os.path.join(WORK, "results.jsonl")

# Fabbri et al. 2017, Table 5, "Present model" column.
PUBLISHED = {"CL_ms": 814.0, "MDP_mV": -58.9, "OS_mV": 26.4,
             "DDR100_mV_s": 48.1, "dVdtmax_V_s": 7.4}
PUBLISHED["APA_mV"] = PUBLISHED["OS_mV"] - PUBLISHED["MDP_mV"]

# The 12 mechanisms come from config, never duplicated here.
PARAMS = [(p["zhou_symbol"], p["variable"], float(p["baseline"]))
          for p in CFG["parameters"]]

_s, _sim, _r = CFG["sampling"], CFG["simulation"], CFG["retention"]
N_MODELS = int(_s["n_models"])
SCALE_MIN, SCALE_MAX = float(_s["scale_min"]), float(_s["scale_max"])
SEED = int(_s["seed"])
DURATION_S = float(_sim["duration_s"])
WINDOW_S = float(_sim["measure_window_s"])
LOG_DT = float(_sim["log_dt_s"])
TOL_ABS, TOL_REL = float(_sim["tol_abs"]), float(_sim["tol_rel"])
BCL_MIN, BCL_MAX = float(_r["bcl_min_ms"]), float(_r["bcl_max_ms"])

# --------------------------------------------------------------------------
# biomarkers (Fabbri Table 5 definitions)
# --------------------------------------------------------------------------
DDR_WINDOW_S = 0.100


def find_peaks(t, v, min_peak_mv=-10.0, min_sep_s=0.150):
    peaks = []
    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] > min_peak_mv:
            if peaks and (t[i] - t[peaks[-1]]) < min_sep_s:
                if v[i] > v[peaks[-1]]:
                    peaks[-1] = i
                continue
            peaks.append(i)
    return np.array(peaks, dtype=int)


def biomarkers(t, v, require_beats=3):
    t = np.asarray(t, float)
    v = np.asarray(v, float)
    peaks = find_peaks(t, v)
    if len(peaks) < require_beats:
        return None
    cls, mdps, oss, ddrs, dvdts = [], [], [], [], []
    for k in range(len(peaks) - 1):
        i0, i1 = peaks[k], peaks[k + 1]
        seg = slice(i0, i1 + 1)
        j = i0 + int(np.argmin(v[seg]))
        mdp = v[j]
        t_end = t[j] + DDR_WINDOW_S
        if t_end <= t[i1]:
            ddrs.append((np.interp(t_end, t, v) - mdp) / DDR_WINDOW_S)
        up = slice(j, i1 + 1)
        if up.stop - up.start > 2:
            dvdts.append(np.max(np.diff(v[up]) / np.diff(t[up])) / 1000.0)
        cls.append((t[i1] - t[i0]) * 1000.0)
        mdps.append(mdp)
        oss.append(v[i1])
    if not cls:
        return None
    return {"n_beats": len(cls), "CL_ms": float(np.mean(cls)),
            "CL_ms_sd": float(np.std(cls)), "MDP_mV": float(np.mean(mdps)),
            "OS_mV": float(np.mean(oss)),
            "APA_mV": float(np.mean(oss) - np.mean(mdps)),
            "DDR100_mV_s": float(np.mean(ddrs)) if ddrs else float("nan"),
            "dVdtmax_V_s": float(np.mean(dvdts)) if dvdts else float("nan")}


# --------------------------------------------------------------------------
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def fetch_model():
    if not os.path.exists(CELLML):
        print(f"downloading {CELLML_URL}")
        req = urllib.request.Request(CELLML_URL,
                                     headers={"User-Agent": "zhou-san/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, \
                open(CELLML, "wb") as o:
            o.write(r.read())
    got = sha256(CELLML)
    print(f"cellml sha256: {got}")
    if got != CELLML_SHA:
        raise SystemExit(
            f"FATAL: CellML checksum mismatch.\n"
            f"  expected {CELLML_SHA}\n  found    {got}\n"
            f"The baseline validation does not transfer to a different model "
            f"file. Refusing to run. Delete {CELLML} to re-download, or update "
            f"baseline_model.sha256 in config.yaml deliberately.")
    import myokit
    import myokit.formats.cellml
    model = myokit.formats.importer("cellml").model(CELLML)
    model.validate()
    myokit.save_model(MMT, model)
    return model


def check_baseline():
    import myokit
    m = myokit.load_model(MMT)
    for q, want in (("Membrane.clamp_mode", 0),
                    ("Rate_modulation_experiments.ACh", 0),
                    ("Rate_modulation_experiments.Iso_1_uM", 0)):
        got = m.get(q).eval()
        print(f"  {q:44s} = {got:g}  (expected {want})")
        if got != want:
            print("  FAIL: model is not in control conditions.")
            return False, None
    s = myokit.Simulation(m)
    s.set_tolerance(TOL_ABS, TOL_REL)
    s.pre(500.0)
    d = s.run(WINDOW_S, log=["environment.time", "Membrane.V"],
              log_times=np.arange(0, WINDOW_S, LOG_DT))
    b = biomarkers(np.array(d["environment.time"]), np.array(d["Membrane.V"]))
    if b is None:
        print("  FAIL: baseline model does not pace.")
        return False, None
    print(f"\n  {'feature':13s}{'published':>11s}{'simulated':>11s}{'% diff':>9s}")
    ok = True
    for k in ["CL_ms", "MDP_mV", "OS_mV", "APA_mV", "DDR100_mV_s", "dVdtmax_V_s"]:
        pct = (b[k] - PUBLISHED[k]) / abs(PUBLISHED[k]) * 100
        print(f"  {k:13s}{PUBLISHED[k]:11.2f}{b[k]:11.2f}{pct:+8.1f}%")
        if k in ("CL_ms", "MDP_mV", "OS_mV", "APA_mV") and abs(pct) > 5:
            ok = False
    if abs((b["CL_ms"] - 814.0) / 814.0) > 0.02:
        ok = False
    print(f"  steady state: CL SD = {b['CL_ms_sd']:.4f} ms over "
          f"{b['n_beats']} beats")
    return ok, b


def make_sample():
    from scipy.stats import qmc
    base = np.array([p[2] for p in PARAMS], float)
    eng = qmc.LatinHypercube(d=len(PARAMS), seed=SEED)
    scales = qmc.scale(eng.random(n=N_MODELS), SCALE_MIN, SCALE_MAX)
    np.savez_compressed(SAMPLE, scales=scales, values=scales * base,
                        names=np.array([p[0] for p in PARAMS]),
                        variables=np.array([p[1] for p in PARAMS]),
                        baseline=base, seed=np.int64(SEED),
                        scale_min=np.float64(SCALE_MIN),
                        scale_max=np.float64(SCALE_MAX))
    print(f"  sample: {scales.shape}, scale in "
          f"[{scales.min():.3f}, {scales.max():.3f}], seed {SEED}")
    return scales


def validate_sample():
    """Refuse to reuse a cached sample that disagrees with config."""
    z = np.load(SAMPLE, allow_pickle=True)
    base = np.array([p[2] for p in PARAMS], float)
    bad = []
    if tuple(z["scales"].shape) != (N_MODELS, len(PARAMS)):
        bad.append(f"shape {tuple(z['scales'].shape)} != "
                   f"{(N_MODELS, len(PARAMS))}")
    if "seed" not in z.files:
        bad.append("sample does not record its seed")
    elif int(z["seed"]) != SEED:
        bad.append(f"seed {int(z['seed'])} != config {SEED}")
    if [str(x) for x in z["names"]] != [p[0] for p in PARAMS]:
        bad.append("parameter names differ from config")
    if [str(x) for x in z["variables"]] != [p[1] for p in PARAMS]:
        bad.append("model variables differ from config")
    if not np.allclose(z["baseline"], base, rtol=1e-9, atol=0):
        bad.append("baseline values differ from config")
    lo, hi = float(z["scales"].min()), float(z["scales"].max())
    if lo < SCALE_MIN - 1e-12 or hi > SCALE_MAX + 1e-12:
        bad.append(f"scale range [{lo:.6f}, {hi:.6f}] outside config "
                   f"[{SCALE_MIN}, {SCALE_MAX}]")
    if not np.allclose(z["values"], z["scales"] * z["baseline"],
                       rtol=1e-9, atol=0):
        bad.append("values != scales * baseline")
    if bad:
        raise SystemExit("FATAL: cached LHS sample disagrees with config:\n  - "
                         + "\n  - ".join(bad)
                         + f"\n  delete {SAMPLE} to regenerate.")
    print(f"  validated against config ({len(PARAMS)} parameters, seed {SEED})")


_S = {}


def _init():
    for v in ("TMPDIR", "TEMP", "TMP"):
        os.environ[v] = _TMP
    import tempfile as _tf
    _tf.tempdir = _TMP
    import myokit
    m = myokit.load_model(MMT)
    sim = myokit.Simulation(m)
    sim.set_tolerance(TOL_ABS, TOL_REL)
    z = np.load(SAMPLE, allow_pickle=True)
    # STATE ISOLATION: pre() advances BOTH the current state and the default
    # state, so a bare reset() would start each model from the PREVIOUS model's
    # steady state instead of the published Fabbri initial conditions. Capture
    # the pristine state once and restore it before every model.
    _S.update(sim=sim, pristine=list(sim.state()),
              variables=[str(x) for x in z["variables"]],
              values=z["values"])


def run_one(idx):
    sim = _S["sim"]
    t0 = time.time()
    rec = {"index": int(idx), "status": None, "CL_ms": None, "OS_mV": None,
           "MDP_mV": None, "APA_mV": None}
    try:
        sim.set_default_state(_S["pristine"])
        sim.set_state(_S["pristine"])
        sim.set_time(0)
        for var, val in zip(_S["variables"], _S["values"][idx]):
            sim.set_constant(var, float(val))
        sim.pre(DURATION_S - WINDOW_S)
        d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, WINDOW_S, LOG_DT))
        b = biomarkers(np.array(d["environment.time"]),
                       np.array(d["Membrane.V"]))
        if b is None:
            rec["status"] = "no_pacing"
        else:
            rec.update(status="ok", CL_ms=b["CL_ms"], OS_mV=b["OS_mV"],
                       MDP_mV=b["MDP_mV"], APA_mV=b["APA_mV"])
    except Exception as e:
        rec["status"] = "solver_failure"
        rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    rec["seconds"] = time.time() - t0
    return rec


def load_done():
    done = {}
    if os.path.exists(RESULTS):
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        done[r["index"]] = r
                    except json.JSONDecodeError:
                        pass          # tolerate a torn final line
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_MODELS)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--skip-baseline", action="store_true")
    args = ap.parse_args()

    print("=" * 70)
    print("Zhou et al. human SAN population of models - reproduction")
    print("=" * 70)
    print(f"host: {platform.platform()} | {os.cpu_count()} logical CPUs")
    print(f"work dir: {WORK}\n")

    print("[1/4] model")
    fetch_model()

    if not args.skip_baseline:
        print("\n[2/4] baseline validation vs Fabbri 2017 Table 5")
        ok, _ = check_baseline()
        if not ok:
            print("\nBASELINE FAILED - stopping. Downstream results would be "
                  "meaningless.")
            return 1
        print("  BASELINE PASS")
    else:
        print("\n[2/4] baseline validation SKIPPED (--skip-baseline)")

    print("\n[3/4] Latin hypercube sample")
    if not os.path.exists(SAMPLE):
        make_sample()
    else:
        print(f"  reusing {SAMPLE}")
    validate_sample()

    done = load_done() if args.resume else {}
    todo = [i for i in range(args.n) if i not in done]
    if args.resume:
        print(f"\n  resuming: {len(done)} done, {len(todo)} remaining")
    if not todo:
        print("  nothing to do")
    else:
        print(f"\n[4/4] simulating {len(todo)} models on {args.workers} workers")
        print(f"  {DURATION_S:.0f} s per model; expect roughly "
              f"{len(todo)*26/args.workers/3600:.1f} h")
        t0 = time.time()
        with open(RESULTS, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_init) as pool:
                for k, r in enumerate(pool.imap_unordered(run_one, todo,
                                                          chunksize=1), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    done[r["index"]] = r
                    if k % 25 == 0 or k == len(todo):
                        el = time.time() - t0
                        eta = el / k * (len(todo) - k)
                        print(f"    {k}/{len(todo)}  elapsed {el/60:6.1f} min  "
                              f"ETA {eta/60:6.1f} min", flush=True)

    # ---- retention -------------------------------------------------------
    recs = [done[i] for i in sorted(done) if i < args.n]
    n = len(recs)
    kept = [r for r in recs if r["status"] == "ok"
            and BCL_MIN <= r["CL_ms"] <= BCL_MAX and r["OS_mV"] > 0]
    n_nop = sum(1 for r in recs if r["status"] == "no_pacing")
    n_bad = sum(1 for r in recs if r["status"] == "solver_failure")

    print("\n" + "=" * 70)
    print(f"  simulated       : {n}")
    print(f"  no pacing       : {n_nop} ({n_nop/n*100:.1f}%)")
    print(f"  solver failures : {n_bad} ({n_bad/n*100:.1f}%)")
    print(f"  RETAINED        : {len(kept)} / {n} = {len(kept)/n*100:.2f}%")
    print(f"  Zhou reference  : 1046 / 5000 = 20.92%")
    print("=" * 70)

    z = np.load(SAMPLE, allow_pickle=True)
    ki = np.array([r["index"] for r in kept], int)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = os.path.join(WORK, f"population_retained_{stamp}.npz")
    np.savez_compressed(out, model_index=ki, scales=z["scales"][ki],
                        values=z["values"][ki], names=z["names"],
                        variables=z["variables"], baseline=z["baseline"],
                        CL_ms=np.array([r["CL_ms"] for r in kept]),
                        OS_mV=np.array([r["OS_mV"] for r in kept]),
                        MDP_mV=np.array([r["MDP_mV"] for r in kept]),
                        APA_mV=np.array([r["APA_mV"] for r in kept]))
    digest = sha256(out)
    with open(os.path.join(WORK, f"population_manifest_{stamp}.json"), "w",
              encoding="utf-8") as f:
        json.dump({"frozen_utc": datetime.now(timezone.utc).isoformat(),
                   "n_simulated": n, "n_retained": len(kept),
                   "retention_fraction": len(kept) / n,
                   "reference": "Zhou et al. 2019: 1046/5000 = 0.2092",
                   "criteria": {"bcl_ms": [BCL_MIN, BCL_MAX],
                                "overshoot_positive": True,
                                "duration_s": DURATION_S},
                   "seed": SEED, "scale_range": [SCALE_MIN, SCALE_MAX],
                   "parameters": [{"zhou_symbol": a, "variable": b,
                                   "baseline": c} for a, b, c in PARAMS],
                   "cellml_sha256": sha256(CELLML),
                   "population_file": os.path.basename(out),
                   "population_sha256": digest}, f, indent=2)
    print(f"\n  frozen -> {out}")
    print(f"  sha256 : {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
