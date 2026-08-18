# Momentum Confluence -- Koşul Ablasyonu Optimizasyon Backtesti

Oluşturulma: 2026-08-18 19:15 UTC

## Kapsam

Sembol sayısı: 657 · Zaman dilimleri: 1D, 240 · Backtest derinliği: ~2.0 yıl · Varyant sayısı: 19 (bkz. `src/analysis/momentum_confluence_variants.py::VARIANTS`). V1_BASELINE/V2_BASELINE, `MOMENTUM_CONFLUENCE_BACKTEST.md`deki orijinal V1/V2 sonuçlarıyla PARITY doğrulanmıştır (bkz. commit notu) -- aradaki KÜÇÜK sayısal farklar (varsa) SADECE bu koşunun farklı n_bars/tarih penceresinden kaynaklanabilir, mantık AYNIDIR.

- `min_trades_show=30` altındaki hücreler ASLA gizlenmez.

## Sonuçlar (R-multiple bazlı, PF'ye göre sıralı)

| Varyant | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Güven |
|---|---|---|---|---|---|---|---|
| V2_ARTI_MACD | 240 | 593 | 60.54 | 1.47 | -0.066 | -0.67 | GUVENILIR |
| V2_YESILSIZ | 240 | 1095 | 59.54 | 1.41 | 0.038 | -0.91 | GUVENILIR |
| V2_ARTI_RSI | 240 | 1008 | 59.82 | 1.41 | 0.020 | -0.87 | GUVENILIR |
| V2_GEVSEK_HACIM | 240 | 1284 | 59.74 | 1.41 | 0.047 | -1.02 | GUVENILIR |
| V2_BASELINE | 240 | 1040 | 59.81 | 1.41 | 0.024 | -0.89 | GUVENILIR |
| V2_ARTI_STOCHRSI | 240 | 980 | 59.18 | 1.37 | 0.001 | -0.87 | GUVENILIR |
| V1_ARTI_WT | 240 | 1911 | 58.45 | 1.35 | 0.080 | -1.36 | GUVENILIR |
| V2_ARTI_BB | 240 | 862 | 58.58 | 1.33 | -0.035 | -0.84 | GUVENILIR |
| V1_ARTI_MACD | 240 | 2431 | 58.29 | 1.32 | 0.078 | -1.63 | GUVENILIR |
| V1_ARTI_RSI | 240 | 3325 | 57.23 | 1.26 | 0.074 | -2.11 | GUVENILIR |
| V1_ARTI_YESIL | 240 | 4219 | 57.53 | 1.26 | 0.085 | -2.42 | GUVENILIR |
| V1_ARTI_SIKI_EMA | 240 | 2704 | 57.47 | 1.26 | 0.063 | -1.79 | GUVENILIR |
| V1_ARTI_MACD | 1D | 1006 | 59.44 | 1.26 | 0.094 | -0.76 | GUVENILIR |
| V1_HACIM_GEVSEK | 240 | 5832 | 57.17 | 1.25 | 0.090 | -2.97 | GUVENILIR |
| V1_ARTI_STOCHRSI | 240 | 3631 | 56.90 | 1.25 | 0.076 | -2.24 | GUVENILIR |
| V1_BASELINE | 240 | 4438 | 57.08 | 1.25 | 0.082 | -2.52 | GUVENILIR |
| V2_HACIM_BANTSIZ | 240 | 1846 | 57.20 | 1.24 | 0.028 | -1.40 | GUVENILIR |
| V1_ARTI_BB | 240 | 4029 | 56.61 | 1.23 | 0.069 | -2.43 | GUVENILIR |
| V1_HACIM_GEVSEK | 1D | 2289 | 57.14 | 1.19 | 0.087 | -1.42 | GUVENILIR |
| V1_BASELINE | 1D | 1580 | 57.47 | 1.18 | 0.085 | -1.07 | GUVENILIR |
| V1_ARTI_SIKI_EMA | 1D | 1242 | 57.33 | 1.17 | 0.094 | -0.93 | GUVENILIR |
| V1_HACIM_BANTSIZ | 240 | 6499 | 55.70 | 1.17 | 0.061 | -3.27 | GUVENILIR |
| V1_ARTI_YESIL | 1D | 1533 | 57.34 | 1.17 | 0.083 | -1.05 | GUVENILIR |
| V1_HACIMSIZ | 240 | 10735 | 54.95 | 1.15 | 0.059 | -4.54 | GUVENILIR |
| V2_ARTI_MACD | 1D | 321 | 58.26 | 1.14 | 0.058 | -0.51 | GUVENILIR |
| V1_HACIMSIZ | 1D | 4260 | 55.19 | 1.12 | 0.057 | -2.24 | GUVENILIR |
| V1_ARTI_BB | 1D | 1441 | 56.21 | 1.12 | 0.067 | -1.05 | GUVENILIR |
| V1_HACIM_BANTSIZ | 1D | 2096 | 56.73 | 1.11 | 0.054 | -1.31 | GUVENILIR |
| V1_ARTI_RSI | 1D | 1316 | 56.38 | 1.11 | 0.060 | -0.98 | GUVENILIR |
| V1_ARTI_STOCHRSI | 1D | 1212 | 55.94 | 1.10 | 0.060 | -0.94 | GUVENILIR |
| V2_GEVSEK_HACIM | 1D | 695 | 55.40 | 1.07 | 0.029 | -0.73 | GUVENILIR |
| V1_ARTI_WT | 1D | 704 | 55.54 | 1.05 | 0.010 | -0.72 | GUVENILIR |
| V2_YESILSIZ | 1D | 543 | 56.35 | 1.05 | 0.021 | -0.64 | GUVENILIR |
| V2_BASELINE | 1D | 527 | 55.98 | 1.01 | 0.007 | -0.64 | GUVENILIR |
| V2_ARTI_RSI | 1D | 509 | 55.60 | 0.98 | -0.006 | -0.63 | GUVENILIR |
| V2_ARTI_BB | 1D | 457 | 54.49 | 0.97 | -0.014 | -0.65 | GUVENILIR |
| V2_ARTI_STOCHRSI | 1D | 497 | 55.13 | 0.96 | -0.015 | -0.66 | GUVENILIR |
| V2_HACIM_BANTSIZ | 1D | 739 | 54.94 | 0.96 | -0.017 | -0.76 | GUVENILIR |

## Ham Veri

`C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\momentum_confluence_optimizasyon_summary.csv`
