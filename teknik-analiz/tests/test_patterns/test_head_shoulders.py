"""patterns.head_shoulders testleri.

Elle inşa edilmiş bir TOBO senaryosu (`_tobo_ohlcv`; pivotlar GERÇEK
`find_pivots`/`alternate_pivots`/`find_hs` çalıştırılarak doğrulanmıştır):
l1(idx2,97) -> h1(idx7,117) -> head(idx12,88) -> h2(idx16,117) ->
l3(idx20,95, `finalized_idx=23`'te PENDING doğar — idx21'deki küçük tepe
l3'ü finalize eder) -> idx24'te boyun kırılımı (kapanış 118>~115) ->
idx29'da hedefe ulaşma (kapanış 148>=146).

`test_pending_born_at_l3_finalized_idx_not_confirmed_idx` bu modülü
yazarken bulunan GERÇEK hatayı (bkz. head_shoulders.py docstring'i) kilitler:
`HSPattern.created_idx` (=l3.confirmed_idx=22) YANLIŞ born barı olurdu —
doğrusu `l3.finalized_idx` (23)'tür."""

from __future__ import annotations

import pandas as pd
import pytest

from tests.test_structure.fixtures import build_registry_smoke_ohlcv
from tlab.core.errors import RegistryError
from tlab.core.indicator import registry
from tlab.indicators.patterns.head_shoulders import HeadShouldersIndicator, HeadShouldersParams
from tlab.testing.repaint import repaint_test

_TZ = "Europe/Istanbul"

_ROWS: list[tuple[float, float, float, float]] = [
    (105, 104, 106, 103),
    (104, 101, 105, 100),
    (101, 98, 102, 97),      # l1 low=97 (idx2)
    (98, 100, 101, 98.5),
    (100, 103, 104, 99.5),
    (103, 108, 109, 102),
    (108, 113, 114, 107),
    (113, 116, 117, 112),    # h1 high=117 (idx7)
    (116, 113, 117, 112),
    (113, 108, 114, 107),
    (108, 102, 109, 101),
    (102, 95, 103, 94),
    (95, 90, 96, 88),        # head low=88 (idx12)
    (90, 93, 94, 89),
    (93, 100, 101, 92),
    (100, 110, 111, 99),
    (110, 116, 117, 108),    # h2 high=117 (idx16)
    (116, 112, 117, 110),
    (112, 105, 113, 104),
    (105, 99, 106, 97),
    (99, 96, 100, 95),       # l3 low=95 (idx20, confirmed_idx=22)
    (96, 101, 108, 95.5),    # l3'ü finalize eden küçük tepe (finalized_idx=23)
    (101, 99, 101.5, 98),
    (99, 103, 104, 98.5),    # born (idx23): l3.finalized_idx
    (103, 118, 119, 102),    # boyun kırılımı (idx24)
    (118, 124, 125, 117),
    (124, 130, 131, 123),
    (130, 138, 139, 129),
    (138, 144, 145, 137),
    (144, 148, 149, 143),    # hedefe ulaşma (idx29)
]


