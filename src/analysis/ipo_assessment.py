"""Halka arz izahname rakamlarından (`src.fetchers.kap_ipo.IpoFacts`) türetilmiş
metrikler -- Faz 20 devamı (2026-08-06). `calculator.py`/`trends.py` ile AYNI
ilke: SAF matematik, hiçbir I/O yapmaz, Decimal girer Decimal çıkar (Kural 1/2).

Burada üretilen HİÇBİR alan bir "iyi/kötü" YARGISI değildir -- sadece
izahnamenin KENDİ rakamlarından (Kural 3: uydurma yok) deterministik biçimde
türetilmiş oranlar/sınıflandırmalardır (örn. "arzın ne kadarı sermaye artırımı",
"tahsisatın ne kadarı bireysele ayrılmış"). Yorum/değerlendirme metni (varsa)
render katmanında BU rakamlar okunarak yazılır, burada ÜRETİLMEZ.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

from src.fetchers.kap_ipo import IpoFacts

_HUNDRED = Decimal(100)
_ONE = Decimal(1)
_PURE_CAPITAL_INCREASE_THRESHOLD_PCT = Decimal("99.5")

# Tahsisat etiketlerini gruplamak için anahtar kelimeler (KARCL/QUICK/BEWEN
# izahnamelerinde CANLI gözlemlenen tipik gruplar, bkz. kap_ipo.py fixture'ları).
# Sıra ÖNEMLİ: "Yurt Dışı Kurumsal" ve "Yüksek Talep" önce kontrol edilir,
# yoksa "Kurumsal" tek başına "Yurt İçi Kurumsal"ı da yakalar. "Yüksek Talep"
# (KARCL'daki "Yüksek Talepte Bulunacak Yatırımcı Grubu" gibi) ÖNCEDEN "diğer"e
# düşüyordu -- referans görselin ayrı bir "Yüksek Başvurulu Yatırımcı" satırı
# istemesi üzerine KENDİ grubuna ayrıldı (2026-08-07).
_ALLOCATION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("foreign_institutional", ("yurt dışı", "yurtdışı")),
    ("high_demand", ("yüksek",)),
    ("retail", ("bireysel",)),
    ("domestic_institutional", ("kurumsal",)),
)

# Halka arz katılımcı sayısına göre "tahmini dağıtım" senaryo tablosu (referans
# görseldeki gibi) -- BUNLAR GERÇEK bir tahmin/öngörü DEĞİLDİR, sadece "eğer bu
# kadar kişi başvurursa kişi başına kaç lot düşer" sorusuna SAF bölme ile cevap
# veren varsayımsal senaryolardır (Kural 1: LLM'e hesaplattırılmaz, burada SAF
# Decimal matematiği). Eşit dağıtım grubu (bireysel) TAM SAYI lot dağıtır --
# kalan kesirli lot bölüşülemediği için ROUND_FLOOR kullanılır (referans
# görseldeki 14.600.000/500.000=29,2 -> 29 lot ile BİREBİR eşleşti).
#
# Kullanıcı isteği (2026-08-07, üçüncü tur): 150 Bin/2,2 Milyon gibi "tuhaf"
# (yuvarlak olmayan) katılımcı sayıları "saçma kaçıyor" -- SADECE 300 Bin'den
# 1 Milyon'a, 100 Bin'lik adımlarla yuvarlak senaryolar istendi.
_DISTRIBUTION_SCENARIO_PARTICIPANTS: tuple[int, ...] = (
    300_000, 400_000, 500_000, 600_000, 700_000, 800_000, 900_000, 1_000_000,
)


@dataclass(frozen=True)
class IpoAssessment:
    capital_increase_share_pct: Decimal | None
    partner_sale_share_pct: Decimal | None
    is_pure_capital_increase: bool

    allocation_retail_pct: Decimal | None
    allocation_domestic_institutional_pct: Decimal | None
    allocation_foreign_institutional_pct: Decimal | None
    allocation_high_demand_pct: Decimal | None
    allocation_other_pct: Decimal | None

    top_use_of_proceeds: tuple[tuple[str, Decimal], ...] | None

    price_to_book_before: Decimal | None
    equity_growth_pct: Decimal | None

    # --- Lot bazlı büyüklükler (2026-08-07, referans görsel isteği) ---
    # Kaynağı SADECE izahnamenin KENDİ rakamları (offering_size ÷ offering_price
    # -- "1 lot = 1 TL nominal pay" konvansiyonu, Çitlekçi referansıyla CANLI
    # doğrulandı: 36.500.000 lot × 73,70 TL = 2.690.050.000 TL). Talep toplama
    # tarihi/yüksek başvuru şartının KESİN eşiği/katılım endeksi uygunluğu KAP'ın
    # AYRI yayınladığı "Tasarruf Sahiplerine Satış Duyurusu" belgesinde yer alıyor
    # -- bu belge canlı test edilen 3/3 örnekte (VEYAS/CITAS/BEWEN) taranmış
    # görüntüden oluşuyor, metin katmanı yok (OCR gerekir) -- Kural 3 gereği
    # BURADA üretilmez, render katmanı bu alanları "Açıklanacak" gösterir.
    total_lot_count: Decimal | None
    allocation_retail_lot_count: Decimal | None
    allocation_domestic_institutional_lot_count: Decimal | None
    allocation_foreign_institutional_lot_count: Decimal | None
    allocation_high_demand_lot_count: Decimal | None
    allocation_other_lot_count: Decimal | None
    # (katılımcı_sayısı, kişi_başı_lot, kişi_başı_TL) -- SADECE yurt içi bireysel
    # (eşit dağıtım) grubu için anlamlıdır, oransal dağıtılan gruplar için HESAPLANMAZ.
    estimated_retail_distribution: tuple[tuple[int, Decimal, Decimal], ...] | None


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return (numerator / denominator) * _HUNDRED


def _capital_increase_share(facts: IpoFacts) -> tuple[Decimal | None, Decimal | None, bool]:
    """Arzın ne kadarı YENİ sermaye (şirketin kasasına giren), ne kadarı
    mevcut ortak satışı -- nominal artış tutarını halka arz fiyatıyla
    ölçeklendirip `offering_size` (arz büyüklüğü, HER ZAMAN arz fiyatı
    üzerinden) ile aynı birime getirir. Girdilerden biri eksikse (Kural 3)
    None döner."""
    if facts.capital_increase_amount is None or facts.offering_price is None or facts.offering_size is None:
        return None, None, False
    if facts.offering_size == 0:
        return None, None, False

    capital_increase_value = facts.capital_increase_amount * facts.offering_price
    share_pct = _pct(capital_increase_value, facts.offering_size)
    if share_pct is None:
        return None, None, False
    # arz büyüklüğü ile nominal x fiyat tam örtüşmeyebilir (yuvarlama/ayrı
    # bileşenler) -- %100'ü aşarsa güvenli tavana kırpılır, negatif olamaz.
    share_pct = min(share_pct, _HUNDRED)
    partner_pct = _HUNDRED - share_pct
    is_pure = share_pct >= _PURE_CAPITAL_INCREASE_THRESHOLD_PCT
    return share_pct, partner_pct, is_pure


def _classify_allocation(
    breakdown: dict[str, Decimal] | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, Decimal | None, Decimal | None]:
    """Tahsisat kırılımını (dict[etiket, yüzde]) 4 bilinen gruba +
    "diğer"e toplar. `breakdown` None ise (izahnameden ayrıştırılamadıysa)
    beş alan da None döner -- Kural 3."""
    if breakdown is None:
        return None, None, None, None, None

    retail = Decimal(0)
    domestic_inst = Decimal(0)
    foreign_inst = Decimal(0)
    high_demand = Decimal(0)
    other = Decimal(0)

    for label, pct in breakdown.items():
        label_lower = label.lower()
        matched = False
        for group_key, keywords in _ALLOCATION_GROUPS:
            if any(kw in label_lower for kw in keywords):
                if group_key == "foreign_institutional":
                    foreign_inst += pct
                elif group_key == "high_demand":
                    high_demand += pct
                elif group_key == "retail":
                    retail += pct
                else:
                    domestic_inst += pct
                matched = True
                break
        if not matched:
            other += pct

    return retail, domestic_inst, foreign_inst, high_demand, other


def _total_lot_count(facts: IpoFacts) -> Decimal | None:
    """Toplam lot sayısı = Halka Arz Büyüklüğü ÷ Halka Arz Fiyatı ("1 lot =
    1 TL nominal pay" konvansiyonu -- Çitlekçi referansıyla CANLI doğrulandı:
    2.690.050.000 ÷ 73,70 = 36.500.000, kullanıcının paylaştığı görselle
    BİREBİR eşleşti). Lot sayısı tanım gereği tam sayıdır."""
    if facts.offering_size is None or facts.offering_price is None or facts.offering_price == 0:
        return None
    return (facts.offering_size / facts.offering_price).quantize(_ONE, rounding=ROUND_HALF_UP)


def _lot_count_for_pct(pct: Decimal | None, total_lot_count: Decimal | None) -> Decimal | None:
    if pct is None or total_lot_count is None:
        return None
    return ((pct / _HUNDRED) * total_lot_count).quantize(_ONE, rounding=ROUND_HALF_UP)


def _estimated_retail_distribution(
    retail_lot_count: Decimal | None, offering_price: Decimal | None
) -> tuple[tuple[int, Decimal, Decimal], ...] | None:
    """"N kişi başvurursa kişi başına kaç lot düşer" senaryo tablosu -- SAF
    bölme (Kural 1), bir TAHMİN/ÖNGÖRÜ değil, varsayımsal senaryo. Eşit
    dağıtımda kesirli lot bölüşülemez (ROUND_FLOOR) -- katılımcı sayısı o kadar
    yüksek ki kişi başı 1 lottan az düşüyorsa (bireysel grubun tamamı 1 lota
    bile yetmiyorsa) o senaryo satırı EKLENMEZ (yanıltıcı "0 lot" göstermek
    yerine)."""
    if retail_lot_count is None or offering_price is None:
        return None

    rows: list[tuple[int, Decimal, Decimal]] = []
    for participants in _DISTRIBUTION_SCENARIO_PARTICIPANTS:
        lots_per_person = (retail_lot_count / Decimal(participants)).to_integral_value(rounding=ROUND_FLOOR)
        if lots_per_person < 1:
            continue
        tl_per_person = (lots_per_person * offering_price).quantize(_ONE, rounding=ROUND_HALF_UP)
        rows.append((participants, lots_per_person, tl_per_person))
    return tuple(rows) if rows else None


def estimate_capital_vs_partner_pct(
    capital_increase_lot: Decimal | None, partner_sale_lot: Decimal | None
) -> tuple[Decimal | None, Decimal | None, bool]:
    """`_capital_increase_share()`in DEĞİŞKENİ -- 2026-08-07 (üçüncü tur):
    `ipo_broker_page.py`nin halkarz.com'un "Halka Arz Şekli" bloğundan
    (izahname okunamadığında, VEYAS gibi) doğrudan LOT cinsinden okuduğu
    Sermaye Artırımı/Ortak Satışı rakamlarından aynı yüzdeleri üretir --
    burada fiyat/arz büyüklüğü GEREKMEZ (ikisi de zaten aynı birimde/lot),
    sadece oran alınır. `_capital_increase_share()` ile AYNI eşik/yuvarlama
    kuralları (`_PURE_CAPITAL_INCREASE_THRESHOLD_PCT`) kullanılır."""
    if capital_increase_lot is None or partner_sale_lot is None:
        return None, None, False
    total = capital_increase_lot + partner_sale_lot
    if total == 0:
        return None, None, False
    capital_pct = _pct(capital_increase_lot, total)
    if capital_pct is None:
        return None, None, False
    partner_pct = _HUNDRED - capital_pct
    is_pure = capital_pct >= _PURE_CAPITAL_INCREASE_THRESHOLD_PCT
    return capital_pct, partner_pct, is_pure


def estimate_retail_distribution(
    retail_lot_count: Decimal | None, offering_price: Decimal | None
) -> tuple[tuple[int, Decimal, Decimal], ...] | None:
    """`_estimated_retail_distribution()`in DIŞARIYA AÇIK hali -- 2026-08-07
    (üçüncü tur): `ipo_broker_page.py`nin halkarz.com'dan (ikincil kaynak)
    okuduğu fiyat/lot rakamlarından da AYNI standart senaryo tablosunu
    (`_DISTRIBUTION_SCENARIO_PARTICIPANTS`) üretebilmesi için -- halkarz.com'un
    KENDİ senaryo tablosundaki yuvarlak olmayan katılımcı sayıları (150 Bin,
    2,2 Milyon vb.) kullanıcı tarafından "saçma" bulundu, tüm kartlarda TEK
    bir tutarlı senaryo listesi kullanılması istendi. Mantık KOPYALANMADI,
    sadece dışarı açıldı."""
    return _estimated_retail_distribution(retail_lot_count, offering_price)


def _top_use_of_proceeds(use_of_proceeds: dict[str, Decimal] | None, top_n: int = 3) -> tuple[tuple[str, Decimal], ...] | None:
    if not use_of_proceeds:
        return None
    ordered = sorted(use_of_proceeds.items(), key=lambda item: item[1], reverse=True)
    return tuple(ordered[:top_n])


def _price_to_book(facts: IpoFacts) -> Decimal | None:
    if facts.offering_price is None or facts.book_value_per_share_before is None or facts.book_value_per_share_before == 0:
        return None
    return facts.offering_price / facts.book_value_per_share_before


def _equity_growth(facts: IpoFacts) -> Decimal | None:
    if facts.equity_before is None or facts.equity_after is None or facts.equity_before == 0:
        return None
    return _pct(facts.equity_after - facts.equity_before, facts.equity_before)


def compute_ipo_assessment(facts: IpoFacts) -> IpoAssessment:
    capital_increase_pct, partner_sale_pct, is_pure = _capital_increase_share(facts)
    retail_pct, domestic_inst_pct, foreign_inst_pct, high_demand_pct, other_pct = _classify_allocation(
        facts.allocation_breakdown
    )

    total_lot_count = _total_lot_count(facts)
    retail_lot_count = _lot_count_for_pct(retail_pct, total_lot_count)

    return IpoAssessment(
        capital_increase_share_pct=capital_increase_pct,
        partner_sale_share_pct=partner_sale_pct,
        is_pure_capital_increase=is_pure,
        allocation_retail_pct=retail_pct,
        allocation_domestic_institutional_pct=domestic_inst_pct,
        allocation_foreign_institutional_pct=foreign_inst_pct,
        allocation_high_demand_pct=high_demand_pct,
        allocation_other_pct=other_pct,
        top_use_of_proceeds=_top_use_of_proceeds(facts.use_of_proceeds),
        price_to_book_before=_price_to_book(facts),
        equity_growth_pct=_equity_growth(facts),
        total_lot_count=total_lot_count,
        allocation_retail_lot_count=retail_lot_count,
        allocation_domestic_institutional_lot_count=_lot_count_for_pct(domestic_inst_pct, total_lot_count),
        allocation_foreign_institutional_lot_count=_lot_count_for_pct(foreign_inst_pct, total_lot_count),
        allocation_high_demand_lot_count=_lot_count_for_pct(high_demand_pct, total_lot_count),
        allocation_other_lot_count=_lot_count_for_pct(other_pct, total_lot_count),
        estimated_retail_distribution=_estimated_retail_distribution(retail_lot_count, facts.offering_price),
    )
