"""GET /api/chart.svg — grafiği Faz 3'ün saf SVG motoruyla (`tlab/viz/svg/`)
üretir; Plotly/kaleido'ya hiç uğramaz.

Yalnızca SVG sahnesi PORTLANMIŞ göstergeler için çalışır (şimdilik tek biri:
`patterns.double_top_bottom`) — henüz portlanmamış bir gösterge istenirse
422 döner (sessizce Plotly'e düşmez, çağıran taraf net bir hata görür;
PNG'yi her koşulda isteyen istemciler `chart_png.py`yi kullanmalı, o motoru
kendisi seçer)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from tlab.viz.live import render_live

router = APIRouter(tags=["chart_svg"])

_THEME_MAP = {"dark": "dark", "classic": "light", "editorial": "paper"}


@router.get("/chart.svg")
def get_chart_svg(
    symbol: str, tf: str, indicator: str, market: str = "bist", theme: str = "dark"
) -> Response:
    resolved_theme = _THEME_MAP.get(theme, "dark")
    try:
        fig = render_live(indicator, symbol, tf, market, theme=resolved_theme, engine="svg")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    if not isinstance(fig, str):
        raise HTTPException(422, f"'{indicator}' için SVG sahnesi henüz portlanmadı")

    return Response(
        content=fig, media_type="image/svg+xml",
        headers={"Cache-Control": "private, max-age=300"},
    )
