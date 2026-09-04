"""Task M3 - values manifest.

Every number destined for the manuscript, read PROGRAMMATICALLY from the frozen
output files. Nothing is copied from a task report's prose and nothing is typed
from memory. Each entry records:

    key          stable identifier used in the Methods draft
    value        the number/string as read
    source       the frozen output file it was read from
    script       the script that produced that file
    note         what it is

Two discrepancies between report prose and frozen data were found while building
this and are resolved in favour of the DATA:

  * retention is 188/940 = 20.0%, not the 187/19.89% quoted in README.md. The
    README figure predates the state-isolation fix; every task from A onward
    uses the 188-model population.
  * the integration counts are ok=539 / no_pacing=401, not 537/403.

Run:  python 05_manuscript/taskM_manifest.py
"""
import hashlib
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "05_manuscript")


def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        return json.load(f)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


M = []


def rec(key, value, source, script, note):
    M.append({"key": key, "value": value, "source": source,
              "script": script, "note": note})


# ---------------------------------------------------------------- A. model
b = load("step1_baseline.json")
s2 = load("step2_sampling.json")
s3 = load("step3fix_run_statefix.json")

rec("model.cellml_sha256", s3["cellml_sha256"], "step3fix_run_statefix.json",
    "03_population/run_population.py", "SHA256 of the Fabbri 2017 CellML actually used")
rec("model.source", b["model_source"], "step1_baseline.json",
    "01_baseline/run_baseline.py", "CellML provenance string (PMR exposure)")
rec("model.reference", b["reference"], "step1_baseline.json",
    "01_baseline/run_baseline.py", "Fabbri Table 5 column used")
for k in ("prepace_s", "log_dt_s", "tol_abs", "tol_rel", "clamp_mode",
          "ACh_mM", "Iso"):
    rec(f"baseline.setting.{k}", b["settings"][k], "step1_baseline.json",
        "01_baseline/run_baseline.py", f"baseline run setting {k}")

# ------------------------------------------------------- B. Table 5 gate
for feat, v in b["comparison"].items():
    rec(f"baseline.{feat}.published", v["published"], "step1_baseline.json",
        "01_baseline/run_baseline.py", f"Fabbri Table 5 {feat}")
    rec(f"baseline.{feat}.simulated", v["simulated"], "step1_baseline.json",
        "01_baseline/run_baseline.py", f"reproduced {feat}")
    rec(f"baseline.{feat}.pct_diff", v["pct"], "step1_baseline.json",
        "01_baseline/run_baseline.py", f"% difference {feat}")
rec("baseline.worst_abs_pct_diff",
    max(abs(v["pct"]) for v in b["comparison"].values()),
    "step1_baseline.json", "01_baseline/run_baseline.py",
    "largest absolute % deviation across all Table 5 features")
rec("baseline.n_beats", b["n_beats"], "step1_baseline.json",
    "01_baseline/run_baseline.py", "beats used for steady-state check")
rec("baseline.CL_sd_ms", b["CL_sd_ms"], "step1_baseline.json",
    "01_baseline/run_baseline.py", "SD of cycle length across consecutive beats")
rec("baseline.verdict", b["verdict"], "step1_baseline.json",
    "01_baseline/run_baseline.py", "baseline gate outcome")

