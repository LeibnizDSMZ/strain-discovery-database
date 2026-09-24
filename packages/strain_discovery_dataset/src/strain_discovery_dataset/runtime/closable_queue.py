# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from collections.abc import Iterable
from typing import overload
from typing import Literal
from time import sleep
from multiprocessing.context import SpawnContext
from multiprocessing.queues import Queue
from ctypes import c_bool


class ClosableQueue[T]:
    __slots__ = (
        "__all_sources",
        "__closed",
        "__error",
        "__lock",
        "__max_elements",
        "__queue",
        "__source_finished",
        "__stack_size",
    )

    def __init__(
        self, ctx: SpawnContext, all_sources: int, max_elements: int = 1_000, /
    ) -> None:
        self.__queue: Queue[T] = ctx.Queue()
        self.__all_sources = all_sources
        self.__max_elements = max_elements
        self.__source_finished = ctx.Value("i", 0, lock=False)
        self.__stack_size = ctx.Value("i", 0, lock=False)
        self.__closed = ctx.Value(c_bool, False, lock=False)
        self.__error = ctx.Value(c_bool, False, lock=False)
        self.__lock = ctx.RLock()

    def __put(self, item: T) -> bool:
        with self.__lock:
            if self.__stack_size.value <= self.__max_elements:
                self.__stack_size.value += 1
                self.__queue.put(item)
                return True
        sleep(0.5)
        return False

    def put(self, item: T) -> None:
        to_send = True
        while to_send and self.__to_put():
            to_send = not self.__put(item)
        if to_send:
            raise ValueError("Queue is closed")

    @overload
    def __get(self) -> tuple[Literal[True], T]: ...
    @overload
    def __get(self) -> tuple[Literal[False], None]: ...
    def __get(self):
        with self.__lock:
            if self.__stack_size.value > 0:
                self.__stack_size.value -= 1
                return True, self.__queue.get()
        sleep(0.5)
        return False, None

    def get(self) -> Iterable[T]:
        while self.__to_get():
            received, item = self.__get()
            if received:
                yield item
        raise ValueError("Queue is closed and empty")

    def source_finished(self, name: str, /) -> None:
        with self.__lock:
            cur_loc = self.__source_finished.value + 1
            self.__source_finished.value = cur_loc
        print(f"\n{name} finished {cur_loc} / {self.__all_sources}")
        if cur_loc >= self.__all_sources:
            self.__close_queue()

    def __close_queue(self) -> None:
        with self.__lock:
            self.__closed.value = True

    def __to_put(self) -> bool:
        with self.__lock:
            if self.__error.value or self.__closed.value:
                return False
        return True

    def __to_get(self) -> bool:
        with self.__lock:
            if self.__error.value:
                return True
            return not (self.__closed.value and self.__stack_size.value == 0)

    def force_close(self) -> None:
        print("\nclosing queue forcefully\n")
        with self.__lock:
            self.__closed.value = True
            self.__error.value = True

    def has_error(self) -> bool:
        return bool(self.__error.value)
