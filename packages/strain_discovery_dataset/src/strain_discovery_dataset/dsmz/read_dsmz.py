from typing import Any
from strain_discovery_dataset.utils.collections import (
    create_collection_dict,
    get_brc_from_string,
)
from strain_discovery_dataset.utils.data import ACR_DB_VERSION
from saim.designation.manager import AcronymManager
import httpx
from strain_discovery_dataset.utils.fetch import fetch_with_retry
from strain_discovery_dataset.utils.seq import get_seq_acc
from cafi.container.acr_db import CatArgs
from cafi.library.catalogue import create_catalogue_link
from cafi.container.acr_db import AcrDbEntry

URL = "https://api.strains.dsmz.de/strains"

_ACR = AcronymManager(ACR_DB_VERSION)


def _fix_dsmz_url(source, dsmz_id):
    ana = _ACR.identify_ccno(dsmz_id)
    if ana.acr != "DSM":
        return source
    brc_id = _ACR.identify_acr(ana.acr)
    if len(brc_id) != 1:
        return source
    brc = _ACR.get_brc_by_id(next(iter(brc_id)))
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
    selected: AcrDbEntry | None = get_brc_from_string(_ACR, ccno, "DSMZ")
    if len(strain.get("collections", [])) != 1 or selected is None:
        return []
    return [create_collection_dict(_ACR, selected, ccno)]


async def dsmz_get_all():
    page = 0
    page_size = 1000
    total_count = 1
    async with httpx.AsyncClient(timeout=100) as client:
        while page * page_size < total_count:
            page += 1
            data = await fetch_with_retry(
                client, f"{URL}/?page={page}&page_size={page_size}", {}, {}
            )
            if isinstance(data, dict):
                total_count = data.get("meta", {}).get("totalCount", 0)
                for strain in data.get("data", []):
                    print(f"\r{strain.get('primaryId')}{' ' * 10}", end="")
                    ccno: dict[str | tuple[str, str, str, str], tuple[str, str]] = {}
                    for des in strain["identifier"]:
                        ana = _ACR.identify_ccno(des.get("value", ""))
                        if ana.designation == "":
                            continue
                        if ana.acr == "":
                            ccno[ana.designation] = ("Designation", ana.designation)
                        else:
                            ccno[(ana.acr, ana.id.pre, ana.id.core, ana.id.suf)] = (
                                "CCNO",
                                ana.designation,
                            )
                    strain["identifier"] = [
                        {
                            "name": nam,
                            "value": val,
                            "source": ["/sources/0"],
                        }
                        for nam, val in ccno.values()
                    ]
                    if len(strain["identifier"]) == 0:
                        print(f"\nNO IDENTIFIERS for {strain.get('primaryId')}\n")
                        continue
                    for seq in strain.get("sequence", []):
                        acc = seq.get("accessionNumber")
                        if not acc:
                            continue
                        seq["accessionNumber"] = get_seq_acc(acc)
                    for rel in strain.get("relatedData", []):
                        src = rel.get("source")
                        if not isinstance(src, list):
                            continue
                        rel["source"] = "/sources/0"
                    strain["sources"] = [
                        _fix_dsmz_url(source, strain["primaryId"])
                        for source in strain["sources"]
                        if source.get("name", "").startswith("DSMZ")
                    ]
                    strain["collections"] = _fix_collections(strain)
                    strain["version"] = 1
                    yield strain
            else:
                yield None
