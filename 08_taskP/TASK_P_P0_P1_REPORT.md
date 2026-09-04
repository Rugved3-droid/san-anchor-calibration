# Task P — P4 seed commitment, P0 provenance audit, P1 gates, and P1 execution decision

All Task-P outputs are namespaced under `D:\zhou-san\08_taskP\`. No existing project file,
frozen output, figure or manuscript has been modified, deleted or renamed.

**Bottom line: P0 passes without blocking P1. Both P1 gates pass, including a strengthened
version. The P1 population run is NOT started, because it requires ~53 h of wall clock in an
environment that has demonstrably killed long-lived jobs and filled its system disk
mid-session. Per the brief's own instruction, the runner is verified, the exact command is
given, and execution stops here rather than fabricating a run that would die.**

---

# Pre-P1 — P4 seed commitment (done before any P1 work)

Committed before any P1 simulation existed, by a documented deterministic procedure.

| item | value |
|---|---|
| constant string | `TASK_P_P4_INDEPENDENT_LHS_V1` |
| procedure | `seed = int(SHA256(constant)[:8], 16) mod (2**31 − 1)` |
| SHA256 | `2efa507b9164d2890a3a4b1c3e4f8f6eb9ec3eb77df801d04caac7b872018f43` |
| first 8 hex | `2efa507b` |
| **P4 seed** | **788156539** |
| committed (UTC) | 2026-08-23T03:44:57Z |
| file | `08_taskP/P4_SEED_COMMITMENT.json` |
| file SHA256 | `bfd8ed625f966c5001ba89c955bcb9b3a18401a4f7b240174dfa24a05739d69b` |

The P4 population has **not** been generated. This seed must not be changed on the basis of
P1/P2/P3 results.

---

# P0 — provenance and terminology (no simulation)

## P0.1 — Verapamil exposure provenance

**The premise in the brief is half right.** The values are not attributed to refs 3/4; they
are attributed to nothing at all. Methods 2.6 says only "taken from the regulatory label",
in a manuscript whose only label references are the two ivabradine documents. So the reader
is left to infer an ivabradine source for a verapamil quantity.

Traced through: `04_pharmacology/taskH_analyse.py` docstring → `outputs/_sim0/Drug_Audit.csv`
(verapamil PK URL points at DailyMed verapamil, not an ivabradine document) → the verapamil
FDA label itself, which I re-verified verbatim.

| band | value | dose / formulation | context | total vs free | supported? |
|---|---|---|---|---|---|
| 480 mg/day | **125–400 ng/mL** | 120 mg every 6 h, **immediate release** | chronic oral, steady state | total plasma | **YES, verbatim** |
| 240 mg/day lower edge | **35 ng/mL** | 240 mg **extended release**, once daily, **with food** | AUC(0–24 h) 841 ng·h/mL ÷ 24 | total plasma | **DERIVED, not reported** |
| 240 mg/day upper edge | **164 ng/mL** | 240 mg extended release, **fasting** | peak concentration | total plasma | **YES, verbatim** |

Source: *Verapamil Hydrochloride Extended-Release Tablets USP*, CLINICAL PHARMACOLOGY;
DailyMed setid `d1a0aa24-0f81-498a-8c25-5095b2bb8f57`, label revision 6/2010. Verbatim:
"Chronic oral administration of 120 mg of verapamil hydrochloride every 6 hours resulted in
plasma levels of verapamil ranging from 125 to 400 ng/mL"; "peak plasma verapamil
concentrations of 79 ng/mL … AUC(0-24hr) of 841 ng-hr/mL" (with food); "peak plasma
verapamil concentration was 164 ng/mL … AUC(0-24hr) was 1,478 ng-hr/mL" (fasting).

**Two previously undisclosed heterogeneities inside the bands:**

1. **Formulation mismatch between bands.** 480 mg/day is immediate-release q6h; 240 mg/day
   is extended-release once daily. The manuscript presents them as a single "chronic oral"
   series.
2. **Prandial mismatch within the 240 mg/day band.** Its lower edge is a *fed*
   AUC-derived time-average; its upper edge is a *fasting* peak. The fed peak (79 ng/mL) and
   the fasting time-average (1478/24 = 61.6 ng/mL) both sit inside the band, so the band is
   wider than any single prandial state would give.

Verdict: **values fully supported; the manuscript statement is PARTIALLY SUPPORTED** —
correct numbers, absent citation, and an undisclosed construction. Proposed correction D1.

## P0.2 — Numerical-citation forensic audit

Full table: `08_taskP/P0_citation_audit.csv` (17 claims).

**Same class of problem found in two further places:**

- **Ivabradine 30% unbound** — used in the 12.2 nM derivation, cited nowhere.
- **Verapamil 10.4% unbound** — supported by ref 13 but the reference appears two sentences
  later against a different number.

**One potential input error checked and cleared.** The 12.2 nM anchor depends on which
molecular weight is used. Ivabradine is dosed as the hydrochloride (505.05) but the free
base is 468.59; the project uses 468.6. I verified from Choi 2013 that the assay measured
"levels of ivabradine … by validated LC-MS/MS", i.e. the base. **The free-base MW is
correct.** Had the salt mass been appropriate, the anchor would have been 11.3 nM rather
than 12.2 nM and every downstream ivabradine quantity would have shifted.

Everything else — Bucchi 2.0 µM, Doesch heart rates, Keefe binding, Nawrath ratio, Crumb
fit, Fabbri Table 5, Zhou retention, SmPC 2–3× and −5 bpm — verified as correctly
attributed.

**Unresolved at first pass, now CLOSED (2026-08-23):** the ivabradine Hill slope 0.80. See
the addendum at the end of this report — the full text was obtained and it *is* reported,
in Results rather than the abstract.

**Remaining gap:** ivabradine 30% unbound (citation only, value not in dispute). Carried forward.

## P0.3 — Effective model-equivalent block terminology

Four locations identified where an I_f block fraction is inferred from a clinical open-loop
observation, plus a new Methods statement. Deliberately **not** applied to the Bucchi
channel measurements or to the direct model-perturbation ladders in Results 3.2 / Figure 2,
which are not clinical inferences. Full diff: `08_taskP/P0_proposed_manuscript_diff.md`.

## P0 gate

**P0 does not trigger the STOP-before-P1 condition.** Every quantity that enters a
simulation was verified correct. The defects are citation and wording only. No candidate
correction changes a simulation input, so P1 inputs are unchanged and P1 may proceed.

**No manuscript file was modified.** All corrections exist only as a candidate diff.

---

# P1 — gates

## Runner verification

`run_full_population.py` (448 lines) is the project's self-contained resumable runner. It:
verifies the CellML SHA256 against config and refuses to run on a mismatch; runs the Fabbri
Table 5 baseline gate and halts on failure; regenerates and validates the LHS sample against
config; appends one JSON record per model and `flush()`es immediately; and supports
`--resume` via `load_done()`, which tolerates a torn final line.

**Sample identity verified:** the runner's regenerated sample is **bit-identical** to the
frozen `outputs/step2_lhs_sample.npz` (`np.array_equal` True on both `scales` and `values`,
seed 20260816). CellML SHA256 confirmed `9062dd65…b2aa1ec`. So "use the existing frozen
5000 × 12 sample" is satisfied in substance, not merely by copying a file.

## Gate 1 — state isolation

Tested on the actual `run_one()` code path, not a re-implementation.

*First pass* — probe model 3 run with three different predecessors (none, a fast pacer, a
slow pacer): identical in all three. But model 3 is non-pacing, so the comparison is
`None == None`, which is a weak test. **I therefore ran a strengthened version.**

*Strengthened* — probe model **0 (pacing)** with three different predecessors:

| predecessor | model 0 CL (ms) | model 0 OS (mV) |
|---|---|---|
| none | 872.745454545455 | 28.639068290653 |
| model 1 (pacer) | 872.745454545455 | 28.639068290653 |
| model 2 (pacer) | 872.745454545455 | 28.639068290653 |

**Bit-identical to twelve decimal places**, and matching the frozen historical value
(872.7454545454547) to < 1 × 10⁻⁹. Every model executed during the gates reproduced its
frozen historical record. **GATE 1: PASS.**

## Gate 2 — resume determinism

Set [3, 1, 4] executed uninterrupted, then re-executed with an artificial interruption after
the first model and a `--resume`-equivalent restart:

- `load_done()` saw the completed index and skipped it — **not re-simulated**;
- uninterrupted vs resumed results identical for all three models.

**GATE 2: PASS.**

Artifacts: `08_taskP/P1_gate_results.json`, `08_taskP/P1_gate1_strengthened.json`.

---

# P1 — execution decision: STOP

## Measured runtime basis

From the frozen historical run (`step3fix_run_statefix.json`), which used the same
procedure, same solver settings, same 8 workers:

| quantity | value |
|---|---|
| models | 940 |
| wall clock | 44,406 s = **12.34 h** |
| summed CPU | 365,686 s = 101.6 h (parallel efficiency ≈ 1.03 of 8 workers) |
| **wall clock per model** | **47.24 s** |
| pacing models (n = 539) | mean 677.9 s CPU |
| non-pacing (n = 401) | mean 0.8 s CPU |

Single-threaded timings measured during the gates (model 1: 43.6 s; model 0: 15.6 s) are
consistent with the recorded per-model CPU once 8-way contention is removed, so the
wall-clock-per-model figure is the correct basis for projection.

| scenario | simulations | projected wall clock |
|---|---|---|
| remaining 4060 (resume from seeded checkpoint) | 4,060 | **191,796 s = 53.3 h = 2.22 days** |
| all 5000 from scratch | 5,000 | 236,203 s = 65.6 h = 2.73 days |

## Why this is not launched

The brief is explicit: *"Do not rely on fragile background execution inside an environment
known to terminate long-lived jobs … STOP rather than launching a process expected to be
killed. Do not fabricate completion."*

This environment is known to terminate long-lived jobs, from this project's own record:

- the original 940-model run was split into seven chunks **precisely because** the full 5000
  was not viable here — that is the documented origin of the 940 prefix;
- background jobs have been killed mid-run in this project before;
- the system drive filled to zero mid-session during Task L, taking both shell tools offline
  until space was freed.

A 53-hour job in that environment would not complete, and a partial run reported as complete
would be exactly the failure mode the brief forbids. **P1 is therefore prepared and
verified, but not executed.**

## Ready-to-run state

The runner's working directory is prepared and its checkpoint seeded with the 940 models
already simulated under the state-isolated procedure. Seeding is legitimate here **because
the gates proved the runner reproduces those exact values bit-identically** — this is not an
assumption. Verified: `load_done()` reports 940 complete, 4060 remaining.

```
# from D:\zhou-san
# (already done) seed the checkpoint with the verified historical 940:
python 08_taskP\seed_checkpoint_from_history.py

