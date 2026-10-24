"""Figure 1: matched quality effect for all frozen condition/logging cells.
Legacy filename retained; old volume code/figure remain in git history.
"""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dqd import stats as ST
root=Path(__file__).resolve().parents[1]
d=pd.read_csv(root/'results/revision.csv.gz')
d=d[(d.capacity==.2)&(d.weighting=='unweighted')&(d.arm=='matched')&d.method.isin(['prob','quality_A'])]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
    'axes.titlesize':10,'legend.fontsize':8,'xtick.labelsize':8,'ytick.labelsize':8,
    'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(7.1,2.75),sharey=True,layout='constrained')
conditions=['clean','informative','stale','shift'];data=[]
for ax,ds,title in zip(axs,['default','bank'],['(a) Default: development','(b) Bank: new validation']):
    for j,(policy,label,color,marker) in enumerate([
        ('random','Random','#0072B2','o'),('uncertainty','Uncertainty-prioritized','#D55E00','^'),
        ('rules','Rule-prioritized','#009E73','s')]):
        vals=[];err=[]
        for cond in conditions:
            s=d[(d.dataset==ds)&(d.logging==policy)&(d.condition==cond)]
            x=s.groupby(['seed','method']).cost.mean().unstack()
            m,lo,hi,p=ST.corrected_t(x['prob']-x['quality_A']);scale=100/x['prob'].mean()
            vals.append(m*scale);err.append([(m-lo)*scale,(hi-m)*scale])
            data.append(dict(dataset=ds,logging=policy,condition=cond,relative=m*scale,
                lo=lo*scale,hi=hi*scale,p=p,n=len(x),primary=(ds=='bank' and policy=='random' and cond=='informative')))
        ax.errorbar(np.arange(4)+(j-1)*.19,vals,yerr=np.array(err).T,color=color,
            marker=marker,markersize=4,capsize=2,elinewidth=.8,linewidth=.8,linestyle='none',label=label)
    ax.axhline(0,color='#555555',linewidth=.7,linestyle='--')
    ax.set_xticks(range(4),['Clean','Informative\nmissingness','Stale','Severe\nshift'])
    ax.set_title(title,loc='left');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
axs[0].set_ylabel('Cost reduction versus probability-only (%)')
handles,labels=axs[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='outside upper center',ncol=3,frameon=False)
(root/'figs').mkdir(exist_ok=True)
fig.savefig(root/'figs/fig3_volume.pdf',bbox_inches='tight')
fig.savefig(root/'figs/fig3_volume.png',dpi=450,bbox_inches='tight')
(root/'results/revision-figure.json').write_text(json.dumps(data,indent=2))
plt.close(fig)
print('Generated Figure 1 from',len(data),'complete cells')
