from pymongo.collection import Collection
from strain_discovery_dataset.utils.data import SOURCE_MATCH_MAPPING, Statistics


def _count_si_all(col: Collection, /) -> int:
    pipeline = [
        {"$unwind": "$sources"},
        {"$match": {"sources.name": "StrainInfo"}},
        {"$group": {"_id": "$primaryId", "count": {"$sum": 1}}},
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _count_si_src(src_name: str, col: Collection, /) -> int:
    pipeline = [
        {
            "$match": {
                "$and": [{"sources.name": "StrainInfo"}, {"sources.name": src_name}]
            }
        },
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _count_saim_src(src_name: str, col: Collection, /) -> int:
    pipeline = [
        {"$match": {"primaryId": {"$regex": "^SAIM"}}},
        {"$match": {"sources.name": src_name}},
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _count_saim(col: Collection, /) -> int:
    pipeline = [{"$match": {"primaryId": {"$regex": "^SAIM"}}}, {"$count": "total"}]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _count_unmatched_all(col: Collection, /) -> int:
    pipeline = [
        {
            "$match": {
                "$nor": [
                    {"primaryId": {"$regex": "^SAIM"}},
                    {"sources.name": "StrainInfo"},
                ]
            }
        },
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def _count_unmatched_all_src(src_name: str, col: Collection, /) -> int:
    pipeline = [
        {
            "$match": {
                "$nor": [
                    {"primaryId": {"$regex": "^SAIM"}},
                    {"sources.name": "StrainInfo"},
                ]
            }
        },
        {"$match": {"sources.name": src_name}},
        {"$count": "total"},
    ]
    result = list(col.aggregate(pipeline))
    return result[0]["total"] if result else 0


def get_all_match_count(con: Statistics, col: Collection, /) -> None:
    con.match.strainInfo.total = _count_si_all(col)
    for key, src_name in SOURCE_MATCH_MAPPING.items():
        setattr(con.match.strainInfo, key, _count_si_src(src_name, col))
    con.match.saim.total = _count_saim(col)
    for key, src_name in SOURCE_MATCH_MAPPING.items():
        setattr(con.match.saim, key, _count_saim_src(src_name, col))
    con.match.unmatched.total = _count_unmatched_all(col)
    for key, src_name in SOURCE_MATCH_MAPPING.items():
        setattr(con.match.unmatched, key, _count_unmatched_all_src(src_name, col))
