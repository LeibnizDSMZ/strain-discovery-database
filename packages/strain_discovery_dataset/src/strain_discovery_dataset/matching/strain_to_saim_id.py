from typing import Iterable, MutableSequence, Sequence

from microbial_strain_data_model.strain import (
    OrganismType,
    Strain,
)
from requests_cache import Callable
from collections import deque
from strain_discovery_dataset.utils.data import Memory, SaimMatchData
from saim.strain_matching.private.container import CulMatCon, ErrCon
from saim.strain_matching.manager import UpdateResults
from strain_discovery_dataset.utils.taxa import (
    compare_taxon_name,
    create_unique_taxon_con,
    parse_org_to_dom,
)
from saim.shared.parse.general import pa_int

type _MatchStrain = Callable[[Iterable[str]], set[int]]
type _Matcher = Callable[
    [SaimMatchData, Callable[[CulMatCon[SaimMatchData]], UpdateResults]],
    ErrCon[SaimMatchData] | None,
]

_SAIM = {
    "saim_id": 1,
    "saim_dep_id": 1,
    "saim_pre": "SAIM-ID",
}


def _update_match(mat: CulMatCon[SaimMatchData], saim_id: int, /) -> UpdateResults:
    saim_dep = mat.culture_id
    if saim_dep < 1:
        saim_dep = _SAIM["saim_dep_id"]
        _SAIM["saim_dep_id"] += 1
        return UpdateResults(
            si_id=saim_id,
            si_cu=saim_dep,
            used_in_update=True,
            cid=(
                mat.cul.brc_id,
                mat.cul.id.pre,
                mat.cul.id.core,
                mat.cul.id.suf,
            ),
        )
    return UpdateResults(si_id=saim_id, si_cu=saim_dep, used_in_update=False)


def _gather_match(
    mat: CulMatCon[SaimMatchData], queue: MutableSequence[int], /
) -> UpdateResults:
    saim_id = mat.strain_id
    if saim_id > 0:
        queue.append(saim_id)
    return UpdateResults(si_id=1, si_cu=1, used_in_update=False)


def _create_new_saim_id() -> int:
    nid = _SAIM["saim_id"]
    _SAIM["saim_id"] += 1
    return nid


def _to_saim_id(sid: int, /) -> str:
    return f"{_SAIM['saim_pre']} {sid}"


def _vote_saim_id(
    matchedIds: Sequence[int],
    taxon: str,
    org_type: OrganismType,
    strains: dict[str, list[Strain]],
    memory: Memory,
    /,
) -> int:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    tax = memory["man"]["tax"]
    if len(matchedIds) == 0:
        return _create_new_saim_id()
    vote_majority: dict[int, int] = {}
    domain = parse_org_to_dom(org_type)
    if taxon != "" and (taxon, domain) not in memory["taxa"]:
        memory["taxa"][(taxon, domain)] = create_unique_taxon_con(
            taxon, None, None, domain, tax
        )
    for pid in matchedIds:
        saim_id = _to_saim_id(pid)
        for strain in strains.get(saim_id, []):
            taxa_strain = strain.taxon[0].name if len(strain.taxon) > 0 else ""
            if taxa_strain == "" or org_type != strain.organismType:
                continue
            com_domain = parse_org_to_dom(strain.organismType)
            if (taxa_strain, com_domain) not in memory["taxa"]:
                memory["taxa"][(taxa_strain, com_domain)] = create_unique_taxon_con(
                    taxa_strain, None, None, com_domain, tax
                )
            com_taxa = memory["taxa"][(taxa_strain, com_domain)]
            taxa_id = (
                taxon,
                domain,
                com_taxa["name"],
                pa_int(com_taxa.get("ncbi", None)),
                pa_int(com_taxa.get("lpsn", None)),
            )
            if taxa_id not in memory["match"]:
                memory["match"][taxa_id] = compare_taxon_name(
                    memory["taxa"].get((taxon, domain), None),
                    domain,
                    com_taxa,
                    tax,
                )
            if not memory["match"][taxa_id]:
                continue
            if pid not in vote_majority:
                vote_majority[pid] = 0
            vote_majority[pid] += 1
    if len(vote_majority) == 0:
        return _create_new_saim_id()
    return max(vote_majority, key=lambda k: vote_majority[k])


def run_saim_resolution(
    memory: Memory,
    matcher: _Matcher,
    strain: Strain,
    strains: dict[str, list[Strain]],
) -> None:
    if memory["man"] is None:
        raise Exception("Manager not initialized in memory")
    acr_man = memory["man"]["acr"]
    tasks = [
        SaimMatchData(
            acr=ccno.acr,
            ccno=ccno.designation,
            brc_id=next(iter(brc_id)),
            id=ccno.id,
        )
        for des in strain.identifier
        if (ccno := acr_man.identify_ccno(des.value)).acr != ""
        and len(brc_id := acr_man.identify_acr(ccno.acr)) == 1
    ]
    matched_ids = deque()
    for to_match in tasks:
        matcher(to_match, lambda mat: _gather_match(mat, matched_ids))
    voted_id = _vote_saim_id(
        matched_ids,
        strain.taxon[0].name if len(strain.taxon) > 0 else "",
        strain.organismType,
        strains,
        memory,
    )
    strains[_to_saim_id(voted_id)].append(strain)
    for to_match in tasks:
        matcher(to_match, lambda mat: _update_match(mat, voted_id))
