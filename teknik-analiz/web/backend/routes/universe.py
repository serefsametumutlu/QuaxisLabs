"""GET /api/universe — bir piyasadaki sembol listesi (`config/universe_{market}.txt`)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tlab.core.types import Market
from tlab.data.universe import load_universe

router = APIRouter(tags=["universe"])


@router.get("/universe")
def get_universe(market: str = "bist") -> list[str]:
    try:
        mkt = Market(market.lower())
    except ValueError as exc:
        raise HTTPException(422, f"Bilinmeyen piyasa: {market}") from exc
    try:
        return load_universe(mkt)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