def _tobo_ohlcv() -> pd.DataFrame:
    """`open` kasıtlı olarak `close`'a EŞİTLENİR (bu indikatör `open`
    kolonunu hiç okumaz) — yalnızca `high`/`low`/`close` pivot/kırılım
    geometrisi için özenle seçilmiştir, `validate_ohlcv`'in `low<=close<=high`
    şartını basitçe garanti eder."""
    idx = pd.date_range("2024-01-02", periods=len(_ROWS), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [{"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0} for _o, c, h, lo in _ROWS],
        index=idx,
    )


def _params() -> HeadShouldersParams:
    # prior_trend_lookback=3: l1.bar_idx=2 -- lookback'in daha büyük her
    # değeri pencereyi sığdıramaz (bkz. prior_trend docstring'i,
    # window_start=start_idx-lookback+1<0 -> her zaman False). Ampirik
    # doğrulama: lookback=3 -> (True, t=-116.6) (fixture'ın idx0-2 kapanışı
    # zaten net düşüyor); min_depth_pct/min_depth_atr varsayılanları
    # (0.04/2.5) fixture'ın depth=29 / atr[23]=6.51 değerleriyle zaten
    # rahatça geçiyor, gevşetmeye gerek yok.
    return HeadShouldersParams(
        left=2, right=2, zigzag_method="fixed", kind="tobo", prior_trend_lookback=3
    )


def test_pending_born_at_l3_finalized_idx_not_confirmed_idx() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    pending = next(s for s in result.signals if s.payload["event"] == "tobo_pending")
    assert pending.bar_time == df.index[23]
    assert pending.bar_time != df.index[22]  # l3.confirmed_idx -- YANLIŞ olurdu


def test_neckline_break_confirms_and_reaches_target() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "tobo_confirmed")
    completed = next(s for s in result.signals if s.state == "completed")
    assert confirmed.bar_time == df.index[24]
    assert confirmed.payload["break_price"] == pytest.approx(118.0)
    assert completed.bar_time == df.index[29]
    assert completed.payload["target"] == pytest.approx(146.0, abs=0.5)


def test_require_volume_confirm_suppresses_confirmed_when_volume_fails() -> None:
    """Faz 0.5, A4: fixture hacmi SABİT (1000) -- vol_k=1.2 varsayılanıyla
    sağ omuz hacmi kırılım hacmini AŞAMAZ (volume_profile_ok HER ZAMAN
    False). require_volume_confirm=True iken confirmed sinyali hiç
    ÜRETİLMEMELİ."""
    df = _tobo_ohlcv()
    params = HeadShouldersParams(left=2, right=2, zigzag_method="fixed", kind="tobo",
                                  prior_trend_lookback=3, require_volume_confirm=True)
    result = HeadShouldersIndicator(params).compute(df)
    assert not any(s.payload["event"] == "tobo_confirmed" for s in result.signals)
    # K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): confirm_
    # signal() None dönerse (hiç onaylanmamış aday) ne hedef Level'i ne
    # AL/SAT/KIRILIM/ONAY/HEDEF marker'ı üretilmemeli.
    assert not any(lv.style == "pattern_target" for lv in result.levels)
    for prefix in (
        "pattern_entry_", "pattern_breakout:", "pattern_retest_ok:", "pattern_target_hit:",
    ):
        assert not any(m.kind.startswith(prefix) for m in result.markers)


def test_require_volume_confirm_false_keeps_default_behavior() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "tobo_confirmed")
    assert confirmed.payload["volume_profile_ok"] is False  # ölçüldü ama FİLTRELEMEDİ


def test_shoulder_markers_present() -> None:
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    texts = {m.text for m in result.markers}
    assert {"SOL OMUZ", "BAŞ", "SAĞ OMUZ"} <= texts


def test_entry_marker_emitted_at_confirmation() -> None:
    """2026-09-04: kullanıcı "nerede AL sinyali geldiğini de yazman
    gerekiyor" dedi — TOBO (long yön) için kırılım onaylandığında ayrı bir
    `pattern_entry_long:{pid}` marker'ı, metni "AL" olarak eklenmelidir.

    K3 düzeltmesi (2026-09-05, bkz. docs/GORSEL_HATA_TESHISI.md): bu test
    ESKİDEN `entry.t == last_sig.bar_time` bekliyordu -- bu fixture'da
    `last_sig` formasyon HEDEFE ULAŞTIĞINDA (`completed`) zincirin SON
    olayı oluyor, yani test AL işaretinin GİRİŞ yerine HEDEFE konmasını
    (kullanıcının birebir şikayet ettiği hata) doğru sanıp kilitliyordu.
    Artık AL, kırılım onayı (`_confirmed`) barına konur."""
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    entry = next(m for m in result.markers if m.kind.startswith("pattern_entry_long:"))
    assert entry.text == "AL"
    confirmed = next(s for s in result.signals if s.payload["event"].endswith("_confirmed"))
    assert entry.t == confirmed.bar_time
    last_sig = result.signals[-1]
    assert last_sig.state in ("confirmed", "completed")
    if last_sig.state == "completed":
        assert entry.t != last_sig.bar_time


def test_asymmetric_shoulder_time_ratio_filters_pattern_out() -> None:
    """Sol omuz->baş ve baş->sağ omuz süreleri (10 bar / 8 bar) aslında
    (0.5,2.0) bandına GİRER — çok dar bir bant (0.9,1.1) ile filtrelenmesi
    beklenir (10/8=1.25 > 1.1)."""
    df = _tobo_ohlcv()
    params = HeadShouldersParams(
        left=2, right=2, zigzag_method="fixed", prior_trend_lookback=3,
        shoulder_time_ratio=(0.9, 1.1),
    )
    result = HeadShouldersIndicator(params).compute(df)
    assert result.signals == []


def test_kind_both_also_scans_obo_independently() -> None:
    df = _tobo_ohlcv()
    params = HeadShouldersParams(
        left=2, right=2, zigzag_method="fixed", kind="both", prior_trend_lookback=3
    )
    result = HeadShouldersIndicator(params).compute(df)
    assert any(s.payload["pattern_name"] == "tobo" for s in result.signals)


