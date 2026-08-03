"""Is Yatirim MaliTablo uc noktasindan BIST sirketlerinin ceyreklik
bilanco ve gelir tablosu verilerini ceker.

Kesif adiminda (scripts/explore_isyatirim.py) THYAO (XI_29 - sanayi) ve
AKBNK (UFRS - banka) icin GERCEK canli yanitlar incelendi (data/exploration/
altinda saklidir). Bu yanitlardan dogrulanan gercekler:

- Uc nokta GET ile calisiyor (POST'a gerek yok), sonuc JSON:
  {"ok": bool, "errorCode": str|None, "errorDescription": str|None,
   "transactionId": str, "value": [...]}
- "value" bos liste ([]) donmesi HEM "yanlis financialGroup" HEM "hisse
  kodu yok" HEM "veri henuz aciklanmadi" durumlarinda ayni sekilde olur;
  uc nokta bu ucunu HTTP seviyesinde ayirt etmez (errorCode/errorDescription
  bile None kalir). Bu yuzden CompanyNotFoundError'un mesaji her iki
  ihtimali de belirtir.
- itemCode on eki anlam tasir:
    '1*' -> Bilanco Varliklari   (STOK, kumulatif duzeltme YAPILMAZ)
    '2*' -> Bilanco Kaynaklari   (STOK, kumulatif duzeltme YAPILMAZ)
    '3*' -> Gelir Tablosu        (KUMULATIF/YTD, ceyreklik turetme gerekir)
    '4*' -> Nakit Akis + ek kalemler (KUMULATIF/YTD, ayni sekilde)
- value1..value4, istekte verilen year1/period1..year4/period4 sirasiyla
  birebir eslesir (donen JSON donem etiketi ICERMEZ, sadece deger doner).
- XI_29 (sanayi/ticaret) ile UFRS (banka) TAMAMEN FARKLI itemCode semalari
  kullanir (orn. toplam varlik XI_29'da '1BL', UFRS'te '1Z'). Bu modul
  standart alan eslemesini SADECE XI_29 icin tanimlar; UFRS/UFRS_K
  tespit edilirse ham veri (RawFinancials) yine doner ama
  standardized_value()/quarterly_standardized_value() cagrilari
  UnsupportedFinancialGroupError firlatir (Kural 8: emin olunmayan
  semaya gore varsayimsal esleme yazilmadi).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

ENDPOINT = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"

# Gunluk kapanis fiyati gecmisi (kesif sirasinda dogrulandi: startdate/enddate
# DD-MM-YYYY formatinda ZORUNLU, aksi halde "Failed to convert ... LocalDate"
# hatasi donuyor). Yanit artan tarih sirasinda gelir; son eleman en guncel
# GUNUN KAPANIS fiyatidir (canli/aninda fiyat degil -- BIST kapaliyken de
# calisir, "son islem gunu kapanisi" olarak gosterilir).
PRICE_ENDPOINT = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil"

# Deneme sirasi onemli: once sanayi/ticaret (en yaygin), sonra banka/sigorta,
# sonra araci kurum.
FINANCIAL_GROUPS: tuple[str, ...] = ("XI_29", "UFRS", "UFRS_K")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.isyatirim.com.tr/",
}

Period = tuple[int, int]  # (yil, donem); donem in {3, 6, 9, 12}


# --- Hata siniflari -----------------------------------------------------


class IsYatirimError(Exception):
    """Is Yatirim fetcher'i icin taban hata sinifi."""


class CompanyNotFoundError(IsYatirimError):
    """Verilen hisse kodu icin denenen hicbir financialGroup'ta veri bulunamadi.

    Not: Is Yatirim uc noktasi 'hisse kodu yok' ile 'veri henuz yok' durumlarini
    HTTP seviyesinde ayirt etmedigi icin bu hata her iki ihtimali de kapsar.
    """


class FinancialDataNotAvailableError(IsYatirimError):
    """Sirket dogrulandi (baska donemler icin veri var) ama istenen en
    guncel donem henuz hicbir kalemde raporlanmamis."""


class UnsupportedFinancialGroupError(IsYatirimError):
    """XI_29 disindaki (banka/sigorta/araci kurum) semalar henuz standart
    alanlara eslenmedi; sadece ham veriye (RawFinancials.items) erisilebilir."""


