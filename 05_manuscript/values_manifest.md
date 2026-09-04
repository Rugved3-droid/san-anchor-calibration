# Values manifest

Every number destined for the manuscript, read programmatically from the frozen outputs by `05_manuscript/taskM_manifest.py`. No value is transcribed from a task report's prose.

**151 entries.**

| key | value | source file | generating script | note |
|---|---|---|---|---|
| `model.cellml_sha256` | 9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec | `step3fix_run_statefix.json` | `03_population/run_population.py` | SHA256 of the Fabbri 2017 CellML actually used |
| `model.source` | HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml (PMR e/568) | `step1_baseline.json` | `01_baseline/run_baseline.py` | CellML provenance string (PMR exposure) |
| `model.reference` | Fabbri et al. 2017, J Physiol 595:2365-2396, Table 5, 'Present model' column | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 column used |
| `baseline.setting.prepace_s` | 500 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting prepace_s |
| `baseline.setting.log_dt_s` | 0.0001 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting log_dt_s |
| `baseline.setting.tol_abs` | 1e-08 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting tol_abs |
| `baseline.setting.tol_rel` | 1e-08 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting tol_rel |
| `baseline.setting.clamp_mode` | 0 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting clamp_mode |
| `baseline.setting.ACh_mM` | 0 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting ACh_mM |
| `baseline.setting.Iso` | 0 | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline run setting Iso |
| `baseline.CL_ms.published` | 814 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 CL_ms |
| `baseline.CL_ms.simulated` | 813.418 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced CL_ms |
| `baseline.CL_ms.pct_diff` | -0.0714764 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference CL_ms |
| `baseline.MDP_mV.published` | -58.9 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 MDP_mV |
| `baseline.MDP_mV.simulated` | -58.8853 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced MDP_mV |
| `baseline.MDP_mV.pct_diff` | 0.0249618 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference MDP_mV |
| `baseline.OS_mV.published` | 26.4 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 OS_mV |
| `baseline.OS_mV.simulated` | 26.4087 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced OS_mV |
| `baseline.OS_mV.pct_diff` | 0.0327761 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference OS_mV |
| `baseline.APA_mV.published` | 85.3 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 APA_mV |
| `baseline.APA_mV.simulated` | 85.294 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced APA_mV |
| `baseline.APA_mV.pct_diff` | -0.00709216 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference APA_mV |
| `baseline.DDR100_mV_s.published` | 48.1 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 DDR100_mV_s |
| `baseline.DDR100_mV_s.simulated` | 48.016 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced DDR100_mV_s |
| `baseline.DDR100_mV_s.pct_diff` | -0.174538 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference DDR100_mV_s |
| `baseline.dVdtmax_V_s.published` | 7.4 | `step1_baseline.json` | `01_baseline/run_baseline.py` | Fabbri Table 5 dVdtmax_V_s |
| `baseline.dVdtmax_V_s.simulated` | 7.47337 | `step1_baseline.json` | `01_baseline/run_baseline.py` | reproduced dVdtmax_V_s |
| `baseline.dVdtmax_V_s.pct_diff` | 0.991458 | `step1_baseline.json` | `01_baseline/run_baseline.py` | % difference dVdtmax_V_s |
| `baseline.worst_abs_pct_diff` | 0.991458 | `step1_baseline.json` | `01_baseline/run_baseline.py` | largest absolute % deviation across all Table 5 features |
| `baseline.n_beats` | 11 | `step1_baseline.json` | `01_baseline/run_baseline.py` | beats used for steady-state check |
| `baseline.CL_sd_ms` | 0.0385695 | `step1_baseline.json` | `01_baseline/run_baseline.py` | SD of cycle length across consecutive beats |
| `baseline.verdict` | PASS | `step1_baseline.json` | `01_baseline/run_baseline.py` | baseline gate outcome |
| `lhs.n_models` | 5000 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | LHS sample size |
| `lhs.n_parameters` | 12 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | number of varied mechanisms |
| `lhs.scale_min` | 0 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | multiplicative scaling lower bound |
| `lhs.scale_max` | 2 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | multiplicative scaling upper bound |
| `lhs.seed` | 20260816 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | RNG seed |
| `lhs.sample_sha256` | 681f8fc6b8963467ace9f047a37e5a599ec1b92fc8c87c9ccfac5f8b214b9d35 | `step2_sampling.json` | `02_sampling/generate_lhs.py` | SHA256 of the frozen LHS sample |
| `lhs.applied_as` | parameter_value = baseline_value * scale_factor | `step2_sampling.json` | `02_sampling/generate_lhs.py` | how the scale factor is applied |
| `lhs.parameters` | `[{"zhou": "G_f", "variable": "i_f.g_f", "baseline": 0.00427}, {"zhou": "G_CaL", "variab…` | `step2_sampling.json` | `02_sampling/generate_lhs.py` | the 12 mechanisms and their CellML variable mappings |
| `population.n_simulated` | 940 | `step3fix_run_statefix.json` | `03_population/run_population.py` | models actually integrated |
| `population.n_integrated_ok` | 539 | `step3fix_run_statefix.json` | `03_population/run_population.py` | models that produced a stable rhythm |
| `population.n_no_pacing` | 401 | `step3fix_run_statefix.json` | `03_population/run_population.py` | models that did not pace |
| `population.n_solver_failures` | 0 | `step3fix_run_statefix.json` | `03_population/run_population.py` | solver failures |
| `population.n_retained` | 188 | `step3fix_run_statefix.json` | `03_population/run_population.py` | models meeting the retention criteria |
| `population.retention_fraction` | 0.2 | `step3fix_run_statefix.json` | `03_population/run_population.py` | retained / simulated |
| `population.retention_wilson95` | `[0.175672688665853, 0.2267694160262903]` | `computed from step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | Wilson 95% CI on the retention proportion |
| `population.criteria.bcl_min_ms` | 600 | `step3fix_run_statefix.json` | `03_population/run_population.py` | retention criterion bcl_min_ms |
| `population.criteria.bcl_max_ms` | 1000 | `step3fix_run_statefix.json` | `03_population/run_population.py` | retention criterion bcl_max_ms |
| `population.criteria.overshoot_must_be_positive` | True | `step3fix_run_statefix.json` | `03_population/run_population.py` | retention criterion overshoot_must_be_positive |
| `population.criteria.reference_retained` | 1046 | `step3fix_run_statefix.json` | `03_population/run_population.py` | retention criterion reference_retained |
| `population.criteria.reference_total` | 5000 | `step3fix_run_statefix.json` | `03_population/run_population.py` | retention criterion reference_total |
| `population.zhou_reference_fraction` | 0.2092 | `step3fix_run_statefix.json` | `03_population/run_population.py` | Zhou et al. retention for comparison |
| `population.host` | `{"platform": "Windows-11-10.0.26200-SP0", "cpu_count": 8}` | `step3fix_run_statefix.json` | `03_population/run_population.py` | compute host |
| `population.retained_recount` | 188 | `step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | retention criteria re-applied to the raw per-model records (integrity check) |
| `population.retained.CL_ms` | `{"min": 602.15625, "max": 983.5555555555555, "mean": 759.7918708020703}` | `step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | retained-population CL_ms range (ms) |
| `population.retained.OS_mV` | `{"min": 2.693054596350604, "max": 41.667874465921194, "mean": 26.346639467014047}` | `step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | retained-population OS_mV range (mV) |
| `population.retained.MDP_mV` | `{"min": -70.5917242430783, "max": -38.92220524025835, "mean": -58.60741252060292}` | `step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | retained-population MDP_mV range (mV) |
| `population.retained.bpm` | `{"min": 61.00316312697696, "max": 99.64191187918418, "median": 82.20477715868}` | `step3fix_run_statefix.json` | `05_manuscript/taskM_manifest.py` | retained-population intrinsic rate |
| `stateisolation.n_compared` | 940 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: n_compared |
| `stateisolation.retained_before` | 187 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: retained_before |
| `stateisolation.retained_after` | 188 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: retained_after |
| `stateisolation.retention_before` | 0.198936 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: retention_before |
| `stateisolation.retention_after` | 0.2 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: retention_after |
| `stateisolation.identical_retained` | 187 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: identical_retained |
| `stateisolation.retained_to_rejected` | 0 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: retained_to_rejected |
| `stateisolation.rejected_to_retained` | 1 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: rejected_to_retained |
| `stateisolation.no_pacing_reclassifications` | 2 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: no_pacing_reclassifications |
| `stateisolation.max_abs_dCL_ms` | 241.45 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: max_abs_dCL_ms |
| `stateisolation.mean_abs_dCL_ms` | 0.909207 | `statefix_comparison.json` | `03_population/aggregate_and_freeze.py` | state-isolation before/after comparison: mean_abs_dCL_ms |
| `threshold.G_CaL.n` | 188 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: n |
| `threshold.G_CaL.n_never_quiescent` | 0 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: n_never_quiescent |
| `threshold.G_CaL.threshold_median` | 0.4 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: threshold_median |
| `threshold.G_CaL.threshold_iqr` | `[0.3, 0.5125]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: threshold_iqr |
| `threshold.G_CaL.threshold_range` | `[0.1, 0.8]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: threshold_range |
| `threshold.G_CaL.max_drop_median` | -36.4933 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: max_drop_median |
| `threshold.G_CaL.max_drop_iqr` | `[-47.000490539923334, -27.647470396046096]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: max_drop_iqr |
| `threshold.G_CaL.frac_reaching_-10bpm` | 0.994681 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL quiescence-threshold summary: frac_reaching_-10bpm |
| `threshold.G_CaL.fraction_pacing` | `{"0.3": 0.7180851063829787, "0.4": 0.46808510638297873, "0.5": 0.25, "0.6": 0.117021276…` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_CaL fraction of population still pacing per block level |
| `threshold.G_f.n` | 188 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: n |
| `threshold.G_f.n_never_quiescent` | 176 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: n_never_quiescent |
| `threshold.G_f.threshold_median` | 0.675 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: threshold_median |
| `threshold.G_f.threshold_iqr` | `[0.4375, 0.7625]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: threshold_iqr |
| `threshold.G_f.threshold_range` | `[0.25, 0.9]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: threshold_range |
| `threshold.G_f.max_drop_median` | -15.9089 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: max_drop_median |
| `threshold.G_f.max_drop_iqr` | `[-23.190129532926015, -7.4722221115085965]` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: max_drop_iqr |
| `threshold.G_f.frac_reaching_-10bpm` | 0.664894 | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f quiescence-threshold summary: frac_reaching_-10bpm |
| `threshold.G_f.fraction_pacing` | `{"0.3": 0.9946808510638298, "0.4": 0.9840425531914894, "0.5": 0.9787234042553191, "0.6"…` | `taskA_summary.json` | `04_pharmacology/taskA_analyse.py` | G_f fraction of population still pacing per block level |
| `ladder.G_CaL.n_models` | 188 | `taskA_G_CaL_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_CaL block-ladder metadata: n_models |
| `ladder.G_CaL.prepace_s` | 300 | `taskA_G_CaL_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_CaL block-ladder metadata: prepace_s |
| `ladder.G_CaL.n_non_monotone` | 0 | `taskA_G_CaL_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_CaL block-ladder metadata: n_non_monotone |
| `ladder.G_CaL.blocks` | `[0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75…` | `taskA_G_CaL_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_CaL block levels simulated |
| `ladder.G_f.n_models` | 188 | `taskA_G_f_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_f block-ladder metadata: n_models |
| `ladder.G_f.prepace_s` | 300 | `taskA_G_f_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_f block-ladder metadata: prepace_s |
| `ladder.G_f.n_non_monotone` | 0 | `taskA_G_f_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_f block-ladder metadata: n_non_monotone |
| `ladder.G_f.blocks` | `[0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75…` | `taskA_G_f_population_sweep.json` | `04_pharmacology/population_block_sweep.py` | G_f block levels simulated |
| `simulation.duration_s` | 1000 | `00_config/config.yaml` | `00_config/config.yaml (authored)` | per-model integration time used for population retention |
| `config.nonobvious_mappings` | `{"G_f": {"variable": "i_f.g_f", "note": "Root of the funny-current chain. g_f -> G_f ->…` | `00_config/config.yaml` | `00_config/config.yaml (authored)` | the three parameter mappings that are not inferable from the name |
| `config.no_pair_feedback.rule` | No quantity derived from a drug COMBINATION may be used, directly or indirectly, to set… | `00_config/config.yaml` | `00_config/config.yaml (authored)` | the no-pair-feedback integrity rule, verbatim |
| `config.no_pair_feedback.voids_study` | True | `00_config/config.yaml` | `00_config/config.yaml (authored)` | whether violation voids the study |
| `config.comparison_point.rule` | For any chronic, steady-state oral regimen, the model is evaluated at the TIME-AVERAGE … | `00_config/config.yaml` | `00_config/config.yaml (authored)` | pre-specified exposure comparator for chronic steady-state dosing |
| `config.anchor.selection_rule` | DESIGN QUALITY ONLY. The anchor is chosen on four design criteria and explicitly NOT on… | `00_config/config.yaml` | `00_config/config.yaml (authored)` | the four design criteria used to select the ivabradine anchor |
| `config.anchor.gap_exclusion` | The switch INCREASES the unexplained discrepancy against the in vitro IC50 from 61x to … | `00_config/config.yaml` | `00_config/config.yaml (authored)` | explicit exclusion of gap magnitude as a selection criterion |
| `config.anchor.primary_block` | 0.584 | `00_config/config.yaml` | `00_config/config.yaml (authored)` | adopted primary ivabradine I_f block |
| `config.anchor.sensitivity_band` | `[{"anchor": "Doesch 2007 8-week crossover (PRIMARY)", "drop_pct": 21.0, "block": 0.584,…` | `00_config/config.yaml` | `00_config/config.yaml (authored)` | all three anchors with implied IC50 and fold gap |
| `anchors.ivabradine` | `[{"label": "Doesch 2007  (PRIMARY)", "block_1x": 0.584, "arms": [0.584, 0.7097, 0.7717]…` | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | three open-loop ivabradine anchors: I_f block at 1x and the 1x/2x/3x arms |
| `anchor.verapamil.binding.measured_dog_bound_pct` | 90.7 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: measured_dog_bound_pct |
| `anchor.verapamil.binding.measured_dog_f_unbound` | 0.093 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: measured_dog_f_unbound |
| `anchor.verapamil.binding.human_f_unbound_same_assay` | 0.104 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: human_f_unbound_same_assay |
| `anchor.verapamil.binding.crosscheck_belpaire_f_unbound` | 0.15 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: crosscheck_belpaire_f_unbound |
| `anchor.verapamil.binding.f_unbound_needed_for_taskF_pass` | 0.2 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: f_unbound_needed_for_taskF_pass |
| `anchor.verapamil.binding.rescue_available` | False | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: rescue_available |
| `anchor.verapamil.binding.source` | Keefe DL, Yee YG, Kates RE. Clin Pharmacol Ther 1981;29(1):21-6. PMID 6970111 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: source |
| `anchor.verapamil.binding.crosscheck_source` | Belpaire FM et al. J Pharm Pharmacol 1990;42(1):45-9. PMID 1969949 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | verapamil protein binding: crosscheck_source |
| `anchor.verapamil.schulman.anchor` | Schulman DS et al. J Cardiovasc Pharmacol 1993;21(4):567-72. PMID 7681901 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: anchor |
| `anchor.verapamil.schulman.n` | 13 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: n |
| `anchor.verapamil.schulman.dose_mg_iv_median` | 4 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: dose_mg_iv_median |
| `anchor.verapamil.schulman.magnitude_recoverable` | False | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: magnitude_recoverable |
| `anchor.verapamil.schulman.pk_frame` | Reiter MJ et al. Am J Cardiol 1982;50(4):716-21. PMID 7124631 | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: pk_frame |
| `anchor.verapamil.schulman.assumed_total_ng_per_mL` | `[25, 80]` | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: assumed_total_ng_per_mL |
| `anchor.verapamil.schulman.implied_block_range` | `[0.02048704762841377, 0.06917522854591299]` | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: implied_block_range |
| `anchor.verapamil.schulman.observed_bound_0_of_13_ci` | `[0.0, 0.22810184305529166]` | `taskG_singles.json` | `04_pharmacology/taskG_singles.py` | Schulman open-loop anchor: observed_bound_0_of_13_ci |
| `mapping.verapamil.ic50_nM` | `{"Ba2+-derived (198.7 nM)": 198.7, "Ca2+-corrected (47.3 nM)": 47.3095238095238}` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | verapamil I_CaL IC50, Ba2+-derived and Ca2+-corrected |
| `mapping.verapamil.hill` | 1.09 | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | verapamil Hill coefficient |
| `mapping.verapamil.f_unbound` | 0.104 | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | human unbound fraction used |
| `mapping.verapamil.bands_ng_per_mL` | `{"240 mg/day": [35.0, 164.0], "480 mg/day": [125.0, 400.0]}` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | chronic oral total-plasma bands from the FDA label |
| `mapping.verapamil.bands_free_nM` | `{"240 mg/day": [8.007039155301364, 37.51869775626924], "480 mg/day": [28.59656841179058…` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | corresponding free concentrations |
| `mapping.verapamil.band_blocks` | `{"Ba2+-derived (198.7 nM)\|240 mg/day": [0.02929778407008014, 0.13979630222770817], "Ba2…` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | I_CaL block spanned by each band under each IC50 |
| `ear.control.n` | 188 | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | denominator: models pacing drug-free in the control state |
| `ear.control.band_thresholds` | `{"240 mg/day\|Doesch 2007  (PRIMARY)\|1x": {"max_EAR": 0.0425531914893617, "ci": [0.02171…` | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | max EAR inside each clinical band, per anchor and PK arm (control) |
| `ear.iso.n` | 168 | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | denominator: models pacing drug-free in the iso state |
| `ear.iso.band_thresholds` | `{"240 mg/day\|Doesch 2007  (PRIMARY)\|1x": {"max_EAR": 0.02976190476190476, "ci": [0.0127…` | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | max EAR inside each clinical band, per anchor and PK arm (iso) |
| `ear.bands_block` | `{"240 mg/day": [0.029, 0.14], "480 mg/day": [0.108, 0.3]}` | `taskL_three_anchor_EAR.json` | `04_pharmacology/taskL_analyse.py` | clinical bands expressed as I_CaL block |
| `bliss.n_models` | 188 | `taskE_interaction_invariance.json` | `04_pharmacology/taskE_interaction_invariance.py` | population size |
| `bliss.multipliers` | `[0.0625, 0.077, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0]` | `taskE_interaction_invariance.json` | `04_pharmacology/taskE_interaction_invariance.py` | exposure multipliers swept |
| `bliss.pairs` | `[{"pair": ["diltiazem", "verapamil"], "same_target": true, "classes_informative": ["SUP…` | `taskE_interaction_invariance.json` | `04_pharmacology/taskE_interaction_invariance.py` | Bliss classification invariance across exposure, per pair |
| `bliss.crosstarget_classes_control` | `[{"b_verapamil": 0.0, "class": "additive", "EAR": 0.0, "rescue": 0.0}, {"b_verapamil": …` | `taskG_pair_prediction.json` | `04_pharmacology/taskG_analyse.py` | Bliss class alternating along one drug's exposure ladder for a cross-target pair, with the paired EAR and rescue fraction alongside |
| `sims.pair_checkpoint_lines` | 65424 | `taskG_pair_checkpoint.jsonl` | `04_pharmacology/taskG_pair_prediction.py + taskH/taskI/taskL runners` | total records written across all pair runs |
| `sims.pair_unique` | 59784 | `taskG_pair_checkpoint.jsonl` | `05_manuscript/taskM_manifest.py` | unique (state, I_CaL block, I_f block, model) simulations |
| `sims.pair_duplicate_reruns` | 5640 | `taskG_pair_checkpoint.jsonl` | `05_manuscript/taskM_manifest.py` | records repeated by concurrent workers (independent re-executions) |
| `sims.pair_determinism_disagreements` | 0 | `taskG_pair_checkpoint.jsonl` | `05_manuscript/taskM_manifest.py` | repeat runs of the same (state, block, block, model) returning a different value; 0 = every re-execution was bit-identical |
| `sims.pair_checkpoint_sha256` | 661763c00f80fb3cec2f9da5f635ff39b703c3dc6e0d23aa9eb960fbc878c1fc | `taskG_pair_checkpoint.jsonl` | `05_manuscript/taskM_manifest.py` | checksum of the pair simulation store |
| `derived.anchor_ratio_2_3fold` | 2.30769 | `taskL_three_anchor_EAR.json` | `05_manuscript/taskM_manifest.py` | the 2.3-fold anchor-driven movement quoted in the abstract and discussion (primary / superseded, 480 mg/day, 1x, control) |
| `state_transfer.iso_baseline_bpm` | 93.9398 | `taskD_state_transfer.json` | `04_pharmacology/taskD_state_transfer.py` | elevated-rate baseline for the state-transfer test of static block |
| `state_transfer.control_baseline_bpm` | 68.7474 | `taskD_state_transfer.json` | `04_pharmacology/taskD_state_transfer.py` | control baseline for the state-transfer test of static block |
| `state_transfer.population_n` | 188 | `taskD_state_transfer.json` | `04_pharmacology/taskD_state_transfer.py` | population used for the state-transfer test |
| `state_transfer.strata_at_10bpm_calibration` | `{"<=74 bpm  (Boden: NO effect)": {"n": 57, "median_drop_bpm": -9.785220063772265}, "74-…` | `taskD_strata.json` | `04_pharmacology/taskD_strata.py` | median rate change by baseline-rate stratum at the -10 bpm calibration; supports the claim that a fixed block fraction does not transfer across rates |
| `ca_corrected.monotherapy_block_480` | `[0.3661583800669478, 0.6724090738477463]` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | I_CaL block spanned by 480 mg/day under the Ca2+-corrected IC50; underpins the self-falsifying characterisation |
| `ca_corrected.monotherapy_block_240` | `[0.12605867935842247, 0.43714903294245144]` | `taskH_exposure.json` | `04_pharmacology/taskH_analyse.py` | as above for 240 mg/day |
| `verapamil.ic50_sensitivity_202nM` | `{"ic50_old_nM": 198.7, "ic50_new_nM": 202.0, "n_headline_changes": 11, "bands": {"240 m…` | `07_v6_cleanup/verapamil_202nm_recompute.json` | `07_v6_cleanup/taskV6_verapamil_202nm_recompute.py` | sensitivity of the exposure->block mapping to substituting the CiPA tabulated 202 nM for the fitted 198.7 nM; NOT adopted, see audit |
| `endpoint.name` | excess model-quiescence fraction (EMQF) | `manuscript v6` | `07_v6_cleanup/taskV6_make_v6.py` | endpoint renamed from 'excess absolute risk' to avoid a patient-level reading; the underlying quantity and all values are unchanged |
