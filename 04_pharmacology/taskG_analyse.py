"""Task G3 analysis - verapamil x ivabradine, EXCESS ABSOLUTE RISK.

Reads only taskG_pair_checkpoint.jsonl. Computes nothing that feeds back into a
parameter (see study_integrity.no_pair_feedback in 00_config/config.yaml).

Endpoint definitions
--------------------
P_A, P_B, P_AB   population fraction losing automaticity under verapamil alone,
                 ivabradine alone, and the pair.

EAR_paired  (PRIMARY, the Task F definition)
    fraction of models that PACE under A alone AND PACE under B alone but FAIL
    under A+B. This is per-model and paired, so it is the literal
    "fails on the combination at exposures where neither drug alone does it".

EAR_marginal
    P_AB - max(P_A, P_B). The conventional marginal contrast, reported so the
    two definitions can be compared.

RESCUE
    fraction failing under a single but pacing under the pair. Reported for
    honesty; a non-zero value means the endpoint is not monotone.

Bliss (SECONDARY, ARTIFACT DEMONSTRATION ONLY)
    P_exp = P_A + P_B - P_A*P_B. Task E established that ANY endpoint defined as
    "fraction crossing a steep threshold" manufactures super-additivity from
    additive target occupancy. It is reported to demonstrate that artifact, not
    to make a pharmacological claim.

DENOMINATOR
    The endpoint is drug-INDUCED loss of automaticity, so the denominator is the
    models that pace DRUG-FREE in that state. At control all 188 do. At Iso 1 uM
    20/188 do not pace even drug-free - a property of the Iso state, not of any
    drug - and those 20 are excluded from the Iso analysis. Excluding them is
    reported explicitly rather than silently.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

B_IVAB = 0.312          # 36-month transplant anchor  (fixed input)
B_IVAB_10YR = 0.509     # 10-year anchor              (sensitivity only)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# --------------------------------------------------------------------- load
res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    res[(r["state"], round(r["b_cal"], 6), round(r["b_f"], 6))] = \
        res.get((r["state"], round(r["b_cal"], 6), round(r["b_f"], 6)), {})
    res[(r["state"], round(r["b_cal"], 6), round(r["b_f"], 6))][r["model"]] = r["bpm"]

VER_GRID = sorted({k[1] for k in res})
report = {"B_ivabradine": B_IVAB, "states": {}}


def _complete(key, models):
    """Every model must have a checkpoint entry for the rung to be usable.

    'Absent from the checkpoint' means not yet simulated; 'present with
    bpm = None' means simulated and quiescent. Conflating them would invent
    failures in a rung that a background run is still writing.
    """
    d = res.get(key)
    return d is not None and all(m in d for m in models)

for state in ("control", "iso"):
    free = res[(state, 0.0, 0.0)]
    pop = sorted(m for m, v in free.items() if v is not None)
    n = len(pop)
    excl = len(free) - n
    base = {m: free[m] for m in pop}

    print("\n" + "=" * 92)
    print(f"STATE = {state.upper()}"
          + ("   (Fabbri ACh=0, Iso=0; the true no-autonomic-input state)"
             if state == "control" else
             "   (Fabbri Iso 1 uM; matches the anchor RATE, not its mechanism)"))
    print("=" * 92)
    print(f"drug-free pacing population: {n}/188"
          + (f"   ({excl} excluded: quiescent drug-free at this state)"
             if excl else ""))
    print(f"drug-free median rate: {np.median(list(base.values())):.2f} bpm")

    def fails(key):
        d = res[key]
        return {m for m in pop if d.get(m) is None}

    st = {"n": n, "n_excluded_drugfree": excl,
          "median_bpm_drugfree": float(np.median(list(base.values()))),
          "rows": []}

    for b_ivab, tag in ((B_IVAB, "36-month anchor"),
                        (B_IVAB_10YR, "10-year (sensitivity)")):
        avail = [b for b in VER_GRID
                 if _complete((state, b, b_ivab), pop)
                 and _complete((state, b, 0.0), pop)]
        if not avail:
            continue
        print(f"\n  ivabradine I_f block = {b_ivab:.1%}   [{tag}]")
        print(f"  {'verap':>6s} {'P_A':>7s} {'P_B':>7s} {'P_AB':>7s} "
              f"{'95% CI':>16s} | {'EAR_paired':>11s} {'95% CI':>16s} "
              f"{'EAR_marg':>9s} {'rescue':>7s} | {'Bliss':>7s} {'class':>16s}")
        B_only = fails((state, 0.0, b_ivab))
        PB = len(B_only) / n
        for b_cal in avail:
            A_only = fails((state, b_cal, 0.0))
            AB = fails((state, b_cal, b_ivab))
            PA, PAB = len(A_only) / n, len(AB) / n

            surv_both = {m for m in pop if m not in A_only and m not in B_only}
            k_ear = len(AB & surv_both)
            ear_p = k_ear / n
            lo_e, hi_e = wilson(k_ear, n)
            ear_m = PAB - max(PA, PB)
            resc = len((A_only | B_only) - AB) / n

            Pexp = PA + PB - PA * PB
            lo, hi = wilson(len(AB), n)
            EPS = 1e-9
            if len(AB) == 0 and PA < EPS and PB < EPS:
                cls = "no events"
            elif Pexp > 0.95 or PAB > 0.95:
                cls = "ceiling"
            elif Pexp < lo - EPS:
                cls = "SUPER-ADDITIVE"
            elif Pexp > hi + EPS:
                cls = "SUB-ADDITIVE"
            else:
                cls = "additive"

            print(f"  {b_cal:6.0%} {PA:7.3f} {PB:7.3f} {PAB:7.3f} "
                  f"[{lo:5.3f},{hi:5.3f}] | {ear_p:11.3f} "
                  f"[{lo_e:5.3f},{hi_e:5.3f}] {ear_m:+9.3f} {resc:7.3f} | "
                  f"{Pexp:7.3f} {cls:>16s}")

            surv = [m for m in pop if res[(state, b_cal, b_ivab)].get(m)]
            dhr = ([res[(state, b_cal, b_ivab)][m] - base[m] for m in surv]
                   if surv else [])
            st["rows"].append({
                "b_ivabradine": b_ivab, "b_verapamil": b_cal,
                "P_A_verapamil_alone": PA, "P_B_ivabradine_alone": PB,
                "P_AB_pair": PAB, "P_AB_ci": [lo, hi],
                "EAR_paired": ear_p, "EAR_paired_k": k_ear,
                "EAR_paired_ci": [lo_e, hi_e],
                "EAR_marginal": ear_m, "rescue_fraction": resc,
                "bliss_expected": Pexp, "bliss_class": cls,
                "n_survivors_pair": len(surv),
                "median_dHR_pair": float(np.median(dhr)) if dhr else None})
    report["states"][state] = st

with open(os.path.join(OUT, "taskG_pair_prediction.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskG_pair_prediction.json')}")
