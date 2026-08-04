"""SEC EDGAR companyfacts uc noktasindan NASDAQ/ABD sirketlerinin ceyreklik
bilanco ve gelir tablosu verilerini ceker.

Kesif adiminda (scripts/explore_sec.py) AAPL (klasik urun sirketi), NVDA
(takvim yiliyla ORTUSMEYEN mali yil -- Ocak sonu biter) ve JPM (banka --
XI_29'daki gibi FARKLI kalem seti) icin GERCEK canli yanitlar incelendi
(data/exploration/ altinda saklidir). Bu yanitlardan dogrulanan gercekler:

- https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json (CIK 10
  haneye SIFIRLA doldurulur) bir sirketin TUM tarihsel XBRL fact'lerini TEK
  istekte doner -- Is Yatirim'in aksine "en fazla 4 donem/istek" siniri YOK,
  pencereleme/chunk'lama gerekmez.
- SEC "10 istek/sn/IP" hiz limiti uyguluyor (asilirsa ~10 dk IP blogu);
  User-Agent header'i ACIKLAYICI olmak ZORUNDA (orn. "QuaxisLabs Bilanco
  Radar <email>"), aksi halde 403 doner (canli dogrulandi).
- Her XBRL fact'i {start, end, val, form, fp, fy, frame, filed} alanlarini
  tasir. fp SADECE {None, "Q1", "Q2", "Q3", "FY"} degerlerini alir -- "Q4"
  HICBIR ZAMAN literal olarak gelmez (canli dogrulandi, AAPL 2010-2026 arasi
  TUM NetIncomeLoss fact'leri tarandi). Yillik 10-K'nin fp="FY" degeri her
  zaman TAM YIL kumulatiftir (Ocak-Aralik DEGIL, sirketin KENDI mali yili).
- Gelir tablosu/nakit akis kalemleri (3*/4* itemCode'lariyla AYNI kavram)
  KUMULATIFTIR (YTD) -- Is Yatirim'daki durumun BIREBIR AYNISI. Ayni
  (fy, fp) icin BAZEN dogrudan TEK CEYREKLIK bir fact de (start-end arasi
  ~90 gun, cogunlukla "frame" alani CYyyyyQn ile dolu) raporlanir (orn.
  AAPL/NVDA'nin 10-Q'sundaki "3 Months Ended" kolonu) -- ANCAK bu CEVRIMDE
  BILEREK KULLANILMADI (bkz. asagidaki not): guvenilirligi sirketten
  sirkete/donem'den doneme DEGISKEN (JPM eski verisinde bazen YOK), bu
  yuzden Is Yatirim'la BIREBIR AYNI, HER ZAMAN calisan yontem -- kumulatiften
  ceyreklik TURETME (quarterly_value_from_cumulative ile AYNI ilke,
  fp="FY" - fp="Q3" = fiskal 4. ceyrek) -- TEK yontem olarak kullanildi.
  Dogrudan tek-ceyreklik fact'i ONCELIKLI kullanmak GELECEKTE bir dogruluk
  iyilestirmesi olarak degerlendirilebilir (KESIFTE bulundu, henuz
  ETKINLESTIRILMEDI -- Kural 8: "yanlis rakamdan iyidir" ilkesi geregi
  ONCE tek, ongorulebilir/regresyonu test edilebilir yontemle baslandi).
- Bilanco kalemleri (Assets, StockholdersEquity, Cash, ...) INSTANT (STOK)
  degerdir -- start=None, sadece "end" tarihi vardir; Is Yatirim'daki gibi
  kumulatif duzeltme YAPILMAZ. INSTANT fact'ler de fy/fp tasir (o mali
  ceyregin SONUNDAKI bakiye) -- bu, kumulatif VE stok alanlarin AYNI
  (fy, fp) anahtariyla sorgulanabilmesini saglar.
- Ayni kavram icin BIRDEN FAZLA XBRL tag'i olabilir (orn. "Revenues" vs
  "RevenueFromContractWithCustomerExcludingAssessedTax") -- hangisinin
  KULLANILDIGI sirkete VE DONEME gore DEGISIR (AAPL/NVDA 2018 civarinda tag
  degistirdi; JPM/bankalar hic "RevenueFromContractWithCustomer..." veya
  "GrossProfit"/"OperatingIncomeLoss" KULLANMAZ). Bu yuzden esleme sirket
  bazinda SABIT DEGIL -- STANDARD_ITEM_MAP_US_GAAP her alan icin bir ONCELIK
  LISTESI tutar, standardized_value_us_gaap() ilk ADAY tag'den ISTENEN
  DONEM icin deger BULUNANI kullanir (bkz. asagidaki modul ici not).
- Fiscal year (mali yil) takvim yiliyla ORTUSMEYEBILIR (NVDA: mali yil
  ~Ocak sonu biter). Bu modul mali ceyregi TAKVIM ceyregine ZORLA
  ESLEMEZ (uydurma olur, Kural 8 ihlali) -- Period=(fiscal_year, fp*3)
  SIRKETIN KENDI mali yili/ceyregidir ("year" alani takvim yili DEGIL, SEC
  'fy' alanidir). calculator.py'nin (fy,fp) uzerinde sadece SIRALAMA
  matematigi yaptigi icin (takvim anlamina bakmadan) bu tamamen uyumludur;
  gercek takvim tarihini gostermek isteyen bir kart/analiz katmani (Faz 10)
  sirketin kendi "FYyy Qn" etiketini KULLANMALI, takvim ceyregi UYDURMAMALI.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config

logger = logging.getLogger(__name__)

TICKERS_ENDPOINT = "https://www.sec.gov/files/company_tickers.json"
COMPANYFACTS_ENDPOINT = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"

# yfinance kutuphanesi EKLEMEK yerine, yfinance'in de altta kullandigi AYNI
# halka acik uc noktaya (query1.finance.yahoo.com) dogrudan httpx ile
# gidiyoruz -- projenin geri kalaniyla TUTARLI (isyatirim.py de ayni
# sekilde httpx ile dogrudan HTML/JSON uc noktasina gidiyor, ek bagimlilik
# YOK). Stooq CSV ALTERNATIFI CANLI denendi (2026-08-02): artik bir
# JavaScript bot-dogrulama sayfasi donduruyor (200 OK ama HTML/JS, CSV
# DEGIL) -- sunucu tarafindan basit bir HTTP istegiyle KULLANILAMAZ hale
# gelmis, bu yuzden REDDEDILDI.
PRICE_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

# SEC.gov: kullanici e-postasi ZORUNLU VE ACIKLAYICI olmali, aksi halde 403
# doner (canli dogrulandi). CLAUDE.md kullanici e-postasi kullanildi.
USER_AGENT = "QuaxisLabs Bilanco Radar serefsamet2021@gmail.com"

_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}
_PRICE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

_CACHE_DIR = config.DATA_DIR / "cache"
_TICKER_MAP_CACHE_PATH = _CACHE_DIR / "sec_company_tickers.json"
_TICKER_MAP_CACHE_MAX_AGE_HOURS = 24

Period = tuple[int, int]  # (fiscal_year, fiscal_period); fiscal_period in {3, 6, 9, 12} = fp Q1..Q4 * 3


# --- Hata siniflari -----------------------------------------------------


class SecEdgarError(Exception):
    """SEC EDGAR fetcher'i icin taban hata sinifi."""


class CompanyNotFoundError(SecEdgarError):
    """Ticker company_tickers.json icinde bulunamadi VEYA SEC bu CIK icin
    companyfacts dondurmuyor (XBRL raporlamayan/cok yeni bir sirket olabilir)."""


class FinancialDataNotAvailableError(SecEdgarError):
    """Sirket dogrulandi ama istenen donem(ler) icin hicbir standart alanda
    veri turetilemedi."""


class SecEdgarNetworkError(SecEdgarError):
    """SEC'e ag seviyesinde ulasilamadi (timeout, DNS, beklenmeyen yanit)
    veya yanit beklenmeyen bicimde geldi."""


class UnsupportedTaxonomyError(SecEdgarError):
    """Bilinmeyen/desteklenmeyen bir alan adi istendi (STANDARD_ITEM_MAP_US_GAAP'ta yok)."""


# --- Veri modelleri -----------------------------------------------------


