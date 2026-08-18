# Momentum Confluence -- Koşul Ablasyonu Optimizasyon Backtesti

Oluşturulma: 2026-08-18 18:07 UTC

## Kapsam

Sembol sayısı: 657 · Zaman dilimleri: 1D, 240 · Backtest derinliği: ~2.0 yıl · Varyant sayısı: 11 (bkz. `src/analysis/momentum_confluence_variants.py::VARIANTS`). V1_BASELINE/V2_BASELINE, `MOMENTUM_CONFLUENCE_BACKTEST.md`deki orijinal V1/V2 sonuçlarıyla PARITY doğrulanmıştır (bkz. commit notu) -- aradaki KÜÇÜK sayısal farklar (varsa) SADECE bu koşunun farklı n_bars/tarih penceresinden kaynaklanabilir, mantık AYNIDIR.

- `min_trades_show=30` altındaki hücreler ASLA gizlenmez.

## Sonuçlar (R-multiple bazlı, PF'ye göre sıralı)

| Varyant | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Güven |
|---|---|---|---|---|---|---|---|
| V2_ARTI_HACIM_BANDI | 240 | 1042 | 59.88 | 1.41 | 0.025 | -0.89 | GUVENILIR |
| V2_GEVSEK_HACIM | 240 | 2091 | 57.44 | 1.26 | 0.042 | -1.52 | GUVENILIR |
| V1_HACIM_BANDI | 240 | 4437 | 57.07 | 1.25 | 0.083 | -2.52 | GUVENILIR |
| V2_YESILSIZ | 240 | 1927 | 57.03 | 1.25 | 0.037 | -1.43 | GUVENILIR |
| V2_BASELINE | 240 | 1847 | 57.23 | 1.24 | 0.029 | -1.40 | GUVENILIR |
| V1_ARTI_WT | 240 | 2992 | 56.65 | 1.23 | 0.062 | -1.95 | GUVENILIR |
| V1_HACIM_GEVSEK | 240 | 7876 | 56.04 | 1.19 | 0.071 | -3.67 | GUVENILIR |
| V1_ARTI_YESIL | 240 | 6215 | 56.06 | 1.18 | 0.064 | -3.17 | GUVENILIR |
| V1_HACIM_BANDI | 1D | 1580 | 57.47 | 1.18 | 0.085 | -1.07 | GUVENILIR |
| V1_BASELINE | 240 | 6500 | 55.71 | 1.17 | 0.061 | -3.27 | GUVENILIR |
| V1_ARTI_SIKI_EMA | 240 | 4343 | 55.74 | 1.17 | 0.047 | -2.58 | GUVENILIR |
| V1_HACIMSIZ | 240 | 10736 | 54.95 | 1.15 | 0.059 | -4.54 | GUVENILIR |
| V1_HACIM_GEVSEK | 1D | 2802 | 56.71 | 1.14 | 0.065 | -1.63 | GUVENILIR |
| V1_HACIMSIZ | 1D | 4256 | 55.19 | 1.12 | 0.057 | -2.24 | GUVENILIR |
| V1_ARTI_YESIL | 1D | 2030 | 56.90 | 1.11 | 0.056 | -1.28 | GUVENILIR |
| V1_BASELINE | 1D | 2096 | 56.73 | 1.11 | 0.054 | -1.31 | GUVENILIR |
| V1_ARTI_SIKI_EMA | 1D | 1694 | 56.26 | 1.09 | 0.053 | -1.15 | GUVENILIR |
| V2_ARTI_HACIM_BANDI | 1D | 529 | 55.95 | 1.02 | 0.008 | -0.64 | GUVENILIR |
| V2_GEVSEK_HACIM | 1D | 910 | 54.73 | 1.01 | 0.005 | -0.84 | GUVENILIR |
| V1_ARTI_WT | 1D | 965 | 54.82 | 0.98 | -0.014 | -0.86 | GUVENILIR |
| V2_YESILSIZ | 1D | 767 | 54.76 | 0.96 | -0.014 | -0.77 | GUVENILIR |
| V2_BASELINE | 1D | 741 | 54.93 | 0.96 | -0.016 | -0.76 | GUVENILIR |

## Ham Veri

`C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\momentum_confluence_optimizasyon_summary.csv`
