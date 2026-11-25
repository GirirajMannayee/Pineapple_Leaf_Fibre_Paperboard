"""Package-group comparisons (Eqs. 39-40): ANOVA, Tukey HSD, Kruskal-Wallis, effect sizes."""
import numpy as np
import pandas as pd
from scipy import stats

GROUPS = ["Uncoated PALF", "FSM-coated PALF", "Commercial reference"]
PKG_RESPONSES = ["cobb60_g_m2", "wvtr_g_m2_day", "otr_cm3_m2_day", "grease_kit",
                 "tensile_md_kn_m", "burst_kpa", "fold_double_folds", "compression_n"]


def hedges_g(x1, x2):
    n1, n2 = len(x1), len(x2)
    sp = np.sqrt(((n1 - 1) * np.var(x1, ddof=1) + (n2 - 1) * np.var(x2, ddof=1)) / (n1 + n2 - 2))
    J = 1 - 3 / (4 * (n1 + n2) - 9)
    return J * (np.mean(x1) - np.mean(x2)) / sp


def summary(df):
    rows = []
    for g in GROUPS:
        sub = df[df.treatment == g]
        row = {"treatment": g, "n": len(sub)}
        for r in PKG_RESPONSES:
            row[r + "_mean"] = sub[r].mean(); row[r + "_sd"] = sub[r].std(ddof=1)
        rows.append(row)
    return pd.DataFrame(rows)


def compare(df):
    out = []
    for r in PKG_RESPONSES:
        a, b, c = (df.loc[df.treatment == g, r].to_numpy() for g in GROUPS)
        F, p = stats.f_oneway(a, b, c)
        tk = stats.tukey_hsd(a, b, c)
        kw = stats.kruskal(a, b, c)
        out.append({
            "response": r, "anova_F": F, "anova_p": p,
            "tukey_p_coated_vs_uncoated": tk.pvalue[0, 1],
            "tukey_p_coated_vs_cr": tk.pvalue[1, 2],
            "tukey_p_uncoated_vs_cr": tk.pvalue[0, 2],
            "delta_pct_vs_uncoated": 100 * (b.mean() - a.mean()) / a.mean(),
            "abs_hedges_g": abs(hedges_g(b, a)),
            "gci_pct": 100 * (b.mean() - a.mean()) / (c.mean() - a.mean()),
            "kruskal_p": kw.pvalue,
            "cr_delta_pct_vs_uncoated": 100 * (c.mean() - a.mean()) / a.mean()})
    return pd.DataFrame(out)


def tukey_letters(df, response, alpha=0.05):
    """Compact-letter display for the three groups (Fig. 15 / 17)."""
    arrs = [df.loc[df.treatment == g, response].to_numpy() for g in GROUPS]
    p = stats.tukey_hsd(*arrs).pvalue
    means = [a.mean() for a in arrs]
    order = np.argsort(means)[::-1]
    letters = {i: "" for i in range(3)}
    cur = 0; ch = "a"
    letters[order[0]] += ch
    for k in order[1:]:
        placed = False
        for lc in sorted(set("".join(letters.values()))):
            members = [i for i in range(3) if lc in letters[i]]
            if all(p[k, m] >= alpha for m in members):
                letters[k] += lc; placed = True
        if not placed:
            ch = chr(ord(max(set("".join(letters.values())))) + 1)
            letters[k] += ch
    return {GROUPS[i]: "".join(sorted(set(v))) for i, v in letters.items()}
