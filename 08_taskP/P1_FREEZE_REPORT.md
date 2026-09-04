# P1 — freeze verification, forensic check, and representativeness of the historical 188

Completed 2026-08-23. Verification script: `08_taskP/P1_verify_population.py`;
machine-readable results: `08_taskP/P1_verification.json`, `P1_rate_comparison.json`.

**Status: the population is frozen and verified. The forensic check PASSES. Intrinsic-rate
representativeness is reported below. The threshold-geometry comparison is NOT yet complete —
it requires simulation that is still running (§7).**

---

## 1. The frozen population

| item | value |
|---|---|
| population file | `zhou_san_run/population_retained_20260823T094616Z.npz` |
| population SHA256 | `f52879d3db435b198cc68f2dcff51fb498209bde949a248d5ae98d738ebf59be` |
| manifest | `zhou_san_run/population_manifest_20260823T094616Z.json` |
| frozen (UTC) | 2026-08-23T09:46:16.543626+00:00 |
| simulated | **5000** |
| no pacing | 2280 (45.6%) |
| solver failures | **0** (0.0%) |
| **retained** | **1028 / 5000 = 20.56%** |
| Zhou 2019 reference | 1046 / 5000 = 20.92% |
| criteria | 600.0 ≤ CL ≤ 1000.0 ms, overshoot > 0, 1000 s duration |
| seed | 20260816, scale range [0, 2] |
| CellML SHA256 | `9062dd65…b2aa1ec` |

Retention lands 0.36 percentage points below Zhou's reference — an 18-model difference on
5,000. That is the validation, reported as it came out; nothing was tuned toward it.

## 2. Integrity — every check passed

| check | result |
|---|---|
| records in `results.jsonl` | 5000, **0 duplicates**, contiguous 0–4999 |
| status | 2720 ok / 2280 no_pacing / 0 solver_failure |
| seeded block is exactly 0–939 | **yes** |
| fresh block is exactly 940–4999 | **yes** |
| seeded records still equal history exactly | **yes, 0 mismatches** across all 940 |
| retention re-derived independently from `results.jsonl` | **1028**, matches manifest |
| npz SHA256 vs manifest | **match** |
| npz index set vs recomputed retained set | **identical** |
| npz biomarkers vs `results.jsonl` | identical for CL, OS, MDP, APA |
| npz `scales`/`values` vs frozen LHS rows | **identical** |
| all retained CL within [600, 1000] | **yes** |
| all retained OS > 0 | **yes** |

The npz is internally consistent, consistent with the record file, and consistent with the
frozen Latin-hypercube sample. Nothing in the freeze had to be taken on trust.

## 3. Live determinism re-check

Five models were re-simulated **after** the run, in the current environment, and compared
with their stored records:

| index | provenance | CL_ms re-run | CL_ms stored | identical |
|---|---|---|---|---|
| 940 | new | 446.2047619047619 | 446.2047619047619 | **yes** |
| 1500 | new | 667.45 | 667.45 | **yes** |
| 3777 | new | 405.0208333333333 | 405.0208333333333 | **yes** |
| 4999 | new | 2261.3333333333335 | 2261.3333333333335 | **yes** |
| 0 | historical anchor | 872.7454545454547 | 872.7454545454547 | **yes** |

Bit-identical in every case, spanning both provenances and both ends of the index range.

## 4. Runtime anomaly — investigated, benign

The run finished in **157 min**, against my pre-launch projection of 53.3 h. That is a 20×
discrepancy and it had to be explained before the population could be certified.

| | historical 940 | this run (940–4999) |
|---|---|---|
| mean CPU per pacing model | 677.9 s | **34.1 s** |
| mean CPU per non-pacing model | 0.79 s | 0.46 s |
| ratio | — | **19.9× faster** |

Same machine (`Windows-11-10.0.26200`, 8 CPUs, recorded in both run headers), same CellML
hash, same criteria, same solver tolerances, same `duration_s`.

**The new run is the normal one; the historical run was anomalously slow.** Two independent
lines of evidence:

1. The block sweep, which uses a 300 s pre-pace, takes ~8.8 s per level in *both* the old and
   the current environment. Scaling that to the population run's 994 s pre-pace predicts
   ≈29 s per pacing model — which matches this run's 34.1 s, not the historical 677.9 s.
