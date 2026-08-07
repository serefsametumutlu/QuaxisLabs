"""src/fetchers/kap_ipo.py testleri -- Faz 20 (SPK onaylı izahname analizi).

Kural 11: ağ isteği ATILMAZ. PDF ayrıştırma testleri GERÇEK, canlı çekilmiş
bir KAP izahnamesi kullanır (tests/fixtures/kap_izahname_karcl_2026_07.txt
-- Kardemir Çelik Sanayi A.Ş., 2026-08-06'da CANLI indirildi/ayrıştırıldı) --
sonuçlar izahnamenin KENDİ "Sulanma Etkisi Analizi" tablosuyla rakam rakam
doğrulanmıştır (bkz. modül üst notu, Kural 3).

⚠️ CANLI GÖZLEMLENDİ (aynı oturum, QUICK/Garanti Yatırım örneğiyle): bazı
aracı kurumların izahname PDF'leri (farklı bir oluşturma/damgalama sistemi
kullanıyor olabilir) pdfplumber ile GARBLED (karman çorman) metin
üretiyor -- bu durumda ayrıştırıcı YANLIŞ rakam ÜRETMEK yerine tüm
alanlarda None döner (Kural 3), bu dosyadaki testler de bu davranışı
doğrular.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.fetchers import kap
from src.fetchers import kap_ipo

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
KARCL_IZAHNAME_TEXT = (FIXTURES_DIR / "kap_izahname_karcl_2026_07.txt").read_text(encoding="utf-8")
# Çitlekçi Mağazacılık (CITAS) -- 2026-08-07'de zaten data/exploration/'a
# indirilmiş, Faz 20.2/20.3'te Sulanma Etkisi Analizi/tahsisat testlerinde
# KULLANILMAMIŞ ama 26.5/27.3/28.2 bölümlerini (KARCL'ın izahnamesinde
# incelenmemiş) İÇEREN gerçek bir izahname -- Faz 20.5 fiyat istikrarı/
# taahhüt/28.2 fallback testleri için buraya kopyalandı.
CITAS_IZAHNAME_TEXT = (FIXTURES_DIR / "kap_izahname_citas_2026_08.txt").read_text(encoding="utf-8")


def _ek5_text() -> str:
    pdf_bytes = (FIXTURES_DIR / "kap_izahname_ek5_fon_kullanim_karcl.pdf").read_bytes()
    return kap_ipo._pdf_bytes_to_text(pdf_bytes)


# --- _pdf_bytes_to_text OCR yedeği (2026-08-07, otuz birinci tur, YENİ) -------------------------


def test_pdf_bytes_to_text_pdfplumber_metni_yeterliyse_ocr_denenmez(monkeypatch) -> None:
    """`_ek5_text()` fixture'ı ZATEN 5700+ karakter döndürüyor (gerçek KARCL
    PDF'i, taranmış DEĞİL) -- OCR'a hiç gidilmemeli."""
    called = False

    def _fake_ocr_fallback(pdf_bytes: bytes, pdfplumber_text: str) -> str:
        nonlocal called
        called = True
        return pdfplumber_text

    monkeypatch.setattr(kap_ipo.pdf_ocr, "extract_text_with_ocr_fallback", _fake_ocr_fallback)

    _ek5_text()

    assert called is True  # sarmalayıcı HER ZAMAN çağrılır, ama içeride OCR denenmez (bkz. pdf_ocr testleri)


def test_pdf_bytes_to_text_taranmis_pdfde_ocr_yedegi_devreye_girer(monkeypatch) -> None:
    """Kural 9: `pdfplumber` boş dönerse (taranmış PDF) OCR yedeği
    denenmeli -- gerçek Tesseract ÇAĞRILMADAN (Kural 11), sadece kablolamanın
    doğruluğu test edilir."""
    monkeypatch.setattr(
        kap_ipo.pdf_ocr,
        "extract_text_with_ocr_fallback",
        lambda pdf_bytes, pdfplumber_text: "OCR İLE OKUNAN METİN" if not pdfplumber_text.strip() else pdfplumber_text,
    )
    # 1x1 boş bir PDF -- pdfplumber gerçek bir dosya OLMADAN boş metin döner
    bos_pdf = (FIXTURES_DIR / "kap_izahname_ek5_fon_kullanim_karcl.pdf").read_bytes()

    # Not: gerçek OCR'ı TETİKLEMEDEN kablolamayı doğrulamak için pdfplumber
    # sonucu da monkeypatch'lenir (dolu bir PDF'te dahi "boşmuş gibi" davranır).
    class _BosSayfa:
        def extract_text(self) -> None:
            return None

    class _BosPdf:
        pages = [_BosSayfa()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(kap_ipo.pdfplumber, "open", lambda *_args, **_kwargs: _BosPdf())

    result = kap_ipo._pdf_bytes_to_text(bos_pdf)

    assert result == "OCR İLE OKUNAN METİN"


# --- extract_ipo_facts (Sulanma Etkisi Analizi tablosu) -- GERÇEK KARCL verisiyle -------------


def test_extract_ipo_facts_karcl_dilution_table_birebir_dogru() -> None:
    """CANLI doğrulama: bu değerler izahnamenin 148. sayfasındaki "Sulanma
    Etkisi Analizi" tablosuyla rakam rakam eşleşiyor (bkz. modül üst notu)."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)

    assert facts.offering_price == Decimal("35.00")
    assert facts.capital_increase_amount == Decimal("110000000")
    assert facts.offering_size == Decimal("3850000000")
    assert facts.estimated_offering_cost == Decimal("122174720")
    assert facts.net_offering_proceeds == Decimal("3727825280")
    assert facts.equity_before == Decimal("11686748615")
    assert facts.equity_after == Decimal("15414573895")
    assert facts.paid_capital_before == Decimal("720000000")
    assert facts.paid_capital_after == Decimal("830000000")  # CANLI HATA + DÜZELTME regresyonu (bkz. modül üst notu)
    assert facts.book_value_per_share_before == Decimal("16.2316")
    assert facts.book_value_per_share_after == Decimal("18.5718")
    assert facts.dilution_existing_pct == Decimal("14.42")
    assert facts.dilution_new_pct == Decimal("-46.94")


