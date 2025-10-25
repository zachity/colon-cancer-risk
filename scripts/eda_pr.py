import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(r"..\data\processed\combined_state_summary_2022.csv")


print(df[["obesity_rate","smoking_rate","incidence_rate_adj"]].corr())


plt.figure()
plt.scatter(df["obesity_rate"], df["incidence_rate_adj"])
plt.xlabel("Obesity rate (%)")
plt.ylabel("Age-adjusted colon & rectum incidence (per 100,000)")
plt.title("BRFSS 2022 vs CDC 2022 (by state)")
for _, r in df.iterrows():
    plt.annotate(r["Abbrev"], (r["obesity_rate"], r["incidence_rate_adj"]), fontsize=8)
plt.tight_layout()
plt.show()


plt.figure()
plt.scatter(df["smoking_rate"], df["incidence_rate_adj"])
plt.xlabel("Smoking rate (%)")
plt.ylabel("Age-adjusted colon & rectum incidence (per 100,000)")
plt.title("Smoking vs Incidence (2022)")
for _, r in df.iterrows():
    plt.annotate(r["Abbrev"], (r["smoking_rate"], r["incidence_rate_adj"]), fontsize=8)
plt.tight_layout()
plt.show()
