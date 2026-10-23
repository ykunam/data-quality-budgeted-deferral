"""Produce every table/number used in the manuscript from result CSVs -> results/tables/*.csv + numbers.json"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import json, os
import numpy as np, pandas as pd
from dqd import stats as ST
from dqd import core as C

os.makedirs("results/tables", exist_ok=True)
NUM = {}
ORIG = ["german", "australian", "default"]
NONCLEAN = C.FAMILY_A + C.FAMILY_B
MAIN_METHODS = ["automation_only", "random", "confidence", "chow_risk", "quality_only", "sh_quality",
                "l2d_ce", "l2d_ova", "2h_rich_gorder", "2h_prob", "2h_quality", "oracle"]
LABEL = {"automation_only": "Automation only (no rules)", "random": "Random + rules", "confidence": "Confidence",
         "chow_risk": "Chow cost risk", "quality_only": "Quality only", "sh_quality": "Single-head gain (earlier draft)",
         "sh_prob": "Single-head, probability only", "sh_feature": "Single-head, feature-aware",
         "l2d_ce": "L2D-CE (Mozannar & Sontag)", "l2d_ova": "L2D-OvA (Verma & Nalisnick)",
         "2h_rich_gorder": "Differential triage (Raghu et al.)", "2h_prob": "Two-head, probability only",
         "2h_quality": "Two-head, quality-aware (proposed)", "2h_feature": "Two-head, feature-aware",
         "oracle": "Oracle (labels; bound)"}
REV = ["constant", "quality", "feature", "correlated", "adverse"]
REVL = {"constant": "Constant", "quality": "Quality-coupled", "feature": "Feature-dep.", "correlated": "AI-correlated",
        "adverse": "Adverse"}

df = pd.read_csv("results/static_logs.csv.gz")
df["family"] = np.where(df.condition.isin(C.FAMILY_A), "A", np.where(df.condition.isin(C.FAMILY_B), "B", "clean"))


def seedmean(d, by=()):
    """Average to one value per seed (and optional keys) giving equal weight to dataset/condition/reviewer cells."""
    return d.groupby(["seed", "method", *by]).cost.mean().reset_index()


def paired(d, a, b, by=()):
    """cost(b) - cost(a) per seed; positive favours a."""
    s = seedmean(d[d.method.isin([a, b])], by)
    w = s.pivot_table(index=["seed", *by], columns="method", values="cost").reset_index()
    w["diff"] = w[b] - w[a]
    return w


# ------------------------------------------------------------------ Table 5: main results by reviewer
prim = df[(df.dataset.isin(ORIG)) & (df.condition.isin(NONCLEAN)) & (df.capacity == 0.2)]
t5 = prim.groupby(["method", "reviewer"]).cost.mean().unstack()[REV]
t5["Macro"] = t5.mean(1)
t5 = t5.loc[MAIN_METHODS]
t5.index = [LABEL[m] for m in t5.index]
t5.round(4).to_csv("results/tables/t5_main_by_reviewer.csv")
print(t5.round(4))
rank = prim[~prim.method.isin(["oracle", "automation_only"])].groupby(["method"]).cost.mean().sort_values()
print(rank.round(4))

# review/hold summary for proposed
ops = prim.groupby("method")[["review", "hold", "violation"]].mean()
NUM["prop_review"] = ops.loc["2h_quality", "review"]; NUM["prop_hold"] = ops.loc["2h_quality", "hold"]

# ------------------------------------------------------------------ Table 6: paired comparisons
comps = ["sh_quality", "l2d_ce", "l2d_ova", "2h_rich_gorder", "chow_risk", "confidence", "2h_prob", "automation_only"]
rows = []
for c in comps:
    w = paired(prim, "2h_quality", c)
    m, lo, hi, p = ST.corrected_t(w["diff"])
    rows.append(dict(comparator=LABEL[c], diff=m, lo=lo, hi=hi, p=p, wins=int((w["diff"] > 0).sum()),
                     rel=100 * m / w[c].mean()))
t6 = pd.DataFrame(rows); t6["p_holm"] = ST.holm(t6.p)
t6.to_csv("results/tables/t6_paired.csv", index=False)
print(t6.round(4))

# per reviewer and family breakdown of proposed vs key comparators
rows = []
for rv in REV:
    for fam in ["A", "B"]:
        sub = prim[(prim.reviewer == rv) & (prim.family == fam)]
        for c in ["2h_prob", "chow_risk", "l2d_ce", "sh_quality"]:
            w = paired(sub, "2h_quality", c)
            m, lo, hi, p = ST.corrected_t(w["diff"])
            rows.append(dict(reviewer=rv, family=fam, comparator=c, diff=m, lo=lo, hi=hi, p=p,
                             wins=int((w["diff"] > 0).sum())))
tb = pd.DataFrame(rows); tb.to_csv("results/tables/t_breakdown.csv", index=False)

# ------------------------------------------------------------------ quality value: 2h_prob - 2h_quality by condition x reviewer
rows = []
for cap in [0.05, 0.1, 0.2, 0.3]:
    for cond in ["clean"] + NONCLEAN:
        for rv in REV:
            sub = df[(df.dataset.isin(ORIG)) & (df.capacity == cap) & (df.condition == cond) & (df.reviewer == rv)]
            w = paired(sub, "2h_quality", "2h_prob")
            m, lo, hi, p = ST.corrected_t(w["diff"])
            rows.append(dict(capacity=cap, condition=cond, reviewer=rv, diff=m, lo=lo, hi=hi, p=p,
                             rel=100 * m / w["2h_prob"].mean(), wins=int((w["diff"] > 0).sum())))
qv = pd.DataFrame(rows); qv.to_csv("results/tables/quality_value.csv", index=False)
print(qv[qv.capacity == 0.2].pivot_table(index="condition", columns="reviewer", values="rel").round(2))

# hypothesis tests H1/H2 (20% capacity)
def hyp(sub):
    w = paired(sub, "2h_quality", "2h_prob"); m, lo, hi, p = ST.corrected_t(w["diff"])
    return dict(diff=m, lo=lo, hi=hi, p=p, rel=100 * m / w["2h_prob"].mean(), wins=int((w["diff"] > 0).sum()))
H = {}
H["H1"] = hyp(prim[(prim.reviewer == "quality") & (prim.family == "A")])
H["H2_decoupled_A"] = hyp(prim[(prim.reviewer != "quality") & (prim.family == "A")])
H["H2_coupled_B"] = hyp(prim[(prim.reviewer == "quality") & (prim.family == "B")])
H["H2_decoupled_B"] = hyp(prim[(prim.reviewer != "quality") & (prim.family == "B")])
for rv in REV:
    for fam in "AB":
        H[f"{rv}_{fam}"] = hyp(prim[(prim.reviewer == rv) & (prim.family == fam)])
# H3 overload ordering
sh = df[(df.dataset.isin(ORIG)) & (df.condition == "shift") & (df.capacity == 0.2)]
w = paired(sh, "2h_quality", "2h_quality_gorder"); m, lo, hi, p = ST.corrected_t(w["diff"])
H["H3"] = dict(diff=m, lo=lo, hi=hi, p=p, rel=100 * m / w["2h_quality_gorder"].mean(), wins=int((w["diff"] > 0).sum()))
for rv in REV:
    w = paired(sh[sh.reviewer == rv], "2h_quality", "2h_quality_gorder"); m, lo, hi, p = ST.corrected_t(w["diff"])
    H[f"H3_{rv}"] = dict(diff=m, lo=lo, hi=hi, p=p, wins=int((w["diff"] > 0).sum()))
# H4 single vs two head (main protocol)
w = paired(prim, "2h_quality", "sh_quality"); m, lo, hi, p = ST.corrected_t(w["diff"])
H["H4_main"] = dict(diff=m, lo=lo, hi=hi, p=p, rel=100 * m / w["sh_quality"].mean(), wins=int((w["diff"] > 0).sum()))
NUM["H"] = H
print(json.dumps(H, indent=1, default=float)[:3000])

# ------------------------------------------------------------------ 2x2 ablation quality x rules
ab = df[(df.dataset.isin(ORIG)) & (df.capacity == 0.2) & (df.condition.isin(["mixed", "shift", "realistic"]))
        & df.method.isin(["2h_prob", "2h_quality", "2h_prob_norules", "2h_quality_norules"])]
t7 = ab.groupby(["condition", "method"])[["cost", "review", "hold", "violation"]].mean().reset_index()
t7.to_csv("results/tables/t7_ablation.csv", index=False)
print(t7.round(4))

# ------------------------------------------------------------------ capacity curves (figure data)
cc = df[(df.dataset.isin(ORIG)) & (df.condition.isin(NONCLEAN))].groupby(["reviewer", "capacity", "method", "seed"]).cost.mean().reset_index()
cc.to_csv("results/tables/capacity_curves_seed.csv", index=False)

# ------------------------------------------------------------------ HMEQ external
hm = df[(df.dataset == "hmeq") & (df.capacity == 0.2)]
th = hm.groupby(["method", "condition"]).cost.mean().unstack()
th = th[["clean"] + NONCLEAN].loc[MAIN_METHODS]
th["Mean (all)"] = th.mean(1)
th.to_csv("results/tables/t8_hmeq.csv")
rows = []
for c in ["2h_prob", "chow_risk", "l2d_ce", "sh_quality", "2h_rich_gorder", "confidence"]:
    for name, sub in [("natural", hm[hm.condition == "clean"]), ("all", hm)]:
        w = paired(sub, "2h_quality", c); m, lo, hi, p = ST.corrected_t(w["diff"])
        rows.append(dict(comparator=c, subset=name, diff=m, lo=lo, hi=hi, p=p, wins=int((w["diff"] > 0).sum())))
pd.DataFrame(rows).to_csv("results/tables/t8b_hmeq_paired.csv", index=False)
print(pd.DataFrame(rows).round(4))
# HMEQ natural: mandatory fraction, mean u
NUM["hmeq_natural"] = hm[(hm.condition == "clean") & (hm.method == "2h_quality")][["d_mand", "d_u", "d_v", "cost", "review", "hold"]].mean().to_dict()

# diagnostics per condition
dg = df[(df.method == "2h_quality") & (df.capacity == 0.2) & (df.reviewer == "quality")].groupby(["dataset", "condition"])[
    ["d_mand", "d_u", "d_v", "d_defect", "d_visible", "d_ai_err"]].mean()
dg.to_csv("results/tables/diag_conditions.csv")
print(dg.round(3))

# ------------------------------------------------------------------ protocol comparison (oracle targets vs logs)
if os.path.exists("results/static_oracle.csv.gz"):
    do = pd.read_csv("results/static_oracle.csv.gz")
    po = do[(do.dataset.isin(ORIG)) & (do.condition.isin(C.FAMILY_A)) & (do.capacity == 0.2)]
    pl = df[(df.dataset.isin(ORIG)) & (df.condition.isin(C.FAMILY_A)) & (df.capacity == 0.2)]
    rows = []
    for rv in REV + ["all"]:
        a = po if rv == "all" else po[po.reviewer == rv]; b = pl if rv == "all" else pl[pl.reviewer == rv]
        for m in ["sh_quality", "sh_feature", "sh_prob", "2h_quality", "2h_prob", "confidence", "chow_risk"]:
            rows.append(dict(reviewer=rv, method=m, oracle=a[a.method == m].cost.mean(), logs=b[b.method == m].cost.mean()))
    tp = pd.DataFrame(rows); tp.to_csv("results/tables/t_protocol.csv", index=False)
    print(tp.round(4))
    # replication of the original primary comparison: quality reviewer, family A, 20%: feature gain - quality gain
    q = po[po.reviewer == "quality"]
    w = paired(q, "sh_quality", "sh_feature"); m, lo, hi, p = ST.corrected_t(w["diff"]); lo2, hi2 = ST.naive_ci(w["diff"])
    NUM["replication"] = dict(diff=m, lo=lo, hi=hi, p=p, naive_lo=lo2, naive_hi=hi2,
                              sh_quality=q[q.method == "sh_quality"].cost.mean(), sh_feature=q[q.method == "sh_feature"].cost.mean(),
                              confidence=q[q.method == "confidence"].cost.mean(), chow=q[q.method == "chow_risk"].cost.mean(),
                              by_ds={ds: q[(q.dataset == ds)].groupby("method").cost.mean()[["sh_quality", "sh_feature", "confidence", "chow_risk"]].to_dict() for ds in ORIG})
    print(NUM["replication"])

json.dump(NUM, open("results/numbers.json", "w"), indent=1, default=float)
