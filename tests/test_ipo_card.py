"""src/render/ipo_card.py testleri -- Faz 20 devamı.

Kural 11: context builder testleri ağ isteği ATMAZ (GERÇEK KARCL fixture
metniyle, tests/test_kap_ipo.py ile PAYLAŞILIR). SADECE
test_render_ipo_card_gercek_png_uretir GERÇEK Playwright render'i doğrular
(calendar_card.py/card.py'deki AYNI desen).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from src.analysis import ipo_assessment
from src.fetchers import kap_ipo
from src.fetchers import ipo_price_report
from src.fetchers.ipo_broker_page import SupplementaryIpoInfo
from src.render import card, ipo_card

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
KARCL_IZAHNAME_TEXT = (FIXTURES_DIR / "kap_izahname_karcl_2026_07.txt").read_text(encoding="utf-8")
CITAS_IZAHNAME_TEXT = (FIXTURES_DIR / "kap_izahname_citas_2026_08.txt").read_text(encoding="utf-8")
VEYAS_PRICE_REPORT_TEXT = (FIXTURES_DIR / "veyas_fiyat_tespit_raporu_2026_05.txt").read_text(encoding="utf-8")

_NOW = datetime(2026, 8, 6, 12, 0)


def _karcl_disclosure() -> kap_ipo.IzahnameDisclosure:
    return kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1636670,),
        publish_date=date(2026, 7, 17),
        underwriter_name="A1 CAPİTAL YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=("KARCL",),
        summary="Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname",
    )


def _karcl_context() -> dict:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    return ipo_card.build_ipo_card_context(_karcl_disclosure(), facts, assessment, now=_NOW)


# --- _derive_company_name ------------------------------------------------


def test_derive_company_name_ek_yok_konvansiyonu() -> None:
    assert ipo_card._derive_company_name("Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname") == "Kardemir Çelik Sanayi AŞ"


def test_derive_company_name_paylarinin_konvansiyonu() -> None:
    assert ipo_card._derive_company_name("Quick Sigorta A.Ş. Paylarının Halka Arzına İlişkin İzahname") == "Quick Sigorta A.Ş."


def test_derive_company_name_hicbir_desen_eslesmezse_ham_baslik_doner() -> None:
    assert ipo_card._derive_company_name("Alakasız Bir Başlık") == "Alakasız Bir Başlık"


def test_derive_company_name_spk_onayli_izahname_konvansiyonu() -> None:
    """VEYAS ile CANLI bulundu (2026-08-07): bazı başlıklarda "Halka Arz"
    kelimesi hiç geçmez, doğrudan "... SPK Onaylı İzahname" ile biter."""
    assert (
        ipo_card._derive_company_name("Türker Vangölü Enerji Yatırım A.Ş. SPK Onaylı İzahname")
        == "Türker Vangölü Enerji Yatırım A.Ş."
    )


def test_derive_company_name_iyelik_eki_temizlenir() -> None:
    """Kapeks ile CANLI bulundu (2026-08-07): "A.Ş.'nin SPK Onaylı
    İzahnamesi hk" gibi başlıklarda iyelik eki ("'nin") şirket adının
    parçası gibi görünüp kalıyordu."""
    assert (
        ipo_card._derive_company_name("Kapeks Kimya Sanayi A.Ş.'nin SPK onaylı İzahnamesi hk")
        == "Kapeks Kimya Sanayi A.Ş."
    )
    assert (
        ipo_card._derive_company_name("Bewen Enerji A.Ş.'nin SPK onaylı İzahnamesi hk")
        == "Bewen Enerji A.Ş."
    )


# --- build_ipo_card_context (GERÇEK KARCL verisiyle) ----------------------


def test_build_ipo_card_context_karcl_temel_alanlar() -> None:
    context = _karcl_context()

    assert context["company_name"] == "Kardemir Çelik Sanayi AŞ"
    assert context["primary_ticker"] == "KARCL"
    assert context["other_tickers_display"] is None
    assert context["offering_price_display"] == "35,00 TL"
    assert context["has_capital_split"] is True
    assert context["is_pure_capital_increase"] is True
    assert context["capital_increase_pct_display"] == "%100,0"


def test_build_ipo_card_context_karcl_tahsisat_dort_satir() -> None:
    context = _karcl_context()
    labels = {row["label"] for row in context["allocation_rows"]}
    assert labels == {"Yurt İçi Bireysel", "Yurt İçi Kurumsal", "Yurt Dışı Kurumsal", "Yüksek Başvurulu Yatırımcı"}
    assert context["is_allocation_empty"] is False


def test_build_ipo_card_context_fon_kullanim_yeri_verilmezse_bos() -> None:
    context = _karcl_context()
    assert context["is_use_of_proceeds_empty"] is True
    assert context["use_of_proceeds_rows"] == []


def test_build_ipo_card_context_diger_ticker_gosterilir() -> None:
    disclosure = kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1,),
        publish_date=date(2026, 7, 17),
        underwriter_name="A1 CAPİTAL YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=("KARCL", "VKY", "ZRY"),
        summary="Kardemir Çelik Sanayi AŞ Halka Arzına İlişkin Onaylı İzahname",
    )
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    context = ipo_card.build_ipo_card_context(disclosure, facts, assessment, now=_NOW)
    assert context["other_tickers_display"] == "VKY, ZRY"


def test_build_ipo_card_context_lot_sayilari_satirlarda_gorunur() -> None:
    """Referans görsel isteği (2026-08-07): her dağıtım grubunun lot
    sayısı da gösterilmeli -- KARCL: toplam 110.000.000 lot, bireysel %40
    -> 44.000.000."""
    context = _karcl_context()
    assert context["total_lot_display"] == "110.000.000"
    retail_row = next(row for row in context["allocation_rows"] if row["label"] == "Yurt İçi Bireysel")
    assert retail_row["lot_display"] == "44.000.000"


def test_build_ipo_card_context_tahmini_dagitim_doldurulur() -> None:
    context = _karcl_context()
    assert context["is_estimated_distribution_empty"] is False
    row_500k = next(r for r in context["estimated_distribution_rows"] if r["participants_display"] == "500.000")
    assert row_500k["lot_display"] == "88"


def test_build_ipo_card_context_supplementary_verilmezse_halkarz_alanlari_gizli() -> None:
    """Kullanıcı isteği (2026-08-07): halkarz.com bulunamazsa/verilmezse
    o KAYNAĞA özgü alanlar N/A GÖSTERİLMEZ, tamamen gizlenir. ⚠️ Faz 20.5
    (2026-08-07 devamı) ile `has_quick_info` ARTIK SADECE halkarz.com'a
    bağlı DEĞİL -- KARCL'ın izahnamesi 27.3 bölümünde GERÇEK bir "İhraççı
    Taahhüdü" (1 yıl) içeriyor, bu PRİMER kaynak (izahname) supplementary
    OLMADAN da has_quick_info'yu True yapar (eski test varsayımı artık
    GEÇERSİZ, bkz. issuer_lockup_period_display)."""
    context = _karcl_context()
    assert context["demand_period_display"] is None
    assert context["participation_compliant"] is None
    assert context["has_quick_info"] is True
    assert context["issuer_lockup_period_display"] == "1 yıl"


def test_build_ipo_card_context_supplementary_verilirse_quick_info_dolar() -> None:
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    supplementary = SupplementaryIpoInfo(
        demand_period_display="10-11-12 Ağustos 2026",
        demand_period_hours="09:00-17:00",
        participation_index_compliant=True,
        participation_index_name="XKTUM",
        price_stabilization_note="30 gün.",
        sales_method_note="Sabit Fiyatla Talep Toplama.",
        source_url="https://halkarz.com/ornek/",
    )
    context = ipo_card.build_ipo_card_context(_karcl_disclosure(), facts, assessment, now=_NOW, supplementary=supplementary)
    assert context["has_quick_info"] is True
    assert context["demand_period_display"] == "10-11-12 Ağustos 2026"
    assert context["participation_compliant"] is True
    assert context["has_supplementary_source"] is True


def test_build_ipo_card_context_izahname_okunamazsa_halkarz_fallback_devreye_girer() -> None:
    """VEYAS ile CANLI bulundu (2026-08-07, kullanıcı raporu: "hiçbir bilgi
    çıkmadı"): izahname PDF'i taranmış/OCR'siz olduğunda facts/assessment
    TAMAMEN None kalır -- bu durumda halkarz.com'un DÜZ METİN rakamları
    (fiyat/lot/dağıtım/tahmini dağıtım) FALLBACK olarak kullanılmalı ve
    "kaynak: halkarz.com" ile işaretlenmeli."""
    facts = kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    supplementary = SupplementaryIpoInfo(
        demand_period_display="12-13-14 Ağustos 2026",
        demand_period_hours="09:00-17:00",
        participation_index_compliant=False,
        participation_index_name=None,
        price_stabilization_note=None,
        sales_method_note=None,
        source_url="https://halkarz.com/veyas-ornek/",
        offering_price_text="136,00 TL",
        total_lot_text="65.000.000",  # ipo_broker_page zaten "Lot" birimini ayıklıyor
        distribution_method_text="Eşit Dağıtım",
        allocation_lines=("Yurt İçi Bireysel Yatırımcı: %45 (29.250.000 Lot)",),
        estimated_retail_distribution=((500_000, Decimal("58"), Decimal("7888")),),
        capital_increase_pct_fallback=Decimal("57.7"),
        partner_sale_pct_fallback=Decimal("42.3"),
        is_pure_capital_increase_fallback=False,
    )
    context = ipo_card.build_ipo_card_context(_karcl_disclosure(), facts, assessment, now=_NOW, supplementary=supplementary)

    assert context["offering_price_display"] == "136,00 TL"
    assert context["offering_price_is_fallback"] is True
    assert context["total_lot_display"] == "65.000.000"
    assert context["total_lot_is_fallback"] is True
    assert context["allocation_fallback_lines"] == ("Yurt İçi Bireysel Yatırımcı: %45 (29.250.000 Lot)",)
    assert context["estimated_distribution_is_fallback"] is True
    assert context["estimated_distribution_rows"][0]["participants_display"] == "500.000"
    assert context["capital_split_is_fallback"] is True
    assert context["capital_increase_pct_display"] == "%57,7"


def test_build_ipo_card_context_izahname_okunabiliyorsa_fallback_devreye_girmez() -> None:
    """Gerçek bir KAP rakamı VARSA (KARCL) halkarz.com fallback'i ASLA
    devreye girmemeli/üzerine yazmamalı."""
    context = _karcl_context()
    assert context["offering_price_is_fallback"] is False
    assert context["total_lot_is_fallback"] is False
    assert context["allocation_fallback_lines"] is None


# --- build_ipo_share_text -------------------------------------------------


def test_build_ipo_share_text_temel_alanlari_icerir() -> None:
    context = _karcl_context()
    text = ipo_card.build_ipo_share_text(context)
    assert "Kardemir Çelik Sanayi AŞ (KARCL)" in text
    assert "35,00 TL" in text
    assert "Yurt İçi Bireysel" in text
    assert "yatırım tavsiyesi değildir" in text
    assert "@QuaxisLabs" in text


# --- build_ipo_analysis_text -----------------------------------------------


def test_build_ipo_analysis_text_temel_alanlari_icerir() -> None:
    context = _karcl_context()
    text = ipo_card.build_ipo_analysis_text(context)
    assert "Kardemir Çelik Sanayi AŞ" in text
    assert "yatırım tavsiyesi değildir" in text
    assert "@QuaxisLabs" in text


def test_build_ipo_analysis_text_fiyat_buyukluk_yoksa_anlamsiz_cumle_kurmaz() -> None:
    """VEYAS ile CANLI bulundu (2026-08-07): izahname PDF'i taranmış/OCR'siz
    olduğunda (§B31) fiyat/büyüklük/lot ÜÇÜ DE None kalır -- "- Lot'un - fiyatla
    satışıyla" gibi anlamsız bir cümle KURULMAMALI, paragraf atlanmalı."""
    disclosure = kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1,),
        publish_date=date(2026, 8, 7),
        underwriter_name="HALK YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=("VEYAS",),
        summary="Türker Vangölü Enerji Yatırım A.Ş. SPK Onaylı İzahname",
    )
    facts = kap_ipo.IpoFacts(
        offering_price=None, capital_increase_amount=None, offering_size=None,
        estimated_offering_cost=None, net_offering_proceeds=None,
        equity_before=None, equity_after=None,
        paid_capital_before=None, paid_capital_after=None,
        book_value_per_share_before=None, book_value_per_share_after=None,
        dilution_existing_pct=None, dilution_new_pct=None,
        allocation_breakdown=None, use_of_proceeds=None,
    )
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    context = ipo_card.build_ipo_card_context(disclosure, facts, assessment, now=_NOW)
    text = ipo_card.build_ipo_analysis_text(context)
    assert "Lot'un" not in text
    assert "- fiyatla" not in text


