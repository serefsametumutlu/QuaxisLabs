"""AB=CD "erken tespit" arastirmasi -- D pivotu henuz ONAYLANMADAN (sadece
ABC olusmus, C onaylanmisken), o ana kadarki C->D ilerlemesine (`cd_progress`)
bakarak "bu aday tarihsel olarak ne siklikta gecerli bir D ile TAMAMLANIR"
sorusuna DURUST, istatistiksel olarak sağlam bir cevap uretir.

Metodoloji kaynagi: gorev talimatinin "METODOLOJI" bolumu (quant-mathematician
+ market-microstructure-expert + devils-advocate-risk-finder uc-agent
denetiminin sonucu) -- bu modul o metodolojiyi BIREBIR uygular, yeniden
tasarlamaz.

## KESIN dil kurali (metodoloji, madde 5)

Bu modul VE onu kullanan her rapor/CLI **"olasilik" kelimesini KULLANMAZ**.
Uretilen sey bir olasilik modeli DEGIL, HAM FREKANS + Wilson %95 guven
araligi + null-hipotez (GBM rastgele yuruyus) karsilastirmasidir. Kucuk
orneklemde sahte kesinlik riski (bkz. `abcd_backtest.py`/`spec_kapsam_cezali_
skor.md`deki AYNI disiplin) -- n<30 olan hucreler ASLA gizlenmez, "GUVENSIZ
(n=X)" etiketlenir.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`.

  Karar 1 -- Modul izolasyonu: `abcd_pattern.py`/`abcd_backtest.py`/
  `abcd_factor_analysis.py` ile AYNI ilke -- bu modul de `src/analysis/`in
  genel felsefesinden (skorsuz/sinyalsiz) BILINCLI bir sapmadir; yonlu
  AL/SAT sinyali degil, ILISKISEL/tanimlayici bir frekans analizi uretir.
  Bir istisnadir, emsal DEGILDIR.

  Karar 2 -- Decimal istisnasi: AYNI gerekceyle (ayni float64 sinyal/fiyat
  zincirinin devami) bu modul TAMAMEN float + numpy/pandas/statsmodels/scipy
  kullanir. Float deger BURADAN hicbir zaman Decimal tipli dataclass'lara/
  `scorer.py`'ye/`calculator.py`'ye SIZMAZ.

Katman disiplini: `abcd_pattern.py` ile AYNI -- bu modul `src.fetchers.*`/
`src.db.*` HICBIR modulu import ETMEZ, saf mantik + I/O YOK. Girdi olarak
zaten cekilmis `pd.DataFrame`(lar) alir. Gercek veri/DB orkestrasyonu
`scripts/abcd_early_detection_research.py`'dedir.

## Pine-parity notu -- bu modul Pine kaynaginin PORTU DEGIL

`abcd_pattern.py`nin aksine bu modulun Pine'da bir karsiligi YOK (Pine
gostergesi sadece ONAYLANMIS D'yi cizer, "D henuz yokken ilerleme" kavramini
hic modellemez) -- bu YENI bir arastirma katmanidir. Yine de `pivot_high`/
`pivot_low`/`_is_valid_abcd`i (abcd_pattern.py'den, KASITLI olarak private
`_is_valid_abcd` dahil) DOGRUDAN import eder, KOPYALAMAZ -- amac: ayni oran
dogrulama mantiginin BAGIMSIZ bir kopyasini yazip iki dosyanin sessizce
SURUKLENMESI riskini almamak (bkz. abcd_pattern.py modul-ust notu: "Pine
mantigindan Python tarafinda BAGIMSIZ 'iyilestirme' YAPILMAZ").

## Look-ahead disiplini

C onaylandiktan (`c_confirm = c_bar + pivot_lookback`) SONRAKI barlardan
(`i > c_confirm`, sadece kapanmis/onaylanmis barlar; formasyonu HENUZ
olusturmakta olan "forming" bar hicbir zaman kullanilmaz) itibaren ilerleme
hesaplanir. D adayi olarak kullanilan pivot da (varsa) KENDI onay barinda
(`d_bar + pivot_lookback`) degerlendirilir -- `abcd_pattern.py` ile AYNI
onay-hizalama ilkesi, bkz. o modulun `pivot_high`/`pivot_low` docstring'i.

## Kova tablosu tasarim notu -- bar-seviyeli gozlem, aday-seviyeli DEGIL

`build_bucket_table`, HER (aday, bar) ciftini AYRI bir gozlem sayar (aday C
onayindan nihai sonucuna kadar gectigi HER kovaya bir gozlem birakir), sonuc
etiketi (basari/basarisiz) o adayin NIHAI etiketidir. Bu, "CD ilerlemesi
%X-%Y araligindayken D'ye ulasma sikligi" (gorev dilinin BIREBIR karsiligi)
sorusuna doğal karsilik gelir, ama ISTATISTIKSEL bir uyari tasir: AYNI
adayin ardisik barlari BAGIMSIZ gozlemler DEGILDIR (otokorelasyonlu) --
Wilson araligi bu yuzden HAFIFCE iyimser olabilir. Bu, "olasilik modeli
DEGIL, ham frekans sayimi" cercevesiyle TUTARLIDIR (metodoloji madde 5) ve
raporda ACIKCA belirtilir; aday-basina TEK gozlem alternatifi (orn. "nihai
olay barindaki ilerleme") de gecerli bir tasarimdir ama "hangi ilerleme
araliginda GEC ILERI" sorusunu YANITLAMAZ -- bu yuzden bar-seviyeli tasarim
BILINCLI olarak secildi.

## Kova ust siniri -- "100%+" acik uclu (spec'in "100-120%" etiketinden sapma)

Varsayilan `cd_max_ext=1.272` + `fib_tolerance=0.05` ile asiri-uzama esigi
1.322'dir -- yani bir bar 1.20-1.322 araliginda ilerleme gosterebilir, D
adayi ya da asiri-uzama BU aralikta HENUZ tetiklenmemis olabilir. Sabit bir
"100-120%" kovasi bu degerleri SESSIZCE disarida birakirdi (ya da yanlis
kovaya sigdirilirdi); bunun yerine son kova ACIK UCLU (`>=100%`, "100%+"
etiketli) birakilir -- higbir gozlem sessizce KAYBOLMAZ.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

from src.analysis.abcd_pattern import Params, Signal, _is_valid_abcd, pivot_high, pivot_low

# ── sabitler ─────────────────────────────────────────────────────────────

BUCKET_EDGES = (0.0, 0.20, 0.40, 0.60, 0.80, 1.00)
BUCKET_LABELS = ("0-20%", "20-40%", "40-60%", "60-80%", "80-100%", "100%+")

MIN_TRUSTWORTHY_N = 30  # abcd_backtest.py::run_grid'in min_trades_show'uyla AYNI disiplin
T_MAX_FLOOR_BARS = 20  # cok az/hicbir sinyal yoksa (kucuk evren/kisa test verisi) taban


# ── veri yapilari ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ABCCandidate:
    """D henuz onaylanmamisken tespit edilmis bir A->B->C ucluesu.

    `c_confirm`, C'nin PIVOT olarak onaylandigi bardir (`c_bar +
    pivot_lookback`) -- erken tespit tam bu bardan itibaren "aktif" olur.
    `is_long`: True ise C bir tepe (high), beklenen D bir dip (low) --
    `abcd_pattern.detect()`'in "long/BUY" yonuyle AYNI kural (a=high,
    b=low, c=high, d=low bekleniyor).
    """

    a_price: float
    a_bar: int
    b_price: float
    b_bar: int
    c_price: float
    c_bar: int
    c_confirm: int
    is_long: bool


@dataclass(frozen=True)
class CandidateLabel:
    """Bir `ABCCandidate`in nihai (ileri-taramali) etiketi."""

    candidate: ABCCandidate
    label: int | None  # 1=basari, 0=basarisiz (overextension/reshuffled), None=timeout (belirsiz)
    reason: str  # "success" | "overextension" | "reshuffled" | "timeout"
    t_event: int | None  # etiketin belirlendigi barin c_confirm'e gore ofseti (timeout'ta None)


@dataclass(frozen=True)
class BucketObservation:
    """Tek bir (aday, bar) gozlemi -- bkz. modul-ust "Kova tablosu tasarim notu"."""

    is_long: bool
    bucket_index: int
    outcome: int | None  # adayin NIHAI etiketi (1/0/None) -- bkz. modul notu


# ── pivot sirasi + aday tespiti ─────────────────────────────────────────


def _ordered_pivots(high: np.ndarray, low: np.ndarray, L: int) -> list[tuple[float, int, int, int]]:
    """(price, bar, type, confirm_bar) -- `abcd_pattern.detect()`nin ayni
    kesin-alternans/onay-hizalama mantiginin PORTU, ama SADECE son 4
    pivotu degil TUM pivot dizisini kronolojik sirayla biriktirir. Erken
    tespit, henuz D gelmemisken her ABC ucluesunu analiz etmek icin tam
    pivot GECMISINE ihtiyac duyar (`detect()`nin rolling 4-skaler state'i
    bu amaca yetmez)."""
    ph = pivot_high(high, L)
    pl = pivot_low(low, L)
    n = len(high)
    pivots: list[tuple[float, int, int, int]] = []
    last_ptype = 0
    for i in range(n):
        new_price = np.nan
        new_bar: int | None = None
        new_type = 0
        if not np.isnan(ph[i]) and last_ptype != 1:
            new_price, new_bar, new_type = float(ph[i]), i - L, 1
        elif not np.isnan(pl[i]) and last_ptype != -1:
            new_price, new_bar, new_type = float(pl[i]), i - L, -1
        if new_type != 0:
            pivots.append((new_price, new_bar, new_type, i))
            last_ptype = new_type
    return pivots


def _build_candidates(
    pivots: list[tuple[float, int, int, int]], params: Params
) -> list[tuple[ABCCandidate, tuple[float, int, int, int] | None]]:
    """Her `(A,B,C)` ardisik pivot ucluesunden bir `ABCCandidate` kurar --
    tip alternansi PIVOT KABUL kuralindan (bkz. `_ordered_pivots`) zaten
    otomatik saglanir (ardisik kabul edilen pivotlar HER ZAMAN alternandir),
    bu yuzden ayrica bir tip-eslesme kontrolu GEREKMEZ. `next_pivot`
    (varsa), bu adayin D'si OLABILECEK bir sonraki pivottur -- henuz
    gelmemisse `None`."""
    out: list[tuple[ABCCandidate, tuple[float, int, int, int] | None]] = []
    for k in range(2, len(pivots)):
        a_price, a_bar, _a_type, _ = pivots[k - 2]
        b_price, b_bar, _b_type, _ = pivots[k - 1]
        c_price, c_bar, c_type, c_confirm = pivots[k]

        is_long = c_type == 1
        if is_long and not params.enable_long:
            continue
        if not is_long and not params.enable_short:
            continue
        if not abs(b_price - a_price) > 0.0:
            continue  # dejenere AB araligi -- ilerleme/oran hesaplanamaz

        candidate = ABCCandidate(a_price, a_bar, b_price, b_bar, c_price, c_bar, c_confirm, is_long)
        next_pivot = pivots[k + 1] if k + 1 < len(pivots) else None
        out.append((candidate, next_pivot))
    return out


def find_abc_candidates(df: pd.DataFrame, params: Params) -> list[ABCCandidate]:
    """`df` (kolonlar: high, low en az) icindeki TUM A->B->C adaylarini
    (D henuz onaylanmamis) kronolojik `c_confirm` sirasinda doner."""
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    pivots = _ordered_pivots(high, low, params.pivot_lookback)
    return [c for c, _next in _build_candidates(pivots, params)]


# ── ilerleme + etiketleme ────────────────────────────────────────────────


def cd_progress_at(close_price: float, c_price: float, is_long: bool, ab_range: float) -> float:
    """`_is_valid_abcd`deki `cd_r = |d_p - c_p| / ab` ile AYNI formul,
    sadece D henuz bir pivot degilken ANLIK `close_price` ile hesaplanir.

    Yon kontrolu (metodoloji madde 1): `is_long` (C tepe, D dip beklentisi)
    ise gecerli yon `close_price < c_price`dir (fiyat C'nin ALTINA
    inmeli); degilse (C dip, D tepe beklentisi) gecerli yon `close_price >
    c_price`dir. Yanlis yonde (henuz gerceklesmemis/ters hareket) `0.0`
    doner -- asla negatif/anlamsiz bir ilerleme uydurulmaz.
    """
    if ab_range <= 0.0:
        return 0.0
    if is_long:
        if not close_price < c_price:
            return 0.0
    else:
        if not close_price > c_price:
            return 0.0
    return abs(close_price - c_price) / ab_range


def _bucket_index(progress: float) -> int | None:
    if progress < 0.0 or math.isnan(progress):
        return None
    for i in range(len(BUCKET_EDGES) - 1):
        if BUCKET_EDGES[i] <= progress < BUCKET_EDGES[i + 1]:
            return i
    return len(BUCKET_LABELS) - 1  # progress >= 1.00 -> acik uclu son kova, bkz. modul-ust not


def _label_one(
    candidate: ABCCandidate,
    next_pivot: tuple[float, int, int, int] | None,
    close: np.ndarray,
    n: int,
    params: Params,
    t_max: int,
) -> tuple[CandidateLabel, list[BucketObservation]]:
    """Tek bir adayi `c_confirm+1`den itibaren ileri tarar (uc-cikisli
    etiketleme, metodoloji madde 2):

      (a) Basari -- karsit tipte bir pivot TAM bu barda onaylanir VE
          `_is_valid_abcd` True doner.
      (b) Asiri-uzama iptali -- (henuz hicbir pivot onaylanmadan) bir
          barin `cd_progress`si `cd_max_ext + fib_tolerance`yi asar.
      (c) Sessiz reshuffle -- karsit tipte bir pivot TAM bu barda
          onaylanir ama oran testi FAIL.

    Ayni barda hem pivot-onayi hem asiri-uzama esigi asilmis olabilir --
    ONCELIK pivot-onayindadir (fiili tamamlanma/reddi, o barin KENDI D
    aday fiyatiyla degerlendirilir; `close` tabanli esik sadece pivot
    HENUZ yokken bir sinyal saglar).

    `t_max` bar icinde hicbiri gerceklesmezse (ya da veri biterse) `label=
    None`, `reason="timeout"` (belirsiz -- ne basari ne ret).

    Donen `BucketObservation` listesi, taranan HER bar icin (adayin nihai
    etiketiyle) bir gozlem icerir -- bkz. modul-ust "Kova tablosu tasarim
    notu".
    """
    ab_range = abs(candidate.b_price - candidate.a_price)
    limit = min(n - 1, candidate.c_confirm + t_max)

    bars_walked: list[tuple[int, float]] = []
    label: int | None = None
    reason = "timeout"
    t_event: int | None = None

    for i in range(candidate.c_confirm + 1, limit + 1):
        progress = cd_progress_at(float(close[i]), candidate.c_price, candidate.is_long, ab_range)
        bars_walked.append((i, progress))

        if next_pivot is not None and next_pivot[3] == i:
            d_price = next_pivot[0]
            valid, _bc_r, _cd_r = _is_valid_abcd(
                candidate.a_price,
                candidate.b_price,
                candidate.c_price,
                d_price,
                is_bearish=not candidate.is_long,
                params=params,
            )
            if valid:
                label, reason, t_event = 1, "success", i - candidate.c_confirm
            else:
                label, reason, t_event = 0, "reshuffled", i - candidate.c_confirm
            break

        if progress > params.cd_max_ext + params.fib_tolerance:
            label, reason, t_event = 0, "overextension", i - candidate.c_confirm
            break
    # dongu hicbir break olmadan bitti -> timeout (label=None, reason="timeout")

    cand_label = CandidateLabel(candidate=candidate, label=label, reason=reason, t_event=t_event)
    observations = [
        BucketObservation(is_long=candidate.is_long, bucket_index=bidx, outcome=label)
        for _bar, prog in bars_walked
        for bidx in [_bucket_index(prog)]
        if bidx is not None
    ]
    return cand_label, observations


def analyze_series(
    df: pd.DataFrame, params: Params, t_max: int
) -> tuple[list[CandidateLabel], list[BucketObservation]]:
    """Bir sembol/tf'in TAM serisi icin `find_abc_candidates` + ileri-
    taramali uc-cikisli etiketleme + bar-seviyeli kova gozlemlerini
    doner. `df` kolonlari en az [high, low, close] icermelidir."""
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    pivots = _ordered_pivots(high, low, params.pivot_lookback)
    pairs = _build_candidates(pivots, params)

    n = len(df)
    labels: list[CandidateLabel] = []
    observations: list[BucketObservation] = []
    for candidate, next_pivot in pairs:
        cand_label, obs = _label_one(candidate, next_pivot, close, n, params, t_max)
        labels.append(cand_label)
        observations.extend(obs)
    return labels, observations


# ── T_max (timeout esigi) ────────────────────────────────────────────────


def compute_t_max(signals: list[Signal], percentile: float = 95.0, floor: int = T_MAX_FLOOR_BARS) -> int:
    """Timeout esigi: onaylanmis TUM ABCD sinyallerinin (`d_bar - c_bar`
    suresi -- `c_confirm`den `d_confirm`e gecen sure ile AYNI, ikisi de
    `+pivot_lookback` oteler) dagiliminin p'inci persentili, evren
    genelinde ampirik belirlenir (bkz. gorev talimati madde 2, "Timeout").

    Sinyal yoksa (bkz. bos evren/veri) `floor` doner -- hicbir zaman 0
    ya da negatif bir pencere URETILMEZ.
    """
    if not signals:
        return floor
    durations = [s.d_bar - s.c_bar for s in signals]
    value = float(np.percentile(durations, percentile))
    return max(int(round(value)), floor)


# ── kova tablosu (Wilson %95 GA) ─────────────────────────────────────────


def build_bucket_table(observations: list[BucketObservation]) -> pd.DataFrame:
    """cd_progress kovalari x yon (LONG/SHORT) hucrelerinde HAM frekans +
    Wilson skoru %95 guven araligi (metodoloji madde 3). n<`MIN_TRUSTWORTHY_N`
    olan hucreler ASLA gizlenmez, `guven_etiketi` sutununda acikca
    "GUVENSIZ (n=X)" etiketlenir -- `abcd_backtest.py::run_grid`nin AYNI
    disiplini.

    Timeout gozlemleri (`outcome is None`) `n_toplam`/`oran`a DAHIL
    EDILMEZ (nihai sonuc belirsiz) -- ayri `n_timeout` sutununda
    raporlanir.
    """
    rows: list[dict] = []
    for is_long in (True, False):
        direction = "LONG" if is_long else "SHORT"
        for bidx, blabel in enumerate(BUCKET_LABELS):
            cell = [o for o in observations if o.is_long == is_long and o.bucket_index == bidx]
            resolved = [o for o in cell if o.outcome is not None]
            n_total = len(resolved)
            n_success = sum(1 for o in resolved if o.outcome == 1)
            n_timeout = len(cell) - n_total

            if n_total > 0:
                rate = n_success / n_total
                ci_low, ci_high = proportion_confint(n_success, n_total, alpha=0.05, method="wilson")
                ci_low, ci_high = float(ci_low), float(ci_high)
            else:
                rate, ci_low, ci_high = float("nan"), float("nan"), float("nan")

            guven_etiketi = f"GUVENSIZ (n={n_total})" if n_total < MIN_TRUSTWORTHY_N else "GUVENILIR"

            rows.append(
                {
                    "direction": direction,
                    "bucket": blabel,
                    "bucket_index": bidx,
                    "n_basari": n_success,
                    "n_toplam": n_total,
                    "oran": rate,
                    "wilson_ci_low": ci_low,
                    "wilson_ci_high": ci_high,
                    "n_timeout": n_timeout,
                    "guven_etiketi": guven_etiketi,
                }
            )
    return pd.DataFrame(rows)


# ── null-hipotez (GBM rastgele yuruyus) karsilastirmasi ──────────────────


def estimate_log_return_std(close: np.ndarray) -> float:
    """Gerceklesmis (log-getiri) volatilite tahmini -- GBM'in kalibrasyon
    girdisi (metodoloji madde 4)."""
    arr = np.asarray(close, dtype=float)
    arr = arr[arr > 0]
    if len(arr) < 2:
        return 0.0
    log_returns = np.diff(np.log(arr))
    if len(log_returns) < 2:
        return 0.0
    return float(np.std(log_returns, ddof=1))


def generate_gbm_series(
    n_bars: int,
    log_return_std: float,
    seed: int,
    start_price: float = 100.0,
    drift: float = 0.0,
    freq: str = "1D",
) -> pd.DataFrame:
    """Gerceklesmis volatiliteye kalibre edilmis basit bir GBM sentetik
    seri -- null-hipotez karsilastirmasinin (metodoloji madde 4) girdisi.
    Sifir drift VARSAYILAN (trend'in kendisini degil, ABC->D tamamlanma
    frekansinin SALT rastgele yuruyustekinden farkli olup olmadigini test
    etmek istiyoruz).

    High/low, GBM'in tanimladigi close etrafinda kucuk bir gurultu ile
    yaklaşiklanir -- pivot tespiti (sadece yerel ekstremumlara ihtiyac
    duyar) icin yeterlidir, gercekci gun-ici mikroyapi iddiasi DEGILDIR.
    Deterministik (ayni `seed` -> ayni seri) -- testte/CLI'de tekrarlanabilir.
    """
    if n_bars <= 0:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    rng = np.random.default_rng(seed)
    log_returns = rng.normal(loc=drift, scale=max(log_return_std, 1e-12), size=n_bars)
    log_path = np.cumsum(log_returns)
    close = start_price * np.exp(log_path)

    open_ = np.empty(n_bars)
    open_[0] = start_price
    open_[1:] = close[:-1]

    noise = np.abs(rng.normal(loc=0.0, scale=max(log_return_std, 1e-12), size=n_bars)) * close
    high = np.maximum(open_, close) + noise
    low = np.minimum(open_, close) - noise
    low = np.maximum(low, 1e-6)  # negatif/sifir fiyat KORUNMAZ

    return pd.DataFrame(
        {
            "time": pd.date_range("2000-01-01", periods=n_bars, freq=freq, tz="UTC"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(n_bars, 1_000_000.0),
        }
    )


def compare_to_null(
    real_table: pd.DataFrame,
    null_table: pd.DataFrame,
    min_n: int = MIN_TRUSTWORTHY_N,
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Her (direction, bucket) hucresi icin gercek vs null (GBM) tamamlanma
    oranini iki-oranli z-testiyle (`statsmodels.stats.proportion.
    proportions_ztest`) karsilastirir (metodoloji madde 4, ZORUNLU adim).

    SADECE her iki tabloda da `n_toplam >= min_n` olan hucreler test
    edilir; `n_hucre_test_edilen`e gore Bonferroni-tipi bir duzeltme
    uygulanir (`effective_alpha = alpha / n_hucre_test_edilen`) --
    `abcd_backtest.py::run_grid`nin AYNI cok-karsilastirma disiplini.
    `null_karsilastirma` sutunu ZORUNLU rapor diline (metodoloji madde 5)
    dogrudan karsilik gelir: "anlamli farkli" / "nulldan ayirt edilemiyor"
    / "test edilemedi (n<min_n)".
    """
    # suffixes=("", "_null"): gercek tablo sutunlari CIPLAK isimleriyle KALIR
    # (n_toplam, n_basari, oran, ...) -- `format_bucket_sentence` HEM ham
    # `build_bucket_table` ciktisini HEM bu birlesmis karsilastirma satirini
    # degisiklik gerektirmeden kabul edebilsin diye (gercek taraf birincil
    # ilgi alani, null taraf SADECE `_null` ekiyle ayrisir).
    merged = real_table.merge(
        null_table, on=["direction", "bucket", "bucket_index"], suffixes=("", "_null")
    )

    testable_mask = (merged["n_toplam"] >= min_n) & (merged["n_toplam_null"] >= min_n)
    n_tested = int(testable_mask.sum())
    effective_alpha = (alpha / n_tested) if n_tested > 0 else alpha

    p_values: list[float] = []
    for _, row in merged.iterrows():
        if row["n_toplam"] >= min_n and row["n_toplam_null"] >= min_n:
            count = np.array([row["n_basari"], row["n_basari_null"]])
            nobs = np.array([row["n_toplam"], row["n_toplam_null"]])
            try:
                # Pooled oran her iki hucrede de TAM 0.0 (ya da TAM 1.0)
                # oldugunda pooled std sifir olur -> statsmodels 0/0
                # RuntimeWarning uretir (deger zaten NaN'a duser, YAKALANIR,
                # sadece konsol gurultusu bastirilir -- `abcd_factor_
                # analysis.py::_fit_logistic_regression` ile AYNI ilke).
                with np.errstate(invalid="ignore", divide="ignore"):
                    _stat, p = proportions_ztest(count, nobs)
                p = float(p)
            except (ValueError, ZeroDivisionError):
                p = float("nan")
        else:
            p = float("nan")
        p_values.append(p)

    merged["p_value"] = p_values
    merged["n_hucre_test_edilen"] = n_tested
    merged["effective_alpha"] = effective_alpha

    def _verdict(p: float) -> str:
        if math.isnan(p):
            return f"test edilemedi (n<{min_n})"
        return "anlamli farkli" if p < effective_alpha else "nulldan ayirt edilemiyor"

    merged["null_karsilastirma"] = merged["p_value"].apply(_verdict)
    return merged


# ── rapor dili yardimcisi (metodoloji madde 5, ZORUNLU format) ───────────


def format_bucket_sentence(row: "pd.Series") -> str:
    """Metodoloji madde 5'in ZORUNLU rapor formatini BIREBIR uretir:
    'Tarihsel bu asamada (... CD ilerlemesi %X-%Y araligindayken) D'ye
    ulasma sikligi: n_basari/n_toplam (%95 GA: ...), null-karsilastirma:
    [...]'. 'olasilik' kelimesi hicbir zaman KULLANILMAZ."""
    if row["n_toplam"] == 0:
        oran_str = "N/A (bu kovada hic gozlem yok)"
    else:
        oran_str = (
            f"{row['n_basari']}/{row['n_toplam']} "
            f"(%95 GA: {row['wilson_ci_low']:.3f}-{row['wilson_ci_high']:.3f})"
        )
    null_str = row.get("null_karsilastirma", "null-karsilastirma calistirilmadi")
    return (
        f"Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, {row['direction']} yonunde CD "
        f"ilerlemesi {row['bucket']} araligindayken) D'ye ulasma sikligi: {oran_str} [{row['guven_etiketi']}], "
        f"null-karsilastirma: {null_str}."
    )
