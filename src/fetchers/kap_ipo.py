"""KAP üzerinden SPK onaylı YENİ halka arz izahnamelerini keşfeden ve
izahname PDF'inden temel rakamları ayrıştıran fetcher -- Faz 20 (2026-08-06).

── KEŞİF (CANLI doğrulandı) ──
Yeni bir uç nokta/kaynak GEREKMEDİ. İzahnameyi halka arza ARACILIK EDEN
kurum (örn. A1 Capital) -- halka arz adayı şirketin (henüz kendi KAP
profili/borsa kaydı OLMAYABİLİR) DEĞİL -- KENDİ KAP profilinden
"İzahname (SPK Tarafından Onaylanan)" kategorisiyle yayınlıyor. Zaten
kullanılan `kap.py::fetch_disclosures_by_oid()` ile A1 Capital'in oid'i
sorgulanınca KARCL (Kardemir Çelik) izahnamesi + tüm ekleri (Ek-1..Ek-6.2)
+ fiyat tespit raporu + halka arz sonuçları dosya indeksleriyle GERÇEKTEN
bulundu (bkz. `data/exploration/karcl_izahname_ornek*`). Bildirimin
`stock_codes` alanı ARACININ kendi kodunu (örn. "A1CAP, ACP"), hedef
şirketin ticker'ı ise `related_stocks` alanını taşır (örn. "KARCL, VKY,
ZRY") -- bu ayrım CANLI doğrulanıp `kap.Disclosure.related_stocks`
alanı olarak eklendi (bkz. kap.py).

── PDF FORMATI (161 sayfalık ana izahname, CANLI doğrulandı) ──
SPK'nın kendi Tebliğ'iyle ZORUNLU KILINAN standart bir formatta: "Sulanma
Etkisi Analizi" tablosu Halka Arz Fiyatı/Büyüklüğü/Net Geliri, Özkaynaklar
(öncesi/sonrası), Ödenmiş Sermaye (öncesi/sonrası) gibi rakamları
etiket:değer formatında TEK yerde veriyor; tahsisat yüzdeleri ayrı bir
madde altında madde işaretli liste olarak geçiyor. Bu, PMC'ye göre
DEĞİŞEN fon portföy PDF şablonlarından (bkz. kap_fund_portfolio.py) DAHA
KOLAY bir problem -- format brokerage'a değil SPK'ya göre standart.
"Fon Kullanım Yeri Raporu" (Ek-5) ise AYRI bir bildirim/PDF olarak filed
ediliyor (ana izahnamenin "35. EKLER" bölümü sadece bir İÇİNDEKİLER
listesi, gerçek içerik DEĞİL).

⚠️ Bu modülde ayrıştırılan HER alan, metinde BEKLENEN etiketle TAM
eşleşme bulunamazsa None kalır (Kural 3: uydurma YAPILMAZ). Tahsisat ve
fon kullanım yeri kırılımları kendi GRUP TOPLAMLARIYLA (~%100)
öz-doğrulanır -- tutmuyorsa TÜMÜ None döner.

🚨 CANLI HATA + DÜZELTME (2026-08-07, kullanıcı raporu): keşif İLK
turda `UNDERWRITER_MEMBERS` adlı ~22 aracı kurumluk SABİT bir listeyi
tek tek tarayarak yapılıyordu -- kullanıcı Çitlekçi Mağazacılık'ın
izahnamesinin (aracısı: TERA YATIRIM, listede YOKTU) hiç bulunamadığını
bildirdi. Kök neden: `kap.py::DISCLOSURES_ENDPOINT`nin `mkkMemberOidList`
alanı BOŞ liste/hiç verilmezse KAP TÜM üyelerin bildirimlerini TEK
istekte döner (CANLI keşfedildi) -- bu, ASLA eksiksiz olamayacak bir
hardcoded kurum listesine (Bewen'in izahnamesini TSKB -- bir "aracı
kurum" bile sayılmayan bir üye -- yayınlamış!) tamamen SON VERİYOR.
YENİ `kap.fetch_all_disclosures()` bunu sağlıyor (bkz. o fonksiyonun
üst notu, yanıt 2000 satırda kesildiği için `days` en fazla ~10 olabilir
-- zaten kullanıcı isteği de "son 1 hafta yeter"). `UNDERWRITER_MEMBERS`/
`_resolve_underwriter_oid` TAMAMEN KALDIRILMADI --
`_find_use_of_proceeds_disclosure_index()` hâlâ TEK bir üyenin (artık
`filer_name`'den gelen GERÇEK/doğrulanmış unvan) profilini sorgulamak
için kullanıyor, o fonksiyon `fetch_all_disclosures`in 2000-satır
sınırına TABİ DEĞİL (tek üye taraması, `fetch_disclosures_by_oid`).
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from src.fetchers import kap

logger = logging.getLogger(__name__)

_IZAHNAME_CATEGORY = "İzahname (SPK Tarafından Onaylanan)"
_DEFAULT_DISCOVERY_DAYS = 7  # kullanıcı isteği (2026-08-07): "son 1 hafta yeter" -- ayrıca kap.fetch_all_disclosures'ın güvenli sınırının (10) altında
_COURTESY_DELAY_SECONDS = 0.4
# CANLI gözlemlenen sayılara dayanır (bkz. find_recent_izahnameler() üst notu):
# QUICK'in gerçek çok-parçalı belgesi AYNI başlığı 2 kez taşıyordu; Türker
# Vangölü Enerji'nin resubmission fırtınası AYNI başlığı 6-7 kez taşıyordu.
# Eşik ikisinin ARASINDA seçildi.
_TITLE_REPEAT_RESUBMISSION_THRESHOLD = 3

# CANLI GÖZLEMLENDİ (2026-08-06, KARCL/QUICK/Saat ve Saat karşılaştırması):
# aracı kurumlar İZAHNAME BAŞLIKLARI için TAMAMEN FARKLI kurallar kullanıyor --
# A1 Capital: ana belge "...Onaylı İzahname" (ek YOK), ekler "Ek-1".."Ek-6.2"
# şeklinde AYRI başlıklı; Garanti Yatırım (QUICK): ana belgenin KENDİSİ 4
# AYRI dosyaya (aynı başlıkla, "...İlişkin İzahname") bölünmüş, diğer TÜM
# ekler ("Hukukçu Raporu", "Gayrimenkul Değerleme Raporu" vb.) başlığında
# "izahname" kelimesi HİÇ GEÇMİYOR; Garanti Yatırım (Saat ve Saat): "(1.
# Kısım)"/"(2. Kısım)" ile bölünmüş. Tek bir "Ek-" filtresi bu 3 farklı
# kuralın SADECE ilkini doğru ayırt ediyordu. Sağlam kural: başlıkta
# "izahname" kelimesi GEÇMELİ (bu, tüm AYRI-adlı raporları otomatik
# ELER) VE "Ek-N" İÇERMEMELİ (A1 Capital'in eklerini eler) -- eşleşen
# TÜM parçalar (QUICK'in 4 parçası gibi) `fetch_and_parse_izahname()`'de
# BİRLEŞTİRİLİR (bkz. aşağısı), tek bir "ana" parça SEÇİLMEYE ÇALIŞILMAZ.
#
# 🚨 CANLI HATA + DÜZELTME (2026-08-07, kullanıcı raporu, Çitlekçi/TERA
# YATIRIM örneği): dar `\bEk-(\d+...)\b` deseni (SADECE "Ek-1" gibi
# tiresiz-bitişik format) Tera Yatırım'ın "Ek 1-", "Ek -2", "Ek 5-1",
# "Ek - 6.", "Ek 9 -" gibi BOŞLUKLU varyasyonlarının HİÇBİRİNİ
# yakalamıyordu -- sonuç: Çitlekçi'nin 19 EKİ (finansal tablolar, gayrimenkul
# değerleme raporları, hukukçu raporu vb. -- ana 161 sayfalık izahnameyle
# İLGİSİZ belgeler) "ana parça" sanılıp TÜMÜ indirilip metne
# BİRLEŞTİRİLİYORDU (20 PDF indirme -- hem çok yavaş hem de "Sulanma Etkisi
# Analizi" gibi anahtar ifadelerin YANLIŞ/gürültülü bir bağlamda tekrar
# geçmesi riski). Yeni desen `\bEk\b.{0,4}?\d` -- "Ek" kelimesinden SONRA
# en fazla 4 karakter içinde bir rakam geçiyorsa (hyphen/boşluk sırası NE
# OLURSA olsun) ek sayılır; TÜM gözlemlenen formatlarla (Ek-1, Ek 1-,
# Ek -2, Ek 5-1, Ek - 6., Ek 9 -, Ek 10-) CANLI test edildi. Grup 1 --
# `_find_use_of_proceeds_disclosure_index()`'in "Ek 5 mi?" kontrolü için --
# İLK rakam dizisini yakalar (örn. "Ek 5-1" -> "5", alt-madde numarası
# "1" YOKSAYILIR, sadece ana ek numarası önemli).
_EK_RE = re.compile(r"\bEk\b.{0,4}?(\d+)")
_IZAHNAME_KEYWORD_RE = re.compile(r"izahname", re.IGNORECASE)
_FON_KULLANIM_KEYWORD_RE = re.compile(r"fon kullanım", re.IGNORECASE)


def _is_izahname_part(title: str) -> bool:
    return bool(_IZAHNAME_KEYWORD_RE.search(title)) and not _EK_RE.search(title)


class KapIpoError(Exception):
    """Bu modül için taban hata sınıfı."""


# --- Keşif ("İzahname (SPK Tarafından Onaylanan)" taraması) -------------------------------


@dataclass(frozen=True)
class IzahnameDisclosure:
    # Faz 20 (canlı bulundu): ana belge bazen (Garanti Yatırım/QUICK gibi)
    # AYNI başlıkla birden fazla PARÇAYA bölünmüş oluyor -- bu yüzden TEK
    # bir disclosure_index değil, dosyalanma sırasına göre (en eski önce,
    # sayfa sırasıyla aynı olduğu varsayılır) SIRALI bir demet tutulur.
    disclosure_indices: tuple[int, ...]
    publish_date: date
    underwriter_name: str
    target_tickers: tuple[str, ...]
    summary: str


def _resolve_underwriter_oid(exact_name: str) -> str | None:
    """`exact_name`i KAP'ta arayıp TAM (case-insensitive) eşleşen üye
    oid'ini döner. Bulunamazsa None (Kural 9 -- bu kurum o an KAP'ta
    bulunamadıysa taramadan sessizce atlanır, tüm tarama ÇÖKMEZ)."""
    try:
        results = kap.search_company_by_name(exact_name)
    except kap.KapError as exc:
        logger.warning("%s için KAP araması başarısız: %s", exact_name, exc)
        return None
    normalized_target = exact_name.strip().upper()
    for r in results:
        if r.name.strip().upper() == normalized_target:
            return r.member_oid
    logger.info("%s KAP aramasında TAM eşleşme bulunamadı (bulunanlar: %s).", exact_name, [r.name for r in results])
    return None


def find_recent_izahnameler(days: int = _DEFAULT_DISCOVERY_DAYS) -> list[IzahnameDisclosure]:
    """`kap.fetch_all_disclosures(days)` (üye kısıtlaması OLMAYAN, TÜM KAP
    üyelerini TEK istekte tarayan uç nokta) ile son `days` günde onaylanmış
    TÜM izahnameleri bulur, en yeni önce -- her HEDEF ŞİRKET için TEK bir
    kayıt döner. `days`, `kap.fetch_all_disclosures`'ın güvenli sınırına
    (2000 satırda kesilme riski) tabidir -- ValueError'ı OLDUĞU GİBİ yukarı
    fırlatır.

    Gruplama anahtarı (filer_name, PRİMER ticker) -- `related_stocks`'un
    TAM kümesi DEĞİL, sadece ilk ticker: CANLI gözlemlendi (Türker Vangölü
    Enerji örneği) aynı şirketin ardışık resubmission'ları arasında
    related_stocks kümesi ("VEYAS, VKF, ZRY" vs "VEYAS, VKY, ZRY" gibi bir
    yazım düzeltmesiyle) TAM ÖRTÜŞMEYEBİLİYOR -- tam küme eşitliği bu
    durumda YANLIŞLIKLA iki AYRI grup oluştururdu.

    Bir grupta AYNI başlık BİRDEN FAZLA kez geçiyorsa (CANLI gözlemlendi --
    hem gerçek çok-parçalı belgeler, örn. Garanti Yatırım/QUICK'in 4
    parçası AYNI başlığı paylaşır, HEM DE Halk Yatırım/Türker Vangölü
    Enerji'de AYNI başlık ("...İzahname"/"...İzahname Ekleri", HİÇBİR
    ek numarası OLMADAN) kısa aralıklarla 6-7 KEZ yeniden filed edilmiş
    -- muhtemelen düzeltme/resubmission) bu İKİSİ başlık metninden TEK
    BAŞINA ayırt edilemez. CANLI gözlemlenen sayılara dayanan bir eşik
    kullanılır (`_TITLE_REPEAT_RESUBMISSION_THRESHOLD`): aynı başlık bu
    eşiği AŞMIYORSA (QUICK'in 2 tekrarı gibi) GERÇEK çok-parçalı belge
    sayılır, TÜMÜ tutulur; AŞIYORSA (Türker Vangölü'nün 6-7 tekrarı gibi)
    resubmission fırtınası sayılır, SADECE o başlığın EN YENİSİ (en büyük
    disclosure_index -- muhtemelen düzeltilmiş/son hali) tutulur."""
    disclosures = kap.fetch_all_disclosures(days=days)

    relevant = [
        d
        for d in disclosures
        if d.category == _IZAHNAME_CATEGORY and _is_izahname_part(d.title) and d.related_stocks.strip()
    ]

    groups: dict[tuple[str, str], list[kap.Disclosure]] = {}
    for d in relevant:
        primary_ticker = d.related_stocks.split(",")[0].strip()
        if not primary_ticker:
            continue
        groups.setdefault((d.filer_name, primary_ticker), []).append(d)

    results: list[IzahnameDisclosure] = []
    for (filer_name, _primary_ticker), items in groups.items():
        by_title: dict[str, list[kap.Disclosure]] = {}
        for d in items:
            by_title.setdefault(d.title, []).append(d)

        kept: list[kap.Disclosure] = []
        for title_items in by_title.values():
            if len(title_items) > _TITLE_REPEAT_RESUBMISSION_THRESHOLD:
                kept.append(max(title_items, key=lambda d: d.disclosure_index))
            else:
                kept.extend(title_items)

        deduped = sorted(kept, key=lambda d: d.disclosure_index)
        latest_overall = max(deduped, key=lambda d: d.disclosure_index)

        results.append(
            IzahnameDisclosure(
                disclosure_indices=tuple(d.disclosure_index for d in deduped),
                publish_date=latest_overall.date.date(),
                underwriter_name=filer_name,
                target_tickers=tuple(t.strip() for t in latest_overall.related_stocks.split(",") if t.strip()),
                summary=latest_overall.title,
            )
        )

    results.sort(key=lambda x: x.publish_date, reverse=True)
    return results


def find_izahname_for_ticker(ticker: str, days: int = _DEFAULT_DISCOVERY_DAYS) -> IzahnameDisclosure | None:
    """Belirli bir (henüz işlem görmeyen) ticker için en son izahnameyi
    bulur -- `find_recent_izahnameler()`'in doğrudan-arama kısayoludur."""
    ticker_upper = ticker.strip().upper()
    for disclosure in find_recent_izahnameler(days=days):
        if ticker_upper in disclosure.target_tickers:
            return disclosure
    return None


def _find_use_of_proceeds_disclosure_index(underwriter_name: str, primary_ticker: str, days: int = 60) -> int | None:
    """Aynı yayınlayıcının (`filer_name`, artık `UNDERWRITER_MEMBERS`
    sabitinden DEĞİL, canlı KAP verisinden geliyor) AYNI hedef şirket için
    yayınladığı "Fon Kullanım Yeri Raporu" bildirimini bulur -- ana
    izahnamenin "35. EKLER" bölümü sadece bir İÇİNDEKİLER listesi, gerçek
    içerik AYRI bir bildirim/PDF (CANLI doğrulandı, bkz. modül üst notu).
    ⚠️ Aracıya göre başlık "Ek-5" (A1 Capital) VEYA doğrudan "...Fon
    Kullanım Yerlerine İlişkin..." (Garanti Yatırım) olabilir -- ÖNCE
    anahtar kelime (daha güvenilir, aracıdan BAĞIMSIZ), bulunamazsa "Ek-5"
    deseni denenir. `target_tickers` TAM küme eşitliği YERİNE `primary_
    ticker` İÇERME kontrolü kullanır (bkz. `find_recent_izahnameler()` üst
    notu -- resubmission'lar arasında küme TAM örtüşmeyebiliyor, bu
    fonksiyon `days=60` ile `fetch_disclosures_by_oid`'in TEK ÜYE taraması
    olduğu için `fetch_all_disclosures`'ın 2000-satır sınırına TABİ
    DEĞİLDİR)."""
    oid = _resolve_underwriter_oid(underwriter_name)
    if oid is None:
        return None
    try:
        disclosures = kap.fetch_disclosures_by_oid(oid, days=days)
    except kap.KapError as exc:
        logger.warning("%s için fon kullanım yeri taraması başarısız: %s", underwriter_name, exc)
        return None

    candidates = [
        d
        for d in disclosures
        if d.category == _IZAHNAME_CATEGORY
        and primary_ticker in {t.strip() for t in d.related_stocks.split(",") if t.strip()}
    ]
    for d in candidates:
        if _FON_KULLANIM_KEYWORD_RE.search(d.title):
            return d.disclosure_index
    for d in candidates:
        ek_match = _EK_RE.search(d.title)
        if ek_match and ek_match.group(1) == "5":
            return d.disclosure_index
    return None


# --- PDF ayrıştırma (Sulanma Etkisi Analizi tablosu + Tahsisat) -------------------------------

_TR_NUM = r"-?\d{1,3}(?:\.\d{3})*(?:,\d+)?"


def _to_decimal(text: str) -> Decimal | None:
    """`kap_fund_portfolio._to_decimal()` ile AYNI Türkçe sayı formatı
    (nokta binlik ayraç, virgül ondalık) -- tek kaynak yerine burada da
    tanımlanmasının nedeni, bu modülün kap_fund_portfolio'nun PDF satır-
    pozisyon ayrıştırma mantığına DEĞİL, düz metin/regex ayrıştırmasına
    dayanması (farklı bir problem sınıfı, bkz. modül üst notu)."""
    cleaned = text.strip().rstrip("%").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


# CANLI GÖZLEMLENDİ (2026-08-07, KARCL/Çitlekçi karşılaştırması): "Sulanma
# Etkisi Analizi" tablosu SPK standardı OLMASINA RAĞMEN hazırlayan
# aracı kuruma göre BAZI etiketler FARKLI yazılıyor -- her alan için
# GERÇEK, doğrulanmış varyant(lar) alternation (`|`) ile eklenir; hiçbiri
# eşleşmezse (Kural 3) None kalmaya devam eder, uydurma YAPILMAZ.
_SINGLE_VALUE_FIELDS: tuple[tuple[str, re.Pattern], ...] = (
    ("offering_price", re.compile(r"Halka Arz Fiyatı\s+(" + _TR_NUM + r")")),
    # KARCL: "Artırılan Sermaye"; Çitlekçi: "Sermaye Artırımı (nominal TL)"
    ("capital_increase_amount", re.compile(r"(?:Artırılan Sermaye|Sermaye Artırımı \(nominal TL\))\s+(" + _TR_NUM + r")")),
    ("offering_size", re.compile(r"Halka Arz Büyüklüğü[^\n\d]{0,60}(" + _TR_NUM + r")")),
    # KARCL: "Tahmini Halka Arz Maliyeti"; Çitlekçi: "Halka Arz Masrafları*"
    (
        "estimated_offering_cost",
        re.compile(r"(?:Tahmini Halka Arz Maliyeti|Halka Arz Masrafları\*?)[^\n\d]{0,60}(" + _TR_NUM + r")"),
    ),
    ("net_offering_proceeds", re.compile(r"Net Halka Arz Geliri[^\n\d]{0,60}(" + _TR_NUM + r")")),
    # Çitlekçi "Mevcut Ortaklar İçin (pozitif) Sulanma Etkisi (%)" -- KARCL'da "(pozitif)" ARA SÖZü YOK
    ("dilution_existing_pct", re.compile(r"Mevcut Ortaklar İçin(?:\s*\([^)]{0,20}\))?\s+Sulanma Etkisi \(%\)\s+(" + _TR_NUM + r")")),
    ("dilution_new_pct", re.compile(r"Yeni Ortaklar İçin(?:\s*\([^)]{0,20}\))?\s+Sulanma Etkisi \(%\)\s+(" + _TR_NUM + r")")),
)

_PAIR_VALUE_FIELDS: tuple[tuple[str, str, re.Pattern], ...] = (
    ("equity_before", "equity_after", re.compile(r"Özkaynaklar \(Defter Değeri\)\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")")),
    ("paid_capital_before", "paid_capital_after", re.compile(r"Ödenmiş Sermaye\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")")),
    (
        "book_value_per_share_before",
        "book_value_per_share_after",
        re.compile(r"Pay Başına Defter Değeri\s+(" + _TR_NUM + r")\s+(" + _TR_NUM + r")"),
    ),
)

# CANLI GÖZLEMLENDİ (2026-08-07, KARCL/Çitlekçi karşılaştırması): tahsisat
# bloğu da aracı kuruma göre İKİ FARKLI biçimde yazılıyor -- KARCL "•"
# madde imi + "kısmı (PCT%)" (yüzde SONDA, parantez içinde); Çitlekçi "-"
# madde imi + "%PCT oranındaki kısmı" (yüzde ÖNDE, "oranındaki" ile).
# Kapanış ibaresi de farklı ("...gerçekleştirilecek satışlar için tahsis
# edilmiştir" [KARCL] vs sadece "...tahsis edilmiştir" [Çitlekçi]) --
# ortak alt küme ("tahsis edilmiştir") kapanış çapası olarak kullanılır.
# Blok açılışındaki TOPLAM nominal tutar da AYRICA yakalanır (grup 1) --
# `extract_ipo_facts()` bunu "Halka Arz Büyüklüğü" etiketi hiç
# BULUNAMADIĞINDA (Çitlekçi'de olduğu gibi -- bu etiket belgede HİÇ
# GEÇMİYOR, CANLI doğrulandı) `offering_price` ile çarparak offering_size
# TÜRETMEK için kullanır (Kural 1'e AYKIRI DEĞİL: LLM'e değil, burada SAF
# Python çarpımına dayanır, ikisi de belgeden GERÇEKTEN okunmuş rakamlar).
_ALLOCATION_BLOCK_RE = re.compile(
    r"Halka arz edilecek toplam\s+(" + _TR_NUM + r")\s*TL nominal değerli\s*\n?payların;(.*?)tahsis edilmiştir",
    re.DOTALL,
)
_ALLOCATION_ROW_RE = re.compile(
    r"[•\-]\s*" + _TR_NUM + r"\s*TL nominal değerdeki(?:\s*kısmı\s*\((" + _TR_NUM + r")%?\)"
    r"|\s*%(" + _TR_NUM + r")\s*oranındaki kısmı)\s*(.+?)(?=[•\-]\s*\d|\ngerçekleştirilecek|\Z)",
    re.DOTALL,
)
_GROUP_TOTAL_TOLERANCE = Decimal("2.0")

_USE_OF_PROCEEDS_HEADING_RE = re.compile(r"^\(?(\d+)\)?\s+([A-ZÇĞİÖŞÜ][^\n]{4,90})$", re.MULTILINE)
_INLINE_PCT_RE = re.compile(r"%(\d{1,3}(?:,\d+)?)")


# CANLI HATA + DÜZELTME (KARCL ile bulundu): "Ödenmiş Sermaye"/"Özkaynaklar"
# gibi etiketler izahnamenin BAŞINDAKİ geçmiş finansal tablo özetinde de
# (farklı bir bağlamda, örn. 4 dönemlik bir seri) tekrar geçebiliyor --
# `.search()` (ilk eşleşme) bu yüzden YANLIŞ değeri (örn. Ödenmiş Sermaye
# "sonrası" için 830.000.000 yerine tekrar 720.000.000) yakalayabiliyordu.
# Çözüm: TÜM alanlar "Sulanma Etkisi Analizi" tablosuyla SINIRLI bir metin
# penceresinde aranır -- bu başlık (ve altındaki "Halka Arz Fiyatı" ilk
# satırı) CANLI doğrulandığı üzere belgede TEK YERDE geçiyor.
_DILUTION_TABLE_ANCHOR_RE = re.compile(r"Sulanma Etkisi Analizi|Halka Arz Fiyatı")
_DILUTION_TABLE_WINDOW_CHARS = 2500


def _dilution_table_window(text: str) -> str | None:
    match = _DILUTION_TABLE_ANCHOR_RE.search(text)
    if not match:
        return None
    return text[match.start() : match.start() + _DILUTION_TABLE_WINDOW_CHARS]


def _extract_single_values(text: str) -> dict[str, Decimal | None]:
    window = _dilution_table_window(text)
    if window is None:
        logger.warning("İzahname metninde 'Sulanma Etkisi Analizi' tablosu bulunamadı -- ilgili alanlar None kalacak.")
        window = ""

    values: dict[str, Decimal | None] = {}
    for field_name, pattern in _SINGLE_VALUE_FIELDS:
        match = pattern.search(window)
        values[field_name] = _to_decimal(match.group(1)) if match else None
    for before_name, after_name, pattern in _PAIR_VALUE_FIELDS:
        match = pattern.search(window)
        if match:
            values[before_name] = _to_decimal(match.group(1))
            values[after_name] = _to_decimal(match.group(2))
        else:
            values[before_name] = None
            values[after_name] = None
    return values


def _parse_allocation(text: str) -> dict[str, Decimal] | None:
    """Tahsisat yüzdelerini (Yurt İçi Bireysel/Kurumsal, Yurt Dışı Kurumsal
    vb.) madde işaretli listeden ayrıştırır. Öz-doğrulama (Kural 3): grup
    toplamı ~%100 değilse (satır kaybı/format sapması) TÜMÜ None döner."""
    block_match = _ALLOCATION_BLOCK_RE.search(text)
    if not block_match:
        return None
    block = block_match.group(2)

    rows: dict[str, Decimal] = {}
    total = Decimal(0)
    for row_match in _ALLOCATION_ROW_RE.finditer(block):
        pct = _to_decimal(row_match.group(1) or row_match.group(2))
        label = " ".join(row_match.group(3).split()).rstrip(",.").strip()
        if pct is None or not label:
            continue
        rows[label] = rows.get(label, Decimal(0)) + pct
        total += pct

    if not rows or abs(total - Decimal(100)) > _GROUP_TOTAL_TOLERANCE:
        if rows:
            logger.warning("İzahname tahsisat toplamı %%100'den sapıyor (%s) -- güvenilir değil, boş dönüyor.", total)
        return None
    return rows


def _total_nominal_offering(text: str) -> Decimal | None:
    """"Halka arz edilecek toplam X TL nominal değerli payların;" cümlesinden
    TOPLAM nominal tutarı çeker -- `extract_ipo_facts()`'ta `offering_size`
    "Halka Arz Büyüklüğü" etiketiyle bulunamadığında (Çitlekçi'de bu etiket
    belgede HİÇ GEÇMİYOR, CANLI doğrulandı) `offering_price` ile çarpılarak
    offering_size türetmek için kullanılır."""
    match = _ALLOCATION_BLOCK_RE.search(text)
    return _to_decimal(match.group(1)) if match else None


def _parse_use_of_proceeds(text: str) -> dict[str, Decimal] | None:
    """"Fon Kullanım Yeri Raporu"ndaki numaralı maddelerden (her biri KENDİ
    metninde TEK bir "%N" oranı içerir) bir kırılım çıkarır. Bir madde
    hiç yüzde içermiyorsa VEYA BİRDEN FAZLA yüzde içeriyorsa (hangisinin
    "asıl" oran olduğu BELİRSİZLEŞİR) Kural 3 gereği TÜM sözlük None
    döner -- kısmi/belirsiz bir kırılım GÖSTERİLMEZ."""
    headings = list(_USE_OF_PROCEEDS_HEADING_RE.finditer(text))
    if not headings:
        return None

    rows: dict[str, Decimal] = {}
    total = Decimal(0)
    for i, heading in enumerate(headings):
        label = " ".join(heading.group(2).split()).strip()
        span_start = heading.end()
        span_end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        section_text = text[span_start:span_end]

        pct_matches = _INLINE_PCT_RE.findall(section_text)
        if len(pct_matches) != 1:
            continue  # belirsiz (0 veya >1 oran) -- bu maddeyi ATLA, toplamı BOZMAMASI icin dahil edilmez
        pct = _to_decimal(pct_matches[0])
        if pct is None:
            continue
        rows[label] = rows.get(label, Decimal(0)) + pct
        total += pct

    if not rows or abs(total - Decimal(100)) > _GROUP_TOTAL_TOLERANCE:
        if rows:
            logger.warning("İzahname fon kullanım yeri toplamı %%100'den sapıyor (%s) -- güvenilir değil, boş dönüyor.", total)
        return None
    return rows


@dataclass(frozen=True)
class IpoFacts:
    offering_price: Decimal | None
    capital_increase_amount: Decimal | None
    offering_size: Decimal | None
    estimated_offering_cost: Decimal | None
    net_offering_proceeds: Decimal | None
    equity_before: Decimal | None
    equity_after: Decimal | None
    paid_capital_before: Decimal | None
    paid_capital_after: Decimal | None
    book_value_per_share_before: Decimal | None
    book_value_per_share_after: Decimal | None
    dilution_existing_pct: Decimal | None
    dilution_new_pct: Decimal | None
    allocation_breakdown: dict[str, Decimal] | None
    use_of_proceeds: dict[str, Decimal] | None


def extract_ipo_facts(izahname_text: str, use_of_proceeds_text: str | None = None) -> IpoFacts:
    """Ana izahname metninden (ve varsa AYRICA çekilmiş Ek-5 metninden)
    `IpoFacts`'i üretir -- SAF ayrıştırma, ağ erişimi YOK (bkz.
    `fetch_and_parse_izahname()` orkestrasyon katmanı)."""
    values = _extract_single_values(izahname_text)
    allocation = _parse_allocation(izahname_text)
    use_of_proceeds = _parse_use_of_proceeds(use_of_proceeds_text) if use_of_proceeds_text else None

    offering_size = values.get("offering_size")
    offering_price = values.get("offering_price")
    if offering_size is None and offering_price is not None:
        # "Halka Arz Büyüklüğü" etiketi bazı izahnamelerde (Çitlekçi, CANLI
        # doğrulandı) HİÇ GEÇMİYOR -- tahsisat bloğunun açılışındaki TOPLAM
        # nominal tutar (bkz. _total_nominal_offering) fiyatla çarpılarak
        # türetilir. İkisi de belgeden GERÇEKTEN okunmuş rakamlar (Kural 1'e
        # aykırı değil); tahsisat bloğu da bulunamazsa None kalmaya devam eder.
        total_nominal = _total_nominal_offering(izahname_text)
        if total_nominal is not None:
            offering_size = total_nominal * offering_price

    return IpoFacts(
        offering_price=offering_price,
        capital_increase_amount=values.get("capital_increase_amount"),
        offering_size=offering_size,
        estimated_offering_cost=values.get("estimated_offering_cost"),
        net_offering_proceeds=values.get("net_offering_proceeds"),
        equity_before=values.get("equity_before"),
        equity_after=values.get("equity_after"),
        paid_capital_before=values.get("paid_capital_before"),
        paid_capital_after=values.get("paid_capital_after"),
        book_value_per_share_before=values.get("book_value_per_share_before"),
        book_value_per_share_after=values.get("book_value_per_share_after"),
        dilution_existing_pct=values.get("dilution_existing_pct"),
        dilution_new_pct=values.get("dilution_new_pct"),
        allocation_breakdown=allocation,
        use_of_proceeds=use_of_proceeds,
    )


def _pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def fetch_and_parse_izahname(disclosure: IzahnameDisclosure) -> IpoFacts | None:
    """Ana izahnamenin TÜM parçalarını (`disclosure.disclosure_indices` --
    bazı aracılarda birden fazla, bkz. `_is_izahname_part` üst notu)
    indirip BİRLEŞTİRİR, artı bulunabilirse fon kullanım yeri raporunu
    çeker, `IpoFacts`'i üretir. HİÇBİR parça indirilemezse (Kural 9) None
    döner -- fon kullanım yeri raporu AYRI/İKİNCİL sayılır, bulunamazsa
    SADECE `use_of_proceeds=None` kalır, TÜM sonuç iptal EDİLMEZ."""
    parts: list[str] = []
    for idx in disclosure.disclosure_indices:
        pdf_bytes = kap.fetch_disclosure_attachment_pdf(idx)
        if pdf_bytes is None:
            logger.warning("İzahname bildirimi %s için PDF indirilemedi, atlanıyor.", idx)
            continue
        parts.append(_pdf_bytes_to_text(pdf_bytes))
        time.sleep(_COURTESY_DELAY_SECONDS)

    if not parts:
        logger.warning("%s için izahnamenin HİÇBİR parçası indirilemedi.", disclosure.target_tickers)
        return None
    izahname_text = "\n".join(parts)

    use_of_proceeds_text: str | None = None
    try:
        primary_ticker = disclosure.target_tickers[0] if disclosure.target_tickers else ""
        fon_index = _find_use_of_proceeds_disclosure_index(disclosure.underwriter_name, primary_ticker)
        if fon_index is not None:
            fon_pdf = kap.fetch_disclosure_attachment_pdf(fon_index)
            if fon_pdf is not None:
                use_of_proceeds_text = _pdf_bytes_to_text(fon_pdf)
    except Exception:  # noqa: BLE001 -- Kural 9: fon kullanım yeri ikincildir, hata TÜM sonucu ÇÖKERTMEMELİ
        logger.warning("Fon kullanım yeri raporu çekilirken hata oluştu, o bölüm olmadan devam ediliyor.", exc_info=True)

    return extract_ipo_facts(izahname_text, use_of_proceeds_text)
