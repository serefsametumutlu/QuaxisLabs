"""SPEC: docs/spec/spec_dashboard.md §"Dashboard'a gömülecek JSON şeması" +
.claude/skills/kart-tasarim-sistemi/SKILL.md §"Dashboard (piyasa görünümü)
standartları" -- `src/render/dashboard.py::build_dashboard_data()`/
`render_dashboard_html()`/`build_and_write_dashboard()` testleri.

`tests/test_card.py`/`tests/test_market_scan_result.py` ile AYNI desen:
gerçek ağ isteği ATILMAZ, izole bir SQLite dosyasına yazılan sentetik
`MarketScanResult` satırları üzerinden test edilir.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from src.db import models
from src.db.models import Company, MarketScanResult, utcnow_naive
from src.render import dashboard


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_dashboard.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def _add_company(session, ticker: str, market: str, ust_sektor: str | None, sirket_turu: str | None) -> None:
    session.add(Company(ticker=ticker, name=ticker, market=market, ust_sektor=ust_sektor, sirket_turu=sirket_turu))


def _add_ok_row(
    session,
    ticker: str,
    market: str = "BIST",
    ust_sektor: str = "Sanayi",
    sirket_turu: str = "sanayi",
    *,
    bilesik_score: str = "6.5",
    bilesik_badge: str = "DENGELİ",
    deger_coverage: str = "90",
    computed_at=None,
) -> None:
    _add_company(session, ticker, market, ust_sektor, sirket_turu)
    session.add(MarketScanResult(
        ticker=ticker, market=market, company_name=f"{ticker} A.Ş.", ust_sektor=ust_sektor, sirket_turu=sirket_turu,
        template="sanayi", year=2026, period=6, scan_status="ok",
        deger_score=Decimal("6.0"), deger_badge="DENGELİ", deger_coverage_pct=Decimal(deger_coverage),
        kalite_score=Decimal("6.0"), kalite_badge="DENGELİ", kalite_coverage_pct=Decimal("90"),
        buyume_score=Decimal("6.0"), buyume_badge="DENGELİ", buyume_coverage_pct=Decimal("90"),
        guvenlik_score=Decimal("6.0"), guvenlik_badge="DENGELİ", guvenlik_coverage_pct=Decimal("90"),
        bilesik_score=Decimal(bilesik_score), bilesik_badge=bilesik_badge, bilesik_data_coverage_pct=Decimal("90"),
        dahil_edilen_mercekler=["değer", "kalite", "büyüme", "güvenlik"],
        current_price=Decimal("100"), market_cap=Decimal("1000000000"), pe_ratio=Decimal("5"),
        pb_ratio=Decimal("1"), ev_ebitda=Decimal("4"), currency="TRY",
        computed_at=computed_at or utcnow_naive(),
    ))


# --- build_dashboard_data() -- şema/gruplama -----------------------------------------------------


def test_build_dashboard_data_ust_seviye_sema(session) -> None:
    _add_ok_row(session, "THYAO")
    session.commit()

    data = dashboard.build_dashboard_data(session)

    assert set(data.keys()) == {"meta", "markets", "methodology"}
    assert set(data["markets"].keys()) == {"BIST", "NASDAQ"}
    for key in ("generated_at", "bist_last_scan_at", "nasdaq_last_scan_at", "bist_company_count", "nasdaq_company_count", "nasdaq_universe_total"):
        assert key in data["meta"]
    assert data["meta"]["bist_company_count"] == 1
    assert data["meta"]["nasdaq_company_count"] == 0
    assert data["meta"]["nasdaq_universe_total"] is None  # spec: kodlama fazına kadar null kabul edilebilir
    # Metodoloji paneli (kullanıcı talebi, 2026-08-12): statik referans içeriği,
    # tarama verisinden BAĞIMSIZ olarak HER render'da AYNI şekilde mevcuttur.
    assert {"bilesik_aciklama", "kapsam_aciklama", "rozet_esikleri", "kaynak_kitaplar", "mercekler"} <= set(data["methodology"].keys())
    assert len(data["methodology"]["mercekler"]) == 4


def test_build_dashboard_data_satir_semasi(session) -> None:
    _add_ok_row(session, "THYAO")
    session.commit()

    data = dashboard.build_dashboard_data(session)
    sectors = data["markets"]["BIST"]["sectors"]
    assert len(sectors) == 1
    company = sectors[0]["companies"][0]

    # spec'in "Satır (şirket) şeması" ile birebir -- ham SAYISAL değerler
    # (JS sıralaması için) + hazır _display string'ler (sunum için).
    assert company["ticker"] == "THYAO"
    assert company["scan_status"] == "ok"
    assert set(company["mercekler"].keys()) == {"değer", "kalite", "büyüme", "güvenlik"}
    assert company["mercekler"]["değer"]["score"] == 6.0
    assert company["bilesik"]["score"] == 6.5
    assert company["bilesik"]["badge"] == "DENGELİ"
    assert company["carpanlar"]["pe_ratio"] == 5.0
    assert company["carpanlar"]["currency"] == "TRY"
    assert isinstance(company["veri_uyarilari"], list)
    # Görev 2 (detay sayfa linki) + Görev 3 (BIST30/BIST100 çipleri) alanları.
    assert company["detail_url"] == "detay/BIST_THYAO.html"
    assert company["in_bist30"] is True  # THYAO gerçek BIST30 endeks üyesi
    assert company["in_bist100"] is True


def test_dusuk_kapsamli_mercek_skoru_gosterilmez(session) -> None:
    """DÜZELTME (kullanıcı denetimi, 2026-08-12 -- AYES canlı örneği): bir
    mercek 1-2 bileşenden şişirilmiş yüksek bir skora sahip olsa BİLE
    (badge zaten "YETERSİZ VERİ" ise, coverage<%50 ile TANIM gereği AYNI
    şey) score_display "N/A" olmalı -- sayı asla güven verici GÖRÜNMEMELİ
    (Kural 3: yanlış rakamdan iyidir)."""
    _add_company(session, "AYES", "BIST", "Diğer", "sanayi")
    session.add(MarketScanResult(
        ticker="AYES", market="BIST", company_name="AYES A.Ş.", ust_sektor="Diğer", sirket_turu="sanayi",
        template="sanayi", year=2026, period=6, scan_status="ok",
        deger_score=Decimal("8.0"), deger_badge="SAĞLAM", deger_coverage_pct=Decimal("80"),
        kalite_score=Decimal("9.21"), kalite_badge="YETERSİZ VERİ", kalite_coverage_pct=Decimal("25"),
        currency="TRY", computed_at=utcnow_naive(),
    ))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["BIST"]["sectors"][0]["companies"][0]
    kalite = company["mercekler"]["kalite"]
    assert kalite["badge"] == "YETERSİZ VERİ"
    assert kalite["score"] is None
    assert kalite["score_display"] == "N/A"
    # Sağlam kapsamlı diğer mercek ETKİLENMEMELİ.
    assert company["mercekler"]["değer"]["score_display"] != "N/A"


def test_bist30_bist100_uyelik_bayraklari(session) -> None:
    _add_ok_row(session, "THYAO")  # BIST30 + BIST100 üyesi
    _add_ok_row(session, "HALKB", ust_sektor="Bankacılık", sirket_turu="banka")  # SADECE BIST100 üyesi
    _add_ok_row(session, "ZZZZZ", ust_sektor="Diğer", sirket_turu="sanayi")  # hiçbir endekste yok
    session.commit()

    data = dashboard.build_dashboard_data(session)
    by_ticker = {c["ticker"]: c for sec in data["markets"]["BIST"]["sectors"] for c in sec["companies"]}
    assert by_ticker["THYAO"]["in_bist30"] is True
    assert by_ticker["THYAO"]["in_bist100"] is True
    assert by_ticker["HALKB"]["in_bist30"] is False
    assert by_ticker["HALKB"]["in_bist100"] is True
    assert by_ticker["ZZZZZ"]["in_bist30"] is False
    assert by_ticker["ZZZZZ"]["in_bist100"] is False

    assert "bist30_index" in data["markets"]["BIST"]
    assert "THYAO" in data["markets"]["BIST"]["bist30_index"]
    assert "HALKB" not in data["markets"]["BIST"]["bist30_index"]
    assert "HALKB" in data["markets"]["BIST"]["bist100_index"]


def test_nasdaq_satirlarinda_bist_endeks_bayraklari_hep_false(session) -> None:
    _add_ok_row(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["NASDAQ"]["sectors"][0]["companies"][0]
    assert company["in_bist30"] is False
    assert company["in_bist100"] is False


def test_build_dashboard_data_hatali_satir_ornegi_veri_yok(session) -> None:
    """spec §"Hatalı/desteklenmeyen satır örneği" -- scan_status='veri_yok'
    satırında mercekler/bilesik/carpanlar null, veri_uyarilari boş liste."""
    _add_company(session, "XYZCO", "NASDAQ", "Teknoloji", None)
    session.add(MarketScanResult(ticker="XYZCO", market="NASDAQ", scan_status="veri_yok", computed_at=utcnow_naive()))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["NASDAQ"]["sectors"][0]["companies"][0]
    assert company["mercekler"] is None
    assert company["bilesik"] is None
    assert company["carpanlar"] is None
    assert company["veri_uyarilari"] == []


# --- Kenar durumlar (spec §Kenar durumlar + §Test senaryoları) -----------------------------------------------------


def test_hata_sonrasi_eski_skor_korunur_dashboardda_gorunur(session) -> None:
    """spec test senaryosu #5'in dashboard karşılığı: `scan_status='hata'`
    ama önceki BAŞARILI skor DB'de zaten varsa dashboard bunu 'sessizce boş'
    göstermez, en son bilinen gerçek skoru gösterir + bir 'bayat' notu ekler."""
    _add_company(session, "ESKI", "BIST", "Sanayi", "sanayi")
    session.add(MarketScanResult(
        ticker="ESKI", market="BIST", company_name="Eski A.Ş.", ust_sektor="Sanayi", sirket_turu="sanayi",
        scan_status="hata", error_detail="gecici ag hatasi",
        deger_score=Decimal("7.2"), deger_badge="SAĞLAM", deger_coverage_pct=Decimal("88"),
        bilesik_score=Decimal("7.0"), bilesik_badge="SAĞLAM", bilesik_data_coverage_pct=Decimal("88"),
        dahil_edilen_mercekler=["değer"], computed_at=utcnow_naive(),
    ))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["BIST"]["sectors"][0]["companies"][0]
    assert company["scan_status"] == "hata"
    assert company["bilesik"]["score"] == 7.0  # eski skor SESSİZCE gizlenmedi
    turler = [u["tur"] for u in company["veri_uyarilari"]]
    assert "hata_bayat" in turler


def test_hata_ilk_denemede_hicbir_skor_yoksa_veri_uyarisi_yok(session) -> None:
    """spec: 'İlk kez taranan bir ticker hata alırsa ... tüm skor alanları
    NULL kalır' -- bu durumda 'bayat skor' notu da EKLENMEZ (gösterilecek
    eski bir skor yok)."""
    _add_company(session, "ILKHATA", "BIST", "Sanayi", "sanayi")
    session.add(MarketScanResult(ticker="ILKHATA", market="BIST", scan_status="hata", error_detail="timeout", computed_at=utcnow_naive()))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["BIST"]["sectors"][0]["companies"][0]
    assert company["bilesik"] is None
    assert company["veri_uyarilari"] == []


def test_desteklenmiyor_satiri_uyari_tasir(session) -> None:
    """spec: 'desteklenmiyor' satırı SESSİZCE atlanmaz, açık bir uyarı taşır."""
    _add_company(session, "DESTEK", "BIST", None, None)
    session.add(MarketScanResult(ticker="DESTEK", market="BIST", scan_status="desteklenmiyor", error_detail="UnsupportedCompanyTypeError", computed_at=utcnow_naive()))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["BIST"]["sectors"][0]["companies"][0]  # "Sınıflandırılmamış" grubu
    assert company["mercekler"] is None
    assert len(company["veri_uyarilari"]) == 1
    assert company["veri_uyarilari"][0]["tur"] == "desteklenmiyor"


def test_gyo_notu_sadece_gyo_satirinda_gorunur(session) -> None:
    """spec test senaryosu #7 -- BİREBİR."""
    _add_ok_row(session, "EKGYO", ust_sektor="Gayrimenkul/GYO", sirket_turu="gyo")
    _add_ok_row(session, "THYAO", ust_sektor="Sanayi", sirket_turu="sanayi")
    session.commit()

    data = dashboard.build_dashboard_data(session)
    by_ticker = {c["ticker"]: c for sec in data["markets"]["BIST"]["sectors"] for c in sec["companies"]}

    gyo_turler = [u["tur"] for u in by_ticker["EKGYO"]["veri_uyarilari"]]
    sanayi_turler = [u["tur"] for u in by_ticker["THYAO"]["veri_uyarilari"]]
    assert "gyo" in gyo_turler
    assert "gyo" not in sanayi_turler


