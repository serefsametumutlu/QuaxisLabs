"""SPEC: `docs/spec/spec_mercek_kalite.md` testleri -- Kalite Merceği (v2)."""

from __future__ import annotations

from decimal import Decimal

from src.analysis import calculator
from src.analysis.fundamental_screens import GreenblattResult
from src.analysis.lens_kalite import KaliteGirdisi, hesapla_kalite_mercegi, hesapla_kalite_mercegi_banka

_LATEST = (2026, 3)
_QOQ_PRIOR = (2025, 12)
_YOY_PRIOR = (2025, 3)


def _sample_financials(equity_current=Decimal("400")) -> dict:
    return {
        _LATEST: {
            "revenue": Decimal("120"), "revenue_cum": Decimal("120"),
            "gross_profit": Decimal("60"), "gross_profit_cum": Decimal("60"),
            "operating_profit": Decimal("20"), "operating_profit_cum": Decimal("20"),
            "operating_profit_ebitda_base": Decimal("20"), "operating_profit_ebitda_base_cum": Decimal("20"),
            "depreciation_amortization": Decimal("10"), "depreciation_amortization_cum": Decimal("10"),
            "net_income": Decimal("15"), "net_income_cum": Decimal("15"),
            "cash": Decimal("200"), "total_assets": Decimal("1000"),
            "financial_debt": Decimal("300"), "equity": equity_current,
        },
        _QOQ_PRIOR: {
            "revenue": Decimal("140"), "revenue_cum": Decimal("140"),
            "gross_profit": Decimal("62"), "gross_profit_cum": Decimal("62"),
            "operating_profit": Decimal("25"), "operating_profit_cum": Decimal("25"),
            "operating_profit_ebitda_base": Decimal("25"), "operating_profit_ebitda_base_cum": Decimal("25"),
            "depreciation_amortization": Decimal("11"), "depreciation_amortization_cum": Decimal("11"),
            "net_income": Decimal("18"), "net_income_cum": Decimal("18"),
            "cash": Decimal("180"), "total_assets": Decimal("950"),
            "financial_debt": Decimal("310"), "equity": Decimal("380"),
        },
        _YOY_PRIOR: {
            "revenue": Decimal("100"), "revenue_cum": Decimal("100"),
            "gross_profit": Decimal("40"), "gross_profit_cum": Decimal("40"),
            "operating_profit": Decimal("12"), "operating_profit_cum": Decimal("12"),
            "operating_profit_ebitda_base": Decimal("12"), "operating_profit_ebitda_base_cum": Decimal("12"),
            "depreciation_amortization": Decimal("8"), "depreciation_amortization_cum": Decimal("8"),
            "net_income": Decimal("10"), "net_income_cum": Decimal("10"),
            "cash": Decimal("150"), "total_assets": Decimal("800"),
            "financial_debt": Decimal("290"), "equity": Decimal("200"),
        },
    }


def _analysis(equity_current=Decimal("400")):
    return calculator.analyze("TEST", _sample_financials(equity_current))


def test_kalite_mercegi_tum_veriyle_calisir_ve_veri_yeterli() -> None:
    analysis = _analysis()
    greenblatt = GreenblattResult(
        ebit=Decimal("20"), enterprise_value=Decimal("100"), earnings_yield_pct=Decimal("20"), earnings_yield_band="Yüksek",
        net_working_capital=Decimal("250"), net_fixed_assets=Decimal("300"), return_on_capital_pct=Decimal("30"), return_on_capital_band="Yüksek",
    )
    girdi = KaliteGirdisi(analysis=analysis, greenblatt=greenblatt, operating_cash_flow_ttm=Decimal("20"))
    sonuc = hesapla_kalite_mercegi(girdi)
    assert sonuc.data_sufficient
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")
    isimler = {c.name for c in sonuc.components}
    assert isimler == {
        "Nakit Üretimi (FAVÖK marjı)", "Özkaynak Kârlılığı (ROE)", "Kârlılık (Net Marj)", "Brüt Kâr Marjı",
        "Greenblatt Sermaye Getirisi (ROC)", "Aktif Kârlılığı (ROA)", "Nakit Kâr Kalitesi (OCF/Net Kâr)",
        "SG&A/Brüt Kâr", "Ar-Ge/Brüt Kâr", "Faiz Gideri/Faaliyet Kârı",
    }


