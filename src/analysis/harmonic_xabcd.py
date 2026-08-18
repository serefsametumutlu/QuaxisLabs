"""XABCD harmonik formasyon tespiti (Gartley/Bat/Butterfly/Crab) -- Pine
parity, SAF MANTIK, I/O YOK.

Bu modul `pine/harmonic_formations_v1_indicator.pine` (V2.1, TradingView
Pine v6) dosyasinin Python portudur. `src/analysis/abcd_pattern.py`nin
(klasik AB=CD, 4 nokta) YANINDA yasar, ONUN YERINE GECMEZ -- ikisi kasitli
olarak AYRI modullerdir:

  - `abcd_pattern.py`: SADECE 4 nokta (A-B-C-D), CD AB'ye goreli. Pine
    kaynagi `abcd_v2_5_indicator.pine` ile LOCKSTEP kalmak ZORUNDA.
  - Bu modul (`harmonic_xabcd.py`): 5 nokta (X-A-B-C-D), literatur-dogru
    XABCD tanimi -- CD dogrudan BC'ye goreli, ARTI XD/XA tamamlanma orani
    (formasyonun ASIL ayirt edici olcusu). Pine kaynagi
    `harmonic_formations_v1_indicator.pine` (V2.1) ile LOCKSTEP.

## Neden ayri modul (yeni detector yazmama ilkesine ISTISNA)

`harmonic_presets.py` (eski, 4-noktali) modul ustu notu "yeni bir detector
YAZMA" diyordu -- ama o karar, BC/CD banti PARAMETRIK oldugu surece
gecerliydi. Kullanicinin 2026-08-18 canli TradingView testi (TUPRS) somut
bir sorun ortaya cikardi: Gartley/Bat/Butterfly SUREKLI ayni noktada
BIRLIKTE tetikleniyordu -- 4-noktali + AB-goreli-CD yaklasimi biraraya
geldiginde bantlar asiri genis/ortusen kaliyordu. Gercek duzeltme (X noktasi
+ BC-goreli CD + XD/XA kontrolu) `abcd_pattern.py`nin state machine'ini
DEGISTIRMEDEN eklenemezdi (5. nokta, farkli oran tanimlari) -- bu yuzden
YENI, PARALEL bir modul, `abcd_pattern.py`ye HICBIR SEKILDE DOKUNMADAN.

## KRITIK matematiksel not -- XD/XA yonu (canli hata + duzeltme, 2026-08-18)

Standart Fibonacci retracement okunuşu (X'ten A'ya cizilen bir retracement
aracinin "0.786" seviyesi): D, A'dan XA bacaginin %78.6'si kadar GERI
CEKILMIS bir fiyattir -- yani dogru oran `xd_r = |D-A|/|A-X|`dir. Bu
modulun ilk Pine taslaginda (V2.1, ilk commit) YANLISLIKLA `|D-X|/|A-X|`
(TAMAMLAYAN oran, `1 - xd_r_dogru`) kullanilmisti -- kullanici canli testte
"gercek sinyaller cok azaldi + PRZ bazen alakasiz" bildirince fark edildi
(D'nin OLMASI gereken bolgenin TAM TERSI arandigi icin ya hic sinyal
gelmiyordu ya da yanlislikla farkli bir bolgede "gecerli" sayiliyordu). Bu
modul BASTAN ITIBAREN dogru formulu (`|D-A|/XA`) kullanir; Pine kaynagi da
AYNI committe duzeltildi (bkz. o dosyanin "DUZELTME" yorumu).

## PRZ (Potential Reversal Zone) erken tespiti

`detect_prz()`, Pine'daki opsiyonel "erken uyari" katmaninin portudur:
onayli X-A-B-C tamamlaninca (D henuz olusmadan), CD/BC + XD/XA
projeksiyonlarinin KESISIMINDEN bir fiyat bolgesi hesaplar, o bolgeye
fiyatin ILK DEGDIGI barda bir `PrzEvent` uretir (mum kapanmadan canli tetik
Pine'a OZGU bir kavramdir; burada "bar'in high/low araligi bolgeye
degdi mi" ile modellenir -- backtest'te tarihsel her bar zaten
"onaylanmis" kabul edildigi icin bu, Pine'in intrabar canli tetiginin en
yakin, look-ahead'siz karsiligidir).

`vindication` (dogrulanma) analizi: bir PRZ olayinin GERCEK bir formasyona
mi yoksa "yanlis alarm"a mi denk geldigi, AYNI `c_bar` + yon icin sonradan
gercekten bir onayli `Signal` uretilip uretilmedigine bakilarak (bkz.
`match_prz_to_confirmed()`) OBJEKTIF olarak olculebilir -- kullanicinin
"bazi PRZ sinyalleri alakasiz" gozlemini SAYISALLASTIRIR.

Katman disiplini: `abcd_pattern.py` ile AYNI -- `src.fetchers.*`/`src.db.*`
HICBIR modulu import etmez, tamamen float + numpy/pandas (Pine float64
parity zorunlulugu, Decimal istisnasi `abcd_pattern.py` ile AYNI gerekce).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.analysis.abcd_pattern import atr_wilder, pivot_high, pivot_low

OHLC_COLUMNS = ("time", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class Params:
    """`pine/harmonic_formations_v1_indicator.pine`deki (V2.1) her formasyon
    on-ayarinin sayisal ikizi -- `HARMONIC_XABCD_PRESETS` uzerinden erisilir,
    dogrudan elle KURULMAZ (Custom disinda)."""

    name: str
    pivot_lookback: int = 5
    fib_tolerance: float = 0.05
    min_bc_retrace: float = 0.382
    max_bc_retrace: float = 0.886
    cd_bc_min: float = 1.272
    cd_bc_max: float = 1.618
    xd_target: float = 0.786
    atr_mult: float = 1.0
    enable_long: bool = True
    enable_short: bool = True
    # V2.2 EKLENTISI (2026-08-18, kullanici canli test raporu -- TATGD'de
    # "ABCD exact 1.0" sectigi halde sinyal gelmiyordu): Pine V2.2
    # (`harmonic_formations_v1_indicator.pine`) artik klasik AB=CD'yi de
    # AYNI anlik-D mekanizmasinin bir preseti olarak isliyor -- bu alanlar
    # o "else" (is_xabcd=False) dalini Python'da da mumkun kilar. `is_xabcd
    # =False` iken cd_bc_min/max/xd_target KULLANILMAZ (X noktasi da hic
    # gerekmez), yerine klasik AB-goreli CD tanimi (`abcd_pattern.py` ile
    # AYNI formul) gecerlidir.
    is_xabcd: bool = True
    use_exact_cd: bool = True
    cd_min_ext: float = 0.886
    cd_max_ext: float = 1.272


# Pine `eff_cd_bc_min/max`/`eff_xd_target` ternary zincirleriyle BIREBIR AYNI
# sayilar (bkz. o dosyanin "FORMATION PRESET -> bantlar" bolumu). SADECE
# XABCD (X-noktali) 4 aileyi icerir -- `ABCD_PRESET` (klasik AB=CD, is_xabcd
# =False) KASITLI olarak buraya EKLENMEDI: bu sozluk uzerinde `for name,
# params in HARMONIC_XABCD_PRESETS.items()` diye donen mevcut scriptler
# (harmonic_xabcd_research.py/vindication_factors.py/prz_filter_backtest.py,
# bkz. onlarin ust notlari) zaten calisip commit edilmis SONUCLAR uretti --
# buraya sessizce 5. bir eleman eklemek o scriptleri (ve gecmis raporlarini)
# SESSIZCE degistirebilirdi. ABCD preseti ayri tutulur (asagida).
HARMONIC_XABCD_PRESETS: dict[str, Params] = {
    "GARTLEY": Params(name="GARTLEY", cd_bc_min=1.272, cd_bc_max=1.618, xd_target=0.786),
    "BAT": Params(name="BAT", cd_bc_min=1.618, cd_bc_max=2.618, xd_target=0.886),
    "BUTTERFLY": Params(name="BUTTERFLY", cd_bc_min=1.618, cd_bc_max=2.24, xd_target=1.27),
    "CRAB": Params(name="CRAB", cd_bc_min=2.24, cd_bc_max=3.618, xd_target=1.618),
}

# Klasik AB=CD (Pine V2.2'nin "ABCD (exact 1.0)" preseti, is_xabcd=False --
# X noktasi/XD kontrolu YOK, CD AB'ye goreli). `HARMONIC_XABCD_PRESETS`e
# BILINCLI olarak DAHIL EDILMEDI (yukaridaki not) -- SADECE V2.2'nin "anlik
# D" mekanizmasini TUM 5 formasyon icin backtest eden yeni scriptler bunu
# ayrica import eder.
ABCD_PRESET = Params(name="ABCD", is_xabcd=False, use_exact_cd=True)


@dataclass(frozen=True)
class Signal:
    """Onaylanmis (confirmed) TEK bir XABCD formasyonu -- `abcd_pattern.Signal`
    ile alan-ADI uyumlu (direction/signal_bar/entry_ref/fill_ref/tp1/tp2/sl),
    boylece `abcd_backtest.backtest_symbol`/`compute_metrics` HICBIR
    DEGISIKLIK olmadan bu modulun sinyalleriyle de calisir (duck-typing) --
    ARTI x_bar/x_price/xd_ratio (XABCD'ye ozgu, `abcd_pattern.Signal`de yok)."""

    direction: int  # +1 = bullish/BUY, -1 = bearish/SELL
    x_bar: int
    a_bar: int
    b_bar: int
    c_bar: int
    d_bar: int
    x_price: float
    a_price: float
    b_price: float
    c_price: float
    d_price: float
    signal_bar: int  # = d_bar + pivot_lookback
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    bc_ratio: float
    cd_ratio: float  # = cd_bc_r (BC'ye goreli, abcd_pattern.Signal.cd_ratio'nun AB-goreli tanimindan FARKLI)
    xd_ratio: float


@dataclass(frozen=True)
class PrzEvent:
    """Onaylanmamis (teyitsiz) erken PRZ bolge-girisi -- `Signal` ile AYNI
    alan sozlesmesi (backtest_symbol uyumlulugu icin), `d_bar`/`d_price`
    burada GERCEK D DEGIL, bolgeye ILK DEGEN barin fiyatidir (proxy)."""

    direction: int
    x_bar: int
    a_bar: int
    b_bar: int
    c_bar: int
    d_bar: int  # = touch_bar (proxy, D HENUZ ONAYLANMADI)
    x_price: float
    a_price: float
    b_price: float
    c_price: float
    d_price: float  # = bolgeye ilk degen fiyat (proxy D)
    signal_bar: int  # = touch_bar
    signal_time: pd.Timestamp
    entry_ref: float
    fill_ref: float
    tp1: float
    tp2: float
    sl: float
    bc_ratio: float
    zone_low: float
    zone_high: float


def _is_valid_xabcd(
    x_p: float, a_p: float, b_p: float, c_p: float, d_p: float, is_bearish: bool, params: Params
) -> tuple[bool, float, float, float]:
    """Pine'in `isValidHarmonic()` portu (XABCD dali). (is_valid, bc_ratio,
    cd_bc_ratio, xd_ratio) doner."""
    ab = abs(b_p - a_p)
    bc = abs(c_p - b_p)
    if not ab > 0.0 or not bc > 0.0:
        return False, float("nan"), float("nan"), float("nan")

    bc_r = bc / ab
    if is_bearish:
        strict = a_p < c_p < b_p and d_p > b_p
    else:
        strict = a_p > c_p > b_p and d_p < b_p

    bc_ok = (params.min_bc_retrace - params.fib_tolerance) <= bc_r <= (params.max_bc_retrace + params.fib_tolerance)

    cd_bc_r = abs(d_p - c_p) / bc
    cd_ok = (params.cd_bc_min - params.fib_tolerance) <= cd_bc_r <= (params.cd_bc_max + params.fib_tolerance)

    xa = abs(a_p - x_p)
    if xa > 0.0:
        xd_r = abs(d_p - a_p) / xa  # KRITIK: A'ya goreli retracement, X'e DEGIL (bkz. modul ust notu)
        xd_ok = abs(xd_r - params.xd_target) <= params.fib_tolerance
    else:
        xd_r = float("nan")
        xd_ok = False

    return (strict and bc_ok and cd_ok and xd_ok), bc_r, cd_bc_r, xd_r


def detect(df: pd.DataFrame, params: Params) -> list[Signal]:
    """Pine'in `if barstate.isconfirmed` blogunun (XABCD dali) portu:
    rolling X/A/B/C/D pivot state machine + pattern taramasi."""
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

    pX = pA = pB = pC = pD = None
    last_ptype = 0
    last_d_drawn = -1

    signals: list[Signal] = []

    for i in range(n):
        new_price = np.nan
        new_bar = None
        new_type = 0

        if not np.isnan(ph[i]) and last_ptype != 1:
            new_price, new_bar, new_type = float(ph[i]), i - L, 1
        elif not np.isnan(pl[i]) and last_ptype != -1:
            new_price, new_bar, new_type = float(pl[i]), i - L, -1

        if new_type != 0:
            pX, pA, pB, pC = pA, pB, pC, pD
            pD = (new_price, new_bar, new_type)
            last_ptype = new_type

        if pA is not None and pD[1] != last_d_drawn:
            x_price, x_bar, x_type = pX if pX is not None else (float("nan"), -1, 0)
            a_price, a_bar, a_type = pA
            b_price, b_bar, b_type = pB
            c_price, c_bar, c_type = pC
            d_price, d_bar, d_type = pD

            pattern_ok = False
            is_bear = False
            bc_ratio = cd_ratio = xd_ratio = float("nan")

            if (
                params.enable_short
                and a_type == -1 and b_type == 1 and c_type == -1 and d_type == 1
                and x_type == 1
            ):
                valid, bc_r, cd_r, xd_r = _is_valid_xabcd(x_price, a_price, b_price, c_price, d_price, True, params)
                if valid:
                    pattern_ok, is_bear, bc_ratio, cd_ratio, xd_ratio = True, True, bc_r, cd_r, xd_r

            if (
                params.enable_long
                and a_type == 1 and b_type == -1 and c_type == 1 and d_type == -1
                and x_type == -1
            ):
                valid, bc_r, cd_r, xd_r = _is_valid_xabcd(x_price, a_price, b_price, c_price, d_price, False, params)
                if valid:
                    pattern_ok, is_bear, bc_ratio, cd_ratio, xd_ratio = True, False, bc_r, cd_r, xd_r

            if pattern_ok:
                last_d_drawn = d_bar
                signal_bar = d_bar + L

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
                        x_bar=x_bar, a_bar=a_bar, b_bar=b_bar, c_bar=c_bar, d_bar=d_bar,
                        x_price=x_price, a_price=a_price, b_price=b_price, c_price=c_price, d_price=d_price,
                        signal_bar=signal_bar,
                        signal_time=time_col.iloc[signal_bar],
                        entry_ref=entry_ref,
                        fill_ref=fill_ref,
                        tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                        bc_ratio=float(bc_ratio), cd_ratio=float(cd_ratio), xd_ratio=float(xd_ratio),
                    )
                )

    return signals


