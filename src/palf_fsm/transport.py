"""Series-resistance partition (Eqs. 9, 16) and sheet indices (Eqs. 1-2, 17)."""
import numpy as np
import pandas as pd


def series_partition(uncoated: float, coated: float, reference: float, coverage=(0.96, 0.98)):
    bif = uncoated / coated
    coat_only = 1.0 / (1.0 / coated - 1.0 / uncoated)
    share = 100 * (1 - coated / uncoated)
    ceil = tuple(1 / (1 - c) for c in coverage)
    return {"uncoated": uncoated, "coated": coated, "reference": reference, "BIF": bif,
            "coating_only_rate": coat_only, "coating_share_pct": share,
            "defect_ceiling_low": ceil[0], "defect_ceiling_high": ceil[1]}


def sheet_indices(sheets: pd.DataFrame, rho_cell=1.5) -> pd.DataFrame:
    d = pd.DataFrame({"sheet_id": sheets.sheet_id})
    d["porosity_pct"] = 100 * (1 - sheets.apparent_density_g_cm3 / rho_cell)
    d["tensile_index_md_nm_g"] = sheets.tensile_md_n_m / sheets.grammage_g_m2
    d["tensile_index_cd_nm_g"] = sheets.tensile_cd_n_m / sheets.grammage_g_m2
    d["md_cd_ratio"] = sheets.tensile_md_n_m / sheets.tensile_cd_n_m
    d["burst_index_kpa_m2_g"] = sheets.burst_kpa / sheets.grammage_g_m2
    d["tear_index_mn_m2_g"] = sheets.tear_mn / sheets.grammage_g_m2
    d["apparent_density_calc_g_cm3"] = sheets.grammage_g_m2 / sheets.caliper_um
    return d
