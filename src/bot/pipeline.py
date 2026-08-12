"""Uctan uca boru hattini orkestre eder: onbellek kontrolu -> gerekiyorsa
Is Yatirim/KAP'tan veri cekme -> DB'ye yazma -> calculator -> scorer ->
commentary (Gemini) -> card (Playwright PNG).

Bu modul HICBIR Telegram bagimliligi icermez -- hem src/bot/telegram_bot.py
hem de scripts/demo_pipeline.py buradaki SENKRON run_pipeline() fonksiyonunu
kullanir. (telegram_bot.py bunu asyncio.to_thread() ile sarar ki event loop
bloklanmasin.)

Bu, projedeki "fetcher -> repository donusumu ileride bir orkestrasyon/
servis katmaninda yapilacaktir" notunun (bkz. src/db/repository.py modul
docstring'i) karsiligidir: Is Yatirim'in ham itemCode'lu verisi burada
calculator.py'nin bekledigi standart alan adlarina cevrilip DB'ye o sekilde
yazilir; boylece repository.get_financials() calculator.analyze()'a
DOGRUDAN verilebilir hale gelir.

Bilinen sinirlar (kasitli, "varsayimsal parser yazma" ilkesi geregi):
    - XI_29 (sanayi/ticaret), UFRS (konvansiyonel banka), UFRS_KATILIM
      (katilim bankasi, orn. ALBRK) VE UFRS_K (sigorta) semalari canli
      veriyle dogrulanip standart alanlara eslendi (bkz. isyatirim.py
      STANDARD_ITEM_MAP_XI_29 / STANDARD_ITEM_MAP_UFRS /
      STANDARD_ITEM_MAP_UFRS_KATILIM / STANDARD_ITEM_MAP_UFRS_K).
      "UFRS_KATILIM" GERCEK bir Is Yatirim financialGroup degeri DEGILDIR --
      bu modulun kendi ic siniflandirmasidir (bkz. isyatirim.py
      _resolve_actual_group: Is Yatirim'in uc noktasi 'financialGroup'u
      guvenilir sekilde filtrelemiyor, katilim bankalari da "UFRS" ile
      sorulunca veri donduruyor ama TAMAMEN FARKLI itemCode siralamasi
      kullaniyor). UFRS_K'yi ARACI KURUMLAR da paylasir ama TAMAMEN FARKLI
      kalemler kullanabilir (henuz dogrulanmadi) -- STANDARD_ITEM_MAP_UFRS_K
      SADECE sigorta sirketleri (ANSGR ile dogrulandi) icin gecerlidir;
      araci kurum bir hisse UFRS_K donerse yanlis/anlamsiz kalemlerle
      eslenebilir (bilinen bir risk, henuz ayirt edilmiyor).
    - financial_group'a gore analiz/kart yolu belirlenir: XI_29 ->
      calculator.analyze()/scorer.score_industrial()/card.build_card_context(),
      UFRS/UFRS_KATILIM -> calculator.analyze_bank()/scorer.score_bank()/
      card.build_bank_card_context() (UFRS_KATILIM icin bank_variant=
      'participation' ile SADECE etiketler degisir, bkz. calculator.py),
      UFRS_K -> calculator.analyze_insurance()/scorer.score_insurance()/
      card.build_insurance_card_context() (bkz. run_pipeline icindeki dallanma).
    - KAP TAZELIK YAMASI (bkz. src/fetchers/kap_financials.py, SADECE XI_29
      icin): Is Yatirim'in MaliTablo uc noktasi KAP'ta yayinlanan bir
      bilancoyu islemek icin saatler/gunler alabiliyor (canli dogrulandi:
      TATGD icin KAP'ta 2Ç26 raporu yayinlandiginda Is Yatirim hala 1Ç26
      donduruyordu). _patch_with_kap_if_fresher(), Is Yatirim'in en guncel
      olarak dondurdugu donemden DAHA YENI bir KAP "Finansal Rapor"u varsa
      o TEK donemi KAP'tan (XBRL taxonomy tag'leriyle) cekip DB'ye ekler.
      KAP'tan veri CEKILEMEZSE veya daha yeni donem YOKSA sessizce atlanir
      (bu yama ASLA pipeline'i BLOKE ETMEMELI).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

import config
from src.ai import commentary as commentary_module
from src.analysis import calculator, fundamental_screens, scorer, valuation
from src.analysis import lens_bilesik_skor, lens_buyume, lens_common, lens_deger, lens_guvenlik, lens_kalite
from src.analysis import merton as merton_module
from src.db import models, repository
from src.fetchers import earnings_calendar, isyatirim, kap, kap_financials, price_history, sec_edgar, stockanalysis
from src.render import card

logger = logging.getLogger(__name__)

Period = tuple[int, int]

_QUARTERLY_FIELDS: tuple[str, ...] = (
    "revenue",
    "gross_profit",
    "operating_profit",
    "operating_profit_ebitda_base",
    "net_income",
    "depreciation_amortization",
    "operating_cash_flow",  # Faz 21 (Degerleme ekrani) -- Piotroski F-Skoru kriter 2/4
    # Faz "Veri Tamlığı" V-07 (docs/spec/spec_veri_tamlik_yol_haritasi.md) --
    # isyatirim.STANDARD_ITEM_MAP_XI_29'a YENI eklenen "pretax_profit"/
    # "tax_provision" ("3I"/"3IA") whitelist'e eklendi.
    "pretax_profit",
    "tax_provision",
    # Faz "Veri Tamlığı" V-10/V-11/V-12 -- isyatirim.STANDARD_ITEM_MAP_XI_29'a
    # YENI eklenen "capex"/"dividends_paid"/"net_financing_debt_change"
    # ("4CAI"/"4CBB"/"4CBA") whitelist'e eklendi. "capex"/"dividends_paid"
    # NASDAQ (US_GAAP) ile AYNI alan adini kullanir -- calculator.py'nin
    # ttm_capex/capex_to_net_income_pct VE YENI payout_ratio_pct rasyolari
    # PIYASA-BAGIMSIZ oldugu icin ekstra kod GEREKMEDEN BIST'te de calisir.
    "capex",
    "dividends_paid",
    "net_financing_debt_change",
)
_STOCK_FIELDS: tuple[str, ...] = (
    "total_assets",
    "current_assets",
    "trade_receivables",
    "equity",
    "cash",
    "financial_investments",
    "short_term_liabilities",
    "long_term_liabilities",  # Faz 3c (v2 skorlama, spec_mercek_guvenlik.md) -- Toplam Yukumluluk/Ozkaynak (genis
    # tanim) bileseninin girdisi. isyatirim.STANDARD_ITEM_MAP_XI_29'da ZATEN eslenmisti ("2B"), sadece bu
    # whitelist'e EKSIKTI -- YENI bir fetcher/kesif GEREKTIRMEDI, SIFIR maliyetli bir "quick win".
    "share_capital",
    "tangible_fixed_assets",  # Faz 21 (Degerleme ekrani) -- Greenblatt "Net Fixed Assets" bileseni
    "long_term_financial_debt",  # Faz 21 -- Piotroski "uzun vadeli kaldirac degisimi" kriteri (2BA zaten esleniyordu, sadece _STOCK_FIELDS'e eklendi)
)

# Banka (UFRS) alanlari -- bkz. isyatirim.STANDARD_ITEM_MAP_UFRS.
_UFRS_QUARTERLY_FIELDS: tuple[str, ...] = (
    "interest_income",
    "interest_expense",
    "net_fee_income",
    "net_operating_profit",
    "net_income",
)
_UFRS_STOCK_FIELDS: tuple[str, ...] = (
    "loans",
    "deposits",
    "provisions",
    "total_assets",
    "equity",
    "share_capital",
)

# Sigorta (UFRS_K) alanlari -- bkz. isyatirim.STANDARD_ITEM_MAP_UFRS_K.
_UFRS_K_QUARTERLY_FIELDS: tuple[str, ...] = (
    "gross_written_premiums",
    "net_premiums_earned",
    "technical_income",
    "net_income",
)
_UFRS_K_STOCK_FIELDS: tuple[str, ...] = (
    "receivables_from_operations",
    "payables_from_operations",
    "equity",
    "share_capital",
)

# Tasarruf Finansman Sirketleri (XI_29K, orn. KTLEV) alanlari -- bkz.
# isyatirim.STANDARD_ITEM_MAP_FINANSMAN.
_FINANSMAN_QUARTERLY_FIELDS: tuple[str, ...] = (
    "financing_revenue",
    "operating_expenses",
    "net_operating_profit",
    "net_income",
)
_FINANSMAN_STOCK_FIELDS: tuple[str, ...] = (
    "cash",
    "overdue_receivables",
    "total_assets",
    "equity",
    "share_capital",
)

# NASDAQ/ABD (US_GAAP) alanlari -- bkz. sec_edgar.STANDARD_ITEM_MAP_US_GAAP.
# Alan adlari BILEREK XI_29 ile AYNI tutuldu (revenue/gross_profit/
# operating_profit/net_income/total_assets/current_assets/equity/cash) ki
# Faz 10'da calculator.analyze()/FIELD_LABELS_TR DOGRUDAN yeniden
# kullanilabilsin. "shares_outstanding" YENI bir alandir (BIST'teki
# "share_capital" ile KARISTIRILMAMALI -- bkz. sec_edgar.py modul notu:
# ABD sirketlerinde nominal pay degeri yok, piyasa degeri price *
# shares_outstanding ile hesaplanmali).
_US_GAAP_QUARTERLY_FIELDS: tuple[str, ...] = (
    "revenue",
    "gross_profit",
    "operating_profit",
    "net_income",
    "depreciation_amortization",
    # Faz "Veri Tamlığı" İlk Dalga (docs/spec/spec_veri_tamlik_yol_haritasi.md
    # V-01/V-02/V-08/V-09/V-03) -- bkz. sec_edgar.STANDARD_ITEM_MAP_US_GAAP
    # ilgili alan yorumları. Genel (özel dallanma gerektirmeyen) `else`
    # dalıyla otomatik hem çeyreklik hem kümülatif (`_cum`) olarak DB'ye
    # yazılır (bkz. _standardize_to_records_us_gaap).
    "sga_expense",
    "research_development_expense",
    "interest_expense",
    "capex",
    "dividend_per_share",
    # Faz "Veri Tamlığı" V-12 (docs/spec/spec_veri_tamlik_yol_haritasi.md) --
    # bkz. sec_edgar.STANDARD_ITEM_MAP_US_GAAP ilgili alan yorumları.
    "dividends_paid",
    "share_buyback",
)
_US_GAAP_STOCK_FIELDS: tuple[str, ...] = (
    "total_assets",
    "current_assets",
    "short_term_liabilities",
    "trade_receivables",
    "equity",
    "cash",
    "shares_outstanding",
    # Faz "Veri Tamlığı" V-04 -- Hazine Hissesi Düzeltmeli ROE bileşeninin girdisi.
    "treasury_stock",
    # Faz "Veri Tamlığı" V-13 -- bkz. sec_edgar.STANDARD_ITEM_MAP_US_GAAP
    # ilgili alan yorumları.
    "diluted_shares_weighted_avg",
    "basic_shares_weighted_avg",
)


class PipelineError(Exception):
    """Boru hatti icin taban hata sinifi."""


class TickerNotFoundError(PipelineError):
    """Hisse kodu Is Yatirim'da (BIST) veya SEC company_tickers.json'da
    (NASDAQ) hic BULUNAMADI -- muhtemelen bir yazim hatasi."""


class FinancialDataNotFoundError(PipelineError):
    """SADECE NASDAQ/US_GAAP: ticker SEC'te (company_tickers.json) KAYITLI
    ama companyfacts'te HICBIR donemde net_income turetilemedi -- bkz.
    sec_edgar.FinancialDataNotAvailableError. CANLI hata (kullanici raporu,
    2026-08-02: 'SKHY' aratildi, bot 'bulamadim' dedi): SKHY -> SK hynix
    Inc.'in CIK'i VAR ama companyfacts SADECE 'ffd' (Form D ucret verisi)
    icin fact iceriyor, 'us-gaap' ad alani BOMBOS -- yabanci ozel ihracci
    (foreign private issuer) genelde ABD GAAP/XBRL ile 10-Q/10-K raporlamaz.
    TickerNotFoundError'dan AYRI tutulur ki bot kullaniciya "yazim hatasi mi"
    yerine "bu sirket ABD SEC standardinda raporlamiyor olabilir" gibi
    DOGRU bir aciklama versin (Kural: anlamli hata mesaji)."""


class UnsupportedCompanyTypeError(PipelineError):
    """Sirket XI_29 disinda bir semaya (banka/sigorta/araci kurum) sahip;
    standart alan eslemesi henuz sadece XI_29 icin tanimli."""


class DataSourceUnavailableError(PipelineError):
    """Veri kaynagina (Is Yatirim) ag seviyesinde ulasilamadi."""


class PeriodNotAvailableError(PipelineError):
    """Istenen (en guncel) donem henuz aciklanmamis; bir onceki ceyrek
    MEVCUT bulunduysa `available_label`/`retry_periods` doldurulur ki
    cagiran taraf (bot) kullaniciya "o donemi analiz edeyim mi?" diye sorup
    onay alirsa run_pipeline'i `periods=retry_periods` ile tekrar cagirsin."""

    def __init__(self, ticker: str, requested_label: str, available_label: str | None, retry_periods: list[Period] | None):
        self.ticker = ticker
        self.requested_label = requested_label
        self.available_label = available_label
        self.retry_periods = retry_periods
        super().__init__(f"{ticker}: {requested_label} donemi yok, en son mevcut: {available_label}")


@dataclass(frozen=True)
class PipelineResult:
    ticker: str
    analysis: (
        calculator.AnalysisResult
        | calculator.BankAnalysisResult
        | calculator.InsuranceAnalysisResult
        | calculator.FinancingAnalysisResult
    )
    score: scorer.ScoreResult
    commentary: commentary_module.Commentary
    png_path: str
    company_name: str
    sector: str | None
    # Faz 14 (X teaser kartı) icin eklendi -- ana kart zaten `price`'i
    # build_*_card_context()'e geciriyordu ama run_pipeline() donduginde
    # bu yerel degisken KAYBOLUYORDU; teaser karti AYRI bir fiyat cekme
    # istegine gerek KALMADAN (ikincil veri, Kural 9) burada tekrar
    # kullanabilsin diye PipelineResult'a eklendi.
    price: Decimal | None = None


@dataclass(frozen=True)
class FundamentalScreensResult:
    """`compute_fundamental_screens_for_ticker()` çıktısı -- render katmanının
    (fundamental_screens_card.py) ihtiyaç duyduğu ticker/şirket adı/fiyat
    render/görüntüleme bilgisini `fundamental_screens.FundamentalScreens`
    (SAF matematik, ticker/isim gibi görüntüleme alanı TAŞIMAZ) ile birlikte
    tek bir pakette taşır -- `PipelineResult`'ın (yukarısı) AYNI ilkesi."""

    ticker: str
    company_name: str | None
    price: Decimal | None
    applicable: bool  # False: banka/sigorta/katılım bankası -- bu yöntem bu şirket türüne uygulanamaz
    screens: "fundamental_screens.FundamentalScreens | None"  # applicable=True ise dolu


def quarter_label(period: Period, annual_only: bool = False) -> str:
    """`annual_only=True` (bkz. calculator.AnalysisResult.is_annual_only, B21
    -- NVO/TSM/SHEL/BABA gibi SADECE yillik veri raporlayan ADR/20-F
    sirketleri): "nÇyy" yerine "FYyy" doner -- bu sirketlerde gosterilen
    rakam izole bir ceyrek DEGIL, tam yilin kendisidir (Kural 8: "4Ç26"
    demek YANLIS/uydurma olurdu, bkz. src/render/card.py._fiscal_quarter_label
    ile AYNI ilke)."""
    year, quarter = period
    if annual_only:
        return f"FY{year % 100:02d}"
    return f"{quarter // 3}Ç{year % 100:02d}"