class IsYatirimNetworkError(IsYatirimError):
    """Is Yatirim'a ag seviyesinde ulasilamadi (timeout, DNS, baglanti vb.)
    veya yanit beklenmeyen bicimde geldi."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class FinancialItem:
    """Tek bir mali tablo kaleminin (itemCode) birden fazla donem icin degerleri."""

    item_code: str
    description_tr: str
    values_by_period: dict[Period, Decimal]


@dataclass(frozen=True)
class RawFinancials:
    """Bir sirketin cekilen tum donemler icin ham mali tablo verisi."""

    ticker: str
    company_code: str
    financial_group: str
    periods: list[Period]  # basariyla veri donen tum donemler, yeniden eskiye
    items: dict[str, FinancialItem]  # itemCode -> FinancialItem

    def value(self, item_code: str, period: Period) -> Decimal | None:
        row = self.items.get(item_code)
        if row is None:
            return None
        return row.values_by_period.get(period)


# --- Kalem esleme tablosu (SADECE XI_29 - sanayi/ticaret semasi) --------
#
# Anahtar: bizim ic alan adimiz (calculator.py / scorer.py bunu kullanir).
# Deger: Is Yatirim itemCode'u. Kolay guncellenebilmesi icin ayri bir
# sabit olarak tutulur; kesif dosyalarindaki gercek yanitla dogrulanmistir
# (bkz. data/exploration/thyao_items_readable.txt).
STANDARD_ITEM_MAP_XI_29: dict[str, str] = {
    # --- Gelir tablosu (KUMULATIF -> quarterly_standardized_value ile ceyreklestirin) ---
    "revenue": "3C",  # Satis Gelirleri / Net Sales
    "gross_profit": "3D",  # BRUT KAR (ZARAR)
    # "operating_profit" = 3DF ("FAALIYET KARI (ZARARI)") -- Fintables'in
    # gelir tablosunda gosterdigi "Faaliyet Karı" satiriyla VE PD/EFK
    # carpaniyla CANLI TOASO verisiyle birebir dogrulandi (bkz. asagida).
    # BILEREK 3H ("Net Faaliyet Kar/Zararı") DEGIL -- ikisi FARKLI kavramlar:
    #   3H = 3D (Brüt Kâr) + 3DA + 3DB + 3DC (pazarlama/genel yönetim/Ar-Ge
    #        giderleri) -- "Diğer Faaliyet Gelir/Giderleri" (3DD/3DE, sıklıkla
    #        tek seferlik/düzenli-olmayan kalemler icerir) HARIÇ, "temiz"/dar
    #        faaliyet kârı.
    #   3DF = 3H + 3DD - 3DE (Diğer Faaliyet Gelir/Giderleri DAHIL) -- IFRS
    #        "Profit from Operating Activities" (ifrs-full_ProfitLossFrom
    #        OperatingActivities, bkz. kap_financials.py) ile BIREBIR eslesir,
    #        KAP XBRL taxonomy'siyle CANLI dogrulandi.
    # Fintables PD/EFK VE gelir tablosu satiri icin 3DF (GENIS kavram)
    # kullanir (TOASO 2026/06 TTM ile canli dogrulandi: PD/EFK=16,96 SADECE
    # 3DF TTM ile eslesir, 3H TTM ile degil) -- bu yuzden "operating_profit"
    # 3DF'dir. FAVÖK ICIN ISE Fintables 3H (DAR kavram) + Amortisman kullanir
    # (TOASO: 3H+4B=4.832.996.000, Fintables FAVÖK'uyle TAM ayni) -- bu, AYRI
    # bir alan olarak asagida "operating_profit_ebitda_base" ile tutulur ve
    # SADECE calculator.ebitda()/ebitda_cum() tarafindan kullanilir; hicbir
    # yerde DOGRUDAN gosterilmez.
    "operating_profit": "3DF",
    "operating_profit_ebitda_base": "3H",  # SADECE FAVÖK hesabi icin (bkz. yukarida)
    "net_income": "3Z",  # Ana Ortakliga Ait Net Donem Kari (EPS'e esas rakam)
    "net_income_total": "3L",  # DONEM KARI (ZARARI) - azinlik paylari dahil toplam
    # --- Nakit akis / ek kalemler (KUMULATIF) ---
    "depreciation_amortization": "4B",  # Amortisman Giderleri (EBITDA bileseni: operating_profit_ebitda_base + bu)
    # --- Bilanco (STOK deger - kumulatif duzeltme YAPILMAZ) ---
    "total_assets": "1BL",  # TOPLAM VARLIKLAR
    "current_assets": "1A",  # Donen Varliklar (cari oran bileseni)
    "trade_receivables": "1AC",  # Ticari Alacaklar (Donen Varliklar alti, KISA VADELI)
    "equity": "2N",  # Ozkaynaklar (toplam, azinlik payi dahil)
    "cash": "1AA",  # Nakit ve Nakit Benzerleri
    # Net borc hesabinin nakit-benzeri ikinci bileseni (bkz. calculator.py
    # net_debt notu, canli TERA/Fintables karsilastirmasi): kisa vadeli
    # menkul kiymet/repo portfoyu. Araci kurum gibi bu kalemi buyuk tasiyan
    # sirketlerde SADECE "cash" (1AA) kullanmak net borcu ONLARCA MILYAR TL
    # YANLIS gosteriyordu (TERA: Fintables -146,4 mr iken bizim eski
    # hesabimiz +15,5 mn cikiyordu). CANLI DOGRULANDI: TERA icin bu alanla
    # hesaplanan net borc, KAP'in ayni kavrami tasiyan
    # kap-fr_CurrentFinancialInvestments tag'iyle hesaplanan degere ~%0,02
    # fark ile (31 mn TL / 146 mr TL) eslesti.
    "financial_investments": "1AB",  # Finansal Yatirimlar (Donen Varliklar alti, KISA VADELI)
    "short_term_liabilities": "2A",  # Kisa Vadeli Yukumlulukler (toplam)
    "long_term_liabilities": "2B",  # Uzun Vadeli Yukumlulukler (toplam)
    "short_term_financial_debt": "2AA",  # Kisa Vadeli Finansal Borclar (total_debt bileseni)
    "long_term_financial_debt": "2BA",  # Uzun Vadeli Finansal Borclar (total_debt bileseni)
    "share_capital": "2OA",  # Odenmis Sermaye (piyasa degeri = fiyat x sermaye hesabinin girdisi)
}

# Gelir tablosu / nakit akis alanlari kumulatiftir (yil icinde YTD toplanir).
# Bilanco alanlari (total_assets, equity, cash, *_liabilities, *_financial_debt)
# bu kumede YOKTUR cunku onlar zaten belirli bir tarihteki STOK degerdir.
CUMULATIVE_FIELDS: frozenset[str] = frozenset(
    {
        "revenue",
        "gross_profit",
        "operating_profit",
        "operating_profit_ebitda_base",
        "net_income",
        "net_income_total",
        "depreciation_amortization",
    }
)

# total_debt icin tek bir itemCode yoktur; iki bilanco kaleminin toplamidir.
_TOTAL_DEBT_COMPONENT_FIELDS: tuple[str, str] = (
    "short_term_financial_debt",
    "long_term_financial_debt",
)


# --- Kalem esleme tablosu (SADECE UFRS - banka semasi) --------
#
# GARAN + AKBNK icin CANLI cekilen yanitlarla dogrulandi (bkz.
# data/exploration/GARAN_UFRS_get_*.json, akbnk_ufrs_items_readable.txt).
# Bankalarin gelir tablosu XI_29'dakinden TAMAMEN FARKLI kalemler kullanir
# (brut kar/esas faaliyet kari kavramlari YOK); bu yuzden ayri bir harita.
STANDARD_ITEM_MAP_UFRS: dict[str, str] = {
    # --- Gelir tablosu (KUMULATIF -> quarterly_standardized_value_ufrs ile ceyreklestirin) ---
    "interest_income": "3A",  # I. FAIZ GELIRLERI
    "interest_expense": "3B",  # II. FAIZ GIDERLERI (ham veride POZITIF buyukluk; standardized_value_ufrs BURADA NEGATIFE cevirir -- referans kartlarda gider satiri eksi olarak gosteriliyor)
    "net_fee_income": "3CA",  # IV. NET UCRET VE KOMISYON GELIRLERI/GIDERLERI
    "net_operating_profit": "3CH",  # XI. NET FAALIYET KARI/ZARARI
    "net_income": "3ZA",  # 23.1 Grubun Kari/Zarari (ANA ORTAKLIGA AIT -- XI_29'daki '3Z'nin banka karsiligi)
    "net_income_total": "3Z",  # XXIII. NET DONEM KARI/ZARARI (azinlik payi dahil TOPLAM)
    # --- Bilanco (STOK deger - kumulatif duzeltme YAPILMAZ) ---
    "loans": "1AF",  # VI. KREDILER
    "deposits": "2A",  # I. MEVDUAT
    # NOT: "1AFE" (6.3 Ozel Karsiliklar) TFRS 9 sonrasi cogu bankada 0 gorunuyor
    # (canli dogrulandi: GARAN + AKBNK'de v1=0) -- karsilik artik kredi
    # bakiyesinden (1AF) NET dusulmus olarak tutuluyor, ayri satirda degil.
    # Bu yuzden GENEL "2L Karsiliklar" (calisan haklari + diger karsiliklar
    # dahil TOPLAM) kullanilir -- daha spesifik bir "beklenen kredi zarari"
    # kalemi Is Yatirim'in bu uc noktasinda YOKTUR (Kural 8: olmayan/emin
    # olunmayan bir kalemi varsayimsal DOLDURMA).
    "provisions": "2L",  # XII. KARSILIKLAR (toplam)
    "total_assets": "1Z",  # AKTIF TOPLAMI
    "equity": "2O",  # XVI. OZKAYNAKLAR
    "share_capital": "2OA",  # 16.1 Odenmis Sermaye -- XI_29'daki ile AYNI itemCode (canli GARAN verisiyle dogrulandi)
}

# Bankalarin gelir tablosu kalemleri de (XI_29'daki gibi) kumulatiftir.
CUMULATIVE_FIELDS_UFRS: frozenset[str] = frozenset(
    {
        "interest_income",
        "interest_expense",
        "net_fee_income",
        "net_operating_profit",
        "net_income",
        "net_income_total",
    }
)

# "Finansal Varlıklar (Net)" gibi bazi Fintables/referans kalemleri tek bir
# itemCode karsiligi degil, birden fazla bilanco kaleminin DOGRULANMAMIS bir
# toplamidir (Kural 8: emin olunmayan agregasyon yazilmaz) -- bu yuzden bu
# haritada YOKTUR; onun yerine guvenilir tek-kalemli "total_assets" (1Z)
# kullanilir (bkz. src/analysis/calculator.py analyze_bank docstring'i).


# --- Kalem esleme tablosu (SADECE UFRS_K - sigorta) --------
#
# ANSGR (Anadolu Sigorta) icin CANLI cekilen yanitla dogrulandi (bkz.
# data/exploration/ANSGR_UFRS_K_get_*.json). Referans karttaki (Fintables)
# TUM rakamlarla (Prim Uretimi, Alinan Net Primler, Teknik Gelirler, Ozkaynaklar,
# Esas Faaliyetlerden Alacaklar/Borclar) BIREBIR (son haneye kadar) eslesti --
# bankadaki "Finansal Varliklar (Net)" belirsizliginin AKSINE, buradaki iki
# bilesik kalem de (asagida) TEK TEK dogrulanmis alt kalemlerin toplami
# oldugu KANITLANDI (Kural 8 ihlali degil, DOGRULANMIS toplama).
STANDARD_ITEM_MAP_UFRS_K: dict[str, str] = {
    # --- Gelir tablosu (KUMULATIF) ---
    "gross_written_premiums": "3AAAA",  # 1.1.1- Brut Yazilan Primler (+) -- "Prim Uretimi"
    "net_premiums_earned": "3AAA",  # 1.1- Yazilan Primler (Reasurer Payi Dusulmus) -- "Alinan Net Primler"
    "technical_income": "3A",  # A- Hayat Disi Teknik Gelir -- "Teknik Gelirler"
    "technical_expense": "3B",  # B- Hayat Disi Teknik Gider(-) -- SADECE technical_balance hesaplamak icin, ayri satirda GOSTERILMEZ
    "net_income": "3NJA",  # N- Donem Net Kari veya Zarari
    # --- Bilanco (STOK) ---
    "cash_and_equivalents": "1A",  # A- Nakit Ve Nakit Benzeri Varliklar -- SADECE cash_and_financial_assets bileseni
    "financial_assets": "1B",  # B- Finansal Varliklar ile Riski Sigortalilara Ait Finansal Yatirimlar -- SADECE cash_and_financial_assets bileseni
    "receivables_from_operations": "1C",  # C- Esas Faaliyetlerden Alacaklar
    "payables_from_operations": "2B",  # B- Esas Faaliyetlerden Borclar
    "technical_provisions_current": "2E",  # E- Sigortacilik Teknik Karsiliklari (kisa vadeli) -- SADECE technical_provisions bileseni
    "technical_provisions_noncurrent": "2MD",  # E- Sigortacilik Teknik Karsiliklari (uzun vadeli) -- SADECE technical_provisions bileseni
    "equity": "2O",  # Ozsermaye Toplami
    "share_capital": "2MEA",  # A- Odenmis Sermaye
}

CUMULATIVE_FIELDS_UFRS_K: frozenset[str] = frozenset(
    {"gross_written_premiums", "net_premiums_earned", "technical_income", "technical_expense", "net_income"}
)


# --- Kalem esleme tablosu (SADECE UFRS - katilim bankasi) --------
#
# ALBRK (Albaraka Turk) ile CANLI dogrulandi (bkz. data/exploration/
# ALBRK_UFRS_get_*.json). ONEMLI: katilim bankalari "faizsiz bankacilik"
# ilkesi geregi FARKLI TERMINOLOJI (Faiz -> Kar Payi, Mevduat -> Toplanan
# Fonlar) KULLANMAKLA KALMAZ -- itemCode SIRALAMASI da TAMAMEN FARKLIDIR
# (orn. konvansiyonel bankada Faiz Giderleri '3B' iken ALBRK'de o kod hic
# YOK, karsiligi '3AAK'). Bu yuzden STANDARD_ITEM_MAP_UFRS'i (konvansiyonel
# banka) katilim bankasina uygulamak NEREDEYSE TUM kalemlerde "veri yok"
# uretiyordu (bilinen bir bug olarak tespit edildi) -- bu ayri harita o
# sorunu cozer.
STANDARD_ITEM_MAP_UFRS_KATILIM: dict[str, str] = {
    # --- Gelir tablosu (KUMULATIF) ---
    "interest_income": "3A",  # I. KAR PAYI GELIRLERI
    "interest_expense": "3AAK",  # II. KAR PAYI GIDERLERI (ham veride POZITIF, standardized_value_ufrs_katilim NEGATIFE cevirir)
    "net_fee_income": "3AAS",  # IV. NET UCRET VE KOMISYON GELIRLERI/GIDERLERI
    "net_operating_profit": "3ABK",  # XI. NET FAALIYET KARI/ZARARI
    "net_income": "3ZA",  # 23.1 Grubun Kari/Zarari (ANA ORTAKLIGA AIT)
    "net_income_total": "3Z",  # XVIII. NET DONEM KARI/ZARARI (azinlik payi dahil TOPLAM)
    # --- Bilanco (STOK deger) ---
    "loans": "1ABF",  # VI. KREDILER
    "deposits": "2A",  # I. TOPLANAN FONLAR
    "provisions": "2AAR",  # X. KARSILIKLAR (toplam)
    "total_assets": "1Z",  # AKTIF TOPLAMI
    "equity": "2O",  # OZKAYNAK
    "share_capital": "2NA",  # 14.1 Odenmis Sermaye
}

CUMULATIVE_FIELDS_UFRS_KATILIM: frozenset[str] = frozenset(
    {"interest_income", "interest_expense", "net_fee_income", "net_operating_profit", "net_income", "net_income_total"}
)


# --- Yardimci: hisse kodu / donem hesaplamalari -----------------------------------------------------


def normalize_company_code(ticker: str) -> str:
    """'THYAO.IS' -> 'THYAO' seklinde Is Yatirim'in bekledigi koda cevirir."""
    code = ticker.strip().upper()
    if code.endswith(".IS"):
        code = code[: -len(".IS")]
    return code


