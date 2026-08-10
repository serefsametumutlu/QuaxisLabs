"""2026/6 (2. çeyrek kümülatif) dönemi için 30 BİST hissesinin toplu temel
analiz veri çıkarımı -- kullanıcı isteği (2026-08-08).

Bu script SADECE Decimal/saf matematik sonucu üretir ve
`scratchpad/batch_report_2026Q2.json`'a yazar -- Kural 1 gereği HİÇBİR
sayı burada ya da sonraki rapor adımında LLM'e ÜRETTİRİLMEZ, LLM sadece bu
JSON'daki hazır sayıları SÖZEL olarak yorumlar.

Kullanılan yöntemler:
  - FAVÖK marjı, Net Borç/FAVÖK, ROE, satış büyümesi: calculator.analyze()/
    analyze_bank()/analyze_insurance() (MEVCUT, Faz 2-16).
  - Graham + Greenblatt Sihirli Formül + Carlisle Acquirer's Multiple +
    Piotroski F-Skoru: fundamental_screens.py (MEVCUT, Faz 21) -- SADECE
    XI_29 (sanayi/ticaret).
  - Damodaran İstikrarlı Büyüme FCFE (basit DCF): valuation.py (MEVCUT,
    Faz 16.6/16.7).
  - Merton DD/EDF: src/analysis/merton.py (YENİ, bu oturumda yazıldı).
  - Kısa/Uzun Dönem/Sektör çarpan üçlemesi ("A" hedef fiyatı):
    src/analysis/multi_scenario_valuation.py (YENİ, bu oturumda yazıldı).

Çalıştırma: `python scripts/batch_report_2026Q2.py` (bilanco-radar/ kök
dizininden).
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis import calculator, fundamental_screens, merton, multi_scenario_valuation, valuation  # noqa: E402
from src.bot import pipeline  # noqa: E402
from src.db import models, repository  # noqa: E402
from src.fetchers import isyatirim, price_history  # noqa: E402

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("batch_report")

XI_29_TICKERS = [
    "BNTAS", "FORTE", "ISDMR", "LOGO", "TABGD", "MPARK", "KCAER", "SAYAS",
    "TTKOM", "TUPRS", "AYGAZ", "ESCOM", "KORDS", "CIMSA", "OYAKC", "NTGAZ",
    "CWENE", "TAVHL", "TERA", "TATGD", "AKMGY", "BRSAN", "FMIZP",
]
BANK_TICKERS = ["ISCTR", "GARAN", "AKBNK", "YKBNK"]
INSURANCE_TICKERS = ["TURSG", "ANSGR", "AGESA"]
ALL_TICKERS = XI_29_TICKERS + BANK_TICKERS + INSURANCE_TICKERS

_RISK_FREE_RATE_PCT = valuation._RISK_FREE_RATE_PCT["TRY"]  # proje genelinde TEK kaynak (Faz 16.7 makro sabiti)
_HISTORY_DAYS = 1600  # ~4.4 yil -- DEFAULT_HISTORY_QUARTERS=16 (finansal veri) ile TUTARLI ust sinir
_REPORT_LAG_DAYS = 45  # ceyrek sonu + tipik KAP acikla,a gecikmesi yaklasimi (Kural 3: belgelenmiş yaklaşım)
_PRICE_MATCH_WINDOW_DAYS = 10


def _period_end_date(period: tuple[int, int]) -> date:
    year, q = period
    return {3: date(year, 3, 31), 6: date(year, 6, 30), 9: date(year, 9, 30), 12: date(year, 12, 31)}[q]


def _nearest_price(bars_by_date: dict[date, Decimal], target: date) -> Decimal | None:
    for offset in range(_PRICE_MATCH_WINDOW_DAYS + 1):
        for candidate in (target + timedelta(days=offset), target - timedelta(days=offset)):
            if candidate in bars_by_date:
                return bars_by_date[candidate]
    return None


def _fetch_price_safe(ticker: str) -> Decimal | None:
    try:
        return isyatirim.fetch_latest_price(ticker)
    except Exception:
        logger.warning("%s fiyat cekilemedi", ticker, exc_info=True)
        return None


def _to_jsonable(obj):
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, tuple):
        return list(obj)
    return obj


def _historical_multiples_for_xi29(
    ticker: str, financials_by_period: dict, bars_by_date: dict[date, Decimal]
) -> dict[str, list[Decimal]]:
    """Bkz. multi_scenario_valuation.py modul ust notu -- şirketin KENDİ
    geçmiş dönemlerindeki TTM temel değerlerini o dönemin (yaklaşık) fiyatıyla
    eşleyerek geçmiş F/K, PD/DD, FD/FAVÖK gözlemleri üretir."""
    periods = sorted(financials_by_period.keys(), reverse=True)
    pe_obs: list[tuple[tuple[int, int], Decimal]] = []
    pb_obs: list[tuple[tuple[int, int], Decimal]] = []
    ev_ebitda_obs: list[tuple[tuple[int, int], Decimal]] = []

    for p in periods:
        ttm_ni = calculator.trailing_12m_from_cumulative(financials_by_period, p, lambda d: d.get("net_income_cum"))
        ttm_ebitda = calculator.trailing_12m_from_cumulative(financials_by_period, p, lambda d: d.get("ebitda_cum"))
        row = financials_by_period.get(p, {})
        equity = row.get("equity")
        share_capital = row.get("share_capital")
        net_debt = calculator.net_debt(row.get("financial_debt"), row.get("cash"), row.get("financial_investments"))

        approx_date = _period_end_date(p) + timedelta(days=_REPORT_LAG_DAYS)
        price_at_p = _nearest_price(bars_by_date, approx_date)
        if price_at_p is None or share_capital is None or share_capital <= 0:
            continue
        market_cap = price_at_p * share_capital

        if ttm_ni is not None and ttm_ni > 0:
            pe_obs.append((p, market_cap / ttm_ni))
        if equity is not None and equity > 0:
            pb_obs.append((p, market_cap / equity))
        if ttm_ebitda is not None and ttm_ebitda > 0 and net_debt is not None:
            ev = market_cap + net_debt
            if ev > 0:
                ev_ebitda_obs.append((p, ev / ttm_ebitda))

    def _split(obs: list[tuple[tuple[int, int], Decimal]]) -> tuple[list[Decimal], list[Decimal]]:
        obs_sorted = sorted(obs, key=lambda x: x[0], reverse=True)
        short = [v for _, v in obs_sorted[:4]]
        long_ = [v for _, v in obs_sorted[:16]]
        return short, long_

    pe_short, pe_long = _split(pe_obs)
    pb_short, pb_long = _split(pb_obs)
    ev_short, ev_long = _split(ev_ebitda_obs)
    return {
        "pe_short": pe_short, "pe_long": pe_long,
        "pb_short": pb_short, "pb_long": pb_long,
        "ev_ebitda_short": ev_short, "ev_ebitda_long": ev_long,
    }


def main() -> None:
    print(f"Toplam {len(ALL_TICKERS)} hisse icin veri tazeleniyor (DB'de yoksa/eskiyse gercek fetch tetiklenir)...")
    for ticker in ALL_TICKERS:
        try:
            pipeline._ensure_financials_cached(ticker, "BIST", periods=None)
        except Exception:
            logger.warning("%s onbellek tazeleme basarisiz", ticker, exc_info=True)

    with repository.get_session() as session:
        companies = {t: session.get(models.Company, t) for t in ALL_TICKERS}

    # --- XI_29 icin sektor havuzu (GUNCEL carpanlar, batch icindeki peer'lerle sinirli -- bkz. modul notu) ---
    xi29_current: dict[str, dict] = {}
    with repository.get_session() as session:
        for ticker in XI_29_TICKERS:
            fin = repository.get_financials(session, ticker, n_periods=20)
            if not fin:
                continue
            analysis = calculator.analyze(ticker, fin)
            price = _fetch_price_safe(ticker)
            share_capital = fin.get(analysis.latest_period, {}).get("share_capital")
            vm = calculator.compute_valuation(analysis, price, share_capital)
            xi29_current[ticker] = {
                "financials_by_period": fin,
                "analysis": analysis,
                "price": price,
                "share_capital": share_capital,
                "valuation_metrics": vm,
                "sector": companies[ticker].sector if companies[ticker] else None,
            }
            print(f"  {ticker}: fiyat={price}, F/K={vm.pe_ratio if vm else None}")

    sector_pools: dict[str, dict[str, list[Decimal]]] = {}
    for ticker, d in xi29_current.items():
        sector = d["sector"]
        if not sector or d["valuation_metrics"] is None:
            continue
        pool = sector_pools.setdefault(sector, {"pe": [], "pb": [], "ev_ebitda": []})
        vm = d["valuation_metrics"]
        if vm.pe_ratio is not None and vm.pe_ratio > 0:
            pool["pe"].append(vm.pe_ratio)
        if vm.pb_ratio is not None and vm.pb_ratio > 0:
            pool["pb"].append(vm.pb_ratio)
        if vm.ev_ebitda is not None and vm.ev_ebitda > 0:
            pool["ev_ebitda"].append(vm.ev_ebitda)

    results: dict[str, dict] = {}

    # --- XI_29 sirketleri: tam analiz ---
    for ticker, d in xi29_current.items():
        print(f"İşleniyor (XI_29): {ticker}")
        analysis = d["analysis"]
        fin = d["financials_by_period"]
        price = d["price"]
        share_capital = d["share_capital"]
        vm = d["valuation_metrics"]
        r = analysis.ratios

        # Faz 21 ekranlari (Graham/Greenblatt/Carlisle/Piotroski) -- MEVCUT modul, KOPYALANMADI
        screens = fundamental_screens.compute_fundamental_screens(
            fin, price=price, share_capital=share_capital,
            own_pe=vm.pe_ratio if vm else None, own_pb=vm.pb_ratio if vm else None,
        )

        # Damodaran DCF (MEVCUT modul, sektor gerektirmez)
        damodaran = valuation.compute_valuation_assessment(
            own_pe=vm.pe_ratio if vm else None, own_pb=vm.pb_ratio if vm else None,
            peer_multiples=[], current_price=price, price_30d_ago=None, price_90d_ago=None,
            growth_rate_pct=r.revenue_growth_yoy_pct, ttm_net_income=r.ttm_net_income,
            roe_pct=r.roe_annualized, share_capital=share_capital, currency="TRY",
        )

        # Merton DD/EDF (YENI)
        bars = price_history.fetch_ohlcv(ticker, "BIST", days=_HISTORY_DAYS)
        closes = [b.close for b in bars]
        bars_by_date = {b.trade_date: b.close for b in bars}
        eq_vol = merton.annualized_equity_volatility(closes)
        latest_row = fin.get(analysis.latest_period, {})
        short_term_liabilities = latest_row.get("short_term_liabilities")
        long_term_debt = latest_row.get("long_term_financial_debt")
        debt_point = None
        if short_term_liabilities is not None:
            debt_point = short_term_liabilities + (long_term_debt or Decimal(0)) / 2
        merton_result = None
        if vm is not None and debt_point is not None and eq_vol is not None:
            merton_result = merton.compute_merton_dd_edf(vm.market_cap, debt_point, eq_vol, _RISK_FREE_RATE_PCT)

        # Coklu senaryo carpan degerlemesi (YENI)
        hist = _historical_multiples_for_xi29(ticker, fin, bars_by_date)
        sector = d["sector"]
        sector_pool = sector_pools.get(sector, {"pe": [], "pb": [], "ev_ebitda": []})
        # kendi carpanini sektor havuzundan cikar (kendi kendine kiyaslamasin)
        own_pe_val = vm.pe_ratio if vm else None
        sector_pe_others = [v for v in sector_pool["pe"] if v != own_pe_val]
        sector_pb_others = [v for v in sector_pool["pb"] if v != (vm.pb_ratio if vm else None)]
        sector_ev_others = [v for v in sector_pool["ev_ebitda"] if v != (vm.ev_ebitda if vm else None)]

        multi_scenario = multi_scenario_valuation.compute_multi_scenario_valuation(
            sector_pe=sector_pe_others, sector_pb=sector_pb_others, sector_ev_ebitda=sector_ev_others,
            short_term_pe=hist["pe_short"], short_term_pb=hist["pb_short"], short_term_ev_ebitda=hist["ev_ebitda_short"],
            long_term_pe=hist["pe_long"], long_term_pb=hist["pb_long"], long_term_ev_ebitda=hist["ev_ebitda_long"],
            ttm_net_income=r.ttm_net_income, current_equity=analysis.balance_sheet.equity.current,
            ttm_ebitda=r.ttm_ebitda, share_capital=share_capital, net_debt=r.net_debt,
        )

        final_target_price = None
        a = multi_scenario.final_target_price_a
        dcf = damodaran.damodaran_fair_value_price if damodaran else None
        if a is not None and dcf is not None:
            final_target_price = a * Decimal("0.6") + dcf * Decimal("0.4")
        elif a is not None:
            final_target_price = a

        results[ticker] = {
            "financial_group": "XI_29",
            "company_name": companies[ticker].name if companies[ticker] else ticker,
            "sector": sector,
            "price": price,
            "latest_period": analysis.latest_period,
            "revenue_growth_yoy_pct": r.revenue_growth_yoy_pct,
            "ebitda_margin_current": r.ebitda_margin_current,
            "ebitda_margin_prior_year": r.ebitda_margin_prior_year,
            "net_margin_current": r.net_margin_current,
            "net_debt_to_ebitda": r.net_debt_to_ebitda,
            "roe_annualized": r.roe_annualized,
            "current_ratio": r.current_ratio,
            "net_debt": r.net_debt,
            "valuation_metrics": vm,
            "fundamental_screens": screens,
            "damodaran": damodaran,
            "merton": merton_result,
            "equity_volatility_pct": eq_vol,
            "debt_point_used": debt_point,
            "multi_scenario": multi_scenario,
            "final_target_price": final_target_price,
        }

    # --- Bankalar ---
    for ticker in BANK_TICKERS:
        print(f"İşleniyor (Banka): {ticker}")
        with repository.get_session() as session:
            fin = repository.get_financials(session, ticker, n_periods=20)
        if not fin:
            results[ticker] = {"financial_group": "UFRS", "error": "veri yok"}
            continue
        variant = "participation" if companies[ticker] and companies[ticker].financial_group == "UFRS_KATILIM" else "conventional"
        analysis = calculator.analyze_bank(ticker, fin, bank_variant=variant)
        price = _fetch_price_safe(ticker)
        share_capital = fin.get(analysis.latest_period, {}).get("share_capital")
        vm = calculator.compute_valuation_bank(analysis, price, share_capital)
        r = analysis.ratios
        damodaran = valuation.compute_valuation_assessment(
            own_pe=vm.pe_ratio if vm else None, own_pb=vm.pb_ratio if vm else None,
            peer_multiples=[], current_price=price, price_30d_ago=None, price_90d_ago=None,
            growth_rate_pct=None, ttm_net_income=r.ttm_net_income, roe_pct=r.roe_annualized,
            share_capital=share_capital, currency="TRY",
        )
        results[ticker] = {
            "financial_group": companies[ticker].financial_group if companies[ticker] else "UFRS",
            "company_name": companies[ticker].name if companies[ticker] else ticker,
            "sector": companies[ticker].sector if companies[ticker] else None,
            "price": price,
            "latest_period": analysis.latest_period,
            "net_interest_margin_current": r.net_interest_margin_current,
            "net_interest_margin_prior_year": r.net_interest_margin_prior_year,
            "return_on_assets_annualized": r.return_on_assets_annualized,
            "roe_annualized": r.roe_annualized,
            "equity_to_assets_current": r.equity_to_assets_current,
            "valuation_metrics": vm,
            "damodaran": damodaran,
            "note": "FAVOK/Merton/Piotroski/Greenblatt bankalara UYGULANMAZ (farkli sermaye yapisi, bkz. rapor notu)",
        }

    # --- Sigorta ---
    for ticker in INSURANCE_TICKERS:
        print(f"İşleniyor (Sigorta): {ticker}")
        with repository.get_session() as session:
            fin = repository.get_financials(session, ticker, n_periods=20)
        if not fin:
            results[ticker] = {"financial_group": "UFRS_K", "error": "veri yok"}
            continue
        analysis = calculator.analyze_insurance(ticker, fin)
        price = _fetch_price_safe(ticker)
        share_capital = fin.get(analysis.latest_period, {}).get("share_capital")
        vm = calculator.compute_valuation_insurance(analysis, price, share_capital)
        r = analysis.ratios
        damodaran = valuation.compute_valuation_assessment(
            own_pe=vm.pe_ratio if vm else None, own_pb=vm.pb_ratio if vm else None,
            peer_multiples=[], current_price=price, price_30d_ago=None, price_90d_ago=None,
            growth_rate_pct=None, ttm_net_income=getattr(r, "ttm_net_income", None), roe_pct=getattr(r, "roe_annualized", None),
            share_capital=share_capital, currency="TRY",
        )
        results[ticker] = {
            "financial_group": "UFRS_K",
            "company_name": companies[ticker].name if companies[ticker] else ticker,
            "sector": companies[ticker].sector if companies[ticker] else None,
            "price": price,
            "latest_period": analysis.latest_period,
            "ratios": r,
            "valuation_metrics": vm,
            "damodaran": damodaran,
            "note": "FAVOK/Merton/Piotroski/Greenblatt sigortaya UYGULANMAZ (farkli sermaye yapisi, bkz. rapor notu)",
        }

    out_path = Path(__file__).resolve().parent.parent / "scratchpad_batch_report_2026Q2.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(_to_jsonable(results), f, ensure_ascii=False, indent=2, default=str)
    print(f"\nYazildi: {out_path}")


if __name__ == "__main__":
    main()
