"""AnalysisResult + ScoreResult + Commentary'yi Jinja2 ile HTML'e, Playwright
(chromium headless) ile PNG karta cevirir. Bu, kullanicinin gorecegi TEK
ciktidir.

Bu modul kesinlikle sayi HESAPLAMAZ; sadece calculator/scorer/commentary
tarafindan zaten hesaplanmis/formatlanmis degerleri gorsel bir duzene
yerlestirir. Butun Turkce sayi/para birimi formatlamasi (yuzde isareti,
virgullu ondalik, milyar/milyon kisaltma) src.formatting'teki TEK ortak
yardimcilarla yapilir; sablon (card.html) HICBIR bicimlendirme mantigi
icermez, sadece onceden hazirlanmis string'leri yerlestirir.

Iki asama:
    1. build_card_context(...) -- domain nesnelerini (AnalysisResult,
       ScoreResult, Commentary, disclosures) duz bir dict'e cevirir. Bu
       dict'in tam semasi asagida belgelenmistir.
    2. render_card(context, out_path) -- context'i Jinja2 ile HTML'e
       render eder (debug icin data/last_card.html'e de yazar), Playwright
       chromium ile acar, #card elementinin ekran goruntusunu
       device_scale_factor=2 (retina) ile PNG olarak kaydeder.

context semasi (build_card_context'in urettigi, render_card'in bekledigi):
    ticker, company_name, sector, period_label, report_timestamp,
    price_display (str|None), valuation (dict|None: piyasa_degeri, sermaye,
        fk, pd_dd, fd_favok, fd_hasilat, pd_efk -- fiyat/sermaye ikisi de
        yoksa None, bkz. calculator.compute_valuation; Net Borç burada YOK,
        SADECE balance_rows icinde gosterilir),
    valuation_analysis (dict: has_data + verdict/graham_verdict/peg_verdict/
        hedef fiyatlar -- bkz. src.render.valuation_view.build_valuation_view,
        BİLANÇO SKORU bölümündeki kompakt Değerleme Analizi kutusu icin,
        yukaridaki `valuation` ile KARISTIRILMASIN -- o ust banttaki F/K/
        PD-DD seridi icin AYRI bir semadir),
    headline, summary, show_ebitda (bool),
    income_rows (dict: revenue/gross_profit/operating_profit/ebitda/net_income
        -> {label,current,comparison,change_display,color_class} | None),
    balance_rows (dict: current_assets/non_current_assets/total_assets/net_debt/equity
        -> ayni sekil -- Net Borç SADECE burada gosterilir, valuation kutularinda
        TEKRAR gosterilmez, bkz. _valuation_context),
    charts (dict: revenue/ebitda/net_income -> {title, points:[{label,display,
        pos_pct,neg_pct}]} | None),
    positives (list[str]), negatives (list[str]),
    score_total_display, score_badge, score_badge_class,
    score_rows (list[{name,weight,score,contribution,reasoning}]),
    kap_note (str|None), disclosure_rows (list[{date,title}]),
    commentary_source, data_sources_note, disclaimer.

Font secimi: harici Google Fonts CAGRISI YAPILMAZ (Playwright'in cevrimdisi
de guvenilir render etmesi icin) -- sistem monospace yigininin ("Cascadia
Code", "Consolas" gibi kaliteli terminal fontlari coğu Windows/Mac/Linux
kurulumunda hazir bulunur) fallback zinciri kullanilir.
"""

from __future__ import annotations

import base64
import logging
import math
import threading
from datetime import datetime
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

import jinja2

import config
from src.ai import commentary as commentary_module
from src.analysis import calculator, scorer
from src.analysis.valuation import ValuationAssessment
from src.fetchers import company_logo, kap
from src.formatting import format_currency_short, format_number_tr, format_percent_tr
from src.render import valuation_view

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_LOGO_PATH = _ASSETS_DIR / "quaxis_logo_badge.png"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
    autoescape=jinja2.select_autoescape(["html"]),
)

# QuaxisLabs marka rozeti (masthead + tum kart genelindeki dusuk-opasiteli
# filigran) -- kart hangi build_*_card_context() cagrisiyla uretilirse
# uretilsin (sanayi/banka/sigorta) AYNI rozeti gostersin diye context'e her
# seferinde ayri ayri eklenmek yerine Jinja global'i olarak KAYIT EDILIR;
# boylece card.html tum PNG'lerde (Twitter/X'te paylasilan TEK cikti) marka
# kaynagi belli olur ve baskasi kirpip kendi hesabindan paylasirsa bile
# filigran kirpilmadigi surece kaynagi gosterir. Dosya kucuk (~130KB) oldugu
# icin modul yuklenirken BIR KEZ base64'e cevrilip bellekte tutulur.
_env.globals["logo_data_uri"] = "data:image/png;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")

# Chromium'u HER render_card() cagrisinda yeniden baslatip kapatmak (~1-2sn
# baslangic maliyeti) yerine, is parcacigi basina BIR kez baslatilip
# saklanir (Playwright'in sync API'si is parcaciklari arasi PAYLASILAMAZ --
# resmi kisitlama; bu yuzden process-genelinde TEK bir singleton yerine
# threading.local() kullanilir). asyncio.to_thread() varsayilan havuzu ayni
# is parcaciklarini istekler arasi yeniden kullandigi icin bu, ardisik
# isteklerde gercek bir hiz kazanci saglar.
_thread_local = threading.local()


def _get_browser():
    browser = getattr(_thread_local, "browser", None)
    if browser is not None and browser.is_connected():
        return browser

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise CardRenderError(
            "playwright paketi kurulu değil. `pip install playwright` ve `playwright install chromium` çalıştırın."
        ) from exc

    playwright_ctx = sync_playwright().start()
    browser = playwright_ctx.chromium.launch()
    _thread_local.playwright_ctx = playwright_ctx
    _thread_local.browser = browser
    return browser


class CardRenderError(Exception):
    """Kart HTML->PNG donusumu basarisiz oldu (orn. Playwright chromium
    kurulu degil -- `playwright install chromium` calistirilmali)."""


# --- Renk/rozet esleme (LLM'siz, saf esleme -- sayi uretmez) -----------------------------------------------------

_LABEL_COLOR_CLASS: dict[str, str] = {
    calculator.ChangeLabel.GUCLU_ARTIS: "positive",
    calculator.ChangeLabel.ARTIS: "positive",
    calculator.ChangeLabel.YATAY: "neutral",
    calculator.ChangeLabel.AZALIS: "negative",
    calculator.ChangeLabel.SERT_DUSUS: "negative",
    calculator.ChangeLabel.ZARARDAN_KARA_GECTI: "positive",
    calculator.ChangeLabel.KARA_KARSIN_ZARAR: "negative",
    calculator.ChangeLabel.VERI_YOK: "neutral",
    # net_debt'e ozel (bkz. calculator.classify_debt_change): net nakitten
    # net borca gecmek KOTULESME (kirmizi), net borctan net nakde gecmek
    # IYILESME (yesil) -- kar/zarar etiketleriyle TERS renklenir.
    calculator.ChangeLabel.NET_BORCA_GECTI: "negative",
    calculator.ChangeLabel.NET_NAKDE_GECTI: "positive",
}

_BADGE_CLASS: dict[str, str] = {
    "SAĞLAM": "saglam",
    "DENGELİ": "dengeli",
    "KARIŞIK": "karisik",
    "RİSKLİ": "riskli",
    scorer.YETERSIZ_VERI_ROZETI: "yetersiz",
}

_MIN_BAR_PCT = 6  # cok kucuk degerler de gorsel olarak fark edilsin diye taban bar yuksekligi


def _quarter_label(period: tuple[int, int]) -> str:
    year, quarter = period
    return f"{quarter // 3}Ç{year % 100:02d}"


