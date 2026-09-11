"""docs/KALAN_ISLER.md madde 1.3 -- Deflated Sharpe Ratio (Bailey & Lopez
de Prado, 2014). 23 gosterge arasindan "en iyi" gorunenin, sirf COK
gosterge denendigi icin (coklu-secim onyargisi) sansla iyi cikip
cikmadigini test eder -- Benjamini-Hochberg'in (madde 1.3'un diger yarisi)
TAMAMLAYICISI, onun yerine gecmez.

DSR = Phi( (SR_hat - SR_0) / sigma_SR_hat )

  SR_hat: gozlenen (donem-basi, YILLIKLANDIRILMAMIS) Sharpe orani.
  sigma_SR_hat: SR_hat'in kendi standart hatasi (getirilerin carpiklik/
    basiklik'ini hesaba katar -- Mertens 2002 formulu).
  SR_0: N BAGIMSIZ deneyden BEKLENEN maksimum Sharpe orani (deneyler
    arasi Sharpe varyansindan turetilir) -- Bailey&Lopez de Prado Denklem 10.
  Phi: standart normal CDF.

DSR > belirli bir esigi (ornegin 0.95, tek-yonlu %95 guven) asarsa,
gozlenen en iyi performansin YALNIZCA sans/coklu-deneme eseri olmadigi
soylenebilir."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats as sps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def sharpe_stderr(sharpe: float, skew: float, kurt_excess: float, n: int) -> float:
    """Mertens (2002) -- carpiklik/basikliğin duzelttigi Sharpe standart hatasi."""
    var = (1 - skew * sharpe + (kurt_excess) / 4 * sharpe**2) / max(n - 1, 1)
    return float(np.sqrt(max(var, 0.0)))


def expected_max_sharpe(sharpe_std_across_trials: float, n_trials: int) -> float:
    """Bailey & Lopez de Prado (2014) Denklem 10 -- N BAGIMSIZ SR~N(0, sigma^2)
    denemesinden beklenen MAKSIMUM Sharpe (Euler-Mascheroni sabiti ile)."""
    euler_mascheroni = 0.5772156649
    if n_trials <= 1:
        return 0.0
    z1 = sps.norm.ppf(1 - 1.0 / n_trials)
    z2 = sps.norm.ppf(1 - 1.0 / (n_trials * np.e))
    return float(sharpe_std_across_trials * (
        (1 - euler_mascheroni) * z1 + euler_mascheroni * z2
    ))


def deflated_sharpe_ratio(
    returns: np.ndarray, sharpe_std_across_trials: float, n_trials: int,
) -> dict:
    n = len(returns)
    sharpe = float(np.mean(returns) / np.std(returns, ddof=1)) if np.std(returns, ddof=1) > 0 else 0.0
    skew = float(sps.skew(returns))
    kurt_excess = float(sps.kurtosis(returns, fisher=True))  # fazla basiklik (normal=0)
    sr0 = expected_max_sharpe(sharpe_std_across_trials, n_trials)
    se = sharpe_stderr(sharpe, skew, kurt_excess, n)
    dsr = float(sps.norm.cdf((sharpe - sr0) / se)) if se > 0 else float("nan")
    return {
        "n": n, "sharpe_hat": sharpe, "skew": skew, "kurt_excess": kurt_excess,
        "sr0_beklenen_max": sr0, "se_sharpe": se, "dsr": dsr,
    }


if __name__ == "__main__":
    import pandas as pd

    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "outputs" / "reports"
        / "tam_istatistiksel_dogrulama_2026-09-11.csv"
    )
    df = pd.read_csv(csv_path)
    # Sharpe-benzeri bir olcum: her gostergenin OOS fark/sqrt(n) "t-istatistigi"
    # yakinsagi -- ayri bir returns serisi olmadan (bu CSV yalnizca ozet
    # istatistik tasiyor) tam DSR icin returns dizisine ihtiyac var; bu
    # script bu yuzden asil hesaplamayi cagiran (tam_istatistiksel_
    # dogrulama.py icine entegre edilecek bir sonraki adim) icin fonksiyon
    # kutuphanesi olarak tasarlandi -- bkz. modul docstring'i.
    print("Bu dosya bir fonksiyon kutuphanesi + CLI ornegidir; gercek "
          "returns dizileriyle cagrilmasi gerekir (bkz. tam_istatistiksel_"
          "dogrulama.py'nin returns dondurmesi icin genisletilmesi).")
