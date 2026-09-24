# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from multiprocessing.context import SpawnContext
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.queues import Queue
from ctypes import c_bool
import queue


class ClosableQueue[T]:
    __slots__ = (
        "__all_sources",
        "__closed",
        "__error",
        "__lock",
        "__queue",
        "__source_finished",
    )

    def __init__(
        self, ctx: SpawnContext, all_sources: int, error: Synchronized, /
    ) -> None:
        self.__queue: Queue[T] = ctx.Queue(10_000)
        self.__all_sources = all_sources
        self.__source_finished = ctx.Value("i", 0)
        self.__closed = ctx.Value(c_bool, False)
        self.__error = error
        self.__lock = ctx.RLock()
        self.__queue.cancel_join_thread()

    def __is_closed(self) -> bool:
        return self.__closed.value or self.__error.value

    def put(self, item: T) -> None:
        to_send = True
        while to_send:
            if self.__is_closed():
                raise ValueError("Queue is closed")
            try:
                self.__queue.put(item, timeout=2)
                to_send = False
            except queue.Full:
                pass

    def get(self) -> T:
        if not self.running:
            raise ValueError("Queue is closed and empty")
        return self.__queue.get(True, 1.0)

    def source_finished(self, name: str, /) -> None:
        with self.__lock:
            cur_loc = self.__source_finished.value + 1
            self.__source_finished.value = cur_loc
        print(f"\n{name} finished {cur_loc} / {self.__all_sources}")
        if cur_loc >= self.__all_sources:
            self.__closed.value = True

    @property
    def running(self) -> bool:
        if self.__error.value:
            return False
        return not (self.__closed.value and self.__queue.empty())

    def force_close(self) -> None:
        print("\nclosing queue forcefully\n")
        self.__closed.value = True
        self.__error.value = True
        try:
            while True:
                self.__queue.get_nowait()
        except queue.Empty:
            pass
