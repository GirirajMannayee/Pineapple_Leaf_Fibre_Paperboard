"""Storage-trial kinetics (Eqs. 35-36) and threshold interpolation."""
import numpy as np
import pandas as pd
from scipy import stats

GROUPS = ["Uncoated PALF", "FSM-coated PALF", "Commercial reference"]


def slopes(rep: pd.DataFrame, col: str) -> pd.DataFrame:
    """Zero-order rate per group from the pooled regression of all package
    replicates on day (value +/- standard error of the slope, as reported in
    Table 24).  The SD of per-package slopes is returned as an extra column."""
    rows = []
    for g in GROUPS:
        sub = rep[rep.treatment == g]
        lr = stats.linregress(sub.day, sub[col])
        per_pkg = [stats.linregress(x.day, x[col]).slope
                   for _, x in sub.groupby("package_replicate")]
        rows.append({"treatment": g, "slope": lr.slope, "se_slope": lr.stderr,
                     "r2": lr.rvalue ** 2, "per_package_slope_sd": np.std(per_pkg, ddof=1),
                     "n_points": len(sub)})
    return pd.DataFrame(rows)


def group_mean_r2(summ: pd.DataFrame, col: str) -> dict:
    return {g: stats.linregress(s.day, s[col]).rvalue ** 2
            for g, s in summ.groupby("treatment")}


def delta_e(summ: pd.DataFrame) -> pd.DataFrame:
    """CIE76 colour difference vs day 0 using group means."""
    out = []
    for g, s in summ.groupby("treatment"):
        s = s.sort_values("day"); b = s.iloc[0]
        for _, r in s.iterrows():
            out.append({"treatment": g, "day": int(r.day), "delta_E_ab": float(np.sqrt(
                (r.L_star - b.L_star) ** 2 + (r.a_star - b.a_star) ** 2 + (r.b_star - b.b_star) ** 2))})
    return pd.DataFrame(out)


def time_to(summ: pd.DataFrame, col: str, threshold: float, rising=True) -> dict:
    res = {}
    for g, s in summ.groupby("treatment"):
        s = s.sort_values("day"); d, y = s.day.to_numpy(float), s[col].to_numpy(float)
        t = np.nan
        for i in range(1, len(d)):
            lo, hi = y[i - 1], y[i]
            crossed = (lo < threshold <= hi) if rising else (lo >= threshold > hi)
            if crossed:
                t = d[i - 1] + (threshold - lo) * (d[i] - d[i - 1]) / (hi - lo); break
        res[g] = t
    return res


def day_anova(rep: pd.DataFrame, col: str, day=10):
    arrs = [rep[(rep.day == day) & (rep.treatment == g)][col].to_numpy() for g in GROUPS]
    return stats.f_oneway(*arrs).pvalue
