"""ChannelIndicator — regresyon veya pivot kanalı + dip/tepe dokunuş ve
kırılım taraması. Haftalık (W1) taramalar için tasarlandı ama 1D'yi de
destekler (`Timeframe.W1`, `tlab/core/types.py`da Faz 2-EK'te eklendi).

**method='regression'** (varsayılan): `channels.regression_channel` — HER
barın kanalı yalnızca kendi trailing [t-n+1,t] penceresinden hesaplanır
(non-repaint by construction, bkz. o modülün docstring'i); dokunuş/kırılım
sayaçları (`bottom_touches`/`top_touches`) da SIRAYLA (valid_from'dan
itibaren) biriktirilir, yalnızca geçmişe bakar. Sinyaller bu anlamda
non-repaint'tir. **AMA** spec'in açıkça istediği "güncel kanal ayrı Line
olarak" öğesi (`style="channel_current"`) KASITLI OLARAK HER barda
DEĞİŞEN, "şu an" durumunu gösteren canlı bir overlay'dir — points'i her
`compute()` çağrısında en son bara göre kayar. Bu GERÇEK bir repaint hatası
DEĞİLDİR (geçmişteki hiçbir gerçek yeniden yazılmıyor, yalnızca "şu anki
görünüm" tanımı gereği güncelleniyor) ama generic `repaint_test`'in Line
karşılaştırması (points+label eşleşmesi) bunu "aynı label, farklı points"
olarak MISMATCH sanır. Bu yüzden `structure.price_structure`/`trend.
breakouts` ile AYNI istisna yolu (`register_verified_elsewhere`) kullanılır;
`channel_bottom_touch`/`channel_top_touch`/`channel_break_*` sinyallerinin
VE `channel_frozen_*` çizgilerinin (geçmiş bir sinyal barında dondurulmuş,
BİR DAHA DEĞİŞMEYEN) gerçek non-repaint'liği `tests/test_trend/
test_weekly_channel.py`'de HEDEFLİ testlerle doğrulanır.

**method='pivot'**: `channels.pivot_channel(..., max_channels=1)` — "en iyi"
kanalın SEÇİMİ df büyüdükçe değişebilen AYRI bir "aday havuzu" deseni
(trendlines.py ile aynı) — bu yöntem için de aynı istisna yolu geçerli.

Görsel: regresyon modunda her sinyal barında `frozen_channel_at` ile
DONDURULMUŞ (extend_right=False, style="channel_frozen", soluk) bir
kanal + ayrıca EN GÜNCEL kanalın kendisi (style="channel_current",
belirgin, son `n` bardan). Pivot modunda tek, extend-only bir kanal
(style="channel"). Alt panel: `channel_position` osilatörü (`series_layout`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Line,
    Signal,
    Timeframe,
)
from tlab.features.channels import (
    RegressionChannel,
    channel_position,
    frozen_channel_at,
    pivot_channel,
    pivot_channel_series,
    regression_channel,
)
from tlab.features.oscillators import rsi
from tlab.features.swings import ZigzagMethod, significant_pivots

ChannelMethod = Literal["regression", "pivot"]


@dataclass(frozen=True)
class ChannelParams(BaseParams):
    method: ChannelMethod = "regression"
    n: int = 52
    k: float = 2.0
    touch_tol: float = 0.05
    min_prev_touches: int = 2
    rsi_max: float = 40.0
    rsi_window: int = 14
    confirm_bars: int = 1
    left: int = 3
    right: int = 3
    # Faz 0.5, A1 — ortak pivot girişi (bkz. tlab/features/swings.py::
    # significant_pivots). Varsayılan zigzag_method="atr" (sistem geneli
    # karar, scripts/sistemik_denetim.py ölçümüyle doğrulandı).
    zigzag_method: ZigzagMethod = "atr"
    atr_mult: float = 3.0
    atr_period: int = 14
    min_swing_atr: float | None = None


class ChannelIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="trend.weekly_channel",
        version="0.1.0",
        category="trend",
        description="Regresyon/pivot kanalı — dip/tepe dokunuş ve kırılım taraması.",
        supported_timeframes=(Timeframe.W1, Timeframe.D1),
    )

    def __init__(self, params: ChannelParams | None = None) -> None:
        self.params: ChannelParams = params or ChannelParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        lines: list[Line] = []

        if p.method == "regression":
            band = regression_channel(df, p.n, p.k)
            has_valid = band.mid.notna().any()
            valid_from = int(band.mid.notna().to_numpy().argmax()) if has_valid else len(df)
            mid_diff_last = band.mid.diff().iloc[-1] if len(df) > 1 else float("nan")
            slope = float(mid_diff_last) if not pd.isna(mid_diff_last) else 0.0
        else:
            pivots = significant_pivots(
                df, method=p.zigzag_method, left=p.left, right=p.right,
                atr_mult=p.atr_mult, atr_period=p.atr_period, min_swing_atr=p.min_swing_atr,
            )
            channels = pivot_channel(df, pivots, max_channels=1)
            if not channels:
                band = RegressionChannel(
                    mid=pd.Series(float("nan"), index=df.index),
                    upper=pd.Series(float("nan"), index=df.index),
                    lower=pd.Series(float("nan"), index=df.index),
                )
                valid_from = len(df)
                slope = 0.0
            else:
                ch = channels[0]
                band = pivot_channel_series(df, ch)
                valid_from = ch.created_idx
                slope = float(ch.slope)
                lines.append(
                    Line(
                        points=((ch.p1.bar_time, ch.lower_at(ch.p1.bar_idx)),
                                (ch.p2.bar_time, ch.lower_at(ch.p2.bar_idx))),
                        label="channel_lower", style="channel", extend_right=True,
                    )
                )
                lines.append(
                    Line(
                        points=((ch.p1.bar_time, ch.upper_at(ch.p1.bar_idx)),
                                (ch.p2.bar_time, ch.upper_at(ch.p2.bar_idx))),
                        label="channel_upper", style="channel", extend_right=True,
                    )
                )

        signals, bottom_touches, top_touches = _scan(df, band, p, valid_from)

        if p.method == "regression" and valid_from < len(df):
            last = len(df) - 1
            current = frozen_channel_at(df, last, p.n, p.k)
            lines.append(
                Line(points=((current.t0, current.lower[0]), (current.t1, current.lower[1])),
                     label="channel_current_lower", style="channel_current", extend_right=False)
            )
            lines.append(
                Line(points=((current.t0, current.upper[0]), (current.t1, current.upper[1])),
                     label="channel_current_upper", style="channel_current", extend_right=False)
            )
            for sig in signals:
                t = df.index.get_loc(sig.bar_time)
                if t < p.n - 1 or t == last:
                    continue
                frozen = frozen_channel_at(df, t, p.n, p.k)
                lines.append(
                    Line(
                        points=((frozen.t0, frozen.lower[0]), (frozen.t1, frozen.lower[1])),
                        label=f"channel_frozen_lower_{t}", style="channel_frozen",
                        extend_right=False,
                    )
                )
                lines.append(
                    Line(
                        points=((frozen.t0, frozen.upper[0]), (frozen.t1, frozen.upper[1])),
                        label=f"channel_frozen_upper_{t}", style="channel_frozen",
                        extend_right=False,
                    )
                )

        position = channel_position(df, band)
        last_pos = position.iloc[-1]
        last_pos_pct = float(last_pos * 100.0) if not pd.isna(last_pos) else None

        last_state = {
            "position_pct": last_pos_pct,
            "slope": slope,
            "touches": {"bottom": bottom_touches, "top": top_touches},
            "at_bottom": bool(last_pos_pct is not None and last_pos_pct < 15.0),
        }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, lines=lines,
            series={"channel_position": position},
            series_layout={"channel_position": ["channel_position"]},
            last_state=last_state,
        )


def _scan(
    df: pd.DataFrame, band: RegressionChannel, p: ChannelParams, valid_from: int
) -> tuple[list[Signal], int, int]:
    n = len(df)
    close = df["close"].to_numpy()
    low = df["low"].to_numpy()
    high = df["high"].to_numpy()
    rsi_series = rsi(df["close"], p.rsi_window)

    signals: list[Signal] = []
    bottom_touches = 0
    top_touches = 0
    streak_up = 0
    streak_down = 0

    for t in range(valid_from, n):
        up_t, lo_t = band.upper.iloc[t], band.lower.iloc[t]
        if pd.isna(up_t) or pd.isna(lo_t):
            continue
        width = up_t - lo_t
        tol = p.touch_tol * width

        beyond_up = close[t] > up_t
        beyond_down = close[t] < lo_t

        if beyond_up:
            streak_up += 1
            streak_down = 0
        elif beyond_down:
            streak_down += 1
            streak_up = 0
        else:
            streak_up = 0
            streak_down = 0

        if streak_up >= p.confirm_bars:
            signals.append(
                Signal(df.index[t], df.index[t], "long", "confirmed", 0.7,
                       {"event": "channel_break_up"})
            )
        if streak_down >= p.confirm_bars:
            signals.append(
                Signal(df.index[t], df.index[t], "short", "confirmed", 0.7,
                       {"event": "channel_break_down"})
            )

        near_bottom = not beyond_down and abs(low[t] - lo_t) <= tol
        near_top = not beyond_up and abs(high[t] - up_t) <= tol

        if near_bottom:
            if bottom_touches >= p.min_prev_touches:
                rsi_t = rsi_series.iloc[t]
                if not pd.isna(rsi_t) and rsi_t <= p.rsi_max:
                    direction: Direction = "long"
                    signals.append(
                        Signal(df.index[t], df.index[t], direction, "active", 0.8,
                               {"event": "channel_bottom_touch", "rsi": float(rsi_t),
                                "touch_no": bottom_touches + 1})
                    )
            bottom_touches += 1

        if near_top:
            if top_touches >= p.min_prev_touches:
                signals.append(
                    Signal(df.index[t], df.index[t], "short", "active", 0.7,
                           {"event": "channel_top_touch", "touch_no": top_touches + 1})
                )
            top_touches += 1

    return signals, bottom_touches, top_touches
