# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.utils.venn import calculate_venn_stats
from pymongo.collection import Collection
from strain_discovery_dataset.utils.data import SOURCE_MAPPING, Statistics


def _create_pipeline(src_name: str, /):
    return [
        {"$match": {"literature": {"$exists": True, "$ne": []}}},
        {"$unwind": "$literature"},
        {"$unwind": {"path": "$sources", "includeArrayIndex": "srcIndex"}},
        {"$match": {"sources.name": src_name}},
        {
            "$addFields": {
                "sourcePath": {"$concat": ["/sources/", {"$toString": "$srcIndex"}]}
            }
        },
        {"$unwind": "$literature"},
        {"$unwind": "$literature.source"},
        {"$match": {"$expr": {"$eq": ["$literature.source", "$sourcePath"]}}},
        {"$group": {"_id": "$literature.url", "count": {"$sum": 1}}},
    ]


def _count_lit_src(src_name: str, col: Collection, /) -> int:
    pipeline = [*_create_pipeline(src_name), {"$count": "total"}]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _get_src_lit(src_name: str, col: Collection, /) -> set[str]:
    pipeline = _create_pipeline(src_name)
    result = list(col.aggregate(pipeline))
    return {doc["_id"] for doc in result}


def _count_lit_all(col: Collection, /) -> int:
    pipeline = [
        {"$match": {"literature": {"$exists": True, "$ne": []}}},
        {"$unwind": "$literature"},
        {"$group": {"_id": "$literature.url", "count": {"$sum": 1}}},
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def get_all_literature_count(con: Statistics, col: Collection, /) -> None:
    source_names = list(SOURCE_MAPPING.values())
    for key, src_name in SOURCE_MAPPING.items():
        setattr(con.literature, key, _count_lit_src(src_name, col))
    con.literature.total = _count_lit_all(col)
    con.literature.venn = calculate_venn_stats(
        source_names, {src: _get_src_lit(src, col) for src in source_names}
    )
