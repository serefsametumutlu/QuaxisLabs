"""src/fetchers/price_history.py + isyatirim.fetch_price_history() +
sec_edgar.fetch_price_history() testleri.

Kural 11: hicbir ag istegi ATILMAZ -- HTTP katmanindaki ozel (_request_*)
fonksiyonlar monkeypatch ile sahte JSON payload'lari dondurecek sekilde
degistirilir; sadece ayristirma/donusum mantigi test edilir.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
import pytest

from src.fetchers import isyatirim, price_history, sec_edgar
from src.fetchers.price_history import OhlcvBar


# --- isyatirim.fetch_price_history --------------------------------------------


def test_isyatirim_fetch_price_history_hgdg_alanlarini_kullanir(monkeypatch):
    """Duzeltilmis (HGDG_*) seri kullanilmali, HG_* (duzeltilmemis) DEGIL --
    bkz. fonksiyon docstring'indeki THYAO canli gozlemi."""
    payload = {
        "value": [
            {
                "HGDG_TARIH": "30-06-2025",
                "HGDG_KAPANIS": "280.6087",
                "HGDG_MIN": "265.7617",
                "HGDG_MAX": "281.1036",
                "HGDG_HACIM": "16941637915.0",
                "HG_KAPANIS": "283.5",  # duzeltilmemis -- KULLANILMAMALI
            },
            {
                "HGDG_TARIH": "31-07-2026",
                "HGDG_KAPANIS": "314.0",
                "HGDG_MIN": "308.75",
                "HGDG_MAX": "315.25",
                "HGDG_HACIM": "14307510787.0",
            },
        ]
    }
    monkeypatch.setattr(isyatirim, "_request_price_history", lambda company_code, start, end: payload)

    bars = isyatirim.fetch_price_history("THYAO", days=400)

    assert len(bars) == 2
    first = bars[0]
    assert first["date"] == date(2025, 6, 30)
    assert first["open"] is None  # uc noktada acilis fiyati YOK
    assert first["close"] == Decimal("280.6087")
    assert first["high"] == Decimal("281.1036")
    assert first["low"] == Decimal("265.7617")
    assert first["volume"] == Decimal("16941637915.0")


def test_isyatirim_fetch_price_history_eksik_alanli_satiri_atlar(monkeypatch):
    """HGDG_MAX/MIN/KAPANIS'ten biri eksikse o satir tamamen atlanir (Kural 3:
    yarim bir mum uydurulmaz)."""
    payload = {
        "value": [
            {"HGDG_TARIH": "01-01-2026", "HGDG_KAPANIS": None, "HGDG_MIN": "10", "HGDG_MAX": "12"},
            {"HGDG_TARIH": "02-01-2026", "HGDG_KAPANIS": "11", "HGDG_MIN": "10", "HGDG_MAX": "12", "HGDG_HACIM": "100"},
        ]
    }
    monkeypatch.setattr(isyatirim, "_request_price_history", lambda company_code, start, end: payload)

    bars = isyatirim.fetch_price_history("THYAO", days=30)

    assert len(bars) == 1
    assert bars[0]["date"] == date(2026, 1, 2)


def test_isyatirim_fetch_price_history_bozuk_tarihi_atlar(monkeypatch):
    payload = {
        "value": [
            {"HGDG_TARIH": "gecersiz-tarih", "HGDG_KAPANIS": "11", "HGDG_MIN": "10", "HGDG_MAX": "12", "HGDG_HACIM": "1"},
        ]
    }
    monkeypatch.setattr(isyatirim, "_request_price_history", lambda company_code, start, end: payload)

    bars = isyatirim.fetch_price_history("THYAO", days=30)

    assert bars == []


def test_isyatirim_fetch_price_history_bos_deger_bos_liste_doner(monkeypatch):
    monkeypatch.setattr(isyatirim, "_request_price_history", lambda company_code, start, end: {"value": []})

    assert isyatirim.fetch_price_history("YOKTUR", days=30) == []


def test_isyatirim_fetch_price_history_ag_hatasinda_bos_liste_doner(monkeypatch):
    def _patlar(company_code, start, end):
        raise isyatirim.IsYatirimNetworkError("test ag hatasi")

    monkeypatch.setattr(isyatirim, "_request_price_history", _patlar)

    assert isyatirim.fetch_price_history("THYAO", days=30) == []


# --- sec_edgar.fetch_price_history --------------------------------------------


