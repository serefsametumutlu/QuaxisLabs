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
from tlab.viz.labels_tr import tr_direction, tr_indicator, tr_state

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


_PAYLOAD_SKIP_KEYS = {"event", "pattern_id", "triple_id"}


def _payload_facts(payload: dict) -> list[str]:
    """Bir `Signal.payload`'ındaki (ekstra kimlik alanları hariç) sayısal/
    metinsel alanları okunur cümlelere çevirir — LLM'e OLGU olarak verilecek
    ham malzemeyi zenginleştirir (2026-09-03, "raporlar daha detaylı olsun"
    isteğine yanıt). Yeni bir hesap YOK, `payload` zaten hesaplanmış."""
    parts: list[str] = []
    for key, value in payload.items():
        if key in _PAYLOAD_SKIP_KEYS or value is None:
            continue
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):  # NaN/inf
                continue
            parts.append(f"{key}={value:.3g}")
        elif isinstance(value, (int, str, bool)):
            parts.append(f"{key}={value}")
    return parts


def build_generic_summary_lines(result: IndicatorResult, df: pd.DataFrame) -> list[str]:
    """`build_summary_lines`'ın `structure.report`e ÖZEL olmayan, geri kalan
    ~25 gösterge türü için TEK ortak yedek yolu (2026-09-02) — kullanıcı AI
    rapor butonunun HER gösterge için görünmesini istedi, ama her tür için
    ayrı bir olgu-çıkarma fonksiyonu yazmak (`structure.report`'unki gibi)
    ayrı/büyük bir iştir (bkz. proje planı, bilinçli kapsam dışı bırakıldı).
    Bunun yerine HER `IndicatorResult`'ın ZATEN taşıdığı ortak alanlardan
    (symbol, indicator adı, son birkaç `Signal`, `last_state`, payload
    detayları) dürüst/genel bir olgu listesi üretir — `structure.report`
    kadar el ile tasarlanmış DEĞİL ama YENİ bir hesap YAPMAZ, yalnızca var
    olan verinin biçimlendirmesidir (aynı ilke).

    2026-09-03: kullanıcı raporların "şimdiye kadar olduğundan daha detaylı"
    olmasını istedi — LLM'e daha ÖNCE yalnızca 1 sinyal + `event` alanı
    veriliyordu, bu az malzemeyle uzun/özgün bir metin üretmesi mümkün
    değildi (kısa kalıyor ya da tekrara düşüyordu). Artık son 3 sinyal (payload
    detaylarıyla) + tüm `last_state` alanları veriliyor — hâlâ YENİ bir hesap
    YOK, yalnızca LLM'e daha ZENGİN bir olgu tabanı."""
    close = float(df["close"].iloc[-1])
    tf = getattr(result.timeframe, "value", result.timeframe)
    lines: list[str] = [
        f"Sembol: {result.symbol} · Gösterge: {tr_indicator(result.indicator)} "
        f"· Zaman Dilimi: {tf}",
        f"Son Kapanış: {close:.2f}",
    ]
    if result.signals:
        recent = sorted(result.signals, key=lambda s: s.detected_at, reverse=True)[:3]
        state_counts: dict[str, int] = {}
        for s in result.signals:
            state_counts[s.state] = state_counts.get(s.state, 0) + 1
        counts_str = ", ".join(
            f"{tr_state(k)}: {v}" for k, v in sorted(state_counts.items())
        )
        lines.append(f"Bu tarama penceresindeki tüm sinyal durumları — {counts_str}.")
        for i, sig in enumerate(recent):
            prefix = "En güncel sinyal" if i == 0 else f"Önceki sinyal ({i + 1}.)"
            lines.append(
                f"{prefix} — Yön: {tr_direction(sig.direction)}, "
                f"Durum: {tr_state(sig.state)}, Skor: {sig.score:.2f}, "
                f"Bar Zamanı: {pd.Timestamp(sig.bar_time).strftime('%d.%m.%Y')}."
            )
            extra = _payload_facts(sig.payload)
            if extra:
                lines.append(f"  Detaylar: {', '.join(extra)}.")
    else:
        lines.append("Bu tarama penceresinde aktif bir sinyal bulunmuyor.")
    if result.last_state:
        state_parts = _payload_facts(result.last_state)
        if state_parts:
            lines.append(f"Güncel durum bilgileri: {', '.join(state_parts)}.")
        else:
            lines.append(f"Takip edilen aday/bölge sayısı: {len(result.last_state)}.")
    return lines


