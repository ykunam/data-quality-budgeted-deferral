"""Identification, overlap, leakage and matched-allocation checks for revision."""
import itertools, unittest, json
from pathlib import Path
from scipy import stats
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


class SavedRevisionResults(unittest.TestCase):
    path=Path(__file__).resolve().parents[1]/'results/revision.csv.gz'

    def test_figure_exports_are_complete(self):
        for name in ('fig3_volume.pdf','fig5_backlog.pdf'):
            p=self.path.parents[1]/'figs'/name
            if not p.exists():continue
            raw=p.read_bytes()
            self.assertGreater(len(raw),1000)
            self.assertTrue(raw.startswith(b'%PDF-'))
            self.assertIn(b'%%EOF',raw[-1024:])

    @unittest.skipUnless(path.exists(),'Run the revision grid to check saved outputs')
    def test_complete_grid_capacity_costs_and_structural_null(self):
        d=pd.read_csv(self.path)
        self.assertEqual(len(d),102960)
        keys=['dataset','seed','reviewer','logging','weighting','condition','capacity','method','arm']
        self.assertFalse(d.duplicated(keys).any())
        self.assertEqual(set(d.dataset),{'default','bank','human'})
        self.assertTrue((d.review<=d.capacity+1e-10).all())
        self.assertTrue((d[d.arm!='no_rules'].violation==0).all())
        np.testing.assert_allclose(d.cost,d.auto_loss+d.review_loss+.05*d.review+1.5*d.hold,atol=1e-10)
        fill=d[(d.arm=='fill')&(d.method!='rules_only')]
        np.testing.assert_allclose(fill.review,np.floor(fill.capacity*fill.n)/fill.n,atol=1e-10)
        x=d[(d.arm=='matched')&(d.mandatory>d.capacity)&d.method.isin(['prob','quality_A'])]
        x=x.pivot(index=keys[:7],columns='method',values='cost')
        np.testing.assert_allclose(x.prob,x.quality_A,atol=1e-12)

    @unittest.skipUnless(path.exists(),'Run the revision grid to check saved inference')
    def test_primary_inference_and_declared_holm_family(self):
        d=pd.read_csv(self.path)
        s=d[(d.dataset=='bank')&(d.condition=='informative')&(d.logging=='random')&
            (d.weighting=='unweighted')&(d.capacity==.2)&(d.arm=='matched')]
        x=s.groupby(['seed','method']).cost.mean().unstack();diff=x.prob-x.quality_A
        mean=diff.mean();se=np.sqrt((1/20+.25)*diff.var(ddof=1))
        p=2*stats.t.sf(abs(mean/se),19)
        summary=json.loads((self.path.parent/'revision-summary.json').read_text())
        self.assertAlmostEqual(summary['primary']['diff'],mean,places=12)
        self.assertAlmostEqual(summary['primary']['p'],p,places=12)
        ci=stats.t.ppf(.975,19)*se
        self.assertAlmostEqual(summary['primary']['lo'],mean-ci,places=12)
        self.assertAlmostEqual(summary['primary']['hi'],mean+ci,places=12)
        rows=summary['secondary_family_6'];self.assertEqual(len(rows),6)
        self.assertEqual({(r['dataset'],r['logging']) for r in rows},
            set(itertools.product(['default','bank'],['random','uncertainty','rules'])))
        raw=np.array([r['p'] for r in rows]);order=np.argsort(raw)
        adjusted=np.empty(6);adjusted[order]=np.minimum(1,np.maximum.accumulate(raw[order]*np.arange(6,0,-1)))
        np.testing.assert_allclose(adjusted,[r['p_holm'] for r in rows],atol=1e-12)


if __name__=='__main__':unittest.main()
