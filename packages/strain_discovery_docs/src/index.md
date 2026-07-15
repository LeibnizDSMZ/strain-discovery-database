# The StrainDiscoveryDatabase (SDD)

## An open framework for standardized, large-scale microbial strain data

The vast amount of microbial strain data available today holds immense potential for bioindustrial applications, large-scale comparative genomics, and Artificial Intelligence (AI). However, the discovery of microbial strains is often hindered by fragmented data silos and the widespread use of synonymous strain identifiers across different culture collections.

The **StrainDiscoveryDatabase (SDD)** is built to overcome these bottlenecks. It is a comprehensive, machine-readable dataset encompassing over **6.3 million harmonized data points** for **256,900 microbial strains** across Bacteria, Archaea, Fungi, and Algae.

The SDD is utilizing the [Microbial Strain Data Standard](https://leibnizdsmz.github.io/microbial-data-standard/) and is part of the work of WP6 of the [Bioindustry 4.0](https://www.bioindustry4.eu/) project.

---

## Key Features

- **Dynamic Data Aggregation**: The SDD does not rely on a static, isolated repository. Instead, it systematically retrieves up-to-date phenotypic, genotypic, and contextual data on the fly via public APIs from highly curated databases, including BacDive, MIRRI-IS, and the DSMZ catalogue.

- **Deduplication**: A single microbial strain is frequently deposited in multiple collections under different names. By leveraging the {StrainInfo database API](https://straininfo.dsmz.de/service) and the [SAIM](https://github.com/LeibnizDSMZ/saim/) (Strain Authentication and Identification Methods) library, the SDD accurately resolves synonymous strain identifiers, deduplicates records, and merges disparate knowledge into a single biological entity.

- **Highly Standardized Output**: All aggregated data is structured into a unified JSON format utilizing the [Microbial Strain Data Standard](https://leibnizdsmz.github.io/microbial-data-standard/) to ensure strict adherence to **FAIR** (Findable, Accessible, Interoperable, and Reusable) data principles.

---

## Why use the SDD?

By bridging isolated database silos and linking distributed knowledge, the SDD provides a high-quality, foundational architecture for researchers and industry professionals. It is designed to accelerate:

- Trait-based strain discovery
- Large-scale comparative analysis
- Machine learning and AI predictions for microbial traits

---

## Getting Started with the Code

To start using or building upon the SDD framework, researchers can clone the [Strain Discovery Database repository](https://leibnizdsmz.github.io/strain-discovery-database/). The repository provides the complete, open-source Python pipeline used to fetch, transform, and match the data from the source APIs.

You can run the pipeline out-of-the-box to recreate the full, up-to-date dataset locally, or you can extend the scripts to integrate your own specialized tools, in-house datasets, and additional web services.

Because the entire framework is built around the [Microbial Strain Data Standard](https://leibnizdsmz.github.io/microbial-data-standard/), integrating new data sources into your bioinformatics or machine learning workflows is highly streamlined.

---

> **Note**: This project is a product of the Horizon Europe project [Bioindustry 4.0](https://www.bioindustry4.eu/) and supported by the [NFDI4Microbiota consortium](https://nfdi4microbiota.de/).
