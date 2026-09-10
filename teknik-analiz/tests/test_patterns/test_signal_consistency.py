"""Durum etiketi ile AL/SAT işaretinin TUTARLILIĞI — tüm sınır-çizgili
formasyonlar için tek denetim.

Kullanıcının kuralı (2026-09-10): "al sat sinyalleri veya tamamlandı gibi
sinyaller tam olmalı eksik hatalı sinyal olmamalı". Somut karşılığı:

* Kırılım GERÇEKLEŞMİŞSE (ONAY / RETEST TUTTU / HEDEFE ULAŞTI) grafikte
  MUTLAKA bir AL/SAT işareti olmalı — `to_pattern` bu işareti yalnızca
  `pattern_entry_{direction}:{pattern_id}` marker'ı varsa kurar, yoksa
  onaylanmış bir formasyon SESSİZCE işaretsiz kalırdı.
* Kırılım HENÜZ OLMAMIŞSA (OLUŞUYOR) işaret OLMAMALI — "erken sinyal".
* Yön/taraf tutarlı olmalı: long -> AL, mumun ALTINDA, bullish rol.

Ayrıca formasyon İÇERMEYEN serilerde (kanal, yatay sıkışma, bayrak) hiç
aday çıkmadığı da doğrulanır — yanlış pozitif kapısı.
"""

from __future__ import annotations

import pytest

from tlab.chart import fixtures as fx
from tlab.core.types import Timeframe, validate_ohlcv
from tlab.indicators.bootstrap import scaled_factory
from tlab.indicators.patterns.boundary_adapter import to_pattern

# Kırılım gerçekleşmiş durumlar -- işaret ZORUNLU.
_BROKEN_STATES = {"ONAY", "RETEST TUTTU", "HEDEFE ULAŞTI"}

_PATTERN_CASES = [
    ("ucgen_simetrik", lambda: fx.triangle(kind="simetrik"), "patterns.triangle"),
    ("ucgen_yukselen", lambda: fx.triangle(kind="yukselen"), "patterns.triangle"),
    ("ucgen_alcalan", lambda: fx.triangle(kind="alcalan"), "patterns.triangle"),
    ("takoz_alcalan", lambda: fx.wedge(kind="alcalan"), "patterns.wedge"),
    ("takoz_yukselen", lambda: fx.wedge(kind="yukselen"), "patterns.wedge"),
    ("megafon_tepe", lambda: fx.broadening(kind="tepe"), "patterns.broadening"),
    ("megafon_dip", lambda: fx.broadening(kind="dip"), "patterns.broadening"),
]


@pytest.mark.parametrize(("label", "make_df", "indicator"), _PATTERN_CASES)
def test_signal_marker_matches_pattern_state(label, make_df, indicator) -> None:
    df = make_df()
    validate_ohlcv(df)
    pat = to_pattern(scaled_factory(indicator, Timeframe.D1)(df), df)
    assert pat is not None, f"{label}: {indicator} bu fikstürde aday bulmalı"

    broken = pat.state in _BROKEN_STATES
    assert (pat.signal is not None) == broken, (
        f"{label}: durum {pat.state!r} ama işaret={pat.signal is not None} -- "
        "kırılmış formasyon işaretsiz ya da oluşan formasyon erken işaretli"
    )
    if pat.signal is not None:
        s = pat.signal
        # long -> AL, mumun ALTINDA, bullish; short -> SAT, ÜSTÜNDE, bearish
        assert (s.role == "bullish") == s.below, (
            f"{label}: rol {s.role!r} ile konum (below={s.below}) çelişiyor"
        )
        assert s.text in ("AL", "SAT"), f"{label}: beklenmeyen işaret metni {s.text!r}"
        assert (s.text == "AL") == (s.role == "bullish")


@pytest.mark.parametrize(
    ("label", "make_df", "indicator"),
    [
        ("yukselen_kanal", fx.rising_channel, "patterns.triangle"),
        ("yatay_sikisma", fx.range_market, "patterns.triangle"),
        ("direk_bayrak", fx.flag_after_pole, "patterns.wedge"),
    ],
)
def test_no_false_positive_on_series_without_that_pattern(label, make_df, indicator) -> None:
    """Yakınsayan sınırı OLMAYAN seride üçgen/takoz ÇIKMAMALI."""
    df = make_df()
    assert to_pattern(scaled_factory(indicator, Timeframe.D1)(df), df) is None, (
        f"{label}: {indicator} yanlış pozitif üretti"
    )


def test_every_emitted_state_has_a_turkish_label() -> None:
    """Durum makinesinin ürettiği HER ek Türkçe sözlükte olmalı.

    Eksik bir ek `suffix.upper()`e düşüyor, yani kullanıcı grafikte
    "RETEST_HOLD" gibi ham bir dize görürdü.
    """
    from tlab.core.pattern_state import SUFFIX_LABEL_TR

    emitted = {"pending", "confirmed", "retest_hold", "target_reached",
               "invalidated", "expired"}
    assert emitted <= set(SUFFIX_LABEL_TR), (
        f"Türkçe karşılığı olmayan durum: {emitted - set(SUFFIX_LABEL_TR)}"
    )