# ------------------------------------------------------- C. population
rec("lhs.n_models", s2["n_models"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "LHS sample size")
rec("lhs.n_parameters", s2["n_parameters"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "number of varied mechanisms")
rec("lhs.scale_min", s2["scale_min"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "multiplicative scaling lower bound")
rec("lhs.scale_max", s2["scale_max"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "multiplicative scaling upper bound")
rec("lhs.seed", s2["seed"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "RNG seed")
rec("lhs.sample_sha256", s2["sample_sha256"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "SHA256 of the frozen LHS sample")
rec("lhs.applied_as", s2["applied_as"], "step2_sampling.json",
    "02_sampling/generate_lhs.py", "how the scale factor is applied")
rec("lhs.parameters", [{"zhou": p["zhou_symbol"], "variable": p["variable"],
                        "baseline": p["baseline"]} for p in s2["parameters"]],
    "step2_sampling.json", "02_sampling/generate_lhs.py",
    "the 12 mechanisms and their CellML variable mappings")

c = s3["counts"]
n_run = s3["n_models"]
lo, hi = wilson(c["retained"], n_run)
rec("population.n_simulated", n_run, "step3fix_run_statefix.json",
    "03_population/run_population.py", "models actually integrated")
rec("population.n_integrated_ok", c["ok"], "step3fix_run_statefix.json",
    "03_population/run_population.py", "models that produced a stable rhythm")
rec("population.n_no_pacing", c["no_pacing"], "step3fix_run_statefix.json",
    "03_population/run_population.py", "models that did not pace")
rec("population.n_solver_failures", c["solver_failure"],
    "step3fix_run_statefix.json", "03_population/run_population.py",
    "solver failures")
rec("population.n_retained", c["retained"], "step3fix_run_statefix.json",
    "03_population/run_population.py", "models meeting the retention criteria")
rec("population.retention_fraction", s3["retention_fraction"],
    "step3fix_run_statefix.json", "03_population/run_population.py",
    "retained / simulated")
rec("population.retention_wilson95", [lo, hi], "computed from "
    "step3fix_run_statefix.json", "05_manuscript/taskM_manifest.py",
    "Wilson 95% CI on the retention proportion")
for k in ("bcl_min_ms", "bcl_max_ms", "overshoot_must_be_positive",
          "reference_retained", "reference_total"):
    rec(f"population.criteria.{k}", s3["criteria"][k],
        "step3fix_run_statefix.json", "03_population/run_population.py",
        f"retention criterion {k}")
rec("population.zhou_reference_fraction",
    s3["criteria"]["reference_retained"] / s3["criteria"]["reference_total"],
    "step3fix_run_statefix.json", "03_population/run_population.py",
    "Zhou et al. retention for comparison")
rec("population.host", s3["host"], "step3fix_run_statefix.json",
    "03_population/run_population.py", "compute host")

ok = [r for r in s3["results"] if r["status"] == "ok"]
ret = [r for r in ok if s3["criteria"]["bcl_min_ms"] <= r["CL_ms"]
       <= s3["criteria"]["bcl_max_ms"] and r["OS_mV"] > 0]
rec("population.retained_recount", len(ret), "step3fix_run_statefix.json",
    "05_manuscript/taskM_manifest.py",
    "retention criteria re-applied to the raw per-model records (integrity check)")
for feat, unit in (("CL_ms", "ms"), ("OS_mV", "mV"), ("MDP_mV", "mV")):
    v = [r[feat] for r in ret]
    rec(f"population.retained.{feat}", {"min": min(v), "max": max(v),
                                        "mean": float(np.mean(v))},
        "step3fix_run_statefix.json", "05_manuscript/taskM_manifest.py",
        f"retained-population {feat} range ({unit})")
bpm = sorted(60000.0 / r["CL_ms"] for r in ret)
rec("population.retained.bpm", {"min": bpm[0], "max": bpm[-1],
                                "median": float(np.median(bpm))},
    "step3fix_run_statefix.json", "05_manuscript/taskM_manifest.py",
    "retained-population intrinsic rate")

# ------------------------------------------- D. state isolation/determinism
sf = load("statefix_comparison.json")
for k in ("n_compared", "retained_before", "retained_after",
          "retention_before", "retention_after", "identical_retained",
          "retained_to_rejected", "rejected_to_retained",
          "no_pacing_reclassifications", "max_abs_dCL_ms", "mean_abs_dCL_ms"):
    rec(f"stateisolation.{k}", sf[k], "statefix_comparison.json",
        "03_population/aggregate_and_freeze.py",
        f"state-isolation before/after comparison: {k}")

# --------------------------------------------------- E. threshold ladders
ta = load("taskA_summary.json")
for tgt in ("G_CaL", "G_f"):
    t = ta[tgt]
    for k in ("n", "n_never_quiescent", "threshold_median", "threshold_iqr",
              "threshold_range", "max_drop_median", "max_drop_iqr",
              "frac_reaching_-10bpm"):
        rec(f"threshold.{tgt}.{k}", t[k], "taskA_summary.json",
            "04_pharmacology/taskA_analyse.py",
            f"{tgt} quiescence-threshold summary: {k}")
    rec(f"threshold.{tgt}.fraction_pacing", t["fraction_pacing"],
        "taskA_summary.json", "04_pharmacology/taskA_analyse.py",
        f"{tgt} fraction of population still pacing per block level")

for fn, tgt in (("taskA_G_CaL_population_sweep.json", "G_CaL"),
                ("taskA_G_f_population_sweep.json", "G_f")):
    lad = load(fn)
    for k in ("n_models", "prepace_s", "n_non_monotone"):
        rec(f"ladder.{tgt}.{k}", lad[k], fn,
            "04_pharmacology/population_block_sweep.py",
            f"{tgt} block-ladder metadata: {k}")
    rec(f"ladder.{tgt}.blocks", lad["blocks"], fn,
        "04_pharmacology/population_block_sweep.py",
        f"{tgt} block levels simulated")

# --------------------------------------------------- E2. config-borne rules
import yaml                                                    # noqa: E402
with open(os.path.join(ROOT, "00_config", "config.yaml"),
          encoding="utf-8") as f:
    CFG = yaml.safe_load(f)
rec("simulation.duration_s", CFG["simulation"]["duration_s"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "per-model integration time used for population retention")
rec("config.nonobvious_mappings",
    {p["zhou_symbol"]: {"variable": p["variable"], "note": p["note"]}
     for p in CFG["parameters"]
     if p.get("note") and p["zhou_symbol"] in ("G_f", "G_Ks", "P_Jup")},
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "the three parameter mappings that are not inferable from the name")
rec("config.no_pair_feedback.rule",
    CFG["study_integrity"]["no_pair_feedback"]["rule"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "the no-pair-feedback integrity rule, verbatim")
rec("config.no_pair_feedback.voids_study",
    CFG["study_integrity"]["no_pair_feedback"]["voids_study_if_violated"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "whether violation voids the study")
rec("config.comparison_point.rule", CFG["comparison_point"]["rule"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "pre-specified exposure comparator for chronic steady-state dosing")
rec("config.anchor.selection_rule",
    CFG["calibration_provenance"]["ivabradine"]["selection_rule"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "the four design criteria used to select the ivabradine anchor")
rec("config.anchor.gap_exclusion",
    CFG["calibration_provenance"]["ivabradine"]
       ["gap_magnitude_is_not_a_criterion"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "explicit exclusion of gap magnitude as a selection criterion")
rec("config.anchor.primary_block",
    CFG["calibration_provenance"]["ivabradine"]["block_fraction"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "adopted primary ivabradine I_f block")
rec("config.anchor.sensitivity_band",
    CFG["calibration_provenance"]["ivabradine"]["sensitivity_band"],
    "00_config/config.yaml", "00_config/config.yaml (authored)",
    "all three anchors with implied IC50 and fold gap")

# ------------------------------------------------------------ F. anchors
tl = load("taskL_three_anchor_EAR.json")
rec("anchors.ivabradine", tl["anchors"], "taskL_three_anchor_EAR.json",
    "04_pharmacology/taskL_analyse.py",
    "three open-loop ivabradine anchors: I_f block at 1x and the 1x/2x/3x arms")
tg = load("taskG_singles.json")
g1 = tg["G1_dog_binding"]
for k in ("measured_dog_bound_pct", "measured_dog_f_unbound",
          "human_f_unbound_same_assay", "crosscheck_belpaire_f_unbound",
          "f_unbound_needed_for_taskF_pass", "rescue_available", "source",
          "crosscheck_source"):
    rec(f"anchor.verapamil.binding.{k}", g1[k], "taskG_singles.json",
        "04_pharmacology/taskG_singles.py", f"verapamil protein binding: {k}")
g2 = tg["G2_verapamil_schulman"]
for k in ("anchor", "n", "dose_mg_iv_median", "magnitude_recoverable",
          "pk_frame", "assumed_total_ng_per_mL", "implied_block_range",
          "observed_bound_0_of_13_ci"):
    rec(f"anchor.verapamil.schulman.{k}", g2[k], "taskG_singles.json",
        "04_pharmacology/taskG_singles.py", f"Schulman open-loop anchor: {k}")

# -------------------------------------------------------- G. drug mapping
th = load("taskH_exposure.json")
rec("mapping.verapamil.ic50_nM", th["ic50_nM"], "taskH_exposure.json",
    "04_pharmacology/taskH_analyse.py",
    "verapamil I_CaL IC50, Ba2+-derived and Ca2+-corrected")
rec("mapping.verapamil.hill", th["hill"], "taskH_exposure.json",
    "04_pharmacology/taskH_analyse.py", "verapamil Hill coefficient")
rec("mapping.verapamil.f_unbound", th["f_unbound"], "taskH_exposure.json",
    "04_pharmacology/taskH_analyse.py", "human unbound fraction used")
rec("mapping.verapamil.bands_ng_per_mL", th["bands_total_ng_per_mL"],
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py",
    "chronic oral total-plasma bands from the FDA label")
rec("mapping.verapamil.bands_free_nM", th["bands_free_nM"],
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py",
    "corresponding free concentrations")
rec("mapping.verapamil.band_blocks", th["band_blocks"], "taskH_exposure.json",
    "04_pharmacology/taskH_analyse.py",
    "I_CaL block spanned by each band under each IC50")

# ------------------------------------------------------------- H. EAR
for state in ("control", "iso"):
    st = tl["states"][state]
    rec(f"ear.{state}.n", st["n"], "taskL_three_anchor_EAR.json",
        "04_pharmacology/taskL_analyse.py",
        f"denominator: models pacing drug-free in the {state} state")
    rec(f"ear.{state}.band_thresholds", st["band_thresholds"],
        "taskL_three_anchor_EAR.json", "04_pharmacology/taskL_analyse.py",
        f"max EAR inside each clinical band, per anchor and PK arm ({state})")
rec("ear.bands_block", tl["bands"], "taskL_three_anchor_EAR.json",
    "04_pharmacology/taskL_analyse.py",
    "clinical bands expressed as I_CaL block")

# ------------------------------------------------- I. Bliss artifact
te = load("taskE_interaction_invariance.json")
rec("bliss.n_models", te["n_models"], "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py", "population size")
rec("bliss.multipliers", te["multipliers"], "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py", "exposure multipliers swept")
rec("bliss.pairs", [{"pair": r["pair"], "same_target": r["same_target"],
                     "classes_informative": r["classes_failure_informative"],
                     "invariant": r["invariant_failure"],
                     "n_informative": r["n_informative_rows"]}
                    for r in te["results"]],
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py",
    "Bliss classification invariance across exposure, per pair")
tG = load("taskG_pair_prediction.json")
rec("bliss.crosstarget_classes_control",
    [{"b_verapamil": r["b_verapamil"], "class": r["bliss_class"],
      "EAR": r["EAR_paired"], "rescue": r["rescue_fraction"]}
     for r in tG["states"]["control"]["rows"]
     if abs(r["b_ivabradine"] - tG["B_ivabradine"]) < 1e-9],
    "taskG_pair_prediction.json", "04_pharmacology/taskG_analyse.py",
    "Bliss class alternating along one drug's exposure ladder for a "
    "cross-target pair, with the paired EAR and rescue fraction alongside")

# ------------------------------------------------- J. simulation accounting
ck = os.path.join(OUT, "taskG_pair_checkpoint.jsonl")
n_lines = 0
seen = {}
with open(ck, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        n_lines += 1
        r = json.loads(line)
        k = (r["state"], round(r["b_cal"], 6), round(r["b_f"], 6), r["model"])
        seen.setdefault(k, set()).add(
            None if r["bpm"] is None else repr(r["bpm"]))
keys = set(seen)
n_disagree = sum(1 for v in seen.values() if len(v) > 1)
rec("sims.pair_checkpoint_lines", n_lines, "taskG_pair_checkpoint.jsonl",
    "04_pharmacology/taskG_pair_prediction.py + taskH/taskI/taskL runners",
    "total records written across all pair runs")
rec("sims.pair_unique", len(keys), "taskG_pair_checkpoint.jsonl",
    "05_manuscript/taskM_manifest.py",
    "unique (state, I_CaL block, I_f block, model) simulations")
rec("sims.pair_duplicate_reruns", n_lines - len(keys),
    "taskG_pair_checkpoint.jsonl", "05_manuscript/taskM_manifest.py",
    "records repeated by concurrent workers (independent re-executions)")
rec("sims.pair_determinism_disagreements", n_disagree,
    "taskG_pair_checkpoint.jsonl", "05_manuscript/taskM_manifest.py",
    "repeat runs of the same (state, block, block, model) returning a "
    "different value; 0 = every re-execution was bit-identical")

h = hashlib.sha256()
with open(ck, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 16), b""):
        h.update(chunk)
rec("sims.pair_checkpoint_sha256", h.hexdigest(), "taskG_pair_checkpoint.jsonl",
    "05_manuscript/taskM_manifest.py", "checksum of the pair simulation store")


# ------------------------------------------------- V6 additions (Task 12)
rec("derived.anchor_ratio_2_3fold",
    tl["states"]["control"]["band_thresholds"]["480 mg/day|Doesch 2007  (PRIMARY)|1x"]["max_EAR"]
    / tl["states"]["control"]["band_thresholds"]["480 mg/day|36-month (superseded)|1x"]["max_EAR"],
    "taskL_three_anchor_EAR.json", "05_manuscript/taskM_manifest.py",
    "the 2.3-fold anchor-driven movement quoted in the abstract and discussion "
    "(primary / superseded, 480 mg/day, 1x, control)")
_td = load("taskD_state_transfer.json")
rec("state_transfer.iso_baseline_bpm", _td["iso_baseline_bpm"],
    "taskD_state_transfer.json", "04_pharmacology/taskD_state_transfer.py",
    "elevated-rate baseline for the state-transfer test of static block")
rec("state_transfer.control_baseline_bpm", _td["control_baseline_bpm"],
    "taskD_state_transfer.json", "04_pharmacology/taskD_state_transfer.py",
    "control baseline for the state-transfer test of static block")
rec("state_transfer.population_n", _td["population_n"],
    "taskD_state_transfer.json", "04_pharmacology/taskD_state_transfer.py",
    "population used for the state-transfer test")
_ts = load("taskD_strata.json")
rec("state_transfer.strata_at_10bpm_calibration",
    {k: {"n": v["n"], "median_drop_bpm": v["median_drop_bpm"]}
     for k, v in _ts["10.0"].items()},
    "taskD_strata.json", "04_pharmacology/taskD_strata.py",
    "median rate change by baseline-rate stratum at the -10 bpm calibration; "
    "supports the claim that a fixed block fraction does not transfer across rates")
_thx = load("taskH_exposure.json")
rec("ca_corrected.monotherapy_block_480",
    _thx["band_blocks"]["Ca2+-corrected (47.3 nM)|480 mg/day"],
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py",
    "I_CaL block spanned by 480 mg/day under the Ca2+-corrected IC50; "
    "underpins the self-falsifying characterisation")
rec("ca_corrected.monotherapy_block_240",
    _thx["band_blocks"]["Ca2+-corrected (47.3 nM)|240 mg/day"],
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py",
    "as above for 240 mg/day")
import json as _json, os as _os
_v6 = _os.path.join(ROOT, "07_v6_cleanup", "verapamil_202nm_recompute.json")
if _os.path.exists(_v6):
    with open(_v6, encoding="utf-8") as _f:
        _r = _json.load(_f)
    rec("verapamil.ic50_sensitivity_202nM",
        {"ic50_old_nM": _r["ic50_old_nM"], "ic50_new_nM": _r["ic50_new_nM"],
         "n_headline_changes": _r["n_headline_changes"],
         "bands": _r["bands"]},
        "07_v6_cleanup/verapamil_202nm_recompute.json",
        "07_v6_cleanup/taskV6_verapamil_202nm_recompute.py",
        "sensitivity of the exposure->block mapping to substituting the CiPA "
        "tabulated 202 nM for the fitted 198.7 nM; NOT adopted, see audit")
rec("endpoint.name", "excess model-quiescence fraction (EMQF)",
    "manuscript v6", "07_v6_cleanup/taskV6_make_v6.py",
    "endpoint renamed from 'excess absolute risk' to avoid a patient-level "
    "reading; the underlying quantity and all values are unchanged")

# ------------------------------------------------------------- write out
os.makedirs(DEST, exist_ok=True)
with open(os.path.join(DEST, "values_manifest.json"), "w",
          encoding="utf-8") as f:
    json.dump({"n_entries": len(M), "entries": M}, f, indent=2)

lines = ["# Values manifest",
         "",
         "Every number destined for the manuscript, read programmatically from "
         "the frozen outputs by `05_manuscript/taskM_manifest.py`. No value is "
         "transcribed from a task report's prose.",
         "",
         f"**{len(M)} entries.**",
         "",
         "| key | value | source file | generating script | note |",
         "|---|---|---|---|---|"]
for e in M:
    v = e["value"]
    if isinstance(v, float):
        vs = f"{v:.6g}"
    elif isinstance(v, (dict, list)):
        vs = json.dumps(v)
        if len(vs) > 90:
            vs = vs[:87] + "…"
        vs = "`" + vs.replace("|", "\\|") + "`"
    else:
        vs = str(v)
        if len(vs) > 90:
            vs = vs[:87] + "…"
    lines.append(f"| `{e['key']}` | {vs} | `{e['source']}` | "
                 f"`{e['script']}` | {e['note']} |")
with open(os.path.join(DEST, "values_manifest.md"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"{len(M)} entries")
print(f"-> {os.path.join(DEST, 'values_manifest.json')}")
print(f"-> {os.path.join(DEST, 'values_manifest.md')}")
print()
print("KEY NUMBERS (as read, not as remembered):")
for k in ("baseline.worst_abs_pct_diff", "population.n_retained",
          "sims.pair_determinism_disagreements",
          "population.retention_fraction", "population.retained_recount",
          "population.zhou_reference_fraction", "population.retention_wilson95",
          "sims.pair_unique", "sims.pair_duplicate_reruns"):
    e = next(x for x in M if x["key"] == k)
    print(f"  {k:38s} {e['value']}")
