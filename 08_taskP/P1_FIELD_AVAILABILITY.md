# P1 — ancillary field availability across the completed population

Recorded 2026-08-23, before P1 launch. **Route A (resume from the 940-model checkpoint) is
the adopted route.** This file is the permanent record of the resulting field coverage.

---

## 1. The coverage split

> **CORRECTION, 2026-08-23 (post-run).** The version of this section written before P1 ran
> was **wrong**, and in two ways. It claimed that `CL_ms_sd`, `DDR100_mV_s` and
> `dVdtmax_V_s` would be present for indices 940–4999 and absent for 0–939. Verified against
> the completed 5,000-record file, **neither half is true.** Corrected below. The practical
> conclusion — exclude them from full-population analyses — is unchanged, but the reason and
> the direction of the split were both misstated.

**What actually happens.** `biomarkers()` computes eight quantities, but `run_one()`
(`run_full_population.py:298-321`) copies only four of them into the record:

```python
rec.update(status="ok", CL_ms=b["CL_ms"], OS_mV=b["OS_mV"],
           MDP_mV=b["MDP_mV"], APA_mV=b["APA_mV"])
```

So `CL_ms_sd`, `DDR100_mV_s` and `dVdtmax_V_s` are **computed and then discarded, for every
model**. They appear in **none** of the 5,000 records — not in 0–939, and not in 940–4999.
There is no split in these three fields; they are uniformly absent.

The real split runs the opposite way, and in a different field:

| field | indices 0–939 (seeded) | indices 940–4999 (this run) |
|---|---|---|
| `index`, `status`, `CL_ms`, `OS_mV`, `MDP_mV`, `APA_mV`, `seconds` | present | present |
| **`n_beats`** | **present** (940) | **absent** — `run_one()` does not write it |
| `seeded_from: "step3fix"` | present (provenance marker) | absent |
| `CL_ms_sd`, `DDR100_mV_s`, `dVdtmax_V_s` | **absent** | **absent** |

Verified coverage across the completed file (`08_taskP/P1_verification.json`):
`APA_mV` 5000, `CL_ms` 5000, `MDP_mV` 5000, `OS_mV` 5000, `index` 5000, `seconds` 5000,
`status` 5000, `n_beats` **940**, `seeded_from` **940**.

The `seeded_from` key makes the two provenances distinguishable programmatically at any
later date — no record can be mistaken for the other kind.

**Consequence of the correction.** The standing rule in §4 still applies, but the backfill in
§5 is now understood differently: obtaining these three fields for the population requires
`run_one()` to be **extended to write them** and then the **whole 5,000** re-run — not merely
indices 0–939. That is a materially larger job than previously stated (≈29 h at the observed
speed, not ≈12 h), and it is a code change, so it must not be done inside P1/P2.

## 2. Why this does not affect P1 or P2

Confirmed by reading the code, not by assumption.

**Frozen retention** (`run_full_population.py:402-403`) uses only:

```python
kept = [r for r in recs if r["status"] == "ok"
        and BCL_MIN <= r["CL_ms"] <= BCL_MAX and r["OS_mV"] > 0]
```

— `status`, `CL_ms`, `OS_mV`. All present for all 5,000.

**The frozen population file** (`:417-424`) stores `model_index`, `scales`, `values`,
`names`, `variables`, `baseline`, `CL_ms`, `OS_mV`, `MDP_mV`, `APA_mV`. All present for all
5,000. **The `.npz` is therefore schema-homogeneous regardless of route** — the split exists
only in the intermediate `results.jsonl`.

**Threshold analysis / EMQF** operates on quiescence (loss of pacing) and cycle length —
`status` and `CL_ms`. All present for all 5,000.

**P2 (anchor dominance, ceiling-limit analysis)** consumes the retained population and the
quiescence endpoint. Same fields. All present.

## 3. Correction to my earlier risk note

In the execution package I flagged that "the manuscript does compare DDR100 and dV/dt
against Fabbri Table 5, so this is a live constraint." **That was overstated, and the
constraint is narrower than I described.**

A search of every `.py` in the project for the three field names returns consumers in only
these places, all of which are **single-baseline-model** contexts:

| consumer | what it reads |
|---|---|
| `01_baseline/biomarkers.py` | the definitions themselves |
| `01_baseline/run_baseline.py` | the one baseline model, vs Fabbri Table 5 |
| `05_manuscript/taskM_methods.py` | manifest keys `baseline.DDR100_mV_s.*`, `baseline.dVdtmax_V_s.*` |
| `05_manuscript/taskM_figures.py` (Figure 1) | `step1_baseline.json` → `b["comparison"][k]["pct"]` |
| `04_pharmacology/taskL2_verify_linder.py` | Linder reference values, unrelated to the population |

**There is no population-wide consumer of these three fields anywhere in the project.** The
Fabbri Table 5 comparison — including its DDR100 and (dV/dt)max rows, and Figure 1's left
panel — is a comparison of the *single baseline model* against the published table. It never
touches the 5,000-model population and is completely unaffected by this split.

So the practical impact of Route A is **nil for every analysis that currently exists.**

## 4. Standing rule

> `CL_ms_sd`, `DDR100_mV_s` and `dVdtmax_V_s` are ancillary. They are **excluded from all
> full-population analyses.** No population-level statistic, figure, table or manuscript
> claim may be computed from them while indices 0–939 lack them.

Any population-wide use of these fields is a protocol deviation unless the backfill in §5 has
been completed first.

## 5. Backfill procedure, if ever required

**Revised 2026-08-23 in light of the §1 correction.** Because the three fields are absent for
*all* 5,000 models — not just 0–939 — a backfill is no longer a partial job. It requires a
code change plus a full re-run, and is therefore a separate task that **must not be folded
into P1 or P2.**

1. Extend `run_one()` to copy `CL_ms_sd`, `DDR100_mV_s` and `dVdtmax_V_s` from the
   `biomarkers()` dict into `rec`. This is a **change to the runner**, so it invalidates the
   frozen `run_full_population.py` hash and must be version-recorded.
2. Re-run **all 5,000** models with unchanged config, unchanged LHS and unchanged criteria,
   writing to a **separate** file (e.g. `zhou_san_run/backfill_all.jsonl`). Do not write into
   `results.jsonl`.
3. Cost: 5,000 models at the observed 18.5 s/model mean CPU ÷ 8 workers ≈ **3.2 h**
   (the historical 47.24 s/model wall figure does not apply — see the runtime note in
   `P1_FREEZE_REPORT.md`).
3. **Verification gate before use:** for all 940, the recomputed `status`, `CL_ms`, `OS_mV`,
   `MDP_mV` and `APA_mV` must equal the checkpoint values bit-identically. The P1 gates
   already demonstrated this reproducibility (model 0 CL = 872.745454545455 under three
   different predecessors, matching history to < 1e-9), so a disagreement would indicate the
   environment or code has changed and must halt the backfill.
4. Only after that gate passes may the three ancillary fields be merged in and the standing
   rule in §4 lifted.
5. The backfill must not alter the frozen population file or retention — those are
   independent of these fields by construction (§2).

## 6. Disclosure wording for the manuscript, if these fields are ever reported

> Cycle-length standard deviation, DDR₁₀₀ and (dV/dt)max were recorded for models 940–4999
> only, because the first 940 models were simulated before those biomarkers were added to
> the per-model output. All population-level analyses reported here use cycle length,
> overshoot, maximum diastolic potential and action-potential amplitude, which were recorded
> for all 5000 models. The baseline comparison against Fabbri et al. Table 5 concerns the
> single baseline model and is unaffected.
