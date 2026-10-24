"""Cybersecurity extension: fetch, verify, run, analyze, report. See root protocol.

No operational analyst data are claimed. All losses are benchmark/simulation
quantities; randomization intervals condition on the acquired traffic corpora.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, io, json, math, os, platform
import time, urllib.request, importlib.metadata as md
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from . import core as C, revision as R

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/cyber'
OUT=ROOT/'results'
SEEDS=tuple(range(2,22))
CONDITIONS=('clean','outage','severe','replacement')
METHODS=('prob','quality_A','quality_both','features','single','confidence','chow','rules_only','random','conformal')
CAPS=(.05,.10,.20)
COSTS=C.Costs()
HF='https://huggingface.co/datasets/'
CIC_REV='70bac6246d99cf046186a02e1cce6883e2ffe7ea'
UNSW_REV='6f5f54594dfc80c84264aec4c7cc3d9b162f1e2f'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(obj,path):
    path=Path(path);b=json.dumps(obj,indent=2,allow_nan=False).encode()
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(b);tmp.replace(path)

def fetch():
    DATA.mkdir(exist_ok=True,parents=True)
    manifest=[]
    for dataset,rev,folder in [('Mouwiya/UNSW-NB15-small',UNSW_REV,''),('bvsam/cic-ids-2017',CIC_REV,'traffic_labels')]:
        url=f'https://huggingface.co/api/datasets/{dataset}/tree/{rev}/'+folder
        tree=json.load(urllib.request.urlopen(url,timeout=60))
        for x in tree:
            if not x['path'].endswith(('.csv','.parquet')) or ('UNSW' not in x['path'] and folder==''):continue
            name=x['path'].split('/')[-1];target=DATA/name
            u=HF+dataset+'/resolve/'+rev+'/'+x['path']
            if not target.exists():
                with urllib.request.urlopen(u,timeout=60) as f:b=f.read()
                target.write_bytes(b)
            expected=x['lfs']['oid'];actual=sha(target)
            if actual!=expected:raise ValueError(f'Download hash mismatch: {name}')
            manifest.append(dict(name=name,url=u,sha256=actual,bytes=target.stat().st_size,mirror_hash_verified=True))
    dump(manifest,DATA/'acquisition.json')
    return manifest

def hashes(frame):
    return pd.util.hash_pandas_object(frame,index=False).to_numpy(np.uint64)

def merge_groups(feature,session):
    """Connected components of equal features OR equal capture-session keys."""
    parent=np.arange(len(feature))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for values in (feature,session):
        first={}
        for i,v in enumerate(values):
            if v in first:parent[root(i)]=root(first[v])
            else:first[v]=i
    return np.array([root(i) for i in range(len(feature))],dtype=np.int64)

def families(columns,ds):
    if ds=='unsw':
        groups=[[],[],[],[]]
        timing={'dur','sinpkt','dinpkt','sjit','djit','tcprtt','synack','ackdat'}
        context={'proto','service','state','sttl','dttl'}
        for j,c in enumerate(columns):
            k=0 if c in timing else 1 if c in context else 2 if c.startswith('ct_') or c.startswith('is_') else 3
            groups[k].append(j)
    else:
        groups=[[],[],[],[]]
        for j,c in enumerate(columns):
            k=0 if any(t in c for t in ['Duration','IAT','Active','Idle']) else 1 if any(t in c for t in ['Flag','Protocol','Port','Window','Win_']) else 2 if any(t in c for t in ['Length','Size','Bytes']) else 3
            groups[k].append(j)
    if any(len(g)==0 for g in groups):raise ValueError('Empty acquisition family')
    return groups

def cap_frame(frame,cap):
    if len(frame)<=cap:return frame
    # Feature/group hashes, not outcomes, determine the sampled corpus.
    return frame.sort_values('_hash',kind='stable').iloc[:cap].copy()

def verify():
    """Read all source rows; schema/label/leakage audit only, no fitted models."""
    metadata={'sources':json.loads((DATA/'acquisition.json').read_text()),'datasets':{}}
    for name in ('unsw','cic'):
        frames={};audit=[]
        if name=='unsw':
            paths=sorted(DATA.glob('UNSW*set.csv'))
        else:paths=sorted(DATA/x['name'] for x in metadata['sources'] if x['name'].endswith('.parquet'))
        for path in paths:
            raw=pd.read_csv(path) if name=='unsw' else pd.read_parquet(path)
            raw.columns=raw.columns.str.strip()
            lab='label' if name=='unsw' else 'Label'
            missing_label=int(raw[lab].isna().sum());d=raw[raw[lab].notna()].copy()
            y=d[lab].astype(int) if name=='unsw' else (d[lab].astype(str).str.strip()!='BENIGN').astype(int)
            cats=d['attack_cat'].astype(str) if name=='unsw' else d[lab].astype(str)
            excluded=['id','attack_cat','label'] if name=='unsw' else ['Flow ID','Source IP','Source Port','Destination IP','Destination Port','Timestamp','Label','Fwd Header Length.1']
            X=d.drop(columns=excluded)
            nonfinite=negative=0
            for col in X:
                if X[col].dtype=='object':X[col]=X[col].astype(str)
                else:
                    z=pd.to_numeric(X[col],errors='coerce').to_numpy(float)
                    nonfinite+=int((~np.isfinite(z)).sum());negative+=int((z<0).sum())
                    z[(~np.isfinite(z))|(z<0)]=np.nan;X[col]=z
            h=hashes(X)
            X['_y']=y.to_numpy();X['_category']=cats.to_numpy();X['_hash']=h
            X['_group']=h if name=='unsw' else hashes(pd.DataFrame({'session':d['Flow ID'].astype(str).to_numpy(),'date':d['Timestamp'].dt.strftime('%Y-%m-%d').to_numpy()}))
            before=len(X);X=X.drop_duplicates(subset=list(X.columns.drop(['_category','_hash','_group'])))
            dup=before-len(X)
            part=('dev' if 'training' in path.name else 'test') if name=='unsw' else ('test' if path.name.startswith('Friday') else 'calgain' if path.name.startswith('Thursday') else 'train')
            frames.setdefault(part,[]).append(X)
            audit.append(dict(file=path.name,rows=len(raw),unlabeled=missing_label,labeled=before,attacks=int(y.sum()),benign=int((y==0).sum()),exact_duplicates=dup,nonfinite_cells=nonfinite,negative_cells=negative,features=len(X.columns)-4))
        frames={p:pd.concat(v,ignore_index=True).drop_duplicates(subset=list(v[0].columns.drop(['_category','_hash','_group']))) for p,v in frames.items()}
        # Earlier role owns a duplicate's features. Test labels never choose exclusions.
        earlier=set();removals={}
        order=('dev','test') if name=='unsw' else ('train','calgain','test')
        for role in order:
            d=frames[role];over=d['_hash'].isin(earlier);removals[role]=int(over.sum())
            d=d[~over].copy();earlier.update(d['_hash'].tolist());frames[role]=d
        limits={'dev':80000,'train':60000,'calgain':40000,'test':40000 if name=='cic' else 1000000}
        for role in frames:
            frames[role]=cap_frame(frames[role],limits[role])
            if name=='cic':frames[role]['_group']=merge_groups(frames[role]['_hash'].to_numpy(),frames[role]['_group'].to_numpy())
        cols=[x for x in frames[order[0]] if not x.startswith('_')]
        out=dict(files=audit,cross_role_exclusions=removals,features=cols,families=[[cols[j] for j in g] for g in families(cols,name)],roles={})
        for role,d in frames.items():
            out['roles'][role]=dict(rows=len(d),attacks=int(d['_y'].sum()),benign=int((d['_y']==0).sum()),groups=int(d['_group'].nunique()))
            target=DATA/f'{name}-{role}.parquet';d.to_parquet(target,index=False)
            out['roles'][role]['prepared_sha256']=sha(target)
        metadata['datasets'][name]=out
    dump(metadata,OUT/'cyber-data-verification.json')
    print(json.dumps(metadata['datasets'],indent=2))

def split_groups(h,seed,fractions=(.6,.2,.2)):
    u=np.unique(h);r=np.random.default_rng(seed).permutation(len(u));role=np.empty(len(u),int)
    cuts=np.cumsum((0,)+fractions);ends=(cuts*len(u)).astype(int);ends[-1]=len(u)
    for j in range(len(fractions)):role[r[ends[j]:ends[j+1]]]=j
    return role[np.searchsorted(u,h)]

def encode(frame,train):
    return R.encode_training_categories(frame,train) if any(frame.dtypes=='object') else frame.to_numpy(float)

def corrupt(X,condition,rng,groups,donors):
    """Label-independent family loss/replacement; labels are not arguments."""
    Z=X.copy();defect=np.zeros(len(X),bool)
    if condition=='clean':return Z,defect
    affected=np.ones(len(X),bool) if condition=='severe' else rng.random(len(X))<.5
    family=rng.integers(0,4,len(X));defect=affected.copy()
    for k in range(4):
        rows=np.flatnonzero(affected&(family==k))
        selected=groups[k] if condition!='severe' else sorted(set(range(X.shape[1]))-set(groups[k]))
        if condition=='replacement':
            donor=rng.integers(0,len(donors),len(rows));Z[np.ix_(rows,selected)]=donors[np.ix_(donor,selected)]
        else:Z[np.ix_(rows,selected)]=np.nan
    return Z,defect

def measure(X,Q,groups):
    u,v=Q.measure(X)
    f=np.column_stack([np.isnan(X[:,g]).mean(1) for g in groups])
    return u,v,f

def representations(p,X,Q,groups):
    u,v,f=measure(X,Q,groups);s=np.minimum(5*p,1-p);yh=p>=1/6
    return {'prob':np.c_[p,s], 'quality':np.c_[p,s,u,v,f,p[:,None]*f], 'rich':np.c_[p,s,u,v,f,X]},u,v,yh

def thresholds(p,y,alpha=.05,beta=.05):
    b=np.sort(p[y==0]);t=np.sort(p[y==1]);kh=math.ceil((1-alpha)*(len(b)+1));kl=math.floor(beta*(len(t)+1))
    return (b[kh-1] if 1<=kh<=len(b) else np.inf,t[kl-1] if 1<=kl<=len(t) else -np.inf)

def reviewer(y,yh,pclean,kind):
    return np.full(len(y),.1) if kind=='constant' else np.minimum(.45,.05+.25*(yh!=y)+.1*(1-np.abs(2*pclean-1)))

def metrics(r,h,y,yh,e,m,costs=COSTS):
    a=~r&~h;w=costs.weight(y)
    out=C.evaluate(r,h,w*(yh!=y),w*e,m,costs)
    den1=max(1,int(y.sum()));den0=max(1,int((y==0).sum()))
    out.update(auto_close_attack=float((a&(y==1)&~yh).sum()/den1),benign_escalation=float((a&(y==0)&yh).sum()/den0),held_attack=float((h&(y==1)).sum()/den1),unmet_attack=float(((a&(y==1)&~yh).sum()+(r*(y==1)*e).sum()+(h&(y==1)).sum())/den1),review_error=float((r*e).sum()/max(1,r.sum())),reviewed=int(r.sum()),held=int(h.sum()))
    return out

def run_seed(ds,seed):
    start=time.monotonic()
    if ds=='unsw':
        D=pd.read_parquet(DATA/'unsw-dev.parquet');te=pd.read_parquet(DATA/'unsw-test.parquet')
        roles=split_groups(D['_group'].to_numpy(),seed)
        tr,ca,ga=[np.flatnonzero(roles==i) for i in range(3)]
    else:
        trd=pd.read_parquet(DATA/'cic-train.parquet');cg=pd.read_parquet(DATA/'cic-calgain.parquet');te=pd.read_parquet(DATA/'cic-test.parquet')
        D=pd.concat([trd,cg],ignore_index=True);tr=np.arange(len(trd))
        roles=split_groups(cg['_group'].to_numpy(),seed,(.375,.625))
        ca=np.flatnonzero(roles==0)+len(trd);ga=np.flatnonzero(roles==1)+len(trd)
    cols=[c for c in D if not c.startswith('_')];groups=families(cols,ds)
    full=pd.concat([D[cols],te[cols]],ignore_index=True);X=encode(full,tr);Xt=X[len(D):];X=X[:len(D)]
    y=D['_y'].to_numpy(int);yt=te['_y'].to_numpy(int);Q=C.Quality(X[tr])
    clf=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,learning_rate=.07,l2_regularization=1.,early_stopping=False,random_state=seed).fit(X[tr],y[tr])
    def logit(Z):
        p=np.clip(clf.predict_proba(Z)[:,1],1e-6,1-1e-6);return np.log(p/(1-p))[:,None]
    rng=np.random.default_rng(seed*7919)
    calX=np.vstack([corrupt(X[ca],c,rng,groups,X[tr])[0] for c in ('clean','outage','severe')]);caly=np.tile(y[ca],3)
    cal=LogisticRegression(C=1.).fit(logit(calX),caly)
    def proba(Z):return cal.predict_proba(logit(Z))[:,1]
    GX=np.vstack([corrupt(X[ga],c,rng,groups,X[tr])[0] for c in ('clean','outage','severe')]);gy=np.tile(y[ga],3)
    gp=proba(GX);Z,gu,gv,gyh=representations(gp,GX,Q,groups);gclean=np.tile(proba(X[ga]),3)
    # This pool is disjoint from detector training and logistic calibration.
    # Corrupted copies are dependent; no exchangeability guarantee is asserted.
    theta=thresholds(gp,gy)
    gh=np.tile(D['_group'].to_numpy()[ga],3);allrows=np.ones(len(gy),bool);ones=np.ones(len(gy))
    la=COSTS.weight(gy)*(gyh!=gy)
    A={k:R.fit_head(z,la,allrows,ones,gh,seed,False)[0] for k,z in Z.items()}
    tests={}
    for j,condition in enumerate(CONDITIONS):
        z,defect=corrupt(Xt,condition,np.random.default_rng(seed*31337+j),groups,X[tr]);p=proba(z)
        reps,u,v,yh=representations(p,z,Q,groups)
        tests[condition]=dict(reps=reps,p=p,u=u,v=v,yh=yh,defect=defect,pclean=proba(Xt),a={k:np.clip(model.predict(reps[k]),0,5) for k,model in A.items()})
    rows=[]
    for kind in ('constant','correlated'):
        e=reviewer(gy,gyh,gclean,kind);rg=np.random.default_rng(seed*104729+(kind=='correlated'))
        lh=COSTS.weight(gy)*(rg.random(len(gy))<e);logged=rg.random(len(gy))<.4
        H={k:R.fit_head(z,lh,logged,ones,gh,seed,False)[0] for k,z in Z.items()}
        single=R.fit_head(Z['quality'],la-lh-COSTS.review,logged,ones,gh,seed,False)[0]
        for condition,T in tests.items():
            p=T['p'];yh=T['yh'];n=len(yt);ee=reviewer(yt,yh,T['pclean'],kind)
            h={k:np.clip(model.predict(T['reps'][k]),0,5) for k,model in H.items()};a=T['a']
            m=(T['u']>=.5)|(T['v']>=.25)
            scores={'prob':a['prob']-h['prob']-.05,'quality_A':a['quality']-h['prob']-.05,'quality_both':a['quality']-h['quality']-.05,'features':a['rich']-h['rich']-.05,'single':single.predict(T['reps']['quality']),'confidence':-abs(p-1/6),'chow':np.minimum(5*p,1-p),'rules_only':np.zeros(n),'random':rg.random(n)}
            for cap in CAPS:
                B=int(cap*n)
                for method in METHODS:
                    for arm in ('matched','native'):
                        if method=='conformal':
                            if arm=='matched':continue
                            high,low=theta;band=~((p>high)|(p<low));mm=m|band
                            yy=np.where(p<low,False,np.where(p>high,True,yh))
                            r,hold=C.allocate(mm,B,-abs(p-1/6),np.zeros(n,bool),-h['prob'])
                        else:
                            mm=m;yy=yh;scores_i=scores[method]
                            admit=np.ones(n,bool) if arm=='matched' or method in ('confidence','chow','random') else scores_i>0
                            if method=='rules_only':admit=np.zeros(n,bool)
                            mand=-h['quality'] if arm=='native' and method=='quality_both' else -h['rich'] if arm=='native' and method=='features' else -h['prob']
                            r,hold=C.allocate(mm,B,scores_i,admit,mand)
                        common=dict(dataset=ds,seed=seed,reviewer=kind,condition=condition,capacity=cap,method=method,arm=arm,n=n,mandatory=float(mm.mean()),logged=int(logged.sum()),n_gain=len(gy),defect_coverage=float(m[T['defect']].mean()) if T['defect'].any() else 0.)
                        rows.append(dict(**common,**metrics(r,hold,yt,yy,ee,mm)))
                        # Fixed-route valuation sensitivity, not retrained policies.
                        if method in ('prob','quality_A') and arm=='matched' and cap==.2:
                            for fn in (2.,10.,20.):
                                cc=C.Costs(fn=fn)
                                rows.append(dict(**{**common,'arm':f'valuation_fn{int(fn)}'},**metrics(r,hold,yt,yy,ee,mm,cc)))
                # Rules ablation: same estimates, fill the budget, no mandatory set.
                score=scores['quality_both'];r,hold=C.allocate(np.zeros(n,bool),B,score,np.ones(n,bool),-h['quality'])
                rows.append(dict(dataset=ds,seed=seed,reviewer=kind,condition=condition,capacity=cap,method='quality_both',arm='no_rules',n=n,mandatory=float(m.mean()),logged=int(logged.sum()),n_gain=len(gy),defect_coverage=float(m[T['defect']].mean()) if T['defect'].any() else 0.,**metrics(r,hold,yt,yh,ee,m)))
    df=pd.DataFrame(rows);R.atomic_csv(df,OUT/f'cyber-parts/{ds}-{seed}.csv.gz')
    return ds,seed,len(df),round(time.monotonic()-start,1)

def run(jobs=4,ds=None,seed=None):
    (OUT/'cyber-parts').mkdir(exist_ok=True)
    env={'source_sha256':sha(__file__),'core_sha256':sha(C.__file__),'head_fitting_sha256':sha(R.__file__),'python':platform.python_version(),'packages':{p:md.version(p) for p in ['numpy','pandas','scipy','scikit-learn','pyarrow','matplotlib']},'plan_commit':os.environ.get('CYBER_PLAN_COMMIT','unrecorded'),'verification_sha256':sha(OUT/'cyber-data-verification.json')}
    manifest=OUT/'cyber-environment.json'
    if manifest.exists() and json.loads(manifest.read_text())!=env:raise ValueError('Environment/source changed; archive old checkpoints before resuming')
    dump(env,manifest)
    tasks=[(d,s) for d in (ds or ('unsw','cic')) for s in ((seed,) if seed else SEEDS)]
    with concurrent.futures.ProcessPoolExecutor(jobs) as ex:
        fs=[ex.submit(run_seed,d,s) for d,s in tasks if not (OUT/f'cyber-parts/{d}-{s}.csv.gz').exists()]
        for f in concurrent.futures.as_completed(fs):print(f.result(),flush=True)
    files=[OUT/f'cyber-parts/{d}-{s}.csv.gz' for d,s in tasks]
    R.atomic_csv(pd.concat([pd.read_csv(p) for p in files],ignore_index=True),OUT/'cyber-results.csv.gz')

def contrast(values):
    x=np.asarray(values,float);mean=float(x.mean());se=float(stats.sem(x))
    if se<1e-14:return dict(diff=mean,lo=mean,hi=mean,p=1. if abs(mean)<1e-14 else 0.,wins=int((x>0).sum()),seeds=len(x))
    lo,hi=stats.t.interval(.95,len(x)-1,loc=mean,scale=se)
    return dict(diff=mean,lo=float(lo),hi=float(hi),p=float(stats.ttest_1samp(x,0).pvalue),wins=int((x>0).sum()),seeds=len(x))

def analyze():
    df=pd.read_csv(OUT/'cyber-results.csv.gz');keys=['dataset','seed','reviewer','condition','capacity','method','arm']
    assert not df.duplicated(keys).any()
    assert len(df)==40*528,('incomplete grid',len(df))
    assert (df.review<=df.capacity+1e-12).all()
    assert (df[df.arm!='no_rules'].violation==0).all()
    pair=df[(df.arm=='matched')&df.method.isin(['prob','quality_A'])]
    for _,sub in pair.groupby(['dataset','seed','reviewer','condition','capacity']):
        assert sub.reviewed.nunique()==1 and sub.held.nunique()==1
        if (sub.mandatory>sub.capacity).all():assert sub.cost.max()-sub.cost.min()<1e-10
    rows=[]
    for ds in ('unsw','cic'):
        for cond in CONDITIONS:
            p=pair[(pair.dataset==ds)&(pair.condition==cond)&(pair.capacity==.2)].groupby(['seed','method']).cost.mean().unstack()
            assert len(p)==20
            result=contrast(p['prob']-p['quality_A'])
            result.update(dataset=ds,condition=cond,baseline=float(p['prob'].mean()),quality=float(p['quality_A'].mean()),relative=100*result['diff']/p['prob'].mean(),primary=ds=='unsw' and cond=='outage')
            rows.append(result)
    secondary=[r for r in rows if not r['primary']]
    from .stats import holm
    for r,pv in zip(secondary,holm([r['p'] for r in secondary])):r['p_holm']=float(pv)
    primary=next(r for r in rows if r['primary']);primary['success']=bool(primary['diff']>0 and primary['relative']>=1 and primary['p']<.05)
    dump(dict(primary=primary,contrasts=rows,rows=len(df),checks=dict(unique_cells=True,budgets=True,policy_compliance=True,matched_counts=True,overload_null=True)),OUT/'cyber-summary.json')
    pd.DataFrame(rows).to_csv(OUT/'cyber-contrasts.csv',index=False,float_format='%.12g')
    print(json.dumps(primary,indent=2))

def export_figure(fig,path):
    for suffix,kwargs in [('pdf',{}),('png',{'dpi':450})]:
        b=io.BytesIO();fig.savefig(b,format=suffix,bbox_inches='tight',**kwargs);payload=b.getvalue()
        assert len(payload)>1000
        if suffix=='pdf':assert payload.startswith(b'%PDF') and b'%%EOF' in payload[-30:]
        target=path.with_suffix('.'+suffix);tmp=target.with_suffix(target.suffix+'.tmp');tmp.write_bytes(payload);tmp.replace(target)

def report():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    figs=ROOT/'figs';figs.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(7.2,3.5));ax.set(xlim=(0,10),ylim=(0,5));ax.axis('off')
    def box(x,y,w,h,label,color='#edf3f7'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.08',facecolor=color,edgecolor='#29465b',linewidth=.9));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=8)
    def arrow(x,y,xx,yy):ax.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'->','lw':1,'color':'#29465b'})
    box(.1,2.5,1.6,1.2,'Completed-flow\ntelemetry')
    box(2.3,3.3,2.1,.9,'Calibrated detector\nprobability / risk')
    box(2.3,1.7,2.1,.9,'Observable quality\nmissingness / range')
    box(5.1,2.5,2.1,1.2,'Loss estimates\n+ knowledge rules')
    box(7.9,2.5,1.7,1.2,'Budgeted allocation\nautomate / review\nor hold unresolved')
    arrow(1.8,3.1,2.2,3.65);arrow(1.8,3.1,2.2,2.2);arrow(4.5,3.7,5,3.3);arrow(4.5,2.2,5,2.8);arrow(7.3,3.1,7.8,3.1)
    box(.2,.15,9.3,.85,'Matched comparison: change automation-loss inputs only; share detector, reviewer-loss head,\nknowledge rules, mandatory ordering and review counts. Overload implies zero routing effect.','#f4f1e8')
    ax.text(.1,4.65,'Quality can improve ranking; it cannot create analyst capacity.',fontsize=10,weight='bold')
    export_figure(fig,figs/'cyber_fig1');plt.close(fig)
    df=pd.read_csv(OUT/'cyber-results.csv.gz')
    wanted=['prob','quality_A','quality_both','chow','conformal']
    sub=df[((df.arm=='matched')&(df.method!='conformal'))|((df.arm=='native')&(df.method=='conformal'))]
    agg=sub[sub.method.isin(wanted)].groupby(['dataset','seed','capacity','method'])[['cost','unmet_attack']].mean().reset_index()
    fig,axes=plt.subplots(2,2,figsize=(7.2,5.0),sharex=True)
    colors=['#0072b2','#d55e00','#009e73','#cc79a7','#333333'];names=['Probability only','Quality in A','Quality in A and H','Chow risk','Conformal adaptation']
    for col,ds in enumerate(('unsw','cic')):
        for row,metric in enumerate(('cost','unmet_attack')):
            ax=axes[row,col]
            for method,color,label in zip(wanted,colors,names):
                x=agg[(agg.dataset==ds)&(agg.method==method)].groupby('capacity')[metric]
                mean=x.mean();err=x.sem()*stats.t.ppf(.975,19)
                ax.errorbar(mean.index*100,mean.values,yerr=err.values,color=color,marker='o',ms=3,capsize=2,lw=1.3,label=label)
            ax.grid(alpha=.18);ax.set_xticks([5,10,20]);ax.set_ylabel('Cost per retained flow' if row==0 else 'Unmet attacks / all attacks')
            if row==0:ax.set_title(('(a) UNSW-NB15' if col==0 else '(b) CICIDS2017'),loc='left',fontsize=10)
            if row==1:ax.set_xlabel('Analyst review capacity (%)')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8,frameon=False)
    fig.tight_layout(rect=(0,.12,1,1));export_figure(fig,figs/'cyber_fig2');plt.close(fig)
    # Editable table bodies. Every displayed cell is derived here, never typed by hand.
    names=dict(prob='Probability only',quality_A='Quality in A',quality_both='Quality in A and H',features='Observed features',chow='Chow risk',conformal='Conformal adaptation')
    lines=[r'\newcommand{\CyberTableOne}{%',r'\begin{tabular}{llrrrrr}\toprule',r'Data & Method & Cost & Close & Esc. & Held & Unmet\\\midrule']
    display=[]
    for ds in ('unsw','cic'):
        for method,label in names.items():
            z=sub[(sub.dataset==ds)&(sub.condition=='outage')&(sub.capacity==.2)&(sub.method==method)].mean(numeric_only=True)
            vals=[float(z[c]) for c in ['cost','auto_close_attack','benign_escalation','held_attack','unmet_attack']]
            display.append(dict(dataset=ds,method=method,**dict(zip(['cost','close','escalation','held_attack','unmet_attack'],vals))))
            lines.append(f"{'UNSW' if ds=='unsw' else 'CIC'} & {label} & {vals[0]:.4f} & "+' & '.join(f'{100*v:.1f}' for v in vals[1:])+r'\\')
    lines += [r'\bottomrule\end{tabular}}',r'\newcommand{\CyberTableTwo}{%',r'\begin{tabular}{llrrlrr}\toprule',r'Data & Condition & $\Delta$ & Rel. (\%) & 95\% MC interval & $p$ & Holm\\\midrule']
    results=json.loads((OUT/'cyber-summary.json').read_text())
    def pv(x):return '$<0.001$' if x<.001 else f'{x:.3f}'
    for z in results['contrasts']:
        lines.append(f"{'UNSW' if z['dataset']=='unsw' else 'CIC'} & {z['condition']}{'*' if z['primary'] else ''} & {z['diff']:+.4f} & {z['relative']:+.2f} & [{z['lo']:+.4f}, {z['hi']:+.4f}] & {pv(z['p'])} & "+('--' if z['primary'] else pv(z['p_holm']))+r'\\')
    lines += [r'\bottomrule\end{tabular}}']
    (OUT/'cyber-tables.tex').write_text('\n'.join(lines)+'\n');dump(display,OUT/'cyber-display.json')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fetch','verify','run','analyze','report']);p.add_argument('--jobs',type=int,default=4);p.add_argument('--datasets',nargs='+');p.add_argument('--seed',type=int);a=p.parse_args()
    if a.action=='fetch':fetch()
    elif a.action=='verify':verify()
    elif a.action=='run':run(a.jobs,a.datasets,a.seed)
    elif a.action=='analyze':analyze()
    else:report()
if __name__=='__main__':main()
