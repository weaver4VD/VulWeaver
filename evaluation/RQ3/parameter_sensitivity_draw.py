import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FormatStrFormatter

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42


def generate_data():
    f1 = np.array(
        [
            0.726575342,
            0.763636364,
            0.76977492,
            0.769548387,
            0.771794872,
        ]
    )
    vp_s = np.array(
        [
            0.49,
            0.54,
            0.554,
            0.55,
            0.557,
        ]
    )
    return vp_s, f1


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.8, alpha=0.35)
    ax.grid(False, axis="x")
    ax.tick_params(axis="both", labelsize=11, width=1.0, length=3.5)


def zoom_ylim(ax, y, pad_ratio=0.12, min_pad=0.015):
    y = np.asarray(y, dtype=float)
    y_min = float(np.min(y))
    y_max = float(np.max(y))
    span = max(y_max - y_min, 1e-9)
    pad = max(span * pad_ratio, min_pad)
    lo = max(0.0, y_min - pad)
    hi = min(1.0, y_max + pad)
    ax.set_ylim(lo, hi)
    ax.yaxis.set_major_locator(plt.MaxNLocator(4))

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    pass

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times"]

vp_s, f1 = generate_data()
num_points = len(f1)

rounds = np.arange(1, 2 * num_points, 2)

x = np.arange(num_points)

balance_x = 3
balance_idx = int(np.where(rounds == balance_x)[0][0]) if balance_x in rounds else 0
balance_pos = x[balance_idx]

color_f1 = "#E69F00"
color_vps = "#56B4E9"

fig, (ax_f1, ax_vps) = plt.subplots(
    nrows=2,
    ncols=1,
    figsize=(4.2, 3.0),
    sharex=True,
    gridspec_kw={"height_ratios": [1.12, 1.0], "hspace": 0.16},
)
style_axes(ax_f1)
style_axes(ax_vps)

for _ax in (ax_f1, ax_vps):
    _ax.axvspan(balance_pos - 0.18, balance_pos + 0.18, color="grey", alpha=0.12, lw=0)

ax_f1.plot(x, f1, color=color_f1, linewidth=2.0, marker="o", markersize=4.6, label="F1 score")
ax_vps.plot(x, vp_s, color=color_vps, linewidth=2.0, marker="D", markersize=4.5, label="VP-S")

ax_f1.scatter(
    balance_pos,
    f1[balance_idx],
    s=52,
    marker="o",
    facecolors="white",
    edgecolors=color_f1,
    linewidth=1.3,
    zorder=6,
)
ax_vps.scatter(
    balance_pos,
    vp_s[balance_idx],
    s=52,
    marker="o",
    facecolors="white",
    edgecolors=color_vps,
    linewidth=1.3,
    zorder=6,
)

for _ax in (ax_f1, ax_vps):
    _ax.axvline(balance_pos, color="0.35", linestyle=":", linewidth=1.1, alpha=0.9, zorder=1)

ax_f1.set_ylabel("F1 score", fontsize=12.5)
ax_vps.set_ylabel("VP-S", fontsize=12.5)
ax_vps.set_xlabel("Voting Rounds", fontsize=12.5)

zoom_ylim(ax_f1, f1)
zoom_ylim(ax_vps, vp_s)
ax_vps.yaxis.set_major_formatter(FormatStrFormatter("%.2f"))

f1_span = ax_f1.get_ylim()[1] - ax_f1.get_ylim()[0]
vps_span = ax_vps.get_ylim()[1] - ax_vps.get_ylim()[0]
ax_f1.text(
    balance_pos,
    float(f1[balance_idx]) + 0.2 * f1_span,
    f"F1={float(f1[balance_idx]):.3f}",
    ha="center",
    va="bottom",
    fontsize=10.5,
    fontweight="bold",
    color=color_f1,
    bbox=dict(
        boxstyle="round,pad=0.22",
        facecolor="white",
        edgecolor="0.7",
        linewidth=1.1,
        alpha=0.95,
    ),
    zorder=7,
)
ax_vps.text(
    balance_pos,
    float(vp_s[balance_idx]) + 0.2 * vps_span,
    f"VP-S={float(vp_s[balance_idx]):.2f}",
    ha="center",
    va="bottom",
    fontsize=10.5,
    fontweight="bold",
    color=color_vps,
    bbox=dict(
        boxstyle="round,pad=0.22",
        facecolor="white",
        edgecolor="0.7",
        linewidth=1.1,
        alpha=0.95,
    ),
    zorder=7,
)

ax_vps.set_xticks(x, [str(r) for r in rounds])
ax_vps.set_xlim(-0.40, (num_points - 1) + 0.40)

ax_f1.legend(loc="lower right", fontsize=11.5, frameon=False)
ax_vps.legend(loc="lower right", fontsize=11.5, frameon=False)

plt.tight_layout()
pdf_path = "./parameter_sensitivity.pdf"
plt.savefig(pdf_path, bbox_inches="tight")
plt.show()
