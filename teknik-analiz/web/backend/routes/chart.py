"""GET /api/chart — bir sembol/zaman dilimi/indikatör için OHLCV + çizim
primitifleri (Level/Line/Box/Polygon/Marker) JSON olarak.

Hesap tlab'ın mevcut motorundan (`tlab/viz/live.py::compute_live`) GELİR —
burada yeniden hesap YAPILMAZ. Declutter (hangi Level/Box/Polygon/Marker
gösterilir) `tlab/viz/renderer.py`'nin ZATEN var olan saf-veri fonksiyonları
(`_filter_confirmed_patterns`/`_filter_harmonic_result`/`_declutter_levels`)
çağrılarak uygulanır — mantık burada TEKRAR YAZILMAZ, yalnızca Plotly figürü
üretilmeden (`render()`'a hiç girilmeden) IndicatorResult üzerinde çalıştırılır.
Mumların/etiketlerin piksel-uzayında nereye yerleştirileceği (sağ boşluk,
üst üste binme önleme) bilerek BURADA çözülmez — bu, tarayıcının gerçek
piksel boyutunu bilen frontend'in işi (bkz. plan dosyası, "Mimari Karar")."""

from __future__ import annotations

import json
import math

import pandas as pd
from fastapi import APIRouter, HTTPException

from tlab.core.types import IndicatorResult
from tlab.viz.live import STRUCTURE_REPORT_NAME, compute_live, compute_structure_report
from tlab.viz.renderer import _declutter_levels, _filter_confirmed_patterns, _filter_harmonic_result

router = APIRouter(tags=["chart"])


def _apply_declutter(result: IndicatorResult) -> IndicatorResult:
    """`renderer.py::_render_price_based`'in (satır ~495-539) uyguladığı AYNI
    sırayı, Plotly'e hiç girmeden tekrar eder."""
    if result.indicator.startswith("patterns."):
        result = _filter_confirmed_patterns(result)
    if result.indicator.startswith("harmonic."):
        result = _filter_harmonic_result(result)
    result.levels = _declutter_levels(result.levels)
    return result


def _ohlcv_records(df: pd.DataFrame) -> list[dict[str, float | int]]:
    """`lightweight-charts`'ın beklediği `{time, open, high, low, close, volume}`
    biçimi — `time` unix saniye (UTC)."""
    out = []
    for ts, row in df.iterrows():
        if any(math.isnan(v) for v in (row["open"], row["high"], row["low"], row["close"])):
            continue
        out.append(
            {
                "time": int(pd.Timestamp(ts).timestamp()),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]) if not math.isnan(row["volume"]) else 0.0,
            }
        )
    return out


@router.get("/chart")
def get_chart(symbol: str, tf: str, indicator: str, market: str = "bist") -> dict[str, object]:
    try:
        if indicator == STRUCTURE_REPORT_NAME:
            ps_result, sf_result, df = compute_structure_report(symbol, tf, market)
            merged = IndicatorResult(
                indicator=STRUCTURE_REPORT_NAME,
                version=ps_result.version,
                params_hash=ps_result.params_hash,
                symbol=symbol,
                timeframe=ps_result.timeframe,
                signals=ps_result.signals + sf_result.signals,
                levels=ps_result.levels + sf_result.levels,
                lines=ps_result.lines + sf_result.lines,
                boxes=ps_result.boxes,
                polygons=[],
                markers=ps_result.markers + sf_result.markers,
                series=ps_result.series,
                series_layout=ps_result.series_layout,
                last_state={**ps_result.last_state, **sf_result.last_state},
            )
            result = _apply_declutter(merged)
        else:
            result, df = compute_live(indicator, symbol, tf, market)
            if df is None:
                raise HTTPException(422, "Pair indikatörler bu endpoint'te henüz desteklenmiyor")
            result = _apply_declutter(result)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Veri bulunamadı: {exc}") from exc

    return {
        "symbol": symbol,
        "market": market,
        "tf": tf,
        "ohlcv": _ohlcv_records(df),
        "result": json.loads(result.to_json()),
    }
