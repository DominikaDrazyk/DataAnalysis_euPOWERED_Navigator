#!/usr/bin/env python
# Streamlit dashboard: layout, data load, figure description popovers, ``st.pyplot`` calls.
# Plot titles and axis labels live in ``figures.py``.
# All brand / widget CSS lives in ``brand.css``.

from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from figures import (
    STANDARD_FIG_SIZE,
    figure_consumption_scale_context,
    figure_investment_potential,
    figure_price_stability_analysis,
    figure_sectoral_ren_share,
    figure_share_vs_price_correlation,
    figure_total_ren_share,
)

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "data"
PREPROCESSED_CSV = "preprocessed_data.csv"
_CSS_PATH = _HERE / "brand.css"

FIGURE_META: list[str] = [
    (
        "Stacked barplot displaying Total Energy Consumption for the 2023 period. "
        "Categorizes consumption into three primary segments using Consumption Industry [nrg_bal: FC_IND_E], "
        "Consumption Transport [nrg_bal: FC_TRA_E], and Consumption Households [nrg_bal: FC_OTH_HH_E]. "
        "Visualizes selected Countries to provide context on the scale of national energy needs."
    ),
    (
        "Temporal lineplot tracking the evolution of the Total Renewable Energy Share from 2015 to 2024. "
        "It utilizes the REN Share variable [nrg_bal: REN] for a single Country selected "
        "and serves as the primary indicator for national-level climate goal achievement."
    ),
    (
        "Multi-line chart illustrating Renewable Energy Share penetration across sectoral energy balances. "
        "It maps line colors to REN Share Transport [nrg_bal: REN_TRA], "
        "REN Share Heat-Cool [nrg_bal: REN_HEAT_CL], and REN Share Electricity [nrg_bal: REN_ELC]. "
        "Distinct line patterns differentiate between multiple selected Countries. "
        "Plot allows for a granular comparison of transformation speeds across different sectors."
    ),
    (
        "Scatterplot correlating Renewable Share [nrg_bal: REN] with consumer energy costs. "
        "It features a dynamic y-axis that switches between Price+tax [tax: I_TAX] and Price [tax: X_TAX] "
        "based on user selection. Plot clusters data points by color per Country, representing annual "
        "observations from 2015 to 2024."
    ),
    (
        "Boxplot visualizing price distribution and fluctuations over a trailing 5-year window. "
        'It categorizes Countries into "High" and "Low" groups based on the median of the latest '
        "REN Share value [nrg_bal: REN]. Plot displays the statistical spread of the Price variable "
        "(excluding taxes) [tax: X_TAX] for the user-selected Country cohort."
    ),
    (
        "Multidimensional bubble chart identifying market opportunities for 2023. "
        "It plots REN Share Electricity [nrg_bal: REN_ELC] against Price [tax: X_TAX]. "
        "Bubble size and color intensity represent Total Energy Consumption, calculated as the sum of "
        "Consumption Industry [nrg_bal: FC_IND_E], Consumption Transport [nrg_bal: FC_TRA_E], and "
        "Consumption Households [nrg_bal: FC_OTH_HH_E]. It highlights countries in the upper-left quadrant "
        "as high-priority areas for renewable infrastructure investment."
    ),
]

FIGURE_QUESTIONS: list[str] = [
    "How much energy do our factories and families actually burn through every day?",
    "Are we actually getting anywhere with energy independence?",
    "The grid is getting cleaner, but why are cars and home heating still stuck in the past?",
    "Can you actually promise that going green won't inflate people's monthly bills?",
    "Will going all-in on renewables actually shield us before the next global market crisis?",
    "Where do we actually have the most room to move the needle?",
]

_FIGURE_HEADING_PT = 26
_CHOOSER_LABEL_PT = 19


# ── CSS injection ───────────────────────────────────────────────────────────

def _inject_brand_styles() -> None:
    """Load all brand + widget CSS from the external stylesheet."""
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ── Inline HTML helpers ─────────────────────────────────────────────────────

