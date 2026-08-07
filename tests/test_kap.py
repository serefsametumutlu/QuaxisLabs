"""kap.py icindeki saf mantik fonksiyonlarinin birim testleri.

Ag erisimi gerektiren fetch_disclosures()/search_company() bu dosyada test
EDILMEZ (bkz. scripts/demo_kap.py -- canli veriyle calisan Faz 2 (KAP)
teslim kriteri scripti). Burada sadece disariya bagimliligi olmayan
siniflandirma/sirlama mantigi dogrulanir.
"""

from __future__ import annotations

from datetime import datetime

from src.fetchers import kap
from src.fetchers.kap import (
    IMPORTANCE_HIGH,
    IMPORTANCE_LOW,
    Disclosure,
    classify_importance,
    get_top_disclosures,
    normalize_ticker,
    search_company_by_name,
    fetch_disclosure_attachment_pdf,
    _parse_publish_date,
    _parse_sector_map,
    _row_to_disclosure,
    _turkish_lower,
)


class _FakeResponse:
    def __init__(self, text: str = "", content: bytes = b"", status_code: int = 200):
        self.text = text
        self.content = content
        self.status_code = status_code


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
    assert disclosure.related_stocks == ""  # bu ornekte yok -- bos string varsayilan


def test_row_to_disclosure_related_stocks_alani_eslenir() -> None:
    """Faz 20: bir ARACI KURUMUN kendi profilinden yayınladığı bir izahname
    bildirimi -- `stock_codes` ARACININ kendi kodu, `related_stocks` ise
    İZAHNAMENİN KONUSU olan (henüz kendi KAP profili olmayabilecek) halka
    arz adayı şirket(ler) -- CANLI doğrulandı (A1CAP/KARCL örneği)."""
    row = {
        "publishDate": "17.07.2026 18:13:58",
        "subject": "İzahname (SPK Tarafından Onaylanan)",
        "summary": "Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname",
        "disclosureIndex": 1634594,
        "isLate": False,
        "stockCodes": "A1CAP, ACP",
        "relatedStocks": "KARCL, VKY, ZRY",
    }
    disclosure = _row_to_disclosure(row)
    assert disclosure.stock_codes == "A1CAP, ACP"
    assert disclosure.related_stocks == "KARCL, VKY, ZRY"


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


# --- _parse_sector_map (Faz 16, Derin Kart -- sektör ortalaması) -----------------------------------------------------


def _fake_sektorler_html(*entries: tuple[str, str]) -> str:
    """(stockCode, sectorName) çiftlerinden kap.org.tr/tr/Sektorler
    sayfasının GERÇEK biçimine (Next.js RSC push, ÇİFT ESCAPED JSON)
    uygun sentetik bir HTML gövdesi üretir -- bkz. _parse_sector_map()."""
    objs = []
    for stock_code, sector_name in entries:
        obj = (
            '{\\"sectorName\\":\\"' + sector_name + '\\",\\"sectorOid\\":\\"OID1\\",'
            '\\"sectorNo\\":\\"001000.\\",\\"mkkMemberOid\\":\\"OID2\\",'
            '\\"stockCode\\":\\"' + stock_code + '\\",\\"title\\":\\"X A.S.\\",'
            '\\"kapTypes\\":[\\"IGS\\"]}'
        )
        objs.append(obj)
    return 'self.__next_f.push([1,"15:[\\"$\\",...' + ",".join(objs) + '..."])'


def test_parse_sector_map_tek_sirket_dogru_ayristirilir() -> None:
    html = _fake_sektorler_html(("THYAO", "ULAŞTIRMA VE DEPOLAMA"))
    assert _parse_sector_map(html) == {"THYAO": "ULAŞTIRMA VE DEPOLAMA"}


def test_parse_sector_map_birden_fazla_sirket() -> None:
    html = _fake_sektorler_html(
        ("THYAO", "ULAŞTIRMA VE DEPOLAMA"),
        ("TUPRS", "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER"),
        ("EREGL", "ANA METAL SANAYİ"),
    )
    result = _parse_sector_map(html)
    assert result["THYAO"] == "ULAŞTIRMA VE DEPOLAMA"
    assert result["TUPRS"] == "KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER"
    assert result["EREGL"] == "ANA METAL SANAYİ"


def test_parse_sector_map_coklu_pay_sinifi_virgullu_kod_ayristirilir() -> None:
    """cmpOrFundCode ile AYNI ilke -- coklu pay sinifli sirketlerde
    stockCode virgulle ayrilmis birden fazla kod icerebilir (orn. TVB, VAKBN)."""
    html = _fake_sektorler_html(("TVB,VAKBN", "BANKALAR"))
    result = _parse_sector_map(html)
    assert result["TVB"] == "BANKALAR"
    assert result["VAKBN"] == "BANKALAR"


def test_parse_sector_map_bos_sayfada_bos_sozluk_doner() -> None:
    assert _parse_sector_map("hicbir sirket verisi yok") == {}


# --- search_company_by_name (Faz 20) -----------------------------------------------------


def _company_search_payload(*rows):
    return [
        {"category": "combined", "results": []},
        {"category": "subjects", "results": []},
        {"category": "companyOrFunds", "results": list(rows)},
    ]


