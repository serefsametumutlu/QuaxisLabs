"""Bilanco Radar Telegram botunu baslatan giris noktasi.

Konfigurasyon dogrulamasi ve loglama kurulumu src.bot.telegram_bot.run_bot()
icinde yapilir; bu dosya sadece onu cagirir ve cikis kodunu yonetir.
"""

from __future__ import annotations

import logging
import sys

from telegram.error import TelegramError

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
    except TelegramError as exc:
        # run_polling(bootstrap_retries=-1) baslangicta SINIRSIZ tekrar dener
        # (bkz. telegram_bot.run_bot) -- buraya duserse artik baslangic
        # DISINDA (calisirken) beklenmeyen bir Telegram hatasidir. Ham
        # traceback yerine kisa bir satir: terminali cift traceback ile
        # doldurup kullaniciyi asil sebepten uzaklastirmasin.
        logger.error("Telegram baglantisinda beklenmeyen hata, bot kapatiliyor: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