def build_pair_summary_lines(result: IndicatorResult) -> list[str]:
    """`pair.relative_momentum`/`pair.vol_harvest` için özel olgu listesi
    (2026-09-03) — bu ikisi `compute_live()`'da `df=None` döndüğü için
    (grafik render'ı pair modunda tekil bir OHLCV istemiyor, bkz. `live.py`)
    `build_generic_summary_lines`'ın `df["close"]` bağımlılığına UYMUYORDU;
    web arayüzü bu yüzden pair göstergelerinde "AI raporu desteklenmiyor"
    diyordu (gerçek kullanıcı bulgusu). Burada `df` yerine DOĞRUDAN
    `result.last_state`/`result.series['z']` kullanılıyor — ikisi de zaten
    `RelativeMomentumPair`/`VolHarvestPair`'in hesapladığı hazır veri, yeni
    bir hesap YOK."""
    tf = getattr(result.timeframe, "value", result.timeframe)
    st = result.last_state or {}
    lines: list[str] = [
        f"Sembol Çifti: {result.symbol} · Gösterge: {tr_indicator(result.indicator)} "
        f"· Zaman Dilimi: {tf}",
    ]

    holding = st.get("holding")
    if holding:
        lines.append(f"Şu an portföyün tutulan tarafı: {holding}.")
    zone_state = st.get("zone_state")
    if zone_state:
        lines.append(f"Z-skor bölgesi: {zone_state}.")
    if "z_today" in st:
        z_prev = st.get("z_yesterday")
        trend = ""
        if isinstance(z_prev, (int, float)):
            trend = " (bir önceki bara göre yükseliyor)" if st["z_today"] > z_prev else (
                " (bir önceki bara göre düşüyor)" if st["z_today"] < z_prev else ""
            )
        lines.append(f"Güncel z-skor: {st['z_today']:.2f}{trend}.")
    if "corr_today" in st:
        lines.append(f"Güncel korelasyon: {st['corr_today']:.2f}.")
    if "adf_pvalue" in st:
        lines.append(f"Kointegrasyon (ADF) p-değeri: {st['adf_pvalue']:.3f}.")
    halflife = st.get("halflife")
    if isinstance(halflife, (int, float)) and halflife != float("inf"):
        lines.append(f"Spread'in ortalamaya dönüş yarı-ömrü: {halflife:.1f} bar.")
    if "paused" in st:
        lines.append(
            "Strateji şu an DURAKLATILMIŞ (kointegrasyon/istatistiksel şartlar bozulmuş)."
            if st["paused"] else "Strateji şu an aktif olarak pozisyon taşıyor."
        )
    if "return_pct" in st:
        lines.append(f"Backtest getirisi: %{st['return_pct']:.1f}.")
    if "harvest_pct" in st:
        lines.append(f"Oynaklık hasadı katkısı: %{st['harvest_pct']:.1f}.")
    if "max_drawdown_pct" in st:
        lines.append(f"Maksimum düşüş (drawdown): %{st['max_drawdown_pct']:.1f}.")
    if "win_rate_pct" in st:
        lines.append(f"Kazanma oranı: %{st['win_rate_pct']:.1f}.")
    if "n_trades" in st:
        lines.append(f"Toplam işlem sayısı: {st['n_trades']}.")
    if "avg_holding_bars" in st:
        lines.append(f"Ortalama pozisyon tutma süresi: {st['avg_holding_bars']:.1f} bar.")

    if result.signals:
        last = max(result.signals, key=lambda s: s.detected_at)
        lines.append(
            f"En güncel rejim/sinyal olayı — Yön: {tr_direction(last.direction)}, "
            f"Durum: {tr_state(last.state)}, Bar Zamanı: "
            f"{pd.Timestamp(last.bar_time).strftime('%d.%m.%Y')}."
        )
        extra = _payload_facts(last.payload)
        if extra:
            lines.append(f"Detaylar: {', '.join(extra)}.")

    return lines
