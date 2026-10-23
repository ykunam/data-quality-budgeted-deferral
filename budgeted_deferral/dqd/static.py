"""Static (single-batch) experiment: all routing methods under matched data, information,
costs, rules and capacity.  One call = one (dataset, seed) and returns a list of row dicts."""
from __future__ import annotations
import zlib
import numpy as np
from . import core as C

CAPACITIES = [0.05, 0.10, 0.20, 0.30]


class Rules:
    def __init__(self, u_thr=0.5, v_thr=0.25, on=True):
        self.u_thr, self.v_thr, self.on = u_thr, v_thr, on

    def __call__(self, u, v):
        if not self.on:
            return np.zeros(len(u), bool)
        return (u >= self.u_thr) | (v >= self.v_thr)


def prepare(ds, seed, costs=C.Costs(), gain_frac=1.0):
    """Fit everything that does not depend on the reviewer."""
    X, y = C.load(ds)
    tr, ca, ga, te = C.group_split(X, y, seed)
    if gain_frac < 1.0:                                   # data-volume experiment: subsample gain partition
        ga = np.random.default_rng(seed + 555).permutation(ga)[:max(40, int(gain_frac * len(ga)))]
    Q = C.Quality(X[tr])
    base = C.Base(X[tr], y[tr], seed)
    rng = np.random.default_rng(seed * 7919 + 1)
    Xc = np.vstack([C.corrupt(X[ca], y[ca], c, rng, Q)[0] for c in C.TRAIN_CONDITIONS])
    base.calibrate(Xc, np.tile(y[ca], len(C.TRAIN_CONDITIONS)))
    # expanded gain-fitting partition
    parts = [C.corrupt(X[ga], y[ga], c, rng, Q)[0] for c in C.TRAIN_CONDITIONS]
    G = dict(X=np.vstack(parts), y=np.tile(y[ga], 4), Xclean=np.tile(X[ga], (4, 1)))
    feats(G, base, Q, costs)
    G["p_clean"] = np.tile(base.proba(X[ga]), 4)
    return dict(X=X, y=y, idx=(tr, ca, ga, te), Q=Q, base=base, G=G, ds=ds, seed=seed)


def feats(D, base, Q, costs):
    p = base.proba(D["X"])
    u, v = Q.measure(D["X"])
    yh = (p >= costs.threshold).astype(int)
    s = np.minimum(costs.fn * p, costs.fp * (1 - p))            # Bayes risk of automation (Chow)
    D.update(p=p, u=u, v=v, yh=yh, s=s, la=C.Costs.weight(costs, D["y"]) * (yh != D["y"]))
    D["reps"] = {k: f(p, s, u, v, yh, D["X"], Q) for k, f in C.REPS.items()}
    D["l2d_in"] = np.c_[Q.scaled(D["X"]), u, v, p]
    return D


def fit_router(P, reviewer, costs, protocol="logs", log_frac=0.4, l2d=True, reps_needed=None):
    """Fit all learned routers for one reviewer.  protocol='logs': the learner sees a single
    sampled reviewer decision for a random log_frac of gain-fitting records (noisy, incomplete);
    protocol='oracle': expected reviewer loss for every record (the original, optimistic setup)."""
    G, Q, seed = P["G"], P["Q"], P["seed"]
    ctx = C.ReviewerContext(Q, seed, Q.d)
    e = ctx.error(reviewer, G["u"], G["v"], G["Xclean"], G["yh"], G["y"], G["p_clean"])
    w = C.Costs.weight(costs, G["y"])
    rng = np.random.default_rng(seed * 104729 + C.REVIEWERS.index(reviewer))
    n = len(G["y"])
    if protocol == "logs":
        logged = rng.random(n) < log_frac
        correct = rng.random(n) >= e
        lh_t = w * (~correct)
    else:
        logged = np.ones(n, bool); correct = None
        lh_t = w * e
    N = logged.sum()
    R = {}
    reps = reps_needed or ["prob", "quality", "feature", "rich"]
    for k in reps:
        Z = G["reps"][k]
        # single-head gain: needs both outcome and reviewer feedback -> logged rows only
        if k != "rich":
            R[f"sh_{k}"] = C.hgb_reg(N, seed).fit(Z[logged], (G["la"] - lh_t - costs.review)[logged])
        # two-head: automation-loss head on all labelled rows, reviewer-loss head on logged rows
        R[f"2h_{k}_A"] = C.hgb_reg(n, seed).fit(Z, G["la"])
        R[f"2h_{k}_H"] = C.hgb_reg(N, seed).fit(Z[logged], lh_t[logged])
    if l2d and protocol == "logs":
        Xl = G["l2d_in"][logged]
        R["l2d_ce"] = C.fit_l2d_ce(Xl, G["y"][logged], lh_t[logged], costs, seed)
        R["l2d_ova"] = C.fit_l2d_ova(Xl, G["y"][logged], correct[logged], costs, seed)
    R["ctx"] = ctx
    return R


