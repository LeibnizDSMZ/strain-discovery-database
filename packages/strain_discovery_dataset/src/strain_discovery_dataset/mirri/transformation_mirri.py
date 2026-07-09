from strain_discovery_dataset.utils.run import get_log_file
from microbial_strain_data_model.classes.enums import OrganismType
from microbial_strain_data_model.classes.enums import SupplyForm
from microbial_strain_data_model.classes.enums import Restriction
import json
from datetime import datetime
import re
from typing import Any
from microbial_strain_data_model.strain import Strain
from pydantic_core import ValidationError
from saim.designation.manager import AcronymManager

from strain_discovery_dataset.utils.collections import (
    create_collection_dict,
    get_brc_from_string,
)
from strain_discovery_dataset.utils.data import ACR_DB_VERSION
from cafi.container.acr_db import AcrDbEntry
from strain_discovery_dataset.utils.seq import get_seq_acc


_SEP = re.compile(r"[,;]+")
_MIRRI_ID = re.compile(r"^MIRRI0*")
_ACR = AcronymManager(ACR_DB_VERSION)
_CURRENT_DATE = datetime.now()


_RESISTENCES = {
    "amphotericinBResistance": {
        "name": "amphotericin B",
        "identifier": "2682",
    },
    "fluconazoleResistance": {
        "name": "fluconazole",
        "identifier": "46081",
    },
    "itraconazoleResistance": {
        "name": "itraconazole",
        "identifier": "6076",
    },
    "voriconazoleResistance": {
        "name": "voriconazole",
        "identifier": "10023",
    },
    "resistanceToAzoles": {
        "name": "azole",
        "identifier": "68452",
    },
    "terbinafinResistance": {
        "name": "terbinafine",
        "identifier": "9448",
    },
    "posaconazoleResistance": {
        "name": "posaconazole",
        "identifier": "64355",
    },
    "caspofungiResistance": {
        "name": "caspofungin",
        "identifier": "474180",
    },
}


