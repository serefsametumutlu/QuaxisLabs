"""Pine-parity testleri: src.analysis.momentum_confluence.

Bkz. `pine/momentum confluence 1.txt` / `pine/momentum confluence 2.txt`.
Gercek ag/dosya I/O YOK, tamamen sentetik DataFrame'ler kullanilir --
`test_abcd_pattern.py` ile AYNI insa felsefesi.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.momentum_confluence import Params, _compute_trf, _compute_wavetrend, _ema, detect


def _ohlcv(close: list[float], volume: list[float] | None = None, open_: list[float] | None = None) -> pd.DataFrame:
    n = len(close)
    close_arr = np.array(close, dtype=float)
    open_arr = np.array(open_, dtype=float) if open_ is not None else close_arr.copy()
    high = np.maximum(open_arr, close_arr) + 0.01
    low = np.minimum(open_arr, close_arr) - 0.01
    vol = np.array(volume, dtype=float) if volume is not None else np.full(n, 1000.0)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": open_arr,
            "high": high,
            "low": low,
            "close": close_arr,
            "volume": vol,
        }
    )


# ── _ema ────────────────────────────────────────────────────────────────


def test_ema_ilk_deger_ile_seed_edilir():
    values = np.array([10.0, 20.0, 20.0])
    out = _ema(values, span=2)  # alpha = 2/3
    assert out[0] == 10.0
    assert out[1] == pytest.approx(10.0 + (20.0 - 10.0) * (2 / 3))
    assert out[2] == pytest.approx(out[1] + (20.0 - out[1]) * (2 / 3))


def test_ema_tekil_nan_girdi_sonsuza_kadar_yayilmaz():
    """CANLI HATA + DUZELTME regresyon testi (2026-08-18): eski `_ema`,
    ilk deger NaN ise (orn. WaveTrend'in `ci[0]` sifira-bolme korumasi
    yuzunden NaN donmesi) o NaN'i SEED olarak alip TUM seriyi NaN'a
    cevirirdi -- V2'nin hicbir zaman sinyal uretmemesinin kok nedeniydi.
    Simdi: ilk NaN-olmayan degerle seed edilir, aradaki tekil NaN'larda
    onceki deger korunur (yayilmaz)."""
    values = np.array([np.nan, 5.0, 5.0, np.nan, 5.0, 5.0])
    out = _ema(values, span=2)
    assert np.isnan(out[0])
    assert not np.isnan(out[1])
    assert not np.any(np.isnan(out[1:]))  # bar 3'teki tekil NaN sonrasini bozmamali
    assert out[-1] == pytest.approx(5.0, abs=0.01)


def test_wavetrend_bar_0_sifira_bolme_serinin_tamamini_nan_yapmaz():
    """Ust duzey regresyon: `_compute_wavetrend`, bar 0'da `d=0` (esa
    bar 0'da ap'a esitlenerek seed edildigi icin) -> `ci[0]` NaN
    ureteceginden, eski kod wt1/wt2'nin TAMAMINI NaN doonduruyordu."""
    rng = np.random.default_rng(3)
    n = 60
    close = 100.0 + np.cumsum(rng.normal(0, 1, n))
    high = close + 1.0
    low = close - 1.0
    wt1, wt2 = _compute_wavetrend(high, low, close, chan_len=10, avg_len=21, smooth=4)
    assert not np.all(np.isnan(wt1))
    assert np.isnan(wt1).sum() < n  # sadece bar 0 (en fazla birkac bar) NaN kalabilir, TUMU DEGIL


# ── _compute_trf (Twin Range Filter) ─────────────────────────────────────


def test_trf_duz_fiyatta_filt_kaynagi_birebir_takip_eder():
    """Fiyat tamamen duzse (hic degisim yok), smrng=0 her barda -- filt
    matematiksel olarak src'ye ESIT olmali, upward/downward hic tetiklenmez
    (filt[i]==filt[i-1] her bar, ne > ne <)."""
    src = np.full(20, 100.0)
    filt, upward, downward = _compute_trf(src, per1=12, mult1=1.0, per2=4, mult2=2.0)
    assert np.allclose(filt, 100.0)
    assert np.all(upward == 0.0)
    assert np.all(downward == 0.0)