def _fiscal_quarter_label(period: tuple[int, int], annual_only: bool = False) -> str:
    """_quarter_label()'in NASDAQ/ABD (US_GAAP) karsiligi. `period[0]`
    US_GAAP icin TAKVIM yili DEGIL, sirketin KENDI mali yilidir (SEC 'fy'
    alani, bkz. src/fetchers/sec_edgar.py modul notu) -- NVDA gibi mali
    yili takvim yiliyla ORTUSMEYEN sirketlerde "_quarter_label" biciminde
    (orn. "1Ç27") gosterilirse TAKVIM 1. ceyregiymis gibi YANLIS izlenim
    verir (Kural 8: "uydurma" olur). Bu yuzden ayri, ACIKCA "mali yil"
    oldugunu belirten bir bicim kullanilir: "FYyy Çn" (orn. "FY27 Ç1").

    `annual_only=True` (bkz. calculator.AnalysisResult.is_annual_only, B21 --
    NVO/TSM/SHEL/BABA gibi SADECE yillik veri raporlayan ADR/20-F sirketleri):
    "Çn" eki DUSURULUR ("FY25" -- Kural 8, "Ç4" YOKTUR ki bu sirketlerde,
    gosterilen rakam ZATEN tam yilin kendisidir, izole bir ceyrek DEGIL)."""
    year, quarter = period
    if annual_only:
        return f"FY{year % 100:02d}"
    return f"FY{year % 100:02d} Ç{quarter // 3}"


def _money_or_dash(value: Decimal | None, currency_symbol: str = "₺") -> str:
    return format_currency_short(value, symbol=currency_symbol) if value is not None else "—"


def _ratio_or_dash(value: Decimal | None, decimals: int = 2, suffix: str = "") -> str:
    return f"{format_number_tr(value, decimals=decimals)}{suffix}" if value is not None else "—"


# Degerleme kutulari (Piyasa Degeri, F/K, PD/DD, FD/FAVOK, vb.) icin AYRI
# fallback: kullanici geri bildirimi -- Fintables gibi referans platformlar
# bu carpanlar SIRKET ICIN ANLAMLI/HESAPLANABILIR DEGILSE (ör. zarar eden
# sirkette F/K) "N/A" yazar, "—" DEGIL. _money_or_dash/_ratio_or_dash ise
# gelir/bilanco tablosu satirlarinda (_line_item_row) FARKLI bir anlamla
# ("bu donem icin veri cekilememis") paylasilmaya devam ediyor -- o yuzden
# BURADA ayri fonksiyonlar tanimlanir, mevcut ikisi DEGISTIRILMEZ.
def _money_or_na(value: Decimal | None, currency_symbol: str = "₺") -> str:
    return format_currency_short(value, symbol=currency_symbol) if value is not None else "N/A"


def _ratio_or_na(value: Decimal | None, decimals: int = 2, suffix: str = "") -> str:
    return f"{format_number_tr(value, decimals=decimals)}{suffix}" if value is not None else "N/A"


def _item_color_class(item: calculator.LineItemChange, *, lower_is_better: bool = False) -> str:
    """`_line_item_row()`'dan (Faz 14'te `build_teaser_context()` ile de
    PAYLAŞILSIN diye) çıkarılan renk mantığı -- kopyala-yapıştır yerine
    ortak yardımcı (proje ilkesi, bkz. 01_MIMARI.md).

    Renk, öncelikle YÜZDENİN KENDİ İŞARETİNE göre belirlenir (kullanıcı
    geri bildirimi: "pozitifler yeşil, negatifler kırmızı olmalı" -- eski
    mantık YATAY (|değişim|<%5) etiketini HER ZAMAN nötr/gri boyuyordu).
    percent_change None ise (geçiş etiketleri: zarardan kâra geçti/kârdan
    zarara geçti, ya da veri yok) etikete göre renklendirilir (bkz.
    `_LABEL_COLOR_CLASS`).

    CANLI hata (kullanıcı raporu, Fintables karşılaştırması): Net Borç
    için AZALIŞ İYİ (daha az borç/daha fazla net nakit) haberdir --
    `lower_is_better=True` (SADECE net_debt satırı için) işareti TERSİNE
    çevirir."""
    if item.percent_change is not None:
        sign = -item.percent_change if lower_is_better else item.percent_change
        if sign > 0:
            return "positive"
        if sign < 0:
            return "negative"
        return "neutral"
    return _LABEL_COLOR_CLASS.get(item.change_label, "neutral")


def _line_item_row(
    item: calculator.LineItemChange | None,
    *,
    lower_is_better: bool = False,
    currency_symbol: str = "₺",
    field_label: str = "",
) -> dict:
    # FAVOK banka/sigortada VEYA eksik amortisman verisinde item'in KENDISI
    # None doner (diger kalemler -- revenue/gross_profit/vb. -- her zaman
    # bir LineItemChange nesnesidir, SADECE ICINDEKI current/comparison None
    # olabilir) -- bkz. calculator.IncomeStatementSummary.ebitda docstring'i.
    # Satir HER ZAMAN gorunsun istegi (§B17) icin diger "veri yok" satirlarla
    # (orn. gross_profit) AYNI gorunumde bir satir uretilir.
    if item is None:
        return {
            "label": field_label,
            "current": "—",
            "value_class": "",
            "comparison": "—",
            "change_display": "veri yok",
            "color_class": "neutral",
        }
    # Gecis etiketlerinde (zarardan kara gecti / kara karsin zarar / net
    # nakit<->net borc) BILEREK yuzde GOSTERILMEZ: (guncel-onceki)/|onceki|
    # formulu guncel deger onceki DEGERE GORE cok kucuk kaldiginda (orn.
    # TERA canli hatasi: -4,7 mr'dan 15,5 mn'ye) buyuklukten BAGIMSIZ olarak
    # neredeyse HER ZAMAN ~%100 uretir -- bilgi degeri yoktur, hatta yanlis
    # bir "yaklasik %100 degisim" izlenimi verir. Etiketin kendisi zaten
    # yon/anlami tam olarak tasir, ek yuzdeye gerek yoktur.
    if item.percent_change is not None:
        change_display = format_percent_tr(item.percent_change)
    else:
        change_display = item.change_label
    color_class = _item_color_class(item, lower_is_better=lower_is_better)
    # CANLI hata (kullanici raporu): guncel donem degeri (gelir tablosu VE
    # bilanco) HER ZAMAN duz/beyaz gosterilmeli, eski donem (comparison) HER
    # ZAMAN gri ("secondary", bkz. card.html) -- rengi tasiyan tek sutun
    # DEGISIM'dir. Eskiden guncel deger NEGATIFSE (orn. Net Borc net nakit
    # pozisyonundayken) otomatik kirmiziya boyaniyordu; bu Net Borc icin
    # YANLIS izlenim veriyordu (negatif net borc IYI bir seydir, alarm rengi
    # DEGIL) VE genel kurala (guncel=beyaz) aykiriydi.
    value_class = ""
    return {
        "label": item.label_tr,
        "current": _money_or_dash(item.current, currency_symbol),
        "value_class": value_class,
        "comparison": _money_or_dash(item.comparison, currency_symbol),
        "change_display": change_display,
        "color_class": color_class,
    }


def _ebitda_row_with_ttm_fallback(analysis: calculator.AnalysisResult, currency_symbol: str = "₺") -> dict:
    """FAVÖK satırı için `_line_item_row(analysis.income_statement.ebitda)`
    ile AYNI şekli üretir, ama TEK ÇEYREKLİK FAVÖK None ISE (AMD/TSLA gibi
    D&A'nın bir bileşeni hiç çeyreklik kırılımı olmadığı için -- bkz.
    PROJE_HAFIZASI/06_BILINEN_SORUNLAR.md §B20) VE `analysis.ratios.ttm_ebitda`
    HESAPLANABILDIYSE (bkz. calculator._build_analysis_result'taki
    `ttm_depreciation_amortization_override` yedeği) tamamen "veri yok"
    göstermek yerine "FAVÖK (TTM)" etiketiyle son 12 aylık değeri gösterir.
    Bu bir TEK ÇEYREKLİK rakamla KARIŞTIRILMASIN diye hem etiket hem
    "değişim" sütunu AÇIKÇA "TTM" der; YoY karşılaştırma YAPILMAZ (comparison
    "—")."""
    if analysis.income_statement.ebitda is not None:
        return _line_item_row(
            analysis.income_statement.ebitda, currency_symbol=currency_symbol, field_label=calculator.FIELD_LABELS_TR["ebitda"]
        )
    if analysis.ratios.ttm_ebitda is not None:
        return {
            "label": f"{calculator.FIELD_LABELS_TR['ebitda']} (TTM)",
            "current": _money_or_dash(analysis.ratios.ttm_ebitda, currency_symbol),
            "value_class": "",
            "comparison": _money_or_dash(None, currency_symbol),
            "change_display": "son 12 ay",
            "color_class": "neutral",
        }
    return _line_item_row(None, currency_symbol=currency_symbol, field_label=calculator.FIELD_LABELS_TR["ebitda"])


