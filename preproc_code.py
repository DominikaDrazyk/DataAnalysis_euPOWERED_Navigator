#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import numpy as np
import scipy as sp
from scipy.stats import shapiro
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'fonts', 'Ubuntu-Regular.ttf')
STYLE_PATH = os.path.join(BASE_DIR, 'custom.mplstyle')
FIGURES_PATH = os.path.join(BASE_DIR, 'figures')
DATA_PATH = os.path.join(BASE_DIR, 'data')

pd.options.display.precision = 3
plt.style.use(STYLE_PATH)
full_palette = plt.rcParams["axes.prop_cycle"].by_key()["color"]

if os.path.exists(FONT_PATH):
    fe = fm.FontEntry(
        fname = FONT_PATH,
        name = 'ProjectUbuntu'
    )
    fm.fontManager.ttflist.insert(0, fe)
    plt.rcParams['font.family'] = fe.name
else:
    print("Warning: Font file not found. Falling back to sans-serif.")
    plt.rcParams['font.family'] = 'sans-serif'

def load_datasets():
    print("---- O1.1 Loading datasets...")
    
    df_path = os.path.join(DATA_PATH, 'scraper_data.csv')
    df = pd.read_csv(df_path)
    print(f"✓ Main dataset loaded: {len(df):,} records")

    mdf_path = os.path.join(DATA_PATH, 'scraper_metadata.csv')
    mdf = pd.read_csv(mdf_path)
    print(f"✓ Metadata loaded: {len(mdf):,} records")

    return df, mdf

