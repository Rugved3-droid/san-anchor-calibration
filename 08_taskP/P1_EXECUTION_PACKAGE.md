# P1 — durable external execution package

Prepared 2026-08-23. **P1 is NOT launched.** Everything below is verification and
instructions for running it outside this environment.

---

## 1. Environment verified

| item | value | verdict |
|---|---|---|
| Python | 3.12.10 | matches the environment the gates passed under |
| Myokit | 1.39.2 | — |
| NumPy | 2.4.2 | — |
| logical CPUs | 8 | supports `--workers 8`, the historical configuration |
| solver | CVODE, `tol_abs` / `tol_rel` = 1e-8 / 1e-8 | as config |

The historical 940-model run used 8 workers on this same 8-CPU machine and achieved a
parallel efficiency of ≈1.03 workers-equivalent per worker, i.e. it was already CPU-saturated.
**Use `--workers 8`** — it reproduces the historical timing basis exactly. Going higher will
not help; going lower only lengthens the run.

## 2. Disk space verified

| drive | used | **free** |
|---|---|---|
| C: | 157.78 GB | **79.32 GB** |
| D: (project) | 72.47 GB | **859.02 GB** |

**Projected P1 storage requirement: 3.70 MiB total**, itemised:

| item | size |
|---|---|
| `results.jsonl` (940 seeded + 4060 new) | 1,163 KiB |
| `lhs_sample.npz` (5000 × 12, already present) | 894 KiB |
| `fabbri_2017.cellml` + `.mmt` (already present) | 230 KiB |
| `population_retained_<stamp>.npz` (≈21% retained) | 221 KiB |
| `population_manifest_<stamp>.json` | 6 KiB |
| Myokit compile temp (8 workers × ≈160 KiB) | 1,280 KiB |
| **total** | **≈3.7 MiB** |

Record sizes were measured, not guessed: the seeded records are 199 B each; a full runner
record is 289 B for `ok` and 191 B for `no_pacing`, and the historical status split is
539 ok / 401 no_pacing (57.3% ok).

**Storage is a non-issue — the requirement is under 4 MiB against 859 GB free.** Crucially,
the earlier disk crisis was on **C:**, and it broke the *tooling*, not the science. The runner
already redirects its own temp away from C: — `run_full_population.py:61-66` and `:279-281`
set `TMPDIR`/`TEMP`/`TMP` and `tempfile.tempdir` to `D:\zhou-san\zhou_san_run\tmp` in both the
parent and every pool worker, so Myokit's per-worker C compilation never touches C:. Running
outside this assistant session removes the remaining C: exposure entirely.

## 3. Paths verified

All resolved relative to `run_full_population.py`'s own location — the script is
position-independent as long as `00_config/config.yaml` sits beside it.

| constant | resolved path | exists |
|---|---|---|
| `WORK` | `D:\zhou-san\zhou_san_run` | yes |
| `CONFIG` | `D:\zhou-san\00_config\config.yaml` | yes |
| `CELLML` | `D:\zhou-san\zhou_san_run\fabbri_2017.cellml` | yes, 215,043 B |
| `MMT` | `D:\zhou-san\zhou_san_run\fabbri_2017.mmt` | yes, 20,363 B |
| `SAMPLE` | `D:\zhou-san\zhou_san_run\lhs_sample.npz` | yes, 915,695 B |
| `RESULTS` | `D:\zhou-san\zhou_san_run\results.jsonl` | yes, 187,040 B, 940 records |

Outputs written at completion: `population_retained_<UTC stamp>.npz` and
`population_manifest_<UTC stamp>.json`, both into `WORK`. Timestamped, so **a re-run cannot
overwrite a previous freeze.**

## 4. Configuration and model hashes

| file | SHA256 |
|---|---|
| `00_config/config.yaml` | `37c1dac662daf22d94ff0bdd6973fb56cf7599ad93d15cd2832affe19cc031d4` |
| `zhou_san_run/fabbri_2017.cellml` | `9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec` |

The CellML hash **matches the value recorded in `config.yaml`, in the frozen historical run
`outputs/step3fix_run_statefix.json`, and in the manuscript.** The runner re-checks it at
startup and aborts with `FATAL: CellML checksum mismatch` on any disagreement
(`run_full_population.py:176-180`); it also aborts if the cached LHS sample disagrees with
config (`:269`). Neither guard can be bypassed by a flag.

