"""HTTP client that pages through the keyless OSDR study search API."""

import time
from typing import Any

import httpx

from osdr_explorer import OSDR_HOST

OSDR_SEARCH_URL = f"{OSDR_HOST}/osdr/data/search"
SEARCH_TYPE = "cgene"
SNAPSHOT_SOURCE = f"{OSDR_SEARCH_URL}?type={SEARCH_TYPE}"


def build_client(*, timeout: float = 30.0) -> httpx.Client:
    """Create a default httpx client with a sensible timeout."""
    return httpx.Client(timeout=timeout)


class OSDRClient:
    """Pages the OSDR search API for the full set of study records."""

    def __init__(
        self,
        client: httpx.Client,
        *,
        page_size: int = 100,
        max_retries: int = 3,
        backoff: float = 0.0,
    ) -> None:
        self._client = client
        self._page_size = page_size
        self._max_retries = max_retries
        self._backoff = backoff

    def get_page(self, offset: int) -> dict[str, Any]:
        """Fetch one page at the given offset, retrying on 5xx and transport errors."""
        params = {"term": "", "type": SEARCH_TYPE, "size": self._page_size, "from": offset}
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.get(OSDR_SEARCH_URL, params=params)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "server error", request=response.request, response=response
                    )
                response.raise_for_status()
                data: dict[str, Any] = response.json()
                return data
            except (httpx.HTTPStatusError, httpx.TransportError) as error:
                last_error = error
                if attempt < self._max_retries and self._backoff > 0:
                    time.sleep(self._backoff * (attempt + 1))
        raise RuntimeError(f"OSDR request failed after retries: {last_error}")

    def fetch_all_studies(self) -> list[dict[str, Any]]:
        """Return every study's ``_source`` dict by paging until the total is reached."""
        records: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self.get_page(offset)
            hits = page.get("hits", {})
            total_raw = hits.get("total")
            if not isinstance(total_raw, (int, float)) or isinstance(total_raw, bool):
                raise RuntimeError(f"OSDR response has no usable hits.total: {total_raw!r}")
            total = int(total_raw)
            sources = [hit["_source"] for hit in hits.get("hits", []) if "_source" in hit]
            records.extend(sources)
            offset += self._page_size
            if not sources or offset >= total:
                break
        return records
