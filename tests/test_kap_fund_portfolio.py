"""src/fetchers/kap_fund_portfolio.py testleri.

Kural 11: hiçbir ağ isteği ATILMAZ -- `kap._post_json` ve
`kap_fund_portfolio._get` monkeypatch ile sahte yanıtlar dönecek şekilde
değiştirilir. PDF ayrıştırma testleri GERÇEK, canlı çekilmiş bir KAP
"Portföy Dağılım Raporu" PDF'i kullanır (tests/fixtures/
kap_portfoy_dagilim_phe_2026_07.pdf, PHE fonu Temmuz 2026 -- 2026-08-05'te
CANLI indirildi) -- ayrıştırma sonucu KAP'ın PDF içindeki KENDİ "GRUP
TOPLAMI" satırıyla (21 hisse, toplam ağırlık %77,05) rakam rakam
doğrulanmıştır (bkz. kap_fund_portfolio.py modül üst notu, Kural 3).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from src.fetchers import kap
from src.fetchers import kap_fund_portfolio as kfp

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
PHE_PDF_BYTES = (FIXTURES_DIR / "kap_portfoy_dagilim_phe_2026_07.pdf").read_bytes()


_PHE_SEARCH_RESULT = {
    "searchValue": "PUSULA PORTFÖY HİSSE SENEDİ FONU (HİSSE SENEDİ YOĞUN FON)",
    "searchType": "F",
    "memberOrFundOid": "4028328c8e21cef8018e2de1258c2053",
    "cmpOrFundCode": "phe",
}


def _search_payload(*rows):
    return [
        {"category": "combined", "results": []},
        {"category": "subjects", "results": []},
        {"category": "companyOrFunds", "results": list(rows)},
    ]


def _escape(text: str) -> str:
    """Gerçek KAP RSC payload'ının kullandığı tek-seviye ters-eğik-çizgi
    escape'ini üretir (bkz. modül üst notu, `_unescape_next_js_string`'in
    tersi)."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _disclosure_list_html(rows: list[dict]) -> str:
    """`bildirim-sorgu-sonuc` sayfasının GERÇEK yanıtındaki gibi (escape'li)
    bir `"data":[{"disclosureBasic":{...}}]` bloğu üretir."""
    entries = []
    for row in rows:
        entries.append(
            '{"disclosureBasic":{"publishDate":"%s","disclosureIndex":%d,"stockCode":null,'
            '"hasMultiLanguageSupport":"N","companyTitle":"%s","title":"%s","relatedStocks":null,'
            '"disclosureClass":"DG","summary":"%s","isChanged":null,"isLate":false,'
            '"year":%d,"period":%d,"donem":"%d. Ay","attachmentCount":1,"fundCode":"%s"}}'
            % (
                row["publish_date"],
                row["disclosure_index"],
                row["company_title"],
                row["title"],
                row["summary"],
                row["year"],
                row["period"],
                row["period"],
                row["fund_code"],
            )
        )
    body = '{"data":[' + ",".join(entries) + "]}"
    return _escape(body)


def _detail_html(obj_id: str, file_name: str) -> str:
    body = '{"attachments":[{"objId":"%s","fileName":"%s"}]}' % (obj_id, file_name)
    return _escape(body)


class _FakeResponse:
    def __init__(self, text: str = "", content: bytes = b"", status_code: int = 200):
        self.text = text
        self.content = content
        self.status_code = status_code


def _install_get(monkeypatch, url_to_response: dict[str, _FakeResponse]):
    def _fake_get(url, params=None):
        key = url
        if params:
            key = url + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        for candidate_key, response in url_to_response.items():
            if url in candidate_key or candidate_key in url or candidate_key == key:
                return response
        raise AssertionError(f"beklenmeyen istek: {url} params={params}")

    monkeypatch.setattr(kfp, "_get", _fake_get)


# --- _search_fund --------------------------------------------