@dataclass(frozen=True)
class ConceptFact:
    """Tek bir XBRL fact'i (bir tag'in bir donem/context icin degeri)."""

    start: date | None  # None ise INSTANT (bilanco) deger
    end: date
    val: Decimal
    form: str
    fp: str | None  # "Q1" / "Q2" / "Q3" / "FY" / None
    fy: int | None
    frame: str | None
    filed: str | None


@dataclass(frozen=True)
class RawUsFinancials:
    """Bir ABD sirketinin cekilen tum donemler icin ham XBRL verisi."""

    ticker: str
    cik10: str
    company_name: str | None
    periods: list[Period]  # (fiscal_year, fiscal_period) -- yeniden eskiye
    facts_by_tag: dict[str, list[ConceptFact]]  # "us-gaap:Assets" -> fact listesi


# --- Kalem esleme tablosu (SADECE US GAAP -- STANDARD_ITEM_MAP_US_GAAP) --
#
# AAPL (urun sirketi), NVDA (takvim-disi mali yil) VE JPM (banka) ile
# CANLI dogrulandi (bkz. data/exploration/{AAPL,NVDA,JPM}_ozet_*.txt).
# Deger: ADAY tag ONCELIK LISTESI -- standardized_value_us_gaap() ilk
# tag'ten baslayarak ISTENEN DONEM icin veri bulunanı kullanir (bkz. modul
# ust notu, "Aynı kavram icin birden fazla tag" maddesi).
STANDARD_ITEM_MAP_US_GAAP: dict[str, list[str]] = {
    # --- Gelir tablosu (KUMULATIF -> quarterly_standardized_value_us_gaap ile ceyreklestirin) ---
    "revenue": [
        # AAPL + NVDA (2018 sonrasi) bu tag'i kullaniyor -- CANLI dogrulandi.
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        # JPM (banka) VE AAPL/NVDA'nin 2018 ONCESI verisi bu ESKI tag'i
        # kullaniyor -- CANLI dogrulandi (JPM'de "RevenueFromContractWith
        # Customer..." HIC yok, sadece bu tag var).
        "us-gaap:Revenues",
        # ASTS (genc/kucuk NASDAQ sirketi, §B17) 2025 Ç1'den itibaren YUKARIDAKI
        # IKI tag'i de birakip bu ucuncu varyanta GECTI -- CANLI dogrulandi
        # (data/exploration/ASTS_companyfacts_*.json): "ExcludingAssessedTax"
        # VE "Revenues" ikisi de FY2024'te KESILIYOR (son veri noktasi
        # 2024-12-31), 2025/2026 verisi SADECE bu tag'de var (2026 Ç1 icin
        # 14.735.000 USD, dogrudan ceyreklik sure ile). "IncludingAssessedTax"
        # (satis vergisi DAHIL) "Excluding" ile ayni muhasebe kavramini
        # (hasilat) temsil eder, sadece vergi dahil/haric ayrimi degisir --
        # ExcludingAssessedTax/Revenues zaten YOKSA (o donem icin) burada
        # kullanilir, bu yuzden cift sayim riski yok.
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
        # B21 (ADR/yabanci ozel ihracci -- NVO/TSM/SHEL): bu sirketler
        # `us-gaap` YERINE `ifrs-full` ad alanini kullanir, 20-F dosyalar
        # (SADECE yillik, fp="FY"). CANLI dogrulandi (scripts/explore_ifrs.py):
        # NVO 253 tag, TSM 334 tag, SHEL 333 tag -- ucunde de "Revenue" tag'i
        # VAR ve fp dagilimi TAMAMEN/COGUNLUKLA 'FY'. Ayni aday-liste ilkesi
        # geregi buraya EKLENIR (ayri bir "STANDARD_ITEM_MAP_IFRS_FULL"
        # GEREKMEZ) -- us-gaap tag'leri hicbirinde YOK oldugundan (ifrs-full
        # kullanan sirketlerde) bu aday HER ZAMAN us-gaap denemelerinden
        # SONRA devreye girer, mevcut us-gaap sirketlerini ETKILEMEZ.
        "ifrs-full:Revenue",
    ],
    # NOT: "gross_profit"/"operating_profit" JPM'de (banka) HIC raporlanmiyor
    # (CANLI dogrulandi: us-gaap:GrossProfit VE us-gaap:OperatingIncomeLoss
    # ikisi de JPM'nin XBRL faktlerinde YOK) -- BIST UFRS (banka) semasinda
    # da bu iki kavramin olmamasiyla AYNI durum, kart/analiz katmani (Faz 10)
    # bu alanlari None/N-A gostermeye HAZIR olmali.
    #
    # NOT (10 resmi NASDAQ hissesinin TAMAMI canli tarandi, 2026-08-02):
    # GOOGL/AMZN/META/NFLX/PYPL de "GrossProfit" tag'ini GUNCEL donemde HIC
    # kullanmiyor (AMZN/NFLX'te tag GECMISTE var ama YILLARDIR guncellenmemis
    # -- son NFLX verisi 2020, son AMZN verisi 2009). Bu 5 sirket icin
    # standardized_value_us_gaap("gross_profit", ...) YINE None doner (bu
    # alan haritasi DEGISMEDI) -- DOGRU/DOGRULANMIS deger ISTEYEN caller
    # `gross_profit_us_gaap()`/`quarterly_gross_profit_us_gaap()` fonksiyonlarini
    # KULLANMALI (asagida, isyatirim.total_revenue() ile AYNI desen): once bu
    # DOGRUDAN tag'i dener, yoksa Hasilat - Satislarin Maliyeti (asagidaki
    # "cost_of_revenue" ic alani) turetir.
    "gross_profit": ["us-gaap:GrossProfit", "ifrs-full:GrossProfit"],
    # SADECE gross_profit_us_gaap() turetmesi icin ic (internal) alan --
    # pipeline._standardize_to_records_us_gaap() bunu DOGRUDAN DB'ye YAZMAZ
    # (isyatirim.py'deki "3CAC" finans segmenti geliri ic kalemiyle AYNI
    # ilke). CANLI DOGRULANDI (stockanalysis.com ile BIREBIR eslesti):
    #   GOOGL 2026 Ç2: Hasilat $119.796mr - CostOfRevenue $45.943mr =
    #     $73.853mr Brut Kar (stockanalysis.com: $73.853mr)
    #   NFLX  2026 Ç2: $12.560mr - $6.037mr = $6.523mr (stockanalysis.com: $6.523mr)
    #   AMZN  2026 Ç2: $200.606mr - $95.778mr = $104.828mr (stockanalysis.com: $104.828mr)
    #   META  2026 Ç1: $56.311mr - $10.218mr = $46.093mr (%81,85 brut marj --
    #     stockanalysis.com'un Ç2 2026 icin raporladigi %81,36 marjla TUTARLI,
    #     ayni ceyrek icin BIREBIR karsilastirma YAPILAMADI cunku SEC'in
    #     companyfacts API'si META'nin Ç2 2026 10-Q'sunu HENUZ islememisti
    #     -- bkz. 06_BILINEN_SORUNLAR.md, SEC verisi CANLI earnings
    #     paylasimlarindan birkac gun GERIDE kalabiliyor).
    #   PYPL: HICBIR maliyet tag'i (CostOfRevenue/CostOfGoodsAndServicesSold/
    #     CostsAndExpenses) PYPL'in XBRL verisinde YOK -- turetme YAPILAMAZ,
    #     None kalir (Kural 8: yanlis rakamdan iyidir).
    "cost_of_revenue": [
        "us-gaap:CostOfRevenue",  # GOOGL/META/NFLX
        "us-gaap:CostOfGoodsAndServicesSold",  # AMZN
        "ifrs-full:CostOfSales",  # B21 -- NVO/TSM/SHEL (CANLI dogrulandi)
    ],
    "operating_profit": [
        "us-gaap:OperatingIncomeLoss",
        "ifrs-full:ProfitLossFromOperatingActivities",  # B21 -- NVO/TSM/SHEL (CANLI dogrulandi)
    ],
    "net_income": [
        "us-gaap:NetIncomeLoss",
        # B21 -- IFRS'te "ana ortaklik payi" (NCI HARIC) ile toplam kar/zarar
        # (NCI DAHIL) AYRI tag'lerdir; ABD GAAP'teki "NetIncomeLoss" (ana
        # ortaklik payi) ile daha KARSILASTIRILABILIR olan bu YUZDEN ONCE
        # denenir. CANLI dogrulandi: TSM VE SHEL'de ikisi de mevcut; NVO'da
        # SADECE "ProfitLoss" var (NVO'nun onemli bir azinlik payi/NCI'si
        # yok, ikisi zaten esit).
        "ifrs-full:ProfitLossAttributableToOwnersOfParent",
        "ifrs-full:ProfitLoss",
    ],
    "depreciation_amortization": [
        # AAPL + NVDA bu tag'i kullaniyor.
        "us-gaap:DepreciationDepletionAndAmortization",
        # JPM (banka) bu FARKLI tag'i kullaniyor -- CANLI dogrulandi
        # ("DepreciationDepletionAndAmortization" JPM'de YOK).
        "us-gaap:DepreciationAmortizationAndAccretionNet",
        # B21 -- TSM/SHEL birlesik bu tag'i kullaniyor (CANLI dogrulandi).
        "ifrs-full:DepreciationAndAmortisationExpense",
    ],
    # SADECE depreciation_amortization_us_gaap() turetmesi icin ic (internal)
    # alanlar -- pipeline._standardize_to_records_us_gaap() bunlari DOGRUDAN
    # DB'ye YAZMAZ (cost_of_revenue ic alaniyla AYNI ilke). CANLI hata
    # (kullanici raporu, 2026-08-02): MSFT'nin gelir tablosunda (kart) FAVOK
    # satiri EKSIKTI (5 yerine 4 metrik gorunuyordu) -- kok neden MSFT'nin
    # yukaridaki IKI birlesik D&A tag'ini de HIC kullanmamasi (CANLI
    # dogrulandi: DepreciationDepletionAndAmortization VE
    # DepreciationAmortizationAndAccretionNet MSFT'de YOK), bunun yerine
    # amortismani Depreciation (maddi duran varlik) ve
    # AmortizationOfIntangibleAssets (maddi olmayan duran varlik) olarak IKI
    # AYRI satirda raporluyor. depreciation_amortization_us_gaap() once
    # birlesik tag'i dener, yoksa bu ikisini TOPLAR. CANLI dogrulandi (web
    # aramasi, gurufocus.com): MSFT FY2026 Ç3 (Ocak-Mart 2026) icin
    # Depreciation $9,0mr + AmortizationOfIntangibleAssets $1,1mr = $10,1mr
    # -- gurufocus'un raporladigi birlesik "$10.167mr" ile %1'in ALTINDA
    # farkla eslesiyor.
    "depreciation_component": [
        "us-gaap:Depreciation",
        # B21 -- NVO birlesik D&A tag'ini kullanmiyor, bu ikisini AYRI
        # raporluyor (CANLI dogrulandi); "DepreciationExpense" TSM'de de var.
        "ifrs-full:DepreciationExpense",
        "ifrs-full:DepreciationPropertyPlantAndEquipmentIncludingRightofuseAssets",
    ],
    "amortization_component": [
        "us-gaap:AmortizationOfIntangibleAssets",
        "ifrs-full:AmortisationIntangibleAssetsOtherThanGoodwill",  # B21 -- NVO (CANLI dogrulandi)
    ],
    # --- Bilanco (STOK deger -- kumulatif duzeltme YAPILMAZ) ---
    "total_assets": ["us-gaap:Assets", "ifrs-full:Assets"],
    # NOT: JPM'de (banka) "AssetsCurrent" HIC raporlanmiyor (CANLI dogrulandi)
    # -- bankalarin bilancosu donen/duran varlik ayrimi YAPMAZ, BIST UFRS
    # semasinda da bu ayrim YOK (bkz. isyatirim.STANDARD_ITEM_MAP_UFRS).
    "current_assets": ["us-gaap:AssetsCurrent", "ifrs-full:CurrentAssets"],
    # Faz 10 (analyze_us -> current_ratio) icin eklendi -- AAPL FY2024 ile
    # CANLI dogrulandi: LiabilitiesCurrent = $176.392 mr, Apple'in FY2024
    # 10-K'sindeki "Total current liabilities" rakamiyla BIREBIR eslesiyor.
    # JPM'de (banka) HIC raporlanmiyor -- current_assets ile AYNI sebep
    # (bankalar donen/duran ayrimi YAPMAZ, BIST UFRS'te de bu alan YOK).
    "short_term_liabilities": ["us-gaap:LiabilitiesCurrent", "ifrs-full:CurrentLiabilities"],
    "equity": ["us-gaap:StockholdersEquity", "ifrs-full:Equity"],
    # Faz 10 icin eklendi (BIST XI_29'daki "Ticari Alacaklar" karsiligi) --
    # AAPL FY2024 ile CANLI dogrulandi: $33.410 mr, Apple'in FY2024 10-K'sindeki
    # "Accounts receivable, net" rakamiyla BIREBIR eslesiyor. JPM'de (banka)
    # HIC raporlanmiyor -- bankalarin "ticari alacak" kavrami YOK (musteri
    # kredileri "loans" olarak AYRI izlenir), BIST UFRS'te de bu alan YOK.
    "trade_receivables": ["us-gaap:AccountsReceivableNetCurrent"],
    "cash": [
        # AAPL + NVDA GUNCEL veride bu tag'i kullaniyor.
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        # JPM bu tag'i SADECE 2018'e KADAR kullandi, SONRASINDA (2019+)
        # SADECE bu ALTERNATIF tag'e gecti (CANLI dogrulandi: "CashAndCash
        # EquivalentsAtCarryingValue" JPM'de en son 2018-12-31 icin var,
        # 2019 sonrasi TUM JPM nakit verisi SADECE bu tag'de) -- AAPL/NVDA'da
        # ikisi de AYNI degeri tasiyor (restricted cash yok), JPM'de FARKLI
        # (restricted cash dahil) -- bu yuzden JPM icin "cash" alani KATI
        # anlamda "serbest nakit" degil, "nakit + kisitli nakit" olabilir
        # (bilinen bir yaklastirma, KAP/Fintables gibi bagimsiz bir
        # referansla henuz dogrulanmadi).
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "ifrs-full:CashAndCashEquivalents",  # B21 -- NVO/TSM/SHEL (CANLI dogrulandi)
    ],
    # NOT: "kisa/uzun vadeli finansal borc" icin JPM (banka) TAMAMEN FARKLI
    # tag'ler kullaniyor (AAPL/NVDA'nin "LongTermDebtCurrent/Noncurrent"
    # cifti JPM'de HIC yok) -- CANLI dogrulandi.
    "short_term_financial_debt": [
        "us-gaap:LongTermDebtCurrent",  # AAPL + NVDA
        "us-gaap:ShortTermBorrowings",  # JPM (banka)
        # B21 -- IFRS'te "kisa vadeli finansal borc" iki AYRI tag'e
        # bolunebiliyor (uzun vadeli borcun bu yilki taksiti + saf kisa
        # vadeli borclanma); bu aday liste ilkesi (ILK bulunan kullanilir,
        # TOPLANMAZ) geregi CurrentPortionOfLongtermBorrowings ONCE denenir
        # (CANLI dogrulandi: NVO/TSM/SHEL ucunde de mevcut) -- bilinen bir
        # yaklastirma, saf ShorttermBorrowings AYRICA varsa o GORULMEZ.
        "ifrs-full:CurrentPortionOfLongtermBorrowings",
        "ifrs-full:ShorttermBorrowings",
    ],
    "long_term_financial_debt": [
        "us-gaap:LongTermDebtNoncurrent",  # AAPL + NVDA
        "us-gaap:LongTermDebt",  # JPM (banka) -- JPM'de "Noncurrent" varyanti YOK,
        # bankalarin bilancosunda "Uzun Vadeli Borclar" ZATEN tek bir kalem
        # olarak (cari/cari-disi ayrimi olmadan) raporlaniyor (CANLI
        # dogrulandi: deger buyuklugu JPM'nin toplam borclanma programiyla
        # TUTARLI, ayrica bir "current" varyantiyla CIFT SAYILMIYOR).
        "ifrs-full:LongtermBorrowings",  # B21 -- NVO/TSM/SHEL (CANLI dogrulandi)
    ],
    # Piyasa degeri (fiyat x pay adedi) girdisi -- BIST'teki "share_capital"
    # (odenmis sermaye, TL nominal deger) KAVRAMSAL OLARAK FARKLIDIR; ABD
    # sirketlerinde nominal pay degeri YOK, piyasa degeri dogrudan pay
    # ADEDIYLE carpilir. Bu yuzden BIST'teki "share_capital" alan adi
    # YENIDEN KULLANILMADI, ayri bir alan adi ("shares_outstanding")
    # tanimlandi -- Faz 10 (kart) piyasa degerini price * shares_outstanding
    # olarak hesaplamali, share_capital MANTIGINI (fiyat * nominal sermaye)
    # KULLANMAMALI.
    "shares_outstanding": [
        # dei ad alani (taxonomy) -- 10-Q/10-K kapak sayfasindaki (cover
        # page) pay adedi, ceyrek SONU bilanco tarihinden birkac hafta
        # SONRAKI (dosyalama tarihine yakin) bir "as of" tarihi tasir --
        # CANLI dogrulandi (NVDA: bilanco tarihi 2026-04-26 iken bu fact'in
        # "end" tarihi 2026-05-15). Piyasa degeri yaklastirmasi icin yeterli
        # (pay adedi kisa surede COK degismez) ama TAM bilanco tarihiyle
        # BIREBIR ayni tarihte DEGIL -- bilinen bir yaklastirma.
        "dei:EntityCommonStockSharesOutstanding",
        # us-gaap ad alanindaki alternatif -- "end" tarihi genelde BILANCO
        # tarihinin KENDISIYLE eslesir (daha "temiz") ama fy/fp etiketleri
        # dei tag'i kadar TUTARLI doldurulmamis olabilir; bu yuzden IKINCIL.
        "us-gaap:CommonStockSharesOutstanding",
        # UCUNCUL yedek -- CANLI dogrulandi: META'da (10 resmi NASDAQ hissesi
        # taramasinda bulundu) YUKARIDAKI IKI tag de HIC YOK (dei namespace'i
        # SADECE "EntityPublicFloat" iceriyor, us-gaap'ta "SharesOutstanding"
        # gecen HICBIR tag YOK) -- muhtemelen Class A/Class B pay sinifi
        # boyutlandirmasi (dimensional) yuzunden bulk companyfacts API'sinde
        # boyutsuz (varsayilan) bir toplam hic YAYINLANMAMIS. Bu DURUM SADECE
        # ANLIK (point-in-time) degil, DONEM ORTALAMASI (weighted average,
        # bir sure/duration fact) bir kalemdir -- _select_best_fact zaten
        # DURATION facts'i ~90 gunluk ceyrek uzunluguna filtreler (bkz.
        # _EXPECTED_CUMULATIVE_DURATION_DAYS), bu yuzden ekstra kod GEREKMEZ.
        # CANLI DOGRULANDI: META FY2026 Ç1 (2026-01-01/2026-03-31) icin bu
        # tag 2.564.000.000 doner -- macrotrends.net'in bagimsiz olarak
        # raporladigi "shares outstanding for quarter ending March 31, 2026:
        # 2.564B" ile BIREBIR eslesiyor. Bilinen yaklastirma: DONEM
        # ORTALAMASI, o donemin SONUNDAKI ANLIK bakiye DEGIL (buyback/ihrac
        # yogun donemlerde kucuk bir sapma olusturabilir).
        "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
}

# Gelir tablosu / nakit akis alanlari kumulatiftir (mali yil icinde YTD
# toplanir) -- Is Yatirim'daki CUMULATIVE_FIELDS ile AYNI ilke, SADECE alan
# adlari BIST XI_29 ile TUTARLI tutuldu (Faz 10'da calculator.py'nin
# DOGRUDAN yeniden kullanilabilmesi icin).
CUMULATIVE_FIELDS_US_GAAP: frozenset[str] = frozenset(
    {
        "revenue", "gross_profit", "cost_of_revenue", "operating_profit", "net_income",
        "depreciation_amortization", "depreciation_component", "amortization_component",
    }
)

_STOCK_FIELDS_US_GAAP: frozenset[str] = frozenset(
    {
        "total_assets",
        "current_assets",
        "short_term_liabilities",
        "equity",
        "cash",
        "trade_receivables",
        "short_term_financial_debt",
        "long_term_financial_debt",
        "shares_outstanding",
    }
)

# fp etiketi -> (mali yil basindan itibaren BEKLENEN sure araligi, gun).
# _select_best_fact() bu araliga en iyi UYAN fact'i secer -- bazi eski
# 10-K'lerde "Secilmis Ceyreklik Veri" dipnotundan gelen GURULTU (tek
# ceyreklik ama fp="FY" etiketli, CANLI gozlemlendi AAPL 2010 verisinde)
# bu sekilde ELENIR.
_EXPECTED_CUMULATIVE_DURATION_DAYS: dict[str, tuple[int, int]] = {
    "Q1": (75, 100),
    "Q2": (165, 200),
    "Q3": (255, 290),
    "FY": (350, 380),
}

_FP_LABELS: dict[int, str] = {3: "Q1", 6: "Q2", 9: "Q3", 12: "FY"}


def previous_quarter_period(period: Period) -> Period:
    """isyatirim.previous_quarter()/calculator.previous_quarter_period() ile
    AYNI ilke: bir onceki mali CEYREGIN (fiscal_year, fiscal_period) ciftini
    doner (fiscal_period ∈ {3,6,9,12} -- pozisyonel Ç1..Ç4, bkz. modul ust
    notu §6.4 NVDA takvim-disi mali yil aciklamasi)."""
    year, fiscal_period = period
    if fiscal_period == 3:
        return year - 1, 12
    return year, fiscal_period - 3


def _period_end_date(raw: RawUsFinancials, period: Period) -> date | None:
    """Verilen (fy, fiscal_period) donemi icin GERCEK bilanco/donem sonu
    tarihini doner -- net_income HEMEN HEMEN HER filer'da bulunan tek alan
    oldugu icin (bkz. _discover_available_periods() ust notu) guvenilir bir
    "bu donem ne zaman bitti" gostergesi olarak kullanilir."""
    fy, fiscal_period = period
    fp_label = _FP_LABELS[fiscal_period]
    for tag in STANDARD_ITEM_MAP_US_GAAP["net_income"]:
        fact = _select_best_fact(raw.facts_by_tag.get(tag, []), fy, fp_label)
        if fact is not None:
            return fact.end
    return None


# --- Yardimci: ticker normalize / CIK cozumleme -----------------------------------------------------


def normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def _ensure_cache_dir() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _ticker_map_cache_is_fresh() -> bool:
    if not _TICKER_MAP_CACHE_PATH.exists():
        return False
    age_hours = (time.time() - _TICKER_MAP_CACHE_PATH.stat().st_mtime) / 3600
    return age_hours <= _TICKER_MAP_CACHE_MAX_AGE_HOURS


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_ticker_map() -> dict:
    try:
        response = httpx.get(TICKERS_ENDPOINT, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("SEC company_tickers.json istegi basarisiz, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise SecEdgarNetworkError(f"SEC company_tickers.json beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise SecEdgarNetworkError("SEC company_tickers.json JSON olarak ayristirilamadi.") from exc


def _load_ticker_map() -> dict[str, str]:
    """{TICKER: cik10} -- data/cache/sec_company_tickers.json altinda GUNLUK
    yerel onbellek (dosya yasi 24 saati asarsa yeniden cekilir)."""
    if _ticker_map_cache_is_fresh():
        try:
            raw = json.loads(_TICKER_MAP_CACHE_PATH.read_text(encoding="utf-8"))
            return raw
        except (ValueError, OSError) as exc:
            logger.warning("SEC ticker onbellegi okunamadi, yeniden cekilecek: %s", exc)

    payload = _request_ticker_map()
    by_ticker: dict[str, str] = {}
    for row in payload.values():
        ticker = str(row.get("ticker", "")).upper()
        cik = row.get("cik_str")
        if ticker and cik is not None:
            by_ticker[ticker] = f"{int(cik):010d}"

    _ensure_cache_dir()
    try:
        _TICKER_MAP_CACHE_PATH.write_text(json.dumps(by_ticker), encoding="utf-8")
    except OSError as exc:
        logger.warning("SEC ticker onbellegi yazilamadi (bir sonraki cagrida tekrar cekilecek): %s", exc)

    return by_ticker


def resolve_cik(ticker: str) -> str:
    """'AAPL' -> '0000320193'. Ticker bulunamazsa CompanyNotFoundError."""
    ticker = normalize_ticker(ticker)
    ticker_map = _load_ticker_map()
    cik10 = ticker_map.get(ticker)
    if cik10 is None:
        raise CompanyNotFoundError(
            f"'{ticker}' SEC company_tickers.json icinde bulunamadi. Ticker'i kontrol edin "
            "(NASDAQ/NYSE disi bir sembol olabilir veya SEC'e hic XBRL raporlamamis olabilir)."
        )
    return cik10


# --- HTTP katmani -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_companyfacts(cik10: str) -> dict:
    url = COMPANYFACTS_ENDPOINT.format(cik10=cik10)
    try:
        response = httpx.get(url, headers=_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        logger.warning("SEC companyfacts istegi basarisiz, yeniden denenecek: %s", exc)
        raise

    if response.status_code == 404:
        raise CompanyNotFoundError(
            f"SEC CIK{cik10} icin companyfacts bulunamadi (sirket XBRL raporlamiyor olabilir)."
        )
    if response.status_code != 200:
        raise SecEdgarNetworkError(f"SEC companyfacts beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise SecEdgarNetworkError("SEC companyfacts yaniti JSON olarak ayristirilamadi.") from exc


# --- Ham JSON -> ConceptFact donusumu -----------------------------------------------------


def _parse_decimal(raw_value: object) -> Decimal | None:
    if raw_value is None:
        return None
    try:
        return Decimal(str(raw_value))
    except InvalidOperation:
        return None


def _parse_date(raw_value: object) -> date | None:
    if not raw_value:
        return None
    try:
        return date.fromisoformat(str(raw_value))
    except ValueError:
        return None


def _parse_facts_for_tag(payload: dict, tag: str) -> list[ConceptFact]:
    taxonomy, concept = tag.split(":", 1)
    node = payload.get("facts", {}).get(taxonomy, {}).get(concept)
    if node is None:
        return []
    units = node.get("units", {})
    raw_entries: list[dict] = []
    for unit_key in ("USD", "shares", "USD/shares"):
        if unit_key in units:
            raw_entries = units[unit_key]
            break
    else:
        for values in units.values():
            raw_entries = values
            break

    facts: list[ConceptFact] = []
    for entry in raw_entries:
        val = _parse_decimal(entry.get("val"))
        end = _parse_date(entry.get("end"))
        if val is None or end is None:
            continue
        facts.append(
            ConceptFact(
                start=_parse_date(entry.get("start")),
                end=end,
                val=val,
                form=str(entry.get("form") or ""),
                fp=entry.get("fp"),
                fy=entry.get("fy"),
                frame=entry.get("frame"),
                filed=entry.get("filed"),
            )
        )
    return facts


def _extract_relevant_facts(payload: dict) -> dict[str, list[ConceptFact]]:
    """STANDARD_ITEM_MAP_US_GAAP'ta gecen TUM aday tag'leri ham JSON'dan
    ayiklar (Faz gorevindeki alanlarin DISINDAKI onlarca gereksiz kavramin
    hafizada tutulmasini onler)."""
    all_tags: set[str] = set()
    for candidates in STANDARD_ITEM_MAP_US_GAAP.values():
        all_tags.update(candidates)

    facts_by_tag: dict[str, list[ConceptFact]] = {}
    for tag in all_tags:
        parsed = _parse_facts_for_tag(payload, tag)
        if parsed:
            facts_by_tag[tag] = parsed
    return facts_by_tag


# --- (fy, fp) bazinda "en iyi" fact secimi -----------------------------------------------------


def _select_best_fact(facts: list[ConceptFact], fy: int, fp_label: str) -> ConceptFact | None:
    """Verilen (fy, fp_label) icin ADAY fact'ler arasindan "en iyi" olani
    secer: STOK (instant, start=None) alanlar icin dogrudan eslesenler;
    KUMULATIF (duration) alanlar icin sure BEKLENEN araliga (bkz.
    _EXPECTED_CUMULATIVE_DURATION_DAYS) UYANLAR tercih edilir (eski 10-K'lerin
    "Secilmis Ceyreklik Veri" dipnotu gibi GURULTULU fact'leri elemek icin,
    bkz. modul ust notu).

    CANLI HATA (AAPL ile kesifte bulundu, bkz. data/exploration/AAPL_companyfacts_*):
    SEC 'fy'/'fp' alanlarini fact'in KENDI donemine gore DEGIL, ICINDE
    GECTIGI DOSYALAMANIN (accession/10-Q) donemine gore atiyor. Bir 10-Q'nun
    bilancosu HEM "bu ceyrek sonu" HEM "bir onceki mali yil sonu" (karsilastirma)
    kolonunu icerir -- SEC IKISINE DE O DOSYALAMANIN fy/fp'sini yapistiriyor.
    Ornek (AAPL, fy=2026, fp='Q1'): iki fact ayni (fy,fp) ile etiketli --
    end=2025-12-27 (GERCEK Ç1 FY26 bakiyesi) VE end=2025-09-27 (ONCEKI mali
    yil sonu karsilastirma kolonu, YANLIS). Ikisi de AYNI dosyalamadan
    geldigi icin 'filed' alani IKISINDE DE AYNI -- 'filed' ile ayirt
    edilemez. Cozum: karsilastirma kolonlari HER ZAMAN GERCEK donemden
    DAHA ESKI bir 'end' tarihi tasir (donemler geriye dogru karsilastirilir,
    ileriye degil) -- bu yuzden 'end' tarihi EN BUYUK (en yeni) olan fact
    secilir. Ayni 'end' tarihinde birden fazla fact kalirsa (restatement)
    'filed' ikincil kirici olarak kullanilir."""
    candidates = [f for f in facts if f.fy == fy and f.fp == fp_label]
    if not candidates:
        return None

    expected = _EXPECTED_CUMULATIVE_DURATION_DAYS.get(fp_label)
    if expected is not None:
        lo, hi = expected
        duration_matched = [
            f for f in candidates if f.start is not None and lo <= (f.end - f.start).days <= hi
        ]
        if duration_matched:
            candidates = duration_matched

    return max(candidates, key=lambda f: (f.end, f.filed or ""))


def _cumulative_value(facts: list[ConceptFact], fy: int, fiscal_period: int) -> Decimal | None:
    """fiscal_period in {3,6,9,12} (Q1..Q4*3) icin KUMULATIF (YTD) degeri doner."""
    fp_label = _FP_LABELS[fiscal_period]
    fact = _select_best_fact(facts, fy, fp_label)
    return fact.val if fact is not None else None


def _instant_value(facts: list[ConceptFact], fy: int, fiscal_period: int) -> Decimal | None:
    fp_label = _FP_LABELS[fiscal_period]
    fact = _select_best_fact(facts, fy, fp_label)
    return fact.val if fact is not None else None


def quarterly_value_from_cumulative_us_gaap(
    facts: list[ConceptFact], fy: int, fiscal_period: int
) -> Decimal | None:
    """isyatirim.quarterly_value_from_cumulative() ile AYNI ilke: TEK
    CEYREKLIK deger = bu donem kumulatif - onceki donem kumulatif. Mali
    yilin ilk ceyreginde (fiscal_period=3, fp="Q1") CIKARMA YAPILMAZ."""
    current = _cumulative_value(facts, fy, fiscal_period)
    if current is None:
        return None
    if fiscal_period == 3:
        return current

    previous = _cumulative_value(facts, fy, fiscal_period - 3)
    if previous is None:
        return None
    return current - previous


# --- Ana API: fetch_financials -----------------------------------------------------


def _discover_available_periods(facts_by_tag: dict[str, list[ConceptFact]]) -> list[Period]:
    """Hangi (fiscal_year, fiscal_period) ciftlerinin GERCEKTEN raporlandigini
    net_income (STANDARD_ITEM_MAP_US_GAAP['net_income']) fact'lerinden
    turetir -- net donem kari/zarari NEREDEYSE HER filer'da bulunan tek
    alan oldugu icin "bu donem var mi" sorusu icin GUVENILIR bir gostergedir."""
    candidates: set[Period] = set()
    for tag in STANDARD_ITEM_MAP_US_GAAP["net_income"]:
        for fact in facts_by_tag.get(tag, []):
            if fact.fy is None or fact.fp not in ("Q1", "Q2", "Q3", "FY"):
                continue
            fiscal_period = {"Q1": 3, "Q2": 6, "Q3": 9, "FY": 12}[fact.fp]
            expected = _EXPECTED_CUMULATIVE_DURATION_DAYS[fact.fp]
            if fact.start is None or not (expected[0] <= (fact.end - fact.start).days <= expected[1]):
                continue
            candidates.add((fact.fy, fiscal_period))
    return sorted(candidates, reverse=True)


# Derin Kart'in mevsimsellik karsilastirmasi icin en az 4 farkli yil
# gerekir -- isyatirim.DEFAULT_HISTORY_QUARTERS ile AYNI ilke/deger (16 ceyrek
# = 4 yil). SEC companyfacts zaten TEK istekte TUM tarihceyi dondugu icin
# bu degisiklik EK bir ag istegi GETIRMEZ, sadece zaten indirilmis veriden
# daha fazla donem dilimlenir (canli dogrulandi: AAPL icin 16 donem sorunsuz
# donuyor).
DEFAULT_HISTORY_QUARTERS = 16


def fetch_financials(ticker: str, periods: list[Period] | None = None, count: int = DEFAULT_HISTORY_QUARTERS) -> RawUsFinancials:
    """Bir NASDAQ/ABD sirketinin ceyreklik finansal tablolarini SEC EDGAR'dan
    ceker. Is Yatirim'in aksine TEK istekte TUM tarihce doner -- `periods`
    verilmezse net_income'dan turetilen en yeni `count` mali ceyrek kullanilir.

    Hatalar:
        CompanyNotFoundError: Ticker company_tickers.json'da yok VEYA SEC bu
            sirket icin companyfacts dondurmuyor.
        FinancialDataNotAvailableError: Sirket dogrulandi ama hicbir donem
            turetilemedi (net_income hic raporlanmamis -- cok nadir).
        SecEdgarNetworkError: Ag hatasi.
    """
    ticker = normalize_ticker(ticker)
    cik10 = resolve_cik(ticker)
    payload = _request_companyfacts(cik10)
    facts_by_tag = _extract_relevant_facts(payload)

    if periods is not None:
        target_periods = periods
    else:
        available = _discover_available_periods(facts_by_tag)
        if not available:
            raise FinancialDataNotAvailableError(
                f"'{ticker}' (CIK{cik10}) icin hicbir donemde net_income turetilemedi."
            )
        target_periods = available[:count]

    return RawUsFinancials(
        ticker=ticker,
        cik10=cik10,
        company_name=payload.get("entityName"),
        periods=target_periods,
        facts_by_tag=facts_by_tag,
    )


# --- Standart alan erisimi -----------------------------------------------------


def _require_known_field(field_name: str) -> list[str]:
    candidates = STANDARD_ITEM_MAP_US_GAAP.get(field_name)
    if candidates is None:
        raise UnsupportedTaxonomyError(f"Bilinmeyen standart alan adi: '{field_name}'")
    return candidates


def standardized_value_us_gaap(raw: RawUsFinancials, field_name: str, period: Period) -> Decimal | None:
    """Ic sema alan adina gore HAM (kumulatif olabilen) degeri doner --
    isyatirim.standardized_value() ile AYNI semantik. ADAY tag'ler ONCELIK
    sirasiyla denenir, ilk deger bulunan tag kullanilir (bkz. modul ust
    notu "Aynı kavram icin birden fazla tag" maddesi)."""
    candidates = _require_known_field(field_name)
    fy, fiscal_period = period
    is_stock = field_name in _STOCK_FIELDS_US_GAAP

    for tag in candidates:
        facts = raw.facts_by_tag.get(tag)
        if not facts:
            continue
        value = _instant_value(facts, fy, fiscal_period) if is_stock else _cumulative_value(facts, fy, fiscal_period)
        if value is not None:
            return value
    return None


def quarterly_standardized_value_us_gaap(raw: RawUsFinancials, field_name: str, period: Period) -> Decimal | None:
    """standardized_value_us_gaap()'in TEK CEYREKLIK karsiligi --
    CUMULATIVE_FIELDS_US_GAAP alanlari icin kumulatiften ceyreklik turetme
    uygular; STOK alanlar icin standardized_value_us_gaap ile AYNIDIR.

    CANLI HATA (kullanici raporu -- GOOGL kartinda "Satislar (Ç2 2025,
    karsilastirma)" satiri sessizce "veri yok" gosteriyordu, bkz.
    06_BILINEN_SORUNLAR.md): ONCEKI uygulama, mevcut VE onceki donemin
    kumulatif degerlerinin AYNI TEK tag'in fact listesinden gelmesini
    ZORUNLU kiliyordu (quarterly_value_from_cumulative_us_gaap tek bir
    `facts` listesi alir). GOOGL CANLI ornegi: 2025 Ç1 10-Q'su "RevenueFrom
    ContractWithCustomerExcludingAssessedTax" tag'ini kullanirken, 2025 Ç2
    10-Q'su (SEBEBI BILINMEYEN bir taksonomi/etiketleme degisikligiyle)
    "Revenues" tag'ine GECIYOR -- iki donem de AYRI AYRI standardized_value_us_gaap()
    ile (her biri KENDI donemi icin TUM aday tag'leri dener) basariyla
    bulunuyor, ama TEK bir tag'in ICINDE HER IKI donem de YOK, bu yuzden
    eski (tek-tag) cikarma HER IKI tag icin de basarisiz oluyordu.

    Cozum: cikarma, HER DONEM icin AYRI AYRI (TUM aday tag'ler denenerek,
    bkz. standardized_value_us_gaap) cozulen kumulatif degerler UZERINDEN
    yapilir -- boylece bir sirket iki komsu ceyrek arasinda tag DEGISTIRSE
    bile (ayni MUHASEBE kavramini temsil ettikleri surece, STANDARD_ITEM_MAP_US_GAAP'in
    aday listesi geregi) ceyreklik turetme ÇALIŞMAYA devam eder."""
    if field_name not in CUMULATIVE_FIELDS_US_GAAP:
        return standardized_value_us_gaap(raw, field_name, period)

    fy, fiscal_period = period
    current_cum = standardized_value_us_gaap(raw, field_name, period)
    if current_cum is None:
        return None
    if fiscal_period == 3:  # mali yilin ilk ceyregi -- kumulatif zaten ceyregin kendisi
        return current_cum

    previous_period = (fy, fiscal_period - 3)
    previous_cum = standardized_value_us_gaap(raw, field_name, previous_period)
    if previous_cum is None:
        return None
    return current_cum - previous_cum


def total_debt_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """Toplam finansal borc = kisa + uzun vadeli finansal borc -- isyatirim.total_debt()
    ile AYNI ilke (STOK deger, tek bir XBRL tag'i karsiligi yok)."""
    short_debt = standardized_value_us_gaap(raw, "short_term_financial_debt", period)
    long_debt = standardized_value_us_gaap(raw, "long_term_financial_debt", period)
    if short_debt is None and long_debt is None:
        return None
    return (short_debt or Decimal(0)) + (long_debt or Decimal(0))


def gross_profit_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """Brut Kar (KUMULATIF) -- isyatirim.total_revenue() ile AYNI desen
    (dogrudan tag ONCELIKLI, yoksa DOGRULANMIS bir turetme). Once
    "us-gaap:GrossProfit" tag'i (AAPL/NVDA/MSFT/TSLA/AMD -- CANLI dogrulandi)
    denenir; o donem icin YOKSA "Hasilat - Satislarin Maliyeti" turetilir
    (GOOGL/AMZN/META/NFLX -- bkz. STANDARD_ITEM_MAP_US_GAAP 'cost_of_revenue'
    ic alani ust notu, stockanalysis.com ile BIREBIR dogrulandi). PYPL gibi
    HICBIR maliyet tag'i olmayan sirketlerde None doner (Kural 8)."""
    direct = standardized_value_us_gaap(raw, "gross_profit", period)
    if direct is not None:
        return direct
    revenue = standardized_value_us_gaap(raw, "revenue", period)
    cost = standardized_value_us_gaap(raw, "cost_of_revenue", period)
    if revenue is None or cost is None:
        return None
    return revenue - cost


def quarterly_gross_profit_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """gross_profit_us_gaap()'in TEK CEYREKLIK karsiligi -- bkz. docstring'i."""
    direct = quarterly_standardized_value_us_gaap(raw, "gross_profit", period)
    if direct is not None:
        return direct
    revenue = quarterly_standardized_value_us_gaap(raw, "revenue", period)
    cost = quarterly_standardized_value_us_gaap(raw, "cost_of_revenue", period)
    if revenue is None or cost is None:
        return None
    return revenue - cost


# AMD/TSLA canli hatasi (kullanici raporu, 2026-08-03, bkz.
# PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B20): "iki bilesenden SADECE biri
# varsa None doner" kurali cok KATIYDI -- TSLA'nin 'AmortizationOfIntangibleAssets'
# etiketi 2021'den beri HIC raporlanmamis (CANLI doğrulandi, tam SEC tag
# taramasiyla: 9 fact'in TAMAMI 2021 ve ONCESI, hepsi YILLIK) -- yani bu
# bilesen sadece o CEYREK icin degil, YAPISAL olarak (yillardir) YOK. Boyle
# bir durumda bunu "eksik veri" (None donup FAVOK'u tamamen iptal etmek)
# yerine "sirket bu kalemi ayrica raporlamiyor, onemsiz/sifir" olarak
# yorumlamak DAHA DOGRU -- cogu veri saglayicisinin (macrotrends,
# stockanalysis.com) yaptigi da budur. Bu yuzden: bir bilesen SON
# `_STRUCTURAL_ABSENCE_LOOKBACK_YEARS` yil icinde HICBIR bicimde (ceyreklik
# NE DE yillik) raporlanmamissa, o bilesen 0 SAYILIR (uydurma DEGIL --
# gercekte YOK sayilan bir kalem). Bu, AMD'nin 'Depreciation' etiketini
# ETKILEMEZ (AMD bunu HER YIL duzenli raporluyor, sadece ceyreklik KIRILIMI
# yok) -- o durumda hala None donulur (Depreciation gercek ve kucumsenemeyecek
# kadar buyuk, atlanamaz).
_STRUCTURAL_ABSENCE_LOOKBACK_YEARS = 3


def _component_tag_reported_recently(raw: RawUsFinancials, field_name: str, as_of_fy: int) -> bool:
    """`field_name` (orn. 'amortization_component') icin ADAY tag'lerden
    HERHANGI BIRI, son `_STRUCTURAL_ABSENCE_LOOKBACK_YEARS` mali yil
    icinde (ceyreklik VEYA yillik, HERHANGI bir sure ile) EN AZ bir fact
    icin raporlanmis mi? Yoksa bu kalem YAPISAL olarak terk edilmis/hic
    kullanilmamis sayilir (bkz. yukaridaki modul notu)."""
    candidates = STANDARD_ITEM_MAP_US_GAAP.get(field_name, [])
    cutoff_fy = as_of_fy - _STRUCTURAL_ABSENCE_LOOKBACK_YEARS
    for tag in candidates:
        for fact in raw.facts_by_tag.get(tag, []):
            if fact.fy is not None and fact.fy >= cutoff_fy:
                return True
    return False


def _latest_annual_fact_value(raw: RawUsFinancials, field_name: str, at_or_before: date) -> Decimal | None:
    """`field_name` icin ADAY tag'ler arasinda, `at_or_before` tarihine
    KADAR (dahil) biten EN YENI YILLIK (fp='FY', ~340-380 gun) fact'in
    degerini doner -- ceyreklik kirilimi HIC olmayan ama duzenli YILLIK
    raporlanan bir kalemin (orn. AMD'nin 'Depreciation'i) TTM hesaplarinda
    'en iyi bilinen gercek deger' olarak kullanilmasi icin (bkz.
    trailing_12m_depreciation_amortization_us_gaap())."""
    candidates = STANDARD_ITEM_MAP_US_GAAP.get(field_name, [])
    best: ConceptFact | None = None
    for tag in candidates:
        for fact in raw.facts_by_tag.get(tag, []):
            if fact.fp != "FY" or fact.start is None:
                continue
            duration_days = (fact.end - fact.start).days
            if not (340 <= duration_days <= 380):
                continue
            if fact.end > at_or_before:
                continue
            if best is None or fact.end > best.end:
                best = fact
    return best.val if best is not None else None


def depreciation_amortization_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """D&A (KUMULATIF) -- gross_profit_us_gaap() ile AYNI desen (dogrudan
    birlesik tag ONCELIKLI, yoksa DOGRULANMIS bir toplama). Once
    "DepreciationDepletionAndAmortization"/"DepreciationAmortizationAndAccretionNet"
    (AAPL/NVDA/JPM) denenir; o donem icin YOKSA "Depreciation" (maddi duran
    varlik) + "AmortizationOfIntangibleAssets" (maddi olmayan duran varlik)
    TOPLANARAK turetilir (MSFT -- CANLI dogrulandi, bkz. STANDARD_ITEM_MAP_US_GAAP
    'depreciation_component'/'amortization_component' ic alanlari ust notu).
    Iki bilesenden biri eksikse: o bilesen YAPISAL olarak (son 3 yildir) HIC
    raporlanmamissa 0 SAYILIR (bkz. yukaridaki §B20 notu -- TSLA'nin
    amortisman kalemi gibi); YAKIN GECMISTE raporlanmis ama SADECE bu donem
    icin eksikse None doner (Kural 8: yanlis rakamdan iyidir)."""
    direct = standardized_value_us_gaap(raw, "depreciation_amortization", period)
    if direct is not None:
        return direct
    depreciation = standardized_value_us_gaap(raw, "depreciation_component", period)
    amortization = standardized_value_us_gaap(raw, "amortization_component", period)
    if depreciation is not None and amortization is not None:
        return depreciation + amortization
    fiscal_year = period[0]
    if depreciation is not None and not _component_tag_reported_recently(raw, "amortization_component", fiscal_year):
        return depreciation
    if amortization is not None and not _component_tag_reported_recently(raw, "depreciation_component", fiscal_year):
        return amortization
    return None


def quarterly_depreciation_amortization_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """depreciation_amortization_us_gaap()'in TEK CEYREKLIK karsiligi -- bkz. docstring'i."""
    direct = quarterly_standardized_value_us_gaap(raw, "depreciation_amortization", period)
    if direct is not None:
        return direct
    depreciation = quarterly_standardized_value_us_gaap(raw, "depreciation_component", period)
    amortization = quarterly_standardized_value_us_gaap(raw, "amortization_component", period)
    if depreciation is not None and amortization is not None:
        return depreciation + amortization
    fiscal_year = period[0]
    if depreciation is not None and not _component_tag_reported_recently(raw, "amortization_component", fiscal_year):
        return depreciation
    if amortization is not None and not _component_tag_reported_recently(raw, "depreciation_component", fiscal_year):
        return amortization
    return None


def _quarterly_component_sum_trailing_4(raw: RawUsFinancials, field_name: str, period: Period) -> Decimal | None:
    """`field_name` icin son 4 mali CEYREGIN (bu donem dahil) TEK CEYREKLIK
    degerlerini toplar -- TUM 4 ceyrek de cozulmezse None doner (kismi/
    parcali bir TTM uydurulmaz)."""
    total = Decimal(0)
    current = period
    for _ in range(4):
        value = quarterly_standardized_value_us_gaap(raw, field_name, current)
        if value is None:
            return None
        total += value
        current = previous_quarter_period(current)
    return total


def trailing_12m_depreciation_amortization_us_gaap(raw: RawUsFinancials, period: Period) -> Decimal | None:
    """D&A'nin TTM (son 12 ay) karsiligi -- FAVOK'un TEK CEYREKLIK turetmesi
    basarisiz oldugunda (AMD gibi, bkz. §B20) TTM FAVOK'u YINE DE
    hesaplayabilmek icin. Her bilesen (depreciation/amortization) icin AYRI
    bir strateji dener:
      1. Son 4 ceyregin TEK CEYREKLIK degerleri TOPLANABILIYORSA (cogu
         sirket) -- bu KULLANILIR, en dogru sonuc budur.
      2. Bilesen YAPISAL olarak (son 3 yildir) HIC raporlanmamissa -- 0
         SAYILIR (bkz. §B20 notu, TSLA'nin amortismani gibi).
      3. Bilesen SADECE YILLIK raporlaniyorsa (ceyreklik kirilimi HIC yok,
         AMD'nin Depreciation'i gibi) -- EN SON bilinen YILLIK (FY) deger
         DOGRUDAN kullanilir (bir onceki tam mali yilin GERCEK, aciklanmis
         rakami -- 4'e BOLUNEREK tahmin YAPILMAZ, ceyreklik bir uydurma
         DEGIL, sadece "son bilinen 12 aylik gercek deger" olarak kullanilir).
      4. Hicbiri gecerli degilse (kismi/duzensiz veri) -- None doner.
    Iki bilesenin TTM'i TOPLANARAK D&A TTM elde edilir; ikisi de
    cozulemezse None doner."""
    direct = _quarterly_component_sum_trailing_4(raw, "depreciation_amortization", period)
    if direct is not None:
        return direct

    fiscal_year = period[0]
    end_date = _period_end_date(raw, period)

    def _real_component_ttm(field_name: str) -> Decimal | None:
        """SADECE GERCEK (ceyreklik toplam VEYA yillik yedek) bir deger
        arar -- yapisal-yoksayma (0 varsayimi) BURADA YAPILMAZ, cunku bu
        fonksiyon iki bilesenin de gercekten cozulup cozulmedigini onceden
        bilmeden 0 varsaymak, IKISI DE cozulemedigi durumda (orn. hicbir
        bilesen tag'i hic yoksa) 'D&A TTM'si tam olarak 0' gibi YANLIS bir
        izlenim uretirdi (bkz. asagidaki birlestirme mantigi -- 0 varsayimi
        SADECE DIGER bilesen GERCEKTEN cozulduyse uygulanir)."""
        quarterly_sum = _quarterly_component_sum_trailing_4(raw, field_name, period)
        if quarterly_sum is not None:
            return quarterly_sum
        if end_date is not None:
            annual_value = _latest_annual_fact_value(raw, field_name, end_date)
            if annual_value is not None:
                return annual_value
        return None

    depreciation_real = _real_component_ttm("depreciation_component")
    amortization_real = _real_component_ttm("amortization_component")

    if depreciation_real is not None and amortization_real is not None:
        return depreciation_real + amortization_real
    # Bir bilesen GERCEKTEN cozuldu, DIGERI YAPISAL olarak (son 3 yildir)
    # HIC raporlanmamissa -- o bilesen 0 SAYILIR (bkz. §B20 notu, TSLA'nin
    # amortismani gibi). Her iki bilesen de cozulemezse (asagida ikisi de
    # None kalir) None doner -- "ikisi de 0" gibi YANLIS bir TTM uydurulmaz.
    if depreciation_real is not None and not _component_tag_reported_recently(raw, "amortization_component", fiscal_year):
        return depreciation_real
    if amortization_real is not None and not _component_tag_reported_recently(raw, "depreciation_component", fiscal_year):
        return amortization_real
    return None


# --- Fiyat -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_price_chart(ticker: str) -> dict:
    url = PRICE_ENDPOINT.format(ticker=ticker)
    try:
        response = httpx.get(
            url, params={"range": "5d", "interval": "1d"}, headers=_PRICE_HEADERS, timeout=config.HTTP_TIMEOUT_SECONDS
        )
    except httpx.RequestError as exc:
        logger.warning("Fiyat istegi basarisiz, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise SecEdgarNetworkError(f"Fiyat uc noktasi beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise SecEdgarNetworkError("Fiyat yaniti JSON olarak ayristirilamadi.") from exc


def fetch_latest_price(ticker: str) -> Decimal | None:
    """Son islem gunu kapanisa yakin/guncel fiyati doner (Decimal | None).
    Bu YARDIMCI/IKINCIL bir veridir (Kural 9) -- herhangi bir hata SESSIZCE
    None ile sonuclanir, cagiran taraf (pipeline.py) bunu ASLA bloke
    etmemelidir.

    Hatalar: FIRLATMAZ -- ag/parse hatalari yakalanip loglanir, None doner.
    """
    ticker = normalize_ticker(ticker)
    try:
        payload = _request_price_chart(ticker)
    except (SecEdgarNetworkError, httpx.RequestError) as exc:
        logger.warning("%s icin fiyat cekilemedi: %s", ticker, exc)
        return None

    try:
        meta = payload["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("%s icin fiyat yaniti beklenmeyen bicimde: %s", ticker, exc)
        return None

    return _parse_decimal(price)


@retry(
    reraise=True,
    stop=stop_after_attempt(config.HTTP_MAX_RETRIES),
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(httpx.RequestError),
)
def _request_price_chart_history(ticker: str, range_label: str) -> dict:
    url = PRICE_ENDPOINT.format(ticker=ticker)
    try:
        response = httpx.get(
            url,
            params={"range": range_label, "interval": "1d"},
            headers=_PRICE_HEADERS,
            timeout=config.HTTP_TIMEOUT_SECONDS,
        )
    except httpx.RequestError as exc:
        logger.warning("Fiyat gecmisi istegi basarisiz, yeniden denenecek: %s", exc)
        raise
    if response.status_code != 200:
        raise SecEdgarNetworkError(f"Fiyat gecmisi uc noktasi beklenmeyen HTTP durum kodu dondurdu: {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise SecEdgarNetworkError("Fiyat gecmisi yaniti JSON olarak ayristirilamadi.") from exc


def fetch_price_history(ticker: str, days: int = 400) -> list[dict]:
    """Son `days` gunun GUNLUK OHLCV serisini doner (Faz 15 - teknik analiz).

    Kesif (scripts/explore_price_history.py AAPL --market NASDAQ --days 400,
    2026-08-03) CANLI olarak dogruladi: ayni Yahoo chart uc noktasi
    (fetch_latest_price'in kullandigi PRICE_ENDPOINT) 'range' parametresi
    genisletilince TAM bir gunluk OHLCV serisi donuyor --
    result.indicators.quote[0] icinde 'open'/'high'/'low'/'close'/'volume'
    dizileri, result.timestamp icinde UNIX epoch (saniye) tarihleri VAR.
    Bu, Is Yatirim'in aksine 'acilis' fiyatini da icerir.
    'range' Yahoo'da GUN SAYISI degil ONCEDEN TANIMLI etiketler alir
    (1y/2y/...); istenen `days` kadar tampon icin en yakin BUYUK etiket
    secilir (>365 gun icin '2y', aksi halde '1y').

    Doner: [{"date": date, "open": Decimal|None, "high": Decimal|None,
             "low": Decimal|None, "close": Decimal|None, "volume": Decimal|None}, ...]
    artan tarih sirasinda. Bir bar'in HERHANGI bir OHLC alani None ise
    (Yahoo bazi kismi/tatil gunlerinde null doner, canli gozlemlendi)
    o bar TAMAMEN atlanir -- eksik bir mumu yariya tamamlamak Kural 3'e
    aykiri bir uydurma olurdu.
    Sirket icin veri yoksa BOS liste doner -- bu supplementary bir veridir,
    cagiran taraf (price_history.py) ASLA bunun icin pipeline'i BLOKE ETMEMELIDIR.

    Hatalar: FIRLATMAZ -- ag/parse hatalari yakalanip loglanir, bos liste doner.
    """
    ticker = normalize_ticker(ticker)
    range_label = "2y" if days > 365 else "1y"
    try:
        payload = _request_price_chart_history(ticker, range_label)
    except (SecEdgarNetworkError, httpx.RequestError) as exc:
        logger.warning("%s icin fiyat gecmisi cekilemedi: %s", ticker, exc)
        return []

    try:
        result = payload["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("%s icin fiyat gecmisi yaniti beklenmeyen bicimde: %s", ticker, exc)
        return []

    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    bars: list[dict] = []
    for idx, ts in enumerate(timestamps):
        high = _parse_decimal(highs[idx]) if idx < len(highs) else None
        low = _parse_decimal(lows[idx]) if idx < len(lows) else None
        close = _parse_decimal(closes[idx]) if idx < len(closes) else None
        if high is None or low is None or close is None:
            continue
        open_ = _parse_decimal(opens[idx]) if idx < len(opens) else None
        volume = _parse_decimal(volumes[idx]) if idx < len(volumes) else None
        bars.append(
            {
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).date(),
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume if volume is not None else Decimal(0),
            }
        )
    return bars
