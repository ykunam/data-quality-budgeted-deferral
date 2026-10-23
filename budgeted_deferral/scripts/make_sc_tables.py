"""Write the two Short Communication tables (LaTeX) directly from seed-level results."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import pandas as pd
from dqd import core as C, stats as ST

df = pd.read_csv("results/static_logs.csv.gz")
nc = df[df.condition.isin(C.FAMILY_A + C.FAMILY_B) & (df.capacity == 0.2)]
nat = df[(df.dataset == "hmeq") & (df.condition == "clean") & (df.capacity == 0.2)]
ROWS = [("automation_only", "Automation only (rules ignored)$^a$"), ("random", "Random"), ("confidence", "Confidence"),
        ("chow_risk", "Chow cost risk \\cite{chow}"), ("quality_only", "Quality only"),
        ("sh_quality", "Single-head gain (earlier version)"), ("l2d_ce", "L2D-CE \\cite{mozannar}"),
        ("l2d_ova", "L2D-OvA \\cite{verma}"), ("2h_rich_gorder", "Differential triage \\cite{raghu}"),
        ("2h_prob", "Two-head, probability only"), ("2h_quality", "Two-head, quality-aware (proposed)"),
        ("oracle", "Oracle (uses labels)$^b$")]
cols = {ds: nc[nc.dataset == ds].groupby("method").cost.mean() for ds in ["german", "australian", "default"]}
macro = pd.concat(cols, axis=1).mean(1)
hm = nat.groupby("method").cost.mean()
deploy = [m for m, _ in ROWS if m not in ("automation_only", "oracle")]
best = {k: v[deploy].idxmin() for k, v in {**cols, "macro": macro, "hmeq": hm}.items()}
def cell(series, key, m):
    s = f"{series[m]:.4f}"
    return f"\\textbf{{{s}}}" if best[key] == m else s
lines = []
for m, lab in ROWS:
    lines.append(f"{lab} & {cell(cols['german'],'german',m)} & {cell(cols['australian'],'australian',m)} & "
                 f"{cell(cols['default'],'default',m)} & {cell(macro,'macro',m)} & {cell(hm,'hmeq',m)} \\\\")
t1 = ("\\begin{tabular}{lccccc}\\toprule\n"
      "Method & German & Australian & Default & Macro & HMEQ (natural) \\\\\\midrule\n" + "\n".join(lines) +
      "\n\\bottomrule\\end{tabular}")

def rel(sub, a, b):
    s = sub[sub.method.isin([a, b])].groupby(["seed", "method"]).cost.mean().unstack(); d = s[b] - s[a]
    m, lo, hi, p = ST.corrected_t(d)
    return 100 * m / s[b].mean(), int((d > 0).sum()), p
orig = df[df.dataset.isin(["german", "australian", "default"]) & (df.capacity == 0.2)]
R = [("Informative missingness (B)", orig[orig.condition == "informative"]),
     ("Stale records (B)", orig[orig.condition == "stale"]),
     ("Inconsistent codes (B)", orig[orig.condition == "inconsistent"]),
     ("Visible defects (A), quality-coupled reviewer", orig[orig.condition.isin(C.FAMILY_A) & (orig.reviewer == "quality")]),
     ("Visible defects (A), four decoupled reviewers", orig[orig.condition.isin(C.FAMILY_A) & (orig.reviewer != "quality")]),
     ("HMEQ, natural missingness (external)", nat)]
VARIANTS = ["2h_qA", "2h_qH", "2h_quality"]
cells = [[rel(sub, v, "2h_prob") for v in VARIANTS] for _, sub in R]
# Holm adjustment over the whole table (18 comparisons = one family)
padj = ST.holm([c[2] for row in cells for c in row]).reshape(len(R), len(VARIANTS))
def fmt(c, pa):
    txt = (f"$+${c[0]:.2f}" if c[0] >= 0 else f"$-${-c[0]:.2f}") + f" ({c[1]})"
    return f"\\textbf{{{txt}}}" if pa < 0.05 else (txt + "$^{\\dagger}$" if c[2] < 0.05 else txt)
lines = [f"{lab} & " + " & ".join(fmt(c, pa) for c, pa in zip(row, prow)) + " \\\\"
         for (lab, _), row, prow in zip(R, cells, padj)]
pd.DataFrame([dict(condition=lab, variant=v, rel=c[0], wins=c[1], p=c[2], p_holm=pa)
              for (lab, _), row, prow in zip(R, cells, padj) for v, c, pa in zip(VARIANTS, row, prow)]
             ).to_csv("results/tables/sc_table2_holm.csv", index=False)
t2 = ("\\begin{tabular}{lccc}\\toprule\n"
      "Condition & Automation head only & Reviewer head only & Both heads (proposed) \\\\\\midrule\n" + "\n".join(lines) +
      "\n\\bottomrule\\end{tabular}")
open("results/sc_tables.tex", "w").write("\\newcommand{\\TableOne}{%\n" + t1 + "}\n\\newcommand{\\TableTwo}{%\n" + t2 + "}\n")
print(t1); print(t2)
