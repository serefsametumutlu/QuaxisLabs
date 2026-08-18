# XABCD V2.1 (X-noktali) Arastirmasi -- Confirmed vs PRZ Kalitesi

Olusturulma: 2026-08-18 13:37 UTC

## Kapsam

Sembol sayisi: 657 · Zaman dilimleri: 1D, 240 · Backtest derinligi: ~5.0 yil · Para birimi: TRY. Formasyonlar: GARTLEY/BAT/BUTTERFLY/CRAB, X-noktali (V2.1) literatur-dogru CD/BC + XD/XA tanimiyla -- `pine/harmonic_formations_v1_indicator.pine` (V2.1, XD yon duzeltmesi dahil) ile Pine-parity.

## ⚠️ METODOLOJI UYARISI

`min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak etiketlenip tabloda TUTULUR. "En iyi" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir.

## PRZ Dogrulanma (Vindication) Oranlari

Bir PRZ erken-uyarisi "dogrulanmis" sayilir eger AYNI C pivotu icin SONRADAN gercekten onayli bir D sinyali olustuysa (`harmonic_xabcd.match_prz_to_confirmed`). Dusuk oran = PRZ'nin "alakasiz" gorunen kismi.

| Formasyon | Yon | TF | PRZ Olay Sayisi | Dogrulanan | Dogrulanma Orani % |
|---|---|---|---|---|---|
| BAT | LONG | 1D | 247 | 45 | 18.22 |
| BAT | LONG | 240 | 530 | 114 | 21.51 |
| BAT | SHORT | 1D | 373 | 39 | 10.46 |
| BAT | SHORT | 240 | 620 | 84 | 13.55 |
| BUTTERFLY | LONG | 1D | 390 | 77 | 19.74 |
| BUTTERFLY | LONG | 240 | 702 | 113 | 16.10 |
| BUTTERFLY | SHORT | 1D | 402 | 42 | 10.45 |
| BUTTERFLY | SHORT | 240 | 720 | 55 | 7.64 |
| CRAB | LONG | 1D | 150 | 31 | 20.67 |
| CRAB | LONG | 240 | 346 | 61 | 17.63 |
| CRAB | SHORT | 1D | 297 | 31 | 10.44 |
| CRAB | SHORT | 240 | 483 | 61 | 12.63 |
| GARTLEY | LONG | 1D | 426 | 63 | 14.79 |
| GARTLEY | LONG | 240 | 739 | 95 | 12.86 |
| GARTLEY | SHORT | 1D | 428 | 36 | 8.41 |
| GARTLEY | SHORT | 240 | 680 | 72 | 10.59 |

## Kategori Karsilastirmasi (CONFIRMED vs PRZ_ALL vs PRZ_VINDICATED vs PRZ_FALSE_START)

| Formasyon | Yon | TF | Kategori | n | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|---|---|---|
| BAT | LONG | 1D | CONFIRMED | 33 | 60.61 | 1.13 | 0.051 | -0.36 | DUSUK GUVEN (n=33) |
| BAT | LONG | 1D | PRZ_ALL | 240 | 35.83 | 0.64 | -0.248 | -0.81 | GUVENILIR |
| BAT | LONG | 1D | PRZ_VINDICATED | 44 | 77.27 | 4.18 | 0.686 | -0.22 | DUSUK GUVEN (n=44) |
| BAT | LONG | 1D | PRZ_FALSE_START | 196 | 26.53 | 0.42 | -0.458 | -0.90 | GUVENILIR |
| BAT | LONG | 240 | CONFIRMED | 97 | 56.70 | 0.76 | -0.098 | -0.42 | DUSUK GUVEN (n=97) |
| BAT | LONG | 240 | PRZ_ALL | 499 | 37.27 | 0.90 | -0.065 | -0.98 | GUVENILIR |
| BAT | LONG | 240 | PRZ_VINDICATED | 110 | 65.45 | 3.09 | 0.765 | -0.36 | GUVENILIR |
| BAT | LONG | 240 | PRZ_FALSE_START | 389 | 29.31 | 0.62 | -0.300 | -1.07 | GUVENILIR |
| BAT | SHORT | 1D | CONFIRMED | 14 | 50.00 | 0.50 | -0.218 | -0.44 | GUVENSIZ (n=14) |
| BAT | SHORT | 1D | PRZ_ALL | 328 | 36.89 | 0.74 | -3.513 | -0.79 | GUVENILIR |
| BAT | SHORT | 1D | PRZ_VINDICATED | 32 | 81.25 | 5.50 | 0.733 | -0.17 | DUSUK GUVEN (n=32) |
| BAT | SHORT | 1D | PRZ_FALSE_START | 296 | 32.09 | 0.62 | -3.972 | -0.85 | GUVENILIR |
| BAT | SHORT | 240 | CONFIRMED | 54 | 50.00 | 0.80 | -0.078 | -0.42 | DUSUK GUVEN (n=54) |
| BAT | SHORT | 240 | PRZ_ALL | 516 | 38.18 | 0.76 | -0.181 | -0.99 | GUVENILIR |
| BAT | SHORT | 240 | PRZ_VINDICATED | 78 | 70.51 | 2.48 | 0.348 | -0.26 | DUSUK GUVEN (n=78) |
| BAT | SHORT | 240 | PRZ_FALSE_START | 438 | 32.42 | 0.66 | -0.275 | -1.06 | GUVENILIR |
| BUTTERFLY | LONG | 1D | CONFIRMED | 60 | 66.67 | 2.00 | 0.274 | -0.28 | DUSUK GUVEN (n=60) |
| BUTTERFLY | LONG | 1D | PRZ_ALL | 372 | 37.90 | 1.01 | 0.001 | -0.86 | GUVENILIR |
| BUTTERFLY | LONG | 1D | PRZ_VINDICATED | 73 | 75.34 | 5.93 | 1.123 | -0.24 | DUSUK GUVEN (n=73) |
| BUTTERFLY | LONG | 1D | PRZ_FALSE_START | 300 | 28.67 | 0.64 | -0.275 | -0.95 | GUVENILIR |
| BUTTERFLY | LONG | 240 | CONFIRMED | 82 | 45.12 | 0.40 | -0.312 | -0.55 | DUSUK GUVEN (n=82) |
| BUTTERFLY | LONG | 240 | PRZ_ALL | 662 | 33.99 | 0.92 | -0.115 | -1.19 | GUVENILIR |
| BUTTERFLY | LONG | 240 | PRZ_VINDICATED | 105 | 62.86 | 2.15 | 0.364 | -0.40 | GUVENILIR |
| BUTTERFLY | LONG | 240 | PRZ_FALSE_START | 558 | 28.49 | 0.81 | -0.206 | -1.22 | GUVENILIR |
| BUTTERFLY | SHORT | 1D | CONFIRMED | 28 | 60.71 | 0.81 | -0.065 | -0.35 | GUVENSIZ (n=28) |
| BUTTERFLY | SHORT | 1D | PRZ_ALL | 348 | 41.95 | 1.08 | 0.025 | -0.80 | GUVENILIR |
| BUTTERFLY | SHORT | 1D | PRZ_VINDICATED | 38 | 81.58 | 3.94 | 0.479 | -0.17 | DUSUK GUVEN (n=38) |
| BUTTERFLY | SHORT | 1D | PRZ_FALSE_START | 310 | 37.10 | 0.99 | -0.030 | -0.84 | GUVENILIR |
| BUTTERFLY | SHORT | 240 | CONFIRMED | 37 | 51.35 | 0.73 | -0.100 | -0.36 | DUSUK GUVEN (n=37) |
| BUTTERFLY | SHORT | 240 | PRZ_ALL | 612 | 34.97 | 0.65 | -0.308 | -1.12 | GUVENILIR |
| BUTTERFLY | SHORT | 240 | PRZ_VINDICATED | 48 | 79.17 | 4.26 | 0.621 | -0.21 | DUSUK GUVEN (n=48) |
| BUTTERFLY | SHORT | 240 | PRZ_FALSE_START | 564 | 31.21 | 0.56 | -0.387 | -1.14 | GUVENILIR |
| CRAB | LONG | 1D | CONFIRMED | 23 | 73.91 | 3.75 | 0.599 | -0.23 | GUVENSIZ (n=23) |
| CRAB | LONG | 1D | PRZ_ALL | 141 | 47.52 | 1.72 | 0.371 | -0.59 | GUVENILIR |
| CRAB | LONG | 1D | PRZ_VINDICATED | 30 | 93.33 | 24.93 | 1.589 | -0.07 | DUSUK GUVEN (n=30) |
| CRAB | LONG | 1D | PRZ_FALSE_START | 111 | 35.14 | 1.09 | 0.041 | -0.71 | GUVENILIR |
| CRAB | LONG | 240 | CONFIRMED | 47 | 63.83 | 1.05 | 0.036 | -0.39 | DUSUK GUVEN (n=47) |
| CRAB | LONG | 240 | PRZ_ALL | 322 | 35.09 | 0.78 | -0.183 | -0.95 | GUVENILIR |
| CRAB | LONG | 240 | PRZ_VINDICATED | 58 | 72.41 | 4.16 | 0.935 | -0.33 | DUSUK GUVEN (n=58) |
| CRAB | LONG | 240 | PRZ_FALSE_START | 264 | 26.89 | 0.50 | -0.429 | -1.02 | GUVENILIR |
| CRAB | SHORT | 1D | CONFIRMED | 21 | 57.14 | 1.49 | 0.183 | -0.42 | GUVENSIZ (n=21) |
| CRAB | SHORT | 1D | PRZ_ALL | 274 | 33.94 | 0.62 | -0.270 | -0.86 | GUVENILIR |
| CRAB | SHORT | 1D | PRZ_VINDICATED | 29 | 72.41 | 3.16 | 0.528 | -0.26 | GUVENSIZ (n=29) |
| CRAB | SHORT | 1D | PRZ_FALSE_START | 245 | 29.39 | 0.52 | -0.365 | -0.92 | GUVENILIR |
| CRAB | SHORT | 240 | CONFIRMED | 43 | 48.84 | 0.29 | -0.310 | -0.46 | DUSUK GUVEN (n=43) |
| CRAB | SHORT | 240 | PRZ_ALL | 420 | 38.33 | 0.95 | -0.182 | -0.93 | GUVENILIR |
| CRAB | SHORT | 240 | PRZ_VINDICATED | 56 | 76.79 | 4.31 | 0.820 | -0.26 | DUSUK GUVEN (n=56) |
| CRAB | SHORT | 240 | PRZ_FALSE_START | 365 | 32.60 | 0.78 | -0.335 | -0.99 | GUVENILIR |
| GARTLEY | LONG | 1D | CONFIRMED | 54 | 64.81 | 1.13 | 0.035 | -0.31 | DUSUK GUVEN (n=54) |
| GARTLEY | LONG | 1D | PRZ_ALL | 411 | 37.71 | 0.95 | -0.041 | -0.88 | GUVENILIR |
| GARTLEY | LONG | 1D | PRZ_VINDICATED | 61 | 70.49 | 3.78 | 0.705 | -0.28 | DUSUK GUVEN (n=61) |
| GARTLEY | LONG | 1D | PRZ_FALSE_START | 350 | 32.00 | 0.76 | -0.171 | -0.93 | GUVENILIR |
| GARTLEY | LONG | 240 | CONFIRMED | 73 | 65.75 | 0.93 | -0.021 | -0.35 | DUSUK GUVEN (n=73) |
| GARTLEY | LONG | 240 | PRZ_ALL | 682 | 35.63 | 0.79 | -0.222 | -1.20 | GUVENILIR |
| GARTLEY | LONG | 240 | PRZ_VINDICATED | 89 | 76.40 | 4.17 | 0.715 | -0.25 | DUSUK GUVEN (n=89) |
| GARTLEY | LONG | 240 | PRZ_FALSE_START | 595 | 29.58 | 0.63 | -0.361 | -1.26 | GUVENILIR |
| GARTLEY | SHORT | 1D | CONFIRMED | 20 | 50.00 | 0.31 | -0.251 | -0.37 | GUVENSIZ (n=20) |
| GARTLEY | SHORT | 1D | PRZ_ALL | 379 | 41.16 | 0.86 | -0.079 | -0.80 | GUVENILIR |
| GARTLEY | SHORT | 1D | PRZ_VINDICATED | 33 | 81.82 | 6.46 | 0.682 | -0.13 | DUSUK GUVEN (n=33) |
| GARTLEY | SHORT | 1D | PRZ_FALSE_START | 346 | 37.28 | 0.76 | -0.152 | -0.84 | GUVENILIR |
| GARTLEY | SHORT | 240 | CONFIRMED | 42 | 45.24 | 0.33 | -0.248 | -0.40 | DUSUK GUVEN (n=42) |
| GARTLEY | SHORT | 240 | PRZ_ALL | 588 | 39.29 | 0.67 | -0.295 | -0.98 | GUVENILIR |
| GARTLEY | SHORT | 240 | PRZ_VINDICATED | 62 | 77.42 | 2.73 | 0.316 | -0.19 | DUSUK GUVEN (n=62) |
| GARTLEY | SHORT | 240 | PRZ_FALSE_START | 526 | 34.79 | 0.60 | -0.366 | -1.04 | GUVENILIR |

## Ham Veri

Ham hucre tablosu: `data\abcd_cache\harmonic_xabcd_summary_5yil.csv`
