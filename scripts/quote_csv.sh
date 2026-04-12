#!/bin/bash

for file in we_history_conv.csv; do
    # Generate a new filename for the converted file
    output_file="${file%.csv}_converted.csv"

    # Process the file and write to the new output file
    awk 'BEGIN {FS=OFS=","} {
        for (i=1; i<=NF; i++) {
            # Check if the field is not a number (integer or float, with optional sign)
            if ($i !~ /^[+-]?[0-9]+([.][0-9]+)?$/) {
                $i = "\"" $i "\""
            }
        }
        print
    }' "$file" > "$output_file"
done
