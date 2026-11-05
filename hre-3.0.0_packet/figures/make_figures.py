"""Generate every figure from model/outputs/results.json and series.json.

No figure contains a hand-entered model number.  Palette: scenarios are a
magnitude ordering and use a single-hue ordinal ramp (validated, --ordinal);
operating profiles use the first three categorical slots (validated all-pairs).
"""
import json, os, sys
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT, "figures", "out")
os.makedirs(OUTD, exist_ok=True)
R = json.load(open(os.path.join(ROOT, "model", "outputs", "results.json")))
S = json.load(open(os.path.join(ROOT, "model", "outputs", "series.json")))
sys.path.insert(0, os.path.join(ROOT, "model"))

# ---------------------------------------------------------------- style
for f in fm.findSystemFonts():
    if "Inter" in os.path.basename(f) and "Display" not in f:
        fm.fontManager.addfont(f)
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
RAMP = {"constrained": "#86b6ef", "reference": "#1c5cab", "accelerated": "#3987e5", "abundance": "#0d366b"}
# ordinal by magnitude: constrained < reference < accelerated < abundance
RAMP = {"constrained": "#86b6ef", "reference": "#3987e5", "accelerated": "#1c5cab", "abundance": "#0d366b"}
CAT = {"factory": "#2a78d6", "warehouse": "#eb6834", "household": "#1baf7a"}
ORANGE = "#eb6834"
LABEL = {"constrained": "Constrained", "reference": "Reference", "accelerated": "Accelerated", "abundance": "Abundance"}
ORDER = ["constrained", "reference", "accelerated", "abundance"]

mpl.rcParams.update({
    "font.family": "Inter", "font.size": 8.2, "axes.titlesize": 8.6, "axes.labelsize": 8.2,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK2, "axes.titleweight": "semibold",
    "axes.titlecolor": INK, "axes.titlelocation": "left", "axes.titlepad": 8,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 3, "ytick.major.size": 3,
    "xtick.minor.size": 1.5, "ytick.minor.size": 1.5, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "legend.fontsize": 7.6, "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
    "pdf.fonttype": 42, "lines.solid_capstyle": "round",
})
W = 6.6  # full text width, inches


def fmt_num(v, _=None):
    if v >= 1e9: return f"{v/1e9:g} bn"
    if v >= 1e6: return f"{v/1e6:g} M"
    if v >= 1e3: return f"{v/1e3:g} k"
    return f"{v:g}"


def fmt_twh(v, _=None):
    return f"{v:,.0f}" if v >= 1 else f"{v:g}"


def logy(ax, formatter=fmt_num):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(FuncFormatter(formatter))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="y"); ax.grid(False, axis="x")


def save(fig, name):
    fig.savefig(os.path.join(OUTD, name + ".pdf"))
    fig.savefig(os.path.join(OUTD, name + ".png"), dpi=200)
    plt.close(fig)


def end_label(ax, x, y, text, color, dy=0, weight="normal"):
    ax.annotate(text, (x, y), xytext=(4, dy), textcoords="offset points", va="center",
                fontsize=7.6, color=INK, fontweight=weight)


def spread_labels(ax, items, x, min_gap_pt=9.5, fontsize=7.4, color=INK, xoff=4):
    """Direct end-labels with vertical de-collision, in axes-fraction space (dpi independent).
    items: list of (y, text, weight, color)."""
    fig = ax.figure
    to_ax = lambda xx, yy: ax.transAxes.inverted().transform(ax.transData.transform((xx, yy)))
    h_pt = ax.get_position().height * fig.get_figheight() * 72.0
    w_pt = ax.get_position().width * fig.get_figwidth() * 72.0
    gap = min_gap_pt / h_pt
    pts = sorted([(to_ax(x, y)[1], t, w, c) for y, t, w, c in items], key=lambda p: p[0])
    ys = [p[0] for p in pts]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < gap:
            ys[i] = ys[i - 1] + gap
    x0 = to_ax(x, 1)[0]
    for (y0, t, w, c), y1 in zip(pts, ys):
        ax.annotate(t, xy=(x0, y0), xycoords="axes fraction", xytext=(x0 + xoff / w_pt, y1),
                    textcoords="axes fraction", va="center", fontsize=fontsize, color=c, fontweight=w,
                    annotation_clip=False)


