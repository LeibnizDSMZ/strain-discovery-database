from strain_discovery_dataset.utils.run import get_log_file
from pydantic_extra_types.country import CountryAlpha2
from strain_discovery_dataset.utils.collections import create_collection
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import re
import time
from io import TextIOWrapper
from microbial_strain_data_model.classes.sequence import (
    SequenceType,
    SequenceLevel,
)
from saim.strain_matching.manager import MatchCache
from strain_discovery_dataset.matching.ccno_to_si_id import (
    Memory,
    prep_run,
    run_resolution_async,
    Task,
)
from microbial_strain_data_model.strain import (
    OrganismType,
    Origin,
    Source,
    Strain,
    TypeStrain,
    Sequence,
    Literature,
    TaxonWithSource,
)
from microbial_strain_data_model.classes.country import Country
from microbial_strain_data_model.classes.identifier import (
    IdentifierStrain,
    Identifier,
)
from microbial_strain_data_model.classes.source import (
    CurationMode,
    Date,
    HttpUrl,
    Organization,
    SourceType,
)
from strain_discovery_dataset.matching.ccno_to_si_id import StrainMaxRecord
from saim.strain_matching.match import match_factory
from strain_discovery_dataset.matching.strain_to_saim_id import run_saim_resolution
from strain_discovery_dataset.utils.data import SaimMatchData
from strain_discovery_dataset.utils.seq import get_seq_acc
from strain_discovery_dataset.utils.taxa import parse_org_to_dom
from saim.designation.manager import AcronymManager
from strain_discovery_dataset.utils.data import ACR_DB_VERSION
from saim.shared.data_con.designation import DesignationType


_ACR = AcronymManager(ACR_DB_VERSION)
_CURRENT_DATE = datetime.now()


def make_strain_info_strain(
    str_inf: StrainMaxRecord, organism_type: OrganismType
) -> Strain:
    si_strain = str_inf["strain"]
    si_deposits = str_inf["deposits"]
    strain = Strain(
        version=1,
        primaryId=f"SI-ID {si_strain['siID']!s}",
        organismType=organism_type,
        typeStrain=[
            TypeStrain(
                typeStrain=si_strain.get("typeStrain", ""),
                source=["/sources/0"],
            )
        ],
        taxon=[
            TaxonWithSource(
                name=si_strain.get("taxon", {}).get("name", ""),
                source=["/sources/0"],
            )
        ],
        sources=[
            Source(
                sourceType=SourceType("website"),
                mode=CurationMode("automated"),
                name="StrainInfo",
                url=HttpUrl(
                    f"https://www.straininfo.dsmz.de/strain/{si_strain['siID']!s}"
                ),
                dateRecorded=Date(
                    _CURRENT_DATE.year, _CURRENT_DATE.month, _CURRENT_DATE.day
                ),
                publisher=[
                    Organization(
                        name="DSMZ",
                        legalName="Leibniz-Institut DSMZ - Deutsche Sammlung von Mikroorganismen und Zellkulturen GmbH",
                        identifier=[
                            Identifier(name="ROR", value="https://ror.org/02tyer376")
                        ],
                    )
                ],
            )
        ],
        identifier=[
            IdentifierStrain(
                name="SI-ID",
                value=f"SI-ID {si_strain['siID']}",
                source=["/sources/0"],
            )
        ],
    )
    strain.identifier.extend(
        IdentifierStrain(
            name="CCNO",
            value=dep["designation"],
            source=["/sources/0"],
        )
        for dep in si_deposits
        if dep["status"] != "erroneous"
    )
    strain.identifier.extend(
        IdentifierStrain(
            name="MIRRI ID"
            if DesignationType.mir in list(_ACR.identify_designation_types(des))
            else "Designation",
            value=des,
            source=["/sources/0"],
        )
        for des in si_strain["relation"].get("designation", [])
    )

    seq_type_match: dict[str, SequenceLevel] = {
        "gene": SequenceLevel.gene,
        "genome": SequenceLevel.genome,
        "rrnaop": SequenceLevel.id_sequence,
    }

    strain.sequences = [
        Sequence(
            type=SequenceType.nuc,
            level=styp,
            accessionNumber=get_seq_acc(sequence["accessionNumber"]),
            source=["/sources/0"],
        )
        for sequence in si_strain.get("sequence", [])
        if (styp := seq_type_match.get(sequence["type"], None)) is not None
    ]

    strain.literature = [
        Literature(
            name=literature.get("title"),
            url=(
                HttpUrl(f"https://doi.org/{literature.get('doi')!s}")
                if literature.get("doi")
                else None
            ),
            source=["/sources/0"],
        )
        for literature in si_strain.get("literature", [])
    ]
    strain.collections = [
        create_collection(_ACR, brc, dep["designation"])
        for dep in si_deposits
        if dep["status"] != "erroneous"
        and (ccID := dep.get("cultureCollection", {}).get("ccID")) is not None
        and (brc := _ACR.get_brc_by_id(ccID)) is not None
    ]

    sam_src: str | None = si_strain.get("sample", {}).get("source")
    try:
        sam_con = CountryAlpha2(si_strain.get("sample", {}).get("countryCode", ""))
        country = Country(name=sam_con.short_name, iso_3166_2=sam_con)
    except Exception:
        country = None

    if country is not None or sam_src:
        strain.origin = [
            Origin(source=["/sources/0"], country=country, description=sam_src)
        ]

    return strain


