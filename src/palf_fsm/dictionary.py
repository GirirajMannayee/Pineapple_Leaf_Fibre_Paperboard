"""Data dictionary: one entry per column name used in data/raw/*.csv."""
M = "Measured (author-confirmed laboratory record)"
D = "Design variable (set by experimenter)"
C = "Derived (calculated from measurements)"
I = "Identifier / label"

# column -> (unit, description, provenance)
COLUMNS = {
 # identifiers ---------------------------------------------------------------
 "pulp_batch_id": ("-", "PALF pulp batch identifier (PALF-B01, PALF-B02)", I),
 "sheet_id": ("-", "Hand-sheet / paperboard sheet identifier (SHT-01, SHT-02)", I),
 "fsm_batch_id": ("-", "Fenugreek seed mucilage extraction batch identifier", I),
 "turmeric_form": ("-", "Turmeric ingredient form (powder or extract)", I),
 "code": ("-", "Formulation code: U0 uncoated, F1 FSM only, FT05/FT10 FSM + 0.5/1.0 % turmeric, T1 turmeric only", I),
 "group": ("-", "Treatment group of the formulation / specimen", I),
 "factor": ("-", "RSM factor name", I),
 "symbol": ("-", "RSM factor symbol (A-D)", I),
 "run": ("-", "Design run number (1-30) of the face-centred central composite design", I),
 "run_id": ("-", "Coating-DOE run identifier (R01-R10)", I),
 "specimen_id": ("-", "Coated-specimen identifier (SP-U0, SP-FT05, SP-FT10)", I),
 "pulp_batch": ("-", "PALF pulp batch used for the specimen", I),
 "point_type": ("-", "CCF point type: factorial (16), axial (8) or centre (6)", I),
 "replicate": ("-", "Within-run (RSM) or within-group (package) replicate number", I),
 "package_replicate": ("-", "Package replicate number (1-3) followed over the storage trial", I),
 "treatment": ("-", "Package group: Uncoated PALF, FSM-coated PALF, Commercial reference", I),
 "day": ("day", "Storage day (0, 2, 4, 6, 8, 10)", D),
 "grease_method": ("-", "Grease-resistance method (kit test)", I),
 # pulp -------------------------------------------------------------------------
 "initial_leaf_mass_g": ("g", "Initial pineapple-leaf mass fed to pulping", M),
 "dry_pulp_mass_g": ("g", "Oven-dry pulp mass", M),
 "pulp_yield_pct": ("%", "Dry pulp yield = dry pulp / initial leaf mass x 100 (Eq. 3)", M),
 "moisture_pct": ("%", "Moisture content", M),
 "ash_pct": ("%", "Ash content", M),
 "extractives_pct": ("%", "Extractives content", M),
 "cellulose_pct": ("%", "Cellulose content", M),
 "hemicellulose_pct": ("%", "Hemicellulose content", M),
 "lignin_pct": ("%", "Lignin content", M),
 "fibre_length_mm": ("mm", "Mean fibre length", M),
 "csf_ml": ("mL", "Canadian standard freeness (drainage)", M),
 # sheets ---------------------------------------------------------------------
 "nominal_grammage_g_m2": ("g m-2", "Target grammage of the sheet (250 g m-2, from text)", D),
 "grammage_g_m2": ("g m-2", "Measured grammage", M),
 "caliper_um": ("um", "Measured caliper (thickness)", M),
 "apparent_density_g_cm3": ("g cm-3", "Apparent density = grammage / caliper (Eq. 1)", M),
 "tensile_md_n_m": ("N m-1", "Tensile strength, machine direction (sheet/specimen records)", M),
 "tensile_cd_n_m": ("N m-1", "Tensile strength, cross direction", M),
 "burst_kpa": ("kPa", "Burst strength", M),
 "tear_mn": ("mN", "Tear resistance", M),
 "folding_double_folds": ("double folds", "Folding endurance", M),
 # FSM --------------------------------------------------------------------------
 "seed_mass_g": ("g", "Fenugreek seed mass", M), "hydration_water_ml": ("mL", "Hydration water volume", M),
 "hydration_temp_c": ("degC", "Hydration temperature", M), "hydration_time_min": ("min", "Hydration time", M),
 "extraction_temp_c": ("degC", "Extraction temperature", M), "extraction_time_min": ("min", "Extraction time", M),
 "wet_mucilage_g": ("g", "Wet mucilage mass recovered", M), "dry_solids_g": ("g", "Dry mucilage solids mass", M),
 "extraction_yield_pct": ("%", "FSM extraction yield (dry solids / seed mass)", M),
 "total_solids_pct": ("%", "Total solids of the extract or coating formulation", M),
 "ph": ("-", "pH", M), "viscosity_mpa_s": ("mPa s", "Dynamic viscosity (conditions not stated in source)", M),
 # turmeric -----------------------------------------------------------------------
 "initial_mass_g": ("g", "Initial turmeric mass", M), "solvent_volume_ml": ("mL", "Solvent volume", M),
 "dry_solids_pct": ("%", "Dry solids of the turmeric preparation", M),
 "particle_size_um": ("um", "Turmeric particle size (blank = not recorded)", M),
 "curcumin_pct": ("%", "Curcumin content (blank = not measured)", M),
 # formulations ------------------------------------------------------------------------
 "fsm_solids_pct": ("% w/w", "FSM solids in the coating solution (RSM factor B)", D),
 "turmeric_pct_dry_fsm": ("% of dry FSM", "Turmeric loading relative to dry FSM", D),
 "glycerol_pct_dry_polymer": ("% of dry polymer", "Glycerol relative to dry polymer", D),
 "water_g": ("g", "Water in 100 g formulation", D), "fsm_g": ("g", "FSM in 100 g formulation", D),
 "turmeric_g": ("g", "Turmeric in 100 g formulation", D), "glycerol_g": ("g", "Glycerol in 100 g formulation", D),
 "mixing_rpm": ("rpm", "Mixing speed", D), "mixing_time_min": ("min", "Mixing time", D),
 # factors --------------------------------------------------------------------------------
 "low": ("per unit", "Low level (coded -1)", D), "centre": ("per unit", "Centre level (coded 0)", D),
 "high": ("per unit", "High level (coded +1)", D), "unit": ("-", "Unit of the factor", I),
 "A_thickness_um": ("um", "Factor A: dry coating thickness (5-25)", D),
 "B_fsm_solids_pct": ("% w/w", "Factor B: FSM solids (1-5)", D),
 "C_glycerol_pct_dry_fsm": ("% dry FSM", "Factor C: glycerol relative to dry FSM (15-35)", D),
 "D_drying_temp_c": ("degC", "Factor D: drying temperature (40-60)", D),
 # responses -----------------------------------------------------------------------------------
 "cobb60_g_m2": ("g m-2", "Cobb60 water absorptiveness, 60 s (Eq. 10); lower = better", M),
 "wvtr_g_m2_day": ("g m-2 day-1", "Water-vapour transmission rate (test conditions not stated); lower = better", M),
 "otr_cm3_m2_day": ("cm3 m-2 day-1", "Oxygen transmission rate (test conditions not stated)", M),
 "grease_kit": ("kit rating", "Grease-resistance kit rating (ordinal; higher = better)", M),
 "tensile_md_kn_m": ("kN m-1", "Tensile strength, machine direction (RSM/package datasets; ~8x larger than sheet records)", M),
 "burst_kpa_": ("kPa", "", M),
 "fold_double_folds": ("double folds", "Folding endurance", M),
 "compression_n": ("N", "Package compression (peak force)", M),
 "coating_add_on_g_m2": ("g m-2", "Dry coating add-on (RSM workbook; implies density ~0.11 g cm-3)", M),
 "drying_energy_kwh_kg": ("kWh kg-1", "Drying energy", M),
 # package ----------------------------------------------------------------------------------------
 "coating_thickness_um": ("um", "Nominal dry coating thickness of the package group (15 um coated; 0 uncoated; blank for reference)", D),
 # storage ---------------------------------------------------------------------------------------------
 "mass_loss_pct": ("%", "Package mass loss during refrigerated storage", M),
 "firmness_n": ("N", "Product firmness", M),
 "L_star": ("-", "CIE L* lightness", M), "a_star": ("-", "CIE a*", M), "b_star": ("-", "CIE b*", M),
 "decay_incidence_pct": ("%", "Visible decay incidence (NOT a microbial count)", M),
 "headspace_o2_pct": ("%", "Headspace oxygen", M), "headspace_co2_pct": ("%", "Headspace carbon dioxide", M),
 "package_condition_1to5": ("score 1-5", "Package condition score (5 = best)", M),
 # specimens -----------------------------------------------------------------------------------------------
 "grease_rating_ordinal": ("kit rating", "Specimen grease-kit rating (ordinal)", M),
 "wet_tensile_n_m": ("N m-1", "Wet tensile strength", M), "wet_burst_kpa": ("kPa", "Wet burst strength", M),
 "density_g_cm3": ("g cm-3", "Specimen apparent density", M), "add_on_g_m2": ("g m-2", "Gravimetric dry add-on (Eq. 7)", M),
 "dry_thickness_um": ("um", "Dry coating thickness (nominal / mean)", M),
 "thickness_mean_sd_um": ("um", "Mean +/- SD of the three thickness positions (text as printed)", C),
 "coverage_pct": ("%", "Coating coverage", M), "pinholes_count": ("count", "Pinholes counted", M),
 "roughness_um": ("um", "Surface roughness", M), "contact_angle_deg": ("deg", "Static water contact angle", M),
 "thickness_p1_um": ("um", "Thickness at position 1", M), "thickness_p2_um": ("um", "Thickness at position 2", M),
 "thickness_p3_um": ("um", "Thickness at position 3", M),
 # DOE ------------------------------------------------------------------------------------------------------------
 "target_thickness_um": ("um", "Target dry thickness", D), "actual_thickness_um": ("um", "Measured dry thickness", M),
 "glycerol_pct_dry_fsm": ("% dry FSM", "Glycerol relative to dry FSM", D), "drying_temp_c": ("degC", "Drying temperature", D),
 "tensile_n_m": ("N m-1", "Tensile strength of the DOE specimen", M), "wet_strength_n_m": ("N m-1", "Wet strength", M),
 "crease_score": ("score", "Crease-cracking score (higher = worse)", M),
 "delamination_score": ("score", "Delamination score (higher = worse)", M),
}
COLUMNS["burst_kpa"] = ("kPa", "Burst strength", M)
del COLUMNS["burst_kpa_"]
