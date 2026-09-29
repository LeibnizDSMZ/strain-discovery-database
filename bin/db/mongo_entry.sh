#!/bin/bash

# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

rm -f /socket/*

python3 /usr/local/bin/docker-entrypoint.py --config "$INIT_MONGO_CONFIG"  &

while [ ! -e "/socket/mongodb-27017.sock" ]; do
    sleep 1
done

chown mongodb:mongodb "/socket/mongodb-27017.sock"
sleep infinity
