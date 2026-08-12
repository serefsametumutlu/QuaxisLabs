"""docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu / Dipnot
Araştırması -- BİST şirketlerinin KAP faaliyet raporu metninden "kâr nereden
geliyor" tipi NİTEL bulgular çıkarır.

KESİN İLKE (mimari anayasa madde 1 -- "LLM asla sayı üretmez" -- BURADA da
GEÇERLİ, spec'in kendi vurgusuyla): bu modülün çıktısı bir SKOR/PUAN
DEĞİLDİR, herhangi bir mercek skoruna KARIŞTIRILMAZ -- sadece ham metinden
çıkarılmış, madde madde bir CHECKLİST + kısa Türkçe yorum metnidir. Gemini'ye
HİÇBİR ZAMAN ham PDF'in TAMAMI verilmez (maliyet + "LLM ham tabloyu okuyup
sayı üretsin" riski); önce anahtar-kelime skorlamasıyla SADECE finansal/
faaliyet ile ilgili görünen sayfalar seçilir (bkz. `_select_relevant_text`),
LLM SADECE bu kırpılmış metni + sabit bir checklist görür.

`src/ai/commentary.py` İLE AYNI katman/ilke (I/O + LLM orkestrasyonu
`src/analysis/*`'e KONMAZ -- o katman SAF matematiktir, hiçbir LLM çağrısı/
fetcher import etmez): mevcut Gemini-çağıran modül tam olarak `src/ai/
commentary.py`'de yaşıyor (kod okumasıyla doğrulandı), bu modül AYNI pakete
(`src/ai/`) paralel bir konum olarak eklendi. HTTP/retry/JSON-güvenlik
katmanı KOPYALANMADI -- `commentary.call_llm_json()` (bu görev için oraya
eklenen, şemadan bağımsız genel amaçlı yardımcı) ÇAĞRILIR.

Sağlamlık garantisi `commentary.generate_commentary()` ile AYNI: GEMINI_API_KEY
tanımlı değilse veya Gemini çağrısı (retry'lardan sonra da) başarısız olursa,
HİÇBİR İSTİSNA FIRLATMADAN kural tabanlı, dürüst bir yedek metne düşülür
("Bu bölüm için otomatik metin analizi şu an kullanılamıyor" -- spec'in
kendi önerdiği ifade).

Kapsam: BU TURDA SADECE BİST (spec'in kendi önerisi -- NASDAQ/SEC 10-K MD&A
metni çekmek için sıfırdan yeni bir fetcher gerekiyor, ayrı/sonraki bir tur).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import config
from src.ai import commentary
from src.db.models import utcnow_naive
from src.fetchers import kap, pdf_ocr
from src.fetchers.kap import _turkish_lower

logger = logging.getLogger(__name__)

# PDF çok büyük olabilir (CANLI ölçüldü: THYAO "Entegre Faaliyet Raporu"
# 263 sayfa) -- native metin çıkarma HIZLI olsa da (OCR DEĞİL) latansı
# öngörülebilir tutmak için bir üst sınır konur; SPK Seri:II No:14.1
# formatındaki standart üç aylık faaliyet raporları (CANLI gözlemlendi:
# THYAO örneğinde 26 sayfa) bu sınırın ÇOK altında kalır, hiç ETKİLENMEZ.
_MAX_PAGES_TO_SCAN = 200

# Gemini'ye giden metin bütçesi (karakter) -- "ham PDF'in TAMAMI ASLA
# verilmez" ilkesinin somut sınırı. ~14.000 karakter, seçilen birkaç sayfayı
# (CANLI örnekte "Sektör ve Faaliyet Ortamı" + "Finansal Durum" bölümleri
# ~5-8 sayfa) rahatça kapsar.
_MAX_PROMPT_CHARS = 14_000

_FALLBACK_NOTE = "Bu bölüm için otomatik metin analizi şu an kullanılamıyor."

# Sayfa-bazlı alaka skorlaması için anahtar kelime listesi -- spec'in 4
# checklist sorusunu (kâr kaynağı, Ar-Ge/yatırım değişimi, faiz/finansman
# etkisi, risk faktörleri) DOĞRUDAN kapsayan çok-kelimeli Türkçe ifadeler.
# BİLİNÇLİ OLARAK tek başına "kar"/"kâr" gibi belirsiz kökler YOK -- CANLI
# gözlemlendi (THYAO "Entegre Faaliyet Raporu"): "karbon" gibi alakasız
# kelimeler "kar" alt dizesini İÇERİR, yanlış pozitif riski yüksek olurdu
# (bkz. `src/ai/commentary.py::_ASCII_DEGRADED_TR_RE` üst notundaki AYNI
# sınıf "belirsiz kök" riski). `_turkish_lower()` (kap.py) kullanılır --
# düz Python `str.lower()` büyük "İ" harfini `_select_relevant_text()`'te
# ARANACAK "finansman"/"kâr" gibi köklerle YANLIŞ eşleşmeyecek şekilde
# COMBINING DOT karakterine çevirip alt dize eşleşmesini BOZAR (bkz.
# kap.py modül üst notu).
_RELEVANT_KEYWORDS: tuple[str, ...] = (
    "net dönem kâr", "net dönem kar", "net dönem zarar",
    "faaliyet kârı", "faaliyet karı", "faaliyet zararı",
    "esas faaliyet", "brüt kâr", "brüt kar", "vergi öncesi",
    "kârlılık", "karlılık", "hasılat", "satış hacmi", "satış geliri",
    "maliyet", "gider art", "gider azal", "gider düş",
    "ar-ge", "araştırma ve geliştirme", "araştırma-geliştirme",
    "yatırım harcaması", "yatırım harcamaları",
    "faiz gideri", "faiz geliri", "finansman gideri", "finansman geliri",
    "kur farkı", "risk", "belirsizlik", "olağandışı", "tek seferlik",
    "varlık satışı", "dava", "tazminat", "teşvik",
    "sektör ve faaliyet ortamı", "finansal durum",
)


@dataclass(frozen=True)
class KarKaynagiBulgulari:
    """Faaliyet raporu nitel bulguları -- `MarketScanResult.faaliyet_raporu_
    bulgulari` (JSON) sütununa `to_dict()` ile, `src/render/company_detail.py`
    tarafından `from_dict()` ile okunur. TÜM alanlar ZATEN Türkçe biçimlenmiş
    string'lerdir (Kural 4: şablonlar hesaplamaz)."""

    kaynak_baslik: str
    kaynak_tarih_display: str
    kaynak_url: str
    kar_kaynagi_ozeti: str
    arge_yatirim_notu: str
    faiz_finansman_notu: str
    risk_faktorleri: list[str] = field(default_factory=list)
    source: str = "fallback"  # "llm" | "fallback"
    generated_at: datetime = field(default_factory=utcnow_naive)

    def to_dict(self) -> dict:
        return {
            "kaynak_baslik": self.kaynak_baslik,
            "kaynak_tarih_display": self.kaynak_tarih_display,
            "kaynak_url": self.kaynak_url,
            "kar_kaynagi_ozeti": self.kar_kaynagi_ozeti,
            "arge_yatirim_notu": self.arge_yatirim_notu,
            "faiz_finansman_notu": self.faiz_finansman_notu,
            "risk_faktorleri": self.risk_faktorleri,
            "source": self.source,
            "generated_at": self.generated_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "KarKaynagiBulgulari":
        generated_at_raw = data.get("generated_at")
        try:
            generated_at = datetime.fromisoformat(generated_at_raw) if generated_at_raw else utcnow_naive()
        except ValueError:
            generated_at = utcnow_naive()
        return KarKaynagiBulgulari(
            kaynak_baslik=data.get("kaynak_baslik") or "",
            kaynak_tarih_display=data.get("kaynak_tarih_display") or "",
            kaynak_url=data.get("kaynak_url") or "",
            kar_kaynagi_ozeti=data.get("kar_kaynagi_ozeti") or "",
            arge_yatirim_notu=data.get("arge_yatirim_notu") or "",
            faiz_finansman_notu=data.get("faiz_finansman_notu") or "",
            risk_faktorleri=list(data.get("risk_faktorleri") or []),
            source=data.get("source") or "fallback",
            generated_at=generated_at,
        )


# --- Sistem istemi + JSON şeması (commentary.py İLE AYNI üslup: ASCII istem
# metni, çıktı Türkçe karakterleri DOĞRU kullanmalı -- bkz. o modülün kural 9) ---

_SYSTEM_INSTRUCTION = """Sen bir BIST temel analiz platformu icin calisan, sirketlerin KAP \
faaliyet raporu metnini okuyup NITEL bulgular cikaran bir analistsin. Sana bir sirketin \
faaliyet raporundan alinmis HAM METIN parcalari verilecek (rapor cok uzun oldugu icin \
SADECE finansal/faaliyet ile ilgili gorunen sayfalar secilip verildi).

KESIN KURALLAR:
1. Uretecegin cikti bir SKOR/PUAN/SAYI DEGILDIR -- sadece VERILEN metinden CIKARILAN nitel \
gozlemlerdir. Metinde GECMEYEN hicbir sayi, yuzde veya iddia URETME/HESAPLAMA; metinde bir \
rakam gorursen OLDUGU GIBI aktarabilirsin, ama YENI bir rakam TURETME.
2. Metinde bir konuda ACIK bilgi YOKSA, o alan icin AYNEN "Raporda bu konuda açık bir bilgi \
bulunmuyor." yaz (bu cumleyi -- Turkce harfleriyle BIREBIR -- degistirmeden kullan) -- UYDURMA \
YAPMA.
3. Yatirim tavsiyesi VERME; "al", "sat", "tut", hedef fiyat gibi ifadeler KULLANMA.
4. Profesyonel, notr bir analist uslubu kullan; abartili/sansasyonel dilden kacin. Emoji kullanma.
5. Tum metin TURKCE olacak, Turkce'ye ozgu harfleri (ı, ğ, ü, ş, ö, ç, İ, Ğ, Ü, Ş, Ö, Ç) HER \
ZAMAN DOGRU kullan -- ASCII'ye indirgenmis kelimeler KESINLIKLE YASAK.
6. Yalniz asagidaki JSON semasina uyan gecerli JSON dondur; baska hicbir aciklama, markdown kod \
blogu isareti veya ek metin EKLEME.
7. Alan degerlerinin ICINE kendi kendine not, taslak duzeltmesi, Ingilizce meta-yorum veya \
parantez ici ic ses YAZMA (orn. "(Wait, ...)" gibi ifadeler KESINLIKLE YASAK).

JSON semasi:
{
  "kar_kaynagi_ozeti": "2-4 cumle: donemin kari/zarari temel olarak NEREDEN geliyor -- satis \
hacmi mi fiyat mi, maliyet degisimi mi, kur etkisi mi, tek seferlik bir kalem (varlik satisi, \
dava tazminati, sigorta tazminati) mi? Metindeki somut ifade/sayilara dayan.",
  "arge_yatirim_notu": "1-3 cumle: Ar-Ge/yatirim harcamalarinda dikkat cekici bir degisim var \
mi, sirket bunu metinde NASIL acikliyor? Metinde bilgi yoksa kural 2'deki sabit cumleyi yaz.",
  "faiz_finansman_notu": "1-3 cumle: faiz geliri/gideri veya net finansman gideri/geliri kari \
anlamli olcude etkiliyor mu? Metinde bilgi yoksa kural 2'deki sabit cumleyi yaz.",
  "risk_faktorleri": ["yonetimin METNINDE ACIKCA belirttigi ana risk/belirsizlik faktorleri, \
en fazla 4 madde -- metinde hicbiri yoksa BOS liste don"]
}"""

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "kar_kaynagi_ozeti": {"type": "STRING"},
        "arge_yatirim_notu": {"type": "STRING"},
        "faiz_finansman_notu": {"type": "STRING"},
        "risk_faktorleri": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["kar_kaynagi_ozeti", "arge_yatirim_notu", "faiz_finansman_notu", "risk_faktorleri"],
}