yrs = np.array(S["reference"]["years"])
cp = R["checkpoints"]
VEH = R["vehicles_2025"]


# ===================================================== Fig 1: trajectories vs evidence
def fig_trajectories():
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.05))
    for ax, key, kind, title in ((axs[0], "q", "q", "Annual deliveries"), (axs[1], "stock", "S", "Installed fleet, year end")):
        for n in ORDER:
            lw = 2.0 if n == "reference" else 1.4
            ax.plot(yrs, S[n][key], color=RAMP[n], lw=lw, zorder=3)
        ax.plot(yrs, S["analogue"][key], color=MUTED, lw=1.0, ls=(0, (3, 2)), zorder=2)
        for c in cp:
            if c["kind"] != kind: continue
            mk = "D" if c["cls"] == "V" else "o"
            ax.scatter(c["year"], c["value"], s=22, marker=mk, facecolor=SURF, edgecolor=INK, lw=0.9, zorder=5)
        logy(ax); ax.set_xlim(2024.5, 2050.5); ax.set_title(title)
        ax.set_xticks([2025, 2030, 2035, 2040, 2045, 2050])
    axs[0].axhline(VEH, color=ORANGE, lw=0.9, zorder=1)

    axs[0].scatter(2025, 7000, s=24, marker="o", color=INK, zorder=6)
    axs[0].annotate("IFR full-size sales, 2025", (2025, 7000), xytext=(6, -9), textcoords="offset points", fontsize=7, color=INK2)
    axs[0].set_ylim(2e3, 2e9); axs[1].set_ylim(5e3, 1e10)
    axs[0].set_ylabel("Units (log scale)")
    fig.subplots_adjust(wspace=0.56, bottom=0.17)
    for ax, key in ((axs[0], "q"), (axs[1], "stock")):
        items = [(S[n][key][-1], LABEL[n], "semibold" if n == "reference" else "normal", INK) for n in ORDER]
        items.append((S["analogue"][key][-1], "IR analogue", "normal", INK2))
        spread_labels(ax, items, 2050, fontsize=7.2)
    h1 = axs[1].scatter([], [], s=22, marker="o", facecolor=SURF, edgecolor=INK, lw=0.9, label="Institutional forecast")
    h2 = axs[1].scatter([], [], s=22, marker="D", facecolor=SURF, edgecolor=INK, lw=0.9, label="Manufacturer statement")
    h3 = axs[0].scatter([], [], s=22, marker="o", color=INK, label="Reported sales")
    h4, = axs[0].plot([], [], color=ORANGE, lw=0.9, label="World vehicle production, 2025")
    fig.legend(handles=[h3, h1, h2, h4], loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.04))
    save(fig, "fig01_trajectories")


