# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from multiprocessing.synchronize import RLock
from io import TextIOWrapper
from strain_discovery_dataset.utils.run import get_log_file
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from collections.abc import Iterable
from microbial_strain_data_model.strain import Strain


def _create_copies(strain: str, num_copies: int, /) -> Iterable[Strain]:
    for ind in range(1, num_copies + 1):
        new_strain = Strain.model_validate_json(strain)
        new_strain.primaryId = f"{new_strain.primaryId}_{ind}_{num_copies}"
        yield new_strain


def _split(source: str, strain: Strain) -> Iterable[tuple[str, Strain]]:
    ccno_identifiers = [
        identifier for identifier in strain.identifier if identifier.name == "CCNO"
    ]

    if len(ccno_identifiers) == 0:
        strain.primaryId = f"{strain.primaryId}_1_1"
        yield (source, strain)
    else:
        origin = strain.model_dump_json()
        num_copies = len(ccno_identifiers)
        for cp_str in _create_copies(origin, num_copies):
            yield (source, cp_str)


class SplitData:
    __slots__ = "__fih", "__lock", "__queue_in", "__queue_out"

    def __init__(
        self,
        lock: RLock,
        queue_in: ClosableQueue[tuple[str, Strain]],
        queue_out: ClosableQueue[tuple[str, Strain]],
        /,
    ) -> None:
        self.__queue_in = queue_in
        self.__queue_out = queue_out
        self.__lock = lock
        self.__fih = None
        super().__init__()

    @property
    def _fih(self) -> TextIOWrapper:
        if self.__fih is None:
            self.__fih = get_log_file("split_errors").open("a", encoding="utf-8")
        return self.__fih

    def _write(self, msg: str, fih: TextIOWrapper | None = None, /) -> None:
        new_f = fih
        if new_f is None:
            new_f = self._fih
        with self.__lock:
            new_f.write(msg)

    def __run(self) -> None:
        cnt = 0
        try:
            for source, strain in self.__queue_in.get():
                for source_out, new_strain in _split(source, strain):
                    self.__queue_out.put((source_out, new_strain))
                    cnt += 1
        except ValueError:
            pass
        with get_log_file("numbers").open("a", encoding="utf-8") as fnu:
            self._write(f"Split strains: {cnt}\n", fnu)
        self.__queue_out.source_finished("splitter")

    def run(self) -> None:
        print("\nsplitter started\n")
        try:
            self.__run()
        except Exception as err:
            self.__queue_out.force_close()
            self.__queue_in.force_close()
            print("\nfatal exception in splitter\n")
            raise err
        finally:
            self._fih.close()
            print("\nsplitter files closed\n")
