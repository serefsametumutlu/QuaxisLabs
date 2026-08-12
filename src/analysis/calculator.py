"""YoY/QoQ yuzde degisim, rasyo ve bulgu hesaplamalari -- SAF MATEMATIK.

Bu modulde HICBIR LLM cagrisi yoktur ve src.fetchers.* / src.db.* hicbir
modulu import ETMEZ (katman ayrimi): girdi olarak zaten "standart alan
adlarina" cevrilmis, ceyreklik (gelir tablosu icin) veya STOK (bilanco
icin) degerler alir. Ham itemCode -> standart alan / kumulatif -> ceyreklik
donusumu Faz 2'de src/fetchers/isyatirim.py icinde yapilir; bu modul o
donusumun SONUCUNU tuketir.

Beklenen girdi seklinin (PeriodData) icermesi gereken anahtarlar:
    Gelir tablosu (CEYREKLIK deger -- cagiran taraf zaten turetmis olmali):
        revenue, gross_profit, operating_profit, net_income,
        depreciation_amortization (FAVOK icin; banka/sigortada YOK sayilir)
    Bilanco (STOK deger, oldugu gibi):
        cash, trade_receivables, total_assets, financial_debt, equity,
        current_assets, short_term_liabilities (sadece rasyo hesaplarinda kullanilir)

Eksik bir alan basitce sozlukte YOK sayilir veya None olarak verilir; bu
modul her yerde None-guvenlidir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

Period = tuple[int, int]  # (yil, donem); donem in {3, 6, 9, 12}
PeriodData = dict[str, Decimal | None]
FinancialsByPeriod = dict[Period, PeriodData]


# --- Degisim etiketleri -----------------------------------------------------


class ChangeLabel:
    GUCLU_ARTIS = "güçlü artış"
    ARTIS = "artış"
    YATAY = "yatay"
    AZALIS = "azalış"
    SERT_DUSUS = "sert düşüş"
    ZARARDAN_KARA_GECTI = "zarardan kâra geçti"
    KARA_KARSIN_ZARAR = "kâra karşın zarar açıkladı"
    VERI_YOK = "veri yok"
    # SADECE net_debt icin -- bkz. classify_debt_change(). "Zarardan kara
    # gecti" gibi kar/zarar (P&L) etiketleri net borc (bilanco/STOK) icin
    # ANLAMSIZ: net borc sifiri gecmesi "kar/zarar" degil "net nakit
    # pozisyonu <-> net borc pozisyonu" gecisidir (canli hata, kullanici
    # raporu: TERA'da net borc -4,7 mn'dan 15 mn'ye (net nakitten net borca,
    # yani KOTULESME) gecmisken kart "zarardan kara gecti" -- yani IYILESME --
    # yaziyordu, tam TERSI).
    NET_BORCA_GECTI = "net nakit pozisyonundan net borca geçti"
    NET_NAKDE_GECTI = "net borçtan net nakit pozisyonuna geçti"


_ESIK_GUCLU = Decimal("25")
_ESIK_NORMAL = Decimal("5")

FIELD_LABELS_TR: dict[str, str] = {
    "revenue": "Satışlar",
    "gross_profit": "Brüt Kâr",
    "operating_profit": "Esas Faaliyet Kârı",
    # SADECE FAVÖK hesabinin ic girdisi -- hicbir yerde DOGRUDAN gosterilmez
    # (bkz. ebitda()/ebitda_cum() ve isyatirim.STANDARD_ITEM_MAP_XI_29 ici not).
    "operating_profit_ebitda_base": "FAVÖK Baz Faaliyet Kârı (iç kullanım)",
    "ebitda": "FAVÖK",
    "net_income": "Net Dönem Kârı",
    "cash": "Nakit ve Benzerleri",
    "financial_investments": "Finansal Yatırımlar",
    "trade_receivables": "Ticari Alacaklar",
    "total_assets": "Toplam Varlıklar",
    "financial_debt": "Finansal Borçlar",
    "current_assets": "Dönen Varlıklar",
    "non_current_assets": "Duran Varlıklar",
    "net_debt": "Net Borç",
    "equity": "Özkaynaklar",
    "share_capital": "Ödenmiş Sermaye",
    # Kumulatif (YTD, Fintables/Matriks/İş Yatırım'ın varsayılan gösterdiği
    # ham) karsiliklari -- bkz. src/bot/pipeline.py _standardize_to_records.
    "revenue_cum": "Satışlar",
    "gross_profit_cum": "Brüt Kâr",
    "operating_profit_cum": "Esas Faaliyet Kârı",
    "operating_profit_ebitda_base_cum": "FAVÖK Baz Faaliyet Kârı (iç kullanım)",
    "ebitda_cum": "FAVÖK",
    "net_income_cum": "Net Dönem Kârı",
    # --- Banka (UFRS) alanlari -- bkz. analyze_bank() -----------------------------------------------------
    "interest_income": "Faiz Gelirleri",
    "interest_expense": "Faiz Giderleri",
    "net_fee_income": "Net Ücret ve Komisyon Gelirleri",
    "net_operating_profit": "Net Faaliyet Kârı",
    "loans": "Krediler",
    "deposits": "Mevduatlar",
    "provisions": "Karşılıklar",
    "interest_income_cum": "Faiz Gelirleri",
    "interest_expense_cum": "Faiz Giderleri",
    "net_fee_income_cum": "Net Ücret ve Komisyon Gelirleri",
    "net_operating_profit_cum": "Net Faaliyet Kârı",
    # --- Sigorta (UFRS_K) alanlari -- bkz. analyze_insurance() -----------------------------------------------------
    "gross_written_premiums": "Prim Üretimi",
    "net_premiums_earned": "Alınan Net Primler",
    "technical_income": "Teknik Gelirler",
    "technical_balance": "Teknik Denge",
    "cash_and_financial_assets": "Nakit Benzeri Finansal Varlıklar",
    "receivables_from_operations": "Esas Faaliyetlerden Alacaklar",
    "technical_provisions": "Teknik Karşılıklar",
    "payables_from_operations": "Esas Faaliyetlerden Borçlar",
    "gross_written_premiums_cum": "Prim Üretimi",
    "net_premiums_earned_cum": "Alınan Net Primler",
    "technical_income_cum": "Teknik Gelirler",
    "technical_balance_cum": "Teknik Denge",
    # --- Tasarruf Finansman Şirketi (XI_29K) alanları -- bkz. analyze_financing() -----------------------------------------------------
    "financing_revenue": "Esas Faaliyet Gelirleri",
    "operating_expenses": "Esas Faaliyet Giderleri",
    "other_operating_income": "Diğer Faaliyet Gelirleri",
    "financing_expenses": "Finansman Giderleri",
    "pretax_profit": "Vergi Öncesi Kâr/Zarar",
    "tax_provision": "Vergi Karşılığı",
    "overdue_receivables": "Takipteki Alacaklar",
    "financing_revenue_cum": "Esas Faaliyet Gelirleri",
    "operating_expenses_cum": "Esas Faaliyet Giderleri",
    "other_operating_income_cum": "Diğer Faaliyet Gelirleri",
    "financing_expenses_cum": "Finansman Giderleri",
    "pretax_profit_cum": "Vergi Öncesi Kâr/Zarar",
    "tax_provision_cum": "Vergi Karşılığı",
    # --- Faz "Veri Tamlığı" İlk Dalga (NASDAQ US_GAAP) alanları -- bkz.
    # src/fetchers/sec_edgar.py STANDARD_ITEM_MAP_US_GAAP ilgili yorumlar.
    "sga_expense": "Satış, Genel ve İdari Giderler",
    "sga_expense_cum": "Satış, Genel ve İdari Giderler",
    "research_development_expense": "Araştırma ve Geliştirme Giderleri",
    "research_development_expense_cum": "Araştırma ve Geliştirme Giderleri",
    "capex": "Yatırım Harcaması (Capex)",
    "capex_cum": "Yatırım Harcaması (Capex)",
    "dividend_per_share": "Hisse Başına Temettü",
    "dividend_per_share_cum": "Hisse Başına Temettü",
    "treasury_stock": "Hazine Hisseleri",
}


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class LineItemChange:
    label_tr: str
    current: Decimal | None
    comparison: Decimal | None  # YoY ya da QoQ karsilastirma degeri
    percent_change: Decimal | None
    change_label: str


@dataclass(frozen=True)
class IncomeStatementSummary:
    revenue: LineItemChange
    gross_profit: LineItemChange
    operating_profit: LineItemChange
    ebitda: LineItemChange | None  # banka/sigorta veya eksik amortisman verisinde None
    net_income: LineItemChange


@dataclass(frozen=True)
class BalanceSheetSummary:
    cash: LineItemChange
    trade_receivables: LineItemChange
    total_assets: LineItemChange
    financial_debt: LineItemChange
    equity: LineItemChange
    # Fintables/Matriks referans kartlarindaki BİLANÇO tablosuyla birebir
    # eslesmesi icin (bkz. references/ klasorundeki ornekler, kullanici
    # geri bildirimi): Donen Varliklar, Duran Varliklar, Net Borc. Duran
    # Varliklar tek bir standart alan olarak cekilmiyor -- Toplam Varliklar
    # - Donen Varliklar seklinde TURETILIR (bkz. analyze()).
    current_assets: LineItemChange
    non_current_assets: LineItemChange
    net_debt: LineItemChange


@dataclass(frozen=True)
class Ratios:
    gross_margin_current: Decimal | None
    gross_margin_prior_year: Decimal | None
    gross_margin_change_points: Decimal | None
    ebitda_margin_current: Decimal | None
    ebitda_margin_prior_year: Decimal | None
    ebitda_margin_change_points: Decimal | None
    net_margin_current: Decimal | None
    net_margin_prior_year: Decimal | None
    net_margin_change_points: Decimal | None
    net_debt_to_ebitda: Decimal | None  # TTM FAVOK ile (bkz. ttm_ebitda)
    current_ratio: Decimal | None  # cari oran
    roe_annualized: Decimal | None  # yıllıklandırılmış (TTM net kar / guncel ozkaynak) özkaynak karliligi, yuzde
    debt_to_equity: Decimal | None
    net_debt: Decimal | None  # finansal borc - nakit (guncel donem, STOK deger); degerleme (FD) hesaplarinin girdisi
    # TTM (son 12 ay) alanlari artik 4 ceyregi TEK TEK toplamiyor -- bkz.
    # _trailing_12m_from_cumulative(): guncel YTD + gecen yil tam yil -
    # gecen yil ayni donem YTD. Sadece 3 kumulatif veri noktasi yeterli;
    # aradaki tek bir ceyrek kaynakta eksik olsa bile (bkz. BORSK 2025/06
    # ornegi) hesaplanabilir. Bu 3 nokta da yoksa None doner.
    ttm_ebitda: Decimal | None
    ttm_revenue: Decimal | None
    ttm_operating_profit: Decimal | None
    ttm_net_income: Decimal | None  # ROE'nin de girdisi
    revenue_growth_yoy_pct: Decimal | None  # CEYREKLIK (standalone, kumulatif DEGIL) hasilat YoY buyumesi -- SADECE scorer.py'nin Buyume bileseni bunu kullanir; income_statement.revenue.percent_change artik KUMULATIF oldugu icin (bkz. analyze() ici not) skorlama icin ayri tutulur
    # --- Faz "Veri Tamlığı" İlk Dalga (docs/spec/spec_veri_tamlik_yol_haritasi.md
    # V-01/V-02/V-08/V-09) -- SADECE NASDAQ (analyze_us) sirketlerinde
    # dolu olur (BIST XI_29'da bu ham alanlar hic cekilmiyor, bkz.
    # isyatirim.py -- her zaman None). BILEREK skorlanan (agirlik tasiyan)
    # bir bilesene DONUSTURULMEDI: spec_mercek_kalite.md/spec_mercek_
    # guvenlik.md/spec_mercek_buyume.md'nin KENDI Agirliklar tablolari bu
    # kalemler icin (henuz) bir agirlik AYIRMIYOR -- ilgili mercek
    # spec'lerinin kendi metni ("simdilik SKORLANMAZ", "HER ZAMAN veri
    # eksik yer tutucu -- veri gelince skorlanan bilesene YUKSELTILIR")
    # bu kararin BILINCLI olarak GELECEK bir spec-revizyon turuna
    # birakildigini belirtiyor (agirlik UYDURULMASI persona kural ihlali
    # olurdu) -- bu alanlar SADECE ham oranin hesaplanip ACIGA CIKARILMASI
    # icindir (bilgi amacli, kartta/gelecek skorlamada kullanilabilir).
    sga_to_gross_profit_pct: Decimal | None = None  # 02/FORMÜL-02
    rd_to_gross_profit_pct: Decimal | None = None  # 02/FORMÜL-03
    interest_expense_to_operating_profit_pct: Decimal | None = None  # 01/FORMÜL-18, 02/FORMÜL-05
    ttm_capex: Decimal | None = None
    capex_to_net_income_pct: Decimal | None = None  # 02/FORMÜL-25,28 (reinvestment/yeniden yatırım kalitesi)
    ttm_dividend_per_share: Decimal | None = None  # V-03 -- DPS TTM (kümülatif alanlardan teleskopik türetim)


@dataclass(frozen=True)
class QuarterlySeriesPoint:
    period: Period
    revenue: Decimal | None
    ebitda: Decimal | None
    net_income: Decimal | None


@dataclass(frozen=True)
class Finding:
    field: str
    label_tr: str
    comparison: str  # "YoY" | "QoQ"
    current: Decimal | None
    previous: Decimal | None
    percent_change: Decimal | None
    direction: str  # "artis" | "azalis" | "yatay" | "belirsiz"
    change_label: str


@dataclass(frozen=True)
class AnalysisResult:
    ticker: str
    latest_period: Period
    income_statement: IncomeStatementSummary
    balance_sheet: BalanceSheetSummary
    ratios: Ratios
    quarterly_series: list[QuarterlySeriesPoint] = field(default_factory=list)  # eskiden yeniye, en fazla 5
    findings: list[Finding] = field(default_factory=list)
    # Faz 10 (NASDAQ/ABD): "TRY" | "USD" -- sadece GORUNTULEME icin (bkz.
    # src/render/card.py build_us_card_context() para birimi sembolu secimi).
    # Bu alanin varliginin hesaplama mantigina HICBIR ETKISI yoktur -- tum
    # Decimal aritmetigi (marj/oran/TTM) para biriminden BAGIMSIZDIR, sadece
    # her iki tarafin da AYNI para biriminde raporlandigi (BIST=TRY, SEC
    # EDGAR=USD) varsayilir. Varsayilan "TRY" -- mevcut analyze() cagrilari
    # (399 BIST testi dahil) bu alani ACIKCA vermez, DAVRANIS DEGISMEZ.
    currency: str = "TRY"
    # B21 (ADR/yabanci ozel ihracci -- NVO/TSM/SHEL/BABA gibi 20-F dosyalayan
    # sirketler): bu sirketler SADECE yillik (fp="FY") veri raporlar, hic
    # ceyreklik (Q1-Q3) donemleri YOKTUR. True ise `income_statement`/
    # `quarterly_series` icindeki "guncel" degerler aslinda TEK CEYREKLIK
    # DEGIL, TAM YIL rakamlaridir (bkz. pipeline._standardize_to_records_us_gaap
    # -- annual-only sirketler icin kumulatif deger DOGRUDAN "guncel" alana
    # yazilir, ceyreklik turetme DENENMEZ) -- render/telegram katmani bu
    # bayragi "4Ç25" yerine "FY25" gibi DOGRU bir etiket secmek icin kullanir
    # (bkz. pipeline.quarter_label, card._fiscal_quarter_label). BIST
    # (analyze()) icin HER ZAMAN False -- XI_29 sirketleri her zaman
    # ceyreklik raporlar.
    is_annual_only: bool = False


# --- Donem aritmetigi -----------------------------------------------------


def year_ago_period(period: Period) -> Period:
    """Onceki yil AYNI ceyrek (YoY karsilastirma icin)."""
    year, quarter = period
    return year - 1, quarter


def previous_quarter_period(period: Period) -> Period:
    """Bir onceki ceyrek (QoQ karsilastirma icin); yil basinda geriye sarar."""
    year, quarter = period
    if quarter == 3:
        return year - 1, 12
    return year, quarter - 3


# --- Yuzde degisim / etiketleme (kenar durumlari burada) -----------------------------------------------------


def _label_from_percent(percent: Decimal) -> tuple[str, str]:
    if percent > _ESIK_GUCLU:
        return ChangeLabel.GUCLU_ARTIS, "artis"
    if percent > _ESIK_NORMAL:
        return ChangeLabel.ARTIS, "artis"
    if percent >= -_ESIK_NORMAL:
        return ChangeLabel.YATAY, "yatay"
    if percent >= -_ESIK_GUCLU:
        return ChangeLabel.AZALIS, "azalis"
    return ChangeLabel.SERT_DUSUS, "azalis"


def classify_change(current: Decimal | None, previous: Decimal | None) -> tuple[Decimal | None, str, str]:
    """(yuzde_degisim, etiket, yon) doner. Kenar durumlari sirayla:

    1. current veya previous None            -> (None, VERI_YOK, "belirsiz")
    2. previous == 0                          -> (None, VERI_YOK, "belirsiz")  [sifira bolme]
    3. previous < 0 ve current >= 0           -> (None, ZARARDAN_KARA_GECTI, "artis")
    4. previous > 0 ve current <= 0           -> (None, KARA_KARSIN_ZARAR, "azalis")
    5. aksi halde: yuzde = (current-previous)/abs(previous)*100, esiklere gore etiket.

    NOT: Payda previous DEGIL abs(previous)'tur. Boylece "zarar daraldi"
    (orn. -100 -> -20) durumu, naif formulun (payda=previous, isareti ters
    cevirir) aksine DOGRU sekilde pozitif/iyilesme olarak isaretlenir.
    """
    if current is None or previous is None:
        return None, ChangeLabel.VERI_YOK, "belirsiz"
    if previous == 0:
        return None, ChangeLabel.VERI_YOK, "belirsiz"
    if previous < 0 and current >= 0:
        return None, ChangeLabel.ZARARDAN_KARA_GECTI, "artis"
    if previous > 0 and current <= 0:
        return None, ChangeLabel.KARA_KARSIN_ZARAR, "azalis"

    percent = (current - previous) / abs(previous) * 100
    label, direction = _label_from_percent(percent)
    return percent, label, direction


def classify_debt_change(current: Decimal | None, previous: Decimal | None) -> tuple[Decimal | None, str, str]:
    """classify_change()'in net_debt'e OZEL karsiligi -- SADECE sifir-gecisi
    (kenar durum 3/4) etiketleri farklidir, geri kalani AYNIDIR. Net borc
    kar/zarar (P&L) kavramı DEGILDIR -- sifiri gecmesi "net nakit pozisyonu
    <-> net borc pozisyonu" gecisidir, "zarardan kara gecti"/"kara karsin
    zarar acikladi" DEGIL (bkz. ChangeLabel.NET_BORCA_GECTI/NET_NAKDE_GECTI
    docstring'i, canli TERA hatasi)."""
    if current is None or previous is None:
        return None, ChangeLabel.VERI_YOK, "belirsiz"
    if previous == 0:
        return None, ChangeLabel.VERI_YOK, "belirsiz"
    if previous < 0 and current >= 0:
        return None, ChangeLabel.NET_BORCA_GECTI, "azalis"  # net nakitten net borca -- KOTULESME
    if previous > 0 and current <= 0:
        return None, ChangeLabel.NET_NAKDE_GECTI, "artis"  # net borctan net nakde -- IYILESME

    percent = (current - previous) / abs(previous) * 100
    label, direction = _label_from_percent(percent)
    return percent, label, direction


