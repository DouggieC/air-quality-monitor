#!/bin/bash

for file in we_history.csv; do
    output_file="${file%.csv}_fixed.csv"
    awk -F',' 'BEGIN { OFS="," }

    # Header row: insert "timezone" after column 3 (country)
    NR == 1 {
        # Print cols 1-3, inject timezone header, then the rest
        for (i = 1; i <= 3; i++)      printf "%s%s", $i, OFS
        printf "\"timezone\""
        for (i = 4; i <= NF; i++)     printf "%s%s", OFS, $i
        printf "\n"
        next
    }

    # Corrupt rows: insert the correct timezone value after column 3
    NR <= 4529 {
        city = $1
        gsub(/"/, "", city)
        gsub(/\r/, "", city)

        tz = (city == "Bern") ? "\"Europe/Zurich\"" : "\"Europe/" city "\""

        for (i = 1; i <= 3; i++)      printf "%s%s", $i, OFS
        printf "%s", tz
        for (i = 4; i <= NF; i++)     printf "%s%s", OFS, $i
        printf "\n"
        next
    }

    # Rows 4530+: already correct, pass through untouched
    { print }

    ' "$file" > "$output_file"
done