def test_kalite_mercegi_negatif_ozkaynakta_roe_none_diger_bilesenler_calisir() -> None:
    analysis = _analysis(equity_current=Decimal("-50"))
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak Kârlılığı (ROE)"].score is None
    assert "negatif özkaynak" in isimler["Özkaynak Kârlılığı (ROE)"].reasoning_tr
    # FAVOK marji/net marj/brut marj -- ozkaynaktan BAGIMSIZ -- HALA calisir.
    assert isimler["Nakit Üretimi (FAVÖK marjı)"].score is not None
    assert sonuc.total_score > Decimal("0")


def test_kalite_mercegi_greenblatt_ve_ocf_yoksa_atlanir_toplam_yine_uretilir() -> None:
    analysis = _analysis()
    girdi = KaliteGirdisi(analysis=analysis, greenblatt=None, operating_cash_flow_ttm=None)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Greenblatt Sermaye Getirisi (ROC)"].score is None
    assert isimler["Nakit Kâr Kalitesi (OCF/Net Kâr)"].score is None
    assert sonuc.total_score > Decimal("0")  # kalan bilesenler agirligi devraldi


# --- V-04 (docs/spec/spec_veri_tamlik_yol_haritasi.md) -- hazine hissesi düzeltmeli ROE -----------------------------------------------------


def test_kalite_mercegi_treasury_stock_verilmezse_ham_roe_davranisi_degismez() -> None:
    """Regresyon kilidi -- treasury_stock varsayılan None, mevcut ham ROE
    davranışı BİREBİR KORUNUR (BİST'te bu alan hiç çekilmiyor, her zaman
    None gelir)."""
    analysis = _analysis()
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    roe_bileseni = isimler["Özkaynak Kârlılığı (ROE)"]
    assert roe_bileseni.score is not None
    assert "hazine hissesi düzeltmeli" not in roe_bileseni.reasoning_tr


def test_kalite_mercegi_treasury_stock_verilirse_duzeltmeli_roe_kullanilir() -> None:
    """02/FORMÜL-21: Net Kâr / (Özkaynak + Hazine Hissesi) -- treasury_stock
    verildiğinde ROE bileşeni AYNI ağırlığı (20) korur, sadece daha doğru
    (düşük özkaynak tabanının şişirmediği) bir girdiyle beslenir."""
    analysis = _analysis()  # ttm_net_income=23, equity_current=400
    girdi = KaliteGirdisi(analysis=analysis, treasury_stock=Decimal("100"))
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    roe_bileseni = isimler["Özkaynak Kârlılığı (ROE)"]
    assert roe_bileseni.score is not None
    assert roe_bileseni.weight_nominal == Decimal("18")
    assert "hazine hissesi düzeltmeli" in roe_bileseni.reasoning_tr
    assert "FORMÜL-21" in roe_bileseni.reasoning_tr


def test_kalite_mercegi_treasury_stock_negatif_ozkaynakta_yine_none() -> None:
    """Negatif özkaynak guard'ı treasury_stock verilse BİLE ÖNCE uygulanır
    -- iki neden ayrımı (bilinçli tam-dağıtım vs iflas riski) hazine
    hissesi düzeltmesiyle ÇÖZÜLEMEZ."""
    analysis = _analysis(equity_current=Decimal("-50"))
    girdi = KaliteGirdisi(analysis=analysis, treasury_stock=Decimal("100"))
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak Kârlılığı (ROE)"].score is None
    assert "negatif özkaynak" in isimler["Özkaynak Kârlılığı (ROE)"].reasoning_tr


