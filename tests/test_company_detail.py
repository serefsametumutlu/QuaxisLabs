"""SPEC: kullanıcı isteği (2026-08-12) -- dashboard satırına tıklanınca açılan
şirket detay sayfası. `tests/test_dashboard.py` ile AYNI desen: gerçek ağ
isteği ATILMAZ, izole bir SQLite dosyasına yazılan sentetik `MarketScanResult`
+ `FinancialPeriod` satırları üzerinden test edilir.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from src.db import models, repository
from src.db.models import Company, MarketScanResult, utcnow_naive
from src.render import company_detail


@pytest.fixture()
def session(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test_company_detail.db'}"
    engine, session_factory = models.create_engine_and_session(db_url)
    models.init_db(engine)
    db_session = session_factory()
    yield db_session
    db_session.close()


def _mercekler_detay_fixture() -> dict:
    def bilesen(name, score, w_nom, w_eff, katki, reasoning):
        return {
            "name": name,
            "score": str(score) if score is not None else None,
            "weight_nominal": str(w_nom),
            "weight_effective": str(w_eff),
            "contribution": str(katki),
            "reasoning_tr": reasoning,
        }

    return {
        "değer": [
            bilesen("Mutlak Ucuzluk (F/K + PD/DD)", "7.5", "35", "35.0", "2.62",
                    "THYAO için F/K=5,2 sektör bandına göre ucuz kabul edildi."),
            bilesen("Kazanç Getirisi vs Risksiz Oran", None, "15", "0.0", "0.00",
                    "Risksiz faiz oranı verisi eksik olduğu için bu bileşen atlandı."),
        ],
        "kalite": [
            bilesen("Nakit Üretimi (FAVÖK marjı)", "8.0", "25", "25.0", "2.00",
                    "FAVÖK marjı %22,4 -- güçlü eşiğin (≥%20) üzerinde."),
        ],
        "büyüme": [
            bilesen("Hasılat Büyümesi", "6.0", "55", "55.0", "3.30", "Reel hasılat büyümesi %14,2."),
        ],
        "güvenlik": [
            bilesen("Kaldıraç (Net Borç/FAVÖK)", "9.0", "30", "30.0", "2.70", "Net Borç/FAVÖK 0,8x -- çok iyi."),
        ],
    }


def _add_ok_row(session, ticker="THYAO", market="BIST", tarihsel_skorlar=None) -> None:
    session.add(Company(ticker=ticker, name=f"{ticker} A.Ş.", market=market, ust_sektor="Sanayi", sirket_turu="sanayi"))
    session.add(MarketScanResult(
        ticker=ticker, market=market, company_name=f"{ticker} A.Ş.", ust_sektor="Sanayi", sirket_turu="sanayi",
        template="sanayi", year=2026, period=6, scan_status="ok",
        deger_score=Decimal("7.0"), deger_badge="SAĞLAM", deger_coverage_pct=Decimal("85"),
        kalite_score=Decimal("8.0"), kalite_badge="SAĞLAM", kalite_coverage_pct=Decimal("100"),
        buyume_score=Decimal("6.0"), buyume_badge="DENGELİ", buyume_coverage_pct=Decimal("100"),
        guvenlik_score=Decimal("9.0"), guvenlik_badge="SAĞLAM", guvenlik_coverage_pct=Decimal("100"),
        bilesik_score=Decimal("7.5"), bilesik_badge="SAĞLAM", bilesik_data_coverage_pct=Decimal("95"),
        dahil_edilen_mercekler=["değer", "kalite", "büyüme", "güvenlik"],
        current_price=Decimal("300"), market_cap=Decimal("400000000000"), pe_ratio=Decimal("5.2"),
        pb_ratio=Decimal("1.8"), ev_ebitda=Decimal("4.1"), currency="TRY",
        mercekler_detay=_mercekler_detay_fixture(),
        tarihsel_skorlar=tarihsel_skorlar,
        computed_at=utcnow_naive(),
    ))


def _tarihsel_skorlar_fixture() -> list[dict]:
    """docs/spec/spec_veri_tamlik_yol_haritasi.md §Skor Geçmişi -- ESKİDEN
    YENİYE sıralı (bkz. scripts/tarama_toplu.py::_tarihsel_skorlar_to_list)."""
    return [
        {
            "donem": "2025/12", "donem_label": "4Ç25",
            "deger_score": "6.5", "deger_badge": "DENGELİ",
            "kalite_score": "7.0", "kalite_badge": "SAĞLAM",
            "buyume_score": "5.0", "buyume_badge": "DENGELİ",
            "guvenlik_score": "8.0", "guvenlik_badge": "SAĞLAM",
            "bilesik_score": "6.6", "bilesik_badge": "DENGELİ",
        },
        {
            "donem": "2026/6", "donem_label": "2Ç26",
            "deger_score": "7.0", "deger_badge": "SAĞLAM",
            "kalite_score": "8.0", "kalite_badge": "SAĞLAM",
            "buyume_score": "6.0", "buyume_badge": "DENGELİ",
            "guvenlik_score": "9.0", "guvenlik_badge": "SAĞLAM",
            "bilesik_score": "7.5", "bilesik_badge": "SAĞLAM",
        },
    ]


def _add_financials(session, ticker="THYAO") -> None:
    records = []
    data_by_period = {
        (2026, 6): {"revenue": Decimal("120"), "gross_profit": Decimal("50"), "operating_profit": Decimal("20"),
                    "net_income": Decimal("15"), "cash": Decimal("200"), "trade_receivables": Decimal("80"),
                    "total_assets": Decimal("1000"), "financial_debt": Decimal("300"), "equity": Decimal("400"),
                    "current_assets": Decimal("500")},
        (2025, 6): {"revenue": Decimal("100"), "gross_profit": Decimal("40"), "operating_profit": Decimal("15"),
                    "net_income": Decimal("10"), "cash": Decimal("150"), "trade_receivables": Decimal("60"),
                    "total_assets": Decimal("900"), "financial_debt": Decimal("280"), "equity": Decimal("350"),
                    "current_assets": Decimal("420")},
        (2026, 3): {"revenue": Decimal("90"), "gross_profit": Decimal("35"), "operating_profit": Decimal("12"),
                    "net_income": Decimal("8"), "cash": Decimal("170"), "trade_receivables": Decimal("70"),
                    "total_assets": Decimal("950"), "financial_debt": Decimal("290"), "equity": Decimal("380"),
                    "current_assets": Decimal("460")},
    }
    for (year, period), fields in data_by_period.items():
        for item_code, value in fields.items():
            records.append((year, period, item_code, item_code, value))
    repository.upsert_financials(session, ticker, records)


# --- build_company_detail_data() ---------------------------------------------------------------


def test_satir_yoksa_none_doner(session) -> None:
    assert company_detail.build_company_detail_data(session, "YOKTUR", "BIST") is None


def test_piyasa_uyusmuyorsa_none_doner(session) -> None:
    _add_ok_row(session, "THYAO", "BIST")
    session.commit()
    assert company_detail.build_company_detail_data(session, "THYAO", "NASDAQ") is None


def test_ust_seviye_kimlik_alanlari(session) -> None:
    _add_ok_row(session)
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert data["ticker"] == "THYAO"
    assert data["company_name"] == "THYAO A.Ş."
    assert data["market"] == "BIST"
    assert data["ust_sektor"] == "Sanayi"
    assert data["sirket_turu_display"] == "Sanayi"
    assert data["bilesik"]["score_display"] == "7,5"
    assert data["bilesik"]["badge"] == "SAĞLAM"


def test_ekosistem_etiketi_thyao_havacilik_diger_sirket_none(session) -> None:
    """docs/spec/spec_sektor_inceltme.md 'Seçenek B' -- SADECE görsel rozet,
    `ust_sektor` (istatistiksel havuz) 'Sanayi' olarak KALIR (regresyon)."""
    _add_ok_row(session, ticker="THYAO")
    _add_ok_row(session, ticker="SISE")
    session.commit()

    thyao = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    sise = company_detail.build_company_detail_data(session, "SISE", "BIST")
    assert thyao["ekosistem_etiketi"] == "Havacılık"
    assert thyao["ust_sektor"] == "Sanayi"
    assert sise["ekosistem_etiketi"] is None


def test_mercekler_detay_tum_bilesenleri_tasir(session) -> None:
    """Görevin EN ÖNEMLİ kısmı -- mercekler_detay'daki HER bileşen (skor,
    ağırlık, katkı, reasoning_tr) sızmadan/eksilmeden data'ya geçmeli."""
    _add_ok_row(session)
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    deger = data["mercekler"]["değer"]
    assert deger["score_display"] == "7,0"
    assert len(deger["components"]) == 2
    ucuzluk = deger["components"][0]
    assert ucuzluk["name"] == "Mutlak Ucuzluk (F/K + PD/DD)"
    assert ucuzluk["score_display"] == "7,5/10"
    assert ucuzluk["weight_nominal_display"] == "%35"
    assert ucuzluk["contribution_display"] == "2,62"
    assert "THYAO için F/K=5,2" in ucuzluk["reasoning_tr"]

    eksik_bilesen = deger["components"][1]
    assert eksik_bilesen["score_display"] == "N/A"
    assert eksik_bilesen["veri_eksik"] is True

    kalite = data["mercekler"]["kalite"]
    assert len(kalite["components"]) == 1
    assert kalite["components"][0]["reasoning_tr"].startswith("FAVÖK marjı")