def _standardize_to_records(raw: isyatirim.RawFinancials) -> list[repository.FinancialRecord]:
    """RawFinancials'in ham itemCode'larini calculator.py'nin bekledigi
    standart alan adlarina (zaten ceyreklestirilmis/stok) cevirir.

    _QUARTERLY_FIELDS icin CEYREKLESTIRILMIS (tek ceyrek) deger `field`
    adiyla kaydedilir -- TTM toplamlari/rasyolar/skorlama/ceyreklik seri
    grafigi bunu kullanir (bunlar icin dogru olan budur, kumulatif degerleri
    ust uste toplamak yanlis olurdu). AYRICA aynı kalemin HAM KUMULATIF
    (YTD, sirketin/KAP'in/Is Yatirim'in/Fintables'in/Matriks'in DEFAULT
    olarak gosterdigi) hali `{field}_cum` adiyla AYRICA kaydedilir --
    kullanici geri bildirimi: kart uzerindeki GELIR TABLOSU ozet
    tablosundaki rakamlar, insanlarin alistigi Fintables/Matriks
    kumulatif rakamlariyla BIREBIR eslessin diye (bkz. calculator.analyze
    icindeki income_statement/findings kullanimlari)."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _QUARTERLY_FIELDS:
            if field == "revenue":
                # bkz. isyatirim.total_revenue() docstring'i: "3C" tek basina
                # finans/leasing kolu olan sirketlerde (orn. TOASO) Fintables'in
                # "Satislar" kaleminden sistematik dusuk kaliyordu (canli
                # dogrulandi, TL'ye kadar eslesti) -- '3CAC' finans segmenti
                # gelirini de dahil eder.
                value = isyatirim.quarterly_total_revenue(raw, period)
                cum_value = isyatirim.total_revenue(raw, period)
            else:
                value = isyatirim.quarterly_standardized_value(raw, field, period)
                cum_value = isyatirim.standardized_value(raw, field, period)

            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))
        for field in _STOCK_FIELDS:
            value = isyatirim.standardized_value(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))
        debt = isyatirim.total_debt(raw, period)
        if debt is not None:
            records.append((period[0], period[1], "financial_debt", calculator.FIELD_LABELS_TR["financial_debt"], debt))
    return records


def _standardize_to_records_ufrs(raw: isyatirim.RawFinancials) -> list[repository.FinancialRecord]:
    """_standardize_to_records()'un banka (UFRS) karsiligi -- bkz. isyatirim.py
    STANDARD_ITEM_MAP_UFRS. Gelir tablosu alanlari icin de ayni sekilde hem
    CEYREKLESTIRILMIS (field) hem HAM KUMULATIF (field_cum) hali kaydedilir."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _UFRS_QUARTERLY_FIELDS:
            value = isyatirim.quarterly_standardized_value_ufrs(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            cum_value = isyatirim.standardized_value_ufrs(raw, field, period)
            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))
        for field in _UFRS_STOCK_FIELDS:
            value = isyatirim.standardized_value_ufrs(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))
    return records