# ============================================================ Fig 2: unit & feasibility
def fig_unit():
    import core, scenarios as SC
    from params import central
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.85), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    u25, u50 = R["unit_detail_2025"], R["unit_2050_ref"]
    profs = ["factory", "warehouse", "household"]
    for i, pr in enumerate(profs):
        a, b = u25[pr]["kwh"], u50[pr]["kwh"]
        ax.plot([a, b], [i, i], color=AXIS, lw=2.2, zorder=1)
        ax.scatter(a, i, s=36, facecolor=SURF, edgecolor=CAT[pr], lw=1.6, zorder=3)
        ax.scatter(b, i, s=36, color=CAT[pr], zorder=3)
        ax.annotate(f"{a:,.0f}", (a, i), xytext=(0, -11), textcoords="offset points", ha="center", fontsize=7, color=INK2)
        ax.annotate(f"{b:,.0f}", (b, i), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7, color=INK)
    ax.set_yticks(range(3)); ax.set_yticklabels([p.capitalize() for p in profs])
    ax.set_ylim(-0.6, 2.9); ax.invert_yaxis(); ax.set_xlim(1000, 2600)
    ax.grid(True, axis="x"); ax.grid(False, axis="y")
    ax.set_xlabel("Grid-side kWh per robot-year"); ax.set_title("Unit energy, 2025 machine to 2050 reference")
    ax.scatter([], [], s=30, facecolor=SURF, edgecolor=INK, label="2025"); ax.scatter([], [], s=30, color=INK, label="2050 reference")
    ax.legend(loc="lower right", handletextpad=0.2)
    # feasibility frontier
    ax = axs[1]
    Pa = np.linspace(0.05, 3.0, 300)
    eta = 0.92 * 0.95
    for pch, ls in ((1, (0, (1, 1.5))), (2, "-"), (6, (0, (4, 2)))):
        H = 8760 * pch * eta / (Pa + pch * eta)
        ax.plot(Pa, H / 365, color=INK2, lw=1.0, ls=ls)
        ax.annotate(f"{pch} kW charger", (Pa[-1], H[-1] / 365), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=7, color=INK2, annotation_clip=False)
    pts = [("2025 factory", u25["factory"]["Pa"], 2400 / 365, CAT["factory"], "o", SURF),
           ("2050 reference", u50["factory"]["Pa"], u50["factory"]["H"] / 365, CAT["factory"], "o", None)]
    pab = SC.params_for("abundance")
    pa_ab = float(core.active_power(pab, "factory", 2050)[0])
    pts.append(("2050 Abundance", pa_ab, 2400 * 2.5 / 365, INK, "D", None))
    for lab, x, y, c, m, fc in pts:
        ax.scatter(x, y, s=34, marker=m, color=c if fc is None else None, facecolor=fc if fc else c, edgecolor=c, lw=1.4, zorder=4)
        ax.annotate(lab, (x, y), xytext=(6, -2), textcoords="offset points", fontsize=7, color=INK)
    ax.axhline(24, color=AXIS, lw=0.6)
    ax.set_xlim(0, 3.0); ax.set_ylim(0, 25)
    ax.set_xlabel("Active power (kW)"); ax.set_ylabel("Feasible active hours per day")
    ax.set_title("Charging occupies calendar time")
    ax.grid(True); fig.subplots_adjust(wspace=0.42)
    save(fig, "fig02_unit")


# ========================================================= Fig 3: annual electricity
def fig_energy():
    fig, ax = plt.subplots(figsize=(W, 3.4))
    fan = R["mc"]["fan"]
    ax.fill_between(yrs, fan["p5"], fan["p95"], color="#cde2fb", lw=0, zorder=1, label="Bounds experiment, 5–95 %")
    ax.fill_between(yrs, fan["p25"], fan["p75"], color="#9ec5f4", lw=0, zorder=1, label="25–75 %")
    for n in ORDER:
        ax.plot(yrs, S[n]["twh"], color=RAMP[n], lw=2.2 if n == "reference" else 1.5, zorder=3)
    ax.plot(yrs, S["analogue"]["twh"], color=MUTED, lw=1.0, ls=(0, (3, 2)), zorder=2)
    for lab, val in (("Finland, total consumption 2024", 83.0), ("Global data centres 2030, IEA", 950.0)):
        ax.axhline(val, color=ORANGE, lw=0.8, zorder=2)
        ax.text(2025.3, val * 1.13, lab, fontsize=7.0, color=INK2, bbox=dict(facecolor=SURF, edgecolor="none", pad=0.6), zorder=6)
    ax.scatter(2035, R["legacy_2035"]["twh"], marker="o", s=26, facecolor=SURF, edgecolor=INK, lw=1, zorder=5)
    ax.annotate("hre-2.0.0, 2035", (2035, R["legacy_2035"]["twh"]), xytext=(6, -8), textcoords="offset points", fontsize=7, color=INK2)
    logy(ax, fmt_twh); ax.set_ylim(0.01, 2e4); ax.set_xlim(2025, 2050)
    ax.set_xticks([2025, 2030, 2035, 2040, 2045, 2050])
    ax.set_ylabel("Grid-side electricity (TWh per year, log scale)")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.12))
    items = [(S[n]["twh"][-1], f"{LABEL[n]}  {S[n]['twh'][-1]:,.0f}", "semibold" if n == "reference" else "normal", INK) for n in ORDER]
    items.append((S["analogue"]["twh"][-1], f"Industrial-robot analogue  {S['analogue']['twh'][-1]:.1f}", "normal", INK2))
    spread_labels(ax, items, 2050)
    save(fig, "fig03_energy")


