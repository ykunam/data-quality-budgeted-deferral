"""Regression tests: published-method baselines must respond to the review fee (matched costs)."""
import os, sys, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from dqd import core as C


class ReviewFeeSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(0); n = 1500
        cls.X = rng.normal(size=(n, 5)); logit = cls.X[:, 0] - 0.5
        cls.y = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
        cls.correct = rng.random(n) >= 0.1
        cls.yhat = (cls.X[:, 0] > 0).astype(int)

    def test_ova_score_shifts_with_fee_and_stops_deferring(self):
        lo = C.fit_l2d_ova(self.X, self.y, self.correct, C.Costs(review=0.0), 1)(self.X, self.yhat)
        hi = C.fit_l2d_ova(self.X, self.y, self.correct, C.Costs(review=100.0), 1)(self.X, self.yhat)
        np.testing.assert_allclose(lo - hi, 100.0, atol=1e-9)      # same network, fee enters linearly
        self.assertEqual(int((hi > 0).sum()), 0)

    def test_ce_stops_deferring_at_prohibitive_fee(self):
        lh = np.where(self.y == 1, 5.0, 1.0) * (~self.correct)
        lo = C.fit_l2d_ce(self.X, self.y, lh, C.Costs(review=0.0), 1)(self.X)
        hi = C.fit_l2d_ce(self.X, self.y, lh, C.Costs(review=100.0), 1)(self.X)
        self.assertGreater(int((lo > 0).sum()), int((hi > 0).sum()))
        self.assertEqual(int((hi > 0).sum()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
