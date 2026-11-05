# hre-3.0.0 — Humanoid-robot electricity demand to 2050

Reproducibility packet for *Electricity demand from humanoid robots to 2050: calibrated diffusion scenarios with a global sensitivity analysis* (Merilehto, 5 November 2026). Extends hre-2.0.0 (doi:10.5281/zenodo.22538130).

## Layout
- `model/params.py` — every executable parameter with low/central/high, evidence class, group, anchor
- `model/core.py` — unit model (inherited), logistic deliveries, Weibull cohorts, exposure, energy, peaks, hre-2.0.0 reproduction
- `model/scenarios.py` — dated checkpoints, scenario narratives, log-least-squares calibration, industrial-robot analogue
- `model/uncertainty.py` — hard/soft bounds experiment, grouped Sobol (Saltelli/Jansen), Ishigami validation
- `model/run_all.py` — runs everything, writes `model/outputs/results.json`, `series.json`, `mc_samples.npz`
- `model/make_numbers.py` — writes `numbers.tex` (LaTeX macros) and `tab_*.tex` table bodies
- `model/tests/` — unit tests (hre-2.0.0 reproduction, anchors, monotonicity, Sobol estimator, macro provenance)
- `figures/make_figures.py` — all figures (PDF + PNG) from outputs
- `paper/` — manuscript source and bibliography

## Rerun (Windows PowerShell / conda)
```
conda create -n hre python=3.11 numpy scipy matplotlib -y; conda activate hre
python model/run_all.py --draws 50000 --sobol-n 8192
python model/make_numbers.py
python -m unittest discover -s model/tests
python figures/make_figures.py
cd paper; latexmk -pdf humanoid_electricity_2050.tex
```
Full run takes about 2 minutes on one core. Figures use the Inter font if installed (falls back otherwise).

## Publishing this release
The manuscript cites `https://github.com/juhanimerilehto/future2050/tree/v3.0.0`. From the unzipped packet folder (PowerShell):
```
git init; git add .; git commit -m "hre-3.0.0: humanoid electricity to 2050"
git remote add origin https://github.com/juhanimerilehto/future2050.git
git push origin HEAD:refs/heads/hre-3.0.0
git tag v3.0.0; git push origin v3.0.0
```
Then make the repository public (Settings > General > Danger Zone > Change visibility) and, optionally, create a GitHub Release from tag `v3.0.0` with Zenodo integration enabled to mint a DOI.