# =========================================== Fig 4: composition and 2050 attribution
def waterfall(ax, steps, title, fmt="{:,.0f}", unit="TWh", final="Result"):
    steps = list(steps) + [(final, steps[-1][1])]
    labels = [s[0] for s in steps]; vals = [s[1] for s in steps]
    xs = np.arange(len(vals))
    for i, v in enumerate(vals):
        if i == 0 or i == len(vals) - 1:
            ax.bar(i, v, width=0.62, color=INK2 if i == 0 else "#3987e5", zorder=3)
        else:
            d = v - vals[i - 1]
            ax.bar(i, d, bottom=vals[i - 1], width=0.62, color="#86b6ef" if d >= 0 else ORANGE, zorder=3)
            ax.plot([i - 1 + 0.31, i - 0.31], [vals[i - 1]] * 2, color=MUTED, lw=0.6, zorder=2)
        txt = fmt.format(v) if i in (0, len(vals) - 1) else (("+" if v - vals[i - 1] >= 0 else "−") + fmt.format(abs(v - vals[i - 1])))
        ax.annotate(txt, (i, max(v, vals[i - 1] if i else v)), xytext=(0, 3), textcoords="offset points",
                    ha="center", fontsize=7, color=INK)
    ax.set_xticks(xs); ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=7.2)
    ax.grid(True, axis="y"); ax.grid(False, axis="x"); ax.set_title(title)
    ax.set_ylabel(f"{unit} per year")


def fig_composition():
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.15), gridspec_kw=dict(width_ratios=[1.05, 1]))
    ax = axs[0]
    pt = S["reference"]["profile_twh"]
    base = np.zeros(len(yrs))
    for pr in ("factory", "warehouse", "household"):
        top = base + np.array(pt[pr])
        ax.fill_between(yrs, base, top, color=CAT[pr], lw=0, alpha=0.92, zorder=2, label=pr.capitalize())
        ax.plot(yrs, top, color=SURF, lw=1.0, zorder=3)
        base = top
    ax.set_xlim(2025, 2050); ax.set_ylim(0, base[-1] * 1.08)
    ax.set_xticks([2025, 2030, 2035, 2040, 2045, 2050]); ax.grid(True, axis="y"); ax.grid(False, axis="x")
    ax.set_ylabel("TWh per year"); ax.set_title("Reference case by operating profile")
    hs, ls = ax.get_legend_handles_labels()
    ax.legend(hs[::-1], ls[::-1], loc="upper left", handlelength=1.2)
    waterfall(axs[1], R["ladder_2050"], "2050 reference: what the machine changes", final="2050 reference")
    fig.subplots_adjust(wspace=0.32)
    save(fig, "fig04_composition")


def fig_ladder2035():
    fig, ax = plt.subplots(figsize=(W * 0.62, 2.9))
    waterfall(ax, R["ladder_2035"], "From hre-2.0.0 to the 2035 checkpoint", fmt="{:.1f}", final="This study, 2035")
    save(fig, "fig05_ladder2035")


