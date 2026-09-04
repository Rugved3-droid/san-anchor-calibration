# Calibration-anchor dependence in a human sinoatrial population of models

Code, configuration, seeds, checksums and frozen analysis outputs for:

> Parmar R, Fahim MD, Budzikowski A. Calibration-Anchor Choice Materially Alters
> Predicted Verapamil–Ivabradine Sinoatrial Susceptibility in a Human Population
> of Models. Submitted to *Am J Physiol Heart Circ Physiol* (Methods and Resources).

## Verified artifact checksums (SHA256)

| Artifact | SHA256 |
|---|---|
| `model/fabbri_2017.cellml` | `9062dd65533092914e04e425e09a81209aae9b44b37adae223f5f8e68b2aa1ec` |
| `model/lhs_sample.npz` (primary, seed 20260816) | `f6867756c3589bacc6457351ff15af3e48664f09e176035a96ea68fdb9d7b238` |
| `model/lhs_sample_independent.npz` (seed 788156539) | `7126bde6aaa4772505454c6c16550d597d8206a763d399210594f67bfe50bb78` |
| `00_config/config.yaml` | see `08_taskP/P4_hashes.json` |
| primary retained population (n = 1028) | `f52879d3db435b198cc68f2dcff51fb498209bde949a248d5ae98d738ebf59be` |
| independent retained population (n = 1044) | `445ea46bd008f356d2a162cfdc11c5cba64b63d7fbf215cb7c5ca6d06bf49e71` |

The model itself is available from the Physiome Model Repository, exposure
[e/568](https://models.physiomeproject.org/e/568).

## Committed random seeds

All seeds were recorded before the corresponding results existed.

| Purpose | Seed | Commitment record |
|---|---|---|
| Primary Latin hypercube sample | 20260816 | `00_config/config.yaml` |
| Independent population | 788156539 | `08_taskP/P4_SEED_COMMITMENT.json` |
| Dense-grid 500-model subset | 95429097 | `08_taskP/P3_SUBSET_COMMITMENT.json` |

Each seed is derived deterministically from a fixed character string by
`seed = int(SHA256(string)[:8], 16) mod (2^31 − 1)`; the string, digest and
resulting seed are recorded in the commitment files, together with the SHA256 of
the drawn subset index list (`08_taskP/P3_subset_500.json`).

## Layout

```
00_config/          configuration: parameters, bounds, retention criteria, rules
01_baseline/        baseline validation against Fabbri Table 5
03_population/      population aggregation and freezing
04_pharmacology/    drug mapping, block ladders, pair simulations
05_manuscript/      values manifest and figure/methods generation
06_audit/, 07_v6_cleanup/   audit and cleanup passes
08_taskP/           completed-population work, independent replication,
                    dense grid, seed commitments, decision reports
model/              CellML, both Latin hypercube samples, retained populations
outputs/            frozen analysis outputs read by the values manifest
run_full_population.py   self-contained resumable population runner
```

Raw per-simulation checkpoint files are omitted for size; they are fully
regenerable from the code, the committed seeds and the frozen samples.

## Reproducing

```
python run_full_population.py --workers 8            # primary population
python 08_taskP/P4_population.py                     # independent population
python 08_taskP/P2_anchor_experiment.py --workers 8  # anchor experiment
python 08_taskP/P3_dense_grid.py --workers 8         # dense exposure grid
```

Every stage verifies the checksum of its inputs and aborts on mismatch.

## Study-integrity rule

No quantity derived from a drug combination was used, directly or indirectly, to
set or adjust any model parameter. Single-drug effects were calibrated to
monotherapy observations; combination outcomes are outputs, never inputs.

## License

Code released under the MIT License. The Fabbri CellML is redistributed under its
original Physiome Model Repository terms.
