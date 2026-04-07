#!/usr/bin/env python
# coding: utf-8

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
from pyjstat import pyjstat
import pandas as pd
import re
import requests
from typing import Optional
from urllib.parse import urlencode
import time
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")

YEAR_MIN = 2015
YEAR_MAX = 2024

EUROSTAT_API_ROOT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# API filters (used only for scraping; removed from final wide dataset)
TEN00124_NRG_BAL = ("FC_IND_E", "FC_TRA_E", "FC_OTH_HH_E")
TEN00124_SIEC = "TOTAL"
TEN00124_UNIT = "KTOE"

NRG_IND_REN_NRG_BAL = ("REN", "REN_TRA", "REN_HEAT_CL", "REN_ELC")
NRG_IND_REN_UNIT = "PC"

NRG_PC_204_NRG_CONS = "KWH2500-4999"
NRG_PC_204_TAX = ("I_TAX", "X_TAX")
NRG_PC_204_CURRENCY = "EUR"

TEN00124_DATABROWSER = "https://ec.europa.eu/eurostat/databrowser/view/ten00124/default/table?lang=en"
NRG_PC_204_DATABROWSER = "https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204__custom_20778998/default/table"
NRG_IND_REN_DATABROWSER = "https://ec.europa.eu/eurostat/databrowser/view/nrg_ind_ren/default/table?lang=en"

GEO_EXCLUDE = {"EA", "EA20", "EA21", "EU27_2020"}

# wide index includes Country as requested
WIDE_INDEX = ["geo", "Country", "year"]


def extract_country_mapping() -> pd.DataFrame:
    """
    Scrape geo → Country (EU + EFTA) mapping from Eurostat glossary.
    Output columns: Country, geo
    """
    url = "https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Glossary:Country_codes"
    # Avoid pandas.read_html() because it requires lxml in many environments.
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    soup = bs(r.text, "html.parser")

    content_div = soup.find("div", {"id": "mw-content-text"})
    if content_div is None:
        raise RuntimeError("Could not find mw-content-text on Country_codes page")

    tables = content_div.find_all("table")
    rows: list[dict] = []

    for i, table in enumerate(tables[:2]):  # EU table + EFTA table
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            # Cells are typically: Country | (CODE) | Country | (CODE) ...
            cells = [td.get_text(" ", strip=True) for td in tds]
            for j in range(0, len(cells) - 1, 2):
                country = cells[j].strip()
                geo = cells[j + 1].strip().replace("(", "").replace(")", "").strip()
                if geo and country:
                    rows.append({"Country": country, "geo": geo})

    df = pd.DataFrame(rows).drop_duplicates().sort_values("geo").reset_index(drop=True)
    df = df[~df["geo"].isin(GEO_EXCLUDE)]

    df.to_csv(os.path.join(DATA_PATH, "eu_efta_countries.csv"), index=False, encoding="utf-8")
    return df


def _eu_api_data_url(dataset_code: str, filters: dict) -> str:
    pairs: list[tuple[str, str]] = [("lang", "en")]
    for key, val in filters.items():
        if isinstance(val, (list, tuple, set)):
            for v in val:
                pairs.append((key, str(v)))
        else:
            pairs.append((key, str(val)))
    return f"{EUROSTAT_API_ROOT}/{dataset_code}?{urlencode(pairs)}"


def _fetch_json_stat_table(url: str, dataset_label: str) -> pd.DataFrame:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("value"):
        raise ValueError(f"{dataset_label}: API returned no observations. URL: {url}")
    df = pyjstat.from_json_stat(payload, naming="id")[0]
    print(f"✓ {dataset_label} extracted: {len(df):,} records, shape {df.shape}")
    return df


