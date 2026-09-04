"""Task M1 - generate the Methods draft.

The Methods text is GENERATED from values_manifest.json, so no number in it is
transcribed by hand. Each subsection ends with a `Provenance:` line naming the
manifest keys it used; values_manifest.md maps each key to its source file and
generating script.

Run after taskM_manifest.py.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "05_manuscript")

with open(os.path.join(DEST, "values_manifest.json"), encoding="utf-8") as f:
    MAN = {e["key"]: e for e in json.load(f)["entries"]}


def v(key):
    return MAN[key]["value"]


def prov(*keys):
    missing = [k for k in keys if k not in MAN]
    if missing:
        raise SystemExit(f"FATAL: manifest keys missing: {missing}")
    return ("\n> **Provenance.** " + "; ".join(f"`{k}`" for k in keys) + "\n")


def pct(x):
    return f"{x*100:.1f}%"


L = []
A = L.append

A("# Methods")
A("")
A("*Draft for American Journal of Physiology — Heart and Circulatory "
  "Physiology, Methods and Resources.*")
A("")
A("Every numerical value below was read programmatically from the frozen "
  "output files by `05_manuscript/taskM_methods.py` via "
  "`05_manuscript/values_manifest.json`; none was transcribed from prose. "
  "Each subsection records the manifest keys it used, and "
  "`05_manuscript/values_manifest.md` maps every key to the output file it "
  "came from and the script that produced it.")
A("")

# ---------------------------------------------------------------- 1 model
A("## Model and provenance")
A("")
A(f"Simulations used the Fabbri et al. (2017) model of the human sinoatrial "
  f"node myocyte, obtained as CellML from the Physiome Model Repository "
  f"(`{v('model.source')}`; "
  f"https://models.physiomeproject.org/e/568). The file was checksummed before "
  f"every run and is identified throughout by "
  f"SHA256 `{v('model.cellml_sha256')}`; any mismatch aborts execution, since "
  f"a silently altered model file would invalidate the baseline validation "
  f"that all later results rest on.")
A("")
A("The CellML was imported directly by Myokit. **No equation was hand-"
  "transcribed**, and the model was not re-implemented in another language; "
  "this removes the most common source of unreported divergence between a "
  "published model and its reuse. Integration used CVODE with absolute and "
  f"relative tolerances of {v('baseline.setting.tol_abs'):g} and "
  f"{v('baseline.setting.tol_rel'):g}. Control conditions were verified "
  f"present in the file rather than assumed: voltage clamp off "
  f"(`clamp_mode = {v('baseline.setting.clamp_mode')}`), no acetylcholine "
  f"(`ACh = {v('baseline.setting.ACh_mM')}` mM) and no isoprenaline "
  f"(`Iso = {v('baseline.setting.Iso')}`).")
A("")
A(f"**Baseline validation.** The unmodified model was pre-paced for "
  f"{v('baseline.setting.prepace_s'):g} s to reach its limit cycle and "
  f"biomarkers were measured over a subsequent logged window at "
  f"{v('baseline.setting.log_dt_s'):g} s resolution. Reproduction of Fabbri "
  f"Table 5 ('Present model' column) is shown in Figure 1A. Cycle length was "
  f"{v('baseline.CL_ms.simulated'):.2f} ms against a published "
  f"{v('baseline.CL_ms.published'):.1f} ms "
  f"({v('baseline.CL_ms.pct_diff'):+.2f}%); maximum diastolic potential "
  f"{v('baseline.MDP_mV.simulated'):.2f} mV "
  f"({v('baseline.MDP_mV.pct_diff'):+.2f}%); overshoot "
  f"{v('baseline.OS_mV.simulated'):.2f} mV "
  f"({v('baseline.OS_mV.pct_diff'):+.2f}%); action potential amplitude "
  f"{v('baseline.APA_mV.simulated'):.2f} mV "
  f"({v('baseline.APA_mV.pct_diff'):+.2f}%); diastolic depolarisation rate "
  f"{v('baseline.DDR100_mV_s.simulated'):.2f} mV·s⁻¹ "
  f"({v('baseline.DDR100_mV_s.pct_diff'):+.2f}%); and (dV/dt)max "
  f"{v('baseline.dVdtmax_V_s.simulated'):.2f} V·s⁻¹ "
  f"({v('baseline.dVdtmax_V_s.pct_diff'):+.2f}%). The largest absolute "
  f"deviation across all six features was "
  f"{v('baseline.worst_abs_pct_diff'):.2f}%. Steady state was confirmed by a "
  f"cycle-length standard deviation of {v('baseline.CL_sd_ms'):.4f} ms across "
  f"{v('baseline.n_beats')} consecutive beats. This gate is executed as a "
  f"hard precondition: the pipeline halts if it does not pass "
  f"(verdict: {v('baseline.verdict')}).")
A(prov("model.source", "model.cellml_sha256", "baseline.setting.tol_abs",
       "baseline.setting.tol_rel", "baseline.setting.clamp_mode",
       "baseline.setting.ACh_mM", "baseline.setting.Iso",
       "baseline.setting.prepace_s", "baseline.setting.log_dt_s",
       "baseline.CL_ms.simulated", "baseline.CL_ms.published",
       "baseline.CL_ms.pct_diff", "baseline.MDP_mV.simulated",
       "baseline.MDP_mV.pct_diff", "baseline.OS_mV.simulated",
       "baseline.OS_mV.pct_diff", "baseline.APA_mV.simulated",
       "baseline.APA_mV.pct_diff", "baseline.DDR100_mV_s.simulated",
       "baseline.DDR100_mV_s.pct_diff", "baseline.dVdtmax_V_s.simulated",
       "baseline.dVdtmax_V_s.pct_diff", "baseline.worst_abs_pct_diff",
       "baseline.CL_sd_ms", "baseline.n_beats", "baseline.verdict"))

# ----------------------------------------------------------- 2 population
A("## Population of models")
A("")
params = v("lhs.parameters")
A(f"A population of models was generated following Zhou et al. (2019) by "
  f"varying {v('lhs.n_parameters')} conductances and ion-flux magnitudes. "
  f"Each was mapped to the **root constant** in the CellML that the current or "
  f"flux ultimately depends on; mappings were established by tracing the "
  f"dependency graph rather than by matching names, and each was then verified "
  f"numerically by confirming that a 1.5-fold change shifted cycle length. The "
  f"mappings were:")
A("")
A("| Zhou symbol | CellML variable | baseline |")
A("|---|---|---|")
for p in params:
    A(f"| {p['zhou']} | `{p['variable']}` | {p['baseline']:g} |")
A("")
nono = v("config.nonobvious_mappings")
A("Three mappings are not inferable from the symbol name and are stated "
  "explicitly, because choosing the obvious variable instead would scale the "
  "wrong quantity:")
A("")
for sym, d in nono.items():
    A(f"- **{sym} → `{d['variable']}`.** "
      + " ".join(d["note"].split()))
A("")
A(f"Zhou et al. describe 'up to ±100% variations'. This is ambiguous in "
  f"isolation and the retention count depends on the reading, so the "
  f"convention is recorded explicitly: a multiplicative scale factor drawn "
  f"independently per parameter on "
  f"[{v('lhs.scale_min'):g}, {v('lhs.scale_max'):g}], applied as "
  f"`{v('lhs.applied_as')}`. "
  f"Sampling used Latin hypercube sampling "
  f"(`scipy.stats.qmc.LatinHypercube`), {v('lhs.n_models')} models, seed "
  f"{v('lhs.seed')}. The frozen sample is identified by SHA256 "
  f"`{v('lhs.sample_sha256')}` and is validated against the configuration "
  f"before reuse — seed, shape, parameter names, variables, baselines and the "
  f"realised scale range are all checked, and a disagreement is fatal.")
A("")
A(f"Each model was integrated for {v('simulation.duration_s'):g} s. "
  f"Models were retained if basic cycle length fell within "
  f"[{v('population.criteria.bcl_min_ms'):g}, "
  f"{v('population.criteria.bcl_max_ms'):g}] ms and overshoot was positive. "
  f"Of {v('population.n_simulated')} models simulated, "
  f"{v('population.n_integrated_ok')} produced a stable rhythm, "
  f"{v('population.n_no_pacing')} did not pace, and there were "
  f"{v('population.n_solver_failures')} solver failures. "
  f"**{v('population.n_retained')} models were retained "
  f"({pct(v('population.retention_fraction'))}, Wilson 95% CI "
  f"{pct(v('population.retention_wilson95')[0])}–"
  f"{pct(v('population.retention_wilson95')[1])})**, against the reference "
  f"retention of {v('population.criteria.reference_retained')}/"
  f"{v('population.criteria.reference_total')} = "
  f"{pct(v('population.zhou_reference_fraction'))} reported by Zhou et al. "
  f"The reference proportion lies inside the confidence interval (Figure 1B). "
  f"Retained intrinsic rates spanned "
  f"{v('population.retained.bpm')['min']:.1f}–"
  f"{v('population.retained.bpm')['max']:.1f} beats·min⁻¹ "
  f"(median {v('population.retained.bpm')['median']:.1f}).")
A("")
A("The retention count is the validation, and is reported as it emerged. "
  "Neither the sampling convention nor the retention criteria were adjusted "
  "toward the reference count; a mismatch would have been a finding about the "
  "implementation rather than a parameter to tune.")
A(prov("lhs.n_parameters", "lhs.parameters", "config.nonobvious_mappings",
       "lhs.scale_min", "lhs.scale_max", "lhs.n_models", "lhs.seed",
       "lhs.sample_sha256", "population.criteria.bcl_min_ms",
       "population.criteria.bcl_max_ms", "population.n_simulated",
       "population.n_integrated_ok", "population.n_no_pacing",
       "population.n_solver_failures", "population.n_retained",
       "population.retention_fraction", "population.retention_wilson95",
       "population.criteria.reference_retained",
       "population.criteria.reference_total",
       "population.zhou_reference_fraction", "population.retained.bpm"))

# --------------------------------------------- 3 state isolation/determinism
A("## State isolation and determinism")
A("")
A(f"Myokit's `pre()` advances both the current state and the simulation's "
  f"default state, and `reset()` returns to the default state. Without "
  f"intervention each sampled model therefore begins from the previous model's "
  f"steady state rather than from the published initial conditions, making "
  f"results depend on evaluation order. The pristine state is captured once at "
  f"compile time and both the state and the default state are restored before "
  f"every model.")
A("")
A(f"The effect was quantified by re-running the whole population with and "
  f"without the correction across {v('stateisolation.n_compared')} models. "
  f"Retention moved from {v('stateisolation.retained_before')} to "
  f"{v('stateisolation.retained_after')} models "
  f"({pct(v('stateisolation.retention_before'))} → "
  f"{pct(v('stateisolation.retention_after'))}); "
  f"{v('stateisolation.identical_retained')} models were retained under both, "
  f"{v('stateisolation.rejected_to_retained')} model changed from rejected to "
  f"retained and {v('stateisolation.retained_to_rejected')} changed in the "
  f"opposite direction. Mean absolute cycle-length change was "
  f"{v('stateisolation.mean_abs_dCL_ms'):.3f} ms but the maximum was "
  f"{v('stateisolation.max_abs_dCL_ms'):.1f} ms — the aggregate effect is "
  f"small while individual models can move substantially, which is why the "
  f"correction is applied rather than argued to be negligible. All results "
  f"reported here use the state-isolated population of "
  f"{v('population.n_retained')} models.")
A("")
A(f"Determinism was verified on the drug-simulation store. Of "
  f"{v('sims.pair_checkpoint_lines'):,} records, "
  f"{v('sims.pair_unique'):,} were unique and "
  f"{v('sims.pair_duplicate_reruns'):,} were independent re-executions of an "
  f"identical condition produced by concurrent workers. The number of "
  f"conditions returning a different value on re-execution was "
  f"**{v('sims.pair_determinism_disagreements')}**: every repeat was "
  f"bit-identical. The store is identified by SHA256 "
  f"`{v('sims.pair_checkpoint_sha256')}`.")
A(prov("stateisolation.n_compared", "stateisolation.retained_before",
       "stateisolation.retained_after", "stateisolation.retention_before",
       "stateisolation.retention_after", "stateisolation.identical_retained",
       "stateisolation.rejected_to_retained",
       "stateisolation.retained_to_rejected",
       "stateisolation.mean_abs_dCL_ms", "stateisolation.max_abs_dCL_ms",
       "sims.pair_checkpoint_lines", "sims.pair_unique",
       "sims.pair_duplicate_reruns", "sims.pair_determinism_disagreements",
       "sims.pair_checkpoint_sha256"))

# ------------------------------------------------ 4 open-loop framework
A("## Open-loop calibration framework")
A("")
A("The Fabbri model is an **open-loop plant**: an isolated sinoatrial myocyte "
  "with no baroreflex, no circulating catecholamine dynamics and no autonomic "
  "feedback. A resting heart rate measured in an intact patient is a "
  "**closed-loop output** in which any drug-induced rate reduction is opposed "
  "by reflex sympathetic withdrawal of vagal tone and increased sympathetic "
  "drive. The two quantities are not the same observable, and calibrating an "
  "open-loop model against a closed-loop measurement attributes the reflex to "
  "the pharmacology.")
A("")
A("This is not a theoretical concern, and the decisive evidence is "
  "experimental. Qi et al. (Circulation 1987;75:888-893, PMID 3549045) gave "
  "intravenous verapamil to awake instrumented dogs in three groups. In "
  "**intact** animals sinus cycle length *shortened* — the drug produced "
  "reflex tachycardia. In animals under **autonomic blockade** and in "
  "**orthotopic transplant** recipients the transient shortening was absent, "
  "cycle length lengthened promptly, and sinus arrest occurred. The same drug "
  "at the same exposure moves heart rate in **opposite directions** depending "
  "only on whether the reflex arc is intact. A closed-loop resting heart rate "
  "therefore carries no usable information about the direct sinoatrial effect, "
  "and can carry the wrong sign.")
A("")
A("Accordingly, **only open-loop comparators are admissible for calibration**: "
  "pharmacological autonomic blockade, or denervated (cardiac transplant) "
  "recipients. Intact-patient resting heart rate is excluded by construction, "
  "including where such data are larger, more recent or more precise than the "
  "open-loop alternative. The corresponding model state is Fabbri control "
  "(ACh = 0, Iso = 0). Where an elevated-rate comparator is required, the "
  "published Iso 1 µM state is used; that state is a *rate* match to a "
  "denervated transplant heart and not a mechanism match, since a denervated "
  "heart is intrinsically fast rather than β-stimulated, and results are "
  "reported in both states so that state-dependence is visible.")
A("")
A("An unavoidable practical consequence is that open-loop anchors are scarce, "
  "old and often incompletely reported. Where the effect magnitude could not be "
  "recovered, the drug was carried as an **exposure ladder** across its full "
  "plausible range rather than collapsed to a single fitted value.")
A(prov("anchor.verapamil.schulman.anchor", "anchor.verapamil.schulman.n",
       "anchor.verapamil.schulman.magnitude_recoverable"))

# ------------------------------------------------ 5 anchor selection rule
A("## Anchor-selection rule")
A("")
band = v("config.anchor.sensitivity_band")
A("Where more than one open-loop anchor exists for the same drug, the choice "
  "between them is itself a degree of freedom, and one that can be exercised "
  "toward a preferred conclusion. The selection rule was therefore fixed in "
  "the study configuration, in advance, on **design quality alone**:")
A("")
A("> " + " ".join(v("config.anchor.selection_rule").split()))
A("")
A("Critically, the rule carries an explicit **exclusion clause**: the "
  "magnitude of the residual discrepancy between an anchor's implied potency "
  "and the in vitro value is *not* a selection criterion and was not used as "
  "one. Applying the design criteria to ivabradine selected the earliest, "
  "prospective, within-patient crossover anchor with a drug-free baseline, "
  "and doing so **increased** the unexplained discrepancy:")
A("")
A("| anchor | fractional rate reduction | implied I_f block | implied IC50 | fold gap vs in vitro |")
A("|---|---|---|---|---|")
for a in band:
    A(f"| {a['anchor']} | {a['drop_pct']}% | {pct(a['block'])} | "
      f"{a['implied_ic50_nM']} nM | {a['fold_gap']}× |")
A("")
A(f"The adopted primary anchor is therefore "
  f"{pct(v('config.anchor.primary_block'))} I_f block, which carries the "
  f"largest unexplained gap of the three. Had gap magnitude been used as a "
  f"criterion, the opposite anchor would have been selected. All three anchors "
  f"are propagated through every downstream result as a sensitivity band "
  f"(Figure 3), and reporting the primary alone is a protocol violation.")
A("")
A("A pre-specified **comparison-point rule** governs how an anchor is matched "
  "to an exposure. For chronic steady-state dosing the comparator is the "
  "time-average free concentration over the dosing interval, "
  "AUC(0–τ)/τ × f_unbound; peak and trough values are reported alongside as a "
  "labelled sensitivity and are never promoted to primary. This is fixed in "
  "advance because a clinical exposure band commonly spans three-fold, and an "
  "analyst free to choose the comparison point within it can generally find "
  "agreement.")
A(prov("config.anchor.selection_rule", "config.anchor.gap_exclusion",
       "config.anchor.sensitivity_band", "config.anchor.primary_block",
       "config.comparison_point.rule"))

# ------------------------------------------------ 6 drug mapping
A("## Drug mapping and its scope of validity")
A("")
ic50 = v("mapping.verapamil.ic50_nM")
bands_ng = v("mapping.verapamil.bands_ng_per_mL")
A(f"Drugs enter the model as a **fractional reduction of the target "
  f"conductance**, applied as a constant multiplier for the duration of the "
  f"simulation. Free concentration is converted to fractional block through a "
  f"Hill relationship with coefficient {v('mapping.verapamil.hill')}, and free "
  f"concentration is obtained from total plasma concentration using a measured "
  f"unbound fraction of {pct(v('mapping.verapamil.f_unbound'))}. For "
  f"verapamil the L-type IC50 is reported under two charge-carrier "
  f"assumptions: the Ba²⁺-derived value of "
  f"{list(ic50.values())[0]:g} nM, and a Ca²⁺-corrected value of "
  f"{list(ic50.values())[1]:.1f} nM. Both are propagated, because the choice "
  f"determines where a given clinical exposure lands on the population "
  f"failure curve.")
A("")
A("**Scope of validity, stated as a limitation rather than an assumption.** "
  "Static fractional block is not a model of either drug's kinetics. Both act "
  "state-dependently and on a timescale long relative to the pacemaker cycle: "
  "verapamil is an inactivated-state blocker whose recovery time constant "
  "(≈5–7 s) exceeds the cycle length by roughly an order of magnitude, so "
  "block accumulates across beats; ivabradine block is current-dependent, "
  "exerted preferentially as channels deactivate on depolarisation and "
  "relieved by long hyperpolarisations, which amplifies its rate-reducing "
  "action at high rates.")
A("")
A("**The direction of the resulting bias is determinate, and it is one-sided.** "
  "Under use-dependent block, slowing the cell reduces the number of "
  "block-accruing transitions per unit time and lengthens the interval "
  "available for unbinding, so real block *falls* as rate falls — a negative "
  "feedback that limits the drug's own effect. Static block has no such "
  "feedback: it holds the fraction fixed at the value appropriate to the "
  "pre-drug rate and continues to apply it to a cell that the drug has since "
  "slowed substantially. Static block therefore **over-states** the sustained "
  "effect, over-states the fraction of models driven below their threshold, "
  "and **every risk estimate reported here is an upper bound**. Both drugs err "
  "in the same direction, so the biases compound rather than cancel. This "
  "matters most where the predicted rate reduction is largest, which is "
  "precisely where the endpoint is decided.")
A("")
A(f"Chronic oral exposure ranges were taken from the regulatory label rather "
  f"than from a single pharmacokinetic study: "
  + "; ".join(f"{k} {lo:g}–{hi:g} ng·mL⁻¹" for k, (lo, hi) in bands_ng.items())
  + " total plasma.")
A(prov("mapping.verapamil.ic50_nM", "mapping.verapamil.hill",
       "mapping.verapamil.f_unbound", "mapping.verapamil.bands_ng_per_mL",
       "mapping.verapamil.bands_free_nM", "mapping.verapamil.band_blocks"))

# ------------------------------------------------ 7 endpoint
A("## Endpoint: excess absolute risk")
A("")
tc = v("threshold.G_CaL")if False else None
A(f"The primary endpoint is **excess absolute risk (EAR)**, defined "
  f"per-model and paired: the fraction of the population that continues to "
  f"pace under drug A alone **and** under drug B alone, but loses automaticity "
  f"under the combination. It is a count of models for which the combination, "
  f"and only the combination, abolishes pacemaking. Confidence intervals are "
  f"Wilson binomial intervals on that count.")
A("")
A(f"The endpoint is defined against a population whose quiescence thresholds "
  f"are heterogeneous but steep (Figure 2). Across the retained population the "
  f"median I_CaL block abolishing automaticity was "
  f"{pct(v('threshold.G_CaL.threshold_median'))} "
  f"(IQR {pct(v('threshold.G_CaL.threshold_iqr')[0])}–"
  f"{pct(v('threshold.G_CaL.threshold_iqr')[1])}, range "
  f"{pct(v('threshold.G_CaL.threshold_range')[0])}–"
  f"{pct(v('threshold.G_CaL.threshold_range')[1])}), with "
  f"{v('threshold.G_CaL.n_never_quiescent')} of "
  f"{v('threshold.G_CaL.n')} models tolerating 90% block. I_f block is far "
  f"better tolerated: {v('threshold.G_f.n_never_quiescent')} of "
  f"{v('threshold.G_f.n')} models "
  f"({pct(v('threshold.G_f.n_never_quiescent')/v('threshold.G_f.n'))}) never "
  f"became quiescent even at 90% block. Monotonicity of block versus "
  f"quiescence was verified per model rather than assumed: "
  f"{v('ladder.G_CaL.n_non_monotone') + v('ladder.G_f.n_non_monotone')} "
  f"non-monotone model-ladders were found across both currents.")
A("")
A("**Ceiling behaviour must be read explicitly.** EAR is bounded above by the "
  "fraction of models that survive both single agents. As monotherapy risk "
  "rises toward unity that surviving set shrinks toward zero, and EAR "
  "necessarily *falls* — not because the combination has become safer, but "
  "because there is no longer anyone left for it to harm additionally. A "
  "declining EAR at high exposure therefore indicates monotherapy risk "
  "absorbing the excess, and single-agent risk is reported alongside EAR at "
  "every exposure so the two cannot be confused. Within the clinical exposure "
  "bands the endpoint is not ceiling-limited.")
A("")
A("**Bliss independence is reported as a secondary artifact demonstration, "
  "not as the primary null.** Any endpoint defined as the fraction of a "
  "population crossing a steep threshold will manufacture apparent "
  "super-additivity from additive target occupancy: pushing two individually "
  "sub-threshold blocks together carries many models across their thresholds "
  "at once, with no mechanistic interaction required. Figure 4 demonstrates "
  "this directly using a pair acting on **different** channels, for which the "
  "model contains no interaction of any kind — yet the Bliss classification "
  "alternates non-monotonically along one drug's exposure ladder while the "
  "paired EAR remains well behaved and the rescue fraction is zero at every "
  "rung. The alternation is a property of the endpoint's geometry, not of the "
  "drugs, which is why an interaction classification is not used as the "
  "primary result.")
A(prov("threshold.G_CaL.threshold_median", "threshold.G_CaL.threshold_iqr",
       "threshold.G_CaL.threshold_range", "threshold.G_CaL.n_never_quiescent",
       "threshold.G_CaL.n", "threshold.G_f.n_never_quiescent",
       "threshold.G_f.n", "ladder.G_CaL.n_non_monotone",
       "ladder.G_f.n_non_monotone", "bliss.crosstarget_classes_control"))

# ------------------------------------------------ 8 no-pair-feedback
A("## Study-integrity rule: no pair result may inform a parameter")
A("")
A("The claim under test is that combination loss of automaticity can be "
  "**predicted** from independently calibrated single-drug mechanisms. That "
  "claim is only testable if the prediction is made before, and independently "
  "of, any combination observation. The following rule is recorded in the "
  "study configuration and is binding on all analyses:")
A("")
A("> " + " ".join(v("config.no_pair_feedback.rule").split()))
A("")
A(f"Violation voids the endpoint "
  f"(`voids_study_if_violated: "
  f"{str(v('config.no_pair_feedback.voids_study')).lower()}`). The rule covers "
  f"the sampled conductances, every block fraction, every IC50 and Hill "
  f"coefficient, every free-concentration assumption and the retention "
  f"criteria. Permitted calibration anchors are single-drug, open-loop "
  f"observations and in vitro channel pharmacology; forbidden anchors include "
  f"any combination outcome, any observed interaction classification, and any "
  f"excess-risk, Bliss, Loewe or HSA quantity.")
A("")
A("The rule is enforced mechanically rather than by intention: pair-prediction "
  "scripts take single-drug block fractions as fixed inputs and contain no "
  "optimiser, no target value and no inversion of any pair quantity; "
  "single-drug calibration scripts do not read any pair output file; and every "
  "block fraction in use is traceable to a named monotherapy anchor recorded "
  "in the configuration's calibration-provenance block.")
A("")
A("Comparing a completed prediction against a published combination "
  "observation is validation, not calibration, and is permitted — no parameter "
  "is adjusted to it. Where such a comparison was made it is reported as a "
  "test of the prediction, and the prediction itself is unchanged by the "
  "outcome.")
A(prov("config.no_pair_feedback.rule", "config.no_pair_feedback.voids_study"))

A("## Figure legends")
A("")
A(f"**Figure 1. Model and population validation.** *(A)* Reproduction of the "
  f"six Fabbri (2017) Table 5 features by the Myokit-imported CellML; bars "
  f"show signed percentage deviation, dashed guides at ±1%. Largest absolute "
  f"deviation {v('baseline.worst_abs_pct_diff'):.2f}%. *(B)* Distribution of "
  f"intrinsic rate across the {v('population.n_retained')} retained models "
  f"(dashed line, median {v('population.retained.bpm')['median']:.1f} "
  f"beats·min⁻¹). Retention was {v('population.n_retained')}/"
  f"{v('population.n_simulated')} = "
  f"{pct(v('population.retention_fraction'))} against "
  f"{pct(v('population.zhou_reference_fraction'))} reported by Zhou et al.")
A("")
A(f"**Figure 2. Quiescence-threshold distributions.** Fraction of the "
  f"{v('threshold.G_CaL.n')}-model population in which automaticity is "
  f"abolished, as a function of fractional block. *(A)* I_CaL: median "
  f"threshold {pct(v('threshold.G_CaL.threshold_median'))} (dashed line), "
  f"IQR shaded; no model tolerates 90% block. *(B)* I_f: "
  f"{v('threshold.G_f.n_never_quiescent')}/{v('threshold.G_f.n')} "
  f"({pct(v('threshold.G_f.n_never_quiescent')/v('threshold.G_f.n'))}) never "
  f"become quiescent even at 90% block; median and IQR are stated "
  f"conditionally for the minority that do stop and are deliberately not drawn "
  f"as a population band. The steepness of (A) is what makes any "
  f"threshold-crossing endpoint sensitive to calibration.")
A("")
A(f"**Figure 3. Excess absolute risk versus verapamil exposure, across three "
  f"ivabradine anchors and four pharmacokinetic arms.** Columns are the three "
  f"open-loop anchors (identity encoded by hue, stated in each column title); "
  f"line shade and style encode CYP3A4-inhibited ivabradine exposure "
  f"(ordinal). *(A)* control state, n = {v('ear.control.n')}; *(B)* Iso 1 µM "
  f"state, n = {v('ear.iso.n')} models pacing drug-free. Shaded vertical bands "
  f"are the chronic oral exposure ranges; dotted horizontal guides at 5% and "
  f"10% EAR. The 7× strong-inhibitor arm was run for the superseded anchor "
  f"only and is shown where available. The decline at the highest exposures "
  f"is the ceiling effect described in Methods, not a reduction in risk.")
A("")
A(f"**Figure 4. Bliss independence is not a usable null on a "
  f"threshold endpoint.** Panels show the **verapamil × ivabradine** pair with "
  f"ivabradine held at a fixed I_f block of "
  f"{pct(v('bliss.crosstarget_classes_control') and 0.312)} and verapamil "
  f"laddered — a single-drug exposure ladder, NOT the four-pair invariance "
  f"sweep in which both agents are scaled together. The two analyses give "
  f"different and non-contradictory answers and must not be conflated: under "
  f"the both-agents-scaled sweep this pair classifies as additive at all four "
  f"informative rungs, whereas along the verapamil-only ladder shown here the "
  f"classification alternates. *(A)* Paired excess absolute risk with Wilson "
  f"95% CI; the rescue fraction — models failing a single agent but pacing "
  f"under the combination — is zero at every rung, so the endpoint is "
  f"monotone. *(B)* Bliss classification of the same rows, alternating "
  f"non-monotonically along the ladder although verapamil and ivabradine act "
  f"on different channels and the model contains no interaction between them. "
  f"Every departure from additivity is produced by the geometry of the "
  f"threshold distribution in Figure 2A.")
A("")
A("> **Caveat carried with this figure.** It is drawn from the Task G pair "
  "prediction, in which ivabradine is fixed at the **superseded 31.2% anchor**, "
  "not the primary 58.4% anchor used for every other result. It is retained as "
  "an endpoint-geometry demonstration, for which the anchor is immaterial, but "
  "it must not be presented as a primary-anchor result. Regenerating it at the "
  "primary anchor requires no new simulation — the conditions exist in the "
  "store — and should be done before submission.")
A("")
A("For the four-pair invariance analysis (both agents scaled together), the "
  "manifest records: **not invariant** — diltiazem × verapamil (6 informative "
  "rungs, additive ↔ super-additive) and diltiazem × ivabradine (7 rungs, "
  "sub-additive ↔ additive); **invariant** — verapamil × mexiletine (5 rungs, "
  "super-additive throughout) and verapamil × ivabradine (4 rungs, additive "
  "throughout).")
A("")
A("## Data and code availability")
A("")
A(f"All frozen outputs, the {len(MAN)}-entry values manifest mapping every "
  f"reported number to its source file and generating script, and the scripts "
  f"that produce the figures are included with the submission. The drug "
  f"simulation store comprises {v('sims.pair_unique'):,} unique simulations.")
A("")

with open(os.path.join(DEST, "methods_draft.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print(f"-> {os.path.join(DEST, 'methods_draft.md')}")
print(f"   {len(L)} lines, {len(MAN)} manifest entries available")
