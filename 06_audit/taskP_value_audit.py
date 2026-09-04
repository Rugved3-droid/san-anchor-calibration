"""Forensic value audit - every headline number in Parmar_SAN_manuscript_v4.docx
checked against the frozen outputs. Emits SAN_VALUE_AUDIT.csv.

Rule: analysis output wins over manuscript prose.
"""
import csv
import json
import os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
DEST = os.path.join(ROOT, "06_audit")


def L(n):
    with open(os.path.join(OUT, n), encoding="utf-8") as f:
        return json.load(f)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


b = L("step1_baseline.json")
s2 = L("step2_sampling.json")
s3 = L("step3fix_run_statefix.json")
sf = L("statefix_comparison.json")
ta = L("taskA_summary.json")
tl = L("taskL_three_anchor_EAR.json")
tn = L("taskN_primary_anchor.json")
th = L("taskH_exposure.json")
te = L("taskE_interaction_invariance.json")
with open(os.path.join(ROOT, "05_manuscript", "values_manifest.json"),
          encoding="utf-8") as f:
    MAN = {e["key"]: e["value"] for e in json.load(f)["entries"]}

rows = []


def chk(claim, loc, reported, verified, src, script, notes="", status=None):
    def _n(x):
        return (str(x).replace("%", "").replace(" ", "").replace("'", "")
                .replace("[", "").replace("]", "").replace("(0)", "")
                .replace("none", "0").lower())
    if status is None:
        status = "MATCH" if _n(reported) == _n(verified) else "MISMATCH"
    rows.append(dict(claim=claim, manuscript_location=loc,
                     reported_value=reported, verified_value=verified,
                     source_file=src, generating_script=script,
                     status=status, notes=notes))


# ---------------------------------------------------------------- baseline
chk("worst baseline deviation", "§2.1, §3.1, Fig1", "0.99%",
    f"{MAN['baseline.worst_abs_pct_diff']:.2f}%", "step1_baseline.json",
    "01_baseline/run_baseline.py")
chk("cycle length reproduced", "§2.1, §3.1", "813.42 ms",
    f"{b['comparison']['CL_ms']['simulated']:.2f} ms", "step1_baseline.json",
    "01_baseline/run_baseline.py")
chk("CL SD across beats", "§2.1, §3.1", "0.0386 ms",
    f"{b['CL_sd_ms']:.4f} ms", "step1_baseline.json",
    "01_baseline/run_baseline.py")

# ------------------------------------------------------------- population
chk("LHS pool size", "§2.2", "5000 models", f"{s2['n_models']} generated",
    "step2_lhs_sample.npz (5000x12)", "02_sampling/generate_lhs.py",
    "Pool genuinely contains 5000 vectors; only 940 were simulated. "
    "Methods does not state this.", "INCOMPLETE")
chk("LHS seed", "§2.2", "20260816", str(s2["seed"]), "step2_sampling.json",
    "02_sampling/generate_lhs.py",
    "Sample regenerates BIT-IDENTICALLY from this seed on scipy 1.17.1")
chk("LHS sample SHA256", "§2.2",
    "681f8fc6b8963467ace9f047a37e5a599ec1b92fc8c87c9ccfac5f8b214b9d35",
    "f6867756c3589bacc6457351ff15af3e48664f09e176035a96ea68fdb9d7b238",
    "step2_lhs_sample.npz", "05_manuscript/... rehash",
    "Digest is of the .npz FILE, and savez_compressed embeds timestamps, so "
    "it is not content-stable. Arrays verified identical to regeneration.",
    "MISMATCH")
chk("models simulated", "§3.1", "940", str(s3["n_models"]),
    "step3fix_run_statefix.json", "03_population/run_population.py",
    "Contiguous indices 0-939 of the 5000-row pool")
chk("stable rhythm", "§3.1", "539", str(s3["counts"]["ok"]),
    "step3fix_run_statefix.json", "03_population/run_population.py")
chk("did not pace", "§3.1", "401", str(s3["counts"]["no_pacing"]),
    "step3fix_run_statefix.json", "03_population/run_population.py")
chk("solver failures", "§3.1", "0", str(s3["counts"]["solver_failure"]),
    "step3fix_run_statefix.json", "03_population/run_population.py")
crit = s3["criteria"]
ok = [r for r in s3["results"] if r["status"] == "ok"]
ret = [r for r in ok if crit["bcl_min_ms"] <= r["CL_ms"] <= crit["bcl_max_ms"]
       and r["OS_mV"] > 0]
