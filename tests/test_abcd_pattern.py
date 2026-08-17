"""Pine-parity testleri: src.analysis.abcd_pattern.

Bkz. docs/spec/spec_abcd_mimari_kararlar.md ve abcd-project/CLAUDE.md kural 6:
detector mantiginda yapilan her degisiklik bu testleri yesil tutmali. Gercek
ag/dosya I/O YOK, tamamen sentetik DataFrame'ler kullanilir.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis.abcd_pattern import Params, atr_wilder, detect, pivot_high, pivot_low

EPS = 0.05  # sentetik zigzag barlar icin kucuk high/low ofseti


def _zigzag_df(anchors: list[tuple[int, float]], eps: float = EPS) -> pd.DataFrame:
    """Anchor barlarda `high`/`low` serisinde KESIN yerel max/min olusturan
    (baska hicbir yerde olmayan) bir OHLC DataFrame'i insa eder: anchor'lar
    arasindan parca-parca lineer bir orta cizgi interpole edilir, sonra
    high/low sabit bir `eps` ile oteler. Sabit bir ofset kesin yerel
    ekstremumlari korur, iki farkli anchor degeri arasindaki kesin monoton
    lineer bir segmentin ic (interior) ekstremumu yoktur, dolayisiyla sadece
    anchor barlari pivot adayidir.
    """
    xs = [a[0] for a in anchors]
    ys = [a[1] for a in anchors]
    n = xs[-1] + 1
    t = np.arange(n)
    mid = np.interp(t, xs, ys)

    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC"),
            "open": mid,
            "high": mid + eps,
            "low": mid - eps,
            "close": mid,
            "volume": np.full(n, 1000.0),
        }
    )


def _bullish_df() -> pd.DataFrame:
    # A(high)@2=100  B(low)@7=80  C(high)@12=90  D(low)@17=70
    return _zigzag_df([(0, 95), (2, 100), (7, 80), (12, 90), (17, 70), (19, 75)])


def _bearish_df() -> pd.DataFrame:
    # A(low)@2=70  B(high)@7=90  C(low)@12=80  D(high)@17=100
    return _zigzag_df([(0, 75), (2, 70), (7, 90), (12, 80), (17, 100), (19, 95)])


PARAMS_L2 = Params(pivot_lookback=2)


# ── pivot_high / pivot_low ──────────────────────────────────────────────


def test_pivot_high_strict_peak_confirmed_l_bars_later():
    high = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    out = pivot_high(high, 2)
    assert out[4] == 3.0  # onaylandi: i = p + L = 2 + 2
    assert np.isnan(out[:4]).all()


def test_pivot_high_tie_is_not_a_pivot():
    # duz tepe: hicbir aday komsularindan KESIN olarak buyuk degil
    high = np.array([1.0, 3.0, 3.0, 3.0, 1.0])
    out = pivot_high(high, 1)
    assert np.all(np.isnan(out))


def test_pivot_low_strict_trough_confirmed_l_bars_later():
    low = np.array([3.0, 2.0, 1.0, 2.0, 3.0])
    out = pivot_low(low, 2)
    assert out[4] == 1.0
    assert np.isnan(out[:4]).all()


def test_pivot_low_tie_is_not_a_pivot():
    low = np.array([3.0, 1.0, 1.0, 1.0, 3.0])
    out = pivot_low(low, 1)
    assert np.all(np.isnan(out))


# ── kesin (strict) alternans ────────────────────────────────────────────


def test_same_type_pivot_does_not_replace_pending_one():
    """Ayni tip (high) ikinci bir pivot geldiginde bekleyen pivot
    DEGISTIRILMEZ, sessizce yoksayilir -- sadece alternan tip (low/high)
    state'e girer. D bari her zaman EN SON alternan pivot olmalidir."""
    # High, High, Low zigzag'i: ilk high (bar 2) A/B/C/D state'ine girer,
    # ikinci high (bar 7) last_ptype hala +1 oldugu icin YOKSAYILIR, ucuncu
    # pivot (low @ bar 12) alternandir ve state'e girer.
    df = _zigzag_df([(0, 90), (2, 100), (7, 105), (12, 80), (16, 85)])
    L = 2
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    ph = pivot_high(high, L)
    pl = pivot_low(low, L)

    # Bar 7'de bir high pivotu var (Pine seviyesinde onaylanmis) ama
    # detect() onu last_ptype==1 oldugu icin state'e almamali.
    assert not np.isnan(ph[7 + L])
    assert not np.isnan(pl[12 + L])

    signals = detect(df, Params(pivot_lookback=L))
    # Sadece 3 pivot var (A/B/C dolu, D yok), tam bir ABCD henuz olusmadi.
    assert signals == []


# ── atr_wilder ───────────────────────────────────────────────────────────


def test_atr_wilder_seeds_with_sma_then_holds_constant():
    n = 20
    df = pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC"),
            "open": np.full(n, 101.0),
            "high": np.full(n, 102.0),
            "low": np.full(n, 100.0),
            "close": np.full(n, 101.0),
            "volume": np.full(n, 1000.0),
        }
    )
    atr = atr_wilder(df, 14)
    assert np.isnan(atr[:13]).all()
    # true range her barda sabit 2.0, dolayisiyla RMA seed'i (ilk 14 TR'nin
    # SMA'si) ve sonraki her smoothed deger de 2.0'dir.
    np.testing.assert_allclose(atr[13:], 2.0)


