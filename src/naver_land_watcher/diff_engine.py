from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from naver_land_watcher.models import Listing, ListingChange

MEANINGFUL_FIELDS = (
    "dealOrWarrantPrc",
    "floorInfo",
    "articleConfirmYmd",
)


def payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def changed_fields(old_payload: dict, new_payload: dict) -> list[str]:
    fields: list[str] = []
    for field in MEANINGFUL_FIELDS:
        if old_payload.get(field) != new_payload.get(field):
            fields.append(field)
    return fields


def build_change(listing: Listing, old_payload: dict | None) -> ListingChange:
    now = datetime.now(timezone.utc)
    if old_payload is None:
        return ListingChange(listing=listing, is_new=True, changed_fields=[], detected_at=now)
    return ListingChange(
        listing=listing,
        is_new=False,
        changed_fields=changed_fields(old_payload, listing.raw),
        detected_at=now,
    )
