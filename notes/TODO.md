# TODO

## Production data fixes

- [x] **Repair script written: `scripts/fix_csvs2.py`** (2026-10-24). Removes the index column from the header and old rows, and keeps the newer rows as they are, which lines them up. Safe to run more than once. Tested on copies of the dev CSVs: all 46,665 AQI and 711,016 weather rows kept, matching the DB, and every timestamp parses
  - Root cause: nothing is still writing the index. The header and older rows got it from `scripts/fix_csvs.py` (2026-09-28, `to_csv` without `index=False`). Since about 2026-10-01 `CSVStorage.save()` has appended correct rows with no index, which pandas then read shifted one column left
- [ ] **Apply the repair to the dev CSVs and in production.** Edit `DATA_DIR` in the script, run it, back up each `.csv`, then rename `.new` to `.csv`. In production, do it while the collector isn't running, or rows appended in between are lost
- [ ] **Check production's `daily_forecast.csv`.** If its header starts with a comma (`,city,...`), add a third call for it in `fix_csvs2.py`. There's no CSV copy in dev, only the DB table

## Security

- [x] **Stop logging API keys.** Done 2026-10-23: `_mask_keys()` in `main.py` masks both keys in the debug logging
- [ ] **Clean up keys already in old logs.** The existing log files still contain the full keys from earlier runs: the dev `log/air_quality_monitor.log`, and probably the production logs too. Delete or clean those entries, and rotate the keys if the logs have ever been shared or copied off the machine

## Data collection

- [ ] **Investigate collector reliability.** Each city has an AQI reading for only 72–89% of hours across the history, which leaves gaps in the lag features. Evidence:
  - 2026-10-04 22:00: no reading for any city
  - 2026-10-18 10:00: only Sarajevo has a reading; no collections are logged at 09:00 or 10:00, and they start again at 11:00
  - Bern was collected only once a day (around 15:00) until 2026-10-09, and hourly since
  - Likely causes (my guess): connection errors, or hitting the monthly IQAir API call limit. Check the production logs and the rate-limit record (`data/rate_limit.json`) around those times

## Feature engineering / prediction

- [x] **Filter by time when predicting, to cut memory use.** Done 2026-10-24: `read()` takes an optional `time_filter_col`/`start`/`end` (DB: `.where()` in the query; CSV: chunked read). `build()` passes the windows in prediction mode. Prediction peak memory fell from >2 GB (killed) to ~430 MB; training output unchanged (same row count and SHA-256)
- [ ] **Training (`prepare`) still reads the whole of every table**, so it needs ~2 GB+ and will grow with the data. Options: chunked feature building, or Parquet for the large tables/`training_data.csv`
- [ ] Make rolling features time-based (`.rolling("6h", on="pollutant_timestamp")`) rather than counting rows, because there are gaps between hourly readings
- [ ] Weather trend features are NaN in prediction mode: `we_df` is filtered to the target times, so the horizon-0 rows from 6 and 24 hours earlier aren't available
- [ ] Log the training column list with each model in MLflow (`mlflow.log_dict`) and load it in `Predictor`, instead of the shared `config/training_columns.json`
- [x] Remove the debug `print`s from `features.py` and `predictor.py`, and the hard-coded `as_of` in `Predictor.predict()`
