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
- Configurable via TOML files
- Logging and error tracking

## Installation

1. Clone the repository:
	```bash
	git clone <repo-url>
	cd transformation
	```
2. Set up a Python virtual environment (recommended):
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	```
3. Install dependencies:
	```bash
	pip install -e .
	```

## Configuration

Edit the TOML files in `configs/` to set up credentials, MongoDB connection, and other options. See `docs/config.md` for details.

## Usage

Run the main pipeline:
```bash
python packages/strain_discovery_dataset/src/strain_discovery_dataset/create_database.py
```
