# Governance-constrained budgeted human deferral (KBS revision)

Reproducibility package for the manuscript **"When Does Data Quality Help Human Deferral?
Governance-Constrained Review Allocation in Knowledge-Based Decision Systems"**
(Y. R. Kunam, revised author-review draft, October 2026).

This directory is self-contained: code, seed-level results, tables and figures.

## What is implemented

| Component | File |
|---|---|
| Data loading, group-disjoint stratified splits, quality measures (missing / out-of-range fractions) | `dqd/core.py` |
| Corruption families A (visible: missing, outliers, mixed, severe shift) and B (domain-valid: informative missingness, stale records, inconsistent codes, realistic mix) | `dqd/core.py` |
| Five reviewer models (constant, quality-coupled, feature-dependent, AI-correlated, adverse) | `dqd/core.py` |
| Two-head loss estimator, single-head gain, L2D-CE (Mozannar & Sontag 2020), L2D-OvA (Verma & Nalisnick 2022), differential triage (Raghu et al. 2019), Chow cost risk, confidence | `dqd/core.py`, `dqd/static.py` |
| Exact governance-constrained allocator (Proposition 1) | `dqd/core.py::allocate` |
| Multi-period backlog simulation (Proposition 2, managerial outcomes) | `dqd/dynamic.py` |
| Corrected resampled t-test (Nadeau & Bengio 2003), Holm | `dqd/stats.py` |

Labels are used only for fitting and retrospective evaluation, never for allocation.

## Reproduce

```bash
cd budgeted_deferral
python -m pip install -r requirements.txt
bash scripts/fetch_data.sh                 # four public datasets -> data/
python scripts/run_main.py logs            # main grid (Tables 5-10, Figs 2, 4)   ~9 min on 2 cores
python scripts/run_main.py oracle          # earlier optimistic protocol (Sect. 5.1)
python scripts/run_volume.py               # data-volume experiment (Fig. 3)       ~20 min
python scripts/run_dynamic.py              # 40-day backlog simulation (Table 13, Fig. 5)
python scripts/run_sens.py e3              # log completeness (Sect. 5.5)
python scripts/run_sens.py e4              # governance-rule alternatives (Table 11)
python scripts/run_sens.py e5              # cost re-optimisation (Table 12)
python scripts/analysis.py                 # writes results/tables/*.csv and results/numbers.json
python scripts/figs_main.py && python scripts/fig_volume.py && python scripts/fig_dynamic.py && python scripts/fig_framework.py
```

Expected data checksums (SHA-256):

```
2752b044394958ab6dd193a0b56ca0f0b3a2d8bc7cb8c008e35a5e84bbec02f8  german.data-numeric
3abe5af151afa50b999a9ba21cbc884e80d80a4050b716cf88b34a2e6ecb731c  australian.dat
dfdbc2b7cdf728a15b53e323cde6127995715dfa6b178bd3c1e3d9916d0367aa  hmeq.csv
bf15b02eb5a2c34f01f6d071083ecb7b8f4e803a4280a7ef497903d84c791c48  default.csv
```

Software used for the reported results: Python 3.13, scikit-learn 1.9.1, NumPy 2.5.3, pandas 3.0.5,
SciPy 1.18.1, matplotlib 3.11.2. All randomness is seeded; with the same versions the seed-level
results in `results/` are reproduced exactly. Seeds 2–21 are evaluation seeds; seeds 0–1 were used
during the original development.

## Results included

`results/*.csv.gz` hold every seed-level metric row (dataset, seed, protocol, reviewer, condition,
capacity, method, cost, review/hold/violation rates and per-condition diagnostics).
`results/tables/` and `results/numbers.json` hold the aggregates quoted in the manuscript.

## Scope and honesty notes

* Reviewer behaviour is simulated; no human participants or real review logs are involved.
* The L2D baselines are adaptations (shared automated classifier, cost weights, one-hidden-layer
  NumPy network); see the manuscript, Table 4.
* The proposed method is **not** uniformly best: Chow's cost-risk rule and confidence ranking are
  cheaper when review history is small. The package is designed to report those conditions, not hide them.
