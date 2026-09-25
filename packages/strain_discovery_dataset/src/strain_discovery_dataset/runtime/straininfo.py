# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.matching.memory import prep_run_memory
from strain_discovery_dataset.utils.data import Memory
from strain_discovery_dataset.matching.strain_matching import process_resolution_results
from strain_discovery_dataset.utils.data import Task
from strain_discovery_dataset.utils.taxa import parse_org_to_dom
from multiprocessing.synchronize import RLock
from strain_discovery_dataset.utils.run import get_cache_dir
import shutil
from typing import Final
from collections.abc import Sequence
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from microbial_strain_data_model.strain import Strain


_BATCH_SIZE: Final[int] = 1_000


CACHE_STRAININFO = "straininfo"


class StrainInfo:
    __slots__ = "__cache", "__lock", "__memory", "__queue_in", "__queue_out"

    def __init__(
        self,
        lock: RLock,
        queue_in: ClosableQueue[tuple[str, Strain]],
        queue_out: ClosableQueue[tuple[str, Strain]],
    ) -> None:
        self.__queue_in = queue_in
        self.__queue_out = queue_out
        self.__cache = get_cache_dir().joinpath(CACHE_STRAININFO)
        self.__lock = lock
        if self.__cache.exists() and self.__cache.is_file():
            raise FileExistsError(f"StrainInfo cache folder is a file {self.__cache!s}")
        if self.__cache.exists() and self.__cache.is_dir():
            shutil.rmtree(self.__cache)
        self.__cache.mkdir(parents=True, exist_ok=True)
        self.__memory: Memory | None = None
        super().__init__()

    @property
    def _memory(self) -> Memory:
        if self.__memory is None:
            self.__memory = prep_run_memory()
        return self.__memory

    def __write_cache(self, source: str, matched: Strain, origin: Strain, /) -> None:
        with self.__lock:
            si_dir = self.__cache.joinpath(matched.primaryId)
            if not si_dir.exists():
                si_dir.mkdir()
                with si_dir.joinpath("straininfo.json").open("w") as sif:
                    sif.write(matched.model_dump_json())
            with si_dir.joinpath(f"{source}_{origin.primaryId}.json").open("w") as orf:
                orf.write(origin.model_dump_json())

    def __match(self, tasks: Sequence[Task], /) -> None:
        for result in process_resolution_results(tasks, self._memory):
            if result["matched"] is None:
                self.__queue_out.put((result["source"], result["origin"]))
                continue
            self.__write_cache(result["source"], result["matched"], result["origin"])

    def __run(self) -> None:
        print("\nstraininfo started\n")
        tasks: list[Task] = []
        try:
            for source, strain in self.__queue_in.get():
                tasks.append(
                    {
                        "id": strain.primaryId,
                        "ccnos": [
                            ccno.value
                            for ccno in strain.identifier
                            if ccno.name == "CCNO"
                        ],
                        "taxon": strain.taxon[0].name if len(strain.taxon) == 1 else "",
                        "domain": parse_org_to_dom(strain.organismType),
                        "source": source,
                        "strain": strain,
                    }
                )
                if len(tasks) >= _BATCH_SIZE:
                    self.__match(tasks)
                    tasks = []

            if len(tasks) > 0:
                self.__match(tasks)
        except ValueError:
            pass
        self.__queue_out.source_finished("straininfo-matching")

    def run(self) -> None:
        try:
            self.__run()
        except Exception as err:
            self.__queue_in.force_close()
            self.__queue_out.force_close()
            print("\nfatal exception in straininfo matcher\n")
            raise err
