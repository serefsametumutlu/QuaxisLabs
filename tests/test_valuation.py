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


def test_peer_yoksa_sektor_goreli_kisim_none_kalir() -> None:
    result = compute_valuation_assessment(Decimal(15), Decimal(2), [], None, None, None)
    assert result.sector_avg_pe is None
    assert result.verdict is None
    assert result.has_data is False


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