def extract_data(allowed_geos: list[str]):
    print("---- O1.1 Extracting Eurostat datasets (API-filtered narrow slice):")

    url_ten = _eu_api_data_url(
        "ten00124",
        {
            "geo": allowed_geos,
            "nrg_bal": TEN00124_NRG_BAL,
            "siec": TEN00124_SIEC,
            "unit": TEN00124_UNIT,
        },
    )
    print("• ten00124 — nrg_bal FC_IND_E/FC_TRA_E/FC_OTH_HH_E; siec TOTAL; unit KTOE")
    data_ten00124 = _fetch_json_stat_table(url_ten, "ten00124")

    url_ren = _eu_api_data_url(
        "nrg_ind_ren",
        {"geo": allowed_geos, "nrg_bal": NRG_IND_REN_NRG_BAL, "unit": NRG_IND_REN_UNIT},
    )
    print("• nrg_ind_ren — nrg_bal REN/REN_TRA/REN_HEAT_CL/REN_ELC; unit PC")
    data_nrg_ind_ren = _fetch_json_stat_table(url_ren, "nrg_ind_ren")

    url_204 = _eu_api_data_url(
        "nrg_pc_204",
        {
            "geo": allowed_geos,
            "nrg_cons": NRG_PC_204_NRG_CONS,
            "tax": NRG_PC_204_TAX,
            "currency": NRG_PC_204_CURRENCY,
        },
    )
    print("• nrg_pc_204 — nrg_cons KWH2500-4999; tax I_TAX,X_TAX; currency EUR")
    data_nrg_pc_204 = _fetch_json_stat_table(url_204, "nrg_pc_204")
    print()

    return data_ten00124, data_nrg_ind_ren, data_nrg_pc_204


def _parse_eurostat_databrowser_metadata(soup: bs) -> list:
    body = soup.find("body")
    if body is None:
        raise RuntimeError("No <body> in Databrowser page source")

    marker = body.find("span", string="last update")
    if marker is None:
        raise RuntimeError("Could not find 'last update' on Databrowser page")
    tag = marker.find_next("b", class_="infobox-text-data")
    last_updated = tag.get_text(strip=True)

    marker = body.find("span", string="Source of data:")
    tag = marker.find_next("span")
    source = tag.get_text(strip=True)

    title_el = soup.find("h1", class_="ecl-page-header__title")
    title = title_el.get_text() if title_el else ""

    marker = body.find("span", string="Online data code:")
    tag = marker.find_next("b", class_="infobox-text-data")
    dataset_id = tag.get_text(strip=True)

    return [dataset_id, source, title, last_updated]


def _scrape_eurostat_metadata(url: str, label: str) -> list:
    print(f"• {label}")
    print(f"  Source: {url}")

    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(20)
    soup = bs(driver.page_source, "html.parser")
    driver.close()

    meta_row = _parse_eurostat_databrowser_metadata(soup)
    print(f"    - Dataset ID: {meta_row[0]}")
    print(f"    - Source: {meta_row[1]}")
    print(f"    - Title: {meta_row[2]}")
    print(f"    - Last updated: {meta_row[3]}")
    print()
    return meta_row


def extract_metadata():
    print("---- O1.2 Extracting dataset metadata:")
    rows = [
        _scrape_eurostat_metadata(TEN00124_DATABROWSER, "ten00124"),
        _scrape_eurostat_metadata(NRG_PC_204_DATABROWSER, "nrg_pc_204 (custom table)"),
        _scrape_eurostat_metadata(NRG_IND_REN_DATABROWSER, "nrg_ind_ren"),
    ]
    meta = pd.DataFrame(
        rows,
        columns=["dataset_id", "dataset_source", "dataset_title", "dataset_last_updated"],
    )
    meta.to_csv(os.path.join(DATA_PATH, "scraper_metadata.csv"), encoding="utf-8", index=False)
    print("✓ Metadata saved: data/scraper_metadata.csv")
    print()


def _drop_freq(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=["freq"], errors="ignore")


def _year_from_eurostat_time(s) -> Optional[str]:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    t = str(s).strip()
    m = re.match(r"^(\d{4})", t)
    return m.group(1) if m else None


def _year_filter(df: pd.DataFrame, label: str) -> pd.DataFrame:
    y = pd.to_numeric(df["year"], errors="coerce")
    mask = y.between(YEAR_MIN, YEAR_MAX)
    out = df.loc[mask].copy()
    out["year"] = y.loc[mask].astype(int)
    print(f"  • {label}: years {YEAR_MIN}–{YEAR_MAX} → {len(out):,} rows")
    return out