_METABOLIC_FIELDS = {
    "glucoseTfield": {"identifier": "17234", "name": "glucose"},
    "glycerolTfield": {"identifier": "17754", "name": "glycerol"},
    "galactose": {"identifier": "28260", "name": "galactose"},
    "cellobiose": {"identifier": "17057", "name": "cellobiose"},
    "maltose": {"identifier": "17306", "name": "maltose"},
    "raffinose": {"identifier": "16634", "name": "raffinose"},
    "trehalose": {"identifier": "27082", "name": "trehalose"},
    "lArabinose": {"identifier": "30849", "name": "L-arabinose"},
    "dRibose": {"identifier": "16988", "name": "D-ribose"},
    "lactose": {"identifier": "17716", "name": "lactose"},
    "lRhamnose": {"identifier": "62345", "name": "L-rhamnose"},
    "dMannitol": {"identifier": "16899", "name": "D-mannitol"},
    "sucrose": {"identifier": "17992", "name": "sucrose"},
    "dXylose": {"identifier": "65327", "name": "D-xylose"},
    "melezitose": {"identifier": "6731", "name": "melezitose"},
    "melibiose": {"identifier": "28053", "name": "melibiose"},
    "lSorbose": {"identifier": "17266", "name": "L-sorbose"},
    "nitrate": {"identifier": "17632", "name": "nitrate"},
    "myoInositol": {"identifier": "17268", "name": "myo-inositol"},
    "erythritol": {"identifier": "17113", "name": "erythritol"},
    "dlLactate": {"identifier": "24996", "name": "lactate"},
    "citrate": {"identifier": "16947", "name": "citrate"},
    "salicin": {"identifier": "17814", "name": "salicin"},
    "dArabinose": {"identifier": "17108", "name": "D-arabinose"},
    "dGlucitol": {"identifier": "17924", "name": "D-sorbitol"},
    "succinate": {"identifier": "30031", "name": "succinate"},
    "ribitol": {"identifier": "15963", "name": "ribitol"},
    "inulin": {"identifier": "15443", "name": "inulin"},
    "galactitol": {"identifier": "16813", "name": "galactitol"},
    "methylADGlucoside": {
        "identifier": "37657",
        "name": "methyl D-glucoside",
    },
    "dGlucosamine": {"identifier": "17315", "name": "D-glucosamine"},
    "lLysine": {"identifier": "18019", "name": "L-lysine"},
    "nitrite": {"identifier": "16301", "name": "nitrite"},
    "ethylamine": {"identifier": "15862", "name": "ethylamine"},
    "cadaverine": {"identifier": "18127", "name": "cadaverine"},
    "dGluconate": {"identifier": "8391", "name": "D-gluconate"},
    "solubleStarch": {"identifier": "28017", "name": "starch"},
    "xylitol": {"identifier": "17151", "name": "xylitol"},
    "dGlucono15Lactone": {
        "identifier": "16217",
        "name": "D-glucono-1,5-lactone",
    },
    "dGlucuronate": {"identifier": "15748", "name": "D-glucuronate"},
    "arbutin": {"identifier": "18305", "name": "arbutin"},
    "creatine": {"identifier": "16919", "name": "creatine"},
    "lArabinitol": {"identifier": "18403", "name": "L-arabitol"},
    "creatinine": {"identifier": "16737", "name": "creatinine"},
    "dGlucosamineAsNitrogenSource": {
        "identifier": "17315",
        "name": "D-glucosamine",
    },
    "propane12Diol": {"identifier": "16997", "name": "1,2-propandiol"},
    "dGalacturonate": {
        "identifier": "18024",
        "name": "D-galacturonic acid",
    },
    "butane23Diol": {"identifier": "62064", "name": "2,3-butanediol"},
    "twoKetoDGluconate": {
        "identifier": "88378",
        "name": "2-Keto-L-gluconate",
    },
    "methanol": {"identifier": "17790", "name": "methanol"},
    "ethanol": {"identifier": "16236", "name": "ethanol"},
    "quinicAcid": {"identifier": "26490", "name": "quinate"},
    "dGlucarate": {"identifier": "33801", "name": "D-saccharate"},
    "dGalactonate": {"identifier": "12931", "name": "D-galactonate"},
    "fiveKetoDGluconate": {
        "identifier": "180368",
        "name": "5-Keto-D-gluconate",
    },
    "dGlucoseF1": {
        "identifier": "17634",
        "name": "D-glucose",
        "kindOfUtilization": "fermentation",
    },
    "acidAceticProduction": {
        "identifier": "16411",
        "name": "acetic acid",
        "production": True,
    },
    "sucroseF5": {
        "identifier": "17992",
        "name": "sucrose",
        "kindOfUtilization": "fermentation",
    },
    "dGalactose": {
        "identifier": "12936",
        "name": "D-galactose",
    },
    "maltoseF23": {
        "identifier": "17306",
        "name": "maltose",
        "kindOfUtilization": "fermentation",
    },
    "raffinoseF11": {
        "identifier": "16634",
        "name": "raffinose",
        "kindOfUtilization": "fermentation",
    },
    "lactoseF8": {
        "identifier": "17716",
        "name": "lactose",
        "kindOfUtilization": "fermentation",
    },
    "cellobioseF9": {
        "identifier": "17057",
        "name": "cellobiose",
        "kindOfUtilization": "fermentation",
    },
    "melibioseF7": {
        "identifier": "28053",
        "name": "melibiose",
        "kindOfUtilization": "fermentation",
    },
    "meADGlucosideF4": {
        "identifier": "320061",
        "name": "methyl alpha-D-glucopyranoside",
        "kindOfUtilization": "fermentation",
    },
    "melezitoseF10": {
        "identifier": "6731",
        "name": "melezitose",
        "kindOfUtilization": "fermentation",
    },
    "inulinF12": {
        "identifier": "15443",
        "name": "inulin",
        "kindOfUtilization": "fermentation",
    },
    "dXyloseF14": {
        "identifier": "65327",
        "name": "D-xylose",
        "kindOfUtilization": "fermentation",
    },
    "starchF13": {
        "identifier": "28017",
        "name": "starch",
        "kindOfUtilization": "fermentation",
    },
}


_SPORE_FIELDS = (
    "asexualReproductionStates.endospores",
    "asexualReproductionStates.chlamydospores",
    "asexualReproductionStates.arthroconidia",
    "teliospores",
    "ascosporesWithAGroove",
    "ascosporesWithGelatinousSheath",
    "asciEvanescence",
    "asciShape",
    "basidiaCatenateSolitary",
    "basidiaSeptation",
    "basidiaShape",
    "sexualReproductionStatesT43",
    "asexualReproductionStates.symmetrical ballistoconidia",
    "asexualReproductionStates.asymmetrical ballistoconidia",
    "asexualReproductionStates.blastoconidia",
    "asexualReproductionStates.Terminal formation of blastoconidia on short denticles on a cylindrical to clavate conidiophore",
)

