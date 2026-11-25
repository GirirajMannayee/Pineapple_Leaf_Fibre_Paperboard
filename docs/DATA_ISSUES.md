# Known data issues and interpretation limits

These points are either stated by the manuscript itself (Sections 4.12, 4.13, Tables 39–40) or were found while building this datapack. They are **properties of the source data**, not errors introduced by the transcription. Resolve them with the original laboratory records before reusing the data for quantitative claims.

## A. Cross-dataset inconsistencies (the most important)

| Quantity | 30-run RSM workbook | Specimens / DOE | Package groups |
|---|---|---|---|
| Add-on at ≈15 µm | 1.61 g m⁻² (centre-run mean) → implied density ≈ 0.11 g cm⁻³ | 14.2 g m⁻² (SP-FT05) → ≈ 0.95 g cm⁻³ | — |
| Cobb60 at ≈15 µm | 81.6 g m⁻² (centre-run mean) ≈ the **uncoated** group (80.9) | 25–26 g m⁻² (DOE R09–R10) | 24.6 g m⁻² (coated) |
| WVTR at ≈15 µm | 407 g m⁻² day⁻¹ ≈ uncoated (416) | — | 281 (coated) |
| Tensile MD | 31.8 kN m⁻¹ | 3.5–4.2 kN m⁻¹ | 30.5–35.2 kN m⁻¹ |

**Consequence.** The RSM models describe *relative* factor effects inside one workbook. The *absolute* predicted optimum (Cobb60 ≈ 67 g m⁻², WVTR ≈ 344 g m⁻² day⁻¹) must **not** be interpreted as equivalent to the package-group coated values (Cobb60 24.6). `results/cross_dataset_comparison.csv` and `Fig30` document the gap. A single, authoritative workbook (or a documented calibration) is needed before any absolute claim.

## B. Design and statistical structure

1. **Replicates are not independent runs.** `08_rsm_replicates` (90 rows) are three technical sub-samples of each of the 30 runs; the models are fitted to the 30 run means. Package (n = 5) and storage (n = 3) replicates may likewise share a coating batch. Generalise at the batch level.
2. **Pure error comes from six centre runs only** (5 df). Lack-of-fit p-values are therefore low-power.
3. **Grease-kit rating is ordinal and floor-limited** (minimum 1.0; three runs at the floor). It is modelled as continuous, as in the paper.
4. **Non-monotonic thickness effect.** Mean Cobb60 at 5 µm (78.6) is below that at 15 µm (81.6) in the RSM workbook, while the DOE shows the expected decrease. Treat the A² structure as an empirical fit.
5. **Predicted R² is low for compression (0.51) and drying energy (0.32).** Their predictions are weak surrogates.
6. **Optimum sits on a design boundary** (FSM 5 %, the upper limit) with leverage 0.44 against a maximum design-point leverage of 0.66. It is an extrapolation-adjacent prediction and requires physical confirmation.
7. **Desirability anchors** (Cobb60 90→70, WVTR 430→340, grease 1→4, folding 80→95, compression 200→225) are analyst-chosen, not regulatory limits. OTR and drying energy are excluded from the objective.

## C. Preparation records (Table 39 / `Calc_Prep_Checks`)

* **Pulp composition sums to 103.3 % (B01) and 103.0 % (B02)** — components were presumably reported on different analytical bases.
* **FSM B02 total solids** reported 4.5 %; dry solids / wet mass gives 4.69 % (difference 0.19 points). B01 agrees.
* **Pulp and FSM yields** recompute exactly from the masses.
* **Turmeric extract**: particle size and curcumin content are blank (not recorded / not measured). Turmeric loading is stated *relative to dry FSM* in some places and as a share of solids in others; confirm the basis.

## D. Coating DOE (Tables 27–28)

* Only **10 of the 30 planned runs** are populated; **turmeric level is confounded with thickness** (all 25 µm runs except R02 carry 1.0 %), so the independent turmeric effect cannot be estimated.
* Contact-angle, viscosity-by-solids and similar statements in Section 4.7 depend on values not printed in any table and are not verifiable from this pack.

## E. Storage trial

* Day-0 values are not all zero: package condition 4.88–4.98; decay incidence 0.004 % (uncoated), 0 % (FSM-coated) and 1.91 % (commercial reference); uncoated mass loss 0.119 %. Check the day-0 sampling protocol.
* **Decay incidence is a visual score, not a microbial count.** Headspace O₂ and CO₂ show no significant group difference at day 10 (ANOVA p = 0.754 and 0.178).
* Storage rates use a pooled regression of all package replicates on day (18 points per group). The ± in Table 24 is the standard error of that pooled slope.

## F. Units and conditions not stated in the source

WVTR and OTR test conditions (temperature, relative humidity, pressure, film thickness basis), viscosity measurement conditions and the exact moisture basis of yield are **not given** in the tables. Add them to `metadata/` when the laboratory records are deposited.
