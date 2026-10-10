# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Any
from pymongo.collection import Collection
from collections.abc import Sequence
from collections.abc import Iterable
from datetime import datetime
from multiprocessing.synchronize import RLock

from microbial_strain_data_model.strain import Strain
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from strain_discovery_dataset.utils.mongo import get_sdd_collection


class MergeSink:
    __slots__ = "__lock", "__mongo", "__queue"

    def __init__(
        self,
        lock: RLock,
        queue: ClosableQueue[tuple[str, Sequence[Strain]]],
        /,
    ) -> None:
        self.__queue = queue
        self.__lock = lock
        self.__mongo: Collection[dict[str, Any]] = None
        super().__init__()

    @property
    def _mongo(self) -> Collection[dict[str, Any]]:
        if self.__mongo is None:
            self.__mongo = get_sdd_collection()
        return self.__mongo

    def __read_from_queue(self) -> Iterable[tuple[str, Sequence[Strain]]]:
        try:
            for item in self.__queue.get():
                yield item
        except ValueError:
            pass

    def _join(self, pri: str, strains: Sequence[Strain], /) -> None:
        merged_strain = strains[0]
        merged_strain.primaryId = pri

        # Join remaining strains onto core
        for strain in strains[1:]:
            if strain.primaryId == "":
                continue
            merged_strain.join(strain)

        # Write final merged strain to MongoDB
        with self.__lock:
            self._mongo.insert_one(merged_strain.model_dump(mode="json"))

    def run(self) -> None:
        print("\nmerge started\n")
        start_time = datetime.now()
        total_strains = 0
        merged_count = 0

        try:
            for source, strains in self.__read_from_queue():
                if not strains or (prim_id := strains[0].primaryId) == "":
                    continue
                total_strains += len(strains)
                merged_count += 1
                self._join(prim_id, strains)
        except Exception as err:
            self.__queue.force_close()
            print("\nfatal exception in merge matcher\n")
            raise err

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(
            f"\nmerge finished: {total_strains} strains merged to {merged_count} IDs in {duration:.2f}s\n"
        )
