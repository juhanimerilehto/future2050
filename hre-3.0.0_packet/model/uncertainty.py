"""Bounds-sampling experiment and Sobol variance decomposition by parameter group.

Two readings of a declared low/central/high (hre-2.0.0, Section 6.2):
  hard  - Triangular(low, central, high)
  soft  - two-piece lognormal, median = central, low/high at the 10th/90th percentile
The shipment ceiling Qmax is sampled on a log scale under both readings.
Sobol indices use Saltelli sampling with the Saltelli (2010) first-order and
Jansen total-effect estimators, by parameter group, with bootstrap intervals.
"""
import numpy as np
from scipy.stats import norm

import core
from params import P

SAMPLED = [k for k in P if P[k]["grp"] != "Offboard"] + ["inf_kw", "inf_duty", "pue"]
LOGSCALE = {"Qmax"}
GROUPS = {}
for k_ in SAMPLED:
    g = P[k_]["grp"]
    if g == "Offboard":
        continue                      # offboard never enters the headline
    GROUPS.setdefault(g, []).append(k_)
GROUP_NAMES = list(GROUPS)


def _tri_ppf(u, a, c, b):
    Fc = (c - a) / (b - a)
    return np.where(u < Fc, a + np.sqrt(u * (b - a) * (c - a)),
                    b - np.sqrt((1 - u) * (b - a) * (b - c)))


def _soft_ppf(u, a, c, b):
    """Two-piece lognormal: median c, a = p10, b = p90 (positive parameters)."""
    z = norm.ppf(np.clip(u, 1e-12, 1 - 1e-12))
    z10 = norm.ppf(0.9)
    sl = np.log(c / a) / z10 if c > a else 0.0
    sh = np.log(b / c) / z10 if b > c else 0.0
    return np.where(z < 0, c * np.exp(sl * z), c * np.exp(sh * z))


def transform(U, reading="hard"):
    """Map a uniform matrix [n, len(SAMPLED)] to a parameter dict."""
    p = {}
    for j, k_ in enumerate(SAMPLED):
        lo, c, hi = P[k_]["lo"], P[k_]["c"], P[k_]["hi"]
        u = U[:, j]
        if reading == "hard":
            if k_ in LOGSCALE:
                p[k_] = np.exp(_tri_ppf(u, np.log(lo), np.log(c), np.log(hi)))
            else:
                p[k_] = _tri_ppf(u, lo, c, hi)
        else:
            lo_ = max(lo, 1e-6) if lo > 0 else c * 0.25   # lognormal needs positive p10
            p[k_] = _soft_ppf(u, lo_, c, hi)
    # physical guards for the soft reading's unbounded tails
    for k_ in ("eta_ch", "eta_pk"):
        p[k_] = np.minimum(p[k_], 0.995)
    for k_ in ("f", "hh50"):
        p[k_] = np.minimum(p[k_], 0.99)
    p["w"] = np.clip(p["w"], 0.01, 0.99)
    p["Qmax"] = np.maximum(p["Qmax"], p["q26"] * 1.5)
    return p


def evaluate(p, years=(2035, 2050), chunk=20000):
    n = len(next(iter(p.values())))
    keep = {y: [] for y in years}
    keep_q = {y: [] for y in years}
    keep_s = {y: [] for y in years}
    off = []
    capped = []
    for s in range(0, n, chunk):
        sub = {k_: (v[s:s + chunk] if np.ndim(v) else v) for k_, v in p.items()}
        o = core.run(sub)
        for y in years:
            j = y - 2025
            keep[y].append(o["twh"][:, j]); keep_q[y].append(o["q"][:, j]); keep_s[y].append(o["stock"][:, j])
        off.append(o["offboard_twh"][:, 2050 - 2025])
        capped.append(o["capped"])
    return ({y: np.concatenate(v) for y, v in keep.items()},
            {y: np.concatenate(v) for y, v in keep_s.items()},
            np.concatenate(off), np.concatenate(capped))


def bounds_experiment(n=50000, seed=20500928, reading="hard"):
    rng = np.random.default_rng(seed)
    U = rng.random((n, len(SAMPLED)))
    p = transform(U, reading)
    twh, stock, off, capped = evaluate(p)
    q = lambda x: {f"p{int(k)}": float(np.percentile(x, k)) for k in (5, 25, 50, 75, 95)}
    return dict(twh2035=twh[2035], twh2050=twh[2050], stock2050=stock[2050], off2050=off,
                quant2035=q(twh[2035]), quant2050=q(twh[2050]), quant_stock2050=q(stock[2050]),
                quant_total2050=q(twh[2050] + off), capped_share=float(capped.mean()))


def sobol(N=8192, seed=20500929, years=(2035, 2050), n_boot=200, reading="hard"):
    rng = np.random.default_rng(seed)
    d = len(SAMPLED)
    A = rng.random((N, d)); B = rng.random((N, d))
    gidx = {g: [SAMPLED.index(k_) for k_ in ks] for g, ks in GROUPS.items()}
    mats = [A, B]
    for g in GROUP_NAMES:
        ABg = A.copy(); ABg[:, gidx[g]] = B[:, gidx[g]]
        mats.append(ABg)
    big = np.vstack(mats)
    twh, *_ = evaluate(transform(big, reading), years=years)
    res = {}
    for y in years:
        Y = twh[y].reshape(len(mats), N)
        fA, fB = Y[0], Y[1]
        out = {}
        for gi, g in enumerate(GROUP_NAMES):
            fABg = Y[2 + gi]

            def est(ix):
                a, b, ab = fA[ix], fB[ix], fABg[ix]
                V = np.var(np.concatenate([a, b]))
                S1 = np.mean(b * (ab - a)) / V
                ST = 0.5 * np.mean((a - ab) ** 2) / V
                return S1, ST
            S1, ST = est(np.arange(N))
            bs = np.array([est(rng.integers(0, N, N)) for _ in range(n_boot)])
            out[g] = dict(S1=float(S1), ST=float(ST),
                          S1_ci=[float(x) for x in np.percentile(bs[:, 0], [2.5, 97.5])],
                          ST_ci=[float(x) for x in np.percentile(bs[:, 1], [2.5, 97.5])])
        res[y] = dict(indices=out, interaction=float(1 - sum(v["S1"] for v in out.values())),
                      n_evals=int(big.shape[0]))
    return res


def ishigami_check(N=20000, seed=1):
    """Validate the estimators on the Ishigami function (a=7, b=0.1)."""
    rng = np.random.default_rng(seed)
    A = rng.uniform(-np.pi, np.pi, (N, 3)); B = rng.uniform(-np.pi, np.pi, (N, 3))
    f = lambda X: np.sin(X[:, 0]) + 7 * np.sin(X[:, 1]) ** 2 + 0.1 * X[:, 2] ** 4 * np.sin(X[:, 0])
    fA, fB = f(A), f(B); V = np.var(np.concatenate([fA, fB]))
    S1, ST = [], []
    for i in range(3):
        AB = A.copy(); AB[:, i] = B[:, i]; fAB = f(AB)
        S1.append(np.mean(fB * (fAB - fA)) / V); ST.append(0.5 * np.mean((fA - fAB) ** 2) / V)
    return np.array(S1), np.array(ST)   # analytic S1 = .314,.442,0 ; ST = .558,.442,.244