@dataclass(slots=True, frozen=True)
class ResData:
    input: dict[str, Strain]
    resolved: dict[str, Strain]
    unknown: dict[str, Strain]


async def process_resolution_results(
    run_tasks: list[Task],
    memory: Memory,
    data: ResData,
    fmc: TextIOWrapper,
    /,
) -> None:

    start_time = time.time()
    async for result in run_resolution_async(run_tasks, memory):
        print(f"\rRESULT: {result['id']}{' ' * 10}", end="")

        si_strain = result["best_match_si_id"]
        if si_strain is None:
            data.unknown[result["id"]] = data.input[result["id"]]
        else:
            si_id = str(si_strain["strain"]["siID"])
            try:
                if si_id not in data.resolved:
                    strain_info = make_strain_info_strain(
                        si_strain,
                        organism_type=data.input[result["id"]].organismType,
                    )
                    data.resolved[si_id] = strain_info.join(
                        data.input[result["id"]],
                    )
                else:
                    data.resolved[si_id] = data.resolved[si_id].join(
                        data.input[result["id"]],
                    )
            except ValueError as exc:
                print(f"\nFAILED TO MERGE SI-ID {si_id}\n")
                fmc.write(
                    f"\nFAILED TO MERGE SI-ID {si_id} \n "
                    + f"{data.resolved.get(si_id, 'Unknown origin')}\n"
                    + f"\n {data.input[result['id']]} \n {exc!s} \n ---\n"
                )
                data.unknown[result["id"]] = data.input[result["id"]]

        del data.input[result["id"]]
    total_end_time = time.time()
    total_duration = total_end_time - start_time
    print(
        f"\nTotal time to process {len(run_tasks)} results: {total_duration:.4f} seconds"
    )


def process_unresolved_results(
    memory: Memory,
    data: ResData,
    fmc: TextIOWrapper,
    /,
) -> None:
    sources = [
        re.compile(r"^BD-ID.+"),
        re.compile(r"^MIRRI.+"),
        re.compile(r"^.+"),
    ]
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    acr_man = memory["man"]["acr"]
    saim_results: dict[str, list[Strain]] = defaultdict(list)
    matcher, _ = match_factory(SaimMatchData, False, False)(
        acr_man,
        MatchCache(
            culture_ccno={},
            relation_ccno={},
            si_id={},
            si_cu_err=set(),
        ),
    )
    for src in sources:
        for key in list(data.unknown.keys()):
            if src.match(key) is None:
                continue
            strain = data.unknown.pop(key, None)
            if strain is None:
                continue
            run_saim_resolution(memory, matcher, strain, saim_results)

    for saim_id, strains in saim_results.items():
        if len(strains) == 0:
            continue
        if len(strains) == 1:
            data.resolved[strains[0].primaryId] = strains[0]
        else:
            strains[0].primaryId = saim_id
            data.resolved[saim_id] = strains[0]
            for to_merge in strains[1:]:
                try:
                    data.resolved[saim_id] = data.resolved[saim_id].join(to_merge)
                except ValueError as exc:
                    print(f"\nFAILED TO MERGE SAIM {saim_id}\n")
                    fmc.write(
                        f"\nFAILED TO MERGE SAIM {saim_id}\n{to_merge}\n"
                        + f"\n{exc!s} \n ---\n"
                    )
                    data.unknown[to_merge.primaryId] = to_merge
    for key, strain in data.unknown.items():
        data.resolved[key] = strain


async def match_strains_from_queue(
    queue: asyncio.Queue[Strain], sources: int, /
) -> dict[str, Strain]:
    data = ResData(input={}, resolved={}, unknown={})
    none_count = 0
    BATCH_SIZE = 5_000
    tasks: list[Task | None] = [None] * BATCH_SIZE
    ind = 0
    memory = prep_run(None)
    with get_log_file("merge_errors").open("a") as fmc:
        while (strain := await queue.get()) is not None or none_count != sources:
            if strain is None:
                none_count += 1
                continue
            tasks[ind] = {
                "id": strain.primaryId,
                "ccnos": [
                    ccno.value for ccno in strain.identifier if ccno.name == "CCNO"
                ],
                "taxon": strain.taxon[0].name if len(strain.taxon) == 1 else "",
                "domain": parse_org_to_dom(strain.organismType),
            }
            data.input[strain.primaryId] = strain
            ind += 1

            if ind == BATCH_SIZE:
                await process_resolution_results(
                    [task for task in tasks[:ind] if task is not None],
                    memory,
                    data,
                    fmc,
                )
                ind = 0

        if ind > 0:
            await process_resolution_results(
                [task for task in tasks[:ind] if task is not None],
                memory,
                data,
                fmc,
            )
    process_unresolved_results(memory, data, fmc)
    return data.resolved
