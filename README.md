# PALF–FSM Paperboard Datapack

**Data, code, figures and Excel workbook for**
*Pineapple Leaf Fibre Paperboard with Fenugreek Mucilage–Turmeric Biocoatings for Improved Barrier Performance and Optimisation*

[![tests](https://img.shields.io/badge/tests-8%20passed-brightgreen)]() [![reproduced](https://img.shields.io/badge/manuscript%20values%20reproduced-462%2F462-brightgreen)]() [![code](https://img.shields.io/badge/code-MIT-blue)]() [![data](https://img.shields.io/badge/data-CC%20BY%204.0%20(proposed)-lightgrey)]()

---

## 1. Purpose of this repository

This repository makes the quantitative content of the manuscript **findable, accessible, interoperable and reusable (FAIR)**. It exists so that a reader, reviewer or follow-up laboratory can:

1. **Inspect every number**: all measurement tables of the paper in tidy, machine-readable form (`data/raw/`, one CSV per experiment, plus an Excel workbook).
2. **Re-run every analysis**: a small Python package (`src/palf_fsm`) and numbered scripts regenerate the response-surface models, desirability optimisation, package statistics, storage kinetics and all data-driven figures from the raw CSVs.
3. **Verify the paper**: `results/reproducibility_report.csv` compares **462 recomputed quantities** with the values printed in the manuscript. All 462 agree to rounding.
4. **Plan the next experiment**: the model-predicted optimum, its 95 % prediction intervals and the proposed confirmation runs are tabulated (`results/confirmation_runs_prediction_intervals.csv`), and a live Excel calculator lets anyone predict responses for any setting inside the design space.
5. **Reuse the data**: a data dictionary documents every column, unit and provenance class (`metadata/data_dictionary.csv`).

> ### Important: what this datapack is and is not
> * The data were **transcribed programmatically from the 46 tables of the manuscript** (`scripts/00_extract_from_manuscript.py`). The original laboratory workbooks, raw instrument exports and notebooks were not available. **Deposit those alongside this pack** before submission, and replace the transcribed CSVs if any value differs.
> * Everything in `results/`, `data/processed/`, `Model_*` sheets and the calculator is **model-derived** (surrogate predictions), not measurement.
> * The manuscript itself identifies inconsistencies between its datasets (different absolute scales between the 30-run RSM workbook and the specimen/DOE/package workbooks). They are documented, not hidden, in [`docs/DATA_ISSUES.md`](docs/DATA_ISSUES.md). Read it before reusing the data.

## 2. Repository map

```
PALF-FSM-Paperboard-Datapack/
├── README.md                     ← you are here
├── CITATION.cff · LICENSE · LICENSE-DATA.md · requirements.txt · Makefile · run_all.py
├── data/
│   ├── PALF_FSM_Complete_Datapack.xlsx          ★ complete workbook (29 sheets, 411 live formulas, native charts)
│   ├── PALF_FSM_Manuscript_Tables_T01-T46.xlsx  verbatim copy of all 46 manuscript tables
│   ├── raw/                      13 tidy measurement datasets (CSV, UTF-8)
│   ├── manuscript_tables/        Table_01 … Table_46 verbatim CSV
│   ├── reported/                 statistics as printed in the paper (used for verification)
│   └── processed/                model-derived datasets (41-point thickness grid, optimiser convergence)
├── src/palf_fsm/                 analysis package: rsm · desirability · optimise · groups · storage · transport
├── scripts/                      00 extract · 02 analyse · 03 figures · 04 Excel · 05 manifest
├── results/                      all recomputed tables (CSV) + reproducibility_report.csv
├── figures/
│   ├── generated/                30 figures, 300-dpi PNG + vector PDF
│   └── manuscript_original/      33 original manuscript figures (incl. schematics)
├── metadata/                     data_dictionary.csv · provenance.csv · manifest + SHA-256 checksums
├── docs/                         DATA_ISSUES · METHODS · DATA_AVAILABILITY_STATEMENT · CONFIRMATION_PLAN
└── tests/                        8 pytest tests (data integrity + full reproduction)
```

## 3. Datasets (`data/raw/`)

| File | Rows | Content | Manuscript source |
|---|---:|---|---|
| `01_pulp_batches.csv` | 2 | PALF pulp yield, composition, fibre length, freeness | Table 4 |
| `02_paperboard_sheets.csv` | 2 | 250 g m⁻² sheet grammage, caliper, density, strength | Table 5 |
| `03_fsm_batches.csv` | 2 | Fenugreek mucilage extraction conditions, yield, solids, pH, viscosity | Table 7 |
| `04_turmeric_preparations.csv` | 2 | Turmeric powder / extract preparation | Table 8 |
| `05_coating_formulations.csv` | 5 | U0, F1, FT05, FT10, T1 formulations | Table 9 |
| `06_rsm_factors.csv` | 4 | Factor ranges (thickness, FSM %, glycerol %, drying T) | Table 11 |
| `07_rsm_run_means.csv` | 30 | Face-centred CCD, 10 response means per run | Tables 14–15 |
| `08_rsm_replicates.csv` | 90 | Three within-run replicates per run | Tables 36–37 |
| `09_package_replicates.csv` | 15 | Uncoated / FSM-coated / commercial reference, n = 5 each | Table 21 |
| `10_storage_summary.csv` | 18 | Storage means, 3 groups × 6 days | Table 31 |
| `11_storage_replicates.csv` | 54 | Storage replicate observations (3 packages) | Table 38 |
| `12_coating_specimens.csv` | 3 | Characterised coated specimens | Tables 25–26 |
| `13_coating_doe_runs.csv` | 10 | Turmeric-containing coating DOE | Tables 27–28 |

Blank = *not recorded / not applicable* (never zero). Units, definitions and provenance classes are in `metadata/data_dictionary.csv`.

## 4. Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_all.py            # analysis → figures → Excel → manifest   (~1 min)
pytest -q                    # 8 tests
```

Single steps: `python scripts/02_run_analysis.py` · `python scripts/03_make_figures.py` · `python scripts/04_build_excel.py`.
Only NumPy, SciPy, pandas, matplotlib and openpyxl are required (`python-docx` only to re-extract from the manuscript).

## 5. What is reproduced

| Manuscript content | Result |
|---|---|
| Tables 13, 16: R², adj./pred. R², F, lack-of-fit, CV, adequate precision, Shapiro–Wilk (10 models) | ✔ identical |
| Table 17: coded coefficients (5 responses × 15 terms) | ✔ identical |
| Table 18: thickness-only optimum 23.87 µm, D = 0.6281 | ✔ |
| Table 32: DE / PSO / cockroach swarm, D = 0.8042 at 21.58 µm, 5 %, 26.94 %, 55.72 °C | ✔ |
| Table 33–34: candidate predictions and 95 % prediction intervals, leverage 0.44 | ✔ |
| Table 35: eight sensitivity scenarios | ✔ (barrier-only optimum is a D = 1 plateau: location not unique) |
| Tables 19–20, 29: package means/SD, ANOVA, Tukey, Kruskal–Wallis, Hedges *g*, GCI, series resistance | ✔ |
| Tables 22–24: storage rates (± SE of pooled slope), ΔE\*ab, threshold times | ✔ |
| Table 6, Table 39 and §4.7 coating-DOE regressions, Fig. 14 correlations | ✔ |

Two definitions needed to be inferred while reproducing the paper and are documented in the code: the "±" on storage rates is the **standard error of the pooled regression slope**, and "targets ±10 % demanding" moves the **target by 10 % of its desirability range**.
Claims in §4.7 that rest on numbers *not printed in any table* (contact-angle correlation, viscosity-by-solids means) cannot be recomputed and are not in the report.

## 6. Figures

`figures/generated/` regenerates Figs 3, 5–23, 25–30 from the raw data and adds four supplementary figures (within-run replicates, confirmation prediction intervals, optimum sensitivity, FSM × glycerol interaction). Schematic/workflow figures (1, 2, 4, 24, 31–33) are not data-driven; the original artwork is in `figures/manuscript_original/`.

## 7. Excel workbook

`data/PALF_FSM_Complete_Datapack.xlsx` — start at the **README** sheet. Highlights:

* **Desirability_Calculator**: type any four factor settings → predictions of all ten responses → individual and overall desirability (default = the four-factor candidate, D = 0.8042).
* **Calc_*** sheets: live formulas (porosity and indices, package means/SD/Δ%/GCI/Hedges *g*, series-resistance partition, SLOPE-based storage kinetics, arithmetic consistency checks).
* **Model_*** sheets: static model-derived outputs, clearly tab-coloured orange.
* **Reproducibility**: all 462 comparisons. **Charts**: native Excel charts.

## 8. How to cite

Use `CITATION.cff` (GitHub “Cite this repository”) and the DOI minted when you archive a release on Zenodo. A ready-to-paste statement for the manuscript is in [`docs/DATA_AVAILABILITY_STATEMENT.md`](docs/DATA_AVAILABILITY_STATEMENT.md).

## 9. Licences

Code: MIT (`LICENSE`). Data, figures and documentation: CC BY 4.0 is proposed (`LICENSE-DATA.md`); confirm with the authors/institution before release.