_QUARTER_END_MONTH_DAY = {3: (3, 31), 6: (6, 30), 9: (9, 30), 12: (12, 31)}


def _quarter_end_date(year: int, period: int) -> date:
    month, day = _QUARTER_END_MONTH_DAY[period]
    return date(year, month, day)


def _previous_quarter_pair(year: int, period: int) -> Period:
    if period == 3:
        return year - 1, 12
    return year, period - 3


def guess_last_periods(count: int = 8, lag_days: int = 75) -> list[Period]:
    """Bugunun tarihine gore en olasi son `count` ceyregi tahmin eder (yeniden eskiye).

    BIST sirketleri (konsolide) ceyrek sonundan ~10-14 hafta sonra rapor
    aciklar; bir gecikme payi birakip cutoff tarihinden ONCE ya da O GUNE
    biten en son ceyregi bulur (ay bazli degil, ceyrek bitis GUNUNU kontrol
    eder). Bu sadece bir baslangic tahminidir -- fetch_financials'a `periods`
    parametresiyle elle de gecilebilir.
    """
    cutoff = date.today() - timedelta(days=lag_days)

    year = cutoff.year
    period: int | None = None
    for candidate in (12, 9, 6, 3):
        if _quarter_end_date(year, candidate) <= cutoff:
            period = candidate
            break
    if period is None:
        year -= 1
        period = 12

    periods: list[Period] = []
    for _ in range(count):
        periods.append((year, period))
        year, period = _previous_quarter_pair(year, period)
    return periods


