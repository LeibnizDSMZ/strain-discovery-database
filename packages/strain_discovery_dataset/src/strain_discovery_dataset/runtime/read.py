# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import override
from strain_discovery_dataset.runtime.saim import CACHE_SAIM
from strain_discovery_dataset.runtime.straininfo import CACHE_STRAININFO
from collections.abc import Sequence
from abc import abstractmethod
from abc import ABC
from multiprocessing.synchronize import RLock
from io import TextIOWrapper
from strain_discovery_dataset.utils.run import get_log_file
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from collections.abc import Iterable
from pathlib import Path
from microbial_strain_data_model.strain import Strain

from strain_discovery_dataset.utils.run import get_cache_dir


class ReadData(ABC):
    __slots__ = "__fih", "__lock", "__queue", "_ca_dir"

    def __init__(
        self,
        lock: RLock,
        queue: ClosableQueue[tuple[str, Sequence[Strain]]],
        /,
    ) -> None:
        self.__queue = queue
        self.__lock = lock
        self.__fih = None
        self._ca_dir: Path | None = None
        super().__init__()

    @property
    def _fih(self) -> TextIOWrapper:
        if self.__fih is None:
            self.__fih = get_log_file(f"{self._reader_name}_errors").open(
                "a", encoding="utf-8"
            )
        return self.__fih

    @property
    @abstractmethod
    def _cache(self) -> Path:
        raise NotImplementedError()

    @property
    @abstractmethod
    def _reader_name(self) -> str:
        raise NotImplementedError()

    def _read(self) -> Iterable[tuple[str, Sequence[Strain]]]:
        for str_con in self._cache.iterdir():
            if not str_con.is_dir():
                continue
            strains: list[Strain] = []
            pri_id = str_con.name
            for str_data in str_con.iterdir():
                try:
                    with str_data.open() as fst:
                        data = fst.read()
                        strain = Strain.model_validate_json(data)
                        strains.append(strain)
                except Exception as err:
                    self._write(f"Error reading {str_data}: {err}\n")
            if strains:
                yield (pri_id, strains)

    def _write(self, msg: str, fih: TextIOWrapper | None = None, /) -> None:
        new_f = fih
        if new_f is None:
            new_f = self._fih
        with self.__lock:
            new_f.write(msg)

    def run(self) -> None:
        print(f"\nreader {self._reader_name} started\n")
        try:
            cnt = 0
            for pri_id, strains in self._read():
                self.__queue.put((pri_id, strains))
                cnt += 1
            with get_log_file("numbers").open("a", encoding="utf-8") as fnu:
                self._write(f"Read {self._reader_name} strains: {cnt}\n", fnu)
            self.__queue.source_finished(f"{self._reader_name}-reader")
        except Exception as err:
            self.__queue.force_close()
            print(f"\nfatal exception in reader {self._reader_name}\n")
            raise err
        finally:
            self._fih.close()
            print(f"\nreader {self._reader_name} finished\n")


class ReadStrainInfo(ReadData):
    @property
    @override
    def _reader_name(self) -> str:
        return "straininfo"

    @property
    @override
    def _cache(self) -> Path:
        if self._ca_dir is None:
            self._ca_dir = get_cache_dir().joinpath(CACHE_STRAININFO)
        return self._ca_dir


class ReadSaim(ReadData):
    @property
    @override
    def _reader_name(self) -> str:
        return "saim"

    @property
    @override
    def _cache(self) -> Path:
        if self._ca_dir is None:
            self._ca_dir = get_cache_dir().joinpath(CACHE_SAIM)
        return self._ca_dir
