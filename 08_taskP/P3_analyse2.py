"""P3 part 2: band maxima + 5/10% status, 240-vs-480, PK/PD decomposition,
external SmPC comparison, and Bliss classification at the primary anchor.

All definitions frozen (see P3_analyse.py header).
"""
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "08_taskP", "p3")
CKPT = os.path.join(DEST, "P3_dense_checkpoint.jsonl")
CORE = json.load(open(os.path.join(DEST, "P3_results_core.json"),
                      encoding="utf-8"))

ANCHORS = [("Doesch 2007 (PRIMARY)", {"1x": 0.5840, "2x": 0.7097, "3x": 0.7717}),
           ("10-year cohort", {"1x": 0.5090, "2x": 0.6435, "3x": 0.7140}),
           ("36-month (superseded)", {"1x": 0.3120, "2x": 0.4412, "3x": 0.5220})]
CMP_240 = {"time-average (PRIMARY)": 0.029, "Cmax (sensitivity)": 0.14}
SMPC_OBSERVED_BPM = -5.0
IC50_V, HILL_V, MW_V, FU_V = 198.7, 1.09, 454.6, 0.104
B_PRIMARY = 0.5840
EPS = 1e-9
BLISS_RUNGS = [0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25, 0.275,
               0.30, 0.40]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def total_ng(block):
    if block <= 0:
        return 0.0
    free = IC50_V * (block / (1.0 - block)) ** (1.0 / HILL_V)
    return free / FU_V * MW_V / 1000.0


bpm = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    bpm[(r["model"], r["state"], round(r["b_cal"], 6),
         round(r["b_f"], 6))] = r["bpm"]
models = sorted({k[0] for k in bpm})
pops = {st: [m for m in models if bpm.get((m, st, 0.0, 0.0)) is not None]
        for st in ("control", "iso")}
out = {}


def paces(m, st, bc, bf):
    return bpm.get((m, st, round(bc, 6), round(bf, 6))) is not None


# ============ 1. BAND MAXIMA + 5/10% STATUS ==============================
print("=" * 118)
print("BAND MAXIMA and INTERVAL-SUPPORTED 5% / 10% STATUS")
print("  point = point estimate exceeds threshold")
print("  CI    = LOWER 95% bound exceeds it (interval-supported)")
print("=" * 118)
print(f"{'anchor':22s} {'arm':3s} {'state':7s} {'band':11s} {'maxEMQF':>8s} "
      f"{'rung':>6s} {'k/n':>9s} {'95% CI':>16s} {'o/ceil':>7s} | "
      f"{'>5pt':>5s} {'>5CI':>5s} {'>10pt':>6s} {'>10CI':>6s}")
out["band_maxima"] = []
for aname, arms in ANCHORS:
    for arm in ("1x", "2x", "3x"):
        for st in ("control", "iso"):
            for band in ("240 mg/day", "480 mg/day"):
                rows = [r for r in CORE["rows"]
                        if r["anchor"] == aname and r["arm"] == arm
                        and r["state"] == st and band in r["bands"]]
                if not rows:
                    continue
                b = max(rows, key=lambda r: r["EMQF"])
                rec = {"anchor": aname, "arm": arm, "state": st, "band": band,
                       "max_EMQF": b["EMQF"], "at_rung": b["b_cal"],
                       "EMQF_k": b["EMQF_k"], "n": b["n"],
                       "EMQF_ci95": b["EMQF_ci95"],
                       "eligible_frac": b["eligible_frac"],
                       "obs_over_max": b["obs_over_max"],
                       "point_gt_5pct": b["point_gt_5pct"],
                       "ci_lower_gt_5pct": b["ci_lower_gt_5pct"],
                       "point_gt_10pct": b["point_gt_10pct"],
                       "ci_lower_gt_10pct": b["ci_lower_gt_10pct"]}
                out["band_maxima"].append(rec)
                print(f"{aname:22s} {arm:3s} {st:7s} {band:11s} "
                      f"{b['EMQF']:8.2%} {b['b_cal']:6.3f} "
                      f"{b['EMQF_k']:4d}/{b['n']:4d} "
                      f"[{b['EMQF_ci95'][0]:6.2%},{b['EMQF_ci95'][1]:6.2%}] "
                      f"{b['obs_over_max'] or 0:7.3f} | "
                      f"{'YES' if b['point_gt_5pct'] else 'no':>5s} "
                      f"{'YES' if b['ci_lower_gt_5pct'] else 'no':>5s} "
                      f"{'YES' if b['point_gt_10pct'] else 'no':>6s} "
                      f"{'YES' if b['ci_lower_gt_10pct'] else 'no':>6s}")

n10 = [r for r in out["band_maxima"] if r["ci_lower_gt_10pct"]]
n10all = [r for r in CORE["rows"] if r["ci_lower_gt_10pct"]]
n5 = [r for r in out["band_maxima"] if r["ci_lower_gt_5pct"]]
print()
print(f"  band maxima with INTERVAL-SUPPORTED >10%: {len(n10)} of "
      f"{len(out['band_maxima'])}")
