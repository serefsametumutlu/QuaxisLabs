"""`momentum.*` (evren göstergeleri) -> `SeriesOverlay`.

İki gösterge de `UniverseIndicator`: `rank_pct` TANIM GEREĞİ tüm evreni
birlikte görmeyi gerektiriyor. Grafik tarafında bunun karşılığı tek bir
"formasyon" değil, sembolün EVRENE GÖRE konumunu anlatan seriler.

  * `alpha_rank`  -> fiyat vs endeks (normalize) + alfa t-istatistiği
  * `momentum_rank` -> göreli güç (RS) + çok-ufuklu momentum

`SeriesOverlay` bunu zaten karşılıyor (`trend.ewmac` ile AYNI desen).
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.composers.series_overlay import OverlaySeries, SeriesOverlay
from tlab.core.types import IndicatorResult


def _bars_ago(result: IndicatorResult, df: pd.DataFrame) -> int | None:
    if not result.signals:
        return None
    last = max(result.signals, key=lambda s: pd.Timestamp(s.bar_time))
    return int((df.index > pd.Timestamp(last.bar_time)).sum())


def _rank_state(st: dict) -> str:
    rank = st.get("rank_pct")
    if not isinstance(rank, int | float):
        return "SIRALAMA YOK"
    tag = "EVRENİN ÜSTÜNDE" if st.get("in_top_pct") in (True, "True") else "SIRALAMA"
    return f"{tag} — %{float(rank):.0f}"


def alpha_rank_to_overlay(result: IndicatorResult, df: pd.DataFrame) -> SeriesOverlay | None:
    ser = result.series
    if "close_norm" not in ser or "index_norm" not in ser:
        return None
    # Normalize seriler BAZ-100; mumlar HAM fiyat. Aynı panele konunca
    # ölçekler çakışıyor (fikstürde mumlar 15-27, normalize 100-190 --
    # mumlar ekranın dibine yapışıyordu, GÖRÜLEREK bulundu). Bu yüzden
    # karşılaştırma ALT panele alınır; fiyat paneli mumlarla bağlamı
    # korur. Alfa t-istatistiği seri olarak kaybolmasın diye SON değeri
    # üst bilgiye taşınır -- `SeriesOverlay` tek alt panel destekliyor.
    sub = [
        OverlaySeries("Fiyat (norm.)", ser["close_norm"], "bullish"),
        OverlaySeries("Endeks (norm.)", ser["index_norm"], "neutral", "dash"),
    ]
    st = result.last_state or {}
    state = _rank_state(st)
    t_stat = ser.get("t_stat")
    if t_stat is not None and len(t_stat.dropna()):
        state += f" • alfa t={float(t_stat.dropna().iloc[-1]):+.2f}"

    return SeriesOverlay(
        title="ALFA SIRALAMASI", state=state,
        series=(), sub_series=tuple(sub), sub_title="Fiyat vs Endeks (baz 100)",
        bars_ago=_bars_ago(result, df),
    )


def momentum_rank_to_overlay(
    result: IndicatorResult, df: pd.DataFrame
) -> SeriesOverlay | None:
    ser = result.series
    if "rs" not in ser:
        return None
    # RS (göreli güç) fiyat ölçeğinde DEĞİL -> alt panele. Fiyat paneli
    # yalnızca mumları çizer (`SeriesOverlay` bunu destekliyor, bkz.
    # `trend.ewmac`).
    sub = [OverlaySeries("Göreli Güç (RS)", ser["rs"], "accent")]
    for key, label, role, dash in (
        ("rs_tstat", "RS t-ist.", "bullish", None),
        ("rs_tstat_upper", "üst", "neutral", "dot"),
        ("rs_tstat_lower", "alt", "neutral", "dot"),
    ):
        if key in ser:
            sub.append(OverlaySeries(label, ser[key], role, dash))

    st = result.last_state or {}
    return SeriesOverlay(
        title="MOMENTUM SIRALAMASI", state=_rank_state(st),
        series=(), sub_series=tuple(sub), sub_title="Göreli güç / t-istatistiği",
        bars_ago=_bars_ago(result, df),
    )
