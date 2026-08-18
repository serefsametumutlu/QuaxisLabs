"""src/analysis/abcd_factor_analysis.py testleri.

Iki katman: (1) `extract_features` -- elle kurulmus, deterministik (dogrusal
artan kapanis serisi -- RSI/ATR/ADX/proximity gibi gostergelerin BEKLENEN
degerlerini elle hesaplanabilir kilan) sentetik OHLC ile, gercek ag cagrisi
YOK. (2) `run_factor_analysis` -- `extract_features`i monkeypatch ederek
(gercek gosterge hesabini degil, SADECE istatistik motorunu -- kronolojik
split/FDR/holdout-dogrulama/underpowered-etiketleme -- test etmek icin)
kontrollu sentetik ozellik/etiket verisiyle.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.analysis import abcd_factor_analysis
from src.analysis.abcd_factor_analysis import (
    ALL_FEATURES,
    extract_features,
    format_report,
    run_factor_analysis,
)


# ── extract_features: deterministik sentetik OHLC ──────────────────────────


def _linear_trend_ohlcv(n: int) -> pd.DataFrame:
    """Her barda close bir onceki bardan TAM 1 birim artar, high=close+1,
    low=close-1, open=close-0.5, volume=1000+i -- RSI/ATR/ADX/proximity gibi
    gostergelerin elle dogrulanabilir, KAPALI-FORM degerler uretmesini
    saglar (bkz. asagidaki testlerin yorum satirlari)."""
    close = 100.0 + np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "time": pd.date_range("2024-01-01", periods=n, freq="1D", tz="UTC"),
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0 + np.arange(n, dtype=float),
        }
    )


def _trade_row(signal_bar: int, a_bar: int, c_bar: int, d_bar: int, close: np.ndarray, cd_ratio: float = 1.03) -> dict:
    return {
        "sig_signal_bar": signal_bar,
        "sig_a_bar": a_bar,
        "sig_b_bar": a_bar + (c_bar - a_bar) // 2,
        "sig_c_bar": c_bar,
        "sig_d_bar": d_bar,
        "sig_a_price": float(close[a_bar]),
        "sig_b_price": float(close[a_bar]),
        "sig_c_price": float(close[c_bar]),
        "sig_d_price": float(close[d_bar]),
        "sig_bc_ratio": 0.6,
        "sig_cd_ratio": cd_ratio,
    }


def test_extract_features_dogrusal_artan_seride_kapali_form_degerler():
    n = 260
    df = _linear_trend_ohlcv(n)
    close = df["close"].to_numpy()
    signal_bar, a_bar, c_bar, d_bar = 250, 230, 240, 248
    row = _trade_row(signal_bar, a_bar, c_bar, d_bar, close, cd_ratio=1.03)

    feats = extract_features(row, df)

    # RSI: her bar kesin bir onceki bardan buyuk (gain=1, loss=0 HER ZAMAN)
    # -> avg_loss=0 -> formul avg_loss==0 durumunda 100.0'a sabitler.
    assert feats["rsi14"] == 100.0

    # d body/range: |close-open|/(high-low) = 0.5 / 2.0 = 0.25 (SABIT).
    assert math.isclose(feats["d_body_range_ratio"], 0.25)

    # Hacim orani: elle ayni pencerelerle hesaplanan beklenen deger.
    volume = df["volume"].to_numpy()
    expected_ratio = volume[c_bar : d_bar + 1].mean() / volume[max(d_bar - 20, 0) : d_bar].mean()
    assert math.isclose(feats["volume_ratio"], expected_ratio)

    # ATR-normalize C->D hizi: TR sabit 2.0 (high-low=2, |high[i]-close[i-1]|=2,
    # |low[i]-close[i-1]|=0 -> max=2) -> atr14 SABIT 2.0. d_price-c_price=8,
    # cd_bars=8 -> |8|/(2*8) = 0.5.
    assert math.isclose(feats["atr_norm_cd_speed"], 0.5, rel_tol=1e-6)

    # cd_ratio hassasiyeti
    assert math.isclose(feats["cd_ratio_dev"], 0.03, rel_tol=1e-6)

    # 50-bar proximity: dogrusal artan seride D her zaman pencerenin ZIRVESINE
    # yakin cikar -- elle hesap (bkz. modul yorumu): (close[248]-close[198]+1)/51 = 1.0
    assert math.isclose(feats["d_proximity_50bar"], 1.0, rel_tol=1e-6)

    # C->D suresi
    assert feats["cd_duration_bars"] == d_bar - c_bar == 8

    # Trend konumu: dogrusal artan seride guncel kapanis HER ZAMAN SMA50/SMA200'un ustunde.
    assert feats["above_sma50"] == 1
    assert feats["above_sma200"] == 1
    assert feats["price_vs_sma200_pct"] > 0.0

    # ADX: sabit egimli dogrusal trend -> +DM sabit 1, -DM sabit 0, TR sabit 2
    # -> +DI->50, -DI->0, DX->100, ADX (Wilder RMA of sabit 100) yakinsak ~100.
    assert abs(feats["adx14"] - 100.0) < 1.0

    # MACD/Bollinger: kesin kapali-form degil, sadece hesaplanabildigini dogrula.
    assert feats["macd_hist_sign"] in (-1, 0, 1)
    assert isinstance(feats["macd_hist_slope"], float)
    assert isinstance(feats["bb_percent_b"], float)


def test_extract_features_open_nan_ise_govde_orani_none_diger_ozellikler_etkilenmez():
    n = 260
    df = _linear_trend_ohlcv(n)
    df["open"] = np.nan
    close = df["close"].to_numpy()
    row = _trade_row(250, 230, 240, 248, close)

    feats = extract_features(row, df)

    assert feats["d_body_range_ratio"] is None
    assert feats["rsi14"] == 100.0  # digger ozellikler ETKILENMEDI


def test_extract_features_yetersiz_gecmiste_none_donen_ozellikler():
    """signal_bar SMA200/ADX warm-up'indan ONCEyse ilgili ozellikler None
    doner, hata FIRLATILMAZ."""
    n = 60
    df = _linear_trend_ohlcv(n)
    close = df["close"].to_numpy()
    row = _trade_row(signal_bar=50, a_bar=30, c_bar=40, d_bar=48, close=close)

    feats = extract_features(row, df)

    assert feats["above_sma200"] is None
    assert feats["price_vs_sma200_pct"] is None


def test_extract_features_signal_bar_disindaki_veri_kullanilmaz_lookahead_yok():
    """`ohlcv_df`nin signal_bar SONRASINDAKI barlari degistirilirse sonuc
    DEGISMEMELI -- extract_features SADECE df.iloc[:signal_bar+1]'i kullanir."""
    n = 260
    df = _linear_trend_ohlcv(n)
    close = df["close"].to_numpy()
    row = _trade_row(200, 180, 190, 198, close)
    feats_before = extract_features(row, df)

    df_mutated = df.copy()
    df_mutated.loc[201:, ["open", "high", "low", "close", "volume"]] = 0.0  # gelecegi boz
    feats_after = extract_features(row, df_mutated)

    assert feats_before == feats_after


