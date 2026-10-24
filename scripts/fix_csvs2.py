import csv
from pathlib import Path

print("Fixing CSVs")

DATA_DIR = "/workspaces/air-quality-monitor/data"
AQI_IN_FILE = Path(DATA_DIR) / "aqi_history.csv"
AQI_OUT_FILE = Path(DATA_DIR) / "aqi_history.new"
WE_IN_FILE = Path(DATA_DIR) / "hourly_forecast.csv"
WE_OUT_FILE = Path(DATA_DIR) / "hourly_forecast.new"

def _fix_columns(infile, outfile):
    with open(infile, "r", newline="") as in_f:
        reader = csv.reader(in_f)
        # Check the file is actually broken by checking header[0] is blank.
        # Return if the column is not empty. Otherwise, drop it and carry on fixing
        header = next(reader)
        if header[0] != "":
            print("File is not broken. Exiting.")
            return False

        with open(outfile, "w", newline="") as out_f:
            writer = csv.writer(out_f, lineterminator="\n")
    
            header = header[1:]
            writer.writerow(header)

            for row in reader:
                if len(row) == len(header):
                    # It's right. No change needed
                    writer.writerow(row)
                elif len(row) == len(header) + 1:
                    # Need to drop the first column
                    row = row[1:]
                    writer.writerow(row)
                else:
                    outfile.unlink()
                    raise ValueError(f"Incorrect number of columns in row {reader.line_num}, file {infile}")
    return True

def main():
    print("Fixing AQI data")
    if _fix_columns(AQI_IN_FILE, AQI_OUT_FILE):
        print("AQI file fixed successfully")
    else:
        print("No fix required for AQI data")

    print("Fixing weather data")
    if _fix_columns(WE_IN_FILE, WE_OUT_FILE):
        print("Weather file fixed successfully")
    else:
        print("No fix required for weather data")

if __name__ == "__main__":
    main()