def filter_and_rename_variables(df):
    print("---- O1.2 Filtering and renaming variables:")
    
    print("• Converting time to datetime format")
    df['year'] = pd.to_datetime(df['year'], format = '%Y', errors = 'coerce')
    nan_pct = df.year.isnull().sum()*100/len(df.year)
    print(f"• Year conversion: {nan_pct:.0f}% values converted to NaT")

    print("• Renaming columns for clarity")
    df = df.rename(columns = {"REN_value": "REN Share",
                              "REN_TRA_value": "REN Share Transport",
                              "REN_HEAT_CL_value" : "REN Share Heat-Cool",
                              "REN_ELC_value": "REN Share Electricity",
                              "FC_IND_E_value": "Consumption Industry",
                              "FC_TRA_E_value": "Consumption Transport",
                              "FC_OTH_HH_E_value": "Consumption Households",
                              "I_TAX_value": "Price+Taxes",
                              "X_TAX_value": "Price"})

    df.sort_values(by= ['year','geo','Country'], inplace = True)

    print(f"Pre-processed Dataset Preview:")
    print(f"• Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print("• Sample data (head):")
    print(df.head(5))
    print()
    
    return df

def review_missing_data(df):
    print("---- O1.3 Missing data analysis:")

    nan_count = df.isna().sum()
    all_count = df.iloc[:,0].count()
    prc = (nan_count * 100)/all_count
    print("Missing Data by Column:")
    for col, pct in prc.items():
            print(f"• {col}: {pct:.0f}% missing")
    print()

    print("---- O1.3.0-2 The percentage of data entry gaps per country:")
    df_nans_ten00124 = df.groupby('geo')[['Consumption Industry', 'Consumption Transport', 'Consumption Households']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'geo')

    df_nans_nrg_ind_ren = df.groupby('geo')[['REN Share','REN Share Transport', 'REN Share Heat-Cool', 'REN Share Electricity']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'geo')

    df_nans_nrg_pc_204 = df.groupby('geo')[['Price+Taxes', 'Price']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'geo')

    f = -1
    for df_nans in [df_nans_ten00124, df_nans_nrg_ind_ren, df_nans_nrg_pc_204]: 
        f += 1
        df_nans = df_nans.stack().reset_index().rename(columns={'level_1': 'metrics', 0: 'value'})

        plt.close('all') 
        plt.style.use(STYLE_PATH)

        metrics = df_nans['metrics'].unique()
        num_rows = len(metrics)

        fig, axes = plt.subplots(num_rows, 1, figsize = (8, 3 * num_rows), sharey = True)
        if num_rows == 1: axes = [axes]
        for i, metric in enumerate(metrics):
            data_subset = df_nans[df_nans['metrics'] == metric]

            sns.barplot(data = data_subset, x = 'geo', y = 'value', ax = axes[i])

            axes[i].set_title(f"Metric: {metric}")
            axes[i].set_ylabel("NaN entries [%]")
            axes[i].set_xlabel("Country")

            axes[i].set_ylim(0, 100)
            axes[i].set_yticks([0, 20, 40, 60, 80, 100])
            axes[i].tick_params(axis = 'x', rotation = 90)

        plt.suptitle('The percentage of NaN values per country', y = 1.005)
        plt.tight_layout()

        file_name = f'Fig1.3.{f} The percentage of NaN values per country.png'
        save_path = os.path.join(FIGURES_PATH, file_name)
        #plt.savefig(save_path)
        #plt.show()
        print(f"✓ Saved: {file_name}")
    print()

    print("---- O1.3.3-5 The percentage of data entry gaps across years:")
    df_nans_ten00124 = df.groupby('year')[['Consumption Industry', 'Consumption Transport', 'Consumption Households']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'year')

    df_nans_nrg_ind_ren = df.groupby('year')[['REN Share','REN Share Transport', 'REN Share Heat-Cool', 'REN Share Electricity']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'year')

    df_nans_nrg_pc_204 = df.groupby('year')[['Price+Taxes', 'Price']].apply(
    lambda x: (x.isna().sum() * 100 / len(x) )).sort_values(by = 'year')

    for df_nans in [df_nans_ten00124, df_nans_nrg_ind_ren, df_nans_nrg_pc_204]: 
        f += 1
        df_nans = df_nans.stack().reset_index().rename(columns={'level_1': 'metrics', 0: 'value'})

        plt.close('all') 
        plt.style.use(STYLE_PATH)
        plt.rcParams.update({'figure.figsize': (7,4)})

        ax = sns.lineplot(data = df_nans, x = 'year', y = 'value', hue = 'metrics', linewidth = 2)

        plt.title('The percentage of NaN values per year', loc = 'center')
        plt.xlabel("Year")
        plt.ylabel("Percentage of NaN entries [%]")

        plt.legend(title = "Metrics", loc = 'upper left', bbox_to_anchor=(1.01, 0.98))

        plt.yticks([0,10,20,30,40,50,60,70,80,90,100], ['0','10','20','30','40','50','60','70','80','90','100'])
        
        plt.tight_layout()
        
        file_name = f'Fig1.3.{f} The percentage of data entry gaps across years.png'
        save_path = os.path.join(FIGURES_PATH, file_name)
        #plt.savefig(save_path)
        #plt.show()
        print(f'✓ Saved: {file_name}')
    print()
    return df

def display_metadata(mdf):
    print("Source metadata:")
    print("• Current analysis was prepared based on the following information sources:")
    
    for i, row in mdf.iterrows():
        print(f"  {i+1}. {mdf.dataset_id[i]} dataset provided by: {mdf.dataset_source[i]}")
        print(f"     Last updated: {mdf.dataset_last_updated[i]}")
    print()

def save_preprocessed_datasets(df):
    print("Saving analysis results:")
    
    file_name = 'preprocessed_data.csv'
    save_path = os.path.join(DATA_PATH, file_name)
    df.to_csv(save_path, encoding='utf-8', index=False)
    print(f"✓ Preprocessed dataset saved: {file_name} ({df.shape[0]:,} rows)")

def main():
    print("=" * 60)
    print("Energy Consumption in the EU (2015‑2025)")
    print("Data Analysis Pipeline")
    print("=" * 60)
    print()
    
    # Phase 1: Loading datasets
    df, mdf = load_datasets()
    
    # Phase 2: Filtering and renaming variables
    df = filter_and_rename_variables(df)
    
    # Phase 3: Analyzing missing data
    df = review_missing_data(df)
    
    # Phase 4: Save results
    save_preprocessed_datasets(df)

if __name__ == "__main__":
    main()