def _company_logo_data_uri(ticker: str, market: str = "BIST") -> str | None:
    """company_logo fetcher'i zaten kendi hatalarini sessizce yutup None
    doner (bkz. modul docstring'i) -- bu sarmalayici sadece BEKLENMEYEN
    (kutuphane ici) istisnalarin kart uretimini KIRMAMASINI garanti eder."""
    try:
        return company_logo.fetch_logo_data_uri(ticker, market=market)
    except Exception:
        logger.warning("%s icin sirket logosu eklenemedi", ticker, exc_info=True)
        return None


def _score_band_class(score: Decimal | None) -> str:
    """Bilesen puanini (0-10) hizli taranabilir bir renge esler -- kullanici
    geri bildirimi: skor bolumu okunmasi zor, her madde tek tek net ayirt
    edilmeli. Sadece GORSEL bir ipucu; puanin kendisi scorer.py'de zaten
    hesaplanmis, burada HICBIR esik/agirlik mantigi TEKRAR uygulanmaz."""
    if score is None:
        return "score-na"
    if score >= 7:
        return "score-good"
    if score >= 4:
        return "score-mid"
    return "score-poor"


def _score_row(c: scorer.ComponentScore) -> dict:
    return {
        "name": c.name,
        "weight": f"%{format_number_tr(c.weight_nominal, decimals=0)}",
        "score": f"{format_number_tr(c.score, decimals=1)}/10" if c.score is not None else "N/A",
        "score_band_class": _score_band_class(c.score),
        "contribution": format_number_tr(c.contribution, decimals=2) if c.score is not None else "N/A",
        "reasoning": c.reasoning_tr,
    }


def _score_display_context(score: scorer.ScoreResult) -> dict:
    """Kart baslik skorunun (BILANÇO SKORU buyuk rakami) context'ini uretir.

    CANLI HATA (kullanici raporu, ASTS, §B17 -- 06_BILINEN_SORUNLAR.md):
    bilesenlerin buyuk cogunlugu "veri yok" iken bile sayisal bir skor
    ("10,00/10 SAĞLAM") gosteriliyordu -- YANILTICI. scorer.ScoreResult.
    data_sufficient=False oldugunda (bkz. scorer.CONFIG["min_veri_agirlik_
    yuzdesi"]) sayisal skor/10 HIC gosterilmez, SADECE "YETERSİZ VERİ"
    rozeti gosterilir (Kural 3: yanlis/yanıltıcı rakamdan iyidir)."""
    return {
        "score_data_sufficient": score.data_sufficient,
        "score_total_display": format_number_tr(score.total_score, decimals=2),
        "score_badge": score.badge,
        "score_badge_class": _BADGE_CLASS.get(score.badge, "karisik"),
    }


_TARGET_TICK_COUNT = 4  # eksende hedeflenen aralik sayisi (guzel yuvarlama sonrasi gercek sayi degisebilir)


def _axis_tick_label(value: Decimal) -> str:
    """Eksen cizgisi etiketi: buyuk tutarlarda mr/mn kisaltmasi kullanir ama
    (referans gorsellerdeki gibi) para birimi sembolu EKLEMEZ (bu yuzden
    currency_symbol parametresi YOK -- deger her iki para biriminde de
    sembolsuz gosterilir); sifir icin daima '0,0' doner."""
    if value == 0:
        return "0,0"
    return format_currency_short(value, symbol="").strip()


def _nice_axis_step(max_abs: Decimal, target_ticks: int = _TARGET_TICK_COUNT) -> tuple[Decimal, int]:
    """Eksen icin 'guzel' (1/2/5/10 katlari) bir aralik ve gereken tik sayisini
    hesaplar -- Fintables referans kartlarindaki gibi (bkz. references/
    klasoru) 25/20/15/10/5/0 turu YUVARLAK sayilar uretir, ham en buyuk
    mutlak degerin (max_abs) HAM KESIRLERINI degil (eski yontem, kullanici
    geri bildirimi: "grafikler profesyonel gorunmuyor" -- 82,1mn/61,6mn/
    41,1mn gibi rastgele kesirli eksen etiketleri buna sebep oluyordu).

    Standart 'nice numbers' algoritmasi: hedef aralik sayisina gore kaba bir
    adim hesaplanir, bu adim en yakin 1/2/5/10'un katina yuvarlanir. Tik
    sayisi bu YUVARLAK adima gore max_abs'i kapsayacak kadar (yukari
    yuvarlanarak) belirlenir -- bu yuzden SABIT DEGIL, veriye gore 2-5 arasi
    degisebilir (Fintables'in kendi referans kartlarinda da tik sayisi
    sabit degil, bkz. ANSGR ornegi 6 satir, TAVHL ornegi 5 satir)."""
    if not max_abs or max_abs <= 0:
        return Decimal(0), 0
    rough_step = float(max_abs) / target_ticks
    magnitude = Decimal(10) ** math.floor(math.log10(rough_step))
    normalized = rough_step / float(magnitude)
    if normalized <= 1:
        nice_multiplier = Decimal(1)
    elif normalized <= 2:
        nice_multiplier = Decimal(2)
    elif normalized <= 5:
        nice_multiplier = Decimal(5)
    else:
        nice_multiplier = Decimal(10)
    step = nice_multiplier * magnitude
    tick_count = int((max_abs / step).to_integral_value(rounding=ROUND_CEILING))
    return step, max(tick_count, 1)


_AXIS_UPPER_PX = 72.0  # .chart-upper yuksekligiyle (CSS) BIREBIR eslesmeli
_AXIS_LOWER_PX = 72.0  # .chart-lower yuksekligiyle (CSS, sadece has_negative iken aktif) BIREBIR eslesmeli
_AXIS_ZERO_PX = 1.0  # .chart-zero yuksekligiyle (CSS) BIREBIR eslesmeli