# --- Yardimci: kumulatif -> ceyreklik deger turetme -----------------------------------------------------


def previous_period(period: Period) -> Period | None:
    """Bir onceki ceyregi doner. Yilin ilk ceyreginde (period=3) None doner
    (yil basinda kumulatif deger zaten o ceyregin kendisidir, cikarma yapilmaz)."""
    year, p = period
    if p not in (3, 6, 9, 12):
        raise ValueError(f"Gecersiz donem: {p}. Beklenen: 3, 6, 9 veya 12.")
    if p == 3:
        return None
    return year, p - 3


def quarterly_value_from_cumulative(
    values_by_period: dict[Period, Decimal], period: Period
) -> Decimal | None:
    """Kumulatif (YTD) bir kalemden tek ceyreklik degeri turetir.

    BIST gelir tablosu / nakit akis kalemleri kumulatiftir (6 aylik = ilk
    6 ayin toplami). Ceyreklik deger = bu donem kumulatif - onceki donem
    kumulatif. Yilin ilk ceyreginde (period=3) CIKARMA YAPILMAZ; kumulatif
    deger zaten o ceyregin kendisidir.
    """
    current = values_by_period.get(period)
    if current is None:
        return None

    prev_period = previous_period(period)
    if prev_period is None:
        return current

    previous_value = values_by_period.get(prev_period)
    if previous_value is None:
        # Onceki ceyregin verisi elimizde yoksa guvenilir turetim yapilamaz.
        return None

    return current - previous_value


# --- HTTP katmani -----------------------------------------------------


def _build_params(company_code: str, financial_group: str, periods_chunk: list[Period]) -> dict[str, object]:
    params: dict[str, object] = {
        "companyCode": company_code,
        "exchange": "TRY",
        "financialGroup": financial_group,
    }
    for index, (year, period) in enumerate(periods_chunk, start=1):
        params[f"year{index}"] = year
        params[f"period{index}"] = period
    return params


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_chunk(company_code: str, financial_group: str, periods_chunk: list[Period]) -> dict:
    """Tek bir istekle en fazla 4 donemlik ham veriyi ceker (JSON dict doner)."""
    params = _build_params(company_code, financial_group, periods_chunk)
    try:
        response = httpx.get(
            ENDPOINT, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS
        )
    except httpx.RequestError as exc:
        logger.warning("Is Yatirim istegi basarisiz, yeniden denenecek: %s", exc)
        raise

    if response.status_code != 200:
        raise IsYatirimNetworkError(
            f"Is Yatirim beklenmeyen HTTP durum kodu dondurdu: {response.status_code}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise IsYatirimNetworkError(
            "Is Yatirim yaniti JSON olarak ayristirilamadi (endpoint sema degistirmis olabilir)."
        ) from exc


# --- Ham satirlari FinancialItem'lara donusturme -----------------------------------------------------

_VALUE_KEYS = ("value1", "value2", "value3", "value4")


def _parse_decimal(raw_value: object) -> Decimal | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if text == "":
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        logger.warning("Sayisal olarak ayristirilamayan deger atlandi: %r", raw_value)
        return None


def _rows_to_items(rows: list[dict], periods_chunk: list[Period]) -> dict[str, FinancialItem]:
    items: dict[str, FinancialItem] = {}
    for row in rows:
        item_code = row.get("itemCode")
        if not item_code:
            continue
        values_by_period: dict[Period, Decimal] = {}
        for value_key, period in zip(_VALUE_KEYS, periods_chunk):
            parsed = _parse_decimal(row.get(value_key))
            if parsed is not None:
                values_by_period[period] = parsed
        items[item_code] = FinancialItem(
            item_code=item_code,
            description_tr=row.get("itemDescTr") or "",
            values_by_period=values_by_period,
        )
    return items


def _merge_items(
    base: dict[str, FinancialItem], extra: dict[str, FinancialItem]
) -> dict[str, FinancialItem]:
    merged = dict(base)
    for code, item in extra.items():
        if code in merged:
            combined_values = {**merged[code].values_by_period, **item.values_by_period}
            merged[code] = FinancialItem(
                item_code=code,
                description_tr=merged[code].description_tr or item.description_tr,
                values_by_period=combined_values,
            )
        else:
            merged[code] = item
    return merged


# --- Ana API -----------------------------------------------------


