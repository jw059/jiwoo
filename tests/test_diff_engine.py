from naver_land_watcher.diff_engine import build_change, changed_fields, payload_hash
from naver_land_watcher.models import Listing


def test_payload_hash_stable() -> None:
    payload1 = {"a": 1, "b": 2}
    payload2 = {"b": 2, "a": 1}
    assert payload_hash(payload1) == payload_hash(payload2)


def test_changed_fields_only_meaningful() -> None:
    old = {"dealOrWarrantPrc": "10억", "floorInfo": "5/20", "articleConfirmYmd": "20250101", "foo": "x"}
    new = {"dealOrWarrantPrc": "11억", "floorInfo": "5/20", "articleConfirmYmd": "20250102", "foo": "y"}
    assert changed_fields(old, new) == ["dealOrWarrantPrc", "articleConfirmYmd"]


def test_build_change_new_and_update() -> None:
    listing = Listing.from_api({"articleNo": "123", "articleName": "A", "dealOrWarrantPrc": "9억"})

    new_change = build_change(listing, old_payload=None)
    assert new_change.is_new is True
    assert new_change.changed_fields == []

    updated_change = build_change(listing, old_payload={"dealOrWarrantPrc": "8억"})
    assert updated_change.is_new is False
    assert updated_change.changed_fields == ["dealOrWarrantPrc"]
