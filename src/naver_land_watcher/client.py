from __future__ import annotations

import logging
import random
import time
from typing import Any

import requests

from naver_land_watcher.models import AppConfig, ComplexConfig, Listing

logger = logging.getLogger(__name__)


class NaverLandClient:
    BASE_URL = "https://new.land.naver.com/api/articles/complex/{complex_no}"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": config.user_agent,
                "Referer": "https://new.land.naver.com/",
            }
        )

    def fetch_listings(self, complex_config: ComplexConfig) -> list[Listing]:
        url = self.BASE_URL.format(complex_no=complex_config.complex_no)
        params = complex_config.query_params()

        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.request_timeout_seconds,
                )
            except requests.RequestException as exc:
                if attempt == self.config.max_retries:
                    raise RuntimeError(f"Request failed after retries: {exc}") from exc
                self._sleep_backoff(attempt, reason=f"network error: {exc}")
                continue

            if response.status_code == 200:
                data = response.json()
                article_list = data.get("articleList", [])
                return [Listing.from_api(item) for item in article_list if item.get("articleNo")]

            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == self.config.max_retries:
                    raise RuntimeError(
                        f"API returned {response.status_code} after {attempt} attempts"
                    )
                self._sleep_backoff(attempt, reason=f"status {response.status_code}")
                continue

            raise RuntimeError(
                f"Unexpected API status {response.status_code}: {response.text[:300]}"
            )

        return []

    def _sleep_backoff(self, attempt: int, reason: str) -> None:
        jitter = random.uniform(0, 0.7)
        seconds = self.config.backoff_base_seconds * (2 ** (attempt - 1)) + jitter
        logger.warning("Retrying after %.2fs due to %s", seconds, reason)
        time.sleep(seconds)