def test_build_ipo_analysis_text_birinci_sahis_kanaat_uretmez() -> None:
    """Bilinçli tasarım kararı (2026-08-07): bu metin kullanıcının paylaştığı
    örnekteki gibi ("ben inandırıcı bulmadım" tarzı) BİRİNCİ ŞAHIS kişisel bir
    yatırım kanaati ÜRETMEMELİ -- sadece hesaplanmış rakamların nötr anlatısı."""
    context = _karcl_context()
    text = ipo_card.build_ipo_analysis_text(context).lower()
    for forbidden in (" bence ", " ben ", "düşünüyorum", "kanaatimce", "inandırıcı bulmadım", "katılırdım", "katılmam"):
        assert forbidden not in text


# --- render_card: gerçek Playwright ile PNG üretimi (uçtan uca) ----------


def test_render_ipo_card_gercek_png_uretir(tmp_path) -> None:
    context = _karcl_context()
    out_path = tmp_path / "test_halka_arz.png"
    result = card.render_card(context, str(out_path), template_name="ipo_card.html", screenshot_selector="#ipo-card")
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


def test_render_ipo_card_supplementary_ile_cokmez(tmp_path) -> None:
    """Quick-info şeridinin (talep toplama/katılım endeksi/satış yöntemi/
    fiyat istikrarı tile'ları) dolu haliyle de render'ın çökmediğini doğrular."""
    facts = kap_ipo.extract_ipo_facts(KARCL_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts)
    supplementary = SupplementaryIpoInfo(
        demand_period_display="10-11-12 Ağustos 2026",
        demand_period_hours="09:00-17:00",
        participation_index_compliant=False,
        participation_index_name=None,
        price_stabilization_note="30 gün.",
        sales_method_note="Sabit Fiyatla Talep Toplama.",
        source_url="https://halkarz.com/ornek/",
    )
    context = ipo_card.build_ipo_card_context(_karcl_disclosure(), facts, assessment, now=_NOW, supplementary=supplementary)
    out_path = tmp_path / "test_halka_arz_supplementary.png"
    result = card.render_card(context, str(out_path), template_name="ipo_card.html", screenshot_selector="#ipo-card")
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0


