"""src/analysis/momentum_confluence_variants.py testleri.

En kritik test PARITY testleridir: `VARIANTS["V1_BASELINE"]`/`VARIANTS
["V2_BASELINE"]`, `momentum_confluence.detect(df, params, "v1"/"v2")` ile
BİREBİR aynı sinyalleri üretmeli -- aksi halde ablasyon karşılaştırmalarının
hiçbir anlamı kalmaz (baseline'ın kendisi yanlışsa, "X'i eklemek/çıkarmak
şunu değiştirdi" iddiası da güvenilmez olur).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analysis import momentum_confluence as mc
from src.analysis import momentum_confluence_variants as mcv


def _ohlcv(close: list[float], volume: list[float] | None = None, open_: list[float] | None = None) -> pd.DataFrame:
    n = len(close)
    close_arr = np.array(close, dtype=float)
    open_arr = np.array(open_, dtype=float) if open_ is not None else close_arr.copy()
    high = np.maximum(open_arr, close_arr) + 0.01
    low = np.minimum(open_arr, close_arr) - 0.01
    vol = np.array(volume, dtype=float) if volume is not None else np.full(n, 1000.0)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": open_arr,
            "high": high,
            "low": low,
            "close": close_arr,
            "volume": vol,
        }
    )


def _dusustensonra_patlamali_kirilim_serisi(n_down: int = 40, n_up: int = 6) -> pd.DataFrame:
    """`tests/test_momentum_confluence.py`deki AYNI senaryo (KOPYALANDI,
    import EDİLMEDİ -- test dosyaları birbirinden bağımsız kalır, proje
    deseni)."""
    rng = np.random.default_rng(7)
    down = 200.0 - np.cumsum(rng.uniform(0.5, 1.5, n_down))
    squeeze_base = down[-1]
    squeeze = squeeze_base + rng.uniform(-0.05, 0.05, 5)
    breakout = squeeze[-1] + np.cumsum(rng.uniform(2.0, 4.0, n_up))
    close = np.concatenate([down, squeeze, breakout])
    volume = np.full(len(close), 1000.0)
    volume[len(down) + len(squeeze):] *= 3.0
    return _ohlcv(list(close), volume=list(volume))


def _sig_key(sig) -> tuple:
    return (sig.direction, sig.signal_bar, round(sig.entry_ref, 6), round(sig.tp1, 6), round(sig.tp2, 6), round(sig.sl, 6))


# ── PARITY: V1_BASELINE/V2_BASELINE == momentum_confluence.detect() ────────


def test_v1_baseline_orijinal_v1_ile_birebir_aynidir():
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    orig = mc.detect(df, params, "v1")
    variant = mcv.detect_variant(df, params, mcv.VARIANTS["V1_BASELINE"])
    assert [_sig_key(s) for s in orig] == [_sig_key(s) for s in variant]


def test_v2_baseline_orijinal_v2_ile_birebir_aynidir():
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    orig = mc.detect(df, params, "v2")
    variant = mcv.detect_variant(df, params, mcv.VARIANTS["V2_BASELINE"])
    assert [_sig_key(s) for s in orig] == [_sig_key(s) for s in variant]


@pytest.mark.parametrize("seed", [1, 2, 3, 11, 42])
def test_parity_farkli_rastgele_serilerde_de_korunur(seed):
    rng = np.random.default_rng(seed)
    n_down, n_up = 40, 6
    down = 200.0 - np.cumsum(rng.uniform(0.5, 1.5, n_down))
    squeeze = down[-1] + rng.uniform(-0.05, 0.05, 5)
    breakout = squeeze[-1] + np.cumsum(rng.uniform(2.0, 4.0, n_up))
    close = np.concatenate([down, squeeze, breakout])
    volume = np.full(len(close), 1000.0)
    volume[n_down + 5:] *= 3.0
    df = _ohlcv(list(close), volume=list(volume))
    params = mc.Params()

    orig_v1 = mc.detect(df, params, "v1")
    var_v1 = mcv.detect_variant(df, params, mcv.VARIANTS["V1_BASELINE"])
    assert [_sig_key(s) for s in orig_v1] == [_sig_key(s) for s in var_v1]

    orig_v2 = mc.detect(df, params, "v2")
    var_v2 = mcv.detect_variant(df, params, mcv.VARIANTS["V2_BASELINE"])
    assert [_sig_key(s) for s in orig_v2] == [_sig_key(s) for s in var_v2]


# ── Ablasyon davranışı ───────────────────────────────────────────────────


def test_hacimsiz_varyant_hacim_filtresi_olmadan_en_az_v1_kadar_sinyal_uretir():
    """`V1_HACIMSIZ`, hacim kosulunu TAMAMEN kaldirir -- yapisal olarak
    V1_BASELINE'in sinyal kumesinin bir UST KUMESI (>=) olmalidir (baska
    hicbir kosul degismedi, SADECE bir tanesi gevsetildi)."""
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    baseline = mcv.detect_variant(df, params, mcv.VARIANTS["V1_BASELINE"])
    hacimsiz = mcv.detect_variant(df, params, mcv.VARIANTS["V1_HACIMSIZ"])
    assert len(hacimsiz) >= len(baseline)
    baseline_bars = {s.signal_bar for s in baseline}
    hacimsiz_bars = {s.signal_bar for s in hacimsiz}
    assert baseline_bars.issubset(hacimsiz_bars)


def test_hacim_bandi_asiri_hacimli_sinyali_eler():
    """`vol_ratio_max` UST SINIRI -- hacim orani bu sayidan BUYUKSE sinyal
    ELENIR (faktor analizi bulgusunun -- asiri hacimin kazanci artirmadigi --
    dogrudan test edilebilir hali)."""
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    baseline_flags = mcv.VariantFlags(name="t", require_volume=True)
    banded_flags = mcv.VariantFlags(name="t2", require_volume=True, vol_ratio_max=0.01)  # imkansiz kadar dar bant

    baseline = mcv.detect_variant(df, params, baseline_flags)
    banded = mcv.detect_variant(df, params, banded_flags)
    assert len(baseline) > 0
    assert banded == []  # hicbir sinyal bu kadar dar bandi gecemez


def test_gevsek_hacim_esigi_daha_fazla_veya_esit_sinyal_uretir():
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    strict = mcv.detect_variant(df, params, mcv.VariantFlags(name="strict", require_volume=True, vol_mult=1.5))
    loose = mcv.detect_variant(df, params, mcv.VariantFlags(name="loose", require_volume=True, vol_mult=1.2))
    assert len(loose) >= len(strict)


# ── Yeni gostergeler (RSI/MACD/StochRSI/Bollinger) -- 2026-08-19 ──────────


def test_rsi_surekli_yukselen_seride_yuksek_kalir():
    close = np.cumsum(np.full(60, 1.0)) + 100.0  # kesintisiz artan
    rsi = mcv._rsi(close, length=14)
    assert not np.isnan(rsi[-1])
    assert rsi[-1] > 90.0  # hic kayip yok -> RSI ~100'e yakin


def test_rsi_surekli_dusen_seride_dusuk_kalir():
    close = 200.0 - np.cumsum(np.full(60, 1.0))
    rsi = mcv._rsi(close, length=14)
    assert rsi[-1] < 10.0


def test_macd_yukselen_trendde_pozitiftir():
    close = np.cumsum(np.full(80, 1.0)) + 100.0
    macd_line, signal_line = mcv._macd(close)
    assert macd_line[-1] > 0
    assert macd_line[-1] > signal_line[-1]


def test_bollinger_duz_fiyatta_bantlar_esittir():
    close = np.full(30, 100.0)
    basis, upper, lower = mcv._bollinger(close, length=20)
    assert upper[-1] == pytest.approx(basis[-1], abs=1e-9)
    assert lower[-1] == pytest.approx(basis[-1], abs=1e-9)


def test_stoch_rsi_0_100_araliginda_kalir():
    rng = np.random.default_rng(5)
    close = 100.0 + np.cumsum(rng.normal(0, 1, 100))
    k, d = mcv._stoch_rsi(close)
    valid_k = k[~np.isnan(k)]
    valid_d = d[~np.isnan(d)]
    assert len(valid_k) > 0
    assert (valid_k >= -1e-6).all() and (valid_k <= 100.0 + 1e-6).all()
    assert (valid_d >= -1e-6).all() and (valid_d <= 100.0 + 1e-6).all()


def test_yeni_gosterge_flagleri_sinyal_sayisini_asla_arttirmaz():
    """Her yeni gosterge kosulu, V1/V2 baseline'a EK bir filtre olarak
    eklenir -- bu yapisal olarak sinyal sayisini ASLA ARTTIRAMAZ (sadece
    daraltabilir/ayni kalabilir)."""
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    v1_baseline = mcv.detect_variant(df, params, mcv.VARIANTS["V1_BASELINE"])
    for name in ("V1_ARTI_RSI", "V1_ARTI_MACD", "V1_ARTI_STOCHRSI", "V1_ARTI_BB"):
        variant_signals = mcv.detect_variant(df, params, mcv.VARIANTS[name])
        assert len(variant_signals) <= len(v1_baseline), name


def test_variants_sozlugu_tum_flagleri_hatasiz_calistirir():
    """`VARIANTS`teki HER kombinasyon en azindan HATASIZ calismali (crash
    YOK) -- gercek sinyal sayisi 0 olabilir, bu gecerli bir sonuc, hata
    DEGIL."""
    df = _dusustensonra_patlamali_kirilim_serisi()
    params = mc.Params()
    for name, flags in mcv.VARIANTS.items():
        signals = mcv.detect_variant(df, params, flags)
        for sig in signals:
            assert sig.sl < sig.entry_ref < sig.tp1 < sig.tp2, name
            assert sig.direction == 1