# ================================================ Fig 6: distribution of the experiment
def fig_distribution():
    d = np.load(os.path.join(ROOT, "model", "outputs", "mc_samples.npz"))
    x = d["twh2050"]
    fig, ax = plt.subplots(figsize=(W, 2.7))
    bins = np.logspace(np.log10(30), np.log10(3e4), 70)
    h, e = np.histogram(x, bins=bins, density=False)
    c = np.sqrt(e[1:] * e[:-1])
    ax.fill_between(c, h / h.max(), color="#cde2fb", lw=0, step="mid", zorder=1)
    ax.step(c, h / h.max(), where="mid", color="#3987e5", lw=1.0, zorder=2)
    q = R["mc"]["hard"]["quant2050"]
    for k_, lab in (("p5", "p5"), ("p50", "median"), ("p95", "p95")):
        ax.axvline(q[k_], color=INK2, lw=0.6, ls=(0, (2, 2)), zorder=1)
        ax.text(q[k_], 1.07, f"{lab} {q[k_]:,.0f}", ha="center", fontsize=7, color=INK2,
                bbox=dict(facecolor=SURF, edgecolor="none", pad=0.8), zorder=5)
    ys = {"constrained": 0.22, "reference": 0.55, "accelerated": 0.38, "abundance": 0.22}
    for n in ORDER:
        v = R["scenarios"][n]["twh2050"]
        ax.scatter(v, ys[n], s=30, color=RAMP[n], edgecolor=SURF, lw=1, zorder=4)
        ax.annotate(f"{LABEL[n]} {v:,.0f}", (v, ys[n]), xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7.2, color=INK)
    ax.set_xscale("log"); ax.xaxis.set_major_formatter(FuncFormatter(fmt_twh))
    ax.set_ylim(0, 1.18); ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlim(30, 3e4); ax.grid(True, axis="x"); ax.grid(False, axis="y")
    ax.set_xlabel("2050 grid-side electricity (TWh per year, log scale)")
    save(fig, "fig06_distribution")


# ============================================================== Fig 7: Sobol
def fig_sobol():
    groups = list(R["sobol"]["2050"]["indices"].keys())
    st50 = {g: R["sobol"]["2050"]["indices"][g]["ST"] for g in groups}
    groups = sorted(groups, key=lambda g: -max(st50[g], R["sobol"]["2035"]["indices"][g]["ST"]))
    fig, axs = plt.subplots(1, 2, figsize=(W, 3.5), sharey=True)
    for ax, y, title in ((axs[0], "2035", "2035: how fast"), (axs[1], "2050", "2050: how large")):
        ind = R["sobol"][y]["indices"]
        ypos = np.arange(len(groups))
        S1 = np.array([max(ind[g]["S1"], 0) for g in groups]); ST = np.array([ind[g]["ST"] for g in groups])
        lo = np.array([ind[g]["ST_ci"][0] for g in groups]); hi = np.array([ind[g]["ST_ci"][1] for g in groups])
        ax.barh(ypos, ST, height=0.62, color="#b7d3f6", zorder=2, label="Total effect $S_T$")
        ax.barh(ypos, S1, height=0.62, color="#1c5cab", zorder=3, label="First order $S_1$")
        ax.errorbar(ST, ypos, xerr=[ST - lo, hi - ST], fmt="none", ecolor=INK2, elinewidth=0.6, capsize=1.5, zorder=4)
        for yy, v in zip(ypos, ST):
            if v >= 0.02:
                ax.annotate(f"{v:.2f}", (hi[list(ypos).index(yy)], yy), xytext=(4, 0), textcoords="offset points", va="center", fontsize=6.8, color=INK)
        ax.set_yticks(ypos); ax.set_yticklabels(groups, fontsize=7.4)
        ax.set_xlim(0, 1.0); ax.grid(True, axis="x"); ax.grid(False, axis="y"); ax.set_title(title)
        ax.set_xlabel("Share of output variance")
    axs[0].invert_yaxis()
    axs[1].legend(loc="lower right")
    fig.subplots_adjust(wspace=0.08)
    save(fig, "fig07_sobol")


