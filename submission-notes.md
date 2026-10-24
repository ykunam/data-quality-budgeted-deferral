# Cybersecurity manuscript audit — 24 October 2026

**Recommendation: Major Revisions before formal KBS submission.** Reproducibility and editorial repairs are complete. Real analyst/SOC validation, domain-validated rules/costs and comparisons with the closest cost/capacity-aware methods remain material scientific gaps. No acceptance certificate, merge or journal submission is claimed.

## Scientific verification

- Initial plan/code frozen before fitting at `cab4cdec3a1827a3a0a1c531f5c1b23eb84a560a`. An audit found omitted p×family-quality interactions in the richer comparator. Correction frozen at `e16fe85e54cd28f77d1e2c4a291d5670661eb2fc`, followed by a complete rerun of all 40 dataset/seed fits. All 19,200 non-rich-comparator rows match initial outputs exactly; the primary is unchanged. Later code amendments affect `report()` layout/precision only; fitting/allocation/inference ASTs are unchanged.
- Complete final grid: 21,120 unique aggregate rows; seeds 2–21; two datasets; two simulated reviewers; four conditions; three capacities. Forty checkpoints verified. All 26 tests pass. Final independent audit recomputed cost decomposition across every row, 70 display cells and all eight paired contrasts.
- Prespecified primary: UNSW outage at 20% capacity, automation-only quality versus probability-only with identical review counts and mandatory ordering. Cost 0.2144142826 → 0.2075548932; absolute reduction 0.0068593894; relative 3.1991%; conditional 95% Monte Carlo interval [0.0056075244, 0.0081112545]; two-sided paired-seed p=5.5478e-10; 20/20 wins. Meets fixed ≥1% practical criterion and p<0.05.
- These are randomization intervals conditional on fixed sampled corpora, not new-network/organization/human uncertainty. Reviewers are averaged within seed. No row-wise pseudo-replication, corrected-resampled t-test or old finance outcome is used.
- Seven secondary contrasts share one Holm adjustment. UNSW clean/replacement survive. Both severe conditions are structural nulls. No CIC contrast survives; outage benefit is 0.16% (Holm p=1.000), replacement adverse −2.18% (Holm p=0.169). All remain in Table 2.
- Confidence cost is 0.5193 on CIC outage versus quality-in-automation 0.6914. Conformal adaptation changes the automation/hold trade-off; original finite-sample guarantees are not asserted under dependent augmentation/temporal shift. All reviewers are simulated, not actual analysts.
- Severe rules make every flow mandatory; at 20% capacity about 80% remain unresolved. Native quality-both ordering holds 96.9% of UNSW attacks and 76.0% of CIC attacks. Constant hold cost can favor inexpensive reviews over severe threats. Holds never count as resolutions. Fixed-route sensitivity does not claim policy refitting.

## Dataset verification

Provider pages were checked. Direct UNSW access returned 403; CIC required a personal-information form, which was not submitted. All 10 acquired file hashes match pinned mirror metadata. This verifies acquired bytes, not provider-signed hashes or original ground truth.

- UNSW: `Mouwiya/UNSW-NB15-small`, revision `6f5f54594dfc80c84264aec4c7cc3d9b162f1e2f`; official-sized source roles 175,341/82,332. An independent LFS pointer matches the smaller partition but misnames its role; official counts determine role assignment. Retained development/test 80,000/52,648.
- CIC: `bvsam/cic-ids-2017`, revision `70bac6246d99cf046186a02e1cce6883e2ffe7ea`. Raw mirror 3,119,345; drop 288,602 unlabeled Thursday-morning extras → 2,830,743 labeled rows. Retained Monday–Wednesday train/Thursday calibration-gain/Friday test 60,000/40,000/40,000.
- Identifier/attack-category leakage removed; nonfinite and negative numeric values become missing, including unknown-window sentinels. Within-source duplicates and later-role modeled-feature overlap excluded. Hash sampling is label-independent. CIC feature/session groups and augmented copies stay together. Category/range fitting uses training data only. Friday class/family shift is retained; test labels never recalibrate the model.
- Corruption generators accept no labels; replacement donors come from training. Completed flows are proxy alerts. No measured telemetry age, adaptive attacker, actual incident queue or production response-time claim is made. Raw third-party corpora are ignored and not redistributed. Full provenance: `budgeted_deferral/results/cyber-data-verification.json`.

