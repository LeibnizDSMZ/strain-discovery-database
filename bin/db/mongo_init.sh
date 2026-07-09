#!/bin/bash

set -eu

USER_ARRAY=(
  "$MONGO_SDD_USER"
)

PASS_ARRAY=(
  "$(tr -d '\n' < "$MONGO_SDD_PASSWORD_FILE")"
)

req_db=(
  "$MONGO_SDD_DATABASE"
)

for var in "${USER_ARRAY[@]}" "${PASS_ARRAY[@]}" "${req_db[@]}"; do
    if [ -z "$var" ]; then
        echo "Error: Environment variable $var is not set or empty"
        exit 1
    fi
done

if [[ ${#USER_ARRAY[@]} -ne ${#PASS_ARRAY[@]} ]]; then
  echo "ERROR: Number of usernames and passwords does not match." >&2
  exit 1
fi

DB_ARRAY=(
  "$MONGO_SDD_DATABASE:$MONGO_SDD_USER:w"
)

mongosh -u "$MONGODB_INITDB_ROOT_USERNAME" -p "$MONGODB_INITDB_ROOT_PASSWORD" --port "$MONGO_PORT" <<EOF
$(

for db_entry in "${DB_ARRAY[@]}"; do
  IFS=':' read -r db_name user perm <<< "$db_entry"

  if [[ "$perm" = "w" ]]; then
    role="readWrite"
  elif [[ "$perm" = "r" ]]; then
    role="read"
  else
    echo "Invalid permission '$perm' for database '$db_name'. Skipping." >&2
    continue
  fi

  password=""
  for ind in "${!USER_ARRAY[@]}"; do
    if [[ "${USER_ARRAY[$ind]}" = "$user" ]]; then
      password="${PASS_ARRAY[$ind]}"
      break
    fi
  done

  if [[ "$password" = "" ]]; then
    echo "No password found for user '$user'. Skipping." >&2
    continue
  fi

  printf "use %s\ndb.createUser({user:'%s',pwd:'%s',roles:[{role:'%s',db:'%s'}]})\n" \
    "$db_name" "$user" "$password" "$role" "$db_name"

done

)

EOF
