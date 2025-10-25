import pandas as pd
import statsmodels.api as sm

df = pd.read_csv(r"..\data\processed\combined_state_summary_2022.csv")

X = df[["obesity_rate","smoking_rate"]]
X = sm.add_constant(X)
y = df["incidence_rate_adj"]

model = sm.OLS(y, X).fit()
print(model.summary())
