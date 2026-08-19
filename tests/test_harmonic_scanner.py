"""src/analysis/harmonic_scanner.py testleri.

`tests/test_abcd_scanner.py` ile AYNI desen (monkeypatch ile gercek ag/detect
cagrisi engellenir) ama `detect_prz` formasyon-basina (dict) cagirilir --
`_scan_one_symbol` sembol basina TUM secili formasyonlari tek fetch uzerinde
tarar (bkz. modul ust notu, verimlilik karari)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.analysis import harmonic_scanner as hs
from src.analysis.harmonic_confirmation import ConfirmationFlags
from src.analysis.harmonic_xabcd import PrzEvent


def _make_event(direction: int, signal_bar: int) -> PrzEvent:
    return PrzEvent(
        direction=direction,
        x_bar=-1, a_bar=0, b_bar=1, c_bar=2, d_bar=signal_bar,
        x_price=float("nan"), a_price=100.0, b_price=90.0, c_price=95.0, d_price=85.0,
        signal_bar=signal_bar,
        signal_time=pd.Timestamp("2026-08-10", tz="UTC"),
        entry_ref=100.0, fill_ref=101.0,
        tp1=110.0, tp2=120.0, sl=90.0,
        bc_ratio=0.5, zone_low=84.0, zone_high=86.0,
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
    """AAA: ABCD'de bu barda (bars_ago=0) BUY; GARTLEY'de sinyal yok.
    BBB: BAT'ta 1 bar once (bars_ago=1) SELL. EMPTY: veri hic donmuyor."""

    events_by_symbol_formation = {
        ("AAA", "ABCD"): [_make_event(direction=1, signal_bar=19)],
        ("BBB", "BAT"): [_make_event(direction=-1, signal_bar=18)],
    }

    def fake_fetch(symbol, tf, n_bars):
        if symbol == "EMPTY":
            return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])
        return _fake_df(symbol)

    def fake_detect_prz(df, params):
        # `df.attrs["symbol"]` ile sembolu, `params.name` ile formasyonu
        # ayirt ederiz -- thread-safe (test_abcd_scanner.py ile AYNI desen,
        # paylasilan mutable durum YOK).
        symbol = df.attrs.get("symbol")
        return events_by_symbol_formation.get((symbol, params.name), [])

    monkeypatch.setattr(hs, "fetch_ohlcv_abcd", fake_fetch)
    monkeypatch.setattr(hs, "detect_prz", fake_detect_prz)

    return events_by_symbol_formation


def test_scan_formasyon_basina_ayri_buy_sell_listesi(scan_universe):
    result = hs.scan(["AAA", "BBB", "EMPTY"], "240", hs.FORMATION_NAMES, lookback_bars=5)

    assert len(result.buys["ABCD"]) == 1
    assert result.buys["ABCD"][0].symbol == "AAA"
    assert result.buys["ABCD"][0].bars_ago == 0

    assert len(result.sells["BAT"]) == 1
    assert result.sells["BAT"][0].symbol == "BBB"
    assert result.sells["BAT"][0].bars_ago == 1

    # Diger formasyonlarda hic sinyal yok
    assert result.buys["GARTLEY"] == []
    assert result.sells["ABCD"] == []


def test_scan_hata_toleransi(scan_universe):
    result = hs.scan(["AAA", "BBB", "EMPTY"], "240", hs.FORMATION_NAMES, lookback_bars=5)

    assert "EMPTY" in result.errors
    assert len(result.buys["ABCD"]) == 1
    assert len(result.sells["BAT"]) == 1


def test_scan_on_progress_her_sembolde_bir_cagrilir(scan_universe):
    calls = []
    hs.scan(
        ["AAA", "BBB", "EMPTY"], "240", hs.FORMATION_NAMES, lookback_bars=5,
        on_progress=lambda done, total: calls.append((done, total)),
    )
    assert len(calls) == 3
    assert all(total == 3 for _, total in calls)


def test_scan_sadece_secilen_formasyonlar_taranir(scan_universe):
    result = hs.scan(["AAA", "BBB"], "240", ("ABCD",), lookback_bars=5)

    assert result.formations == ("ABCD",)
    assert "BAT" not in result.buys
    assert len(result.buys["ABCD"]) == 1


