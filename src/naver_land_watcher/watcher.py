from __future__ import annotations

import logging
import random
import time

from naver_land_watcher.client import NaverLandClient
from naver_land_watcher.diff_engine import build_change
from naver_land_watcher.models import AppConfig
from naver_land_watcher.notifiers import EmailNotifier, TelegramNotifier
from naver_land_watcher.store import SQLiteStore

logger = logging.getLogger(__name__)


class WatcherService:
    def __init__(self, config: AppConfig, enable_email: bool = True, enable_telegram: bool = True) -> None:
        self.config = config
        self.client = NaverLandClient(config)
        self.store = SQLiteStore(config.database_path)
        self.telegram = TelegramNotifier() if enable_telegram else None
        self.email = EmailNotifier() if enable_email else None

    def run_forever(self) -> None:
        self.store.init_schema()
        while True:
            self.run_once()
            sleep_seconds = self.config.poll_interval_seconds + random.uniform(
                -self.config.jitter_seconds, self.config.jitter_seconds
            )
            sleep_seconds = max(20, sleep_seconds)
            logger.info("Sleeping %.1fs before next poll", sleep_seconds)
            time.sleep(sleep_seconds)

    def run_once(self) -> None:
        self.store.init_schema()
        for complex_config in self.config.complexes:
            logger.info("Polling complex %s (%s)", complex_config.name, complex_config.complex_no)
            listings = self.client.fetch_listings(complex_config)
            logger.info("Fetched %s listings for %s", len(listings), complex_config.name)

            for listing in listings:
                old_payload = self.store.get_article_payload(listing.article_no)
                change = build_change(listing, old_payload)

                should_alert = change.is_new or (
                    self.config.detect_updates and change.is_meaningful_update
                )
                self.store.upsert_article(listing.article_no, listing.raw)

                if should_alert:
                    self._notify_all(change, complex_config.name)

    def _notify_all(self, change, complex_name: str) -> None:
        if self.telegram:
            try:
                self.telegram.send(change, complex_name)
                self.store.record_alert(change.listing.article_no, "telegram")
            except Exception as exc:
                logger.exception("Telegram alert failed: %s", exc)

        if self.email:
            try:
                self.email.send(change, complex_name)
                self.store.record_alert(change.listing.article_no, "email")
            except Exception as exc:
                logger.exception("Email alert failed: %s", exc)