def test_extract_features_signal_bar_veriden_uzunsa_hata():
    df = _linear_trend_ohlcv(10)
    close = df["close"].to_numpy()
    row = _trade_row(signal_bar=50, a_bar=1, c_bar=2, d_bar=3, close=np.pad(close, (0, 50)))
    with pytest.raises(ValueError):
        extract_features(row, df)


# ── run_factor_analysis: istatistik motoru (extract_features MONKEYPATCH) ──


_DUMMY_OHLCV = pd.DataFrame(
    {"time": pd.date_range("2024-01-01", periods=5, tz="UTC"), "open": [1.0] * 5,
     "high": [1.0] * 5, "low": [1.0] * 5, "close": [1.0] * 5, "volume": [1.0] * 5}
)


def _synthetic_trades_and_ohlcv(monkeypatch, n: int = 300, seed: int = 7):
    """`extract_features`i monkeypatch ederek `trades_df`nin kendi
    sutunlarindan (ozellik adiyla ayni isimli) degerleri dogrudan doner --
    boylece gercek RSI/MACD/... hesabina gerek kalmadan istatistik motoru
    (FDR/holdout/underpowered) kontrollu bir zemin uzerinde test edilir.

    Kurgu:
      - `rsi14`: kazanan/kaybeden GUCLU ve TUTARLI ayrilir (train VE holdout'ta
        AYNI yonde) -> FDR-anlamli VE holdout-DOGRULANMIS beklenir.
      - `above_sma50` (kategorik): kazananlarda ~%90 1, kaybedenlerde ~%90 0,
        train VE holdout'ta AYNI yonde -> FDR-anlamli VE holdout-DOGRULANMIS.
      - `bb_percent_b`: %95 NaN -> train'de n_win/n_loss < 150 -> UNDERPOWERED.
      - Geri kalan ozellikler: etiketten BAGIMSIZ gurultu -> anlamli OLMAMALI.
    """
    rng = np.random.default_rng(seed)
    label = rng.integers(0, 2, size=n)  # 1=kazanan, 0=kaybeden

    data: dict[str, np.ndarray] = {}
    # Guclu, tutarli surekli etki.
    data["rsi14"] = np.where(label == 1, rng.normal(75, 4, n), rng.normal(25, 4, n))
    # Guclu, tutarli kategorik etki.
    p_win = rng.random(n) < 0.9
    p_loss = rng.random(n) < 0.1
    data["above_sma50"] = np.where(label == 1, p_win.astype(int), p_loss.astype(int))
    # Underpowered: cogunlukla NaN.
    keep = rng.random(n) < 0.05
    data["bb_percent_b"] = np.where(keep, rng.normal(0.5, 0.2, n), np.nan)
    # Kalan tum ozellikler: etiketten bagimsiz gurultu.
    for feat in ALL_FEATURES:
        if feat in data:
            continue
        if feat in abcd_factor_analysis.CATEGORICAL_FEATURES:
            data[feat] = rng.integers(0, 2, size=n)
        else:
            data[feat] = rng.normal(0, 1, n)

    entry_time = pd.date_range("2023-01-01", periods=n, freq="6h", tz="UTC")
    pnl = np.where(label == 1, 100.0, -100.0)

    trades_df = pd.DataFrame(
        {
            "symbol": ["AAA"] * n,
            "tf": ["1D"] * n,
            "currency": ["TRY"] * n,
            "pnl": pnl,
            "entry_time": entry_time,
            **data,
        }
    )

    def _fake_extract_features(trade_row, ohlcv_df):
        return {f: trade_row[f] for f in ALL_FEATURES}

    monkeypatch.setattr(abcd_factor_analysis, "extract_features", _fake_extract_features)
    ohlcv_cache = {("AAA", "1D"): _DUMMY_OHLCV}
    return trades_df, ohlcv_cache


