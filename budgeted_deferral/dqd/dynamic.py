"""Multi-period backlog simulation (managerial outcomes).

Records arrive in daily batches; mandatory-review records that cannot be reviewed are
carried forward as backlog rather than written off.  A data-quality deterioration episode
is imposed on a subset of days.  The same fitted router is used throughout (no refitting)."""
from __future__ import annotations
import zlib
import numpy as np
from . import core as C
from . import static as S


def schedule(T=40):
    return ["mixed"] * 10 + ["shift"] * 10 + ["mixed"] * (T - 20)


def arrivals(P, R, reviewer, costs=C.Costs(), n_day=100, T=40, rules=S.Rules(), seed_shift=0):
    """Pre-generate the arrival stream (independent of the routing policy)."""
    X, y, (tr, ca, ga, te), Q, base = P["X"], P["y"], P["idx"], P["Q"], P["base"]
    rng = np.random.default_rng(P["seed"] * 7777 + seed_shift)
    days = []
    for day, cond in enumerate(schedule(T)):
        idx = rng.choice(te, n_day, replace=True)
        Xt, _ = C.corrupt(X[idx], y[idx], cond, rng, Q)
        D = dict(X=Xt, y=y[idx], Xclean=X[idx]); S.feats(D, base, Q, costs)
        D["p_clean"] = base.proba(X[idx])
        e = R["ctx"].error(reviewer, D["u"], D["v"], D["Xclean"], D["yh"], D["y"], D["p_clean"])
        la_hat = R["2h_quality_A"].predict(D["reps"]["quality"])
        lh_hat = R["2h_quality_H"].predict(D["reps"]["quality"])
        days.append((cond, dict(y=D["y"], la=D["la"], yh=D["yh"], e=e, g=la_hat - lh_hat - costs.review,
                                lh_hat=lh_hat, m=rules(D["u"], D["v"]), age=np.zeros(n_day, int),
                                arr=np.full(n_day, day), wrong=rng.random(n_day))))
    return days


def km_quantile(dur, event, q):
    """Kaplan-Meier time by which a fraction q of cases is resolved; inf if not reached (censoring)."""
    order = np.lexsort((-event, dur)); dur, event = dur[order], event[order]
    surv, n_at_risk = 1.0, len(dur)
    for t in np.unique(dur):
        at = dur == t; d = event[at].sum()
        if n_at_risk > 0 and d > 0:
            surv *= 1 - d / n_at_risk
        if 1 - surv >= q - 1e-12:
            return float(t)
        n_at_risk -= at.sum()
    return float("inf")


def cohort_metrics(ev, T, sla=2):
    """Arrival-cohort service measures for mandatory records, counting unresolved cases.
    SLA attainment uses only cohorts that could be observed for the full SLA window."""
    arr, dur, res = ev[:, 0], ev[:, 1], ev[:, 2].astype(bool)
    elig = arr <= T - 1 - sla
    met = res & (dur <= sla)
    return dict(mand_arrivals=int(len(ev)),
                cohort_sla2=float(met[elig].mean()) if elig.any() else float("nan"),
                cohort_resolved7=float((res & (dur <= 7))[arr <= T - 8].mean()) if (arr <= T - 8).any() else float("nan"),
                cohort_unresolved=float((~res).mean()) if len(ev) else 0.0,
                km_median=km_quantile(dur, res.astype(int), 0.5),
                km_p95=km_quantile(dur, res.astype(int), 0.95))


