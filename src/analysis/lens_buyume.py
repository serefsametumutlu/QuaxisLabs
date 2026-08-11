"""SPEC: `docs/spec/spec_mercek_buyume.md` -- Büyüme Merceği (v2 çok-mercekli
skorlama, Mercek 3/4) -- SAF MATEMATİK, `src.fetchers`/`src.db` HİÇBİR
modülü import ETMEZ (quaxis-mimari anayasa madde 1).

UYARI (spec'in kendi üst notu, AYNEN taşınır): bu mercek Fisher/Lynch
HENÜZ İŞLENMEDİĞİ için ZAYIF TEMELLENMİŞTİR -- bileşen sayısı (3) BİLİNÇLİ
olarak AZ tutulmuştur.

Ağırlıklar (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`, toplam %100):
    Hasılat Büyümesi (reel, seviye+trend)         %55  -- kalibre edilmiş çekirdek (v1'den taşınır)
    PEG Oranı (Lynch)                              %25  -- Lynch GARP felsefesi
    Marjinal ROE + Verimlilik Kaynaklı Büyüme      %20  -- 03/İLKE-85,86 (Damodaran FORMÜL-42,43)

`financials_by_period` girdisi (SADECE bu mercekte gerekli -- Marjinal
ROE'nin `equity_t-1` ve TTM `net_income_t-1` girdileri `calculator.
AnalysisResult`'ta YOKTUR, sadece QoQ karşılaştırma taşınır) --
`fundamental_screens.py`'nin ZATEN kullandığı "ham financials_by_period
dict + calculator public sarmalayıcılar" deseniyle AYNI ilke, katman
kuralını İHLAL ETMEZ (I/O yok, sadece dict okuma + aritmetik).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import calculator, scorer
from src.analysis.calculator import AnalysisResult, FinancialsByPeriod
from src.analysis.lens_common import LensSonucu, _agirlik_dagit_ve_hesapla, _lerp_score, _num_str, seviye_trend_skoru_v2
from src.formatting import format_percent_tr


@dataclass(frozen=True)
class BuyumeGirdisi:
    analysis: AnalysisResult
    financials_by_period: FinancialsByPeriod
    own_pe: Decimal | None = None  # calculator.ValuationMetrics.pe_ratio (PEG'in payı, kanonik ev BURASI)
    enflasyon_yoy_pct: Decimal | None = None
    template: str = "sanayi"


def _skor_hasilat_buyumesi(
    hasilat_yoy_pct: Decimal | None, enflasyon_yoy_pct: Decimal | None, cfg: dict, metrik_adi: str = "satış"
) -> tuple[Decimal | None, str]:
    """Mevcut scorer.py `buyume` cfg'si AYNEN taşınır -- SADECE motor
    `seviye_trend_skoru_v2`'ye (K1 düzeltmeli) geçirilmiştir.

    `metrik_adi` (bu tur EKLENDİ, banka/sigorta/finansman desteği için):
    banka/finansman şablonlarında "satış" yerine "kredi"/"finansman geliri"
    gibi doğru metrik adı geçirilir (spec_mercek_buyume.md §Sektör
    ayarlaması madde 3: Hasılat Büyümesi bileşeni bu şablonlarda Prim/
    kredi büyümesi ile DEĞİŞTİRİLİR) -- varsayılan "satış" ESKİ davranışı
    (sanayi/abd_sanayi metin çıktısı) DEĞİŞTİRMEZ."""
    if hasilat_yoy_pct is None:
        return None, f"{metrik_adi} YoY değişimi hesaplanamadı (önceki dönem verisi yok), bileşen atlandı."

    if enflasyon_yoy_pct is not None:
        reel = hasilat_yoy_pct - enflasyon_yoy_pct
        not_metni = f"(nominal {format_percent_tr(hasilat_yoy_pct)}, enflasyon {format_percent_tr(enflasyon_yoy_pct)} düşülerek)"
    else:
        reel = hasilat_yoy_pct
        not_metni = "(enflasyon verisi girilmedi, nominal büyüme kullanıldı)"

    skor, _gerekce = seviye_trend_skoru_v2(
        f"{metrik_adi.capitalize()} büyümesi", reel, None, guclu_esik=cfg["guclu_esik"], orta_esik=cfg["orta_esik"], tavan=cfg["tavan"], taban=cfg["taban"]
    )
    aciklama = f"{metrik_adi} büyümesi {format_percent_tr(reel)} {not_metni}."
    if reel is not None and reel > Decimal(25):
        # 01/İLKE-72 (Zweig): Fortune 500'ün en büyük 150'sinden sadece 8'i
        # (2 tam onyıl >=%15) sürdürebildi -- BÜYÜME İSTİKRARI ÇEKİNCESİ,
        # DOĞRUDAN ağırlık taşımaz (spec §Eşikler), sadece NİTEL not.
        aciklama += " Yüksek büyümenin (%25+) uzun vadede sürdürülmesi istatistiksel olarak nadirdir (Zweig)."
    return skor, aciklama


def _skor_peg(own_pe: Decimal | None, buyume_orani_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """Peter Lynch PEG oranı -- kanonik ev BÜYÜME merceğidir (DEĞER
    merceğinde SADECE çapraz referans verilir, ağırlık TAŞIMAZ -- çift
    sayma önlenir, bkz. spec §Uygulama notu). `valuation.py`'nin
    `_PEG_CHEAP_CEILING`/`_PEG_EXPENSIVE_FLOOR` sabitleriyle AYNI eşikler."""
    if own_pe is None or own_pe <= 0 or buyume_orani_pct is None or buyume_orani_pct <= 0:
        return None, "PEG oranı hesaplanamadı (F/K negatif/zarar veya büyüme oranı negatif/sıfır), bileşen atlandı."
    peg = own_pe / buyume_orani_pct
    ucuz, pahali = Decimal("0.9"), Decimal("1.1")
    if peg < ucuz:
        skor = _lerp_score(peg, Decimal(0), ucuz, Decimal(10), Decimal(7))
    elif peg <= pahali:
        skor = _lerp_score(peg, ucuz, pahali, Decimal(7), Decimal(5))
    else:
        skor = _lerp_score(peg, pahali, pahali * 4, Decimal(5), Decimal(0))
    aciklama = f"PEG oranı {_num_str(peg)} (F/K, büyüme oranına bölünmüş)."
    if buyume_orani_pct < Decimal(5):
        # 03/İLKE-175, BAYRAK-23: PEG'in U-şekli -- düşük büyümeli
        # şirketlerde YAPISAL OLARAK yüksek çıkar, skor DEĞİŞTİRİLMEZ,
        # sadece YORUM eklenir.
        aciklama += " Düşük büyümeli şirketlerde PEG yapısal olarak yüksek çıkar, bu tek başına 'pahalı' anlamına gelmez."
    return skor, aciklama


def _skor_marjinal_roe_ve_verimlilik(analysis: AnalysisResult, fbp: FinancialsByPeriod) -> tuple[Decimal | None, str]:
    """Damodaran FORMÜL-42 (Marjinal ROE) + FORMÜL-43 (Verimlilik Kaynaklı
    Ek Büyüme) -- TEK bir bileşende BİRLEŞTİRİLİR (spec §Eşikler: "Marjinal
    ROE + Verimlilik Kaynaklı Büyüme" TEK satır, %20).

    K5a DÜZELTMESİ (quant_denetim_01.md): `equity_t-1<=0` ise Marjinal ROE
    None döner (işaretsiz/anlamsız oran, negatif özkaynaklı BİST
    şirketlerinde CANLI doğrulanan bir durum).
    K5b DÜZELTMESİ: `fark_puan = marjinal_roe_pct - standart_roe_pct`,
    `_lerp_score(fark_puan, -15, +15, 0, 10)` -- X=15 puan Damodaran'ın
    Goldman Sachs 2005 örneğindeki sapma büyüklüğüne KABACA denk bir bant
    (03/İLKE-85,86), literatür-kaynaklı bir BAŞLANGIÇ değeri."""
    latest = analysis.latest_period
    year_ago = calculator.year_ago_period(latest)
    equity_t_minus_1 = fbp.get(year_ago, {}).get("equity")
    net_income_t = analysis.ratios.ttm_net_income
    net_income_t_minus_1 = calculator.trailing_12m_from_cumulative(fbp, year_ago, lambda d: d.get("net_income_cum"))
    roe_t = analysis.ratios.roe_annualized

    alt_skorlar: list[Decimal] = []
    parcalar: list[str] = []

    if equity_t_minus_1 is not None and equity_t_minus_1 > 0 and net_income_t is not None and net_income_t_minus_1 is not None:
        marjinal_roe_pct = (net_income_t - net_income_t_minus_1) / equity_t_minus_1 * 100
        if roe_t is not None:
            fark_puan = marjinal_roe_pct - roe_t
            skor = _lerp_score(fark_puan, Decimal(-15), Decimal(15), Decimal(0), Decimal(10))
            alt_skorlar.append(skor)
            parcalar.append(
                f"marjinal ROE {_num_str(marjinal_roe_pct)} puan, standart ROE'ye göre fark {_num_str(fark_puan)} puan"
            )

    roe_t_minus_1 = None
    if equity_t_minus_1 is not None and equity_t_minus_1 > 0 and net_income_t_minus_1 is not None:
        roe_t_minus_1 = net_income_t_minus_1 / equity_t_minus_1 * 100
    if roe_t is not None and roe_t_minus_1 is not None and roe_t_minus_1 != 0:
        verimlilik_buyume_pct = (roe_t - roe_t_minus_1) / abs(roe_t_minus_1) * 100
        skor = _lerp_score(verimlilik_buyume_pct, Decimal(-50), Decimal(50), Decimal(0), Decimal(10))
        alt_skorlar.append(skor)
        if verimlilik_buyume_pct >= 0:
            parcalar.append(f"verimlilik kaynaklı ek büyüme {_num_str(verimlilik_buyume_pct)} puan (ROE iyileşiyor)")
        else:
            parcalar.append(
                f"verimlilik kaynaklı büyüme {_num_str(verimlilik_buyume_pct)} puan (ROE kötüleşiyor) -- büyüme "
                "miktarı yüksek olsa bile kalitesi sorgulanmalı"
            )

    if not alt_skorlar:
        return (
            None,
            "marjinal ROE / verimlilik kaynaklı büyüme hesaplanamadı (geçmiş yıl özkaynağı/net kârı eksik veya "
            "negatif özkaynak), bileşen atlandı.",
        )
    skor = sum(alt_skorlar) / len(alt_skorlar)
    return skor, ", ".join(parcalar) + "."


def hesapla_buyume_mercegi(girdi: BuyumeGirdisi) -> LensSonucu:
    buyume_cfg = scorer.CONFIG[girdi.template]["buyume"]
    hasilat = _skor_hasilat_buyumesi(girdi.analysis.ratios.revenue_growth_yoy_pct, girdi.enflasyon_yoy_pct, buyume_cfg)
    peg = _skor_peg(girdi.own_pe, girdi.analysis.ratios.revenue_growth_yoy_pct)
    marjinal = _skor_marjinal_roe_ve_verimlilik(girdi.analysis, girdi.financials_by_period)

    bilesenler = [
        ("Hasılat Büyümesi (reel, seviye+trend)", Decimal("55"), hasilat),
        ("PEG Oranı (Lynch)", Decimal("25"), peg),
        ("Marjinal ROE + Verimlilik Kaynaklı Büyüme", Decimal("20"), marjinal),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, "büyüme", bilesenler)


# --- Banka/sigorta/finansman şablonu (spec §Sektör ayarlaması madde 3) -----------------------------------------------------
#
# Hasılat Büyümesi bileşeni Prim Büyümesi (sigorta, zaten `analysis.ratios.
# premium_growth_yoy_pct` MEVCUT) veya kredi büyümesi (banka/UFRS_KATILIM,
# `financials_by_period`'daki ham `loans` alanından, YENİ) veya finansman
# geliri büyümesi (finansman/XI_29K, ham `financing_revenue` alanından,
# YENİ) ile DEĞİŞTİRİLİR -- diğer 2 bileşen (PEG, Marjinal ROE) bu
# şablonlarda da KAVRAMSAL OLARAK geçerlidir (ROE zaten `analysis.ratios`
# içinde MEVCUT, bkz. spec_bilesik_skor.md §Kenar durumlar).
#
# EŞİK KAYNAĞI (uydurma DEĞİL): bu 3 şablon için AYRI bir "büyüme" eşik
# seti `scorer.CONFIG`'te YOKTUR (v1'in score_bank()/score_financing()
# fonksiyonları hiç büyüme bileşeni İÇERMEZ) -- yeni bir eşik İCAT ETMEK
# yerine, `scorer.CONFIG["sigorta"]["prim_buyumesi"]` (güçlü=%15/orta=%0/
# tavan=%40/taban=%-20 -- v1'de ZATEN kalibre edilmiş, finansal sektöre
# özgü TEK büyüme eşiği) ÜÇÜNDE de ORTAK kullanılır (sigortada zaten
# doğrudan aynı kaynak, banka/finansman'da "benzer büyüklükte finansal
# sektör büyüme oranı" varsayımıyla GENELLEŞTİRİLİR).


def _finansal_sektor_buyume_cfg() -> dict:
    return scorer.CONFIG["sigorta"]["prim_buyumesi"]


@dataclass(frozen=True)
class BuyumeGirdisiFinans:
    """Banka/sigorta/finansman şablonu için Büyüme merceği girdileri.

    `analysis`: `calculator.BankAnalysisResult` / `InsuranceAnalysisResult`
    / `FinancingAnalysisResult` -- bu fonksiyon SADECE `.ticker`/
    `.latest_period`/`.ratios.roe_annualized`/`.ratios.ttm_net_income`
    ORTAK alanlarına dokunur (duck-typing, `_skor_marjinal_roe_ve_
    verimlilik` sanayi ile TAMAMEN AYNI, kopyalanmadı).

    `buyume_orani_pct`: çağıran taraf (pipeline.py) önceden hesaplar --
    sigorta için `analysis.ratios.premium_growth_yoy_pct` DOĞRUDAN, banka
    için ham `loans` YoY değişimi (`calculator.classify_change`), finansman
    için ham `financing_revenue` YoY değişimi (AYNI fonksiyon) ile."""

    analysis: object
    financials_by_period: FinancialsByPeriod
    template: str  # "banka" | "sigorta" | "finansman"
    buyume_orani_pct: Decimal | None = None
    buyume_metrik_adi: str = "prim"  # "kredi" (banka) | "prim" (sigorta) | "finansman geliri" (finansman)
    own_pe: Decimal | None = None
    enflasyon_yoy_pct: Decimal | None = None


def hesapla_buyume_mercegi_finans(girdi: BuyumeGirdisiFinans) -> LensSonucu:
    """spec_mercek_buyume.md §Sektör ayarlaması madde 3 -- 3 bileşenli AYNI
    yapı (Hasılat/Prim/Kredi Büyümesi %55, PEG %25, Marjinal ROE+Verimlilik
    %20), SADECE büyüme kaynağı ve eşik seti değişir."""
    cfg = _finansal_sektor_buyume_cfg()
    hasilat = _skor_hasilat_buyumesi(girdi.buyume_orani_pct, girdi.enflasyon_yoy_pct, cfg, metrik_adi=girdi.buyume_metrik_adi)
    peg = _skor_peg(girdi.own_pe, girdi.buyume_orani_pct)
    marjinal = _skor_marjinal_roe_ve_verimlilik(girdi.analysis, girdi.financials_by_period)

    etiket = {"banka": "Kredi", "sigorta": "Prim", "finansman": "Finansman Geliri"}.get(girdi.template, girdi.buyume_metrik_adi.capitalize())
    bilesenler = [
        (f"{etiket} Büyümesi (reel, seviye+trend)", Decimal("55"), hasilat),
        ("PEG Oranı (Lynch)", Decimal("25"), peg),
        ("Marjinal ROE + Verimlilik Kaynaklı Büyüme", Decimal("20"), marjinal),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, f"büyüme_{girdi.template}", bilesenler)