2. Every re-run model reproduces its frozen value bit-identically (§3, and the earlier P1
   gates). Speed changed; arithmetic did not.

The historical run was executed under heavy contention (it is the same session in which the
system disk filled). **No numerical concern. My 53.3 h projection was extrapolated from that
degraded baseline and was simply wrong.**

## 5. Forensic check — the historical 188

> **Are the original 188 exactly the retained members among indices 0–939?**

| quantity | value |
|---|---|
| retained among indices 0–939 in the completed analysis | **188** |
| historical retained set, recomputed under the same criteria | **188** |
| **sets identical** | **YES** |
| in one but not the other | none, in either direction |
| retained among indices 940–4999 | 840 |

**Confirmed.** 188 + 840 = 1028. The historical population is exactly the retained prefix —
no member gained, none lost, no index reassigned.

## 6. Representativeness — intrinsic rate

**Statistical basis, stated because it governs everything here.** The 188 are a *subset* of
the 1028. A two-sample test between 188 and 1028 compares nested samples and its p-value is
uninterpretable. The valid comparison is **188 (retained in 0–939) vs 840 (retained in
940–4999)**, which are disjoint. That is the primary contrast; the pooled 1028 is reported
descriptively only.

Retention forces CL into [600, 1000] ms — i.e. rate into [60.0, 100.0] bpm — for both groups
by construction, so only the *shape* inside that interval can differ.

### Cycle length (ms)

| | historical 188 | new 840 | pooled 1028 |
|---|---|---|---|
| median | 729.885 | 736.138 | 735.900 |
| IQR | 667.852–856.975 | 663.641–835.016 | 666.416–837.776 |
| IQR width | 189.123 | 171.375 | 171.360 |
| mean ± SD | 759.792 ± 110.750 | 755.666 ± 107.792 | 756.421 ± 108.296 |
| range | 602.156–983.556 | 600.073–999.544 | 600.073–999.544 |
| 5th–95th | 613.366–955.752 | 613.444–952.565 | 613.294–953.629 |

### Intrinsic rate (bpm)

| | historical 188 | new 840 | pooled 1028 |
|---|---|---|---|
| median | 82.205 | 81.506 | 81.533 |
| IQR | 70.014–89.840 | 71.855–90.410 | 71.618–90.034 |
| mean ± SD | 80.584 ± 11.233 | 80.968 ± 11.102 | 80.898 ± 11.122 |
| range | 61.003–99.642 | 60.027–99.988 | 60.027–99.988 |
| 5th–95th | 62.778–97.821 | 62.988–97.808 | 62.918–97.832 |

### Disjoint comparison, 188 vs 840

| statistic | cycle length | rate |
|---|---|---|
| Kolmogorov–Smirnov D | 0.0525 (p = 0.768) | 0.0525 (p = 0.768) |
| Mann–Whitney p | 0.680 | 0.680 |
| median difference (hist − new) | **−6.254 ms** | **+0.698 bpm** |
| 95% CI (bootstrap, 10 000) | [−27.007, +23.884] ms | [−2.602, +3.030] bpm |
| 90% CI | [−23.867, +19.286] ms | [−2.094, +2.689] bpm |
| Cohen's d | +0.038 | −0.035 |

**These are not equivalence tests and must not be read as such.** No equivalence margin was
prespecified, and a non-significant KS or Mann–Whitney result is not evidence of sameness.
What the data support is a bounded statement: *the median rate difference between the
historical and the new retained models is estimated at +0.70 bpm, and the data are consistent
with a true difference anywhere in [−2.6, +3.0] bpm.* Whether that interval is narrow enough
matters only against a margin someone is willing to state in advance.

### Parameter space — the one signal worth naming

The 12 conductance scale factors, historical vs new, by KS:

