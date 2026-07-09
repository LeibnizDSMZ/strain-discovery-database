from strain_discovery_dataset.utils.venn import calculate_venn_stats
from dataclasses import fields
from pymongo.collection import Collection
from strain_discovery_dataset.utils.data import SOURCE_MAPPING, FieldStatistic, Statistics


def _count_entries(field: str, col: Collection, /) -> int:
    pipeline = [
        {"$match": {field: {"$exists": True, "$ne": []}}},
        {"$unwind": f"${field}"},
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _get_grouped_entries(field: str, src_name: str):
    return [
        {"$match": {field: {"$exists": True, "$ne": []}}},
        {"$unwind": {"path": "$sources", "includeArrayIndex": "srcIndex"}},
        {"$match": {"sources.name": src_name}},
        {
            "$addFields": {
                "sourcePath": {"$concat": ["/sources/", {"$toString": "$srcIndex"}]}
            }
        },
        {"$unwind": {"path": f"${field}", "includeArrayIndex": "fieldIndex"}},
        {"$unwind": f"${field}.source"},
        {"$match": {"$expr": {"$eq": [f"${field}.source", "$sourcePath"]}}},
        {
            "$group": {
                "_id": {"primaryId": "$primaryId", "fieldIndex": "$fieldIndex"},
                "count": {"$sum": 1},
            }
        },
    ]


def _count_entries_source(field: str, src_name: str, col: Collection, /) -> int:
    pipeline = [*_get_grouped_entries(field, src_name), {"$count": "total"}]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _get_source_entries(field: str, src_name: str, col: Collection, /) -> set[str]:
    pipeline = _get_grouped_entries(field, src_name)
    result = list(col.aggregate(pipeline))
    return {f"{doc['_id']['primaryId']}|{doc['_id']['fieldIndex']}" for doc in result}


def get_all_entries_count(con: Statistics, col: Collection, /) -> None:
    source_names = list(SOURCE_MAPPING.values())
    for field in fields(FieldStatistic):
        field_name = field.name
        entries = getattr(con.strains, field_name).entries

        entries.total = _count_entries(field_name, col)

        for key, src_name in SOURCE_MAPPING.items():
            setattr(entries, key, _count_entries_source(field_name, src_name, col))

        entries.venn = calculate_venn_stats(
            source_names,
            {src: _get_source_entries(field_name, src, col) for src in source_names},
        )