def test_skor_roe_treasury_stock_sifir_veya_negatifse_duzeltme_uygulanmaz() -> None:
    """treasury_stock<=0 (raporlanmamış/sıfır) iken ham ROE'ye SESSİZCE
    devam edilir -- pozitif olmayan bir düzeltme uygulamak anlamsızdır."""
    from src.analysis.lens_kalite import _skor_roe

    skor, gerekce = _skor_roe(Decimal("15"), Decimal("400"), Decimal("23"), Decimal("0"))
    assert "hazine hissesi düzeltmeli" not in gerekce


def test_nakit_kar_kalitesi_negatif_net_karda_none() -> None:
    from src.analysis.lens_kalite import _skor_nakit_kar_kalitesi

    skor, gerekce = _skor_nakit_kar_kalitesi(Decimal("10"), Decimal("-5"))
    assert skor is None
    assert "negatif" in gerekce


def test_nakit_kar_kalitesi_oran_str_ile_formatlanir_yuzde_degil() -> None:
    from src.analysis.lens_kalite import _skor_nakit_kar_kalitesi

    skor, gerekce = _skor_nakit_kar_kalitesi(Decimal("15"), Decimal("15"))  # 1,0x
    assert skor is not None
    assert "1,00x" in gerekce
    assert "%1,0" not in gerekce  # K4: yanlislikla yuzde formatlanmamali


# --- hesapla_kalite_mercegi_banka (Y1 duzeltmesi: ROE %80 / ROA %20) -----------------------------------------------------


def test_kalite_mercegi_banka_ikisi_de_varsa_agirlik_orani_80_20() -> None:
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("25"), roa_pct=Decimal("3"))
    isimler = {c.name: c for c in sonuc.components}
    roe_agirlik = isimler["Özkaynak Kârlılığı (ROE)"].weight_effective
    roa_agirlik = isimler["Aktif Kârlılığı (ROA)"].weight_effective
    assert roe_agirlik == Decimal(80)
    assert roa_agirlik == Decimal(20)


def test_kalite_mercegi_banka_ikisi_de_varsa_veri_yeterli() -> None:
    """Nominal agirlik duzeltmesi (bu tur): (20,5) -> (80,20) -- ONCEKI
    surumde nominal toplam (25) HER ZAMAN min_veri_agirlik_yuzdesi (%50)
    esiginin ALTINDA kalip data_sufficient'i YANLISLIKLA False donduruyordu
    (CANLI dogrulandi), ROE+ROA ikisi de dolu olsa BILE."""
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("25"), roa_pct=Decimal("3"))
    assert sonuc.data_sufficient
    assert sonuc.badge != "YETERSİZ VERİ"


def test_kalite_mercegi_banka_sadece_roe_varsa_agirlik_100() -> None:
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("25"), roa_pct=None)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Özkaynak Kârlılığı (ROE)"].weight_effective == Decimal(100)
    assert isimler["Aktif Kârlılığı (ROA)"].score is None


# --- hesapla_kalite_mercegi_banka: template-farkindalik (bu tur -- sigorta/finansman eslikleri banka'dan FARKLI) -----------------------------------------------------


def test_kalite_mercegi_banka_template_varsayilan_banka_esikleriyle_ayni() -> None:
    """template verilmezse ESKI davranis (banka esikleri, ROE guclu=%20)
    KORUNUR -- geriye uyumluluk (mevcut testler DEGISMEDEN gecmeli)."""
    sonuc = hesapla_kalite_mercegi_banka("AKBNK", (2026, 3), roe_pct=Decimal("20"), roa_pct=None)
    isimler = {c.name: c for c in sonuc.components}
    # ROE=20 banka guclu_esik'ine (20) TAM denk -- _lerp_score(20,10,20,4,7)=7 asymptote basi.
    assert isimler["Özkaynak Kârlılığı (ROE)"].score is not None


