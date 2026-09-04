"""Çift (pair) keşfi — statik bir ekran/tarama, indikatör DEĞİLDİR.

Verilen bir sembol listesinde (varsayılan: aynı sektör) TÜM ikili kombinasyonları
tarar; korelasyon + Engle-Granger eşbütünleşme testi + yarı ömür (halflife)
eşiklerinden geçenleri "aday çift" olarak raporlar.

**KRİTİK DİSİPLİN NOTU (bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md,
DISIPLIN-06):** `find_cointegrated_pairs` benzeri bir tarama, backtest ile
AYNI zaman penceresinde yapılırsa bu bir SEÇİM ÖNYARGISI (selection
look-ahead) türüdür — "bu çift eşbütünleşikti" iddiası kısmen gelecek
bilgisiyle kirlenmiş olur. Bu modülün çıktısı bu yüzden KALICI BİR ONAY
DEĞİL, yalnızca ANLIK BİR TARAMA sonucudur — periyodik olarak yeniden
koşulmalı ve `RelativeMomentumPair`'in kendi sinyal penceresiyle KARIŞTIRIL-
MAMALIDIR. `oos_split` parametresi (Faz 2, 2B) bu disiplini KISMEN motora
gömer: çift SEÇİMİ ilk yarıda yapılır, ikinci yarıda YENİDEN doğrulanır.

**Faz 2, 2B (2026-09-04, docs/TANI_VE_YOL_HARITASI_v2.md bölüm 1.4)
DÜZELTMESİ — "606 sahte çift" bulgusu:** eski sürüm ham `adf_pvalue`
kullanıyordu (TAHMİN EDİLMİŞ bir OLS kalıntısına uygulanan ham ADF, nominal
%5 yerine %14-18 reddediyordu — bkz. `tlab/features/stats.py::adf_pvalue`
UYARISI) VE iki yönü (`Y~X`/`X~Y`) deneyip düşük p'yi alıyordu (efektif
α≈0.0975, düzeltilmemiş) VE hiçbir çoklu-test düzeltmesi yapmıyordu (8754
aynı-sektör kombinasyonu, nominal %5'te BEKLENEN ~438 yanlış-pozitif —
gerçek 606 bulgusunun yarısından fazlası GÜRÜLTÜ). Üç düzeltme: (1)
`engle_granger_pvalue` (MacKinnon kritik değerleri); (2) Šidák düzeltmesi
(`p_cift = 1-(1-min(p1,p2))^2`); (3) opsiyonel Benjamini-Hochberg FDR
(`fdr_q`) TÜM taranan kombinasyon sayısı (`n_tests`) üzerinden."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlab.features.stats import (
    benjamini_hochberg,
    engle_granger_pvalue,
    halflife,
    ols_spread,
    rolling_beta,
)


@dataclass(frozen=True)
class PairCandidate:
    symbol_y: str
    symbol_x: str
    corr: float
    adf_pvalue: float  # Faz 2, 2B'den beri: p_adjusted (Šidák-düzeltilmiş) -- kayıtlı sözleşme
    halflife: float
    beta: float
    n_bars: int
    # Faz 2, 2B -- YENİ alanlar (varsayılanlar geriye dönük uyumluluk için)
    p_raw: float = float("nan")  # min(p_yx, p_xy), Šidák ÖNCESİ
    p_adjusted: float = float("nan")  # adf_pvalue ile AYNI değer, açıkça adlandırılmış
    n_tests: int = 0  # bu tarama koşusunda denenen TOPLAM kombinasyon sayısı (FDR'nin M'si)
    fdr_passed: bool | None = None  # fdr_q=None iken None (değerlendirilmedi)
    adf_p_is: float | None = None  # oos_split verildiyse: ilk yarı (in-sample) p'si
    adf_p_oos: float | None = None  # oos_split verildiyse: ikinci yarı (out-of-sample) p'si


@dataclass(frozen=True)
class _Attempt:
    """İç kullanım: bir (sym_a, sym_b) kombinasyonu için TAM değerlendirme
    sonucu -- eşikleri geçip geçmediğinden BAĞIMSIZ, `n_tests`/FDR havuzuna
    girecek HER kombinasyon için üretilir."""

    sym_y: str
    sym_x: str
    corr: float
    p_raw: float
    p_adjusted: float
    halflife: float
    beta: float
    n_bars: int
    adf_p_is: float | None
    adf_p_oos: float | None
    passes_corr_halflife: bool


def _single_beta(y_log: pd.Series, x_log: pd.Series) -> float:
    """Tüm hizalanmış pencere üzerinden TEK (sabit) OLS beta — discovery bir
    anlık tarama olduğu için rolling'e gerek yok, tüm pencere kullanılabilir."""
    window = len(y_log)
    beta_series = rolling_beta(y_log, x_log, window)
    value = beta_series.iloc[-1]
    return float(value) if not pd.isna(value) else float("nan")


