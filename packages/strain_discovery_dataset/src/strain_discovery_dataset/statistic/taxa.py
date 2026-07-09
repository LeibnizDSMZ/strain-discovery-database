from strain_discovery_dataset.utils.venn import calculate_venn_stats
from dataclasses import fields
from pymongo.collection import Collection
from strain_discovery_dataset.utils.data import (
    SOURCE_MAPPING,
    OrganismStatistic,
    Statistics,
)


def _count_org_strain(orga: str, col: Collection, /) -> int:
    return col.count_documents({"organismType": {"$exists": True, "$eq": orga}})


def _create_pipeline(orga: str, src_name: str):
    return [
        {"$match": {"organismType": {"$exists": True, "$eq": orga}}},
        {"$unwind": {"path": "$sources", "includeArrayIndex": "srcIndex"}},
        {"$match": {"sources.name": src_name}},
        {"$group": {"_id": "$primaryId", "count": {"$sum": 1}}},
    ]


def _count_org_src_strain(orga: str, src_name: str, col: Collection, /) -> int:
    pipeline = [*_create_pipeline(orga, src_name), {"$count": "total"}]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _get_src_org(orga: str, src_name: str, col: Collection, /) -> set[str]:
    pipeline = _create_pipeline(orga, src_name)
    result = list(col.aggregate(pipeline))
    return {doc["_id"] for doc in result}


def get_all_taxa_count(con: Statistics, col: Collection, /) -> None:
    source_names = list(SOURCE_MAPPING.values())
    for field in fields(OrganismStatistic):
        org = field.name
        taxa = getattr(con.taxa, org)
        taxa.total = _count_org_strain(org, col)
        for key, src_name in SOURCE_MAPPING.items():
            setattr(taxa, key, _count_org_src_strain(org, src_name, col))
        taxa.venn = calculate_venn_stats(
            source_names, {src: _get_src_org(org, src, col) for src in source_names}
        )
