# TODO

## Production data fixes

- [ ] **One-off prod job in `scripts/` to repair the CSVs**: do again what was done by hand to the dev data on 2026-10-20:
  - Strip the unnamed index column (header begins `,city,...`) from `aqi_history.csv` and `hourly_forecast.csv`
  - Remove rows where the columns have shifted left (a state name in `city`, the country in `state`, etc.)
  - Make it safe to run more than once (skip if no index column is found) and write to a new file or keep a backup before overwriting
  - Notes: `scripts/fix_csvs.py` is an earlier attempt. It has a hard-coded dev `DATA_DIR`, and its `to_csv` calls (lines 109, 136) don't pass `index=False`, so it would bring the bug back
- [ ] ~~Find what is still writing the index column~~ **Root cause found (2026-10-24): nothing is still writing it.** The header and older rows have an index column, probably from `scripts/fix_csvs.py` (2026-09-28, `to_csv` without `index=False`). Since about 2026-10-01, `CSVStorage.save()` has been appending correct rows with no index, so they have one column fewer than the header, and pandas reads them shifted one column left (state names in `city`). In the dev copy: `aqi_history.csv` 3,703 bad rows (7.9%) from row 42,962; `hourly_forecast.csv` 242,976 bad (34.2%) from row 468,040. **Fix:** the repair job above must handle *both* row formats (old rows with an index, new rows without): drop the index from the old ones and keep the new ones as they are, not delete them. After that, new writes will line up. Check whether production has the same problem

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
