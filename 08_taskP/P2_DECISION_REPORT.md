# P2 — decisive full-population anchor experiment: decision report

Completed 2026-08-24. Simulation: `08_taskP/P2_anchor_experiment.py` (imports the frozen
`04_pharmacology/taskL_anchor_switch.py` `_job`/`_init` verbatim). Analysis:
`08_taskP/P2_analyse.py` (frozen `taskG_analyse` endpoint definitions). Raw:
`08_taskP/p2/P2_checkpoint.jsonl` (32,896 records), `08_taskP/p2/P2_results.json`.

**Population verified before execution:**

| item | value |
|---|---|
| population file | `population_retained_20260823T094616Z.npz` |
| population SHA256 | `f52879d3db435b198cc68f2dcff51fb498209bde949a248d5ae98d738ebf59be` |
| manifest SHA256 | `c3eb465fc8ca88a111322ee611d32154bff163abaf64847add4ab4e2f5a88516` |
| npz hash vs manifest | **match** (recomputed at run time) |
| models used | **1028 — all retained, no subsampling** |
| state | control only |
| completeness | 1028/1028 models with complete 32-condition sets, 0 duplicates |
| denominator | **1028** — all retained models pace drug-free at control |

---

## 1. Clinical-anchor mappings (frozen)

| anchor | effective model-equivalent I_f block (1×) | frozen source |
|---|---|---|
| Doesch 2007 (PRIMARY) | **0.5840** | `taskL_anchor_switch.NEW_BF[0]` |
| 10-year cohort | **0.5090** | `taskL_anchor_switch.NEW_BF[3]` |
| 36-month (superseded) | **0.3120** | `taskG_analyse.B_IVAB` |

All three read programmatically from the frozen calibration stage. No re-calibration, no
re-fitting, no Hill or exposure-mapping change. Verapamil rungs are
`taskL_anchor_switch.VER` filtered to the 480 mg/day band (10.8–30.0%), giving the seven
frozen rungs **0.108, 0.140, 0.150, 0.200, 0.250, 0.275, 0.300** — the 27.5% rung included,
nothing added, nothing interpolated.

---

## 2. Rung-level EMQF, single-agent quiescence, and ceiling headroom

Control state, ivabradine 1×, denominator 1028, Wilson 95%.

### Doesch 2007 (PRIMARY), I_f = 0.5840

| b_CaL | ver alone | ivab alone | combo | EMQF k | EMQF % | 95% CI | eligible | max poss. EMQF | obs/max |
|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 26 (2.5%) | 25 (2.4%) | 83 (8.1%) | 45 | 4.38% | [3.29, 5.81] | 990 | 96.3% | 0.045 |
| 0.140 | 54 (5.3%) | 25 (2.4%) | 116 (11.3%) | 51 | 4.96% | [3.79, 6.46] | 963 | 93.7% | 0.053 |
| 0.150 | 57 (5.5%) | 25 (2.4%) | 127 (12.4%) | 59 | 5.74% | [4.48, 7.33] | 960 | 93.4% | 0.061 |
| 0.200 | 104 (10.1%) | 25 (2.4%) | 198 (19.3%) | 87 | 8.46% | [6.91, 10.32] | 917 | 89.2% | 0.095 |
| 0.250 | 168 (16.3%) | 25 (2.4%) | 284 (27.6%) | 111 | 10.80% | [9.04, 12.84] | 855 | 83.2% | 0.130 |
| **0.275** | 215 (20.9%) | 25 (2.4%) | 333 (32.4%) | **116** | **11.28%** | [9.49, 13.36] | 811 | 78.9% | 0.143 |
| 0.300 | 278 (27.0%) | 25 (2.4%) | 386 (37.5%) | 106 | 10.31% | [8.60, 12.32] | 748 | 72.8% | 0.142 |

### 10-year cohort, I_f = 0.5090

| b_CaL | ver alone | ivab alone | combo | EMQF k | EMQF % | 95% CI | eligible | max poss. EMQF | obs/max |
|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 26 (2.5%) | 20 (1.9%) | 70 (6.8%) | 35 | 3.40% | [2.46, 4.70] | 993 | 96.6% | 0.035 |
| 0.140 | 54 (5.3%) | 20 (1.9%) | 100 (9.7%) | 37 | 3.60% | [2.62, 4.92] | 965 | 93.9% | 0.038 |
| 0.150 | 57 (5.5%) | 20 (1.9%) | 108 (10.5%) | 42 | 4.09% | [3.04, 5.48] | 962 | 93.6% | 0.044 |
| 0.200 | 104 (10.1%) | 20 (1.9%) | 182 (17.7%) | 73 | 7.10% | [5.69, 8.84] | 919 | 89.4% | 0.079 |
| 0.250 | 168 (16.3%) | 20 (1.9%) | 269 (26.2%) | 98 | 9.53% | [7.89, 11.48] | 857 | 83.4% | 0.114 |
| **0.275** | 215 (20.9%) | 20 (1.9%) | 318 (30.9%) | **103** | **10.02%** | [8.33, 12.01] | 813 | 79.1% | 0.127 |
| 0.300 | 278 (27.0%) | 20 (1.9%) | 371 (36.1%) | 93 | 9.05% | [7.44, 10.96] | 750 | 73.0% | 0.124 |

