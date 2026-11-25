#!/usr/bin/env python3
"""Run the full pipeline: analysis -> figures -> Excel -> manifest.  Usage: python run_all.py"""
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
for step in ("02_run_analysis.py", "03_make_figures.py", "04_build_excel.py", "05_build_manifest.py"):
    print(f"\n=== {step} ===")
    subprocess.run([sys.executable, str(ROOT / "scripts" / step)], check=True, cwd=ROOT)
print("\nDone. Optional: recalculate the workbook in LibreOffice/Excel so cached values exist.")
