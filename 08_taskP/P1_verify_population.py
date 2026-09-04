"""P1 verification: freeze-check the completed 5000-model run and the 1028-model
retained population, and run the forensic check that the historical 188 are
exactly the retained members of indices 0-939.

Read-only. Writes only 08_taskP/P1_verification.json.
"""
import hashlib
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "zhou_san_run")
RESULTS = os.path.join(WORK, "results.jsonl")
NPZ = os.path.join(WORK, "population_retained_20260823T094616Z.npz")
MAN = os.path.join(WORK, "population_manifest_20260823T094616Z.json")
HIST = os.path.join(ROOT, "outputs", "step3fix_run_statefix.json")

out = {}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


recs = [json.loads(l) for l in open(RESULTS, encoding="utf-8") if l.strip()]
man = json.load(open(MAN, encoding="utf-8"))
z = np.load(NPZ, allow_pickle=True)
hist = json.load(open(HIST, encoding="utf-8"))
hrecs = {r["index"]: r for r in hist["results"]}

print("=" * 74)
print("1. RESULTS.JSONL INTEGRITY")
print("=" * 74)
idx = [r["index"] for r in recs]
out["n_records"] = len(recs)
out["unique_indices"] = len(set(idx))
out["contiguous_0_4999"] = sorted(set(idx)) == list(range(5000))
st = {}
for r in recs:
    st[r["status"]] = st.get(r["status"], 0) + 1
out["status_counts"] = st
print(f"  records                 : {len(recs)}")
print(f"  unique indices          : {len(set(idx))}")
print(f"  contiguous 0-4999       : {out['contiguous_0_4999']}")
print(f"  duplicate indices       : {len(idx) - len(set(idx))}")
print(f"  status                  : {st}")

by = {r["index"]: r for r in recs}

# ---------------------------------------------------------------- provenance
seeded = [i for i in range(5000) if by[i].get("seeded_from") == "step3fix"]
fresh = [i for i in range(5000) if "seeded_from" not in by[i]]
out["n_seeded"] = len(seeded)
out["n_fresh"] = len(fresh)
out["seeded_is_0_939"] = seeded == list(range(940))
out["fresh_is_940_4999"] = fresh == list(range(940, 5000))
print(f"  seeded (0-939)          : {len(seeded)}  exact 0-939: "
      f"{out['seeded_is_0_939']}")
print(f"  fresh  (940-4999)       : {len(fresh)}  exact 940-4999: "
      f"{out['fresh_is_940_4999']}")

# seeded records must still equal history byte-for-value
mism = []
for i in seeded:
    h, g = hrecs[i], by[i]
    for k in ("status", "CL_ms", "OS_mV", "MDP_mV", "APA_mV"):
        a, b = h.get(k), g.get(k)
        if a is None and b is None:
            continue
        if a is None or b is None or (a != b if k == "status"
                                      else abs(a - b) > 0):
            mism.append((i, k, a, b))
out["seeded_exactly_match_history"] = not mism
out["seeded_mismatches"] = mism[:20]
print(f"  seeded == history exact : {not mism}  ({len(mism)} mismatches)")

# ---------------------------------------------------------------- field cover
cov = {}
for r in recs:
    for k in r:
        cov[k] = cov.get(k, 0) + 1
out["field_coverage"] = cov
print("\n  field coverage across 5000:")
for k, v in sorted(cov.items()):
    print(f"    {k:14s} {v:5d}" + ("" if v == 5000 else "   <-- PARTIAL"))

print()
print("=" * 74)
print("2. RETENTION RE-DERIVED INDEPENDENTLY FROM RESULTS.JSONL")
print("=" * 74)
lo, hi = man["criteria"]["bcl_ms"]
kept = [i for i in range(5000)
        if by[i]["status"] == "ok" and by[i]["CL_ms"] is not None
        and lo <= by[i]["CL_ms"] <= hi and by[i]["OS_mV"] > 0]
out["criteria"] = {"bcl_ms": [lo, hi], "overshoot_positive": True}
out["n_retained_recomputed"] = len(kept)
out["n_retained_manifest"] = man["n_retained"]
out["retention_matches_manifest"] = len(kept) == man["n_retained"]
print(f"  criteria                : {lo} <= CL_ms <= {hi}, OS_mV > 0, status ok")
print(f"  retained (recomputed)   : {len(kept)}")
print(f"  retained (manifest)     : {man['n_retained']}")
print(f"  match                   : {out['retention_matches_manifest']}")
print(f"  retention fraction      : {len(kept)/5000:.4f}  "
      f"(Zhou 1046/5000 = 0.2092)")

print()
print("=" * 74)
print("3. NPZ INTEGRITY")
print("=" * 74)
npz_idx = z["model_index"]
out["npz_sha256"] = sha256(NPZ)
out["npz_sha256_matches_manifest"] = out["npz_sha256"] == man["population_sha256"]
out["npz_n"] = int(npz_idx.size)
out["npz_index_equals_recomputed"] = bool(
    np.array_equal(np.sort(npz_idx), np.array(kept)))
