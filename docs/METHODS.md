# Computational methods

All methods follow the manuscript equations; NumPy/SciPy only.

## Response-surface models (`rsm.py`)
Factors are coded to −1/0/+1 (`x = (X − centre)/half-range`). For each of the 10 responses the full quadratic model (15 terms) is fitted by ordinary least squares to the 30 run means. Reported statistics: R², adjusted R², predicted R² (PRESS, leave-one-out), model F and p, lack-of-fit F from the six centre runs, RMSE = √(SSE/n) (manuscript Eq. 25), CV = √MSE/ȳ, adequate precision = (ŷmax − ŷmin)/√(p·MSE/n), Shapiro–Wilk on residuals. Prediction intervals for a new observation use ŷ ± t(0.975, 15)·√(MSE(1 + z′(Z′Z)⁻¹z)) (Eq. 29).

## Desirability and optimisation (`desirability.py`, `optimise.py`)
Linear Derringer–Suich functions (smaller-is-better: Cobb60, WVTR; larger-is-better: grease, folding, compression) combined by a weighted geometric mean. Optimisers: differential evolution (SciPy, Sobol init, polished), particle swarm (own implementation, 40 particles × 300 iterations) and cockroach-swarm optimisation (own implementation with local refinement); ten DE seeds converge to the same optimum. A thickness-only search (41-point grid + bounded refinement) gives the baseline.

## Package comparisons (`groups.py`)
One-way ANOVA, Tukey HSD, Kruskal–Wallis, Hedges *g* (small-sample corrected), gap-closure index GCI = (coated − uncoated)/(reference − uncoated).

## Storage (`storage.py`)
Zero-order rates from the pooled regression on day (± SE of slope); CIE76 ΔE\*ab against day 0 from group-mean L\*a\*b\*; threshold times by linear interpolation of group means.

## Transport (`transport.py`)
Series model: BIF = P_uncoated/P_coated; coating-alone rate = 1/(1/P_coated − 1/P_uncoated); coating resistance share = 1 − P_coated/P_uncoated; defect ceiling = 1/(1 − coverage).

## Verification
`scripts/02_run_analysis.py` writes `results/reproducibility_report.csv`; tolerances equal half a unit in the last printed digit. `tests/` asserts every row reads `REPRODUCED`.