def _yahoo_payload(timestamps, opens, highs, lows, closes, volumes):
    return {
        "chart": {
            "result": [
                {
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [
                            {"open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes}
                        ]
                    },
                }
            ],
            "error": None,
        }
    }


def test_sec_edgar_fetch_price_history_acilis_fiyatini_da_doner(monkeypatch):
    """NASDAQ kaynagi (Yahoo chart) BIST'ten farkli olarak 'open' iceriyor."""
    payload = _yahoo_payload(
        timestamps=[1722470400],  # 2024-08-01 00:00:00 UTC
        opens=[224.3699951171875],
        highs=[224.47999572753906],
        lows=[217.02000427246094],
        closes=[218.36000061035125],
        volumes=[62501000],
    )
    monkeypatch.setattr(sec_edgar, "_request_price_chart_history", lambda ticker, range_label: payload)

    bars = sec_edgar.fetch_price_history("AAPL", days=400)

    assert len(bars) == 1
    bar = bars[0]
    assert bar["date"] == date(2024, 8, 1)
    assert bar["open"] == Decimal("224.3699951171875")
    assert bar["volume"] == Decimal("62501000")


def test_sec_edgar_fetch_price_history_null_barlari_atlar(monkeypatch):
    """Yahoo tatil/kismi gunlerde null OHLC dondurebiliyor -- bu barlar
    TAMAMEN atlanir, yariya tamamlanmis bir mum uydurulmaz."""
    payload = _yahoo_payload(
        timestamps=[1722470400, 1722556800],
        opens=[100.0, None],
        highs=[105.0, None],
        lows=[95.0, None],
        closes=[102.0, None],
        volumes=[1000, None],
    )
    monkeypatch.setattr(sec_edgar, "_request_price_chart_history", lambda ticker, range_label: payload)

    bars = sec_edgar.fetch_price_history("AAPL", days=400)

    assert len(bars) == 1
    assert bars[0]["close"] == Decimal("102.0")


def test_sec_edgar_fetch_price_history_ag_hatasinda_bos_liste_doner(monkeypatch):
    def _patlar(ticker, range_label):
        raise sec_edgar.SecEdgarNetworkError("test ag hatasi")

    monkeypatch.setattr(sec_edgar, "_request_price_chart_history", _patlar)

    assert sec_edgar.fetch_price_history("AAPL", days=400) == []


# --- price_history.fetch_ohlcv (dispatcher) -----------------------------------


def test_fetch_ohlcv_bist_isyatirimi_cagirir_ve_artan_tarihe_sirali_doner(monkeypatch):
    raw_rows = [
        {"date": date(2026, 1, 2), "open": None, "high": Decimal("12"), "low": Decimal("10"), "close": Decimal("11"), "volume": Decimal("100")},
        {"date": date(2026, 1, 1), "open": None, "high": Decimal("11"), "low": Decimal("9"), "close": Decimal("10"), "volume": Decimal("50")},
    ]
    monkeypatch.setattr(isyatirim, "fetch_price_history", lambda ticker, days=400: raw_rows)

    bars = price_history.fetch_ohlcv("THYAO", "BIST", days=400)

    assert bars == [
        OhlcvBar(trade_date=date(2026, 1, 1), open=None, high=Decimal("11"), low=Decimal("9"), close=Decimal("10"), volume=Decimal("50")),
        OhlcvBar(trade_date=date(2026, 1, 2), open=None, high=Decimal("12"), low=Decimal("10"), close=Decimal("11"), volume=Decimal("100")),
    ]


def test_fetch_ohlcv_nasdaq_sec_edgari_cagirir(monkeypatch):
    raw_rows = [
        {"date": date(2026, 1, 1), "open": Decimal("9"), "high": Decimal("11"), "low": Decimal("8"), "close": Decimal("10"), "volume": Decimal("1000")},
    ]
    calls = []
    monkeypatch.setattr(isyatirim, "fetch_price_history", lambda ticker, days=400: (_ for _ in ()).throw(AssertionError("BIST fetcher cagrilmamali")))
    monkeypatch.setattr(sec_edgar, "fetch_price_history", lambda ticker, days=400: calls.append(ticker) or raw_rows)

    bars = price_history.fetch_ohlcv("AAPL", "NASDAQ", days=400)

    assert calls == ["AAPL"]
    assert bars[0].open == Decimal("9")


def test_fetch_ohlcv_veri_yoksa_bos_liste_doner(monkeypatch):
    monkeypatch.setattr(isyatirim, "fetch_price_history", lambda ticker, days=400: [])

    assert price_history.fetch_ohlcv("YOKTUR", "BIST", days=400) == []
