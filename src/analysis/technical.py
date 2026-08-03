"""Teknik gostergeler -- SAF MATEMATIK, I/O YOK (Faz 15 - Teknik Analiz).

Bu modul HICBIR ag istegi atmaz, src.fetchers.* / src.db.* HICBIR modulu
import ETMEZ (01_MIMARI.md katman kurali -- calculator.py/scorer.py ile
AYNI ilke). Girdi olarak zaten cekilmis, artan tarihe sirali `PriceBar`
listesi alir (src/fetchers/price_history.py::OhlcvBar'dan cagiran taraf
tarafindan donusturulur -- bu modul o donusumu YAPMAZ, sadece TUKETIR).

BAGLAYICI KISITLAR (YENI_FAZ_PROMPTLARI.md Faz 15 gorev talimati):
  K1. Bu modul bir "SKOR" URETMEZ -- src/analysis/scorer.py'nin temel analiz
      skoruyla KARISTIRILMAYACAK ayri bir kavramdir.
  K2. "Al/Sat/Tut" sinyali URETMEZ -- sadece hesaplanmis OLGU (sayisal
      deger) doner, yorumu okuyucuya/karta birakir.
  K3. Butun formuller standart ve tartismasizdir; her fonksiyonun
      docstring'inde formul + kaynak (yazar/kitap) yazilidir.
  K4. Yeterli veri yoksa (yeni halka arz, yeterli gecmis yok) None doner --
      ASLA tahmin/uydurma yapilmaz. Bir gostergenin eksik olmasi digerlerini
      ETKILEMEZ (her fonksiyon kendi veri yeterliligini BAGIMSIZ kontrol eder).

Tum parasal/sayisal hesaplar Decimal ile yapilir (Degismez Kural 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

_TRADING_DAYS_PER_YEAR = 252
_CHART_LOOKBACK_DAYS = 183  # ~6 ay -- kart fiyat grafiginin gosterdigi pencere


@dataclass(frozen=True)
class PriceBar:
    """Tek bir gunluk mum. `technical.py` SADECE high/low/close/volume
    kullanir -- hicbir gosterge acilis fiyatina ihtiyac DUYMAZ (bkz.
    src/fetchers/price_history.py modul notu, BIST kaynaginda acilis YOK)."""

    trade_date: date
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class TechnicalSnapshot:
    """Bir hissenin GUNCEL teknik gorunumu -- tum alanlar OLGU, hicbiri
    yorum/sinyal degildir (K2). Herhangi bir alan, o gosterge icin yeterli
    veri yoksa None'dir (K4); kartin geri kalani yine de uretilir."""

    as_of_date: date
    price: Decimal
    sma_20: Decimal | None
    sma_50: Decimal | None
    sma_200: Decimal | None
    ema_12: Decimal | None
    ema_26: Decimal | None
    rsi_14: Decimal | None
    macd_line: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    bb_upper: Decimal | None
    bb_middle: Decimal | None
    bb_lower: Decimal | None
    atr_14: Decimal | None
    adx_14: Decimal | None
    sma_cross_state: str | None  # "golden" | "death" | None (bkz. sma_cross_state())
    sma_cross_recent: bool
    week52_high: Decimal | None
    week52_low: Decimal | None
    week52_position_pct: Decimal | None
    avg_volume_20: Decimal | None
    last_volume: Decimal
    volume_ratio_pct: Decimal | None
    price_vs_sma200_pct: Decimal | None
    # Kart grafigi icin son ~6 aylik (artan tarihe sirali) seriler --
    # chart_sma50/200'un elemanlari o gundeki SMA yeterli veri BULAMADIYSA None olabilir.
    chart_dates: tuple[date, ...]
    chart_closes: tuple[Decimal, ...]
    chart_sma50: tuple[Decimal | None, ...]
    chart_sma200: tuple[Decimal | None, ...]


# --- Hareketli ortalamalar ----------------------------------------------------


