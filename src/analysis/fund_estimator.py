"""Fon günlük getiri TAHMİN motoru -- Faz 18.

🚨🚨🚨 GERİYE DÖNÜK DOĞRULAMA SONUCU: BU MOTOR ŞU HALİYLE YAYINLANMAMALI.
`scripts/validate_fon_tahmini.py` 2026-08-05'te 10 fon × ~20 gün (213 test
noktası) üzerinde CANLI veriyle çalıştırıldı: **Ortalama Mutlak Hata (MAE)
1,36 puan** -- hedefin (0,15) ~9 katı, "kabul edilemez" eşiğin (0,50)
belirgin ÜSTÜNDE. Tam rapor: `data/exploration/fon_tahmini_dogrulama_raporu.txt`.
Bu modülü herhangi bir bot/kart çıktısına BAĞLAMADAN ÖNCE bu durum
ÇÖZÜLMELİ (bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md açık risk maddesi).

En güçlü ipucu: en TİTİZ doğrulanan fon (PHE -- KAP PDF'inin 3 yüzde
kolonunun anlamı rakam rakam GRUP TOPLAMI'yla eşleştirilmişti) MAE=0,60
ile diğer 9 fondan (MAE 1,06-1,73) BELİRGİN ÖLÇÜDE daha iyi çıktı. Bu,
kolon anlamının (5./6./7. sayısal alan) PHE/TLY DIŞINDAKİ fonlarda/PMC'lerde
(Ak Portföy, Allbatross, Atlas, QNB, Yapı Kredi, Bulls, İş Portföy, Ata
Portföy) FARKLI olabileceğini düşündürüyor -- `kap_fund_portfolio.py`'nin
öz-doğrulaması (grup toplamı ~%100) SADECE İÇ TUTARLILIĞI kontrol eder,
kolonların GERÇEKTEN doğru YORUMLANDIĞINI garanti ETMEZ. Ayrıca güven
kalibrasyonu TERS çıktı ("yüksek" güven MAE=1,63, "orta" güven MAE=1,21) --
mevcut güven skoru formülü gerçek isabetle ÖRTÜŞMÜYOR, YENİDEN
tasarlanmalı. Kesin kök neden bu oturumda BULUNAMADI/DOĞRULANAMADI --
sadece güçlü bir hipotez.

🚨 BU BİR TAHMİN MOTORUDUR, GERÇEK/AÇIKLANMIŞ FİYAT DEĞİLDİR. Fonun
resmi fiyatı henüz TEFAS'a düşmeden ÖNCE, elimizdeki (KAP'ın aylık
"Portföy Dağılım Raporu"ndan gelen, BAYAT olabilen) portföy içeriğine ve
GÜNCEL hisse/fon fiyat hareketlerine dayanarak "bugün fon büyük ihtimalle
ne kadar değişmiştir" sorusuna bir TAHMİN üretir. Bu tahminin GERÇEK
doğruluğu `scripts/validate_fon_tahmini.py`nin ürettiği geriye dönük
doğrulama raporu OKUNMADAN hiçbir yere (bot, kart) BAĞLANMAMALIDIR.

SAF MATEMATİK -- bu modül `src.fetchers`/`src.db` hiçbir modülü import
ETMEZ, hiçbir ağ isteği/DB erişimi yapmaz (01_MIMARI.md katman kuralı,
`calculator.py`/`trends.py`/`valuation.py` ile AYNI ilke). Girdiler
(portföy, fiyat değişimleri, fon gider oranı) çağıran taraf tarafından
ÖNCEDEN `kap_fund_portfolio.py` + `tefas.py`/`isyatirim.py` ile
çekilmiş/hazırlanmış olmalı.

── TEMEL FORMÜL ──
    tahmini_günlük_getiri = Σ(ağırlık_i × varlık_i_günlük_getirisi) − günlük_fon_gideri

Bileşen bazında (bu oturumda `kap_fund_portfolio.Holding.instrument_type`
kümesiyle -- "hisse"/"fon"/"türev"/"nakit" -- sınırlı, bkz. o modülün
üst notu):
  - "hisse" (BİST hissesi -- yabancı hisse şu an KAP parser'ımızda ayrı
    ayrıştırılmıyor, AFA gibi yabancı ağırlıklı fonlarda zaten
    `is_estimable_fund_type()` bu fonu baştan ELER): `price_changes`
    sözlüğünde ticker'ı varsa o günlük kapanış getirisi kullanılır.
  - "fon" (fon-içinde-fon -- alt fonun KENDİ TEFAS kodu `price_changes`
    sözlüğünde AYNI anahtar altında aranır; çağıran taraf alt fonun
    `tefas.fetch_fund_returns(alt_kod).d1`'ini BURAYA koymalıdır).
  - "türev": genelde ihmal edilebilir ağırlıkta (CANLI gözlemlendi,
    PHE'de %0,01) -- fiyatlandırılamıyorsa 0 getiri VARSAYILIR ama
    `contributions`'ta `daily_return_pct=None` olarak İŞARETLENİR ve
    belirsizlik puanına dahil edilir (Kural 3: sessizce yok sayılmaz).
  - "nakit" (kap_fund_portfolio'nun residual "kalan" satırı -- GERÇEK
    nakit/alacak/borç OLABİLİR ama ayrıştırılamayan bono/yabancı hisse
    içeriğini de İÇERİYOR olabilir, bkz. o modülün üst notu): 0 getiri
    VARSAYILIR ama İSİMLENDİRİLMİŞ bir belirsizlik kaynağı olarak
    `confidence` hesabına girer -- SESSİZCE %100 doğru varsayılmaz.
  - Fon yönetim ücreti: `fund_expense_ratio_annual_pct / 365` günlük
    olarak DÜŞÜLÜR (KAP'ın Genel Bilgiler sayfasındaki "Fon Yönetim
    Ücreti Oranı" -- kap_fund_portfolio.py bu alanı bu oturumda
    fetch_latest_portfolio() ile DÖNDÜRMÜYOR, çağıran taraf isterse ayrı
    çeker; verilmezse `Decimal(0)` varsayılır, VARSAYIM AÇIKÇA
    loglanmaz çünkü None/0 ayrımı çağıran tarafın sorumluluğundadır).

── UYGULANABİLİRLİK SINIRI (`is_estimable_fund_type()`) ──
Görev tanımının kendi sınıflandırması, TEFAS `fonKategori` alanıyla
eşlenir (CANLI görülen değerler: "Hisse Senedi Fonu", "Serbest Fon" vb.):
  ✅ yüksek güven adayı : Hisse Senedi Fonu, Endeks Fonu
  ⚠️ orta güven adayı   : Karma Fon, Değişken Fon, Değişken Şemsiye Fon,
                          Serbest Fon, Serbest Şemsiye Fon (bkz. aşağıdaki
                          not -- kategori adı TEK BAŞINA şeffaflığı
                          belirlemiyor, gerçek kapsam/tazelik güven
                          skoruyla ayrıca değerlendiriliyor)
  ❌ UYGULANAMAZ        : Borçlanma Araçları Fonu, Para Piyasası Fonu,
                          Fon Sepeti Fonu, Katılım şemsiyeleri (yapısı
                          gereği hisse-fiyat hareketiyle ilişkisiz VEYA
                          KAP'ta hisse-bazlı portföy raporu YAYINLAMIYOR)
  ❓ bilinmeyen kategori : UYGULANAMAZ (Kural 3: temkinli varsayım)
Bu liste `_NOT_APPLICABLE_CATEGORIES`/`_HIGH_APPLICABLE_CATEGORIES` altında
AÇIK sabitler olarak tutulur -- CANLI gözlemlenmemiş bir kategori
eklenmeden ÖNCE gerekçe yazılmalı (Kural 3).

── GÜVEN SEVİYESİ VE ARALIK ──
Üç bileşenden ağırlıklı bir puan (0-3) hesaplanır (a: portföy tazeliği,
en yüksek ağırlık; b: fiyatlandırılabilen ağırlık yüzdesi; c: belirsiz
varlık sınıflarının -- türev+nakit residual -- toplam ağırlığı), sonra
puan "yüksek"/"orta"/"düşük"e eşlenir ve buna göre bir güven aralığı
(± puan, tahmini getirinin etrafında) üretilir. Bu eşikler bu oturumda
YENİ tanımlandı, HENÜZ gerçek veriyle KALİBRE EDİLMEDİ --
`scripts/validate_fon_tahmini.py`nin geriye dönük testi bu eşiklerin
gerçekçi olup olmadığını ÖLÇMEK içindir; sonuç kötü çıkarsa (MAE
güven aralığıyla TUTARSIZ) burası GÜNCELLENMELİDİR.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

# --- Fon tipi uygulanabilirlik sınıflandırması -----------------------------------------------------

# CANLI gözlemlenen TEFAS "fonKategori" değerleriyle eşlenir (bkz. modül üst
# notu). Bilinmeyen/eşleşmeyen HER kategori _NOT_APPLICABLE sayılır (Kural 3).
_HIGH_APPLICABLE_CATEGORIES = frozenset({"Hisse Senedi Fonu", "Endeks Fonu"})
# "Serbest Fon"/"Serbest Şemsiye Fon" BURAYA (orta güven) taşındı -- ilk
# varsayım ("opaque portföy") CANLI veriyle YANLIŞLANDI: 2026-08-05'te 15
# hedef fon teşhis edildiğinde TLY (Serbest Fon) %81,83 hisse kapsamı + 5
# günlük tazelikle PHE (Hisse Senedi Fonu) kadar İYİ çıktı; buna karşın BMU
# (yine Serbest Fon) neredeyse HİÇ ayrıştırılabilir içerik vermedi (%99,45
# residual). Yani "Serbest Fon" TEK BAŞINA şeffaflığı belirlemiyor -- fon
# fon'a DEĞİŞİYOR. Kategori adına göre TOPTAN reddetmek yerine, gerçek
# `covered_weight_pct`/tazelik bu fonları zaten `estimate_daily_return()`
# içindeki güven skoruyla (bkz. aşağı) doğru yere ("düşük" güven, geniş
# aralık) düşürüyor -- bu YETERLİ bir güvenlik ağı (Kural 3 hâlâ geçerli:
# emin olunmayan durumda geniş aralık/"düşük" güven verilir, susarak
# EMİNMİŞ gibi davranılmaz).
_MEDIUM_APPLICABLE_CATEGORIES = frozenset(
    {"Karma Fon", "Değişken Fon", "Değişken Şemsiye Fon", "Serbest Fon", "Serbest Şemsiye Fon"}
)
_NOT_APPLICABLE_CATEGORIES = frozenset(
    {
        "Borçlanma Araçları Fonu",
        "Para Piyasası Fonu",
        "Fon Sepeti Fonu",
        "Kısa Vadeli Borçlanma Araçları Fonu",
        "Katılım Fonu",
        "Katılım Şemsiye Fonu",
        "Kira Sertifikaları Fonu",
        "Altın Fonu",
        "Kıymetli Madenler Fonu",
    }
)

# instrument_type -> bu türün "belirsiz" (fiyatlandırma kalitesi düşük)
# sayılıp sayılmayacağı. "hisse"/"fon" fiyatlandırılabilirse GÜVENİLİR;
# "türev"/"nakit" HER ZAMAN belirsizlik puanına katkı yapar (residual
# "nakit" gerçek nakit DEĞİL, ayrıştırılamayan bono/yabancı hisse de
# olabilir -- bkz. modül üst notu).
_INHERENTLY_UNCERTAIN_TYPES = frozenset({"türev", "nakit"})


def is_estimable_fund_type(fund_category: str | None) -> tuple[bool, str]:
    """Verilen TEFAS fon kategorisi için tahmin motorunun ANLAMLI olup
    olmadığını belirler. Döner: `(uygulanabilir_mi, gerekçe)`.

    `fund_category` None/boş ise veya bilinen HİÇBİR sınıfa girmiyorsa
    (yeni/nadir bir kategori) TEMKİNLİ davranılır: UYGULANAMAZ (Kural 3 --
    "emin olmadığın veri kalemini varsayımla eşleme")."""
    if not fund_category or not fund_category.strip():
        return False, "Fon kategorisi bilinmiyor -- temkinli olarak tahmin üretilmiyor."

    normalized = fund_category.strip()
    if normalized in _NOT_APPLICABLE_CATEGORIES:
        return False, (
            f"'{normalized}' kategorisindeki fonlar için tahmin motoru UYGULANAMAZ "
            "(portföy şeffaf değil, hisse fiyat hareketiyle zayıf ilişkili veya aşırı değişken)."
        )
    if normalized in _HIGH_APPLICABLE_CATEGORIES or normalized in _MEDIUM_APPLICABLE_CATEGORIES:
        return True, ""

    return False, (
        f"'{normalized}' bilinmeyen/doğrulanmamış bir fon kategorisi -- Kural 3 gereği "
        "temkinli olarak tahmin üretilmiyor (bkz. fund_estimator.py modül üst notu)."
    )


# --- Veri modelleri -----------------------------------------------------


class HoldingLike(Protocol):
    instrument_type: str
    ticker: str | None
    name: str
    weight_pct: Decimal


class PortfolioLike(Protocol):
    fund_code: str
    report_date: date
    staleness_days: int
    holdings: list[HoldingLike]


@dataclass(frozen=True)
class HoldingContribution:
    ticker: str | None
    name: str
    weight_pct: Decimal
    daily_return_pct: Decimal | None  # None = bu varlık fiyatlandırılamadı (uncovered)
    contribution_pct: Decimal  # (weight_pct/100) * daily_return_pct -- fiyatlandırılamadıysa 0


@dataclass(frozen=True)
class FundEstimate:
    fund_code: str
    estimate_date: date
    estimated_return_pct: Decimal
    confidence: str  # "yüksek" | "orta" | "düşük"
    confidence_interval: tuple[Decimal, Decimal]
    covered_weight_pct: Decimal  # fiyatlandırılabilen portföy yüzdesi
    portfolio_staleness_days: int
    contributions: list[HoldingContribution]  # katkıya (contribution_pct, mutlak deger) göre SIRALI
    uncovered_note: str | None


# --- Güven skoru -----------------------------------------------------

# Her bileşen 0-3 arası bir "puan" alır; toplam ağırlıklı puan [0,3]
# aralığına normalize edilip güven seviyesine ve aralık genişliğine
# eşlenir. Ağırlıklar (tazelik %50, kapsam %30, belirsizlik %20) görev
# tanımının "a. tazelik -- en yüksek ağırlık" talimatına göre seçildi;
# KESİN bir bilimsel türetim DEĞİL, `scripts/validate_fon_tahmini.py` ile
# KALİBRE EDİLMESİ gereken bir başlangıç noktasıdır (bkz. modül üst notu).
_STALENESS_WEIGHT = Decimal("0.5")
_COVERAGE_WEIGHT = Decimal("0.3")
_UNCERTAINTY_WEIGHT = Decimal("0.2")


def _staleness_score(staleness_days: int) -> Decimal:
    if staleness_days <= 7:
        return Decimal(3)
    if staleness_days <= 15:
        return Decimal(2)
    if staleness_days <= 30:
        return Decimal(1)
    return Decimal(0)


def _coverage_score(covered_weight_pct: Decimal) -> Decimal:
    if covered_weight_pct >= 85:
        return Decimal(3)
    if covered_weight_pct >= 60:
        return Decimal(2)
    if covered_weight_pct >= 35:
        return Decimal(1)
    return Decimal(0)


def _uncertainty_score(uncertain_weight_pct: Decimal) -> Decimal:
    """Belirsiz (türev/nakit residual + fiyatlandırılamayan hisse/fon)
    ağırlık NE KADAR AZSA puan O KADAR YÜKSEK (tersine orantılı)."""
    if uncertain_weight_pct <= 5:
        return Decimal(3)
    if uncertain_weight_pct <= 15:
        return Decimal(2)
    if uncertain_weight_pct <= 30:
        return Decimal(1)
    return Decimal(0)


def _confidence_from_score(score: Decimal) -> str:
    if score >= Decimal("2.3"):
        return "yüksek"
    if score >= Decimal("1.2"):
        return "orta"
    return "düşük"


# Güven seviyesine göre tahmini getirinin etrafındaki ± aralık (yüzde
# puan cinsinden) -- düşük güvende aralık ÇOK daha geniştir (tahminin
# kendisi kadar önemli bir sinyal: "bu sayıya güvenme").
_CONFIDENCE_INTERVAL_WIDTH = {
    "yüksek": Decimal("0.3"),
    "orta": Decimal("0.8"),
    "düşük": Decimal("2.0"),
}


# --- Ana fonksiyon -----------------------------------------------------


def estimate_daily_return(
    portfolio: PortfolioLike,
    price_changes: dict[str, Decimal],
    fund_expense_ratio_annual_pct: Decimal | None = None,
    fund_category: str | None = None,
    estimate_date: date | None = None,
) -> FundEstimate | None:
    """Bir fonun BUGÜNKÜ (henüz TEFAS'a düşmemiş) günlük getirisini,
    portföy içeriği + varlık bazlı güncel fiyat değişimlerinden TAHMİN
    eder.

    Argümanlar:
        portfolio: `kap_fund_portfolio.FundPortfolio`-benzeri bir nesne
            (`.holdings`, `.staleness_days`, `.fund_code`, `.report_date`).
        price_changes: {ticker: günlük_yüzde_getiri} sözlüğü -- hem BİST
            hisseleri hem fon-içinde-fon alt kodları AYNI sözlükte,
            AYNI anahtar biçimiyle (ticker) aranır. Bir ticker bu
            sözlükte YOKSA o holding "fiyatlandırılamadı" sayılır.
        fund_expense_ratio_annual_pct: fonun YILLIK toplam gider oranı
            (örn. Decimal("2.00") = %2). None/verilmezse gider düşülmez
            (Decimal(0) varsayılır) -- bu sistematik bir İYİMSER sapma
            kaynağıdır, çağıran taraf MÜMKÜNSE bu değeri versin.
        fund_category: TEFAS "fonKategori" (örn. "Hisse Senedi Fonu").
            `is_estimable_fund_type()` ile uygulanabilirlik kontrolü
            yapılır -- uygulanamayan bir kategori için None DÖNER
            (Kural: "bu fon tipi için tahmin üretilemiyor").
        estimate_date: tahminin AİT OLDUĞU gün (varsayılan: bugün).

    Dönen değer:
        `FundEstimate` -- ya da fon tipi UYGULANAMAZSA veya portföyde
        HİÇ holding yoksa `None` (Kural 3/9: hata FIRLATMAZ, sessizce
        "üretilemedi" der).
    """
    applicable, _reason = is_estimable_fund_type(fund_category)
    if not applicable:
        return None

    if not portfolio.holdings:
        return None

    expense_ratio = fund_expense_ratio_annual_pct if fund_expense_ratio_annual_pct is not None else Decimal(0)
    daily_expense_pct = expense_ratio / Decimal(365)

    contributions: list[HoldingContribution] = []
    covered_weight = Decimal(0)
    uncertain_weight = Decimal(0)
    total_return = Decimal(0)

    for holding in portfolio.holdings:
        daily_return = price_changes.get(holding.ticker) if holding.ticker else None
        is_covered = daily_return is not None
        is_inherently_uncertain = holding.instrument_type in _INHERENTLY_UNCERTAIN_TYPES

        if is_covered:
            contribution = (holding.weight_pct / Decimal(100)) * daily_return
            covered_weight += holding.weight_pct
            total_return += contribution
        else:
            contribution = Decimal(0)

        # Fiyatlandirilamayan HER holding (turu ne olursa olsun) VEYA
        # dogasi geregi belirsiz sayilan turler ("turev"/"nakit" --
        # fiyatlandirilsa BILE) belirsizlik puanina girer. `or` sayesinde
        # her iki kosul da dogruyken TEK seferde sayilir (mukerrer yok).
        if not is_covered or is_inherently_uncertain:
            uncertain_weight += holding.weight_pct

        contributions.append(
            HoldingContribution(
                ticker=holding.ticker,
                name=holding.name,
                weight_pct=holding.weight_pct,
                daily_return_pct=daily_return,
                contribution_pct=contribution,
            )
        )

    total_return -= daily_expense_pct

    contributions.sort(key=lambda c: -abs(c.contribution_pct))

    staleness_days = portfolio.staleness_days
    score = (
        _STALENESS_WEIGHT * _staleness_score(staleness_days)
        + _COVERAGE_WEIGHT * _coverage_score(covered_weight)
        + _UNCERTAINTY_WEIGHT * _uncertainty_score(uncertain_weight)
    )
    confidence = _confidence_from_score(score)
    interval_width = _CONFIDENCE_INTERVAL_WIDTH[confidence]
    confidence_interval = (total_return - interval_width, total_return + interval_width)

    uncovered_note: str | None = None
    if covered_weight < Decimal(100):
        uncovered_pct = Decimal(100) - covered_weight
        uncovered_pct_display = f"{uncovered_pct:.2f}".replace(".", ",")  # Turkce ondalik ayrac (virgul)
        uncovered_note = (
            f"Portföyün %{uncovered_pct_display}'i (fiyatlandırılamayan hisse/fon/türev/nakit "
            "kalemleri) tahmine dahil edilemedi -- bu kalemler %0 getiri VARSAYILDI, gerçek "
            "katkıları farklı olabilir."
        )

    return FundEstimate(
        fund_code=portfolio.fund_code,
        estimate_date=estimate_date if estimate_date is not None else date.today(),
        estimated_return_pct=total_return,
        confidence=confidence,
        confidence_interval=confidence_interval,
        covered_weight_pct=covered_weight,
        portfolio_staleness_days=staleness_days,
        contributions=contributions,
        uncovered_note=uncovered_note,
    )
