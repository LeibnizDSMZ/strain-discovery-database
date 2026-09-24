# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.dsmz.read_dsmz import dsmz_get_all
from strain_discovery_dataset.mirri.read_mirri import mirri_get_all
from strain_discovery_dataset.bacdive.read_bacdive import bacdive_get_all
from abc import abstractmethod
from abc import ABC
from multiprocessing.synchronize import RLock
from io import TextIOWrapper
from strain_discovery_dataset.utils.run import get_log_file
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from typing import Any
from collections.abc import Iterable
from typing import override


class FetchData(ABC):
    __slots__ = "__fih", "__lock", "__queue"

    def __init__(
        self,
        lock: RLock,
        queue: ClosableQueue[dict[str, Any]],
        /,
    ) -> None:
        self.__queue = queue
        self.__lock = lock
        self.__fih = None
        super().__init__()

    @property
    def _fih(self) -> TextIOWrapper:
        if self.__fih is None:
            self.__fih = get_log_file(f"{self._fetch_name}_errors").open(
                "a", encoding="utf-8"
            )
        return self.__fih

    @property
    @abstractmethod
    def _fetch_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _fetcher(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError()

    def _write(self, msg: str, fih: TextIOWrapper | None = None, /) -> None:
        new_f = fih
        if new_f is None:
            new_f = self._fih
        with self.__lock:
            new_f.write(msg)

    def run(self) -> None:
        print(f"\nfetcher {self._fetch_name} started\n")
        try:
            cnt = 0
            for strain in self._fetcher():
                self.__queue.put(strain)
                cnt += 1
            with get_log_file("numbers").open("a", encoding="utf-8") as fnu:
                self._write(f"Fetched {self._fetch_name} strains: {cnt}\n", fnu)
            self.__queue.source_finished(f"{self._fetch_name}-fetcher")
        except Exception as err:
            self.__queue.force_close()
            print(f"\nfatal exception in fetcher {self._fetch_name}\n")
            raise err
        finally:
            self._fih.close()
            print(f"\ntransformer {self._fetch_name} files closed\n")


class FetchBacDive(FetchData):
    @property
    @override
    def _fetch_name(self) -> str:
        return "bacdive"

    @override
    def _fetcher(self) -> Iterable[dict[str, Any]]:
        for data in bacdive_get_all():
            yield data


class FetchMirri(FetchData):
    @property
    @override
    def _fetch_name(self) -> str:
        return "mirri"

    @override
    def _fetcher(self) -> Iterable[dict[str, Any]]:
        for data in mirri_get_all():
            if "error" in data:
                self._write(f"{data['error']}\n")
                continue
            yield data


class FetchDsmz(FetchData):
    @property
    @override
    def _fetch_name(self) -> str:
        return "dsmz"

    @override
    def _fetcher(self) -> Iterable[dict[str, Any]]:
        for data in dsmz_get_all():
            if data is None:
                self._write("DSMZ None strain\n")
                continue
            yield data
