"""Faz 3c: `src/bot/pipeline.py::compute_multi_lens_score_for_ticker()` --
v2 çok-mercekli (Değer/Kalite/Büyüme/Güvenlik) skorlamanın pipeline
orkestrasyon testleri.

Gerçek ağ isteği ATILMAZ -- `isyatirim.fetch_financials`/`fetch_price_history`,
`kap.search_company`/`fetch_disclosures`/`fetch_sector_map` monkeypatch ile
sahtelenir (tests/test_pipeline.py'nin `izole_db`/`_fake_raw_saglikli`
desenleriyle AYNI ilke).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

import config
from src.bot import pipeline
from src.db import models, repository
from src.fetchers import isyatirim, kap


@pytest.fixture()
def izole_db(monkeypatch, tmp_path):
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_pipeline_multi_lens.db'}")
    models.init_db(engine)
    monkeypatch.setattr(repository, "DefaultSessionLocal", session_factory)
    monkeypatch.setattr(repository, "_default_db_initialized", True)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(isyatirim, "fetch_latest_price", lambda ticker, lookback_days=10: None)
    monkeypatch.setattr(kap, "fetch_sector_map", lambda: {})
    monkeypatch.setattr(kap, "search_company", lambda ticker: kap.CompanyMatch(member_oid="1", name="Test Sanayi A.Ş.", ticker_codes=(ticker.lower(),)))
    monkeypatch.setattr(kap, "fetch_disclosures", lambda ticker, days=90: [])
    return engine


def _donem(revenue, gross, op, dep, net, cash, assets, debt, equity, stl, ltl=None, share_capital=None, ocf=None) -> dict:
    d = {
        "revenue": Decimal(revenue), "gross_profit": Decimal(gross), "operating_profit": Decimal(op),
        "depreciation_amortization": Decimal(dep), "net_income": Decimal(net), "cash": Decimal(cash),
        "total_assets": Decimal(assets), "financial_debt": Decimal(debt), "equity": Decimal(equity),
        "short_term_liabilities": Decimal(stl),
    }
    if ltl is not None:
        d["long_term_liabilities"] = Decimal(ltl)
    if share_capital is not None:
        d["share_capital"] = Decimal(share_capital)
    if ocf is not None:
        d["operating_cash_flow"] = Decimal(ocf)
    return d


def _build_fake_raw(ticker: str, values_by_period: dict[tuple[int, int], dict[str, Decimal]]) -> isyatirim.RawFinancials:
    values_by_item_code: dict[str, dict[tuple[int, int], Decimal]] = {}
    for period, field_values in values_by_period.items():
        for field, value in field_values.items():
            std_field = "short_term_financial_debt" if field == "financial_debt" else field
            item_code = isyatirim.STANDARD_ITEM_MAP_XI_29[std_field]
            values_by_item_code.setdefault(item_code, {})[period] = value

    items = {
        code: isyatirim.FinancialItem(item_code=code, description_tr="", values_by_period=vals)
        for code, vals in values_by_item_code.items()
    }
    periods = sorted(values_by_period.keys(), reverse=True)
    return isyatirim.RawFinancials(ticker=ticker, company_code=ticker, financial_group="XI_29", periods=periods, items=items)


def _fake_raw_zengin(ticker: str = "TESTAS") -> isyatirim.RawFinancials:
    values = {
        (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900, ltl=500, share_capital=100, ocf=200),
        (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850, ltl=480, share_capital=100, ocf=150),
        (2024, 3): _donem(900, 360, 230, 50, 150, 280, 4200, 650, 2400, 820, ltl=460, share_capital=100, ocf=140),
        (2023, 3): _donem(800, 320, 200, 45, 120, 260, 4000, 600, 2200, 800, ltl=440, share_capital=100, ocf=130),
    }
    return _build_fake_raw(ticker, values)


def _make_fake_fetch(fixture: isyatirim.RawFinancials):
    def fake_fetch(ticker, periods=None, financial_group=None):
        target_periods = periods if periods is not None else isyatirim.guess_last_periods(count=8)
        newest = target_periods[0]
        if not any(newest in item.values_by_period for item in fixture.items.values()):
            raise isyatirim.FinancialDataNotAvailableError(f"{ticker}: {newest} yok")
        achieved = [p for p in target_periods if any(p in item.values_by_period for item in fixture.items.values())]
        items = {
            code: isyatirim.FinancialItem(
                item_code=code, description_tr=item.description_tr,
                values_by_period={p: v for p, v in item.values_by_period.items() if p in achieved},
            )
            for code, item in fixture.items.items()
        }
        return isyatirim.RawFinancials(ticker=ticker, company_code=ticker, financial_group=fixture.financial_group, periods=achieved, items=items)
    return fake_fetch


def _fake_price_history(n_days: int = 10):
    def fetcher(ticker, days=400):
        base = date(2026, 3, 1)
        return [
            {"date": base + timedelta(days=i), "open": None, "high": Decimal("10.5"), "low": Decimal("9.5"), "close": Decimal("10") + Decimal(i) * Decimal("0.01"), "volume": Decimal("1000")}
            for i in range(n_days)
        ]
    return fetcher


def test_compute_multi_lens_score_ucdan_uca_dort_mercek_ve_bilesik_uretir(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_zengin("TESTAS")))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history(10))

    sonuc = pipeline.compute_multi_lens_score_for_ticker("testas", market="BIST")

    assert sonuc.ticker == "TESTAS"
    assert sonuc.market == "BIST"
    assert sonuc.price is not None
    assert sonuc.bilesik.mercekler.deger is not None
    assert sonuc.bilesik.mercekler.kalite is not None
    assert sonuc.bilesik.mercekler.buyume is not None
    assert sonuc.bilesik.mercekler.guvenlik is not None
    assert Decimal("0") <= sonuc.bilesik.total_score <= Decimal("10")


def test_compute_multi_lens_score_az_fiyat_gecmisinde_merton_atlanir_diger_bilesenler_calisir(izole_db, monkeypatch) -> None:
    # < 120 gozlem -- merton.annualized_equity_volatility None doner (Kural 3),
    # ama Guvenlik merceginin diger bilesenleri (Kaldirac/Bilanco/Piotroski/TYO) calismaya devam eder.
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_zengin("TESTAS")))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history(10))

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTAS", market="BIST")
    guvenlik = sonuc.bilesik.mercekler.guvenlik
    isimler = {c.name: c for c in guvenlik.components}
    assert isimler["Merton Temerrüt Olasılığı (EDF)"].score is None
    # Fixture SADECE 1. ceyrekleri (Q1) icerdigi icin TTM FAVOK/Piotroski de
    # veri yetersizligiyle None doner (mevcut test_pipeline.py fixture'iyla
    # AYNI bilinen sinir) -- ama Bilanco Kalitesi / Toplam Yukumluluk-Ozkaynak
    # (ikisi de TEK-donemlik veriyle calisir) BAGIMSIZ olarak calismaya devam eder.
    assert isimler["Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)"].score is not None
    assert isimler["Toplam Yükümlülük/Özkaynak (geniş tanım)"].score is not None


def test_compute_multi_lens_score_banka_semasi_desteklenmiyor_hata_firlatir(izole_db, monkeypatch) -> None:
    raw = _fake_raw_zengin("FAKEBANK")
    raw = isyatirim.RawFinancials(ticker="FAKEBANK", company_code="FAKEBANK", financial_group="UFRS", periods=raw.periods, items=raw.items)
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(raw))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history(10))

    with pytest.raises(pipeline.UnsupportedCompanyTypeError):
        pipeline.compute_multi_lens_score_for_ticker("FAKEBANK", market="BIST")


def test_compute_multi_lens_score_ticker_bulunamazsa_hata_firlatir(izole_db, monkeypatch) -> None:
    def patlayan_fetch(ticker, periods=None, financial_group=None):
        raise isyatirim.CompanyNotFoundError(f"{ticker} bulunamadi")

    monkeypatch.setattr(isyatirim, "fetch_financials", patlayan_fetch)

    with pytest.raises(pipeline.TickerNotFoundError):
        pipeline.compute_multi_lens_score_for_ticker("YOKYOK", market="BIST")
