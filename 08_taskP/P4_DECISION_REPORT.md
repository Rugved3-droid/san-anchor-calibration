# P4 — independent population replication: decision report

Completed 2026-08-27. Scripts: `08_taskP/P4_population.py`, `P4_threshold_sweep.py`,
`P4_threshold_compare.py`, `P4_anchor_experiment.py`, `P4_analyse.py`. Raw:
`zhou_san_run_p4/`, `08_taskP/p4/`, `08_taskP/p4_threshold/`.

**Headline: the anchor effect replicates in an independently sampled population, at
near-identical magnitude. And the 10% crossing is NOT interval-supported in P4 — confirming,
independently, that the historical 10% claim must not be carried forward.**

---

## 1. Population construction and hashes

Seed derivation re-verified at run time: SHA256(`TASK_P_P4_INDEPENDENT_LHS_V1`) =
`2efa507b…`, first 8 hex → mod (2³¹−1) → **788156539**. Unchanged from the pre-P1 commitment.

**Pre-execution**

| item | SHA256 |
|---|---|
| P4 seed | **788156539** |
| seed commitment file | `bfd8ed625f966c5001ba89c955bcb9b3a18401a4f7b240174dfa24a05739d69b` |
| config.yaml | `37c1dac662daf22d94ff0bdd6973fb56cf7599ad93d15cd2832affe19cc031d4` |
| CellML | `9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec` |
| **generated P4 LHS** | `7126bde6aaa4772505454c6c16550d597d8206a763d399210594f67bfe50bb78` |

**Post-execution**

| item | SHA256 |
|---|---|
| results.jsonl | `973dd59be4e5ed22f1d8d0b2e9cd17c95a4d618560fcb911f4fc5749951a8854` |
| retained population npz | `445ea46bd008f356d2a162cfdc11c5cba64b63d7fbf215cb7c5ca6d06bf49e71` |
| manifest | `f154cc20db76253c83f39b8c17d14167a458686798b17e75d225e8dc046d1546` |

The npz hash matches the value declared inside the manifest.

**Independence verified before simulating:** shape (5000, 12), scale range [0, 2], stored seed
788156539, parameter ordering / variable names / baseline vector all identical to P1, and no
row shared with the P1 sample. Implementation calls the frozen
`run_full_population.main()` directly — sampling, model, solver, tolerances, duration,
pristine-state restoration, biomarkers, retention criteria and manifest writing are the same
code that produced P1. Only the seed and working paths differ.

*Spawn-safety note:* Windows pool workers re-import with fresh globals, so the seed/path
rebinding is applied at module level and every worker asserts the loaded sample's stored seed
equals 788156539 before simulating. Without that guard a worker could have paired P4 model
indices with P1 parameter vectors silently. The same guard is used in the threshold sweep and
the anchor replication.

**Nothing was regenerated, re-seeded, or discarded. This is the first and only realisation
drawn from 788156539.**

---

## 2. P4 population report

| # | quantity | value |
|---|---|---|
| 1 | models attempted | **5000** (contiguous 0–4999, 0 duplicates) |
| 2 | successful simulations | **5000** |
| 3 | **solver failures** | **0 (0.0%)** |
| 4 | pacing / non-pacing | **2733 / 2267** (45.3% non-pacing) |
| 5 | retained | **1044** (independently recomputed; matches manifest) |
| 6 | retained fraction | **20.88%** |
| 7 | **Wilson 95%** | **[19.78%, 22.03%]** |
| 8 | P1 comparison | 1028/5000 = 20.56%, Wilson [19.46%, 21.70%] |
| 9 | Zhou comparison | 1046/5000 = 20.92% |

**Bounded differences (not equivalence claims):**

- P4 − P1 = **+0.32 pp**, 95% CI **[−1.27, +1.91] pp**
- P4 − Zhou = **−0.04 pp**

P4 retention lands essentially on Zhou's published 20.92%. The P1 and P4 intervals overlap
substantially, but no equivalence margin was prespecified and I am not claiming the
populations are identical — only that the retention difference is bounded within about
±2 pp.

