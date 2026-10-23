"""Statistical helpers: corrected resampled t-test (Nadeau & Bengio, 2003) and Holm correction."""
import numpy as np
from scipy import stats

TEST_TRAIN_RATIO = 0.20 / 0.80      # test share / share used for fitting (predictor+calibration+gain)


def corrected_t(diff, ratio=TEST_TRAIN_RATIO, alpha=0.05):
    """diff: per-split paired differences (J values).  Returns mean, CI low, CI high, p (two-sided)."""
    d = np.asarray(diff, float)
    J = len(d)
    m, s2 = d.mean(), d.var(ddof=1)
    se = np.sqrt((1 / J + ratio) * s2)
    if se == 0:
        return m, m, m, (1.0 if m == 0 else 0.0)
    t = m / se
    p = 2 * stats.t.sf(abs(t), J - 1)
    h = stats.t.ppf(1 - alpha / 2, J - 1) * se
    return m, m - h, m + h, p


def naive_ci(diff, alpha=0.05):
    d = np.asarray(diff, float); J = len(d)
    se = d.std(ddof=1) / np.sqrt(J)
    h = stats.t.ppf(1 - alpha / 2, J - 1) * se
    return d.mean() - h, d.mean() + h


def holm(pvals):
    p = np.asarray(pvals, float); n = len(p)
    order = np.argsort(p); adj = np.empty(n)
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, (n - k) * p[i]); adj[i] = min(1.0, run)
    return adj