def test_run_factor_analysis_guclu_surekli_etki_fdr_anlamli_ve_holdout_dogrulanir(monkeypatch):
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)

    result = run_factor_analysis(trades_df, ohlcv_cache)

    rsi_row = next(r for r in result["univariate"] if r["feature"] == "rsi14")
    assert rsi_row["significant_train"] is True
    assert rsi_row["fdr_q"] < 0.10
    assert rsi_row["validated"] is True
    assert "dogrulandi" in rsi_row["note"]


def test_run_factor_analysis_guclu_kategorik_etki_fdr_anlamli_ve_holdout_dogrulanir(monkeypatch):
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)

    result = run_factor_analysis(trades_df, ohlcv_cache)

    cat_row = next(r for r in result["univariate"] if r["feature"] == "above_sma50")
    assert cat_row["type"] == "categorical"
    assert cat_row["significant_train"] is True
    assert cat_row["validated"] is True
    assert cat_row["effect_size_name"] is not None and "Cramer" in cat_row["effect_size_name"]


def test_run_factor_analysis_underpowered_etiketi_etki_yok_denmez(monkeypatch):
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)

    result = run_factor_analysis(trades_df, ohlcv_cache)

    bb_row = next(r for r in result["univariate"] if r["feature"] == "bb_percent_b")
    assert bb_row["underpowered"] is True
    assert "underpowered" in bb_row["note"] or "gucu yetersiz" in bb_row["note"]
    assert "etki YOK" not in bb_row["note"] or "denemez" in bb_row["note"]