**10 — intrinsic-rate distribution (retained, n = 1044)**

| | median | IQR | range | 5th–95th | mean ± SD |
|---|---|---|---|---|---|
| CL (ms) | 746.413 | 669.786–840.839 | 600.231–999.956 | 612.367–965.383 | 761.284 ± 108.812 |
| rate (bpm) | 80.385 | 71.357–89.581 | 60.003–99.961 | 62.152–97.980 | 80.385 ± 11.104 |

P1 retained for comparison: median 735.900 ms / 81.533 bpm. Both are truncated to the same
[600, 1000] ms band by the retention rule, so only the shape inside it can differ.

---

## 3. P4 threshold geometry (frozen ladder, 19 levels, 5% steps)

### I_CaL

Both populations: **0 censored, 0 non-monotone, 0 errors.**

| | P1 (1028) | P4 (1044) |
|---|---|---|
| conditional median | 0.45 | **0.40** |
| IQR | 0.30–0.55 | 0.30–0.55 |
| range | 0.05–0.85 | 0.05–0.85 |

| block | P1 % | P1 95% CI | P4 % | P4 95% CI | diff (pp) |
|---|---|---|---|---|---|
| 0.10 | 2.24 | [1.50, 3.33] | 3.45 | [2.50, 4.74] | −1.21 |
| 0.20 | 10.12 | [8.42, 12.11] | 10.63 | [8.90, 12.65] | −0.52 |
| 0.25 | 16.34 | [14.21, 18.73] | 18.77 | [16.52, 21.26] | −2.43 |
| 0.30 | 27.04 | [24.42, 29.84] | 27.59 | [24.96, 30.38] | −0.54 |
| 0.35 | 38.91 | [35.98, 41.93] | 40.80 | [37.86, 43.81] | −1.89 |
| **0.40** | 49.90 | [46.85, 52.95] | 52.87 | [49.84, 55.89] | **−2.97** |
| 0.45 | 61.96 | [58.96, 64.88] | 62.74 | [59.76, 65.62] | −0.77 |
| 0.50 | 73.15 | [70.36, 75.77] | 73.95 | [71.20, 76.52] | −0.79 |
| 0.60 | 87.35 | [85.18, 89.25] | 88.12 | [86.02, 89.95] | −0.77 |
| 0.70 | 96.79 | [95.53, 97.71] | 96.65 | [95.37, 97.58] | +0.14 |
| 0.80 | 99.81 | [99.29, 99.95] | 99.81 | [99.30, 99.95] | −0.00 |

**Largest |P1−P4| difference across the frozen ladder: 2.97 pp, at block 0.40.**
Wilson intervals overlap at **19/19** levels.

### I_f

| | P1 (1028) | P4 (1044) |
|---|---|---|
| **still pacing at 90% block** | 955 (**92.9%**) | 955 (**91.5%**) |
| uncensored | 73 | 89 |
| conditional median | 0.70 | 0.70 |
| conditional IQR | 0.50–0.85 | 0.55–0.85 |
| range | 0.05–0.90 | 0.15–0.90 |
| non-monotone | 0 | 0 |

| block | P1 % | P1 95% CI | P4 % | P4 95% CI | diff (pp) |
|---|---|---|---|---|---|
| 0.30 | 0.58 | [0.27, 1.27] | 0.57 | [0.26, 1.25] | +0.01 |
| 0.40 | 1.07 | [0.60, 1.91] | 0.86 | [0.45, 1.63] | +0.21 |
| 0.50 | 1.85 | [1.19, 2.87] | 1.25 | [0.73, 2.12] | +0.60 |
| 0.60 | 2.63 | [1.81, 3.79] | 2.97 | [2.10, 4.18] | −0.34 |
| 0.70 | 4.18 | [3.12, 5.59] | 4.69 | [3.57, 6.15] | −0.51 |
| 0.80 | 5.25 | [4.05, 6.79] | 5.84 | [4.58, 7.43] | −0.59 |
| **0.90** | 7.10 | [5.69, 8.84] | 8.52 | [6.98, 10.37] | **−1.42** |

