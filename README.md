# Electricity Demand from Humanoid Robots to 2050

[![Release](https://img.shields.io/badge/release-v3.0.0-1f6feb.svg)](https://github.com/juhanimerilehto/future2050/tree/v3.0.0)
[![Previous version DOI](https://img.shields.io/badge/hre--2.0.0-10.5281%2Fzenodo.22538130-lightgrey.svg)](https://doi.org/10.5281/zenodo.22538130)

**How much electricity could humanoid robots draw by 2050, and which assumptions decide it?**

This repository holds the paper and reproducibility packet for *Electricity demand from humanoid robots to 2050: calibrated diffusion scenarios with a global sensitivity analysis* (Merilehto, 5 November 2026). Release **hre-3.0.0** extends [hre-2.0.0](https://doi.org/10.5281/zenodo.22538130) with:

- **Calibrated diffusion:** logistic deliveries with Weibull fleet cohorts, calibrated by log-least-squares to dated checkpoints and an industrial-robot analogue.
- **Global sensitivity analysis:** grouped Sobol indices (Saltelli/Jansen), with an Ishigami validation of the estimator.
- **Hard and soft bounds:** a Monte Carlo bounds experiment over the parameter ranges.
- **Traceable numbers:** manuscript numbers and tables are written from the model outputs as LaTeX macros, and the tests check where they come from.

---

## Contents

| Item | What it is |
|---|---|
| [`Merilehto_2026_humanoid_electricity_2050.pdf`](Merilehto_2026_humanoid_electricity_2050.pdf) | The paper |
| [`hre-3.0.0_packet/`](hre-3.0.0_packet/) | Reproducibility packet: model, tests, figures, manuscript source |
| `hre-3.0.0_packet.zip` | The same packet as a single download |

Inside the packet:

```
hre-3.0.0_packet/
├── model/
│   ├── params.py         # every parameter: low/central/high, evidence class, group, anchor
│   ├── core.py           # unit model, logistic deliveries, Weibull cohorts, exposure, energy, peaks
│   ├── scenarios.py      # dated checkpoints, narratives, calibration, industrial-robot analogue
│   ├── uncertainty.py    # hard/soft bounds, grouped Sobol, Ishigami validation
│   ├── run_all.py        # runs everything → model/outputs/
│   ├── make_numbers.py   # LaTeX macros (numbers.tex) and table bodies
│   └── tests/            # hre-2.0.0 reproduction, anchors, monotonicity, Sobol estimator, macro provenance
├── figures/make_figures.py
└── paper/                # manuscript source and bibliography
```

## Reproduce

Windows PowerShell with conda, from inside `hre-3.0.0_packet/`:

```powershell
conda create -n hre python=3.11 numpy scipy matplotlib -y; conda activate hre
python model/run_all.py --draws 50000 --sobol-n 8192
python model/make_numbers.py
python -m unittest discover -s model/tests
python figures/make_figures.py
cd paper; latexmk -pdf humanoid_electricity_2050.tex
```

The full run takes about 2 minutes on one core. The figures use the Inter font if it is installed and fall back to the default otherwise.

## Versions

| Version | Where |
|---|---|
| **hre-3.0.0** (this release) | [`tree/v3.0.0`](https://github.com/juhanimerilehto/future2050/tree/v3.0.0), the version cited by the manuscript |
| hre-2.0.0 | [doi:10.5281/zenodo.22538130](https://doi.org/10.5281/zenodo.22538130) |

## Citation

```bibtex
@techreport{merilehto2026hre3,
  author      = {Merilehto, Juhani},
  title       = {Electricity demand from humanoid robots to 2050: calibrated diffusion
                 scenarios with a global sensitivity analysis},
  year        = {2026},
  month       = nov,
  institution = {GitHub},
  url         = {https://github.com/juhanimerilehto/future2050/tree/v3.0.0}
}
```

GitHub's **Cite this repository** button uses `CITATION.cff`.

The analysis and views are solely the author's and do not represent any employer or affiliated institution.
