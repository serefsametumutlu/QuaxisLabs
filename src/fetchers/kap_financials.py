"""KAP (Kamuyu Aydinlatma Platformu) "Finansal Rapor" bildirimlerinden
DOGRUDAN, XBRL taxonomy tag'leriyle etiketlenmis finansal veri ceker.

NEDEN BU MODUL VAR: Is Yatirim'in MaliTablo uc noktasi KAP'ta yayinlanan
bir bilancoyu ISLEYIP kendi API'sine yansitmak icin saatler/gunler
alabiliyor -- CANLI DOGRULANDI: TATGD icin KAP'ta 30.07.2026 19:00'da
2Ç26 "Finansal Rapor"u yayinlandi (bkz. https://www.kap.org.tr/tr/Bildirim/1639813),
ama Is Yatirim ayni gun/ertesi gun hala sadece 1Ç26'yi donduruyordu
(kullanici geri bildirimi: "biz geriden geliyoruz"). Bu modul, botun EN
GUNCEL ceyregi Is Yatirim'in isleme suresini BEKLEMEDEN KAP'tan dogrudan
cekebilmesini saglar.

MIMARI KARAR (bkz. pipeline.py _patch_with_kap_if_fresher): Is Yatirim
BULK/GECMIS veri icin (hizli: 8 ceyrek ~2 istek) KULLANILMAYA DEVAM EDER;
KAP SADECE Is Yatirim'dan DAHA YENI bir Finansal Rapor varsa o TEK ceyregi
"yamalamak" icin kullanilir. 8 ceyregin TAMAMINI KAP'tan cekmek COK YAVAS
olurdu -- her bildirim sayfasi ~5MB (canli dogrulandi, TATGD sayfasi
5.059.449 karakter).

KAP'in bildirim detay sayfasi (https://www.kap.org.tr/tr/Bildirim/{id})
GWT tabanli bir XBRL taxonomy goruntuleyicisidir -- HER finansal satirin
STANDART, MAKINE-OKUNABILIR bir XBRL taxonomy tag'i vardir (orn.
"ifrs-full_Revenue", "ifrs-full_Assets", "kap-fr_..." Turkiye'ye ozgu
uzantilar icin). Bu, Is Yatirim'in opak itemCode semasindan (orn. "3C")
COK DAHA GUVENILIR bir eslesme temelidir -- IFRS taxonomy GLOBAL standarttir,
Turkce metin/etiket degisikliklerinden ETKILENMEZ. Sayfa duz bir httpx.get()
ile (JAVASCRIPT CALISTIRMADAN) cekilebiliyor -- tum veri sunucu tarafinda
render edilmis HTML icinde geliyor (canli dogrulandi).

Bilinen sinirlama (Kural 8: varsayimsal parser yazma): SADECE XI_29
(sanayi/ticaret) sirketleri icin canli TATGD verisiyle dogrulandi. Banka/
sigorta KAP raporlari FARKLI taxonomy uzantilari kullanabilir (BDDK/SGK
duzenleyici semasi), HENUZ dogrulanmadi -- bu sirketler icin bu modul
KULLANILMAMALIDIR (bkz. STANDARD_ITEM_MAP_KAP_XI_29 yorumu).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.fetchers import kap

logger = logging.getLogger(__name__)

Period = tuple[int, int]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.kap.org.tr/",
}

_DISCLOSURE_URL_TEMPLATE = "https://www.kap.org.tr/tr/Bildirim/{disclosure_index}"


# --- Yardimci: yayin tarihinden takvim ceyregi cikarimi -----------------------------------------------------

_QUARTER_END_MONTH_DAY = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}


def _quarter_end_date(year: int, period: int) -> date:
    month, day = _QUARTER_END_MONTH_DAY[period]
    return date(year, month, day)


def _infer_period_from_publish_date(publish_date: datetime, min_lag_days: int = 14) -> Period:
    """Bir Finansal Rapor'un hangi takvim ceyregini raporladigini KAP'in
    (year, kap_period) alanlarina GUVENMEDEN dogrudan yayin tarihinden
    cikarir -- bkz. FinancialReportRef.period docstring'i (kap_period'un
    sirkete gore farkli anlam tasiyabildigi, canli BORSK/TATGD karsilastirmasiyla
    dogrulandi). Bir sirket bir donemi ancak o donem BITTIKTEN SONRA
    raporlayabilir; `min_lag_days` (varsayilan 14) yayin gunu/hemen ertesi
    gun gibi imkansiz bir gecikmeyi eler, publish_date'ten en az bu kadar
    ONCE biten en yakin takvim ceyrek sonunu (Mart/Haziran/Eylul/Aralik)
    doner (isyatirim.guess_last_periods'taki cutoff-tarama deseniyle ayni,
    ama "bugun" yerine bilinen publish_date'ten geriye dogru tarar)."""
    cutoff = publish_date.date() - timedelta(days=min_lag_days)
    year = cutoff.year
    for candidate in (12, 9, 6, 3):
        if _quarter_end_date(year, candidate) <= cutoff:
            return (year, candidate)
    return (year - 1, 12)


# --- Hata siniflari -----------------------------------------------------


class KapFinancialsError(Exception):
    """KAP finansal rapor fetcher'i icin taban hata sinifi."""


class NoFinancialReportFoundError(KapFinancialsError):
    """Ticker icin KAP'ta 'Finansal Rapor' (FR) tipinde bildirim bulunamadi
    (arastirilan tarih penceresinde)."""


class KapFinancialsNetworkError(KapFinancialsError):
    """KAP'a ag seviyesinde ulasilamadi veya yanit beklenmeyen bicimde geldi."""


class KapFinancialsParseError(KapFinancialsError):
    """KAP bildirim sayfasi ayristirilamadi (sayfa yapisi degismis olabilir)."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class FinancialReportRef:
    """Bir 'Finansal Rapor' bildirimine referans (henuz sayfa icerigi CEKILMEDI
    -- bkz. find_latest_financial_report).

    ONEMLI (canli TATGD + BORSK verisiyle dogrulanan bug, duzeltildi): KAP'in
    kendi `kap_period` alani (1/2/3/4) HER SIRKETTE AYNI takvim ceyregine
    karsilik GELMEZ -- TATGD icin kap_period=1 gercekten 1Ç (Mart) iken, BORSK
    icin kap_period=1 GERCEKTE 2Ç'yi (Haziran) temsil ediyor (canli dogrulandi:
    BORSK'in disclosure_index=1639748 raporu, XBRL context tarihleri
    "01.04.2026-30.06.2026" ve PDF eki "BORŞEKER 30.06.2026.pdf" ile 2Ç26
    oldugu KANITLANDI, ama eski `kap_period * 3` formulu bunu YANLISLIKLA
    (2026,3) olarak hesaplayip Is Yatirim'in zaten bildigi donemle AYNI
    sanip KAP tazelik yamasini SESSIZCE ATLIYORDU). Bu yuzden `period` artik
    `kap_period` aritmetigiyle DEGIL, bildirimin KENDI `publish_date`'inden
    (bkz. _infer_period_from_publish_date) cikarilir -- bir sirket ancak bir
    donem BITTIKTEN SONRA o donemi raporlayabilir, bu yuzden "yayin
    tarihinden hemen ONCEKI en yakin takvim ceyrek sonu" sirkete-ozgu
    indeksleme kaymalarindan BAGIMSIZ, guvenilir bir sinyaldir."""

    disclosure_index: int
    year: int
    kap_period: int
    publish_date: datetime

    @property
    def period(self) -> Period:
        return _infer_period_from_publish_date(self.publish_date)


@dataclass(frozen=True)
class RawKapFinancials:
    """KAP Finansal Rapor sayfasindan ayristirilan ham veri. Bilanco
    kalemleri 2 deger (cari donem sonu, onceki YIL SONU) tasir; gelir
    tablosu kalemleri 4 deger tasir (cari kumulatif, onceki yil kumulatif,
    cari CEYREK, onceki yil CEYREGI -- bkz. modul ici not, sira KAP'in
    context-header'inda dogrulandi).

    ONEMLI (canli BORSK arastirmasi sirasinda gozlemlendi, KASITLI olarak
    "duzeltilmedi"): bazi sirketlerin gelir tablosu satirlari icin SADECE
    2 kolon donuyor (4 degil). Bu 2 kolonun anlamini "cari kumulatif +
    onceki yil kumulatif" (bilanco kalipiyla ayni) varsayip kumulatiften
    ceyreklik turetmeyi denedim, ama BORSK'ta bu varsayim YANLIS ciktı --
    donen degerler Is Yatirim'in ZATEN bildigi bir ONCEKI ceyregin
    (1Ç26) rakamlarıyla BIREBIR aynıydı (col-order-class alanları 1/2
    degil 4/5 idi -- yani bu kolonlar sayfanin GENEL context sirasinda
    FARKLI/bilinmeyen bir anlam tasiyor, KARSILASTIRMALI/eski donem verisi
    olabilir). Yanlis (ama makul gorunen) bir rakam uretmek, "N/A" gostermekten
    daha kotu bir hata modudur (Kural 8: emin olunmayan semaya gore
    varsayimsal esleme yazilmaz) -- bu yuzden bu durumda income_cum_value()/
    income_quarterly_value() KASITLI olarak None doner; ilgili skor bilesenleri
    (Kaldirac, ROE) N/A kalir. Sağlam bir cozum icin KAP'in context-header
    tablosunun col-order-class -> gercek tarih eslemesi once ayrica
    dogrulanmali (bu proje asamasinda yapilmadi)."""

    ticker: str
    disclosure_index: int
    period: Period
    balance_sheet_items: dict[str, list[Decimal | None]]
    income_statement_items: dict[str, list[Decimal | None]]

    def balance_value(self, tag: str) -> Decimal | None:
        """CANLI DOGRULANDI (YKBNK konsolide raporu): banka (UFRS) bilanco
        satirlari XI_29'dan FARKLI bir kolon duzeni kullanir -- XI_29'da
        2 kolon [cari, onceki YIL SONU] iken bankalarda 6 kolon [TP_cari,
        YP_cari, TOPLAM_cari, TP_onceki, YP_onceki, TOPLAM_onceki] (TP=Turk
        Parasi, YP=Yabanci Para). 6 kolonlu durumda istenen "cari TOPLAM"
        deger indeks 0 DEGIL indeks 2'dir (kap-fr_Loans/Deposits, ifrs-full_Equity/
        Assets/IssuedCapital icin Fintables'in konsolide rakamlarina TL'ye
        kadar birebir eslesti)."""
        values = self.balance_sheet_items.get(tag)
        if not values:
            return None
        if len(values) == 6:
            return values[2]
        return values[0]

    def income_cum_value(self, tag: str) -> Decimal | None:
        values = self.income_statement_items.get(tag)
        return values[0] if values and len(values) >= 1 else None

    def income_quarterly_value(self, tag: str) -> Decimal | None:
        """4. kolonun degil 3. kolonun (indeks 2) kullanildigina dikkat --
        bkz. modul ici not: kolon sirasi [cari kumulatif, onceki kumulatif,
        cari CEYREK, onceki CEYREK]. KAP bu degeri ZATEN dogrudan verir --
        Is Yatirim'deki gibi kumulatiften cikarma islemi GEREKMEZ."""
        values = self.income_statement_items.get(tag)
        return values[2] if values and len(values) >= 3 else None


