# P3 — dense Task-L1 grid on the pre-specified 500-model subset: decision report

Completed 2026-08-31. Scripts: `P3_subset_commit.py`, `P3_subset_characterise.py`,
`P3_dense_grid.py`, `P3_analyse.py`, `P3_analyse2.py`, `P3_manifest_figures.py`.
Raw: `08_taskP/p3/P3_dense_checkpoint.jsonl` (132,000 records).

---

## 1. Subset commitment — fixed before any dense-grid output existed

| item | value |
|---|---|
| constant string | `TASK_P3_SUBSET_500_OF_1028_V1` |
| SHA256 | `85b021e854bff12598b6b383b28c295066a96f934db6436535d824011f9cebaf` |
| **P3 subset seed** | **95429097** |
| **subset SHA256** | **`ffd4d347cd39ba3b5709c2a4434009d91b2657c19b4b3f38eb956e51c5cb76ba`** |
| size | 500 of 1028 |
| source | P1 retained population, `f52879d3…` |
| config.yaml | `37c1dac6…` → `e7574471…` (`p3_subset` block appended) |
| commitment file | `57b5994cff0e395060ce4307c24c2a3010825696c9ccdfcf80ce068c9ed2e0be` |

Uniform draw without replacement over the sorted retained-index list. The selection code
reads no phenotype, cycle length, threshold, drug response or outcome. **89 of 500 fall in
the historical <940 prefix against 91.4 expected** under uniform sampling — the prefix was
never a criterion; the count is reported, not imposed. The commit script refuses to overwrite
an existing commitment, and the grid runner re-verifies the subset hash on every launch.

## 2. Pre-grid characterisation

**Reported before the grid ran.** The 500 are nested in the 1028, so the valid test is
subset vs **complement (528)**, which is disjoint; subset-vs-full is descriptive only.

| | subset 500 | complement 528 | full 1028 |
|---|---|---|---|
| median CL | 724.299 ms | 747.410 ms | 735.900 ms |
| median rate | 82.839 bpm | 80.277 bpm | 81.533 bpm |
| IQR (CL) | 659.963–826.195 | 670.370–850.177 | 666.416–837.776 |

**⚠ The subset is faster than its complement.** Median CL difference **−23.111 ms, 95% CI
[−41.475, −3.392]**; rate +2.561 bpm, CI [+0.372, +4.557]; KS p = 0.044, MW p = 0.025. **The
interval excludes zero.** This is a genuine imbalance from an honest pre-committed draw.

**It was not redrawn.** Redrawing after inspection is precisely what the protocol forbids, and
the commitment is marked immutable. It is carried as a standing caveat on every P3 result
below: the subset runs ~2.6 bpm faster at the median than the models excluded from it, which
plausibly shifts EMQF slightly *downward* relative to the full population (faster models sit
further from the quiescence boundary).

**Threshold geometry, by contrast, is well matched:**

| current | largest \|subset − full\| | Wilson overlap | censoring (subset/full) | cond. median |
|---|---|---|---|---|
| I_CaL | **3.23 pp** (at 0.55) | 19/19 | 0% / 0% | 0.45 / 0.45 |
| I_f | **1.10 pp** (at 0.90) | 19/19 | 94.0% / 92.9% | 0.65 / 0.70 |

Bounded differences; no equivalence claimed from the overlap.

## 3. Grid executed

264 conditions × 500 models = **132,000 simulations**, 0 duplicates, all 500 models with
complete condition sets. Frozen `taskL_anchor_switch._job`, `PREPACE_S` 300, `WINDOW_S` 6,
`LOG_DT` 1e-4. Both states; the full 12-rung VER ladder; three anchors at 1×/2×/3×.

**Denominators (models pacing drug-free in that state, frozen definition):**
control **500/500**; iso **465/500** — 35 models do not pace drug-free under Iso 1 µM, a
property of the Iso state and not of any drug, and are excluded from the Iso analysis exactly
as the frozen definition requires.

*Flagged addition:* the 36-month **7× bounding arm** (0.6827) was simulated so Figure 3's
existing strong-inhibitor trace could be regenerated rather than dropped. It is **not** one of
the three specified PK arms, is labelled as such in the grid, and is **excluded from every
1×/2×/3× analysis in this report**. Say if you want it removed.

## 4. Rung-level results

