# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.utils.run import create_run_config
from strain_discovery_dataset.utils.mongo import get_sdd_collection
from strain_discovery_dataset.utils.data import SOURCE_MAPPING
from strain_discovery_dataset.utils.venn import create_venn_headers
from pathlib import Path
from dataclasses import fields
import csv
from strain_discovery_dataset.statistic.field import get_all_entries_count
from strain_discovery_dataset.statistic.matched import get_all_match_count
from strain_discovery_dataset.statistic.literature import get_all_literature_count
from strain_discovery_dataset.statistic.sequences import get_all_sequences_count
from strain_discovery_dataset.statistic.strain import get_all_strains_count
from strain_discovery_dataset.statistic.taxa import get_all_taxa_count
from strain_discovery_dataset.utils.data import Statistics


def _export_non_empty_to_csv(stats: Statistics, out_dir: Path) -> None:
    with out_dir.joinpath("non_empty_strains.csv").open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        venn_keys = create_venn_headers(list(SOURCE_MAPPING.values()))
        header = [
            "Field",
            "BacDive",
            "MIRRI",
            "DSMZ",
            "StrainInfo",
            "Total",
            "Coverage",
            *venn_keys,
        ]
        writer.writerow(header)

        for field in fields(stats.strains):
            field_name = field.name
            field_data = getattr(stats.strains, field_name)

            writer.writerow(
                [
                    field_name,
                    field_data.notEmpty.BacDive,
                    field_data.notEmpty.MIRRI,
                    field_data.notEmpty.DSMZ,
                    field_data.notEmpty.StrainInfo,
                    field_data.notEmpty.total,
                    float(field_data.notEmpty.total) / float(stats.total) * 100,
                    *[field_data.notEmpty.venn.get(key, 0) for key in venn_keys],
                ]
            )


def _export_taxa_to_csv(stats: Statistics, out_dir: Path) -> None:
    with out_dir.joinpath("taxa.csv").open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        venn_keys = create_venn_headers(list(SOURCE_MAPPING.values()))
        header = [
            "Organism",
            "BacDive",
            "MIRRI",
            "DSMZ",
            "StrainInfo",
            "Total",
            *venn_keys,
        ]
        writer.writerow(header)

        for field in fields(stats.taxa):
            field_name = field.name
            field_data = getattr(stats.taxa, field_name)

            writer.writerow(
                [
                    field_name,
                    field_data.BacDive,
                    field_data.MIRRI,
                    field_data.DSMZ,
                    field_data.StrainInfo,
                    field_data.total,
                    *[field_data.venn.get(key, 0) for key in venn_keys],
                ]
            )


def _export_seq_lit_to_csv(stats: Statistics, out_dir: Path) -> None:
    with out_dir.joinpath("sequences_literature.csv").open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        venn_keys = create_venn_headers(list(SOURCE_MAPPING.values()))
        header = ["Field", "BacDive", "MIRRI", "DSMZ", "StrainInfo", "Total", *venn_keys]
        writer.writerow(header)

        for field_name in ["sequences", "literature"]:
            field_data = getattr(stats, field_name)
            writer.writerow(
                [
                    field_name,
                    field_data.BacDive,
                    field_data.MIRRI,
                    field_data.DSMZ,
                    field_data.StrainInfo,
                    field_data.total,
                    *[field_data.venn.get(key, 0) for key in venn_keys],
                ]
            )


def _export_match_to_csv(stats: Statistics, out_dir: Path) -> None:
    with out_dir.joinpath("match.csv").open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        header = ["Field", "BacDive", "MIRRI", "DSMZ", "AllStrainsField", "AllStrains"]
        writer.writerow(header)

        for field_name in ["strainInfo", "saim", "unmatched"]:
            field_data = getattr(stats.match, field_name)
            writer.writerow(
                [
                    field_name,
                    field_data.BacDive,
                    field_data.MIRRI,
                    field_data.DSMZ,
                    field_data.total,
                    stats.total,
                ]
            )


def _export_entries_to_csv(stats: Statistics, out_dir: Path) -> None:
    with out_dir.joinpath("strain_entries.csv").open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        venn_keys = create_venn_headers(list(SOURCE_MAPPING.values()))
        header = ["Field", "BacDive", "MIRRI", "DSMZ", "StrainInfo", "Total", *venn_keys]
        writer.writerow(header)

        for field in fields(stats.strains):
            field_name = field.name
            field_data = getattr(stats.strains, field_name)

            writer.writerow(
                [
                    field_name,
                    field_data.entries.BacDive,
                    field_data.entries.MIRRI,
                    field_data.entries.DSMZ,
                    field_data.entries.StrainInfo,
                    field_data.entries.total,
                    *[field_data.entries.venn.get(key, 0) for key in venn_keys],
                ]
            )


def main():
    mongo_collection = get_sdd_collection()
    stats_container = Statistics()
    get_all_match_count(stats_container, mongo_collection)
    get_all_sequences_count(stats_container, mongo_collection)
    get_all_literature_count(stats_container, mongo_collection)
    get_all_taxa_count(stats_container, mongo_collection)
    get_all_strains_count(stats_container, mongo_collection)
    get_all_entries_count(stats_container, mongo_collection)

    output = create_run_config().output

    _export_non_empty_to_csv(stats_container, output)
    _export_entries_to_csv(stats_container, output)
    _export_taxa_to_csv(stats_container, output)
    _export_seq_lit_to_csv(stats_container, output)
    _export_match_to_csv(stats_container, output)
    print("FINISHED")


if __name__ == "__main__":
    main()