Record `37c1dac6…` now: if `config.yaml` is edited before P1 finishes, the run is no longer
the pre-specified one.

## 5. Checkpoint state verified

```
load_done() sees: 940 | remaining: 4060
contiguous 0-939: True
status: 539 ok / 401 no_pacing
```

The checkpoint was re-seeded today to carry `n_beats` and `seconds` in addition to the six
required fields, so the seeded records now match the historical source in full. Previous
checkpoint preserved at `results.jsonl.bak`.

### Finding — record-schema heterogeneity on the resume path

The historical records carry `index, status, CL_ms, OS_mV, MDP_mV, APA_mV, n_beats, seconds`.
The current `run_one()` additionally returns **`CL_ms_sd`, `DDR100_mV_s`, `dVdtmax_V_s`**
(`run_full_population.py:151-156`). Seeding therefore yields a population where 940 models
lack those three fields and 4,060 have them.

- **No effect on the population file or retention.** Retention uses only `status`, `CL_ms`
  and `OS_mV`; the frozen `.npz` stores only `CL_ms`, `OS_mV`, `MDP_mV`, `APA_mV`. All four
  are present for all 5,000.
- **`DDR100_mV_s` and `dVdtmax_V_s` are excluded from population-wide analysis** on the
  resume path.

**DECISION (2026-08-23): Route A — resume — is adopted. Route B is withdrawn.**

I had recommended Route B and flagged that "the manuscript already compares DDR100 and dV/dt
against Fabbri Table 5, so this is a live constraint." **That was overstated.** A search of
every `.py` for the three field names shows every consumer is a *single-baseline-model*
context (`01_baseline/run_baseline.py`, the `baseline.*` manifest keys in
`taskM_methods.py`, and Figure 1's left panel, which reads `step1_baseline.json` →
`b["comparison"]`). **No population-wide consumer of these fields exists anywhere in the
project.** The Fabbri Table 5 comparison concerns the one baseline model and is untouched by
the split. The practical impact of Route A on every analysis that currently exists is nil.

The frozen `.npz` is schema-homogeneous under either route — it stores only the four
biomarkers common to all 5,000 — so the split lives solely in the intermediate
`results.jsonl`, and the `seeded_from` marker keeps the two provenances distinguishable
forever.

Full record and the standing exclusion rule: **`08_taskP/P1_FIELD_AVAILABILITY.md`**, which
also specifies the separate additive backfill (≈12.3 h for indices 0–939, into its own file,
behind a bit-identity gate) should those fields ever be needed population-wide.

## 6. Runtime projection

Measured from the historical run (same procedure, same solver settings, same 8 workers):
940 models in 44,406 s wall = **47.24 s/model**.

| route | simulations | projected wall clock |
|---|---|---|
| **A — resume from the seeded checkpoint** | 4,060 | **191,796 s ≈ 53.3 h ≈ 2.2 days** |
| **B — all 5,000 fresh (recommended)** | 5,000 | **236,203 s ≈ 65.6 h ≈ 2.7 days** |

Note the runner's own inline ETA (`len(todo)*26/workers/3600`) assumes 26 s/model and will
**under-estimate by about 45%**. Trust the 47.24 s/model figure above; the printed ETA
becomes accurate once it is measured from actual progress.

---

## 7. Launch commands

Run from `D:\zhou-san` in a terminal that survives disconnection — **not** inside an
assistant session.

### THE COMMAND — Route A, resume from the 940-model checkpoint

Run this and nothing else. 4,060 models, ≈53.3 h.

```powershell
cd D:\zhou-san
python run_full_population.py --workers 8 --resume | Tee-Object -FilePath 08_taskP\P1_run.log
```

### Resume after any interruption

**The identical command.** Safe to repeat as many times as needed; completed indices are
skipped, never re-simulated. `Tee-Object` truncates the log on each invocation — use
`-Append` on re-launches if you want to keep the earlier log:

```powershell
cd D:\zhou-san
python run_full_population.py --workers 8 --resume | Tee-Object -FilePath 08_taskP\P1_run.log -Append
```

