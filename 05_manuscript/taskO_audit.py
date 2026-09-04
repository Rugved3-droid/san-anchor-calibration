"""Task O - audit manuscript_full_v3.md against the frozen outputs.

Findings only. Does not modify the manuscript.
"""
import json
import os
import re
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
MS = r"D:\manuscript_full_v3.md"

with open(os.path.join(ROOT, "05_manuscript", "values_manifest.json"),
          encoding="utf-8") as f:
    MAN = {e["key"]: e["value"] for e in json.load(f)["entries"]}


def load(n):
    with open(os.path.join(OUT, n), encoding="utf-8") as f:
        return json.load(f)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


txt = open(MS, encoding="utf-8").read()
F = []


def flag(loc, issue, sev, fix=""):
    F.append({"loc": loc, "issue": issue, "sev": sev, "fix": fix})


print("=" * 100)
print("O1 - NUMERICAL AUDIT")
print("=" * 100)

# ---- exact manifest matches -----------------------------------------
checks = [
    ("worst deviation 0.99%", "0.99", MAN["baseline.worst_abs_pct_diff"],
     lambda v: f"{v:.2f}"),
    ("CL 813.42", "813.42", MAN["baseline.CL_ms.simulated"],
     lambda v: f"{v:.2f}"),
    ("CL SD 0.0386", "0.0386", MAN["baseline.CL_sd_ms"], lambda v: f"{v:.4f}"),
    ("retained 188", "188", MAN["population.n_retained"], str),
    ("ok 539", "539", MAN["population.n_integrated_ok"], str),
    ("no-pacing 401", "401", MAN["population.n_no_pacing"], str),
    ("unique sims 59,784", "59,784", MAN["sims.pair_unique"],
     lambda v: f"{v:,}"),
    ("records 65,424", "65,424", MAN["sims.pair_checkpoint_lines"],
     lambda v: f"{v:,}"),
    ("reruns 5,640", "5,640", MAN["sims.pair_duplicate_reruns"],
     lambda v: f"{v:,}"),
    ("manifest entries 142", "142", len(MAN), str),
    ("frac reaching -10bpm 66.5%", "66.5",
     MAN["threshold.G_f.frac_reaching_-10bpm"] * 100, lambda v: f"{v:.1f}"),
    ("I_f median max drop 15.9", "15.9",
     abs(MAN["threshold.G_f.max_drop_median"]), lambda v: f"{v:.1f}"),
]
for label, claimed, actual, fmt in checks:
    got = fmt(actual)
    ok = claimed.replace(",", "") == got.replace(",", "")
    print(f"  [{'OK ' if ok else 'MISMATCH'}] {label:34s} manuscript "
          f"'{claimed}'  manifest '{got}'")
    if not ok:
        flag("various", f"{label}: manuscript {claimed}, manifest {got}",
             "HIGH", got)

# ---- IQR rounding ----------------------------------------------------
iqr = MAN["threshold.G_CaL.threshold_iqr"]
print(f"\n  I_CaL IQR: manifest = {iqr[0]*100:.4g}–{iqr[1]*100:.4g}% ; "
      f"manuscript states 30.0–51.3%")
if abs(iqr[1] * 100 - 51.25) < 1e-9:
    flag("Abstract; §3.2; Fig 2 legend",
         "IQR upper bound is 51.25%, presented as 51.3% in text but the "
         "generated Figure 2 prints '51%' (0-dp). Same quantity, three "
         "renderings.", "LOW",
         "Use 51.25% (or 51.2%) consistently in text and figure")

# ---- EAR values and their confidence intervals ------------------------
tl = load("taskL_three_anchor_EAR.json")
ANCH = {"Doesch": "Doesch 2007  (PRIMARY)", "10-year": "10-year cohort",
        "36-month": "36-month (superseded)"}