def test_search_company_by_name_sadece_sirket_tipini_doner(monkeypatch) -> None:
    """Faz 20: halka arza aracılık eden kurumları KENDİ ADIYLA (tam ticker
    bilmeden, Kural 3: uydurma yapılmaz) bulmak için -- `search_company()`nin
    aksine TEK bir tam eşleşme ZORUNLU değil, TÜM 'C' (şirket) sonuçları döner."""
    payload = _company_search_payload(
        {"searchValue": "A1 CAPİTAL YATIRIM MENKUL DEĞERLER A.Ş.", "searchType": "C", "memberOrFundOid": "oid-1", "cmpOrFundCode": "a1cap,acp"},
        {"searchValue": "A1 CAPİTAL PORTFÖY YÖNETİMİ A.Ş.", "searchType": "C", "memberOrFundOid": "oid-2", "cmpOrFundCode": "cp1"},
        {"searchValue": "A1 CAPİTAL PORTFÖY DİNAMİK FON SEPETİ FONU", "searchType": "F", "memberOrFundOid": "oid-3", "cmpOrFundCode": "dnf"},
    )
    monkeypatch.setattr(kap, "_post_json", lambda url, body: payload)

    results = search_company_by_name("a1 capital")

    assert len(results) == 2  # sadece 'C' tipi (fon -- 'F' -- HARIC)
    assert results[0].member_oid == "oid-1"
    assert results[0].ticker_codes == ("a1cap", "acp")


def test_search_company_by_name_sonuc_yoksa_bos_liste_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _company_search_payload())
    assert search_company_by_name("olmayan bir kurum") == []


# --- fetch_disclosure_attachment_pdf (Faz 20) ---------------------------------------------


def _escape_kap(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def test_fetch_disclosure_attachment_pdf_indirir(monkeypatch) -> None:
    detail_html = _escape_kap('{"attachments":[{"objId":"obj-123","fileName":"izahname.pdf"}]}')

    def _fake_get(url, params=None):
        if "Bildirim/1634594" in url:
            return _FakeResponse(text=detail_html)
        if "file/download" in url:
            return _FakeResponse(content=b"%PDF-fake-bytes")
        raise AssertionError(f"beklenmeyen istek: {url}")

    monkeypatch.setattr(kap, "_get", _fake_get)

    result = fetch_disclosure_attachment_pdf(1634594)

    assert result == b"%PDF-fake-bytes"


def test_fetch_disclosure_attachment_pdf_ekli_dosya_yoksa_none_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap, "_get", lambda url, params=None: _FakeResponse(text=_escape_kap('{"no":"attachments"}')))
    assert fetch_disclosure_attachment_pdf(1634594) is None


def test_fetch_disclosure_attachment_pdf_pdf_disinda_dosyayi_atlar(monkeypatch) -> None:
    detail_html = _escape_kap('{"attachments":[{"objId":"obj-999","fileName":"ek.docx"}]}')
    monkeypatch.setattr(kap, "_get", lambda url, params=None: _FakeResponse(text=detail_html))
    assert fetch_disclosure_attachment_pdf(1634594) is None


# --- fetch_all_disclosures (Faz 20 devamı, 2026-08-07: 22-üye tarama YERİNE KAP-geneli tek istek) ------


def test_fetch_all_disclosures_mkkmemberoidlist_bos_gonderilir(monkeypatch) -> None:
    """CANLI keşfedildi: `mkkMemberOidList: []` -- yani ÜYE KISITLAMASI
    OLMADAN -- gönderilirse KAP TÜM üyelerin bildirimlerini döner. Bu, üye
    oid'i GEREKTİRMEYEN tek isteklik bir tarama sağlar (Kural: hiçbir
    hardcoded kurum listesi asla eksiksiz olamaz)."""
    captured_body = {}

    def _fake_post_json(url, body):
        captured_body.update(body)
        return [
            {
                "publishDate": "06.08.2026 20:35:56",
                "subject": "İzahname (SPK Tarafından Onaylanan)",
                "summary": "Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname",
                "disclosureIndex": 1700001,
                "isLate": False,
                "stockCodes": "TERA, TRA",
                "relatedStocks": "CITAS",
            }
        ]

    monkeypatch.setattr(kap, "_post_json", _fake_post_json)

    results = kap.fetch_all_disclosures(days=7)

    assert captured_body["mkkMemberOidList"] == []
    assert len(results) == 1
    assert results[0].related_stocks == "CITAS"


def test_fetch_all_disclosures_guvenli_pencereyi_asarsa_valueerror(monkeypatch) -> None:
    """CANLI ölçüldü: yanıt tam 2000 satırda kesiliyor (14/30 günlük
    pencerelerin İKİSİ DE 2000 döndü) -- `days` bu sınırı aşarsa istek
    hiç ATILMAZ, sessizce eksik veri dönmek yerine açık bir hata verilir."""
    import pytest

    with pytest.raises(ValueError, match="güvenli sınırı"):
        kap.fetch_all_disclosures(days=30)


def test_fetch_all_disclosures_2000_satira_ulasirsa_uyari_loglar(monkeypatch, caplog) -> None:
    monkeypatch.setattr(kap, "_post_json", lambda url, body: [{"publishDate": "06.08.2026 20:35:56", "subject": "x", "summary": "x", "disclosureIndex": i, "isLate": False, "stockCodes": "X"} for i in range(2000)])

    with caplog.at_level("WARNING"):
        results = kap.fetch_all_disclosures(days=7)

    assert len(results) == 2000
    assert any("kesme sınırına" in record.message for record in caplog.records)