def test_n_bes_alti_yetersiz_ornek_bayragi_sinir_testi(session) -> None:
    """spec test senaryosu #6 -- BİREBİR (n=4 -> True, n=5 -> False)."""
    for i in range(4):
        _add_ok_row(session, f"SAG{i}", ust_sektor="Sağlık", sirket_turu="sanayi")
    session.commit()

    data = dashboard.build_dashboard_data(session)
    saglik = next(s for s in data["markets"]["BIST"]["sectors"] if s["ust_sektor"] == "Sağlık")
    assert saglik["n"] == 4
    assert saglik["yetersiz_ornek"] is True

    _add_ok_row(session, "SAG4", ust_sektor="Sağlık", sirket_turu="sanayi")
    session.commit()

    data2 = dashboard.build_dashboard_data(session)
    saglik2 = next(s for s in data2["markets"]["BIST"]["sectors"] if s["ust_sektor"] == "Sağlık")
    assert saglik2["n"] == 5
    assert saglik2["yetersiz_ornek"] is False


def test_siniflandirilmamis_grubu_yetersiz_ornek_kuralina_tabi_degil(session) -> None:
    _add_company(session, "BELIRSIZ", "BIST", None, None)
    session.add(MarketScanResult(ticker="BELIRSIZ", market="BIST", scan_status="veri_yok", computed_at=utcnow_naive()))
    session.commit()

    data = dashboard.build_dashboard_data(session)
    grup = data["markets"]["BIST"]["sectors"][0]
    assert grup["ust_sektor"] == "Sınıflandırılmamış"
    assert grup["yetersiz_ornek"] is None