def test_dusuk_kapsamli_mercek_kapsam_cezali_skor_gosterir(session) -> None:
    """docs/spec/spec_kapsam_cezali_skor.md §3/§8 test senaryo 1 (AYES canlı
    örneği): badge "YETERSİZ VERİ" VE 0<kapsam<%50 ise artık TAMAMEN "N/A"
    DEĞİL -- nominal ağırlıklı/eksik=sıfır kapsam-cezalı skor
    (S′=9,21×0,25=2,30 -> "2,3") gösterilir, kapsam_notu §4'teki tam
    cümleyi ("Kalite: 2,3/10 (YETERSİZ VERİ — kapsam %25 — sadece 2/7
    bileşen ölçülebildi)") taşır."""
    session.add(Company(ticker="AYES", name="AYES A.Ş.", market="BIST", ust_sektor="Diğer", sirket_turu="sanayi"))
    session.add(MarketScanResult(
        ticker="AYES", market="BIST", company_name="AYES A.Ş.", ust_sektor="Diğer", sirket_turu="sanayi",
        template="sanayi", year=2026, period=6, scan_status="ok",
        kalite_score=Decimal("9.21"), kalite_badge="YETERSİZ VERİ", kalite_coverage_pct=Decimal("25"),
        mercekler_detay={
            "kalite": [
                {"name": "ROE", "score": "9.3", "weight_nominal": "20", "weight_effective": "80", "contribution": "7.44", "reasoning_tr": "-"},
                {"name": "ROA", "score": "8.8", "weight_nominal": "5", "weight_effective": "20", "contribution": "1.76", "reasoning_tr": "-"},
                {"name": "FAVÖK Marjı", "score": None, "weight_nominal": "25", "weight_effective": "0", "contribution": "0", "reasoning_tr": "veri yok"},
                {"name": "Net Marj", "score": None, "weight_nominal": "15", "weight_effective": "0", "contribution": "0", "reasoning_tr": "veri yok"},
                {"name": "Brüt Kâr Marjı", "score": None, "weight_nominal": "15", "weight_effective": "0", "contribution": "0", "reasoning_tr": "veri yok"},
                {"name": "Greenblatt ROC", "score": None, "weight_nominal": "10", "weight_effective": "0", "contribution": "0", "reasoning_tr": "veri yok"},
                {"name": "OCF/Net Kâr", "score": None, "weight_nominal": "10", "weight_effective": "0", "contribution": "0", "reasoning_tr": "veri yok"},
            ],
        },
        currency="TRY", computed_at=utcnow_naive(),
    ))
    session.commit()

    data = company_detail.build_company_detail_data(session, "AYES", "BIST")
    kalite = data["mercekler"]["kalite"]
    assert kalite["badge"] == "YETERSİZ VERİ"
    assert kalite["score_display"] == "2,3"
    assert kalite["kapsam_notu"] == (
        "Kalite: 2,3/10 (YETERSİZ VERİ — kapsam %25 — sadece 2/7 bileşen ölçülebildi)"
    )