### 36-month (superseded), I_f = 0.3120

| b_CaL | ver alone | ivab alone | combo | EMQF k | EMQF % | 95% CI | eligible | max poss. EMQF | obs/max |
|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 26 (2.5%) | 6 (0.6%) | 46 (4.5%) | 20 | 1.95% | [1.26, 2.99] | 1002 | 97.5% | 0.020 |
| 0.140 | 54 (5.3%) | 6 (0.6%) | 75 (7.3%) | 21 | 2.04% | [1.34, 3.10] | 974 | 94.7% | 0.022 |
| 0.150 | 57 (5.5%) | 6 (0.6%) | 81 (7.9%) | 24 | 2.33% | [1.57, 3.45] | 971 | 94.5% | 0.025 |
| 0.200 | 104 (10.1%) | 6 (0.6%) | 145 (14.1%) | 41 | 3.99% | [2.95, 5.37] | 924 | 89.9% | 0.044 |
| 0.250 | 168 (16.3%) | 6 (0.6%) | 219 (21.3%) | 51 | 4.96% | [3.79, 6.46] | 860 | 83.7% | 0.059 |
| **0.275** | 215 (20.9%) | 6 (0.6%) | 274 (26.7%) | **59** | **5.74%** | [4.48, 7.33] | 813 | 79.1% | 0.073 |
| 0.300 | 278 (27.0%) | 6 (0.6%) | 336 (32.7%) | 58 | 5.64% | [4.39, 7.22] | 750 | 73.0% | 0.077 |

No rung omitted. No zero rungs occurred — every in-band rung × anchor produced a non-zero
EMQF.

---

## 3. Maximum EMQF within the band (simulated frozen rungs only)

| anchor | max EMQF | at rung | k / n | 95% CI | eligible | max possible | obs/max |
|---|---|---|---|---|---|---|---|
| Doesch 2007 (PRIMARY) | **11.28%** | 0.275 | 116 / 1028 | [9.49, 13.36] | 811 (78.9%) | 78.9% | **0.143** |
| 10-year cohort | **10.02%** | 0.275 | 103 / 1028 | [8.33, 12.01] | 813 (79.1%) | 79.1% | **0.127** |
| 36-month (superseded) | **5.74%** | 0.275 | 59 / 1028 | [4.48, 7.33] | 813 (79.1%) | 79.1% | **0.073** |

All three maxima fall at the same frozen rung, 0.275. No interpolation; no continuous
maximum estimated. Maxima are unique — no ties.

---

## 4. Single-agent quiescence

Reported in full in §2. Summary at the maximising rung (b_CaL = 0.275):

| condition | quiescent count | fraction |
|---|---|---|
| verapamil alone (0.275) | 215 | 20.9% |
| ivabradine alone, Doesch (0.5840) | 25 | 2.4% |
| ivabradine alone, 10-year (0.5090) | 20 | 1.9% |
| ivabradine alone, 36-month (0.3120) | 6 | 0.6% |
| combination, Doesch | 333 | 32.4% |
| combination, 10-year | 318 | 30.9% |
| combination, 36-month | 274 | 26.7% |

Verapamil-alone quiescence rises monotonically across the band, 2.5% → 27.0%. Ivabradine-alone
quiescence is constant within an anchor by construction (it does not depend on b_CaL) and
separates the anchors cleanly: 2.4% / 1.9% / 0.6%.

---

## 5. Ceiling headroom

Eligibility is computed **per model at each exact (rung, anchor) pair** — automatic under
verapamil alone AND automatic under ivabradine alone — not reconstructed from marginals.

At the maximising rung 0.275: eligible 811–813 of 1028 (**78.9–79.1%**), so the maximum
mathematically possible EMQF is ~79%.

| anchor | observed max EMQF | ceiling | headroom (ceiling − observed) | observed/ceiling |
|---|---|---|---|---|
| Doesch | 11.28% | 78.9% | **67.6 pp** | 0.143 |
| 10-year | 10.02% | 79.1% | **69.1 pp** | 0.127 |
| 36-month | 5.74% | 79.1% | **73.4 pp** | 0.073 |