Full table — EMQF with Wilson 95%, verapamil-alone, ivabradine-alone, combination, eligible
count, ceiling and observed/ceiling for all **198** anchor × arm × state × rung conditions —
is in `08_taskP/p3/P3_results_core.json`, and every value is reproduced in the manifest.

Representative slice (Doesch primary, 1×, control):

| b_CaL | ng/mL | ver alone | ivab alone | combo | k | EMQF | 95% CI | elig | ceiling | obs/ceil |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.029 | 34.7 | 3 (0.6%) | 13 (2.6%) | 16 (3.2%) | 3 | 0.60% | [0.20, 1.75] | 486 | 97.2% | 0.006 |
| 0.108 | 125.2 | 9 (1.8%) | 13 (2.6%) | 40 (8.0%) | 23 | 4.60% | [3.08, 6.81] | 483 | 96.6% | 0.048 |
| 0.200 | 243.5 | 46 (9.2%) | 13 (2.6%) | 84 (16.8%) | 34 | 6.80% | [4.91, 9.35] | 450 | 90.0% | 0.076 |
| 0.275 | 356.9 | 95 (19.0%) | 13 (2.6%) | 147 (29.4%) | 52 | **10.40%** | [8.02, 13.38] | 405 | 81.0% | 0.128 |
| 0.300 | 399.2 | 127 (25.4%) | 13 (2.6%) | 171 (34.2%) | 44 | 8.80% | [6.62, 11.61] | 373 | 74.6% | 0.118 |

**Ceiling headroom is ample throughout: observed/ceiling never exceeds 0.180 at any of the 198
conditions.** No result here is constrained by endpoint depletion.

## 5. Interval-supported 5% and 10% status — point and interval reported separately

Band maxima, all 36 anchor × arm × state × band combinations
(`P3_results_full.json → band_maxima`). Selected rows:

| anchor | arm | state | band | max EMQF | rung | 95% CI | >5 pt | **>5 CI** | >10 pt | **>10 CI** |
|---|---|---|---|---|---|---|---|---|---|---|
| Doesch | 1× | control | 480 | 10.40% | 0.275 | [8.02, 13.38] | YES | **YES** | YES | **no** |
| Doesch | 2× | control | 480 | 12.00% | 0.275 | [9.44, 15.14] | YES | **YES** | YES | **no** |
| **Doesch** | **3×** | **control** | **480** | **14.40%** | 0.275 | [11.59, 17.75] | YES | **YES** | YES | **YES** |
| **Doesch** | **3×** | **iso** | **480** | **13.33%** | 0.300 | [10.54, 16.73] | YES | **YES** | YES | **YES** |
| 10-year | 3× | control | 480 | 12.20% | 0.275 | [9.62, 15.36] | YES | YES | YES | no |
| 36-month | 1× | control | 480 | 6.00% | 0.275 | [4.23, 8.44] | YES | **no** | no | no |
| Doesch | 1× | control | 240 | 4.60% | 0.108 | [3.08, 6.81] | no | no | no | no |

**Summary**

- **Interval-supported >10%: 2 of 36 band maxima** — both the Doesch primary anchor at the
  **3× PK arm** in the 480 mg/day band (control and iso).
- Interval-supported >5%: **15 of 36** band maxima.
- Across all 198 conditions, 7 have a lower bound above 10%; **5 of those 7 sit at the
  0.40 rung, which is the out-of-band headroom marker and supports no dose claim.** The two
  in-band ones are the Doesch 3× cases above.
- **No 1× or 2× condition anywhere achieves interval-supported >10% within either band.**

**This qualifies the P2/P4 conclusion rather than contradicting it.** P2 and P4 examined only
the 1× arm and found no interval-supported 10% crossing; P3 reproduces that at 1× and 2×, and
finds the crossing appears **only** under 3× CYP3A4-inhibited exposure at the primary anchor.
A manuscript 10% claim is therefore defensible only if explicitly restricted to strong-inhibitor
co-exposure at the primary anchor — not as a general statement.

## 6. 240 vs 480 mg/day, all PK arms, both states

