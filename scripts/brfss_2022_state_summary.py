

import argparse
import pandas as pd
import numpy as np
from pathlib import Path


FIPS_TO_STATE = {
    1: ("Alabama","AL"), 2: ("Alaska","AK"), 4: ("Arizona","AZ"), 5: ("Arkansas","AR"),
    6: ("California","CA"), 8: ("Colorado","CO"), 9: ("Connecticut","CT"), 10: ("Delaware","DE"),
    11: ("District of Columbia","DC"), 12: ("Florida","FL"), 13: ("Georgia","GA"), 15: ("Hawaii","HI"),
    16: ("Idaho","ID"), 17: ("Illinois","IL"), 18: ("Indiana","IN"), 19: ("Iowa","IA"),
    20: ("Kansas","KS"), 21: ("Kentucky","KY"), 22: ("Louisiana","LA"), 23: ("Maine","ME"),
    24: ("Maryland","MD"), 25: ("Massachusetts","MA"), 26: ("Michigan","MI"), 27: ("Minnesota","MN"),
    28: ("Mississippi","MS"), 29: ("Missouri","MO"), 30: ("Montana","MT"), 31: ("Nebraska","NE"),
    32: ("Nevada","NV"), 33: ("New Hampshire","NH"), 34: ("New Jersey","NJ"), 35: ("New Mexico","NM"),
    36: ("New York","NY"), 37: ("North Carolina","NC"), 38: ("North Dakota","ND"), 39: ("Ohio","OH"),
    40: ("Oklahoma","OK"), 41: ("Oregon","OR"), 42: ("Pennsylvania","PA"), 44: ("Rhode Island","RI"),
    45: ("South Carolina","SC"), 46: ("South Dakota","SD"), 47: ("Tennessee","TN"), 48: ("Texas","TX"),
    49: ("Utah","UT"), 50: ("Vermont","VT"), 51: ("Virginia","VA"), 53: ("Washington","WA"),
    54: ("West Virginia","WV"), 55: ("Wisconsin","WI"), 56: ("Wyoming","WY"),
    66: ("Guam","GU"), 72: ("Puerto Rico","PR"), 78: ("U.S. Virgin Islands","VI")
}

POSSIBLE_COLO_VARS = [
    "HADCOLO", "HADCOLN2", "HADSGCO1", "HADSIGM3", "COLNSPY", "CRCREC", "COLCREEN"
]

def weighted_mean_boolean(indicator: pd.Series, weights: pd.Series) -> float:
    """Weighted mean of a boolean/0-1 series, ignoring NaNs and nonpositive weights."""
    m = indicator.astype("float")
    w = weights.astype("float")
    mask = m.notna() & w.notna() & (w > 0)
    if not mask.any():
        return np.nan
    return np.average(m[mask], weights=w[mask])

def find_weight_column(cols, override=None):
    """Find a plausible BRFSS final weight column (allow user override)."""
    if override:
        if override in cols:
            return override
        raise ValueError(f"--weight-column '{override}' not found in file.")
    common = ["_LLCPWT", "X_LLCPWT", "LLCPWT", "_FINALWT", "FINALWT"]
    for c in common:
        if c in cols:
            return c
    for c in cols:
        u = c.upper()
        if u.endswith("WT") or "WEIGHT" in u or "LLCPWT" in u:
            return c
    return None

def main():
    ap = argparse.ArgumentParser(description="State-level weighted prevalence from BRFSS 2022 XPT.")
    ap.add_argument("--xpt", required=True, help="Path to LLCP22V1.XPT")
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--include-colonoscopy", action="store_true", help="Compute colonoscopy/sigmoidoscopy prevalence if present")
    ap.add_argument("--weight-column", help="Explicit weight column name (e.g., _LLCPWT or X_LLCPWT)")
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading BRFSS XPT: {args.xpt}")
    df = pd.read_sas(args.xpt, format="xport")
    df.columns = [str(c) for c in df.columns]  

    
    for req in ["_STATE", "_BMI5"]:
        if req not in df.columns:
            raise ValueError(f"Missing required column in file: {req}")

  
    weight_col = find_weight_column(df.columns, override=args.weight_column)
    if weight_col is None:
        print("WARNING: No weight column found. Proceeding with UNWEIGHTED percentages (for quick progress only).")
    else:
        print(f"Using weight column: {weight_col}")

    
    bmi = pd.to_numeric(df["_BMI5"], errors="coerce") 
    obese = (bmi >= 3000) & (bmi < 9999)              

  
    if "_SMOKER3" in df.columns:
        sm = pd.to_numeric(df["_SMOKER3"], errors="coerce")
        current_smoker = sm.isin([1, 2])
    else:
        current_smoker = pd.Series(index=df.index, dtype="float")

    colo_series = None
    if args.include_colonoscopy:
        for v in POSSIBLE_COLO_VARS:
            if v in df.columns:
                print(f"Using colonoscopy/sigmoidoscopy variable: {v} (1=Yes)")
                cv = pd.to_numeric(df[v], errors="coerce")
                colo_series = (cv == 1)
                break
        if colo_series is None:
            print("No recognized colonoscopy/sigmoidoscopy variable found; skipping that metric.")

    df["_STATE"] = pd.to_numeric(df["_STATE"], errors="coerce").astype("Int64")
    weights = None if weight_col is None else pd.to_numeric(df[weight_col], errors="coerce")

    def wmean(ind):
        if weights is None:
            m = ind.astype("float")
            m = m[m.notna()]
            return float(m.mean()) if len(m) else np.nan
        return weighted_mean_boolean(ind, weights)

    rows = []
    for fips in sorted(df["_STATE"].dropna().unique()):
        idx = df.index[df["_STATE"] == fips]
        ob_prev = wmean(obese.loc[idx])
        sm_prev = wmean(current_smoker.loc[idx])

        row = {
            "StateFIPS": int(fips),
            "obesity_rate": round(ob_prev * 100, 3) if pd.notna(ob_prev) else np.nan,
            "smoking_rate": round(sm_prev * 100, 3) if pd.notna(sm_prev) else np.nan
        }
        if colo_series is not None:
            co_prev = wmean(colo_series.loc[idx])
            row["colonoscopy_rate"] = round(co_prev * 100, 3) if pd.notna(co_prev) else np.nan

        rows.append(row)

    out = pd.DataFrame(rows).sort_values("StateFIPS").reset_index(drop=True)
    out["State"]  = out["StateFIPS"].map(lambda s: FIPS_TO_STATE.get(s, (None, None))[0])
    out["Abbrev"] = out["StateFIPS"].map(lambda s: FIPS_TO_STATE.get(s, (None, None))[1])

    cols = ["StateFIPS", "State", "Abbrev", "obesity_rate", "smoking_rate"]
    if "colonoscopy_rate" in out.columns:
        cols.append("colonoscopy_rate")
    out = out[cols]

    out.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
