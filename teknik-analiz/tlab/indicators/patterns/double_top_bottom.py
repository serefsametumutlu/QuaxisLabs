"""Çift Tepe (double top) / Çift Dip (double bottom) tarayıcı — Faz 8B (K1
TWYS eki, bkz. bilgi-bankasi/teknik/10_pesavento_twys.md FORMASYON atıfları).

`swings.alternate_pivots` zigzag'inden (yalnızca kesinleşmiş pivotlar —
`structure.golden_zone`/`patterns.head_shoulders` ile AYNI mimari) aynı
türden İKİ ARDIŞIK pivot (p1, p2 — aralarında TAM OLARAK bir zıt-türde ara
pivot olmalı, bu "boyun" — çukur/tepe) arar. `p2`, kendi `finalized_idx`'inde
(daha ekstrem bir pivotla İPTAL EDİLEMEYECEĞİ kesinleştiği bar) PENDING
doğar — `p2.confirmed_idx`'te DEĞİL (aksi halde p2 sonradan daha ekstrem bir
pivotla değişebileceği için band/hedef repaint ederdi).

Kırılım = boyun (ara pivotun düz fiyat seviyesi) kapanışla kırılması; hedef
= boyun +/- derinlik (iki tepe/dibin ortalaması ile boyun arası mesafe).
Geçersizlik = kapanışın ikinci tepenin/dibin ÖTESİNE geçmesi (klasik kural:
ikinci uç aşılırsa çift tepe/dip iptal, muhtemelen trend devam ediyor).

Aday havuzu zamanlaması YOKTUR (her (p1,p2) çifti zigzag'den DOĞRUDAN,
seçim/top-N kesmesi olmadan üretilir) — generic `Registry.register()`'a
TEMİZ kaydolur."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import pandas as pd

from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.pattern_state import (
    PatternTrackingConfig,
    level_end_from_signals,
    marker_text,
    track_breakout_pattern,
)
from tlab.core.types import (
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Level,
    Marker,
    Polygon,
    Signal,
    Timeframe,
)
from tlab.features.pattern_context import breakout_volume_ok, pattern_depth_ok, prior_trend
from tlab.features.swings import Pivot, ZigzagMethod, significant_pivots
from tlab.features.volatility import atr

_LABEL_TR = {"double_top": "ÇİFT TEPE", "double_bottom": "ÇİFT DİP"}


def _bump(context: dict | None, key: str) -> None:
    """Faz 1, 1D — ölçüm betikleri (`scripts/formasyon_denetim.py`) için
    OPSİYONEL elenme-sebebi sayacı. `context={"elim": {}}` verilmediği
    sürece (varsayılan davranış) HİÇBİR ŞEY yapmaz -- var olan `context`
    parametresini (şimdiye kadar yalnızca pair indikatörlerinin kullandığı)
    genişletir, yeni bir Params alanı GEREKTİRMEZ."""
    if context is None:
        return
    counter = context.get("elim")
    if counter is None:
        return
    counter[key] = counter.get(key, 0) + 1


@dataclass(frozen=True)
class DoubleTopBottomParams(BaseParams):
    left: int = 3
    right: int = 3
    # Faz 1, 1B — Lo-Mamaysky-Wang (Journal of Finance, 2000) DTOP/DBOT
    # tanımı: iki uç ORTALAMALARININ %1.5'i içinde olmalı (eski 0.02 gevşekti).
    eq_tol: float = 0.015
    # Faz 1, 1B — LMW: iki uç en az BİR AY (22 işlem günü) arayla olmalı
    # (eski değer 5'ti — 4H'te bu 20 saatten az demekti, kullanıcının
    # gördüğü sahte çift diplerin doğrudan kök nedeni). 1D taban, diğer
    # zaman dilimlerine `for_timeframe` ile ölçeklenir (bkz. _BAR_FIELDS).
    min_bars_between: int = 22
    # Faz 1, 1B — YENİ. 0 = sınırsız (varsayılan, davranış eskisi gibi
    # kapalı). Çift tepe/dip birkaç yıl arayla iki tepeyle "oluşmaz" —
    # D1 için makul üst sınır ~250 bar (config/scans.yaml'da bir preset
    # önerilebilir). BİLİNÇLİ OLARAK _BAR_FIELDS'e EKLENMEDİ: 0 "sınırsız"
    # sentinel'i, min alanların aksine, ölçeklenirse (`max(1, round(0*6))`)
    # YANLIŞLIKLA "üst sınır 1 bar" gibi katastrofik bir değere döner.
    max_bars_between: int = 0
    # Faz 1, 1B — YENİ (Bulkowski): iki dip arasında en az %10'luk bir
    # yükseliş (çift tepede: iki tepe arasında en az %10'luk düşüş) olmalı
    # — "dümdüz bir taban" tipi sahte formasyonları eler. Ölçü: boyun
    # pivotu ile iki ucun ortalaması arasındaki mesafenin ucun fiyatına oranı.
    min_rise_between_pct: float = 0.10
    # Faz 1, 1B — YENİ (Bulkowski): çift dip DÜŞEN, çift tepe YÜKSELEN bir
    # ön trendden sonra gelmeli (bkz. tlab/features/pattern_context.py::
    # prior_trend). lookback 1D taban, diğer zaman dilimlerine ölçeklenir.
    prior_trend_lookback: int = 20
    prior_trend_min_tstat: float = 1.5
    # Faz 1, 1B — YENİ (STRATEJI_DENETIM_TAM.md): formasyon derinliği
    # önemsizse (ZOREN örneğinde ~%3, 4H gürültüsünden ayırt edilemezdi)
    # elenir (bkz. pattern_context.py::pattern_depth_ok — HEM yüzde HEM
    # ATR eşiği birden gerekir).
    min_depth_pct: float = 0.03
    min_depth_atr: float = 2.0
    confirm_bars: int = 1
    vol_k: float = 1.2
    max_bars_to_confirm_mult: float = 3.0
    retest_tol_atr: float = 0.3
    atr_period: int = 14
    vol_ma_window: int = 20
    # Faz 0.5, A1 — ortak pivot girişi (bkz. tlab/features/swings.py::
    # significant_pivots). Varsayılan zigzag_method="atr" (sistem geneli
    # karar, scripts/sistemik_denetim.py ölçümüyle doğrulandı).
    zigzag_method: ZigzagMethod = "atr"
    atr_mult: float = 3.0
    min_swing_atr: float | None = None
    # Faz 0.5, A2 — takvimsel süre temsil eden bar-alanları; 1D taban kabul
    # edilip diğer zaman dilimlerine ölçeklenir (bkz. tlab/core/params.py::
    # BaseParams.for_timeframe). max_bars_between KASITLI OLARAK dışarıda
    # (yukarıdaki yorum).
    _BAR_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"min_bars_between", "prior_trend_lookback"}
    )
    # Faz 0.5, A4 — `volume_ok` ZATEN hesaplanıp payload'a yazılıyordu ama
    # hiçbir sinyali FİLTRELEMİYORDU (bkz. STRATEJI_DENETIM_TAM.md A4).
    # Varsayılan False = davranış DEĞİŞMEDİ; True iken hacim onayı
    # geçmeyen aday confirmed'a TERFİ ETMEZ (invalidated OLMAZ).
    require_volume_confirm: bool = False


def _matched_pairs(zigzag: list[Pivot], kind: str) -> list[tuple[Pivot, Pivot, Pivot]]:
    """Aynı türden ardışık (p1,p2) + aralarındaki TEK zıt-türde ara pivot
    (boyun). Aralarında sıfır ya da birden fazla ara pivot varsa (zigzag
    alternation garantisi altında bu normalde olmaz, ama defensif) atlanır."""
    opposite = "low" if kind == "high" else "high"
    same = [pv for pv in zigzag if pv.kind == kind]
    pairs: list[tuple[Pivot, Pivot, Pivot]] = []
    for p1, p2 in zip(same, same[1:], strict=False):
        between = [
            pv for pv in zigzag
            if pv.kind == opposite and p1.bar_idx < pv.bar_idx < p2.bar_idx
        ]
        if len(between) == 1:
            pairs.append((p1, between[0], p2))
    return pairs


class DoubleTopBottomIndicator(BaseIndicator):
    meta = IndicatorMeta(
        name="patterns.double_top_bottom",
        version="0.1.0",
        category="patterns",
        description="Çift tepe / çift dip formasyon tarayıcı.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: DoubleTopBottomParams | None = None) -> None:
        self.params: DoubleTopBottomParams = params or DoubleTopBottomParams()

    def compute(self, df: pd.DataFrame, context: dict | None = None) -> IndicatorResult:
        p = self.params
        n = len(df)
        zigzag = significant_pivots(
            df, method=p.zigzag_method, left=p.left, right=p.right,
            atr_mult=p.atr_mult, atr_period=p.atr_period, min_swing_atr=p.min_swing_atr,
        )
        atr_series = atr(df, p.atr_period)
        close = df["close"].to_numpy()
        volume = df["volume"].to_numpy()

        signals: list[Signal] = []
        levels: list[Level] = []
        markers: list[Marker] = []
        polygons: list[Polygon] = []
        last_state: dict[str, dict] = {}

        for kind, pattern_name in (("high", "double_top"), ("low", "double_bottom")):
            direction: Direction = "short" if kind == "high" else "long"
            for p1, neckline_pivot, p2 in _matched_pairs(zigzag, kind):
                bars_between = p2.bar_idx - p1.bar_idx
                if bars_between < p.min_bars_between:
                    _bump(context, "min_bars_between")
                    continue
                if p.max_bars_between > 0 and bars_between > p.max_bars_between:
                    _bump(context, "max_bars_between")
                    continue
                avg_price = (p1.price + p2.price) / 2.0
                if avg_price == 0:
                    continue
                if abs(p1.price - p2.price) / avg_price > p.eq_tol:
                    _bump(context, "eq_tol")
                    continue

                neckline_price = neckline_pivot.price
                depth = abs(avg_price - neckline_price)
                if depth == 0:
                    continue
                # Faz 1, 1B — Bulkowski: iki uç arasında en az min_rise_
                # between_pct kadar bir ters hareket olmalı ("dümdüz bir
                # taban" tipi sahte formasyonları eler).
                if depth / avg_price < p.min_rise_between_pct:
                    _bump(context, "min_rise_between_pct")
                    continue

                born_idx = p2.finalized_idx
                if born_idx is None or born_idx >= n:
                    continue

                # Faz 1, 1B — ön trend şartı (Bulkowski): çift dip DÜŞEN,
                # çift tepe YÜKSELEN bir trendden sonra gelmeli.
                trend_ok, _ = prior_trend(
                    df, p1.bar_idx, p.prior_trend_lookback, direction, p.prior_trend_min_tstat,
                )
                if not trend_ok:
                    _bump(context, "prior_trend")
                    continue

                # Faz 1, 1B — minimum derinlik (STRATEJI_DENETIM_TAM.md):
                # önemsiz derinlikteki formasyonlar 4H gürültüsünden ayırt
                # edilemez.
                if not pattern_depth_ok(
                    depth, avg_price, atr_series.iloc[born_idx], p.min_depth_pct, p.min_depth_atr,
                ):
                    _bump(context, "min_depth")
                    continue

                extreme = max(p1.price, p2.price) if kind == "high" else min(p1.price, p2.price)
                target = neckline_price - depth if direction == "short" else neckline_price + depth

                def _invalidation(
                    t: int, _hi: float, _lo: float,
                    _extreme: float = extreme, _dir: str = direction,
                ) -> bool:
                    return close[t] > _extreme if _dir == "short" else close[t] < _extreme

                def _break_line(_t: int, _lvl: float = neckline_price) -> float:
                    return _lvl

                pattern_id = f"{pattern_name}_{p1.bar_idx}_{neckline_pivot.bar_idx}_{p2.bar_idx}"
                max_bars_to_confirm = int(p.max_bars_to_confirm_mult * (p2.bar_idx - p1.bar_idx))
                # 2026-09-03: bkz. `PatternTrackingConfig.max_bars_to_target`
                # docstring'i (`wedge.py`'deki aynı düzeltmeyle aynı gerekçe).
                max_bars_to_target = max(1, round(1.5 * (p2.bar_idx - p1.bar_idx)))
                cfg = PatternTrackingConfig(
                    pattern_id=pattern_id, pattern_name=pattern_name, direction=direction,
                    break_line=_break_line, target=target,
                    confirm_bars=p.confirm_bars, max_bars_to_confirm=max_bars_to_confirm,
                    retest_tol_atr=p.retest_tol_atr, atr_series=atr_series, score=0.6,
                    invalidation_check=_invalidation,
                    extra_payload={"depth": depth, "neckline": neckline_price},
                    max_bars_to_target=max_bars_to_target,
                )
                pattern_signals = track_breakout_pattern(df, born_idx, cfg)

                confirm_sig = next(
                    (s for s in pattern_signals if s.payload["event"].endswith("_confirmed")), None
                )
                if confirm_sig is not None:
                    breakout_idx = df.index.get_loc(confirm_sig.bar_time)
                    volume_ok = breakout_volume_ok(volume, breakout_idx, p.vol_ma_window, p.vol_k)
                    confirm_sig.payload["volume_ok"] = volume_ok
                    if p.require_volume_confirm and not volume_ok:
                        # Faz 0.5, A4: aday GEÇERSİZLEŞMİYOR, yalnızca
                        # confirmed'a TERFİ ETMİYOR -- diğer yaşam döngüsü
                        # sinyalleri (pending vb.) olduğu gibi kalır.
                        pattern_signals = [s for s in pattern_signals if s is not confirm_sig]

                signals.extend(pattern_signals)

                levels.append(
                    Level(
                        price=neckline_price, label=f"{pattern_id}_neckline",
                        style="pattern_boundary",
                        start=p2.bar_time, end=level_end_from_signals(pattern_signals),
                    )
                )
                levels.append(
                    Level(
                        price=target, label=f"{pattern_id}_target", style="pattern_target",
                        start=p2.bar_time, end=level_end_from_signals(pattern_signals),
                    )
                )
                # Faz 1, 1B — hologram DÜZELTMESİ: eski hâli (p1-p2 arası
                # GERÇEK kapanış yolu) geometrik olarak doğruydu ama
                # görsel olarak AMORF bir leke üretiyordu (bkz. STRATEJI_
                # DENETIM_TAM.md — ALTNY örneğindeki "mavi bulut" tam bu).
                # `docs/design/grafik_stil_vitrini.html::sceneDoubleTopBottom`
                # 5 köşeli, boyun seviyesine OTURAN, kendi kendini kesmeyen
                # bir M/W silueti çiziyor — [boyun_sol, uç1, boyun, uç2,
                # boyun_sağ]. boyun_sol/boyun_sağ, uç1/uç2 ile AYNI zamanda
                # ama boyun FİYATINDA (dikey bir "direk" ile uca bağlanan
                # şematik köşeler) — kendi kendini kesmeyen kapalı bir
                # poligon garantiler.
                polygons.append(
                    Polygon(
                        points=(
                            (p1.bar_time, neckline_price),
                            (p1.bar_time, p1.price),
                            (neckline_pivot.bar_time, neckline_price),
                            (p2.bar_time, p2.price),
                            (p2.bar_time, neckline_price),
                        ),
                        label=f"{pattern_id}_hologram", style="pattern_hologram",
                    )
                )
                vertex_kind = f"pattern_vertex:{pattern_id}"
                markers.append(Marker(t=p1.bar_time, price=p1.price, text="1", kind=vertex_kind))
                markers.append(Marker(t=p2.bar_time, price=p2.price, text="2", kind=vertex_kind))

                last_sig = pattern_signals[-1]
                marker_price = close[df.index.get_loc(last_sig.bar_time)]
                marker_label = marker_text(
                    _LABEL_TR[pattern_name], last_sig.payload["event"], pattern_name,
                )
                markers.append(
                    Marker(
                        t=last_sig.bar_time, price=marker_price, text=marker_label,
                        kind=f"pattern_{last_sig.state}:{pattern_id}",
                    )
                )
                # 2026-09-04: kullanıcı "nerede AL sinyali geldiğini de
                # yazman gerekiyor" dedi -- head_shoulders.py'deki AYNI
                # marker altfyapısı (renderer._draw_markers'da dolgulu
                # üçgen + kalın AL/SAT metni).
                if last_sig.state in ("confirmed", "completed"):
                    markers.append(
                        Marker(
                            t=last_sig.bar_time, price=marker_price,
                            text="AL" if direction == "long" else "SAT",
                            kind=f"pattern_entry_{direction}:{pattern_id}",
                        )
                    )
                last_state[pattern_id] = {
                    "pattern": pattern_name, "direction": direction, "state": last_sig.state,
                    "event": last_sig.payload["event"], "target": target,
                }

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version, params_hash=params_hash(p),
            symbol="", timeframe=Timeframe.D1,
            signals=signals, levels=levels, markers=markers, polygons=polygons,
            last_state=last_state,
        )