def test_kapsam_sifir_mercek_skoru_na_gosterir(session) -> None:
    """docs/spec/spec_kapsam_cezali_skor.md §3/§8 test senaryo 3: kapsam=%0
    olan bir mercekte S′ formülü hiç TETİKLENMEZ -- score_display "N/A"
    AYNEN kalır, kapsam_notu None ("veri yok" ile "şirket kötü"
    KARIŞTIRILMASIN)."""
    session.add(Company(ticker="TBORG", name="TBORG A.Ş.", market="BIST", ust_sektor="Diğer", sirket_turu="sanayi"))
    session.add(MarketScanResult(
        ticker="TBORG", market="BIST", company_name="TBORG A.Ş.", ust_sektor="Diğer", sirket_turu="sanayi",
        template="sanayi", year=2026, period=6, scan_status="ok",
        deger_score=Decimal("0"), deger_badge="YETERSİZ VERİ", deger_coverage_pct=Decimal("0"),
        currency="TRY", computed_at=utcnow_naive(),
    ))
    session.commit()

    data = company_detail.build_company_detail_data(session, "TBORG", "BIST")
    deger = data["mercekler"]["değer"]
    assert deger["badge"] == "YETERSİZ VERİ"
    assert deger["score_display"] == "N/A"
    assert deger["kapsam_notu"] is None


