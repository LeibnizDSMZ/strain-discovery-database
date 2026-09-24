# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from saim.taxon_name.private.container import LPSNConf
from saim.taxon_name.manager import TaxonManager
from strain_discovery_dataset.utils.lpsn import create_lpsn_config
from saim.designation.manager import AcronymManager
from strain_discovery_dataset.utils.data import ACR_DB_VERSION
from strain_discovery_dataset.utils.run import create_run_config
from strain_discovery_dataset.utils.data import Memory

_ACR = None


def get_acr_man() -> AcronymManager:
    global _ACR
    if _ACR is None:
        _ACR = AcronymManager(ACR_DB_VERSION)
    return _ACR


def prep_run_memory() -> Memory:
    conf = create_run_config()
    acr = get_acr_man()
    lpsn_conf: LPSNConf = create_lpsn_config()
    tax = TaxonManager(conf.cache, lpsn_conf)
    mem: Memory = {
        "ccnos": {},
        "strains": {},
        "taxa": {},
        "match": {},
        "man": {"acr": acr, "tax": tax},
    }
    return mem
