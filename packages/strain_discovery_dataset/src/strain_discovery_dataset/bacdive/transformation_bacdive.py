# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT
from strain_discovery_dataset.utils.run import get_log_file
from requests_cache import Iterable

from strain_discovery_dataset.utils.collections import (
    create_collection_dict,
    get_brc_from_string,
)
from strain_discovery_dataset.utils.seq import get_seq_length
import json
from cafi.container.acr_db import AcrDbEntry
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any
from pydantic import HttpUrl
from pydantic_core import ValidationError
from saim.designation.manager import AcronymManager
from saim.shared.parse.date import get_date
from microbial_strain_data_model.strain import Strain
from microbial_strain_data_model.classes.enums import ConcentrationUnit
from strain_discovery_dataset.utils.data import ACR_DB_VERSION
from strain_discovery_dataset.utils.seq import get_seq_acc
from deepdiff import DeepHash

_SEP = re.compile(r"[,;]+")
_CAT = re.compile(r"^Curators of.+$")
_ACR = AcronymManager(ACR_DB_VERSION)
_CURRENT_DATE = datetime.now()
_GROWTH = ["growth", "maximum", "minimum", "optimum"]
_COLONY_COLORS = [
    "white",
    "cream",
    "yellowish",
    "orange",
    "pink",
    "red",
    "buff",
    "darkbrown",
    "reyish",
    "tannish",
    "beige",
    "brownish",
]

