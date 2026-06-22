"""
notifier.py — Low-stock email alert system.

Configuration (via .env or shell environment):
  SMTP_HOST   — SMTP server hostname  (e.g. smtp.gmail.com)
  SMTP_PORT   — SMTP port             (default 587)
  SMTP_USER   — Sender email address
  SMTP_PASS   — Sender email password / app password
  ALERT_EMAIL — Recipient email address for low-stock alerts

If any of these are not set, is_smtp_configured() returns False and
send_low_stock_alert() returns a descriptive error string.

For Gmail: create an App Password at
  https://myaccount.google.com/apppasswords
and set SMTP_PASS to that 16-char password.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Tuple

logger = logging.getLogger(__name__)

SMTP_HOST   = os.environ.get("SMTP_HOST",   "")
SMTP_PORT   = int(os.environ.get("SMTP_PORT",   "587"))
SMTP_USER   = os.environ.get("SMTP_USER",   "")
SMTP_PASS   = os.environ.get("SMTP_PASS",   "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")


def is_smtp_configured() -> bool:
    """Return True only if all four SMTP env vars are set."""
    return all([SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_EMAIL])


def send_low_stock_alert(drugs: List[tuple]) -> Tuple[bool, str]:
    """
    Send a low-stock alert email.

    drugs: list of (D_Name, D_id, D_Qty) tuples — from drug_get_low_stock().

    Returns (success, message).
    """
    if not is_smtp_configured():
        missing = [v for v, e in {
            "SMTP_HOST": SMTP_HOST, "SMTP_USER": SMTP_USER,
            "SMTP_PASS": SMTP_PASS, "ALERT_EMAIL": ALERT_EMAIL,
        }.items() if not e]
        return False, f"SMTP not configured. Missing env vars: {', '.join(missing)}"

    if not drugs:
        return False, "No low-stock drugs to report."

    # ── Build message body ───────────────────────────────────────────────
    rows = "\n".join(
        f"  • {d[0]} (ID: {d[1]}) — {d[2]} unit(s) remaining"
        for d in drugs
    )
    body = (
        f"Hello,\n\n"
        f"{len(drugs)} drug(s) are running low on stock and require restocking:\n\n"
        f"{rows}\n\n"
        f"Please log into PharmaSystem to restock these items.\n\n"
        f"— PharmaSystem Auto-Alert"
    )

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = ALERT_EMAIL
    msg["Subject"] = f"⚠️ Low Stock Alert — {len(drugs)} drug(s) need restocking"
    msg.attach(MIMEText(body, "plain"))

    # ── Send ─────────────────────────────────────────────────────────────
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info("Low-stock alert sent to %s (%d drugs)", ALERT_EMAIL, len(drugs))
        return True, f"Alert sent to {ALERT_EMAIL}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check SMTP_USER and SMTP_PASS."
    except smtplib.SMTPConnectError:
        return False, f"Could not connect to {SMTP_HOST}:{SMTP_PORT}."
    except Exception as exc:
        logger.error("send_low_stock_alert failed: %s", exc)
        return False, str(exc)
