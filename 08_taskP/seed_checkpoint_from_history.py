"""OPTIONAL P1 accelerator: seed the standalone runner's checkpoint with the
940 models already simulated under the state-isolated procedure.

This is legitimate only because the P1 gates verified that the runner
reproduces those exact historical values bit-identically (see
08_taskP/P1_gate_results.json and P1_gate1_strengthened.json: model 0 CL
872.745454545455 under three different predecessors, matching the frozen
historical record to <1e-9).

KNOWN LIMITATION - RECORD-SCHEMA HETEROGENEITY
  The historical records carry index, status, CL_ms, OS_mV, MDP_mV, APA_mV,
  n_beats and seconds. The current runner's run_one() additionally returns
  CL_ms_sd, DDR100_mV_s and dVdtmax_V_s. Seeding therefore produces a
  population in which 940 models lack those three fields and 4060 have them.

  This does NOT affect the retention criteria or the frozen population file:
  both use only status, CL_ms and OS_mV (plus MDP_mV/APA_mV for storage).
  It DOES mean DDR100_mV_s and dVdtmax_V_s must not be analysed across the
  whole population unless the 940 are re-run.

  If uniform biomarkers across all 5000 are wanted, do NOT seed - run all
  5000 fresh (about 12 h more). Both routes give identical values for the
  four biomarkers that the analysis actually uses.

Running WITHOUT this step is equally valid. Use whichever you prefer.

It writes ONLY to zhou_san_run/results.jsonl and touches nothing else.
"""
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "outputs", "step3fix_run_statefix.json")
WORK = os.path.join(ROOT, "zhou_san_run")
RESULTS = os.path.join(WORK, "results.jsonl")

REQUIRED = ("index", "status", "CL_ms", "OS_mV", "MDP_mV", "APA_mV")
# carried when present: preserves the historical beat count and per-model
# wall-clock time so the seeded records are as complete as the source allows.
OPTIONAL = ("n_beats", "seconds")

with open(HIST, encoding="utf-8") as f:
    hist = json.load(f)

recs = hist["results"]
assert hist["cellml_sha256"].lower() == \
    "9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec", \
    "historical run used a different CellML; refusing to seed"

bad = [r["index"] for r in recs if not all(k in r for k in REQUIRED)]
if bad:
    raise SystemExit(f"FATAL: {len(bad)} historical records missing required "
                     f"fields; refusing to seed")

if os.path.exists(RESULTS) and os.path.getsize(RESULTS) > 0:
    bak = RESULTS + ".bak"
    shutil.copyfile(RESULTS, bak)
    print(f"existing checkpoint backed up -> {bak}")

os.makedirs(WORK, exist_ok=True)
with open(RESULTS, "w", encoding="utf-8") as f:
    for r in sorted(recs, key=lambda x: x["index"]):
        rec = {k: r[k] for k in REQUIRED if k in r}
        rec.update({k: r[k] for k in OPTIONAL if k in r})
        rec["seeded_from"] = "step3fix"
        f.write(json.dumps(rec) + "\n")

idx = sorted(r["index"] for r in recs)
print(f"seeded {len(recs)} records into {RESULTS}")
print(f"  index range      : {idx[0]}-{idx[-1]} (contiguous: "
      f"{idx == list(range(len(idx)))})")
print(f"  status counts    : "
      f"{ {s: sum(1 for r in recs if r['status'] == s) for s in {x['status'] for x in recs}} }")
print(f"  fields carried   : {REQUIRED + OPTIONAL}")
print("  fields NOT in history (present only on the 4060 new models): "
      "('CL_ms_sd', 'DDR100_mV_s', 'dVdtmax_V_s')")
print(f"  remaining to run : {5000 - len(recs)}")
print()
print("Now launch with --resume; the seeded models will be skipped.")