_ISO_MAPPING = {
    "AFG": "AF",
    "ALA": "AX",
    "ALB": "AL",
    "DZA": "DZ",
    "ASM": "AS",
    "AND": "AD",
    "AGO": "AO",
    "AIA": "AI",
    "ATA": "AQ",
    "ATG": "AG",
    "ARG": "AR",
    "ARM": "AM",
    "ABW": "AW",
    "AUS": "AU",
    "AUT": "AT",
    "AZE": "AZ",
    "BHS": "BS",
    "BHR": "BH",
    "BGD": "BD",
    "BRB": "BB",
    "BLR": "BY",
    "BEL": "BE",
    "BLZ": "BZ",
    "BEN": "BJ",
    "BMU": "BM",
    "BTN": "BT",
    "BOL": "BO",
    "BES": "BQ",
    "BIH": "BA",
    "BWA": "BW",
    "BVT": "BV",
    "BRA": "BR",
    "BA1": "B1",
    "IOT": "IO",
    "VGB": "VG",
    "BRN": "BN",
    "BGR": "BG",
    "BFA": "BF",
    "BDI": "BI",
    "CPV": "CV",
    "KHM": "KH",
    "CMR": "CM",
    "CAN": "CA",
    "CYM": "KY",
    "CAF": "CF",
    "TCD": "TD",
    "CHL": "CL",
    "CHN": "CN",
    "CXR": "CX",
    "CCK": "CC",
    "COL": "CO",
    "COM": "KM",
    "COG": "CG",
    "COK": "CK",
    "CRI": "CR",
    "CIV": "CI",
    "HRV": "HR",
    "CUB": "CU",
    "CUW": "CW",
    "CYP": "CY",
    "CZE": "CZ",
    "DNK": "DK",
    "DJI": "DJ",
    "DMA": "DM",
    "DOM": "DO",
    "COD": "CD",
    "ECU": "EC",
    "EGY": "EG",
    "SLV": "SV",
    "GNQ": "GQ",
    "ERI": "ER",
    "EST": "EE",
    "SWZ": "SZ",
    "ETH": "ET",
    "FRO": "FO",
    "FLK": "FK",
    "FJI": "FJ",
    "FIN": "FI",
    "FRA": "FR",
    "GUF": "GF",
    "PYF": "PF",
    "ATF": "TF",
    "GAB": "GA",
    "GMB": "GM",
    "GEO": "GE",
    "DEU": "DE",
    "GHA": "GH",
    "GIB": "GI",
    "GRC": "GR",
    "GRL": "GL",
    "GRD": "GD",
    "GLP": "GP",
    "GUM": "GU",
    "GTM": "GT",
    "GGY": "GG",
    "GIN": "GN",
    "GNB": "GW",
    "GUY": "GY",
    "HTI": "HT",
    "HMD": "HM",
    "HND": "HN",
    "HKG": "HK",
    "HUN": "HU",
    "ISL": "IS",
    "IND": "IN",
    "IDN": "ID",
    "IRN": "IR",
    "IRQ": "IQ",
    "IRL": "IE",
    "IMN": "IM",
    "ISR": "IL",
    "ITA": "IT",
    "JAM": "JM",
    "JPN": "JP",
    "JEY": "JE",
    "JOR": "JO",
    "KAZ": "KZ",
    "KEN": "KE",
    "KIR": "KI",
    "XKX": "XK",
    "KWT": "KW",
    "KGZ": "KG",
    "LAO": "LA",
    "LVA": "LV",
    "LBN": "LB",
    "LSO": "LS",
    "LBR": "LR",
    "LBY": "LY",
    "LIE": "LI",
    "LTU": "LT",
    "LUX": "LU",
    "MAC": "MO",
    "MKD": "MK",
    "MDG": "MG",
    "MWI": "MW",
    "MYS": "MY",
    "MDV": "MV",
    "MLI": "ML",
    "MLT": "MT",
    "MHL": "MH",
    "MTQ": "MQ",
    "MRT": "MR",
    "MUS": "MU",
    "MYT": "YT",
    "MEX": "MX",
    "FSM": "FM",
    "MDA": "MD",
    "MCO": "MC",
    "MNG": "MN",
    "MNE": "ME",
    "MSR": "MS",
    "MAR": "MA",
    "MOZ": "MZ",
    "MMR": "MM",
    "NAM": "NA",
    "NRU": "NR",
    "NPL": "NP",
    "NLD": "NL",
    "ANT": "AN",
    "NCL": "NC",
    "NZL": "NZ",
    "NIC": "NI",
    "NER": "NE",
    "NGA": "NG",
    "NIU": "NU",
    "NFK": "NF",
    "PRK": "KP",
    "MNP": "MP",
    "NOR": "NO",
    "OMN": "OM",
    "PAK": "PK",
    "PLW": "PW",
    "PSE": "PS",
    "PAN": "PA",
    "PNG": "PG",
    "PRY": "PY",
    "PER": "PE",
    "PHL": "PH",
    "PCN": "PN",
    "POL": "PL",
    "PRT": "PT",
    "PRI": "PR",
    "QAT": "QA",
    "REU": "RE",
    "ROU": "RO",
    "RUS": "RU",
    "RWA": "RW",
    "MAF": "MF",
    "WSM": "WS",
    "SMR": "SM",
    "STP": "ST",
    "SAU": "SA",
    "SEN": "SN",
    "SRB": "RS",
    "SYC": "SC",
    "SLE": "SL",
    "SGP": "SG",
    "SXM": "SX",
    "SVK": "SK",
    "SVN": "SI",
    "SLB": "SB",
    "SOM": "SO",
    "ZAF": "ZA",
    "SGS": "GS",
    "KOR": "KR",
    "SSD": "SS",
    "SUN": "SU",
    "ESP": "ES",
    "LKA": "LK",
    "BLM": "BL",
    "SHN": "SH",
    "KNA": "KN",
    "LCA": "LC",
    "SPM": "PM",
    "VCT": "VC",
    "SDN": "SD",
    "SUR": "SR",
    "SJM": "SJ",
    "SWE": "SE",
    "CHE": "CH",
    "SYR": "SY",
    "TWN": "TW",
    "TJK": "TJ",
    "TZA": "TZ",
    "THA": "TH",
    "TLS": "TL",
    "TGO": "TG",
    "TKL": "TK",
    "TON": "TO",
    "TTO": "TT",
    "TUN": "TN",
    "TUR": "TR",
    "TKM": "TM",
    "TCA": "TC",
    "TUV": "TV",
    "UGA": "UG",
    "UKR": "UA",
    "ARE": "AE",
    "GBR": "GB",
    "USA": "US",
    "UMI": "UM",
    "VIR": "VI",
    "URY": "UY",
    "UZB": "UZ",
    "VUT": "VU",
    "VAT": "VA",
    "VEN": "VE",
    "VNM": "VN",
    "WLF": "WF",
    "ESH": "EH",
    "YEM": "YE",
    "ZMB": "ZM",
    "ZWE": "ZW",
}

_CLEAN_FLOAT = re.compile(r"[\s><]+")
_ONLY_NUM = re.compile(r"[^\d.]+")
_CLEAN_PER = re.compile(r"%.*$")