def test_guven_etiketi_bilinen_kombinasyon_karli():
    label = hs.guven_etiketi("CRAB", "1D", direction=1)
    assert "GÜVENİLİR" in label
    assert "1.40" in label


def test_guven_etiketi_bilinmeyen_tf_dogrulanmadi_der():
    label = hs.guven_etiketi("ABCD", "60", direction=1)
    assert "DOĞRULANMADI" in label


def test_format_report_formasyon_basliklari_ve_yok_metni(scan_universe):
    result = hs.scan(["AAA", "BBB", "EMPTY"], "240", hs.FORMATION_NAMES, lookback_bars=5)
    report = hs.format_report(result, markdown=False)

    assert "── ABCD ──" in report
    assert "── BAT ──" in report
    assert "AAA" in report
    assert "BBB" in report
    assert "(yok)" in report  # GARTLEY/BUTTERFLY/CRAB'da hic sinyal yok


def test_format_report_markdown_fenced_code_block(scan_universe):
    result = hs.scan(["AAA", "BBB", "EMPTY"], "240", hs.FORMATION_NAMES, lookback_bars=5)
    report = hs.format_report(result, markdown=True)

    assert report.count("```") == 2
    assert "1" in report and "basarisiz" in report


_FLAGS = ConfirmationFlags(
    rsi_value=50.0, rsi_divergence=False, rsi_extreme_turn=False, rsi_ok=False,
    macd_hist=0.1, macd_ok=False,
    candle_pattern=None, candle_ok=False,
    volume_ratio=1.0, volume_compression=False, volume_expansion=False, volume_ok=False,
    score=0,
)


def _scanned(symbol: str, formation: str) -> hs.ScannedPrz:
    return hs.ScannedPrz(
        symbol=symbol, formation=formation, event=_make_event(direction=1, signal_bar=0),
        bars_ago=0, confidence="◻ DOĞRULANMADI (test)", confirmation=_FLAGS,
    )


def test_format_report_chunks_kucuk_rapor_tek_parca_doner():
    result = hs.HarmonicScanResult(
        tf="1D", scanned_at=pd.Timestamp("2026-08-19", tz="UTC"), lookback_bars=5,
        formations=("ABCD",), buys={"ABCD": [_scanned("AAA", "ABCD")]}, sells={"ABCD": []}, errors={},
    )
    chunks = hs.format_report_chunks(result, markdown=True)
    assert len(chunks) == 1
    assert "AAA" in chunks[0]
    assert "parca" not in chunks[0].lower()


def test_format_report_chunks_buyuk_rapor_birden_fazla_mesaja_bolunur_ve_hicbir_sinyal_kaybolmaz():
    many_buys = [_scanned(f"SYM{i:04d}", "ABCD") for i in range(120)]
    result = hs.HarmonicScanResult(
        tf="1D", scanned_at=pd.Timestamp("2026-08-19", tz="UTC"), lookback_bars=5,
        formations=("ABCD",), buys={"ABCD": many_buys}, sells={"ABCD": []}, errors={"ZZZ": "hata"},
    )
    chunks = hs.format_report_chunks(result, markdown=True, max_chars=1000)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) < 4096  # Telegram sinirinin altinda kalmali
    combined = "\n".join(chunks)
    for i in range(120):
        assert f"SYM{i:04d}" in combined  # HICBIR sinyal kaybolmamis
    assert "parca 1/" in chunks[0].lower()
    assert "basarisiz" in chunks[-1]  # hata ozeti SADECE son parcada


def test_format_report_chunks_her_zaman_en_az_bir_mesaj_doner_bos_sonucta_bile():
    result = hs.HarmonicScanResult(
        tf="1D", scanned_at=pd.Timestamp("2026-08-19", tz="UTC"), lookback_bars=5,
        formations=("ABCD",), buys={"ABCD": []}, sells={"ABCD": []}, errors={},
    )
    chunks = hs.format_report_chunks(result, markdown=True)
    assert len(chunks) == 1
    assert "(yok)" in chunks[0]
