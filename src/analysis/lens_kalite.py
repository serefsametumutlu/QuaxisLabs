"""SPEC: `docs/spec/spec_mercek_kalite.md` -- Kalite Merceği (v2 çok-mercekli
skorlama, Mercek 2/4) -- SAF MATEMATİK, `src.fetchers`/`src.db` HİÇBİR
modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Ölçtüğü soru: rekabet avantajı + kârlılık kalitesi -- şirket parasını ne
kadar İYİ ve SÜRDÜRÜLEBİLİR biçimde kazanıyor? (Fiyattan BAĞIMSIZ, DEĞER
merceğinden KASITLI olarak ayrık -- 00_sentez.md §2.5.)

Ağırlıklar (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`, toplam %100):
    Nakit Üretimi (FAVÖK marjı)     %25  -- 02/İLKE-01-06
    Özkaynak Kârlılığı (ROE)        %20  -- 02/FORMÜL-22, İLKE-40,41
    Kârlılık (Net Marj)             %15  -- 02/FORMÜL-07, İLKE-13
    Brüt Kâr Marjı (seviye+trend)   %15  -- 02/FORMÜL-01, İLKE-02,03
    Greenblatt ROC                  %10  -- Greenblatt "Sihirli Formül"ünün KALİTE bacağı
    ROA                              %5  -- 02/FORMÜL-13, İLKE-26
    Nakit Kâr Kalitesi (OCF/NetKâr) %10  -- Piotroski kriter #4'ün SÜREKLİ versiyonu

Banka/sigorta/finansman şablonlarında (spec §Sektör ayarlaması madde 1)
KALİTE merceği SADECE ROE+ROA'dan oluşur; ağırlıklar (%20/%5 nominal
kendi içinde) `_agirlik_dagit_ve_hesapla`'nın orantısal dağıtımıyla
OTOMATİK %80/%20'ye döner (quant_denetim_01.md Y1 düzeltmesi: doğru
orantısal değer BU merceğin KENDİ nominal ağırlıklarından türetilir).

Amortisman/Brüt Kâr (Formüller-3): spec'in kendi Eşikler tablosunda AĞIRLIK
TAŞIMAZ (weight tablosu 25+20+15+15+10+5+10=%100'dür, bu bileşen o toplama
DAHİL DEĞİLDİR) -- SADECE bilgi amaçlı hesaplanabilir bir formül olarak
belgelenir, bu turda skorlanan bileşen KÜMESİNE EKLENMEDİ (gelecekte veri/
kalibrasyon netleşirse eklenebilir).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import scorer
from src.analysis.calculator import AnalysisResult
from src.analysis.fundamental_screens import GreenblattResult
from src.analysis.lens_common import LensSonucu, _agirlik_dagit_ve_hesapla, _lerp_score, _asymptote_to, oran_str, seviye_trend_skoru_v2


@dataclass(frozen=True)
class KaliteGirdisi:
    analysis: AnalysisResult
    greenblatt: GreenblattResult | None = None  # SADECE BİST XI_29 sanayi
    operating_cash_flow_ttm: Decimal | None = None  # pipeline.py: calculator.trailing_12m_from_cumulative(...)
    template: str = "sanayi"


def _skor_roe(roe: Decimal | None, equity_current: Decimal | None) -> tuple[Decimal | None, str]:
    """02/İLKE-36,41: negatif özkaynak/anormal yüksek ROE İKİ neden
    (bilinçli tam-dağıtım politikası OLUMLU, iflasa sürüklenme OLUMSUZ)
    taşıyabilir -- QuaxisLabs bu ayrımı yapacak çok-yıllı seriye SAHİP
    DEĞİL, bu yüzden negatif özkaynakta bileşen SESSİZCE None döner
    (Kural 3: uydurma yapılmaz)."""
    if equity_current is not None and equity_current <= 0:
        return (
            None,
            "negatif özkaynak -- Warren Buffett çerçevesine göre bu ya bilinçli tam-dağıtım politikası (olumlu) "
            "ya iflas riski (olumsuz) anlamına gelebilir, ayrım için çok-yıllı kazanç geçmişi gerekir; bileşen atlandı.",
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


def hesapla_kalite_mercegi(girdi: KaliteGirdisi) -> LensSonucu:
    """`sanayi`/`abd_sanayi` şablonu için 7 bileşenli tam Kalite Merceği."""
    r = girdi.analysis.ratios
    nakit_uretimi = seviye_trend_skoru_v2(
        "FAVÖK marjı", r.ebitda_margin_current, r.ebitda_margin_change_points, guclu_esik=Decimal(20), orta_esik=Decimal(10), tavan=Decimal(30)
    )
    roe = _skor_roe(r.roe_annualized, girdi.analysis.balance_sheet.equity.current)
    net_marj = seviye_trend_skoru_v2(
        "Net marj", r.net_margin_current, r.net_margin_change_points, guclu_esik=Decimal(15), orta_esik=Decimal(5), tavan=Decimal(25)
    )
    brut_marj = seviye_trend_skoru_v2(
        "Brüt kâr marjı", r.gross_margin_current, r.gross_margin_change_points, guclu_esik=Decimal(40), orta_esik=Decimal(20), tavan=Decimal(70)
    )
    roc = _skor_greenblatt_roc(girdi.greenblatt)
    roa = _skor_roa(girdi.analysis)
    nakit_kalitesi = _skor_nakit_kar_kalitesi(girdi.operating_cash_flow_ttm, r.ttm_net_income)

    bilesenler = [
        ("Nakit Üretimi (FAVÖK marjı)", Decimal("25"), nakit_uretimi),
        ("Özkaynak Kârlılığı (ROE)", Decimal("20"), roe),
        ("Kârlılık (Net Marj)", Decimal("15"), net_marj),
        ("Brüt Kâr Marjı", Decimal("15"), brut_marj),
        ("Greenblatt Sermaye Getirisi (ROC)", Decimal("10"), roc),
        ("Aktif Kârlılığı (ROA)", Decimal("5"), roa),
        ("Nakit Kâr Kalitesi (OCF/Net Kâr)", Decimal("10"), nakit_kalitesi),
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