@dataclass
class _MapGrowthKey:
    min: str
    max: str
    opt: str


@dataclass
class _GrowthRes:
    test: dict[str, bool | float | None]
    condition: dict[str, float | None]


def _bool_from_str(value: Any) -> bool | None:
    if isinstance(value, str):
        val = value.strip().lower()
        if val == "yes" or val == "positive" or val == "+":
            return True
        if val == "no" or val == "negative" or val == "-":
            return False
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _safe_avg(values: list[float | None]) -> float | None:
    res = 0.0
    cnt = 0
    for val in values:
        if val is not None:
            res += val
            cnt += 1
    if cnt == 0:
        return None
    return res / cnt


def _safe_convert_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if isinstance(value, float):
        return value
    return None


def _get_growth(
    min_val: float | None, max_val: float | None, growth_type: str, map: _MapGrowthKey
) -> dict[str, float | None]:
    if growth_type == "maximum":
        return {map.max: max_val}
    if growth_type == "minimum":
        return {map.min: min_val}
    if growth_type == "optimum":
        return {map.opt: _safe_avg([min_val, max_val])}
    return {}


def _get_size_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    if "mm" in unit:
        return "mm"
    if "µm" in unit:
        return "µm"
    return None


def _get_pathogenicity(risk_ass: dict[str, Any]) -> Iterable[tuple[str, bool]]:
    host = _bool_from_str(risk_ass.get("pathogenicity animal"))
    if host is not None:
        yield ("animal", host)
    host = _bool_from_str(risk_ass.get("pathogenicity human"))
    if host is not None:
        yield ("human", host)
    host = _bool_from_str(risk_ass.get("pathogenicity plant"))
    if host is not None:
        yield ("plant", host)


def _create_size(
    min: float | None,
    max: float | None,
    unit: str | None,
) -> dict | None:
    con = {
        "minimal": min,
        "maximal": max,
        "unit": unit,
    }
    if (
        con["maximal"] is not None
        and con["minimal"] is not None
        and con["unit"] is not None
    ):
        return con
    return None


def _get_clean_float(value: str | None, index: int) -> None | float:
    if not isinstance(value, str) or value == "":
        return None
    try:
        cleaned = _CLEAN_FLOAT.sub("", value)
        parts = cleaned.split("-")
        return _safe_convert_float(_ONLY_NUM.sub("", parts[index]))
    except IndexError:
        return None


def _growth(
    input_val: str | None,
    input_growth: str | None,
    input_ttyp: str | None,
    map: _MapGrowthKey,
) -> None | _GrowthRes:
    if input_val is None or input_val == "":
        return None
    value = _CLEAN_PER.sub("", input_val).strip()
    growth = _bool_from_str(input_growth)
    if growth is None:
        return None
    min_con = _get_clean_float(value, 0)
    max_con = _get_clean_float(value, -1)
    if max_con is None:
        max_con = min_con
    if input_ttyp is None or input_ttyp.lower() not in _GROWTH:
        return None
    condition = {}
    if growth:
        condition = _get_growth(min_con, max_con, input_ttyp, map)
    return _GrowthRes(
        test={"minimal": min_con, "maximal": max_con, "growth": growth},
        condition=condition,
    )


def _merge_growth_condition(
    old_con: dict[str, Any], new_con: dict[str, float | None], map: _MapGrowthKey
) -> dict[str, float | None]:
    min_val = _safe_float(old_con.get(map.min))
    max_val = _safe_float(old_con.get(map.max))
    opt_val = _safe_float(old_con.get(map.opt))
    min_val_new = new_con.get(map.min)
    max_val_new = new_con.get(map.max)
    opt_val_new = new_con.get(map.opt)

    if min_val_new is not None and (min_val is None or min_val_new < min_val):
        min_val = min_val_new
    if max_val_new is not None and (max_val is None or max_val_new > max_val):
        max_val = max_val_new

    # If optimal not set, compute from min and max
    if opt_val is None and opt_val_new is not None:
        opt_val = opt_val_new

    return {
        map.min: min_val,
        map.max: max_val,
        map.opt: opt_val,
    }


