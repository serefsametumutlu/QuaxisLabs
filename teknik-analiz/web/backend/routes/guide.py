"""GET /api/guide — bir gösterge için `tlab/viz/labels_tr.py::signal_reading()`
rehberi (nereye bak / ne ölçer / değerler ne demek / AL sinyali ne zaman
oluşur). Bilinmeyen/rehberi olmayan gösterge için `null` döner — frontend
paneli hiç göstermemeli."""

from __future__ import annotations

from fastapi import APIRouter

from tlab.viz.labels_tr import signal_reading

router = APIRouter(tags=["guide"])


@router.get("/guide")
def get_guide(indicator: str) -> dict[str, str] | None:
    reading = signal_reading(indicator)
    return dict(reading) if reading else None
