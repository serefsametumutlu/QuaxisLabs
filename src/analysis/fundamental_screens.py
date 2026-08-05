"""Faz 21: "Değerleme" ekranı için 3 bağımsız, "elle tutulur" (peer/sektör
GEREKTİRMEYEN, elle güncellenmesi gereken makro varsayım İÇERMEYEN) yöntem
-- SAF matematik, `src.analysis.calculator`/`trends` ile AYNI ilke: bu
modül HİÇBİR I/O yapmaz, `src.fetchers`/`src.db` HİÇBİR modülü import
ETMEZ (01_MIMARI.md katman kuralı).

Kullanıcı isteği (2026-08-05): eski "Değerleme Analizi" panelindeki sektör
karşılaştırması (DB'de az peer varken güvenilmez, "%47,3 ucuz" gibi
istatistiksel olarak anlamsız kesinlik) VE Aswath Damodaran modeli (elle
periyodik güncellenmesi gereken risksiz faiz/özkaynak risk primi
sabitlerine bağımlı, "elle tutulur değil" bulundu) TAMAMEN kaldırıldı --
bunların YERİNE, başarılı değer yatırımcılarının KENDİ, iyi belgelenmiş
yöntemleri araştırılıp seçildi. ÜÇÜ DE SADECE şirketin kendi bilanço/gelir
tablosu/nakit akış verisinden hesaplanır -- peer/sektör/makro sabit
GEREKTİRMEZ:

1. **Joel Greenblatt "Sihirli Formül"** ("The Little Book That Beats the
   Market", 2005) -- Kazanç Getirisi (EBIT/Kurumsal Değer) + Sermaye
   Getirisi (EBIT/(Net Çalışma Sermayesi + Maddi Duran Varlıklar)).
2. **Tobias Carlisle "Acquirer's Multiple"** ("Deep Value" / "The
   Acquirer's Multiple", 2014/2017) -- Kurumsal Değer/EBIT (Greenblatt'in
   TEK ÇARPANLI sadeleştirilmiş hali).
3. **Joseph Piotroski F-Skoru** ("Value Investing: The Use of Historical
   Financial Statement Information to Separate Winners from Losers",
   2000) -- 9 maddelik ikili (0/1) finansal SAĞLIK kontrol listesi
   (değerleme değil KALİTE ölçer -- "ucuz ama kötü şirket" tuzağını
   Greenblatt/Carlisle'ı TAMAMLAYARAK önler).

── VERİ KAYNAĞI (CANLI keşfedildi, 2026-08-05, THYAO ham verisiyle
   doğrulandı -- bkz. isyatirim.py STANDARD_ITEM_MAP_XI_29 üst notu) ──
  - EBIT ≈ TTM Esas Faaliyet Kârı ("3DF" itemCode, calculator.py'nin
    zaten hesapladığı/Fintables ile CANLI doğrulanmış AYNI alan).
  - Kurumsal Değer (FD) = Piyasa Değeri + Net Borç -- `calculator.
    compute_valuation()` ile AYNI formül, burada bağımsız olarak (çağıran
    tarafın hazır bir AnalysisResult'a ihtiyaç duymaması için) yeniden
    hesaplanır ama mantık KOPYALANMAZ: `calculator.net_debt()` public
    sarmalayıcısı kullanılır.
  - Maddi Duran Varlıklar: "1BG" itemCode'u ("Duran Varlıklar" [1AK]
    TOPLAMI DEĞİL -- goodwill/mali yatırım/ertelenmiş vergi varlığı gibi
    operasyonel OLMAYAN kalemleri DIŞLAR, Greenblatt'ın kendi "Net Fixed
    Assets" tanımıyla BİREBİR).
  - İşletme Faaliyetlerinden Nakit Akışı (OCF): "4C" itemCode'u --
    Piotroski'nin kendi "Cash Flow from Operations" kriteriyle BİREBİR.

── KAPSAM SINIRI ──
Greenblatt'ın KENDİ metodolojisi finansal (banka/sigorta/aracı kurum) ve
düzenlemeye tabi (kamu hizmeti) şirketleri BİLİNÇLİ olarak DIŞLAR --
farklı sermaye yapıları FD/EBIT çarpanını anlamsız kılar (bir bankanın
"çalışma sermayesi" kavramı yoktur). Bu modül SADECE BIST XI_29 (sanayi/
ticaret) `financials_by_period` girdisiyle çağrılmalıdır -- çağıran taraf
(pipeline.py) bankacılık/sigorta şirketlerinde bu modülü HİÇ ÇAĞIRMAZ.

NASDAQ/US_GAAP desteği BU FAZIN KAPSAMI DIŞINDA (SEC EDGAR'da 1BG/4C
karşılığı XBRL tag'leri AYRI bir keşif turu gerektirir, Kural 3 gereği
körü körüne eşlenmedi) -- bu modül SADECE BIST verisiyle çağrılmalıdır.

── PİOTROSKİ F-SKORU: EKSİK VERİ DAVRANIŞI (Kural 3) ──
9 kriterden biri için yeterli geçmiş veri YOKSA (örn. 2 yıl öncesine ait
bir dönem hiç yayınlanmamışsa) o kriter SESSİZCE "başarısız" SAYILMAZ --
puanlamadan TAMAMEN ÇIKARILIR. Sonuç "F-Skoru: 6/9" yerine, mevcut
kriterlere göre "F-Skoru: 5/7" gibi gösterilebilir (`criteria_evaluated`
alanı bunu taşır) -- yanlış/eksik bir "6/9" göstermek yerine dürüst bir
kısmi skor tercih edilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.analysis import calculator
from src.analysis.calculator import FinancialsByPeriod, Period

# Greenblatt'in kendi kitabındaki gözlemi: Kazanç Getirisi (Earnings Yield)
# çift haneli (%10+) olan şirketler "ucuz", Sermaye Getirisi (ROC) %25'i
# aşan şirketler "kaliteli" kabul edilir -- Graham'ın 22,5 sabiti gibi bu
# da Greenblatt'in KENDİ, yaygın atıf edilen kaba eşikleridir (bizim
# tercihimiz DEĞİL). Tek bir "ucuz/pahalı" rozeti YERİNE üç seviyeli
# (yüksek/orta/düşük) betimleyici bant kullanılır -- Greenblatt'ın kendi
# yöntemi zaten bir SIRALAMA (ranking) sistemidir, "eşik altı=ucuz" gibi
# ikili bir yargı İDDİA ETMEZ (Kural 2: al/sat sinyali üretilmez).
_EARNINGS_YIELD_HIGH_PCT = Decimal("12")
_EARNINGS_YIELD_LOW_PCT = Decimal("6")
_RETURN_ON_CAPITAL_HIGH_PCT = Decimal("25")
_RETURN_ON_CAPITAL_LOW_PCT = Decimal("10")

# Carlisle'ın kendi geriye dönük testlerinde (bkz. "The Acquirer's
# Multiple") ucuz/pahalı sınırları için sabit bir evrensel eşik YOKTUR
# (kendi calışması decile/onda birlik dilim sıralamasına dayanır, bu
# projede taranmış şirket sayısı bir "evren" oluşturacak kadar büyük
# DEĞİL) -- bunun yerine değer yatırımcılığı literatüründe YAYGIN atıf
# edilen kaba bantlar kullanılır (Graham/Greenblatt'inkiyle AYNI ilke:
# açıkça belgelenmiş, kaynağı gösterilmiş bir kaba sınır, "bizim icat
# ettiğimiz" bir sayı DEĞİL).
_ACQUIRERS_MULTIPLE_CHEAP_CEILING = Decimal("8")
_ACQUIRERS_MULTIPLE_EXPENSIVE_FLOOR = Decimal("15")

# Piotroski'nin KENDİ (2000 makalesi) yorumlama bandı.
_F_SCORE_STRONG_FLOOR_RATIO = Decimal("0.85")  # ~8/9 ve üzeri "güçlü"
_F_SCORE_WEAK_CEILING_RATIO = Decimal("0.3")  # ~2-3/9 ve altı "zayıf"

# Benjamin Graham'in KENDI, 1949'dan beri KLASIK esigi ("The Intelligent
# Investor" -- savunmaci yatirimci icin onerilen F/K x PD/DD tavani, klasik
# ornek F/K 15 x PD/DD 1.5 = 22.5). `src.analysis.valuation.py` icindeki
# AYNI sabitle BIREBIR (iki modul BAGIMSIZ, biri sektor/PEG/Damodaran icin
# eski "Değerleme Analizi" panelinde, digeri bu yeni "Değerleme" ekraninda
# kullanilir -- sabitin kendisi Graham'in KENDI, degismeyen tarihsel
# esigi oldugu icin ayni deger IKI modulde de tekrar tanimlanir).
_GRAHAM_MULTIPLE_CEILING = Decimal("22.5")


@dataclass(frozen=True)
class GreenblattResult:
    ebit: Decimal | None
    enterprise_value: Decimal | None
    earnings_yield_pct: Decimal | None  # EBIT / FD
    earnings_yield_band: str | None  # "Yüksek" | "Orta" | "Düşük"
    net_working_capital: Decimal | None
    net_fixed_assets: Decimal | None
    return_on_capital_pct: Decimal | None  # EBIT / (NWC + Maddi Duran Varlık)
    return_on_capital_band: str | None  # "Yüksek" | "Orta" | "Düşük"


@dataclass(frozen=True)
class AcquirersMultipleResult:
    acquirers_multiple: Decimal | None  # FD / EBIT -- DÜŞÜK = ucuz
    band: str | None  # "Ucuz" | "Makul" | "Pahalı"


@dataclass(frozen=True)
class PiotroskiResult:
    score: int
    criteria_evaluated: int  # yeterli veriyle DEGERLENDIRILEBILEN kriter sayisi (<=9, bkz. modul ust notu)
    band: str | None  # "Güçlü" | "Orta" | "Zayıf" -- criteria_evaluated < 5 ise None (Kural 3: cok az kriterle yorum yapilmaz)
    details: list[tuple[str, bool | None]]  # (kriter adi, 1 mi/0 mi/None=degerlendirilemedi) -- SIRALI, kart bunu listeler


@dataclass(frozen=True)
class GrahamResult:
    graham_multiple: Decimal | None  # F/K x PD/DD -- Graham'ın klasik eşiği 22,5
    fair_value_price: Decimal | None
    upside_pct: Decimal | None
    verdict: str | None  # "Graham Ölçütüne Göre Ucuz" | "...Pahalı"


@dataclass(frozen=True)
class FundamentalScreens:
    has_data: bool
    graham: GrahamResult | None
    greenblatt: GreenblattResult | None
    acquirers_multiple: AcquirersMultipleResult | None
    piotroski: PiotroskiResult | None


def _stock_value(financials_by_period: FinancialsByPeriod, period: Period, field: str) -> Decimal | None:
    return financials_by_period.get(period, {}).get(field)


def _compute_greenblatt(
    financials_by_period: FinancialsByPeriod,
    latest_period: Period,
    price: Decimal | None,
    share_capital: Decimal | None,
) -> tuple[GreenblattResult | None, Decimal | None, Decimal | None]:
    """Döner: (GreenblattResult, ebit, enterprise_value) -- ebit/enterprise_value
    Carlisle Acquirer's Multiple'da da (kopyalanmadan) TEKRAR kullanılsın diye
    ayrıca döndürülür."""
    ebit = calculator.trailing_12m_from_cumulative(
        financials_by_period, latest_period, lambda d: d.get("operating_profit_cum")
    )

    enterprise_value: Decimal | None = None
    if price is not None and share_capital is not None:
        market_cap = price * share_capital
        financial_debt = _stock_value(financials_by_period, latest_period, "financial_debt")
        cash = _stock_value(financials_by_period, latest_period, "cash")
        financial_investments = _stock_value(financials_by_period, latest_period, "financial_investments")
        nd = calculator.net_debt(financial_debt, cash, financial_investments)
        if nd is not None:
            enterprise_value = market_cap + nd

    earnings_yield_pct: Decimal | None = None
    earnings_yield_band: str | None = None
    if ebit is not None and enterprise_value is not None and enterprise_value > 0:
        earnings_yield_pct = ebit / enterprise_value * 100
        if earnings_yield_pct >= _EARNINGS_YIELD_HIGH_PCT:
            earnings_yield_band = "Yüksek"
        elif earnings_yield_pct <= _EARNINGS_YIELD_LOW_PCT:
            earnings_yield_band = "Düşük"
        else:
            earnings_yield_band = "Orta"

    current_assets = _stock_value(financials_by_period, latest_period, "current_assets")
    short_term_liabilities = _stock_value(financials_by_period, latest_period, "short_term_liabilities")
    net_working_capital: Decimal | None = None
    if current_assets is not None and short_term_liabilities is not None:
        net_working_capital = current_assets - short_term_liabilities

    net_fixed_assets = _stock_value(financials_by_period, latest_period, "tangible_fixed_assets")

    return_on_capital_pct: Decimal | None = None
    return_on_capital_band: str | None = None
    if (
        ebit is not None
        and net_working_capital is not None
        and net_fixed_assets is not None
        and (invested_capital := net_working_capital + net_fixed_assets) > 0
    ):
        return_on_capital_pct = ebit / invested_capital * 100
        if return_on_capital_pct >= _RETURN_ON_CAPITAL_HIGH_PCT:
            return_on_capital_band = "Yüksek"
        elif return_on_capital_pct <= _RETURN_ON_CAPITAL_LOW_PCT:
            return_on_capital_band = "Düşük"
        else:
            return_on_capital_band = "Orta"

    if earnings_yield_pct is None and return_on_capital_pct is None:
        return None, ebit, enterprise_value

    return (
        GreenblattResult(
            ebit=ebit,
            enterprise_value=enterprise_value,
            earnings_yield_pct=earnings_yield_pct,
            earnings_yield_band=earnings_yield_band,
            net_working_capital=net_working_capital,
            net_fixed_assets=net_fixed_assets,
            return_on_capital_pct=return_on_capital_pct,
            return_on_capital_band=return_on_capital_band,
        ),
        ebit,
        enterprise_value,
    )


def _compute_graham(own_pe: Decimal | None, own_pb: Decimal | None, current_price: Decimal | None) -> GrahamResult | None:
    """`src.analysis.valuation.compute_valuation_assessment()` içindeki
    Graham bloğuyla BİREBİR AYNI formül (bkz. modül üst notu) -- SEKTÖR
    PEER'İ GEREKTİRMEZ, sadece şirketin kendi F/K + PD/DD'sinden hesaplanır."""
    if own_pe is None or own_pe <= 0 or own_pb is None or own_pb <= 0:
        return None

    graham_multiple = own_pe * own_pb
    verdict = "Graham Ölçütüne Göre Ucuz" if graham_multiple <= _GRAHAM_MULTIPLE_CEILING else "Graham Ölçütüne Göre Pahalı"

    fair_value_price: Decimal | None = None
    upside_pct: Decimal | None = None
    if current_price is not None and current_price > 0:
        fair_value_price = current_price * (_GRAHAM_MULTIPLE_CEILING / graham_multiple).sqrt()
        upside_pct = (fair_value_price - current_price) / current_price * 100

    return GrahamResult(
        graham_multiple=graham_multiple,
        fair_value_price=fair_value_price,
        upside_pct=upside_pct,
        verdict=verdict,
    )


def _compute_acquirers_multiple(ebit: Decimal | None, enterprise_value: Decimal | None) -> AcquirersMultipleResult | None:
    if ebit is None or ebit <= 0 or enterprise_value is None:
        return None
    multiple = enterprise_value / ebit
    if multiple <= _ACQUIRERS_MULTIPLE_CHEAP_CEILING:
        band = "Ucuz"
    elif multiple >= _ACQUIRERS_MULTIPLE_EXPENSIVE_FLOOR:
        band = "Pahalı"
    else:
        band = "Makul"
    return AcquirersMultipleResult(acquirers_multiple=multiple, band=band)


def _ttm_pair(
    financials_by_period: FinancialsByPeriod, latest_period: Period, cum_field: str
) -> tuple[Decimal | None, Decimal | None]:
    """(güncel TTM, 1 yıl önceki TTM) -- Piotroski'nin TÜM YoY kriterleri
    için tek-çeyrek gürültüsü yerine TTM bazlı karşılaştırma kullanılır
    (projenin geri kalanıyla AYNI ilke, bkz. calculator.py Ratios.ttm_*
    alanları)."""
    current_ttm = calculator.trailing_12m_from_cumulative(financials_by_period, latest_period, lambda d: d.get(cum_field))
    prior_period = calculator.year_ago_period(latest_period)
    prior_ttm = calculator.trailing_12m_from_cumulative(financials_by_period, prior_period, lambda d: d.get(cum_field))
    return current_ttm, prior_ttm


def _compute_piotroski(financials_by_period: FinancialsByPeriod, latest_period: Period) -> PiotroskiResult | None:
    prior_period = calculator.year_ago_period(latest_period)

    ttm_net_income, ttm_net_income_prior = _ttm_pair(financials_by_period, latest_period, "net_income_cum")
    ttm_ocf, ttm_ocf_prior = _ttm_pair(financials_by_period, latest_period, "operating_cash_flow_cum")
    ttm_revenue, ttm_revenue_prior = _ttm_pair(financials_by_period, latest_period, "revenue_cum")
    ttm_gross_profit, ttm_gross_profit_prior = _ttm_pair(financials_by_period, latest_period, "gross_profit_cum")

    total_assets = _stock_value(financials_by_period, latest_period, "total_assets")
    total_assets_prior = _stock_value(financials_by_period, prior_period, "total_assets")
    long_term_debt = _stock_value(financials_by_period, latest_period, "long_term_financial_debt")
    long_term_debt_prior = _stock_value(financials_by_period, prior_period, "long_term_financial_debt")
    current_assets = _stock_value(financials_by_period, latest_period, "current_assets")
    current_assets_prior = _stock_value(financials_by_period, prior_period, "current_assets")
    short_term_liabilities = _stock_value(financials_by_period, latest_period, "short_term_liabilities")
    short_term_liabilities_prior = _stock_value(financials_by_period, prior_period, "short_term_liabilities")
    share_capital = _stock_value(financials_by_period, latest_period, "share_capital")
    share_capital_prior = _stock_value(financials_by_period, prior_period, "share_capital")

    details: list[tuple[str, bool | None]] = []

    # 1. ROA > 0 (guncel)
    roa = calculator.safe_div(ttm_net_income, total_assets)
    details.append(("Aktif Kârlılığı (ROA) Pozitif", None if roa is None else roa > 0))

    # 2. Isletme Faaliyetlerinden Nakit Akisi > 0
    details.append(("Faaliyet Nakit Akışı Pozitif", None if ttm_ocf is None else ttm_ocf > 0))

    # 3. ROA arttı (YoY)
    roa_prior = calculator.safe_div(ttm_net_income_prior, total_assets_prior)
    details.append(("ROA Geçen Yıla Göre Arttı", None if (roa is None or roa_prior is None) else roa > roa_prior))

    # 4. Nakit akisi kalitesi: OCF > Net Kar (tahakkuk/accrual kontrolu)
    details.append(
        ("Nakit Akışı Net Kârdan Yüksek (Kazanç Kalitesi)", None if (ttm_ocf is None or ttm_net_income is None) else ttm_ocf > ttm_net_income)
    )

    # 5. Kaldırac azaldi (YoY): uzun vadeli finansal borc / toplam varlik
    leverage = calculator.safe_div(long_term_debt, total_assets)
    leverage_prior = calculator.safe_div(long_term_debt_prior, total_assets_prior)
    details.append(
        ("Uzun Vadeli Kaldıraç Azaldı", None if (leverage is None or leverage_prior is None) else leverage < leverage_prior)
    )

    # 6. Cari oran artti (YoY)
    current_ratio = calculator.safe_div(current_assets, short_term_liabilities)
    current_ratio_prior = calculator.safe_div(current_assets_prior, short_term_liabilities_prior)
    details.append(
        (
            "Cari Oran Arttı (Likidite İyileşti)",
            None if (current_ratio is None or current_ratio_prior is None) else current_ratio > current_ratio_prior,
        )
    )

    # 7. Yeni hisse ihraci yok (sermaye artmadi/sulanma yok)
    details.append(
        ("Pay Sulanması Yok", None if (share_capital is None or share_capital_prior is None) else share_capital <= share_capital_prior)
    )

    # 8. Brut kar marji artti (YoY, TTM bazli)
    gross_margin = calculator.margin_pct(ttm_gross_profit, ttm_revenue)
    gross_margin_prior = calculator.margin_pct(ttm_gross_profit_prior, ttm_revenue_prior)
    details.append(
        ("Brüt Kâr Marjı Arttı", None if (gross_margin is None or gross_margin_prior is None) else gross_margin > gross_margin_prior)
    )

    # 9. Aktif devir hizi artti (YoY): TTM hasilat / toplam varlik
    asset_turnover = calculator.safe_div(ttm_revenue, total_assets)
    asset_turnover_prior = calculator.safe_div(ttm_revenue_prior, total_assets_prior)
    details.append(
        (
            "Aktif Devir Hızı Arttı (Verimlilik)",
            None if (asset_turnover is None or asset_turnover_prior is None) else asset_turnover > asset_turnover_prior,
        )
    )

    evaluated = [d for _label, d in details if d is not None]
    if not evaluated:
        return None

    score = sum(1 for d in evaluated if d)
    criteria_evaluated = len(evaluated)

    band: str | None = None
    if criteria_evaluated >= 5:  # Kural 3: cok az kriterle (<5/9) bir "guclu/zayif" yorumu YAPILMAZ
        ratio = Decimal(score) / Decimal(criteria_evaluated)
        if ratio >= _F_SCORE_STRONG_FLOOR_RATIO:
            band = "Güçlü"
        elif ratio <= _F_SCORE_WEAK_CEILING_RATIO:
            band = "Zayıf"
        else:
            band = "Orta"

    return PiotroskiResult(score=score, criteria_evaluated=criteria_evaluated, band=band, details=details)


def compute_fundamental_screens(
    financials_by_period: FinancialsByPeriod,
    price: Decimal | None,
    share_capital: Decimal | None,
    own_pe: Decimal | None = None,
    own_pb: Decimal | None = None,
) -> FundamentalScreens:
    """Değerleme ekranı için 4 bağımsız yöntemi hesaplar (bkz. modül üst
    notu). `financials_by_period` SADECE BIST XI_29 (sanayi/ticaret)
    şirketi için anlamlıdır -- çağıran taraf (pipeline.py) banka/sigorta/
    NASDAQ şirketlerinde bu fonksiyonu HİÇ ÇAĞIRMAMALIDIR.

    `own_pe`/`own_pb`: SADECE Graham ölçütü için -- çağıran taraf zaten
    `calculator.compute_valuation()` ile hesaplamış olduğu için burada
    TEKRAR hesaplanmaz (Kural: hesaplama mantığı KOPYALANMAZ), sadece
    parametre olarak geçirilir.

    Hiçbiri hesaplanamazsa (`has_data=False`) kart "bu şirket için
    değerleme üretilemiyor" der (Kural 3/9) -- hata FIRLATILMAZ."""
    if not financials_by_period:
        return FundamentalScreens(has_data=False, graham=None, greenblatt=None, acquirers_multiple=None, piotroski=None)

    latest_period = max(financials_by_period.keys())

    graham = _compute_graham(own_pe, own_pb, price)
    greenblatt, ebit, enterprise_value = _compute_greenblatt(financials_by_period, latest_period, price, share_capital)
    acquirers_multiple = _compute_acquirers_multiple(ebit, enterprise_value)
    piotroski = _compute_piotroski(financials_by_period, latest_period)

    has_data = graham is not None or greenblatt is not None or acquirers_multiple is not None or piotroski is not None
    return FundamentalScreens(
        has_data=has_data,
        graham=graham,
        greenblatt=greenblatt,
        acquirers_multiple=acquirers_multiple,
        piotroski=piotroski,
    )
