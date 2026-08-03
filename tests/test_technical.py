"""src/analysis/technical.py testleri -- Faz 15 (Teknik Analiz).

BU DOSYA KRITIK: teknik gosterge hatalari sessizce YANLIS sonuc uretir
(skorlama gibi bariz bir "0/10" ile kendini ele vermez). Bu yuzden her
gosterge EN AZ bir BAGIMSIZ referans degeriyle dogrulanir:

  - RSI(14): tamamen ELLE (kagit uzerinde) turetilmis kesir aritmetigiyle
    dogrulanir (asagidaki test docstring'inde adim adim yazili) -- gorev
    talimatinin ozellikle istedigi yontem.
  - SMA/EMA/MACD/Bollinger/ATR: technical.py'nin KENDI kodundan TAMAMEN
    BAGIMSIZ, bu dosya icinde yazilmis naif bir float referans
    implementasyonuyla (farkli kod yolu -- rolling-sum optimizasyonu
    YOK, her adimda yeniden hesaplanir) capraz dogrulanir. Referans
    degerler `python3` ile ayri bir REPL'de onceden hesaplanip buraya
    sabit olarak yazildi (bkz. yorumlar).

Hicbir ag istegi/I-O yoktur (technical.py saf matematik).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.analysis.technical import (
    PriceBar,
    atr_wilder,
    average_volume,
    bollinger_bands,
    compute_snapshot,
    ema,
    ema_series,
    macd,
    price_distance_from_sma_pct,
    rsi_wilder,
    sma,
    sma_series,
    volume_ratio_pct,
    week_52_range,
)


def _d(value) -> Decimal:
    return Decimal(str(value))


def _bars_from_closes(closes: list[float], start: date = date(2026, 1, 1)) -> list[PriceBar]:
    """Testler icin sentetik bar listesi -- high=close*1.01, low=close*0.99."""
    bars = []
    for i, close in enumerate(closes):
        c = _d(close)
        bars.append(
            PriceBar(
                trade_date=start + timedelta(days=i),
                high=c * _d("1.01"),
                low=c * _d("0.99"),
                close=c,
                volume=_d(1000 + i),
            )
        )
    return bars


# --- SMA / EMA -----------------------------------------------------------------


def test_sma_basit_aritmetik_seri_elle_dogrulanir():
    """Aritmetik dizi [10,11,...,20] -- son 5 deger [16,17,18,19,20],
    ortalamasi ELLE: (16+17+18+19+20)/5 = 90/5 = 18."""
    closes = [_d(v) for v in range(10, 21)]  # 10..20, 11 deger
    assert sma(closes, 5) == Decimal(18)


def test_sma_series_yetersiz_veride_none_doner():
    closes = [_d(v) for v in [1, 2, 3]]
    series = sma_series(closes, 5)
    assert series == [None, None, None]
    assert sma(closes, 5) is None


def test_ema_aritmetik_seride_sma_ile_ayni_noktaya_yakinsar_elle_dogrulanir():
    """[10,11,...,20] icin EMA(5), k=2/6=1/3, seed=SMA(ilk5)=(10+..+14)/5=12.
    Elle adim adim (rapor edilen her adimda (x-onceki)/3 + onceki):
      idx5 (x=15): (15-12)/3+12=13
      idx6 (x=16): (16-13)/3+13=14
      idx7 (x=17): (17-14)/3+14=15
      idx8 (x=18): (18-15)/3+15=16
      idx9 (x=19): (19-16)/3+16=17
      idx10(x=20): (20-17)/3+17=18
    Sonuc: EMA(5) = 18 (bu ozel aritmetik-dizi durumunda SMA'yla AYNI --
    tesadufi degil, sabit artisli bir seride EMA sabit adimda SMA'ya esitlenir)."""
    closes = [_d(v) for v in range(10, 21)]
    assert ema(closes, 5) == Decimal(18)


def test_ema_series_yetersiz_veride_none_doner():
    closes = [_d(v) for v in [1, 2, 3]]
    assert ema_series(closes, 5) == [None, None, None]
    assert ema(closes, 5) is None


# --- RSI (Wilder) -- ELLE HESAPLANMIS referans -----------------------------


def test_rsi_wilder_elle_hesaplanan_referans_degerle_esit():
    """Kapanislar: [100,101,100,101,100,101,100,101,100,101,100,101,100,101,100,102]
    (16 deger, 15 delta -- period+1 = 15 GEREKIYOR, tam siniirinda).

    ELLE HESAP:
      Delta'lar (1..14, 7 cift +1/-1): +1,-1,+1,-1,+1,-1,+1,-1,+1,-1,+1,-1,+1,-1
      -> ilk_ort_kazanc = (7*1)/14 = 0.5 ; ilk_ort_kayip = (7*1)/14 = 0.5
      15. delta (delta15) = 102-100 = +2 (kazanc=2, kayip=0)
      Wilder yumusatmasi (period=14):
        ort_kazanc = (0.5*13 + 2)/14 = 8.5/14 = 17/28
        ort_kayip  = (0.5*13 + 0)/14 = 6.5/14 = 13/28
      RS  = (17/28) / (13/28) = 17/13
      RSI = 100 - 100/(1 + 17/13) = 100 - 100/(30/13) = 100 - 1300/30
          = (3000 - 1300)/30 = 1700/30 = 56,6666...  (tam kesir)

    Bagimsiz bir python REPL'inde float aritmetigiyle de dogrulandi:
    56.666666666666664 (bkz. gorev notlari) -- kesirle BIREBIR uyumlu.
    """
    closes = [_d(v) for v in [100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 102]]

    rsi = rsi_wilder(closes, period=14)

    expected = Decimal(1700) / Decimal(30)
    assert rsi is not None
    assert abs(rsi - expected) < Decimal("0.0000001")


def test_rsi_wilder_tum_kazanc_ise_100_doner():
    """14 ardisik +1 hareket -- hic kayip yok -> RS sonsuz limiti -> RSI=100."""
    closes = [_d(100 + i) for i in range(15)]  # 100..114, 14 delta, hepsi +1
    assert rsi_wilder(closes, period=14) == Decimal(100)


def test_rsi_wilder_fiyat_tamamen_sabitse_50_doner():
    closes = [_d(100)] * 20
    assert rsi_wilder(closes, period=14) == Decimal(50)


def test_rsi_wilder_yetersiz_veride_none_doner():
    closes = [_d(v) for v in range(100, 110)]  # 10 deger, period+1=15 gerekir
    assert rsi_wilder(closes, period=14) is None


# --- MACD -- bagimsiz naif referans implementasyonu ile capraz dogrulama ------


_SYNTHETIC_CLOSES = [
    100.0, 103.1552, 106.0464, 108.4333, 110.1204, 110.9749, 110.9385, 110.0321, 108.3546, 106.0738,
    103.4112, 100.6225, 97.9748, 95.7223, 94.0842, 93.2247, 93.2384, 94.1419, 95.8724, 98.2931,
    101.2058, 104.3681, 107.5154, 110.3844, 112.7367, 114.38, 115.1854, 115.0989, 114.146, 112.4297,
    110.1212, 107.4445, 104.6567, 102.0246, 99.8013, 98.203, 97.3906, 97.4545, 98.4067, 100.1802,
]  # 40 deger; sin dalgasi + hafif trend ile uretildi (100 + 10*sin(i*0.3) + 0.2*i, 4 basamak yuvarlandi)


def _naive_ema_series(values: list[float], period: int) -> list[float | None]:
    """technical.ema_series() ile AYNI formul ama TAMAMEN AYRI/naif kod --
    capraz dogrulama icin (Python float, rolling-sum optimizasyonu yok)."""
    k = 2 / (period + 1)
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = (values[i] - prev) * k + prev
        out[i] = prev
    return out


def test_macd_bagimsiz_float_referansiyla_esit():
    """Beklenen degerler (bagimsiz python REPL'inde onceden hesaplandi,
    bkz. modul docstring'i): macd_line=-1.4334982387373287,
    signal=0.03758363853489943, histogram=-1.471081877272228."""
    closes = [_d(v) for v in _SYNTHETIC_CLOSES]

    result = macd(closes, fast=12, slow=26, signal=9)

    assert result is not None
    macd_line, signal_line, histogram = result
    assert abs(macd_line - _d("-1.4334982387373287")) < Decimal("0.0001")
    assert abs(signal_line - _d("0.03758363853489943")) < Decimal("0.0001")
    assert abs(histogram - _d("-1.471081877272228")) < Decimal("0.0001")

    # Ayrica bu dosyadaki BAGIMSIZ naif referans implementasyonuyla da
    # (float, farkli kod yolu) capraz kontrol:
    ema_fast = _naive_ema_series(_SYNTHETIC_CLOSES, 12)
    ema_slow = _naive_ema_series(_SYNTHETIC_CLOSES, 26)
    macd_series_ref = [ema_fast[i] - ema_slow[i] for i in range(25, len(_SYNTHETIC_CLOSES))]
    signal_ref = _naive_ema_series(macd_series_ref, 9)
    assert abs(float(macd_line) - macd_series_ref[-1]) < 1e-6
    assert abs(float(signal_line) - signal_ref[-1]) < 1e-6


def test_macd_yetersiz_veride_none_doner():
    closes = [_d(v) for v in range(30)]  # slow+signal=35 gerekir
    assert macd(closes, 12, 26, 9) is None


# --- Bollinger Bantlari ---------------------------------------------------------


def test_bollinger_bands_bagimsiz_float_referansiyla_esit():
    """Beklenen (bagimsiz REPL): middle=106.156685, std=6.370695108485022
    (POPULASYON std -- N'e bolme), upper=118.89807521697004,
    lower=93.41529478302995."""
    closes = [_d(v) for v in _SYNTHETIC_CLOSES]

    result = bollinger_bands(closes, period=20, num_std=Decimal("2"))

    assert result is not None
    upper, middle, lower = result
    assert abs(middle - _d("106.156685")) < Decimal("0.0001")
    assert abs(upper - _d("118.89807521697004")) < Decimal("0.0001")
    assert abs(lower - _d("93.41529478302995")) < Decimal("0.0001")


def test_bollinger_bands_yetersiz_veride_none_doner():
    closes = [_d(v) for v in range(10)]  # period=20 gerekir
    assert bollinger_bands(closes, period=20) is None


# --- ATR (Wilder) ----------------------------------------------------------


def test_atr_wilder_bagimsiz_float_referansiyla_esit():
    """Sentetik barlar: high=close*1.01, low=close*0.99 -- beklenen ATR14
    (bagimsiz REPL): 2.893162249548373."""
    bars = _bars_from_closes(_SYNTHETIC_CLOSES)

    atr = atr_wilder(bars, period=14)

    assert atr is not None
    assert abs(atr - _d("2.893162249548373")) < Decimal("0.0001")


def test_atr_wilder_yetersiz_veride_none_doner():
    bars = _bars_from_closes(_SYNTHETIC_CLOSES[:10])  # period+1=15 gerekir
    assert atr_wilder(bars, period=14) is None


# --- 52 hafta araligi ------------------------------------------------------------


def test_week_52_range_elle_kurgulanan_tepe_ve_dip_ile_dogrulanir():
    """252 bar: hepsi high=200/low=200 SABIT, index 100'de high=250 (TEPE),
    index 50'de low=150 (DIP), son kapanis=200.
    Elle: yuksek=250, dusuk=150, konum% = (200-150)/(250-150)*100 = 50."""
    bars = []
    for i in range(252):
        high = _d(250) if i == 100 else _d(200)
        low = _d(150) if i == 50 else _d(200)
        bars.append(PriceBar(trade_date=date(2025, 1, 1) + timedelta(days=i), high=high, low=low, close=_d(200), volume=_d(1)))

    result = week_52_range(bars)

    assert result == (Decimal(250), Decimal(150), Decimal(50))


def test_week_52_range_yetersiz_veride_none_doner():
    bars = _bars_from_closes(_SYNTHETIC_CLOSES)  # 40 bar, 252 gerekir
    assert week_52_range(bars) is None


def test_week_52_range_fiyat_tamamen_sabitse_konum_50_doner():
    bars = [
        PriceBar(trade_date=date(2025, 1, 1) + timedelta(days=i), high=_d(100), low=_d(100), close=_d(100), volume=_d(1))
        for i in range(252)
    ]
    assert week_52_range(bars) == (Decimal(100), Decimal(100), Decimal(50))


# --- Hacim -------------------------------------------------------------------


def test_average_volume_ve_volume_ratio_elle_dogrulanir():
    """19 gun hacim=100, son gun hacim=300. Elle:
    ortalama = (19*100 + 300)/20 = (1900+300)/20 = 2200/20 = 110.
    oran% = 300/110*100 = 30000/110 = 272,7272... """
    volumes = [_d(100)] * 19 + [_d(300)]

    avg = average_volume(volumes, period=20)
    ratio = volume_ratio_pct(volumes, period=20)

    assert avg == Decimal(110)
    expected_ratio = Decimal(30000) / Decimal(110)
    assert ratio is not None
    assert abs(ratio - expected_ratio) < Decimal("0.0000001")


def test_average_volume_yetersiz_veride_none_doner():
    assert average_volume([_d(1), _d(2)], period=20) is None
    assert volume_ratio_pct([_d(1), _d(2)], period=20) is None


# --- Fiyat / SMA mesafesi ------------------------------------------------------


def test_price_distance_from_sma_pct_elle_dogrulanir():
    """fiyat=110, sma=100 -> (110-100)/100*100 = %10."""
    assert price_distance_from_sma_pct(_d(110), _d(100)) == Decimal(10)


def test_price_distance_from_sma_pct_sma_none_ise_none_doner():
    assert price_distance_from_sma_pct(_d(110), None) is None


# --- compute_snapshot orkestrasyonu -------------------------------------------


def test_compute_snapshot_bos_bar_listesinde_none_doner():
    assert compute_snapshot([]) is None


def test_compute_snapshot_yeterli_veriyle_tum_alanlari_doldurur():
    """260 gunluk (>=252, SMA200 icin de yeterli) bir seri -- hicbir alan
    beklenmedik sekilde None KALMAMALI (K4: sadece GERCEKTEN yetersiz veri
    None doner, burada hepsi yeterli)."""
    closes = [100.0 + i * 0.1 for i in range(260)]
    bars = _bars_from_closes(closes)

    snapshot = compute_snapshot(bars)

    assert snapshot is not None
    assert snapshot.as_of_date == bars[-1].trade_date
    assert snapshot.price == bars[-1].close
    assert snapshot.sma_20 is not None
    assert snapshot.sma_50 is not None
    assert snapshot.sma_200 is not None
    assert snapshot.rsi_14 is not None
    assert snapshot.macd_line is not None
    assert snapshot.bb_upper is not None
    assert snapshot.atr_14 is not None
    assert snapshot.week52_high is not None
    assert snapshot.avg_volume_20 is not None
    assert snapshot.price_vs_sma200_pct is not None


def test_compute_snapshot_grafik_serisi_sadece_son_6_ayi_kapsar():
    """183 gunluk kesim penceresi -- gunluk (bosluksuz) 260 barlik seride
    son 184 bar (indeks 76..259) kalmali (bkz. hesap: son_tarih-183gun
    -> indeks >= 260-1-183 = 76)."""
    closes = [100.0 + i * 0.1 for i in range(260)]
    bars = _bars_from_closes(closes)

    snapshot = compute_snapshot(bars)

    assert snapshot is not None
    assert len(snapshot.chart_dates) == 184
    assert snapshot.chart_dates[0] == bars[76].trade_date
    assert snapshot.chart_dates[-1] == bars[-1].trade_date
    assert snapshot.chart_closes[-1] == bars[-1].close


def test_compute_snapshot_yetersiz_veride_ilgili_alanlar_none_ama_snapshot_uretilir():
    """Sadece 30 barlik bir seri -- SMA200/RSI(gerekli olsa da 30>15 aslinda
    yeterli, ama SMA200/hafta52 gibi UZUN pencereler None kalmali, kisa
    pencereler (SMA20, RSI14) DOLU olmali -- K4: kismi eksiklik TUM
    snapshot'i None yapmaz."""
    closes = [100.0 + i * 0.1 for i in range(30)]
    bars = _bars_from_closes(closes)

    snapshot = compute_snapshot(bars)

    assert snapshot is not None
    assert snapshot.sma_20 is not None
    assert snapshot.rsi_14 is not None
    assert snapshot.sma_200 is None
    assert snapshot.week52_high is None
    assert snapshot.price_vs_sma200_pct is None  # sma200 None oldugu icin
