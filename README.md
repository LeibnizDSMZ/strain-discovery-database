<!--
SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH

SPDX-License-Identifier: CC0-1.0
-->

[![release: 0.1.0](https://img.shields.io/badge/rel-0.1.0-blue.svg?style=flat-square)](https://github.com/LeibnizDSMZ/strain-discovery-database)
[![MIT LICENSE](https://img.shields.io/badge/License-MIT-brightgreen.svg?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Documentation Status](https://img.shields.io/badge/docs-GitHub-blue.svg?style=flat-square)](https://LeibnizDSMZ.github.io/strain-discovery-database/)


# Strain Discovery Database

## Overview

This project provides a robust pipeline for fetching, transforming, matching, and storing microbial strain data from multiple sources (**BacDive**, **MIRRI**, **DSMZ**) into a unified format. The processed data is loaded into **MongoDB** for research, data integration, and bioinformatics applications.

> **⚠️ HARDWARE WARNING**  
> This pipeline is memory-intensive. It is **strongly recommended** to run this on a machine with at least **32GB of RAM**. Running on insufficient memory may cause the container to crash during data processing.

## Features

- 🌐 **Multi-Source Ingestion:** Fetches data from BacDive, MIRRI, and DSMZ.
- 🧹 **Data Standardization:** Cleans and normalizes data using source-specific transformation modules.
- 🔗 **Strain Matching:** Identifies and links matching strains across different sources.
- 🗄️ **MongoDB Storage:** Stores processed, unified data in a NoSQL database.
- 📝 **Logging:** Comprehensive logging and error tracking for pipeline monitoring.

## Prerequisites

- **Docker** & **Docker Compose** installed
- **RAM:** Minimum 32GB recommended (depends on data volume)
- **Disk Space:** Sufficient space for database storage (depends on data volume)

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
   *Required variables:* `LPSN_USER`, `LPSN_PASSWORD`, `MONGO_SDD_PASSWORD`, etc.

## Usage

### 1. Start the Pipeline

Run the Docker Compose stack. This will build the images (if necessary) and start the data ingestion process.

```bash
docker compose up --build
```

*Note: If you configured your `.env` file correctly, you do not need to pass passwords via command line arguments.*

### 2. Access the Database

Once the pipeline initialization is complete, the MongoDB service will be running.

**Option A: Access via Container Shell**
1. Find the running container name:
   ```bash
   docker compose ps
   ```
2. Execute a bash shell inside the container (replace `<container_name>` with the actual name, e.g., `strain-discovery-database-1`):
   ```bash
   docker exec -it <container_name> bash
   ```

**Option B: Access via External Client (Compass, CLI, etc.)**
You can connect to the MongoDB instance from your host machine using the exposed port.
- **Host:** `localhost`
- **Port:** `27372` (or as defined in `MONGO_PORT`)
- **Username:** `<MONGO_SDD_USER>`
- **Password:** `<MONGO_SDD_PASSWORD>`