def test_search_fund_bulunur(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload(_PHE_SEARCH_RESULT))

    row = kfp._search_fund("PHE")

    assert row["memberOrFundOid"] == "4028328c8e21cef8018e2de1258c2053"


def test_search_fund_bulunamazsa_hata_firlatir(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload())

    with pytest.raises(kfp.FundNotFoundError):
        kfp._search_fund("YOKTUR123")


# --- _find_latest_portfolio_disclosure --------------------------------------------


def test_find_latest_portfolio_disclosure_en_yeniyi_secer(monkeypatch):
    html = _disclosure_list_html(
        [
            {
                "publish_date": "08.07.2026 18:31:42",
                "disclosure_index": 1629843,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Portföy Dağılım Raporu",
                "summary": "PHE - PORTFÖY DAĞILIM RAPORU HAZİRAN 2026",
                "year": 2026,
                "period": 6,
                "fund_code": "PHE",
            },
            {
                "publish_date": "05.08.2026 12:04:23",
                "disclosure_index": 1643421,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Portföy Dağılım Raporu",
                "summary": "PHE - PORTFÖY DAĞILIM RAPORU TEMMUZ 2026",
                "year": 2026,
                "period": 7,
                "fund_code": "PHE",
            },
            {
                "publish_date": "31.07.2026 17:03:41",
                "disclosure_index": 1641215,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Performans Sunum Raporu",  # farkli tur -- filtrelenmeli
                "summary": "PHE Fon Denetlenmiş Performans Sunum Raporu",
                "year": 2026,
                "period": 6,
                "fund_code": "PHE",
            },
        ]
    )
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=html))

    result = kfp._find_latest_portfolio_disclosure("some-oid")

    assert result["disclosure_index"] == 1643421
    assert result["year"] == 2026
    assert result["period"] == 7
    assert result["publish_date"] == date(2026, 8, 5)


def test_find_latest_portfolio_disclosure_bulunamazsa_none_doner(monkeypatch):
    html = _disclosure_list_html(
        [
            {
                "publish_date": "31.07.2026 17:03:41",
                "disclosure_index": 1641215,
                "company_title": "X",
                "title": "Performans Sunum Raporu",
                "summary": "x",
                "year": 2026,
                "period": 6,
                "fund_code": "PHE",
            }
        ]
    )
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=html))

    assert kfp._find_latest_portfolio_disclosure("some-oid") is None


# --- _fetch_attachment_pdf --------------------------------------------


def test_fetch_attachment_pdf_indirir(monkeypatch):
    detail_html = _detail_html("obj-123", "PHE_2026.07.pdf")

    def _fake_get(url, params=None):
        if "Bildirim" in url:
            return _FakeResponse(text=detail_html)
        if "file/download" in url:
            return _FakeResponse(content=b"%PDF-fake-bytes")
        raise AssertionError(url)

    monkeypatch.setattr(kfp, "_get", _fake_get)

    result = kfp._fetch_attachment_pdf(1643421)

    assert result == b"%PDF-fake-bytes"


def test_fetch_attachment_pdf_ekli_dosya_yoksa_none_doner(monkeypatch):
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=_escape('{"no":"attachments"}')))

    assert kfp._fetch_attachment_pdf(1643421) is None


def test_fetch_attachment_pdf_pdf_disinda_dosyayi_atlar(monkeypatch):
    detail_html = _detail_html("obj-999", "izahname.docx")
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=detail_html))

    assert kfp._fetch_attachment_pdf(1643421) is None


# --- _parse_portfolio_pdf (GERÇEK PDF fixture ile) --------------------------------------------