def test_dusuk_veri_kapsami_gorsel_bayrak_tetikler(session) -> None:
    """spec §"Veri eksikliği görünürlüğü" -- şirket-spesifik düşük kapsam
    (data_coverage_pct < %50) satır/hücre bazında AYRI bir sinyal olmalı."""
    _add_ok_row(session, "DUSUK", deger_coverage="30")
    session.commit()

    data = dashboard.build_dashboard_data(session)
    company = data["markets"]["BIST"]["sectors"][0]["companies"][0]
    assert company["mercekler"]["değer"]["dusuk_kapsam"] is True
    assert company["dusuk_kapsam_var"] is True


# --- render_dashboard_html() -- tek dosya, gömülü JSON -----------------------------------------------------


def test_render_dashboard_html_tek_dosya_harici_kaynak_yok(session) -> None:
    _add_ok_row(session, "THYAO")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    html = dashboard.render_dashboard_html(data)

    assert "<!DOCTYPE html>" in html
    assert "</html>" in html
    assert "<html lang=\"tr\">" in html
    # skill zorunluluğu: harici kaynak/CDN YOK.
    assert "http://" not in html
    assert "https://" not in html
    assert "<link " not in html
    assert 'src="' not in html  # <script src="..."> / <img src="..."> gibi harici referans YOK


