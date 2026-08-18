"""Momentum Confluence (V1/V2) icin kazanan/kaybeden faktor analizi --
`abcd_factor_analysis.py`nin (Faz 8) AYNI istatistik motorunu (kronolojik
split, Benjamini-Hochberg FDR, holdout dogrulama, VIF-budanmis lojistik
regresyon) YENIDEN KULLANIR (`run_factor_analysis`in `feature_names`/
`categorical_features`/`extract_features_fn` parametreleri -- bkz. o
fonksiyonun docstring'i) -- hesaplama mantigi IKI YERDE YASAMAZ ilkesi.

Momentum Confluence sinyalinin ABCD'den (A/B/C/D pivotu) FARKLI bir yapisi
oldugu icin (bkz. `momentum_confluence.py` modul ust notu) ozellik kumesi de
FARKLI: `abcd_factor_analysis.extract_features`in ABCD'ye ozgu 13 ozelligi
(cd_ratio_dev, d_proximity_50bar, vb.) BURAYA UYGULANMAZ -- bunun yerine
sinyalin KENDI tesbit-anindaki teshis alanlari (`momentum_confluence.Signal`
-- ema_spread_pct, volume_ratio, downward_streak_before_flip, wt1_at_signal)
+ genel teknik baglam gostergeleri (RSI/ADX/Bollinger/SMA200 -- AYNI
`abcd_factor_analysis`daki SAF fonksiyonlardan REUSE edilir, YENIDEN
YAZILMAZ) kullanilir.

Katman disiplini: `abcd_factor_analysis.py` ile AYNI -- `src.fetchers.*`/
`src.db.*` HICBIR modulu import etmez.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.abcd_factor_analysis import _adx_wilder, _bollinger_percent_b, _rsi_wilder

CONTINUOUS_FEATURES = [
    "ema_spread_pct",
    "volume_ratio",
    "downward_streak_before_flip",
    "wt1_at_signal",
    "rsi14",
    "adx14",
    "bb_percent_b",
    "price_vs_sma50_pct",
    "body_range_ratio",
]
CATEGORICAL_FEATURES = ["above_sma200"]
ALL_FEATURES = CONTINUOUS_FEATURES + CATEGORICAL_FEATURES


def extract_features(trade_row: pd.Series | dict, ohlcv_df: pd.DataFrame) -> dict[str, float | int | None]:
    """`trade_row`: `scripts/momentum_confluence_arastirma.py`nin urettigi
    satir sekli (`sig_signal_bar`, `sig_ema_spread_pct`, `sig_volume_ratio`,
    `sig_downward_streak_before_flip`, `sig_wt1_at_signal` -- `Signal`in
    teshis alanlarinin `sig_` onekiyle KOPYASI, `abcd_backtest.collect_trades`
    ile AYNI isimlendirme ilkesi). LOOK-AHEAD YOK: genel gostergeler
    `ohlcv_df.iloc[:signal_bar+1]`e kesilerek hesaplanir (`abcd_factor_
    analysis.extract_features` ile AYNI disiplin)."""
    row = trade_row if isinstance(trade_row, dict) else trade_row.to_dict()
    signal_bar = int(row["sig_signal_bar"])

    df = ohlcv_df.iloc[: signal_bar + 1].reset_index(drop=True)
    n = len(df)
    if n <= signal_bar:
        raise ValueError(f"ohlcv_df, signal_bar={signal_bar} icin yeterli veri icermiyor (n={n}).")

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    open_ = df["open"].to_numpy(dtype=float)

    features: dict[str, float | int | None] = {
        "ema_spread_pct": row.get("sig_ema_spread_pct"),
        "volume_ratio": row.get("sig_volume_ratio"),
        "downward_streak_before_flip": row.get("sig_downward_streak_before_flip"),
        "wt1_at_signal": row.get("sig_wt1_at_signal"),
    }
    # NaN'lar (orn. V1'de wt1_at_signal HER ZAMAN NaN) None'a cevrilir --
    # `run_factor_analysis` None'lari dropna ile eler, NaN'i SESSIZCE
    # gecistirmez.
    for key, value in list(features.items()):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            features[key] = None

    rsi = _rsi_wilder(close, 14)
    features["rsi14"] = float(rsi[signal_bar]) if not np.isnan(rsi[signal_bar]) else None

    adx = _adx_wilder(df, 14)
    features["adx14"] = float(adx[signal_bar]) if not np.isnan(adx[signal_bar]) else None

    bb = _bollinger_percent_b(close, 20, 2.0)
    features["bb_percent_b"] = float(bb[signal_bar]) if not np.isnan(bb[signal_bar]) else None

    sma50 = pd.Series(close).rolling(50).mean().to_numpy()
    sma200 = pd.Series(close).rolling(200).mean().to_numpy()
    s50, s200 = sma50[signal_bar], sma200[signal_bar]
    features["price_vs_sma50_pct"] = float((close[signal_bar] - s50) / s50 * 100.0) if (not np.isnan(s50) and s50 != 0) else None
    features["above_sma200"] = int(close[signal_bar] > s200) if not np.isnan(s200) else None

    o, h, l, c = open_[signal_bar], high[signal_bar], low[signal_bar], close[signal_bar]
    features["body_range_ratio"] = float(abs(c - o) / (h - l)) if (h - l) > 0 else None

    return features