def test_run_factor_analysis_gurultu_ozellik_fdr_anlamli_degil(monkeypatch):
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)

    result = run_factor_analysis(trades_df, ohlcv_cache)

    noise_row = next(r for r in result["univariate"] if r["feature"] == "cd_duration_bars")
    assert noise_row["significant_train"] is False


def test_run_factor_analysis_label_fn_ile_vindicated_etiketi_kullanilabilir(monkeypatch):
    """`scripts/harmonic_xabcd_vindication_factors.py`nin dayandigi genisleme:
    `label_fn` verilirse `pnl` DEGIL, cagiranin belirttigi ikili sonuc
    kullanilir -- `pnl`'i tersine cevirip `vindicated`i `pnl`den bagimsiz
    (ama orijinal `label` ile AYNI) kuran bir fixture'la, sadece `label_fn`
    ile hala dogru sonuc (rsi14 anlamli+dogrulanmis) alindigini kanitlar."""
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)
    trades_df = trades_df.copy()
    trades_df["vindicated"] = (trades_df["pnl"] > 0).astype(int)
    trades_df["pnl"] = -trades_df["pnl"]  # pnl KASITLI ters -- varsayilan label_fn kullanilsaydi sonuc TERSINE cikardi

    custom_note = "OZEL METODOLOJI NOTU -- vindication testi"
    result = run_factor_analysis(
        trades_df, ohlcv_cache, label_fn=lambda row: int(row["vindicated"]), methodology_note=custom_note
    )

    rsi_row = next(r for r in result["univariate"] if r["feature"] == "rsi14")
    assert rsi_row["significant_train"] is True
    assert rsi_row["validated"] is True
    assert result["methodology_note"] == custom_note
    assert custom_note in format_report(result)


def test_run_factor_analysis_ozel_ozellik_kumesiyle_calisir(monkeypatch):
    """`scripts/momentum_confluence_arastirma.py`nin dayandigi genisleme:
    `feature_names`/`categorical_features`/`extract_features_fn` verilirse
    ABCD'ye ozgu 13 ozellik DEGIL, cagiranin KENDI (A/B/C/D pivotu olmayan
    bir sinyal ailesi icin) kucuk ozellik kumesi kullanilir."""
    n = 200
    rng = np.random.default_rng(11)
    label = rng.integers(0, 2, n)
    custom_feature = np.where(label == 1, rng.normal(10, 1, n), rng.normal(0, 1, n))
    trades_df = pd.DataFrame(
        {
            "symbol": ["AAA"] * n,
            "tf": ["1D"] * n,
            "currency": ["TRY"] * n,
            "pnl": np.where(label == 1, 100.0, -100.0),
            "entry_time": pd.date_range("2023-01-01", periods=n, freq="6h", tz="UTC"),
            "ozel_ozellik": custom_feature,
        }
    )

    def _fake_extract(trade_row, ohlcv_df):
        return {"ozel_ozellik": trade_row["ozel_ozellik"]}

    result = run_factor_analysis(
        trades_df,
        {("AAA", "1D"): _DUMMY_OHLCV},
        feature_names=["ozel_ozellik"],
        categorical_features=[],
        extract_features_fn=_fake_extract,
    )

    assert len(result["univariate"]) == 1
    row = result["univariate"][0]
    assert row["feature"] == "ozel_ozellik"
    assert row["significant_train"] is True
    assert row["validated"] is True
    assert result["logistic_regression"]["features_used"] == ["ozel_ozellik"]