print("\n  EAR values and Wilson CI reproduction from count/denominator:")
ms_ear = [
    ("§3.3/Abstract 480 36-month 1x", "control", "36-month", "1x",
     "480 mg/day", 6.9, (4.1, 11.5)),
    ("§3.3/Abstract 480 Doesch 1x", "control", "Doesch", "1x",
     "480 mg/day", 16.0, (11.4, 21.9)),
    ("§3.3 480 10-year 1x", "control", "10-year", "1x", "480 mg/day",
     12.8, (8.7, 18.3)),
    ("§3.4 240 Doesch 1x", "control", "Doesch", "1x", "240 mg/day",
     4.3, (2.2, 8.2)),
    ("§3.4 240 Doesch 2x", "control", "Doesch", "2x", "240 mg/day",
     5.9, (3.3, 10.2)),
    ("§3.4 480 Doesch 2x", "control", "Doesch", "2x", "480 mg/day",
     18.6, (13.7, 24.8)),
    ("§3.4 480 Doesch 3x", "control", "Doesch", "3x", "480 mg/day",
     18.1, (13.2, 24.2)),
    ("§3.4 iso 480 Doesch 1x", "iso", "Doesch", "1x", "480 mg/day",
     12.5, (8.3, 18.4)),
    ("§3.4 iso 480 Doesch 2x", "iso", "Doesch", "2x", "480 mg/day",
     14.3, (9.8, 20.4)),
    ("§3.4 iso 480 Doesch 3x", "iso", "Doesch", "3x", "480 mg/day",
     19.0, (13.8, 25.7)),
]
for loc, state, ak, arm, band, claim_pct, claim_ci in ms_ear:
    th = tl["states"][state]["band_thresholds"][f"{band}|{ANCH[ak]}|{arm}"]
    got_pct = th["max_EAR"] * 100
    got_ci = (th["ci"][0] * 100, th["ci"][1] * 100)
    n = tl["states"][state]["n"]
    k = round(th["max_EAR"] * n)
    rec_ci = tuple(x * 100 for x in wilson(k, n))
    ok_p = abs(got_pct - claim_pct) < 0.06
    ok_c = (abs(got_ci[0] - claim_ci[0]) < 0.06
            and abs(got_ci[1] - claim_ci[1]) < 0.06)
    ok_r = (abs(rec_ci[0] - got_ci[0]) < 1e-6
            and abs(rec_ci[1] - got_ci[1]) < 1e-6)
    tag = "OK " if (ok_p and ok_c and ok_r) else "CHECK"
    print(f"  [{tag}] {loc:32s} ms {claim_pct:5.1f}% "
          f"({claim_ci[0]:.1f}-{claim_ci[1]:.1f})  data {got_pct:5.1f}% "
          f"({got_ci[0]:.1f}-{got_ci[1]:.1f})  k={k}/n={n} "
          f"CI-reproduces={ok_r}")
    if not ok_p:
        flag(loc, f"EAR point estimate {claim_pct}% vs data {got_pct:.1f}%",
             "HIGH", f"{got_pct:.1f}%")
    if not ok_c:
        flag(loc, f"CI {claim_ci} vs data ({got_ci[0]:.1f}, {got_ci[1]:.1f})",
             "HIGH", f"({got_ci[0]:.1f}-{got_ci[1]:.1f})")

# ---- fold-gap consistency -------------------------------------------
print("\n  in vitro fold gap:")
band = MAN["config.anchor.sensitivity_band"]
tn = load("taskN_primary_anchor.json")
cfg_gap = [b["fold_gap"] for b in band if b["block"] == 0.584][0]
comp_gap = tn["anchors"]["Doesch 2007 (PRIMARY)"]["fold_gap_vs_invitro"]
print(f"    config band: {cfg_gap}x   recomputed: {comp_gap:.1f}x")
n250 = len(re.findall(r"250-fold", txt))
n251 = len(re.findall(r"251-fold", txt))
print(f"    manuscript uses '250-fold' {n250}x and '251-fold' {n251}x")
if n250 and n251:
    flag("Abstract, §3.3, §4.1 vs §2.6",
         f"Same quantity written as 250-fold ({n250} places) and 251-fold "
         f"({n251} place). Recomputed value is {comp_gap:.1f}.",
         "MEDIUM", "Use one value throughout; 251-fold is the computed one, "
                   "250-fold is the config band's rounded entry")