def set_source(transformed_data, bd_id):
    transformed_data["sources"] = [
        {
            "sourceType": "dataset",
            "mode": "automated",
            "name": "BacDive",
            "dateRecorded": _CURRENT_DATE.strftime("%Y-%m-%d"),
            "url": f"https://bacdive.dsmz.de/strain/{bd_id!s}",
            "publisher": [
                {
                    "name": "DSMZ",
                    "identifier": [],
                    "address": {
                        "addressCountry": "Germany",
                        "addressCountryIso": "DE",
                        "addressLocality": "Braunschweig",
                        "postalCode": "38124",
                        "streetAddress": "Inhoffenstraße 7B",
                    },
                    "url": "https://www.dsmz.de/",
                }
            ],
        }
    ]


def analyse_taxonomy(input_data, out):
    taxonomy_in = input_data["Name and taxonomic classification"]
    out["organismType"] = (
        taxonomy_in.get("domain")
        if taxonomy_in.get("domain")
        else (
            taxonomy_in.get("LPSN").get("domain")
            if taxonomy_in.get("LPSN") and taxonomy_in["LPSN"].get("domain")
            else "Other"
        )
    )
    out["taxon"] = [
        {
            "name": taxonomy_in.get("species"),
            "taxonRank": "species",
            "source": ["/sources/0"],
        }
    ]
    out["typeStrain"] = [
        {
            "typeStrain": _bool_from_str(taxonomy_in.get("type strain")),
            "source": ["/sources/0"],
        }
    ]


def strain_identifiers(input_data, out):
    ccno: dict[str | tuple[str, str, str, str], tuple[str, str]] = {}
    for des in _SEP.split(
        input_data["Literature"].get("culture collection no.", "")
        + " ; "
        + input_data.get("Name and taxonomic classification", {}).get(
            "strain designation", ""
        )
    ):
        if not isinstance(des, str) or des.strip() == "":
            continue
        ana = _ACR.identify_ccno(des.strip())
        if ana.designation == "":
            continue
        if ana.acr == "":
            ccno[ana.designation] = ("Designation", ana.designation)
        else:
            ccno[(ana.acr, ana.id.pre, ana.id.core, ana.id.suf)] = (
                "CCNO",
                ana.designation,
            )

    out["identifier"] = [
        {
            "name": nam,
            "value": val,
            "source": ["/sources/0"],
        }
        for nam, val in ccno.values()
    ]

    out["identifier"].append(
        {
            "name": "BD-ID",
            "value": f"BD-ID {input_data.get('General', {}).get('BacDive-ID')}",
            "source": ["/sources/0"],
        }
    )


def origin(input_data):
    origin_in = input_data["Isolation, sampling and environmental information"]

    isolation_in = origin_in.get("isolation")
    if isolation_in:
        for iso in _as_list(isolation_in):
            if c_iso := _ISO_MAPPING.get(iso.get("origin.country")):
                country_iso = c_iso
            else:
                country_iso = None
            ori = {
                "sampleDate": (
                    dat.to_string(True)
                    if (dat := get_date(iso.get("sampling date", ""))) is not None
                    else None
                ),
                "country": (
                    {
                        "name": iso.get("country"),
                        "iso_3166_2": country_iso,
                    }
                    if iso.get("country") or country_iso
                    else None
                ),
                "description": iso.get("sample type"),
                "locationCreated": (
                    {
                        "name": iso.get("geographic location"),
                        "geo": (
                            {
                                "latitude": iso.get("latitude"),
                                "longitude": iso.get("longitude"),
                            }
                            if iso.get("latitude") and iso.get("longitude")
                            else None
                        ),
                    }
                    if iso.get("geographic location")
                    or iso.get("latitude")
                    or iso.get("longitude")
                    else None
                ),
                "source": ["/sources/0"],
            }
            if (
                ori.get("sampleDate")
                or ori["country"]
                or ori["description"]
                or ori["locationCreated"]
            ):
                yield ori

    iso_source_in = origin_in.get("isolation source categories")
    if iso_source_in:
        tag_obj = {
            "tags": [
                {
                    "level1": iso.get("Cat1"),
                    "level2": iso.get("Cat2"),
                    "level3": iso.get("Cat3"),
                }
                for iso in _as_list(iso_source_in)
            ],
            "source": ["/sources/0"],
        }
        if tag_obj.get("tags") != []:
            yield tag_obj


