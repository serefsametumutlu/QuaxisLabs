# XABCD V2.1 (X-noktali) Arastirmasi -- Confirmed vs PRZ Kalitesi

Olusturulma: 2026-08-18 10:46 UTC

## Kapsam

Sembol sayisi: 657 · Zaman dilimleri: 1D, 240 · Backtest derinligi: ~2.0 yil · Para birimi: TRY. Formasyonlar: GARTLEY/BAT/BUTTERFLY/CRAB, X-noktali (V2.1) literatur-dogru CD/BC + XD/XA tanimiyla -- `pine/harmonic_formations_v1_indicator.pine` (V2.1, XD yon duzeltmesi dahil) ile Pine-parity.

## ⚠️ METODOLOJI UYARISI

`min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak etiketlenip tabloda TUTULUR. "En iyi" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir.

## PRZ Dogrulanma (Vindication) Oranlari

Bir PRZ erken-uyarisi "dogrulanmis" sayilir eger AYNI C pivotu icin SONRADAN gercekten onayli bir D sinyali olustuysa (`harmonic_xabcd.match_prz_to_confirmed`). Dusuk oran = PRZ'nin "alakasiz" gorunen kismi.

| Formasyon | Yon | TF | PRZ Olay Sayisi | Dogrulanan | Dogrulanma Orani % |
|---|---|---|---|---|---|
| BAT | LONG | 1D | 174 | 32 | 18.39 |
| BAT | LONG | 240 | 375 | 90 | 24.00 |
| BAT | SHORT | 1D | 276 | 28 | 10.14 |
| BAT | SHORT | 240 | 436 | 59 | 13.53 |
| BUTTERFLY | LONG | 1D | 297 | 55 | 18.52 |
| BUTTERFLY | LONG | 240 | 443 | 78 | 17.61 |
| BUTTERFLY | SHORT | 1D | 300 | 36 | 12.00 |
| BUTTERFLY | SHORT | 240 | 524 | 38 | 7.25 |
| CRAB | LONG | 1D | 106 | 26 | 24.53 |
| CRAB | LONG | 240 | 205 | 39 | 19.02 |
| CRAB | SHORT | 1D | 224 | 24 | 10.71 |
| CRAB | SHORT | 240 | 351 | 38 | 10.83 |
| GARTLEY | LONG | 1D | 307 | 50 | 16.29 |
| GARTLEY | LONG | 240 | 526 | 74 | 14.07 |
| GARTLEY | SHORT | 1D | 319 | 28 | 8.78 |
| GARTLEY | SHORT | 240 | 485 | 54 | 11.13 |

## Kategori Karsilastirmasi (CONFIRMED vs PRZ_ALL vs PRZ_VINDICATED vs PRZ_FALSE_START)

| Formasyon | Yon | TF | Kategori | n | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|---|---|---|
| BAT | LONG | 1D | CONFIRMED | 24 | 70.83 | 1.74 | 0.168 | -0.22 | GUVENSIZ (n=24) |
| BAT | LONG | 1D | PRZ_ALL | 168 | 37.50 | 0.67 | -0.227 | -0.74 | GUVENILIR |
| BAT | LONG | 1D | PRZ_VINDICATED | 31 | 83.87 | 6.31 | 0.710 | -0.14 | DUSUK GUVEN (n=31) |
| BAT | LONG | 1D | PRZ_FALSE_START | 137 | 27.01 | 0.45 | -0.439 | -0.85 | GUVENILIR |
| BAT | LONG | 240 | CONFIRMED | 79 | 59.49 | 0.80 | -0.084 | -0.41 | DUSUK GUVEN (n=79) |
| BAT | LONG | 240 | PRZ_ALL | 354 | 36.16 | 0.90 | -0.055 | -0.88 | GUVENILIR |
| BAT | LONG | 240 | PRZ_VINDICATED | 86 | 63.95 | 3.04 | 0.782 | -0.37 | DUSUK GUVEN (n=86) |
| BAT | LONG | 240 | PRZ_FALSE_START | 268 | 27.24 | 0.60 | -0.323 | -0.96 | GUVENILIR |
| BAT | SHORT | 1D | CONFIRMED | 9 | 44.44 | 0.30 | -0.323 | -0.46 | GUVENSIZ (n=9) |
| BAT | SHORT | 1D | PRZ_ALL | 241 | 39.83 | 0.86 | -4.615 | -0.72 | GUVENILIR |
| BAT | SHORT | 1D | PRZ_VINDICATED | 24 | 79.17 | 5.69 | 0.816 | -0.18 | GUVENSIZ (n=24) |
| BAT | SHORT | 1D | PRZ_FALSE_START | 217 | 35.48 | 0.72 | -5.216 | -0.77 | GUVENILIR |
| BAT | SHORT | 240 | CONFIRMED | 36 | 38.89 | 0.62 | -0.174 | -0.49 | DUSUK GUVEN (n=36) |
| BAT | SHORT | 240 | PRZ_ALL | 357 | 39.22 | 0.85 | -0.129 | -0.85 | GUVENILIR |
| BAT | SHORT | 240 | PRZ_VINDICATED | 54 | 68.52 | 2.00 | 0.250 | -0.28 | DUSUK GUVEN (n=54) |
| BAT | SHORT | 240 | PRZ_FALSE_START | 303 | 33.99 | 0.77 | -0.196 | -0.91 | GUVENILIR |
| BUTTERFLY | LONG | 1D | CONFIRMED | 41 | 58.54 | 1.13 | 0.042 | -0.34 | DUSUK GUVEN (n=41) |
| BUTTERFLY | LONG | 1D | PRZ_ALL | 282 | 38.65 | 1.02 | 0.010 | -0.81 | GUVENILIR |
| BUTTERFLY | LONG | 1D | PRZ_VINDICATED | 52 | 73.08 | 4.61 | 0.938 | -0.27 | DUSUK GUVEN (n=52) |
| BUTTERFLY | LONG | 1D | PRZ_FALSE_START | 231 | 30.74 | 0.72 | -0.203 | -0.88 | GUVENILIR |
| BUTTERFLY | LONG | 240 | CONFIRMED | 55 | 49.09 | 0.46 | -0.255 | -0.50 | DUSUK GUVEN (n=55) |
| BUTTERFLY | LONG | 240 | PRZ_ALL | 420 | 35.95 | 1.04 | 0.030 | -0.99 | GUVENILIR |
| BUTTERFLY | LONG | 240 | PRZ_VINDICATED | 71 | 67.61 | 2.69 | 0.510 | -0.35 | DUSUK GUVEN (n=71) |
| BUTTERFLY | LONG | 240 | PRZ_FALSE_START | 350 | 29.43 | 0.90 | -0.070 | -1.05 | GUVENILIR |
| BUTTERFLY | SHORT | 1D | CONFIRMED | 24 | 58.33 | 0.72 | -0.099 | -0.36 | GUVENSIZ (n=24) |
| BUTTERFLY | SHORT | 1D | PRZ_ALL | 259 | 42.86 | 0.92 | -0.069 | -0.72 | GUVENILIR |
| BUTTERFLY | SHORT | 1D | PRZ_VINDICATED | 33 | 78.79 | 3.59 | 0.484 | -0.20 | DUSUK GUVEN (n=33) |
| BUTTERFLY | SHORT | 1D | PRZ_FALSE_START | 226 | 37.61 | 0.81 | -0.150 | -0.76 | GUVENILIR |
| BUTTERFLY | SHORT | 240 | CONFIRMED | 23 | 60.87 | 1.74 | 0.124 | -0.19 | GUVENSIZ (n=23) |
| BUTTERFLY | SHORT | 240 | PRZ_ALL | 435 | 34.48 | 0.64 | -0.297 | -0.95 | GUVENILIR |
| BUTTERFLY | SHORT | 240 | PRZ_VINDICATED | 31 | 90.32 | 14.60 | 0.848 | -0.07 | DUSUK GUVEN (n=31) |
| BUTTERFLY | SHORT | 240 | PRZ_FALSE_START | 404 | 30.20 | 0.55 | -0.385 | -0.98 | GUVENILIR |
| CRAB | LONG | 1D | CONFIRMED | 19 | 73.68 | 3.16 | 0.461 | -0.23 | GUVENSIZ (n=19) |
| CRAB | LONG | 1D | PRZ_ALL | 100 | 46.00 | 1.38 | 0.196 | -0.60 | GUVENILIR |
| CRAB | LONG | 1D | PRZ_VINDICATED | 25 | 92.00 | 19.04 | 1.431 | -0.09 | GUVENSIZ (n=25) |
| CRAB | LONG | 1D | PRZ_FALSE_START | 75 | 30.67 | 0.72 | -0.215 | -0.76 | DUSUK GUVEN (n=75) |
| CRAB | LONG | 240 | CONFIRMED | 29 | 65.52 | 1.42 | 0.129 | -0.34 | GUVENSIZ (n=29) |
| CRAB | LONG | 240 | PRZ_ALL | 191 | 36.65 | 0.73 | -0.224 | -0.82 | GUVENILIR |
| CRAB | LONG | 240 | PRZ_VINDICATED | 37 | 72.97 | 3.81 | 0.727 | -0.28 | DUSUK GUVEN (n=37) |
| CRAB | LONG | 240 | PRZ_FALSE_START | 154 | 27.92 | 0.48 | -0.453 | -0.90 | GUVENILIR |
| CRAB | SHORT | 1D | CONFIRMED | 14 | 57.14 | 0.23 | -0.284 | -0.37 | GUVENSIZ (n=14) |
| CRAB | SHORT | 1D | PRZ_ALL | 208 | 34.13 | 0.55 | -0.322 | -0.81 | GUVENILIR |
| CRAB | SHORT | 1D | PRZ_VINDICATED | 23 | 78.26 | 2.15 | 0.255 | -0.22 | GUVENSIZ (n=23) |
| CRAB | SHORT | 1D | PRZ_FALSE_START | 185 | 28.65 | 0.49 | -0.394 | -0.88 | GUVENILIR |
| CRAB | SHORT | 240 | CONFIRMED | 26 | 53.85 | 0.31 | -0.280 | -0.41 | GUVENSIZ (n=26) |
| CRAB | SHORT | 240 | PRZ_ALL | 306 | 33.99 | 0.77 | -0.357 | -0.89 | GUVENILIR |
| CRAB | SHORT | 240 | PRZ_VINDICATED | 36 | 77.78 | 3.93 | 0.768 | -0.25 | DUSUK GUVEN (n=36) |
| CRAB | SHORT | 240 | PRZ_FALSE_START | 271 | 28.41 | 0.63 | -0.505 | -0.96 | GUVENILIR |
| GARTLEY | LONG | 1D | CONFIRMED | 43 | 67.44 | 1.36 | 0.088 | -0.27 | DUSUK GUVEN (n=43) |
| GARTLEY | LONG | 1D | PRZ_ALL | 295 | 42.71 | 1.12 | 0.072 | -0.75 | GUVENILIR |
| GARTLEY | LONG | 1D | PRZ_VINDICATED | 48 | 75.00 | 4.30 | 0.723 | -0.24 | DUSUK GUVEN (n=48) |
| GARTLEY | LONG | 1D | PRZ_FALSE_START | 247 | 36.44 | 0.91 | -0.055 | -0.82 | GUVENILIR |
| GARTLEY | LONG | 240 | CONFIRMED | 55 | 65.45 | 1.00 | 0.000 | -0.35 | DUSUK GUVEN (n=55) |
| GARTLEY | LONG | 240 | PRZ_ALL | 492 | 36.99 | 0.86 | -0.171 | -1.02 | GUVENILIR |
| GARTLEY | LONG | 240 | PRZ_VINDICATED | 70 | 74.29 | 3.55 | 0.621 | -0.26 | DUSUK GUVEN (n=70) |
| GARTLEY | LONG | 240 | PRZ_FALSE_START | 423 | 30.97 | 0.71 | -0.298 | -1.09 | GUVENILIR |
| GARTLEY | SHORT | 1D | CONFIRMED | 15 | 40.00 | 0.10 | -0.375 | -0.43 | GUVENSIZ (n=15) |
| GARTLEY | SHORT | 1D | PRZ_ALL | 282 | 40.43 | 0.83 | -0.132 | -0.77 | GUVENILIR |
| GARTLEY | SHORT | 1D | PRZ_VINDICATED | 25 | 84.00 | 9.03 | 0.653 | -0.09 | GUVENSIZ (n=25) |
| GARTLEY | SHORT | 1D | PRZ_FALSE_START | 257 | 36.19 | 0.73 | -0.209 | -0.82 | GUVENILIR |
| GARTLEY | SHORT | 240 | CONFIRMED | 33 | 42.42 | 0.17 | -0.303 | -0.38 | DUSUK GUVEN (n=33) |
| GARTLEY | SHORT | 240 | PRZ_ALL | 417 | 38.61 | 0.51 | -0.419 | -0.87 | GUVENILIR |
| GARTLEY | SHORT | 240 | PRZ_VINDICATED | 49 | 79.59 | 2.94 | 0.301 | -0.16 | DUSUK GUVEN (n=49) |
| GARTLEY | SHORT | 240 | PRZ_FALSE_START | 368 | 33.15 | 0.44 | -0.515 | -0.93 | GUVENILIR |

## Ham Veri

Ham hucre tablosu: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\harmonic_xabcd_summary.csv`
