"""docs/spec/spec_dashboard.md §"Dashboard'a gömülecek JSON şeması": `MarketScanResult`
satırlarını okuyup tek dosyalık `output/dashboard.html` piyasa dashboard'unu üretir.

Bu modül -- `src/render/card.py` ile AYNI ilke (quaxis-mimari anayasa) --
HİÇBİR skor/çarpan HESAPLAMAZ: `MarketScanResult` satırları zaten
`scripts/tarama_toplu.py` tarafından ÖNCEDEN hesaplanmış durumda; burada
SADECE okuma + gruplama (sektör/n<5 bayrağı) + Türkçe biçimlendirme +
JSON'a serileştirme + Jinja2 ile HTML render yapılır (`kart-tasarim-sistemi`
skill: "HTML hesaplama yapmaz, sıralama/filtre saf sunum işlemidir").

İki aşama (`src/render/card.py` deseniyle BİREBİR aynı):
    1. build_dashboard_data(session) -- MarketScanResult satırlarını spec'in
       JSON şemasına birebir uyan bir dict'e çevirir (bkz. spec §"Dashboard'a
       gömülecek JSON şeması").
    2. render_dashboard_html(data) -- Jinja2 ile tek-dosyalık, harici
       kaynak/CDN İÇERMEYEN bir HTML üretir (JSON gömülü, arama/filtre/sıralama
       istemci-içi vanilla JS ile yapılır -- skill: "Dashboard PNG değil,
       tarayıcıda açılır").

`build_and_write_dashboard()` ikisini birleştirip `output/dashboard.html`'e
yazar -- Telegram `/piyasa` komutunun (Faz 6/sonraki adım, BU MODÜLÜN
KAPSAMI DIŞINDA) bağlanacağı net arayüz budur.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import jinja2
from sqlalchemy.orm import Session

import config
from src.analysis.lens_common import MIN_SECTOR_N
from src.analysis.scorer import YETERSIZ_VERI_ROZETI
from src.db import repository
from src.db.models import MarketScanResult, utcnow_naive
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
    autoescape=jinja2.select_autoescape(["html"]),
)

_DEFAULT_OUTPUT_PATH = config.BASE_DIR / "output" / "dashboard.html"

# --- Rozet -> CSS sınıfı eşlemesi (src/render/card.py::_BADGE_CLASS ile
#     BİREBİR AYNI -- görsel kimlik TUTARLILIĞI, aynı token sistemi). ------
_BADGE_CLASS: dict[str, str] = {
    "SAĞLAM": "saglam",
    "DENGELİ": "dengeli",
    "KARIŞIK": "karisik",
    "RİSKLİ": "riskli",
    YETERSIZ_VERI_ROZETI: "yetersiz",
}

_SIRKET_TURU_DISPLAY: dict[str | None, str] = {
    "sanayi": "Sanayi",
    "abd_sanayi": "ABD Sanayi",
    "banka": "Banka",
    "sigorta": "Sigorta",
    "finansman": "Finansman",
    "gyo": "GYO",
    None: "—",
}

_MERCEK_ANAHTAR_ETIKET: tuple[tuple[str, str], ...] = (
    ("deger", "değer"), ("kalite", "kalite"), ("buyume", "büyüme"), ("guvenlik", "güvenlik"),
)

# Bir merceğin verisinin "düşük kapsamlı" sayılıp GÖRSEL bir uyarı ikonu
# tetiklemesi için eşik -- v2 mercek modüllerinin KENDİ `data_sufficient`
# eşiğiyle (lens_common, %50) AYNI mertebe; burada YENİDEN türetilmiyor,
# sadece dashboard'un hücre-bazlı görsel işaretleme kararı için kopyalanıyor
# (spec §Veri eksikliği görünürlüğü: "şirket-spesifik eksik veri ... satır
# bazlı sayı ... FARKLI bir sinyaldir").
LOW_COVERAGE_THRESHOLD_PCT = Decimal("50")

# --- spec §Veri eksikliği görünürlüğü: statik, market bazlı sistemik eksik
#     bileşen tablosu (docs/spec/veri_tamlik_notu.md §1-6'nın etiketli
#     karşılığı). Company-SPESİFİK DEĞİL -- aynı piyasadaki HER satırda
#     AYNI liste görünür (spec'in AÇIKÇA istediği davranış). `tur` alanı
#     3 görsel tona eşlenir (bkz. dashboard.html CSS): "yapisal" (sönük/
#     kalıcı), "gecici" (turuncu/"yakında"), "gecici_oncelikli" (öncelikli
#     vurgu), "kismi" (kısmi/özel durum). -------------------------------
PIYASA_SISTEMIK_EKSIK_BILESENLER: dict[str, list[dict[str, str]]] = {
    "BIST": [
        {"mercek": "kalite", "bilesen": "SG&A / Ar-Ge oranı", "tur": "yapisal",
         "aciklama": "BİST'te bu kalemler KAP XBRL'de standart etiketlenmemiş -- sistemik eksik."},
        {"mercek": "kalite", "bilesen": "Hazine Hissesi Düzeltmeli ROE", "tur": "yapisal",
         "aciklama": "BİST'te hazine hissesi nadiren ayrı raporlanır."},
        {"mercek": "güvenlik", "bilesen": "Faiz Karşılama Oranı", "tur": "yapisal",
         "aciklama": "KAP alt-kalem araştırması henüz yapılmadı -- kitaplar arası en sık tekrarlanan açık."},
        {"mercek": "değer", "bilesen": "Temettü Verimi / Payout", "tur": "yapisal",
         "aciklama": "BİST'te DPS verisi henüz çekilmiyor."},
        {"mercek": "büyüme", "bilesen": "Capex Oranı", "tur": "gecici",
         "aciklama": "KAP ifrs-full kaleminden ORTA maliyetle açılabilir, henüz kodlanmadı."},
        {"mercek": "büyüme", "bilesen": "10+ Yıllık Trend Serisi", "tur": "yapisal",
         "aciklama": "MAX_TREND_PERIODS=12 (~3 yıl) mimari kısıt, piyasa-bağımsız."},
        {"mercek": "güvenlik", "bilesen": "Kredi Notu / Temerrüt Olasılığı", "tur": "yapisal",
         "aciklama": "Harici veri kaynağı entegrasyonu henüz yok."},
    ],
    "NASDAQ": [
        {"mercek": "değer", "bilesen": "Greenblatt Kazanç Getirisi + Carlisle Acquirer's Multiple", "tur": "yapisal",
         "aciklama": ("`fundamental_screens.py` SADECE BIST XI_29 (sanayi) şirketleri için çağrılır "
                      "(`pipeline.py`: \"not is_us and financial_group=='XI_29'\") -- NASDAQ'ta bu iki bileşen "
                      "HİÇ hesaplanmaz, ağırlığı (Değer merceği içi %10+%5) diğer bileşenlere yeniden dağıtılır. "
                      "US GAAP/SEC EDGAR karşılığı ayrı bir keşif turu gerektirir, henüz yapılmadı.")},
        {"mercek": "kalite", "bilesen": "Greenblatt ROC (EBIT/Yatırılan Sermaye)", "tur": "yapisal",
         "aciklama": "Aynı BIST-only kısıt (bkz. Değer merceği notu) -- NASDAQ'ta bu bileşen de hesaplanmaz."},
        {"mercek": "kalite", "bilesen": "SG&A / Ar-Ge oranı", "tur": "gecici",
         "aciklama": "us-gaap standart etiketler mevcut, DÜŞÜK maliyetle açılabilir, henüz kodlanmadı."},
        {"mercek": "kalite", "bilesen": "Hazine Hissesi Düzeltmeli ROE", "tur": "gecici_oncelikli",
         "aciklama": "us-gaap:TreasuryStockValue neredeyse evrensel -- öncelikli, düşük maliyetli bir kazanım."},
        {"mercek": "güvenlik", "bilesen": "Faiz Karşılama Oranı", "tur": "gecici",
         "aciklama": "us-gaap:InterestExpense standart tag, orta-düşük maliyet."},
        {"mercek": "değer", "bilesen": "Temettü Verimi / Payout", "tur": "gecici",
         "aciklama": "us-gaap:CommonStockDividendsPerShareDeclared standart, düşük maliyet."},
        {"mercek": "büyüme", "bilesen": "Capex Oranı", "tur": "gecici",
         "aciklama": "us-gaap kaleminden orta-düşük maliyetle açılabilir, henüz kodlanmadı."},
        {"mercek": "değer", "bilesen": "Opsiyon / Warrant Seyreltme", "tur": "kismi",
         "aciklama": "Kaba vekil türetilebilir ama dipnot düzeyi tam veri yok."},
        {"mercek": "büyüme", "bilesen": "10+ Yıllık Trend Serisi", "tur": "yapisal",
         "aciklama": "MAX_TREND_PERIODS=12 (~3 yıl) mimari kısıt, piyasa-bağımsız."},
        {"mercek": "güvenlik", "bilesen": "Kredi Notu / Temerrüt Olasılığı", "tur": "yapisal",
         "aciklama": "Harici veri kaynağı entegrasyonu henüz yok."},
    ],
}

# --- Metodoloji paneli (kullanıcı talebi, 2026-08-12): statik, tarama
#     verisinden BAĞIMSIZ referans metni -- "hangi mercek bileşeni hangi
#     kitap/formüle dayanıyor" sorusunu docs/spec/spec_mercek_*.md ve
#     spec_bilesik_skor.md'deki kitap referans kodlarından (örn. "01/
#     FORMÜL-03" = bilgi-bankasi/01_graham_akilli_yatirimci.md) kullanıcı-
#     okunabilir bir tabloya çevirir. HESAPLAMA DEĞİL -- spec tablolarının
#     BİREBİR kopyası (PIYASA_SISTEMIK_EKSIK_BILESENLER ile AYNI desen,
#     quaxis-mimari anayasa: dashboard.py sadece okur/biçimlendirir). ------
SCORE_METHODOLOGY: dict[str, Any] = {
    "bilesik_aciklama": (
        "Bileşik Skor, 4 merceğin (Değer/Kalite/Büyüme/Güvenlik) kendi içinde "
        "0-10'a normalize edilmiş skorlarının ağırlıklı ortalamasıdır. Bir "
        "mercek veri kapsamı %50'nin altındaysa bileşik skora HİÇ DAHİL "
        "EDİLMEZ -- ağırlığı geri kalan merceklere orantısal olarak yeniden "
        "dağıtılır. Dört merecek de yetersizse rozet doğrudan "
        '"YETERSİZ VERİ" olur (sıfıra bölme hiçbir zaman oluşmaz).'
    ),
    "kapsam_aciklama": (
        '"Kapsam" (veri kapsamı, %), bir merceğin puanının alt-bileşenlerinin '
        "ne kadarının gerçek veriyle hesaplandığını gösterir. %100 kapsam -- "
        "o merceğin TÜM alt-bileşenleri veriye dayanıyor; düşük kapsam -- "
        "bazı alt-bileşenler (örn. sektör karşılaştırması için yetersiz "
        "örneklem ya da eksik ham veri) atlandı ve ağırlığı geri kalan "
        "bileşenlere aktarıldı. %50'nin altındaki kapsam tabloda bir uyarı "
        "ikonuyla işaretlenir."
    ),
    "rozet_esikleri": [
        {"aralik": "≥ 8,0", "rozet": "SAĞLAM", "css": "saglam"},
        {"aralik": "6,0 – 7,9", "rozet": "DENGELİ", "css": "dengeli"},
        {"aralik": "4,0 – 5,9", "rozet": "KARIŞIK", "css": "karisik"},
        {"aralik": "< 4,0", "rozet": "RİSKLİ", "css": "riskli"},
        {"aralik": "kapsam < %50", "rozet": "YETERSİZ VERİ", "css": "yetersiz"},
    ],
    "kaynak_kitaplar": [
        {"kod": "01", "yazar": "Graham",
         "tam_ad": "Benjamin Graham — Akıllı Yatırımcı (rev. 1973, Jason Zweig yorumlarıyla 2003 basımı)"},
        {"kod": "02", "yazar": "Buffett",
         "tam_ad": "Mary Buffett & David Clark — Warren Buffett ve Finansal Tabloları Yorumlama Sanatı"},
        {"kod": "03", "yazar": "Damodaran",
         "tam_ad": "Aswath Damodaran — Değerleme (2. Baskı, 2006)"},
        {"kod": "—", "yazar": "Diğer",
         "tam_ad": ("Joel Greenblatt (Sihirli Formül), Tobias Carlisle (Acquirer's Multiple), "
                    "Joseph Piotroski (F-Skoru, 2000) — kitap-bilgi-bankası dışı, akademik/pratik "
                    "kaynaklar; proje kod tabanında zaten kalibre edilmiş")},
    ],
    "mercekler": [
        {
            "key": "deger", "baslik": "Değer", "bilesik_agirlik": "%30",
            "soru": "Hisse, ödediğiniz paraya göre ucuz mu?",
            "bilesenler": [
                {"isim": "Mutlak Ucuzluk (F/K + PD/DD)", "agirlik": "%35",
                 "esik": "Sektöre özgü F/K ve PD/DD bantları (ucuz/makul/pahalı/tavan)",
                 "kaynak": "01/FORMÜL-02, İLKE-80,133"},
                {"isim": "Sektöre Göreli Konum", "agirlik": "%20",
                 "esik": "Sektör medyanına göre robust z-skor (n≥5 şirket şartı)",
                 "kaynak": "03/BAYRAK-20, İLKE-197"},
                {"isim": "Kazanç Getirisi vs Risksiz Oran", "agirlik": "%15",
                 "esik": "E/P ≥ risksiz faiz + 2 puan tercih edilir",
                 "kaynak": "01/FORMÜL-03,36 · 02/İLKE-52-57 · 03/FORMÜL-84"},
                {"isim": "Graham Çarpanı (F/K × PD/DD)", "agirlik": "%10",
                 "esik": "≤ 22,5 \"savunmacı yatırımcı\" eşiği",
                 "kaynak": "01/FORMÜL-21,32"},
                {"isim": "Greenblatt Kazanç Getirisi (EBIT/FD)", "agirlik": "%10",
                 "esik": "Yüksek EBIT/Firma Değeri = ucuz (borç etkisi dahil)",
                 "kaynak": "Greenblatt, Sihirli Formül"},
                {"isim": "Carlisle Acquirer's Multiple (FD/EBIT)", "agirlik": "%5",
                 "esik": "Düşük FD/EBIT = ucuz",
                 "kaynak": "Carlisle, Acquirer's Multiple"},
                {"isim": "NCAV / Net-Net Bonus", "agirlik": "%5 (bonus)",
                 "esik": "Piyasa değeri net işletme sermayesinin ALTINDAysa bonus (asla ceza yok)",
                 "kaynak": "01/İLKE-64,66,75 · FORMÜL-01,12,14"},
            ],
        },
        {
            "key": "kalite", "baslik": "Kalite", "bilesik_agirlik": "%30",
            "soru": "Şirket sürdürülebilir, dayanıklı bir rekabet avantajına sahip mi?",
            "bilesenler": [
                {"isim": "Nakit Üretimi (FAVÖK marjı)", "agirlik": "%25",
                 "esik": "güçlü ≥ %20, orta ≥ %10", "kaynak": "v1 Radar Skoru çekirdeği · 02/İLKE-01 (genel bağlam)",
                 "uyari": ("BİLİNEN GERİLİM: bu metrik projenin ÖNCEDEN kalibre edilmiş v1 çekirdeğidir, "
                            "Buffett kitabından DOĞRUDAN türetilmemiştir -- kitabın kendisi (02/İLKE-06, s.67-68) "
                            "FAVÖK/EBITDA mantığını \"amortismanı gerçek bir maliyet gibi görmeyen bir YANILSAMA\" "
                            "olarak AÇIKÇA eleştirir. Bu çelişki ÇÖZÜLMEMİŞTİR, bilinçli olarak burada belgelenir "
                            "(bkz. docs/spec/spec_mercek_kalite.md).")},
                {"isim": "Özkaynak Kârlılığı (ROE)", "agirlik": "%20",
                 "esik": "güçlü ≥ %15, orta ≥ %10", "kaynak": "02/FORMÜL-22, İLKE-40,41"},
                {"isim": "Kârlılık (Net Marj)", "agirlik": "%15",
                 "esik": "proje kalibrasyonu (sanayi eşikleri)", "kaynak": "02/FORMÜL-07, İLKE-13"},
                {"isim": "Brüt Kâr Marjı (seviye + trend)", "agirlik": "%15",
                 "esik": "güçlü ≥ %40, orta ≥ %20", "kaynak": "02/FORMÜL-01, İLKE-02,03"},
                {"isim": "Greenblatt ROC (EBIT/Yatırılan Sermaye)", "agirlik": "%10",
                 "esik": "yüksek ≥ %25, düşük ≤ %10", "kaynak": "Greenblatt · 03/İLKE-203,208,212 (kavramsal örtüşme)",
                 "uyari": ("Doğrudan kaynağı Greenblatt'ın Sihirli Formül'üdür (kitap-bilgi-bankası dışı). "
                            "03/İLKE-203,208,212 (Damodaran) BİREBİR aynı formülü tanımlamaz -- ROC/sermaye "
                            "maliyeti farkının firma-değeri çarpanlarını sürüklediği KAVRAMSAL paralelliği kurar, "
                            "gevşek bir bağlam notudur.")},
                {"isim": "ROA", "agirlik": "%5",
                 "esik": "güçlü ≥ %8, orta ≥ %3", "kaynak": "02/FORMÜL-13, İLKE-26"},
                {"isim": "Nakit Kâr Kalitesi (OCF/Net Kâr)", "agirlik": "%10",
                 "esik": "≥1,0 güçlü, 0,7-1,0 orta, <0,7 zayıf", "kaynak": "01/Ch.12 Kontrol L (Piotroski öncülü)"},
            ],
        },
        {
            "key": "buyume", "baslik": "Büyüme", "bilesik_agirlik": "%15",
            "soru": "Şirket ne kadar hızlı VE ne kadar kaliteli büyüyor?",
            "bilesenler": [
                {"isim": "Hasılat Büyümesi (reel, seviye + trend)", "agirlik": "%55",
                 "esik": "sanayi: güçlü ≥ %15 · abd_sanayi: güçlü ≥ %10 (enflasyon-arındırılmış)",
                 "kaynak": "proje kalibrasyonu (Zweig uyarısıyla 01/İLKE-72,73 çapraz okunur)"},
                {"isim": "PEG Oranı (büyümeye göre değerleme)", "agirlik": "%25",
                 "esik": "PEG < 0,9 ucuz · 0,9-1,1 makul · > 1,1 pahalı",
                 "kaynak": "Lynch, GARP · 03/İLKE-159,175, FORMÜL-74"},
                {"isim": "Marjinal ROE + Verimlilik Kaynaklı Büyüme", "agirlik": "%20",
                 "esik": "marjinal ROE − standart ROE farkı sürekli fonksiyonla skorlanır",
                 "kaynak": "03/İLKE-85,86"},
            ],
        },
        {
            "key": "guvenlik", "baslik": "Güvenlik", "bilesik_agirlik": "%25",
            "soru": "Şirket bir krizi/durgunluğu atlatabilir mi, batma riski nedir?",
            "bilesenler": [
                {"isim": "Kaldıraç (Net Borç/FAVÖK)", "agirlik": "%30",
                 "esik": "çok iyi < 1 · iyi < 2,5 · orta < 4", "kaynak": "piyasa pratiği (Moody's/S&P kaldıraç bantları)"},
                {"isim": "Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)", "agirlik": "%20",
                 "esik": "cari oran ≥ 1,5 iyi · özkaynak/varlık ≥ %40 iyi", "kaynak": "01/FORMÜL-26, İLKE-154"},
                {"isim": "Piotroski F-Skoru", "agirlik": "%25",
                 "esik": "9 kriterden ≥5'i hesaplanabiliyorsa oran ≥ %78 güçlü", "kaynak": "Piotroski (2000)"},
                {"isim": "Toplam Yükümlülük/Özkaynak (geniş tanım)", "agirlik": "%15",
                 "esik": "< 1 güçlü · 1-2 orta · > 2 zayıf", "kaynak": "02/FORMÜL-16, İLKE-30"},
                {"isim": "Merton Temerrüt Olasılığı (EDF)", "agirlik": "%10",
                 "esik": "düşük ≤ %1-2 güçlü · yüksek > %10 risk sinyali", "kaynak": "03/İLKE-441-444, FORMÜL-171/172"},
            ],
        },
    ],
}


GYO_UYARI_NOTU: dict[str, str] = {
    "tur": "gyo",
    "aciklama": (
        "Bu şirket bir GYO -- F/K, ROE gibi standart sanayi çarpanları bir REIT için doğrudan "
        "karşılaştırılabilir olmayabilir (NAV/portföy değeri bazlı özel bir değerleme çerçevesi "
        "bu mimaride henüz yok)."
    ),
}


def _num(value: Decimal | None) -> float | None:
    """Decimal -> float (JSON'a gömülecek, JS tarafında SAYISAL sıralama
    için gerekli -- spec'in JSON şeması ham sayı gösterir, string DEĞİL,
    bkz. modül docstring'i)."""
    return float(value) if value is not None else None


def _iso(dt: datetime | None) -> str | None:
    """Timezone-naive UTC datetime'ı ISO8601 + 'Z' son ekiyle string'e
    çevirir -- spec'in JSON şeması örnekleri BÖYLE gösteriyor (bkz.
    "generated_at": "2026-08-12T14:03:00Z")."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _tr_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def _mercek_data_coverage(row: MarketScanResult, key: str) -> Decimal | None:
    return getattr(row, f"{key}_coverage_pct")


def _has_snapshot(row: MarketScanResult) -> bool:
    """Bu satırın (scan_status'tan BAĞIMSIZ olarak) gösterilecek bir skor
    anlık görüntüsü var mı -- spec §Kenar durumlar "scan_status=hata sonrası
    eski skor KORUNUR": `upsert_market_scan_result` `scan_status="hata"` VE
    satır zaten VARSA skor alanlarını EZMEZ, bu yüzden "hata" durumundaki
    bir satır bile ESKİ, GERÇEK bir skor taşıyor olabilir -- dashboard bunu
    "sessizce boş" göstermek yerine (Kural 3) en son BİLİNEN gerçek değerle
    gösterir."""
    return row.bilesik_score is not None or row.deger_score is not None or row.kalite_score is not None


def _mercek_block(row: MarketScanResult, key: str) -> dict[str, Any] | None:
    score = getattr(row, f"{key}_score")
    badge = getattr(row, f"{key}_badge")
    coverage = _mercek_data_coverage(row, key)
    if score is None and badge is None:
        return None
    dusuk_kapsam = coverage is not None and coverage < LOW_COVERAGE_THRESHOLD_PCT
    return {
        "score": _num(score),
        "score_display": format_number_tr(score, decimals=1) if score is not None else "N/A",
        "badge": badge,
        "badge_class": _BADGE_CLASS.get(badge or "", "yetersiz"),
        "data_coverage_pct": _num(coverage),
        "data_coverage_pct_display": format_percent_tr(coverage, decimals=0) if coverage is not None else "—",
        "dusuk_kapsam": dusuk_kapsam,
    }


def _carpanlar_block(row: MarketScanResult) -> dict[str, Any] | None:
    if row.current_price is None and row.market_cap is None and row.pe_ratio is None:
        return None
    symbol = "₺" if row.currency == "TRY" else ("$" if row.currency == "USD" else "")
    return {
        "price": _num(row.current_price),
        "price_display": f"{format_number_tr(row.current_price, decimals=2)} {symbol}".strip() if row.current_price is not None else "—",
        "market_cap": _num(row.market_cap),
        "market_cap_display": format_currency_short(row.market_cap, symbol=symbol) if row.market_cap is not None else "—",
        "pe_ratio": _num(row.pe_ratio),
        "pe_ratio_display": format_number_tr(row.pe_ratio, decimals=1) if row.pe_ratio is not None else "N/A",
        "pb_ratio": _num(row.pb_ratio),
        "pb_ratio_display": format_number_tr(row.pb_ratio, decimals=2) if row.pb_ratio is not None else "N/A",
        "ev_ebitda": _num(row.ev_ebitda),
        "ev_ebitda_display": format_number_tr(row.ev_ebitda, decimals=1) if row.ev_ebitda is not None else "N/A",
        "currency": row.currency,
    }


def _veri_uyarilari(row: MarketScanResult, has_snapshot: bool) -> list[dict[str, str]]:
    """spec §Veri eksikliği görünürlüğü + §Kenar durumlar (GYO notu,
    "desteklenmiyor" notu, "hata sonrası bayat skor" notu) -- BİREBİR."""
    uyarilar: list[dict[str, str]] = []

    if row.scan_status == "desteklenmiyor":
        uyarilar.append({
            "tur": "desteklenmiyor",
            "aciklama": row.error_detail or (
                "Bu şirket türü/finansal grup şu an desteklenen 5 şablonun "
                "(sanayi/abd_sanayi/banka/sigorta/finansman) dışında -- henüz skorlanamadı."
            ),
        })
        return uyarilar  # spec örneği: veri_yok/desteklenmiyor satırlarında sistemik tablo eklenmez (skor zaten yok)

    if row.scan_status == "veri_yok":
        return []  # spec'in "Hatalı/desteklenmeyen satır örneği" -- veri_uyarilari: []

    if row.scan_status == "hata" and has_snapshot:
        uyarilar.append({
            "tur": "hata_bayat",
            "aciklama": f"Son taramada geçici bir hata oluştu -- gösterilen skor {_tr_datetime(row.computed_at)} tarihli önceki başarılı taramaya ait.",
        })
    elif row.scan_status == "hata" and not has_snapshot:
        return []

    # "ok" (ve skoru korunmuş "hata") satırları -- piyasa-geneli sistemik tablo + GYO notu.
    uyarilar.extend(PIYASA_SISTEMIK_EKSIK_BILESENLER.get(row.market, []))
    if row.sirket_turu == "gyo":
        uyarilar.append(GYO_UYARI_NOTU)
    return uyarilar


def _serialize_row(row: MarketScanResult) -> dict[str, Any]:
    has_snapshot = _has_snapshot(row)
    mercekler = None
    bilesik = None
    carpanlar = None
    dusuk_kapsam_var = False

    if has_snapshot:
        mercekler = {}
        for key, label in _MERCEK_ANAHTAR_ETIKET:
            block = _mercek_block(row, key)
            mercekler[label] = block
            if block is not None and block["dusuk_kapsam"]:
                dusuk_kapsam_var = True
        bilesik = {
            "score": _num(row.bilesik_score),
            "score_display": format_number_tr(row.bilesik_score, decimals=1) if row.bilesik_score is not None else "N/A",
            "badge": row.bilesik_badge,
            "badge_class": _BADGE_CLASS.get(row.bilesik_badge or "", "yetersiz"),
            "data_coverage_pct": _num(row.bilesik_data_coverage_pct),
            "data_coverage_pct_display": (
                format_percent_tr(row.bilesik_data_coverage_pct, decimals=0)
                if row.bilesik_data_coverage_pct is not None else "—"
            ),
            "dahil_edilen_mercekler": row.dahil_edilen_mercekler or [],
        }
        carpanlar = _carpanlar_block(row)

    return {
        "ticker": row.ticker,
        "company_name": row.company_name or row.ticker,
        "market": row.market,
        "ust_sektor": row.ust_sektor,
        "sirket_turu": row.sirket_turu,
        "sirket_turu_display": _SIRKET_TURU_DISPLAY.get(row.sirket_turu, row.sirket_turu or "—"),
        "template": row.template,
        "period": [row.year, row.period] if row.year is not None and row.period is not None else None,
        "period_display": f"{row.year}/{row.period}" if row.year is not None and row.period is not None else "—",
        "scan_status": row.scan_status,
        "computed_at": _iso(row.computed_at),
        "computed_at_display": _tr_datetime(row.computed_at),
        "mercekler": mercekler,
        "bilesik": bilesik,
        "carpanlar": carpanlar,
        "dusuk_kapsam_var": dusuk_kapsam_var,
        "veri_uyarilari": _veri_uyarilari(row, has_snapshot),
    }


def _sector_sort_key(ust_sektor: str) -> tuple[int, str]:
    # "Sınıflandırılmamış" sözde-grubu HER ZAMAN en sonda (spec: karşılaştırma
    # amaçlı bir grup değil, sadece toplama kutusu) -- geri kalanı alfabetik.
    if ust_sektor == "Sınıflandırılmamış":
        return (1, ust_sektor)
    return (0, ust_sektor)


def _company_sort_key(company: dict[str, Any]) -> tuple[int, float, str]:
    # Varsayılan sıralama: bileşik skor YÜKSEKTEN DÜŞÜĞE (skoru olmayanlar
    # en sona) -- istemci-içi JS tablo BUNU her sütuna göre DEĞİŞTİREBİLİR,
    # bu SADECE ilk-yükleme sırasıdır (saf sunum kararı, hesaplama DEĞİL).
    bilesik = company["bilesik"]
    score = bilesik["score"] if bilesik is not None else None
    return (0, -score, company["ticker"]) if score is not None else (1, 0.0, company["ticker"])


def _build_sectors(market_rows: list[MarketScanResult]) -> list[dict[str, Any]]:
    gruplar: dict[str, list[MarketScanResult]] = {}
    for row in market_rows:
        anahtar = row.ust_sektor or "Sınıflandırılmamış"
        gruplar.setdefault(anahtar, []).append(row)

    sonuc = []
    for ust_sektor in sorted(gruplar, key=_sector_sort_key):
        rows = gruplar[ust_sektor]
        n = len(rows)
        yetersiz_ornek: bool | None
        if ust_sektor == "Sınıflandırılmamış":
            yetersiz_ornek = None
        else:
            yetersiz_ornek = n < MIN_SECTOR_N
        kirilim = Counter((_SIRKET_TURU_DISPLAY[r.sirket_turu] if r.sirket_turu in _SIRKET_TURU_DISPLAY and r.sirket_turu else "bilinmiyor") for r in rows)
        companies = sorted((_serialize_row(r) for r in rows), key=_company_sort_key)
        sonuc.append({
            "ust_sektor": ust_sektor,
            "sirket_turu_kirilimi": dict(kirilim),
            "n": n,
            "min_sector_n": MIN_SECTOR_N,
            "yetersiz_ornek": yetersiz_ornek,
            "companies": companies,
        })
    return sonuc


def _badge_dagilimi(market_rows: list[MarketScanResult]) -> dict[str, int]:
    """Piyasa-geneli rozet dağılımı -- dashboard'un kahraman (3 saniyede
    okunur) özet şeridi için saf sayım (skor HESAPLAMAZ, sadece VAR OLAN
    `bilesik_badge` alanlarını sayar)."""
    sayim = Counter(r.bilesik_badge for r in market_rows if r.bilesik_badge is not None)
    return dict(sayim)


def build_dashboard_data(session: Session, *, now: datetime | None = None) -> dict[str, Any]:
    """`MarketScanResult` satırlarını spec §"Dashboard'a gömülecek JSON
    şeması"na birebir uyan bir dict'e çevirir. SAF okuma+gruplama+biçimlendirme
    -- hiçbir skor/çarpan burada YENİDEN HESAPLANMAZ (quaxis-mimari anayasa)."""
    now = now or utcnow_naive()
    rows = repository.get_market_scan_results(session)

    bist_rows = [r for r in rows if r.market == "BIST"]
    nasdaq_rows = [r for r in rows if r.market == "NASDAQ"]

    bist_last_scan_at = min((r.computed_at for r in bist_rows), default=None)
    nasdaq_last_scan_at = min((r.computed_at for r in nasdaq_rows), default=None)

    return {
        "methodology": SCORE_METHODOLOGY,
        "meta": {
            "generated_at": _iso(now),
            "generated_at_display": _tr_datetime(now),
            "bist_last_scan_at": _iso(bist_last_scan_at),
            "bist_last_scan_at_display": _tr_datetime(bist_last_scan_at),
            "nasdaq_last_scan_at": _iso(nasdaq_last_scan_at),
            "nasdaq_last_scan_at_display": _tr_datetime(nasdaq_last_scan_at),
            # spec'in AÇIKÇA izin verdiği durum ("kodlama fazına kadar null
            # kabul edilebilir") -- KESİN sayı SADECE `tarama_toplu.py
            # --market nasdaq --dry-run` ile ölçülüp bir SONRAKİ üretimde
            # buraya taşınabilir (spec §NASDAQ "tam evren" kapsamı). Render
            # katmanı bu filtre sorgusunu kendisi TEKRAR üretip "hesaplama"
            # YAPMAZ (quaxis-mimari: filtre mantığı repository/tarama_toplu.py
            # katmanına aittir, burada DUPLICATE edilmez).
            "bist_company_count": len(bist_rows),
            "nasdaq_company_count": len(nasdaq_rows),
            "nasdaq_universe_total": None,
        },
        "markets": {
            "BIST": {
                "badge_dagilimi": _badge_dagilimi(bist_rows),
                "sistemik_uyarilar": PIYASA_SISTEMIK_EKSIK_BILESENLER.get("BIST", []),
                "sectors": _build_sectors(bist_rows),
            },
            "NASDAQ": {
                "badge_dagilimi": _badge_dagilimi(nasdaq_rows),
                "sistemik_uyarilar": PIYASA_SISTEMIK_EKSIK_BILESENLER.get("NASDAQ", []),
                "sectors": _build_sectors(nasdaq_rows),
            },
        },
    }


def _json_default(obj: Any) -> Any:
    """`json.dumps` güvencesi -- `build_dashboard_data()` normalde TÜM
    Decimal'leri `_num()` ile önceden float'a çevirir, ama ileride EKLENECEK
    yeni bir alan yanlışlıkla Decimal/datetime bırakırsa sessizce
    TypeError yerine güvenli bir dize/sayıya döner (savunma amaçlı)."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def render_dashboard_html(data: dict[str, Any], template_name: str = "dashboard.html") -> str:
    """`data`'dan (build_dashboard_data() çıktısı) tek-dosyalık HTML üretir --
    Playwright OLMADAN da test edilebilsin diye render_dashboard_html/
    build_and_write_dashboard AYRI tutuldu (src/render/card.py::render_html
    ile AYNI desen). Dashboard PNG DEĞİLDİR -- tarayıcıda açılır, bu yüzden
    burada Playwright/screenshot YOK.

    `data` AYRICA ham JSON olarak `<script id="dashboard-data">` içine
    gömülür (spec: "içine JSON gömülü") -- `</` dizisi kaçırılır ki gömülü
    JSON içinde (örn. bir açıklama metninde) yanlışlıkla `</script>`
    üretip HTML'i BOZMASIN (standart, belgelenmiş bir güvenlik/doğruluk
    önlemi)."""
    template = _env.get_template(template_name)
    data_json = json.dumps(data, ensure_ascii=False, default=_json_default).replace("</", "<\\/")
    return template.render(data=data, data_json=data_json)


def build_and_write_dashboard(
    output_path: str | Path | None = None,
    *,
    session: Session | None = None,
) -> str:
    """`/piyasa` komutunun (Faz 6/sonraki adım, BU MODÜLÜN KAPSAMI DIŞINDA)
    bağlanacağı TEK giriş noktası -- spec §"/piyasa komutu": "SADECE mevcut
    MarketScanResult anlık görüntüsünden dashboard.html'i YENİDEN ÜRETİR,
    ağa GİTMEZ" ilkesiyle BİREBİR uyumlu: bu fonksiyon DA hiçbir fetcher/
    `compute_multi_lens_score_for_ticker` çağrısı YAPMAZ, SADECE DB okur.

    `session` verilmezse `repository.get_session()` ile varsayılan (üretim)
    veritabanına kısa ömürlü bir session açılır (testler kendi izole
    session'larını GEÇİRİR). Üretilen dosyanın yolunu (str) döner."""
    out_path = Path(output_path) if output_path is not None else _DEFAULT_OUTPUT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if session is not None:
        data = build_dashboard_data(session)
    else:
        with repository.get_session() as owned_session:
            data = build_dashboard_data(owned_session)

    html = render_dashboard_html(data)
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    yol = build_and_write_dashboard()
    print(f"Dashboard üretildi: {yol}")