def simulate(days, cap, order, costs=C.Costs(), n_day=100, wait_cost=0.25):
    B = int(round(cap * n_day))
    T = len(days)
    backlog = None
    log = []
    tot = dict(auto=0.0, review=0.0, fee=0.0, wait=0.0, arrivals=0, completed=0, overrides=0, reviewed=0)
    waits = []
    events = []                                      # (arrival day, duration, resolved?) for every mandatory record
    for day, (cond, new) in enumerate(days):
        tot["arrivals"] += len(new["y"])
        cur = new if backlog is None else {k: np.concatenate([backlog[k], new[k]]) for k in new}
        n = len(cur["y"])
        if order == "fifo":
            mand = cur["age"] * 1e3 - cur["lh_hat"]          # oldest first, then cheapest review
        elif order == "cost":
            mand = -cur["lh_hat"]                            # static exact ordering
        else:
            mand = cur["g"]                                  # original gain ordering
        r, h = C.allocate(cur["m"], B, cur["g"], cur["g"] > 0, mand)
        a = ~r & ~h
        w = C.Costs.weight(costs, cur["y"])
        tot["auto"] += (a * cur["la"]).sum()
        tot["review"] += (r * w * cur["e"]).sum()
        tot["fee"] += r.sum() * costs.review
        tot["wait"] += h.sum() * wait_cost
        tot["completed"] += (r | a).sum()
        rev_dec = np.where(cur["wrong"] < cur["e"], 1 - cur["y"], cur["y"])
        tot["overrides"] += (r & (rev_dec != cur["yh"])).sum(); tot["reviewed"] += r.sum()
        waits += list(cur["age"][r & cur["m"]])
        rm = r & cur["m"]
        events += [(a_, d_, 1) for a_, d_ in zip(cur["arr"][rm], cur["age"][rm])]
        log.append(dict(day=day, cond=cond, backlog_in=0 if backlog is None else len(backlog["y"]),
                        mand_new=int(new["m"].sum()), reviewed=int(r.sum()), held=int(h.sum()), auto=int(a.sum())))
        backlog = {k: v[h] for k, v in cur.items()}
        backlog["age"] = backlog["age"] + 1
    left = len(backlog["y"])
    unresolved = left * costs.hold
    waits = np.array(waits) if waits else np.array([0])
    events += [(a_, d_, 0) for a_, d_ in zip(backlog["arr"], backlog["age"])]   # censored at horizon
    coh = cohort_metrics(np.array(events, float).reshape(-1, 3), T)
    total_cost = tot["auto"] + tot["review"] + tot["fee"] + tot["wait"] + unresolved
    out = dict(cost_per_arrival=total_cost / tot["arrivals"],
               cost_per_completed=(total_cost - unresolved) / max(tot["completed"], 1),
               completed_frac=tot["completed"] / tot["arrivals"],
               unresolved_end=left, unresolved_frac=left / tot["arrivals"],
               # conditional on resolution (resolved mandatory cases only)
               wait_mean_resolved=waits.mean(), wait_p95_resolved=np.quantile(waits, 0.95),
               wait_max_resolved=waits.max(), sla2_resolved=(waits <= 2).mean(),
               **coh,
               override_rate=tot["overrides"] / max(tot["reviewed"], 1),
               util=tot["reviewed"] / (B * T) if B else 0.0,
               peak_backlog=max(l["backlog_in"] for l in log),
               mand_rate_mixed=np.mean([l["mand_new"] for l in log if l["cond"] == "mixed"]) / n_day,
               mand_rate_shift=np.mean([l["mand_new"] for l in log if l["cond"] == "shift"]) / n_day)
    return out, log


def run(ds, seed, reviewers=("quality", "feature"), caps=(0.1, 0.2, 0.3, 0.4, 0.5, 0.7),
        orders=("fifo", "cost", "gain"), costs=C.Costs()):
    P = S.prepare(ds, seed, costs)
    rows, logs = [], []
    for rv in reviewers:
        R = S.fit_router(P, rv, costs, "logs", 0.4, l2d=False, reps_needed=["quality"])
        days = arrivals(P, R, rv, costs, seed_shift=zlib.crc32(rv.encode()) % 1000)
        for cap in caps:
            for od in orders:
                o, lg = simulate(days, cap, od, costs)
                rows.append(dict(dataset=ds, seed=seed, reviewer=rv, capacity=cap, order=od, **o))
                if seed == 2:
                    logs += [dict(dataset=ds, seed=seed, reviewer=rv, capacity=cap, order=od, **l) for l in lg]
    return rows, logs
