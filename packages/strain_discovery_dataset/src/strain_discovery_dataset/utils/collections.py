# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Literal
from pydantic import HttpUrl
from typing import Any
from microbial_strain_data_model.strain import Collection
from microbial_strain_data_model.classes.identifier import Identifier
from cafi.container.acr_db import AcrDbEntry
from saim.designation.manager import AcronymManager
from cafi.container.acr_db import CatArgs
from cafi.library.catalogue import create_catalogue_link
from typing import overload


@overload
def _create_catalogue_url(
    acr_man: AcronymManager, brc: AcrDbEntry, ccno: str, as_string: Literal[False] = False
) -> HttpUrl | None: ...


@overload
def _create_catalogue_url(
    acr_man: AcronymManager, brc: AcrDbEntry, ccno: str, as_string: Literal[True]
) -> str | None: ...


def _create_catalogue_url(
    acr_man: AcronymManager, brc: AcrDbEntry, ccno: str, as_string: bool = False
) -> HttpUrl | str | None:
    ana = acr_man.identify_ccno(ccno)
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
    if len(urls) != 1:
        return None
    if as_string:
        return urls[0]
    return HttpUrl(urls[0])


def get_brc_from_string(
    acr_man: AcronymManager, ccno: str, verify: str | None, /
) -> AcrDbEntry | None:
    for brc in [
        ele
        for acr in set(des.acr for des in acr_man.identify_ccno_all_valid(ccno))
        for brc_id in acr_man.identify_acr(acr)
        if (ele := acr_man.get_brc_by_id(brc_id)) is not None
    ]:
        if verify is None:
            return brc
        aut = verify.lower()
        if (
            brc.code.lower() in aut
            or brc.acr.lower() in aut
            or any(acr.lower() in aut for acr in brc.acr_synonym)
        ):
            return brc
    return None


def create_collection(
    acr_man: AcronymManager, brc: AcrDbEntry, ccno: str, /
) -> Collection:
    return Collection(
        name=brc.name,
        url=brc.homepage,
        identifier=[Identifier(name="ROR", value=brc.ror)] if brc.ror != "" else [],
        resourceNumber=ccno,
        catalogUrl=_create_catalogue_url(acr_man, brc, ccno),
        source=["/sources/0"],
    )


def create_collection_dict(
    acr_man: AcronymManager, brc: AcrDbEntry, ccno: str, /
) -> dict[str, Any]:
    return {
        "name": brc.name,
        "url": brc.homepage if brc.homepage is None else brc.homepage.encoded_string(),
        "identifier": [{"name": "ROR", "value": brc.ror}] if brc.ror != "" else [],
        "resourceNumber": ccno,
        "catalogUrl": _create_catalogue_url(acr_man, brc, ccno, True),
        "source": ["/sources/0"],
    }