def fattyAcids(input_data):
    fatty_acids_in = input_data.get("Physiology and metabolism", {}).get(
        "fatty acid profile"
    )
    if fatty_acids_in:
        for fa_profile in _as_list(fatty_acids_in):
            fa_obj = {
                "library": fa_profile.get("library/peak naming table"),
                "software": fa_profile.get("software version"),
                "profile": [
                    {
                        "name": fa.get("fatty acid"),
                        "percent": _safe_convert_float(fa.get("percentage")),
                    }
                    for fa in _as_list(fa_profile.get("fatty acids"))
                ],
                "source": ["/sources/0"],
            }
            if fa_obj["library"] or fa_obj["software"] or len(fa_obj["profile"]) > 0:
                yield fa_obj


def biosafety(input_data):
    risk_assessment = input_data["Interaction and safety"].get("risk assessment")
    if risk_assessment:
        for risk in _as_list(risk_assessment):
            lvl = risk.get("biosafety level")
            if lvl is None:
                continue
            yield {
                "riskgroup": lvl,
                "classification": risk.get("biosafety level comment"),
                "source": ["/sources/0"],
            }


def morphology(input_data):
    cell_morph = input_data["Morphology"].get("cell morphology")
    if cell_morph:
        for morph in _as_list(cell_morph):
            cel_len = _create_size(
                _get_clean_float(morph.get("cell length"), 0),
                _get_clean_float(morph.get("cell length"), -1),
                _get_size_unit(morph.get("cell length")),
            )
            cel_wid = _create_size(
                _get_clean_float(morph.get("cell width"), 0),
                _get_clean_float(morph.get("cell width"), -1),
                _get_size_unit(morph.get("cell width")),
            )

            morph_obj = {
                "cellShape": morph.get("cell shape"),
                "cellLength": cel_len,
                "cellWidth": cel_wid,
                "motile": _bool_from_str(morph.get("motility")),
                "flagellum": morph.get("flagellum"),
                "flagellumArrangement": (
                    morph.get("flagellum arrangement").capitalize().replace(",", "")
                    if morph.get("flagellum arrangement")
                    and morph.get("flagellum arrangement")
                    in ["polar", "peritrichous", "Monotrichous, polar"]
                    else None
                ),
                "gliding": (
                    True if morph.get("flagellum arrangement") == "gliding" else None
                ),
                "source": ["/sources/0"],
            }

            if (
                morph_obj["cellShape"]
                or morph_obj["cellLength"]
                or morph_obj["cellWidth"]
                or morph_obj["motile"]
                or morph_obj["flagellum"]
                or morph_obj["flagellumArrangement"]
                or morph_obj["gliding"]
            ):
                yield morph_obj

    colony_morph = input_data["Morphology"].get("colony morphology")
    if colony_morph:
        for morph in _as_list(colony_morph):
            cel_siz = _create_size(
                _get_clean_float(morph.get("colony size"), 0),
                _get_clean_float(morph.get("colony size"), -1),
                _get_size_unit(morph.get("colony size")),
            )
            col_morph = {
                "colonySize": cel_siz,
                "colonyColor": (
                    morph.get("colony color")
                    if morph.get("colony color") in _COLONY_COLORS
                    else None
                ),
                "multiCellComplexForming": morph.get("multi cell complex forming"),
                "source": ["/sources/0"],
            }
            if col_morph["colonyColor"] or col_morph["colonySize"]:
                yield col_morph

    multicell_morph = input_data["Morphology"].get("multicellular morphology")
    if multicell_morph:
        for morph in _as_list(multicell_morph):
            mc_morph = {
                "multiCellComplexForming": _bool_from_str(
                    morph.get("forms multicellular complex")
                ),
                "source": ["/sources/0"],
            }
            if mc_morph["multiCellComplexForming"]:
                yield mc_morph


def staining(input_data):
    cell_morph = input_data["Morphology"].get("cell morphology")
    if cell_morph:
        for morph in _as_list(cell_morph):
            sta = morph.get("gram stain")
            if sta is None:
                continue
            yield {
                "name": "gram stain",
                "value": sta,
                "source": ["/sources/0"],
            }