# --- Kalem esleme tablosu (SADECE XI_29 - sanayi/ticaret) --------
#
# TATGD'nin 2Ç26 Finansal Rapor'u (bkz. data/exploration/TATGD_kap_*.html)
# ile CANLI dogrulandi -- her XBRL tag'i gercek satirla eslesip deger
# dondurdugu teyit edildi.
STANDARD_ITEM_MAP_KAP_XI_29_BALANCE: dict[str, str] = {
    "cash": "ifrs-full_CashAndCashEquivalents",
    "trade_receivables": "ifrs-full_CurrentTradeReceivables",
    "current_assets": "ifrs-full_CurrentAssets",
    "total_assets": "ifrs-full_Assets",
    "short_term_liabilities": "ifrs-full_CurrentLiabilities",
    "long_term_liabilities": "ifrs-full_NoncurrentLiabilities",
    "share_capital": "ifrs-full_IssuedCapital",
    "equity": "ifrs-full_Equity",
    "long_term_financial_debt": "ifrs-full_LongtermBorrowings",
    # bkz. isyatirim.py STANDARD_ITEM_MAP_XI_29["financial_investments"]
    # yorumu (canli TERA/Fintables karsilastirmasi) -- net borcun nakit-
    # benzeri ikinci bileseni (kisa vadeli menkul kiymet/repo portfoyu).
    "financial_investments": "kap-fr_CurrentFinancialInvestments",
}

STANDARD_ITEM_MAP_KAP_XI_29_INCOME: dict[str, str] = {
    "revenue": "ifrs-full_Revenue",
    "gross_profit": "ifrs-full_GrossProfit",
    "operating_profit": "ifrs-full_ProfitLossFromOperatingActivities",
    "net_income": "ifrs-full_ProfitLossAttributableToOwnersOfParent",
    "net_income_total": "ifrs-full_ProfitLoss",
    # Amortisman/itfa gideri gelir tablosunda AYRI satir olarak gosterilmez
    # (TFRS interim raporlarda genelde fonksiyon bazli gruplanir) -- nakit
    # akis tablosunun "duzeltmeler" bolumunde bulunur, bu yuzden bu haritada
    # degil, ayri bir sabit olarak asagida tanimlanir (bkz. _DEPRECIATION_TAG).
    # "operating_profit_ebitda_base" (Is Yatirim itemCode '3H', FAVOK'un
    # DAR-kavram girdisi) TEK bir KAP tag'i olarak YOK -- 3 tag'in
    # BIRLESIMIYLE turetilir, bu yuzden burada degil asagida
    # _narrow_operating_profit_cum/_quarterly() olarak ayri tanimlanir.
}

# operating_profit_ebitda_base (Is Yatirim '3H', calculator.ebitda()'nin
# GIRDISI) icin TEK bir KAP XBRL tag'i YOK -- CANLI TOASO verisiyle
# dogrulandi (Is Yatirim'in kendi bildirdigi '3H' degeriyle TL'ye kadar
# eslesti): 3H = 3DF (ifrs-full_ProfitLossFromOperatingActivities, GENIS
# "Faaliyet Kari") - 3DD (ifrs-full_OtherIncome, "Diger Faaliyet
# Gelirleri") - 3DE (ifrs-full_OtherExpenseByFunction, "Diger Faaliyet
# Giderleri", KAP'ta ZATEN NEGATIF deger tasir).
_OTHER_OPERATING_INCOME_TAG = "ifrs-full_OtherIncome"
_OTHER_OPERATING_EXPENSE_TAG = "ifrs-full_OtherExpenseByFunction"


