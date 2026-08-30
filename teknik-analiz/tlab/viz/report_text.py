"""Özet Raporu metni — `structure.price_structure` + `structure.swing_fib_abcd`
sonuçlarından KURAL TABANLI Türkçe cümleler üretir. LLM ÇAĞRISI YOK: tamamen
deterministik, iki `IndicatorResult`'ta zaten hesaplanmış değerlerin (POC/VAH/
VAL, RSI, swing yapı etiketi, AB=CD hedefi, MACD kesişimi) if/else ile metne
çevrilmesi — `renderer.py::_pair_header_lines`'ın "biçimlendirme, yeni hesap
değil" ilkesiyle AYNI (bkz. CLAUDE.md 2026-08-30 kaydı, kullanıcı onayı: "Ger-
çek AI" DEĞİL "Deterministik şablon metni" seçildi). Yeni bir tahmin/olasılık
modeli YOK — yalnızca zaten var olan yapının okunur bir anlatıya dökülmesi."""

from __future__ import annotations

import pandas as pd

from tlab.core.types import IndicatorResult

_SWING_LABEL_TR: dict[str, str] = {
    "HH": "Yükselen tepe (HH) — trend yukarı yönlü",
    "HL": "Yükselen dip (HL) — yukarı trend devam ediyor",
    "LH": "Alçalan tepe (LH) — trend aşağı yönlü",
    "LL": "Alçalan dip (LL) — aşağı trend devam ediyor",
}

_ZONE_POSITION_TR: dict[str, str] = {
    "içinde": "Fiyat bir destek/direnç bölgesinin İÇİNDE.",
    "dışında": "Fiyat şu an herhangi bir destek/direnç bölgesinin dışında.",
}


def build_summary_lines(
    ps: IndicatorResult, sf: IndicatorResult, df: pd.DataFrame
) -> list[str]:
    """Rapor panelinde üstten alta sırayla gösterilecek kısa cümle listesi."""
    close = float(df["close"].iloc[-1])
    lines: list[str] = [f"Son Kapanış: {close:.2f}"]

    poc = next((lv.price for lv in ps.levels if lv.label == "POC"), None)
    vah = next((lv.price for lv in ps.levels if lv.label == "VAH"), None)
    val = next((lv.price for lv in ps.levels if lv.label == "VAL"), None)
    if poc is not None:
        pos = "üzerinde" if close > poc else "altında"
        lines.append(f"Fiyat POC'un ({poc:.2f}) {pos}.")
    if vah is not None and val is not None:
        if close > vah:
            lines.append(f"Değer alanının üzerinde (VAH: {vah:.2f}).")
        elif close < val:
            lines.append(f"Değer alanının altında (VAL: {val:.2f}).")
        else:
            lines.append(f"Değer alanı içinde ({val:.2f} - {vah:.2f}).")

    rsi_series = ps.series.get("rsi_14")
    if rsi_series is not None and rsi_series.dropna().size:
        rsi_val = float(rsi_series.dropna().iloc[-1])
        if rsi_val >= 70:
            lines.append(f"RSI {rsi_val:.1f} — aşırı alım bölgesinde.")
        elif rsi_val <= 30:
            lines.append(f"RSI {rsi_val:.1f} — aşırı satım bölgesinde.")
        else:
            lines.append(f"RSI {rsi_val:.1f} — nötr bölgede.")

    last_label = sf.last_state.get("last_label")
    if last_label:
        lines.append(_SWING_LABEL_TR.get(str(last_label), f"Son yapı: {last_label}"))

    open_targets = [
        lv for lv in sf.levels if lv.label.startswith("D (hedef)") and lv.end is None
    ]
    if open_targets:
        nearest = min(open_targets, key=lambda lv: abs(lv.price - close))
        yon = "yukarı" if nearest.price > close else "aşağı"
        pct = abs(nearest.price - close) / close * 100.0 if close else 0.0
        lines.append(
            f"En yakın AB=CD hedefi: {nearest.price:.2f} ({yon} yönde, %{pct:.1f} mesafe)."
        )

    zone_pos = ps.last_state.get("price_vs_zone")
    if zone_pos in _ZONE_POSITION_TR:
        lines.append(_ZONE_POSITION_TR[zone_pos])

    active_lines = ps.last_state.get("active_trendlines")
    if active_lines:
        lines.append(f"Aktif trend çizgisi sayısı: {active_lines}.")

    macd_crosses = [m for m in ps.markers if m.kind == "macd_cross"]
    if macd_crosses:
        last_cross = macd_crosses[-1]
        yon = "yukarı" if "↑" in last_cross.text else "aşağı"
        lines.append(
            f"Son MACD kesişimi {yon} yönlü ({pd.Timestamp(last_cross.t).strftime('%d.%m.%Y')})."
        )

    return lines
