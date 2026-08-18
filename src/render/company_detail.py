"""Kullanıcı isteği (2026-08-12): dashboard.html'deki her satıra tıklanınca
açılan, TEK bir şirkete özel detay sayfası -- `src/render/dashboard.py` ile
BİREBİR AYNI iki-aşamalı desen (quaxis-mimari anayasa: render katmanı
HİÇBİR skor/formül YENİDEN HESAPLAMAZ, sadece var olan veriyi okur+biçimlendirir):

    1. build_company_detail_data(session, ticker, market) -- `MarketScanResult`
       satırını (mercekler_detay JSON blob'u DAHİL -- bkz. scripts/tarama_toplu.py
       ::_mercekler_detay/_component_to_dict, ZATEN o hissenin KENDİ değerleriyle
       üretilmiş `reasoning_tr` metinleri taşıyor) + `repository.get_financials()`
       çok-dönemli ham finansal veriyi bir dict'e çevirir.
    2. render_company_detail_html(data) -- Jinja2 ile tek-dosyalık, harici
       kaynak İÇERMEYEN HTML üretir (`_design_tokens.css` dashboard.html/card.html
       ile AYNI kaynaktan include edilir -- görsel kimlik tutarlılığı).

Dosya adı deseni: `output/detay/{market}_{ticker}.html` (bkz. detail_relative_path/
detail_output_path) -- dashboard.py bu İKİ yardımcıyı import ederek `detail_url`
alanını doldurur (TEK kaynak, path mantığı iki yerde TEKRARLANMAZ).

Finansal tablo özeti (Görev 1 madde 4) İSTİSNAİ bir durum gibi görünebilir:
`repository.get_financials()` HAM item_code->value sözlüğü döner, ama bu
item_code'lar `src/bot/pipeline.py::_standardize_to_records*()` tarafından
ZATEN "revenue"/"net_income"/"equity" gibi STANDART alan adlarına çevrilerek
yazılmıştır (bkz. o modülün üst notu + `compute_multi_lens_score_for_ticker()`
içindeki `financials_by_period = repository.get_financials(...)` çağrısının
DOĞRUDAN `calculator.analyze()`'a verilmesi) -- yani bu modülün DB'den okuyup
`calculator.analyze()`/`analyze_bank()`/`analyze_insurance()`/`analyze_financing()`/
`analyze_us()` çağırması YENİ bir hesaplama İCAT ETMEZ, pipeline.py'nin
ZATEN yaptığı AYNI saf-matematik dönüşümü (I/O'suz, `calculator.py` modül
docstring'i: "HİÇBİR LLM çağrısı yoktur ve src.fetchers/src.db import ETMEZ")
tekrar çağırır -- görevin kendi talimatı da BUNU açıkça istiyor ("calculator.py'nin
zaten hesapladığı alanlardan ... mevcut alanları TABLOLA").
"""

from __future__ import annotations

import csv
import dataclasses
import functools
import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import jinja2
from sqlalchemy.orm import Session

import config
from src.ai.kar_kaynagi import KarKaynagiBulgulari
from src.analysis import calculator
from src.db import repository
from src.db.models import Company, MarketScanResult, utcnow_naive
from src.fetchers.kap import ekosistem_etiketi_for_ticker
from src.formatting import format_currency_short, format_number_tr, format_percent_tr
from src.render.render_common import mercek_bilesen_sayimi, mercek_score_display

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_TEMPLATE_DIR),
    autoescape=jinja2.select_autoescape(["html"]),
)

