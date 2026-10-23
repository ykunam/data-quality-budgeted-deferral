"""Core library for data-quality-aware budgeted human deferral (revised study).

Everything here is label-free at allocation time; labels enter only model
fitting and retrospective evaluation.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# ----------------------------------------------------------------------------- costs
class Costs:
    def __init__(self, fn=5.0, fp=1.0, review=0.05, hold=1.5):
        self.fn, self.fp, self.review, self.hold = fn, fp, review, hold

    @property
    def threshold(self):            # Bayes threshold for the automated decision
        return self.fp / (self.fp + self.fn)

    def weight(self, y):            # loss of an error on a record with label y
        return np.where(y == 1, self.fn, self.fp)


# ----------------------------------------------------------------------------- data
def load(name):
    if name == "german":
        a = np.loadtxt(os.path.join(DATA, "german.data-numeric"))
        X, y = a[:, :-1], (a[:, -1] == 2).astype(int)
    elif name == "australian":
        a = np.loadtxt(os.path.join(DATA, "australian.dat"))
        X, y = a[:, :-1], a[:, -1].astype(int)
    elif name == "default":
        d = pd.read_csv(os.path.join(DATA, "default.csv"), skiprows=1)
        y = d.iloc[:, -1].to_numpy().astype(int)
        X = d.iloc[:, 1:-1].to_numpy().astype(float)          # identifier removed
    elif name == "hmeq":
        d = pd.read_csv(os.path.join(DATA, "hmeq.csv"))
        y = d["BAD"].to_numpy().astype(int)
        d = d.drop(columns="BAD")
        d["REASON"] = d["REASON"].map({"DebtCon": 0, "HomeImp": 1})
        jobs = {j: i for i, j in enumerate(sorted(d["JOB"].dropna().unique()))}
        d["JOB"] = d["JOB"].map(jobs)
        X = d.to_numpy().astype(float)                       # natural missingness kept
    else:
        raise ValueError(name)
    return X.astype(float), y


def group_split(X, y, seed, fr=(0.45, 0.15, 0.20, 0.20)):
    """Group feature-identical records (incl. conflicting labels), stratify groups
    by majority label, and assign whole groups to roles."""
    key = pd.util.hash_pandas_object(pd.DataFrame(np.nan_to_num(X, nan=-9.87e9)), index=False).to_numpy()
    _, g = np.unique(key, return_inverse=True)
    G = g.max() + 1
    size = np.bincount(g, minlength=G)
    maj = (np.bincount(g, weights=y, minlength=G) / size >= 0.5).astype(int)
    rng = np.random.default_rng(seed)
    role_of_group = np.empty(G, dtype=int)
    cuts = np.cumsum(fr)[:-1]
    for lab in (0, 1):
        idx = rng.permutation(np.where(maj == lab)[0])
        cum = np.cumsum(size[idx]) / size[idx].sum()
        role_of_group[idx] = np.searchsorted(cuts, cum - 1e-12, side="right")
    role = role_of_group[g]
    return [np.where(role == r)[0] for r in range(4)]          # train, calib, gain, test


# ----------------------------------------------------------------------------- quality
class Quality:
    """Bounds and feature typing learned from predictor-training rows only."""
    def __init__(self, Xtr):
        q01, q99 = np.nanquantile(Xtr, 0.01, axis=0), np.nanquantile(Xtr, 0.99, axis=0)
        self.t = np.maximum(q99 - q01, 1.0)
        self.lo, self.hi = q01 - 0.1 * self.t, q99 + 0.1 * self.t
        self.med = np.nanmedian(Xtr, axis=0)
        nun = np.array([len(np.unique(c[~np.isnan(c)])) for c in Xtr.T])
        self.cat = nun <= 10                                    # code-like fields
        self.codes = [np.unique(c[~np.isnan(c)]) for c in Xtr.T]
        self.d = Xtr.shape[1]

    def measure(self, X):
        miss = np.isnan(X)
        out = (~miss) & ((X < self.lo) | (X > self.hi))
        return miss.mean(1), out.sum(1) / self.d                  # u, v (all features in denominator)

    def scaled(self, X):
        Z = np.where(np.isnan(X), self.med, X)
        return np.clip((Z - self.med) / self.t, -5, 5)


# ----------------------------------------------------------------------------- corruption
# Family A: detectable defects (missing cells, out-of-range values) -- the original protocol.
# Family B: domain-valid defects -- informative missingness, stale records, inconsistent codes;
#           the last two are largely invisible to completeness/range checks.
TRAIN_CONDITIONS = ["clean", "missing", "outliers", "mixed"]
FAMILY_A = ["missing", "outliers", "mixed", "shift"]
FAMILY_B = ["informative", "stale", "inconsistent", "realistic"]


def _missing(X, rng, rates):
    M = rng.random(X.shape) < rates[:, None]
    X = X.copy(); X[M] = np.nan
    return X, M


def _outliers(X, rng, rates, Q):
    M = (rng.random(X.shape) < rates[:, None]) & ~np.isnan(X)
    off = rng.choice([-1, 1], X.shape) * rng.uniform(1.2, 2.5, X.shape) * Q.t
    X = X.copy(); X[M] = X[M] + off[M]
    return X, M


def _stale(X, rng, prob, Q):
    """An outdated snapshot: for affected records, continuous fields are deflated by a
    record-level factor (values remain plausible and usually in range)."""
    rec = rng.random(len(X)) < prob
    f = rng.uniform(0.55, 0.90, len(X))
    M = rec[:, None] & (~Q.cat)[None, :] & ~np.isnan(X)
    X = X.copy(); X = np.where(M, X * f[:, None], X)
    return X, M


def _inconsistent(X, rng, rates, Q):
    """Code-like fields replaced by a different *valid* code (e.g., mis-keyed category)."""
    M = (rng.random(X.shape) < rates[:, None]) & Q.cat[None, :] & ~np.isnan(X)
    X = X.copy()
    for j in np.where(Q.cat)[0]:
        rows = np.where(M[:, j])[0]
        codes = Q.codes[j]
        if len(codes) < 2 or len(rows) == 0:
            M[:, j] = False; continue
        new = rng.choice(codes, len(rows))
        same = new == X[rows, j]
        while same.any():
            new[same] = rng.choice(codes, same.sum()); same = new == X[rows, j]
        X[rows, j] = new
    return X, M


def corrupt(X, y, cond, rng, Q):
    """Return corrupted copy and the per-record fraction of truly defective cells."""
    n = len(X)
    D = np.zeros(X.shape, bool)
    if cond in ("clean", "natural"):
        return X.copy(), D.mean(1)
    if cond == "missing":
        X, M = _missing(X, rng, rng.uniform(0, 0.55, n)); D |= M
    elif cond == "outliers":
        X, M = _outliers(X, rng, rng.uniform(0, 0.18, n), Q); D |= M
    elif cond in ("mixed", "shift"):
        lo_m, hi_m, lo_o, hi_o = (0, .35, 0, .12) if cond == "mixed" else (.35, .75, .08, .25)
        X, M = _outliers(X, rng, rng.uniform(lo_o, hi_o, n), Q); D |= M
        X, M = _missing(X, rng, rng.uniform(lo_m, hi_m, n)); D |= M
    elif cond == "informative":
        base = rng.uniform(0, 0.35, n)
        X, M = _missing(X, rng, np.minimum(0.9, base * np.where(y == 1, 1.8, 0.6))); D |= M
    elif cond == "stale":
        X, M = _stale(X, rng, 0.5, Q); D |= M
    elif cond == "inconsistent":
        X, M = _inconsistent(X, rng, rng.uniform(0, 0.30, n), Q); D |= M
    elif cond == "realistic":
        X, M = _stale(X, rng, 0.3, Q); D |= M
        X, M = _inconsistent(X, rng, rng.uniform(0, 0.15, n), Q); D |= M
        base = rng.uniform(0, 0.20, n)
        X, M = _missing(X, rng, np.minimum(0.9, base * np.where(y == 1, 1.8, 0.6))); D |= M
    else:
        raise ValueError(cond)
    return X, D.mean(1)


# ----------------------------------------------------------------------------- base predictor
class Base:
    def __init__(self, Xtr, ytr, seed):
        self.clf = HistGradientBoostingClassifier(max_iter=120, max_leaf_nodes=15, learning_rate=0.07,
                                                  l2_regularization=1.0, random_state=seed).fit(Xtr, ytr)
        self.cal = None

    def _logit(self, X):
        p = np.clip(self.clf.predict_proba(X)[:, 1], 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p))[:, None]

    def calibrate(self, Xc, yc):
        self.cal = LogisticRegression(C=1.0).fit(self._logit(Xc), yc)
        return self

    def proba(self, X):
        return self.cal.predict_proba(self._logit(X))[:, 1]


# ----------------------------------------------------------------------------- reviewers
REVIEWERS = ["constant", "quality", "feature", "correlated", "adverse"]


class ReviewerContext:
    """Per-(dataset, seed) latent quantities the router never observes."""
    def __init__(self, Q, seed, d):
        rng = np.random.default_rng(10_000 + seed)
        self.w = rng.standard_normal(d) / np.sqrt(d)
        self.Q = Q

    def error(self, kind, u, v, Xclean, yhat, y, p_clean):
        if kind == "constant":
            return np.full(len(u), 0.10)
        if kind == "adverse":
            return np.full(len(u), 0.25)
        if kind == "quality":     # original: coupled to the router's observed quality signals
            return np.minimum(0.40, 0.05 + 0.35 * u + 0.25 * v)
        if kind == "feature":     # decoupled: depends on a hidden projection of clean features
            z = self.Q.scaled(Xclean) @ self.w
            z = (z - z.mean()) / (z.std() + 1e-9) if len(z) > 1 else z
            return 0.02 + 0.24 * norm.cdf(1.5 * z)
        if kind == "correlated":  # human errors concentrate where the model errs / is uncertain
            b = 1 - np.abs(2 * p_clean - 1)
            return np.minimum(0.45, 0.05 + 0.25 * (yhat != y) + 0.10 * b)
        raise ValueError(kind)


# ----------------------------------------------------------------------------- representations
def rep_prob(p, s, u, v, yh, X, Q):
    return np.c_[p, s]


def rep_quality(p, s, u, v, yh, X, Q):
    return np.c_[p, s, u, v, p * u, p * v, yh * u, yh * v]


def rep_feature(p, s, u, v, yh, X, Q):
    return np.c_[p, s, Q.scaled(X)]


def rep_rich(p, s, u, v, yh, X, Q):     # raw observed values incl. NaN + quality + probability
    return np.c_[p, s, u, v, X]


REPS = {"prob": rep_prob, "quality": rep_quality, "feature": rep_feature, "rich": rep_rich}


def hgb_reg(N, seed):
    return HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=7, learning_rate=0.06,
                                         l2_regularization=5.0, min_samples_leaf=max(20, N // 200),
                                         random_state=seed)


# ----------------------------------------------------------------------------- numpy MLP for L2D surrogates
class MLP:
    """One-hidden-layer network trained with Adam; used for the published L2D surrogates."""
    def __init__(self, d, k, hidden=32, seed=0):
        r = np.random.default_rng(seed)
        self.P = [r.standard_normal((d, hidden)) * np.sqrt(2 / d), np.zeros(hidden),
                  r.standard_normal((hidden, k)) * np.sqrt(1 / hidden), np.zeros(k)]

    def forward(self, X, P=None):
        W1, b1, W2, b2 = P or self.P
        H = np.maximum(X @ W1 + b1, 0)
        return H, H @ W2 + b2

    def fit(self, X, lossgrad, Xv, lossv, epochs=60, bs=128, lr=2e-3, wd=1e-4, seed=0, patience=8):
        r = np.random.default_rng(seed)
        m = [np.zeros_like(p) for p in self.P]; v = [np.zeros_like(p) for p in self.P]
        t = 0; best = np.inf; bestP = [p.copy() for p in self.P]; bad = 0
        for ep in range(epochs):
            idx = r.permutation(len(X))
            for st in range(0, len(X), bs):
                b = idx[st:st + bs]
                H, O = self.forward(X[b])
                G = lossgrad(O, b) / len(b)                       # dL/dO
                W1, b1, W2, b2 = self.P
                gW2 = H.T @ G + wd * W2; gb2 = G.sum(0)
                GH = (G @ W2.T) * (H > 0)
                gW1 = X[b].T @ GH + wd * W1; gb1 = GH.sum(0)
                t += 1
                for i, g in enumerate([gW1, gb1, gW2, gb2]):
                    m[i] = 0.9 * m[i] + 0.1 * g; v[i] = 0.999 * v[i] + 0.001 * g * g
                    self.P[i] -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
            L = lossv(self.forward(Xv)[1])
            if L < best - 1e-5:
                best, bestP, bad = L, [p.copy() for p in self.P], 0
            else:
                bad += 1
                if bad >= patience:
                    break
        self.P = bestP
        return self


def _softmax(O):
    O = O - O.max(1, keepdims=True); E = np.exp(O); return E / E.sum(1, keepdims=True)


def fit_l2d_ce(X, y, lh, costs, seed):
    """Cost-sensitive cross-entropy surrogate of Mozannar & Sontag (2020): options
    {predict 0, predict 1, defer}; weights max_j c_j - c_i."""
    C = np.c_[costs.fn * (y == 1), costs.fp * (y == 0), lh + costs.review]
    W = C.max(1, keepdims=True) - C
    n = len(X); r = np.random.default_rng(seed); va = r.random(n) < 0.2
    Xt, Wt, Xv, Wv = X[~va], W[~va], X[va], W[va]
    gr = lambda O, b: (_softmax(O) * Wt[b].sum(1, keepdims=True) - Wt[b])
    lv = lambda O: -(Wv * np.log(_softmax(O) + 1e-12)).sum(1).mean()
    net = MLP(X.shape[1], 3, seed=seed).fit(Xt, gr, Xv, lv, seed=seed)

    def score(Z):
        P = _softmax(net.forward(Z)[1]); return P[:, 2] - P[:, :2].max(1)
    return score


def fit_l2d_ova(X, y, correct, costs, seed):
    """One-vs-all surrogate of Verma & Nalisnick (2022) with logistic phi; examples
    weighted by the asymmetric error cost (our adaptation for the 5:1 loss)."""
    w = np.where(y == 1, costs.fn, costs.fp)
    T = np.c_[y == 0, y == 1, correct].astype(float)            # targets for the three OvA heads
    n = len(X); r = np.random.default_rng(seed); va = r.random(n) < 0.2
    sig = lambda O: 1 / (1 + np.exp(-O))
    gr = lambda O, b: (sig(O) - T[~va][b]) * w[~va][b, None]
    def lv(O):
        S = np.clip(sig(O), 1e-9, 1 - 1e-9); Tv = T[va]
        return -((Tv * np.log(S) + (1 - Tv) * np.log(1 - S)).sum(1) * w[va]).mean()
    net = MLP(X.shape[1], 3, seed=seed).fit(X[~va], gr, X[va], lv, seed=seed)

    def score(Z):
        S = sig(net.forward(Z)[1]); return S[:, 2] - S[:, :2].max(1)
    return score


# ----------------------------------------------------------------------------- allocation
def allocate(m, B, opt_score, admit, mand_score):
    """Three-action allocator.  Returns arrays (review, hold) of booleans.
    feasible (|M|<=B): review all mandatory, then up to B-|M| admitted optional records
                       with the highest opt_score;
    overload (|M|>B):  review the B mandatory records with highest mand_score, hold the rest.
    Stable ordering resolves ties."""
    n = len(m); r = np.zeros(n, bool); h = np.zeros(n, bool)
    M = np.where(m)[0]
    if len(M) <= B:
        r[M] = True
        cand = np.where(~m & admit)[0]
        k = B - len(M)
        if k > 0 and len(cand):
            order = cand[np.argsort(-opt_score[cand], kind="stable")]
            r[order[:k]] = True
    else:
        order = M[np.argsort(-mand_score[M], kind="stable")]
        r[order[:B]] = True
        h[order[B:]] = True
    return r, h


def evaluate(r, h, la, lh, m, costs):
    """Expected cost per record (expected over reviewer randomness)."""
    a = ~r & ~h
    cost = (a * la + r * (lh + costs.review) + h * costs.hold).mean()
    return dict(cost=cost, review=r.mean(), hold=h.mean(), violation=(a & m).mean(),
                auto_loss=(a * la).mean(), review_loss=(r * lh).mean())
