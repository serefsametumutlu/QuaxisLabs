"""AB=CD sinyalleri icin event-driven backtest motoru (Faz 3).

Kaynak: `C:\\Users\\Samet\\Desktop\\abcd-project\\abcd\\backtest.py` -- bu
projeye adapte edilmis (birebir kopya DEGIL). `pine/abcd_v2_5_indicator.pine`
artik strateji/emir kodu icermiyor (V2.5 = V2.1 PRO'nun tespit+cizim
mantigi, `strategy()` -> `indicator()`), yani asagidaki islem/maliyet
varsayimlarinin hicbiri Pine-parity zorunlulugu DEGIL -- bu modulun kendi,
acikca belgelenmis varsayimlaridir:

- Komisyon (`commission_pct`, varsayilan fill basina %0.1) ve kayma
  (`slippage_ticks` * `tick_size`, varsayilan 1 tick @ 0.01) icin kopyalanacak
  bir Pine kaynagi yok -- makul BIST-olcekli varsayilanlar secildi, ikisi de
  calistirma basina tam konfigure edilebilir.
- Pozisyon boyutlandirma ve equity compounding sembol-bazlidir: her sembol
  kendi backtest'ine `initial_equity` ile baslar ve bagimsiz compound eder
  (bu modulde portfoy-seviyesi heat/margin modeli YOK). `run_grid`, islemleri
  sadece siralama-amacli toplu istatistikler icin (R-multiple bazli: win
  rate, profit factor, expectancy) (tf, para birimi, parametre) hucresi
  basina havuzlar -- sembol/para birimleri arasinda ham PnL'i ASLA toplamaz.
- USD-denominasyonlu backtestler TL OHLC'yi her barin zaman damgasina en
  yakin USDTRY kapanisina boler (as-of merge) -- gercek bir
  BIST:XXXX/USDTRY sentetik grafiginin YAKLASIK degeri, birebir
  reprodüksiyonu DEGIL.

Islem yasam dongusu: TP1, pozisyonun `tp1_pct` kadarini `tp1` limitinde
kapatir, TP2 kalani `tp2`de kapatir, SL acik kalan ne varsa `sl`de cikar.
`use_be` ise, TP1 doldugunda kalanin stop'u (kayma-ayarli) giris fiyatina
tasinir. Tek bir barin high/low'u hem bir kar-al hem aktif stop'a
degdiginde, `conservative_same_bar` (varsayilan True) bunu SL-once cozer.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`.

  Karar 1 -- Modul izolasyonu: `abcd_pattern.py` ile ayni ilke -- bu modul de
  `src/analysis/`in genel felsefesinden (skorsuz/sinyalsiz) BILINCLI bir
  sapmadir, bir istisnadir, emsal DEGILDIR.

  Karar 2 -- Decimal istisnasi: Proje geneli Decimal-only olsa da, bu modul
  `abcd_pattern.py`/`abcd_data.py` ile AYNI gerekceyle (Pine-parity zorunlu
  olmasa da, ayni float64 sinyal/fiyat zincirinin devami oldugu icin) TAMAMEN
  float + pandas/numpy kullanir. Float deger BURADAN hicbir zaman Decimal
  tipli dataclass'lara/`scorer.py`'ye/`calculator.py`'ye SIZMAZ.

Katman disiplini -- bu modul SAF DEGILDIR (`abcd_pattern.py` gibi degil):
`run_grid`, coklu sembol x zaman dilimi x para birimi x parametre
kombinasyonunu `src.fetchers.abcd_data`'dan veri cekerek orkestre eder --
bu gercek I/O gerektirir (ag + parquet onbellek), bu yuzden saf olamaz.
`backtest_symbol`/`compute_metrics`/`to_usd`/`_simulate_trade` kendileri
SAF kalir (girdi olarak zaten cekilmis `pd.DataFrame`/`Signal` listesi alir,
hicbir I/O yapmaz) -- impurluk SADECE `run_grid` (ve `save_summary`)
sinirindadir. Bu modul `src.db.*` HICBIR modulu import ETMEZ.

## Quant-uzmani denetiminin 2 ek disiplini (spec, "Backtest metodolojisi")

1. **Coklu karsilastirma / overfitting riski.** `run_grid`, `min_trades_show`
   (varsayilan 30) esiginin ALTINDAKI hucreleri ASLA sessizce atmaz/gizlemez
   -- "GUVENSIZ (n=X)" gibi acikca etiketler (`guven_etiketi` sutunu). Rapor/
   "en verimli kosul" iddialari icin asil esik `min_trades_trustworthy`
   (varsayilan 100) -- `trustworthy` (bool) ayri bir sutundur, `n_trades` ile
   AYNI satirda. Grid boyutuna gore Bonferroni-tipi bir uyari (`grid_warning`
   sutunu/`DataFrame.attrs`) hesaplanir: `effective_alpha = 0.05 / n_hucre`.
2. **TL vs USD ayriminin gercek anlami.** `to_usd()` sonrasi `detect()`
   YENIDEN cagrilir -> USD serisindeki pivotlar TL'dekinden FARKLI olabilir.
   Bu, ayni sinyalin doviz-ayarlı getirisi DEGIL, USD-payda grafiginde
   BAGIMSIZ tespit edilmis bir sinyal kumesidir -- `run_grid` USD satirlarina
   bunu acikca belirten bir `currency_note` sutunu ekler.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, fields
from pathlib import Path

import numpy as np
import pandas as pd

import config
from src.analysis.abcd_pattern import Params, Signal, detect
from src.fetchers.abcd_data import fetch_ohlcv_abcd, fetch_usdtry

RESULTS_DIR = config.DATA_DIR / "abcd_backtest_results"

# Zaman dilimi basina yaklasik islem bari sayisi -- SADECE `--years` gecmis
# istegini boyutlandirmak icin kullanilir (fazla istemek asla hataya yol
# acmaz, sadece birkac fazladan onbellek bari ister).
_BARS_PER_YEAR = {"60": 252 * 7, "120": 252 * 4, "240": 252 * 2, "1D": 252, "1W": 52}


@dataclass(frozen=True)
class BacktestParams:
    tp1_pct: float = 0.40  # TP1'de kapatilan pozisyon orani
    risk_pct: float = 0.01  # islem basina riske edilen equity orani (boyutlandirma girdisi)
    commission_pct: float = 0.001  # fill basina, orn. 0.001 = %0.1
    slippage_ticks: float = 1.0
    tick_size: float = 0.01
    use_be: bool = True  # TP1 dolunca kalanin stop'unu girise tasi
    conservative_same_bar: bool = True  # ayni barda hem TP hem SL -> SL kazanir
    entry_mode: str = "fill"  # "fill" (gerceksi) veya "d_close" (iyimser)
    initial_equity: float = 100_000.0


@dataclass(frozen=True)
class Trade:
    symbol: str
    direction: int
    signal_bar: int
    entry_bar: int
    entry_time: pd.Timestamp
    entry_price: float
    sl_initial: float
    tp1: float
    tp2: float
    size: float
    tp1_filled: bool
    tp1_bar: int | None
    exit_bar: int
    exit_time: pd.Timestamp
    exit_price: float
    exit_reason: str  # "SL" | "SL_BE" | "TP1_FULL" | "TP2" | "OPEN_AT_END"
    bars_held: int
    commission_paid: float
    pnl: float
    pnl_pct: float
    r_multiple: float


def _entry_for(signal: Signal, params: BacktestParams, n_bars: int) -> tuple[int, float] | None:
    """Bir islemin nerede/hangi fiyattan girecegi. `None` = gerceklestirilemez
    (fill bari bu veri setinde henuz mevcut degil -- look-ahead bias YOK)."""
    if params.entry_mode == "fill":
        if np.isnan(signal.fill_ref):
            return None
        entry_bar = signal.signal_bar + 1
        return (entry_bar, float(signal.fill_ref)) if entry_bar < n_bars else None
    if params.entry_mode == "d_close":
        return signal.signal_bar, float(signal.entry_ref)
    raise ValueError(f"Bilinmeyen entry_mode: {params.entry_mode!r}")


def _already_beyond_at_signal_close(df: pd.DataFrame, signal: Signal) -> bool:
    """Pattern atlama kurali: onay barinin KENDI kapanisinda fiyat zaten
    TP1 veya SL'nin otesindeyse, kurulum harekete gecmeden once eskimistir
    -- kovalamak yerine atla."""
    close = float(df["close"].iloc[signal.signal_bar])
    if signal.direction > 0:
        return close >= signal.tp1 or close <= signal.sl
    return close <= signal.tp1 or close >= signal.sl


def _position_size(equity: float, entry_price: float, sl: float, params: BacktestParams) -> float:
    risk_per_share = abs(entry_price - sl)
    if risk_per_share <= 0 or entry_price <= 0:
        return 0.0
    raw = (equity * params.risk_pct) / risk_per_share
    capped = min(raw, equity / entry_price)
    return float(math.floor(max(capped, 0.0)))


def _simulate_trade(
    df: pd.DataFrame,
    symbol: str,
    signal: Signal,
    entry_bar: int,
    entry_price: float,
    equity: float,
    params: BacktestParams,
) -> Trade | None:
    direction = signal.direction
    sl_initial = signal.sl
    tp1, tp2 = signal.tp1, signal.tp2

    size = _position_size(equity, entry_price, sl_initial, params)
    if size <= 0:
        return None

    slip = params.slippage_ticks * params.tick_size
    fill_entry = entry_price + slip if direction > 0 else entry_price - slip
    if params.entry_mode == "d_close":
        fill_entry = entry_price  # iyimser mod: hayali fill'de islem kaymasi yok

    tp1_qty = math.floor(size * params.tp1_pct) if params.tp1_pct > 0 else 0.0
    remainder_qty = size - tp1_qty

    commission = fill_entry * size * params.commission_pct
    stop = sl_initial
    tp1_filled = False
    tp1_bar: int | None = None
    exit_bar = exit_price = exit_reason = None

    n = len(df)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)

    for i in range(entry_bar, n):
        hi, lo = high[i], low[i]
        hit_tp1 = (not tp1_filled) and tp1_qty > 0 and ((direction > 0 and hi >= tp1) or (direction < 0 and lo <= tp1))
        hit_tp2 = (direction > 0 and hi >= tp2) or (direction < 0 and lo <= tp2)
        hit_stop = (direction > 0 and lo <= stop) or (direction < 0 and hi >= stop)

        if not tp1_filled:
            if hit_stop and (params.conservative_same_bar or not hit_tp1):
                exit_bar, exit_price, exit_reason = i, stop, "SL"
                break
            if hit_tp1:
                tp1_filled, tp1_bar = True, i
                commission += tp1 * tp1_qty * params.commission_pct
                if remainder_qty <= 0:
                    exit_bar, exit_price, exit_reason = i, tp1, "TP1_FULL"
                    break
                if params.use_be:
                    stop = fill_entry
                if hit_tp2:  # kalan da TP1'in doldugu ayni barda TP2'ye deger
                    exit_bar, exit_price, exit_reason = i, tp2, "TP2"
                    break
                continue
            continue

        # tp1_filled: kalan pozisyon, muhtemelen break-even stop ile
        hit_stop_now = (direction > 0 and lo <= stop) or (direction < 0 and hi >= stop)
        if hit_stop_now and (params.conservative_same_bar or not hit_tp2):
            exit_bar, exit_price, exit_reason = i, stop, "SL_BE" if stop == fill_entry else "SL"
            break
        if hit_tp2:
            exit_bar, exit_price, exit_reason = i, tp2, "TP2"
            break
    else:
        exit_bar = n - 1
        exit_price = float(df["close"].iloc[-1])
        exit_reason = "OPEN_AT_END"

    remainder_exit_qty = remainder_qty if tp1_filled else size
    if exit_reason == "TP1_FULL":
        remainder_exit_qty = 0.0
    commission += exit_price * remainder_exit_qty * params.commission_pct

    sign = 1.0 if direction > 0 else -1.0
    pnl = sign * (exit_price - fill_entry) * remainder_exit_qty
    if tp1_filled and exit_reason != "TP1_FULL":
        pnl += sign * (tp1 - fill_entry) * tp1_qty
    elif exit_reason == "TP1_FULL":
        pnl = sign * (tp1 - fill_entry) * tp1_qty
    pnl -= commission

    initial_risk = abs(fill_entry - sl_initial) * size
    r_multiple = pnl / initial_risk if initial_risk > 0 else float("nan")

    return Trade(
        symbol=symbol,
        direction=direction,
        signal_bar=signal.signal_bar,
        entry_bar=entry_bar,
        entry_time=df["time"].iloc[entry_bar],
        entry_price=fill_entry,
        sl_initial=sl_initial,
        tp1=tp1,
        tp2=tp2,
        size=size,
        tp1_filled=tp1_filled,
        tp1_bar=tp1_bar,
        exit_bar=exit_bar,
        exit_time=df["time"].iloc[exit_bar],
        exit_price=float(exit_price),
        exit_reason=exit_reason,
        bars_held=exit_bar - entry_bar,
        commission_paid=commission,
        pnl=pnl,
        pnl_pct=(pnl / equity * 100.0) if equity > 0 else float("nan"),
        r_multiple=r_multiple,
    )


def backtest_symbol(
    df: pd.DataFrame, symbol: str, signals: list[Signal], params: BacktestParams = BacktestParams()
) -> tuple[list[Trade], pd.DataFrame]:
    """Bir sembol icin sinyalleri motordan gecirir. Ayni anda sadece TEK acik
    pozisyon: giris bari onceki islemin cikis barindan once olan bir sinyal
    atlanir. (islemler, equity_curve[time, equity]) doner."""
    equity = params.initial_equity
    trades: list[Trade] = []
    curve = [(df["time"].iloc[0], equity)]
    next_available_bar = 0
    n = len(df)

    for signal in sorted(signals, key=lambda s: s.signal_bar):
        entry = _entry_for(signal, params, n)
        if entry is None:
            continue
        entry_bar, entry_price = entry
        if entry_bar < next_available_bar or entry_bar >= n:
            continue
        if _already_beyond_at_signal_close(df, signal):
            continue

        trade = _simulate_trade(df, symbol, signal, entry_bar, entry_price, equity, params)
        if trade is None:
            continue

        equity += trade.pnl
        trades.append(trade)
        curve.append((trade.exit_time, equity))
        next_available_bar = trade.exit_bar + 1

    return trades, pd.DataFrame(curve, columns=["time", "equity"])


def trades_to_frame(trades: list[Trade]) -> pd.DataFrame:
    columns = [f.name for f in fields(Trade)]
    if not trades:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame([t.__dict__ for t in trades], columns=columns)


def compute_metrics(trades: list[Trade], equity_curve: pd.DataFrame, initial_equity: float, total_bars: int) -> dict:
    """Tek bir sembol/hucre icin R-multiple bazli istatistikler."""
    n = len(trades)
    if n == 0:
        return {
            "num_trades": 0,
            "win_rate": float("nan"),
            "profit_factor": float("nan"),
            "net_profit_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "expectancy_r": float("nan"),
            "avg_r": float("nan"),
            "exposure_pct": 0.0,
        }

    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_profit = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)

    final_equity = equity_curve["equity"].iloc[-1]
    running_max = equity_curve["equity"].cummax()
    drawdown = (equity_curve["equity"] - running_max) / running_max.replace(0, np.nan)

    r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
    bars_held_total = sum(t.bars_held for t in trades)

    return {
        "num_trades": n,
        "win_rate": len(wins) / n * 100.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
        "net_profit_pct": (final_equity - initial_equity) / initial_equity * 100.0,
        "max_drawdown_pct": float(drawdown.min() * 100.0) if not drawdown.empty else 0.0,
        "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
        "avg_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
        "exposure_pct": (bars_held_total / total_bars * 100.0) if total_bars > 0 else 0.0,
    }


def to_usd(df: pd.DataFrame, usdtry_df: pd.DataFrame) -> pd.DataFrame:
    """Yaklasik USD-denominasyonlu OHLC: her barin KENDI zaman damgasina en
    yakin (asof, geriye dogru) USDTRY kapanisina boler. Bkz. modul ust notu
    -- bu, TL serisi + `detect()`'in USD-payda serisinde BAGIMSIZ olarak
    YENIDEN calistirilacagi anlamina gelir, "doviz-ayarlı getiri" DEGIL."""
    if usdtry_df.empty:
        raise ValueError("Doviz cevrimi icin USDTRY verisi mevcut degil")
    merged = pd.merge_asof(
        df.sort_values("time"),
        usdtry_df[["time", "close"]].sort_values("time").rename(columns={"close": "usdtry"}),
        on="time",
        direction="backward",
    )
    merged = merged.dropna(subset=["usdtry"])
    out = merged.copy()
    for col in ("open", "high", "low", "close"):
        out[col] = out[col] / out["usdtry"]
    return out.drop(columns="usdtry").reset_index(drop=True)


# ── coklu-sembol / coklu-zaman-dilimi / coklu-para-birimi grid ────────────


def _bars_for_years(tf: str, years: float) -> int:
    return max(int(_BARS_PER_YEAR[tf] * years) + 50, 200)


def _params_label(p: Params) -> str:
    return f"L{p.pivot_lookback}_atr{p.atr_mult}_eps{p.fib_tolerance}"


_CURRENCY_NOTE_USD = (
    "USD-payda grafiginde BAGIMSIZ tespit -- ayni sinyalin doviz-ayarlı hali DEGIL: "
    "to_usd() sonrasi detect() USD-payda serisinde YENIDEN calistirilir, pivotlar "
    "(A/B/C/D) TL serisinden FARKLI cikabilir."
)


def run_grid(
    symbols: list[str],
    tfs: list[str] = ("240", "1D"),
    backtest_params: BacktestParams = BacktestParams(),
    denominators: tuple[str, ...] = ("TRY", "USD"),
    years: float = 2.0,
    min_trades_show: int = 30,
    min_trades_trustworthy: int = 100,
    detector_params: list[Params] = (Params(),),
    show_progress: bool = False,
) -> pd.DataFrame:
    """Her (sembol x tf x detector_params x para birimi) kombinasyonunu
    backtest'ten gecirir ve siralama-amacli toplu istatistikler icin islemleri
    (tf, para birimi, params) hucresi basina havuzlar.

    quant-uzmani denetiminin 2 disiplini burada uygulanir (bkz. modul ust
    notu): HICBIR hucre -- `min_trades_show`'un altinda olsa bile -- sessizce
    ATILMAZ; `n_trades` her satirda `profit_factor`/`expectancy_r` ile AYNI
    hucrede goruntulenir; `trustworthy` (n>=`min_trades_trustworthy`) ayri
    bir bool sutundur; USD satirlari `currency_note` ile acikca etiketlenir;
    grid boyutuna gore Bonferroni-tipi bir `grid_warning` hesaplanir.

    Donen DataFrame BOSSA (hicbir sembol/tf veri getirmediyse) sutunlari
    tanimli bos bir DataFrame doner, hata FIRLATMAZ.
    """
    cells: dict[tuple[str, str, str], dict] = {}

    tf_iter = list(tfs)
    denom_iter = list(denominators)
    dp_iter = list(detector_params)

    for tf in tf_iter:
        n_bars = _bars_for_years(tf, years)
        usdtry_df = None
        if "USD" in denom_iter:
            usdtry_df = fetch_usdtry(tf, n_bars)

        for symbol in symbols:
            df_try = fetch_ohlcv_abcd(symbol, tf, n_bars)
            if df_try.empty:
                continue

            for denom in denom_iter:
                if denom == "USD":
                    if usdtry_df is None or usdtry_df.empty:
                        continue
                    try:
                        df = to_usd(df_try, usdtry_df)
                    except ValueError:
                        continue
                elif denom == "TRY":
                    df = df_try
                else:
                    raise ValueError(f"Desteklenmeyen para birimi: {denom!r}")

                if df.empty:
                    continue

                for dp in dp_iter:
                    label = _params_label(dp)
                    signals = detect(df, dp)
                    trades, curve = backtest_symbol(df, symbol, signals, backtest_params)

                    key = (tf, denom, label)
                    cell = cells.setdefault(key, {"trades": [], "drawdowns": [], "total_bars": 0})
                    cell["trades"].extend(trades)
                    if trades:
                        metrics = compute_metrics(trades, curve, backtest_params.initial_equity, len(df))
                        cell["drawdowns"].append(metrics["max_drawdown_pct"])
                    cell["total_bars"] += len(df)

    rows = []
    for (tf, denom, label), cell in cells.items():
        trades = cell["trades"]
        n = len(trades)
        r_values = [t.r_multiple for t in trades if not math.isnan(t.r_multiple)]
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = -sum(t.pnl for t in losses)

        if n < min_trades_show:
            guven_etiketi = f"GUVENSIZ (n={n})"
        elif n < min_trades_trustworthy:
            guven_etiketi = f"DUSUK GUVEN (n={n})"
        else:
            guven_etiketi = "GUVENILIR"

        rows.append(
            {
                "tf": tf,
                "currency": denom,
                "params": label,
                "n_trades": n,
                "win_rate": (len(wins) / n * 100.0) if n else float("nan"),
                "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else float("nan"),
                "expectancy_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
                "avg_r": (sum(r_values) / len(r_values)) if r_values else float("nan"),
                "avg_max_drawdown_pct": float(np.mean(cell["drawdowns"])) if cell["drawdowns"] else float("nan"),
                "exposure_pct": (sum(t.bars_held for t in trades) / cell["total_bars"] * 100.0) if cell["total_bars"] else 0.0,
                "trustworthy": n >= min_trades_trustworthy,
                "guven_etiketi": guven_etiketi,
                "currency_note": _CURRENCY_NOTE_USD if denom == "USD" else "",
            }
        )

    # Coklu-karsilastirma uyarisi: grid boyutu = fiilen uretilen hucre sayisi
    # (veri bulunamayan kombinasyonlar zaten hic hucre olusturmaz); hic hucre
    # yoksa teorik grid boyutuna (tf x para birimi x parametre) duser.
    n_hucre = len(rows) if rows else max(len(tf_iter) * len(denom_iter) * len(dp_iter), 1)
    effective_alpha = 0.05 / n_hucre
    grid_warning = (
        f"{n_hucre} hucre karsilastirildi ({len(tf_iter)} zaman dilimi x {len(denom_iter)} para birimi x "
        f"{len(dp_iter)} parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= "
        f"{effective_alpha:.5f} (0.05/{n_hucre}) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; "
        "secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin."
    )

    columns = [
        "tf", "currency", "params", "n_trades", "win_rate", "profit_factor", "expectancy_r", "avg_r",
        "avg_max_drawdown_pct", "exposure_pct", "trustworthy", "guven_etiketi", "currency_note", "grid_warning",
    ]
    if rows:
        summary = pd.DataFrame(rows)
        summary["grid_warning"] = grid_warning
        summary = summary[columns].sort_values(
            ["trustworthy", "profit_factor", "expectancy_r"], ascending=[False, False, False]
        ).reset_index(drop=True)
    else:
        summary = pd.DataFrame(columns=columns)

    summary.attrs["grid_warning"] = grid_warning
    summary.attrs["effective_alpha"] = effective_alpha
    summary.attrs["n_hucre"] = n_hucre
    return summary


def save_summary(summary: pd.DataFrame, path: Path | None = None) -> Path:
    """`run_grid` ciktisini CSV olarak kaydeder (HTML/plotly raporu YOK --
    proje bu bagimliligi istemiyor, sade CSV yeterli)."""
    target = path or (RESULTS_DIR / "abcd_backtest_summary.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(target, index=False)
    return target
