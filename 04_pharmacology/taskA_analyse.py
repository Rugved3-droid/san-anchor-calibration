"""Task A analysis: distributions across the retained population."""
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")


def load(cur):
    with open(os.path.join(OUT, f"taskA_{cur}_population_sweep.json"),
              encoding="utf-8") as f:
        return json.load(f)


def pct(a, p):
    return float(np.percentile(a, p))


summary = {}
for cur in ("G_CaL", "G_f"):
    d = load(cur)
    recs = d["records"]
    print("=" * 72)
    print(f"{cur}: {len(recs)} retained models")

    thr = [r["threshold"] for r in recs]
    fin = np.array([t for t in thr if t is not None], float)
    n_never = sum(1 for t in thr if t is None)
    print(f"  never quiescent to 90% : {n_never} ({n_never/len(recs)*100:.1f}%)")
    if len(fin):
        print(f"  quiescence threshold (n={len(fin)}): median {np.median(fin)*100:.1f}%"
              f"  IQR {pct(fin,25)*100:.1f}-{pct(fin,75)*100:.1f}%"
              f"  range {fin.min()*100:.0f}-{fin.max()*100:.0f}%")

    fr = {}
    for lv in (0.30, 0.40, 0.50, 0.60, 0.70, 0.80):
        n = sum(1 for r in recs if r["levels"].get(str(lv)) is not None)
        fr[lv] = n / len(recs)
        print(f"    pacing at {lv:.0%} block: {n}/{len(recs)} = {n/len(recs)*100:.1f}%")

    # rate ceiling: largest bpm drop still achieved while pacing
    drops, base_bpms = [], []
    for r in recs:
        lv = r["levels"]
        b0 = lv.get("0.0")
        if not b0:
            continue
        base = b0["bpm"]
        base_bpms.append(base)
        alive = [v["bpm"] for k, v in lv.items() if v is not None]
        drops.append(min(alive) - base)
    drops = np.array(drops)
    base_bpms = np.array(base_bpms)
    print(f"\n  baseline rate of retained models: "
          f"median {np.median(base_bpms):.1f} bpm "
          f"(range {base_bpms.min():.1f}-{base_bpms.max():.1f})")
    print(f"  max rate drop while still pacing:")
    print(f"    median {np.median(drops):+.2f} bpm   "
          f"IQR {pct(drops,25):+.2f} to {pct(drops,75):+.2f}   "
          f"range {drops.min():+.2f} to {drops.max():+.2f}")
    n10 = int((drops <= -10).sum())
    print(f"    models able to reach -10 bpm: {n10}/{len(drops)} "
          f"= {n10/len(drops)*100:.1f}%")

    summary[cur] = {
        "n": len(recs), "n_never_quiescent": n_never,
        "threshold_median": float(np.median(fin)) if len(fin) else None,
        "threshold_iqr": [pct(fin, 25), pct(fin, 75)] if len(fin) else None,
        "threshold_range": [float(fin.min()), float(fin.max())] if len(fin) else None,
        "fraction_pacing": {str(k): v for k, v in fr.items()},
        "baseline_bpm_median": float(np.median(base_bpms)),
        "max_drop_median": float(np.median(drops)),
        "max_drop_iqr": [pct(drops, 25), pct(drops, 75)],
        "max_drop_range": [float(drops.min()), float(drops.max())],
        "frac_reaching_-10bpm": n10 / len(drops),
    }

# diltiazem / verapamil mapped block levels
print("\n" + "=" * 72)
print("Mapped block levels vs population tolerance (I_CaL):")
cal = summary["G_CaL"]["fraction_pacing"]


def interp_pacing(b):
    ks = sorted(float(k) for k in cal)
    if b <= ks[0]:
        return cal[str(ks[0])]
    if b >= ks[-1]:
        return cal[str(ks[-1])]      # 0% pacing at/above the top tabulated level
    for i in range(len(ks) - 1):
        if ks[i] <= b <= ks[i + 1]:
            f = (b - ks[i]) / (ks[i + 1] - ks[i])
            return cal[str(ks[i])] + f * (cal[str(ks[i + 1])] - cal[str(ks[i])])
    return None


for drug, b_ba, b_ca in (("diltiazem", 0.533, 0.828), ("verapamil", 0.182, 0.483)):
    p_ba, p_ca = interp_pacing(b_ba), interp_pacing(b_ca)
    print(f"  {drug:10s} Ba2+ {b_ba:.1%} block -> ~{p_ba*100:.0f}% of population still pacing")
    print(f"  {'':10s} Ca2+ {b_ca:.1%} block -> ~{p_ca*100:.0f}% of population still pacing")

with open(os.path.join(OUT, "taskA_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print(f"\n-> {os.path.join(OUT, 'taskA_summary.json')}")
