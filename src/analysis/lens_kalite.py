"""SPEC: `docs/spec/spec_mercek_kalite.md` -- Kalite Merceği (v2 çok-mercekli
skorlama, Mercek 2/4) -- SAF MATEMATİK, `src.fetchers`/`src.db` HİÇBİR
modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Ölçtüğü soru: rekabet avantajı + kârlılık kalitesi -- şirket parasını ne
kadar İYİ ve SÜRDÜRÜLEBİLİR biçimde kazanıyor? (Fiyattan BAĞIMSIZ, DEĞER
merceğinden KASITLI olarak ayrık -- 00_sentez.md §2.5.)

Ağırlıklar (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`, toplam %100
-- docs/spec/spec_yeni_bilesenler_agirliklandirma.md §1 turunda GÜNCELLENDİ,
üç YENİ bileşen eklendi, payın çoğu FAVÖK marjından çekildi):
    Nakit Üretimi (FAVÖK marjı)     %20  -- 02/İLKE-01 (eski %25, -5)
    Özkaynak Kârlılığı (ROE)        %18  -- 02/FORMÜL-22, İLKE-40,41 (eski %20, -2)
    Kârlılık (Net Marj)             %13  -- 02/FORMÜL-07, İLKE-13 (eski %15, -2)
    Brüt Kâr Marjı (seviye+trend)   %13  -- 02/FORMÜL-01, İLKE-02,03 (eski %15, -2)
    Greenblatt ROC                   %8  -- Greenblatt "Sihirli Formül"ünün KALİTE bacağı (eski %10, -2)
    ROA                               %4  -- 02/FORMÜL-13, İLKE-26 (eski %5, -1)
    Nakit Kâr Kalitesi (OCF/NetKâr)  %9  -- Piotroski kriter #4'ün SÜREKLİ versiyonu (eski %10, -1)
    SG&A/Brüt Kâr (YENİ)             %5  -- 02/FORMÜL-02, NASDAQ'ta VE BİST XI_29 (sanayi/ticaret) şirketlerinde dolu (2026-08-14'ten itibaren)
    Ar-Ge/Brüt Kâr (YENİ)            %3  -- 02/FORMÜL-03, NASDAQ'ta VE BİST XI_29'da dolu (GERİLİM notu, bkz. _skor_rd_orani)
    Faiz Gideri/Faaliyet Kârı (YENİ) %7  -- 01/FORMÜL-18, 02/FORMÜL-05, BAYRAK-06, NASDAQ'ta VE BİST XI_29'da dolu

Banka/sigorta/finansman şablonlarında (spec §Sektör ayarlaması madde 1)
KALİTE merceği SADECE ROE+ROA'dan oluşur; ağırlıklar (%20/%5 nominal
kendi içinde) `_agirlik_dagit_ve_hesapla`'nın orantısal dağıtımıyla
OTOMATİK %80/%20'ye döner (quant_denetim_01.md Y1 düzeltmesi: doğru
orantısal değer BU merceğin KENDİ nominal ağırlıklarından türetilir).
Bu banka/sigorta/finansman şablonu YENİ 3 bileşenden ETKİLENMEDİ (spec_
yeni_bilesenler_agirliklandirma.md: "yeni bileşenlerin TÜMÜ sanayi/
abd_sanayi şablonlarında yaşıyor").

Amortisman/Brüt Kâr (Formüller-3): spec'in kendi Eşikler tablosunda AĞIRLIK
TAŞIMAZ -- SADECE bilgi amaçlı hesaplanabilir bir formül olarak belgelenir,
bu turda skorlanan bileşen KÜMESİNE EKLENMEDİ (gelecekte veri/kalibrasyon
netleşirse eklenebilir).

SG&A/Ar-Ge/Faiz Gideri (docs/spec/spec_yeni_bilesenler_agirliklandirma.md
§1): BİST XI_29 (sanayi/ticaret) haritasına bu üç ham alan 2026-08-14'te
eklendi (`isyatirim.py::STANDARD_ITEM_MAP_XI_29`), bu yüzden XI_29
şirketlerinde artık NASDAQ ile AYNI 10-bileşenli KALİTE kartı görülür.
Banka (UFRS)/sigorta (UFRS_K)/finansman (FINANSMAN) şablonlarında bu üç
ham alan HÂLÂ çekilmiyor (kavramsal olarak "brüt kâr" yapısı bu şirket
türlerinde YOK, KALICI kapsam-dışı) -- bu şablonlarda bileşenler `None`
döner, ağırlığı (%15 toplam) diğer 7 bileşene ORANTISAL yeniden
dağıtılır (`_agirlik_dagit_ve_hesapla`, DEĞİŞMEDİ).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import scorer
from src.analysis.calculator import AnalysisResult
from src.analysis.fundamental_screens import GreenblattResult
from src.analysis.lens_common import (
    LensSonucu,
    _agirlik_dagit_ve_hesapla,
    _asymptote_to,
    _lerp_score,
    oran_str,
    seviye_trend_skoru_v2,
)
from src.formatting import format_percent_tr


@dataclass(frozen=True)
class KaliteGirdisi:
    analysis: AnalysisResult
    greenblatt: GreenblattResult | None = None  # SADECE BİST XI_29 sanayi
    operating_cash_flow_ttm: Decimal | None = None  # pipeline.py: calculator.trailing_12m_from_cumulative(...)
    # V-04 (docs/spec/spec_veri_tamlik_yol_haritasi.md) -- SADECE NASDAQ
    # (sec_edgar.STANDARD_ITEM_MAP_US_GAAP "treasury_stock",
    # us-gaap:TreasuryStockValue) -- pipeline.py: en güncel dönemin ham
    # "treasury_stock" alanı. BİST'te bu alan hiç çekilmediği için her
    # zaman None (fallback: mevcut ham ROE davranışı DEĞİŞMEZ).
    treasury_stock: Decimal | None = None
    template: str = "sanayi"


def _skor_roe(
    roe: Decimal | None,
    equity_current: Decimal | None,
    ttm_net_income: Decimal | None = None,
    treasury_stock: Decimal | None = None,
) -> tuple[Decimal | None, str]:
    """02/İLKE-36,41: negatif özkaynak/anormal yüksek ROE İKİ neden
    (bilinçli tam-dağıtım politikası OLUMLU, iflasa sürüklenme OLUMSUZ)
    taşıyabilir -- QuaxisLabs bu ayrımı yapacak çok-yıllı seriye SAHİP
    DEĞİL, bu yüzden negatif özkaynakta bileşen SESSİZCE None döner
    (Kural 3: uydurma yapılmaz).

    V-04 (docs/spec/spec_veri_tamlik_yol_haritasi.md, 02/FORMÜL-21):
    `treasury_stock` MEVCUTSA (şimdilik SADECE NASDAQ, `us-gaap:
    TreasuryStockValue`) "finansal-mühendislik-arındırılmış" ROE = TTM Net
    Kâr / (Özkaynak + Hazine Hissesi [pozitife çevrilmiş]) kullanılır --
    Buffett'ın "AAPL-tipi düşük özkaynak tabanı" (agresif geri alım ->
    yapay yüksek ROE) uyarısını AAPL'in KENDİSİ dışında (Apple hazine
    hissesi TUTMUYOR, geri aldığı payları İPTAL ediyor -- bu durumda
    `treasury_stock=None` kalır, ham ROE'ye SESSİZCE devam edilir)
    hazine hissesi biriktiren şirketlerde (JPM gibi) doğrudan ÇÖZER. AYNI
    ROE eşikleri (güçlü≥%15/orta≥%10/tavan%25) ve AYNI ağırlık (%20)
    KULLANILIR -- yeni bir bileşen/ağırlık İCAT EDİLMEDİ, mevcut "Özkaynak
    Kârlılığı (ROE)" bileşeni DAHA DOĞRU bir girdiyle besleniyor."""
    if equity_current is not None and equity_current <= 0:
        return (
            None,
            "negatif özkaynak -- Warren Buffett çerçevesine göre bu ya bilinçli tam-dağıtım politikası (olumlu) "
            "ya iflas riski (olumsuz) anlamına gelebilir, ayrım için çok-yıllı kazanç geçmişi gerekir; bileşen atlandı.",
        )
    if treasury_stock is not None and treasury_stock > 0 and equity_current is not None and ttm_net_income is not None:
        equity_duzeltilmis = equity_current + treasury_stock
        roe_duzeltilmis = ttm_net_income / equity_duzeltilmis * 100
        skor, aciklama = seviye_trend_skoru_v2(
            "Özkaynak kârlılığı (hazine hissesi düzeltmeli ROE)", roe_duzeltilmis, None,
            guclu_esik=Decimal(15), orta_esik=Decimal(10), tavan=Decimal(25),
        )
        return skor, (
            aciklama + " Buffett'ın finansal-mühendislik-arındırılmış ROE formülü (02/FORMÜL-21: Net Kâr/"
            "(Özkaynak+Hazine Hissesi)) kullanıldı -- geri alım kaynaklı yapay ROE şişmesi arındırıldı."
        )
    if roe is None:
        return None, "özkaynak kârlılığı (ROE) hesaplanamadı (TTM net kâr veya güncel özkaynak eksik), bileşen atlandı."
    return seviye_trend_skoru_v2("Özkaynak kârlılığı (ROE)", roe, None, guclu_esik=Decimal(15), orta_esik=Decimal(10), tavan=Decimal(25))


