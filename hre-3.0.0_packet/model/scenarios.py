"""Coherent scenarios and their calibration to published checkpoints.

Each scenario is a narrative: it names the parameters it changes and the
published statements its shipment trajectory is fitted to.  The two shipment
parameters (Qmax, k) are fitted by least squares in log space; every other
unnamed parameter takes its central value.  Checkpoints a scenario is NOT
fitted to are reported afterwards as out-of-fit comparisons.
"""
import numpy as np
from scipy.optimize import least_squares

import core
from params import central

# Published checkpoints (published by 22 October 2026; retrieved by 5 November 2026).  kind: q = annual shipments,
# S = installed / in-service stock.  cls follows the evidence-class scheme.
CHECKPOINTS = [
    # id,               year, kind, value,  source label,                         cls
    ("SAG-2030",        2030, "q", 5.0e5,  "SAG (Sep 2026)",                       "F"),
    ("IDC-2030",        2030, "q", 7.5e5,  "IDC (Oct 2026)",                       "F"),
    ("GS-2030",         2030, "q", 8.9e5,  "Goldman Sachs (Sep 2026)",             "F"),
    ("BofA-2030",       2030, "q", 1.2e6,  "BofA Global Research (Mar 2026)",      "F"),
    ("WM-2035",         2035, "q", 4.0e6,  "Wood Mackenzie (Aug 2026)",            "F"),
    ("GS-2035",         2035, "q", 6.5e6,  "Goldman Sachs (Sep 2026)",             "F"),
    ("BofA-2035",       2035, "q", 1.0e7,  "BofA Global Research (Mar 2026)",      "F"),
    ("Berg-2040",       2040, "q", 2.6e7,  "Berg Insight (Sep 2026)",              "F"),
    ("WM-S2035",        2035, "S", 1.0e7,  "Wood Mackenzie (Aug 2026)",            "F"),
    ("BofA-S2040",      2040, "S", 3.0e8,  "BofA Global Research (Mar 2026)",      "F"),
    ("Citi-S2050",      2050, "S", 6.5e8,  "Citi GPS (Nov 2024)",                      "F"),
    ("MS-S2050",        2050, "S", 1.0e9,  "Morgan Stanley (May 2025)",                "F"),
    ("Tesla-q2028",     2028, "q", 1.04e6, "Tesla (Oct 2026), line-rate target",       "V"),
    ("Musk-S2036",      2036, "S", 1.0e9,  "Musk (Sep 2026), G20 remarks",  "V"),
]
CP = {c[0]: c for c in CHECKPOINTS}

# Source access: P = verified in the publisher's own document; S = available only
# through named secondary reporting at the evidence cutoff.
ACCESS = {"SAG-2030": "S", "IDC-2030": "P", "GS-2030": "S", "BofA-2030": "P", "WM-2035": "P",
          "GS-2035": "S", "BofA-2035": "P", "Berg-2040": "S", "WM-S2035": "P", "BofA-S2040": "P",
          "Citi-S2050": "P", "MS-S2050": "P", "Tesla-q2028": "S", "Musk-S2036": "S"}

SCENARIOS = {
    "constrained": dict(
        label="Constrained",
        narrative="Humanoids remain factory and logistics equipment; household adoption stalls; "
                  "the lowest published near-term trajectory holds.",
        fit=["SAG-2030", "WM-2035"],
        over=dict(hh50=0.10, rH=1.20, rSR=0.85, rPc=1.25, L=8.0)),
    "reference": dict(
        label="Reference",
        narrative="One trajectory fitted jointly to all twelve institutional checkpoints, from the "
                  "2030 shipment forecasts to the 2050 installed-base views; household use grows to "
                  "two-fifths of deliveries; utilisation rises by half.",
        fit=[c[0] for c in CHECKPOINTS if c[5] == "F"],
        over=dict()),
    "accelerated": dict(
        label="Accelerated",
        narrative="The Bank of America trajectory: 10 million shipments in 2035 and a 300 million "
                  "installed base by 2040, household-led.",
        fit=["BofA-2030", "BofA-2035", "BofA-S2040"],
        over=dict(hh50=0.55, rH=1.75, rSR=0.70, rPc=1.75)),
    "abundance": dict(
        label="Abundance",
        narrative="The manufacturer-led trajectory: Tesla's stated 2027 line rate and a billion "
                  "humanoids within ten years of September 2026.",
        fit=["Tesla-q2028", "Musk-S2036"],
        over=dict(hh50=0.65, rH=2.50, rSR=0.60, rPc=2.0, L=10.0)),
}
ORDER = ["constrained", "reference", "accelerated", "abundance"]


