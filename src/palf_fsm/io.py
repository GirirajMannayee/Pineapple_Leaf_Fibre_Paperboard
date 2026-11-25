"""Data loading helpers (all paths relative to the repository root)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
REPORTED = ROOT / "data" / "reported"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures" / "generated"

FACTORS = ["A_thickness_um", "B_fsm_solids_pct", "C_glycerol_pct_dry_fsm", "D_drying_temp_c"]
FACTOR_LABELS = {"A": "Thickness (µm)", "B": "FSM solids (%)",
                 "C": "Glycerol (% dry FSM)", "D": "Drying temp. (°C)"}
LOW = dict(A=5.0, B=1.0, C=15.0, D=40.0)
CENTRE = dict(A=15.0, B=3.0, C=25.0, D=50.0)
HIGH = dict(A=25.0, B=5.0, C=35.0, D=60.0)
STEP = {k: (HIGH[k] - LOW[k]) / 2 for k in LOW}

RESPONSES = {  # column -> pretty label
    "cobb60_g_m2": "Cobb60", "wvtr_g_m2_day": "WVTR", "otr_cm3_m2_day": "OTR",
    "grease_kit": "Grease kit", "tensile_md_kn_m": "Tensile MD", "burst_kpa": "Burst",
    "fold_double_folds": "Folding", "compression_n": "Compression",
    "coating_add_on_g_m2": "Coating add-on", "drying_energy_kwh_kg": "Drying energy"}
UNITS = {"cobb60_g_m2": "g m⁻²", "wvtr_g_m2_day": "g m⁻² day⁻¹", "otr_cm3_m2_day": "cm³ m⁻² day⁻¹",
         "grease_kit": "kit rating", "tensile_md_kn_m": "kN m⁻¹", "burst_kpa": "kPa",
         "fold_double_folds": "double folds", "compression_n": "N",
         "coating_add_on_g_m2": "g m⁻²", "drying_energy_kwh_kg": "kWh kg⁻¹"}


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / f"{name}.csv")


def run_means() -> pd.DataFrame:
    return load("07_rsm_run_means")


def replicates() -> pd.DataFrame:
    return load("08_rsm_replicates")


def packages() -> pd.DataFrame:
    return load("09_package_replicates")


def storage_summary() -> pd.DataFrame:
    return load("10_storage_summary")


def storage_replicates() -> pd.DataFrame:
    return load("11_storage_replicates")