def _figure_question_heading(text: str) -> None:
    safe = html.escape(text)
    st.markdown(
        f'<p style="font-size:{_FIGURE_HEADING_PT}pt;font-weight:bold;line-height:1.25;'
        f'margin:0;">{safe}</p><br>',
        unsafe_allow_html=True,
    )


def _chooser_label(text: str, extra_style: str = "") -> None:
    safe = html.escape(text)
    st.markdown(
        f'<p style="font-size:{_CHOOSER_LABEL_PT}pt;font-weight:normal;'
        f'margin-bottom:0.35rem;{extra_style}">{safe}</p>',
        unsafe_allow_html=True,
    )


def _countries_chooser_label() -> None:
    _chooser_label("Choose your countries of interest:")


def _metric_chooser_label(*, tight_below_country_panel: bool = False) -> None:
    """Place after country multiselect when True (small gap before metric label)."""
    extra = "margin-top:0.35rem;" if tight_below_country_panel else ""
    _chooser_label("Choose your metric:", extra_style=extra)


def _after_figure_break() -> None:
    """Spacer + horizontal rule between figure blocks (centered, 2/3 width, unpressed fill colour)."""
    st.markdown(
        '<div class="dash-figure-rule-wrap">'
        '<hr class="dash-figure-rule" aria-hidden="true" />'
        "</div>",
        unsafe_allow_html=True,
    )


GITHUB_PROFILE_URL = "https://github.com/DominikaDrazyk"
CURSOR_URL = "https://cursor.com"
CURSOR_AFFILIATION_URL = "https://anysphere.inc/"


def _credit_above_divider() -> None:
    """Right-aligned attribution snug above the page divider, aligned to the content columns."""
    _cred_left, _cred_body, _cred_pad = st.columns([1.5, 6, 1.5])
    with _cred_body:
        st.markdown(
            f'<div style="text-align:right;font-size:11px;line-height:1.25;margin:0;padding:0;margin-bottom:-0.2em;">'
            f"Imagined by "
            f'<a href="{html.escape(GITHUB_PROFILE_URL)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape('Dominika Drazyk')}</a><br>"
            f'<span style="white-space:nowrap;">Coded with '
            f'<a href="{html.escape(CURSOR_URL)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape('Cursor')}</a> "
            f'<a href="{html.escape(CURSOR_AFFILIATION_URL)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape('Anysphere')}</a></span></div>",
            unsafe_allow_html=True,
        )


