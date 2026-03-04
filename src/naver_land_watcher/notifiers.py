from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import requests

from naver_land_watcher.config import required_env
from naver_land_watcher.models import ListingChange

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self) -> None:
        self.bot_token = required_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = required_env("TELEGRAM_CHAT_ID")

    def send(self, change: ListingChange, complex_name: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        message = _format_message(change, complex_name)
        response = requests.post(
            url,
            json={"chat_id": self.chat_id, "text": message, "disable_web_page_preview": True},
            timeout=10,
        )
        response.raise_for_status()


class EmailNotifier:
    def __init__(self) -> None:
        self.smtp_host = required_env("SMTP_HOST")
        self.smtp_port = int(required_env("SMTP_PORT"))
        self.smtp_user = required_env("SMTP_USER")
        self.smtp_pass = required_env("SMTP_PASS")
        self.email_to = required_env("EMAIL_TO")

    def send(self, change: ListingChange, complex_name: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = f"[Naver Land] {'NEW' if change.is_new else 'UPDATE'} {change.listing.article_name}"
        msg["From"] = self.smtp_user
        msg["To"] = self.email_to
        msg.set_content(_format_message(change, complex_name))

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(self.smtp_user, self.smtp_pass)
            smtp.send_message(msg)


def _format_message(change: ListingChange, complex_name: str) -> str:
    listing = change.listing
    header = "🆕 New listing" if change.is_new else "🔄 Listing updated"
    changes = f"Changes: {', '.join(change.changed_fields)}" if change.changed_fields else ""
    url = f"https://new.land.naver.com/articles/{listing.article_no}"
    lines = [
        header,
        f"Complex: {complex_name}",
        f"Article: {listing.article_name} ({listing.article_no})",
        f"Price: {listing.deal_or_warrant_prc}",
        f"Floor: {listing.floor_info}",
        f"Area: {listing.area_name}",
        f"Direction: {listing.direction}",
        f"Confirm: {listing.article_confirm_ymd}",
        f"Realtor: {listing.realtor_name}",
        changes,
        url,
    ]
    return "\n".join(line for line in lines if line)
