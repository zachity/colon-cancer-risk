# Colon Cancer Risk Analysis: Behavioral Predictors at the U.S. State Level

This project investigates how behavioral and demographic factors—specifically **obesity** and **smoking**—relate to **colon & rectum cancer incidence** across U.S. states.  
Using public health datasets (BRFSS 2022 and USCS 1999–2022), the project builds a reproducible data pipeline and predictive models to identify which factors best explain state-level variation in cancer incidence.

The workflow follows the **CRISP-DM lifecycle**:
1. Business Understanding  
2. Data Understanding  
3. Data Preparation  
4. Modeling  
5. Evaluation  
6. Deployment / Reproducibility

---

## Repository Structure



data/
raw/ # Raw BRFSS XPT and USCS WONDER exports (NOT included)
processed/ # Cleaned + merged datasets ready for analysis

scripts/
brfss_2022_state_summary.py # Processes BRFSS XPT → state-level obesity & smoking
cdc_colon_state_summaries.py # Processes USCS/WONDER → state-level cancer incidence
combine_state_summaries.py # Merges BRFSS + USCS into modeling dataset

notebooks/
01_eda.ipynb # Exploratory Data Analysis
02_modeling.ipynb # Linear regression + random forest
03_final_outputs.ipynb # Final plots/tables used in the report

final_report/
final_report.pdf # Course project report (added upon submission)


---

## Data Sources & Use Requirements

### **BRFSS 2022**
- Source: *Behavioral Risk Factor Surveillance System*  
- File: `LLCP2022.XPT`  
- Access: https://www.cdc.gov/brfss/annual_data/annual_2022.html  
- Notes:  
  - Self-reported survey data  
  - Large file (~1.1 GB)  
  - This repository **does not redistribute** the raw XPT file.  

### **USCS / CDC WONDER (Cancer Incidence)**
- Source: *United States Cancer Statistics (USCS)* via CDC WONDER  
- Access: https://wonder.cdc.gov/cancer.html  
- Query used:  
  - Cancer Site: **Colon and Rectum**  
  - Grouping: **State × Year**  
  - Measures: Age-Adjusted Incidence Rate, Case Count  
- Users must agree to CDC WONDER Terms of Use.

This repository provides **processing scripts only**, not raw data.

---

## Environment Setup

Install required Python packages:
pip install pandas numpy matplotlib seaborn statsmodels scikit-learn pyreadstat


Optional (for notebook use):

pip install jupyter

Reproducing the Full Workflow
1. Download raw data

Place the following in data/raw/:

LLCP2022.XPT                 # BRFSS 2022 combined landline/cell
uscs_1999_2022_full.csv      # USCS WONDER export for colon & rectum cancer

2. Generate processed datasets

From the scripts/ directory:

(A) BRFSS → state-level obesity/smoking
python brfss_2022_state_summary.py ^
  --xpt "../data/raw/LLCP2022.XPT" ^
  --out "../data/processed/brfss_state_summary_2022.csv" ^
  --include-colonoscopy

(B) USCS → state-level cancer incidence
python cdc_colon_state_summaries.py ^
  --in "../data/raw/uscs_1999_2022_full.csv" ^
  --out-state-year "../data/processed/colon_state_year_1999_2022.csv" ^
  --out-state "../data/processed/colon_state_summary_2022.csv" ^
  --year 2022 ^
  --exclude-territories

(C) Merge BRFSS + USCS
python combine_state_summaries.py


After running all steps, you should have:

data/processed/brfss_state_summary_2022.csv
data/processed/colon_state_summary_2022.csv
data/processed/combined_state_summary_2022.csv

Running Analysis

Execute the notebooks in order:

01_eda.ipynb – Summary stats, correlations, plots

02_modeling.ipynb – Linear regression, random forest

03_final_outputs.ipynb – Final figures/tables for the report

Key Output Dataset

combined_state_summary_2022.csv

Column	Meaning
StateFIPS	Numeric state FIPS code
State	Full state name
Abbrev	Two-letter state abbreviation
obesity_rate	Weighted % of adults with BMI ≥ 30 (BRFSS 2022)
smoking_rate	Weighted % of adults who smoke every/some days
incidence_rate_adj	Age-adjusted colon & rectum cancer incidence per 100,000
incidence_cases	Number of cases (USCS 2022)
Limitations

Ecological study: results cannot infer individual risk.

BRFSS is self-reported; subject to bias.

Only two behavioral predictors modeled.

USCS suppressed/small-count cells may add uncertainty.

Required Citation

If using data or scripts from this repo, please cite:

Centers for Disease Control and Prevention (CDC).
Behavioral Risk Factor Surveillance System (BRFSS), 2022.

Centers for Disease Control and Prevention (CDC).
United States Cancer Statistics (USCS), via CDC WONDER.

Author

Zachariah Conlee
University of Illinois – CS 598: Data Curation Final Project
November 2025