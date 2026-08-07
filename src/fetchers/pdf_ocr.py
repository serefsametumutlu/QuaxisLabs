"""Taranmış/görüntü-tabanlı (metin katmanı olmayan) PDF'ler için OCR yedeği --
2026-08-07 (otuz birinci tur, kullanıcı isteği: KPEKS/VEYAS izahnamelerinin
BÜYÜK kısmı `pdfplumber` ile 0 karakter döndürüyor -- `kap_ipo.py`/
`ipo_price_report.py` modül üst notlarında belgelenen, önceki turlarda
BİLİNÇLİ OLARAK eklenmemiş olan "yeni bağımlılık").

── NEDEN AYRI BİR MODÜL ──
Hem `kap_ipo.py` (ana izahname) hem `ipo_price_report.py` (Fiyat Tespit
Raporu) AYNI "önce pdfplumber dene, boşsa OCR'a düş" desenine ihtiyaç
duyuyor -- mantık TEK yerde, iki modül de sadece `extract_text()`'i çağırır.

── KURULUM (bu modül SADECE Python paketlerini varsayar, sistem ikili
dosyalarını KURMAZ) ──
1. Tesseract OCR motoru (binary) -- Windows'ta `winget install --id
   UB-Mannheim.TesseractOCR -e` ile kurulur, VARSAYILAN olarak
   `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`'ye kurulur.
2. Türkçe dil paketi (`tur.traineddata`) -- Tesseract'ın KENDİ kurulumu
   SADECE İngilizce (`eng`) içerir, Türkçe AYRI indirilmesi gerekir.
   `Program Files` altına yazmak YÖNETİCİ hakkı istediği için (bu oturumda
   `Access denied` ile CANLI doğrulandı) proje-yerel `data/tessdata/`
   klasörüne indirilip `TESSDATA_PREFIX` ortam değişkeniyle gösterilir --
   `Invoke-WebRequest -Uri
   https://github.com/tesseract-ocr/tessdata/raw/main/tur.traineddata
   -OutFile data/tessdata/tur.traineddata` (~18 MB, TEK seferlik).

Her iki bileşen de EKSİKSE `is_available()` `False` döner, çağıran taraf
(Kural 9) SESSİZCE OCR'sız devam eder -- bu bot BAŞKA bir makinede
çalıştırılırsa (Tesseract kurulu olmayabilir) pipeline ÇÖKMEZ, sadece
taranmış PDF'lerde eskisi gibi None/boş kalır.

── DOĞRULUK SINIRI (KRİTİK, Kural 1/2/3 ile DOĞRUDAN İLGİLİ) ──
CANLI test edildi (KPEKS Fiyat Tespit Raporu, sayfa 11 -- ortaklık yapısı
tablosu): OCR, DÜZ METİN/cümle içeriğinde (sektör açıklaması, taahhüt
paragrafları, tarih/eşik cümleleri) iyi sonuç veriyor, ama YOĞUN SAYISAL
TABLOLARDA (bilanço/gelir tablosu gibi çok kolonlu ızgaralar) sütun
hizası bozulup rakamlar KAYIYOR/KARIŞIYOR (örn. "%5" -> "965", "19,25" ->
"1925" gibi CANLI gözlemlenen hatalar). Bu YÜZDEN bu modül BİLİNÇLİ olarak
SADECE düz metin/cümle tabanlı alanlar için kullanılır (örn. Yüksek
Başvuru eşiği cümlesi, fiyat istikrarı/taahhüt paragrafları) -- Fiyat
Tespit Raporu'nun BİLANÇO/GELİR TABLOSU gibi çok kolonlu sayısal
tablolarını OCR'dan TÜRETMEK bu modülün kapsamı DIŞINDA bırakılmıştır
(yanlış rakam riski, Kural 3: "emin değilsen None bırak, yanlış rakamdan
iyidir").
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_TESSDATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "tessdata"
_TESSERACT_CMD_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)
_LANG = "tur"
_DEFAULT_DPI = 200
# latans butcesi -- ~6 sn/sayfa CANLI olculdu. 2026-08-07 (otuz birinci tur)
# CANLI GOZLEMLENDI: KPEKS/VEYAS ile 25 sayfa (~2,5 dk/parca) denendi, HER
# IKI ornekte de -- kucuk (birkac sayfalik) eklerde YENI bilgi vermedi,
# BUYUK (50-160 sayfalik) ana belgelerde hedef bolume (Sulanma Etkisi
# Analizi/Tahsisat) ULASAMADI (bilinmeyen sayfa konumu) -- SADECE latansi
# artirdi (bir kartta toplam ~4-8 dk EK sure). 8'e dusuruldu: KISA (birkac
# sayfalik) eklerde hala TAM taranir (deger BURADA), BUYUK belgelerde
# "korlemesine tara" stratejisinden vazgecilip (Kural 9 ruhu -- ikincil
# veri, ana pipeline'i agir sekilde YAVASLATMAMALI) halkarz.com fallback'ine
# guvenilir.
_MAX_OCR_PAGES = 8
_PDFPLUMBER_TEXT_THRESHOLD = 300  # bu esigin ALTINDAKI toplam metin "taranmis/OCR gerekli" sayilir


def is_available() -> bool:
    """Tesseract binary'si + Türkçe dil paketi mevcut mu? Kural 9: eksikse
    çağıran taraf OCR'ı hiç DENEMEZ, sessizce eski (pdfplumber-only)
    davranışa döner."""
    tessdata_ready = (_PROJECT_TESSDATA_DIR / f"{_LANG}.traineddata").is_file()
    tesseract_ready = any(Path(candidate).is_file() for candidate in _TESSERACT_CMD_CANDIDATES)
    return tessdata_ready and tesseract_ready


def _configure_pytesseract() -> None:
    import pytesseract

    for candidate in _TESSERACT_CMD_CANDIDATES:
        if Path(candidate).is_file():
            pytesseract.pytesseract.tesseract_cmd = candidate
            break
    os.environ["TESSDATA_PREFIX"] = str(_PROJECT_TESSDATA_DIR)


def ocr_pdf_text(pdf_bytes: bytes, max_pages: int = _MAX_OCR_PAGES, dpi: int = _DEFAULT_DPI) -> str:
    """Taranmış bir PDF'in ilk `max_pages` sayfasını görüntüye çevirip
    Türkçe OCR ile düz metne çevirir. HERHANGİ bir hata durumunda (Kural 9
    -- bu bir İKİNCİL/yedek yol) sessizce boş string döner, İSTİSNA
    fırlatmaz -- çağıran taraf zaten pdfplumber sonucunu (muhtemelen boş)
    kullanmaya devam edebilir."""
    if not is_available():
        logger.info("OCR yedeği atlanıyor -- Tesseract binary'si veya '%s' dil paketi bulunamadı.", _LANG)
        return ""
    try:
        import fitz  # PyMuPDF -- poppler gibi ayrı bir sistem ikili dosyası GEREKTİRMEZ
        import pytesseract
        from PIL import Image

        _configure_pytesseract()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            parts: list[str] = []
            for page_index in range(min(max_pages, doc.page_count)):
                page = doc[page_index]
                # Sayfa ZATEN gerçek bir metin katmanı taşıyorsa (kısmen
                # taranmış belgelerde olur) OCR'a hiç GEREK YOK -- hem
                # daha hızlı hem daha DOĞRU (Kural 3).
                native_text = page.get_text()
                if len(native_text.strip()) > 40:
                    parts.append(native_text)
                    continue
                pix = page.get_pixmap(dpi=dpi)
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                parts.append(pytesseract.image_to_string(image, lang=_LANG))
            return "\n".join(parts)
        finally:
            doc.close()
    except Exception:  # noqa: BLE001 -- Kural 9: OCR ikincil bir yoldur, hata TÜM ayrıştırmayı ÇÖKERTMEMELİ
        logger.warning("PDF OCR yedeği başarısız oldu, boş metinle devam ediliyor.", exc_info=True)
        return ""


def extract_text_with_ocr_fallback(pdf_bytes: bytes, pdfplumber_text: str, max_pages: int = _MAX_OCR_PAGES) -> str:
    """`pdfplumber_text` (çağıranın ZATEN `pdfplumber` ile ürettiği metin)
    `_PDFPLUMBER_TEXT_THRESHOLD`'un ALTINDAYSA (taranmış/OCR'siz belge
    belirtisi) OCR yedeğini dener ve OCR metnini döner; ÜSTÜNDEYSE
    `pdfplumber_text`'i OLDUĞU GİBİ döner (gereksiz/yavaş OCR'dan kaçınır).
    OCR de boş dönerse (Kural 9) yine `pdfplumber_text` (muhtemelen boş)
    döner -- çağıran tarafın davranışı DEĞİŞMEZ, sadece bir şans daha
    verilmiş olur."""
    if len(pdfplumber_text.strip()) >= _PDFPLUMBER_TEXT_THRESHOLD:
        return pdfplumber_text
    ocr_text = ocr_pdf_text(pdf_bytes, max_pages=max_pages)
    return ocr_text if len(ocr_text.strip()) > len(pdfplumber_text.strip()) else pdfplumber_text