def _select_relevant_text(pages: list[str], max_chars: int = _MAX_PROMPT_CHARS) -> str:
    """Her sayfayı `_RELEVANT_KEYWORDS` geçiş SAYISINA göre skorlar, en
    yüksek skorlu sayfaları (bütçe -- `max_chars` -- dolana kadar) seçer,
    SONRA okunabilirlik için orijinal sayfa SIRASINA göre yeniden dizer ve
    birleştirir. Hiçbir sayfa eşleşmezse boş string döner (Kural 3 --
    çağıran taraf bunu "ilgili bölüm bulunamadı" olarak yorumlar, LLM'e
    ALAKASIZ/kapak-sayfası metni GÖNDERMEZ)."""
    scored: list[tuple[int, int, str]] = []
    for index, page_text in enumerate(pages):
        haystack = _turkish_lower(page_text)
        score = sum(haystack.count(keyword) for keyword in _RELEVANT_KEYWORDS)
        if score > 0:
            scored.append((index, score, page_text))

    if not scored:
        return ""

    scored.sort(key=lambda item: item[1], reverse=True)
    selected_indices: set[int] = set()
    total_chars = 0
    for index, _score, page_text in scored:
        if total_chars >= max_chars:
            break
        selected_indices.add(index)
        total_chars += len(page_text)

    ordered_pages = [pages[i] for i in sorted(selected_indices)]
    combined = "\n\n".join(ordered_pages)
    return combined[:max_chars]


