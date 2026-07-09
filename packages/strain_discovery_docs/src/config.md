# Configuration Guide

This document explains the configuration options for the data transformation pipeline.

## Main Config File
- Located at `configs/src/config.toml`.
- Contains credentials, MongoDB connection info, and pipeline options.

## Example

```toml
[dsmz_keycloak]
pw = "pw"
url = "https://sso.dsmz.de/auth/"
user = "user"

[main]
output="tmp"

[mongodb]
pw = "pw"
url = "mongodb://mongodb...."
user = "username"
db = "db_name"
collection = "collection_name"
```

## Security
- Do not commit secrets to version control.
- Use environment variables or secret management for sensitive data.