def _build_chart(title: str, values: list[Decimal | None], period_labels: list[str], currency_symbol: str = "₺") -> dict:
    """Saf CSS mini bar grafik icin veri hazirlar: her nokta icin sifir
    cizgisinin ustunde (pos_pct) ya da altinda (neg_pct) yuzde-yukseklik
    uretir -- ARTIK o serideki HAM en buyuk mutlak degere (max_abs) degil,
    _nice_axis_step()'in urettigi YUVARLAK eksen tavanina (axis_max >=
    max_abs) gore olceklenir; boylece bar yukseklikleri ile sol eksendeki
    yuvarlak sayilar ayni referansi kullanir (axis_max'a ulasan bar %100
    degil, kendi payina dusen orani gosterir -- bkz. asagidaki y_axis_ticks).

    Kullanici geri bildirimi: bar yukseklikleri eksendeki sayilarla TAM
    hizali degildi. Kok neden IKI KATMANLIYDI:
      1. Eksen etiketleri flexbox `justify-content:space-between` ile
         dizilmisti -- bu, metin kutularinin kendi satir yuksekligini
         (line-height) hesaba katarak araligi bozuyor, 0/25/50/75/100
         yuzdelerinden kayan bir konum uretiyordu. Duzeltme: her etiket
         icin PIKSEL-KESIN bir top_pct onceden (burada, Python'da) hesaplanip
         `position:absolute; top: {top_pct}%` ile yerlestiriliyor (bkz.
         sablon/card.html) -- boylece etiket ile bar'in gercek yuzde-yukseklik
         olceginin AYNI referans noktasini kullanmasi garanti edilir.
      2. .chart-lower (negatif bar alani) CSS'te has_negative olmasa BILE
         her zaman ust ile ayni yer kapliyordu; bu da eksen ile bar sutununun
         gercek render yuksekligi arasinda uyumsuzluga, dolayisiyla gorsel
         olarak "sikismis" bir eksen/bar oranina yol aciyordu. Duzeltme:
         sablonda has_negative degilse .chart-lower 0 yuksekliğe collapse
         edilir (bkz. .mini-chart.has-negative .chart-lower).

    Seride en az bir negatif deger varsa (has_negative) eksen simetrik hale
    getirilir: +axis_max'tan 0'a, 0'dan -axis_max'e kadar uzanir; toplam
    eksen yuksekligi _AXIS_UPPER_PX + _AXIS_ZERO_PX + _AXIS_LOWER_PX olur,
    yoksa sadece _AXIS_UPPER_PX.

    Ayrica en son (en guncel) ceyregin degeri current_value_display/
    current_value_class olarak AYRICA doner -- sablon bunu mini grafigin
    basligi yaninda bir "guncel deger" etiketi olarak gosterir (profesyonel
    finans panellerindeki gibi en onemli rakami one cikarir); bar'in kendisi
    de (bkz. card.html .mini-chart .chart-col:last-child) hafifce vurgulanir."""
    max_abs = max((abs(v) for v in values if v is not None), default=None)
    has_negative = any(v is not None and v < 0 for v in values)
    axis_step, tick_count = _nice_axis_step(max_abs) if max_abs else (Decimal(0), 0)
    axis_max = axis_step * tick_count if tick_count else None

    points = []
    for label, value in zip(period_labels, values):
        if value is None or not axis_max:
            points.append({"label": label, "display": "—", "pos_pct": 0, "neg_pct": 0})
            continue
        pct = max(int(round(abs(value) / axis_max * 100)), _MIN_BAR_PCT) if value != 0 else 0
        display = format_currency_short(value, symbol=currency_symbol)
        if value >= 0:
            points.append({"label": label, "display": display, "pos_pct": pct, "neg_pct": 0})
        else:
            points.append({"label": label, "display": display, "pos_pct": 0, "neg_pct": pct})

    y_axis_ticks: list[dict] = []
    if axis_max:
        axis_total_px = _AXIS_UPPER_PX + (_AXIS_ZERO_PX + _AXIS_LOWER_PX if has_negative else 0)
        for i in range(tick_count, -1, -1):
            tick_value = axis_step * i
            top_px = (tick_count - i) / tick_count * _AXIS_UPPER_PX
            y_axis_ticks.append({"label": _axis_tick_label(tick_value), "top_pct": top_px / axis_total_px * 100})
        if has_negative:
            for i in range(1, tick_count + 1):
                tick_value = -axis_step * i
                top_px = _AXIS_UPPER_PX + _AXIS_ZERO_PX + (i / tick_count) * _AXIS_LOWER_PX
                y_axis_ticks.append({"label": _axis_tick_label(tick_value), "top_pct": top_px / axis_total_px * 100})

    last_value = values[-1] if values else None
    if last_value is None:
        current_value_class = "neutral"
    elif last_value > 0:
        current_value_class = "positive"
    elif last_value < 0:
        current_value_class = "negative"
    else:
        current_value_class = "neutral"

    return {
        "title": title,
        "points": points,
        "y_axis_ticks": y_axis_ticks,
        "has_negative": has_negative,
        # Izgara cizgileri (bkz. card.html .chart-upper/.chart-lower) sabit
        # %25 araliklarla DEGIL, bu grafigin GERCEK tik sayisina gore
        # (100/tick_count) inline bir CSS degiskeni olarak yerlestirilir --
        # tick_count artik sabit 4 degil, veriye gore degisiyor (bkz.
        # _nice_axis_step). tick_count=0 iken (veri yok) 25 varsayilanina
        # duser, ama o durumda zaten hicbir cizgi gorunmuyor olacak.
        "grid_interval_pct": (100 / tick_count) if tick_count else 25,
        "current_value_display": points[-1]["display"] if points else "—",
        "current_value_class": current_value_class,
    }


def _table_period_labels(latest_period: calculator.Period, label_fn=_quarter_label) -> dict:
    """GELİR TABLOSU/BİLANÇO basliklarinda "Güncel"/"Geçen Yıl"/"Ö. Çeyrek"
    gibi JENERIK etiketler yerine GERÇEK donem etiketleri (orn. "2Ç26",
    "2Ç25") gosterilmesi icin -- kullanici geri bildirimi: "hangi donemle
    karsilastirildigi belli degildi, direkt yil/donem yazsak daha iyi olur".
    Gelir tablosu YoY (bir yil once ayni ceyrek), bilanco QoQ (bir onceki
    ceyrek) karsilastirir -- bkz. calculator.analyze() icindeki ayni ayrim.

    `label_fn`: US_GAAP kartlari icin `_fiscal_quarter_label` verilir (bkz.
    build_us_card_context()) -- "year" mali yil oldugu icin TAKVIM ceyregi
    UYDURULMAZ."""
    return {
        "current": label_fn(latest_period),
        "income_comparison": label_fn(calculator.year_ago_period(latest_period)),
        "balance_comparison": label_fn(calculator.previous_quarter_period(latest_period)),
    }


def _valuation_context(valuation: calculator.ValuationMetrics | None, currency_symbol: str = "₺") -> dict | None:
    """ValuationMetrics'i (varsa) karttaki DEĞERLEME kutucuklari icin
    onceden Turkce bicimlendirilmis string'lere cevirir. Fiyat/sermaye
    ikisi de yoksa (henuz cekilememis) None doner -- sablon bu durumda
    tum bolumu gizler (bkz. card.html valuation-section kosulu)."""
    if valuation is None:
        return None
    return {
        "piyasa_degeri": _money_or_na(valuation.market_cap, currency_symbol),
        "sermaye": _money_or_na(valuation.share_capital, currency_symbol),
        "fk": _ratio_or_na(valuation.pe_ratio),
        "pd_dd": _ratio_or_na(valuation.pb_ratio),
        "fd_favok": _ratio_or_na(valuation.ev_ebitda),
        "fd_hasilat": _ratio_or_na(valuation.ev_revenue),
        "pd_efk": _ratio_or_na(valuation.price_to_operating_profit),
    }


def _valuation_context_bank(valuation: calculator.BankValuationMetrics | None) -> dict | None:
    """_valuation_context()'in banka karsiligi -- BILEREK sadece Piyasa
    Degeri/F-K/PD-DD icerir (bkz. calculator.compute_valuation_bank docstring'i:
    bankalar icin FD bazli carpanlar anlamsizdir, referans kartlarda da
    gosterilmez)."""
    if valuation is None:
        return None
    return {
        "piyasa_degeri": _money_or_na(valuation.market_cap),
        "fk": _ratio_or_na(valuation.pe_ratio),
        "pd_dd": _ratio_or_na(valuation.pb_ratio),
    }


def _valuation_context_insurance(valuation: calculator.InsuranceValuationMetrics | None) -> dict | None:
    """_valuation_context()'in sigorta karsiligi -- bankadaki gibi BILEREK
    sadece Piyasa Degeri/F-K/PD-DD icerir (bkz. compute_valuation_insurance
    docstring'i)."""
    if valuation is None:
        return None
    return {
        "piyasa_degeri": _money_or_na(valuation.market_cap),
        "fk": _ratio_or_na(valuation.pe_ratio),
        "pd_dd": _ratio_or_na(valuation.pb_ratio),
    }