| parameter | median hist | median new | KS D | p |
|---|---|---|---|---|
| **G_f** | **1.1387** | **0.9807** | **0.1114** | **0.0404** |
| G_Ks | 0.8702 | 1.0212 | 0.1042 | 0.0656 |
| G_CaL | 1.1534 | 1.2748 | 0.0993 | 0.0895 |
| G_Kr | 1.1992 | 1.2493 | 0.0987 | 0.0926 |
| P_Jup | 0.9317 | 1.0037 | 0.0956 | 0.1119 |
| G_Kur | 0.8611 | 0.9611 | 0.0901 | 0.1542 |
| G_CaT | 0.8522 | 0.9344 | 0.0706 | 0.4070 |
| G_Na | 1.0197 | 1.0103 | 0.0613 | 0.5852 |
| G_to | 0.9156 | 0.9848 | 0.0609 | 0.5946 |
| P_Jrel | 1.0890 | 1.0043 | 0.0523 | 0.7723 |
| G_NaCa | 1.1790 | 1.1288 | 0.0401 | 0.9560 |
| G_NaK | 0.9412 | 0.8926 | 0.0382 | 0.9707 |

One of twelve reaches uncorrected p < 0.05; 0.6 is what chance alone predicts, and nothing
survives Bonferroni (p < 0.00417). **On a purely statistical reading this is unremarkable.**

But the one that moved is **G_f**, and its direction is the concerning one: the historical
188 carry a *higher* median funny-current scale (1.139) than the new 840 (0.981), a 16%
relative shift. G_f is the single parameter that most directly governs I_f quiescence-threshold
geometry, so this is a **directed** concern rather than a random flag, and it cannot be waved
away by the multiplicity argument alone. If the historical 188 are enriched for high G_f, they
would be expected to resist I_f block *more* than the full population — which would make the
historical I_f thresholds biased high and the historical censoring fraction (176/188 never
quiescent to 90%) biased high as well.

**This is precisely what the threshold sweep in §7 will settle, and it is why the I_f arm of
that comparison cannot be skipped.** I am flagging it now rather than after the fact.

## 7. Threshold geometry — NOT YET COMPLETE

The I_CaL and I_f quiescence-threshold comparison requires simulating the block ladder for the
840 new retained models, under the frozen definitions.

**Definitions are reused, not restated.** `08_taskP/P1_threshold_sweep.py` imports
`04_pharmacology/population_block_sweep.py` and uses its `BLOCKS`, `PREPACE_S`, `WINDOW_S`,
`LOG_DT`, `_one()`, `run_model()` and `_pool_init()` verbatim. Echoed at run time:

```
BLOCKS    : 0.00..0.90 (19 levels, step 0.05)
PREPACE_S : 300.0
WINDOW_S  : 6.0
LOG_DT    : 0.0001
```

Only two things differ: which indices are fed in (the 1028 from the new npz rather than the
188 from the historical json), and where the checkpoint is written (`08_taskP/threshold/`, so
the frozen `outputs/taskA_*_checkpoint.jsonl` are never modified — they were copied in, not
edited).

**Reuse of the historical 188 sweep records is validated**, by the same standard applied to
the population: three of them were re-run under `--recheck` and reproduced not only the
threshold but the entire 19-level ladder identically —

```
   0  threshold 0.45 vs 0.45  levels identical: True
  10  threshold 0.55 vs 0.55  levels identical: True
  11  threshold 0.25 vs 0.25  levels identical: True
  ALL IDENTICAL: True
```

### Historical reference values (n = 188)

| | I_CaL (G_CaL) | I_f (G_f) |
|---|---|---|
| threshold median | 0.40 | 0.675 |
| range | 0.10–0.80 | 0.25–0.90 |
| never quiescent to 90% | 0 / 188 | **176 / 188 (93.6%)** |
| non-monotone | 0 | 0 |
| fraction pacing at 50% block | 0.250 | 0.979 |
| fraction pacing at 60% | 0.117 | 0.973 |
| fraction pacing at 70% | 0.016 | 0.957 |

The I_f distribution is **93.6% right-censored**: its median describes only the 12 models that
ever stop. The analysis in `P1_threshold_report.py` therefore reports conditional quantiles,
a Kaplan–Meier estimate that uses the censored models correctly, and a **log-rank** test for
the disjoint 188-vs-840 comparison — not a rank test on the uncensored subset. The primary
display is the quiescent-fraction-versus-block curve with Wilson intervals, which is
censoring-free and is what the prespecified Figure 2 already plots.

### I_CaL — COMPLETE (840 new models, 136.4 min)