**Largest |P1−P4| difference across the frozen ladder: 1.42 pp, at block 0.90.**
Wilson intervals overlap at **19/19** levels. Censoring fractions differ by 1.4 pp.

The conditional median agrees at 0.70, but it rests on 73 and 89 uncensored models
respectively. Per the carried-forward P1 finding it is **not** treated as a well-estimated
population threshold; the fixed-block curve and the censoring fraction are the primary
quantities and both replicate tightly.

### Threshold summary

| current | largest \|P1−P4\| difference | at block | Wilson overlap | censoring |
|---|---|---|---|---|
| I_CaL | **2.97 pp** | 0.40 | 19/19 | 0% both |
| I_f | **1.42 pp** | 0.90 | 19/19 | 92.9% vs 91.5% |

All threshold claims are limited to the 5%-block grid resolution. Note the I_CaL median has
now been estimated three times independently — historical 188: 0.40, P1: 0.45, P4: 0.40 — all
within one grid step, exactly as the carried-forward finding anticipated.

---

## 4. P4 rung-level results, with interval-supported 5%/10% classification

Control state, ivabradine 1×, **denominator 1044** (all retained models pace drug-free),
Wilson 95%. All 1044 models have complete 32-condition sets; 33,408 simulations, 0 duplicates.

`>5 pt` = point estimate > 5%; `>5 CI` = **lower 95% bound** > 5% (interval-supported).
Same for 10%.

### Doesch 2007 (PRIMARY), I_f = 0.5840

| b_CaL | ver alone | ivab alone | combo | k | EMQF % | 95% CI | elig | max poss. | obs/max | >5 pt | >5 CI | >10 pt | >10 CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 37 (3.5%) | 29 (2.8%) | 94 (9.0%) | 36 | 3.45% | [2.50, 4.74] | 986 | 94.4% | 0.037 | no | no | no | no |
| 0.140 | 56 (5.4%) | 29 (2.8%) | 134 (12.8%) | 63 | 6.03% | [4.74, 7.65] | 972 | 93.1% | 0.065 | YES | no | no | no |
| 0.150 | 65 (6.2%) | 29 (2.8%) | 150 (14.4%) | 69 | 6.61% | [5.26, 8.28] | 963 | 92.2% | 0.072 | YES | YES | no | no |
| 0.200 | 111 (10.6%) | 29 (2.8%) | 217 (20.8%) | 93 | 8.91% | [7.33, 10.79] | 920 | 88.1% | 0.101 | YES | YES | no | no |
| 0.250 | 196 (18.8%) | 29 (2.8%) | 306 (29.3%) | 100 | 9.58% | [7.94, 11.51] | 837 | 80.2% | 0.119 | YES | YES | no | no |
| 0.275 | 241 (23.1%) | 29 (2.8%) | 363 (34.8%) | 114 | 10.92% | [9.17, 12.96] | 795 | 76.1% | 0.143 | YES | YES | YES | **no** |
| **0.300** | 288 (27.6%) | 29 (2.8%) | 409 (39.2%) | **117** | **11.21%** | [9.43, 13.26] | 752 | 72.0% | 0.156 | YES | YES | YES | **no** |

### 10-year cohort, I_f = 0.5090

