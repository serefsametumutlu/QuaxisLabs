"""RelativeMomentumPair — long-only rölatif momentum geçişi (pair trading).

`context={"x": df_x}` alan İLK indikatör (Faz 0'dan beri BaseIndicator.compute
context parametresini destekliyordu, ama Faz 3/4'teki hiçbir indikatör
kullanmamıştı). `df` = Y hissesi, `context["x"]` = X hissesi.

Hesap: spread = log(Y) - β·log(X); z = (spread - rolling_mean)/rolling_std
(bkz. tlab/features/stats.py — bu modül Faz 2'de tam bu amaçla yazılmıştı).
Sinyal DÖNÜŞ ONAYLIDIR (eşiği İLK aşan bar değil, eşiğin İÇİNE geri dönen
bar): z[t-1] < -k ve z[t] >= -k -> Y ucuzdu, dönüş onaylandı -> "Y AL";
z[t-1] > +k ve z[t] <= +k -> "X AL". Yalnızca kapanmış barlarla, yalnızca
min_periods sonrası.

bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md (K2, STRAT-08) disiplinleri:
- DISIPLIN-08: β geçmişten (yalnızca t'den ÖNCEki pencere) tahmin edilir,
  sinyal t'de üretilir, işlem execution parametresine göre t'nin kapanışında
  ya da t+1'in açılışında yürütülür — üç zaman dilimi hiç karışmaz.
- DISIPLIN-06 (bkz. discovery.py): bu indikatörün KENDİSİ çift seçmez,
  yalnızca VERİLEN bir çiftin sinyalini üretir — seçim-lookahead riski
  discovery.py'nin sorumluluğundadır, burada YOKTUR.

Context güvenlik deseni: `context["x"]` HER ZAMAN önce `df.index` (Y) ile
inner-join edilir (`common_idx`), SONRA tüm hesaplar `common_idx`'e
kısıtlanmış Series'ler üzerinden yapılır. Bu yüzden context DataFrame'i
`df`'den daha uzun/gelecek barlar içerse bile sızıntı YOKTUR — kesilme
sınırı her zaman `df`'nin kendi uzunluğundan gelir. `tlab/testing/
repaint.py`'nin context'i de kesen genel mekanizması yine de gelecekteki
(bu deseni takip etmeyen) context'li indikatörler için bağımsız bir
güvenlik ağıdır."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from tlab.backtest.pairs_engine import run_pair_backtest, run_pair_backtest_market_neutral
from tlab.core.indicator import BaseIndicator
from tlab.core.params import BaseParams, params_hash
from tlab.core.types import (
    Box,
    Direction,
    IndicatorMeta,
    IndicatorResult,
    Marker,
    Signal,
    Timeframe,
)
from tlab.features.stats import adf_pvalue, halflife, log_spread, rolling_beta, rolling_corr, zscore
from tlab.indicators.pairs.coint_monitor import cointegration_broken

BetaMethod = Literal["one", "rolling_ols"]
InitialHolding = Literal["y", "x", "none_until_signal"]
Execution = Literal["close", "next_open"]
Mode = Literal["rotational", "mean_reversion"]


@dataclass(frozen=True)
class RelativeMomentumParams(BaseParams):
    # window/beta_window=60 (2026-08-29, kullanıcı kararı): eski varsayılan
    # (90) hem sıkı (13 çift) hem gevşek (28 çift) eşikli discover_pairs
    # örnekleminde en az işlemi ve en düşük toplam PnL/profit-factor'ü
    # üretiyordu (bkz. gerçek discover_pairs+run_pair_backtest ile yapılan
    # pencere taraması, 20/30/40/60/90 arası) — 60, keşfedilen çiftlerin
    # tipik yarı ömrüne (~13-27 gün) göre de daha tutarlı bir oran (3-5x
    # kaba kuralına yakın; 90 bu çiftler için aşırı yavaş kalıyordu).
    # İN-SAMPLE bir seçim, walk-forward doğrulaması YAPILMADI — bkz.
    # CLAUDE.md backlog'daki "kointegrasyon çürüme izleyicisi" notu.
    window: int = 60
    k: float = 2.0
    beta_method: BetaMethod = "rolling_ols"
    beta_window: int = 60
    min_periods: int = 60
    execution: Execution = "close"
    commission_bps: float = 10.0
    start_capital: float = 100_000.0
    initial_holding: InitialHolding = "none_until_signal"
    y_symbol: str = "Y"
    x_symbol: str = "X"
    # 2026-09-03: kullanıcı "arbitraj nadir sinyal veren bir strateji değil
    # mi, günlük onlarca sinyal geliyor" dedi -- kök neden, bu stratejinin
    # ROTASYONEL olması (her an ya Y ya da X'i tutuyor, "pozisyon dışı"
    # diye bir hâli yok). Bir geçiş (regime_switch) gerçekten NADİR (gerçek
    # veride ör. ~1/ay) ama `latest_signals()` o çiftin EN SON geçişini,
    # ne kadar eski olursa olsun, hep "confirmed" (= "AL sinyali geldi")
    # gösteriyordu -- taze bir olayla "hâlâ aynı tarafı tutuyoruz" bilgisini
    # ayırt etmiyordu. `freshness_bars` kadar bar geçtikten sonra AYNI
    # zincire (aynı `payload["event"]`, dedup için) "active" durumunda bir
    # takip sinyali eklenir -- bu, `latest_signals()`'ın varsayılan
    # confirmed/completed filtresinden düşer (BEKLENİYOR/arka plan bilgisi
    # olarak "Tüm durumları göster"de hâlâ görülebilir), zincirin KENDİSİ
    # SİLİNMEZ. Sabit bir bar (`switch_idx + freshness_bars`) kullanılır --
    # tarama HANGİ günü çalışırsa çalışsın AYNI sonucu verir (non-repaint).
    freshness_bars: int = 3
    # Faz 2, 2C (docs/TANI_VE_YOL_HARITASI_v2.md ## FAZ 2) -- mevcut
    # ROTASYONEL motoru BOZMADAN yanına gerçek bir istatistiksel arbitraj
    # modu: "rotational" (varsayılan, davranış AYNEN korunuyor -- aşağıdaki
    # 5 alan bu modda HİÇ okunmaz) vs "mean_reversion" (referans:
    # awesome-quant-ai chapter2 -- Faz 2 tanısının (f) bulgusu: eski motorda
    # çıkış/zarar-kes/zaman-stopu/kilit YOKTU, her an ya Y ya X'te %100
    # long'du, "nakit/flat" hâli hiç yoktu -- market-neutral istatistiksel
    # arbitraj DEĞİL, sürekli piyasa beta'sına maruz bir rotasyondu).
    mode: Mode = "rotational"
    # |z| < exit_k -> pozisyon KAPATILIR (nakit/flat -- mean_reversion'ın
    # rotasyoneldeki "hep bir tarafta" sorununu çözen asıl mekanizma).
    exit_k: float = 0.5
    # 2026-09-04 KULLANICI KARARI (docs/PROGRESS_LOG.md "Faz 2" bölümü):
    # gerçek 17-çiftlik listede in-sample/out-of-sample ayrımlı bir parametre
    # taraması (window/k/exit_k/stop_k/max_hold_bars, 243 kombinasyon)
    # koşuldu. Eski değer (3.0) OOS'ta kazanma oranını %53.2'de tutuyordu;
    # `stop_k` GEVŞETİLDİĞİNDE (4.0) -- window/k SABİT tutulup YALNIZCA bu
    # mode'a ÖZGÜ alanlar (exit_k/stop_k/max_hold_bars, rotasyonel modu HİÇ
    # etkilemez) taranınca -- OOS kazanma oranı %53.5'e, medyan getiri
    # +0.86%'ya çıktı (n=43 OOS işlem). Bu, birçok farklı window/k/exit_k
    # kombinasyonunda TUTARLI tekrarlanan bir bulguydu (tek bir "şanslı
    # hücre" değil) -- eski (3.0), pozisyonları normal oynaklıkta bile
    # gereksiz erken kapatıyordu. `window`/`k` (rotasyonel modun da PAYLAŞTIĞI
    # alanlar) KASITLI OLARAK değiştirilmedi -- taramanın window=20/k=2.5 ile
    # ÇOK HAFİF daha iyi bir OOS sonucu (kazanma %56.1) olsa da, bunları
    # değiştirmek 2026-08-29'da AYRI bir kullanıcı kararıyla kalibre edilmiş
    # rotasyonel modun varsayılan davranışını da SESSİZCE değiştirirdi (Faz
    # 2, 2C'nin "mevcut ROTASYONEL motoru BOZMA" ilkesini ihlal eder) --
    # mean_reversion'ın TAM optimize edilmiş seti isteyen `window=20, k=2.5`
    # açıkça geçmeli.
    stop_k: float = 4.0
    # Giriş barından bu kadar bar sonra -- z hâlâ dönmediyse -- zorunlu kapat
    # (zaman stopu, referans uygulamadaki "30 gün sonra kapat" kuralı).
    # 2026-09-04: yukarıdaki `stop_k` taramasıyla AYNI turda 30->40 optimize
    # edildi (AYNI gerekçe/kısıt -- window/k sabit).
    max_hold_bars: int = 40
    # Zorunlu tasfiye (stop_k) SONRASI z tekrar GİRİŞ bandının (±k) içine
    # dönene kadar yeni giriş YOK -- "kırılmış" bir eşbütünleşmenin hemen
    # ardından aynı yönde yeniden girmeyi önler (normal exit_k çıkışı ya da
    # zaman stopu SONRASI kilit UYGULANMAZ, yalnızca stop_k -- ikisi
    # "beklenen" bir dönüş, stop "beklenmeyen" bir kırılma sinyali).
    lockout_until_reentry: bool = True
    # Faz 2, 2C -- YENİ: tlab/indicators/pairs/coint_monitor.py (CLAUDE.md
    # backlog madde 4) opsiyonel entegrasyonu. `None` (varsayılan) =
    # KAPALI, davranış DEĞİŞMEZ. Verilirse: aktif bir pozisyonun spread'i
    # üzerinde ROLLING Engle-Granger p-değeri izlenir, eşiği (`coint_break_
    # p_threshold`) geri aşarsa (yapısal kırılma) z HENÜZ dönmemiş olsa
    # bile pozisyon zorunlu kapatılır (`mr_cointegration_broken` olayı) --
    # stop_k/exit_k/max_hold_bars'tan BAĞIMSIZ, EK bir çıkış tetikleyicisi.
    coint_monitor_window: int | None = None
    coint_break_p_threshold: float = 0.10


def _beta_series(y_log: pd.Series, x_log: pd.Series, p: RelativeMomentumParams) -> pd.Series:
    rolling = rolling_beta(y_log, x_log, p.beta_window)
    if p.beta_method == "rolling_ols":
        return rolling
    first_valid = rolling.first_valid_index()
    if first_valid is None:
        return pd.Series(float("nan"), index=y_log.index)
    fixed_value = float(rolling.loc[first_valid])
    beta = pd.Series(float("nan"), index=y_log.index)
    beta.loc[first_valid:] = fixed_value
    return beta


class RelativeMomentumPair(BaseIndicator):
    """İki hisse (Y=df, X=context["x"]) arasında long-only rölatif momentum
    geçişi: Z-skoru ±k eşiğinden dönüş onaylandığında ucuz kalan tarafa
    geçiş yapılır."""

    meta = IndicatorMeta(
        name="pair.relative_momentum",
        version="0.1.0",
        category="pair",
        description="Long-only rölatif momentum geçişi (Z-skor dönüş onaylı) + backtest.",
        supported_timeframes=(Timeframe.D1, Timeframe.H4),
    )

    def __init__(self, params: RelativeMomentumParams | None = None) -> None:
        self.params: RelativeMomentumParams = params or RelativeMomentumParams()

    def compute(self, df: pd.DataFrame, context: dict[str, Any] | None = None) -> IndicatorResult:
        if context is None or "x" not in context:
            raise ValueError("RelativeMomentumPair context={'x': df_x} gerektirir")
        p = self.params
        df_x = context["x"]

        common_idx = df.index.intersection(df_x.index)
        dropped_y = len(df) - len(common_idx)
        dropped_x = len(df_x) - len(common_idx)
        if len(common_idx) < p.min_periods + 2:
            raise ValueError(
                f"Hizalanan {len(common_idx)} bar, min_periods+2={p.min_periods + 2}'den az"
            )

        y = df.loc[common_idx, "close"].astype(float)
        x = df_x.loc[common_idx, "close"].astype(float)
        y_open = df.loc[common_idx, "open"].astype(float) if "open" in df.columns else None
        x_open = df_x.loc[common_idx, "open"].astype(float) if "open" in df_x.columns else None

        y_log, x_log = y.apply(_safe_log), x.apply(_safe_log)
        beta = _beta_series(y_log, x_log, p)
        spread = log_spread(y, x, beta)
        z = zscore(spread, p.window)
        corr_series = rolling_corr(y_log, x_log, p.window)

        n = len(common_idx)
        first_signal_ok = max(p.window, p.beta_window, p.min_periods)

        if p.mode == "mean_reversion":
            signals, markers, boxes, series, last_state = self._compute_mean_reversion(
                p, common_idx, y, x, y_open, x_open, beta, spread, z, n, first_signal_ok,
            )
        else:
            signals, markers, boxes, series, last_state = self._compute_rotational(
                p, common_idx, y, x, y_open, x_open, beta, spread, z, corr_series, n,
                first_signal_ok, dropped_y, dropped_x,
            )

        return IndicatorResult(
            indicator=self.meta.name, version=self.meta.version,
            params_hash=params_hash(p), symbol=f"{p.y_symbol}/{p.x_symbol}",
            timeframe=Timeframe.D1,
            signals=signals, boxes=boxes, markers=markers,
            series=series, last_state=last_state,
        )

    def _compute_rotational(
        self, p: RelativeMomentumParams, common_idx: pd.Index,
        y: pd.Series, x: pd.Series, y_open: pd.Series | None, x_open: pd.Series | None,
        beta: pd.Series, spread: pd.Series, z: pd.Series, corr_series: pd.Series,
        n: int, first_signal_ok: int, dropped_y: int, dropped_x: int,
    ) -> tuple[list[Signal], list[Marker], list[Box], dict[str, pd.Series], dict[str, Any]]:
        """Faz 0'dan beri var olan ROTASYONEL davranış -- BİREBİR korunuyor
        (Faz 2, 2C'nin `mode="mean_reversion"` eklemesi bunu HİÇ değiştirmez,
        yalnızca `compute()`'tan buraya taşındı)."""
        holding = _initial_holding_series(common_idx, p.initial_holding)
        signals: list[Signal] = []
        markers: list[Marker] = []
        switch_idxs: list[int] = []

        for t in range(1, n):
            if t < first_signal_ok:
                continue
            z_prev, z_now = z.iloc[t - 1], z.iloc[t]
            if pd.isna(z_prev) or pd.isna(z_now):
                continue

            side: Literal["y", "x"] | None = None
            if z_prev < -p.k and z_now >= -p.k:
                side = "y"
            elif z_prev > p.k and z_now <= p.k:
                side = "x"
            if side is None:
                continue

            holding.iloc[t:] = 1.0 if side == "y" else 0.0
            direction: Direction = "long"
            symbol = p.y_symbol if side == "y" else p.x_symbol
            window_start = max(0, t - p.window + 1)
            corr_t = corr_series.iloc[t]
            corr = float(corr_t) if not pd.isna(corr_t) else float("nan")
            spread_window = spread.iloc[window_start : t + 1].dropna()
            try:
                adf_p = adf_pvalue(spread_window) if len(spread_window) >= 8 else float("nan")
            except ValueError:
                adf_p = float("nan")
            try:
                hl = halflife(spread_window) if len(spread_window) >= 3 else float("nan")
            except ValueError:
                hl = float("nan")

            payload = {
                "event": "regime_switch", "side": side, "symbol": symbol,
                "z_prev": float(z_prev), "z_now": float(z_now),
                "beta": float(beta.iloc[t]) if not pd.isna(beta.iloc[t]) else None,
                "corr": corr, "adf_pvalue": adf_p, "halflife": hl,
            }
            signals.append(
                Signal(
                    bar_time=common_idx[t], detected_at=common_idx[t], direction=direction,
                    state="confirmed", score=1.0, payload=payload,
                )
            )
            markers.append(
                Marker(t=common_idx[t], price=float(z_now), text=f"{symbol} AL", kind="pair_signal")
            )
            switch_idxs.append(t)

        # Her geçişin (yalnızca SONUNCUsunun DEĞİL — bkz. yukarıdaki not,
        # aksi hâlde eski bir geçişin bayatlama sinyali bir SONRAKİ geçiş
        # olduğunda kesikte kaybolur, bu REPAINT sayılır) kendi bayatlama
        # işareti — sabit `switch_idx + freshness_bars` barında, bir daha
        # geri alınmaz (extend-only).
        for i, switch_idx in enumerate(switch_idxs):
            stale_idx = switch_idx + p.freshness_bars
            # Bir SONRAKİ geçiş zaten bu bardan önce olduysa bayatlama
            # işareti eklenmez -- yoksa eski geçişin (daha geç barlı)
            # "active" işareti yeni geçişin "confirmed"ini yanlışlıkla
            # geçersiz kılar (detected_at karşılaştırmasında kazanır).
            next_switch_idx = switch_idxs[i + 1] if i + 1 < len(switch_idxs) else n
            if stale_idx < next_switch_idx and stale_idx < n:
                switch_signal = signals[i]
                signals.append(
                    Signal(
                        bar_time=common_idx[stale_idx], detected_at=common_idx[stale_idx],
                        direction=switch_signal.direction, state="active", score=1.0,
                        payload=switch_signal.payload,
                    )
                )

        result = run_pair_backtest(
            y, x, holding, p.start_capital, p.commission_bps, p.execution, y_open, x_open,
        )

        boxes = _holding_boxes(common_idx, holding, y, x, p.y_symbol, p.x_symbol)

        series = {
            "y_norm": y / y.iloc[0] * 100.0,
            "x_norm": x / x.iloc[0] * 100.0,
            "z": z,
            "upper": pd.Series(p.k, index=common_idx),
            "lower": pd.Series(-p.k, index=common_idx),
            "portfolio": result.portfolio,
            "buyhold_5050": result.buyhold_5050,
            "holding": holding,
        }

        z_today = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else None
        z_yesterday = float(z.iloc[-2]) if n > 1 and not pd.isna(z.iloc[-2]) else None
        last_signal = signals[-1] if signals else None
        fired_today = last_signal is not None and last_signal.bar_time == common_idx[-1]
        signal_today = "YENİ AL SİNYALİ" if fired_today else None
        last_holding = holding.iloc[-1]
        holding_symbol = (
            None if pd.isna(last_holding) else (p.y_symbol if last_holding >= 0.5 else p.x_symbol)
        )
        last_state = {
            "z_today": z_today,
            "z_yesterday": z_yesterday,
            "holding": holding_symbol,
            "signal_today": signal_today,
            "portfolio_value": float(result.portfolio.iloc[-1]),
            "net_pnl": result.net_pnl,
            "return_pct": result.return_pct,
            "n_trades": result.n_trades,
            "max_drawdown_pct": result.max_drawdown,
            "win_rate_pct": result.win_rate,
            "avg_holding_bars": result.avg_holding_bars,
            "dropped_bars_y": dropped_y,
            "dropped_bars_x": dropped_x,
            "zone_state": _zone_state(z_today, p.k),
        }
        return signals, markers, boxes, series, last_state

    def _compute_mean_reversion(
        self, p: RelativeMomentumParams, common_idx: pd.Index,
        y: pd.Series, x: pd.Series, y_open: pd.Series | None, x_open: pd.Series | None,
        beta: pd.Series, spread: pd.Series, z: pd.Series, n: int, first_signal_ok: int,
    ) -> tuple[list[Signal], list[Marker], list[Box], dict[str, pd.Series], dict[str, Any]]:
        """Faz 2, 2C -- GERÇEK istatistiksel arbitraj modu (bkz. `Relative
        MomentumParams.mode` docstring'i): `position[t]` +1 (Y uzun/X kısa,
        z<=-k'da girilir), -1 (Y kısa/X uzun, z>=+k'da girilir), 0 (nakit).
        Referans: awesome-quant-ai chapter2 -- giriş eşiği AŞILDIĞINDA
        (rotasyonel moddaki gibi bandın İÇİNE dönüşü BEKLEMEDEN) girilir,
        çünkü burada bahis "aşırı sapmanın devam eden ortalamaya dönüşü"
        üzerine (rotasyonelin "dönüş zaten onaylandı, ucuz tarafa geç"
        mantığından FARKLI)."""
        position = pd.Series(0.0, index=common_idx, dtype=float)
        signals: list[Signal] = []
        markers: list[Marker] = []

        # Faz 2, 2C -- opsiyonel kointegrasyon çürüme izleyicisi (bkz.
        # `coint_monitor.py` + `RelativeMomentumParams.coint_monitor_window`
        # docstring'i). TEK SEFERDE önceden hesaplanır (döngü içinde her
        # bar için yeniden `engle_granger_pvalue` çağırmak O(n*window) yerine
        # O(n^2*window) olurdu).
        coint_broken = (
            cointegration_broken(y, x, p.coint_monitor_window, p.coint_break_p_threshold)
            if p.coint_monitor_window is not None else None
        )

        current = 0.0
        entry_idx: int | None = None
        locked_out = False

        for t in range(n):
            if t < first_signal_ok:
                continue
            zt = z.iloc[t]
            if pd.isna(zt):
                position.iloc[t] = current
                continue

            if current == 0.0:
                if locked_out and abs(zt) < p.k:
                    locked_out = False
                if not locked_out:
                    if zt <= -p.k:
                        current, entry_idx = 1.0, t
                        self._emit_mr_signal(
                            signals, markers, common_idx, t, "mr_entry_long", "long",
                            p.y_symbol, zt, beta,
                        )
                    elif zt >= p.k:
                        current, entry_idx = -1.0, t
                        self._emit_mr_signal(
                            signals, markers, common_idx, t, "mr_entry_short", "short",
                            p.x_symbol, zt, beta,
                        )
            else:
                assert entry_idx is not None
                az = abs(zt)
                bars_held = t - entry_idx
                exit_event: str | None = None
                if coint_broken is not None and bool(coint_broken.iloc[t]):
                    exit_event = "mr_cointegration_broken"
                elif az > p.stop_k:
                    exit_event = "mr_stop"
                elif az < p.exit_k:
                    exit_event = "mr_exit"
                elif bars_held >= p.max_hold_bars:
                    exit_event = "mr_time_stop"
                if exit_event is not None:
                    prior_dir: Direction = "long" if current > 0 else "short"
                    self._emit_mr_signal(
                        signals, markers, common_idx, t, exit_event, prior_dir,
                        p.y_symbol if current > 0 else p.x_symbol, zt, beta, state="completed",
                    )
                    current, entry_idx = 0.0, None
                    if exit_event == "mr_stop" and p.lockout_until_reentry:
                        locked_out = True
            position.iloc[t] = current

        result = run_pair_backtest_market_neutral(
            y, x, position, beta, p.start_capital, p.commission_bps, p.execution, y_open, x_open,
        )
        boxes = _position_boxes(common_idx, position, y, x, p.y_symbol, p.x_symbol)

        series = {
            "y_norm": y / y.iloc[0] * 100.0,
            "x_norm": x / x.iloc[0] * 100.0,
            "z": z,
            "upper": pd.Series(p.k, index=common_idx),
            "lower": pd.Series(-p.k, index=common_idx),
            "exit_upper": pd.Series(p.exit_k, index=common_idx),
            "exit_lower": pd.Series(-p.exit_k, index=common_idx),
            "stop_upper": pd.Series(p.stop_k, index=common_idx),
            "stop_lower": pd.Series(-p.stop_k, index=common_idx),
            "portfolio": result.portfolio,
            "position": position,
        }

        z_today = float(z.iloc[-1]) if not pd.isna(z.iloc[-1]) else None
        z_yesterday = float(z.iloc[-2]) if n > 1 and not pd.isna(z.iloc[-2]) else None
        last_signal = signals[-1] if signals else None
        fired_today = last_signal is not None and last_signal.bar_time == common_idx[-1]
        last_position = position.iloc[-1]
        position_label = (
            f"{p.y_symbol} UZUN / {p.x_symbol} KISA" if last_position > 0
            else f"{p.y_symbol} KISA / {p.x_symbol} UZUN" if last_position < 0
            else "NAKİT"
        )
        last_state = {
            "z_today": z_today,
            "z_yesterday": z_yesterday,
            "position": position_label,
            "signal_today": (
                last_signal.payload["event"] if fired_today and last_signal is not None else None
            ),
            "portfolio_value": float(result.portfolio.iloc[-1]),
            "net_pnl": result.net_pnl,
            "return_pct": result.return_pct,
            "n_trades": result.n_trades,
            "max_drawdown_pct": result.max_drawdown,
            "win_rate_pct": result.win_rate,
            "avg_holding_bars": result.avg_holding_bars,
            "zone_state": _zone_state(z_today, p.k),
        }
        return signals, markers, boxes, series, last_state

    @staticmethod
    def _emit_mr_signal(
        signals: list[Signal], markers: list[Marker], common_idx: pd.Index, t: int,
        event: str, direction: Direction, symbol: str, zt: float, beta: pd.Series,
        state: Literal["confirmed", "completed"] = "confirmed",
    ) -> None:
        beta_t = beta.iloc[t]
        payload = {
            "event": event, "symbol": symbol, "z": float(zt),
            "beta": float(beta_t) if not pd.isna(beta_t) else None,
        }
        signals.append(
            Signal(
                bar_time=common_idx[t], detected_at=common_idx[t], direction=direction,
                state=state, score=1.0, payload=payload,
            )
        )
        text = {
            "mr_entry_long": "AL", "mr_entry_short": "SAT", "mr_exit": "ÇIK",
            "mr_stop": "STOP", "mr_time_stop": "SÜRE", "mr_cointegration_broken": "KIRILDI",
        }[event]
        markers.append(
            Marker(t=common_idx[t], price=float(zt), text=f"{symbol} {text}", kind="pair_mr_signal")
        )


def _safe_log(v: float) -> float:
    import math

    return math.log(v) if v > 0 else float("nan")


def _initial_holding_series(index: pd.Index, initial_holding: InitialHolding) -> pd.Series:
    if initial_holding == "none_until_signal":
        return pd.Series(float("nan"), index=index)
    value = 1.0 if initial_holding == "y" else 0.0
    return pd.Series(value, index=index)


def _zone_state(z_today: float | None, k: float) -> str:
    """Faz 6 tarama panosu için üç kademeli sınıflama (bkz. images/ referans
    ekran görüntüsü: YENİ AL SİNYALİ / DEVAM EDEN FIRSAT / BÖLGEYE
    YAKLAŞIYOR) — burada yalnızca ANLIK durum hesaplanır, sıralama Faz 6'nın işi."""
    if z_today is None:
        return "veri_yok"
    az = abs(z_today)
    if az >= k:
        return "asiri_bolgede"
    if az >= 0.75 * k:
        return "bolgeye_yaklasiyor"
    return "notr"


def _holding_boxes(
    index: pd.Index, holding: pd.Series, y: pd.Series, x: pd.Series, y_symbol: str, x_symbol: str
) -> list[Box]:
    """Tutulan dönem kutuları — low/high, o pencerede Y ve X fiyatlarının
    kapladığı aralıktır (renderer bunu fiyat panelinin ARKASINA tam
    yükseklikte gölge olarak çizecek, bkz. Faz 7 — bu alan yalnızca
    o pencerenin gerçek fiyat aralığını kaydeder, extend-only sözleşmesi
    gereği kutu bittiğinde bir daha değişmez)."""
    boxes: list[Box] = []
    n = len(index)
    run_start: int | None = None
    run_side: float | None = None

    def emit(start: int, end: int, side: float) -> None:
        # low/high YALNIZCA giriş barından (start) hesaplanır ve bir daha
        # değişmez (ranges.py/zones.py'deki "sınırlar tespit anında
        # sabitlenir" ilkesiyle aynı) — pencerenin TÜM aralığından
        # (start..end) hesaplamak, kutu hâlâ açıkken (end ileri kaydıkça)
        # low/high'ın sonradan değişmesine (repaint) yol açardı.
        symbol = y_symbol if side >= 0.5 else x_symbol
        style = "y_holding" if side >= 0.5 else "x_holding"
        entry_low = float(min(y.iloc[start], x.iloc[start]))
        entry_high = float(max(y.iloc[start], x.iloc[start]))
        boxes.append(
            Box(
                t0=index[start], t1=index[end], low=entry_low, high=entry_high,
                label=f"{symbol} Tutulan Dönem", style=style,
            )
        )

    for i in range(n):
        h = holding.iloc[i]
        side = None if pd.isna(h) else (1.0 if h >= 0.5 else 0.0)
        if side != run_side:
            if run_start is not None and run_side is not None:
                emit(run_start, i - 1, run_side)
            run_start, run_side = (i, side) if side is not None else (None, None)
    if run_start is not None and run_side is not None:
        emit(run_start, n - 1, run_side)
    return boxes


def _position_boxes(
    index: pd.Index, position: pd.Series, y: pd.Series, x: pd.Series, y_symbol: str, x_symbol: str
) -> list[Box]:
    """`_holding_boxes`'ın Faz 2, 2C (`mode="mean_reversion"`) eşdeğeri --
    TEK fark: `position` üç değer alır (+1/-1/0), `0` (nakit/flat) hiçbir
    kutu ÜRETMEZ (rotasyonel modun aksine, burada gerçek bir "pozisyon
    dışı" hâli var -- extend-only/sabitlenmiş-sınır sözleşmesi AYNI)."""
    boxes: list[Box] = []
    n = len(index)
    run_start: int | None = None
    run_side: float | None = None

    def emit(start: int, end: int, side: float) -> None:
        symbol_pair = (
            f"{y_symbol} UZUN / {x_symbol} KISA" if side > 0
            else f"{y_symbol} KISA / {x_symbol} UZUN"
        )
        style = "y_holding" if side > 0 else "x_holding"
        entry_low = float(min(y.iloc[start], x.iloc[start]))
        entry_high = float(max(y.iloc[start], x.iloc[start]))
        boxes.append(
            Box(
                t0=index[start], t1=index[end], low=entry_low, high=entry_high,
                label=symbol_pair, style=style,
            )
        )

    for i in range(n):
        p_i = position.iloc[i]
        side = None if pd.isna(p_i) or p_i == 0.0 else (1.0 if p_i > 0 else -1.0)
        if side != run_side:
            if run_start is not None and run_side is not None:
                emit(run_start, i - 1, run_side)
            run_start, run_side = (i, side) if side is not None else (None, None)
    if run_start is not None and run_side is not None:
        emit(run_start, n - 1, run_side)
    return boxes