def _line_item_change(label_tr: str, current: Decimal | None, comparison: Decimal | None) -> LineItemChange:
    percent, label, _direction = classify_change(current, comparison)
    return LineItemChange(
        label_tr=label_tr, current=current, comparison=comparison, percent_change=percent, change_label=label
    )


def _line_item_change_debt(label_tr: str, current: Decimal | None, comparison: Decimal | None) -> LineItemChange:
    percent, label, _direction = classify_debt_change(current, comparison)
    return LineItemChange(
        label_tr=label_tr, current=current, comparison=comparison, percent_change=percent, change_label=label
    )


def _finding(field_name: str, comparison_type: str, current: Decimal | None, previous: Decimal | None) -> Finding:
    percent, label, direction = classify_change(current, previous)
    return Finding(
        field=field_name,
        label_tr=FIELD_LABELS_TR[field_name],
        comparison=comparison_type,
        current=current,
        previous=previous,
        percent_change=percent,
        direction=direction,
        change_label=label,
    )


# --- None-guvenli yardimci aritmetik -----------------------------------------------------


def _safe_sub(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    if a is None or b is None:
        return None
    return a - b


def _safe_div(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _net_debt(
    financial_debt: Decimal | None, cash: Decimal | None, financial_investments: Decimal | None
) -> Decimal | None:
    """Net Borc = Finansal Borclar - (Nakit ve Benzerleri + Finansal
    Yatirimlar). CANLI hata (kullanici raporu, Fintables karsilastirmasi):
    "financial_investments" (kisa vadeli menkul kiymet/repo portfoyu)
    eskiden HESABA KATILMIYORDU -- araci kurum gibi bu kalemi buyuk tasiyan
    sirketlerde (TERA) net borc ONLARCA MILYAR TL YANLIS cikiyordu
    (Fintables -146,4 mr iken eski hesap +15,5 mn). financial_debt/cash
    None ise (STANDARD alanlar, HER XI_29 sirketinde bulunur) sonuc yine
    None'dir -- ama financial_investments COGU sirkette hic RAPORLANMAZ, bu
    yuzden None ise 0 SAYILIR (aksi halde bu kalemi tasimayan sirketlerin
    TAMAMINDA net borc yanlislikla None/N-A'ya duserdi)."""
    if financial_debt is None or cash is None:
        return None
    return financial_debt - cash - (financial_investments or Decimal(0))


def _margin_pct(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    ratio = _safe_div(numerator, denominator)
    return ratio * 100 if ratio is not None else None


def _points_diff(current: Decimal | None, previous: Decimal | None) -> Decimal | None:
    return _safe_sub(current, previous)


def ebitda(period_data: PeriodData) -> Decimal | None:
    """FAVOK = "operating_profit_ebitda_base" + amortisman gideri.

    ONEMLI (canli TOASO verisiyle dogrulanan bug, duzeltildi): bu BILEREK
    "operating_profit" (gelir tablosunda gosterilen, PD/EFK'nin de girdisi
    olan "Faaliyet Kari") DEGIL, AYRI bir "operating_profit_ebitda_base"
    alanidir -- Fintables'in FAVOK'u ("Diger Faaliyet Gelir/Giderleri"
    HARIC, DAHA DAR bir faaliyet kari + amortisman) ile "Faaliyet Kari"
    (gelir tablosu satiri, DAHA GENIS -- Diger Faaliyet Gelir/Giderleri
    DAHIL) FARKLI kavramlar oldugu canli dogrulandi (TOASO 2026/06:
    FAVOK=4.832.996.000 SADECE dar kavram + amortismanla eslesiyor, PD/EFK
    ise SADECE genis kavramin TTM'iyle eslesiyor -- ikisini karistirmak
    FAVOK'u sistematik olarak "Diger Faaliyet Gelir/Gider" kadar YANLIS
    gosteriyordu). Amortisman verisi yoksa (orn. banka/sigorta sirketleri
    icin bu kalem izlenmiyorsa) None doner; cagiran taraf bunu ilgili tum
    alanlarda (rasyo, ozet blok, bulgu listesi) gizlemek icin kullanir."""
    operating_profit = period_data.get("operating_profit_ebitda_base")
    depreciation = period_data.get("depreciation_amortization")
    if operating_profit is None or depreciation is None:
        return None
    return operating_profit + depreciation


def ebitda_cum(period_data: PeriodData) -> Decimal | None:
    """ebitda()'nin KUMULATIF (YTD, "_cum" alanlarindan) karsiligi --
    SADECE GELIR TABLOSU ozet tablosunda/bulgu listesinde gosterim icin
    kullanilir (bkz. analyze() icindeki income_statement kurulumu);
    rasyo/skorlama/TTM hesaplarinda kullanilmaz (onlar ceyreklik ebitda()'yi
    kullanmaya devam eder). ebitda() gibi BILEREK "operating_profit_cum"
    DEGIL "operating_profit_ebitda_base_cum" okur (bkz. ebitda() docstring'i)."""
    operating_profit_cum = period_data.get("operating_profit_ebitda_base_cum")
    depreciation_cum = period_data.get("depreciation_amortization_cum")
    if operating_profit_cum is None or depreciation_cum is None:
        return None
    return operating_profit_cum + depreciation_cum


def _trailing_12m_from_cumulative(
    financials_by_period: FinancialsByPeriod, latest_period: Period, cum_getter
) -> Decimal | None:
    """TTM'i (son 12 ay) 4 ayri ceyregin CEYREKLESTIRILMIS degerini ust uste
    toplamak yerine, sirketin/KAP'in zaten yayinladigi KUMULATIF (YTD)
    rakamlardan turetir:

        TTM = guncel_YTD + gecen_yil_TAM_YIL - gecen_yil_AYNI_DONEM_YTD

    (guncel donem yilin son ceyregiyse -- period=12 -- guncel_YTD zaten tam
    yil demektir, tek basina TTM'dir.) Bu, matematiksel olarak 4 ceyregi
    ust uste toplamakla AYNI sonucu verir (kumulatif degerler teleskopik
    oldugu icin araya giren ceyrekler sadelesir) ama SADECE 3 veri noktasina
    ihtiyac duyar; aradaki ceyreklerden biri (orn. yari yil raporu) kaynakta
    hic yoksa bile calisir -- kullanici geri bildirimi: BORSK'ta İş
    Yatırım'in 2025/06 donemi icin HICBIR veri donmedigi canli dogrulandi,
    eski (4 ceyregi tek tek toplayan) yontem bu yuzden F/K, FD/FAVÖK,
    FD/HASILAT ve PD/EFK'yi hep "N/A" birakiyordu."""
    year, period = latest_period
    current_ytd = cum_getter(financials_by_period.get(latest_period, {}))
    if current_ytd is None:
        return None
    if period == 12:
        return current_ytd

    prior_year_full = cum_getter(financials_by_period.get((year - 1, 12), {}))
    prior_year_same_period = cum_getter(financials_by_period.get((year - 1, period), {}))
    if prior_year_full is None or prior_year_same_period is None:
        return None
    return current_ytd + prior_year_full - prior_year_same_period


# --- Çok dönemli trend serileri için PUBLIC sarmalayıcılar (Derin Kart, 2026-08-03) -----------------------------------------------------
#
# src/analysis/trends.py (analysis/ katmanının içinde, saf matematik) bu
# ÜÇ hesaplamayı TEK bir dönem yerine BİRDEN FAZLA geçmiş dönem için tekrar
# tekrar çağırır (marj/kaldıraç/ROE trendi). Mantığı KOPYALAMAK yerine
# (ikinci bir yerde TERA/BORSK tarzı bir hatanın SESSİZCE tekrarlanması
# riski) burada zaten var olan `_safe_div`/`_net_debt`/`_trailing_12m_from_cumulative`'e
# ince PUBLIC sarmalayıcılar eklendi -- iç mantık TEK yerde (yukarıdaki
# private fonksiyonlar) kalır, DEĞİŞTİRİLMEDİ.


def safe_div(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    """_safe_div()'in PUBLIC sarmalayıcısı."""
    return _safe_div(numerator, denominator)


def margin_pct(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    """_margin_pct()'in PUBLIC sarmalayıcısı."""
    return _margin_pct(numerator, denominator)


def net_debt(financial_debt: Decimal | None, cash: Decimal | None, financial_investments: Decimal | None) -> Decimal | None:
    """_net_debt()'in PUBLIC sarmalayıcısı."""
    return _net_debt(financial_debt, cash, financial_investments)


def trailing_12m_from_cumulative(financials_by_period: FinancialsByPeriod, period: Period, cum_getter) -> Decimal | None:
    """_trailing_12m_from_cumulative()'in PUBLIC sarmalayıcısı -- `period`
    illa en GÜNCEL dönem olmak ZORUNDA değildir, `financials_by_period`
    içindeki HERHANGİ bir dönem için TTM türetmede kullanılabilir (bkz.
    trends.py -- geçmiş her çeyrek için "o ana kadarki TTM" hesaplanır)."""
    return _trailing_12m_from_cumulative(financials_by_period, period, cum_getter)


# --- Ana giris noktasi -----------------------------------------------------


def analyze(ticker: str, financials_by_period: FinancialsByPeriod) -> AnalysisResult:
    """BIST XI_29 (sanayi/ticaret) sirketleri icin en yeni donemi baz alarak
    tam bir AnalysisResult uretir (currency='TRY').

    financials_by_period en az 1 donem icermelidir (en yeni donem = en
    buyuk (yil, ceyrek) anahtari); YoY/QoQ karsilastirma donemleri
    sozlukte yoksa ilgili alanlar None ile gosterilir (hata firlatilmaz).
    """
    return _build_analysis_result(ticker, financials_by_period, currency="TRY")


def analyze_us(
    ticker: str, financials_by_period: FinancialsByPeriod, ttm_depreciation_amortization_override: Decimal | None = None
) -> AnalysisResult:
    """NASDAQ/ABD (US_GAAP) sirketleri icin analyze()'nin karsiligi
    (currency='USD') -- bkz. src/fetchers/sec_edgar.py ve
    src/bot/pipeline.py._standardize_to_records_us_gaap().

    US GAAP sanayi sirketi ile BIST XI_29 sanayi sirketi KAVRAMSAL olarak
    NEREDEYSE AYNIDIR (Satislar, Brut Kar, Faaliyet Kari, Net Kar, FAVOK,
    Net Borc, Ozkaynaklar) -- bu yuzden analyze() ile TAMAMEN AYNI
    _build_analysis_result() cekirdegini kullanir, KOPYALANMAZ. Girdi
    sozlugundeki alan adlari (revenue/gross_profit/.../equity) BILEREK
    XI_29 ile AYNI tutuldu (bkz. pipeline._standardize_to_records_us_gaap
    docstring'i) ki bu fonksiyon HICBIR US GAAP'e OZEL kod icermesin.

    Farklar (SADECE cagiran/yazan tarafta, bu fonksiyonun ICINDE DEGIL):
      - Para birimi: `currency='USD'` (bkz. AnalysisResult.currency, SADECE
        goruntuleme icin -- bkz. card.build_us_card_context()).
      - FAVOK: US GAAP'te BIST'teki gibi "dar/genis faaliyet kari" ayrimi
        YOKTUR (bkz. pipeline._standardize_to_records_us_gaap() ust notu,
        CANLI dogrulandi: AAPL FY2024 OperatingIncomeLoss + D&A = kamuya
        acik FAVOK rakamiyla BIREBIR eslesti) -- bu yuzden
        "operating_profit_ebitda_base" alani DB'ye YAZILIRKEN zaten
        "operating_profit" ile AYNI deger olarak kaydedilir (pipeline
        katmaninda), calculator.ebitda() burada HICBIR DEGISIKLIK
        GEREKTIRMEDEN calisir.
      - Enflasyon: BIST tarafinda da su an REEL buyume duzeltmesi
        UYGULANMIYOR (bkz. PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md B6 --
        "enflasyon verisi girilmedi, nominal buyume kullanildi" HER IKI
        tarafta da GECERLI davranistir) -- ABD icin bu zaten DOGRU
        davranistir (ABD TUFE tipik olarak %2-4, TL'ye kiyasla ONEMSIZ,
        nominal USD buyumesi PRATIKTE reel buyumeye YAKINDIR); bu yuzden
        BURADA hicbir ek enflasyon mantigi EKLENMEDI -- scorer.py
        tarafinda (score_industrial(enflasyon_yoy_pct=...)) esikler
        farkli KALIBRE edildi (bkz. scorer.CONFIG['abd_sanayi']['buyume']),
        hesaplama KATMANI DEGISMEDI.
      - GELIR TABLOSU / bulgu listesi GORUNUMU: BIST'te (analyze()) bu
        tablo KASITLI olarak KUMULATIF (YTD) rakam gosterir (bkz.
        _build_analysis_result ici not, Fintables/Matriks konvansiyonu).
        ABD'de bu YANLIS/YANILTICI olur -- CANLI DOGRULANDI (kullanici
        raporu, AAPL Ç3 FY2026): sosyal medyada paylasilan "earnings
        highlights" (Bloomberg/earnings-bot tarzi) HER ZAMAN TEK CEYREKLIK
        rakam kullanir (orn. "$109,42 mr" TEK ceyrek, DEGIL "$364,4 mr" 9
        aylik kumulatif) -- bu projenin TEK ceyreklik turetme mantigi
        ($109.417 mr, 3 KURUS farkla eslesti) zaten DOGRUYDU, ama tablo
        kumulatif GOSTERDIGI icin "yanlis veri" IZLENIMI veriyordu. Bu
        yuzden analyze_us() `use_cumulative_display=False` gecer --
        GELIR TABLOSU/bulgu listesi de TEK CEYREKLIK rakamlari gosterir
        (ratios/TTM/degerleme zaten HER ZAMAN ceyreklikti, ETKILENMEDI).

    `ttm_depreciation_amortization_override`: AMD/TSLA gibi sirketlerde (bkz.
    PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B20) standart kumulatif-turetme
    (_trailing_12m_from_cumulative + ebitda_cum) D&A'nin bir bileseni (orn.
    AMD'de 'Depreciation') hic ceyreklik/YTD kirilimi olmadigi icin basarisiz
    olabilir -- oysa `ttm_operating_profit` (esas faaliyet kari) KENDISI
    genelde eksiksizdir. Cagiran taraf (pipeline.py)
    sec_edgar.trailing_12m_depreciation_amortization_us_gaap() ile AYRICA
    hesapladigi TTM D&A degerini buraya verirse, standart `ttm_ebitda`
    None DONERSE (SADECE o zaman) `ttm_operating_profit + bu deger` ile
    TTM FAVOK YINE DE hesaplanir (bkz. _build_analysis_result ici not).
    Bu deger HALA calculator.py DISINDA (sec_edgar.py'de) hesaplanir; bu
    fonksiyon SADECE hazir bir Decimal alir, hicbir fetcher import ETMEZ
    (katman kurali korunur).
    """
    return _build_analysis_result(
        ticker,
        financials_by_period,
        currency="USD",
        use_cumulative_display=False,
        ttm_depreciation_amortization_override=ttm_depreciation_amortization_override,
    )


def _build_analysis_result(
    ticker: str,
    financials_by_period: FinancialsByPeriod,
    currency: str,
    use_cumulative_display: bool = True,
    ttm_depreciation_amortization_override: Decimal | None = None,
) -> AnalysisResult:
    """analyze()/analyze_us() ORTAK cekirdegi -- bkz. her iki fonksiyonun
    docstring'i. Kopyala-yapıştır ONLENMESI icin TUM hesaplama mantigi
    burada TEK YERDE tutulur; iki giris noktasi SADECE `currency` VE
    `use_cumulative_display` degerlerini farklilastirir.

    `use_cumulative_display`: GELIR TABLOSU ozet tablosu VE bulgu listesinin
    (Artislar/Azalislar kutusu) KUMULATIF (YTD, True -- BIST varsayilani) mi
    yoksa TEK CEYREKLIK (False -- ABD, bkz. analyze_us() docstring'i) rakam
    mi gosterecegini secer. ratios/TTM/degerleme/quarterly_series bu
    bayraktan ETKILENMEZ -- onlar HER ZAMAN ceyreklik alanlari okur (TTM 4
    ceyregi ust uste toplar, kumulatif degerlerle bu YANLIS olurdu)."""
    if not financials_by_period:
        raise ValueError("financials_by_period bos olamaz.")

    periods_desc = sorted(financials_by_period.keys(), reverse=True)
    latest_period = periods_desc[0]

    current = financials_by_period.get(latest_period, {})
    yoy_prior = financials_by_period.get(year_ago_period(latest_period), {})
    qoq_prior = financials_by_period.get(previous_quarter_period(latest_period), {})

    ebitda_current = ebitda(current)
    ebitda_yoy_prior = ebitda(yoy_prior)

    # GELIR TABLOSU ozet tablosu (BIST'te, use_cumulative_display=True)
    # KASITLI olarak KUMULATIF (YTD) alanlari kullanir -- kullanici geri
    # bildirimi: insanlar genelde Fintables'i referans aliyor, Fintables'in
    # varsayilan (ucretsiz) gorunumu de KAP'a bagli kumulatif rakam
    # gosteriyor (canli dogrulandi: TAVHL 2026/6 Ana Ortaklik Paylari =
    # 528.152 bin TL, hem Fintables hem Matriks'te BIREBIR ayni) --
    # ceyreklestirilmis (standalone) rakamla kiyaslaninca "bu yanlis mi"
    # sanilabiliyordu. ABD'de (use_cumulative_display=False) TERSI GECERLI
    # -- bkz. analyze_us() docstring'i (CANLI DOGRULANDI: sosyal medya
    # earnings-highlight paylasimlari TEK CEYREKLIK rakam kullanir).
    # TTM/rasyo/skorlama/CEYREKLIK SERI grafigi ise HER IKI tarafta da
    # BILEREK ceyreklik (asagidaki ebitda_current/quarterly_series/ratios)
    # kullanmaya devam eder -- TTM 4 ceyregi ust uste toplar, kumulatif
    # degerlerle bu YANLIS olurdu.
    ebitda_cum_current = ebitda_cum(current)
    ebitda_cum_yoy_prior = ebitda_cum(yoy_prior)

    if use_cumulative_display:
        revenue_display_field, gross_profit_display_field = "revenue_cum", "gross_profit_cum"
        operating_profit_display_field, net_income_display_field = "operating_profit_cum", "net_income_cum"
        ebitda_display_current, ebitda_display_yoy_prior = ebitda_cum_current, ebitda_cum_yoy_prior
    else:
        revenue_display_field, gross_profit_display_field = "revenue", "gross_profit"
        operating_profit_display_field, net_income_display_field = "operating_profit", "net_income"
        ebitda_display_current, ebitda_display_yoy_prior = ebitda_current, ebitda_yoy_prior

    income_statement = IncomeStatementSummary(
        revenue=_line_item_change(
            FIELD_LABELS_TR["revenue"], current.get(revenue_display_field), yoy_prior.get(revenue_display_field)
        ),
        gross_profit=_line_item_change(
            FIELD_LABELS_TR["gross_profit"],
            current.get(gross_profit_display_field),
            yoy_prior.get(gross_profit_display_field),
        ),
        operating_profit=_line_item_change(
            FIELD_LABELS_TR["operating_profit"],
            current.get(operating_profit_display_field),
            yoy_prior.get(operating_profit_display_field),
        ),
        ebitda=(
            _line_item_change(FIELD_LABELS_TR["ebitda"], ebitda_display_current, ebitda_display_yoy_prior)
            if ebitda_display_current is not None
            else None
        ),
        net_income=_line_item_change(
            FIELD_LABELS_TR["net_income"], current.get(net_income_display_field), yoy_prior.get(net_income_display_field)
        ),
    )

    balance_sheet = BalanceSheetSummary(
        cash=_line_item_change(FIELD_LABELS_TR["cash"], current.get("cash"), qoq_prior.get("cash")),
        trade_receivables=_line_item_change(
            FIELD_LABELS_TR["trade_receivables"], current.get("trade_receivables"), qoq_prior.get("trade_receivables")
        ),
        total_assets=_line_item_change(
            FIELD_LABELS_TR["total_assets"], current.get("total_assets"), qoq_prior.get("total_assets")
        ),
        financial_debt=_line_item_change(
            FIELD_LABELS_TR["financial_debt"], current.get("financial_debt"), qoq_prior.get("financial_debt")
        ),
        current_assets=_line_item_change(
            FIELD_LABELS_TR["current_assets"], current.get("current_assets"), qoq_prior.get("current_assets")
        ),
        non_current_assets=_line_item_change(
            FIELD_LABELS_TR["non_current_assets"],
            _safe_sub(current.get("total_assets"), current.get("current_assets")),
            _safe_sub(qoq_prior.get("total_assets"), qoq_prior.get("current_assets")),
        ),
        net_debt=_line_item_change_debt(
            FIELD_LABELS_TR["net_debt"],
            _net_debt(current.get("financial_debt"), current.get("cash"), current.get("financial_investments")),
            _net_debt(qoq_prior.get("financial_debt"), qoq_prior.get("cash"), qoq_prior.get("financial_investments")),
        ),
        equity=_line_item_change(FIELD_LABELS_TR["equity"], current.get("equity"), qoq_prior.get("equity")),
    )

    gross_margin_current = _margin_pct(current.get("gross_profit"), current.get("revenue"))
    gross_margin_prior_year = _margin_pct(yoy_prior.get("gross_profit"), yoy_prior.get("revenue"))
    ebitda_margin_current = _margin_pct(ebitda_current, current.get("revenue"))
    ebitda_margin_prior_year = _margin_pct(ebitda_yoy_prior, yoy_prior.get("revenue"))
    net_margin_current = _margin_pct(current.get("net_income"), current.get("revenue"))
    net_margin_prior_year = _margin_pct(yoy_prior.get("net_income"), yoy_prior.get("revenue"))

    ttm_ebitda = _trailing_12m_from_cumulative(financials_by_period, latest_period, ebitda_cum)
    ttm_net_income = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("net_income_cum")
    )
    ttm_revenue = _trailing_12m_from_cumulative(financials_by_period, latest_period, lambda d: d.get("revenue_cum"))
    ttm_operating_profit = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("operating_profit_cum")
    )
    if ttm_ebitda is None and ttm_operating_profit is not None and ttm_depreciation_amortization_override is not None:
        # AMD/TSLA gibi sirketlerde (bkz. §B20) standart yontem
        # (_trailing_12m_from_cumulative + ebitda_cum) D&A'nin bir
        # bileseninin (orn. AMD'nin 'Depreciation'i) hic ceyreklik/YTD
        # kirilimi olmamasi yuzunden basarisiz olabilir. `ttm_operating_profit`
        # KENDISI zaten calisiyorsa (AMD/TSLA'da bu boyle -- esas faaliyet
        # kari eksiksiz raporlaniyor), cagiran tarafin (pipeline.py, bkz.
        # sec_edgar.trailing_12m_depreciation_amortization_us_gaap)
        # SADECE D&A'nin TTM'ini ayrica hesaplayip verdigi bu YEDEK ile
        # birlestirilerek TTM FAVOK YINE DE elde edilir.
        ttm_ebitda = ttm_operating_profit + ttm_depreciation_amortization_override
    net_debt = _net_debt(current.get("financial_debt"), current.get("cash"), current.get("financial_investments"))
    revenue_growth_yoy_pct, _label, _direction = classify_change(current.get("revenue"), yoy_prior.get("revenue"))

    # Faz "Veri Tamlığı" İlk Dalga -- bkz. Ratios ici not (ham/bilgi amacli,
    # BILINCLI olarak skorlanmiyor). BIST XI_29'da bu ham alanlar (current
    # dict'inde) hic yok -- hepsi otomatik None kalir (Kural 3).
    sga_to_gross_profit_pct = _margin_pct(current.get("sga_expense"), current.get("gross_profit"))
    rd_to_gross_profit_pct = _margin_pct(current.get("research_development_expense"), current.get("gross_profit"))
    interest_expense_to_operating_profit_pct = _margin_pct(current.get("interest_expense"), current.get("operating_profit"))
    ttm_capex = _trailing_12m_from_cumulative(financials_by_period, latest_period, lambda d: d.get("capex_cum"))
    capex_to_net_income_pct = _margin_pct(ttm_capex, ttm_net_income) if ttm_net_income is not None and ttm_net_income > 0 else None
    ttm_dividend_per_share = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("dividend_per_share_cum")
    )

    ratios = Ratios(
        gross_margin_current=gross_margin_current,
        gross_margin_prior_year=gross_margin_prior_year,
        gross_margin_change_points=_points_diff(gross_margin_current, gross_margin_prior_year),
        ebitda_margin_current=ebitda_margin_current,
        ebitda_margin_prior_year=ebitda_margin_prior_year,
        ebitda_margin_change_points=_points_diff(ebitda_margin_current, ebitda_margin_prior_year),
        net_margin_current=net_margin_current,
        net_margin_prior_year=net_margin_prior_year,
        net_margin_change_points=_points_diff(net_margin_current, net_margin_prior_year),
        net_debt_to_ebitda=_safe_div(net_debt, ttm_ebitda),
        current_ratio=_safe_div(current.get("current_assets"), current.get("short_term_liabilities")),
        roe_annualized=_margin_pct(ttm_net_income, current.get("equity")),
        debt_to_equity=_safe_div(current.get("financial_debt"), current.get("equity")),
        net_debt=net_debt,
        ttm_ebitda=ttm_ebitda,
        ttm_revenue=ttm_revenue,
        ttm_operating_profit=ttm_operating_profit,
        ttm_net_income=ttm_net_income,
        revenue_growth_yoy_pct=revenue_growth_yoy_pct,
        sga_to_gross_profit_pct=sga_to_gross_profit_pct,
        rd_to_gross_profit_pct=rd_to_gross_profit_pct,
        interest_expense_to_operating_profit_pct=interest_expense_to_operating_profit_pct,
        ttm_capex=ttm_capex,
        capex_to_net_income_pct=capex_to_net_income_pct,
        ttm_dividend_per_share=ttm_dividend_per_share,
    )

    series_periods = list(reversed(periods_desc[:5]))
    quarterly_series = [
        QuarterlySeriesPoint(
            period=p,
            revenue=financials_by_period.get(p, {}).get("revenue"),
            ebitda=ebitda(financials_by_period.get(p, {})),
            net_income=financials_by_period.get(p, {}).get("net_income"),
        )
        for p in series_periods
    ]

    # Bulgu listesi (Artislar/Azalislar kutusu + LLM/yedek yorum girdisi) de
    # GELIR TABLOSU ile TUTARLI kalsin diye AYNI display alanini kullanir --
    # aksi halde ayni karti icinde tablo "528 mn" derken Artislar kutusu
    # farkli bir rakam (kumulatif/ceyreklik karisikligi) gosterip CELISKI
    # yaratirdi (bkz. yukaridaki income_statement notu).
    findings = [
        _finding("revenue", "YoY", current.get(revenue_display_field), yoy_prior.get(revenue_display_field)),
        _finding(
            "gross_profit", "YoY", current.get(gross_profit_display_field), yoy_prior.get(gross_profit_display_field)
        ),
        _finding(
            "operating_profit", "YoY",
            current.get(operating_profit_display_field), yoy_prior.get(operating_profit_display_field),
        ),
    ]
    if ebitda_display_current is not None:
        findings.append(_finding("ebitda", "YoY", ebitda_display_current, ebitda_display_yoy_prior))
    findings.append(
        _finding("net_income", "YoY", current.get(net_income_display_field), yoy_prior.get(net_income_display_field))
    )

    findings.extend(
        [
            _finding("cash", "QoQ", current.get("cash"), qoq_prior.get("cash")),
            _finding("trade_receivables", "QoQ", current.get("trade_receivables"), qoq_prior.get("trade_receivables")),
            _finding("total_assets", "QoQ", current.get("total_assets"), qoq_prior.get("total_assets")),
            _finding("financial_debt", "QoQ", current.get("financial_debt"), qoq_prior.get("financial_debt")),
            _finding("equity", "QoQ", current.get("equity"), qoq_prior.get("equity")),
        ]
    )

    return AnalysisResult(
        ticker=ticker,
        latest_period=latest_period,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        ratios=ratios,
        quarterly_series=quarterly_series,
        findings=findings,
        currency=currency,
        # bkz. AnalysisResult.is_annual_only alan notu. SADECE en yakin
        # zamanli (en fazla 4) donem penceresine bakilir -- pipeline.
        # _standardize_to_records_us_gaap() ile AYNI ilke (izole/eski bir
        # ceyreklik fact TEK BASINA "hala ceyreklik raporluyor" sanmamiza
        # yol acmamali, bkz. o fonksiyonun ici notu -- BABA'da CANLI
        # dogrulanan 2020'den kalma boyle bir fact vardi).
        is_annual_only=all(fp == 12 for _, fp in periods_desc[:4]),
    )


# --- Degerleme (piyasa degeri / F-K / PD-DD / FD carpanlari) -----------------------------------------------------
#
# Bu blok da SAF MATEMATIKTIR (LLM/fetcher bagimliligi yok). Fiyat ve
# odenmis sermaye disaridan (fetcher katmanindan) verilir; AnalysisResult
# tek basina bunlari icermez. BIST'te nominal pay degeri 1 TL oldugu icin
# "sermaye" (odenmis sermaye, TL) = toplam pay adedi varsayimi kullanilir --
# bu, piyasa katilimcilarinin (Matriks, Is Yatirim vb.) da kullandigi
# standart kisayoldur.


@dataclass(frozen=True)
class ValuationMetrics:
    price: Decimal
    share_capital: Decimal  # odenmis sermaye (TL) = varsayilan pay adedi (nominal 1 TL/pay)
    market_cap: Decimal  # piyasa degeri = fiyat x sermaye
    net_debt: Decimal | None  # finansal borc - nakit (guncel donem)
    enterprise_value: Decimal | None  # FD = piyasa degeri + net borc
    pe_ratio: Decimal | None  # F/K = piyasa degeri / TTM net kar (ana ortaklik)
    pb_ratio: Decimal | None  # PD/DD = piyasa degeri / guncel ozkaynak
    ev_ebitda: Decimal | None  # FD/FAVÖK = FD / TTM FAVOK
    ev_revenue: Decimal | None  # FD/Hasılat = FD / TTM hasilat
    price_to_operating_profit: Decimal | None  # PD/EFK = piyasa degeri / TTM esas faaliyet kari


def compute_valuation(
    analysis: AnalysisResult, price: Decimal | None, share_capital: Decimal | None
) -> ValuationMetrics | None:
    """Fiyat ve odenmis sermaye ikisi de mevcutsa piyasa degeri + carpanlari
    hesaplar; ikisinden biri eksikse (henuz cekilememis olabilir) None doner
    -- kartin geri kalanini BLOKE ETMEMELI (fiyat/sermaye supplementary veridir,
    bkz. isyatirim.fetch_latest_price docstring'i)."""
    if price is None or share_capital is None:
        return None

    market_cap = price * share_capital
    r = analysis.ratios
    equity_current = analysis.balance_sheet.equity.current

    net_debt = r.net_debt
    enterprise_value = market_cap + net_debt if net_debt is not None else None

    return ValuationMetrics(
        price=price,
        share_capital=share_capital,
        market_cap=market_cap,
        net_debt=net_debt,
        enterprise_value=enterprise_value,
        pe_ratio=_safe_div(market_cap, r.ttm_net_income),
        pb_ratio=_safe_div(market_cap, equity_current),
        ev_ebitda=_safe_div(enterprise_value, r.ttm_ebitda),
        ev_revenue=_safe_div(enterprise_value, r.ttm_revenue),
        price_to_operating_profit=_safe_div(market_cap, r.ttm_operating_profit),
    )


# --- Banka (UFRS) analiz sonucu -----------------------------------------------------
#
# Bankalarin gelir tablosu XI_29'daki (hasilat/brut kar/esas faaliyet kari/
# FAVOK) kavramlarini ICERMEZ -- IncomeStatementSummary/BalanceSheetSummary
# bu yuzden YENIDEN KULLANILMAZ (alanlari banka icin anlamsiz/yanlis
# etiketli olurdu); ayri, paralel bir veri modeli + analyze_bank() tanimlanir.
# Girdi alanlari src.bot.pipeline._standardize_to_records_ufrs tarafindan
# yazilir (bkz. src/fetchers/isyatirim.py STANDARD_ITEM_MAP_UFRS).


@dataclass(frozen=True)
class BankIncomeStatementSummary:
    interest_income: LineItemChange
    interest_expense: LineItemChange
    net_fee_income: LineItemChange
    net_operating_profit: LineItemChange
    net_income: LineItemChange


@dataclass(frozen=True)
class BankBalanceSheetSummary:
    loans: LineItemChange
    deposits: LineItemChange
    provisions: LineItemChange
    total_assets: LineItemChange
    equity: LineItemChange


@dataclass(frozen=True)
class BankRatios:
    # BASITLESTIRILMIS yaklasik net faiz marji: TTM net faiz geliri / GUNCEL
    # toplam varlik. GERCEK regulatuar NIM ortalama GETIRILI varlik uzerinden
    # hesaplanir (bu detay fetcher katmaninda yok) -- bu yuzden bu sadece bir
    # YAKLASIMDIR, scorer.score_bank()'a da bu sekilde belgelenerek verilir.
    net_interest_margin_current: Decimal | None
    # KULLANICI RAPORU (TURSG/sigorta icin, 2026-08-03 -- ayni sablon
    # bankada da BOSTU): Net Faiz Marji/Aktif Karliligi skor bilesenleri
    # HER ZAMAN "trend verisi yok" gosteriyordu -- score_bank() trend_puan'i
    # SABIT None geciyordu (bkz. scorer.py, artik duzeltildi). Bir onceki
    # yilin AYNI ceyregi icin biten TTM (yoy_prior donemine kadar olan 4
    # ceyrek) ile guncel TTM kiyaslanir -- n_periods=8 ceyrek fetch'i tam
    # SINIRINDA yeterli (yoy_prior'un TTM'i icin ONDAN 3 ceyrek daha geriye
    # gerekir); yetersizse (yeni sirket) _trailing_12m_from_cumulative
    # zaten None doner, GERI DONUS "trend verisi yok" ile AYNI (regresyon
    # yok).
    net_interest_margin_prior_year: Decimal | None
    net_interest_margin_change_points: Decimal | None
    net_margin_current: Decimal | None  # net kar / faiz geliri
    roe_annualized: Decimal | None  # yıllıklandırılmış (TTM net kar / guncel ozkaynak) ozkaynak karliligi, yuzde
    # CAMELS (bkz. scorer.score_bank docstring'i) "Earnings" bileseninde NIM
    # ile BIRLIKTE onerilen ikinci gosterge: yıllıklandırılmış (TTM net kar /
    # guncel toplam varlik) aktif karliligi, yuzde.
    return_on_assets_annualized: Decimal | None
    return_on_assets_prior_year: Decimal | None
    return_on_assets_change_points: Decimal | None
    # Sermaye Yeterlilik Orani (BDDK duzenleyici, risk agirlikli varlik
    # bazli) bu veri kaynaginda YOKTUR (bkz. isyatirim.py -- MaliTablo uc
    # noktasinda bulunmuyor). Bunun yerine CAMELS "Capital Adequacy"
    # ruhuna uygun, TAMAMEN bu veriyle hesaplanabilen bir KALDIRAÇ/SERMAYE
    # GUCU YAKLASIMI kullanilir: guncel ozkaynak / guncel toplam varlik,
    # yuzde. Regulatuar CAR'in (Tier1+2/RWA) YERINE GECMEZ, ayri bir
    # yaklasik gostergedir -- scorer.score_bank()'a da bu sekilde
    # belgelenerek verilir.
    equity_to_assets_current: Decimal | None
    ttm_net_income: Decimal | None
    ttm_interest_income: Decimal | None


@dataclass(frozen=True)
class BankQuarterlySeriesPoint:
    period: Period
    net_interest_income: Decimal | None
    net_income: Decimal | None
    loans: Decimal | None


@dataclass(frozen=True)
class BankAnalysisResult:
    ticker: str
    latest_period: Period
    income_statement: BankIncomeStatementSummary
    balance_sheet: BankBalanceSheetSummary
    ratios: BankRatios
    quarterly_series: list[BankQuarterlySeriesPoint] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    sector_template: str = "banka"


# Katilim bankalari (orn. ALBRK) "faizsiz bankacilik" ilkesi geregi FARKLI
# terminoloji kullanir -- canli dogrulandi (bkz. isyatirim.py
# STANDARD_ITEM_MAP_UFRS_KATILIM yorumu). Sadece bu UC alanin etiketi
# degisir; diger tum banka kalemleri (Krediler, Net Faaliyet Kari,
# Ozkaynaklar, vb.) NOTR terimlerdir, katilim/konvansiyonel farki yoktur.
_PARTICIPATION_BANK_LABELS: dict[str, str] = {
    "interest_income": "Kâr Payı Gelirleri",
    "interest_expense": "Kâr Payı Giderleri",
    "deposits": "Toplanan Fonlar",
}


def analyze_bank(
    ticker: str, financials_by_period: FinancialsByPeriod, bank_variant: str = "conventional"
) -> BankAnalysisResult:
    """Banka (UFRS) sirketleri icin analyze()'nin karsiligi -- bkz. modul
    ici ust not. financials_by_period en az 1 donem icermelidir.

    `bank_variant="participation"` verilirse (katilim bankasi, bkz.
    pipeline.py financial_group=='UFRS_KATILIM' dallanmasi) Faiz Gelirleri/
    Giderleri ve Mevduat etiketleri sirasiyla Kâr Payı Gelirleri/Giderleri
    ve Toplanan Fonlar olarak degisir -- DEGERLER ayni sekilde hesaplanir,
    SADECE goruntulenen Turkce etiket degisir (bkz. _PARTICIPATION_BANK_LABELS)."""
    if not financials_by_period:
        raise ValueError("financials_by_period bos olamaz.")

    labels = {**FIELD_LABELS_TR, **_PARTICIPATION_BANK_LABELS} if bank_variant == "participation" else FIELD_LABELS_TR

    periods_desc = sorted(financials_by_period.keys(), reverse=True)
    latest_period = periods_desc[0]

    current = financials_by_period.get(latest_period, {})
    yoy_prior = financials_by_period.get(year_ago_period(latest_period), {})
    qoq_prior = financials_by_period.get(previous_quarter_period(latest_period), {})

    income_statement = BankIncomeStatementSummary(
        interest_income=_line_item_change(
            labels["interest_income"], current.get("interest_income_cum"), yoy_prior.get("interest_income_cum")
        ),
        interest_expense=_line_item_change(
            labels["interest_expense"], current.get("interest_expense_cum"), yoy_prior.get("interest_expense_cum")
        ),
        net_fee_income=_line_item_change(
            labels["net_fee_income"], current.get("net_fee_income_cum"), yoy_prior.get("net_fee_income_cum")
        ),
        net_operating_profit=_line_item_change(
            labels["net_operating_profit"],
            current.get("net_operating_profit_cum"),
            yoy_prior.get("net_operating_profit_cum"),
        ),
        net_income=_line_item_change(
            labels["net_income"], current.get("net_income_cum"), yoy_prior.get("net_income_cum")
        ),
    )

    balance_sheet = BankBalanceSheetSummary(
        loans=_line_item_change(labels["loans"], current.get("loans"), qoq_prior.get("loans")),
        deposits=_line_item_change(labels["deposits"], current.get("deposits"), qoq_prior.get("deposits")),
        provisions=_line_item_change(
            labels["provisions"], current.get("provisions"), qoq_prior.get("provisions")
        ),
        total_assets=_line_item_change(
            labels["total_assets"], current.get("total_assets"), qoq_prior.get("total_assets")
        ),
        equity=_line_item_change(labels["equity"], current.get("equity"), qoq_prior.get("equity")),
    )

    ttm_interest_income = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("interest_income_cum")
    )
    ttm_net_income = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("net_income_cum")
    )
    yoy_prior_period = year_ago_period(latest_period)
    ttm_interest_income_prior_year = _trailing_12m_from_cumulative(
        financials_by_period, yoy_prior_period, lambda d: d.get("interest_income_cum")
    )
    ttm_net_income_prior_year = _trailing_12m_from_cumulative(
        financials_by_period, yoy_prior_period, lambda d: d.get("net_income_cum")
    )
    net_interest_margin_current = _margin_pct(ttm_interest_income, current.get("total_assets"))
    net_interest_margin_prior_year = _margin_pct(ttm_interest_income_prior_year, yoy_prior.get("total_assets"))
    return_on_assets_annualized = _margin_pct(ttm_net_income, current.get("total_assets"))
    return_on_assets_prior_year = _margin_pct(ttm_net_income_prior_year, yoy_prior.get("total_assets"))

    ratios = BankRatios(
        net_interest_margin_current=net_interest_margin_current,
        net_interest_margin_prior_year=net_interest_margin_prior_year,
        net_interest_margin_change_points=_points_diff(net_interest_margin_current, net_interest_margin_prior_year),
        net_margin_current=_margin_pct(current.get("net_income"), current.get("interest_income")),
        roe_annualized=_margin_pct(ttm_net_income, current.get("equity")),
        return_on_assets_annualized=return_on_assets_annualized,
        return_on_assets_prior_year=return_on_assets_prior_year,
        return_on_assets_change_points=_points_diff(return_on_assets_annualized, return_on_assets_prior_year),
        equity_to_assets_current=_margin_pct(current.get("equity"), current.get("total_assets")),
        ttm_net_income=ttm_net_income,
        ttm_interest_income=ttm_interest_income,
    )

    series_periods = list(reversed(periods_desc[:5]))
    quarterly_series = [
        BankQuarterlySeriesPoint(
            period=p,
            net_interest_income=financials_by_period.get(p, {}).get("interest_income"),
            net_income=financials_by_period.get(p, {}).get("net_income"),
            loans=financials_by_period.get(p, {}).get("loans"),
        )
        for p in series_periods
    ]

    findings = [
        _finding("interest_income", "YoY", current.get("interest_income_cum"), yoy_prior.get("interest_income_cum")),
        _finding("interest_expense", "YoY", current.get("interest_expense_cum"), yoy_prior.get("interest_expense_cum")),
        _finding("net_fee_income", "YoY", current.get("net_fee_income_cum"), yoy_prior.get("net_fee_income_cum")),
        _finding(
            "net_operating_profit", "YoY", current.get("net_operating_profit_cum"), yoy_prior.get("net_operating_profit_cum")
        ),
        _finding("net_income", "YoY", current.get("net_income_cum"), yoy_prior.get("net_income_cum")),
        _finding("loans", "QoQ", current.get("loans"), qoq_prior.get("loans")),
        _finding("deposits", "QoQ", current.get("deposits"), qoq_prior.get("deposits")),
        _finding("equity", "QoQ", current.get("equity"), qoq_prior.get("equity")),
    ]

    return BankAnalysisResult(
        ticker=ticker,
        latest_period=latest_period,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        ratios=ratios,
        quarterly_series=quarterly_series,
        findings=findings,
    )


