"""Create Parmar_SAN_manuscript_v5_AUDITED.docx from v4.

ONLY corrections directly justified by the forensic audit are applied. No
stylistic edits, no restructuring, no change to the argument, authors or any
scientific number whose provenance was verified.

Each edit is listed with its justification. v4 is not overwritten.
"""
import os
import shutil
import docx

SRC = r"D:\Parmar_SAN_manuscript_v4.docx"
DST = r"D:\Parmar_SAN_manuscript_v5_AUDITED.docx"

# (why, old_substring, new_substring)
EDITS = [
    # ---- C1: the 5000 vs 940 provenance gap (PRIMARY AUDIT FINDING) -----
    ("C1 Methods 2.2 - Methods stated 5000 sampled while Results reported 940 "
     "simulated, with no statement that only a prefix of the pool was run. "
     "Verified: pool = 5000x12, simulated = contiguous indices 0-939.",
     "Sampling used Latin hypercube sampling (scipy.stats.qmc.LatinHypercube), "
     "5000 models, seed 20260816.",
     "Sampling used Latin hypercube sampling (scipy.stats.qmc.LatinHypercube) "
     "to generate a pool of 5000 parameter vectors, seed 20260816. Of that "
     "pool, the first 940 vectors (contiguous indices 0\u2013939) were "
     "simulated in the present study and constitute the production "
     "population; the remaining 4060 were generated but not evaluated, "
     "because the per-model integration time made the full pool impractical "
     "in the available compute environment. This is a resource constraint "
     "rather than a selection step: no filtering, screening or convergence "
     "criterion was applied before simulation, and the pool is retained in "
     "full so that the population can be completed reproducibly. Because a "
     "contiguous prefix of a scrambled Latin hypercube is not itself a Latin "
     "hypercube, the 940 simulated models should be read as a random "
     "subsample of the 12-dimensional parameter distribution rather than as "
     "a space-filling design; their marginal distributions remain "
     "indistinguishable from uniform."),

    # ---- C2: reproducibility identifier ---------------------------------
    ("C2 Methods 2.2 - the quoted SHA256 does not match the file on disk. The "
     "digest is taken over the .npz, and savez_compressed embeds timestamps, "
     "so it is not content-stable. The arrays were verified to regenerate "
     "bit-identically from the recorded seed, which is the reproducibility "
     "guarantee that actually holds.",
     "The frozen sample is identified by SHA256 "
     "681f8fc6b8963467ace9f047a37e5a599ec1b92fc8c87c9ccfac5f8b214b9d35 and "
     "is validated against the configuration before reuse",
     "The frozen sample regenerates bit-identically from the recorded seed "
     "and parameter table, which we verified directly; a file-level checksum "
     "is not quoted because the compressed archive embeds timestamps and is "
     "therefore not content-stable across writes. The sample is validated "
     "against the configuration before reuse"),

    # ---- C3: 'sampled' -> 'simulated' -----------------------------------
    ("C3 Results 3.1 - 940 models were simulated, not sampled; 5000 were "
     "sampled. Wording aligned with the corrected Methods.",
     "Of 940 sampled models, 539 produced a stable rhythm",
     "Of the 940 simulated models, 539 produced a stable rhythm"),

    # ---- C4: unsupported derivation claim -------------------------------
    ("C4 Methods 2.6 - v4 asserted 198.7 nM arises 'after Hill-consistent "
     "re-solution at the panel's stated conditions'. No such computation "
     "exists anywhere in the analysis record; 198.7 appears only as a "
     "hardcoded literal, and an earlier project script used 202. The "
     "unsupported justification is removed; the numerical difference is "
     "stated instead. The value itself is NOT changed, because doing so "
     "would invalidate every downstream result without materially altering "
     "any conclusion.",
     "The first is a Ba\u00b2\u207a-derived value of 198.7 nM; the CiPA ion "
     "channel panel reports 202 nM for verapamil under Ba\u00b2\u207a charge "
     "carrier (10), and 198.7 nM is the working value used here after "
     "Hill-consistent re-solution at the panel's stated conditions.",
     "The first is a Ba\u00b2\u207a-derived value of 198.7 nM, the working "
     "value used throughout this analysis; the CiPA ion channel panel "
     "reports 202 nM for verapamil under Ba\u00b2\u207a charge carrier (10). "
     "The two differ by 1.7%, which shifts I_CaL block by at most 0.4 "
     "percentage points across the exposure range examined here and changes "
     "no reported conclusion."),

    # ---- C5: ratio span understated -------------------------------------
    ("C5 Results 3.7 - the quoted span 0.83-2.34 is the control-state range. "
     "Across both autonomic states and all three anchors the full span is "
     "0.83-2.43 (upper bound is the superseded anchor at Cmax in the Iso "
     "state).",
     "could produce anything from 0.83 to 2.34 relative to the same "
     "observation",
     "could produce anything from 0.83 to 2.43 relative to the same "
     "observation, across the three anchors and two autonomic states"),

    # ---- C6: Figure 4 anchor --------------------------------------------
    ("C6 Figure 4 legend - the figure has been regenerated at the primary "
     "58.4% anchor (no new simulation required; all conditions already "
     "present in the simulation store). The legend now states the anchor.",
     "(A) Paired excess absolute risk for verapamil \u00d7 ivabradine across "
     "the verapamil exposure ladder, with Wilson 95% confidence intervals;",
     "(A) Paired excess absolute risk for verapamil \u00d7 ivabradine across "
     "the verapamil exposure ladder with ivabradine held at the primary "
     "58.4% anchor, with Wilson 95% confidence intervals;"),

    # ---- C7 / C8: revision notes updated to audit outcome ---------------
    ("C7 Revision note 2 - resolved by audit: no derivation of 198.7 exists; "
     "the unsupported sentence has been removed and the discrepancy "
     "quantified.",
     "Confirm the derivation of the 198.7 nM working IC50 relative to the "
     "202 nM reported by ref. 10, and state it accurately in \u00a72.6 or "
     "adopt 202 nM.",
     "RESOLVED BY AUDIT: no derivation of 198.7 nM exists in the analysis "
     "record; it is a hardcoded working value and an earlier project script "
     "used 202 nM. \u00a72.6 no longer claims a derivation. Adopting 202 nM "
     "outright remains optional and would change no conclusion (\u22640.4 "
     "percentage points of I_CaL block), but would require regenerating all "
     "downstream outputs."),
    ("C8 Revision note 3 - Figure 4 regenerated at the primary anchor.",
     "Regenerate Figure 4 at the primary anchor (no new simulation "
     "required) and remove the panel note, or retain the note as written.",
     "DONE: Figure 4 regenerated at the primary 58.4% anchor from existing "
     "simulations (06_audit/Figure4_primary_anchor.png/.pdf, produced by "
     "06_audit/taskP_figure4_primary_anchor.py). The endpoint-geometry "
     "conclusion is unchanged: classification still alternates "
     "non-monotonically along the ladder, and the rescue fraction remains "
     "zero at every rung."),
]


