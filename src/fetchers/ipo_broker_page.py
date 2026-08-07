"""Halka arz kartı için İKİNCİL (Kural 9) zenginleştirme kaynağı -- 2026-08-07.

KAP'ın "Tasarruf Sahiplerine Satış Duyurusu" belgesi (talep toplama tarihi/
günü, Katılım Endeksi uygunluğu, fiyat istikrarı gibi alanların GERÇEK
kaynağı) canlı test edilen 3/3 örnekte (VEYAS/CITAS/BEWEN) taranmış
görüntüden oluşuyor -- pdfplumber 0 karakter döndürüyor, OCR olmadan
OKUNAMIYOR (bkz. kap_ipo.py modül üst notu). Kullanıcı, bu alanları KAP
dışında yaygın kullanılan bir halka arz takip sitesinden (halkarz.com)
çekmeyi TERCİH ETTİ (2026-08-07, canlı istek: "bu sitelerde ... çekmeye
çalış").

⚠️ Bu KAP gibi RESMİ/BİRİNCİL bir kaynak DEĞİLDİR -- üçüncü taraf bir web
sitesi:
  - Öncelik SIRASI HER ZAMAN izahname (`kap_ipo.py`) -- burası SADECE
    izahnamenin İLGİLİ alanı `None` kaldığında YEDEK (fallback) olarak
    kullanılır, gerçek bir KAP rakamının ÜZERİNE YAZMAZ.
  - Herhangi bir adımda (site yapısı değişmiş, ağ hatası, ticker
    bulunamadı) başarısız olursa SESSİZCE None döner -- ana kart/pipeline
    ASLA bloklanmaz/çökmez (Kural 9).
  - Kartta bu alanların yanında kaynağı AÇIKÇA belirtilir ("kaynak:
    halkarz.com") -- KAP izahnamesinden geldiği izlenimi VERİLMEZ.

🚨 CANLI BULGU + GENİŞLETME (2026-08-07, kullanıcı raporu): VEYAS'ın
izahnamesi (TÜM 8 resubmission'ı tek tek denendi -- `_TITLE_REPEAT_
RESUBMISSION_THRESHOLD` yüzünden dedup'lanıp SADECE en yenisi tutuluyordu,
ama en ESKİ 7 tanesi de KONTROL EDİLDİ) İSTİSNASIZ taranmış/OCR'siz --
kart neredeyse tamamen boş kalıyordu (Fiyat/Büyüklük/Lot/Tahsisat/Tahmini
Dağıtım HİÇBİRİ yoktu). halkarz.com'un AYNI "Özet Bilgiler" widget'ı
ASLINDA fiyat/lot/tahsisat/tahmini-dağıtım rakamlarını da (Çitlekçi
örneğinde bizim SAF matematiğimizle BİREBİR eşleşerek doğrulanan
"Dağıtılacak Pay Miktarı" tablosu dahil) içeriyor -- bu yüzden kapsam
genişletildi: `offering_price_text`/`total_lot_text`/`distribution_method_text`
(sp-table'dan) + `allocation_lines`/`estimated_distribution_lines`
(sp-arz-extra'dan) eklendi. Bunlar `ipo_card.py`'de SADECE izahnameden
gelen karşılığı `None` ise (fallback), AYRI/açıkça "kaynak: halkarz.com"
etiketli bir blokta gösterilir -- ASLA bizim `ipo_assessment.py`'nin SAF
matematiğiyle KARIŞTIRILMAZ (Decimal'e çevrilip yeniden hesaplanmaz,
sadece siteden okunduğu GİBİ metin olarak gösterilir, Kural 1/2'ye
uygun -- burası bir HESAPLAMA değil bir ALINTI).

── KEŞİF (CANLI doğrulandı, Çitlekçi/CITAS örneği, 2026-08-07) ──
`https://halkarz.com/?s={ticker}` arama sonucu `article.index-list` bloğu
içindeki `h2.il-bist-kod` (BIST kodu, TAM eşleşme) ile hedef şirketin detay
sayfası bulunur. Detay sayfasında İKİ ayrı yapılandırılmış blok var:
  1. `table.sp-table` -- "Halka Arz Tarihi" satırındaki `<time>` etiketi
     talep toplama tarihini (örn. "10-11-12 Ağustos 2026") taşır, yanındaki
     `<small>` saat aralığını taşır.
  2. `article.sp-arz-extra` içindeki `<li><h5>Etiket</h5><p>İçerik</p></li>`
     çiftleri -- "Fiyat İstikrarı"/"Halka Arz Satış Yöntemi" gibi etiketli
     serbest metin blokları. Aynı bloğun SONUNDA "Katılım Endeksine uygun.
     (XKTUM)" / "...uygun değil" şeklinde bir dipnot satırı var -- bu ayrı
     bir h5/p ÇİFTİ DEĞİL, düz metin dipnotu, bu yüzden tüm makale metni
     üzerinde regex ile aranır.

data/exploration/halkarz_citas.html + halkarz_search_citas.html'de kanıt
olarak saklıdır (Kural 3/12: keşif kanıtı silinmez).

🚨 CANLI BULGU 2 (2026-08-07, aynı gün üçüncü tur, kullanıcı raporu:
"katılım sayısı ... 2 milyon veya 150 bin saçma kaçıyor"): halkarz.com'un
KENDİ "Dağıtılacak Pay Miktarı (Olası)" tablosu yuvarlak olmayan katılımcı
sayıları kullanıyor (150 Bin, 2,2 Milyon gibi) -- bunları OLDUĞU GİBİ
alıntılamak yerine, buradan SADECE ham "Tahsisat Grupları" (bireysel grup
lot sayısı) + "Halka Arz Fiyatı" rakamlarını Decimal'e çevirip `ipo_
assessment.estimate_retail_distribution()`i (AYNI standart/yuvarlak
senaryo listesiyle, `_DISTRIBUTION_SCENARIO_PARTICIPANTS`) ÇAĞIRIYORUZ --
sonuç TÜM kartlarda (izahname okunsun/okunmasın) TUTARLI bir senaryo
listesi üretir. ⚠️ Bu, bir fetcher'ın analiz katmanını İÇE AKTARMASI
(normalde TERS yön) -- BİLİNÇLİ bir istisna: `ipo_assessment`in ilgili
fonksiyonları SAF matematik (I/O yok), burada TEKRAR YAZILMASINDANSA
(kod tekrarı) yeniden kullanılması tercih edildi. Aynı ilkeyle "Halka Arz
Şekli" bloğundan (Sermaye Artırımı/Ortak Satışı LOT'ları) `ipo_assessment.
estimate_capital_vs_partner_pct()` ile sermaye artırımı/ortak satışı
yüzdesi de türetiliyor (VEYAS'ta CANLI doğrulandı: %57,7/%42,3).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.analysis import ipo_assessment
from src.formatting import format_number_tr

logger = logging.getLogger(__name__)

_BASE_URL = "https://halkarz.com/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

_PARTICIPATION_INDEX_RE = re.compile(
    r"Kat[ıi]l[ıi]m Endeksine (uygun de[gğ]il|uygun)(?:[^(]{0,40}\(([A-ZÇĞİÖŞÜ]{3,8})\))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SupplementaryIpoInfo:
    """`kap_ipo.IpoFacts`in KAPSAMADIĞI, halkarz.com'dan (ikincil kaynak)
    best-effort okunan alanlar. Her alan ayrı ayrı None olabilir (Kural 3).

    `offering_price_text`/`total_lot_text`/`distribution_method_text`/
    `allocation_lines`/`estimated_distribution_lines` (2026-08-07 eklendi):
    izahname OCU'suz kaldığında (VEYAS gibi) FALLBACK olarak kullanılır --
    bilerek DÜZ METİN (Decimal DEĞİL): bunlar bizim hesaplamamız değil,
    siteden OLDUĞU GİBİ alıntılanan rakamlardır, `ipo_assessment.py`'nin
    SAF matematiğine hiç KARIŞTIRILMAZ."""

    demand_period_display: str | None  # örn. "10-11-12 Ağustos 2026"
    demand_period_hours: str | None  # örn. "09:00-17:00"
    participation_index_compliant: bool | None
    participation_index_name: str | None  # örn. "XKTUM"
    price_stabilization_note: str | None
    sales_method_note: str | None
    source_url: str
    # --- İzahname OCR'siz kaldığında FALLBACK (Kural 1/2: alıntı, hesap değil) ---
    offering_price_text: str | None = None  # örn. "136,00 TL"
    total_lot_text: str | None = None  # örn. "65.000.000" ("Pay" satırı, "Lot" birimi ayıklanmış -- "Ek Pay"/greenshoe HARİÇ)
    offering_size_text: str | None = None  # örn. "～ 10,5 Milyar TL. (Ek satış dahil.)"
    distribution_method_text: str | None = None  # örn. "Eşit Dağıtım"
    allocation_lines: tuple[str, ...] | None = None  # örn. ("Yurt İçi Bireysel Yatırımcı: %45 (29.250.000 Lot)", ...)
    # AYNI standart senaryo listesiyle (izahname okunabildiğinde kullanılanla
    # BİREBİR) `ipo_assessment.estimate_retail_distribution()` ÇAĞRILARAK
    # üretilir -- halkarz.com'un KENDİ (yuvarlak olmayan) senaryo tablosu
    # KULLANILMAZ (kullanıcı isteği, 2026-08-07 üçüncü tur).
    estimated_retail_distribution: tuple[tuple[int, Decimal, Decimal], ...] | None = None
    capital_increase_pct_fallback: Decimal | None = None
    partner_sale_pct_fallback: Decimal | None = None
    is_pure_capital_increase_fallback: bool = False


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _get(url: str, params: dict | None = None) -> httpx.Response:
    response = httpx.get(url, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True)
    response.raise_for_status()
    return response


def _find_page_url(ticker: str) -> str | None:
    response = _get(_BASE_URL, params={"s": ticker.strip().upper()})
    soup = BeautifulSoup(response.text, "html.parser")
    for article in soup.select("article.index-list"):
        kod_tag = article.select_one("h2.il-bist-kod")
        if kod_tag is None or kod_tag.get_text(strip=True).upper() != ticker.strip().upper():
            continue
        link_tag = article.select_one("a[href]")
        if link_tag is not None:
            return link_tag["href"]
    return None


def _parse_demand_period(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    time_tag = soup.select_one("table.sp-table time")
    if time_tag is None:
        return None, None
    period = time_tag.get_text(strip=True) or None
    hours = None
    small_tag = time_tag.find_next("small")
    if small_tag is not None:
        hours_text = small_tag.get_text(" ", strip=True)
        hours_match = re.search(r"\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}", hours_text)
        hours = hours_match.group(0) if hours_match else None
    return period, hours


# halkarz.com her satırın sonuna kaynak dipnotu ekliyor (örn. "* İzahname,
# Sayfa 229."/"* Fiyat Tespit Raporu, Sayfa 53.") -- kart üzerinde gösterime
# uygun olmadığı için (bizim gerçek izahname sayfa numaramızla eşleşmesi
# GARANTİ değil, kafa karıştırır) bu satırlar ayıklanır.
_FOOTNOTE_LINE_RE = re.compile(r"^\*\s*(İzahname|Fiyat Tespit Raporu|SPK Bülteni)", re.IGNORECASE)


def _clean_extra_field_text(raw: str) -> str:
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line or _FOOTNOTE_LINE_RE.match(line):
            continue
        line = line.lstrip("-*～").strip().rstrip(".").strip()
        if line:
            lines.append(line)
    return ", ".join(lines)


_LOT_SUFFIX_RE = re.compile(r"\s*Lot\s*$", re.IGNORECASE)


def _strip_lot_suffix(text: str | None) -> str | None:
    """`total_lot_text`'i (`format_number_tr()`'ın döndürdüğü BİRİNCİL yoldaki
    "65.000.000" gibi salt sayı biçimiyle TUTARLI kalması için) sondaki
    "Lot" birimini ayıklar -- aksi halde çağıran taraflar (örn. `build_ipo_
    analysis_text()`) kendi "Lot" ekini de eklediğinde "65.000.000 Lot Lot"
    gibi çift birim ortaya çıkıyordu (CANLI bulundu, VEYAS)."""
    if text is None:
        return None
    return _LOT_SUFFIX_RE.sub("", text).strip() or None


def _parse_extra_fields(soup: BeautifulSoup) -> dict[str, str]:
    fields: dict[str, str] = {}
    for li in soup.select("article.sp-arz-extra li"):
        h5 = li.find("h5")
        p = li.find("p")
        if h5 is None or p is None:
            continue
        cleaned = _clean_extra_field_text(p.get_text("\n", strip=True))
        if cleaned:
            fields[h5.get_text(strip=True)] = cleaned
    return fields


def _parse_sp_table_fields(soup: BeautifulSoup) -> dict[str, str]:
    """`table.sp-table`'daki `<em>Etiket : </em><td>Değer</td>` satır
    çiftlerini (CANLI doğrulandı, CITAS/VEYAS) düz bir sözlüğe çevirir."""
    fields: dict[str, str] = {}
    table = soup.select_one("table.sp-table")
    if table is None:
        return fields
    for row in table.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        em = cells[0].find("em")
        label = (em.get_text(strip=True) if em is not None else cells[0].get_text(strip=True)).rstrip(" :").strip()
        value = cells[1].get_text(" ", strip=True)
        if label and value:
            fields[label] = value
    return fields


def _to_decimal(text: str | None) -> Decimal | None:
    """`kap_ipo._to_decimal()` ile AYNI Türkçe sayı formatı (nokta binlik
    ayraç, virgül ondalık) -- tek kaynağa taşınmadı çünkü bu modül PDF değil
    HTML metni ayrıştırıyor (farklı bir problem sınıfı, aynı gerekçe
    kap_ipo.py'nin kendi `_to_decimal()`'ı için de geçerli)."""
    if not text:
        return None
    match = re.search(r"-?\d{1,3}(?:\.\d{3})*(?:,\d+)?", text)
    if not match:
        return None
    cleaned = match.group(0).replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


# "Tahsisat Grupları" satırı örneği (CANLI, CITAS/VEYAS): "- 29.250.000 Lot
# (%45) Yurt İçi Bireysel Yatırımcı". Eşleşmeyen satırlar (örn. "Ek satış
# için herhangi bir sınırlama yoktur.") sessizce ATLANIR.
_ALLOCATION_LINE_RE = re.compile(r"^([\d.]+)\s*Lot\s*\(%([\d,]+)\)\s*(.+)$")

# "Halka Arz Şekli" satırı örneği: "Sermaye Artırımı : 37.500.000 Lot" /
# "Ortak Satışı : 27.500.000 Lot (...)" -- "Ek Ortak Satışı" "Ek" ile
# başladığı için bu ÇAPALI desenle eşleşmez, bilerek greenshoe/ek satış
# HARİÇ tutulur ("Pay"/total_lot_text ile AYNI kapsam, tutarlılık için).
_CAPITAL_STRUCTURE_LINE_RE = re.compile(r"^(Sermaye Artırımı|Ortak Satışı)\s*:\s*([\d.]+)\s*Lot", re.IGNORECASE)


def _parse_allocation_structured(text: str | None) -> list[tuple[str, Decimal, Decimal]]:
    """"Tahsisat Grupları" metnini (label, yüzde, lot) Decimal üçlülerine
    çevirir -- HEM kart üzerindeki görüntüleme metnini HEM de "Tahmini
    Dağıtım" hesabı için gereken bireysel grup lot sayısını üretmek için."""
    if not text:
        return []
    rows: list[tuple[str, Decimal, Decimal]] = []
    for raw_line in text.split(","):  # _clean_extra_field_text zaten ", " ile birleştirdi
        match = _ALLOCATION_LINE_RE.match(raw_line.strip())
        if not match:
            continue
        lot, pct, label = match.groups()
        lot_decimal = _to_decimal(lot)
        pct_decimal = _to_decimal(pct)
        if lot_decimal is not None and pct_decimal is not None:
            rows.append((label.strip(), pct_decimal, lot_decimal))
    return rows