_SPORE_FORMING = frozenset(
    (
        "yes",
        # teliospores
        "angular",
        "round to oval",
        "angular to round to oval",
        # asciEvanescence
        "evanescent",
        "persistent",
        "evanescent and/or persistent",
        # asciShape
        "club shaped",
        # basidiaCatenateSolitary
        "solitary",
        "catenate",
        "solitary and/or catenate",
        # basidiaSeptation
        "one celled",
        "transversely septate",
        "one celled and/or transversely septate",
        "longitudinally-obliquely septate",
        "one celled and/or longitudinally-obliquely septate",
        "transversely septate and/or longitudinally-obliquely septate",
        "all forms possible",
        # basidiaShape
        "clavate",
        "cylindrical",
        "clavate and/or/to cylindrical",
        "capitate",
        "clavate and/or capitate",
        "cylindrical and/or capitate",
        "clavate and/or cylindrical and/or capitate",
        # sexualReproductionStatesT43
        "ascomycetous",
        "basidiomycetous",
    )
)

_COUNTRIES = {
    "Afghanistan": "AF",
    "Albania": "AL",
    "Algeria": "DZ",
    "American Samoa": "AS",
    "Andorra": "AD",
    "Angola": "AO",
    "Anguilla": "AI",
    "Antarctica": "AQ",
    "Antigua and Barbuda": "AG",
    "Argentina": "AR",
    "Armenia": "AM",
    "Aruba": "AW",
    "Australia": "AU",
    "Austria": "AT",
    "Azerbaijan": "AZ",
    "Bahamas (the)": "BS",
    "Bahrain": "BH",
    "Bangladesh": "BD",
    "Barbados": "BB",
    "Belarus": "BY",
    "Belgium": "BE",
    "Belize": "BZ",
    "Benin": "BJ",
    "Bermuda": "BM",
    "Bhutan": "BT",
    "Bolivia (Plurinational State of)": "BO",
    "Bonaire, Sint Eustatius and Saba": "BQ",
    "Bosnia and Herzegovina": "BA",
    "Botswana": "BW",
    "Bouvet Island": "BV",
    "Brazil": "BR",
    "British Indian Ocean Territory (the)": "IO",
    "Brunei Darussalam": "BN",
    "Bulgaria": "BG",
    "Burkina Faso": "BF",
    "Burundi": "BI",
    "Cabo Verde": "CV",
    "Cambodia": "KH",
    "Cameroon": "CM",
    "Canada": "CA",
    "Cayman Islands (the)": "KY",
    "Central African Republic (the)": "CF",
    "Chad": "TD",
    "Chile": "CL",
    "China": "CN",
    "Christmas Island": "CX",
    "Cocos (Keeling) Islands (the)": "CC",
    "Colombia": "CO",
    "Comoros (the)": "KM",
    "Congo (the Democratic Republic of the)": "CD",
    "Congo (the)": "CG",
    "Cook Islands (the)": "CK",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Cuba": "CU",
    "Curaçao": "CW",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Côte d'Ivoire": "CI",
    "Denmark": "DK",
    "Djibouti": "DJ",
    "Dominica": "DM",
    "Dominican Republic (the)": "DO",
    "Ecuador": "EC",
    "Egypt": "EG",
    "El Salvador": "SV",
    "Equatorial Guinea": "GQ",
    "Eritrea": "ER",
    "Estonia": "EE",
    "Eswatini": "SZ",
    "Ethiopia": "ET",
    "Falkland Islands (the) [Malvinas]": "FK",
    "Faroe Islands (the)": "FO",
    "Fiji": "FJ",
    "Finland": "FI",
    "France": "FR",
    "French Guiana": "GF",
    "French Polynesia": "PF",
    "French Southern Territories (the)": "TF",
    "Gabon": "GA",
    "Gambia (the)": "GM",
    "Georgia": "GE",
    "Germany": "DE",
    "Ghana": "GH",
    "Gibraltar": "GI",
    "Greece": "GR",
    "Greenland": "GL",
    "Grenada": "GD",
    "Guadeloupe": "GP",
    "Guam": "GU",
    "Guatemala": "GT",
    "Guernsey": "GG",
    "Guinea": "GN",
    "Guinea-Bissau": "GW",
    "Guyana": "GY",
    "Haiti": "HT",
    "Heard Island and McDonald Islands": "HM",
    "Holy See (the)": "VA",
    "Honduras": "HN",
    "Hong Kong": "HK",
    "Hungary": "HU",
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Iran (Islamic Republic of)": "IR",
    "Iraq": "IQ",
    "Ireland": "IE",
    "Isle of Man": "IM",
    "Israel": "IL",
    "Italy": "IT",
    "Jamaica": "JM",
    "Japan": "JP",
    "Jersey": "JE",
    "Jordan": "JO",
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kiribati": "KI",
    "Korea (the Democratic People's Republic of)": "KP",
    "Korea (the Republic of)": "KR",
    "Kuwait": "KW",
    "Kyrgyzstan": "KG",
    "Lao People's Democratic Republic (the)": "LA",
    "Latvia": "LV",
    "Lebanon": "LB",
    "Lesotho": "LS",
    "Liberia": "LR",
    "Libya": "LY",
    "Liechtenstein": "LI",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Macao": "MO",
    "Madagascar": "MG",
    "Malawi": "MW",
    "Malaysia": "MY",
    "Maldives": "MV",
    "Mali": "ML",
    "Malta": "MT",
    "Marshall Islands (the)": "MH",
    "Martinique": "MQ",
    "Mauritania": "MR",
    "Mauritius": "MU",
    "Mayotte": "YT",
    "Mexico": "MX",
    "Micronesia (Federated States of)": "FM",
    "Moldova (the Republic of)": "MD",
    "Monaco": "MC",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Montserrat": "MS",
    "Morocco": "MA",
    "Mozambique": "MZ",
    "Myanmar": "MM",
    "Namibia": "NA",
    "Nauru": "NR",
    "Nepal": "NP",
    "Netherlands (the)": "NL",
    "New Caledonia": "NC",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Niger (the)": "NE",
    "Nigeria": "NG",
    "Niue": "NU",
    "Norfolk Island": "NF",
    "Northern Mariana Islands (the)": "MP",
    "Norway": "NO",
    "Oman": "OM",
    "Pakistan": "PK",
    "Palau": "PW",
    "Palestine, State of": "PS",
    "Panama": "PA",
    "Papua New Guinea": "PG",
    "Paraguay": "PY",
    "Peru": "PE",
    "Philippines (the)": "PH",
    "Pitcairn": "PN",
    "Poland": "PL",
    "Portugal": "PT",
    "Puerto Rico": "PR",
    "Qatar": "QA",
    "Republic of North Macedonia": "MK",
    "Romania": "RO",
    "Russian Federation (the)": "RU",
    "Rwanda": "RW",
    "Réunion": "RE",
    "Saint Barthélemy": "BL",
    "Saint Helena, Ascension and Tristan da Cunha": "SH",
    "Saint Kitts and Nevis": "KN",
    "Saint Lucia": "LC",
    "Saint Martin (French part)": "MF",
    "Saint Pierre and Miquelon": "PM",
    "Saint Vincent and the Grenadines": "VC",
    "Samoa": "WS",
    "San Marino": "SM",
    "Sao Tome and Principe": "ST",
    "Saudi Arabia": "SA",
    "Senegal": "SN",
    "Serbia": "RS",
    "Seychelles": "SC",
    "Sierra Leone": "SL",
    "Singapore": "SG",
    "Sint Maarten (Dutch part)": "SX",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Solomon Islands": "SB",
    "Somalia": "SO",
    "South Africa": "ZA",
    "South Georgia and the South Sandwich Islands": "GS",
    "South Sudan": "SS",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Sudan (the)": "SD",
    "Suriname": "SR",
    "Svalbard and Jan Mayen": "SJ",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Syrian Arab Republic": "SY",
    "Taiwan (Province of China)": "TW",
    "Tajikistan": "TJ",
    "Tanzania, United Republic of": "TZ",
    "Thailand": "TH",
    "Timor-Leste": "TL",
    "Togo": "TG",
    "Tokelau": "TK",
    "Tonga": "TO",
    "Trinidad and Tobago": "TT",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Turkmenistan": "TM",
    "Turks and Caicos Islands (the)": "TC",
    "Tuvalu": "TV",
    "Uganda": "UG",
    "Ukraine": "UA",
    "United Arab Emirates (the)": "AE",
    "United Kingdom of Great Britain and Northern Ireland (the)": "GB",
    "United States Minor Outlying Islands (the)": "UM",
    "United States of America (the)": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Vanuatu": "VU",
    "Venezuela (Bolivarian Republic of)": "VE",
    "Viet Nam": "VN",
    "Virgin Islands (British)": "VG",
    "Virgin Islands (U.S.)": "VI",
    "Wallis and Futuna": "WF",
    "Western Sahara": "EH",
    "Yemen": "YE",
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
    "Åland Islands": "AX",
}