| anchor | arm | state | 240 max | 480 max | diff | ratio |
|---|---|---|---|---|---|---|
| Doesch | 1× | control | 4.60% | 10.40% | +5.80 pp | 2.26 |
| Doesch | 1× | iso | 2.37% | 8.39% | +6.02 pp | 3.55 |
| Doesch | 2× | control | 4.20% | 12.00% | +7.80 pp | 2.86 |
| Doesch | 2× | iso | 3.66% | 11.61% | +7.96 pp | 3.18 |
| Doesch | 3× | control | 5.00% | 14.40% | +9.40 pp | 2.88 |
| Doesch | 3× | iso | 5.81% | 13.33% | +7.53 pp | 2.30 |
| 10-year | 1× | control | 3.00% | 9.00% | +6.00 pp | 3.00 |
| 36-month | 1× | control | 3.00% | 6.00% | +3.00 pp | 2.00 |
| 36-month | 1× | iso | 0.86% | 4.09% | +3.23 pp | 4.75 |

**480 mg/day exceeds 240 mg/day in all 18 comparisons**, by +3.00 to +9.40 pp (ratio 2.00–4.75).
The dose separation is the most consistent feature in the whole grid. **No 240 mg/day band
maximum achieves interval-supported 5% in any arm or state**; the highest is 5.81% (Doesch 3×
iso), whose lower bound is 4.02%.

## 7. PK/PD decomposition (bpm, vs ivabradine alone at 1×)

| state | anchor | rung | PK only | PD only | PK+PD 2× | PK+PD 3× | larger |
|---|---|---|---|---|---|---|---|
| control | Doesch | 2.9% | −1.96 | −1.67 | −3.80 | −4.73 | PK |
| control | Doesch | 30.0% | −1.71 | **−19.76** | −22.01 | −23.30 | PD |
| control | 10-year | 2.9% | −1.99 | −1.90 | −3.70 | −4.97 | PK |
| control | 10-year | 30.0% | −1.88 | −19.77 | −22.06 | −23.42 | PD |
| control | 36-month | 2.9% | −1.82 | −1.88 | −3.71 | −4.82 | **PD** |
| control | 36-month | 30.0% | −1.68 | −20.22 | −22.53 | −23.65 | PD |
| iso | Doesch | 2.9% | −4.13 | −1.33 | −5.37 | −7.78 | PK |
| iso | Doesch | 30.0% | −3.60 | −16.26 | −20.68 | −22.51 | PD |
| iso | 10-year | 2.9% | −4.26 | −1.56 | −5.58 | −7.88 | PK |
| iso | 10-year | 30.0% | −3.85 | −16.31 | −20.87 | −23.28 | PD |
| iso | 36-month | 2.9% | −3.75 | −1.59 | −5.23 | −7.69 | PK |
| iso | 36-month | 30.0% | −3.60 | −16.47 | −20.38 | −23.15 | PD |

**Rank swap PK → PD across the licensed range in 5 of 6 anchor × state combinations.** The one
exception is 36-month/control, where PD is already marginally larger at 2.9% (−1.88 vs −1.82,
a 0.06 bpm difference — far too small to treat as a real ordering). The qualitative finding is
unchanged: at the low end the interaction is dominated by the PK effect, at the high end
overwhelmingly by verapamil's own PD effect.

## 8. External comparison vs the SmPC −5 bpm

Matching contrast is PK+PD 2× (the clinical study had both the exposure rise and verapamil's
own PD effect). **Primary point = time-average free concentration = 2.9% block**, per the
frozen `comparison_point` rule.

| state | anchor | point | block | predicted | observed | ratio |
|---|---|---|---|---|---|---|
| control | Doesch | **time-average (PRIMARY)** | 2.9% | **−3.83** | −5.0 | **0.77** |
| control | 10-year | time-average (PRIMARY) | 2.9% | −3.87 | −5.0 | 0.77 |
| control | 36-month | time-average (PRIMARY) | 2.9% | −3.71 | −5.0 | 0.74 |
| control | Doesch | Cmax (sensitivity) | 14.0% | −10.95 | −5.0 | 2.19 |
| iso | Doesch | **time-average (PRIMARY)** | 2.9% | **−5.43** | −5.0 | **1.09** |
| iso | 10-year | time-average (PRIMARY) | 2.9% | −5.60 | −5.0 | 1.12 |
| iso | 36-month | time-average (PRIMARY) | 2.9% | −5.29 | −5.0 | 1.06 |
| iso | Doesch | Cmax (sensitivity) | 14.0% | −10.93 | −5.0 | 2.19 |

**At the pre-specified primary point the model under-predicts by ~25% in control and
over-predicts by ~6–12% in Iso — both within about 1.2 bpm of the reported −5 bpm.** The Cmax
sensitivity over-predicts roughly two-fold in every case and is *not* promoted to primary.

