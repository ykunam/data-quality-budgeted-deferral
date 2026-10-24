# Cybersecurity alert triage under analyst capacity constraints

Reproducibility package for **Data-quality-aware human deferral for cybersecurity alert triage under analyst capacity constraints**, an author-review Short Communication for *Knowledge-Based Systems*. It is not accepted or submitted. The current editable source and 10-page PDF are `manuscript.tex` and `manuscript.pdf`.

## Findings and limits

Forty dataset/seed fits generate 21,120 aggregate rows. In the prespecified UNSW-NB15 outage comparison at 20% review capacity, automation-only quality information reduced simulated expected cost by 3.20% (absolute 0.006859; 95% conditional Monte Carlo interval 0.005608–0.008111). This is a randomization interval on fixed sampled corpora, not an interval for new networks or human analysts. The temporal CICIDS2017 outage comparison did not corroborate the benefit; confidence routing had lower cost there. Under severe degradation, mandatory overload leaves about 80% of flows unresolved. Null and adverse contrasts are retained.

Both reviewers are explicitly simulated. Completed flows are proxy alerts; no real analyst judgments, operational response times, regulatory compliance or production security effectiveness are established. Rules and costs are experimental assumptions. Dataset mirrors are byte-verified; original ground truth is not certified.

## Reproduce

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r budgeted_deferral/requirements.txt
cd budgeted_deferral
python -m dqd.cybersecurity fetch
python -m dqd.cybersecurity verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CYBER_PLAN_COMMIT=e16fe85e54cd28f77d1e2c4a291d5670661eb2fc python -m dqd.cybersecurity run --jobs 4
python -m dqd.cybersecurity analyze
python -m dqd.cybersecurity report
python -m unittest discover -s tests -v
cd ..
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
pdflatex -interaction=nonstopmode -halt-on-error manuscript.tex
```

Data acquisition uses pinned public mirrors because provider access was blocked or form-gated. The loader verifies mirror SHA256 values and excludes 288,602 unlabeled CIC mirror extras. Dataset provider terms still apply; raw corpora are ignored and not redistributed. Review source manifests before reuse. PyArrow 22.0.0 is included in the pinned requirements. Source-hash checks prevent resuming checkpoints produced by a different fitting source.

## Compact implementation and provenance

- `budgeted_deferral/dqd/cybersecurity.py`: acquisition, verification, fitting, routing, analysis and publication exports.
- `budgeted_deferral/tests/test_cybersecurity.py`: invariants and saved-output checks; the complete suite has 26 passing tests.
- `budgeted_deferral/results/cyber-*`: complete compressed aggregate grid, source/environment manifests, contrasts, machine-readable display cells, editable tables and reference verification.
- `budgeted_deferral/figs/cyber_fig1.pdf` and `cyber_fig2.pdf`: the two vector publication figures, with 450 dpi PNG previews.
- `submission-notes.md`: scientific/editorial audit and unresolved submission items.

The initial analysis plan/code was frozen at `cab4cdec3a1827a3a0a1c531f5c1b23eb84a560a` before model fitting. An audit found omitted interactions in the richer comparator. The correction was frozen at `e16fe85e54cd28f77d1e2c4a291d5670661eb2fc`, then **all 40 fits were rerun**. All 19,200 non-rich-comparator rows remained exactly identical. Subsequent code edits affect only `report()` layout/percentage precision; fitted calculations and inference are unchanged. The immutable corrected experimental snapshot is [f5bb01a155bda5ee4f62810ffdc5f39fd61b7e4d](https://github.com/ykunam/data-quality-budgeted-deferral/tree/f5bb01a155bda5ee4f62810ffdc5f39fd61b7e4d). The current branch additionally contains the final editorial package and presentation-only amendments.

The manuscript has exactly two figures, two editable tables, a 175-word abstract, seven keywords and 33 cited references. Twenty-two requested-publisher journal articles meet the checked **SJR 2025 best-quartile Q1** criterion. Necessary Q2 and unquartiled methodological/dataset sources remain explicitly identified; this is not an all-Q1 bibliography or a JCR/publication-year verification.

## Historical work

The pre-cybersecurity financial and image studies remain in git history and existing files for provenance. `dqd.revision`, the old root `experiment.py`, older figures/tables and old results are **not** the current cybersecurity manuscript's reproduction entry point. Their numbers and statistical assumptions must not be imported into this study. Existing code and licenses remain in place; no raw third-party dataset rights are granted by this repository.