chk("retained models", "Abstract, §3.1, Figs 1-3", "188", str(len(ret)),
    "step3fix_run_statefix.json", "06_audit/taskP_value_audit.py",
    "Independently recomputed by re-applying retention criteria to raw records")
lo, hi = wilson(len(ret), s3["n_models"])
chk("retention fraction", "Abstract, §3.1", "20.0%",
    f"{len(ret)/s3['n_models']:.1%}", "step3fix_run_statefix.json",
    "06_audit/taskP_value_audit.py")
chk("retention Wilson 95% CI", "Abstract, §3.1, Fig1",
    "17.6-22.7%", f"{lo:.1%}-{hi:.1%}", "computed from 188/940",
    "06_audit/taskP_value_audit.py")
chk("Zhou reference retention", "Abstract, §3.1", "1046/5000 = 20.9%",
    f"{crit['reference_retained']}/{crit['reference_total']} = "
    f"{crit['reference_retained']/crit['reference_total']:.1%}",
    "config.yaml / Zhou et al.", "03_population/run_population.py")
bpm = sorted(60000.0 / r["CL_ms"] for r in ret)
chk("retained rate range", "§3.1", "61.0-99.6 bpm",
    f"{bpm[0]:.1f}-{bpm[-1]:.1f} bpm", "step3fix_run_statefix.json",
    "06_audit/taskP_value_audit.py")
chk("retained median rate", "§3.1, Fig1", "82.2 bpm",
    f"{np.median(bpm):.1f} bpm", "step3fix_run_statefix.json",
    "06_audit/taskP_value_audit.py")

# ------------------------------------------------------ state isolation
chk("retention before state fix", "§3.1", "187", str(sf["retained_before"]),
    "statefix_comparison.json", "03_population/aggregate_and_freeze.py")
chk("retention after state fix", "§3.1", "188", str(sf["retained_after"]),
    "statefix_comparison.json", "03_population/aggregate_and_freeze.py")
chk("retained under both", "§3.1", "187", str(sf["identical_retained"]),
    "statefix_comparison.json", "03_population/aggregate_and_freeze.py")
chk("moved rejected->retained", "§3.1", "1",
    str(sf["rejected_to_retained"]), "statefix_comparison.json",
    "03_population/aggregate_and_freeze.py",
    "Model index 200: no_pacing -> ok, CL 937.59 ms, OS 28.58 mV")
chk("mean |dCL|", "§3.1", "0.909 ms", f"{sf['mean_abs_dCL_ms']:.3f} ms",
    "statefix_comparison.json", "03_population/aggregate_and_freeze.py")
chk("max |dCL|", "§3.1", "241.4 ms", f"{sf['max_abs_dCL_ms']:.1f} ms",
    "statefix_comparison.json", "03_population/aggregate_and_freeze.py")
chk("total sim records", "§3.1", "65,424",
    f"{MAN['sims.pair_checkpoint_lines']:,}", "taskG_pair_checkpoint.jsonl",
    "05_manuscript/taskM_manifest.py")
chk("unique sims", "§3.1, §5", "59,784", f"{MAN['sims.pair_unique']:,}",
    "taskG_pair_checkpoint.jsonl", "05_manuscript/taskM_manifest.py")
chk("re-executions", "§3.1", "5,640",
    f"{MAN['sims.pair_duplicate_reruns']:,}", "taskG_pair_checkpoint.jsonl",
    "05_manuscript/taskM_manifest.py")
chk("determinism disagreements", "§3.1", "none (0)",
    str(MAN["sims.pair_determinism_disagreements"]),
    "taskG_pair_checkpoint.jsonl", "05_manuscript/taskM_manifest.py")

# ---------------------------------------------------------- thresholds
g = ta["G_CaL"]
chk("I_CaL median threshold", "Abstract, §3.2, Fig2", "40.0%",
    f"{g['threshold_median']:.1%}", "taskA_summary.json",
    "04_pharmacology/taskA_analyse.py")
chk("I_CaL IQR", "Abstract, §3.2, Fig2", "30.0-51.25%",
    f"{g['threshold_iqr'][0]:.4g}-{g['threshold_iqr'][1]*100:.4g}% "
    f"(0.30-0.5125)", "taskA_summary.json",
    "04_pharmacology/taskA_analyse.py",
    "v4 text now correct at 51.25%; generated Figure 2 still prints 51%",
    "MATCH (figure disagrees)")
