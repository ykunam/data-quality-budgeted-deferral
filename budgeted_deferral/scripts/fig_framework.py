import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from dqd.style import setup, PAL, INK, INK2
setup()
fig, ax = plt.subplots(figsize=(7.2, 3.3)); ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")
def box(x, y, w, h, title, body, c):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=c + "1f", ec=c, lw=1.2))
    ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=7.6, weight="bold", color=INK)
    ax.text(x + w / 2, y + h - 6.3, body, ha="center", va="top", fontsize=6.3, color=INK2, linespacing=1.6)
def arr(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, color=INK2, lw=0.9))
box(1, 26, 17, 18, "Incoming batch", "records $x_i$\n(may be degraded:\nmissing, out-of-range,\nstale, mis-coded)", PAL[0])
box(23, 33, 20, 11, "Base predictor", "calibrated $p_i$\ncost decision $\\hat y_i$", PAL[0])
box(23, 17, 20, 12, "Quality monitor", "$u_i$ missing fraction\n$v_i$ out-of-range fraction", PAL[2])
box(48, 33, 22, 11, "Two-head estimator", "automation loss $\\hat\\ell^A_i$ (labels)\nreview loss $\\hat\\ell^H_i$ (logs)", PAL[6])
box(48, 17, 22, 12, "Knowledge base", "R1: $u_i\\geq\\tau_u\\Rightarrow m_i{=}1$\nR2: $v_i\\geq\\tau_v\\Rightarrow m_i{=}1$", PAL[3])
box(75, 22, 24, 22, "Exact allocator", "capacity $B$, service-first\n$|M|\\leq B$: all mandatory +\ntop positive $\\hat g_i$\n$|M|>B$: $B$ lowest $\\hat\\ell^H_i$,\nhold the rest", PAL[1])
box(1, 1, 30, 10.5, "Automate", "optional records,\n$\\hat g_i\\leq 0$ or no capacity", PAL[5])
box(35, 1, 30, 10.5, "Human review", "mandatory first, then\nhighest positive gain", PAL[0])
box(69, 1, 30, 10.5, "Hold / backlog", "unresolved mandatory cases;\nage, SLA, staffing gap", PAL[7])
arr(18, 38, 23, 38); arr(18, 30, 23, 24); arr(43, 38.5, 48, 38.5); arr(43, 24, 48, 36); arr(43, 22, 48, 22)
arr(70, 38.5, 75, 36); arr(70, 22, 75, 28)
ax.plot([87, 87], [21.6, 15.5], color=INK2, lw=0.9); ax.plot([16, 87], [15.5, 15.5], color=INK2, lw=0.9)
for xx in (16, 50, 84): arr(xx, 15.5, xx, 12.4)
ax.text(87, 46, "label-free audit record per case: $(p_i, u_i, v_i, m_i, \\hat\\ell^A_i, \\hat\\ell^H_i, a_i)$", ha="right", va="bottom", fontsize=6.6, color=INK2, style="italic")
fig.savefig("figs/fig1_framework.png"); fig.savefig("figs/fig1_framework.pdf")
