"""Çoklu senaryo (Kısa Dönem / Uzun Dönem / Sektör Ortalaması) çarpan
değerlemesi -- SAF matematik, `src.analysis.calculator`/`fundamental_screens`
ile AYNI ilke: HİÇBİR I/O yapmaz, `src.fetchers`/`src.db` import ETMEZ.

Kullanıcının kendi (2026-08-08) tarif ettiği ve paylaştığı referans
görsellerdeki (ASUZU örneği) yöntem: F/K, PD/DD, FD/FAVÖK çarpanlarının
HER biri için üç ayrı ortalama (kısa dönem/uzun dönem/sektör) hesaplanır,
her biri şirketin KENDİ güncel temel değerine (TTM net kâr, güncel
özkaynak, TTM FAVÖK) uygulanarak bir hedef fiyat üretir; üç senaryonun
ortalaması o çarpanın hedef fiyatıdır; üç çarpanın (F/K, PD/DD, FD/FAVÖK)
hedef fiyatlarının ortalaması nihai "A" fiyatıdır.

── BİLİNÇLİ KAPSAM FARKI (Kural 3, açıkça belirtilir) ──
Kullanıcının referans görselinde "Kısa Dönem" 8 çeyrek, "Uzun Dönem" 36
çeyrek (9 yıl) pencere kullanıyordu. Bu projenin fiyat/finansal veri
fetcher'ları (`src.fetchers.isyatirim`) yalnızca ~4 yıl (16 çeyrek) geriye
GÜVENİLİR derinlik sağlıyor (`DEFAULT_HISTORY_QUARTERS=16`,
PROJE_HAFIZASI/01_MIMARI.md'de belgeli sistem sabiti) -- bu modül bu
YÜZDEN "Kısa Dönem" için son 4 çeyrek (1 yıl), "Uzun Dönem" için mevcut
TÜM derinliği (en fazla 16 çeyrek/4 yıl) kullanır. Bu, kullanıcının
yöntemiyle AYNI İLKE (kısa/uzun/sektör üçlemesi + IQR aykırı değer
temizliği) ama VERİ KAYNAĞININ izin verdiği pencereyle sınırlıdır.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# IQR (Çeyrekler Arası Açıklık) yöntemiyle aykırı değer temizliği --
# kullanıcının referans görselindeki aracın KENDİ metodolojisi (k=1.5,
# istatistikte standart Tukey eşiği, bizim tercihimiz DEĞİL).
_IQR_K = Decimal("1.5")

# Bir "ortalama"nin istatistiksel olarak anlamli sayilmasi icin en az kac
# gozlem gerekir -- valuation.py'deki _MIN_PEER_COUNT_FOR_SECTOR_COMPARISON
# ile AYNI ilke (Kural 4: yetersiz veriyle YANILTICI KESINLIK sunulmaz).
_MIN_OBSERVATIONS = 3


@dataclass(frozen=True)
class MultipleScenario:
    label: str  # "Sektör Ortalaması" | "Kısa Dönem Ortalaması (son 1 yıl)" | "Uzun Dönem Ortalaması (mevcut derinlik)"
    multiple: Decimal | None
    sample_size: int
    target_price: Decimal | None


@dataclass(frozen=True)
class MultipleValuation:
    multiple_name: str  # "F/K" | "PD/DD" | "FD/FAVÖK"
    scenarios: list[MultipleScenario]
    blended_target_price: Decimal | None  # gecerli senaryolarin ortalamasi


@dataclass(frozen=True)
class MultiScenarioResult:
    pe: MultipleValuation
    pb: MultipleValuation
    ev_ebitda: MultipleValuation
    final_target_price_a: Decimal | None  # uc carpanin blended_target_price ortalamasi


def _quantile(sorted_values: list[Decimal], q: Decimal) -> Decimal:
    """Doğrusal enterpolasyonla yüzdelik dilim -- ek bir istatistik
    kütüphanesine bağımlı olmamak için (proje zaten hiçbir yerde numpy/
    pandas kullanmıyor, bkz. requirements.txt) elle yazılmıştır."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    pos = q * (n - 1)
    lower_idx = int(pos)
    upper_idx = min(lower_idx + 1, n - 1)
    frac = pos - lower_idx
    return sorted_values[lower_idx] + (sorted_values[upper_idx] - sorted_values[lower_idx]) * frac


def trim_outliers_iqr(values: list[Decimal]) -> list[Decimal]:
    """IQR yöntemiyle (k=1.5) aykırı değerleri çıkarır. <4 gözlemde IQR
    istatistiksel olarak güvenilir olmadığı için değerler OLDUĞU GİBİ
    döner (Kural 3)."""
    positive = sorted(v for v in values if v is not None and v > 0)
    if len(positive) < 4:
        return positive
    q1 = _quantile(positive, Decimal("0.25"))
    q3 = _quantile(positive, Decimal("0.75"))
    iqr = q3 - q1
    lower_bound = q1 - _IQR_K * iqr
    upper_bound = q3 + _IQR_K * iqr
    return [v for v in positive if lower_bound <= v <= upper_bound]