> **Cost correction.** I earlier projected ≈5.5 h for I_CaL and ≈20 h in total, from an ETA
> printed after only 10 models. That early ETA was dominated by worker start-up and was
> wrong. I_CaL actually ran in **136.4 min**, matching the original estimate from the
> historical per-model cost. On the same basis I_f should take **≈6 h**, not 14, for a total
> nearer **8 h** than 20.

Sweep completed with **0 errors, 0 non-monotone models, 0 censored** across all 1028.

| | historical 188 | new 840 | pooled 1028 |
|---|---|---|---|
| threshold median | **0.40** | **0.45** | **0.45** |
| IQR | 0.30–0.5125 | 0.30–0.55 | 0.30–0.55 |
| range | 0.10–0.80 | 0.05–0.85 | 0.05–0.85 |
| Kaplan–Meier median | 0.40 | 0.45 | 0.45 |
| never quiescent to 90% | 0 / 188 | 0 / 840 | 0 / 1028 |
| non-monotone | 0 | 0 | 0 |

The historical median of 0.40 reproduces the frozen `taskA_G_CaL_population_sweep.json`
value exactly — an independent consistency check on the whole pipeline.

**Disjoint comparison, 188 vs 840:**

| test | result |
|---|---|
| log-rank (right-censored) | χ² = 1.669, **p = 0.196** |
| Kolmogorov–Smirnov | D = 0.0402, p = 0.955 |
| Mann–Whitney | p = 0.299 |
| median difference (hist − new) | **−0.05** (one grid step), 95% CI [−0.05, +0.05] |
| max quiescent-fraction difference, any level | **4.02 pp** (at 40% block) |

Quiescent fraction with Wilson 95% intervals, every level:

| block | hist % | hist 95% CI | new % | new 95% CI | diff (pp) |
|---|---|---|---|---|---|
| 0.10 | 1.1 | [0.3, 3.8] | 2.5 | [1.6, 3.8] | −1.44 |
| 0.20 | 10.1 | [6.6, 15.2] | 10.1 | [8.3, 12.3] | −0.01 |
| 0.25 | 19.1 | [14.2, 25.4] | 15.7 | [13.4, 18.3] | +3.43 |
| 0.30 | 28.2 | [22.2, 35.0] | 26.8 | [23.9, 29.9] | +1.41 |
| 0.35 | 42.0 | [35.2, 49.2] | 38.2 | [35.0, 41.5] | +3.81 |
| **0.40** | **53.2** | [46.1, 60.2] | **49.2** | [45.8, 52.5] | **+4.02** |
| 0.45 | 64.9 | [57.8, 71.4] | 61.3 | [58.0, 64.5] | +3.58 |
| 0.50 | 75.0 | [68.4, 80.6] | 72.7 | [69.6, 75.6] | +2.26 |
| 0.55 | 84.0 | [78.1, 88.6] | 80.4 | [77.5, 82.9] | +3.69 |
| 0.60 | 88.3 | [82.9, 92.1] | 87.1 | [84.7, 89.2] | +1.16 |
| 0.70 | 98.4 | [95.4, 99.5] | 96.4 | [94.9, 97.5] | +1.98 |
| 0.80 | 100.0 | [98.0, 100.0] | 99.8 | [99.1, 99.9] | +0.24 |

**Reading.** The two curves track each other across the whole ladder; the Wilson intervals
overlap at every one of the 19 levels; the largest gap anywhere is 4.0 pp. The historical 188
sit consistently ~2–4 pp *above* the new 840 in the mid-range, i.e. marginally more sensitive
to I_CaL block, and their median threshold is one grid step lower (0.40 vs 0.45).

Two caveats on that median shift. First, **the ladder resolves thresholds only to 5%**, and
the bootstrap CI for the median difference is [−0.05, +0.05] — exactly ±1 grid step, i.e. the
resolution floor. The shift is therefore at the limit of what this design can resolve, and no
finer statement is available without a finer grid. Second, this is not an equivalence result:
p = 0.196 is not evidence of sameness, and I am not offering it as such. What is supportable
is the bounded statement that the quiescent-fraction curves differ by at most ~4 pp anywhere
on the ladder.

**Manuscript-relevant:** any I_CaL threshold median quoted from the 188 as **0.40** becomes
**0.45** on the full population. That is a real change to a reported headline number, even
though it is one grid step.