def growthconditios(input_data):
    growth_in = input_data.get("Culture and growth conditions", {})
    temp = growth_in.get("culture temp")
    if temp:
        temp_obj: dict[str, Any] = {
            "testsTemperature": {},
            "source": ["/sources/0"],
        }
        mapper = _MapGrowthKey(
            min="minimalTemperature", max="maximalTemperature", opt="optimalTemperature"
        )
        for tem in _as_list(temp):
            growth = _growth(
                tem.get("temperature"), tem.get("growth"), tem.get("type"), map=mapper
            )
            if growth is None:
                continue
            temp_obj |= _merge_growth_condition(temp_obj, growth.condition, mapper)
            test_hash = DeepHash(growth.test)[growth.test]
            temp_obj["testsTemperature"][test_hash] = growth.test
        temp_obj["testsTemperature"] = [
            val for val in temp_obj["testsTemperature"].values()
        ]
        yield temp_obj

    ph = growth_in.get("culture pH")
    if ph:
        ph = _as_list(ph)
        ph_obj: dict[str, Any] = {
            "testsPh": {},
            "source": ["/sources/0"],
        }
        mapper = _MapGrowthKey(min="minimalPh", max="maximalPh", opt="optimalPh")
        for p in ph:
            growth = _growth(p.get("pH"), p.get("growth"), p.get("type"), map=mapper)
            if growth is None:
                continue
            ph_obj |= _merge_growth_condition(ph_obj, growth.condition, mapper)
            test_hash = DeepHash(growth.test)[growth.test]
            ph_obj["testsPh"][test_hash] = growth.test
        ph_obj["testsPh"] = [val for val in ph_obj["testsPh"].values()]
        yield ph_obj

    physio_in = input_data["Physiology and metabolism"]
    oxygen = physio_in.get("oxygen tolerance")
    if oxygen:
        for oxy in _as_list(oxygen):
            yield {
                "oxygenRelation": oxy.get("oxygen tolerance"),
                "source": ["/sources/0"],
            }


def halophily(input_data):
    physio = input_data["Physiology and metabolism"]
    hal = physio.get("halophily")
    if hal:
        hal_con: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "source": ["/sources/0"],
                "tests": {},
            }
        )
        mapper = _MapGrowthKey(min="minimal", max="maximal", opt="optimal")
        for entry in _as_list(hal):
            growth = _growth(
                entry.get("concentration"),
                entry.get("growth"),
                entry.get("tested relation"),
                map=mapper,
            )
            if growth is None:
                continue
            hal_con[entry.get("salt", "salt")].update(
                {
                    "name": entry.get("salt"),
                    "unit": ConcentrationUnit.volume_percent,
                    **_merge_growth_condition(
                        hal_con[entry.get("salt", "salt")], growth.condition, mapper
                    ),
                }
            )
            test_hash = DeepHash(growth.test)[growth.test]
            hal_con[entry.get("salt")]["tests"][test_hash] = growth.test

        for con in hal_con.values():
            con["tests"] = [val for val in con["tests"].values()]
            yield con


def cultivationMedia(input_data):
    growth_in = input_data.get("Culture and growth conditions", {})
    media = growth_in.get("culture medium")
    if media:
        for med in _as_list(media):
            if _bool_from_str(med.get("growth")) and (med.get("name") or med.get("link")):
                yield {
                    "name": med.get("name"),
                    "url": med.get("link"),
                    "source": ["/sources/0"],
                }


def spore_formation(input_data):
    spo_in = input_data["Physiology and metabolism"].get("spore formation", [])
    seen: set[bool] = set()
    if spo_in:
        for spo in _as_list(spo_in):
            spore_forming = _bool_from_str(spo.get("spore formation"))
            if spore_forming in seen:
                continue
            if spore_forming is not None:
                seen.add(spore_forming)
                yield {
                    "sporeForming": spore_forming,
                    "source": ["/sources/0"],
                }


def hemolysis(input_data):
    morph = input_data["Morphology"].get("colony morphology", [])
    seen: set[bool] = set()
    default = {
        "blood": "unknown",
        "source": ["/sources/0"],
    }
    if morph:
        for mor in _as_list(morph):
            hem = mor.get("type of hemolysis")
            if hem in seen:
                continue
            seen.add(hem)
            if hem == "gamma":
                yield default | {
                    "hemolysisType": "gamma",
                }
            if hem == "alpha":
                yield default | {
                    "hemolysisType": "alpha",
                }
            if hem == "beta":
                yield default | {
                    "hemolysisType": "beta",
                }


def literature(input_data):
    lit_in = input_data["Literature"].get("literature", [])
    if lit_in:
        for lit in _as_list(lit_in):
            yield {
                "name": lit.get("title"),
                "url": (
                    HttpUrl(f"https://doi.org/{lit.get('DOI')!s}").encoded_string()
                    if lit.get("DOI")
                    else None
                ),
                "source": ["/sources/0"],
            }


