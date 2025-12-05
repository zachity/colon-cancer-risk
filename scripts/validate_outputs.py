import os
import sys
import pandas as pd

OUTPUT_PATH = os.path.join("data", "processed", "combined_state_summary_2022.csv")

EXPECTED_COLUMNS = [
    "StateFIPS",
    "State",
    "Abbrev",
    "obesity_rate",
    "smoking_rate",
    "incidence_rate_adj",
    "incidence_cases",
]

def fail(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(code)

def warn(msg: str) -> None:
    print(f"[WARN] {msg}")

def ok(msg: str) -> None:
    print(f"[OK]   {msg}")

def main() -> None:
    print("===============================================")
    print("  Validating combined_state_summary_2022.csv")
    print("===============================================")

    # 1. File exists
    if not os.path.exists(OUTPUT_PATH):
        fail(f"Output file not found: {OUTPUT_PATH}")

    ok(f"Found output file: {OUTPUT_PATH}")

    # 2. Load CSV
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        fail(f"Could not read CSV: {e}")

    # 3. Columns check
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        fail(f"Missing expected columns: {missing_cols}")

    extra_cols = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if extra_cols:
        warn(f"Extra columns present (this is OK if intentional): {extra_cols}")

    ok("All expected columns present.")

    # 4. Row count check (51 states: 50 + DC)
    n_rows = len(df)
    if n_rows != 51:
        warn(f"Expected 51 rows (50 states + DC), found {n_rows}.")
    else:
        ok("Row count is 51 (50 states + DC).")

    # 5. Missing values in key columns
    key_cols = ["State", "Abbrev", "obesity_rate", "smoking_rate", "incidence_rate_adj"]
    missing_summary = df[key_cols].isnull().sum()
    problematic = missing_summary[missing_summary > 0]
    if not problematic.empty:
        warn(f"Missing values detected in key columns:\n{problematic}")
    else:
        ok("No missing values in key columns.")

    # 6. Range checks for rates (soft sanity checks)
    def check_range(col, low, high):
        if col not in df.columns:
            return
        series = df[col].dropna()
        if series.empty:
            warn(f"{col}: no non-missing values to check.")
            return
        min_val, max_val = series.min(), series.max()
        if min_val < low or max_val > high:
            warn(f"{col}: values out of expected range [{low}, {high}]. "
                 f"Observed min={min_val}, max={max_val}")
        else:
            ok(f"{col}: values within expected range [{low}, {high}].")

    check_range("obesity_rate", 10, 60)
    check_range("smoking_rate", 0, 40)
    check_range("incidence_rate_adj", 10, 100)

    # 7. Incidence cases non-negative
    if "incidence_cases" in df.columns:
        negative_cases = (df["incidence_cases"] < 0).sum()
        if negative_cases > 0:
            warn(f"incidence_cases: {negative_cases} rows have negative values.")
        else:
            ok("incidence_cases: all values are non-negative.")

    print("===============================================")
    print("Validation complete. See messages above.")
    print("===============================================")

if __name__ == "__main__":
    main()
