#!/usr/bin/env python3
"""
03_make_figures.py
==================
Regenerates all data-driven figures of the manuscript (Figs 3, 5-23, 25-30) from
the raw CSVs and adds supplementary figures S1-S4.  Output: figures/generated/
as 300-dpi PNG and vector PDF.

Schematic / workflow figures (1, 2, 4, 24, 31-33) are not data-driven; the
original artwork is in figures/manuscript_original/.

Run:  python scripts/03_make_figures.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy import stats
from scipy.optimize import differential_evolution

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from palf_fsm import desirability as dz                                 # noqa: E402
from palf_fsm import groups as gr                                       # noqa: E402
from palf_fsm import io, optimise as op, rsm, storage as st, transport as tr   # noqa: E402

OUT = io.FIGURES
OUT.mkdir(parents=True, exist_ok=True)
RES, PROC = io.RESULTS, io.PROCESSED

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": .25, "grid.linewidth": .5, "figure.dpi": 110, "savefig.dpi": 300,
    "savefig.bbox": "tight", "legend.frameon": False, "legend.fontsize": 8})
COL = {"Uncoated PALF": "#8c6d46", "FSM-coated PALF": "#2a9d8f", "Commercial reference": "#3d5a98"}
SHORT = {"Uncoated PALF": "Uncoated", "FSM-coated PALF": "FSM-coated", "Commercial reference": "Comm. ref."}
FC = {"A": "#d1495b", "B": "#00798c", "C": "#edae49", "D": "#66a182"}

runs = io.run_means(); fits = rsm.fit_all(runs, list(io.RESPONSES))
pk = io.packages(); ssum = io.storage_summary(); srep = io.storage_replicates()
doe = io.load("13_coating_doe_runs"); spec = io.load("12_coating_specimens")
CAND = np.array([21.58, 5.0, 26.94, 55.72])


def save(fig, name):
    fig.savefig(OUT / f"{name}.png"); fig.savefig(OUT / f"{name}.pdf"); plt.close(fig)
    print("  ", name)


def tag(ax, s):
    ax.text(-.12, 1.06, s, transform=ax.transAxes, fontsize=11, fontweight="bold")


def surface(ax, resp, cmap="viridis", levels=14, label=None):
    a = np.linspace(5, 25, 80); b = np.linspace(1, 5, 80)
    AA, BB = np.meshgrid(a, b)
    Xc = np.column_stack([(AA.ravel() - 15) / 10, (BB.ravel() - 3) / 2, np.zeros(AA.size), np.zeros(AA.size)])
    Z = fits[resp].predict(Xc).reshape(AA.shape)
    cs = ax.contourf(AA, BB, Z, levels=levels, cmap=cmap)
    ax.contour(AA, BB, Z, levels=levels, colors="k", linewidths=.3, alpha=.5)
    ax.plot(CAND[0], CAND[1], marker="*", ms=14, mfc="w", mec="k", ls="", clip_on=False, zorder=5)
    ax.set_xlabel("Coating thickness (µm)"); ax.set_ylabel("FSM solids (%)")
    plt.colorbar(cs, ax=ax, label=label or f"{io.RESPONSES[resp]} ({io.UNITS[resp]})")


# ---------------------------------------------------------------- Fig 3
def fig03():
    pairs = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]
    idx = {"A": "A_thickness_um", "B": "B_fsm_solids_pct", "C": "C_glycerol_pct_dry_fsm", "D": "D_drying_temp_c"}
    fig, axs = plt.subplots(2, 3, figsize=(9, 5.6))
    for ax, (p, q) in zip(axs.ravel(), pairs):
        for t, m, c in (("factorial", "o", "#2a9d8f"), ("axial", "s", "#e9c46a"), ("centre", "D", "#d1495b")):
            s = runs[runs.point_type == t]
            ax.scatter(s[idx[p]], s[idx[q]], marker=m, c=c, s=34 if t != "centre" else 60,
                       edgecolor="k", linewidth=.4, alpha=.9, label=t)
        ax.set_xlabel(io.FACTOR_LABELS[p]); ax.set_ylabel(io.FACTOR_LABELS[q])
    axs[0, 0].legend(title="Point type", title_fontsize=8)
    fig.suptitle("Face-centred central composite design (30 runs; 6 overlapping centre points)", y=1.0)
    fig.tight_layout(); save(fig, "Fig03_CCF_design_projections")


# ---------------------------------------------------------------- Fig 5
def fig05():
    names = [io.RESPONSES[k] for k in fits]
    r2 = [f.r2 for f in fits.values()]; pr = [f.pred_r2 for f in fits.values()]
    x = np.arange(len(names)); fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(x - .2, r2, .4, label="R²", color="#2a9d8f"); ax.bar(x + .2, pr, .4, label="Predicted R² (LOO)", color="#e9c46a")
    ax.axhline(.95, ls="--", c="k", lw=.8); ax.set_xticks(x); ax.set_xticklabels(names, rotation=35, ha="right")
    ax.set_ylim(0, 1.05); ax.set_ylabel("Coefficient of determination"); ax.legend(loc="lower left")
    ax.set_title("Second-order model fit vs. predictive ability")
    for i, (a, b) in enumerate(zip(r2, pr)):
        ax.text(i - .2, a + .01, f"{a:.2f}", ha="center", fontsize=6.5); ax.text(i + .2, b + .01, f"{b:.2f}", ha="center", fontsize=6.5)
    save(fig, "Fig05_R2_vs_predicted_R2")


# ---------------------------------------------------------------- Fig 6
def fig06():
    fig, axs = plt.subplots(1, 3, figsize=(11, 4.4))
    for ax, k, lab in zip(axs, ["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit"], "abc"):
        f = fits[k]; d = f.coef_table().iloc[1:].copy(); d["abs_t"] = d.t.abs(); d = d.sort_values("abs_t")
        ax.barh(d.term, d.abs_t, color=["#2a9d8f" if p < .05 else "#bbbbbb" for p in d.p])
        ax.axvline(2.13, ls="--", c="k", lw=.8); ax.set_xlabel("|t| of coded coefficient")
        ax.set_title(io.RESPONSES[k]); tag(ax, f"({lab})")
    fig.suptitle("Standardised effects (dashed: two-sided 5 % critical t = 2.13, 15 df; grey = n.s.)", y=1.02)
    fig.tight_layout(); save(fig, "Fig06_standardised_effects")


# ---------------------------------------------------------------- Fig 7
def fig07():
    ks = ["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit", "fold_double_folds", "compression_n"]
    fig, axs = plt.subplots(1, 5, figsize=(14, 3.1)); t = np.linspace(-1, 1, 41)
    for ax, k in zip(axs, ks):
        for i, f in enumerate("ABCD"):
            X = np.zeros((41, 4)); X[:, i] = t
            ax.plot(t, fits[k].predict(X), color=FC[f], lw=1.8, label=f)
        ax.set_title(io.RESPONSES[k]); ax.set_xlabel("Coded level"); ax.set_ylabel(io.UNITS[k])
    axs[0].legend(title="Factor", ncol=2, title_fontsize=7)
    fig.suptitle("Main effects (A thickness, B FSM solids, C glycerol, D drying T; others at centre)", y=1.04)
    fig.tight_layout(); save(fig, "Fig07_main_effects")


# ---------------------------------------------------------------- Fig 8
def fig08():
    fig, axs = plt.subplots(2, 3, figsize=(10, 6))
    for j, k in enumerate(["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit"]):
        f = fits[k]
        (osm, osr), (sl, ic, r) = stats.probplot(f.stud_resid, dist="norm")
        axs[0, j].scatter(osm, osr, s=22, c="#2a9d8f", edgecolor="k", lw=.3)
        axs[0, j].plot(osm, sl * np.array(osm) + ic, "k--", lw=.8)
        axs[0, j].set_title(f"{io.RESPONSES[k]} (Shapiro p = {f.shapiro_p:.2f})")
        axs[0, j].set_xlabel("Theoretical quantiles"); axs[0, j].set_ylabel("Studentised residuals")
        axs[1, j].scatter(f.fitted, f.stud_resid, s=22, c="#e76f51", edgecolor="k", lw=.3)
        axs[1, j].axhline(0, c="k", lw=.8); axs[1, j].axhline(2, c="gray", ls=":"); axs[1, j].axhline(-2, c="gray", ls=":")
        axs[1, j].set_xlabel("Fitted value"); axs[1, j].set_ylabel("Studentised residuals")
    fig.suptitle("Residual diagnostics: normal probability (top) and residuals vs fitted (bottom)")
    fig.tight_layout(); save(fig, "Fig08_residual_diagnostics")


# ---------------------------------------------------------------- Fig 9
def fig09():
    s = spec[spec.dry_thickness_um > 0]
    fig, axs = plt.subplots(1, 2, figsize=(7.5, 3.4))
    th = s[["thickness_p1_um", "thickness_p2_um", "thickness_p3_um"]].to_numpy()
    axs[0].bar(s.specimen_id, th.mean(1), yerr=th.std(1, ddof=1), capsize=4, color="#2a9d8f", alpha=.85)
    for i, row in enumerate(th):
        axs[0].scatter([i] * 3, row, c="k", s=10, zorder=3)
    axs[0].set_ylabel("Dry coating thickness (µm)"); axs[0].set_title("Thickness (mean ± SD, 3 positions)")
    axs[1].bar(s.specimen_id, s.add_on_g_m2, color="#e9c46a"); axs[1].set_ylabel("Add-on (g m⁻²)"); axs[1].set_title("Gravimetric add-on")
    fig.suptitle("Coated specimens (uncoated control SP-U0: not applicable)", y=1.03)
    fig.tight_layout(); save(fig, "Fig09_specimen_thickness_addon")


# ---------------------------------------------------------------- Fig 10 / 28
def fig10():
    g = pd.read_csv(PROC / "thickness_grid_41_points_model_derived.csv")
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(g.thickness_um, g.overall_desirability, c="#2a9d8f", lw=2)
    i = g.overall_desirability.idxmax(); opt = pd.read_csv(RES / "optimum_thickness_only.csv").iloc[0]
    ax.scatter([opt.thickness_um], [opt.desirability], c="#d1495b", s=60, zorder=3)
    ax.annotate(f"optimum {opt.thickness_um:.2f} µm\nD = {opt.desirability:.4f}", (opt.thickness_um, opt.desirability),
                xytext=(-85, -35), textcoords="offset points", arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel("Coating thickness (µm)"); ax.set_ylabel("Overall desirability D")
    ax.set_title("Thickness-only search (FSM 3 %, glycerol 25 %, 50 °C)")
    save(fig, "Fig10_desirability_vs_thickness")


def fig28():
    fig, ax = plt.subplots(figsize=(6.8, 4)); a = np.linspace(5, 25, 201)
    Xc = np.column_stack([(a - 15) / 10, np.full(a.size, 1.0), np.full(a.size, (26.94 - 25) / 10), np.full(a.size, .572)])
    preds = {r: fits[r].predict(Xc) for r in dz.OBJECTIVE}
    D, ds = dz.overall(preds)
    for i, r in enumerate(dz.OBJECTIVE):
        ax.plot(a, ds[i], lw=1.2, label=io.RESPONSES[r])
    ax.plot(a, D, "k", lw=2.4, label="Overall D")
    ax.axvline(CAND[0], ls=":", c="gray")
    ax.set_xlabel("Coating thickness (µm)"); ax.set_ylabel("Desirability"); ax.legend(ncol=3, loc="lower center", fontsize=7)
    ax.set_title("At optimised FSM 5 %, glycerol 26.94 %, 55.72 °C")
    save(fig, "Fig28_desirability_profile_at_optimum")


# ---------------------------------------------------------------- Fig 11-13
def fig11():
    fig, ax = plt.subplots(figsize=(5.6, 4.2)); surface(ax, "wvtr_g_m2_day", "viridis_r")
    ax.set_title("WVTR response surface (glycerol 25 %, 50 °C; ★ candidate)"); save(fig, "Fig11_WVTR_surface")


def fig12():
    fig, ax = plt.subplots(figsize=(5.6, 4.2)); surface(ax, "cobb60_g_m2", "viridis_r")
    ax.set_title("Cobb60 response surface (glycerol 25 %, 50 °C; ★ candidate)"); save(fig, "Fig12_Cobb60_surface")


def fig13():
    fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.2))
    for ax, (k, cm), l in zip(axs.ravel(), [("grease_kit", "viridis"), ("fold_double_folds", "viridis"),
                                            ("compression_n", "viridis"), ("otr_cm3_m2_day", "viridis_r")], "abcd"):
        surface(ax, k, cm); ax.set_title(io.RESPONSES[k]); tag(ax, f"({l})")
    fig.tight_layout(); save(fig, "Fig13_response_surfaces_grease_fold_compression_OTR")


# ---------------------------------------------------------------- Fig 14
def fig14():
    c = pd.read_csv(RES / "response_correlation_matrix.csv", index_col=0)
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    im = ax.imshow(c, cmap="RdBu_r", vmin=-1, vmax=1); ax.grid(False)
    ax.set_xticks(range(len(c))); ax.set_yticks(range(len(c)))
    ax.set_xticklabels(c.columns, rotation=45, ha="right"); ax.set_yticklabels(c.index)
    for i in range(len(c)):
        for j in range(len(c)):
            ax.text(j, i, f"{c.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                    color="w" if abs(c.iloc[i, j]) > .6 else "k")
    plt.colorbar(im, label="Pearson r"); ax.set_title("Correlation of the ten response means (30 runs)")
    save(fig, "Fig14_correlation_matrix")


# ---------------------------------------------------------------- package panels
def pkg_panel(ax, col, ylabel, letters=True):
    for i, g in enumerate(gr.GROUPS):
        v = pk.loc[pk.treatment == g, col].to_numpy()
        ax.bar(i, v.mean(), yerr=v.std(ddof=1), capsize=4, color=COL[g], alpha=.85, width=.65)
        ax.scatter(np.full(len(v), i) + np.linspace(-.12, .12, len(v)), v, c="k", s=10, zorder=3)
    if letters:
        L = gr.tukey_letters(pk, col)
        tops = [pk.loc[pk.treatment == g, col].max() for g in gr.GROUPS]
        rng_ = max(tops) - min(pk[col].min(), 0)
        for i, g in enumerate(gr.GROUPS):
            ax.text(i, tops[i] + .03 * rng_, L[g], ha="center", fontweight="bold", fontsize=11)
        ax.set_ylim(min(0, pk[col].min() * 1.1), max(tops) + .14 * rng_)
    ax.set_xticks(range(3)); ax.set_xticklabels([SHORT[g] for g in gr.GROUPS]); ax.set_ylabel(ylabel)


def fig15():
    fig, ax = plt.subplots(figsize=(4.8, 3.8)); pkg_panel(ax, "cobb60_g_m2", "Cobb60 (g m⁻²)")
    ax.set_title("Package Cobb60 (n = 5; letters: Tukey HSD)"); save(fig, "Fig15_package_Cobb60")


def fig17():
    fig, ax = plt.subplots(figsize=(4.8, 3.8)); pkg_panel(ax, "compression_n", "Compression (N)")
    ax.set_title("Package compression (n = 5; letters: Tukey HSD)"); save(fig, "Fig17_package_compression")


def fig16():
    s = pd.read_csv(RES / "package_group_summary.csv").set_index("treatment")
    m = s[[c + "_mean" for c in gr.PKG_RESPONSES]]; m.columns = [io.RESPONSES[c] for c in gr.PKG_RESPONSES]
    sc = (m - m.min()) / (m.max() - m.min()); x = np.arange(sc.shape[1])
    fig, ax = plt.subplots(figsize=(9, 3.8))
    for i, g in enumerate(gr.GROUPS):
        ax.bar(x + (i - 1) * .27, sc.loc[g], .27, color=COL[g], label=g)
    ax.set_xticks(x); ax.set_xticklabels(sc.columns, rotation=25, ha="right"); ax.set_ylabel("Min–max scaled group mean")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.18)); ax.set_title("Descriptive profile (not a performance score)", pad=22)
    save(fig, "Fig16_scaled_group_profile")


def fig18():
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, (c, y, l) in zip(axs, [("cobb60_g_m2", "Cobb60 (g m⁻²)", "a"), ("wvtr_g_m2_day", "WVTR (g m⁻² day⁻¹)", "b"),
                                   ("otr_cm3_m2_day", "OTR (cm³ m⁻² day⁻¹)", "c")]):
        pkg_panel(ax, c, y); tag(ax, f"({l})")
    fig.tight_layout(); save(fig, "Fig18_package_barrier_responses")


def fig19():
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, (c, y, l) in zip(axs, [("tensile_md_kn_m", "Tensile MD (kN m⁻¹)", "a"), ("burst_kpa", "Burst (kPa)", "b"),
                                   ("fold_double_folds", "Folding endurance (double folds)", "c")]):
        pkg_panel(ax, c, y); tag(ax, f"({l})")
    fig.tight_layout(); save(fig, "Fig19_package_mechanical_responses")


def fig20():
    s = pd.read_csv(RES / "package_group_statistics.csv"); x = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(9, 3.9))
    ax.bar(x - .2, s.delta_pct_vs_uncoated, .4, color=COL["FSM-coated PALF"], label="FSM-coated PALF")
    ax.bar(x + .2, s.cr_delta_pct_vs_uncoated, .4, color=COL["Commercial reference"], label="Commercial reference")
    ax.axhline(0, c="k", lw=.8); ax.set_xticks(x); ax.set_xticklabels([io.RESPONSES[r] for r in s.response], rotation=25, ha="right")
    ax.set_ylabel("Change vs uncoated PALF (%)"); ax.legend(); ax.set_title("Percentage change in group means (n = 5 per group)")
    for i, v in enumerate(s.delta_pct_vs_uncoated):
        ax.text(i - .2, v + (6 if v >= 0 else -14), f"{v:+.1f}", ha="center", fontsize=7)
    save(fig, "Fig20_percent_change_vs_uncoated")


# ---------------------------------------------------------------- storage
def storage_plot(ax, col, ylabel, mean_only=False):
    for g in gr.GROUPS:
        s = srep[srep.treatment == g].groupby("day")[col].agg(["mean", "std"])
        ax.errorbar(s.index, s["mean"], yerr=s["std"], marker="o", ms=4, capsize=2.5, color=COL[g], label=SHORT[g], lw=1.5)
    ax.set_xlabel("Storage time (day)"); ax.set_ylabel(ylabel)


def fig21():
    fig, ax = plt.subplots(figsize=(5.8, 4)); storage_plot(ax, "mass_loss_pct", "Mass loss (%)")
    sl = st.slopes(srep, "mass_loss_pct").set_index("treatment")
    for g in gr.GROUPS:
        d = np.array([0, 10]); lr = stats.linregress(srep[srep.treatment == g].day, srep[srep.treatment == g].mass_loss_pct)
        ax.plot(d, lr.intercept + lr.slope * d, ls="--", c=COL[g], lw=.8)
    ax.legend(title=None, loc="upper left")
    ax.text(.98, .06, "\n".join(f"{SHORT[g]}: {sl.loc[g, 'slope']:.3f} ± {sl.loc[g, 'se_slope']:.3f} % d⁻¹" for g in gr.GROUPS),
            transform=ax.transAxes, ha="right", fontsize=7.5)
    ax.set_title("Refrigerated storage: mass loss (mean ± SD, n = 3)"); save(fig, "Fig21_storage_mass_loss")


def fig22():
    fig, axs = plt.subplots(2, 3, figsize=(11, 6.2))
    for ax, (c, y), l in zip(axs.ravel(), [("firmness_n", "Firmness (N)"), ("decay_incidence_pct", "Decay incidence (%)"),
                                           ("package_condition_1to5", "Package condition (1–5)"), (None, "ΔE*ab vs day 0"),
                                           ("headspace_o2_pct", "Headspace O₂ (%)"), ("headspace_co2_pct", "Headspace CO₂ (%)")], "abcdef"):
        if c:
            storage_plot(ax, c, y)
        else:
            de = pd.read_csv(RES / "storage_delta_E.csv")
            for g in gr.GROUPS:
                s = de[de.treatment == g]; ax.plot(s.day, s.delta_E_ab, "o-", c=COL[g], ms=4, label=SHORT[g])
            ax.axhline(3, ls=":", c="gray"); ax.set_xlabel("Storage time (day)"); ax.set_ylabel(y)
        tag(ax, f"({l})")
    axs[0, 0].legend(); fig.suptitle("Storage-trial trajectories (mean ± SD, n = 3 packages)", y=1.0)
    fig.tight_layout(); save(fig, "Fig22_storage_trajectories")


# ---------------------------------------------------------------- Fig 23
def fig23():
    fig, axs = plt.subplots(1, 2, figsize=(10, 4)); mk = {0.5: "o", 1.0: "^"}
    cmap = plt.get_cmap("viridis")
    for ax, (c, y, l) in zip(axs, [("cobb60_g_m2", "Cobb60 (g m⁻²)", "a"), ("wvtr_g_m2_day", "WVTR (g m⁻² day⁻¹)", "b")]):
        for t, m in mk.items():
            s = doe[doe.turmeric_pct_dry_fsm == t]
            sc = ax.scatter(s.actual_thickness_um, s[c], c=s.fsm_solids_pct, cmap="viridis", vmin=1, vmax=5, marker=m,
                            s=70, edgecolor="k", lw=.5)
        ax.set_xlabel("Measured dry thickness (µm)"); ax.set_ylabel(y); tag(ax, f"({l})")
    plt.colorbar(sc, ax=axs, label="FSM solids (%)")
    axs[0].legend(handles=[Line2D([], [], marker=m, ls="", c="gray", mec="k", label=f"Turmeric {t} %") for t, m in mk.items()])
    fig.suptitle("Coating-DOE runs (n = 10); turmeric is confounded with thickness", y=1.02); save(fig, "Fig23_coating_DOE_thickness_effects")


# ---------------------------------------------------------------- Fig 25
def fig25():
    sr = pd.read_csv(RES / "series_resistance_partition.csv")
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    sub = 100 - sr.coating_share_pct; co = sr.coating_share_pct; x = np.arange(2)
    ax.bar(x, sub, color="#8c6d46", label="PALF substrate"); ax.bar(x, co, bottom=sub, color="#2a9d8f", label="FSM coating")
    for i in range(2):
        ax.text(i, sub[i] / 2, f"{sub[i]:.1f} %", ha="center", c="w"); ax.text(i, sub[i] + co[i] / 2, f"{co[i]:.1f} %", ha="center", c="w" if co[i] > 15 else "k")
    ax.set_xticks(x); ax.set_xticklabels(["Water vapour", "Oxygen"]); ax.set_ylabel("Share of total transport resistance (%)")
    ax.legend(loc="upper right", bbox_to_anchor=(1, 1.15), ncol=2); ax.set_title("Series-resistance partition (Eq. 9)", pad=24)
    save(fig, "Fig25_series_resistance_partition")


# ---------------------------------------------------------------- Fig 26
def fig26():
    d = pd.read_csv(RES / "individual_desirabilities.csv").set_index("scenario")
    cols = [io.RESPONSES[r] for r in dz.OBJECTIVE] + ["D_overall"]; x = np.arange(len(cols))
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    for i, (sc, c) in enumerate(zip(d.index, ["#bbbbbb", "#2a9d8f"])):
        ax.bar(x + (i - .5) * .38, d.loc[sc, cols], .38, label=sc, color=c)
        for xi, v in zip(x, d.loc[sc, cols]):
            ax.text(xi + (i - .5) * .38, v + .01, f"{v:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(cols[:-1] + ["Overall D"]); ax.set_ylim(0, 1.15); ax.set_ylabel("Desirability")
    ax.legend(loc="upper center", ncol=2); ax.set_title("Which responses limit the optimum?"); save(fig, "Fig26_individual_desirabilities")


# ---------------------------------------------------------------- Fig 27
def fig27():
    obj = op.make_objective(fits); h = pd.read_csv(PROC / "optimiser_convergence.csv")
    hist = []
    def cb(intermediate_result):
        hist.append(-intermediate_result.fun)
    differential_evolution(obj, op.BOUNDS_CODED, seed=3, popsize=15, tol=0, maxiter=300, polish=False, callback=cb, init="random")
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.semilogx(h.iteration[1:], h.PSO[1:], label="PSO", lw=1.8); ax.semilogx(h.iteration[1:], h.Cockroach[1:], label="Cockroach swarm", lw=1.8)
    ax.semilogx(np.arange(1, len(hist) + 1), hist, label="Differential evolution", lw=1.8)
    ax.axhline(.8042, ls=":", c="k"); ax.set_xlabel("Iteration (log scale)"); ax.set_ylabel("Best desirability D")
    ax.legend(loc="lower right"); ax.set_title("Optimiser convergence on the fitted surrogate"); ax.set_ylim(.6, .82)
    save(fig, "Fig27_optimiser_convergence")


# ---------------------------------------------------------------- Fig 29
def fig29():
    ks = ["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit", "fold_double_folds", "compression_n", "otr_cm3_m2_day"]
    fig, axs = plt.subplots(2, 3, figsize=(10.5, 6.4))
    for ax, k in zip(axs.ravel(), ks):
        f = fits[k]; lo, hi = min(f.y.min(), f.fitted.min()), max(f.y.max(), f.fitted.max()); pad = .04 * (hi - lo)
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], "k--", lw=.8)
        ax.scatter(f.y, f.fitted, s=24, c="#2a9d8f", edgecolor="k", lw=.3)
        ax.set_xlabel("Observed run mean"); ax.set_ylabel("Fitted"); ax.set_title(io.RESPONSES[k])
        ax.text(.05, .88, f"R² = {f.r2:.3f}\nPred. R² = {f.pred_r2:.3f}", transform=ax.transAxes, fontsize=8)
    fig.tight_layout(); save(fig, "Fig29_observed_vs_fitted")


# ---------------------------------------------------------------- Fig 30
def fig30():
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax = axs[0]
    ax.scatter(runs.A_thickness_um, runs.coating_add_on_g_m2, s=28, c="#3d5a98", label="30-run RSM", edgecolor="k", lw=.3)
    ax.scatter(doe.actual_thickness_um, doe.add_on_g_m2, s=36, c="#2a9d8f", marker="s", label="Coating DOE", edgecolor="k", lw=.3)
    s = spec[spec.dry_thickness_um > 0]; ax.scatter(s.dry_thickness_um, s.add_on_g_m2, s=60, c="#d1495b", marker="^", label="Specimens", edgecolor="k", lw=.3)
    t = np.linspace(0, 26, 10)
    for rho in (.11, .5, 1.0, 1.5):
        ax.plot(t, rho * t, ls=":", c="gray", lw=.8); ax.text(26, rho * 26, f"ρ = {rho}", fontsize=7, va="center")
    ax.set_xlabel("Dry thickness (µm)"); ax.set_ylabel("Add-on (g m⁻²)"); ax.set_yscale("log"); ax.legend(loc="lower right"); tag(ax, "(a)")
    ax = axs[1]
    ax.scatter(runs.A_thickness_um, runs.cobb60_g_m2, s=28, c="#3d5a98", label="30-run RSM", edgecolor="k", lw=.3)
    ax.scatter(doe.actual_thickness_um, doe.cobb60_g_m2, s=36, c="#2a9d8f", marker="s", label="Coating DOE", edgecolor="k", lw=.3)
    ax.scatter(s.dry_thickness_um, s.cobb60_g_m2, s=60, c="#d1495b", marker="^", label="Specimens", edgecolor="k", lw=.3)
    ax.scatter([15], [pk[pk.treatment == "FSM-coated PALF"].cobb60_g_m2.mean()], s=90, c="#e9c46a", marker="D", label="Package (coated)", edgecolor="k", lw=.5)
    ax.set_xlabel("Dry thickness (µm)"); ax.set_ylabel("Cobb60 (g m⁻²)"); ax.legend(); tag(ax, "(b)")
    fig.suptitle("Cross-dataset comparison: the RSM workbook differs strongly in absolute scale (Section 4.12)", y=1.02)
    fig.tight_layout(); save(fig, "Fig30_cross_dataset_comparison")


# ---------------------------------------------------------------- supplementary
def figS1():
    rp = io.replicates(); fig, axs = plt.subplots(2, 2, figsize=(10, 6.2))
    for ax, k in zip(axs.ravel(), ["cobb60_g_m2", "wvtr_g_m2_day", "grease_kit", "compression_n"]):
        ax.scatter(rp.run, rp[k], s=12, c="#8c6d46", alpha=.7, label="replicates")
        m = runs.set_index("run")[k]; ax.scatter(m.index, m.values, s=36, marker="_", c="k", lw=2, label="run mean")
        ax.set_xlabel("Design run"); ax.set_ylabel(f"{io.RESPONSES[k]} ({io.UNITS[k]})")
    axs[0, 0].legend(); fig.suptitle("Within-run replicates (3 per run) — technical sub-samples, not independent runs"); fig.tight_layout()
    save(fig, "FigS1_within_run_replicates")


def figS2():
    pi = pd.read_csv(RES / "confirmation_runs_prediction_intervals.csv")
    ks = ["Cobb60", "WVTR", "Grease kit", "Folding", "Compression"]
    fig, axs = plt.subplots(1, 5, figsize=(14, 3.4)); y = np.arange(len(pi))[::-1]
    for ax, k in zip(axs, ks):
        ax.errorbar(pi[f"{k}_pred"], y, xerr=[pi[f"{k}_pred"] - pi[f"{k}_PI_low"], pi[f"{k}_PI_high"] - pi[f"{k}_pred"]],
                    fmt="o", c="#2a9d8f", capsize=3)
        ax.set_yticks(y); ax.set_yticklabels([s[:2] for s in pi.setting] if ax is not axs[0] else [s.split(" ")[0] + " " + " ".join(s.split(" ")[1:3]) for s in pi.setting], fontsize=7)
        ax.set_title(k)
    fig.suptitle("Proposed confirmation runs: model prediction and 95 % prediction interval", y=1.04); fig.tight_layout()
    save(fig, "FigS2_confirmation_prediction_intervals")


def figS3():
    s = pd.read_csv(RES / "optimum_sensitivity.csv")
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={"width_ratios": [1.1, 1]})
    axs[0].barh(s.scenario[::-1], s.D_overall[::-1], color="#2a9d8f"); axs[0].set_xlabel("Overall desirability D"); axs[0].set_title("Optimum D by scenario")
    for i, v in enumerate(s.D_overall[::-1]):
        axs[0].text(v + .01, i, f"{v:.3f}", va="center", fontsize=7)
    axs[0].set_xlim(0, 1.15)
    for c, nm in zip(["A_um", "B_pct", "C_pct", "D_C"], ["Thickness (µm)", "FSM (%)", "Glycerol (%)", "Drying (°C)"]):
        lo, hi = {"A_um": (5, 25), "B_pct": (1, 5), "C_pct": (15, 35), "D_C": (40, 60)}[c]
        axs[1].plot(s[c].sub(lo).div(hi - lo), range(len(s)), "o-", label=nm, lw=1)
    axs[1].set_yticks(range(len(s))); axs[1].set_yticklabels(range(1, len(s) + 1)); axs[1].set_xlabel("Position in design range (0 = low, 1 = high)")
    axs[1].set_ylabel("Scenario #"); axs[1].legend(fontsize=7); axs[1].set_title("Optimum location")
    fig.tight_layout(); save(fig, "FigS3_optimum_sensitivity")


def figS4():
    fig, axs = plt.subplots(1, 2, figsize=(10, 4)); t = np.linspace(-1, 1, 41)
    for ax, k in zip(axs, ["cobb60_g_m2", "wvtr_g_m2_day"]):
        for b, c in ((-1, "#d1495b"), (0, "#edae49"), (1, "#2a9d8f")):
            X = np.zeros((41, 4)); X[:, 2] = t; X[:, 1] = b
            ax.plot(25 + 10 * t, fits[k].predict(X), c=c, lw=2, label=f"FSM {3 + 2 * b:g} %")
        ax.set_xlabel("Glycerol (% dry FSM)"); ax.set_ylabel(f"{io.RESPONSES[k]} ({io.UNITS[k]})"); ax.legend()
    fig.suptitle("FSM × glycerol interaction (thickness 15 µm, 50 °C): extra glycerol erodes the benefit of high FSM", y=1.02)
    fig.tight_layout(); save(fig, "FigS4_FSM_glycerol_interaction")


if __name__ == "__main__":
    print("Writing figures to", OUT)
    for fn in (fig03, fig05, fig06, fig07, fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15, fig16, fig17,
               fig18, fig19, fig20, fig21, fig22, fig23, fig25, fig26, fig27, fig28, fig29, fig30,
               figS1, figS2, figS3, figS4):
        fn()