### I_f — COMPLETE (840 new models, 0 errors, 0 non-monotone)

The sweep was killed twice by the environment mid-run and resumed from checkpoint both times
(626 → 733 → 840 new models). No model was lost or duplicated: the final checkpoint holds
1028 unique records with 0 duplicates and 0 failures. Total ~3.4 h across three launches.

| | historical 188 | new 840 | pooled 1028 |
|---|---|---|---|
| **never quiescent to 90%** | **176 (93.6%)** | **779 (92.7%)** | **955 (92.9%)** |
| uncensored n | **12** | **61** | 73 |
| conditional median | 0.675 | 0.700 | 0.700 |
| conditional IQR | 0.4375–0.7625 | 0.55–0.85 | 0.50–0.85 |
| range (uncensored) | 0.25–0.90 | 0.05–0.90 | 0.05–0.90 |
| Kaplan–Meier median | **undefined** | **undefined** | **undefined** |
| non-monotone | 0 | 0 | 0 |

The KM median is undefined in every group because survival never falls to 0.5 — fewer than
8% of models ever stop within the 0–90% ladder. **That is the dominant fact about the I_f
arm and it is a property of the biology, not a data problem.** The historical value carries
over unchanged.

**Disjoint comparison, 188 vs 840:**

| test | result |
|---|---|
| log-rank (right-censored) | χ² = 0.165, **p = 0.684** |
| censoring-fraction difference | **0.9 pp** (93.6% vs 92.7%) |
| max quiescent-fraction difference, any level | **0.88 pp** (at 90% block) |
| conditional median difference | −0.025, 95% CI **[−0.275, +0.100]** |
| KS on uncensored subset | D = 0.154, p = 0.937 |
| Mann–Whitney on uncensored subset | p = 0.455 |

Quiescent fraction with Wilson 95% intervals:

| block | hist % | hist 95% CI | new % | new 95% CI | diff (pp) |
|---|---|---|---|---|---|
| 0.40 | 1.6 | [0.5, 4.6] | 1.0 | [0.5, 1.9] | +0.64 |
| 0.50 | 2.1 | [0.8, 5.3] | 1.8 | [1.1, 2.9] | +0.34 |
| 0.60 | 2.7 | [1.1, 6.1] | 2.6 | [1.7, 3.9] | +0.04 |
| 0.70 | 4.3 | [2.2, 8.2] | 4.2 | [3.0, 5.7] | +0.09 |
| 0.80 | 5.3 | [2.9, 9.5] | 5.2 | [3.9, 7.0] | +0.08 |
| 0.90 | 6.4 | [3.7, 10.8] | 7.3 | [5.7, 9.2] | −0.88 |

**Reading.** The two curves are nearly coincident — the largest disagreement anywhere on the
ladder is 0.88 pp, and the Wilson intervals overlap heavily at every level. The censoring
fractions differ by 0.9 pp. Log-rank p = 0.684.

**The G_f concern flagged in §6 did not materialise.** The historical 188 carry a 16% higher
median G_f scale, which predicted they would resist I_f block *more* and show a *higher*
censoring fraction. They show 93.6% vs 92.7% — higher by 0.9 pp, in the predicted direction
but an order of magnitude too small to matter, and well inside sampling noise. The prediction
was worth testing and it came back negative.

**But note what is genuinely weak here, independent of representativeness.** The historical
conditional median of 0.675 rests on **12 uncensored models**. Its 95% CI against the new
data spans [−0.275, +0.100] — roughly ±5 grid steps. So while the two groups agree, the
historical I_f conditional median was never a well-determined quantity in the first place.
The full population improves it only to 73 uncensored models out of 1028. Any manuscript
statement resting on the I_f conditional median should carry that n explicitly; the
censoring fraction and the quiescent-fraction curve are the far better-supported quantities,
and the prespecified Figure 2 is already right to state the I_f median conditionally rather
than as a population band.

### Figure

`08_taskP/P1_threshold_geometry.png` / `.pdf` — prespecified Figure 2 layout, with the
historical 188 and new 840 overlaid, Wilson 95% bands on each, and the pooled 1028 dashed.
Rendered and inspected: no label collisions, both panels on the same 0–100% scale as the
prespecified figure. Panel B is visually compressed because fewer than 8% of models ever stop
— that compression is faithful to the data and is why the numeric table above matters more
than the panel.

