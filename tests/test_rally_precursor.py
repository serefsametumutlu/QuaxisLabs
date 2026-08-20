"""src.analysis.rally_precursor testleri -- sentetik DataFrame'ler, gercek
ag/dosya I/O YOK (bkz. test_abcd_pattern.py ile AYNI insa felsefesi)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.rally_precursor import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    extract_features,
    find_rally_candidates,
)


def _zigzag_df(anchors: list[tuple[int, float]], eps: float = 0.3) -> pd.DataFrame:
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    n = xs[-1] + 1
    t = np.arange(n)
    mid = np.interp(t, xs, ys)
    return pd.DataFrame(
        {
            "time": pd.date_range("2018-01-01", periods=n, freq="1D", tz="UTC"),
            "open": mid,
            "high": mid + eps,
            "low": mid - eps,
            "close": mid,
            "volume": np.full(n, 1_000_000.0),
        }
    )


def test_yetersiz_veri_bos_liste():
    df = _zigzag_df([(0, 100), (20, 90), (40, 100)])
    assert find_rally_candidates(df, "TEST", "1D", pivot_lookback=10, max_lookahead_bars=120) == []


def test_buyuk_yukselisten_once_dip_dogru_etiketlenir():
    # Dip @ bar ~60 (fiyat 80), sonra buyuk bir yukselisle 200'e -- rally_pct
    # yuksek olmali. Serinin sonuna kadar (max_lookahead + isinma) YETERLI
    # bar birakilir.
    anchors = [
        (0, 100), (20, 130), (40, 110), (60, 80),  # dip burada
        (140, 200),  # buyuk yukselis (rally_pct ~= (200-80)/80*100 = 150)
        (200, 190),
    ]
    df = _zigzag_df(anchors)
    candidates = find_rally_candidates(df, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=100)
    assert len(candidates) > 0

    dip_candidates = [c for c in candidates if abs(c.low_price - 80.0) < 1.0]
    assert dip_candidates, "80 civarindaki dip aday olarak bulunmali"
    c = dip_candidates[0]
    assert c.rally_pct > 100.0  # buyuk bir yukselis yakalanmali


def test_serinin_sonundaki_dipler_yeterli_ileri_veri_olmadigindan_DISLANIR():
    anchors = [(0, 100), (20, 80), (40, 100), (60, 70), (80, 100)]
    df = _zigzag_df(anchors)
    # max_lookahead_bars COK BUYUK -- hicbir dip yeterli ileri veriye sahip DEGIL.
    candidates = find_rally_candidates(df, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=1000)
    assert candidates == []


def test_fibonacci_geri_cekilme_dogru_hesaplanir():
    # Isinma sacagi (0->20->40, bar 0 seri basi oldugu icin pivot OLAMAZ,
    # bar20/bar40 GERCEK pivotlar olur) + ASIL test edilen bacak: dip(100)@40
    # -> tepe(200)@80. Sonraki dip 0.618 geri cekilme seviyesinde:
    # 200 - 0.618*(200-100) = 138.2, bar 120'de.
    retr_price = 200.0 - 0.618 * (200.0 - 100.0)
    anchors = [(0, 70), (20, 130), (40, 100), (80, 200), (120, retr_price), (240, 250)]
    df = _zigzag_df(anchors)
    candidates = find_rally_candidates(df, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=100)
    target = [c for c in candidates if abs(c.low_price - retr_price) < 1.0]
    assert target, "0.618 geri cekilme dipi aday olarak bulunmali"
    c = target[0]
    row = c.__dict__
    feats = extract_features(row, df)
    assert feats["fib_retracement"] is not None
    assert feats["fib_retracement"] == pytest.approx(0.618, abs=0.03)
    assert feats["fib_dist_from_618"] == pytest.approx(0.0, abs=0.03)


def test_extract_features_look_ahead_yok():
    """KRITIK: `extract_features` `signal_bar`den SONRAKI veriyi GORMEMELI --
    gelecegi degistirmek gecmis ozellikleri ETKILEMEMELI."""
    anchors_a = [(0, 100), (20, 80), (40, 110), (60, 90), (140, 130)]
    anchors_b = [(0, 100), (20, 80), (40, 110), (60, 90), (140, 400)]  # SADECE gelecek FARKLI
    df_a = _zigzag_df(anchors_a)
    df_b = _zigzag_df(anchors_b)

    cands_a = find_rally_candidates(df_a, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=70)
    cands_b = find_rally_candidates(df_b, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=70)
    assert len(cands_a) > 0 and len(cands_b) > 0

    feats_a = extract_features(cands_a[0].__dict__, df_a)
    feats_b = extract_features(cands_b[0].__dict__, df_b)
    for key in ALL_FEATURES:
        if key in ("momentum_signal_nearby", "harmonic_signal_nearby"):
            continue  # bu ikisi TUM df'i (signal_bar+1'e kesilmis) tarar, gelecek zaten YOK
        assert feats_a[key] == feats_b[key], f"{key} gelecekten ETKILENMEMELI"


def test_extract_features_tum_ozellikler_sozlukte_mevcut():
    anchors = [(0, 100), (30, 70), (60, 120), (90, 60), (250, 300)]
    df = _zigzag_df(anchors)
    candidates = find_rally_candidates(df, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=150)
    assert len(candidates) > 0
    feats = extract_features(candidates[-1].__dict__, df)
    for key in ALL_FEATURES:
        assert key in feats


def test_higher_low_dogru_isaretlenir():
    # Isinma sacagi (bar0 seri basi, pivot OLAMAZ) + dip1(100)@40 -> tepe(150)@60
    # -> dip2(120)@80 [dip1'den (100) YUKSEK -- higher low].
    anchors = [(0, 70), (20, 130), (40, 100), (60, 150), (80, 120), (220, 250)]
    df = _zigzag_df(anchors)
    candidates = find_rally_candidates(df, "TEST", "1D", pivot_lookback=5, max_lookahead_bars=130)
    dip2 = [c for c in candidates if abs(c.low_price - 120.0) < 1.0]
    assert dip2
    feats = extract_features(dip2[0].__dict__, df)
    assert feats["higher_low"] == 1


def test_categorical_features_all_features_alt_kumesi():
    assert set(CATEGORICAL_FEATURES).issubset(set(ALL_FEATURES))