def _build_user_prompt(ticker: str, disclosure: kap.Disclosure, secili_metin: str) -> str:
    return (
        f"Hisse: {ticker}\n"
        f"Kaynak KAP bildirimi: {disclosure.title} ({disclosure.date.strftime('%d.%m.%Y')})\n\n"
        "## Faaliyet Raporundan Seçilen İlgili Sayfalar\n"
        "(finansal/faaliyet anahtar kelimesi geçen sayfalar, orijinal sayfa sırasıyla; "
        "raporun TAMAMI değil)\n\n"
        f"{secili_metin}"
    )


def _fallback_bulgular(disclosure: kap.Disclosure, reason: str | None = None) -> KarKaynagiBulgulari:
    """LLM'siz, kural tabanlı, DÜRÜST bir yedek metin -- `commentary.py`'nin
    LLM'siz yedek modu İLE AYNI güvenlik ağı ilkesi (GEMINI_API_KEY yoksa
    veya API hatasında bu modül ASLA çökmez/boş dönmez). Faaliyet raporu
    METNİNİN kendisi NLP olmadan otomatik özetlenemeyeceği için (Schilit/06
    kitabı işlenene kadar bu bölüm TAMAMEN nitel/LLM'e bağımlı kalır, bkz.
    spec §Faaliyet Raporu madde 4) yedek metin sadece DÜRÜST bir "şu an
    kullanılamıyor" notudur -- sahte/uydurma bir bulgu ÜRETİLMEZ (Kural 3)."""
    not_metni = f"{_FALLBACK_NOTE} ({reason})" if reason else _FALLBACK_NOTE
    return KarKaynagiBulgulari(
        kaynak_baslik=disclosure.title,
        kaynak_tarih_display=disclosure.date.strftime("%d.%m.%Y"),
        kaynak_url=disclosure.url,
        kar_kaynagi_ozeti=not_metni,
        arge_yatirim_notu=not_metni,
        faiz_finansman_notu=not_metni,
        risk_faktorleri=[],
        source="fallback",
    )


