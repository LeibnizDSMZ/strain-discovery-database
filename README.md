<!--
SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH

SPDX-License-Identifier: CC0-1.0
-->

[![release: 0.2.1](https://img.shields.io/badge/rel-0.2.1-blue.svg?style=flat-square)](https://github.com/LeibnizDSMZ/strain-discovery-database)
[![MIT LICENSE](https://img.shields.io/badge/License-MIT-brightgreen.svg?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Documentation Status](https://img.shields.io/badge/docs-GitHub-blue.svg?style=flat-square)](https://LeibnizDSMZ.github.io/strain-discovery-database/)

[![main](https://github.com/LeibnizDSMZ/strain-discovery-database/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/LeibnizDSMZ/strain-discovery-database/actions/workflows/main.yml)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21375664.svg)](https://doi.org/10.5281/zenodo.21375664)

---

# Strain Discovery Database

## Overview

This project provides a robust pipeline for fetching, transforming, matching, and storing microbial strain data from multiple sources (**BacDive**, **MIRRI**, **DSMZ**) into a unified format. The processed data is loaded into **MongoDB** for research, data integration, and bioinformatics applications.

> **⚠️ HARDWARE WARNING**  
> ---
> This pipeline is memory-intensive. It is **strongly recommended** to run this on a machine with at least **32GB of RAM**. Running on insufficient memory may cause the container to crash during data processing.

## Features

- 🌐 **Multi-Source Ingestion:** Fetches data from BacDive, MIRRI, and DSMZ.
- 🧹 **Data Standardization:** Cleans and normalizes data using source-specific transformation modules.
- 🔗 **Strain Matching:** Identifies and links matching strains across different sources.
- 🗄️ **MongoDB Storage:** Stores processed, unified data in a NoSQL database.
- 📝 **Logging:** Logging and error tracking for pipeline monitoring.
- 📊 **Statistics:** Generates statistics for strain data analysis.

## Prerequisites

- **Docker** & **Docker Compose** installed
- **RAM:** Minimum 32GB recommended
- **Disk Space:** Docker images ~3 GB total (`mongo` ~1.3 GB, `app` ~1.7 GB); MongoDB database < 1 GB
- **LPSN API Account**: Required for taxonomic name validation and LPSN ID resolution
  - See the [LPSN API Registration Guide](https://LeibnizDSMZ.github.io/strain-discovery-database/lpsn_guide) for configuration details

> ✏️ **Note**:
> Both RAM and disk space requirements scale heavily with strain count and strain content depth.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd strain-discovery-database
   ```

2. **Initialize Configuration:**
   Copy the example environment file to create your local configuration.
   ```bash
   cp package.env .env
   ```

3. **Configure Secrets:**
   Open the `.env` file and fill in the required credentials. **Do not commit this file to version control.**
   ```bash
   nano .env
   # OR
   vim .env
   ```

## Usage

### 1. Start the Pipeline

Run the Docker Compose stack. This will build the images and start the data ingestion process.
If you want to avoid restarting the database creation process, set `SDD_UPDATE=false` in the `.env` file.

```bash
docker compose up --build
```

**Note on Collection Naming:**

Collections are named with timestamps: `<MONGO_SDD_COLLECTION>_YYYY_MM_DD_HH_MM`
This allows you to identify and select specific runs by their creation time.

### 2. Access the Database

Once the pipeline initialization is complete, you can access the database:

**Option A: Access via Container Shell**
1. Find the running container name - `<container_name>`:
   ```bash
   docker compose ps
   ```
2. Execute a bash shell inside the container:
   ```bash
   docker exec -it <container_name> bash
   ```

**Option B: Access via External Client (Compass, CLI, etc.)**
You can connect to the MongoDB instance from your host machine using the exposed port.
- **Host:** `localhost`
- **Port:** `27372` (or as defined in `MONGO_PORT`)
- **Username:** `<MONGO_SDD_USER>`
- **Password:** `<MONGO_SDD_PASSWORD>`

### 3. Running Statistics

The pipeline generates statistics about the processed strain data. Statistics are computed from the selected database collection and stored in timestamped output directories.

**Running Statistics in Docker:**

Once the database is populated, you can run `create_statistics`. The statistics are computed from database collection defined by `MONGO_SDD_COLLECTION`.

```bash
docker compose exec app MONGO_SDD_COLLECTION=<MONGO_SDD_COLLECTION>_YYYY_MM_DD_HH_MM create_statistics
```

This will export results to `/data/output/<timestamp>/` within the container as CSV files.


**Inspecting Statistics:**

To view the generated statistics:

```bash
docker compose exec app ls /data/output/

docker compose exec app cat /data/output/<timestamp>/taxa.csv
```

-----

> ✏️ **Note**:
> This project uses AI tools for code generation, review, and documentation.
> All AI-generated content is human-reviewed.