_MONTH = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


_ORG_TYPE = {
    "Algae": OrganismType.algae.value,
    "Archaea": OrganismType.archaea.value,
    "Bacteria": OrganismType.bacteria.value,
    "Cyanobacteria": OrganismType.bacteria.value,
    "Filamentous Fungi": OrganismType.fungi.value,
    "Microalgae": OrganismType.algae.value,
    "Yeast": OrganismType.fungi.value,
}

_SUPPLY = {
    "Agar": SupplyForm.agar.value,
    "Cryo": SupplyForm.cryo.value,
    "Dry Ice": SupplyForm.dry.value,
    "Liquid Culture Medium": SupplyForm.liquid.value,
    "Lyo": SupplyForm.lyo.value,
    "Oil": SupplyForm.oil.value,
    "Water": SupplyForm.water.value,
    "DNA": SupplyForm.dna.value,
}

_RESTRICTIONS = {
    "no known restriction apply": Restriction.no_restrictions.value,
    "only for non-commercial purposes": Restriction.no_commercial.value,
    "for commercial development a special agreement is requested": Restriction.agreement.value,
}

_STAINING = {"+": "positive", "-": "negative", "-, +": "variable", "-,+": "variable"}


def _map_supply_form(original_name):
    return _SUPPLY.get(original_name, None)


