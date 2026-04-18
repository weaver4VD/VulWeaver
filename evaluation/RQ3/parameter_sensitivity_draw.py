import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter

def generate_data():
    f1 = np.array([0.726575342, 0.753636364, 0.75977492, 0.759548387, 0.761794872])
    vp_s = np.array([0.547, 0.583, 0.59, 0.587, 0.592])
    return vp_s, f1

def style_axes(ax, is_top=False, is_bottom=False):
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8, alpha=0.35)
    ax.grid(False, axis="x")
    ax.tick_params(axis="both", labelsize=11, width=1.2, length=4.0)
    
    if is_top:
        ax.spines["bottom"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.tick_params(labelbottom=False, bottom=False)
    if is_bottom:
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_linewidth(1.2)

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    pass

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.family": "Times New Roman",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    }
)

vp_s, f1 = generate_data()
num_points = len(f1)
rounds = np.arange(1, 2 * num_points, 2)
x = np.arange(num_points)

balance_x = 3
balance_idx = int(np.where(rounds == balance_x)[0][0]) if balance_x in rounds else 0
balance_pos = x[balance_idx]

color_f1 = "#E69F00"  
color_vps = "#56B4E9" 

fig, (ax_top, ax_bottom) = plt.subplots(
    2, 1, sharex=True, figsize=(5.5, 4.2), 
    gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.08}
)

style_axes(ax_top, is_top=True)
style_axes(ax_bottom, is_bottom=True)

for ax in (ax_top, ax_bottom):
    ax.axvspan(balance_pos - 0.18, balance_pos + 0.18, color="grey", alpha=0.12, lw=0)
    ax.axvline(balance_pos, color="0.35", linestyle=":", linewidth=1.2, alpha=0.9, zorder=1)

for ax in (ax_top, ax_bottom):
    ax.plot(x, f1, color=color_f1, linewidth=2.0, linestyle="-", marker="o", markersize=5.0, 
            label="F1-score" if ax==ax_bottom else "")

    ax.plot(x, vp_s, color=color_vps, linewidth=2.0, linestyle="-", marker="D", markersize=5.0, 
            label="VP-S" if ax==ax_bottom else "")
    

    ax.scatter(balance_pos, f1[balance_idx], s=70, marker="o", facecolors="white", 
               edgecolors=color_f1, linewidth=1.5, zorder=6)
    ax.scatter(balance_pos, vp_s[balance_idx], s=60, marker="D", facecolors="white", 
               edgecolors=color_vps, linewidth=1.5, zorder=6)


f1_lo, f1_hi = float(f1.min()), float(f1.max())
f1_rng = f1_hi - f1_lo
f1_pad = max(f1_rng * 0.15, 0.004)
ax_top.set_ylim(f1_lo - f1_pad, f1_hi + f1_pad)

vps_lo, vps_hi = float(vp_s.min()), float(vp_s.max())
vps_rng = vps_hi - vps_lo
vps_pad = max(vps_rng * 0.15, 0.004)
ax_bottom.set_ylim(vps_lo - vps_pad, vps_hi + vps_pad)

ax_top.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
ax_bottom.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
ax_top.yaxis.set_major_locator(plt.MaxNLocator(4))
ax_bottom.yaxis.set_major_locator(plt.MaxNLocator(4))

f1_span = ax_top.get_ylim()[1] - ax_top.get_ylim()[0]
vps_span = ax_bottom.get_ylim()[1] - ax_bottom.get_ylim()[0]

ax_top.text(
    balance_pos - 0.12, float(f1[balance_idx]) + 0.05 * f1_span,
    f"F1={float(f1[balance_idx]):.3f}",
    ha="right", va="bottom", fontsize=8, fontweight="bold", color=color_f1,
    bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="0.7", linewidth=1.1, alpha=0.95), zorder=7,
)
ax_bottom.text(
    balance_pos - 0.12, float(vp_s[balance_idx]) + 0.05 * vps_span,
    f"VP-S={float(vp_s[balance_idx]):.2f}",
    ha="right", va="bottom", fontsize=8, fontweight="bold", color=color_vps,
    bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="0.7", linewidth=1.1, alpha=0.95), zorder=7,
)

ax_bottom.set_xlabel("Query Rounds (N)", fontsize=10, fontweight="bold")

fig.text(0.01, 0.5, "Detection Performance", va='center', rotation='vertical', fontsize=10, fontweight="bold")

d = 0.015  
kwargs = dict(transform=ax_top.transAxes, color='k', linewidth=1.2, clip_on=False)

ax_top.plot((-d, +d), (-d, +d), **kwargs)

kwargs.update(transform=ax_bottom.transAxes)

ax_bottom.plot((-d, +d), (1 - d, 1 + d), **kwargs)

ax_bottom.set_xticks(x)
ax_bottom.set_xticklabels([str(r) for r in rounds])
ax_bottom.set_xlim(-0.40, (num_points - 1) + 0.40)

ax_bottom.legend(loc="lower right", fontsize=8, frameon=False, handlelength=None)

plt.tight_layout()
plt.subplots_adjust(left=0.15) 

pdf_path = "./parameter_sensitivity.pdf"
plt.savefig(pdf_path, bbox_inches="tight")
plt.show()