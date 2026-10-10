# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from multiprocessing.synchronize import RLock
from typing import Sequence
import argparse
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
from strain_discovery_dataset.runtime.read import ReadStrainInfo, ReadSaim
from strain_discovery_dataset.runtime.merge import MergeSink


def _valid_email(value: str) -> str:
    if "@" not in value or "." not in value.split("@")[-1]:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid email address")
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the strain discovery dataset pipeline."
    )
    parser.add_argument(
        "--contact-email",
        "-e",
        type=_valid_email,
        required=True,
        dest="email",
        help="Contact email sent along with API requests",
    )
    return parser.parse_args()


def _set_up_logs() -> None:
    date = datetime.datetime.now()
    for log_name in [
        "saim_errors",
        "straininfo_errors",
        "bacdive_errors",
        "mirri_errors",
        "dsmz_errors",
        "merge_errors",
        "mirri_validation_errors",
        "bacdive_validation_errors",
        "dsmz_validation_errors",
        "numbers",
    ]:
        with get_log_file(log_name).open("w", encoding="utf-8") as f:
            f.write(f"Date: {date}\n")


def _wrap_processes(
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


def _run_data_collection(ctx: SpawnContext, lock: RLock, email: str, /) -> None:
    """Run data collection: fetch, transform, straininfo, saim."""
    queue_bac: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1)
    queue_dsmz: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1)
    queue_mirri: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, 10_000)
    queue_strain: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 3)
    queue_si: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1)

    all_processes = [
        ctx.Process(target=FetchDsmz(lock, queue_dsmz, email).run, name="FetchDsmz"),
        ctx.Process(target=FetchMirri(lock, queue_mirri, email).run, name="FetchMirri"),
        ctx.Process(target=FetchBacDive(lock, queue_bac, email).run, name="FetchBacDive"),
        ctx.Process(
            target=TransformDsmz(lock, queue_dsmz, queue_strain).run,
            name="TransformDsmz",
        ),
        ctx.Process(
            target=TransformMirri(lock, queue_mirri, queue_strain).run,
            name="TransformMirri",
        ),
        ctx.Process(
            target=TransformBacDive(lock, queue_bac, queue_strain).run,
            name="TransformBacDive",
        ),
        ctx.Process(
            target=StrainInfo(lock, queue_strain, queue_si, email).run,
            name="StrainInfo",
        ),
        ctx.Process(target=SaimSink(lock, queue_si).run, name="SaimSink"),
    ]

    all_queues: list[ClosableQueue[Any]] = [
        queue_bac,
        queue_dsmz,
        queue_mirri,
        queue_strain,
        queue_si,
    ]
    _wrap_processes(all_processes, all_queues)


def _run_cache_merge(ctx: SpawnContext, lock: RLock, /) -> None:

    # Calculate number of merge processes (half of CPU or at least 1)
    num_join = max(1, multiprocessing.cpu_count() // 2)

    # Create queue for merge input (sized for readers + merge processes)
    queue_merge: ClosableQueue[tuple[str, Sequence[Strain]]] = ClosableQueue(ctx, 2)

    # Start reader processes
    readers = [
        ctx.Process(target=ReadStrainInfo(lock, queue_merge).run, name="ReadStrainInfo"),
        ctx.Process(target=ReadSaim(lock, queue_merge).run, name="ReadSaim"),
    ]

    # Start merge processes
    all_processes = readers + [
        ctx.Process(target=MergeSink(lock, queue_merge).run, name="MergeSink")
        for _ in range(num_join)
    ]
    _wrap_processes(all_processes, [queue_merge])


def main() -> None:
    ctx: SpawnContext = multiprocessing.get_context("spawn")
    start_time = datetime.datetime.now()
    args = _parse_args()
    print(f"Start time: {start_time}")

    file_lock = ctx.RLock()
    _set_up_logs()

    # Run data collection (fetch, transform, straininfo, saim)
    _run_data_collection(ctx, file_lock, args.email)

    # Run cache merge (read cached data and write to MongoDB)
    _run_cache_merge(ctx, file_lock)

    end_time = datetime.datetime.now()
    print(f"\nDuration: {end_time - start_time}\n")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
