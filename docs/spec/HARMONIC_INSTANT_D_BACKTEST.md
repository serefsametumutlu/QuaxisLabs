# Harmonic "Anlik D" (V2.2) Backtest -- 5 Formasyon

Olusturulma: 2026-08-18 16:33 UTC

## Kapsam

Sembol sayisi: 657 · Zaman dilimleri: 1D, 240 · Backtest derinligi: ~2.0 yil · Para birimi: TRY. Formasyonlar: ABCD (klasik, X yok) + Gartley/Bat/Butterfly/Crab (X-noktali). HER BIRI `detect_prz()`nin (D pivot onayi BEKLEMEDEN, fiyat istatistiksel D bolgesine CANLI girdigi an) urettigi sinyalleri DOGRUDAN BUY/SELL islemi olarak kullanir -- `pine/harmonic_formations_v1_indicator.pine` V2.2 ile Pine-parity.

## ⚠️ Bu sinyaller REPAINT EDEBILIR

D, klasik `detect()`teki gibi kendi pivot onayini gecirmis bir nokta DEGIL -- sadece fiyatin istatistiksel hedefe ulastigi andir; formasyon sonradan tamamlanmayabilir. Asagidaki sonuclar bu OLDUGU gibi -- onaylanmis/onaylanmamis ayrimi YAPMADAN -- backtest edilmistir (kullanicinin acik talebi).

- `min_trades_show=30` altindaki hucreler ASLA gizlenmez.

## Sonuclar (R-multiple bazli, PF'ye gore siralı)

| Formasyon | Yon | TF | n_trades | Win Rate % | Profit Factor | Beklenti (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|---|---|
| CRAB | LONG | 1D | 100 | 45.00 | 1.40 | 0.207 | -0.61 | GUVENILIR |
| ABCD | LONG | 1D | 1344 | 42.41 | 1.20 | 0.086 | -1.36 | GUVENILIR |
| GARTLEY | LONG | 1D | 294 | 42.18 | 1.10 | 0.062 | -0.76 | GUVENILIR |
| BUTTERFLY | LONG | 240 | 411 | 36.25 | 1.06 | 0.031 | -0.98 | GUVENILIR |
| BUTTERFLY | LONG | 1D | 280 | 38.57 | 0.99 | -0.010 | -0.81 | GUVENILIR |
| BUTTERFLY | SHORT | 1D | 253 | 43.08 | 0.95 | -0.050 | -0.71 | GUVENILIR |
| ABCD | SHORT | 1D | 1719 | 40.20 | 0.94 | -0.008 | -1.68 | GUVENILIR |
| BAT | LONG | 240 | 351 | 36.18 | 0.89 | -0.057 | -0.88 | GUVENILIR |
| GARTLEY | LONG | 240 | 489 | 36.81 | 0.86 | -0.172 | -1.02 | GUVENILIR |
| BAT | SHORT | 1D | 240 | 39.58 | 0.85 | -4.641 | -0.72 | GUVENILIR |
| ABCD | LONG | 240 | 2074 | 34.76 | 0.84 | -0.138 | -2.36 | GUVENILIR |
| GARTLEY | SHORT | 1D | 280 | 40.71 | 0.84 | -0.127 | -0.77 | GUVENILIR |
| BAT | SHORT | 240 | 353 | 38.81 | 0.81 | -0.155 | -0.85 | GUVENILIR |
| CRAB | SHORT | 240 | 305 | 33.44 | 0.75 | -0.371 | -0.90 | GUVENILIR |
| CRAB | LONG | 240 | 185 | 36.22 | 0.71 | -0.247 | -0.81 | GUVENILIR |
| BAT | LONG | 1D | 167 | 37.13 | 0.67 | -0.233 | -0.74 | GUVENILIR |
| BUTTERFLY | SHORT | 240 | 429 | 34.50 | 0.63 | -0.302 | -0.95 | GUVENILIR |
| ABCD | SHORT | 240 | 2576 | 36.02 | 0.62 | -0.275 | -2.81 | GUVENILIR |
| CRAB | SHORT | 1D | 200 | 35.00 | 0.56 | -0.307 | -0.78 | GUVENILIR |
| GARTLEY | SHORT | 240 | 412 | 38.35 | 0.51 | -0.425 | -0.87 | GUVENILIR |

## Ham Veri

`C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\harmonic_instant_summary.csv`