def test_hologram_is_three_separate_inverted_triangles() -> None:
    """2026-09-04: kullanıcı elle TradingView'de çizip paylaştığı referansa
    göre hologramın ÜÇ AYRI, apeksi omuz/baş noktasına bakan ters üçgen
    olmasını istedi ("ters üçgen içi dolu Sol Omuz, ters üçgen içi dolu
    Baş, ters üçgen içi dolu Sağ Omuz") — tek bağlı bir candle-izleyen
    çokgen DEĞİL (önceki tur, 2026-09-03 — jaggy/gürültülü duruyordu).
    Komşu üçgenler H1/H2 boyun noktalarını PAYLAŞIR."""
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    holograms = [p for p in result.polygons if p.style == "pattern_hologram"]
    assert len(holograms) == 3
    for h in holograms:
        assert len(h.points) == 3  # her biri basit bir üçgen

    tri1, tri2, tri3 = holograms
    # Üçgen 1: dış-sol (H1 fiyatında, aynalanmış zaman) -> L1 (apeks) -> H1.
    assert tri1.points[1][0] == df.index[2] and tri1.points[1][1] == pytest.approx(97)  # l1
    assert tri1.points[2][0] == df.index[7] and tri1.points[2][1] == pytest.approx(117)  # h1
    assert tri1.points[0][1] == pytest.approx(117)  # dış kenar h1 fiyatında düz

    # Üçgen 2: H1 -> Baş (apeks) -> H2 -- paylaşılan boyun tabanı.
    assert tri2.points[0] == tri1.points[2]  # H1 paylaşılıyor
    assert tri2.points[1][0] == df.index[12] and tri2.points[1][1] == pytest.approx(88)  # baş
    assert tri2.points[2][0] == df.index[16] and tri2.points[2][1] == pytest.approx(117)  # h2

    # Üçgen 3: H2 -> L3 (apeks) -> dış-sağ (H2 fiyatında, aynalanmış zaman).
    assert tri3.points[0] == tri2.points[2]  # H2 paylaşılıyor
    assert tri3.points[1][0] == df.index[20] and tri3.points[1][1] == pytest.approx(95)  # l3
    assert tri3.points[2][1] == pytest.approx(117)  # dış kenar h2 fiyatında düz


# --- Faz 1, 1C — YENİ literatür filtrelerinin her biri GERÇEKTEN eliyor mu ---
# (fixture'ın gerçek ön trendi idx0-2'de düşüyor (lookback=3 ile t=-116.6),
# depth=29 / neckline_avg_price=117 / atr[23]=6.51 -- `_params()`'ın
# gevşetilmiş temel değerlerinden yalnızca TEK BİR parametre sıkılaştırılıp
# diğerleri sabit tutuluyor, `double_top_bottom.py`'nin test dosyasındaki
# AYNI desen.)


def _base_kwargs() -> dict:
    return {
        "left": 2, "right": 2, "zigzag_method": "fixed", "kind": "tobo",
        "prior_trend_lookback": 3,
    }


def test_prior_trend_default_lookback_20_filters_out_fixture() -> None:
    """Varsayılan prior_trend_lookback=20: l1.bar_idx=2 için pencere hiç
    SIĞMAZ (window_start=2-20+1=-17<0) -- `prior_trend` bu durumda HER ZAMAN
    (False, 0.0) döner, eski değer (yok/uygulanmıyordu) bunu hiç ELEMEZDİ."""
    kwargs = _base_kwargs()
    del kwargs["prior_trend_lookback"]  # varsayılan (20) devrede kalsın
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(**kwargs)).compute(df)
    assert result.signals == []


def test_prior_trend_filters_out_when_min_tstat_too_strict() -> None:
    """Fixture'ın ön trendi GERÇEK ama küçük (3 barlık) bir pencerede -- t
    büyük olsa da (-116.6) imkânsız derecede yüksek bir eşik ELEMELİ."""
    kwargs = _base_kwargs()
    kwargs["prior_trend_min_tstat"] = 1000.0
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(**kwargs)).compute(df)
    assert result.signals == []


def test_min_depth_pct_filters_out_shallow_pattern() -> None:
    kwargs = _base_kwargs()
    kwargs["min_depth_pct"] = 0.99  # depth=29/neckline_avg=117 (~%25), %99 asla geçmez
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(**kwargs)).compute(df)
    assert result.signals == []


def test_min_depth_atr_filters_out_when_atr_multiple_too_high() -> None:
    kwargs = _base_kwargs()
    kwargs["min_depth_atr"] = 1000.0
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(**kwargs)).compute(df)
    assert result.signals == []


