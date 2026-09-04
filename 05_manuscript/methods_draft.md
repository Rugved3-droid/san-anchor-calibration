# Methods

*Draft for American Journal of Physiology — Heart and Circulatory Physiology, Methods and Resources.*

Every numerical value below was read programmatically from the frozen output files by `05_manuscript/taskM_methods.py` via `05_manuscript/values_manifest.json`; none was transcribed from prose. Each subsection records the manifest keys it used, and `05_manuscript/values_manifest.md` maps every key to the output file it came from and the script that produced it.

## Model and provenance

Simulations used the Fabbri et al. (2017) model of the human sinoatrial node myocyte, obtained as CellML from the Physiome Model Repository (`HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml (PMR e/568)`; https://models.physiomeproject.org/e/568). The file was checksummed before every run and is identified throughout by SHA256 `9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec`; any mismatch aborts execution, since a silently altered model file would invalidate the baseline validation that all later results rest on.

The CellML was imported directly by Myokit. **No equation was hand-transcribed**, and the model was not re-implemented in another language; this removes the most common source of unreported divergence between a published model and its reuse. Integration used CVODE with absolute and relative tolerances of 1e-08 and 1e-08. Control conditions were verified present in the file rather than assumed: voltage clamp off (`clamp_mode = 0`), no acetylcholine (`ACh = 0` mM) and no isoprenaline (`Iso = 0`).

**Baseline validation.** The unmodified model was pre-paced for 500 s to reach its limit cycle and biomarkers were measured over a subsequent logged window at 0.0001 s resolution. Reproduction of Fabbri Table 5 ('Present model' column) is shown in Figure 1A. Cycle length was 813.42 ms against a published 814.0 ms (-0.07%); maximum diastolic potential -58.89 mV (+0.02%); overshoot 26.41 mV (+0.03%); action potential amplitude 85.29 mV (-0.01%); diastolic depolarisation rate 48.02 mV·s⁻¹ (-0.17%); and (dV/dt)max 7.47 V·s⁻¹ (+0.99%). The largest absolute deviation across all six features was 0.99%. Steady state was confirmed by a cycle-length standard deviation of 0.0386 ms across 11 consecutive beats. This gate is executed as a hard precondition: the pipeline halts if it does not pass (verdict: PASS).

> **Provenance.** `model.source`; `model.cellml_sha256`; `baseline.setting.tol_abs`; `baseline.setting.tol_rel`; `baseline.setting.clamp_mode`; `baseline.setting.ACh_mM`; `baseline.setting.Iso`; `baseline.setting.prepace_s`; `baseline.setting.log_dt_s`; `baseline.CL_ms.simulated`; `baseline.CL_ms.published`; `baseline.CL_ms.pct_diff`; `baseline.MDP_mV.simulated`; `baseline.MDP_mV.pct_diff`; `baseline.OS_mV.simulated`; `baseline.OS_mV.pct_diff`; `baseline.APA_mV.simulated`; `baseline.APA_mV.pct_diff`; `baseline.DDR100_mV_s.simulated`; `baseline.DDR100_mV_s.pct_diff`; `baseline.dVdtmax_V_s.simulated`; `baseline.dVdtmax_V_s.pct_diff`; `baseline.worst_abs_pct_diff`; `baseline.CL_sd_ms`; `baseline.n_beats`; `baseline.verdict`

## Population of models

A population of models was generated following Zhou et al. (2019) by varying 12 conductances and ion-flux magnitudes. Each was mapped to the **root constant** in the CellML that the current or flux ultimately depends on; mappings were established by tracing the dependency graph rather than by matching names, and each was then verified numerically by confirming that a 1.5-fold change shifted cycle length. The mappings were:

| Zhou symbol | CellML variable | baseline |
|---|---|---|
| G_f | `i_f.g_f` | 0.00427 |
| G_CaL | `i_CaL.P_CaL` | 0.4578 |
| G_CaT | `i_CaT.P_CaT` | 0.04132 |
| G_Kr | `i_Kr.g_Kr` | 0.00424 |
| G_Ks | `i_Ks.g_Ks_` | 0.00065 |
| G_to | `i_to.g_to` | 0.0035 |
| G_Na | `i_Na.g_Na` | 0.0223 |
| G_NaK | `i_NaK.i_NaK_max` | 0.08105 |
| G_NaCa | `i_NaCa.K_NaCa` | 3.343 |
| G_Kur | `i_Kur.g_Kur` | 0.0001539 |
| P_Jrel | `Ca_SR_release.ks` | 1.48041e+08 |
| P_Jup | `Ca_intracellular_fluxes.P_up_basal` | 5 |

Three mappings are not inferable from the symbol name and are stated explicitly, because choosing the obvious variable instead would scale the wrong quantity:

- **G_f → `i_f.g_f`.** Root of the funny-current chain. g_f -> G_f -> G_f_K/G_f_Na -> g_f_K/g_f_Na -> i_fK/i_fNa. g_f_K and g_f_Na are computed variables, not independent constants, so scaling g_f scales the whole current.
- **G_Ks → `i_Ks.g_Ks_`.** g_Ks_ is the base constant; g_Ks = 1.2 * g_Ks_ only when Iso > 0. With Iso = 0 they are equal, but g_Ks_ is the correct scaling target.
- **P_Jup → `Ca_intracellular_fluxes.P_up_basal`.** P_up = P_up_basal * (1 - b_up), and b_up = 0 at baseline, so P_up_basal is the correct scaling target.

Zhou et al. describe 'up to ±100% variations'. This is ambiguous in isolation and the retention count depends on the reading, so the convention is recorded explicitly: a multiplicative scale factor drawn independently per parameter on [0, 2], applied as `parameter_value = baseline_value * scale_factor`. Sampling used Latin hypercube sampling (`scipy.stats.qmc.LatinHypercube`), 5000 models, seed 20260816. The frozen sample is identified by SHA256 `681f8fc6b8963467ace9f047a37e5a599ec1b92fc8c87c9ccfac5f8b214b9d35` and is validated against the configuration before reuse — seed, shape, parameter names, variables, baselines and the realised scale range are all checked, and a disagreement is fatal.

Each model was integrated for 1000 s. Models were retained if basic cycle length fell within [600, 1000] ms and overshoot was positive. Of 940 models simulated, 539 produced a stable rhythm, 401 did not pace, and there were 0 solver failures. **188 models were retained (20.0%, Wilson 95% CI 17.6%–22.7%)**, against the reference retention of 1046/5000 = 20.9% reported by Zhou et al. The reference proportion lies inside the confidence interval (Figure 1B). Retained intrinsic rates spanned 61.0–99.6 beats·min⁻¹ (median 82.2).

The retention count is the validation, and is reported as it emerged. Neither the sampling convention nor the retention criteria were adjusted toward the reference count; a mismatch would have been a finding about the implementation rather than a parameter to tune.

> **Provenance.** `lhs.n_parameters`; `lhs.parameters`; `config.nonobvious_mappings`; `lhs.scale_min`; `lhs.scale_max`; `lhs.n_models`; `lhs.seed`; `lhs.sample_sha256`; `population.criteria.bcl_min_ms`; `population.criteria.bcl_max_ms`; `population.n_simulated`; `population.n_integrated_ok`; `population.n_no_pacing`; `population.n_solver_failures`; `population.n_retained`; `population.retention_fraction`; `population.retention_wilson95`; `population.criteria.reference_retained`; `population.criteria.reference_total`; `population.zhou_reference_fraction`; `population.retained.bpm`

## State isolation and determinism

Myokit's `pre()` advances both the current state and the simulation's default state, and `reset()` returns to the default state. Without intervention each sampled model therefore begins from the previous model's steady state rather than from the published initial conditions, making results depend on evaluation order. The pristine state is captured once at compile time and both the state and the default state are restored before every model.

The effect was quantified by re-running the whole population with and without the correction across 940 models. Retention moved from 187 to 188 models (19.9% → 20.0%); 187 models were retained under both, 1 model changed from rejected to retained and 0 changed in the opposite direction. Mean absolute cycle-length change was 0.909 ms but the maximum was 241.4 ms — the aggregate effect is small while individual models can move substantially, which is why the correction is applied rather than argued to be negligible. All results reported here use the state-isolated population of 188 models.

Determinism was verified on the drug-simulation store. Of 65,424 records, 59,784 were unique and 5,640 were independent re-executions of an identical condition produced by concurrent workers. The number of conditions returning a different value on re-execution was **0**: every repeat was bit-identical. The store is identified by SHA256 `661763c00f80fb3cec2f9da5f635ff39b703c3dc6e0d23aa9eb960fbc878c1fc`.

> **Provenance.** `stateisolation.n_compared`; `stateisolation.retained_before`; `stateisolation.retained_after`; `stateisolation.retention_before`; `stateisolation.retention_after`; `stateisolation.identical_retained`; `stateisolation.rejected_to_retained`; `stateisolation.retained_to_rejected`; `stateisolation.mean_abs_dCL_ms`; `stateisolation.max_abs_dCL_ms`; `sims.pair_checkpoint_lines`; `sims.pair_unique`; `sims.pair_duplicate_reruns`; `sims.pair_determinism_disagreements`; `sims.pair_checkpoint_sha256`

## Open-loop calibration framework

The Fabbri model is an **open-loop plant**: an isolated sinoatrial myocyte with no baroreflex, no circulating catecholamine dynamics and no autonomic feedback. A resting heart rate measured in an intact patient is a **closed-loop output** in which any drug-induced rate reduction is opposed by reflex sympathetic withdrawal of vagal tone and increased sympathetic drive. The two quantities are not the same observable, and calibrating an open-loop model against a closed-loop measurement attributes the reflex to the pharmacology.

This is not a theoretical concern, and the decisive evidence is experimental. Qi et al. (Circulation 1987;75:888-893, PMID 3549045) gave intravenous verapamil to awake instrumented dogs in three groups. In **intact** animals sinus cycle length *shortened* — the drug produced reflex tachycardia. In animals under **autonomic blockade** and in **orthotopic transplant** recipients the transient shortening was absent, cycle length lengthened promptly, and sinus arrest occurred. The same drug at the same exposure moves heart rate in **opposite directions** depending only on whether the reflex arc is intact. A closed-loop resting heart rate therefore carries no usable information about the direct sinoatrial effect, and can carry the wrong sign.

Accordingly, **only open-loop comparators are admissible for calibration**: pharmacological autonomic blockade, or denervated (cardiac transplant) recipients. Intact-patient resting heart rate is excluded by construction, including where such data are larger, more recent or more precise than the open-loop alternative. The corresponding model state is Fabbri control (ACh = 0, Iso = 0). Where an elevated-rate comparator is required, the published Iso 1 µM state is used; that state is a *rate* match to a denervated transplant heart and not a mechanism match, since a denervated heart is intrinsically fast rather than β-stimulated, and results are reported in both states so that state-dependence is visible.

An unavoidable practical consequence is that open-loop anchors are scarce, old and often incompletely reported. Where the effect magnitude could not be recovered, the drug was carried as an **exposure ladder** across its full plausible range rather than collapsed to a single fitted value.

> **Provenance.** `anchor.verapamil.schulman.anchor`; `anchor.verapamil.schulman.n`; `anchor.verapamil.schulman.magnitude_recoverable`

## Anchor-selection rule

Where more than one open-loop anchor exists for the same drug, the choice between them is itself a degree of freedom, and one that can be exercised toward a preferred conclusion. The selection rule was therefore fixed in the study configuration, in advance, on **design quality alone**:

> DESIGN QUALITY ONLY. The anchor is chosen on four design criteria and explicitly NOT on the size of the resulting in-vitro discrepancy: (1) within-patient crossover, each subject their own control; (2) a DRUG-FREE baseline measured in the same patients, not a between-cohort contrast; (3) prospective rather than retrospective/observational; (4) earliest post-transplant (8-week treatment periods), therefore the least sympathetically reinnervated and the purest open-loop measurement. This is the same criterion the project already used when preferring the 36-month cohort over the 10-year one; applied consistently it selects Doesch over both.

Critically, the rule carries an explicit **exclusion clause**: the magnitude of the residual discrepancy between an anchor's implied potency and the in vitro value is *not* a selection criterion and was not used as one. Applying the design criteria to ivabradine selected the earliest, prospective, within-patient crossover anchor with a drug-free baseline, and doing so **increased** the unexplained discrepancy:

| anchor | fractional rate reduction | implied I_f block | implied IC50 | fold gap vs in vitro |
|---|---|---|---|---|
| Doesch 2007 8-week crossover (PRIMARY) | 21.0% | 58.4% | 8.0 nM | 250× |
| 10-year cohort | 18.1% | 50.9% | 11.7 nM | 172× |
| 36-month cohort (superseded) | 10.8% | 31.2% | 32.8 nM | 61× |

The adopted primary anchor is therefore 58.4% I_f block, which carries the largest unexplained gap of the three. Had gap magnitude been used as a criterion, the opposite anchor would have been selected. All three anchors are propagated through every downstream result as a sensitivity band (Figure 3), and reporting the primary alone is a protocol violation.

A pre-specified **comparison-point rule** governs how an anchor is matched to an exposure. For chronic steady-state dosing the comparator is the time-average free concentration over the dosing interval, AUC(0–τ)/τ × f_unbound; peak and trough values are reported alongside as a labelled sensitivity and are never promoted to primary. This is fixed in advance because a clinical exposure band commonly spans three-fold, and an analyst free to choose the comparison point within it can generally find agreement.

> **Provenance.** `config.anchor.selection_rule`; `config.anchor.gap_exclusion`; `config.anchor.sensitivity_band`; `config.anchor.primary_block`; `config.comparison_point.rule`

## Drug mapping and its scope of validity

Drugs enter the model as a **fractional reduction of the target conductance**, applied as a constant multiplier for the duration of the simulation. Free concentration is converted to fractional block through a Hill relationship with coefficient 1.09, and free concentration is obtained from total plasma concentration using a measured unbound fraction of 10.4%. For verapamil the L-type IC50 is reported under two charge-carrier assumptions: the Ba²⁺-derived value of 198.7 nM, and a Ca²⁺-corrected value of 47.3 nM. Both are propagated, because the choice determines where a given clinical exposure lands on the population failure curve.

**Scope of validity, stated as a limitation rather than an assumption.** Static fractional block is not a model of either drug's kinetics. Both act state-dependently and on a timescale long relative to the pacemaker cycle: verapamil is an inactivated-state blocker whose recovery time constant (≈5–7 s) exceeds the cycle length by roughly an order of magnitude, so block accumulates across beats; ivabradine block is current-dependent, exerted preferentially as channels deactivate on depolarisation and relieved by long hyperpolarisations, which amplifies its rate-reducing action at high rates.

**The direction of the resulting bias is determinate, and it is one-sided.** Under use-dependent block, slowing the cell reduces the number of block-accruing transitions per unit time and lengthens the interval available for unbinding, so real block *falls* as rate falls — a negative feedback that limits the drug's own effect. Static block has no such feedback: it holds the fraction fixed at the value appropriate to the pre-drug rate and continues to apply it to a cell that the drug has since slowed substantially. Static block therefore **over-states** the sustained effect, over-states the fraction of models driven below their threshold, and **every risk estimate reported here is an upper bound**. Both drugs err in the same direction, so the biases compound rather than cancel. This matters most where the predicted rate reduction is largest, which is precisely where the endpoint is decided.

Chronic oral exposure ranges were taken from the regulatory label rather than from a single pharmacokinetic study: 240 mg/day 35–164 ng·mL⁻¹; 480 mg/day 125–400 ng·mL⁻¹ total plasma.

> **Provenance.** `mapping.verapamil.ic50_nM`; `mapping.verapamil.hill`; `mapping.verapamil.f_unbound`; `mapping.verapamil.bands_ng_per_mL`; `mapping.verapamil.bands_free_nM`; `mapping.verapamil.band_blocks`

## Endpoint: excess absolute risk

The primary endpoint is **excess absolute risk (EAR)**, defined per-model and paired: the fraction of the population that continues to pace under drug A alone **and** under drug B alone, but loses automaticity under the combination. It is a count of models for which the combination, and only the combination, abolishes pacemaking. Confidence intervals are Wilson binomial intervals on that count.

The endpoint is defined against a population whose quiescence thresholds are heterogeneous but steep (Figure 2). Across the retained population the median I_CaL block abolishing automaticity was 40.0% (IQR 30.0%–51.2%, range 10.0%–80.0%), with 0 of 188 models tolerating 90% block. I_f block is far better tolerated: 176 of 188 models (93.6%) never became quiescent even at 90% block. Monotonicity of block versus quiescence was verified per model rather than assumed: 0 non-monotone model-ladders were found across both currents.

**Ceiling behaviour must be read explicitly.** EAR is bounded above by the fraction of models that survive both single agents. As monotherapy risk rises toward unity that surviving set shrinks toward zero, and EAR necessarily *falls* — not because the combination has become safer, but because there is no longer anyone left for it to harm additionally. A declining EAR at high exposure therefore indicates monotherapy risk absorbing the excess, and single-agent risk is reported alongside EAR at every exposure so the two cannot be confused. Within the clinical exposure bands the endpoint is not ceiling-limited.

**Bliss independence is reported as a secondary artifact demonstration, not as the primary null.** Any endpoint defined as the fraction of a population crossing a steep threshold will manufacture apparent super-additivity from additive target occupancy: pushing two individually sub-threshold blocks together carries many models across their thresholds at once, with no mechanistic interaction required. Figure 4 demonstrates this directly using a pair acting on **different** channels, for which the model contains no interaction of any kind — yet the Bliss classification alternates non-monotonically along one drug's exposure ladder while the paired EAR remains well behaved and the rescue fraction is zero at every rung. The alternation is a property of the endpoint's geometry, not of the drugs, which is why an interaction classification is not used as the primary result.

> **Provenance.** `threshold.G_CaL.threshold_median`; `threshold.G_CaL.threshold_iqr`; `threshold.G_CaL.threshold_range`; `threshold.G_CaL.n_never_quiescent`; `threshold.G_CaL.n`; `threshold.G_f.n_never_quiescent`; `threshold.G_f.n`; `ladder.G_CaL.n_non_monotone`; `ladder.G_f.n_non_monotone`; `bliss.crosstarget_classes_control`

## Study-integrity rule: no pair result may inform a parameter

The claim under test is that combination loss of automaticity can be **predicted** from independently calibrated single-drug mechanisms. That claim is only testable if the prediction is made before, and independently of, any combination observation. The following rule is recorded in the study configuration and is binding on all analyses:

> No quantity derived from a drug COMBINATION may be used, directly or indirectly, to set or adjust any model parameter. This covers the 12 sampled conductances/fluxes, every drug block fraction, every IC50 or Hill coefficient, every free-concentration assumption, and the retention criteria. Combination outcomes are outputs of this study, never inputs.

Violation voids the endpoint (`voids_study_if_violated: true`). The rule covers the sampled conductances, every block fraction, every IC50 and Hill coefficient, every free-concentration assumption and the retention criteria. Permitted calibration anchors are single-drug, open-loop observations and in vitro channel pharmacology; forbidden anchors include any combination outcome, any observed interaction classification, and any excess-risk, Bliss, Loewe or HSA quantity.

The rule is enforced mechanically rather than by intention: pair-prediction scripts take single-drug block fractions as fixed inputs and contain no optimiser, no target value and no inversion of any pair quantity; single-drug calibration scripts do not read any pair output file; and every block fraction in use is traceable to a named monotherapy anchor recorded in the configuration's calibration-provenance block.

Comparing a completed prediction against a published combination observation is validation, not calibration, and is permitted — no parameter is adjusted to it. Where such a comparison was made it is reported as a test of the prediction, and the prediction itself is unchanged by the outcome.

> **Provenance.** `config.no_pair_feedback.rule`; `config.no_pair_feedback.voids_study`

## Figure legends

**Figure 1. Model and population validation.** *(A)* Reproduction of the six Fabbri (2017) Table 5 features by the Myokit-imported CellML; bars show signed percentage deviation, dashed guides at ±1%. Largest absolute deviation 0.99%. *(B)* Distribution of intrinsic rate across the 188 retained models (dashed line, median 82.2 beats·min⁻¹). Retention was 188/940 = 20.0% against 20.9% reported by Zhou et al.

**Figure 2. Quiescence-threshold distributions.** Fraction of the 188-model population in which automaticity is abolished, as a function of fractional block. *(A)* I_CaL: median threshold 40.0% (dashed line), IQR shaded; no model tolerates 90% block. *(B)* I_f: 176/188 (93.6%) never become quiescent even at 90% block; median and IQR are stated conditionally for the minority that do stop and are deliberately not drawn as a population band. The steepness of (A) is what makes any threshold-crossing endpoint sensitive to calibration.

**Figure 3. Excess absolute risk versus verapamil exposure, across three ivabradine anchors and four pharmacokinetic arms.** Columns are the three open-loop anchors (identity encoded by hue, stated in each column title); line shade and style encode CYP3A4-inhibited ivabradine exposure (ordinal). *(A)* control state, n = 188; *(B)* Iso 1 µM state, n = 168 models pacing drug-free. Shaded vertical bands are the chronic oral exposure ranges; dotted horizontal guides at 5% and 10% EAR. The 7× strong-inhibitor arm was run for the superseded anchor only and is shown where available. The decline at the highest exposures is the ceiling effect described in Methods, not a reduction in risk.

**Figure 4. Bliss independence is not a usable null on a threshold endpoint.** Panels show the **verapamil × ivabradine** pair with ivabradine held at a fixed I_f block of 31.2% and verapamil laddered — a single-drug exposure ladder, NOT the four-pair invariance sweep in which both agents are scaled together. The two analyses give different and non-contradictory answers and must not be conflated: under the both-agents-scaled sweep this pair classifies as additive at all four informative rungs, whereas along the verapamil-only ladder shown here the classification alternates. *(A)* Paired excess absolute risk with Wilson 95% CI; the rescue fraction — models failing a single agent but pacing under the combination — is zero at every rung, so the endpoint is monotone. *(B)* Bliss classification of the same rows, alternating non-monotonically along the ladder although verapamil and ivabradine act on different channels and the model contains no interaction between them. Every departure from additivity is produced by the geometry of the threshold distribution in Figure 2A.

> **Caveat carried with this figure.** It is drawn from the Task G pair prediction, in which ivabradine is fixed at the **superseded 31.2% anchor**, not the primary 58.4% anchor used for every other result. It is retained as an endpoint-geometry demonstration, for which the anchor is immaterial, but it must not be presented as a primary-anchor result. Regenerating it at the primary anchor requires no new simulation — the conditions exist in the store — and should be done before submission.

For the four-pair invariance analysis (both agents scaled together), the manifest records: **not invariant** — diltiazem × verapamil (6 informative rungs, additive ↔ super-additive) and diltiazem × ivabradine (7 rungs, sub-additive ↔ additive); **invariant** — verapamil × mexiletine (5 rungs, super-additive throughout) and verapamil × ivabradine (4 rungs, additive throughout).

## Data and code availability

All frozen outputs, the 142-entry values manifest mapping every reported number to its source file and generating script, and the scripts that produce the figures are included with the submission. The drug simulation store comprises 59,784 unique simulations.