# --- Faz 20.5 (2026-08-07 devamı): Öne Çıkan Noktalar / Gelir Kullanımı / --------------------
# Fiyat İstikrarı-Taahhütler / Operasyonel-Finansal Veriler -- GERÇEK CITAS + VEYAS verisiyle


def _citas_disclosure() -> kap_ipo.IzahnameDisclosure:
    return kap_ipo.IzahnameDisclosure(
        disclosure_indices=(1,),
        publish_date=date(2026, 8, 7),
        underwriter_name="TERA YATIRIM MENKUL DEĞERLER A.Ş.",
        target_tickers=("CITAS",),
        summary="Çitlekçi Mağazacılık Gıda A.Ş. Halka Arzına İlişkin Onaylı İzahname",
    )


def _citas_context(price_report=None, supplementary=None) -> dict:
    facts = kap_ipo.extract_ipo_facts(CITAS_IZAHNAME_TEXT)
    assessment = ipo_assessment.compute_ipo_assessment(facts, price_report=price_report)
    return ipo_card.build_ipo_card_context(
        _citas_disclosure(), facts, assessment, now=_NOW, supplementary=supplementary, price_report=price_report
    )


def test_build_ipo_card_context_highlight_rows_ozne_kanaat_icermez() -> None:
    """K2/build_ipo_analysis_text ile AYNI ilke: highlight_rows nötr
    olgusal cümleler içerir, öznel/yatırım-tavsiyesi ifadesi ASLA içermez."""
    context = _citas_context()
    assert len(context["highlight_rows"]) >= 3
    joined = " ".join(context["highlight_rows"]).lower()
    for forbidden in ("dikkat çekici", "önce kote olması gereken", "bence", "tavsiye ederim", "yatırım yapmalı"):
        assert forbidden not in joined