def _standardize_to_records_ufrs_katilim(raw: isyatirim.RawFinancials) -> list[repository.FinancialRecord]:
    """_standardize_to_records_ufrs()'un katilim bankasi karsiligi -- bkz.
    isyatirim.py STANDARD_ITEM_MAP_UFRS_KATILIM. Alan adlari konvansiyonel
    bankayla AYNIDIR (interest_income, deposits, vb.) -- SADECE itemCode
    esleme farklidir; goruntulenen Turkce etiket (Kâr Payı Gelirleri gibi)
    calculator.analyze_bank(bank_variant='participation') tarafinda RENDER
    ANINDA secilir, burada DB'ye yazilan 'label' sadece bilgi amaclidir."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _UFRS_QUARTERLY_FIELDS:
            value = isyatirim.quarterly_standardized_value_ufrs_katilim(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            cum_value = isyatirim.standardized_value_ufrs_katilim(raw, field, period)
            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))
        for field in _UFRS_STOCK_FIELDS:
            value = isyatirim.standardized_value_ufrs_katilim(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))
    return records


def _standardize_to_records_ufrs_k(raw: isyatirim.RawFinancials) -> list[repository.FinancialRecord]:
    """_standardize_to_records()'un sigorta (UFRS_K) karsiligi -- bkz.
    isyatirim.py STANDARD_ITEM_MAP_UFRS_K. "technical_balance" (Teknik Denge),
    "cash_and_financial_assets" (Nakit Benzeri Finansal Varliklar) ve
    "technical_provisions" (Teknik Karsiliklar) tek bir itemCode karsiligi
    olmadigi icin (dogrulanmis IKI kalemin toplami, bkz. isyatirim.py ilgili
    fonksiyonlar) STANDARD_ITEM_MAP_UFRS_K'de degil, ayri hesaplanir."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _UFRS_K_QUARTERLY_FIELDS:
            value = isyatirim.quarterly_standardized_value_ufrs_k(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            cum_value = isyatirim.standardized_value_ufrs_k(raw, field, period)
            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))
        for field in _UFRS_K_STOCK_FIELDS:
            value = isyatirim.standardized_value_ufrs_k(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

        technical_balance = isyatirim.quarterly_technical_balance_ufrs_k(raw, period)
        if technical_balance is not None:
            records.append(
                (period[0], period[1], "technical_balance", calculator.FIELD_LABELS_TR["technical_balance"], technical_balance)
            )
        technical_balance_cum = isyatirim.technical_balance_ufrs_k(raw, period)
        if technical_balance_cum is not None:
            records.append(
                (period[0], period[1], "technical_balance_cum", calculator.FIELD_LABELS_TR["technical_balance_cum"], technical_balance_cum)
            )
        cash_and_financial = isyatirim.cash_and_financial_assets_ufrs_k(raw, period)
        if cash_and_financial is not None:
            records.append(
                (period[0], period[1], "cash_and_financial_assets", calculator.FIELD_LABELS_TR["cash_and_financial_assets"], cash_and_financial)
            )
        technical_provisions = isyatirim.technical_provisions_ufrs_k(raw, period)
        if technical_provisions is not None:
            records.append(
                (period[0], period[1], "technical_provisions", calculator.FIELD_LABELS_TR["technical_provisions"], technical_provisions)
            )
    return records


def _standardize_to_records_financing(raw: isyatirim.RawFinancials) -> list[repository.FinancialRecord]:
    """_standardize_to_records()'un Tasarruf Finansman Sirketi (XI_29K, orn.
    KTLEV) karsiligi -- bkz. isyatirim.py STANDARD_ITEM_MAP_FINANSMAN."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _FINANSMAN_QUARTERLY_FIELDS:
            value = isyatirim.quarterly_standardized_value_financing(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            cum_value = isyatirim.standardized_value_financing(raw, field, period)
            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))
        for field in _FINANSMAN_STOCK_FIELDS:
            value = isyatirim.standardized_value_financing(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))
    return records


def _stockanalysis_yedek_veri(ticker: str) -> dict[Period, stockanalysis.QuarterlyIncomeSnapshot] | None:
    """SEC'te (ozellikle genc/kucuk NASDAQ sirketlerinde, bkz. 06_BILINEN_
    SORUNLAR.md §B17 -- orn. ASTS) eksik kalan Satislar/Brut Kar/Esas
    Faaliyet Kari icin YEDEK kaynak. SADECE cagiran taraf (asagida,
    _standardize_to_records_us_gaap) SEC verisinde en az bir eksik
    bulduysa cagrilir -- SEC'in eksiksiz oldugu (ornegin AAPL/NVDA/MSFT)
    COGUNLUK durumda GEREKSIZ bir dis istek YAPILMAZ.

    Kural 9 geregi bu IKINCIL/yardimci bir veri kaynagidir -- HERHANGI bir
    hata (ag, ayristirma, site yapisi degisikligi) pipeline'i ASLA
    BLOKLAMAZ, sessizce None doner ve loglanir; SEC'te eksik kalan alanlar
    bu durumda N/A kalmaya devam eder (Kural 3: yanlis rakamdan iyidir)."""
    try:
        snapshots = stockanalysis.fetch_quarterly_income(ticker)
    except stockanalysis.StockAnalysisError:
        logger.warning(
            "%s icin stockanalysis.com yedek verisi cekilemedi -- SEC'teki eksik alanlar N/A kalacak", ticker,
            exc_info=True,
        )
        return None
    return {snap.period: snap for snap in snapshots}


def _standardize_to_records_us_gaap(raw: sec_edgar.RawUsFinancials) -> list[repository.FinancialRecord]:
    """_standardize_to_records()'un NASDAQ/ABD (US_GAAP) karsiligi -- bkz.
    sec_edgar.py STANDARD_ITEM_MAP_US_GAAP. `raw.periods` icindeki Period
    ciftleri (fiscal_year, fiscal_period) sirketin KENDI mali yili/ceyregidir
    (takvim yili DEGIL, bkz. sec_edgar.py modul notu) -- calculator.py'nin
    (year, period) uzerinde SADECE siralama matematigi yaptigi icin bu
    DOGRUDAN uyumludur, ekstra bir donusum GEREKMEZ.

    BIST XI_29'daki gibi "financial_debt" (kisa+uzun vadeli finansal borc
    toplami) TEK bir bilesik alan olarak yazilir (bkz. sec_edgar.total_debt_us_gaap);
    "short_term_financial_debt"/"long_term_financial_debt" bilesenleri
    AYRICA DB'ye yazilmaz -- XI_29 ile BIREBIR AYNI davranis.

    FAVOK (bkz. calculator.ebitda() docstring'i) XI_29'da IKI AYRI kalemden
    (dar "operating_profit_ebitda_base" + amortisman) turetilir çünkü İş
    Yatırım'ın "Faaliyet Karı" (3DF, GENIS -- Diğer Faaliyet Gelir/Giderleri
    DAHIL) ile FAVÖK'un tabani (3H, DAR) FARKLI KALEMLERDIR. US GAAP'te bu
    ayrim YOK -- stockanalysis.com/Yahoo Finance gibi platformlarin da
    kullandigi standart yaklasim TEK bir "Operating Income" (OperatingIncomeLoss)
    + D&A'dir (CANLI dogrulandi: AAPL FY2024 OperatingIncomeLoss $123,216 mr +
    D&A $11,445 mr = $134,661 mr -- kamuya acik/iyi bilinen Apple FAVOK
    rakamiyla BIREBIR eslesiyor). Bu yuzden "operating_profit_ebitda_base"
    (VE kumulatif karsiligi) burada AYRI bir SEC tag'inden DEGIL, dogrudan
    "operating_profit" ile AYNI deger olarak YAZILIR -- boylece calculator.ebitda()/
    ebitda_cum() SIFIR degisiklikle (kopyalanmadan) US_GAAP verisinde de
    calisir (bkz. calculator.analyze_us() -- ayni _build_analysis_result()
    cekirdegini kullanir).

    §B17 (kullanici raporu, ASTS): SEC XBRL'de "revenue"/"gross_profit"/
    "operating_profit" bir donem icin HALA None ise (SEC otoritatif
    kaynaktir ama genc/kucuk sirketler bu tag'leri raporlamayi BIRAKABILIYOR,
    bkz. sec_edgar.py STANDARD_ITEM_MAP_US_GAAP "revenue" notu) SADECE O
    DURUMDA stockanalysis.com'dan (bkz. _stockanalysis_yedek_veri) TEK
    ceyreklik (KUMULATIF DEGIL -- stockanalysis zaten ceyreklik veri
    verdigi icin "_cum" alani doldurulmaz, TTM/kaldirac bileseni bu
    donemler icin N/A KALMAYA devam eder) deger YEDEK olarak kullanilir."""
    # B21 (ADR/yabanci ozel ihracci -- NVO/TSM/SHEL/BABA gibi 20-F dosyalayan
    # sirketler): bu sirketler SADECE fp="FY" raporlar, hic Q1-Q3 donemi
    # YOKTUR. Boyle bir sirket icin ceyreklik turetme (kumulatif - onceki
    # ceyrek kumulatif) HER ZAMAN None doner (onceki ceyrek hic YOK) --
    # bu KENDI BASINA dogru/zararsizdir (Kural 8). ANCAK "yedek_gerekli"
    # tetiklenip stockanalysis.com'dan TAKVIM CEYREGI bazli veri cekilirse,
    # o verinin (fy,fp) anahtari bu sirketin mali YIL bazli anahtariyla
    # YANLIS eslesip TAMAMEN ILGISIZ bir donemin rakamini "guncel" gibi
    # gosterebilir (CANLI DOGRULANDI, kullanici raporu incelemesi: BABA
    # icin boyle bir yanlis eslesme bulundu, bkz. 06_BILINEN_SORUNLAR.md
    # §B21). Bu yuzden annual-only sirketlerde yedek YOLU HIC DENENMEZ VE
    # "guncel" alana DOGRUDAN TAM YIL kumulatif deger yazilir (asagida) --
    # zaten annual-only bir sirket icin "TEK CEYREK" diye bir kavram
    # YOKTUR, gosterilecek DOGRU rakam ZATEN tam yilin kendisidir.
    # SADECE en yakin zamanli (en fazla 4) donem penceresine bakilir --
    # `raw.periods` (yeniden eskiye siralidir) COK eski (bazen tek, izole)
    # bir fp="Q2"/"Q3" fact'i (CANLI dogrulandi: BABA'da 2020'den kalma
    # boyle bir fact var, muhtemelen bir gecis donemi dosyalamasi/SEC fy-fp
    # etiketleme tuhafligi -- bkz. _select_best_fact ust notu) TASIYABILIR;
    # bu TEK BASINA sirketi "hala ceyreklik raporluyor" sanmamiza yol
    # ACMAMALI. SHEL gibi YARI YILLIK (H1+FY, fp=6/12) raporlayan sirketler
    # bu pencerede fp=6 GORECEGI icin annual_only=False kalir -- bu BILINCLI
    # bir sinir (yari-yillik turetme AYRI/daha karmasik bir konu, bkz.
    # 06_BILINEN_SORUNLAR.md §B21, bu oturumda cozulmedi).
    _annual_check_window = raw.periods[:4]
    annual_only = bool(_annual_check_window) and all(fp == 12 for _, fp in _annual_check_window)

    yedek_gerekli = not annual_only and any(
        sec_edgar.standardized_value_us_gaap(raw, alan, donem) is None
        for donem in raw.periods
        for alan in ("revenue", "gross_profit", "operating_profit")
    )
    yedek_veri = _stockanalysis_yedek_veri(raw.ticker) if yedek_gerekli else None

    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        yedek_donem = yedek_veri.get(period) if yedek_veri else None
        for field in _US_GAAP_QUARTERLY_FIELDS:
            if field == "revenue":
                value = sec_edgar.quarterly_standardized_value_us_gaap(raw, field, period)
                cum_value = sec_edgar.standardized_value_us_gaap(raw, field, period)
                if value is None and yedek_donem is not None and yedek_donem.revenue is not None:
                    value = yedek_donem.revenue
            elif field == "gross_profit":
                # bkz. sec_edgar.gross_profit_us_gaap() docstring'i: dogrudan
                # "GrossProfit" tag'i (AAPL/NVDA/MSFT/TSLA/AMD) yoksa Hasilat -
                # Satislarin Maliyeti turetilir (GOOGL/AMZN/META/NFLX --
                # stockanalysis.com ile BIREBIR dogrulandi, PYPL'de HALA None).
                value = sec_edgar.quarterly_gross_profit_us_gaap(raw, period)
                cum_value = sec_edgar.gross_profit_us_gaap(raw, period)
                if value is None and yedek_donem is not None and yedek_donem.gross_profit is not None:
                    value = yedek_donem.gross_profit
            elif field == "operating_profit":
                value = sec_edgar.quarterly_standardized_value_us_gaap(raw, field, period)
                cum_value = sec_edgar.standardized_value_us_gaap(raw, field, period)
                if value is None and yedek_donem is not None and yedek_donem.operating_profit is not None:
                    value = yedek_donem.operating_profit
            elif field == "depreciation_amortization":
                # bkz. sec_edgar.depreciation_amortization_us_gaap() docstring'i:
                # dogrudan birlesik tag yoksa (MSFT -- CANLI hata, kullanici
                # raporu: FAVOK satiri kartta eksikti) Depreciation +
                # AmortizationOfIntangibleAssets TOPLANARAK turetilir.
                value = sec_edgar.quarterly_depreciation_amortization_us_gaap(raw, period)
                cum_value = sec_edgar.depreciation_amortization_us_gaap(raw, period)
            else:
                value = sec_edgar.quarterly_standardized_value_us_gaap(raw, field, period)
                cum_value = sec_edgar.standardized_value_us_gaap(raw, field, period)

            if annual_only:
                # bkz. yukaridaki annual_only notu -- ceyreklik turetme
                # DENENMEZ, tam yil kumulatif deger DOGRUDAN "guncel" olarak
                # kullanilir (ikisi ZATEN ayni sey: annual-only bir sirket
                # icin "bu yilin verisi" = "bu ceyregin verisi").
                value = cum_value

            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

            if cum_value is not None:
                cum_label = calculator.FIELD_LABELS_TR.get(f"{field}_cum", field)
                records.append((period[0], period[1], f"{field}_cum", cum_label, cum_value))

            if field == "operating_profit":
                if value is not None:
                    records.append((period[0], period[1], "operating_profit_ebitda_base", "FAVÖK Baz Faaliyet Kârı (iç kullanım)", value))
                if cum_value is not None:
                    records.append((period[0], period[1], "operating_profit_ebitda_base_cum", "FAVÖK Baz Faaliyet Kârı (iç kullanım)", cum_value))
        for field in _US_GAAP_STOCK_FIELDS:
            value = sec_edgar.standardized_value_us_gaap(raw, field, period)
            if value is not None:
                label = calculator.FIELD_LABELS_TR.get(field, field)
                records.append((period[0], period[1], field, label, value))

        debt = sec_edgar.total_debt_us_gaap(raw, period)
        if debt is not None:
            records.append(
                (period[0], period[1], "financial_debt", calculator.FIELD_LABELS_TR["financial_debt"], debt)
            )

        # AMD/TSLA gibi sirketlerde (bkz. 06_BILINEN_SORUNLAR.md §B20)
        # standart "depreciation_amortization_cum" bir bilesenin (orn.
        # AMD'nin 'Depreciation'i) hic ceyreklik/YTD kirilimi olmamasi
        # yuzunden None kalabiliyor -- bu da TTM FAVOK'u (Kaldirac orani VE
        # kart FAVOK satiri icin) surekli N/A birakiyordu. Ayrica, BAGIMSIZ
        # bir TTM D&A degeri (sec_edgar.trailing_12m_depreciation_amortization_us_gaap,
        # farkli bir stratejiyle -- ceyreklik toplam / yapisal-yoksayma /
        # en son yillik gercek deger) DB'ye YEDEK olarak yazilir;
        # calculator.analyze_us() SADECE standart yontem basarisiz olursa
        # bunu kullanir (bkz. calculator._build_analysis_result ici not).
        ttm_da = sec_edgar.trailing_12m_depreciation_amortization_us_gaap(raw, period)
        if ttm_da is not None:
            records.append(
                (period[0], period[1], "depreciation_amortization_ttm", "FAVÖK TTM D&A (iç kullanım)", ttm_da)
            )
    return records


_QUARTER_END_MONTH_DAY = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}
_MAX_FORWARD_PROBES = 2


def _quarter_has_ended(period: Period) -> bool:
    year, quarter = period
    month, day = _QUARTER_END_MONTH_DAY[quarter]
    return date(year, month, day) <= date.today()


def _next_quarter_period(period: Period) -> Period:
    year, quarter = period
    return (year, quarter + 3) if quarter != 12 else (year + 1, 3)


def _probe_period_has_data(ticker: str, candidate: Period, known_good_periods: list[Period], financial_group: str) -> bool:
    """`candidate` doneminin GERCEKTEN yayinlanip yayinlanmadigini kontrol
    eder. ONEMLI: Is Yatirim uc noktasi SADECE candidate'i tek basina
    (baska donem eklemeden) sorunca -- o donem hicbir grupta yoksa --
    TAMAMEN BOS bir yanit donuyor; fetch_financials bunu "sirket/grup
    bulunamadi" (CompanyNotFoundError) sanip YANLIS grubu deniyor (canli
    dogrulandi: TAVHL icin boyle sorunca CompanyNotFoundError alindi).
    Bu yuzden candidate, ZATEN VERISI OLDUGU BILINEN birkac donemle
    (known_good_periods) VE dogru financial_group ile BIRLIKTE sorulur --
    boylece grup doğru sekilde cozulur ve candidate'in EKSIK oldugu durum
    doğru sekilde FinancialDataNotAvailableError olarak gelir."""
    probe_periods = [candidate, *known_good_periods[:3]]
    try:
        isyatirim.fetch_financials(ticker, periods=probe_periods, financial_group=financial_group)
        return True
    except (isyatirim.FinancialDataNotAvailableError, isyatirim.CompanyNotFoundError):
        # CompanyNotFoundError da MUMKUN (canli hata, RAYSG): resolved_group
        # ("UFRS_K" gibi bu modulun ic siniflandirma etiketi) buraya TEK
        # BASINA financial_group olarak gecilince fetch_financials bunu
        # DOGRUDAN API parametresi sanip sorguluyor -- bazi sirketlerde
        # (RAYSG) bu TEK-grup sorgusu 0 satir donduruyor (sirket zaten
        # dogrulanmis olsa BILE), CompanyNotFoundError firlatiliyor. Bu
        # istisna yakalanmazsa _find_true_newest_period -> _resolve_raw_financials
        # -> _fetch_and_store zincirinde CompanyNotFoundError olarak kalip
        # YANLISLIKLA TickerNotFoundError'a cevriliyordu (kullanici raporu,
        # 2026-08-04: RAYSG BIST'te GERCEKTEN var ve verisi ZATEN basariyla
        # cekilmisti, sadece bu ileri-prob adiminda YANLIS "bulunamadi"
        # sonucuna dusuluyordu). Burada da FinancialDataNotAvailableError ile
        # AYNI anlama geliyor: "bu aday donem icin veri yok", ticker'in
        # kendisi zaten `raw` ile dogrulanmis durumda.
        return False


def _has_newer_period_available(ticker: str, cached_newest: Period, financial_group: str) -> bool:
    """Onbellek YAS bakimindan "taze" (bkz. run_pipeline, is_data_fresh
    max_age_hours penceresi) olsa bile, `cached_newest`'ten bir SONRAKI
    ceyrek o pencere icinde zaten yayinlanmis olabilir -- canli hata (kullanici
    raporu): YKBNK icin bot hala 1Ç26 gosteriyordu ama 2Ç26 bilancosu KAP/Is
    Yatirim'da ZATEN vardi; onbellek suresi dolmadigi icin _fetch_and_store hic
    tetiklenmiyor, dolayisiyla _find_true_newest_period'un ileri-probe mantigi
    (bkz. asagisi) hic calismiyordu. Bu fonksiyon, TAM fetch'i (8 donem + KAP
    bildirimleri + KAP tazelik yamasi) YAPMADAN, ucuz kontrollerle "bir sonraki
    ceyrek gercekten var mi" sorusuna cevap arar -- cagiran taraf (run_pipeline)
    True donerse onbellegi bypass edip tam fetch'i tetikler.

    IKI AYRI kontrol yapilir (Is Yatirim'in kendisi de KAP'tan GUNLER/SAATLER
    geride kalabiliyor, bkz. kap_financials.py modul notu -- SADECE Is Yatirim'a
    bakmak bu durumda YENI donemi asla YAKALAYAMAZ):
      1. Is Yatirim'da `candidate` (cached_newest+1 ceyrek) dogrudan probe edilir.
      2. Bulamazsa, KAP'ta (XI_29 VE UFRS icin, bkz. _kap_patch_records_for_xi29/
         _kap_patch_records_for_ufrs) cached_newest'ten daha yeni bir Finansal
         Rapor VAR MI diye TEK bir ucuz istekle (sayfa ICERIGI CEKILMEDEN,
         sadece bildirim listesi) kontrol edilir."""
    candidate = _next_quarter_period(cached_newest)
    if _quarter_has_ended(candidate):
        try:
            if _probe_period_has_data(ticker, candidate, [cached_newest], financial_group):
                return True
        except Exception:
            logger.warning(
                "%s icin taze-onbellek Is Yatirim yeni-donem kontrolu basarisiz oldu.",
                ticker, exc_info=True,
            )

    if financial_group not in ("XI_29", "UFRS", "UFRS_K", "XI_29K"):
        return False
    try:
        ref = kap_financials.find_latest_financial_report(ticker)
    except Exception:
        logger.warning(
            "%s icin taze-onbellek KAP yeni-donem kontrolu basarisiz oldu, mevcut onbellek kullanilacak.",
            ticker, exc_info=True,
        )
        return False
    return ref is not None and ref.period > cached_newest


def _find_true_newest_period(ticker: str, raw: isyatirim.RawFinancials) -> Period:
    """guess_last_periods()'un varsayilan 75 gunluk gecikme tahmini FAZLA
    TUTUCU kalabilir -- bazi sirketler cok daha erken raporluyor (canli
    gozlemlendi: TAVHL 2. ceyregi acikladigi halde guess_last_periods hala
    1. ceyregi "en guncel" saniyordu, biz de onu gosteriyorduk). Bu yuzden
    tahminin bir/iki ceyrek ILERISI de (henuz bitmemis ceyrekler HARIC)
    probe edilir; veri varsa o daha yeni donem gercek "en guncel" kabul edilir."""
    newest = max(raw.periods)
    known_good = sorted(raw.periods, reverse=True)
    for _ in range(_MAX_FORWARD_PROBES):
        candidate = _next_quarter_period(newest)
        if not _quarter_has_ended(candidate):
            break
        if not _probe_period_has_data(ticker, candidate, known_good, raw.financial_group):
            break
        logger.info("%s icin tahminden daha yeni bir donem bulundu: %s", ticker, quarter_label(candidate))
        newest = candidate
    return newest


def _resolve_raw_financials(ticker: str, periods: list[Period] | None) -> isyatirim.RawFinancials:
    """Is Yatirim'dan veri ceker.

    `periods` acikca verilmisse (kullanici onceki donemi zaten onayladiysa)
    dogrudan o donemler cekilir, kaydirma/probe YAPILMAZ.

    `periods` verilmemisse (varsayilan "en guncel" akisi):
      1. guess_last_periods() ile tahmin edilen donem henuz aciklanmamissa,
         bir ceyrek GERIYE kaydirip TEK SEFER daha denenir.
      2. Tahmin basarili olsa BILE, sirket tahminden daha erken raporlamis
         olabilecegi icin bir/iki ceyrek ILERISI de probe edilir (bkz.
         _find_true_newest_period); daha yeni bir donem bulunursa O donem
         etrafinda (8 ceyreklik pencere) YENIDEN cekilir.
    """
    if periods is not None:
        return isyatirim.fetch_financials(ticker, periods=periods)

    try:
        raw = isyatirim.fetch_financials(ticker)
    except isyatirim.FinancialDataNotAvailableError:
        shifted = [
            calculator.previous_quarter_period(p)
            for p in isyatirim.guess_last_periods(count=isyatirim.DEFAULT_HISTORY_QUARTERS)
        ]
        logger.info("%s icin en guncel donem henuz yok, bir ceyrek geriye kayarak deneniyor.", ticker)
        return isyatirim.fetch_financials(ticker, periods=shifted)

    guessed_newest = max(raw.periods)
    true_newest = _find_true_newest_period(ticker, raw)
    if true_newest == guessed_newest:
        return raw

    forward_periods: list[Period] = [true_newest]
    while len(forward_periods) < isyatirim.DEFAULT_HISTORY_QUARTERS:
        forward_periods.append(calculator.previous_quarter_period(forward_periods[-1]))
    return isyatirim.fetch_financials(ticker, periods=forward_periods, financial_group=raw.financial_group)


def _fetch_kap_data(ticker: str) -> tuple[str | None, list[kap.Disclosure] | None]:
    """KAP'tan sirket adi + bildirimleri ceker (ag hatalarini kendi icinde
    yutar, sadece uyari loglar -- KAP supplementary veridir, boru hattini
    BLOKE ETMEMELI). _resolve_raw_financials ile PARALEL calistirilabilmesi
    icin DB yazma islemi burada YAPILMAZ (SQLAlchemy Session tek bir is
    parcacigina bagli kalmali); sonuc cagiran tarafin (ana is parcacigi)
    kendi session'iyla yazmasi icin duz deger olarak doner."""
    company_name: str | None = None
    disclosures: list[kap.Disclosure] | None = None

    try:
        company_match = kap.search_company(ticker)
        company_name = company_match.name
    except kap.KapError as exc:
        logger.warning("%s icin KAP sirket adi alinamadi (kart ticker koduyla gosterilecek): %s", ticker, exc)

    try:
        disclosures = kap.fetch_disclosures(ticker, days=config.KAP_LOOKBACK_DAYS)
    except kap.KapError as exc:
        logger.warning("%s icin KAP bildirimleri cekilemedi (bos gecilecek): %s", ticker, exc)

    return company_name, disclosures


# CANLI hata (kullanici raporu, AHSGY, 2026-08-10 -- KRITIK): KAP'in
# "Sunum Para Birimi" basligi ("1.000.000 TL") ile disclosure'a GERCEKTEN
# gomulu ham XBRL rakami birbiriyle TUTARSIZ olabiliyor -- AHSGY'nin KAP
# Finansal Rapor'unda baslik "1.000.000 TL" diyordu ama ham deger (orn.
# Nakit = 1.009.053.647) zaten TAM TL cinsindendi; kap_financials.py'nin
# olcek carpani (x1.000.000) korulukce uygulaninca Nakit "1 katrilyon TL"
# gibi anlamsiz bir rakama sicradi (Toplam Varliklar da ayni sekilde
# sise), bu da karttaki "Degisim" yuzdelerini (%108.430.801,5 gibi)
# anlamsizlastirdi (bkz. 06_BILINEN_SORUNLAR.md #49). Bu, tek bir
# sirkete/olceğe ozgu degil -- HERHANGI bir KAP disclosure'inin basligi
# yanlis/tutarsiz olursa AYNI sinifta bir hataya yol acabilir. Bu yuzden
# KAP'tan patchlenen "toplam" nitelikli kalemler (total_assets/equity),
# Is Yatirim'in ZATEN guvendigi en guncel donemle KARSILASTIRILIR -- tek
# ceyrekte gercekci OLMAYAN (bu esigin USTUNDE) bir sicrama/dususe
# rastlanirsa TUM KAP yamasi (o donem icin) REDDEDILIR, Is Yatirim'in eski
# ama TUTARLI verisiyle devam edilir (Kural 3: yanlis rakamdan iyidir).
_KAP_PATCH_MAX_PLAUSIBLE_RATIO = Decimal(50)


