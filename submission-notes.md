# Editorial compliance and reproducibility audit

Editorial and reproducibility audit

Knowledge-Based Systems | Short Communication | 23 October 2026

Recommendation: MAJOR REVISIONS before submission. The manuscript is materially clearer and locally reproducible, but the evidence does not yet establish a strong methodological advance or real managerial effectiveness. Formatting corrections do not resolve the scientific and administrative blockers below.

Delivered revision

The edited manuscript is 10 pages, with exactly two figures and two editable tables. Double spacing now extends to captions, table text, and references. The editable LaTeX source and separate vector artwork are included in the updated compact project. The original uploaded PDF and all 16 original tracked files were preserved before editing. The requested private GitHub repository now holds the reviewed project.

Scientific and editorial improvements applied

• Clarified the gap as a fixed-batch integration and evaluation question; retained the distinction from selective prediction, learned deferral, training-query budgets, and queue control.

• Defined the asymmetric loss, expected reviewer loss and single review fee; specified quality denominators, training bounds, feature imputation/scaling/clipping, label coding, baseline scores and estimator defaults.

• Retained conditional allocation exactness only when mandatory demand is feasible, and separated overload holding guarantees from cost optimality.

• Explained the small, mixed routing gains, the competitive simple baselines, actual review usage and the cost of held cases.

• Added the simulator’s dependence on the proposed quality inputs as an explicit limitation. Reduced repetition and sharpened the managerial interpretation without changing experimental numbers.

Key unchanged evidence

| Primary comparison / quantity | Verified value |
| --- | --- |
| Quality-aware / feature-aware mean cost | 0.6055 / 0.6067 |
| Feature minus quality cost difference | 0.0012; descriptive interval [−0.0022, 0.0046] |
| Confidence / cost-risk mean cost | 0.6028 / 0.6051 |
| Proposed actual review / hold fractions | 19.85% / 11.80% across primary conditions |

Primary = equal weighting of three datasets and four non-clean conditions, quality-dependent simulated reviewer, 20% maximum capacity. Intervals describe overlapping repeated splits; they are not independent population inference.

1  Authority and reference-document analysis


The complete supplied official KBS guide (20 PDF pages; printed 23 October 2026) is the primary authority. The supplied Thota DOCX is an example of presentation only. No official manuscript-template source file was supplied. Its described acceptance status was not independently authenticated.

| Element | Official guide / editorial application | Accepted DOCX observation |
| --- | --- | --- |
| Article structure | Numbered sections; logical scientific sequence. No mandatory literal IMRaD heading set found. | Abstract; keywords; Introduction; Proposed framework; Experimental Design; Results and Discussion; Limitations; Conclusion; declarations; references. |
| Layout | Editable .tex or .doc/.docx. Word single column; LaTeX double column permitted. Elsevier LaTeX template encouraged, not mandatory (p.9). | Letter page, 0.75-inch margins; Normal style Times New Roman 12 pt; no explicit global double-spacing value in Normal style. |
| Mechanism and evidence | Explain model, objective, assumptions, comparisons and inferential limits. Applied to present code, not transferred from reference. | Explicit rule model and algorithm; matched baselines, ablation, tradeoff, sensitivity and limitations. |
| Tables and figures | Editable tables, numbered captions/citations, no vertical rules or shading; separate artwork (pp.11–12). | Five Word tables, including equation/algorithm constructs; three labeled research tables; one inline image. Counts are not journal limits. |
| End matter | Data statement; applicable author, funding, conflict and AI-use declarations; verified references. | Data Availability, Competing Interest, GenAI, Funding, CRediT and 35 references. |
| Originality | No transfer of reference wording, domain findings, data, figures or contributions. | UAV/quantum-inspired scenario is unrelated to this credit-benchmark study; none of its numerical evidence is used. |

Applied structure

Title and author details → abstract → six keywords → 1 Introduction → 2 Method → 3 Experimental protocol → 4 Results and discussion → 5 Limitations → 6 Conclusion → availability → pending author declarations → AI-use statement → references. The sequence preserves a focused Short Communication and the actual study design.

Verification boundary

Direct access to the live ScienceDirect guide returned HTTP 403. Official search indexing corroborated the Short Communication page limit, but the live submission portal was not inspected. This report applies the supplied guide and flags portal-only fields as unverified. It does not infer current requirements from the accepted paper.

Authoritative guide: https://www.sciencedirect.com/journal/knowledge-based-systems/publish/guide-for-authors

