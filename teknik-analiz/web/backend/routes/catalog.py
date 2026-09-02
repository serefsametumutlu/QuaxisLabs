"""GET /api/catalog — kayıtlı indikatörlerin listesi (`tlab list-indicators` ile aynı kaynak)."""

from __future__ import annotations

from fastapi import APIRouter

from tlab.indicators.bootstrap import CATALOG

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def get_catalog() -> list[dict[str, object]]:
    return [
        {
            "name": spec.name,
            "category": spec.category,
            "needs_context": spec.needs_context,
            "needs_universe": spec.needs_universe,
        }
        for spec in CATALOG.values()
    ]
