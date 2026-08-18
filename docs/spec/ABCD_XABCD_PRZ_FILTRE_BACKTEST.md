# PRZ Dogrulanma Filtresi -- Somut Kural + Out-of-Sample Backtest

Olusturulma: 2026-08-18 12:14 UTC

## Kural

`cd_duration_bars >= 8.0` VE `volume_ratio <= 1.128` -- esikler SADECE kronolojik train'in (%70, ilk) medyanlarindan turetildi, holdout'a (%30, son -- gercekten gorulmemis veri) DEGISTIRILMEDEN uygulandi.

- Toplam PRZ olayi: 5344 (train=3741, holdout=1603)
- Kronolojik split esigi: 2026-03-05 09:00:00+03:00

## ⚠️ Bu raporun SADECE holdout satirlari out-of-sample gecerlidir

Train satirlari SADECE referans/karsilastirma icindir -- esikler train'den turetildigi icin train uzerindeki herhangi bir 'iyilesme' dolasiktir (circular), kanit DEGERI YOK.

## Dogrulanma Orani (Vindication Rate)

| Kume | n | Dogrulanma Orani % |
|---|---|---|
| HOLDOUT -- tum PRZ (filtresiz) | 1603 | 13.66 |
| HOLDOUT -- filtreyi GECEN | 510 | 18.82 |
| HOLDOUT -- filtreyi GECEMEYEN | 1093 | 11.25 |
| (referans, train) tum PRZ | 3741 | 14.14 |
| (referans, train) filtreyi GECEN | 1164 | 20.45 |

## Backtest Performansi (R-multiple bazli)

| Kume | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % |
|---|---|---|---|---|---|
| HOLDOUT -- tum PRZ (filtresiz) | 1245 | 36.95 | 0.86 | -0.083 | -1.23 |
| HOLDOUT -- filtreyi GECEN | 450 | 36.89 | 0.91 | -0.026 | -0.88 |
| HOLDOUT -- filtreyi GECEMEYEN | 814 | 36.86 | 0.83 | -0.110 | -1.00 |
| (referans, train) tum PRZ | 2881 | 37.83 | 0.83 | -0.542 | -1.79 |
| (referans, train) filtreyi GECEN | 1001 | 38.66 | 0.91 | -1.162 | -1.05 |

## Ham Veri

Ham PRZ olay tablosu (ozellikler + vindicated etiketi): `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\harmonic_xabcd_prz_filter_events.csv`
