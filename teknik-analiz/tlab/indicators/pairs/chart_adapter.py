"""`pair.*` göstergelerinin `IndicatorResult`ini `PairView`e çevirir.

Diğer adaptörlerden İKİ farkı var:
  * girdi olarak TEK bir df değil, Y ve X'in HAM serileri gerekiyor
    (`pair_health.assess` korelasyon/beta/yarı-ömrü fiyatlardan hesaplar)
    -- bu yüzden `live.py::compute_pair_live` köprüsü eklendi;
  * `composers/pair.py::compose` imzası `df` ALMAZ (pair grafiği tek
    sembolün mumlarını çizmez), rota bu yüzden ayrı bir dal kullanır.

Hesap YAPMAZ: seriler göstergenin `result.series`inden, sağlık ise
`features/pair_health.py`nin KENDİ değerlendirmesinden gelir.
"""

from __future__ import annotations

import pandas as pd

from tlab.chart.composers.pair import PairTrade, PairView
from tlab.core.types import IndicatorResult
from tlab.features.pair_health import assess


def to_view(
    result: IndicatorResult, df_y: pd.DataFrame, df_x: pd.DataFrame,
) -> PairView | None:
    ser = result.series
    need = ("y_norm", "x_norm", "z", "spread")
    if not all(k in ser for k in need):
        return None

    y_sym, _, x_sym = str(result.symbol).partition("/")
    if not y_sym or not x_sym:
        return None

    # Ortak takvim: iki seri farklı uzunlukta olabilir (tatil/halka arz).
    # Gösterge zaten inner-join yapıyor; sağlık ölçümü de AYNI kesişimde
    # yapılmalı, yoksa korelasyon hizasız iki seriden hesaplanır.
    common = df_y.index.intersection(df_x.index)
    spread = ser["spread"]
    health = assess(
        df_y.loc[common, "close"], df_x.loc[common, "close"],
        spread.reindex(common).dropna(),
    )

    # İşlemler: `holding` serisinin DEĞİŞTİĞİ barlar. Gösterge geçişi
    # zaten bu seriyle anlatıyor (1.0 = Y, 0.0 = X); adaptör yalnızca
    # değişim noktalarını okur, yeni bir kural uygulamaz.
    trades: list[PairTrade] = []
    z = ser["z"]
    # İKİ pair göstergesi farklı konuşuyor:
    #  * `relative_momentum` ROTASYONEL -> `holding` (1.0=Y, 0.0=X),
    #    değişim barı = işlem.
    #  * `vol_harvest` SÜREKLİ AĞIRLIKLI -> `holding` YOK, `w_actual`
    #    var. Orada "işlem" ağırlığın 0.5'i geçtiği bar sayılır (baskın
    #    bacağın el değiştirdiği an) -- yaklaşıktır ve stratejinin
    #    doğasından gelir, her rebalansı işlem saymak yanıltıcı olurdu.
    holding = ser.get("holding")
    if holding is None:
        w = ser.get("w_actual")
        holding = None if w is None else (w >= 0.5).astype(float)
    if holding is not None:
        prev = None
        for t, v in holding.items():
            if pd.isna(v):
                continue
            if prev is not None and v != prev:
                leg = y_sym if v >= 0.5 else x_sym
                trades.append(
                    PairTrade(
                        t=pd.Timestamp(t), z=float(z.get(t, 0.0)),
                        leg=leg, side="long",
                    )
                )
            prev = v

    st = result.last_state or {}
    entry_z = float(st.get("entry_z", 2.0)) if isinstance(st.get("entry_z"), int | float) else 2.0

    # KAYAN korelasyon/beta göstergeden gelir. İlk sürümde `PairHealth`in
    # son değerleri sabit bir seriye yayılıyordu ve alt panel DÜZ bir
    # çizgi oluyordu -- oysa çiftin bozulması tam olarak bu iki serinin
    # ZAMAN İÇİNDE kaymasıyla görülür (kointegrasyon çürümesi).
    idx = ser["z"].index
    corr = ser.get("corr", pd.Series(health.corr_now, index=idx))
    beta = ser.get("beta", pd.Series(health.beta_now, index=idx))

    return PairView(
        y_symbol=y_sym, x_symbol=x_sym,
        y_norm=ser["y_norm"], x_norm=ser["x_norm"],
        equity=ser.get("portfolio", ser["y_norm"]),
        benchmark=ser.get("buyhold_5050", ser["x_norm"]),
        zscore=z, corr=corr, beta=beta,
        trades=tuple(trades), health=health, entry_z=entry_z,
    )
