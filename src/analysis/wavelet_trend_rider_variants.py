"""Wavelet Trend Rider -- "KOTU SINYAL" ELEME ablasyonu icin AYRI, deneysel
modul (2026-08-20, kullanici canli TradingView geri bildirimi: "sinyallerin
cogu hissenin tepesinde geliyor, SL'ye gidiyor -- bunlari eleyecek bir
formul bulmamiz gerekiyor").

Neden `wavelet_trend_rider.py`nin ICINE eklenmedi (`harmonic_xabcd.py`nin
`abcd_pattern.py`ye, `momentum_confluence_variants.py`nin `momentum_
confluence.py`ye yaptigi AYNI ayrim): o modul "Pine-parity temel" rolunu
oynar -- `pine/wavelet_trend_rider_v1_indicator.pine` ile SAYISAL OZDESLIK
kaybedilmemeli. Bu modul BILEREK Pine'da HENUZ OLMAYAN ek filtreleri
(asiri-uzama, pullback-sart, ADX tavani, yesil-mum, hacim onayi) dener --
arastirma amaçli, KESIN indikatorun KENDISI DEGIL. Kazanan filtre(ler)
sectikten SONRA hem `wavelet_trend_rider.py`ye (Python/backtest) HEM
`pine/wavelet_trend_rider_v1_indicator.pine`ye (TradingView) EKLENECEK
(kullanici onayindan sonra, `momentum_confluence.py`nin hacim-ust-bandi
ablasyonundan SONRA KESIN olarak Params'a eklenmesiyle AYNI gecmis
pattern -- bkz. o modulun ust notu).

Cekirdek hesaplama mantigi (`_ema`/`_atr`/`_rsi`/`_adx`/`_causal_wavelet_
denoise`/`_daily_series_aligned`) `wavelet_trend_rider.py`den KOPYALANMISTIR
(o modulun ozel/alt-cizgili yardimcilarini disaridan import etmek katman/
kapsulleme ihlali olurdu -- `momentum_confluence_variants.py` ile AYNI
gerekce, bkz. o modulun ust notu).

Teshis hipotezleri (kaynak: `wavelet_trend_rider.py`nin Signal'ine 2026-08-20'de
eklenen `dist_from_denoised_atr`/`is_new_high_20`/`pullback_bars` alanlari):

  1. **asiri-uzama** (max_extension_atr): fiyat, temizlenmis trend cizgisinden
     COK uzaklastiginda (dist_from_denoised_atr > esik) sinyal "gec kaliyor"
     olabilir -- trend zaten olgunlasmis/tukenmek uzere.
  2. **pullback-sartsizligi** (min_pullback_bars): velocity/acceleration
     DUZ bir devam icinde pozitife donuyorsa (pullback_bars=0), bu "yeni
     baslayan" bir hareket DEGIL, zaten devam eden/olgunlasmis bir hareketin
     ic-titremesi olabilir -- gercek bir "dip sonrasi devam" ARANMALI.
  3. **yeni-tepe disi** (exclude_new_high_20): son 20 barin en yuksek kapanisi
     GUNUNDE alim, tanim geregi "tepede alim" riskini en yuksek tasir.
  4. **ADX tavani** (adx_ceiling): Wilder'in kendi gozlemi -- ADX>40-50 genelde
     bir trendin TUKENMEK UZERE oldugunu, DEVAM ETMEYECEGINI isaret eder
     (asiri "isinmis" trend, donus riski yuksek).
  5. **yesil mum onayi** (require_green_candle): sinyal barinin KENDISI
     yukselen (close>open) olmali -- ic-bar zayifligini disla.
  6. **hacim onayi** (require_volume_confirm): sinyal barinda hacim, SMA20
     hacminin USTUNDE olmali -- "taze ilgi" var mi, yoksa dusuk-hacimli bir
     surunmede mi.

`min_trades_show`/`min_trades_trustworthy` disiplini `abcd_scanner.py` ile
AYNI -- kucuk n ASLA gizlenmez, `scripts/wavelet_trend_rider_optimizasyon.py`
"orneklem kucuk" etiketiyle GOSTERIR.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.wavelet_trend_rider import Params, Signal

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")

# `wavelet_trend_rider.py`den KOPYALANDI (bkz. modul ust notu -- katman/
# kapsulleme ilkesi, `momentum_confluence_variants.py` ile AYNI gerekce).
_DB8_H: tuple[float, ...] = (
    -0.00008306863068661, 0.00047761485564963, -0.00027700227447939, -0.00344385962844181,
    0.00618442240981592, 0.00988607964835076, -0.03117510332513943, -0.01228195052284841,
    0.09103817842365775, 0.00033409704622012, -0.20082931639048901, -0.01119286766688022,
    0.41390826621119586, 0.47774307521387360, 0.22123362357612489, 0.03847781105407623,
)
_DB8_LEVELS = 4


@dataclass(frozen=True)
class VariantFlags:
    """Hangi ek filtrenin `long_ok`e DAHIL EDILDIGINI kontrol eder --
    her biri bagimsiz acilip/kapatilabilir (bkz. modul ust notu, 6 hipotez)."""

    name: str
    max_extension_atr: float | None = None
    min_pullback_bars: int | None = None
    exclude_new_high_20: bool = False
    adx_ceiling: float | None = None
    require_green_candle: bool = False
    require_volume_confirm: bool = False
    rsi_upper_override: float | None = None


def _ema(series: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(series).ewm(span=period, adjust=False).mean().to_numpy()


def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    prev_close = pd.Series(close).shift(1)
    tr = pd.concat(
        [pd.Series(high) - pd.Series(low), (pd.Series(high) - prev_close).abs(), (pd.Series(low) - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=1).mean().to_numpy()


def _rsi(close: np.ndarray, period: int) -> np.ndarray:
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return (100.0 - 100.0 / (1.0 + rs)).to_numpy()


def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    high_s, low_s, close_s = pd.Series(high), pd.Series(low), pd.Series(close)
    prev_close = close_s.shift(1)
    tr = pd.concat([high_s - low_s, (high_s - prev_close).abs(), (low_s - prev_close).abs()], axis=1).max(axis=1)
    atr_val = tr.ewm(span=period, adjust=False).mean()

    up_move = high_s.diff()
    down_move = -low_s.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=high_s.index).ewm(span=period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=high_s.index).ewm(span=period, adjust=False).mean()

    plus_di = 100.0 * plus_dm_s / (atr_val + 1e-10)
    minus_di = 100.0 * minus_dm_s / (atr_val + 1e-10)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    return dx.ewm(span=period, adjust=False).mean().to_numpy()


def _db8_atrous_smooth(series: np.ndarray, step: int) -> np.ndarray:
    n = len(series)
    out = np.zeros(n)
    valid = np.ones(n, dtype=bool)
    for k, h in enumerate(_DB8_H):
        lag = k * step
        shifted = np.full(n, np.nan)
        if lag == 0:
            shifted = series.astype(float, copy=True)
        else:
            shifted[lag:] = series[:-lag]
        out = out + h * np.nan_to_num(shifted, nan=0.0)
        valid = valid & ~np.isnan(shifted)
    return np.where(valid, out, np.nan)


def _causal_wavelet_denoise(close: np.ndarray, levels: int = _DB8_LEVELS) -> np.ndarray:
    c = close.astype(float, copy=True)
    for j in range(1, levels + 1):
        c = _db8_atrous_smooth(c, step=2 ** (j - 1))
    return c


def _daily_series_aligned(bar_times: pd.Series, daily_df: pd.DataFrame, daily_values: np.ndarray) -> np.ndarray:
    if daily_df.empty:
        return np.full(len(bar_times), np.nan)
    daily_dates = pd.to_datetime(daily_df["time"]).dt.tz_localize(None).dt.normalize().to_numpy()
    bar_dates = pd.to_datetime(bar_times).dt.tz_localize(None).dt.normalize().to_numpy()
    idx = np.searchsorted(daily_dates, bar_dates, side="left") - 1
    out = np.full(len(bar_times), np.nan)
    valid = idx >= 0
    out[valid] = daily_values[idx[valid]]
    return out


def detect_variant(df: pd.DataFrame, df_daily: pd.DataFrame, params: Params, flags: VariantFlags) -> list[Signal]:
    """`wavelet_trend_rider.detect()` ile AYNI cekirdek (EMA/ADX/RSI/ATR/
    causal-wavelet/MTF), ARTI `flags`teki ek kosullar (hepsi VARSAYILAN
    KAPALI -- `flags=VariantFlags("BASELINE")` cagrisi `detect()` ile
    BIREBIR AYNI sinyalleri uretir, bkz. tests)."""
    p = params
    n = len(df)
    warmup = min(p.ema_slow, n // 3)
    if n <= warmup:
        return []

    close = df["close"].to_numpy(dtype=float)
    open_ = df["open"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    time_col = df["time"]

    ema_fast = _ema(close, p.ema_fast)
    ema_slow = _ema(close, p.ema_slow)
    adx = _adx(high, low, close, p.adx_period)
    rsi = _rsi(close, p.rsi_period)
    atr = _atr(high, low, close, p.atr_period)

    denoised = _causal_wavelet_denoise(close)
    velocity = np.diff(denoised, prepend=np.nan)
    acceleration = np.diff(velocity, prepend=np.nan)

    roll_high_20 = pd.Series(close).rolling(20, min_periods=1).max().to_numpy()
    vol_sma_20 = pd.Series(volume).rolling(20, min_periods=1).mean().to_numpy()

    daily_ema_series = _ema(df_daily["close"].to_numpy(dtype=float), p.ema_fast) if not df_daily.empty else np.array([])
    daily_ema = _daily_series_aligned(time_col, df_daily, daily_ema_series)
    daily_close_aligned = _daily_series_aligned(time_col, df_daily, df_daily["close"].to_numpy(dtype=float))

    rsi_upper = flags.rsi_upper_override if flags.rsi_upper_override is not None else p.rsi_upper

    signals: list[Signal] = []
    for i in range(warmup, n):
        if any(
            np.isnan(v)
            for v in (ema_fast[i], ema_slow[i], adx[i], rsi[i], atr[i], velocity[i], acceleration[i], daily_ema[i], daily_close_aligned[i])
        ):
            continue
        long_ok = (
            close[i] > ema_fast[i] > ema_slow[i]
            and adx[i] > p.adx_threshold
            and velocity[i] > 0
            and acceleration[i] > 0
            and rsi[i] < rsi_upper
            and daily_close_aligned[i] > daily_ema[i]
        )
        if not long_ok:
            continue

        dist_from_denoised_atr = (close[i] - denoised[i]) / atr[i] if atr[i] > 0 else float("nan")
        if flags.max_extension_atr is not None and (np.isnan(dist_from_denoised_atr) or dist_from_denoised_atr > flags.max_extension_atr):
            continue

        pullback_bars = 0
        j = i - 1
        while j >= 0 and not np.isnan(velocity[j]) and velocity[j] <= 0:
            pullback_bars += 1
            j -= 1
        if flags.min_pullback_bars is not None and pullback_bars < flags.min_pullback_bars:
            continue

        is_new_high_20 = bool(close[i] >= roll_high_20[i])
        if flags.exclude_new_high_20 and is_new_high_20:
            continue

        if flags.adx_ceiling is not None and adx[i] > flags.adx_ceiling:
            continue

        if flags.require_green_candle and not (close[i] > open_[i]):
            continue

        if flags.require_volume_confirm and not (vol_sma_20[i] > 0 and volume[i] > vol_sma_20[i]):
            continue

        entry_ref = float(close[i])
        fill_bar = i + 1
        fill_ref = float(df["open"].iloc[fill_bar]) if fill_bar < n else float("nan")
        sl = entry_ref - atr[i] * p.sl_atr_mult
        tp1 = entry_ref + atr[i] * p.tp1_atr_mult
        tp2 = entry_ref + atr[i] * p.tp2_atr_mult

        signals.append(
            Signal(
                direction=1,
                signal_bar=i,
                signal_time=time_col.iloc[i],
                entry_ref=entry_ref,
                fill_ref=fill_ref,
                tp1=float(tp1),
                tp2=float(tp2),
                sl=float(sl),
                velocity=float(velocity[i]),
                acceleration=float(acceleration[i]),
                adx=float(adx[i]),
                dist_from_denoised_atr=float(dist_from_denoised_atr),
                is_new_high_20=is_new_high_20,
                pullback_bars=pullback_bars,
            )
        )

    return signals


# --- Arastirilacak varyantlar (2026-08-20, kullanici sorusu: "bu kotu
#     sinyalleri eleyecek bir formul bulmamiz gerekiyor") -- baseline +
#     her filtrenin TEK BASINA etkisi + birkac umut vaat eden kombinasyon. ---
#
# TUR 1 SONUCU (tam BIST, 657 sembol -- docs/spec/WAVELET_TREND_RIDER_
# OPTIMIZASYON.md): acik ara EN GUCLU tekil filtre ARTI_UZAMA_1.0 (max_
# extension_atr=1.0) -- PF 1.20->1.41 (n=5027->797, HALA buyuk/guvenilir).
# Pullback sarti (1/2/3 bar) BEKLENENIN AKSINE HICBIR IYILESME saglamadi
# (PF 1.16, BASELINE'dan bile hafif kotu) -- "gercek bir dip sonrasi devam"
# hipotezi tam BIST olceginde YANLISLANDI, VARIANTS'ta REFERANS icin
# tutuluyor (sessizce silinmedi). TUR 2: UZAMA_1.0'in daha da SIKI
# esiklerle (0.5/0.75) ve en iyi 2. sirali filtrelerle (yesil mum, ADX
# tavani, hacim) KOMBINE edilince daha da iyilesip iyilesmedigini test eder.
VARIANTS: dict[str, VariantFlags] = {
    "BASELINE": VariantFlags(name="BASELINE"),
    "ARTI_UZAMA_0.5": VariantFlags(name="ARTI_UZAMA_0.5", max_extension_atr=0.5),
    "ARTI_UZAMA_0.75": VariantFlags(name="ARTI_UZAMA_0.75", max_extension_atr=0.75),
    "ARTI_UZAMA_1.0": VariantFlags(name="ARTI_UZAMA_1.0", max_extension_atr=1.0),
    "ARTI_UZAMA_1.5": VariantFlags(name="ARTI_UZAMA_1.5", max_extension_atr=1.5),
    "ARTI_UZAMA_2.0": VariantFlags(name="ARTI_UZAMA_2.0", max_extension_atr=2.0),
    "ARTI_PULLBACK_1": VariantFlags(name="ARTI_PULLBACK_1", min_pullback_bars=1),
    "ARTI_PULLBACK_2": VariantFlags(name="ARTI_PULLBACK_2", min_pullback_bars=2),
    "ARTI_PULLBACK_3": VariantFlags(name="ARTI_PULLBACK_3", min_pullback_bars=3),
    "ARTI_YENI_TEPE_DISI": VariantFlags(name="ARTI_YENI_TEPE_DISI", exclude_new_high_20=True),
    "ARTI_ADX_TAVAN_40": VariantFlags(name="ARTI_ADX_TAVAN_40", adx_ceiling=40.0),
    "ARTI_ADX_TAVAN_50": VariantFlags(name="ARTI_ADX_TAVAN_50", adx_ceiling=50.0),
    "ARTI_YESIL_MUM": VariantFlags(name="ARTI_YESIL_MUM", require_green_candle=True),
    "ARTI_HACIM_ONAY": VariantFlags(name="ARTI_HACIM_ONAY", require_volume_confirm=True),
    "ARTI_RSI_60": VariantFlags(name="ARTI_RSI_60", rsi_upper_override=60.0),
    "ARTI_RSI_55": VariantFlags(name="ARTI_RSI_55", rsi_upper_override=55.0),
    # --- TUR 2 kombinasyonlari -- UZAMA_1.0 (en iyi tekil) + 2. sirali adaylar ---
    "KOMBO_UZAMA1.0_YESILMUM": VariantFlags(name="KOMBO_UZAMA1.0_YESILMUM", max_extension_atr=1.0, require_green_candle=True),
    "KOMBO_UZAMA1.0_ADX40": VariantFlags(name="KOMBO_UZAMA1.0_ADX40", max_extension_atr=1.0, adx_ceiling=40.0),
    "KOMBO_UZAMA1.0_HACIM": VariantFlags(name="KOMBO_UZAMA1.0_HACIM", max_extension_atr=1.0, require_volume_confirm=True),
    "KOMBO_UZAMA0.75_YESILMUM": VariantFlags(name="KOMBO_UZAMA0.75_YESILMUM", max_extension_atr=0.75, require_green_candle=True),
    "KOMBO_UZAMA1.0_YESILMUM_ADX40": VariantFlags(
        name="KOMBO_UZAMA1.0_YESILMUM_ADX40", max_extension_atr=1.0, require_green_candle=True, adx_ceiling=40.0,
    ),
    # --- TUR 1'den kalan (referans/karsilastirma icin) ---
    "KOMBO_UZAMA1.5_PULLBACK1": VariantFlags(name="KOMBO_UZAMA1.5_PULLBACK1", max_extension_atr=1.5, min_pullback_bars=1),
    "KOMBO_UZAMA1.5_TEPEDISI": VariantFlags(name="KOMBO_UZAMA1.5_TEPEDISI", max_extension_atr=1.5, exclude_new_high_20=True),
    "KOMBO_PULLBACK1_ADX40": VariantFlags(name="KOMBO_PULLBACK1_ADX40", min_pullback_bars=1, adx_ceiling=40.0),
    "KOMBO_TUMU_GEVSEK": VariantFlags(
        name="KOMBO_TUMU_GEVSEK", max_extension_atr=2.0, min_pullback_bars=1, adx_ceiling=50.0,
    ),
    "KOMBO_TUMU_SIKI": VariantFlags(
        name="KOMBO_TUMU_SIKI", max_extension_atr=1.0, min_pullback_bars=2, exclude_new_high_20=True, adx_ceiling=40.0,
    ),
}

# TUR 2 KAZANANI (2026-08-20, tam BIST, n=403): PF 1.20 (BASELINE) -> 1.61,
# Win Rate %44.9 -> %52.1. `pine/wavelet_trend_rider_v1_indicator.pine`
# (V2) VARSAYILAN olarak AYNI formulu uygular -- Python/Pine parite icin
# BURADA da isimlendirilmis, ileride Telegram/canli kullanim icin "resmi"
# onerilen varyant BUDUR (kullanici onayladiginda).
RECOMMENDED = VariantFlags(
    name="RECOMMENDED", max_extension_atr=1.0, require_green_candle=True, adx_ceiling=40.0,
)