2  Journal compliance checklist: manuscript


PASS = checked in the revised files. PENDING = verified requirement with an unfinished item. NOT SPECIFIED = no such restriction found in the supplied guide; not a guarantee about the live portal. Sources refer to the printed guide’s page numbers.

| Requirement / authority | Status | Evidence and remaining action |
| --- | --- | --- |
| Scope: AI systems, decision support, data-driven optimization (p.2) | Scope match | Rule-conditioned deferral supports prediction and capacity-constrained decisions. Editorial significance remains uncertain; scope fit is not acceptance. |
| Short Communication: ≤10 double-line-spaced pages including figures/tables (p.3) | PASS | Final PDF: 10 pages total, including end matter and references. Double-spaced text/captions/references and table rows. Recheck after author declarations are finalized. |
| Separate word/reference/figure/table count limits | NOT SPECIFIED | No separate numerical limits located in the supplied guide. Exactly two figures and two tables meet the author’s requested count; that count is not attributed to KBS. |
| Editable submission source (p.9) | PASS | manuscript.tex and results/tables.tex included. PDF is the reading copy, not the only source. Separate figure PDFs are provided. |
| Title and author/correspondence details (p.10) | PENDING | Title retained. Name, affiliation, postal address and email present but require human confirmation before publication. |
| Abstract ≤250 words; 1–7 keywords (p.10) | PASS | 169 words under the recorded tokenization; six English keywords. Abstract is self-contained and has no citations. |
| Numbered section sequence (p.14) | PASS | Six numbered sections; all figures, tables and equations have labels and in-text references. |
| Editable mathematical notation (p.11) | PASS | Three numbered display equations plus inline definitions. Decision threshold, dimensions, costs, constraints and gain target cross-checked against implementation. |
| Table presentation (p.11) | PASS | Exactly two editable LaTeX tables; consecutive captions; no vertical rules or shading. Numeric precision and percentage denominators specified. |
| Figure presentation (pp.11–12) | PASS | Two separate vector PDFs with embedded TrueType fonts, sequential captions and citations; vector output has no raster DPI requirement. All final manuscript pages visually checked. |

Spacing correction

The original draft used single-spacing environments for tables and references and compact captions. These exceptions were removed or revised. The 10-page result therefore reflects the supplied double-line-spacing instruction more closely than the original nine-page reading copy.

3  Journal compliance checklist: submission materials


| Material / authority | Status | Verification or required action |
| --- | --- | --- |
| Highlights encouraged: 3–5 bullets, ≤85 characters each (p.10) | PASS | Separate editable highlights.txt: five bullets, 78 / 75 / 59 / 76 / 75 characters excluding bullet markers. Wording preserves negative comparisons. |
| Graphical abstract | NOT SPECIFIED | No graphical-abstract requirement located in the supplied KBS guide. No third image was added. Confirm whether the live portal requests one; generic Elsevier guidance does not establish a KBS requirement. |
| Research-data deposit, citation and linking: Option C (p.13) | PENDING | All generated metrics and software are in the package, but no appropriate public archival deposit/link is verified. Original UCI DOIs do not archive this study’s generated evidence. |
| Data availability statement (p.13) | PENDING | Transparent draft statement is present. Replace the missing code/archive wording with actual versioned links after deposit; do not claim an unavailable archive exists. |
| Funding declaration (pp.5–6) | PENDING | Actual funding and sponsor involvement have not been confirmed. No unsupported “no funding” assertion was inserted. |
| Competing interests / declarations tool (pp.5–6) | PENDING | Author must supply truthful details and produce the requested separate declaration document using Elsevier’s declarations tool. Not supplied or certified in this draft. |
| Author contributions and human responsibility (pp.14–15) | PENDING | Author must confirm actual contributions, affiliation, correspondence, institutional approval, originality and exclusive submission. AI is not an author. |
| AI-use disclosure and figure provenance (pp.6–7, 12) | Draft present | Actual assistance is disclosed; figures derive from executable analysis rather than generated artwork. Author review/adoption remains explicitly unconfirmed; finalize truthful declaration after review. |
| Supplementary / reproducibility materials (pp.12–13) | Available locally | Compact source/results ZIP contains 16 project files. Code, results, manifest and audit sample are present. Upload classification and public accessibility remain unverified. |
| Remote GitHub repository / code release | Private repo created | Owner ykunam and private visibility verified. Repository: github.com/ykunam/data-quality-budgeted-deferral. The compact reviewed project is uploaded; public release and archival identifier remain outstanding. |
| Submission-system fields / permissions (p.18) | UNVERIFIED | No journal submission performed. Live portal article-type selection, generated forms and author attestations must be checked at submission. |

