from strain_discovery_dataset.utils.venn import calculate_venn_stats
from dataclasses import fields
from pymongo.collection import Collection
from strain_discovery_dataset.utils.data import SOURCE_MAPPING, FieldStatistic, Statistics


def _count_non_empty(field: str, col: Collection, /) -> int:
    return col.count_documents({field: {"$exists": True, "$ne": []}})


def _create_pipeline(field: str, src_name: str):
    return [
        {"$unwind": {"path": "$sources", "includeArrayIndex": "index"}},
        {"$match": {"sources.name": src_name}},
        {
            "$addFields": {
                "sourcePath": {"$concat": ["/sources/", {"$toString": "$index"}]}
            }
        },
        {"$unwind": f"${field}"},
        {"$unwind": f"${field}.source"},
        {"$match": {"$expr": {"$eq": [f"${field}.source", "$sourcePath"]}}},
        {"$group": {"_id": "$primaryId", "count": {"$sum": 1}}},
    ]


def _get_src_non_empty(field: str, src_name: str, col: Collection, /) -> set[str]:
    pipeline = _create_pipeline(field, src_name)
    result = list(col.aggregate(pipeline))
    return {doc["_id"] for doc in result}


def _count_non_empty_source(field: str, src_name: str, col: Collection, /) -> int:
    pipeline = [*_create_pipeline(field, src_name), {"$count": "total"}]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def get_all_strains_count(con: Statistics, col: Collection, /) -> None:
    con.total = col.count_documents({})

    source_names = list(SOURCE_MAPPING.values())
    for field in fields(FieldStatistic):
        field_name = field.name
        not_empty = getattr(con.strains, field_name).notEmpty
        not_empty.total = _count_non_empty(field_name, col)
        for key, src_name in SOURCE_MAPPING.items():
            setattr(not_empty, key, _count_non_empty_source(field_name, src_name, col))
        not_empty.venn = calculate_venn_stats(
            source_names,
            {src: _get_src_non_empty(field_name, src, col) for src in source_names},
        )
