# Data Model

This document describes the data model used for microbial strain data in the pipeline.

## Strain Object

- Unified representation of microbial strains from BacDive, MIRRI, and DSMZ.
- Fields include: strain ID, taxonomy, source, metadata, and more.

## Transformation Logic

- Each source module transforms raw data into the unified Strain object.
- See `bacdive/transformation_bacdive.py` and `mirri/transformation_mirri.py` for details.

## Example

```json
{
  "strain_id": "...",
  "taxonomy": { ... },
  "source": "bacdive",
  "metadata": { ... }
}
```
