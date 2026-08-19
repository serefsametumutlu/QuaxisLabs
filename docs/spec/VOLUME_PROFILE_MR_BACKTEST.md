# Hacim Profili Ortalamaya Donus -- Tam BIST Backtest (YENI STRATEJI)

Olusturulma: 2026-08-19 19:21 UTC

## Strateji

D -20 barlik hacim profilinden POC/VAH/VAL turetilir. Fiyat VAL altina inip RSI(5)<30 aşırı satima duserse VE donus mumu (kapanis>acilis) olusursa LONG: TP1=POC, TP2=VAH, SL=VAL-1.0xATR. `ULTIMATE_5_STRATEGIES.md §4 Microstructure Mean-Reverter`den OHLCV-only uyarlama (gercek LOB verisi yok).

## Kapsam

Sembol: 657 · TF: 1D, 240 · Derinlik: 2.0 yil

## Sonuclar (TF bazinda, iki varyant)

| TF | Varyant | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|
| 1D | BASELINE (Hurst filtresiz) | 3391 | 28.93 | 0.99 | -0.143 | guvenilir n |
| 1D | +Hurst(MR<0.45) | 2414 | 28.96 | 1.00 | -0.070 | guvenilir n |
| 240 | BASELINE (Hurst filtresiz) | 8092 | 26.37 | 0.86 | -0.403 | guvenilir n |
| 240 | +Hurst(MR<0.45) | 4905 | 26.93 | 0.85 | -0.384 | guvenilir n |
