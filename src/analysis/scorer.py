"""Kural tabanli, agirlikli 0-10 puanlama motoru -- SAF MATEMATIK.

Bu modulde HICBIR LLM cagrisi yoktur. Gerekce metinleri kural icinde f-string
ile uretilir. Girdi olarak `src.analysis.calculator.AnalysisResult` alir (bu
modul calculator'i import EDER, ama src.fetchers.*/src.db.* hicbir modulu
import ETMEZ).

Fiyat/degerleme (F/K, PD/DD) ve bankaya/sigortaya ozgu metrikler (net faiz
marji, prim buyumesi, teknik denge marji, sermaye yeterlilik orani)
AnalysisResult icinde YOKTUR -- calculator.py bunlari uretmez, cunku fiyat
verisi ve sektore ozgu KAP kalemleri bu projenin fetcher katmaninda henuz
yok. Bu yuzden ilgili fonksiyonlara ayri, istege bagli parametreler olarak
verilir; verilmezse o bilesen ATLANIR ve agirligi diger bilesenlere
ORANTISAL olarak yeniden dagitilir (boylece toplam efektif agirlik her
zaman %100'e tamamlanir).

Esikler ve agirliklar asagidaki CONFIG sozlugunde toplanmistir; elle
ayarlanabilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.analysis.calculator import AnalysisResult
from src.formatting import format_percent_tr

# --- CONFIG: esikler ve agirliklar (tek yerden ayarlanir) -----------------

CONFIG: dict = {
    "sanayi": {
        # FAVOK marji seviyesi + istikrari (>25=25).
        "nakit_uretimi": {
            "agirlik": Decimal("21"),
            "guclu_esik": Decimal("20"),  # % ustu "guclu"
            "orta_esik": Decimal("10"),  # % altinda "dusuk"
            "tavan": Decimal("30"),  # bu marja ulasinca skor tam 10
        },
        # Net borc/FAVOK (TTM).
        "kaldirac": {
            "agirlik": Decimal("17"),
            "cok_iyi_esik": Decimal("1"),
            "iyi_esik": Decimal("2.5"),
            "orta_esik": Decimal("4"),
            "tavan": Decimal("8"),  # bu oranin ustunde skor 0'a sabitlenir
        },
        # Net marj seviyesi + YoY yonu.
        "karlilik": {
            "agirlik": Decimal("13"),
            "guclu_esik": Decimal("15"),
            "orta_esik": Decimal("5"),
            "tavan": Decimal("25"),
        },
        # Hasilat YoY (reel) buyumesi.
        "buyume": {
            "agirlik": Decimal("13"),
            "guclu_esik": Decimal("15"),
            "orta_esik": Decimal("0"),
            "tavan": Decimal("30"),
            "taban": Decimal("-20"),  # bu buyumenin altinda skor 0'a sabitlenir
        },
        # F/K ve PD/DD.
        "degerleme": {
            "agirlik": Decimal("17"),
            "fk_ucuz": Decimal("8"),
            "fk_makul": Decimal("15"),
            "fk_pahali": Decimal("25"),
            "fk_tavan": Decimal("40"),
            "pddd_ucuz": Decimal("1"),
            "pddd_makul": Decimal("2.5"),
            "pddd_pahali": Decimal("5"),
            "pddd_tavan": Decimal("8"),
        },
        # Cari oran + ozkaynak/varlik orani.
        "bilanco_kalitesi": {
            "agirlik": Decimal("4"),
            "cari_oran_iyi": Decimal("1.5"),
            "cari_oran_orta": Decimal("1"),
            "ozkaynak_varlik_iyi": Decimal("40"),
            "ozkaynak_varlik_orta": Decimal("25"),
        },
        # Ozkaynak karliligi (ROE, yillıklandirilmis TTM net kar / guncel
        # ozkaynak) -- Graham/Buffett/Munger/Lynch/O'Neil'in ORTAK vurgusu
        # (bkz. SCORING_METHODOLOGY.md); veri zaten calculator.Ratios.roe_annualized
        # icinde hesapli (bankada/sigortada zaten kullaniliyordu, sanayi
        # sablonunda EKSIKTI). Esikler banka sablonundakinden (guclu %20)
        # biraz DUSUK tutuldu -- sanayi/holding sirketlerinde ozkaynak
        # karliligi bankalara gore yapisal olarak daha dusuk seyreder.
        "ozkaynak_karliligi": {
            "agirlik": Decimal("15"),
            "guclu_esik": Decimal("15"),
            "orta_esik": Decimal("10"),
            "tavan": Decimal("25"),
        },
    },
    # Banka/sigorta icin basit iskelet sablonlar -- gercek veriyle ileride kalibre edilecek.
    "sigorta": {
        "prim_buyumesi": {"agirlik": Decimal("25"), "guclu_esik": Decimal("15"), "orta_esik": Decimal("0"), "tavan": Decimal("40"), "taban": Decimal("-20")},
        "teknik_denge_marji": {"agirlik": Decimal("25"), "guclu_esik": Decimal("5"), "orta_esik": Decimal("0"), "tavan": Decimal("15"), "taban": Decimal("-15")},
        "ozkaynak_karliligi": {"agirlik": Decimal("25"), "guclu_esik": Decimal("25"), "orta_esik": Decimal("10"), "tavan": Decimal("40")},
        # CANLI HATA (kullanıcı raporu, 2026-08-03): bu alt sözlükte SADECE
        # "agirlik" vardı, fk_ucuz/fk_makul/... eşikleri YOKTU --
        # _skor_degerleme() fiyat verisi olan (F/K veya PD/DD dolu) HERHANGİ
        # bir sigorta şirketinde `KeyError: 'fk_ucuz'` ile ÇÖKÜYORDU.
        # Eşikler Türkiye sigorta şirketlerinin (ANSGR/TURSG gibi) genel
        # F/K ~5-15x, PD/DD ~1-3x aralığında seyretme eğilimine göre KABACA
        # seçildi -- "sanayi" şablonundan KOPYALANMADI (sigortada tipik
        # çarpanlar farklıdır) ama gerçek veriyle KALİBRE EDİLMEDİ (bkz.
        # 06_BILINEN_SORUNLAR.md §B8, hâlâ açık).
        "degerleme": {
            "agirlik": Decimal("25"),
            "fk_ucuz": Decimal("6"),
            "fk_makul": Decimal("10"),
            "fk_pahali": Decimal("15"),
            "fk_tavan": Decimal("25"),
            "pddd_ucuz": Decimal("1"),
            "pddd_makul": Decimal("2"),
            "pddd_pahali": Decimal("3.5"),
            "pddd_tavan": Decimal("6"),
        },
    },
    # CAMELS (Capital/Assets/Management/Earnings/Liquidity/Sensitivity)
    # cercevesine dayanir -- bkz. scorer.score_bank() docstring'i. Regulatuar
    # Sermaye Yeterlilik Orani (Tier1+2/RWA) bu veri kaynaginda YOK (İş
    # Yatirim'in MaliTablo uc noktasinda bulunmuyor); "ozkaynak_aktif_orani"
    # CAMELS'in "Capital Adequacy" ruhuna uygun, TAMAMEN hesaplanabilen bir
    # YAKLASIMdir (regulatuar CAR'in YERINE GECMEZ).
    "banka": {
        "ozkaynak_karliligi": {"agirlik": Decimal("25"), "guclu_esik": Decimal("20"), "orta_esik": Decimal("10"), "tavan": Decimal("35")},
        "net_faiz_marji": {"agirlik": Decimal("20"), "guclu_esik": Decimal("5"), "orta_esik": Decimal("2"), "tavan": Decimal("10"), "taban": Decimal("-5")},
        # CAMELS "Earnings": NIM ile BIRLIKTE onerilen aktif karliligi (ROA).
        "aktif_karliligi": {"agirlik": Decimal("20"), "guclu_esik": Decimal("2.5"), "orta_esik": Decimal("1"), "tavan": Decimal("4"), "taban": Decimal("-2")},
        "ozkaynak_aktif_orani": {"agirlik": Decimal("15"), "guclu_esik": Decimal("12"), "orta_esik": Decimal("8"), "tavan": Decimal("18")},
        # CANLI HATA (kullanıcı raporu, 2026-08-03, ISCTR): bu alt sözlükte
        # SADECE "agirlik" vardı -- _skor_degerleme() fiyat verisi olan
        # (F/K veya PD/DD dolu) HERHANGİ bir banka için `KeyError: 'fk_ucuz'`
        # ile ÇÖKÜYORDU (canlı Telegram logunda doğrulandı). Eşikler
        # Türkiye bankalarının (AKBNK/GARAN/ISCTR/YKBNK gibi) tipik olarak
        # DÜŞÜK çarpanlarla (F/K ~3-8x, PD/DD ~0.5-1.5x -- makro risk primi
        # yüzünden sanayi şirketlerinden YAPISAL OLARAK ucuz) işlem görme
        # eğilimine göre KABACA seçildi -- "sanayi" şablonundan (F/K ucuz=8)
        # KOPYALANMADI, o eşik bankalar için ÇOK YÜKSEK olurdu (her banka
        # "ucuz" görünürdü). Gerçek veriyle KALİBRE EDİLMEDİ (bkz.
        # 06_BILINEN_SORUNLAR.md §B8, hâlâ açık).
        "degerleme": {
            "agirlik": Decimal("20"),
            "fk_ucuz": Decimal("4"),
            "fk_makul": Decimal("7"),
            "fk_pahali": Decimal("10"),
            "fk_tavan": Decimal("15"),
            "pddd_ucuz": Decimal("0.7"),
            "pddd_makul": Decimal("1.2"),
            "pddd_pahali": Decimal("2"),
            "pddd_tavan": Decimal("3"),
        },
    },
    # Tasarruf Finansman Sirketleri (XI_29K, orn. KTLEV) icin sablon --
    # bkz. calculator.analyze_financing() docstring'i. "cari oran"/"kaldirac"
    # gibi sanayi/banka rasyoları BURADA YOK (girdi kalemleri Kural 3 geregi
    # haritaya eklenmedi) -- bunun yerine Net Kâr Marjı + ROE + ROA + Ozkaynak/
    # Aktif Orani + Degerleme (banka sablonuyla AYNI ilke, F/K-PD/DD dar
    # esikleri). Esikler HENUZ gercek veriyle KALIBRE EDILMEDI (yeni sirket
    # tipi, sadece KTLEV ile canli dogrulandi) -- bkz. 06_BILINEN_SORUNLAR.md.
    "finansman": {
        "karlilik": {"agirlik": Decimal("20"), "guclu_esik": Decimal("15"), "orta_esik": Decimal("5"), "tavan": Decimal("30")},
        "ozkaynak_karliligi": {"agirlik": Decimal("25"), "guclu_esik": Decimal("20"), "orta_esik": Decimal("10"), "tavan": Decimal("35")},
        "aktif_karliligi": {"agirlik": Decimal("20"), "guclu_esik": Decimal("5"), "orta_esik": Decimal("2"), "tavan": Decimal("10"), "taban": Decimal("-5")},
        "ozkaynak_aktif_orani": {"agirlik": Decimal("15"), "guclu_esik": Decimal("15"), "orta_esik": Decimal("8"), "tavan": Decimal("25")},
        "degerleme": {
            "agirlik": Decimal("20"),
            "fk_ucuz": Decimal("5"),
            "fk_makul": Decimal("9"),
            "fk_pahali": Decimal("13"),
            "fk_tavan": Decimal("20"),
            "pddd_ucuz": Decimal("1"),
            "pddd_makul": Decimal("1.8"),
            "pddd_pahali": Decimal("3"),
            "pddd_tavan": Decimal("5"),
        },
    },
    # NASDAQ/ABD (US_GAAP) sanayi sirketleri icin sablon -- Faz 10. "sanayi"
    # sablonunu TABAN ALIR (bkz. score_industrial_us()), sadece PIYASAYA OZGU
    # (para birimi/enflasyon/carpan seviyesi ile ilgili) esikler kalibre
    # edildi. Detayli gerekce: bilanco-radar/SCORING_METHODOLOGY.md.
    "abd_sanayi": {
        # FAVOK marji kalitesi PIYASADAN/PARA BIRIMINDEN BAGIMSIZ operasyonel
        # bir gostergedir (yuksek FAVOK marji her ulkede "iyi" demektir) --
        # "sanayi" sablonuyla AYNI esikler kullanildi (bilinçli, degistirilmedi).
        "nakit_uretimi": {
            "agirlik": Decimal("21"),
            "guclu_esik": Decimal("20"),
            "orta_esik": Decimal("10"),
            "tavan": Decimal("30"),
        },
        # Net Borc/FAVOK: kredi derecelendirme kuruluslarinin (Moody's/S&P)
        # ULKE/PARA BIRIMINDEN BAGIMSIZ kullandigi EVRENSEL banlardir
        # (<1,5x güçlü yatirim yapilabilir, 1,5-3x saglam YY, 3-4x zayif
        # YY/ust HY, 4x+ kaldiracli/spekulatif) -- gorev talimati geregi
        # "sanayi" sablonuyla BIREBIR AYNI birakildi.
        "kaldirac": {
            "agirlik": Decimal("17"),
            "cok_iyi_esik": Decimal("1"),
            "iyi_esik": Decimal("2.5"),
            "orta_esik": Decimal("4"),
            "tavan": Decimal("8"),
        },
        # Net marj kalitesi de PIYASADAN BAGIMSIZ -- "sanayi" ile AYNI birakildi.
        "karlilik": {
            "agirlik": Decimal("13"),
            "guclu_esik": Decimal("15"),
            "orta_esik": Decimal("5"),
            "tavan": Decimal("25"),
        },
        # Hasilat YoY buyumesi: "sanayi" sablonunda NOMINAL TRY buyumesi
        # yuksek yerel enflasyonu (bazi yillarda %40-60+) ZIMNEN icerir --
        # "guclu" %15 nominal buyume REEL terimde cok dusuk/negatif olabilir.
        # analyze_us() NOMINAL USD buyumesi kullanir (bkz. docstring'i) --
        # ABD TUFE tipik %2-4 (TL'ye kiyasla ONEMSIZ), bu yuzden nominal USD
        # buyume ZATEN yaklasik REEL buyumeye esittir -- esikler enflasyon
        # kaynakli YAPAY sisirme OLMADAN, dogrudan gercek performansi
        # yansitsin diye "sanayi"dekinden DUSUK tutuldu.
        "buyume": {
            "agirlik": Decimal("13"),
            "guclu_esik": Decimal("10"),
            "orta_esik": Decimal("0"),
            "tavan": Decimal("25"),
            "taban": Decimal("-15"),
        },
        # Degerleme: CANLI arastirildi (2026-08, GuruFocus/Multpl/MacroMicro --
        # bkz. SCORING_METHODOLOGY.md kaynak listesi). S&P 500 trailing F/K
        # ~25 (tarihsel ORTALAMA ~19,7-25,4; 1871'den beri MEDYAN ~18,0),
        # PD/DD ~5,9-6,0 (tarihsel MEDYAN ~2,9). "sanayi"nin "ucuz F/K <8"
        # esigi ABD piyasasinda NEREDEYSE HICBIR saglikli buyuk sirkette
        # gorulmez (yapisal olarak DAHA DUSUK sermaye maliyeti + DAHA YUKSEK
        # buyume beklentisi carpanlari YUKARI ceker) -- esikler ABD piyasa
        # medyan/ortalamalarina gore YUKARI kaydirildi.
        "degerleme": {
            "agirlik": Decimal("17"),
            "fk_ucuz": Decimal("12"),
            "fk_makul": Decimal("20"),
            "fk_pahali": Decimal("30"),
            "fk_tavan": Decimal("50"),
            "pddd_ucuz": Decimal("1.5"),
            "pddd_makul": Decimal("3"),
            "pddd_pahali": Decimal("6"),
            "pddd_tavan": Decimal("12"),
        },
        # Cari oran + ozkaynak/varlik orani -- muhasebe rasyolaridir, PARA
        # BIRIMINDEN/PIYASADAN bagimsiz -- "sanayi" ile AYNI birakildi.
        "bilanco_kalitesi": {
            "agirlik": Decimal("4"),
            "cari_oran_iyi": Decimal("1.5"),
            "cari_oran_orta": Decimal("1"),
            "ozkaynak_varlik_iyi": Decimal("40"),
            "ozkaynak_varlik_orta": Decimal("25"),
        },
        # ROE: Graham/Buffett/Munger/Lynch/O'Neil ölçütleri PIYASADAN
        # BAGIMSIZ evrensel kabul edilir -- "sanayi" ile AYNI birakildi.
        # BILINEN SINIR: sermaye-hafif/geri-alim-agirlikli ABD teknoloji
        # sirketlerinde (orn. AAPL) ozkaynak agresif hisse geri alimlariyla
        # kucultulmus olabilir, bu da ROE'yi YAPAY sekilde COK YUKSEK
        # gosterebilir (AAPL CANLI dogrulandi: ROE %100'un UZERINDE cikiyor,
        # bu "asiri karli" degil "dusuk ozkaynak tabani" anlamina gelir) --
        # tek basina asiri yuksek ROE, dusuk ozkaynak/agresif geri alim
        # sinyaliyle BIRLIKTE yorumlanmalidir (bkz. SCORING_METHODOLOGY.md).
        "ozkaynak_karliligi": {
            "agirlik": Decimal("15"),
            "guclu_esik": Decimal("15"),
            "orta_esik": Decimal("10"),
            "tavan": Decimal("25"),
        },
    },
    # Toplam skora gore rozet esikleri (sol-kapali: 8 SAGLAM'a dahildir, 6 DENGELI'ye dahildir, vb.)
    "rozet_esikleri": {
        "saglam": Decimal("8"),
        "dengeli": Decimal("6"),
        "karisik": Decimal("4"),
    },
    # CANLI HATA (kullanici raporu, ASTS/AST SpaceMobile, §B17 -- 06_BILINEN_
    # SORUNLAR.md): bilesenlerin NEREDEYSE TAMAMI (agirlik toplaminin %96'si)
    # "veri yok" oldugunda, SADECE %4 agirlikli "Bilanço Kalitesi" bilesenin
    # 10/10 almasi yeniden-dagitim yuzunden toplam skoru "10,00/10 SAĞLAM"
    # gosteriyordu -- Kural 3'e ("yanlis rakamdan iyidir") DOGRUDAN aykiri.
    # Cevaplanan bilesenlerin NOMINAL agirlik toplami bu esigin ALTINDAYSA
    # (_agirlik_dagit_ve_hesapla, bkz. asagisi) rozet normal SAGLAM/DENGELI/
    # KARISIK/RISKLI OLCEGINE GIRMEZ, "YETERSİZ VERİ" doner -- olcum orneklemi
    # cok kucukken olumlu (ozellikle "SAGLAM") bir etiket ASLA uretilmez. %50
    # (agirlik toplaminin en az yarisi cevaplanmis olmali) muhafazakar/
    # kasitli secildi -- kullanicinin onerdigi %40-50 araliginin UST ucu.
    "min_veri_agirlik_yuzdesi": Decimal("50"),
}

YETERSIZ_VERI_ROZETI = "YETERSİZ VERİ"


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class ValuationInput:
    """Fiyat verisine dayali degerleme girdisi -- AnalysisResult icinde
    bulunmaz, disaridan (fiyat + hisse sayisi biliniyorsa) verilir."""

    pe_ratio: Decimal | None = None  # F/K
    pb_ratio: Decimal | None = None  # PD/DD


@dataclass(frozen=True)
class ComponentScore:
    name: str
    score: Decimal | None  # 0-10; None ise veri yok, bilesen atlandi
    weight_nominal: Decimal  # CONFIG'deki orijinal agirlik (yuzde puani)
    weight_effective: Decimal  # atlanan bilesenler cikarilip yeniden dagitilmis agirlik (yuzde)
    contribution: Decimal  # skor * efektif_agirlik / 100 (0-10 olcekli katki)
    reasoning_tr: str


@dataclass(frozen=True)
class ScoreResult:
    ticker: str
    period: tuple[int, int]
    template: str  # "sanayi_holding" | "sigorta" | "banka"
    total_score: Decimal
    badge: str
    data_coverage_pct: Decimal  # cevaplanan bilesenlerin NOMINAL agirlik toplami (0-100)
    data_sufficient: bool  # False ise badge=YETERSIZ_VERI_ROZETI, total_score GUVENILIR DEGIL
    components: list[ComponentScore] = field(default_factory=list)


# --- Genel yardimcilar -----------------------------------------------------


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    return max(lo, min(hi, value))


def _lerp_score(value: Decimal, x0: Decimal, x1: Decimal, y0: Decimal, y1: Decimal) -> Decimal:
    """value'yu [x0,x1] araligindan [y0,y1] puan araligina dogrusal esler;
    value araligin disindaysa en yakin uca kirpilir (x1==x0 ise y0 doner)."""
    if x1 == x0:
        return y0
    t = (value - x0) / (x1 - x0)
    t = _clamp(t, Decimal(0), Decimal(1))
    return y0 + t * (y1 - y0)


def _asymptote_to(distance_beyond: Decimal, half_life: Decimal, start_score: Decimal, target_score: Decimal) -> Decimal:
    """Bir esigin OTESINDEKI mesafeye (distance_beyond >= 0) gore start_score'dan
    target_score'a dogru YUMUSAKCA (rasyonel/Michaelis-Menten egrisi ile) yaklasir;
    HICBIR ZAMAN target_score'a TAM ULASMAZ.

    Kullanici geri bildirimi: eski (dogrusal + kirpma) modelde bir esigin
    (orn. FAVOK marji %20) UZERINDEKI her deger, "tavan" esigine (orn. %30)
    ulasir ulasmaz SABIT 10 puan aliyordu -- yani FAVOK marji %30 olan sirket
    ile %70 olan sirket AYNI puani (10/10) aliyordu, ki bu adaletsizdi (marj
    ne kadar yuksek olursa olsun puan hep ayni). Bu fonksiyon esikten sonra
    da SUREKLI ARTAN (ama giderek yavaslayan) bir puan uretir:
      distance_beyond=0            -> start_score (esikte sureklilik, sicrama yok)
      distance_beyond=half_life    -> start_score ile target_score'un TAM ORTASI
      distance_beyond -> sonsuz    -> target_score'a YAKLASIR, asla esitlenmez
    """
    if half_life <= 0:
        return target_score
    if distance_beyond <= 0:
        return start_score
    t = distance_beyond / (distance_beyond + half_life)
    return start_score + (target_score - start_score) * t


def _num_str(value: Decimal | None) -> str:
    if value is None:
        return "-"
    return f"{value.quantize(Decimal('0.1'))}".replace(".", ",")


def _safe_pct(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator * 100


def _badge(total_score: Decimal) -> str:
    esik = CONFIG["rozet_esikleri"]
    if total_score >= esik["saglam"]:
        return "SAĞLAM"
    if total_score >= esik["dengeli"]:
        return "DENGELİ"
    if total_score >= esik["karisik"]:
        return "KARIŞIK"
    return "RİSKLİ"


def _seviye_trend_skoru(
    etiket: str,
    seviye: Decimal | None,
    trend_puan: Decimal | None,
    guclu_esik: Decimal,
    orta_esik: Decimal,
    tavan: Decimal,
    taban: Decimal = Decimal(0),
) -> tuple[Decimal | None, str]:
    """Bir seviye (marj/oran/buyume, yuzde) + istege bagli YoY egilim puanina
    (onceki yila gore puan degisimi) gore 0-10 skor uretir.

    Oncelik sirasi:
      1. seviye None ise -> None (bilesen atlanir)
      2. trend_puan < 0 (bozuluyor) -> [0,4] araligi (seviyeye gore kaydirilir)
      3. seviye > guclu_esik -> [8,10] araligi
      4. orta_esik <= seviye <= guclu_esik -> [5,7] araligi
      5. seviye < orta_esik -> [0,4] araligi
    trend_puan verilmezse (None) 2. adim atlanir, sadece seviyeye bakilir.
    """
    if seviye is None:
        return None, "veri yok, bileşen atlandı."

    # KULLANICI GERI BILDIRIMI: "FAVOK marji %2,7 ancak -0,2 puan bozuluyor,
    # trend olumsuz" cumlesi ne "puan"un ne anlama geldigini (gecen yila
    # gore YUZDE PUAN degisimi) ne de bunun puani NEDEN dusurdugunu acikca
    # soyluyordu. Asagidaki metin ikisini de acikca yazar.
    bozuluyor = trend_puan is not None and trend_puan < 0
    if bozuluyor:
        skor = _lerp_score(seviye, taban, orta_esik, Decimal(0), Decimal(4))
        aciklama = (
            f"{etiket} {format_percent_tr(seviye)} seviyesinde, ancak geçen yıla göre {_num_str(trend_puan)} "
            f"yüzde puan bozuluyor (kötüleşen trend) — bu gerileme düşük puanın nedenidir."
        )
    elif seviye > guclu_esik:
        # Tavanda SABIT 10'a kirpma YOK -- "tavan" artik esikten sonraki
        # yari-omur (half-life) mesafesi olarak kullanilir: seviye=tavan'da
        # puan 8 ile 10'un TAM ORTASI (9), sonrasinda 10'a YAKLASIR ama
        # asla esitlenmez (bkz. _asymptote_to docstring).
        skor = _asymptote_to(seviye - guclu_esik, tavan - guclu_esik, Decimal(8), Decimal(10))
        if trend_puan is None:
            yon = "trend verisi yok"
        elif trend_puan > 0:
            yon = "yükseliyor"
        else:
            yon = "yatay"
        aciklama = f"{etiket} {format_percent_tr(seviye)}, güçlü ve {yon}."
    elif seviye >= orta_esik:
        skor = _lerp_score(seviye, orta_esik, guclu_esik, Decimal(5), Decimal(7))
        aciklama = f"{etiket} {format_percent_tr(seviye)}, orta düzeyde."
    else:
        skor = _lerp_score(seviye, taban, orta_esik, Decimal(0), Decimal(4))
        aciklama = f"{etiket} {format_percent_tr(seviye)}, düşük."
    return skor, aciklama


def _agirlik_dagit_ve_hesapla(
    ticker: str,
    period: tuple[int, int],
    template_adi: str,
    bilesenler: list[tuple[str, Decimal, tuple[Decimal | None, str]]],
) -> ScoreResult:
    """bilesenler: (isim, nominal_agirlik, (skor_veya_None, gerekce)) listesi.

    Skoru None olan bilesenler (veri yok) ATLANIR; kalan bilesenlerin
    agirliklari, toplamlari %100'e tamamlanacak sekilde ORANTISAL olarak
    yeniden dagitilir. Hicbir bilesen hesaplanamazsa toplam skor 0 doner
    (RISKLI rozeti ile) -- sifira bolme olmaz.
    """
    mevcut_nominal_toplam = sum(agirlik for _, agirlik, (skor, _gerekce) in bilesenler if skor is not None)

    components: list[ComponentScore] = []
    toplam_puan = Decimal(0)
    for isim, nominal_agirlik, (skor, gerekce) in bilesenler:
        if skor is None:
            components.append(
                ComponentScore(
                    name=isim,
                    score=None,
                    weight_nominal=nominal_agirlik,
                    weight_effective=Decimal(0),
                    contribution=Decimal(0),
                    reasoning_tr=gerekce,
                )
            )
            continue

        efektif_agirlik = (
            (nominal_agirlik / mevcut_nominal_toplam) * Decimal(100) if mevcut_nominal_toplam > 0 else Decimal(0)
        )
        katki = skor * efektif_agirlik / Decimal(100)
        toplam_puan += katki
        components.append(
            ComponentScore(
                name=isim,
                score=skor,
                weight_nominal=nominal_agirlik,
                weight_effective=efektif_agirlik,
                contribution=katki,
                reasoning_tr=gerekce,
            )
        )

    toplam_puan = _clamp(toplam_puan, Decimal(0), Decimal(10))
    veri_yeterli = mevcut_nominal_toplam >= CONFIG["min_veri_agirlik_yuzdesi"]
    return ScoreResult(
        ticker=ticker,
        period=period,
        template=template_adi,
        total_score=toplam_puan,
        badge=_badge(toplam_puan) if veri_yeterli else YETERSIZ_VERI_ROZETI,
        data_coverage_pct=mevcut_nominal_toplam,
        data_sufficient=veri_yeterli,
        components=components,
    )


# --- Sanayi/holding bilesenleri -----------------------------------------------------


def _skor_nakit_uretimi(
    favok_marji: Decimal | None, favok_marji_degisim_puan: Decimal | None, cfg: dict
) -> tuple[Decimal | None, str]:
    if favok_marji is None:
        return None, "FAVÖK hesaplanamadı (banka/sigorta ya da amortisman verisi yok), bileşen atlandı."
    return _seviye_trend_skoru(
        "FAVÖK marjı", favok_marji, favok_marji_degisim_puan, cfg["guclu_esik"], cfg["orta_esik"], cfg["tavan"]
    )


def _skor_kaldirac(net_borc_favok: Decimal | None, cfg: dict) -> tuple[Decimal | None, str]:
    if net_borc_favok is None:
        return None, "net borç/FAVÖK hesaplanamadı (FAVÖK yok veya TTM için 4 çeyrek eksik), bileşen atlandı."

    # NOT (kullanici geri bildirimi): "cok dusuk kaldirac" / "makul kaldirac"
    # gibi ifadeler finans bilmeyen bir okuyucuya "dusuk = kotu puan" gibi
    # yanlis anlasilabiliyordu -- oysa DUSUK net borc/FAVOK SIRKET ICIN
    # IYI bir durumdur (az borc, yuksek puan). Bu yuzden asagidaki metinlerde
    # yon ACIKCA ("olumlu"/"guclu bir gosterge" gibi) belirtilir.
    oran = net_borc_favok
    if oran < 0:
        return Decimal(10), f"net borç/FAVÖK {_num_str(oran)}x (net nakit pozisyonu) — borcundan fazla nakdi var, en olumlu durum."
    if oran < cfg["cok_iyi_esik"]:
        skor = _lerp_score(oran, Decimal(0), cfg["cok_iyi_esik"], Decimal(10), Decimal(9))
        aciklama = f"net borç/FAVÖK {_num_str(oran)}x — çok düşük kaldıraç (olumlu: borç yükü hafif, yüksek puanın nedeni budur)."
    elif oran < cfg["iyi_esik"]:
        skor = _lerp_score(oran, cfg["cok_iyi_esik"], cfg["iyi_esik"], Decimal(8), Decimal(6))
        aciklama = f"net borç/FAVÖK {_num_str(oran)}x — makul kaldıraç (sağlıklı düzey)."
    elif oran < cfg["orta_esik"]:
        skor = _lerp_score(oran, cfg["iyi_esik"], cfg["orta_esik"], Decimal(5), Decimal(3))
        aciklama = f"net borç/FAVÖK {_num_str(oran)}x, yüksek kaldıraç."
    else:
        skor = _lerp_score(oran, cfg["orta_esik"], cfg["tavan"], Decimal(2), Decimal(0))
        aciklama = f"net borç/FAVÖK {_num_str(oran)}x, aşırı yüksek kaldıraç."
    return skor, aciklama


def _skor_karlilik(
    net_marj: Decimal | None, net_marj_degisim_puan: Decimal | None, cfg: dict
) -> tuple[Decimal | None, str]:
    if net_marj is None:
        return None, "net marj hesaplanamadı, bileşen atlandı."
    return _seviye_trend_skoru(
        "Net marj", net_marj, net_marj_degisim_puan, cfg["guclu_esik"], cfg["orta_esik"], cfg["tavan"]
    )


def _skor_buyume(
    hasilat_yoy_pct: Decimal | None, enflasyon_yoy_pct: Decimal | None, cfg: dict
) -> tuple[Decimal | None, str]:
    if hasilat_yoy_pct is None:
        return None, "hasılat YoY değişimi hesaplanamadı (önceki dönem verisi yok), bileşen atlandı."

    if enflasyon_yoy_pct is not None:
        reel = hasilat_yoy_pct - enflasyon_yoy_pct
        not_metni = f"(nominal {format_percent_tr(hasilat_yoy_pct)}, enflasyon {format_percent_tr(enflasyon_yoy_pct)} düşülerek)"
    else:
        reel = hasilat_yoy_pct
        not_metni = "(enflasyon verisi girilmedi, nominal büyüme kullanıldı)"

    skor, _gerekce = _seviye_trend_skoru(
        "Satış büyümesi", reel, None, cfg["guclu_esik"], cfg["orta_esik"], cfg["tavan"], cfg["taban"]
    )
    aciklama = f"satış büyümesi {format_percent_tr(reel)} {not_metni}."
    return skor, aciklama


def _skor_degerleme(valuation: ValuationInput | None, cfg: dict) -> tuple[Decimal | None, str]:
    if valuation is None or (valuation.pe_ratio is None and valuation.pb_ratio is None):
        return None, "fiyat verisi girilmedi (F/K, PD/DD yok), bileşen atlandı."

    alt_skorlar: list[Decimal] = []
    parcalar: list[str] = []

    pe = valuation.pe_ratio
    if pe is not None and pe > 0:
        if pe < cfg["fk_ucuz"]:
            pe_skor = _lerp_score(pe, Decimal(0), cfg["fk_ucuz"], Decimal(10), Decimal(9))
        elif pe < cfg["fk_makul"]:
            pe_skor = _lerp_score(pe, cfg["fk_ucuz"], cfg["fk_makul"], Decimal(8), Decimal(6))
        elif pe < cfg["fk_pahali"]:
            pe_skor = _lerp_score(pe, cfg["fk_makul"], cfg["fk_pahali"], Decimal(5), Decimal(3))
        else:
            pe_skor = _lerp_score(pe, cfg["fk_pahali"], cfg["fk_tavan"], Decimal(2), Decimal(0))
        alt_skorlar.append(pe_skor)
        parcalar.append(f"F/K {_num_str(pe)}")
    elif pe is not None:
        parcalar.append("F/K negatif (zarar), değerlendirme dışı")

    pb = valuation.pb_ratio
    if pb is not None and pb > 0:
        if pb < cfg["pddd_ucuz"]:
            pb_skor = _lerp_score(pb, Decimal(0), cfg["pddd_ucuz"], Decimal(10), Decimal(9))
        elif pb < cfg["pddd_makul"]:
            pb_skor = _lerp_score(pb, cfg["pddd_ucuz"], cfg["pddd_makul"], Decimal(8), Decimal(6))
        elif pb < cfg["pddd_pahali"]:
            pb_skor = _lerp_score(pb, cfg["pddd_makul"], cfg["pddd_pahali"], Decimal(5), Decimal(3))
        else:
            pb_skor = _lerp_score(pb, cfg["pddd_pahali"], cfg["pddd_tavan"], Decimal(2), Decimal(0))
        alt_skorlar.append(pb_skor)
        parcalar.append(f"PD/DD {_num_str(pb)}")
    elif pb is not None:
        parcalar.append("PD/DD negatif (özkaynak eksi), değerlendirme dışı")

    if not alt_skorlar:
        return None, "F/K ve PD/DD anlamlı değil (negatif), bileşen atlandı."

    skor = sum(alt_skorlar) / len(alt_skorlar)

    # KULLANICI GERI BILDIRIMI: sirket ZARAR ediyorsa (F/K negatif oldugu icin
    # degerlendirme disi birakildiginda) PD/DD TEK BASINA %9'lari bulan bir
    # puan uretebiliyordu -- "PD/DD 0,7 ama F/K zarar, nasil 9,3 puan olur"
    # diye kafa karistiriyordu. Bu SADECE PD/DD'nin (tek basina) DUSUK olmasi
    # "ucuz" demek degildir -- zarar eden bir sirkette defter degerinin
    # altinda islem gormek bir "deger tuzagi" (value trap) sinyali de olabilir
    # (piyasa, defter degerinin gercekci olmadigini fiyatliyor olabilir).
    # Bu yuzden bu ozel durumda (F/K zarar nedeniyle disi, sadece PD/DD
    # katki verdi) nihai puan makul ama TAM UST SINIRA ULASMAYAN bir tavana
    # (7,5) kirpilir -- "ucuz ama riskli" mesaji acikca gerekceye eklenir.
    zarar_nedeniyle_fk_disi = pe is not None and pe <= 0
    if zarar_nedeniyle_fk_disi and pb is not None and pb > 0:
        deger_tuzagi_tavani = Decimal("7.5")
        if skor > deger_tuzagi_tavani:
            skor = deger_tuzagi_tavani
        parcalar.append(
            "yalnızca PD/DD'ye göre hesaplandı; şirket zararda olduğundan defter değerinin altındaki "
            "fiyat tek başına 'ucuzluk' garantisi değildir (değer tuzağı riski), puan bu nedenle sınırlı tutuldu"
        )

    return skor, ", ".join(parcalar) + "."


def _skor_ozkaynak_karliligi(roe: Decimal | None, cfg: dict) -> tuple[Decimal | None, str]:
    if roe is None:
        return None, "özkaynak kârlılığı (ROE) hesaplanamadı (TTM net kâr veya güncel özkaynak eksik), bileşen atlandı."
    return _seviye_trend_skoru(
        "Özkaynak kârlılığı (ROE)", roe, None, cfg["guclu_esik"], cfg["orta_esik"], cfg["tavan"]
    )


def _skor_bilanco_kalitesi(
    cari_oran: Decimal | None, ozkaynak_varlik_pct: Decimal | None, cfg: dict
) -> tuple[Decimal | None, str]:
    if cari_oran is None and ozkaynak_varlik_pct is None:
        return None, "cari oran ve özkaynak/varlık oranı hesaplanamadı, bileşen atlandı."

    alt_skorlar: list[Decimal] = []
    parcalar: list[str] = []

    if cari_oran is not None:
        if cari_oran >= cfg["cari_oran_iyi"]:
            cari_skor = _lerp_score(cari_oran, cfg["cari_oran_iyi"], cfg["cari_oran_iyi"] + Decimal(1), Decimal(8), Decimal(10))
        elif cari_oran >= cfg["cari_oran_orta"]:
            cari_skor = _lerp_score(cari_oran, cfg["cari_oran_orta"], cfg["cari_oran_iyi"], Decimal(5), Decimal(7))
        else:
            cari_skor = _lerp_score(cari_oran, Decimal(0), cfg["cari_oran_orta"], Decimal(0), Decimal(4))
        alt_skorlar.append(cari_skor)
        parcalar.append(f"cari oran {_num_str(cari_oran)}")

    if ozkaynak_varlik_pct is not None:
        if ozkaynak_varlik_pct >= cfg["ozkaynak_varlik_iyi"]:
            oz_skor = _lerp_score(
                ozkaynak_varlik_pct, cfg["ozkaynak_varlik_iyi"], cfg["ozkaynak_varlik_iyi"] + Decimal(20), Decimal(8), Decimal(10)
            )
        elif ozkaynak_varlik_pct >= cfg["ozkaynak_varlik_orta"]:
            oz_skor = _lerp_score(ozkaynak_varlik_pct, cfg["ozkaynak_varlik_orta"], cfg["ozkaynak_varlik_iyi"], Decimal(5), Decimal(7))
        else:
            oz_skor = _lerp_score(ozkaynak_varlik_pct, Decimal(0), cfg["ozkaynak_varlik_orta"], Decimal(0), Decimal(4))
        alt_skorlar.append(oz_skor)
        parcalar.append(f"özkaynak/varlık {format_percent_tr(ozkaynak_varlik_pct)}")

    skor = sum(alt_skorlar) / len(alt_skorlar)
    # KULLANICI GERI BILDIRIMI: sirketin karlilik/FAVOK/net kar bilesenleri
    # kotu (kirmizi) olsa bile bu bilesen yuksek cikabiliyor -- bu bir HATA
    # DEGIL, cunku bu bilesen KASITLI olarak SADECE likidite (cari oran) ve
    # kaldirac/sermaye yapisi (ozkaynak/varlik) gucunu olcer -- yani "bu
    # sirket borcunu odeyebilir mi / iflasa ne kadar uzak" sorusuna yanit
    # verir, kARLILIGI DEGIL. Zarar eden ama borcu az/ozkaynagi guclu bir
    # sirket (orn. BORSK) bu ikisinde AYNI ANDA hem kotu hem iyi olabilir --
    # bu yuzden aciklama metninde kapsam ACIKCA belirtilir, karisiklik
    # yasanmasin diye.
    parcalar.append("bu bileşen sadece likidite/borç ödeme gücünü ölçer, kârlılığı yansıtmaz")
    return skor, ", ".join(parcalar) + "."


# --- Ana giris noktalari -----------------------------------------------------


_INDUSTRIAL_TEMPLATE_LABELS: dict[str, str] = {
    "sanayi": "sanayi_holding",
    "abd_sanayi": "sanayi_holding_abd",
}


def score_industrial(
    analysis: AnalysisResult,
    valuation: ValuationInput | None = None,
    enflasyon_yoy_pct: Decimal | None = None,
    template: str = "sanayi",
) -> ScoreResult:
    """Sanayi/holding sirketleri icin varsayilan sablon (7 bilesen, agirlik
    toplami %100): Nakit Uretimi %21, Kaldirac %17, Ozkaynak Karliligi
    (ROE) %15, Karlilik %13, Buyume %13, Degerleme %17, Bilanco Kalitesi %4.

    `valuation` verilmezse (fiyat verisi yoksa) Degerleme bileseni atlanir
    ve agirligi diger bilesenlere orantisal olarak dagitilir. `enflasyon_yoy_pct`
    verilirse Buyume bileseni reel (enflasyondan arindirilmis) hasilat
    buyumesine gore hesaplanir; verilmezse nominal buyume kullanilir.

    `template`: `CONFIG` icindeki hangi esik/agirlik setinin kullanilacagini
    secer -- "sanayi" (BIST XI_29, varsayilan) veya "abd_sanayi" (NASDAQ/ABD,
    bkz. score_industrial_us()). Bilesen YAPISI (7 bilesen, hangi rasyonun
    hangi bilesene girdigi) HER IKI sablonda da AYNIDIR -- SADECE esik
    DEGERLERI (CONFIG[template][...]) degisir, bu yuzden fonksiyon
    KOPYALANMADI (bkz. SCORING_METHODOLOGY.md abd_sanayi gerekceleri).
    """
    cfg = CONFIG[template]
    r = analysis.ratios
    equity = analysis.balance_sheet.equity.current
    assets = analysis.balance_sheet.total_assets.current

    bilesenler = [
        ("Nakit Üretimi (FAVÖK)", cfg["nakit_uretimi"]["agirlik"],
         _skor_nakit_uretimi(r.ebitda_margin_current, r.ebitda_margin_change_points, cfg["nakit_uretimi"])),
        ("Kaldıraç", cfg["kaldirac"]["agirlik"], _skor_kaldirac(r.net_debt_to_ebitda, cfg["kaldirac"])),
        ("Özkaynak Kârlılığı (ROE)", cfg["ozkaynak_karliligi"]["agirlik"],
         _skor_ozkaynak_karliligi(r.roe_annualized, cfg["ozkaynak_karliligi"])),
        ("Kârlılık", cfg["karlilik"]["agirlik"],
         _skor_karlilik(r.net_margin_current, r.net_margin_change_points, cfg["karlilik"])),
        ("Büyüme", cfg["buyume"]["agirlik"],
         _skor_buyume(analysis.ratios.revenue_growth_yoy_pct, enflasyon_yoy_pct, cfg["buyume"])),
        ("Değerleme", cfg["degerleme"]["agirlik"], _skor_degerleme(valuation, cfg["degerleme"])),
        ("Bilanço Kalitesi", cfg["bilanco_kalitesi"]["agirlik"],
         _skor_bilanco_kalitesi(r.current_ratio, _safe_pct(equity, assets), cfg["bilanco_kalitesi"])),
    ]
    template_label = _INDUSTRIAL_TEMPLATE_LABELS.get(template, template)
    return _agirlik_dagit_ve_hesapla(analysis.ticker, analysis.latest_period, template_label, bilesenler)


def score_industrial_us(analysis: AnalysisResult, valuation: ValuationInput | None = None) -> ScoreResult:
    """score_industrial()'in NASDAQ/ABD (US_GAAP) karsiligi --
    CONFIG['abd_sanayi'] esikleriyle (bkz. modul ust notu, SCORING_METHODOLOGY.md)
    AYNI 7 bilesenli sablonu kullanir. `enflasyon_yoy_pct` BILEREK
    verilmez/gecirilmez -- ABD icin nominal USD buyumesi zaten PRATIKTE reel
    buyumeye yakindir (bkz. calculator.analyze_us() docstring'i), ayrica bir
    enflasyon duzeltmesi YAPILMAZ; Buyume bileseninin esikleri (guclu/orta/
    tavan/taban) bu farki ZATEN esik KALIBRASYONUYLA yansitir."""
    return score_industrial(analysis, valuation=valuation, enflasyon_yoy_pct=None, template="abd_sanayi")


def score_insurance(
    analysis: AnalysisResult,
    valuation: ValuationInput | None = None,
    prim_buyumesi_yoy_pct: Decimal | None = None,
    teknik_denge_marji_pct: Decimal | None = None,
    teknik_denge_marji_degisim_puan: Decimal | None = None,
) -> ScoreResult:
    """Sigorta sirketleri icin BASIT iskelet sablon (4 bilesen: Prim
    Buyumesi, Teknik Denge Marji, Ozkaynak Karliligi (ROE), Degerleme).

    Prim buyumesi ve teknik denge marji AnalysisResult icinde yoktur --
    calculator.py bunlari uretmez (sigortaya ozgu POLICY/hasar kalemleri
    fetcher katmaninda henuz cekilmiyor) -- bu yuzden disaridan parametre
    olarak alinir; verilmezse ilgili bilesen atlanir. Esikler ileride
    gercek sigorta sirketi verisiyle kalibre edilmelidir.
    """
    cfg = CONFIG["sigorta"]

    if prim_buyumesi_yoy_pct is not None:
        prim = _seviye_trend_skoru(
            "Prim büyümesi", prim_buyumesi_yoy_pct, None,
            cfg["prim_buyumesi"]["guclu_esik"], cfg["prim_buyumesi"]["orta_esik"],
            cfg["prim_buyumesi"]["tavan"], cfg["prim_buyumesi"]["taban"],
        )
    else:
        prim = (None, "prim büyümesi verisi girilmedi, bileşen atlandı.")

    if teknik_denge_marji_pct is not None:
        teknik = _seviye_trend_skoru(
            "Teknik denge marjı", teknik_denge_marji_pct, teknik_denge_marji_degisim_puan,
            cfg["teknik_denge_marji"]["guclu_esik"], cfg["teknik_denge_marji"]["orta_esik"],
            cfg["teknik_denge_marji"]["tavan"], cfg["teknik_denge_marji"]["taban"],
        )
    else:
        teknik = (None, "teknik denge marjı verisi girilmedi, bileşen atlandı.")

    roe = _seviye_trend_skoru(
        "Özkaynak kârlılığı", analysis.ratios.roe_annualized, None,
        cfg["ozkaynak_karliligi"]["guclu_esik"], cfg["ozkaynak_karliligi"]["orta_esik"], cfg["ozkaynak_karliligi"]["tavan"],
    )

    bilesenler = [
        ("Prim Büyümesi", cfg["prim_buyumesi"]["agirlik"], prim),
        ("Teknik Denge Marjı", cfg["teknik_denge_marji"]["agirlik"], teknik),
        ("Özkaynak Kârlılığı (ROE)", cfg["ozkaynak_karliligi"]["agirlik"], roe),
        ("Değerleme", cfg["degerleme"]["agirlik"], _skor_degerleme(valuation, cfg["degerleme"])),
    ]
    return _agirlik_dagit_ve_hesapla(analysis.ticker, analysis.latest_period, "sigorta", bilesenler)


def score_bank(
    analysis: AnalysisResult,
    valuation: ValuationInput | None = None,
    net_faiz_marji_pct: Decimal | None = None,
    net_faiz_marji_degisim_puan: Decimal | None = None,
    aktif_karliligi_pct: Decimal | None = None,
    aktif_karliligi_degisim_puan: Decimal | None = None,
    ozkaynak_aktif_orani_pct: Decimal | None = None,
) -> ScoreResult:
    """Banka sirketleri icin CAMELS (Capital/Assets/Management/Earnings/
    Liquidity/Sensitivity) cercevesinden esinlenen 5 bilesenli sablon:
    Ozkaynak Karliligi (ROE), Net Faiz Marji (NIM), Aktif Karliligi (ROA),
    Ozkaynak/Aktif Orani, Degerleme.

    ONEMLI: Regulatuar Sermaye Yeterlilik Orani (Tier1+2/Risk Agirlikli
    Varlik) bu projenin veri kaynaginda (İş Yatirim MaliTablo uc noktasi)
    HİÇ YOKTUR -- ayri bir BDDK duzenleyici rapor gerektirir, canli
    arastirmayla dogrulandi (bkz. GARAN icin denenen alternatif uc nokta
    parametreleri, hicbiri veri dondurmedi). Bu yuzden onceki tasarimdaki
    "Sermaye Yeterlilik Orani" bileseni HER ZAMAN "-" gosteriyordu (kullanici
    geri bildirimi: "gorselimde belirsiz bir sey gormek istemiyorum").
    Yerine CAMELS arastirmasindan (bkz. proje notlari) iki TAMAMEN
    HESAPLANABILIR gosterge kondu:
      - Aktif Karliligi (ROA): CAMELS "Earnings" bileseninde NIM ile
        BIRLIKTE onerilir (net kar / toplam varlik).
      - Ozkaynak/Aktif Orani: CAMELS "Capital Adequacy" ruhuna uygun bir
        KALDIRAÇ/SERMAYE GUCU YAKLASIMIDIR (ozkaynak / toplam varlik) --
        regulatuar CAR'in YERINE GECMEZ, ama ayni sekilde "bu banka ne
        kadar ozkaynakla desteklendi" sorusuna hicbir veri eksigi
        OLMADAN yanit verir.
    net_faiz_marji_pct/aktif_karliligi_pct/ozkaynak_aktif_orani_pct
    AnalysisResult icinde (genel Ratios) yoktur -- disaridan parametre
    olarak alinir (bkz. BankRatios, pipeline.py cagrisi); verilmezse
    ilgili bilesen atlanir.
    """
    cfg = CONFIG["banka"]

    roe = _seviye_trend_skoru(
        "Özkaynak kârlılığı", analysis.ratios.roe_annualized, None,
        cfg["ozkaynak_karliligi"]["guclu_esik"], cfg["ozkaynak_karliligi"]["orta_esik"], cfg["ozkaynak_karliligi"]["tavan"],
    )

    if net_faiz_marji_pct is not None:
        nfm = _seviye_trend_skoru(
            "Net faiz marjı", net_faiz_marji_pct, net_faiz_marji_degisim_puan,
            cfg["net_faiz_marji"]["guclu_esik"], cfg["net_faiz_marji"]["orta_esik"],
            cfg["net_faiz_marji"]["tavan"], cfg["net_faiz_marji"]["taban"],
        )
    else:
        nfm = (None, "net faiz marjı verisi girilmedi, bileşen atlandı.")

    if aktif_karliligi_pct is not None:
        roa = _seviye_trend_skoru(
            "Aktif kârlılığı (ROA)", aktif_karliligi_pct, aktif_karliligi_degisim_puan,
            cfg["aktif_karliligi"]["guclu_esik"], cfg["aktif_karliligi"]["orta_esik"],
            cfg["aktif_karliligi"]["tavan"], cfg["aktif_karliligi"]["taban"],
        )
    else:
        roa = (None, "aktif kârlılığı (ROA) verisi girilmedi, bileşen atlandı.")

    if ozkaynak_aktif_orani_pct is not None:
        oao = _seviye_trend_skoru(
            "Özkaynak/aktif oranı", ozkaynak_aktif_orani_pct, None,
            cfg["ozkaynak_aktif_orani"]["guclu_esik"], cfg["ozkaynak_aktif_orani"]["orta_esik"],
            cfg["ozkaynak_aktif_orani"]["tavan"],
        )
    else:
        oao = (None, "özkaynak/aktif oranı verisi girilmedi, bileşen atlandı.")

    bilesenler = [
        ("Özkaynak Kârlılığı (ROE)", cfg["ozkaynak_karliligi"]["agirlik"], roe),
        ("Net Faiz Marjı", cfg["net_faiz_marji"]["agirlik"], nfm),
        ("Aktif Kârlılığı (ROA)", cfg["aktif_karliligi"]["agirlik"], roa),
        ("Özkaynak/Aktif Oranı", cfg["ozkaynak_aktif_orani"]["agirlik"], oao),
        ("Değerleme", cfg["degerleme"]["agirlik"], _skor_degerleme(valuation, cfg["degerleme"])),
    ]
    return _agirlik_dagit_ve_hesapla(analysis.ticker, analysis.latest_period, "banka", bilesenler)


def score_financing(analysis: AnalysisResult, valuation: ValuationInput | None = None) -> ScoreResult:
    """Tasarruf Finansman Şirketleri (XI_29K, orn. KTLEV) için score_bank()'in
    karşılığı -- 5 bileşenli şablon: Net Kâr Marjı, Özkaynak Kârlılığı (ROE),
    Aktif Kârlılığı (ROA), Özkaynak/Aktif Oranı, Değerleme.

    Trend (YoY nokta-değişimi) parametreleri bilinçli olarak YOK -- bkz.
    calculator.analyze_financing() docstring'i, bu şirket tipi için henüz
    önceki yıla ait yeterli veri derinliği doğrulanmadı (yeni halka arz)."""
    cfg = CONFIG["finansman"]

    karlilik = _seviye_trend_skoru(
        "Net kâr marjı", analysis.ratios.net_margin_current, None,
        cfg["karlilik"]["guclu_esik"], cfg["karlilik"]["orta_esik"], cfg["karlilik"]["tavan"],
    )
    roe = _seviye_trend_skoru(
        "Özkaynak kârlılığı", analysis.ratios.roe_annualized, None,
        cfg["ozkaynak_karliligi"]["guclu_esik"], cfg["ozkaynak_karliligi"]["orta_esik"], cfg["ozkaynak_karliligi"]["tavan"],
    )
    roa = _seviye_trend_skoru(
        "Aktif kârlılığı (ROA)", analysis.ratios.return_on_assets_annualized, None,
        cfg["aktif_karliligi"]["guclu_esik"], cfg["aktif_karliligi"]["orta_esik"],
        cfg["aktif_karliligi"]["tavan"], cfg["aktif_karliligi"]["taban"],
    )
    oao = _seviye_trend_skoru(
        "Özkaynak/aktif oranı", analysis.ratios.equity_to_assets_current, None,
        cfg["ozkaynak_aktif_orani"]["guclu_esik"], cfg["ozkaynak_aktif_orani"]["orta_esik"], cfg["ozkaynak_aktif_orani"]["tavan"],
    )

    bilesenler = [
        ("Kârlılık", cfg["karlilik"]["agirlik"], karlilik),
        ("Özkaynak Kârlılığı (ROE)", cfg["ozkaynak_karliligi"]["agirlik"], roe),
        ("Aktif Kârlılığı (ROA)", cfg["aktif_karliligi"]["agirlik"], roa),
        ("Özkaynak/Aktif Oranı", cfg["ozkaynak_aktif_orani"]["agirlik"], oao),
        ("Değerleme", cfg["degerleme"]["agirlik"], _skor_degerleme(valuation, cfg["degerleme"])),
    ]
    return _agirlik_dagit_ve_hesapla(analysis.ticker, analysis.latest_period, "finansman", bilesenler)
