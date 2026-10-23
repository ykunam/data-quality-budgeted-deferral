---
title: "Revision notes: response to the eight improvement suggestions"
---

All results in the revised manuscript come from a reimplemented pipeline (code in `budgeted_deferral/`, intended for ykunam/data-quality-budgeted-deferral). The original repository was not accessible from the working environment, so the earlier protocol was rebuilt from the manuscript and first checked against it (Section 5.1). It reproduced the earlier pattern: a small, non-significant quality-vs-feature difference, Default favouring quality, Australian reversing, and heuristics competitive. All numbers in the earlier draft have been replaced by numbers from the new runs.

| # | Suggestion | What changed | What the evidence showed |
|---|---|---|---|
| 1 | Demonstrated methodological novelty | Formal allocation problem; Proposition 1 (exact in both regimes, corrects the draft's overload ordering, proves hold-penalty invariance); Proposition 2 (backlog invariant to prioritisation); two-head estimator for incomplete logs | Propositions verified numerically (identical backlogs across orderings; hold-penalty change = 2.5 × hold rate). Overload-ordering correction matters little empirically (+0.18%, n.s.) |
| 2 | Published-method comparisons | Added L2D-CE (Mozannar & Sontag 2020), L2D-OvA (Verma & Nalisnick 2022), differential triage (Raghu et al. 2019), Chow's rule, with matched information, rules, costs, capacity | Proposed beats both L2D surrogates (L2D-CE 19/20 splits) but is 1.2% worse than Chow/confidence when pooled; beats everything 20/20 on the large Default dataset |
| 3 | Reviewer simulation may favour model | Five reviewer models (constant, quality-coupled, feature-dependent on hidden clean features, AI-correlated, adverse); training on single sampled decisions for 40% of records instead of expected losses | Coupling inflated the quality channel only slightly; the quality value comes mainly via the automation-loss head, not the reviewer head (Table 8) |
| 4 | Limited performance benefit; conditions where quality helps | New RQ; four prespecified hypotheses; quality-value map (condition × reviewer); head-specific mechanism ablation; data-volume experiment | Quality helps under informative missingness (+1.2 to +3.5% across all reviewers; +2.8%, 20/20 via automation head). Learned routing needs roughly 1,800+ gain records to beat Chow |
| 5 | Narrow data-quality and domain validation | Family B: informative missingness (MNAR), stale records, inconsistent valid codes, realistic mix; external HMEQ dataset with natural missingness | Invisible defects barely trigger rules or quality signals; on HMEQ, quality-aware beats prob-only (19/20) and Chow (19/20) but confidence is best |
| 6 | Governance rules lack validation | Four rule sets (none, lenient, main, strict); new appropriateness measure (defective records automated) | Strict rules cut automated defective records to 4.5% under visible shift at +111% cost, but miss ~75% under invisible defects |
| 7 | Managerial outcomes not measured | 40-day multi-period simulation with deterioration episode: workload, backlog, wait (mean/P95), SLA-2, override rate, cost per completed case, staffing | Staffing dominates; fluid rule predicts peak backlog almost exactly; FIFO halves tail wait but cuts 2-day SLA from 65% to 41% |
| 8 | Statistical and robustness evidence | Nadeau–Bengio corrected resampled t-test + Holm; win counts; full refit for each cost setting (FN:FP 2/5/10, review fee 0/0.05/0.2, hold 0.5/1.5/3) | Ranking stable across all cost settings; several effects honestly reported as inconclusive (H1, H3, H4) |

## Items the author must complete before submission

1. Review and adopt all content; confirm author declarations, funding and CRediT statement.
2. Merge the code pull request and create a versioned release with an archival DOI (e.g., Zenodo); update the Data availability statement with the DOI.
3. Check that Knowledge-Based Systems' current Guide for Authors limits (abstract length, highlights, article type, word count) are met. The revision is now a full-length article rather than a short communication.
4. Optionally seek organisational input on rule thresholds and cost values, and real reviewer logs; these are the most important remaining limitations.
5. Verify the two 2025–2026 arXiv references carried over from the earlier draft (DeSalvo et al.; Saketos et al.) against their current versions.