def sma_series(values: list[Decimal], period: int) -> list[Decimal | None]:
    """Basit Hareketli Ortalama (Simple Moving Average) -- TUM seri.

    Formul: SMA[i] = ortalama(values[i-period+1 .. i])
    Kaynak: standart teknik analiz tanimi (orn. John J. Murphy,
    "Technical Analysis of the Financial Markets", 1999, Bolum 9).

    Doner: values ile AYNI uzunlukta liste; ilk (period-1) eleman ve
    len(values) < period ise TUMU None (yeterli veri yok -- uydurma YAPILMAZ).
    """
    n = len(values)
    result: list[Decimal | None] = [None] * n
    if period <= 0 or n < period:
        return result

    window_sum = sum(values[:period])
    result[period - 1] = window_sum / period
    for i in range(period, n):
        window_sum += values[i] - values[i - period]
        result[i] = window_sum / period
    return result


def sma(values: list[Decimal], period: int) -> Decimal | None:
    """sma_series()'in EN GUNCEL degeri -- gosterge tablosu icin kisayol."""
    series = sma_series(values, period)
    return series[-1] if series else None


def ema_series(values: list[Decimal], period: int) -> list[Decimal | None]:
    """Ustel Hareketli Ortalama (Exponential Moving Average) -- TUM seri.

    Formul: k = 2 / (period + 1)
            EMA[period-1] = SMA(values[0..period-1])   (ilk deger SMA ile "seed" edilir)
            EMA[i] = (values[i] - EMA[i-1]) * k + EMA[i-1]   (i > period-1)
    Kaynak: standart teknik analiz tanimi (orn. Murphy 1999, Bolum 9).
    Ilk deger icin SMA kullanma yontemi en yaygin/standart baslatma
    seklidir (bazi kaynaklar ilk `values[0]`'i kullanir; SMA-seed daha
    kararlidir ve TradingView dahil cogu platformun varsayilanidir).

    Doner: values ile AYNI uzunlukta liste; ilk (period-1) eleman ve
    len(values) < period ise TUMU None.
    """
    n = len(values)
    result: list[Decimal | None] = [None] * n
    if period <= 0 or n < period:
        return result

    k = Decimal(2) / Decimal(period + 1)
    seed = sum(values[:period]) / period
    result[period - 1] = seed
    prev = seed
    for i in range(period, n):
        prev = (values[i] - prev) * k + prev
        result[i] = prev
    return result


def ema(values: list[Decimal], period: int) -> Decimal | None:
    """ema_series()'in EN GUNCEL degeri -- gosterge tablosu icin kisayol."""
    series = ema_series(values, period)
    return series[-1] if series else None


# --- RSI -----------------------------------------------------------------------


