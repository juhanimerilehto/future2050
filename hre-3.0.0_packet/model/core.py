"""Core model: unit energy, shipment trajectory, Weibull cohorts, exposure, energy.

All functions are vectorised over a leading axis of parameter draws, so that the
same code evaluates one scenario or a 100 000-draw sensitivity design.
"""
import numpy as np
from scipy.special import gammainc, gamma

from params import (WEIBULL_K, Q2024, READY_FRAC, HOURS0, TASK, NONHH_SPLIT, HH0,
                    YEARS, AVAIL, SHAPE_UNMANAGED, SHAPE_MANAGED, REGIONS, UTC_OFF)

G = 9.81
PROFILES = ("factory", "warehouse", "household")
COHORTS = np.arange(2024, 2051)          # delivery years carried in the fleet
YR = np.array(YEARS)                      # calendar years reported


def _a(x):
    return np.atleast_1d(np.asarray(x, dtype=float))


def frac(year):
    """Linear progress from 2025 (0) to 2050 (1), clipped."""
    return np.clip((year - 2025.0) / 25.0, 0.0, 1.0)


# --------------------------------------------------------------------------- unit
def active_power(p, profile, cohort):
    """Mix-weighted active electrical draw (kW) for a machine built in `cohort`."""
    phiL, phiM, phiS = TASK[profile]
    SR = _a(p["SR0"]) * (1.0 + (_a(p["rSR"]) - 1.0) * frac(cohort))
    Pc = _a(p["Pc0"]) * (1.0 + (_a(p["rPc"]) - 1.0) * frac(cohort))
    PL = SR * _a(p["mass"]) * G * _a(p["speed"]) / 1000.0
    mech = phiL * PL + phiM * _a(p["kM"]) * PL + phiS * _a(p["kS"]) * PL
    return mech * (1.0 + _a(p["tau"])) + Pc


def active_hours(p, profile, year):
    return HOURS0[profile] * (1.0 + (_a(p["rH"]) - 1.0) * frac(year))


def unit_energy(p, Pa, H, profile):
    """Grid-side kWh per robot-year, the hours actually worked, and a cap flag.

    Charging occupies calendar time: H + Pa*H/(Pch*eta) <= 8760.  Draws that
    request more active hours than the charger can replenish are capped at the
    calendar limit and flagged (hre-2.0.0, Eq. 3, annual form).
    """
    eta = _a(p["eta_ch"]) * _a(p["eta_pk"])
    Pch = _a(p["Pch"])
    Hmax = 8760.0 * Pch * eta / (Pa + Pch * eta)
    capped = H > Hmax
    Hw = np.minimum(H, Hmax)
    Hch = Pa * Hw / (Pch * eta)
    rem = np.maximum(8760.0 - Hw - Hch, 0.0)
    Hr = READY_FRAC[profile] * rem
    Hs = rem - Hr
    e = (Pa * Hw + _a(p["Pr"]) * Hr + _a(p["Ps"]) * Hs) / eta
    e = e * (1.0 + _a(p["dock"])) * (1.0 + _a(p["site"]))
    return e, Hw, Hch, Hr, capped


def household_share(p, cohort):
    hh0 = _a(p.get("hh0", HH0))
    return hh0 + (_a(p["hh50"]) - hh0) * frac(cohort)


def mix_weights(p, cohort):
    hh = household_share(p, cohort)
    return {"factory": (1 - hh) * NONHH_SPLIT["factory"],
            "warehouse": (1 - hh) * NONHH_SPLIT["warehouse"],
            "household": hh}


# -------------------------------------------------------------------------- fleet
def shipments(p):
    """Annual deliveries for COHORTS.  Logistic in calendar time from 2026.

    q_t = Qmax / (1 + exp(-k (t - t_m))), with t_m chosen so that q_2026 equals
    the observed-run-rate anchor q26.  2025 is the reported anchor q25 and 2024
    a fixed residual cohort.
    """
    Q = _a(p["Qmax"]); k = _a(p["k"]); q26 = _a(p["q26"])
    tm = 2026.0 + np.log(Q / q26 - 1.0) / k
    q = np.empty((Q.size, COHORTS.size))
    q[:, 0] = Q2024
    q[:, 1] = _a(p["q25"])
    t = COHORTS[2:][None, :]
    q[:, 2:] = Q[:, None] / (1.0 + np.exp(-k[:, None] * (t - tm[:, None])))
    return q, tm


def _G(x, lam):
    """Integral of Weibull survival from 0 to x (shape WEIBULL_K, scale lam)."""
    x = np.maximum(x, 0.0)
    a = 1.0 / WEIBULL_K
    return lam * gamma(1.0 + a) * gammainc(a, (x / lam) ** WEIBULL_K)


def _W(x, lam):
    return np.where(x < 0, 0.0, np.exp(-(np.maximum(x, 0) / lam) ** WEIBULL_K))