def _parse_capital_structure(text: str | None) -> tuple[Decimal | None, Decimal | None]:
    """"Halka Arz Şekli" metninden Sermaye Artırımı/Ortak Satışı LOT
    sayılarını döner -- CANLI doğrulandı (VEYAS: 37.500.000/27.500.000,
    toplamı `total_lot_text`teki "Pay" [65.000.000] ile BİREBİR eşleşti).

    🚨 CANLI HATA + DÜZELTME (2026-08-07, otuz birinci tur, KPEKS örneği):
    bu alan SADECE İKİ satır (Sermaye Artırımı / Ortak Satışı) içerebilir --
    biri EKSİKSE bu "veri eksik" DEĞİL, "o bileşen sıfır" anlamına gelir
    (KPEKS'in "Halka Arz Şekli" metninde SADECE "Sermaye Artırımı : 25.100.000
    Lot" var, "Ortak Satışı" satırı HİÇ YOK -- CANLI, izahnamenin KENDİ
    giriş cümlesiyle de doğrulandı: "...25.100.000 TL nominal değerli
    25.100.000 adet ... payın halka arzına ilişkin izahnamedir", yani arzın
    TAMAMI yeni sermaye artırımı payı, ortak satışı YOK). Önceki davranış
    (bulunamayan bileşen None kalır) `estimate_capital_vs_partner_pct()`'te
    HER İKİSİ de None olmadıkça hesap yapılmadığı için TÜM "Sermaye Artırımı
    vs Ortak Satışı" bölümünü sessizce gizliyordu -- oysa halkarz.com'un
    KENDİSİ zaten net bir sinyal veriyordu (satırın YOKLUĞU = sıfır).
    Sadece İKİ satırdan EN AZ BİRİ bulunduysa diğeri 0'a düşürülür; İKİSİ DE
    yoksa (metin tamamen boş/alakasız) None/None olarak kalır (Kural 3)."""
    if not text:
        return None, None
    capital_lot: Decimal | None = None
    partner_lot: Decimal | None = None
    for raw_line in text.split(","):
        match = _CAPITAL_STRUCTURE_LINE_RE.match(raw_line.strip())
        if not match:
            continue
        label, digits = match.groups()
        value = _to_decimal(digits)
        if label.strip().lower().startswith("sermaye"):
            capital_lot = value
        else:
            partner_lot = value
    if capital_lot is not None and partner_lot is None:
        partner_lot = Decimal(0)
    elif partner_lot is not None and capital_lot is None:
        capital_lot = Decimal(0)
    return capital_lot, partner_lot