def _narrow_operating_profit_cum(raw: "RawKapFinancials") -> Decimal | None:
    """bkz. modul notu (canli TOASO dogrulamasi). UCU tag'den HERHANGI biri
    eksikse KASITLI olarak None doner -- GENIS kavrama (3DF) sessizce
    duşmek, FAVOK icin YANLIS (ama makul gorunen) bir rakam uretir; bu
    "Kural 8" ihlali olur (bkz. proje geneli varsayimsal esleme yasagi)."""
    broad = raw.income_cum_value("ifrs-full_ProfitLossFromOperatingActivities")
    other_income = raw.income_cum_value(_OTHER_OPERATING_INCOME_TAG)
    other_expense = raw.income_cum_value(_OTHER_OPERATING_EXPENSE_TAG)
    if broad is None or other_income is None or other_expense is None:
        return None
    return broad - other_income - other_expense


def _narrow_operating_profit_quarterly(raw: "RawKapFinancials") -> Decimal | None:
    broad = raw.income_quarterly_value("ifrs-full_ProfitLossFromOperatingActivities")
    other_income = raw.income_quarterly_value(_OTHER_OPERATING_INCOME_TAG)
    other_expense = raw.income_quarterly_value(_OTHER_OPERATING_EXPENSE_TAG)
    if broad is None or other_income is None or other_expense is None:
        return None
    return broad - other_income - other_expense


# --- Kalem esleme tablosu (SADECE UFRS - konvansiyonel banka, KONSOLIDE) --------
#
# YKBNK'nin 2Ç26 Finansal Rapor'u (KONSOLIDE varyanti, bkz. find_latest_financial_report
# "Finansal Tablo Niteligi" secimi) ile CANLI dogrulandi -- her deger Fintables'in
# gosterdigi konsolide rakamla TL'ye kadar BIREBIR eslesti (Krediler, Mevduatlar,
# Ozkaynaklar, Beklenen Zarar Karsiliklari, Faiz Gelirleri/Giderleri, Net Ucret
# Komisyon Geliri, Net Faaliyet Kari, Net Donem Kari). Katilim bankalari (UFRS_KATILIM)
# icin HENUZ dogrulanmadi -- FARKLI XBRL tag'leri kullanabilirler (bkz. isyatirim.py
# UFRS_KATILIM notu, "kar payi" vs "faiz" ayrimi), bu yuzden bu harita SADECE
# financial_group=="UFRS" (konvansiyonel banka) icin kullanilmali.
STANDARD_ITEM_MAP_KAP_UFRS_BALANCE: dict[str, str] = {
    "loans": "kap-fr_Loans",
    "deposits": "kap-fr_Deposits",
    "provisions": "kap-fr_AllowanceForExpectedCreditLosses",
    "total_assets": "ifrs-full_Assets",
    "equity": "ifrs-full_Equity",
    "share_capital": "ifrs-full_IssuedCapital",
}

STANDARD_ITEM_MAP_KAP_UFRS_INCOME: dict[str, str] = {
    "interest_income": "kap-fr_InterestIncome",
    "interest_expense": "kap-fr_InterestExpenses",
    "net_fee_income": "kap-fr_FeeAndCommissionIncomeOrExpenses",
    "net_operating_profit": "ifrs-full_ProfitLossFromOperatingActivities",
    "net_income": "ifrs-full_ProfitLossAttributableToOwnersOfParent",
}

# Amortisman/itfa gideri: Nakit Akis Tablosu'ndaki duzeltme kalemi. Gelir
# tablosu kalemlerinin AKSINE bu satir SADECE 2 kolon tasir (cari kumulatif,
# onceki yil kumulatif -- ceyreklik kirilim YOK, nakit akis tablosu TFRS'de
# sadece kumulatif/YTD gosterilir). Bu yuzden _pick_by_value_count(count=2)
# tarafindan "balance_sheet_items" sozlugune duser (isim yaniltici olsa da
# ISLEVSEL olarak dogru) -- raw.balance_value() ile okunur, income_cum_value()
# ILE DEGIL. TATGD ile canli dogrulandi: "Amortisman ve İtfa Gideri İle
# İlgili Düzeltme" = vals=['105943187', '98262723'] (2 kolon).
_DEPRECIATION_TAG = "ifrs-full_AdjustmentsForDepreciationAndAmortisationExpense"


# --- Kalem esleme tablosu (SADECE XI_29K - Tasarruf Finansman Sirketi) --------
#
# KTLEV'in (Katilimevim Tasarruf Finansman A.S.) 2Ç26 Finansal Rapor'u
# (disclosure_index=1645958, 10.08.2026 06:30, "Konsolide Olmayan") ile
# CANLI dogrulandi -- kullanici raporu: "KTLEV 2Ç bilancosu geldi fakat
# hala 1Ç bilanco geliyor" (Is Yatirim henuz islememisti, TATGD/RAYSG ile
# AYNI gecikme deseni). Bilanco satirlari bankadaki gibi 6 kolonlu (TP/YP/
# TOPLAM x cari/onceki) -- balance_column_count=6. TUM 4 bilanco kalemi
# Is Yatirim'in (2025,12) donemiyle TL'YE KADAR BIREBIR eslesti (Nakit
# 8.517.955.658, Ozkaynak 12.456.487.203, Takipteki Alacaklar 71.844.452,
# Aktif Toplami 47.455.977.200 -- HEPSI ✅). Gelir tablosu kalemleri
# (financing_revenue/operating_expenses/net_operating_profit) 4 kolonlu --
# Q1(Is Yatirim'dan BILINEN) + KAP'in kendi Q2-ceyrek kolonu (indeks 2)
# TOPLANINCA KAP'in H1 kumulatifiyle (indeks 0) BIREBIR eslesti (kesin
# dogrulama, HER 3 gelir tablosu kalemi icin ayri ayri yapildi):
#   - financing_revenue (I. Esas Faaliyet Gelirleri, A3A): 4.032.758.951 (Q1)
#     + 5.172.465.863 (Q2) = 9.205.224.814 (H1) ✅
#   - operating_expenses (II. Esas Faaliyet Giderleri, A3ACCA): -1.725.631.994
#     + -2.060.209.377 = -3.785.841.371 ✅
#   - net_operating_profit (VII. Net Faaliyet K/Z, A3AH = I+II+III+IV+V+VI):
#     4.763.274.586 + 28.589.419.373 = 33.352.693.959, KAP'in TEK bir
#     "kap-fr_OperatingProfitLoss" tag'i (I..VI'nin bilesik subtotal'i) ile
#     BIREBIR eslesti ✅
STANDARD_ITEM_MAP_KAP_FINANSMAN_BALANCE: dict[str, str] = {
    "cash": "kap-fr_CashAndCashBalancesAtCentralBanks",
    "overdue_receivables": "kap-fr_NonPerformingReceivables",
    "total_assets": "ifrs-full_Assets",
    "equity": "ifrs-full_Equity",
    "share_capital": "ifrs-full_IssuedCapital",
}

