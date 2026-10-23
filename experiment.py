"""Reproducible, quality-conditioned batch deferral; no test-label routing.

Run: python experiment.py --seeds 20 --start-seed 2 --out results
Review outcomes are simulated expectations, not observed human decisions.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import platform
import sys
import time
import urllib.request
import zipfile

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.stats import t
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from threadpoolctl import threadpool_limits

DATA = {
 'german': ('https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data-numeric', 'german.data-numeric', '10.24432/C5NC77'),
 'australian': ('https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/australian/australian.dat', 'australian.dat', '10.24432/C59012'),
 'default': ('https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip', 'default.zip', '10.24432/C55S3H'),
}
HASHES = {'german': '2752b044394958ab6dd193a0b56ca0f0b3a2d8bc7cb8c008e35a5e84bbec02f8',
          'australian': '3abe5af151afa50b999a9ba21cbc884e80d80a4050b716cf88b34a2e6ecb731c',
          'default': '56c885f84457f6680f8438f02bfcdac9579323d8a94465ee5f26e32baa727602'}
SCENARIOS = ('clean', 'missing', 'outliers', 'mixed', 'shift')
PROFILES = ('constant', 'quality', 'adverse')
BUDGETS = (.05, .10, .20, .30)
METHODS = ('auto', 'random', 'confidence', 'cost_risk', 'quality_only', 'learned_p', 'learned_x', 'proposed', 'no_rules', 'no_rules_p')
COST_FN, COST_FP, REVIEW_COST, HOLD_COST = 5., 1., .05, 1.5


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_data(name, cache):
    url, filename, doi = DATA[name]
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    path = cache / filename
    if not path.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            content = response.read()
        tmp = path.with_suffix(path.suffix + '.part'); tmp.write_bytes(content); tmp.replace(path)
    if sha256(path) != HASHES[name]:
        raise ValueError(f'Checksum mismatch for {path}; expected official archived bytes')
    if name == 'default':
        with zipfile.ZipFile(path) as z:
            member = next(n for n in z.namelist() if n.endswith('.xls'))
            df = pd.read_excel(io.BytesIO(z.read(member)), header=1)
        # ID is never a predictor. Retain benchmark covariates; no fairness claim.
        x = df.iloc[:, 1:-1].to_numpy(float); y = df.iloc[:, -1].to_numpy(int)
    else:
        a = np.loadtxt(path)
        x, y = a[:, :-1], a[:, -1].astype(int)
        if name == 'german': y = (y == 2).astype(int)
    assert np.isfinite(x).all() and set(np.unique(y)) == {0, 1}
    return x, y, dict(url=url, file=filename, doi=doi, sha256=sha256(path), n=len(y), d=x.shape[1], positive_rate=float(y.mean()))


def split_rows(x, y, seed):
    """Stratify feature-identical groups, keeping even conflicting labels together."""
    _, groups = np.unique(x, axis=0, return_inverse=True)
    ids = np.unique(groups)
    votes = np.bincount(groups, weights=y) / np.bincount(groups)
    strata = (votes >= .5).astype(int)
    development, test = train_test_split(ids, test_size=.2, stratify=strata, random_state=seed)
    training, remain = train_test_split(development, test_size=.4375, stratify=strata[development], random_state=seed+101)
    calibration, selection = train_test_split(remain, test_size=4/7, stratify=strata[remain], random_state=seed+202)
    parts = tuple(np.flatnonzero(np.isin(groups, part)) for part in (training,calibration,selection,test))
    for i,j in itertools.combinations(range(4),2):
        assert not set(groups[parts[i]]) & set(groups[parts[j]])
    assert sum(map(len,parts)) == len(y)
    return parts


class Quality:
    """Bounds learned from predictor-training rows only; no corruption oracle."""
    def fit(self, x):
        self.med = np.median(x, axis=0)
        lo, hi = np.quantile(x, [.01, .99], axis=0)
        self.scale = np.maximum(hi - lo, 1.)
        self.lo, self.hi = lo - .1*self.scale, hi + .1*self.scale
        return self

    def transform(self, x):
        missing = np.isnan(x)
        outside = ((x < self.lo) | (x > self.hi)) & ~missing
        # Range violations are flags, not claimed measurements of true corruption.
        q = np.column_stack([missing.mean(1), outside.mean(1)])
        z = np.clip((np.where(missing, self.med, x)-self.med)/self.scale, -5, 5)
        return z, q, missing.astype(float), outside.astype(float)

    def mandatory(self, q):
        # Illustrative organization policy, not a legal or lending requirement.
        return (q[:, 0] >= .5) | (q[:, 1] >= .25)


def corrupt(x, scenario, seed, quality):
    rng = np.random.default_rng(seed); a = x.copy(); n, d = a.shape
    if scenario == 'clean': return a
    if scenario == 'missing':
        rm, ro = rng.uniform(0, .55, n), np.zeros(n)
    elif scenario == 'outliers':
        rm, ro = np.zeros(n), rng.uniform(0, .18, n)
    elif scenario == 'mixed':
        rm, ro = rng.uniform(0, .35, n), rng.uniform(0, .12, n)
    elif scenario == 'shift':
        # Unseen stress severity; selector training never sees this scenario.
        rm, ro = rng.uniform(.35, .75, n), rng.uniform(.08, .25, n)
    else: raise ValueError(scenario)
    mask_o = rng.random((n, d)) < ro[:, None]
    signs = rng.choice([-1., 1.], size=(n, d))
    a[mask_o] += (signs * rng.uniform(1.2, 2.5, (n, d)) * quality.scale)[mask_o]
    a[rng.random((n, d)) < rm[:, None]] = np.nan
    return a


def expert_error(q, profile):
    if profile == 'constant': return np.full(len(q), .10)
    if profile == 'quality': return np.clip(.05 + .35*q[:, 0] + .25*q[:, 1], 0, .4)
    if profile == 'adverse': return np.full(len(q), .25)
    raise ValueError(profile)


def losses(y, prediction):
    return np.where(y == 1, COST_FN, COST_FP)*(prediction != y)


def reviewer_loss(y, q, profile):
    return np.where(y == 1, COST_FN, COST_FP)*expert_error(q, profile) + REVIEW_COST


def logit(p):
    p = np.clip(p, 1e-6, 1-1e-6)
    return np.log(p/(1-p)).reshape(-1, 1)


def features(p, x, quality, with_quality):
    z, q, missing, outside = quality.transform(x)
    core = np.column_stack([p, np.minimum(COST_FN*p, COST_FP*(1-p)), z])
    if with_quality == 'p': return core[:, :2]
    # Compact quality representation avoids per-feature mask proliferation.
    return np.column_stack([core[:, :2], q, p[:,None]*q, (p[:,None] >= 1/6)*q]) if with_quality else core


def allocate(gain, mandatory, budget, *, force_fill=False):
    """Exact top-positive estimated gains if compulsory load fits capacity.

    If overloaded: compulsory jobs consume capacity first; overflow is held.
    action: 0 automate, 1 review, 2 hold. Stable ties use original row order.
    """
    gain = np.asarray(gain, dtype=float); mandatory = np.asarray(mandatory, dtype=bool)
    if gain.ndim != 1 or mandatory.shape != gain.shape or not np.isfinite(gain).all():
        raise ValueError('Invalid gain or rule vector')
    if not 0 <= budget <= len(gain): raise ValueError('Budget outside batch size')
    budget = int(budget); action = np.zeros(len(gain), dtype=np.int8)
    required = np.flatnonzero(mandatory)
    ordered = required[np.argsort(-gain[required], kind='stable')]
    action[required] = 2
    action[ordered[:budget]] = 1
    capacity = budget - min(len(required), budget)
    optional = np.flatnonzero(~mandatory)
    optional = optional[np.argsort(-gain[optional], kind='stable')]
    if not force_fill: optional = optional[gain[optional] > 0]
    action[optional[:capacity]] = 1
    assert (action == 1).sum() <= budget
    assert not np.any(mandatory & (action == 0))
    return action


def evaluate(y, pred, q, profile, action, mandatory):
    la, lh = losses(y, pred), reviewer_loss(y, q, profile)
    a, r, h = action == 0, action == 1, action == 2
    return dict(cost=float(np.where(a, la, np.where(r, lh, HOLD_COST)).mean()),
                auto_risk=float(la[a].mean()) if a.any() else np.nan,
                review=float(r.mean()), hold=float(h.mean()),
                violation=float(np.mean(mandatory & a)), mandatory=float(mandatory.mean()),
                completed=float((~h).mean()),
                expected_error=float(np.sum((pred[a]!=y[a])) + np.sum(expert_error(q,profile)[r]))/max(1,(~h).sum()))


def build_seed(name, seed, cache):
    start = time.perf_counter(); x, y, meta = load_data(name, cache)
    training, calibration, selection, test = split_rows(x,y,seed)
    quality = Quality().fit(x[training])
    base = HistGradientBoostingClassifier(max_iter=120,max_leaf_nodes=15,learning_rate=.07,l2_regularization=1.,random_state=seed)
    base.fit(x[training], y[training])
    # Calibrate on clean and three in-distribution corruption types.
    train_scenarios = SCENARIOS[:4]
    xc = np.concatenate([corrupt(x[calibration], s, seed+1000+j, quality) for j,s in enumerate(train_scenarios)])
    yc = np.tile(y[calibration],4)
    calibrator = LogisticRegression(C=1., max_iter=500).fit(logit(base.predict_proba(xc)[:,1]),yc)
    def probability(a): return calibrator.predict_proba(logit(base.predict_proba(a)[:,1]))[:,1]
    xs = np.concatenate([corrupt(x[selection],s,seed+2000+j,quality) for j,s in enumerate(train_scenarios)])
    ys = np.tile(y[selection],4); ps = probability(xs); preds = (ps >= 1/6).astype(int)
    _, qs, _, _ = quality.transform(xs)
    # Same learner/capacity for feature-aware comparator and quality-aware method.
    selectors = {}
    for profile in PROFILES:
        gain_target = losses(ys,preds) - reviewer_loss(ys,qs,profile)
        for with_quality in ('p', False, True):
            model = HistGradientBoostingRegressor(loss='squared_error',max_iter=100,max_leaf_nodes=7,
                     min_samples_leaf=max(20,int(len(ys)*.005)),learning_rate=.06,l2_regularization=5.,random_state=seed)
            model.fit(features(ps,xs,quality,with_quality),gain_target)
            selectors[profile,with_quality] = model
    records=[]; audit=None
    for j,scenario in enumerate(SCENARIOS):
        xt=corrupt(x[test],scenario,seed+3000+j,quality); yt=y[test]
        p=probability(xt); pred=(p >= 1/6).astype(int)
        _,q,_,_=quality.transform(xt); mandatory=quality.mandatory(q)
        for profile in PROFILES:
            gain_x=selectors[profile,False].predict(features(p,xt,quality,False))
            gain_q=selectors[profile,True].predict(features(p,xt,quality,True))
            gain_p=selectors[profile,'p'].predict(features(p,xt,quality,'p'))
            score = {'random': np.random.default_rng(seed+9999).random(len(yt)),
                     'confidence': -np.abs(p-1/6),
                     'cost_risk': np.minimum(COST_FN*p,COST_FP*(1-p)),
                     'quality_only': q.sum(1), 'learned_p':gain_p, 'learned_x':gain_x,'proposed':gain_q,'no_rules':gain_q,'no_rules_p':gain_p}
            for budget in BUDGETS:
                cap=int(np.floor(budget*len(yt)))
                for method in METHODS:
                    if method=='auto': action=np.zeros(len(yt),dtype=np.int8)
                    else: action=allocate(score[method],mandatory if not method.startswith('no_rules') else np.zeros(len(yt),bool),cap,
                                          force_fill=method in ('random','confidence','cost_risk','quality_only'))
                    r=evaluate(yt,pred,q,profile,action,mandatory)
                    records.append(dict(dataset=name,seed=seed,scenario=scenario,profile=profile,budget=budget,method=method,**r))
                    if seed==2 and name=='default' and scenario=='mixed' and profile=='quality' and budget==.2 and method=='proposed':
                        audit=pd.DataFrame(dict(row_id=test,p=p,missing=q[:,0],outside=q[:,1],mandatory=mandatory,gain=gain_q,
                                               action=np.array(['automate','review','hold'])[action]))
    print(f'{name} seed={seed}: {time.perf_counter()-start:.1f}s',flush=True)
    meta['split_counts']={k:len(v) for k,v in [('train',training),('calibration',calibration),('selector',selection),('test',test)]}
    return records, meta, audit


def paired_summary(frame, reference='learned_x', scenario=None, profile='quality', budget=.2):
    d=frame[(frame.profile==profile)&np.isclose(frame.budget,budget)]
    if scenario: d=d[d.scenario==scenario]
    else: d=d[d.scenario!='clean']
    wide=d.pivot_table(index=['dataset','seed','scenario'],columns='method',values='cost')
    delta=(wide[reference]-wide.proposed).groupby('seed').mean().to_numpy()
    # Split-seed intervals are descriptive, not population-independent inference.
    half=float(t.ppf(.975,len(delta)-1)*np.std(delta,ddof=1)/np.sqrt(len(delta))) if len(delta)>1 else 0.
    return dict(mean=float(np.mean(delta)),low=float(np.mean(delta)-half),high=float(np.mean(delta)+half),n_seeds=len(delta),
                relative=float((wide[reference].mean()-wide.proposed.mean())/wide[reference].mean()),
                comparator=float(wide[reference].mean()),proposed=float(wide.proposed.mean()))


def report(frame,out,manifest):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    frame.to_csv(out/'metrics.csv',index=False,float_format='%.10g')
    summary={f'{profile}_{ref}':paired_summary(frame,ref,profile=profile) for profile in PROFILES for ref in ('confidence','cost_risk','learned_p','learned_x','quality_only')}
    summary['by_dataset']={name:paired_summary(frame[frame.dataset==name]) for name in DATA if name in set(frame.dataset)}
    main=frame[(frame.profile=='quality') & np.isclose(frame.budget,.2)]
    summary['main_means']=main[main.scenario!='clean'].groupby('method')[['cost','review','hold','violation']].mean().to_dict('index')
    fixed=frame[(frame.profile=='quality') & np.isclose(frame.budget,.2) & (frame.scenario=='shift') & (frame.method=='proposed')]
    summary['fixed_route_stress_hold_sensitivity']={str(c):float((fixed.cost+(c-HOLD_COST)*fixed.hold).mean()) for c in (.5,1.5,3.)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest['results_sha256']=sha256(out/'metrics.csv')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    colors={'confidence':'#D55E00','cost_risk':'#7570B3','learned_x':'#0072B2','quality_only':'#009E73','proposed':'#111111'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'ps.fonttype':42})
    fig,ax=plt.subplots(figsize=(6.4,3.0))
    f=frame[(frame.profile=='quality') & (frame.scenario!='clean')]
    for method in colors:
        seedmeans=f[f.method==method].groupby(['budget','seed']).cost.mean().unstack('seed')
        mean=seedmeans.mean(1); sem=seedmeans.std(1,ddof=1)/np.sqrt(seedmeans.shape[1])
        ax.plot(mean.index*100,mean,marker={'confidence':'^','cost_risk':'s','learned_x':'o','quality_only':'v','proposed':'D'}[method],linestyle={'confidence':'-','cost_risk':'--','learned_x':':','quality_only':'--','proposed':'-'}[method],label={'learned_x':'Feature-aware gain','proposed':'Quality-aware gain','cost_risk':'Cost risk','quality_only':'Quality-only ranking','confidence':'Confidence'}[method],color=colors[method],lw=1.7,ms=4)
        ax.fill_between(mean.index*100,mean-1.96*sem,mean+1.96*sem,color=colors[method],alpha=.10)
    ax.set(xlabel='Maximum review capacity (% of batch)',ylabel='Expected cost per record')
    ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.17);ax.legend(fontsize=8,ncol=2,frameon=False)
    fig.tight_layout();fig.savefig(out/'Figure_1.pdf');fig.savefig(out/'Figure_1.png',dpi=300);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.4,3.6))
    items=[]
    for scenario in SCENARIOS:
        for profile in PROFILES:
            result=paired_summary(frame,'learned_x',scenario,profile)
            items.append((scenario,profile,result))
    # Each point averages all three datasets, paired within seed.
    for k,(scenario,profile,r) in enumerate(items):
        ax.errorbar(r['mean'],len(items)-1-k,xerr=[[r['mean']-r['low']],[r['high']-r['mean']]],fmt='o',ms=3,
                    color={'constant':'#0072B2','quality':'#009E73','adverse':'#D55E00'}[profile],capsize=2)
    ax.axvline(0,color='.45',lw=.8);ax.set_yticks(range(len(items)),[f'{s} / {p}' for s,p,_ in items][::-1],fontsize=7)
    ax.set_xlabel('Expected cost difference (feature gain minus quality gain)')
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.17)
    fig.tight_layout();fig.savefig(out/'Figure_2.pdf');fig.savefig(out/'Figure_2.png',dpi=300);plt.close(fig)
    names={'auto':'Automation only','random':'Random + rules','confidence':'Confidence + rules','cost_risk':'Cost risk + rules','quality_only':'Quality only + rules','learned_p':'Probability gain + rules','learned_x':'Feature gain + rules','proposed':'Quality gain + rules','no_rules':'Quality gain, no rules','no_rules_p':'Probability gain, no rules'}
    tex=[]
    r=summary['quality_learned_x']
    for name,value in [('StudyDelta',r['mean']),('StudyDeltaLow',r['low']),('StudyDeltaHigh',r['high']),('StudyRelative',100*r['relative'])]:
        tex.append('\\newcommand{\\'+name+'}{'+f'{value:.4f}'+'}')
    comp_datasets=[name for name in ('german','australian','default') if name in set(frame.dataset)]
    tex.append(r'\newcommand{\MainTable}{'+'\n'+r'\begin{tabular}{l'+'r'*(len(comp_datasets)+1)+r'}\toprule Method & '+' & '.join(k.title() for k in comp_datasets)+r' & Macro \\ \midrule')
    comp=main[main.scenario!='clean'].groupby(['method','dataset']).cost.mean().unstack('dataset')
    for method in METHODS:
        values=[comp.loc[method,k] for k in comp_datasets]
        tex.append(names[method]+' & '+' & '.join(f'{v:.4f}' for v in values+[float(np.mean(values))])+r' \\')
    tex.append(r'\bottomrule\end{tabular}}')
    tex.append(r'\newcommand{\GovernanceTable}{'+'\n'+r'\begin{tabular}{lccrrrr}\toprule Condition & Quality & Rules & Cost & Review & Hold & Violation \\ \midrule')
    for scenario in ('mixed','shift'):
        for method in ('learned_p','proposed','no_rules_p','no_rules'):
            row=main[(main.scenario==scenario)&(main.method==method)][['cost','review','hold','violation']].mean()
            tex.append(scenario+' & '+('On' if method in ('proposed','no_rules') else 'Off')+' & '+('Off' if method.startswith('no_rules') else 'On')+' & '+f'{row.cost:.4f}'+' & '+' & '.join(f'{100*row[k]:.1f}' for k in ('review','hold','violation'))+r' \\')
    tex.append(r'\bottomrule\end{tabular}}')
    (out/'tables.tex').write_text('\n'.join(tex)+'\n')
    print(json.dumps(summary['quality_learned_x'],indent=2),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=20)
    parser.add_argument('--start-seed',type=int,default=2)
    parser.add_argument('--datasets',nargs='+',choices=list(DATA),default=list(DATA))
    parser.add_argument('--cache',type=Path,default=Path('../data_cache'))
    parser.add_argument('--out',type=Path,default=Path('results'))
    parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args()
    if args.report_only:
        report(pd.read_csv(args.out/'metrics.csv'),args.out,json.loads((args.out/'manifest.json').read_text()));return
    if args.seeds<1:parser.error('--seeds must be positive')
    records=[]; metadata={};start=time.perf_counter();args.out.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=1):
        for name in args.datasets:
            for seed in range(args.start_seed,args.start_seed+args.seeds):
                r,m,a=build_seed(name,seed,args.cache);records.extend(r);metadata.setdefault(name,dict(m,split_counts_by_seed={}));metadata[name]['split_counts_by_seed'][str(seed)]=m['split_counts']
                if a is not None:a.to_csv(args.out/'audit.csv',index=False,float_format='%.10g')
                # Checkpoint protects lengthy runs; report-only can regenerate figures.
                pd.DataFrame(records).to_csv(args.out/'metrics.csv',index=False)
    manifest=dict(version='1.1.0',command=sys.argv,python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
      scipy=scipy.__version__,sklearn=sklearn.__version__,matplotlib=matplotlib.__version__,code_sha256=sha256(__file__),datasets=metadata,
      seeds=list(range(args.start_seed,args.start_seed+args.seeds)),budgets=BUDGETS,scenarios=SCENARIOS,profiles=PROFILES,costs=dict(false_negative=COST_FN,false_positive=COST_FP,review=REVIEW_COST,hold=HOLD_COST),
      reviewer='Simulated expected losses; no human participants',duration_seconds=time.perf_counter()-start)
    report(pd.DataFrame(records),args.out,manifest)

if __name__=='__main__':main()