out["npz_arrays"] = {k: list(z[k].shape) for k in z.files}
print(f"  sha256 matches manifest : {out['npz_sha256_matches_manifest']}")
print(f"  n models                : {npz_idx.size}")
print(f"  index set == recomputed : {out['npz_index_equals_recomputed']}")
print(f"  arrays                  : "
      f"{ {k: list(z[k].shape) for k in z.files} }")

# biomarkers in npz must equal results.jsonl
bm_ok = {}
for k in ("CL_ms", "OS_mV", "MDP_mV", "APA_mV"):
    a = z[k]
    b = np.array([by[int(i)][k] for i in npz_idx])
    bm_ok[k] = bool(np.array_equal(a, b))
out["npz_biomarkers_match_jsonl"] = bm_ok
print(f"  biomarkers == jsonl     : {bm_ok}")

# scales must equal the frozen LHS rows
lhs = np.load(os.path.join(WORK, "lhs_sample.npz"), allow_pickle=True)
out["npz_scales_match_lhs"] = bool(
    np.array_equal(z["scales"], lhs["scales"][npz_idx]))
out["npz_values_match_lhs"] = bool(
    np.array_equal(z["values"], lhs["values"][npz_idx]))
print(f"  scales == frozen LHS    : {out['npz_scales_match_lhs']}")
print(f"  values == frozen LHS    : {out['npz_values_match_lhs']}")
print(f"  all retained CL in band : "
      f"{bool(((z['CL_ms'] >= lo) & (z['CL_ms'] <= hi)).all())}")
print(f"  all retained OS > 0     : {bool((z['OS_mV'] > 0).all())}")

print()
print("=" * 74)
print("4. FORENSIC — ARE THE HISTORICAL 188 EXACTLY THE RETAINED 0-939?")
print("=" * 74)
prefix_kept = [i for i in kept if i < 940]
out["n_retained_in_prefix"] = len(prefix_kept)

# historical retained set, recomputed from the historical records with the
# SAME criteria (this is the definition the 188 came from)
hist_kept = [i for i in sorted(hrecs)
             if hrecs[i]["status"] == "ok" and hrecs[i]["CL_ms"] is not None
             and lo <= hrecs[i]["CL_ms"] <= hi and hrecs[i]["OS_mV"] > 0]
out["n_historical_retained"] = len(hist_kept)
out["historical_188_equals_prefix_retained"] = prefix_kept == hist_kept
out["prefix_only"] = [i for i in prefix_kept if i not in set(hist_kept)]
out["historical_only"] = [i for i in hist_kept if i not in set(prefix_kept)]
print(f"  retained among 0-939    : {len(prefix_kept)}")
print(f"  historical retained     : {len(hist_kept)}")
print(f"  SETS IDENTICAL          : "
      f"{out['historical_188_equals_prefix_retained']}")
if out["prefix_only"] or out["historical_only"]:
    print(f"    in prefix not history : {out['prefix_only'][:20]}")
    print(f"    in history not prefix : {out['historical_only'][:20]}")
out["n_retained_in_new_940_4999"] = len(kept) - len(prefix_kept)
print(f"  retained among 940-4999 : {out['n_retained_in_new_940_4999']}")

print()
print("=" * 74)
print("5. RUNTIME FORENSICS")
print("=" * 74)


def secstat(ii, label):
    s = np.array([by[i]["seconds"] for i in ii if by[i].get("seconds")
                  is not None])
    p = np.array([by[i]["seconds"] for i in ii if by[i]["status"] == "ok"])
    n = np.array([by[i]["seconds"] for i in ii
                  if by[i]["status"] == "no_pacing"])
    d = {"n": len(s), "sum_s": float(s.sum()), "mean_s": float(s.mean()),
         "median_s": float(np.median(s)),
         "pacing_mean_s": float(p.mean()) if p.size else None,
         "no_pacing_mean_s": float(n.mean()) if n.size else None}
    print(f"  {label}")
    print(f"    n={d['n']}  sum={d['sum_s']:.0f} s  mean={d['mean_s']:.1f} s  "
          f"median={d['median_s']:.1f} s")
    print(f"    pacing mean={d['pacing_mean_s']:.1f} s   "
          f"no_pacing mean={d['no_pacing_mean_s']:.2f} s")
    return d


out["timing_seeded_0_939"] = secstat(seeded, "indices 0-939 (historical)")
out["timing_fresh_940_4999"] = secstat(fresh, "indices 940-4999 (this run)")
r = (out["timing_seeded_0_939"]["pacing_mean_s"] /
     out["timing_fresh_940_4999"]["pacing_mean_s"])
out["pacing_cpu_speedup_hist_over_new"] = float(r)
print(f"\n  per-pacing-model CPU ratio historical/new : {r:.1f}x")
print(f"  historical duration_s : {hist.get('criteria', {}).get('duration_s')}")
print(f"  this run duration_s   : {man['criteria']['duration_s']}")
out["hist_criteria"] = hist.get("criteria")

with open(os.path.join(ROOT, "08_taskP", "P1_verification.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print("\n-> 08_taskP/P1_verification.json")
