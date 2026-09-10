"""`trend.*` göstergelerinin `IndicatorResult`ini `tlab/chart` sözleşmelerine
çevirir.

`patterns/boundary_adapter.py` ve `harmonics/adapter.py` ile AYNI ilke:
tarayıcının ZATEN hesapladığı çizgi/seri/durumu okuyup tipli bir sonuca
paketler. Hiçbir eşik/geometri burada yeniden HESAPLANMAZ.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.composers.series_overlay import OverlaySeries, SeriesOverlay
from tlab.chart.tokens import Role
from tlab.core.types import IndicatorResult
from tlab.indicators.trend.channel import Channel

# EMA yelpazesinde hangi çizgi hangi rolü alır — kısa vadeli boğa yeşili,
# uzun vadeli nötr. `series_overlay.ma_system()`in AYNI sırası.
_MA_ROLES: tuple[Role, ...] = ("bullish", "accent", "warn", "neutral")

_STACK_TR: dict[str, str] = {
    "bullish": "BOĞA DİZİLİMİ", "bearish": "AYI DİZİLİMİ", "mixed": "KARIŞIK",
}


def _last_signal(result: IndicatorResult):
    return max(result.signals, key=lambda s: pd.Timestamp(s.bar_time)) if result.signals else None


def _bars_ago(df: pd.DataFrame, sig) -> int | None:
    return None if sig is None else int((df.index > pd.Timestamp(sig.bar_time)).sum())


def ma_systems_to_overlay(result: IndicatorResult, df: pd.DataFrame) -> SeriesOverlay | None:
    """`trend.ma_systems` -> EMA yelpazesi + bant genişliği alt paneli.

    EMA'lar `result.lines`ta ÇOK NOKTALI `Line` olarak geliyor (`label`
    "EMA8" vb.); burada tam diziye çevrilir -- iki uca indirgenmez
    (`GORSEL_HATA_TESHISI.md` K1: eski renderer bunu yapıp EMA'ları düz
    çizgiye çeviriyordu).
    """
    ma_lines = [ln for ln in result.lines if ln.label.startswith("EMA")]
    if not ma_lines:
        return None

    series: list[OverlaySeries] = []
    for i, ln in enumerate(ma_lines):
        idx = [pd.Timestamp(t) for t, _ in ln.points]
        vals = [float(v) for _, v in ln.points]
        series.append(
            OverlaySeries(ln.label, pd.Series(vals, index=idx), _MA_ROLES[i % len(_MA_ROLES)])
        )

    sub: list[OverlaySeries] = []
    if "band_width" in result.series:
        sub.append(OverlaySeries("Bant Genişliği", result.series["band_width"], "accent"))
    if "squeeze_threshold" in result.series:
        sub.append(
            OverlaySeries("Sıkışma Eşiği", result.series["squeeze_threshold"], "neutral", "dot")
        )

    st = result.last_state or {}
    state = _STACK_TR.get(str(st.get("stack_state")), str(st.get("stack_state", "")).upper())
    if st.get("is_squeeze"):
        state += " • SIKIŞMA"

    sig = _last_signal(result)
    return SeriesOverlay(
        title="HAREKETLİ ORTALAMA SİSTEMİ", state=state,
        series=tuple(series), sub_series=tuple(sub), sub_title="Bant Genişliği",
        signal_t=pd.Timestamp(sig.bar_time) if sig else None,
        signal_price=float(df["close"].loc[pd.Timestamp(sig.bar_time)]) if sig else None,
        signal_text="AL" if sig and sig.direction == "long" else ("SAT" if sig else ""),
        signal_role="bullish" if sig and sig.direction == "long" else "bearish",
        bars_ago=_bars_ago(df, sig),
    )


def ewmac_to_overlay(result: IndicatorResult, df: pd.DataFrame) -> SeriesOverlay | None:
    """`trend.ewmac` -> tahmin serileri (YALNIZCA alt panel).

    Tahminler -20..+20 ölçeğinde; fiyat paneline konulursa mumları ezer.
    Bu yüzden `series` BOŞ bırakılır (fiyat paneli yalnızca mum çizer) ve
    hepsi `sub_series`e gider -- `SeriesOverlay` sözleşmesi bu durumu
    açıkça destekliyor.
    """
    pairs = [k for k in result.series if k.startswith("ewmac_") and k not in
             ("ewmac_combined", "ewmac_zero")]
    if not pairs:
        return None

    sub: list[OverlaySeries] = []
    if "ewmac_combined" in result.series:
        sub.append(OverlaySeries("Birleşik Tahmin", result.series["ewmac_combined"], "accent"))
    if "ewmac_zero" in result.series:
        sub.append(OverlaySeries("Sıfır", result.series["ewmac_zero"], "neutral", "dot"))
    for k in sorted(pairs):
        label = "EWMAC " + k.removeprefix("ewmac_").replace("_", "/")
        sub.append(OverlaySeries(label, result.series[k], "neutral"))

    st = result.last_state or {}
    fc = st.get("forecast_combined")
    state = "YÖN YOK"
    if isinstance(fc, int | float):
        state = f"TAHMİN {float(fc):+.1f}"

    sig = _last_signal(result)
    return SeriesOverlay(
        title="EWMAC TREND TAHMİNİ", state=state,
        series=(), sub_series=tuple(sub), sub_title="Tahmin (-20 / +20)",
        signal_t=pd.Timestamp(sig.bar_time) if sig else None,
        signal_price=float(df["close"].loc[pd.Timestamp(sig.bar_time)]) if sig else None,
        signal_text="AL" if sig and sig.direction == "long" else ("SAT" if sig else ""),
        signal_role="bullish" if sig and sig.direction == "long" else "bearish",
        bars_ago=_bars_ago(df, sig),
    )


def weekly_channel_to_channel(result: IndicatorResult, df: pd.DataFrame) -> Channel | None:
    """`trend.weekly_channel` -> `Channel`.

    YALNIZCA `channel_current_*` çizilir. `result.lines` 160 çizgi taşıyor
    ve bunların ~158'i `channel_frozen_*` (her hafta yeniden dondurulmuş
    TARİHSEL kanallar). `tlab/viz/svg/scenes/weekly_channel.py` de bunları
    BİLİNÇLİ çizmiyordu -- "okunamaz kalabalık" (PROGRESS_LOG, Faz 4a).
    """
    lines = {ln.label: ln for ln in result.lines}
    up, lo = lines.get("channel_current_upper"), lines.get("channel_current_lower")
    if up is None or lo is None:
        return None

    st = result.last_state or {}
    (ut0, uy0), (ut1, uy1) = up.points[0], up.points[-1]
    (lt0, ly0), (lt1, ly1) = lo.points[0], lo.points[-1]

    # DİKKAT: `last_state["slope"]` kanalın eğimi DEĞİL -- orta çizginin
    # SON haftalık farkı (`weekly_channel.py:108`, `mid_diff_last`), yani
    # anlık bir değişim. Kanal yükselirken bile negatif olabilir; ilk
    # denemede `rising_channel` fikstürü bu yüzden "alçalan" sınıflandı
    # (çizgiler 27.0->28.2 YÜKSELİRKEN). Eğim ÇİZDİĞİMİZ çizginin kendi
    # uçlarından türetilir -- yeni bir fit değil, aynı doğrunun eğimi.
    i0 = int(df.index.searchsorted(pd.Timestamp(ut0)))
    i1 = int(df.index.searchsorted(pd.Timestamp(ut1)))
    slope = (float(uy1) - float(uy0)) / max(i1 - i0, 1)

    ref = float(df["close"].iloc[-1]) or 1.0
    flat = abs(slope) < ref * 0.0005
    direction = "yatay" if flat else ("yukselen" if slope > 0 else "alcalan")
    width_pct = abs(uy1 - ly1) / ref * 100 if ref else 0.0

    pos = st.get("position_pct")
    if st.get("at_bottom"):
        state = "ALT BANT TEMASI"
    elif isinstance(pos, int | float) and float(pos) >= 95:
        state = "ÜST BANT TEMASI"
    else:
        state = "BANT İÇİNDE"

    sig = _last_signal(result)
    # TEMAS KONUMLARI gösterge tarafından DIŞA AÇILMIYOR (`last_state`
    # yalnızca SAYIYI taşıyor: {"top": 22, "bottom": 26}). Adaptör bunları
    # yeniden HESAPLAMAZ -- boş bırakılır; sayı zaten üst bilgide görünür.
    return Channel(
        slope_per_bar=slope,
        upper_at=((pd.Timestamp(ut0), float(uy0)), (pd.Timestamp(ut1), float(uy1))),
        lower_at=((pd.Timestamp(lt0), float(ly0)), (pd.Timestamp(lt1), float(ly1))),
        upper_touches=(), lower_touches=(),
        direction=direction, width_pct=width_pct, state=state,
        current_touch=None, bars_ago=_bars_ago(df, sig),
    )
