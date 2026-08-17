"""src/analysis/abcd_scanner.py testleri.

`get_bist_universe` icin `tests/test_db.py`nin izole-SQLite-dosyasi
fixture'iyla AYNI desen kullanilir (gercek `data/bilanco_radar.db`ye asla
DOKUNULMAZ). `scan()` icin gercek ag/DB cagrisi YOK -- `abcd_scanner.
fetch_ohlcv_abcd` ve `abcd_scanner.detect` monkeypatch ile taklit edilir
(Kural 11 ile ayni ilke, bkz. test_abcd_data.py/test_abcd_backtest.py).
"""

from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
import pytest

from src.analysis import abcd_scanner
from src.analysis.abcd_pattern import Signal
from src.db import models
from src.db.models import Company

# --- get_bist_universe -----------------------------------------------------


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def test_get_bist_universe_sadece_bist_sirketlerini_alfabetik_sirali_doner(session):
    session.add_all(
        [
            Company(ticker="THYAO", market="BIST"),
            Company(ticker="ASELS", market="BIST"),
            Company(ticker="AAPL", market="NASDAQ"),
        ]
    )
    session.commit()

    result = abcd_scanner.get_bist_universe(session=session)

    assert result == ["ASELS", "THYAO"]


def test_get_bist_universe_session_verilmezse_get_session_kullanir(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_default.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    default_session = session_factory()
    default_session.add(Company(ticker="SISE", market="BIST"))
    default_session.add(Company(ticker="MSFT", market="NASDAQ"))
    default_session.commit()

    @contextmanager
    def fake_get_session():
        yield default_session

    monkeypatch.setattr(abcd_scanner, "get_session", fake_get_session)

    result = abcd_scanner.get_bist_universe()

    assert result == ["SISE"]
    default_session.close()


# --- scan --------------------------------------------------------------


def _make_signal(direction: int, signal_bar: int, symbol_tag: str = "") -> Signal:
    return Signal(
        direction=direction,
        a_bar=0,
        b_bar=1,
        c_bar=2,
        d_bar=signal_bar - 2,
        a_price=100.0,
        b_price=90.0,
        c_price=95.0,
        d_price=85.0,
        signal_bar=signal_bar,
        signal_time=pd.Timestamp("2026-08-10", tz="UTC"),
        entry_ref=100.0,
        fill_ref=101.0,
        tp1=110.0,
        tp2=120.0,
        sl=90.0,
        bc_ratio=0.5,
        cd_ratio=1.0,
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
    """AAA: bu barda (bars_ago=0) BUY sinyali. BBB: 1 bar once (bars_ago=1)
    SELL sinyali. EMPTY: veri hic donmuyor -- diger sembolleri ETKILEMEMELI."""

    signals_by_symbol = {
        "AAA": [_make_signal(direction=1, signal_bar=19)],
        "BBB": [_make_signal(direction=-1, signal_bar=18)],
        "EMPTY": [],
    }

    def fake_fetch(symbol, tf, n_bars):
        if symbol == "EMPTY":
            return pd.DataFrame(columns=abcd_scanner_ohlcv_columns())
        return _fake_df(symbol)

    def fake_detect(df, params):
        symbol = df.attrs.get("symbol")
        return signals_by_symbol.get(symbol, [])

    monkeypatch.setattr(abcd_scanner, "fetch_ohlcv_abcd", fake_fetch)
    monkeypatch.setattr(abcd_scanner, "detect", fake_detect)
    return signals_by_symbol


def abcd_scanner_ohlcv_columns():
    return ["time", "open", "high", "low", "close", "volume"]


def test_scan_buy_sell_ayrimi_ve_bars_ago(scan_universe):
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5)

    assert len(result.buys) == 1
    assert result.buys[0].symbol == "AAA"
    assert result.buys[0].bars_ago == 0

    assert len(result.sells) == 1
    assert result.sells[0].symbol == "BBB"
    assert result.sells[0].bars_ago == 1


def test_scan_d_bars_ago_onay_gecikmesini_ayri_gosterir(scan_universe):
    """Kullanici karisikligi (canli test, 2026-08-18): D pivotunun kendisi
    onay barindan `pivot_lookback` bar ONCE olusur -- `d_bars_ago`,
    `bars_ago`'dan tam `pivot_lookback` kadar buyuk olmali, ikisi
    KARISTIRILMAMALI."""
    params = abcd_scanner.Params(pivot_lookback=5)
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", params, lookback_bars=10)

    buy = result.buys[0]
    assert buy.bars_ago == 0
    assert buy.d_bars_ago == 5  # 0 + pivot_lookback

    sell = result.sells[0]
    assert sell.bars_ago == 1
    assert sell.d_bars_ago == 6  # 1 + pivot_lookback

    report = abcd_scanner.format_report(result, markdown=False)
    assert "D olustu: 5 bar once (onay: bu bar)" in report
    assert "D olustu: 6 bar once (onay: 1 bar once)" in report


def test_scan_hata_toleransi_bir_sembol_patlarsa_digerleri_etkilenmez(scan_universe):
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5)

    assert "EMPTY" in result.errors
    assert len(result.buys) == 1
    assert len(result.sells) == 1


