"""Create Parmar_SAN_manuscript_v6_CLEAN.docx from v5_AUDITED.

Applies ONLY the corrections specified in the v6 brief and supported by the
forensic audit plus the provenance discovered during this pass. No stylistic
rewriting, no restructuring, no author changes, no change to any verified
number.

v4 and v5 are not modified.
"""
import os
import shutil
import docx

SRC = r"D:\Parmar_SAN_manuscript_v5_AUDITED.docx"
DST = r"D:\Parmar_SAN_manuscript_v6_CLEAN.docx"

# --------------------------------------------------------------- Task 1
# Ordered longest-first so no replacement eats another's prefix.
GLOBAL = [
    ("excess absolute risk (EAR)", "excess model-quiescence fraction (EMQF)"),
    ("Excess absolute risk", "Excess model-quiescence fraction"),
    ("excess absolute risk", "excess model-quiescence fraction"),
    ("combination-risk estimate", "combination-quiescence estimate"),
    ("headline risk estimate", "headline EMQF estimate"),
    ("single-agent risk", "single-agent quiescence fraction"),
    ("EAR", "EMQF"),
]

TARGETED = [
    # ---------------- Task 1: definition, and the no-clinical-risk guard --
    ("T1a endpoint definition names the retained population and rules out a "
     "patient-level reading",
     "The primary endpoint is excess model-quiescence fraction (EMQF), "
     "defined per-model and paired: the fraction of the population that "
     "continues to pace under drug A alone and under drug B alone, but loses "
     "automaticity under the combination.",
     "The primary endpoint is the excess model-quiescence fraction (EMQF), "
     "defined per-model and paired: the fraction of retained population "
     "models that continue to pace under drug A alone and under drug B "
     "alone, but lose automaticity under the combination. EMQF is a property "
     "of the simulated model population and is not an estimate of "
     "patient-level event probability, of sinus arrest incidence, or of "
     "clinical risk; the unit is a parameterised myocyte, the event is loss "
     "of automaticity in an isolated cell, and no time dimension is "
     "involved."),

    # ---------------- Task 2: Wilson qualification -----------------------
    ("T2a Wilson intervals qualified as parameter-space sampling only, and "
     "arms declared paired",
     "Confidence intervals are Wilson binomial intervals on that count.",
     "Confidence intervals are Wilson binomial intervals on that count. They "
     "are reported as finite-sample intervals for the proportion of the "
     "specified parameter-space population represented in the retained model "
     "sample, and they quantify parameter-space sampling variability only. "
     "They do not incorporate calibration uncertainty, model-structure "
     "uncertainty, or pharmacokinetic and pharmacodynamic structural "
     "uncertainty; the anchor sensitivity band reported throughout is the "
     "larger source of uncertainty and is presented separately. Because all "
     "treatment conditions are evaluated in the same retained models, "
     "comparisons across conditions are paired."),

    # ---------------- Task 2: Zhou two-proportion ------------------------
    ("T2b Zhou comparison stated as a two-proportion test rather than by "
     "interval overlap",
     "against the reference retention of 1046 of 5000 (20.9%) reported by "
     "Zhou et al. (2); the reference proportion lies within the interval "
     "(Figure 1B).",
     "against the reference retention of 1046 of 5000 (20.9%) reported by "
     "Zhou et al. (2). The two proportions do not differ detectably "
     "(\u03c7\u00b2 = 0.353, p = 0.55), and the reference proportion lies "
     "within our interval (Figure 1B); we read this as consistency of "
     "retention behaviour rather than as formal validation of the "
     "population."),

    # ---------------- Task 3: upper-bound softening (Methods) ------------
    ("T3a Methods 2.6 - upper-bound claim softened to match what was "
     "demonstrated",
     "Static block therefore over-states the sustained effect, over-states "
     "the fraction of models driven below threshold, and every quiescence-"
     "fraction estimate reported here is an upper bound.",
     "Static block is therefore expected to over-state sustained drug effect "
     "and the fraction of models driven below threshold; we accordingly "
     "interpret the resulting model-quiescence estimates as upper bounds, "
     "while recognising that the direction of this bias is inferred from "
     "published state dependence rather than demonstrated here with an "
     "explicit kinetic block model."),

    # ---------------- Task 4: verapamil provenance, corrected ------------
    ("T4 Methods 2.6 - verapamil IC50 provenance corrected. The forensic "
     "audit reported that 198.7 nM had no documented derivation; that finding "
     "was WRONG. outputs/_sim0/Crumb_Fits.csv records it as an independent "
     "nonlinear Hill refit to the Crumb supplemental mean data that "
     "reproduces the author's ~202 nM value, with the paired Hill "
     "coefficient 1.09.",
     "The first is a Ba\u00b2\u207a-derived value of 198.7 nM, the working "
     "value used throughout this analysis; the CiPA ion channel panel "
     "reports 202 nM for verapamil under Ba\u00b2\u207a charge carrier (10). "
     "The two differ by 1.7%, which shifts I_CaL block by at most 0.4 "
     "percentage points across the exposure range examined here and changes "
     "no reported conclusion.",
     "The first is a Ba\u00b2\u207a-derived value of 198.7 nM with a Hill "
     "coefficient of 1.09. These are not the panel's tabulated summary "
     "values but a paired independent nonlinear Hill fit to the "
     "concentration\u2013response data of the CiPA ion channel panel (10), "
     "performed for this project; the fit reproduces that panel's reported "
     "\u2248202 nM verapamil value to within 1.7%. IC50 and Hill coefficient "
     "are used together because they derive from the same fit. Substituting "
     "the panel's tabulated 202 nM while retaining the fitted Hill "
     "coefficient would mix two parameterisations of the same curve, and "
     "would additionally move the upper edge of the 480 mg/day exposure band "
     "from 30.05% to 29.67% block, excluding an existing simulated ladder "
     "rung and shifting several reported maxima by a band-boundary artifact "
     "rather than by any change in the underlying simulation. The fitted "
     "pair is therefore retained; the substitution was computed as a "
     "sensitivity and is reported in the accompanying analysis record."),

    # ---------------- Task 5 + 6: ivabradine provenance and HCN4 ---------
    ("T5/T6 Methods 2.6 - ivabradine free Cmax and Hill provenance stated, "
     "and the HCN4 value phrased as the specific cited experiment rather "
     "than a universal constant",
     "To evaluate the same drug at CYP3A4-inhibited exposure, the in vitro "
     "Hill slope (n = 0.80) was retained and the potency re-solved so that "
     "the concentration\u2013response curve passes through the empirical "
     "anchor at the clinical free peak concentration of 12.2 nM.",
     "The in vitro ivabradine parameters are taken from a single cited "
     "experiment: half-block of heterologously expressed human HCN4 in "
     "HEK 293 cells at approximately 2.0 \u00b5M with a Hill slope of "
     "approximately 0.8, under open-channel, use-dependent conditions (15). "
     "Reported HCN4 potency varies across experimental protocols and channel "
     "states, so all comparisons below are to this specific cited value "
     "rather than to a universal constant. The clinical free peak "
     "concentration of 12.2 nM is derived from a steady-state peak total "
     "concentration of 19 ng/mL on 5 mg twice daily (17) at 30% unbound "
     "(19 ng/mL \u00f7 468.6 g/mol \u00d7 0.30 = 12.2 nM). To evaluate the "
     "same drug at CYP3A4-inhibited exposure, the in vitro Hill slope "
     "(n = 0.80) was retained and the potency re-solved so that the "
     "concentration\u2013response curve passes through the empirical anchor "
     "at that concentration."),

    # ---------------- Task 6: discrepancy phrasing -----------------------
    ("T6b Methods 2.6 - discrepancy phrased against the cited experiment",
     "The 251-fold discrepancy between them is unexplained",
     "The \u2248250-fold discrepancy between the empirical anchor and that "
     "cited in vitro value is unexplained"),

    # ---------------- Task 3: upper-bound softening (Limitations) --------
    ("T3b Limitations - upper-bound claim softened; the demonstrated / "
     "inferred / undemonstrated distinction made explicit",
     "Static block is not a kinetic model, and every quiescence-fraction "
     "estimate is an upper bound.",
     "Static block is not a kinetic model, and the upper-bound "
     "interpretation is inferred rather than proved."),
    ("T3c Limitations - closing sentence softened",
     "Every estimate reported here should be read as a bounded upper limit.",
     "What is demonstrated here is that a fixed block fraction does not "
     "transfer appropriately across rates; that use- and state-dependence "
     "should reduce effective block as rate slows is supported by the cited "
     "literature rather than by simulation in this study; and the exact sign "
     "and magnitude of the resulting bias at the threshold-population "
     "endpoint are not directly demonstrated. We therefore read the "
     "estimates as upper bounds without claiming a proved bound."),

    # ---------------- Task 9: Figure 4 anchor-dependence sentence --------
    ("T9 Results 3.5 - one sentence recording that the two anchors give "
     "different Bliss classifications at 6 of 12 identical rungs",
     "Interaction classification is therefore reported only as an artifact "
     "demonstration (Figure 4), with excess model-quiescence fraction and "
     "single-agent quiescence fraction used as the primary readout.",
     "Notably, the primary and superseded ivabradine anchors yielded "
     "different Bliss classifications at 6 of 12 identical verapamil "
     "exposure rungs, further illustrating that apparent interaction "
     "classification can depend on calibration choice rather than on any "
     "pharmacological interaction. Interaction classification is therefore "
     "reported only as an artifact demonstration (Figure 4), with excess "
     "model-quiescence fraction and single-agent quiescence fraction used as "
     "the primary readout."),

    # ---------------- residual 'risk' wording ----------------------------
    ("R1 Abstract conclusions - 'risk estimate' -> quiescence-fraction",
     "Calibration anchor choice, rather than model structure, dominates the "
     "resulting risk estimate.",
     "Calibration anchor choice, rather than model structure, dominates the "
     "resulting quiescence-fraction estimate."),
    ("R2 Introduction - 'risk estimate' -> quiescence-fraction",
     "the calibration anchor, not the model, dominates the risk estimate",
     "the calibration anchor, not the model, dominates the "
     "quiescence-fraction estimate"),
    ("R3 Results 3.3 - 'risk estimate' -> quiescence-fraction",
     "the most conservative on the risk estimate",
     "the most conservative on the quiescence-fraction estimate"),
    ("R4 Results 3.6 - 'risk endpoint' -> quiescence endpoint",
     "On the risk endpoint the pharmacokinetic arm",
     "On the quiescence endpoint the pharmacokinetic arm"),
    ("R5 Methods 2.7 - 'monotherapy risk' -> single-agent quiescence",
     "As monotherapy risk rises toward unity that surviving set shrinks "
     "toward zero and EMQF necessarily falls",
     "As the single-agent quiescence fraction rises toward unity that "
     "surviving set shrinks toward zero and EMQF necessarily falls"),
    ("R6 Methods 2.7 - 'monotherapy risk' -> single-agent quiescence",
     "therefore indicates monotherapy risk absorbing the excess",
     "therefore indicates the single-agent quiescence fraction absorbing the "
     "excess"),
    ("R7 Limitations - 'monotherapy risk' -> single-agent quiescence",
     "therefore falls as monotherapy risk approaches unity",
     "therefore falls as the single-agent quiescence fraction approaches "
     "unity"),
    ("R8 Section heading",
     "2.7 Endpoint: excess model-quiescence fraction",
     "2.7 Endpoint: excess model-quiescence fraction (EMQF)"),

    # ---------------- Task 7: references ---------------------------------
    ("T7a Reference 3 completed from the primary source",
     "3.  Ivabradine. Summary of Product Characteristics (European Medicines "
     "Agency). [version and access date to be completed]",
     "3.  Procoralan 5 mg film-coated tablets. Summary of Product "
     "Characteristics, section 4.5. Les Laboratoires Servier, Suresnes, "
     "France. Date of revision of the text 10/2021; electronic Medicines "
     "Compendium, last updated 5 January 2022."),
    ("T7b Reference 4 completed from the primary source",
     "4.  Ivabradine. US Prescribing Information. [version and access date to "
     "be completed]",
     "4.  CORLANOR (ivabradine) tablets, for oral use; oral solution. US "
     "Prescribing Information. Amgen Inc., Thousand Oaks, CA. Revised August "
     "2021."),
    ("T7c Reference 15 annotated with the specific quantitative support it "
     "provides, verified against the primary abstract",
     "15.  Bucchi A, Tognati A, Milanesi R, Baruscotti M, DiFrancesco D. "
     "Properties of ivabradine-induced block of HCN1 and HCN4 pacemaker "
     "channels. J Physiol 572: 335\u2013346, 2006. PMID 16484306",
     "15.  Bucchi A, Tognati A, Milanesi R, Baruscotti M, DiFrancesco D. "
     "Properties of ivabradine-induced block of HCN1 and HCN4 pacemaker "
     "channels. J Physiol 572: 335\u2013346, 2006. "
     "doi:10.1113/jphysiol.2005.100776. PMID 16484306. [Half-block "
     "concentration 2.0 \u00b5M for human HCN4 heterologously expressed in "
     "HEK 293 cells.]"),
    ("T7d Reference 16 title completed",
     "16.  Doesch AO, Celik S, Ehlermann P, Frankenstein L, Zehelein J, "
     "Koehler F, Katus HA, Dengler TJ. [full title to be completed] "
     "Transplantation 84: 988\u2013996, 2007. PMID 17989604",
     "16.  Doesch AO, Celik S, Ehlermann P, Frankenstein L, Zehelein J, Koch "
     "A, Katus HA, Dengler TJ. Heart rate reduction after heart "
     "transplantation with beta-blocker versus the selective If channel "
     "antagonist ivabradine. Transplantation 84: 988\u2013996, 2007. "
     "doi:10.1097/01.tp.0000285265.86954.80. PMID 17989604"),
]