def _sidak(p_raw: float) -> float:
    """İki yönün (Y~X, X~Y) MİNİMUMUNU seçmenin şişirdiği alfa'yı düzeltir:
    p_cift = 1 - (1-p_raw)^2 -- iki bağımsız denemeden EN AZ BİRİNİN p_raw
    kadar aşırı olma olasılığı (Šidák, bağımsızlık varsayımıyla; iki yön
    TAM bağımsız değildir ama pozitif bağımlılık altında Šidák hâlâ
    KONSERVATİF bir üst sınırdır -- bkz. Faz 2 tanısı bölüm 1.4c)."""
    return 1.0 - (1.0 - p_raw) ** 2


def _pair_pvalue(y: pd.Series, x: pd.Series) -> tuple[str, str, float, float] | None:
    """İki yönü de dener (Y~X, X~Y), (kazanan_y, kazanan_x, p_raw, p_adjusted)
    döner -- p_raw = min(p_yx, p_xy), p_adjusted = Šidák düzeltmesi."""
    try:
        p_yx = engle_granger_pvalue(y, x)
        p_xy = engle_granger_pvalue(x, y)
    except ValueError:
        return None
    if p_yx <= p_xy:
        return "y_as_y", "x_as_x", p_yx, _sidak(p_yx)
    return "x_as_y", "y_as_x", p_xy, _sidak(p_xy)


def _corr_beta_halflife(
    y: pd.Series, x: pd.Series,
) -> tuple[float, float, float] | None:
    """`corr`, `beta`, `halflife` -- Faz 2, 2A'nın `ols_spread`i (intercept'li,
    bkz. tanı bulgusu (e)) kullanır."""
    y_log = np.log(y.where(y > 0))
    x_log = np.log(x.where(x > 0))
    if y_log.isna().any() or x_log.isna().any():
        return None
    corr = float(y_log.corr(x_log))
    beta = _single_beta(y_log, x_log)
    if math.isnan(beta):
        return None
    try:
        spread, _alpha, _beta_ols = ols_spread(y, x)
    except ValueError:
        return None
    try:
        hl = halflife(spread)
    except ValueError:
        return None
    return corr, beta, hl


