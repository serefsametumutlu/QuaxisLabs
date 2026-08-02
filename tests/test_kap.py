"""kap.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren fetch_disclosures()/search_company() bu dosyada test
EDILMEZ (bkz. scripts/demo_kap.py -- canli veriyle calisan Faz 2 (KAP)
teslim kriteri scripti). Burada sadece disariya bagimliligi olmayan
siniflandirma/sirlama mantigi dogrulanir.
"""

from __future__ import annotations

from datetime import datetime

from src.fetchers.kap import (
    IMPORTANCE_HIGH,
    IMPORTANCE_LOW,
    Disclosure,
    classify_importance,
    get_top_disclosures,
    normalize_ticker,
    _parse_publish_date,
    _row_to_disclosure,
    _turkish_lower,
)


def test_turkish_lower_buyuk_i_dogru_cevrilir() -> None:
    # Python'un standart str.lower() 'İ' -> 'i' + COMBINING DOT ABOVE uretir
    # ve "ihale" alt dizesini bozar; _turkish_lower bunu duzeltmeli.
    assert _turkish_lower("İhale Süreci") == "ihale süreci"


def test_turkish_lower_buyuk_harfli_i_dogru_cevrilir() -> None:
    assert _turkish_lower("SATIN ALMA") == "satın alma"


def test_normalize_ticker_strips_suffix_and_lowercases() -> None:
    assert normalize_ticker("TAVHL.IS") == "tavhl"
    assert normalize_ticker("  ThyaO  ") == "thyao"


def test_normalize_ticker_turkce_i_harfi_kap_ile_ayni_kodu_uretir() -> None:
    """CANLI hata (kullanıcı raporu, 2026-08-02 — Faz 13 takvim doğrulaması):
    KAP'in arama API'si "I" harfini TÜRKÇE kurala göre NOKTASIZ "ı"ya çevirip
    dönüyor (örn. BİM'in cmpOrFundCode'u "bımas" olarak geliyor, CANLI
    doğrulandı) -- eski kod düz Python str.lower() kullandığı için "bimas"
    (NOKTALI i) üretiyordu, bu da search_company()'nin eşleşmesini SESSİZCE
    bozuyordu. "I" harfi içeren BİM/İş Bankası/Enka gibi büyük şirketler
    KapCompanyNotFoundError ile pipeline'dan (takvim dahil) tamamen
    DÜŞÜYORDU. Beklenen değerler KAP'in canlı yanıtından (search_company
    ile) birebir alındı."""
    assert normalize_ticker("BIMAS") == "bımas"
    assert normalize_ticker("ISCTR") == "ısctr"
    assert normalize_ticker("ENKAI") == "enkaı"
    assert normalize_ticker("ISBTR") == "ısbtr"
    assert normalize_ticker("SISE") == "sıse"


def test_normalize_ticker_is_suffix_turkce_donusumden_etkilenmez() -> None:
    """'.IS' suffix'i (ASCII borsa eki) Türkçe I->ı dönüşümünden ÖNCE
    kaldırılmalı -- aksi halde '.IS' -> '.ıs' olur ve endswith kontrolü
    KIRILIR (bu regresyonu önlemek için ayrı bir test)."""
    assert normalize_ticker("BIMAS.IS") == "bımas"
    assert normalize_ticker("bimas.is") == "bımas"


def test_classify_importance_ihale_yuksek_onem() -> None:
    assert classify_importance("İhale Süreci / Sonucu", "Terminal 2 İhalesi") == IMPORTANCE_HIGH


def test_classify_importance_yatirimci_bulteni_yanlis_pozitif_degil() -> None:
    # Gercek TAVHL verisiyle bulunan hata: 'yatirim' anahtar kelimesi
    # 'yatirimci' (rutin, aylik bulten) icinde alt dize olarak geciyordu.
    assert classify_importance("Özel Durum Açıklaması (Genel)", "Yatırımcı Bülteni (Haziran 2026)") == IMPORTANCE_LOW


def test_classify_importance_gercek_yatirim_haberi_hala_yuksek() -> None:
    assert classify_importance("Genel Kurul", "Yeni Yatırım Kararı Alındı") == IMPORTANCE_HIGH


def test_classify_importance_rutin_finansal_rapor_dusuk_onem() -> None:
    assert classify_importance("Finansal Rapor", "TAVHL Faaliyet Raporu") == IMPORTANCE_LOW


def test_classify_importance_sozlesme_yuksek_onem() -> None:
    assert classify_importance("Özel Durum Açıklaması (Genel)", "Yeni Sözleşme İmzalandı") == IMPORTANCE_HIGH


def test_parse_publish_date_format() -> None:
    parsed = _parse_publish_date("28.07.2026 19:17:38")
    assert parsed == datetime(2026, 7, 28, 19, 17, 38)


def test_row_to_disclosure_alan_eslemesi() -> None:
    row = {
        "publishDate": "08.06.2026 16:06:21",
        "subject": "İhale Süreci / Sonucu",
        "summary": "Terminal 2 İhalesi",
        "disclosureIndex": 1614665,
        "isLate": False,
        "stockCodes": "TAVHL",
    }
    disclosure = _row_to_disclosure(row)
    assert disclosure.category == "İhale Süreci / Sonucu"
    assert disclosure.title == "Terminal 2 İhalesi"
    assert disclosure.importance == IMPORTANCE_HIGH
    assert disclosure.url == "https://www.kap.org.tr/tr/Bildirim/1614665"
    assert disclosure.stock_codes == "TAVHL"


def _make_disclosure(day: int, importance: str, title: str = "x") -> Disclosure:
    return Disclosure(
        date=datetime(2026, 7, day),
        title=title,
        category="kategori",
        summary=title,
        url="https://example.com",
        importance=importance,
        is_late=False,
        disclosure_index=day,
        stock_codes="TEST",
    )


def test_get_top_disclosures_onem_once_tarih_sonra_siralar() -> None:
    disclosures = [
        _make_disclosure(1, IMPORTANCE_LOW),
        _make_disclosure(10, IMPORTANCE_HIGH),
        _make_disclosure(5, IMPORTANCE_HIGH),
        _make_disclosure(20, IMPORTANCE_LOW),
    ]
    top = get_top_disclosures(disclosures, limit=10)
    assert [d.disclosure_index for d in top] == [10, 5, 20, 1]


def test_get_top_disclosures_limit_uygular() -> None:
    disclosures = [_make_disclosure(d, IMPORTANCE_LOW) for d in range(1, 8)]
    top = get_top_disclosures(disclosures, limit=5)
    assert len(top) == 5
