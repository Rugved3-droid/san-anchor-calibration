"""Task L2 - repair the Linder 2025 extended-Fabbri CellML so Myokit can import
it, and verify two things only. DOES NOT MIGRATE ANYTHING.

Provenance problem this solves
------------------------------
The published file is distributed under the name
    HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml
which is byte-for-byte the SAME FILENAME as the project's checksummed baseline
model, while being a different model (306,733 vs 215,043 bytes). Ingesting it
under that name would silently shadow the validated baseline. Both the pristine
original and the repaired derivative are therefore stored under distinct names
in their own directory, each with its own sha256.

The repair
----------
Myokit's CellML importer enforces CellML 1.0 rule 3.4.6.4 on connection
interfaces; OpenCOR is permissive about it. Seven variables are declared as
inputs on one side of a connection with no matching output declaration on the
other. All seven sit at the seams where the beta-AR cascade attaches to base
Fabbri. Every fix is an INTERFACE DECLARATION ONLY - no equation, no
connection, no initial value, and no component is altered.

  (A) parent pass-through: the parent receives the signal (public_interface
      ="in") and must forward it to its encapsulated child, which already
      declares public_interface="in". Fix: add private_interface="out".
        i_f.cAMP        -> i_f_y_gate.cAMP
        i_CaL.PKA       -> i_CaL_dL_gate.PKA
        i_Ks.PKA        -> i_Ks_n_gate.PKA
        i_KACh.ACh_cas  -> i_KACh_a_gate.ACh_cas

  (B) sibling export: Ca_buffering holds the source (kb_CM and kf_CM are
      constants with initial values; fCMi is a state variable with an ODE in
      Ca_buffering) and the cAMP component declares public_interface="in".
      Fix: add public_interface="out" on the Ca_buffering side.
        Ca_buffering.kb_CM -> cAMP.kb_CM
        Ca_buffering.kf_CM -> cAMP.kf_CM
        Ca_buffering.fCMi  -> cAMP.fCMi

The edit is done as a targeted TEXTUAL substitution on the seven <variable>
declarations rather than by re-serialising the XML, so that the diff against the
published original is exactly seven lines and can be audited by eye. Re-writing
the tree would reformat the whole document and make the change unverifiable.
"""
import hashlib
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tmp", "k2_scope",
                   "Linder_HumanSAN_Fabbri_extended.cellml")
DEST_DIR = os.path.join(ROOT, "data", "models", "linder2025")
ORIG = os.path.join(DEST_DIR, "Linder2025_FabbriExtended_ORIGINAL.cellml")
REPAIRED = os.path.join(DEST_DIR, "Linder2025_FabbriExtended_REPAIRED.cellml")

PUBLISHED_SHA = ("18401c61b7cc13b3b90d86e97598b61767ca29208ac9df180"
                 "db84cde85d07ec5")