def _evaluate_combo(
    sym_a: str, sym_b: str, a_raw: pd.Series, b_raw: pd.Series,
    corr_min: float, halflife_range: tuple[float, float], min_overlap_bars: int,
    oos_split: float | None,
) -> _Attempt | None:
    common = a_raw.index.intersection(b_raw.index)
    if len(common) < min_overlap_bars:
        return None
    a = a_raw.loc[common].astype(float)
    b = b_raw.loc[common].astype(float)
    if (a <= 0).any() or (b <= 0).any():
        return None

    if oos_split is not None:
        split_at = int(len(common) * oos_split)
        if split_at < min_overlap_bars or (len(common) - split_at) < min_overlap_bars:
            return None  # her iki yarı da min_overlap_bars'ı karşılamalı
        sel_common = common[:split_at]
        oos_common = common[split_at:]
    else:
        sel_common = common
        oos_common = None

    a_sel, b_sel = a.loc[sel_common], b.loc[sel_common]
    winner = _pair_pvalue(a_sel, b_sel)
    if winner is None:
        return None
    which_y, _which_x, p_raw, p_adjusted = winner
    sym_y, sym_x = (sym_a, sym_b) if which_y == "y_as_y" else (sym_b, sym_a)
    y_sel = a_sel if which_y == "y_as_y" else b_sel
    x_sel = b_sel if which_y == "y_as_y" else a_sel

    stats = _corr_beta_halflife(y_sel, x_sel)
    if stats is None:
        return None
    corr, beta, hl = stats
    passes = corr >= corr_min and halflife_range[0] <= hl <= halflife_range[1]

    adf_p_is: float | None = None
    adf_p_oos: float | None = None
    if oos_split is not None:
        adf_p_is = p_adjusted
        assert oos_common is not None
        y_oos = a.loc[oos_common] if which_y == "y_as_y" else b.loc[oos_common]
        x_oos = b.loc[oos_common] if which_y == "y_as_y" else a.loc[oos_common]
        try:
            adf_p_oos = engle_granger_pvalue(y_oos, x_oos)
        except ValueError:
            adf_p_oos = float("nan")
            passes = False

    return _Attempt(
        sym_y=sym_y, sym_x=sym_x, corr=corr, p_raw=p_raw, p_adjusted=p_adjusted,
        halflife=hl, beta=beta, n_bars=len(sel_common),
        adf_p_is=adf_p_is, adf_p_oos=adf_p_oos, passes_corr_halflife=passes,
    )


def _is_eligible_combo(
    sym_a: str, sym_b: str, sector_map: dict[str, str] | None,
    economic_link_map: dict[str, set[str]] | None,
) -> bool:
    """`same_sector_only=True` iken bir kombinasyonun taranıp
    TARANMAYACAĞINA karar verir -- aynı sektörse VEYA `economic_link_map`
    (Faz 2, 2B: holding-iştirak/aynı emtia/aynı endeks gibi sektör
    haritasının kaçırdığı bağlar) eşleşiyorsa uygun."""
    sector_a = (sector_map or {}).get(sym_a)
    sector_b = (sector_map or {}).get(sym_b)
    if sector_a is not None and sector_b is not None and sector_a == sector_b:
        return True
    if economic_link_map is not None:
        linked_a = economic_link_map.get(sym_a, set())
        linked_b = economic_link_map.get(sym_b, set())
        if sym_b in linked_a or sym_a in linked_b:
            return True
    return False


