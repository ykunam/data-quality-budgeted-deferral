"""Generate two manuscript tables and numerical prose from saved runs."""
from pathlib import Path
import json, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
root=Path(__file__).resolve().parents[1]
d=pd.read_csv(root/'results/revision.csv.gz')
summary=json.loads((root/'results/revision-summary.json').read_text())
base=d[(d.capacity==.2)&(d.logging=='random')&(d.weighting=='unweighted')&(d.arm=='matched')]
means=base.groupby(['dataset','method']).cost.mean().unstack()
labels={'prob':'Probability-only two-head','quality_A':'Quality in automation head',
    'quality_both':'Quality in both heads','features':'Observed-feature two-head',
    'single':'Single-head gain','confidence':'Confidence','chow':'Chow cost risk','rules_only':'Rules only'}
methods=['rules_only','confidence','chow','single','prob','quality_A','quality_both','features']
datasets=['default','bank','human']
assert set(datasets)<=set(means.index)
t1=[r'\begin{tabular}{lrrr}\toprule',r'Method & Default & Bank & CIFAR-10H \\\midrule']
for method in methods:
    cells=[]
    for ds in datasets:
        cell=f'{means.loc[ds,method]:.4f}'
        if means.loc[ds].idxmin()==method:cell=r'\textbf{'+cell+'}'
        cells.append(cell)
    t1.append(labels[method]+' & '+' & '.join(cells)+r' \\')
t1.append(r'\bottomrule\end{tabular}')
def pv(p):return '$<0.001$' if p<.001 else f'{p:.3f}'
p=summary['primary']
t2=[r'\begin{tabular}{lrrr}\toprule',r'Contrast & Reduction & 95\% interval & $p$ \\\midrule']
def row(label,r,p):
    return f"{label} & {r['diff']:+.4f} & [{r['lo']:+.4f}, {r['hi']:+.4f}] & {pv(p)}"+r' \\'
t2.append(row('Primary: Bank, quality in automation head',p,p['p']))
t2.append(r'\midrule')
for r in summary['secondary_family_6']:
    lab=('Default' if r['dataset']=='default' else 'Bank')+', '+{'random':'random','uncertainty':'uncertainty logs','rules':'rule-prioritized logs'}[r['logging']]
    t2.append(row('IPW: '+lab,r,r['p_holm']))
t2.append(r'\bottomrule\end{tabular}')
commands={'TableOne':'\n'.join(t1),'TableTwo':'\n'.join(t2),
    'PrimaryRelative':f"{p['relative']:.2f}\\%",'PrimaryDiff':f"{p['diff']:.4f}",
    'PrimaryCI':f"[{p['lo']:.4f}, {p['hi']:.4f}]"}
commands['MainResultSentence']=(
    f"Quality in the automation head had the lowest mean among the matched variants on Default "
    f"({means.loc['default','quality_A']:.4f}) and Bank ({means.loc['bank','quality_A']:.4f}); "
    f"Chow cost risk gave {means.loc['default','chow']:.4f} and {means.loc['bank','chow']:.4f}, respectively.")
h=base[base.dataset=='human'].groupby('method').cost.mean()
commands['HumanResultSentence']=(
    f"on clean images under random logging, quality-in-automation-only cost was {h['quality_A']:.4f}, "
    f"probability-only {h['prob']:.4f}, and Chow {h['chow']:.4f}; these means do not establish a human-domain quality effect.")
rule=base[(base.method=='quality_both')&base.dataset.isin(['default','bank'])]
stale=rule[rule.condition=='stale'];shift=rule[rule.condition=='shift']
no=d[(d.dataset.isin(['default','bank']))&(d.method=='quality_both')&(d.arm=='no_rules')&
    (d.capacity==.2)&(d.logging=='random')&(d.weighting=='unweighted')]
commands['RuleResultSentence']=(
    f"Across Default and Bank, rules flagged {100*shift.defect_recall.mean():.1f}\\% of records with injected severe defects "
    f"but {100*stale.defect_recall.mean():.1f}\\% with injected stale values. "
    f"Under severe shift, the combined router held {100*shift.hold.mean():.1f}\\% of all records; "
    f"removing rules automated {100*no[no.condition=='shift'].violation.mean():.1f}\\% of all records despite mandatory flags.")
(root/'results/sc_tables.tex').write_text(''.join('\\newcommand{\\'+k+'}{%\n'+v+'}\n' for k,v in commands.items()))
(root/'results/revision-display.json').write_text(json.dumps({'table1':means.to_dict(),
    'table2':[summary['primary']]+summary['secondary_family_6'],
    'prose':{k:v for k,v in commands.items() if k not in ['TableOne','TableTwo']}},indent=2))
print('Generated both tables, numerical macros and display audit.')
