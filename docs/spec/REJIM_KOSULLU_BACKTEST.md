# Rejim Kosullu Backtest -- Momentum Confluence + Harmonik XABCD

Olusturulma: 2026-08-19 19:07 UTC

## Kapsam

Sembol: 657 · TF: 1D · Toplam etiketli sinyal: 30852 · Rejim esikleri: ADX14>=25=TREND, ATR/close 252-gunluk yuzdelik>=%50=YUKSEK_VOL

## Trend vs Yatay -- ozet (tum varyant/formasyonlar TOPLANMIS)

| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|
| MOMENTUM | TREND | 1119 | 53.62 | 1.09 | 0.061 | guvenilir |
| MOMENTUM | YATAY | 3386 | 55.02 | 1.10 | 0.039 | guvenilir |
| HARMONIK | TREND | 1447 | 38.91 | 1.05 | -0.592 | guvenilir |
| HARMONIK | YATAY | 3065 | 41.53 | 1.00 | -0.004 | guvenilir |

## Yuksek vs Dusuk Oynaklik -- ozet (tum varyant/formasyonlar TOPLANMIS)

| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|
| MOMENTUM | YUKSEK_VOL | 1214 | 56.59 | 1.25 | 0.136 | guvenilir |
| MOMENTUM | DUSUK_VOL | 3295 | 54.05 | 1.04 | 0.012 | guvenilir |
| HARMONIK | YUKSEK_VOL | 1758 | 43.57 | 1.21 | -0.330 | guvenilir |
| HARMONIK | DUSUK_VOL | 2768 | 38.95 | 0.90 | -0.105 | guvenilir |

## Hurst Rejimi -- ozet (Strateji kaynakları/gecikme_direncli_stratejiler.md'den uyarlandi)

| Sistem | Rejim | n | Win % | PF | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|
| MOMENTUM | TRENDING_H | 2805 | 54.19 | 1.06 | 0.034 | guvenilir |
| MOMENTUM | MEAN_REV_H | 373 | 58.18 | 1.37 | 0.141 | guvenilir |
| MOMENTUM | NOTR_H | 1341 | 54.88 | 1.11 | 0.042 | guvenilir |
| HARMONIK | TRENDING_H | 2770 | 39.82 | 0.99 | -0.299 | guvenilir |
| HARMONIK | MEAN_REV_H | 414 | 41.55 | 1.11 | 0.031 | guvenilir |
| HARMONIK | NOTR_H | 1370 | 42.34 | 1.01 | -0.050 | guvenilir |

## Gap Bolgesi -- ozet (PHASE7_2_STRATEGY_UPDATE_REPORT.md'den uyarlandi, BIST kalibrasyonu)

A=acilis gap'i <=0.5xATR (normal) · B=0.5-2.0xATR (sicrama) · C=>2.0xATR (asiri, kaynak rapor iptal onerir)

| Sistem | Bolge | n | Win % | PF | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|
| MOMENTUM | A_NORMAL | 3799 | 55.44 | 1.11 | 0.052 | guvenilir |
| MOMENTUM | B_SICRAMA | 656 | 53.51 | 0.99 | 0.012 | guvenilir |
| MOMENTUM | C_ASIRI | 52 | 15.38 | 0.28 | -0.101 | kucuk |
| HARMONIK | A_NORMAL | 3998 | 38.52 | 0.95 | -0.273 | guvenilir |
| HARMONIK | B_SICRAMA | 462 | 56.71 | 1.91 | 0.432 | guvenilir |
| HARMONIK | C_ASIRI | 49 | 67.35 | 4.59 | 0.513 | kucuk |

## Detay -- her varyant/formasyon x tam rejim (trend x vol, 4 kova)