*(Route B — all 5,000 fresh — was considered and is **withdrawn**; see §5.)*

### Optional flags

- `--skip-baseline` skips the Fabbri Table 5 reproduction gate at startup. **Do not use it
  on the first launch** — that gate is the run's integrity check. It is reasonable on a
  resume, where it saves a few minutes.
- `--n` defaults to 5000. Do not change it.

### Notes for the operator

- Every completed model is written and `flush()`ed immediately, so an interruption costs at
  most one model.
- Progress prints every 25 models with elapsed time and ETA.
- Expect ≈57% `ok` / ≈43% `no_pacing`; `no_pacing` models finish in under a second, so
  throughput is bursty. This is normal and matches the historical run.
- On completion the runner prints the retained count and the frozen file's SHA256, and
  compares retention against the Zhou reference (1046/5000 = 20.92%).
- Do not edit `00_config/config.yaml` while the run is in flight.

## 8. What to hand back for P2

- `zhou_san_run/results.jsonl` (5,000 records)
- `zhou_san_run/population_retained_<stamp>.npz` and `population_manifest_<stamp>.json`
- `08_taskP/P1_run.log`
- which route was used (A or B)

P2 analysis is a pure read of those files and takes minutes.

---

## Status

| gate | status |
|---|---|
| free disk space verified | **DONE** — C: 79.32 GB, D: 859.02 GB free |
| storage requirement projected | **DONE** — 3.70 MiB, measured not estimated |
| checkpoint path verified | **DONE** — 940 records, contiguous, `load_done()` confirms |
| output paths verified | **DONE** — timestamped, no overwrite risk |
| config hash verified | **DONE** — `37c1dac6…`; CellML `9062dd65…` matches config and history |
| launch / resume commands | **DONE** — section 7 |
| route decision | **Route A (resume) adopted**; Route B withdrawn |
| ancillary-field record | **DONE** — `P1_FIELD_AVAILABILITY.md`, standing exclusion rule |
| **P1 execution** | **NOT LAUNCHED HERE — to be launched in the durable terminal** |
| P2 / P3 / P4 | **BLOCKED until P1 completes** |

---

## 9. Pre-launch integrity baseline (2026-08-23, read-only)

Recorded immediately before handover. Nothing was altered to produce it. If any of these
changes before P1 completes, the run is no longer the pre-specified one and must be treated
as void.

| file | SHA256 |
|---|---|
| `zhou_san_run/results.jsonl` (940 records, 187,040 B) | `e3508a17b6febb15c04b14fc7a4c01298bc6418a7203653b80b972661c887aaf` |
| `00_config/config.yaml` | `37c1dac662daf22d94ff0bdd6973fb56cf7599ad93d15cd2832affe19cc031d4` |
| `zhou_san_run/fabbri_2017.cellml` | `9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec` |
| `zhou_san_run/fabbri_2017.mmt` | `e93963bbb82c1d7852db1357bef36cf03332dd085455eb8f7c61bbc97c94974d` |
| `zhou_san_run/lhs_sample.npz` | `f6867756c3589bacc6457351ff15af3e48664f09e176035a96ea68fdb9d7b238` |
| `outputs/step2_lhs_sample.npz` (frozen) | `f6867756c3589bacc6457351ff15af3e48664f09e176035a96ea68fdb9d7b238` |
| `run_full_population.py` | `9d56b3f847e3f0423203bb78c91a3c33e53b806eb148c5c1a9b42808523c4cd3` |

The runner's LHS copy is **byte-identical** to the frozen sample — same SHA256, not merely
array-equal. Shape (5000, 12), `np.array_equal` True on both `scales` and `values`.

Checkpoint state at handover, read-only via `load_done()`:

```
load_done()      : 940
contiguous 0-939 : True
remaining        : 4060
status split     : {'ok': 539, 'no_pacing': 401}
fields present   : index, status, CL_ms, OS_mV, MDP_mV, APA_mV, n_beats, seconds, seeded_from  (940 each)
```

`results.jsonl` last modified 2026-08-23 00:55 — the P0-era re-seed. **No write has touched
it since**, and none was made under this instruction. `results.jsonl.bak` retains the prior
six-field version.