def test_build_ipo_card_context_highlight_rows_gercek_rakamlari_yansitir() -> None:
    context = _citas_context()
    joined = " ".join(context["highlight_rows"])
    assert "2,7 mr" in joined  # halka arz büyüklüğü
    assert "%82,2" in joined  # sermaye artırımı payı
    assert "30 gün" in joined  # fiyat istikrarı süresi


def test_build_ipo_card_context_fiyat_istikrari_ve_taahhut_izahnameden_dolar() -> None:
    context = _citas_context()
    assert context["price_stabilization_period_display"] == "30 gün"
    assert context["price_stabilization_source_pct_display"] == "kaynağın %15'i"
    assert context["issuer_lockup_period_display"] == "1 yıl"
    assert context["has_quick_info"] is True


def test_build_ipo_card_context_28_2_fallback_ek5_yokken_dolar() -> None:
    context = _citas_context()
    assert context["is_use_of_proceeds_empty"] is True  # Ek-5 verilmedi
    assert context["use_of_proceeds_range_lines"] is not None
    assert "İşletme Sermayesi Güçlendirilmesi: %30-40" in context["use_of_proceeds_range_lines"]


def test_build_ipo_card_context_operasyonel_finansal_price_report_yoksa_bos() -> None:
    context = _citas_context()
    assert context["is_operational_financial_empty"] is True
    assert context["operational_financial_rows"] == []


