# Statistics Generation

This document describes the statistics generation process for the Strain Discovery Database.

## Overview

Statistics generation provides insights into the dataset composition, data quality, and source coverage.

## Running Statistics

### Basic Command

```bash
docker compose exec app MONGO_SDD_COLLECTION=<MONGO_SDD_COLLECTION>_YYYY_MM_DD_HH_MM create_statistics
```

### Environment Variables

- `MONGO_SDD_COLLECTION`: Collection to analyze
- Output directory: `/data/output/<timestamp>/`

### Example Output

```bash
docker compose exec app ls /data/output/

docker compose exec app cat /data/output/<timestamp>/taxa.csv
```

## Generated Statistics

### 1. Non-Empty Strains (`non_empty_strains.csv`)

Shows field coverage across strains.

| Field | BacDive | MIRRI | DSMZ | StrainInfo | Total | Coverage | Venn Regions |
|-------|---------|-------|------|------------|-------|----------|--------------|
| legal | 0 | 149501 | 33110 | 0 | 176276 | 67.81 | ... |
| typeStrain | 98271 | 3695 | 33110 | 132444 | 181231 | 69.72 | ... |

**Columns:**
- `Field`: Name of the field
- `BacDive`: Count of strains with data from BacDive
- `MIRRI`: Count of strains with data from MIRRI
- `DSMZ`: Count of strains with data from DSMZ
- `StrainInfo`: Count of strains with data from StrainInfo
- `Total`: Total number of strains with non-empty field
- `Coverage`: Percentage of strains with non-empty field
- `Venn Regions`: Strain counts for each source combination region

### 2. Strain Entries (`strain_entries.csv`)

Counts entries per field across sources.

| Field | BacDive | MIRRI | DSMZ | StrainInfo | Total | Venn Regions |
|-------|---------|-------|------|------------|-------|--------------|
| legal | 0 | 153753 | 33110 | 0 | 186863 | ... |
| identifier | 336146 | 573964 | 106093 | 544166 | 1118152 | ... |

**Columns:**
- `Field`: Name of the field
- `BacDive`: Count of entries from BacDive
- `MIRRI`: Count of entries from MIRRI
- `DSMZ`: Count of entries from DSMZ
- `StrainInfo`: Count of entries from StrainInfo
- `Total`: Total number of entries
- `Venn Regions`: Entry counts for each source combination region

### 3. Taxa (`taxa.csv`)

Taxonomic distribution of strains.

| Organism | BacDive | MIRRI | DSMZ | StrainInfo | Total | Venn Regions |
|----------|---------|-------|------|------------|-------|--------------|
| Algae | 0 | 1769 | 0 | 561 | 1769 | ... |
| Bacteria | 97136 | 45513 | 29532 | 75661 | 136166 | ... |

**Columns:**
- `Organism`: Taxonomic name (e.g., Algae, Bacteria)
- `BacDive`: Count of strains from BacDive
- `MIRRI`: Count of strains from MIRRI
- `DSMZ`: Count of strains from DSMZ
- `StrainInfo`: Count of strains from StrainInfo
- `Total`: Total count of strains
- `Venn Regions`: Strain counts for each source combination region

### 4. Sequences & Literature (`sequences_literature.csv`)

Sequence and publication data coverage.

| Field | BacDive | MIRRI | DSMZ | StrainInfo | Total | Venn Regions |
|-------|---------|-------|------|------------|-------|--------------|
| sequences | 68673 | 12749 | 20456 | 97010 | 151424 | ... |
| literature | 222065 | 1747 | 0 | 30587 | 230878 | ... |

**Columns:**
- `Field`: Type of data (sequences or literature)
- `BacDive`: Count of entries from BacDive
- `MIRRI`: Count of entries from MIRRI
- `DSMZ`: Count of entries from DSMZ
- `StrainInfo`: Count of entries from StrainInfo
- `Total`: Total count of entries
- `Venn Regions`: Entry counts for each source combination region

### 5. Match Statistics (`match.csv`)

Matching results summary.

| Field | BacDive | MIRRI | DSMZ | AllStrainsField | AllStrains |
|-------|---------|-------|------|-----------------|------------|
| strainInfo | 52373 | 85911 | 29871 | 132444 | 259942 |
| saim | 1593 | 1762 | 1239 | 2862 | 259942 |
| unmatched | 44305 | 78331 | 2000 | 124636 | 259942 |

**Columns:**
- `Field`: Match status (strainInfo, saim, unmatched)
- `BacDive`: Count of matches from BacDive
- `MIRRI`: Count of matches from MIRRI
- `DSMZ`: Count of matches from DSMZ
- `AllStrainsField`: Count of strains matching the field
- `AllStrains`: Total count of strains in the collection
