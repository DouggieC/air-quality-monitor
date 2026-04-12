#!/bin/bash

for file in we_history.csv; do
    output_file="${file%.csv}_fixed.csv"
    awk -F',' 'BEGIN { OFS="," }

    # Header row: always rebuild with timezone inserted if missing
    NR == 1 {
        if (NF == 24) {
            for (i = 1; i <= 3; i++)  printf "%s%s", $i, OFS
            printf "\"timezone\""
            for (i = 4; i <= NF; i++) printf "%s%s", OFS, $i
            printf "\n"
        } else {
            print  # already has timezone header
        }
        next
    }

    # Data rows: insert timezone if missing (24 cols), else pass through
    {
        if (NF == 24) {
            city = $1
            gsub(/"/, "", city)
            gsub(/\r/, "", city)

            tz = (city == "Bern") ? "\"Europe/Zurich\"" : "\"Europe/" city "\""

            for (i = 1; i <= 3; i++)  printf "%s%s", $i, OFS
            printf "%s", tz
            for (i = 4; i <= NF; i++) printf "%s%s", OFS, $i
            printf "\n"
        } else {
            print  # already 25 cols, leave untouched
        }
    }

    ' "$file" > "$output_file"
done