def test_build_ipo_card_context_operasyonel_finansal_price_report_ile_dolar() -> None:
    price_report = ipo_price_report.extract_price_report_financials(VEYAS_PRICE_REPORT_TEXT)
    context = _citas_context(price_report=price_report)

    assert context["is_operational_financial_empty"] is False
    labels = {row["label"] for row in context["operational_financial_rows"]}
    assert "Hasılat (2025)" in labels
    ciro_row = next(row for row in context["operational_financial_rows"] if row["label"] == "Ciro (31.03.2026)")
    assert ciro_row["yoy_display"] == "%13,6"
    assert ciro_row["yoy_class"] == "positive"


def test_build_ipo_card_context_operasyonel_finansal_price_report_bos_donerse_halkarz_yedegine_duser() -> None:
    """🚨 CANLI HATA + DÜZELTME (2026-08-07, otuz birinci tur, KPEKS ile
    bulundu): `price_report` `None` DEĞİL ama TEK BİR alanı bile
    doldurmamış bir `PriceReportFinancials` nesnesi olduğunda (taranmış PDF)
    eski kod `is None` kontrolü yüzünden halkarz.com yedeğine HİÇ
    DÜŞMÜYORDU -- bölüm SESSİZCE boş kalıyordu."""
    bos_price_report = ipo_price_report.extract_price_report_financials("alakasız bir metin, hiçbir tablo yok")
    supplementary = SupplementaryIpoInfo(
        demand_period_display=None,
        demand_period_hours=None,
        participation_index_compliant=None,
        participation_index_name=None,
        price_stabilization_note=None,
        sales_method_note=None,
        source_url="https://halkarz.com/kapeks-kimya-sanayi-a-s/",
        financial_table_revenue_full_year_text="3,8 Milyar TL",
        financial_table_gross_profit_full_year_text="1,2 Milyar TL",
        financial_table_period_label="2025",
    )

    context = _citas_context(price_report=bos_price_report, supplementary=supplementary)

    assert context["is_operational_financial_empty"] is False
    rows = {row["label"]: row for row in context["operational_financial_rows"]}
    assert rows["Hasılat (2025)"]["value_display"] == "3,8 Milyar TL"
    assert rows["Hasılat (2025)"]["is_fallback"] is True
    assert rows["Brüt Kâr (2025)"]["value_display"] == "1,2 Milyar TL"


def test_render_ipo_card_faz_20_5_bolumleriyle_cokmez(tmp_path) -> None:
    """4 yeni bölümün (Öne Çıkan Noktalar/Fiyat İstikrarı-Taahhüt/28.2
    fallback/Operasyonel-Finansal) HEPSİ dolu haliyle GERÇEK Playwright
    render'ı çökmediğini doğrular."""
    price_report = ipo_price_report.extract_price_report_financials(VEYAS_PRICE_REPORT_TEXT)
    context = _citas_context(price_report=price_report)
    out_path = tmp_path / "test_halka_arz_faz_20_5.png"
    result = card.render_card(context, str(out_path), template_name="ipo_card.html", screenshot_selector="#ipo-card")
    assert Path(result).exists()
    assert Path(result).stat().st_size > 0
