from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ComplexConfig:
    name: str
    complex_no: str
    trade_type: str = "A1"
    area_nos: list[str] = field(default_factory=list)
    price_min: int | None = None
    price_max: int | None = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    def query_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "tradeType": self.trade_type,
            "page": 1,
            "type": "list",
        }
        if self.area_nos:
            params["areaNos"] = ",".join(self.area_nos)
        if self.price_min is not None:
            params["priceMin"] = self.price_min
        if self.price_max is not None:
            params["priceMax"] = self.price_max
        params.update(self.extra_params)
        return params


@dataclass(slots=True)
class AppConfig:
    complexes: list[ComplexConfig]
    poll_interval_seconds: int = 120
    jitter_seconds: int = 20
    request_timeout_seconds: int = 10
    max_retries: int = 4
    backoff_base_seconds: float = 1.5
    detect_updates: bool = True
    database_path: str = "./watcher.db"
    user_agent: str = "Mozilla/5.0"


@dataclass(slots=True)
class Listing:
    article_no: str
    article_name: str
    deal_or_warrant_prc: str | None
    floor_info: str | None
    area_name: str | None
    direction: str | None
    article_confirm_ymd: str | None
    realtor_name: str | None
    raw: dict[str, Any]

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Listing":
        return cls(
            article_no=str(payload.get("articleNo", "")),
            article_name=str(payload.get("articleName", "")),
            deal_or_warrant_prc=payload.get("dealOrWarrantPrc"),
            floor_info=payload.get("floorInfo"),
            area_name=payload.get("areaName"),
            direction=payload.get("direction"),
            article_confirm_ymd=payload.get("articleConfirmYmd"),
            realtor_name=payload.get("realtorName"),
            raw=payload,
        )


@dataclass(slots=True)
class ListingChange:
    listing: Listing
    is_new: bool
    changed_fields: list[str]
    detected_at: datetime

    @property
    def is_meaningful_update(self) -> bool:
        return (not self.is_new) and bool(self.changed_fields)