**Verdict: all three anchors are FAR FROM THE CEILING.** The highest observed value uses
14.3% of its mathematically available range; the lowest uses 7.3%. Across the whole band the
observed/ceiling ratio never exceeds 0.143 for any anchor at any rung. Endpoint depletion
does **not** materially constrain any result reported here, and no observed difference
between anchors can be attributed to ceiling saturation.

---

## 6. Comparison with the historical 188-model analysis

Recomputed from the frozen `outputs/taskG_pair_checkpoint.jsonl` under identical definitions.
The historical triplet reproduces exactly: **16.0 / 12.8 / 6.9%**.

| | historical 188 | completed 1028 |
|---|---|---|
| Doesch max EMQF | **15.96%** at rung 0.275 | **11.28%** at rung 0.275 |
| 10-year max EMQF | **12.77%** at rung 0.275 | **10.02%** at rung 0.275 |
| 36-month max EMQF | **6.91%** at rung **0.300** | **5.74%** at rung **0.275** |

One structural change worth recording: the 36-month maximum sat at rung **0.300**
historically and sits at **0.275** in the completed population. The two candidate values are
5.74% (0.275) and 5.64% (0.300) — a 0.10 pp difference, far inside the interval, so the rung
shift is not itself meaningful. It matters only because the historical 6.9% figure came from
a different rung than the other two anchors' figures.

### Single-agent and ceiling comparison at rung 0.275

| quantity | historical 188 | completed 1028 |
|---|---|---|
| verapamil alone | 40 (21.3%) | 215 (20.9%) |
| ivabradine alone, Doesch | 5 (2.7%) | 25 (2.4%) |
| ivabradine alone, 10-year | 5 (2.7%) | 20 (1.9%) |
| ivabradine alone, 36-month | 1 (0.5%) | 6 (0.6%) |
| **eligible (ceiling)** | **148 (78.7%)** | **811–813 (78.9–79.1%)** |
| observed/ceiling, Doesch | 0.203 | 0.143 |

---

## 7. Did the change reflect altered anchor separation, altered ceiling limitation, or both?

**Altered anchor separation. Ceiling limitation is excluded as an explanation.**

The ceiling is essentially identical between the two populations: eligible fraction
**78.7%** historically versus **78.9–79.1%** in the completed population — a difference of
0.2–0.4 pp. Single-agent depletion is likewise unchanged: verapamil alone 21.3% → 20.9%,
ivabradine alone 2.7% → 2.4% (Doesch). **The denominator of available models was not
squeezed.** Both populations use roughly the same 79% of models eligible to show the paired
effect, and both use only a small fraction of that headroom.

What fell is the fraction of eligible models that actually fail on the combination:
observed/ceiling for Doesch drops from **0.203 → 0.143**. That is a real reduction in paired
combination susceptibility, not an artefact of endpoint exhaustion.

I am stating this in the direction the brief warns against invoking loosely: **the completed
population genuinely shows a smaller combination effect than the truncated subset did**, and
I am not using ceiling limitation to protect the historical numbers.

---

## 8. Central assessment — does anchor choice materially alter susceptibility?

**Yes. The qualitative claim survives, with materially different absolute values.**

Evaluated against each criterion the brief specifies:

**Ordering.** Doesch ≥ 10-year ≥ 36-month holds at **all seven** in-band rungs, without
exception.

| rung | Doesch | 10-year | 36-month |
|---|---|---|---|
| 0.108 | 4.38% | 3.40% | 1.95% |
| 0.140 | 4.96% | 3.60% | 2.04% |
| 0.150 | 5.74% | 4.09% | 2.33% |
| 0.200 | 8.46% | 7.10% | 3.99% |
| 0.250 | 10.80% | 9.53% | 4.96% |
| 0.275 | 11.28% | 10.02% | 5.74% |
| 0.300 | 10.31% | 9.05% | 5.64% |

**Absolute separation.** Primary minus superseded: **+5.54 pp** (historical +9.05 pp). The
separation shrank by about 40%.

**Relative separation.** Primary/superseded: **1.97×** (historical 2.31×). The primary anchor
still produces roughly twice the susceptibility of the superseded one.

**Interval support.** Because all three anchors are evaluated on the *same* 1028 models, the
correct test is paired, not an independent-sample interval overlap. McNemar exact at the
maximising rung:

| comparison | discordant counts | McNemar exact p |
|---|---|---|
| Doesch vs 10-year | 17 vs 4 | **7.2 × 10⁻³** |
| Doesch vs 36-month | 59 vs 2 | **1.6 × 10⁻¹⁵** |
| 10-year vs 36-month | 44 vs 0 | **1.1 × 10⁻¹³** |

