"""VRP (Variance Risk Premium) -- gerçekleşen (RV) ve tahmini/beklenen (IV
proxy) volatilite farkı, sektör rotasyon backtestinin (`sector_rotation_
backtest.py`) girdisi. SAF MATEMATIK, I/O YOK (`src.fetchers`/`src.db`
import ETMEZ) -- `momentum_confluence.py` ile AYNI katman ilkesi.

Kaynak/motivasyon: kullanıcının paylaştığı bir quant'ın "VRP Scanner"
dashboard'u (RV=gerçekleşen vol, IV=piyasanın fiyatladığı beklenen vol,
VRP=IV-RV; VRP çok negatifse "fırtına öncesi sessizlik" = kırılım/breakout
beklenir). Quant'ın TAM formülü/veri kaynağı elde YOK (kullanıcı 2026-08-19'da
teyit etti) -- BİST'te de tekil hisse opsiyon zinciri için ücretsiz/erişilebilir
bir kaynak projede YOK (bkz. `src/analysis/merton.py` sadece Black-Scholes'i
TERSİNE, temerrüt olasılığı için kullanıyor, gerçek opsiyon IV'si çekmiyor).
Bu yüzden IV BURADA kendi GARCH(1,1) ileri-volatilite TAHMİNİMİZDİR (kullanıcı
kararı, 2026-08-19: "arch" paketi EKLENMEDİ, mevcut `scipy` ile hand-rolled
MLE) -- gerçek piyasa-fiyatlı implied volatilite DEĞİLDİR, açıkça "IV proxy"
olarak adlandırılır.

Sayısal kararlılık: `abcd_data.py` unadjusted fiyat kullanır (auto_adjust=
False) -- temettü/bölünme kaynaklı tek-günlük aşırı sıçramalar GARCH fit'ini
bozabileceğinden log-getiriler ±`_RETURN_CLIP` ile winsorize edilir. Bu SADECE
bu modülde uygulanır -- Pine-parity modüllerinde (abcd_pattern.py,
momentum_confluence.py) böyle bir filtre YASAKTIR, ama bu modülün Pine kaynağı
yok, kendi YENİ stratejimiz.

Look-ahead güvenliği: `compute_vrp_snapshot(closes, as_of_idx)` SADECE
`closes[:as_of_idx+1]` dilimine bakar -- `sector_rotation_backtest.py`'nin
aylık rebalance döngüsü bunu HER rebalance tarihinde çağırır, gelecekteki
fiyatlar asla sızmamalıdır (bkz. tests/test_vrp.py look-ahead regresyon testi).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

_TRADING_DAYS_PER_YEAR = 252
_RV_WINDOW = 21  # ~1 aylık iş günü -- sektör rotasyon rebalance ufkuyla AYNI
_GARCH_LOOKBACK = 500  # ~2 yıllık iş günü -- MLE için yeterli örneklem
_GARCH_MIN_OBS = 250  # bunun altında fit GÜVENİLMEZ, None döner
_GARCH_FORECAST_HORIZON = 21  # RV penceresiyle AYNI ufuk -- karşılaştırılabilirlik
_RETURN_CLIP = 0.20  # log-getiri winsorize sınırı (bkz. modül üst notu)
_MIN_VARIANCE = 1e-12  # log(0)/bölme-sıfır koruması (savunmacı, omega>0 zaten engeller)


def _log_returns(closes: np.ndarray) -> np.ndarray:
    """Ardışık kapanışlardan log-getiri, non-finite (NaN/inf, sıfır/negatif
    close) barlar atılır, ±`_RETURN_CLIP` ile winsorize edilir."""
    closes = np.asarray(closes, dtype=float)
    valid = closes > 0
    closes = closes[valid]
    if len(closes) < 2:
        return np.empty(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.diff(np.log(closes))
    r = r[np.isfinite(r)]
    return np.clip(r, -_RETURN_CLIP, _RETURN_CLIP)


def realized_volatility(log_returns: np.ndarray, window: int = _RV_WINDOW) -> float | None:
    """Son `window` günün log-getiri std sapması, yıllıklandırılmış yüzde
    (`merton.annualized_equity_volatility` ile AYNI √252 ilkesi, ama TEK
    noktalık Decimal API yerine burada float dizi/rolling-uyumlu)."""
    log_returns = np.asarray(log_returns, dtype=float)
    if len(log_returns) < window:
        return None
    tail = log_returns[-window:]
    return float(np.std(tail, ddof=1) * np.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0)


def rolling_realized_volatility(log_returns: np.ndarray, window: int = _RV_WINDOW) -> np.ndarray:
    """`realized_volatility`nin tüm seri üzerinde kayan-pencere hali (test/
    teşhis kolaylığı için) -- ilk `window-1` eleman NaN."""
    log_returns = np.asarray(log_returns, dtype=float)
    n = len(log_returns)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        out[i] = float(np.std(log_returns[i - window + 1 : i + 1], ddof=1) * np.sqrt(_TRADING_DAYS_PER_YEAR) * 100.0)
    return out


@dataclass(frozen=True)
class GarchFitResult:
    omega: float
    alpha: float
    beta: float
    converged: bool
    log_likelihood: float
    unconditional_vol_annualized_pct: float
    last_h: float  # son barın kosullu varyansi -- ileri tahmin (garch_forecast_iv) icin
    last_eps2: float  # son barin (demeaned) kare getirisi -- ayni amac


def _garch_h_series(eps: np.ndarray, omega: float, alpha: float, beta: float) -> np.ndarray:
    """GARCH(1,1) koşullu varyans rekürsiyonu: h[0]=koşulsuz varyans (seed,
    Pine-parity modüllerindeki `atr_wilder` bar-0 fallback ilkesiyle AYNI
    ruhta), t>=1: h[t] = omega + alpha*eps[t-1]^2 + beta*h[t-1]."""
    n = len(eps)
    h = np.empty(n)
    h[0] = max(float(np.var(eps)), _MIN_VARIANCE)
    for t in range(1, n):
        h[t] = max(omega + alpha * eps[t - 1] ** 2 + beta * h[t - 1], _MIN_VARIANCE)
    return h


def _garch_neg_log_likelihood(params: np.ndarray, eps: np.ndarray) -> float:
    omega, alpha, beta = params
    with np.errstate(over="ignore", invalid="ignore"):
        h = _garch_h_series(eps, omega, alpha, beta)
        nll = 0.5 * np.sum(np.log(h[1:]) + eps[1:] ** 2 / h[1:])
    return float(nll) if np.isfinite(nll) else float("inf")


def _nll_reparam(x: np.ndarray, eps: np.ndarray) -> float:
    """`_garch_neg_log_likelihood`nin (omega,s,p) yeniden-parametrizasyonu
    -- `s=alpha+beta` (toplam kalıcılık), `p=alpha/s` (kalıcılığın alpha'ya
    düşen payı). `alpha+beta<0.999` durağanlık kısıtı BÖYLECE bounds'a
    GÖMÜLÜR (ayrı bir eşitsizlik kısıtı GEREKMEZ) -- bkz. modül üst notu
    "GARCH performans notu": bu, eşitsizlik-kısıtlı `trust-constr`e göre
    ~10x daha hızlı, bounds-only `L-BFGS-B` kullanmayı MÜMKÜN kılar."""
    omega, s, p = x
    alpha, beta = s * p, s * (1.0 - p)
    return _garch_neg_log_likelihood(np.array([omega, alpha, beta]), eps)


# 3 farkli baslangic noktasi ((s0,p0): toplam kalicilik, alpha payi) --
# yerel optimum riskine karsi, maliyeti dusuk (bkz. modul ust notu).
_GARCH_INIT_S_P = ((0.95, 0.10 / 0.95), (0.85, 0.10 / 0.85), (0.90, 0.15 / 0.90))


def fit_garch11(log_returns: np.ndarray) -> GarchFitResult | None:
    """Trailing `log_returns` üzerinde GARCH(1,1) MLE fit. GARCH PERFORMANS
    NOTU (2026-08-19): ilk deneme `scipy.optimize.minimize(method="SLSQP")`
    ile doğrudan (omega,alpha,beta) + eşitsizlik kısıtıydı -- hem SLSQP hem
    `trust-constr` sınır-yakını noktalarda sık sık takılıyordu/YAVAŞTI
    (~2.8s/fit -- tam-BIST ölçeğinde saatler sürerdi). Şimdiki yaklaşım:
    `_nll_reparam` ile durağanlık kısıtı bounds'a gömülür, bounds-only
    `L-BFGS-B` kullanılır (~0.1s/fit, ~25x daha hızlı, AYNI kalite kurtarma
    -- bkz. tests/test_vrp.py). `< _GARCH_MIN_OBS` girişte None. Hiçbir
    restart yakınsamazsa `converged=False` ile en iyi (en düşük NLL)
    bulunan parametreler YİNE DE döner -- sessizce atmaz, etiketler
    (`merton.py`nin `converged` alanı deseniyle AYNI ilke)."""
    log_returns = np.asarray(log_returns, dtype=float)
    if len(log_returns) < _GARCH_MIN_OBS:
        return None

    tail = log_returns[-_GARCH_LOOKBACK:]
    eps = tail - np.mean(tail)  # demean (GARCH-in-mean kapsam disi)
    var_eps = float(np.var(eps))
    if var_eps <= 0:
        return None

    bounds = [(1e-10, None), (0.0, 0.999), (0.0, 1.0)]

    best_result = None
    best_converged = False
    for s0, p0 in _GARCH_INIT_S_P:
        omega0 = var_eps * (1.0 - s0)
        x0 = np.array([omega0, s0, p0])
        try:
            res = minimize(_nll_reparam, x0, args=(eps,), method="L-BFGS-B", bounds=bounds, options={"maxiter": 200})
        except Exception:
            continue
        if not np.isfinite(res.fun):
            continue
        is_better = best_result is None or res.fun < best_result.fun
        # Yakinsayan bir sonuc varsa yakinsamayanlar ONA tercih EDILMEZ.
        if best_result is None or (res.success and not best_converged) or (res.success == best_converged and is_better):
            best_result = res
            best_converged = bool(res.success)

    if best_result is None:
        return None

    omega, s, p = best_result.x
    alpha, beta = float(s * p), float(s * (1.0 - p))
    h = _garch_h_series(eps, omega, alpha, beta)
    persistence = max(1.0 - alpha - beta, 1e-6)
    uncond_vol_pct = float(np.sqrt((omega / persistence) * _TRADING_DAYS_PER_YEAR) * 100.0)

    return GarchFitResult(
        omega=float(omega),
        alpha=float(alpha),
        beta=float(beta),
        converged=best_converged,
        log_likelihood=float(-best_result.fun),
        unconditional_vol_annualized_pct=uncond_vol_pct,
        last_h=float(h[-1]),
        last_eps2=float(eps[-1] ** 2),
    )


def garch_forecast_iv(fit: GarchFitResult, horizon: int = _GARCH_FORECAST_HORIZON) -> float:
    """GARCH(1,1) çok-adımlı varyans tahmini: 1. adım gerçek `last_eps2`/
    `last_h`den, sonraki adımlar E[eps^2]=h_t varsayımıyla (`h_{k} = omega +
    (alpha+beta)*h_{k-1}`) rekürsif ilerletilir. `horizon` günlük ortalama
    varyans yıllıklandırılıp "IV proxy" (yüzde) olarak döner."""
    h_next = fit.omega + fit.alpha * fit.last_eps2 + fit.beta * fit.last_h
    path = [max(h_next, _MIN_VARIANCE)]
    persistence = fit.alpha + fit.beta
    for _ in range(horizon - 1):
        h_next = fit.omega + persistence * path[-1]
        path.append(max(h_next, _MIN_VARIANCE))
    mean_variance = float(np.mean(path))
    return float(np.sqrt(mean_variance * _TRADING_DAYS_PER_YEAR) * 100.0)


def compute_vrp(iv_annualized_pct: float, rv_annualized_pct: float) -> float:
    """VRP = IV_proxy - RV (ham fark, yıllıklandırılmış vol puanı cinsinden
    -- oran DEĞİL, bkz. modül üst notu: quant'ın tam formülü bilinmiyor,
    kendi tanımımız açıkça budur). Negatif = IV, RV'nin altında = piyasa
    /GARCH modelinin gelecekten beklediği hareket geçmişten DAHA DÜŞÜK ->
    "fırtına öncesi sessizlik", kırılım/breakout adayı."""
    return float(iv_annualized_pct - rv_annualized_pct)


@dataclass(frozen=True)
class VrpSnapshot:
    as_of_idx: int
    rv_annualized_pct: float | None
    iv_proxy_annualized_pct: float | None
    vrp: float | None
    garch: GarchFitResult | None


def compute_vrp_snapshot(closes: np.ndarray, as_of_idx: int) -> VrpSnapshot:
    """`closes[:as_of_idx+1]` (ve SADECE bu dilim -- look-ahead güvenliği,
    bkz. modül üst notu) üzerinden RV/IV-proxy/VRP hesaplar. Yetersiz
    geçmişte (`< _GARCH_MIN_OBS` geçerli log-getiri) tüm alanlar None."""
    window = np.asarray(closes, dtype=float)[: as_of_idx + 1]
    log_returns = _log_returns(window)

    if len(log_returns) < _GARCH_MIN_OBS:
        return VrpSnapshot(as_of_idx=as_of_idx, rv_annualized_pct=None, iv_proxy_annualized_pct=None, vrp=None, garch=None)

    rv = realized_volatility(log_returns, _RV_WINDOW)
    garch = fit_garch11(log_returns)
    if rv is None or garch is None:
        return VrpSnapshot(as_of_idx=as_of_idx, rv_annualized_pct=rv, iv_proxy_annualized_pct=None, vrp=None, garch=garch)

    iv = garch_forecast_iv(garch, _GARCH_FORECAST_HORIZON)
    vrp = compute_vrp(iv, rv)
    return VrpSnapshot(as_of_idx=as_of_idx, rv_annualized_pct=rv, iv_proxy_annualized_pct=iv, vrp=vrp, garch=garch)
