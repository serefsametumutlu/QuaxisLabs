"""tlab.cli'nin scan preset/filtre yardımcıları için testler.

Tam Typer CLI çağrısı (ağ/veri gerektirir) DEĞİL — yalnızca saf
`_load_scan_preset`/`_signal_passes_filter` fonksiyonları, gerçek
`config/scans.yaml`'a karşı test edilir."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tlab.cli import _load_scan_preset, _signal_passes_filter


@dataclass
class _FakeSignal:
    payload: dict[str, Any] = field(default_factory=dict)


def test_break_types_filter() -> None:
    filt = {"break_types": ["downtrend_break"]}
    assert _signal_passes_filter(_FakeSignal({"break_type": "downtrend_break"}), filt)
    assert not _signal_passes_filter(_FakeSignal({"break_type": "uptrend_break"}), filt)


def test_events_filter() -> None:
    filt = {"events": ["golden_zone_reaction"]}
    assert _signal_passes_filter(_FakeSignal({"event": "golden_zone_reaction"}), filt)
    assert not _signal_passes_filter(_FakeSignal({"event": "golden_zone_touch"}), filt)


def test_zone_kind_filter() -> None:
    filt = {"zone_kind": ["demand"]}
    assert _signal_passes_filter(_FakeSignal({"zone_kind": "demand"}), filt)
    assert not _signal_passes_filter(_FakeSignal({"zone_kind": "supply"}), filt)


def test_fresh_filter() -> None:
    filt = {"fresh": True}
    assert _signal_passes_filter(_FakeSignal({"fresh": True}), filt)
    assert not _signal_passes_filter(_FakeSignal({"fresh": False}), filt)
    assert not _signal_passes_filter(_FakeSignal({}), filt)


def test_no_filter_passes_everything() -> None:
    assert _signal_passes_filter(_FakeSignal({}), {})


def test_combined_filters_all_must_match() -> None:
    filt = {"events": ["sd_new"], "zone_kind": ["demand"], "fresh": True}
    assert _signal_passes_filter(
        _FakeSignal({"event": "sd_new", "zone_kind": "demand", "fresh": True}), filt
    )
    assert not _signal_passes_filter(
        _FakeSignal({"event": "sd_new", "zone_kind": "supply", "fresh": True}), filt
    )


def test_scans_yaml_presets_load() -> None:
    for name in ("dusen_kiran", "golden_zone", "demand_taze", "kanal_dibi_hafta"):
        indicators, filt = _load_scan_preset(name)
        assert indicators
        assert isinstance(filt, dict)


def test_unknown_preset_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        _load_scan_preset("yok_boyle_bir_preset")
