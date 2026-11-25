#!/usr/bin/env python3
"""Writes metadata/provenance.csv, metadata/file_manifest.csv and metadata/checksums.sha256."""
import hashlib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
SRC = {
    "01_pulp_batches": ("Table 4", "PALF pulp batches"), "02_paperboard_sheets": ("Table 5", "Paperboard sheets"),
    "03_fsm_batches": ("Table 7", "FSM extraction batches"), "04_turmeric_preparations": ("Table 8", "Turmeric preparations"),
    "05_coating_formulations": ("Table 9", "Coating formulations"), "06_rsm_factors": ("Table 11", "RSM factors/levels"),
    "07_rsm_run_means": ("Tables 14-15", "30-run CCD run means"), "08_rsm_replicates": ("Tables 36-37", "90 within-run replicates"),
    "09_package_replicates": ("Table 21", "Package replicates"), "10_storage_summary": ("Table 31", "Storage group means"),
    "11_storage_replicates": ("Table 38", "Storage replicates"), "12_coating_specimens": ("Tables 25-26", "Coated specimens"),
    "13_coating_doe_runs": ("Tables 27-28", "Coating DOE runs")}
rows = []
for stem, (tab, desc) in SRC.items():
    d = pd.read_csv(RAW / f"{stem}.csv")
    rows.append({"dataset": stem, "description": desc, "manuscript_source": tab, "n_rows": len(d), "n_columns": d.shape[1],
                 "n_missing_cells": int(d.isna().sum().sum()),
                 "origin": "Transcribed programmatically from the manuscript tables (scripts/00_extract_from_manuscript.py)",
                 "status": "Awaiting verification against original laboratory records"})
pd.DataFrame(rows).to_csv(ROOT / "metadata/provenance.csv", index=False)

files = sorted(p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts
               and p.name not in ("file_manifest.csv", "checksums.sha256"))
man, sums = [], []
for p in files:
    h = hashlib.sha256(p.read_bytes()).hexdigest(); rel = p.relative_to(ROOT).as_posix()
    man.append({"path": rel, "bytes": p.stat().st_size, "sha256": h}); sums.append(f"{h}  {rel}")
pd.DataFrame(man).to_csv(ROOT / "metadata/file_manifest.csv", index=False)
(ROOT / "metadata/checksums.sha256").write_text("\n".join(sums) + "\n")
print(len(files), "files catalogued")