STANDARD_ITEM_MAP_KAP_FINANSMAN_INCOME: dict[str, str] = {
    "financing_revenue": "kap-fr_OperatingIncome",
    "net_operating_profit": "kap-fr_OperatingProfitLoss",
    "operating_expenses": "kap-fr_OperatingExpenses",
    # "3Z" (Is Yatirim, azinlik payi DAHIL toplam) karsiligi -- "ProfitLossAttributableToOwnersOfParent"
    # DEGIL (o "3ZA"nin karsiligidir).
    "net_income": "ifrs-full_ProfitLoss",
}


# --- Kalem esleme tablosu (SADECE UFRS_K - sigorta) --------
#
# RAYSG'nin (Ray Sigorta) 2Ç26 Finansal Rapor'u (disclosure_index=1643198,
# 04.08.2026 20:07, "Konsolide Olmayan") ile CANLI dogrulandi (kullanici
# raporu: RAYSG icin Is Yatirim hala 1Ç26 donduruyordu ama KAP'ta 2Ç26 ZATEN
# vardi -- bkz. modul ust notu, TATGD ile AYNI gecikme deseni).
#
# "net_income": ifrs-full_ProfitLossAttributableToOwnersOfParent = 1.896.687.175
# TL, kullanicinin Fintables'te gordugu "1,9 mr TL" ile BIREBIR eslesti.
# "receivables_from_operations"/"payables_from_operations": KAP'ta bunlar
# ZATEN TEK bir subtotal tag'i olarak geliyor, Is Yatirim'daki gibi elle
# toplama GEREKMEZ -- CANLI dogrulandi: kap-fr_CurrentReceivablesFromMainOperations
# (9.488.764.179) == kap-fr_CurrentReceivablesFromInsuranceOperations
# (9.505.486.027) + kap-fr_ProvisionForCurrentReceivablesFromInsuranceOperations
# (-16.721.848), yani isyatirim'in "1C" (Esas Faaliyetlerden Alacaklar)
# toplamiyla AYNI kapsam (Şüpheli Alacaklar + %100 karşılığı RAYSG'de
# birbirini tam gotürdüğü icin subtotal'a etkisi yok); ayni sekilde
# kap-fr_ShortTermPayablesFromMainOperations (5.620.763.851) ==
# kap-fr_ShortTermPayablesFromInsuranceOperations (digerleri 0) --
# isyatirim'in "2B" (Esas Faaliyetlerden Borçlar) toplamiyla AYNI kapsam.
# Digger alanlar (asagidaki tekil-tag OLMAYAN yardimcilar) icin bkz.
# _cash_and_equivalents_ufrs_k/_financial_assets_ufrs_k/
# _technical_provisions_noncurrent_ufrs_k/_technical_balance_*_ufrs_k.
STANDARD_ITEM_MAP_KAP_UFRS_K_BALANCE: dict[str, str] = {
    "equity": "ifrs-full_Equity",
    "share_capital": "ifrs-full_IssuedCapital",
    "receivables_from_operations": "kap-fr_CurrentReceivablesFromMainOperations",
    "payables_from_operations": "kap-fr_ShortTermPayablesFromMainOperations",
}

STANDARD_ITEM_MAP_KAP_UFRS_K_INCOME: dict[str, str] = {
    "gross_written_premiums": "kap-fr_GrossWrittenPremiumsClassifiedAsNonlifeTechnicalIncome",
    "net_premiums_earned": "kap-fr_WrittenPremiumsClassifiedAsNonlifeTechnicalIncomeNetOfReinsurerShare",
    "technical_income": "kap-fr_NonlifeTechnicalIncome",
    "net_income": "ifrs-full_ProfitLossAttributableToOwnersOfParent",
}

# technical_income'in "B- Hayat Disi Teknik Gider(-)" karsiligi -- SADECE
# technical_balance hesaplamak icin kullanilir (isyatirim.py'deki
# STANDARD_ITEM_MAP_UFRS_K["technical_expense"] ile AYNI amac), tek basina
# ayri bir alan olarak DB'ye YAZILMAZ.
_TECHNICAL_EXPENSE_TAG_UFRS_K = "kap-fr_NonlifeTechnicalExpense"

# isyatirim "1B" (B- Finansal Varlıklar ile Riski Sigortalılara Ait Finansal
# Yatırımlar) karsiligi -- CANLI dogrulandi: bu TEK tag zaten kendi alt
# kalemlerinin (AvailableForSaleCurrentFinancialAssets + CurrentFinancial
# InvestmentsHeldToMaturity + CurrentFinancialAssetsHeldForTrading, RAYSG'de
# digerleri 0) TOPLAMINA ESIT (5.983.337.894 = 0 + 4.273.074.553 +
# 1.710.263.341) -- yani KAP sayfasinda ZATEN hazir bir subtotal, elle
# toplama GEREKMEZ.
_FINANCIAL_ASSETS_TAG_UFRS_K = "kap-fr_FinancialAssetsAndFinancialInvestmentsWithRisksOnPolicyholders"

# isyatirim "1A" (A- Nakit Ve Nakit Benzeri Varlıklar) karsiligi -- isyatirim
# semasinda "Banka Garantili ve Uç Aydan Kısa Vadeli Kredi Kartı Alacakları"
# (1AE) bu toplamin bir PARCASIDIR (bkz. isyatirim.py STANDARD_ITEM_MAP_UFRS_K
# "cash_and_equivalents":"1A" yorumu) -- KAP sayfasinda ise
# ifrs-full_CashAndCashEquivalents'tan AYRI bir sibling satir olarak
# gelistigi icin (CROSS-PERIOD dogrulanamadi, Is Yatirim henuz 2Ç26'yi
# donmuyor) BURADA ELLE toplanir; bu FinansalAssets'in aksine subtotal
# olarak dogrulanmamis bir tahmin -- yanlis olma riski digerlerinden
# YUKSEK ama TAMAMEN N/A birakmaktan (bkz. kullanici geri bildirimi:
# "her sey eksik, bu sekilde olmaz") daha az kotu kabul edildi.
_CASH_TAGS_UFRS_K: tuple[str, ...] = (
    "ifrs-full_CashAndCashEquivalents",
    "kap-fr_BankGuaranteedCreditCardReceivablesWithMaturitiesLessThanThreeMonths",
    "ifrs-full_OtherCashAndCashEquivalents",
)

# isyatirim "2MD" (uzun vadeli Sigortacılık Teknik Karşılıkları) karsiligi --
# ayni sekilde CROSS-PERIOD dogrulanamadi (bkz. _CASH_TAGS_UFRS_K notu),
# "IV- Uzun Vadeli Yükümlülükler" grubu altindaki iki teknik karsilik
# satirinin (Sigortacilik + Diger) toplami olarak en-yakin karsilik kabul
# edildi.
_TECHNICAL_PROVISIONS_NONCURRENT_TAGS_UFRS_K: tuple[str, ...] = (
    "kap-fr_LongTermInsuranceTechnicalProvisions",
    "kap-fr_OtherLongTermTechnicalProvisions",
)

# isyatirim "2E" (kisa vadeli Sigortacılık Teknik Karşılıkları) karsiligi --
# CANLI dogrulandi: RAYSG 1Ç26'da isyatirim "2E" toplami (23.133.721.147)
# ile KAP 2Ç26 kap-fr_ShortTermInsuranceTechnicalProvisions (23.793.992.654)
# BUYUKLUK MERTEBESI olarak tutarli (bir ceyrekte %2-3 artis makul).
_TECHNICAL_PROVISIONS_CURRENT_TAG_UFRS_K = "kap-fr_ShortTermInsuranceTechnicalProvisions"


