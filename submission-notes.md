# Submission-readiness audit — Short Communication (revision v2, after review of PR #2)

Knowledge-Based Systems | Short Communication | 23 October 2026
**Authority:** the official *Guide for Authors — Knowledge-Based Systems* (ScienceDirect, retrieved 23 October 2026, supplied by the author). The accepted KNOSYS paper (Thota) was used only as a model of presentation: an explicit contribution list, a paragraph separating the work from the closest method, ablations and an honest limitations section. No text, figures or results were taken from it.

**Recommendation: MINOR REVISIONS before submission.** All six review findings were addressed in code, results, tables and text, and every quoted number was recomputed from the final result files. What remains is author-side administration (Section 6). Two caveats:
- The proposed estimator is not superior pooled. The paper's contribution rests on the exact governance-constrained allocator, the conditions analysis and the staffing results.
- The corrected baseline and service metrics have not yet been independently re-reviewed. Please re-review PR #2 before merging.

The v1 manuscript is preserved in git history at commit `a343665`.

## 1. Response to the PR #2 review

| # | Finding | Resolution | Evidence |
|---|---|---|---|
| 1 | OvA ignores the review fee | OvA is now trained as published (unweighted, calibrated heads). Routing uses a cost-sensitive plug-in rule: expected automation loss − expected review loss − c_R. All OvA-dependent experiments were rerun: main grid, data volume, log completeness, rules, cost refits. | `dqd/core.py::fit_l2d_ova`; `tests/test_baselines.py`: score shifts by exactly 100 when the fee goes 0→100, and no record is deferred at fee 100. **Outcome changed:** OvA is now the strongest learned router pooled (0.5312 vs 0.5355, n.s.) and on default data. The manuscript no longer calls the proposed router the best learned method. |
| 2 | "Overtook Chow at 1,800" unsupported | Reworded to "approximately competitive at 1,800 (+0.1%, 10/20, p = 0.85) and cheaper only at 6,000". Explicitly "not a deployment threshold". Highlight 3 and the managerial advice reworded. | Rerun `e6_volume.csv.gz`. |
| 3 | Table 2 lacks Holm adjustment | Holm applied over the table's 18 cells (declared family); bold = adjusted p < 0.05 (none). Unadjusted p < 0.05 is marked †. The analysis is labeled exploratory in the text, table note, abstract and highlights. Holm families declared in the protocol: pooled (8), per-dataset (9), data-volume (7), Table 2 (18). | `results/tables/sc_table2_holm.csv`. |
| 4 | Service metrics exclude unresolved cases | Added arrival-cohort measures counting cases unresolved at day 40 as unmet, plus Kaplan–Meier resolution-time quantiles with censoring. The old measures are kept, labeled "conditional on resolution". Fig. 2(b–c) now plots cohort measures. | `dqd/dynamic.py::cohort_metrics`; `tests/test_service_metrics.py` reproduces the reviewer's case (conditional SLA 100% while ~half are unresolved → cohort SLA < 60%, KM p95 = ∞). At 20% capacity, cohort two-day resolution is 36% vs 48% conditional, 21.7% unresolved. |
| 5 | Audit overstated readiness | This document replaces the earlier audit. The recommendation is now conditional on re-review and on the author-side items. | — |
| 6 | Oracle described as an upper bound | Now "an optimistic lower bound on attainable cost, not deployable" (Table 1 note). | `manuscript.tex`, Table 1. |

## 2. Guide-for-Authors checklist (official guide)

| Requirement (guide section) | Status | Evidence / action |
|---|---|---|
| Short communication ≤ 10 double-line-spaced pages including tables and figures (Article types) | PASS | 10 pages (US Letter, 11 pt Times, 0.75 in margins, double-spaced text, captions and references; table rows at 1.5×). |
| Editable source; `.tex` accepted; PDF not a source file (Manuscript formatting) | PASS | Upload `manuscript.tex`, `budgeted_deferral/results/sc_tables.tex` and the figure PDFs. Use of the Elsevier LaTeX template is *encouraged*, not required; the article class is used. |
| Title page: title, author, lettered affiliation with full postal address and country, corresponding author with e-mail (Title page) | PASS with one deviation | Corresponding author's e-mail (yeshwanth.kunam@gmail.com) on the title page. Affiliation is "Independent Researcher, USA" at the author's request; the guide asks for a full postal address, so the editorial office may request one. |
| Abstract ≤ 250 words, stand-alone, states purpose, procedures, main findings with statistical significance, conclusions; no references (Abstract) | PASS | 229 words; reports p-values and the Holm result; no citations. |
| 1–7 keywords (Keywords) | PASS | 6. |
| Highlights: separate editable file with "highlights" in the name; 3–5 bullets ≤ 85 characters (Highlights) | PASS | `highlights.txt`: 5 bullets, 72–80 characters. |
| Equations as editable text (Math) | PASS | LaTeX math; 1 numbered display equation. |
| Tables editable, cited, numbered consecutively, captions, **notes below the table body**, no vertical rules or shading (Tables) | PASS | Tables 1–2 generated as LaTeX (booktabs); notes moved below the table body in this revision. |
| Artwork: cited, numbered, captioned (brief title + description); **each figure as a separate file named logically, e.g. Figure_1** (Figures) | PASS (upload step) | Both figures are cited and captioned with a title sentence. At upload, submit `budgeted_deferral/figs/fig3_volume.pdf` as **Figure_1.pdf** and `fig5_backlog.pdf` as **Figure_2.pdf**. These are vector PDFs with embedded fonts, programmatically generated from results; the GenAI declaration covers AI-assisted analysis code. |
| Numbered sections and subsections; abstract unnumbered (Article structure) | PASS | 1–6 with 2.1/2.2. |
| References: every cited item listed and vice versa; real sources; DOIs where available; any consistent style (References) | PASS | 35 entries; all cited in order of first appearance; all verified to exist (Section 4); DOIs given for all DOI-bearing items. |
| Data statement (Research data) | PASS (pending DOI) | Repository URL given; archival DOI to be added. |
| Funding statement; sentence required if none (Funding sources) | PENDING | Placeholder with the guide's wording; author to confirm. |
| CRediT statement (Author contributions) | PENDING | Draft roles; author to confirm. |
| Competing interests via the declarations tool; Word file uploaded (Declaration of competing interests) | PENDING | Not in the manuscript text, per the guide. Complete the tool at submission ("I have nothing to declare" if applicable). |
| GenAI declaration in a section directly before the references, using the guide's statement (Declaration of generative AI use) | PASS (confirm) | Present before the references; bracketed sentence to be confirmed by the author. |
| Acknowledgements directly before references, if any (Acknowledgements) | N/A | None. |

