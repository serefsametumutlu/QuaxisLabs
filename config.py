"""Bilanco Radar icin merkezi ayarlar ve sabitler.

Tum modüller ortam degiskenlerine ve sabitlere buradan erisir.
Gizli anahtarlar .env dosyasindan okunur, koda asla gomulmez.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# --- Dizin yollari -----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# .env dosyasini yukle (varsa)
load_dotenv(BASE_DIR / ".env")


def _ensure_utf8_console() -> None:
    """Windows'ta varsayilan konsol kod sayfasi (orn. Turkce cp1254) TL
    isareti (₺) gibi bazi Unicode karakterleri temsil edemez ve print/log
    sirasinda UnicodeEncodeError ile cokmeye sebep olur (canli Gemini
    yanitinda gozlemlendi -- LLM'in urettigi ozet metninde ₺ gecince demo
    scripti coktu). stdout/stderr UTF-8'i destekliyorsa yeniden yapilandirir;
    desteklemiyorsa (orn. bazi test/CI ortamlarinda) sessizce atlar."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_ensure_utf8_console()

# --- API anahtarlari -----------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# --- Veritabani -----------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'bilanco_radar.db').as_posix()}")

# --- Dis servis ayarlari -----------------------------------------------------
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "15"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))
HTTP_RATE_LIMIT_DELAY_SECONDS = float(os.getenv("HTTP_RATE_LIMIT_DELAY_SECONDS", "1.0"))

# --- KAP ayarlari -----------------------------------------------------
KAP_LOOKBACK_DAYS = int(os.getenv("KAP_LOOKBACK_DAYS", "90"))

# --- Gemini ayarlari -----------------------------------------------------
# "gemini-flash-latest" GUNLUK kotasi (canli dogrulandi: 20 istek/gun,
# RESOURCE_EXHAUSTED) cok hizli tukeniyordu. "gemini-flash-lite-latest"
# AYRI (ve gozlemlenen kullanimda daha yuksek) bir kota havuzuna sahip --
# canli test edildi, ayni anda flash-latest 429 donerken lite-latest 200
# OK dondu. Yapisal JSON ciktisi (bu projenin tek kullanim sekli) icin
# kalite farki onemsiz; kota sorununu asmak icin varsayilan bu yapildi.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
# HTTP_TIMEOUT_SECONDS (varsayilan 15s) Is Yatirim/KAP gibi hizli REST
# uc noktalari icin yeterliyken, Gemini generateContent bir dil modeli
# cagrisidir ve yuk altinda 15s'yi asabilir (canli loglarda "The read
# operation timed out" tekrar tekrar gozlemlendi, her seferinde retry+
# fallback'e dusuyordu). Bu yuzden Gemini icin AYRI ve daha yuksek bir
# zaman asimi kullanilir.
GEMINI_TIMEOUT_SECONDS = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "45"))

# --- Loglama -----------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = LOG_DIR / "bilanco_radar.log"


_LOGGING_CONFIGURED = False


def setup_logging() -> None:
    """Kok logger'i dosyaya + konsola yazacak sekilde yapilandirir.

    Idempotentligi root logger'daki handler sayisiyla degil, kendi modul
    bayragiyla takip eder; boylece pytest gibi disaridan handler ekleyen
    araclarla calisirken tekrar cagrildiginda dosya handler'i atlanmaz.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _LOGGING_CONFIGURED = True


def validate_config() -> list[str]:
    """Eksik zorunlu ayarlari kontrol eder, hata mesajlari listesi doner."""
    errors = []
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY tanimli degil (.env dosyasini kontrol et)")
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN tanimli degil (.env dosyasini kontrol et)")
    return errors