print()
print("=" * 100)
print("O2 - INTERNAL CONSISTENCY")
print("=" * 100)
for pat, name in ((r"\b188\b", "188"), (r"\b168\b", "168"),
                  (r"58\.4", "58.4%"), (r"50\.9", "50.9%"),
                  (r"31\.2", "31.2%")):
    print(f"  '{name}' occurrences: {len(re.findall(pat, txt))}")

meth = txt[txt.index("## 2. Methods"):txt.index("## 3. Results")]
res = txt[txt.index("## 3. Results"):txt.index("## 4. Discussion")]
leg = txt[txt.index("## 6. Figure legends"):txt.index("## 7. References")]
if "168" not in meth:
    flag("§2.7 Methods",
         "The Iso-state denominator (n = 168, conditioned on models pacing "
         "drug-free) is defined in Results §3.4 and the Figure 3 legend but "
         "never in Methods, where the endpoint denominator is specified.",
         "MEDIUM",
         "State in §2.7 that the Iso-state denominator is the 168 models "
         "pacing drug-free, and why 20 are excluded")
print(f"  n=168 defined in Methods? {'168' in meth}  Results? "
      f"{'168' in res}  Fig3 legend? {'168' in leg}")

# ---- 7x claim vs primary anchor --------------------------------------
print("\n  strong-inhibitor (7x) arm availability:")
ti = load("taskI_pk_interaction.json")
arms7 = [a["label"] for a in ti["arms"] if a["label"].startswith("7x")]
print(f"    7x arm exists in taskI for anchor(s): 36-month only "
      f"(label {arms7})")
d480 = tl["states"]["control"]["band_thresholds"]["480 mg/day|"
                                                 "Doesch 2007  (PRIMARY)|1x"]
print(f"    primary anchor, 480 mg/day, 1x (moderate/no interaction): "
      f"EAR {d480['max_EAR']:.1%}, crosses 10% by CI = "
      f"{d480['crosses_10_ci']}")
if d480["crosses_10_ci"]:
    flag("§3.6 final paragraph",
         "Claims 'every moderate-inhibition arm sat below every "
         "interval-supported threshold'. Under the PRIMARY anchor the 1x arm "
         "at 480 mg/day clears 10% WITH interval support "
         f"({d480['max_EAR']:.1%}, CI {d480['ci'][0]:.1%}-"
         f"{d480['ci'][1]:.1%}), contradicting §3.3 and §3.4. The claim holds "
         "only under the superseded 36-month anchor, which is the only anchor "
         "for which the 7x arm was ever run.", "HIGH",
         "Restrict the regulatory-gradient claim to the superseded anchor and "
         "say so, or drop it")

print()
print("=" * 100)
print("O5 - BLISS INVARIANCE, FROM THE MANIFEST")
print("=" * 100)
for p in MAN["bliss.pairs"]:
    print(f"  {' x '.join(p['pair']):26s} same_target={str(p['same_target']):5s} "
          f"informative={p['n_informative']}  classes={p['classes_informative']}"
          f"  INVARIANT={p['invariant']}")
noninv = [" × ".join(p["pair"]) for p in MAN["bliss.pairs"]
          if not p["invariant"]]
inv = [" × ".join(p["pair"]) for p in MAN["bliss.pairs"] if p["invariant"]]
print(f"\n  NOT invariant: {noninv}")
print(f"  Invariant    : {inv}")

# Figure 4 as actually generated
tG = load("taskG_pair_prediction.json")
rows = [r for r in tG["states"]["control"]["rows"]
        if abs(r["b_ivabradine"] - tG["B_ivabradine"]) < 1e-9]
cls = [r["bliss_class"] for r in rows]
print(f"\n  Figure 4 as generated plots taskG_pair_prediction.json:")
print(f"    pair          : verapamil x ivabradine (ONE pair)")
print(f"    ivabradine I_f: {tG['B_ivabradine']:.1%}  <-- SUPERSEDED anchor")
print(f"    classes along the verapamil ladder: {cls}")

with open(os.path.join(ROOT, "outputs", "taskO_audit.json"), "w",
          encoding="utf-8") as f:
    json.dump({"findings": F}, f, indent=2)
print(f"\n{len(F)} machine-checkable findings -> outputs/taskO_audit.json")