def test_parse_portfolio_pdf_gercek_rapor_grup_toplamlariyla_esler():
    """CANLI doğrulama (Kural 3): PHE Temmuz 2026 raporunun 'HİSSE
    SENETLERİ' bölümü 21 satır/%77,05, 'DİĞER' (fon-içinde-fon) bölümü
    4 satır/%20,60, 'TÜREV' (VIOP Nakit Teminatı) %0,01 veriyor -- HEPSİ
    PDF'in KENDİ 'GRUP TOPLAMI' satırlarıyla BİREBİR eşleşmeli. Kalan
    fark (%2,34) tek bir 'nakit' sözde-satırı olarak eklenir; NİHAİ
    TOPLAM %100,00'e ulaşmalı (bkz. modül üst notu)."""
    holdings = kfp._parse_portfolio_pdf(PHE_PDF_BYTES)

    hisse = [h for h in holdings if h.instrument_type == "hisse"]
    fon = [h for h in holdings if h.instrument_type == "fon"]
    turev = [h for h in holdings if h.instrument_type == "türev"]
    nakit = [h for h in holdings if h.instrument_type == "nakit"]

    assert len(hisse) == 21
    assert sum(h.weight_pct for h in hisse) == Decimal("77.05")
    assert len(fon) == 4
    assert sum(h.weight_pct for h in fon) == Decimal("20.60")
    assert len(turev) == 1
    assert turev[0].weight_pct == Decimal("0.01")
    assert len(nakit) == 1
    assert nakit[0].weight_pct == Decimal("2.34")

    assert sum(h.weight_pct for h in holdings) == Decimal("100.00")

    by_ticker = {h.ticker: h for h in hisse}
    assert by_ticker["ODINE"].weight_pct == Decimal("14.50")
    assert by_ticker["ODINE"].name == "ODİNE SOLUTİON S TEKNOLOJİ TİCARET VE SANAYİ A.Ş."

    fon_tickers = {h.ticker for h in fon}
    assert fon_tickers == {"PCS", "PDG", "PKZ", "PRY"}


def test_parse_portfolio_pdf_gecersiz_pdf_bos_liste_doner():
    assert kfp._parse_portfolio_pdf(b"gecerli bir PDF degil") == []


def _fake_word(text: str, x0: float, top: float) -> dict:
    return {"text": text, "x0": x0, "top": top}


def _fake_hisse_row(top: float, ticker: str, isin: str, group_pct: str, weight_pct: str) -> list[dict]:
    """Tek bir hisse satırının (ad hariç) minimal kelime listesini üretir --
    `_parse_section_rows`'un beklediği 8 sayısal alan + ISIN + ticker+TL
    başlangıç işaretiyle."""
    return [
        _fake_word(ticker, 20.0, top),
        _fake_word("TL", 100.4, top),
        _fake_word("1.000,00", 368.3, top),
        _fake_word("10,000000", 426.0, top),
        _fake_word("01/07/26", 466.9, top),
        _fake_word("10,000000", 718.9, top),
        _fake_word("10.000,00", 762.5, top),
        _fake_word(group_pct, 836.4, top),
        _fake_word("50,00", 866.4, top),
        _fake_word(weight_pct, 896.4, top),
        _fake_word(isin, 225.3, top + 6),
    ]


def test_parse_section_rows_grup_toplami_tutmuyorsa_bos_liste_doner():
    """Kural 3: sentetik bir satırda GRUP (%) kolonu tek başına %50 --
    grup toplamı %100'e (±tolerans) yakın olmadığı için güvenilmez
    sayılır, yanlış rakam üretmek yerine boş liste döner."""
    words = _fake_hisse_row(100.0, "TESTA", "TRTESTA00011", group_pct="50,00", weight_pct="40,00")

    holdings = kfp._parse_section_rows(words, kfp._STOCK_TICKER_RE, "hisse")

    assert holdings == []


def test_parse_section_rows_grup_toplami_tutuyorsa_holding_doner():
    words = _fake_hisse_row(100.0, "TESTA", "TRTESTA00011", group_pct="100,00", weight_pct="40,00")

    holdings = kfp._parse_section_rows(words, kfp._STOCK_TICKER_RE, "hisse")

    assert len(holdings) == 1
    assert holdings[0].ticker == "TESTA"
    assert holdings[0].weight_pct == Decimal("40.00")


# --- _parse_viop_cash_collateral --------------------------------------------


