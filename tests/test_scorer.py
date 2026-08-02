"""Faz 4 (devam) teslim kriteri: puanlama motorunun esik/agirlik davranisini
elle hesaplanmis degerlerle dogrulayan testler.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.analysis import calculator, scorer


# --- _lerp_score / _badge -----------------------------------------------------


def test_lerp_score_araligin_ortasinda_dogrusal_enterpolasyon() -> None:
    skor = scorer._lerp_score(Decimal("15"), Decimal("10"), Decimal("20"), Decimal("5"), Decimal("7"))
    assert skor == Decimal("6")


def test_lerp_score_alt_sinirin_altinda_kirpilir() -> None:
    skor = scorer._lerp_score(Decimal("-5"), Decimal("0"), Decimal("10"), Decimal("0"), Decimal("4"))
    assert skor == Decimal("0")


def test_lerp_score_ust_sinirin_ustunde_kirpilir() -> None:
    skor = scorer._lerp_score(Decimal("100"), Decimal("20"), Decimal("30"), Decimal("8"), Decimal("10"))
    assert skor == Decimal("10")


def test_lerp_score_x0_esittir_x1_ise_y0_doner() -> None:
    skor = scorer._lerp_score(Decimal("5"), Decimal("0"), Decimal("0"), Decimal("3"), Decimal("9"))
    assert skor == Decimal("3")


@pytest.mark.parametrize(
    "puan,beklenen",
    [
        (Decimal("10"), "SAĞLAM"),
        (Decimal("8"), "SAĞLAM"),  # sinir: 8 SAGLAM'a dahil
        (Decimal("7.99"), "DENGELİ"),
        (Decimal("6"), "DENGELİ"),  # sinir: 6 DENGELI'ye dahil
        (Decimal("5.99"), "KARIŞIK"),
        (Decimal("4"), "KARIŞIK"),  # sinir: 4 KARISIK'a dahil
        (Decimal("3.99"), "RİSKLİ"),
        (Decimal("0"), "RİSKLİ"),
    ],
)
def test_badge_sinir_degerleri(puan, beklenen) -> None:
    assert scorer._badge(puan) == beklenen


# --- _seviye_trend_skoru -----------------------------------------------------


def test_seviye_trend_skoru_veri_yoksa_none() -> None:
    skor, gerekce = scorer._seviye_trend_skoru("X", None, None, Decimal("20"), Decimal("10"), Decimal("30"))
    assert skor is None
    assert "veri yok" in gerekce


def test_seviye_trend_skoru_bozulan_trend_zayif_bucket_tetikler() -> None:
    # marj guclu esikte (25) olsa bile trend negatifse zayif bucket'a duser.
    skor, gerekce = scorer._seviye_trend_skoru(
        "FAVÖK marjı", Decimal("25"), Decimal("-2"), Decimal("20"), Decimal("10"), Decimal("30")
    )
    assert Decimal("0") <= skor <= Decimal("4")
    assert "bozuluyor" in gerekce


def test_seviye_trend_skoru_guclu_bucket_tavanda_yarim_yolda() -> None:
    # Eskiden "tavan" esigine ulasan her deger SABIT 10 puan aliyordu (kullanici
    # geri bildirimi: FAVOK marji %30 olan da %70 olan da ayni puani aliyordu,
    # adaletsizdi). Artik "tavan" esigi TAM ORTA NOKTA (8 ile 10'un ortasi,
    # yani 9) -- 10'a sadece asimptotik olarak yaklasilir, hicbir zaman esitlenmez.
    skor, _ = scorer._seviye_trend_skoru(
        "FAVÖK marjı", Decimal("30"), Decimal("1"), Decimal("20"), Decimal("10"), Decimal("30")
    )
    assert skor == Decimal("9")


def test_seviye_trend_skoru_guclu_bucket_tavanin_cok_otesi_10a_esitlenmez() -> None:
    skor_30, _ = scorer._seviye_trend_skoru(
        "FAVÖK marjı", Decimal("30"), None, Decimal("20"), Decimal("10"), Decimal("30")
    )
    skor_70, _ = scorer._seviye_trend_skoru(
        "FAVÖK marjı", Decimal("70"), None, Decimal("20"), Decimal("10"), Decimal("30")
    )
    assert skor_30 < skor_70 < Decimal("10")


def test_seviye_trend_skoru_orta_bucket() -> None:
    skor, gerekce = scorer._seviye_trend_skoru(
        "FAVÖK marjı", Decimal("15"), None, Decimal("20"), Decimal("10"), Decimal("30")
    )
    assert Decimal("5") <= skor <= Decimal("7")
    assert "orta düzeyde" in gerekce


def test_seviye_trend_skoru_negatif_seviye_taban_ile_dogru_enterpole() -> None:
    # taban gecerli oldugunda (buyume gibi) negatif seviyeler flat 0'a
    # sabitlenmez, tabanina gore kademelenir.
    dusuk_skor, _ = scorer._seviye_trend_skoru(
        "Hasılat büyümesi", Decimal("-19"), None, Decimal("15"), Decimal("0"), Decimal("30"), Decimal("-20")
    )
    cok_dusuk_skor, _ = scorer._seviye_trend_skoru(
        "Hasılat büyümesi", Decimal("-20"), None, Decimal("15"), Decimal("0"), Decimal("30"), Decimal("-20")
    )
    assert cok_dusuk_skor == Decimal("0")
    assert dusuk_skor > cok_dusuk_skor  # -19 skoru -20 skorundan yuksek olmali (flat degil)


# --- _skor_kaldirac -----------------------------------------------------


def test_skor_kaldirac_veri_yoksa_none() -> None:
    skor, gerekce = scorer._skor_kaldirac(None, scorer.CONFIG["sanayi"]["kaldirac"])
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_kaldirac_net_nakit_pozisyonu_tam_10() -> None:
    skor, gerekce = scorer._skor_kaldirac(Decimal("-0.5"), scorer.CONFIG["sanayi"]["kaldirac"])
    assert skor == Decimal("10")
    assert "net nakit" in gerekce


def test_skor_kaldirac_cok_iyi_esik_sinirinda() -> None:
    # tam 1x -> "1 < 2.5" bucketine (8-6 araligi) girer, alt sinirdaki deger 8.
    skor, _ = scorer._skor_kaldirac(Decimal("1"), scorer.CONFIG["sanayi"]["kaldirac"])
    assert skor == Decimal("8")


def test_skor_kaldirac_asiri_yuksek_kaldiracta_sifira_yaklasir() -> None:
    skor, gerekce = scorer._skor_kaldirac(Decimal("8"), scorer.CONFIG["sanayi"]["kaldirac"])
    assert skor == Decimal("0")
    assert "aşırı yüksek" in gerekce


def test_skor_kaldirac_makul_araliginda_beklenen_deger() -> None:
    # 1.75x, [1, 2.5) araliginin tam ortasi -> skor (8+6)/2 = 7
    skor, _ = scorer._skor_kaldirac(Decimal("1.75"), scorer.CONFIG["sanayi"]["kaldirac"])
    assert skor == Decimal("7")


# --- _skor_degerleme -----------------------------------------------------


def test_skor_degerleme_valuation_none_ise_atlanir() -> None:
    skor, gerekce = scorer._skor_degerleme(None, scorer.CONFIG["sanayi"]["degerleme"])
    assert skor is None
    assert "fiyat verisi girilmedi" in gerekce


def test_skor_degerleme_sadece_fk_verilirse_sadece_ona_gore_puanlanir() -> None:
    skor, gerekce = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("5")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor is not None
    assert "F/K" in gerekce
    assert "PD/DD" not in gerekce


def test_skor_degerleme_negatif_fk_degerlendirme_disi() -> None:
    skor, gerekce = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("-10")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor is None
    assert "negatif" in gerekce


def test_skor_degerleme_ucuz_fk_ve_pddd_yuksek_skor() -> None:
    skor, _ = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("4"), pb_ratio=Decimal("0.5")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor >= Decimal("9")


def test_skor_degerleme_pahali_fk_ve_pddd_dusuk_skor() -> None:
    skor, _ = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("35"), pb_ratio=Decimal("7")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor <= Decimal("1")


def test_skor_degerleme_zararda_sirkette_dusuk_pddd_deger_tuzagi_tavanina_kirpilir() -> None:
    # Kullanici geri bildirimi: F/K zarar nedeniyle disi birakildiginda,
    # PD/DD TEK BASINA (orn. 0,3 gibi cok ucuz bir PD/DD) puani ~9,5'e
    # tasiyabiliyordu -- "zarar eden sirkette bu kadar yuksek puan mantikli
    # degil" hissi yaratiyordu. Artik bu senaryoda skor 7,5 tavaniyla
    # sinirlanir ve gerekcede "deger tuzagi" uyarisi yer alir.
    skor, gerekce = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("-10"), pb_ratio=Decimal("0.3")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor == Decimal("7.5")
    assert "değer tuzağı" in gerekce
    assert "F/K negatif" in gerekce


def test_skor_degerleme_zararda_ama_pddd_zaten_dusuk_skorsa_tavan_uygulanmaz() -> None:
    # Tavan sadece skoru YUKARI sinirlar -- PD/DD zaten pahaliysa (dusuk skor)
    # kirpma gereksiz/etkisiz olmali.
    skor, _ = scorer._skor_degerleme(scorer.ValuationInput(pe_ratio=Decimal("-10"), pb_ratio=Decimal("6")), scorer.CONFIG["sanayi"]["degerleme"])
    assert skor < Decimal("7.5")


# --- _skor_bilanco_kalitesi -----------------------------------------------------


def test_skor_bilanco_kalitesi_ikisi_de_yoksa_none() -> None:
    skor, gerekce = scorer._skor_bilanco_kalitesi(None, None, scorer.CONFIG["sanayi"]["bilanco_kalitesi"])
    assert skor is None
    assert "atlandı" in gerekce


def test_skor_bilanco_kalitesi_sadece_cari_oran_varsa_calisir() -> None:
    skor, gerekce = scorer._skor_bilanco_kalitesi(Decimal("2"), None, scorer.CONFIG["sanayi"]["bilanco_kalitesi"])
    assert skor is not None
    assert "cari oran" in gerekce
    assert "özkaynak" not in gerekce


# --- _agirlik_dagit_ve_hesapla: agirlik yeniden dagitimi -----------------------------------------------------


def test_agirlik_dagit_tum_bilesenler_varsa_toplam_efektif_agirlik_100() -> None:
    bilesenler = [
        ("A", Decimal("25"), (Decimal("10"), "x")),
        ("B", Decimal("20"), (Decimal("10"), "x")),
        ("C", Decimal("15"), (Decimal("10"), "x")),
        ("D", Decimal("15"), (Decimal("10"), "x")),
        ("E", Decimal("20"), (Decimal("10"), "x")),
        ("F", Decimal("5"), (Decimal("10"), "x")),
    ]
    sonuc = scorer._agirlik_dagit_ve_hesapla("TEST", (2026, 3), "sanayi_holding", bilesenler)
    toplam_efektif = sum(c.weight_effective for c in sonuc.components)
    assert toplam_efektif == Decimal("100")
    assert sonuc.total_score == Decimal("10")  # hepsi 10 puansa toplam da 10 olmali


def test_agirlik_dagit_bir_bilesen_atlanirsa_kalanlar_orantisal_buyur() -> None:
    # Degerleme (%20) atlaniyor; kalan 5 bilesenin nominal toplami 80.
    # Nakit Uretimi (%25) efektifte 25/80*100 = 31.25 olmali.
    bilesenler = [
        ("Nakit Üretimi", Decimal("25"), (Decimal("10"), "x")),
        ("Kaldıraç", Decimal("20"), (Decimal("10"), "x")),
        ("Kârlılık", Decimal("15"), (Decimal("10"), "x")),
        ("Büyüme", Decimal("15"), (Decimal("10"), "x")),
        ("Değerleme", Decimal("20"), (None, "fiyat verisi girilmedi (F/K, PD/DD yok), bileşen atlandı.")),
        ("Bilanço Kalitesi", Decimal("5"), (Decimal("10"), "x")),
    ]
    sonuc = scorer._agirlik_dagit_ve_hesapla("TEST", (2026, 3), "sanayi_holding", bilesenler)

    degerleme = next(c for c in sonuc.components if c.name == "Değerleme")
    nakit = next(c for c in sonuc.components if c.name == "Nakit Üretimi")

    assert degerleme.score is None
    assert degerleme.weight_effective == Decimal("0")
    assert nakit.weight_effective == Decimal("25") / Decimal("80") * Decimal("100")
    assert sonuc.total_score == Decimal("10")


def test_agirlik_dagit_hicbir_bilesen_yoksa_sifir_donmez_hata_vermez() -> None:
    bilesenler = [
        ("A", Decimal("50"), (None, "veri yok")),
        ("B", Decimal("50"), (None, "veri yok")),
    ]
    sonuc = scorer._agirlik_dagit_ve_hesapla("TEST", (2026, 3), "sanayi_holding", bilesenler)
    assert sonuc.total_score == Decimal("0")
    assert sonuc.badge == "RİSKLİ"


# --- Tam entegrasyon: calculator.analyze() -> scorer.score_industrial() -----------------------------------------------------

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    # "_cum" (kumulatif/YTD) alanlari bu testlerde KASITLI OLARAK ceyreklik
    # alanla ayni deger tasir -- bkz. test_calculator.py::_sample_financials notu.
    return {
        "revenue": Decimal(revenue),
        "revenue_cum": Decimal(revenue),
        "gross_profit": Decimal(gross),
        "gross_profit_cum": Decimal(gross),
        "operating_profit": Decimal(op),
        "operating_profit_cum": Decimal(op),
        # KASITLI OLARAK "operating_profit" ile AYNI deger -- bkz.
        # test_calculator.py::_sample_financials notu.
        "operating_profit_ebitda_base": Decimal(op),
        "operating_profit_ebitda_base_cum": Decimal(op),
        "depreciation_amortization": Decimal(dep),
        "depreciation_amortization_cum": Decimal(dep),
        "net_income": Decimal(net),
        "net_income_cum": Decimal(net),
        "cash": Decimal(cash),
        "trade_receivables": Decimal(tr),
        "total_assets": Decimal(assets),
        "financial_debt": Decimal(debt),
        "equity": Decimal(equity),
        "current_assets": Decimal(ca),
        "short_term_liabilities": Decimal(stl),
    }


@pytest.fixture()
def saglikli_analiz() -> calculator.AnalysisResult:
    """Guclu FAVOK marji, dusuk kaldirac, pozitif buyume/karlilik olan
    ornek bir sanayi sirketi -- SAGLAM rozetini beklenir kilan senaryo."""
    financials = {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }
    return calculator.analyze("TESTAS", financials)


def test_score_industrial_fiyat_verisi_olmadan_calisir_ve_deger_uretir(saglikli_analiz) -> None:
    sonuc = scorer.score_industrial(saglikli_analiz)

    assert sonuc.ticker == "TESTAS"
    assert sonuc.template == "sanayi_holding"
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")
    assert len(sonuc.components) == 7

    degerleme = next(c for c in sonuc.components if c.name == "Değerleme")
    assert degerleme.score is None  # fiyat verisi verilmedi
    assert degerleme.weight_effective == Decimal("0")

    # Degerleme disindaki 6 bilesenin efektif agirliklari 100'e tamamlanmali.
    diger_toplam = sum(c.weight_effective for c in sonuc.components if c.name != "Değerleme")
    assert diger_toplam == Decimal("100")

    # Bu senaryo guclu FAVOK marji + dusuk kaldirac + buyume iceriyor -> SAGLAM/DENGELI beklenir.
    assert sonuc.badge in ("SAĞLAM", "DENGELİ")


def test_score_industrial_fiyat_verisiyle_degerleme_bileseni_dahil_olur(saglikli_analiz) -> None:
    sonuc = scorer.score_industrial(saglikli_analiz, valuation=scorer.ValuationInput(pe_ratio=Decimal("10"), pb_ratio=Decimal("1.5")))

    degerleme = next(c for c in sonuc.components if c.name == "Değerleme")
    assert degerleme.score is not None
    assert degerleme.weight_effective == Decimal("17")  # hicbir bilesen atlanmadi, nominal = efektif

    toplam_efektif = sum(c.weight_effective for c in sonuc.components)
    assert toplam_efektif == Decimal("100")


def test_score_industrial_her_bilesenin_gerekce_metni_dolu(saglikli_analiz) -> None:
    sonuc = scorer.score_industrial(saglikli_analiz)
    for bilesen in sonuc.components:
        assert bilesen.reasoning_tr  # bos olmamali


def test_score_industrial_enflasyon_verilirse_reel_buyumeyi_dusurur(saglikli_analiz) -> None:
    sonuc_nominal = scorer.score_industrial(saglikli_analiz)
    sonuc_enflasyonlu = scorer.score_industrial(saglikli_analiz, enflasyon_yoy_pct=Decimal("15"))

    buyume_nominal = next(c for c in sonuc_nominal.components if c.name == "Büyüme")
    buyume_enflasyonlu = next(c for c in sonuc_enflasyonlu.components if c.name == "Büyüme")

    assert buyume_enflasyonlu.score <= buyume_nominal.score
    assert "enflasyon %15" in buyume_enflasyonlu.reasoning_tr


def test_score_industrial_tek_donem_veri_eksikligini_zarafetle_yonetir() -> None:
    # Sadece en yeni donem var -> YoY/QoQ karsilastirma yapilamiyor, cogu
    # bilesen atlanacak ama fonksiyon hata firlatmamali.
    financials = {_LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900)}
    analiz = calculator.analyze("TEKDONEM", financials)

    sonuc = scorer.score_industrial(analiz)

    assert Decimal("0") <= sonuc.total_score <= Decimal("10")
    # Kaldirac (TTM icin 4 donem gerektirir) atlanmis olmali.
    kaldirac = next(c for c in sonuc.components if c.name == "Kaldıraç")
    assert kaldirac.score is None


# --- score_insurance / score_bank iskeletleri -----------------------------------------------------


def test_score_insurance_hic_parametre_verilmeden_de_calisir(saglikli_analiz) -> None:
    sonuc = scorer.score_insurance(saglikli_analiz)
    assert sonuc.template == "sigorta"
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")

    prim = next(c for c in sonuc.components if c.name == "Prim Büyümesi")
    teknik = next(c for c in sonuc.components if c.name == "Teknik Denge Marjı")
    assert prim.score is None
    assert teknik.score is None
    # ROE calculator.py'den geldigi icin bu bilesen calismis olmali.
    roe = next(c for c in sonuc.components if c.name == "Özkaynak Kârlılığı (ROE)")
    assert roe.score is not None


def test_score_bank_hic_parametre_verilmeden_de_calisir(saglikli_analiz) -> None:
    sonuc = scorer.score_bank(saglikli_analiz)
    assert sonuc.template == "banka"
    assert Decimal("0") <= sonuc.total_score <= Decimal("10")

    # Sermaye Yeterlilik Orani KALDIRILDI (regulatuar veri kaynakta yok,
    # HER ZAMAN "-" gosteriyordu) -- yerine aktif_karliligi/ozkaynak_aktif_orani
    # geldi; disaridan parametre verilmedigi icin bu ikisi de atlanmis olmali.
    assert not any(c.name == "Sermaye Yeterlilik Oranı" for c in sonuc.components)
    roa = next(c for c in sonuc.components if c.name == "Aktif Kârlılığı (ROA)")
    oao = next(c for c in sonuc.components if c.name == "Özkaynak/Aktif Oranı")
    assert roa.score is None
    assert oao.score is None


def test_score_bank_aktif_karliligi_ve_ozkaynak_aktif_orani_hesaplanir(saglikli_analiz) -> None:
    sonuc = scorer.score_bank(
        saglikli_analiz,
        aktif_karliligi_pct=Decimal("2.8"),
        ozkaynak_aktif_orani_pct=Decimal("11"),
    )
    roa = next(c for c in sonuc.components if c.name == "Aktif Kârlılığı (ROA)")
    oao = next(c for c in sonuc.components if c.name == "Özkaynak/Aktif Oranı")
    assert roa.score is not None
    assert oao.score is not None


def test_score_bank_agirliklar_yuzde_yuze_tamamlanir() -> None:
    """5 bilesenin nominal agirliklari (25+20+20+15+20) tam %100 olmali."""
    cfg = scorer.CONFIG["banka"]
    toplam = sum(cfg[k]["agirlik"] for k in cfg)
    assert toplam == Decimal("100")
