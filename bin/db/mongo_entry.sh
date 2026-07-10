#!/bin/bash

# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

rm -f /socket/*

sed "/^net:/,/^[^[:space:]]/ s/^\([[:space:]]*port:\)[[:space:]]*[0-9]\+/\1 $MONGO_PORT/" "$INIT_MONGO_CONFIG" > /tmp/mongod.conf.new
cat /tmp/mongod.conf.new > "$INIT_MONGO_CONFIG"
rm /tmp/mongod.conf.new

python3 /usr/local/bin/docker-entrypoint.py --config "$INIT_MONGO_CONFIG"  &

while [ ! -e "/socket/mongodb-$MONGO_PORT.sock" ]; do
    sleep 1
done

chown mongodb:mongodb "/socket/mongodb-$MONGO_PORT.sock"
sleep infinity