def test_parse_viop_cash_collateral_veri_satirini_bulur():
    words = [
        _fake_word("VIOP", 20.0, 100.0),
        _fake_word("Nakit", 46.6, 100.0),
        _fake_word("Teminatı", 73.8, 100.0),  # sadece etiket satiri -- sayisal veri YOK
        _fake_word("VIOP", 20.0, 130.0),
        _fake_word("Nakit", 38.6, 130.0),
        _fake_word("Teminatı", 56.5, 130.0),
        _fake_word("4.828.762,67", 372.1, 130.0),
        _fake_word("4.828.762,67", 776.1, 130.0),
        _fake_word("100,00", 828.6, 130.0),
        _fake_word("0,01", 866.4, 130.0),
    ]

    holding = kfp._parse_viop_cash_collateral(words)

    assert holding is not None
    assert holding.instrument_type == "türev"
    assert holding.weight_pct == Decimal("0.01")


def test_parse_viop_cash_collateral_bulunamazsa_none_doner():
    assert kfp._parse_viop_cash_collateral([]) is None


# --- nakit residual --------------------------------------------


def test_parse_portfolio_pdf_hicbir_bolum_ayristirilamazsa_residual_eklenmez(monkeypatch):
    """Kural 3: hiçbir bölüm güvenilir ayrıştırılamadıysa (`all_holdings`
    boş) residual 'nakit' satırı da eklenmez -- aksi halde '%100 nakit'
    gibi YANLIŞ bir izlenim verirdi."""
    monkeypatch.setattr(kfp, "_extract_section_words", lambda pdf, section_start: [])
    monkeypatch.setattr(kfp, "_parse_viop_cash_collateral", lambda words: None)

    assert kfp._parse_portfolio_pdf(PHE_PDF_BYTES) == []


# --- fetch_latest_portfolio (uçtan uca, mock'lu) --------------------------------------------


def test_fetch_latest_portfolio_uctan_uca(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload(_PHE_SEARCH_RESULT))

    disclosure_html = _disclosure_list_html(
        [
            {
                "publish_date": "05.08.2026 12:04:23",
                "disclosure_index": 1643421,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Portföy Dağılım Raporu",
                "summary": "PHE - PORTFÖY DAĞILIM RAPORU TEMMUZ 2026",
                "year": 2026,
                "period": 7,
                "fund_code": "PHE",
            }
        ]
    )
    detail_html = _detail_html("obj-123", "PHE_2026.07.pdf")

    def _fake_get(url, params=None):
        if url == kfp._SEARCH_RESULT_ENDPOINT:
            return _FakeResponse(text=disclosure_html)
        if "Bildirim/1643421" in url:
            return _FakeResponse(text=detail_html)
        if "file/download" in url:
            return _FakeResponse(content=PHE_PDF_BYTES)
        raise AssertionError(f"beklenmeyen istek: {url}")

    monkeypatch.setattr(kfp, "_get", _fake_get)

    result = kfp.fetch_latest_portfolio("PHE")

    assert result is not None
    assert result.fund_code == "PHE"
    assert result.report_date == date(2026, 7, 31)
    assert result.publish_date == date(2026, 8, 5)
    assert result.staleness_days == (date.today() - date(2026, 7, 31)).days
    assert len(result.holdings) == 27  # 21 hisse + 4 fon + 1 türev (VIOP nakit teminatı) + 1 nakit residual
    assert sum(h.weight_pct for h in result.holdings) == Decimal("100.00")


def test_fetch_latest_portfolio_fon_bulunamazsa_none_doner(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload())

    assert kfp.fetch_latest_portfolio("YOKTUR123") is None


def test_fetch_latest_portfolio_bildirim_yoksa_none_doner(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload(_PHE_SEARCH_RESULT))
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=_disclosure_list_html([])))

    assert kfp.fetch_latest_portfolio("PHE") is None


