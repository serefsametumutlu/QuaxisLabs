"""src/analysis/sector_rotation_backtest.py testleri.

`get_bist_sector_map` icin `tests/test_abcd_scanner.py`nin izole-SQLite
fixture'iyla AYNI desen. Geri kalan fonksiyonlar SAF DEGIL ama tamamen DI
uzerinden (price_history/price_fetcher sozlugu, `vrp.compute_vrp_snapshot`
monkeypatch) test edilir -- gercek ag/DB YOK (Kural 11 ile ayni ilke)."""

from __future__ import annotations

from contextlib import contextmanager

import pandas as pd
import pytest

from src.analysis import sector_rotation_backtest as srb
from src.analysis import vrp
from src.db import models
from src.db.models import Company

# --- get_bist_sector_map -----------------------------------------------------


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def test_get_bist_sector_map_sadece_bist_ve_dolu_ust_sektoru_alir(session):
    session.add_all(
        [
            Company(ticker="THYAO", market="BIST", ust_sektor="Sanayi"),
            Company(ticker="ASELS", market="BIST", ust_sektor="Teknoloji"),
            Company(ticker="AAPL", market="NASDAQ", ust_sektor="Teknoloji"),
            Company(ticker="BOSSIZ", market="BIST", ust_sektor=None),
        ]
    )
    session.commit()

    result = srb.get_bist_sector_map(session=session)

    assert result == {"THYAO": "Sanayi", "ASELS": "Teknoloji"}


def test_get_bist_sector_map_session_verilmezse_get_session_kullanir(monkeypatch, tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_default.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    default_session = session_factory()
    default_session.add(Company(ticker="SISE", market="BIST", ust_sektor="Sanayi"))
    default_session.commit()

    @contextmanager
    def fake_get_session():
        yield default_session

    monkeypatch.setattr(srb, "get_session", fake_get_session)

    result = srb.get_bist_sector_map()

    assert result == {"SISE": "Sanayi"}
    default_session.close()


# --- compute_sector_medians / select_leading_sectors -----------------------------------------------------


def _make_df(closes: list[float]) -> pd.DataFrame:
    times = pd.date_range("2026-01-01", periods=len(closes), freq="D", tz="Europe/Istanbul")
    return pd.DataFrame({"time": times, "close": closes})


def _sector_map(members: dict[str, str]) -> dict[str, str]:
    return dict(members)


def test_compute_sector_medians_ve_n5_esigi():
    """'TEK' sektorunde 5 uye (eligible), 'KUCUK'te 3 uye (ineligible) --
    KUCUK'un medyani SAYISAL olarak COK daha yuksek olsa bile eligible=False
    olmali (bkz. sektor-siniflandirma skill'i n>=5 kurali)."""
    price_history = {}
    sector_map = {}
    for name, r in zip("ABCDE", [0.10, 0.20, 0.30, 0.40, 0.50]):
        price_history[name] = _make_df([100.0] * 10 + [100.0 * (1 + r)])
        sector_map[name] = "TEK"
    for name, r in zip("FGH", [0.90, 0.90, 0.90]):
        price_history[name] = _make_df([100.0] * 10 + [100.0 * (1 + r)])
        sector_map[name] = "KUCUK"

    as_of = price_history["A"]["time"].iloc[-1]
    rows = srb.compute_sector_medians(price_history, sector_map, as_of, momentum_window=5, min_members=5)

    by_sector = {r.ust_sektor: r for r in rows}
    assert by_sector["TEK"].n_members == 5
    assert by_sector["TEK"].eligible is True
    assert by_sector["TEK"].median_return_pct == pytest.approx(30.0)
    assert by_sector["KUCUK"].n_members == 3
    assert by_sector["KUCUK"].eligible is False
    assert by_sector["KUCUK"].median_return_pct == pytest.approx(90.0)


def test_select_leading_sectors_ineligible_sayisal_ustunlugune_ragmen_secilmez():
    rows = [
        srb.SectorMedianRow(ust_sektor="TEK", n_members=5, median_return_pct=30.0, eligible=True),
        srb.SectorMedianRow(ust_sektor="KUCUK", n_members=3, median_return_pct=90.0, eligible=False),
        srb.SectorMedianRow(ust_sektor="IKINCI", n_members=6, median_return_pct=20.0, eligible=True),
    ]

    leading = srb.select_leading_sectors(rows, n_leading=2)

    assert leading == ["TEK", "IKINCI"]  # KUCUK, en yuksek medyana ragmen DISLANDI


# --- select_vrp_basket -----------------------------------------------------


def _fake_vrp_by_last_close(vrp_by_close: dict[float, float | None]):
    def _fake(closes, as_of_idx):
        last_close = float(closes[as_of_idx])
        v = vrp_by_close.get(last_close)
        return vrp.VrpSnapshot(as_of_idx=as_of_idx, rv_annualized_pct=30.0, iv_proxy_annualized_pct=25.0, vrp=v, garch=None)

    return _fake


def test_select_vrp_basket_en_negatif_5_secilir_6dan(monkeypatch):
    # close degerleri = benzersiz "isim etiketi" (1..6), vrp'ye eslenir
    vrp_by_close = {1.0: -5.0, 2.0: -4.0, 3.0: -3.0, 4.0: -2.5, 5.0: -1.0, 6.0: -0.5}
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", _fake_vrp_by_last_close(vrp_by_close))

    price_history = {name: _make_df([100.0] * 5 + [close]) for name, close in zip("ABFGCH", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])}
    sector_map = {name: "LIDER" for name in price_history}
    as_of = price_history["A"]["time"].iloc[-1]

    basket = srb.select_vrp_basket(price_history, sector_map, ["LIDER"], as_of, basket_size=5)

    assert [m.ticker for m in basket] == ["A", "B", "F", "G", "C"]  # H (en dusuk buyukluk) DISLANDI
    assert basket[0].vrp == pytest.approx(-5.0)


