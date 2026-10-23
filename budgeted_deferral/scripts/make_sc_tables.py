"""Write the two Short Communication tables (LaTeX) directly from seed-level results."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
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
    txt = f"{100 * m / s[b].mean():+.2f} ({int((d > 0).sum())})"
    return f"\\textbf{{{txt}}}" if p < 0.05 else txt
orig = df[df.dataset.isin(["german", "australian", "default"]) & (df.capacity == 0.2)]
R = [("Informative missingness (B)", orig[orig.condition == "informative"]),
     ("Stale records (B)", orig[orig.condition == "stale"]),
     ("Inconsistent codes (B)", orig[orig.condition == "inconsistent"]),
     ("Visible defects (A), quality-coupled reviewer", orig[orig.condition.isin(C.FAMILY_A) & (orig.reviewer == "quality")]),
     ("Visible defects (A), four decoupled reviewers", orig[orig.condition.isin(C.FAMILY_A) & (orig.reviewer != "quality")]),
     ("HMEQ, natural missingness (external)", nat)]
lines = [f"{lab} & {rel(s,'2h_qA','2h_prob')} & {rel(s,'2h_qH','2h_prob')} & {rel(s,'2h_quality','2h_prob')} \\\\" for lab, s in R]
t2 = ("\\begin{tabular}{lccc}\\toprule\n"
      "Condition & Automation head only & Reviewer head only & Both heads (proposed) \\\\\\midrule\n" + "\n".join(lines) +
      "\n\\bottomrule\\end{tabular}")
open("results/sc_tables.tex", "w").write("\\newcommand{\\TableOne}{%\n" + t1 + "}\n\\newcommand{\\TableTwo}{%\n" + t2 + "}\n")
print(t1); print(t2)
