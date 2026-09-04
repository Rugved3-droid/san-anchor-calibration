# P0 — proposed manuscript corrections (CANDIDATE ONLY, NOT APPLIED)

Against `D:\Parmar_SAN_manuscript_v6_CLEAN.docx`. **No manuscript file has been
modified by Task P.** These are candidate edits for review.

Each entry gives the exact current text, the proposed replacement, and the justification.

---

## D1 — Verapamil exposure provenance (P0.1)

**Location:** Methods 2.6, final paragraph.

**Current:**
> Chronic oral exposure ranges were taken from the regulatory label rather than from a
> single pharmacokinetic study: 240 mg/day, 35–164 ng·mL⁻¹; 480 mg/day, 125–400 ng·mL⁻¹
> total plasma.

**Proposed (revised 2026-08-23 — 240 mg/day reframed as a constructed envelope):**
> Verapamil exposures were derived from the product label (18) rather than from a single
> pharmacokinetic study, and the two dose levels are not equivalent in kind. For 480 mg/day
> the label reports a measured steady-state concentration range of 125–400 ng·mL⁻¹ on
> chronic immediate-release dosing of 120 mg every six hours. For 240 mg/day the label
> reports no corresponding range, so the interval used here, 35–164 ng·mL⁻¹, is **not a
> reported concentration range but an exposure envelope constructed from the
> extended-release single-dose data**: its lower bound is the fed AUC(0–24 h) of
> 841 ng·h·mL⁻¹ divided by 24 h, giving a dose-interval time-average of 35 ng·mL⁻¹, and its
> upper bound is the fasted peak concentration of 164 ng·mL⁻¹. The envelope therefore spans
> a fed time-average to a fasted peak and is bounded by two different feeding states and a
> different formulation from the 480 mg/day range. It is used as a plausible-exposure
> bracket for the block ladder, not as an observed concentration distribution, and no
> quantity reported in this study is interpolated within it.

**New reference 18:**
> 18. Verapamil Hydrochloride Extended-Release Tablets USP. Prescribing information,
> CLINICAL PHARMACOLOGY. DailyMed setid d1a0aa24-0f81-498a-8c25-5095b2bb8f57; label
> revision 6/2010.

**Justification.** The values are verbatim-traceable but were uncited, and the 240 mg/day
interval was presented in the same grammatical form as the 480 mg/day interval although only
the latter is a label-reported concentration range. The revised wording (i) names the source,
(ii) states explicitly that the 240 mg/day interval is a *constructed envelope* rather than a
regulatory concentration range, (iii) makes the formulation (extended- vs immediate-release)
and feeding state (fed lower bound, fasted upper bound) explicit for each bound, and (iv)
states the envelope's role as a bracket rather than a distribution. **No numerical value
changes and no simulation input is affected.**

*Note on scope:* the block ladder is computed at fixed block fractions and inverted to
concentration exactly (`taskH_exposure_ladder.py`), so the envelope is used only to say
whether a threshold falls inside or outside it. Its internal heterogeneity therefore affects
the wording of that statement, not any computed number.

---

## D2 — Verapamil unbound fraction citation (P0.2)

**Location:** Methods 2.6, first paragraph.

**Current:** "For verapamil the unbound fraction was 10.4%, and the L-type IC50 …"

**Proposed:** "For verapamil the unbound fraction was 10.4%, that is, one minus the
measured 89.6% bound fraction (13), and the L-type IC50 …"

**Justification.** Supported by ref 13 but the link was implicit and the reference appeared
only two sentences later against a different number.

---

## D3 — Ivabradine unbound fraction citation (P0.2)

**Location:** Methods 2.6, extrapolation paragraph.

**Current:** "… at 30% unbound (19 ng/mL ÷ 468.6 g/mol × 0.30 = 12.2 nM)."

**Proposed:** "… at 30% unbound (3) (19 ng/mL ÷ 468.6 g/mol, the free-base molecular
weight, × 0.30 = 12.2 nM; the assay measured ivabradine base)."

**Justification.** The 30% unbound figure carried no citation anywhere. The free-base
molecular weight matters: had the hydrochloride mass (505.05) been used the anchor
concentration would be 11.3 nM rather than 12.2 nM. **Flagged as requiring verbatim
verification of the ~70% protein-binding statement before submission.**

---

## D4 — Effective model-equivalent I_f block (P0.3)

Applies **only** where the block fraction is inferred by reproducing a clinical open-loop
heart-rate observation. It is **not** applied to block fractions measured in a channel
experiment (the Bucchi HCN4 values) nor to the direct model perturbation ladders in
Results 3.2 and Figure 2, which are not clinical inferences.

