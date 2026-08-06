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
    adx_wilder,
    atr_wilder,
    average_volume,
    bollinger_bands,
    compute_snapshot,
    ema,
    ema_series,
    macd,
    macd_series,
    price_distance_from_sma_pct,
    rsi_series,
    rsi_wilder,
    sma,
    sma_cross_state,
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


def test_rsi_series_son_eleman_rsi_wilder_ile_esit():
    """rsi_series()'in EN SON elemanı rsi_wilder()'ın döndürdüğü tek
    değerle BİREBİR eşleşmeli -- ikisi AYNI Wilder formülünü (bkz.
    _rsi_from_averages()) paylaşıyor, tek fark serinin TAMAMININ mı yoksa
    sadece son noktanın mı döndüğü."""
    closes = [_d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(102)]

    series = rsi_series(closes, period=14)

    assert len(series) == len(closes)
    assert series[-1] == rsi_wilder(closes, period=14)
    assert abs(series[-1] - _d("56.6667")) < Decimal("0.001")


def test_rsi_series_ilk_period_eleman_none_doner():
    closes = [_d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(101), _d(100), _d(102)]

    series = rsi_series(closes, period=14)

    assert series[:14] == [None] * 14
    assert series[14] is not None


def test_rsi_series_yetersiz_veride_tamami_none_doner():
    closes = [_d(v) for v in range(100, 110)]

    series = rsi_series(closes, period=14)

    assert series == [None] * len(closes)


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


def test_macd_series_son_eleman_macd_ile_esit():
    """macd_series()'in üç serisinin de EN SON elemanı macd()'nin tek
    değerleriyle BİREBİR eşleşmeli (AYNI formül, bkz. modül üst notu)."""
    closes = [_d(v) for v in _SYNTHETIC_CLOSES]

    line_series, signal_series, hist_series = macd_series(closes, fast=12, slow=26, signal=9)
    macd_line, signal_line, histogram = macd(closes, fast=12, slow=26, signal=9)

    assert len(line_series) == len(signal_series) == len(hist_series) == len(closes)
    assert line_series[-1] == macd_line
    assert signal_series[-1] == signal_line
    assert hist_series[-1] == histogram


def test_macd_series_yetersiz_veride_tamami_none_doner():
    closes = [_d(v) for v in range(30)]

    line_series, signal_series, hist_series = macd_series(closes, 12, 26, 9)

    assert line_series == [None] * len(closes)
    assert signal_series == [None] * len(closes)
    assert hist_series == [None] * len(closes)


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


# --- ADX -- bagimsiz naif float referans implementasyonu ile capraz dogrulama ------


def _naive_adx_float_reference(bars: list[PriceBar], period: int = 14) -> float:
    """adx_wilder() ile AYNI algoritma ama TAMAMEN AYRI bir kod yolunda
    (float, rolling-sum optimizasyonu YOK) yeniden yazilmis -- MACD/Bollinger/
    ATR testlerinde kullanilan capraz dogrulama ilkesiyle AYNI (bkz. modul
    ust notu)."""
    trs, plus_dms, minus_dms = [], [], []
    for i in range(1, len(bars)):
        high, low = float(bars[i].high), float(bars[i].low)
        prev_high, prev_low, prev_close = float(bars[i - 1].high), float(bars[i - 1].low), float(bars[i - 1].close)
        up_move = high - prev_high
        down_move = prev_low - low
        plus_dms.append(up_move if (up_move > down_move and up_move > 0) else 0.0)
        minus_dms.append(down_move if (down_move > up_move and down_move > 0) else 0.0)
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))

    def dx(p, m, t):
        if t == 0:
            return None
        pdi, mdi = 100 * p / t, 100 * m / t
        s = pdi + mdi
        return 0.0 if s == 0 else 100 * abs(pdi - mdi) / s

    s_tr = sum(trs[:period]) / period
    s_plus = sum(plus_dms[:period]) / period
    s_minus = sum(minus_dms[:period]) / period
    dx_values = []
    first = dx(s_plus, s_minus, s_tr)
    if first is not None:
        dx_values.append(first)
    for i in range(period, len(trs)):
        s_tr = (s_tr * (period - 1) + trs[i]) / period
        s_plus = (s_plus * (period - 1) + plus_dms[i]) / period
        s_minus = (s_minus * (period - 1) + minus_dms[i]) / period
        d = dx(s_plus, s_minus, s_tr)
        if d is not None:
            dx_values.append(d)

    adx = sum(dx_values[:period]) / period
    for i in range(period, len(dx_values)):
        adx = (adx * (period - 1) + dx_values[i]) / period
    return adx


