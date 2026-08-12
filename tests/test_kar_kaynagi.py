"""src/ai/kar_kaynagi.py testleri -- docs/spec/spec_veri_tamlik_yol_haritasi.md
§Faaliyet Raporu / Dipnot Araştırması.

Gerçek KAP/Gemini ağ isteği ATILMAZ -- `kap.fetch_latest_annual_report_pdf`,
`pdf_ocr.extract_native_pages` ve `commentary.call_llm_json` monkeypatch ile
sahtelenir (bu üç fonksiyonun KENDİ testleri -- test_kap.py/test_pdf_ocr.py/
test_commentary.py -- ayrı dosyalarda zaten var, burada SADECE bu modülün
KENDİ orkestrasyon/seçim mantığı test edilir).
"""

from __future__ import annotations

from datetime import datetime

import config
from src.ai import kar_kaynagi
from src.fetchers import kap


def _disclosure(index: int = 1) -> kap.Disclosure:
    return kap.Disclosure(
        date=datetime(2026, 3, 4), title="2025 Faaliyet Raporu", category="Faaliyet Raporu (Konsolide)",
        summary="2025 Faaliyet Raporu", url="https://kap.org.tr/tr/Bildirim/1566094",
        importance=kap.IMPORTANCE_LOW, is_late=False, disclosure_index=index, stock_codes="THYAO",
    )


# --- _select_relevant_text -----------------------------------------------------


def test_select_relevant_text_ilgisiz_sayfalari_disarida_birakir() -> None:
    pages = ["Kapak sayfası, içindekiler, marka hikayesi.", "Bu dönem net dönem kârı ve faiz gideri artışı görüldü."]
    result = kar_kaynagi._select_relevant_text(pages)
    assert "faiz gideri" in result
    assert "marka hikayesi" not in result


def test_select_relevant_text_orijinal_sayfa_sirasi_korunur() -> None:
    pages = [
        "Ar-Ge harcamaları bu dönem arttı.",       # sayfa 0 -- 1 anahtar kelime
        "Kapak.",                                    # sayfa 1 -- alakasız
        "Net dönem kârı ve faiz gideri ve risk ve belirsizlik.",  # sayfa 2 -- birden çok anahtar kelime
    ]
    result = kar_kaynagi._select_relevant_text(pages)
    # skor sırasına göre SAYFA 2 önce seçilir ama BİRLEŞTİRİLİRKEN orijinal
    # sıraya (0, sonra 2) göre dizilir -- "Ar-Ge" metni "Net dönem"den ÖNCE gelmeli.
    assert result.index("Ar-Ge harcamaları") < result.index("Net dönem kârı")


def test_select_relevant_text_hic_eslesme_yoksa_bos_string() -> None:
    pages = ["Alakasız kapak metni.", "Şirket kültürü ve marka hikayesi."]
    assert kar_kaynagi._select_relevant_text(pages) == ""


def test_select_relevant_text_karakter_butcesini_asmaz() -> None:
    pages = ["net dönem kârı " * 2000]
    result = kar_kaynagi._select_relevant_text(pages, max_chars=500)
    assert len(result) <= 500


# --- KarKaynagiBulgulari.to_dict/from_dict -----------------------------------------------------


def test_bulgular_to_dict_from_dict_round_trip() -> None:
    bulgular = kar_kaynagi.KarKaynagiBulgulari(
        kaynak_baslik="2025 Faaliyet Raporu", kaynak_tarih_display="04.03.2026",
        kaynak_url="https://kap.org.tr/tr/Bildirim/1566094",
        kar_kaynagi_ozeti="Kâr artışı satış hacminden kaynaklandı.",
        arge_yatirim_notu="Ar-Ge harcamaları %10 arttı.",
        faiz_finansman_notu="Faiz gideri kârı sınırlı etkiledi.",
        risk_faktorleri=["Kur riski", "Akaryakıt maliyeti"],
        source="llm",
    )
    geri = kar_kaynagi.KarKaynagiBulgulari.from_dict(bulgular.to_dict())
    assert geri.kaynak_baslik == bulgular.kaynak_baslik
    assert geri.risk_faktorleri == bulgular.risk_faktorleri
    assert geri.source == "llm"


def test_bulgular_from_dict_eksik_alanlarda_uydurma_yapmaz() -> None:
    geri = kar_kaynagi.KarKaynagiBulgulari.from_dict({})
    assert geri.kaynak_baslik == ""
    assert geri.risk_faktorleri == []
    assert geri.source == "fallback"


# --- analyze_kar_kaynagi -----------------------------------------------------


