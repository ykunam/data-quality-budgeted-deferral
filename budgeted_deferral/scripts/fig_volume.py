import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from dqd.style import setup, PAL, INK2
setup()
d = pd.read_csv("results/e6_volume.csv.gz")
M = [("confidence", "Confidence", PAL[3]), ("l2d_ce", "L2D-CE", PAL[1]), ("sh_quality", "Single-head (draft)", PAL[6]),
     ("2h_prob", "Two-head, prob. only", PAL[2]), ("2h_quality", "Two-head, quality-aware", PAL[0])]
fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.5), sharey=True)
for ax, ds, ttl in zip(axs, ["default", "hmeq"], ["(a) Default of credit-card clients", "(b) HMEQ (external, natural missingness)"]):
    s = d[d.dataset == ds].groupby(["n_gain", "seed", "method"]).cost.mean().unstack()
    for m, lab, c in M:
        rel = 100 * (s[m] - s["chow_risk"]) / s["chow_risk"]
        g = rel.groupby(level=0); mu, se = g.mean(), g.std() / np.sqrt(20)
        ax.plot(mu.index, mu.values, marker="o", ms=3, color=c, label=lab)
        ax.fill_between(mu.index, mu - 1.96 * se, mu + 1.96 * se, color=c, alpha=0.12, lw=0)
    ax.axhline(0, color=INK2, ls="--", lw=0.8); ax.set_xscale("log")
    xs = sorted(d[d.dataset == ds].n_gain.unique()); ax.set_xticks(xs); ax.set_xticklabels([f"{int(x):,}" for x in xs]); ax.minorticks_off()
    ax.set_xlabel("Gain-fitting records (log scale)"); ax.set_title(ttl, fontsize=8)
axs[0].set_ylabel("Cost vs Chow cost risk (%)")
fig.legend(*axs[0].get_legend_handles_labels(), loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.08), fontsize=6.6)
fig.tight_layout()
fig.savefig("figs/fig3_volume.png"); fig.savefig("figs/fig3_volume.pdf")