def test_fetch_latest_portfolio_agsal_hatada_cokme_yok_none_doner(monkeypatch):
    def _patlar(url, body):
        raise kap.KapNetworkError("test ağ hatası")

    monkeypatch.setattr(kap, "_post_json", _patlar)

    assert kfp.fetch_latest_portfolio("PHE") is None


# --- resolve_fund_oid / find_portfolio_disclosures / fetch_portfolio_by_disclosure (Faz 18 hazirligi) --------


def test_resolve_fund_oid_bulur(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload(_PHE_SEARCH_RESULT))

    assert kfp.resolve_fund_oid("PHE") == "4028328c8e21cef8018e2de1258c2053"


def test_resolve_fund_oid_bulunamazsa_none_doner(monkeypatch):
    monkeypatch.setattr(kap, "_post_json", lambda url, body: _search_payload())

    assert kfp.resolve_fund_oid("YOKTUR123") is None


def test_find_portfolio_disclosures_tumunu_en_yeniden_eskiye_dondurur(monkeypatch):
    html = _disclosure_list_html(
        [
            {
                "publish_date": "08.07.2026 18:31:42",
                "disclosure_index": 1629843,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Portföy Dağılım Raporu",
                "summary": "PHE - PORTFÖY DAĞILIM RAPORU HAZİRAN 2026",
                "year": 2026,
                "period": 6,
                "fund_code": "PHE",
            },
            {
                "publish_date": "05.08.2026 12:04:23",
                "disclosure_index": 1643421,
                "company_title": "PUSULA PORTFÖY HİSSE SENEDİ FONU",
                "title": "Portföy Dağılım Raporu",
                "summary": "PHE - PORTFÖY DAĞILIM RAPORU TEMMUZ 2026",
                "year": 2026,
                "period": 7,
                "fund_code": "PHE",
            },
        ]
    )
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=html))

    disclosures = kfp.find_portfolio_disclosures("some-oid")

    assert [d["disclosure_index"] for d in disclosures] == [1643421, 1629843]  # en yeni once


def test_find_portfolio_disclosures_bos_liste_doner(monkeypatch):
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=_disclosure_list_html([])))

    assert kfp.find_portfolio_disclosures("some-oid") == []


def test_report_period_end_ay_sonu_dogru_hesaplanir():
    assert kfp.report_period_end(2026, 7) == date(2026, 7, 31)
    assert kfp.report_period_end(2026, 2) == date(2026, 2, 28)
    assert kfp.report_period_end(2026, 12) == date(2026, 12, 31)


def test_fetch_portfolio_by_disclosure_as_of_ile_staleness_gecmise_gore_hesaplanir(monkeypatch):
    detail_html = _detail_html("obj-123", "PHE_2026.07.pdf")

    def _fake_get(url, params=None):
        if "Bildirim/1643421" in url:
            return _FakeResponse(text=detail_html)
        if "file/download" in url:
            return _FakeResponse(content=PHE_PDF_BYTES)
        raise AssertionError(url)

    monkeypatch.setattr(kfp, "_get", _fake_get)

    disclosure = {
        "disclosure_index": 1643421,
        "publish_date": date(2026, 8, 5),
        "summary": "PHE - PORTFÖY DAĞILIM RAPORU TEMMUZ 2026",
        "year": 2026,
        "period": 7,
    }

    result = kfp.fetch_portfolio_by_disclosure("PHE", disclosure, as_of=date(2026, 8, 20))

    assert result.report_date == date(2026, 7, 31)
    assert result.staleness_days == 20  # 2026-08-20 - 2026-07-31
    assert len(result.holdings) == 27


def test_fetch_portfolio_by_disclosure_pdf_indirilemezse_none_doner(monkeypatch):
    monkeypatch.setattr(kfp, "_get", lambda url, params=None: _FakeResponse(text=_escape('{"no":"attachments"}')))

    disclosure = {"disclosure_index": 1643421, "publish_date": date(2026, 8, 5), "summary": "", "year": 2026, "period": 7}

    assert kfp.fetch_portfolio_by_disclosure("PHE", disclosure) is None
