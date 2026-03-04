# Naver Land New Listing Watcher (Python 3.12)

Production-ready watcher for Naver Land listings that:
- polls apartment complex listing API endpoints (no browser automation),
- detects new article IDs and meaningful updates,
- sends Telegram + Email alerts,
- stores seen listing state in SQLite.

## Features

- Monitors one or more `complexNo` targets.
- Configurable request query params (`tradeType`, area filters, price filters, etc.).
- Low-frequency polling with random jitter to avoid burst traffic.
- Retry + exponential backoff for `429` and `5xx` responses.
- SQLite persistence for listing history + sent alerts.
- Clean CLI entrypoint for one-shot or daemon mode.

## API Endpoint

The watcher uses direct JSON API calls to:

`https://new.land.naver.com/api/articles/complex/{complexNo}?tradeType=A1&page=1&type=list`

Extra query params can be injected per-complex via YAML (`extra_params`).

## Project Tree

```text
.
├── .env.example
├── config.example.yaml
├── pyproject.toml
├── README.md
├── src/naver_land_watcher/
│   ├── __init__.py
│   ├── cli.py
│   ├── client.py
│   ├── config.py
│   ├── diff_engine.py
│   ├── logging_setup.py
│   ├── models.py
│   ├── notifiers.py
│   ├── store.py
│   └── watcher.py
└── tests/
    ├── test_diff_engine.py
    └── test_store.py
```

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
cp .env.example .env
cp config.example.yaml config.yaml
```

Populate `.env` values for Telegram + SMTP.

## Configuration

`config.yaml` supports:

- `complexes`: list of monitored targets:
  - `name`: display name
  - `complex_no`: Naver complex number
  - `trade_type`: e.g. `A1`
  - `area_nos` (optional)
  - `price_min` / `price_max` (optional)
  - `extra_params` (optional key/value map passed to API)
- `poll_interval_seconds` default 120
- `jitter_seconds` default 20
- `request_timeout_seconds`
- `max_retries`
- `backoff_base_seconds`
- `detect_updates` (price/floor/confirm-date)
- `database_path`

## Run

One-shot (good for smoke test):

```bash
naver-land-watcher --config config.yaml --once
```

Daemon loop:

```bash
naver-land-watcher --config config.yaml
```

Disable channels if needed:

```bash
naver-land-watcher --config config.yaml --disable-email
naver-land-watcher --config config.yaml --disable-telegram
```

## Cron Example

For cron-driven polling every 3 minutes (instead of daemon mode):

```cron
*/3 * * * * cd /path/to/repo && /path/to/.venv/bin/naver-land-watcher --config config.yaml --once >> watcher.log 2>&1
```

## SQLite Schema

- `seen_articles(article_no PRIMARY KEY, first_seen_at, last_seen_at, last_payload_hash, payload_json)`
- `alerts(id, article_no, sent_at, channel)`

## Tests

```bash
pytest
```
