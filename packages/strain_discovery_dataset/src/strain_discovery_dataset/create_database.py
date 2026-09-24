# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Any
from ctypes import c_bool
import multiprocessing
from multiprocessing.context import SpawnContext
from strain_discovery_dataset.runtime.saim import SaimSink
from strain_discovery_dataset.runtime.straininfo import StrainInfo
from strain_discovery_dataset.runtime.transform import TransformBacDive
from strain_discovery_dataset.runtime.transform import TransformMirri
from microbial_strain_data_model.strain import Strain
from strain_discovery_dataset.runtime.transform import TransformDsmz
from strain_discovery_dataset.runtime.fetch import FetchBacDive
from strain_discovery_dataset.runtime.fetch import FetchMirri
from strain_discovery_dataset.runtime.fetch import FetchDsmz
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from strain_discovery_dataset.utils.run import get_log_file
import datetime


def set_up_logs():
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


def main():
    # Use spawn context for safety (especially on macOS/Linux)
    ctx: SpawnContext = multiprocessing.get_context("spawn")
    start_time = datetime.datetime.now()
    print(f"Start time: {start_time}")

    # Shared error flag (lightweight, no Manager needed)
    error = ctx.Value(c_bool, False)
    file_lock = ctx.RLock()

    try:
        set_up_logs()

        # Shared resources

        # Queues (multiprocessing-safe)
        queue_bac: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, error)
        queue_dsmz: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, error)
        queue_mirri: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, error)
        queue_strain: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 3, error)
        queue_si: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1, error)

        # Create processes with dedicated names
        processes = [
            ctx.Process(target=FetchDsmz(file_lock, queue_dsmz).run, name="FetchDsmz"),
            ctx.Process(target=FetchMirri(file_lock, queue_mirri).run, name="FetchMirri"),
            ctx.Process(
                target=FetchBacDive(file_lock, queue_bac).run, name="FetchBacDive"
            ),
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

        # Start all processes
        for pro in processes:
            pro.start()
            print(f"Started process: {pro.name}")

        # Wait for all to finish
        for ind, pro in enumerate(processes):
            print(f"\nJoining process {ind + 1} - {pro.name}")
            pro.join()
            print(f"Joined process {ind + 1} - {pro.name}")

        end_time = datetime.datetime.now()
        print(f"Duration: {end_time - start_time}")

    except Exception as err:
        print("Main process threw an exception")
        error.value = True
        raise err

    # Optional: Check if any process failed
    if error.value:
        print("One or more processes failed.")
        exit(1)


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