| Sistem | Varyant/Formasyon | Yon | Rejim | n | Win % | PF | Guven |
|---|---|---|---|---|---|---|---|
| HARMONIK | ABCD | LONG | TREND+YUKSEK_VOL | 178 | 41.01 | 1.28 | guvenilir |
| HARMONIK | ABCD | LONG | TREND+DUSUK_VOL | 124 | 39.52 | 1.20 | guvenilir |
| HARMONIK | ABCD | LONG | YATAY+YUKSEK_VOL | 461 | 49.67 | 1.57 | guvenilir |
| HARMONIK | ABCD | LONG | YATAY+DUSUK_VOL | 720 | 38.47 | 0.88 | guvenilir |
| HARMONIK | ABCD | SHORT | TREND+YUKSEK_VOL | 367 | 42.78 | 1.14 | guvenilir |
| HARMONIK | ABCD | SHORT | TREND+DUSUK_VOL | 438 | 36.30 | 1.02 | guvenilir |
| HARMONIK | ABCD | SHORT | YATAY+YUKSEK_VOL | 307 | 43.32 | 0.89 | guvenilir |
| HARMONIK | ABCD | SHORT | YATAY+DUSUK_VOL | 797 | 41.66 | 0.92 | guvenilir |
| HARMONIK | BAT | LONG | TREND+YUKSEK_VOL | 35 | 34.29 | 0.35 | kucuk |
| HARMONIK | BAT | LONG | TREND+DUSUK_VOL | 14 | 50.00 | 0.91 | kucuk |
| HARMONIK | BAT | LONG | YATAY+YUKSEK_VOL | 70 | 35.71 | 0.68 | kucuk |
| HARMONIK | BAT | LONG | YATAY+DUSUK_VOL | 89 | 34.83 | 0.65 | kucuk |
| HARMONIK | BAT | SHORT | TREND+YUKSEK_VOL | 24 | 45.83 | 1.45 | kucuk |
| HARMONIK | BAT | SHORT | TREND+DUSUK_VOL | 43 | 32.56 | 0.47 | kucuk |
| HARMONIK | BAT | SHORT | YATAY+YUKSEK_VOL | 55 | 49.09 | 0.88 | kucuk |
| HARMONIK | BAT | SHORT | YATAY+DUSUK_VOL | 136 | 38.24 | 0.91 | guvenilir |
| HARMONIK | BUTTERFLY | LONG | TREND+YUKSEK_VOL | 31 | 38.71 | 1.28 | kucuk |
| HARMONIK | BUTTERFLY | LONG | TREND+DUSUK_VOL | 16 | 31.25 | 0.63 | kucuk |
| HARMONIK | BUTTERFLY | LONG | YATAY+YUKSEK_VOL | 102 | 41.18 | 1.03 | guvenilir |
| HARMONIK | BUTTERFLY | LONG | YATAY+DUSUK_VOL | 165 | 37.58 | 0.86 | guvenilir |
| HARMONIK | BUTTERFLY | SHORT | TREND+YUKSEK_VOL | 41 | 53.66 | 1.74 | kucuk |
| HARMONIK | BUTTERFLY | SHORT | TREND+DUSUK_VOL | 69 | 42.03 | 0.74 | kucuk |
| HARMONIK | BUTTERFLY | SHORT | YATAY+YUKSEK_VOL | 47 | 36.17 | 0.73 | kucuk |
| HARMONIK | BUTTERFLY | SHORT | YATAY+DUSUK_VOL | 123 | 41.46 | 0.95 | guvenilir |
| HARMONIK | CRAB | LONG | TREND+YUKSEK_VOL | 18 | 55.56 | 1.48 | kucuk |
| HARMONIK | CRAB | LONG | TREND+DUSUK_VOL | 13 | 53.85 | 2.01 | kucuk |
| HARMONIK | CRAB | LONG | YATAY+YUKSEK_VOL | 44 | 47.73 | 2.17 | kucuk |
| HARMONIK | CRAB | LONG | YATAY+DUSUK_VOL | 42 | 47.62 | 1.20 | kucuk |
| HARMONIK | CRAB | SHORT | TREND+YUKSEK_VOL | 48 | 31.25 | 0.49 | kucuk |
| HARMONIK | CRAB | SHORT | TREND+DUSUK_VOL | 65 | 33.85 | 0.60 | kucuk |
| HARMONIK | CRAB | SHORT | YATAY+YUKSEK_VOL | 33 | 66.67 | 1.93 | kucuk |
| HARMONIK | CRAB | SHORT | YATAY+DUSUK_VOL | 78 | 26.92 | 0.35 | kucuk |
| HARMONIK | GARTLEY | LONG | TREND+YUKSEK_VOL | 48 | 43.75 | 0.78 | kucuk |
| HARMONIK | GARTLEY | LONG | TREND+DUSUK_VOL | 28 | 46.43 | 1.01 | kucuk |
| HARMONIK | GARTLEY | LONG | YATAY+YUKSEK_VOL | 123 | 42.28 | 1.56 | guvenilir |
| HARMONIK | GARTLEY | LONG | YATAY+DUSUK_VOL | 148 | 37.16 | 0.77 | guvenilir |
| HARMONIK | GARTLEY | SHORT | TREND+YUKSEK_VOL | 23 | 56.52 | 2.48 | kucuk |
| HARMONIK | GARTLEY | SHORT | TREND+DUSUK_VOL | 36 | 47.22 | 0.79 | kucuk |
| HARMONIK | GARTLEY | SHORT | YATAY+YUKSEK_VOL | 70 | 47.14 | 0.72 | kucuk |
| HARMONIK | GARTLEY | SHORT | YATAY+DUSUK_VOL | 174 | 40.23 | 0.86 | guvenilir |
| MOMENTUM | V1_ARTI_BB | LONG | TREND+YUKSEK_VOL | 109 | 56.88 | 1.43 | guvenilir |
| MOMENTUM | V1_ARTI_BB | LONG | TREND+DUSUK_VOL | 254 | 51.57 | 0.92 | guvenilir |
| MOMENTUM | V1_ARTI_BB | LONG | YATAY+YUKSEK_VOL | 295 | 58.31 | 1.44 | guvenilir |
| MOMENTUM | V1_ARTI_BB | LONG | YATAY+DUSUK_VOL | 880 | 55.11 | 1.01 | guvenilir |
| MOMENTUM | V1_ARTI_MACD | LONG | TREND+YUKSEK_VOL | 46 | 67.39 | 2.02 | kucuk |
| MOMENTUM | V1_ARTI_MACD | LONG | TREND+DUSUK_VOL | 186 | 53.23 | 1.02 | guvenilir |
| MOMENTUM | V1_ARTI_MACD | LONG | YATAY+YUKSEK_VOL | 162 | 65.43 | 2.24 | guvenilir |
| MOMENTUM | V1_ARTI_MACD | LONG | YATAY+DUSUK_VOL | 662 | 57.70 | 1.09 | guvenilir |
| MOMENTUM | V1_ARTI_RSI | LONG | TREND+YUKSEK_VOL | 103 | 53.40 | 1.22 | guvenilir |
| MOMENTUM | V1_ARTI_RSI | LONG | TREND+DUSUK_VOL | 184 | 49.46 | 0.79 | guvenilir |
| MOMENTUM | V1_ARTI_RSI | LONG | YATAY+YUKSEK_VOL | 294 | 59.18 | 1.51 | guvenilir |
| MOMENTUM | V1_ARTI_RSI | LONG | YATAY+DUSUK_VOL | 826 | 55.69 | 1.01 | guvenilir |
| MOMENTUM | V1_ARTI_SIKI_EMA | LONG | TREND+YUKSEK_VOL | 78 | 56.41 | 1.60 | kucuk |
| MOMENTUM | V1_ARTI_SIKI_EMA | LONG | TREND+DUSUK_VOL | 216 | 51.85 | 0.92 | guvenilir |
| MOMENTUM | V1_ARTI_SIKI_EMA | LONG | YATAY+YUKSEK_VOL | 248 | 61.29 | 1.69 | guvenilir |
| MOMENTUM | V1_ARTI_SIKI_EMA | LONG | YATAY+DUSUK_VOL | 780 | 56.15 | 1.03 | guvenilir |
| MOMENTUM | V1_ARTI_STOCHRSI | LONG | TREND+YUKSEK_VOL | 83 | 50.60 | 1.18 | kucuk |
| MOMENTUM | V1_ARTI_STOCHRSI | LONG | TREND+DUSUK_VOL | 185 | 49.19 | 0.79 | guvenilir |
| MOMENTUM | V1_ARTI_STOCHRSI | LONG | YATAY+YUKSEK_VOL | 265 | 58.11 | 1.50 | guvenilir |
| MOMENTUM | V1_ARTI_STOCHRSI | LONG | YATAY+DUSUK_VOL | 800 | 56.12 | 1.03 | guvenilir |
| MOMENTUM | V1_ARTI_WT | LONG | TREND+YUKSEK_VOL | 41 | 48.78 | 0.57 | kucuk |
| MOMENTUM | V1_ARTI_WT | LONG | TREND+DUSUK_VOL | 86 | 48.84 | 0.74 | kucuk |
| MOMENTUM | V1_ARTI_WT | LONG | YATAY+YUKSEK_VOL | 161 | 56.52 | 1.65 | guvenilir |
| MOMENTUM | V1_ARTI_WT | LONG | YATAY+DUSUK_VOL | 473 | 56.24 | 0.98 | guvenilir |
| MOMENTUM | V1_ARTI_YESIL | LONG | TREND+YUKSEK_VOL | 111 | 57.66 | 1.47 | guvenilir |
| MOMENTUM | V1_ARTI_YESIL | LONG | TREND+DUSUK_VOL | 263 | 51.71 | 0.95 | guvenilir |
| MOMENTUM | V1_ARTI_YESIL | LONG | YATAY+YUKSEK_VOL | 299 | 59.53 | 1.56 | guvenilir |
| MOMENTUM | V1_ARTI_YESIL | LONG | YATAY+DUSUK_VOL | 954 | 56.71 | 1.05 | guvenilir |
| MOMENTUM | V1_BASELINE | LONG | TREND+YUKSEK_VOL | 116 | 56.90 | 1.40 | guvenilir |
| MOMENTUM | V1_BASELINE | LONG | TREND+DUSUK_VOL | 271 | 51.66 | 0.92 | guvenilir |
| MOMENTUM | V1_BASELINE | LONG | YATAY+YUKSEK_VOL | 312 | 59.62 | 1.56 | guvenilir |
| MOMENTUM | V1_BASELINE | LONG | YATAY+DUSUK_VOL | 975 | 56.82 | 1.07 | guvenilir |
| MOMENTUM | V1_HACIMSIZ | LONG | TREND+YUKSEK_VOL | 378 | 57.67 | 1.33 | guvenilir |
| MOMENTUM | V1_HACIMSIZ | LONG | TREND+DUSUK_VOL | 742 | 51.48 | 0.98 | guvenilir |
| MOMENTUM | V1_HACIMSIZ | LONG | YATAY+YUKSEK_VOL | 839 | 56.02 | 1.22 | guvenilir |
| MOMENTUM | V1_HACIMSIZ | LONG | YATAY+DUSUK_VOL | 2558 | 54.85 | 1.06 | guvenilir |
| MOMENTUM | V1_HACIM_BANTSIZ | LONG | TREND+YUKSEK_VOL | 138 | 58.70 | 1.42 | guvenilir |
| MOMENTUM | V1_HACIM_BANTSIZ | LONG | TREND+DUSUK_VOL | 367 | 50.68 | 0.87 | guvenilir |
| MOMENTUM | V1_HACIM_BANTSIZ | LONG | YATAY+YUKSEK_VOL | 407 | 59.95 | 1.49 | guvenilir |
| MOMENTUM | V1_HACIM_BANTSIZ | LONG | YATAY+DUSUK_VOL | 1296 | 56.25 | 1.02 | guvenilir |
| MOMENTUM | V1_HACIM_GEVSEK | LONG | TREND+YUKSEK_VOL | 161 | 59.63 | 1.51 | guvenilir |
| MOMENTUM | V1_HACIM_GEVSEK | LONG | TREND+DUSUK_VOL | 397 | 52.14 | 1.02 | guvenilir |
| MOMENTUM | V1_HACIM_GEVSEK | LONG | YATAY+YUKSEK_VOL | 445 | 58.43 | 1.42 | guvenilir |
| MOMENTUM | V1_HACIM_GEVSEK | LONG | YATAY+DUSUK_VOL | 1412 | 56.59 | 1.09 | guvenilir |
| MOMENTUM | V2_ARTI_BB | LONG | TREND+YUKSEK_VOL | 23 | 52.17 | 0.55 | kucuk |
| MOMENTUM | V2_ARTI_BB | LONG | TREND+DUSUK_VOL | 60 | 48.33 | 0.78 | kucuk |
| MOMENTUM | V2_ARTI_BB | LONG | YATAY+YUKSEK_VOL | 115 | 55.65 | 1.60 | guvenilir |
| MOMENTUM | V2_ARTI_BB | LONG | YATAY+DUSUK_VOL | 307 | 53.75 | 0.85 | guvenilir |
| MOMENTUM | V2_ARTI_MACD | LONG | TREND+YUKSEK_VOL | 4 | 50.00 | 0.86 | cok kucuk |
| MOMENTUM | V2_ARTI_MACD | LONG | TREND+DUSUK_VOL | 38 | 50.00 | 0.63 | kucuk |
| MOMENTUM | V2_ARTI_MACD | LONG | YATAY+YUKSEK_VOL | 65 | 63.08 | 2.63 | kucuk |
| MOMENTUM | V2_ARTI_MACD | LONG | YATAY+DUSUK_VOL | 235 | 59.15 | 1.05 | guvenilir |
| MOMENTUM | V2_ARTI_RSI | LONG | TREND+YUKSEK_VOL | 25 | 52.00 | 0.54 | kucuk |
| MOMENTUM | V2_ARTI_RSI | LONG | TREND+DUSUK_VOL | 64 | 46.88 | 0.65 | kucuk |
| MOMENTUM | V2_ARTI_RSI | LONG | YATAY+YUKSEK_VOL | 123 | 58.54 | 1.77 | guvenilir |
| MOMENTUM | V2_ARTI_RSI | LONG | YATAY+DUSUK_VOL | 351 | 55.56 | 0.89 | guvenilir |
| MOMENTUM | V2_ARTI_STOCHRSI | LONG | TREND+YUKSEK_VOL | 24 | 50.00 | 0.54 | kucuk |
| MOMENTUM | V2_ARTI_STOCHRSI | LONG | TREND+DUSUK_VOL | 63 | 47.62 | 0.70 | kucuk |
| MOMENTUM | V2_ARTI_STOCHRSI | LONG | YATAY+YUKSEK_VOL | 119 | 57.14 | 1.71 | guvenilir |
| MOMENTUM | V2_ARTI_STOCHRSI | LONG | YATAY+DUSUK_VOL | 350 | 55.43 | 0.89 | guvenilir |
| MOMENTUM | V2_BASELINE | LONG | TREND+YUKSEK_VOL | 26 | 50.00 | 0.50 | kucuk |
| MOMENTUM | V2_BASELINE | LONG | TREND+DUSUK_VOL | 66 | 48.48 | 0.73 | kucuk |
| MOMENTUM | V2_BASELINE | LONG | YATAY+YUKSEK_VOL | 123 | 58.54 | 1.77 | guvenilir |
| MOMENTUM | V2_BASELINE | LONG | YATAY+DUSUK_VOL | 361 | 55.96 | 0.91 | guvenilir |
| MOMENTUM | V2_GEVSEK_HACIM | LONG | TREND+YUKSEK_VOL | 36 | 50.00 | 0.75 | kucuk |
| MOMENTUM | V2_GEVSEK_HACIM | LONG | TREND+DUSUK_VOL | 94 | 51.06 | 0.91 | kucuk |
| MOMENTUM | V2_GEVSEK_HACIM | LONG | YATAY+YUKSEK_VOL | 166 | 54.22 | 1.40 | guvenilir |
| MOMENTUM | V2_GEVSEK_HACIM | LONG | YATAY+DUSUK_VOL | 462 | 56.28 | 1.02 | guvenilir |
| MOMENTUM | V2_HACIM_BANTSIZ | LONG | TREND+YUKSEK_VOL | 29 | 55.17 | 0.60 | kucuk |
| MOMENTUM | V2_HACIM_BANTSIZ | LONG | TREND+DUSUK_VOL | 92 | 46.74 | 0.68 | kucuk |
| MOMENTUM | V2_HACIM_BANTSIZ | LONG | YATAY+YUKSEK_VOL | 168 | 58.33 | 1.60 | guvenilir |
| MOMENTUM | V2_HACIM_BANTSIZ | LONG | YATAY+DUSUK_VOL | 505 | 54.65 | 0.87 | guvenilir |
| MOMENTUM | V2_YESILSIZ | LONG | TREND+YUKSEK_VOL | 26 | 50.00 | 0.50 | kucuk |
| MOMENTUM | V2_YESILSIZ | LONG | TREND+DUSUK_VOL | 67 | 49.25 | 0.73 | kucuk |
| MOMENTUM | V2_YESILSIZ | LONG | YATAY+YUKSEK_VOL | 130 | 58.46 | 1.77 | guvenilir |
| MOMENTUM | V2_YESILSIZ | LONG | YATAY+DUSUK_VOL | 369 | 56.10 | 0.93 | guvenilir |

