"""Scientific invariants: routing optimality, governance, budget and leakage guards."""
import itertools
import unittest
import numpy as np
from experiment import Quality, allocate, corrupt, expert_error, evaluate, features, losses, split_rows

class RoutingTests(unittest.TestCase):
    def test_exact_feasible_optimizer(self):
        rng=np.random.default_rng(4)
        for n in range(1,9):
            for _ in range(25):
                gain=rng.normal(size=n);mandatory=rng.random(n)<.3
                b=int(rng.integers(mandatory.sum(),n+1))
                action=allocate(gain,mandatory,b)
                feasible=[np.array(bits,bool) for bits in itertools.product([0,1],repeat=n)
                          if sum(bits)<=b and np.all(np.array(bits)[mandatory])]
                best=max(gain[s].sum() for s in feasible)
                self.assertAlmostEqual(gain[action==1].sum(),best)
                self.assertFalse(np.any(action==2))
    def test_overload_is_held_not_automated(self):
        a=allocate(np.array([3.,2.,1.,4.]),np.array([1,1,1,0]),1)
        np.testing.assert_array_equal(a,[1,2,2,0])
    def test_zero_budget(self):
        np.testing.assert_array_equal(allocate([1.,2.],[True,False],0),[2,0])
    def test_negative_optional_is_not_reviewed(self):
        np.testing.assert_array_equal(allocate([-1.,0.,1.],[False]*3,3),[0,0,1])
    def test_stable_ties(self):
        np.testing.assert_array_equal(allocate([1.,1.,1.],[False]*3,1),[1,0,0])
    def test_bad_budget_and_nan(self):
        for gain,b in [([np.nan],1),([1.],2),([1.],-1)]:
            with self.assertRaises(ValueError): allocate(gain,[False],b)
    def test_all_capacity(self):
        np.testing.assert_array_equal(allocate([1.,2.],[True,True],2),[1,1])

class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.x=np.arange(60,dtype=float).reshape(20,3);self.q=Quality().fit(self.x)
    def test_identical_features_never_cross_splits(self):
        rng=np.random.default_rng(1)
        x=rng.normal(size=(100,4));y=np.array([0,1]*50)
        x=np.vstack([x,x[:4],x[:4]]);y=np.r_[y,[0,1,0,1],[1,0,1,0]]
        parts=split_rows(x,y,3)
        for i,j in itertools.combinations(range(4),2):
            self.assertFalse(set(map(tuple,x[parts[i]])) & set(map(tuple,x[parts[j]])))
        self.assertEqual(sum(map(len,parts)),len(y))
    def test_quality_features_are_compact_and_label_free(self):
        f=features(np.full(20,.2),self.x,self.q,True)
        self.assertEqual(f.shape,(20,8));self.assertTrue(np.isfinite(f).all())
    def test_quality_uses_training_bounds(self):
        original=self.q.hi.copy();a=self.x.copy();a[0,0]=1e6;a[1,1]=np.nan
        z,q,m,o=self.q.transform(a)
        np.testing.assert_array_equal(self.q.hi,original)
        self.assertTrue(np.isfinite(z).all());self.assertEqual(q[1,0],1/3);self.assertTrue(o[0,0])
    def test_corruption_reproducible_and_nonmutating(self):
        before=self.x.copy();a=corrupt(self.x,'mixed',7,self.q);b=corrupt(self.x,'mixed',7,self.q)
        np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(self.x,before)
    def test_clean_unchanged(self):
        np.testing.assert_array_equal(corrupt(self.x,'clean',1,self.q),self.x)
    def test_asymmetric_loss(self):
        np.testing.assert_array_equal(losses(np.array([0,1]),np.array([1,0])),[1.,5.])
    def test_holding_penalty_counted(self):
        result=evaluate(np.array([0,1]),np.array([0,1]),np.zeros((2,2)),'constant',np.array([0,2]),np.array([0,1],bool))
        self.assertEqual(result['cost'],.75);self.assertEqual(result['hold'],.5);self.assertEqual(result['violation'],0)
    def test_reviewer_not_perfect(self):
        for p in ('constant','quality','adverse'):
            e=expert_error(np.zeros((4,2)),p);self.assertTrue(np.all(e>0));self.assertTrue(np.all(e<1))
    def test_routing_interface_has_no_labels(self):
        import inspect
        self.assertNotIn('y',inspect.signature(allocate).parameters)
        self.assertNotIn('y',inspect.signature(features).parameters)

if __name__=='__main__':unittest.main()
