import unittest
import numpy as np
import sys
import json
import pandas as pd
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dqd import cybersecurity as Y, core as C

class CybersecurityInvariants(unittest.TestCase):
    def test_rich_comparator_contains_full_quality_representation(self):
        X=np.arange(240,dtype=float).reshape(20,12);X[0,0]=np.nan
        q=C.Quality(X);groups=[list(range(i*3,i*3+3)) for i in range(4)]
        reps,_,_,_=Y.representations(np.linspace(.1,.9,20),X,q,groups)
        n=reps['quality'].shape[1]
        np.testing.assert_array_equal(reps['rich'][:,:n],reps['quality'])
        np.testing.assert_array_equal(reps['rich'][:,n:],X)
    def test_session_and_feature_components(self):
        h=np.array([1,2,2,4,5]);s=np.array([6,6,7,7,8])
        g=Y.merge_groups(h,s)
        self.assertEqual(len(set(g[:4])),1);self.assertNotEqual(g[0],g[4])
    def test_group_isolation(self):
        h=np.repeat(np.arange(100,dtype=np.uint64),3)
        roles=Y.split_groups(h,7)
        self.assertTrue(all(len(set(roles[h==g]))==1 for g in np.unique(h)))
        self.assertEqual(set(roles),{0,1,2})

    def test_corruption_has_no_label_input_and_preserves_clean(self):
        X=np.arange(240,dtype=float).reshape(20,12);g=[list(range(j*3,j*3+3)) for j in range(4)]
        z,d=Y.corrupt(X,'clean',np.random.default_rng(2),g,X)
        np.testing.assert_array_equal(z,X);self.assertFalse(d.any())
        z,d=Y.corrupt(X,'severe',np.random.default_rng(2),g,X)
        self.assertTrue(d.all());np.testing.assert_allclose(np.isnan(z).mean(1),.75)
        z,d=Y.corrupt(X,'replacement',np.random.default_rng(2),g,X)
        self.assertFalse(np.isnan(z).any())

    def test_conformal_order_statistics_and_small_sample(self):
        p=np.tile(np.arange(100)/100,2);y=np.repeat([0,1],100)
        high,low=Y.thresholds(p,y)
        self.assertAlmostEqual(high,.95);self.assertAlmostEqual(low,.04)
        self.assertEqual(Y.thresholds(np.array([.2,.8]),np.array([0,1])),(np.inf,-np.inf))

    def test_matched_counts_and_overload_null(self):
        m=np.array([1,1,1,0,0],bool);h=np.arange(5.)
        r1,b1=C.allocate(m,2,np.arange(5.),np.ones(5,bool),-h)
        r2,b2=C.allocate(m,2,np.arange(5.)[::-1],np.ones(5,bool),-h)
        np.testing.assert_array_equal(r1,r2);np.testing.assert_array_equal(b1,b2)
        self.assertEqual(r1.sum(),2);self.assertFalse((~r1&~b1&m).any())

    def test_holding_attack_cannot_count_as_resolution(self):
        y=np.array([1,0]);yh=np.array([False,False]);r=np.zeros(2,bool);h=np.array([True,False])
        v=Y.metrics(r,h,y,yh,np.array([.1,.1]),h)
        self.assertEqual(v['auto_close_attack'],0);self.assertEqual(v['held_attack'],1)
        self.assertEqual(v['unmet_attack'],1)

@unittest.skipUnless((Y.OUT/'cyber-results.csv.gz').exists(),'Run the frozen experiment first')
class SavedCybersecurityOutputs(unittest.TestCase):
    def test_complete_grid_and_cost_accounting(self):
        d=pd.read_csv(Y.OUT/'cyber-results.csv.gz')
        self.assertEqual(len(d),21120)
        self.assertFalse(d.duplicated(['dataset','seed','reviewer','condition','capacity','method','arm']).any())
        np.testing.assert_allclose(d.cost,d.auto_loss+d.review_loss+.05*d.review+1.5*d.hold,atol=1e-10)
        self.assertTrue((d.review<=d.capacity+1e-12).all())
        self.assertTrue((d[d.arm!='no_rules'].violation==0).all())
    def test_primary_and_secondary_family_preserved(self):
        s=json.loads((Y.OUT/'cyber-summary.json').read_text())
        self.assertEqual(len(s['contrasts']),8)
        self.assertEqual(sum(x['primary'] for x in s['contrasts']),1)
        self.assertEqual(sum('p_holm' in x for x in s['contrasts']),7)
        self.assertEqual(s['primary']['seeds'],20)
        self.assertEqual([s['primary'][k] for k in ['dataset','condition']],['unsw','outage'])
    def test_display_values_and_vector_exports(self):
        d=pd.read_csv(Y.OUT/'cyber-results.csv.gz')
        for x in json.loads((Y.OUT/'cyber-display.json').read_text()):
            arm='native' if x['method']=='conformal' else 'matched'
            z=d[(d.dataset==x['dataset'])&(d.method==x['method'])&(d.condition=='outage')&(d.capacity==.2)&(d.arm==arm)].cost.mean()
            self.assertAlmostEqual(x['cost'],z,12)
        for n in (1,2):
            b=(Y.ROOT/f'figs/cyber_fig{n}.pdf').read_bytes()
            self.assertTrue(b.startswith(b'%PDF') and b'%%EOF' in b[-30:])

if __name__=='__main__':unittest.main()