def run(p, years=YR, detail=False):
    """Evaluate the model.  Returns a dict of arrays shaped [draws, years]."""
    if "q_override" in p:                       # externally specified delivery path
        q = np.atleast_2d(np.asarray(p["q_override"], dtype=float)); tm = np.array([np.nan])
    else:
        q, tm = shipments(p)
    n = max(q.shape[0], max(np.size(v) for k_, v in p.items() if k_ != "q_override"))
    if q.shape[0] == 1 and n > 1:
        q = np.repeat(q, n, axis=0)
    lam = _a(p["L"]) / np.log(2.0) ** (1.0 / WEIBULL_K)
    lam = np.broadcast_to(lam, (n,))
    f = np.broadcast_to(_a(p["f"]), (n,))
    w = np.broadcast_to(_a(p["w"]), (n,))

    ny = len(years)
    stock = np.zeros((n, ny)); ry = np.zeros((n, ny)); energy = np.zeros((n, ny))
    prof_E = {pr: np.zeros((n, ny)) for pr in PROFILES}
    capped_any = np.zeros(n, dtype=bool)
    # cache cohort-dependent active power
    Pa = {(pr, c): np.broadcast_to(active_power(p, pr, c), (n,)) for pr in PROFILES for c in COHORTS}
    W8 = {c: mix_weights(p, c) for c in COHORTS}
    for j, t in enumerate(years):
        for i, c in enumerate(COHORTS):
            if c > t:
                break
            tau = c + w
            up = t + 1.0 - tau
            lo = np.maximum(t, tau) - tau
            exp_ = f * q[:, i] * np.where(up > 0, _G(up, lam) - _G(lo, lam), 0.0)
            stock[:, j] += f * q[:, i] * _W(t + 1.0 - tau, lam)
            ry[:, j] += exp_
            for pr in PROFILES:
                e, Hw, _, _, cap = unit_energy(p, Pa[(pr, c)], active_hours(p, pr, t), pr)
                wt = np.broadcast_to(W8[c][pr], (n,))
                contrib = exp_ * wt * e
                energy[:, j] += contrib
                prof_E[pr][:, j] += contrib
                if t == years[-1]:
                    capped_any |= np.broadcast_to(cap, (n,)) & (wt > 0)
    off = ry * (_a(p["inf_kw"]) * _a(p["inf_duty"]) * _a(p["pue"]))[:, None] * 8760.0
    out = dict(years=np.array(years), q=q[:, 1:1 + ny], stock=stock, ry=ry,
               twh=energy / 1e9, offboard_twh=off / 1e9, tm=tm, capped=capped_any)
    out["kwh_per_ry"] = np.divide(energy, ry, out=np.zeros_like(energy), where=ry > 0)
    if detail:
        out["profile_twh"] = {pr: v / 1e9 for pr, v in prof_E.items()}
    return out


# -------------------------------------------------------------------------- peaks
def _shape(vals):
    s = np.array(vals); return s / s.mean()


def charging_peaks(stock_eoy, kwh_per_ry, regions=REGIONS):
    """Regional coincident charging peaks (GW), end-of-year stock basis."""
    # Year-end energised stock times grid energy per robot-year.  The in-service
    # fraction is already in the stock and standby is already in the intensity, so
    # no further availability factor is applied (hre-2.0.0 applied 0.88 here).
    E_kwh = stock_eoy * kwh_per_ry
    res = {}
    for case, shp in (("unmanaged", _shape(SHAPE_UNMANAGED)), ("managed", _shape(SHAPE_MANAGED))):
        regional = {r: E_kwh * sh / 8760.0 * shp.max() / 1e6 for r, sh in regions.items()}
        world = np.zeros(24)
        for r, sh in regions.items():
            local = E_kwh * sh / 8760.0 * shp / 1e6
            world += np.roll(local, -UTC_OFF[r])   # local hour h -> UTC h - offset
        res[case] = dict(regional=regional, sum=sum(regional.values()),
                         world_peak=world.max(), world_profile=world)
    return res


# ------------------------------------------------------------ hre-2.0.0 legacy
def legacy_2035(mix=(0.45, 0.30, 0.25)):
    """Reproduce the hre-2.0.0 reference case with this unit model.

    Geometric shipments 30 000 (2025) -> 5 000 000 (2035), stock recursion with
    constant survival 0.93 and in-service fraction 0.88, exposure by Eq. (6) of
    hre-2.0.0.  The use-case mix (factory, warehouse, household) is the one that
    reproduces the published 1 674 kWh per robot-year.
    """
    from params import central
    p = central(); p["rSR"] = 1.0; p["rPc"] = 1.0; p["rH"] = 1.0
    s, f = 0.93, 0.88
    yrs = np.arange(2025, 2036)
    qq = 30000 * (5e6 / 30000) ** ((yrs - 2025) / 10)
    S = 20000.0
    for qi in qq[1:-1]:
        S = s * S + f * qi
    S34 = S
    S35 = s * S34 + f * qq[-1]
    RY = 0.5 * (1 + s) * S34 + 0.5 * f * qq[-1]
    es = []
    for pr in PROFILES:
        e, *_ = unit_energy(p, active_power(p, pr, 2025), HOURS0[pr], pr)
        es.append(float(e[0]))
    e_mix = float(np.dot(mix, es))
    return dict(stock=S35, ry=RY, kwh=e_mix, twh=RY * e_mix / 1e9, unit=dict(zip(PROFILES, es)))
