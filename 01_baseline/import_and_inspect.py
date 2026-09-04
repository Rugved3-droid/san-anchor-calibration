"""Import the Fabbri 2017 human SAN CellML into Myokit and inspect its structure.

No equations are hand-translated. The CellML file from the Physiome Model
Repository is the single source of truth for the model mathematics.
"""
import os

import myokit
import myokit.formats.cellml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CELLML = os.path.join(ROOT, "data", "models",
                      "HumanSAN_Fabbri_Fantini_Wilders_Severi_2017.cellml")
MMT = os.path.join(ROOT, "data", "models", "fabbri_2017.mmt")

imp = myokit.formats.importer("cellml")
model = imp.model(CELLML)

print(f"model name : {model.name()}")
print(f"states     : {model.count_states()}")
print(f"components : {len(list(model.components()))}")

t = model.time()
print(f"\ntime variable : {t.qname()}  unit={t.unit()}")

vm = model.label("membrane_potential")
if vm is None:
    cands = [v for v in model.states() if v.name().lower() in ("v", "vm")]
    vm = cands[0] if cands else None
print(f"membrane V    : {vm.qname() if vm else None}  unit="
      f"{vm.unit() if vm else None}")

print("\n-- state variables --")
for v in model.states():
    print(f"   {v.qname():40s} init={v.initial_value(as_float=True):+.6g}  "
          f"unit={v.unit()}")

print("\n-- components --")
for c in model.components():
    print(f"   {c.name()}")

# Validate: a model that does not validate must not be silently simulated.
model.validate()
print(f"\nvalidation: OK  (warnings: {len(model.warnings())})")
for w in model.warnings():
    print(f"   WARNING {w}")

# These two components can silently invalidate a "baseline" run if their
# switches are not at control values, so they are printed explicitly.
for cname in ("Voltage_clamp", "Rate_modulation_experiments", "Membrane"):
    c = model.get(cname)
    print(f"\n-- {cname} --")
    for v in c.variables(deep=True):
        try:
            val = v.eval()
            print(f"   {v.qname():45s} = {val:+.6g}   {v.unit()}"
                  f"{'  [STATE]' if v.is_state() else ''}")
        except Exception:
            print(f"   {v.qname():45s} = <not constant>   {v.unit()}")

myokit.save_model(MMT, model)
print(f"\nsaved myokit model -> {MMT}")