# --- Tasarruf Finansman Şirketi (XI_29K) analiz sonucu -----------------------------------------------------
#
# Bankadaki gibi ayri bir paralel veri modeli: Katilimevim (KTLEV) gibi
# Tasarruf Finansman Sirketlerinin gelir tablosu/bilancosu sanayi/banka
# kalemlerinden FARKLIDIR (bkz. isyatirim.py STANDARD_ITEM_MAP_FINANSMAN).
# Kural 3 geregi SADECE acikca/tek anlamli etiketli "toplam" kalemler
# eslendi -- bilesik/yorum gerektiren kalemler (orn. "Gercege Uygun Deger
# Farki K/Z'a Yansitilan Finansal Varliklar") BILINCLI OLARAK DISARIDA
# birakildi, bu yuzden "cari oran"/"kaldirac" gibi sanayi/banka rasyolari
# BURADA YOK (girdi kalemleri yok, uretilirse UYDURMA olurdu).


@dataclass(frozen=True)
class FinancingIncomeStatementSummary:
    financing_revenue: LineItemChange
    operating_expenses: LineItemChange
    net_operating_profit: LineItemChange
    net_income: LineItemChange


@dataclass(frozen=True)
class FinancingBalanceSheetSummary:
    cash: LineItemChange
    overdue_receivables: LineItemChange
    total_assets: LineItemChange
    equity: LineItemChange


