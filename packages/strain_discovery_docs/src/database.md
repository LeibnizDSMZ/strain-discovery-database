# Database Operations

This document covers MongoDB database operations and collection management.

## Overview

The Strain Discovery Database uses MongoDB to store unified strain data with timestamped collections for historical tracking.

## Collection Naming Convention

Collections are named using the pattern:

```
<MONGO_SDD_COLLECTION>_YYYY_MM_DD_HH_MM
```

### Examples

```
strain_discovery_dataset_2024_01_15_10_30
strain_discovery_dataset_2024_01_16_08_15
strain_discovery_dataset_2024_01_17_14_45
```

### Components

- `strain_discovery_dataset`: Base collection name (from `MONGO_SDD_COLLECTION`)
- `YYYY`: 4-digit year
- `MM`: 2-digit month
- `DD`: 2-digit day
- `HH`: 2-digit hour (24-hour format)
- `MM`: 2-digit minute

## MongoDB Connection

### Connection Parameters

| Parameter | Environment Variable | Default |
|-----------|---------------------|---------|
| Host | `MONGO_HOST` | `localhost` |
| Port | `MONGO_PORT` | `27017` |
| Socket | `MONGO_SOCKET` | `/mongo/mongod.sock` |
| User | `MONGO_SDD_USER` | (required) |
| Password | `MONGO_SDD_PASSWORD` | (required) |
| Database | `MONGO_SDD_DATABASE` | `strain_discovery_database` |
| Collection | `MONGO_SDD_COLLECTION` | `strain_discovery_dataset` |


## Collection Operations

### Creating Timestamped Collections

Timestamped collections are created automatically when running the database creation pipeline:

```bash
docker compose exec app create_database
```

The `create_database` command uses `get_sdd_collection(create=True)` which:
- Creates a new collection with timestamp: `strain_discovery_dataset_YYYY_MM_DD_HH_MM`
- Populates it with matched and deduplicated strains
- Logs the run in `/data/output/logs/<timestamp>/`

## Database Schema

### Strain Document Structure

```jsonc
{
  "_id": ObjectId(...),
  # See: https://github.com/LeibnizDSMZ/microbial-data-standard
}
```

## Troubleshooting

### Connection Issues

```bash
# Check MongoDB service
docker compose ps

# Check logs
docker compose logs mongo
```