# ── pattern tespiti ──────────────────────────────────────────────────────


def test_bullish_abcd_detected_with_correct_levels():
    df = _bullish_df()
    signals = detect(df, PARAMS_L2)

    assert len(signals) == 1
    sig = signals[0]
    assert sig.direction == 1
    assert (sig.a_bar, sig.b_bar, sig.c_bar, sig.d_bar) == (2, 7, 12, 17)
    assert sig.signal_bar == sig.d_bar + PARAMS_L2.pivot_lookback == 19

    assert sig.a_price == pytest.approx(100 + EPS)
    assert sig.b_price == pytest.approx(80 - EPS)
    assert sig.c_price == pytest.approx(90 + EPS)
    assert sig.d_price == pytest.approx(70 - EPS)

    ad_range = abs(sig.a_price - sig.d_price)
    assert sig.tp1 == pytest.approx(sig.d_price + ad_range * 0.382)
    assert sig.tp2 == pytest.approx(sig.c_price)

    atr = atr_wilder(df, 14)
    assert sig.sl == pytest.approx(sig.d_price - PARAMS_L2.atr_mult * atr[sig.signal_bar])

    assert sig.entry_ref == pytest.approx(df["close"].iloc[sig.d_bar])
    # D bari son bar (index 19): onay barindan sonra henuz bar yok,
    # dolayisiyla fill_ref NaN olmali, asla uydurulmamali.
    assert np.isnan(sig.fill_ref)


def test_bearish_abcd_detected_with_correct_levels():
    df = _bearish_df()
    signals = detect(df, PARAMS_L2)

    assert len(signals) == 1
    sig = signals[0]
    assert sig.direction == -1
    assert (sig.a_bar, sig.b_bar, sig.c_bar, sig.d_bar) == (2, 7, 12, 17)

    ad_range = abs(sig.a_price - sig.d_price)
    assert sig.tp1 == pytest.approx(sig.d_price - ad_range * 0.382)
    assert sig.tp2 == pytest.approx(sig.c_price)

    atr = atr_wilder(df, 14)
    assert sig.sl == pytest.approx(sig.d_price + PARAMS_L2.atr_mult * atr[sig.signal_bar])
    assert np.isnan(sig.fill_ref)


# ── look-ahead yoklugu ──────────────────────────────────────────────────


def test_fill_ref_is_open_of_bar_after_confirmation_when_available():
    """fill_ref, onay barindan sonraki barin acilisi olmali -- eger o bar
    veri setinde mevcutsa. Bunu gormek icin onay barindan sonra fazladan
    bar ekliyoruz (bullish fixture D=17, onay=19, fazladan bar 20)."""
    df = _bullish_df()
    extra = pd.DataFrame(
        {
            "time": [df["time"].iloc[-1] + pd.Timedelta(hours=4)],
            "open": [77.5],
            "high": [78.0],
            "low": [77.0],
            "close": [77.8],
            "volume": [1000.0],
        }
    )
    df_extended = pd.concat([df, extra], ignore_index=True)

    signals = detect(df_extended, PARAMS_L2)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.signal_bar == 19
    assert sig.fill_ref == pytest.approx(77.5)  # bar 20'nin (=signal_bar+1) open'i


@pytest.mark.parametrize(
    "df_factory, params",
    [
        (_bullish_df, PARAMS_L2),
        (_bearish_df, PARAMS_L2),
    ],
)
def test_signal_bar_equals_d_bar_plus_lookback(df_factory, params):
    df = df_factory()
    signals = detect(df, params)
    for sig in signals:
        assert sig.signal_bar == sig.d_bar + params.pivot_lookback


def _random_zigzag_df(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    steps = rng.normal(loc=0.0, scale=1.5, size=n)
    mid = 100.0 + np.cumsum(steps)
    spread = rng.uniform(0.3, 1.5, size=n)
    high = mid + spread
    low = mid - spread
    close = mid + rng.uniform(-spread, spread, size=n)
    open_ = np.roll(close, 1)
    open_[0] = mid[0]
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(n, 1000.0),
        }
    )


def test_truncating_future_bars_does_not_change_past_signals():
    """Asil look-ahead-yoklugu garantisi: `signal_bar`de onaylanan bir
    sinyal, tam olarak `signal_bar`de biten veriden yeniden uretilebilir
    olmali -- ondan sonraki barlar gecmisi ETKILEMEMELI."""
    df = _random_zigzag_df()
    params = Params()
    full_signals = detect(df, params)
    assert full_signals, "fixture en az bir sinyal uretmeli"

    for sig in full_signals:
        truncated = df.iloc[: sig.signal_bar + 1]
        replay = detect(truncated, params)
        match = [s for s in replay if s.d_bar == sig.d_bar]
        assert len(match) == 1
        replayed = match[0]
        assert replayed.signal_bar == sig.signal_bar
        assert replayed.direction == sig.direction
        assert replayed.tp1 == pytest.approx(sig.tp1)
        assert replayed.tp2 == pytest.approx(sig.tp2)
        assert replayed.sl == pytest.approx(sig.sl)
        assert replayed.entry_ref == pytest.approx(sig.entry_ref)