def _page_title_and_subtitle(title: str, subtitle: str) -> None:
    """Centered header; each line +3pt vs typical Streamlit title / h3.

    The substring ``euPOWERED`` in *title* is rendered in the brand accent colour.
    """
    accent = "var(--brand-accent)"
    title_html = html.escape(title).replace(
        html.escape("euPOWERED"),
        f'<span style="color:{accent};">euPOWERED</span>',
    )
    st.markdown(
        f'<div style="text-align:center;">'
        f'<p style="font-size:calc(2.75rem + 3pt);font-weight:700;margin:0 0 0.4rem 0;'
        f'line-height:1.2;">{title_html}</p>'
        f'<p style="font-size:calc(1.35rem + 3pt);font-weight:600;margin:0;line-height:1.35;">'
        f"{html.escape(subtitle)}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _figure_description_popover_html(description: str) -> str:
    """Escaped HTML for popover body; bracket codes rendered as ``<code>``."""
    parts = re.split(r"(\[[^\]]+\])", description)
    chunks: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("[") and part.endswith("]"):
            inner = html.escape(part[1:-1])
            chunks.append(f"<code>[{inner}]</code>")
        else:
            chunks.append(html.escape(part))
    return "".join(chunks)


def _figure_help_button(description: str, *, key: str) -> None:
    """"Description" opens a popover with styled figure copy."""
    with st.popover(
        "Description",
        width="content",
        key=key,
        help="Open figure description",
    ):
        body = _figure_description_popover_html(description)
        st.markdown(
            f'<div class="figure-desc-popover-copy">{body}</div>',
            unsafe_allow_html=True,
        )


# ── Data loading ────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    path = DATA_PATH / PREPROCESSED_CSV
    df = pd.read_csv(path)
    df["year"] = pd.to_datetime(df["year"], errors="coerce")
    return df



# ── Page renderers ──────────────────────────────────────────────────────────

_DATA_MODEL_SECTIONS = ["Sources", "Methodology", "Key Variables", "Analysis Limitations"]

_DATA_MODEL_CONTENT: dict[str, str] = {}

_accent = "var(--brand-accent)"
_unp = "var(--brand-unpressed)"

_METADATA_CSV = "scraper_metadata.csv"

def _build_sources_content() -> str:
    """Build Sources HTML, injecting 'Last updated' dates from scraper_metadata.csv."""
    meta_path = DATA_PATH / _METADATA_CSV
    updated: dict[str, str] = {}
    if meta_path.is_file():
        mdf = pd.read_csv(meta_path)
        for _, row in mdf.iterrows():
            updated[str(row["dataset_id"])] = str(row["dataset_last_updated"])

    def _updated_line(dataset_id: str) -> str:
        ts = updated.get(dataset_id)
        if not ts:
            return ""
        return (
            f'<br><span style="font-size:0.9em;color:var(--brand-text-dim);">'
            f"Last updated: {html.escape(ts)}</span>"
        )

    return (
        "<p>The dashboard is powered by robust, open-access data retrieved from the "
        "Eurostat Data Browser via the official API. <br>Three primary datasets "
        "form the backbone of the analysis:</p>"
        f'<p><a href="https://ec.europa.eu/eurostat/databrowser/view/ten00124/" target="_blank" rel="noopener noreferrer" '
        f'style="color:inherit;text-decoration:none;"><code style="color:{_accent};font-weight:700;">[ten00124]</code></a> '
        f'<span style="font-weight:700;">Final energy consumption by sector</span>: '
        "<br>provides annual data on the energy end-use across industrial and residential segments;"
        f"{_updated_line('ten00124')}</p>"
        f'<p><a href="https://ec.europa.eu/eurostat/databrowser/view/nrg_ind_ren/" target="_blank" rel="noopener noreferrer" '
        f'style="color:inherit;text-decoration:none;"><code style="color:{_accent};font-weight:700;">[nrg_ind_ren]</code></a> '
        f'<span style="font-weight:700;">Share of energy from renewable sources</span>: '
        "<br>official monitoring indicators for EU renewable energy targets, detailing "
        f"penetration across specific economic sectors;{_updated_line('nrg_ind_ren')}</p>"
        f'<p><a href="https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204/" target="_blank" rel="noopener noreferrer" '
        f'style="color:inherit;text-decoration:none;"><code style="color:{_accent};font-weight:700;">[nrg_pc_204]</code></a> '
        f'<span style="font-weight:700;">Electricity prices for household consumers (bi-annual)</span>: '
        "<br>tracks the evolution of energy costs for the medium-sized consumer segment, including "
        f"a breakdown of taxes and levies.{_updated_line('nrg_pc_204')}</p>"
    )

_DATA_MODEL_CONTENT["Key Variables"] = (
    "<p>To ensure analytical focus, the following specific dimensions were "
    "isolated from the source datasets:</p>"
    f'<p style="font-weight:700;margin-bottom:0.2em;">'
    f'Energy Consumption <code style="color:{_accent};">[ten00124]</code></p>'
    '<ul style="padding-left:2em;">'
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">Consumption Industry</span> '
    f'<code style="color:{_accent};">nrg_bal: FC_IND_E</code>: '
    "final energy consumption in the industrial sector;</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">Consumption Transport</span> '
    f'<code style="color:{_accent};">nrg_bal: FC_TRA_E</code>: '
    "final energy consumption in the transport sector;</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">Consumption Households</span> '
    f'<code style="color:{_accent};">nrg_bal: FC_OTH_HH_E</code>: '
    "final energy consumption by residential consumers.</li>"
    "</ul>"
    f'<p style="font-weight:700;margin-bottom:0.2em;">'
    f'Renewable Shares <code style="color:{_accent};">[nrg_ind_ren]</code></p>'
    '<ul style="padding-left:2em;">'
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">REN Share</span> '
    f'<code style="color:{_accent};">nrg_bal: REN</code>: '
    "overall share of energy from renewable sources;</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">REN Share Transport</span> '
    f'<code style="color:{_accent};">nrg_bal: REN_TRA</code>: '
    "share of renewables in the transport sector;</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">REN Share Heat-Cool</span> '
    f'<code style="color:{_accent};">nrg_bal: REN_HEAT_CL</code>: '
    "share of renewables in heating and cooling;</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">REN Share Electricity</span> '
    f'<code style="color:{_accent};">nrg_bal: REN_ELC</code>: '
    "share of renewables in the electricity sector.</li>"
    "</ul>"
    f'<p style="font-weight:700;margin-bottom:0.2em;">'
    f'Energy Pricing <code style="color:{_accent};">[nrg_pc_204]</code></p>'
    '<ul style="padding-left:2em;">'
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">Price</span> '
    f'<code style="color:{_accent};">tax: X_TAX</code>: '
    "electricity price excluding all taxes, levies, and VAT (net market price);</li>"
    f'<li style="margin-bottom:0.5em;"><span style="font-weight:700;">Price+Tax</span> '
    f'<code style="color:{_accent};">tax: I_TAX</code>: '
    "electricity price including all taxes, levies, and VAT (gross consumer price).</li>"
    "</ul>"
)

_DATA_MODEL_CONTENT["Methodology"] = (
    "<p>The project follows a rigorous pipeline of extraction, transformation, and loading "
    "to ensure data harmonization:</p>"
    "<ul>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">API Integration</span>: '
    "For the price dataset"
    f'<code style="color:{_accent};">[nrg_pc_204]</code>'
    ", which is published semi-annually, S1 and S2 values "
    "are averaged to produce a single annual figure, ensuring alignment with the annual "
    "frequency of consumption and REN datasets"
    f'<code style="color:{_accent};">[nrg_ind_ren]</code>'
    ";</li>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Geographic Filtering</span>: '
    "the scope is strictly limited to individual Member States and EFTA partners. Regional "
    "aggregates (e.g.,"
    f'<code style="color:{_accent};">geo: EU27_2020</code>'
    "," 
    f'<code style="color:{_accent};">geo: EA20</code>'
    ") are programmatically excluded to prevent data duplication in national comparisons;</li>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Temporal Standardization</span>: '
    "the analysis window is fixed to a ten-year band (2015\u20132024). All series are truncated "
    "and merged based on a shared"
    f'<code style="color:{_accent};">geo</code>'  
    "and" 
    f'<code style="color:{_accent};">TIME_PERIOD</code>'  
    "index;</li>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Unit Normalization</span>: '
    "all consumption metrics are expressed in KTOE (Kilotonnes of Oil Equivalent) to allow "
    "for cross-sectoral volume comparison, while RES indicators are maintained in percentages "
    "and prices in EUR/kWh.</li>"
    "</ul>"
)

_DATA_MODEL_CONTENT["Analysis Limitations"] = (
    "<p>While the dashboard provides a comprehensive overview, several constraints should "
    "be noted by the end-user:</p>"
    "<ul>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Sectoral Scope</span>: '
    "by construction, the pipeline omits the Commercial and Public Services ("
    f'<code style="color:{_accent};">nrg_bal: FC_OTH_CP_E</code>'
    "). While the \u201cBig Three\u201d (Industry, Transport, Households) "
    "cover the vast majority of consumption, the Total figures in this dashboard "
    "represent this specific subset, not the absolute national total;</li>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Consumer Band Bias</span>: '
    "pricing data is anchored to the DC Band from 2500 to 4999 kWh ("
    f'<code style="color:{_accent};">nrg_cons: KWH2500-4999</code>'
    "). While this represents "
    "the median EU household, it may not reflect the costs faced by low-income households "
    "or heavy industrial users who operate under different tariff structures;</li>"
    f'<li style="margin-bottom:0.8em;"><span style="font-weight:700;">Missing Data Points</span>: '
    "an \u201cOuter Merge\u201d strategy is used to accommodate countries with incomplete "
    "records for specific years. Consequently, some time-series or scatterplot clusters "
    "may appear fragmented for specific Member States.</li>"
    "</ul>"
)


def render_data_model() -> None:
    """Data Model page — vertical nav buttons (left) with section content (right)."""
    st.session_state.setdefault("dm_section", _DATA_MODEL_SECTIONS[0])

    _pad_l2, col_nav, col_body, _pad_r2 = st.columns([1.5, 1.25, 4.75, 1.5], gap="large")

    with col_nav:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """<style>
            div[data-testid="stVerticalBlock"] div.dm-nav-wrap button {
                width: 100% !important;
                text-align: left !important;
            }
            </style>""",
            unsafe_allow_html=True,
        )
        for label in _DATA_MODEL_SECTIONS:
            btn_type = "primary" if st.session_state.dm_section == label else "secondary"
            if st.button(label, key=f"dm_{label}", use_container_width=True, type=btn_type):
                st.session_state.dm_section = label
                st.rerun()

    with col_body:
        section = st.session_state.dm_section
        st.header(section)
        body = _build_sources_content() if section == "Sources" else _DATA_MODEL_CONTENT.get(section, "")
        st.markdown(
            f'<div style="color:var(--brand-text);font-size:1.05rem;line-height:1.6;'
            f'text-align:justify;text-justify:inter-word;">{body}</div>',
            unsafe_allow_html=True,
        )


