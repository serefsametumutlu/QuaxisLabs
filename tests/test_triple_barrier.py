"""src.analysis.triple_barrier testleri."""

from __future__ import annotations

import numpy as np

from src.analysis.triple_barrier import label_outcome


def _bars(highs, lows, closes):
    return np.array(highs, dtype=float), np.array(lows, dtype=float), np.array(closes, dtype=float)


def test_uzun_tp_once_vurulursa_win_true():
    high, low, close = _bars([101, 102, 106, 105], [99, 100, 104, 103], [100.5, 101, 105, 104])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=105.0, sl=98.0, direction=1, max_hold_bars=10)
    assert out.win is True
    assert out.hit == "TP"
    assert out.r_multiple > 0


def test_uzun_sl_once_vurulursa_win_false():
    high, low, close = _bars([101, 100, 99], [99, 97, 96], [100, 97.5, 96.5])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=110.0, sl=98.0, direction=1, max_hold_bars=10)
    assert out.win is False
    assert out.hit == "SL"
    assert out.r_multiple == -1.0


def test_ayni_barda_hem_tp_hem_sl_araliginda_sl_oncelikli():
    # entry bari (idx0) + bir SONRAKI bar (idx1) -- o barin high'i TP'yi,
    # low'u SL'yi ayni anda gecerse (genis bar): muhafazakar varsayim SL kazanir.
    high, low, close = _bars([100, 120], [99, 90], [99.5, 105])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=110.0, sl=95.0, direction=1, max_hold_bars=5)
    assert out.hit == "SL"
    assert out.win is False


def test_hicbiri_vurulmazsa_timeout_isaret_getiriye_gore():
    high, low, close = _bars([101, 102, 103], [99, 100, 101], [100.5, 101.5, 102.5])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=200.0, sl=50.0, direction=1, max_hold_bars=3)
    assert out.hit == "TIMEOUT"
    assert out.win is True  # son kapanis > giris
    assert out.r_multiple > 0


def test_kisa_yonde_sl_ve_tp_ters_calisir():
    high, low, close = _bars([100, 108, 106], [98, 106, 104], [99.5, 107, 105])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=90.0, sl=107.0, direction=-1, max_hold_bars=10)
    assert out.win is False
    assert out.hit == "SL"


def test_seri_sonuna_cok_yakin_giriste_insufficient_data():
    high, low, close = _bars([100], [99], [99.5])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=105.0, sl=95.0, direction=1, max_hold_bars=10)
    assert out.hit == "INSUFFICIENT_DATA"
    assert out.win is False
    assert out.r_multiple == 0.0


def test_sifir_risk_firlatmaz_insufficient_data_doner():
    high, low, close = _bars([101, 102], [99, 100], [100.5, 101.5])
    out = label_outcome(high, low, close, entry_bar=0, entry_price=100.0, tp=105.0, sl=100.0, direction=1, max_hold_bars=5)
    assert out.hit == "INSUFFICIENT_DATA"