def rsi_wilder(closes: list[Decimal], period: int = 14) -> Decimal | None:
    """Wilder'in Gorece Guc Endeksi (Relative Strength Index).

    Formul (J. Welles Wilder Jr., "New Concepts in Technical Trading
    Systems", 1978, Bolum 6):
        delta[i]  = close[i] - close[i-1]
        gain[i]   = max(delta[i], 0) ; loss[i] = max(-delta[i], 0)
        ilk_ort_kazanc = ortalama(gain[1..period]) ; ilk_ort_kayip = ortalama(loss[1..period])
        sonraki_ort_kazanc = (onceki_ort_kazanc * (period-1) + gain[i]) / period
        sonraki_ort_kayip  = (onceki_ort_kayip  * (period-1) + loss[i]) / period
        RS  = ort_kazanc / ort_kayip
        RSI = 100 - 100 / (1 + RS)

    ⚠️ Bu BASIT (aritmetik) ortalama DEGILDIR -- "Wilder yumusatmasi"
    (alpha = 1/period ile ustel yumusatmanin bir varyanti) kullanilir.
    Bu, RSI'in TARTISMASIZ standart tanimidir (TradingView, Fintables gibi
    tum platformlar bunu kullanir); basit ortalamayla hesaplanan bir RSI
    farkli (ve yanlis) sonuc verir -- gorev talimatinda ozellikle
    vurgulanan fark budur.

    En az `period + 1` kapanis fiyati GEREKIR (ilk `period` degisimi
    hesaplamak icin). Azsa None doner.

    Kenar durumlar:
      - ort_kayip == 0 ve ort_kazanc > 0  -> RSI = 100 (RS -> sonsuz limiti)
      - ort_kazanc == ort_kayip == 0 (fiyat TAMAMEN sabit) -> RS tanimsiz
        (0/0); kural geregi notr RSI = 50 doner.
    """
    n = len(closes)
    if n < period + 1:
        return None

    deltas = [closes[i] - closes[i - 1] for i in range(1, n)]
    gains = [max(d, Decimal(0)) for d in deltas]
    losses = [max(-d, Decimal(0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_gain == 0 and avg_loss == 0:
        return Decimal(50)
    if avg_loss == 0:
        return Decimal(100)

    rs = avg_gain / avg_loss
    return Decimal(100) - (Decimal(100) / (Decimal(1) + rs))


# --- MACD ------------------------------------------------------------------


def macd(
    closes: list[Decimal], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[Decimal, Decimal, Decimal] | None:
    """MACD (Moving Average Convergence Divergence).

    Formul (Gerald Appel, 1970'ler -- bkz. Murphy 1999, Bolum 12):
        MACD_cizgisi   = EMA(closes, fast) - EMA(closes, slow)
        Sinyal_cizgisi = EMA(MACD_cizgisi serisi, signal)
        Histogram      = MACD_cizgisi - Sinyal_cizgisi

    Standart parametreler (12, 26, 9) gunluk grafikler icin Appel'in
    orijinal onerisidir.

    En az `slow + signal` kapanis GEREKIR (MACD serisinin sinyal EMA'sini
    hesaplamak icin yeterli MACD noktasi olmali). Azsa None doner.

    Doner: (macd_cizgisi, sinyal_cizgisi, histogram) -- EN GUNCEL deger.
    """
    n = len(closes)
    if n < slow + signal:
        return None

    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)

    start_idx = slow - 1  # ema_slow ilk defa bu indexte dolar (fast daha erken doldugu icin guvenli)
    macd_line_series = [ema_fast[i] - ema_slow[i] for i in range(start_idx, n)]

    signal_series = ema_series(macd_line_series, signal)
    if signal_series[-1] is None:
        return None

    macd_last = macd_line_series[-1]
    signal_last = signal_series[-1]
    return macd_last, signal_last, macd_last - signal_last


# --- Bollinger Bantlari --------------------------------------------------------


def bollinger_bands(
    closes: list[Decimal], period: int = 20, num_std: Decimal = Decimal("2")
) -> tuple[Decimal, Decimal, Decimal] | None:
    """Bollinger Bantlari.

    Formul (John Bollinger, "Bollinger on Bollinger Bands", 2001):
        Orta_bant = SMA(closes, period)
        std       = POPULASYON standart sapmasi (N'e bolme, N-1 DEGIL --
                    Bollinger'in orijinal tanimi budur)
        Ust_bant  = Orta_bant + num_std * std
        Alt_bant  = Orta_bant - num_std * std

    Standart parametreler: period=20, num_std=2 (Bollinger'in kendi onerisi).

    En az `period` kapanis GEREKIR. Azsa None doner.

    Doner: (ust_bant, orta_bant, alt_bant) -- EN GUNCEL pencere icin.
    """
    n = len(closes)
    if n < period:
        return None

    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((c - middle) ** 2 for c in window) / period
    std = variance.sqrt()

    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


# --- ATR -----------------------------------------------------------------------


def atr_wilder(bars: list[PriceBar], period: int = 14) -> Decimal | None:
    """Wilder'in Ortalama Gercek Aralik (Average True Range) gostergesi.

    Formul (J. Welles Wilder Jr., "New Concepts in Technical Trading
    Systems", 1978, Bolum 4):
        Gercek_Aralik[i] = max(
            high[i] - low[i],
            |high[i] - close[i-1]|,
            |low[i]  - close[i-1]|,
        )
        ilk_ATR   = ortalama(Gercek_Aralik[1..period])
        sonraki_ATR = (onceki_ATR * (period-1) + Gercek_Aralik[i]) / period   (Wilder yumusatmasi -- rsi_wilder() ile AYNI ilke)

    En az `period + 1` bar GEREKIR (ilk barin bir onceki kapanisi olmali).
    Azsa None doner.
    """
    n = len(bars)
    if n < period + 1:
        return None

    true_ranges: list[Decimal] = []
    for i in range(1, n):
        high, low = bars[i].high, bars[i].low
        prev_close = bars[i - 1].close
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))

    atr = sum(true_ranges[:period]) / period
    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
    return atr


# --- ADX (Trend Gucu) -----------------------------------------------------------


def adx_wilder(bars: list[PriceBar], period: int = 14) -> Decimal | None:
    """Wilder'in Ortalama Yon Endeksi (Average Directional Index) -- bir
    trendin YONUNU degil GUCUNU olcer (arastirma bulgusu: SMA50/200 kesisimi
    gibi trend sinyallerini "yatay piyasada gurultu" olabilecek durumlardan
    ayirt etmek icin standart bir filtredir).

    Formul (J. Welles Wilder Jr., "New Concepts in Technical Trading
    Systems", 1978, Bolum 4 -- atr_wilder() ile AYNI kaynak/bolum):
        yukselis[i]  = high[i] - high[i-1] ; dusus[i] = low[i-1] - low[i]
        +DM[i] = yukselis[i]  eger (yukselis[i] > dusus[i] ve yukselis[i] > 0) degilse 0
        -DM[i] = dusus[i]     eger (dusus[i] > yukselis[i] ve dusus[i] > 0) degilse 0
        GA[i]  = Gercek Aralik (atr_wilder() ile AYNI tanim)
        +DM/-DM/GA, Wilder yumusatmasiyla (rsi_wilder/atr_wilder ile AYNI
          yontem) yumusatilir -> smoothed(+DM), smoothed(-DM), smoothed(GA)
        +DI = 100 * smoothed(+DM) / smoothed(GA)
        -DI = 100 * smoothed(-DM) / smoothed(GA)
        DX  = 100 * |+DI - -DI| / (+DI + -DI)
        ADX = DX serisinin Wilder yumusatmasiyla ortalamasi (ilk deger ilk
              `period` DX'in BASIT ortalamasi, sonrasi Wilder yumusamasi)

    Klasik yorum esikleri (Wilder'in KENDI onerisi, RSI'in 70/30'u gibi
    tartismasiz standart): ADX < 20 zayif/yatay piyasa, 20-25 trend
    olusuyor, ADX > 25 guclu trend. Yorum karta/render katmanina birakilir
    (K2), burada SADECE sayisal deger uretilir.

    En az 2*period bar GEREKIR (ilk period: +DM/-DM/GA'nin ilk smoothed
    degeri icin; ikinci period: ilk ADX'i olusturacak DX serisi icin). Azsa
    None doner.
    """
    n = len(bars)
    if n < 2 * period:
        return None

    trs: list[Decimal] = []
    plus_dms: list[Decimal] = []
    minus_dms: list[Decimal] = []
    for i in range(1, n):
        high, low = bars[i].high, bars[i].low
        prev_high, prev_low, prev_close = bars[i - 1].high, bars[i - 1].low, bars[i - 1].close
        up_move = high - prev_high
        down_move = prev_low - low
        plus_dms.append(up_move if (up_move > down_move and up_move > 0) else Decimal(0))
        minus_dms.append(down_move if (down_move > up_move and down_move > 0) else Decimal(0))
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))

    def _dx(smoothed_plus: Decimal, smoothed_minus: Decimal, smoothed_tr: Decimal) -> Decimal | None:
        if smoothed_tr == 0:
            return None
        plus_di = Decimal(100) * smoothed_plus / smoothed_tr
        minus_di = Decimal(100) * smoothed_minus / smoothed_tr
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return Decimal(0)
        return Decimal(100) * abs(plus_di - minus_di) / di_sum

    smoothed_tr = sum(trs[:period]) / period
    smoothed_plus_dm = sum(plus_dms[:period]) / period
    smoothed_minus_dm = sum(minus_dms[:period]) / period

    dx_values: list[Decimal] = []
    first_dx = _dx(smoothed_plus_dm, smoothed_minus_dm, smoothed_tr)
    if first_dx is not None:
        dx_values.append(first_dx)

    for i in range(period, len(trs)):
        smoothed_tr = (smoothed_tr * (period - 1) + trs[i]) / period
        smoothed_plus_dm = (smoothed_plus_dm * (period - 1) + plus_dms[i]) / period
        smoothed_minus_dm = (smoothed_minus_dm * (period - 1) + minus_dms[i]) / period
        dx = _dx(smoothed_plus_dm, smoothed_minus_dm, smoothed_tr)
        if dx is not None:
            dx_values.append(dx)

    if len(dx_values) < period:
        return None

    adx = sum(dx_values[:period]) / period
    for i in range(period, len(dx_values)):
        adx = (adx * (period - 1) + dx_values[i]) / period
    return adx


