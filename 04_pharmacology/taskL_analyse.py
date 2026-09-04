"""Task L1 analysis - EAR across ALL THREE ivabradine anchors.

The primary anchor is now Doesch 2007 (PMID 17989604), selected on DESIGN
QUALITY and explicitly not on gap magnitude (see config
calibration_provenance.ivabradine.selection_rule). All three anchors are
reported as a sensitivity band, as the config's reporting_requirement demands.

  anchor                        drop    I_f block   implied IC50   fold gap
  Doesch 2007 (PRIMARY)        21.0%      58.40%        8.0 nM        250x
  10-year cohort               18.1%      50.90%       11.7 nM        172x
  36-month (superseded)        10.8%      31.20%       32.8 nM         61x

Exposure scaling as in Task I: keep the in vitro Hill slope n = 0.80, re-solve
IC50 through each anchor at free Cmax 12.2 nM, evaluate at 1x/2x/3x CYP3A4-
inhibited exposure.

Verapamil: Ba2+ mapping only (IC50 198.7 nM, Hill 1.09, f_u 10.4%), on the
chronic oral rungs, which include the exact clinical band edges so the
"does it cross inside the band" question needs no interpolation.
"""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
CKPT = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")

ANCHORS = [
    ("Doesch 2007  (PRIMARY)", 0.584,  [0.584, 0.7097, 0.7717], 250),
    ("10-year cohort",         0.509,  [0.509, 0.6435, 0.714],  172),
    ("36-month (superseded)",  0.312,  [0.312, 0.4412, 0.522],   61),
]
MULT = ["1x", "2x", "3x"]
IC50_V, HILL_V, MW, FU = 198.7, 1.09, 454.6, 0.104
BANDS = {"240 mg/day": (0.029, 0.140), "480 mg/day": (0.108, 0.300)}
VER = [0.0, 0.029, 0.05, 0.10, 0.108, 0.14, 0.15, 0.20, 0.25, 0.275, 0.30, 0.40]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def conc(b):
    return 0.0 if b <= 0 else IC50_V * (b / (1.0 - b)) ** (1.0 / HILL_V)


res = {}
for line in open(CKPT, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    res.setdefault((r["state"], round(r["b_cal"], 6),
                    round(r["b_f"], 6)), {})[r["model"]] = r["bpm"]

pops = {st: sorted(m for m, v in res[(st, 0.0, 0.0)].items() if v is not None)
        for st in ("control", "iso")}


def complete(st, bc, bf):
    d = res.get((st, round(bc, 6), round(bf, 6)))
    return d is not None and all(m in d for m in pops[st])


print("=" * 116)
print("TASK L1 - excess absolute risk across ALL THREE ivabradine anchors")
print("=" * 116)
print("Ba2+ verapamil mapping. Bands: 240 mg/day = 2.9-14.0% block, "
      "480 mg/day = 10.8-30.0% block.")

report = {"anchors": [{"label": a, "block_1x": b, "arms": arms,
                       "fold_gap": g} for a, b, arms, g in ANCHORS],
          "bands": BANDS, "states": {}}

for state in ("control", "iso"):
    pop = pops[state]
    n = len(pop)
    base = {m: res[(state, 0.0, 0.0)][m] for m in pop}
    print("\n" + "=" * 116)
    print(f"STATE = {state.upper()}   (n = {n}/188 drug-free pacing, median "
          f"{np.median(list(base.values())):.1f} bpm)")
    print("=" * 116)

    def fails(bc, bf):
        d = res[(state, round(bc, 6), round(bf, 6))]
        return {m for m in pop if d.get(m) is None}

    st_rows = []
    for label, b1x, arms, gap in ANCHORS:
        print(f"\n  --- {label}   I_f 1x = {b1x:.1%}   "
              f"({gap}x vs in vitro) ---")
        print(f"  {'verap':>7s} {'ng/mL':>8s} {'P_A':>6s} |"
              + "".join(f"{m + '  EAR [95% CI]':>26s}" for m in MULT)
              + "   band")
        for bc in VER:
            A = fails(bc, 0.0)
            PA = len(A) / n
            cells = []
            rec = {"anchor": label, "block": bc,
                   "total_ng_per_mL": conc(bc) / FU * MW / 1000,
                   "P_A": PA, "arms": {}}
            for mi, bf in zip(MULT, arms):
                B = fails(0.0, bf)
                AB = fails(bc, bf)
                surv = {m for m in pop if m not in A and m not in B}
                k = len(AB & surv)
                ear = k / n
                lo, hi = wilson(k, n)
                cells.append(f"{ear:8.3f} [{lo:5.3f},{hi:5.3f}]")
                rec["arms"][mi] = {"b_f": bf, "P_B": len(B) / n,
                                   "P_AB": len(AB) / n, "EAR": ear,
                                   "EAR_ci": [lo, hi], "EAR_k": k}
            inb = [x for x, (l_, h_) in BANDS.items() if l_ <= bc <= h_]
            rec["in_bands"] = inb
            st_rows.append(rec)
            print(f"  {bc:7.1%} {conc(bc)/FU*MW/1000:8.1f} {PA:6.3f} |"
                  + "".join(f"{c:>26s}" for c in cells)
                  + ("   " + ",".join(x.split()[0] for x in inb) if inb else ""))

        print(f"  {'ivab alone':>7s} {'-':>8s} {'-':>6s} |"
              + "".join(f"{('P_B=' + format(len(fails(0.0, bf))/n, '.3f')):>26s}"
                        for bf in arms))

    # ---- threshold crossings inside each band, all anchors ---------------
    print(f"\n  THRESHOLD CROSSINGS INSIDE THE CLINICAL BANDS ({state})")
    print(f"  {'band':12s} {'anchor':24s} {'arm':4s} {'max EAR':>9s} "
          f"{'at block':>9s}  {'>5%':>5s} {'>5%CI':>6s}  {'>10%':>5s} "
          f"{'>10%CI':>6s}")
    th = {}
    for band, (blo, bhi) in BANDS.items():
        for label, b1x, arms, gap in ANCHORS:
            for mi in MULT:
                rows = [r for r in st_rows if r["anchor"] == label
                        and blo <= r["block"] <= bhi]
                best = max(rows, key=lambda r: r["arms"][mi]["EAR"])
                e = best["arms"][mi]
                c5 = any(r["arms"][mi]["EAR"] > 0.05 for r in rows)
                c10 = any(r["arms"][mi]["EAR"] > 0.10 for r in rows)
                c5c = any(r["arms"][mi]["EAR_ci"][0] > 0.05 for r in rows)
                c10c = any(r["arms"][mi]["EAR_ci"][0] > 0.10 for r in rows)
                th[f"{band}|{label}|{mi}"] = {
                    "max_EAR": e["EAR"], "ci": e["EAR_ci"],
                    "at_block": best["block"],
                    "crosses_5": c5, "crosses_5_ci": c5c,
                    "crosses_10": c10, "crosses_10_ci": c10c}
                print(f"  {band:12s} {label:24s} {mi:4s} {e['EAR']:8.1%} "
                      f"{best['block']:8.1%}  "
                      f"{'YES' if c5 else 'no':>5s} {'YES' if c5c else 'no':>6s}  "
                      f"{'YES' if c10 else 'no':>5s} "
                      f"{'YES' if c10c else 'no':>6s}")
    report["states"][state] = {"n": n, "rows": st_rows, "band_thresholds": th}

with open(os.path.join(OUT, "taskL_three_anchor_EAR.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskL_three_anchor_EAR.json')}")