def _sum_balance_tags_ufrs_k(raw: "RawKapFinancials", tags: tuple[str, ...]) -> Decimal | None:
    values = [raw.balance_value(tag) for tag in tags]
    if all(v is None for v in values):
        return None
    return sum((v for v in values if v is not None), Decimal(0))


def _cash_and_equivalents_ufrs_k(raw: "RawKapFinancials") -> Decimal | None:
    return _sum_balance_tags_ufrs_k(raw, _CASH_TAGS_UFRS_K)


def _technical_provisions_noncurrent_ufrs_k(raw: "RawKapFinancials") -> Decimal | None:
    return _sum_balance_tags_ufrs_k(raw, _TECHNICAL_PROVISIONS_NONCURRENT_TAGS_UFRS_K)


def _technical_balance_cum_ufrs_k(raw: "RawKapFinancials") -> Decimal | None:
    """isyatirim.technical_balance_ufrs_k()'nin KAP karsiligi -- Teknik Gelir
    + Teknik Gider (KAP'ta da ZATEN negatif isaretle gelir). CANLI dogrulandi:
    16.200.719.584 + (-13.958.520.691) = 2.242.198.893, sayfadaki hazir
    "kap-fr_TechnicalPartBalanceNonlife" satiriyla (2.242.198.893) BIREBIR
    eslesti."""
    income = raw.income_cum_value(STANDARD_ITEM_MAP_KAP_UFRS_K_INCOME["technical_income"])
    expense = raw.income_cum_value(_TECHNICAL_EXPENSE_TAG_UFRS_K)
    if income is None and expense is None:
        return None
    return (income or Decimal(0)) + (expense or Decimal(0))


def _technical_balance_quarterly_ufrs_k(raw: "RawKapFinancials") -> Decimal | None:
    income = raw.income_quarterly_value(STANDARD_ITEM_MAP_KAP_UFRS_K_INCOME["technical_income"])
    expense = raw.income_quarterly_value(_TECHNICAL_EXPENSE_TAG_UFRS_K)
    if income is None and expense is None:
        return None
    return (income or Decimal(0)) + (expense or Decimal(0))

# Kisa vadeli finansal borc TEK bir XBRL tag'i olarak raporlanmiyor --
# ilişkili/ilişkili olmayan taraflardan kisa vadeli borclanmalar + uzun
# vadeli borclanmalarin kisa vadeli kismi (TUMU "kap-fr_" Turkiye'ye ozgu
# uzantilar) TOPLANARAK hesaplanir. TATGD ile canli dogrulandi.
_SHORT_TERM_DEBT_TAGS: tuple[str, ...] = (
    "kap-fr_CurrentBorrowingsFromRelatedParties",
    "kap-fr_OtherShortTermBorrowingsFromRelatedParties",
    "kap-fr_CurrentBorrowingsFromUnrelatedParties",
    "kap-fr_OtherShortTermBorrowingsFromUnrelatedParties",
    "kap-fr_CurrentPortionOfNoncurrentBorrowingsFromRelatedParties",
    "kap-fr_CurrentPortionOfOtherLongTermBorrowingsFromRelatedParties",
    "kap-fr_CurrentPortionOfNoncurrentBorrowingsFromUnrelatedParties",
    "kap-fr_CurrentPortionOfOtherLongTermBorrowingsFromUnrelatedParties",
)


