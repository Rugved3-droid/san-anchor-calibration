"""Task E-prime - interaction invariance sweep.

Question: does the super/sub-additive CLASSIFICATION of a drug pair depend on the
block-fraction calibration we cannot pin down? Magnitude is not the endpoint;
invariance is.

Method
------
Block fraction per drug from the SIM-0 table via Hill:
    b(m) = (m*r)^n / (1 + (m*r)^n),   r = free_Cmax / IC50
`m` is a multiplier on effective exposure/potency, swept over a log2 grid. This
formulation keeps b in [0,1) at every multiplier, which naive scaling of b does
not. At m = 1 it reproduces the in vitro-derived block in the SIM-0 sheet
exactly (diltiazem 52.3%, ivabradine 1.66%).

Marked points:
  m = 1.0    in vitro-derived (Crumb IC50 at free Cmax)
  m = 0.077  clinically calibrated diltiazem (15.11% block, Task D)

Endpoints, across the 188 retained models:
  P   = fraction of models in which automaticity FAILS (quiescent)
  dHR = median rate change among models pacing in all of A, B, AB
Bliss independence:
  P_AB_expected  = P_A + P_B - P_A*P_B
  E_AB_expected  = E_A + E_B - E_A*E_B      (E = fractional rate reduction)

Same-target pairs (I_CaL x I_CaL) combine as independent binding on one channel,
b_comb = 1 - (1-b_A)(1-b_B), so the population response is read from the existing
Task A I_CaL ladder. Note this is independence at the TARGET; the endpoint is a
nonlinear function of total block, so Bliss on the ENDPOINT can still be violated
- which is exactly what is being tested.

Cross-target pairs (I_CaL x I_f) require new joint simulations.

SCOPE LIMIT: primary SAN mechanism only. Verapamil's I_Kr and mexiletine's I_Na
components are not applied - no I_Kr/I_Na population ladders exist. Stated, not
silently dropped.
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

DRUGS = {
    "diltiazem":  {"target": "G_CaL", "ic50": 112.2,  "hill": 0.71, "cmax": 127.5},
    "verapamil":  {"target": "G_CaL", "ic50": 198.7,  "hill": 1.09, "cmax": 45.0},
    "mexiletine": {"target": "G_CaL", "ic50": 38281., "hill": 1.00, "cmax": 2503.2},
    "ivabradine": {"target": "G_f",   "ic50": 2000.,  "hill": 0.80, "cmax": 12.2},
}
PAIRS = [("diltiazem", "verapamil"), ("verapamil", "mexiletine"),
         ("diltiazem", "ivabradine"), ("verapamil", "ivabradine")]
MULTIPLIERS = [0.0625, 0.077, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0]

PREPACE_S = 300.0
WINDOW_S = 6.0
LOG_DT = 1e-4


def block(drug, m):
    d = DRUGS[drug]
    x = (m * d["cmax"] / d["ic50"]) ** d["hill"]
    return x / (1.0 + x)


# ---------------------------------------------------------------- simulation
_S = {}


def _init(prepace):
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
              values=z["values"], idx=idx, prepace=prepace)


def _job(args):
    """One model under a joint (I_CaL block, I_f block)."""
    model_idx, b_cal, b_f = args
    S = _S
    sim = S["sim"]
    try:
        reset_pristine(sim, S["pristine"])
        vals = list(S["values"][model_idx])
        vals[S["idx"]["G_CaL"]] *= (1.0 - b_cal)
        vals[S["idx"]["G_f"]] *= (1.0 - b_f)
        for var, val in zip(S["variables"], vals):
            sim.set_constant(var, float(val))
        sim.pre(S["prepace"])
        d = sim.run(WINDOW_S, log=["environment.time", "Membrane.V"],
                    log_times=np.arange(0, WINDOW_S, LOG_DT))
        bm = S["bm"](np.array(d["environment.time"]), np.array(d["Membrane.V"]))
    except Exception:
        bm = None
    return {"model": int(model_idx), "b_cal": b_cal, "b_f": b_f,
            "bpm": (60000.0 / bm["CL_ms"]) if bm else None}


# ---------------------------------------------------------------- ladders
def ladder_lookup(lad, model_idx_map, model, b):
    """Population response at arbitrary block, interpolated on the 5% grid."""
    rec = model_idx_map[model]
    grid = sorted(float(k) for k in rec["levels"])
    if b <= grid[0]:
        lo = hi = grid[0]
    elif b >= grid[-1]:
        lo = hi = grid[-1]
    else:
        lo = max(g for g in grid if g <= b)
        hi = min(g for g in grid if g >= b)
    a, c = rec["levels"].get(str(lo)), rec["levels"].get(str(hi))
    if a is None or c is None:
        return None
    f = 0.0 if hi == lo else (b - lo) / (hi - lo)
    return a["bpm"] + f * (c["bpm"] - a["bpm"])


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    with open(LAD_CAL, encoding="utf-8") as f:
        cal = json.load(f)
    with open(LAD_F, encoding="utf-8") as f:
        lf = json.load(f)
    cal_map = {r["index"]: r for r in cal["records"]}
    f_map = {r["index"]: r for r in lf["records"]}
    models = sorted(set(cal_map) & set(f_map))
    base_bpm = {m: cal_map[m]["levels"]["0.0"]["bpm"] for m in models}
    print(f"population: {len(models)} retained models")

    # ---- which joint sims are needed -----------------------------------
    need = []
    for a, b in PAIRS:
        if DRUGS[a]["target"] == DRUGS[b]["target"]:
            continue
        for m in MULTIPLIERS:
            ba = block(a, m)
            bb = block(b, m)
            b_cal = ba if DRUGS[a]["target"] == "G_CaL" else bb
            b_f = bb if DRUGS[b]["target"] == "G_f" else ba
            need.append((round(b_cal, 6), round(b_f, 6)))
    need = sorted(set(need))
    print(f"joint (I_CaL, I_f) points required: {len(need)}  "
          f"-> {len(need) * len(models)} simulations")

    ck = os.path.join(OUT_DIR, "taskE_joint_checkpoint.jsonl")
    done = {}
    if os.path.exists(ck):
        with open(ck, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        done[(r["model"], r["b_cal"], r["b_f"])] = r["bpm"]
                    except json.JSONDecodeError:
                        pass
    todo = [(mi, bc, bf) for (bc, bf) in need for mi in models
            if (mi, bc, bf) not in done]
    print(f"checkpoint: {len(done)} done, {len(todo)} to run", flush=True)

    if todo:
        t0 = time.time()
        with open(ck, "a", encoding="utf-8") as fh:
            with Pool(args.workers, initializer=_init,
                      initargs=(PREPACE_S,)) as pool:
                for k, r in enumerate(pool.imap_unordered(_job, todo,
                                                          chunksize=4), 1):
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    done[(r["model"], r["b_cal"], r["b_f"])] = r["bpm"]
                    if k % 200 == 0 or k == len(todo):
                        el = time.time() - t0
                        print(f"  {k}/{len(todo)}  {el/60:.1f} min  "
                              f"ETA {el/k*(len(todo)-k)/60:.1f} min", flush=True)

    # ---- analysis -------------------------------------------------------
    results = []
    for a, b in PAIRS:
        same = DRUGS[a]["target"] == DRUGS[b]["target"]
        print(f"\n{'='*78}\n{a} x {b}  "
              f"({DRUGS[a]['target']} x {DRUGS[b]['target']}"
              f"{', same target' if same else ''})\n{'='*78}")
        print(f"{'mult':>7s} {'bA':>7s} {'bB':>7s} | "
              f"{'P_A':>6s} {'P_B':>6s} {'P_exp':>6s} {'P_obs':>6s} "
              f"{'95% CI':>15s} | {'class (failure)':>16s} | "
              f"{'dHR class':>12s}")
        rows = []
        for m in MULTIPLIERS:
            ba, bb = block(a, m), block(b, m)

            def resp(drug, bl, model):
                if DRUGS[drug]["target"] == "G_CaL":
                    return ladder_lookup(cal, cal_map, model, bl)
                return ladder_lookup(lf, f_map, model, bl)

            rA, rB, rAB = {}, {}, {}
            for mi in models:
                rA[mi] = resp(a, ba, mi)
                rB[mi] = resp(b, bb, mi)
                if same:
                    rAB[mi] = ladder_lookup(cal, cal_map, mi,
                                            1 - (1 - ba) * (1 - bb))
                else:
                    bc = ba if DRUGS[a]["target"] == "G_CaL" else bb
                    bf = bb if DRUGS[b]["target"] == "G_f" else ba
                    rAB[mi] = done.get((mi, round(bc, 6), round(bf, 6)))

            n = len(models)
            PA = sum(1 for mi in models if rA[mi] is None) / n
            PB = sum(1 for mi in models if rB[mi] is None) / n
            kAB = sum(1 for mi in models if rAB[mi] is None)
            PAB = kAB / n
            Pexp = PA + PB - PA * PB
            lo, hi = wilson(kAB, n)
            # Rows with no failures anywhere carry no information about
            # interaction: comparing Pexp=0 against a Wilson bound that is 0 to
            # within floating-point noise would classify spuriously. Likewise
            # rows where both arms are already near-total failure are
            # ceiling-limited and cannot show super-additivity.
            EPS = 1e-9
            if kAB == 0 and PA < EPS and PB < EPS:
                cls_p = "no events"
            elif Pexp > 0.95 or PAB > 0.95:
                cls_p = "ceiling"
            elif Pexp < lo - EPS:
                cls_p = "SUPER-ADDITIVE"
            elif Pexp > hi + EPS:
                cls_p = "SUB-ADDITIVE"
            else:
                cls_p = "additive"

            # dHR on the subset pacing in all three conditions
            surv = [mi for mi in models
                    if rA[mi] and rB[mi] and rAB[mi]]
            if surv:
                EA = np.median([(base_bpm[mi] - rA[mi]) / base_bpm[mi] for mi in surv])
                EB = np.median([(base_bpm[mi] - rB[mi]) / base_bpm[mi] for mi in surv])
                EAB = np.median([(base_bpm[mi] - rAB[mi]) / base_bpm[mi] for mi in surv])
                Eexp = EA + EB - EA * EB
                ratio = EAB / Eexp if Eexp > 1e-9 else float("nan")
                cls_e = ("SUPER" if ratio > 1.05 else
                         "SUB" if ratio < 0.95 else "additive")
            else:
                EA = EB = EAB = Eexp = ratio = float("nan")
                cls_e = "n/a"

            mark = ""
            if abs(m - 1.0) < 1e-9:
                mark = "  <- in vitro"
            elif abs(m - 0.077) < 1e-9:
                mark = "  <- clin. dilt"
            print(f"{m:7.4f} {ba:7.3f} {bb:7.3f} | "
                  f"{PA:6.3f} {PB:6.3f} {Pexp:6.3f} {PAB:6.3f} "
                  f"[{lo:5.3f},{hi:5.3f}] | {cls_p:>16s} | "
                  f"{cls_e:>7s} {ratio:5.2f}{mark}")
            rows.append({"multiplier": m, "b_A": ba, "b_B": bb,
                         "P_A": PA, "P_B": PB, "P_expected": Pexp,
                         "P_observed": PAB, "P_ci": [lo, hi],
                         "class_failure": cls_p,
                         "E_A": EA, "E_B": EB, "E_expected": Eexp,
                         "E_observed": EAB, "E_ratio": ratio,
                         "class_dHR": cls_e, "n_survivors": len(surv)})
        UNINF = {"no events", "ceiling", "n/a"}
        cls_set = {r["class_failure"] for r in rows}
        inf_set = cls_set - UNINF
        cls_e_set = {r["class_dHR"] for r in rows if r["class_dHR"] not in UNINF}
        n_inf = sum(1 for r in rows if r["class_failure"] not in UNINF)
        print(f"\n  all rows                : {sorted(cls_set)}")
        print(f"  informative rows ({n_inf}/{len(rows)}): {sorted(inf_set)}")
        print(f"  dHR classification      : {sorted(cls_e_set)}")
        print(f"  INVARIANT over informative rows: {len(inf_set) == 1}")
        results.append({"pair": [a, b], "same_target": same, "rows": rows,
                        "classes_failure_all": sorted(cls_set),
                        "classes_failure_informative": sorted(inf_set),
                        "n_informative_rows": n_inf,
                        "classes_dHR": sorted(cls_e_set),
                        "invariant_failure": len(inf_set) == 1,
                        "invariant_dHR": len(cls_e_set) == 1})

    with open(os.path.join(OUT_DIR, "taskE_interaction_invariance.json"),
              "w", encoding="utf-8") as f:
        json.dump({"multipliers": MULTIPLIERS, "drugs": DRUGS,
                   "n_models": len(models), "results": results}, f, indent=2)
    print(f"\n-> {os.path.join(OUT_DIR, 'taskE_interaction_invariance.json')}")


if __name__ == "__main__":
    main()
