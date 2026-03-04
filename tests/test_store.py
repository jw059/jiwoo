import sqlite3

from naver_land_watcher.store import SQLiteStore


def test_store_upsert_and_get_payload(tmp_path) -> None:
    db_path = tmp_path / "watcher.db"
    store = SQLiteStore(str(db_path))
    store.init_schema()

    payload = {"articleNo": "111", "dealOrWarrantPrc": "10억"}
    store.upsert_article("111", payload)

    got = store.get_article_payload("111")
    assert got == payload

    updated = {"articleNo": "111", "dealOrWarrantPrc": "11억"}
    store.upsert_article("111", updated)
    assert store.get_article_payload("111") == updated


def test_record_alert(tmp_path) -> None:
    db_path = tmp_path / "watcher.db"
    store = SQLiteStore(str(db_path))
    store.init_schema()
    store.record_alert("123", "telegram")

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT article_no, channel FROM alerts").fetchone()
    conn.close()

    assert row == ("123", "telegram")
