"""Metaheuristic optimisation of the fitted response surfaces (Eqs. 33-34).

DE uses SciPy; PSO and cockroach-swarm optimisation (CSO) are compact
NumPy implementations so that convergence histories can be recorded.
"""
import numpy as np
from scipy.optimize import differential_evolution, minimize_scalar

from . import desirability as dz
from .rsm import code

BOUNDS_NAT = np.array([[5, 25], [1, 5], [15, 35], [40, 60]], float)
BOUNDS_CODED = np.array([[-1, 1]] * 4, float)


def make_objective(fits, weights=None, anchors=dz.ANCHORS, responses=None, fsm_cap=None):
    responses = responses or list(anchors)

    def f(xc):
        xc = np.atleast_2d(xc)
        preds = {r: fits[r].predict(xc) for r in responses}
        D, _ = dz.overall(preds, weights, anchors, responses)
        pen = 0.0
        if fsm_cap is not None:  # FSM solids (coded B) cap
            b_nat = 3 + 2 * xc[:, 1]
            pen = np.where(b_nat > fsm_cap, 10 * (b_nat - fsm_cap), 0)
        return float(-(np.atleast_1d(D) - pen)[0])
    return f


def run_de(obj, seed=0, popsize=40, tol=1e-10, maxiter=2000):
    r = differential_evolution(obj, BOUNDS_CODED, seed=seed, popsize=popsize, tol=tol,
                               maxiter=maxiter, polish=True, init="sobol")
    return r.x, -r.fun


def run_pso(obj, seed=0, n=40, iters=300, w=0.7, c1=1.5, c2=1.5):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, (n, 4)); v = rng.uniform(-.2, .2, (n, 4))
    pbest, pval = x.copy(), np.array([obj(p) for p in x])
    g = pbest[pval.argmin()].copy(); gval = pval.min(); hist = [-gval]
    for _ in range(iters):
        r1, r2 = rng.random((n, 4)), rng.random((n, 4))
        v = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (g - x)
        x = np.clip(x + v, -1, 1)
        val = np.array([obj(p) for p in x])
        imp = val < pval
        pbest[imp], pval[imp] = x[imp], val[imp]
        if pval.min() < gval:
            gval = pval.min(); g = pbest[pval.argmin()].copy()
        hist.append(-gval)
    return g, -gval, np.array(hist)


def run_cso(obj, seed=0, n=40, iters=300, step=0.3, visual=0.6, hunger=0.1):
    """Cockroach-swarm optimisation (chase-swarming, dispersion, ruthless step)."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, (n, 4)); val = np.array([obj(p) for p in x])
    hist = [-val.min()]
    for it in range(iters):
        best = x[val.argmin()].copy()
        new = x.copy()
        for i in range(n):
            d = np.linalg.norm(x - x[i], axis=1)
            nb = np.where((d < visual) & (val < val[i]))[0]   # better neighbours
            local = x[nb[val[nb].argmin()]] if len(nb) else best
            new[i] = x[i] + step * rng.random(4) * np.sign(local - x[i]) * np.minimum(
                np.abs(local - x[i]), 1) * (1 if len(nb) else 0.5)
            if rng.random() < hunger:                           # dispersion
                new[i] += rng.uniform(-0.1, 0.1, 4)
        new = np.clip(new, -1, 1)
        nv = np.array([obj(p) for p in new])
        acc = nv <= val
        x[acc], val[acc] = new[acc], nv[acc]
        k = rng.integers(n)                                     # ruthless
        x[k] = best; val[k] = obj(best)
        step *= 0.985
        hist.append(-val.min())
    i = val.argmin()
    # local refinement (shrinking random perturbations) to polish the swarm best
    xb, vb = x[i].copy(), val[i]
    for s in np.geomspace(0.05, 1e-5, 400):
        cand = np.clip(xb + rng.normal(0, s, 4), -1, 1)
        cv = obj(cand)
        if cv < vb:
            xb, vb = cand, cv
    return xb, -vb, np.array(hist)


def thickness_only(fits, grid=None):
    """Baseline: search thickness with B=3 %, C=25 %, D=50 C (coded 0)."""
    def D_at(a_nat):
        xc = np.array([[(a_nat - 15) / 10, 0, 0, 0]])
        preds = {r: fits[r].predict(xc) for r in dz.OBJECTIVE}
        return float(np.atleast_1d(dz.overall(preds)[0])[0])
    grid = np.arange(5, 25.0001, 0.5) if grid is None else grid
    Dg = np.array([D_at(a) for a in grid])
    i = Dg.argmax()
    r = minimize_scalar(lambda a: -D_at(a), bounds=(max(5, grid[i] - .5), min(25, grid[i] + .5)),
                        method="bounded", options={"xatol": 1e-8})
    return grid, Dg, float(r.x), float(-r.fun)