# New reference 17 (ivabradine PK), appended after ref 16.
NEW_REF_17 = ("17.  Choi HY, Noh YH, Cho SH, Ghim JL, Choe S, Kim UJ, Kim HS, "
              "Jung JA, Bae KS, Lim HS. Evaluation of pharmacokinetic and "
              "pharmacodynamic profiles and tolerability after single (2.5, 5 "
              "or 10 mg) and repeated (2.5, 5 or 10 mg bid for 4.5 days) oral "
              "administration of ivabradine in healthy male Korean "
              "volunteers. Clin Ther 35: 819\u2013835, 2013. "
              "doi:10.1016/j.clinthera.2013.04.012. PMID 23755867")

DELETE_CONTAINING = [
    "AUTHOR NOTE \u2014 DELETE BEFORE SUBMISSION",
    "Revision notes \u2014 actions required before submission",
]
DELETE_RANGE_AFTER = "Revision notes \u2014 actions required before submission"


def replace_across_runs(par, old, new):
    full = "".join(r.text for r in par.runs)
    if old not in full:
        return False
    start = full.index(old)
    end = start + len(old)
    pos, spans = 0, []
    for i, r in enumerate(par.runs):
        s, e = pos, pos + len(r.text)
        if e > start and s < end:
            spans.append((i, s, e))
        pos = e
    i0, s0, _ = spans[0]
    head = par.runs[i0].text[:start - s0]
    ilast, slast, _ = spans[-1]
    tail = par.runs[ilast].text[end - slast:]
    par.runs[i0].text = head + new + tail
    for i, _, _ in spans[1:]:
        par.runs[i].text = ""
    return True


