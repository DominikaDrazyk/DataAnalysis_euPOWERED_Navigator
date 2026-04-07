# Matplotlib / seaborn figures for the energy dashboard and optional CLI preview.
# ``dashboard.py`` builds the UI and calls these functions.

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter
import pandas as pd
import seaborn as sns

# --- Paths & style ---------------------------------------------------------

_HERE = Path(__file__).resolve().parent
FONT_PATH = _HERE / "assets" / "fonts" / "Ubuntu-Regular.ttf"
STYLE_PATH = _HERE / "custom.mplstyle"
DATA_PATH = _HERE / "data"

# Sectoral REN lines for Figure 3 (total economy-wide REN Share is omitted)
REN_METRICS = [
    "REN Share Transport",
    "REN Share Heat-Cool",
    "REN Share Electricity",
]

# Figure 3 legend: dataframe column names -> display labels (hue header uses column name "Sector")
FIGURE3_SECTOR_LEGEND_LABELS: dict[str, str] = {
    "REN Share Transport": "Transport",
    "REN Share Heat-Cool": "Heat-Cool",
    "REN Share Electricity": "Electricity",
}

CONSUMPTION_COLUMNS = {
    "Consumption Industry": "Industry",
    "Consumption Transport": "Transport",
    "Consumption Households": "Households",
}

# Figure 1 stacked bars — sector fill colours (order follows ``CONSUMPTION_COLUMNS``)
FIGURE1_CONSUMPTION_COLORS: dict[str, str] = {
    "Industry": "#7c9356",
    "Transport": "#3d6a6d",
    "Households": "#a8c59d",
}

# Figures 2–4 — hue colours for Country (2, 4) and Sector lines (3); seaborn cycles if more categories.
# Same hues as the design swatches, bumped in saturation (~+18%) and value (~+5%) so they read less muted.
FIGURE234_SERIES_PALETTE: list[str] = [
    "#b98d4b",
    "#bd6147",
    "#498188",
    "#81586c",
    "#63364e",
    "#2c7007",
    "#32a375",
    "#bdbf27",
    "#7c835e",
    "#accfa2",
]

STANDARD_FIG_SIZE = (6.5, 4.5)

pd.options.display.precision = 3
plt.style.use(STYLE_PATH)

if FONT_PATH.exists():
    _fe = fm.FontEntry(fname=str(FONT_PATH), name="ProjectUbuntu")
    fm.fontManager.ttflist.insert(0, _fe)
    plt.rcParams["font.family"] = _fe.name
else:
    plt.rcParams["font.family"] = "sans-serif"


def _resolve_figsize(figsize: tuple[float, float] | None) -> tuple[float, float]:
    return figsize if figsize is not None else STANDARD_FIG_SIZE


def _empty_fig(message: str, figsize: tuple[float, float] | None = None) -> plt.Figure:
    size = _resolve_figsize(figsize)
    fig, ax = plt.subplots(figsize=size)
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    return fig


REFERENCE_YEAR = 2023


def _reference_year_ts(df: pd.DataFrame) -> pd.Timestamp:
    """Return the Timestamp for REFERENCE_YEAR if present, otherwise fall back to the latest year."""
    target = pd.Timestamp(year=REFERENCE_YEAR, month=1, day=1)
    if target in df["year"].values:
        return target
    return df["year"].max()


def _consumption_colorbar_ticks(tc_min: float, tc_max: float) -> list[float]:
    """KTOE colorbar stops for Figure 6: prefer 10k (0, 10k, 20k, …); use 5k when the span is too narrow."""
    if not math.isfinite(tc_min) or not math.isfinite(tc_max):
        return []
    lo, hi = (tc_min, tc_max) if tc_min <= tc_max else (tc_max, tc_min)
    span = hi - lo
    if span < 1e-9:
        return [max(0.0, lo), max(10000.0, hi)]

    def _range_ticks(step: float) -> list[float]:
        start = math.floor(lo / step) * step
        start = max(0.0, start)
        end = math.ceil(hi / step) * step
        if end <= start:
            end = start + step
        n = int(round((end - start) / step))
        return [start + i * step for i in range(n + 1)]

    ticks = _range_ticks(10000.0)
    if len(ticks) < 4:
        ticks = _range_ticks(5000.0)
    if len(ticks) > 12:
        ticks = _range_ticks(10000.0)
    return ticks