def _map_restriction(restriction_text):
    return _RESTRICTIONS.get(restriction_text.lower(), None)


def _fix_date(date):
    if not date:
        return None

    for key, value in _MONTH.items():
        date = date.replace(key, value)

    if re.findall(r"\D{2,}", date):
        print(f"Non standardized date: {date}")

    sdate = re.findall(r"\d+", date)

    if len(sdate) >= 3:
        return f"{sdate[2]}-{sdate[1]}-{sdate[0]}"
    elif len(sdate) == 2:
        return f"{sdate[1]}-{sdate[0]}"
    elif len(sdate) == 1:
        return f"{sdate[0]}"
    else:
        return None


def set_source(out, mirri_id):
    out["sources"] = [
        {
            "sourceType": "dataset",
            "mode": "automated",
            "name": "MIRRI catalogue",
            "dateRecorded": _CURRENT_DATE.strftime("%Y-%m-%d"),
            "url": f"https://catalog.mirri.org/page/Strains_display/{mirri_id!s}",
            "publisher": [
                {
                    "name": "MIRRI ERIC",
                    "identifier": [],
                    "address": {
                        "addressCountry": "Portugal",
                        "addressCountryIso": "PT",
                        "addressLocality": "Braga",
                        "postalCode": "4710-057",
                        "streetAddress": "University of Minho, Campus of Gualtar, Pedagogic Complex 3,Floor 0,",
                    },
                    "url": "https://mirri.org/",
                }
            ],
        }
    ]


def get_default_str(
    data: dict[str, Any],
    key: str,
    default: str,
) -> str:
    val = data.get(key, default)
    if isinstance(val, str):
        return val
    return default


def strain_identifiers(input_data, out):
    out["primaryId"] = input_data["name"]

    ccno: dict[str | tuple[str, str, str, str], tuple[str, str]] = {}
    for des in _SEP.split(
        get_default_str(input_data, "otherCcNumber", "")
        + " ; "
        + get_default_str(input_data, "mirriAccessionNumber", "")
        + " ; "
        + get_default_str(input_data, "otherDenomination", "")
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
            "name": "MIRRI ID",
            "value": input_data["name"],
            "source": ["/sources/0"],
        }
    )