@dataclass(frozen=True)
class FinancingRatios:
    net_margin_current: Decimal | None  # net kar / esas faaliyet geliri (guncel donem, KUMULATIF)
    roe_annualized: Decimal | None  # yıllıklandırılmış (TTM net kar / guncel ozkaynak)
    return_on_assets_annualized: Decimal | None  # yıllıklandırılmış (TTM net kar / guncel toplam varlik)
    equity_to_assets_current: Decimal | None
    ttm_net_income: Decimal | None
    ttm_financing_revenue: Decimal | None


@dataclass(frozen=True)
class FinancingQuarterlySeriesPoint:
    period: Period
    financing_revenue: Decimal | None
    net_income: Decimal | None


@dataclass(frozen=True)
class FinancingAnalysisResult:
    ticker: str
    latest_period: Period
    income_statement: FinancingIncomeStatementSummary
    balance_sheet: FinancingBalanceSheetSummary
    ratios: FinancingRatios
    quarterly_series: list[FinancingQuarterlySeriesPoint] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    sector_template: str = "finansman"


def analyze_financing(ticker: str, financials_by_period: FinancialsByPeriod) -> FinancingAnalysisResult:
    """Tasarruf Finansman Sirketleri (XI_29K, orn. KTLEV) icin analyze_bank()'in
    karsiligi -- bkz. modul ici ust not. financials_by_period en az 1 donem
    icermelidir."""
    if not financials_by_period:
        raise ValueError("financials_by_period bos olamaz.")

    periods_desc = sorted(financials_by_period.keys(), reverse=True)
    latest_period = periods_desc[0]

    current = financials_by_period.get(latest_period, {})
    yoy_prior = financials_by_period.get(year_ago_period(latest_period), {})
    qoq_prior = financials_by_period.get(previous_quarter_period(latest_period), {})

    income_statement = FinancingIncomeStatementSummary(
        financing_revenue=_line_item_change(
            FIELD_LABELS_TR["financing_revenue"],
            current.get("financing_revenue_cum"),
            yoy_prior.get("financing_revenue_cum"),
        ),
        operating_expenses=_line_item_change(
            FIELD_LABELS_TR["operating_expenses"],
            current.get("operating_expenses_cum"),
            yoy_prior.get("operating_expenses_cum"),
        ),
        net_operating_profit=_line_item_change(
            FIELD_LABELS_TR["net_operating_profit"],
            current.get("net_operating_profit_cum"),
            yoy_prior.get("net_operating_profit_cum"),
        ),
        net_income=_line_item_change(
            FIELD_LABELS_TR["net_income"], current.get("net_income_cum"), yoy_prior.get("net_income_cum")
        ),
    )

    balance_sheet = FinancingBalanceSheetSummary(
        cash=_line_item_change(FIELD_LABELS_TR["cash"], current.get("cash"), qoq_prior.get("cash")),
        overdue_receivables=_line_item_change(
            FIELD_LABELS_TR["overdue_receivables"], current.get("overdue_receivables"), qoq_prior.get("overdue_receivables")
        ),
        total_assets=_line_item_change(
            FIELD_LABELS_TR["total_assets"], current.get("total_assets"), qoq_prior.get("total_assets")
        ),
        equity=_line_item_change(FIELD_LABELS_TR["equity"], current.get("equity"), qoq_prior.get("equity")),
    )

    ttm_financing_revenue = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("financing_revenue_cum")
    )
    ttm_net_income = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("net_income_cum")
    )

    ratios = FinancingRatios(
        net_margin_current=_margin_pct(current.get("net_income_cum"), current.get("financing_revenue_cum")),
        roe_annualized=_margin_pct(ttm_net_income, current.get("equity")),
        return_on_assets_annualized=_margin_pct(ttm_net_income, current.get("total_assets")),
        equity_to_assets_current=_margin_pct(current.get("equity"), current.get("total_assets")),
        ttm_net_income=ttm_net_income,
        ttm_financing_revenue=ttm_financing_revenue,
    )

    series_periods = list(reversed(periods_desc[:5]))
    quarterly_series = [
        FinancingQuarterlySeriesPoint(
            period=p,
            financing_revenue=financials_by_period.get(p, {}).get("financing_revenue"),
            net_income=financials_by_period.get(p, {}).get("net_income"),
        )
        for p in series_periods
    ]

    findings = [
        _finding("financing_revenue", "YoY", current.get("financing_revenue_cum"), yoy_prior.get("financing_revenue_cum")),
        _finding("operating_expenses", "YoY", current.get("operating_expenses_cum"), yoy_prior.get("operating_expenses_cum")),
        _finding(
            "net_operating_profit", "YoY", current.get("net_operating_profit_cum"), yoy_prior.get("net_operating_profit_cum")
        ),
        _finding("net_income", "YoY", current.get("net_income_cum"), yoy_prior.get("net_income_cum")),
        _finding("total_assets", "QoQ", current.get("total_assets"), qoq_prior.get("total_assets")),
        _finding("equity", "QoQ", current.get("equity"), qoq_prior.get("equity")),
    ]

    return FinancingAnalysisResult(
        ticker=ticker,
        latest_period=latest_period,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        ratios=ratios,
        quarterly_series=quarterly_series,
        findings=findings,
    )


