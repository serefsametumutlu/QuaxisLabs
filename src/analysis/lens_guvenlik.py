"""SPEC: `docs/spec/spec_mercek_guvenlik.md` -- Güvenlik Merceği (v2
çok-mercekli skorlama, Mercek 4/4) -- SAF MATEMATİK, `src.fetchers`/
`src.db` HİÇBİR modülü import ETMEZ (quaxis-mimari anayasa madde 1).

Ölçtüğü soru: muhasebe hilesi + bilanço riski -- bu şirket YAKINDA ZOR
duruma düşer mi, raporlanan rakamlara GÜVENİLEBİLİR mi?

Ağırlıklar (spec §Eşikler ve ağırlıklar, `sanayi`/`abd_sanayi`, toplam %100
-- docs/spec/spec_yeni_bilesenler_agirliklandirma.md §2 turunda GÜNCELLENDİ,
Faiz Karşılama Oranı "yer tutucu"dan GERÇEK skorlanan bileşene yükseltildi):
    Kaldıraç (Net Borç/FAVÖK)                  %29  -- kalibre edilmiş çekirdek (eski %30, -1)
    Bilanço Kalitesi (Cari Oran+Özkaynak/Varlık) %18  -- kalibre edilmiş çekirdek (eski %20, -2)
    Piotroski F-Skoru                          %24  -- Piotroski (2000) (eski %25, -1)
    Toplam Yükümlülük/Özkaynak (geniş tanım)   %12  -- 02/FORMÜL-16, İLKE-30 (eski %15, -3)
    Merton Temerrüt Olasılığı (EDF)             %7  -- 03/İLKE-441-444, BAYRAK-79/80 (eski %10, -3)
    Faiz Karşılama Oranı (YENİ)                %10  -- 03/Tablo 2.4, FORMÜL-19; 01/FORMÜL-18; 02/FORMÜL-05 -- SADECE NASDAQ'ta dolu

`financials_by_period` girdisi SADECE Toplam Yükümlülük/Özkaynak (geniş
tanım, `short_term_liabilities`+`long_term_liabilities` ham alanları
`calculator.AnalysisResult`'ta YOKTUR) için gerekir -- `fundamental_
screens.py` ile AYNI "ham dict + aritmetik" deseni, katman kuralını
İHLAL ETMEZ.

Faiz Karşılama Oranı BİST'te HER ZAMAN `None` döner (girdisi olan
`interest_expense_to_operating_profit_pct` BİST XI_29 haritasında hiç
çekilmiyor, KALİTE merceğinin §1 bileşeniyle AYNI asimetri) -- ağırlığı
diğer 5 bileşene ORANTISAL yeniden dağıtılır.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import scorer
from src.analysis.calculator import AnalysisResult, FinancialsByPeriod
from src.analysis.fundamental_screens import PiotroskiResult
from src.analysis.lens_common import LensSonucu, _agirlik_dagit_ve_hesapla, _lerp_score, _num_str, _safe_pct, oran_str, seviye_trend_skoru_v2
from src.analysis.merton import MertonResult
from src.formatting import format_percent_tr


@dataclass(frozen=True)
class GuvenlikGirdisi:
    analysis: AnalysisResult
    financials_by_period: FinancialsByPeriod
    piotroski: PiotroskiResult | None = None  # SADECE BİST XI_29 sanayi
    merton: MertonResult | None = None  # pipeline.py: merton.compute_merton_dd_edf(...) -- BAYRAK-79/80 koprusu
    template: str = "sanayi"


def _skor_piotroski(piotroski: PiotroskiResult | None) -> tuple[Decimal | None, str]:
    """Piotroski F-Skoru'nun SÜREKLİ hali: `score/criteria_evaluated*100`,
    %78~7/9 güçlü, %44~4/9 orta (Piotroski'nin kendi 2000 makalesi bandına
    yakın). `criteria_evaluated<5` ise mevcut `fundamental_screens.py`
    davranışı (band=None, Kural 3: çok az kriterle yorum yapılmaz) KORUNUR."""
    if piotroski is None or piotroski.band is None:
        return (
            None,
            "Piotroski F-Skoru hesaplanamadı (sadece BİST XI_29 sanayi şirketlerinde mevcut veya yeterli kriter "
            "değerlendirilemedi), bileşen atlandı.",
        )
    f_skoru_pct = Decimal(piotroski.score) / Decimal(piotroski.criteria_evaluated) * 100
    return seviye_trend_skoru_v2(
        "Piotroski F-Skoru", f_skoru_pct, None, guclu_esik=Decimal(78), orta_esik=Decimal(44), tavan=Decimal(100)
    )


def _skor_toplam_yukumluluk_ozkaynak(analysis: AnalysisResult, fbp: FinancialsByPeriod) -> tuple[Decimal | None, str]:
    """02/FORMÜL-16, İLKE-30: (Kısa+Uzun Vadeli Toplam Yükümlülük)/Özkaynak
    -- mevcut dar `debt_to_equity`'den (SADECE finansal borç) YAPISAL
    OLARAK FARKLI bir soruya cevap verir, YERİNE GEÇMEZ, YANINA eklenir.

    K3a DÜZELTMESİ (quant_denetim_01.md, KALİBRASYONLA DOĞRULANDI): BİST
    sanayi'de 4/167 şirket negatif özkaynağa sahip, guard OLMADAN oran
    min=-39,70 gibi BÜYÜK NEGATİF değerler üretip YANLIŞLIKLA "<1 güçlü"
    bandına düşüyordu (derin sıkıntıdaki şirket EN YÜKSEK puanı alıyordu) --
    `equity<=0` ise None döner. K4 BİRİM UYARISI: x-katı oran, `oran_str`
    ile formatlanır (YÜZDE DEĞİL).

    CANLI hata düzeltmesi (kullanıcı raporu, SAHOL PD/DD -- bkz.
    isyatirim.STANDARD_ITEM_MAP_XI_29["equity"] yorumu): `equity` ARTIK ana
    ortaklık-only; payda küçüldüğü için azınlık payı büyük şirketlerde
    (SAHOL gibi) bu oran BİRAZ ARTAR (daha muhafazakar/YÜKSEK kaldıraç
    gösterir) -- kontrol gücü olan hissedarın gerçek yükümlülük/özkaynak
    maruziyetini yansıtır, hata değildir (bkz. NCAV/ROE ile AYNI ilke,
    calculator.py roe_annualized yorumu)."""
    equity = analysis.balance_sheet.equity.current
    if equity is None or equity <= 0:
        return None, "özkaynak negatif/sıfır, toplam yükümlülük/özkaynak oranı işaretsiz/anlamsız, bileşen atlandı."

    latest = fbp.get(analysis.latest_period, {})
    stl = latest.get("short_term_liabilities")
    ltl = latest.get("long_term_liabilities")
    if stl is None or ltl is None:
        return None, "kısa/uzun vadeli toplam yükümlülük verisi eksik, bileşen atlandı."

    oran = (stl + ltl) / equity
    guclu, zayif = Decimal(1), Decimal(2)
    if oran < guclu:
        skor = _lerp_score(oran, Decimal(0), guclu, Decimal(10), Decimal(7))
    elif oran <= zayif:
        skor = _lerp_score(oran, guclu, zayif, Decimal(7), Decimal(4))
    else:
        skor = _lerp_score(oran, zayif, zayif * 3, Decimal(4), Decimal(0))
    return (
        skor,
        f"toplam yükümlülük/özkaynak (geniş tanım, ticari borç+tahakkuk dahil) {oran_str(oran)} -- mevcut dar "
        "borç/özkaynak oranının YANINA eklenir, YERİNE GEÇMEZ.",
    )


def _skor_merton(merton: MertonResult | None) -> tuple[Decimal | None, str]:
    """03/İLKE-441-444, FORMÜL-171/172: Merton'un opsiyon-teorik özkaynak
    çerçevesi -- kaba bant (EDF<=%2 güçlü, %2-10 izlenmeli, >%10 risk
    sinyali), Damodaran Tablo 17.1 kredi notu-temerrüt eşleşmesiyle KABACA
    hizalı. `merton is None` ise (fiyat oynaklığı serisi eksik/yeni halka
    arz) bileşen atlanır."""
    if merton is None:
        return None, "Merton temerrüt olasılığı hesaplanamadı (fiyat oynaklığı serisi eksik veya yeni halka arz olabilir), bileşen atlandı."
    edf = merton.default_probability_pct
    dusuk, yuksek = Decimal(2), Decimal(10)
    if edf <= dusuk:
        skor = _lerp_score(edf, Decimal(0), dusuk, Decimal(10), Decimal(7))
    elif edf <= yuksek:
        skor = _lerp_score(edf, dusuk, yuksek, Decimal(7), Decimal(3))
    else:
        skor = _lerp_score(edf, yuksek, yuksek * 4, Decimal(3), Decimal(0))
    return (
        skor,
        f"Merton temerrüt olasılığı (EDF, sentetik/dolaylı gösterge -- faiz karşılama oranı verisi eksikliği "
        f"nedeniyle) {format_percent_tr(edf, decimals=2)} (mesafe-i temerrüt {_num_str(merton.distance_to_default)} std. sapma).",
    )


# --- Faiz Karşılama Oranı (docs/spec/spec_yeni_bilesenler_agirliklandirma.md §2) -----------------------------------------------------
#
# Damodaran Tablo 2.4 (03/Tablo 2.4, FORMÜL-19) -- 14-kademeli sentetik
# kredi notu bant tablosu, CANLI kitap metninden BİREBİR alındı (spec §2
# Formüller bölümü). (alt sınır, üst sınır, alt puan, üst puan, kredi notu
# etiketi) -- küçükten büyüğe SIRALI, ardışık bantlar arasında `_lerp_score`
# ile YUMUŞATILIR (mevcut motorun sürekli-skor felsefesiyle TUTARLI).
_DAMODARAN_FAIZ_KARSILAMA_BANTLARI: tuple[tuple[Decimal, Decimal, Decimal, Decimal, str], ...] = (
    (Decimal(0), Decimal("0.50"), Decimal("0.0"), Decimal("0.5"), "D"),
    (Decimal("0.50"), Decimal("0.80"), Decimal("0.5"), Decimal("1.0"), "C"),
    (Decimal("0.80"), Decimal("1.25"), Decimal("1.0"), Decimal("1.5"), "CC"),
    (Decimal("1.25"), Decimal("1.50"), Decimal("1.5"), Decimal("2.0"), "CCC"),
    (Decimal("1.50"), Decimal("2.00"), Decimal("2.0"), Decimal("3.0"), "B-"),
    (Decimal("2.00"), Decimal("2.50"), Decimal("3.0"), Decimal("4.0"), "B"),
    (Decimal("2.50"), Decimal("3.00"), Decimal("4.0"), Decimal("5.0"), "B+"),
    (Decimal("3.00"), Decimal("3.50"), Decimal("5.0"), Decimal("5.5"), "BB"),  # Graham sanayi "en kötü 5x" ALTI burada başlar
    (Decimal("3.50"), Decimal("4.00"), Decimal("5.5"), Decimal("6.0"), "BB+"),
    (Decimal("4.00"), Decimal("4.50"), Decimal("6.0"), Decimal("6.5"), "BBB"),
    (Decimal("4.50"), Decimal("6.00"), Decimal("6.5"), Decimal("7.5"), "A-"),
    (Decimal("6.00"), Decimal("7.50"), Decimal("7.5"), Decimal("8.0"), "A"),  # Graham sanayi "en iyi 7x" ile ÇAPRAZ TUTARLI
    (Decimal("7.50"), Decimal("9.50"), Decimal("8.0"), Decimal("9.0"), "A+"),
    (Decimal("9.50"), Decimal("12.50"), Decimal("9.0"), Decimal("10.0"), "AA"),
)


def _skor_faiz_karsilama(interest_expense_to_operating_profit_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """03/Tablo 2.4, FORMÜL-19 (Interest Coverage Ratio) -- Faiz Karşılama
    Oranı = FVÖK (Faaliyet Kârı ile YAKLAŞIK)/Faiz Gideri, KALİTE merceğinin
    §1 bileşeni olan `interest_expense_to_operating_profit_pct`'in (AYNI ham
    veri, FARKLI formül -- TERS çevrilmiş hali) üzerinden türetilir; yeni
    bir fetcher/alan GEREKMEZ (spec §2 Formüller bölümü).

    Kaynak: 03/Tablo 2.4, FORMÜL-19; 01/FORMÜL-18 (Graham'ın sanayi 7x/5x
    bandı, ÇAPRAZ referans olarak bant etiketlerinde anılır); 02/FORMÜL-05
    (Buffett <%15 -- KALİTE'deki §1 bileşeniyle AYNI ham veri, FARKLI
    formül, çift-sayma SAYILMAZ -- "TEK satırda BİRLEŞTİRİLDİ" ilkesi).

    Damodaran Tablo 2.4'ün kendisi "2004, küçük sanayi şirketleri" için
    kalibre edilmiştir (kitap metninde AÇIKÇA yazılı) -- mega-cap NASDAQ
    şirketlerinde bu bantlar KATI olmayabilir, kart bu sınırlamayı AÇIKÇA
    taşır (uydurma yapılmadan, kitabın KENDİ sınırlaması aktarılır)."""
    if interest_expense_to_operating_profit_pct is None or interest_expense_to_operating_profit_pct <= 0:
        return None, (
            "faiz karşılama oranı hesaplanamadı (faiz gideri sıfır/negatif/net faiz geliri olarak birleşik "
            "raporlanmış olabilir -- oran anlamsız -- veya bu veri sadece NASDAQ şirketlerinde mevcut), "
            "bileşen atlandı."
        )
    oran = Decimal(100) / interest_expense_to_operating_profit_pct
    if oran > Decimal("12.50"):
        skor, etiket = Decimal("10.0"), "AAA"
    else:
        skor, etiket = None, None
        for alt, ust, puan_alt, puan_ust, bant_etiketi in _DAMODARAN_FAIZ_KARSILAMA_BANTLARI:
            if oran <= ust:
                skor = _lerp_score(oran, alt, ust, puan_alt, puan_ust)
                etiket = bant_etiketi
                break
        if skor is None:  # oran < 0 -- fiilen imkansız (guard yukarıda), guvence icin
            skor, etiket = Decimal("0.0"), "D"
    return skor, (
        f"faiz karşılama oranı (FVÖK/faiz gideri, Faiz Gideri/Faaliyet Kârı oranından türetilmiş) {oran_str(oran)} "
        f"-- Damodaran Tablo 2.4 sentetik kredi notu bandı: {etiket}. Bu bant (2004, küçük/orta ölçekli sanayi "
        "şirketleri için kalibre edilmiştir) mega-cap şirketlerde gevşek yorumlanmalıdır."
    )


def hesapla_guvenlik_mercegi(girdi: GuvenlikGirdisi) -> LensSonucu:
    cfg = scorer.CONFIG[girdi.template]
    r = girdi.analysis.ratios
    equity = girdi.analysis.balance_sheet.equity.current
    assets = girdi.analysis.balance_sheet.total_assets.current

    kaldirac = scorer._skor_kaldirac(r.net_debt_to_ebitda, cfg["kaldirac"])
    bilanco = scorer._skor_bilanco_kalitesi(r.current_ratio, _safe_pct(equity, assets), cfg["bilanco_kalitesi"])
    piotroski = _skor_piotroski(girdi.piotroski)
    tyo = _skor_toplam_yukumluluk_ozkaynak(girdi.analysis, girdi.financials_by_period)
    merton = _skor_merton(girdi.merton)
    faiz_karsilama = _skor_faiz_karsilama(r.interest_expense_to_operating_profit_pct)

    bilesenler = [
        ("Kaldıraç (Net Borç/FAVÖK)", Decimal("29"), kaldirac),
        ("Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)", Decimal("18"), bilanco),
        ("Piotroski F-Skoru", Decimal("24"), piotroski),
        ("Toplam Yükümlülük/Özkaynak (geniş tanım)", Decimal("12"), tyo),
        ("Merton Temerrüt Olasılığı (EDF)", Decimal("7"), merton),
        ("Faiz Karşılama Oranı", Decimal("10"), faiz_karsilama),
    ]
    return _agirlik_dagit_ve_hesapla(girdi.analysis.ticker, girdi.analysis.latest_period, "güvenlik", bilesenler)


# --- Banka/sigorta/finansman şablonu (spec §Sektör ayarlaması madde 1) -----------------------------------------------------
#
# Kaldıraç (Net Borç/FAVÖK) ve Toplam Yükümlülük/Özkaynak KAVRAMSAL OLARAK
# UYGULANAMAZ (02/İLKE-31: bankalar iş modeli gereği ~10:1 kaldıraçla
# NORMAL çalışır -- "net borç"/FAVÖK kavramı da mevduat/kredi=iş modelinin
# kendisi olduğu için ANLAMSIZDIR). Bu şablonlarda GÜVENLİK merceği
# `özkaynak_aktif_orani` (zaten CAMELS-esinli `scorer.CONFIG["banka"]`
# içinde MEVCUT, "Capital Adequacy" ruhuna uygun bir proxy) + Piotroski
# BENZERİ bir finansal sağlık taraması (spec'in kendi ifadesiyle "bankalar
# için henüz YOK, iskelet" -- fundamental_screens.py Piotroski'yi SADECE
# BİST XI_29 sanayi için hesaplar, bu yüzden burada HER ZAMAN None/YAPISAL
# OLARAK YOK) ile ÇALIŞIR. Nominal ağırlıklar İCAT EDİLMEDİ -- sanayi
# GÜVENLİK tablosundaki (spec_mercek_guvenlik.md) MEVCUT "Bilanço Kalitesi"
# (%20, özkaynak/varlık bunun YARISIdır) ve "Piotroski F-Skoru" (%25)
# ağırlıkları AYNI 4:5 ORANIYLA, ama %100'e TAMAMLANACAK şekilde YENİDEN
# YAZILIR (20/45*100=%44,44, 25/45*100=%55,56) -- SADELİKLE (20,25) DEĞİL
# çünkü `_agirlik_dagit_ve_hesapla`'nın `min_veri_agirlik_yuzdesi=%50`
# kontrolü nominal ağırlıkların TOPLAMDA %100'e tamamlandığı VARSAYIMIYLA
# çalışır (bkz. `lens_kalite.hesapla_kalite_mercegi_banka`'daki AYNI
# düzeltme, bu turda İKİ yerde de giderildi) -- Piotroski HER ZAMAN None
# döndüğü için `_agirlik_dagit_ve_hesapla` ağırlığını OTOMATİK olarak
# özkaynak/aktif oranına (%100) devreder (banka/finansman'da); sigorta'da
# özkaynak/aktif oranı da None'dır (UFRS_K şemasında `total_assets` hiç
# YOK) -- bu durumda mercek dürüstçe "YETERSİZ VERİ" döner (Kural 3:
# uydurma yapılmaz, spec_bilesik_skor.md'nin "eksik ama dürüst" ilkesi).


def _skor_ozkaynak_aktif_orani(oran_pct: Decimal | None) -> tuple[Decimal | None, str]:
    """CAMELS "Capital Adequacy" ruhuna uygun proxy -- `scorer.CONFIG["banka"]
    ["ozkaynak_aktif_orani"]` eşikleri (güçlü≥%12, orta≥%8, tavan%18) AYNEN
    kullanılır (regülatif Sermaye Yeterlilik Oranı'nın YERİNE GEÇMEZ, bkz.
    scorer.score_bank() docstring'i -- v1'deki AYNI proxy v2'ye taşınır)."""
    if oran_pct is None:
        return (
            None,
            "özkaynak/aktif oranı hesaplanamadı (bu şirket türünde toplam varlık verisi eksik/uygulanamaz), "
            "bileşen atlandı.",
        )
    cfg = scorer.CONFIG["banka"]["ozkaynak_aktif_orani"]
    return seviye_trend_skoru_v2(
        "Özkaynak/aktif oranı (sermaye yeterliliği proxy'si)", oran_pct, None,
        guclu_esik=cfg["guclu_esik"], orta_esik=cfg["orta_esik"], tavan=cfg["tavan"],
    )


def hesapla_guvenlik_mercegi_finans(
    ticker: str,
    period: tuple[int, int],
    ozkaynak_aktif_orani_pct: Decimal | None,
    piotroski: PiotroskiResult | None = None,
) -> LensSonucu:
    """Banka/sigorta/finansman şablonu -- SADECE özkaynak/aktif oranı +
    (varsa) Piotroski benzeri sağlık taraması (spec §Sektör ayarlaması
    madde 1).

    `piotroski` BU TURDA daima `None` gelir (fundamental_screens.py
    SADECE BİST XI_29 sanayi için hesaplar) -- parametre olarak TUTULDU ki
    bu iskelet ileride (spec'in kendi notu: "bankalar için henüz YOK,
    iskelet") gerçek bir Piotroski-benzeri tarama eklenirse tek satırla
    doldurulabilsin. `piotroski is None` iken bu bileşen `spec_mercek_
    kalite.md`'nin "YAPISAL OLARAK YOK -- kartta boş satır DEĞİL" ilkesiyle
    TUTARLI olarak bileşen LİSTESİNDEN TAMAMEN ÇIKARILIR (None-skorlu bir
    bileşen olarak GÖSTERİLMEZ) -- aksi halde HİÇBİR ZAMAN dolmayacak bir
    nominal ağırlık (%55,56) sürekli "veri kapsamını" %50 eşiğinin altında
    tutar ve mercek asla `data_sufficient=True` OLAMAZDI (CANLI doğrulandı,
    `lens_kalite.hesapla_kalite_mercegi_banka`'daki AYNI sınıf hatanın bir
    başka örneği)."""
    oao = _skor_ozkaynak_aktif_orani(ozkaynak_aktif_orani_pct)
    if piotroski is not None:
        piyo = _skor_piotroski(piotroski)
        bilesenler = [
            # 20:25 (sanayi güvenlik tablosundaki Bilanço Kalitesi:Piotroski
            # oranı) AYNI 4:5 ORANIYLA, %100'e tamamlanacak şekilde: 44,44/55,56.
            ("Özkaynak/Aktif Oranı (sermaye yeterliliği proxy'si)", Decimal("44.44"), oao),
            ("Piotroski Benzeri Finansal Sağlık Taraması", Decimal("55.56"), piyo),
        ]
    else:
        bilesenler = [
            ("Özkaynak/Aktif Oranı (sermaye yeterliliği proxy'si)", Decimal("100"), oao),
        ]
    return _agirlik_dagit_ve_hesapla(ticker, period, "güvenlik_finans", bilesenler)
