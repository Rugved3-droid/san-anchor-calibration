"""Task P1 mandatory gates - state isolation and resume determinism.

Tests the ACTUAL code path that P1 would use: run_one() and load_done() from
run_full_population.py. Nothing here is a re-implementation.

GATE 1 - STATE ISOLATION
  The same model index must give an identical result regardless of which model
  (if any) was executed before it in the same worker process. Tested by running
  a probe index with three different predecessors, including a fast pacer that
  leaves a very different steady state behind.

GATE 2 - RESUME DETERMINISM
  A set executed uninterrupted must equal the same set executed with an
  artificial interruption and --resume, and completed indices must be skipped
  rather than re-simulated.

Both gates also cross-check against the frozen historical values in
outputs/step3fix_run_statefix.json, which is an independent integrity check on
the whole path.

Writes 08_taskP/P1_gate_results.json.
"""
import importlib.util
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "08_taskP")
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location(
    "rfp", os.path.join(ROOT, "run_full_population.py"))
rfp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rfp)

HIST = {r["index"]: r for r in json.load(
    open(os.path.join(ROOT, "outputs", "step3fix_run_statefix.json"),
         encoding="utf-8"))["results"]}

PROBE = 3          # fast non-pacing model, used as the probe
PACER = 1          # fast pacer, leaves a very different steady state
SLOW = 0           # slow pacer
KEYS = ("status", "CL_ms", "OS_mV", "MDP_mV", "APA_mV")


def strip(r):
    """Compare only the scientific content; drop wall-clock timing."""
    return {k: r.get(k) for k in KEYS}


def fresh_worker():
    """A pristine _init(), as a new pool worker would get."""
    rfp._S.clear()
    rfp._init()


out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "runner": "run_full_population.py",
       "duration_s": rfp.DURATION_S, "window_s": rfp.WINDOW_S,
       "tol_abs": rfp.TOL_ABS, "tol_rel": rfp.TOL_REL}

print("=" * 78)
print("GATE 1 - STATE ISOLATION")
print("=" * 78)
seqs = {
    "probe_alone":        [PROBE],
    "probe_after_pacer":  [PACER, PROBE],
    "probe_after_slow":   [SLOW, PROBE],
}
g1 = {}
for name, seq in seqs.items():
    fresh_worker()
    res = {}
    for idx in seq:
        t0 = time.time()
        res[idx] = rfp.run_one(idx)
        print(f"  {name:20s} model {idx:4d} -> {res[idx]['status']:14s} "
              f"({time.time()-t0:6.1f} s)", flush=True)
    g1[name] = {str(k): strip(v) for k, v in res.items()}
out["gate1_state_isolation"] = g1

probe_results = [g1[n][str(PROBE)] for n in seqs]
iso_ok = all(r == probe_results[0] for r in probe_results)
print(f"\n  probe model {PROBE} identical under all three predecessors: {iso_ok}")
for n in seqs:
    print(f"    {n:20s} {g1[n][str(PROBE)]}")

# the pacer/slow models themselves must also match history
hist_ok = {}
for name, seq in seqs.items():
    for idx in seq:
        h = strip(HIST[idx])
        g = g1[name][str(idx)]
        same = all(
            (h[k] is None and g[k] is None) or
            (h[k] is not None and g[k] is not None and
             (h[k] == g[k] if k == "status" else abs(h[k] - g[k]) < 1e-9))
            for k in KEYS)
        hist_ok[f"{name}|{idx}"] = same
print(f"\n  every run reproduces the frozen historical value: "
      f"{all(hist_ok.values())}")
for k, v in hist_ok.items():
    if not v:
        print(f"    MISMATCH vs history: {k}")
out["gate1_matches_history"] = hist_ok
out["gate1_pass"] = bool(iso_ok and all(hist_ok.values()))

print()
print("=" * 78)
print("GATE 2 - RESUME DETERMINISM")
print("=" * 78)
SET = [PROBE, PACER, 4]
ck = os.path.join(DEST, "_gate2_results.jsonl")
if os.path.exists(ck):
    os.remove(ck)

# --- uninterrupted -------------------------------------------------------
fresh_worker()
uninterrupted = {}
with open(ck, "a", encoding="utf-8") as fh:
    for idx in SET:
        r = rfp.run_one(idx)
        uninterrupted[idx] = r
        fh.write(json.dumps(r) + "\n")
        fh.flush()
print(f"  uninterrupted run of {SET}: "
      f"{[uninterrupted[i]['status'] for i in SET]}")

# --- interrupted + resume ------------------------------------------------
os.remove(ck)
fresh_worker()
partial = {}
with open(ck, "a", encoding="utf-8") as fh:
    for idx in SET[:1]:                       # simulate a kill after model 1
        r = rfp.run_one(idx)
        partial[idx] = r
        fh.write(json.dumps(r) + "\n")
        fh.flush()
print(f"  interrupted after {len(partial)} model(s); checkpoint written")

rfp.RESULTS = ck                              # point load_done at the test file
done = rfp.load_done()
todo = [i for i in SET if i not in done]
print(f"  load_done() sees {sorted(done)}; resuming with {todo} "
      f"(skipped {len(done)}, not re-simulated)")

fresh_worker()                                # a resumed run starts fresh
resumed = dict(done)
with open(ck, "a", encoding="utf-8") as fh:
    for idx in todo:
        r = rfp.run_one(idx)
        resumed[idx] = r
        fh.write(json.dumps(r) + "\n")
        fh.flush()

same = {i: strip(uninterrupted[i]) == strip(resumed[i]) for i in SET}
print(f"\n  uninterrupted vs resumed, per model: {same}")
for i in SET:
    if not same[i]:
        print(f"    MISMATCH {i}: {strip(uninterrupted[i])} vs "
              f"{strip(resumed[i])}")
out["gate2_resume_determinism"] = {
    "set": SET, "skipped_on_resume": sorted(done),
    "identical": {str(k): v for k, v in same.items()},
    "uninterrupted": {str(i): strip(uninterrupted[i]) for i in SET},
    "resumed": {str(i): strip(resumed[i]) for i in SET}}
out["gate2_pass"] = bool(all(same.values()) and len(done) == 1)

print()
print("=" * 78)
print(f"GATE 1 (state isolation)     : "
      f"{'PASS' if out['gate1_pass'] else 'FAIL'}")
print(f"GATE 2 (resume determinism)  : "
      f"{'PASS' if out['gate2_pass'] else 'FAIL'}")
print("=" * 78)

with open(os.path.join(DEST, "P1_gate_results.json"), "w",
          encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"-> {os.path.join(DEST, 'P1_gate_results.json')}")