**Trough:** the label publishes no 24-h trough for 240 mg/day, and the true trough lies
**below** the time-average, so the 2.9% point is an **upper bound** on any trough-based
comparison — a trough comparison would predict a smaller reduction still. Reported as a bound
rather than invented as a point.

The external agreement is essentially anchor-independent (0.74–0.77 control, 1.06–1.12 iso
across all three anchors) — the incremental 2× contrast cancels most of the anchor difference,
consistent with the Task N finding.

## 9. Bliss classification at the primary anchor

Frozen 5-way ladder; **no-events** and **ceiling** are the non-informative classes.

| state | informative rungs | additive | SUPER-ADDITIVE | excluded |
|---|---|---|---|---|
| control | **11/11** | 2 (2.9%, 5.0%) | 9 | **0** |
| iso | **11/11** | 5 | 6 | **0** |

**No rung was excluded** — every rung was informative in both states, so the
informative-rung exclusion rule was applied and found to remove nothing. Super-additivity
appears from ~10% block in control and from ~14% in iso.

As the frozen definition states, this is an **artifact demonstration, not a mechanistic
claim**: a threshold endpoint manufactures Bliss super-additivity from additive target
occupancy, and Figure 4 carries that caption.

## 10. Manifest and figures

- **`08_taskP/p3/P3_values_manifest.json`** — **659 values**, every one read programmatically
  from the frozen P3 outputs, never from prose.
- **`08_taskP/p3_figures/`** — all four regenerated on P3 results:
  1. `P3_figure1_population.png` — baseline reproduction vs Fabbri Table 5; population/subset
  2. `P3_figure2_quiescence_thresholds.png` — I_CaL and I_f curves, subset vs full, Wilson bands
  3. `P3_figure3_EMQF_three_anchors.png` — EMQF vs exposure, 3 anchors × 3 arms × both states
  4. `P3_figure4_bliss_primary_anchor.png` — **primary anchor**, EMQF ladder + Bliss classes

  Each rendered and inspected: no label collisions, exposure bands and 5%/10% guides legible.

## 11. Change from the historical 188-model results

Historical values are comparisons, not targets. Nothing was tuned toward them.

| quantity | historical 188 | P2 (1028) | **P3 (500 subset)** |
|---|---|---|---|
| Doesch max EMQF, 1× control, 480 band | **16.0%** | 11.28% | **10.40%** |
| 10-year, same | 12.8% | 10.02% | **9.00%** |
| 36-month, same | 6.9% | 5.74% | **6.00%** |
| rung of maximum | 0.275 / 0.275 / 0.300 | 0.275 (all) | 0.275 (all) |
| ordering preserved | yes | yes | **yes** |
| interval-supported 10%, 1× | claimed | **no** | **no** |

**Quantitative change:** the primary-anchor EMQF continues to fall as the population widens —
16.0% (188) → 11.28% (1028) → 10.40% (500 subset). The P3 value sits slightly below P2's, which
is the direction the §2 rate imbalance predicts (a faster subset should be marginally more
resistant), so I would not read the P3–P2 gap as an independent effect.

**Qualitative changes:**

1. **The historical interval-supported 10% claim remains unsupported at 1× and 2×**, in the
   dense grid as in P2 and P4.
2. **A new, narrower finding:** interval-supported >10% *does* occur — but only at the **3×
   arm, primary anchor, 480 mg/day band**, in both states. This is a strong-inhibitor
   condition, not the general case, and was invisible to P2/P4 because those examined 1× only.
3. **No 240 mg/day condition reaches interval-supported 5%** in any arm or state.
4. The PK → PD rank swap, the ~2× Cmax over-prediction, and the Bliss super-additivity pattern
   all reproduce.

## 12. Gates and integrity

No gate failed. Nothing was fitted; no pair result informed any parameter; the subset was not
redrawn; no anchor mapping, Hill value, exposure mapping, rung, retention criterion or endpoint
definition was modified. The one deviation from a literal reading of the brief — simulating the
7× bounding arm — is disclosed in §3 and excluded from all reported analyses.

**Standing caveat:** the committed subset is faster than its complement (median rate +2.56 bpm,
95% CI [+0.37, +4.56]). Every P3 number above inherits that imbalance. It is a property of an
honest pre-committed draw, not a defect in execution, and the full 1,028-model population
remains the primary basis for any manuscript claim.