@dataclass(frozen=True)
class FinancingValuationMetrics:
    price: Decimal
    share_capital: Decimal
    market_cap: Decimal
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None


def compute_valuation_financing(
    analysis: FinancingAnalysisResult, price: Decimal | None, share_capital: Decimal | None
) -> FinancingValuationMetrics | None:
    """compute_valuation_bank()'in Tasarruf Finansman Sirketi karsiligi --
    AYNI gerekceyle (bkz. compute_valuation_bank docstring'i) SADECE F/K ve
    PD/DD hesaplar, EV bazli carpanlar (FD/FAVOK vb.) YOK."""
    if price is None or share_capital is None:
        return None

    market_cap = price * share_capital
    equity_current = analysis.balance_sheet.equity.current

    return FinancingValuationMetrics(
        price=price,
        share_capital=share_capital,
        market_cap=market_cap,
        pe_ratio=_safe_div(market_cap, analysis.ratios.ttm_net_income),
        pb_ratio=_safe_div(market_cap, equity_current),
    )


@dataclass(frozen=True)
class BankValuationMetrics:
    price: Decimal
    share_capital: Decimal
    market_cap: Decimal
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None


def compute_valuation_bank(
    analysis: BankAnalysisResult, price: Decimal | None, share_capital: Decimal | None
) -> BankValuationMetrics | None:
    """compute_valuation()'nin banka karsiligi -- BILEREK SADECE F/K ve PD/DD
    hesaplar. FD/FAVOK, FD/Hasilat, PD/EFK gibi kurumsal deger (EV) carpanlari
    YOK: bankalar EV/EBITDA ile degerlendirilmez (FAVOK kavrami yok, "net
    borc" da bankalar icin anlamsizdir -- mevduat/kredi zaten bankanin is
    modelinin kendisidir, sanayi sirketi net borc formulune sokulamaz);
    referans kartlarda da (GARAN) bankalar icin sadece F/K ve PD/DD gosterilir."""
    if price is None or share_capital is None:
        return None

    market_cap = price * share_capital
    equity_current = analysis.balance_sheet.equity.current

    return BankValuationMetrics(
        price=price,
        share_capital=share_capital,
        market_cap=market_cap,
        pe_ratio=_safe_div(market_cap, analysis.ratios.ttm_net_income),
        pb_ratio=_safe_div(market_cap, equity_current),
    )


