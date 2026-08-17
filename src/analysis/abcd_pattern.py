"""AB=CD harmonik formasyon tespiti -- Pine parity, SAF MANTIK, I/O YOK.

Bu modul `pine/abcd_v2_5_indicator.pine` (TradingView Pine v6, abcd-project
deposu) dosyasinin birebir Python portudur -- kaynak `abcd-project/abcd/
detector.py`'den bu projeye adapte edilmistir. Pine dosyasi TEK dogruluk
kaynagidir: pivotlar (`ta.pivothigh`/`ta.pivotlow(L, L)`), KESIN pivot tipi
alternansi (ayni tip pivot gelirse eskisi DEGISTIRILMEZ, sessizce yoksayilir),
rolling A->B->C->D skaler state (dizi degil), `isValidABCD` oran kontrolleri
(BC retracement, CD extension, yapisal strict inequality), TP1 = D +/-
0.382*|A-D|, TP2 = C, SL = D +/- ATR14(confirmation bar)*atr_mult. Pine
mantigindan Python tarafinda BAGIMSIZ "iyilestirme" YAPILMAZ -- iki dosya
lockstep kalmak ZORUNDADIR; bir davranis degisikligi gerekiyorsa once Pine
dosyasi guncellenir, sonra bu modul, ikisi ayri commit'lerde asla birakilmaz.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`.

  Karar 1 -- Modul izolasyonu: Bu modul `src/analysis/`in genel felsefesinden
  (skorsuz/sinyalsiz, bkz. technical.py K2) BILINCLI bir sapmadir -- yonlu
  BUY/SELL sinyali + TP/SL uretir. Bu bir istisnadir, bir emsal DEGILDIR.
  Kullaniciya gosterilen her yerde (kart, mesaj) "bu deneysel bir sinyal
  ureticidir, temel/teknik-olgu skorlarindan bagimsizdir" ayrimi net yapilir.

  Karar 2 -- Decimal istisnasi: Proje geneli Decimal-only olsa da (Degismez
  Kural 2/3), bu modul TAMAMEN float + numpy/pandas kullanir -- Pine'in
  float64 aritmetigiyle bar-bar eslesme (RMA/ATR seed, strict pivot
  karsilastirmasi) zorunlulugu nedeniyle. Bu, quaxis-mimari Kural 3'e
  kapsami sinirli, gerekceli bir istisnadir. Float deger BURADAN hicbir
  zaman Decimal tipli dataclass'lara, scorer.py'ye veya calculator.py'ye
  SIZMAZ -- Decimal'e/string'e donusum SADECE render sinirinda
  (src/render/abcd_card.py context builder, henuz yazilmadi) yapilir.

Katman disiplini: bu modul `src.fetchers.*` / `src.db.*` HICBIR modulu
import ETMEZ (calculator.py/scorer.py/technical.py ile AYNI ilke). Girdi
olarak zaten cekilmis bir `pd.DataFrame` alir (kolonlar: time, open, high,
low, close, volume, artan zamana sirali), hicbir ag/dosya I/O yapmaz.

Tarihsel/backtest verisi tamamen onaylanmis (confirmed) barlardan olustugu
varsayilir, bu yuzden Pine'in `barstate.isconfirmed` bayragi burada ayrica
modellenmez -- Pine'da o bayrak her tarihsel bar icin true'dur, bu detector
sadece o durumda calisir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    """Pine dosyasindaki her `input.*` ile birebir ayni isim, ayni varsayilan."""

    pivot_lookback: int = 5
    fib_tolerance: float = 0.05
    min_bc_retrace: float = 0.382
    max_bc_retrace: float = 0.886
    use_exact_cd: bool = True
    cd_min_ext: float = 0.886
    cd_max_ext: float = 1.272
    atr_mult: float = 1.0
    enable_long: bool = True
    enable_short: bool = True


@dataclass(frozen=True)
class Signal:
    """Onaylanmis (confirmed) tek bir AB=CD formasyonu.

    `entry_ref`, D barinin close'udur (Pine grafiginin cizdigi deger,
    `close[pivot_lookback]` uzerinden) -- sinyal bilindiginde zaten
    gecmiste kalmis bir degerdir. `fill_ref`, look-ahead'siz gercekci
    giris fiyatidir: onay barindan hemen SONRAKI barin acilisi. O bar
    henuz mevcut degilse (sinyal, elde bulunan en son barda ise) NaN
    doner -- asla uydurulmaz.
    """

    direction: int  # +1 = bullish/BUY, -1 = bearish/SELL
    a_bar: int
    b_bar: int
    c_bar: int
    d_bar: int
    a_price: float
    b_price: float
    c_price: float
    d_price: float
    signal_bar: int  # = d_bar + pivot_lookback, onay (confirmation) bari
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    bc_ratio: float
    cd_ratio: float


def pivot_high(high: np.ndarray, L: int) -> np.ndarray:
    """Pine'in `ta.pivothigh(high, L, L)` portu.

    Pine bir pivot high'i, gerceklestikten `L` bar SONRA onaylar. Bar `i`de
    (0 indeksli, `bar_index`), aday bar `p = i - L`nin `high[p]` degeri,
    `2*L + 1` barlik `[p - L, p + L]` penceresindeki (esdeger olarak
    `[i - 2L, i]`) her digger high'tan KESIN olarak buyukse (soldaki `L` bar
    VE sagdaki `L` bar) fonksiyon o degeri doner. Karsilastirma strict'tir
    (`>`, `>=` degil) -- pencerede herhangi bir esitlik adayi diskalifiye
    eder, asla pivot olmaz (Pine'in yerlesik fonksiyonu ayni davranir; duz
    bir tepe hic pivot uretmez).

    `high` ile ayni uzunlukta bir dizi doner, ONAY barina hizalanmistir:
    `result[i]`, bar `i - L`deki pivot fiyatidir, veya bar `i - L` (henuz ya
    da hicbir zaman) onayli bir pivot degilse NaN. `high` icinde NaN
    OLMADIGI varsayilir.
    """
    n = len(high)
    out = np.full(n, np.nan)
    for p in range(L, n - L):
        center = high[p]
        left = high[p - L:p]
        right = high[p + 1:p + L + 1]
        if center > left.max() and center > right.max():
            out[p + L] = center
    return out


def pivot_low(low: np.ndarray, L: int) -> np.ndarray:
    """Pine'in `ta.pivotlow(low, L, L)` portu. `pivot_high`in strict `<`
    ile aynasi -- strict karsilastirma / onay-bari kurali icin onun
    docstring'ine bakiniz."""
    n = len(low)
    out = np.full(n, np.nan)
    for p in range(L, n - L):
        center = low[p]
        left = low[p - L:p]
        right = low[p + 1:p + L + 1]
        if center < left.min() and center < right.min():
            out[p + L] = center
    return out


