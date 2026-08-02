"""src/fetchers/earnings_calendar.py testleri.

Ağ erişimi gerektiren fonksiyonlar (kap.fetch_disclosures, kap.search_company,
kap_financials.find_latest_financial_report, httpx.get/post) monkeypatch ile
sahtelenir -- hiçbir gerçek ağ isteği ATILMAZ. `_parse_finansal_takvim_html()`
testleri CANLI keşifte kaydedilen gerçek KAP sayfalarını (TAVHL/ASELS, bkz.
scripts/explore_kap_takvim.py) data/exploration/ altından okur.

⚠️ Tarih tahmini yapan HER fonksiyon `date.today()`'yi DOĞRUDAN çağırmaz --
`today`/`period` parametre olarak enjekte edilir (bkz. Faz 12 görev talimatı,
testlerin zamanla kırılmaması için).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.fetchers import earnings_calendar as ec
from src.fetchers import kap, kap_financials

BASE_DIR = Path(__file__).resolve().parent.parent
EXPLORATION_DIR = BASE_DIR / "data" / "exploration"


# --- legal_deadline (Yaklaşım 2: SPK II-14.1 yasal süre) -----------------------------------------------------


def test_legal_deadline_ara_donem_konsolide_kirk_arti_on_gun() -> None:
    # 2026 Ç1 sonu = 31.03.2026. 40 (konsolide) + 10 (sinirli bag. denetim) = 50 gun -> 20.05.2026.
    # 20.05.2026 (Carsamba) resmi tatile/hafta sonuna denk gelmiyor.
    assert ec.legal_deadline((2026, 3), is_consolidated=True) == date(2026, 5, 20)


def test_legal_deadline_ara_donem_konsolide_olmayan_otuz_arti_on_gun() -> None:
    # 30 (konsolide olmayan) + 10 = 40 gun -> 31.03.2026 + 40 = 10.05.2026 (Pazar) -> 11.05.2026'ya kayar.
    assert ec.legal_deadline((2026, 3), is_consolidated=False) == date(2026, 5, 11)


def test_legal_deadline_yillik_konsolide_yetmis_gun() -> None:
    # 2025 Ç4 sonu = 31.12.2025. 70 gun -> 11.03.2026 (Carsamba), tatile denk gelmiyor.
    assert ec.legal_deadline((2025, 12), is_consolidated=True) == date(2026, 3, 11)


def test_legal_deadline_yillik_konsolide_olmayan_altmis_gun() -> None:
    # 31.12.2025 + 60 gun = 01.03.2026 (Pazar) -> 02.03.2026'ya kayar.
    assert ec.legal_deadline((2025, 12), is_consolidated=False) == date(2026, 3, 2)


def test_legal_deadline_resmi_tatile_denk_gelirse_sonraki_is_gunune_kayar() -> None:
    # 2026 Ç2 sonu = 30.06.2026. 40+10=50 gun -> 19.08.2026 (Carsamba, sorun yok) --
    # bunun yerine dogrudan resmi tatil listesindeki bir gunu hedefleyen sentetik bir
    # kontrol: 23.04.2026 (Ulusal Egemenlik Bayrami) + 0 gun senaryosu icin
    # _roll_forward_to_business_day'i DOGRUDAN test et.
    assert ec._roll_forward_to_business_day(date(2026, 4, 23)) == date(2026, 4, 24)  # 23'u Persembe (tatil), 24'u Cuma'ya (is gunu) kayar


def test_roll_forward_hafta_sonuna_denk_gelirse_pazartesiye_kayar() -> None:
    # 2026-08-01 Cumartesi, 2026-08-02 Pazar -> ilk is günü 2026-08-03 Pazartesi.
    assert ec._roll_forward_to_business_day(date(2026, 8, 1)) == date(2026, 8, 3)


def test_roll_forward_is_gunundeyse_degismez() -> None:
    assert ec._roll_forward_to_business_day(date(2026, 8, 4)) == date(2026, 8, 4)


# --- _period_from_end_date -----------------------------------------------------


@pytest.mark.parametrize(
    "period_end,beklenen",
    [
        (date(2026, 3, 31), (2026, 3)),
        (date(2026, 6, 30), (2026, 6)),
        (date(2026, 9, 30), (2026, 9)),
        (date(2026, 12, 31), (2026, 12)),
    ],
)
def test_period_from_end_date_gecerli_ceyrek_sonlari(period_end, beklenen) -> None:
    assert ec._period_from_end_date(period_end) == beklenen


def test_period_from_end_date_ceyrek_sonu_olmayan_tarih_none_doner() -> None:
    assert ec._period_from_end_date(date(2026, 6, 15)) is None


# --- _parse_finansal_takvim_html (CANLI kaydedilmiş KAP sayfaları) -----------------------------------------------------


def _load_html(filename: str) -> str:
    path = EXPLORATION_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} bulunamadı (scripts/explore_kap_takvim.py çalıştırılmamış olabilir).")
    return path.read_text(encoding="utf-8")


def test_parse_finansal_takvim_tavhl_ikinci_ceyrek_dogru_cikarilir() -> None:
    """CANLI DOĞRULANDI: TAVHL disclosure_index=1630730 -- "2026 İkinci Çeyrek
    Finansal Takvimi" bildirimi, planlanan 28/07/2026 tarihi GERÇEK yayın
    tarihiyle (2026-07-28, bkz. historical_publish_lag_days testleri)
    BİREBİR eşleşti."""
    html = _load_html("TAVHL_finansal_takvim_1630730.html")
    results = ec._parse_finansal_takvim_html(html)
    assert (( 2026, 6), date(2026, 7, 28)) in results


def test_parse_finansal_takvim_asels_ikinci_ceyrek_dogru_cikarilir() -> None:
    """CANLI DOĞRULANDI: ASELS disclosure_index=1635301 -- Dönem Başlangıç
    Tarihi TAVHL'den FARKLI (01/04/2026, tek çeyrek -- TAVHL'de 01/01/2026,
    YTD) ama Dönem Bitiş Tarihi (30/06/2026) AYNI ve dönem çıkarımı için
    yeterli."""
    html = _load_html("ASELS_finansal_takvim_1635301.html")
    results = ec._parse_finansal_takvim_html(html)
    assert ((2026, 6), date(2026, 8, 4)) in results


def test_parse_finansal_takvim_bos_html_bos_liste_doner() -> None:
    assert ec._parse_finansal_takvim_html("<html><body>bos</body></html>") == []


# --- _period_from_fiscal_quarter_ending (NASDAQ) -----------------------------------------------------


@pytest.mark.parametrize(
    "text,beklenen",
    [
        ("Jun/2026", (2026, 6)),
        ("Jan/2027", (2027, 3)),
        ("Sep/2025", (2025, 9)),
        ("Dec/2026", (2026, 12)),
    ],
)
def test_period_from_fiscal_quarter_ending_gecerli(text, beklenen) -> None:
    assert ec._period_from_fiscal_quarter_ending(text) == beklenen


@pytest.mark.parametrize("text", ["", "N/A", "Foo/2026", "Jun/abcd", "Jun-2026"])
def test_period_from_fiscal_quarter_ending_gecersiz_none_doner(text) -> None:
    assert ec._period_from_fiscal_quarter_ending(text) is None


# --- historical_publish_lag_days (Yaklaşım 3) -----------------------------------------------------


def test_historical_publish_lag_days_medyan_hesaplanabilir_veri(monkeypatch) -> None:
    monkeypatch.setattr(kap, "search_company", lambda ticker: SimpleNamespace(member_oid="oid-test"))
    fake_rows = [
        {"disclosureCategory": "FR", "year": 2026, "period": 1, "publishDate": "29.04.2026 18:00:00", "disclosureIndex": 1},
        {"disclosureCategory": "FR", "year": 2025, "period": 4, "publishDate": "04.03.2026 18:00:00", "disclosureIndex": 2},
        # FR OLMAYAN bir bildirim -- elenmeli.
        {"disclosureCategory": "ODA", "year": 2026, "period": 1, "publishDate": "01.01.2026 10:00:00", "disclosureIndex": 3},
    ]
    monkeypatch.setattr(kap_financials, "_fetch_disclosures_raw", lambda member_oid, days: fake_rows)

    lags = ec.historical_publish_lag_days("TESTAS")

    # (2026,1) -> ceyrek sonu cikarimi 2026-03-31 (kap_period=1 varsayimsal
    # numaralandirmadan DEGIL, publish_date'ten -- 29.04.2026, min_lag_days=14
    # geriye tarandiginda 2026-03-31'e duser) -> gecikme = 29 gun.
    # (2025,4) -> publish_date 04.03.2026 -> 2025-12-31 ceyrek sonu -> gecikme = 63 gun.
    assert sorted(lags) == [29, 63]


def test_historical_publish_lag_days_sirket_bulunamazsa_bos_liste(monkeypatch) -> None:
    monkeypatch.setattr(
        kap, "search_company", lambda ticker: (_ for _ in ()).throw(kap.KapCompanyNotFoundError("yok"))
    )
    assert ec.historical_publish_lag_days("ZZZZZ") == []


# --- resolve_bist_earnings_date: öncelik sırası (kesin > tahmini > son_tarih) -----------------------------------------------------


def _fake_ref(period):
    return SimpleNamespace(period=period)


def test_resolve_bist_earnings_date_kesin_oncelikli(monkeypatch) -> None:
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker: _fake_ref((2026, 3)))
    monkeypatch.setattr(ec, "fetch_kap_financial_calendar", lambda ticker, days=180: [((2026, 6), date(2026, 8, 4))])
    monkeypatch.setattr(ec, "historical_publish_lag_days", lambda ticker: [10, 20, 30])  # kesin varsa hic bakilmamali

    entry = ec.resolve_bist_earnings_date("TESTAS", "Test A.Ş.")

    assert entry.confidence == ec.CONFIDENCE_KESIN
    assert entry.source == ec.SOURCE_KAP_TAKVIM
    assert entry.period == (2026, 6)
    assert entry.expected_date == date(2026, 8, 4)


def test_resolve_bist_earnings_date_takvim_yoksa_tahmini_medyana_duser(monkeypatch) -> None:
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker: _fake_ref((2026, 3)))
    monkeypatch.setattr(ec, "fetch_kap_financial_calendar", lambda ticker, days=180: [])
    monkeypatch.setattr(ec, "historical_publish_lag_days", lambda ticker: [30, 40])  # medyan 35

    entry = ec.resolve_bist_earnings_date("TESTAS", "Test A.Ş.")

    assert entry.confidence == ec.CONFIDENCE_TAHMINI
    assert entry.source == ec.SOURCE_GECMIS_MEDYAN
    assert entry.period == (2026, 6)
    assert entry.expected_date == date(2026, 6, 30) + __import__("datetime").timedelta(days=35)


def test_resolve_bist_earnings_date_hicbiri_yoksa_son_tarihe_duser(monkeypatch) -> None:
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker: _fake_ref((2025, 12)))
    monkeypatch.setattr(ec, "fetch_kap_financial_calendar", lambda ticker, days=180: [])
    monkeypatch.setattr(ec, "historical_publish_lag_days", lambda ticker: [])

    entry = ec.resolve_bist_earnings_date("TESTAS", "Test A.Ş.")

    assert entry.confidence == ec.CONFIDENCE_SON_TARIH
    assert entry.source == ec.SOURCE_SPK_SURESI
    assert entry.period == (2026, 3)
    assert entry.expected_date == ec.legal_deadline((2026, 3))


def test_resolve_bist_earnings_date_son_donem_bulunamazsa_none_doner(monkeypatch) -> None:
    monkeypatch.setattr(kap_financials, "find_latest_financial_report", lambda ticker: None)
    assert ec.resolve_bist_earnings_date("TESTAS", "Test A.Ş.") is None


# --- fetch_upcoming_bist: tarih aralığı filtresi + hata izolasyonu -----------------------------------------------------


def test_fetch_upcoming_bist_aralik_disindakiler_elenir(monkeypatch) -> None:
    def fake_resolve(ticker, company_name):
        return ec.EarningsDate(
            ticker=ticker, company_name=company_name, market="BIST", period=(2026, 6),
            expected_date=date(2026, 9, 1), confidence=ec.CONFIDENCE_TAHMINI, source=ec.SOURCE_GECMIS_MEDYAN,
        )

    monkeypatch.setattr(ec, "resolve_bist_earnings_date", fake_resolve)

    results = ec.fetch_upcoming_bist([("TESTAS", "Test A.Ş.")], days_ahead=30, today=date(2026, 8, 1))
    assert results == []  # 2026-09-01, 2026-08-01+30=2026-08-31'in disinda


def test_fetch_upcoming_bist_bir_ticker_hata_verirse_digerleri_etkilenmez(monkeypatch) -> None:
    def fake_resolve(ticker, company_name):
        if ticker == "PATLAYAN":
            raise RuntimeError("beklenmeyen hata")
        return ec.EarningsDate(
            ticker=ticker, company_name=company_name, market="BIST", period=(2026, 6),
            expected_date=date(2026, 8, 10), confidence=ec.CONFIDENCE_TAHMINI, source=ec.SOURCE_GECMIS_MEDYAN,
        )

    monkeypatch.setattr(ec, "resolve_bist_earnings_date", fake_resolve)

    results = ec.fetch_upcoming_bist(
        [("PATLAYAN", "Patlayan A.Ş."), ("SAGLAM", "Sağlam A.Ş.")], days_ahead=30, today=date(2026, 8, 1)
    )
    assert len(results) == 1
    assert results[0].ticker == "SAGLAM"


def test_fetch_upcoming_bist_tarihe_gore_siralanir(monkeypatch) -> None:
    def fake_resolve(ticker, company_name):
        gun = {"A": 20, "B": 5, "C": 10}[ticker]
        return ec.EarningsDate(
            ticker=ticker, company_name=company_name, market="BIST", period=(2026, 6),
            expected_date=date(2026, 8, 1) + __import__("datetime").timedelta(days=gun),
            confidence=ec.CONFIDENCE_TAHMINI, source=ec.SOURCE_GECMIS_MEDYAN,
        )

    monkeypatch.setattr(ec, "resolve_bist_earnings_date", fake_resolve)
    results = ec.fetch_upcoming_bist([("A", "A"), ("B", "B"), ("C", "C")], days_ahead=30, today=date(2026, 8, 1))
    assert [e.ticker for e in results] == ["B", "C", "A"]


# --- fetch_upcoming_nasdaq -----------------------------------------------------


def test_fetch_upcoming_nasdaq_gunluk_veriyi_dogru_cikarir(monkeypatch) -> None:
    def fake_request(day):
        if day == date(2026, 8, 3):
            return {"data": {"rows": [
                {"symbol": "AAPL", "name": "Apple Inc.", "fiscalQuarterEnding": "Jun/2026", "time": "time-after-hours"},
                {"symbol": "BADROW", "name": None, "fiscalQuarterEnding": "Jun/2026"},  # eksik alan -- elenmeli
            ]}}
        return {"data": {"rows": None}}

    monkeypatch.setattr(ec, "_request_nasdaq_calendar_day", fake_request)

    results = ec.fetch_upcoming_nasdaq(days_ahead=1, today=date(2026, 8, 3))

    assert len(results) == 1
    entry = results[0]
    assert entry.ticker == "AAPL"
    assert entry.market == "NASDAQ"
    assert entry.period == (2026, 6)
    assert entry.expected_date == date(2026, 8, 3)
    assert entry.confidence == ec.CONFIDENCE_TAHMINI
    assert entry.source == ec.SOURCE_NASDAQ_API


def test_fetch_upcoming_nasdaq_bir_gun_hata_verirse_atlanir(monkeypatch) -> None:
    def fake_request(day):
        if day == date(2026, 8, 3):
            raise ec.httpx.RequestError("ag hatasi", request=None)
        return {"data": {"rows": [
            {"symbol": "MSFT", "name": "Microsoft", "fiscalQuarterEnding": "Sep/2026"},
        ]}}

    monkeypatch.setattr(ec, "_request_nasdaq_calendar_day", fake_request)

    results = ec.fetch_upcoming_nasdaq(days_ahead=1, today=date(2026, 8, 3))
    assert len(results) == 1
    assert results[0].ticker == "MSFT"


# --- get_bist_top_market_cap_tickers -----------------------------------------------------


def test_get_bist_top_market_cap_tickers_dogru_ayristirir(monkeypatch) -> None:
    monkeypatch.setattr(
        ec, "_request_bist_screener",
        lambda limit: {"data": [{"s": "BIST:ASELS", "d": ["ASELS", 100]}, {"s": "BIST:THYAO", "d": ["THYAO", 90]}]},
    )
    assert ec.get_bist_top_market_cap_tickers(limit=2) == ["ASELS", "THYAO"]


def test_get_bist_top_market_cap_tickers_ag_hatasinda_bos_liste(monkeypatch) -> None:
    def raise_error(limit):
        raise ec.httpx.RequestError("ag hatasi", request=None)

    monkeypatch.setattr(ec, "_request_bist_screener", raise_error)
    assert ec.get_bist_top_market_cap_tickers() == []
