"""Pine-parity testleri: src.analysis.harmonic_xabcd.

Bkz. pine/harmonic_formations_v1_indicator.pine (V2.1) ve o modulun ust
notundaki "KRITIK matematiksel not" (XD/XA yon duzeltmesi, 2026-08-18).
Gercek ag/dosya I/O YOK, tamamen sentetik DataFrame'ler kullanilir --
test_abcd_pattern.py::_zigzag_df ile AYNI insa teknigi.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from dataclasses import replace

from src.analysis import abcd_pattern
from src.analysis.harmonic_xabcd import (
    ABCD_PRESET,
    HARMONIC_XABCD_PRESETS,
    Params,
    detect,
    detect_prz,
    match_prz_to_confirmed,
)

ABCD_PRESET_L2 = replace(ABCD_PRESET, pivot_lookback=2)

EPS = 0.05


def _zigzag_df(anchors: list[tuple[int, float]], eps: float = EPS) -> pd.DataFrame:
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


# Elle kurulmus "gercek" GARTLEY LONG: X=100(dusuk) A=161.8(yuksek) B=120(dusuk)
# C=145.08(yuksek) D=113.2252(dusuk). Turetim (bkz. modul ust notu):
#   XA = 61.8; D = A - 0.786*XA = 113.2252  -> xd_ratio = |D-A|/XA = 0.786 (TAM HEDEF)
#   bc_r = (C-B)/(A-B) = 25.08/41.8 = 0.6 (band [0.382,0.886] icinde)
#   cd_bc_r = |D-C|/(C-B) = 31.8548/25.08 = 1.2701 (Gartley band [1.272,1.618], tol ile icinde)
_GARTLEY_LONG_ANCHORS = [(0, 130), (2, 100), (7, 161.8), (12, 120), (17, 145.08), (22, 113.2252), (26, 130)]
PARAMS_GARTLEY_L2 = Params(**{**HARMONIC_XABCD_PRESETS["GARTLEY"].__dict__, "pivot_lookback": 2})


def test_gartley_long_dogru_xd_orani_ile_tespit_edilir():
    df = _zigzag_df(_GARTLEY_LONG_ANCHORS)
    signals = detect(df, PARAMS_GARTLEY_L2)

    assert len(signals) == 1
    sig = signals[0]
    assert sig.direction == 1
    assert sig.x_bar == 2 and sig.a_bar == 7 and sig.b_bar == 12 and sig.c_bar == 17 and sig.d_bar == 22
    assert math.isclose(sig.xd_ratio, 0.786, abs_tol=0.01)
    assert math.isclose(sig.cd_ratio, 1.2701, abs_tol=0.01)


def test_xd_yonu_yanlis_olsaydi_ayni_veri_reddedilirdi():
    """Regresyon: eski (hatali) `|D-X|/XA` formulu bu ayni veriye uygulansaydi
    0.214 cikardi (1 - 0.786), Gartley hedefinden (0.786) fib_tolerance
    disina duserdi -- yani eski kod bu GERCEK Gartley'i REDDEDERDI. Dogru
    formul (`|D-A|/XA`) tam 0.786 verir ve kabul eder (ust test). Bu test
    "ters formul reddederdi" iddiasini dogrudan sayisal olarak dogrular."""
    x_price, a_price, d_price = 100.0, 161.8, 113.2252
    xa = abs(a_price - x_price)
    wrong_xd_r = abs(d_price - x_price) / xa
    correct_xd_r = abs(d_price - a_price) / xa
    assert math.isclose(correct_xd_r, 0.786, abs_tol=0.001)
    assert math.isclose(wrong_xd_r, 1 - 0.786, abs_tol=0.001)
    assert abs(wrong_xd_r - 0.786) > Params(name="x").fib_tolerance


def test_x_noktasi_henuz_olusmamissa_sadece_4_pivotla_sinyal_uretilmez():
    """XABCD 5 nokta gerektirir -- veri setinin EN BASINDA (X'ten once hicbir
    pivot yoksa, yani A ilk tespit edilen pivotsa) A/B/C/D sekli tek basina
    yeterli DEGILDIR, X hala None'dir ve sinyal uretilmemelidir (`abcd_pattern`
    -- klasik 4-noktali AB=CD -- ile bilincli fark budur)."""
    # A(161.8)@7 SERININ ILK pivotu olacak sekilde (once hicbir donus yok,
    # 0->7 duz yukselen), B/C/D golden testle AYNI kalir.
    anchors = [(0, 140), (7, 161.8), (12, 120), (17, 145.08), (22, 113.2252), (26, 130)]
    df = _zigzag_df(anchors)
    signals = detect(df, PARAMS_GARTLEY_L2)
    assert signals == []


def test_dort_formasyon_preset_sayisal_degerleri_pine_ile_esit():
    """`harmonic_formations_v1_indicator.pine`deki (V2.1) `eff_cd_bc_min/max`/
    `eff_xd_target` ternary zincirleriyle BIREBIR ayni sayilar -- bu test
    KASITLI olarak sabit sayilar icerir (Pine'daki sabitlerin YANLISLIKLA
    surukleneceginin/farklilasacaginin erken uyarisi)."""
    g, b, bf, c = (
        HARMONIC_XABCD_PRESETS["GARTLEY"],
        HARMONIC_XABCD_PRESETS["BAT"],
        HARMONIC_XABCD_PRESETS["BUTTERFLY"],
        HARMONIC_XABCD_PRESETS["CRAB"],
    )
    assert (g.cd_bc_min, g.cd_bc_max, g.xd_target) == (1.272, 1.618, 0.786)
    assert (b.cd_bc_min, b.cd_bc_max, b.xd_target) == (1.618, 2.618, 0.886)
    assert (bf.cd_bc_min, bf.cd_bc_max, bf.xd_target) == (1.618, 2.24, 1.27)
    assert (c.cd_bc_min, c.cd_bc_max, c.xd_target) == (2.24, 3.618, 1.618)


# ── PRZ erken tespit ────────────────────────────────────────────────────


def test_prz_onayli_gartley_oncesinde_ayni_bolgeye_giren_bir_olay_uretir():
    """Onayli sinyal olusmadan HEMEN once (D pivotu henuz L bar onaylanmadan),
    fiyat projekte edilen bolgeye girdiginde `detect_prz` bir `PrzEvent`
    uretmeli, ve bu olay `match_prz_to_confirmed` ile SONRADAN onaylanan
    GERCEK sinyalle eslesmeli (`vindicated=True`)."""
    df = _zigzag_df(_GARTLEY_LONG_ANCHORS)
    confirmed = detect(df, PARAMS_GARTLEY_L2)
    events = detect_prz(df, PARAMS_GARTLEY_L2)

    assert len(confirmed) == 1
    assert len(events) >= 1
    # Ayni C bar'ina (=17) ait olaylardan en az biri onayli sinyalle eslesmeli.
    matches = [ev for ev in events if ev.c_bar == 17]
    assert matches
    vindicated = match_prz_to_confirmed(matches, confirmed)
    assert any(vindicated)


def test_prz_hicbir_zaman_gecerli_bolgeye_girmeyen_seride_olay_uretmez():
    """A-B-C onayli ama D projeksiyon bolgesinden UZAK bir yerde olusan
    (bc_r bandin disinda) bir seride, `detect_prz` HICBIR erken olay
    uretmemeli -- yanlis pozitif uretmeme testi."""
    # bc_r = (C-B)/(A-B), B=120 A=161.8 -> C'yi bandin (0.382-0.886) COK
    # disina, cok kucuk bir retracement'a (0.1) tasiyoruz. C sonrasi kisa bir
    # dusus (C'yi gercek bir tepe/peak yapmak icin) ile bitiyor, kuyrukta
    # yeni bir sahte pivot OLUSTURMAYACAK sekilde duz/monoton birakiliyor.
    c_off = 120 + 0.1 * (161.8 - 120)
    anchors = [(0, 130), (2, 100), (7, 161.8), (12, 120), (17, c_off), (24, 100)]
    df = _zigzag_df(anchors)
    events = detect_prz(df, PARAMS_GARTLEY_L2)
    assert events == []


def test_match_prz_to_confirmed_farkli_c_bar_icin_dogrulanmaz():
    """Bir PRZ olayinin `c_bar`i, hicbir onayli sinyalin `c_bar`iyle
    eslesmiyorsa `vindicated=False` olmali."""
    df = _zigzag_df(_GARTLEY_LONG_ANCHORS)
    confirmed = detect(df, PARAMS_GARTLEY_L2)
    fake_event = detect_prz(df, PARAMS_GARTLEY_L2)[0]
    fake_event = fake_event.__class__(**{**fake_event.__dict__, "c_bar": 999})
    assert match_prz_to_confirmed([fake_event], confirmed) == [False]


# ── ABCD_PRESET (klasik AB=CD, is_xabcd=False) -- V2.2 "anlik D" ─────────


def test_abcd_preset_sadece_3_pivotla_projeksiyon_yapabilir():
    """CANLI HATA + DUZELTME regresyon testi (2026-08-18, kullanici TATGD
    karsilastirmasi): eski kod X (4. bir onceki pivot) yoksa TUM projeksiyonu
    atliyordu -- klasik ABCD'nin (is_xabcd=False) X'e HICBIR ZAMAN ihtiyaci
    olmadigi halde. `abcd_pattern._bullish_df` (test_abcd_pattern.py) ile
    AYNI, cd_r=1.0 TAM hedefte olacak sekilde tasarlanmis veri kullanilir --
    A(100)@2 B(80)@7 C(90)@12 D(70)@17, SADECE 3 pivot (X yok) mevcutken
    bile detect_prz bir olay URETMELI."""
    anchors = [(0, 95), (2, 100), (7, 80), (12, 90), (17, 70), (19, 75)]
    df = _zigzag_df(anchors)
    events = detect_prz(df, ABCD_PRESET_L2)
    assert len(events) >= 1
    ev = events[0]
    assert ev.direction == 1
    assert ev.c_bar == 12  # prospektif C = onceki testteki "C" (90@12)


def test_abcd_preset_anlik_sinyal_onayli_sinyalden_ONCE_gelir():
    """V2.2'nin ASIL amaci: 'anlik' (PRZ tabanli) sinyal, D pivotunun
    KENDISININ onaylanmasini (`pivot_lookback` bar) BEKLEYEN klasik
    `abcd_pattern.detect()` sinyalinden ONCE (ya da en gec AYNI barda)
    gelmeli -- ASLA SONRA."""
    anchors = [(0, 95), (2, 100), (7, 80), (12, 90), (17, 70), (19, 75)]
    df = _zigzag_df(anchors)
    confirmed = abcd_pattern.detect(df, abcd_pattern.Params(pivot_lookback=2))
    instant = detect_prz(df, ABCD_PRESET_L2)

    assert len(confirmed) == 1
    assert len(instant) >= 1
    matching_instant = [ev for ev in instant if ev.c_bar == confirmed[0].c_bar]
    assert matching_instant
    assert matching_instant[0].signal_bar <= confirmed[0].signal_bar
