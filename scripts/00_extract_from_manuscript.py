#!/usr/bin/env python3
"""
00_extract_from_manuscript.py
=============================
Provenance script: transcribes every table (and every embedded figure) of the
manuscript "Pineapple Leaf Fibre Paperboard with Fenugreek Mucilage-Turmeric
Biocoatings for Improved Barrier Performance and Optimisation" into
machine-readable files.

Outputs
-------
data/manuscript_tables/Table_XX.csv   verbatim transcription of all 46 tables
data/raw/*.csv                        tidy, analysis-ready measurement datasets
data/reported/*.csv                   statistics REPORTED in the paper (used to
                                      verify the re-analysis in step 02)
figures/manuscript_original/*         the original manuscript figures

Usage:  python scripts/00_extract_from_manuscript.py path/to/manuscript.docx
"""
import re
import sys
from pathlib import Path

import docx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, MAN, REP = ROOT / "data/raw", ROOT / "data/manuscript_tables", ROOT / "data/reported"
FIGDIR = ROOT / "figures/manuscript_original"


def clean(s):
    s = s.replace("\u2212", "-").replace("\xa0", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def num(s):
    s = clean(str(s)).replace("*", "").replace(",", "")
    if s in {"", "—", "-", "N/A", "n/a", "Not recorded", "Not measured", "— / — / —"}:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def df_of(rows):
    return pd.DataFrame(rows[1:], columns=rows[0])


def numeric(df, skip=()):
    for c in df.columns:
        if c not in skip:
            df[c] = df[c].map(num)
    return df


def transposed(rows, mapping):
    """Parameters-in-rows table -> one row per sample/batch."""
    ids = rows[0][1:-1]
    recs = []
    for j, sid in enumerate(ids, start=1):
        rec = {"sample_id": sid}
        for r in rows[1:]:
            key = mapping.get(r[0])
            if key:
                rec[key] = num(r[j])
        recs.append(rec)
    return pd.DataFrame(recs)


def main(docx_path):
    for p in (MAN, RAW, REP, FIGDIR):
        p.mkdir(parents=True, exist_ok=True)
    doc = docx.Document(docx_path)
    T = [[[clean(c.text) for c in r.cells] for r in t.rows] for t in doc.tables]
    assert len(T) == 46, f"expected 46 tables, found {len(T)}"

    # 1. verbatim copies -----------------------------------------------------
    for i, rows in enumerate(T, start=1):
        w = max(len(r) for r in rows)
        rows = [r + [""] * (w - len(r)) for r in rows]
        pd.DataFrame(rows[1:], columns=rows[0]).to_csv(
            MAN / f"Table_{i:02d}.csv", index=False, encoding="utf-8-sig")

    # 2. tidy raw datasets -----------------------------------------------------
    pulp = transposed(T[3], {
        "Initial leaf mass": "initial_leaf_mass_g", "Dry pulp mass": "dry_pulp_mass_g",
        "Pulp yield": "pulp_yield_pct", "Moisture": "moisture_pct", "Ash": "ash_pct",
        "Extractives": "extractives_pct", "Cellulose": "cellulose_pct",
        "Hemicellulose": "hemicellulose_pct", "Lignin": "lignin_pct",
        "Fibre length": "fibre_length_mm", "Drainage / CSF": "csf_ml"})
    pulp.rename(columns={"sample_id": "pulp_batch_id"}).to_csv(RAW / "01_pulp_batches.csv", index=False)

    sheets = transposed(T[4], {
        "Measured grammage": "grammage_g_m2", "Caliper": "caliper_um",
        "Apparent density": "apparent_density_g_cm3", "Moisture": "moisture_pct",
        "Tensile MD": "tensile_md_n_m", "Tensile CD": "tensile_cd_n_m", "Burst": "burst_kpa",
        "Tear": "tear_mn", "Folding endurance": "folding_double_folds"})
    sheets = sheets.rename(columns={"sample_id": "sheet_id"})
    sheets.insert(1, "nominal_grammage_g_m2", 250.0)
    sheets.to_csv(RAW / "02_paperboard_sheets.csv", index=False)

    fsm = transposed(T[6], {
        "Seed mass": "seed_mass_g", "Hydration water": "hydration_water_ml",
        "Hydration temperature": "hydration_temp_c", "Hydration time": "hydration_time_min",
        "Extraction temperature": "extraction_temp_c", "Extraction time": "extraction_time_min",
        "Wet mucilage mass": "wet_mucilage_g", "Dry solids mass": "dry_solids_g",
        "Extraction yield": "extraction_yield_pct", "Total solids": "total_solids_pct",
        "pH": "ph", "Viscosity": "viscosity_mpa_s", "Ash": "ash_pct"})
    fsm.rename(columns={"sample_id": "fsm_batch_id"}).to_csv(RAW / "03_fsm_batches.csv", index=False)

    tur = transposed(T[7], {
        "Initial mass": "initial_mass_g", "Solvent volume": "solvent_volume_ml",
        "Extraction temperature": "extraction_temp_c", "Extraction time": "extraction_time_min",
        "Dry solids": "dry_solids_pct", "Particle size": "particle_size_um",
        "Curcumin": "curcumin_pct", "pH": "ph"})
    tur["sample_id"] = ["Turmeric powder", "Turmeric extract"]
    tur.rename(columns={"sample_id": "turmeric_form"}).to_csv(
        RAW / "04_turmeric_preparations.csv", index=False)

    f = df_of(T[8])
    f.columns = ["code", "group", "fsm_solids_pct", "turmeric_pct_dry_fsm",
                 "glycerol_pct_dry_polymer", "total_solids_pct", "water_g", "fsm_g",
                 "turmeric_g", "glycerol_g", "mixing_rpm", "mixing_time_min", "ph",
                 "viscosity_mpa_s"]
    numeric(f, skip=("code", "group")).to_csv(RAW / "05_coating_formulations.csv", index=False)

    fa = df_of(T[10])
    fa.columns = ["factor", "symbol", "low", "centre", "high", "unit"]
    numeric(fa, skip=("factor", "symbol", "unit")).to_csv(RAW / "06_rsm_factors.csv", index=False)

    mech = df_of(T[13])
    mech.columns = ["run", "tensile_md_kn_m", "burst_kpa", "fold_double_folds",
                    "compression_n", "coating_add_on_g_m2", "drying_energy_kwh_kg"]
    bar = df_of(T[14])
    bar.columns = ["run", "A_thickness_um", "B_fsm_solids_pct", "C_glycerol_pct_dry_fsm",
                   "D_drying_temp_c", "cobb60_g_m2", "wvtr_g_m2_day", "otr_cm3_m2_day",
                   "grease_kit"]
    run = numeric(bar).merge(numeric(mech), on="run")
    centre, axial = {5, 7, 9, 11, 12, 16}, {13, 14, 15, 19, 20, 24, 29, 30}
    run.insert(1, "point_type", ["centre" if r in centre else "axial" if r in axial
                                 else "factorial" for r in run["run"]])
    run["run"] = run["run"].astype(int)
    run.to_csv(RAW / "07_rsm_run_means.csv", index=False)

    r1 = numeric(df_of(T[35]))
    r1.columns = ["run", "replicate", "A_thickness_um", "B_fsm_solids_pct",
                  "C_glycerol_pct_dry_fsm", "D_drying_temp_c", "cobb60_g_m2",
                  "wvtr_g_m2_day", "otr_cm3_m2_day", "grease_kit"]
    r2 = numeric(df_of(T[36]))
    r2.columns = ["run", "replicate", "tensile_md_kn_m", "burst_kpa", "fold_double_folds",
                  "compression_n", "coating_add_on_g_m2", "drying_energy_kwh_kg"]
    rep = r1.merge(r2, on=["run", "replicate"])
    rep[["run", "replicate"]] = rep[["run", "replicate"]].astype(int)
    rep.to_csv(RAW / "08_rsm_replicates.csv", index=False)

    p = df_of(T[20])
    p.columns = ["treatment", "replicate", "coating_thickness_um", "cobb60_g_m2",
                 "wvtr_g_m2_day", "otr_cm3_m2_day", "grease_kit", "tensile_md_kn_m",
                 "burst_kpa", "fold_double_folds", "compression_n"]
    p = numeric(p, skip=("treatment",))
    p["replicate"] = p["replicate"].astype(int)
    p.to_csv(RAW / "09_package_replicates.csv", index=False)

    s = df_of(T[30])
    s.columns = ["day", "treatment", "mass_loss_pct", "firmness_n", "L_star", "a_star",
                 "b_star", "decay_incidence_pct", "headspace_o2_pct", "headspace_co2_pct",
                 "package_condition_1to5"]
    s = numeric(s, skip=("treatment",))
    s["day"] = s["day"].astype(int)
    s.to_csv(RAW / "10_storage_summary.csv", index=False)

    sr = df_of(T[37])
    sr.columns = ["day", "treatment", "package_replicate", "mass_loss_pct", "firmness_n",
                  "L_star", "a_star", "b_star", "decay_incidence_pct", "headspace_o2_pct",
                  "headspace_co2_pct", "package_condition_1to5"]
    sr = numeric(sr, skip=("treatment",))
    sr[["day", "package_replicate"]] = sr[["day", "package_replicate"]].astype(int)
    sr.to_csv(RAW / "11_storage_replicates.csv", index=False)

    t25 = df_of(T[24])
    t25.columns = ["specimen_id", "run_id", "pulp_batch", "treatment", "grease_method",
                   "grease_rating_ordinal", "tensile_md_n_m", "tensile_cd_n_m", "burst_kpa",
                   "tear_mn", "fold_double_folds", "wet_tensile_n_m", "wet_burst_kpa"]
    t26 = df_of(T[25])
    t26.columns = ["specimen_id", "run_id", "pulp_batch", "group", "grammage_g_m2",
                   "caliper_um", "density_g_cm3", "moisture_pct", "add_on_g_m2",
                   "dry_thickness_um", "thickness_p1_p2_p3_um", "thickness_mean_sd_um",
                   "coverage_pct", "pinholes_count", "roughness_um", "contact_angle_deg",
                   "cobb60_g_m2", "wvtr_g_m2_day", "otr_cm3_m2_day"]
    spec = t25.merge(t26.drop(columns=["run_id", "pulp_batch"]), on="specimen_id")
    text_cols = {"specimen_id", "run_id", "pulp_batch", "treatment", "grease_method", "group",
                 "thickness_p1_p2_p3_um", "thickness_mean_sd_um"}
    for c in spec.columns:
        if c not in text_cols:
            spec[c] = spec[c].map(num)
    pos = spec["thickness_p1_p2_p3_um"].str.split("/", expand=True)
    for k in range(3):
        spec[f"thickness_p{k+1}_um"] = pos[k].map(num)
    spec.drop(columns=["thickness_p1_p2_p3_um"]).to_csv(RAW / "12_coating_specimens.csv", index=False)

    d1 = df_of(T[26])
    d1.columns = ["run_id", "tensile_n_m", "burst_kpa", "fold_double_folds", "wet_strength_n_m",
                  "crease_score", "delamination_score", "compression_n", "drying_energy_kwh_kg"]
    d2 = df_of(T[27])
    d2.columns = ["run_id", "group", "target_thickness_um", "fsm_solids_pct",
                  "turmeric_pct_dry_fsm", "glycerol_pct_dry_fsm", "drying_temp_c",
                  "actual_thickness_um", "add_on_g_m2", "cobb60_g_m2", "wvtr_g_m2_day",
                  "otr_cm3_m2_day", "grease_kit"]
    numeric(d2, skip=("run_id", "group")).merge(
        numeric(d1, skip=("run_id",)), on="run_id").to_csv(RAW / "13_coating_doe_runs.csv", index=False)

    # 3. statistics reported in the paper -----------------------------------------
    def save_rep(idx, name, cols=None):
        df = df_of(T[idx])
        if cols:
            df.columns = cols
        df.to_csv(REP / name, index=False, encoding="utf-8-sig")

    save_rep(12, "reported_T13_model_fit.csv", ["response", "r2", "rmse"])
    save_rep(15, "reported_T16_model_adequacy.csv",
             ["response", "r2", "adj_r2", "pred_r2", "F", "p_model", "lof_p", "cv_pct",
              "adeq_prec", "shapiro_p"])
    save_rep(16, "reported_T17_coded_coefficients.csv",
             ["term", "Cobb60", "WVTR", "Grease_kit", "Folding", "Compression"])
    save_rep(18, "reported_T19_package_summary.csv")
    save_rep(19, "reported_T20_package_stats.csv",
             ["response", "anova_F", "anova_p", "tukey_p_coated_vs_uncoated",
              "tukey_p_coated_vs_cr", "delta_pct_vs_uncoated", "abs_hedges_g", "gci_pct",
              "kruskal_p"])
    save_rep(17, "reported_T18_thickness_optimum.csv")
    save_rep(21, "reported_T22_day10_summary.csv")
    save_rep(23, "reported_T24_storage_kinetics.csv")
    save_rep(28, "reported_T29_series_resistance.csv")
    save_rep(31, "reported_T32_optimiser_comparison.csv")
    save_rep(32, "reported_T33_candidate_predictions.csv")
    save_rep(33, "reported_T34_confirmation_settings.csv")
    save_rep(34, "reported_T35_sensitivity.csv")
    save_rep(5, "reported_T06_sheet_indices.csv")

    # 4. original figures (document order == figure number) -----------------------
    n = 0
    for shp in doc.inline_shapes:
        rid = shp._inline.graphic.graphicData.pic.blipFill.blip.embed
        part = doc.part.related_parts[rid]
        n += 1
        (FIGDIR / f"Manuscript_Figure_{n:02d}{Path(part.partname).suffix}").write_bytes(part.blob)
    print("tables:", len(T), "| figures:", n)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else
         "/mnt/user-data/uploads/1_Pineapple_Leaf_Fibre_Paperboard.docx")