def _average(values: list[Decimal]) -> Decimal | None:
    trimmed = trim_outliers_iqr(values)
    if len(trimmed) < _MIN_OBSERVATIONS:
        return None
    return sum(trimmed) / len(trimmed)


def _build_multiple_valuation(
    multiple_name: str,
    sector_multiples: list[Decimal],
    short_term_multiples: list[Decimal],
    long_term_multiples: list[Decimal],
    own_fundamental: Decimal | None,
    price_from_market_cap: bool,
    share_capital: Decimal | None,
    net_debt: Decimal | None,
) -> MultipleValuation:
    """`own_fundamental`: F/K için TTM net kâr, PD/DD için güncel özkaynak,
    FD/FAVÖK için TTM FAVÖK. `price_from_market_cap=True` (F/K, PD/DD) ise
    hedef fiyat = (çarpan × own_fundamental) / share_capital; FD/FAVÖK'te
    ise önce Kurumsal Değer hedefi (çarpan × FAVÖK) bulunur, net borç
    çıkarılıp Piyasa Değeri'ne çevrilir, SONRA share_capital'e bölünür."""
    scenarios: list[MultipleScenario] = []
    for label, pool in (
        ("Sektör Ortalaması", sector_multiples),
        ("Kısa Dönem Ortalaması (son 1 yıl)", short_term_multiples),
        ("Uzun Dönem Ortalaması (mevcut derinlik)", long_term_multiples),
    ):
        avg_multiple = _average(pool)
        target_price: Decimal | None = None
        # own_fundamental (TTM net kar/FAVOK) negatifse (zarar eden sirket)
        # pozitif bir carpanla carpip "hedef fiyat" uretmek MATEMATIKSEL
        # olarak anlamsizdir (negatif/yaniltici bir sayi -- CANLI bulundu,
        # KORDS'ta zarar TTM net kariyla -120,98 TL gibi negatif bir "hedef
        # fiyat" cikti) -- Kural 3 geregi bu durumda hedef None birakilir.
        if (
            avg_multiple is not None
            and own_fundamental is not None
            and own_fundamental > 0
            and share_capital is not None
            and share_capital > 0
        ):
            if price_from_market_cap:
                implied_market_cap = avg_multiple * own_fundamental
                target_price = implied_market_cap / share_capital
            else:
                implied_enterprise_value = avg_multiple * own_fundamental
                implied_market_cap = implied_enterprise_value - (net_debt or Decimal(0))
                if implied_market_cap > 0:
                    target_price = implied_market_cap / share_capital
        scenarios.append(
            MultipleScenario(
                label=label,
                multiple=avg_multiple,
                sample_size=len(trim_outliers_iqr(pool)),
                target_price=target_price,
            )
        )

    valid_targets = [s.target_price for s in scenarios if s.target_price is not None]
    blended = sum(valid_targets) / len(valid_targets) if valid_targets else None
    return MultipleValuation(multiple_name=multiple_name, scenarios=scenarios, blended_target_price=blended)


def compute_multi_scenario_valuation(
    *,
    sector_pe: list[Decimal],
    sector_pb: list[Decimal],
    sector_ev_ebitda: list[Decimal],
    short_term_pe: list[Decimal],
    short_term_pb: list[Decimal],
    short_term_ev_ebitda: list[Decimal],
    long_term_pe: list[Decimal],
    long_term_pb: list[Decimal],
    long_term_ev_ebitda: list[Decimal],
    ttm_net_income: Decimal | None,
    current_equity: Decimal | None,
    ttm_ebitda: Decimal | None,
    share_capital: Decimal | None,
    net_debt: Decimal | None,
) -> MultiScenarioResult:
    """Bkz. modül üst notu. Tüm `list[Decimal]` girdiler ÇAĞIRAN TARAFIN
    (scripts/batch_report_2026Q2.py) zaten topladığı HAM (henüz IQR
    temizlenmemiş) çarpan gözlemleridir -- temizlik burada yapılır."""
    pe = _build_multiple_valuation(
        "F/K", sector_pe, short_term_pe, long_term_pe, ttm_net_income, True, share_capital, None
    )
    pb = _build_multiple_valuation(
        "PD/DD", sector_pb, short_term_pb, long_term_pb, current_equity, True, share_capital, None
    )
    ev_ebitda = _build_multiple_valuation(
        "FD/FAVÖK", sector_ev_ebitda, short_term_ev_ebitda, long_term_ev_ebitda, ttm_ebitda, False, share_capital, net_debt
    )

    blended_targets = [v.blended_target_price for v in (pe, pb, ev_ebitda) if v.blended_target_price is not None]
    final_target_price_a = sum(blended_targets) / len(blended_targets) if blended_targets else None

    return MultiScenarioResult(pe=pe, pb=pb, ev_ebitda=ev_ebitda, final_target_price_a=final_target_price_a)
