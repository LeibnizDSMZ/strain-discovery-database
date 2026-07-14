#!/bin/sh

# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

set -eu

USER_LIST="$MONGO_SDD_USER"
PASS_LIST=$(tr -d '\n\r' < "$MONGO_SDD_PASSWORD_FILE")
REQ_DB_LIST="$MONGO_SDD_DATABASE"

for var_name in $USER_LIST $PASS_LIST $REQ_DB_LIST; do
  if [ -z "$var_name" ]; then
    echo "Error: One of the required variables is not set or empty"
    exit 1
  fi
done

user_count=0
for _ in $USER_LIST; do user_count=$((user_count + 1)); done

pass_count=0
for _ in $PASS_LIST; do pass_count=$((pass_count + 1)); done

if [ "$user_count" -ne "$pass_count" ]; then
  echo "ERROR: Number of usernames and passwords does not match." >&2
  exit 1
fi

DB_LIST="$MONGO_SDD_DATABASE:$MONGO_SDD_USER:w"

MONGO_SCRIPT=""
db_entry=""

eval set -- "$DB_LIST"
db_index=0

while [ "$db_index" -lt "$#" ]; do
  eval db_entry="\$$((db_index + 1))"

  db_name=$(echo "$db_entry" | cut -d':' -f1)
  user=$(echo "$db_entry" | cut -d':' -f2)
  perm=$(echo "$db_entry" | cut -d':' -f3)

  role=""
  if [ "$perm" = "w" ]; then
    role="readWrite"
  elif [ "$perm" = "r" ]; then
    role="read"
  else
    echo "Invalid permission '$perm' for database '$db_name'. Skipping." >&2
    db_index=$((db_index + 1))
    continue
  fi

  password=""
  user_idx=0

  eval set -- "$USER_LIST"
  for u in "$@"; do
    if [ "$u" = "$user" ]; then
      p_idx=0
      for p in $PASS_LIST; do
        if [ "$p_idx" -eq "$user_idx" ]; then
          password="$p"
          break
        fi
        p_idx=$((p_idx + 1))
      done
      break
    fi
    user_idx=$((user_idx + 1))
  done

  if [ -z "$password" ]; then
    echo "No password found for user '$user'. Skipping." >&2
    db_index=$((db_index + 1))
    continue
  fi

  MONGO_SCRIPT="$MONGO_SCRIPT$(printf "use %s\ntry {\n  db.createUser({user:'%s',pwd:'%s',roles:[{role:'%s',db:'%s'}]})\n} catch(e) {\n  if (e.code == 51003) {\n    db.updateUser('%s', {pwd:'%s',roles:[{role:'%s',db:'%s'}]})\n  } else {\n    throw e\n  }\n}\n" \
    "$db_name" "$user" "$password" "$role" "$db_name" "$user" "$password" "$role" "$db_name")"

  db_index=$((db_index + 1))
done

echo "$MONGO_SCRIPT" | mongosh -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --port "$MONGO_PORT"
