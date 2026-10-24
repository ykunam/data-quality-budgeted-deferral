# Cybersecurity alert triage extension

Design version 0.1, 24 October 2026. Base repository snapshot: `298d02838d3ed20cb56fd8863b915735db06d354`.

**Status: research design, not a completed experiment or a frozen statistical analysis plan.** The user selected cybersecurity alert triage as the extension. No cybersecurity datasets have been downloaded or analyzed in preparing this document; no cybersecurity results are claimed. Resolve the preflight items below and commit the complete analysis specification and implementation before examining validation outcomes.

## Working title and contribution

**Data-quality-aware human deferral for cybersecurity alert triage under analyst capacity constraints**

The intended contribution is a controlled investigation of when observable telemetry quality improves routing beyond predictive uncertainty, while explicit knowledge rules restrict automation and analysts have limited capacity. The contribution must be established through matched comparisons, not inferred from adding a cybersecurity dataset or changing the title. Retain AI governance and managerial decision-making in the abstract, keywords and interpretation of escalation rules, staffing and unresolved workload.

Primary question: **When does telemetry quality improve security-alert triage beyond predictive uncertainty under a fixed analyst review budget?**

Secondary questions: (1) Does any improvement persist when review counts and mandatory ordering are identical? (2) When do escalation rules exhaust analyst capacity, leaving unresolved threats despite policy compliance?

The directional hypothesis is conditional: quality information may reduce decision cost under observable degradation. A null or harmful effect remains publishable evidence about the method's operating conditions. Do not promise improved security, analyst effectiveness, legal compliance or real-world deployment before testing them.

## Position against existing work

- Jalalvand et al. already study learning to defer with human feedback for SOC alert prioritization on UNSW-NB15 and CICIDS2017 [1]. Do not claim the first application of learning to defer to cybersecurity. Compare the problem settings, reviewer assumptions, workload treatment and feedback access before claiming an unresolved gap.
- A recent dual-threshold conformal security-triage study is a required prior-art and comparator candidate [2]. Its accompanying repository is accessible, but the publisher full text returned an access/rate-limit error during this review. Complete the primary-paper and code review before implementing it or asserting that its assumptions exclude telemetry quality or capacity. A constrained adaptation must be labeled separately from the original method; capacity clipping does not automatically preserve conformal guarantees.
- Cost-sensitive learning to defer with workload constraints is also existing work [3]. The current repository does not contain a newly tuned DeCCaF implementation. Retain that limitation unless an audited comparison is actually added.

The gap to investigate is the **joint effect of observable telemetry degradation, explicit automation restrictions and binding analyst capacity**, with estimation and allocation effects separated. This is a candidate gap, not an exhaustive novelty finding.

## Data and validity

Use UNSW-NB15 as the first candidate benchmark and CICIDS2017 as an independent replication candidate [4,5]. Train dataset-specific models under one frozen protocol; independently training on two datasets is replication, not transfer of a detector across incompatible feature schemas.

UNSW-NB15 contains cyber-range traffic combining normal activity and generated attack behavior. CICIDS2017 is a controlled, scheduled traffic collection. Neither establishes performance in a contemporary production SOC. A network flow is a proxy triage unit; flow labels are not analyst judgments, incident severity, review time or organizational losses. State whether the experiment routes all flows or only alerts emitted by a detector, and use that population consistently in every denominator.

Prefer source-provider distributions. Record URLs, access dates, licensing terms, file hashes, row counts, label mappings and exclusions. Cite the provider's requested dataset papers; necessary dataset and statistical sources need not be Q1 journal articles. Do not redistribute data merely because source code is public.

Exclude labels, attack category, identifiers and fields unavailable at the stated decision time from predictor and router inputs. Attack category may be retained for retrospective subgroup reporting. Completed-flow features support post-flow triage; they do not establish early packet-level detection. Unknown categories and transformations must be learned using training data only. Rare but valid attack patterns must not be automatically described as corrupt telemetry.

Preserve the official UNSW train/test boundary if using its prepared files. Audit duplicates across that boundary before fitting, and document a deterministic leakage-removal rule. Do not pool and randomly repartition the official test set. Keep augmented copies, related flows and duplicate groups together. For CIC data, use acquisition/session/day metadata to design a temporal or grouped split before fitting; Monday is benign-only, so a naive Monday-only supervised training design is unsuitable. Exact source files, grouping keys and split maps remain preflight items.

## Telemetry quality and knowledge rules

Operationalize completeness as the missing fraction of required, available fields. Operationalize validity using documented schema constraints and training-only bounds, while distinguishing legitimate extreme traffic from malformed measurements. Investigate source-family outages, using label-independent corruption at the record or acquisition-block level. Predefine numeric and categorical field families and corruption intensities before outcome evaluation.

