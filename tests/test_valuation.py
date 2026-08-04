"""src/analysis/valuation.py testleri -- sektöre göre değerleme + momentum +
ima edilen hedef fiyat (SAF matematik, I/O yok). Beklenen değerler ELLE
hesaplanmıştır (bkz. 07_BAKIM_KURALLARI.md §3.3: "eşik sınırları elle
hesaplanmış değerlerle test edilir")."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.valuation import PeerMultiple, compute_valuation_assessment

# --- Sektör-göreli değerleme -----------------------------------------------------


def test_own_pahalı_sektor_ortalamasinin_ustunde() -> None:
    # own F/K=15, peer'ler 10 ve 10 -> sektor ort=10, fark = (15-10)/10*100 = %50
    peers = [
        PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None),
        PeerMultiple(ticker="B", pe_ratio=Decimal(10), pb_ratio=None),
    ]
    result = compute_valuation_assessment(Decimal(15), None, peers, None, None, None)
    assert result.sector_avg_pe == Decimal(10)
    assert result.pe_diff_pct == Decimal(50)
    assert result.verdict == "Sektöre Göre Pahalı"
    assert "F/K sektör ortalamasından %50.0 yüksek" in result.verdict_reasoning


def test_own_ucuz_sektor_ortalamasinin_altinda() -> None:
    # own F/K=6, peer ort=10 -> fark = (6-10)/10*100 = -%40
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None)]
    result = compute_valuation_assessment(Decimal(6), None, peers, None, None, None)
    assert result.pe_diff_pct == Decimal(-40)
    assert result.verdict == "Sektöre Göre Ucuz"


def test_own_makul_esik_icinde() -> None:
    # own F/K=11, peer ort=10 -> fark = %10, -20/+20 esiginin icinde -> Makul
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None)]
    result = compute_valuation_assessment(Decimal(11), None, peers, None, None, None)
    assert result.pe_diff_pct == Decimal(10)
    assert result.verdict == "Sektöre Göre Makul"


def test_esik_sinirinda_tam_yirmi_pahali_sayilir() -> None:
    # sağ-kapalı eşik: tam +20 "Pahalı" sayılır (>= karşılaştırması)
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None)]
    result = compute_valuation_assessment(Decimal(12), None, peers, None, None, None)
    assert result.pe_diff_pct == Decimal(20)
    assert result.verdict == "Sektöre Göre Pahalı"


def test_pe_ve_pb_ikisi_de_varsa_ortalamasi_alinir() -> None:
    # F/K farki = %50 (pahali), PD/DD farki = -%50 (ucuz) -> harmanlanmis = 0 -> Makul
    peers = [
        PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=Decimal(4)),
    ]
    result = compute_valuation_assessment(Decimal(15), Decimal(2), peers, None, None, None)
    assert result.pe_diff_pct == Decimal(50)
    assert result.pb_diff_pct == Decimal(-50)
    assert result.verdict == "Sektöre Göre Makul"


def test_negatif_pe_peer_ortalamaya_katilmaz() -> None:
    # zarar eden bir peer'in negatif F/K'si (K3: anlamsiz deger) ortalamadan DISLANIR
    peers = [
        PeerMultiple(ticker="A", pe_ratio=Decimal(-5), pb_ratio=None),
        PeerMultiple(ticker="B", pe_ratio=Decimal(10), pb_ratio=None),
    ]
    result = compute_valuation_assessment(Decimal(10), None, peers, None, None, None)
    assert result.sector_avg_pe == Decimal(10)


def test_peer_yoksa_sektor_goreli_kisim_none_kalir_ama_graham_calisir() -> None:
    # Peer olmasa bile Graham olcutu (own_pe/own_pb'den, SEKTOR GEREKTIRMEZ)
    # calismaya devam eder -- bu yuzden has_data ARTIK True (Faz 16.6).
    result = compute_valuation_assessment(Decimal(15), Decimal(2), [], None, None, None)
    assert result.sector_avg_pe is None
    assert result.verdict is None
    assert result.has_data is True
    assert result.graham_multiple == Decimal(30)


# --- Momentum -----------------------------------------------------


def test_hizli_yukselis_uyari_notu_uretir() -> None:
    # (130-100)/100*100 = %30 -- %25 esiginin ustunde
    result = compute_valuation_assessment(None, None, [], Decimal(130), Decimal(100), None)
    assert result.price_change_1m_pct == Decimal(30)
    assert result.momentum_note is not None
    assert "%30.0" in result.momentum_note
    assert result.has_data is True


def test_esik_altindaki_yukselis_uyari_uretmez() -> None:
    # %20 yukselis, %25 esiginin ALTINDA -> not YOK ama yuzde yine de doner
    result = compute_valuation_assessment(None, None, [], Decimal(120), Decimal(100), None)
    assert result.price_change_1m_pct == Decimal(20)
    assert result.momentum_note is None


def test_dusus_uyari_uretmez() -> None:
    result = compute_valuation_assessment(None, None, [], Decimal(80), Decimal(100), None)
    assert result.price_change_1m_pct == Decimal(-20)
    assert result.momentum_note is None


def test_3_ay_degisimi_bagimsiz_hesaplanir() -> None:
    # 1 ay: (150-140)/140*100 ; 3 ay: (150-100)/100*100 = %50 -- ikisi BAGIMSIZ
    result = compute_valuation_assessment(None, None, [], Decimal(150), Decimal(140), Decimal(100))
    assert result.price_change_1m_pct == (Decimal(10) / Decimal(140) * 100)
    assert result.price_change_3m_pct == Decimal(50)


# --- İma edilen hedef fiyat -----------------------------------------------------


def test_implied_target_fk_bazinda_hesaplanir() -> None:
    # own F/K=8, sektor ort F/K=10, fiyat=80 -> hedef = 80 * (10/8) = 100
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None)]
    result = compute_valuation_assessment(Decimal(8), None, peers, Decimal(80), None, None)
    assert result.implied_target_price == Decimal(100)
    assert result.implied_target_basis == "F/K"
    assert result.implied_upside_pct == Decimal(25)  # (100-80)/80*100


def test_implied_target_fk_yoksa_pddd_bazina_duser() -> None:
    # own F/K negatif (zarar) -> F/K bazi KULLANILAMAZ, PD/DD bazina duser
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=Decimal(4))]
    result = compute_valuation_assessment(Decimal(-5), Decimal(2), peers, Decimal(80), None, None)
    assert result.implied_target_basis == "PD/DD"
    assert result.implied_target_price == Decimal(80) * (Decimal(4) / Decimal(2))


def test_implied_target_fiyat_yoksa_none() -> None:
    peers = [PeerMultiple(ticker="A", pe_ratio=Decimal(10), pb_ratio=None)]
    result = compute_valuation_assessment(Decimal(8), None, peers, None, None, None)
    assert result.implied_target_price is None
    assert result.implied_upside_pct is None


def test_hicbir_veri_yoksa_has_data_false() -> None:
    result = compute_valuation_assessment(None, None, [], None, None, None)
    assert result.has_data is False
    assert result.implied_target_price is None
    assert result.momentum_note is None


# --- Benjamin Graham "savunmacı yatırımcı" ölçütü (Faz 16.6) -----------------------------------------------------


def test_graham_carpani_esik_altinda_ucuz_sayilir() -> None:
    # F/K 10 x PD/DD 2 = 20 <= 22,5 -> Graham'a gore UCUZ
    result = compute_valuation_assessment(Decimal(10), Decimal(2), [], Decimal(100), None, None)
    assert result.graham_multiple == Decimal(20)
    assert result.graham_verdict == "Graham Ölçütüne Göre Ucuz"


def test_graham_carpani_esik_ustunde_pahali_sayilir() -> None:
    # F/K 20 x PD/DD 2 = 40 > 22,5 -> Graham'a gore PAHALI
    result = compute_valuation_assessment(Decimal(20), Decimal(2), [], Decimal(100), None, None)
    assert result.graham_multiple == Decimal(40)
    assert result.graham_verdict == "Graham Ölçütüne Göre Pahalı"


def test_graham_adil_deger_elle_hesaplanmis_karekokle_eslesir() -> None:
    # current_price * sqrt(22.5 / (F/K*PD/DD)) = 100 * sqrt(22.5/20) = 100 * sqrt(1.125)
    result = compute_valuation_assessment(Decimal(10), Decimal(2), [], Decimal(100), None, None)
    beklenen = Decimal(100) * (Decimal("22.5") / Decimal(20)).sqrt()
    assert result.graham_fair_value_price == beklenen
    assert result.graham_upside_pct == (beklenen - Decimal(100)) / Decimal(100) * 100


def test_graham_zarar_eden_sirkette_tanimsiz_none_kalir() -> None:
    # F/K negatif (zarar) -> Graham Sayisi TANIMSIZ (karekok negatif olurdu)
    result = compute_valuation_assessment(Decimal(-5), Decimal(2), [], Decimal(100), None, None)
    assert result.graham_multiple is None
    assert result.graham_fair_value_price is None
    assert result.graham_verdict is None


def test_graham_peer_gerektirmez_sifir_peerle_de_calisir() -> None:
    result = compute_valuation_assessment(Decimal(10), Decimal(2), [], Decimal(100), None, None)
    assert result.peer_count == 0
    assert result.graham_multiple is not None  # peer OLMADAN calisti


# --- Peter Lynch PEG oranı (Faz 16.6) -----------------------------------------------------


def test_peg_esik_altinda_ucuz_sayilir() -> None:
    # F/K 10 / buyume %20 = PEG 0,5 < 0,9 -> ucuz
    result = compute_valuation_assessment(Decimal(10), None, [], None, None, None, growth_rate_pct=Decimal(20))
    assert result.peg_ratio == Decimal("0.5")
    assert result.peg_verdict == "Büyümeye Göre Ucuz (PEG)"


def test_peg_esik_ustunde_pahali_sayilir() -> None:
    # F/K 15 / buyume %10 = PEG 1,5 > 1,1 -> pahali
    result = compute_valuation_assessment(Decimal(15), None, [], None, None, None, growth_rate_pct=Decimal(10))
    assert result.peg_ratio == Decimal("1.5")
    assert result.peg_verdict == "Büyümeye Göre Pahalı (PEG)"


def test_peg_bandin_icinde_makul_sayilir() -> None:
    # F/K 10 / buyume %10 = PEG 1,0 -- 0,9 ile 1,1 arasinda -> makul
    result = compute_valuation_assessment(Decimal(10), None, [], None, None, None, growth_rate_pct=Decimal(10))
    assert result.peg_ratio == Decimal(1)
    assert result.peg_verdict == "Büyümeye Göre Makul (PEG)"


def test_peg_negatif_buyumede_none_kalir() -> None:
    # Kucalen (negatif buyumeli) bir sirkette Lynch'in kurali GECERSIZDIR (K4).
    result = compute_valuation_assessment(Decimal(10), None, [], None, None, None, growth_rate_pct=Decimal(-5))
    assert result.peg_ratio is None
    assert result.peg_verdict is None


def test_peg_buyume_verisi_yoksa_none_kalir() -> None:
    result = compute_valuation_assessment(Decimal(10), None, [], None, None, None, growth_rate_pct=None)
    assert result.peg_ratio is None
    assert result.peg_verdict is None


# --- Aswath Damodaran "İstikrarlı Büyüme (Stable Growth) FCFE" modeli (Faz 16.7) -----------------------------------------------------


def test_damodaran_elle_hesaplanmis_deger_ile_eslesir() -> None:
    # TRY varsayimlari: risksiz faiz %32, ozkaynak risk primi %8 -> r=%40.
    # g = min(buyume %20, risksiz faiz %32) = %20 (tavana takilmiyor).
    # reinvestment_rate = 20/25 = 0,8 -> FCFE = 1000*(1-0,8) = 200.
    # Ozkaynak Degeri = 200*(1+0,20)/((40-20)/100) = 200*1,2/0,20 = 1200.
    # Adil deger/pay = 1200/100 = 12. Guncel fiyat 50 -> upside = (12-50)/50*100 = -%76.
    result = compute_valuation_assessment(
        None, None, [], Decimal(50), None, None,
        growth_rate_pct=Decimal(20), ttm_net_income=Decimal(1000), roe_pct=Decimal(25), share_capital=Decimal(100),
    )
    assert result.damodaran_cost_of_equity_pct == Decimal(40)
    assert result.damodaran_growth_used_pct == Decimal(20)
    assert result.damodaran_fair_value_price == Decimal(12)
    assert result.damodaran_upside_pct == Decimal(-76)
    assert result.damodaran_verdict == "Damodaran Modeline Göre Pahalı"


def test_damodaran_buyume_risksiz_faiz_tavanina_takilir() -> None:
    # buyume %50, risksiz faiz %32 -> g = min(50,32) = %32 KULLANILIR (istikrarli
    # buyume kisiti: hicbir sirket sonsuza kadar ekonomiden hizli buyuyemez).
    result = compute_valuation_assessment(
        None, None, [], None, None, None,
        growth_rate_pct=Decimal(50), ttm_net_income=Decimal(1000), roe_pct=Decimal(50), share_capital=Decimal(100),
    )
    assert result.damodaran_growth_used_pct == Decimal(32)
    assert result.damodaran_fair_value_price == Decimal("59.4")
    # current_price verilmedi -> adil deger hesaplanir ama upside/verdict None kalir
    assert result.damodaran_upside_pct is None
    assert result.damodaran_verdict is None


def test_damodaran_roe_negatifse_none_kalir() -> None:
    result = compute_valuation_assessment(
        None, None, [], Decimal(50), None, None,
        growth_rate_pct=Decimal(10), ttm_net_income=Decimal(1000), roe_pct=Decimal(-5), share_capital=Decimal(100),
    )
    assert result.damodaran_fair_value_price is None
    assert result.damodaran_verdict is None


def test_damodaran_buyume_negatifse_none_kalir() -> None:
    result = compute_valuation_assessment(
        None, None, [], Decimal(50), None, None,
        growth_rate_pct=Decimal(-5), ttm_net_income=Decimal(1000), roe_pct=Decimal(20), share_capital=Decimal(100),
    )
    assert result.damodaran_fair_value_price is None


def test_damodaran_buyume_roeye_esit_veya_buyukse_none_kalir() -> None:
    # g (buyume, tavana takilmadan once %30) >= ROE (%20) -> reinvestment_rate
    # >= 1 (imkansiz, %100'den fazla reinvestment gerektirir) -> K4 geregi None.
    result = compute_valuation_assessment(
        None, None, [], Decimal(50), None, None,
        growth_rate_pct=Decimal(30), ttm_net_income=Decimal(1000), roe_pct=Decimal(20), share_capital=Decimal(100),
    )
    assert result.damodaran_fair_value_price is None


def test_damodaran_zarar_eden_sirkette_none_kalir() -> None:
    result = compute_valuation_assessment(
        None, None, [], Decimal(50), None, None,
        growth_rate_pct=Decimal(10), ttm_net_income=Decimal(-100), roe_pct=Decimal(20), share_capital=Decimal(100),
    )
    assert result.damodaran_fair_value_price is None


def test_damodaran_gerekli_veri_hic_verilmezse_none_kalir() -> None:
    result = compute_valuation_assessment(None, None, [], None, None, None)
    assert result.damodaran_fair_value_price is None
    assert result.damodaran_verdict is None


def test_damodaran_usd_icin_farkli_makro_varsayimlar_kullanilir() -> None:
    # USD (NASDAQ) seti TRY'den farkli (risksiz faiz %4,3, ozkaynak risk primi %4,6).
    result = compute_valuation_assessment(
        None, None, [], Decimal(100), None, None,
        growth_rate_pct=Decimal(3), ttm_net_income=Decimal(1000), roe_pct=Decimal(15), share_capital=Decimal(100),
        currency="USD",
    )
    assert result.damodaran_cost_of_equity_pct == Decimal("8.9")
    assert result.damodaran_growth_used_pct == Decimal(3)
    assert result.damodaran_fair_value_price is not None