def detect_prz(df: pd.DataFrame, params: Params) -> list[PrzEvent]:
    """Pine'in opsiyonel PRZ (erken uyari) blogunun portu -- her bar icin
    GUNCEL (en son onayli) X/A/B/C zincirini "beklenen D bolgesi" olarak
    yeniden yorumlar, CD/BC + XD/XA projeksiyonlarinin KESISIMINI hesaplar,
    fiyat (o barin high/low araligi) bolgeye ILK degdiginde bir `PrzEvent`
    uretir. Ayni prospektif C icin (yeni bir pivot onaylanana kadar) SADECE
    ILK degis raporlanir (Pine'daki `przAlerted` bayraginin portu)."""
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

    pX = pA = pB = pC = pD = None
    last_ptype = 0

    prz_active_c: int | None = None
    prz_alerted = False

    events: list[PrzEvent] = []

    for i in range(n):
        new_price = np.nan
        new_bar = None
        new_type = 0
        if not np.isnan(ph[i]) and last_ptype != 1:
            new_price, new_bar, new_type = float(ph[i]), i - L, 1
        elif not np.isnan(pl[i]) and last_ptype != -1:
            new_price, new_bar, new_type = float(pl[i]), i - L, -1
        if new_type != 0:
            pX, pA, pB, pC = pA, pB, pC, pD
            pD = (new_price, new_bar, new_type)
            last_ptype = new_type

        # Prospektif A/B/C = guncel pB/pC/pD (D henuz olusmamis) -- bu UCU,
        # HERHANGI bir projeksiyon (XABCD veya klasik ABCD) icin MINIMUM
        # gereksinimdir. Prospektif X (=pA) SADECE `is_xabcd` formasyonlar
        # icin (XD projeksiyonu icin) gerekir.
        #
        # CANLI HATA + DUZELTME (2026-08-18, kullanici TATGD karsilastirmasi
        # -- "ABCD exact 1.0 secmeme ragmen hic sinyal gelmiyor"): eski kod
        # `pA is None` (=X henuz yok) durumunda da TUM barlari atliyordu --
        # klasik ABCD'nin (`is_xabcd=False`) X'e HICBIR ZAMAN ihtiyaci
        # olmadigi halde, sadece 3 pivot (A,B,C) yeterliyken 4 pivot (X,A,B,C)
        # birikene kadar HICBIR projeksiyon denenmiyordu -- ilk formasyon
        # dongusunu tamamen KACIRIYORDU. Pine V2.2 (`valid_pending`) zaten
        # SADECE 3 nokta gerektiriyordu, bu satir simdi ONA UYDURULDU.
        if pB is None or pC is None or pD is None:
            continue
        q_x = pA  # None OLABILIR -- asagida is_xabcd icin ayrica kontrol edilir
        q_a = pB
        q_b = pC
        q_c = pD

        if q_c[1] != prz_active_c:
            prz_active_c = q_c[1]
            prz_alerted = False

        if prz_alerted:
            continue

        is_bear2 = q_c[2] == -1
        if is_bear2 and not params.enable_short:
            continue
        if not is_bear2 and not params.enable_long:
            continue

        # Yapisal siralama (CANLI HATA + DUZELTME, 2026-08-18, kullanici
        # Pine karsilastirmasi -- ayni eksiklik `pine/harmonic_formations_v1_
        # indicator.pine`de de bulunup duzeltildi): BC orani TEK BASINA
        # q_c'nin q_a ile q_b ARASINDA kaldigini GARANTI ETMEZ (sadece
        # |q_c-q_b|/|q_a-q_b| BUYUKLUGUNU olcer, YONU/SIRALAMAYI degil) --
        # bu kontrol olmadan A'yi ASAN bir "sahte" C de ayni orani
        # tutturabilirdi.
        strct2 = (q_a[0] < q_c[0] < q_b[0]) if is_bear2 else (q_a[0] > q_c[0] > q_b[0])
        if not strct2:
            continue

        ab2 = abs(q_b[0] - q_a[0])
        bc2 = abs(q_c[0] - q_b[0])
        if not (ab2 > 0.0 and bc2 > 0.0):
            continue

        bc_r2 = bc2 / ab2
        if not (
            (params.min_bc_retrace - params.fib_tolerance)
            <= bc_r2
            <= (params.max_bc_retrace + params.fib_tolerance)
        ):
            continue

        # CD projeksiyonu -- XABCD (Gartley/Bat/Butterfly/Crab): BC-goreli,
        # dar CD/BC bandi. Klasik ABCD (`params.is_xabcd=False`, Pine V2.2'nin
        # "ABCD (exact 1.0)"/Custom preseti): AB-goreli, `abcd_pattern.py` ile
        # AYNI tanim (`use_exact_cd`/`cd_min_ext`/`cd_max_ext`).
        if params.is_xabcd:
            if is_bear2:
                cd_lo = q_c[0] + (params.cd_bc_min - params.fib_tolerance) * bc2
                cd_hi = q_c[0] + (params.cd_bc_max + params.fib_tolerance) * bc2
            else:
                cd_lo = q_c[0] - (params.cd_bc_max + params.fib_tolerance) * bc2
                cd_hi = q_c[0] - (params.cd_bc_min - params.fib_tolerance) * bc2
        else:
            cd_min_use = (1.0 - params.fib_tolerance) if params.use_exact_cd else (params.cd_min_ext - params.fib_tolerance)
            cd_max_use = (1.0 + params.fib_tolerance) if params.use_exact_cd else (params.cd_max_ext + params.fib_tolerance)
            if is_bear2:
                cd_lo = q_c[0] + cd_min_use * ab2
                cd_hi = q_c[0] + cd_max_use * ab2
            else:
                cd_lo = q_c[0] - cd_max_use * ab2
                cd_hi = q_c[0] - cd_min_use * ab2

        if params.is_xabcd:
            if q_x is None:
                continue  # XABCD icin X sart -- klasik ABCD'nin aksine burada zarif "degrade" YOK (XD tanimlayici olcu)
            xa2 = abs(q_a[0] - q_x[0])
            if not xa2 > 0.0:
                continue
            xd_center = q_a[0] + params.xd_target * xa2 if is_bear2 else q_a[0] - params.xd_target * xa2
            xd_half = params.fib_tolerance * xa2
            xd_lo, xd_hi = xd_center - xd_half, xd_center + xd_half
            zone_low, zone_high = max(cd_lo, xd_lo), min(cd_hi, xd_hi)
        else:
            # Klasik ABCD: X noktasi/XD kontrolu YOK (Pine'in `not is_xabcd`
            # dalinda oldugu gibi) -- bolge dogrudan CD projeksiyonudur.
            zone_low, zone_high = cd_lo, cd_hi
        if zone_low > zone_high:
            continue

        entered = low[i] <= zone_high and high[i] >= zone_low
        if not entered:
            continue

        touch_price = zone_high if not is_bear2 else zone_low
        # Yapisal D kontrolu (CANLI HATA + DUZELTME, ayni gerekce -- D, B'nin
        # ARKASINDA/OTESINDE kalmali, C'ye cok yakin sahte bir bolge
        # eslesmesi OLMAMALI).
        d_structurally_ok = touch_price > q_b[0] if is_bear2 else touch_price < q_b[0]
        if not d_structurally_ok:
            continue

        prz_alerted = True
        d_bar = i
        signal_bar = i
        entry_ref = float(close[i])
        fill_bar = signal_bar + 1
        fill_ref = float(open_[fill_bar]) if fill_bar < n else float("nan")

        ad_range = abs(q_a[0] - touch_price)
        if is_bear2:
            tp1 = touch_price - ad_range * 0.382
            sl = touch_price + params.atr_mult * atr14[signal_bar]
        else:
            tp1 = touch_price + ad_range * 0.382
            sl = touch_price - params.atr_mult * atr14[signal_bar]
        tp2 = q_c[0]

        events.append(
            PrzEvent(
                direction=-1 if is_bear2 else 1,
                x_bar=(q_x[1] if q_x is not None else -1), a_bar=q_a[1], b_bar=q_b[1], c_bar=q_c[1], d_bar=d_bar,
                x_price=(q_x[0] if q_x is not None else float("nan")), a_price=q_a[0], b_price=q_b[0], c_price=q_c[0], d_price=touch_price,
                signal_bar=signal_bar,
                signal_time=time_col.iloc[signal_bar],
                entry_ref=entry_ref, fill_ref=fill_ref,
                tp1=float(tp1), tp2=float(tp2), sl=float(sl),
                bc_ratio=float(bc_r2), zone_low=float(zone_low), zone_high=float(zone_high),
            )
        )

    return events


def match_prz_to_confirmed(prz_events: list[PrzEvent], confirmed: list[Signal]) -> list[bool]:
    """Her `PrzEvent` icin, AYNI `c_bar` + yonde sonradan gercekten bir
    onayli `Signal` uretilip uretilmedigini doner (`vindicated` listesi,
    `prz_events` ile AYNI sirada/uzunlukta). Bu, "bu erken uyari GERCEK bir
    formasyona mi denk geldi" sorusunun OBJEKTIF, backtest-edilebilir
    cevabidir -- kullanicinin "bazi PRZ sinyalleri alakasiz" gozlemini
    sayisallastirmak icin."""
    confirmed_keys = {(s.c_bar, s.direction) for s in confirmed}
    return [(ev.c_bar, ev.direction) in confirmed_keys for ev in prz_events]