```powershell
cd D:\zhou-san
python 08_taskP\P1_threshold_sweep.py --current G_CaL --workers 8
python 08_taskP\P1_threshold_sweep.py --current G_f   --workers 8
python 08_taskP\P1_threshold_report.py
```

Run these in a durable terminal, sequentially — running both sweeps at once contends for the
same 8 cores and saves nothing. `P1_threshold_report.py` produces
`08_taskP/P1_threshold_comparison.json` and the overlaid Figure-2-layout plot
`08_taskP/P1_threshold_geometry.png/.pdf`.

---

## 8. Representativeness verdict — with respect to threshold geometry

**Not yet determinable, and I will not assert it.**

- **Intrinsic rate: closely matched.** Medians differ by 0.70 bpm with a 95% CI of
  [−2.6, +3.0] bpm; KS D = 0.053. Stated as a bounded difference, not as equivalence.
- **Parameter space: one directed caveat.** G_f is shifted 16% lower in the new 840, at
  uncorrected p = 0.040. Statistically unremarkable among 12 tests; substantively pointed,
  because G_f is the parameter that drives I_f threshold geometry.
- **I_CaL threshold geometry: closely matched, with one reportable shift.** Curves overlap at
  every level (max gap 4.0 pp), log-rank p = 0.196, zero censoring in both groups. The median
  moves 0.40 → 0.45, one grid step and at the design's resolution floor. On this current the
  historical 188 behave like the full population.
- **I_f threshold geometry: matched, and more closely than I_CaL.** Censoring 93.6% vs 92.7%
  (0.9 pp), max curve difference 0.88 pp, log-rank p = 0.684. The G_f-enrichment prediction
  was tested and came back negative.

### Verdict

**With respect to threshold geometry, the historical 188 are representative of the completed
1028-model population, on both currents, within the resolution of this design.** The specific
supportable statements are:

| quantity | bound |
|---|---|
| I_CaL quiescent-fraction curve | differs by ≤ **4.02 pp** at any of 19 block levels |
| I_f quiescent-fraction curve | differs by ≤ **0.88 pp** at any of 19 block levels |
| I_f censoring fraction | differs by **0.9 pp** (93.6% vs 92.7%) |
| I_CaL threshold median | differs by **one grid step** (0.40 vs 0.45), at the 5% resolution floor |
| intrinsic rate median | differs by **+0.70 bpm**, 95% CI [−2.60, +3.03] |

**This is a bounded-difference verdict, not an equivalence claim, and the distinction is not
cosmetic.** Three of the four comparisons returned p > 0.19 (log-rank 0.196 and 0.684; KS
0.955 and 0.937), and none of those p-values is evidence of sameness — no equivalence margin
was prespecified, and with n = 188 the historical group has limited power to detect
moderate differences. What licenses the verdict is not the p-values but the **width of the
observed differences together with the Wilson intervals**: the curves are separated by at
most 4 pp (I_CaL) and 0.9 pp (I_f) with overlapping intervals at every level, which is a
direct statement about magnitude rather than an inference from non-rejection.

**Three caveats carried forward:**

1. The I_CaL median moves **0.40 → 0.45**. One grid step, but it is a reported number.
2. The I_f conditional median rests on **12 uncensored models** historically and 73 in the
   full population. It agrees between groups, but it was never well determined — its
   between-group CI spans ±5 grid steps.
3. All threshold statements are resolved only to **5% block**, the ladder step. No finer
   claim is available from this design.

## 9. Status

| item | status |
|---|---|
| population frozen and verified | **DONE** |
| forensic check: 188 = retained 0–939 | **PASS** |
| intrinsic-rate comparison | **DONE** |
| parameter-space comparison | **DONE** — G_f flagged |
| I_CaL threshold sweep (840 new) | **DONE** — 136.4 min, 0 errors |
| I_f threshold sweep (840 new) | **DONE** — ~3.4 h over 3 launches, 0 errors |
| threshold comparison + figure | **DONE** |
| representativeness verdict | **DONE** — representative on both currents, bounded |
| **this report** | **COMPLETE** |
| **P2** | **UNBLOCKED** — awaiting your go-ahead, not started |