# --- SMA50/200 kesisim durumu (Golden/Death Cross) --------------------------------


def sma_cross_state(
    sma_50_series: list[Decimal | None], sma_200_series: list[Decimal | None], lookback: int = 20
) -> tuple[str, bool] | None:
    """SMA50'nin SMA200'e GORE guncel konumu + bu konumun YAKIN zamanda
    (son `lookback` bar icinde) olusup olusmadigi -- "Altin Kesisim"/"Olum
    Kesisimi" olarak bilinen, uzun vadeli trend donusu icin YAYGIN kullanilan
    klasik bir OLGUDUR (Murphy 1999, Bolum 9 -- hareketli ortalama
    kesisimleri). K2 geregi bir "AL/SAT" sinyali DEGIL, sadece iki hareketli
    ortalamanin birbirine gore KONUMU + bu konumun "tazeligi".

    Doner: (durum, yakin_zamanda_mi) -- durum "golden" (SMA50 > SMA200) veya
    "death" (SMA50 < SMA200). Guncel deger(ler) None/esitse (yeterli veri
    yok ya da tam kesisim noktasindaysa) None doner. `yakin_zamanda_mi`:
    `lookback` bar ONCESINDEKI durum FARKLIYSA True -- referans nokta(lar)
    eksikse (None) MUHAFAZAKAR sekilde False kalir (K4: uydurma yapilmaz).
    """
    n = len(sma_50_series)
    if n == 0 or len(sma_200_series) != n:
        return None

    last_50, last_200 = sma_50_series[-1], sma_200_series[-1]
    if last_50 is None or last_200 is None or last_50 == last_200:
        return None
    current_state = "golden" if last_50 > last_200 else "death"

    reference_idx = max(0, n - 1 - lookback)
    ref_50, ref_200 = sma_50_series[reference_idx], sma_200_series[reference_idx]
    is_recent = False
    if ref_50 is not None and ref_200 is not None and ref_50 != ref_200:
        reference_state = "golden" if ref_50 > ref_200 else "death"
        is_recent = reference_state != current_state

    return current_state, is_recent


