"""Run every analysis in the paper and write model/outputs/.

python3 model/run_all.py [--draws 50000] [--sobol-n 8192]
"""
import argparse, csv, hashlib, json, os, sys, time
import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core, scenarios as SC, uncertainty as UQ
from params import P, central, HOURS0, REGIONS, REGIONS_CN

OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

VEHICLES_2025 = 96.4e6        # OICA, world motor-vehicle production 2025
WORLD_2025 = 28200.0    # TWh, IEA Electricity 2026: global consumption 2025
WORLD_2030 = 33600.0    # TWh, IEA Electricity 2026: global consumption 2030
COMPARATORS = [
    ("Wood Mackenzie, humanoids 2035", 6.0, "F"),
    ("Finland, total consumption 2024", 83.0, "S"),
    ("Wood Mackenzie, all robotics 2035", 363.0, "F"),
    ("IEA, data centres 2025", 485.0, "B"),
    ("IEA, data centres 2030", 950.0, "F"),
    ("Gartner, data centres 2030 (>1,200)", 1200.0, "F"),
    ("IEA, world consumption 2025", WORLD_2025, "B"),
    ("IEA, world consumption 2030", WORLD_2030, "F"),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def j(y):
    return y - 2025


def scenario_block(cal):
    rows, series = {}, {}
    for n in SC.ORDER:
        c = cal[n]; o = c["run"]
        pk35 = core.charging_peaks(o["stock"][0, j(2035)], o["kwh_per_ry"][0, j(2035)])
        pk50 = core.charging_peaks(o["stock"][0, j(2050)], o["kwh_per_ry"][0, j(2050)])
        pk50cn = core.charging_peaks(o["stock"][0, j(2050)], o["kwh_per_ry"][0, j(2050)], REGIONS_CN)
        rows[n] = dict(
            label=SC.SCENARIOS[n]["label"], Qmax=c["Qmax"], k=c["k"], tm=float(o["tm"][0]),
            fit_ratios=c["residuals"], checkpoint_ratios=c["ratio_to_checkpoint"],
            overrides=SC.SCENARIOS[n]["over"],
            **{f"{m}{y}": float(o[m][0, j(y)]) for m in ("q", "stock", "ry", "twh", "offboard_twh", "kwh_per_ry")
               for y in (2030, 2035, 2040, 2050)},
            hh_share_2050=float(o["profile_twh"]["household"][0, j(2050)] / o["twh"][0, j(2050)]),
            peak2035_cn=float(pk35["unmanaged"]["regional"]["China"]),
            peak2035_sum=float(pk35["unmanaged"]["sum"]),
            peak2050_cn=float(pk50["unmanaged"]["regional"]["China"]),
            peak2050_sum=float(pk50["unmanaged"]["sum"]),
            peak2050_sum_managed=float(pk50["managed"]["sum"]),
            peak2050_world=float(pk50["unmanaged"]["world_peak"]),
            peak2050_cn_concentrated=float(pk50cn["unmanaged"]["regional"]["China"]),
            peak_profile_2050_unmanaged=pk50["unmanaged"]["world_profile"].tolist(),
            peak_profile_2050_managed=pk50["managed"]["world_profile"].tolist(),
            peak_regional_2050={r: float(v) for r, v in pk50["unmanaged"]["regional"].items()},
            peak_regional_2050_managed={r: float(v) for r, v in pk50["managed"]["regional"].items()},
            cum_deliveries=float(o["q"][0].sum()),
            q_peak_over_vehicles=float(o["q"][0].max() / VEHICLES_2025),
            year_q_exceeds_vehicles=next((int(y) for y, v in zip(o["years"], o["q"][0]) if v > VEHICLES_2025), None),
            battery_gwh_2050=float(o["q"][0, j(2050)] * P_pack / 1e6),
            charger_gw_2050=float(o["stock"][0, j(2050)] * c["params"]["Pch"] / 1e6),
            share_world_2035=float(o["twh"][0, j(2035)] / WORLD_2030),
            share_world_2050_vs2035=float(o["twh"][0, j(2050)] / WORLD_2030),
        )
        series[n] = dict(years=o["years"].tolist(), q=o["q"][0].tolist(), stock=o["stock"][0].tolist(),
                         twh=o["twh"][0].tolist(), kwh_per_ry=o["kwh_per_ry"][0].tolist(),
                         profile_twh={k: v[0].tolist() for k, v in o["profile_twh"].items()})
    return rows, series


P_pack = 4.0   # kWh nominal pack, hre-2.0.0 central


def ladder_2035(ref):
    """Walk from hre-2.0.0 (13.3 TWh) to this study's 2035 reference, one change at a time."""
    steps = []
    leg = core.legacy_2035()
    steps.append(("hre-2.0.0 as published", leg["twh"]))
    # legacy deliveries in cohort form
    yrs = np.arange(2025, 2036)
    qq = 30000 * (5e6 / 30000) ** ((yrs - 2025) / 10)
    qc = np.zeros(core.COHORTS.size)
    qc[1] = 20000 / 0.88
    qc[2:2 + 10] = qq[1:]
    p = central(); p.update(dict(rSR=1.0, rPc=1.0, rH=1.0, hh0=0.25, hh50=0.25, q_override=qc))
    steps.append(("Cohort survival", float(core.run(p)["twh"][0, j(2035)])))
    p = central(); p.update(dict(rSR=1.0, rPc=1.0, rH=1.0, hh0=0.25, hh50=0.25, Qmax=ref["Qmax"], k=ref["k"]))
    steps.append(("Delivery trajectory", float(core.run(p)["twh"][0, j(2035)])))
    p.pop("hh0"); p["hh50"] = central()["hh50"]
    steps.append(("Use-case mix", float(core.run(p)["twh"][0, j(2035)])))
    p = SC.params_for("reference", ref["Qmax"], ref["k"]); p["rH"] = 1.0
    steps.append(("Hardware learning", float(core.run(p)["twh"][0, j(2035)])))
    p["rH"] = central()["rH"]
    steps.append(("Utilisation", float(core.run(p)["twh"][0, j(2035)])))
    return steps


def ladder_2050(ref):
    """From a frozen-2025 machine on the reference fleet to the 2050 reference."""
    steps = []
    p = SC.params_for("reference", ref["Qmax"], ref["k"])
    p.update(dict(rSR=1.0, rPc=1.0, rH=1.0, hh0=0.05, hh50=0.05))
    steps.append(("Frozen 2025 machine", float(core.run(p)["twh"][0, j(2050)])))
    p["hh50"] = central()["hh50"]
    steps.append(("Household share", float(core.run(p)["twh"][0, j(2050)])))
    p["rSR"] = central()["rSR"]
    steps.append(("Locomotion efficiency", float(core.run(p)["twh"][0, j(2050)])))
    p["rPc"] = central()["rPc"]
    steps.append(("Onboard compute", float(core.run(p)["twh"][0, j(2050)])))
    p["rH"] = central()["rH"]
    steps.append(("Utilisation", float(core.run(p)["twh"][0, j(2050)])))
    return steps


def reverse(ref, targets=(10, 100, 1000, 5000)):
    out = []
    base = SC.params_for("reference", ref["Qmax"], ref["k"])
    for T in targets:
        def g(lq):
            p = dict(base); p["Qmax"] = float(np.exp(lq))
            return core.run(p)["twh"][0, j(2050)] - T
        lq = brentq(g, np.log(base["q26"] * 1.6), np.log(5e9))
        p = dict(base); p["Qmax"] = float(np.exp(lq)); o = core.run(p)
        out.append(dict(target=T, Qmax=float(np.exp(lq)), over_vehicles=float(np.exp(lq) / VEHICLES_2025),
                        stock2050=float(o["stock"][0, j(2050)]), q2035=float(o["q"][0, j(2035)])))
    return out


def economics():
    """Break-even useful-work productivity, Eq. (14) of the manuscript."""
    i, Lr, m, alpha, W, pe = 0.08, 8, 0.10, 0.10, 19.01, 0.15
    A = i * (1 + i) ** Lr / ((1 + i) ** Lr - 1)
    p = SC.params_for("reference")
    Pa = core.active_power(p, "factory", 2050)
    rows = []
    for C in (15000, 30000, 50000, 100000, 200000):
        for H in (2400, 3600, 6000):
            e, Hw, *_ = core.unit_energy(p, Pa, np.array([float(H)]), "factory")
            cost = C * (A + m) + float(e[0]) * pe
            rows.append(dict(capex=C, hours=H, kwh=float(e[0]), elec_cost=float(e[0]) * pe,
                             annual_cost=cost, elec_share=float(e[0]) * pe / cost,
                             p_min=alpha + cost / (H * W)))
    return dict(A=A, rows=rows)


def main(draws, sobol_n):
    t0 = time.time()
    res = dict(meta=dict(model="hre-3.0.0", evidence_cutoff="2026-11-05", draws=draws,
                         sobol_base=sobol_n, seed_mc=20500928, seed_sobol=20500929))
    res["unit_2025"] = {pr: float(core.unit_energy(central(), core.active_power(central(), pr, 2025),
                                                   HOURS0[pr], pr)[0][0]) for pr in core.PROFILES}
    res["unit_detail_2025"] = {}
    for pr in core.PROFILES:
        pc = central(); Pa = core.active_power(pc, pr, 2025)
        e, Hw, Hch, Hr, cap = core.unit_energy(pc, Pa, HOURS0[pr], pr)
        res["unit_detail_2025"][pr] = dict(Pa=float(Pa[0]), H=float(Hw[0]), Hch=float(Hch[0]), Hr=float(Hr[0]), kwh=float(e[0]))
    res["unit_2050_ref"] = {}
    pr_ = SC.params_for("reference")
    for pr in core.PROFILES:
        Pa = core.active_power(pr_, pr, 2050)
        e, Hw, Hch, Hr, cap = core.unit_energy(pr_, Pa, core.active_hours(pr_, pr, 2050), pr)
        res["unit_2050_ref"][pr] = dict(Pa=float(Pa[0]), H=float(Hw[0]), Hch=float(Hch[0]), Hr=float(Hr[0]), kwh=float(e[0]))
    res["legacy_2035"] = {k: (float(v) if not isinstance(v, dict) else v) for k, v in core.legacy_2035().items()}

    print("calibrating scenarios ..."); cal = SC.calibrate()
    res["scenarios"], series = scenario_block(cal)
    ref = res["scenarios"]["reference"]
    # sensitivity: reference fit without the two 2050 installed-base views (MS, Citi)
    saved = SC.SCENARIOS["reference"]["fit"]
    SC.SCENARIOS["reference"]["fit"] = [c for c in saved if c not in ("MS-S2050", "Citi-S2050")]
    Qn, kn, _ = SC.fit("reference")
    SC.SCENARIOS["reference"]["fit"] = saved
    on = core.run(SC.params_for("reference", Qn, kn))
    res["ref_no_secondary"] = dict(Qmax=Qn, k=kn, stock2050=float(on["stock"][0, j(2050)]),
                                   twh2050=float(on["twh"][0, j(2050)]), twh2035=float(on["twh"][0, j(2035)]))
    # sensitivity: reference fit to primary-verified checkpoints only
    SC.SCENARIOS["reference"]["fit"] = [c for c in saved if SC.ACCESS[c] == "P"]
    Qp, kp, _ = SC.fit("reference")
    SC.SCENARIOS["reference"]["fit"] = saved
    op = core.run(SC.params_for("reference", Qp, kp))
    res["ref_primary_only"] = dict(Qmax=Qp, k=kp, n=len([c for c in saved if SC.ACCESS[c] == "P"]),
                                   stock2050=float(op["stock"][0, j(2050)]),
                                   twh2050=float(op["twh"][0, j(2050)]), twh2035=float(op["twh"][0, j(2035)]))
    # reconciliation of the peak basis with annual energy (reference, 2050)
    o_ref = cal["reference"]["run"]
    res["peak_reconcile"] = dict(
        annual_avg_gw=float(o_ref["twh"][0, j(2050)] / 8.76),
        stock_basis_avg_gw=float(o_ref["stock"][0, j(2050)] * o_ref["kwh_per_ry"][0, j(2050)] / 8760 / 1e6),
        legacy_peak_cn_present_basis=float(1.09 / 0.88))
    an = SC.analogue_floor()
    res["analogue"] = dict(twh2035=float(an["twh"][0, j(2035)]), twh2050=float(an["twh"][0, j(2050)]),
                           stock2050=float(an["stock"][0, j(2050)]), q2050=float(an["q"][0, j(2050)]))
    series["analogue"] = dict(years=an["years"].tolist(), q=an["q"][0].tolist(),
                              stock=an["stock"][0].tolist(), twh=an["twh"][0].tolist())
    res["checkpoints"] = [dict(id=c[0], year=c[1], kind=c[2], value=c[3], source=c[4], cls=c[5],
                               access=SC.ACCESS[c[0]])
                          for c in SC.CHECKPOINTS]
    res["ladder_2035"] = ladder_2035(ref)
    res["ladder_2050"] = ladder_2050(ref)
    res["reverse"] = reverse(ref)
    res["economics"] = economics()
    res["comparators"] = COMPARATORS
    res["vehicles_2025"] = VEHICLES_2025

    print("bounds experiment ...")
    mc = {}
    for reading in ("hard", "soft"):
        b = UQ.bounds_experiment(n=draws, reading=reading)
        mc[reading] = {k: v for k, v in b.items() if k.startswith("quant") or k == "capped_share"}
        for sname in SC.ORDER:
            v = res["scenarios"][sname]["twh2050"]
            mc[reading][f"pct_{sname}"] = float((b["twh2050"] < v).mean() * 100)
        if reading == "hard":
            np.savez_compressed(os.path.join(OUT, "mc_samples.npz"), twh2035=b["twh2035"],
                                twh2050=b["twh2050"], stock2050=b["stock2050"])
    # fan band by year for the reference-envelope figure (smaller run, all years)
    rng = np.random.default_rng(20500930)
    pf = UQ.transform(rng.random((10000, len(UQ.SAMPLED))), "hard")
    of = core.run(pf)
    mc["fan"] = {f"p{k}": np.percentile(of["twh"], k, axis=0).tolist() for k in (5, 25, 50, 75, 95)}
    mc["fan_stock"] = {f"p{k}": np.percentile(of["stock"], k, axis=0).tolist() for k in (5, 50, 95)}
    # seed stability
    seeds = []
    for s in range(5):
        b = UQ.bounds_experiment(n=draws // 5, seed=1000 + s)
        seeds.append([b["quant2050"]["p5"], b["quant2050"]["p50"], b["quant2050"]["p95"]])
    seeds = np.array(seeds)
    mc["seed_spread_pct"] = (100 * (seeds.max(0) - seeds.min(0)) / seeds.mean(0)).tolist()
    res["mc"] = mc

    print("sobol ...")
    sob = UQ.sobol(N=sobol_n)
    res["sobol"] = {str(y): v for y, v in sob.items()}
    S1i, STi = UQ.ishigami_check()
    res["ishigami"] = dict(S1=S1i.tolist(), ST=STi.tolist())

    with open(os.path.join(OUT, "series.json"), "w") as fh:
        json.dump(series, fh)
    res["provenance"] = dict(params_sha=sha(os.path.join(HERE, "params.py")),
                             core_sha=sha(os.path.join(HERE, "core.py")),
                             runtime_s=round(time.time() - t0, 1))
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print("done in", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=50000)
    ap.add_argument("--sobol-n", type=int, default=8192)
    a = ap.parse_args()
    main(a.draws, a.sobol_n)