def test_adx_wilder_bagimsiz_float_referansiyla_esit():
    bars = _bars_from_closes(_SYNTHETIC_CLOSES)  # 40 bar, 2*period=28 gerekir

    adx = adx_wilder(bars, period=14)
    beklenen = _naive_adx_float_reference(bars, period=14)

    assert adx is not None
    assert abs(adx - _d(str(beklenen))) < Decimal("0.0001")


def test_adx_wilder_yetersiz_veride_none_doner():
    bars = _bars_from_closes(_SYNTHETIC_CLOSES[:27])  # 2*period=28 gerekir, 1 eksik
    assert adx_wilder(bars, period=14) is None


def test_adx_wilder_duz_yatay_fiyatta_dusuk_cikar():
    """Fiyat tamamen SABIT -- yon hareketi YOK, ADX dusuk (yatay piyasa
    olgusu) olmali."""
    bars = _bars_from_closes([100.0] * 40)
    adx = adx_wilder(bars, period=14)
    assert adx is not None
    assert adx < Decimal(5)


def test_adx_wilder_guclu_tek_yonlu_trendde_yuksek_cikar():
    """Fiyat HER gun DUZENLI artiyor -- guclu, kesintisiz bir trend; ADX
    yuksek (Wilder'in KENDI "guclu trend" esigi >25) cikmali."""
    bars = _bars_from_closes([100.0 + i * 2.0 for i in range(40)])
    adx = adx_wilder(bars, period=14)
    assert adx is not None
    assert adx > Decimal(25)


# --- SMA50/200 kesisim durumu (Golden/Death Cross) --------------------------------


def test_sma_cross_state_sma50_ustteyse_golden_doner():
    assert sma_cross_state([_d(110)] * 25, [_d(100)] * 25) == ("golden", False)


def test_sma_cross_state_sma50_altteyse_death_doner():
    assert sma_cross_state([_d(90)] * 25, [_d(100)] * 25) == ("death", False)


def test_sma_cross_state_yakin_zamanda_kesisim_true_doner():
    """Ilk 15 bar death (SMA50<SMA200), sonraki 10 bar golden (SMA50>SMA200)
    -- son deger golden, lookback=20 penceresi 15. bardaki (hala death)
    degere geri gittigi icin 'yakin zamanda' True olmali."""
    sma50 = [_d(90)] * 15 + [_d(110)] * 10
    sma200 = [_d(100)] * 25
    assert sma_cross_state(sma50, sma200, lookback=20) == ("golden", True)


def test_sma_cross_state_uzun_suredir_ayni_durumdaysa_yeni_degil():
    """40 bar boyunca HEP golden -- lookback=20 penceresindeki referans nokta
    da golden, dolayisiyla 'yakin zamanda' False olmali."""
    sma50 = [_d(110)] * 40
    sma200 = [_d(100)] * 40
    assert sma_cross_state(sma50, sma200, lookback=20) == ("golden", False)


def test_sma_cross_state_deger_none_ise_none_doner():
    assert sma_cross_state([None], [None]) is None
    assert sma_cross_state([_d(100)], [None]) is None


def test_sma_cross_state_sma50_sma200ye_esitse_none_doner():
    """Tam kesisim noktasindaki tek an -- ne golden ne death, belirsiz."""
    assert sma_cross_state([_d(100)], [_d(100)]) is None


def test_sma_cross_state_farkli_uzunluktaki_seriler_none_doner():
    assert sma_cross_state([_d(100)], [_d(100), _d(100)]) is None


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
    assert snapshot.adx_14 is not None
    assert snapshot.sma_cross_state in ("golden", "death")
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
    # Faz 15.1: RSI/MACD/hacim serileri de AYNI pencereyle (184 eleman) hizalı olmalı.
    assert len(snapshot.chart_rsi) == 184
    assert len(snapshot.chart_macd_line) == 184
    assert len(snapshot.chart_macd_signal) == 184
    assert len(snapshot.chart_macd_histogram) == 184
    assert len(snapshot.chart_volumes) == 184
    assert snapshot.chart_rsi[-1] == snapshot.rsi_14
    assert snapshot.chart_macd_line[-1] == snapshot.macd_line
    assert snapshot.chart_volumes[-1] == bars[-1].volume


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
    assert snapshot.adx_14 is not None  # ADX icin 2*period=28 bar yeter, 30 bar VAR
    assert snapshot.sma_200 is None
    assert snapshot.sma_cross_state is None  # sma200 None oldugu icin kesisim de belirlenemez
    assert snapshot.sma_cross_recent is False
    assert snapshot.week52_high is None
    assert snapshot.price_vs_sma200_pct is None  # sma200 None oldugu icin
