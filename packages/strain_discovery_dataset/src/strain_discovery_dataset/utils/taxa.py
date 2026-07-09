from typing import Final

from saim.taxon_name.manager import TaxonManager
from saim.shared.data_con.taxon import DomainE
from saim.shared.parse.general import pa_int
from saim.shared.data_con.taxon import is_species_or_lower
from saim.taxon_name.private.container import TaxonName as TaxonNameSaim
from strain_discovery_dataset.utils.data import TaxonName
from microbial_strain_data_model.strain import OrganismType

_ORG_MAP: Final[dict[OrganismType, DomainE]] = {
    OrganismType.algae: DomainE.euk,
    OrganismType.fungi: DomainE.euk,
    OrganismType.protist: DomainE.euk,
    OrganismType.archaea: DomainE.arc,
    OrganismType.bacteria: DomainE.bac,
}


def parse_org_to_dom(org: OrganismType, /) -> DomainE:
    return _ORG_MAP.get(org, DomainE.ukn)


def _get_most_value_domain(
    name: str, domain: DomainE, tax: TaxonManager, /
) -> tuple[set[int], set[int]]:
    domains = tax.get_domain(name)
    ind_pos = -1
    ind_max = 0
    for ind, dom in enumerate(domains):
        if dom.domain == DomainE.ukn:
            continue
        if domain != DomainE.ukn and domain != dom.domain:
            continue
        ids = len(dom.lpsn) + len(dom.ncbi)
        if ind_max < ids:
            ind_max = ids
            ind_pos = ind
    if ind_pos == -1 or ind_pos >= len(domains):
        return set(), set()

    return domains[ind_pos].ncbi, domains[ind_pos].lpsn


def _get_lpsn_id(name: str, domain: DomainE, tax: TaxonManager, /) -> int | None:
    _, lpsn_did = _get_most_value_domain(name, domain, tax)
    lpsn_ids = tax.get_lpsn_id(name)
    if (
        len(lpsn_ids) == 1
        or len(lpsn_ids := list(filter(lambda lid: lid in lpsn_did, lpsn_ids))) == 1
    ):
        return lpsn_ids[0]
    return None


def _get_ncbi_id(name: str, domain: DomainE, tax: TaxonManager, /) -> int | None:
    ncbi_did, _ = _get_most_value_domain(name, domain, tax)
    ncbi_ids = tax.get_ncbi_id(name)
    if (
        len(ncbi_ids) == 1
        or len(ncbi_ids := list(filter(lambda nid: nid in ncbi_did, ncbi_ids))) == 1
    ):
        return ncbi_ids[0]
    return None


def _get_ncbi_lpsn(
    name: str,
    tax: TaxonManager,
    ncbi: int | None,
    lpsn: int | None,
    domain: DomainE,
    /,
) -> tuple[int | None, int | None]:
    lpsn_id = lpsn
    if lpsn_id is None:
        lpsn_id = _get_lpsn_id(name, domain, tax)
    ncbi_id = tax.patch_ncbi_id(ncbi)
    if ncbi_id is None:
        ncbi_id = _get_ncbi_id(name, domain, tax)
    return ncbi_id, lpsn_id


def _get_domain(
    name: str,
    tax: TaxonManager,
    ncbi_id: int | None,
    lpsn_id: int | None,
    cur_dom: DomainE = DomainE.ukn,
    /,
) -> DomainE:
    domain = DomainE.ukn
    if len(domains := tax.get_domain(name, pa_int(ncbi_id), pa_int(lpsn_id))) == 1:
        domain = domains[0].domain
    if domain != DomainE.ukn:
        return domain
    return cur_dom


def _get_domain_ncbi_lpsn(
    name_canonical: str,
    ncbi: int | None,
    lpsn: int | None,
    domain: DomainE,
    tax: TaxonManager,
    /,
) -> tuple[int | None, int | None]:
    ncbi_id, lpsn_id = _get_ncbi_lpsn(name_canonical, tax, ncbi, lpsn, domain)
    new_domain = _get_domain(name_canonical, tax, ncbi_id, lpsn_id, domain)
    if new_domain == DomainE.ukn and (ncbi is None or lpsn is None):
        ncbi_n = None if ncbi is None else ncbi_id
        lpsn_n = None if lpsn is None else lpsn_id
        return ncbi_n, lpsn_n
    return ncbi_id, lpsn_id


def create_unique_taxon_con(
    taxon_name: str,
    ncbi: int | None,
    lpsn: int | None,
    domain: DomainE,
    tax: TaxonManager,
    /,
) -> TaxonName:
    buf_nam = taxon_name
    name_canonical = tax.get_patched_name(taxon_name)
    if name_canonical == "":
        name_canonical = buf_nam
    ncbi_id, lpsn_id = _get_domain_ncbi_lpsn(name_canonical, ncbi, lpsn, domain, tax)
    return {"name": name_canonical, "ncbi": ncbi_id, "lpsn": lpsn_id}


def _is_spec_or_lower(tax: TaxonManager, taxa: str, ncbi: int, lpsn: int, /) -> bool:
    for rank in tax.get_rank(taxa, ncbi, lpsn):
        if is_species_or_lower(rank.rank):
            return True
    return False


def compare_taxon_name(
    task_taxon: TaxonName | None,
    task_domain: DomainE,
    strain: TaxonName,
    tax: TaxonManager,
    /,
) -> bool:
    strain_dom = tuple(
        dom.domain
        for dom in tax.get_domain(
            strain["name"],
            pa_int(strain.get("ncbi", None)),
            pa_int(strain.get("lpsn", None)),
        )
    )
    if task_domain != DomainE.ukn and task_domain not in strain_dom:
        return False
    if task_taxon is None:
        return True
    overlap = tax.has_reasonable_taxon_overlap(
        task_taxon["name"],
        [
            TaxonNameSaim(
                name=strain["name"],
                ncbi=pa_int(strain.get("ncbi", None)),
                lpsn=pa_int(strain.get("lpsn", None)),
            )
        ],
    )
    if _is_spec_or_lower(tax, task_taxon["name"], -1, -1) or _is_spec_or_lower(
        tax,
        strain["name"],
        pa_int(strain.get("ncbi", None)),
        pa_int(strain.get("lpsn", None)),
    ):
        return overlap.species
    return overlap.genus
