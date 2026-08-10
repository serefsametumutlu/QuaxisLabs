"""Merton (1974) Yapısal Kredi Riski Modeli -- Mesafe-i Temerrüt (Distance
to Default, DD) ve Beklenen Temerrüt Sıklığı (Expected Default Frequency,
EDF).

Kullanıcı isteği (2026-08-08): "bu hisseye girmeden önce kaldıracı ve nakit
akışını mutlaka kontrol et... Temerrüt önemli artık daha çok bakmak lazım" --
şirketin özkaynağını, Black-Scholes'in bir "call opsiyonu" olarak modelleyip
(hissedarlar, borcu ödeyip kalan varlığa sahip çıkma HAKKINA sahiptir --
tam bir Avrupa tipi call opsiyonu), buradan şirketin GÖZLEMLENEMEYEN toplam
varlık değerini/oynaklığını GERİ ÇIKARIR (Vassalou & Xing 2004 / Moody's
KMV'nin standart iteratif prosedürü).

Bu modül `src.analysis.calculator`/`fundamental_screens` ile AYNI ilke:
HİÇBİR I/O yapmaz, `src.fetchers`/`src.db` import ETMEZ (01_MIMARI.md
katman kuralı) -- girdi olarak ÇAĞIRAN TARAFIN zaten hesaplamış olduğu
Decimal değerleri alır.

── NEDEN BU TEK MODÜLDE `float` KULLANILIYOR (Kural 2'nin bilinçli, dar
   kapsamlı istisnası) ──
Projenin geri kalanı (F/K, PD/DD, FAVÖK, skor vb.) parasal/oransal KESİN
değerlerdir ve `Decimal` ile hesaplanır -- 1 kuruşluk bir yuvarlama farkı
bile kullanıcıya YANLIŞ bir rakam gösterebilir. Merton modeli ise DOĞASI
GEREĞİ kesin değil: normal dağılım kümülatif fonksiyonu (N(x)) ve
doğrusal OLMAYAN bir denklem sistemi (iteratif Newton-Raphson) içerir.
Python'ın `decimal` modülü `ln`/`exp`/`sqrt` sağlar ama normal dağılım
CDF'i (erf) veya sayısal kök bulma için HİÇBİR kütüphane desteği YOKTUR --
bunu Decimal ile elle yeniden icat etmek (a) gerçek bir doğruluk kazancı
SAĞLAMAZ (girdilerin kendisi -- oynaklık, borcun "vade değeri" -- zaten
tahmine dayalı) ve (b) standart kantitatif finans pratiğine aykırıdır
(numpy/scipy/QuantLib hepsi float64 kullanır). Bu yüzden BİLİNÇLİ olarak:
girdiler `Decimal` olarak alınır/doğrulanır, iteratif çözüm `float` ile
yapılır, NİHAİ sonuç (DD/EDF/örtük varlık değeri) tekrar `Decimal`'e
yuvarlanarak döner -- `src.formatting` ile tutarlı gösterim için.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from decimal import Decimal

_TRADING_DAYS_PER_YEAR = 252
_MIN_PRICE_OBSERVATIONS = 120  # ~6 ay gunluk veri -- daha azinda yillik oynaklik tahmini guvenilmez (Kural 3)
_MAX_ITERATIONS = 200
_CONVERGENCE_TOLERANCE = 1e-8
_NORMAL = statistics.NormalDist(mu=0, sigma=1)


@dataclass(frozen=True)
class MertonResult:
    asset_value: Decimal  # A0 -- ortuk (gozlemlenemeyen) toplam varlik degeri, bugunku
    asset_volatility_pct: Decimal  # sigma_A -- varlik oynakligi, yillik, yuzde
    debt_face_value: Decimal  # D -- girdinin kendisi (KMV "temerrut noktasi"), gorunum icin tasinir
    distance_to_default: Decimal  # DD -- kac standart sapma "tampon" var
    default_probability_pct: Decimal  # EDF = N(-DD), yuzde
    converged: bool  # False ise DD/EDF YINE DE dondurulur ama yakinsama garanti degildir (kartta/raporda belirtilmeli)


def annualized_equity_volatility(daily_closes: list[Decimal]) -> Decimal | None:
    """Günlük kapanış fiyatlarından (artan tarih sırasında) yıllıklandırılmış
    özkaynak (hisse fiyatı) oynaklığını (%) hesaplar -- günlük logaritmik
    getirilerin standart sapması × √252.

    En az `_MIN_PRICE_OBSERVATIONS` gözlem yoksa (yeni halka arz, veri
    kesintisi vb.) None döner -- Kural 3: yetersiz veriyle bir "oynaklık"
    UYDURULMAZ."""
    if len(daily_closes) < _MIN_PRICE_OBSERVATIONS:
        return None

    closes = [float(c) for c in daily_closes if c is not None and c > 0]
    if len(closes) < _MIN_PRICE_OBSERVATIONS:
        return None

    log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(log_returns) < 2:
        return None

    daily_std = statistics.stdev(log_returns)
    annualized = daily_std * math.sqrt(_TRADING_DAYS_PER_YEAR)
    return Decimal(str(round(annualized * 100, 4)))


def compute_merton_dd_edf(
    equity_market_value: Decimal,
    debt_face_value: Decimal,
    equity_volatility_pct: Decimal,
    risk_free_rate_pct: Decimal,
    horizon_years: Decimal = Decimal(1),
) -> MertonResult | None:
    """Merton modelinin KMV/Vassalou-Xing iteratif çözümü.

    `equity_market_value` (E): piyasa değeri (fiyat × pay adedi).
    `debt_face_value` (D): KMV "temerrüt noktası" -- çağıran taraf bunu
        `kısa_vadeli_yükümlülükler + 0,5 × uzun_vadeli_finansal_borç`
        (Moody's KMV'nin standart yaklaşımı) olarak hesaplayıp geçirmelidir;
        bu modül D'nin NASIL türetildiğini bilmez/karışmaz.
    `equity_volatility_pct`: bkz. `annualized_equity_volatility()`.
    `risk_free_rate_pct`: proje genelinde zaten `src.analysis.valuation.
        _RISK_FREE_RATE_PCT` ile AYNI, elle periyodik güncellenen makro
        sabit -- burada TEKRAR TANIMLANMAZ, çağıran taraf geçirir.

    Girdilerden biri None/<=0 ise VEYA iteratif çözüm `_MAX_ITERATIONS`
    içinde yakınsamazsa None döner (Kural 3/9 -- kartın/raporun geri
    kalanını bloke etmemeli)."""
    if equity_market_value is None or equity_market_value <= 0:
        return None
    if debt_face_value is None or debt_face_value <= 0:
        return None
    if equity_volatility_pct is None or equity_volatility_pct <= 0:
        return None
    if risk_free_rate_pct is None:
        return None

    E = float(equity_market_value)
    D = float(debt_face_value)
    sigma_E = float(equity_volatility_pct) / 100.0
    r = float(risk_free_rate_pct) / 100.0
    T = float(horizon_years)

    def bs_equity_and_d1(asset_value: float, asset_vol: float) -> tuple[float, float]:
        d1 = (math.log(asset_value / D) + (r + 0.5 * asset_vol**2) * T) / (asset_vol * math.sqrt(T))
        d2 = d1 - asset_vol * math.sqrt(T)
        equity_implied = asset_value * _NORMAL.cdf(d1) - D * math.exp(-r * T) * _NORMAL.cdf(d2)
        return equity_implied, d1

    # Baslangic tahmini (Crosbie & Bohn'un standart baslangic noktasi)
    asset_value = E + D
    asset_vol = sigma_E * E / (E + D)
    converged = False
    d1 = 0.0

    for _ in range(_MAX_ITERATIONS):
        # Ic dongu: sigma_A SABITKEN, Black-Scholes ozkaynak denklemini
        # E_implied(A) = E'ye esitleyen A'yi Newton-Raphson ile bul
        # (dE/dA ~ N(d1), opsiyon "delta"si).
        for _inner in range(_MAX_ITERATIONS):
            equity_implied, d1 = bs_equity_and_d1(asset_value, asset_vol)
            delta = _NORMAL.cdf(d1)
            if delta <= 1e-12:
                return None  # kopus -- yakinsayamaz (asiri riskli/aykiri girdi)
            diff = equity_implied - E
            asset_value = asset_value - diff / delta
            if asset_value <= 0:
                return None
            if abs(diff) < _CONVERGENCE_TOLERANCE * E:
                break

        new_asset_vol = sigma_E * E / (asset_value * delta)
        if abs(new_asset_vol - asset_vol) < _CONVERGENCE_TOLERANCE:
            asset_vol = new_asset_vol
            converged = True
            break
        asset_vol = new_asset_vol

    if asset_vol <= 0 or not math.isfinite(asset_value) or not math.isfinite(asset_vol):
        return None

    distance_to_default = (math.log(asset_value / D) + (r - 0.5 * asset_vol**2) * T) / (asset_vol * math.sqrt(T))
    default_probability = _NORMAL.cdf(-distance_to_default)

    return MertonResult(
        asset_value=Decimal(str(round(asset_value, 2))),
        asset_volatility_pct=Decimal(str(round(asset_vol * 100, 4))),
        debt_face_value=debt_face_value,
        distance_to_default=Decimal(str(round(distance_to_default, 4))),
        default_probability_pct=Decimal(str(round(default_probability * 100, 4))),
        converged=converged,
    )