## Ozet -- her varyant/formasyon icin EN IYI rejim (n>=10 hucreler arasindan)

| Sistem | Varyant/Formasyon | Yon | En iyi rejim | PF | n |
|---|---|---|---|---|---|
| MOMENTUM | V2_ARTI_MACD | LONG | YATAY+YUKSEK_VOL | 2.63 | 65 |
| HARMONIK | GARTLEY | SHORT | TREND+YUKSEK_VOL | 2.48 | 23 |
| MOMENTUM | V1_ARTI_MACD | LONG | YATAY+YUKSEK_VOL | 2.24 | 162 |
| HARMONIK | CRAB | LONG | YATAY+YUKSEK_VOL | 2.17 | 44 |
| HARMONIK | CRAB | SHORT | YATAY+YUKSEK_VOL | 1.93 | 33 |
| MOMENTUM | V2_ARTI_RSI | LONG | YATAY+YUKSEK_VOL | 1.77 | 123 |
| MOMENTUM | V2_BASELINE | LONG | YATAY+YUKSEK_VOL | 1.77 | 123 |
| MOMENTUM | V2_YESILSIZ | LONG | YATAY+YUKSEK_VOL | 1.77 | 130 |
| HARMONIK | BUTTERFLY | SHORT | TREND+YUKSEK_VOL | 1.74 | 41 |
| MOMENTUM | V2_ARTI_STOCHRSI | LONG | YATAY+YUKSEK_VOL | 1.71 | 119 |
| MOMENTUM | V1_ARTI_SIKI_EMA | LONG | YATAY+YUKSEK_VOL | 1.69 | 248 |
| MOMENTUM | V1_ARTI_WT | LONG | YATAY+YUKSEK_VOL | 1.65 | 161 |
| MOMENTUM | V2_ARTI_BB | LONG | YATAY+YUKSEK_VOL | 1.60 | 115 |
| MOMENTUM | V2_HACIM_BANTSIZ | LONG | YATAY+YUKSEK_VOL | 1.60 | 168 |
| HARMONIK | ABCD | LONG | YATAY+YUKSEK_VOL | 1.57 | 461 |
| MOMENTUM | V1_ARTI_YESIL | LONG | YATAY+YUKSEK_VOL | 1.56 | 299 |
| HARMONIK | GARTLEY | LONG | YATAY+YUKSEK_VOL | 1.56 | 123 |
| MOMENTUM | V1_BASELINE | LONG | YATAY+YUKSEK_VOL | 1.56 | 312 |
| MOMENTUM | V1_HACIM_GEVSEK | LONG | TREND+YUKSEK_VOL | 1.51 | 161 |
| MOMENTUM | V1_ARTI_RSI | LONG | YATAY+YUKSEK_VOL | 1.51 | 294 |
| MOMENTUM | V1_ARTI_STOCHRSI | LONG | YATAY+YUKSEK_VOL | 1.50 | 265 |
| MOMENTUM | V1_HACIM_BANTSIZ | LONG | YATAY+YUKSEK_VOL | 1.49 | 407 |
| HARMONIK | BAT | SHORT | TREND+YUKSEK_VOL | 1.45 | 24 |
| MOMENTUM | V1_ARTI_BB | LONG | YATAY+YUKSEK_VOL | 1.44 | 295 |
| MOMENTUM | V2_GEVSEK_HACIM | LONG | YATAY+YUKSEK_VOL | 1.40 | 166 |
| MOMENTUM | V1_HACIMSIZ | LONG | TREND+YUKSEK_VOL | 1.33 | 378 |
| HARMONIK | BUTTERFLY | LONG | TREND+YUKSEK_VOL | 1.28 | 31 |
| HARMONIK | ABCD | SHORT | TREND+YUKSEK_VOL | 1.14 | 367 |
| HARMONIK | BAT | LONG | TREND+DUSUK_VOL | 0.91 | 14 |

## Ham Veri

Sinyal basina rejim etiketleri: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\rejim_kosullu_events.csv`