def test_mercek_veri_yoksa_none_doner(session) -> None:
    _add_ok_row(session)
    session.commit()
    # Güvenlik skorunu temizle -- veri yok senaryosu
    row = session.get(MarketScanResult, "THYAO")
    row.guvenlik_score = None
    row.guvenlik_badge = None
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert data["mercekler"]["güvenlik"] is None


def test_snapshot_yoksa_bilesik_ve_mercekler_none(session) -> None:
    session.add(Company(ticker="YENI", name="Yeni A.Ş.", market="BIST"))
    session.add(MarketScanResult(ticker="YENI", market="BIST", scan_status="veri_yok", computed_at=utcnow_naive()))
    session.commit()

    data = company_detail.build_company_detail_data(session, "YENI", "BIST")
    assert data["bilesik"] is None
    assert data["mercekler"] is None
    assert data["carpanlar"] is None


def test_carpanlar_bloku(session) -> None:
    _add_ok_row(session)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert data["carpanlar"]["pe_ratio_display"] == "5,2"
    assert "₺" in data["carpanlar"]["price_display"]


# --- Skor Geçmişi (docs/spec/spec_veri_tamlik_yol_haritasi.md §Skor Geçmişi) ----------------------


def test_skor_gecmisi_yoksa_bos_liste_doner(session) -> None:
    _add_ok_row(session, tarihsel_skorlar=None)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert data["skor_gecmisi"] == []


def test_skor_gecmisi_donem_biciminde_ve_skorlar_decimal_donusumlu(session) -> None:
    _add_ok_row(session, tarihsel_skorlar=_tarihsel_skorlar_fixture())
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")

    gecmis = data["skor_gecmisi"]
    assert len(gecmis) == 2
    assert gecmis[0]["donem_label"] == "4Ç25"
    assert gecmis[0]["bilesik"]["display"] == "6,6"
    assert gecmis[0]["bilesik"]["badge_class"] == "dengeli"
    assert gecmis[1]["donem_label"] == "2Ç26"
    assert gecmis[1]["deger"]["display"] == "7,0"
    assert gecmis[1]["deger"]["badge_class"] == "saglam"


