#!/bin/bash

# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

# Check if file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <log_file>"
    exit 1
fi

LOG_FILE="$1"

# Check if file exists and is readable
if [ ! -f "$LOG_FILE" ] || [ ! -r "$LOG_FILE" ]; then
    echo "Error: Cannot read file '$LOG_FILE'"
    exit 1
fi

# Process the log file with awk
awk '
/^(Validation error for BacDive ID|Validation failed)/ {
    in_block = 1
    next
}

in_block && /^[0-9]+[[:space:]]+validation/ {
    next
}

in_block && /^[a-zA-Z0-9._]+/ {
    path = $0
    gsub(/^[[:space:]]+/, "", path)  # trim leading spaces

    if (path == "organismType") {
        normalized_path = "organismType"
    } else {
        gsub(/[0-9]+/, "*", path)  # replace numbers with *
        normalized_path = path
    }

    # Read next line for error type
    if ((getline next_line) > 0) {
        if (match(next_line, /type=([a-z_]+)/, arr)) {
            print normalized_path "|" arr[1]
        }
    }
    next
}
' "$LOG_FILE" | sort | uniq -c | sort -nr