# LAUNCH — run to completion, resumable, ~53 h on 8 workers:
python run_full_population.py --workers 8 --resume

# RESUME after any interruption — identical command, safe to repeat:
python run_full_population.py --workers 8 --resume

# To run all 5000 from scratch instead (~66 h), delete the checkpoint first:
del zhou_san_run\results.jsonl
python run_full_population.py --workers 8
```

Run this in a terminal that survives disconnection (not inside an assistant session).
Progress and ETA print to stdout; every completed model is flushed to
`zhou_san_run/results.jsonl` immediately, so an interruption costs at most one model.

**Recommendation:** run it overnight across two to three days on the workstation, or on any
machine with ≥ 8 cores; `run_full_population.py` is single-file and needs only
`00_config/config.yaml` beside it. Free disk on C: first — Myokit's temp is redirected to
the project drive, but the earlier zero-space event still broke tooling.

## What P1 will produce when run

`zhou_san_run/results.jsonl` (5000 records) plus the runner's own frozen population file and
manifest. The P1 analysis — population accounting, baseline phenotype, both
quiescence-threshold distributions, and the prefix-representativeness comparison against the
historical 188 — is then a pure read of those outputs and takes minutes, not hours.

---

# Status against the Task-P gates

| gate | status |
|---|---|
| P4 seed committed before P1 | **DONE** — 788156539, procedure and hash recorded |
| P0.1 verapamil provenance | **DONE** — values verified, citation defect and band heterogeneity documented |
| P0.2 citation audit | **DONE** — 17 claims; 2 uncited, 1 partially linked, 1 unresolved (Hill 0.80) |
| P0.3 terminology | **DONE** — candidate diff prepared, not applied |
| P0 STOP condition | **NOT triggered** — no simulation input is wrong |
| P1 state isolation | **PASS** (strengthened with a pacing probe) |
| P1 resume determinism | **PASS** |
| P1 runner verified | **PASS** — sample bit-identical, checksums confirmed |
| P1 population run | **NOT STARTED — stopped by design; command supplied** |
| P2 | blocked on P1 |
| P3 | not authorized (requires explicit authorization after P2) |
| P4 | seed committed, population not generated |

## Files created (all new, nothing overwritten)

```
08_taskP/P4_SEED_COMMITMENT.json          P4 seed, derivation, timestamp
08_taskP/P4_SEED_COMMITMENT.sha256        its checksum
08_taskP/P0_citation_audit.csv            17-claim citation audit
08_taskP/P0_proposed_manuscript_diff.md   candidate corrections (NOT applied)
08_taskP/P1_gates.py                      gate harness
08_taskP/P1_gate_results.json             gate 1 + gate 2 results
08_taskP/P1_gate1_strengthened.json       pacing-probe state-isolation result
08_taskP/seed_checkpoint_from_history.py  optional checkpoint seeding
08_taskP/TASK_P_P0_P1_REPORT.md           this report
zhou_san_run/                             runner workdir, checkpoint seeded (940)
```

---

# ADDENDUM — 2026-08-23

## A1. P0 CLOSED — Bucchi Hill factor verified from the full text

The last open P0 item is resolved. Bucchi 2006 full text retrieved (PMC1779671); the Hill
factor **is** reported, in Results — not in the abstract, which is why the earlier
abstract-only check could not confirm it.

Verbatim, Results, "Ivabradine blocks HCN4 and HCN1 channels", Fig. 1C:

> "Fitting data points with the Hill equation resulted in half-block concentrations of 2.0
> and 0.94 uM and slope coefficients of 0.8 and 1.2 for HCN4 (n = 23) and HCN1 (n = 27)
> channels, respectively."

hHCN4: half-block 2.0 uM, **Hill factor 0.8**, n = 23, HEK 293, -100 mV / 1.8 s activating
step from -35 mV holding. Two independent retrievals agreed on every number, differing only
in rendering the phrase as "Hill factors" versus "slope coefficients"; the paper's discussion
calls it a Hill slope.

**The 0.80 is therefore correct, correctly attributed to ref 15, and FITTED rather than
assumed.** The contingency wording drafted earlier ("state that 0.80 is a project-adopted
slope") is withdrawn as unnecessary. The Hill-shape assumption carried into the 2x and 3x
arms is about extrapolating a measured curve past its anchor, not about the slope value --
which is what the manuscript already says.

Recorded in `P0_citation_audit.csv` (row now YES) and `P0_proposed_manuscript_diff.md` (D5).

## A2. Exposure-language diff revised (D1)

The 240 mg/day interval is now described as a **constructed label-derived exposure envelope**
rather than a regulatory concentration range, with formulation and feeding state explicit at
each bound: lower bound = fed AUC(0-24 h) 841 ng*h/mL / 24 h = 35 ng/mL (extended-release);
upper bound = fasted peak 164 ng/mL (extended-release). The 480 mg/day interval remains
described as what it is -- a label-reported measured range, on immediate-release 120 mg q6h.
The revision also states the envelope's role: a plausible-exposure bracket, not an observed
distribution, with nothing interpolated within it.

**No numerical value changed and no simulation input was altered.** The block ladder is
computed at fixed block fractions and inverted to concentration exactly, so the envelope is
used only to say whether a threshold falls inside or outside it.

## A3. P1 prepared for durable external execution

Full package: **`08_taskP/P1_EXECUTION_PACKAGE.md`**. Summary:

- disk free: C: 79.32 GB, D: 859.02 GB. Projected P1 footprint **3.70 MiB** (measured record
  sizes, not estimates). Storage is a non-issue; the runner already redirects TMPDIR/TEMP/TMP
  to D: in parent and workers, so Myokit compilation never touches C:.
- config `00_config/config.yaml` sha256 `37c1dac662daf22d94ff0bdd6973fb56cf7599ad93d15cd2832affe19cc031d4`;
  CellML sha256 `9062dd65...b2aa1ec`, matching config, the frozen historical run, and the
  manuscript. Runner aborts on any mismatch and the guard cannot be flag-bypassed.
- checkpoint verified: `load_done()` = 940, contiguous 0-939, 539 ok / 401 no_pacing,
  4060 remaining. Re-seeded today to also carry `n_beats` and `seconds`.
- outputs are UTC-timestamped, so no re-run can overwrite a previous freeze.
- **New finding:** on the resume path 940 models will lack `CL_ms_sd`, `DDR100_mV_s` and
  `dVdtmax_V_s`, which `run_one()` now returns. Retention and the frozen population file are
  unaffected (they use only the four common biomarkers), but DDR100 and dV/dt cannot be
  analysed population-wide -- and the manuscript does compare both against Fabbri Table 5.
  **Recommended route: run all 5000 fresh (65.6 h) rather than resume (53.3 h)**, for a
  homogeneous record set.

Launch, from `D:\zhou-san`, in a terminal that survives disconnection:

    python run_full_population.py --workers 8                 # Route B, all 5000 fresh
    python run_full_population.py --workers 8 --resume        # Route A, or resume either route

**P1 was not launched.** P2, P3 and P4 remain blocked.

---

# ADDENDUM 2 — 2026-08-23, route decision and P1 handover

**P0 accepted and closed. Task-P design not reopened.**

## B1. Route A (resume) adopted; Route B withdrawn

P1 proceeds by resuming from the validated 940-model checkpoint: 4,060 models remaining,
projected 53.3 h at the measured 47.24 s/model on 8 workers.

## B2. Correction to my Route-B recommendation

I had recommended running all 5,000 fresh, on the grounds that "the manuscript already
compares DDR100 and dV/dt against Fabbri Table 5, so this is a live constraint."
**That was overstated.**

A search of every .py in the project for `CL_ms_sd`, `DDR100_mV_s` and `dVdtmax_V_s` returns
consumers only in single-baseline-model contexts: `01_baseline/biomarkers.py` (definitions),
`01_baseline/run_baseline.py` (the one baseline model vs Fabbri Table 5), the `baseline.*`
manifest keys in `05_manuscript/taskM_methods.py`, Figure 1's left panel in
`taskM_figures.py` (which reads `step1_baseline.json` -> `b["comparison"]`), and
`04_pharmacology/taskL2_verify_linder.py` (Linder reference values, unrelated to the
population).

**No population-wide consumer of these three fields exists anywhere in the project.** The
Fabbri Table 5 comparison concerns the single baseline model and is untouched by the record
split. The practical impact of Route A on every analysis that currently exists is nil.

Also relevant: the frozen population `.npz` stores only `CL_ms`, `OS_mV`, `MDP_mV`, `APA_mV`
alongside the sample arrays, so **it is schema-homogeneous under either route.** The split
lives solely in the intermediate `results.jsonl`, where the `seeded_from: "step3fix"` marker
keeps the two provenances distinguishable permanently.

## B3. Field absence documented

`08_taskP/P1_FIELD_AVAILABILITY.md` records the coverage split, the code-level demonstration
that retention, threshold analysis, P1 and P2 are unaffected, the standing rule excluding the
three fields from all full-population analyses, a separate additive backfill procedure
(indices 0-939, ~12.3 h, into its own file, behind a bit-identity gate) should they ever be
needed population-wide, and disclosure wording for the manuscript.

## B4. Nothing altered

Checkpoint, config, LHS, model, retention criteria and analysis definitions are all
unchanged. Pre-launch integrity baseline recorded read-only in
`08_taskP/P1_EXECUTION_PACKAGE.md` section 9:

    results.jsonl        e3508a17b6febb15c04b14fc7a4c01298bc6418a7203653b80b972661c887aaf
    config.yaml          37c1dac662daf22d94ff0bdd6973fb56cf7599ad93d15cd2832affe19cc031d4
    fabbri_2017.cellml   9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec
    lhs_sample.npz       f6867756c3589bacc6457351ff15af3e48664f09e176035a96ea68fdb9d7b238
    run_full_population  9d56b3f847e3f0423203bb78c91a3c33e53b806eb148c5c1a9b42808523c4cd3

The runner's LHS copy is byte-identical to the frozen `outputs/step2_lhs_sample.npz` (same
SHA256, not merely array-equal). Checkpoint verified read-only: 940 records, contiguous
0-939, 539 ok / 401 no_pacing, 4060 remaining.

## B5. Launch

P1 is **not** launched from this session. To be run in the durable terminal:

    cd D:\zhou-san
    python run_full_population.py --workers 8 --resume | Tee-Object -FilePath 08_taskP\P1_run.log

The identical command resumes after any interruption. P2, P3 and P4 remain blocked until P1
completes.