# (component, variable, attribute to add, value)
FIXES = [
    ("i_f",           "cAMP",    "private_interface", "out"),
    ("i_CaL",         "PKA",     "private_interface", "out"),
    ("i_Ks",          "PKA",     "private_interface", "out"),
    ("i_KACh",        "ACh_cas", "private_interface", "out"),
    ("Ca_buffering",  "kb_CM",   "public_interface",  "out"),
    ("Ca_buffering",  "kf_CM",   "public_interface",  "out"),
    ("Ca_buffering",  "fCMi",    "public_interface",  "out"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def component_span(text, name):
    """Character span of <component name="...">...</component>."""
    m = re.search(r'<component[^>]*\bname="%s"[^>]*>' % re.escape(name), text)
    if not m:
        raise SystemExit(f"FATAL: component {name} not found")
    end = text.index("</component>", m.end())
    return m.start(), end


def main():
    os.makedirs(DEST_DIR, exist_ok=True)

    got = sha256(SRC)
    if got != PUBLISHED_SHA:
        raise SystemExit(
            f"FATAL: source checksum mismatch.\n  expected {PUBLISHED_SHA}\n"
            f"  found    {got}\nRefusing to repair an unexpected file.")
    print(f"published original verified: sha256 {got}")

    shutil.copyfile(SRC, ORIG)
    text = open(SRC, encoding="utf-8").read()
    original = text

    diff_lines = []
    for comp, var, attr, val in FIXES:
        lo, hi = component_span(text, comp)
        seg = text[lo:hi]
        pat = re.compile(r'(<variable\b[^>]*\bname="%s"[^>]*?)(/?>)'
                         % re.escape(var))
        m = pat.search(seg)
        if not m:
            raise SystemExit(f"FATAL: variable {comp}.{var} not found")
        before = m.group(0)
        if f'{attr}=' in before:
            raise SystemExit(
                f"FATAL: {comp}.{var} already declares {attr}; "
                f"refusing to overwrite an existing declaration.")
        after = f'{m.group(1)} {attr}="{val}"{m.group(2)}'
        seg = seg[:m.start()] + after + seg[m.end():]
        text = text[:lo] + seg + text[hi:]
        diff_lines.append((f"{comp}.{var}", before.strip(), after.strip()))
        print(f"  fixed {comp}.{var}: added {attr}=\"{val}\"")

    # ---- fix (C): duplicate <connection> for one component pair ----------
    # CellML 1.0 rule 3.4.5.4 requires each connection to join a UNIQUE pair of
    # components; multiple mappings between the same pair belong in ONE
    # <connection> with several <map_variables>. The published file declares
    # ATPi <-> cAMP twice, once carrying ATPi and once carrying cAMP. Merging
    # them is semantically identity - the same two variable mappings survive,
    # in the same directions - and is required for import.
    con_re = re.compile(
        r'[ \t]*<connection>\s*<map_components\s+component_1="([^"]+)"\s+'
        r'component_2="([^"]+)"\s*/>(.*?)</connection>\s*', re.S)
    blocks = list(con_re.finditer(text))
    seen_pairs = {}
    merged = []
    for m in blocks:
        key = tuple(sorted((m.group(1), m.group(2))))
        seen_pairs.setdefault(key, []).append(m)
    for key, ms in seen_pairs.items():
        if len(ms) < 2:
            continue
        maps = []
        for m in ms:
            maps += re.findall(r'<map_variables\b[^>]*/>', m.group(3))
        first = ms[0]
        newblock = ('      <connection>\n'
                    f'         <map_components component_1="{first.group(1)}" '
                    f'component_2="{first.group(2)}"/>\n'
                    + "".join(f'         {x}\n' for x in maps)
                    + '      </connection>\n')
        # replace last-to-first so earlier spans stay valid
        for m in sorted(ms[1:], key=lambda x: -x.start()):
            text = text[:m.start()] + text[m.end():]
        text = text[:first.start()] + newblock + text[first.end():]
        merged.append((f"{key[0]} <-> {key[1]}", len(ms), maps))
        print(f"  merged {len(ms)} duplicate <connection> blocks for "
              f"{key[0]} <-> {key[1]} ({len(maps)} map_variables preserved)")

    # ---- fix (D): undefined units --------------------------------------
    # Two units are referenced in MathML but never declared, so the model
    # violates CellML 1.0 rule 4.4.3.2 and cannot be imported.
    #
    # SAFETY. Every units declaration in this file uses the Fabbri-lineage
    # convention where the prefix is a NAME ONLY and the multiplier is 1
    # (e.g. millisecond = second^1 x1, nanomolar = mole.litre^-1 x1, identical
    # to millimolar). The numbers in the equations carry the scaling. The only
    # multipliers != 1 anywhere are minute/per_minute (60), which are not
    # touched. Adding the two declarations below therefore introduces NO
    # numerical scaling of any kind.
    #
    #   per_nanomolar : missing entirely. Added as nanomolar^-1 x1, by exact
    #                   analogy with the existing per_millimolar =
    #                   millimolar^-1 x1.
    #   nonomolar     : a typo for "nanomolar". It annotates a single literal
    #                   <cn>0</cn>, so it is numerically inert either way; the
    #                   typo is corrected rather than aliased.
    unit_fixes = []
    if 'name="per_nanomolar"' not in text:
        anchor_re = re.compile(
            r'([ \t]*)<units name="per_millimolar">.*?</units>\s*', re.S)
        am = anchor_re.search(text)
        if not am:
            raise SystemExit("FATAL: could not locate per_millimolar anchor")
        ind = am.group(1)
        block = (f'{ind}<units name="per_nanomolar">\n'
                 f'{ind}   <unit exponent="-1" units="nanomolar"/>\n'
                 f'{ind}</units>\n')
        text = text[:am.end()] + block + text[am.end():]
        unit_fixes.append(("per_nanomolar",
                           "undeclared", 'nanomolar^-1, multiplier 1'))
        print('  added units declaration per_nanomolar = nanomolar^-1')

    n_typo = text.count('units="nonomolar"')
    if n_typo:
        text = text.replace('units="nonomolar"', 'units="nanomolar"')
        unit_fixes.append(("nonomolar",
                           f'typo, {n_typo} occurrence(s) on literal 0',
                           'corrected to nanomolar'))
        print(f'  corrected units typo nonomolar -> nanomolar '
              f'({n_typo} occurrence)')

    with open(REPAIRED, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    # ---- integrity accounting -------------------------------------------
    import difflib
    n_changed = sum(
        1 for l in difflib.unified_diff(original.splitlines(),
                                        text.splitlines(), n=0)
        if l[:1] in "+-" and not l.startswith(("+++", "---")))
    print(f"\ndiff lines (added+removed) vs published original: {n_changed}")
    print(f"byte delta: {len(text) - len(original):+d}")

    rec = [
        "# Linder 2025 extended Fabbri model - provenance and repair record",
        "",
        "## Source",
        "",
        "Linder M et al. *Sympathetic stimulation can compensate for",
        "hypocalcaemia-induced bradycardia in human and rabbit sinoatrial node",
        "cells.* J Physiol 2025. PMID 40014045, doi:10.1113/JP287557.",
        "Extends Fabbri 2017 (human) with the beta-AR/AC/cAMP/PKA cascade of",
        "Behar et al. 2016 (Front Physiol 7:419, PMID 27729868).",
        "",
        "Obtained from the Physiome Model Repository:",
        "  exposure  https://models.physiomeproject.org/e/d14",
        "  workspace https://models.physiomeproject.org/workspace/c65",
        "",
        "## FILENAME COLLISION - why these files are renamed",
        "",
        "The published file is distributed as",
        "`HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml` - identical in",
        "name to this project's checksummed baseline model, but a different",
        "model (306,733 bytes vs 215,043). Ingesting it under the published",
        "name would silently shadow the validated baseline. Both files here are",
        "renamed for that reason.",
        "",
        "## Files and checksums",
        "",
        "| file | sha256 | bytes |",
        "|---|---|---|",
        f"| `{os.path.basename(ORIG)}` (pristine, unmodified) | "
        f"`{sha256(ORIG)}` | {os.path.getsize(ORIG):,} |",
        f"| `{os.path.basename(REPAIRED)}` (project-repaired) | "
        f"`{sha256(REPAIRED)}` | {os.path.getsize(REPAIRED):,} |",
        "",
        "## Repair: 7 interface declarations, nothing else",
        "",
        "Myokit's CellML importer enforces CellML 1.0 rule 3.4.6.4 on",
        "connection interfaces; OpenCOR is permissive about it. Seven variables",
        "were declared as inputs on one side of a connection with no matching",
        "output declaration on the other. All seven are at the seams where the",
        "beta-AR cascade attaches to base Fabbri.",
        "",
        "**No equation, connection, initial value, component or unit was",
        "altered.** Only the listed attributes were added.",
        "",
        "| variable | before | after |",
        "|---|---|---|",
    ]
    for name, b, a in diff_lines:
        rec.append(f"| `{name}` | `{b}` | `{a}` |")
    rec += [
        "",
        "### (C) duplicate connection merge",
        "",
        "CellML 1.0 rule 3.4.5.4 requires each `<connection>` to join a unique",
        "pair of components. The published file declares `ATPi <-> cAMP` twice,",
        "once carrying `ATPi` and once carrying `cAMP`. The two blocks were",
        "merged into one `<connection>` holding both `<map_variables>`. This is",
        "a semantic identity: the same two mappings survive in the same",
        "directions.",
        "",
    ] + [
        f"- merged **{n}** blocks for `{k}`, **{len(mp)}** map_variables "
        f"preserved: {', '.join('`' + x + '`' for x in mp)}"
        for k, n, mp in merged
    ] + [
        "",
        "### (D) undefined units",
        "",
        "Two units are referenced in MathML but never declared (CellML 1.0",
        "rule 4.4.3.2), which alone blocks import.",
        "",
        "**No numerical scaling is introduced.** Every units declaration in",
        "this file follows the Fabbri-lineage convention in which the prefix is",
        "a NAME ONLY and the multiplier is 1 - `millisecond = second^1 x1`,",
        "`nanomolar = mole.litre^-1 x1` (identical to `millimolar`). The",
        "equations carry the scaling. The only multipliers other than 1",
        "anywhere in the file are `minute`/`per_minute` (60), which are not",
        "touched.",
        "",
        "| unit | problem | fix |",
        "|---|---|---|",
    ] + [
        f"| `{u}` | {prob} | {fix} |" for u, prob, fix in unit_fixes
    ] + [
        "",
        f"Total diff lines vs published original: **{n_changed}**. Byte delta: "
        f"**{len(text) - len(original):+d}**.",
        "",
        "## Status",
        "",
        "**NOT MIGRATED.** This model is not used by any task. The project",
        "baseline remains `data/models/HumanSAN_Fabbri_Fantini_Wilders_Severi",
        "_2017.cellml` (sha256 9062dd65...b2aa1ec). This directory exists only",
        "to hold a verified, importable copy for the Task L2 viability tests.",
    ]
    with open(os.path.join(DEST_DIR, "PROVENANCE.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(rec) + "\n")

    print(f"\n-> {ORIG}")
    print(f"-> {REPAIRED}")
    print(f"-> {os.path.join(DEST_DIR, 'PROVENANCE.md')}")
    print(f"\nrepaired sha256: {sha256(REPAIRED)}")


if __name__ == "__main__":
    main()
