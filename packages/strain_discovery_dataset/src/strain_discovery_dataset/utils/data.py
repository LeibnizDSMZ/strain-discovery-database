from pydantic_extra_types.country import CountryAlpha2
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Final, Literal, NotRequired, TypedDict, final
from pydantic import BaseModel
from saim.shared.data_con.culture import CultureStatus
from saim.designation.manager import AcronymManager
from saim.taxon_name.manager import TaxonManager
from saim.shared.data_con.taxon import DomainE
from saim.shared.data_con.designation import CCNoId
from datetime import date

# TODO update types to correct API version 2, especially DOIs and online status

ACR_DB_VERSION: Final[str] = "v0.11.1"

DataSourceEnum = Literal[
    "straininfo archive",
    "scraped from brc website",
    "found on brc website",
    "provided by brc",
    "external database",
    "mirri database",
    "registration",
]

StrainStatusEnum = Literal[
    "erroneous",
    "deposition",
    "published online",
    "published offline",
]

DepositStatusEnum = Literal[
    "private",
    "dead",
    "unknown",
    "available",
    "erroneous data",
]

SequenceTypeEnum = Literal["gene", "genome", "rrnaop", "patent"]

AssemblyLevelEnum = Literal["complete", "chromosome", "scaffold", "contig"]


@dataclass(slots=True, frozen=True)
class _RelData:
    @property
    def relation(self) -> list[str]:
        return []


@dataclass(slots=True, frozen=True)
class SaimMatchData:
    ccno: str
    acr: str
    brc_id: int
    id: CCNoId
    strain: _RelData = field(default_factory=_RelData)

    @property
    def status(self) -> CultureStatus:
        return CultureStatus.unk

    def to_json(self) -> str:
        def convert(obj):
            if isinstance(obj, _RelData):
                return {"relation": obj.relation}
            elif isinstance(obj, CCNoId):
                return asdict(obj)
            return obj

        return json.dumps(asdict(self), default=convert)


class Sample(TypedDict):
    source: NotRequired[str]
    countryCode: NotRequired[CountryAlpha2]


class DepositRelation(TypedDict):
    siDP: int
    designation: str
    ccID: NotRequired[int]
    erroneous: bool
    origin: NotRequired[int]


class Relation(TypedDict):
    deposit: list[DepositRelation]
    designation: NotRequired[list[str]]


class TaxonNameSI(TypedDict):
    name: str
    ncbi: NotRequired[int]
    lpsn: NotRequired[int]


class ArchiveEntry(TypedDict):
    doi: str
    online: bool  # TODO: change to correct API
    date: date
    title: str


class RelationToDeposit(TypedDict):
    siDP: int
    designation: str


class Sequence(TypedDict):
    accessionNumber: str
    deposit: list[RelationToDeposit]
    year: NotRequired[int]
    description: NotRequired[str]
    length: NotRequired[int]
    assemblyLevel: NotRequired[AssemblyLevelEnum]
    type: SequenceTypeEnum


class Literature(TypedDict):
    title: str
    year: int
    deposit: list[RelationToDeposit]
    pubmed: NotRequired[int]
    pmc: NotRequired[int]
    issn: NotRequired[str]
    doi: NotRequired[str]
    author: NotRequired[str]
    publisher: NotRequired[str]


class CultureCollection(TypedDict):
    ccID: int
    name: str
    code: str
    deprecated: bool


class Catalogue(TypedDict):
    url: str
    online: bool


class Submitter(TypedDict):
    name: NotRequired[str]
    institute: NotRequired[str]
    countryCode: NotRequired[CountryAlpha2]
    place: NotRequired[list[str]]
    ror: NotRequired[str]
    orcid: NotRequired[str]


class Registration(TypedDict):
    date: date
    submitter: NotRequired[Submitter]


class SIDeposit(TypedDict):
    siDP: int
    designation: str
    dataSource: list[DataSourceEnum]
    catalogue: NotRequired[Catalogue]
    cultureCollection: NotRequired[CultureCollection]
    registration: NotRequired[Registration]
    taxon: NotRequired[TaxonNameSI]
    typeStrain: bool
    lastUpdate: date
    status: DepositStatusEnum


class SIStrain(TypedDict):
    siID: int
    doi: str
    doi_online: bool
    merged: NotRequired[list[int]]
    typeStrain: bool
    sample: NotRequired[Sample]
    bdID: NotRequired[int]
    status: NotRequired[StrainStatusEnum]
    taxon: NotRequired[TaxonNameSI]
    relation: Relation
    archive: list[ArchiveEntry]
    alternative: NotRequired[list[int]]
    sequence: NotRequired[list[Sequence]]
    literature: NotRequired[list[Literature]]


class StrainMaxRecord(TypedDict):
    strain: SIStrain
    deposits: list[SIDeposit]


class Task(TypedDict):
    id: str
    ccnos: list[str]
    taxon: str
    domain: DomainE


