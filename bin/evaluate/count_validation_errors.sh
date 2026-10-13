#!/bin/bash

# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

LOG_FILE="$1"

if [ $# -eq 0 ] || [ ! -r "$LOG_FILE" ]; then
    echo "Usage: $0 <log_file>"
    exit 1
fi

awk '
/Validation failed/ {
    match($0, /Validation failed ([A-Z0-9]+)/, arr)
    current_id = arr[1]
    in_block = 1
    next
}

/Validation error for BacDive ID/ {
    match($0, /Validation error for BacDive ID ([0-9]+)/, arr)
    current_id = arr[1]
    in_block = 1
    next
}

in_block && /^[0-9]+[[:space:]]+validation/ {
    next
}

in_block && /^[a-zA-Z0-9._]+/ {
    path = $0
    gsub(/^[[:space:]]+/, "", path)

    # Normalize path
    if (path == "organismType") {
        normalized_path = "organismType"
    } else {
        normalized_path = path
        gsub(/[0-9]+/, "*", normalized_path)
    }

    # Read next line for error type
    if ((getline next_line) > 0) {
        if (match(next_line, /type=([a-z_]+)/, arr)) {
            error_type = arr[1]
            key = normalized_path "|" error_type

            # Count total occurrences per pattern
            counts[key]++

            # Track unique IDs per pattern
            if (!seen[key, current_id]++) {
                unique_ids_per_pattern[key]++
            }

            # Track global unique strain IDs (across *all* patterns)
            if (!global_seen[current_id]++) {
                global_unique_count++
            }
        }
    }
    next
}
END {
    # Print per-pattern stats
    for (key in counts) {
        printf "%6d %s (affected strains: %d)\n", counts[key], key, unique_ids_per_pattern[key]
    }

    # Print grand total of unique strains affected by *any* error
    printf "\nTotal unique strains affected by any validation error: %d\n", global_unique_count
}
' "$LOG_FILE" | sort -t' ' -k1 -nr