## 3. Figures and tables — verification

| Item | Source | Check |
|---|---|---|
| Table 1 (cost by method × dataset; HMEQ natural) | `scripts/make_sc_tables.py` ← `results/static_logs.csv.gz` (rerun) | Generated; bold computed as lowest deployable cost per column; notes below table. |
| Table 2 (quality value by head) | same script; Holm over 18 cells | Generated; no cell significant after adjustment; † marks unadjusted p < 0.05. |
| Fig. 1 (data volume, default and HMEQ) | `results/e6_volume.csv.gz` (rerun) via `scripts/fig_volume.py` | Now includes the corrected OvA; inspected. |
| Fig. 2 (backlog, cohort resolution) | `results/dynamic*.csv.gz` (rerun) via `scripts/fig_dynamic.py` | Panels (b)–(c) use cohort measures; inspected. |
| Every number quoted in the text | 77 checks recomputed from the final result files | 74 passed directly. 3 flags were corrected in the text: FIFO two-day cohort resolution is 40% (not 41%), and the cost-refit sentence now reads "confidence cheapest in all seven settings; best learned router within 0.7% of Chow". |
| Tests | `python -m unittest discover -s budgeted_deferral/tests` | 8/8 pass (propositions, baseline fee sensitivity, cohort metrics). |

## 4. Reference verification

35 references: **22 journal articles from Elsevier (15), IEEE (6) and MDPI (1)**; 7 conference, journal or preprint papers for the compared methods and closest prior art (PMLR ×2, arXiv ×2, TMLR, AAAI, EMNLP); 2 statistical method papers; 4 datasets.

- **Existence:** every reference was located in this session through publisher, repository, institutional or index records (e.g., RePEc for IJIM, Bus. Horiz. and EJOR; repository records for GIQ, JSIS, Inf. Fusion, Neurocomputing and Sensors; DOI search for Proc. IEEE; proceedings pages for the PMLR, AAAI and EMNLP papers; arXiv for both preprints).
- **Correction made:** Abbaspour Onari et al. (2024, *Knowledge-Based Systems* 295, 111761). Both surnames were wrong in v1, now corrected from a co-author's publication list.
- **Not re-fetched:** volume, page and DOI fields for the other v1-audited entries could not be re-fetched from Crossref here (blocked). They are retained from the v1 Crossref audit and are consistent with the records found.
- **Q1 status:** for the 20 retained journals it comes from the v1 audit (SJR 2025 best quartile via search-indexed SCImago records). For the two added journals (*Information Systems*, *Future Generation Computer Systems*) it comes from Journal Metrics (OpenAlex-based, 2026). SCImago could not be reached from this environment, so SJR quartiles were not re-verified this session. "Q1" means the journal's best quartile, not every category.
- **Placement:** each citation supports the sentence it appears in. Methods cited in Table 1 are the methods implemented.

## 5. Scientific and editorial changes in this revision

- Results reframed to match the corrected evidence. Cost-aware heuristics lead pooled. OvA and the two-head estimator are the strongest learned routers and are statistically tied. Both beat Chow on all 20 splits with about 6,000 training records. The two-head router is the most data-efficient at 200–600 records (Holm p < 0.005).
- The quality mechanism is reported as exploratory, in line with the multiplicity correction.
- Service results now count unresolved cases. The staffing conclusion strengthens: at 20% capacity, 21.7% of mandatory cases are never resolved.
- Introduction strengthened: why the problem matters, an explicit gap statement, and how the study differs structurally from learning-to-defer work.
- Language edited for consistency (US spelling, minus signs, terminology "two-head router/estimator"), with redundancy removed to keep 10 pages.

## 6. Unresolved items (author-side, before submission)

1. Funding and CRediT statements, the declarations-tool upload, the GenAI sentence in brackets, and affiliation/e-mail confirmation.
2. Make the repository public; create a release and Zenodo DOI; add the DOI to the Data statement.
3. Upload figures as `Figure_1.pdf` / `Figure_2.pdf` and highlights as a separate file.
4. Optional: confirm SJR quartiles on SCImago for the two new journals.
5. **Scientific risk (disclosed, not blocking):** simulated reviewers; old benchmarks; stylized defects; illustrative thresholds and costs; three of four hypotheses inconclusive; modest methodological novelty. An editor may still judge the contribution insufficient for KBS.
