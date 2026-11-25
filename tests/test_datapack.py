"""Integrity and reproducibility tests.  Run:  pytest -q   (after scripts/02_run_analysis.py)"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from palf_fsm import io, rsm   # noqa: E402


def test_row_counts():
    assert len(io.run_means()) == 30
    assert len(io.replicates()) == 90
    assert len(io.packages()) == 15
    assert len(io.storage_summary()) == 18
    assert len(io.storage_replicates()) == 54
    assert len(io.load("13_coating_doe_runs")) == 10


def test_ccf_design_structure():
    r = io.run_means()
    Xc = rsm.code(r[io.FACTORS].to_numpy(float))
    assert set(np.unique(Xc)) == {-1.0, 0.0, 1.0}
    nz = (Xc != 0).sum(1)
    assert (nz == 4).sum() == 16            # factorial
    assert (nz == 1).sum() == 8             # axial
    assert (nz == 0).sum() == 6             # centre
    assert (r.point_type == "factorial").sum() == 16 and (r.point_type == "axial").sum() == 8
    assert ((r.point_type == "centre") == (nz == 0)).all()


def test_replicates_average_to_run_means():
    r, p = io.run_means().set_index("run"), io.replicates()
    cols = [c for c in r.columns if c not in io.FACTORS + ["point_type"]]
    m = p.groupby("run")[cols].mean()
    assert np.abs(m - r[cols]).max().max() < 2e-3     # run means are printed to 3 decimals


def test_replicate_factors_match_run_factors():
    r, p = io.run_means().set_index("run"), io.replicates().set_index("run")
    for f in io.FACTORS:
        assert (p[f] == r[f].reindex(p.index)).all()


def test_no_negative_physical_values():
    for name in ("07_rsm_run_means", "08_rsm_replicates", "09_package_replicates", "11_storage_replicates"):
        d = io.load(name).select_dtypes("number")
        assert (d.drop(columns=[c for c in d.columns if c in ("day",)]).min() >= 0).all(), name


def test_every_reported_quantity_is_reproduced():
    rep = pd.read_csv(ROOT / "results/reproducibility_report.csv")
    bad = rep[rep.status != "REPRODUCED"]
    assert len(rep) >= 400
    assert bad.empty, bad.to_string()


def test_four_factor_candidate():
    c = pd.read_csv(ROOT / "results/optimiser_comparison.csv")
    de = c.iloc[0]
    assert de.desirability == pytest.approx(0.8042, abs=5e-5)
    assert de.thickness_um == pytest.approx(21.58, abs=0.01)
    assert de.fsm_solids_pct == pytest.approx(5.0, abs=1e-6)


def test_data_dictionary_is_complete():
    dd = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    for f in (ROOT / "data/raw").glob("*.csv"):
        cols = set(pd.read_csv(f).columns)
        assert cols <= set(dd[dd.dataset == f.stem].column), f.name
