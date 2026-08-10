"""src/analysis/multi_scenario_valuation.py testleri -- kısa/uzun dönem/
sektör çarpan üçlemesi + IQR aykırı değer temizliği (SAF matematik, I/O
yok). Beklenen değerler ELLE hesaplanmıştır."""

from __future__ import annotations

from decimal import Decimal

from src.analysis.multi_scenario_valuation import compute_multi_scenario_valuation, trim_outliers_iqr


def test_trim_outliers_iqr_acik_aykiri_degeri_cikarir():
    values = [Decimal(x) for x in [8, 9, 10, 10, 11, 12, 100]]
    trimmed = trim_outliers_iqr(values)
    assert Decimal(100) not in trimmed
    assert Decimal(10) in trimmed


def test_trim_outliers_iqr_az_gozlemde_oldugu_gibi_doner():
    values = [Decimal(5), Decimal(50)]
    assert trim_outliers_iqr(values) == [Decimal(5), Decimal(50)]


def test_compute_multi_scenario_valuation_tam_senaryo():
    # F/K: sektor [8,9,10] -> ort 9; kisa [10,11,12] -> ort 11; uzun [10,10,10,10]-> ort 10
    # own TTM net kar = 1000, share_capital = 100 -> her F/K icin hedef = (carpan*1000)/100
    result = compute_multi_scenario_valuation(
        sector_pe=[Decimal(8), Decimal(9), Decimal(10)],
        sector_pb=[Decimal(1), Decimal(1.2), Decimal(1.4)],
        sector_ev_ebitda=[Decimal(5), Decimal(6), Decimal(7)],
        short_term_pe=[Decimal(10), Decimal(11), Decimal(12)],
        short_term_pb=[],
        short_term_ev_ebitda=[],
        long_term_pe=[Decimal(10)] * 4,
        long_term_pb=[],
        long_term_ev_ebitda=[],
        ttm_net_income=Decimal(1000),
        current_equity=Decimal(2000),
        ttm_ebitda=Decimal(500),
        share_capital=Decimal(100),
        net_debt=Decimal(1000),
    )
    assert result.pe.scenarios[0].multiple == Decimal(9)  # sektor ort
    assert result.pe.scenarios[0].target_price == Decimal(90)  # (9*1000)/100
    assert result.pe.scenarios[1].multiple == Decimal(11)  # kisa donem ort
    assert result.pe.scenarios[2].multiple == Decimal(10)  # uzun donem ort
    # blended = (90 + 110 + 100) / 3 = 100
    assert result.pe.blended_target_price == Decimal(100)
    # PD/DD ve FD/FAVok icin sadece sektor verisi var (kisa/uzun bos -> None)
    assert result.pb.scenarios[1].target_price is None
    assert result.final_target_price_a is not None


def test_compute_multi_scenario_valuation_zarar_eden_sirkette_fk_hedefi_none_doner():
    """CANLI hata (KORDS, 2026-08-08): TTM net kar negatifken F/K hedefi
    -120,98 TL gibi anlamsız bir sayı üretiyordu -- artık None dönmeli,
    PD/DD gibi diğer çarpanlar (pozitif temel değere sahipse) etkilenmemeli."""
    result = compute_multi_scenario_valuation(
        sector_pe=[], sector_pb=[], sector_ev_ebitda=[],
        short_term_pe=[Decimal(90), Decimal(85), Decimal(95), Decimal(88)],
        short_term_pb=[Decimal(0.6), Decimal(0.7), Decimal(0.9), Decimal(0.8)],
        short_term_ev_ebitda=[],
        long_term_pe=[Decimal(90), Decimal(85), Decimal(95), Decimal(88)],
        long_term_pb=[Decimal(0.6), Decimal(0.7), Decimal(0.9), Decimal(0.8)],
        long_term_ev_ebitda=[],
        ttm_net_income=Decimal(-5000),  # zarar
        current_equity=Decimal(20000),
        ttm_ebitda=None,
        share_capital=Decimal(100),
        net_debt=Decimal(1000),
    )
    assert result.pe.blended_target_price is None
    for scenario in result.pe.scenarios:
        assert scenario.target_price is None
    assert result.pb.blended_target_price is not None
    assert result.final_target_price_a == result.pb.blended_target_price


def test_compute_multi_scenario_valuation_veri_yoksa_none_doner():
    result = compute_multi_scenario_valuation(
        sector_pe=[], sector_pb=[], sector_ev_ebitda=[],
        short_term_pe=[], short_term_pb=[], short_term_ev_ebitda=[],
        long_term_pe=[], long_term_pb=[], long_term_ev_ebitda=[],
        ttm_net_income=None, current_equity=None, ttm_ebitda=None,
        share_capital=None, net_debt=None,
    )
    assert result.final_target_price_a is None
