# Momentum Confluence V1/V2 -- Tam BIST Backtest

Olusturulma: 2026-08-18 16:14 UTC

## Kapsam

Sembol sayisi: 657 · Zaman dilimleri: 1D, 240 · Backtest derinligi: ~2.0 yil · Para birimi: TRY. V1 = TRF flip + EMA Squeeze + Hacim patlamasi. V2 = V1'in TUMU + WaveTrend kesisim onayi + yesil mum + daha siki EMA sirali/mesafe kosulu.

## ⚠️ TP/SL -- kaynak Pine dosyalarinda YOKTU, bu arastirma icin EKLENDI

SL = entry - atr_mult(1.5) * ATR14(Wilder) · risk = entry-SL · TP1 = entry + 1R · TP2 = entry + 2R (abcd_backtest.py'nin AYNI 1R/2R kismi-cikis motoru reuse edildi -- bkz. src/analysis/momentum_confluence.py modul ust notu).

- `min_trades_show=30` altindaki hucreler ASLA gizlenmez.

## Backtest Sonuclari (R-multiple bazli)

| Varyant | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|---|
| V1 | 1D | 2096 | 56.73 | 1.11 | 0.054 | -1.31 | GUVENILIR |
| V1 | 240 | 6500 | 55.71 | 1.17 | 0.061 | -3.27 | GUVENILIR |
| V2 | 1D | 741 | 54.93 | 0.96 | -0.016 | -0.76 | GUVENILIR |
| V2 | 240 | 1847 | 57.23 | 1.24 | 0.029 | -1.40 | GUVENILIR |

## V1 vs V2 Sinyal Sikligi

- V1 toplam işlem: 8596
- V2 toplam işlem: 2588
- V2/V1 orani: %30.1 (V2, V1'in kosullarinin USTUNE ek filtre ekliyor -- bu oranin <100 olmasi BEKLENIR)

## Ham Veri

Hucre bazli ozet: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\momentum_confluence_summary.csv`
