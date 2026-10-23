import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from dqd.style import setup, PAL, INK, INK2
from dqd import core as C
setup()
df = pd.read_csv("results/static_logs.csv.gz")
ORIG = ["german", "australian", "default"]
REV = ["constant", "quality", "feature", "correlated", "adverse"]
REVL = {"constant": "Constant", "quality": "Quality-coupled", "feature": "Feature-dependent", "correlated": "AI-correlated", "adverse": "Adverse"}
# ---------------- Fig 2: cost relative to Chow across capacity, by reviewer
M = [("confidence", "Confidence", PAL[3]), ("l2d_ce", "L2D-CE", PAL[1]), ("l2d_ova", "L2D-OvA", PAL[4]),
     ("sh_quality", "Single-head (earlier draft)", PAL[6]), ("2h_quality", "Two-head quality-aware", PAL[0])]
d = df[df.dataset.isin(ORIG) & df.condition.isin(C.FAMILY_A + C.FAMILY_B)]
s = d.groupby(["reviewer", "capacity", "method", "seed"]).cost.mean().unstack("method")
fig, axs = plt.subplots(1, 5, figsize=(7.3, 2.25), sharey=True)
for ax, rv in zip(axs, REV):
    sub = s.loc[rv]
    for m, lab, c in M:
        rel = 100 * (sub[m] - sub["chow_risk"]) / sub["chow_risk"]
        g = rel.groupby("capacity"); mu = g.mean(); se = g.std() / np.sqrt(20)
        x = mu.index * 100
        ax.plot(x, mu.values, color=c, marker="o", ms=3, label=lab, lw=1.4)
        ax.fill_between(x, mu - 1.96 * se, mu + 1.96 * se, color=c, alpha=0.12, lw=0)
    ax.axhline(0, color=INK2, lw=0.8, ls="--")
    ax.set_title(REVL[rv], fontsize=8, color=INK); ax.set_xticks([5, 10, 20, 30]); ax.set_xlabel("Capacity (%)")
axs[0].set_ylabel("Cost vs Chow cost risk (%)")
fig.legend(*axs[0].get_legend_handles_labels(), loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.1), fontsize=7)
fig.savefig("figs/fig2_capacity.png"); fig.savefig("figs/fig2_capacity.pdf")
# ---------------- Fig 3: quality value heatmap
qv = pd.read_csv("results/tables/quality_value.csv")
q = qv[qv.capacity == 0.2].pivot_table(index="condition", columns="reviewer", values="rel")
W = qv[qv.capacity == 0.2].pivot_table(index="condition", columns="reviewer", values="wins")
P = qv[qv.capacity == 0.2].pivot_table(index="condition", columns="reviewer", values="p")
order = ["clean", "missing", "outliers", "mixed", "shift", "informative", "stale", "inconsistent", "realistic"]
names = {"clean": "clean", "missing": "A: missing", "outliers": "A: outliers", "mixed": "A: mixed", "shift": "A: severe shift",
         "informative": "B: informative missing", "stale": "B: stale records", "inconsistent": "B: inconsistent codes", "realistic": "B: realistic mix"}
q, W, P = q.loc[order, REV], W.loc[order, REV], P.loc[order, REV]
cmap = LinearSegmentedColormap.from_list("div", ["#e34948", "#f3f2ee", "#2a78d6"])
fig, ax = plt.subplots(figsize=(5.2, 3.3))
lim = 3.6
im = ax.imshow(q.values, cmap=cmap, norm=TwoSlopeNorm(0, -lim, lim), aspect="auto")
for i in range(q.shape[0]):
    for j in range(q.shape[1]):
        star = "*" if P.values[i, j] < 0.05 else ""
        ax.text(j, i, f"{q.values[i, j]:+.1f}{star}\n{int(W.values[i, j])}/20", ha="center", va="center", fontsize=6.4, color=INK)
ax.set_xticks(range(5)); ax.set_xticklabels([REVL[r] for r in REV], rotation=20, ha="right", fontsize=7)
ax.set_yticks(range(len(order))); ax.set_yticklabels([names[o] for o in order], fontsize=7)
ax.grid(False); ax.axhline(4.5, color="white", lw=2); ax.axhline(0.5, color="white", lw=2)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label("Cost reduction from quality inputs (%)", fontsize=7); cb.ax.tick_params(labelsize=6.5)
fig.savefig("figs/fig4_quality_value.png"); fig.savefig("figs/fig4_quality_value.pdf")
print("ok")
