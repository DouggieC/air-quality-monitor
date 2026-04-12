import pandas as pd
import numpy as np
import json

#pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)

df = pd.read_csv("data/old/we_history.csv")

#print(df)
#print(df.info())

# Drop obsolete columns
df_new = df.drop(["timezone", "timezone_offset", "dt_local", "sunrise_local", "sunset_local"], axis=1)
#print(df_new)
#print(df_new.info())

df_new.rename(columns={"dt_utc": "dt", "sunrise_utc": "sunrise", "sunset_utc": "sunset"}, inplace=True)
#print(df_new)
#print(df_new.info())

df_new["collected_at"] = df_new["collected_at"].fillna(df_new["dt"])
#df_filled = df_new.collected_at.fillna(df_new.dt)
print(df_new)
print(df_new.info())

df_new.to_csv("data/we_history_conv.csv", index=False)
