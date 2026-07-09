#!/bin/bash

set -euo pipefail

echo "Initializing database"
echo "This process may currently require up to 2 days"
echo "However, with complete caches, it typically completes in approximately 11 hours"

create_database

echo "FINISHED"
echo "To view statistics, you can run create_statistics"
sleep infinity
