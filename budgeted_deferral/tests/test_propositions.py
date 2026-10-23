"""Brute-force checks of Proposition 1 (exact allocation, both regimes; hold-penalty invariance)
and Proposition 2 (backlog invariant to mandatory-record ordering)."""
import itertools, os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from dqd.core import allocate


def objective(act, la, lh, cR, cH):           # act: 0 automate, 1 review, 2 hold
    return np.where(act == 0, la, np.where(act == 1, lh + cR, cH)).sum()


def brute_force(la, lh, m, B, cR, cH):
    n = len(la); need_hold = max(0, int(m.sum()) - B); best = np.inf
    for act in itertools.product((0, 1, 2), repeat=n):
        act = np.array(act)
        if (act == 1).sum() > B or np.any((act == 0) & m) or np.any((act == 2) & ~m) or (act == 2).sum() != need_hold:
            continue
        best = min(best, objective(act, la, lh, cR, cH))
    return best


class Proposition1(unittest.TestCase):
    def test_exact_in_both_regimes(self):
        rng = np.random.default_rng(0); cR = 0.05
        for n in range(1, 8):
            for _ in range(40):
                la, lh = rng.exponential(1, n), rng.exponential(0.5, n)
                m = rng.random(n) < 0.5; B = int(rng.integers(0, n + 1)); cH = rng.uniform(0.2, 3)
                g = la - lh - cR
                r, h = allocate(m, B, g, g > 0, -lh)
                act = np.where(r, 1, np.where(h, 2, 0))
                self.assertAlmostEqual(objective(act, la, lh, cR, cH), brute_force(la, lh, m, B, cR, cH), places=9)

    def test_gain_ordering_can_be_suboptimal_under_overload(self):
        la, lh, m = np.array([5.0, 0.0]), np.array([1.0, 0.2]), np.array([True, True])
        g = la - lh - 0.05
        r_gain, _ = allocate(m, 1, g, g > 0, g)
        r_exact, _ = allocate(m, 1, g, g > 0, -lh)
        self.assertTrue(r_gain[0] and r_exact[1])

    def test_routes_invariant_to_hold_penalty(self):
        """The allocator's route is optimal for every hold penalty, and the optimum shifts by (|M|-B)+ * dcH."""
        rng = np.random.default_rng(1); cR = 0.05
        for _ in range(60):
            n = 6; la, lh = rng.exponential(1, n), rng.exponential(0.5, n); m = rng.random(n) < 0.6
            B = int(rng.integers(0, n)); g = la - lh - cR
            r, h = allocate(m, B, g, g > 0, -lh); act = np.where(r, 1, np.where(h, 2, 0))
            vals = []
            for cH in (0.5, 1.5, 3.0):
                opt = brute_force(la, lh, m, B, cR, cH)
                self.assertAlmostEqual(objective(act, la, lh, cR, cH), opt, places=9)
                vals.append(opt)
            self.assertAlmostEqual(vals[2] - vals[0], 2.5 * max(0, int(m.sum()) - B), places=9)


class Proposition2(unittest.TestCase):
    def test_backlog_invariant_to_mandatory_order(self):
        rng = np.random.default_rng(2)
        for _ in range(50):
            T, n, B = 15, 20, int(rng.integers(2, 12))
            days = [(rng.random(n) < rng.uniform(0, 0.9), rng.normal(size=n)) for _ in range(T)]
            traces = []
            for order in ("fifo", "random", "score"):
                orng = np.random.default_rng(3); back_m, back_age, back_s = np.zeros(0, bool), np.zeros(0), np.zeros(0)
                trace = []
                for m_new, s_new in days:
                    m = np.r_[back_m, m_new]; s = np.r_[back_s, s_new]; age = np.r_[back_age, np.zeros(n)]
                    key = age if order == "fifo" else (orng.random(len(m)) if order == "random" else s)
                    r, h = allocate(m, B, s, s > 0, key)
                    trace.append((h.sum(), r.sum(), (~h).sum()))
                    back_m, back_s, back_age = m[h], s[h], age[h] + 1
                traces.append(trace)
            self.assertEqual(traces[0], traces[1]); self.assertEqual(traces[0], traces[2])


if __name__ == "__main__":
    unittest.main(verbosity=2)