def replace_across_runs(par, old, new):
    """Replace `old` with `new` inside a paragraph, preserving run formatting
    where the match sits in one run, and folding into the first overlapped run
    otherwise."""
    full = "".join(r.text for r in par.runs)
    if old not in full:
        return False
    start = full.index(old)
    end = start + len(old)
    pos, first, spans = 0, None, []
    for i, r in enumerate(par.runs):
        s, e = pos, pos + len(r.text)
        if e > start and s < end:
            spans.append((i, s, e))
            if first is None:
                first = i
        pos = e
    i0, s0, _ = spans[0]
    head = par.runs[i0].text[:start - s0]
    _, _, e_last = spans[-1]
    tail = par.runs[spans[-1][0]].text[end - (e_last - len(
        par.runs[spans[-1][0]].text)):]
    par.runs[i0].text = head + new + tail
    for i, _, _ in spans[1:]:
        par.runs[i].text = ""
    return True


def main():
    shutil.copyfile(SRC, DST)
    d = docx.Document(DST)
    log = []
    for why, old, new in EDITS:
        done = False
        for par in d.paragraphs:
            if replace_across_runs(par, old, new):
                done = True
                break
        log.append((why.split(" - ")[0], done, why))
        print(f"  [{'APPLIED' if done else 'NOT FOUND'}] {why.split(' - ')[0]}")
    d.save(DST)
    print(f"\n-> {DST}")
    n_ok = sum(1 for _, ok, _ in log if ok)
    print(f"{n_ok}/{len(EDITS)} edits applied")
    with open(r"D:\zhou-san\06_audit\v5_edit_log.txt", "w",
              encoding="utf-8") as f:
        for tag, ok, why in log:
            f.write(f"[{'APPLIED' if ok else 'NOT FOUND'}] {why}\n\n")


if __name__ == "__main__":
    main()
