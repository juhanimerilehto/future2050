"""Emit every model-derived number in the manuscript as a LaTeX macro (numbers.tex)
and the generated table bodies (tab_*.tex).  The manuscript contains no literal
model output; a test checks that the headline appears only via these macros."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
R = json.load(open(os.path.join(OUT, "results.json")))
from params import P

M = {}


def th(v, d=0):
    s = f"{v:,.{d}f}"
    return s.replace(",", "\\,")


def units(v):
    """Human-readable unit count: 724 million, 1.07 billion, 55.3 million."""
    if v >= 1e9: return f"{v/1e9:.2f}~billion"
    if v >= 1e8: return f"{v/1e6:.0f}~million"
    if v >= 1e7: return f"{v/1e6:.0f}~million"
    if v >= 1e6: return f"{v/1e6:.1f}~million"
    if v >= 1e3: return f"{v/1e3:.0f}\\,000"
    return f"{v:.0f}"


def twh(v):
    if v >= 100: return th(v)
    if v >= 10: return f"{v:.1f}"
    if v >= 1: return f"{v:.2f}"
    return f"{v:.2f}"


def put(name, val):
    assert re.fullmatch(r"[A-Za-z]+", name), name
    M[name] = val


SC = R["scenarios"]
NM = {"constrained": "Con", "reference": "Ref", "accelerated": "Acc", "abundance": "Abu"}
for n, ab in NM.items():
    s = SC[n]
    for y, yy in ((2030, "Thirty"), (2035, "ThirtyFive"), (2040, "Forty"), (2050, "Fifty")):
        put(f"{ab}TWh{yy}", twh(s[f"twh{y}"]))
        put(f"{ab}Stock{yy}", units(s[f"stock{y}"]))
        put(f"{ab}Ship{yy}", units(s[f"q{y}"]))
        put(f"{ab}Kwh{yy}", th(s[f"kwh_per_ry{y}"]))
        put(f"{ab}Off{yy}", twh(s[f"offboard_twh{y}"]))
    put(f"{ab}Qmax", units(s["Qmax"]))
    put(f"{ab}QmaxM", f"{s['Qmax']/1e6:.0f}")
    put(f"{ab}k", f"{s['k']:.2f}")
    put(f"{ab}kpct", f"{(2.718281828**s['k']-1)*100:.0f}")
    put(f"{ab}tm", f"{s['tm']:.0f}")
    put(f"{ab}VehRatio", f"{s['q_peak_over_vehicles']:.2f}")
    yv = s["year_q_exceeds_vehicles"]
    put(f"{ab}VehYear", str(yv) if yv else "never")
    put(f"{ab}Cum", units(s["cum_deliveries"]))
    put(f"{ab}PeakCN", th(s["peak2050_cn"]) if s["peak2050_cn"] >= 10 else f"{s['peak2050_cn']:.1f}")
    put(f"{ab}PeakSum", th(s["peak2050_sum"]) if s["peak2050_sum"] >= 10 else f"{s['peak2050_sum']:.1f}")
    put(f"{ab}PeakSumMan", th(s["peak2050_sum_managed"]) if s["peak2050_sum_managed"] >= 10 else f"{s['peak2050_sum_managed']:.1f}")
    put(f"{ab}PeakWorld", th(s["peak2050_world"]) if s["peak2050_world"] >= 10 else f"{s['peak2050_world']:.1f}")
    put(f"{ab}PeakCNconc", th(s["peak2050_cn_concentrated"]) if s["peak2050_cn_concentrated"] >= 10 else f"{s['peak2050_cn_concentrated']:.1f}")
    put(f"{ab}PeakCNThirtyFive", f"{s['peak2035_cn']:.1f}")
    put(f"{ab}HHshare", f"{100*s['hh_share_2050']:.0f}")
    put(f"{ab}Battery", th(s["battery_gwh_2050"]))
    put(f"{ab}ChargerGW", th(s["charger_gw_2050"]))
    put(f"{ab}WorldShare", f"{100*s['share_world_2050_vs2035']:.1f}")
    put(f"{ab}WorldShareThirtyFive", f"{100*s['share_world_2035']:.2f}")

ref = SC["reference"]
fr = ref["fit_ratios"]
put("RefFitMin", f"{min(fr.values()):.2f}"); put("RefFitMax", f"{max(fr.values()):.2f}")
import math
put("RefFitGeo", f"{math.exp(sum(abs(math.log(v)) for v in fr.values())/len(fr)):.2f}")
cr = ref["checkpoint_ratios"]
put("RefCitiRatio", f"{cr['Citi-S2050']:.2f}"); put("RefMSRatio", f"{cr['MS-S2050']:.2f}")
put("RefGSThirtyFive", f"{cr['GS-2035']:.2f}"); put("RefBerg", f"{cr['Berg-2040']:.2f}")
put("RefBofASForty", f"{cr['BofA-S2040']:.2f}")
put("RefWMSThirtyFive", f"{cr['WM-S2035']:.2f}")
put("AccBofAThirty", f"{SC['accelerated']['fit_ratios']['BofA-2030']:.2f}")
put("AccBofAThirtyFive", f"{SC['accelerated']['fit_ratios']['BofA-2035']:.2f}")
put("AccBofASForty", f"{SC['accelerated']['fit_ratios']['BofA-S2040']:.2f}")
put("AbuStockThirtyFiveTxt", units(SC["abundance"]["stock2035"]))
put("RatioFiftyThirtyFive", f"{ref['twh2050']/ref['twh2035']:.0f}")
put("RatioRefLegacy", f"{ref['twh2035']/R['legacy_2035']['twh']:.2f}")
put("RatioAbuCon", f"{SC['abundance']['twh2050']/SC['constrained']['twh2050']:.0f}")

L = R["legacy_2035"]
put("LegacyTWh", f"{L['twh']:.1f}"); put("LegacyStock", f"{L['stock']/1e6:.2f}~million"); put("LegacyRY", f"{L['ry']/1e6:.2f}~million")
put("LegacyErr", f"{abs(L['twh']/13.3-1)*100:.2f}")
u = R["unit_detail_2025"]; u5 = R["unit_2050_ref"]
for pr, ab in (("factory", "Fac"), ("warehouse", "Wh"), ("household", "Hh")):
    put(f"Unit{ab}TwentyFive", th(u[pr]["kwh"])); put(f"Unit{ab}Fifty", th(u5[pr]["kwh"]))
    put(f"Unit{ab}PaTwentyFive", f"{u[pr]['Pa']:.3f}"); put(f"Unit{ab}PaFifty", f"{u5[pr]['Pa']:.3f}")
    put(f"Unit{ab}HFifty", th(u5[pr]["H"])); put(f"Unit{ab}HchFifty", th(u5[pr]["Hch"]))
    put(f"Unit{ab}HrFifty", th(u5[pr]["Hr"]))

lad = R["ladder_2035"]
names35 = ["LadA", "LadB", "LadC", "LadD", "LadE", "LadF"]
for (lab, v), nm in zip(lad, names35):
    put(nm, f"{v:.1f}")
for i, nm in enumerate(["LadBd", "LadCd", "LadDd", "LadEd", "LadFd"]):
    d = lad[i + 1][1] - lad[i][1]
    put(nm, ("$+$" if d >= 0 else "$-$") + f"{abs(d):.1f}")
lad5 = R["ladder_2050"]
for (lab, v), nm in zip(lad5, ["LfA", "LfB", "LfC", "LfD", "LfE"]):
    put(nm, th(v))
for i, nm in enumerate(["LfBd", "LfCd", "LfDd", "LfEd"]):
    d = lad5[i + 1][1] - lad5[i][1]
    put(nm, ("$+$" if d >= 0 else "$-$") + th(abs(d)))

ns = R["ref_no_secondary"]
put("NoSecQmax", units(ns["Qmax"])); put("NoSecStock", units(ns["stock2050"])); put("NoSecTWh", th(ns["twh2050"]))
put("NoSecTWhThirtyFive", f"{ns['twh2035']:.1f}")
po = R["ref_primary_only"]
put("PrimQmax", units(po["Qmax"])); put("PrimStock", units(po["stock2050"])); put("PrimTWh", th(po["twh2050"]))
put("PrimTWhThirtyFive", f"{po['twh2035']:.1f}"); put("PrimN", str(po["n"]))
nS = sum(1 for c in R["checkpoints"] if c["access"] == "S")
put("NSecondary", str(nS)); put("NCheckpoints", str(len(R["checkpoints"])))
pr = R["peak_reconcile"]
put("PeakAnnualAvg", f"{pr['annual_avg_gw']:.0f}"); put("PeakStockAvg", f"{pr['stock_basis_avg_gw']:.0f}")
put("LegacyPeakPresent", f"{pr['legacy_peak_cn_present_basis']:.2f}")
an = R["analogue"]
put("AnaTWhFifty", f"{an['twh2050']:.1f}"); put("AnaTWhThirtyFive", f"{an['twh2035']:.2f}")
put("AnaStockFifty", units(an["stock2050"]))
put("AnaRatio", th(ref["twh2050"] / an["twh2050"]))

for reading, ab in (("hard", "H"), ("soft", "S")):
    m = R["mc"][reading]
    for k_ in ("p5", "p25", "p50", "p75", "p95"):
        kk = {"p5": "Five", "p25": "TwentyFive", "p50": "Med", "p75": "SeventyFive", "p95": "NinetyFive"}[k_]
        put(f"MC{ab}Fifty{kk}", th(m["quant2050"][k_]))
        put(f"MC{ab}ThirtyFive{kk}", twh(m["quant2035"][k_]))
        put(f"MC{ab}Stock{kk}", units(m["quant_stock2050"][k_]))
        put(f"MC{ab}Total{kk}", th(m["quant_total2050"][k_]))
    put(f"MC{ab}Capped", f"{100*m['capped_share']:.1f}")
    for n, abn in NM.items():
        put(f"MC{ab}Pct{abn}", f"{m['pct_'+n]:.0f}")
put("SeedSpreadMed", f"{R['mc']['seed_spread_pct'][1]:.1f}")
put("SeedSpreadHi", f"{R['mc']['seed_spread_pct'][2]:.1f}")
put("SeedSpreadLo", f"{R['mc']['seed_spread_pct'][0]:.1f}")
put("Draws", th(R["meta"]["draws"]))
put("SobolBase", th(R["meta"]["sobol_base"]))
put("SobolEvals", th(R["sobol"]["2050"]["n_evals"]))
put("SeedMC", th(R["meta"]["seed_mc"]).replace("\\,", "\\,"))
for y, yy in (("2035", "ThirtyFive"), ("2050", "Fifty")):
    ind = R["sobol"][y]["indices"]
    for g, ab in (("Ramp rate", "Ramp"), ("Shipment ceiling", "Ceil"), ("Locomotion physics", "Loco"),
                  ("Duty cycle", "Duty"), ("Service life", "Life"), ("Near-term anchors", "Anchor"),
                  ("Loss chain", "Loss"), ("Use-case mix", "Mix"), ("Hardware learning", "Learn"),
                  ("Onboard compute", "Compute"), ("Battery and charger", "Batt"), ("Task composition", "Task")):
        put(f"Sob{ab}ST{yy}", f"{ind[g]['ST']:.3f}"); put(f"Sob{ab}SOne{yy}", f"{ind[g]['S1']:.3f}")
    put(f"SobInter{yy}", f"{R['sobol'][y]['interaction']:.2f}")
    phys = ["Locomotion physics", "Task composition", "Onboard compute", "Standby states", "Battery and charger",
            "Loss chain", "Hardware learning", "Duty cycle", "Use-case mix"]
    put(f"SobPhysST{yy}", f"{sum(ind[g]['ST'] for g in phys):.2f}")
rv = R["reverse"]
for r, ab in zip(rv, ("Ten", "Hundred", "Thousand", "FiveThousand")):
    put(f"Rev{ab}Q", units(r["Qmax"])); put(f"Rev{ab}Veh", f"{r['over_vehicles']:.2f}")
    put(f"Rev{ab}Stock", units(r["stock2050"]))
ec = R["economics"]["rows"]
def eco(C, H): return next(r for r in ec if r["capex"] == C and r["hours"] == H)
put("EcoElecShareMax", f"{100*max(r['elec_share'] for r in ec):.1f}")
put("EcoElecShareMin", f"{100*min(r['elec_share'] for r in ec):.1f}")
put("EcoPminThirtyKThreeSix", f"{eco(30000,3600)['p_min']:.2f}")
put("EcoPminHundredKTwoFour", f"{eco(100000,2400)['p_min']:.2f}")
put("EcoPminFifteenKSix", f"{eco(15000,6000)['p_min']:.2f}")
put("EcoPminTwoHundredKTwoFour", f"{eco(200000,2400)['p_min']:.2f}")
put("EcoElecCostThreeSix", f"{eco(30000,3600)['elec_cost']:.0f}")
put("EcoA", f"{R['economics']['A']:.3f}")
put("ParamsSha", R["provenance"]["params_sha"]); put("CoreSha", R["provenance"]["core_sha"])
put("VehiclesM", f"{R['vehicles_2025']/1e6:.1f}")
put("WorldThirty", th(33600)); put("WorldTwentyFive", th(28200))

with open(os.path.join(OUT, "numbers.tex"), "w") as fh:
    fh.write("% Generated by model/make_numbers.py from results.json -- do not edit.\n")
    for k_, v in sorted(M.items()):
        fh.write(f"\\newcommand{{\\{k_}}}{{{v}}}\n")

# ------------------------------------------------------------- tables
def scen_table():
    rows = []
    for n in ("constrained", "reference", "accelerated", "abundance"):
        s = SC[n]
        rows.append(f"{s['label']} & {th(s['Qmax']/1e6,1)} & {s['k']:.2f} & {s['q2035']/1e6:.1f} & {s['stock2035']/1e6:.1f} & "
                    f"{twh(s['twh2035'])} & {th(s['stock2050']/1e6)} & {th(s['kwh_per_ry2050'])} & {twh(s['twh2050'])} & {twh(s['offboard_twh2050'])} & {th(s['peak2050_sum'])} \\\\")
    return "\n".join(rows)


def cp_table():
    rows = []
    for c in R["checkpoints"]:
        if c["year"] > 2050: continue
        kind = "shipments" if c["kind"] == "q" else "installed"
        r_ = SC["reference"]["checkpoint_ratios"][c["id"]]
        fitted = {n: (c["id"] in SC[n]["fit_ratios"]) for n in SC}
        tag = ", ".join(SC[n]["label"][:3] for n in ("constrained", "reference", "accelerated", "abundance") if fitted[n])
        val = units(c["value"]).replace("~", " ")
        rows.append(f"{c['source']} & {c['year']} & {kind} & {val} & {c['cls']} & {c['access']} & {tag or '--'} & {r_:.2f} \\\\")
    return "\n".join(rows)


def param_table():
    order = list(P.keys())
    rows = []
    def f(v):
        if abs(v) >= 1e6: return f"{v/1e6:g}\\,M"
        if abs(v) >= 1000: return th(v)
        return f"{v:g}"
    labels = {"SR0": "Specific resistance, 2025", "mass": "Robot mass (kg)", "speed": "Walking speed (m\\,s$^{-1}$)",
              "kM": "Manipulation ratio $\\kappa_M$", "kS": "Static-hold ratio $\\kappa_S$", "tau": "Thermal overhead $\\tau$",
              "Pc0": "Onboard compute, 2025 (kW)", "Pr": "Connected-ready power (kW)", "Ps": "Deep-sleep power (kW)",
              "Pch": "Charger rating (kW)", "eta_ch": "Charger efficiency", "eta_pk": "Pack round-trip efficiency",
              "dock": "Dock auxiliary", "site": "Site distribution", "rSR": "SR 2050 / SR 2025", "rPc": "Compute 2050 / 2025",
              "rH": "Active hours 2050 / 2025", "hh50": "Household share of 2050 deliveries", "q25": "2025 deliveries (units)",
              "q26": "2026 deliveries (units)", "Qmax": "Shipment ceiling $Q_{\\max}$ (units/yr)", "k": "Ramp rate $k$ (yr$^{-1}$)",
              "L": "Median service life (yr)", "f": "In-service fraction", "w": "Commissioning weight $w$",
              "inf_kw": "Offboard inference allocation (kW)", "inf_duty": "Offboard duty fraction", "pue": "Facility PUE"}
    for k_ in order:
        p = P[k_]
        anc = p["anchor"].replace("%", "\\%").replace("~", "")
        rows.append(f"{labels[k_]} & {f(p['lo'])} & {f(p['c'])} & {f(p['hi'])} & {p['cls']} & {p['grp']} & {anc} \\\\")
    return "\n".join(rows)


def sobol_table():
    groups = sorted(R["sobol"]["2050"]["indices"], key=lambda g: -R["sobol"]["2050"]["indices"][g]["ST"])
    rows = []
    for g in groups:
        a = R["sobol"]["2035"]["indices"][g]; b = R["sobol"]["2050"]["indices"][g]
        rows.append(f"{g} & {max(a['S1'],0):.3f} & {a['ST']:.3f} & {max(b['S1'],0):.3f} & {b['ST']:.3f} \\\\")
    rows.append("\\midrule")
    rows.append(f"Interaction share $1-\\sum S_1$ & \\multicolumn{{2}}{{c}}{{{R['sobol']['2035']['interaction']:.2f}}} & \\multicolumn{{2}}{{c}}{{{R['sobol']['2050']['interaction']:.2f}}} \\\\")
    return "\n".join(rows)


def econ_table():
    rows = []
    for C in (15000, 30000, 50000, 100000, 200000):
        r = [next(x for x in ec if x["capex"] == C and x["hours"] == H) for H in (2400, 3600, 6000)]
        rows.append(f"{th(C)} & {r[0]['p_min']:.2f} & {r[1]['p_min']:.2f} & {r[2]['p_min']:.2f} & {100*r[1]['elec_share']:.1f} \\\\")
    return "\n".join(rows)


def reverse_table():
    rows = []
    for r in rv:
        rows.append(f"{th(r['target'])} & {th(r['Qmax']/1e6, 1)} & {r['over_vehicles']:.2f} & {th(r['stock2050']/1e6)} \\\\")
    return "\n".join(rows)


for nm, fn in (("tab_scenarios", scen_table), ("tab_checkpoints", cp_table), ("tab_params", param_table),
               ("tab_sobol", sobol_table), ("tab_econ", econ_table), ("tab_reverse", reverse_table)):
    with open(os.path.join(OUT, nm + ".tex"), "w") as fh:
        fh.write(fn() + "\n")
print(len(M), "macros written")