def test_render_dashboard_html_json_gomulu_ve_gecerli(session) -> None:
    _add_ok_row(session, "THYAO")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    html = dashboard.render_dashboard_html(data)

    marker = '<script type="application/json" id="dashboard-data">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    embedded = json.loads(html[start:end])
    assert embedded["meta"]["bist_company_count"] == 1
    assert embedded["markets"]["BIST"]["sectors"][0]["companies"][0]["ticker"] == "THYAO"


def test_render_dashboard_html_bist_nasdaq_sekmeleri_var(session) -> None:
    _add_ok_row(session, "THYAO", market="BIST")
    _add_ok_row(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    html = dashboard.render_dashboard_html(data)

    assert 'data-market="BIST"' in html
    assert 'data-market="NASDAQ"' in html
    assert "THYAO" in html
    assert "AAPL" in html


def test_render_dashboard_html_ticker_hucresi_detay_sayfasina_baglanir(session) -> None:
    """Görev 2: ticker hücresi artık `<a href="detay/...">` linki, yeni
    sekmede açılır."""
    _add_ok_row(session, "THYAO")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    html = dashboard.render_dashboard_html(data)

    assert 'href="detay/BIST_THYAO.html"' in html
    assert 'target="_blank"' in html


def test_render_dashboard_html_bist30_bist100_cipleri_sadece_bist_panelinde(session) -> None:
    """Görev 3: filtre çipleri SADECE BİST panelinde görünür, NASDAQ'ta yok."""
    _add_ok_row(session, "THYAO", market="BIST")
    _add_ok_row(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    session.commit()
    data = dashboard.build_dashboard_data(session)
    html = dashboard.render_dashboard_html(data)

    assert 'data-index-chip-row="BIST"' in html
    assert 'data-index-chip-row="NASDAQ"' not in html
    assert 'data-in-bist30="true"' in html  # THYAO satırı



# --- build_and_write_dashboard() -- üretim giriş noktası -----------------------------------------------------


def test_build_and_write_dashboard_dosyaya_yazar(session, tmp_path) -> None:
    _add_ok_row(session, "THYAO")
    session.commit()

    out_path = tmp_path / "alt_dizin" / "dashboard.html"
    result_path = dashboard.build_and_write_dashboard(out_path, session=session)

    assert result_path == str(out_path)
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "THYAO" in content
    assert "<!DOCTYPE html>" in content


def test_build_and_write_dashboard_with_details_hepsini_uretir(session, tmp_path) -> None:
    """Görev 2: dashboard.html'in YANINDA HER satır için ayrı bir detay
    sayfası -- gerçek proje output/ klasörü KİRLETİLMEZ (tmp_path altına
    yazılır)."""
    _add_ok_row(session, "THYAO", market="BIST")
    _add_ok_row(session, "AAPL", market="NASDAQ", ust_sektor="Teknoloji")
    session.commit()

    out_path = tmp_path / "dashboard.html"
    dashboard_path, detail_paths = dashboard.build_and_write_dashboard_with_details(out_path, session=session)

    assert dashboard_path == str(out_path)
    assert len(detail_paths) == 2
    thyao_path = tmp_path / "detay" / "BIST_THYAO.html"
    aapl_path = tmp_path / "detay" / "NASDAQ_AAPL.html"
    assert thyao_path.exists()
    assert aapl_path.exists()
    assert "THYAO" in thyao_path.read_text(encoding="utf-8")
