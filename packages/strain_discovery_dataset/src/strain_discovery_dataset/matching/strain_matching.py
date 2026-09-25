# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from saim.designation.manager import AcronymManager
from strain_discovery_dataset.utils.data import ResultSAIM
from strain_discovery_dataset.utils.data import SaimStrain
from strain_discovery_dataset.utils.data import ResultSI
from collections.abc import Iterable
from pydantic_extra_types.country import CountryAlpha2
from strain_discovery_dataset.utils.collections import create_collection
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import time
from microbial_strain_data_model.classes.sequence import (
    SequenceType,
    SequenceLevel,
)
from saim.strain_matching.manager import MatchCache
from strain_discovery_dataset.matching.ccno_to_si_id import (
    Memory,
    run_resolution_async,
    Task,
)
from collections.abc import Sequence as SequenceT
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
from saim.shared.data_con.designation import DesignationType


_CURRENT_DATE = datetime.now()


def make_strain_info_strain(
    str_inf: StrainMaxRecord, organism_type: OrganismType, acr_man: AcronymManager, /
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
            if DesignationType.mir in list(acr_man.identify_designation_types(des))
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
        create_collection(acr_man, brc, dep["designation"])
        for dep in si_deposits
        if dep["status"] != "erroneous"
        and (ccID := dep.get("cultureCollection", {}).get("ccID")) is not None
        and (brc := acr_man.get_brc_by_id(ccID)) is not None
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


def process_resolution_results(
    run_tasks: SequenceT[Task],
    memory: Memory,
    contact: str,
    /,
) -> Iterable[ResultSI]:
    start_time = time.time()
    for result in asyncio.run(run_resolution_async(run_tasks, memory, contact)):
        print(f"\rRESULT: {result['id']}{' ' * 20}", end="")

        si_strain = result["best_match_si_id"]
        output = {"source": result["source"], "matched": None, "origin": result["strain"]}
        if si_strain is not None:
            output["matched"] = make_strain_info_strain(
                si_strain, result["strain"].organismType, memory["man"]["acr"]
            )
        yield output
    total_end_time = time.time()
    total_duration = total_end_time - start_time
    print(
        f"\nTotal time to process {len(run_tasks)} results: {total_duration:.4f} seconds"
    )


def process_unresolved_results(
    memory: Memory,
    data: Iterable[tuple[str, Strain]],
    /,
) -> Iterable[ResultSAIM]:
    # Order of strains is not guaranteed, thus can lead to different results each run
    acr_man = memory["man"]["acr"]
    matcher, _ = match_factory(SaimMatchData, False, False)(
        acr_man,
        MatchCache(
            culture_ccno={},
            relation_ccno={},
            si_id={},
            si_cu_err=set(),
        ),
    )
    saim_cache: dict[str, list[SaimStrain]] = defaultdict(list)
    for source, strain in data:
        if strain.primaryId == "":
            continue
        yield {
            "source": source,
            "saim": run_saim_resolution(memory, matcher, strain, saim_cache),
            "origin": strain,
        }