| b_CaL | ver alone | ivab alone | combo | k | EMQF % | 95% CI | elig | max poss. | obs/max | >5 pt | >5 CI | >10 pt | >10 CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 37 (3.5%) | 15 (1.4%) | 81 (7.8%) | 36 | 3.45% | [2.50, 4.74] | 999 | 95.7% | 0.036 | no | no | no | no |
| 0.140 | 56 (5.4%) | 15 (1.4%) | 119 (11.4%) | 57 | 5.46% | [4.24, 7.01] | 982 | 94.1% | 0.058 | YES | no | no | no |
| 0.150 | 65 (6.2%) | 15 (1.4%) | 130 (12.5%) | 59 | 5.65% | [4.41, 7.22] | 973 | 93.2% | 0.061 | YES | no | no | no |
| 0.200 | 111 (10.6%) | 15 (1.4%) | 197 (18.9%) | 80 | 7.66% | [6.20, 9.44] | 927 | 88.8% | 0.086 | YES | YES | no | no |
| 0.250 | 196 (18.8%) | 15 (1.4%) | 288 (27.6%) | 89 | 8.52% | [6.98, 10.37] | 844 | 80.8% | 0.105 | YES | YES | no | no |
| 0.275 | 241 (23.1%) | 15 (1.4%) | 335 (32.1%) | 92 | 8.81% | [7.24, 10.69] | 800 | 76.6% | 0.115 | YES | YES | no | no |
| **0.300** | 288 (27.6%) | 15 (1.4%) | 396 (37.9%) | **108** | **10.34%** | [8.64, 12.34] | 756 | 72.4% | 0.143 | YES | YES | YES | **no** |

### 36-month (superseded), I_f = 0.3120

| b_CaL | ver alone | ivab alone | combo | k | EMQF % | 95% CI | elig | max poss. | obs/max | >5 pt | >5 CI | >10 pt | >10 CI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.108 | 37 (3.5%) | 6 (0.6%) | 55 (5.3%) | 17 | 1.63% | [1.02, 2.59] | 1006 | 96.4% | 0.017 | no | no | no | no |
| 0.140 | 56 (5.4%) | 6 (0.6%) | 81 (7.8%) | 25 | 2.39% | [1.63, 3.51] | 988 | 94.6% | 0.025 | no | no | no | no |
| 0.150 | 65 (6.2%) | 6 (0.6%) | 91 (8.7%) | 26 | 2.49% | [1.71, 3.62] | 979 | 93.8% | 0.027 | no | no | no | no |
| 0.200 | 111 (10.6%) | 6 (0.6%) | 160 (15.3%) | 49 | 4.69% | [3.57, 6.15] | 933 | 89.4% | 0.053 | no | no | no | no |
| 0.250 | 196 (18.8%) | 6 (0.6%) | 247 (23.7%) | 52 | 4.98% | [3.82, 6.47] | 848 | 81.2% | 0.061 | no | no | no | no |
| 0.275 | 241 (23.1%) | 6 (0.6%) | 297 (28.4%) | 58 | 5.56% | [4.32, 7.11] | 803 | 76.9% | 0.072 | YES | **no** | no | no |
| **0.300** | 288 (27.6%) | 6 (0.6%) | 348 (33.3%) | **60** | **5.75%** | [4.49, 7.33] | 756 | 72.4% | 0.079 | YES | **no** | no | no |

No rung omitted.

---

## 5. Maximum EMQF within the 480 mg/day band

Maxima taken over simulated frozen rungs only; no interpolation. No ties.

| anchor | max EMQF | rung | k / n | 95% CI | ceiling | obs/ceiling | P2 (comparison only) |
|---|---|---|---|---|---|---|---|
| Doesch (PRIMARY) | **11.21%** | **0.300** | 117 / 1044 | [9.43, 13.26] | 752 (72.0%) | 0.156 | 11.28% |
| 10-year | **10.34%** | **0.300** | 108 / 1044 | [8.64, 12.34] | 756 (72.4%) | 0.143 | 10.02% |
| 36-month | **5.75%** | **0.300** | 60 / 1044 | [4.49, 7.33] | 756 (72.4%) | 0.079 | 5.74% |

**Rung of maximum shifted from 0.275 (P2) to 0.300 (P4) for all three anchors.** The
neighbouring values are close — Doesch 10.92% at 0.275 vs 11.21% at 0.300 — so this is a
one-grid-step shift within noise, not a change in where the effect lives. It is recorded
because the maximum must be reported at an actually simulated rung.

---

## 6. Interval-supported 5% and 10% threshold status — the decisive re-derivation

### At each anchor's maximum

| anchor | >5% point | **>5% interval-supported** | >10% point | **>10% interval-supported** |
|---|---|---|---|---|
| Doesch (PRIMARY) | YES | **YES** | YES | **NO** |
| 10-year | YES | **YES** | YES | **NO** |
| 36-month | YES | **NO** | NO | **NO** |

