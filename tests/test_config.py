"""Faz 1 bagimsiz test/demo scripti: config.py ve loglama kurulumunu dogrular.

Calistirmak icin: pytest tests/test_config.py -v
"""

from __future__ import annotations

import logging

import config


def test_dizinler_olusturulmus() -> None:
    assert config.DATA_DIR.exists()
    assert config.LOG_DIR.exists()


def test_sabitler_dogru_tipte() -> None:
    assert isinstance(config.HTTP_TIMEOUT_SECONDS, float)
    assert isinstance(config.HTTP_MAX_RETRIES, int)
    assert isinstance(config.KAP_LOOKBACK_DAYS, int)
    assert config.DATABASE_URL.startswith("sqlite:///")


def test_validate_config_liste_doner() -> None:
    errors = config.validate_config()
    assert isinstance(errors, list)


def test_setup_logging_dosya_olusturur() -> None:
    config.setup_logging()
    logger = logging.getLogger("bilanco_radar.test")
    logger.info("Faz 1 loglama testi mesaji")

    for handler in logging.getLogger().handlers:
        handler.flush()

    assert config.LOG_FILE.exists()
    assert config.LOG_FILE.read_text(encoding="utf-8").strip() != ""


def test_setup_logging_idempotent() -> None:
    handler_count_before = len(logging.getLogger().handlers)
    config.setup_logging()
    handler_count_after = len(logging.getLogger().handlers)
    assert handler_count_before == handler_count_after
