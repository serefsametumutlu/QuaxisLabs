"""src.analysis.harmonic_presets testleri -- saf veri dogrulamasi, gercek
ag/dosya I/O YOK. `abcd_pattern.detect()` Pine-parity mantigi buraya DAHIL
DEGIL (bkz. test_abcd_pattern.py) -- burada SADECE her formasyon ailesinin
`Params` degerlerinin dogru hesaplandigi/tutarli oldugu dogrulanir.
"""

from __future__ import annotations

import math

import pytest

from src.analysis.abcd_pattern import Params
from src.analysis.harmonic_presets import HARMONIC_PRESETS, _cd_bounds


# ── on-ayar envanteri ───────────────────────────────────────────────────


def test_all_five_families_present():
    assert set(HARMONIC_PRESETS) == {"ABCD", "GARTLEY", "BAT", "BUTTERFLY", "CRAB"}


def test_every_preset_is_params_instance():
    for name, params in HARMONIC_PRESETS.items():
        assert isinstance(params, Params), name


def test_abcd_preset_is_untouched_pine_default():
    """Referans/kontrol grubu: ABCD on-ayari mevcut Pine-parity varsayilanindan
    (use_exact_cd=True, cd_r ~= 1.0) SAPMAMALI."""
    assert HARMONIC_PRESETS["ABCD"] == Params()
    assert HARMONIC_PRESETS["ABCD"].use_exact_cd is True


# ── BC retracement bandi -- 4 harmonik aile icin ORTAK olmali ───────────


@pytest.mark.parametrize("name", ["GARTLEY", "BAT", "BUTTERFLY", "CRAB"])
def test_harmonic_families_share_standard_bc_band(name):
    p = HARMONIC_PRESETS[name]
    assert p.min_bc_retrace == pytest.approx(0.382)
    assert p.max_bc_retrace == pytest.approx(0.886)


@pytest.mark.parametrize("name", ["GARTLEY", "BAT", "BUTTERFLY", "CRAB"])
def test_harmonic_families_use_range_cd_not_exact(name):
    """Klasik ABCD'nin aksine (CD ~= AB), harmonik aileler bir CD ARALIGI
    kullanir -- `use_exact_cd=False` olmali, aksi halde cd_min_ext/cd_max_ext
    hic dikkate alinmaz (bkz. abcd_pattern._is_valid_abcd)."""
    assert HARMONIC_PRESETS[name].use_exact_cd is False


# ── CD bilesik sinir matematigi ─────────────────────────────────────────


def test_cd_bounds_formula_matches_compound_bound_definition():
    """cd_min_ext = k_min * bc_min, cd_max_ext = k_max * bc_max (modul ust
    notundaki "KRITIK matematiksel not"taki formul)."""
    lo, hi = _cd_bounds(1.272, 1.618)
    assert lo == pytest.approx(1.272 * 0.382, abs=1e-4)
    assert hi == pytest.approx(1.618 * 0.886, abs=1e-4)


@pytest.mark.parametrize(
    "name,k_min,k_max",
    [
        ("GARTLEY", 1.272, 1.618),
        ("BAT", 1.618, 2.618),
        ("BUTTERFLY", 1.618, 2.24),
        ("CRAB", 2.24, 3.618),
    ],
)
def test_each_family_cd_bounds_derived_from_its_own_literature_ratio(name, k_min, k_max):
    p = HARMONIC_PRESETS[name]
    expected_lo, expected_hi = _cd_bounds(k_min, k_max)
    assert p.cd_min_ext == pytest.approx(expected_lo)
    assert p.cd_max_ext == pytest.approx(expected_hi)
    assert p.cd_min_ext < p.cd_max_ext


def test_cd_bounds_strictly_increasing_with_extension_aggressiveness():
    """Literatur sirasiyla daha genis CD uzatmasi ister: Gartley < Bat ~=
    Butterfly (ayni k_min, farkli k_max) < Crab -- bu monotonluk cd_max_ext
    uzerinde acikca gorulmeli (Crab en agresif/en genis uzatmali formasyon,
    bkz. Carney Bolum 6)."""
    gartley, bat, butterfly, crab = (
        HARMONIC_PRESETS["GARTLEY"],
        HARMONIC_PRESETS["BAT"],
        HARMONIC_PRESETS["BUTTERFLY"],
        HARMONIC_PRESETS["CRAB"],
    )
    assert gartley.cd_max_ext < butterfly.cd_max_ext < bat.cd_max_ext < crab.cd_max_ext
    assert gartley.cd_min_ext < crab.cd_min_ext


# ── diger alanlar Pine-parity varsayilanindan sapmamali ─────────────────


@pytest.mark.parametrize("name", ["GARTLEY", "BAT", "BUTTERFLY", "CRAB"])
def test_harmonic_presets_do_not_touch_unrelated_pine_parity_fields(name):
    """Sadece BC/CD bantlari + use_exact_cd degisir -- pivot_lookback/
    fib_tolerance/atr_mult/enable_long/enable_short Pine-parity varsayilaninda
    KALMALI (state machine'e/ATR SL'e dokunulmadi)."""
    p = HARMONIC_PRESETS[name]
    default = Params()
    assert p.pivot_lookback == default.pivot_lookback
    assert p.fib_tolerance == default.fib_tolerance
    assert p.atr_mult == default.atr_mult
    assert p.enable_long == default.enable_long
    assert p.enable_short == default.enable_short


@pytest.mark.parametrize("name", HARMONIC_PRESETS.keys())
def test_no_nan_leaks_into_any_preset_field(name):
    """Proje-genelinde NaN disiplini (bkz. abcd_backtest._position_size
    canli hata notu): hicbir Params alani sessizce NaN olmamali."""
    p = HARMONIC_PRESETS[name]
    for field_name in ("min_bc_retrace", "max_bc_retrace", "cd_min_ext", "cd_max_ext", "fib_tolerance", "atr_mult"):
        value = getattr(p, field_name)
        assert not math.isnan(value), f"{name}.{field_name} NaN"


@pytest.mark.parametrize("name", HARMONIC_PRESETS.keys())
def test_presets_are_frozen_and_hashable(name):
    """`Params` `frozen=True` dataclass -- on-ayarlarin yanlislikla mutasyona
    ugramadigini (`run_grid`in ayni Params nesnesini coklu hucrede paylasabildigi
    icin) dogrular."""
    p = HARMONIC_PRESETS[name]
    with pytest.raises(Exception):
        p.cd_min_ext = 0.0  # type: ignore[misc]
