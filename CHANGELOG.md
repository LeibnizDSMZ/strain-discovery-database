<!--
SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH

SPDX-License-Identifier: CC0-1.0
-->

## v0.2.1 (2026-07-17)

### Refactor

- improve documentation and add ai note

## v0.2.0 (2026-07-15)

### Feat

- **deploy**: add sdd_update flag to conditionally initialize database

### Fix

- **create_database**: pass true flag to get_sdd_collection before mongo insert
- **bacdive**: update accession retrieval to use correct INSDC field name
- **bacdive**: update genome sequence key to plural
- **bacdive**: strip non-numeric characters before float conversion
- correct socket connection to mongo
- correct endless loop
- **bacdive**: add length check to row filter

### Refactor

- move from bash to sh
- **mirri**: update pagination logic for mirri data fetching
- sort id instead of creationDate
- **mirri**: remove unused supply form and restriction mapping logic
- change name for docs
- correct docker production deployment

### Perf

- **mirri**: reduce page size to 500

## v0.1.0 (2026-07-09)