def atr_wilder(df: pd.DataFrame, length: int = 14) -> np.ndarray:
    """Pine'in `ta.atr(length)` == `ta.rma(ta.tr(true), length)` portu.

    Bar 0'da onceki close olmadigindan true range `high - low`ya duser
    (Pine'in `ta.tr(true)` "handle_na" davranisi).

    `ta.rma`, ilk bardan itibaren duz bir EMA DEGILDIR: `length` deger
    mevcut olana kadar tanimsizdir (NaN), o barda ilk `length` true-range
    degerinin duz SMA'siyla kendini seed eder, ancak ONDAN SONRA Wilder
    smoothing'e gecer: `rma[i] = rma[i-1] + (tr[i] - rma[i-1]) / length`.
    """
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    n = len(df)

    tr = np.empty(n)
    if n > 0:
        tr[0] = high[0] - low[0]
    if n > 1:
        prev_close = close[:-1]
        hl = high[1:] - low[1:]
        hc = np.abs(high[1:] - prev_close)
        lc = np.abs(low[1:] - prev_close)
        tr[1:] = np.maximum(hl, np.maximum(hc, lc))

    atr = np.full(n, np.nan)
    if n >= length:
        atr[length - 1] = tr[:length].mean()
        alpha = 1.0 / length
        for i in range(length, n):
            atr[i] = atr[i - 1] + (tr[i] - atr[i - 1]) * alpha
    return atr


def _is_valid_abcd(
    a_p: float, b_p: float, c_p: float, d_p: float, is_bearish: bool, params: Params
) -> tuple[bool, float, float]:
    """Pine'in `isValidABCD()` portu. (is_valid, bc_ratio, cd_ratio) doner."""
    ab = abs(b_p - a_p)
    if not ab > 0.0:
        return False, float("nan"), float("nan")

    bc_r = abs(c_p - b_p) / ab
    cd_r = abs(d_p - c_p) / ab

    if is_bearish:
        strict = a_p < c_p < b_p and d_p > b_p
    else:
        strict = a_p > c_p > b_p and d_p < b_p

    bc_ok = (params.min_bc_retrace - params.fib_tolerance) <= bc_r <= (
        params.max_bc_retrace + params.fib_tolerance
    )
    if params.use_exact_cd:
        cd_ok = abs(cd_r - 1.0) <= params.fib_tolerance
    else:
        cd_ok = (params.cd_min_ext - params.fib_tolerance) <= cd_r <= (
            params.cd_max_ext + params.fib_tolerance
        )

    return (strict and bc_ok and cd_ok), bc_r, cd_r


