"""Service metrics must not hide unresolved cases (conditional vs cohort measures)."""
import os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from dqd.dynamic import simulate


def synthetic_days(T=20, n=10, seed=0):
    rng = np.random.default_rng(seed); days = []
    for d in range(T):
        lh = rng.random(n)
        days.append(("shift", dict(y=np.zeros(n, int), la=np.zeros(n), yh=np.zeros(n, int), e=np.zeros(n),
                                   g=-np.ones(n), lh_hat=lh, m=np.ones(n, bool), age=np.zeros(n, int),
                                   arr=np.full(n, d), wrong=rng.random(n))))
    return days


class CohortMetrics(unittest.TestCase):
    def test_conditional_sla_can_hide_backlog_but_cohort_does_not(self):
        # every arrival is mandatory, capacity is half of arrivals, newest-cheapest served first
        out, _ = simulate(synthetic_days(), cap=0.5, order="cost", n_day=10)
        self.assertGreater(out["unresolved_frac"], 0.3)
        self.assertLess(out["cohort_sla2"], 0.6)                    # cohort counts unresolved cases as failures
        self.assertGreaterEqual(out["sla2_resolved"], out["cohort_sla2"])
        self.assertEqual(out["km_p95"], float("inf"))               # 95% resolution never reached

    def test_full_capacity_meets_sla(self):
        out, _ = simulate(synthetic_days(), cap=1.0, order="fifo", n_day=10)
        self.assertEqual(out["cohort_sla2"], 1.0); self.assertEqual(out["unresolved_frac"], 0.0)
        self.assertEqual(out["km_p95"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
