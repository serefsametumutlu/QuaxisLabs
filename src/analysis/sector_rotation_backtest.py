"""VRP tabanlı sektör rotasyonu portföy backtest motoru (2026-08-19,
kullanıcı isteği). `abcd_backtest.py`/`abcd_scanner.py` ile AYNI ilke:
bu modül SAF DEĞİL (`Company` DB sorgusu + OHLCV I/O gerektirir), her impur
fonksiyon test edilebilirlik için DI parametresi alır (`session`/
`price_fetcher`).

Mantık (kullanıcının paylaştığı bir quant'ın "VRP Scanner" fikrinden
uyarlandı, bkz. `vrp.py` modül üst notu -- gerçek formülü bilinmiyor, kendi
tanımımız): her ay (1) `ust_sektor` başına trailing getiri medyanı hesaplanır
(n>=5 üye şartı, bkz. `.claude/skills/sektor-siniflandirma`), en yüksek
medyanlı `n_leading_sectors` "lider" seçilir; (2) SADECE o sektörlerin
üyelerinde `vrp.compute_vrp_snapshot` çalıştırılır (TÜM evrende DEĞİL --
performans, bkz. modül üst notu maliyet tahmini), VRP<0 olanlardan en
negatif `basket_size` tanesi eşit ağırlıkla sepete alınır; (3) sepet BİR
SONRAKİ rebalance tarihine kadar tutulur, TAM LİKİDASYON + yeniden alım
(turnover-optimizasyonu YOK, kasıtlı v1 basitliği).

Ağırlıklandırma kararı (kullanıcı, 2026-08-19): sepette `basket_size`'dan AZ
uygun hisse varsa (VRP<0 şartını geçen), KALAN hisselere yeniden ağırlık
verilir (`1/k`, k=uygun hisse sayısı) -- sabit `1/basket_size` slot +nakit
YAKLAŞIMI DEĞİL, her ay TAM yatırımlı kalınır. Aynı ilke, dönem ortasında
veri eksikliği (örn. delisting) nedeniyle ileri fiyatı bulunamayan bir üye
için de uygulanır -- o üye o ayın ortalamasından basitçe DIŞLANIR (fiktif bir
getiri İCAT EDİLMEZ), kalan üyeler üzerinden ortalama alınır.

Komisyon: proje konvansiyonu `abcd_backtest.BacktestParams.commission_pct`
(fill başına %0.1) AYNEN reuse edilir (motorun kendisi DEĞİL, sadece sabit
-- `abcd_backtest.py`nin tek-sembol TP/SL/kısmi-çıkış motoru portföy-seviyesi
aylık rebalance ile kavramsal olarak UYUŞMAZ, bu yüzden REUSE EDİLMEDİ).

DB'ye/dosyaya KAYDEDİLMEZ (`abcd_scanner.ScanResult` ilkesiyle AYNI) --
`run_sector_rotation_backtest`'in dönüş değeri SADECE çağıranın (script
katmanının) elinde yaşar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.analysis import vrp
from src.db.models import Company
from src.db.repository import get_session

_DEFAULT_COMMISSION_PCT = 0.001  # abcd_backtest.BacktestParams ile AYNI (fill basina %0.1)


@dataclass(frozen=True)
class SectorRotationParams:
    n_leading_sectors: int = 2
    sector_momentum_window: int = 21  # is günü, ~1 ay
    min_sector_members: int = 5  # sektor-siniflandirma skill'i ile AYNI esik
    basket_size: int = 5
    lookback_years: float = 3.0
    commission_pct: float = _DEFAULT_COMMISSION_PCT


def get_bist_sector_map(session: Session | None = None) -> dict[str, str]:
    """`abcd_scanner.get_bist_universe` ile AYNI DI deseni -- {ticker:
    ust_sektor}, sadece `ust_sektor` dolu BIST şirketleri (bkz. o modülün
    docstring'i: testler izole SQLite `session` ile ağa/gerçek DB'ye
    dokunmadan çalışır)."""
    query = select(Company.ticker, Company.ust_sektor).where(
        Company.market == "BIST", Company.ust_sektor.is_not(None)
    )
    if session is not None:
        rows = session.execute(query).all()
        return {ticker: sektor for ticker, sektor in rows}

    with get_session() as db_session:
        rows = db_session.execute(query).all()
    return {ticker: sektor for ticker, sektor in rows}


def _as_of_index(df: pd.DataFrame, as_of: pd.Timestamp) -> int | None:
    """`df["time"]` (artan sıralı) içinde `as_of`a kadar (dahil) olan SON
    satırın konumu. `as_of`tan önce hiç veri yoksa None (sembol henüz işlem
    görmüyordu)."""
    if df.empty:
        return None
    idx = int(df["time"].searchsorted(as_of, side="right")) - 1
    return idx if idx >= 0 else None


def _monthly_rebalance_dates(times: pd.Series, lookback_years: float) -> list[pd.Timestamp]:
    """`times` (benchmark'ın işlem günleri) içinde, son `lookback_years`
    yıla ait her ayın İLK işlem gününü döner -- rebalance takvimi."""
    times = pd.to_datetime(times).sort_values().reset_index(drop=True)
    if times.empty:
        return []
    end = times.iloc[-1]
    start = end - pd.Timedelta(days=lookback_years * 365.25)  # DateOffset(years=..) kesirli yil KABUL ETMEZ
    in_range = times[(times >= start) & (times <= end)]
    if in_range.empty:
        return []
    df = pd.DataFrame({"time": in_range})
    df["ym"] = df["time"].dt.tz_localize(None).dt.to_period("M")  # to_period tz-aware'i KABUL ETMEZ (uyari verir)
    firsts = df.groupby("ym")["time"].min().sort_values()
    return list(firsts)


@dataclass(frozen=True)
class SectorMedianRow:
    ust_sektor: str
    n_members: int
    median_return_pct: float
    eligible: bool  # n_members >= min_members


def compute_sector_medians(
    price_history: dict[str, pd.DataFrame],
    sector_map: dict[str, str],
    as_of: pd.Timestamp,
    momentum_window: int,
    min_members: int,
) -> list[SectorMedianRow]:
    """`as_of` tarihinde, `ust_sektor` başına üyelerin trailing
    `momentum_window` iş günü getirisinin MEDYANI. `n_members < min_members`
    olan sektörler `eligible=False` (ELENİR ama gösterilir -- sahte kesinlik
    yasağı, bkz. sektor-siniflandirma skill'i, `abcd_scanner.guven_etiketi`
    ile AYNI "asla gizleme" ilkesi)."""
    returns_by_sector: dict[str, list[float]] = {}
    for symbol, df in price_history.items():
        sektor = sector_map.get(symbol)
        if sektor is None:
            continue
        idx = _as_of_index(df, as_of)
        if idx is None or idx < momentum_window:
            continue
        close_now = float(df["close"].iloc[idx])
        close_then = float(df["close"].iloc[idx - momentum_window])
        if close_then <= 0:
            continue
        ret_pct = (close_now / close_then - 1.0) * 100.0
        returns_by_sector.setdefault(sektor, []).append(ret_pct)

    rows = [
        SectorMedianRow(
            ust_sektor=sektor,
            n_members=len(rets),
            median_return_pct=float(np.median(rets)),
            eligible=len(rets) >= min_members,
        )
        for sektor, rets in returns_by_sector.items()
    ]
    rows.sort(key=lambda r: r.median_return_pct, reverse=True)
    return rows


def select_leading_sectors(sector_medians: list[SectorMedianRow], n_leading: int) -> list[str]:
    """Sadece `eligible=True` sektörler arasından en yüksek medyan getirili
    `n_leading` tanesi -- n>=5 şartını geçmeyen bir sektör, medyanı ne kadar
    yüksek olursa olsun SEÇİLMEZ (bkz. modül üst notu)."""
    eligible = [r for r in sector_medians if r.eligible]
    eligible.sort(key=lambda r: r.median_return_pct, reverse=True)
    return [r.ust_sektor for r in eligible[:n_leading]]


@dataclass(frozen=True)
class BasketMember:
    ticker: str
    ust_sektor: str
    vrp: float


def select_vrp_basket(
    price_history: dict[str, pd.DataFrame],
    sector_map: dict[str, str],
    leading_sectors: list[str],
    as_of: pd.Timestamp,
    basket_size: int,
) -> list[BasketMember]:
    """SADECE `leading_sectors` üyelerinde (performans -- bkz. modül üst
    notu maliyet tahmini) `vrp.compute_vrp_snapshot` çalıştırır, VRP<0
    olanlardan en negatif `basket_size` tanesini döner. `basket_size`'dan
    az aday varsa (hatta hiç yoksa) sepet KISA kalır -- doldurulmaz
    (kullanıcı kararı, bkz. modül üst notu)."""
    leading_set = set(leading_sectors)
    candidates: list[BasketMember] = []
    for symbol, df in price_history.items():
        sektor = sector_map.get(symbol)
        if sektor not in leading_set:
            continue
        idx = _as_of_index(df, as_of)
        if idx is None:
            continue
        closes = df["close"].to_numpy(dtype=float)
        snap = vrp.compute_vrp_snapshot(closes, idx)
        if snap.vrp is None or snap.vrp >= 0:
            continue
        candidates.append(BasketMember(ticker=symbol, ust_sektor=sektor, vrp=snap.vrp))

    candidates.sort(key=lambda m: m.vrp)  # en negatif (en "sikisik") once
    return candidates[:basket_size]


@dataclass(frozen=True)
class MonthlyResult:
    period_start: pd.Timestamp
    period_end: pd.Timestamp
    leading_sectors: list[str]
    basket: list[str]
    n_realized: int  # ileri fiyati bulunup GERCEKTEN getiriye katilan uye sayisi
    basket_return_pct: float
    benchmark_return_pct: float
    portfolio_equity: float
    benchmark_equity: float
    alpha_pct: float


def run_sector_rotation_backtest(
    symbols: list[str],
    sector_map: dict[str, str],
    benchmark_df: pd.DataFrame,
    price_fetcher: Callable[[str], pd.DataFrame],
    params: SectorRotationParams = SectorRotationParams(),
) -> list[MonthlyResult]:
    """`symbols` evreninde aylık rebalance backtesti (bkz. modül üst notu).
    `price_fetcher(symbol) -> DataFrame[time,...,close]` DI parametresi --
    üretimde `fetch_ohlcv_abcd(symbol,"1D",n_bars)`, testte sentetik/sahte
    veri (Kural 11, ağ YOK). `benchmark_df` AYNI şekle sahip olmalı (örn.
    XU100 -- bkz. `scripts/vrp_sektor_rotasyon_arastirma.py` preflight'i).

    Look-ahead güvenliği: her `as_of` tarihinde SADECE `_as_of_index`in
    döndüğü indekse KADAR olan veri kullanılır (`vrp.compute_vrp_snapshot`
    zaten kendi içinde bunu garanti eder, bkz. o modülün docstring'i) --
    `period_end`teki fiyat SADECE getiri hesabı için (karar SONRASI)
    kullanılır, hiçbir seçim kararına sızmaz."""
    price_history: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        df = price_fetcher(symbol)
        if df is not None and not df.empty:
            price_history[symbol] = df.sort_values("time").reset_index(drop=True)

    benchmark_df = benchmark_df.sort_values("time").reset_index(drop=True)
    rebalance_dates = _monthly_rebalance_dates(benchmark_df["time"], params.lookback_years)
    if len(rebalance_dates) < 2:
        return []

    results: list[MonthlyResult] = []
    portfolio_equity = 1.0
    benchmark_equity = 1.0

    for i in range(len(rebalance_dates) - 1):
        rb_date = rebalance_dates[i]
        next_date = rebalance_dates[i + 1]

        medians = compute_sector_medians(
            price_history, sector_map, rb_date, params.sector_momentum_window, params.min_sector_members
        )
        leading = select_leading_sectors(medians, params.n_leading_sectors)
        basket = select_vrp_basket(price_history, sector_map, leading, rb_date, params.basket_size)

        member_net_returns: list[float] = []
        for member in basket:
            df = price_history[member.ticker]
            idx_now = _as_of_index(df, rb_date)
            idx_next = _as_of_index(df, next_date)
            if idx_now is None or idx_next is None or idx_next <= idx_now:
                continue  # ileri fiyat yok (orn. delisting) -- DISLANIR, fiktif getiri ICAT EDILMEZ
            close_now = float(df["close"].iloc[idx_now])
            close_next = float(df["close"].iloc[idx_next])
            if close_now <= 0:
                continue
            gross = close_next / close_now
            net = (1.0 - params.commission_pct) * gross * (1.0 - params.commission_pct) - 1.0
            member_net_returns.append(net)

        basket_return_pct = float(np.mean(member_net_returns) * 100.0) if member_net_returns else 0.0

        bidx_now = _as_of_index(benchmark_df, rb_date)
        bidx_next = _as_of_index(benchmark_df, next_date)
        bench_close_now = float(benchmark_df["close"].iloc[bidx_now])
        bench_close_next = float(benchmark_df["close"].iloc[bidx_next])
        benchmark_return_pct = (bench_close_next / bench_close_now - 1.0) * 100.0

        portfolio_equity *= 1.0 + basket_return_pct / 100.0
        benchmark_equity *= 1.0 + benchmark_return_pct / 100.0

        results.append(
            MonthlyResult(
                period_start=rb_date,
                period_end=next_date,
                leading_sectors=leading,
                basket=[m.ticker for m in basket],
                n_realized=len(member_net_returns),
                basket_return_pct=basket_return_pct,
                benchmark_return_pct=benchmark_return_pct,
                portfolio_equity=portfolio_equity,
                benchmark_equity=benchmark_equity,
                alpha_pct=basket_return_pct - benchmark_return_pct,
            )
        )

    return results