# ======================================================= Fig 8: industrial feasibility
def fig_feasibility():
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.9), gridspec_kw=dict(width_ratios=[1.2, 1]))
    ax = axs[0]
    for n in ORDER:
        r = np.array(S[n]["q"]) / VEH
        ax.plot(yrs, r, color=RAMP[n], lw=2.0 if n == "reference" else 1.4)
    ax.axhline(1.0, color=ORANGE, lw=0.9)
    ax.text(2034, 0.78, "world vehicle production, 2025", fontsize=6.9, color=INK2, va="top",
            bbox=dict(facecolor=SURF, edgecolor="none", pad=0.6), zorder=6)
    ax.set_yscale("log"); ax.set_ylim(1e-4, 10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}×"))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(2025, 2050); ax.set_xticks([2025, 2030, 2035, 2040, 2045, 2050])
    ax.grid(True, axis="y"); ax.grid(False, axis="x")
    ax.set_title("Humanoid output relative to the car industry"); ax.set_ylabel("Annual deliveries ÷ 96.4 M")
    fig.subplots_adjust(wspace=0.62)
    spread_labels(ax, [(S[n]["q"][-1] / VEH, LABEL[n], "semibold" if n == "reference" else "normal", INK) for n in ORDER], 2050, fontsize=7.2)
    ax = axs[1]
    rv = R["reverse"]
    t = [r["target"] for r in rv]; qm = [r["Qmax"] for r in rv]
    ax.plot(t, qm, color="#3987e5", lw=1.4, marker="o", ms=4.5, mfc=SURF, mec="#3987e5", mew=1.4)
    for r in rv:
        ax.annotate(f"{r['Qmax']/1e6:,.0f} M/yr" if r["Qmax"] >= 1e6 else f"{r['Qmax']/1e3:,.0f} k/yr",
                    (r["target"], r["Qmax"]), xytext=(7, -3), textcoords="offset points", ha="left", va="top", fontsize=7, color=INK)
    ax.axhline(VEH, color=ORANGE, lw=0.9)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_twh)); ax.yaxis.set_major_formatter(FuncFormatter(fmt_num))
    ax.yaxis.set_minor_formatter(NullFormatter()); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(5, 2e4); ax.set_ylim(2e5, 2e9)
    ax.set_xlabel("2050 electricity target (TWh)"); ax.set_ylabel("Required shipment ceiling")
    ax.set_title("Reverse calculation"); ax.grid(True)
    save(fig, "fig08_feasibility")


# =========================================================== Fig 9: charging peaks
def fig_peaks():
    ref = R["scenarios"]["reference"]
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.7), gridspec_kw=dict(width_ratios=[1.15, 1]))
    ax = axs[0]
    h = np.arange(24)
    ax.plot(h, ref["peak_profile_2050_unmanaged"], color=INK, lw=1.6, drawstyle="steps-mid")
    ax.plot(h, ref["peak_profile_2050_managed"], color="#3987e5", lw=1.6, drawstyle="steps-mid")
    ax.annotate("unmanaged", (h[13], ref["peak_profile_2050_unmanaged"][13]), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=7, color=INK)
    ax.annotate("managed", (h[3], ref["peak_profile_2050_managed"][3]), xytext=(0, 6), textcoords="offset points", fontsize=7, color=INK)
    ax.set_xlim(0, 23); ax.set_xticks([0, 4, 8, 12, 16, 20]); ax.set_ylim(0, max(ref["peak_profile_2050_unmanaged"]) * 1.15)
    ax.set_xlabel("Hour (UTC)"); ax.set_ylabel("GW"); ax.set_title("Simultaneous world charging load, 2050 reference")
    ax = axs[1]
    regs = ["China", "Rest", "US", "EU+UK"]
    y = np.arange(len(regs))
    un = [ref["peak_regional_2050"][r] for r in regs]; ma = [ref["peak_regional_2050_managed"][r] for r in regs]
    ax.barh(y - 0.17, un, height=0.32, color=INK2, zorder=3, label="unmanaged")
    ax.barh(y + 0.17, ma, height=0.32, color="#3987e5", zorder=3, label="managed")
    for yy, a, b in zip(y, un, ma):
        ax.annotate(f"{a:.0f}", (a, yy - 0.17), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=INK)
        ax.annotate(f"{b:.0f}", (b, yy + 0.17), xytext=(3, 0), textcoords="offset points", va="center", fontsize=7, color=INK)
    ax.set_yticks(y); ax.set_yticklabels(regs); ax.invert_yaxis()
    ax.set_xlabel("Regional coincident peak (GW)"); ax.set_title("By accounting region")
    ax.grid(True, axis="x"); ax.grid(False, axis="y"); ax.legend(loc="lower right")
    ax.set_xlim(0, max(un) * 1.2)
    fig.subplots_adjust(wspace=0.4)
    save(fig, "fig09_peaks")


