# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.matching.memory import get_acr_man
from deepdiff.serialization import json_dumps
from typing import Any
from strain_discovery_dataset.utils.collections import create_collection_dict
from cafi.container.acr_db import AcrDbEntry
from strain_discovery_dataset.utils.collections import get_brc_from_string
from cafi.container.acr_db import CatArgs
from cafi.library.catalogue import create_catalogue_link
from strain_discovery_dataset.utils.seq import get_seq_acc
from microbial_strain_data_model.strain import Strain


def _fix_dsmz_url(source, dsmz_id):
    ana = get_acr_man().identify_ccno(dsmz_id)
    if ana.acr != "DSM":
        return source
    brc_id = get_acr_man().identify_acr(ana.acr)
    if len(brc_id) != 1:
        return source
    brc = get_acr_man().get_brc_by_id(next(iter(brc_id)))
    if brc is None:
        return source
    urls = list(
        create_catalogue_link(
            brc,
            CatArgs(
                acr=ana.acr,
                id=ana.id.full,
                pre=ana.id.pre,
                core=ana.id.core,
                suf=ana.id.suf,
            ),
        )
    )
    if len(urls) == 1:
        source["url"] = urls[0]

    return source


def _fix_collections(strain) -> list[dict[str, Any]]:
    ccno = strain.get("primaryId")
    selected: AcrDbEntry | None = get_brc_from_string(get_acr_man(), ccno, "DSMZ")
    if len(strain.get("collections", [])) != 1 or selected is None:
        return []
    return [create_collection_dict(get_acr_man(), selected, ccno)]


def transform_dsmz(dsmz_data) -> Strain | None:
    ccno: dict[str | tuple[str, str, str, str], tuple[str, str]] = {}
    for des in dsmz_data["identifier"]:
        ana = get_acr_man().identify_ccno(des.get("value", ""))
        if ana.designation == "":
            return None
        if ana.acr == "":
            ccno[ana.designation] = ("Designation", ana.designation)
        else:
            ccno[(ana.acr, ana.id.pre, ana.id.core, ana.id.suf)] = (
                "CCNO",
                ana.designation,
            )
    dsmz_data["identifier"] = [
        {
            "name": nam,
            "value": val,
            "source": ["/sources/0"],
        }
        for nam, val in ccno.values()
    ]
    if len(dsmz_data["identifier"]) == 0:
        print(f"\nNO IDENTIFIERS for {dsmz_data.get('primaryId')}\n")
        return None
    for seq in dsmz_data.get("sequence", []):
        acc = seq.get("accessionNumber")
        if not acc:
            return None
        seq["accessionNumber"] = get_seq_acc(acc)
    for rel in dsmz_data.get("relatedData", []):
        src = rel.get("source")
        if not isinstance(src, list):
            return None
        rel["source"] = "/sources/0"
    dsmz_data["sources"] = [
        _fix_dsmz_url(source, dsmz_data["primaryId"])
        for source in dsmz_data["sources"]
        if source.get("name", "").startswith("DSMZ")
    ]
    dsmz_data["collections"] = _fix_collections(dsmz_data)
    dsmz_data["version"] = 1
    return Strain.model_validate_json(json_dumps(dsmz_data))
