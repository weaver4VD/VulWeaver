import json
import os

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np

# ======================== 可配置区域 ========================
JSON_PATH = os.path.join(os.path.dirname(__file__), "token_tax.json")
PDF_OUTPUT = os.path.join(os.path.dirname(__file__), "token_tax.pdf")
# 坐标轴脊线 / 刻度线粗细（与 parameter_sensitivity 断轴图脚本一致：spine 与 tick 均为 1.2）
AXES_LINEWIDTH = 1.2
TICK_LINEWIDTH = 1.2
TICK_LENGTH = 4.0
# ============================================================

plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except Exception:
    pass

# seaborn 会在 style.use 里改写字体；必须在之后重新指定，整图才统一为 Times New Roman
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times"]
plt.rcParams["axes.unicode_minus"] = False


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(AXES_LINEWIDTH)
    ax.spines["bottom"].set_linewidth(AXES_LINEWIDTH)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.4, color="gray")
    ax.grid(False, axis="x")
    ax.tick_params(
        axis="both",
        labelsize=11,
        width=TICK_LINEWIDTH,
        length=TICK_LENGTH,
    )


def load_and_draw(json_path: str, pdf_output: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bin_labels = list(data.keys())
    num_points = len(bin_labels)
    x = np.arange(num_points)

    f1 = np.array([data[k]["metrics"]["F1"] for k in bin_labels])
    vps = np.array([data[k]["metrics"]["VP-S"] for k in bin_labels])
    counts = np.array([data[k]["metrics"]["n"] for k in bin_labels])
    pairs = np.array([data[k]["metrics"]["pairs"] for k in bin_labels])

    print("=" * 65)
    for i, lbl in enumerate(bin_labels):
        print(f"  {lbl:>20s}  |  n={counts[i]:3d}  pairs={pairs[i]:3d}  "
              f"F1={f1[i]:.3f}  VP-S={vps[i]:+.3f}")
    print("=" * 65)

    color_f1 = "#E69F00"
    color_vps = "#56B4E9"
    bar_color = "#E2E8F0"
    bar_edge = "#CBD5E1"

    fig, ax1 = plt.subplots(figsize=(6.0, 4.2))
    ax2 = ax1.twinx()

    style_axes(ax1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_linewidth(AXES_LINEWIDTH)
    ax2.spines["bottom"].set_linewidth(AXES_LINEWIDTH)
    ax2.grid(False)
    ax2.tick_params(
        axis="y", labelsize=11, width=TICK_LINEWIDTH, length=TICK_LENGTH
    )

    bars = ax2.bar(x, counts, color=bar_color, edgecolor=bar_edge,
                   linewidth=1.0, width=0.4, alpha=0.8, label="Count")

    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height + max(counts) * 0.03,
            str(int(height)),
            ha="center", va="bottom", fontsize=10.5,
            family="Times New Roman",
            color="#555555", fontweight="bold",
            transform=ax2.transData, zorder=10,
            path_effects=[path_effects.withStroke(linewidth=2.5, foreground="white")],
        )

    ax1.plot(x, f1, color=color_f1, linewidth=2.5,
             marker="o", markersize=7.5, markeredgecolor="white",
             markeredgewidth=1.2, label="F1")
    ax1.plot(x, vps, color=color_vps, linewidth=2.5,
             marker="s", markersize=7.0, markeredgecolor="white",
             markeredgewidth=1.2, label="VP-S")

    ax1.set_zorder(ax2.get_zorder() + 1)
    ax1.patch.set_visible(False)

    ax1.set_ylabel("Detection Performance", fontsize=12, family="Times New Roman",fontweight="bold")
    ax2.set_ylabel("Number of Samples (#)", fontsize=12, family="Times New Roman",fontweight="bold")
    ax1.set_xlabel("Context Length", fontsize=12, family="Times New Roman",fontweight="bold")

    ax1.set_ylim(0.0, 1.05)
    ax1.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax2.set_ylim(0, max(counts) * 3.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(
        bin_labels, rotation=15, ha="center", family="Times New Roman"
    )
    ax1.set_xlim(-0.45, (num_points - 1) + 0.45)

    for _ax in (ax1, ax2):
        for _lbl in _ax.get_xticklabels() + _ax.get_yticklabels():
            _lbl.set_fontfamily("Times New Roman")

    lines, labels_ = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines + lines2,
        labels_ + labels2,
        loc="upper left",
        fontsize=10.0,
        prop={"family": "Times New Roman"},
        frameon=True,
        framealpha=0.9,
        edgecolor="none",
        ncol=1,
    )

    plt.tight_layout()
    plt.savefig(pdf_output, bbox_inches="tight")
    print(f"[✓] 已保存至 {pdf_output}")
    plt.show()


if __name__ == "__main__":
    load_and_draw(JSON_PATH, PDF_OUTPUT)