def _skor_roa(analysis: AnalysisResult) -> tuple[Decimal | None, str]:
    """02/FORMÜL-13, İLKE-26: ROA = TTM Net Kâr / Toplam Varlık -- ham veri
    zaten mevcut (`ratios.ttm_net_income`, `balance_sheet.total_assets`),
    `calculator.Ratios`'a henüz eklenmemiş bir alan, burada türetilir."""
    ttm_net_income = analysis.ratios.ttm_net_income
    total_assets = analysis.balance_sheet.total_assets.current
    if ttm_net_income is None or total_assets is None or total_assets <= 0:
        return None, "aktif kârlılığı (ROA) hesaplanamadı (TTM net kâr veya toplam varlık eksik), bileşen atlandı."
    roa_pct = ttm_net_income / total_assets * 100
    return seviye_trend_skoru_v2("Aktif kârlılığı (ROA)", roa_pct, None, guclu_esik=Decimal(8), orta_esik=Decimal(3), tavan=Decimal(20))


def _skor_greenblatt_roc(greenblatt: GreenblattResult | None) -> tuple[Decimal | None, str]:
    """Greenblatt'ın "Sihirli Formül"ünün KALİTE bacağı (EBIT/Yatırılan
    Sermaye) -- sermaye verimliliği. SADECE BİST XI_29 sanayi için mevcut."""
    if greenblatt is None or greenblatt.return_on_capital_pct is None:
        return None, "Greenblatt Sermaye Getirisi (ROC) hesaplanamadı (sadece BİST XI_29 sanayi şirketlerinde mevcut), bileşen atlandı."
    return seviye_trend_skoru_v2("Sermaye getirisi (ROC)", greenblatt.return_on_capital_pct, None, guclu_esik=Decimal(25), orta_esik=Decimal(10), tavan=Decimal(50))