def test_select_vrp_basket_yetersiz_aday_doldurulmaz(monkeypatch):
    vrp_by_close = {1.0: -5.0, 2.0: -3.0, 3.0: -1.0, 4.0: 0.5, 5.0: None}
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", _fake_vrp_by_last_close(vrp_by_close))

    price_history = {name: _make_df([100.0] * 5 + [close]) for name, close in zip("ABCDE", [1.0, 2.0, 3.0, 4.0, 5.0])}
    sector_map = {name: "LIDER" for name in price_history}
    as_of = price_history["A"]["time"].iloc[-1]

    basket = srb.select_vrp_basket(price_history, sector_map, ["LIDER"], as_of, basket_size=5)

    assert [m.ticker for m in basket] == ["A", "B", "C"]  # sadece VRP<0 olan 3'u -- DOLDURULMADI


def test_select_vrp_basket_lider_olmayan_sektor_elenir(monkeypatch):
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", _fake_vrp_by_last_close({1.0: -5.0}))
    price_history = {"A": _make_df([100.0] * 5 + [1.0])}
    sector_map = {"A": "ZAYIF"}
    as_of = price_history["A"]["time"].iloc[-1]

    basket = srb.select_vrp_basket(price_history, sector_map, ["LIDER"], as_of, basket_size=5)

    assert basket == []


# --- run_sector_rotation_backtest -----------------------------------------------------


def _flat_benchmark(n_months: int = 4) -> pd.DataFrame:
    times = pd.date_range("2026-01-01", periods=n_months * 22, freq="D", tz="Europe/Istanbul")
    return pd.DataFrame({"time": times, "close": [100.0] * len(times)})


