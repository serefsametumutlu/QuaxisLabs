"""GET /api/catalog — kayıtlı indikatörlerin listesi (`tlab list-indicators` ile aynı kaynak)."""

from __future__ import annotations

from fastapi import APIRouter

from tlab.indicators.bootstrap import CATALOG
from tlab.viz.labels_tr import INDICATOR_CATEGORY_TR, tr_indicator

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def get_catalog() -> list[dict[str, object]]:
    return [
        {
            "name": spec.name,
            "category": spec.category,
            "category_label": INDICATOR_CATEGORY_TR.get(spec.category, spec.category),
            "display_name": tr_indicator(spec.name),
            "needs_context": spec.needs_context,
            "needs_universe": spec.needs_universe,
        }
        for spec in CATALOG.values()
    ]


@router.get("/categories")
def get_categories() -> list[dict[str, str]]:
    """Sidebar'ın "Stratejiler" bölümü + tarama sayfasının kategori filtresi
    için tekil kategori listesi (`category`/`category_label`), CATALOG'daki
    gerçek kayıtlardan türetilir — elle bakımlı ikinci bir liste DEĞİL."""
    seen: dict[str, str] = {}
    for spec in CATALOG.values():
        seen.setdefault(spec.category, INDICATOR_CATEGORY_TR.get(spec.category, spec.category))
    return [{"category": k, "category_label": v} for k, v in seen.items()]