def _skor_nakit_kar_kalitesi(ocf_ttm: Decimal | None, net_income_ttm: Decimal | None) -> tuple[Decimal | None, str]:
    """Nakit Kâr Kalitesi = OCF/Net Kâr -- Piotroski kriter #4'ün (OCF>NetKâr,
    ikili) SÜREKLİ versiyonu. K4 BİRİM UYARISI (quant_denetim_01.md): bu
    bir ORANDIR (x-katı), YÜZDE DEĞİLDİR -- `oran_str` ile formatlanır."""
    if ocf_ttm is None or net_income_ttm is None:
        return None, "nakit kâr kalitesi (OCF/Net Kâr) hesaplanamadı (TTM işletme nakit akışı veya net kâr eksik), bileşen atlandı."
    if net_income_ttm <= 0:
        return None, "net kâr negatif/sıfır, nakit kâr kalitesi oranının işareti anlamsız, bileşen atlandı."
    oran = ocf_ttm / net_income_ttm
    guclu, orta = Decimal("1.0"), Decimal("0.7")
    if oran >= guclu:
        skor = _asymptote_to(oran - guclu, Decimal("1.0"), Decimal(7), Decimal(10))
    elif oran >= orta:
        skor = _lerp_score(oran, orta, guclu, Decimal(4), Decimal(7))
    else:
        skor = _lerp_score(oran, Decimal(-1), orta, Decimal(0), Decimal(4))
    return skor, f"nakit kâr kalitesi (OCF/Net Kâr) {oran_str(oran)} -- ideal ~1,00x veya üzeri (Piotroski kriter #4'ün sürekli hali)."


