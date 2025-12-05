@echo off
echo ===========================================
echo   Colon Cancer Data Curation Pipeline (Windows)
echo ===========================================

set RAW_DIR=data\raw
set PROC_DIR=data\processed
set SCRIPT_DIR=scripts

echo [1/6] Checking for raw datasets...

IF NOT EXIST %RAW_DIR%\LLCP2022.XPT (
    echo ERROR: Missing BRFSS file: %RAW_DIR%\LLCP2022.XPT
    echo Download from: https://www.cdc.gov/brfss/annual_data/annual_2022.html
    pause
    exit /b
)

IF NOT EXIST %RAW_DIR%\uscs_1999_2022_full.csv (
    echo ERROR: Missing USCS file: %RAW_DIR%\uscs_1999_2022_full.csv
    echo Download from: https://wonder.cdc.gov/cancer.html
    pause
    exit /b
)

echo Raw files found.

echo [2/6] Creating processed data directory...
mkdir %PROC_DIR% >nul 2>&1

echo [3/6] Running BRFSS script...
python %SCRIPT_DIR%\brfss_2022_state_summary.py
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR running brfss_2022_state_summary.py
    pause
    exit /b
)

echo [4/6] Running USCS script...
python %SCRIPT_DIR%\cdc_colon_state_summaries.py
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR running cdc_colon_state_summaries.py
    pause
    exit /b
)

echo [5/6] Merging BRFSS + USCS datasets...
python %SCRIPT_DIR%\combine_state_summaries.py
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR running combine_state_summaries.py
    pause
    exit /b
)

echo [6/6] Validating outputs...
python %SCRIPT_DIR%\validate_outputs.py
IF %ERRORLEVEL% NEQ 0 (
    echo Validation script reported issues. See messages above.
    pause
    exit /b
)

echo Processed datasets are located in data\processed\
pause
