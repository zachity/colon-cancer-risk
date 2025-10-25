import pandas as pd
from pathlib import Path

BRFSS = Path("..")/"data"/"processed"/"brfss2022_state_summary.csv"
CDC   = Path("..")/"data"/"processed"/"cdc_colon_state_summary_2022.csv"
OUT   = Path("..")/"data"/"processed"/"combined_state_summary_2022.csv"

brf = pd.read_csv(BRFSS)
cdc = pd.read_csv(CDC)

valid = set([
 "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY",
 "LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH",
 "OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
])
brf = brf[brf["Abbrev"].isin(valid)].copy()


merged = brf.merge(
    cdc[["Abbrev","age_adjusted_rate","total_cases"]],
    on="Abbrev", how="inner", validate="one_to_one"
)


merged = merged.rename(columns={
    "age_adjusted_rate": "incidence_rate_adj",
    "total_cases": "incidence_cases"
})


print("Rows in merged:", len(merged))
print(merged.head(10).to_string(index=False))

OUT.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUT, index=False)
print("Saved:", OUT)
