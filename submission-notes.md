# Submission-readiness audit — Short Communication (revision v2)

Knowledge-Based Systems | Short Communication | audit date 23 October 2026

**Manuscript:** `manuscript.tex` / `manuscript.pdf` — *When does data quality help human deferral? Governance-constrained review allocation in knowledge-based decision systems*.
**Recommendation: MINOR REVISIONS (author-side items only).** The scientific content, figures, tables and references were checked against the code and results. The items in Section 6 must be completed by the author before submission.

The v1 short communication is preserved in the git history at commit `a343665` (on `main`). The extended full-length version of this revision is in `manuscript_v2/`, for reference or as supplementary material.

## 1. Journal requirement checklist

The official KBS Guide for Authors was not supplied in this session. Requirements marked "from v1 audit" restate the page-referenced rules recorded in the previous version of this file, and should be re-checked against the current guide before submission.

| Requirement (source) | Status | Evidence |
|---|---|---|
| Short Communication ≤ 10 double-spaced pages including tables and figures (v1 audit, guide p. 3) | PASS | 10 pages (pdflatex, US Letter, 11 pt Times, 0.75 in margins). Text, captions and references are double-spaced; table rows use 1.55× stretch because `setspace` single-spaces float bodies (same convention as v1, now widened). |
| Abstract ≤ 250 words, no citations (v1 audit, p. 10) | PASS | 187 words, no citations. |
| 1–7 keywords (v1 audit, p. 10) | PASS | 6 keywords. |
| Highlights 3–5 bullets, ≤ 85 characters each (v1 audit, p. 10) | PASS | `highlights.txt`: 5 bullets, 72–80 characters. |
| Editable source (v1 audit, p. 9) | PASS | `manuscript.tex`; tables generated as editable LaTeX (`budgeted_deferral/results/sc_tables.tex`). |
| Numbered sections in standard order (v1 audit, p. 14) | PASS | Introduction → Method → Experimental protocol → Results and discussion → Limitations → Conclusion → declarations → references. |
| Numbered equations; consecutive table and figure numbering, all cited in text (v1 audit, p. 11) | PASS | 1 numbered display equation; Tables 1–2 and Figs 1–2 each cited before they appear. |
| Vector artwork with embedded fonts (v1 audit, pp. 11–12) | PASS | `fig3_volume.pdf`, `fig5_backlog.pdf` are vector PDFs with embedded fonts; the manuscript PDF embeds all 15 fonts. |
| Numbered references in order of first citation (v1 audit, pp. 16–18) | PASS | 35 entries, ordered by first citation programmatically; no missing or unused keys. |
| Data statement, AI-use declaration (journal policy) | PASS | Both present. |
| Competing interests, funding, CRediT (journal policy) | **PENDING** | Placeholders — author must complete. |
| Graphical abstract (optional at KBS per v1 audit) | NOT PROVIDED | Optional; not created. |
| Author's own constraint: exactly two figures and two tables | PASS | Fig. 1 (data volume), Fig. 2 (backlog); Table 1 (main comparison), Table 2 (where quality helps). |

## 2. Scientific and editorial improvements (v1 → v2)

