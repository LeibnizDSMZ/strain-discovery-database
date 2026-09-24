# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Any
from time import sleep
from httpx import Client
import httpx
import csv
import io
from strain_discovery_dataset.utils.fetch import fetch_with_retry
from itertools import islice
from typing import Iterable

_URL = "https://api.bacdive.dsmz.de/v2/fetch"
_URL_CSV = "https://bacdive.dsmz.de/advsearch/csv"


def chunked(iterable: Iterable[str], size: int) -> Iterable[list[str]]:
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


def _get_bacdive_csv(client: Client, /) -> str:
    max_retries = 3
    retry_delay = 2.0
    csv_content = None
    for attempt in range(max_retries):
        try:
            csv_response = client.get(_URL_CSV, timeout=60)
            csv_response.raise_for_status()
            csv_content = csv_response.text
            break
        except httpx.HTTPError as exc:
            if attempt == max_retries - 1:
                raise Exception(
                    f"Failed to download CSV after {max_retries} attempts: {exc}"
                )
            print(f"CSV download attempt {attempt + 1} failed, retrying...")
            sleep(retry_delay * (attempt + 1))

    if not csv_content:
        raise Exception("Failed to download CSV content")
    return csv_content


def bacdive_get_all() -> Iterable[dict[str, Any]]:
    with httpx.Client(timeout=200) as client:
        csv_content = csv.reader(io.StringIO(_get_bacdive_csv(client)))
        ids = [row[0] for row in csv_content if len(row) > 0 and row[0].isdigit()]
        for req_id in chunked(ids, 20):
            print(f"\r[BD] {req_id[0]} - {len(req_id)}{' ' * 20}", end="")
            one_url = f"{_URL}/{';'.join(req_id)}"
            data = fetch_with_retry(client, one_url, {}, {})
            if not isinstance(data, dict):
                continue
            res = data.get("results", None)
            if not isinstance(res, dict):
                continue
            for strain in res.values():
                yield strain


def bacdive_get_one(strain_id, client):
    one_url = f"{_URL}/{strain_id}"
    data = fetch_with_retry(client, one_url, {}, {})

    if not isinstance(data, dict):
        return None

    res = data.get("results", None)

    if isinstance(res, dict) and res.get(strain_id):
        return res.get(strain_id)
    else:
        print("No BacDive strain found for ID:", strain_id)
        return None