# --- YENİ bileşenler (docs/spec/spec_yeni_bilesenler_agirliklandirma.md §1) -----------------------------------------------------
#
# Üçü de SADECE NASDAQ'ta dolu (BİST XI_29 sanayi haritasında bu ham alanlar
# hiç çekilmiyor, isyatirim.py grep ile doğrulandı -- her zaman None kalır,
# `_agirlik_dagit_ve_hesapla` ağırlığını diğer 7 bileşene ORANTISAL dağıtır).


def _skor_sga_orani(oran_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """02/FORMÜL-02 -- SG&A (satış, genel, idari giderler)/Brüt Kâr, DÜŞÜK=
    iyi (ters yön). Eşik (spec_mercek_kalite.md satır 140, spec_yeni_
    bilesenler_agirliklandirma.md §1'in AYNEN aktardığı tablo): <%30
    fantastik (9-10), %30-80 mümkün (kademeli 8->3), ~%100+ tekrarlayan
    kırmızı bayrak (0-2)."""
    if oran_pct is None:
        return None, (
            "SG&A/Brüt Kâr oranı hesaplanamadı (bu veri sadece NASDAQ şirketlerinde mevcut, BİST'te henüz "
            "çekilmiyor -- araştırma gerekiyor), bileşen atlandı."
        )
    esik_fantastik, esik_mumkun = Decimal(30), Decimal(80)
    if oran_pct < esik_fantastik:
        skor = _lerp_score(oran_pct, Decimal(0), esik_fantastik, Decimal(10), Decimal(9))
    elif oran_pct <= esik_mumkun:
        skor = _lerp_score(oran_pct, esik_fantastik, esik_mumkun, Decimal(8), Decimal(3))
    else:
        skor = _lerp_score(oran_pct, esik_mumkun, Decimal(100), Decimal(3), Decimal(0))
    return skor, (
        f"SG&A (satış, genel, idari giderler)/Brüt Kâr oranı {format_percent_tr(oran_pct)} -- düşük olması "
        "operasyonel disiplin/dayanıklı rekabet avantajı göstergesidir (02/FORMÜL-02)."
    )


def _skor_rd_orani(oran_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """02/FORMÜL-03 -- Ar-Ge/Brüt Kâr, DÜŞÜK=iyi (ters yön). Eşik (spec_
    mercek_kalite.md satır 141): %0 en iyi (10), ~%30 sürdürmek zorunda/
    kırılgan sınırı (5), tavan %50+ (0-2).

    GERİLİM notu (spec_yeni_bilesenler_agirliklandirma.md §1, ÇÖZÜLMEZ,
    BİLİNÇLİ tutulur -- persona kural 4): Buffett'ın çerçevesi DÜŞÜK Ar-Ge
    oranını dayanıklı rekabet avantajı sinyali sayar (Coca-Cola %0 vs Intel
    %16,8 örneği), Fisher'ın çerçevesi (HENÜZ İŞLENMEDİ) muhtemelen TERS
    yönde okurdu (yüksek ama verimli Ar-Ge bir moat-İNŞA aracı, özellikle
    NASDAQ'ın teknoloji ağırlıklı evreninde) -- bu gerilim ağırlığın
    BİLEREK en düşük tutulmasıyla (%3) VE kart notuyla yansıtılır."""
    if oran_pct is None:
        return None, (
            "Ar-Ge/Brüt Kâr oranı hesaplanamadı (bu veri sadece NASDAQ şirketlerinde mevcut, BİST'te henüz "
            "çekilmiyor -- araştırma gerekiyor), bileşen atlandı."
        )
    esik_kirilgan = Decimal(30)
    if oran_pct <= esik_kirilgan:
        skor = _lerp_score(oran_pct, Decimal(0), esik_kirilgan, Decimal(10), Decimal(5))
    else:
        skor = _lerp_score(oran_pct, esik_kirilgan, Decimal(50), Decimal(5), Decimal(0))
    aciklama = (
        f"Ar-Ge/Brüt Kâr oranı {format_percent_tr(oran_pct)} -- Buffett çerçevesinde düşük oran dayanıklı "
        "rekabet avantajı göstergesi sayılır (02/FORMÜL-03)."
    )
    if oran_pct > esik_kirilgan:
        aciklama += (
            " Yüksek Ar-Ge oranı bu NASDAQ teknoloji şirketinde OTOMATİK olumsuz sayılmamalı -- Fisher merceği "
            "eklendiğinde bu yön yeniden değerlendirilecek (bilinen gerilim, henüz çözülmedi)."
        )
    return skor, aciklama


def _skor_faiz_gideri_orani(oran_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """01/FORMÜL-18, 02/FORMÜL-05, BAYRAK-06 -- Faiz Gideri/Faaliyet Kârı,
    DÜŞÜK=iyi (ters yön). Eşik (spec_mercek_kalite.md satır 142, spec_yeni_
    bilesenler_agirliklandirma.md §1): <%15 güçlü (Buffett'ın tüketici
    ürünleri sektörü tipik üst sınırı, 9-10), %15-40 orta (kademeli 8->3),
    >%40 zayıf (0-3). Spec bu bölgede sabit bir tavan sayısı VERMEDİ
    ("uydurma tavan" riskinden kaçınmak için) -- bunun yerine asimptotik
    olarak 0'a yaklaşan bir kuyruk kullanılır (`_asymptote_to`, mevcut
    FAVÖK marjı motorunun "eşik ötesi" tekniğiyle AYNI, sadece yön TERS).

    K3-tipi net faiz geliri riski (spec §1 Kenar Durumlar): bazı NASDAQ
    şirketlerinde `interest_expense` NET (gider-gelir birleşik) raporlanmış
    olabilir -- negatif oran çıkarsa (fiilen "en düşük/en iyi" ucuna
    kırpılır) kart bunu AÇIKÇA bir uyarı notuyla işaretler."""
    if oran_pct is None:
        return None, (
            "Faiz Gideri/Faaliyet Kârı oranı hesaplanamadı (bu veri sadece NASDAQ şirketlerinde mevcut, BİST "
            "sanayi haritasında henüz çekilmiyor -- araştırma gerekiyor), bileşen atlandı."
        )
    esik_guclu, esik_orta = Decimal(15), Decimal(40)
    if oran_pct < esik_guclu:
        skor = _lerp_score(oran_pct, Decimal(0), esik_guclu, Decimal(10), Decimal(9))
    elif oran_pct <= esik_orta:
        skor = _lerp_score(oran_pct, esik_guclu, esik_orta, Decimal(8), Decimal(3))
    else:
        yari_omur = (esik_orta - esik_guclu) / 2
        skor = _asymptote_to(oran_pct - esik_orta, yari_omur, Decimal(3), Decimal(0))
    aciklama = (
        f"Faiz Gideri/Faaliyet Kârı oranı {format_percent_tr(oran_pct)} -- Buffett'ın tüketici ürünleri sektörü "
        "tipik üst sınırı %15 (02/FORMÜL-05)."
    )
    if oran_pct < 0:
        aciklama += " Negatif oran -- net faiz geliri/gideri birleşik raporlanmış olabilir, dikkatli yorumlanmalı."
    return skor, aciklama


def hesapla_kalite_mercegi(girdi: KaliteGirdisi) -> LensSonucu:
    """`sanayi`/`abd_sanayi` şablonu için 7 bileşenli tam Kalite Merceği."""
    r = girdi.analysis.ratios
    nakit_uretimi = seviye_trend_skoru_v2(
        "FAVÖK marjı", r.ebitda_margin_current, r.ebitda_margin_change_points, guclu_esik=Decimal(20), orta_esik=Decimal(10), tavan=Decimal(30)
    )
    roe = _skor_roe(r.roe_annualized, girdi.analysis.balance_sheet.equity.current, r.ttm_net_income, girdi.treasury_stock)
    net_marj = seviye_trend_skoru_v2(
        "Net marj", r.net_margin_current, r.net_margin_change_points, guclu_esik=Decimal(15), orta_esik=Decimal(5), tavan=Decimal(25)
    )
    brut_marj = seviye_trend_skoru_v2(
        "Brüt kâr marjı", r.gross_margin_current, r.gross_margin_change_points, guclu_esik=Decimal(40), orta_esik=Decimal(20), tavan=Decimal(70)
    )
    roc = _skor_greenblatt_roc(girdi.greenblatt)
    roa = _skor_roa(girdi.analysis)
    nakit_kalitesi = _skor_nakit_kar_kalitesi(girdi.operating_cash_flow_ttm, r.ttm_net_income)
    sga_orani = _skor_sga_orani(r.sga_to_gross_profit_pct)
    rd_orani = _skor_rd_orani(r.rd_to_gross_profit_pct)
    faiz_gideri_orani = _skor_faiz_gideri_orani(r.interest_expense_to_operating_profit_pct)

    bilesenler = [
        ("Nakit Üretimi (FAVÖK marjı)", Decimal("20"), nakit_uretimi),
        ("Özkaynak Kârlılığı (ROE)", Decimal("18"), roe),
        ("Kârlılık (Net Marj)", Decimal("13"), net_marj),
        ("Brüt Kâr Marjı", Decimal("13"), brut_marj),
        ("Greenblatt Sermaye Getirisi (ROC)", Decimal("8"), roc),
        ("Aktif Kârlılığı (ROA)", Decimal("4"), roa),
        ("Nakit Kâr Kalitesi (OCF/Net Kâr)", Decimal("9"), nakit_kalitesi),
        ("SG&A/Brüt Kâr", Decimal("5"), sga_orani),
        ("Ar-Ge/Brüt Kâr", Decimal("3"), rd_orani),
        ("Faiz Gideri/Faaliyet Kârı", Decimal("7"), faiz_gideri_orani),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, "kalite", bilesenler)


def hesapla_kalite_mercegi_banka(
    ticker: str,
    period: tuple[int, int],
    roe_pct: Decimal | None,
    roa_pct: Decimal | None,
    template: str = "banka",
) -> LensSonucu:
    """Banka/sigorta/finansman şablonu -- SADECE ROE+ROA (spec §Sektör
    ayarlaması madde 1). Nominal ağırlıklar HER şablonda AYNI tutulur
    (ROE=80, ROA=20 -- quant_denetim_01.md Y1 düzeltmesinin ÖNERDİĞİ
    80/20 oranı BURADA nominal ağırlığın KENDİSİ olarak yazılır, KALİTE
    merceğinin `sanayi` şablonundaki 20/5 -- AYNI 4:1 ORANI -- yerine
    DOĞRUDAN kullanılır).

    DÜZELTME (bu tur -- iki AYRI hata giderildi):
    1. Nominal ağırlıklar ÖNCEDEN (20, 5) idi -- toplamları 25 olduğu için
       `_agirlik_dagit_ve_hesapla`'nın `min_veri_agirlik_yuzdesi=%50`
       kontrolü HER ZAMAN (ROE+ROA İKİSİ de dolu olsa BİLE) `data_sufficient
       =False`/"YETERSİZ VERİ" ÜRETİYORDU (CANLI doğrulandı) -- oysa bu
       eşik nominal ağırlıkların TOPLAMDA %100'e tamamlandığı VARSAYIMIYLA
       tasarlanmıştır (v1'in TÜM CONFIG şablonlarında ve `hesapla_kalite_
       mercegi`'nin 7 bileşeninde bu HER ZAMAN doğrudur). Efektif ağırlık
       oranı (80/20) DEĞİŞMEDİ (80:20 ORANI 20:5 ile AYNIDIR) -- SADECE
       "veri yeterliliği" hesabının doğru çalışması için nominal ağırlıklar
       100'e tamamlanacak şekilde YENİDEN YAZILDI.
    2. Eşikler artık `template` parametresine göre `scorer.CONFIG[template]`
    eşikler artık `template` parametresine göre `scorer.CONFIG[template]`
    içinden okunur -- ÖNCEKİ sürüm BANKA'nın kendi eşiklerini (ROE
    güçlü=%20/orta=%10/tavan=%35, ROA güçlü=%2,5/orta=%1/tavan=%4)
    sigorta/finansman için de SESSİZCE kullanıyordu; oysa v1'in KENDİ
    kalibre ettiği şablon-özel eşikleri FARKLIDIR
    (`CONFIG["sigorta"]["ozkaynak_karliligi"]` güçlü=%25/orta=%10/tavan=%40,
    `CONFIG["finansman"]["aktif_karliligi"]` güçlü=%5/orta=%2/tavan=%10,
    taban=%-5) -- persona kural 8 ("v1'deki desene sadık kal") gereği
    artık DOĞRU şablondan okunur. `template="banka"` varsayılanı ESKİ
    davranışı (ve mevcut testleri) DEĞİŞTİRMEZ. Sigorta CONFIG'inde
    `aktif_karliligi` alt-sözlüğü hiç YOK (ham `total_assets` verisi
    UFRS_K şemasında hiç yok, ROA zaten HER ZAMAN None gelir) -- bu
    durumda banka'nın ROA eşikleri YEDEK olarak kullanılır (hiçbir zaman
    tetiklenmez, sadece KeyError'u önler)."""
    roe_cfg = scorer.CONFIG[template]["ozkaynak_karliligi"]
    roa_cfg = scorer.CONFIG[template].get("aktif_karliligi") or scorer.CONFIG["banka"]["aktif_karliligi"]
    roe = seviye_trend_skoru_v2(
        "Özkaynak kârlılığı (ROE)", roe_pct, None,
        guclu_esik=roe_cfg["guclu_esik"], orta_esik=roe_cfg["orta_esik"], tavan=roe_cfg["tavan"],
    )
    roa = seviye_trend_skoru_v2(
        "Aktif kârlılığı (ROA)", roa_pct, None,
        guclu_esik=roa_cfg["guclu_esik"], orta_esik=roa_cfg["orta_esik"], tavan=roa_cfg["tavan"],
    )
    bilesenler = [
        ("Özkaynak Kârlılığı (ROE)", Decimal("80"), roe),
        ("Aktif Kârlılığı (ROA)", Decimal("20"), roa),
    ]
    return _agirlik_dagit_ve_hesapla(ticker, period, f"kalite_{template}", bilesenler)
