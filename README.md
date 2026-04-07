# euPOWERED: EU Renewable Energy Navigator
***Strategic Analytics for Decarbonization, Economic Resilience, and Energy Security (2015–2024)***

## :large_orange_diamond: About Me

I am a Doctor of Neuroscience with strong experience in data analysis, statistical modelling and research design. I focus on translating complex data into actionable insights for business and policy. I enjoy data wrangling, visualization, and project management.

**Skills & tools:** 
- advanced **R**, advanced **Python** (*pandas*, *NumPy*, *matplotlib*, *seaborn*, *scipy*) - see my [Python portfolio project](https://github.com/DominikaDrazyk/DataAnalysis_Efficiency_and_Diversity), 
- developing my skills in **Power BI** and **Power Apps** - see my [PowerBI portfolio project](https://github.com/DominikaDrazyk/DataAnalysis_Consultant_Dashboard),
- developing my skills in **SQL** (**ETL**, **PostgreSQL**, **pgAdmin4**, **DBeaver**) - see my [SQL portfolio project](https://github.com/DominikaDrazyk/DataAnalysis_eCommerce_Audit),
- comfortable managing **AI-augmented workflow**, leveraging *Cursor IDE* and *Claude* while ensuring code integrity through manual review - read along for more information,
- technical documentation in **Jupyter Notebook** (*Markdown* syntax), version control in **Git**.

&emsp; **Location**: Poland, Krakow <br> 
&emsp; **Contact**: dominika.a.drazyk@gmail.com <br> 
&emsp; **LinkedIn**: [in/dominika-drazyk-otw95](https://www.linkedin.com/in/dominika-drazyk-otw95/)

## :large_orange_diamond: Project Navigation
Select the path that best matches your interest:

**1. Executive & Business Insight** <br>
*For reviewers focused on storytelling, strategy, and end-results.*

- [PDF Presentation](./reports/euPOWERED_Navigator_presentation.pdf): a step-by-step walkthrough of the project’s assumptions, technical execution highlights, and business insights;

- [Images](./images/): a repository of all screenshots from the dashboard used to present the capabilities of the Navigator.

**2. Technical Deep-Dive & Audit** <br>
*For reviewers interested in the full analytical process and data interpretation.*

- [Codes](./codes/): production-ready data scraping, preprocessing and analysis scripts:
    - [Scraper code](./py_codes/scraper_code.py): script for Eurostat datasets and metadata scraping;
    - [Preprocessing code](./py_codes/preproc_code.py): script for preprocessing and a systematic missing-data audit;
    - [Figure code](./py_codes/figures.py): script generating styled, publication-ready figures;
    - [Dashboard code](./py_codes/dashboard.py): script rendering a three-page dashboard.

:eight_spoked_asterisk: **Dependency Management** <br>
A strictly defined environment manifest ensuring 100% reproducibility and security. Please, follow those steps in case you would like to run the code on your local machine: 

- **Step 1: Initialize the Virtual Environment**

*Linux / macOS Bash*
```
python3 -m venv .venv
source .venv/bin/activate
```
*Windows PowerShell*
```
python -m venv .venv
.venv\Scripts\activate
```
- **Step 2: Install Required Dependencies**
```
pip install --upgrade pip
pip install -r requirements.txt
```

## :large_orange_diamond: Overview

An end-to-end data analytics project that scrapes, harmonizes, and visualizes a decade of EU energy statistics from Eurostat — then delivers the results through an interactive Streamlit dashboard built for lobbyists, policymakers, and energy analysts.

:part_alternation_mark: *Practical business applications*:
- **Present the affordability argument**, by correlating high renewable penetration with long-term price stability and lower net costs;
- **Expose sectoral bottlenecks** by identifying exactly where heating and transport systems fail to keep pace with the power grid;
- **Optimize capital flow** by pinpointing the “High Potential” markets where infrastructure investment will deliver the most significant economic and environmental ROI;
- **Test national decarbonization performance**, by direct, evidence-based comparisons between member states.

![Screenshot of the dashboard welcome page.](/images/Showroom1.png)

### Data & Source Metadata

External data sources (EUROSTAT):
- [ten00124](https://ec.europa.eu/eurostat/databrowser/view/ten00124/default/table?lang=en) **Final energy consumption by sector**: provides annual data on the energy end-use across industrial and residential segments;
- [nrg_ind_ren](https://ec.europa.eu/eurostat/databrowser/view/nrg_ind_ren/default/table?lang=en) **Share of energy from renewable sources**: official monitoring indicators for EU renewable energy targets, detailing penetration across specific economic sectors;
- [nrg_pc_204](https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_204/default/table?lang=en) **Electricity prices for household consumers (bi-annual)**: tracks the evolution of energy costs for the medium-sized consumer segment, including a breakdown of taxes and levies.

### Key variables

Energy Consumption `[ten00124]`
- Consumption Industry `nrg_bal: FC_IND_E`: final energy consumption in the industrial sector;
- Consumption Transport `nrg_bal: FC_TRA_E`: final energy consumption in the transport sector;
- Consumption Households `nrg_bal: FC_OTH_HH_E`: final energy consumption by residential consumers.

Renewable Shares `[nrg_ind_ren]`
- REN Share `nrg_bal: REN`: overall share of energy from renewable sources;
- REN Share Transport `nrg_bal: REN_TRA`: share of renewables in the transport sector;
- REN Share Heat-Cool `nrg_bal: REN_HEAT_CL`: share of renewables in heating and cooling;
- REN Share Electricity `nrg_bal: REN_ELC`: share of renewables in the electricity sector.

Energy Pricing `[nrg_pc_204]`
- Price `tax: X_TAX`: electricity price excluding all taxes, levies, and VAT (net market price);
- Price+Tax `tax: I_TAX`: electricity price including all taxes, levies, and VAT (gross consumer price).

### Tools & Methods

**Programming & Analysis**: Python {`pandas`, `matplotlib`, `seaborn`, `pyjstat`, `BeautifulSoup`, `Selenium`,`Streamlit`}, HTML/CSS;

**Reporting**: `Streamlit` interactive dashboard, custom `Matplotlib stylesheet`, branded `CSS design system` with custom properties;

**Data Engineering**: Eurostat JSON-stat REST API integration, web scraping, ETL pipeline;

**Version control & sharing**: Git & GitHub;

**Analytics performed**: systematic missing-data audit, trend analysis, correlation analysis, trailing 5-year boxplot with median thresholding, cross-national benchmarking.

## :large_orange_diamond: AI-augumented Workflow

The project was built through an **AI-augmented workflow**, using the `Cursor IDE` and `Claude`. Data extraction, preprocessing, and analytical figure logic were written by the Author and optimized by Cursor. Presentation layer (Streamlit, CSS branding, HTML rendering, code refactoring) were implemented by Cursor under the following rules:
- **Author-driven design decisions**: All visual design choices (e.g, color palette, layout proportions, typography), content, and analytics (e.g, how to group RES Shares) originated from the Author;
- **AI-assisted implementation**: Cursor translated high-level instructions into working code, handling the CSS specificity with Streamlit's internal styles, HTML templating, and Matplotlib API details;
- **Continuous review**: The Author verified every change and provided feedback. The Author also **made direct edits to the Streamlit code independently** between Cursor sessions. Large structural improvements were first proposed by Cursor, then selectively approved or rejected by the Author before implementation.

## :large_orange_diamond: Objectives

1. Extract Eurostat datasets via the official JSON-stat API, scrape country-code mappings and dataset metadata, then harmonize and merge into a single wide CSV indexed by country and year.
<br> Code: `scraper_code.py`

2. Preproces the wide dataset, rename dimension codes to analyst-friendly labels, convert time formats, run a systematic missing-data audit with diagnostic visualizations, export the dashboard-ready CSV.
<br> Code: `preproc_code.py`

3. Return styled, publication-ready figures using a custom font, color palette, and shared matplotlib stylesheet.
<br> Code: `figures.py` 

4. Drive a Streamlit application that renders six interactive analytical figures with per-figure country selection and metric toggles, a Data Model reference section with methodology and variable documentation, and an About page — all styled through a centralized CSS design system.
<br> Code: `dashboard.py`

### What this project delivers:

- A robust Python scraping and preprocessing pipeline ready for raw data imput and normalization.

- A set of well-documented codes for data visualization, ready for reporting.

- Ready-to-use and clear dashboard to support data-driven discussions and decisions.

:part_alternation_mark: Policy-relevant insights for lobbyists, policymakers and publicists interested in EU renewal energy sources transformation.

### Limitations & Challenges

- By design, the pipeline *omits the Commercial and Public Services* (`nrg_bal: FC_OTH_CP_E`). While the Industry, Transport, and Households cover the vast majority of consumption, the Total figures in this dashboard represent this specific subset, not the absolute national total;
- Pricing data is anchored to the DC Band from 2500 to 4999 kWh (`nrg_cons: KWH2500-4999`). While this represents the median EU household, *it may not reflect the costs faced by low-income households or heavy industrial users* who operate under different tariff structures;
- An “Outer Merge” strategy is used to accommodate countries with incomplete records for specific years. Consequently, some time-series or scatterplot clusters may appear *fragmented for specific Member States*.

:grey_exclamation: The insights provided are focused on the strategic application of energy metrics for policy advocacy and are not based on formal academic expertise in European energy economics or legislative drafting. My aim was to demonstrate the ability to architect data, design robust ETL processes, and extract actionable business intelligence from complex relational datasets.

## :large_orange_diamond: Presented skills

**Data Modelling & Engineering**
- Developing custom *web scrapers* (`BeautifulSoup`, `selenium`) to automate the extraction of public datasets and metadata.
- Preparing and cleaning datasets using `pandas` and `NumPy` (*synchronizing* semi-annual series, *mapping* technical Eurostat codes to human-readable, policy-relevant labels, designing an *"Outer Merge" data architecture*).
- Executing systematic *missing-data audits and diagnostic visualizations* to maintain the structural integrity of the unified data model.
- Leveraging AI-augmented development (`Cursor`, `Claude`) to optimize the presentation layer while maintaining strict authorial oversight of analytical logic and visual proportions.

**Data Visualization & Storytelling**
- Imagining an interactive `Streamlit` dashboard with a custom-branded CSS design system and dedicated Matplotlib stylesheets for high-fidelity reporting.
- Translating abstract statistics into a *strategic lobbyist narrative* focused on economic affordability and decarbonization progress.
- Utilizing *advanced visual analytics*, including multidimensional bubble charts and percentile-based boxplots—to identify high-yield investment opportunities and sectoral bottlenecks.
- Preparing *comprehensive documentation* to effectively communicate methodology and limitations.
