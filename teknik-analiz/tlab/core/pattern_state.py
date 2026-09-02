"""Genel "kırılım çizgisi + hedef" durum makinesi.

`tlab/indicators/harmonics/state.py`'nin XABCD'ye özgü `track_pattern`'inden
genelleştirilmiştir — takoz/üçgen (wedge/triangle), omuz-baş-omuz (H&S),
bayrak/flama (flag/pennant), çift tepe/dip ve genişleyen formasyon (broadening)
gibi "bir kırılım çizgisini/boynu aşınca onaylanır, sonra hedefe gider ya da
retest eder" yapısındaki TÜM Faz 8B formasyonları bunu paylaşır.

Durumlar: PENDING -> CONFIRMED (kırılım) -> RETEST_HOLD (kırılım seviyesine
geri dönüp tutma) / TARGET_REACHED (hedefe ulaşma); PENDING -> INVALIDATED
(kırılımdan ÖNCE ters yönde geçersizlik) / EXPIRED (kırılım hiç gelmeden
zaman aşımı). `SignalState` (core/types.py) yalnızca 6 sabit değer taşıdığı
için (retest_hold/target_reached gibi ek anlamlar YOK), bu ayrım
`golden_zone.py`'nin ZATEN kullandığı desenle aynı şekilde `payload["event"]`
üzerinden yapılır: pending->"pending", confirmed VE retest_hold->"confirmed",
target_reached->"completed", invalidated->"invalidated", expired->"expired".
`event` alanı her zaman `f"{pattern_name}_{suffix}"` biçimindedir (ör.
"falling_wedge_confirmed") — `config/scans.yaml`'daki `filter.events` bu
alana bakar.

Her geçiş kendi barında damgalanır (bar_time=detected_at=o bar), geriye
yazım yok — `invalidation_check`/`break_line` yalnızca [0,t] barlarını
kullanan (df/close/high/low'a closure ile erişen) çağıran tarafından
sağlanmalıdır; bu modül df'ye HİÇ dokunmaz (yalnızca ön-hesaplı `atr_series`
ve callable'lar üzerinden çalışır)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from tlab.core.types import Direction, Signal

EVENT_SUFFIXES = (
    "pending", "confirmed", "retest_hold", "target_reached", "invalidated", "expired",
)

SUFFIX_LABEL_TR: dict[str, str] = {
    "pending": "OLUŞUYOR", "confirmed": "ONAY", "retest_hold": "RETEST TUTTU",
    "target_reached": "HEDEFE ULAŞTI", "invalidated": "GEÇERSİZ", "expired": "SÜRESİ DOLDU",
}


def marker_text(pattern_label_tr: str, event: str, pattern_name: str) -> str:
    """`event` (`"{pattern_name}_{suffix}"`) içindeki son eki Türkçe'ye
    çevirip `pattern_label_tr` ile birleştirir (ör. "ALÇALAN TAKOZ [ONAY]")
    — tüm Faz 8B indikatörlerinin marker metinleri bunu paylaşır."""
    prefix = pattern_name + "_"
    suffix = event[len(prefix):] if event.startswith(prefix) else event
    return f"{pattern_label_tr} [{SUFFIX_LABEL_TR.get(suffix, suffix.upper())}]"


@dataclass(frozen=True)
class PatternTrackingConfig:
    """`track_breakout_pattern`'a bir adayın nasıl izleneceğini anlatır.

    break_line: kırılım çizgisinin/boynun idx barındaki değeri (ör.
    `Trendline.value_at` veya `neckline_value_at`). direction="long" ise
    onay = kapanışın bu değerin ÜSTÜNE geçmesi, "short" ise ALTINA.
    invalidation_check(t, bar_high, bar_low): True dönerse PENDING iken
    aday geçersizleşir (ör. ters yöndeki çizginin kırılması) — None ise
    kırılımdan önce geçersizleşme kontrolü yapılmaz.
    max_bars_to_confirm: born_idx'ten itibaren bu kadar bar içinde
    onaylanmazsa EXPIRED (None ise süresiz beklenir).
    """

    pattern_id: str
    pattern_name: str
    direction: Direction
    break_line: Callable[[int], float]
    target: float
    confirm_bars: int
    max_bars_to_confirm: int | None
    retest_tol_atr: float
    atr_series: pd.Series
    score: float
    invalidation_check: Callable[[int, float, float], bool] | None = None
    extra_payload: dict = field(default_factory=dict)
    max_bars_to_target: int | None = None
    """CONFIRMED (kırılım onaylandı) olduktan sonra hedefin gelmesi için
    üst sınır — `max_bars_to_confirm`'ün AYNISI ama kırılım SONRASI hedef
    bekleyişi için (2026-09-03, gerçek veriyle bulunan bir sorun: bu alan
    eklenmeden önce hedef beklemesi SÜRESİZDİ — `patterns.*` göstergelerinde
    684 güne kadar çıkan "kırılım oldu, aylarca sonra tesadüfen hedefe
    değindi" zincirleri `latest_signals()`'ın en-güncel-satır mantığıyla
    bugünmüş gibi bir AL sinyali olarak görünüyordu). None ise (varsayılan,
    geriye dönük uyumluluk için) süresiz beklenir — çağıran taraf KENDİ
    formasyon geometrisine göre bir değer vermelidir (bkz. `patterns/*.py`)."""


def level_end_from_signals(signals: list[Signal]) -> pd.Timestamp | None:
    """Bir Level'ın (ör. hedef fiyatı) `end`'ini son sinyalin durumuna göre
    belirler: "pending"/"confirmed" hâlâ AÇIK sayılır (uzamaya devam eder,
    `end=None`); "completed"/"invalidated"/"expired" TERMİNALDİR, `end`
    o barda SABİTLENİR. Tüm Faz 8B pattern indikatörleri bunu paylaşır."""
    terminal = signals[-1]
    if terminal.state in ("pending", "confirmed"):
        return None
    return terminal.bar_time


def track_breakout_pattern(
    df: pd.DataFrame, born_idx: int, cfg: PatternTrackingConfig,
) -> list[Signal]:
    """`born_idx`'ten (adayın PENDING olarak doğduğu bar) başlayarak df'nin
    sonuna kadar bar-bar tarar; en az bir "pending" Signal her zaman döner."""
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    close = df["close"].to_numpy()
    n = len(df)
    direction = cfg.direction

    def _event(suffix: str) -> str:
        return f"{cfg.pattern_name}_{suffix}"

    def _payload(suffix: str, **extra: object) -> dict:
        return {
            "pattern_id": cfg.pattern_id, "pattern_name": cfg.pattern_name,
            "event": _event(suffix), "target": cfg.target,
            **cfg.extra_payload, **extra,
        }

    signals: list[Signal] = [
        Signal(
            bar_time=df.index[born_idx], detected_at=df.index[born_idx],
            direction=direction, state="pending", score=cfg.score, payload=_payload("pending"),
        )
    ]

    state = "pending"
    confirm_streak = 0
    confirmed_idx: int | None = None
    retest_done = False

    for t in range(born_idx, n):
        if state in ("invalidated", "expired", "target_reached"):
            break

        if state == "pending":
            bars_since_born = t - born_idx
            if cfg.max_bars_to_confirm is not None and bars_since_born > cfg.max_bars_to_confirm:
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="expired", score=cfg.score, payload=_payload("expired"),
                    )
                )
                state = "expired"
                break

            if cfg.invalidation_check is not None and cfg.invalidation_check(t, high[t], low[t]):
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="invalidated", score=cfg.score, payload=_payload("invalidated"),
                    )
                )
                state = "invalidated"
                break

            line_val = cfg.break_line(t)
            beyond = close[t] > line_val if direction == "long" else close[t] < line_val
            confirm_streak = confirm_streak + 1 if beyond else 0
            if confirm_streak >= cfg.confirm_bars:
                confirmed_idx = t
                signals.append(
                    Signal(
                        bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                        state="confirmed", score=cfg.score,
                        payload=_payload("confirmed", break_price=float(close[t])),
                    )
                )
                state = "confirmed"
            continue

        # state == "confirmed": hedef ve retest izlemesi
        if (
            cfg.max_bars_to_target is not None
            and confirmed_idx is not None
            and (t - confirmed_idx) > cfg.max_bars_to_target
        ):
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                    state="expired", score=cfg.score, payload=_payload("expired"),
                )
            )
            state = "expired"
            break

        target_hit = close[t] >= cfg.target if direction == "long" else close[t] <= cfg.target
        if target_hit:
            signals.append(
                Signal(
                    bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                    state="completed", score=cfg.score, payload=_payload("target_reached"),
                )
            )
            state = "target_reached"
            break

        if not retest_done and confirmed_idx is not None and t > confirmed_idx:
            a = cfg.atr_series.iloc[t]
            if not pd.isna(a):
                line_val = cfg.break_line(t)
                near = abs(close[t] - line_val) <= cfg.retest_tol_atr * a
                held = close[t] > line_val if direction == "long" else close[t] < line_val
                if near and held:
                    retest_done = True
                    signals.append(
                        Signal(
                            bar_time=df.index[t], detected_at=df.index[t], direction=direction,
                            state="confirmed", score=cfg.score, payload=_payload("retest_hold"),
                        )
                    )

    return signals