def _parse_participation_index(soup: BeautifulSoup) -> tuple[bool | None, str | None]:
    extra_block = soup.select_one("article.sp-arz-extra")
    haystack = extra_block.get_text(" ", strip=True) if extra_block is not None else soup.get_text(" ", strip=True)
    match = _PARTICIPATION_INDEX_RE.search(haystack)
    if not match:
        return None, None
    compliant = "değil" not in match.group(1).lower() and "degil" not in match.group(1).lower()
    return compliant, match.group(2)


def fetch_supplementary_ipo_info(ticker: str) -> SupplementaryIpoInfo | None:
    """`ticker` için halkarz.com'dan best-effort tamamlayıcı bilgi çeker.
    HERHANGİ bir adımda başarısız olursa (Kural 9) None döner, hata
    FIRLATMAZ -- çağıran taraf (ipo_pipeline) bu alanları YOKSA kartta
    ilgili bölümleri basitçe göstermez."""
    try:
        page_url = _find_page_url(ticker)
        if page_url is None:
            logger.info("halkarz.com: '%s' için sayfa bulunamadı (ikincil kaynak, kart bu alanlar olmadan üretilecek).", ticker)
            return None

        response = _get(page_url)
        soup = BeautifulSoup(response.text, "html.parser")

        demand_period, demand_hours = _parse_demand_period(soup)
        extra_fields = _parse_extra_fields(soup)
        sp_table_fields = _parse_sp_table_fields(soup)
        participation_compliant, participation_index_name = _parse_participation_index(soup)

        price_stabilization_note = extra_fields.get("Fiyat İstikrarı")
        sales_method_note = extra_fields.get("Halka Arz Satış Yöntemi")
        offering_price_text = sp_table_fields.get("Halka Arz Fiyatı/Aralığı")
        total_lot_text = _strip_lot_suffix(sp_table_fields.get("Pay"))
        offering_size_text = extra_fields.get("Halka Arz Büyüklüğü")
        distribution_method_text = sp_table_fields.get("Dağıtım Yöntemi")

        allocation_rows = _parse_allocation_structured(extra_fields.get("Tahsisat Grupları"))
        allocation_lines = (
            tuple(
                f"{label}: %{format_number_tr(pct, decimals=0)} ({format_number_tr(lot, decimals=0)} Lot)"
                for label, pct, lot in allocation_rows
            )
            if allocation_rows
            else None
        )

        # Tahmini Dağıtım: halkarz.com'un KENDİ (yuvarlak olmayan) senaryo
        # tablosu KULLANILMAZ -- bireysel grubun lot sayısını + fiyatı
        # Decimal'e çevirip AYNI standart senaryo listesiyle (`ipo_assessment.
        # estimate_retail_distribution()`) yeniden hesaplanır (kullanıcı
        # isteği, 2026-08-07 üçüncü tur).
        retail_lot_decimal = next((lot for label, _pct, lot in allocation_rows if "bireysel" in label.lower()), None)
        offering_price_decimal = _to_decimal(offering_price_text)
        estimated_retail_distribution = ipo_assessment.estimate_retail_distribution(retail_lot_decimal, offering_price_decimal)

        capital_lot, partner_lot = _parse_capital_structure(extra_fields.get("Halka Arz Şekli"))
        capital_pct_fallback, partner_pct_fallback, is_pure_fallback = ipo_assessment.estimate_capital_vs_partner_pct(
            capital_lot, partner_lot
        )

        if not any(
            [
                demand_period,
                participation_compliant is not None,
                price_stabilization_note,
                sales_method_note,
                offering_price_text,
                total_lot_text,
                offering_size_text,
                allocation_lines,
                estimated_retail_distribution,
                capital_pct_fallback is not None,
            ]
        ):
            return None

        return SupplementaryIpoInfo(
            demand_period_display=demand_period,
            demand_period_hours=demand_hours,
            participation_index_compliant=participation_compliant,
            participation_index_name=participation_index_name,
            price_stabilization_note=price_stabilization_note,
            sales_method_note=sales_method_note,
            source_url=page_url,
            offering_price_text=offering_price_text,
            total_lot_text=total_lot_text,
            offering_size_text=offering_size_text,
            distribution_method_text=distribution_method_text,
            allocation_lines=allocation_lines,
            estimated_retail_distribution=estimated_retail_distribution,
            capital_increase_pct_fallback=capital_pct_fallback,
            partner_sale_pct_fallback=partner_pct_fallback,
            is_pure_capital_increase_fallback=is_pure_fallback,
        )
    except Exception:  # noqa: BLE001 -- Kural 9: ikincil/tamamlayıcı veri, hata TÜM kartı ÇÖKERTMEMELİ
        logger.warning("halkarz.com'dan '%s' için tamamlayıcı bilgi çekilemedi.", ticker, exc_info=True)
        return None
