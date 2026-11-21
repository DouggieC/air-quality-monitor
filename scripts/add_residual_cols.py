import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path("/home/doug/apps/air-quality-monitor")
DATA_DIR = Path(BASE_DIR / "data")
DB_FILE = Path(DATA_DIR / "air_quality_monitor.db")
CSV_FILE = Path(DATA_DIR / "predictions.csv")

print("Starting DB migration")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("Getting current list of columns in prediction table")
cursor.execute("PRAGMA table_info(prediction)")
existing_cols = {row[1] for row in cursor.fetchall()}
print(f"existing_cols: {existing_cols}")

if "actual_aqi" not in existing_cols:
    print("Adding column actual_aqi")
    cursor.execute("ALTER TABLE prediction ADD COLUMN actual_aqi INTEGER")
if "residual" not in existing_cols:
    print("Adding column residual")
    cursor.execute("ALTER TABLE prediction ADD COLUMN residual INTEGER")

print("Committing DB changes")
conn.commit()
conn.close()

print("Finished DB migration")

print("Starting CSV migration")
print("Getting current list of columns in predictions.csv")
df = pd.read_csv(CSV_FILE)
modified = False

if "actual_aqi" not in df.columns:
    print("Adding column actual_aqi")
    df["actual_aqi"] = None
    modified = True
if "residual" not in df.columns:
    print("Adding column residual")
    df["residual"] = None
    modified = True

if modified:
    print("Saving changes")
    df.to_csv(CSV_FILE, index=False)
else:
    print("Columns already exist - no changes made")

print("Finished CSV migration")