def origin(input_data, out):
    country_list = input_data["country"]
    out["origin"] = []

    country = {}
    if isinstance(country_list, list) and len(country_list) > 0:
        country = {
            "name": country_list[0].get("name"),
            "iso_3166_2": _COUNTRIES.get(country_list[0].get("name")),
        }

    coordinates = input_data["coordinates"]
    if coordinates:
        coordinates["elevation"] = input_data["coordinates"].pop("altitude")

    orig = {
        "locationCreated": (
            {
                "name": (
                    input_data["geographicOrigin"]
                    if input_data["geographicOrigin"]
                    else None
                ),
                "geo": coordinates if coordinates else None,
            }
            if input_data["geographicOrigin"] or coordinates
            else None
        ),
        "country": country if country.get("iso_3166_2") else None,
        "description": f"{input_data['substrateOfIsolation']}, {input_data['isolationHabitat']}",
        "sampleDate": _fix_date(input_data["collectionDate"]),
        "isolationDate": _fix_date(input_data["isolationDate"]),
        "source": ["/sources/0"],
    }

    if (
        orig["country"]
        or orig["locationCreated"]
        or orig["description"]
        or orig["sampleDate"]
        or orig["isolationDate"]
    ):
        out["origin"].append(orig)


def biosafety(input_data, out):
    out["bioSafety"] = [
        {
            "riskgroup": input_data["riskGroup"],
            "source": ["/sources/0"],
        }
    ]


def spore_formation(input_data, out):
    for field_path in _SPORE_FIELDS:
        keys = field_path.split(".")
        value = input_data
        try:
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
        except (KeyError, TypeError, AttributeError):
            value = None

        if value is not None and value in _SPORE_FORMING:
            out["sporeFormation"] = [
                {
                    "sporeForming": True,
                    "source": ["/sources/0"],
                }
            ]
            break
    asc_sha = input_data.get("ascosporesShape")
    if "sporeFormation" not in out and isinstance(asc_sha, dict):
        for val in asc_sha.values():
            if val == "yes":
                out["sporeFormation"] = [
                    {
                        "sporeForming": True,
                        "source": ["/sources/0"],
                    }
                ]
                break


def morphology(input_data, out):
    cell_length = None
    if input_data.get("lengthOfCellsInBrothMedium"):
        length_obj = input_data["lengthOfCellsInBrothMedium"]
        cell_length = {
            "minimal": length_obj.get("min"),
            "maximal": length_obj.get("max"),
            "size": "µm",
        }
    elif input_data.get("lengthOfCellsOnSolidMedium"):
        length_obj = input_data["lengthOfCellsOnSolidMedium"]
        cell_length = {
            "minimal": length_obj.get("min"),
            "maximal": length_obj.get("max"),
            "size": "µm",
        }

    cell_width = None
    if input_data.get("widthOfCellsInBrothMedium"):
        width_obj = input_data["widthOfCellsInBrothMedium"]
        cell_width = {
            "minimal": width_obj.get("min"),
            "maximal": width_obj.get("max"),
            "size": "µm",
        }

    cell_shape = None
    if input_data.get("cellShape"):
        for key, value in input_data["cellShape"].items():
            if value == "yes":
                cell_shape = key
                break

    if cell_width is not None or cell_length is not None or cell_shape is not None:
        out["morphology"] = [
            {
                "cellShape": cell_shape,
                "cellLength": cell_length,
                "cellWidth": cell_width,
                "motile": None,
                "flagellum": None,
                "flagellumArrangement": None,
                "gliding": None,
                "colonySize": None,
                "colonyColor": None,
                "multiCellComplexForming": None,
                "source": ["/sources/0"],
            }
        ]


def staining(input_data, out):
    out["staining"] = []

    if (
        input_data["diazoniumBlueBReaction"]
        and not input_data["diazoniumBlueBReaction"] == "?"
    ):
        diazoniumbb = _STAINING.get(input_data["diazoniumBlueBReaction"])
        if diazoniumbb is not None:
            out["staining"].append(
                {
                    "name": "Diazonium Blue B",
                    "value": diazoniumbb,
                    "source": ["/sources/0"],
                }
            )