def test_kalite_mercegi_sigorta_kendi_roe_esiklerini_kullanir() -> None:
    """CONFIG['sigorta']['ozkaynak_karliligi'] = guclu=%25/orta=%10/tavan=%40
    -- banka'dan (guclu=%20) FARKLI. ROE=%22 banka'da 'guclu' bandina
    girerken sigortada henuz 'orta-guclu arasi' kalir -- iki template
    FARKLI skor uretmeli (aksi halde eski hatali davranis SESSIZCE devam
    ediyor demektir)."""
    banka_sonuc = hesapla_kalite_mercegi_banka("XBANK", (2026, 3), roe_pct=Decimal("22"), roa_pct=None, template="banka")
    sigorta_sonuc = hesapla_kalite_mercegi_banka("XSIGORTA", (2026, 3), roe_pct=Decimal("22"), roa_pct=None, template="sigorta")
    banka_roe = {c.name: c for c in banka_sonuc.components}["Özkaynak Kârlılığı (ROE)"].score
    sigorta_roe = {c.name: c for c in sigorta_sonuc.components}["Özkaynak Kârlılığı (ROE)"].score
    assert banka_roe != sigorta_roe


def test_kalite_mercegi_finansman_kendi_roa_esiklerini_kullanir() -> None:
    """CONFIG['finansman']['aktif_karliligi'] = guclu=%5/orta=%2/tavan=%10
    -- banka'dan (guclu=%2,5) FARKLI. ROA=%4 banka esiginde 'guclu'ye
    YAKIN/UZERINDE iken finansmanda henuz orta-guclu arasindadir."""
    banka_sonuc = hesapla_kalite_mercegi_banka("XBANK", (2026, 3), roe_pct=None, roa_pct=Decimal("4"), template="banka")
    finansman_sonuc = hesapla_kalite_mercegi_banka("XFIN", (2026, 3), roe_pct=None, roa_pct=Decimal("4"), template="finansman")
    banka_roa = {c.name: c for c in banka_sonuc.components}["Aktif Kârlılığı (ROA)"].score
    finansman_roa = {c.name: c for c in finansman_sonuc.components}["Aktif Kârlılığı (ROA)"].score
    assert banka_roa != finansman_roa


def test_kalite_mercegi_sigorta_roa_yoksa_keyerror_atmaz_yedek_esik_kullanir() -> None:
    """CONFIG['sigorta']'da 'aktif_karliligi' alt-sozlugu hic YOK -- roa_pct
    zaten None geldigi icin bu hicbir zaman TETIKLENMEZ ama yedek esik
    (banka'nin) dict erisiminde KeyError FIRLATMAMALI."""
    sonuc = hesapla_kalite_mercegi_banka("XSIGORTA", (2026, 3), roe_pct=Decimal("25"), roa_pct=None, template="sigorta")
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["Aktif Kârlılığı (ROA)"].score is None
    assert isimler["Özkaynak Kârlılığı (ROE)"].weight_effective == Decimal(100)


# --- YENİ bileşenler (docs/spec/spec_yeni_bilesenler_agirliklandirma.md §1) -----------------------------------------------------


def test_kalite_mercegi_agirlik_toplami_her_zaman_yuz() -> None:
    """Nominal ağırlıklar (veri durumundan BAĞIMSIZ, statik) HER ZAMAN
    %100'e tamamlanmalı -- 7 eski + 3 yeni bileşen (20+18+13+13+8+4+9+5+3+7)."""
    analysis = _analysis()
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    toplam_nominal = sum((c.weight_nominal for c in sonuc.components), Decimal(0))
    assert toplam_nominal == Decimal(100)


