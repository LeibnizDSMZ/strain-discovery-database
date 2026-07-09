import asyncio
import httpx
from typing import Final

MAX_REQUESTS_PER_SECOND: Final[int] = 40


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    params: dict,
    retries: int = 3,
    timeout: int = 200,
    /,
) -> list | dict | None:
    request_kwargs = {
        "timeout": timeout,
    }
    if headers:
        request_kwargs["headers"] = headers
    if params:
        request_kwargs["params"] = params
    for attempt in range(retries):
        try:
            response = await client.get(url, **request_kwargs)
            response.raise_for_status()
            await asyncio.sleep(1 / MAX_REQUESTS_PER_SECOND)
            return response.json()
        except httpx.HTTPStatusError as exe:
            if exe.response.status_code == 404:
                return None
            if exe.response.status_code >= 500:
                if attempt < retries - 1:
                    print(f"\nFAILED to fetch {url}")
                    await asyncio.sleep(4 * (retries + 1))
        except (httpx.RequestError, httpx.TimeoutException):
            if attempt < retries - 1:
                await asyncio.sleep(1 * (retries + 1))
            else:
                print(f"Fatal exception in fetching {url}")
                return None
    return None