def test_scan_on_progress_callback_her_sembolde_cagirilir(scan_universe):
    calls = []

    def on_progress(completed, total):
        calls.append((completed, total))

    abcd_scanner.scan(
        ["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5, on_progress=on_progress
    )

    assert len(calls) == 3
    assert all(total == 3 for _, total in calls)
    completed_values = sorted(c for c, _ in calls)
    assert completed_values == [1, 2, 3]


def test_scan_lookback_disinda_kalan_sinyal_raporlanmaz(monkeypatch):
    def fake_fetch(symbol, tf, n_bars):
        return _fake_df(symbol)

    def fake_detect(df, params):
        return [_make_signal(direction=1, signal_bar=10)]  # bars_ago = 19-10 = 9

    monkeypatch.setattr(abcd_scanner, "fetch_ohlcv_abcd", fake_fetch)
    monkeypatch.setattr(abcd_scanner, "detect", fake_detect)

    result = abcd_scanner.scan(["AAA"], "240", abcd_scanner.Params(), lookback_bars=5)

    assert result.buys == []
    assert result.sells == []
    assert result.errors == {}


# --- format_report -------------------------------------------------------


def test_format_report_markdown_govde_fenced_code_block_icindedir(scan_universe):
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5)

    report = abcd_scanner.format_report(result, markdown=True)

    assert report.count("```") == 2
    body = report.split("```")[1]
    assert "AAA" in body
    assert "BBB" in body
    # Code block icinde MDV2 rezerve karakterleri KACISLANMAMIS olmali
    # (sadece backslash/backtick kacislanir) -- orn. "|" ya da "." backslash'siz.
    assert "\\|" not in body
    assert "\\." not in body


def test_format_report_markdown_baslik_disarida_kacislanmis(scan_universe):
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5)

    report = abcd_scanner.format_report(result, markdown=True)
    header = report.split("\n")[0]

    assert "\\(" in header and "\\)" in header  # "(son 5 bar)" kacislanmis


def test_format_report_markdown_hata_sayisini_bildirir(scan_universe):
    result = abcd_scanner.scan(["AAA", "BBB", "EMPTY"], "240", abcd_scanner.Params(), lookback_bars=5)

    report = abcd_scanner.format_report(result, markdown=True)

    assert "1" in report and "basarisiz" in report


def test_format_report_duz_metin_code_block_icermez():
    result = abcd_scanner.ScanResult(
        tf="240", scanned_at=pd.Timestamp.now("UTC"), lookback_bars=5, buys=[], sells=[], errors={}
    )

    report = abcd_scanner.format_report(result, markdown=False)

    assert "```" not in report
    assert "(yok)" in report