def test_skor_gecmisi_eksik_alan_na_gosterir(session) -> None:
    eksik = [{
        "donem": "2025/12", "donem_label": "4Ç25",
        "deger_score": None, "deger_badge": None,
        "kalite_score": "7.0", "kalite_badge": "SAĞLAM",
        "buyume_score": None, "buyume_badge": None,
        "guvenlik_score": None, "guvenlik_badge": None,
        "bilesik_score": None, "bilesik_badge": "YETERSİZ VERİ",
    }]
    _add_ok_row(session, tarihsel_skorlar=eksik)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")

    gecmis = data["skor_gecmisi"][0]
    assert gecmis["deger"]["display"] == "N/A"
    assert gecmis["bilesik"]["badge_class"] == "yetersiz"


def test_render_html_skor_gecmisi_tablosu_gorunur(session) -> None:
    _add_ok_row(session, tarihsel_skorlar=_tarihsel_skorlar_fixture())
    _add_financials(session)
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    html = company_detail.render_company_detail_html(data)

    assert "Skor Geçmişi" in html
    assert "4Ç25" in html
    assert "2Ç26" in html


# --- Finansal tablo özeti -----------------------------------------------------------------------


def test_finansal_veri_yoksa_available_false(session) -> None:
    _add_ok_row(session)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert data["financials"]["available"] is False
    assert data["financials"]["note"]


def test_finansal_ozet_sanayi_sablonu(session) -> None:
    _add_ok_row(session)
    _add_financials(session)
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    fin = data["financials"]
    assert fin["available"] is True
    labels = [r["label"] for r in fin["income_rows"]]
    assert "Satışlar" in labels
    assert "Net Dönem Kârı" in labels
    balance_labels = [r["label"] for r in fin["balance_rows"]]
    assert "Toplam Varlıklar" in balance_labels
    assert "Özkaynaklar" in balance_labels
    # quarterly_trend en az revenue/ebitda/net_income kalemlerini içerir
    trend_labels = [t["label"] for t in fin["quarterly_trend"]]
    assert "Satışlar" in trend_labels
    assert "Net Dönem Kârı" in trend_labels


def test_faaliyet_raporu_placeholder_dogru_ve_dahil(session) -> None:
    _add_ok_row(session)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    assert "henüz araştırılmadı" in data["faaliyet_raporu_placeholder"]
    assert data["faaliyet_raporu"] is None


# --- faaliyet_raporu (docs/spec/spec_veri_tamlik_yol_haritasi.md §Faaliyet
# Raporu, 2026-08-12) ---------------------------------------------------------------


def _faaliyet_raporu_bulgulari_fixture() -> dict:
    return {
        "kaynak_baslik": "2025 Faaliyet Raporu",
        "kaynak_tarih_display": "04.03.2026",
        "kaynak_url": "https://kap.org.tr/tr/Bildirim/1566094",
        "kar_kaynagi_ozeti": "Kâr artışı satış hacminden kaynaklandı.",
        "arge_yatirim_notu": "Ar-Ge harcamaları %10 arttı.",
        "faiz_finansman_notu": "Faiz gideri kârı sınırlı etkiledi.",
        "risk_faktorleri": ["Kur riski", "Akaryakıt maliyeti riski"],
        "source": "llm",
        "generated_at": "2026-08-12T10:00:00",
    }


def test_faaliyet_raporu_bulgulari_varsa_taniniyor(session) -> None:
    _add_ok_row(session)
    session.commit()
    row = session.get(MarketScanResult, "THYAO")
    row.faaliyet_raporu_bulgulari = _faaliyet_raporu_bulgulari_fixture()
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")

    assert data["faaliyet_raporu"] is not None
    assert data["faaliyet_raporu"]["kar_kaynagi_ozeti"] == "Kâr artışı satış hacminden kaynaklandı."
    assert data["faaliyet_raporu"]["risk_faktorleri"] == ["Kur riski", "Akaryakıt maliyeti riski"]
    assert "skor" in data["faaliyet_raporu"]["kaynak_etiket"].lower() or "gemini" in data["faaliyet_raporu"]["kaynak_etiket"].lower()


