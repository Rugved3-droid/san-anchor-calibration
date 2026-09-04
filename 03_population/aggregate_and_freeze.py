"""Step 4 - aggregate completed chunks, apply retention, freeze the population.

Combines every step3_run_*.json produced so far, de-duplicates by model index,
applies Zhou's criteria, reports the retention count against the reference
(1,046 of 5,000), and writes the retained parameter vectors to a timestamped,
checksummed file.

The retention count is reported exactly as it comes out. Nothing here tunes the
sampling or the criteria toward the reference value.
"""
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "outputs")
CONFIG = os.path.join(ROOT, "00_config", "config.yaml")
SAMPLE = os.path.join(ROOT, "outputs", "step2_lhs_sample.npz")


def wilson(k, n, z=1.96):
    """Wilson score interval - correct for proportions near the tails."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    r = cfg["retention"]

    # ---- gather, de-duplicate by index ----------------------------------
    records, sources = {}, []
    for p in sorted(glob.glob(os.path.join(OUT_DIR, "step3_run_*.json"))):
        with open(p, encoding="utf-8") as f:
            blob = json.load(f)
        tag = blob["tag"]
        if tag == "bench10":
            continue     # timing probe; its indices are re-run in bench100
        sources.append({"tag": tag, "n": blob["n_models"],
                        "wall_s": blob["wall_clock_s"],
                        "workers": blob["workers"]})
        for rec in blob["results"]:
            records[rec["index"]] = rec

    idxs = sorted(records)
    n = len(idxs)
    if n == 0:
        print("no runs found")
        return 1

    ok = [records[i] for i in idxs if records[i]["status"] == "ok"]
    nop = [i for i in idxs if records[i]["status"] == "no_pacing"]
    fail = [i for i in idxs if records[i]["status"] == "solver_failure"]

    def keep(rec):
        return (rec["status"] == "ok"
                and r["bcl_min_ms"] <= rec["CL_ms"] <= r["bcl_max_ms"]
                and rec["OS_mV"] > 0.0)

    kept = [records[i] for i in idxs if keep(records[i])]
    frac = len(kept) / n
    lo, hi = wilson(len(kept), n)

    ref_frac = r["reference_retained"] / r["reference_total"]

    print("Step 4 - retention")
    print(f"  chunks combined      : {len(sources)}")
    print(f"  models simulated     : {n} of {cfg['sampling']['n_models']} sampled")
    print(f"  contiguous index span: {idxs[0]}..{idxs[-1]}")
    print(f"\n  integrated ok        : {len(ok)}  ({len(ok)/n*100:.1f}%)")
    print(f"  no pacing            : {len(nop)}  ({len(nop)/n*100:.1f}%)")
    print(f"  solver failures      : {len(fail)}  ({len(fail)/n*100:.1f}%)")
    print(f"\n  RETAINED             : {len(kept)} / {n}  = {frac*100:.2f}%")
    print(f"  95% CI (Wilson)      : [{lo*100:.2f}%, {hi*100:.2f}%]")
    print(f"\n  Zhou et al. reference: {r['reference_retained']} / "
          f"{r['reference_total']} = {ref_frac*100:.2f}%")
    print(f"  reference inside CI  : {lo <= ref_frac <= hi}")
    print(f"  implied count at 5,000: {frac*r['reference_total']:.0f} "
          f"(95% CI {lo*r['reference_total']:.0f}-{hi*r['reference_total']:.0f})")

    if kept:
        cls = np.array([k["CL_ms"] for k in kept])
        oss = np.array([k["OS_mV"] for k in kept])
        mdp = np.array([k["MDP_mV"] for k in kept])
        print(f"\n  retained CL  : {cls.min():.1f} - {cls.max():.1f} ms "
              f"(mean {cls.mean():.1f})")
        print(f"  retained OS  : {oss.min():.1f} - {oss.max():.1f} mV "
              f"(mean {oss.mean():.1f})")
        print(f"  retained MDP : {mdp.min():.1f} - {mdp.max():.1f} mV "
              f"(mean {mdp.mean():.1f})")

    # ---- freeze the retained parameter vectors --------------------------
    z = np.load(SAMPLE, allow_pickle=True)
    names = [str(x) for x in z["names"]]
    variables = [str(x) for x in z["variables"]]
    baseline = z["baseline"]
    ki = np.array([k["index"] for k in kept], dtype=int)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    frozen = os.path.join(OUT_DIR, f"population_retained_{stamp}.npz")
    np.savez_compressed(
        frozen,
        model_index=ki,
        scales=z["scales"][ki],
        values=z["values"][ki],
        names=np.array(names),
        variables=np.array(variables),
        baseline=baseline,
        CL_ms=np.array([k["CL_ms"] for k in kept]),
        OS_mV=np.array([k["OS_mV"] for k in kept]),
        MDP_mV=np.array([k["MDP_mV"] for k in kept]),
        APA_mV=np.array([k["APA_mV"] for k in kept]),
    )
    with open(frozen, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()

    # human-readable companion
    csv = os.path.join(OUT_DIR, f"population_retained_{stamp}.csv")
    with open(csv, "w", encoding="utf-8") as f:
        f.write("model_index," + ",".join(f"scale_{x}" for x in names)
                + ",CL_ms,OS_mV,MDP_mV,APA_mV\n")
        for k in kept:
            sc = z["scales"][k["index"]]
            f.write(f"{k['index']}," + ",".join(f"{x:.6f}" for x in sc)
                    + f",{k['CL_ms']:.3f},{k['OS_mV']:.3f},"
                      f"{k['MDP_mV']:.3f},{k['APA_mV']:.3f}\n")

    manifest = {
        "step": "4 - retention and frozen population",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "status": ("PARTIAL - subset of the 5,000-model sample completed in this "
                   "environment" if n < cfg["sampling"]["n_models"] else "COMPLETE"),
        "reference_study": ("Zhou et al. 2019, Front Physiol 10:259, "
                            "doi:10.3389/fphys.2019.00259"),
        "baseline_model": "Fabbri et al. 2017, PMR e/568 CellML, imported via Myokit",
        "criteria": {"bcl_min_ms": r["bcl_min_ms"], "bcl_max_ms": r["bcl_max_ms"],
                     "overshoot_positive": True,
                     "simulated_s_per_model": cfg["simulation"]["duration_s"]},
        "sample_file": os.path.basename(SAMPLE),
        "n_sampled_total": int(cfg["sampling"]["n_models"]),
        "n_simulated": n,
        "counts": {"ok": len(ok), "no_pacing": len(nop),
                   "solver_failure": len(fail), "retained": len(kept)},
        "retention_fraction": frac,
        "retention_ci95_wilson": [lo, hi],
        "reference_retention_fraction": ref_frac,
        "reference_within_ci": bool(lo <= ref_frac <= hi),
        "implied_retained_at_5000": frac * r["reference_total"],
        "parameters": [{"zhou_symbol": nm, "variable": v, "baseline": float(b)}
                       for nm, v, b in zip(names, variables, baseline)],
        "frozen_population_file": os.path.basename(frozen),
        "frozen_population_sha256": digest,
        "frozen_population_csv": os.path.basename(csv),
        "chunks": sources,
        "note": ("Retention reported exactly as computed. Neither the sampling nor "
                 "the criteria were adjusted toward the reference value."),
    }
    mp = os.path.join(OUT_DIR, f"population_manifest_{stamp}.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n  frozen population -> {frozen}")
    print(f"  sha256            : {digest}")
    print(f"  manifest          -> {mp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
