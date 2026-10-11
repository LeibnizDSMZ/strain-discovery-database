# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

"""Confusion matrix analysis for strain prediction.

WARNING: This module only works correctly for recrafting strains from a single source.
When multiple sources are involved, statistics are corrupted because two strains from
different sources could be the same, but only one is selected as the truth for
the strain container. This leads to inaccurate accuracy metrics.
"""

from collections import Counter
from microbial_strain_data_model.strain import Strain
from collections.abc import Sequence
from multiprocessing.synchronize import RLock
from io import TextIOWrapper
from strain_discovery_dataset.utils.run import get_log_file
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
import re


def _select_tag(group: list[str], tags: set[str], /) -> str | None:
    for tag in sorted(Counter(tag for tag in group), reverse=True):
        if tag in tags:
            tags.remove(tag)
            return tag
    return None


def _assign_tag(
    ord_str: dict[int, dict[str, list[str]]], tags: set[str], /
) -> dict[str, str]:
    predicted: dict[str, str] = {}
    for _, strains in sorted(ord_str.items(), reverse=True):
        for ori, group in strains.items():
            selected = _select_tag(group, tags)
            if selected is not None:
                predicted[selected] = ori
    return predicted


def _create_confusion_matrix(
    ord_str: dict[int, dict[str, list[str]]], pred: dict[str, str], /
) -> dict[str, int]:
    keys = (
        f"{ori}_to_{pred.get(pre_id, 'UNKNOWN')}"
        for strains in ord_str.values()
        for ori, group in strains.items()
        for pre_id in group
    )
    return dict(Counter(keys))


def _confusion_report(matrix: dict[str, int], /) -> tuple[int, str]:
    if not matrix:
        return 0, "Confusion Matrix (empty)"

    total = sum(matrix.values())
    correct = sum(
        count for key, count in matrix.items() if (ids := key.split("_to_"))[0] == ids[1]
    )

    lines = [
        "Confusion Matrix (real_predicted):",
        f"  Total predictions: {total}",
        f"  Correct predictions: {correct}",
        f"  Accuracy: {correct / total:.4f}" if total > 0 else "  Accuracy: N/A",
        "",
        "Breakdown:",
    ]

    for key, count in sorted(matrix.items()):
        lines.append(f"  {key}: {count}")

    return total, "\n".join(lines)


_ID = re.compile(r"^(.+)_(\d+)_(\d+)$")


class ConfusionSink:
    __slots__ = "__ca_ids", "__ca_str", "__fih", "__lock", "__min_size", "__queue"

    def __init__(
        self,
        lock: RLock,
        queue: ClosableQueue[tuple[str, Sequence[Strain]]],
        min_size: int = 1,
        /,
    ) -> None:
        self.__queue = queue
        self.__lock = lock
        self.__fih = None
        self.__ca_ids: set[str] = set()
        self.__ca_str: dict[int, dict[str, list[str]]] = {}
        self.__min_size = min_size
        super().__init__()

    @property
    def _fih(self) -> TextIOWrapper:
        if self.__fih is None:
            self.__fih = get_log_file("confusion_errors").open("a", encoding="utf-8")
        return self.__fih

    def _process(self, pri_id: str, strains: Sequence[Strain], /) -> None:
        self.__ca_ids.add(pri_id)
        for strain in strains:
            mat = _ID.search(strain.primaryId)
            if mat is None:
                continue
            siz = int(mat.group(3))
            if siz < self.__min_size:
                continue
            if siz not in self.__ca_str:
                self.__ca_str[siz] = {}
            if mat.group(1) not in self.__ca_str[siz]:
                self.__ca_str[siz][mat.group(1)] = []
            self.__ca_str[siz][mat.group(1)].append(pri_id)

    def _write(self, msg: str, fih: TextIOWrapper | None = None, /) -> None:
        new_f = fih
        if new_f is None:
            new_f = self._fih
        with self.__lock:
            new_f.write(msg)

    def __run(self) -> None:
        total, matrix = 0, ""
        try:
            for pri_id, strains in self.__queue.get():
                self._process(pri_id, strains)
            total, matrix = _confusion_report(
                _create_confusion_matrix(
                    self.__ca_str, _assign_tag(self.__ca_str, self.__ca_ids)
                )
            )
        except ValueError:
            pass
        with get_log_file("numbers").open("a", encoding="utf-8") as fnu:
            self._write(f"Strains analyzed for confusion matrix: {total}\n", fnu)
        with get_log_file("confusion_matrix").open("a", encoding="utf-8") as fco:
            self._write(matrix, fco)
        self.__queue.source_finished("confusion")

    def run(self) -> None:
        print("\nconfusion matrix creation started\n")
        try:
            self.__run()
        except Exception as err:
            self.__queue.force_close()
            print("\nfatal exception in confusion matrix creation\n")
            raise err
        finally:
            self._fih.close()
            print("\nconfusion matrix creation - files closed\n")