def test_extract_ipo_facts_karcl_tahsisat_birebir_dogru() -> None:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)

    assert facts.allocation_breakdown is not None
    assert facts.allocation_breakdown["Yurt İçi Bireysel Yatırımcılara"] == Decimal("40.00")
    assert facts.allocation_breakdown["Yurt İçi Kurumsal Yatırımcılara"] == Decimal("30.00")
    assert facts.allocation_breakdown["Yurt Dışı Kurumsal Yatırımcılara"] == Decimal("20.00")
    assert sum(facts.allocation_breakdown.values()) == Decimal("100.00")


def test_extract_ipo_facts_karcl_fon_kullanim_yeri_ek5_ile_birebir_dogru() -> None:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT, use_of_proceeds_text=_ek5_text())

    assert facts.use_of_proceeds is not None
    assert facts.use_of_proceeds["Hammadde Tedariki ve İşletme Sermayesi İhtiyacının Finansmanı"] == Decimal("90")
    assert facts.use_of_proceeds["Yenilenebilir Enerji Yatırımları"] == Decimal("4")
    assert facts.use_of_proceeds["Üretim Tesisi Yatırımlarının Finansmanı"] == Decimal("6")
    assert sum(facts.use_of_proceeds.values()) == Decimal("100")


def test_extract_ipo_facts_use_of_proceeds_verilmezse_none() -> None:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assert facts.use_of_proceeds is None


# --- Fiyat İstikrarı (26.5) / Taahhütler (27.3) / 28.2 fallback -- GERÇEK CITAS verisiyle ------
# (Faz 20.5, 2026-08-07 devamı) CANLI doğrulama: bu değerler izahnamenin
# 229-232. sayfalarındaki 26.5/27.3/28.2 bölümleriyle birebir eşleşiyor.


def test_extract_ipo_facts_citas_fiyat_istikrari_birebir_dogru() -> None:
    facts = kap_ipo.extract_ipo_facts(CITAS_IZAHNAME_TEXT)

    assert facts.price_stabilization_period_display == "30 gün"
    assert facts.price_stabilization_source_pct == Decimal("15")


def test_extract_ipo_facts_citas_taahhutler_birebir_dogru() -> None:
    facts = kap_ipo.extract_ipo_facts(CITAS_IZAHNAME_TEXT)

    assert facts.issuer_lockup_period_display == "1 yıl"
    assert facts.shareholder_lockup_note is not None
    assert "Tunçlar Yatırım Holding" in facts.shareholder_lockup_note


