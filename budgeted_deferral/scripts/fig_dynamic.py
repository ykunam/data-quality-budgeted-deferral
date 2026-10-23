import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from dqd.style import setup, PAL, INK, INK2
setup()
lg = pd.read_csv("results/dynamic_log.csv.gz"); d = pd.read_csv("results/dynamic.csv.gz")
fig, axs = plt.subplots(1, 3, figsize=(7.3, 2.4))
ax = axs[0]
sub = lg[(lg.order == "cost") & (lg.reviewer == "quality")]
caps = [0.2, 0.4, 0.5, 0.7]
mu_s = d.mand_rate_shift.mean(); mu_m = d.mand_rate_mixed.mean()
for c, col in zip(caps, [PAL[7], PAL[1], PAL[0], PAL[2]]):
    tr = sub[sub.capacity == c].groupby("day").backlog_in.mean()
    ax.plot(tr.index + 1, tr.values, color=col, label=f"{int(c*100)}%")
    # fluid approximation
    L, fl = 0.0, []
    for t in range(40):
        fl.append(L); mu = mu_s if 10 <= t < 20 else mu_m
        L = max(0.0, L + 100 * (mu - c))
    ax.plot(np.arange(1, 41), fl, color=col, ls=":", lw=1.1)
ax.axvspan(11, 20.5, color=INK2, alpha=0.08, lw=0); ax.text(15.7, ax.get_ylim()[1] * 0.93, "severe\nshift", ha="center", va="top", fontsize=6.5, color=INK2)
ax.set_xlabel("Day"); ax.set_ylabel("Backlog at start of day (records)"); ax.set_title("(a) Backlog; dotted = fluid model", fontsize=8)
ax.legend(title="Capacity", fontsize=6.5, title_fontsize=6.5, loc="upper right")
L = {"fifo": ("FIFO", PAL[2]), "cost": ("Cost-exact", PAL[0]), "gain": ("Gain order (earlier)", PAL[6])}
g = d.groupby(["capacity", "order"])[["cohort_resolved7", "cohort_sla2"]].mean().reset_index()
for o, (lab, col) in L.items():
    s = g[g.order == o]
    axs[1].plot(100 * s.capacity, 100 * s.cohort_resolved7, marker="o", ms=3, color=col, label=lab)
    axs[2].plot(100 * s.capacity, 100 * s.cohort_sla2, marker="o", ms=3, color=col, label=lab)
axs[1].set_xlabel("Capacity (% of daily arrivals)"); axs[1].set_ylabel("Resolved ≤ 7 days (% of cohort)"); axs[1].set_title("(b) Seven-day resolution (cohort)", fontsize=8)
axs[2].set_xlabel("Capacity (% of daily arrivals)"); axs[2].set_ylabel("Resolved ≤ 2 days (% of cohort)"); axs[2].set_title("(c) Two-day resolution (cohort)", fontsize=8)
for ax in axs[1:]: ax.set_ylim(0, 102)
axs[1].legend(fontsize=6.5, loc="lower right")
fig.tight_layout(w_pad=1.2)
fig.savefig("figs/fig5_backlog.png"); fig.savefig("figs/fig5_backlog.pdf")
