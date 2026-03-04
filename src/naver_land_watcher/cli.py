from __future__ import annotations

import argparse

from naver_land_watcher.config import load_config
from naver_land_watcher.logging_setup import configure_logging
from naver_land_watcher.watcher import WatcherService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Naver Land listing watcher")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--once", action="store_true", help="Run one polling cycle and exit")
    parser.add_argument("--disable-telegram", action="store_true")
    parser.add_argument("--disable-email", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(args.config)
    service = WatcherService(
        config,
        enable_email=not args.disable_email,
        enable_telegram=not args.disable_telegram,
    )

    if args.once:
        service.run_once()
    else:
        service.run_forever()


if __name__ == "__main__":
    main()