def sequences(input_data):
    seq_in = input_data["Sequence information"]
    genome_seq = seq_in.get("Genome sequences")
    if genome_seq:
        for seq in _as_list(genome_seq):
            yield {
                "type": "nucleotide",
                "level": "genome",
                "accessionNumber": get_seq_acc(seq.get("INSDC accession")),
                "description": seq.get("description"),
                "length": get_seq_length(seq.get("length")),
                "source": ["/sources/0"],
            }

    sixteen_s = seq_in.get("16S sequences")
    if sixteen_s:
        for seq in _as_list(sixteen_s):
            yield {
                "type": "nucleotide",
                "level": "identifier sequence",
                "accessionNumber": get_seq_acc(seq.get("accession")),
                "description": seq.get("description"),
                "length": get_seq_length(seq.get("length")),
                "source": ["/sources/0"],
            }


def gc_content(input_data):
    seq_in = input_data["Sequence information"]
    gc_content = seq_in.get("GC content")
    if gc_content:
        for gc in _as_list(gc_content):
            if "±" in gc.get("GC-content", ""):
                continue
            avg = _safe_avg(
                [
                    _get_clean_float(gc.get("GC-content"), 0),
                    _get_clean_float(gc.get("GC-content"), -1),
                ]
            )
            if avg is None:
                continue
            yield {
                "method": (
                    "genome sequence"
                    if gc.get("method") == "sequence analysis"
                    else "experimental"
                ),
                "value": avg,
                "source": ["/sources/0"],
            }


def enzymes(input_data):
    enzyme_in = input_data["Physiology and metabolism"]
    enzyme_list = enzyme_in.get("enzymes")
    if enzyme_list:
        for enzyme in _as_list(enzyme_list):
            if enzyme.get("ec") and re.match(
                r"^(?:EC)? ?\d+\.\d+\.\d+\.n?\d+$", enzyme.get("ec")
            ):
                yield {
                    "name": enzyme.get("value"),
                    "hasECNumber": enzyme.get("ec"),
                    "active": (True if enzyme.get("activity") == "+" else False),
                    "source": ["/sources/0"],
                }


def pathogenicity(input_data):
    risk_assessment = input_data["Interaction and safety"].get("risk assessment")
    if risk_assessment:
        for risk in _as_list(risk_assessment):
            for host, pat in _get_pathogenicity(risk):
                res = {"source": ["/sources/0"], "host": host, "pathogen": "no"}
                if pat:
                    res["pathogen"] = "obligate"
                yield res


def tolerances(input_data):
    physio = input_data["Physiology and metabolism"]
    tol_in = physio.get("antibiotic resistance")
    if tol_in:
        for tol in _as_list(tol_in):
            react = None
            if _bool_from_str(tol.get("is sensitive")):
                react = "sensitive"
            elif _bool_from_str(tol.get("is resistant")):
                react = "resistant"
            tol_obj = {
                "name": tol.get("metabolite"),
                "reaction": react,
                "source": ["/sources/0"],
            }
            if tol_obj["name"] and tol_obj["reaction"]:
                yield tol_obj

    # TODO: add values of concentration and tests later