def legal(input_data, out):
    out["legal"] = []
    legal_obj = {
        "nagoyaRestrictions": (
            input_data["nagoya"] if input_data["nagoya"] != "?" else None
        ),
        "dualUse": True if input_data["dualUse"] == "Yes" else False,
        "quarantineEU": (True if input_data["quarantineEurope"] == "Yes" else False),
        "gmo": True if input_data["gmofield"] == "Yes" else False,
        "gmoInformation": input_data["gmo"],
        "source": ["/sources/0"],
    }
    if legal_obj["nagoyaRestrictions"]:
        out["legal"].append(legal_obj)


def cultivationMedia(input_data, out):
    out["cultivationMedia"] = []

    for media in input_data["recommendedMediumForGrowth"]:
        out["cultivationMedia"].append({"name": media["name"], "source": ["/sources/0"]})


def growthconditios(input_data, out):
    min_test = float()
    max_test = float()

    if input_data["recommendedGrowthTemperature"]:
        min_test = float(input_data["recommendedGrowthTemperature"]["min"])
        max_test = float(input_data["recommendedGrowthTemperature"]["max"])

    if input_data["testedTemperatureGrowthRange"]:
        min_test = min(float(input_data["testedTemperatureGrowthRange"]["min"]), min_test)
        max_test = max(float(input_data["testedTemperatureGrowthRange"]["max"]), max_test)

    out["growthConditions"] = []

    out["growthConditions"].append(
        {
            "optimalTemperature": None,
            "minimalTemperature": None,
            "maximalTemperature": None,
            "testsTemperature": (
                [{"minimal": min_test, "maximal": max_test, "growth": True}]
                if min_test
                else []
            ),
            "optimalPh": None,
            "minimalPh": None,
            "maximalPh": None,
            "testsPh": [],
            "oxygenRelation": None,
            "source": ["/sources/0"],
        }
    )


def taxon(input_data, out):
    out["taxon"] = []

    for i in input_data["taxonName"]:
        out["taxon"].append(
            {
                "name": f"{i['name']}, {i['authors']}",
                "scientificName": {"name": i["name"], "author": i["authors"]},
                "taxonRank": ("species" if len(i["name"].split(" ")) == 2 else None),
                "source": ["/sources/0"],
            }
        )


def literature(input_data, out):
    lit_in = input_data.get("literatureDoi", [])
    if lit_in:
        out["literature"] = [
            {
                "name": lit.get("name"),
                "url": lit.get("url"),
                "source": ["/sources/0"],
            }
            for lit in lit_in
        ]


def sequences(input_data, out):
    out["sequences"] = []

    for genome in input_data["eukaryoticGenomes"]:
        gen_name = genome.get("name", "")
        if (
            isinstance(gen_name, str) and gen_name.startswith("GCA_")
        ) or gen_name.startswith("GCF_"):
            out["sequences"].append(
                {
                    "type": "nucleotide",
                    "level": "genome",
                    "accessionNumber": get_seq_acc(genome["name"]),
                    "source": ["/sources/0"],
                }
            )

    for genome in input_data["prokaryoticGenomes"]:
        gen_name = genome.get("name", "")
        if (
            isinstance(gen_name, str) and gen_name.startswith("GCA_")
        ) or gen_name.startswith("GCF_"):
            out["sequences"].append(
                {
                    "type": "nucleotide",
                    "level": "genome",
                    "accessionNumber": get_seq_acc(genome["name"]),
                    "source": ["/sources/0"],
                }
            )


def organism_type(input_data, out):
    out["organismType"] = _ORG_TYPE.get(input_data.get("organismType"))

    if out["organismType"] == "Fungi":
        morph_types = {"Filamentous Fungi": "filamentous", "Yeast": "yeast"}
        out["morphType"] = morph_types.get(input_data["organismType"])


def knownApplications(input_data, out):
    app = input_data.get("applicationsMirri")
    if isinstance(app, str) and app != "":
        out["knownApplications"] = [
            {"application": app, "source": ["/sources/0"]}
            for ele in app.split(",")
            if (cle := ele.strip()) != ""
        ]


