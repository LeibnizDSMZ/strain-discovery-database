# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Sequence
import multiprocessing
from typing import Any

from strain_discovery_dataset.runtime.closable_queue import ClosableQueue


def wrap_processes(
    all_processes: Sequence[multiprocessing.context.SpawnProcess],
    all_queues: Sequence[ClosableQueue[Any]],
    /,
) -> None:
    try:
        for pro in all_processes:
            pro.start()
            print(f"\nStarted process: {pro.name}\n")

        error_broadcasted = False
        alive = len(all_processes)
        while not error_broadcasted and alive > 0:
            alive = len(all_processes)
            for idx, pro in enumerate(all_processes):
                print(
                    f"\rJoining process {idx + 1}/{len(all_processes)} {pro.name}{' ' * 10}",
                    end="",
                )
                pro.join(timeout=1.5)
                alive -= 0 if pro.is_alive() else 1
                if error_broadcasted:
                    continue

                if any(que.has_error() for que in all_queues):
                    print("\nDetected an error broadcasting shutdown\n")
                    for pro in all_processes:
                        if pro.is_alive():
                            pro.terminate()
                    error_broadcasted = True

        for pro in all_processes:
            if pro.is_alive():
                print(f"\nWaiting for {pro.name} to finish (no timeout)...\n")
                pro.join()
            print(f"\nJoined - {pro.name}\n")

    except Exception as exc:
        print(f"\nMain process raised an exception: {exc!r}\n")
        for pro in all_processes:
            if pro.is_alive():
                pro.terminate()
        raise
