"""P3 Option B - commit the 500-model subset BEFORE any dense-grid output exists.

Seed derivation is deterministic and documented, exactly as the P4 seed was:

    seed = int(SHA256("TASK_P3_SUBSET_500_OF_1028_V1")[:8], 16) mod (2**31 - 1)

Selection is a uniform random draw without replacement from the SORTED list of
the 1028 P1-retained model indices. It therefore depends only on:
  * the frozen P1 retained index list, and
  * the committed seed.

It does NOT depend on phenotype, cycle length, threshold, drug response, or any
outcome - none of those quantities is read by this script. The historical
contiguous 940-row prefix plays no role: the draw is over all 1028 retained
models and the prefix/non-prefix composition is REPORTED afterwards, never
imposed.

Writes 08_taskP/P3_SUBSET_COMMITMENT.json and appends a p3_subset block to
00_config/config.yaml. Refuses to overwrite an existing commitment.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NPZ = os.path.join(ROOT, "zhou_san_run",
                   "population_retained_20260823T094616Z.npz")
CFG = os.path.join(ROOT, "00_config", "config.yaml")
OUT = os.path.join(ROOT, "08_taskP", "P3_SUBSET_COMMITMENT.json")
NPY = os.path.join(ROOT, "08_taskP", "P3_subset_500.json")

CONST = "TASK_P3_SUBSET_500_OF_1028_V1"
SIZE = 500

if os.path.exists(OUT):
    raise SystemExit(f"REFUSING: {OUT} already exists. A subset commitment "
                     f"must never be redrawn.")


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


digest = hashlib.sha256(CONST.encode("utf-8")).hexdigest()
seed = int(digest[:8], 16) % (2 ** 31 - 1)

z = np.load(NPZ, allow_pickle=True)
pool = sorted(int(i) for i in z["model_index"])
assert len(pool) == 1028, f"expected 1028 retained, got {len(pool)}"

rng = np.random.default_rng(seed)
subset = sorted(int(x) for x in rng.choice(np.array(pool), size=SIZE,
                                           replace=False))
assert len(set(subset)) == SIZE

subset_sha = hashlib.sha256(
    json.dumps(subset, separators=(",", ":")).encode("utf-8")).hexdigest()

n_prefix = sum(1 for i in subset if i < 940)
commit = {
    "purpose": "P3 Option B dense-grid subset: 500 models drawn from the "
               "1028-model P1 retained population.",
    "committed_before": "any P3 dense-grid output existed",
    "derivation_procedure": [
        f"1. Fixed constant string: {CONST}",
        "2. digest = SHA256(constant, UTF-8) hex",
        "3. take the first 8 hex characters",
        "4. seed = int(those 8 hex chars, 16) mod (2**31 - 1)",
        "5. subset = numpy default_rng(seed).choice(sorted retained indices, "
        "500, replace=False), then sorted",
    ],
    "constant_string": CONST,
    "sha256_full": digest,
    "first8_hex": digest[:8],
    "P3_SUBSET_SEED": seed,
    "subset_size": SIZE,
    "source_population": os.path.basename(NPZ),
    "source_population_sha256": sha256_file(NPZ),
    "source_n": len(pool),
    "subset_sha256": subset_sha,
    "selection_independence": (
        "Uniform random draw over the sorted retained-index list. No "
        "phenotype, cycle length, threshold, drug response or outcome value "
        "is read by the selection procedure."),
    "prefix_note": (
        f"{n_prefix} of {SIZE} drawn models have index < 940 (the historical "
        f"contiguous prefix). Expected under uniform sampling: "
        f"{SIZE*188/1028:.1f}. The prefix was NOT used as a selection "
        f"criterion; this count is reported, not imposed."),
    "committed_utc": datetime.now(timezone.utc).isoformat(),
    "immutability": "This seed and subset MUST NOT be redrawn on the basis of "
                    "any dense-grid result.",
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(commit, f, indent=2)
with open(NPY, "w", encoding="utf-8") as f:
    json.dump(subset, f, separators=(",", ":"))

cfg_before = sha256_file(CFG)
block = f"""
# ---------------------------------------------------------------------------
# P3 Option B dense-grid subset - committed {commit['committed_utc']}
# BEFORE any dense-grid output existed. Must not be redrawn.
# ---------------------------------------------------------------------------
p3_subset:
  size: {SIZE}
  source_population: {os.path.basename(NPZ)}
  source_population_sha256: {commit['source_population_sha256']}
  source_n: {len(pool)}
  seed_constant_string: {CONST}
  seed_sha256: {digest}
  seed: {seed}
  subset_sha256: {subset_sha}
  subset_file: 08_taskP/P3_subset_500.json
  selection: uniform random without replacement over sorted retained indices
  selection_independent_of_outcome: true
  historical_940_prefix_used: false
  commitment_file: 08_taskP/P3_SUBSET_COMMITMENT.json
  immutable: true
"""
with open(CFG, "a", encoding="utf-8") as f:
    f.write(block)
cfg_after = sha256_file(CFG)

print("=" * 70)
print("P3 SUBSET COMMITMENT")
print("=" * 70)
print(f"  constant string   : {CONST}")
print(f"  SHA256            : {digest}")
print(f"  first 8 hex       : {digest[:8]}")
print(f"  P3 SUBSET SEED    : {seed}")
print(f"  subset size       : {SIZE} of {len(pool)}")
print(f"  subset sha256     : {subset_sha}")
print(f"  source population : {os.path.basename(NPZ)}")
print(f"  source sha256     : {commit['source_population_sha256']}")
print(f"  index range       : {subset[0]} .. {subset[-1]}")
print(f"  from historical prefix (<940): {n_prefix}  "
      f"(expected {SIZE*188/1028:.1f} under uniform sampling)")
print(f"  config.yaml sha256 before : {cfg_before}")
print(f"  config.yaml sha256 after  : {cfg_after}")
print(f"  commitment file sha256    : {sha256_file(OUT)}")
print("=" * 70)
