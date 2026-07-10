<!--
SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH

SPDX-License-Identifier: CC0-1.0
-->

[![release: 0.1.0](https://img.shields.io/badge/rel-0.1.0-blue.svg?style=flat-square)](https://github.com/LeibnizDSMZ/strain-discovery-database)
[![MIT LICENSE](https://img.shields.io/badge/License-MIT-brightgreen.svg?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Documentation Status](https://img.shields.io/badge/docs-GitHub-blue.svg?style=flat-square)](https://LeibnizDSMZ.github.io/strain-discovery-database/)


# Strain Discovery Database

## Overview

This project provides a robust pipeline for fetching, transforming, matching, and storing microbial strain data from multiple sources (BacDive, MIRRI, DSMZ) into a unified format and loading it into MongoDB. It is designed for research, data integration, and bioinformatics applications.

## Features

- Fetches data from BacDive, MIRRI, and DSMZ
- Cleans and standardizes data using source-specific transformation modules
- Matches strains across sources
- Stores processed data in MongoDB
- Logging and error tracking

## Installation

1. Clone the repository:
	```bash
	git clone <repo-url>
	cd strain-discovery-database
	```
2. Create core config .env:
	```bash
	cat package.env > .env
	```

## Usage

1. Run the main pipeline:
	```bash
	LPSN_PASSWORD=password \
	LPSN_USER=user@mail.local \
	MONGO_SDD_PASSWORD=password \
    docker compose up
	```
2. When the database creation is finished:
	```bash
    docker exec -it strain-discovery-database-1 bash
	```

3. The MongoDB can be reached via MONGO_PORT (default: 27372)