## Journal and presentation checklist

Primary authority: supplied 20-page KBS Guide for Authors, read completely. Supplied 19-page example was read for presentation only; its acceptance was not independently certified and its length does not establish Short Communication compliance. No content copied.

- Short Communications supported, maximum 10 double-spaced pages including figures/tables. Final LaTeX PDF and Word render each have 10 pages. No exact mandatory font/margin or separate word/reference maximum verified.
- Abstract 175 words (≤250), seven keywords (1–7), no abstract citations. Numbered sections/equations/pages; editable mathematics, declarations and numeric first-use references.
- Exactly two programmatic figures, cited/captioned, separate vector PDFs with embedded fonts. PNGs are 450 dpi previews, not a claimed 1000 dpi raster-line submission.
- Exactly two editable tables, horizontal rules only. Table 1: seven methods × two datasets, 42 displayed values; percentages to two decimals. Table 2: all eight declared contrasts and seven secondary Holm values. All 70 machine-readable display means checked.
- Five highlights, lengths 62/61/65/65/66 characters (≤85). No mandatory graphical abstract established from supplied guide; live portal remains unchecked.
- Narration frames a bounded conditions analysis, separates estimation/review volume/policy and foregrounds non-replication, simple-baseline strength and unresolved threats. No first-system, new-surrogate, universal-superiority or real analyst-performance claim.

## Reference and citation audit

33/33 entries cited in numeric first-use order. Twenty-nine DOI records plus four primary non-DOI records verified. Full evidence, final-issue overrides and ranking URLs: `budgeted_deferral/results/cyber-reference-verification.json`. No exhaustive full-text, plagiarism or retraction certificate is claimed.

22 requested-publisher journal articles meet **SJR 2025 best-quartile Q1**, checked 24 October 2026. This is not an every-category, JCR, publication-year or current Scopus-coverage certification. Necessary exceptions: Electronics Q2 (closest conformal prior art), Information Security Journal Q2 (UNSW evaluation), ICML/TMLR, statistical source, dataset conferences and Springer chapters. Relevance takes priority over manufacturing an all-Q1 list.

Corrected Vielberth DOI `10.1109/ACCESS.2020.3045514`, Verma PMLR `verma22c`, Chai final 2023/35(5)/4646–4667 and Lu final 2019/31(12)/2346–2363. Jalalvand is online in 2026 with assigned Information Sciences 760 (2027), 124128; verified future issue year retained. Sahin metadata/abstract and released E11 code inspected; full publisher text was blocked, so no full-text verification claimed.

## Author declarations and remaining submission work

No funding and no competing interests preserve author confirmations. Affiliation: Midwest University, 851 Parr Road, Wentzville, MO 63385, USA. Correspondence: yeshwanth.kunam@gmail.com. Prior contribution confirmation retained; author must personally review/approve this new cybersecurity manuscript, code/results and AI disclosure.

Complete Elsevier’s official Declarations Tool and upload its generated form. Existing disclosure DOCX is not claimed tool-generated. Verify live portal/current guide, including any graphical-abstract requirement. Code/results/manifests are cited via immutable corrected snapshot `f5bb01a155bda5ee4f62810ffdc5f39fd61b7e4d`; the current branch adds presentation-only changes. Persistent archival deposit remains outstanding; no DOI invented. Follow source licensing/access terms.

Scientific improvements still needed: SOC-validated analyst/rule/cost assumptions; compatible newly tuned L2DHF/DeCCaF comparison or stronger methodological advance; preferably provider-authorized/corrected contemporary data; severity/delay-dependent unresolved-threat valuation. These require new evidence and a newly declared analysis, not cosmetic editing or favorable post hoc selection.