def _apply_legend_fontsizes(ax: plt.Axes, item_pt: float, title_pt: float) -> None:
    """Set legend entry and title font sizes (points)."""
    leg = ax.get_legend()
    if leg is None:
        return
    for text in leg.get_texts():
        text.set_fontsize(item_pt)
    t = leg.get_title()
    if t is not None:
        t.set_fontsize(title_pt)


# --- Figures ---------------------------------------------------------------

def figure_total_ren_share(
    df: pd.DataFrame,
    figsize: tuple[float, float] | None = None,
) -> plt.Figure:
    # Figure 2 — Temporal lineplot tracking the evolution of the Total Renewable Energy Share from 2015 to
    # 2024. It utilizes the REN Share variable [nrg_bal: REN] for a single Country selected and serves as the
    # primary indicator for national-level climate goal achievement.
    size = _resolve_figsize(figsize)
    if "REN Share" not in df.columns:
        return _empty_fig("No REN Share column", size)
    plot_df = df.dropna(subset=["year", "REN Share"])
    if plot_df.empty:
        return _empty_fig("No data", size)

    fig, ax = plt.subplots(figsize=size)
    sns.lineplot(
        data=plot_df,
        x="year",
        y="REN Share",
        hue="Country",
        palette=FIGURE234_SERIES_PALETTE,
        linewidth=2,
        ax=ax,
    )
    y_min = int(plot_df["year"].dt.year.min())
    y_max = int(plot_df["year"].dt.year.max())
    ax.set_xlabel("Year")
    ax.set_ylabel("Total Renewable Energy Share (%)")
    ax.set_title(f"National Progression of Total Renewable Energy Share ({y_min}-{y_max})")
    ax.legend(
        title="Country",
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0,
    )
    _apply_legend_fontsizes(ax, 9, 10)
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig


def figure_sectoral_ren_share(
    df: pd.DataFrame,
    figsize: tuple[float, float] | None = None,
) -> plt.Figure:
    # Figure 3 — Multi-line chart illustrating Renewable Energy Share penetration across sectoral balances.
    # Lines: REN Share Transport [nrg_bal: REN_TRA], REN Share Heat-Cool [nrg_bal: REN_HEAT_CL], and
    # REN Share Electricity [nrg_bal: REN_ELC] (economy-wide REN Share is not shown). Distinct line patterns
    # differentiate between multiple selected Countries.
    size = _resolve_figsize(figsize)
    value_vars = [m for m in REN_METRICS if m in df.columns]
    if not value_vars:
        return _empty_fig("No REN columns in data", size)

    id_vars = [c for c in ("year", "geo", "Country") if c in df.columns]
    long_df = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="metric",
        value_name="value",
    ).dropna(subset=["value", "year"])
    long_df["Sector"] = long_df["metric"].map(FIGURE3_SECTOR_LEGEND_LABELS)
    long_df = long_df.dropna(subset=["Sector"]).drop(columns=["metric"])
    if long_df.empty:
        return _empty_fig("No data", size)

    hue_order = [FIGURE3_SECTOR_LEGEND_LABELS[m] for m in value_vars]

    fig, ax = plt.subplots(figsize=size)
    sns.lineplot(
        data=long_df,
        x="year",
        y="value",
        hue="Sector",
        hue_order=hue_order,
        palette=FIGURE234_SERIES_PALETTE,
        style="Country",
        linewidth=2,
        ax=ax,
    )
    y_min = int(long_df["year"].dt.year.min())
    y_max = int(long_df["year"].dt.year.max())
    ax.set_title(f"Sectoral Dynamics of Renewable Energy Integration ({y_min}-{y_max})")
    ax.set_xlabel("Year")
    ax.set_ylabel("Sectoral Renewable Energy Share (%)")
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0,
    )
    _apply_legend_fontsizes(ax, 7, 8)
    ax.set_yticks(range(0, 101, 10))
    ax.set_yticklabels([str(i) for i in range(0, 101, 10)])
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig


def figure_consumption_scale_context(
    df: pd.DataFrame,
    figsize: tuple[float, float] | None = None,
) -> plt.Figure:
    # Figure 1 — Stacked barplot displaying Total Energy Consumption for the 2023 period. Categorizes
    # consumption into three primary segments using Consumption Industry [nrg_bal: FC_IND_E], Consumption
    # Transport [nrg_bal: FC_TRA_E], and Consumption Households [nrg_bal: FC_OTH_HH_E]. Visualizes selected
    # Countries to provide context on the scale of national energy needs.
    size = _resolve_figsize(figsize)
    present = {k: v for k, v in CONSUMPTION_COLUMNS.items() if k in df.columns}
    if not present:
        return _empty_fig("No consumption columns in data", size)
    if df["year"].notna().sum() == 0:
        return _empty_fig("No year data", size)

    latest_year = _reference_year_ts(df)
    df_latest = df[df["year"] == latest_year].copy()
    if df_latest.empty:
        return _empty_fig(f"No data for {int(latest_year.year)}", size)

    label_col = "Country" if "Country" in df_latest.columns else "geo"
    cols = list(present.keys()) + [label_col]
    plot_df = df_latest[cols].copy()
    plot_df = plot_df.rename(columns=present)
    sector_cols = list(present.values())
    plot_df = plot_df.set_index(label_col)[sector_cols].fillna(0)
    plot_df = (
        plot_df.assign(_total=plot_df.sum(axis=1))
        .sort_values("_total", ascending=False)
        .drop(columns="_total")
    )
    if plot_df.empty:
        return _empty_fig("No data", size)

    fig, ax = plt.subplots(figsize=size)
    sector_colors = [FIGURE1_CONSUMPTION_COLORS[s] for s in sector_cols]
    plot_df.plot(
        kind="bar",
        stacked=True,
        ax=ax,
        color=sector_colors,
        edgecolor="black",
        linewidth=1.25,
        width=0.8,
    )
    ax.set_title(
        f"National Energy Consumption Profiles by Economic Sector ({int(latest_year.year)})"
    )
    ax.set_ylabel("Energy Consumption (KTOE)")
    ax.set_xlabel("Country")
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax.legend(title="Sector", bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0)
    _apply_legend_fontsizes(ax, 9, 10)
    plt.tight_layout()
    return fig


def figure_share_vs_price_correlation(
    df: pd.DataFrame,
    price_col: str = "Price",
    figsize: tuple[float, float] | None = None,
    show_legend: bool = True,
) -> plt.Figure:
    # Figure 4 — Scatterplot correlating Renewable Share [nrg_bal: REN] with consumer energy costs. It
    # features a dynamic y-axis that switches between Price+tax [tax: I_TAX] and Price [tax: X_TAX] based on
    # user selection. Plot clusters data points by color per Country, representing annual observations from
    # 2015 to 2024.
    size = _resolve_figsize(figsize)
    if "REN Share" not in df.columns or price_col not in df.columns:
        return _empty_fig(f"Need REN Share and {price_col}", size)

    plot_df = df.dropna(subset=["REN Share", price_col]).copy()
    if plot_df.empty:
        return _empty_fig("No data", size)

    fig, ax = plt.subplots(figsize=size)
    sns.scatterplot(
        data=plot_df,
        x="REN Share",
        y=price_col,
        hue="Country",
        palette=FIGURE234_SERIES_PALETTE,
        ax=ax,
        alpha=0.85,
    )
    ax.set_xlabel("Total Renewable Energy Share (%)")
    ax.set_ylabel("Household Electricity Price (EUR/kWh)")
    ax.set_title("Historical Correlation: Renewable Penetration vs. Energy Pricing")
    if show_legend:
        ax.legend(
            title="Country",
            bbox_to_anchor=(1.01, 1),
            loc="upper left",
            borderaxespad=0,
        )
        _apply_legend_fontsizes(ax, 9, 10)
    else:
        ax.legend().remove()
    plt.tight_layout()
    return fig