def analyze_kar_kaynagi(ticker: str, *, days: int = kap._ANNUAL_REPORT_DISCOVERY_DAYS) -> KarKaynagiBulgulari | None:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet Raporu -- BİST
    için uçtan uca orkestrasyon: KAP'tan en güncel faaliyet raporu/yıllık
    rapor bildirimini bul -> PDF indir -> ilgili sayfaları seç -> Gemini'ye
    checklist ile yorumlat (GEMINI_API_KEY yoksa/hata verirse kural tabanlı
    yedek).

    Uygun bir bildirim/PDF BULUNAMAZSA `None` döner (Kural 3 -- çağıran
    taraf, `src/render/company_detail.py`, MEVCUT dürüst placeholder'ı
    KORUR, sahte/boş bir "bulgular" kutusu GÖSTERMEZ). Bildirim/PDF
    bulunduktan SONRAKİ her adımda (metin çıkarma, alaka bulunamaması,
    LLM hatası) `KarKaynagiBulgulari(source="fallback")` döner -- kaynak
    (bildirim başlığı/tarihi/linki) HER ZAMAN gösterilir, sadece yorum
    alanları dürüst bir "kullanılamıyor" notu taşır."""
    try:
        result = kap.fetch_latest_annual_report_pdf(ticker, days=days)
    except kap.KapError as exc:  # noqa: BLE001 -- Kural 9: bu ikincil bir zenginleştirmedir, ANA taramayı ETKİLEMEMELİ
        logger.warning("%s icin faaliyet raporu kesfi basarisiz: %s", ticker, exc)
        return None
    if result is None:
        return None
    disclosure, pdf_bytes = result

    pages = pdf_ocr.extract_native_pages(pdf_bytes, max_pages=_MAX_PAGES_TO_SCAN)
    if not pages:
        return _fallback_bulgular(disclosure, reason="PDF metni çıkarılamadı")

    secili_metin = _select_relevant_text(pages)
    if not secili_metin.strip():
        return _fallback_bulgular(disclosure, reason="ilgili finansal bölüm bulunamadı")

    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY tanımlı değil, kâr kaynağı analizi kural tabanlı yedek modda.")
        return _fallback_bulgular(disclosure)

    user_prompt = _build_user_prompt(ticker, disclosure, secili_metin)
    try:
        data = commentary.call_llm_json(
            user_prompt, system_instruction=_SYSTEM_INSTRUCTION, response_schema=_RESPONSE_SCHEMA
        )
        return KarKaynagiBulgulari(
            kaynak_baslik=disclosure.title,
            kaynak_tarih_display=disclosure.date.strftime("%d.%m.%Y"),
            kaynak_url=disclosure.url,
            kar_kaynagi_ozeti=str(data.get("kar_kaynagi_ozeti") or "").strip() or _FALLBACK_NOTE,
            arge_yatirim_notu=str(data.get("arge_yatirim_notu") or "").strip() or _FALLBACK_NOTE,
            faiz_finansman_notu=str(data.get("faiz_finansman_notu") or "").strip() or _FALLBACK_NOTE,
            risk_faktorleri=[str(x).strip() for x in (data.get("risk_faktorleri") or []) if str(x).strip()][:4],
            source="llm",
        )
    except Exception as exc:  # noqa: BLE001 -- Kural 9: LLM/ağ hatalarının TÜMÜ -- bu fonksiyon asla çökmemeli
        logger.warning("%s icin kar kaynagi LLM analizi basarisiz (%s), kural tabanli yedege dusuluyor.", ticker, exc)
        return _fallback_bulgular(disclosure)
