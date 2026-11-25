# Proposed confirmation experiments (model-based)

The surrogate predictions below come from `results/confirmation_runs_prediction_intervals.csv` and must be tested physically. A confirmation batch mean inside the 95 % prediction interval is consistent with the model; it does not prove the optimum.

| Run | Thickness (µm) | FSM (%) | Glycerol (%) | Drying (°C) | Purpose |
|---|---:|---:|---:|---:|---|
| C1 | 21.58 | 5.00 | 26.94 | 55.72 | Four-factor candidate (D = 0.8042) |
| C2 | 23.49 | 4.00 | 26.79 | 55.44 | FSM-capped alternative (viscosity-friendly), D = 0.7513 |
| C3 | 23.87 | 3.00 | 25.00 | 50.00 | Thickness-only baseline (D = 0.6281) |
| C4 | 15.00 | 3.00 | 25.00 | 50.00 | Centre point (model-consistency anchor) |

Recommended minimum: ≥ 3 independently prepared coating batches per run (batch, not sub-sample, as the experimental unit), measured with the same Cobb60, WVTR, grease-kit, folding and compression protocols and the **same workbook scale** as the RSM data (see `DATA_ISSUES.md`, section A). Record WVTR/OTR test conditions.