print(f"  ANY of the {len(CORE['rows'])} conditions with lower bound > 10%: "
      f"{len(n10all)}")
for r in n10all:
    print(f"    {r['anchor']} {r['arm']} {r['state']} rung {r['b_cal']}: "
          f"{r['EMQF']:.2%} CI [{r['EMQF_ci95'][0]:.2%},"
          f"{r['EMQF_ci95'][1]:.2%}]")
print(f"  band maxima with INTERVAL-SUPPORTED >5%: {len(n5)} of "
      f"{len(out['band_maxima'])}")
out["summary_5_10"] = {
    "n_band_maxima": len(out["band_maxima"]),
    "n_band_maxima_ci_gt_10": len(n10),
    "n_band_maxima_ci_gt_5": len(n5),
    "n_conditions_total": len(CORE["rows"]),
    "n_conditions_ci_gt_10": len(n10all)}

# ============ 2. 240 vs 480 =============================================
print()
print("=" * 100)
print("240 vs 480 mg/day - all PK arms, both states (band maxima)")
print("=" * 100)
print(f"{'anchor':22s} {'arm':3s} {'state':7s} {'240 max':>9s} {'480 max':>9s} "
      f"{'diff pp':>8s} {'ratio':>6s}")
out["band_comparison"] = []
for aname, _ in ANCHORS:
    for arm in ("1x", "2x", "3x"):
        for st in ("control", "iso"):
            g = {r["band"]: r for r in out["band_maxima"]
                 if r["anchor"] == aname and r["arm"] == arm
                 and r["state"] == st}
            if len(g) != 2:
                continue
            a, b = g["240 mg/day"], g["480 mg/day"]
            rec = {"anchor": aname, "arm": arm, "state": st,
                   "max_240": a["max_EMQF"], "max_480": b["max_EMQF"],
                   "diff_pp": (b["max_EMQF"] - a["max_EMQF"]) * 100,
                   "ratio": (b["max_EMQF"] / a["max_EMQF"]
                             if a["max_EMQF"] > 0 else None)}
            out["band_comparison"].append(rec)
            print(f"{aname:22s} {arm:3s} {st:7s} {a['max_EMQF']:9.2%} "
                  f"{b['max_EMQF']:9.2%} {rec['diff_pp']:+8.2f} "
                  f"{rec['ratio'] if rec['ratio'] else float('nan'):6.2f}")

# ============ 3. PK/PD DECOMPOSITION (bpm) ==============================
print()
print("=" * 108)
print("PK/PD DECOMPOSITION (bpm, vs ivabradine alone at 1x) at the 2.9% and "
      "30.0% rungs")
print("=" * 108)
out["decomposition"] = []
for st in ("control", "iso"):
    pop = pops[st]
    base = {m: bpm[(m, st, 0.0, 0.0)] for m in pop}
    print(f"\nSTATE = {st.upper()}  (n = {len(pop)})")
    print(f"  {'anchor':22s} {'rung':>7s} {'ng/mL':>7s} {'n':>4s} | "
          f"{'PK only':>9s} {'PD only':>9s} {'PK+PD 2x':>9s} {'PK+PD 3x':>9s} "
          f"| {'larger':>6s}")
    for aname, a in ANCHORS:
        for bc in (0.029, 0.30):
            need = [(0.0, a["1x"]), (0.0, a["2x"]), (0.0, a["3x"]),
                    (bc, a["1x"]), (bc, a["2x"]), (bc, a["3x"])]
            cohort = [m for m in pop
                      if all(bpm.get((m, st, round(x, 6), round(y, 6)))
                             is not None for x, y in need)]
            if not cohort:
                continue

            def med(x, y, _c=None):
                cc = _c if _c is not None else cohort
                return float(np.median(
                    [bpm[(m, st, round(x, 6), round(y, 6))] - base[m]
                     for m in cc]))

            ref = med(0.0, a["1x"])
            pk = med(0.0, a["2x"]) - ref
            pd = med(bc, a["1x"]) - ref
            rec = {"state": st, "anchor": aname, "block": bc,
                   "total_ng_per_mL": total_ng(bc),
                   "n_cohort": len(cohort), "dHR_ref_ivab_1x": ref,
                   "PK_only": pk, "PD_only": pd,
                   "PK_plus_PD_2x": med(bc, a["2x"]) - ref,
                   "PK_plus_PD_3x": med(bc, a["3x"]) - ref,
                   "larger": "PK" if abs(pk) > abs(pd) else "PD"}
            out["decomposition"].append(rec)
            print(f"  {aname:22s} {bc:7.1%} {rec['total_ng_per_mL']:7.1f} "
                  f"{len(cohort):4d} | {pk:+9.2f} {pd:+9.2f} "
                  f"{rec['PK_plus_PD_2x']:+9.2f} {rec['PK_plus_PD_3x']:+9.2f} "
                  f"| {rec['larger']:>6s}")
    for aname, _ in ANCHORS:
        rr = [r for r in out["decomposition"]
              if r["state"] == st and r["anchor"] == aname]
        if len(rr) == 2:
            swap = rr[0]["larger"] != rr[1]["larger"]
            print(f"    {aname:22s} rank swap 2.9% -> 30.0%: "
                  f"{'YES' if swap else 'NO'} "
                  f"({rr[0]['larger']} -> {rr[1]['larger']})")

