# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import AsyncGenerator
from typing import Any
import httpx
from strain_discovery_dataset.utils.fetch import fetch_with_retry

_URL = "https://webservices.bio-aware.com/mirri_new/public/strains"

_HEADERS = {"Accept": "application/links+json"}


async def mirri_get_all() -> AsyncGenerator[dict[str, Any]]:
    page = 1
    seen_ids = set()
    page_size = 500
    params = {
        "page": 1,
        "pageSize": page_size,
        "sortBy": "creationDate",
        "sortDir": "asc",
    }

    async with httpx.AsyncClient(timeout=200) as client:
        while (
            data := await fetch_with_retry(client, _URL, _HEADERS, params)
        ) is not None:
            if not isinstance(data, dict):
                print("API response is not 200")
                yield {"error": f"API response for mirri id {page} is not 200"}
                break
            new_items = data.get("items")
            if not isinstance(new_items, list):
                yield {"error": f"API response for mirri id {page} has no items"}
                break
            for item in new_items:
                item_id = item.get("id")
                if (
                    isinstance(item_id, str) or isinstance(item_id, int)
                ) and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    yield item
            if len(new_items) < page_size:
                break

            page += 1
            params["page"] = page


async def mirri_get_one(strain_id) -> dict | None:
    one_url = f"{_URL}/{strain_id}"

    async with httpx.AsyncClient(timeout=100) as client:
        data = await fetch_with_retry(client, one_url, _HEADERS, {})

    if data is None:
        print("API response is not 200")
        return None

    # pyrefly: ignore [bad-return]
    return data