def metabolic_data(input_data):
    physio = input_data["Physiology and metabolism"]
    m_prod = physio.get("metabolite production")

    if m_prod:
        for met in _as_list(m_prod):
            m_obj = {
                "name": met.get("metabolite"),
                "identifier": (
                    [
                        {
                            "name": "ChEBI",
                            "propertyID": "https://wikidata.org/wiki/Property:P683",
                            "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{met.get('Chebi-ID')}",
                            "value": f"CHEBI:{met.get('Chebi-ID')}",
                        }
                    ]
                    if met.get("Chebi-ID")
                    else []
                ),
                "tests": (
                    [
                        {
                            "type": "production",
                            "active": _bool_from_str(met.get("production")),
                            "kindOfUtilization": None,
                            "protocol": None,
                        }
                    ]
                    if met.get("production")
                    else []
                ),
                "source": ["/sources/0"],
            }
            if m_obj["name"] and m_obj["tests"] is not None:
                yield m_obj

    m_util = physio.get("metabolite utilization")

    if m_util:
        for met in _as_list(m_util):
            m_obj = {
                "name": met.get("metabolite"),
                "identifier": (
                    [
                        {
                            "name": "ChEBI",
                            "propertyID": "https://wikidata.org/wiki/Property:P683",
                            "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{met.get('Chebi-ID')}",
                            "value": f"CHEBI:{met.get('Chebi-ID')}",
                        }
                    ]
                    if met.get("Chebi-ID")
                    else []
                ),
                "tests": (
                    [
                        {
                            "type": "utilization",
                            "active": _bool_from_str(met.get("utilization activity")),
                            "kindOfUtilization": (
                                met.get("kind of utilization tested")
                                if met.get("kind of utilization tested")
                                in [
                                    "assimilation",
                                    "builds acid from",
                                    "degradation",
                                    "energy source",
                                    "fermentation",
                                    "hydrolysis",
                                    "reduction",
                                ]
                                else None
                            ),
                            "protocol": None,
                        }
                    ]
                    if met.get("utilization activity")
                    else []
                ),
                "source": ["/sources/0"],
            }
            if m_obj["name"] and m_obj["tests"] is not None:
                yield m_obj


def collection(input_data):
    references = input_data["Reference"]
    if references:
        for reference in _as_list(references):
            if (
                _CAT.search(reference.get("authors", "")) is None
                or "catalogue" not in reference
                or "@id" not in reference
            ):
                continue
            ccnos = set(
                des.designation
                for des in _ACR.extract_all_valid_ccno_from_text(reference["catalogue"])
                if des.acr != ""
            )
            if len(ccnos) != 1:
                continue
            ccno = ccnos.pop()
            selected: AcrDbEntry | None = get_brc_from_string(
                _ACR, ccno, reference["authors"]
            )
            if selected is None:
                continue
            yield create_collection_dict(_ACR, selected, ccno)


def transform(bac_dive_data) -> Strain | None:

    transformed_data: dict[str, Any] = {"version": 1}
    transformed_data["primaryId"] = f"BD-ID {bac_dive_data['General']['BacDive-ID']!s}"

    # Required
    set_source(transformed_data, bac_dive_data["General"]["BacDive-ID"])
    analyse_taxonomy(bac_dive_data, transformed_data)
    strain_identifiers(bac_dive_data, transformed_data)
    if len(transformed_data["identifier"]) == 1:
        print(f"Only one identifier for BD-ID {bac_dive_data['General']['BacDive-ID']}")
        return None

    # Optional
    transformed_data["origin"] = list(origin(bac_dive_data))
    transformed_data["pathogenicity"] = list(pathogenicity(bac_dive_data))
    transformed_data["bioSafety"] = list(biosafety(bac_dive_data))
    transformed_data["hemolysis"] = list(hemolysis(bac_dive_data))
    transformed_data["fattyAcidProfiles"] = list(fattyAcids(bac_dive_data))
    transformed_data["morphology"] = list(morphology(bac_dive_data))
    transformed_data["staining"] = list(staining(bac_dive_data))
    transformed_data["cultivationMedia"] = list(cultivationMedia(bac_dive_data))
    transformed_data["growthConditions"] = list(growthconditios(bac_dive_data))
    transformed_data["sporeFormation"] = list(spore_formation(bac_dive_data))
    transformed_data["halophily"] = list(halophily(bac_dive_data))
    transformed_data["sequences"] = list(sequences(bac_dive_data))
    transformed_data["gcContent"] = list(gc_content(bac_dive_data))
    transformed_data["literature"] = list(literature(bac_dive_data))
    transformed_data["enzymes"] = list(enzymes(bac_dive_data))
    transformed_data["tolerances"] = list(tolerances(bac_dive_data))
    transformed_data["metabolites"] = list(metabolic_data(bac_dive_data))
    transformed_data["collections"] = list(collection(bac_dive_data))
    # Validation
    try:
        return Strain.model_validate_json(json.dumps(transformed_data))
    except ValidationError as e:
        with get_log_file("bacdive_validation_errors").open("a") as log_file:
            log_file.write(
                f"Validation error for BacDive ID {bac_dive_data['General']['BacDive-ID']}:\n"
            )
            log_file.write(str(e) + "\n\n")
        print(
            f"BacDive Validation failed for ID {bac_dive_data['General']['BacDive-ID']}"
        )
        return None