Do not reuse the original label-conditioned informative-missingness mechanism as the sole cybersecurity justification. Include an unmodified-data condition. If natural quality defects are absent, describe the quality experiments as synthetic stress tests on benchmark traffic.

Use staleness only if source acquisition and measurement timestamps genuinely identify data age. Replacing values with synthetic stale copies is a separately labeled simulation, not observed telemetry freshness. Without reliable timestamps, omit real staleness and response-time claims.

Represent each knowledge rule with its input fields, rationale, threshold provenance, triggered action and unresolved-case behavior. Schema-invalid telemetry can trigger an explicit experimental prohibition on auto-closure; broader escalation rules require an actual policy source or expert validation. Retain thresholds as stated experimental assumptions when such validation is unavailable. Measure both rule compliance and defect coverage, including false triggers on valid traffic.

Adversarial tampering is outside the initial extension. Random defects do not establish evasion resistance, poisoning resistance or robustness against an adaptive attacker.

## Decisions and matched comparisons

Maintain three routing actions: automate the detector's disposition, review, or hold pending review. Automation may classify a flow as benign or malicious; automatic escalation is a referral decision, not verified incident resolution. State whether downstream incident-response capacity is modeled. Hold means unresolved; it is not a correct classification, successful containment or safe dismissal.

Reuse the existing fixed-loss allocator where its assumptions apply. It is exact for estimated losses under unit review cost and mandatory priority, not for realized security harm. Adding heterogeneous investigation times or analyst assignments changes the optimization problem and invalidates reuse of its exactness proof without a new derivation. Preserve the original structural result: when mandatory cases exceed capacity and reviewer-loss ordering is fixed, changing only the automation-loss estimator cannot change routing.

Core comparisons should include probability-only two-head estimation; quality added only to the automation-loss head; quality in both heads; an observed-feature comparator; uncertainty routing; Chow-style cost-risk routing; and rules-only routing. Include the relevant SOC-specific deferral comparator after its assumptions and implementation are reviewed. Give learned estimators identical training access, search budgets and validation opportunities.

Run a matched arm with common mandatory flags, identical reviewer estimates and ordering, and identical review counts. This isolates quality's contribution to optional ranking. Retain a separate native-policy arm to evaluate the complete method. Do not confuse better estimation with additional review or weaker policy restrictions. Include a no-rule ablation with violations explicitly counted; do not describe prohibited automation as an unqualified benefit.

Proposed review budgets are 5%, 10% and 20%, with 20% as the candidate primary budget. These are design choices, not measured SOC staffing levels. Candidate initial cost ratios may reuse false-negative 5, false-positive 1, review 0.05 and hold 1.5 for continuity, but must be labeled illustrative and accompanied by a prespecified sensitivity grid. They are not empirically measured cyber losses.

No real analyst response data have been supplied. If unavailable, use clearly declared simulated reviewer scenarios shared across methods, including an imperfect reviewer and a reviewer whose errors correlate with detector errors. Do not define quality-aware reviewer error in a way that mechanically favors the quality-aware router. A perfect oracle can be an upper-bound scenario only. Never relabel recorded traffic truth as an observed analyst decision.

## Outcomes and statistical specification

Candidate primary contrast: quality in the automation-loss head versus probability-only estimation, on UNSW-NB15, under a prespecified moderate source-family outage, random review logging and 20% review capacity, with matched review counts and mandatory ordering. Freeze the exact outage, reviewer averaging, logging rate, cost vector, split design and inference procedure before fitting or scoring validation data. Reuse seeds 2–21 only as a reproducibility choice; random seeds are not independent organizations or deployments.

Report the primary contrast even if it is null or adverse. The existing 5.23% Bank Marketing reduction is historical finance-domain evidence and must never appear as a cybersecurity finding. Any practical-effect threshold must be chosen in advance; 1% relative cost reduction is a candidate continuity threshold, not an established security standard.

Report these outcomes with explicit denominators:

- Expected decision cost per incoming triage unit, including declared hold cost.
- Automatically closed attacks divided by all labeled attacks.
- Benign flows automatically escalated divided by all benign flows.
- Reviewer error, using its stated observation or simulation model.
- Held attacks divided by all attacks, and held cases divided by all arrivals.
- A sensitivity endpoint counting both incorrectly resolved and unresolved attacks as unmet, so favorable miss rates cannot be produced solely by holding more threats.
- Review utilization, automation coverage, rule violations and rule defect coverage.

Classification accuracy or F1 alone cannot establish operational triage benefit. Do not count a deferred or held attack as detected by a human who has not reviewed it. Report attack-family outcomes descriptively unless they belong to a prespecified multiplicity family; do not derive costs or real criticality from retrospective attack labels.

