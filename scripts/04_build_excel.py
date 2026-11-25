#!/usr/bin/env python3
"""
04_build_excel.py
=================
Builds the complete Excel datapack

    data/PALF_FSM_Complete_Datapack.xlsx            (data + live calculation sheets + charts)
    data/PALF_FSM_Manuscript_Tables_T01-T46.xlsx    (verbatim copy of all 46 manuscript tables)

Conventions
-----------
* Blue font  = hard-coded measured/design input transcribed from the manuscript
* Black font = formula
* Green font = formula that pulls from another sheet
* Yellow fill = cell the user may edit (Desirability_Calculator)
* Calc_* sheets use live Excel formulas; Model_* sheets hold static,
  model-derived output of scripts/02_run_analysis.py (labelled as such).

After running, recalculate with LibreOffice so cached values exist:
    python /mnt/skills/public/xlsx/scripts/recalc.py data/PALF_FSM_Complete_Datapack.xlsx
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from palf_fsm import io                                    # noqa: E402
from palf_fsm.dictionary import COLUMNS                    # noqa: E402

RAW, RES, PROC, MAN = io.RAW, io.RESULTS, io.PROCESSED, ROOT / "data/manuscript_tables"
OUTFILE = ROOT / "data/PALF_FSM_Complete_Datapack.xlsx"

FONT = "Arial"
F_IN = Font(name=FONT, size=10, color="0000FF")
F_CALC = Font(name=FONT, size=10, color="000000")
F_LINK = Font(name=FONT, size=10, color="008000")
F_B = Font(name=FONT, size=10, bold=True)
F_H = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_T = Font(name=FONT, size=14, bold=True, color="1F4E3D")
F_N = Font(name=FONT, size=9, italic=True, color="595959")
FILL_H = PatternFill("solid", start_color="1F4E3D")
FILL_Y = PatternFill("solid", start_color="FFFF00")
FILL_G = PatternFill("solid", start_color="E8F3EE")
FILL_O = PatternFill("solid", start_color="FDEBD0")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()
wb.remove(wb.active)


def fmt_for(col, series):
    if series.dtype.kind in "iu":
        return "0"
    if series.dtype.kind == "f":
        name = col.lower()
        if "pct" in name and series.abs().max() < 200 and series.dropna().round(3).mod(1).abs().max() > 0:
            return "0.000"
        return "0.000" if series.dropna().abs().max() < 1000 else "0.00"
    return "General"


def write_df(ws, df, r0=1, c0=1, input_font=True, header_fill=FILL_H, autofilt=True, widths=None):
    for j, col in enumerate(df.columns):
        c = ws.cell(row=r0, column=c0 + j, value=col)
        c.font, c.fill, c.border = F_H, header_fill, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            if isinstance(v, (np.floating, float)) and np.isnan(v):
                v = None
            elif isinstance(v, np.integer):
                v = int(v)
            elif isinstance(v, np.floating):
                v = float(v)
            c = ws.cell(row=r0 + i, column=c0 + j, value=v)
            c.font = F_IN if (input_font and not isinstance(v, str)) else (F_CALC if not isinstance(v, str) else Font(name=FONT, size=10))
            c.border = BOX
            if isinstance(v, float):
                c.number_format = fmt_for(df.columns[j], df.iloc[:, j])
    for j, col in enumerate(df.columns):
        w = (widths or {}).get(col) or min(max(11, len(str(col)) * 0.9 + 2), 34)
        ws.column_dimensions[L(c0 + j)].width = w
    ws.row_dimensions[r0].height = 42
    if autofilt:
        ws.auto_filter.ref = f"{L(c0)}{r0}:{L(c0 + len(df.columns) - 1)}{r0 + len(df)}"
    ws.freeze_panes = ws.cell(row=r0 + 1, column=c0)


def title(ws, text, note=None):
    ws["A1"] = text; ws["A1"].font = F_T
    if note:
        ws["A2"] = note; ws["A2"].font = F_N
        ws["A2"].alignment = Alignment(wrap_text=False)


def sheet_from_csv(name, csvname, desc):
    df = pd.read_csv(RAW / f"{csvname}.csv")
    ws = wb.create_sheet(name)
    ws.sheet_properties.tabColor = "2A9D8F"
    title(ws, desc, f"Source: data/raw/{csvname}.csv  |  Blue = measured/design input transcribed from the manuscript. Blank = not recorded / not applicable (never zero).")
    write_df(ws, df, r0=4)
    return ws, df


# =============================================================== data sheets
SHEETS = {}
for sname, csv, desc in [
    ("01_Pulp", "01_pulp_batches", "PALF pulp batches (Table 4)"),
    ("02_Sheets", "02_paperboard_sheets", "PALF paperboard sheets (Table 5)"),
    ("03_FSM", "03_fsm_batches", "Fenugreek seed mucilage extraction batches (Table 7)"),
    ("04_Turmeric", "04_turmeric_preparations", "Turmeric ingredient preparations (Table 8)"),
    ("05_Formulations", "05_coating_formulations", "Coating formulation & preparation records (Table 9)"),
    ("06_RSM_Factors", "06_rsm_factors", "Response-surface factors and levels (Table 11)"),
    ("07_RSM_RunMeans", "07_rsm_run_means", "30-run face-centred CCD: factor settings and run-mean responses (Tables 14-15)"),
    ("08_RSM_Replicates", "08_rsm_replicates", "90 within-run replicate records (Tables 36-37) - technical sub-samples, NOT 90 independent runs"),
    ("09_Pkg_Replicates", "09_package_replicates", "Package-performance replicate records, 5 per group (Table 21)"),
    ("10_Storage_Summary", "10_storage_summary", "Storage-trial group means by day (Table 31)"),
    ("11_Storage_Replicates", "11_storage_replicates", "54 storage replicate observations (Table 38), sorted by treatment/package/day"),
    ("12_Specimens", "12_coating_specimens", "Coated-specimen characterisation (Tables 25-26)"),
    ("13_Coating_DOE", "13_coating_doe_runs", "Turmeric-containing coating DOE, 10 populated runs (Tables 27-28)"),
]:
    SHEETS[sname] = sheet_from_csv(sname, csv, desc)

# 11: sort for contiguous SLOPE ranges
ws11, d11 = SHEETS["11_Storage_Replicates"]
order = ["Uncoated PALF", "FSM-coated PALF", "Commercial reference"]
d11s = d11.assign(_o=d11.treatment.map({k: i for i, k in enumerate(order)})).sort_values(
    ["_o", "package_replicate", "day"]).drop(columns="_o").reset_index(drop=True)
for r in range(5, 5 + len(d11) + 1):
    for c in range(1, len(d11.columns) + 1):
        ws11.cell(row=r, column=c).value = None
for i, row in enumerate(d11s.itertuples(index=False), start=5):
    for j, v in enumerate(row, start=1):
        c = ws11.cell(row=i, column=j, value=(None if isinstance(v, float) and np.isnan(v) else (float(v) if isinstance(v, (np.floating,)) else (int(v) if isinstance(v, np.integer) else v))))
        c.font = F_IN if not isinstance(v, str) else Font(name=FONT, size=10)
        c.border = BOX
        if isinstance(v, (float, np.floating)):
            c.number_format = "0.000"
# header row for sheet 11 is row 4; data rows 5..58 -> groups: 5-22, 23-40, 41-58

# 07: coded-factor columns (formulas referencing 06_RSM_Factors)
ws07, d07 = SHEETS["07_RSM_RunMeans"]
ws06, d06 = SHEETS["06_RSM_Factors"]
# add step column to factors sheet: row 5..8 (A..D); columns: factor,symbol,low,centre,high,unit
ws06["G4"] = "step (formula)"; ws06["G4"].font, ws06["G4"].fill, ws06["G4"].border = F_H, FILL_H, BOX
for r in range(5, 9):
    ws06[f"G{r}"] = f"=(E{r}-C{r})/2"; ws06[f"G{r}"].font = F_CALC; ws06[f"G{r}"].border = BOX
    ws06[f"G{r}"].number_format = "0.00"
ncol07 = len(d07.columns)
for k, (lab, srccol, frow) in enumerate([("A_coded", "C", 5), ("B_coded", "D", 6), ("C_coded", "E", 7), ("D_coded", "F", 8)]):
    col = ncol07 + 1 + k
    h = ws07.cell(row=4, column=col, value=lab + " (formula)"); h.font, h.fill, h.border = F_H, FILL_H, BOX
    ws07.column_dimensions[L(col)].width = 13
    for r in range(5, 35):
        c = ws07.cell(row=r, column=col, value=f"=({srccol}{r}-'06_RSM_Factors'!$D${frow})/'06_RSM_Factors'!$G${frow}")
        c.font = F_LINK; c.number_format = "0.0;-0.0;0.0"; c.border = BOX
ws07.auto_filter.ref = f"A4:{L(ncol07 + 4)}34"

# 10: delta E formulas
ws10, d10 = SHEETS["10_Storage_Summary"]
cde = len(d10.columns) + 1
h = ws10.cell(row=4, column=cde, value="deltaE*ab vs day 0 (formula)"); h.font, h.fill, h.border = F_H, FILL_H, BOX
ws10.column_dimensions[L(cde)].width = 16
cL, ca, cb = [L(list(d10.columns).index(x) + 1) for x in ("L_star", "a_star", "b_star")]
for r in range(5, 5 + len(d10)):
    base = 5 + ((r - 5) % 3)    # day-0 row of same treatment (rows sorted day, treatment)
    c = ws10.cell(row=r, column=cde, value=f"=SQRT(({cL}{r}-{cL}{base})^2+({ca}{r}-{ca}{base})^2+({cb}{r}-{cb}{base})^2)")
    c.font = F_CALC; c.number_format = "0.00"; c.border = BOX

# =============================================================== calc sheets
# ---- Calc_Sheet_Indices -----------------------------------------------------
ws = wb.create_sheet("Calc_Sheet_Indices"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Derived sheet properties (Eqs. 1, 2, 17) - live formulas", "Inputs pulled from 02_Sheets; cell-wall density is an assumption (blue).")
ws["A4"] = "Cell-wall density of cellulose (g cm-3)"; ws["A4"].font = F_B
ws["B4"] = 1.5; ws["B4"].font = F_IN; ws["B4"].fill = FILL_Y
ws["C4"] = "Assumption stated in the manuscript (Eq. 2)"; ws["C4"].font = F_N
hdr = ["Index", "SHT-01", "SHT-02", "Unit"]
for j, t in enumerate(hdr, 1):
    c = ws.cell(row=6, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
cols_ = list(pd.read_csv(RAW / "02_paperboard_sheets.csv").columns)
cl = {n: L(cols_.index(n) + 1) for n in cols_}
G, CAL, RHO, TMD, TCD, BUR, TEA = (cl[k] for k in ("grammage_g_m2", "caliper_um", "apparent_density_g_cm3",
                                                   "tensile_md_n_m", "tensile_cd_n_m", "burst_kpa", "tear_mn"))
S = "'02_Sheets'!"
rows_ = [("Apparent density = grammage/caliper", "={S}{G}{r}/{S}{CAL}{r}", "g cm-3", "0.000"),
         ("Porosity", "=100*(1-{S}{RHO}{r}/$B$4)", "%", "0.0"),
         ("Tensile index, MD", "={S}{TMD}{r}/{S}{G}{r}", "N m g-1", "0.0"),
         ("Tensile index, CD", "={S}{TCD}{r}/{S}{G}{r}", "N m g-1", "0.0"),
         ("MD/CD tensile ratio", "={S}{TMD}{r}/{S}{TCD}{r}", "-", "0.00"),
         ("Burst index", "={S}{BUR}{r}/{S}{G}{r}", "kPa m2 g-1", "0.000"),
         ("Tear index", "={S}{TEA}{r}/{S}{G}{r}", "mN m2 g-1", "0.00")]
for i, (lab, f, unit, nf) in enumerate(rows_, start=7):
    ws.cell(row=i, column=1, value=lab).font = F_CALC
    for j, rr in enumerate((5, 6)):
        c = ws.cell(row=i, column=2 + j, value=f.format(S=S, G=G, CAL=CAL, RHO=RHO, TMD=TMD, TCD=TCD, BUR=BUR, TEA=TEA, r=rr))
        c.font = F_LINK; c.number_format = nf; c.border = BOX
    ws.cell(row=i, column=4, value=unit).font = F_CALC
for col, w in zip("ABCD", (40, 12, 12, 14)):
    ws.column_dimensions[col].width = w

# ---- Calc_Prep_Checks ---------------------------------------------------------
ws = wb.create_sheet("Calc_Prep_Checks"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Arithmetic consistency checks on preparation records (Table 39) - live formulas")
pcols = list(pd.read_csv(RAW / "01_pulp_batches.csv").columns); fcols = list(pd.read_csv(RAW / "03_fsm_batches.csv").columns)
pc = {n: L(pcols.index(n) + 1) for n in pcols}; fc = {n: L(fcols.index(n) + 1) for n in fcols}
hdr = ["Check", "Batch 1: recalculated", "Batch 1: reported", "Difference", "Batch 2: recalculated", "Batch 2: reported", "Difference", "Comment"]
for j, t in enumerate(hdr, 1):
    c = ws.cell(row=4, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
    c.alignment = Alignment(wrap_text=True)
checks = [
    ("Pulp yield (%) = dry pulp / initial leaf x 100", "=100*'01_Pulp'!{dp}{r}/'01_Pulp'!{il}{r}", "='01_Pulp'!{py}{r}", "State feedstock moisture basis", pc),
    ("Pulp composition sum (%) (cellulose+hemicellulose+lignin+ash+extractives)",
     "='01_Pulp'!{ce}{r}+'01_Pulp'!{he}{r}+'01_Pulp'!{li}{r}+'01_Pulp'!{as}{r}+'01_Pulp'!{ex}{r}", "=100", "Exceeds 100 %: components on different analytical bases", pc),
    ("FSM extraction yield (%) = dry solids / seed x 100", "=100*'03_FSM'!{ds}{r}/'03_FSM'!{sm}{r}", "='03_FSM'!{ey}{r}", "Consistent", fc),
    ("FSM total solids (%) = dry solids / wet mucilage x 100", "=100*'03_FSM'!{ds}{r}/'03_FSM'!{wm}{r}", "='03_FSM'!{ts}{r}", "B02 differs by ~0.19 points", fc)]
keys = dict(dp=pc["dry_pulp_mass_g"], il=pc["initial_leaf_mass_g"], py=pc["pulp_yield_pct"], ce=pc["cellulose_pct"],
            he=pc["hemicellulose_pct"], li=pc["lignin_pct"], **{"as": pc["ash_pct"]}, ex=pc["extractives_pct"],
            ds=fc["dry_solids_g"], sm=fc["seed_mass_g"], ey=fc["extraction_yield_pct"], wm=fc["wet_mucilage_g"], ts=fc["total_solids_pct"])
for i, (lab, calc, rep, com, _) in enumerate(checks, start=5):
    ws.cell(row=i, column=1, value=lab).font = F_CALC
    for b, (r, c0) in enumerate(((5, 2), (6, 5))):
        a = ws.cell(row=i, column=c0, value=calc.format(r=r, **keys)); a.font = F_LINK; a.number_format = "0.00"
        bb = ws.cell(row=i, column=c0 + 1, value=rep.format(r=r, **keys)); bb.font = F_LINK; bb.number_format = "0.00"
        d = ws.cell(row=i, column=c0 + 2, value=f"={L(c0)}{i}-{L(c0 + 1)}{i}"); d.font = F_CALC; d.number_format = "0.00;-0.00;0.00"
    ws.cell(row=i, column=8, value=com).font = F_N
ws["A10"] = "Implied coating density = add-on / dry thickness (g cm-3)"; ws["A10"].font = F_B
sc = list(pd.read_csv(RAW / "12_coating_specimens.csv").columns); scl = {n: L(sc.index(n) + 1) for n in sc}
for i, (sid, r) in enumerate((("SP-FT05", 6), ("SP-FT10", 7)), start=11):
    ws.cell(row=i, column=1, value=sid).font = F_CALC
    c = ws.cell(row=i, column=2, value=f"='12_Specimens'!{scl['add_on_g_m2']}{r}/'12_Specimens'!{scl['dry_thickness_um']}{r}")
    c.font = F_LINK; c.number_format = "0.00"
ws["A13"] = "RSM centre runs (mean add-on / 15 um)"; ws["A13"].font = F_CALC
rc = list(pd.read_csv(RAW / "07_rsm_run_means.csv").columns); rcl = {n: L(rc.index(n) + 1) for n in rc}
ws["B13"] = f"=AVERAGEIFS('07_RSM_RunMeans'!{rcl['coating_add_on_g_m2']}5:{rcl['coating_add_on_g_m2']}34,'07_RSM_RunMeans'!{rcl['point_type']}5:{rcl['point_type']}34,\"centre\")/15"
ws["B13"].font = F_LINK; ws["B13"].number_format = "0.00"
ws["C13"] = "~9x lower than the specimen records - see docs/DATA_ISSUES.md"; ws["C13"].font = F_N
ws.column_dimensions["A"].width = 64
for col in "BCDEFG":
    ws.column_dimensions[col].width = 16
ws.column_dimensions["H"].width = 54

# ---- Calc_Package_Stats ---------------------------------------------------------
ws = wb.create_sheet("Calc_Package_Stats"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Package-group means, SDs and effect sizes (Table 19, Eqs. 39-40) - live formulas",
      "ANOVA/Tukey/Kruskal-Wallis need statistical software: see results/package_group_statistics.csv (scripts/02_run_analysis.py).")
pcn = list(pd.read_csv(RAW / "09_package_replicates.csv").columns); pcl = {n: L(pcn.index(n) + 1) for n in pcn}
hdr = ["Response", "Unit", "Uncoated mean", "Uncoated SD", "FSM-coated mean", "FSM-coated SD", "Comm. ref. mean", "Comm. ref. SD",
       "Δ% coated vs uncoated", "Δ% ref vs uncoated", "GCI (%)", "|Hedges g| coated vs uncoated", "BIF = uncoated/coated (barrier responses only)"]
for j, t in enumerate(hdr, 1):
    c = ws.cell(row=4, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
ws.row_dimensions[4].height = 44
ws["A15"] = "n per group"; ws["A15"].font = F_B; ws["B15"] = 5; ws["B15"].font = F_IN
pk_resp = [("cobb60_g_m2", "Cobb60", "g m-2"), ("wvtr_g_m2_day", "WVTR", "g m-2 day-1"), ("otr_cm3_m2_day", "OTR", "cm3 m-2 day-1"),
           ("grease_kit", "Grease kit", "rating"), ("tensile_md_kn_m", "Tensile MD", "kN m-1"), ("burst_kpa", "Burst", "kPa"),
           ("fold_double_folds", "Folding", "double folds"), ("compression_n", "Compression", "N")]
for i, (col, nm, unit) in enumerate(pk_resp, start=5):
    c = pcl[col]; sh_ = "'09_Pkg_Replicates'!"
    ws.cell(row=i, column=1, value=nm).font = F_B; ws.cell(row=i, column=2, value=unit).font = F_CALC
    for j, (a, b) in enumerate(((5, 9), (10, 14), (15, 19))):
        m_ = ws.cell(row=i, column=3 + 2 * j, value=f"=AVERAGE({sh_}{c}{a}:{c}{b})"); m_.font = F_LINK; m_.number_format = "0.00"
        s_ = ws.cell(row=i, column=4 + 2 * j, value=f"=STDEV({sh_}{c}{a}:{c}{b})"); s_.font = F_LINK; s_.number_format = "0.00"
    ws.cell(row=i, column=9, value=f"=100*(E{i}-C{i})/C{i}").number_format = "+0.0;-0.0"
    ws.cell(row=i, column=10, value=f"=100*(G{i}-C{i})/C{i}").number_format = "+0.0;-0.0"
    ws.cell(row=i, column=11, value=f"=100*(E{i}-C{i})/(G{i}-C{i})").number_format = "0"
    ws.cell(row=i, column=12, value=f"=ABS((E{i}-C{i})/SQRT(((($B$15-1)*F{i}^2)+(($B$15-1)*D{i}^2))/(2*$B$15-2)))*(1-3/(4*(2*$B$15)-9))").number_format = "0.0"
    ws.cell(row=i, column=13, value=f"=C{i}/E{i}").number_format = "0.00"
    for j in range(9, 14):
        ws.cell(row=i, column=j).font = F_CALC
    for j in range(1, 14):
        ws.cell(row=i, column=j).border = BOX
ws.column_dimensions["A"].width = 14; ws.column_dimensions["B"].width = 14
for j in range(3, 14):
    ws.column_dimensions[L(j)].width = 14

# ---- Calc_Series_Resistance --------------------------------------------------------
ws = wb.create_sheet("Calc_Series_Resistance"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Series-resistance partition (Eqs. 9, 14, 16; Table 29) - live formulas", "Means pulled from Calc_Package_Stats; coverage inputs are assumptions from the manuscript (96-98 %).")
for j, t in enumerate(["Quantity", "WVTR (g m-2 day-1)", "OTR (cm3 m-2 day-1)"], 1):
    c = ws.cell(row=4, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
lab = [("Uncoated PALF (substrate)", "=Calc_Package_Stats!C6", "=Calc_Package_Stats!C7", "0.0"),
       ("FSM-coated PALF", "=Calc_Package_Stats!E6", "=Calc_Package_Stats!E7", "0.0"),
       ("Commercial reference", "=Calc_Package_Stats!G6", "=Calc_Package_Stats!G7", "0.0"),
       ("Barrier improvement factor (coated)", "=B5/B6", "=C5/C6", "0.00"),
       ("Equivalent transmission rate of coating alone", "=1/(1/B6-1/B5)", "=1/(1/C6-1/C5)", "#,##0"),
       ("Coating share of total resistance (%)", "=100*(1-B6/B5)", "=100*(1-C6/C5)", "0.0"),
       ("Substrate share of total resistance (%)", "=100-B10", "=100-C10", "0.0")]
for i, (a, b, c, nf) in enumerate(lab, start=5):
    ws.cell(row=i, column=1, value=a).font = F_CALC
    for j, f in ((2, b), (3, c)):
        x = ws.cell(row=i, column=j, value=f); x.number_format = nf; x.font = F_LINK if "Calc_" in f else F_CALC
ws["A13"] = "Defect-limited ceiling (Eq. 14): 1/(1-coverage)"; ws["A13"].font = F_B
for i, cov in ((14, .96), (15, .98)):
    ws.cell(row=i, column=1, value=f"Coverage {int(cov * 100)} %").font = F_CALC
    x = ws.cell(row=i, column=2, value=cov); x.font = F_IN; x.fill = FILL_Y; x.number_format = "0%"
    y = ws.cell(row=i, column=3, value=f"=1/(1-B{i})"); y.font = F_CALC; y.number_format = "0"
ws.column_dimensions["A"].width = 48; ws.column_dimensions["B"].width = 20; ws.column_dimensions["C"].width = 20

# ---- Calc_Storage_Rates -----------------------------------------------------------------
ws = wb.create_sheet("Calc_Storage_Rates"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Zero-order storage kinetics (Eq. 35) - live SLOPE/RSQ formulas on 11_Storage_Replicates",
      "Rate = slope of pooled regression on day (18 points per group); ± = standard error of the slope (as in Table 24).")
scn = list(pd.read_csv(RAW / "11_storage_replicates.csv").columns); scc = {n: L(scn.index(n) + 1) for n in scn}
for j, t in enumerate(["Metric", "Group", "Slope", "SE of slope", "R²", "Rows"], 1):
    c = ws.cell(row=4, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
i = 5
for col, nm in (("mass_loss_pct", "Mass-loss rate (% day-1)"), ("firmness_n", "Firmness rate (N day-1)")):
    for g, (a, b) in zip(order, ((5, 22), (23, 40), (41, 58))):
        y = f"'11_Storage_Replicates'!{scc[col]}{a}:{scc[col]}{b}"; x = f"'11_Storage_Replicates'!{scc['day']}{a}:{scc['day']}{b}"
        ws.cell(row=i, column=1, value=nm).font = F_CALC; ws.cell(row=i, column=2, value=g).font = F_CALC
        for j, (f, nf) in enumerate(((f"=SLOPE({y},{x})", "0.000"), (f"=STEYX({y},{x})/SQRT(DEVSQ({x}))", "0.000"), (f"=RSQ({y},{x})", "0.000"), (f"=COUNT({y})", "0"))):
            z = ws.cell(row=i, column=3 + j, value=f); z.font = F_LINK; z.number_format = nf
        i += 1
ws.column_dimensions["A"].width = 28; ws.column_dimensions["B"].width = 24
for col in "CDEF":
    ws.column_dimensions[col].width = 13

# ---- Calc_Storage_Pivot (for charts) ---------------------------------------------------------
ws = wb.create_sheet("Calc_Storage_Pivot"); ws.sheet_properties.tabColor = "E9C46A"
title(ws, "Storage means by day and group (SUMIFS pivot of 10_Storage_Summary) - feeds the charts")
sc10 = list(pd.read_csv(RAW / "10_storage_summary.csv").columns); s10 = {n: L(sc10.index(n) + 1) for n in sc10}
blocks = [("mass_loss_pct", "Mass loss (%)"), ("decay_incidence_pct", "Decay incidence (%)"), ("firmness_n", "Firmness (N)")]
r0 = 4
PIV = {}
for col, lab_ in blocks:
    ws.cell(row=r0, column=1, value=lab_).font = F_B
    for j, t in enumerate(["Day"] + order, 1):
        c = ws.cell(row=r0 + 1, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
    for k, d in enumerate((0, 2, 4, 6, 8, 10)):
        r = r0 + 2 + k
        ws.cell(row=r, column=1, value=d).font = F_IN
        for j, g in enumerate(order, 2):
            z = ws.cell(row=r, column=j, value=f"=SUMIFS('10_Storage_Summary'!${s10[col]}$5:${s10[col]}$22,'10_Storage_Summary'!$A$5:$A$22,$A{r},'10_Storage_Summary'!$B$5:$B$22,{L(j)}${r0 + 1})")
            z.font = F_LINK; z.number_format = "0.00"
    PIV[col] = r0
    r0 += 10
for col in "ABCD":
    ws.column_dimensions[col].width = 22

# =============================================================== model sheets (static)
ws = wb.create_sheet("Model_Coefficients"); ws.sheet_properties.tabColor = "F4A261"
coef = pd.read_csv(RES / "rsm_coded_coefficients_wide.csv")
title(ws, "Second-order RSM coded coefficients, all 10 responses (full precision)",
      "MODEL-DERIVED (static): OLS refit of the 30 run means in coded units; produced by scripts/02_run_analysis.py. Used by Desirability_Calculator.")
write_df(ws, coef, r0=4, input_font=False)
for r in range(5, 5 + len(coef)):
    for c in range(2, len(coef.columns) + 1):
        ws.cell(row=r, column=c).number_format = "0.000000"; ws.cell(row=r, column=c).font = F_CALC
COEF_COLS = {c: L(i + 1) for i, c in enumerate(coef.columns)}

ws = wb.create_sheet("Model_Fit_Stats"); ws.sheet_properties.tabColor = "F4A261"
ad = pd.read_csv(RES / "rsm_model_adequacy.csv").drop(columns=["column"])
title(ws, "Model adequacy of the ten second-order models (Tables 13 and 16, recomputed)", "MODEL-DERIVED (static). All values reproduce the manuscript to rounding (see Reproducibility).")
write_df(ws, ad, r0=4, input_font=False)
for r in range(5, 5 + len(ad)):
    for c in range(2, len(ad.columns) + 1):
        ws.cell(row=r, column=c).number_format = "0.0000"
ch = BarChart(); ch.type = "col"; ch.title = "R² and predicted R² of the RSM models"; ch.roundedCorners = False
ch.add_data(Reference(ws, min_col=2, min_row=4, max_row=14), titles_from_data=True)
ch.add_data(Reference(ws, min_col=4, min_row=4, max_row=14), titles_from_data=True)
ch.set_categories(Reference(ws, min_col=1, min_row=5, max_row=14)); ch.y_axis.title = "R²"; ch.y_axis.scaling.min = 0; ch.y_axis.scaling.max = 1.05
ch.legend.overlay = False; ch.title.overlay = False; ch.x_axis.delete = False; ch.y_axis.delete = False; ch.height, ch.width = 8, 18
ws.add_chart(ch, "A17")

ws = wb.create_sheet("Model_Optimisation"); ws.sheet_properties.tabColor = "F4A261"
title(ws, "Optimisation results (Tables 18, 32-35, recomputed)", "MODEL-DERIVED (static). Surrogate-model predictions - NOT validation measurements.")
r = 4
for lab_, f in (("Optimiser comparison (Table 32)", "optimiser_comparison.csv"), ("Thickness-only optimum (Table 18)", "optimum_thickness_only.csv"),
                ("Predicted responses at four-factor candidate (Table 33)", "candidate_predictions.csv"),
                ("Sensitivity of optimum (Table 35)", "optimum_sensitivity.csv"),
                ("Individual desirabilities (Fig. 26)", "individual_desirabilities.csv"),
                ("Ten-seed DE convergence check", "de_ten_seed_check.csv")):
    d = pd.read_csv(RES / f)
    ws.cell(row=r, column=1, value=lab_).font = F_B
    write_df(ws, d, r0=r + 1, input_font=False, autofilt=False)
    ws.freeze_panes = None
    for rr in range(r + 2, r + 2 + len(d)):
        for c in range(1, len(d.columns) + 1):
            if isinstance(ws.cell(row=rr, column=c).value, float):
                ws.cell(row=rr, column=c).number_format = "0.0000" if "desirab" in d.columns[c - 1].lower() or d.columns[c - 1].startswith("D_") else "0.00"
    r += len(d) + 4
ws.column_dimensions["A"].width = 44
for j in range(2, 12):
    ws.column_dimensions[L(j)].width = 15

ws = wb.create_sheet("Model_ConfirmationRuns"); ws.sheet_properties.tabColor = "F4A261"
title(ws, "Proposed confirmation runs: predictions and 95 % prediction intervals (Table 34, Eq. 29)", "MODEL-DERIVED (static). A confirmation batch mean inside the PI is consistent with the model.")
write_df(ws, pd.read_csv(RES / "confirmation_runs_prediction_intervals.csv"), r0=4, input_font=False)
for rr in range(5, 9):
    for c in range(2, 80):
        if isinstance(ws.cell(row=rr, column=c).value, float):
            ws.cell(row=rr, column=c).number_format = "0.00"

ws = wb.create_sheet("Thickness_Grid"); ws.sheet_properties.tabColor = "F4A261"
tg = pd.read_csv(PROC / "thickness_grid_41_points_model_derived.csv")
title(ws, "41-point thickness grid, 5-25 µm in 0.5 µm steps (FSM 3 %, glycerol 25 %, 50 °C)", "MODEL-DERIVED (static).")
write_df(ws, tg, r0=4, input_font=False)
sc_ = ScatterChart(); sc_.title = "Overall desirability vs coating thickness"; sc_.style = 13; sc_.roundedCorners = False
sc_.x_axis.title = "Thickness (µm)"; sc_.y_axis.title = "Overall desirability D"
s = Series(Reference(ws, min_col=2, min_row=5, max_row=45), Reference(ws, min_col=1, min_row=5, max_row=45), title="D"); s.marker.symbol = "none"
sc_.series.append(s); sc_.legend = None; sc_.x_axis.delete = False; sc_.y_axis.delete = False; sc_.title.overlay = False; sc_.height, sc_.width = 8, 14
ws.add_chart(sc_, "M4")

ws = wb.create_sheet("Reproducibility"); ws.sheet_properties.tabColor = "F4A261"
rep = pd.read_csv(RES / "reproducibility_report.csv")
n_ok = int((rep.status == "REPRODUCED").sum())
title(ws, f"Reproducibility report: {n_ok} of {len(rep)} quantities recomputed from raw data match the manuscript within rounding",
      "Each row compares a value recomputed by scripts/02_run_analysis.py with the value printed in the manuscript.")
write_df(ws, rep, r0=4, input_font=False)
for r_ in range(5, 5 + len(rep)):
    for c in (3, 4, 5, 6):
        ws.cell(row=r_, column=c).number_format = "0.0000"
    s_ = ws.cell(row=r_, column=7)
    s_.fill = FILL_G if s_.value == "REPRODUCED" else FILL_O
ws.column_dimensions["B"].width = 52

# =============================================================== Desirability calculator
ws = wb.create_sheet("Desirability_Calculator", 0); ws.sheet_properties.tabColor = "D1495B"
title(ws, "Live response-surface predictor and desirability calculator",
      "Edit the YELLOW cells. Predictions use the coded second-order models (Model_Coefficients); valid only inside the design ranges.")
ws["A4"] = "Factor"; ws["B4"] = "Value"; ws["C4"] = "Range"; ws["D4"] = "Coded"
for c in "ABCD":
    ws[f"{c}4"].font, ws[f"{c}4"].fill, ws[f"{c}4"].border = F_H, FILL_H, BOX
inp = [("A  Thickness (µm)", 21.58, "5 – 25", 5), ("B  FSM solids (% w/w)", 5.0, "1 – 5", 6),
       ("C  Glycerol (% dry FSM)", 26.94, "15 – 35", 7), ("D  Drying temperature (°C)", 55.72, "40 – 60", 8)]
for i, (a, v, rg, frow) in enumerate(inp, start=5):
    ws.cell(row=i, column=1, value=a).font = F_B
    c = ws.cell(row=i, column=2, value=v); c.font, c.fill, c.border = F_IN, FILL_Y, BOX; c.number_format = "0.00"
    ws.cell(row=i, column=3, value=rg).font = F_N
    d = ws.cell(row=i, column=4, value=f"=(B{i}-'06_RSM_Factors'!$D${frow})/'06_RSM_Factors'!$G${frow}")
    d.font = F_LINK; d.number_format = "0.000"
ws["F4"] = "Check"; ws["F4"].font, ws["F4"].fill = F_H, FILL_H
ws["F5"] = '=IF(AND(B5>=5,B5<=25,B6>=1,B6<=5,B7>=15,B7<=35,B8>=40,B8<=60),"Inside design space","OUTSIDE design space – extrapolation")'
ws["F5"].font = F_B
ws["A10"] = "Model terms (coded)"; ws["A10"].font = F_B
terms = ["Intercept", "A", "B", "C", "D", "A²", "B²", "C²", "D²", "A×B", "A×C", "A×D", "B×C", "B×D", "C×D"]
tf = ["=1", "=D5", "=D6", "=D7", "=D8", "=D5^2", "=D6^2", "=D7^2", "=D8^2", "=D5*D6", "=D5*D7", "=D5*D8", "=D6*D7", "=D6*D8", "=D7*D8"]
for i, (t, f) in enumerate(zip(terms, tf), start=11):
    ws.cell(row=i, column=1, value=t).font = F_CALC
    z = ws.cell(row=i, column=2, value=f); z.font = F_CALC; z.number_format = "0.0000"
# predictions
ws["D10"] = "Predicted responses"; ws["D10"].font = F_B
for j, t in enumerate(["Response", "Unit", "Prediction"], 4):
    c = ws.cell(row=11, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
resp_order = list(io.RESPONSES)
PRED_ROW = {}
for k, rcol in enumerate(resp_order):
    r = 12 + k; nm = io.RESPONSES[rcol]; cc = COEF_COLS[nm]
    ws.cell(row=r, column=4, value=nm).font = F_B
    ws.cell(row=r, column=5, value=io.UNITS[rcol]).font = F_CALC
    z = ws.cell(row=r, column=6, value=f"=SUMPRODUCT($B$11:$B$25,Model_Coefficients!{cc}$5:{cc}$19)")
    z.font = F_LINK; z.number_format = "0.000"
    PRED_ROW[rcol] = r
# desirability
ws["A28"] = "Desirability (Derringer–Suich, Eqs. 30–32)"; ws["A28"].font = F_B
for j, t in enumerate(["Response", "Goal", "Lower / target", "Target / upper", "Weight", "Prediction", "d_i", "d_i ^ weight"], 1):
    c = ws.cell(row=29, column=j, value=t); c.font, c.fill, c.border = F_H, FILL_H, BOX
from palf_fsm.desirability import ANCHORS    # noqa: E402
for k, (rcol, (kind, a, b)) in enumerate(ANCHORS.items()):
    r = 30 + k
    ws.cell(row=r, column=1, value=io.RESPONSES[rcol]).font = F_B
    ws.cell(row=r, column=2, value="Minimise" if kind == "min" else "Maximise").font = F_CALC
    for j, v in ((3, a), (4, b), (5, 1)):
        c = ws.cell(row=r, column=j, value=v); c.font, c.fill = F_IN, FILL_Y
    ws.cell(row=r, column=6, value=f"=F{PRED_ROW[rcol]}").number_format = "0.00"
    if kind == "min":
        f = f"=MAX(0,MIN(1,(D{r}-F{r})/(D{r}-C{r})))"      # target C, upper bound D
    else:
        f = f"=MAX(0,MIN(1,(F{r}-C{r})/(D{r}-C{r})))"      # lower C, target D
    ws.cell(row=r, column=7, value=f).number_format = "0.000"
    ws.cell(row=r, column=8, value=f"=G{r}^E{r}").number_format = "0.000"
    for j in (6, 7, 8):
        ws.cell(row=r, column=j).font = F_CALC
ws["A36"] = "Overall desirability D"; ws["A36"].font = F_B
ws["G36"] = "=PRODUCT(H30:H34)^(1/SUM(E30:E34))"; ws["G36"].font = Font(name=FONT, size=12, bold=True); ws["G36"].number_format = "0.0000"; ws["G36"].fill = FILL_G
ws["A38"] = ("Anchors (Cobb60 90→70, WVTR 430→340, grease 1→4, folding 80→95, compression 200→225) are analyst-chosen scoring bounds, not regulatory limits. "
             "Default inputs = four-factor candidate: expected D = 0.8042.")
ws["A38"].font = F_N
ws["A39"] = "Predictions are surrogate-model outputs (R² 0.88–0.99; predicted R² for compression only 0.51) and require physical confirmation."; ws["A39"].font = F_N
for col, w in zip("ABCDEFGH", (30, 14, 16, 18, 14, 22, 12, 14)):
    ws.column_dimensions[col].width = w

# =============================================================== Charts sheet
ws = wb.create_sheet("Charts", 1); ws.sheet_properties.tabColor = "D1495B"
title(ws, "Native Excel charts (linked to the Calc_* sheets)")
bc = BarChart(); bc.type = "col"; bc.title = "Cobb60 by package group (mean)"; bc.roundedCorners = False
ref = Reference(wb["Calc_Package_Stats"], min_col=3, max_col=3, min_row=5, max_row=5)
for col, nm in ((3, "Uncoated"), (5, "FSM-coated"), (7, "Comm. ref.")):
    s = Series(Reference(wb["Calc_Package_Stats"], min_col=col, min_row=5, max_row=5), title=nm); bc.series.append(s)
bc.y_axis.title = "g m-2"; bc.legend.overlay = False; bc.title.overlay = False; bc.x_axis.delete = False; bc.y_axis.delete = False
bc.height, bc.width = 8, 12; ws.add_chart(bc, "A3")

bc2 = BarChart(); bc2.type = "col"; bc2.title = "Change vs uncoated PALF (%)"; bc2.roundedCorners = False
for col, nm in ((9, "FSM-coated"), (10, "Comm. ref.")):
    bc2.series.append(Series(Reference(wb["Calc_Package_Stats"], min_col=col, min_row=5, max_row=12), title=nm))
bc2.set_categories(Reference(wb["Calc_Package_Stats"], min_col=1, min_row=5, max_row=12))
bc2.y_axis.title = "%"; bc2.legend.overlay = False; bc2.title.overlay = False; bc2.x_axis.delete = False; bc2.y_axis.delete = False
bc2.height, bc2.width = 8, 16; ws.add_chart(bc2, "J3")

pv = wb["Calc_Storage_Pivot"]
for idx, (col, lab_) in enumerate(blocks):
    lc = LineChart(); lc.title = f"{lab_} during storage"; lc.roundedCorners = False
    r0_ = PIV[col]
    for j in (2, 3, 4):
        lc.series.append(Series(Reference(pv, min_col=j, min_row=r0_ + 2, max_row=r0_ + 7), title=order[j - 2]))
    lc.set_categories(Reference(pv, min_col=1, min_row=r0_ + 2, max_row=r0_ + 7))
    lc.x_axis.title = "Day"; lc.y_axis.title = lab_; lc.legend.overlay = False; lc.title.overlay = False
    lc.x_axis.delete = False; lc.y_axis.delete = False; lc.height, lc.width = 8, 12
    ws.add_chart(lc, f"{['A', 'J', 'S'][idx]}20")

# =============================================================== Data dictionary
ws = wb.create_sheet("Data_Dictionary", 1); ws.sheet_properties.tabColor = "264653"
title(ws, "Data dictionary", "One row per column per dataset. Provenance classes: measured / design / derived / identifier.")
rows = []
import glob, os
for f in sorted(glob.glob(str(RAW / "*.csv"))):
    nm = os.path.basename(f)[:-4]
    for c in pd.read_csv(f).columns:
        u, d, p = COLUMNS[c]; rows.append([nm, c, u, d, p])
dd = pd.DataFrame(rows, columns=["dataset", "column", "unit", "description", "provenance"])
write_df(ws, dd, r0=4, input_font=False, widths={"dataset": 28, "column": 30, "unit": 16, "description": 90, "provenance": 44})
dd.to_csv(ROOT / "metadata/data_dictionary.csv", index=False)

# =============================================================== README sheet
ws = wb.create_sheet("README", 0); ws.sheet_properties.tabColor = "1F4E3D"
ws.column_dimensions["A"].width = 30; ws.column_dimensions["B"].width = 110
ws["A1"] = "PALF–FSM paperboard datapack: complete Excel workbook"; ws["A1"].font = Font(name=FONT, size=16, bold=True, color="1F4E3D")
lines = [
    ("Manuscript", "Pineapple Leaf Fibre Paperboard with Fenugreek Mucilage–Turmeric Biocoatings for Improved Barrier Performance and Optimisation"),
    ("Purpose", "Complete, machine-readable record of every measurement table in the manuscript, plus live calculation sheets, a working response-surface/desirability calculator and the recomputed model outputs."),
    ("Provenance", "All data sheets were transcribed programmatically (scripts/00_extract_from_manuscript.py) from the 46 tables of the manuscript. The original laboratory workbooks, raw instrument exports and notebooks were NOT available; deposit them alongside this pack."),
    ("Colour code", "Blue = hard-coded input from the manuscript · Black = formula · Green = formula linking to another sheet · Yellow fill = editable assumption/input · Orange tab = model-derived static output."),
    ("Blank cells", "Blank means not recorded / not applicable. It is never a zero measurement."),
    ("Hierarchy warning", "08_RSM_Replicates (90 rows) are within-run technical replicates of the 30 runs; 09 and 11 are 5 and 3 replicates per group. Treat the coating batch as the experimental unit when generalising."),
    ("Model-derived values", "Model_* sheets, Thickness_Grid and the calculator output are surrogate-model results, not measurements."),
    ("Known data issues", "See docs/DATA_ISSUES.md: the 30-run RSM dataset differs strongly in absolute scale from the specimen/DOE/package datasets (add-on ~9x, tensile ~8x, drying energy ~3x, RSM centre Cobb60/WVTR equal to the uncoated group)."),
    ("Recalculation", "Formulas were recalculated with LibreOffice; Excel will recompute on open."),
]
for i, (a, b) in enumerate(lines, start=3):
    ws.cell(row=i, column=1, value=a).font = F_B
    c = ws.cell(row=i, column=2, value=b); c.font = F_CALC; c.alignment = WRAP
    ws.row_dimensions[i].height = 32 if len(b) > 105 else 18
r = 3 + len(lines) + 1
ws.cell(row=r, column=1, value="Sheet index").font = Font(name=FONT, size=12, bold=True)
desc = {
    "README": "This sheet", "Data_Dictionary": "Every column: unit, description, provenance class", "Desirability_Calculator": "Live predictor for all 10 responses and overall desirability D",
    "Charts": "Native Excel charts", "01_Pulp": "PALF pulp batches", "02_Sheets": "Paperboard sheets", "03_FSM": "FSM extraction batches",
    "04_Turmeric": "Turmeric preparations", "05_Formulations": "Coating formulations", "06_RSM_Factors": "Factor ranges",
    "07_RSM_RunMeans": "30-run CCD with coded factors (formulas)", "08_RSM_Replicates": "90 within-run replicates", "09_Pkg_Replicates": "15 package records",
    "10_Storage_Summary": "18 group-day means + ΔE*ab (formulas)", "11_Storage_Replicates": "54 storage replicates", "12_Specimens": "3 coated specimens",
    "13_Coating_DOE": "10 turmeric DOE runs", "Calc_Sheet_Indices": "Porosity, tensile/burst/tear indices (formulas)", "Calc_Prep_Checks": "Arithmetic consistency checks (formulas)",
    "Calc_Package_Stats": "Means, SD, Δ%, GCI, Hedges g (formulas)", "Calc_Series_Resistance": "Series-resistance partition (formulas)",
    "Calc_Storage_Rates": "Storage kinetic rates (SLOPE/RSQ formulas)", "Calc_Storage_Pivot": "SUMIFS pivot feeding charts", "Model_Coefficients": "Coded RSM coefficients (all responses)",
    "Model_Fit_Stats": "R², adj./pred. R², F, LOF, CV, adequate precision", "Model_Optimisation": "DE/PSO/CSO, sensitivity, desirabilities",
    "Model_ConfirmationRuns": "Predictions and 95 % prediction intervals", "Thickness_Grid": "41-point thickness profile", "Reproducibility": "Recomputed vs reported (all checks)"}
for k, name in enumerate(wb.sheetnames, start=r + 1):
    a = ws.cell(row=k, column=1, value=name); a.hyperlink = f"#'{name}'!A1"; a.font = Font(name=FONT, size=10, color="0563C1", underline="single")
    ws.cell(row=k, column=2, value=desc.get(name, "")).font = F_CALC

# order sheets
want = ["README", "Desirability_Calculator", "Charts", "Data_Dictionary"]
rest = [s for s in wb.sheetnames if s not in want]
wb._sheets = [wb[s] for s in want + rest]
for s in wb.worksheets:
    s.sheet_view.showGridLines = False if s.title in ("README", "Charts") else True
wb.save(OUTFILE)
print("saved", OUTFILE)

# =============================================================== manuscript tables workbook
wb2 = Workbook(); wb2.remove(wb2.active)
idx = wb2.create_sheet("Index")
idx["A1"] = "Verbatim transcription of all 46 manuscript tables"; idx["A1"].font = F_T
idx["A2"] = "Text-heavy tables are kept as strings; numeric tables are the printed values."; idx["A2"].font = F_N
for j, t in enumerate(["Sheet", "First column / content"], 1):
    c = idx.cell(row=4, column=j, value=t); c.font, c.fill = F_H, FILL_H
for n in range(1, 47):
    df = pd.read_csv(MAN / f"Table_{n:02d}.csv", dtype=str, keep_default_na=False)
    s = wb2.create_sheet(f"T{n:02d}")
    write_df(s, df, r0=1, input_font=False, autofilt=False)
    for row in s.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for j in range(1, len(df.columns) + 1):
        s.column_dimensions[L(j)].width = 18 if len(df.columns) > 5 else 34
    a = idx.cell(row=4 + n, column=1, value=f"T{n:02d}"); a.hyperlink = f"#'T{n:02d}'!A1"; a.font = Font(name=FONT, color="0563C1", underline="single")
    idx.cell(row=4 + n, column=2, value=", ".join(df.columns[:4])[:110]).font = F_CALC
idx.column_dimensions["A"].width = 10; idx.column_dimensions["B"].width = 110
wb2.save(ROOT / "data/PALF_FSM_Manuscript_Tables_T01-T46.xlsx")
print("saved manuscript-tables workbook")
