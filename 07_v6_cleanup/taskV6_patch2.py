"""Second pass on v6: the three targeted edits whose source strings differed
from the assumed form, plus one further HCN4 phrasing fix."""
import sys
import docx

sys.path.insert(0, r"D:\zhou-san\07_v6_cleanup")
from taskV6_make_v6 import replace_across_runs          # noqa: E402

DST = r"D:\Parmar_SAN_manuscript_v6_CLEAN.docx"

EDITS = [
    ("T3a Methods 2.6 upper-bound softened",
     "Static block therefore over-states the sustained effect, over-states "
     "the fraction of models driven below threshold, and every risk estimate "
     "reported here is an upper bound.",
     "Static block is therefore expected to over-state sustained drug effect "
     "and the fraction of models driven below threshold; we accordingly "
     "interpret the resulting model-quiescence estimates as upper bounds, "
     "while recognising that the direction of this bias is inferred from "
     "published state dependence rather than demonstrated here with an "
     "explicit kinetic block model."),

    ("T3b Limitations upper-bound softened",
     "Static block is not a kinetic model, and every risk estimate is an "
     "upper bound.",
     "Static block is not a kinetic model, and the upper-bound "
     "interpretation is inferred rather than proved."),

    ("T6b Methods 2.6 HCN4 stated as the specific cited experiment",
     "The 250-fold discrepancy between the re-solved potency and the in "
     "vitro value of 2000 nM for human HCN4 (15) is unexplained",
     "The \u2248250-fold discrepancy between the re-solved potency and the "
     "\u22482.0 \u00b5M half-block concentration reported in the cited human "
     "HCN4 experiment (15) is unexplained"),

    ("T6c Limitations HCN4 stated as the cited experiment, not a universal "
     "value",
     "The primary anchor implies a potency approximately 250-fold from "
     "published in vitro values (15).",
     "The primary anchor implies a potency approximately 250-fold from the "
     "\u22482.0 \u00b5M half-block concentration reported in the cited human "
     "HCN4 experiment (15); reported HCN4 potency varies across experimental "
     "protocols and channel states, so this ratio is specific to that "
     "comparison."),
]

d = docx.Document(DST)
for why, old, new in EDITS:
    ok = any(replace_across_runs(p, old, new) for p in d.paragraphs)
    print(f"  [{'OK ' if ok else 'MISS'}] {why}")
d.save(DST)
print(f"\n-> {DST}")