def render_about() -> None:
    """About page — project mission (left column) with room for future right column."""
    accent = "var(--brand-accent)"
    text = "var(--brand-text)"
    _pad_l, col_left, _col_right, _pad_r = st.columns([1.5, 3, 3, 1.5], gap="large")
    with col_left:
        st.header("About")
        st.markdown(
            f'<div style="color:{text};font-size:1.05rem;line-height:1.6;text-align:justify;text-justify:inter-word;">'
            f'<p><span style="color:{accent};font-weight:700;">EU-powered</span> '
            f"is a strategic data engine designed to transform complex Eurostat datasets "
            f"into actionable political leverage. This comprehensive roadmap for the "
            f"European energy transition, provides lobbyists and policy advocates with "
            f"the empirical evidence needed to "
            f'<span style="color:{accent};font-weight:700;">bridge the gap between '
            f"climate ambition and economic reality</span>.</p>"
            f'<p style="font-size:calc(1.05rem + 3pt);font-weight:700;">Intended Audience</p>'
            f"<ul>"
            f'<li><span style="color:var(--brand-unpressed);font-weight:700;">Lobbyists</span>: '
            f"seeking to anchor their renewable energy pitches in validated, cross-border statistics;</li>"
            f'<li><span style="color:var(--brand-unpressed);font-weight:700;">Policymakers and '
            f"Advisors</span>: requiring a high-level overview of national progress "
            f"relative to EU-wide benchmarks;</li>"
            f'<li><span style="color:var(--brand-unpressed);font-weight:700;">Publicists and '
            f"Analysts</span>: looking to debunk common myths regarding the costs and "
            f"stability of the green energy transition.</li>"
            f"</ul>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with _col_right:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:{text};font-size:1.05rem;line-height:1.6;text-align:justify;text-justify:inter-word;">'
            f'<p style="font-size:calc(1.05rem + 3pt);font-weight:700;">Strategic Applications</p>'
            f'<ul style="list-style-position:outside;">'
            f'<li style="margin-bottom:0.8em;"><span style="color:var(--brand-unpressed);font-weight:700;">Present the affordability '
            f"argument</span>, by correlating high renewable penetration with long-term "
            f"price stability and lower net costs;</li>"
            f'<li style="margin-bottom:0.8em;"><span style="color:var(--brand-unpressed);font-weight:700;">Expose sectoral '
            f"bottlenecks</span> by identifying exactly where heating and transport "
            f"systems are failing to keep pace with the power grid;</li>"
            f'<li style="margin-bottom:0.8em;"><span style="color:var(--brand-unpressed);font-weight:700;">Optimize capital '
            f"flow</span> by pinpointing the &ldquo;High Potential&rdquo; markets where "
            f"infrastructure investment will deliver the most significant economic and "
            f"environmental ROI;</li>"
            f'<li style="margin-bottom:0.8em;"><span style="color:var(--brand-unpressed);font-weight:700;">Test national '
            f"decarbonization performance</span>, by direct, evidence-based comparisons between "
            f"member states.</li>"
            f"</ul>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ── Figure block config & renderer ──────────────────────────────────────────

@dataclass
class _FigureBlock:
    question: str
    description: str
    country_key: str
    help_key: str
    figure_fn: Callable[..., plt.Figure]
    country_help: str = "Countries shown in this chart only."
    dropna_subset: tuple[str, ...] | None = None
    metric_key: str | None = None
    metric_help: str = ""
    price_source: str | None = None
    default_countries: list[str] | None = None  # None → all available


def _price_format(choice: str) -> str:
    return "Price" if choice == "Price" else "Price + taxes"


_FIGURE_BLOCKS: list[_FigureBlock] = [
    _FigureBlock(
        question=FIGURE_QUESTIONS[0],
        description=FIGURE_META[0],
        country_key="countries_consumption_scale",
        help_key="figure_help_0",
        figure_fn=figure_consumption_scale_context,
        country_help="Countries shown in this chart only (latest year, stacked by sector).",
        default_countries=["Germany", "France", "Poland", "Italy"],
    ),
    _FigureBlock(
        question=FIGURE_QUESTIONS[1],
        description=FIGURE_META[1],
        country_key="countries_total_ren",
        help_key="figure_help_1",
        figure_fn=figure_total_ren_share,
        dropna_subset=("year", "REN Share"),
        default_countries=["Poland", "Sweden", "Germany"],
    ),
    _FigureBlock(
        question=FIGURE_QUESTIONS[2],
        description=FIGURE_META[2],
        country_key="countries_sectoral_ren",
        help_key="figure_help_2",
        figure_fn=figure_sectoral_ren_share,
        default_countries=["Poland", "Sweden", "Germany"],
    ),
    _FigureBlock(
        question=FIGURE_QUESTIONS[3],
        description=FIGURE_META[3],
        country_key="countries_price_corr",
        help_key="figure_help_3",
        figure_fn=figure_share_vs_price_correlation,
        metric_key="fig4_price_kind",
        metric_help="Same price series is used for Figure 5 (boxplot).",
        price_source="fig4_price_kind",
    ),
    _FigureBlock(
        question=FIGURE_QUESTIONS[4],
        description=FIGURE_META[4],
        country_key="countries_price_stability",
        help_key="figure_help_4",
        figure_fn=figure_price_stability_analysis,
        price_source="fig4_price_kind",
    ),
    _FigureBlock(
        question=FIGURE_QUESTIONS[5],
        description=FIGURE_META[5],
        country_key="countries_invest_potential",
        help_key="figure_help_5",
        figure_fn=figure_investment_potential,
        metric_key="fig6_price_kind",
        price_source="fig6_price_kind",
        default_countries=["Poland", "Hungary", "Romania"],
    ),
]


def _render_figure_block(
    cfg: _FigureBlock,
    df: pd.DataFrame,
    countries: list[str],
    price_selections: dict[str, str],
    *,
    is_last: bool,
) -> None:
    _pad_l3, col_plot, col_text, _pad_r3 = st.columns([0.25, 1.8, 1.2, 0.25], gap="large")

    if cfg.default_countries is not None:
        fig_defaults = [c for c in cfg.default_countries if c in countries]
    else:
        fig_defaults = countries

    with col_text:
        _figure_question_heading(cfg.question)
        _countries_chooser_label()
        selected = st.multiselect(
            "Country selection",
            options=countries,
            default=fig_defaults,
            help=cfg.country_help,
            key=cfg.country_key,
            label_visibility="collapsed",
        )
        if cfg.metric_key:
            _metric_chooser_label(tight_below_country_panel=True)
            radio_kw: dict = dict(
                label="Metric selection",
                options=["Price", "Price+Taxes"],
                format_func=_price_format,
                horizontal=True,
                key=cfg.metric_key,
                label_visibility="collapsed",
            )
            if cfg.metric_help:
                radio_kw["help"] = cfg.metric_help
            price_selections[cfg.metric_key] = st.radio(**radio_kw)
        _figure_help_button(cfg.description, key=cfg.help_key)

    with col_plot:
        if not selected:
            st.info("Select at least one country for this chart.")
        else:
            plot_df = df[df["Country"].isin(selected)]
            if cfg.dropna_subset:
                plot_df = plot_df.dropna(subset=list(cfg.dropna_subset))
            if plot_df.empty:
                st.warning("No rows for this selection.")
            else:
                kwargs: dict = {"figsize": STANDARD_FIG_SIZE}
                if cfg.price_source:
                    kwargs["price_col"] = price_selections.get(
                        cfg.price_source, "Price"
                    )
                if cfg.figure_fn is figure_share_vs_price_correlation:
                    kwargs["show_legend"] = len(selected) <= 10
                fig = cfg.figure_fn(plot_df, **kwargs)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    if not is_last:
        _after_figure_break()


# ── Navigation ──────────────────────────────────────────────────────────────

_NAV_LABELS = ["Showroom", "Data Model", "About"]


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="EU Renewable Energy Navigator",
        layout="wide",
    )
    _inject_brand_styles()
    _page_title_and_subtitle(
        "euPOWERED: EU Renewable Energy Navigator",
        "Strategic Analytics for Decarbonization, Economic Resilience, "
        "and Energy Security (2015–2024)",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.session_state.setdefault("dashboard_view_mode", "Showroom")
    nav_clicked = False
    _, nav_block, _ = st.columns([1, 1, 1])
    with nav_block:
        cols = st.columns(len(_NAV_LABELS))
        for col, label in zip(cols, _NAV_LABELS):
            with col:
                btn_type = (
                    "primary"
                    if st.session_state.dashboard_view_mode == label
                    else "secondary"
                )
                if st.button(
                    label,
                    use_container_width=True,
                    type=btn_type,
                    key=f"btn_{label.lower().replace(' ', '')}",
                ):
                    st.session_state.dashboard_view_mode = label
                    nav_clicked = True

    view = st.session_state.dashboard_view_mode
    _credit_above_divider()
    st.divider()

    if nav_clicked:
        st.rerun()

    if view == "Data Model":
        render_data_model()
        return

    if view == "About":
        render_about()
        return

    preprocessed_path = DATA_PATH / PREPROCESSED_CSV
    if not preprocessed_path.is_file():
        st.error(f"Missing data file: `{PREPROCESSED_CSV}`")
        st.info(
            "Run the preprocessing pipeline first, for example:\n\n"
            "`python preproc_code.py`"
        )
        return

    df = load_data()
    countries = sorted(df["Country"].dropna().unique().tolist())

    for cfg in _FIGURE_BLOCKS:
        if cfg.metric_key:
            st.session_state.setdefault(cfg.metric_key, "Price")

    price_selections: dict[str, str] = {}
    for i, cfg in enumerate(_FIGURE_BLOCKS):
        _render_figure_block(
            cfg,
            df,
            countries,
            price_selections,
            is_last=(i == len(_FIGURE_BLOCKS) - 1),
        )


if __name__ == "__main__":
    main()
