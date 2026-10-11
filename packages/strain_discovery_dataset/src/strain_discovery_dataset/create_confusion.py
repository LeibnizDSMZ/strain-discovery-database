# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from strain_discovery_dataset.runtime.confusion import ConfusionSink
from strain_discovery_dataset.utils.process import wrap_processes
from strain_discovery_dataset.runtime.split import SplitData
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
)
from strain_discovery_dataset.runtime.fetch import (
    FetchBacDive,
)
from strain_discovery_dataset.runtime.closable_queue import ClosableQueue
from strain_discovery_dataset.runtime.read import ReadStrainInfo, ReadSaim


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
    parser.add_argument(
        "--min-size",
        "-l",
        type=int,
        default=1,
        dest="min_size",
        help="Minimum strain size to include in confusion matrix analysis",
    )
    return parser.parse_args()


def _run_data_collection(ctx: SpawnContext, lock: RLock, email: str, /) -> None:
    queue_bac: ClosableQueue[dict[str, Any]] = ClosableQueue(ctx, 1, 10_000)
    queue_split: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1)
    queue_strain: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1)
    queue_si: ClosableQueue[tuple[str, Strain]] = ClosableQueue(ctx, 1)

    all_processes = [
        ctx.Process(target=FetchBacDive(lock, queue_bac, email).run, name="FetchBacDive"),
        ctx.Process(
            target=TransformBacDive(lock, queue_bac, queue_split).run,
            name="TransformBacDive",
        ),
        ctx.Process(
            target=SplitData(lock, queue_split, queue_strain).run,
            name="SplitStrains",
        ),
        ctx.Process(
            target=StrainInfo(lock, queue_strain, queue_si, email).run,
            name="StrainInfo",
        ),
        ctx.Process(target=SaimSink(lock, queue_si).run, name="SaimSink"),
    ]

    all_queues: list[ClosableQueue[Any]] = [
        queue_bac,
        queue_split,
        queue_strain,
        queue_si,
    ]
    wrap_processes(all_processes, all_queues)


def _run_cache_merge(ctx: SpawnContext, lock: RLock, min_size: int, /) -> None:

    # Create queue for merge input (sized for readers + merge processes)
    queue_statistic: ClosableQueue[tuple[str, Sequence[Strain]]] = ClosableQueue(ctx, 2)

    all_processes = [
        ctx.Process(
            target=ReadStrainInfo(lock, queue_statistic).run, name="ReadStrainInfo"
        ),
        ctx.Process(target=ReadSaim(lock, queue_statistic).run, name="ReadSaim"),
        ctx.Process(
            target=ConfusionSink(lock, queue_statistic, min_size).run,
            name="ConfusionSink",
        ),
    ]

    wrap_processes(all_processes, [queue_statistic])


def main() -> None:
    ctx: SpawnContext = multiprocessing.get_context("spawn")
    start_time = datetime.datetime.now()
    args = _parse_args()
    print(f"Start time: {start_time}")

    file_lock = ctx.RLock()

    # Run data collection (fetch, transform, straininfo, saim)
    _run_data_collection(ctx, file_lock, args.email)

    # Run cache merge (read cached data and write to MongoDB)
    _run_cache_merge(ctx, file_lock, args.min_size)

    end_time = datetime.datetime.now()
    print(f"\nDuration: {end_time - start_time}\n")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
