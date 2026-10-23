# Quality-aware budgeted deferral

Reproducibility package for **Data-Quality-Aware Knowledge-Based Systems for AI Governance and Managerial Decision-Making: Budgeted Human Deferral**.

**Status:** author-review research draft, not accepted or peer reviewed. All reviewer performance is simulated. This package does not demonstrate actual managerial behavior or legal compliance. The technical contribution is a compact quality-conditioned gain model combined with an explicit, auditable batch-routing policy; novelty and journal acceptance are not guaranteed.

Repository: https://github.com/ykunam/data-quality-budgeted-deferral (private author-review stage). Public archival deposit remains outstanding.

## Compact layout

Two Python files: `experiment.py` implements loading, split isolation, training, corruption, routing, evaluation and reporting; `test_experiment.py` checks the scientific invariants. `manuscript.tex` is the editable manuscript. `results/` contains the numerical evidence and the two figures. There is no web app, package scaffold, notebook, or GPU dependency.

## Reproduce

Use Python 3.12 (the recorded run uses Python 3.12; see the manifest for the exact patch version). CPU only.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell alternative: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest -v
python experiment.py --seeds 20 --start-seed 2 --cache ../data_cache --out results
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
```

An internet connection is needed once to download official UCI files. A cached run does not need network access. A smaller smoke run can use `--datasets german --seeds 1 --start-seed 22 --out smoke_results`; it does not reproduce the manuscript. Regenerate charts and editable tables without refitting using `python experiment.py --out results --report-only`. The manuscript uses the generated `results/tables.tex` directly.

## Protocol and interpretation

- Three UCI datasets: German numeric credit (1,000 rows; 24 released numeric predictors), Australian credit (690; 14), and credit-card default (30,000; 23; ID removed). Original categorical codes remain numeric as released. This is a benchmark choice, not a validated production encoding.
- Stratified feature-group-disjoint split: 45% predictor training, approximately 15% probability calibration, 20% gain fitting, 20% testing. Integer counts are in `manifest.json`. Feature bounds are fitted only on predictor-training rows. Feature-identical rows, including conflicting labels, are grouped before splitting and stratified by the group majority label. No identical feature vector crosses split roles. Exact per-seed counts are recorded.
- Calibration and gain fitting use four copies of their own rows: clean, missing, outliers, mixed. Shift severity is held out from fitting. Training the predictor on clean data is intentional. One predictor and one calibrator are shared by all routing methods per seed.
- Predictor: histogram gradient boosting, at most 120 iterations, 15 leaves, learning rate .07, L2 1. Logistic regression on predicted log odds calibrates probabilities. Decision threshold is 1/6 for costs FN=5 and FP=1. Other settings use the pinned scikit-learn defaults, including automatic early stopping.
- All gain regressors use identical hyperparameters: squared loss, at most 100 iterations, 7 leaves, learning rate .06, L2 5, leaf size max(20, .005 times the expanded gain-fit sample). Feature gain uses probability, implied cost risk, and robustly scaled observed features. Probability gain uses only the first two. Proposed gain uses the first two, the missing/out-of-range fractions, and their interactions with probability and the decision indicator. It has eight inputs, regardless of dataset width.
- Observable quality is missing fraction and fraction outside training 1st/99th-percentile bounds expanded by 10% of their range (range floor 1). Quality is not inferred from injected-corruption labels. Mandatory review: missing fraction >= .5 OR range-violation fraction >= .25. These illustrative policies are not regulatory requirements.
- Missingness is independently sampled per cell with a row-specific rate U(0,.55). Outlier-only uses U(0,.18); mixed uses missing U(0,.35), outlier U(0,.12); held-out stress uses missing U(.35,.75), outlier U(.08,.25). Outliers add +/- U(1.2,2.5) times the training range before missingness. This generic corruption can produce invalid category codes; it is a deliberate stress test, not a model of every business data defect.
- Simulated symmetric reviewer error: .10 constant; .05+.35*missing+.25*range violations capped at .40 quality-dependent; .25 adverse. Expected reviewer error costs are computed analytically using labels only for gain fitting and retrospective evaluation. Each review additionally costs .05. Held cases cost 1.5. No actual human labels are claimed.
- Capacities: 5%, 10%, 20%, 30%, rounded down per batch. Mandatory cases receive capacity first; excess mandatory cases are held, not automated. Optional learned gains must be positive. Heuristic baselines fill remaining capacity. Actual usage is reported alongside capacity.
- Primary comparison: equal-weight average across the three datasets and four non-clean conditions, quality-dependent reviewer, 20% capacity. All seeds 2..21 are retained, with no best-seed selection. Seeds 0 and 1 were developmental pilot runs; their results motivated compact quality features. Datasets and observations overlap across split seeds; this is not a preregistered or fully independent validation study.
- Figure 1: cost/capacity tradeoff. Figure 2: paired cost differences versus feature-aware gain. Error bars are descriptive split-seed t intervals; shaded bands in Figure 1 use 1.96 standard errors. They are **not** independent population-level confidence statements. Raw seed results, including negative results, are retained.
- `auto`, `no_rules` and `no_rules_p` are deliberately unconstrained diagnostics. Their cheaper cost must not be described as a governance-compliant improvement. Other heuristics are practical comparators, not claimed reproductions of the cited surrogate-loss algorithms.

## Evidence and integrity

`results/metrics.csv` stores every evaluated method/condition/seed, not only aggregates. `summary.json` stores paired summaries. `manifest.json` records source URLs, dataset SHA-256 checksums, dimensions, costs, software versions, command, experiment-code hash and elapsed time. `audit.csv` records label-free decisions for the default/mixed/quality/20%-capacity/seed-2 batch. The audit uses source row indices, not identity information. The two vector PDFs are the journal artwork; PNG versions are generated for convenient inspection and need not be committed.

`test_experiment.py` exhaustively checks small feasible allocation problems against the optimum; tests fail-closed overload, ties, zero/full capacity, negative gains, invalid inputs, corruption reproducibility, train-only quality bounds, asymmetric costs, holding penalties, and label-free routing interfaces.

Original data: [German](https://doi.org/10.24432/C5NC77), [Australian](https://doi.org/10.24432/C59012), [Default](https://doi.org/10.24432/C55S3H), distributed by UCI under CC BY 4.0. Cite the original dataset creators. Raw data are downloaded to the chosen cache and are not redistributed in this repository.

## Submission status

Read `submission-notes.md` for guide compliance and remaining author decisions. The manuscript must be reviewed and adopted by its human author; AI assistance is disclosed. Verify the final funding, conflict-of-interest, authorship and correspondence details. The private author-review repository is linked above. Add a public versioned release and archival deposit before journal submission. No journal submission has been performed.

## Reference-informed presentation

The author supplied Thota's UAV-planning manuscript as a writing reference. Its organization informed explicit rule definitions, matched comparisons, a 2-by-2 ablation, parameter sensitivity and failure-boundary reporting. Its wording, figures, tables, results and references were not reused as evidence for this study, and the supplied acceptance status was not independently verified. The factorial ablation crosses compact quality conditioning with the rule layer (`learned_p`, `proposed`, `no_rules_p`, `no_rules`). Sensitivity in `summary.json` varies the hold penalty for the same fixed routes; it is an accounting sensitivity, not policy retraining.