# src/render/dashboard.py::_BADGE_CLASS/_SIRKET_TURU_DISPLAY ile BİREBİR AYNI
# eşlemeler -- görsel kimlik tutarlılığı (bkz. o modülün üst notu). Burada
# KOPYALANIR (import EDİLMEZ) -- dashboard.py'nin alanları alt çizgiyle
# başlayan modül-içi sabitlerdir, card.py'deki build_bank/us/insurance
# context fonksiyonlarının da birbirinden bağımsız kendi küçük eşlemelerini
# tuttuğu desenle TUTARLI (proje kuralı: paralel context inşacılar arası
# ince eşlemeler ayrı tutulur, ORTAK olan sadece _line_item_row gibi gerçek
# hesaplama/formatlama mantığıdır -- burada YOK, sadece sabit sözlük).
_BADGE_CLASS: dict[str, str] = {
    "SAĞLAM": "saglam",
    "DENGELİ": "dengeli",
    "KARIŞIK": "karisik",
    "RİSKLİ": "riskli",
    "YETERSİZ VERİ": "yetersiz",
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

# (MarketScanResult sütun öneki [ASCII], mercekler_detay/label sözlük anahtarı
# [Türkçe glif], görüntü etiketi) -- src/render/dashboard.py::_MERCEK_ANAHTAR_ETIKET
# İLE AYNI ayrım gereksinimi: SQLAlchemy sütun adları ASCII ("deger_score"),
# ama mercekler_detay JSON'u VE görüntü etiketleri Türkçe glif kullanır
# ("değer") -- ikisi KARIŞTIRILIRSA getattr() AttributeError fırlatır.
_MERCEK_ANAHTAR_ETIKET: tuple[tuple[str, str, str], ...] = (
    ("deger", "değer", "Değer"),
    ("kalite", "kalite", "Kalite"),
    ("buyume", "büyüme", "Büyüme"),
    ("guvenlik", "güvenlik", "Güvenlik"),
)

# quarterly_series alan adlarından bazıları (banka: net_interest_income)
# calculator.FIELD_LABELS_TR içinde YOK (o sözlük SADECE income_statement/
# balance_sheet alanlarını kapsıyor, bkz. calculator.py card.py._build_chart
# çağrılarındaki "Net Faiz Geliri" başlığıyla AYNI, elle kopyalanan tek
# etiket) -- geri kalan tüm quarterly_series alanları (revenue/ebitda/
# net_income/loans/financing_revenue/gross_written_premiums/technical_balance)
# zaten FIELD_LABELS_TR'de VAR, burada TEKRARLANMAZ.
_QUARTERLY_FIELD_LABEL_FALLBACK: dict[str, str] = {
    "net_interest_income": "Net Faiz Geliri",
}

# Kullanıcı isteği (2026-08-12, ikinci tur): "o puanı nasıl bulduk" -- her
# bileşenin `reasoning_tr`'si ZATEN o hissenin KENDİ sayılarıyla üretilmiş
# bir cümledir (örn. "F/K sektör medyanından %12 sapıyor"), ama bunun
# HANGİ genel FORMÜLDEN geldiğini (şirketten BAĞIMSIZ, soyut) AYRICA
# göstermek istendi. Bu sözlük `src/analysis/lens_{deger,kalite,buyume,
# guvenlik}.py`'deki bileşen adı sabitleriyle (tuple'ların İLK elemanı)
# BİREBİR eşleşir -- yeni bir bileşen eklenirse (bkz. İlk Dalga çalışması)
# burada da bir satır eklenmesi gerekir, aksi halde o bileşen "—" formül
# göstermez (sessizce KAYBOLMAZ, sadece boş kalır -- Kural 3).
FORMUL_LOOKUP: dict[str, str] = {
    # --- Değer ---
    "Mutlak Ucuzluk (F/K + PD/DD)": "F/K = Piyasa Değeri / Net Kâr (TTM) · PD/DD = Piyasa Değeri / Özkaynak -- ikisi sektöre özgü ucuz/makul/pahalı bantlarına göre puanlanıp ortalanır.",
    "Sektöre Göreli Konum": "z-skoru = (Şirketin F/K veya PD/DD − Sektör Medyanı) / (1,4826 × Sektör MAD) -- sektör medyanına göre robust (aykırı-değer dayanıklı) sapma.",
    "Kazanç Getirisi vs Risksiz Oran": "Kazanç Getirisi (E/P) = 100 / F-K · Fark = Kazanç Getirisi − Risksiz Faiz Oranı.",
    "Graham Çarpanı (F/K×PD/DD)": "Graham Çarpanı = F/K × PD/DD (≤22,5 klasik eşiğiyle karşılaştırılır).",
    "Greenblatt Kazanç Getirisi (EBIT/FD)": "Kazanç Getirisi = EBIT / Firma (Kurumsal) Değeri × 100.",
    "Carlisle Acquirer's Multiple (FD/EBIT)": "Çarpan = Firma (Kurumsal) Değeri / EBIT.",
    "NCAV / Net-Net Bonus": "Net İşletme Sermayesi = Dönen Varlıklar − Toplam Yükümlülükler; Piyasa Değeri bu tutarın ALTINDAysa bonus puan verilir.",
    # --- Kalite ---
    "Nakit Üretimi (FAVÖK marjı)": "FAVÖK Marjı = FAVÖK / Toplam Hasılat × 100.",
    "Özkaynak Kârlılığı (ROE)": "ROE = Net Kâr (TTM) / Özkaynak × 100.",
    "Kârlılık (Net Marj)": "Net Marj = Net Kâr / Toplam Hasılat × 100.",
    "Brüt Kâr Marjı": "Brüt Kâr Marjı = Brüt Kâr / Toplam Hasılat × 100 (seviye + çok dönemli trend birlikte değerlendirilir).",
    "Greenblatt Sermaye Getirisi (ROC)": "ROC = EBIT / (Net Çalışma Sermayesi + Maddi Duran Varlıklar) × 100.",
    "Aktif Kârlılığı (ROA)": "ROA = Net Kâr (TTM) / Toplam Varlıklar × 100.",
    "Nakit Kâr Kalitesi (OCF/Net Kâr)": "Oran = Faaliyetlerden Nakit Akışı (OCF) / Net Kâr -- 1,0'a yakın/üzeri kazancın nakitle desteklendiğini gösterir.",
    # --- Büyüme ---
    "Hasılat Büyümesi (reel, seviye+trend)": "Reel Büyüme (%) = Nominal Yıllık (YoY) Hasılat Büyümesi − Enflasyon Oranı (seviye + çok dönemli trend birlikte).",
    "PEG Oranı (Lynch)": "PEG = F/K / Yıllık Kazanç Büyüme Oranı (%).",
    "Marjinal ROE + Verimlilik Kaynaklı Büyüme": "Marjinal ROE = ΔNet Kâr / Önceki Dönem Özkaynağı; Fark = Marjinal ROE − Standart ROE.",
    # --- Güvenlik ---
    "Kaldıraç (Net Borç/FAVÖK)": "Net Borç / FAVÖK = (Toplam Finansal Borç − Nakit ve Benzerleri) / FAVÖK.",
    "Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)": "Cari Oran = Dönen Varlıklar / Kısa Vadeli Yükümlülükler · Özkaynak/Varlık = Özkaynak / Toplam Varlıklar × 100.",
    "Piotroski F-Skoru": "9 ikili (0/1) finansal sağlık kriterinin toplamı / hesaplanabilen kriter sayısı (Piotroski, 2000).",
    "Toplam Yükümlülük/Özkaynak (geniş tanım)": "Toplam Yükümlülükler (ticari borç + tahakkuk + ertelenmiş vergi DAHİL) / Özkaynak.",
    "Merton Temerrüt Olasılığı (EDF)": "Black-Scholes/Merton opsiyon modeli: özkaynak = Firma Değeri üzerine bir alım opsiyonu -- çıkan N(d2)'den temerrüt olasılığı [1−N(d2)] türetilir.",
    "Özkaynak/Aktif Oranı (sermaye yeterliliği proxy'si)": "Özkaynak / Toplam Varlıklar × 100 (banka/sigorta/finansman için basitleştirilmiş sermaye yeterliliği göstergesi).",
    "Piotroski Benzeri Finansal Sağlık Taraması": "Banka/sigorta/finansman için uyarlanmış, basitleştirilmiş ikili (0/1) kriter seti (Piotroski (2000) yönteminin bu şablonlara uyarlanmış hali).",
}


FAALIYET_RAPORU_PLACEHOLDER = (
    "Bu bölüm henüz araştırılmadı -- gelecek bir fazda faaliyet raporu/dipnot "
    "analizinden doldurulacak. Şu an burada gösterilecek gerçek bir bulgu yok."
)

# docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu (2026-08-12):
# `KarKaynagiBulgulari.source` -> kullanıcıya gösterilecek dürüst kaynak
# etiketi (Kural 2: "LLM asla sayı üretmez" ilkesiyle AYNI ruhla, bu bölümün
# bir SKOR değil METİN ANALİZİ olduğu HER ZAMAN açıkça belirtilir).
_FAALIYET_RAPORU_KAYNAK_ETIKET: dict[str, str] = {
    "llm": "Gemini ile faaliyet raporu metninden çıkarılmış nitel bulgu (skor DEĞİLDİR)",
    "fallback": "Otomatik metin analizi şu an kullanılamıyor -- kural tabanlı yedek not",
}


def detail_relative_path(ticker: str, market: str) -> str:
    """`output/` klasörüne göre RELATİF yol (dashboard.html'in `<a href>`
    değeri için) -- `detail_output_path()` ile TEK kaynak, iki yerde
    (dashboard.py + company_detail.py) yol mantığı TEKRARLANMASIN diye."""
    return f"detay/{market}_{ticker}.html"


def detail_output_path(ticker: str, market: str) -> Path:
    return config.BASE_DIR / "output" / detail_relative_path(ticker, market)


def _num(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _tr_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def _decimal_or_none(value: str | None) -> Decimal | None:
    """`mercekler_detay` JSON'undaki sayısal alanlar `str()` olarak
    saklanmıştı (bkz. scripts/tarama_toplu.py::_component_to_dict --
    SQLite JSON sütunu Decimal'i SERİLEŞTİREMEZ) -- burada geri Decimal'e
    çevrilir ki `src.formatting` yardımcıları normal şekilde çalışsın."""
    if value is None:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _mercek_summary(row: MarketScanResult, prefix: str, detay_key: str, label: str) -> dict[str, Any] | None:
    score = getattr(row, f"{prefix}_score")
    badge = getattr(row, f"{prefix}_badge")
    coverage = getattr(row, f"{prefix}_coverage_pct")
    if score is None and badge is None:
        return None
    # DÜZELTME (kullanıcı denetimi, 2026-08-12 -- AYES: kapsam %25, badge
    # zaten "YETERSİZ VERİ" ama skor hâlâ "9,2" olarak GÖSTERİLİYORDU --
    # ilk yama commit c5c8499 skoru TAMAMEN "N/A" yapmıştı).
    # docs/spec/spec_kapsam_cezali_skor.md §3/§4 ile bu davranış GÜNCELLENDİ
    # (dashboard.py::_mercek_block ile AYNI, ORTAK `render_common.
    # mercek_score_display` üzerinden): badge YETERSİZ VERİ VE 0<kapsam<%50
    # ise artık TAMAMEN N/A DEĞİL, nominal ağırlıklı/eksik=sıfır kapsam-
    # cezalı skor (S′=S×kapsam/100) gösterilir -- kapsam=%0 (veya score/
    # coverage None) durumunda "N/A" AYNEN kalır (Kural 3: "veri yok" ile
    # "şirket kötü" KARIŞTIRILMASIN).
    n_mevcut, n_toplam = mercek_bilesen_sayimi(row.mercekler_detay, detay_key)
    _score_value, score_display, kapsam_notu = mercek_score_display(
        score, badge, coverage, mercek_label=label, n_mevcut=n_mevcut, n_toplam=n_toplam,
    )
    return {
        "score_display": score_display,
        "kapsam_notu": kapsam_notu,
        "badge": badge,
        "badge_class": _BADGE_CLASS.get(badge or "", "yetersiz"),
        "data_coverage_pct_display": format_percent_tr(coverage, decimals=0) if coverage is not None else "—",
    }


def _mercek_components(row: MarketScanResult, key: str) -> list[dict[str, str]]:
    """`mercekler_detay[key]`'deki HER bileşeni (skor/ağırlık/katkı/hazır
    Türkçe gerekçe) tabloya hazır string'lere çevirir. Bu, kullanıcının
    "hangi formülle, hisseye özgü hangi değerle hesaplandı" sorusunun
    doğrudan cevabıdır -- `reasoning_tr` ZATEN o hissenin kendi verileriyle
    scorer.py tarafından üretilmiş bir cümledir, burada SADECE taşınır."""
    detay = row.mercekler_detay or {}
    bilesenler = detay.get(key, [])
    rows = []
    for b in bilesenler:
        score = _decimal_or_none(b.get("score"))
        weight_nominal = _decimal_or_none(b.get("weight_nominal"))
        weight_effective = _decimal_or_none(b.get("weight_effective"))
        contribution = _decimal_or_none(b.get("contribution"))
        name = b.get("name", "—")
        rows.append({
            "name": name,
            "formula": FORMUL_LOOKUP.get(name, "—"),
            "score_display": f"{format_number_tr(score, decimals=1)}/10" if score is not None else "N/A",
            "weight_nominal_display": f"%{format_number_tr(weight_nominal, decimals=0)}" if weight_nominal is not None else "—",
            "weight_effective_display": f"%{format_number_tr(weight_effective, decimals=1)}" if weight_effective is not None else "—",
            "contribution_display": format_number_tr(contribution, decimals=2) if contribution is not None else "N/A",
            "reasoning_tr": b.get("reasoning_tr") or "—",
            "veri_eksik": score is None,
        })
    return rows


def _skor_hucre(score: Decimal | None, badge: str | None) -> dict[str, str]:
    return {
        "display": format_number_tr(score, decimals=1) if score is not None else "N/A",
        "badge_class": _BADGE_CLASS.get(badge or "", "yetersiz"),
    }


def _skor_gecmisi_block(row: MarketScanResult) -> list[dict[str, Any]]:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Skor Geçmişi (2026-08-12):
    `row.tarihsel_skorlar` (bkz. scripts/tarama_toplu.py::
    _tarihsel_skorlar_to_list, ESKİDEN YENİYE sıralı JSON) çıktısını tabloya
    hazır satırlara çevirir -- Decimal alanlar `_decimal_or_none` (bu
    modülde ZATEN `mercekler_detay` için kullanılan AYNI yardımcı) ile geri
    çevrilip `format_number_tr` ile Türkçe biçimlendirilir (Kural 4: şablon
    HİÇBİR hesaplama yapmaz, sadece hazır string basar). Sütun YOKSA/henüz
    hiç tarama yapılmadıysa (eski satır, migration ÖNCESİ) boş liste döner
    -- şablon bu durumda dürüst bir "henüz veri yok" notu gösterir."""
    if not row.tarihsel_skorlar:
        return []
    rows: list[dict[str, Any]] = []
    for s in row.tarihsel_skorlar:
        rows.append({
            "donem_label": s.get("donem_label") or s.get("donem") or "—",
            "deger": _skor_hucre(_decimal_or_none(s.get("deger_score")), s.get("deger_badge")),
            "kalite": _skor_hucre(_decimal_or_none(s.get("kalite_score")), s.get("kalite_badge")),
            "buyume": _skor_hucre(_decimal_or_none(s.get("buyume_score")), s.get("buyume_badge")),
            "guvenlik": _skor_hucre(_decimal_or_none(s.get("guvenlik_score")), s.get("guvenlik_badge")),
            "bilesik": _skor_hucre(_decimal_or_none(s.get("bilesik_score")), s.get("bilesik_badge")),
        })
    return rows


# Kullanıcı isteği (2026-08-13, ikinci tur): kullanıcı Fintables'ın
# TEK-metrik, TEK-renk küçük grafik kartlarını referans gösterdi ("bu
# şekilde yapmak istiyorum") -- 5 SERİyi TEK grafikte üst üste bindiren
# ilk tasarım BEĞENİLMEDİ. Bu, ilkinin YERİNE her mercek/Bileşik için
# AYRI bir küçük grafik kartı üretir (`kart-tasarim-sistemi` skill:
# şablon hesaplama YAPMAZ, koordinatlar burada Python'da üretilir).
# Renk: 5 ayrı seri kimliği ARTIK gerekmiyor (her kart TEK seri) --
# Fintables referansındaki gibi TEK marka rengi (`--brand-gold`,
# sayfanın kimlik vurgusuyla AYNI) tüm kartlarda tutarlı kullanılır.
# İnteraktif imleç/tooltip (kullanıcının ekran görüntüsündeki davranış)
# `company_detail.html`'in altındaki TEK, statik/vanilla JS bloğuyla
# sağlanır (kart-tasarim-sistemi skill §Dashboard: "dashboard PNG
# değil, tarayıcıda açılır, vanilla JS serbest" -- bu sayfa da AYNI
# ilkeye tabi, Playwright/PNG kartlarından FARKLI); JS SADECE piksel
# pozisyonu okuyup ÖNCEDEN Python'da hazırlanmış (`data-points` JSON)
# metin/değerleri gösterir, HİÇBİR skor/format HESAPLAMAZ.
_METRIC_CHART_FIELDS: tuple[tuple[str, str], ...] = (
    ("deger_score", "Değer"),
    ("kalite_score", "Kalite"),
    ("buyume_score", "Büyüme"),
    ("guvenlik_score", "Güvenlik"),
    ("bilesik_score", "Bileşik"),
)

_MCHART_W = 600
_MCHART_H = 230
_MCHART_PAD_L = 34
_MCHART_PAD_R = 14
_MCHART_PAD_T = 16
_MCHART_PAD_B = 44  # Fintables referansındaki gibi 45° döndürülmüş dönem etiketleri için


def _json_compact(obj: Any) -> str:
    """JS'in `data-points` attribute'ünden okuyacağı JSON -- HTML
    attribute'u TEK tırnakla sarıldığı için (`data-points='...'`) içindeki
    olası tek tırnaklar (Türkçe metinde YOK ama savunmacı) HTML entity'e
    çevrilir; JSON'un KENDİSİ çift tırnak kullandığı için bu ikisi
    ÇAKIŞMAZ."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("'", "&#39;")


def _mchart_x(i: int, n: int) -> float:
    usable = _MCHART_W - _MCHART_PAD_L - _MCHART_PAD_R
    if n <= 1:
        return _MCHART_PAD_L + usable / 2
    return _MCHART_PAD_L + usable * i / (n - 1)


def _mchart_y(score: Decimal) -> float:
    usable = _MCHART_H - _MCHART_PAD_T - _MCHART_PAD_B
    frac = max(Decimal("0"), min(Decimal("10"), score)) / Decimal("10")
    return _MCHART_H - _MCHART_PAD_B - float(frac) * usable


def _aggregate_annual(tarihsel_skorlar: list[dict]) -> list[dict]:
    """Kullanıcı isteği (2026-08-13, üçüncü tur): "3 aylık" (mevcut, ham
    dönem) yanında bir de "yıllık" görünüm istendi. YENİ bir hesaplama/
    fetch YAPILMAZ -- ZATEN var olan çeyreklik anlık görüntüler (`donem`
    alanının "YIL/AY" biçimindeki YIL kısmına göre) gruplanıp HER alan
    için (4 mercek + Bileşik + price) o yıldaki MEVCUT (None olmayan)
    değerlerin ortalaması alınır. Çıktı, `tarihsel_skorlar` ile AYNI
    sözlük şeklini taşır (`donem`/`donem_label`=yıl, alanlar str-Decimal)
    ki `_skor_gecmisi_chart_for_rows` İKİ girdi türünü de (çeyreklik/
    yıllık) AYNI kod yoluyla işleyebilsin (kod tekrarı YOK)."""
    by_year: dict[str, list[dict]] = {}
    for s in tarihsel_skorlar:
        donem = s.get("donem") or ""
        year = donem.split("/")[0] if "/" in donem else (s.get("donem_label") or "?")
        by_year.setdefault(year, []).append(s)

    fields = ("deger_score", "kalite_score", "buyume_score", "guvenlik_score", "bilesik_score", "price")
    result: list[dict] = []
    for year in sorted(by_year.keys()):
        rows = by_year[year]
        agg: dict[str, Any] = {"donem": year, "donem_label": year}
        for f in fields:
            vals = [v for v in (_decimal_or_none(r.get(f)) for r in rows) if v is not None]
            agg[f] = str(sum(vals) / len(vals)) if vals else None
        result.append(agg)
    return result


def _price_norm_y(price: Decimal, pmin: Decimal, pmax: Decimal) -> float:
    usable = _MCHART_H - _MCHART_PAD_T - _MCHART_PAD_B
    frac = Decimal("0.5") if pmax == pmin else (price - pmin) / (pmax - pmin)
    frac = max(Decimal("0"), min(Decimal("1"), frac))
    return _MCHART_H - _MCHART_PAD_B - float(frac) * usable


def _skor_gecmisi_chart_for_rows(
    rows: list[dict], field: str, label: str, ticker: str, currency_symbol: str, css_class: str,
) -> str:
    """Tek bir (dönem-modu × mercek) kombinasyonu için SVG üretir --
    `rows` çeyreklik (`row.tarihsel_skorlar`) VEYA yıllık (`_aggregate_
    annual()` çıktısı) olabilir, fonksiyon İKİSİNE de KÖR çalışır (aynı
    sözlük şekli). Skor çizgisi HER ZAMAN çizilir; fiyat çizgisi (kullanıcı
    isteği: "hisse fiyatı grafiğini ekle/kaldır" butonu) min-max 0-10
    bandına normalize edilip AYRI bir katman olarak eklenir, başlangıçta
    CSS ile GİZLİ (`.mchart-card.show-price` sınıfı JS ile eklenince
    görünür olur, bkz. company_detail.html) -- dataviz skill "tek eksen"
    kuralı: fiyat İKİNCİ bir y-ekseni AÇMAZ, SADECE aynı 0-10 görsel
    bandına indekslenir (gerçek TL/$ değeri nokta başlıklarında/tooltipte
    ayrıca gösterilir)."""
    donemler = [r.get("donem_label") or r.get("donem") or "—" for r in rows]
    n = len(donemler)

    coords: list[tuple[float, float] | None] = []
    points_json: list[dict[str, Any]] = []
    fiyatlar: list[Decimal | None] = []
    for i, r in enumerate(rows):
        score = _decimal_or_none(r.get(field))
        fiyat = _decimal_or_none(r.get("price"))
        fiyatlar.append(fiyat)
        x = _mchart_x(i, n)
        if score is not None:
            y = _mchart_y(score)
            coords.append((x, y))
        else:
            coords.append(None)
            y = None
        points_json.append({
            "x": round(x, 1),
            "y": round(y, 1) if y is not None else None,
            "period": donemler[i],
            "display": format_number_tr(score, decimals=1) if score is not None else None,
            "price_display": f"{format_number_tr(fiyat, decimals=2)} {currency_symbol}".strip() if fiyat is not None else None,
        })

    parts: list[str] = [
        f'<svg viewBox="0 0 {_MCHART_W} {_MCHART_H}" class="metric-chart {css_class}" role="img" '
        f'aria-label="{label} skorunun dönemsel seyri" data-ticker="{ticker}" '
        f'data-points=\'{_json_compact(points_json)}\'>'
    ]

    for g in (0, 2, 4, 6, 8, 10):
        y = _mchart_y(Decimal(g))
        parts.append(
            f'<line x1="{_MCHART_PAD_L}" y1="{y:.1f}" x2="{_MCHART_W - _MCHART_PAD_R}" y2="{y:.1f}" class="mchart-grid"/>'
        )
        parts.append(f'<text x="{_MCHART_PAD_L - 6}" y="{y + 3:.1f}" class="mchart-axis-label" text-anchor="end">{g}</text>')

    for i, plabel in enumerate(donemler):
        x = _mchart_x(i, n)
        parts.append(
            f'<text x="{x:.1f}" y="{_MCHART_H - _MCHART_PAD_B + 14}" class="mchart-axis-label" '
            f'text-anchor="end" transform="rotate(-45 {x:.1f} {_MCHART_H - _MCHART_PAD_B + 14})">{plabel}</text>'
        )

    # --- Fiyat overlay (skor çizgisinin ARKASINDA, önce çizilir ki skor
    #     çizgisi/noktaları görsel olarak ÜSTTE kalsın) ---------------------
    gecerli_fiyatlar = [f for f in fiyatlar if f is not None]
    if len(gecerli_fiyatlar) >= 2:
        pmin, pmax = min(gecerli_fiyatlar), max(gecerli_fiyatlar)
        price_coords: list[tuple[float, float] | None] = []
        for i, f in enumerate(fiyatlar):
            if f is None:
                price_coords.append(None)
                continue
            price_coords.append((_mchart_x(i, n), _price_norm_y(f, pmin, pmax)))
        d_parts = []
        drawing = False
        for pt in price_coords:
            if pt is None:
                drawing = False
                continue
            x, y = pt
            d_parts.append(f'{"M" if not drawing else "L"}{x:.1f},{y:.1f}')
            drawing = True
        if d_parts:
            parts.append(f'<path d="{" ".join(d_parts)}" class="mchart-price-line" fill="none"/>')
        for pt in price_coords:
            if pt is None:
                continue
            x, y = pt
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" class="mchart-price-dot"/>')

    d_parts = []
    drawing = False
    for pt in coords:
        if pt is None:
            drawing = False
            continue
        x, y = pt
        d_parts.append(f'{"M" if not drawing else "L"}{x:.1f},{y:.1f}')
        drawing = True
    if d_parts:
        parts.append(f'<path d="{" ".join(d_parts)}" class="mchart-line" fill="none"/>')
    for pt in coords:
        if pt is None:
            continue
        x, y = pt
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" class="mchart-dot"/>')

    # İmleç/crosshair + tooltip -- JS bunları göster/gizle yapar,
    # başlangıç konumu/görünürlüğü ÖNEMSİZ (JS ilk mousemove'da günceller).
    parts.append(
        f'<line x1="0" y1="{_MCHART_PAD_T}" x2="0" y2="{_MCHART_H - _MCHART_PAD_B}" class="mchart-crosshair" style="opacity:0;"/>'
    )
    parts.append('<circle r="5" class="mchart-hover-dot" style="opacity:0;"/>')
    parts.append(
        f'<rect x="{_MCHART_PAD_L}" y="{_MCHART_PAD_T}" '
        f'width="{_MCHART_W - _MCHART_PAD_L - _MCHART_PAD_R}" height="{_MCHART_H - _MCHART_PAD_T - _MCHART_PAD_B}" '
        f'class="mchart-hit-area" fill="transparent"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _skor_gecmisi_metric_charts(row: MarketScanResult) -> list[dict[str, Any]] | None:
    """`row.tarihsel_skorlar` (ESKİDEN YENİYE) üzerinden HER mercek/
    Bileşik için AYRI bir kart üretir -- kullanıcı isteği (2026-08-13,
    üçüncü tur): her kartta "3 Aylık"/"Yıllık" dönem seçici (iki ayrı
    ÖNCEDEN üretilmiş SVG, JS ile gösterilip/gizlenir) + fiyat grafiği
    ekle/kaldır butonu (`_skor_gecmisi_chart_for_rows` içinde AYNI SVG'ye
    gömülü ikinci bir katman, CSS ile aç/kapa). En az 2 dönem YOKSA
    `None` döner -- şablon bu durumda mevcut tabloyu TEK başına gösterir
    (Kural 3: uydurma yapılmaz)."""
    if not row.tarihsel_skorlar or len(row.tarihsel_skorlar) < 2:
        return None

    yillik_skorlar = _aggregate_annual(row.tarihsel_skorlar)
    currency_symbol = "₺" if row.currency == "TRY" else ("$" if row.currency == "USD" else "")

    charts: list[dict[str, Any]] = []
    for field, label in _METRIC_CHART_FIELDS:
        svg_ceyreklik = _skor_gecmisi_chart_for_rows(
            row.tarihsel_skorlar, field, label, row.ticker, currency_symbol, "mode-ceyreklik",
        )
        svg_yillik = (
            _skor_gecmisi_chart_for_rows(yillik_skorlar, field, label, row.ticker, currency_symbol, "mode-yillik hidden")
            if len(yillik_skorlar) >= 2 else None
        )
        charts.append({
            "label": label,
            "svg_ceyreklik": svg_ceyreklik,
            "svg_yillik": svg_yillik,
        })
    return charts


def _fiyat_degisimi_block(row: MarketScanResult) -> dict[str, Any] | None:
    """Kullanıcı isteği (2026-08-13, düzeltme): İLK sürüm "en eski
    mevcut dönemden şimdiye kadar" (8 dönem derinliğiyle ~2 yıla kadar
    çıkan, YANILTICI şekilde uzun bir aralık) kıyaslıyordu -- kullanıcı
    bunun yerine ÇEYREKTEN ÇEYREĞE anlamlı bir karşılaştırma istedi: "tam
    olarak bir ÖNCEKİ bilanço açıklandığı günün kapanış fiyatı ile GÜNCEL
    fiyat". `row.tarihsel_skorlar` ESKİDEN YENİYE sıralı olduğu için son
    eleman GÜNCEL dönem, ondan BİR ÖNCEKİ eleman (index -2) tam olarak bu
    -- `price` alanı zaten `_price_at_period_end()` ile o dönemin BİTİŞ
    tarihine en yakın kapanışı taşıyor (YENİ hesaplama/ağ isteği YOK).
    Bir önceki dönemde fiyat YOKSA (own_bars'ın ~760 günlük penceresi
    dışında kalan çok eski bir şirket/veri boşluğu) `None` döner -- daha
    ESKİ bir döneme SESSİZCE atlanmaz (Kural 3: kullanıcının İSTEDİĞİ
    tam karşılaştırma yapılamıyorsa dürüstçe gösterilmez)."""
    if row.current_price is None or not row.tarihsel_skorlar or len(row.tarihsel_skorlar) < 2:
        return None

    onceki_donem = row.tarihsel_skorlar[-2]
    onceki_fiyat = _decimal_or_none(onceki_donem.get("price"))
    onceki_donem_label = onceki_donem.get("donem_label") or onceki_donem.get("donem")
    if onceki_fiyat is None or onceki_fiyat == 0 or onceki_donem_label is None:
        return None

    fark = row.current_price - onceki_fiyat
    yuzde = (fark / onceki_fiyat) * Decimal("100")
    symbol = "₺" if row.currency == "TRY" else ("$" if row.currency == "USD" else "")
    if fark > 0:
        yon, yon_class = "yükseldi", "positive"
    elif fark < 0:
        yon, yon_class = "düştü", "negative"
    else:
        yon, yon_class = "değişmedi", "neutral"

    return {
        "ilk_donem_label": onceki_donem_label,
        "ilk_fiyat_display": f"{format_number_tr(onceki_fiyat, decimals=2)} {symbol}".strip(),
        "guncel_fiyat_display": f"{format_number_tr(row.current_price, decimals=2)} {symbol}".strip(),
        "fark_display": f"{format_number_tr(abs(fark), decimals=2)} {symbol}".strip(),
        "yuzde_display": format_percent_tr(abs(yuzde), decimals=1),
        "yon": yon,
        "yon_class": yon_class,
    }


def _carpanlar_block(row: MarketScanResult) -> dict[str, Any] | None:
    if row.current_price is None and row.market_cap is None and row.pe_ratio is None:
        return None
    symbol = "₺" if row.currency == "TRY" else ("$" if row.currency == "USD" else "")
    return {
        "price_display": f"{format_number_tr(row.current_price, decimals=2)} {symbol}".strip() if row.current_price is not None else "—",
        "market_cap_display": format_currency_short(row.market_cap, symbol=symbol) if row.market_cap is not None else "—",
        "pe_ratio_display": format_number_tr(row.pe_ratio, decimals=1) if row.pe_ratio is not None else "N/A",
        "pb_ratio_display": format_number_tr(row.pb_ratio, decimals=2) if row.pb_ratio is not None else "N/A",
        "ev_ebitda_display": format_number_tr(row.ev_ebitda, decimals=1) if row.ev_ebitda is not None else "N/A",
    }


def _period_label(period: tuple[int, int], market: str, is_annual_only: bool) -> str:
    """`src/render/card.py::_quarter_label`/`_fiscal_quarter_label`'ın BİREBİR
    aynı biçimlendirme mantığı -- KOPYALANDI (import EDİLMEDİ), card.py'nin
    kendisi de build_card_context()/build_us_card_context() arasında AYNI
    şekilde küçük yardımcıları TEKRAR tanımlıyor (proje deseni, mimari
    ihlal DEĞİL -- sadece bir sabit biçimlendirme kuralı, hesaplama yok)."""
    year, quarter = period
    if market == "NASDAQ":
        if is_annual_only:
            return f"FY{year % 100:02d}"
        return f"FY{year % 100:02d} Ç{quarter // 3}"
    return f"{quarter // 3}Ç{year % 100:02d}"


def _line_change_row(item: calculator.LineItemChange | None, currency_symbol: str, fallback_label: str) -> dict[str, str]:
    if item is None:
        return {"label": fallback_label, "current": "N/A", "comparison": "N/A", "change": "veri yok"}
    current = format_currency_short(item.current, symbol=currency_symbol) if item.current is not None else "N/A"
    comparison = format_currency_short(item.comparison, symbol=currency_symbol) if item.comparison is not None else "N/A"
    change = format_percent_tr(item.percent_change) if item.percent_change is not None else item.change_label
    return {"label": item.label_tr, "current": current, "comparison": comparison, "change": change}


def _summary_rows(section: Any, currency_symbol: str) -> list[dict[str, str]]:
    """`IncomeStatementSummary`/`BalanceSheetSummary` (VE banka/sigorta/
    finansman karşılıkları) dataclass'larını GENERİK olarak (alan adı
    SABİTLENMEDEN, `dataclasses.fields()` ile) satırlara çevirir -- 5
    şablonun HER BİRİ için ayrı ayrı elle eşleme YAZMAK yerine (calculator.py
    zaten her şablon için doğru LineItemChange nesnelerini üretiyor, bu
    fonksiyon SADECE onları taşır)."""
    rows = []
    for f in dataclasses.fields(section):
        item = getattr(section, f.name)
        fallback_label = calculator.FIELD_LABELS_TR.get(f.name, f.name)
        rows.append(_line_change_row(item, currency_symbol, fallback_label))
    return rows


def _quarterly_trend(quarterly_series: list, market: str, is_annual_only: bool, currency_symbol: str) -> list[dict[str, Any]]:
    if not quarterly_series:
        return []
    metric_fields = [f.name for f in dataclasses.fields(quarterly_series[0]) if f.name != "period"]
    trend = []
    for name in metric_fields:
        label = calculator.FIELD_LABELS_TR.get(name, _QUARTERLY_FIELD_LABEL_FALLBACK.get(name, name))
        points = []
        for point in quarterly_series:
            value = getattr(point, name)
            points.append({
                "period_label": _period_label(point.period, market, is_annual_only),
                "display": format_currency_short(value, symbol=currency_symbol) if value is not None else "N/A",
            })
        trend.append({"label": label, "points": points})
    return trend


def _build_financials_block(session: Session, row: MarketScanResult) -> dict[str, Any]:
    """Görev 1 madde 4: `get_financials()`'tan gelen çok-dönemli ham veriyi
    `calculator.py`'nin ZATEN tanımlı analyze*() fonksiyonlarına (şablona
    göre seçilir) verip SADECE üretilen alanları tabloya döker -- YENİ bir
    formül/eşik İCAT EDİLMEZ (bkz. modül üst notu)."""
    financials_by_period = repository.get_financials(session, row.ticker, n_periods=8)
    if not financials_by_period:
        return {
            "available": False,
            "income_rows": [], "balance_rows": [], "quarterly_trend": [],
            "note": "Bu şirket için veritabanında henüz çok-dönemli finansal tablo verisi yok.",
        }

    currency_symbol = "$" if row.currency == "USD" else "₺"
    template = row.template

    try:
        if template == "banka":
            company = session.get(Company, row.ticker)
            variant = "participation" if (company is not None and company.financial_group == "UFRS_KATILIM") else "conventional"
            analysis = calculator.analyze_bank(row.ticker, financials_by_period, bank_variant=variant)
        elif template == "sigorta":
            analysis = calculator.analyze_insurance(row.ticker, financials_by_period)
        elif template == "finansman":
            analysis = calculator.analyze_financing(row.ticker, financials_by_period)
        elif template == "abd_sanayi":
            analysis = calculator.analyze_us(row.ticker, financials_by_period)
        else:  # "sanayi" -- VE bilinmeyen/None şablonlarda GÜVENLİ varsayılan (BİST XI_29 en yaygın durum)
            analysis = calculator.analyze(row.ticker, financials_by_period)
    except Exception:  # noqa: BLE001 -- src/render/card.py::_company_logo_data_uri İLE AYNI ilke: bu SADECE
        # görüntüleme katmanındaki bir zenginleştirmedir (skor/rozet zaten row'da hazır, ETKİLENMEZ),
        # bir tickera özgü beklenmeyen veri şekli TÜM sayfanın render'ını ÇÖKERTMEMELİ -- açıkça
        # loglanır VE kullanıcıya DÜRÜST bir "işlenemedi" notu gösterilir (Kural 3: sessiz varsayılan
        # DEĞİL, görünür bir uyarı).
        logger.warning("%s icin finansal tablo ozeti islenemedi", row.ticker, exc_info=True)
        return {
            "available": False,
            "income_rows": [], "balance_rows": [], "quarterly_trend": [],
            "note": "Finansal tablo verisi işlenirken beklenmeyen bir durum oluştu -- skor/rozet bundan ETKİLENMEDİ.",
        }

    is_annual_only = getattr(analysis, "is_annual_only", False)
    return {
        "available": True,
        "currency_symbol": currency_symbol,
        "latest_period_display": _period_label(analysis.latest_period, row.market, is_annual_only),
        "income_rows": _summary_rows(analysis.income_statement, currency_symbol),
        "balance_rows": _summary_rows(analysis.balance_sheet, currency_symbol),
        "quarterly_trend": _quarterly_trend(analysis.quarterly_series, row.market, is_annual_only, currency_symbol),
        "note": None,
    }


def _faaliyet_raporu_block(row: MarketScanResult) -> dict[str, Any] | None:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu, Adım 4:
    `row.faaliyet_raporu_bulgulari` (JSON, `src/ai/kar_kaynagi.py::
    KarKaynagiBulgulari.to_dict()` çıktısı) VARSA gerçek bulguları TAŞIR;
    henüz analiz edilmemiş bir şirkette (sütun NULL) `None` döner -- çağıran
    taraf (`build_company_detail_data`) bu durumda MEVCUT dürüst
    `FAALIYET_RAPORU_PLACEHOLDER`'ı KORUR (Kural 3). Bu fonksiyon HİÇBİR
    yeni sayı/skor ÜRETMEZ -- sadece ZATEN Türkçe biçimlenmiş alanları
    tabloya/şablona hazır bir sözlüğe taşır."""
    if not row.faaliyet_raporu_bulgulari:
        return None
    bulgular = KarKaynagiBulgulari.from_dict(row.faaliyet_raporu_bulgulari)
    return {
        "kaynak_baslik": bulgular.kaynak_baslik,
        "kaynak_tarih_display": bulgular.kaynak_tarih_display,
        "kaynak_url": bulgular.kaynak_url,
        "kar_kaynagi_ozeti": bulgular.kar_kaynagi_ozeti,
        "arge_yatirim_notu": bulgular.arge_yatirim_notu,
        "faiz_finansman_notu": bulgular.faiz_finansman_notu,
        "risk_faktorleri": bulgular.risk_faktorleri,
        "source": bulgular.source,
        "kaynak_etiket": _FAALIYET_RAPORU_KAYNAK_ETIKET.get(bulgular.source, bulgular.source),
    }


# --- İş anlaşmaları (kullanıcı isteği, 2026-08-19: "hisse detaylarına
#     girdiğimde iş anlaşmaları olan hisselerde bunu görebilmek istiyorum") --
#
# Kaynak: `scripts/is_anlasma_arastirma.py` tarafından ÖNCEDEN üretilmiş
# `data/abcd_cache/is_anlasmalari_yillik.csv` -- BU MODÜL bu araştırmayı
# TEKRAR ÇALIŞTIRMAZ (ağa GİTMEZ, KAP/fetcher import ETMEZ), sadece o
# CSV'nin ZATEN hesaplanmış satırlarını okuyup şirkete göre filtreler +
# Türkçe biçimlendirir (quaxis-mimari anayasa ile AYNI ilke -- dashboard.py
# da benzer şekilde DB'den ÖNCEDEN hesaplanmış `MarketScanResult` okur).
#
# `docs/spec/IS_ANLASMALARI_FORWARD_RETURN.md` bulgusu (2026-08-19): eşiği
# GEÇEN (n=11) ile GEÇMEYEN (n=98) grupların 6 aylık ileri getirisi arasında
# istatistiksel olarak anlamlı fark BULUNAMADI (p=0.52) -- bu bölüm bu
# yüzden AÇIKÇA "yatırım tavsiyesi değildir, bilgilendirme amaçlıdır" notu
# taşır (Kural: bir ilişkiyi KANITLANMAMIŞ bir öngörü gibi SUNMAK YASAK).
_IS_ANLASMA_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_yillik.csv"
# Kullanıcı isteği (2026-08-19): "iş anlaşmaları ve miktarları belli olan
# her hisse için yazmak zorundayız hepsini yazabilecek şekilde güncelle" --
# yıllık TOPLAM'ın yanında TEK TEK anlaşma satırları da gösterilir (bkz.
# `scripts/is_anlasma_arastirma.py`nin ÜRETTİĞİ, ÖNCEDEN hesaplanmış CSV --
# bu modül YİNE hiçbir parse/FX-çevrim işlemi TEKRARLAMAZ, sadece okur).
_IS_ANLASMA_DETAY_CSV = config.DATA_DIR / "abcd_cache" / "is_anlasmalari_detay.csv"

IS_ANLASMALARI_ACIKLAMA = (
    "\"Eşiği geçti\" -- şirketin o yıl duyurduğu YENİ (mevcut/yenileme anlaşmaları HARİÇ) iş "
    "anlaşmalarının toplamı, bir önceki yılın TÜM satış gelirinden en az %20 FAZLA mı (yeni iş ≥ "
    "önceki yıl hasılatının 1,2 katı) -- yani şirket tek başına yeni anlaşmalarla bile bir önceki "
    "yılın cirosunu aşmış mı, sorusuna cevap verir (çok yüksek bir çıta, çoğu şirket geçemez). "
    "⚠️ İlk istatistiksel testte (n=11 eşiği geçen vs n=98 geçmeyen, Mann-Whitney p=0,52) bu eşiği "
    "geçmenin sonraki 6 aylık hisse performansını öngördüğüne dair bir kanıt BULUNAMADI -- bu bölüm "
    "SADECE bilgilendirme amaçlıdır, yatırım tavsiyesi DEĞİLDİR."
)


@functools.lru_cache(maxsize=1)
def _load_is_anlasma_rows() -> dict[str, list[dict[str, str]]]:
    """CSV'yi bir kez okuyup ticker'a göre gruplar -- `_write_all_details`
    yüzlerce şirket için tek tek dosya AÇMASIN diye modül-seviyesinde
    önbelleklenir (CSV değişirse süreç yeniden başlatılmalı, tarama_toplu.py
    ile AYNI "process ömrü boyunca sabit" varsayımı)."""
    if not _IS_ANLASMA_CSV.exists():
        return {}
    by_ticker: dict[str, list[dict[str, str]]] = {}
    with _IS_ANLASMA_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_ticker.setdefault(row["ticker"], []).append(row)
    return by_ticker


def _is_anlasmalari_block(ticker: str, now: datetime) -> list[dict[str, Any]] | None:
    rows = _load_is_anlasma_rows().get(ticker)
    if not rows:
        return None
    out: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda r: r["yil"], reverse=True):
        esik_gecti = r["esik_gecti_mi"].strip().lower() == "true"
        oran = _decimal_or_none(r.get("oran"))
        yeni_is = _decimal_or_none(r.get("yeni_is_toplami_try"))
        onceki_hasilat = _decimal_or_none(r.get("onceki_yil_hasilat_try"))
        kapsam = _decimal_or_none(r.get("kapsam_pct"))
        # DÜZELTME (kullanıcı denetimi, 2026-08-19): içinde bulunulan yıl
        # (örn. 2026) HENÜZ TAMAMLANMADIYSA, o yılın (kısmi) yeni-iş toplamını
        # bir ÖNCEKİ yılın TAM cirosuyla kıyaslayıp kesin "Evet/Hayır"
        # göstermek YANILTICI olur (yıl bitmeden oran sistematik olarak
        # DÜŞÜK çıkar) -- bu durumda eşik yargısı GİZLENİR, sadece "yıl
        # tamamlanmadı" notu + ham rakamlar gösterilir (Kural 3: sahte
        # kesinlik YOK, ama VAR OLAN veri de saklanmaz).
        yil_tamamlanmadi = int(r["yil"]) >= now.year
        if yil_tamamlanmadi:
            esik_display = f"◐ {now.year} yılı henüz tamamlanmadı -- eşik karşılaştırması (henüz) yapılamaz"
        else:
            esik_display = "✅ Eşiği geçti (yeni iş ≥ önceki yıl cirosunun 1,2 katı)" if esik_gecti else "◻ Eşiği geçmedi"
        out.append({
            "yil": r["yil"],
            "esik_gecti": esik_gecti and not yil_tamamlanmadi,
            "yil_tamamlanmadi": yil_tamamlanmadi,
            "esik_gecti_display": esik_display,
            "oran_display": format_percent_tr(oran * Decimal("100"), decimals=1) if oran is not None else "N/A",
            "yeni_is_toplami_display": format_currency_short(yeni_is, symbol="₺") if yeni_is is not None else "N/A",
            "onceki_yil_hasilat_display": format_currency_short(onceki_hasilat, symbol="₺") if onceki_hasilat is not None else "N/A",
            "n_anlasma": r.get("n_anlasma", "—"),
            "kapsam_display": format_percent_tr(kapsam, decimals=0) if kapsam is not None else "N/A",
        })
    return out


@functools.lru_cache(maxsize=1)
def _load_is_anlasma_deal_rows() -> dict[str, list[dict[str, str]]]:
    if not _IS_ANLASMA_DETAY_CSV.exists():
        return {}
    by_ticker: dict[str, list[dict[str, str]]] = {}
    with _IS_ANLASMA_DETAY_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_ticker.setdefault(row["ticker"], []).append(row)
    return by_ticker


def _is_anlasma_detaylari_block(ticker: str) -> list[dict[str, Any]] | None:
    """Yıllık toplamın YANINDA, TEK TEK anlaşma satırları -- kullanıcı
    isteği (2026-08-19): "miktarları belli olan her hisse için ... hepsini
    yazabilecek şekilde". Yenileme sözleşmeleri de listede GÖRÜNÜR (toplama
    katılmazlar ama SAKLANMAZLAR) -- `yenileme_mi` ile açıkça etiketlenir."""
    rows = _load_is_anlasma_deal_rows().get(ticker)
    if not rows:
        return None
    out: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda r: r["tarih"], reverse=True):
        yenileme = r["yenileme_mi"].strip().lower() == "true"
        tutar_try = _decimal_or_none(r.get("tutar_try"))
        out.append({
            "tarih": r["tarih"],
            "karsi_taraf": r.get("karsi_taraf") or "—",
            "aciklama": r.get("aciklama") or "—",
            "tutar_ham": r.get("tutar_ham") or "—",
            "tutar_try_display": format_currency_short(tutar_try, symbol="₺") if tutar_try is not None else (
                "yenileme (hariç)" if yenileme else "N/A (ayrıştırılamadı)"
            ),
            "yenileme_mi": yenileme,
        })
    return out


def build_company_detail_data(session: Session, ticker: str, market: str, *, now: datetime | None = None) -> dict[str, Any] | None:
    """`MarketScanResult` + `mercekler_detay` + `get_financials()`'ı company
    detay sayfası şemasına çevirir. Satır YOKSA veya piyasa uyuşmuyorsa
    `None` döner (çağıran taraf -- ileride /telegram veya bir web route --
    404 benzeri bir yanıt üretebilsin diye)."""
    ticker = ticker.strip().upper()
    row = session.get(MarketScanResult, ticker)
    if row is None or row.market != market:
        return None

    # Kullanıcı isteği (2026-08-13, dördüncü tur): "sektör" meta-chip'i
    # SADECE geniş `ust_sektor`u (11 grup, istatistiksel) gösteriyordu --
    # Fintables'takine benzer İNCE sektör etiketi de (`Company.sector`,
    # bugün fintables_sektor.py kaynaklı) AYRICA görünsün istendi. Bu alan
    # `MarketScanResult`'ta YOK (sadece `ust_sektor` kopyalanır) -- `Company`
    # satırından okunur, İSTATİSTİKSEL hiçbir hesaba KARIŞMAZ (Kural 3:
    # sadece görüntüleme, `_build_financials_block`'un KENDİ `Company`
    # okumasıyla AYNI ilke).
    company_row = session.get(Company, ticker)
    ince_sektor = company_row.sector if company_row is not None else None

    now = now or utcnow_naive()
    has_snapshot = row.bilesik_score is not None or row.deger_score is not None or row.kalite_score is not None

    bilesik = None
    mercekler = None
    if has_snapshot:
        bilesik = {
            "score_display": format_number_tr(row.bilesik_score, decimals=1) if row.bilesik_score is not None else "N/A",
            "badge": row.bilesik_badge,
            "badge_class": _BADGE_CLASS.get(row.bilesik_badge or "", "yetersiz"),
            "data_coverage_pct_display": (
                format_percent_tr(row.bilesik_data_coverage_pct, decimals=0)
                if row.bilesik_data_coverage_pct is not None else "—"
            ),
            "dahil_edilen_mercekler": row.dahil_edilen_mercekler or [],
        }
        mercekler = {}
        for prefix, key, label in _MERCEK_ANAHTAR_ETIKET:
            summary = _mercek_summary(row, prefix, key, label)
            if summary is None:
                mercekler[key] = None
                continue
            summary["label"] = label
            summary["components"] = _mercek_components(row, key)
            mercekler[key] = summary

    return {
        "ticker": row.ticker,
        "company_name": row.company_name or row.ticker,
        "market": row.market,
        "ust_sektor": row.ust_sektor or "Sınıflandırılmamış",
        "ince_sektor": ince_sektor,
        # docs/spec/spec_sektor_inceltme.md "Seçenek B" -- dashboard.py ile
        # AYNI SADECE-görsel rozet (bkz. o modülün üst notu), istatistiksel
        # `ust_sektor`'e karışmaz.
        "ekosistem_etiketi": ekosistem_etiketi_for_ticker(row.ticker),
        "sirket_turu_display": _SIRKET_TURU_DISPLAY.get(row.sirket_turu, row.sirket_turu or "—"),
        "template": row.template,
        "period_display": f"{row.year}/{row.period}" if row.year is not None and row.period is not None else "—",
        "scan_status": row.scan_status,
        "computed_at_display": _tr_datetime(row.computed_at),
        "generated_at_display": _tr_datetime(now),
        "bilesik": bilesik,
        "mercekler": mercekler,
        "skor_gecmisi": _skor_gecmisi_block(row),
        "skor_gecmisi_charts": _skor_gecmisi_metric_charts(row),
        "fiyat_degisimi": _fiyat_degisimi_block(row),
        "carpanlar": _carpanlar_block(row),
        "financials": _build_financials_block(session, row),
        "faaliyet_raporu": _faaliyet_raporu_block(row),
        "faaliyet_raporu_placeholder": FAALIYET_RAPORU_PLACEHOLDER,
        "is_anlasmalari": _is_anlasmalari_block(row.ticker, now),
        "is_anlasma_detaylari": _is_anlasma_detaylari_block(row.ticker),
        "is_anlasmalari_aciklama": IS_ANLASMALARI_ACIKLAMA,
        "dashboard_relative_url": "../dashboard.html",
    }


def render_company_detail_html(data: dict[str, Any], template_name: str = "company_detail.html") -> str:
    template = _env.get_template(template_name)
    return template.render(data=data)


def build_and_write_company_detail(
    ticker: str, market: str, output_path: str | Path | None = None, *, session: Session | None = None,
) -> str | None:
    """Tek şirket için `output/detay/{market}_{ticker}.html` üretir --
    `src/render/dashboard.py::build_and_write_dashboard()`'ın tek-şirketlik
    karşılığı. Satır bulunamazsa `None` döner (dosya YAZILMAZ)."""
    if session is not None:
        data = build_company_detail_data(session, ticker, market)
    else:
        with repository.get_session() as owned_session:
            data = build_company_detail_data(owned_session, ticker, market)

    if data is None:
        return None

    out_path = Path(output_path) if output_path is not None else detail_output_path(ticker, market)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_company_detail_html(data)
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)


def build_and_write_all_company_details(*, session: Session | None = None, output_dir: str | Path | None = None) -> list[str]:
    """Görev 2: HER `MarketScanResult` satırı için ayrı bir detay sayfası
    üretir -- `scripts/tarama_toplu.py` tarafından doldurulmuş TÜM satırları
    (BIST + NASDAQ) tarar, ağa GİTMEZ (SADECE DB okur, `build_and_write_
    dashboard()` ile AYNI "veri kaynağı zaten hazır" ilkesi).

    `output_dir` verilmezse varsayılan `output/detay/` kullanılır
    (`detail_output_path()`); testler VEYA `dashboard.py`'nin özel bir
    `output_path` ile çağrılması durumunda GERÇEK proje `output/` klasörünü
    KİRLETMEMEK için AYRI bir dizin geçirilebilir (dosya adı deseni --
    `{market}_{ticker}.html` -- AYNI kalır)."""
    if session is not None:
        return _write_all_details(session, output_dir)
    with repository.get_session() as owned_session:
        return _write_all_details(owned_session, output_dir)


def _write_all_details(session: Session, output_dir: str | Path | None = None) -> list[str]:
    written: list[str] = []
    for row in repository.get_market_scan_results(session):
        data = build_company_detail_data(session, row.ticker, row.market)
        if data is None:
            continue
        if output_dir is not None:
            out_path = Path(output_dir) / f"{row.market}_{row.ticker}.html"
        else:
            out_path = detail_output_path(row.ticker, row.market)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        html = render_company_detail_html(data)
        out_path.write_text(html, encoding="utf-8")
        written.append(str(out_path))
    return written


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Kullanım: python -m src.render.company_detail <TICKER> <BIST|NASDAQ>")
        raise SystemExit(1)
    yol = build_and_write_company_detail(sys.argv[1].upper(), sys.argv[2].upper())
    print(f"Detay sayfası üretildi: {yol}" if yol else "Satır bulunamadı.")
