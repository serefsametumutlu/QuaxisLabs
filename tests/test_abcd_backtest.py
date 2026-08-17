"""src/analysis/abcd_backtest.py testleri.

`abcd-project/tests/test_backtest.py`'nin yapisini ornek alir: kucuk elle
kurulmus OHLC frame'leri + sentetik `Signal` nesneleriyle (gercek
`detect()` cagirmadan) -- TP1 kismi kapanis, break-even stop, ayni barda
TP+SL cakismasi (conservative_same_bar), `compute_metrics` hesaplarinin
elle dogrulanmasi.

`run_grid`/`to_usd` icin gercek ag cagrisi YOK: `abcd_backtest.fetch_ohlcv_abcd`
ve `abcd_backtest.fetch_usdtry` monkeypatch ile taklit edilir; `detect()` de
(pattern taramasi degil, sadece trade-motoru/GUVENSIZ-etiketleme/grid_warning/
currency_note mantigini test etmek icin) `abcd_backtest.detect` monkeypatch
ile sabit sayida sentetik Signal doner.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.analysis import abcd_backtest
from src.analysis.abcd_backtest import (
    BacktestParams,
    _already_beyond_at_signal_close,
    _entry_for,
    _position_size,
    backtest_symbol,
    compute_metrics,
    run_grid,
    save_summary,
    to_usd,
    trades_to_frame,
)
from src.analysis.abcd_pattern import Params, Signal


def _bar(t, o, h, l, c, v=1000.0):
    return {"time": pd.Timestamp(t, tz="UTC"), "open": o, "high": h, "low": l, "close": c, "volume": v}


def _make_signal(direction: int, signal_bar: int, tp1: float, tp2: float, sl: float, entry_ref: float, fill_ref: float) -> Signal:
    return Signal(
        direction=direction, a_bar=0, b_bar=1, c_bar=2, d_bar=signal_bar - 2,
        a_price=0, b_price=0, c_price=0, d_price=0,
        signal_bar=signal_bar, signal_time=pd.Timestamp("2024-01-01", tz="UTC"),
        entry_ref=entry_ref, fill_ref=fill_ref, tp1=tp1, tp2=tp2, sl=sl, bc_ratio=0.5, cd_ratio=1.0,
    )


NO_COST = BacktestParams(commission_pct=0.0, slippage_ticks=0.0, initial_equity=100_000.0)


# ── _entry_for / _already_beyond_at_signal_close / _position_size ─────────


def test_entry_for_fill_modu_bir_sonraki_barin_acilisini_kullanir():
    sig = _make_signal(1, signal_bar=5, tp1=110, tp2=120, sl=90, entry_ref=100, fill_ref=101)
    entry = _entry_for(sig, BacktestParams(entry_mode="fill"), n_bars=10)
    assert entry == (6, 101)


def test_entry_for_fill_modu_fill_ref_yoksa_none_doner():
    sig = _make_signal(1, signal_bar=5, tp1=110, tp2=120, sl=90, entry_ref=100, fill_ref=float("nan"))
    assert _entry_for(sig, BacktestParams(entry_mode="fill"), n_bars=10) is None


def test_entry_for_d_close_modu_signal_barindaki_entry_refi_kullanir():
    sig = _make_signal(1, signal_bar=5, tp1=110, tp2=120, sl=90, entry_ref=100, fill_ref=101)
    entry = _entry_for(sig, BacktestParams(entry_mode="d_close"), n_bars=10)
    assert entry == (5, 100)


def test_signal_kapanisinda_zaten_tp1i_gecmisse_atlanir():
    df = pd.DataFrame([_bar("2024-01-01", 100, 100, 100, 112)])
    sig = _make_signal(1, signal_bar=0, tp1=110, tp2=120, sl=90, entry_ref=100, fill_ref=101)
    assert _already_beyond_at_signal_close(df, sig)


def test_position_size_asagi_yuvarlar_ve_equityle_sinirlar():
    size = _position_size(equity=10_000, entry_price=100, sl=95, params=BacktestParams(risk_pct=0.01))
    assert size == 20.0


def test_position_size_risk_mesafesi_yoksa_sifir():
    assert _position_size(equity=10_000, entry_price=100, sl=100, params=BacktestParams()) == 0.0


# ── backtest_symbol: TP1/TP2, break-even, ayni-bar cakismasi ──────────────


def test_long_islem_tp1_sonra_tp2_ile_tam_cikis():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 106, 99, 105),
        _bar("2024-01-04", 105, 111, 104, 110),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)

    trades, curve = backtest_symbol(df, "TEST", [sig], NO_COST)

    assert len(trades) == 1
    t = trades[0]
    assert t.entry_bar == 1 and t.entry_price == 100
    assert t.tp1_filled and t.tp1_bar == 2
    assert t.exit_bar == 3 and t.exit_reason == "TP2"
    assert t.size == 200
    expected_pnl = (105 - 100) * 80 + (110 - 100) * 120
    assert math.isclose(t.pnl, expected_pnl)
    assert curve["equity"].iloc[-1] == NO_COST.initial_equity + expected_pnl


def test_long_islem_tp1den_once_stop_out():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 99, 100, 94, 95),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)

    trades, _ = backtest_symbol(df, "TEST", [sig], NO_COST)

    assert len(trades) == 1
    t = trades[0]
    assert not t.tp1_filled
    assert t.exit_reason == "SL"
    assert t.exit_bar == 2
    expected_pnl = (95 - 100) * t.size
    assert math.isclose(t.pnl, expected_pnl)
    assert math.isclose(t.r_multiple, -1.0)


def test_break_even_stop_tp1_sonrasi_kalani_korur():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 106, 99, 105),
        _bar("2024-01-04", 105, 108, 99, 100),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)

    trades, _ = backtest_symbol(df, "TEST", [sig], NO_COST)

    assert len(trades) == 1
    t = trades[0]
    assert t.tp1_filled
    assert t.exit_reason == "SL_BE"
    assert t.exit_bar == 3
    tp1_qty = math.floor(t.size * NO_COST.tp1_pct)
    remainder = t.size - tp1_qty
    expected = (105 - 100) * tp1_qty + (100 - 100) * remainder
    assert math.isclose(t.pnl, expected)


def test_ayni_barda_tp_ve_sl_conservative_ile_sl_kazanir():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 106, 94, 95),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)

    trades, _ = backtest_symbol(
        df, "TEST", [sig], BacktestParams(commission_pct=0, slippage_ticks=0, conservative_same_bar=True)
    )

    assert trades[0].exit_reason == "SL"
    assert not trades[0].tp1_filled


def test_sembol_basina_ayni_anda_tek_acik_pozisyon():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 101, 99, 100),
        _bar("2024-01-04", 100, 106, 99, 105),
        _bar("2024-01-05", 105, 106, 104, 105),
    ]
    df = pd.DataFrame(rows)
    sig1 = _make_signal(1, signal_bar=0, tp1=104, tp2=106, sl=95, entry_ref=99, fill_ref=100)
    sig2 = _make_signal(1, signal_bar=1, tp1=104, tp2=106, sl=95, entry_ref=100, fill_ref=100)

    trades, _ = backtest_symbol(df, "TEST", [sig1, sig2], NO_COST)

    assert len(trades) == 1


def test_short_islem_pnl_isareti():
    rows = [
        _bar("2024-01-01", 100, 101, 99, 100),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 101, 89, 90),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(-1, signal_bar=0, tp1=95, tp2=90, sl=105, entry_ref=100, fill_ref=100)

    trades, _ = backtest_symbol(df, "TEST", [sig], NO_COST)

    assert len(trades) == 1
    t = trades[0]
    assert t.exit_reason == "TP2"
    assert t.pnl > 0


def test_komisyon_ve_kayma_pnli_azaltir():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 111, 99, 110),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)

    cheap, _ = backtest_symbol(df, "TEST", [sig], NO_COST)
    costly, _ = backtest_symbol(df, "TEST", [sig], BacktestParams(commission_pct=0.01, slippage_ticks=5, tick_size=0.1))

    assert costly[0].pnl < cheap[0].pnl


def test_compute_metrics_bos_islem_listesi():
    m = compute_metrics([], pd.DataFrame({"time": [], "equity": []}), 100_000, 100)
    assert m["num_trades"] == 0
    assert m["net_profit_pct"] == 0.0


def test_compute_metrics_elle_hesap_dogrulama():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 106, 99, 105),
        _bar("2024-01-04", 105, 111, 104, 110),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)
    trades, curve = backtest_symbol(df, "TEST", [sig], NO_COST)
    m = compute_metrics(trades, curve, NO_COST.initial_equity, total_bars=len(df))

    expected_pnl = (105 - 100) * 80 + (110 - 100) * 120
    assert m["num_trades"] == 1
    assert m["win_rate"] == 100.0
    assert m["profit_factor"] == float("inf")  # gross_loss == 0, gross_profit > 0
    assert math.isclose(m["net_profit_pct"], expected_pnl / NO_COST.initial_equity * 100.0)
    assert math.isclose(m["expectancy_r"], trades[0].r_multiple)
    assert m["max_drawdown_pct"] == 0.0  # equity hicbir zaman geri cekilmedi


def test_trades_to_frame_sutunlari():
    rows = [
        _bar("2024-01-01", 99, 100, 98, 99),
        _bar("2024-01-02", 100, 101, 99, 100),
        _bar("2024-01-03", 100, 106, 99, 105),
        _bar("2024-01-04", 105, 111, 104, 110),
    ]
    df = pd.DataFrame(rows)
    sig = _make_signal(1, signal_bar=0, tp1=105, tp2=110, sl=95, entry_ref=99, fill_ref=100)
    trades, _ = backtest_symbol(df, "TEST", [sig], NO_COST)
    frame = trades_to_frame(trades)
    assert "pnl" in frame.columns and len(frame) == 1


def test_to_usd_en_yakin_usdtry_kapanisina_boler():
    df = pd.DataFrame(
        {
            "time": pd.to_datetime(["2024-01-01T00:00Z", "2024-01-01T04:00Z"]),
            "open": [3200.0, 3210.0], "high": [3220.0, 3230.0], "low": [3190.0, 3200.0], "close": [3210.0, 3220.0],
            "volume": [1000, 1000],
        }
    )
    usdtry_df = pd.DataFrame({"time": pd.to_datetime(["2024-01-01T00:00Z"]), "close": [32.0]})
    out = to_usd(df, usdtry_df)
    assert math.isclose(out["close"].iloc[0], 3210.0 / 32.0)
    assert math.isclose(out["close"].iloc[1], 3220.0 / 32.0)


def test_to_usd_bos_usdtry_ile_firlatir():
    df = pd.DataFrame([_bar("2024-01-01", 100, 100, 100, 100)])
    with pytest.raises(ValueError):
        to_usd(df, pd.DataFrame(columns=["time", "close"]))


# ── run_grid: GUVENSIZ etiketi / trustworthy / grid_warning / currency_note ─


def _synthetic_ohlcv(n_bars: int) -> pd.DataFrame:
    """Her barda TP1(105)+TP2(110)'u aninda vurup SL(95)'e degmeyen, sabit
    genisman bir OHLCV serisi -- long sinyaller entry barinda hemen TP2 ile
    kapanir (deterministik islem sayisi icin)."""
    times = pd.date_range("2024-01-01", periods=n_bars, freq="4h", tz="UTC")
    return pd.DataFrame(
        {
            "time": times,
            "open": [100.0] * n_bars,
            "high": [115.0] * n_bars,
            "low": [95.5] * n_bars,  # sl=90 asla vurulmaz
            "close": [100.0] * n_bars,  # signal_bar kapanisi tp1(105)'in altinda -> atlanmaz
            "volume": [1000.0] * n_bars,
        }
    )


def _make_dense_signals(n: int) -> list[Signal]:
    """`n` adet, ust uste binmeyen (her biri kendi entry barinda hemen TP2
    ile kapanan) long Signal listesi -- backtest_symbol'un "next_available_bar"
    kuraliyla uyumlu, signal_bar = 0..n-1."""
    return [
        _make_signal(1, signal_bar=i, tp1=105, tp2=110, sl=90, entry_ref=100, fill_ref=100)
        for i in range(n)
    ]


@pytest.fixture
def _patch_data_layer(monkeypatch):
    """`abcd_backtest.fetch_ohlcv_abcd`/`fetch_usdtry`/`detect`'i taklit eder
    -- gercek ag cagrisi YOK, gercek pattern taramasi YOK (islem sayisi
    testin kontrolunde olmali)."""

    def _apply(n_trades_per_symbol: int, n_bars: int = 250, usdtry_available: bool = True):
        calls = {"ohlcv": [], "usdtry": []}

        def _fake_ohlcv(symbol, tf, n_bars_req):
            calls["ohlcv"].append((symbol, tf, n_bars_req))
            return _synthetic_ohlcv(n_bars)

        def _fake_usdtry(tf, n_bars_req):
            calls["usdtry"].append((tf, n_bars_req))
            if not usdtry_available:
                return pd.DataFrame(columns=["time", "close"])
            times = pd.date_range("2024-01-01", periods=n_bars, freq="4h", tz="UTC")
            return pd.DataFrame({"time": times, "close": [32.0] * n_bars})

        def _fake_detect(df, params):
            return _make_dense_signals(n_trades_per_symbol)

        monkeypatch.setattr(abcd_backtest, "fetch_ohlcv_abcd", _fake_ohlcv)
        monkeypatch.setattr(abcd_backtest, "fetch_usdtry", _fake_usdtry)
        monkeypatch.setattr(abcd_backtest, "detect", _fake_detect)
        return calls

    return _apply


def test_run_grid_dusuk_n_hucreyi_atmaz_guvensiz_etiketler(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=12)  # < min_trades_show varsayilani (30)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY",), min_trades_show=30, min_trades_trustworthy=100)

    assert len(summary) == 1  # hucre hic ATILMADI
    row = summary.iloc[0]
    assert row["n_trades"] == 12
    assert row["trustworthy"] == False  # noqa: E712
    assert row["guven_etiketi"] == "GUVENSIZ (n=12)"


def test_run_grid_trustworthy_esigi_100(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=150, n_bars=400)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY",), min_trades_show=30, min_trades_trustworthy=100)

    row = summary.iloc[0]
    assert row["n_trades"] == 150
    assert row["trustworthy"] == True  # noqa: E712
    assert row["guven_etiketi"] == "GUVENILIR"


def test_run_grid_orta_n_dusuk_guven_ama_guvensiz_degil(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=50, n_bars=200)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY",), min_trades_show=30, min_trades_trustworthy=100)

    row = summary.iloc[0]
    assert row["trustworthy"] == False  # noqa: E712
    assert row["guven_etiketi"] == "DUSUK GUVEN (n=50)"


def test_run_grid_usd_satirlari_currency_note_tasir(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=40, n_bars=300)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY", "USD"), min_trades_show=30, min_trades_trustworthy=100)

    try_row = summary[summary["currency"] == "TRY"].iloc[0]
    usd_row = summary[summary["currency"] == "USD"].iloc[0]
    assert try_row["currency_note"] == ""
    assert "BAGIMSIZ tespit" in usd_row["currency_note"]
    assert "doviz-ayarlı" in usd_row["currency_note"] or "doviz" in usd_row["currency_note"].lower()


def test_run_grid_usdtry_verisi_yoksa_usd_hucresi_atlanir_ama_firlatmaz(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=40, n_bars=300, usdtry_available=False)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY", "USD"))

    assert set(summary["currency"]) == {"TRY"}  # USD hucresi sessizce atlandi, hata YOK


def test_run_grid_grid_warning_bonferroni_hesap(_patch_data_layer):
    _patch_data_layer(n_trades_per_symbol=40, n_bars=300)

    summary = run_grid(["THYAO"], tfs=["1D"], denominators=("TRY",))

    assert "grid_warning" in summary.columns
    assert summary["grid_warning"].nunique() == 1
    warning = summary["grid_warning"].iloc[0]
    assert "hucre" in warning
    n_hucre = len(summary)
    expected_alpha = 0.05 / n_hucre
    assert f"{expected_alpha:.5f}" in warning
    assert summary.attrs["n_hucre"] == n_hucre
    assert math.isclose(summary.attrs["effective_alpha"], expected_alpha)


def test_run_grid_bos_veri_bos_dataframe_doner(monkeypatch):
    monkeypatch.setattr(abcd_backtest, "fetch_ohlcv_abcd", lambda symbol, tf, n_bars: pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"]))
    monkeypatch.setattr(abcd_backtest, "fetch_usdtry", lambda tf, n_bars: pd.DataFrame(columns=["time", "close"]))

    summary = run_grid(["YOKSEMBOL"], tfs=["1D"], denominators=("TRY",))

    assert summary.empty
    assert list(summary.columns) == [
        "tf", "currency", "params", "n_trades", "win_rate", "profit_factor", "expectancy_r", "avg_r",
        "avg_max_drawdown_pct", "exposure_pct", "trustworthy", "guven_etiketi", "currency_note", "grid_warning",
    ]


def test_run_grid_agi_dokunmaz_sadece_taklit_edilen_fonksiyonlar_cagrilir(_patch_data_layer):
    calls = _patch_data_layer(n_trades_per_symbol=5, n_bars=250)

    run_grid(["THYAO", "ASELS"], tfs=["1D", "240"], denominators=("TRY", "USD"))

    assert len(calls["ohlcv"]) == 4  # 2 sembol x 2 tf
    assert len(calls["usdtry"]) == 2  # 2 tf (USD istendigi icin)
    assert all(symbol in ("THYAO", "ASELS") for symbol, tf, n in calls["ohlcv"])


# ── save_summary ────────────────────────────────────────────────────────


def test_save_summary_csv_yazar(tmp_path):
    summary = pd.DataFrame(
        {
            "tf": ["1D"], "currency": ["TRY"], "params": ["L5_atr1.0_eps0.05"], "n_trades": [40],
            "win_rate": [55.0], "profit_factor": [1.8], "expectancy_r": [0.3], "avg_r": [0.3],
            "avg_max_drawdown_pct": [-5.0], "exposure_pct": [12.0], "trustworthy": [False],
            "guven_etiketi": ["DUSUK GUVEN (n=40)"], "currency_note": [""], "grid_warning": ["1 hucre karsilastirildi"],
        }
    )
    target = tmp_path / "sub" / "summary.csv"
    result_path = save_summary(summary, path=target)

    assert result_path == target
    assert target.exists()
    loaded = pd.read_csv(target)
    assert loaded.iloc[0]["n_trades"] == 40
