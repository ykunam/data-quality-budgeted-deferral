"""E3 log completeness, E4 governance-rule alternatives, E5 cost re-optimisation (refit)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import sys, time, zlib
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from dqd import static as S, core as C

DATASETS = ["german", "australian", "default"]
SEEDS = range(2, 12)
METHODS = ["random", "confidence", "chow_risk", "sh_quality", "2h_prob", "2h_quality", "2h_rich", "l2d_ce", "l2d_ova"]
CONDS = ["mixed", "shift", "realistic"]
RULESETS = {"none": S.Rules(on=False), "lenient": S.Rules(0.7, 0.4), "main": S.Rules(0.5, 0.25),
            "strict": S.Rules(0.3, 0.15)}


def e3(ds, seed):
    P = S.prepare(ds, seed); rows = []
    for lf in [0.1, 0.4, 1.0]:
        rows += S.run(ds, seed, ["mixed", "realistic"], reviewers=["quality", "feature"], caps=[0.2],
                      log_frac=lf, l2d=True, P=P, tag=f"logfrac={lf}",
                      keep=["chow_risk", "sh_quality", "2h_quality", "2h_prob", "l2d_ce", "l2d_ova"])
    for r in rows:
        r["log_frac"] = float(r["tag"].split("=")[1])
    return rows


def e4(ds, seed):
    P = S.prepare(ds, seed); costs = C.Costs(); rows = []
    tests = {c: S.test_set(P, c, costs) for c in CONDS}
    for rv in ["quality", "feature"]:
        R = S.fit_router(P, rv, costs)
        for cond, T in tests.items():
            e = R["ctx"].error(rv, T["u"], T["v"], T["Xclean"], T["yh"], T["y"], T["p_clean"])
            lh = C.Costs.weight(costs, T["y"]) * e
            Sc = S.route_scores(T, R, costs)
            n = len(T["y"]); B = int(0.2 * n)
            for rname, rule in RULESETS.items():
                m = rule(T["u"], T["v"])
                for meth in METHODS:
                    opt, adm, mand, _ = Sc[meth]
                    r, h = C.allocate(m, B, opt, adm, mand)
                    ev = C.evaluate(r, h, T["la"], lh, m, costs)
                    # also: share of truly defective records automated (defect fraction > 0.2)
                    a = ~r & ~h
                    bad = T["defect"] > 0.2
                    rows.append(dict(dataset=ds, seed=seed, reviewer=rv, condition=cond, rules=rname,
                                     method=meth, mand=m.mean(), auto_defective=(a & bad).sum() / max(bad.sum(), 1),
                                     **ev))
    return rows


def e5(ds, seed):
    rows = []
    settings = [("ratio", dict(fn=f, fp=1.0, review=0.05, hold=1.5)) for f in [2.0, 5.0, 10.0]] + \
               [("review_fee", dict(fn=5.0, fp=1.0, review=c, hold=1.5)) for c in [0.0, 0.2]] + \
               [("hold", dict(fn=5.0, fp=1.0, review=0.05, hold=h)) for h in [0.5, 3.0]]
    for fam, kw in settings:
        costs = C.Costs(**kw)
        P = S.prepare(ds, seed, costs)                    # threshold, targets and routers refit
        rr = S.run(ds, seed, CONDS, reviewers=["quality", "feature"], caps=[0.2], costs=costs, P=P,
                   tag=f"{fam}", keep=METHODS)
        for r in rr:
            r.update(family=fam, fn=kw["fn"], cR=kw["review"], cH=kw["hold"])
        rows += rr
    return rows


if __name__ == "__main__":
    which = sys.argv[1]
    f = dict(e3=e3, e4=e4, e5=e5)[which]
    t = time.time()
    out = Parallel(n_jobs=2)(delayed(f)(d, s) for d in DATASETS for s in SEEDS)
    df = pd.DataFrame([r for o in out for r in o])
    df.to_csv(f"results/{which}.csv.gz", index=False)
    print(which, len(df), round(time.time() - t), "s")