def test_all_faz1_filters_relaxed_still_produces_confirmed_signal() -> None:
    """Sağlık kontrolü: `_base_kwargs()`'ın (fixture'a kalibre edilmiş, aşırı
    sıkı olmayan) hâliyle formasyon HÂLÂ confirmed'a ulaşmalı -- yukarıdaki
    negatif testlerin "elenme" iddiası gerçekten yalnızca sıkılaştırılan TEK
    parametreden kaynaklanıyor."""
    df = _tobo_ohlcv()
    result = HeadShouldersIndicator(HeadShouldersParams(**_base_kwargs())).compute(df)
    assert any(s.state == "confirmed" for s in result.signals)


def _up_sloping_neckline_rows() -> list[tuple[float, float, float, float]]:
    """`_ROWS`'un h2'si (idx16) 117->130'a YÜKSELTİLMİŞ hâli -- boyun çizgisi
    artık YUKARI eğimli (neckline_slope=1.444, total_rise=~%10.5, varsayılan
    neck_total_slope_max=0.15 içinde kalır). idx24'teki kapanış (133) h2.price
    (130)'u AŞAR ama boyun çizgisinin o bardaki EKSTRAPOLE değerini (141.56)
    AŞMAZ -- bu, `break_rule="right_armpit"` düzeltmesinin (bkz. head_
    shoulders.py docstring'i) GERÇEKTEN devrede olduğunu kanıtlayan senaryo:
    eski (buggy) mantık hep `neckline_value_at(t)`'yi kullansaydı idx24'te
    HİÇ onaylanmazdı."""
    return [
        (105, 104, 106, 103),
        (104, 101, 105, 100),
        (101, 98, 102, 97),      # l1 low=97 (idx2)
        (98, 100, 101, 98.5),
        (100, 103, 104, 99.5),
        (103, 108, 109, 102),
        (108, 113, 114, 107),
        (113, 116, 117, 112),    # h1 high=117 (idx7)
        (116, 113, 117, 112),
        (113, 108, 114, 107),
        (108, 102, 109, 101),
        (102, 95, 103, 94),
        (95, 90, 96, 88),        # head low=88 (idx12)
        (90, 93, 94, 89),
        (93, 100, 101, 92),
        (100, 110, 111, 99),
        (110, 129, 130, 108),    # h2 high=130 (idx16) -- YUKARI eğimli boyun
        (129, 112, 130, 110),
        (112, 105, 113, 104),
        (105, 99, 106, 97),
        (99, 96, 100, 95),       # l3 low=95 (idx20)
        (96, 101, 108, 95.5),    # l3'ü finalize eden küçük tepe (idx21)
        (101, 99, 101.5, 98),
        (99, 103, 104, 98.5),    # born (idx23): l3.finalized_idx
        (103, 133, 134, 102),    # sağ koltukaltı kırılımı: kapanış 133 (idx24)
        (133, 138, 139, 132),
        (138, 144, 145, 137),
        (144, 150, 151, 143),
        (150, 156, 157, 149),
        (156, 162, 163, 155),
    ]


def _up_sloping_neckline_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2024-01-02", periods=len(_up_sloping_neckline_rows()), freq="1D", tz=_TZ)
    return pd.DataFrame(
        [
            {"open": c, "close": c, "high": h, "low": lo, "volume": 1000.0}
            for _o, c, h, lo in _up_sloping_neckline_rows()
        ],
        index=idx,
    )


def test_right_armpit_break_rule_used_when_neckline_slopes_upward() -> None:
    df = _up_sloping_neckline_ohlcv()
    result = HeadShouldersIndicator(_params()).compute(df)
    confirmed = next(s for s in result.signals if s.payload["event"] == "tobo_confirmed")
    assert confirmed.bar_time == df.index[24]
    assert confirmed.payload["break_rule"] == "right_armpit"
    assert confirmed.payload["break_price"] == pytest.approx(133.0)
    # Boyun çizgisinin o bardaki (idx24) ekstrapole değeri ~141.56 -- kırılım
    # fiyatı (133) bunun ALTINDA kalıyor, yani eski "hep neckline_value_at"
    # mantığı bu barda ONAY ÜRETMEZDİ (aşağıdaki assert bunu kilitler).
    assert confirmed.payload["break_price"] < 141.56


def test_registers_in_registry() -> None:
    df = build_registry_smoke_ohlcv()
    try:
        registry.register(HeadShouldersIndicator(), df)
    except RegistryError as exc:
        if "zaten kayıtlı" not in str(exc):
            raise
    assert registry.get("patterns.head_shoulders") is HeadShouldersIndicator


def test_passes_repaint() -> None:
    df = _tobo_ohlcv()
    cut_points = list(range(25, len(df) + 1))
    report = repaint_test(HeadShouldersIndicator(_params()), df, cut_points=cut_points)
    assert report.passed, report.mismatches