def discover_pairs(
    prices: dict[str, pd.Series],
    corr_min: float = 0.7,
    adf_max: float = 0.05,
    halflife_range: tuple[float, float] = (5.0, 60.0),
    min_overlap_bars: int = 120,
    sector_map: dict[str, str] | None = None,
    same_sector_only: bool = True,
    fdr_q: float | None = 0.05,
    oos_split: float | None = 0.5,
    economic_link_map: dict[str, set[str]] | None = None,
) -> list[PairCandidate]:
    """`prices`: sembol -> kapanış fiyatı Series (index datetime, hizalanmamış
    olabilir — her çift kendi içinde inner-join ile hizalanır).

    `sector_map` verilmezse VEYA bir sembol map'te YOKSA (bilinmeyen sektör),
    o sembol `same_sector_only=True` iken (VE `economic_link_map`'te de
    eşleşmiyorsa) taramaya DAHİL EDİLMEZ (varsayılan sektöre atanarak
    uydurulmaz) — bkz. modül docstring'i, "bilmediğin sektörü uydurma"
    ilkesi.

    `fdr_q` (Faz 2, 2B, varsayılan 0.05): verilirse, TÜM denenen kombinasyon
    sayısı (`n_tests`, corr/halflife eşiklerinden BAĞIMSIZ -- Faz 2 tanısının
    referans ölçümüyle AYNI M) üzerinden Benjamini-Hochberg FDR uygulanır;
    yalnızca hem eşikleri geçen HEM FDR'den geçen çiftler döner. `None`
    verilirse düzeltme yapılmaz (eski davranış, karşılaştırma için).

    `oos_split` (Faz 2, 2B, varsayılan 0.5): verilirse örneklem ikiye
    bölünür (ilk `oos_split` payı = in-sample), çift SEÇİMİ (yön + p_raw/
    p_adjusted + corr/halflife) yalnızca in-sample'da yapılır, kointegrasyon
    out-of-sample'da (SEÇİLEN yönle) YENİDEN test edilir -- ikisi de
    `adf_max`'ı geçmezse aday elenir. `None` verilirse tüm örneklem tek
    pencere olarak kullanılır (eski davranış).

    `economic_link_map` (Faz 2, 2B): `same_sector_only=True` olsa bile bu
    haritada (sembol -> {eşleştiği semboller}) eşleşen çiftler taramaya
    DAHİL edilir — sektör haritasının kaçırdığı ekonomik bağlar için
    (bkz. `config/economic_links.yaml`).

    **SEKTÖR MU TÜM EVREN Mİ — KARAR VE GEREKÇE (Faz 2, 2B):** `same_
    sector_only=True` VARSAYILAN olarak KALIYOR, iki bağımsız gerekçeyle:
    (a) Do & Faff (2010), Gatev-Goetzmann-Rouwenhorst'u 1962-2009'a
    genişleterek getirilerin sektör-içi çiftlerde EN YÜKSEK olduğunu, daha
    ince sektör sınıflandırmasının performansı DAHA DA artırdığını
    gösteriyor — aynı sektördeki iki hisse birbirinin gerçek ikamesi
    olduğu için yakınsama olasılığı yüksek. (b) İstatistiksel: BİST 648
    sembolde TÜM evren 209.628 çift, sektör-içi yalnızca 8.754 — çoklu-test
    yükü 24 KAT düşüyor, AYNI FDR seviyesinde sektör-içi tarama DAHA FAZLA
    gerçek çift bulur (bkz. Faz 2 tanısı bölüm 1.4g). `same_sector_only=
    False` (tüm evren) bir SEÇENEK olarak kalıyor ama o modda `fdr_q`
    ZORUNLUDUR (`None` verilirse `ValueError`) — 209.628 kombinasyonluk bir
    aramada FDR düzeltmesi OLMADAN sonuç güvenilmezdir."""
    if not same_sector_only and fdr_q is None:
        raise ValueError(
            "same_sector_only=False (tüm evren taraması) iken fdr_q ZORUNLUDUR "
            "-- 200 binin üzerinde kombinasyonda düzeltmesiz p-değeri güvenilmez "
            "(bkz. discover_pairs docstring'i, 'SEKTÖR MU TÜM EVREN Mİ')"
        )
    symbols = sorted(prices.keys())
    attempts: list[_Attempt] = []

    for sym_a, sym_b in itertools.combinations(symbols, 2):
        if same_sector_only and not _is_eligible_combo(
            sym_a, sym_b, sector_map, economic_link_map
        ):
            continue
        attempt = _evaluate_combo(
            sym_a, sym_b, prices[sym_a], prices[sym_b],
            corr_min, halflife_range, min_overlap_bars, oos_split,
        )
        if attempt is not None:
            attempts.append(attempt)

    n_tests = len(attempts)
    if fdr_q is not None and attempts:
        fdr_result = benjamini_hochberg([a.p_adjusted for a in attempts], fdr_q)
    else:
        fdr_result = np.ones(len(attempts), dtype=bool)

    candidates: list[PairCandidate] = []
    for attempt, fdr_ok in zip(attempts, fdr_result, strict=True):
        if not attempt.passes_corr_halflife:
            continue
        if attempt.p_adjusted >= adf_max:
            continue
        if attempt.adf_p_oos is not None and (
            math.isnan(attempt.adf_p_oos) or attempt.adf_p_oos >= adf_max
        ):
            continue
        if fdr_q is not None and not bool(fdr_ok):
            continue
        candidates.append(
            PairCandidate(
                symbol_y=attempt.sym_y, symbol_x=attempt.sym_x, corr=attempt.corr,
                adf_pvalue=attempt.p_adjusted, halflife=attempt.halflife,
                beta=attempt.beta, n_bars=attempt.n_bars,
                p_raw=attempt.p_raw, p_adjusted=attempt.p_adjusted, n_tests=n_tests,
                fdr_passed=bool(fdr_ok) if fdr_q is not None else None,
                adf_p_is=attempt.adf_p_is, adf_p_oos=attempt.adf_p_oos,
            )
        )

    return sorted(candidates, key=lambda c: c.adf_pvalue)