def test_render_html_faaliyet_raporu_bulgulari_gorunur_ve_skor_degildir_uyarisi_var(session) -> None:
    _add_ok_row(session)
    session.commit()
    row = session.get(MarketScanResult, "THYAO")
    row.faaliyet_raporu_bulgulari = _faaliyet_raporu_bulgulari_fixture()
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    html = company_detail.render_company_detail_html(data)

    assert "Kâr artışı satış hacminden kaynaklandı." in html
    assert "Akaryakıt maliyeti riski" in html
    assert "SKOR/PUAN DEĞİLDİR" in html
    assert "henüz araştırılmadı" not in html  # placeholder ARTIK gösterilmemeli


# --- render_company_detail_html() ---------------------------------------------------------------


def test_render_html_tek_dosya_ve_bilesenler_gorunur(session) -> None:
    _add_ok_row(session)
    _add_financials(session)
    session.commit()

    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    html = company_detail.render_company_detail_html(data)

    assert "<!DOCTYPE html>" in html
    assert "THYAO" in html
    assert "Mutlak Ucuzluk (F/K + PD/DD)" in html
    assert "THYAO için F/K=5,2 sektör bandına göre ucuz kabul edildi." in html
    assert "henüz araştırılmadı" in html
    assert '<link ' not in html
    assert 'src="' not in html


def test_render_html_dashboard_geri_donus_linki(session) -> None:
    _add_ok_row(session)
    session.commit()
    data = company_detail.build_company_detail_data(session, "THYAO", "BIST")
    html = company_detail.render_company_detail_html(data)
    assert 'href="../dashboard.html"' in html


# --- build_and_write_company_detail() / build_and_write_all_company_details() -----------------


def test_build_and_write_company_detail_dosyaya_yazar(session, tmp_path) -> None:
    _add_ok_row(session)
    session.commit()

    out_path = tmp_path / "detay" / "BIST_THYAO.html"
    result = company_detail.build_and_write_company_detail("THYAO", "BIST", out_path, session=session)

    assert result == str(out_path)
    assert out_path.exists()
    assert "THYAO" in out_path.read_text(encoding="utf-8")


def test_build_and_write_company_detail_satir_yoksa_none(session, tmp_path) -> None:
    out_path = tmp_path / "yok.html"
    result = company_detail.build_and_write_company_detail("YOKTUR", "BIST", out_path, session=session)
    assert result is None
    assert not out_path.exists()


def test_detail_relative_path_deseni() -> None:
    assert company_detail.detail_relative_path("THYAO", "BIST") == "detay/BIST_THYAO.html"


# --- İş anlaşmaları bölümü (kullanıcı isteği, 2026-08-19) -------------------