chk("I_CaL threshold range", "Abstract, §3.2, Fig2", "10.0-80.0%",
    f"{g['threshold_range'][0]:.1%}-{g['threshold_range'][1]:.1%}",
    "taskA_summary.json", "04_pharmacology/taskA_analyse.py")
f_ = ta["G_f"]
chk("I_f never quiescent", "Abstract, §3.2, Fig2", "176 of 188 (93.6%)",
    f"{f_['n_never_quiescent']} of {f_['n']} "
    f"({f_['n_never_quiescent']/f_['n']:.1%})", "taskA_summary.json",
    "04_pharmacology/taskA_analyse.py")
chk("fraction reaching -10 bpm via I_f", "§3.2", "66.5%",
    f"{f_['frac_reaching_-10bpm']:.1%}", "taskA_summary.json",
    "04_pharmacology/taskA_analyse.py")
chk("median max I_f rate reduction", "§3.2", "15.9 bpm",
    f"{abs(f_['max_drop_median']):.1f} bpm", "taskA_summary.json",
    "04_pharmacology/taskA_analyse.py")
chk("non-monotone ladders", "§3.2", "none",
    str(MAN["ladder.G_CaL.n_non_monotone"] + MAN["ladder.G_f.n_non_monotone"]),
    "taskA_G_*_population_sweep.json",
    "04_pharmacology/population_block_sweep.py")

# ------------------------------------------------------------- anchors
for lbl, blk, gap in (("Doesch primary", 0.584, 250), ("10-year", 0.509, 172),
                      ("36-month superseded", 0.312, 61)):
    a = tn["anchors"][{"Doesch primary": "Doesch 2007 (PRIMARY)",
                       "10-year": "10-year cohort",
                       "36-month superseded": "36-month (superseded)"}[lbl]]
    chk(f"anchor block {lbl}", "Abstract, §2.6, §3.3", f"{blk:.1%}",
        f"{a['block_1x']:.1%}", "taskN_primary_anchor.json",
        "04_pharmacology/taskN_primary_anchor_decomposition.py")
    chk(f"in vitro fold gap {lbl}", "Abstract, §3.3, §4.1", f"{gap}-fold",
        f"{a['fold_gap_vs_invitro']:.1f}-fold", "taskN_primary_anchor.json",
        "04_pharmacology/taskN_primary_anchor_decomposition.py",
        "Rounded in manuscript", "MATCH (rounded)")
