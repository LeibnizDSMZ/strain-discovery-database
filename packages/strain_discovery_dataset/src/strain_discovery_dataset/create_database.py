from strain_discovery_dataset.utils.run import get_log_file
from strain_discovery_dataset.utils.mongo import get_sdd_collection
import json
import asyncio
import datetime

from strain_discovery_dataset.bacdive import read_bacdive, transformation_bacdive
from strain_discovery_dataset.matching.strain_matching import (
    match_strains_from_queue,
)
from strain_discovery_dataset.mirri import read_mirri, transformation_mirri
from strain_discovery_dataset.dsmz import read_dsmz
from microbial_strain_data_model.strain import Strain
import traceback


async def get_all_bacdive(queue: asyncio.Queue) -> None:
    print("Start Bacdive all")
    cnt = 0
    with get_log_file("bacdive_errors").open("a", encoding="utf-8") as fbd:
        async for strain in read_bacdive.bacdive_get_all():
            if strain is None:
                fbd.write("Received None for a strain\n")
                continue
            else:
                try:
                    tranformed_data = transformation_bacdive.transform(strain)
                except Exception as e:
                    fbd.write(
                        "Error transforming strain "
                        + f"{strain.get('General').get('BacDive-ID')}: {e}\n"
                        + f"Traceback:\n{traceback.format_exc()}\n"
                        + f"{'=' * 80}\n"
                    )
                    continue

            if tranformed_data is not None:
                await queue.put(tranformed_data)
                cnt += 1

    with get_log_file("numbers").open("a", encoding="utf-8") as fn:
        fn.write(f"Transformed BacDive strains: {cnt}\n")

    print(f"\nBacDive strains {cnt}\n")
    await queue.put(None)


async def get_all_mirri(queue: asyncio.Queue) -> None:
    print("Start MIRRI all")
    cnt = 0
    with get_log_file("mirri_errors").open("a", encoding="utf-8") as fmi:
        async for strain in read_mirri.mirri_get_all():
            if "error" in strain:
                fmi.write(f"{strain['error']}\n")
                continue
            else:
                try:
                    tranformed_data = transformation_mirri.transform(strain)
                except Exception as e:
                    fmi.write(
                        f"Error transforming strain {strain.get('name')}: {e}\n"
                        + f"Traceback:\n{traceback.format_exc()}\n"
                        + f"{'=' * 80}\n"
                    )
                    continue
            if tranformed_data is not None:
                await queue.put(tranformed_data)
                cnt += 1

    with get_log_file("numbers").open("a", encoding="utf-8") as fn:
        fn.write(f"Transformed MIRRI strains: {cnt}\n")

    print(f"\nMirri strains {cnt}\n")
    await queue.put(None)


async def get_all_dsmz(queue: asyncio.Queue) -> None:
    print("Start DSMZ all")
    cnt = 0
    with get_log_file("dsmz_errors").open("a", encoding="utf-8") as fds:
        async for strain in read_dsmz.dsmz_get_all():
            if strain is None:
                fds.write("Received None for a strain\n")
                continue
            else:
                try:
                    tranformed_data = Strain.model_validate_json(json.dumps(strain))
                except Exception as e:
                    fds.write(
                        f"Error transforming strain {strain.get('primaryId')}: {e}\n"
                        + f"Traceback:\n{traceback.format_exc()}\n"
                        + f"{'=' * 80}\n"
                    )
                    continue

            if tranformed_data is not None:
                await queue.put(tranformed_data)
                cnt += 1
    with get_log_file("numbers").open("a", encoding="utf-8") as fn:
        fn.write(f"Valid DSMZ strains: {cnt}\n")
    print(f"\nDSMZ strains {cnt}\n")
    await queue.put(None)


def set_up_logs():
    date = datetime.datetime.now()
    with get_log_file("bacdive_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("mirri_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("dsmz_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("merge_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("mirri_validation_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("bacdive_validation_errors").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")

    with get_log_file("numbers").open("w", encoding="utf-8") as f:
        f.write(f"Date: {date}\n")


async def _run():
    set_up_logs()

    start_time = datetime.datetime.now()
    print(f"Start time: {start_time}")

    queue = asyncio.Queue(15_000)

    tasks = [
        asyncio.create_task(get_all_bacdive(queue)),
        asyncio.create_task(get_all_mirri(queue)),
        asyncio.create_task(get_all_dsmz(queue)),
    ]

    # Example of further processing
    matched_strains = await match_strains_from_queue(queue, len(tasks))
    for task in tasks:
        await task
    # Write matched strains to MongoDB
    mongo_collection = get_sdd_collection()

    for strain in matched_strains.values():
        mongo_collection.insert_one(strain.model_dump(mode="json"))

    end_time = datetime.datetime.now()
    print(f"Duration: {end_time - start_time}")


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