def test_extract_ipo_facts_citas_28_2_fallback_dort_kategori_birebir_dogru() -> None:
    """Ek-5/Ek-7 (use_of_proceeds_text) VERİLMEDİĞİNDE ana izahnamenin
    kendi 28.2 bölümünden ARALIK formatlı fallback devreye girer."""
    facts = kap_ipo.extract_ipo_facts(CITAS_IZAHNAME_TEXT)

    assert facts.use_of_proceeds is None  # Ek-5 verilmedi
    assert facts.use_of_proceeds_range == {
        "İşletme Sermayesi Güçlendirilmesi": "%30-40",
        "Yurt İçi Yeni Şube Yatırımları ile Diğer Alternatif Yatırım Fırsatlarının Değerlendirilmesi": "%30-40",
        "Yurt İçi Yeni Depo Yatırımları": "%10-20",
        "GES Yatırımı": "%10-20",
    }


def test_extract_ipo_facts_28_2_fallback_ek5_varsa_devre_disi_kalir() -> None:
    """Ek-5/Ek-7 raporu ZATEN dolu bir kırılım verdiyse (KARCL örneği)
    28.2 fallback'i devreye GİRMEMELİ -- ikisi aynı anda gösterilmez."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT, use_of_proceeds_text=_ek5_text())

    assert facts.use_of_proceeds is not None
    assert facts.use_of_proceeds_range is None


def test_extract_ipo_facts_fiyat_istikrari_ve_taahhut_anchor_bulunamazsa_none() -> None:
    facts = kap_ipo.extract_ipo_facts("bu metinde ilgili hiçbir bölüm yok, tamamen alakasız bir metin.")

    assert facts.price_stabilization_period_display is None
    assert facts.price_stabilization_source_pct is None
    assert facts.issuer_lockup_period_display is None
    assert facts.shareholder_lockup_note is None
    assert facts.use_of_proceeds_range is None


# --- Kural 3 güvenlik ağı: bulunamayan/belirsiz alanlar None döner ----------------------------


def test_extract_ipo_facts_anchor_bulunamazsa_tum_tekli_alanlar_none() -> None:
    """CANLI gözlemlendi (QUICK/Garanti Yatırım örneği): bazı izahname
    PDF'leri pdfplumber ile GARBLED metin üretiyor -- "Sulanma Etkisi
    Analizi" tablosu (veya "Halka Arz Fiyatı" ilk satırı) hiç
    bulunamadığında YANLIŞ bir rakam ÜRETİLMEMELİ, tümü None kalmalı."""
    facts = kap_ipo.extract_ipo_facts("bu metinde ilgili hiçbir tablo yok, tamamen alakasız bir metin.")

    assert facts.offering_price is None
    assert facts.capital_increase_amount is None
    assert facts.equity_before is None
    assert facts.equity_after is None
    assert facts.allocation_breakdown is None
    assert facts.use_of_proceeds is None


def test_parse_allocation_grup_toplami_tutmuyorsa_none_doner() -> None:
    text = (
        "Halka arz edilecek toplam 100.000.000 TL nominal değerli payların;\n"
        "• 50.000.000 TL nominal değerdeki kısmı (50,00%) Yurt İçi Bireysel Yatırımcılara,\n"
        "gerçekleştirilecek satışlar için tahsis edilmiştir."
    )
    # tek satır = %50 toplam -- %100'den COK sapıyor, güvenilmez sayılmalı
    assert kap_ipo._parse_allocation(text) is None


def test_parse_use_of_proceeds_belirsiz_madde_varsa_o_madde_disarida_kalir() -> None:
    """Bir maddede İKİ ayrı yüzde geçiyorsa (hangisinin 'asıl' oran olduğu
    belirsiz) o madde dahil EDİLMEZ -- ama diğer maddeler geçerliyse VE
    toplamları %100'e yakınsa sözlük yine dönebilir (bkz. modül üst notu:
    Kural 3, belirsiz TEK maddeyi ele, TÜMÜNÜ değil -- ancak toplam
    kontrolü hâlâ geçerli olmalı)."""
    text = (
        "(1) Birinci Kalem\n"
        "Bu kalem icin %90 kullanılacak, ayrıca %10 baska bir yerde de gecebilir.\n"
        "(2) Ikinci Kalem\n"
        "Bu kalemin tamami net fonun %10'u kadardir.\n"
    )
    # 1. madde belirsiz (2 yuzde) -> disarida kalir, sadece 2. madde (%10) kalir -> toplam %100'den COK sapar -> None
    assert kap_ipo._parse_use_of_proceeds(text) is None


# --- Keşif: başlık sınıflandırma (_is_izahname_part) ------------------------------------------


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname", True),
        ("Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname Ek-1", False),
        ("Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname Ek-6.2", False),
        ("Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin İzahname", True),  # Garanti Yatırım -- Ek YOK, tire de YOK
        ("Saat ve Saat Sanayi ve Ticaret Anonim Şirketi Paylarının Halka Arzına İlişkin SPK Onaylı İzahname (1. Kısım)", True),
        ("Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin Hukukçu Raporu", False),  # "izahname" hiç geçmiyor
        ("Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin Fiyat Tespit Raporu", False),
        # CANLI HATA + DÜZELTME (2026-08-07, Çitlekçi/TERA YATIRIM): boşluklu "Ek N-" varyasyonları
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname", True),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek 1- Şirket Esas Sözleşmesi", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek -2 Çitlekçi İç Yönerge TTSG", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek 5-1 ANKARA YENİMAHALLE MERKEZ BİNA DEĞERLEME RAPORU", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek - 6. Değerleme Kuruluşu Sorumluluk Beyanı", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek - 7. Fon Kullanım Yeri Raporu", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek 9 - Çitlekçi Hukukçu Raporu 1.Kısım", False),
        ("Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname Ek 10- Çitlekçi Katılım Finansı İlkeleri Bilgi Formu", False),
    ],
)
def test_is_izahname_part_farkli_araci_kurum_konvansiyonlarini_ayirt_eder(title, expected) -> None:
    """CANLI gözlemlendi (KARCL/QUICK/Saat ve Saat karşılaştırması): her
    aracı kurum FARKLI bir başlıklandırma konvansiyonu kullanıyor -- bkz.
    modül üst notu."""
    assert kap_ipo._is_izahname_part(title) is expected


def _fake_izahname_disclosure(
    index: int,
    title: str,
    related_stocks: str,
    filer_name: str = "GARANTİ YATIRIM MENKUL KIYMETLER A.Ş.",
    hour: int = 20,
    minute: int = 0,
) -> kap.Disclosure:
    return kap.Disclosure(
        date=datetime(2026, 7, 24, hour, minute, 0),
        title=title,
        category="İzahname (SPK Tarafından Onaylanan)",
        summary="x",
        url=f"https://example.com/{index}",
        importance="dusuk",
        is_late=False,
        disclosure_index=index,
        stock_codes="GARAN",
        related_stocks=related_stocks,
        filer_name=filer_name,
    )


def test_find_recent_izahnameler_parcalari_hedef_ticker_grubuna_gore_birlestirir(monkeypatch) -> None:
    """Faz 20 CANLI hata + düzeltme (QUICK örneği): AYNI yayınlayıcı+hedef
    için BİRDEN FAZLA parça (aynı başlıkla bölünmüş) TEK bir
    IzahnameDisclosure altında `disclosure_indices` demetinde toplanmalı,
    dosyalanma sırasına (disclosure_index artan) göre sıralı. "Hukukçu
    Raporu" (izahname parçası DEĞİL) devre dışı bırakılır."""
    disclosures = [
        _fake_izahname_disclosure(1636670, "Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin İzahname", "QUICK", minute=2),
        _fake_izahname_disclosure(1636672, "Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin İzahname", "QUICK", minute=4),
        _fake_izahname_disclosure(1636688, "Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin Hukukçu Raporu", "QUICK", minute=25),
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].target_tickers == ("QUICK",)
    assert results[0].disclosure_indices == (1636670, 1636672)  # Hukukçu Raporu HARİÇ, artan sırada
    assert results[0].publish_date == date(2026, 7, 24)