def metabolic_data(input_data, out):
    out["metabolites"] = []

    for metabo_field, metabolite in _METABOLIC_FIELDS.items():
        if metabo_field in input_data and input_data[metabo_field] in (
            "+",
            "-",
        ):
            out["metabolites"].append(
                {
                    "name": metabolite["name"],
                    "identifier": [
                        {
                            "name": "ChEBI",
                            "propertyID": "https://wikidata.org/wiki/Property:P662",
                            "url": f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={metabolite['identifier']}",
                            "value": f"CHEBI:{metabolite['identifier']}",
                        }
                    ],
                    "tests": [
                        {
                            "active": (
                                True if input_data[metabo_field] == "+" else False
                            ),
                            "kindOfUtilization": metabolite.get("kindOfUtilization"),
                            "protocol": None,
                            "relatedData": [],
                            "type": (
                                "production"
                                if metabolite.get("production", False) == True
                                else "utilization"
                            ),
                        }
                    ],
                    "source": ["/sources/0"],
                }
            )


def tolerances(input_data, out):
    out["tolerances"] = []

    for field_name, antibiotic in _RESISTENCES.items():
        if field_name in input_data and input_data[field_name] in (
            "resistant",
            "not resistant",
        ):
            out["tolerances"].append(
                {
                    "name": antibiotic["name"],
                    "identifier": [
                        {
                            "name": "ChEBI",
                            "propertyID": "https://wikidata.org/wiki/Property:P662",
                            "url": f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={antibiotic['identifier']}",
                            "value": f"CHEBI:{antibiotic['identifier']}",
                        }
                    ],
                    "reaction": (
                        "resistant"
                        if input_data.get(field_name) == "resistant"
                        else "sensitive"
                    ),
                    "source": ["/sources/0"],
                }
            )


def collection(input_data, out):
    out["collections"] = []
    col_name = input_data.get("dataFrom")
    ccno_str = get_default_str(input_data, "mirriAccessionNumber", "")
    ccnos = set(
        des.designation for des in _ACR.extract_all_valid_ccno_from_text(ccno_str)
    )
    if isinstance(col_name, str) and col_name != "" and len(ccnos) == 1:
        ccno = ccnos.pop()
        selected: AcrDbEntry | None = get_brc_from_string(_ACR, ccno, col_name)
        if selected is not None:
            if selected.ror == "02tyer376":
                raise ValueError(f"DSMZ {ccno} detected in {out['primaryId']}")
            out["collections"].append(create_collection_dict(_ACR, selected, ccno))


def transform(mirri_data) -> Strain | None:
    transformed_data: dict[str, Any] = {"version": 1}

    # Required
    organism_type(mirri_data, transformed_data)
    set_source(transformed_data, _MIRRI_ID.sub("", mirri_data["name"]))

    if mirri_data["type"] == "Yes":
        transformed_data["typeStrain"] = [
            {
                "typeStrain": True,
                "source": ["/sources/0"],
            }
        ]
    elif mirri_data["type"] == "No":
        transformed_data["typeStrain"] = [
            {
                "typeStrain": False,
                "source": ["/sources/0"],
            }
        ]

    strain_identifiers(mirri_data, transformed_data)
    taxon(mirri_data, transformed_data)
    if len(transformed_data["identifier"]) == 1:
        print(f"Only one identifier for MIRRI-ID {mirri_data.get('name', 'unknown')}")
        return None

    # Optional
    origin(mirri_data, transformed_data)
    legal(mirri_data, transformed_data)
    biosafety(mirri_data, transformed_data)
    morphology(mirri_data, transformed_data)
    staining(mirri_data, transformed_data)
    growthconditios(mirri_data, transformed_data)
    cultivationMedia(mirri_data, transformed_data)
    spore_formation(mirri_data, transformed_data)
    sequences(mirri_data, transformed_data)
    literature(mirri_data, transformed_data)
    knownApplications(mirri_data, transformed_data)
    collection(mirri_data, transformed_data)
    tolerances(mirri_data, transformed_data)
    metabolic_data(mirri_data, transformed_data)

    # Validation
    try:
        return Strain.model_validate_json(json.dumps(transformed_data))
    except (ValidationError, ValueError) as e:
        with get_log_file("mirri_validation_errors").open(
            "a", encoding="utf-8"
        ) as log_file:
            log_file.write(f"Validation failed {mirri_data.get('name', 'unknown')}\n")
            log_file.write(f"{e}\n")
        print(f"MIRRI Validation failed {mirri_data.get('name', 'unknown')}")
        return None
