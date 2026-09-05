"""patterns.double_top_bottom testleri.

Elle inşa edilmiş bir çift dip senaryosu (`_double_bottom_ohlcv`, pivotlar
GERÇEK `find_pivots`/`alternate_pivots` çalıştırılarak doğrulanmıştır —
bkz. yorumlar): dip1(idx2, 97) -> boyun(idx7, 117) -> dip2(idx12, 96,
`finalized_idx=16`'da PENDING doğar) -> idx19'da boyun kırılımı (kapanış
118>117) -> idx23'te hedefe ulaşma (kapanış 138>=137.5)."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.double_top_bottom import (
    DoubleTopBottomIndicator,
    DoubleTopBottomParams,
)
from tlab.testing.repaint import repaint_test

_TZ = "Europe/Istanbul"

_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103),
    (104, 101, 105, 100),
    (101, 98, 102, 97),      # dip1 low=97 (idx2)
    (98, 100, 101, 98.5),
    (100, 103, 104, 99.5),
    (103, 108, 109, 102),
    (108, 113, 114, 107),
    (113, 116, 117, 112),    # boyun (neckline) high=117 (idx7)
    (116, 113, 117, 112),
    (113, 110, 114, 109),
    (110, 105, 111, 104),
    (105, 101, 106, 100),
    (101, 97, 102, 96),      # dip2 low=96 (idx12)
    (97, 100, 101, 96.5),
    (100, 104, 105, 99.5),   # ufak ara tepe (dip2'yi finalize eder, idx14)
    (104, 100, 104.5, 99),
    (100, 98, 101, 97.5),    # born (idx16): dip2.finalized_idx
    (98, 103, 104, 97),
    (103, 110, 111, 102),
    (110, 118, 119, 109),    # boyun kırılımı: kapanış 118>117 (idx19)
    (118, 123, 124, 117),
    (123, 128, 129, 122),
    (128, 132, 133, 127),
    (132, 138, 139, 131),    # hedefe ulaşma: kapanış 138>=137.5 (idx23)
]


def _double_bottom_ohlcv() -> pd.DataFrame:
    """`open` kasıtlı olarak `close`'a EŞİTLENİR (bu indikatör `open`
    kolonunu hiç okumaz) — yalnızca `high`/`low`/`close` pivot/kırılım
    geometrisi için özenle seçilmiştir, `validate_ohlcv`'in `low<=close<=high`
    şartını basitçe garanti eder."""
    idx = pd.date_range("2024-01-02", periods=len(_ROWS), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [{"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0} for _o, c, h, lo in _ROWS],
        index=idx,
    )


def _params() -> DoubleTopBottomParams:
    # Faz 0.5: sistem varsayılanı zigzag_method="atr"; bu dosyanın küçük el
    # yapımı fixture'ları ATR zigzag'in ısınma penceresine sığmıyor — bant
    # mekaniğini test ettikleri için bilinçli olarak "fixed"e sabitlendi.
    #
    # Faz 1: yeni literatür filtreleri (min_bars_between=22, prior_trend_
    # lookback=20 vb.) bu KÜÇÜK el yapımı fixture'a (24 bar) sığmaz -- bu
    # dosya formasyon MEKANİĞİNİ (pending/confirmed/completed, hedef,
    # marker, hologram) test ediyor, YENİ filtrelerin doğruluğu AYRI
    # testlerle (aşağıda) doğrulanıyor. min_bars_between=10 fixture'ın
    # GERÇEK p1-p2 mesafesiyle (idx2->idx12) TAM eşleşir; prior_trend_
    # lookback=3 (fixture'da p1=idx2'den önce yalnızca 3 bar var, idx0-2
    # GERÇEKTEN düşüyor: 104->101->98) + min_tstat=0.5 (gevşek); rise/
    # depth eşikleri fixture'da zaten rahatça geçiyor (depth ~%21, ölçüldü)
    # ama garanti olsun diye sıfırlandı.
    return DoubleTopBottomParams(
        left=2, right=2, zigzag_method="fixed",
        min_bars_between=10, prior_trend_lookback=3, prior_trend_min_tstat=0.5,
        min_rise_between_pct=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    )


def test_pending_born_at_p2_finalized_idx() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    pending = next(s for s in result.signals if s.payload["event"] == "double_bottom_pending")
    assert pending.bar_time == df.index[16]
    assert pending.direction == "long"


def test_neckline_break_confirms_at_expected_bar() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "double_bottom_confirmed")
    assert confirmed.bar_time == df.index[19]
    assert confirmed.payload["neckline"] == pytest.approx(117.0)


def test_target_is_neckline_plus_depth_and_reached() -> None:
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    completed = next(s for s in result.signals if s.state == "completed")
    assert completed.payload["target"] == pytest.approx(137.5, abs=0.01)
    assert completed.bar_time == df.index[23]


def test_entry_marker_emitted_at_confirmation() -> None:
    """2026-09-04: kullanıcı "nerede AL sinyali geldiğini de yazman
    gerekiyor" dedi -- head_shoulders.py'deki AYNI marker altyapısı,
    tüm patterns/*.py dosyalarına portlandı.

    K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): bu test
    ESKİDEN `entry.t == completed.bar_time` bekliyordu -- yani AYNEN
    kullanıcının şikayet ettiği hatayı (AL işareti hedefe konuyor) doğru
    davranış sanıp KİLİTLİYORDU. Artık AL, kırılım onayı (`_confirmed`)
    barına konur -- hedefe ulaşma barından (`completed`) FARKLI bir bar."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    entry = next(m for m in result.markers if m.kind.startswith("pattern_entry_long:"))
    assert entry.text == "AL"
    confirmed = next(s for s in result.signals if s.payload["event"].endswith("_confirmed"))
    assert entry.t == confirmed.bar_time
    completed = next(s for s in result.signals if s.state == "completed")
    assert entry.t != completed.bar_time


def test_require_volume_confirm_suppresses_confirmed_when_volume_fails() -> None:
    """Faz 0.5, A4: fixture hacmi SABİT (1000) -- vol_k=1.2 varsayılanıyla
    eşiği HİÇBİR barda geçmez (volume_ok HER ZAMAN False).
    require_volume_confirm=True iken confirmed sinyali hiç ÜRETİLMEMELİ
    (aday GEÇERSİZLEŞMEZ -- pending sinyali olduğu gibi kalır)."""
    df = _double_bottom_ohlcv()
    params = DoubleTopBottomParams(
        left=2, right=2, zigzag_method="fixed", require_volume_confirm=True,
        min_bars_between=10, prior_trend_lookback=3, prior_trend_min_tstat=0.5,
        min_rise_between_pct=0.0, min_depth_pct=0.0, min_depth_atr=0.0,
    )
    result = DoubleTopBottomIndicator(params).compute(df)
    assert not any(s.state == "confirmed" for s in result.signals)
    assert any(s.payload.get("event", "").endswith("_pending") for s in result.signals)
    # K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): confirm_
    # signal() None dönerse (hiç onaylanmamış aday) ne hedef Level'i ne
    # AL/SAT/KIRILIM/ONAY/HEDEF marker'ı üretilmemeli.
    assert not any(lv.style == "pattern_target" for lv in result.levels)
    for prefix in (
        "pattern_entry_", "pattern_breakout:", "pattern_retest_ok:", "pattern_target_hit:",
    ):
        assert not any(m.kind.startswith(prefix) for m in result.markers)


def test_require_volume_confirm_false_keeps_default_behavior() -> None:
    """Varsayılan (require_volume_confirm=False) davranış DEĞİŞMEMELİ --
    aynı fixture'da confirmed sinyali hâlâ üretilir (bkz.
    test_neckline_break_confirms_at_expected_bar)."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.state == "confirmed")
    assert confirmed.payload["volume_ok"] is False  # ölçüldü ama FİLTRELEMEDİ


def test_no_double_top_false_positive_for_asymmetric_neckline_peaks() -> None:
    """idx7(117)/idx14(105) tepe çifti eq_tol'u (varsayılan 0.02) çok aşıyor
    (~%11) -> hiç double_top adayı üretilmemeli."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    assert all(s.payload["pattern_name"] != "double_top" for s in result.signals)


def test_eq_tol_too_strict_filters_out_pair() -> None:
    df = _double_bottom_ohlcv()
    strict = DoubleTopBottomIndicator(
        DoubleTopBottomParams(left=2, right=2, zigzag_method="fixed", eq_tol=0.001)
    )
    result = strict.compute(df)
    assert result.signals == []


def test_hologram_polygon_is_five_point_mw_silhouette() -> None:
    """Faz 1, 1B DÜZELTMESİ (2026-09-04): eski hâli (p1->p2 arası GERÇEK
    kapanış fiyatı yolu, 11 nokta) görsel olarak AMORF bir leke üretiyordu
    (bkz. STRATEJI_DENETIM_TAM.md — ALTNY örneği). 5 köşeli, boyun
    seviyesine OTURAN M/W silueti: [boyun_sol, uç1, boyun, uç2, boyun_sağ].

    2026-09-04 İKİNCİ DÜZELTME: dış köşeler (boyun_sol/boyun_sağ) artık
    uç1/uç2 ile AYNI zaman damgasını (dikey "direk") PAYLAŞMIYOR — kullanıcı
    geri bildirimiyle (TradingView referansı, "yarım üçgen" görünümü)
    p1<->boyun / boyun<->p2 bar mesafesi dışa doğru aynalanarak eğik kenarlı
    simetrik üçgenlere çevrildi (bkz. `double_top_bottom.py`nin hologram
    yorumu). p1(idx2)->boyun(idx7) mesafesi 5 bar, geriye aynalanınca
    idx=max(0,2-5)=0; boyun(idx7)->p2(idx12) mesafesi 5 bar, ileri
    aynalanınca idx=min(n-1,12+5)=17."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(_params()).compute(df)
    hologram = next(p for p in result.polygons if p.style == "pattern_hologram")
    assert len(hologram.points) == 5
    (t0, y0), (t1, y1), (t2, y2), (t3, y3), (t4, y4) = hologram.points
    neckline = 117.0
    assert t0 == df.index[0]  # boyun_sol -- aynalanmış mesafe df başına clamp edildi
    assert y0 == pytest.approx(neckline)
    assert t1 == df.index[2]  # uç1 (p1)
    assert y1 == pytest.approx(97.0)  # dip1
    assert t2 == df.index[7]  # boyun (neckline pivot)
    assert y2 == pytest.approx(neckline)
    assert t3 == df.index[12]  # uç2 (p2)
    assert y3 == pytest.approx(96.0)  # dip2
    assert t4 == df.index[17]  # boyun_sağ -- p1<->boyun mesafesi kadar ileri aynalanmış
    assert y4 == pytest.approx(neckline)


# --- Faz 1, 1B — YENİ literatür filtrelerinin her biri GERÇEKTEN eliyor mu ---
# (fixture'ın gerçek p1-p2 mesafesi 10 bar, ön trend idx0-2'de düşüyor, depth
# ~%21 -- `_params()`'ın gevşetilmiş temel değerlerinden yalnızca TEK BİR
# parametre sıkılaştırılıp diğerleri sabit tutuluyor.)


def _base_kwargs() -> dict:
    return {
        "left": 2, "right": 2, "zigzag_method": "fixed",
        "min_bars_between": 10, "prior_trend_lookback": 3, "prior_trend_min_tstat": 0.5,
        "min_rise_between_pct": 0.0, "min_depth_pct": 0.0, "min_depth_atr": 0.0,
    }


def test_min_bars_between_default_22_filters_out_fixture() -> None:
    """Varsayılan min_bars_between=22 (LMW: en az bir ay) fixture'ın GERÇEK
    p1-p2 mesafesini (10 bar) elemeli -- eski değer (5) bunu ELEMEZDİ."""
    kwargs = _base_kwargs()
    del kwargs["min_bars_between"]  # varsayılan (22) devrede kalsın
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_max_bars_between_filters_out_too_wide_pair() -> None:
    kwargs = _base_kwargs()
    kwargs["max_bars_between"] = 5  # fixture'ın GERÇEK mesafesi (10) > 5
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_max_bars_between_zero_means_unlimited() -> None:
    kwargs = _base_kwargs()
    kwargs["max_bars_between"] = 0
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert any(s.state == "confirmed" for s in result.signals)


def test_min_rise_between_pct_filters_out_shallow_pair() -> None:
    """Fixture'ın gerçek yükseliş oranı ~%21 -- %99 gibi imkânsız bir eşik
    ELEMELİ."""
    kwargs = _base_kwargs()
    kwargs["min_rise_between_pct"] = 0.99
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_prior_trend_filters_out_when_min_tstat_too_strict() -> None:
    """Fixture'ın ön trendi GERÇEK ama zayıf bir istatistiksel güçle (3
    noktalı pencere) -- imkânsız derecede yüksek bir min_tstat ELEMELİ."""
    kwargs = _base_kwargs()
    kwargs["prior_trend_min_tstat"] = 1000.0
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_min_depth_pct_filters_out_shallow_pattern() -> None:
    kwargs = _base_kwargs()
    kwargs["min_depth_pct"] = 0.99  # depth zaten ~%21, %99 asla geçmez
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_min_depth_atr_filters_out_when_atr_multiple_too_high() -> None:
    kwargs = _base_kwargs()
    kwargs["min_depth_atr"] = 1000.0
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**kwargs)).compute(df)
    assert result.signals == []


def test_all_faz1_filters_relaxed_still_produces_confirmed_signal() -> None:
    """Sağlık kontrolü: `_base_kwargs()`'ın (fixture'a göre kalibre
    edilmiş, hiçbiri aşırı sıkı olmayan) tam hâliyle formasyon HÂLÂ
    confirmed'a ulaşmalı -- yukarıdaki negatif testlerin "elenme" iddiası
    gerçekten yalnızca sıkılaştırılan TEK parametreden kaynaklanıyor."""
    df = _double_bottom_ohlcv()
    result = DoubleTopBottomIndicator(DoubleTopBottomParams(**_base_kwargs())).compute(df)
    assert any(s.state == "confirmed" for s in result.signals)


def test_registers_in_registry() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(DoubleTopBottomIndicator(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.double_top_bottom") is DoubleTopBottomIndicator


def test_passes_repaint() -> None:
    """cut_points, boyun kırılımı ve hedef barlarının HEPSİNİN zaten
    gerçekleştiği son barlardan seçilir (golden_zone.py'nin aynı deseni)."""
    df = _double_bottom_ohlcv()
    cut_points = list(range(20, len(df) + 1))
    report = repaint_test(DoubleTopBottomIndicator(_params()), df, cut_points=cut_points)
    assert report.passed, report.mismatches