def _kap_patch_is_plausible(
    ticker: str,
    new_period: Period,
    values: dict[str, Decimal | None],
    raw: isyatirim.RawFinancials,
    baseline_period: Period,
    value_fn=isyatirim.standardized_value,
) -> bool:
    """KAP'tan patchlenen total_assets/equity, Is Yatirim'in son bilinen
    donemine gore _KAP_PATCH_MAX_PLAUSIBLE_RATIO kati asan/altina inen bir
    sicrama gosteriyorsa False doner (bkz. yukaridaki CANLI hata notu).
    `value_fn`: Is Yatirim tarafinda karsilastirma degerini okumak icin
    kullanilacak fonksiyon -- XI_29 icin standardized_value, UFRS/UFRS_K
    icin standardized_value_ufrs/standardized_value_ufrs_k (alan adlari
    ayni ('total_assets'/'equity') ama itemCode haritalari farkli)."""
    for field in ("total_assets", "equity"):
        new_value = values.get(field)
        if new_value is None or new_value == 0:
            continue
        try:
            baseline_value = value_fn(raw, field, baseline_period)
        except KeyError:
            continue
        if baseline_value is None or baseline_value == 0:
            continue
        ratio = abs(new_value) / abs(baseline_value)
        if ratio > _KAP_PATCH_MAX_PLAUSIBLE_RATIO or ratio < (Decimal(1) / _KAP_PATCH_MAX_PLAUSIBLE_RATIO):
            logger.warning(
                "%s icin KAP yamasi (%s) reddedildi: '%s' alani Is Yatirim'in %s donemine gore "
                "%.1fx degisim gosteriyor (esik: %sx) -- olcek/birim hatasi olabilir, KAP yamasi ATLANDI.",
                ticker, quarter_label(new_period), field, quarter_label(baseline_period), ratio, _KAP_PATCH_MAX_PLAUSIBLE_RATIO,
            )
            return False
    return True


