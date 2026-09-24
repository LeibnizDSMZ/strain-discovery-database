# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT


from strain_discovery_dataset.matching.memory import prep_run_memory
from strain_discovery_dataset.utils.data import Memory
from collections.abc import Iterable
from strain_discovery_dataset.matching.strain_matching import process_unresolved_results
from queue import Empty
import shutil
from strain_discovery_dataset.utils.run import get_cache_dir
from microbial_strain_data_model.strain import Strain
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from multiprocessing.synchronize import RLock


CACHE_SAIM = "saim"


# IMPORTANT: Should only be one instance because of the matcher
class SaimSink:
    __slots__ = "__cache", "__lock", "__memory", "__queue"

    def __init__(self, lock: RLock, queue: ClosableQueue[tuple[str, Strain]], /) -> None:
        self.__queue = queue
        self.__cache = get_cache_dir().joinpath(CACHE_SAIM)
        self.__lock = lock
        if self.__cache.exists() and self.__cache.is_file():
            raise FileExistsError(f"SAIM cache folder is a file {self.__cache!s}")
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

    def __write_cache(self, source: str, saim_id: str, origin: Strain, /) -> None:
        with self.__lock:
            sa_dir = self.__cache.joinpath(saim_id)
            if not sa_dir.exists():
                sa_dir.mkdir()
            with sa_dir.joinpath(f"{source}_{origin.primaryId}.json").open("w") as orf:
                orf.write(origin.model_dump_json())

    def __read_from_queue(self) -> Iterable[tuple[str, Strain]]:
        try:
            while self.__queue.running:
                try:
                    yield self.__queue.get()
                except Empty:
                    pass
        except ValueError as exc:
            if self.__queue.running:
                raise exc

    def run(self) -> None:
        print("\nsaim started\n")
        try:
            for result in process_unresolved_results(
                self._memory, self.__read_from_queue()
            ):
                self.__write_cache(result["source"], result["saim"], result["origin"])
        except Exception as err:
            self.__queue.force_close()
            print("\nfatal exception in saim matcher\n")
            raise err