### Across all 21 anchor × rung conditions

- **Lower 95% bound > 10%: NONE.** Not one condition in P4.
- Lower 95% bound > 5%: Doesch at 0.150, 0.200, 0.250, 0.275, 0.300; 10-year at 0.200,
  0.250, 0.275, 0.300. The 36-month anchor never achieves it.

### Comparison with P2, computed identically

| | P2 (1028) | P4 (1044) |
|---|---|---|
| conditions with lower bound > 10% | **NONE** | **NONE** |
| Doesch: 5% interval-supported | YES | YES |
| 10-year: 5% interval-supported | YES | YES |
| 36-month: 5% interval-supported | NO | NO |

**P4 independently re-derives the conclusion that the 10% crossing is not interval-supported.**
Both the primary and 10-year anchors exceed 10% as point estimates at their maxima, and
neither has a lower confidence bound above 10% in either population. The historical
manuscript claim of an interval-supported 10% crossing is not recoverable from either the
completed P1/P2 population or the independent P4 population, and must not be carried forward.

The 5% crossing **is** interval-supported, but only for the two high anchors. The 36-month
anchor exceeds 5% as a point estimate at its maximum (5.75%) while its lower bound (4.49%)
does not — a case where relying on the point estimate alone would have been wrong.

---

## 7. Paired McNemar comparisons

All anchors evaluated on the same models, so the comparison is paired. Effect sizes given
alongside every p-value.

### At rung 0.275

| comparison | A⁺B⁻ | A⁻B⁺ | exact p | absolute difference |
|---|---|---|---|---|
| Doesch vs 10-year | 27 | 5 | **1.13 × 10⁻⁴** | **+2.11 pp** |
| Doesch vs 36-month | 64 | 8 | **5.77 × 10⁻¹²** | **+5.36 pp** |
| 10-year vs 36-month | 37 | 3 | **1.95 × 10⁻⁸** | **+3.26 pp** |

### At rung 0.300 (all three anchors' maximum)

| comparison | A⁺B⁻ | A⁻B⁺ | exact p | absolute difference |
|---|---|---|---|---|
| Doesch vs 10-year | 13 | 4 | **4.90 × 10⁻²** | **+0.86 pp** |
| Doesch vs 36-month | 62 | 5 | **1.42 × 10⁻¹³** | **+5.46 pp** |
| 10-year vs 36-month | 49 | 1 | **9.06 × 10⁻¹⁴** | **+4.60 pp** |

**Reading, with both cautions the brief demands.** The Doesch-vs-36-month and
10-year-vs-36-month contrasts are large and overwhelmingly supported at both rungs — that is
the low-versus-high calibration contrast, and it is robust. The Doesch-vs-10-year contrast is
different in kind: at rung 0.300 it reaches p = 0.049 on a difference of **0.86 pp**. A small
p-value on a sub-percentage-point difference should not be read as a large or mechanistically
important effect, and I am not presenting it as one. Conversely, the unpaired Wilson intervals
for Doesch and 10-year overlap heavily at every rung, and that overlap is **not** evidence
that the paired conditions do not differ — the discordance is consistently one-sided
(27 vs 5 at 0.275, 13 vs 4 at 0.300).

---

## 8. Comparison with P1/P2

| quantity | P2 (1028) | P4 (1044) |
|---|---|---|
| Doesch max EMQF | 11.28% | **11.21%** |
| 10-year max EMQF | 10.02% | **10.34%** |
| 36-month max EMQF | 5.74% | **5.75%** |
| ordering preserved | yes | **yes** |
| rung of maximum | 0.275 (all three) | 0.300 (all three) |
| absolute separation (primary − superseded) | +5.54 pp | **+5.46 pp** |
| relative ratio (primary / superseded) | 1.97× | **1.95×** |
| ceiling at maximising rung | 78.9–79.1% | 72.0–72.4% |
| obs/ceiling, Doesch | 0.143 | 0.156 |
| obs/ceiling, 10-year | 0.127 | 0.143 |
| obs/ceiling, 36-month | 0.073 | 0.079 |
| 10% interval-supported anywhere | NO | **NO** |
| 5% interval-supported (Doesch, 10-year) | YES | **YES** |
| 5% interval-supported (36-month) | NO | **NO** |