def test_set(P, cond, costs):
    X, y, (tr, ca, ga, te), Q, base = P["X"], P["y"], P["idx"], P["Q"], P["base"]
    rng = np.random.default_rng(P["seed"] * 31337 + zlib.crc32(cond.encode()) % 9973)
    Xt, defect = C.corrupt(X[te], y[te], cond, rng, Q)
    T = dict(X=Xt, y=y[te], Xclean=X[te], defect=defect)
    feats(T, base, Q, costs)
    T["p_clean"] = base.proba(X[te])
    T["rseed"] = P["seed"] * 1009 + zlib.crc32(cond.encode()) % 997
    return T


def route_scores(T, R, costs):
    """Scores used by each method: (opt_score, admit, mand_score, rules_on)."""
    n = len(T["y"])
    rnd = np.random.default_rng(T["rseed"]).random(n)
    S = {}
    conf = -np.abs(T["p"] - costs.threshold)
    S["random"] = (rnd, np.ones(n, bool), rnd, True)
    S["confidence"] = (conf, np.ones(n, bool), conf, True)
    S["chow_risk"] = (T["s"], np.ones(n, bool), T["s"], True)
    S["quality_only"] = (T["u"] + T["v"], np.ones(n, bool), T["u"] + T["v"], True)
    for k in ["prob", "quality", "feature"]:
        if f"sh_{k}" in R:
            g = R[f"sh_{k}"].predict(T["reps"][k])
            S[f"sh_{k}"] = (g, g > 0, g, True)
    for k in ["prob", "quality", "feature", "rich"]:
        if f"2h_{k}_A" in R:
            la = R[f"2h_{k}_A"].predict(T["reps"][k]); lh = R[f"2h_{k}_H"].predict(T["reps"][k])
            g = la - lh - costs.review
            S[f"2h_{k}"] = (g, g > 0, -lh, True)                 # exact overload ordering
            S[f"2h_{k}_gorder"] = (g, g > 0, g, True)            # original overload ordering
            S[f"2h_{k}_norules"] = (g, g > 0, -lh, False)
    if "2h_quality_A" in R and "2h_prob_A" in R:     # where does quality information act?
        qa, qh = R["2h_quality_A"].predict(T["reps"]["quality"]), R["2h_quality_H"].predict(T["reps"]["quality"])
        pa, ph = R["2h_prob_A"].predict(T["reps"]["prob"]), R["2h_prob_H"].predict(T["reps"]["prob"])
        g = qa - ph - costs.review; S["2h_qA"] = (g, g > 0, -ph, True)
        g = pa - qh - costs.review; S["2h_qH"] = (g, g > 0, -qh, True)
    for k in ["l2d_ce", "l2d_ova"]:
        if k in R:
            sc = R[k](T["l2d_in"])
            S[k] = (sc, sc > 0, sc, True)
    return S


def run(ds, seed, conditions, reviewers=C.REVIEWERS, caps=CAPACITIES, costs=C.Costs(),
        rules=Rules(), protocol="logs", log_frac=0.4, l2d=True, P=None, tag="main", keep=None):
    P = P or prepare(ds, seed, costs)
    rows = []
    tests = {c: test_set(P, c, costs) for c in conditions}
    for rv in reviewers:
        R = fit_router(P, rv, costs, protocol, log_frac, l2d)
        for cond, T in tests.items():
            e = R["ctx"].error(rv, T["u"], T["v"], T["Xclean"], T["yh"], T["y"], T["p_clean"])
            lh = C.Costs.weight(costs, T["y"]) * e
            m_rules = rules(T["u"], T["v"])
            S = route_scores(T, R, costs)
            if keep:
                S = {k: S[k] for k in S if k in keep}
            true_g = T["la"] - lh - costs.review
            S["oracle"] = (true_g, true_g > 0, -lh, True)
            diag = dict(mand=m_rules.mean(), u=T["u"].mean(), v=T["v"].mean(), defect=T["defect"].mean(),
                        visible=np.corrcoef(T["defect"], T["u"] + T["v"])[0, 1] if T["defect"].std() > 0 and (T["u"] + T["v"]).std() > 0 else np.nan,
                        rev_err=e.mean(), ai_err=(T["yh"] != T["y"]).mean())
            n = len(T["y"])
            for b in caps:
                B = int(np.floor(b * n))
                base_row = dict(tag=tag, dataset=ds, seed=seed, protocol=protocol, reviewer=rv,
                                condition=cond, capacity=b, n=n, **{f"d_{k}": v for k, v in diag.items()})
                z = np.zeros(n, bool)
                rows.append({**base_row, "method": "automation_only",
                             **C.evaluate(z, z, T["la"], lh, m_rules, costs)})
                for name, (opt, adm, mand, on) in S.items():
                    m = m_rules if on else np.zeros(n, bool)
                    r, h = C.allocate(m, B, opt, adm, mand)
                    rows.append({**base_row, "method": name,
                                 **C.evaluate(r, h, T["la"], lh, m_rules, costs)})
    return rows