All three pairwise differences are supported. Note that the unpaired Wilson intervals for
Doesch [9.49, 13.36] and 10-year [8.33, 12.01] overlap substantially; the paired test is the
appropriate one here and it separates them, because the discordance is strongly one-sided
(17 vs 4). Reporting only the overlapping marginal intervals would understate the evidence,
and reporting only the paired p-value would overstate how *large* the Doesch-vs-10-year gap
is — it is 1.26 pp, the smallest of the three.

**Consistency across rungs.** The ordering is stable at every rung; the primary-vs-superseded
gap ranges from 2.43 pp (rung 0.108) to 5.54 pp (rung 0.275), growing with verapamil block.

**Ceiling robustness.** Established in §7 — obs/ceiling ≤ 0.143 everywhere, so no difference
depends on endpoint depletion.

### Statement of the result

Admissible open-loop calibration-anchor choice **does** materially alter downstream
verapamil–ivabradine susceptibility in the completed 1028-model population. The effect is
**weaker in absolute terms** than the historical subset indicated: the primary-versus-
superseded gap is 5.54 pp rather than 9.05 pp, and the maximum EMQF under the primary anchor
is 11.28% rather than 16.0%. The ordering, the direction, the ~2× relative separation, and
the paired statistical support all survive. The 36-month anchor's headline value is
essentially unchanged (6.9% → 5.74%); most of the shrinkage comes from the primary anchor
falling.

Nothing was tuned, refit, or re-selected. The historical triplet 16.0 / 12.8 / 6.9 was used
only as a comparison and is not reproduced — nor was reproduction attempted.

---

## 9. Measured P2 throughput

| quantity | value |
|---|---|
| total simulations | **32,896** (32 conditions × 1028 models) |
| workers | 8 |
| **measured throughput** | **1.1173 sims/s** |
| **CPU cost per simulation** | **7.16 s** |
| equivalent single-pass wall clock | **8.2 h** |
| actual elapsed | 8 launches (environment terminated 7); checkpoint clean throughout |

The rate was stable across the whole run (1.11–1.16 sims/s from the first 2,000 simulations
to the last). The final completed segment — 8,544 simulations in 7,646.9 s — is recorded in
`08_taskP/p2/P2_throughput.json` and is the basis used below.

---

## 10. Projected P3 runtime (estimates only — nothing drawn, nothing executed)

The historical Task-L1 dense grid is
`STATES(2) × NEW_BF(6) × VER(12)` = **144 conditions per model**
(`taskL_anchor_switch.main()`), covering both states, the Doesch and 10-year anchors at
1×/2×/3×, and all twelve verapamil rungs.

Basis: 1.1173 sims/s on 8 workers (7.16 s CPU per simulation), measured in P2 above.

| population | model-condition simulations | estimated wall clock |
|---|---|---|
| **1028 (full completed population)** | **148,032** | **36.8 h** |
| 500 | 72,000 | 17.9 h |
| 250 | 36,000 | 9.0 h |
| 188 | 27,072 | 6.7 h |

Assumptions stated explicitly: 8 workers on this machine; per-simulation cost independent of
block level and state (supported — P2's rate was flat across all 32 conditions); no
resume overhead. Given that this environment terminated 7 of 8 P2 launches, a full-population
P3 would need a durable terminal; at the observed ~2 h per surviving launch it would
otherwise take roughly 18 restarts.

**No subset was drawn. No dense grid was executed. These are projections only.**

---

## P2 MANDATORY STOP

P2 is complete and this report closes it. **Stopping here.**

- P3 **not started** — requires explicit authorization.
- P4 population **not generated**; seed 788156539 remains frozen and unused.
- No parameter, anchor, Hill value, exposure mapping, rung, or endpoint definition was
  modified at any point in P2.

### Carried forward from P1 (not to be re-derived or silently replaced)

1. The I_CaL median quiescence threshold moved 40% → 45% between the historical 188 and the
   completed 1028; this is one 5%-block grid step and at the design's resolution limit. The
   revised manuscript should lead with the full fixed-block quiescence curve and bounded
   between-population differences rather than the median.
2. The I_f conditional threshold median is poorly determined under heavy right-censoring
   (93.6% / 92.7% never quiescent to 90% block). The revised manuscript should lead with the
   fixed-block quiescence curve and the censoring fraction, not the conditional median.
3. P1 established only that the truncated subset happened to resemble the completed
   population on the threshold geometry relevant here. That does not make the truncated
   design defensible, and the manuscript must be rebuilt on the completed 1028-model
   population. **P2 now supplies a concrete instance of why: the headline EMQF triplet
   changes from 16.0 / 12.8 / 6.9 to 11.28 / 10.02 / 5.74.**
