"""src/fetchers/pdf_ocr.py testleri -- 2026-08-07 (otuz birinci tur).

Kural 11: gerçek Tesseract/OCR çağrısı ATILMAZ -- bu makinede Tesseract
kurulu olsa bile (`is_available()` True dönebilir) testler `ocr_pdf_text`'i
monkeypatch'leyerek İZOLE eder, gerçek görüntü işleme/OCR süresi
testlere SIZMAZ.
"""

from __future__ import annotations

from src.fetchers import pdf_ocr


def test_is_available_dosyalar_yoksa_false(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(pdf_ocr, "_PROJECT_TESSDATA_DIR", tmp_path)
    monkeypatch.setattr(pdf_ocr, "_TESSERACT_CMD_CANDIDATES", (str(tmp_path / "yok.exe"),))

    assert pdf_ocr.is_available() is False


def test_extract_text_with_ocr_fallback_esik_ustundeyse_ocr_denenmez(monkeypatch) -> None:
    """`pdfplumber_text` zaten yeterince uzunsa OCR'a HİÇ gidilmemeli --
    hem gereksiz yavaşlık hem de OCR'ın kendi hatalarını (bkz. kap_ipo.py
    üst notu) riske atmamak için."""
    called = False

    def _fake_ocr(pdf_bytes: bytes, max_pages: int = 25) -> str:
        nonlocal called
        called = True
        return "OCR METNİ"

    monkeypatch.setattr(pdf_ocr, "ocr_pdf_text", _fake_ocr)

    uzun_metin = "gerçek metin " * 50  # >300 karakter
    result = pdf_ocr.extract_text_with_ocr_fallback(b"sahte-pdf-bytes", uzun_metin)

    assert called is False
    assert result == uzun_metin


def test_extract_text_with_ocr_fallback_esik_altindaysa_ocr_devreye_girer(monkeypatch) -> None:
    def _fake_ocr(pdf_bytes: bytes, max_pages: int = 25) -> str:
        return "OCR ile okunan çok daha uzun bir metin " * 20

    monkeypatch.setattr(pdf_ocr, "ocr_pdf_text", _fake_ocr)

    result = pdf_ocr.extract_text_with_ocr_fallback(b"sahte-pdf-bytes", "kısa")

    assert "OCR ile okunan" in result


def test_extract_text_with_ocr_fallback_ocr_de_bosgeri_donerse_pdfplumber_metni_korunur(monkeypatch) -> None:
    monkeypatch.setattr(pdf_ocr, "ocr_pdf_text", lambda pdf_bytes, max_pages=25: "")

    result = pdf_ocr.extract_text_with_ocr_fallback(b"sahte-pdf-bytes", "kısa metin")

    assert result == "kısa metin"


def test_ocr_pdf_text_tesseract_yoksa_bos_doner(monkeypatch) -> None:
    monkeypatch.setattr(pdf_ocr, "is_available", lambda: False)

    assert pdf_ocr.ocr_pdf_text(b"sahte-pdf-bytes") == ""


# --- extract_native_pages (docs/spec/spec_veri_tamlik_yol_haritasi.md
# §Faaliyet Raporu, 2026-08-12) ------------------------------------------


def _fake_pdf_bytes(page_texts: list[str]) -> bytes:
    """PyMuPDF'in KENDİSİYLE (fixture dosyası/reportlab GEREKMEDEN) minik,
    gerçek bir PDF üretir -- her sayfaya verilen metni yazar."""
    import fitz

    doc = fitz.open()
    try:
        for text in page_texts:
            page = doc.new_page()
            page.insert_text((72, 72), text)
        return doc.tobytes()
    finally:
        doc.close()


def test_extract_native_pages_her_sayfayi_ayri_string_olarak_doner() -> None:
    pdf_bytes = _fake_pdf_bytes(["Birinci Sayfa Metni", "Ikinci Sayfa Metni"])

    pages = pdf_ocr.extract_native_pages(pdf_bytes)

    assert len(pages) == 2
    assert "Birinci Sayfa" in pages[0]
    assert "Ikinci Sayfa" in pages[1]


def test_extract_native_pages_max_pages_sinirlar() -> None:
    pdf_bytes = _fake_pdf_bytes(["Sayfa 1", "Sayfa 2", "Sayfa 3"])

    pages = pdf_ocr.extract_native_pages(pdf_bytes, max_pages=2)

    assert len(pages) == 2


def test_extract_native_pages_gecersiz_pdfde_bos_liste_doner() -> None:
    assert pdf_ocr.extract_native_pages(b"gecersiz-bayt-dizisi") == []
