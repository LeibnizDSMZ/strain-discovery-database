# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ‑German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from microbial_strain_data_model.strain import Strain
import datetime
import multiprocessing
from multiprocessing.context import SpawnContext
from typing import Any

from strain_discovery_dataset.runtime.saim import SaimSink
from strain_discovery_dataset.runtime.straininfo import StrainInfo
from strain_discovery_dataset.runtime.transform import (
    TransformBacDive,
    TransformDsmz,
    TransformMirri,
)
from strain_discovery_dataset.runtime.fetch import (
    FetchBacDive,
    FetchDsmz,
    FetchMirri,
)
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from strain_discovery_dataset.utils.run import get_log_file


def set_up_logs() -> None:
    date = datetime.datetime.now()
    for log_name in [
        "bacdive_errors",
        "mirri_errors",
        "dsmz_errors",
        "merge_errors",
        "mirri_validation_errors",
        "bacdive_validation_errors",
        "numbers",
    ]:
        with get_log_file(log_name).open("w", encoding="utf-8") as f:
            f.write(f"Date: {date}\n")


def main() -> None:
    ctx: SpawnContext = multiprocessing.get_context("spawn")
    start_time = datetime.datetime.now()
    print(f"Start time: {start_time}")

    file_lock = ctx.RLock()
    set_up_logs()

    queue_bac: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1)
    queue_dsmz: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1)
    queue_mirri: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, 10_000)
    queue_strain: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 3)
    queue_si: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1)

    processes = [
        ctx.Process(target=FetchDsmz(file_lock, queue_dsmz).run, name="FetchDsmz"),
        ctx.Process(target=FetchMirri(file_lock, queue_mirri).run, name="FetchMirri"),
        ctx.Process(target=FetchBacDive(file_lock, queue_bac).run, name="FetchBacDive"),
        ctx.Process(
            target=TransformDsmz(file_lock, queue_dsmz, queue_strain).run,
            name="TransformDsmz",
        ),
        ctx.Process(
            target=TransformMirri(file_lock, queue_mirri, queue_strain).run,
            name="TransformMirri",
        ),
        ctx.Process(
            target=TransformBacDive(file_lock, queue_bac, queue_strain).run,
            name="TransformBacDive",
        ),
        ctx.Process(
            target=StrainInfo(file_lock, queue_strain, queue_si).run,
            name="StrainInfo",
        ),
        ctx.Process(target=SaimSink(file_lock, queue_si).run, name="SaimSink"),
    ]

    all_queues: list[ClosableQueue[Any]] = [
        queue_bac,
        queue_dsmz,
        queue_mirri,
        queue_strain,
        queue_si,
    ]

    try:
        for pro in processes:
            pro.start()
            print(f"\nStarted process: {pro.name}\n")

        error_broadcasted = False
        alive = len(processes)
        while not error_broadcasted and alive > 0:
            alive = len(processes)
            for idx, pro in enumerate(processes):
                print(
                    f"\rJoining process {idx + 1}/{len(processes)} {pro.name}{' ' * 10}",
                    end="",
                )
                pro.join(timeout=1.5)
                alive -= 0 if pro.is_alive() else 1
                if error_broadcasted:
                    continue

                if any(que.has_error() for que in all_queues):
                    print("\nDetected an error broadcasting shutdown\n")
                    for pro in processes:
                        if pro.is_alive():
                            pro.terminate()
                    error_broadcasted = True

        for pro in processes:
            if pro.is_alive():
                print(f"\nWaiting for {pro.name} to finish (no timeout)...\n")
                pro.join()
            print(f"\nJoined - {pro.name}\n")

        end_time = datetime.datetime.now()
        print(f"\nDuration: {end_time - start_time}\n")

    except Exception as exc:
        print(f"\nMain process raised an exception: {exc!r}\n")
        for pro in processes:
            if pro.is_alive():
                pro.terminate()
        raise


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