# ============================================================ Fig 10: comparators
def fig_comparators():
    rows = [(f"This study, {LABEL[n]}, 2050", R["scenarios"][n]["twh2050"], "model") for n in ORDER]
    rows += [(f"This study, Reference, 2035", R["scenarios"]["reference"]["twh2035"], "model")]
    rows += [(lab, v, "ext") for lab, v, cls in R["comparators"]]
    rows.append(("Industrial-robot analogue, 2050", R["analogue"]["twh2050"], "model2"))
    rows = sorted(rows, key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(W, 3.6))
    y = np.arange(len(rows))
    for yy, (lab, v, kind) in zip(y, rows):
        col = {"model": "#3987e5", "model2": "#86b6ef", "ext": AXIS}[kind]
        ax.barh(yy, v, height=0.62, color=col, zorder=3)
        ax.annotate(f"{v:,.0f}" if v >= 10 else f"{v:.1f}", (v, yy), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=7, color=INK)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.4)
    ax.set_xscale("log"); ax.xaxis.set_major_formatter(FuncFormatter(fmt_twh)); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(0.5, 2e5); ax.grid(True, axis="x"); ax.grid(False, axis="y")
    ax.set_xlabel("Annual electricity (TWh per year, log scale)")
    save(fig, "fig10_comparators")


# ============================================================== Fig 11: economics
def fig_economics():
    rows = R["economics"]["rows"]
    fig, ax = plt.subplots(figsize=(W * 0.62, 2.7))
    cols = {2400: "#86b6ef", 3600: "#3987e5", 6000: "#0d366b"}
    for H in (2400, 3600, 6000):
        rr = [r for r in rows if r["hours"] == H]
        x = [r["capex"] / 1e3 for r in rr]; yv = [r["p_min"] for r in rr]
        ax.plot(x, yv, color=cols[H], lw=1.5, marker="o", ms=3.5)
        ax.annotate(f"{H:,} h/yr", (x[-1], yv[-1]), xytext=(4, 0), textcoords="offset points", va="center",
                    fontsize=7.2, color=INK, annotation_clip=False)
    ax.axhline(1.0, color=ORANGE, lw=0.9)
    ax.text(3, 1.04, "one human-equivalent hour", fontsize=7, color=INK2)
    ax.set_xlim(0, 210); ax.set_ylim(0, None)
    ax.set_xlabel("Installed cost (thousand USD)"); ax.set_ylabel("Required output per robot hour")
    ax.set_title("Break-even useful work")
    save(fig, "fig11_economics")


if __name__ == "__main__":
    for fn in (fig_trajectories, fig_unit, fig_energy, fig_composition, fig_ladder2035, fig_distribution,
               fig_sobol, fig_feasibility, fig_peaks, fig_comparators, fig_economics):
        fn(); print("ok", fn.__name__)
