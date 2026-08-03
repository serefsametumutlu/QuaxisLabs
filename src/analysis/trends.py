"""Çok dönemli (8-12 çeyrek) trend serileri -- "Derin Kart" için SAF matematik.

Bu modül, `src/analysis/calculator.py`'nin TEK bir "güncel dönem" için ürettiği
`AnalysisResult`'un aksine, ELDE MEVCUT (repository.get_financials() zaten
DB'de ne kadar dönem varsa) TÜM dönemler için AYNI oran/marj/kaldıraç/ROE
hesaplamalarını tekrarlar -- "bu çeyrek ne oldu" değil "bu şirket ZAMAN
İÇİNDE nasıl bir seyir izliyor" sorusunu cevaplamak için (bkz.
YENI_FAZ_PROMPTLARI.md "Derin Kart" görev tanımı).

Hesaplama mantığını İKİNCİ kez YAZMAK yerine (bir TERA/BORSK tarzı hatanın
sessizce tekrarlanması riski) `calculator.py`'nin zaten doğrulanmış PUBLIC
sarmalayıcılarını (`ebitda`, `ebitda_cum`, `margin_pct`, `net_debt`,
`trailing_12m_from_cumulative`) kullanır -- bu modül SIFIR yeni finansal
formül İCAT ETMEZ, sadece bunları bir dönem DÖNGÜSÜNE uygular.

Bu modül HİÇBİR I/O yapmaz, `src.fetchers`/`src.db` HİÇBİR modülü import
ETMEZ (01_MIMARI.md katman kuralı -- calculator.py/technical.py ile AYNI
ilke). Girdi olarak zaten DB'den okunmuş `calculator.FinancialsByPeriod`
alır. Yalnızca XI_29/US_GAAP alan adlarıyla (revenue/gross_profit/
operating_profit_ebitda_base/depreciation_amortization/net_income/equity/
financial_debt/cash/financial_investments + "_cum" YTD karşılıkları)
çalışır -- banka/sigorta (UFRS/UFRS_K) şemaları FARKLI alan adları
kullandığı için bu modülün kapsamı DIŞINDADIR (bkz. deep_card.py modül
notu, sadece sanayi/US_GAAP şirketlerinde "🔬 Detaylı Analiz" butonu
gösterilir).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import calculator
from src.analysis.calculator import FinancialsByPeriod, Period

# "Derin Kart"ın gösterdiği pencere -- görev talimatı "8-12 çeyrek" diyor;
# repository.get_financials() zaten en fazla ne kadar dönem varsa onu
# döner (YENİ bir ağ isteği GEREKMEZ, bkz. modül üst notu), bu sabit SADECE
# üst sınırı ifade eder.
MAX_TREND_PERIODS = 12

# Mevsimsellik karşılaştırması icin ayni ceyrek numarasinda EN AZ kac farkli
# yil GEREKIR (K4: tek bir veri noktasi "karsilastirma" SAYILMAZ).
_MIN_SEASONALITY_YEARS = 2


@dataclass(frozen=True)
class PeriodTrendPoint:
    """Tek bir çeyreğin ÇOK DÖNEMLİ resme katkısı -- bir alan hesaplanamıyorsa
    (yetersiz trailing veri vb.) None kalır, TÜM nokta atılmaz (K4)."""

    period: Period
    revenue: Decimal | None
    ebitda: Decimal | None
    net_income: Decimal | None
    equity: Decimal | None
    gross_margin_pct: Decimal | None
    ebitda_margin_pct: Decimal | None
    net_margin_pct: Decimal | None
    current_ratio: Decimal | None  # Cari Oran (Dönen Varlıklar / Kısa Vadeli Yükümlülükler)
    net_debt_to_ebitda: Decimal | None  # TTM FAVÖK bazlı (o dönem "o ana kadarki" TTM)
    roe_pct: Decimal | None  # TTM net kâr bazlı (o dönem "o ana kadarki" TTM)


# compute_sector_average()'ın PeriodTrendPoint'ten SADECE ölçek-bağımsız
# (oran/yüzde) alanları ortalayabileceği alanlar -- revenue/ebitda/net_income/
# equity gibi MUTLAK (para birimi) alanlar KASITLI OLARAK burada YOK: farklı
# büyüklükteki şirketlerin mutlak değerlerini ortalamak anlamsız/yanıltıcı
# olurdu (bkz. compute_sector_average() docstring'i).
_SECTOR_AVERAGE_FIELDS: tuple[str, ...] = (
    "gross_margin_pct",
    "ebitda_margin_pct",
    "net_margin_pct",
    "current_ratio",
    "net_debt_to_ebitda",
    "roe_pct",
)


@dataclass(frozen=True)
class SeasonalityGroup:
    """Aynı çeyrek numarasının (örn. hep "2. çeyrek") yıllar arası serisi --
    mevsimsel şirketlerde (perakende/turizm) çeyrekler arası karşılaştırma
    YANILTICI olabilir, bu yüzden AYNI çeyrek yıldan yıla karşılaştırılır."""

    quarter_number: int  # 3, 6, 9 veya 12
    years: tuple[int, ...]  # artan yıl sırası
    revenues: tuple[Decimal | None, ...]  # years ile AYNI sırada


@dataclass(frozen=True)
class MultiPeriodTrend:
    points: tuple[PeriodTrendPoint, ...]  # artan (eskiden yeniye) dönem sırası
    seasonality: tuple[SeasonalityGroup, ...]  # en az 2 yıllık veri olan gruplar


def _period_point(financials_by_period: FinancialsByPeriod, period: Period) -> PeriodTrendPoint:
    data = financials_by_period.get(period, {})
    revenue = data.get("revenue")
    ebitda_value = calculator.ebitda(data)
    net_income = data.get("net_income")
    equity = data.get("equity")

    gross_margin_pct = calculator.margin_pct(data.get("gross_profit"), revenue)
    ebitda_margin_pct = calculator.margin_pct(ebitda_value, revenue)
    net_margin_pct = calculator.margin_pct(net_income, revenue)

    ttm_ebitda = calculator.trailing_12m_from_cumulative(financials_by_period, period, calculator.ebitda_cum)
    period_net_debt = calculator.net_debt(
        data.get("financial_debt"), data.get("cash"), data.get("financial_investments")
    )
    net_debt_to_ebitda = calculator.safe_div(period_net_debt, ttm_ebitda)

    ttm_net_income = calculator.trailing_12m_from_cumulative(
        financials_by_period, period, lambda d: d.get("net_income_cum")
    )
    roe_pct = calculator.margin_pct(ttm_net_income, equity)

    current_ratio = calculator.safe_div(data.get("current_assets"), data.get("short_term_liabilities"))

    return PeriodTrendPoint(
        period=period,
        revenue=revenue,
        ebitda=ebitda_value,
        net_income=net_income,
        equity=equity,
        gross_margin_pct=gross_margin_pct,
        ebitda_margin_pct=ebitda_margin_pct,
        net_margin_pct=net_margin_pct,
        current_ratio=current_ratio,
        net_debt_to_ebitda=net_debt_to_ebitda,
        roe_pct=roe_pct,
    )


def _build_seasonality(financials_by_period: FinancialsByPeriod) -> tuple[SeasonalityGroup, ...]:
    """Her çeyrek numarası (3/6/9/12) için, o numaraya sahip TÜM dönemleri
    yıl sırasına göre toplar. En az `_MIN_SEASONALITY_YEARS` farklı yılı
    OLMAYAN gruplar (tek bir veri noktası karşılaştırma sayılmaz, K4)
    sonuca DAHİL EDİLMEZ."""
    by_quarter: dict[int, list[tuple[int, Decimal | None]]] = {}
    for (year, quarter), data in financials_by_period.items():
        by_quarter.setdefault(quarter, []).append((year, data.get("revenue")))

    groups = []
    for quarter_number in sorted(by_quarter):
        entries = sorted(by_quarter[quarter_number])
        # En az iki YIL degil, en az iki GERCEK (None olmayan) hasilat
        # degeri gerekir -- aksi halde "karsilastirma" tek bir gercek
        # noktaya (digeri None) dayanan sahte-dolu bir cizgi olurdu (K4).
        non_none_count = sum(1 for _, revenue in entries if revenue is not None)
        if non_none_count < _MIN_SEASONALITY_YEARS:
            continue
        years = tuple(year for year, _ in entries)
        revenues = tuple(revenue for _, revenue in entries)
        groups.append(SeasonalityGroup(quarter_number=quarter_number, years=years, revenues=revenues))
    return tuple(groups)


def compute_multi_period_trend(financials_by_period: FinancialsByPeriod) -> MultiPeriodTrend | None:
    """`financials_by_period` içindeki (repository.get_financials() zaten
    DB'de ne kadar dönem varsa, en fazla ~8) TÜM dönemler için trend
    noktalarını hesaplar. Dönem sayısı 0 ise None döner (K4)."""
    if not financials_by_period:
        return None

    periods_asc = sorted(financials_by_period.keys())[-MAX_TREND_PERIODS:]
    points = tuple(_period_point(financials_by_period, period) for period in periods_asc)
    seasonality = _build_seasonality(financials_by_period)

    return MultiPeriodTrend(points=points, seasonality=seasonality)


@dataclass(frozen=True)
class SectorAveragePoint:
    """Bir dönem için AYNI sektördeki DİĞER şirketlerin (kendisi hariç,
    bkz. repository.get_sector_peer_tickers()) basit ortalaması -- SADECE
    ölçek-bağımsız (oran/yüzde) alanlar (bkz. _SECTOR_AVERAGE_FIELDS).
    `peer_count`: bu dönem için ortalamaya KATKI VEREN (None olmayan
    değere sahip) peer sayısı -- 1 peer'lik bir "ortalama" tek şirketin
    kendisidir, karta/legend'e bu sayı YANSITILIR (yanıltıcı olmasın)."""

    period: Period
    peer_count: int
    gross_margin_pct: Decimal | None
    ebitda_margin_pct: Decimal | None
    net_margin_pct: Decimal | None
    current_ratio: Decimal | None
    net_debt_to_ebitda: Decimal | None
    roe_pct: Decimal | None


def compute_sector_average(peer_financials_list: list[FinancialsByPeriod]) -> dict[Period, SectorAveragePoint]:
    """Derin Kart'ın "Karşılaştırma Ortalaması" (sektör ortalaması) çizgisi
    için: her peer şirketin `compute_multi_period_trend()` sonucunu
    hesaplar, sonra AYNI dönem (year, quarter) için peer'ler arasında basit
    ortalama alır.

    ⚠️ SADECE oran/yüzde alanları ortalanır (marj/cari oran/kaldıraç/ROE)
    -- Hasılat/FAVÖK/Net Kâr/Özkaynak gibi MUTLAK (para birimi) alanlar
    KASITLI OLARAK burada YOK: THY gibi milyar $'lık bir şirketle küçük bir
    peer'in mutlak hasılatını ortalamak (biri diğerini görsel olarak
    "ezer") anlamlı bir karşılaştırma ÜRETMEZ -- oysa marj/oran gibi
    ölçek-bağımsız metrikler için sektör ortalaması GERÇEKTEN anlamlıdır.

    Her (dönem, alan) çifti İÇİN o alanda GERÇEK (None olmayan) değeri olan
    peer'ler arasında ortalama alınır -- bir peer'in tek bir alanda eksik
    verisi olması (örn. kaldıraç TTM yetersizliği yüzünden None) diğer
    alanların ortalamasını ETKİLEMEZ (K4 ile AYNI ilke).

    `peer_financials_list` boşsa (hiç peer yoksa, örn. sektör bilgisi henüz
    `refresh_sector_cache.py` ile doldurulmamışsa) boş sözlük döner."""
    points_by_period: dict[Period, list[PeriodTrendPoint]] = {}
    for peer_financials in peer_financials_list:
        peer_trend = compute_multi_period_trend(peer_financials)
        if peer_trend is None:
            continue
        for point in peer_trend.points:
            points_by_period.setdefault(point.period, []).append(point)

    def _average(points: list[PeriodTrendPoint], field: str) -> Decimal | None:
        values = [getattr(p, field) for p in points if getattr(p, field) is not None]
        return (sum(values) / len(values)) if values else None

    result: dict[Period, SectorAveragePoint] = {}
    for period, points in points_by_period.items():
        result[period] = SectorAveragePoint(
            period=period,
            peer_count=len(points),
            **{field: _average(points, field) for field in _SECTOR_AVERAGE_FIELDS},
        )
    return result
