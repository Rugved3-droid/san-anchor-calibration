"""Task 1 - compare the pre-statefix run against the state-isolated re-run.

Reports aggregate retention plus the model-by-model switch analysis: how many
retained models are identical, how many switch in each direction, the maximum
single-model CL change, whether switches cluster at the 600/1000 ms boundaries,
and whether any NO_PACING classifications changed.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from common import load_config                              # noqa: E402
import numpy as np                                           # noqa: E402

OUT_DIR = os.path.join(ROOT, "outputs")
OLD_DIR = os.path.join(ROOT, "zhou_san_run_pre_statefix")


def load_old():
    recs = {}
    for p in sorted(glob.glob(os.path.join(OLD_DIR, "step3_run_*.json"))):
        with open(p, encoding="utf-8") as f:
            blob = json.load(f)
        if blob["tag"] == "bench10":
            continue
        for r in blob["results"]:
            recs[r["index"]] = r
    return recs


def load_new():
    recs = {}
    ck = os.path.join(OUT_DIR, "checkpoint_statefix.jsonl")
    if os.path.exists(ck):
        with open(ck, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        recs[r["index"]] = r
                    except json.JSONDecodeError:
                        pass
    return recs


def keep(r, cfg):
    c = cfg["retention"]
    return (r["status"] == "ok"
            and c["bcl_min_ms"] <= r["CL_ms"] <= c["bcl_max_ms"]
            and r["OS_mV"] > 0.0)


def main():
    cfg = load_config()
    old, new = load_old(), load_new()
    common = sorted(set(old) & set(new))
    if not common:
        print("no overlapping models yet")
        return 1

    print(f"Comparison over {len(common)} models "
          f"(old {len(old)}, new {len(new)})\n")

    ko = {i: keep(old[i], cfg) for i in common}
    kn = {i: keep(new[i], cfg) for i in common}
    n_old, n_new = sum(ko.values()), sum(kn.values())

    both = [i for i in common if ko[i] and kn[i]]
    lost = [i for i in common if ko[i] and not kn[i]]     # retained -> rejected
    gained = [i for i in common if not ko[i] and kn[i]]   # rejected -> retained

    print(f"  retained BEFORE : {n_old} / {len(common)} = "
          f"{n_old/len(common)*100:.2f}%")
    print(f"  retained AFTER  : {n_new} / {len(common)} = "
          f"{n_new/len(common)*100:.2f}%")
    print(f"  net change      : {n_new-n_old:+d}\n")
    print(f"  identical (retained in both) : {len(both)}")
    print(f"  retained -> rejected         : {len(lost)}")
    print(f"  rejected -> retained         : {len(gained)}")
    print(f"  total switches               : {len(lost)+len(gained)} "
          f"({(len(lost)+len(gained))/len(common)*100:.2f}% of models)")

    # ---- status changes, incl. the bistable no_pacing class ---------------
    st_change = [(i, old[i]["status"], new[i]["status"]) for i in common
                 if old[i]["status"] != new[i]["status"]]
    print(f"\n  status classification changes: {len(st_change)}")
    from collections import Counter
    for (a, b), n in Counter((x[1], x[2]) for x in st_change).most_common():
        print(f"    {a:16s} -> {b:16s} : {n}")
    nop_changed = [x for x in st_change
                   if "no_pacing" in (x[1], x[2])]
    print(f"  NO_PACING reclassifications  : {len(nop_changed)}")
    if nop_changed[:10]:
        for i, a, b in nop_changed[:10]:
            print(f"     model {i}: {a} -> {b}")

    # ---- CL changes among models that paced in both ----------------------
    pace_both = [i for i in common
                 if old[i]["status"] == "ok" and new[i]["status"] == "ok"]
    d = np.array([new[i]["CL_ms"] - old[i]["CL_ms"] for i in pace_both])
    print(f"\n  models pacing in both        : {len(pace_both)}")
    if len(d):
        j = int(np.argmax(np.abs(d)))
        worst = pace_both[j]
        print(f"  |dCL| mean {np.mean(np.abs(d)):.4f} ms, "
              f"median {np.median(np.abs(d)):.4f} ms")
        print(f"  MAX |dCL| = {abs(d[j]):.4f} ms  (model {worst}: "
              f"{old[worst]['CL_ms']:.3f} -> {new[worst]['CL_ms']:.3f})")
        print(f"  models with |dCL| > 1 ms     : {int((np.abs(d) > 1).sum())}")
        print(f"  models with |dCL| > 10 ms    : {int((np.abs(d) > 10).sum())}")

    # ---- do switches cluster at the boundaries? --------------------------
    lo, hi = cfg["retention"]["bcl_min_ms"], cfg["retention"]["bcl_max_ms"]

    def dist_to_edge(cl):
        return min(abs(cl - lo), abs(cl - hi))

    sw = lost + gained
    if sw:
        dists = []
        for i in sw:
            cls = [r["CL_ms"] for r in (old[i], new[i])
                   if r["status"] == "ok" and r["CL_ms"] is not None]
            if cls:
                dists.append(min(dist_to_edge(c) for c in cls))
        if dists:
            dists = np.array(dists)
            print(f"\n  switching models, distance of CL to nearest "
                  f"{lo:.0f}/{hi:.0f} ms boundary:")
            print(f"    median {np.median(dists):.2f} ms, "
                  f"mean {np.mean(dists):.2f} ms, max {np.max(dists):.2f} ms")
            for thr in (5, 10, 25, 50):
                print(f"    within {thr:3d} ms of a boundary: "
                      f"{int((dists <= thr).sum())} / {len(dists)} "
                      f"({(dists <= thr).mean()*100:.0f}%)")
    # non-switching retained models, for contrast
    if both:
        dn = np.array([dist_to_edge(new[i]["CL_ms"]) for i in both])
        print(f"\n  non-switching retained models, distance to boundary:")
        print(f"    median {np.median(dn):.2f} ms  "
              f"(within 25 ms: {int((dn <= 25).sum())}/{len(dn)})")

    rep = {
        "n_compared": len(common),
        "retained_before": n_old, "retained_after": n_new,
        "retention_before": n_old / len(common),
        "retention_after": n_new / len(common),
        "identical_retained": len(both),
        "retained_to_rejected": len(lost),
        "rejected_to_retained": len(gained),
        "switch_indices": {"lost": lost, "gained": gained},
        "status_changes": [{"index": i, "before": a, "after": b}
                           for i, a, b in st_change],
        "no_pacing_reclassifications": len(nop_changed),
        "max_abs_dCL_ms": float(np.max(np.abs(d))) if len(d) else None,
        "mean_abs_dCL_ms": float(np.mean(np.abs(d))) if len(d) else None,
    }
    p = os.path.join(OUT_DIR, "statefix_comparison.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print(f"\n  -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