def _resolve_actual_group(requested_group: str, rows: list[dict], company_code: str) -> str:
    """Is Yatirim'in MaliTablo uc noktasi 'financialGroup' parametresini
    XI_29 DISINDA GUVENILIR sekilde filtrelemiyor -- CANLI DOGRULANDI: ayni
    sirket icin HEM 'UFRS' HEM 'UFRS_K' istegi AYNI (gercek) veriyi
    donduruyor. Ornekler:
      - ANSGR (GERCEK sigorta sirketi) 'financialGroup=UFRS' ile sorulunca
        BOS DONMEDI -- kendi GERCEK sigorta verisini (405 satir, itemCode
        '3A'='A- Hayat Disi Teknik Gelir') dondurdu. Bu, onceden
        fetch_financials'in "UFRS" olarak YANLIS etiketlemesine ve
        pipeline.py'nin bankayla ayni STANDARD_ITEM_MAP_UFRS'i uygulayip
        anlamsiz "Faiz Gelirleri" satirlari uretmesine yol aciyordu.
      - GARAN (GERCEK banka) 'financialGroup=UFRS_K' ile sorulunca da BOS
        DONMEDI -- kendi GERCEK banka verisini (192 satir) dondurdu.
      - ALBRK (GERCEK katilim bankasi) 'financialGroup=UFRS' ile sorulunca
        kendi verisini donduruyor AMA "faizsiz bankacilik" ilkesi geregi
        itemCode SIRALAMASI TAMAMEN FARKLI (bkz. STANDARD_ITEM_MAP_UFRS_KATILIM
        yorumu) -- konvansiyonel banka haritasi uygulanirsa NEREDEYSE TUM
        kalemler "veri yok" donuyordu. Bu yuzden DONEN "UFRS" etiketi de
        tek basina GUVENILIR DEGIL; '3A' aciklamasi "KAR PAYI" iceriyorsa
        gercekte katilim bankasidir, `resolved_group` "UFRS_KATILIM" olarak
        DONER (bu, gercek Is Yatirim API'sinin TANIMADIGI, SADECE bu
        modulun ic siniflandirmasi icin uydurulmus bir etikettir -- HTTP
        istekleri icin KULLANILMAZ, bkz. fetch_financials).
    Bu yuzden `requested_group` (hangi parametreyle sorduğumuz) KORUNMAZ --
    donen SATIRLARIN ICERIGI (itemCode '3A'nin Turkce aciklamasi, HER
    semada farkli ama HER ZAMAN dolu bir gelir tablosu ana kalemidir)
    incelenerek GERCEK sema belirlenir. XI_29 icin bu fonksiyon
    CAGRILMAZ -- XI_29 filtrelemesi guvenilir (canli dogrulandi: yanlis
    sirkette 0 satir donuyor, bkz. fetch_financials)."""
    if requested_group not in ("UFRS", "UFRS_K"):
        return requested_group

    item_3a_desc = next((row.get("itemDescTr") or "" for row in rows if row.get("itemCode") == "3A"), "").upper()
    if "KAR PAYI" in item_3a_desc:
        return "UFRS_KATILIM"
    if "FAİZ" in item_3a_desc or "FAIZ" in item_3a_desc:
        return "UFRS"
    if "TEKNİK" in item_3a_desc or "TEKNIK" in item_3a_desc:
        return "UFRS_K"

    logger.warning(
        "companyCode=%s: '%s' istegiyle donen veride sema ('3A' aciklamasi: %r) "
        "FAIZ/TEKNIK ile ayirt edilemedi -- denenen grup ('%s') oldugu gibi "
        "KORUNDU, YANLIS olabilir (bilinen sinirlama: araci kurumlar UFRS_K'yi "
        "sigortayla PAYLASIR ama farkli '3A' anlamina sahip olabilir).",
        company_code,
        requested_group,
        item_3a_desc,
        requested_group,
    )
    return requested_group


def fetch_financials(
    ticker: str,
    periods: list[Period] | None = None,
    financial_group: str | None = None,
) -> RawFinancials:
    """Bir BIST sirketinin ceyreklik finansal tablolarini Is Yatirim'dan ceker.

    Tek istekte en fazla 4 donem cekilebildigi icin `periods` 4'erli
    parcalara bolunup ayri isteklerle cekilir (varsayilan: son 8 ceyrek =
    2 istek). `financial_group` verilmezse once XI_29 (sanayi/ticaret),
    bos donerse UFRS (banka/sigorta), o da bos donerse UFRS_K (araci
    kurum) denenir; hangi grubun kullanildigi RawFinancials.financial_group
    alaninda doner.

    Hatalar:
        CompanyNotFoundError: Denenen hicbir financialGroup'ta veri yok
            (hisse kodu yanlis olabilir VEYA sirket hic veri aciklamamis
            olabilir -- uc nokta bu ikisini ayirt etmiyor).
        FinancialDataNotAvailableError: Sirket dogrulandi ama istenen en
            guncel donem hicbir kalemde raporlanmamis (henuz aciklanmamis).
        IsYatirimNetworkError: Ag hatasi (timeout, DNS, beklenmeyen yanit).
    """
    company_code = normalize_company_code(ticker)
    target_periods = periods if periods is not None else guess_last_periods(count=8)
    if not target_periods:
        raise ValueError("periods bos olamaz.")

    chunks = [target_periods[i : i + 4] for i in range(0, len(target_periods), 4)]
    groups_to_try = [financial_group] if financial_group else list(FINANCIAL_GROUPS)

    resolved_group: str | None = None
    request_group: str | None = None  # GERCEK Is Yatirim API'sinin tanidigi parametre (bkz. asagidaki not)
    items: dict[str, FinancialItem] = {}
    achieved_periods: list[Period] = []

    for index, group in enumerate(groups_to_try):
        # "UFRS_KATILIM" GERCEK bir Is Yatirim financialGroup degeri DEGILDIR
        # (bu modulun kendi ic siniflandirma etiketidir, bkz. _resolve_actual_group) --
        # API'ye HER ZAMAN "UFRS" olarak sorulur (canli dogrulandi: API'nin
        # tanimadigi bir deger BOS doner, orn. "UFRS_KONSOLIDE" 0 satir verdi).
        api_group = "UFRS" if group == "UFRS_KATILIM" else group
        payload = _request_chunk(company_code, api_group, chunks[0])
        rows = payload.get("value") or []

        if rows:
            resolved_group = _resolve_actual_group(group, rows, company_code)
            request_group = api_group
            items = _rows_to_items(rows, chunks[0])
            achieved_periods = list(chunks[0])
            break

        logger.info(
            "companyCode=%s financialGroup=%s icin veri bulunamadi, siradaki grup denenecek.",
            company_code,
            group,
        )
        if index < len(groups_to_try) - 1:
            time.sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)

    if resolved_group is None or request_group is None:
        raise CompanyNotFoundError(
            f"'{ticker}' icin denenen hicbir financialGroup'ta ({', '.join(groups_to_try)}) "
            "veri bulunamadi. Hisse kodunu kontrol edin; sirket henuz halka "
            "acik olmayabilir veya kod hatali olabilir."
        )

    newest_period = chunks[0][0]
    if not any(newest_period in item.values_by_period for item in items.values()):
        raise FinancialDataNotAvailableError(
            f"'{ticker}' ({resolved_group}) icin {newest_period[0]}/Ç{newest_period[1] // 3}. "
            "donem verisi henuz hicbir kalemde raporlanmamis."
        )

    for chunk in chunks[1:]:
        time.sleep(config.HTTP_RATE_LIMIT_DELAY_SECONDS)
        payload = _request_chunk(company_code, request_group, chunk)
        rows = payload.get("value") or []
        if not rows:
            logger.warning(
                "companyCode=%s financialGroup=%s donemler=%s icin veri donmedi; "
                "sirket bu tarihten once halka acik olmayabilir.",
                company_code,
                request_group,
                chunk,
            )
            continue
        items = _merge_items(items, _rows_to_items(rows, chunk))
        achieved_periods.extend(chunk)

    return RawFinancials(
        ticker=ticker,
        company_code=company_code,
        financial_group=resolved_group,
        periods=achieved_periods,
        items=items,
    )


