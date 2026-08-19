"""src.analysis.volume_profile_mr testleri -- sentetik DataFrame'ler."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.volume_profile_mr import Params, detect


def _df(closes, opens=None, highs=None, lows=None, volumes=None) -> pd.DataFrame:
    n = len(closes)
    opens = opens if opens is not None else closes
    highs = highs if highs is not None else [max(o, c) + 0.3 for o, c in zip(opens, closes)]
    lows = lows if lows is not None else [min(o, c) - 0.3 for o, c in zip(opens, closes)]
    volumes = volumes if volumes is not None else [1000.0] * n
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": opens, "high": highs, "low": lows, "close": closes, "volume": volumes,
        }
    )


def test_hicbir_kosul_saglanmazsa_sinyal_yok():
    closes = [100.0 + 0.01 * i for i in range(60)]  # yavas yukselis, RSI dusuk kalmaz
    df = _df(closes)
    signals = detect(df, Params())
    assert signals == []


def test_deger_alani_altina_dusup_donen_seride_sinyal_uretir():
    # 30 bar 100 civari SIKI yatay (hacim profili dar bir VAL uretir), sonra
    # HAFIF bir dusus (VAL'in biraz altina, RSI dusuk) -- SL'nin entry'nin
    # ALTINDA kalmasi icin dusus asiri BUYUK OLMAMALI (bkz. modul ust notu
    # "dejenere/ters siralanmis hedefler" korumasi).
    rng = np.random.default_rng(0)
    flat = 100.0 + rng.normal(0, 0.3, 30)
    drop = list(np.linspace(flat[-1], 98.9, 6))  # VAL'in HEMEN altina, 1 ATR'den AZ (bkz. ust not)
    # Donus bari SON bar OLMAMALI -- detect() fill_ref icin bir SONRAKI bari
    # gerektirir (range(n-1)), bu yuzden donustan sonra 1 bar daha eklenir.
    closes = list(flat) + drop + [99.0, 99.3]
    opens = closes.copy()
    opens[-2] = 98.85  # donus bari yesil: close(99.0) > open(98.85)
    df = _df(closes, opens=opens)
    signals = detect(df, Params(vp_lookback=20, rsi_period=5, rsi_oversold=40.0))
    assert len(signals) >= 1
    sig = signals[-1]
    assert sig.direction == 1
    assert sig.sl < sig.entry_ref < sig.tp1 <= sig.tp2


def test_hurst_mr_filtresi_acikken_daha_az_veya_esit_sinyal():
    rng = np.random.default_rng(1)
    flat = 100.0 + rng.normal(0, 1.0, 40)
    drop = list(np.linspace(flat[-1], 85.0, 10))
    closes = list(flat) + drop + [86.0, 86.5, 87.0]
    df = _df(closes)
    base = detect(df, Params(vp_lookback=20, rsi_period=5, rsi_oversold=45.0))
    filtered = detect(df, Params(vp_lookback=20, rsi_period=5, rsi_oversold=45.0, require_hurst_mr=True, hurst_window=30, hurst_max_lag=10))
    assert len(filtered) <= len(base)


def test_kisa_seride_firlatmaz_bos_liste():
    df = _df([100.0, 101.0, 99.0])
    assert detect(df, Params()) == []