def test_kalite_mercegi_bist_yeni_uc_bilesen_none_agirlik_dagitilir() -> None:
    """BİST sanayi haritasında sga_expense/research_development_expense/
    interest_expense hiç çekilmiyor -- bu 3 bileşen HER ZAMAN None döner,
    ağırlığı diğer 7 bileşene ORANTISAL dağıtılır, mercek YİNE de
    'YETERSİZ VERİ' düşmez (7-bileşenli v1'e yakın davranış korunur)."""
    analysis = _analysis()  # sga_expense/research_development_expense/interest_expense fixture'da YOK
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["SG&A/Brüt Kâr"].score is None
    assert isimler["Ar-Ge/Brüt Kâr"].score is None
    assert isimler["Faiz Gideri/Faaliyet Kârı"].score is None
    assert "NASDAQ" in isimler["SG&A/Brüt Kâr"].reasoning_tr
    assert sonuc.data_sufficient
    assert sonuc.total_score > Decimal("0")


def test_kalite_mercegi_nasdaq_benzeri_veriyle_yeni_uc_bilesen_hesaplanir() -> None:
    """NASDAQ tipi bir fixture (sga_expense/research_development_expense/
    interest_expense DOLU) -- 3 yeni bileşen skorlanır, mercek 10-bileşenli
    çalışır."""
    finansallar = _sample_financials()
    finansallar[_LATEST]["sga_expense"] = Decimal("10")  # SG&A/Brüt Kâr = 10/60 ~ %16,7 (fantastik bandı)
    finansallar[_LATEST]["research_development_expense"] = Decimal("3")  # Ar-Ge/Brüt Kâr = 3/60 = %5
    finansallar[_LATEST]["interest_expense"] = Decimal("2")  # Faiz Gideri/Faaliyet Kârı = 2/20 = %10
    analysis = calculator.analyze("TESTUS", finansallar)
    girdi = KaliteGirdisi(analysis=analysis)
    sonuc = hesapla_kalite_mercegi(girdi)
    isimler = {c.name: c for c in sonuc.components}
    assert isimler["SG&A/Brüt Kâr"].score is not None
    assert isimler["Ar-Ge/Brüt Kâr"].score is not None
    assert isimler["Faiz Gideri/Faaliyet Kârı"].score is not None
    # düşük oranlar -- düşük=iyi yönünde YÜKSEK puan bekleniyor
    assert isimler["SG&A/Brüt Kâr"].score > Decimal("7")
    assert isimler["Ar-Ge/Brüt Kâr"].score > Decimal("7")
    assert isimler["Faiz Gideri/Faaliyet Kârı"].score > Decimal("7")
    assert sonuc.data_sufficient


def test_skor_sga_orani_yuksek_oranda_dusuk_puan() -> None:
    from src.analysis.lens_kalite import _skor_sga_orani

    dusuk_skor, _ = _skor_sga_orani(Decimal("15"))
    yuksek_skor, _ = _skor_sga_orani(Decimal("95"))
    assert dusuk_skor > yuksek_skor


def test_skor_rd_orani_gerilim_notu_yuksek_oranda_eklenir() -> None:
    from src.analysis.lens_kalite import _skor_rd_orani

    skor, gerekce = _skor_rd_orani(Decimal("40"))
    assert skor is not None
    assert "Fisher merceği" in gerekce


def test_skor_rd_orani_dusuk_oranda_gerilim_notu_eklenmez() -> None:
    from src.analysis.lens_kalite import _skor_rd_orani

    skor, gerekce = _skor_rd_orani(Decimal("5"))
    assert skor is not None
    assert "Fisher merceği" not in gerekce


def test_skor_faiz_gideri_orani_negatifse_uyari_notu_eklenir() -> None:
    """interest_expense NET (gider-gelir birleşik) raporlanmış olabilir --
    negatif oran çıkarsa kart bunu AÇIKÇA işaretler."""
    from src.analysis.lens_kalite import _skor_faiz_gideri_orani

    skor, gerekce = _skor_faiz_gideri_orani(Decimal("-5"))
    assert skor is not None
    assert "net faiz geliri" in gerekce


def test_skor_faiz_gideri_orani_none_ise_atlanir() -> None:
    from src.analysis.lens_kalite import _skor_faiz_gideri_orani

    skor, gerekce = _skor_faiz_gideri_orani(None)
    assert skor is None
    assert "atlandı" in gerekce