def _years_for(ids):
    return sorted({CP[i][1] for i in ids} | {2050})


def model_value(o, year, kind):
    j = int(year) - 2025
    return o["q"][0, j] if kind == "q" else o["stock"][0, j]


def params_for(name, Qmax=None, k=None):
    p = central(); p.update(SCENARIOS[name]["over"])
    if Qmax is not None:
        p["Qmax"], p["k"] = Qmax, k
    return p


def fit(name):
    ids = SCENARIOS[name]["fit"]
    base = params_for(name)

    def resid(x):
        p = dict(base); p["Qmax"] = float(np.exp(x[0])); p["k"] = float(x[1])
        o = core.run(p)
        return [np.log(model_value(o, CP[i][1], CP[i][2]) / CP[i][3]) for i in ids]

    best = None
    for x0 in ([np.log(3e7), 0.6], [np.log(1e8), 0.6], [np.log(3e8), 0.8], [np.log(1e9), 1.0]):
        r = least_squares(resid, x0, bounds=([np.log(2e6), 0.2], [np.log(5e9), 2.0]))
        if best is None or r.cost < best.cost:
            best = r
    Q, k = float(np.exp(best.x[0])), float(best.x[1])
    res = dict(zip(ids, np.array(best.fun)))
    return Q, k, res


def calibrate():
    out = {}
    for n in ORDER:
        Q, k, res = fit(n)
        p = params_for(n, Q, k)
        o = core.run(p, detail=True)
        oof = {}
        for cid, yr, kind, val, src, cls in CHECKPOINTS:
            if yr <= 2050:
                oof[cid] = float(model_value(o, yr, kind) / val)
        out[n] = dict(Qmax=Q, k=k, residuals={i: float(np.exp(v)) for i, v in res.items()},
                      ratio_to_checkpoint=oof, params=p, run=o)
    return out


def analogue_floor(mu=0.0865):
    """Industrial-robot analogue: deliveries grow at the 2015-2025 world
    industrial-robot log-growth rate (IFR, 254k -> 603k) from the 2025 anchor."""
    p = central(); p.update(SCENARIOS["constrained"]["over"])
    q = np.empty(core.COHORTS.size)
    q[0] = 3000.0; q[1] = p["q25"]
    q[2:] = p["q25"] * np.exp(mu * (core.COHORTS[2:] - 2025))
    p["q_override"] = q
    return core.run(p, detail=True)


if __name__ == "__main__":
    cal = calibrate()
    for n, c in cal.items():
        o = c["run"]
        print(f"{n:12s} Qmax={c['Qmax']/1e6:8.1f}M k={c['k']:.3f} tm={o['tm'][0]:.1f}")
        print("   fit ratios:", {k: round(v, 2) for k, v in c["residuals"].items()})
        for y in (2030, 2035, 2040, 2050):
            j = y - 2025
            print(f"   {y}: q={o['q'][0,j]/1e6:8.2f}M S={o['stock'][0,j]/1e6:9.1f}M "
                  f"TWh={o['twh'][0,j]:9.2f} kWh/ry={o['kwh_per_ry'][0,j]:6.0f}")
        print("   oof:", {k: round(v, 2) for k, v in c["ratio_to_checkpoint"].items()})
    a = analogue_floor()
    print("analogue 2035/2050 TWh", a["twh"][0, 10], a["twh"][0, 25], a["stock"][0, 25])