**Ceiling headroom.** At their maximising rungs the ceilings differ (79% in P2 at rung 0.275
versus 72% in P4 at rung 0.300), but that is a consequence of the maximum sitting one rung
higher in P4, where verapamil-alone quiescence is larger — at the *same* rung 0.300 the P2
ceiling was 72.8–73.0%, essentially identical to P4's 72.0–72.4%. In both populations every
anchor uses a small fraction of the available headroom: observed/ceiling never exceeds 0.156.
**Endpoint depletion constrains nothing in either population**, and no difference between them
is attributable to ceiling saturation.

---

## 9. Interpretation

**Result: strong robustness — qualitative and quantitative.**

Against the four possibilities in the brief:

- **Strong robustness** — this is what occurred. The anchor effect reproduces with
  near-identical magnitude *and* structure. The three maxima differ from P2 by 0.07, 0.32 and
  0.01 percentage points respectively. The ordering is preserved. The absolute separation
  (+5.46 vs +5.54 pp) and relative separation (1.95× vs 1.97×) match to within rounding. The
  paired McNemar structure is preserved, including the pattern that the low-versus-high
  contrast is large while the Doesch-vs-10-year contrast is small.
- Qualitative robustness with quantitative variation — stronger than this; the absolute values
  also reproduced.
- Population-dependent effect — not supported.
- Failure to replicate — not supported.

**Answering the primary P4 question directly:** admissible open-loop calibration-anchor choice
**does** materially alter verapamil–ivabradine combination susceptibility in an independently
sampled valid SAN model population. The effect is not an artefact of the particular P1 draw.

Two qualifications I want on the record:

1. **The Doesch-vs-10-year separation is modest and rung-dependent.** It is +2.11 pp at rung
   0.275 and +0.86 pp at 0.300. The robust finding is the low-versus-high anchor contrast
   (36-month against either high anchor: +4.6 to +5.5 pp, p < 10⁻⁷ throughout), not fine
   discrimination between the two high anchors. Had the Doesch and 10-year ordering reversed,
   that alone would not have constituted failure — and it did not reverse.
2. **No anchor achieves an interval-supported 10% crossing in either population.** This is the
   single most consequential number for the manuscript revision, and P4 confirms it
   independently rather than inheriting it.

Nothing was tuned, refit, re-seeded or re-selected. The P2 values were used only as
comparisons, and reproducing them was never attempted.

---

## 10. Mandatory stop

P4 is complete: population construction, threshold geometry, decisive anchor replication,
interval-supported 5%/10% classification, paired McNemar, and the P1/P2 versus P4 comparison.

**Stopping here and awaiting explicit authorization.**

- **P3 remains blocked.** No dense Task-L1 grid started; no 188/250/500-model subset selected;
  no P3 subset seed drawn; no figures regenerated; no manuscript result numbers revised; no
  Bliss analysis begun on P4.
- No parameter, anchor mapping, Hill value, exposure mapping, rung, retention criterion or
  endpoint definition was modified anywhere in P4.

### Frozen for the manuscript revision

| finding | status |
|---|---|
| P2 triplet 11.28 / 10.02 / 5.74% at rung 0.275, n = 1028 | frozen (P2) |
| P4 triplet 11.21 / 10.34 / 5.75% at rung 0.300, n = 1044 | **new, independent** |
| historical 6.9 / 12.8 / 16.0% | superseded; comparison only |
| attenuation vs the 188-model subset was **not** ceiling depletion | preserved (P2 §7) |
| interval-supported **10%** crossing | **not supported in either population** |
| interval-supported **5%** crossing | supported for Doesch and 10-year; **not** for 36-month |
| I_CaL median resolution-limited (0.40 / 0.45 / 0.40 across three populations) | carried forward |
| I_f conditional median poorly determined under ~92% censoring | carried forward |
