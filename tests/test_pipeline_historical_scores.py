"""docs/spec/spec_veri_tamlik_yol_haritasi.md §Skor Geçmişi (2026-08-12):
`src/bot/pipeline.py::compute_historical_lens_scores_for_ticker()` --
GÜNCEL dönem + SON N geçmiş dönemin 4 mercek + Bileşik Skor özetini
üretme orkestrasyonunun testleri.

Gerçek ağ isteği ATILMAZ -- `tests/test_pipeline_multi_lens.py`'nin
fixture desenleriyle (`_donem`/`_build_fake_raw`/`_make_fake_fetch`/
`_fake_price_history`) AYNI ilke, bu dosyada kendi başına (cross-import
YAPILMADAN, proje konvansiyonu -- diğer test dosyaları da birbirinden
İTHAL ETMEZ) yeniden tanımlanır.
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
    engine, session_factory = models.create_engine_and_session(f"sqlite:///{tmp_path / 'test_pipeline_historical_scores.db'}")
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


def _fake_raw_cok_donemli(ticker: str = "TESTHIST") -> isyatirim.RawFinancials:
    """`test_pipeline_multi_lens.py::_fake_raw_zengin` ile AYNI desen
    (SADECE Q1'ler, YoY karşılaştırma için) -- ama TAM 4 dönem (güncel +
    3 geçmiş) taşır ki `compute_historical_lens_scores_for_ticker()`'ın
    "en az 3 geçmiş dönem" davranışı UÇTAN UCA doğrulanabilsin."""
    values = {
        (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900, ltl=500, share_capital=100, ocf=200),
        (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850, ltl=480, share_capital=100, ocf=150),
        (2024, 3): _donem(900, 360, 230, 50, 150, 280, 4200, 650, 2400, 820, ltl=460, share_capital=100, ocf=140),
        (2023, 3): _donem(800, 320, 200, 45, 120, 260, 4000, 600, 2200, 800, ltl=440, share_capital=100, ocf=130),
    }
    return _build_fake_raw(ticker, values)


def _make_fake_fetch(fixture: isyatirim.RawFinancials):
    def fake_fetch(ticker, periods=None, financial_group=None):
        # DIKKAT: `test_pipeline_multi_lens.py`'nin AKSİNE burada gerçek
        # `isyatirim.guess_last_periods(count=8)` KULLANILMAZ -- o fonksiyon
        # BUGÜNÜN tarihine göre ARDIŞIK son 8 çeyreği tahmin eder, ama bu
        # dosyanın fixture'ı (Q1-only, çok-yıllı) ARDIŞIK ÇEYREK DEĞİL --
        # `guess_last_periods` ile eşleşmeyip tesadüfen SADECE 1-2 dönemin
        # "isabet etmesi" (wall-clock'a bağlı, KIRILGAN) yerine fixture'ın
        # KENDİ dönemleri varsayılan olarak kullanılır (deterministik).
        target_periods = periods if periods is not None else sorted(fixture.periods, reverse=True)
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


def _fake_price_history(n_days: int = 500):
    def fetcher(ticker, days=400):
        # `2023,3` doneminin (bitis: 2023-03-31) BILE fiyat penceresine
        # dahil olmasi icin yeterince GERIYE giden bir seri -- gercek
        # own_bars ~400 gunluk pencereyle SINIRLI oldugu icin (bkz.
        # compute_multi_lens_score_for_ticker), bu fixture o sinirin
        # NASIL davrandigini (eski donemlerde fiyat=None -> deger
        # bilesenleri dururstce atlanir) de dolayli olarak sergiler.
        base = date(2025, 1, 1)
        return [
            {"date": base + timedelta(days=i), "open": None, "high": Decimal("10.5"), "low": Decimal("9.5"), "close": Decimal("10") + Decimal(i) * Decimal("0.01"), "volume": Decimal("1000")}
            for i in range(n_days)
        ]
    return fetcher


def test_compute_historical_lens_scores_guncel_donem_tekrar_hesaplanmaz(izole_db, monkeypatch) -> None:
    """Güncel dönem satırı `sonuc.bilesik`'in KENDİSİ olmalı (nesne
    kimliği, TEKRAR hesaplanmadığının kanıtı -- performans notu)."""
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_cok_donemli("TESTHIST")))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTHIST", market="BIST")
    tarihsel = pipeline.compute_historical_lens_scores_for_ticker(sonuc)

    assert tarihsel[0].period == sonuc.period == (2026, 3)
    assert tarihsel[0].bilesik_score == (sonuc.bilesik.total_score if sonuc.bilesik.data_sufficient else None)
    assert tarihsel[0].bilesik_badge == sonuc.bilesik.badge


def test_compute_historical_lens_scores_en_az_3_gecmis_donem_uretir(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_cok_donemli("TESTHIST")))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTHIST", market="BIST")
    tarihsel = pipeline.compute_historical_lens_scores_for_ticker(sonuc)

    # fixture TAM 4 donem tasiyor (guncel + 3 gecmis) -- hepsi uretilmeli.
    assert len(tarihsel) == 4
    donemler = [s.period for s in tarihsel]
    assert donemler == [(2026, 3), (2025, 3), (2024, 3), (2023, 3)]
    for snapshot in tarihsel:
        assert Decimal("0") <= (snapshot.bilesik_score or Decimal("0")) <= Decimal("10")


def test_compute_historical_lens_scores_gecmis_donemde_sadece_o_donemin_verisi_kullanilir(izole_db, monkeypatch) -> None:
    """En eski dönemin (2023,3) skoru, SADECE o döneme kadarki veriyle
    kırpılmış `financials_by_period` ile üretilmiş olmalı -- doğrudan
    `_hesapla_mercek_anlik_goruntu`'yu AYNI kırpılmış girdiyle çağırarak
    (referans hesap) `compute_historical_lens_scores_for_ticker`'ın ÜRETTİĞİ
    skorla BİREBİR eşleştiği doğrulanır (Kural: iki ayrı hesaplama yolu
    AYRIŞMAMALI)."""
    fixture = _fake_raw_cok_donemli("TESTHIST")
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(fixture))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTHIST", market="BIST")
    tarihsel = pipeline.compute_historical_lens_scores_for_ticker(sonuc)
    eski_donem_snapshot = next(s for s in tarihsel if s.period == (2023, 3))

    trimmed = {k: v for k, v in sonuc.financials_by_period.items() if k <= (2023, 3)}
    fiyat = pipeline._price_at_period_end(sonuc.own_bars, (2023, 3))
    _analysis, _valuation, referans_bilesik = pipeline._hesapla_mercek_anlik_goruntu(
        "TESTHIST", trimmed, sonuc.template, sonuc.financial_group, fiyat, sonuc.own_bars,
        sonuc.ust_sektor, sonuc.sirket_turu, apply_sector_relative=False, apply_merton=False,
    )

    beklenen_bilesik_score = referans_bilesik.total_score if referans_bilesik.data_sufficient else None
    assert eski_donem_snapshot.bilesik_score == beklenen_bilesik_score
    assert eski_donem_snapshot.bilesik_badge == referans_bilesik.badge
    assert eski_donem_snapshot.deger_score == referans_bilesik.mercekler.deger.total_score


def test_compute_historical_lens_scores_sektore_goreli_ve_merton_gecmiste_atlanir(izole_db, monkeypatch) -> None:
    """`apply_sector_relative=False`/`apply_merton=False` GERÇEKTEN
    devreye giriyor mu -- doğrudan `_hesapla_mercek_anlik_goruntu`'yu
    kırpılmış (geçmiş) girdiyle çağırıp bileşen düzeyinde doğrulanır."""
    fixture = _fake_raw_cok_donemli("TESTHIST")
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(fixture))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTHIST", market="BIST")
    trimmed = {k: v for k, v in sonuc.financials_by_period.items() if k <= (2025, 3)}
    fiyat = pipeline._price_at_period_end(sonuc.own_bars, (2025, 3))
    _analysis, _valuation, bilesik = pipeline._hesapla_mercek_anlik_goruntu(
        "TESTHIST", trimmed, sonuc.template, sonuc.financial_group, fiyat, sonuc.own_bars,
        sonuc.ust_sektor, sonuc.sirket_turu, apply_sector_relative=False, apply_merton=False,
    )

    deger_bilesen = {c.name: c for c in bilesik.mercekler.deger.components}
    assert "yetersiz örneklem" in deger_bilesen["Sektöre Göreli Konum"].reasoning_tr

    guvenlik_bilesen = {c.name: c for c in bilesik.mercekler.guvenlik.components}
    assert guvenlik_bilesen["Merton Temerrüt Olasılığı (EDF)"].score is None


def test_compute_historical_lens_scores_max_historical_parametresi_siniri_uygular(izole_db, monkeypatch) -> None:
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(_fake_raw_cok_donemli("TESTHIST")))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTHIST", market="BIST")
    tarihsel = pipeline.compute_historical_lens_scores_for_ticker(sonuc, max_historical=1)

    assert len(tarihsel) == 2  # guncel + SADECE 1 gecmis
    assert [s.period for s in tarihsel] == [(2026, 3), (2025, 3)]


def test_compute_historical_lens_scores_veri_yetersizse_daha_az_satir_doner(izole_db, monkeypatch) -> None:
    """Sadece 2 donemlik (guncel + 1 gecmis) bir fixture -- 3 istenmesine
    ragmen sadece 2 satir uretilmeli, hata FIRLATILMAMALI (Kural 3)."""
    values = {
        (2026, 3): _donem(1200, 500, 350, 60, 260, 400, 5000, 600, 3000, 900, ltl=500, share_capital=100, ocf=200),
        (2025, 3): _donem(1000, 400, 260, 55, -80, 300, 4500, 700, 2600, 850, ltl=480, share_capital=100, ocf=150),
    }
    fixture = _build_fake_raw("TESTKISA", values)
    monkeypatch.setattr(isyatirim, "fetch_financials", _make_fake_fetch(fixture))
    monkeypatch.setattr(isyatirim, "fetch_price_history", _fake_price_history())

    sonuc = pipeline.compute_multi_lens_score_for_ticker("TESTKISA", market="BIST")
    tarihsel = pipeline.compute_historical_lens_scores_for_ticker(sonuc)

    assert len(tarihsel) == 2
    assert [s.period for s in tarihsel] == [(2026, 3), (2025, 3)]