def detect(df: pd.DataFrame, params: Params) -> list[Signal]:
    """Pine'in `if barstate.isconfirmed` blogunun portu: rolling A/B/C/D
    pivot state machine + pattern taramasi, `df` uzerinde bar bar calisir.

    `df` kolonlari [time, open, high, low, close, volume] olmali, artan
    zamana sirali, onaylanmis her tarihsel bar icin bir satir.

    Sinyalleri artan `signal_bar` sirasinda doner.
    """
    L = params.pivot_lookback
    n = len(df)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    open_ = df["open"].to_numpy(dtype=float)
    time_col = df["time"]

    ph = pivot_high(high, L)
    pl = pivot_low(low, L)
    atr14 = atr_wilder(df, 14)

    # Rolling pivot state, Pine'in `var` skalerlerinin aynasi. Her pX ya
    # None (== Pine'in na'si) ya da bir (price, bar, type) tuple'idir; type
    # +1 (high) veya -1 (low)'dir.
    pA = pB = pC = pD = None
    last_ptype = 0
    last_d_drawn = -1

    signals: list[Signal] = []

    for i in range(n):
        # -- Adim 1: pivot alimi (kesin alternans) --------------------
        new_price = np.nan
        new_bar = None
        new_type = 0

        if not np.isnan(ph[i]) and last_ptype != 1:
            new_price, new_bar, new_type = float(ph[i]), i - L, 1
        elif not np.isnan(pl[i]) and last_ptype != -1:
            new_price, new_bar, new_type = float(pl[i]), i - L, -1

        if new_type != 0:
            pA, pB, pC = pB, pC, pD
            pD = (new_price, new_bar, new_type)
            last_ptype = new_type

        # -- Adim 2: pattern taramasi -----------------------------------
        # Bir pattern ancak D pivotunun tam olarak SET EDILDIGI barda yeni
        # onaylanabilir: A/B/C/D ve Params bunun disinda pivotlar arasi
        # degismedigi icin isValidABCD() deterministiktir, ayni D ile daha
        # sonraki barlarda tekrar kontrol Pine'in zaten hesapladigi ayni
        # (False) sonucu yeniden hesaplamak olurdu. `last_d_drawn` yine de
        # Pine kaynagiyla birebir ayni sekilde koruma altina alir, sadece
        # pratikte daha sonraki bir barda hicbir zaman false olmaz.
        if pA is not None and pD[1] != last_d_drawn:
            a_price, a_bar, a_type = pA
            b_price, b_bar, b_type = pB
            c_price, c_bar, c_type = pC
            d_price, d_bar, d_type = pD

            pattern_ok = False
            is_bear = False
            bc_ratio = cd_ratio = float("nan")

            if (
                params.enable_short
                and a_type == -1
                and b_type == 1
                and c_type == -1
                and d_type == 1
            ):
                valid, bc_r, cd_r = _is_valid_abcd(a_price, b_price, c_price, d_price, True, params)
                if valid:
                    pattern_ok, is_bear, bc_ratio, cd_ratio = True, True, bc_r, cd_r

            if (
                params.enable_long
                and a_type == 1
                and b_type == -1
                and c_type == 1
                and d_type == -1
            ):
                valid, bc_r, cd_r = _is_valid_abcd(a_price, b_price, c_price, d_price, False, params)
                if valid:
                    pattern_ok, is_bear, bc_ratio, cd_ratio = True, False, bc_r, cd_r

            if pattern_ok:
                last_d_drawn = d_bar
                signal_bar = d_bar + L  # == i

                entry_ref = float(close[d_bar])
                fill_bar = signal_bar + 1
                fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")

                ad_range = abs(a_price - d_price)
                if is_bear:
                    tp1 = d_price - ad_range * 0.382
                    sl = d_price + params.atr_mult * atr14[signal_bar]
                else:
                    tp1 = d_price + ad_range * 0.382
                    sl = d_price - params.atr_mult * atr14[signal_bar]
                tp2 = c_price

                signals.append(
                    Signal(
                        direction=-1 if is_bear else 1,
                        a_bar=a_bar,
                        b_bar=b_bar,
                        c_bar=c_bar,
                        d_bar=d_bar,
                        a_price=a_price,
                        b_price=b_price,
                        c_price=c_price,
                        d_price=d_price,
                        signal_bar=signal_bar,
                        signal_time=time_col.iloc[signal_bar],
                        entry_ref=entry_ref,
                        fill_ref=fill_ref,
                        tp1=float(tp1),
                        tp2=float(tp2),
                        sl=float(sl),
                        bc_ratio=float(bc_ratio),
                        cd_ratio=float(cd_ratio),
                    )
                )

    return signals