def test_analyze_kar_kaynagi_bildirim_bulunamazsa_none(monkeypatch) -> None:
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: None)
    assert kar_kaynagi.analyze_kar_kaynagi("THYAO") is None


def test_analyze_kar_kaynagi_kap_hatasinda_none(monkeypatch) -> None:
    def _patlar(ticker, days=365):
        raise kap.KapNetworkError("ağ hatası")

    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", _patlar)
    assert kar_kaynagi.analyze_kar_kaynagi("THYAO") is None


def test_analyze_kar_kaynagi_pdf_metni_cikarilamazsa_fallback(monkeypatch) -> None:
    disclosure = _disclosure()
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: (disclosure, b"%PDF-fake"))
    monkeypatch.setattr(kar_kaynagi.pdf_ocr, "extract_native_pages", lambda pdf_bytes, max_pages=200: [])

    sonuc = kar_kaynagi.analyze_kar_kaynagi("THYAO")

    assert sonuc is not None
    assert sonuc.source == "fallback"
    assert sonuc.kaynak_baslik == "2025 Faaliyet Raporu"
    assert "kullanılamıyor" in sonuc.kar_kaynagi_ozeti


def test_analyze_kar_kaynagi_ilgili_bolum_bulunamazsa_fallback(monkeypatch) -> None:
    disclosure = _disclosure()
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: (disclosure, b"%PDF-fake"))
    monkeypatch.setattr(kar_kaynagi.pdf_ocr, "extract_native_pages", lambda pdf_bytes, max_pages=200: ["kapak sayfası, alakasız metin"])

    sonuc = kar_kaynagi.analyze_kar_kaynagi("THYAO")

    assert sonuc is not None
    assert sonuc.source == "fallback"


def test_analyze_kar_kaynagi_api_anahtari_yoksa_fallback(monkeypatch) -> None:
    disclosure = _disclosure()
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: (disclosure, b"%PDF-fake"))
    monkeypatch.setattr(kar_kaynagi.pdf_ocr, "extract_native_pages", lambda pdf_bytes, max_pages=200: ["net dönem kârı bu dönem arttı"])
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")

    sonuc = kar_kaynagi.analyze_kar_kaynagi("THYAO")

    assert sonuc.source == "fallback"


def test_analyze_kar_kaynagi_basarili_llm_yanitini_kullanir(monkeypatch) -> None:
    disclosure = _disclosure()
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: (disclosure, b"%PDF-fake"))
    monkeypatch.setattr(kar_kaynagi.pdf_ocr, "extract_native_pages", lambda pdf_bytes, max_pages=200: ["net dönem kârı bu dönem arttı"])
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    def _fake_call_llm_json(user_prompt, *, system_instruction, response_schema):
        return {
            "kar_kaynagi_ozeti": "Kâr artışı satış hacminden kaynaklandı.",
            "arge_yatirim_notu": "Raporda bu konuda açık bir bilgi bulunmuyor.",
            "faiz_finansman_notu": "Faiz gideri kârı sınırlı etkiledi.",
            "risk_faktorleri": ["Kur riski", "Faiz riski", "Talep riski", "Maliyet riski", "5. madde -- kırpılmalı"],
        }

    monkeypatch.setattr(kar_kaynagi.commentary, "call_llm_json", _fake_call_llm_json)

    sonuc = kar_kaynagi.analyze_kar_kaynagi("THYAO")

    assert sonuc.source == "llm"
    assert sonuc.kar_kaynagi_ozeti == "Kâr artışı satış hacminden kaynaklandı."
    assert len(sonuc.risk_faktorleri) == 4  # en fazla 4 madde ile sınırlı
    assert sonuc.kaynak_url == disclosure.url


def test_analyze_kar_kaynagi_llm_hatasinda_fallback(monkeypatch) -> None:
    disclosure = _disclosure()
    monkeypatch.setattr(kap, "fetch_latest_annual_report_pdf", lambda ticker, days=365: (disclosure, b"%PDF-fake"))
    monkeypatch.setattr(kar_kaynagi.pdf_ocr, "extract_native_pages", lambda pdf_bytes, max_pages=200: ["net dönem kârı bu dönem arttı"])
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    def _patlar(user_prompt, *, system_instruction, response_schema):
        raise RuntimeError("gemini çöktü")

    monkeypatch.setattr(kar_kaynagi.commentary, "call_llm_json", _patlar)

    sonuc = kar_kaynagi.analyze_kar_kaynagi("THYAO")

    assert sonuc.source == "fallback"