# --- Standart alan erisimi (SADECE XI_29) -----------------------------------------------------


def _require_xi_29(raw: RawFinancials) -> None:
    if raw.financial_group != "XI_29":
        raise UnsupportedFinancialGroupError(
            f"'{raw.financial_group}' financialGroup semasi icin standart alan eslemesi "
            "henuz tanimlanmadi (su an sadece XI_29 / sanayi-ticaret sirketleri icin "
            "dogrulandi). Ham veriye raw.items uzerinden erisebilirsiniz."
        )


def standardized_value(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """Ic sema alan adina (orn. 'revenue', 'equity') gore verilen donem icin
    HAM (kumulatif olabilen) degeri doner. Gelir tablosu/nakit akis alanlari
    icin bu KUMULATIF (YTD) degerdir; ceyreklik icin
    quarterly_standardized_value() kullanin. Bilanco alanlari zaten stok
    degerdir, kumulatif/ceyreklik ayrimi onlar icin gecerli degildir.
    """
    _require_xi_29(raw)
    item_code = STANDARD_ITEM_MAP_XI_29.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen standart alan adi: '{field_name}'")
    return raw.value(item_code, period)


def quarterly_standardized_value(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """Ic sema alan adina gore TEK CEYREKLIK degeri doner.

    Gelir tablosu/nakit akis alanlari (CUMULATIVE_FIELDS icinde) icin
    kumulatiften ceyreklik turetme uygulanir. Bilanco alanlari icin
    (STOK deger) dogrudan standardized_value() ile aynidir.
    """
    _require_xi_29(raw)
    item_code = STANDARD_ITEM_MAP_XI_29.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen standart alan adi: '{field_name}'")

    item = raw.items.get(item_code)
    if item is None:
        return None

    if field_name not in CUMULATIVE_FIELDS:
        return item.values_by_period.get(period)

    return quarterly_value_from_cumulative(item.values_by_period, period)


_FINANCE_SECTOR_INCOME_ITEM_CODE = "3CAC"  # "Faiz, Ucret, Prim, Komisyon ve Diger Gelirler"


def total_revenue(raw: RawFinancials, period: Period) -> Decimal | None:
    """Toplam hasilat (KUMULATIF) = Satis Gelirleri (STANDARD_ITEM_MAP_XI_29['revenue'],
    itemCode '3C', ticari faaliyet) + varsa Finans Sektoru Faaliyetlerinden
    Gelirler (itemCode '3CAC', faiz/ucret/prim/komisyon -- bunyesinde
    finansman/leasing kolu olan sirketlerde ayri raporlanir).

    CANLI DOGRULANDI (TOASO, 2026/6 VE 2025/6 -- ikisi de TL'ye kadar birebir
    eslesti): Fintables'in ozet karttaki "Satislar" kalemi TEK BASINA '3C'
    ile DEGIL, '3C' + '3CAC' toplamiyla eslesiyor. '3C' tek basina kullanilinca
    Fintables'tan sistematik olarak ~%5-6 DUSUK cikiyordu -- cunku TOASO gibi
    bunyesinde finansman/leasing kolu olan sirketlerde 'Satis Gelirleri'
    itemCode'u SADECE ticari segmenti kapsiyor, finans segmentinin gelir
    tarafini (3CAC) DAHIL ETMIYOR. BRUT KAR (itemCode '3D') zaten HER IKI
    segmenti de (3CAB ticari + 3CAF finans) icerdigi icin kar/marj rakamlari
    bundan ETKILENMIYORDU, sadece "Satislar" kalemi dusuk cikiyordu.

    Finans segmenti olmayan (cogunluk) sirketlerde '3CAC' hic raporlanmaz --
    bu durumda fonksiyon SADECE '3C'yi doner, davranis DEGISMEZ.
    """
    _require_xi_29(raw)
    core_sales = raw.value(STANDARD_ITEM_MAP_XI_29["revenue"], period)
    finance_income = raw.value(_FINANCE_SECTOR_INCOME_ITEM_CODE, period)
    if core_sales is None and finance_income is None:
        return None
    return (core_sales or Decimal(0)) + (finance_income or Decimal(0))


def quarterly_total_revenue(raw: RawFinancials, period: Period) -> Decimal | None:
    """total_revenue()'in TEK CEYREKLIK hali -- bkz. total_revenue() docstring'i
    ve quarterly_value_from_cumulative() (kumulatiften ceyreklik turetme)."""
    _require_xi_29(raw)
    core_item = raw.items.get(STANDARD_ITEM_MAP_XI_29["revenue"])
    finance_item = raw.items.get(_FINANCE_SECTOR_INCOME_ITEM_CODE)
    core_q = quarterly_value_from_cumulative(core_item.values_by_period, period) if core_item else None
    finance_q = quarterly_value_from_cumulative(finance_item.values_by_period, period) if finance_item else None
    if core_q is None and finance_q is None:
        return None
    return (core_q or Decimal(0)) + (finance_q or Decimal(0))


def total_debt(raw: RawFinancials, period: Period) -> Decimal | None:
    """Toplam finansal borc = kisa + uzun vadeli finansal borc (bilanco,
    STOK deger). Tek bir itemCode karsiligi olmadigi icin
    STANDARD_ITEM_MAP_XI_29'da degil, ayri bir fonksiyon olarak hesaplanir.
    """
    _require_xi_29(raw)
    short_field, long_field = _TOTAL_DEBT_COMPONENT_FIELDS
    short_debt = raw.value(STANDARD_ITEM_MAP_XI_29[short_field], period)
    long_debt = raw.value(STANDARD_ITEM_MAP_XI_29[long_field], period)
    if short_debt is None and long_debt is None:
        return None
    return (short_debt or Decimal(0)) + (long_debt or Decimal(0))


# --- Standart alan erisimi (SADECE UFRS - banka) -----------------------------------------------------


def _require_ufrs(raw: RawFinancials) -> None:
    if raw.financial_group != "UFRS":
        raise UnsupportedFinancialGroupError(
            f"'{raw.financial_group}' financialGroup semasi icin banka alan eslemesi "
            "tanimlanmadi (su an sadece UFRS / banka sirketleri icin dogrulandi -- "
            "UFRS_K / sigorta-araci kurum henuz desteklenmiyor). Ham veriye "
            "raw.items uzerinden erisebilirsiniz."
        )


def standardized_value_ufrs(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """standardized_value()'nin UFRS (banka) karsiligi. HAM (kumulatif olabilen)
    degeri doner; 'interest_expense' ozel olarak NEGATIFE cevrilir (ham
    veride pozitif buyukluk olarak gelir, ama kart/rapor gelenekte gider
    satiri eksi gosterilir -- bkz. STANDARD_ITEM_MAP_UFRS yorumu)."""
    _require_ufrs(raw)
    item_code = STANDARD_ITEM_MAP_UFRS.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen banka alan adi: '{field_name}'")
    value = raw.value(item_code, period)
    if value is not None and field_name == "interest_expense":
        return -value
    return value


def quarterly_standardized_value_ufrs(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """quarterly_standardized_value()'nin UFRS (banka) karsiligi: gelir
    tablosu kalemleri icin kumulatiften ceyreklik turetme uygular; bilanco
    (STOK) kalemleri icin standardized_value_ufrs ile ayni sonucu doner."""
    _require_ufrs(raw)
    item_code = STANDARD_ITEM_MAP_UFRS.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen banka alan adi: '{field_name}'")

    item = raw.items.get(item_code)
    if item is None:
        return None

    if field_name not in CUMULATIVE_FIELDS_UFRS:
        return item.values_by_period.get(period)

    quarterly = quarterly_value_from_cumulative(item.values_by_period, period)
    if quarterly is not None and field_name == "interest_expense":
        return -quarterly
    return quarterly


# --- Standart alan erisimi (SADECE UFRS - katilim bankasi) -----------------------------------------------------


def _require_ufrs_katilim(raw: RawFinancials) -> None:
    if raw.financial_group != "UFRS_KATILIM":
        raise UnsupportedFinancialGroupError(
            f"'{raw.financial_group}' financialGroup semasi icin katilim bankasi alan eslemesi "
            "tanimlanmadi (su an sadece UFRS_KATILIM icin dogrulandi -- ALBRK ile canli test edildi)."
        )


def standardized_value_ufrs_katilim(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """standardized_value()'nin katilim bankasi karsiligi. 'interest_expense'
    (Kar Payi Giderleri) ham veride POZITIF gelir, konvansiyonel bankadaki
    gibi NEGATIFE cevrilir."""
    _require_ufrs_katilim(raw)
    item_code = STANDARD_ITEM_MAP_UFRS_KATILIM.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen katilim bankasi alan adi: '{field_name}'")
    value = raw.value(item_code, period)
    if value is not None and field_name == "interest_expense":
        return -value
    return value


def quarterly_standardized_value_ufrs_katilim(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """quarterly_standardized_value()'nin katilim bankasi karsiligi."""
    _require_ufrs_katilim(raw)
    item_code = STANDARD_ITEM_MAP_UFRS_KATILIM.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen katilim bankasi alan adi: '{field_name}'")

    item = raw.items.get(item_code)
    if item is None:
        return None

    if field_name not in CUMULATIVE_FIELDS_UFRS_KATILIM:
        return item.values_by_period.get(period)

    quarterly = quarterly_value_from_cumulative(item.values_by_period, period)
    if quarterly is not None and field_name == "interest_expense":
        return -quarterly
    return quarterly


# --- Standart alan erisimi (SADECE UFRS_K - sigorta) -----------------------------------------------------


def _require_ufrs_k(raw: RawFinancials) -> None:
    if raw.financial_group != "UFRS_K":
        raise UnsupportedFinancialGroupError(
            f"'{raw.financial_group}' financialGroup semasi icin sigorta alan eslemesi "
            "tanimlanmadi (su an sadece UFRS_K / sigorta sirketleri icin dogrulandi -- "
            "araci kurumlar UFRS_K'yi PAYLASIR ama TAMAMEN FARKLI kalemler kullanabilir, "
            "HENUZ ayrica dogrulanmadi). Ham veriye raw.items uzerinden erisebilirsiniz."
        )


def standardized_value_ufrs_k(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """standardized_value()'nin UFRS_K (sigorta) karsiligi. HAM (kumulatif
    olabilen) degeri doner."""
    _require_ufrs_k(raw)
    item_code = STANDARD_ITEM_MAP_UFRS_K.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen sigorta alan adi: '{field_name}'")
    return raw.value(item_code, period)


def quarterly_standardized_value_ufrs_k(raw: RawFinancials, field_name: str, period: Period) -> Decimal | None:
    """quarterly_standardized_value()'nin UFRS_K (sigorta) karsiligi."""
    _require_ufrs_k(raw)
    item_code = STANDARD_ITEM_MAP_UFRS_K.get(field_name)
    if item_code is None:
        raise KeyError(f"Bilinmeyen sigorta alan adi: '{field_name}'")

    item = raw.items.get(item_code)
    if item is None:
        return None

    if field_name not in CUMULATIVE_FIELDS_UFRS_K:
        return item.values_by_period.get(period)

    return quarterly_value_from_cumulative(item.values_by_period, period)


def technical_balance_ufrs_k(raw: RawFinancials, period: Period) -> Decimal | None:
    """Teknik Denge = Teknik Gelir (3A) + Teknik Gider (3B, ham veride ZATEN
    negatif isaretle gelir) -- HAM (kumulatif) deger. ANSGR ile canli
    dogrulandi: 54.903.467.315 + (-45.602.915.467) = 9.300.551.848, referans
    kartla BIREBIR eslesiyor."""
    _require_ufrs_k(raw)
    income = raw.value(STANDARD_ITEM_MAP_UFRS_K["technical_income"], period)
    expense = raw.value(STANDARD_ITEM_MAP_UFRS_K["technical_expense"], period)
    if income is None and expense is None:
        return None
    return (income or Decimal(0)) + (expense or Decimal(0))


def quarterly_technical_balance_ufrs_k(raw: RawFinancials, period: Period) -> Decimal | None:
    """technical_balance_ufrs_k()'nin TEK CEYREKLIK karsiligi (her iki
    bilesen de kumulatiften ceyreklestirilip sonra toplanir)."""
    _require_ufrs_k(raw)
    income_item = raw.items.get(STANDARD_ITEM_MAP_UFRS_K["technical_income"])
    expense_item = raw.items.get(STANDARD_ITEM_MAP_UFRS_K["technical_expense"])
    if income_item is None and expense_item is None:
        return None
    income_q = quarterly_value_from_cumulative(income_item.values_by_period, period) if income_item else None
    expense_q = quarterly_value_from_cumulative(expense_item.values_by_period, period) if expense_item else None
    if income_q is None and expense_q is None:
        return None
    return (income_q or Decimal(0)) + (expense_q or Decimal(0))


def cash_and_financial_assets_ufrs_k(raw: RawFinancials, period: Period) -> Decimal | None:
    """Nakit Benzeri Finansal Varliklar = Nakit ve Nakit Benzeri Varliklar (1A)
    + Finansal Varliklar ile Riski Sigortalilara Ait Finansal Yatirimlar (1B)
    -- STOK deger. ANSGR ile canli dogrulandi: 38.872.587.231 + 60.995.842.343
    = 99.868.429.574, referans kartla BIREBIR eslesiyor."""
    _require_ufrs_k(raw)
    cash = raw.value(STANDARD_ITEM_MAP_UFRS_K["cash_and_equivalents"], period)
    financial = raw.value(STANDARD_ITEM_MAP_UFRS_K["financial_assets"], period)
    if cash is None and financial is None:
        return None
    return (cash or Decimal(0)) + (financial or Decimal(0))


def technical_provisions_ufrs_k(raw: RawFinancials, period: Period) -> Decimal | None:
    """Teknik Karsiliklar = Sigortacilik Teknik Karsiliklari (kisa vadeli,
    2E) + (uzun vadeli, 2MD) -- STOK deger. ANSGR ile canli dogrulandi:
    82.395.051.067 + 2.416.774.566 = 84.811.825.633, referans kartla
    BIREBIR eslesiyor."""
    _require_ufrs_k(raw)
    current = raw.value(STANDARD_ITEM_MAP_UFRS_K["technical_provisions_current"], period)
    noncurrent = raw.value(STANDARD_ITEM_MAP_UFRS_K["technical_provisions_noncurrent"], period)
    if current is None and noncurrent is None:
        return None
    return (current or Decimal(0)) + (noncurrent or Decimal(0))


# --- Gunluk kapanis fiyati -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_price_history(company_code: str, start: date, end: date) -> dict:
    params = {
        "hisse": company_code,
        "startdate": start.strftime("%d-%m-%Y"),
        "enddate": end.strftime("%d-%m-%Y"),
    }
    try:
        response = httpx.get(PRICE_ENDPOINT, params=params, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("Is Yatirim fiyat istegi basarisiz, yeniden denenecek: %s", exc)
        raise

    if response.status_code != 200:
        raise IsYatirimNetworkError(f"Is Yatirim fiyat uc noktasi beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise IsYatirimNetworkError("Is Yatirim fiyat yaniti JSON olarak ayristirilamadi.") from exc


def fetch_latest_price(ticker: str, lookback_days: int = 10) -> Decimal | None:
    """Son `lookback_days` gunun gunluk kapanis fiyatlarini ceker (haftasonu/
    resmi tatil bosluklarini tolere etmek icin birkac gunluk pencere kullanilir),
    EN GUNCEL islem gununun kapanis fiyatini (HGDG_KAPANIS) doner. Sirket icin
    hic veri yoksa (yanlis kod, yeni halka arz vb.) None doner -- bu
    supplementary bir veridir, kartin geri kalanini BLOKE ETMEMELI.

    Hatalar:
        IsYatirimNetworkError: Ag hatasi (timeout, DNS, beklenmeyen yanit).
    """
    company_code = normalize_company_code(ticker)
    end = date.today()
    start = end - timedelta(days=lookback_days)
    payload = _request_price_history(company_code, start, end)

    rows = payload.get("value") or []
    if not rows:
        return None

    latest_row = rows[-1]  # API artan tarih sirasinda doner, sonuncusu en guncel
    return _parse_decimal(latest_row.get("HGDG_KAPANIS"))


def fetch_price_history(ticker: str, days: int = 400) -> list[dict]:
    """Son `days` gunun GUNLUK OHLCV serisini doner (Faz 15 - teknik analiz).

    Kesif (scripts/explore_price_history.py THYAO --market BIST --days 400,
    2026-08-03) CANLI olarak dogruladi: HisseTekil uc noktasi sadece kapanis
    DEGIL, tam bir gunluk seri donuyor -- her satirda IKI ayri fiyat ailesi var:
      - 'HGDG_*' (KAPANIS/AOF/MIN/MAX/HACIM): sermaye artirimi/temettu gibi
        kurumsal aksiyonlara gore GERIYE DUZELTILMIS (adjusted) seri --
        THYAO'da 400 gunluk pencerede eski bir HGDG_KAPANIS (280,6087) ile
        HG_KAPANIS'in (283,5) FARKLI oldugu, en guncel satirda ikisinin
        AYNI (314,0) oldugu canli gozlemlendi (araya bir kurumsal aksiyon
        girmis). Teknik analiz (SMA/EMA sureklilik, grafik) icin DOGRU
        secim budur -- duzeltilmemis seri kullanilirsa aksiyon gunu sahte
        bir fiyat "sicramasi" gosterir.
      - 'HG_*': DUZELTILMEMIS (nominal, o gunku gercek islem fiyati) seri --
        BU FONKSIYONDA KULLANILMAZ.
    ⚠️ 'AÇILIŞ' (open) alani uc noktada YOK (ne HGDG_ ne HG_ ailesinde acilis
    fiyati donuyor) -- bu yuzden her satirin 'open' anahtari HER ZAMAN None
    (Kural 8: veri yoksa uydurma). Faz 15'in istedigi hicbir gosterge (SMA/
    EMA/RSI/MACD/Bollinger/ATR/52 hafta/hacim) acilis fiyatina ihtiyac
    DUYMADIGI icin bu eksiklik hesaplamalari ETKILEMEZ.
    ⚠️ 'HGDG_HACIM'/'HG_HACIM' LOT/ADET DEGIL, TL cinsinden islem hacmidir
    (kesifte dogrulandi) -- mutlak degeri BIST'e ozgudur, NASDAQ'in hisse-
    adedi hacmiyle DOGRUDAN KARSILASTIRILAMAZ. Teknik analiz SADECE ayni
    hisse icindeki GORECELI (son hacim / 20 gunluk ortalama) kullanimla
    sinirli oldugu icin bu birim farki bir sorun TESKIL ETMEZ.

    Doner: [{"date": date, "open": None, "high": Decimal, "low": Decimal,
             "close": Decimal, "volume": Decimal}, ...] artan tarih sirasinda.
    Sirket icin veri yoksa (yanlis kod, yeni halka arz) BOS liste doner --
    bu supplementary bir veridir, cagiran taraf (price_history.py) ASLA
    bunun icin pipeline'i bloke ETMEMELIDIR.

    Hatalar: FIRLATMAZ -- ag/parse hatalari yakalanip loglanir, bos liste doner.
    """
    company_code = normalize_company_code(ticker)
    end = date.today()
    start = end - timedelta(days=days)
    try:
        payload = _request_price_history(company_code, start, end)
    except (IsYatirimNetworkError, httpx.RequestError) as exc:
        logger.warning("%s icin fiyat gecmisi cekilemedi: %s", company_code, exc)
        return []

    rows = payload.get("value") or []
    bars: list[dict] = []
    for row in rows:
        raw_date = row.get("HGDG_TARIH")
        high = _parse_decimal(row.get("HGDG_MAX"))
        low = _parse_decimal(row.get("HGDG_MIN"))
        close = _parse_decimal(row.get("HGDG_KAPANIS"))
        volume = _parse_decimal(row.get("HGDG_HACIM"))
        if not raw_date or high is None or low is None or close is None:
            continue
        try:
            bar_date = datetime.strptime(raw_date, "%d-%m-%Y").date()
        except ValueError:
            logger.warning("Fiyat gecmisinde ayristirilamayan tarih atlandi: %r", raw_date)
            continue
        bars.append(
            {
                "date": bar_date,
                "open": None,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume if volume is not None else Decimal(0),
            }
        )
    return bars
