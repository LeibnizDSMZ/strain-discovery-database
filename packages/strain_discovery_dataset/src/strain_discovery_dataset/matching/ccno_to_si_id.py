from strain_discovery_dataset.utils.lpsn import create_lpsn_config
from strain_discovery_dataset.utils.run import create_run_config
import asyncio
import httpx
from typing import (
    AsyncGenerator,
    Final,
    Iterable,
)
from saim.designation.manager import AcronymManager
from saim.taxon_name.manager import TaxonManager
from saim.taxon_name.private.container import LPSNConf
from saim.shared.data_con.taxon import DomainE
from saim.shared.parse.general import pa_int
from strain_discovery_dataset.utils.data import (
    ACR_DB_VERSION,
    Memory,
    Result,
    ResultCCNo,
    StrainMaxRecord,
    Task,
)
from strain_discovery_dataset.utils.fetch import fetch_with_retry
from urllib.parse import quote

from strain_discovery_dataset.utils.taxa import (
    compare_taxon_name,
    create_unique_taxon_con,
)

_BASE_URL: Final[str] = "https://api.straininfo.dsmz.de/v2"
_MAX_BATCH_SIZE: Final[int] = 100


async def _get_strain_ids(
    client: httpx.AsyncClient,
    ccnos: list[str],
    queue: asyncio.Queue[int | None],
    memory: Memory,
    /,
) -> None:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    acr = memory["man"]["acr"]
    for bat in range(0, len(ccnos), _MAX_BATCH_SIZE):
        batch = [
            ccno
            for ccno in ccnos[bat : bat + _MAX_BATCH_SIZE]
            if (des := acr.identify_ccno(ccno)).acr != ""
            and (des.acr, des.id.pre, des.id.core, des.id.suf) not in memory["ccnos"]
        ]
        url = f"{_BASE_URL}/search/strain/cc_no/{quote(','.join(batch), safe='')}"
        ids = await fetch_with_retry(client, url, {}, {})
        if isinstance(ids, list):
            for sid in ids:
                await queue.put(sid)
    await queue.put(None)


async def _request_avg_strain_data(
    client: httpx.AsyncClient, req: list[int], /
) -> list[StrainMaxRecord]:
    url = f"{_BASE_URL}/data/strain/max/{','.join(map(str, req))}"
    data = await fetch_with_retry(client, url, {}, {})
    if isinstance(data, list):
        return data
    print(f"url issues {url}")
    return []


def _add_record_to_memory(records: Iterable[StrainMaxRecord], memory: Memory, /) -> None:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    acr = memory["man"]["acr"]
    for record in records:
        siId = record["strain"]["siID"]
        memory["strains"][siId] = record
        for deposit in record["strain"]["relation"]["deposit"]:
            des = acr.identify_ccno(deposit["designation"])
            cid = (des.acr, des.id.pre, des.id.core, des.id.suf)
            if cid not in memory["ccnos"]:
                memory["ccnos"][cid] = set()
            memory["ccnos"][cid].add(siId)


async def _get_strain_data(
    client: httpx.AsyncClient,
    queue: asyncio.Queue[int | None],
    memory: Memory,
    /,
) -> None:
    buffer: list[int] = []
    while (sid := await queue.get()) is not None:
        buffer.append(sid)
        if len(buffer) >= _MAX_BATCH_SIZE:
            _add_record_to_memory(await _request_avg_strain_data(client, buffer), memory)
            buffer.clear()
    if buffer:
        _add_record_to_memory(await _request_avg_strain_data(client, buffer), memory)


# vote best matching strain


def _vote_on_best_match_strain(
    results: list[ResultCCNo],
    task_taxon: str,
    task_domain: DomainE,
    memory: Memory,
    /,
) -> StrainMaxRecord | None:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    tax = memory["man"]["tax"]
    if len(results) == 0:
        return None
    vote_majority: dict[int, int] = {}
    if task_taxon != "" and (task_taxon, task_domain) not in memory["taxa"]:
        memory["taxa"][(task_taxon, task_domain)] = create_unique_taxon_con(
            task_taxon, None, None, task_domain, tax
        )
    for result in results:
        for si_id, con in result["si_ids"].items():
            strain = con["strain"]
            taxa_strain = strain.get("taxon", None)
            if taxa_strain is None:
                continue
            taxa_id = (
                task_taxon,
                task_domain,
                taxa_strain["name"],
                pa_int(strain.get("ncbi", None)),
                pa_int(strain.get("lpsn", None)),
            )
            if taxa_id not in memory["match"]:
                memory["match"][taxa_id] = compare_taxon_name(
                    memory["taxa"].get((task_taxon, task_domain), None),
                    task_domain,
                    {
                        "name": taxa_strain["name"],
                        "ncbi": pa_int(taxa_strain.get("ncbi", None)),
                        "lpsn": pa_int(taxa_strain.get("lpsn", None)),
                    },
                    tax,
                )
            if not memory["match"][taxa_id]:
                continue
            if si_id not in vote_majority:
                vote_majority[si_id] = 0
            vote_majority[si_id] += 1
    if len(vote_majority) == 0:
        return None
    return memory["strains"].get(max(vote_majority, key=lambda k: vote_majority[k]), None)


# wrap results


def _create_results(tasks: list[Task], memory: Memory, /) -> Iterable[Result]:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    manager = memory["man"]
    for task in tasks:
        result: list[ResultCCNo] = [
            {
                "ccno": ccno,
                "si_ids": {
                    si_id: memory["strains"][si_id]
                    for si_id in memory["ccnos"][cid]
                    if si_id in memory["strains"]
                },
            }
            for ccno in task["ccnos"]
            if (des := manager["acr"].identify_ccno(ccno)).acr != ""
            and (cid := (des.acr, des.id.pre, des.id.core, des.id.suf)) in memory["ccnos"]
            and len(memory["ccnos"][cid]) > 0
        ]
        yield {
            "id": task["id"],
            "best_match_si_id": _vote_on_best_match_strain(
                result, task["taxon"], task["domain"], memory
            ),
            "ccnos": result,
        }


# configure run


def prep_run(memory: Memory | None, /) -> Memory:
    mem: Memory | None = memory
    if mem is None:
        mem = {"ccnos": {}, "strains": {}, "man": None, "taxa": {}, "match": {}}
    if mem["man"] is None:
        print("FINISHED LOADING MANAGER")
        conf = create_run_config()
        acr = AcronymManager(ACR_DB_VERSION)
        lpsn_conf: LPSNConf = create_lpsn_config()
        tax = TaxonManager(conf.cache, lpsn_conf)
        mem["man"] = {"acr": acr, "tax": tax}
    return mem


# runner


async def run_resolution_async(
    tasks: list[Task], memory: Memory, /
) -> AsyncGenerator[Result]:
    strain_queue: asyncio.Queue[int | None] = asyncio.Queue()
    ccnos = [ccno for task in tasks for ccno in task["ccnos"]]
    print(f"Matching started for {len(ccnos)} ccnos")
    async with httpx.AsyncClient(timeout=100) as client:
        reader_task = asyncio.create_task(
            _get_strain_ids(client, ccnos, strain_queue, memory)
        )
        await _get_strain_data(client, strain_queue, memory)
        await reader_task
    for res in _create_results(tasks, memory):
        yield res
