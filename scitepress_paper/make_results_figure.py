#!/usr/bin/env python3
"""Build the paper-ready summary figure for the 2x2 factorial experiment."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_RESULTS = (
    PROJECT_ROOT
    / "results"
    / "2026-09-01"
    / "growth_factorial_18-53-01_raw.csv"
)
OUTPUT_DIR = Path(__file__).resolve().parent / "figures"
OUTPUT_STEM = OUTPUT_DIR / "growth_factorial_results"


ORDER = [
    ("coast_redwood", 1190),
    ("gray_wolf", 1054),
    ("us_cities", 219),
    ("star_8tips", 1000),
    ("star_8tips", 5000),
    ("star_8tips", 10000),
    ("star_8tips", 50000),
    ("unit_disk", 1000),
    ("unit_disk", 5000),
    ("unit_disk", 10000),
    ("unit_disk", 50000),
]


LABELS = {
    ("coast_redwood", 1190): "Coast redwood (1,190)",
    ("gray_wolf", 1054): "Gray wolf (1,054)",
    ("us_cities", 219): "U.S. cities (219)",
    ("star_8tips", 1000): "Eight-tip star (1k)",
    ("star_8tips", 5000): "Eight-tip star (5k)",
    ("star_8tips", 10000): "Eight-tip star (10k)",
    ("star_8tips", 50000): "Eight-tip star (50k)",
    ("unit_disk", 1000): "Unit disk (1k)",
    ("unit_disk", 5000): "Unit disk (5k)",
    ("unit_disk", 10000): "Unit disk (10k)",
    ("unit_disk", 50000): "Unit disk (50k)",
}


COLORS = {
    "bucketing": "#0072B2",
    "geometric": "#D55E00",
    "combined": "#009E73",
    "attempts": "#6C4C9A",
    "area": "#A33D3D",
    "grid": "#D7D7D7",
    "text_muted": "#555555",
}


def median_iqr(series: pd.Series) -> tuple[float, float, float]:
    return (
        float(series.median()),
        float(series.quantile(0.25)),
        float(series.quantile(0.75)),
    )


def load_paired_metrics() -> pd.DataFrame:
    raw = pd.read_csv(RAW_RESULTS)
    paired = raw.pivot(
        index=["dataset", "n", "trial", "seed"],
        columns="variant",
        values=["runtime_ms", "attempts", "area_ratio"],
    )

    metrics = pd.DataFrame(index=paired.index)
    baseline = paired[("runtime_ms", "linear_naive")]
    metrics["bucketing_speedup"] = baseline / paired[("runtime_ms", "linear_bucketed")]
    metrics["geometric_speedup"] = baseline / paired[("runtime_ms", "geometric_naive")]
    metrics["combined_speedup"] = baseline / paired[("runtime_ms", "geometric_bucketed")]
    metrics["attempt_reduction"] = (
        paired[("attempts", "linear_naive")]
        / paired[("attempts", "geometric_naive")]
    )
    metrics["area_ratio_change"] = (
        paired[("area_ratio", "geometric_naive")]
        - paired[("area_ratio", "linear_naive")]
    )
    return metrics.reset_index()


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for dataset, n in ORDER:
        group = metrics[(metrics["dataset"] == dataset) & (metrics["n"] == n)]
        row: dict[str, float | int | str] = {
            "dataset": dataset,
            "n": n,
            "label": LABELS[(dataset, n)],
        }
        for metric in [
            "bucketing_speedup",
            "geometric_speedup",
            "combined_speedup",
            "attempt_reduction",
            "area_ratio_change",
        ]:
            median, q1, q3 = median_iqr(group[metric])
            row[f"{metric}_median"] = median
            row[f"{metric}_q1"] = q1
            row[f"{metric}_q3"] = q3
        rows.append(row)
    return pd.DataFrame(rows)


def draw_interval(ax, y, median, q1, q3, color, marker, label=None, zorder=3):
    ax.hlines(y, q1, q3, color=color, linewidth=1.7, zorder=zorder - 1)
    ax.plot(
        median,
        y,
        marker=marker,
        markersize=5.4,
        markerfacecolor=color,
        markeredgecolor="white",
        markeredgewidth=0.55,
        linestyle="none",
        color=color,
        label=label,
        zorder=zorder,
    )


def build_figure(summary: pd.DataFrame) -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times", "Times New Roman", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.titlesize": 9.0,
            "axes.labelsize": 8.2,
            "xtick.labelsize": 7.4,
            "ytick.labelsize": 7.7,
            "legend.fontsize": 7.4,
            "pdf.use14corefonts": True,
        }
    )

    fig = plt.figure(figsize=(7.15, 5.15))
    grid = fig.add_gridspec(
        1,
        3,
        width_ratios=[3.85, 1.35, 1.65],
        left=0.235,
        right=0.985,
        bottom=0.16,
        top=0.82,
        wspace=0.22,
    )
    ax_speed = fig.add_subplot(grid[0, 0])
    ax_attempts = fig.add_subplot(grid[0, 1], sharey=ax_speed)
    ax_area = fig.add_subplot(grid[0, 2], sharey=ax_speed)

    y_positions = list(range(len(summary)))
    offsets = {"bucketing": -0.20, "geometric": 0.0, "combined": 0.20}
    speed_specs = [
        ("bucketing", "bucketing_speedup", "Bucketing only", "o"),
        ("geometric", "geometric_speedup", "Geometric only", "s"),
        ("combined", "combined_speedup", "Both", "D"),
    ]

    for strategy, metric, legend_label, marker in speed_specs:
        for index, row in summary.iterrows():
            draw_interval(
                ax_speed,
                index + offsets[strategy],
                row[f"{metric}_median"],
                row[f"{metric}_q1"],
                row[f"{metric}_q3"],
                COLORS[strategy],
                marker,
                label=legend_label if index == 0 else None,
            )

    for index, row in summary.iterrows():
        draw_interval(
            ax_attempts,
            index,
            row["attempt_reduction_median"],
            row["attempt_reduction_q1"],
            row["attempt_reduction_q3"],
            COLORS["attempts"],
            "o",
        )
        draw_interval(
            ax_area,
            index,
            row["area_ratio_change_median"],
            row["area_ratio_change_q1"],
            row["area_ratio_change_q3"],
            COLORS["area"],
            "^",
        )

    labels = summary["label"].tolist()
    ax_speed.set_yticks(y_positions, labels)
    ax_speed.invert_yaxis()
    ax_speed.tick_params(axis="y", length=0, pad=5)
    ax_attempts.tick_params(axis="y", labelleft=False, length=0)
    ax_area.tick_params(axis="y", labelleft=False, length=0)

    for ax in (ax_speed, ax_attempts, ax_area):
        ax.set_ylim(len(summary) - 0.45, -0.55)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        for boundary in (2.5, 6.5):
            ax.axhline(boundary, color="#B8B8B8", linewidth=0.75, zorder=0)

    log_formatter = FuncFormatter(lambda value, _: f"{value:g}")
    ax_speed.set_xscale("log")
    ax_speed.set_xlim(0.9, 210)
    ax_speed.xaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20, 50, 100, 200]))
    ax_speed.xaxis.set_major_formatter(log_formatter)
    ax_speed.axvline(1, color="#777777", linestyle="--", linewidth=0.85, zorder=1)
    ax_speed.set_xlabel("Paired speedup (×, log scale)")
    ax_speed.set_title("(a) Runtime improvement", loc="left", fontweight="bold", pad=8)

    ax_attempts.set_xscale("log")
    ax_attempts.set_xlim(0.9, 21)
    ax_attempts.xaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20]))
    ax_attempts.xaxis.set_major_formatter(log_formatter)
    ax_attempts.axvline(1, color="#777777", linestyle="--", linewidth=0.85, zorder=1)
    ax_attempts.set_xlabel("Attempt reduction\n(×, log scale)")
    ax_attempts.set_title("(b) Attempts", loc="left", fontweight="bold", pad=8)

    ax_area.set_xlim(-0.01, 0.222)
    ax_area.xaxis.set_major_locator(FixedLocator([0.0, 0.1, 0.2]))
    ax_area.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.1f}"))
    ax_area.axvline(0, color="#777777", linestyle="--", linewidth=0.85, zorder=1)
    ax_area.set_xlabel(r"Area-ratio change, $\Delta\rho$")
    ax_area.set_title("(c) Shape tradeoff", loc="left", fontweight="bold", pad=8)

    handles, legend_labels = ax_speed.get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper left",
        bbox_to_anchor=(0.235, 0.935),
        ncol=3,
        frameon=False,
        handletextpad=0.35,
        columnspacing=1.4,
        borderaxespad=0,
    )

    # Label the three headline outliers without crowding the rest of the figure.
    redwood = summary.iloc[0]
    wolf = summary.iloc[1]
    ax_speed.annotate(
        f"{redwood['combined_speedup_median']:.0f}×",
        (redwood["combined_speedup_median"], offsets["combined"]),
        xytext=(-4, 7),
        textcoords="offset points",
        ha="right",
        color=COLORS["combined"],
        fontsize=7.2,
        fontweight="bold",
    )
    ax_attempts.annotate(
        f"{redwood['attempt_reduction_median']:.1f}×",
        (redwood["attempt_reduction_median"], 0),
        xytext=(-2, 6),
        textcoords="offset points",
        ha="right",
        color=COLORS["attempts"],
        fontsize=7.0,
        fontweight="bold",
    )
    ax_area.annotate(
        f"+{wolf['area_ratio_change_median']:.3f}",
        (wolf["area_ratio_change_median"], 1),
        xytext=(-2, 6),
        textcoords="offset points",
        ha="right",
        color=COLORS["area"],
        fontsize=7.0,
        fontweight="bold",
    )

    fig.text(0.025, 0.710, "Real", rotation=90, va="center", ha="center", color=COLORS["text_muted"], fontsize=7.4)
    fig.text(0.025, 0.515, "Synthetic star", rotation=90, va="center", ha="center", color=COLORS["text_muted"], fontsize=7.4)
    fig.text(0.025, 0.272, "Synthetic disk", rotation=90, va="center", ha="center", color=COLORS["text_muted"], fontsize=7.4)

    fig.text(
        0.235,
        0.055,
        "Dots show medians; bars show interquartile ranges over 10 paired trials. "
        "All runs succeeded; bucketing preserved the ordered hull.",
        ha="left",
        va="bottom",
        fontsize=7.2,
        color=COLORS["text_muted"],
    )
    return fig


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = summarize(load_paired_metrics())
    figure = build_figure(summary)
    figure.savefig(f"{OUTPUT_STEM}.pdf", bbox_inches="tight")
    figure.savefig(f"{OUTPUT_STEM}.png", dpi=350, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote {OUTPUT_STEM}.pdf")
    print(f"Wrote {OUTPUT_STEM}.png")


if __name__ == "__main__":
    main()
