# Prospective water task assurance revision

14 November 2026. Freeze this protocol on the research branch before running the
new intervention outcomes. This is a prospective computational extension after
inspection of the earlier study, not a registration of the original study.

## Research question and contribution

Can a policy-separable screen combining whole-task prediction with numerical
validity and demand-scenario checks improve acceptable isolation and recovery
completion relative to hold-only learned screening and nominal prediction?
The contribution is a reproducible model-based comparison with explicit
indeterminate outcomes and computation costs. Do not claim the first temporal
safety filter, a new formal-control theorem, an LLM capability gain, or field safety.

## Frozen design

- C-Town and EPA Net3. Retain original model bytes and hashes, PDD minimum 0 m,
  required 15 m, exponent 0.5; 300 s hydraulic/report/rule resolution. Run from
  each model's native initial conditions through the complete task in one
  trajectory. No telemetry-state reconstruction or restart between task phases.
- Per network: 24 training, 24 calibration and 24 test states. Integer start hours
  are evenly spaced over 72--120, 144--168 and 192--240 respectively. Base demand
  multipliers cycle 0.9, 1.0 and 1.1. These are temporally correlated benchmark
  states, not independent utility observations. No new test result is used to
  refit a model, change a cutoff or select a policy.
- Four initially open candidate assets per state, selected by rotating a fixed
  catalogue before observing intervention outcomes. C-Town catalogue is PU1--PU11;
  PU10/PU11 are excluded from training/calibration. Net3 catalogue is pumps 10/335
  and pipes 238/240/241/243/60/20; 60/20 are excluded from development. If fewer
  than four are active, retain all and record the smaller candidate count.
- Hold isolation for 6 h in C-Town and 3 h in Net3. Then request reopening once
  and restore native automation for 6 h. An overriding close rule has highest
  priority only during the hold. Native tank/other controls remain present.
  Report sampled realization separately; do not assert physical maintenance.
- Future positive demands change at task start by a hidden multiplicative factor.
  Train/calibration and half the test states cycle 0.9 and 1.1; the other half of
  test states cycle 0.75 and 1.25 (outside the forecast grid). Negative demands
  remain injections and are never rescaled by this future-demand perturbation.
- Forecast simulations use EPANET 2.2 with factors 0.85, 1.0 and 1.15. Evaluate
  actual outcomes with WNTR's Newton solver and the hidden future factor. Both
  engines share model equations: this is not physical independence. A separate
  actual-input EPANET run is retained for cross-solver sensitivity on every
  candidate. Reference trajectories use the same solver and future factor.
- Integrate positive-demand service shortage at left endpoints. Primary task harm
  remains incremental unmet fraction >=0.01 OR added tank-envelope duration >=1 h,
  relative to the matched no-action trajectory over the complete task. The hold
  endpoint uses the same definition over hold only. A recovery failure additionally
  means >0.001 incremental shortage during the last recovery hour OR a terminal
  tank-level deficit >5% of the tank's operating range relative to reference.
  These thresholds are illustrative research conventions, not operating standards.
- Numerical status is a separate field. Finite/full output, tank-bound error
  <=1e-4 m, continuity residual <=1e-5 m3/s, negative delivered demand at positive
  demand nodes <=1e-7 m3/s, and PDD residual <=max(1e-5, 1% of maximum requested
  node demand) define assessability. Preserve negative-pressure counts and all
  raw continuous metrics. Invalid or failed evaluations remain in denominators
  as indeterminate and cannot count as acceptable completion.

## Comparators and decision rules

Scope only, deny all, a connectivity/storage-budget rule, hold RF at 0.5, whole
task RF at 0.5, whole RF threshold selected on calibration only, nominal hold
prediction, nominal whole prediction, three-scenario whole prediction, and a
learned whole-task screen followed by three-scenario verification. RF uses 300
trees, balanced class weights, leaf size 5 and seed 20261115. Calibration searches
0--0.50 in steps of .01, requiring empirical harmful acceptance <=5% and maximizing
acceptable retention. No statistical risk guarantee follows from this selection.
Nominal/robust task prediction requires predicted realization and recovery, in
addition to endpoint limits. Full numerical checks are required by the robust
rule; the nominal comparator is also reported with the same checks in ablation.

Agents receive the same candidate list and at most four execution attempts.
Compare a catalogue-order controller and a whole-RF-ranked controller for every
test task and gate. Fit the ranking model on training only. Record proposals,
denials, selected assets, abstentions, task outcomes and verification workload.
The controllers are software agents, not LLMs. Earlier contaminated LLM traces
remain exploratory supplementary evidence and are excluded from primary claims.

## Analysis and audit

Report all candidate-level harmful acceptance, acceptable retention and
indeterminate counts; task-level completion and acceptable completion; reserved
assets and inside/outside forecast-grid strata. Use paired task comparisons and
descriptive circular block bootstrap intervals (block three states, 2000
replicates, seed 20261115). Do not count policy variants as independent samples.
All exclusions, errors, warning counts and protocol amendments remain visible.
Report wall-clock timings and forecast simulations; cached workload is not an
online latency benchmark. Re-evaluate a fixed 12-case sample per network at 60 s
after the primary run, selected without inspecting outcomes. Do not overwrite
300 s labels if sensitivity disagrees.

Investigate historical pressure/reconstruction differences separately. Record
whether disagreeing nodes belong to a component lacking an active head boundary;
do not declare physically undefined disconnected pressure a validated measurement.

No independently callable LLM API is available in this session. Provide a reset
context evaluation harness if useful, but never invent runs, seeds or API results.
Final novelty assessment must be a disclosed editorial rubric grounded in the
closest literature, with no acceptance probability or fabricated accuracy score.
