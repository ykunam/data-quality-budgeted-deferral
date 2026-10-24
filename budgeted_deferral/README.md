# Governance-constrained budgeted human deferral (KBS revision)

Reproducibility package for the manuscript **"When Does Data Quality Help Human Deferral?
Knowledge-based systems for AI governance and managerial decision-making"**
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

## Legacy exploratory reproduction (earlier manuscript numbering)

For the current manuscript use **Reproducing the core revision** below.
The commands and old figure/table numbers in this section are historical.

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

The earlier study reports Python 3.13, scikit-learn 1.9.1, NumPy 2.5.3, pandas 3.0.5,
SciPy 1.18.1 and matplotlib 3.11.2. Those historical model fits were not independently
repeated in that reported environment. The core revision uses the separately
pinned actual environment in requirements.txt and revision-environment.json.
Seeds 2--21 are evaluation seeds; seeds 0--1 were used during original development.

## Results included

`results/*.csv.gz` hold every seed-level metric row (dataset, seed, protocol, reviewer, condition,
capacity, method, cost, review/hold/violation rates and per-condition diagnostics).
`results/tables/` and `results/numbers.json` hold the aggregates quoted in the manuscript.

## Scope and honesty notes

* Credit and Bank reviewers are simulated. The new, separate CIFAR-10H check
  reuses recorded public human choices; it does not recruit new participants.
* The L2D baselines are adaptations (shared automated classifier, cost weights, one-hidden-layer
  NumPy network); see the manuscript, Table 4.
* The proposed method is **not** uniformly best: Chow's cost-risk rule and confidence ranking are
  cheaper when review history is small. The package is designed to report those conditions, not hide them.

# Core revision: frozen prospective analysis plan (24 October 2026)

This section was committed before fetching the new validation datasets or running
the revision experiments. It is a timestamped analysis plan, not a registered
clinical protocol. The existing four credit datasets are development evidence;
Bank Marketing and CIFAR-10H have not previously been analyzed in this project.
The earlier PDF and experimental outputs remain recoverable in git history.

Primary question: when does quality information improve loss estimation beyond
model probabilities under mandatory review rules and scarce review capacity?
No new surrogate, universal superiority, or new propensity estimator is claimed.

## Fixed design

- Development: Default of Credit Card Clients, unchanged 45/15/20/20 grouped
  predictor/calibration/gain/test split, seeds 2--21. Prospective validation:
  UCI Bank Marketing `bank-full.csv` (45,211 rows); remove `duration`, which is
  unavailable before the call. Encode categorical values from predictor-training
  rows only and treat unseen/unknown categories as missing. Labels are historical
  subscription outcomes, not human review decisions. The application is a
  transfer stress test with illustrative costs, not a deployed credit policy.
- New data are not used for method selection. Holdout evaluation is run once
  after tests and code freezing. Per-seed inner validation is allowed only within
  the gain-fitting partition, with all augmented copies of an original record
  grouped together (80/20 inner fit/validation). No outcome-dependent tuning.
- Retain the original base predictor and calibration. Train loss regressors
  with max_leaf_nodes in {3, 7}, max_iter=100, learning_rate=.06, L2=5.
  Select each head by inner validation MSE; fit the selected configuration on
  the whole permitted gain partition. Single-head gain uses the same two-option
  search. Models never receive test labels or true reviewer error probabilities.
- Simulated reviewers: constant and AI-correlated (existing definitions).
  Test conditions: clean, informative missingness, stale records and severe shift.
  Train augmentation remains clean/missing/outliers/mixed. Costs FN=5, FP=1,
  review=.05, hold=1.5; capacities .10 and .20. Rules remain missing >=.5 OR
  invalid >=.25. Rules/costs are experimental policy assumptions, not regulations.
- Review logs: random (probability .4); uncertainty-prioritized and
  rule-prioritized (logistic selection, minimum .1, maximum .9, intercept chosen
  to give mean .4). All use shared uniforms and the same potential reviewer
  outcomes per seed/reviewer. Selection depends only on observed covariates.
  Compare unweighted fitting with inverse-propensity-weighted (IPW) fitting.
  Known logging probabilities are simulation metadata, never estimated from
  test outcomes. Label availability for all gain rows remains an assumption.
- Matched variants: probability-only two-head; quality only in automation head;
  quality in both heads; observed-feature two-head; single-head gain; Chow risk;
  confidence. Learned variants use the same allocator. Also evaluate a
  fill-budget arm that ranks optional cases without a positive-gain cutoff;
  and quality-aware full-model arms with gain-order overload and without rules.
  These distinguish estimation, optional admission, overload ordering and rules.
  Published CE/OvA baselines remain in the original exploratory grid; this
  revision does not relabel them as newly tuned state-of-the-art comparisons.

## Primary endpoint and declared inference

Primary contrast: on Bank Marketing, informative missingness, random logging,
20% capacity, unweighted fitting, mean over the two reviewer models, compare
quality-in-automation-only against probability-only, with identical reviewer
head/admission/allocator. Cost reduction is positive when quality helps.
Use the corrected resampled two-sided t-test, test/train ratio .2/.8, 95% CI.
There is one primary test (alpha .05); a practically useful effect additionally
requires >=1% relative cost reduction. Report failure to meet either criterion.
Twenty splits are dependent resamples, not 20 independent datasets.