def load_sector_map(path: str) -> dict[str, str]:
    """config/sectors_bist.yaml'ı okur: {sembol: sektor} düz sözlüğü döner.
    YAML'da sembol -> sektör YOKSA (dosyada geçmiyorsa) bu sembol map'te hiç
    bulunmaz — discover_pairs bunu 'bilinmeyen sektör' sayıp dışlar."""
    import yaml

    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    mapping: dict[str, str] = {}
    for sector, symbols in raw.get("sectors", {}).items():
        for sym in symbols or []:
            mapping[sym] = sector
    return mapping


def load_economic_link_map(path: str) -> dict[str, set[str]]:
    """`config/economic_links.yaml`'ı okur: {sembol: {eşleştiği semboller}}
    döner. YAML formatı: `links:` altında her biri bir sembol listesi olan
    gruplar (aynı grup içindeki HER sembol birbirine bağlı sayılır) --
    `config/sectors_bist.yaml`'ın aksine BOŞ bir dosya/dosya YOKLUĞU
    tamamen geçerlidir (boş sözlük döner, discover_pairs `same_sector_only`
    davranışını hiç DEĞİŞTİRMEZ)."""
    from pathlib import Path

    import yaml

    p = Path(path)
    if not p.exists():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    mapping: dict[str, set[str]] = {}
    for group in raw.get("links", []):
        symbols = list(group or [])
        for sym in symbols:
            mapping.setdefault(sym, set()).update(s for s in symbols if s != sym)
    return mapping


def load_pairs_yaml(path: str = "config/pairs.yaml") -> list[tuple[str, str]]:
    """config/pairs.yaml'daki elle seçilmiş (y,x) çift listesini okur.

    2026-09-03: bu fonksiyon eskiden yalnızca `tlab/cli.py` içinde ÖZEL
    (`_load_pairs_yaml`) tanımlıydı — web backend'in tarama tetikleyicisi
    (`web/backend/routes/scan_trigger.py`) bunu hiç çağırmadığı için
    `run_eod(pairs=None)` (→ boş liste) ile koşuyordu, bu yüzden web'den
    başlatılan taramalarda `pair.*` göstergeleri HİÇ sinyal üretmiyordu
    (gerçek kullanıcı bulgusu). Ortak kaynağa taşındı, hem CLI hem web
    AYNI fonksiyonu çağırır."""
    from pathlib import Path

    import yaml

    p = Path(path)
    if not p.exists():
        return []
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return [(entry["y"], entry["x"]) for entry in raw.get("pairs", [])]


def format_report(candidates: list[PairCandidate]) -> str:
    if not candidates:
        return "Aday çift bulunamadı (eşikleri gevşetmeyi veya evreni genişletmeyi düşünün)."
    lines = [
        f"{'Y':<8} {'X':<8} {'corr':>7} {'adf_p':>8} {'halflife':>9} {'beta':>8} {'bar':>6}",
        "-" * 58,
    ]
    for c in candidates:
        lines.append(
            f"{c.symbol_y:<8} {c.symbol_x:<8} {c.corr:>7.3f} {c.adf_pvalue:>8.4f} "
            f"{c.halflife:>9.1f} {c.beta:>8.3f} {c.n_bars:>6}"
        )
    return "\n".join(lines)