Select inference around the actual independent sampling unit. Repeatedly scoring the same official holdout does not create independent test samples. If session/time clustering is available, use a specified paired cluster/block procedure and document its target population; if unavailable, narrow claims and report conditional descriptive uncertainty. Do not automatically transplant the original corrected resampled t-test to a fixed-holdout design. Freeze the primary test, any secondary family, multiplicity correction, confidence intervals and minimum effective sample requirements before validation. All other comparisons remain exploratory.

Queue analysis requires trustworthy arrival timestamps, explicit service assumptions and an end-of-study rule for unresolved cases. Without them, report batch capacity and held workload rather than observed response time. A synthetic queue is a declared simulation; heterogeneous service or fatigue requires new evidence and modeling.

## Two figures and two tables

1. **Figure 1:** compact system and experimental design, showing telemetry, observable quality, knowledge rules, automate/review/hold actions, and the matched-estimator comparison. Draw deterministically using code.
2. **Figure 2:** panels showing cost versus analyst capacity and unresolved-attack burden versus capacity, across clean and degraded conditions, with uncertainty appropriate to the frozen design. Generate only from saved outputs.
3. **Table 1:** main held-out comparisons, including cost, attack auto-closure, benign auto-escalation, review utilization and unresolved attacks. Identify the single primary contrast and distinguish descriptive means from inferential findings.
4. **Table 2:** matched quality, rules and capacity ablations; report primary and declared secondary contrasts, intervals and corrected significance where justified, including every null result.

Use supplementary machine-readable outputs for full grids rather than introducing a third main figure. Recheck the current KBS author guide, final pagination and any portal requirements after the substantive rewrite. Adding cybersecurity removes the basis for carrying forward the previous manuscript's submission-readiness recommendation without a fresh audit.

## Compact implementation and release gates

Use the existing `budgeted_deferral` layout. Target one new `dqd/cybersecurity.py` entry point, one focused scientific-invariants test module, compact generated results and modifications to existing figure/table scripts. Avoid new notebooks, frameworks or dependency changes unless needed. The exact file count is a target, not a reason to omit provenance or required submission files.

Before evaluation, complete and commit:

- [ ] Source acquisition, licensing review, file hashes and schema availability.
- [ ] Flow-versus-alert population definition, decision-time feature inventory and leakage audit.
- [ ] Immutable train/calibration/gain/test membership and group/temporal keys.
- [ ] Exact quality-feature definitions, outage generator and rule dictionary.
- [ ] Reviewer and logging mechanisms, costs, sensitivity grid and all seeds.
- [ ] Primary estimand, matched comparison, inference unit and secondary multiplicity family.
- [ ] Audited SOC baseline specification, including any constrained adaptations.
- [ ] Tests for budget compliance, mandatory holds, no label leakage, split isolation, matched review counts and the overload structural null.
- [ ] Frozen implementation commit and an environment/data manifest before validation outcomes.

After evaluation, regenerate both figures and both tables from saved outputs; verify exported files; reconcile every reported number with the code; rewrite the abstract and conclusions to match actual findings; and conduct a new journal and reference audit. Actual analyst data, validated organizational costs, contemporary deployment and exhaustive originality checks remain limitations unless independently supplied and verified.

## Sources checked and follow-up reading

[1] F. Jalalvand, M. Baruwal Chhetri, S. Nepal, C. Paris, *Adaptive alert prioritisation in security operations centres via learning to defer with human feedback*, arXiv:2506.18462 (2025). https://doi.org/10.48550/arXiv.2506.18462. Primary abstract and full-text HTML consulted; not labeled a Q1 journal article.

[2] F. Şahin, N.S. Mert, *Dual-Threshold Conformal Deferral for Trustworthy Security Alert Triage*, Electronics 15 (2026) 4084. https://doi.org/10.3390/electronics15184084. Publisher index identifies the paper; publisher full text was inaccessible in this review. Author repository consulted: https://github.com/fsahin197650/conformal-deferral-soc. Full-text methodological verification and journal-quartile verification remain pending.

[3] J.V. Alves et al., *Cost-sensitive learning to defer to multiple experts with workload constraints*, Transactions on Machine Learning Research (2024). https://openreview.net/forum?id=TAvGZm2Rqb. Existing manuscript reference; full implementation comparison remains pending.

[4] UNSW, *The UNSW-NB15 Dataset*. https://research.unsw.edu.au/projects/unsw-nb15-dataset. Official description, prepared partition counts and academic-use terms checked. Its requested underlying references must be verified and cited when data are used.

[5] Canadian Institute for Cybersecurity, UNB, *Intrusion detection evaluation dataset CIC-IDS2017*. https://www.unb.ca/cic/datasets/ids-2017.html. Official collection schedule and feature description checked. Dataset paper: I. Sharafaldin, A.H. Lashkari, A.A. Ghorbani, *Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization*, ICISSP (2018), as identified by the provider; complete bibliographic metadata remains to be checked.

This source list grounds the design. It is not a completed reference audit or a substitute for claim-level citations in the rewritten manuscript.