1. **Research question** reframed from "does quality help?" to "under what conditions does it help?", matching the mixed evidence.
2. **Method:** Proposition 1 gives exact allocation in both regimes and corrects v1's overload ordering. Proposition 2 shows that backlog is invariant to prioritization. Both are tested by brute force (`budgeted_deferral/tests/test_propositions.py`).
3. **Estimator:** a two-head design (automation loss / reviewer loss) trained on noisy, incomplete review logs replaces the optimistic expected-loss targets.
4. **Baselines:** published L2D surrogates (Mozannar & Sontag; Verma & Nalisnick), differential triage (Raghu et al.) and Chow's rule, under matched information, rules, costs and capacity.
5. **Reviewer models:** five instead of three, four of which do not depend on the router's quality signals.
6. **Data quality:** domain-valid, partly invisible defects (informative missingness, stale records, inconsistent codes), plus HMEQ as an external dataset with natural missingness.
7. **Statistics:** corrected resampled t-test with Holm adjustment, plus win counts. Cost sensitivity now refits every method.
8. **Managerial outcomes:** a 40-day backlog simulation reporting workload, backlog, tail waiting time, two-day resolution and override rate.
9. **Writing:** contributions and non-claims stated explicitly. Negative and inconclusive results are reported (pooled loss to Chow's rule; H1, H3 and H4 inconclusive).

## 3. Verification of the two figures and two tables

| Item | Source of numbers | Check |
|---|---|---|
| Table 1 (cost by method × dataset, HMEQ natural) | `budgeted_deferral/scripts/make_sc_tables.py` reading `results/static_logs.csv.gz` | Generated programmatically; bolding is computed. |
| Table 2 (quality value by head) | same script; corrected resampled t-test for bolding | Generated programmatically. |
| Fig. 1 (data volume) | `results/e6_volume.csv.gz` via `scripts/fig_volume.py` | Re-rendered and inspected. |
| Fig. 2 (backlog) | `results/dynamic*.csv.gz` via `scripts/fig_dynamic.py` | Re-rendered and inspected; fluid-model overlay matches the simulation. |
| Numbers quoted in text | 57 checks recomputed from the result files | 49 passed directly. 5 flags were artefacts of the checking script; rechecked against rule-compliant methods, the claim holds. 3 flags exposed one overstated sentence, now corrected: on default data the router beat Chow, confidence, L2D-CE and the probability-only ablation on 20/20 splits, but L2D-OvA and the single-head design only 15/20 (n.s.) and differential triage 19/20. |
| Reproducibility | fixed seeds | Re-running a split reproduces the stored result to all digits. |

## 4. Reference and citation verification

35 references: **22 journal articles from Elsevier (15), IEEE (6) and MDPI (1)**, 7 conference papers or preprints required for the compared methods and closest prior art, 2 statistical method papers, and 4 datasets.

| Group | References | Verification |
|---|---|---|
| Elsevier journals (15) | Abraham 2019 IJIM; Janssen 2020 GIQ; Papagiannidis 2025 JSIS; Wirtz 2022 GIQ; Green 2022 CLSR; Abdar 2021 Inf. Fusion; Mohammed 2025 Inf. Syst.; Wu 2022 FGCS; Tariq 2025 ESWA; Onari 2024 KBS; Barredo Arrieta 2020 Inf. Fusion; Artelt 2023 Neurocomputing; Lessmann 2015 EJOR; Jarrahi 2018 Bus. Horiz.; Mikalef 2021 I&M | Metadata and DOIs: 13 carried over from the v1 Crossref audit; Mohammed 2025 and Wu 2022 newly verified against institutional repository records. |
| IEEE journals (6) | Chow 1970 TIT; Zhang 2023 Proc. IEEE; Mena 2020 Access; Chai 2023 TKDE; Adadi 2018 Access; Lu 2019 TKDE | Carried over from the v1 audit. |
| MDPI journal (1) | Zhang 2021 Sensors | Carried over from the v1 audit. |
| Methods and prior art (7) | Mozannar & Sontag 2020 (PMLR 119); Verma & Nalisnick 2022 (PMLR 162, pp. 22184–22202); Raghu et al. 2019 (arXiv); Alves et al. 2024 (TMLR); Hemmer et al. 2023 (AAAI 37); Farinhas et al. 2025 (EMNLP); Saketos et al. 2026 (arXiv) | Verified against the proceedings or arXiv pages. These are not MDPI/IEEE/Elsevier journals, but they are the methods implemented and the closest prior art, so they cannot be dropped without misrepresenting novelty. |
| Statistics (2) | Nadeau & Bengio 2003 (Mach. Learn.); Holm 1979 (Scand. J. Stat.) | Verified. |
| Datasets (4) | UCI German, Australian, Default; HMEQ (Baesens et al. 2016) | DOIs and checksums recorded. |

**Q1 status — limits that must stay visible.**
- **20 retained journal articles:** Q1 status comes from the v1 audit (SJR 2025 best quartile, from search-indexed SCImago records). It was not re-verified in this session because SCImago and Crossref pages could not be reached from the working environment.
- **Information Systems and FGCS (new):** shown as Q1 by Journal Metrics (OpenAlex-based, 2026 release). Their SJR quartile was not directly confirmed.
- **Scope of the label:** "Q1" means best quartile of the journal, not of every subject category or of the paper.

**Citation placement:** each citation supports the sentence it appears in. Prior-art citations are framed as not establishing novelty. Methods cited in Table 1 are the methods actually implemented.

## 5. Experimental consistency (manuscript ↔ code ↔ data)

- Protocol settings in the text match `budgeted_deferral/dqd/` and the v1 `experiment.py`: splits, quality bounds, rules, costs, corruption, representation and hyperparameters.
- German and Australian file checksums match the v1 manifest. The default dataset comes from an identical-content mirror, so its checksum differs from v1's zip archive.
- L2D baselines are adaptations: shared classifier, cost weights, and a one-hidden-layer NumPy network. This is stated in the text.

## 6. Unresolved items (must be addressed before submission)

1. **Declarations:** funding, competing interests and CRediT statement are placeholders. Also confirm the author's affiliation and e-mail.
2. **Archival release:** create a versioned GitHub release, deposit it on Zenodo, and add the DOI to the Data availability statement. The repository must be public at submission.
3. **Author guide re-check:** confirm the page, abstract, highlights and reference rules against the current KBS Guide for Authors. It was not available in this session.
4. **Q1 confirmation:** if Q1 status matters for your institution, confirm SJR quartiles directly on SCImago for the two new journals and spot-check the carried-over set.
5. **Scientific limitations (disclosed, not blocking):** simulated reviewers, older benchmarks, stylized defects, illustrative thresholds and costs, and three of four hypotheses inconclusive.
6. **Optional:** a graphical abstract.

**Final recommendation: MINOR REVISIONS.** These are author-side administrative items. No further experiments are required for a Short Communication.