Secondary family: IPW versus unweighted full quality two-head, per dataset and
logging policy, averaged over both reviewers and all four conditions at .20:
2 datasets x 3 policies = 6 tests, adjusted together by Holm. All other condition,
rule, allocation, budget and representation breakdowns are descriptive/exploratory;
do not promote them to confirmatory findings after seeing results. The original
pooled 8-test and quality-ablation 18-test families remain explicitly enumerated
in analysis.py; ambiguous earlier 7/9-test claims will be retired from the paper.

## Actual-human transfer check (separate, secondary)

If the original public CIFAR-10/CIFAR-10H files can be obtained, use all 10,000
images, binary animal (labels 2--7) versus vehicle (0,1,8,9), with the same
grouped split and seeds. Predictor input is 8x8 spatially averaged RGB (192
features), no pretrained model or human statistics. Individual human choices
come from original non-attention-check trials; sample one actual recorded choice
per gain image before applying each log mask. Evaluate against the empirical
binary human error rate per test image. No corruption is applied: humans saw
the original clean images. Evaluate .20 capacity, all three logging policies,
unweighted/IPW and the same fixed model search. This checks transfer of review-
loss estimation with genuine human choices, not human response to corrupted
credit records, expert finance performance, or the primary quality hypothesis.
No inferential success criterion is attached; report descriptively. If files are
unavailable, report this limitation rather than substituting simulated humans.

## Reproducibility and reporting

Pin the actual Python/package environment; save source/data hashes, selected
hyperparameters, logging counts, effective sample sizes, row-level paired
contrasts and policy diagnostics. Report all fixed cells, including unfavorable
ones. Keep exactly two manuscript figures and two manuscript tables; generate
them directly from saved outputs. A repeated command must recover the same
numbers. No claims of human-study approval, causal managerial effects, legal
compliance, or guaranteed journal acceptance are made.


## Reproducing the core revision

Use CPython 3.12.14. The exact direct and runtime dependency versions used are
pinned in requirements.txt. From budgeted_deferral/:

```bash
python -m pip install -r requirements.txt
python -m dqd.revision fetch
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -v
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m dqd.revision run --jobs 4
python -m dqd.revision analyze
python scripts/make_sc_tables.py
python scripts/fig_volume.py
python scripts/fig_dynamic.py
```

Compile manuscript.tex twice from the repository root. The original exploratory
360,000-row grid is retained; the new experiment refits models in the pinned
environment and writes revision.csv.gz. Temporary per-seed checkpoints are local
only and are not committed. Delete/checkpoint these intentionally when changing
experimental code; the source-hash guard rejects inconsistent reuse.

Primary inference is the single Bank/informative/random/20%-capacity contrast.
The secondary family has exactly six members, explicitly listed in
revision-summary.json. All other new contrasts are exploratory. Earlier prose
about unspecified seven-/nine-comparison families has been removed; the original
pooled-eight and exploratory-eighteen families remain reproducible in their
original scripts and outputs, without being used as new confirmatory claims.

### Data provenance, human judgments and licenses

- Bank Marketing: original UCI release, DOI 10.24432/C5K306, CC BY 4.0.
  The primary task is pre-call subscription prediction; duration is excluded.
  Bank reviewers are simulated and must not be described as observed staff.
- Default: original UCI release, DOI 10.24432/C55S3H.
- CIFAR-10: original Toronto Python archive, test_batch, original image order.
- CIFAR-10H: original jcpeterson/cifar-10h release. Cite Peterson et al.,
  ICCV 2019, Human uncertainty makes classification more robust. The dataset
  and metadata are licensed CC BY-NC-SA 4.0, as stated in its LICENSE.txt:
  https://github.com/jcpeterson/cifar-10h/blob/master/LICENSE.txt .
  Our changes map recorded ten-class choices to animal (2--7)/vehicle
  (0,1,8,9), exclude attention checks and aggregate or resample recorded choices.
  Derived human-data portions of the result files are distributed under
  CC BY-NC-SA 4.0; this exception does not relicense independent source code.
  Original images and participant-level data are downloaded locally and are not
  redistributed in this repository. Human-image results are descriptive transfer
  evidence, not a finance expert study or a new participant experiment.

Source hashes and the executed environment are in revision-environment.json.
Retain original provider licenses and attributions for downloaded data.

### Technical amendment before human analysis

The original CIFAR-10H CSV calls the image-index field
`cifar10_test_test_idx`, while its README documents `cifar10_test_set_idx`.
The adapter accepts either spelling and asserts that all recorded truth labels
match the original CIFAR-10 image indices. The first human run stopped before
producing results. No model, endpoint or analysis choice changed. All tabular
and human models were rerun after this adapter fix so the final manifest has
one executed source hash.

### Output integrity amendment

A zero-byte checkpoint and incomplete aggregate gzip were detected by readback
checks. The affected seed was recomputed; the verified aggregate contains all
102,960 unique cells. Serialization now compresses in memory, verifies bytes and
atomically replaces each checkpoint/output. No fitting or allocation calculation
changed. `fit_source_sha256` records the source used for the full model fits;
`source_sha256` records the published source after this I/O-only amendment.
A Bank seed-8 refit under the final writer reproduces all saved numeric values.
An interrupted incomplete checkpoint must be removed before resuming; integrity
checks fail loudly rather than silently treating it as valid.

Figure 1 also uses atomic PDF/PNG exports; tests check complete PDF headers and EOF markers. Final manuscript compilation and PDF rendering verify the exported assets.
