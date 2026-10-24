"""Prospective core-revision experiments; see README's frozen analysis plan.

Run: OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m dqd.revision run
     python -m dqd.revision analyze
Only new source module; original exploratory code/results are retained.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, io, json, os, pickle, platform
from pathlib import Path
import tarfile, zipfile
import urllib.request
import importlib.metadata as metadata
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingRegressor
from . import core as C, static as S, stats as ST

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RESULTS = ROOT / 'results'
SEEDS = tuple(range(2, 22))
POLICIES = ('random', 'uncertainty', 'rules')
CONDITIONS = ('clean', 'informative', 'stale', 'shift')
REVIEWERS = ('constant', 'correlated')
CAPACITIES = (.1, .2)
METHODS = ('prob', 'quality_A', 'quality_both', 'features', 'single',
           'confidence', 'chow', 'rules_only')
GRID = (3, 7)


def propensity(policy, p, u, v, costs=C.Costs()):
    """Covariate-only acquisition with known overlap; population mean = .4."""
    if policy == 'random':
        return np.full(len(p), .4)
    if policy == 'uncertainty':
        score = -np.abs(p - costs.threshold)
        score = 3 * (score - score.mean()) / (score.std() + 1e-12)
    elif policy == 'rules':
        score = 4 * S.Rules()(u, v).astype(float) + 2 * (u + v)
    else:
        raise ValueError(policy)
    lo, hi = -50., 50.
    for _ in range(80):
        mid = (lo + hi) / 2
        if (.1 + .8 * expit(score + mid)).mean() > .4:
            hi = mid
        else:
            lo = mid
    return .1 + .8 * expit(score + (lo + hi) / 2)


def inner_masks(groups, seed):
    """Keep all augmented copies and feature-identical rows in the same fold."""
    unique = np.unique(groups)
    val = np.random.default_rng(seed + 919).permutation(unique)[:max(1, len(unique)//5)]
    valid = np.isin(groups, val)
    assert valid.any() and (~valid).any()
    return ~valid, valid


def fit_head(Z, target, observed, probability, groups, seed, weighted):
    """Identical two-configuration search for every regression head.

    IPW corrects covariate selection under known positive propensities. It does
    not correct missing outcome labels, hidden selection, or reviewer drift.
    """
    fit, valid = inner_masks(groups, seed)
    fit &= observed; valid &= observed
    if min(fit.sum(), valid.sum()) < 5:
        raise ValueError('Insufficient logged fit/validation rows; do not silently resample')
    w = 1 / probability if weighted else np.ones(len(Z))
    w /= w[observed].mean()
    scores = []
    for leaves in GRID:
        model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=leaves,
            learning_rate=.06, l2_regularization=5., min_samples_leaf=20,
            early_stopping=False, random_state=seed)
        model.fit(Z[fit], target[fit], sample_weight=w[fit])
        err = (model.predict(Z[valid]) - target[valid])**2
        scores.append(np.average(err, weights=w[valid]))
    leaves = GRID[int(np.argmin(scores))]
    model = HistGradientBoostingRegressor(max_iter=100, max_leaf_nodes=leaves,
        learning_rate=.06, l2_regularization=5., min_samples_leaf=20,
        early_stopping=False, random_state=seed).fit(
            Z[observed], target[observed], sample_weight=w[observed])
    return model, leaves


def load_dataset(name):
    if name == 'bank':
        outer = zipfile.ZipFile(DATA/'bank.zip')
        inner = zipfile.ZipFile(io.BytesIO(outer.read('bank.zip')))
        d = pd.read_csv(io.BytesIO(inner.read('bank-full.csv')), sep=';')
        # Pre-call prediction: duration is a post-call variable and is excluded.
        y = (d.pop('y') == 'yes').to_numpy(int)
        d = d.drop(columns='duration')
        return d, y, None
    if name == 'human':
        with tarfile.open(DATA/'cifar-10-python.tar.gz') as tar:
            f = tar.extractfile('cifar-10-batches-py/test_batch')
            d = pickle.load(f, encoding='bytes')
        images = d[b'data'].reshape(-1, 3, 32, 32).astype(float)/255
        X = images.reshape(-1, 3, 8, 4, 8, 4).mean(axis=(3, 5)).reshape(-1, 192)
        y = np.isin(d[b'labels'], [2, 3, 4, 5, 6, 7]).astype(int)
        z = zipfile.ZipFile(DATA/'cifar10h-raw.zip')
        trials = pd.read_csv(z.open('cifar10h-raw.csv'))
        trials = trials[trials.is_attn_check == 0]
        idx = trials.cifar10_test_set_idx.to_numpy(int)
        choices = np.isin(trials.chosen_label, [2, 3, 4, 5, 6, 7]).astype(int)
        count = np.bincount(idx, minlength=len(y))
        errors = np.bincount(idx, weights=(choices != y[idx]), minlength=len(y))
        assert (count > 0).all()
        return X, y, errors/count
    return C.load(name) + (None,)


def encode_training_categories(frame, train):
    """Fit codebooks on predictor-training rows; unknowns remain missing."""
    cols=[]
    for col in frame:
        if frame[col].dtype=='object':
            codes=sorted(set(frame.iloc[train][col])-{'unknown'})
            cols.append(frame[col].map({v:i for i,v in enumerate(codes)}).to_numpy(float))
        else:
            cols.append(frame[col].to_numpy(float))
    return np.column_stack(cols)


def prepare(name, seed):
    X, y, human_error = load_dataset(name)
    # Hash before converting categories; mappings are fitted only on train rows.
    tr, ca, ga, te = C.group_split(np.asarray(X), y, seed)
    if isinstance(X, pd.DataFrame):
        X = encode_training_categories(X,tr)
    Q = C.Quality(X[tr]); base = C.Base(X[tr], y[tr], seed)
    conds = ('clean',) if name == 'human' else C.TRAIN_CONDITIONS
    rng = np.random.default_rng(seed*7919 + 1)
    Xc = np.vstack([C.corrupt(X[ca], y[ca], c, rng, Q)[0] for c in conds])
    base.calibrate(Xc, np.tile(y[ca], len(conds)))
    G = dict(X=np.vstack([C.corrupt(X[ga], y[ga], c, rng, Q)[0] for c in conds]),
             y=np.tile(y[ga], len(conds)), Xclean=np.tile(X[ga], (len(conds), 1)))
    S.feats(G, base, Q, C.Costs())
    G['p_clean'] = np.tile(base.proba(X[ga]), len(conds))
    # Original feature hashes, not corrupted copies, define inner split groups.
    groups = pd.util.hash_pandas_object(pd.DataFrame(X[ga]), index=False).to_numpy()
    return dict(X=X, y=y, idx=(tr,ca,ga,te), Q=Q, base=base, G=G,
        ds=name, seed=seed, groups=np.tile(groups, len(conds)), human_error=human_error)


def run_seed(name, seed, destination=None):
    costs = C.Costs(); P = prepare(name, seed); G=P['G']; n=len(G['y'])
    all_rows = np.ones(n, bool); ones=np.ones(n)
    A={k:fit_head(G['reps'][k], G['la'], all_rows, ones, P['groups'],seed,False)
       for k in ('prob','quality','rich')}
    conditions = ('clean',) if name == 'human' else CONDITIONS
    tests={c:S.test_set(P,c,costs) for c in conditions}
    reviewers=('empirical',) if name == 'human' else REVIEWERS
    rows=[]
    for rv in reviewers:
        ctx=C.ReviewerContext(P['Q'],seed,P['Q'].d)
        if rv == 'empirical':
            e=P['human_error'][P['idx'][2]]
        else:
            e=ctx.error(rv,G['u'],G['v'],G['Xclean'],G['yh'],G['y'],G['p_clean'])
        rng=np.random.default_rng(seed*104729 + (0 if rv=='empirical' else C.REVIEWERS.index(rv)))
        # Bernoulli with empirical frequency == sampling one recorded binary choice.
        lh=C.Costs.weight(costs,G['y'])*(rng.random(n)<e)
        uniforms=rng.random(n)
        for policy in POLICIES:
            prob=propensity(policy,G['p'],G['u'],G['v'],costs)
            logged=uniforms<prob
            model_cache={}
            for weighting in ('unweighted','ipw'):
                # Constant IPW weights are exactly equivalent, so reuse random fit.
                if policy=='random' and weighting=='ipw':
                    H, single = model_cache['random']
                else:
                    H={k:fit_head(G['reps'][k],lh,logged,prob,P['groups'],seed,weighting=='ipw')
                       for k in ('prob','quality','rich')}
                    single=fit_head(G['reps']['quality'],G['la']-lh-costs.review,
                                    logged,prob,P['groups'],seed,weighting=='ipw')
                    if policy=='random':model_cache['random']=(H,single)
                iw=1/prob[logged]
                ess=iw.sum()**2/(iw@iw)
                for cond,T in tests.items():
                    if rv=='empirical':
                        eh=P['human_error'][P['idx'][3]]
                    else:
                        eh=ctx.error(rv,T['u'],T['v'],T['Xclean'],T['yh'],T['y'],T['p_clean'])
                    true_h=costs.weight(T['y'])*eh
                    a={k:np.clip(m.predict(T['reps'][k]),0,5) for k,(m,_) in A.items()}
                    h={k:np.clip(m.predict(T['reps'][k]),0,5) for k,(m,_) in H.items()}
                    gains={
                        'prob':(a['prob']-h['prob']-costs.review,-h['prob']),
                        'quality_A':(a['quality']-h['prob']-costs.review,-h['prob']),
                        'quality_both':(a['quality']-h['quality']-costs.review,-h['quality']),
                        'features':(a['rich']-h['rich']-costs.review,-h['rich']),
                        'single':(single[0].predict(T['reps']['quality']), None),
                        'confidence':(-abs(T['p']-costs.threshold),None),
                        'chow':(T['s'],None),
                        'rules_only':(np.zeros(len(T['y'])),None)}
                    # Mandatory ordering is common (H_prob) for estimator contrasts
                    # in addition to native overload ordering, preventing confounding.
                    mandatory=S.Rules()(T['u'],T['v'])
                    for cap in ((.2,) if name=='human' else CAPACITIES):
                        B=int(np.floor(cap*len(T['y'])))
                        for method,(score,mand_score) in gains.items():
                            for arm in ('native','fill','matched'):
                                admit=np.ones(len(score),bool) if arm=='fill' or method in ('confidence','chow') else score>0
                                if method=='rules_only':admit=np.zeros(len(score),bool)
                                ms=-h['prob'] if arm=='matched' or mand_score is None else mand_score
                                review,hold=C.allocate(mandatory,B,score,admit,ms)
                                rows.append(dict(dataset=name,seed=seed,reviewer=rv,logging=policy,
                                    weighting=weighting,condition=cond,capacity=cap,method=method,arm=arm,
                                    **C.evaluate(review,hold,T['la'],true_h,mandatory,costs),
                                    n=len(score),n_gain=n,logged=int(logged.sum()),ess=ess,
                                    log_mand=float(logged[S.Rules()(G['u'],G['v'])].mean()) if S.Rules()(G['u'],G['v']).any() else np.nan,
                                    log_optional=float(logged[~S.Rules()(G['u'],G['v'])].mean()),
                                    A_leaves=json.dumps({k:v[1] for k,v in A.items()},sort_keys=True),
                                    H_leaves=json.dumps({k:v[1] for k,v in H.items()},sort_keys=True),
                                    single_leaves=single[1],
                                    mandatory=float(mandatory.mean()),
                                    defect_recall=float(mandatory[T['defect']>0].mean()) if (T['defect']>0).any() else np.nan,
                                    defective_automated=float((~review&~hold)[T['defect']>0].mean()) if (T['defect']>0).any() else np.nan))
                        # Full quality model: isolate overload ordering and rules.
                        for arm,on,gorder in [('gain_overload',True,True),('no_rules',False,False)]:
                            score,ms=gains['quality_both']
                            m=mandatory if on else np.zeros(len(score),bool)
                            review,hold=C.allocate(m,B,score,score>0,score if gorder else ms)
                            rows.append(dict(dataset=name,seed=seed,reviewer=rv,logging=policy,
                                weighting=weighting,condition=cond,capacity=cap,method='quality_both',arm=arm,
                                **C.evaluate(review,hold,T['la'],true_h,mandatory,costs),n=len(score)))
    out=pd.DataFrame(rows)
    if destination:
        out.to_csv(destination,index=False,compression={'method':'gzip','mtime':0},float_format='%.12g')
    return out


def analyze():
    df=pd.read_csv(RESULTS/'revision.csv.gz')
    index=['dataset','seed','reviewer','logging','weighting','condition','capacity','method','arm']
    assert not df.duplicated(index).any()
    assert (df.review <= df.capacity + 1e-10).all()
    assert (df[df.arm!='no_rules'].violation==0).all()
    primary=df[(df.dataset=='bank')&(df.condition=='informative')&(df.logging=='random')&
        (df.weighting=='unweighted')&(df.capacity==.2)&(df.arm=='matched')&df.method.isin(['quality_A','prob'])]
    p=primary.groupby(['seed','method']).cost.mean().unstack()
    assert len(p)==20
    def comparison(x,a,b):
        mean,lo,hi,pv=ST.corrected_t(x[b]-x[a])
        return dict(diff=mean,lo=lo,hi=hi,p=pv,relative=100*mean/x[b].mean(),
                    wins=int((x[b]>x[a]).sum()),n=len(x))
    summary={'primary':comparison(p,'quality_A','prob')}
    summary['primary']['success']=bool(summary['primary']['p']<.05 and
        summary['primary']['diff']>0 and summary['primary']['relative']>=1)
    rows=[]
    for ds in ('default','bank'):
        for policy in POLICIES:
            sub=df[(df.dataset==ds)&(df.logging==policy)&(df.capacity==.2)&
                (df.method=='quality_both')&(df.arm=='matched')]
            x=sub.groupby(['seed','weighting']).cost.mean().unstack()
            rows.append(dict(dataset=ds,logging=policy,**comparison(x,'ipw','unweighted')))
    adj=ST.holm([r['p'] for r in rows])
    for r,v in zip(rows,adj):r['p_holm']=float(v)
    summary['secondary_family_6']=rows
    summary['checks']={'rows':len(df),'unique_cells':True,'capacity':True,'no_policy_violations':True,
        'seeds':sorted(df.seed.unique().tolist()),'datasets':sorted(df.dataset.unique().tolist())}
    (RESULTS/'revision-summary.json').write_text(json.dumps(summary,indent=2))
    # Export every per-split contrast, not only the favorable ones.
    contrasts=[]
    for keys,sub in df[df.arm=='matched'].groupby(['dataset','logging','weighting','condition','capacity']):
        x=sub.groupby(['seed','method']).cost.mean().unstack()
        for method in ('quality_A','quality_both','features','single','confidence','chow'):
            for seed,r in x.iterrows():
                contrasts.append(dict(zip(['dataset','logging','weighting','condition','capacity'],keys),
                    seed=int(seed),method=method,baseline='prob',diff=r['prob']-r[method]))
    pd.DataFrame(contrasts).to_csv(RESULTS/'revision-contrasts.csv.gz',index=False,
        compression={'method':'gzip','mtime':0},float_format='%.12g')
    print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fetch','run','analyze']);p.add_argument('--jobs',type=int,default=4)
    p.add_argument('--datasets',nargs='+',default=['default','bank','human']);p.add_argument('--seed',type=int)
    args=p.parse_args();RESULTS.mkdir(exist_ok=True)
    if args.action=='fetch':
        DATA.mkdir(exist_ok=True)
        urls={
          'bank.zip':'https://archive.ics.uci.edu/static/public/222/bank+marketing.zip',
          'default.zip':'https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip',
          'cifar10h-raw.zip':'https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-raw.zip',
          'cifar-10-python.tar.gz':'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz'}
        for name,url in urls.items():
            if not (DATA/name).exists():urllib.request.urlretrieve(url,DATA/name)
        z=zipfile.ZipFile(DATA/'default.zip')
        pd.read_excel(io.BytesIO(z.read(z.namelist()[0])),header=None).to_csv(
            DATA/'default.csv',header=False,index=False)
        print('Downloaded original public sources. Run manifest records hashes.')
        return
    if args.action=='analyze':return analyze()
    seeds=(args.seed,) if args.seed is not None else SEEDS
    work=RESULTS/'revision-parts';work.mkdir(exist_ok=True)
    tasks=[(ds,seed,work/f'{ds}-{seed}.csv.gz') for ds in args.datasets for seed in seeds]
    # Checkpoint each seed. Existing parts are reproducible checkpoints, never
    # silently reused after source edits: source hash must match the manifest.
    source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest=RESULTS/'revision-environment.json'
    env=dict(python=platform.python_version(),packages={k:metadata.version(k) for k in
        ['numpy','pandas','scipy','scikit-learn','matplotlib','joblib']},source_sha256=source,
        plan_commit='656f5270e5b8d48bf096c0644409397adc55e659',datasets={})
    for f in DATA.iterdir():
        if f.is_file():env['datasets'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    if manifest.exists() and json.loads(manifest.read_text())['source_sha256']!=source:
        raise RuntimeError('Source changed: archive old parts and manifest before rerunning')
    manifest.write_text(json.dumps(env,indent=2))
    with concurrent.futures.ProcessPoolExecutor(args.jobs) as pool:
        fs={pool.submit(run_seed,ds,seed,path):(ds,seed) for ds,seed,path in tasks if not path.exists()}
        for f in concurrent.futures.as_completed(fs):
            out=f.result();print(fs[f],len(out),'rows',flush=True)
    pd.concat([pd.read_csv(path) for _,_,path in tasks],ignore_index=True).to_csv(
        RESULTS/'revision.csv.gz',index=False,compression={'method':'gzip','mtime':0},float_format='%.12g')


if __name__=='__main__':
    main()