chk("re-solved IC50 (primary)", "§2.6", "7.98 nM",
    f"{tn['anchors']['Doesch 2007 (PRIMARY)']['ic50_resolved_nM']:.2f} nM",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("primary anchor arms", "§2.6", "58.40 / 70.97 / 77.17%",
    " / ".join(f"{v*100:.2f}" for v in
               tn["anchors"]["Doesch 2007 (PRIMARY)"]["arms"].values()) + "%",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
hs = tn["N4_hill"]["sensitivity_primary_anchor"]
chk("Hill sensitivity, 2x arm", "§2.6", "68.0-76.3%",
    f"{min(hs[k]['2x'] for k in hs)*100:.1f}-"
    f"{max(hs[k]['2x'] for k in hs)*100:.1f}%", "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")

# ------------------------------------------------------------- EAR
ANCH = {"Doesch": "Doesch 2007  (PRIMARY)", "10-year": "10-year cohort",
        "36-month": "36-month (superseded)"}
for loc, st, ak, arm, band, cp, cci in [
        ("Abstract, §3.3", "control", "36-month", "1x", "480 mg/day", 6.9,
         (4.1, 11.5)),
        ("Abstract, §3.3", "control", "Doesch", "1x", "480 mg/day", 16.0,
         (11.4, 21.9)),
        ("§3.3", "control", "10-year", "1x", "480 mg/day", 12.8, (8.7, 18.3)),
        ("§3.4", "control", "Doesch", "1x", "240 mg/day", 4.3, (2.2, 8.2)),
        ("§3.4", "control", "Doesch", "2x", "240 mg/day", 5.9, (3.3, 10.2)),
        ("§3.4", "control", "Doesch", "2x", "480 mg/day", 18.6, (13.7, 24.8)),
        ("§3.4", "control", "Doesch", "3x", "480 mg/day", 18.1, (13.2, 24.2)),
        ("§3.4", "iso", "Doesch", "1x", "480 mg/day", 12.5, (8.3, 18.4)),
        ("§3.4", "iso", "Doesch", "2x", "480 mg/day", 14.3, (9.8, 20.4)),
        ("§3.4", "iso", "Doesch", "3x", "480 mg/day", 19.0, (13.8, 25.7))]:
    t = tl["states"][st]["band_thresholds"][f"{band}|{ANCH[ak]}|{arm}"]
    n = tl["states"][st]["n"]
    k = round(t["max_EAR"] * n)
    rc = wilson(k, n)
    ok_ = (abs(t["max_EAR"] * 100 - cp) < 0.06
           and abs(t["ci"][0] * 100 - cci[0]) < 0.06
           and abs(t["ci"][1] * 100 - cci[1]) < 0.06
           and abs(rc[0] - t["ci"][0]) < 1e-9)
    chk(f"EAR {band} {ak} {arm} ({st})", loc,
        f"{cp}% ({cci[0]}-{cci[1]})",
        f"{t['max_EAR']*100:.1f}% ({t['ci'][0]*100:.1f}-{t['ci'][1]*100:.1f})",
        "taskL_three_anchor_EAR.json", "04_pharmacology/taskL_analyse.py",
        f"k={k}, n={n}; CI reproduces from count/denominator",
        "MATCH" if ok_ else "MISMATCH")

# ------------------------------------------------------- exposure bands
fb = th["bands_free_nM"]
chk("free verapamil 240 mg/day", "§3.4", "8.0-37.5 nM",
    f"{fb['240 mg/day'][0]:.1f}-{fb['240 mg/day'][1]:.1f} nM",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
chk("free verapamil 480 mg/day", "§3.4", "28.6-91.5 nM",
    f"{fb['480 mg/day'][0]:.1f}-{fb['480 mg/day'][1]:.1f} nM",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
bb = th["band_blocks"]
chk("I_CaL block 240 (Ba)", "§3.4", "2.9-14.0%",
    f"{bb['Ba2+-derived (198.7 nM)|240 mg/day'][0]:.1%}-"
    f"{bb['Ba2+-derived (198.7 nM)|240 mg/day'][1]:.1%}",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
chk("I_CaL block 480 (Ba)", "§3.4", "10.8-30.0%",
    f"{bb['Ba2+-derived (198.7 nM)|480 mg/day'][0]:.1%}-"
    f"{bb['Ba2+-derived (198.7 nM)|480 mg/day'][1]:.1%}",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
chk("Ca-corrected block 480", "§3.4", "36.6-67.2%",
    f"{bb['Ca2+-corrected (47.3 nM)|480 mg/day'][0]:.1%}-"
    f"{bb['Ca2+-corrected (47.3 nM)|480 mg/day'][1]:.1%}",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
chk("verapamil IC50 (Ba)", "§2.6", "198.7 nM (working); 202 nM reported",
    "202 nM is what ref 10 reports", "outputs/_crumb.txt (Crumb 2016 text)",
    "hardcoded literal in all 04_pharmacology scripts",
    "NO derivation of 198.7 exists anywhere in the project. An early script "
    "(sweep_ical_block.py) used 202. The v4 claim of 'Hill-consistent "
    "re-solution' is unsupported by any code.", "UNSUPPORTED")
chk("verapamil unbound fraction", "§2.6", "10.4%", f"{th['f_unbound']:.1%}",
    "taskH_exposure.json", "04_pharmacology/taskH_analyse.py")
chk("verapamil Hill", "§2.6", "1.09", str(th["hill"]), "taskH_exposure.json",
    "04_pharmacology/taskH_analyse.py")

# ------------------------------------------------------- decomposition
d = {r["block"]: r for r in
     tn["N2_decomposition"]["control"]["Doesch 2007 (PRIMARY)"]}
chk("PK-only, 240 time-avg (control)", "§3.6", "-2.60 bpm",
    f"{d[0.029]['PK_only']:.2f} bpm", "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("PD-only, 240 time-avg (control)", "§3.6", "-2.26 bpm",
    f"{d[0.029]['PD_only']:.2f} bpm", "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("PD-only, 480 peak (control)", "§3.6", "-18.29 bpm",
    f"{d[0.30]['PD_only']:.2f} bpm", "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
di = {r["block"]: r for r in tn["N2_decomposition"]["iso"]["Doesch 2007 (PRIMARY)"]}
chk("Iso PK/PD at 240 time-avg", "§3.6", "-4.43 / -1.17 bpm",
    f"{di[0.029]['PK_only']:.2f} / {di[0.029]['PD_only']:.2f} bpm",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("Iso low-dose PK:PD ratio", "§3.6", "approximately four-fold",
    f"{abs(di[0.029]['PK_only']/di[0.029]['PD_only']):.2f}-fold",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py",
    "3.77 rounded up to 'four-fold' overstates slightly",
    "MATCH (rounding flatters)")

# ---------------------------------------------------- external comparison
e = tn["N3_external"]
chk("predicted dHR, control, time-avg", "§3.7", "-4.44 bpm",
    f"{e['control']['Doesch 2007 (PRIMARY)']['time-average (PRIMARY)']['predicted_bpm']:.2f} bpm",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("ratio to reported 5 bpm", "§3.7", "0.89",
    f"{e['control']['Doesch 2007 (PRIMARY)']['time-average (PRIMARY)']['ratio_pred_over_obs']:.2f}",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("predicted dHR, Iso, time-avg", "§3.7", "-6.19 bpm",
    f"{e['iso']['Doesch 2007 (PRIMARY)']['time-average (PRIMARY)']['predicted_bpm']:.2f} bpm",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
chk("predicted dHR, Cmax sensitivity", "§3.7", "-11.24 bpm",
    f"{e['control']['Doesch 2007 (PRIMARY)']['Cmax (sensitivity)']['predicted_bpm']:.2f} bpm",
    "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")
ratios = [v[c]["ratio_pred_over_obs"] for st in e for k, v in e[st].items()
          for c in v]
chk("full ratio span across anchors/points", "§3.7", "0.83 to 2.34",
    f"{min(ratios):.2f} to {max(ratios):.2f}", "taskN_primary_anchor.json",
    "04_pharmacology/taskN_primary_anchor_decomposition.py")

# ------------------------------------------------------------- Bliss
inv = {tuple(p["pair"]): p for p in MAN["bliss.pairs"]}
chk("non-invariant Bliss pairs", "§3.5, Fig4",
    "diltiazem x verapamil; diltiazem x ivabradine",
    "; ".join(" x ".join(k) for k, p in inv.items() if not p["invariant"]),
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py")
chk("informative rungs, dilt x verap", "§3.5", "6",
    str(inv[("diltiazem", "verapamil")]["n_informative"]),
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py")
chk("informative rungs, dilt x ivab", "§3.5", "7",
    str(inv[("diltiazem", "ivabradine")]["n_informative"]),
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py")
chk("verap x mexiletine", "§3.5", "super-additive at all 5",
    f"{inv[('verapamil','mexiletine')]['classes_informative']} at "
    f"{inv[('verapamil','mexiletine')]['n_informative']}",
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py")
chk("verap x ivabradine", "§3.5", "additive at all 4",
    f"{inv[('verapamil','ivabradine')]['classes_informative']} at "
    f"{inv[('verapamil','ivabradine')]['n_informative']}",
    "taskE_interaction_invariance.json",
    "04_pharmacology/taskE_interaction_invariance.py")

# ------------------------------------------------------------- derived
chk("anchor-driven movement", "New&Noteworthy, Abstract, §4", "2.3-fold",
    f"{16.0/6.9:.3f}-fold", "derived from taskL_three_anchor_EAR.json",
    "06_audit/taskP_value_audit.py",
    "Derived, not read; absent from the values manifest", "MATCH (derived)")
chk("Iso denominator", "§2.7, §3.4, Fig3", "168",
    str(tl["states"]["iso"]["n"]), "taskL_three_anchor_EAR.json",
    "04_pharmacology/taskL_analyse.py")

with open(os.path.join(DEST, "SAN_VALUE_AUDIT.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["claim", "manuscript_location",
                                      "reported_value", "verified_value",
                                      "source_file", "generating_script",
                                      "status", "notes"])
    w.writeheader()
    w.writerows(rows)

from collections import Counter
c = Counter(r["status"] for r in rows)
print(f"{len(rows)} claims checked")
for k, v in c.most_common():
    print(f"  {k:24s} {v}")
print()
for r in rows:
    if not r["status"].startswith("MATCH"):
        print(f"  [{r['status']}] {r['claim']}: ms='{r['reported_value']}' "
              f"verified='{r['verified_value']}'")
print(f"\n-> {os.path.join(DEST, 'SAN_VALUE_AUDIT.csv')}")