class ResultCCNo(TypedDict):
    ccno: str
    si_ids: dict[int, StrainMaxRecord]


class Result(TypedDict):
    id: str
    ccnos: list[ResultCCNo]
    best_match_si_id: StrainMaxRecord | None


@final
class RunConf(BaseModel):
    output: Path
    cache: Path


class TaxonName(TypedDict):
    name: str
    ncbi: int | None
    lpsn: int | None


class Manager(TypedDict):
    acr: AcronymManager
    tax: TaxonManager


class Memory(TypedDict):
    ccnos: dict[tuple[str, str, str, str], set[int]]
    strains: dict[int, StrainMaxRecord]
    man: Manager | None
    taxa: dict[tuple[str, DomainE], TaxonName]
    match: dict[tuple[str, DomainE, str, int, int], bool]


@dataclass(slots=True)
class SourceStatistic:
    BacDive: int = 0
    MIRRI: int = 0
    DSMZ: int = 0
    StrainInfo: int = 0
    total: int = 0
    venn: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True)
class SourceMatchStatistic:
    BacDive: int = 0
    MIRRI: int = 0
    DSMZ: int = 0
    total: int = 0


SOURCE_MAPPING: dict[str, str] = {
    "BacDive": "BacDive",
    "MIRRI": "MIRRI catalogue",
    "DSMZ": "DSMZ internal database",
    "StrainInfo": "StrainInfo",
}

SOURCE_MATCH_MAPPING: dict[str, str] = {
    "BacDive": "BacDive",
    "MIRRI": "MIRRI catalogue",
    "DSMZ": "DSMZ internal database",
}


@dataclass(slots=True)
class OrganismStatistic:
    Algae: SourceStatistic = field(default_factory=SourceStatistic)
    Archaea: SourceStatistic = field(default_factory=SourceStatistic)
    Bacteria: SourceStatistic = field(default_factory=SourceStatistic)
    Fungi: SourceStatistic = field(default_factory=SourceStatistic)
    Protist: SourceStatistic = field(default_factory=SourceStatistic)


@dataclass(slots=True)
class DataStatistic:
    entries: SourceStatistic = field(default_factory=SourceStatistic)
    notEmpty: SourceStatistic = field(default_factory=SourceStatistic)


@dataclass
class FieldStatistic:
    legal: DataStatistic = field(default_factory=DataStatistic)
    relatedData: DataStatistic = field(default_factory=DataStatistic)
    fattyAcidProfiles: DataStatistic = field(default_factory=DataStatistic)
    metabolites: DataStatistic = field(default_factory=DataStatistic)
    typeStrain: DataStatistic = field(default_factory=DataStatistic)
    origin: DataStatistic = field(default_factory=DataStatistic)
    cultivationMedia: DataStatistic = field(default_factory=DataStatistic)
    tolerances: DataStatistic = field(default_factory=DataStatistic)
    identifier: DataStatistic = field(default_factory=DataStatistic)
    morphology: DataStatistic = field(default_factory=DataStatistic)
    bioSafety: DataStatistic = field(default_factory=DataStatistic)
    sequences: DataStatistic = field(default_factory=DataStatistic)
    pathogenicity: DataStatistic = field(default_factory=DataStatistic)
    staining: DataStatistic = field(default_factory=DataStatistic)
    collections: DataStatistic = field(default_factory=DataStatistic)
    literature: DataStatistic = field(default_factory=DataStatistic)
    otherMedia: DataStatistic = field(default_factory=DataStatistic)
    sporeFormation: DataStatistic = field(default_factory=DataStatistic)
    hemolysis: DataStatistic = field(default_factory=DataStatistic)
    taxon: DataStatistic = field(default_factory=DataStatistic)
    halophily: DataStatistic = field(default_factory=DataStatistic)
    gcContent: DataStatistic = field(default_factory=DataStatistic)
    knownApplications: DataStatistic = field(default_factory=DataStatistic)
    growthConditions: DataStatistic = field(default_factory=DataStatistic)
    wallConstituents: DataStatistic = field(default_factory=DataStatistic)
    enzymes: DataStatistic = field(default_factory=DataStatistic)


@dataclass(slots=True)
class MatchStatistic:
    strainInfo: SourceMatchStatistic = field(default_factory=SourceMatchStatistic)
    saim: SourceMatchStatistic = field(default_factory=SourceMatchStatistic)
    unmatched: SourceMatchStatistic = field(default_factory=SourceMatchStatistic)


@dataclass(slots=True)
class Statistics:
    match: MatchStatistic = field(default_factory=MatchStatistic)
    strains: FieldStatistic = field(default_factory=FieldStatistic)
    taxa: OrganismStatistic = field(default_factory=OrganismStatistic)
    sequences: SourceStatistic = field(default_factory=SourceStatistic)
    literature: SourceStatistic = field(default_factory=SourceStatistic)
    total: int = 0