# --- HTTP + arama katmani -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _fetch_disclosures_raw(member_oid: str, days: int) -> list[dict]:
    """kap.py'nin Disclosure modeline DONUSTURMEDEN (year/period/disclosureIndex
    kaybolmasin diye) KAP bildirim listesi uc noktasini DOGRUDAN cagirir."""
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    body = {
        "fromDate": from_date.isoformat(),
        "toDate": to_date.isoformat(),
        "mkkMemberOidList": [member_oid],
    }
    try:
        response = httpx.post(kap.DISCLOSURES_ENDPOINT, json=body, headers=kap._HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("KAP bildirim listesi istegi basarisiz, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise KapFinancialsNetworkError(f"KAP beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    payload = response.json()
    if not isinstance(payload, list):
        raise KapFinancialsNetworkError("KAP bildirim yaniti beklenmeyen bicimde (liste degil).")
    return payload


def find_latest_financial_report(ticker: str, days: int = 365) -> FinancialReportRef | None:
    """Bir hissenin KAP'ta yayinlanmis EN GUNCEL 'Finansal Rapor' (FR)
    bildirimini bulur. Bulunamazsa (son `days` gunde hic FR yoksa) None
    doner -- bu bir hata DEGILDIR, cagiran taraf Is Yatirim'e guvenmeye
    devam eder.

    ONEMLI (canli TATGD verisiyle dogrulanan hata): `disclosureClass=="FR"`
    TEK BASINA YETERLI DEGIL -- KAP ayni "6 Aylik" pakette Finansal Rapor'la
    AYNI ANDA "Faaliyet Raporu (Konsolide)" ve "Sorumluluk Beyani (Konsolide)"
    bildirimlerini de disclosureClass="FR" olarak isaretliyor (bunlar XBRL
    veri ICERMEZ -- Sorumluluk Beyani sadece ~5 taxonomy tag'i tasiyan 140KB'lik
    bir imza sayfasi). Gercek finansal tablo satirlarini SADECE
    `disclosureCategory=="FR"` (subject="Finansal Rapor") tasiyan bildirim
    icerir -- bu filtre olmadan ayni (year,period) icin siralama esitligi
    (sort tie) bazen yanlislikla Sorumluluk Beyani'ni "en yeni" secip, o
    bildirimden HICBIR standart alan cikaramadigimiz icin (kap_patch_records
    bos kalir) donem sessizce Is Yatirim'in eski ceyreginde kalirdi.

    ONEMLI: `days` 365'i GECMEMELI -- CANLI DOGRULANDI, KAP'in bildirim
    listesi uc noktasi (/api/disclosure/members/byCriteria) 400 GUNLUK bir
    tarih araligiyla sorulunca HTTP 500 donuyor (365 gun sorunsuz calisiyor).
    365 gun zaten yilda ~4 kez yayinlanan Finansal Rapor'lardan en az
    birkacini yakalamaya yeter.

    KONSOLIDE/SOLO SECIMI (CANLI DOGRULANDI, YKBNK 31.07.2026): bankalar AYNI
    ceyrek icin ~1 dakika arayla IKI AYRI Finansal Rapor yayinliyor (biri
    Konsolide, biri Konsolide Olmayan/solo) -- (year,period) esitliginde
    (sort tie) birden fazla aday varsa, HER birinin sayfasini cekip
    "Finansal Tablo Niteligi" basligindan Konsolide olani tercih eder
    (Fintables/kamuya acik kaynaklarin gosterdigi konsolide rakamlarla
    tutarli olsun diye). Hicbiri "Konsolide" olarak isaretlenmemisse (veya
    sayfa cekilemezse) en yuksek disclosureIndex'e (en son yayinlanan) sahip
    olan kullanilir -- bu ek adim SADECE tek adaydan fazlasi oldugunda
    (ekstra sayfa fetch'i gerektirdigi icin) calisir.

    Hatalar:
        kap.KapCompanyNotFoundError: Hisse kodu KAP'ta bulunamadi.
        KapFinancialsNetworkError: Ag hatasi.
    """
    company = kap.search_company(ticker)
    rows = _fetch_disclosures_raw(company.member_oid, days)

    fr_rows = [r for r in rows if r.get("disclosureCategory") == "FR" and r.get("year") and r.get("period")]
    if not fr_rows:
        return None

    fr_rows.sort(key=lambda r: (r["year"], r["period"]), reverse=True)
    newest_key = (fr_rows[0]["year"], fr_rows[0]["period"])
    candidates = [r for r in fr_rows if (r["year"], r["period"]) == newest_key]

    newest = candidates[0]
    if len(candidates) > 1:
        candidates.sort(key=lambda r: r["disclosureIndex"], reverse=True)
        newest = candidates[0]
        for candidate in candidates:
            try:
                html = fetch_disclosure_html(candidate["disclosureIndex"])
            except Exception as exc:  # noqa: BLE001 -- tek bir adayin sayfasi cekilemese bile digerleri denenmeli
                logger.warning(
                    "%s icin disclosure_index=%s Konsolide/Solo kontrolu icin cekilemedi: %s",
                    ticker, candidate["disclosureIndex"], exc,
                )
                continue
            if _report_variant(html) == "Konsolide":
                newest = candidate
                break

    return FinancialReportRef(
        disclosure_index=newest["disclosureIndex"],
        year=newest["year"],
        kap_period=newest["period"],
        publish_date=datetime.strptime(newest["publishDate"], "%d.%m.%Y %H:%M:%S"),
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def fetch_disclosure_html(disclosure_index: int) -> str:
    """Bir KAP bildirim sayfasinin TAM HTML'ini ceker (JAVASCRIPT calismaz,
    saf httpx.get() -- canli dogrulandi: veri sunucu tarafinda render
    edilmis HTML icinde geliyor). Sayfalar buyuk olabilir (~5MB, TATGD ile
    dogrulandi). Rapor-turune OZGU DEGILDIR -- Finansal Rapor sayfalari icin
    bu modul icinde, Finansal Takvim sayfalari icin src/fetchers/
    earnings_calendar.py'de kullanilir (ONCEDEN '_fetch_report_html' adiyla
    SADECE bu modulde ozeldi, Faz 12'de genel kullanima acildi)."""
    url = _DISCLOSURE_URL_TEMPLATE.format(disclosure_index=disclosure_index)
    try:
        response = httpx.get(url, headers=_HEADERS, timeout=max(config.HTTP_TIMEOUT_SECONDS, 30), follow_redirects=True)
    except httpx.RequestError as exc:
        logger.warning("KAP bildirim sayfasi istegi basarisiz, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise KapFinancialsNetworkError(f"KAP beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    return response.text


# --- HTML ayristirma -----------------------------------------------------


def _parse_decimal(raw: str | None) -> Decimal | None:
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


# --- Sunum para birimi (olcek) -----------------------------------------------------
#
# CANLI DOGRULANDI (canli hata, OTKAR raporu): KAP Finansal Rapor sayfasi
# HER sirket icin AYNI parasal olcekte DEGIL -- sayfanin ust bilgisindeki
# "Sunum Para Birimi" satiri sirkete gore "TL" (x1), "1.000 TL" (Bin TL,
# x1.000) veya "1.000.000 TL" (Milyon TL, x1.000.000) olabilir:
#   - TATGD (bu modulun ilk canli dogrulamasinda kullanilan sirket) = "TL"
#     -- olcek etkisi YOK, bu yuzden orijinal parser (olceklemesiz) TATGD
#     icin TESADUFEN dogru sonuc veriyordu.
#   - OTKAR = "1.000 TL" -- olceklemesiz parser TUM rakamlari (sermaye,
#     hasilat, toplam varliklar, vb.) 1000 KAT KUCUK kaydediyordu (canli
#     hata: sermaye 120.000.000 yerine 120.000 olarak kaydedildi).
#   - YKBNK (banka, konsolide) = "1.000.000 TL".
# Bu bilgi sayfanin GERCEK HTML DOM'unda degil, sayfa icine gomulu bir
# JS/JSON-escaped metin blogunda (< / > kacis dizileriyle) yer
# aliyor -- BeautifulSoup'a değil, ham yanit metnine dogrudan regex
# uygulamak GUVENILIR (3 farkli canli sirkette dogrulandi).
_PRESENTATION_CURRENCY_RE = re.compile(
    r"Sunum Para Birimi.{0,60}?(1\.000\.000 TL|1\.000 TL|TL)", re.DOTALL
)
_CURRENCY_UNIT_MULTIPLIERS: dict[str, Decimal] = {
    "TL": Decimal(1),
    "1.000 TL": Decimal(1000),
    "1.000.000 TL": Decimal(1_000_000),
}


def _extract_presentation_currency_scale(html: str) -> Decimal:
    """KAP sayfasinin "Sunum Para Birimi" basligindan olcek carpanini cikarir.
    Bulunamazsa (sayfa yapisi degismis olabilir) GUVENLI varsayilan olarak
    x1 (TL) doner VE uyari loglar -- yanlislikla KUCUK bir carpanla devam
    etmek (orn. hep x1 varsaymak), COK BUYUK bir carpanla devam etmekten
    (orn. sirkette olmayan bir olcek uydurmak) DAHA GUVENLIDIR."""
    unescaped = html.replace("\\u003c", "<").replace("\\u003e", ">")
    match = _PRESENTATION_CURRENCY_RE.search(unescaped)
    if match is None:
        logger.warning("KAP sayfasinda 'Sunum Para Birimi' bulunamadi, varsayilan olcek (TL, x1) kullanilacak.")
        return Decimal(1)
    return _CURRENCY_UNIT_MULTIPLIERS[match.group(1)]


_REPORT_VARIANT_RE = re.compile(r"Finansal Tablo Niteliği.{0,60}?(Konsolide Olmayan|Konsolide)", re.DOTALL)


def _report_variant(html: str) -> str | None:
    """Sayfanin 'Finansal Tablo Niteligi' basligindan 'Konsolide' veya
    'Konsolide Olmayan' bilgisini okur. CANLI DOGRULANDI (YKBNK, 31.07.2026):
    bankalar AYNI ceyrek icin 1 dakika arayla İKİ AYRI Finansal Rapor
    yayinliyor (biri Konsolide, biri Konsolide Olmayan/solo) -- bkz.
    find_latest_financial_report. Bulunamazsa None doner."""
    unescaped = html.replace("\\u003c", "<").replace("\\u003e", ">")
    match = _REPORT_VARIANT_RE.search(unescaped)
    return match.group(1).strip() if match else None


def _scale_rows(
    rows: list[tuple[str, list[Decimal | None]]], scale: Decimal
) -> list[tuple[str, list[Decimal | None]]]:
    if scale == Decimal(1):
        return rows
    return [(tag, [v * scale if v is not None else None for v in values]) for tag, values in rows]


def _extract_rows(soup: BeautifulSoup) -> list[tuple[str, list[Decimal | None]]]:
    """Sayfadaki TUM 'data-input-row' satirlarindan (tag, [degerler]) ciftleri
    cikarir. AYNI tag birden fazla tabloda (orn. Bilanco VE Ozkaynak Degisim
    Tablosu) tekrar edebilir -- cagiran taraf (balance_value/income_*_value
    yardimcilarindan ONCE _pick_by_value_count) beklenen kolon sayisina
    (2=bilanco, 4=gelir tablosu) gore doğru satiri secer."""
    results: list[tuple[str, list[Decimal | None]]] = []
    for row in soup.select("tr.data-input-row"):
        name_div = row.select_one(".taxonomy-field-name")
        if not name_div:
            continue
        tag = name_div.text.split("|")[0].strip()
        if not tag:
            continue
        values: list[Decimal | None] = []
        for cell in row.select(".taxonomy-context-value"):
            val_div = cell.select_one(".taxonomy-label-field")
            title = val_div.get("title") if val_div else None
            values.append(_parse_decimal(title))
        results.append((tag, values))
    return results


def _pick_by_value_count(rows: list[tuple[str, list[Decimal | None]]], expected_count: int) -> dict[str, list[Decimal | None]]:
    """Ayni tag icin BIRDEN FAZLA satir varsa (bkz. _extract_rows notu),
    beklenen kolon sayisiyla (2 bilanco / 4 gelir tablosu) eslesen ILK
    satiri kullanir -- boylece orn. Ozkaynak Degisim Tablosu'ndaki (40+
    kolonlu) 'ifrs-full_Equity' tekrarindan ETKILENMEZ."""
    picked: dict[str, list[Decimal | None]] = {}
    for tag, values in rows:
        if tag in picked:
            continue
        if len(values) == expected_count:
            picked[tag] = values
    return picked


def parse_financial_report(
    html: str, ticker: str, disclosure_index: int, period: Period, *, balance_column_count: int = 2
) -> RawKapFinancials:
    """KAP Finansal Rapor sayfasinin HTML'ini ayristirir. Sayfa yapisi
    degismisse (KAP guncelleme yaparsa) BeautifulSoup sessizce bos sonuc
    dondurebilir -- bu yuzden HICBIR satir bulunamazsa KapFinancialsParseError
    firlatilir (cagiran taraf Is Yatirim'e guvenmeye devam eder).

    `balance_column_count`: XI_29 icin 2 (varsayilan), UFRS/banka icin 6
    (bkz. RawKapFinancials.balance_value docstring'i, TP/YP/Toplam kolon
    duzeni) -- fetch_latest_ufrs_financials bunu 6 ile cagirir."""
    soup = BeautifulSoup(html, "html.parser")
    rows = _extract_rows(soup)
    if not rows:
        raise KapFinancialsParseError(
            f"KAP bildirim sayfasi (disclosure_index={disclosure_index}) ayristirilamadi: "
            "hicbir 'data-input-row' bulunamadi (sayfa yapisi degismis olabilir)."
        )

    scale = _extract_presentation_currency_scale(html)
    if scale != Decimal(1):
        logger.info(
            "disclosure_index=%s icin sunum para birimi olceklemesi uygulandi: x%s", disclosure_index, scale
        )
        rows = _scale_rows(rows, scale)

    balance_sheet_items = _pick_by_value_count(rows, expected_count=balance_column_count)
    income_statement_items = _pick_by_value_count(rows, expected_count=4)

    return RawKapFinancials(
        ticker=ticker,
        disclosure_index=disclosure_index,
        period=period,
        balance_sheet_items=balance_sheet_items,
        income_statement_items=income_statement_items,
    )


def fetch_latest_xi29_financials(ticker: str) -> RawKapFinancials | None:
    """Bir XI_29 (sanayi/ticaret) hissesi icin KAP'taki EN GUNCEL Finansal
    Rapor'u bulur, ceker ve ayristirir. Uygun bir rapor yoksa (veya
    ayristirma basarisiz olursa) None doner -- HICBIR ISTISNA disariya
    SIZMAZ (bu fonksiyon SADECE bir "tazelik yamasi" saglar, ana veri
    kaynagi degildir; herhangi bir hata cagiran tarafi Is Yatirim'e
    guvenmeye devam etmeye yonlendirmelidir)."""
    try:
        ref = find_latest_financial_report(ticker)
        if ref is None:
            return None
        html = fetch_disclosure_html(ref.disclosure_index)
        return parse_financial_report(html, ticker, ref.disclosure_index, ref.period)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring: tazelik yamasi ASLA pipeline'i BLOKE ETMEMELI
        logger.warning("%s icin KAP'tan tazelik yamasi cekilemedi (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return None


def fetch_latest_ufrs_k_financials(ticker: str) -> RawKapFinancials | None:
    """fetch_latest_xi29_financials()'in sigorta (UFRS_K) karsiligi -- SADECE
    UFRS_K icin (bkz. STANDARD_ITEM_MAP_KAP_UFRS_K_* modul notu). RAYSG (solo/
    "Konsolide Olmayan") ile CANLI dogrulandi: bilanco satirlari XI_29 gibi 2
    kolonlu (banka gibi 6 kolonlu DEGIL) -- balance_column_count VARSAYILANI
    (2) kullanilir. Uygun bir rapor yoksa (veya ayristirma basarisiz olursa)
    None doner -- HICBIR ISTISNA disariya SIZMAZ (bkz. fetch_latest_xi29_financials
    docstring'i, ayni ilke)."""
    try:
        ref = find_latest_financial_report(ticker)
        if ref is None:
            return None
        html = fetch_disclosure_html(ref.disclosure_index)
        return parse_financial_report(html, ticker, ref.disclosure_index, ref.period)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring: tazelik yamasi ASLA pipeline'i BLOKE ETMEMELI
        logger.warning("%s icin KAP'tan (UFRS_K) tazelik yamasi cekilemedi (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return None


def fetch_latest_ufrs_financials(ticker: str) -> RawKapFinancials | None:
    """fetch_latest_xi29_financials()'in konvansiyonel banka (UFRS) karsiligi
    -- SADECE UFRS icin (bkz. STANDARD_ITEM_MAP_KAP_UFRS_* modul notu,
    UFRS_KATILIM HENUZ dogrulanmadi). Balans tablosu 6 kolonlu oldugu icin
    parse_financial_report'a balance_column_count=6 gecirir. Uygun bir rapor
    yoksa (veya ayristirma basarisiz olursa) None doner -- HICBIR ISTISNA
    disariya SIZMAZ (bkz. fetch_latest_xi29_financials docstring'i, ayni ilke)."""
    try:
        ref = find_latest_financial_report(ticker)
        if ref is None:
            return None
        html = fetch_disclosure_html(ref.disclosure_index)
        return parse_financial_report(html, ticker, ref.disclosure_index, ref.period, balance_column_count=6)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring: tazelik yamasi ASLA pipeline'i BLOKE ETMEMELI
        logger.warning("%s icin KAP'tan (UFRS) tazelik yamasi cekilemedi (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return None


def fetch_latest_financing_financials(ticker: str) -> RawKapFinancials | None:
    """fetch_latest_xi29_financials()'in Tasarruf Finansman Sirketi (XI_29K,
    orn. KTLEV) karsiligi -- SADECE XI_29K icin (bkz. STANDARD_ITEM_MAP_KAP_FINANSMAN_*
    modul notu). Bilanco tablosu bankadaki gibi 6 kolonlu oldugu icin
    parse_financial_report'a balance_column_count=6 gecirir. Uygun bir rapor
    yoksa (veya ayristirma basarisiz olursa) None doner -- HICBIR ISTISNA
    disariya SIZMAZ (bkz. fetch_latest_xi29_financials docstring'i, ayni ilke)."""
    try:
        ref = find_latest_financial_report(ticker)
        if ref is None:
            return None
        html = fetch_disclosure_html(ref.disclosure_index)
        return parse_financial_report(html, ticker, ref.disclosure_index, ref.period, balance_column_count=6)
    except Exception as exc:  # noqa: BLE001 -- bkz. docstring: tazelik yamasi ASLA pipeline'i BLOKE ETMEMELI
        logger.warning("%s icin KAP'tan (Tasarruf Finansman) tazelik yamasi cekilemedi (Is Yatirim verisiyle devam edilecek): %s", ticker, exc)
        return None


# --- Standart alan erisimi -----------------------------------------------------


def standardized_record_values(raw: RawKapFinancials) -> dict[str, Decimal | None]:
    """RawKapFinancials'i pipeline.py'nin bekledigi standart alan adlarina
    (revenue, revenue_cum, total_assets, vb.) cevirir -- calculator.py'nin
    XI_29 semasiyla BIREBIR ayni alan adlari kullanilir."""
    out: dict[str, Decimal | None] = {}

    for field, tag in STANDARD_ITEM_MAP_KAP_XI_29_BALANCE.items():
        out[field] = raw.balance_value(tag)

    for field, tag in STANDARD_ITEM_MAP_KAP_XI_29_INCOME.items():
        out[f"{field}_cum"] = raw.income_cum_value(tag)
        out[field] = raw.income_quarterly_value(tag)

    # FAVOK'un DAR-kavram girdisi (bkz. modul notu, canli TOASO dogrulamasi) --
    # tek bir KAP tag'i degil, 3 tag'in birlesimi.
    out["operating_profit_ebitda_base_cum"] = _narrow_operating_profit_cum(raw)
    out["operating_profit_ebitda_base"] = _narrow_operating_profit_quarterly(raw)

    # SADECE kumulatif deger doner -- KAP bu kalem icin ceyreklik kirilim
    # VERMEZ (bkz. _DEPRECIATION_TAG yorumu). Ceyreklik (tek ceyrek) deger
    # BURADA turetilemiyor (onceki ceyregin kumulatif D&A degeri bu tek
    # kayitta YOK) -- pipeline.py'deki birlestirme adimi, ONCEKI ceyregin
    # (Is Yatirim'dan gelen) kumulatif degeriyle FARK alarak turetir; o
    # adim atlanirsa (orn. yil basi ceyregiyse) None kalir, bu GUVENLIDIR
    # (FAVOK o ceyrek icin sadece gizlenir, hicbir yanlis deger uretilmez).
    out["depreciation_amortization_cum"] = raw.balance_value(_DEPRECIATION_TAG)
    out["depreciation_amortization"] = None

    short_term_components = [raw.balance_value(tag) for tag in _SHORT_TERM_DEBT_TAGS]
    short_term_components = [v for v in short_term_components if v is not None]
    short_term_total = sum(short_term_components, Decimal(0)) if short_term_components else None

    long_term = out.get("long_term_financial_debt")
    if short_term_total is not None or long_term is not None:
        out["financial_debt"] = (short_term_total or Decimal(0)) + (long_term or Decimal(0))
    else:
        out["financial_debt"] = None

    return out


def standardized_record_values_ufrs(raw: RawKapFinancials) -> dict[str, Decimal | None]:
    """standardized_record_values()'in konvansiyonel banka (UFRS) karsiligi
    -- pipeline.py'nin _UFRS_QUARTERLY_FIELDS/_UFRS_STOCK_FIELDS ile BIREBIR
    ayni alan adlarini uretir. SADECE financial_group=='UFRS' icin cagrilmali
    (bkz. STANDARD_ITEM_MAP_KAP_UFRS_* modul notu)."""
    out: dict[str, Decimal | None] = {}

    for field, tag in STANDARD_ITEM_MAP_KAP_UFRS_BALANCE.items():
        out[field] = raw.balance_value(tag)

    for field, tag in STANDARD_ITEM_MAP_KAP_UFRS_INCOME.items():
        out[f"{field}_cum"] = raw.income_cum_value(tag)
        out[field] = raw.income_quarterly_value(tag)

    return out


def standardized_record_values_financing(raw: RawKapFinancials) -> dict[str, Decimal | None]:
    """standardized_record_values()'in Tasarruf Finansman Sirketi (XI_29K)
    karsiligi -- pipeline.py'nin _FINANSMAN_QUARTERLY_FIELDS/_FINANSMAN_STOCK_FIELDS
    ile BIREBIR ayni alan adlarini uretir. SADECE financial_group=='XI_29K'
    icin cagrilmali (bkz. STANDARD_ITEM_MAP_KAP_FINANSMAN_* modul notu)."""
    out: dict[str, Decimal | None] = {}

    for field, tag in STANDARD_ITEM_MAP_KAP_FINANSMAN_BALANCE.items():
        out[field] = raw.balance_value(tag)

    for field, tag in STANDARD_ITEM_MAP_KAP_FINANSMAN_INCOME.items():
        out[f"{field}_cum"] = raw.income_cum_value(tag)
        out[field] = raw.income_quarterly_value(tag)

    return out


def standardized_record_values_ufrs_k(raw: RawKapFinancials) -> dict[str, Decimal | None]:
    """standardized_record_values()'in sigorta (UFRS_K) karsiligi --
    pipeline.py'nin _standardize_to_records_ufrs_k() ile AYNI alan
    kumesini (gross_written_premiums/net_premiums_earned/technical_income/
    net_income + _cum varyantlari, receivables_from_operations/
    payables_from_operations/equity/share_capital, technical_balance(+_cum),
    cash_and_financial_assets, technical_provisions) uretir. SADECE
    financial_group=='UFRS_K' icin cagrilmali. Bkz. STANDARD_ITEM_MAP_KAP_UFRS_K_*
    modul notu: bazi alanlar (cash_and_equivalents/1A bileseni,
    technical_provisions_noncurrent/2MD bileseni) CROSS-PERIOD dogrulanamadi
    (Is Yatirim henuz 2Ç26'yi donmuyor) -- en yakin karsilik kabul edildi,
    Is Yatirim kendi verisini isleyince bu alanlar zaten onun DAHA GUVENILIR
    degeriyle EZILECEK."""
    out: dict[str, Decimal | None] = {}

    for field, tag in STANDARD_ITEM_MAP_KAP_UFRS_K_BALANCE.items():
        out[field] = raw.balance_value(tag)

    for field, tag in STANDARD_ITEM_MAP_KAP_UFRS_K_INCOME.items():
        out[f"{field}_cum"] = raw.income_cum_value(tag)
        out[field] = raw.income_quarterly_value(tag)

    cash = _cash_and_equivalents_ufrs_k(raw)
    financial = raw.balance_value(_FINANCIAL_ASSETS_TAG_UFRS_K)
    if cash is not None or financial is not None:
        out["cash_and_financial_assets"] = (cash or Decimal(0)) + (financial or Decimal(0))

    provisions_current = raw.balance_value(_TECHNICAL_PROVISIONS_CURRENT_TAG_UFRS_K)
    provisions_noncurrent = _technical_provisions_noncurrent_ufrs_k(raw)
    if provisions_current is not None or provisions_noncurrent is not None:
        out["technical_provisions"] = (provisions_current or Decimal(0)) + (provisions_noncurrent or Decimal(0))

    technical_balance_cum = _technical_balance_cum_ufrs_k(raw)
    if technical_balance_cum is not None:
        out["technical_balance_cum"] = technical_balance_cum
    technical_balance = _technical_balance_quarterly_ufrs_k(raw)
    if technical_balance is not None:
        out["technical_balance"] = technical_balance

    return out
