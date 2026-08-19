"""src.analysis.harmonic_confirmation testleri -- sentetik DataFrame'ler,
gercek ag/dosya I/O YOK (bkz. test_harmonic_xabcd.py ile AYNI ilke)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.harmonic_confirmation import (
    ConfirmationFlags,
    compute_indicator_series,
    evaluate_confirmations,
)


def _df(closes: list[float], opens: list[float] | None = None, highs: list[float] | None = None,
        lows: list[float] | None = None, volumes: list[float] | None = None) -> pd.DataFrame:
    n = len(closes)
    opens = opens if opens is not None else closes
    highs = highs if highs is not None else [max(o, c) for o, c in zip(opens, closes)]
    lows = lows if lows is not None else [min(o, c) for o, c in zip(opens, closes)]
    volumes = volumes if volumes is not None else [1000.0] * n
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes,
        }
    )


def test_out_of_range_d_bar_firlatmaz_hepsi_bos():
    df = _df([100.0] * 30)
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=5, b_price=100.0, d_bar=999, d_price=100.0)
    assert flags.score == 0
    assert flags.rsi_value is None and flags.candle_pattern is None and flags.volume_ratio is None


def test_uzun_sinyalde_rsi_pozitif_uyumsuzluk_tespit_edilir():
    # Fiyat B(15) -> D(45) arasi DAHA DUSUK dip yapiyor, ama once guclu bir
    # yukselisle RSI'yi yukseklere tasiyip SONRA yavas/sig bir dususle D'ye
    # inerek RSI'nin B'dekinden DAHA YUKSEK kalmasini saglayan seri.
    closes = list(np.linspace(100, 70, 15))          # dususle B'ye (dip, bar 14)
    closes += list(np.linspace(70, 130, 20))[1:]      # guclu toparlanma (RSI yukselir)
    closes += list(np.linspace(130, 65, 15))[1:]      # D'ye yavas inis (bar 48 civari, B'den DAHA DUSUK)
    df = _df(closes)
    ind = compute_indicator_series(df)
    b_bar = 14
    d_bar = len(closes) - 1
    assert closes[d_bar] < closes[b_bar]
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=b_bar, b_price=closes[b_bar], d_bar=d_bar, d_price=closes[d_bar])
    assert flags.rsi_divergence is True
    assert flags.rsi_ok is True


def test_kisa_sinyalde_uyumsuzluk_yoksa_false():
    closes = list(np.linspace(100.0, 130.0, 40))  # duz yukselis, ayni yonlu RSI -- uyumsuzluk YOK
    df = _df(closes)
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=-1, b_bar=10, b_price=closes[10], d_bar=39, d_price=closes[39])
    assert flags.rsi_divergence is False


def test_asiri_satim_bolgesinden_donus_tespit_edilir():
    closes = list(np.linspace(100.0, 50.0, 20)) + [51.0, 53.0]  # sert dusus (RSI<30), sonra 2 bar yukari donus
    df = _df(closes)
    ind = compute_indicator_series(df)
    d_bar = 20  # ilk donus bari (51.0)
    assert ind.rsi[d_bar] <= 35  # dusuk bolgede olmali (tam esik dogrulanmiyor, kabaca kontrol)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=closes[0], d_bar=d_bar, d_price=closes[d_bar])
    assert flags.rsi_extreme_turn is True


def test_macd_ok_uzun_sinyalde_histogram_yukseliyorsa_true():
    closes = list(np.linspace(100.0, 80.0, 30)) + list(np.linspace(80.0, 90.0, 5))
    df = _df(closes)
    ind = compute_indicator_series(df)
    d_bar = len(closes) - 1
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=5, b_price=closes[5], d_bar=d_bar, d_price=closes[d_bar])
    assert flags.macd_hist is not None
    assert flags.macd_ok == (ind.macd_hist[d_bar] > ind.macd_hist[d_bar - 1])
    assert flags.macd_ok is True


def test_bullish_pin_bar_tespit_edilir():
    # Uzun alt fitil, kucuk govde, ust yaridaki kapanis -- boga pin bar/cekic.
    df = _df(closes=[100.0] * 10, opens=[100.0] * 10, highs=[101.0] * 10, lows=[100.0] * 9 + [90.0], volumes=[1000.0] * 10)
    df.loc[9, "open"] = 100.5
    df.loc[9, "close"] = 100.8
    df.loc[9, "low"] = 90.0
    df.loc[9, "high"] = 101.0
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=9, d_price=90.0)
    assert flags.candle_pattern == "PIN_BAR"
    assert flags.candle_ok is True


def test_bullish_engulfing_tespit_edilir():
    df = _df(closes=[100.0] * 10, volumes=[1000.0] * 10)
    df.loc[8, ["open", "close", "high", "low"]] = [100.0, 95.0, 100.5, 94.5]  # kirmizi
    df.loc[9, ["open", "close", "high", "low"]] = [94.0, 101.0, 101.5, 93.5]  # yesil, 8'i YUTUYOR
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=9, d_price=93.5)
    assert flags.candle_pattern == "ENGULFING"


def test_hicbir_mum_paterni_yoksa_none():
    df = _df(closes=[100.0, 100.2, 100.1, 100.3])
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=3, d_price=100.3)
    assert flags.candle_pattern is None
    assert flags.candle_ok is False


def test_hacim_sikisma_ve_patlama_birlikte_volume_ok_true():
    baseline = [2000.0] * 15   # taban (uzak gecmis)
    recent = [500.0] * 5       # D'ye giden sikisma (dusuk hacim)
    burst = [3000.0]           # donus bari -- patlama
    volumes = baseline + recent + burst
    closes = [100.0] * len(volumes)
    df = _df(closes, volumes=volumes)
    ind = compute_indicator_series(df)
    d_bar = len(volumes) - 1
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=d_bar, d_price=100.0)
    assert flags.volume_compression is True
    assert flags.volume_expansion is True
    assert flags.volume_ok is True


def test_hacim_duz_seride_compression_false():
    volumes = [1000.0] * 30
    closes = [100.0] * 30
    df = _df(closes, volumes=volumes)
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=29, d_price=100.0)
    assert flags.volume_compression is False
    assert flags.volume_ok is False


def test_score_dort_kosulun_toplami():
    df = _df(closes=[100.0] * 10)
    ind = compute_indicator_series(df)
    flags = evaluate_confirmations(df, ind, direction=1, b_bar=0, b_price=100.0, d_bar=9, d_price=100.0)
    assert flags.score == sum([flags.rsi_ok, flags.macd_ok, flags.candle_ok, flags.volume_ok])
    assert 0 <= flags.score <= 4