def test_run_factor_analysis_tamamen_eksik_ozellik_lojistik_regresyonu_engellemez(monkeypatch):
    """CANLI HATA + DUZELTME regresyon testi (harmonic_xabcd_vindication_
    factors.py kosusu, 2026-08-18): `cd_ratio_dev` gibi bir ozellik TRAIN'de
    HICBIR satirda dolu degilse (hepsi None), eski kod `dropna()` yuzunden
    TUM satirlari silip n=0 ile 'yeterli veri yok' donuyordu -- digger 10
    ozellik dolu olsa BILE. Simdi o ozellik BASTAN cikarilmali, model geri
    kalan ozelliklerle CALISMALI."""
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)
    trades_df = trades_df.copy()
    trades_df["cd_ratio_dev"] = np.nan  # TAMAMEN eksik -- eski davranista tum modeli cokertiyordu
    # Fixture'daki `bb_percent_b` KASITLI %95 eksik (underpowered testi icin) --
    # bu test SADECE "tamamen eksik ozellik" senaryosunu izole etmek istiyor,
    # o yuzden bu AYRI/beklenen kismi-eksiklik konfuzu doldurulur.
    rng = np.random.default_rng(7)
    trades_df["bb_percent_b"] = rng.normal(0.5, 0.2, len(trades_df))

    result = run_factor_analysis(trades_df, ohlcv_cache)

    logreg = result["logistic_regression"]
    # Odak: yapisal duzeltme (tamamen-eksik ozellik BASTAN cikarilip n=0'a
    # DUSMEMELI) -- gercek MLE yakinsamasi (guclu sentetik ayrisma yuzunden
    # statsmodels'in kendi numerik durumu) bu testin KAPSAMI DISINDA.
    assert "cd_ratio_dev" in logreg["features_excluded_all_nan"]
    assert "cd_ratio_dev" not in logreg["features_used"]
    assert logreg["n_used"] >= 150  # cd_ratio_dev cikarilmadan ONCE n=0 donuyordu -- artik cogunluk kaliyor
    assert "yeterli tam-veri satiri yok" not in logreg["note"]


def test_run_factor_analysis_kronolojik_split_70_30():
    n = 200
    trades_df = pd.DataFrame(
        {
            "symbol": ["AAA"] * n,
            "tf": ["1D"] * n,
            "currency": ["TRY"] * n,
            "pnl": [100.0] * n,
            "entry_time": pd.date_range("2023-01-01", periods=n, freq="1D", tz="UTC"),
        }
    )

    import unittest.mock as mock

    with mock.patch.object(abcd_factor_analysis, "extract_features", return_value={f: 0.0 for f in ALL_FEATURES}):
        result = run_factor_analysis(trades_df, {("AAA", "1D"): _DUMMY_OHLCV})

    assert result["n_train"] == round(n * 0.7)
    assert result["n_total"] == n
    assert result["n_train"] + result["n_holdout"] == n


def test_run_factor_analysis_birden_fazla_para_birimi_firlatir():
    trades_df = pd.DataFrame({"currency": ["TRY", "USD"], "symbol": ["A", "A"], "tf": ["1D", "1D"]})
    with pytest.raises(ValueError):
        run_factor_analysis(trades_df, {})


def test_run_factor_analysis_bos_trades_df_hata_alaniyla_doner():
    result = run_factor_analysis(pd.DataFrame(columns=["currency", "symbol", "tf", "pnl", "entry_time"]), {})
    assert result["n_total"] == 0
    assert "error" in result


def test_run_factor_analysis_eksik_ohlcv_cache_sessizce_atlar():
    n = 5
    trades_df = pd.DataFrame(
        {
            "symbol": ["AAA"] * n,
            "tf": ["1D"] * n,
            "currency": ["TRY"] * n,
            "pnl": [100.0] * n,
            "entry_time": pd.date_range("2023-01-01", periods=n, freq="1D", tz="UTC"),
        }
    )
    result = run_factor_analysis(trades_df, {})  # ohlcv_cache BOS -- hicbir (symbol, tf) yok
    assert result["n_total"] == 0
    assert result["n_skipped"] == n


# ── format_report: crash etmez, iliskisel dil iceriyor ────────────────────


def test_format_report_hatali_sonucta_crashsiz_hata_metni_uretir():
    result = {"error": "test hatasi", "methodology_note": "not"}
    report = format_report(result)
    assert "HATA" in report
    assert "test hatasi" in report


def test_format_report_normal_sonucta_nedensellik_yasagi_metni_icerir(monkeypatch):
    trades_df, ohlcv_cache = _synthetic_trades_and_ohlcv(monkeypatch)
    result = run_factor_analysis(trades_df, ohlcv_cache)
    report = format_report(result)

    assert "nedensellik" in report.lower() or "iliskisel" in report.lower() or "association" in report.lower()
    assert "rsi14" in report
    assert "Lojistik regresyon" in report
