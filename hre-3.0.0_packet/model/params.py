"""Executable parameter set for hre-3.0.0 (humanoid electricity to 2050).

Every parameter carries a central value, a declared low and high, an evidence
class and an anchor.  Evidence classes follow hre-2.0.0:
M measured, V vendor claim, S official statistic, F institutional forecast,
B external benchmark, A declared assumption of this study.

Unit-model parameters for 2025 hardware are carried over unchanged from
hre-2.0.0 (Merilehto 2026a, Table 4).  Parameters that only matter after 2035
(hardware learning, utilisation growth, household share, service life and the
shipment trajectory) are new in this version.
"""

P = {
    # ---- unit power, 2025 vintage (hre-2.0.0) -------------------------------
    "SR0":        dict(c=0.80,  lo=0.50,  hi=2.00,  cls="M/V", grp="Locomotion physics", anchor="Cassie 0.7; ASIMO 2.27"),
    "mass":       dict(c=60.0,  lo=45.0,  hi=75.0,  cls="V",   grp="Locomotion physics", anchor="G1 35 kg; Optimus 72.6 kg"),
    "speed":      dict(c=1.20,  lo=1.00,  hi=1.50,  cls="A",   grp="Locomotion physics", anchor="Kashiri et al. test speeds"),
    "kM":         dict(c=0.60,  lo=0.40,  hi=0.90,  cls="A",   grp="Task composition",   anchor="declared"),
    "kS":         dict(c=0.25,  lo=0.10,  hi=0.45,  cls="A",   grp="Task composition",   anchor="Optimus seated/walking"),
    "tau":        dict(c=0.12,  lo=0.05,  hi=0.25,  cls="A",   grp="Task composition",   anchor="F.03 active cooling"),
    "Pc0":        dict(c=0.060, lo=0.030, hi=0.150, cls="A",   grp="Onboard compute",    anchor="one inference SoC"),
    "Pr":         dict(c=0.100, lo=0.050, hi=0.180, cls="V",   grp="Standby states",     anchor="Optimus seated 100 W"),
    "Ps":         dict(c=0.015, lo=0.005, hi=0.030, cls="A",   grp="Standby states",     anchor="declared"),
    # ---- battery and charging (hre-2.0.0) ----------------------------------
    "Pch":        dict(c=2.0,   lo=1.0,   hi=6.0,   cls="V",   grp="Battery and charger", anchor="F.03 2 kW fast charge"),
    "eta_ch":     dict(c=0.92,  lo=0.85,  hi=0.96,  cls="M",   grp="Loss chain",          anchor="INL; NREL"),
    "eta_pk":     dict(c=0.95,  lo=0.90,  hi=0.98,  cls="A",   grp="Loss chain",          anchor="declared"),
    "dock":       dict(c=0.03,  lo=0.01,  hi=0.07,  cls="A",   grp="Loss chain",          anchor="declared"),
    "site":       dict(c=0.03,  lo=0.01,  hi=0.06,  cls="A",   grp="Loss chain",          anchor="declared"),
    # ---- evolution to 2050 (new) --------------------------------------------
    "rSR":        dict(c=0.75,  lo=0.50,  hi=1.00,  cls="A",   grp="Hardware learning",   anchor="Human walking SR 0.2"),
    "rPc":        dict(c=1.50,  lo=0.50,  hi=4.00,  cls="A",   grp="Onboard compute",     anchor="declared"),
    "rH":         dict(c=1.50,  lo=1.00,  hi=2.50,  cls="A",   grp="Duty cycle",          anchor="Multi-shift operation; charging limit"),
    "hh50":       dict(c=0.40,  lo=0.10,  hi=0.65,  cls="F/A", grp="Use-case mix",        anchor="Morgan Stanley about 8% (2050); BofA 62% (2060)"),
    # ---- fleet (new structure) ----------------------------------------------
    "q25":        dict(c=18000, lo=7000,  hi=30000, cls="S/F", grp="Near-term anchors",   anchor="IFR 7,000 full-size; BofA 20,000; Unitree 5,511"),
    "q26":        dict(c=60000, lo=45000, hi=90000, cls="M/F", grp="Near-term anchors",   anchor="IDC H1 2026 about 25,000; Goldman Sachs 75,000; BofA 90,000"),
    "Qmax":       dict(c=1.1e8, lo=1.0e7, hi=6.0e8, cls="A",   grp="Shipment ceiling",    anchor="World vehicle production 96.4 M (2025)"),
    "k":          dict(c=0.55,  lo=0.40,  hi=0.80,  cls="F/A", grp="Ramp rate",           anchor="Published 2030 range 0.5-1.2 M"),
    "L":          dict(c=8.0,   lo=5.0,   hi=12.0,  cls="A",   grp="Service life",        anchor="Morgan Stanley 6-year cycle; industrial robots 12+ yr"),
    "f":          dict(c=0.88,  lo=0.80,  hi=0.93,  cls="A",   grp="Fleet dynamics",      anchor="hre-2.0.0"),
    "w":          dict(c=0.50,  lo=0.35,  hi=0.65,  cls="A",   grp="Fleet dynamics",      anchor="0.50 = uniform commissioning"),
    # ---- offboard inference, reported separately (hre-2.0.0) ----------------
    "inf_kw":     dict(c=0.05,  lo=0.00,  hi=0.30,  cls="A",   grp="Offboard",            anchor="declared"),
    "inf_duty":   dict(c=0.30,  lo=0.10,  hi=1.00,  cls="A",   grp="Offboard",            anchor="declared"),
    "pue":        dict(c=1.20,  lo=1.10,  hi=1.60,  cls="B",   grp="Offboard",            anchor="NREL"),
}

# Fixed structural constants (not sampled)
WEIBULL_K = 3.0
Q2024 = 3000.0          # pre-2025 residual cohort (BofA 2024 shipments)
READY_FRAC = {"factory": 0.35, "warehouse": 0.35, "household": 0.65}
HOURS0 = {"factory": 2400.0, "warehouse": 2480.0, "household": 1095.0}
TASK = {  # locomotion, manipulation, static-hold shares of an active hour
    "factory":   (0.300, 0.560, 0.140),
    "warehouse": (0.505, 0.400, 0.095),
    "household": (0.300, 0.560, 0.140),
}
NONHH_SPLIT = {"factory": 0.60, "warehouse": 0.40}
HH0 = 0.05              # household share of 2025 deliveries
YEARS = list(range(2025, 2051))
AVAIL = 0.88            # availability fraction for peak analysis (hre-2.0.0 App. C)
REGIONS = {"China": 0.40, "US": 0.22, "EU+UK": 0.15, "Rest": 0.23}
REGIONS_CN = {"China": 0.70, "US": 0.11, "EU+UK": 0.08, "Rest": 0.11}
UTC_OFF = {"China": 8, "US": -6, "EU+UK": 1, "Rest": 3}
SHAPE_UNMANAGED = [0.55, 0.50, 0.45, 0.42, 0.40, 0.45, 0.62, 0.70, 0.55, 0.45, 0.42, 0.45,
                   0.58, 0.55, 0.50, 0.58, 0.88, 1.00, 0.98, 0.90, 0.80, 0.72, 0.66, 0.60]
SHAPE_MANAGED = [1.10, 1.15, 1.18, 1.18, 1.15, 1.10, 1.02, 0.98, 0.92, 0.88, 0.86, 0.88,
                 0.95, 0.94, 0.90, 0.92, 1.00, 1.05, 1.02, 0.98, 0.95, 0.98, 1.04, 1.08]


def central():
    return {k: v["c"] for k, v in P.items()}
