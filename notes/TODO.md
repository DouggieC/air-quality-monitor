# TODO

## Production data fixes

- [ ] **One-off prod job in `scripts/` to repair the CSVs**: do again what was done by hand to the dev data on 2026-10-20:
  - Strip the unnamed index column (header begins `,city,...`) from `aqi_history.csv` and `hourly_forecast.csv`
  - Remove rows where the columns have shifted left (a state name in `city`, the country in `state`, etc.)
  - Make it safe to run more than once (skip if no index column is found) and write to a new file or keep a backup before overwriting
  - Notes: `scripts/fix_csvs.py` is an earlier attempt. It has a hard-coded dev `DATA_DIR`, and its `to_csv` calls (lines 109, 136) don't pass `index=False`, so it would bring the bug back
- [ ] **Find what is still writing the index column in production** and fix it at the source. `CSVStorage.save()` has `index=False`, so the cause is somewhere else (an older deployed version? a script?)

## Security

- [ ] **Stop logging API keys.** At `DEBUG` level, `main()` logs `IQAIR_API_KEY` and `OWM_API_KEY` in full (the "Environment variables" block), and with `LOG_TO_FILE` on they also go into the log files. Mask them (e.g. show only the last 4 characters) or drop those lines. If those logs have ever been shared or copied off the machine, rotate the keys

## Data collection

- [ ] **Investigate collector reliability.** Each city has an AQI reading for only 72–89% of hours across the history, which leaves gaps in the lag features. Evidence:
  - 2026-10-04 22:00: no reading for any city
  - 2026-10-18 10:00: only Sarajevo has a reading; no collections are logged at 09:00 or 10:00, and they start again at 11:00
  - Bern was collected only once a day (around 15:00) until 2026-10-09, and hourly since
  - Likely causes (my guess): connection errors, or hitting the monthly IQAir API call limit. Check the production logs and the rate-limit record (`data/rate_limit.json`) around those times

## Feature engineering / prediction

- [ ] **Filter in SQL when predicting, to cut memory use.** `build()` reads whole tables and then filters in pandas. In the dev codespace (8 GB RAM, no swap, about 2 GB free), `predict` was killed ("Terminated") while reading the DB. `hourly_forecast` has 711k rows, loaded through `pd.read_sql` (`storage.py:226`)
  - Give `read()` optional start/end times and use them in the query's `WHERE` clause (`storage.py:217`)
  - Weather when predicting: only `forecast_for` from `as_of` to `as_of + 48h`
  - AQI when predicting: from about `as_of - 72h` to `as_of` (48h longest lag + 24h rolling window, plus some margin)
  - Training passes no start/end and reads everything, as now
  - Matters most in production, especially on a Raspberry Pi (`k8s-dev-pi`). See also the old `memory_problems` branch

- [ ] Make rolling features time-based (`.rolling("6h", on="pollutant_timestamp")`) rather than counting rows, because there are gaps between hourly readings
- [ ] Weather trend features are NaN in prediction mode: `we_df` is filtered to the target times, so the horizon-0 rows from 6 and 24 hours earlier aren't available
- [ ] Log the training column list with each model in MLflow (`mlflow.log_dict`) and load it in `Predictor`, instead of the shared `config/training_columns.json`
- [ ] Remove the debug `print`s from `features.py` and `predictor.py`, and the hard-coded `as_of` in `Predictor.predict()`