# --- Sigorta (UFRS_K) analiz sonucu -----------------------------------------------------
#
# Bankadaki gibi ayri bir paralel veri modeli: sigorta sirketlerinin gelir
# tablosu (Prim Uretimi/Teknik Gelir/Teknik Denge) ve bilancosu (Esas
# Faaliyetlerden Alacaklar/Borclar, Teknik Karsiliklar) sanayi/banka
# kalemlerinden TAMAMEN FARKLIDIR. Girdi alanlari
# src.bot.pipeline._standardize_to_records_ufrs_k tarafindan yazilir (bkz.
# src/fetchers/isyatirim.py STANDARD_ITEM_MAP_UFRS_K).


@dataclass(frozen=True)
class InsuranceIncomeStatementSummary:
    gross_written_premiums: LineItemChange
    net_premiums_earned: LineItemChange
    technical_income: LineItemChange
    technical_balance: LineItemChange
    net_income: LineItemChange


@dataclass(frozen=True)
class InsuranceBalanceSheetSummary:
    cash_and_financial_assets: LineItemChange
    receivables_from_operations: LineItemChange
    technical_provisions: LineItemChange
    payables_from_operations: LineItemChange
    equity: LineItemChange


@dataclass(frozen=True)
class InsuranceRatios:
    technical_balance_margin_current: Decimal | None  # teknik denge / teknik gelir, yuzde -- scorer.score_insurance()'in teknik_denge_marji_pct girdisi
    # KULLANICI RAPORU (TURSG, 2026-08-03): Skor kartinda "Teknik Denge Marji"
    # HER ZAMAN "trend verisi yok" gosteriyordu -- score_insurance() trend_puan'i
    # SABIT None geciyordu (bkz. scorer.py, artik duzeltildi). gross/ebitda/net
    # marj icin analyze()'nin (sanayi) kullandigi AYNI desen: guncel donemin
    # marjini AYNI ceyregin bir yil onceki (yoy_prior) marjiyla kiyaslar.
    technical_balance_margin_prior_year: Decimal | None
    technical_balance_margin_change_points: Decimal | None
    premium_growth_yoy_pct: Decimal | None  # CEYREKLIK (standalone) prim uretimi YoY buyumesi -- scorer.score_insurance()'in prim_buyumesi_yoy_pct girdisi
    roe_annualized: Decimal | None  # yıllıklandırılmış (TTM net kar / guncel ozkaynak) ozkaynak karliligi, yuzde
    ttm_net_income: Decimal | None