# --- 52 hafta araligi ----------------------------------------------------------


def week_52_range(bars: list[PriceBar]) -> tuple[Decimal, Decimal, Decimal] | None:
    """Son 52 haftalik (yaklasik 252 islem gunu) fiyat araligi + fiyatin bu
    aralik icindeki GORECELI konumu.

    Formul: standart "52-hafta yuksek/dusuk" tanimi (borsa/finans terminali
    ortak kullanimi -- orn. Yahoo Finance/Bloomberg):
        yuksek = max(high[-252:]) ; dusuk = min(low[-252:])
        konum_yuzdesi = (son_kapanis - dusuk) / (yuksek - dusuk) * 100

    ⚠️ 252 GUN yaklastirmasidir (bir yilda ortalama ~252 islem gunu vardir),
    takvim haftasi DEGIL. TAM 52 hafta iddia edilemeyecek kadar az veri
    (252 barin altinda -- orn. yeni halka arz) varsa None doner; kismi bir
    pencereyi "52 hafta" diye SUNMAK Kural 3'e aykiri bir uydurma olurdu.

    yuksek == dusuk (fiyat TAMAMEN sabit) ise konum_yuzdesi = 50 (tanimsiz
    orta nokta, 0/0 kacinmasi icin).

    Doner: (yuksek, dusuk, konum_yuzdesi)
    """
    n = len(bars)
    if n < _TRADING_DAYS_PER_YEAR:
        return None

    window = bars[-_TRADING_DAYS_PER_YEAR:]
    high = max(b.high for b in window)
    low = min(b.low for b in window)
    last_close = bars[-1].close

    if high == low:
        return high, low, Decimal(50)

    position_pct = (last_close - low) / (high - low) * Decimal(100)
    return high, low, position_pct


# --- Hacim ---------------------------------------------------------------------