def _kap_patch_records_for_xi29(
    ticker: str, newest_isyatirim_period: Period, raw: isyatirim.RawFinancials
) -> tuple[list[repository.FinancialRecord], Period | None]:
    """Is Yatirim'in dondurdugu en guncel donemden (newest_isyatirim_period)
    DAHA YENI bir KAP 'Finansal Rapor'u varsa, o TEK donemi KAP'tan cekip
    (records, donem) olarak doner; yoksa veya herhangi bir asamada
    basarisiz olursa ([], None) doner. Bu fonksiyon ASLA istisna FIRLATMAZ
    -- KAP tazelik yamasi HICBIR SEKILDE pipeline'i BLOKE ETMEMELI (bkz.
    src/fetchers/kap_financials.py modul notu).

    NOT (BORSK arastirmasi): bazi sirketlerde KAP'in gelir tablosu satirlari
    sadece 2 kolon doner (ceyreklik kirilim yok) -- bu durumda
    kap_financials.standardized_record_values() ilgili gelir tablosu
    alanlarini (revenue/net_income/vb.) KASITLI olarak None dondurur (bkz.
    RawKapFinancials docstring'i: bu 2 kolonun anlami BORSK'ta denenip
    YANLIS ciktı, guvenilir bir eslestirme YOK). Bu, o ceyrege bagli TTM
    skor bilesenlerinin (Kaldirac, ROE) o donem icin N/A kalmasina yol
    acar -- bu YANLIS bir rakam uretmekten iyidir, bilanco kalemleri
    (bkz. asagida) yine de patchlenir.

    `raw`: _resolve_raw_financials'in ZATEN cektigi Is Yatirim verisi --
    asagidaki FAVOK/amortisman turetmesi icin (ekstra ag istegi OLMADAN)
    kullanilir."""
    try:
        ref = kap_financials.find_latest_financial_report(ticker)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring
        logger.warning("%s icin KAP Finansal Rapor kontrolu basarisiz (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return [], None

    if ref is None or ref.period <= newest_isyatirim_period:
        return [], None

    logger.info(
        "%s icin KAP'ta Is Yatirim'dan (%s) daha yeni bir Finansal Rapor bulundu: %s (disclosure_index=%s)",
        ticker, quarter_label(newest_isyatirim_period), quarter_label(ref.period), ref.disclosure_index,
    )
    raw_kap = kap_financials.fetch_latest_xi29_financials(ticker)
    if raw_kap is None:
        return [], None

    values = kap_financials.standardized_record_values(raw_kap)

    if not _kap_patch_is_plausible(ticker, raw_kap.period, values, raw, newest_isyatirim_period):
        return [], None

    # CANLI hata (kullanici raporu, OTKAR): KAP'tan SADECE KUMULATIF
    # amortisman/itfa gideri gelir (bkz. kap_financials.py _DEPRECIATION_TAG
    # notu) -- TEK CEYREKLIK deger (FAVOK = operating_profit_ebitda_base +
    # depreciation_amortization hesabinin gerektirdigi, bkz. calculator.ebitda)
    # burada turetilmezse FAVOK o donem icin SESSIZCE "N/A" gosterilir. Is
    # Yatirim'in ZATEN cektigi BIR ONCEKI ceyregin kumulatif D&A'siyla fark
    # alinarak (isyatirim.quarterly_value_from_cumulative ile AYNI ilke)
    # turetilir -- BIR ONCEKI ceyrek verisi yoksa (orn. yil basi ceyregiyse)
    # turetme atlanir, FAVOK yine N/A kalir (yanlis rakam uretmekten iyidir).
    if values.get("depreciation_amortization") is None and values.get("depreciation_amortization_cum") is not None:
        prev_period = calculator.previous_quarter_period(raw_kap.period)
        prev_cum = isyatirim.standardized_value(raw, "depreciation_amortization", prev_period)
        if prev_cum is not None:
            values["depreciation_amortization"] = values["depreciation_amortization_cum"] - prev_cum

    year, period_no = raw_kap.period
    records: list[repository.FinancialRecord] = []
    for field, value in values.items():
        if value is None:
            continue
        label = calculator.FIELD_LABELS_TR.get(field, field)
        records.append((year, period_no, field, label, value))

    if not records:
        # Sayfa ayristirildi ama HICBIR standart alan cikarilamadi (orn.
        # beklenmedik bir taxonomy varyanti) -- donemi "bulundu" sayip
        # actual_newest'i sessizce yukseltmek YANLIS olur (Is Yatirim'in
        # eski donemi kullanilmaya devam edecek ama kullaniciya "en guncel"
        # gibi gosterilirdi). Bu yuzden bos durumda ([], None) donuyoruz.
        logger.warning(
            "%s icin KAP Finansal Rapor (disclosure_index=%s) ayristirildi ama hicbir "
            "standart alan cikarilamadi -- Is Yatirim verisiyle devam edilecek.",
            ticker, raw_kap.disclosure_index,
        )
        return [], None

    return records, raw_kap.period


def _kap_patch_records_for_ufrs(
    ticker: str, newest_isyatirim_period: Period, raw: isyatirim.RawFinancials
) -> tuple[list[repository.FinancialRecord], Period | None]:
    """_kap_patch_records_for_xi29()'un konvansiyonel banka (UFRS) karsiligi
    -- bkz. kap_financials.py STANDARD_ITEM_MAP_KAP_UFRS_* modul notu (YKBNK
    ile CANLI dogrulandi, Fintables'in konsolide rakamlarina TL'ye kadar
    birebir eslesti). SADECE financial_group=='UFRS' icin cagrilmali --
    UFRS_KATILIM (katilim bankasi) HENUZ dogrulanmadi, farkli XBRL tag'leri
    kullanabilir (bkz. isyatirim.py 'kar payi' vs 'faiz' notu), bu yuzden
    bu yama UFRS_KATILIM icin calistirilmaz -- katilim bankalari eskisi gibi
    SADECE Is Yatirim'a guvenmeye devam eder. Bu fonksiyon ASLA istisna
    FIRLATMAZ (bkz. _kap_patch_records_for_xi29 ile ayni ilke)."""
    try:
        ref = kap_financials.find_latest_financial_report(ticker)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring
        logger.warning("%s icin KAP Finansal Rapor kontrolu basarisiz (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return [], None

    if ref is None or ref.period <= newest_isyatirim_period:
        return [], None

    logger.info(
        "%s (banka) icin KAP'ta Is Yatirim'dan (%s) daha yeni bir Finansal Rapor bulundu: %s (disclosure_index=%s)",
        ticker, quarter_label(newest_isyatirim_period), quarter_label(ref.period), ref.disclosure_index,
    )
    raw_kap = kap_financials.fetch_latest_ufrs_financials(ticker)
    if raw_kap is None:
        return [], None

    values = kap_financials.standardized_record_values_ufrs(raw_kap)

    if not _kap_patch_is_plausible(
        ticker, raw_kap.period, values, raw, newest_isyatirim_period, value_fn=isyatirim.standardized_value_ufrs
    ):
        return [], None

    year, period_no = raw_kap.period
    records: list[repository.FinancialRecord] = []
    for field, value in values.items():
        if value is None:
            continue
        label = calculator.FIELD_LABELS_TR.get(field, field)
        records.append((year, period_no, field, label, value))

    if not records:
        logger.warning(
            "%s (banka) icin KAP Finansal Rapor (disclosure_index=%s) ayristirildi ama hicbir "
            "standart alan cikarilamadi -- Is Yatirim verisiyle devam edilecek.",
            ticker, raw_kap.disclosure_index,
        )
        return [], None

    return records, raw_kap.period


def _kap_patch_records_for_ufrs_k(
    ticker: str, newest_isyatirim_period: Period, raw: isyatirim.RawFinancials
) -> tuple[list[repository.FinancialRecord], Period | None]:
    """_kap_patch_records_for_xi29()'un sigorta (UFRS_K) karsiligi -- bkz.
    kap_financials.py STANDARD_ITEM_MAP_KAP_UFRS_K_* modul notu (RAYSG ile
    CANLI dogrulandi: net_income 1.896.687.175 TL, kullanicinin Fintables'te
    gordugu "1,9 mr TL" ile birebir eslesti). SADECE financial_group=='UFRS_K'
    icin cagrilmali. Kart'in gosterdigi TUM alanlar (prim/teknik gelir-gider,
    net kar, alacaklar/borclar, teknik karsiliklar, nakit+finansal varliklar,
    ozkaynak/sermaye) bu yamayla doldurulur -- bazi bilesik stok kalemleri
    (cash_and_equivalents'in 1A bileseni, technical_provisions_noncurrent'in
    2MD bileseni) Is Yatirim henuz 2Ç26'yi dondurmedigi icin CROSS-PERIOD
    dogrulanamadi, en yakin karsilikla dolduruldu (bkz. kap_financials.py
    modul notu) -- Is Yatirim kendi verisini isleyince bu alanlar zaten onun
    DAHA GUVENILIR degeriyle EZILECEK. Bu fonksiyon ASLA istisna FIRLATMAZ
    (bkz. _kap_patch_records_for_xi29 ile ayni ilke)."""
    try:
        ref = kap_financials.find_latest_financial_report(ticker)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring
        logger.warning("%s icin KAP Finansal Rapor kontrolu basarisiz (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return [], None

    if ref is None or ref.period <= newest_isyatirim_period:
        return [], None

    logger.info(
        "%s (sigorta) icin KAP'ta Is Yatirim'dan (%s) daha yeni bir Finansal Rapor bulundu: %s (disclosure_index=%s)",
        ticker, quarter_label(newest_isyatirim_period), quarter_label(ref.period), ref.disclosure_index,
    )
    raw_kap = kap_financials.fetch_latest_ufrs_k_financials(ticker)
    if raw_kap is None:
        return [], None

    values = kap_financials.standardized_record_values_ufrs_k(raw_kap)

    if not _kap_patch_is_plausible(
        ticker, raw_kap.period, values, raw, newest_isyatirim_period, value_fn=isyatirim.standardized_value_ufrs_k
    ):
        return [], None

    year, period_no = raw_kap.period
    records: list[repository.FinancialRecord] = []
    for field, value in values.items():
        if value is None:
            continue
        label = calculator.FIELD_LABELS_TR.get(field, field)
        records.append((year, period_no, field, label, value))

    if not records:
        logger.warning(
            "%s (sigorta) icin KAP Finansal Rapor (disclosure_index=%s) ayristirildi ama hicbir "
            "standart alan cikarilamadi -- Is Yatirim verisiyle devam edilecek.",
            ticker, raw_kap.disclosure_index,
        )
        return [], None

    return records, raw_kap.period


def _kap_patch_records_for_financing(
    ticker: str, newest_isyatirim_period: Period, raw: isyatirim.RawFinancials
) -> tuple[list[repository.FinancialRecord], Period | None]:
    """_kap_patch_records_for_xi29()'un Tasarruf Finansman Sirketi (XI_29K,
    orn. KTLEV) karsiligi -- bkz. kap_financials.py STANDARD_ITEM_MAP_KAP_FINANSMAN_*
    modul notu. CANLI hata (kullanici raporu, 2026-08-10): "KTLEV 2Ç bilancosu
    geldi fakat hala 1Ç bilanco geliyor" -- Is Yatirim henuz islememisti, KAP'ta
    ZATEN vardi (TATGD/RAYSG ile AYNI gecikme deseni). Bilanco kalemleri (cash/
    overdue_receivables/total_assets/equity) Is Yatirim'in (2025,12) donemiyle
    TL'ye kadar BIREBIR dogrulandi; "net_operating_profit" icin TEK bir KAP
    tag'i bulunamadigindan (Kural 3) bu alan patch'te None kalir. SADECE
    financial_group=='XI_29K' icin cagrilmali. Bu fonksiyon ASLA istisna
    FIRLATMAZ (bkz. _kap_patch_records_for_xi29 ile ayni ilke)."""
    try:
        ref = kap_financials.find_latest_financial_report(ticker)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring
        logger.warning("%s icin KAP Finansal Rapor kontrolu basarisiz (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return [], None

    if ref is None or ref.period <= newest_isyatirim_period:
        return [], None

    logger.info(
        "%s (finansman) icin KAP'ta Is Yatirim'dan (%s) daha yeni bir Finansal Rapor bulundu: %s (disclosure_index=%s)",
        ticker, quarter_label(newest_isyatirim_period), quarter_label(ref.period), ref.disclosure_index,
    )
    raw_kap = kap_financials.fetch_latest_financing_financials(ticker)
    if raw_kap is None:
        return [], None

    values = kap_financials.standardized_record_values_financing(raw_kap)

    if not _kap_patch_is_plausible(
        ticker, raw_kap.period, values, raw, newest_isyatirim_period, value_fn=isyatirim.standardized_value_financing
    ):
        return [], None

    year, period_no = raw_kap.period
    records: list[repository.FinancialRecord] = []
    for field, value in values.items():
        if value is None:
            continue
        label = calculator.FIELD_LABELS_TR.get(field, field)
        records.append((year, period_no, field, label, value))

    if not records:
        logger.warning(
            "%s (finansman) icin KAP Finansal Rapor (disclosure_index=%s) ayristirildi ama hicbir "
            "standart alan cikarilamadi -- Is Yatirim verisiyle devam edilecek.",
            ticker, raw_kap.disclosure_index,
        )
        return [], None

    return records, raw_kap.period


def _ensure_sector_populated(session: Session, ticker: str) -> None:
    """Faz 16.5 (kullanıcı raporu, 2026-08-04): ULAŞTIRMA sektöründe 3-4
    yeni şirket analiz edildiği hâlde Derin Kart hâlâ "1 karşılaştırma
    şirketi" gösteriyordu -- kök neden: `Company.sector` SADECE elle
    çalıştırılan `scripts/refresh_sector_cache.py` ile dolduruluyordu,
    normal bot kullanımıyla eklenen YENİ şirketler `sector=None` kalıyordu
    (script'in son çalıştığı tarihten SONRA sorgulanan HER şirket bu
    sorunu yaşar). Bu fonksiyon HER XI_29 fetch'inde çağrılır ama SADECE
    ilgili şirketin sektörü hâlâ `None` ise gerçekten bir KAP isteği atar
    -- sektör ZATEN doluysa (büyük çoğunluk, rutin/tekrarlanan sorgular)
    HİÇBİR ağ isteği YAPILMAZ. `kap.fetch_sector_map()` TEK istekte TÜM
    BIST'i döndürdüğü için `repository.update_company_sectors()` bu ticker
    İLE BİRLİKTE DB'deki BAŞKA eksik şirketleri de fırsattan yararlanıp
    günceller (yan etki, zararsız). Kural 9: ikincil/yardımcı veri -- hata
    olursa (ağ/parse) SESSİZCE loglanıp atlanır, ana pipeline'ı BLOKE ETMEZ."""
    company = session.get(models.Company, ticker)
    if company is None or company.sector is not None:
        return
    try:
        sector_map = kap.fetch_sector_map()
        updated = repository.update_company_sectors(session, sector_map)
        logger.info("%s icin sektor senkronize edildi (%d sirket guncellendi).", ticker, updated)
    except Exception:
        logger.warning("%s icin sektor bilgisi guncellenemedi (ikincil veri, pipeline devam ediyor).", ticker, exc_info=True)


def _fetch_and_store(ticker: str, periods: list[Period] | None) -> None:
    """Is Yatirim + KAP'tan veri cekip DB'ye standart alanlarla yazar.

    Is Yatirim (finansal tablolar) ve KAP (sirket adi + bildirimler)
    birbirinden BAGIMSIZ ag istekleridir -- ayri is parcaciklarinda PARALEL
    calistirilarak toplam bekleme suresi kisaltilir (sirayla cekilseler
    ikisinin toplam suresi kadar surer; paralelde ikisinden YAVAS olaninin
    suresi kadar surer).

    Hatalar:
        TickerNotFoundError, UnsupportedCompanyTypeError,
        DataSourceUnavailableError, PeriodNotAvailableError
    """
    executor = ThreadPoolExecutor(max_workers=2)
    raw_future = executor.submit(_resolve_raw_financials, ticker, periods)
    kap_future = executor.submit(_fetch_kap_data, ticker)

    try:
        raw = raw_future.result()
    except isyatirim.CompanyNotFoundError as exc:
        executor.shutdown(wait=False)
        raise TickerNotFoundError(str(exc)) from exc
    except isyatirim.FinancialDataNotAvailableError as exc:
        # _resolve_raw_financials zaten bir ceyrek geriye kaymayi denedi ve
        # o da basarisiz oldu -- baska onerecek donem yok.
        executor.shutdown(wait=False)
        guessed = isyatirim.guess_last_periods(count=1)[0]
        raise PeriodNotAvailableError(ticker, quarter_label(guessed), None, None) from exc
    except isyatirim.IsYatirimNetworkError as exc:
        executor.shutdown(wait=False)
        raise DataSourceUnavailableError(str(exc)) from exc

    company_name, disclosures = kap_future.result()
    executor.shutdown(wait=True)

    if raw.financial_group not in ("XI_29", "UFRS", "UFRS_KATILIM", "UFRS_K", "XI_29K"):
        raise UnsupportedCompanyTypeError(
            f"'{ticker}' icin finansal tablo semasi ('{raw.financial_group}') henuz desteklenmiyor."
        )

    # KAP TAZELIK YAMASI (bkz. modul ust notu): Is Yatirim henuz islememis
    # olsa bile KAP'ta ZATEN yayinlanmis bir "Finansal Rapor" varsa, bu
    # TEK donemi ayrica cekip asagidaki "kullaniciya sor" kontrolunden ONCE
    # devreye sokariz -- boylece TATGD gibi bir durumda (Is Yatirim hala
    # eski ceyregi donduruyor ama KAP'ta yenisi zaten var) kullaniciya
    # gereksiz yere "eski donemi mi analiz edeyim?" SORULMAZ. XI_29/UFRS/
    # UFRS_K/XI_29K icin dogrulandi -- UFRS_KATILIM HENUZ desteklenmiyor
    # (bkz. kap_financials.py sinirlamasi).
    kap_patch_records: list[repository.FinancialRecord] = []
    kap_patch_period: Period | None = None
    if raw.financial_group == "XI_29" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_xi29(ticker, max(raw.periods), raw)
    elif raw.financial_group == "UFRS" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_ufrs(ticker, max(raw.periods), raw)
    elif raw.financial_group == "UFRS_K" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_ufrs_k(ticker, max(raw.periods), raw)
    elif raw.financial_group == "XI_29K" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_financing(ticker, max(raw.periods), raw)

    # Eger _resolve_raw_financials bir ceyrek geriye kaydirdiysa (periods
    # parametresi None olarak baslayip raw.periods'in en yenisi guess_last_periods'in
    # tahmininden eskiyse), kullaniciya sorulmasi gerekir -- burada render
    # YAPILMADAN once bunu tespit edip PeriodNotAvailableError firlatiyoruz.
    if periods is None:
        guessed_newest = isyatirim.guess_last_periods(count=1)[0]
        actual_newest = max(raw.periods) if raw.periods else None
        if kap_patch_period is not None and (actual_newest is None or kap_patch_period > actual_newest):
            actual_newest = kap_patch_period
        if actual_newest is not None and actual_newest < guessed_newest:
            retry_periods = [
                calculator.previous_quarter_period(p)
                for p in isyatirim.guess_last_periods(count=isyatirim.DEFAULT_HISTORY_QUARTERS)
            ]
            raise PeriodNotAvailableError(ticker, quarter_label(guessed_newest), quarter_label(actual_newest), retry_periods)

    if raw.financial_group == "XI_29":
        records = _standardize_to_records(raw)
    elif raw.financial_group == "UFRS":
        records = _standardize_to_records_ufrs(raw)
    elif raw.financial_group == "UFRS_KATILIM":
        records = _standardize_to_records_ufrs_katilim(raw)
    elif raw.financial_group == "XI_29K":
        records = _standardize_to_records_financing(raw)
    else:
        records = _standardize_to_records_ufrs_k(raw)
    records = records + kap_patch_records
    with repository.get_session() as session:
        # market="BIST" ACIKCA gecirilir (bkz. upsert_financials docstring'i,
        # Faz 10 NASDAQ hatasindan sonra eklendi) -- BIST tarafi zaten
        # varsayilan "BIST" ile ayni davranir, ama ayni koruma SIMETRIK
        # sekilde burada da GEÇERLI olsun diye (bir NASDAQ ticker'inin
        # yanlislikla BIST olarak sorulmasi durumunda da GURULTULU sekilde
        # reddedilsin) acikca yazildi.
        repository.upsert_financials(session, ticker, records, market="BIST")
        repository.set_company_info(session, ticker, name=company_name, financial_group=raw.financial_group)
        _ensure_sector_populated(session, ticker)

        if disclosures:
            disclosure_records = [(d.date, d.title, d.category, d.importance, d.url) for d in disclosures]
            repository.save_disclosures(session, ticker, disclosure_records)


def _get_or_generate_commentary(
    ticker: str, period: Period, fresh: bool, generate: Callable[[], commentary_module.Commentary]
) -> commentary_module.Commentary:
    """Yorum uretimini onbellekler -- bkz. repository.CommentaryCache modeli
    (Gemini ucretsiz katmaninin GUNLUK kota siniri var, canli dogrulandi:
    20 istek/gun/model -- bkz. Gemini'nin RESOURCE_EXHAUSTED yanitindaki
    'generate_content_free_tier_requests' kota ihlali). Finansal veri
    TAZEYSE (fresh=True, yeni fetch YAPILMADI) VE bu donem icin daha once
    uretilmis bir yorum VARSA, Gemini TEKRAR cagirilmaz -- ayni /son
    sorgusu, farkli kullanicinin ayni hisseyi sormasi gibi TEKRARLI
    isteklerde kota gereksiz tuketilmesin diye. Veri YENI cekildiyse
    (fresh=False) yorum HER ZAMAN yeniden uretilir ve onbellek guncellenir."""
    if fresh:
        with repository.get_session() as session:
            cached = repository.get_cached_commentary(session, ticker, period)
        if cached is not None:
            # 'hook' sutunu Faz 16.4'te eklendi (bkz. models._migrate_add_commentary_hook_column)
            # -- bu tarihten ONCE onbelleklenmis satirlarda None'dur. Boyle
            # bir durumda YENI bir Gemini cagrisi GEREKMEZ: positives'ten
            # (zaten onbellekte var) ayni sekilde yeniden kurulur (bkz.
            # commentary._fallback_commentary'deki AYNI ilke).
            hook = cached.hook or " ".join((cached.positives or [])[:2]) or cached.headline
            return commentary_module.Commentary(
                headline=cached.headline,
                hook=hook,
                summary=cached.summary,
                positives=list(cached.positives),
                negatives=list(cached.negatives),
                kap_note=cached.kap_note,
                disclaimer_context=None,
                source=cached.source,
            )

    yorum = generate()
    with repository.get_session() as session:
        repository.save_commentary(
            session, ticker, period, yorum.headline, yorum.hook, yorum.summary, yorum.positives, yorum.negatives,
            yorum.kap_note, yorum.source,
        )
    return yorum


def _fetch_price_safe(ticker: str) -> Decimal | None:
    """fetch_latest_price'i sarmalar; ag hatasinda None doner (fiyat
    supplementary veridir, boru hattini BLOKE ETMEMELI)."""
    try:
        return isyatirim.fetch_latest_price(ticker)
    except isyatirim.IsYatirimError as exc:
        logger.warning("%s icin fiyat cekilemedi (kart fiyatsiz gosterilecek): %s", ticker, exc)
        return None


def _fetch_price_safe_us(ticker: str) -> Decimal | None:
    """_fetch_price_safe()'in NASDAQ/ABD karsiligi -- sec_edgar.fetch_latest_price()
    zaten hicbir istisna FIRLATMAZ (bkz. docstring'i), bu sarmalayici SADECE
    diger fonksiyonla AYNI imzayi/loglama uslubunu korumak icin var."""
    price = sec_edgar.fetch_latest_price(ticker)
    if price is None:
        logger.warning("%s icin fiyat cekilemedi (kart fiyatsiz gosterilecek).", ticker)
    return price


def _fetch_and_store_us_gaap(ticker: str, periods: list[Period] | None) -> None:
    """NASDAQ/ABD (US_GAAP) sirketleri icin _fetch_and_store()'un karsiligi.

    BIST akisindan (KAP bildirimleri + KAP tazelik yamasi + donem-kaydirma/
    ileri-probe) BILEREK DAHA BASITTIR:
      - KAP bildirimleri (Turkiye'ye ozgu) icin ABD karsiligi 8-K haberleridir
        -- bu TAMAMEN BU FAZIN KAPSAMI DISINDA (gorev talimati: "acikca 'yok'
        olarak gec, uydurma yapma") -- run_pipeline() US_GAAP dalinda
        disclosures HER ZAMAN bos liste kullanir, burada hic CEKILMEZ.
      - Donem kaydirma/ileri-probe (bkz. _resolve_raw_financials,
        _find_true_newest_period) GEREKMEZ: sec_edgar.fetch_financials()
        SEC companyfacts'in TEK istekte TUM tarihceyi donmesi sayesinde HER
        ZAMAN net_income'dan turetilen GERCEKTEN en yeni donemi bulur (bkz.
        sec_edgar._discover_available_periods) -- Is Yatirim'daki "tahmin
        et, yanlissa kaydir/ileri probe et" mantigina GEREK YOK.

    Hatalar:
        TickerNotFoundError, FinancialDataNotFoundError (bkz. sinif
        docstring'i -- SKHY/SK hynix canli hatasi), DataSourceUnavailableError,
        repository.TickerMarketConflictError (BIST/NASDAQ sembol cakismasi
        -- bkz. repository.py docstring'i; BILEREK YUTULMAZ, cagiran tarafa
        GURULTULU sekilde iletilir, bkz. o sinifin "algila ve reddet"
        gerekcesi).
    """
    try:
        raw = sec_edgar.fetch_financials(ticker, periods=periods)
    except sec_edgar.CompanyNotFoundError as exc:
        raise TickerNotFoundError(str(exc)) from exc
    except sec_edgar.FinancialDataNotAvailableError as exc:
        raise FinancialDataNotFoundError(str(exc)) from exc
    except sec_edgar.SecEdgarNetworkError as exc:
        raise DataSourceUnavailableError(str(exc)) from exc

    records = _standardize_to_records_us_gaap(raw)
    with repository.get_session() as session:
        repository.upsert_financials(session, ticker, records, market="NASDAQ")
        repository.set_company_info(session, ticker, name=raw.company_name, financial_group="US_GAAP", market="NASDAQ")


def _closest_close(bars: list, target_date) -> "None | object":
    """`bars` (price_history.OhlcvBar listesi, artan tarih) içinde
    `target_date`'e EN YAKIN kapanışı döner -- tam o gün işlem olmayabilir
    (hafta sonu/tatil), bu yüzden en yakın GERÇEK işlem günü seçilir. Bars
    boşsa None döner (K4/Kural 9: yeterli veri yoksa None, uydurma yapılmaz)."""
    if not bars:
        return None
    closest = min(bars, key=lambda bar: abs((bar.trade_date - target_date).days))
    return closest.close


def compute_valuation_assessment_for_ticker(
    ticker: str,
    market: str,
    financial_group: str,
    financials_by_period: dict,
    peer_tickers: list[str],
    peer_financials_list: list[dict],
) -> "valuation.ValuationAssessment | None":
    """Değerleme Analizi paneli (sektör-göreli F/K-PD/DD karşılaştırması +
    kısa vadeli fiyat momentumu + Benjamin Graham/Peter Lynch ölçütleri)
    hesabını orkestre eder (bkz. src/analysis/valuation.py modül notu --
    HESAPLAMANIN KENDİSİ orada, saf matematik olarak yapılır). Hem Derin
    Kart (`telegram_bot._gonder_derin_analiz`) HEM tek çeyreklik Bilanço
    kartı (`run_pipeline` aşağıda) tarafından PAYLAŞILIR (Kural: hesaplama/
    orkestrasyon mantığı KOPYALANMAZ) -- telegram_bot.py bunu doğrudan
    `pipeline.compute_valuation_assessment_for_ticker(...)` ile çağırır.

    `peer_tickers` BOŞ olsa bile çağrılabilir -- Graham/PEG ölçütleri SEKTÖR
    PEER'İ GEREKTİRMEZ (bkz. valuation.py), sadece sektör-göreli kısım (F/K/
    PD-DD karşılaştırması, sektöre göre ima edilen değer) `peer_tickers`
    doluysa dolar. Bu fonksiyon SADECE `get_sector_peer_tickers()` ile
    bulunan gerçek peer'lerin GÜNCEL fiyatını (`price_history.fetch_ohlcv`,
    YENİ ama hafif/ikincil bir istek -- Kural 9: başarısız olursa SESSİZCE
    atlanır, kartın geri kalanını BLOKE ETMEZ) çeker; peer'ler HER ZAMAN
    BİST/XI_29'dur (sektör verisi SADECE BİST kapsar, bkz. 01_MIMARI.md §8)."""
    own_bars = price_history.fetch_ohlcv(ticker, market, days=100)
    if not own_bars:
        return None
    current_price = own_bars[-1].close
    price_30d_ago = _closest_close(own_bars, own_bars[-1].trade_date - timedelta(days=30))
    price_90d_ago = _closest_close(own_bars, own_bars[-1].trade_date - timedelta(days=90))

    if financial_group == "US_GAAP":
        own_analysis = calculator.analyze_us(ticker, financials_by_period)
        own_share_field = "shares_outstanding"
    else:
        own_analysis = calculator.analyze(ticker, financials_by_period)
        own_share_field = "share_capital"
    own_share_count = financials_by_period.get(own_analysis.latest_period, {}).get(own_share_field)
    own_metrics = calculator.compute_valuation(own_analysis, current_price, own_share_count)

    peer_multiples: list[valuation.PeerMultiple] = []
    for peer_ticker, peer_financials in zip(peer_tickers, peer_financials_list):
        if not peer_financials:
            continue
        peer_analysis = calculator.analyze(peer_ticker, peer_financials)
        peer_bars = price_history.fetch_ohlcv(peer_ticker, "BIST", days=15)
        peer_price = peer_bars[-1].close if peer_bars else None
        peer_share_capital = peer_financials.get(peer_analysis.latest_period, {}).get("share_capital")
        peer_metrics = calculator.compute_valuation(peer_analysis, peer_price, peer_share_capital)
        peer_multiples.append(
            valuation.PeerMultiple(
                ticker=peer_ticker,
                pe_ratio=peer_metrics.pe_ratio if peer_metrics else None,
                pb_ratio=peer_metrics.pb_ratio if peer_metrics else None,
            )
        )

    return valuation.compute_valuation_assessment(
        own_pe=own_metrics.pe_ratio if own_metrics else None,
        own_pb=own_metrics.pb_ratio if own_metrics else None,
        peer_multiples=peer_multiples,
        current_price=current_price,
        price_30d_ago=price_30d_ago,
        price_90d_ago=price_90d_ago,
        growth_rate_pct=own_analysis.ratios.revenue_growth_yoy_pct,
        # Faz 16.7 -- Damodaran istikrarlı büyüme FCFE modeli icin: TTM net
        # kâr + ROE (zaten hesaplanmış, calculator.Ratios) + pay adedi (yukarıda
        # own_metrics icin de kullanılan own_share_count) + para birimi (hangi
        # risksiz faiz/özkaynak risk primi setinin seçileceğini belirler).
        ttm_net_income=own_analysis.ratios.ttm_net_income,
        roe_pct=own_analysis.ratios.roe_annualized,
        share_capital=own_share_count,
        currency=own_analysis.currency,
    )


def _ensure_financials_cached(ticker: str, market: str, periods: list[Period] | None) -> bool:
    """DB onbelleginin TAZE olup olmadigini kontrol eder, degilse (veya
    `periods` acikca verilmisse) fetch tetikleyip DB'ye yazar. Cagiran
    tarafin (run_pipeline) yorum onbellegi icin ihtiyac duydugu `fresh`
    bilgisini (fetch GEREKMEDI mi) DONDURUR -- finansal veri sonucunun
    kendisi (`financials_by_period`) DONDURULMEZ, cagiran taraf bunu ayrica
    `repository.get_financials()` ile okur. `run_pipeline()` (asagida) VE
    `compute_fundamental_screens_for_ticker` tarafindan PAYLASILIR (Kural:
    onbellek/fetch orkestrasyon mantigi KOPYALANMAZ) -- mantigin KENDISI
    eskiden SADECE run_pipeline icindeydi, Faz 21'de (Değerleme ekrani,
    DOĞRUDAN -- önce bir Bilanço Analizi çalıştırılmış olma ÖN KOŞULU
    OLMADAN -- bir ticker sorgulayabilsin diye) buraya cikarildi."""
    is_us = market == "NASDAQ"
    with repository.get_session() as session:
        company_row = session.get(models.Company, ticker)
        # CANLI HATA (kullanici raporu, 2026-08-03): "AMD"/"ASTS" gibi HEM
        # BIST ticker regex'ine (3-6 harf) UYAN HEM DE daha once NASDAQ
        # olarak analiz edilip onbellege alinmis bir sembol, menusuz/
        # varsayilan bir aramada (market="BIST" varsayilaniyla) sorulunca --
        # is_data_fresh() SADECE ticker+last_updated'a bakip HANGI MARKET
        # icin taze oldugunu HIC KONTROL ETMEDIGI icin -- yanlislikla "taze"
        # sayiliyor VE (is_us=False oldugundan) BIST sablonuyla (analyze()/
        # build_card_context(), ₺ + "İş Yatırım, KAP" kaynagiyla) render
        # ediliyordu -- fiyat/degerleme basligi TAMAMEN kayboluyordu (BIST'in
        # compute_valuation'i US_GAAP kayitlarindaki "shares_outstanding"
        # yerine "share_capital" bekliyor, bulamayinca valuation None
        # kaliyor). Cozum: onbellekteki sirketin GERCEK market'i (varsa)
        # istenen market'ten FARKLIYSA onbellek bu istek icin GECERSIZ
        # sayilir (fresh=False) -- bu tam bir fetch'i tetikler, o da (ticker
        # o markette GERCEKTEN yoksa) TickerNotFoundError firlatir --
        # _execute_and_send'deki allow_market_fallback mekanizmasi bu sayede
        # DOGRU market'i (NASDAQ) dener (bkz. 06_BILINEN_SORUNLAR.md §B19).
        market_mismatch = company_row is not None and company_row.market != market
        fresh = (
            periods is None
            and not market_mismatch
            and repository.is_data_fresh(session, ticker, max_age_hours=12)
        )
        cached_newest = None
        cached_group = None
        if fresh:
            cached = repository.get_financials(session, ticker, n_periods=1)
            if cached:
                cached_newest = max(cached)
            cached_group = company_row.financial_group if company_row else None

    if not is_us and fresh and cached_newest is not None and cached_group:
        if _has_newer_period_available(ticker, cached_newest, cached_group):
            logger.info(
                "%s icin onbellek yas bakimindan taze ama daha yeni bir donem bulundu, tam fetch tetikleniyor.",
                ticker,
            )
            fresh = False

    if not fresh:
        if is_us:
            _fetch_and_store_us_gaap(ticker, periods)
        else:
            _fetch_and_store(ticker, periods)

    return fresh


def compute_fundamental_screens_for_ticker(ticker: str) -> FundamentalScreensResult:
    """Faz 21 "Değerleme" ekranı için Graham + Greenblatt Sihirli Formül +
    Carlisle Acquirer's Multiple + Piotroski F-Skoru hesabını orkestre eder
    (bkz. src/analysis/fundamental_screens.py modül notu -- HESAPLAMANIN
    KENDİSİ orada, saf matematik olarak yapılır). SEKTÖR PEER'İ HİÇ
    ÇEKMEZ/KULLANMAZ (kullanıcı isteği, 2026-08-05: "sektörel... gelmesin
    bi değer bu değerleme için" -- DB'de yeterli peer olmadan istatistiksel
    olarak anlamsız).

    `compute_valuation_assessment_for_ticker`'ın AKSİNE (o zaten fetch
    edilmiş `financials_by_period` bekler, çağıran taraf -- run_pipeline/
    Derin Kart -- ÖNCEDEN veri çekmiş OLMALIDIR) bu fonksiyon SADECE ticker
    alır ve DB'yi KENDİSİ tazeler (`_ensure_financials_cached`) -- kullanıcı
    Değerleme ekranına hiç Bilanço Analizi çalıştırmadan DOĞRUDAN bir ticker
    yazabilsin diye (kullanıcı isteği: "değerleme ekranında yazılan hisse
    için bu değerlemeleri hesaplayarak versin").

    Ticker DB'de/hiçbir kaynakta hiç bulunamazsa (gerçekten var olmayan bir
    kod) `TickerNotFoundError` FIRLAR (run_pipeline ile AYNI davranış,
    çağıran taraf -- telegram_bot._gonder_degerleme -- bunu kullanıcı dostu
    bir mesaja çevirir). Ticker BULUNUR ama BIST XI_29 (sanayi/ticaret)
    DIŞINDA bir grupsa (banka/sigorta/katılım bankası) -- Greenblatt'ın
    kendi metodolojisi farklı sermaye yapılı şirketleri BİLİNÇLİ dışladığı
    için (bkz. fundamental_screens.py üst notu) -- `FundamentalScreensResult.
    applicable=False` (`screens=None`) döner, hata FIRLATILMAZ (bu durum
    "veri yok" değil "bu yöntem bu şirket türüne uygulanamaz" anlamına
    gelir, ayırt edilebilir kalmalıdır)."""
    ticker = ticker.strip().upper()
    _ensure_financials_cached(ticker, "BIST", periods=None)

    with repository.get_session() as session:
        company_row = session.get(models.Company, ticker)
        financials_by_period = repository.get_financials(session, ticker, n_periods=8)
        company_name = company_row.name if company_row and company_row.name else None

    if not financials_by_period:
        raise TickerNotFoundError(f"'{ticker}' icin veritabaninda finansal veri bulunamadi.")

    if company_row is None or company_row.financial_group != "XI_29":
        return FundamentalScreensResult(ticker=ticker, company_name=company_name, price=None, applicable=False, screens=None)

    own_bars = price_history.fetch_ohlcv(ticker, "BIST", days=30)
    current_price = own_bars[-1].close if own_bars else None

    own_analysis = calculator.analyze(ticker, financials_by_period)
    own_share_count = financials_by_period.get(own_analysis.latest_period, {}).get("share_capital")
    own_metrics = calculator.compute_valuation(own_analysis, current_price, own_share_count)

    screens = fundamental_screens.compute_fundamental_screens(
        financials_by_period,
        price=current_price,
        share_capital=own_share_count,
        own_pe=own_metrics.pe_ratio if own_metrics else None,
        own_pb=own_metrics.pb_ratio if own_metrics else None,
    )
    return FundamentalScreensResult(
        ticker=ticker, company_name=company_name, price=current_price, applicable=True, screens=screens
    )


@dataclass(frozen=True)
class MultiLensScoreResult:
    """`compute_multi_lens_score_for_ticker()` çıktısı -- v2 çok-mercekli
    (Değer/Kalite/Büyüme/Güvenlik) skorlamanın TAMAMI (4 mercek + bileşik)
    burada taşınır. `bilesik.mercekler` (`lens_bilesik_skor.MercekProfili`)
    üzerinden 4 merceğin HER BİRİ ayrı ayrı de erişilebilir (spec_bilesik_
    skor.md: "kullanıcıya tek skor değil profil gösterilir").

    `valuation_metrics` (docs/spec/spec_dashboard.md §Girdiler): fonksiyon
    İÇİNDE zaten hesaplanan `calculator.ValuationMetrics`/`BankValuationMetrics`/
    `InsuranceValuationMetrics`/`FinancingValuationMetrics` nesnesi -- Faz 5
    ÖNCESİ sadece `deger` merceğinin girdisi olarak kullanılıp DIŞARI
    SIZMIYORDU; `scripts/tarama_toplu.py`'nin F/K, PD/DD, FD/FAVÖK, piyasa
    değeri gibi ana çarpanları HER ticker için AYRICA hesaplamak zorunda
    kalmaması (kod tekrarı, katman ihlali) için buraya taşındı (genişletme,
    mevcut alanlar KORUNDU -- persona kural 8).

    `template` (docs/spec/spec_dashboard.md §DB modeli, `MarketScanResult.
    template` sütunu): fonksiyon İÇİNDE zaten türetilen "sanayi"|"abd_sanayi"|
    "banka"|"sigorta"|"finansman" etiketi -- AYNI gerekçeyle (kod tekrarı
    önleme) dışarı taşındı. `LensSonucu.template` İLE KARIŞTIRILMAMALI: o
    alan mercek adını taşır ("değer"/"kalite_banka"/...), BU alan ise
    ŞİRKET TÜRÜ şablonunu taşır."""

    ticker: str
    market: str
    period: Period
    company_name: str | None
    price: Decimal | None
    bilesik: lens_bilesik_skor.BilesikSkorSonucu
    valuation_metrics: (
        calculator.ValuationMetrics
        | calculator.BankValuationMetrics
        | calculator.InsuranceValuationMetrics
        | calculator.FinancingValuationMetrics
        | None
    ) = None
    template: str | None = None


def _sektor_istatistigi_getir(
    ust_sektor: str | None, sirket_turu: str | None, metric: str, period: Period, exclude_ticker: str
) -> lens_common.SektorIstatistigi | None:
    """🚨 KÖK NEDEN DÜZELTMESİ (kod-geliştirici turu, 2026-08-12):
    `compute_multi_lens_score_for_ticker()` `lens_deger.DegerGirdisi(...)`
    çağırırken `sektor_pe`/`sektor_pb` parametreleri HİÇ GEÇİLMİYORDU --
    varsayılan `None` kaldığı için `lens_deger._skor_sektore_goreli()`
    (`sektor_pe is not None and sektor_pe.n >= MIN_SECTOR_N` koşulu)
    HİÇBİR ZAMAN geçemiyordu, "Sektöre Göreli Konum" bileşeni kaç peer
    taranmış olursa olsun DAİMA atlanıyordu. `SectorMetricCache` tablosu
    (models.py) VE `get_sector_metric_cache`/`save_sector_metric_cache`
    (repository.py) ZATEN vardı ama hiçbir yerden BESLENMİYORDU --
    `scripts/refresh_sector_cache.py` (Faz 16) BAŞKA bir işi yapar
    (`Company.sector`'ı KAP'tan günceller), bu tabloya HİÇ dokunmaz.

    Bu fonksiyon eksik halkayı tamamlar: önce `SectorMetricCache`'i
    (taze ise) okur; yoksa/eskiyse `repository.get_sector_metric_distribution()`
    ile `MarketScanResult`'tan (scripts/tarama_toplu.py'nin ZATEN doldurduğu
    tablo) ham F/K veya PD/DD dağılımını çeker, SADECE pozitif değerleri
    (own_pe>0 ile AYNI ilke -- negatif/zarar eden şirketler F/K
    karşılaştırmasında anlamsızdır) `lens_common.robust_istatistik()`'e
    verir, sonucu önbelleğe YAZAR ve döner. `ust_sektor`/`sirket_turu`
    NULL ise (taksonomi henüz bu ticker'ı işlemediyse) VEYA yeterli/pozitif
    peer verisi yoksa `None` döner -- HATA FIRLATILMAZ, `lens_deger`
    bileşeni zaten `None` girdiyle "yetersiz örneklem" olarak ATLAR (Kural:
    eksik veri = None yayılımı, sessizce 0 varsayılmaz)."""
    if not ust_sektor or not sirket_turu:
        return None
    with repository.get_session() as session:
        cached = repository.get_sector_metric_cache(session, ust_sektor, sirket_turu, metric, period)
        if cached is not None:
            return lens_common.SektorIstatistigi(n=cached.n, medyan=cached.medyan, mad=cached.mad)

        degerler = repository.get_sector_metric_distribution(session, ust_sektor, sirket_turu, metric, exclude_ticker=exclude_ticker)
        pozitif_degerler = [d for d in degerler if d > 0]
        sonuc = lens_common.robust_istatistik(pozitif_degerler)
        if sonuc is None:
            return None
        medyan, mad, n = sonuc
        repository.save_sector_metric_cache(session, ust_sektor, sirket_turu, metric, period, n=n, medyan=medyan, mad=mad)
        session.commit()
        return lens_common.SektorIstatistigi(n=n, medyan=medyan, mad=mad)


def compute_multi_lens_score_for_ticker(ticker: str, market: str = "BIST") -> MultiLensScoreResult:
    """v2 çok-mercekli skorlamayı (`docs/spec/spec_bilesik_skor.md`) BAĞIMSIZ
    bir giriş noktası olarak orkestre eder -- v1'in `run_pipeline()`/
    `scorer.score_industrial()` akışını HİÇ ÇAĞIRMAZ/ETKİLEMEZ (persona
    kural 8: "v1 davranışı ASLA değişmeyecek"). `src/bot/telegram_bot.py`
    henüz bu fonksiyonu ÇAĞIRMAZ (geçiş bayrağı `config`/çağıran taraf
    kararına bırakıldı, bkz. `scripts/demo_v2_skor.py`) -- bu fonksiyonun
    KENDİSİ zaten "bayrak" rolü görür: v1 ayrı, v2 ayrı, hiçbiri diğerini
    bozmaz.

    Desteklenen şablonlar: `sanayi` (BİST XI_29), `abd_sanayi` (NASDAQ
    US_GAAP), `banka` (UFRS konvansiyonel + UFRS_KATILIM katılım bankası),
    `sigorta` (UFRS_K), `finansman` (XI_29K Tasarruf Finansman Şirketleri)
    -- bu turda banka/sigorta/finansman DE eklendi (bkz. `docs/spec/
    spec_mercek_deger.md`/`spec_mercek_kalite.md`/`spec_mercek_buyume.md`/
    `spec_mercek_guvenlik.md` "Sektör ayarlaması" bölümleri): KALİTE
    merceği SADECE ROE+ROA'dan, GÜVENLİK merceği kaldıraç YERİNE özkaynak/
    aktif oranından (+ henüz kodlanmamış Piotroski-benzeri iskelet)
    oluşur, BÜYÜME merceğinde Hasılat Büyümesi bileşeni Prim/Kredi/
    Finansman Geliri büyümesiyle DEĞİŞTİRİLİR. Gerçekten HİÇ desteklenmeyen
    bir `financial_group` gelirse (yukarıdaki 5 türün dışında)
    `UnsupportedCompanyTypeError` AÇIKÇA fırlatılır, sessizce yanlış bir
    şablona DÜŞÜLMEZ (Kural 3)."""
    ticker = ticker.strip().upper()
    _ensure_financials_cached(ticker, market, periods=None)

    with repository.get_session() as session:
        company_row = session.get(models.Company, ticker)
        financials_by_period = repository.get_financials(session, ticker, n_periods=8)
        company_name = company_row.name if company_row and company_row.name else None
        financial_group = company_row.financial_group if company_row else None
        ust_sektor = company_row.ust_sektor if company_row else None
        sirket_turu = company_row.sirket_turu if company_row else None

    if not financials_by_period:
        raise TickerNotFoundError(f"'{ticker}' icin veritabaninda finansal veri bulunamadi.")

    is_us = market == "NASDAQ"
    if is_us:
        analysis = calculator.analyze_us(ticker, financials_by_period)
        template = "abd_sanayi"
        share_field = "shares_outstanding"
        currency = "USD"
    else:
        if financial_group not in (None, "XI_29", "UFRS", "UFRS_KATILIM", "UFRS_K", "XI_29K"):
            raise UnsupportedCompanyTypeError(
                f"'{ticker}' (financial_group={financial_group}) -- v2 çok-mercekli skorlama bu şirket türü "
                "için henüz kodlanmadı (spec'lerde tanımlı değil)."
            )
        share_field = "share_capital"
        currency = "TRY"
        if financial_group in ("UFRS", "UFRS_KATILIM"):
            bank_variant = "participation" if financial_group == "UFRS_KATILIM" else "conventional"
            analysis = calculator.analyze_bank(ticker, financials_by_period, bank_variant=bank_variant)
            template = "banka"
        elif financial_group == "UFRS_K":
            analysis = calculator.analyze_insurance(ticker, financials_by_period)
            template = "sigorta"
        elif financial_group == "XI_29K":
            analysis = calculator.analyze_financing(ticker, financials_by_period)
            template = "finansman"
        else:
            analysis = calculator.analyze(ticker, financials_by_period)
            template = "sanayi"

    own_bars = price_history.fetch_ohlcv(ticker, market, days=400)
    current_price = own_bars[-1].close if own_bars else None
    latest_raw = financials_by_period.get(analysis.latest_period, {})
    share_capital = latest_raw.get(share_field)
    if template == "banka":
        valuation_metrics = calculator.compute_valuation_bank(analysis, current_price, share_capital)
    elif template == "sigorta":
        valuation_metrics = calculator.compute_valuation_insurance(analysis, current_price, share_capital)
    elif template == "finansman":
        valuation_metrics = calculator.compute_valuation_financing(analysis, current_price, share_capital)
    else:
        valuation_metrics = calculator.compute_valuation(analysis, current_price, share_capital)

    fundamental = None
    if not is_us and financial_group == "XI_29":
        # Greenblatt/Carlisle/Graham/Piotroski SADECE BIST XI_29 sanayi icin
        # mevcut (fundamental_screens.py kapsam siniri, bkz. o modulun ust notu)
        # -- banka/sigorta/finansman'da `fundamental` BILINCLI olarak None
        # kalir (v1 deseniyle TUTARLI, bkz. run_pipeline()'in ayni kosulu).
        fundamental = fundamental_screens.compute_fundamental_screens(
            financials_by_period,
            price=current_price,
            share_capital=share_capital,
            own_pe=valuation_metrics.pe_ratio if valuation_metrics else None,
            own_pb=valuation_metrics.pb_ratio if valuation_metrics else None,
        )

    risk_free_rate_pct = valuation._RISK_FREE_RATE_PCT.get(currency)

    sektor_pe = _sektor_istatistigi_getir(ust_sektor, sirket_turu, "pe_ratio", analysis.latest_period, ticker)
    sektor_pb = _sektor_istatistigi_getir(ust_sektor, sirket_turu, "pb_ratio", analysis.latest_period, ticker)

    deger = lens_deger.hesapla_deger_mercegi(
        lens_deger.DegerGirdisi(
            analysis=analysis, valuation=valuation_metrics, fundamental=fundamental,
            risk_free_rate_pct=risk_free_rate_pct, sektor_pe=sektor_pe, sektor_pb=sektor_pb, template=template,
        )
    )

    if template in ("sanayi", "abd_sanayi"):
        ocf_ttm = calculator.trailing_12m_from_cumulative(
            financials_by_period, analysis.latest_period, lambda d: d.get("operating_cash_flow_cum")
        )
        kalite = lens_kalite.hesapla_kalite_mercegi(
            lens_kalite.KaliteGirdisi(
                analysis=analysis, greenblatt=fundamental.greenblatt if fundamental else None,
                operating_cash_flow_ttm=ocf_ttm, treasury_stock=latest_raw.get("treasury_stock"), template=template,
            )
        )
    else:
        # spec_mercek_kalite.md §Sektör ayarlaması madde 1: banka/sigorta/
        # finansman'da KALİTE merceği SADECE ROE+ROA'dan oluşur. Sigorta
        # (UFRS_K) şemasında `total_assets` HİÇ YOK (bkz. isyatirim.py
        # STANDARD_ITEM_MAP_UFRS_K) -- ROA orada HER ZAMAN None'dır, `return_
        # on_assets_annualized` alanı zaten InsuranceRatios'ta hiç TANIMLI
        # DEĞİL (`getattr` ile güvenle None'a düşer).
        roa_pct = getattr(analysis.ratios, "return_on_assets_annualized", None)
        kalite = lens_kalite.hesapla_kalite_mercegi_banka(
            ticker, analysis.latest_period, roe_pct=analysis.ratios.roe_annualized, roa_pct=roa_pct, template=template,
        )

    if template in ("sanayi", "abd_sanayi"):
        buyume = lens_buyume.hesapla_buyume_mercegi(
            lens_buyume.BuyumeGirdisi(
                analysis=analysis, financials_by_period=financials_by_period,
                own_pe=valuation_metrics.pe_ratio if valuation_metrics else None,
                enflasyon_yoy_pct=None, template=template,
            )
        )
    else:
        # spec_mercek_buyume.md §Sektör ayarlaması madde 3: Hasılat Büyümesi
        # bileşeni Prim Büyümesi (sigorta, zaten `InsuranceRatios.
        # premium_growth_yoy_pct` MEVCUT) veya kredi büyümesi (banka, ham
        # `loans` alanından TÜRETİLİR) veya finansman geliri büyümesi
        # (finansman, ham `financing_revenue` alanından TÜRETİLİR) ile
        # DEĞİŞTİRİLİR -- calculator.classify_change() ile TEK satır
        # türetim (BankRatios/FinancingRatios DEĞİŞTİRİLMEDEN, ham fbp +
        # aritmetik deseni, bkz. spec_mercek_guvenlik.md'nin Toplam
        # Yükümlülük/Özkaynak bileşeniyle AYNI ilke).
        if template == "sigorta":
            buyume_orani_pct = analysis.ratios.premium_growth_yoy_pct
            buyume_metrik_adi = "prim"
        else:
            yoy_raw = financials_by_period.get(calculator.year_ago_period(analysis.latest_period), {})
            if template == "banka":
                buyume_orani_pct, _label, _direction = calculator.classify_change(latest_raw.get("loans"), yoy_raw.get("loans"))
                buyume_metrik_adi = "kredi"
            else:  # "finansman"
                buyume_orani_pct, _label, _direction = calculator.classify_change(
                    latest_raw.get("financing_revenue"), yoy_raw.get("financing_revenue")
                )
                buyume_metrik_adi = "finansman geliri"
        buyume = lens_buyume.hesapla_buyume_mercegi_finans(
            lens_buyume.BuyumeGirdisiFinans(
                analysis=analysis, financials_by_period=financials_by_period, template=template,
                buyume_orani_pct=buyume_orani_pct, buyume_metrik_adi=buyume_metrik_adi,
                own_pe=valuation_metrics.pe_ratio if valuation_metrics else None, enflasyon_yoy_pct=None,
            )
        )

    if template in ("sanayi", "abd_sanayi"):
        merton_result = None
        short_term_liabilities = latest_raw.get("short_term_liabilities")
        long_term_financial_debt = latest_raw.get("long_term_financial_debt")
        if (
            current_price is not None
            and share_capital is not None
            and short_term_liabilities is not None
            and risk_free_rate_pct is not None
            and len(own_bars) >= 120
        ):
            # KMV "temerrut noktasi" (merton.compute_merton_dd_edf docstring'i):
            # kisa_vadeli_yukumlulukler + 0,5 x uzun_vadeli_finansal_borc.
            debt_face_value = short_term_liabilities + (Decimal("0.5") * long_term_financial_debt if long_term_financial_debt is not None else Decimal(0))
            equity_market_value = current_price * share_capital
            equity_volatility_pct = merton_module.annualized_equity_volatility([bar.close for bar in own_bars])
            if equity_volatility_pct is not None and debt_face_value > 0:
                merton_result = merton_module.compute_merton_dd_edf(
                    equity_market_value, debt_face_value, equity_volatility_pct, risk_free_rate_pct
                )

        guvenlik = lens_guvenlik.hesapla_guvenlik_mercegi(
            lens_guvenlik.GuvenlikGirdisi(
                analysis=analysis, financials_by_period=financials_by_period,
                piotroski=fundamental.piotroski if fundamental else None, merton=merton_result, template=template,
            )
        )
    else:
        # spec_mercek_guvenlik.md §Sektör ayarlaması madde 1: Kaldıraç/
        # Toplam Yükümlülük-Özkaynak KAVRAMSAL OLARAK UYGULANAMAZ -- SADECE
        # özkaynak/aktif oranı (+ henüz kodlanmamış Piotroski-benzeri
        # iskelet, piotroski=None). Sigorta'da bu oran da None'dır (ham
        # `total_assets` UFRS_K şemasında hiç yok) -- mercek dürüstçe
        # "YETERSİZ VERİ" döner (Kural 3, uydurma yapılmaz).
        ozkaynak_aktif_orani_pct = getattr(analysis.ratios, "equity_to_assets_current", None)
        guvenlik = lens_guvenlik.hesapla_guvenlik_mercegi_finans(
            ticker, analysis.latest_period, ozkaynak_aktif_orani_pct=ozkaynak_aktif_orani_pct, piotroski=None,
        )

    bilesik = lens_bilesik_skor.hesapla_bilesik_skor(ticker, analysis.latest_period, deger, kalite, buyume, guvenlik)
    return MultiLensScoreResult(
        ticker=ticker, market=market, period=analysis.latest_period, company_name=company_name,
        price=current_price, bilesik=bilesik, valuation_metrics=valuation_metrics, template=template,
    )


def run_pipeline(ticker: str, *, periods: list[Period] | None = None, market: str = "BIST") -> PipelineResult:
    """Tam boru hattini calistirir: onbellek -> (gerekirse) fetch -> hesapla
    -> puanla -> yorum -> kart. SENKRON'dur (fetcher'lar/Playwright sync
    calisir) -- Telegram bot tarafinda `asyncio.to_thread(run_pipeline, ...)`
    ile cagrilmalidir.

    `periods` verilirse onbellek TAZE olsa bile fetch zorlanir (kullanici
    "onceki donemi analiz et" dedikten sonraki tekrar cagri icin).

    `market`: "BIST" (varsayilan, davranis TAMAMEN DEGISMEDI -- mevcut
    Telegram botu/399 BIST testi bu parametreyi HIC vermez) veya "NASDAQ"
    (Faz 10 -- bkz. sec_edgar.py/calculator.analyze_us()/scorer.score_industrial_us()/
    card.build_us_card_context()). Hangi ticker'in hangi market'e ait
    oldugunu run_pipeline KENDI TAHMIN ETMEZ -- cagiran taraf (bot/demo
    script) ACIKCA belirtmelidir; bu, İş Yatırım'a "AAPL" gibi var olmayan
    bir kod sorup CompanyNotFoundError almak yerine (veya tam tersi, SEC'e
    "THYAO" sorup CompanyNotFoundError almak yerine) DOGRU fetcher'in
    BASTAN secilmesini saglar (Kural 3 ruhu: varsayimla/deneme-yanilma ile
    DEGIL, ACIK bilgiyle davran).

    NASDAQ dalinda KAP bildirimleri (`disclosures_db`) HER ZAMAN bos liste
    -- ABD'nin KAP karsiligi (SEC 8-K haberleri) BU FAZIN KAPSAMI DISINDA
    (gorev talimati). `_has_newer_period_available()` (İş Yatırım'a ozel
    "taze onbellek ama yeni donem yayinlanmis olabilir" kontrolu) SADECE
    BIST icin cagrilir -- sec_edgar.fetch_financials() zaten HER seferinde
    GERCEKTEN en yeni donemi bulur (bkz. _fetch_and_store_us_gaap docstring'i),
    bu ekstra kontrole GEREK YOK.

    Fiyat cekme (isyatirim.fetch_latest_price / sec_edgar.fetch_latest_price),
    finansal tablo fetch/onbellek islemleriyle BAGIMSIZ oldugu icin en basta
    ayri bir is parcacigina verilir ve sonucu en son (kart context'i
    olusturulmadan hemen once) toplanir -- boylece fiyat istegi diger
    islerle AYNI ANDA surer, ek bekleme suresi eklemez.
    """
    ticker = ticker.strip().upper()
    is_us = market == "NASDAQ"
    price_executor = ThreadPoolExecutor(max_workers=1)
    price_future = price_executor.submit(_fetch_price_safe_us if is_us else _fetch_price_safe, ticker)

    try:
        fresh = _ensure_financials_cached(ticker, market, periods)
    except Exception:
        price_executor.shutdown(wait=False)
        raise

    with repository.get_session() as session:
        financials_by_period = repository.get_financials(session, ticker, n_periods=8)
        disclosures_db = [] if is_us else repository.get_recent_disclosures(session, ticker, days=config.KAP_LOOKBACK_DAYS)
        company = session.get(models.Company, ticker)
        # Bilanço kartındaki kompakt Değerleme Analizi bileşeni (2026-08-04
        # kullanıcı isteği) için sektör peer'leri -- SADECE BIST'te (sektör
        # verisi başka hiçbir markette YOK, bkz. 01_MIMARI.md §8) VE
        # Company.sector doluysa (bkz. repository.get_sector_peer_tickers
        # docstring'i) anlamlıdır. Peer'in tek bir dönemi yeterli (n_periods=1)
        # -- burada peer'in KENDİ trend'i değil, SADECE güncel F/K-PD/DD'si
        # için share_capital/net_income/equity gerekir (bkz.
        # compute_valuation_assessment_for_ticker).
        peer_tickers: list[str] = []
        peer_financials_list: list[dict] = []
        if not is_us and company and company.sector:
            peer_tickers = repository.get_sector_peer_tickers(
                session, company.sector, company.financial_group, exclude_ticker=ticker
            )
            peer_financials_list = [repository.get_financials(session, peer, n_periods=1) for peer in peer_tickers]

    if not financials_by_period:
        price_executor.shutdown(wait=False)
        raise TickerNotFoundError(f"'{ticker}' icin veritabaninda finansal veri bulunamadi.")

    company_name = company.name if company and company.name else ticker
    sector = company.sector if company else None
    is_bank = bool(company and company.financial_group in ("UFRS", "UFRS_KATILIM"))
    is_participation_bank = bool(company and company.financial_group == "UFRS_KATILIM")
    is_insurance = bool(company and company.financial_group == "UFRS_K")
    is_financing = bool(company and company.financial_group == "XI_29K")

    price = price_future.result()
    price_executor.shutdown(wait=True)

    # Bilanço kartındaki kompakt Değerleme Analizi bileşeni (2026-08-04
    # kullanıcı isteği) -- SADECE XI_29 (sanayi) ve US_GAAP kartlarına
    # eklendi (Derin Kart'ın da SADECE bu ikisini desteklediği emsaliyle
    # tutarlı, bkz. _DERIN_ANALIZ_DESTEKLENEN_GRUPLAR); banka/sigorta bir
    # SONRAKİ adıma bırakıldı. Fiyat/eş şirket verisi İKİNCİL olduğu için
    # (Kural 9) herhangi bir hata bu bloğu SESSİZCE atlar, kartın geri
    # kalanı bundan ETKİLENMEZ.
    valuation_assessment = None
    if is_us or not (is_bank or is_insurance or is_financing):
        financial_group = "US_GAAP" if is_us else (company.financial_group if company else None)
        try:
            valuation_assessment = compute_valuation_assessment_for_ticker(
                ticker, market, financial_group, financials_by_period, peer_tickers, peer_financials_list
            )
        except Exception:
            logger.warning("%s için Değerleme Analizi paneli hesaplanamadı, panel gizlenecek.", ticker, exc_info=True)

    if is_us:
        # bkz. _standardize_to_records_us_gaap() ici not (§B20) -- SADECE
        # calculator.analyze_us()'in kendi standart TTM FAVOK turetmesi
        # basarisiz olursa kullanilan bir YEDEK (AMD/TSLA gibi D&A'nin bir
        # bileseni hic ceyreklik/YTD kirilimi olmayan sirketler icin).
        latest_period_for_ttm = max(financials_by_period.keys())
        ttm_da_override = financials_by_period.get(latest_period_for_ttm, {}).get("depreciation_amortization_ttm")
        analysis = calculator.analyze_us(
            ticker, financials_by_period, ttm_depreciation_amortization_override=ttm_da_override
        )
        shares_outstanding = financials_by_period.get(analysis.latest_period, {}).get("shares_outstanding")
        valuation = calculator.compute_valuation(analysis, price, shares_outstanding)
        valuation_input = (
            scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
            if valuation is not None
            else None
        )
        score = scorer.score_industrial_us(analysis, valuation=valuation_input)
        yorum = _get_or_generate_commentary(
            ticker, analysis.latest_period, fresh,
            lambda: commentary_module.generate_commentary(analysis, score, disclosures_db),
        )
        context = card.build_us_card_context(
            analysis,
            score,
            yorum,
            disclosures_db,
            company_name=company_name,
            sector=sector,
            price=price,
            valuation=valuation,
            valuation_assessment=valuation_assessment,
            now=datetime.now(),
        )
    elif is_bank:
        bank_variant = "participation" if is_participation_bank else "conventional"
        analysis = calculator.analyze_bank(ticker, financials_by_period, bank_variant=bank_variant)
        share_capital = financials_by_period.get(analysis.latest_period, {}).get("share_capital")
        valuation = calculator.compute_valuation_bank(analysis, price, share_capital)
        valuation_input = (
            scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
            if valuation is not None
            else None
        )
        score = scorer.score_bank(
            analysis,
            valuation=valuation_input,
            net_faiz_marji_pct=analysis.ratios.net_interest_margin_current,
            net_faiz_marji_degisim_puan=analysis.ratios.net_interest_margin_change_points,
            aktif_karliligi_pct=analysis.ratios.return_on_assets_annualized,
            aktif_karliligi_degisim_puan=analysis.ratios.return_on_assets_change_points,
            ozkaynak_aktif_orani_pct=analysis.ratios.equity_to_assets_current,
        )
        yorum = _get_or_generate_commentary(
            ticker, analysis.latest_period, fresh,
            lambda: commentary_module.generate_commentary_bank(analysis, score, disclosures_db),
        )
        context = card.build_bank_card_context(
            analysis,
            score,
            yorum,
            disclosures_db,
            company_name=company_name,
            sector=sector,
            price=price,
            valuation=valuation,
            now=datetime.now(),
        )
    elif is_insurance:
        analysis = calculator.analyze_insurance(ticker, financials_by_period)
        share_capital = financials_by_period.get(analysis.latest_period, {}).get("share_capital")
        valuation = calculator.compute_valuation_insurance(analysis, price, share_capital)
        valuation_input = (
            scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
            if valuation is not None
            else None
        )
        score = scorer.score_insurance(
            analysis,
            valuation=valuation_input,
            prim_buyumesi_yoy_pct=analysis.ratios.premium_growth_yoy_pct,
            teknik_denge_marji_pct=analysis.ratios.technical_balance_margin_current,
            teknik_denge_marji_degisim_puan=analysis.ratios.technical_balance_margin_change_points,
        )
        yorum = _get_or_generate_commentary(
            ticker, analysis.latest_period, fresh,
            lambda: commentary_module.generate_commentary_insurance(analysis, score, disclosures_db),
        )
        context = card.build_insurance_card_context(
            analysis,
            score,
            yorum,
            disclosures_db,
            company_name=company_name,
            sector=sector,
            price=price,
            valuation=valuation,
            now=datetime.now(),
        )
    elif is_financing:
        analysis = calculator.analyze_financing(ticker, financials_by_period)
        share_capital = financials_by_period.get(analysis.latest_period, {}).get("share_capital")
        valuation = calculator.compute_valuation_financing(analysis, price, share_capital)
        valuation_input = (
            scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
            if valuation is not None
            else None
        )
        score = scorer.score_financing(analysis, valuation=valuation_input)
        yorum = _get_or_generate_commentary(
            ticker, analysis.latest_period, fresh,
            lambda: commentary_module.generate_commentary_financing(analysis, score, disclosures_db),
        )
        context = card.build_financing_card_context(
            analysis,
            score,
            yorum,
            disclosures_db,
            company_name=company_name,
            sector=sector,
            price=price,
            valuation=valuation,
            now=datetime.now(),
        )
    else:
        analysis = calculator.analyze(ticker, financials_by_period)
        share_capital = financials_by_period.get(analysis.latest_period, {}).get("share_capital")
        valuation = calculator.compute_valuation(analysis, price, share_capital)
        valuation_input = (
            scorer.ValuationInput(pe_ratio=valuation.pe_ratio, pb_ratio=valuation.pb_ratio)
            if valuation is not None
            else None
        )
        score = scorer.score_industrial(analysis, valuation=valuation_input)
        yorum = _get_or_generate_commentary(
            ticker, analysis.latest_period, fresh,
            lambda: commentary_module.generate_commentary(analysis, score, disclosures_db),
        )
        context = card.build_card_context(
            analysis,
            score,
            yorum,
            disclosures_db,
            company_name=company_name,
            sector=sector,
            price=price,
            valuation=valuation,
            valuation_assessment=valuation_assessment,
            now=datetime.now(),
        )

    out_path = config.DATA_DIR / "cards" / f"{ticker}_{analysis.latest_period[0]}Q{analysis.latest_period[1]}.png"
    png_path = card.render_card(context, str(out_path))

    with repository.get_session() as session:
        repository.save_generated_card(session, ticker, png_path, float(score.total_score))

    return PipelineResult(
        ticker=ticker, analysis=analysis, score=score, commentary=yorum,
        png_path=png_path, company_name=company_name, sector=sector, price=price,
    )


# --- Faz 13: Yaklaşan Bilanço Tarihleri orkestrasyonu -----------------------------------------------------
#
# earnings_calendar.py (Faz 12) SADECE canlı hesaplama fonksiyonlarını verir
# (fetch_upcoming_bist/nasdaq) -- DB'ye YAZMAZ (katman kuralı: fetchers
# repository'yi bilmez). Bu iki fonksiyon o boşluğu dolduran orkestrasyondur
# (tıpkı run_pipeline'ın Is Yatirim/KAP + repository'yi birleştirmesi gibi).
#
# ⚠️ KRİTİK TASARIM KARARI: refresh_earnings_calendar(market="BIST") ticker
# başına 1-4 KAP isteği (+ nezaket bekletmesi) yapar -- BIST100 yaklaşımı
# (limit=100) için bu GERÇEKÇİ OLARAK BİRKAÇ DAKİKA sürer (bkz.
# scripts/demo_takvim.py docstring'i: 15 ticker için "birkaç dakika").
# Bu yüzden Telegram bot (/takvim, menu:takvim:*) BU fonksiyonu ASLA
# doğrudan/senkron çağırmaz -- kullanıcı isteğine göre canlı 100 şirket
# taraması, "ana boru hattını bloklamaz" ilkesini (bkz. CLAUDE.md kural 9)
# açıkça ihlal ederdi. Bunun yerine bot SADECE get_cached_earnings_calendar()
# ile DB önbelleğini okur; önbelleğin kendisi ayrı, zamanlanmış bir süreçle
# (bkz. scripts/refresh_takvim_cache.py, cron/Görev Zamanlayıcı ile günde
# 1-2 kez çalıştırılması ÖNERİLİR) doldurulur.


# CANLI hata (kullanıcı raporu, 2026-08-02 -- bkz. 06_BILINEN_SORUNLAR.md §B16):
# 100 BIST şirketini TEK seferde (~15 dakikada, yüzlerce KAP isteği) taramak
# KAP'ın TÜM isteklerimizi (ilgili şirketten BAĞIMSIZ) geçici olarak
# `RemoteProtocolError: Server disconnected without sending a response` ile
# düşürmesine sebep oldu -- AKBNK/GARAN/YKBNK/TOASO gibi devasa şirketler
# bile bu yüzden takvimden DÜŞTÜ. Bu yüzden BIST taraması artık küçük
# PARÇALAR (`batch_size`) halinde yapılır, parçalar arasında `batch_pause_seconds`
# beklenir -- toplam süre uzar (100 şirket için ~25-30 dakika) ama KAP'a
# "nezaket" göstererek bloklanma riski azaltılır.
_BIST_BATCH_SIZE = 20
_BIST_BATCH_PAUSE_SECONDS = 15.0


def refresh_earnings_calendar(
    market: str,
    *,
    bist_limit: int = 100,
    days_ahead: int = 45,
    batch_size: int = _BIST_BATCH_SIZE,
    batch_pause_seconds: float = _BIST_BATCH_PAUSE_SECONDS,
) -> int:
    """`market` ("BIST" | "NASDAQ") için canlı takvim verisini çeker ve
    DB önbelleğine (earnings_calendar tablosu) yazar. Dönen değer:
    upsert edilen (eklenen+güncellenen) satır sayısı.

    `days_ahead=45` (bot tarafının varsayılan gösterim penceresi olan 30
    günden GENİŞ) BİLEREK seçildi: refresh periyodik (örn. günde 1 kez)
    çalıştığı için önbellek bir SONRAKİ refresh'e kadar (en kötü ~24-48
    saat) kullanılacak -- pencere görüntüleme anındaki 30 güne TAM
    eşit olsaydı, refresh'ten birkaç gün sonra sorgulanan bir tarih
    (görüntüleme anında hâlâ "yakında" olan ama refresh anında 30 günün
    dışında kaldığı için hiç ÇEKİLMEMİŞ bir tarih) sessizce eksik kalırdı.

    `batch_size`/`batch_pause_seconds`: SADECE BIST için geçerli (NASDAQ
    per-gün tek bir istekle TÜM piyasayı döndürüyor, ticker başına istek
    YOK -- bkz. fetch_upcoming_nasdaq modül notu). BIST tarafında ise
    `symbols` listesi bu boyuttaki parçalara bölünür, her parça ayrı ayrı
    `fetch_upcoming_bist()`'e verilir (bkz. yukarıdaki CANLI hata notu)."""
    if market == "NASDAQ":
        entries = earnings_calendar.fetch_upcoming_nasdaq(days_ahead=days_ahead)
        candidate_count = len(entries)
    else:
        symbols = earnings_calendar.get_bist_top_market_cap_tickers(limit=bist_limit)
        candidate_count = len(symbols)
        entries = []
        for batch_start in range(0, len(symbols), batch_size):
            batch_symbols = symbols[batch_start : batch_start + batch_size]
            ticker_pairs: list[tuple[str, str]] = []
            for symbol in batch_symbols:
                try:
                    company = kap.search_company(symbol)
                    name = company.name
                except kap.KapError:
                    name = symbol
                ticker_pairs.append((symbol, name))
            entries.extend(earnings_calendar.fetch_upcoming_bist(ticker_pairs, days_ahead=days_ahead))

            taranan = batch_start + len(batch_symbols)
            is_last_batch = taranan >= len(symbols)
            if not is_last_batch:
                logger.info(
                    "BIST takvim taraması: %s/%s şirket tarandı, KAP'a nezaketen %.0f sn bekleniyor",
                    taranan, len(symbols), batch_pause_seconds,
                )
                time.sleep(batch_pause_seconds)

    records = [
        (e.ticker, e.market, e.company_name, e.period[0], e.period[1], e.expected_date, e.confidence, e.source)
        for e in entries
    ]
    with repository.get_session() as session:
        count = repository.upsert_earnings_calendar(session, records)
    logger.info(
        "%s takvim önbelleği güncellendi: %s kayıt (%s aday tarandı, %s eşleşme bulundu)",
        market, count, candidate_count, len(entries),
    )
    return count


def get_cached_earnings_calendar(
    market: str, days_ahead: int = 30, today: date | None = None
) -> list[earnings_calendar.EarningsDate]:
    """DB önbelleğinden (repository.get_upcoming_earnings) okur ve
    EarningsDate listesine geri çevirir -- bkz. yukarıdaki modül notu:
    bu fonksiyon ASLA canlı bir KAP/NASDAQ isteği yapmaz, sadece en son
    refresh_earnings_calendar() koşumunun sonucunu okur."""
    with repository.get_session() as session:
        rows = repository.get_upcoming_earnings(session, market, days_ahead=days_ahead, today=today)
    return [
        earnings_calendar.EarningsDate(
            ticker=row.ticker,
            company_name=row.company_name,
            market=row.market,
            period=(row.year, row.period),
            expected_date=row.expected_date,
            confidence=row.confidence,
            source=row.source,
        )
        for row in rows
    ]


def is_earnings_calendar_fresh(market: str, max_age_hours: int = 24) -> bool:
    """scripts/refresh_takvim_cache.py'nin bu marketi ne zamandır
    güncellemediğini kontrol eder -- bot tarafı bunu SADECE kullanıcıya
    "veriler ne kadar güncel" bilgisini göstermek için kullanır, refresh'i
    TETİKLEMEZ (bkz. yukarıdaki modül notu)."""
    with repository.get_session() as session:
        return repository.is_earnings_calendar_fresh(session, market, max_age_hours=max_age_hours)