def test_trf_surekli_yukselen_fiyatta_upward_sayaci_artar():
    src = np.arange(1.0, 40.0, 1.0) * 10.0  # kesintisiz artan seri
    filt, upward, downward = _compute_trf(src, per1=12, mult1=1.0, per2=4, mult2=2.0)
    # Yeterince bar sonra (isinma sonrasi) filt de artan olmali, upward pozitif kalmali
    assert upward[-1] > 0
    assert downward[-1] == 0.0
    assert filt[-1] > filt[10]


# ── detect() -- yapisal ozellikler ────────────────────────────────────────


def _dusustensonra_patlamali_kirilim_serisi(n_down: int = 40, n_up: int = 6) -> pd.DataFrame:
    """Uzun bir dusus (TRF'yi bearish yapip downward sayacini biriktirir),
    ardindan SIKI/dusuk-volatiliteli birkac bar, sonra hacimli SERT bir
    yukselis (EMA kirilimi + hacim patlamasi + TRF flip ayni pencerede
    olusma sansi icin)."""
    rng = np.random.default_rng(7)
    down = 200.0 - np.cumsum(rng.uniform(0.5, 1.5, n_down))
    squeeze_base = down[-1]
    squeeze = squeeze_base + rng.uniform(-0.05, 0.05, 5)
    breakout = squeeze[-1] + np.cumsum(rng.uniform(2.0, 4.0, n_up))
    close = np.concatenate([down, squeeze, breakout])
    volume = np.full(len(close), 1000.0)
    # Kirilim barlarinda hacim patlamasi
    volume[len(down) + len(squeeze):] *= 3.0
    return _ohlcv(list(close), volume=list(volume))


def test_detect_v1_gecerli_tp_sl_sirasi_uretir():
    df = _dusustensonra_patlamali_kirilim_serisi()
    signals = detect(df, Params(), variant="v1")
    for sig in signals:
        assert sig.sl < sig.entry_ref < sig.tp1 < sig.tp2
        assert sig.direction == 1


def test_detect_v2_v1den_daha_az_veya_esit_sinyal_uretir():
    """Kullanici gozlemi (2026-08-18): V2, V1'in TUM kosullarini + WaveTrend
    + yesil mum + daha siki EMA sarti ekliyor -- bu YAPISAL olarak V2'nin
    sinyal kumesinin V1'inkinin bir ALT KUMESI (sayica <=) olmasini
    GEREKTIRIR, kaynak Pine dosyalarinin mantigindan DOGRUDAN."""
    df = _dusustensonra_patlamali_kirilim_serisi()
    v1_signals = detect(df, Params(), variant="v1")
    v2_signals = detect(df, Params(), variant="v2")
    assert len(v2_signals) <= len(v1_signals)
    v1_bars = {s.signal_bar for s in v1_signals}
    v2_bars = {s.signal_bar for s in v2_signals}
    assert v2_bars.issubset(v1_bars)


def test_detect_ilk_14_barda_atr_tanimsizken_sinyal_uretilmez():
    df = _dusustensonra_patlamali_kirilim_serisi()
    signals = detect(df, Params(), variant="v1")
    assert all(sig.signal_bar >= 14 for sig in signals)


def test_detect_bilinmeyen_variant_hata_firlatir():
    df = _ohlcv([100.0] * 30)
    with pytest.raises(ValueError):
        detect(df, Params(), variant="v3")


def test_detect_duz_fiyatta_hicbir_sinyal_uretilmez():
    df = _ohlcv([100.0] * 60)
    assert detect(df, Params(), variant="v1") == []
    assert detect(df, Params(), variant="v2") == []