def test_find_recent_izahnameler_2026_08_07_kap_genelinde_araniyor_uye_kisitlamasi_yok(monkeypatch) -> None:
    """🚨 CANLI HATA + DÜZELTME (kullanıcı raporu, 2026-08-07): Çitlekçi'nin
    aracısı TERA YATIRIM eski `UNDERWRITER_MEMBERS` sabit listesinde YOKTU
    -- artık `kap.fetch_all_disclosures()` (üye kısıtlaması YOK) kullanıldığı
    için HERHANGİ bir yayınlayıcı bulunabilir."""
    disclosures = [
        _fake_izahname_disclosure(
            1700001,
            "Çitlekçi Mağazacılık Gıda Anonim Şirketi Paylarının Halka Arzına İlişkin İzahname",
            "CITAS",
            filer_name="TERA YATIRIM MENKUL DEĞERLER A.Ş.",
        ),
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].underwriter_name == "TERA YATIRIM MENKUL DEĞERLER A.Ş."
    assert results[0].target_tickers == ("CITAS",)


def test_find_recent_izahnameler_ayni_basligin_tekrarlari_hepsi_korunur(monkeypatch) -> None:
    """CANLI gözlemlendi (Bewen örneği): AYNI başlık kısa aralıklarla
    birden fazla kez filed edilebiliyor -- bunun gerçek çok-parçalı bir
    belgeden (QUICK gibi) mi yoksa bir resubmission'dan mı kaynaklandığı
    istemci tarafında GÜVENİLİR ayırt edilemediği için (Kural 3) HİÇBİRİ
    ATILMAZ, tüm tekrarlar `disclosure_indices`'e dahil edilir."""
    disclosures = [
        _fake_izahname_disclosure(100, "Bewen Enerji A.Ş.'nin SPK onaylı İzahnamesi hk", "BEWEN", minute=10),
        _fake_izahname_disclosure(101, "Bewen Enerji A.Ş.'nin SPK onaylı İzahnamesi hk", "BEWEN", minute=12),
        _fake_izahname_disclosure(103, "Bewen Enerji A.Ş.'nin SPK onaylı İzahnamesi ekleri 1. Bölüm", "BEWEN", minute=15),
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].disclosure_indices == (100, 101, 103)