def delete_par(par):
    par._element.getparent().remove(par._element)


def main():
    shutil.copyfile(SRC, DST)
    d = docx.Document(DST)
    log = []

    # ---- global terminology --------------------------------------------
    counts = {o: 0 for o, _ in GLOBAL}
    for par in d.paragraphs:
        for old, new in GLOBAL:
            while replace_across_runs(par, old, new):
                counts[old] += 1
    for o, n in counts.items():
        log.append(("GLOBAL", True, f"'{o}' -> replaced {n}x"))
        print(f"  [GLOBAL {n:2d}x] {o}")

    # ---- targeted -------------------------------------------------------
    for why, old, new in TARGETED:
        done = any(replace_across_runs(p, old, new) for p in d.paragraphs)
        log.append(("TARGETED", done, why))
        print(f"  [{'OK ' if done else 'MISS'}] {why.split(' - ')[0]}")

    # ---- append reference 17 -------------------------------------------
    added = False
    for i, p in enumerate(d.paragraphs):
        if p.text.strip().startswith("16.  Doesch"):
            new_p = p.insert_paragraph_before(NEW_REF_17)
            new_p.style = p.style
            new_p._element.addnext(p._element)   # keep 16 before 17
            added = True
            break
    log.append(("REF17", added, "appended ivabradine PK reference"))
    print(f"  [{'OK ' if added else 'MISS'}] reference 17 appended")

    # ---- delete internal notes -----------------------------------------
    to_del, hit = [], False
    for p in d.paragraphs:
        if any(k in p.text for k in DELETE_CONTAINING):
            if DELETE_RANGE_AFTER in p.text:
                hit = True
            to_del.append(p)
            continue
        if hit:
            to_del.append(p)
    for p in to_del:
        delete_par(p)
    log.append(("DELETE", True, f"removed {len(to_del)} internal-note "
                                f"paragraphs (AUTHOR NOTE + Revision notes)"))
    print(f"  [OK ] removed {len(to_del)} internal-note paragraphs")

    d.save(DST)
    print(f"\n-> {DST}")
    with open(r"D:\zhou-san\07_v6_cleanup\v6_edit_log.txt", "w",
              encoding="utf-8") as f:
        for kind, ok, why in log:
            f.write(f"[{kind}][{'APPLIED' if ok else 'NOT FOUND'}] {why}\n")


if __name__ == "__main__":
    main()
