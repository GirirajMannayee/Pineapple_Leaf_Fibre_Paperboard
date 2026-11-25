#!/usr/bin/env python3
"""
02_run_analysis.py
==================
Re-runs every quantitative analysis of the manuscript from the raw CSVs in
data/raw and writes

    results/*.csv                     all recomputed tables
    data/processed/*.csv              model-derived datasets (grid, predictions)
    results/reproducibility_report.csv  one row per checked quantity:
                                        recomputed vs. value printed in the paper

Run:  python scripts/02_run_analysis.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from palf_fsm import desirability as dz                      # noqa: E402
from palf_fsm import groups as gr                            # noqa: E402
from palf_fsm import io, optimise as op, rsm, storage as st, transport as tr   # noqa: E402

RES, PROC, REP = io.RESULTS, io.PROCESSED, io.REPORTED
RES.mkdir(exist_ok=True); PROC.mkdir(parents=True, exist_ok=True)
CHECKS = []


def fnum(x):
    """First number in a reported string ('<0.001' -> 0.001 flagged separately)."""
    m = re.search(r"-?\d+\.?\d*", str(x).replace("\u2212", "-").replace(",", ""))
    return float(m.group()) if m else np.nan


def check(section, item, computed, reported, tol):
    ok = bool(abs(computed - reported) <= tol) if not (np.isnan(computed) or np.isnan(reported)) else False
    CHECKS.append(dict(section=section, quantity=item, recomputed=computed, reported=reported,
                       abs_diff=abs(computed - reported), tolerance=tol,
                       status="REPRODUCED" if ok else "DIFFERS"))


# ============================================================ 1. RSM
runs = io.run_means()
fits = rsm.fit_all(runs, list(io.RESPONSES))
adeq = pd.DataFrame([{
    "response": io.RESPONSES[k], "column": k, "R2": f.r2, "Adj_R2": f.adj_r2, "Pred_R2": f.pred_r2,
    "RMSE": f.rmse, "F": f.F, "p_model": f.p_model, "LOF_p": f.lof_p, "CV_pct": f.cv_pct,
    "Adeq_precision": f.adeq_prec, "Shapiro_p": f.shapiro_p} for k, f in fits.items()])
adeq.to_csv(RES / "rsm_model_adequacy.csv", index=False)

coef = pd.concat([f.coef_table().assign(response=io.RESPONSES[k]) for k, f in fits.items()])
coef.to_csv(RES / "rsm_coded_coefficients_all_responses.csv", index=False)
wide = coef.pivot(index="term", columns="response", values="coef").reindex(rsm.TERMS)
wide.to_csv(RES / "rsm_coded_coefficients_wide.csv")

rep13 = pd.read_csv(REP / "reported_T13_model_fit.csv")
rep16 = pd.read_csv(REP / "reported_T16_model_adequacy.csv")
for (k, f), (_, a), (_, b) in zip(fits.items(), rep13.iterrows(), rep16.iterrows()):
    n = io.RESPONSES[k]
    check("Table 13", f"{n} R2", f.r2, fnum(a.r2), 5e-5)
    check("Table 13", f"{n} RMSE", f.rmse, fnum(a.rmse), 5e-5)
    check("Table 16", f"{n} adj R2", f.adj_r2, fnum(b.adj_r2), 5e-4)
    check("Table 16", f"{n} pred R2", f.pred_r2, fnum(b.pred_r2), 5e-4)
    check("Table 16", f"{n} F", f.F, fnum(b.F), 0.06)
    check("Table 16", f"{n} LOF p", f.lof_p, fnum(b.lof_p), 5e-4)
    check("Table 16", f"{n} CV %", f.cv_pct, fnum(b.cv_pct), 0.006)
    check("Table 16", f"{n} adeq. precision", f.adeq_prec, fnum(b.adeq_prec), 0.06)
    check("Table 16", f"{n} Shapiro p", f.shapiro_p, fnum(b.shapiro_p), 5e-4)

# Table 17 coded coefficients (five desirability responses)
rep17 = pd.read_csv(REP / "reported_T17_coded_coefficients.csv")
col_map = {"Cobb60": "cobb60_g_m2", "WVTR": "wvtr_g_m2_day", "Grease_kit": "grease_kit",
           "Folding": "fold_double_folds", "Compression": "compression_n"}
for _, r in rep17.iterrows():
    ti = rsm.TERMS.index(r["term"].split(" ")[0].strip())
    for nm, c in col_map.items():
        rep_v = fnum(r[nm]); dec = 3 if nm == "Grease_kit" else 2
        check("Table 17", f"coef {r['term'].split('  ')[0].strip()} / {nm}",
              fits[c].beta[ti], rep_v, 0.5 * 10 ** -dec + 1e-9)

# significance of each coded term (for Fig. 6)
coef[coef.response.isin(["Cobb60", "WVTR", "Grease kit"])].to_csv(RES / "rsm_standardised_effects_fig6.csv", index=False)

# ============================================================ 2. Thickness-only + 41-pt grid
grid, Dg, a_opt, D_opt = op.thickness_only(fits)
rows = []
for a, d in zip(grid, Dg):
    xc = np.array([[(a - 15) / 10, 0, 0, 0]])
    row = {"thickness_um": a, "overall_desirability": d}
    row.update({k: float(f.predict(xc)[0]) for k, f in fits.items()})
    rows.append(row)
pd.DataFrame(rows).to_csv(PROC / "thickness_grid_41_points_model_derived.csv", index=False)
xc = np.array([[(a_opt - 15) / 10, 0, 0, 0]])
cand_thick = {k: float(f.predict(xc)[0]) for k, f in fits.items()}
pd.DataFrame([{"thickness_um": a_opt, "desirability": D_opt, **cand_thick}]).to_csv(
    RES / "optimum_thickness_only.csv", index=False)
check("Table 18", "thickness optimum (µm)", a_opt, 23.87, 0.005)
check("Table 18", "overall desirability", D_opt, 0.6281, 5e-5)
for k, v in {"cobb60_g_m2": 75.73, "wvtr_g_m2_day": 359.2, "grease_kit": 3.31, "fold_double_folds": 86.13,
             "compression_n": 213.84, "otr_cm3_m2_day": 1630.93, "coating_add_on_g_m2": 1.987,
             "drying_energy_kwh_kg": 0.4648}.items():
    check("Table 18", f"predicted {io.RESPONSES[k]}", cand_thick[k], v, 0.006 * max(1, abs(v) / 100) + 0.005)

# ============================================================ 3. four-factor optimisation
obj = op.make_objective(fits)
xde, Dde = op.run_de(obj)
xpso, Dpso, hpso = op.run_pso(obj, seed=1)
xcso, Dcso, hcso = op.run_cso(obj, seed=1)
opt_tbl = pd.DataFrame([
    ["Differential evolution (DE)", *rsm.decode(xde)[0], Dde],
    ["Particle swarm optimisation (PSO)", *rsm.decode(xpso)[0], Dpso],
    ["Cockroach swarm optimisation", *rsm.decode(xcso)[0], Dcso],
    ["Thickness-only search", a_opt, 3.0, 25.0, 50.0, D_opt]],
    columns=["algorithm", "thickness_um", "fsm_solids_pct", "glycerol_pct_dry_fsm",
             "drying_temp_c", "desirability"])
opt_tbl.to_csv(RES / "optimiser_comparison.csv", index=False)
pd.DataFrame({"iteration": np.arange(len(hpso)), "PSO": hpso, "Cockroach": hcso}).to_csv(
    PROC / "optimiser_convergence.csv", index=False)
rep32 = pd.read_csv(REP / "reported_T32_optimiser_comparison.csv")
for (_, a), (_, b) in zip(opt_tbl.iterrows(), rep32.iterrows()):
    for c in ["thickness_um", "fsm_solids_pct", "glycerol_pct_dry_fsm", "drying_temp_c"]:
        check("Table 32", f"{a['algorithm']} {c}", a[c], fnum(b.iloc[1 + ["thickness_um", "fsm_solids_pct", "glycerol_pct_dry_fsm", "drying_temp_c"].index(c)]), 0.02)
    check("Table 32", f"{a['algorithm']} desirability", a.desirability, fnum(b.iloc[5]), 5e-5)

# multi-seed DE convergence
seeds = [op.run_de(obj, seed=s) for s in range(10)]
sd = pd.DataFrame([{"seed": i, "desirability": d, **dict(zip(["A", "B", "C", "D"], rsm.decode(x)[0]))}
                   for i, (x, d) in enumerate(seeds)])
sd.to_csv(RES / "de_ten_seed_check.csv", index=False)
check("Section 4.11", "DE 10-seed desirability spread", sd.desirability.max() - sd.desirability.min(), 0.0, 1e-9)

# predicted responses at candidate (Table 33)
cand_nat = rsm.decode(xde)[0]
xcand = rsm.code(cand_nat[None, :])
cand_pred = {k: float(f.predict(xcand)[0]) for k, f in fits.items()}
pd.DataFrame([{"response": io.RESPONSES[k], "predicted": v, "unit": io.UNITS[k]}
              for k, v in cand_pred.items()]).to_csv(RES / "candidate_predictions.csv", index=False)
rep33 = pd.read_csv(REP / "reported_T33_candidate_predictions.csv")
cm = {"Cobb60": "cobb60_g_m2", "WVTR": "wvtr_g_m2_day", "Grease-kit rating": "grease_kit",
      "Folding endurance": "fold_double_folds", "Compression": "compression_n",
      "OTR": "otr_cm3_m2_day", "Coating add-on": "coating_add_on_g_m2",
      "Drying energy": "drying_energy_kwh_kg"}
for _, r in rep33.iterrows():
    v = fnum(r["Predicted candidate"])
    check("Table 33", f"candidate {r['Response']}", cand_pred[cm[r["Response"]]], v,
          0.006 * max(1, abs(v) / 100) + 0.005)

# individual desirabilities at candidate and at thickness-only optimum (Fig. 26)
d_rows = []
for label, pr in (("Thickness-only optimum", cand_thick), ("Four-factor candidate", cand_pred)):
    D, ds = dz.overall({r: np.array([pr[r]]) for r in dz.OBJECTIVE})
    d_rows.append({"scenario": label, "D_overall": float(np.atleast_1d(D)[0]),
                   **{io.RESPONSES[r]: float(ds[i][0]) for i, r in enumerate(dz.OBJECTIVE)}})
pd.DataFrame(d_rows).to_csv(RES / "individual_desirabilities.csv", index=False)

# ============================================================ 4. confirmation settings (Table 34)
settings = {"C1 Four-factor candidate": cand_nat,
            "C2 FSM-capped alternative": None, "C3 Thickness-only baseline": np.array([a_opt, 3, 25, 50.]),
            "C4 Centre point": np.array([15, 3, 25, 50.])}
xcap, Dcap = op.run_de(op.make_objective(fits, fsm_cap=4.0), popsize=20)
settings["C2 FSM-capped alternative"] = rsm.decode(xcap)[0]
pi_rows = []
for nm, x in settings.items():
    xc_ = rsm.code(x[None, :])
    pr = {k: fits[k].prediction_interval(xc_) for k in fits}
    D, _ = dz.overall({r: pr[r][0] for r in dz.OBJECTIVE})
    row = {"setting": nm, "A_um": x[0], "B_pct": x[1], "C_pct": x[2], "D_C": x[3], "D_overall": float(np.atleast_1d(D)[0]),
           "leverage": float(pr["cobb60_g_m2"][3][0])}
    for k in fits:
        y, lo, hi, _ = pr[k]
        row[f"{io.RESPONSES[k]}_pred"] = float(y[0]); row[f"{io.RESPONSES[k]}_PI_low"] = float(lo[0])
        row[f"{io.RESPONSES[k]}_PI_high"] = float(hi[0])
    pi_rows.append(row)
pi = pd.DataFrame(pi_rows)
pi.to_csv(RES / "confirmation_runs_prediction_intervals.csv", index=False)
rep34 = pd.read_csv(REP / "reported_T34_confirmation_settings.csv")
for (_, a), (_, b) in zip(pi.iterrows(), rep34.iterrows()):
    check("Table 34", f"{a.setting[:2]} overall D", a.D_overall, fnum(b["D overall"]), 5e-5)
    for nm, key in (("Cobb60", "Cobb60"), ("WVTR", "WVTR"), ("Grease kit", "Grease kit"),
                    ("Folding", "Folding"), ("Compression", "Compress.")):
        s = re.findall(r"-?\d+\.?\d*", str(b[key]).replace("–", " "))
        pred, lo, hi = map(float, s[:3])
        tol = 0.06 if nm in ("Cobb60", "WVTR", "Folding", "Compression") else 0.006
        check("Table 34", f"{a.setting[:2]} {nm} prediction", a[f"{nm}_pred"], pred, tol)
        check("Table 34", f"{a.setting[:2]} {nm} PI low", a[f"{nm}_PI_low"], lo, tol)
        check("Table 34", f"{a.setting[:2]} {nm} PI high", a[f"{nm}_PI_high"], hi, tol)
check("Section 4.11", "candidate leverage", float(pi.leverage.iloc[0]), 0.44, 0.005)
Zall = rsm.design_matrix(rsm.code(runs[io.FACTORS].to_numpy(float)))
check("Section 4.11", "max design-point leverage", float(fits["cobb60_g_m2"].hat.max()), 0.66, 0.005)

# ============================================================ 5. sensitivity (Table 35)
scen = {
    "Baseline (source bounds, equal weights)": {},
    "Targets 10 % less demanding": dict(anchors=dz.scaled_anchors(.1, "less")),
    "Targets 10 % more demanding": dict(anchors=dz.scaled_anchors(.1, "more")),
    "Double weight Cobb60+WVTR": dict(weights={"cobb60_g_m2": 2, "wvtr_g_m2_day": 2}),
    "Double weight grease": dict(weights={"grease_kit": 2}),
    "Double weight fold+compression": dict(weights={"fold_double_folds": 2, "compression_n": 2}),
    "Barrier only (Cobb60, WVTR, grease)": dict(responses=["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit"]),
    "FSM solids capped at 4 %": dict(fsm_cap=4.0)}
sens = []
for nm, kw in scen.items():
    x, D = op.run_de(op.make_objective(fits, **kw), popsize=20)
    nat = rsm.decode(x)[0]; xcs = rsm.code(nat[None, :])
    pr = {k: float(fits[k].predict(xcs)[0]) for k in fits}
    sens.append({"scenario": nm, "A_um": nat[0], "B_pct": nat[1], "C_pct": nat[2], "D_C": nat[3],
                 "D_overall": D, "Cobb60": pr["cobb60_g_m2"], "WVTR": pr["wvtr_g_m2_day"],
                 "Grease": pr["grease_kit"], "Fold": pr["fold_double_folds"],
                 "Compression": pr["compression_n"]})
sens = pd.DataFrame(sens)
sens.to_csv(RES / "optimum_sensitivity.csv", index=False)
rep35 = pd.read_csv(REP / "reported_T35_sensitivity.csv")
for (_, a), (_, b) in zip(sens.iterrows(), rep35.iterrows()):
    check("Table 35", f"{a.scenario} D", a.D_overall, fnum(b["D overall"]), 5e-5)
    if "Barrier only" not in a.scenario:   # D = 1 plateau: location not unique
        for c, rc in (("A_um", "A (µm)"), ("B_pct", "B (%)"), ("C_pct", "C (%)"), ("D_C", "D (°C)")):
            check("Table 35", f"{a.scenario} {c}", a[c], fnum(b[rc]), 0.06)

# ============================================================ 6. package groups (Tables 19-20, 29)
pk = io.packages()
summ = gr.summary(pk); summ.to_csv(RES / "package_group_summary.csv", index=False)
cmp_ = gr.compare(pk); cmp_.to_csv(RES / "package_group_statistics.csv", index=False)
rep19 = pd.read_csv(REP / "reported_T19_package_summary.csv")
cols19 = gr.PKG_RESPONSES
for i, g in enumerate(gr.GROUPS):
    for j, c in enumerate(cols19):
        m_s, s_s = re.findall(r"-?\d+\.?\d*", rep19.iloc[i, j + 1])[:2]
        check("Table 19", f"{g} {io.RESPONSES.get(c, c)} mean", summ.loc[i, c + "_mean"], float(m_s), 0.006)
        check("Table 19", f"{g} {io.RESPONSES.get(c, c)} SD", summ.loc[i, c + "_sd"], float(s_s), 0.006)
rep20 = pd.read_csv(REP / "reported_T20_package_stats.csv")
for (_, a), (_, b) in zip(cmp_.iterrows(), rep20.iterrows()):
    n = io.RESPONSES[a.response]
    check("Table 20", f"{n} ANOVA F", a.anova_F, fnum(b.anova_F), 0.06)
    check("Table 20", f"{n} Δ%", a.delta_pct_vs_uncoated, fnum(b.delta_pct_vs_uncoated), 0.06)
    check("Table 20", f"{n} |g|", a.abs_hedges_g, fnum(b.abs_hedges_g), 0.06)
    check("Table 20", f"{n} GCI %", a.gci_pct, fnum(b.gci_pct), 0.6)
    check("Table 20", f"{n} Kruskal p", a.kruskal_p, fnum(b.kruskal_p), 6e-4)
    if "<" not in str(b.tukey_p_coated_vs_uncoated):
        check("Table 20", f"{n} Tukey coated-vs-uncoated p", a.tukey_p_coated_vs_uncoated, fnum(b.tukey_p_coated_vs_uncoated), 6e-4)
    if "<" not in str(b.tukey_p_coated_vs_cr):
        check("Table 20", f"{n} Tukey coated-vs-CR p", a.tukey_p_coated_vs_cr, fnum(b.tukey_p_coated_vs_cr), 6e-4)

mw, mo = summ.set_index("treatment"), None
sr_rows = []
for nm, c in (("WVTR", "wvtr_g_m2_day"), ("OTR", "otr_cm3_m2_day")):
    p = tr.series_partition(mw.loc["Uncoated PALF", c + "_mean"], mw.loc["FSM-coated PALF", c + "_mean"],
                            mw.loc["Commercial reference", c + "_mean"])
    sr_rows.append({"permeant": nm, **p})
sr = pd.DataFrame(sr_rows); sr.to_csv(RES / "series_resistance_partition.csv", index=False)
for _, r in sr.iterrows():
    exp = {"WVTR": (1.48, 868, 32.4), "OTR": (1.07, 24718, 6.4)}[r.permeant]
    check("Table 29", f"{r.permeant} BIF", r.BIF, exp[0], 0.006)
    check("Table 29", f"{r.permeant} coating-only rate", r.coating_only_rate, exp[1], 2.0)
    check("Table 29", f"{r.permeant} coating resistance share %", r.coating_share_pct, exp[2], 0.06)

# ============================================================ 7. storage (Tables 22-24)
srep, ssum = io.storage_replicates(), io.storage_summary()
kin = []
for col, label in (("mass_loss_pct", "Mass-loss rate (% day⁻¹)"), ("firmness_n", "Firmness-loss rate (N day⁻¹)")):
    s = st.slopes(srep, col); s.insert(0, "metric", label); kin.append(s)
pd.concat(kin).to_csv(RES / "storage_rates.csv", index=False)
for (col, lbl, exp) in (("mass_loss_pct", "mass loss", {"Uncoated PALF": 1.474, "FSM-coated PALF": 1.127, "Commercial reference": 1.002}),
                        ("firmness_n", "firmness", {"Uncoated PALF": -0.525, "FSM-coated PALF": -0.403, "Commercial reference": -0.395})):
    s = st.slopes(srep, col).set_index("treatment")
    for g, v in exp.items():
        check("Table 24", f"{g} {lbl} rate", s.loc[g, "slope"], v, 6e-4)
r2 = st.group_mean_r2(ssum, "mass_loss_pct")
check("Section 4.5", "min R² of mass loss vs time (group means)", min(r2.values()), 0.997, 0.003)
de = st.delta_e(ssum); de.to_csv(RES / "storage_delta_E.csv", index=False)
for g, v in {"Uncoated PALF": 9.1, "FSM-coated PALF": 5.2, "Commercial reference": 6.1}.items():
    check("Table 24", f"{g} ΔE*ab day 10", float(de[(de.treatment == g) & (de.day == 10)].delta_E_ab.iloc[0]), v, 0.06)
thr = {"Day mass loss reaches 5 %": ("mass_loss_pct", 5, True, (3.4, 4.5, 5.0)),
       "Day decay reaches 10 %": ("decay_incidence_pct", 10, True, (4.0, 6.3, 7.5)),
       "Day decay reaches 25 %": ("decay_incidence_pct", 25, True, (5.6, 8.3, 9.6)),
       "Day condition falls below 3": ("package_condition_1to5", 3, False, (5.9, 8.0, 9.2))}
trows = []
for lbl, (col, th, rising, exp) in thr.items():
    t = st.time_to(ssum, col, th, rising)
    trows.append({"metric": lbl, **t})
    for g, e in zip(gr.GROUPS, exp):
        check("Table 24", f"{lbl} / {g}", t[g], e, 0.06)
pd.DataFrame(trows).to_csv(RES / "storage_threshold_times.csv", index=False)
day10 = []
for col in ["mass_loss_pct", "firmness_n", "decay_incidence_pct", "package_condition_1to5",
            "headspace_o2_pct", "headspace_co2_pct"]:
    sub = srep[srep.day == 10]
    row = {"response": col}
    for g in gr.GROUPS:
        v = sub[sub.treatment == g][col]; row[g + "_mean"] = v.mean(); row[g + "_sd"] = v.std(ddof=1)
    row["anova_p"] = st.day_anova(srep, col); day10.append(row)
pd.DataFrame(day10).to_csv(RES / "storage_day10_stats.csv", index=False)
for row, (exp_p) in zip(day10, [None, None, None, None, 0.754, 0.178]):
    if exp_p:
        check("Table 24", f"{row['response']} ANOVA p", row["anova_p"], exp_p, 6e-4)
u, c = ssum[(ssum.day == 10) & (ssum.treatment == "Uncoated PALF")].iloc[0], ssum[(ssum.day == 10) & (ssum.treatment == "FSM-coated PALF")].iloc[0]
check("Section 4.5", "mass-loss reduction at day 10 (%)", 100 * (u.mass_loss_pct - c.mass_loss_pct) / u.mass_loss_pct, 24.0, 0.7)
check("Section 4.5.1", "decay reduction at day 10 (%)", 100 * (u.decay_incidence_pct - c.decay_incidence_pct) / u.decay_incidence_pct, 37.3, 0.06)

# ============================================================ 8. sheet indices, consistency audit
sh = io.load("02_paperboard_sheets")
idx = tr.sheet_indices(sh); idx.to_csv(RES / "sheet_indices.csv", index=False)
rep6 = pd.read_csv(REP / "reported_T06_sheet_indices.csv")
cols6 = ["porosity_pct", "tensile_index_md_nm_g", "tensile_index_cd_nm_g", "md_cd_ratio",
         "burst_index_kpa_m2_g", "tear_index_mn_m2_g"]
for i, c in enumerate(cols6):
    for j, sid in enumerate(["SHT-01", "SHT-02"]):
        tol = 0.06 if c in ("porosity_pct", "tensile_index_md_nm_g", "tensile_index_cd_nm_g") else 0.006
        check("Table 6", f"{c} {sid}", idx.loc[j, c], fnum(rep6.iloc[i, j + 1]), tol)

pulp, fsm = io.load("01_pulp_batches"), io.load("03_fsm_batches")
audit = []
audit.append(("Pulp yield B01 (%)", 100 * pulp.dry_pulp_mass_g[0] / pulp.initial_leaf_mass_g[0], pulp.pulp_yield_pct[0]))
audit.append(("Pulp yield B02 (%)", 100 * pulp.dry_pulp_mass_g[1] / pulp.initial_leaf_mass_g[1], pulp.pulp_yield_pct[1]))
for i in range(2):
    audit.append((f"Pulp composition sum B0{i+1} (%)", float(pulp.loc[i, ["cellulose_pct", "hemicellulose_pct", "lignin_pct", "ash_pct", "extractives_pct"]].sum()), 100.0))
for i in range(2):
    audit.append((f"FSM extraction yield B0{i+1} (%)", 100 * fsm.dry_solids_g[i] / fsm.seed_mass_g[i], fsm.extraction_yield_pct[i]))
    audit.append((f"FSM total solids B0{i+1} (%)", 100 * fsm.dry_solids_g[i] / fsm.wet_mucilage_g[i], fsm.total_solids_pct[i]))
spec = io.load("12_coating_specimens")
for _, r in spec.dropna(subset=["dry_thickness_um"]).query("dry_thickness_um > 0").iterrows():
    audit.append((f"Implied coating density {r.specimen_id} (g cm⁻³)", r.add_on_g_m2 / r.dry_thickness_um, np.nan))
audit.append(("Apparent density SHT-01 (g cm⁻³)", sh.grammage_g_m2[0] / sh.caliper_um[0], sh.apparent_density_g_cm3[0]))
audit.append(("Apparent density SHT-02 (g cm⁻³)", sh.grammage_g_m2[1] / sh.caliper_um[1], sh.apparent_density_g_cm3[1]))
rm_c = runs[runs.point_type == "centre"]
audit.append(("RSM centre-run implied coating density (g cm⁻³)", float((rm_c.coating_add_on_g_m2 / 15).mean()), np.nan))
audit_df = pd.DataFrame(audit, columns=["item", "recalculated", "reported"])
audit_df["difference"] = audit_df.recalculated - audit_df.reported
audit_df.to_csv(RES / "consistency_audit.csv", index=False)

# ---- Table-40 style cross-dataset comparison (computed)
doe = io.load("13_coating_doe_runs")
pkc = pk[pk.treatment == "FSM-coated PALF"]
xd = pd.DataFrame([
    ["Add-on at ~15 µm (g m⁻²)", f"{rm_c.coating_add_on_g_m2.min():.2f}–{rm_c.coating_add_on_g_m2.max():.2f}", f"{doe[doe.target_thickness_um==15].add_on_g_m2.min():.1f}–{doe[doe.target_thickness_um==15].add_on_g_m2.max():.1f}", "—"],
    ["Cobb60 at ~15 µm (g m⁻²)", f"{rm_c.cobb60_g_m2.min():.1f}–{rm_c.cobb60_g_m2.max():.1f}", f"{doe[doe.target_thickness_um==15].cobb60_g_m2.min():.0f}–{doe[doe.target_thickness_um==15].cobb60_g_m2.max():.0f}", f"{pkc.cobb60_g_m2.mean():.1f} (coated)"],
    ["WVTR at ~15 µm (g m⁻² day⁻¹)", f"{rm_c.wvtr_g_m2_day.min():.1f}–{rm_c.wvtr_g_m2_day.max():.1f}", f"{doe[doe.target_thickness_um==15].wvtr_g_m2_day.min():.0f}–{doe[doe.target_thickness_um==15].wvtr_g_m2_day.max():.0f}", f"{pkc.wvtr_g_m2_day.mean():.1f} (coated)"],
    ["Tensile MD (kN m⁻¹)", f"{runs.tensile_md_kn_m.min():.1f}–{runs.tensile_md_kn_m.max():.1f}", f"{sh.tensile_md_n_m.min()/1000:.2f}–{sh.tensile_md_n_m.max()/1000:.2f}", f"{pk.tensile_md_kn_m.min():.1f}–{pk.tensile_md_kn_m.max():.1f}"]],
    columns=["quantity", "30-run RSM (run means)", "Coating DOE / specimens", "Package groups"])
xd.to_csv(RES / "cross_dataset_comparison.csv", index=False)
check("Section 4.12", "implied RSM coating density (g cm⁻³)", float((rm_c.coating_add_on_g_m2 / 15).mean()), 0.11, 0.006)

# ============================================================ 9. coating DOE (Section 4.7)
tcol = doe.actual_thickness_um
r_ct, p_ct = stats.pearsonr(tcol, doe.cobb60_g_m2)
r_at, _ = stats.pearsonr(tcol, doe.add_on_g_m2)
check("Section 4.7", "r(Cobb60, thickness), n=10", r_ct, -0.80, 0.006)
check("Section 4.7", "p for r(Cobb60, thickness)", p_ct, 0.005, 6e-4)
check("Section 4.7", "r(add-on, thickness)", r_at, 0.999, 6e-4)
dens = doe.add_on_g_m2 / doe.actual_thickness_um
check("Section 4.7", "min apparent coating density (g cm⁻³)", float(dens.min()), 0.89, 0.006)
check("Section 4.7", "max apparent coating density (g cm⁻³)", float(dens.max()), 0.98, 0.006)


def ols(y, cols):
    X = np.column_stack([np.ones(len(y))] + [doe[c].to_numpy(float) for c in cols])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b; dfr = len(y) - X.shape[1]
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * (res @ res) / dfr)
    p = 2 * stats.t.sf(np.abs(b / se), dfr)
    r2 = 1 - (res @ res) / ((y - y.mean()) @ (y - y.mean()))
    return b, p, r2


bc, pc, r2c = ols(doe.cobb60_g_m2.to_numpy(float), ["actual_thickness_um", "fsm_solids_pct"])
bw, pw, r2w = ols(doe.wvtr_g_m2_day.to_numpy(float), ["actual_thickness_um", "fsm_solids_pct"])
pd.DataFrame([
    ["Cobb60", "thickness", bc[1], pc[1], r2c], ["Cobb60", "FSM solids", bc[2], pc[2], r2c],
    ["WVTR", "thickness", bw[1], pw[1], r2w], ["WVTR", "FSM solids", bw[2], pw[2], r2w]],
    columns=["response", "term", "slope", "p", "R2"]).to_csv(RES / "coating_doe_two_variable_models.csv", index=False)
check("Section 4.7", "Cobb60 slope per µm", bc[1], -1.42, 0.006); check("Section 4.7", "Cobb60 p thickness", pc[1], 0.002, 6e-4)
check("Section 4.7", "Cobb60 slope per % FSM", bc[2], -3.51, 0.006); check("Section 4.7", "Cobb60 p FSM", pc[2], 0.035, 6e-4)
check("Section 4.7", "Cobb60 R²", r2c, 0.82, 0.006)
check("Section 4.7", "WVTR slope per µm", bw[1], -3.01, 0.006); check("Section 4.7", "WVTR p thickness", pw[1], 0.027, 6e-4)
check("Section 4.7", "WVTR p FSM", pw[2], 0.073, 6e-4); check("Section 4.7", "WVTR R²", r2w, 0.64, 0.006)

# ============================================================ 10. correlations (Fig. 14)
corr = runs[list(io.RESPONSES)].rename(columns=io.RESPONSES).corr()
corr.to_csv(RES / "response_correlation_matrix.csv")
cc = runs[list(io.RESPONSES)].corr()
check("Fig. 14", "r(Grease, add-on)", cc.loc["grease_kit", "coating_add_on_g_m2"], 0.90, 0.006)
check("Fig. 14", "r(burst, folding)", cc.loc["burst_kpa", "fold_double_folds"], 0.84, 0.006)
check("Fig. 14", "r(tensile, compression)", cc.loc["tensile_md_kn_m", "compression_n"], 0.79, 0.006)
check("Fig. 14", "r(WVTR, folding)", cc.loc["wvtr_g_m2_day", "fold_double_folds"], 0.55, 0.006)

# ============================================================ 11. replicate-level variability
rp = io.replicates()
var = []
for k in io.RESPONSES:
    g = rp.groupby("run")[k]
    var.append({"response": io.RESPONSES[k], "mean_within_run_SD": g.std(ddof=1).mean(),
                "pooled_within_run_CV_pct": 100 * np.sqrt((g.var(ddof=1)).mean()) / rp[k].mean()})
pd.DataFrame(var).to_csv(RES / "within_run_replicate_variability.csv", index=False)

# ============================================================ report
rep_df = pd.DataFrame(CHECKS)
rep_df.to_csv(RES / "reproducibility_report.csv", index=False)
n_ok = (rep_df.status == "REPRODUCED").sum()
print(f"Reproducibility checks: {n_ok}/{len(rep_df)} reproduced within rounding tolerance")
bad = rep_df[rep_df.status != "REPRODUCED"]
if len(bad):
    print(bad.to_string())
