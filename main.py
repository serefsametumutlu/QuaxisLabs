"""Bilanco Radar Telegram botunu baslatan giris noktasi.

Konfigurasyon dogrulamasi ve loglama kurulumu src.bot.telegram_bot.run_bot()
icinde yapilir; bu dosya sadece onu cagirir ve cikis kodunu yonetir.
"""

from __future__ import annotations

import logging
import sys

from src.bot.telegram_bot import run_bot

logger = logging.getLogger(__name__)


def main() -> int:
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot durduruldu (Ctrl+C).")
    except RuntimeError as exc:
        logger.error("Bot baslatilamadi: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