No cover-letter, graphical-abstract, or reference-count requirement has been invented. Any submission-specific request shown by the portal takes precedence over absence from the supplied artifact.

4  Scientific and implementation consistency


Method and notation

The automated threshold 1/6 follows from false-negative cost 5 and false-positive cost 1. Automated loss is (1+4y) times the error indicator; simulated reviewer loss is (1+4y)e(q), plus the review fee 0.05 once. Holding incurs 1.5 per record. The manuscript now exposes these definitions and the service-first constraint that makes the feasible allocation argument valid.

Quality uses missing and out-of-bound fractions over all predictors. Bounds use training 1st/99th percentiles and a range floor of one. Feature-aware gain uses training-median imputation, centering/scaling and clipping; the base predictor handles missing values directly. HGB iteration settings are maximum counts, with scikit-learn defaults including automatic early stopping. Labels are absent from routing inputs.

What the conditional property establishes

When mandatory demand fits the budget, top-positive optional gains minimize estimated cost under the stated constraints. The elementary excess-cost bound assumes uniformly bounded gain error; it is not a fitted-model guarantee. When overloaded, the code holds the minimum necessary number of mandatory cases; ranking them by automation-to-review gain is not asserted to minimize review-versus-hold cost. Exhaustive small-problem tests check the feasible allocation property.

Numerical and reproducibility audit

| Check | Outcome |
| --- | --- |
| Data provenance | All three cached UCI releases match pinned SHA-256 values and manifest dimensions; default ID excluded; German numeric release distinguished from the 20-attribute original. |
| Split / result integrity | 36,000 unique, balanced rows: 3 datasets × 20 seeds × 5 conditions × 3 profiles × 4 budgets × 10 methods. These are repeated measurements, not 36,000 independent experiments. |
| Capacity / governance | All constrained rows respect capacity and have zero forbidden automation; held fractions match mandatory overflow. A label-free audit batch contains no prohibited mandatory automation. |
| Testing / unchanged outputs | 16 scientific invariant tests passed. Source code, dependency pins, manifest, CSVs, tables and figure files match their pre-edit hashes. Primary summaries independently recomputed to rounding precision. |
| Reproducibility limit | Pinned versions, commands, data hashes and all seeds are recorded. Local verification is not independent replication, external validation, or a guarantee across hardware/software versions. |

Novelty and interpretive assessment

The defensible contribution is an auditable integration and comparative stress test. Explicit rules are a small knowledge base; their zero violation rate is guaranteed by construction. The quality-aware cost reduction against feature-aware gain is about 0.20%, its descriptive interval crosses zero, and simpler baselines can be better. A methodological novelty claim still requires stronger comparison with related published methods and a clearer demonstrated advance.

The simulated reviewer uses the proposed quality fractions and full expected losses, favoring that representation. This is not human evidence. Generic corruption and illustrative costs limit external validity.

5  Verification of two figures and two tables


All four items are generated from results/metrics.csv. No experimental value, row selection, or figure artwork was changed during editing. Captions and interpretation were edited. Publication figures remain separate, scalable PDF files.

| Item | Scientific content and verification |
| --- | --- |
| Figure 1 — capacity versus cost | Five constrained methods × four capacities = 20 plotted means. Equal dataset/non-clean-condition weighting; quality-dependent reviewer. Bands are ±1.96 standard errors of 20 seed averages. Regeneration from the saved CSV reproduces the existing PNG pixel-for-pixel. Separate PDF is vector artwork with embedded font; axis units and maximum-capacity wording verified. |
| Figure 2 — paired differences | Fifteen condition/profile combinations at 20% capacity, averaged across three datasets. Positive feature-aware-minus-quality-aware cost favors quality gain. Paired split-seed t intervals reproduced; regeneration is pixel-exact. All five conditions, including clean and severe shift, are shown; no favorable subset selected. |
| Table 1 — baseline costs | Ten methods × four numeric columns = 40 values. Every cell independently recomputed from CSV and checked at four decimals. Macro equally weights three datasets and four non-clean conditions. Automation-only/no-rule rows are labeled non-compliant diagnostics, not comparable governed policies. |
| Table 2 — factorial ablation | Eight rows × four outcome columns = 32 values. All costs and review/hold/violation percentages verified at displayed precision. Quality Off is probability-only gain, not feature-aware gain. The 2×2 design crosses quality conditioning with rule enforcement. All rates use all records as denominator. |

