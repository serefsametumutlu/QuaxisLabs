"""AB=CD basari faktoru analizi (Faz 8) -- TAMAMLANMIS (D onaylanmis,
backtest edilmis) islemlerden kazananlari kaybedenlerden ayiran ORTAK
faktorleri (hacim, RSI, MACD, mum yapisi, destek/direnc, trend/ADX/
Bollinger) arastirir.

Metodoloji kaynagi: `quant-mathematician` agent denetiminin ciktisi (bkz.
gorev talimatinin "METODOLOJI" bolumu) -- bu modul o metodolojiyi BIREBIR
uygular, yeniden tasarlamaz.

Mimari kararlar: `docs/spec/spec_abcd_mimari_kararlar.md`.

  Karar 1 -- Modul izolasyonu: `abcd_pattern.py`/`abcd_backtest.py` ile AYNI
  ilke -- bu modul de `src/analysis/`in genel felsefesinden (skorsuz/
  sinyalsiz) BILINCLI bir sapmadir; kazanan/kaybeden ILISKISEL analizi
  uretir, YONLU AL/SAT sinyali/skor DEGIL. Bir istisnadir, emsal DEGILDIR.

  Karar 2 -- Decimal istisnasi: `abcd_pattern.py`/`abcd_backtest.py`/
  `abcd_data.py` ile AYNI gerekceyle (ayni float64 sinyal/fiyat zincirinin
  devami) bu modul de TAMAMEN float + pandas/numpy/scipy/statsmodels
  kullanir. Float deger BURADAN hicbir zaman Decimal tipli dataclass'lara/
  `scorer.py`'ye/`calculator.py`'ye SIZMAZ.

Katman disiplini: bu modul `src.fetchers.*`/`src.db.*` HICBIR modulu import
ETMEZ (`abcd_pattern.py` ile AYNI ilke) -- girdi olarak zaten cekilmis
`trades_df` (bkz. `abcd_backtest.collect_trades`) VE `ohlcv_cache` (zaten
cekilmis OHLCV DataFrame'lerinin sozlugu) alir, hicbir ag/DB I/O yapmaz.

## Neden statsmodels (sklearn DEGIL) -- lojistik regresyon karari

Metodoloji "yorumlanabilir lojistik regresyon (katsayi+Wald p+%95 CI)" ister.
`sklearn.linear_model.LogisticRegression` bunlari DOGRUDAN saglamaz -- Wald
p-degeri/CI icin Hessian'dan manuel standart hata hesaplamak gerekir, bu hem
gereksiz kod hem sayisal kirilganlik riski tasir. `statsmodels.Logit` bu
degerleri (`.params`, `.bse`, `.tvalues`, `.pvalues`, `.conf_int()`) DOGRUDAN
verir -- proje venv'inde zaten mevcut, `requirements.txt`'e eklendi (bkz. o
dosyadaki gerekce yorumu). Bu yuzden statsmodels tercih edildi, sklearn
KULLANILMADI.

## Kapsam siniri -- TEK para birimi

`run_factor_analysis`, `trades_df`de BIRDEN FAZLA para birimi (`currency`)
bulunmasina IZIN VERMEZ (ValueError firlatir). Gerekce: RSI/MACD/ADX/
Bollinger gibi ozellikler fiyat SERISINE baglidir -- USD-payda grafiginde
`detect()` YENIDEN calistirildigi icin (spec Karar/"TL vs USD ayrimi") aynen
TL/USD islemlerini AYNI `ohlcv_cache[(symbol, tf)]` anahtariyla karistirmak
yanlis gostergeler uretir. Cagiran taraf her para birimini AYRI cagirmalidir
(bilincli bir kapsam daraltmasi, eksiklik DEGIL).

## 11 aday ozellik -> 13 istatistiksel sutun

Metodolojideki "11 aday ozellik" listesi kavramsal gruplardir; MACD (isaret +
egim) ve trend konumu (ikili + surekli) her biri IKI olculebilir sutun
uretir, toplam 13 istatistiksel sutun (`ALL_FEATURES`) elde edilir.

## VIF / bc_ratio notu

Metodoloji "cd_ratio hassasiyeti ile bc_ratio arasinda yuksek korelasyon
varsa biri elenir" der, ama 11'lik aday listesi `bc_ratio`'yu DOGRUDAN
icermiyor (sadece `cd_ratio_dev` = |cd_ratio-1|). Bu yuzden bc_ratio-ozel bir
kontrol yerine GENEL bir VIF esigi (>10) TUM model ozelliklerine iteratif
uygulanir -- ayni coklu-dogrusallik disiplininin en yakin GUVENLI
uygulamasi.
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as scipy_stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.analysis.abcd_pattern import atr_wilder

# ── esik/sabitler (metodolojiden BIREBIR) ──────────────────────────────────

MIN_GROUP_N_TRAIN = 150  # train'de win VE loss HER BIRI bu sayinin altindaysa "underpowered"
FDR_Q = 0.10  # Benjamini-Hochberg FDR esigi (Bonferroni DEGIL)
HOLDOUT_ALPHA = 0.05  # holdout dogrulama icin duzeltmesiz p esigi
TARGET_TOTAL_N = 400  # metodolojinin "n>=400-500" hedefinin ALT siniri (blocker DEGIL, etiket)
VIF_THRESHOLD = 10.0

CONTINUOUS_FEATURES = [
    "rsi14",
    "macd_hist_slope",
    "volume_ratio",
    "atr_norm_cd_speed",
    "cd_ratio_dev",
    "d_proximity_50bar",
    "cd_duration_bars",
    "d_body_range_ratio",
    "price_vs_sma200_pct",
    "adx14",
    "bb_percent_b",
]
CATEGORICAL_FEATURES = ["macd_hist_sign", "above_sma50", "above_sma200"]
ALL_FEATURES = CONTINUOUS_FEATURES + CATEGORICAL_FEATURES


# ── float/pandas gosterge yardimcilari (Karar 2 istisnasi, Pine parity
#    ZORUNLU DEGIL -- bu modulun kendi, acikca belgelenmis standart
#    formulleridir; `technical.py`nin Decimal mantigi KOPYALANMAZ, sadece
#    formul ilkesi referans alinir) ─────────────────────────────────────────


def _wilder_rma(values: np.ndarray, length: int) -> np.ndarray:
    """`abcd_pattern.atr_wilder`deki RMA seed+smoothing mantiginin genel
    (TR disinda DM/DX icin de kullanilabilen) hali."""
    n = len(values)
    out = np.full(n, np.nan)
    if n < length:
        return out
    out[length - 1] = values[:length].mean()
    alpha = 1.0 / length
    for i in range(length, n):
        out[i] = out[i - 1] + (values[i] - out[i - 1]) * alpha
    return out


def _rsi_wilder(close: np.ndarray, length: int = 14) -> np.ndarray:
    """Standart Wilder RSI: ilk `length` degisimin duz ortalamasiyla seed,
    sonrasi Wilder smoothing -- `atr_wilder`in RMA mantigiyla AYNI ilke."""
    n = len(close)
    rsi = np.full(n, np.nan)
    if n <= length:
        return rsi

    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    avg_gain = np.full(n, np.nan)
    avg_loss = np.full(n, np.nan)
    avg_gain[length] = gain[:length].mean()
    avg_loss[length] = loss[:length].mean()
    alpha = 1.0 / length
    for i in range(length + 1, n):
        avg_gain[i] = avg_gain[i - 1] + (gain[i - 1] - avg_gain[i - 1]) * alpha
        avg_loss[i] = avg_loss[i - 1] + (loss[i - 1] - avg_loss[i - 1]) * alpha

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = np.where(avg_loss == 0, 100.0, rsi)
    rsi = np.where(np.isnan(avg_gain), np.nan, rsi)
    return rsi


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    """Standart (ilk deger ile seed edilen) ussel hareketli ortalama --
    Pine-parity zorunlulugu YOK (bu veri Pine'a hic gitmiyor), bu yuzden
    proje-ozel/basit bir tanim kullanilir."""
    n = len(values)
    out = np.full(n, np.nan)
    if n == 0:
        return out
    alpha = 2.0 / (span + 1)
    out[0] = values[0]
    for i in range(1, n):
        out[i] = out[i - 1] + (values[i] - out[i - 1]) * alpha
    return out


def _macd_hist(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
    macd = _ema(close, fast) - _ema(close, slow)
    signal_line = _ema(macd, signal)
    return macd - signal_line


def _adx_wilder(df: pd.DataFrame, length: int = 14) -> np.ndarray:
    """Standart Wilder ADX yaklasimi (+DM/-DM/TR Wilder-smoothed, DX'in
    Wilder-smoothed hali). Pine-parity ZORUNLU DEGIL -- kaba/standart bir
    yaklasimdir, sadece lojistik regresyon/istatistik girdisi icindir."""
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    n = len(df)

    tr = np.empty(n)
    plus_dm = np.zeros(n)
    minus_dm = np.zeros(n)
    if n > 0:
        tr[0] = high[0] - low[0]
    for i in range(1, n):
        up_move = high[i] - high[i - 1]
        down_move = low[i - 1] - low[i]
        plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

    tr_s = _wilder_rma(tr, length)
    plus_dm_s = _wilder_rma(plus_dm, length)
    minus_dm_s = _wilder_rma(minus_dm, length)

    with np.errstate(divide="ignore", invalid="ignore"):
        plus_di = 100.0 * plus_dm_s / tr_s
        minus_di = 100.0 * minus_dm_s / tr_s
        dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

    dx_filled = np.nan_to_num(dx, nan=0.0)
    adx = _wilder_rma(dx_filled, length)
    # DX ilk `length` barda tanimsiz oldugundan ADX de ilk ~2*length-1
    # barda anlamsizdir -- acikca NaN birakilir (sessizce 0 sizdirilmaz).
    adx = np.where(np.arange(n) < 2 * length - 1, np.nan, adx)
    return adx


def _bollinger_percent_b(close: np.ndarray, length: int = 20, num_std: float = 2.0) -> np.ndarray:
    s = pd.Series(close)
    mid = s.rolling(length).mean()
    std = s.rolling(length).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = upper - lower
    pb = (s - lower) / width
    pb = pb.where(width != 0, np.nan)
    return pb.to_numpy(dtype=float)


# ── ozellik cikarimi ────────────────────────────────────────────────────────


def extract_features(trade_row: pd.Series | dict, ohlcv_df: pd.DataFrame) -> dict[str, float | int | None]:
    """`trade_row` (bkz. `abcd_backtest.collect_trades` cikti satiri -- `sig_*`
    alanlariyla birlikte) ve o islemin ait oldugu `ohlcv_df` (ayni sembol/tf/
    para-birimi icin TAM fiyat serisi) icin 13 istatistiksel ozelligi hesaplar.

    LOOK-AHEAD YOK: hesaplama `ohlcv_df.iloc[: signal_bar + 1]`e (D onay bari
    ve ONCESI, SADECE) kesilerek yapilir -- gostergelerin kendisi zaten
    nedensel/rolling olsa da (gelecek bara bakmazlar), bu kesme ekstra bir
    guvenlik katmanidir; ileride bir gosterge yanlislikla `.shift(-1)` gibi
    ileri-bakan bir sey icerse bile bu fonksiyon disariya sizdirmaz.

    `open` NaN ise (bu projede `abcd_data.py` gercek yfinance acilisi
    dondugu icin pratikte olmaz, ama savunmaci -- bkz. spec Karar 3)
    `d_body_range_ratio` `None` doner, digger ozellikler ETKILENMEZ.

    Donen sozlukteki her deger ya `float`/`int` ya da `None` (hesaplanamadi --
    yetersiz gecmis/sifira bolme/NaN girdi). `None` degerler cagiran
    (`run_factor_analysis`) tarafinda istatistiksel testten ONCE `dropna()`
    ile elenir, asla 0/varsayilan bir sayiyla DOLDURULMAZ.
    """
    row = trade_row if isinstance(trade_row, dict) else trade_row.to_dict()

    signal_bar = int(row["sig_signal_bar"])
    c_bar = int(row["sig_c_bar"])
    d_bar = int(row["sig_d_bar"])
    c_price = float(row["sig_c_price"])
    d_price = float(row["sig_d_price"])
    cd_ratio_raw = row.get("sig_cd_ratio")
    cd_ratio = float(cd_ratio_raw) if cd_ratio_raw is not None else float("nan")

    df = ohlcv_df.iloc[: signal_bar + 1].reset_index(drop=True)
    n = len(df)
    if n <= signal_bar:
        raise ValueError(
            f"ohlcv_df, signal_bar={signal_bar} icin yeterli veri icermiyor (n={n}) -- "
            "trade'in kaynagi olan sinyal, verilen OHLCV serisiyle uyumsuz."
        )

    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)
    open_ = df["open"].to_numpy(dtype=float) if "open" in df.columns else np.full(n, np.nan)

    features: dict[str, float | int | None] = {}

    # 1. RSI(14) @ signal_bar
    rsi = _rsi_wilder(close, 14)
    features["rsi14"] = float(rsi[signal_bar]) if not np.isnan(rsi[signal_bar]) else None

    # 2. MACD histogram isareti + egimi @ signal_bar
    hist = _macd_hist(close)
    h_now = hist[signal_bar]
    if signal_bar >= 3 and not np.isnan(h_now) and not np.isnan(hist[signal_bar - 3]):
        features["macd_hist_sign"] = int(np.sign(h_now))
        features["macd_hist_slope"] = float(h_now - hist[signal_bar - 3])
    else:
        features["macd_hist_sign"] = None
        features["macd_hist_slope"] = None

    # 3. Hacim orani: mean(volume[c_bar:d_bar+1]) / mean(volume[d_bar-20:d_bar])
    seg_cd = volume[c_bar : d_bar + 1]
    base_start = max(d_bar - 20, 0)
    seg_base = volume[base_start:d_bar]
    if len(seg_cd) > 0 and len(seg_base) > 0 and seg_base.mean() > 0:
        features["volume_ratio"] = float(seg_cd.mean() / seg_base.mean())
    else:
        features["volume_ratio"] = None

    # 4. ATR-normalize C->D hizi
    atr14 = atr_wilder(df, 14)
    atr_at_signal = atr14[signal_bar]
    cd_bars = d_bar - c_bar
    if not np.isnan(atr_at_signal) and atr_at_signal > 0 and cd_bars > 0:
        features["atr_norm_cd_speed"] = float(abs(d_price - c_price) / (atr_at_signal * cd_bars))
    else:
        features["atr_norm_cd_speed"] = None

    # 5. |cd_ratio - 1.0| (Fibonacci hassasiyeti)
    features["cd_ratio_dev"] = float(abs(cd_ratio - 1.0)) if not math.isnan(cd_ratio) else None

    # 6. D'nin 50-bar high/low'a yakinligi
    win_start = max(d_bar - 50, 0)
    if d_bar > win_start:
        window_low = float(low[win_start:d_bar].min())
        window_high = float(high[win_start:d_bar].max())
        rng = window_high - window_low
        features["d_proximity_50bar"] = float((d_price - window_low) / rng) if rng > 0 else None
    else:
        features["d_proximity_50bar"] = None

    # 7. C->D pattern suresi
    features["cd_duration_bars"] = int(cd_bars)

    # 8. D barinin mum govde/aralik orani (open NaN ise None -- spec Karar 3)
    o_d, h_d, l_d, c_d = open_[d_bar], high[d_bar], low[d_bar], close[d_bar]
    if np.isnan(o_d) or (h_d - l_d) <= 0:
        features["d_body_range_ratio"] = None
    else:
        features["d_body_range_ratio"] = float(abs(c_d - o_d) / (h_d - l_d))

    # 9. Trend konumu: SMA50/SMA200 ustunde/altinde (ikili) + surekli %
    sma50 = pd.Series(close).rolling(50).mean().to_numpy()
    sma200 = pd.Series(close).rolling(200).mean().to_numpy()
    s50, s200 = sma50[signal_bar], sma200[signal_bar]
    features["above_sma50"] = int(close[signal_bar] > s50) if not np.isnan(s50) else None
    features["above_sma200"] = int(close[signal_bar] > s200) if not np.isnan(s200) else None
    features["price_vs_sma200_pct"] = (
        float((close[signal_bar] - s200) / s200 * 100.0) if (not np.isnan(s200) and s200 != 0) else None
    )

    # 10. ADX(14) @ signal_bar
    adx = _adx_wilder(df, 14)
    features["adx14"] = float(adx[signal_bar]) if not np.isnan(adx[signal_bar]) else None

    # 11. Bollinger %B @ signal_bar
    bb = _bollinger_percent_b(close, 20, 2.0)
    features["bb_percent_b"] = float(bb[signal_bar]) if not np.isnan(bb[signal_bar]) else None

    return features


# ── istatistik motoru ────────────────────────────────────────────────────


def _univariate_test(df: pd.DataFrame, feature: str, is_categorical: bool, min_group_n_train: int) -> dict[str, Any]:
    """Tek bir ozellik icin kazanan(label=1)/kaybeden(label=0) grup testi.
    Surekli: Mann-Whitney U + rank-biserial etki buyuklugu.
    Kategorik: ki-kare (beklenen hucre<5 varsa Fisher exact'a duser) + Cramer's V.
    """
    sub = df[[feature, "label"]].dropna()
    win = sub.loc[sub["label"] == 1, feature]
    loss = sub.loc[sub["label"] == 0, feature]
    n_win, n_loss = len(win), len(loss)
    underpowered = (n_win < min_group_n_train) or (n_loss < min_group_n_train)

    result: dict[str, Any] = {
        "feature": feature,
        "type": "categorical" if is_categorical else "continuous",
        "n_win": n_win,
        "n_loss": n_loss,
        "underpowered": underpowered,
        "p_train": None,
        "effect_size": None,
        "effect_size_name": None,
        "summary_win": None,
        "summary_loss": None,
    }
    if n_win == 0 or n_loss == 0:
        return result

    if is_categorical:
        table = pd.crosstab(sub[feature], sub["label"])
        result["summary_win"] = float(win.mean())
        result["summary_loss"] = float(loss.mean())
        if table.shape[0] < 2 or table.shape[1] < 2:
            return result
        try:
            chi2, p_chi2, _dof, expected = scipy_stats.chi2_contingency(table.to_numpy())
        except ValueError:
            return result
        if table.shape == (2, 2) and (expected < 5).any():
            _, p = scipy_stats.fisher_exact(table.to_numpy())
            test_name = "fisher_exact"
        else:
            p, test_name = p_chi2, "chi2"
        total_n = int(table.to_numpy().sum())
        r, c = table.shape
        cramers_v = math.sqrt(chi2 / (total_n * (min(r, c) - 1))) if total_n > 0 and min(r, c) > 1 else float("nan")
        result["p_train"] = float(p)
        result["effect_size"] = float(cramers_v) if not math.isnan(cramers_v) else None
        result["effect_size_name"] = f"Cramer's V ({test_name})"
    else:
        result["summary_win"] = float(win.mean())
        result["summary_loss"] = float(loss.mean())
        try:
            u_stat, p = scipy_stats.mannwhitneyu(win, loss, alternative="two-sided")
        except ValueError:
            return result
        rank_biserial = 1.0 - (2.0 * float(u_stat)) / (n_win * n_loss)
        result["p_train"] = float(p)
        result["effect_size"] = float(rank_biserial)
        result["effect_size_name"] = "rank-biserial r"

    return result


def _direction_matches(train_result: dict[str, Any], holdout_result: dict[str, Any]) -> bool:
    """Train VE holdout'ta kazanan-ortalama - kaybeden-ortalama farkinin
    AYNI isarette olup olmadigini kontrol eder (metodolojinin "ayni yon"
    dogrulama sarti)."""
    tw, tl = train_result["summary_win"], train_result["summary_loss"]
    hw, hl = holdout_result["summary_win"], holdout_result["summary_loss"]
    if tw is None or tl is None or hw is None or hl is None:
        return False
    return (tw - tl > 0) == (hw - hl > 0)


def _fit_logistic_regression(train_df: pd.DataFrame) -> dict[str, Any]:
    """Yorumlanabilir lojistik regresyon (bkz. modul-ust notu: neden
    statsmodels). Standardize edilmis (z-skor) ozellikler kullanilir; VIF>10
    olan ozellik iteratif olarak modelden CIKARILIR (coklu-dogrusallik)."""
    sub = train_df[ALL_FEATURES + ["label"]].dropna()
    if len(sub) < 30 or sub["label"].nunique() < 2:
        return {
            "converged": False,
            "note": f"lojistik regresyon icin yeterli tam-veri satiri yok (n={len(sub)}, min 30 + her iki sinif gerekir).",
            "coefficients": [],
            "vif": {},
            "features_used": [],
            "features_dropped_vif": [],
            "n_used": len(sub),
        }

    X = sub[ALL_FEATURES].astype(float)
    y = sub["label"].astype(float)

    stds = X.std(ddof=0).replace(0, 1.0)
    means = X.mean()
    X_std = (X - means) / stds

    features_used = list(ALL_FEATURES)
    dropped: list[tuple[str, float]] = []
    vifs: dict[str, float] = {}

    while len(features_used) > 1:
        design = sm.add_constant(X_std[features_used], has_constant="add")
        vifs = {
            col: float(variance_inflation_factor(design.to_numpy(), i))
            for i, col in enumerate(design.columns)
            if col != "const"
        }
        worst_feature, worst_vif = max(vifs.items(), key=lambda kv: kv[1])
        if worst_vif > VIF_THRESHOLD:
            dropped.append((worst_feature, worst_vif))
            features_used.remove(worst_feature)
            continue
        break

    design = sm.add_constant(X_std[features_used], has_constant="add")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.Logit(y, design).fit(disp=0)
    except Exception as exc:  # yakinsama/mukemmel-ayrisma hatasi -- coksmesin, etiketlensin
        return {
            "converged": False,
            "note": f"lojistik regresyon yakinsamadi/basarisiz: {exc}",
            "coefficients": [],
            "vif": vifs,
            "features_used": features_used,
            "features_dropped_vif": dropped,
            "n_used": len(sub),
        }

    conf = model.conf_int(alpha=0.05)
    coefficients = [
        {
            "feature": name,
            "coef": float(model.params[name]),
            "std_err": float(model.bse[name]),
            "wald_z": float(model.tvalues[name]),
            "p_value": float(model.pvalues[name]),
            "ci_low": float(conf.loc[name, 0]),
            "ci_high": float(conf.loc[name, 1]),
        }
        for name in design.columns
    ]

    converged = bool(getattr(model, "mle_retvals", {}).get("converged", True))
    return {
        "converged": converged,
        "note": "standardize edilmis (z-skor) ozellikler; kategorik ozellikler 0/1 kodlu.",
        "coefficients": coefficients,
        "vif": vifs,
        "features_used": features_used,
        "features_dropped_vif": dropped,
        "n_used": len(sub),
    }


def run_factor_analysis(
    trades_df: pd.DataFrame,
    ohlcv_cache: dict[tuple[str, str], pd.DataFrame],
    *,
    min_group_n_train: int = MIN_GROUP_N_TRAIN,
    fdr_q: float = FDR_Q,
    holdout_alpha: float = HOLDOUT_ALPHA,
) -> dict[str, Any]:
    """Metodolojinin TUM disiplinini (kronolojik split, FDR, holdout
    dogrulama, underpowered etiketleme, lojistik regresyon, nedensellik-
    yasagi) uygulayan sonuc sozlugunu doner.

    `trades_df`: `abcd_backtest.collect_trades` cikti sekli (`sig_*` alanlari
    + `symbol`/`tf`/`currency`/`pnl` iceren duz DataFrame). TEK bir `currency`
    icermelidir (bkz. modul-ust notu "Kapsam siniri") -- birden fazlaysa
    `ValueError` firlatilir.

    `ohlcv_cache`: `(symbol, tf) -> pd.DataFrame` -- her trade'in ait oldugu
    TAM fiyat serisi (features `extract_features` icinde `signal_bar`e kadar
    kesilir, bkz. o fonksiyonun look-ahead notu). Eksik anahtar/yetersiz
    veri o trade'i SESSIZCE atlar (hata FIRLATMAZ), atlanan sayisi
    `n_skipped` alaninda raporlanir.

    Donen sozluk hicbir zaman "etki yok" iddiasi icermez -- yetersiz
    orneklemli ozellikler "underpowered" etiketlenir, train'de anlamli ama
    holdoutta dogrulanmayanlar "muhtemelen sans" etiketiyle SONUCTA KALIR
    (silinmez).
    """
    if trades_df.empty:
        return {
            "n_total": 0, "n_train": 0, "n_holdout": 0, "n_skipped": 0,
            "error": "trades_df bos -- analiz yapilamadi.",
            "univariate": [], "logistic_regression": None,
            "methodology_note": _METHODOLOGY_NOTE,
        }

    currencies = trades_df["currency"].dropna().unique()
    if len(currencies) > 1:
        raise ValueError(
            "run_factor_analysis TEK bir para birimi bekler -- trades_df birden fazla "
            f"currency icierdi: {sorted(currencies)!r}. RSI/MACD/ADX/Bollinger gibi ozellikler "
            "fiyat serisine baglidir; TL/USD islemlerini ayni ohlcv_cache anahtariyla karistirmak "
            "yanlis gostergeler uretir (bkz. modul-ust notu 'Kapsam siniri'). Her para birimini "
            "AYRI cagirin."
        )

    rows: list[dict[str, Any]] = []
    skipped = 0
    for _, trade_row in trades_df.iterrows():
        key = (trade_row["symbol"], trade_row["tf"])
        ohlcv_df = ohlcv_cache.get(key)
        if ohlcv_df is None or ohlcv_df.empty:
            skipped += 1
            continue
        try:
            feats = extract_features(trade_row, ohlcv_df)
        except (ValueError, KeyError, TypeError):
            skipped += 1
            continue
        feats["label"] = 1 if trade_row["pnl"] > 0 else 0
        feats["entry_time"] = trade_row["entry_time"]
        rows.append(feats)

    feat_df = pd.DataFrame(rows)
    n_total = len(feat_df)
    if n_total == 0:
        return {
            "n_total": 0, "n_train": 0, "n_holdout": 0, "n_skipped": skipped,
            "error": "hicbir islem icin ozellik hesaplanamadi (ohlcv_cache eksik/yetersiz veri).",
            "univariate": [], "logistic_regression": None,
            "methodology_note": _METHODOLOGY_NOTE,
        }

    feat_df = feat_df.sort_values("entry_time").reset_index(drop=True)
    split_idx = int(round(n_total * 0.7))
    split_idx = min(max(split_idx, 1), n_total - 1) if n_total > 1 else n_total
    train_df = feat_df.iloc[:split_idx]
    holdout_df = feat_df.iloc[split_idx:]
    split_time = feat_df["entry_time"].iloc[split_idx - 1] if split_idx > 0 else None

    univariate: list[dict[str, Any]] = []
    train_pvals: list[float] = []
    train_pval_idx: list[int] = []
    for i, feature in enumerate(ALL_FEATURES):
        result = _univariate_test(train_df, feature, feature in CATEGORICAL_FEATURES, min_group_n_train)
        univariate.append(result)
        if result["p_train"] is not None and not math.isnan(result["p_train"]):
            train_pvals.append(result["p_train"])
            train_pval_idx.append(i)

    for r in univariate:
        r["fdr_q"] = None
        r["significant_train"] = False

    if train_pvals:
        qvals = scipy_stats.false_discovery_control(np.array(train_pvals), method="bh")
        for idx, q in zip(train_pval_idx, qvals):
            univariate[idx]["fdr_q"] = float(q)
            univariate[idx]["significant_train"] = bool(q < fdr_q)

    for result in univariate:
        feature = result["feature"]
        if result["significant_train"]:
            holdout_result = _univariate_test(
                holdout_df, feature, feature in CATEGORICAL_FEATURES, min_group_n_train=0
            )
            result["p_holdout"] = holdout_result["p_train"]
            validated = (
                holdout_result["p_train"] is not None
                and not math.isnan(holdout_result["p_train"])
                and holdout_result["p_train"] < holdout_alpha
                and _direction_matches(result, holdout_result)
            )
            result["validated"] = validated
            result["note"] = (
                "holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05)"
                if validated
                else "muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi)"
            )
        else:
            result["p_holdout"] = None
            result["validated"] = None
            result["note"] = (
                "gucu yetersiz (underpowered) -- etki YOK denemez, sadece orneklem kucuk"
                if result["underpowered"]
                else "train'de FDR (q<%.2f) esigini gecmedi" % fdr_q
            )

    logreg = _fit_logistic_regression(train_df)

    return {
        "n_total": n_total,
        "n_train": len(train_df),
        "n_holdout": len(holdout_df),
        "n_skipped": skipped,
        "split_time": split_time,
        "underpowered_overall": n_total < TARGET_TOTAL_N,
        "target_total_n": TARGET_TOTAL_N,
        "univariate": univariate,
        "logistic_regression": logreg,
        "methodology_note": _METHODOLOGY_NOTE,
    }


_METHODOLOGY_NOTE = (
    "Butun bulgular ILISKISEL dildedir, NEDENSELLIK iddia edilmez -- 'X ozelligi basariyi "
    "artirir' turu ifadeler YASAKTIR; sadece 'kazananlarda X ile birlikte gorulur, n=.., p=.., "
    "FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir."
)


# ── rapor formatlama ─────────────────────────────────────────────────────


def _fmt(value: float | None, spec: str = "{:.4g}") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    return spec.format(value)


def format_report(result: dict[str, Any]) -> str:
    """Metodolojideki rapor formatini (satir basina: ozellik, kazanan/
    kaybeden ortalama+n, p, FDR q, etki buyuklugu, holdout durumu) BIREBIR
    uygulayan Markdown metni doner. NEDENSELLIK dili KULLANILMAZ."""
    lines: list[str] = ["# AB=CD Basari Faktoru Analizi\n"]
    lines.append(f"\n> {result.get('methodology_note', _METHODOLOGY_NOTE)}\n")

    if result.get("error"):
        lines.append(f"\n**HATA:** {result['error']}\n")
        return "".join(lines)

    lines.append(
        f"\n- Toplam islem: {result['n_total']} (train={result['n_train']}, "
        f"holdout={result['n_holdout']}, ozellik-hesaplanamadigi-icin-atlanan={result.get('n_skipped', 0)})\n"
    )
    if result.get("split_time") is not None:
        lines.append(f"- Kronolojik split esigi (giris zamani): {result['split_time']}\n")
    if result.get("underpowered_overall"):
        lines.append(
            f"\n> **UYARI:** toplam n={result['n_total']}, hedef n>={result['target_total_n']}'in ALTINDA -- "
            "bulgular erken/deneme niteliginde, kesin karar icin daha buyuk orneklem gerekir.\n"
        )

    lines.append("\n## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)\n")
    lines.append(
        "\n| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | "
        "p (train) | FDR q | Etki buyuklugu | Holdout durumu |\n"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|\n")
    for r in result.get("univariate", []):
        eff = f"{_fmt(r['effect_size'], '{:.3f}')} ({r['effect_size_name']})" if r["effect_size_name"] else "N/A"
        underpowered_flag = " *(GUCU YETERSIZ)*" if r["underpowered"] else ""
        lines.append(
            f"| {r['feature']} | {r['type']} | {r['n_win']}/{r['n_loss']}{underpowered_flag} | "
            f"{_fmt(r['summary_win'])} | {_fmt(r['summary_loss'])} | {_fmt(r['p_train'])} | "
            f"{_fmt(r.get('fdr_q'))} | {eff} | {r.get('note', '')} |\n"
        )

    logreg = result.get("logistic_regression")
    lines.append("\n## Lojistik regresyon (yorumlanabilir, standardize)\n")
    if not logreg or not logreg.get("converged"):
        note = logreg.get("note") if logreg else "hesaplanamadi (girdi yok)"
        lines.append(f"\n_Model yakinsamadi/uygulanamadi: {note}_\n")
    else:
        if logreg.get("features_dropped_vif"):
            dropped_str = ", ".join(f"{f} (VIF={v:.1f})" for f, v in logreg["features_dropped_vif"])
            lines.append(f"\n- VIF>{VIF_THRESHOLD:.0f} nedeniyle modelden cikarilan: {dropped_str}\n")
        lines.append(f"\n- Kullanilan ozellik sayisi: {len(logreg['features_used'])}, n={logreg['n_used']}\n")
        lines.append("\n| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |\n")
        lines.append("|---|---|---|---|---|---|\n")
        for c in logreg["coefficients"]:
            lines.append(
                f"| {c['feature']} | {c['coef']:.4f} | {c['std_err']:.4f} | {c['wald_z']:.3f} | "
                f"{_fmt(c['p_value'])} | [{c['ci_low']:.4f}, {c['ci_high']:.4f}] |\n"
            )

    lines.append(
        "\n> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. "
        "'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.\n"
    )
    return "".join(lines)
