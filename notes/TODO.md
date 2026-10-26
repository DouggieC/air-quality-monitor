# TODO

## Bigger projects

- [ ] **Website to present the predictions.** Details TBA
- [ ] **Finish the infrastructure: k8s / AWS / IaC.** Details TBA. There's existing work in `k8s/` and `docker/`, and on the remote branches `k8s-dev-pi` and `k8s-docker-dev`

## Production data fixes

- [x] **Repair script written: `scripts/fix_csvs2.py`** (2026-10-24). Removes the index column from the header and old rows, and keeps the newer rows as they are, which lines them up. Safe to run more than once. Tested on copies of the dev CSVs: all 46,665 AQI and 711,016 weather rows kept, matching the DB, and every timestamp parses
  - Root cause: nothing is still writing the index. The header and older rows got it from `scripts/fix_csvs.py` (2026-09-28, `to_csv` without `index=False`). Since about 2026-10-01 `CSVStorage.save()` has appended correct rows with no index, which pandas then read shifted one column left
- [ ] **Apply the repair in production** (dev CSVs done 2026-10-24). Edit `DATA_DIR` in the script, run it, back up each `.csv`, then rename `.new` to `.csv`. In production, do it while the collector isn't running, or rows appended in between are lost
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
- [x] **Cut `prepare` memory.** Done 2026-10-24: the peak (1.9 GB) was temporary Python objects inside `pd.read_sql`, not the DataFrame (172 MB). `DBStorage.read()` now always reads in chunks, with `stream_results=True` so it also streams on PostgreSQL/MySQL. Peak is now ~740 MB; output unchanged (same SHA-256)
- [x] **Training data stored as Parquet.** Done 2026-10-24/25: `prepare` writes `data/training_data.parquet` (~1/16 the size of the CSV, loads ~2x faster); values identical to the old CSV. Parquet exposed that `heat_index` was always empty (as `object`), so it's now dropped from the features (50 columns). Retrained models differ slightly from the old ones (mean diff 0.2–0.8 AQI), most likely because `colsample_bytree` < 1 samples features by column position
- [x] Delete the old `data/training_data.csv` (done 2026-10-25)
- [ ] `heat_index` is never populated: IQAir doesn't send the `"hi"` field (`parser.py:75`). Decide whether to keep collecting it or remove it from the models/DB
- [ ] Make rolling features time-based (`.rolling("6h", on="pollutant_timestamp")`) rather than counting rows, because there are gaps between hourly readings
- [x] **Weather-trend features fixed.** Done 2026-10-26: trends are now looked up in the full weather data (`we_full`, current-conditions rows) in both modes. Prediction: 88/88 NaN → 0; training: ~17% NaN → 2–4%. Retrained
- [ ] Log the training column list with each model in MLflow (`mlflow.log_dict`) and load it in `Predictor`, instead of the shared `config/training_columns.json`
- [x] Remove the debug `print`s from `features.py` and `predictor.py`, and the hard-coded `as_of` in `Predictor.predict()`
