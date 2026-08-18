"""BIST yeni iş anlaşması bildirimleri (statik Fintables/KAP dökümü,
`bist-yeni-is-anlasmalari-2025-2026.md`) için SAF ayrıştırma -- I/O YOK,
girdi olarak zaten okunmuş markdown metnini alır.

## Neden ayrı, saf bir ayrıştırma modülü

Bu proje boyunca tekrarlanan "sahte kesinlik" disiplini (bkz.
`docs/spec/spec_kapsam_cezali_skor.md` ve benzeri notlar): kaynak metin
serbest biçimlidir (karışık para birimi, "KDV dahil/hariç" tutarsızlığı,
"DB:" reconciled rakam, "milyon/milyar" kelime-çarpanlı yazım, birden
fazla para birimi TOPLANMIŞ satırlar). Bu modül AŞIRI YORUM YAPMAZ --
güvenle ayrıştırılamayan bir tutar `None` döner (asla tahmin edilmez),
çağıran taraf bunu "kapsam" hesabına dahil ETMEZ ama satırı KAYBETMEZ
(ham metin her zaman korunur).

## Ayrıştırma önceliği (`parse_amount`)

1. `DB: ...` (veritabanı/reconciled rakamı) varsa ONA öncelik verilir --
   dosyanın kendi üst notu bunun KAP metnindeki KDV/çoklu-kalem
   karmaşıklığını zaten çözdüğünü söylüyor.
2. `toplam X PARA_BİRİMİ` açıkça yazılmışsa (birden fazla kalemin
   toplamı KAP metninde zaten verilmiş) o kullanılır.
3. Metinde BİRDEN FAZLA FARKLI para birimi "+" ile toplanmışsa (örn.
   "35.004.690,09 TL + 790.600,34 USD") ve yukarıdaki 2 kural onu
   çözmediyse -- AMBİGÜE kabul edilir, `None` döner (hangi kur/toplam
   mantığının doğru olduğu güvenle bilinemez).
4. Aksi halde metindeki İLK "sayı + para birimi" (veya "X milyon/milyar
   PARA_BİRİMİ") eşleşmesi kullanılır.

## Yenileme tespiti (`is_renewal`)

Kullanıcı kararı (2026-08-18): yenileme sözleşmeleri YENİ hasılat
sayılmaz (mevcut gelirin devamıdır) -- `is_renewal()` başlık/açıklama
metninde "yenile" kökünü arar (basit ama bu veri setinde YETERLİ:
tüm yenileme satırları KAP başlığında/İş-Proje sütununda net biçimde
"Sözleşme yenilenmesi" ifadesini taşıyor, bkz. TUREX örnekleri).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

_CUR_ALIASES: dict[str, str] = {
    "TL": "TRY",
    "TRY": "TRY",
    "USD": "USD",
    "EUR": "EUR",
    "AVRO": "EUR",
    "GBP": "GBP",
}
_CUR_PATTERN = "|".join(sorted(_CUR_ALIASES, key=len, reverse=True))
_NUM_RE = r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?)"
_AMOUNT_WORD_RE = re.compile(rf"{_NUM_RE}\s*(milyon|milyar)\s*({_CUR_PATTERN})\b", re.IGNORECASE)
_AMOUNT_PLAIN_RE = re.compile(rf"{_NUM_RE}\s*({_CUR_PATTERN})\b", re.IGNORECASE)
_DB_RE = re.compile(r"DB:\s*([^)]*)")
_TOPLAM_RE = re.compile(rf"toplam\s*~?\s*{_NUM_RE}\s*({_CUR_PATTERN})\b", re.IGNORECASE)
_RENEWAL_RE = re.compile(r"yenile", re.IGNORECASE)

# "X CUR1 + Y CUR2" (CUR1 != CUR2) DOGRUDAN yan yana -- gercek bir COKLU-
# PARA-BIRIMI TOPLAMI isareti (orn. "35.004.690,09 TL + 790.600,34 USD",
# iki AYRI kalemin toplami, hangi kur/oranla birlestirilecegi belirsiz).
# BILINCLI olarak "X CUR1 (Y CUR2)" (parantez ici REFERANS cevrim, ayni
# tutarin iki para biriminde ifadesi -- orn. "212.594.092,00 TL (5.835.687,40
# USD)") ya da "X CUR1 + KDV (Y CUR2 + KDV)" (araya KDV giren, sayi
# OLMAYAN bir token) buna YAKALANMAZ -- bu iki durum ambigue DEGIL, ilk
# (birincil) tutar guvenle kullanilabilir.
_MIXED_SUM_RE = re.compile(
    rf"{_NUM_RE}\s*({_CUR_PATTERN})\s*\+\s*{_NUM_RE}\s*({_CUR_PATTERN})\b", re.IGNORECASE
)


def _has_mixed_currency_sum(text: str) -> bool:
    for m in _MIXED_SUM_RE.finditer(text):
        c1 = _CUR_ALIASES[m.group(2).upper()]
        c2 = _CUR_ALIASES[m.group(4).upper()]
        if c1 != c2:
            return True
    return False


def _to_decimal(num_str: str) -> Decimal | None:
    try:
        return Decimal(num_str.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _find_amount(text: str) -> tuple[Decimal, str] | None:
    m = _AMOUNT_WORD_RE.search(text)
    if m:
        value = _to_decimal(m.group(1))
        if value is None:
            return None
        mult = Decimal("1000000") if m.group(2).lower() == "milyon" else Decimal("1000000000")
        return value * mult, _CUR_ALIASES[m.group(3).upper()]
    m = _AMOUNT_PLAIN_RE.search(text)
    if m:
        value = _to_decimal(m.group(1))
        if value is None:
            return None
        return value, _CUR_ALIASES[m.group(2).upper()]
    return None


def parse_amount(raw: str) -> tuple[Decimal | None, str | None]:
    """Bkz. modül üst notu "Ayrıştırma önceliği". Güvenle ayrıştırılamazsa
    `(None, None)` döner -- ASLA tahmin ETMEZ."""
    db_match = _DB_RE.search(raw)
    if db_match:
        found = _find_amount(db_match.group(1))
        if found:
            return found

    toplam_match = _TOPLAM_RE.search(raw)
    if toplam_match:
        value = _to_decimal(toplam_match.group(1))
        if value is not None:
            return value, _CUR_ALIASES[toplam_match.group(2).upper()]

    if _has_mixed_currency_sum(raw):
        return None, None  # "X CUR1 + Y CUR2" -- gercek belirsiz coklu-kalem toplami

    found = _find_amount(raw)
    if found:
        return found
    return None, None


def is_renewal(description: str) -> bool:
    return bool(_RENEWAL_RE.search(description))


@dataclass(frozen=True)
class DealRow:
    ticker: str
    deal_date: date
    counterparty: str
    description: str
    amount_raw: str
    amount_value: Decimal | None
    amount_currency: str | None
    is_renewal: bool


_TABLE_ROW_RE = re.compile(
    r"^\|\s*([A-Z0-9]+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$"
)


def parse_deals_table(md_text: str) -> list[DealRow]:
    """`bist-yeni-is-anlasmalari-2025-2026.md`deki `| Hisse | Tarih | Karşı
    Taraf | İş/Proje | Tutar |` tablosunu satır satır ayrıştırır. Başlık/
    ayırıcı satırları (`---`) ve eşleşmeyen satırlar SESSİZCE atlanır (tablo
    dışı metin -- başlık, kapsam notu vb.)."""
    rows: list[DealRow] = []
    for line in md_text.splitlines():
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        ticker, date_str, counterparty, description, amount_raw = m.groups()
        if ticker in ("Hisse",) or set(ticker) == {"-"}:
            continue
        try:
            deal_date = date.fromisoformat(date_str)
        except ValueError:
            continue
        value, currency = parse_amount(amount_raw)
        rows.append(
            DealRow(
                ticker=ticker,
                deal_date=deal_date,
                counterparty=counterparty,
                description=description,
                amount_raw=amount_raw,
                amount_value=value,
                amount_currency=currency,
                is_renewal=is_renewal(description),
            )
        )
    return rows