def harmonize_semiannual_to_annual(df: pd.DataFrame, label: str) -> pd.DataFrame:
    out = df.copy()
    out["year"] = out["time"].map(_year_from_eurostat_time)
    out = out[out["year"].notna()]
    dim_cols = [c for c in out.columns if c not in ("time", "value", "year")]
    out = out.groupby(dim_cols + ["year"], dropna=False, as_index=False)["value"].mean()
    print(f"  • {label}: semi-annual → annual mean (S1+S2) → {len(out):,} rows")
    return out


def _normalize_base(df: pd.DataFrame, has_time: bool) -> pd.DataFrame:
    out = df.copy()
    if "value" in out.columns:
        out = out.rename(columns={"value": "obs_value"})
    if has_time:
        out["year"] = out["time"].map(_year_from_eurostat_time)
        out = out.drop(columns=["time"], errors="ignore")
    if "obs_value" not in out.columns:
        raise ValueError("Expected column 'value' or 'obs_value'")
    return out


def _pivot_value_column(df: pd.DataFrame, pivot_col: str) -> pd.DataFrame:
    work = df[WIDE_INDEX + [pivot_col, "obs_value"]].dropna(subset=WIDE_INDEX + [pivot_col]).copy()
    wide = (
        work.pivot_table(index=WIDE_INDEX, columns=pivot_col, values="obs_value", aggfunc="mean")
        .reset_index()
    )
    rename = {c: f"{c}_value" for c in wide.columns if c not in WIDE_INDEX}
    return wide.rename(columns=rename)


def _attach_country(df: pd.DataFrame, geo_to_country: dict) -> pd.DataFrame:
    out = df.copy()
    out["Country"] = out["geo"].map(geo_to_country)
    return out


def _safe_outer_merge(left: pd.DataFrame, right: pd.DataFrame, label: str) -> pd.DataFrame:
    right2 = right.copy()
    collisions = set(left.columns).intersection(set(right2.columns)) - set(WIDE_INDEX)
    if collisions:
        right2 = right2.rename(columns={c: c.replace("_value", f"_{label}_value") for c in collisions})
    return pd.merge(left, right2, on=WIDE_INDEX, how="outer", sort=True)


def build_wide_dataset(
    ten: pd.DataFrame,
    ren: pd.DataFrame,
    pc204: pd.DataFrame,
    geo_to_country: dict,
) -> pd.DataFrame:
    print("---- O2 Building wide dataset:")

    ten = _attach_country(_drop_freq(ten), geo_to_country)
    ten = _year_filter(_normalize_base(ten, has_time=True), "ten00124")
    ten_wide = _pivot_value_column(ten, "nrg_bal")

    ren = _attach_country(_drop_freq(ren), geo_to_country)
    ren = _year_filter(_normalize_base(ren, has_time=True), "nrg_ind_ren")
    ren_wide = _pivot_value_column(ren, "nrg_bal")

    pc204 = _attach_country(_drop_freq(pc204), geo_to_country)
    pc204_a = harmonize_semiannual_to_annual(pc204, "nrg_pc_204").rename(columns={"value": "obs_value"})
    pc204_a = _year_filter(pc204_a, "nrg_pc_204")
    pc204_wide = _pivot_value_column(pc204_a, "tax")

    wide = ten_wide
    wide = _safe_outer_merge(wide, ren_wide, "nrg_ind_ren")
    wide = _safe_outer_merge(wide, pc204_wide, "nrg_pc_204")

    wide = wide.sort_values(WIDE_INDEX).reset_index(drop=True)
    print(f"✓ Wide dataset: {wide.shape[0]:,} rows × {wide.shape[1]} cols")
    print()
    return wide


def main():
    print("=" * 60)
    print("Eurostat — wide geo-year dataset (official; no nrg_bal_s)")
    print("=" * 60)
    print()

    countries = extract_country_mapping()
    allowed_geos = sorted([g for g in countries["geo"].unique().tolist() if g not in GEO_EXCLUDE])
    geo_to_country = dict(zip(countries["geo"], countries["Country"]))

    ten, ren, pc204 = extract_data(allowed_geos)
    extract_metadata()

    wide = build_wide_dataset(ten, ren, pc204, geo_to_country)
    wide.to_csv(os.path.join(DATA_PATH, "scraper_data.csv"), index=False, encoding="utf-8")
    print("✓ Saved: data/scraper_data.csv")


if __name__ == "__main__":
    main()