def average_volume(volumes: list[Decimal], period: int = 20) -> Decimal | None:
    """Son `period` gunun ortalama islem hacmi (aritmetik ortalama).

    Kaynak: standart "average volume" tanimi (ortak borsa terminali kullanimi).
    len(volumes) < period ise None doner.
    """
    n = len(volumes)
    if n < period:
        return None
    return sum(volumes[-period:]) / period


def volume_ratio_pct(volumes: list[Decimal], period: int = 20) -> Decimal | None:
    """Son gunun hacminin, son `period` gunun ortalama hacmine oranini
    yuzde olarak doner (orn. 150 -> son hacim ortalamanin %50 UZERINDE).

    Formul: (son_hacim / ortalama_hacim) * 100
    Ortalama hesaplanamiyorsa (yeterli veri yok) veya 0 ise None doner.
    """
    avg = average_volume(volumes, period)
    if not avg:
        return None
    return (volumes[-1] / avg) * Decimal(100)


# --- Fiyat / SMA mesafesi -------------------------------------------------------


def price_distance_from_sma_pct(price: Decimal, sma_value: Decimal | None) -> Decimal | None:
    """Fiyatin bir hareketli ortalamaya (orn. SMA200) GORECELI yuzde uzakligi.

    Formul: (fiyat - sma) / sma * 100
    `sma_value` None veya 0 ise None doner (SMA'nin kendisi yetersiz veri
    yuzunden hesaplanamadiysa mesafe de hesaplanamaz).
    """
    if not sma_value:
        return None
    return (price - sma_value) / sma_value * Decimal(100)


# --- Orkestrasyon --------------------------------------------------------------


def compute_snapshot(bars: list[PriceBar]) -> TechnicalSnapshot | None:
    """Artan tarihe sirali bar listesinden TUM gostergeleri TEK seferde
    hesaplar. `bars` bos ise None doner.

    Her gosterge KENDI ICINDE yeterli veri kontrolu yapar -- bir gostergenin
    eksik olmasi (orn. SMA200 icin 200 barin altinda veri) digerlerini
    ETKILEMEZ; snapshot yine de doner, sadece o alan None kalir (K4).
    """
    if not bars:
        return None

    closes = [b.close for b in bars]
    volumes = [b.volume for b in bars]
    price = closes[-1]

    macd_result = macd(closes)
    bb_result = bollinger_bands(closes)
    week52 = week_52_range(bars)
    sma_200_value = sma(closes, 200)

    sma_50_series = sma_series(closes, 50)
    sma_200_series = sma_series(closes, 200)
    cross = sma_cross_state(sma_50_series, sma_200_series)
    cutoff = bars[-1].trade_date - timedelta(days=_CHART_LOOKBACK_DAYS)
    chart_indices = [i for i, bar in enumerate(bars) if bar.trade_date >= cutoff]

    return TechnicalSnapshot(
        as_of_date=bars[-1].trade_date,
        price=price,
        sma_20=sma(closes, 20),
        sma_50=sma(closes, 50),
        sma_200=sma_200_value,
        ema_12=ema(closes, 12),
        ema_26=ema(closes, 26),
        rsi_14=rsi_wilder(closes, 14),
        macd_line=macd_result[0] if macd_result else None,
        macd_signal=macd_result[1] if macd_result else None,
        macd_histogram=macd_result[2] if macd_result else None,
        bb_upper=bb_result[0] if bb_result else None,
        bb_middle=bb_result[1] if bb_result else None,
        bb_lower=bb_result[2] if bb_result else None,
        atr_14=atr_wilder(bars, 14),
        adx_14=adx_wilder(bars, 14),
        sma_cross_state=cross[0] if cross else None,
        sma_cross_recent=cross[1] if cross else False,
        week52_high=week52[0] if week52 else None,
        week52_low=week52[1] if week52 else None,
        week52_position_pct=week52[2] if week52 else None,
        avg_volume_20=average_volume(volumes, 20),
        last_volume=volumes[-1],
        volume_ratio_pct=volume_ratio_pct(volumes, 20),
        price_vs_sma200_pct=price_distance_from_sma_pct(price, sma_200_value),
        chart_dates=tuple(bars[i].trade_date for i in chart_indices),
        chart_closes=tuple(closes[i] for i in chart_indices),
        chart_sma50=tuple(sma_50_series[i] for i in chart_indices),
        chart_sma200=tuple(sma_200_series[i] for i in chart_indices),
    )
