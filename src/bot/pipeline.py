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
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

import config
from src.ai import commentary as commentary_module
from src.analysis import calculator, scorer
from src.db import models, repository
from src.fetchers import isyatirim, kap, kap_financials, sec_edgar
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
)
_STOCK_FIELDS: tuple[str, ...] = (
    "total_assets",
    "current_assets",
    "trade_receivables",
    "equity",
    "cash",
    "financial_investments",
    "short_term_liabilities",
    "share_capital",
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
)
_US_GAAP_STOCK_FIELDS: tuple[str, ...] = (
    "total_assets",
    "current_assets",
    "short_term_liabilities",
    "trade_receivables",
    "equity",
    "cash",
    "shares_outstanding",
)


class PipelineError(Exception):
    """Boru hatti icin taban hata sinifi."""


class TickerNotFoundError(PipelineError):
    """Hisse kodu Is Yatirim'da bulunamadi."""


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
    analysis: calculator.AnalysisResult | calculator.BankAnalysisResult | calculator.InsuranceAnalysisResult
    score: scorer.ScoreResult
    commentary: commentary_module.Commentary
    png_path: str
    company_name: str
    sector: str | None


def quarter_label(period: Period) -> str:
    year, quarter = period
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
    cekirdegini kullanir)."""
    records: list[repository.FinancialRecord] = []
    for period in raw.periods:
        for field in _US_GAAP_QUARTERLY_FIELDS:
            if field == "gross_profit":
                # bkz. sec_edgar.gross_profit_us_gaap() docstring'i: dogrudan
                # "GrossProfit" tag'i (AAPL/NVDA/MSFT/TSLA/AMD) yoksa Hasilat -
                # Satislarin Maliyeti turetilir (GOOGL/AMZN/META/NFLX --
                # stockanalysis.com ile BIREBIR dogrulandi, PYPL'de HALA None).
                value = sec_edgar.quarterly_gross_profit_us_gaap(raw, period)
                cum_value = sec_edgar.gross_profit_us_gaap(raw, period)
            else:
                value = sec_edgar.quarterly_standardized_value_us_gaap(raw, field, period)
                cum_value = sec_edgar.standardized_value_us_gaap(raw, field, period)

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
    except isyatirim.FinancialDataNotAvailableError:
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

    if financial_group not in ("XI_29", "UFRS"):
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
        shifted = [calculator.previous_quarter_period(p) for p in isyatirim.guess_last_periods(count=8)]
        logger.info("%s icin en guncel donem henuz yok, bir ceyrek geriye kayarak deneniyor.", ticker)
        return isyatirim.fetch_financials(ticker, periods=shifted)

    guessed_newest = max(raw.periods)
    true_newest = _find_true_newest_period(ticker, raw)
    if true_newest == guessed_newest:
        return raw

    forward_periods: list[Period] = [true_newest]
    while len(forward_periods) < 8:
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


def _kap_patch_records_for_ufrs(ticker: str, newest_isyatirim_period: Period) -> tuple[list[repository.FinancialRecord], Period | None]:
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

    if raw.financial_group not in ("XI_29", "UFRS", "UFRS_KATILIM", "UFRS_K"):
        raise UnsupportedCompanyTypeError(
            f"'{ticker}' icin finansal tablo semasi ('{raw.financial_group}') henuz desteklenmiyor."
        )

    # KAP TAZELIK YAMASI (bkz. modul ust notu): Is Yatirim henuz islememis
    # olsa bile KAP'ta ZATEN yayinlanmis bir "Finansal Rapor" varsa, bu
    # TEK donemi ayrica cekip asagidaki "kullaniciya sor" kontrolunden ONCE
    # devreye sokariz -- boylece TATGD gibi bir durumda (Is Yatirim hala
    # eski ceyregi donduruyor ama KAP'ta yenisi zaten var) kullaniciya
    # gereksiz yere "eski donemi mi analiz edeyim?" SORULMAZ. XI_29 VE
    # UFRS (konvansiyonel banka) icin dogrulandi -- UFRS_KATILIM/UFRS_K
    # HENUZ desteklenmiyor (bkz. kap_financials.py sinirlamasi).
    kap_patch_records: list[repository.FinancialRecord] = []
    kap_patch_period: Period | None = None
    if raw.financial_group == "XI_29" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_xi29(ticker, max(raw.periods), raw)
    elif raw.financial_group == "UFRS" and raw.periods:
        kap_patch_records, kap_patch_period = _kap_patch_records_for_ufrs(ticker, max(raw.periods))

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
            retry_periods = [calculator.previous_quarter_period(p) for p in isyatirim.guess_last_periods(count=8)]
            raise PeriodNotAvailableError(ticker, quarter_label(guessed_newest), quarter_label(actual_newest), retry_periods)

    if raw.financial_group == "XI_29":
        records = _standardize_to_records(raw)
    elif raw.financial_group == "UFRS":
        records = _standardize_to_records_ufrs(raw)
    elif raw.financial_group == "UFRS_KATILIM":
        records = _standardize_to_records_ufrs_katilim(raw)
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
            return commentary_module.Commentary(
                headline=cached.headline,
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
            session, ticker, period, yorum.headline, yorum.summary, yorum.positives, yorum.negatives,
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
        TickerNotFoundError, DataSourceUnavailableError,
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
        raise TickerNotFoundError(str(exc)) from exc
    except sec_edgar.SecEdgarNetworkError as exc:
        raise DataSourceUnavailableError(str(exc)) from exc

    records = _standardize_to_records_us_gaap(raw)
    with repository.get_session() as session:
        repository.upsert_financials(session, ticker, records, market="NASDAQ")
        repository.set_company_info(session, ticker, name=raw.company_name, financial_group="US_GAAP", market="NASDAQ")


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

    with repository.get_session() as session:
        fresh = periods is None and repository.is_data_fresh(session, ticker, max_age_hours=12)
        cached_newest = None
        cached_group = None
        if fresh:
            cached = repository.get_financials(session, ticker, n_periods=1)
            if cached:
                cached_newest = max(cached)
            company_row = session.get(models.Company, ticker)
            cached_group = company_row.financial_group if company_row else None

    if not is_us and fresh and cached_newest is not None and cached_group:
        if _has_newer_period_available(ticker, cached_newest, cached_group):
            logger.info(
                "%s icin onbellek yas bakimindan taze ama daha yeni bir donem bulundu, tam fetch tetikleniyor.",
                ticker,
            )
            fresh = False

    if not fresh:
        try:
            if is_us:
                _fetch_and_store_us_gaap(ticker, periods)
            else:
                _fetch_and_store(ticker, periods)
        except Exception:
            price_executor.shutdown(wait=False)
            raise

    with repository.get_session() as session:
        financials_by_period = repository.get_financials(session, ticker, n_periods=8)
        disclosures_db = [] if is_us else repository.get_recent_disclosures(session, ticker, days=config.KAP_LOOKBACK_DAYS)
        company = session.get(models.Company, ticker)

    if not financials_by_period:
        price_executor.shutdown(wait=False)
        raise TickerNotFoundError(f"'{ticker}' icin veritabaninda finansal veri bulunamadi.")

    company_name = company.name if company and company.name else ticker
    sector = company.sector if company else None
    is_bank = bool(company and company.financial_group in ("UFRS", "UFRS_KATILIM"))
    is_participation_bank = bool(company and company.financial_group == "UFRS_KATILIM")
    is_insurance = bool(company and company.financial_group == "UFRS_K")

    price = price_future.result()
    price_executor.shutdown(wait=True)

    if is_us:
        analysis = calculator.analyze_us(ticker, financials_by_period)
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
            aktif_karliligi_pct=analysis.ratios.return_on_assets_annualized,
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
            now=datetime.now(),
        )

    out_path = config.DATA_DIR / "cards" / f"{ticker}_{analysis.latest_period[0]}Q{analysis.latest_period[1]}.png"
    png_path = card.render_card(context, str(out_path))

    with repository.get_session() as session:
        repository.save_generated_card(session, ticker, png_path, float(score.total_score))

    return PipelineResult(
        ticker=ticker, analysis=analysis, score=score, commentary=yorum,
        png_path=png_path, company_name=company_name, sector=sector,
    )
