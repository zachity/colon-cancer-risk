
import argparse
import pandas as pd
import numpy as np
import re
from pathlib import Path

STATE_ABBREV = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL",
    "Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO",
    "Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
    "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH",
    "Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"
}
TERRITORIES = {"Puerto Rico","Guam","American Samoa",
               "Commonwealth of the Northern Mariana Islands",
               "Virgin Islands","U.S. Virgin Islands"}

def read_wonder(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.read_csv(path, sep="\t", engine="python")
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]
    df.columns = [c.strip() for c in df.columns]
    return df

def first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

def to_number(x):
    if pd.isna(x): return np.nan
    s = str(x).strip()
    if s.lower().startswith("suppressed") or s in {".", "NA", "N/A", ""}:
        return np.nan
    s = re.sub(r"[^0-9\.\-]", "", s)
    try: return float(s) if s else np.nan
    except Exception: return np.nan

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    state_col = first_existing(df, ["States","State","Residence State","State Name"])
    year_col  = first_existing(df, ["Year","Years"])
    site_col  = first_existing(df, ["Cancer Sites","Site","Cancer Site"])
    aar_col   = first_existing(df, ["Age-Adjusted Incidence Rate","Age-Adjusted Rate",
                                    "Age-Adjusted Incidence Rate(†)"])
    count_col = first_existing(df, ["Count","Case Count","Number of Cases"])

    missing = [("States/State", state_col),("Year", year_col),("Cancer Sites", site_col),("Age-Adjusted Rate", aar_col)]
    missing = [name for name,val in missing if val is None]
    if missing:
        raise ValueError(f"Could not find required columns: {missing}\nAvailable columns: {df.columns.tolist()}")

    out = df[[state_col, year_col, site_col]].copy()
    out.columns = ["State","Year","Cancer Sites"]
    out["Age-Adjusted Rate"] = df[aar_col].apply(to_number)
    out["Count"] = df[count_col].apply(to_number) if count_col else np.nan
    out = out.dropna(subset=["State","Year"])
    out["Year"] = pd.to_numeric(out["Year"], errors="coerce").astype("Int64")
    return out

def filter_colon(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["Cancer Sites"].str.contains("Colon", case=False, na=False) | \
           df["Cancer Sites"].str.contains("Colorectal", case=False, na=False) | \
           df["Cancer Sites"].str.contains("C18", case=False, na=False)
    return df.loc[mask].copy()

def add_abbrev(df: pd.DataFrame) -> pd.DataFrame:
    df["Abbrev"] = df["State"].map(STATE_ABBREV)
    return df

def summarize(df: pd.DataFrame, year: int | None, exclude_territories: bool):
    d = df.copy()
    if exclude_territories:
        d = d.loc[~d["State"].isin(TERRITORIES)]
    state_year = (d.groupby(["State","Year"], as_index=False)
                    .agg(age_adjusted_rate=("Age-Adjusted Rate","mean"),
                         total_cases=("Count","sum")))
    state_year = add_abbrev(state_year)

    if year is not None:
        ss = state_year.loc[state_year["Year"] == year, ["State","Abbrev","age_adjusted_rate","total_cases"]].copy()
    else:
        ss = (state_year.groupby(["State","Abbrev"], as_index=False)
                        .agg(age_adjusted_rate=("age_adjusted_rate","mean"),
                             total_cases=("total_cases","sum")))
    state_year = state_year.sort_values(["State","Year"]).reset_index(drop=True)
    ss = ss.sort_values("State").reset_index(drop=True)
    return state_year, ss

def main():
    p = argparse.ArgumentParser(description="Process CDC WONDER/USCS export to state-year and state summaries for Colon & Rectum.")
    p.add_argument("--in", dest="infile", required=True, help="Path to CDC WONDER export (.csv or .txt)")
    p.add_argument("--out-state-year", required=True, help="Output CSV: state-year tidy table")
    p.add_argument("--out-state", required=True, help="Output CSV: state summary (single year or mean across years)")
    p.add_argument("--year", type=int, default=None, help="If set (e.g., 2022), produce state summary for that year only")
    p.add_argument("--exclude-territories", action="store_true", help="Exclude PR/territories from outputs")
    args = p.parse_args()

    in_path = Path(args.infile)
    out_sy  = Path(args.out_state_year)
    out_s   = Path(args.out_state)
    out_sy.parent.mkdir(parents=True, exist_ok=True)
    out_s.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {in_path}")
    raw = read_wonder(in_path)
    print(f"Rows read: {len(raw):,}")
    norm = normalize(raw)

    colon = filter_colon(norm)
    print(f"Colon & Rectum rows: {len(colon):,}")

    state_year, state_summary = summarize(colon, args.year, args.exclude_territories)

    state_year.to_csv(out_sy, index=False)
    state_summary.to_csv(out_s, index=False)
    print(f"Saved state-year  -> {out_sy}")
    print(f"Saved state-only  -> {out_s}")
    print("\nPreview (state-only):")
    print(state_summary.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