Traceability of main narrative values

Primary cost difference = 0.0011996809; interval = [−0.0021582877, 0.0045576494]. Proposed cost = 0.6054895942; feature-aware = 0.6066892751. Actual proposed primary review = 19.8527%; hold = 11.8046%. Severe-shift hold ≈47.0%. Fixed-route hold-penalty sensitivity: 0.5606 at 0.5, 1.0304 at 1.5, 1.7350 at 3.0. These are expected normalized costs, not measured money or human behavior.

Presentation checks and limitations

Tables use editable text and horizontal rules without shading. All artwork is readable at manuscript size; Figure 2 uses larger width to preserve 15 labels. Both PDFs embed DejaVu Sans. Captions state the averaging, capacity, interval and simulator assumptions. Both figures are explanatory plots derived from code, not AI-generated visual evidence.

Repeated split intervals are descriptive. Observations and development datasets are reused; nominal “95%” intervals do not justify population significance. Full recalibration, reviewer learning, fairness, external replication and retrained policy/cost sensitivity were not conducted and are not implied.

6  Reference and citation verification: 1–7


Primary publication records were reopened on 23 October 2026. Authors, title, year, venue, volume/pages and identifier were checked against those records; citation claims were assessed at the scope supported by accessible abstracts. This is not a full re-derivation of every cited paper. All 13 bibliography entries are cited, with no missing keys, and follow first-appearance order.

[1] Verified metadata and citation purpose

Geifman &amp; El-Yaniv (2019). SelectiveNet. PMLR 97:2151–2159. Supports selective prediction / reject option.

https://proceedings.mlr.press/v97/geifman19a.html

[2] Verified metadata and citation purpose

Mozannar &amp; Sontag (2020). Consistent Estimators for Learning to Defer to an Expert. PMLR 119:7076–7087. Supports learned routing to a downstream expert.

https://proceedings.mlr.press/v119/mozannar20b.html

[3] Verified metadata and citation purpose

Verma, Barrejon &amp; Nalisnick (2023). Learning to Defer to Multiple Experts. PMLR 206:11415–11434. Supports calibration, consistency and multiple-expert deferral context.

https://proceedings.mlr.press/v206/verma23a.html

[4] Verified metadata and citation purpose

Wei, Cao &amp; Feng (2024). Exploiting Human-AI Dependence for Learning to Defer. PMLR 235:52484–52499. Supports dependence-aware deferral; not an implemented baseline here.

https://proceedings.mlr.press/v235/wei24a.html

[5] Verified metadata and citation purpose

Liu, Cao, Zhang, Feng &amp; An (2024). Mitigating Underfitting in Learning to Defer with Consistent Losses. PMLR 238:4816–4824. Supports consistent-loss / underfitting context.

https://proceedings.mlr.press/v238/liu24h.html

[6] Verified metadata and citation purpose

Mao, Mohri &amp; Zhong (2025). Mastering Multiple-Expert Routing. PMLR 267:43035–43066. Supports multiple-expert learning guarantees; no transfer of its guarantees to our regressor.

https://proceedings.mlr.press/v267/mao25c.html

[7] Verified metadata and citation purpose

Farinhas, Guerreiro, Agrawal, Rei &amp; Martins (2025). Translate Smart, not Hard. EMNLP:26742–26756. DOI 10.18653/v1/2025.emnlp-main.1358. Supports earlier quality-aware translation cascades; distinguishes translation quality from input missingness/range checks.

https://aclanthology.org/2025.emnlp-main.1358/

7  Reference and citation verification: 8–13


[8] Verified metadata and citation purpose

DeSalvo, C. Mohri, M. Mohri &amp; Zhong (2025). Budgeted Multiple-Expert Deferral. arXiv:2510.26706, v1. DOI 10.48550/arXiv.2510.26706. Verified as a preprint. Its budget concerns expert querying during training; it is not cited as the same deployment-batch constraint.

https://arxiv.org/abs/2510.26706

[9] Verified metadata and citation purpose

Saketos, Reveillard, Proutiere, Dalleiger &amp; Xiao (2026). To Defer or Not to Defer? Online Learning with LLMs and Congested Experts. arXiv:2610.15128, v1. DOI 10.48550/arXiv.2610.15128. Verified as a preprint submitted 10 October 2026. Supports congestion-aware online setting; our code has no queue dynamics.