| # | location | current | proposed |
|---|---|---|---|
| D4a | Abstract | "Three admissible open-loop ivabradine anchors implied 58.4%, 50.9% and 31.2% funny-current block." | "Three admissible open-loop ivabradine anchors implied effective model-equivalent funny-current block of 58.4%, 50.9% and 31.2%." |
| D4b | Results 3.3 | "…implying 58.4% I_f block. The three anchors imply 58.4%, 50.9% and 31.2% block…" | "…implying an effective model-equivalent I_f block of 58.4%. The three anchors imply effective model-equivalent blocks of 58.4%, 50.9% and 31.2%…" |
| D4c | Methods 2.6 | "…arms of 58.40%, 70.97% and 77.17% I_f block at one-, two- and three-fold exposure" | "…arms of 58.40%, 70.97% and 77.17% effective model-equivalent I_f block at one-, two- and three-fold exposure" |
| D4d | Results 3.7 | "…the primary anchor more than doubles the funny-current block" | "…the primary anchor more than doubles the effective model-equivalent funny-current block" |

**New Methods statement**, to be added at the end of Methods 2.6:

> The clinically anchored block fraction represents the effective I_f perturbation required
> for this model to reproduce the observed open-loop chronotropic response, and is not an
> estimate of molecular HCN4 channel occupancy. It is a model-equivalent quantity: it
> absorbs any difference between the model's I_f formulation and the real current, and any
> mechanism of drug action not represented by a static conductance scaling. This is why it
> is not directly comparable with a channel-level IC50, and why the discrepancy against the
> cited in vitro value is reported as unexplained rather than as a potency estimate.

**Justification.** The manuscript's own argument depends on this distinction — the
≈250-fold discrepancy is only interpretable if the anchored quantity is understood not to
be channel occupancy. The current wording invites the reader to treat 58.4% as an HCN4
occupancy figure.

---

## D5 — Ivabradine Hill factor, now verified (added 2026-08-23)

**Status: RESOLVED. This was the last open P0 item and it is now closed.**

The Bucchi 2006 full text was obtained (PMC1779671) and the Hill factor **is** reported —
in Results, not in the abstract, which is why the earlier abstract-only check could not
confirm it. Verbatim, Results, "Ivabradine blocks HCN4 and HCN1 channels", Fig. 1C:

> "Fitting data points with the Hill equation resulted in half-block concentrations of 2.0
> and 0.94 μM and slope coefficients of 0.8 and 1.2 for HCN4 (*n* = 23) and HCN1
> (*n* = 27) channels, respectively."

| item | verified value |
|---|---|
| hHCN4 half-block | 2.0 µM (already verified from the abstract) |
| **hHCN4 Hill factor** | **0.8 — fitted, not assumed** |
| n | 23 cells |
| system | HEK 293, transient hHCN4 |
| protocol | −100 mV, 1.8 s activating step from −35 mV holding; +5 mV, 0.45 s; every 6 s |
| figure | Fig. 1C |

Two independent retrievals of the full text returned the same numbers; they differed only in
rendering the phrase as "Hill factors" versus "slope coefficients", which does not affect the
value. The paper's own discussion refers to it as a Hill slope ("A higher Hill slope for the
HCN1 curve…").

**Consequence:** the project's 0.80 is correct, correctly attributed to ref 15, and is a
*fitted* parameter of the published concentration–response — not a project-adopted
assumption. The contingency wording drafted earlier ("state that 0.80 is a project-adopted
slope") is **withdrawn as unnecessary.** The N4 Hill-shape assumption carried forward into
the 2× and 3× extrapolation is therefore an assumption about *extrapolating* a measured
Hill curve beyond its anchor, not about the slope value itself — the manuscript should keep
saying that, and it already does.

**Optional Methods addition** (transparency only, no claim change):

> The Hill factor of 0.80 is the value fitted to the hHCN4 concentration–response in ref 15
> (n = 23, HEK 293), not an assumed slope.

---

## Unresolved after P0

1. **Ivabradine 30% unbound** — the ~70% protein-binding statement has not been verified
   verbatim from the SmPC in this audit. This is the **only** remaining provenance gap. It
   is a citation gap, not a value dispute: 30% unbound is the standard figure and the
   derivation using it is arithmetically correct.

*(The ivabradine Hill slope, previously item 1, is closed — see D5.)*

---

## Effect on P1 inputs

**None.** Every value that enters a simulation was verified correct:

| input | status |
|---|---|
| verapamil exposure bands 35–164, 125–400 ng/mL | verbatim-correct (citation defect only) |
| verapamil f_u 10.4% | correct |
| verapamil IC50 198.7 nM / Hill 1.09 | correct, provenance documented |
| ivabradine free Cmax 12.2 nM | correct; free-base MW confirmed appropriate |
| ivabradine HCN4 2.0 µM | verbatim-correct |
| anchor heart rates (Doesch) | verbatim-correct |
| Fabbri Table 5 comparison values | verbatim-correct |

P0 therefore does **not** trigger the "STOP before P1" condition. The defects are in
citation and wording, not in any simulated quantity.