def figure_investment_potential(
    df: pd.DataFrame,
    price_col: str = "Price",
    figsize: tuple[float, float] | None = None,
) -> plt.Figure:
    # Figure 6 — Multidimensional bubble chart identifying market opportunities for 2023. It plots REN Share
    # Electricity [nrg_bal: REN_ELC] against Price [tax: X_TAX]. Bubble size and color intensity represent
    # Total Energy Consumption, calculated as the sum of Consumption Industry [nrg_bal: FC_IND_E], Consumption
    # Transport [nrg_bal: FC_TRA_E], and Consumption Households [nrg_bal: FC_OTH_HH_E]. It highlights
    # countries in the upper-left quadrant as high-priority areas for renewable infrastructure investment.
    size = _resolve_figsize(figsize)
    required = ["REN Share Electricity", price_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return _empty_fig(f"Missing columns: {', '.join(missing)}", size)

    if df["year"].notna().sum() == 0:
        return _empty_fig("No year data", size)

    latest_year = _reference_year_ts(df)
    latest = df[df["year"] == latest_year].copy()
    if latest.empty:
        return _empty_fig(f"No data for {int(latest_year.year)}", size)

    cons_cols = [c for c in CONSUMPTION_COLUMNS if c in latest.columns]
    if not cons_cols:
        return _empty_fig("No consumption columns for bubble sizes", size)

    latest["total_cons"] = latest[cons_cols].sum(axis=1, numeric_only=True)

    merged_df = latest.dropna(
        subset=["REN Share Electricity", price_col, "total_cons"]
    ).copy()
    if merged_df.empty:
        return _empty_fig("No data", size)

    max_cons = float(merged_df["total_cons"].max())
    if max_cons <= 0:
        sizes = 200
    else:
        sizes = (merged_df["total_cons"] / max_cons) * 1200 + 80

    fig, ax = plt.subplots(figsize=size)
    _bubble_edge = "#454545"
    scatter = ax.scatter(
        merged_df["REN Share Electricity"],
        merged_df[price_col],
        s=sizes,
        c=merged_df["total_cons"],
        cmap="YlOrRd",
        alpha=0.55,
        edgecolors=_bubble_edge,
        linewidth=1.25,
    )

    x_mean = merged_df["REN Share Electricity"].mean()
    y_mean = merged_df[price_col].mean()
    ax.axvline(x_mean, color="grey", linestyle="--", alpha=0.5)
    ax.axhline(y_mean, color="grey", linestyle="--", alpha=0.5)

    label_col = "geo" if "geo" in merged_df.columns else ("Country" if "Country" in merged_df.columns else None)
    if label_col is not None:
        for _, row in merged_df.iterrows():
            ax.text(
                row["REN Share Electricity"],
                row[price_col],
                str(row[label_col]),
                fontsize=8,
                ha="center",
                va="center",
                fontweight="bold",
                color=_bubble_edge,
            )

    ax.set_title(f"Strategic Investment Potential Matrix ({int(latest_year.year)})")
    ax.set_xlabel("Renewable Share in Electricity Segment [%]")
    ax.set_ylabel("Household Electricity Price (EUR/kWh)")

    _cbar_scale = 0.75
    cbar = fig.colorbar(
        scatter,
        ax=ax,
        shrink=_cbar_scale,
        fraction=0.15 * _cbar_scale,
    )
    _base_tick = plt.rcParams["ytick.labelsize"]
    _base_lbl = plt.rcParams["axes.labelsize"]
    try:
        _tick_fs = float(_base_tick) * _cbar_scale
    except (TypeError, ValueError):
        _tick_fs = 7.5
    try:
        _lbl_fs = float(_base_lbl) * _cbar_scale
    except (TypeError, ValueError):
        _lbl_fs = 9.0
    cbar.ax.tick_params(labelsize=_tick_fs)
    cbar.set_label(
        "Total Energy Consumption (KTOE)",
        rotation=270,
        labelpad=12 * _cbar_scale + 5,
        fontsize=_lbl_fs,
    )

    _tc_min = float(merged_df["total_cons"].min())
    _tc_max = float(merged_df["total_cons"].max())
    _ticks = _consumption_colorbar_ticks(_tc_min, _tc_max)
    if len(_ticks) >= 2:
        cbar.set_ticks(_ticks)

    def _consumption_k_label(val: float, _pos: int) -> str:
        if abs(val) < 1e-9:
            return "0"
        return f"{val / 1000.0:.0f}k"

    cbar.ax.yaxis.set_major_formatter(FuncFormatter(_consumption_k_label))

    plt.tight_layout()
    return fig


def figure_price_stability_analysis(
    df: pd.DataFrame,
    price_col: str = "Price",
    figsize: tuple[float, float] | None = None,
) -> plt.Figure:
    # Figure 5 — Boxplot visualizing price distribution and fluctuations over a trailing 5-year window. It
    # categorizes Countries into "High" and "Low" groups based on the median of the latest REN Share value
    # [nrg_bal: REN]. Plot displays the statistical spread of the Price variable (excluding taxes)
    # [tax: X_TAX] for the user-selected Country cohort.
    size = _resolve_figsize(figsize)
    if price_col not in df.columns:
        return _empty_fig(f"Missing column: {price_col}", size)
    if "REN Share" not in df.columns and "REN Share Electricity" not in df.columns:
        return _empty_fig("Missing REN share column", size)
    if df["year"].notna().sum() == 0:
        return _empty_fig("No year data", size)

    latest_year = _reference_year_ts(df)
    share_col = "REN Share Electricity" if "REN Share Electricity" in df.columns else "REN Share"
    latest = df[df["year"] == latest_year].dropna(subset=[share_col]).copy()
    if latest.empty:
        return _empty_fig(f"No RES share data for {int(latest_year.year)}", size)
    if "geo" not in latest.columns:
        return _empty_fig("Missing geo column", size)

    median_res = float(latest[share_col].median())
    latest["group"] = latest[share_col].apply(
        lambda x: "High RES Share" if float(x) >= median_res else "Low RES Share"
    )
    groups = latest[["geo", "group"]].drop_duplicates()

    year_floor = pd.Timestamp(year=int(latest_year.year) - 5, month=1, day=1)
    hist = df[df["year"] >= year_floor].copy()
    hist = hist.dropna(subset=["geo", price_col])
    merged = hist.merge(groups, on="geo", how="inner")
    if merged.empty:
        return _empty_fig("No price history for selected countries", size)

    fig, ax = plt.subplots(figsize=size)
    group_order = ["Low RES Share", "High RES Share"]
    palette = {"Low RES Share": "#67823a", "High RES Share": "#703547"}
    sns.boxplot(
        data=merged,
        x="group",
        y=price_col,
        hue="group",
        order=group_order,
        hue_order=group_order,
        palette=palette,
        width=0.55,
        linewidth=1.25,
        ax=ax,
        legend=False,
        flierprops={
            "marker": "o",
            "markerfacecolor": "#8a8a8a",
            "markeredgecolor": "#6e6e6e",
            "markersize": 5.0,
            "markeredgewidth": 0.65,
            "linestyle": "none",
        },
    )
    sns.stripplot(
        data=merged,
        x="group",
        y=price_col,
        order=group_order,
        size=3.5,
        color="#141414",
        alpha=0.32,
        jitter=True,
        ax=ax,
    )
    ax.set_title("Household Electricity Price Volatility Assessment")
    ax.set_xlabel("Group (split by Median RES Share)")
    ax.set_ylabel("Household Electricity Price (EUR/kWh)")
    plt.tight_layout()
    return fig


# --- CLI -------------------------------------------------------------------

def load_datasets():
    print("---- Loading preprocessed data...")
    df = pd.read_csv(DATA_PATH / "preprocessed_data.csv")
    df["year"] = pd.to_datetime(df["year"], errors="coerce")
    print(f"✓ Loaded: {len(df):,} rows")
    return df


def main():
    print("=" * 60)
    print("Energy Consumption in the EU (2015‑2025) — figure preview")
    print("=" * 60)
    print()

    df = load_datasets()
    preview = [
        ("Total REN share", lambda: figure_total_ren_share(df)),
        ("Sectoral REN", lambda: figure_sectoral_ren_share(df)),
        ("Consumption by sector (latest year)", lambda: figure_consumption_scale_context(df)),
        ("REN vs price (excl. taxes)", lambda: figure_share_vs_price_correlation(df, "Price")),
        ("Investment Potential Matrix", lambda: figure_investment_potential(df)),
        ("Price Stability Analysis", lambda: figure_price_stability_analysis(df)),
    ]
    for title, make_fig in preview:
        plt.close("all")
        print(f"Showing: {title}")
        fig = make_fig()
        plt.show()
        plt.close(fig)


if __name__ == "__main__":
    main()
