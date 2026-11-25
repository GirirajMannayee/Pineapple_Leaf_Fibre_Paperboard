"""Second-order response-surface modelling (full quadratic, coded units).

Implements Eqs. 22-29 of the manuscript with NumPy/SciPy only.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats

from .io import CENTRE, STEP

TERMS = ["Intercept", "A", "B", "C", "D", "A²", "B²", "C²", "D²",
         "A×B", "A×C", "A×D", "B×C", "B×D", "C×D"]


def code(X_nat: np.ndarray) -> np.ndarray:
    """Natural (n,4) -> coded (-1..+1) factors, Eq. 23."""
    c = np.array([CENTRE[k] for k in "ABCD"])
    s = np.array([STEP[k] for k in "ABCD"])
    return (np.atleast_2d(X_nat) - c) / s


def decode(Xc: np.ndarray) -> np.ndarray:
    c = np.array([CENTRE[k] for k in "ABCD"])
    s = np.array([STEP[k] for k in "ABCD"])
    return np.atleast_2d(Xc) * s + c


def design_matrix(Xc: np.ndarray) -> np.ndarray:
    """Columns follow TERMS."""
    Xc = np.atleast_2d(Xc)
    A, B, C, D = Xc.T
    return np.column_stack([np.ones(len(Xc)), A, B, C, D, A**2, B**2, C**2, D**2,
                            A*B, A*C, A*D, B*C, B*D, C*D])


@dataclass
class RSMFit:
    name: str
    beta: np.ndarray
    se: np.ndarray
    t: np.ndarray
    p: np.ndarray
    n: int
    p_terms: int
    r2: float
    adj_r2: float
    pred_r2: float
    rmse: float
    ms_res: float
    F: float
    p_model: float
    lof_p: float
    cv_pct: float
    adeq_prec: float
    shapiro_p: float
    y: np.ndarray
    fitted: np.ndarray
    resid: np.ndarray
    hat: np.ndarray
    stud_resid: np.ndarray
    ZtZinv: np.ndarray

    def predict(self, Xc: np.ndarray) -> np.ndarray:
        return design_matrix(Xc) @ self.beta

    def predict_nat(self, X_nat: np.ndarray) -> np.ndarray:
        return self.predict(code(X_nat))

    def prediction_interval(self, Xc: np.ndarray, alpha: float = 0.05):
        """Eq. 29: PI for a single new observation."""
        z = design_matrix(Xc)
        yhat = z @ self.beta
        lev = np.einsum("ij,jk,ik->i", z, self.ZtZinv, z)
        tcrit = stats.t.ppf(1 - alpha / 2, self.n - self.p_terms)
        half = tcrit * np.sqrt(self.ms_res * (1 + lev))
        return yhat, yhat - half, yhat + half, lev

    def coef_table(self) -> pd.DataFrame:
        return pd.DataFrame({"term": TERMS, "coef": self.beta, "se": self.se,
                             "t": self.t, "p": self.p})


def fit_rsm(Xc: np.ndarray, y: np.ndarray, centre_mask: np.ndarray, name: str = "y") -> RSMFit:
    """Fit full quadratic by OLS. centre_mask flags replicated centre runs (pure error)."""
    Z = design_matrix(Xc)
    n, p = Z.shape
    ZtZinv = np.linalg.inv(Z.T @ Z)
    beta = ZtZinv @ Z.T @ y
    fitted = Z @ beta
    resid = y - fitted
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    dfr = n - p
    ms_res = ss_res / dfr
    hat = np.einsum("ij,jk,ik->i", Z, ZtZinv, Z)
    press = float(((resid / (1 - hat)) ** 2).sum())
    se = np.sqrt(np.diag(ZtZinv) * ms_res)
    t = beta / se
    pv = 2 * stats.t.sf(np.abs(t), dfr)
    r2 = 1 - ss_res / ss_tot
    adj = 1 - (ss_res / dfr) / (ss_tot / (n - 1))
    pred = 1 - press / ss_tot
    F = ((ss_tot - ss_res) / (p - 1)) / ms_res
    p_model = stats.f.sf(F, p - 1, dfr)
    # lack of fit from replicated centre points
    yc = y[centre_mask]
    ss_pe, df_pe = float(((yc - yc.mean()) ** 2).sum()), len(yc) - 1
    ss_lof, df_lof = ss_res - ss_pe, dfr - df_pe
    lof_p = stats.f.sf((ss_lof / df_lof) / (ss_pe / df_pe), df_lof, df_pe)
    rmse = np.sqrt(ss_res / n)  # manuscript Eq. 25 (divides by n)
    cv = 100 * np.sqrt(ms_res) / y.mean()
    ap = (fitted.max() - fitted.min()) / np.sqrt(p * ms_res / n)
    stud = resid / np.sqrt(ms_res * (1 - hat))
    sh = stats.shapiro(resid).pvalue
    return RSMFit(name, beta, se, t, pv, n, p, r2, adj, pred, rmse, ms_res, F, p_model,
                  lof_p, cv, ap, sh, y, fitted, resid, hat, stud, ZtZinv)


def fit_all(df: pd.DataFrame, responses) -> dict:
    from .io import FACTORS
    Xc = code(df[FACTORS].to_numpy(float))
    mask = (df["point_type"] == "centre").to_numpy()
    return {r: fit_rsm(Xc, df[r].to_numpy(float), mask, r) for r in responses}