def build_card_context(
    analysis: calculator.AnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    disclosures: list[kap.Disclosure] | None = None,
    *,
    company_name: str | None = None,
    sector: str | None = None,
    price: Decimal | None = None,
    valuation: calculator.ValuationMetrics | None = None,
    valuation_assessment: ValuationAssessment | None = None,
    data_sources_note: str = "İş Yatırım, KAP",
    now: datetime | None = None,
) -> dict:
    """calculator/scorer/commentary ciktisini render_card()'in bekledigi
    duz dict'e cevirir (bkz. modul docstring'indeki sema). Hicbir sayi
    HESAPLAMAZ -- sadece Turkce bicimlendirir ve gorsel siniflara (renk,
    rozet) esler.

    `valuation_assessment` (2026-08-04, kullanıcı isteği): BİLANÇO SKORU
    bölümündeki kompakt "Değerleme Analizi" kutusu için -- context'e
    `valuation_analysis` anahtarıyla eklenir (mevcut `valuation` anahtarı
    ÜST BANTTAKİ Piyasa Değeri/F-K/PD-DD şeridi için ZATEN kullanıldığından
    ÇAKIŞMASIN diye AYRI bir anahtar). `src.render.valuation_view` (Derin
    Kart'ın da kullandığı PAYLAŞILAN formatlayıcı, bkz. o modülün
    docstring'i) ile biçimlendirilir -- hesaplamanın kendisi burada
    YAPILMAZ, sadece `src.analysis.valuation.compute_valuation_assessment()`
    çıktısı (varsa) Türkçeleştirilir."""
    disclosures = disclosures or []
    now = now or datetime.now()

    # FAVÖK SATIRI her zaman gorunur (deger None ise _line_item_row "N/A"
    # gosterir) -- CANLI HATA (kullanici raporu, MSFT/ASTS, bkz.
    # 06_BILINEN_SORUNLAR.md §A29/§B17): satir tamamen GIZLENINCE kart
    # gorsel olarak eksik/dengesiz gorunuyordu (5 yerine 4 metrik). SADECE
    # grafik (asagida, show_ebitda) veri yoksa gizlenmeye devam eder --
    # bos bir cubuk grafigi anlamsizdir, ama bir "N/A" satiri anlamlidir.
    show_ebitda = analysis.income_statement.ebitda is not None

    income_rows = {
        "revenue": _line_item_row(analysis.income_statement.revenue),
        "gross_profit": _line_item_row(analysis.income_statement.gross_profit),
        "operating_profit": _line_item_row(analysis.income_statement.operating_profit),
        "ebitda": _line_item_row(analysis.income_statement.ebitda, field_label=calculator.FIELD_LABELS_TR["ebitda"]),
        "net_income": _line_item_row(analysis.income_statement.net_income),
    }
    # Fintables/Matriks referans kartlariyla (bkz. references/ klasoru,
    # kullanici geri bildirimi) birebir eslesmesi icin BİLANÇO tablosu
    # Donen Varlıklar/Duran Varlıklar/Toplam Varlıklar/Net Borç/Özkaynaklar
    # gosterir -- Nakit/Ticari Alacaklar/Finansal Borçlar ayri satir olarak
    # GOSTERILMEZ (Net Borç zaten bu ikisinin farki), ama AnalysisResult
    # icinde hesapli kalmaya devam eder (bkz. calculator.BalanceSheetSummary).
    balance_rows = {
        "current_assets": _line_item_row(analysis.balance_sheet.current_assets),
        "non_current_assets": _line_item_row(analysis.balance_sheet.non_current_assets),
        "total_assets": _line_item_row(analysis.balance_sheet.total_assets),
        "net_debt": _line_item_row(analysis.balance_sheet.net_debt, lower_is_better=True),
        "equity": _line_item_row(analysis.balance_sheet.equity),
    }

    period_labels = [_quarter_label(pt.period) for pt in analysis.quarterly_series]
    charts = {
        "revenue": _build_chart("Satışlar", [pt.revenue for pt in analysis.quarterly_series], period_labels),
        "ebitda": (
            _build_chart("FAVÖK", [pt.ebitda for pt in analysis.quarterly_series], period_labels) if show_ebitda else None
        ),
        "net_income": _build_chart("Net Kâr", [pt.net_income for pt in analysis.quarterly_series], period_labels),
    }

    onemli_bildirimler = [d for d in disclosures if d.importance == kap.IMPORTANCE_HIGH][:5]
    disclosure_rows = [{"date": d.date.strftime("%d.%m.%Y"), "title": d.title} for d in onemli_bildirimler]

    return {
        "sector_template": "sanayi",
        "ticker": analysis.ticker,
        "company_logo_data_uri": _company_logo_data_uri(analysis.ticker),
        "company_name": company_name or analysis.ticker,
        "sector": sector,
        "period_label": _quarter_label(analysis.latest_period),
        "period_badge": f"{analysis.latest_period[0]}/{analysis.latest_period[1]}",
        "table_periods": _table_period_labels(analysis.latest_period),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "price_display": f"{format_number_tr(price, decimals=2)} ₺" if price is not None else None,
        "valuation": _valuation_context(valuation),
        "valuation_analysis": valuation_view.build_valuation_view(valuation_assessment, "BIST"),
        "headline": commentary.headline,
        "summary": commentary.summary,
        "show_ebitda": show_ebitda,
        "income_rows": income_rows,
        "balance_rows": balance_rows,
        "charts": charts,
        "positives": commentary.positives,
        "negatives": commentary.negatives,
        **_score_display_context(score),
        "score_rows": [_score_row(c) for c in score.components],
        "kap_note": commentary.kap_note,
        "disclosure_rows": disclosure_rows,
        "commentary_source": commentary.source,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


_USD_SYMBOL = "$"


def build_us_card_context(
    analysis: calculator.AnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    disclosures: list | None = None,
    *,
    company_name: str | None = None,
    sector: str | None = None,
    price: Decimal | None = None,
    valuation: calculator.ValuationMetrics | None = None,
    valuation_assessment: ValuationAssessment | None = None,
    data_sources_note: str = "SEC EDGAR (XBRL)",
    now: datetime | None = None,
) -> dict:
    """build_card_context()'in NASDAQ/ABD (US_GAAP) karsiligi -- Faz 10.

    `analysis`/`score`/`valuation` calculator.analyze_us()/scorer.score_industrial_us()/
    calculator.compute_valuation() ile uretilir ve build_card_context()'in
    bekledigi ile TAMAMEN AYNI TIPTEDIR (calculator.AnalysisResult/
    calculator.ValuationMetrics/scorer.ScoreResult -- ayri US_GAAP'e ozel
    tip YOK, bkz. analyze_us() docstring'i). Bu yuzden bu fonksiyon
    build_card_context()'i COPY-PASTE ETMEK yerine AYNI ozel yardimcilari
    (_line_item_row/_build_chart/_valuation_context/_score_row/vb.)
    `currency_symbol="$"` ile CAGIRIR -- SADECE 3 fark vardir:
      1. Para birimi sembolu: ₺ yerine $ (bkz. yukaridaki yardimcilarin
         currency_symbol parametresi).
      2. Donem etiketi: `_fiscal_quarter_label` ("FYyy Çn") kullanilir,
         `_quarter_label` ("nÇyy") DEGIL -- "year" burada TAKVIM yili
         DEGIL sirketin KENDI mali yilidir (bkz. sec_edgar.py modul notu),
         "1Ç27" gibi bir etiket YANLIŞLIKLA takvim ceyregi izlenimi verirdi.
      3. `sector_template: "abd"` -- card.html'deki `{% if sector_template ==
         "banka" %} {% elif sector_template == "sigorta" %} {% else %}`
         kosullarinin HICBIRINE eslesmedigi icin OTOMATIK olarak sanayi
         seklindeki (varsayilan/else) satir/grafik/degerleme duzenine
         DUSER -- income_rows/balance_rows semasi zaten XI_29 ile AYNI
         oldugundan (revenue/gross_profit/operating_profit/ebitda/net_income,
         current_assets/non_current_assets/total_assets/net_debt/equity)
         card.html'de HICBIR YENI sablon/kosul EKLENMESI GEREKMEDI (CANLI
         dogrulandi: sablonda hicbir yerde "₺" hardcode edilmemis, tum para
         degerleri Python'dan ONCEDEN bicimlendirilmis string olarak gelir).

    KAP bildirimleri (`disclosures`) bu fazda YOKTUR -- ABD'nin KAP
    karsiligi (SEC 8-K haberleri) BU FAZIN KAPSAMI DISINDA, `disclosures`
    HER ZAMAN bos liste varsayilir (parametre sadece imza uyumlulugu icin
    tutuldu, cagiran taraf None/bos gecmelidir)."""
    disclosures = disclosures or []
    now = now or datetime.now()

    # FAVÖK SATIRI her zaman gorunur -- bkz. build_card_context() yukaridaki
    # ayni notu (§B17). SADECE grafik (show_ebitda) veri yoksa gizlenir.
    show_ebitda = analysis.income_statement.ebitda is not None

    income_rows = {
        "revenue": _line_item_row(analysis.income_statement.revenue, currency_symbol=_USD_SYMBOL),
        "gross_profit": _line_item_row(analysis.income_statement.gross_profit, currency_symbol=_USD_SYMBOL),
        "operating_profit": _line_item_row(analysis.income_statement.operating_profit, currency_symbol=_USD_SYMBOL),
        "ebitda": _ebitda_row_with_ttm_fallback(analysis, currency_symbol=_USD_SYMBOL),
        "net_income": _line_item_row(analysis.income_statement.net_income, currency_symbol=_USD_SYMBOL),
    }
    balance_rows = {
        "current_assets": _line_item_row(analysis.balance_sheet.current_assets, currency_symbol=_USD_SYMBOL),
        "non_current_assets": _line_item_row(analysis.balance_sheet.non_current_assets, currency_symbol=_USD_SYMBOL),
        "total_assets": _line_item_row(analysis.balance_sheet.total_assets, currency_symbol=_USD_SYMBOL),
        "net_debt": _line_item_row(analysis.balance_sheet.net_debt, lower_is_better=True, currency_symbol=_USD_SYMBOL),
        "equity": _line_item_row(analysis.balance_sheet.equity, currency_symbol=_USD_SYMBOL),
    }

    us_label_fn = lambda p: _fiscal_quarter_label(p, annual_only=analysis.is_annual_only)  # noqa: E731

    period_labels = [us_label_fn(pt.period) for pt in analysis.quarterly_series]
    charts = {
        "revenue": _build_chart("Satışlar", [pt.revenue for pt in analysis.quarterly_series], period_labels, _USD_SYMBOL),
        "ebitda": (
            _build_chart("FAVÖK", [pt.ebitda for pt in analysis.quarterly_series], period_labels, _USD_SYMBOL)
            if show_ebitda
            else None
        ),
        "net_income": _build_chart("Net Kâr", [pt.net_income for pt in analysis.quarterly_series], period_labels, _USD_SYMBOL),
    }

    return {
        "sector_template": "abd",
        "ticker": analysis.ticker,
        "company_logo_data_uri": _company_logo_data_uri(analysis.ticker, market="NASDAQ"),
        "company_name": company_name or analysis.ticker,
        "sector": sector,
        "period_label": us_label_fn(analysis.latest_period),
        "period_badge": f"FY{analysis.latest_period[0]}/{analysis.latest_period[1]}",
        "table_periods": _table_period_labels(analysis.latest_period, label_fn=us_label_fn),
        "is_annual_only": analysis.is_annual_only,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "price_display": f"{_USD_SYMBOL}{format_number_tr(price, decimals=2)}" if price is not None else None,
        "valuation": _valuation_context(valuation, _USD_SYMBOL),
        "valuation_analysis": valuation_view.build_valuation_view(valuation_assessment, "NASDAQ"),
        "headline": commentary.headline,
        "summary": commentary.summary,
        "show_ebitda": show_ebitda,
        "income_rows": income_rows,
        "balance_rows": balance_rows,
        "charts": charts,
        "positives": commentary.positives,
        "negatives": commentary.negatives,
        **_score_display_context(score),
        "score_rows": [_score_row(c) for c in score.components],
        "kap_note": None,
        "disclosure_rows": [],
        "commentary_source": commentary.source,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


def build_bank_card_context(
    analysis: calculator.BankAnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    disclosures: list[kap.Disclosure] | None = None,
    *,
    company_name: str | None = None,
    sector: str | None = None,
    price: Decimal | None = None,
    valuation: calculator.BankValuationMetrics | None = None,
    data_sources_note: str = "İş Yatırım (solo), en güncel çeyrek KAP'tan konsolide gelmiş olabilir",
    now: datetime | None = None,
) -> dict:
    """build_card_context()'in banka (UFRS) karsiligi. Donen sozlukteki
    `sector_template: "banka"` alani, card.html'in hangi tablo/degerleme/
    grafik bolumunu (sanayi vs banka) cizecegine karar vermesini saglar --
    bkz. modul ici ust not (BankIncomeStatementSummary/BankBalanceSheetSummary
    sanayi sirketlerinden TAMAMEN FARKLI kalemler tasir).

    ONEMLI (canli dogrulandi -- GARAN icin isyatirim.com.tr'nin kendi
    sitesinde "Konsolide UFRS" / "Konsolide Olmayan UFRS" secimi test
    edildi): bu projenin kullandigi HERKESE ACIK MaliTablo JSON uc noktasi
    (companyCode+exchange+financialGroup) bankalar icin SADECE "Konsolide
    Olmayan" (solo, banka-tek-basina) veriyi donduruyor -- ornegin GARAN
    Krediler: solo=2.624.664.000.000 iken Konsolide (kiralama/faktoring
    istirakleri dahil grup geneli, Fintables'in gosterdigi) 2.997.999.000.000.
    Denenen 5 alternatif financialGroup degeri (UFRS_KONSOLIDE, UFRSK, vb.)
    bos sonuc dondu -- konsolide veri bu herkese acik uc noktada YOK, sadece
    sitenin kendi ic mekanizmasinda erisiliyor. Bu yuzden data_sources_note
    varsayilani ACIKCA "solo/konsolide olmayan" der -- Fintables/haberlerdeki
    konsolide rakamlarla farkli olmasi BEKLENEN bir durumdur, veri hatasi
    DEGILDIR."""
    disclosures = disclosures or []
    now = now or datetime.now()

    income_rows = {
        "interest_income": _line_item_row(analysis.income_statement.interest_income),
        "interest_expense": _line_item_row(analysis.income_statement.interest_expense),
        "net_fee_income": _line_item_row(analysis.income_statement.net_fee_income),
        "net_operating_profit": _line_item_row(analysis.income_statement.net_operating_profit),
        "net_income": _line_item_row(analysis.income_statement.net_income),
    }
    balance_rows = {
        "loans": _line_item_row(analysis.balance_sheet.loans),
        "deposits": _line_item_row(analysis.balance_sheet.deposits),
        "provisions": _line_item_row(analysis.balance_sheet.provisions),
        "total_assets": _line_item_row(analysis.balance_sheet.total_assets),
        "equity": _line_item_row(analysis.balance_sheet.equity),
    }

    period_labels = [_quarter_label(pt.period) for pt in analysis.quarterly_series]
    charts = {
        "net_interest_income": _build_chart(
            "Net Faiz Geliri", [pt.net_interest_income for pt in analysis.quarterly_series], period_labels
        ),
        "net_income": _build_chart("Net Kâr", [pt.net_income for pt in analysis.quarterly_series], period_labels),
        "loans": _build_chart("Krediler", [pt.loans for pt in analysis.quarterly_series], period_labels),
    }

    onemli_bildirimler = [d for d in disclosures if d.importance == kap.IMPORTANCE_HIGH][:5]
    disclosure_rows = [{"date": d.date.strftime("%d.%m.%Y"), "title": d.title} for d in onemli_bildirimler]

    return {
        "sector_template": "banka",
        "ticker": analysis.ticker,
        "company_logo_data_uri": _company_logo_data_uri(analysis.ticker),
        "company_name": company_name or analysis.ticker,
        "sector": sector,
        "period_label": _quarter_label(analysis.latest_period),
        "period_badge": f"{analysis.latest_period[0]}/{analysis.latest_period[1]}",
        "table_periods": _table_period_labels(analysis.latest_period),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "price_display": f"{format_number_tr(price, decimals=2)} ₺" if price is not None else None,
        "valuation": _valuation_context_bank(valuation),
        # Değerleme Analizi kutusu (bkz. build_card_context docstring'i) BU
        # FAZDA banka/sigorta kartlarına EKLENMEDİ (kapsam kararı: Derin
        # Kart'ın da SADECE XI_29/US_GAAP desteklediği emsaliyle tutarlı) --
        # ama card.html şablonu SADECE `sector_template` DEĞİL, `score_rows`
        # döngüsünün HEMEN ALTINDA KOŞULSUZ `valuation_analysis.has_data`
        # kontrolü yapıyor (bkz. şablon), bu yüzden anahtar HER context'te
        # (has_data=False ile) bulunmalı, yoksa Jinja UndefinedError fırlatır.
        "valuation_analysis": {"has_data": False},
        "headline": commentary.headline,
        "summary": commentary.summary,
        "show_ebitda": False,
        "income_rows": income_rows,
        "balance_rows": balance_rows,
        "charts": charts,
        "positives": commentary.positives,
        "negatives": commentary.negatives,
        **_score_display_context(score),
        "score_rows": [_score_row(c) for c in score.components],
        "kap_note": commentary.kap_note,
        "disclosure_rows": disclosure_rows,
        "commentary_source": commentary.source,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


def build_insurance_card_context(
    analysis: calculator.InsuranceAnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    disclosures: list[kap.Disclosure] | None = None,
    *,
    company_name: str | None = None,
    sector: str | None = None,
    price: Decimal | None = None,
    valuation: calculator.InsuranceValuationMetrics | None = None,
    data_sources_note: str = "İş Yatırım, KAP",
    now: datetime | None = None,
) -> dict:
    """build_card_context()'in sigorta (UFRS_K) karsiligi. Donen sozlukteki
    `sector_template: "sigorta"` alani, card.html'in hangi tablo/degerleme/
    grafik bolumunu cizecegine karar vermesini saglar -- bkz.
    InsuranceIncomeStatementSummary/InsuranceBalanceSheetSummary (ANSGR ile
    canli dogrulandi, ratios/tum kalemler referans kartla BIREBIR eslesti)."""
    disclosures = disclosures or []
    now = now or datetime.now()

    income_rows = {
        "gross_written_premiums": _line_item_row(analysis.income_statement.gross_written_premiums),
        "net_premiums_earned": _line_item_row(analysis.income_statement.net_premiums_earned),
        "technical_income": _line_item_row(analysis.income_statement.technical_income),
        "technical_balance": _line_item_row(analysis.income_statement.technical_balance),
        "net_income": _line_item_row(analysis.income_statement.net_income),
    }
    balance_rows = {
        "cash_and_financial_assets": _line_item_row(analysis.balance_sheet.cash_and_financial_assets),
        "receivables_from_operations": _line_item_row(analysis.balance_sheet.receivables_from_operations),
        "technical_provisions": _line_item_row(analysis.balance_sheet.technical_provisions),
        "payables_from_operations": _line_item_row(analysis.balance_sheet.payables_from_operations),
        "equity": _line_item_row(analysis.balance_sheet.equity),
    }

    period_labels = [_quarter_label(pt.period) for pt in analysis.quarterly_series]
    charts = {
        "gross_written_premiums": _build_chart(
            "Prim Üretimi", [pt.gross_written_premiums for pt in analysis.quarterly_series], period_labels
        ),
        "technical_balance": _build_chart(
            "Teknik Denge", [pt.technical_balance for pt in analysis.quarterly_series], period_labels
        ),
        "net_income": _build_chart("Net Kâr", [pt.net_income for pt in analysis.quarterly_series], period_labels),
    }

    onemli_bildirimler = [d for d in disclosures if d.importance == kap.IMPORTANCE_HIGH][:5]
    disclosure_rows = [{"date": d.date.strftime("%d.%m.%Y"), "title": d.title} for d in onemli_bildirimler]

    return {
        "sector_template": "sigorta",
        "ticker": analysis.ticker,
        "company_logo_data_uri": _company_logo_data_uri(analysis.ticker),
        "company_name": company_name or analysis.ticker,
        "sector": sector,
        "period_label": _quarter_label(analysis.latest_period),
        "period_badge": f"{analysis.latest_period[0]}/{analysis.latest_period[1]}",
        "table_periods": _table_period_labels(analysis.latest_period),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "price_display": f"{format_number_tr(price, decimals=2)} ₺" if price is not None else None,
        "valuation": _valuation_context_insurance(valuation),
        # bkz. build_bank_card_context() içindeki aynı notu -- bu faz
        # kapsamına girmiyor ama anahtar şablon için HER ZAMAN gerekli.
        "valuation_analysis": {"has_data": False},
        "headline": commentary.headline,
        "summary": commentary.summary,
        "show_ebitda": False,
        "income_rows": income_rows,
        "balance_rows": balance_rows,
        "charts": charts,
        "positives": commentary.positives,
        "negatives": commentary.negatives,
        **_score_display_context(score),
        "score_rows": [_score_row(c) for c in score.components],
        "kap_note": commentary.kap_note,
        "disclosure_rows": disclosure_rows,
        "commentary_source": commentary.source,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


_TEASER_HEADLINE_MAX_CHARS = 90  # roadmap kurali: "maks ~90 karakter, tasarsa kelime sinirinda kes + …"
_TEASER_DISCLAIMER = "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır."


def _truncate_headline(text: str, max_chars: int = _TEASER_HEADLINE_MAX_CHARS) -> str:
    """Teaser kartinin KISITLI tek-cumlelik alani icin -- kelime SINIRINDA
    keser (ortasinda kelime kesmek okunmaz gorunur), sonuna "…" ekler."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated.rstrip(".,;: ") + "…"


def _teaser_metric(item: calculator.LineItemChange | None, label: str, *, lower_is_better: bool = False) -> dict:
    """Faz 14 alt seridindeki 3 kutudan biri (Satışlar/FAVÖK/Net Kâr YoY
    vb.) -- `_line_item_row()`'un KISALTILMIŞ hali (SADECE yüzde + renk,
    tutar YOK -- teaser'da yer kısıtı var). Veri yoksa "N/A" (Kural 8:
    uydurma yok)."""
    if item is None:
        return {"label": label, "display": "N/A", "color_class": "neutral"}
    if item.percent_change is None:
        return {"label": label, "display": item.change_label, "color_class": _LABEL_COLOR_CLASS.get(item.change_label, "neutral")}
    return {
        "label": label,
        "display": format_percent_tr(item.percent_change),
        "color_class": _item_color_class(item, lower_is_better=lower_is_better),
    }


def _teaser_base_fields(
    ticker: str,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    *,
    company_name: str | None,
    price: Decimal | None,
    market: str,
    currency_symbol: str,
    period_label: str,
    data_sources_note: str,
    now: datetime,
) -> dict:
    """4 sektör varyantının (sanayi/US/banka/sigorta) ORTAK alanları --
    kopyala-yapıştır yerine tek yerde (Faz 16 ilkesi: "ortak kodu çıkar").
    Her `build_*_teaser_context()` bunu SADECE kendi `metrics` listesiyle
    tamamlar.

    Fiyat biçimi: $ ÖNEKTE ("$100,00"), ₺ SONEKTE ("142,50 ₺") -- ana
    kart ailesindeki (build_us_card_context/build_card_context) MEVCUT
    kuralla AYNI (bkz. o fonksiyonların price_display satırları), yeni
    bir kural İCAT EDİLMEDİ."""
    if price is None:
        price_display = None
    elif currency_symbol == _USD_SYMBOL:
        price_display = f"{currency_symbol}{format_number_tr(price, decimals=2)}"
    else:
        price_display = f"{format_number_tr(price, decimals=2)} {currency_symbol}"
    return {
        "ticker": ticker,
        "company_logo_data_uri": _company_logo_data_uri(ticker, market=market),
        "company_name": company_name or ticker,
        "period_label": period_label,
        "price_display": price_display,
        **_score_display_context(score),
        "headline": _truncate_headline(commentary.headline),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "data_sources_note": data_sources_note,
        "disclaimer": _TEASER_DISCLAIMER,
    }


def build_teaser_context(
    analysis: calculator.AnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    *,
    company_name: str | None = None,
    price: Decimal | None = None,
    market: str = "BIST",
    currency_symbol: str = "₺",
    data_sources_note: str = "İş Yatırım, KAP",
    now: datetime | None = None,
) -> dict:
    """Faz 14: X/Twitter akışında TIKLANMADAN okunabilen 16:9 'teaser'
    kart context'i -- SADECE build_card_context() ile AYNI girdilerden
    (analysis/score/commentary, zaten hesaplanmış) biçimlendirir, HİÇBİR
    YENİ hesap YAPMAZ. US_GAAP (Faz 9/10) sanayi ile AYNI AnalysisResult
    tipini paylaştığı için (bkz. build_us_card_context docstring'i) BU
    fonksiyon HER İKİSİNDE de kullanılır -- `market="NASDAQ"` verilince
    dönem etiketi `_fiscal_quarter_label()` (mali yıl, `analysis.
    is_annual_only` ile), `market="BIST"` (varsayılan) `_quarter_label()`
    (takvim çeyreği) kullanır -- çağıran taraf (telegram_bot.py) bu
    ayrımı BİLMEK ZORUNDA DEĞİL, SADECE `market` geçer (private
    yardımcı fonksiyonlara modül dışından erişim GEREKMEZ).

    Kart TASARIMI (roadmap, FAZ 14): en fazla 7 sayı, EN FAZLA 1 cümlelik
    hüküm -- X akışında kırpılmadan (16:9) okunsun diye kasıtlı olarak
    ana karttan ÇOK daha az bilgi taşır."""
    now = now or datetime.now()
    if market == "NASDAQ":
        period_label = _fiscal_quarter_label(analysis.latest_period, annual_only=analysis.is_annual_only)
    else:
        period_label = _quarter_label(analysis.latest_period)
    base = _teaser_base_fields(
        analysis.ticker, score, commentary,
        company_name=company_name, price=price, market=market, currency_symbol=currency_symbol,
        period_label=period_label, data_sources_note=data_sources_note, now=now,
    )
    base["metrics"] = [
        _teaser_metric(analysis.income_statement.revenue, "SATIŞLAR"),
        _teaser_metric(analysis.income_statement.ebitda, "FAVÖK"),
        _teaser_metric(analysis.income_statement.net_income, "NET KÂR"),
    ]
    return base


def build_bank_teaser_context(
    analysis: calculator.BankAnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    *,
    company_name: str | None = None,
    price: Decimal | None = None,
    data_sources_note: str = "İş Yatırım (solo)",
    now: datetime | None = None,
) -> dict:
    """build_teaser_context()'in banka karşılığı -- BankIncomeStatementSummary
    sanayiden FARKLI kalemler taşıdığı için (revenue/ebitda YOK) alt şerit
    metrikleri banka'ya uygun karşılıklarla değiştirilir (roadmap notu:
    "banka/sigortada uygun karşılıkları kullan")."""
    now = now or datetime.now()
    base = _teaser_base_fields(
        analysis.ticker, score, commentary,
        company_name=company_name, price=price, market="BIST", currency_symbol="₺",
        period_label=_quarter_label(analysis.latest_period), data_sources_note=data_sources_note, now=now,
    )
    base["metrics"] = [
        _teaser_metric(analysis.income_statement.interest_income, "FAİZ GELİRİ"),
        _teaser_metric(analysis.income_statement.net_operating_profit, "FAALİYET KÂRI"),
        _teaser_metric(analysis.income_statement.net_income, "NET KÂR"),
    ]
    return base


def build_insurance_teaser_context(
    analysis: calculator.InsuranceAnalysisResult,
    score: scorer.ScoreResult,
    commentary: commentary_module.Commentary,
    *,
    company_name: str | None = None,
    price: Decimal | None = None,
    data_sources_note: str = "İş Yatırım, KAP",
    now: datetime | None = None,
) -> dict:
    """build_teaser_context()'in sigorta karşılığı -- InsuranceIncomeStatementSummary
    sanayiden FARKLI kalemler taşıdığı için alt şerit metrikleri sigortaya
    uygun karşılıklarla değiştirilir (roadmap notu: "banka/sigortada
    uygun karşılıkları kullan")."""
    now = now or datetime.now()
    base = _teaser_base_fields(
        analysis.ticker, score, commentary,
        company_name=company_name, price=price, market="BIST", currency_symbol="₺",
        period_label=_quarter_label(analysis.latest_period), data_sources_note=data_sources_note, now=now,
    )
    base["metrics"] = [
        _teaser_metric(analysis.income_statement.gross_written_premiums, "PRİM ÜRETİMİ"),
        _teaser_metric(analysis.income_statement.technical_balance, "TEKNİK DENGE"),
        _teaser_metric(analysis.income_statement.net_income, "NET KÂR"),
    ]
    return base


def render_html(context: dict, template_name: str = "card.html") -> str:
    """context'ten HTML uretir (Playwright olmadan da test edilebilsin
    diye render_card()'dan ayri tutuldu). `template_name`: templates/
    klasorundeki dosya adi -- varsayilan "card.html" ile mevcut TUM
    cagrilar (render_html(context)) DEGISMEDEN calismaya devam eder."""
    template = _env.get_template(template_name)
    return template.render(**context)


def _debug_html_path(template_name: str) -> Path:
    """Her sablon TURU kendi debug HTML dosyasina yazar (orn.
    'calendar_card.html' -> data/last_calendar_card.html) ki farkli
    kart tipleri (Faz 13+) tasarim denerken birbirinin debug ciktisini
    EZMESIN. Varsayilan "card.html" icin sonuc data/last_card.html --
    Faz 13 ONCESI davranisla BIREBIR AYNI (geriye uyumlu)."""
    return config.DATA_DIR / f"last_{Path(template_name).stem}.html"


def render_card(
    context: dict,
    out_path: str,
    template_name: str = "card.html",
    screenshot_selector: str = "#card",
) -> str:
    """context'i HTML'e render eder, debug icin data/last_{sablon}.html'e
    yazar, sonra Playwright chromium (headless) ile `screenshot_selector`
    elementinin ekran goruntusunu device_scale_factor=2 (retina) ile
    out_path'e PNG olarak kaydeder. Uretilen PNG dosya yolunu (out_path) doner.

    `template_name`/`screenshot_selector`: Faz 13'te render altyapisi
    GENELLESTIRILDI -- eskiden bu fonksiyon card.html/#card'a SABITTI, bu da
    her yeni kart tipinin (takvim karti, Faz 14/16/19'daki teaser/derin/fon
    kartlari) AYRI bir render fonksiyonu YAZMASINI gerektirirdi. Varsayilan
    degerler MEVCUT TUM cagrilari (render_card(context, out_path) iki
    pozisyonel argumanla) DEGISTIRMEDEN korur.

    Hatalar:
        CardRenderError: Playwright/chromium baslatilamadi (kurulu
            olmayabilir -- `playwright install chromium` calistirilmali).
    """
    html = render_html(context, template_name=template_name)

    debug_path = _debug_html_path(template_name)
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    debug_path.write_text(html, encoding="utf-8")

    out_path_obj = Path(out_path)
    out_path_obj.parent.mkdir(parents=True, exist_ok=True)

    browser = _get_browser()
    try:
        page = browser.new_page(viewport={"width": 1000, "height": 1200}, device_scale_factor=2)
        try:
            page.set_content(html, wait_until="load")
            page.locator(screenshot_selector).screenshot(path=str(out_path_obj))
        finally:
            page.close()
    except Exception as exc:  # playwright kendi hata siniflarini firlatir (Error, TimeoutError vb.)
        raise CardRenderError(f"Kart PNG'ye render edilemedi: {exc}") from exc

    logger.info("Kart render edildi: %s", out_path_obj)
    return str(out_path_obj)
