"""src/analysis/momentum_scanner.py testleri.

`tests/test_harmonic_scanner.py` ile AYNI desen (monkeypatch ile gercek ag/
detect cagrisi engellenir) -- tek fark: momentum_confluence SADECE LONG
uretir, bu yuzden BUY/SELL sozlugu degil TEK bir sinyal listesi test edilir."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis import momentum_scanner as ms
from src.analysis.momentum_confluence import Signal


def _make_signal(signal_bar: int) -> Signal:
    return Signal(
        direction=1,
        signal_bar=signal_bar,
        signal_time=pd.Timestamp("2026-08-10", tz="UTC"),
        entry_ref=100.0,
        fill_ref=101.0,
        tp1=110.0,
        tp2=120.0,
        sl=90.0,
        ema_spread_pct=0.5,
        volume_ratio=2.0,
        downward_streak_before_flip=3,
        wt1_at_signal=float("nan"),
    )


def _fake_df(symbol: str, n: int = 20) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC"),
            "open": [100.0] * n,
            "high": [105.0] * n,
            "low": [95.0] * n,
            "close": [100.0] * n,
            "volume": [1000.0] * n,
        }
    )
    df.attrs["symbol"] = symbol
    return df


@pytest.fixture()
def scan_universe(monkeypatch):
    """AAA/v1: bu barda (bars_ago=0) sinyal. BBB/v1: 1 bar once (bars_ago=1).
    EMPTY: veri hic donmuyor."""

    signals_by_symbol = {"AAA": [_make_signal(19)], "BBB": [_make_signal(18)]}

    def fake_fetch(symbol, tf, n_bars, skip_recent_30m=False):
        if symbol == "EMPTY":
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        return _fake_df(symbol)

    def fake_detect(df, params, variant="v1"):
        symbol = df.attrs.get("symbol")
        return signals_by_symbol.get(symbol, [])

    monkeypatch.setattr(ms, "fetch_ohlcv_abcd", fake_fetch)
    monkeypatch.setattr(ms, "detect", fake_detect)

    return signals_by_symbol


def test_scan_her_sembol_tam_dogrulukla_tek_gecis_cekilir(monkeypatch):
    """GERI ALINAN "iki asamali" deneyin regresyon testi (2026-08-19):
    ucuz (`skip_recent_30m=True`, SADECE 1sa) bir ilk gecis GERCEK sinyalleri
    (ISMEN, canli kullanici raporu) sessizce KACIRABILIYORDU -- artik HER
    sembol, tf ne olursa olsun, TEK cagriyla ve HER ZAMAN `skip_recent_30m=
    False` (tam dogruluk) ile cekilir."""
    calls: list[tuple[str, bool]] = []

    def fake_fetch(symbol, tf, n_bars, skip_recent_30m=False):
        calls.append((symbol, skip_recent_30m))
        return _fake_df(symbol)

    monkeypatch.setattr(ms, "fetch_ohlcv_abcd", fake_fetch)
    monkeypatch.setattr(ms, "detect", lambda df, params, variant="v1": [_make_signal(19)])

    ms.scan(["AAA", "BBB"], "240", "v1", lookback_bars=5)

    assert calls == [("AAA", False), ("BBB", False)] or calls == [("BBB", False), ("AAA", False)]


def test_scan_sinyalleri_bars_ago_sirasiyla_toplar(scan_universe):
    result = ms.scan(["AAA", "BBB", "EMPTY"], "240", "v1", lookback_bars=5)

    assert result.variant == "v1"
    assert len(result.signals) == 2
    assert result.signals[0].symbol == "AAA"
    assert result.signals[0].bars_ago == 0
    assert result.signals[1].symbol == "BBB"
    assert result.signals[1].bars_ago == 1


def test_scan_hata_toleransi(scan_universe):
    result = ms.scan(["AAA", "BBB", "EMPTY"], "240", "v1", lookback_bars=5)

    assert "EMPTY" in result.errors
    assert len(result.signals) == 2


def test_scan_on_progress_her_sembolde_bir_cagrilir(scan_universe):
    calls = []
    ms.scan(
        ["AAA", "BBB", "EMPTY"], "240", "v1", lookback_bars=5,
        on_progress=lambda done, total: calls.append((done, total)),
    )
    assert len(calls) == 3
    assert all(total == 3 for _, total in calls)


def test_scan_lookback_disinda_kalan_sinyal_atlanir(scan_universe):
    result = ms.scan(["AAA", "BBB"], "240", "v1", lookback_bars=1)

    assert len(result.signals) == 1
    assert result.signals[0].symbol == "AAA"


def test_guven_etiketi_bilinen_kombinasyon_guvenilir():
    label = ms.guven_etiketi("v2", "240")
    assert "GÜVENİLİR" in label
    assert "1.41" in label


def test_guven_etiketi_notr_kombinasyon():
    label = ms.guven_etiketi("v2", "1D")
    assert "NÖTR" in label


def test_guven_etiketi_bilinmeyen_tf_dogrulanmadi_der():
    label = ms.guven_etiketi("v1", "60")
    assert "DOĞRULANMADI" in label


def test_format_report_sinyalleri_ve_yok_metnini_icerir(scan_universe):
    result = ms.scan(["AAA", "BBB", "EMPTY"], "240", "v1", lookback_bars=5)
    report = ms.format_report(result, markdown=False)

    assert "Momentum Confluence V1" in report
    assert "AAA" in report
    assert "BBB" in report


def test_format_report_bos_sonucta_yok_metni(monkeypatch):
    monkeypatch.setattr(
        ms, "fetch_ohlcv_abcd",
        lambda symbol, tf, n_bars, skip_recent_30m=False: pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"]),
    )
    result = ms.scan(["EMPTY"], "240", "v2", lookback_bars=5)
    report = ms.format_report(result, markdown=False)

    assert "(yok)" in report


def test_format_report_markdown_fenced_code_block(scan_universe):
    result = ms.scan(["AAA", "BBB", "EMPTY"], "240", "v1", lookback_bars=5)
    report = ms.format_report(result, markdown=True)

    assert report.count("```") == 2
    assert "1" in report and "basarisiz" in report
