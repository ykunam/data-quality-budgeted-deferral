"""Identification, overlap, leakage and matched-allocation checks for revision."""
import itertools, unittest
import numpy as np
import pandas as pd
from dqd.revision import propensity, inner_masks, encode_training_categories
from dqd.core import allocate


class RevisionDesign(unittest.TestCase):
    def test_selection_has_overlap_and_equal_expected_budget(self):
        p=np.linspace(.001,.999,1000);u=np.linspace(0,.9,1000);v=u/2
        for policy in ('random','uncertainty','rules'):
            pr=propensity(policy,p,u,v)
            self.assertAlmostEqual(pr.mean(),.4,places=12)
            self.assertGreaterEqual(pr.min(),.1)
            self.assertLessEqual(pr.max(),.9)
        pr=propensity('rules',p,u,v)
        self.assertGreater(pr[u>=.5].mean(),pr[u<.5].mean())

    def test_inner_groups_never_leak_augmented_copies(self):
        groups=np.tile(np.arange(100),4)
        a,b=inner_masks(groups,2)
        self.assertFalse(set(groups[a])&set(groups[b]))
        self.assertTrue((a^b).all())
        np.testing.assert_array_equal(b,inner_masks(groups,2)[1])

    def test_ipw_identification_by_exact_enumeration(self):
        p=np.array([.1,.4,.9]);loss=np.array([5.,1.,0.])
        expectation=0.
        for s in itertools.product((0,1),repeat=3):
            s=np.asarray(s);mass=np.prod(np.where(s,p,1-p))
            expectation+=mass*np.mean(s*loss/p)
        self.assertAlmostEqual(expectation,loss.mean(),places=12)
        self.assertNotAlmostEqual(np.sum(p*loss)/p.sum(),loss.mean())

    def test_category_mapping_does_not_learn_test_categories(self):
        frame=pd.DataFrame({'x':['a','b','unknown','new'],'z':[1.,2.,3.,4.]})
        X=encode_training_categories(frame,np.array([0,1]))
        np.testing.assert_array_equal(X[:2,0],[0.,1.])
        self.assertTrue(np.isnan(X[2:,0]).all())

    def test_fill_arm_matches_review_budget_and_primary_overload(self):
        m=np.array([True,True,False,False,False]);h=np.array([.3,.1,.4,.5,.6])
        for B in (1,3,5):
            routes=[]
            for scores in [np.arange(5.),-np.arange(5.)]:
                r,hold=allocate(m,B,scores,np.ones(5,bool),-h)
                self.assertEqual(r.sum(),B)
                self.assertEqual(hold.sum(),max(0,int(m.sum())-B))
                routes.append(r)
            if B<m.sum():np.testing.assert_array_equal(*routes)


if __name__=='__main__':unittest.main()
