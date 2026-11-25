"""Derringer-Suich desirability (Eqs. 30-32) and the manuscript's anchors."""
import numpy as np

# response: (direction, L-or-T, T-or-U)   (anchors from Section 3.7)
ANCHORS = {
    "cobb60_g_m2":       ("min", 70.0, 90.0),    # target, upper bound
    "wvtr_g_m2_day":     ("min", 340.0, 430.0),
    "grease_kit":        ("max", 1.0, 4.0),      # lower bound, target
    "fold_double_folds": ("max", 80.0, 95.0),
    "compression_n":     ("max", 200.0, 225.0),
}
OBJECTIVE = list(ANCHORS)


def d_larger(y, L, T, s=1.0):
    return np.clip((np.asarray(y, float) - L) / (T - L), 0, 1) ** s


def d_smaller(y, T, U, s=1.0):
    return np.clip((U - np.asarray(y, float)) / (U - T), 0, 1) ** s


def individual(resp, y, anchors=ANCHORS):
    kind, a, b = anchors[resp]
    return d_smaller(y, a, b) if kind == "min" else d_larger(y, a, b)


def overall(preds: dict, weights=None, anchors=ANCHORS, responses=None):
    """Weighted geometric mean (Eq. 32). preds: response -> array of predictions."""
    responses = responses or list(anchors)
    w = np.array([1.0 if weights is None else weights.get(r, 1.0) for r in responses])
    ds = np.array([individual(r, preds[r], anchors) for r in responses])
    with np.errstate(divide="ignore"):
        logd = np.where(ds > 0, np.log(np.where(ds > 0, ds, 1)), -np.inf)
    D = np.exp((w[:, None] * logd).sum(0) / w.sum()) if ds.ndim > 1 else \
        np.exp((w * logd).sum() / w.sum())
    return D, ds


def scaled_anchors(fraction: float, mode: str):
    """Scenario helper for Table 35.

    Moves each TARGET by `fraction` of its own desirability range
    (|T - L| or |U - T|): mode='more' makes targets more demanding,
    mode='less' makes them less demanding. The unacceptable bound is unchanged.
    (This definition reproduces the paper's D = 0.7452 / 0.8646.)
    """
    sign = 1 if mode == "more" else -1
    out = {}
    for r, (kind, a, b) in ANCHORS.items():
        s = sign * fraction * (b - a)
        out[r] = (kind, a, b + s) if kind == "max" else (kind, a - s, b)
    return out