def test_run_backtest_komisyon_dogrulugu_sabit_fiyatta(monkeypatch):
    """Fiyat SABIT (getiri=0) oldugunda, sepet getirisi TAM OLARAK
    (1-c)^2-1 formulune esit olmali (alis+satis komisyonu)."""
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", lambda closes, as_of_idx: vrp.VrpSnapshot(as_of_idx, 30.0, 20.0, -10.0, None))

    n = 4 * 22
    times = pd.date_range("2026-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    price_history = {"A": pd.DataFrame({"time": times, "close": [50.0] * n})}
    sector_map = {"A": "TEK"}
    benchmark_df = _flat_benchmark()
    params = srb.SectorRotationParams(
        n_leading_sectors=1, sector_momentum_window=5, min_sector_members=1, basket_size=1,
        lookback_years=0.2, commission_pct=0.001,
    )

    results = srb.run_sector_rotation_backtest(
        ["A"], sector_map, benchmark_df, price_fetcher=lambda s: price_history[s], params=params
    )

    assert len(results) >= 1
    expected = (1 - 0.001) ** 2 - 1
    for r in results:
        assert r.basket_return_pct == pytest.approx(expected * 100.0, abs=1e-9)
        assert r.n_realized == 1


def test_run_backtest_esik_alti_aday_sayisinda_yeniden_agirliklandirma(monkeypatch):
    """basket_size=5 ama sadece 3 uygun aday varsa, getiri SADECE o 3'unun
    ORTALAMASI olmali (kullanici karari: sabit slot+nakit DEGIL)."""
    n = 4 * 22
    times = pd.date_range("2026-01-01", periods=n, freq="D", tz="Europe/Istanbul")

    # A/B/C: VRP<0 (secilir, farkli getiriler); D: VRP>=0 (secilmez).
    # closes[0] (baslangic fiyati) her as_of_idx'te DEGISMEYEN bir kimlik
    # olarak kullanilir -- closes[as_of_idx] zaman icinde surukleniyor.
    def fake_snapshot(closes, as_of_idx):
        first = float(closes[0])
        vrp_map = {10.0: -5.0, 20.0: -3.0, 30.0: -1.0, 40.0: 0.5}
        return vrp.VrpSnapshot(as_of_idx, 30.0, 20.0, vrp_map.get(first), None)

    monkeypatch.setattr(vrp, "compute_vrp_snapshot", fake_snapshot)

    def _grow_df(start_close, monthly_growth):
        closes = [start_close]
        for _ in range(n - 1):
            closes.append(closes[-1] * (1 + monthly_growth / 22))
        return pd.DataFrame({"time": times, "close": closes})

    price_history = {
        "A": _grow_df(10.0, 0.10),
        "B": _grow_df(20.0, 0.20),
        "C": _grow_df(30.0, 0.30),
        "D": _grow_df(40.0, 0.99),
    }
    sector_map = {s: "TEK" for s in price_history}
    benchmark_df = _flat_benchmark()
    params = srb.SectorRotationParams(
        n_leading_sectors=1, sector_momentum_window=5, min_sector_members=1, basket_size=5,
        lookback_years=0.2, commission_pct=0.0,
    )

    results = srb.run_sector_rotation_backtest(
        list(price_history), sector_map, benchmark_df, price_fetcher=lambda s: price_history[s], params=params
    )

    assert len(results) >= 1
    for r in results:
        assert set(r.basket) == {"A", "B", "C"}
        assert r.n_realized == 3
        assert "D" not in r.basket


def test_run_backtest_equity_compounding(monkeypatch):
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", lambda closes, as_of_idx: vrp.VrpSnapshot(as_of_idx, 30.0, 20.0, -10.0, None))

    n = 4 * 22
    times = pd.date_range("2026-01-01", periods=n, freq="D", tz="Europe/Istanbul")
    # Her ay %10 buyuyen bir seri (yaklasik) -- equity carpimsal olmali
    closes = [50.0 * (1.10 ** (i // 22)) for i in range(n)]
    price_history = {"A": pd.DataFrame({"time": times, "close": closes})}
    sector_map = {"A": "TEK"}
    benchmark_df = _flat_benchmark()
    params = srb.SectorRotationParams(
        n_leading_sectors=1, sector_momentum_window=5, min_sector_members=1, basket_size=1,
        lookback_years=0.2, commission_pct=0.0,
    )

    results = srb.run_sector_rotation_backtest(
        ["A"], sector_map, benchmark_df, price_fetcher=lambda s: price_history[s], params=params
    )

    running = 1.0
    for r in results:
        running *= 1.0 + r.basket_return_pct / 100.0
        assert r.portfolio_equity == pytest.approx(running)


def test_run_backtest_look_ahead_guvenligi(monkeypatch):
    """Ayni gecmis + FARKLI/asiri gelecek fiyatlar eklenmis iki backtest
    kosusu, ORTAK aylarda BIREBIR ayni MonthlyResult uretmeli."""
    monkeypatch.setattr(vrp, "compute_vrp_snapshot", lambda closes, as_of_idx: vrp.VrpSnapshot(as_of_idx, 30.0, 20.0, -10.0, None))

    n_common = 4 * 22
    times_common = pd.date_range("2026-01-01", periods=n_common, freq="D", tz="Europe/Istanbul")
    closes_common = [50.0 + 0.01 * i for i in range(n_common)]

    times_extra_calm = pd.date_range(times_common[-1] + pd.Timedelta(days=1), periods=22, freq="D", tz="Europe/Istanbul")
    times_extra_wild = times_extra_calm
    closes_extra_calm = [closes_common[-1] * (1.001**i) for i in range(22)]
    closes_extra_wild = [closes_common[-1] * (3.0**i) for i in range(22)]

    def _bench(times, closes):
        return pd.DataFrame({"time": times, "close": closes})

    bench_calm = _bench(
        list(times_common) + list(times_extra_calm), closes_common + closes_extra_calm
    )
    bench_wild = _bench(
        list(times_common) + list(times_extra_wild), closes_common + closes_extra_wild
    )

    price_history_calm = {"A": pd.DataFrame({"time": list(times_common) + list(times_extra_calm), "close": closes_common + closes_extra_calm})}
    price_history_wild = {"A": pd.DataFrame({"time": list(times_common) + list(times_extra_wild), "close": closes_common + closes_extra_wild})}

    sector_map = {"A": "TEK"}
    params = srb.SectorRotationParams(
        n_leading_sectors=1, sector_momentum_window=5, min_sector_members=1, basket_size=1,
        lookback_years=0.2, commission_pct=0.0,
    )

    results_calm = srb.run_sector_rotation_backtest(
        ["A"], sector_map, bench_calm, price_fetcher=lambda s: price_history_calm[s], params=params
    )
    results_wild = srb.run_sector_rotation_backtest(
        ["A"], sector_map, bench_wild, price_fetcher=lambda s: price_history_wild[s], params=params
    )

    # Ortak (son ay HARIC, cunku son ayin "period_end"i extra veriye bagli
    # olabilir) aylarin sonuclari BIREBIR ayni olmali.
    common_len = min(len(results_calm), len(results_wild)) - 1
    for i in range(common_len):
        assert results_calm[i].period_start == results_wild[i].period_start
        assert results_calm[i].basket_return_pct == pytest.approx(results_wild[i].basket_return_pct)
        assert results_calm[i].basket == results_wild[i].basket
