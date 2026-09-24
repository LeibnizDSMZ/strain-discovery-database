# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.dsmz.transformation_dsmz import transform_dsmz
from strain_discovery_dataset.mirri.transformation_mirri import transform_mirri
from strain_discovery_dataset.bacdive.transformation_bacdive import transform_bacdive
from pydantic import ValidationError
from abc import ABC
from abc import abstractmethod
import traceback
from multiprocessing.synchronize import RLock
from strain_discovery_dataset.utils.run import get_log_file
from io import TextIOWrapper
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from typing import Any
from microbial_strain_data_model.strain import Strain
from typing import override


class TransformData(ABC):
    __slots__ = (
        "__file_err",
        "__file_val_err",
        "__lock",
        "__queue_in",
        "__queue_out",
    )

    def __init__(
        self,
        lock: RLock,
        queue_in: ClosableQueue[dict[str, Any]],
        queue_out: ClosableQueue[tuple[str, Strain]],
        /,
    ) -> None:
        self.__queue_in = queue_in
        self.__queue_out = queue_out
        self.__lock = lock
        self.__file_err = None
        self.__file_val_err = None
        super().__init__()

    @property
    def _file_err(self) -> TextIOWrapper:
        if self.__file_err is None:
            self.__file_err = get_log_file(f"{self._transform_name}_errors").open(
                "a", encoding="utf-8"
            )
        return self.__file_err

    @property
    def _file_val_err(self) -> TextIOWrapper:
        if self.__file_val_err is None:
            self.__file_val_err = get_log_file(
                f"{self._transform_name}_validation_errors"
            ).open("a", encoding="utf-8")
        return self.__file_val_err

    @property
    @abstractmethod
    def _transform_name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _transformer(self, data: dict[str, Any], /) -> Strain | None:
        raise NotImplementedError()

    @abstractmethod
    def _get_id(self, data: dict[str, Any], /) -> Strain | None:
        raise NotImplementedError()

    def __write(self, msg: str, fih: TextIOWrapper, /) -> None:
        with self.__lock:
            fih.write(msg)

    def __transform(self, data: dict[str, Any], /) -> None | Strain:
        results = None
        try:
            results = self._transformer(data)
        except (ValidationError, ValueError, TypeError) as val_e:
            self.__write(
                f"Validation failed {self._get_id(data)}\n" + f"{val_e}\n",
                self._file_val_err,
            )
        except Exception as unk_e:
            self.__write(
                "Error transforming strain "
                + f"{self._get_id(data)}: {unk_e}\n"
                + f"Traceback:\n{traceback.format_exc()}\n"
                + f"{'=' * 80}\n",
                self._file_err,
            )
        return results

    def __run(self) -> None:
        cnt = 0
        try:
            for data in self.__queue_in.get():
                strain = self.__transform(data)
                if strain is not None:
                    self.__queue_out.put((self._transform_name, strain))
                    cnt += 1
        except ValueError:
            pass
        with get_log_file("numbers").open("a", encoding="utf-8") as fnu:
            self.__write(f"Transformed {self._transform_name} strains: {cnt}\n", fnu)
        self.__queue_out.source_finished(f"{self._transform_name}-transformer")

    def run(self) -> None:
        print(f"\ntransformer {self._transform_name} started\n")
        try:
            self.__run()
        except Exception as err:
            self.__queue_out.force_close()
            self.__queue_in.force_close()
            print(f"\nfatal exception in transformer {self._transform_name}\n")
            raise err
        finally:
            self._file_err.close()
            self._file_val_err.close()
            print(f"\ntransformer {self._transform_name} files closed\n")


class TransformBacDive(TransformData):
    @property
    @override
    def _transform_name(self) -> str:
        return "bacdive"

    @override
    def _transformer(self, data: dict[str, Any], /) -> Strain | None:
        return transform_bacdive(data)

    @override
    def _get_id(self, data: dict[str, Any], /) -> Strain | None:
        return data.get("General", {}).get("BacDive-ID", "UNKNOWN")


class TransformMirri(TransformData):
    @property
    @override
    def _transform_name(self) -> str:
        return "mirri"

    @override
    def _transformer(self, data: dict[str, Any], /) -> Strain | None:
        return transform_mirri(data)

    @override
    def _get_id(self, data: dict[str, Any], /) -> Strain | None:
        return data.get("name", "UNKNOWN")


class TransformDsmz(TransformData):
    @property
    @override
    def _transform_name(self) -> str:
        return "dsmz"

    @override
    def _transformer(self, data: dict[str, Any], /) -> Strain | None:
        return transform_dsmz(data)

    @override
    def _get_id(self, data: dict[str, Any], /) -> Strain | None:
        return data.get("primaryId", "UNKNOWN")