# ============ 4. EXTERNAL SmPC COMPARISON ===============================
print()
print("=" * 104)
print("EXTERNAL COMPARISON vs SmPC -5 bpm  (240 mg/day; matching contrast = "
      "PK+PD 2x)")
print("=" * 104)
print("  PRIMARY point = time-average free concentration = 2.9% block "
      "(config comparison_point).")
print("  Cmax (14.0% block) is a LABELLED SENSITIVITY, never promoted to "
      "primary.")
print("  Trough: no 24-h trough is published for 240 mg/day; the true trough "
      "lies BELOW the")
print("  time-average, so the 2.9% point is an UPPER bound on a trough-based "
      "comparison.")
print()
out["external"] = []
for st in ("control", "iso"):
    pop = pops[st]
    base = {m: bpm[(m, st, 0.0, 0.0)] for m in pop}
    print(f"  STATE = {st.upper()}")
    print(f"  {'anchor':22s} {'comparison point':26s} {'block':>7s} "
          f"{'predicted':>10s} {'observed':>9s} {'ratio':>7s}")
    for aname, a in ANCHORS:
        for lbl, bc in CMP_240.items():
            need = [(0.0, a["1x"]), (bc, a["2x"])]
            cohort = [m for m in pop
                      if all(bpm.get((m, st, round(x, 6), round(y, 6)))
                             is not None for x, y in need)]
            if not cohort:
                continue
            ref = float(np.median(
                [bpm[(m, st, 0.0, round(a["1x"], 6))] - base[m]
                 for m in cohort]))
            pred = float(np.median(
                [bpm[(m, st, round(bc, 6), round(a["2x"], 6))] - base[m]
                 for m in cohort])) - ref
            rec = {"state": st, "anchor": aname, "point": lbl, "block": bc,
                   "n_cohort": len(cohort), "predicted_bpm": pred,
                   "observed_bpm": SMPC_OBSERVED_BPM,
                   "ratio": pred / SMPC_OBSERVED_BPM,
                   "is_primary": "PRIMARY" in lbl}
            out["external"].append(rec)
            print(f"  {aname:22s} {lbl:26s} {bc:7.1%} {pred:+10.2f} "
                  f"{SMPC_OBSERVED_BPM:+9.1f} {pred/SMPC_OBSERVED_BPM:7.2f}")
    print()

# ============ 5. BLISS at the PRIMARY anchor ============================
print("=" * 112)
print("BLISS CLASSIFICATION at the PRIMARY anchor (1x), informative-rung "
      "exclusions applied")
print("  frozen ladder: no-events / ceiling are NON-INFORMATIVE and excluded "
      "from interpretation")
print("=" * 112)
out["bliss"] = []
for st in ("control", "iso"):
    pop = pops[st]
    n = len(pop)
    print(f"\n  STATE = {st.upper()}  (n = {n})")
    print(f"  {'block':>7s} {'P_A':>7s} {'P_B':>7s} {'P_AB':>7s} "
          f"{'P_AB 95% CI':>17s} {'Bliss exp':>10s} {'class':>16s} "
          f"{'informative':>12s}")
    for bc in BLISS_RUNGS:
        A = {m for m in pop if not paces(m, st, bc, 0.0)}
        B = {m for m in pop if not paces(m, st, 0.0, B_PRIMARY)}
        AB = {m for m in pop if not paces(m, st, bc, B_PRIMARY)}
        PA, PB, PAB = len(A) / n, len(B) / n, len(AB) / n
        Pexp = PA + PB - PA * PB
        lo, hi = wilson(len(AB), n)
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
        info = cls not in ("no events", "ceiling")
        out["bliss"].append({"state": st, "block": bc, "P_A": PA, "P_B": PB,
                             "P_AB": PAB, "P_AB_ci95": [float(lo), float(hi)],
                             "bliss_expected": Pexp, "bliss_class": cls,
                             "informative": bool(info)})
        print(f"  {bc:7.1%} {PA:7.3f} {PB:7.3f} {PAB:7.3f} "
              f"[{lo:7.3f},{hi:7.3f}] {Pexp:10.3f} {cls:>16s} "
              f"{'yes' if info else 'EXCLUDED':>12s}")
    inf = [r for r in out["bliss"] if r["state"] == st and r["informative"]]
    counts = {}
    for r in inf:
        counts[r["bliss_class"]] = counts.get(r["bliss_class"], 0) + 1
    print(f"    informative rungs: {len(inf)}/{len(BLISS_RUNGS)}   "
          f"classes: {counts}")

with open(os.path.join(DEST, "P3_results_full.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\n-> 08_taskP/p3/P3_results_full.json")