https://arxiv.org/abs/2610.15128

[10] Verified metadata and citation purpose

Si (2026). Governing data trust in digital lending ecosystems. Journal of Banking Regulation 27, article 69. DOI 10.1057/s41261-026-00364-8. Publisher metadata/abstract verified; published 21 October 2026. Full subscription text was not accessed. Used only for claim-specific evidentiary controls, not empirical validation of this study.

https://link.springer.com/article/10.1057/s41261-026-00364-8

[11] Verified metadata and citation purpose

Hofmann (1994). Statlog (German Credit Data). UCI. DOI 10.24432/C5NC77. Dataset citation verified. UCI distinguishes the original 20 attributes from the expanded numeric release used here (24 predictors).

https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

[12] Verified metadata and citation purpose

Quinlan (1987). Statlog (Australian Credit Approval). UCI. DOI 10.24432/C59012. Dataset citation and 690×14 dimensions verified. Released numeric data have no NaNs in the loaded file; this does not mean the source task had no missing-data handling.

https://archive.ics.uci.edu/dataset/143/statlog+australian+credit+approval

[13] Verified metadata and citation purpose

Yeh (2009). Default of Credit Card Clients. UCI. DOI 10.24432/C55S3H. UCI’s recommended citation year is 2009; the current donation date shown is 2016. The manuscript retains the recommended citation, not an inferred donation year.

https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients

Bibliography uses consistent numbered brackets and includes persistent identifiers or publisher URLs. Preprints are clearly marked. Reference [10] now explicitly identifies 69 as an article number. No cited algorithm is described as experimentally reproduced when only a component comparator was run. No exhaustive literature or plagiarism certification is claimed.

8  Final audit and unresolved issues


Reverification after substantive corrections

The methods, gap, results interpretation, limitations, captions and spacing were corrected and then checked again. The recorded numerical/source audit passed 44 checks, including all displayed table values and both figure regenerations. The 16 existing invariant tests passed. LaTeX was compiled twice to resolve citations; the final PDF is 10 pages with exactly two figure and two table environments, six keywords and 13 references. All final pages were rendered and inspected for overlap, clipping and readability.

Unresolved scientific issues — required for a stronger submission

• Novelty and comparison. The exact allocator is elementary conditional selection; the two-rule knowledge base and compact representation alone do not establish a strong new KBS contribution. Compare a suitable published learned-deferral baseline or narrow the contribution and reconsider journal positioning.

• Reviewer evidence and realism. Obtain defensible reviewer evidence or external validation. The constructed reviewer-quality relationship and full expected-loss targets are favorable assumptions. Domain-valid corruption and validation outside reused benchmark observations remain absent.

• Policy robustness. Validate review thresholds, costs and staffing assumptions. The existing hold-cost check keeps routes fixed; it is not a retrained policy sensitivity study. There is no causal business-impact estimate or calibrated risk guarantee under shift.

Unresolved submission items — complete before upload

• Confirm all author details, actual contribution roles, funding and competing interests; produce the requested declaration file. Replace author-review placeholders with truthful final statements after human verification.

• The requested private repository has been created under ykunam and populated with the reviewed project. Make an appropriate versioned release and archive generated evidence, then add public access and a persistent identifier. A private repository is not an archival data deposit.

• Check current portal requirements, including any graphical abstract or additional forms. Recompile and re-audit the page limit after final author declarations and repository references; the current draft already occupies all ten allowed pages.

Preservation and compact handoff

Backup: KBS_Pre_Editing_Backup_2026-10-23.zip contains the original uploaded PDF and the original 16-file project. Revised package: KBS_Budgeted_Human_Deferral_Package.zip retains 16 project files and one results folder. The editorial report is delivered separately; no extra report/scaffolding folders were added to the repository. Scientific code and outputs were preserved; only manuscript, README and submission notes were edited.

Experiment SHA-256: 395ccbfe631ef9d26c8efefad4f613301e91db4186be01093b6e6ca7eb67e641Metrics SHA-256: ddbe872e5b57eb56049f68b54d8a7a13b12ca59f73e053b4d6687bc246a7d405

Final recommendation: MAJOR REVISIONS. The revised files support careful author review and further scientific development. They must not be described as fully submission-ready or as guaranteed Q1 acceptance. The private ykunam repository was created and populated; no public release or journal submission was performed.