@pytest.fixture()
def is_anlasma_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "is_anlasmalari_yillik.csv"
    csv_path.write_text(
        "ticker,yil,yeni_is_toplami_try,n_anlasma,n_ayristirilan,kapsam_pct,onceki_yil_hasilat_try,oran,esik_gecti_mi\n"
        "ASELS,2025,256086637336.8,30,30,100.0,157339901315.0,1.6276,True\n"
        "ASELS,2026,219246077174.8,9,9,100.0,212489200293.0,1.0318,False\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(company_detail, "_IS_ANLASMA_CSV", csv_path)
    company_detail._load_is_anlasma_rows.cache_clear()
    yield csv_path
    company_detail._load_is_anlasma_rows.cache_clear()


_NOW_2026 = datetime(2026, 8, 19)


def test_is_anlasmalari_block_yeniden_eskiye_siralanir(is_anlasma_csv) -> None:
    block = company_detail._is_anlasmalari_block("ASELS", _NOW_2026)
    assert block is not None
    assert [r["yil"] for r in block] == ["2026", "2025"]


def test_is_anlasmalari_block_esik_gecti_ve_gecmedi_dogru_etiketlenir(is_anlasma_csv) -> None:
    block = company_detail._is_anlasmalari_block("ASELS", _NOW_2026)
    gecen = next(r for r in block if r["yil"] == "2025")
    assert gecen["esik_gecti"] is True
    assert "Eşiği geçti" in gecen["esik_gecti_display"]


def test_is_anlasmalari_block_tamamlanmamis_yil_esik_yargisi_gizlenir(is_anlasma_csv) -> None:
    """DÜZELTME (kullanıcı denetimi, 2026-08-19): `now.year` ile aynı olan
    (henüz tamamlanmamış) bir yıl için kesin Evet/Hayır YERİNE "yıl
    tamamlanmadı" notu gösterilmeli -- kısmi yıl verisini tam bir önceki
    yılla kıyaslamak yanıltıcı olurdu."""
    block = company_detail._is_anlasmalari_block("ASELS", _NOW_2026)
    tamamlanmamis = next(r for r in block if r["yil"] == "2026")
    assert tamamlanmamis["yil_tamamlanmadi"] is True
    assert tamamlanmamis["esik_gecti"] is False  # yargı GİZLENİR, kesin False iddia edilmez ama flag de True olamaz
    assert "tamamlanmadı" in tamamlanmamis["esik_gecti_display"]
    assert "Eşiği geçmedi" not in tamamlanmamis["esik_gecti_display"]
    # Ham rakamlar (kısmi de olsa) SAKLANMAZ -- kullanıcı yine görebilir.
    assert tamamlanmamis["yeni_is_toplami_display"] != "N/A"


def test_is_anlasmalari_block_veri_olmayan_ticker_icin_none(is_anlasma_csv) -> None:
    assert company_detail._is_anlasmalari_block("YOKTUR", _NOW_2026) is None


def test_is_anlasmalari_block_csv_yoksa_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(company_detail, "_IS_ANLASMA_CSV", tmp_path / "hic_yok.csv")
    company_detail._load_is_anlasma_rows.cache_clear()
    assert company_detail._is_anlasmalari_block("ASELS", _NOW_2026) is None
    company_detail._load_is_anlasma_rows.cache_clear()


# --- İş anlaşması TEK TEK detayları (kullanıcı isteği, 2026-08-19) ---------


@pytest.fixture()
def is_anlasma_deal_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "is_anlasmalari_detay.csv"
    csv_path.write_text(
        "ticker,tarih,karsi_taraf,aciklama,tutar_ham,tutar_try,yenileme_mi\n"
        "YEOTK,2025-02-05,Doğuş Grubu,GES EPC işi,4.882.651 USD,150000000.0,False\n"
        "YEOTK,2025-03-10,Enerjisa,RES elektrifikasyon,6.900.000 USD,220000000.0,False\n"
        "YEOTK,2024-01-01,Eski Müşteri,Sözleşme yenilenmesi,1.000.000 USD,,True\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(company_detail, "_IS_ANLASMA_DETAY_CSV", csv_path)
    company_detail._load_is_anlasma_deal_rows.cache_clear()
    yield csv_path
    company_detail._load_is_anlasma_deal_rows.cache_clear()


def test_is_anlasma_detaylari_block_tum_anlasmalari_listeler(is_anlasma_deal_csv) -> None:
    block = company_detail._is_anlasma_detaylari_block("YEOTK")
    assert block is not None
    assert len(block) == 3  # yenileme DAHIL -- hicbiri gizlenmez


def test_is_anlasma_detaylari_block_yenilemeyi_acikca_etiketler(is_anlasma_deal_csv) -> None:
    block = company_detail._is_anlasma_detaylari_block("YEOTK")
    yenileme = next(r for r in block if r["yenileme_mi"])
    assert yenileme["tutar_try_display"] == "yenileme (hariç)"


def test_is_anlasma_detaylari_block_yeniden_eskiye_siralanir(is_anlasma_deal_csv) -> None:
    block = company_detail._is_anlasma_detaylari_block("YEOTK")
    assert block[0]["tarih"] == "2025-03-10"


def test_is_anlasma_detaylari_block_veri_olmayan_ticker_icin_none(is_anlasma_deal_csv) -> None:
    assert company_detail._is_anlasma_detaylari_block("YOKTUR") is None
