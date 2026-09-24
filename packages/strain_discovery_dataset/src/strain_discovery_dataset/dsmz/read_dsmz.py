# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT


import httpx
from strain_discovery_dataset.utils.fetch import fetch_with_retry

URL = "https://api.strains.dsmz.de/strains"


def dsmz_get_all():
    page = 0
    page_size = 1000
    total_count = 1
    with httpx.Client(timeout=100) as client:
        while page * page_size < total_count:
            page += 1
            data = fetch_with_retry(
                client, f"{URL}/?page={page}&page_size={page_size}", {}, {}
            )
            if isinstance(data, dict):
                total_count = data.get("meta", {}).get("totalCount", 0)
                for strain in data.get("data", []):
                    print(f"\r[DSMZ] {strain.get('primaryId')}{' ' * 10}", end="")
                    yield strain
            else:
                yield None