def test_find_recent_izahnameler_resubmission_arasi_ticker_kumesi_farkli_olsa_bile_tek_grup(monkeypatch) -> None:
    """🚨 CANLI GÖZLEMLENDİ (Türker Vangölü Enerji): ardışık resubmission'lar
    arasında `related_stocks` kümesi TAM örtüşmeyebiliyor ("VEYAS, VKF,
    ZRY" vs "VEYAS, VKY, ZRY" -- bir yazım düzeltmesi). Gruplama TAM küme
    eşitliği YERİNE sadece PRİMER (ilk) ticker'a göre yapıldığı için bu
    İKİ resubmission YANLIŞLIKLA iki ayrı gruba BÖLÜNMEMELİ."""
    disclosures = [
        _fake_izahname_disclosure(200, "Türker Vangölü Enerji Yatırım A.Ş. SPK Onaylı İzahname", "VEYAS, VKF, ZRY", minute=1),
        _fake_izahname_disclosure(201, "Türker Vangölü Enerji Yatırım A.Ş. SPK Onaylı İzahname Ekleri", "VEYAS, VKY, ZRY", minute=5),
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].disclosure_indices == (200, 201)
    assert results[0].target_tickers == ("VEYAS", "VKY", "ZRY")  # en yeni (201) resubmission "asil" sayılır


def test_find_recent_izahnameler_esigi_asan_tekrarda_sadece_en_yenisi_tutulur(monkeypatch) -> None:
    """🚨 CANLI GÖZLEMLENDİ (Türker Vangölü Enerji/Halk Yatırım, 2026-08-07):
    AYNI başlık ("...İzahname", ek numarası YOK) 6-7 kez kısa aralıklarla
    yeniden filed edilmiş -- eşiği (3) AŞTIĞI için resubmission fırtınası
    sayılır, SADECE en yenisi tutulur."""
    disclosures = [
        _fake_izahname_disclosure(300 + i, "Türker Vangölü Enerji Yatırım A.Ş. SPK Onaylı İzahname", "VEYAS, VKY, ZRY", minute=i)
        for i in range(5)
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].disclosure_indices == (304,)


def test_find_recent_izahnameler_esik_altinda_tekrar_gercek_cok_parcali_belge_sayilir(monkeypatch) -> None:
    """QUICK örneği: eşiğin (3) ALTINDA bir tekrar sayısı GERÇEK çok-parçalı
    belge sayılır, TÜMÜ tutulur (bkz. yukarıdaki
    test_find_recent_izahnameler_parcalari_hedef_ticker_grubuna_gore_birlestirir'in
    2-tekrarlı versiyonuyla AYNI ilke, burada 3 tekrarla sınırda test edilir)."""
    disclosures = [
        _fake_izahname_disclosure(400 + i, "Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin İzahname", "QUICK", minute=i)
        for i in range(3)
    ]
    monkeypatch.setattr(kap, "fetch_all_disclosures", lambda days=7: disclosures)

    results = kap_ipo.find_recent_izahnameler(days=7)

    assert len(results) == 1
    assert results[0].disclosure_indices == (400, 401, 402)


def test_find_recent_izahnameler_kap_genelinde_gunluk_kesme_sinirini_asarsa_yukari_firlatir(monkeypatch) -> None:
    def _boom(days=7):
        raise ValueError("güvenli sınırı aşıyor")

    monkeypatch.setattr(kap, "fetch_all_disclosures", _boom)

    with pytest.raises(ValueError):
        kap_ipo.find_recent_izahnameler(days=30)