@dataclass(frozen=True)
class InsuranceQuarterlySeriesPoint:
    period: Period
    gross_written_premiums: Decimal | None
    technical_balance: Decimal | None
    net_income: Decimal | None


@dataclass(frozen=True)
class InsuranceAnalysisResult:
    ticker: str
    latest_period: Period
    income_statement: InsuranceIncomeStatementSummary
    balance_sheet: InsuranceBalanceSheetSummary
    ratios: InsuranceRatios
    quarterly_series: list[InsuranceQuarterlySeriesPoint] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    sector_template: str = "sigorta"


def analyze_insurance(ticker: str, financials_by_period: FinancialsByPeriod) -> InsuranceAnalysisResult:
    """Sigorta (UFRS_K) sirketleri icin analyze()'nin karsiligi -- bkz. modul
    ici ust not. financials_by_period en az 1 donem icermelidir."""
    if not financials_by_period:
        raise ValueError("financials_by_period bos olamaz.")

    periods_desc = sorted(financials_by_period.keys(), reverse=True)
    latest_period = periods_desc[0]

    current = financials_by_period.get(latest_period, {})
    yoy_prior = financials_by_period.get(year_ago_period(latest_period), {})
    qoq_prior = financials_by_period.get(previous_quarter_period(latest_period), {})

    income_statement = InsuranceIncomeStatementSummary(
        gross_written_premiums=_line_item_change(
            FIELD_LABELS_TR["gross_written_premiums"],
            current.get("gross_written_premiums_cum"),
            yoy_prior.get("gross_written_premiums_cum"),
        ),
        net_premiums_earned=_line_item_change(
            FIELD_LABELS_TR["net_premiums_earned"],
            current.get("net_premiums_earned_cum"),
            yoy_prior.get("net_premiums_earned_cum"),
        ),
        technical_income=_line_item_change(
            FIELD_LABELS_TR["technical_income"], current.get("technical_income_cum"), yoy_prior.get("technical_income_cum")
        ),
        technical_balance=_line_item_change(
            FIELD_LABELS_TR["technical_balance"], current.get("technical_balance_cum"), yoy_prior.get("technical_balance_cum")
        ),
        net_income=_line_item_change(
            FIELD_LABELS_TR["net_income"], current.get("net_income_cum"), yoy_prior.get("net_income_cum")
        ),
    )

    balance_sheet = InsuranceBalanceSheetSummary(
        cash_and_financial_assets=_line_item_change(
            FIELD_LABELS_TR["cash_and_financial_assets"],
            current.get("cash_and_financial_assets"),
            qoq_prior.get("cash_and_financial_assets"),
        ),
        receivables_from_operations=_line_item_change(
            FIELD_LABELS_TR["receivables_from_operations"],
            current.get("receivables_from_operations"),
            qoq_prior.get("receivables_from_operations"),
        ),
        technical_provisions=_line_item_change(
            FIELD_LABELS_TR["technical_provisions"], current.get("technical_provisions"), qoq_prior.get("technical_provisions")
        ),
        payables_from_operations=_line_item_change(
            FIELD_LABELS_TR["payables_from_operations"],
            current.get("payables_from_operations"),
            qoq_prior.get("payables_from_operations"),
        ),
        equity=_line_item_change(FIELD_LABELS_TR["equity"], current.get("equity"), qoq_prior.get("equity")),
    )

    ttm_net_income = _trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("net_income_cum")
    )
    premium_growth_yoy_pct, _label, _direction = classify_change(
        current.get("gross_written_premiums"), yoy_prior.get("gross_written_premiums")
    )
    # NOT: prim_buyumesi_yoy_pct'in KENDISI zaten bir YoY buyume orani --
    # bunun "trendi" (bir onceki yilin AYNI ceyrekteki buyume oraniyla
    # kiyasi) 2 yil geriye veri gerektirir (n_periods=8 ceyrekle SINIRDA/
    # cogu zaman eksik) ve anlami tartismali (buyume oraninin buyume orani)
    # -- BILEREK hesaplanmadi, industrial _skor_buyume()'de de esdegeri
    # YOK. roe_annualized icin de trend hesaplanmiyor -- bu industrial
    # _skor_ozkaynak_karliligi()'de de (bkz. scorer.py satir ~625) SISTEM
    # GENELINDE boyle, sadece sigortaya ozgu bir eksik DEGIL.
    technical_balance_margin_prior_year = _margin_pct(
        yoy_prior.get("technical_balance"), yoy_prior.get("technical_income")
    )

    ratios = InsuranceRatios(
        technical_balance_margin_current=_margin_pct(current.get("technical_balance"), current.get("technical_income")),
        technical_balance_margin_prior_year=technical_balance_margin_prior_year,
        technical_balance_margin_change_points=_points_diff(
            _margin_pct(current.get("technical_balance"), current.get("technical_income")),
            technical_balance_margin_prior_year,
        ),
        premium_growth_yoy_pct=premium_growth_yoy_pct,
        roe_annualized=_margin_pct(ttm_net_income, current.get("equity")),
        ttm_net_income=ttm_net_income,
    )

    series_periods = list(reversed(periods_desc[:5]))
    quarterly_series = [
        InsuranceQuarterlySeriesPoint(
            period=p,
            gross_written_premiums=financials_by_period.get(p, {}).get("gross_written_premiums"),
            technical_balance=financials_by_period.get(p, {}).get("technical_balance"),
            net_income=financials_by_period.get(p, {}).get("net_income"),
        )
        for p in series_periods
    ]

    findings = [
        _finding(
            "gross_written_premiums", "YoY",
            current.get("gross_written_premiums_cum"), yoy_prior.get("gross_written_premiums_cum"),
        ),
        _finding(
            "net_premiums_earned", "YoY",
            current.get("net_premiums_earned_cum"), yoy_prior.get("net_premiums_earned_cum"),
        ),
        _finding("technical_income", "YoY", current.get("technical_income_cum"), yoy_prior.get("technical_income_cum")),
        _finding("technical_balance", "YoY", current.get("technical_balance_cum"), yoy_prior.get("technical_balance_cum")),
        _finding("net_income", "YoY", current.get("net_income_cum"), yoy_prior.get("net_income_cum")),
        _finding(
            "receivables_from_operations", "QoQ",
            current.get("receivables_from_operations"), qoq_prior.get("receivables_from_operations"),
        ),
        _finding("equity", "QoQ", current.get("equity"), qoq_prior.get("equity")),
    ]

    return InsuranceAnalysisResult(
        ticker=ticker,
        latest_period=latest_period,
        income_statement=income_statement,
        balance_sheet=balance_sheet,
        ratios=ratios,
        quarterly_series=quarterly_series,
        findings=findings,
    )


@dataclass(frozen=True)
class InsuranceValuationMetrics:
    price: Decimal
    share_capital: Decimal
    market_cap: Decimal
    pe_ratio: Decimal | None
    pb_ratio: Decimal | None


def compute_valuation_insurance(
    analysis: InsuranceAnalysisResult, price: Decimal | None, share_capital: Decimal | None
) -> InsuranceValuationMetrics | None:
    """compute_valuation()'nin sigorta karsiligi -- bankadaki gibi BILEREK
    SADECE F/K ve PD/DD hesaplar (EV bazli carpanlar sigorta sirketleri
    icin de standart degerleme yontemi degildir; referans kartta -- ANSGR --
    de sadece Fiyat/Piyasa Degeri/F-K/PD-DD gosterilir)."""
    if price is None or share_capital is None:
        return None

    market_cap = price * share_capital
    equity_current = analysis.balance_sheet.equity.current

    return InsuranceValuationMetrics(
        price=price,
        share_capital=share_capital,
        market_cap=market_cap,
        pe_ratio=_safe_div(market_cap, analysis.ratios.ttm_net_income),
        pb_ratio=_safe_div(market_cap, equity_current),
    )
