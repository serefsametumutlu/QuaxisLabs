# Wavelet Trend Rider -- Kotu Sinyal Eleme Ablasyonu (Tam BIST)

Olusturulma: 2026-08-20 08:37 UTC

## Kapsam

Sembol: 657 · TF: 240 (4H) + 1D MTF onay · Derinlik: ~1200 bar · Varyant sayisi: 26

## Motivasyon

Kullanici canli TradingView testinde 'sinyallerin cogu hissenin tepesinde geliyor, SL'ye gidiyor' geri bildirimi verdi. Bu ablasyon 6 hipotezi (asiri-uzama, pullback-sartsizligi, yeni-tepe, ADX tavani, yesil mum, hacim onayi) BASELINE'a TEK TEK ve kombinasyon halinde ekleyip PF/WR/n uzerindeki etkisini olcer.

## Sonuclar

| Varyant | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |
|---|---|---|---|---|---|
| BASELINE | 5027 | 44.92 | 1.20 | 0.101 | guvenilir (n>=50) |
| ARTI_UZAMA_0.5 | 708 | 48.16 | 1.40 | 0.215 | guvenilir (n>=50) |
| ARTI_UZAMA_0.75 | 754 | 48.28 | 1.41 | 0.224 | guvenilir (n>=50) |
| ARTI_UZAMA_1.0 | 797 | 48.31 | 1.41 | 0.216 | guvenilir (n>=50) |
| ARTI_UZAMA_1.5 | 907 | 47.63 | 1.37 | 0.198 | guvenilir (n>=50) |
| ARTI_UZAMA_2.0 | 1031 | 47.24 | 1.38 | 0.201 | guvenilir (n>=50) |
| ARTI_PULLBACK_1 | 2414 | 44.37 | 1.16 | 0.089 | guvenilir (n>=50) |
| ARTI_PULLBACK_2 | 2412 | 44.36 | 1.16 | 0.089 | guvenilir (n>=50) |
| ARTI_PULLBACK_3 | 2404 | 44.34 | 1.16 | 0.089 | guvenilir (n>=50) |
| ARTI_YENI_TEPE_DISI | 4873 | 44.74 | 1.20 | 0.112 | guvenilir (n>=50) |
| ARTI_ADX_TAVAN_40 | 3725 | 45.26 | 1.22 | 0.112 | guvenilir (n>=50) |
| ARTI_ADX_TAVAN_50 | 4466 | 45.14 | 1.22 | 0.115 | guvenilir (n>=50) |
| ARTI_YESIL_MUM | 4145 | 46.01 | 1.27 | 0.147 | guvenilir (n>=50) |
| ARTI_HACIM_ONAY | 4190 | 45.13 | 1.22 | 0.122 | guvenilir (n>=50) |
| ARTI_RSI_60 | 4042 | 44.48 | 1.19 | 0.110 | guvenilir (n>=50) |
| ARTI_RSI_55 | 3251 | 43.40 | 1.15 | 0.077 | guvenilir (n>=50) |
| KOMBO_UZAMA1.0_YESILMUM | 583 | 50.26 | 1.55 | 0.286 | guvenilir (n>=50) |
| KOMBO_UZAMA1.0_ADX40 | 541 | 49.72 | 1.44 | 0.231 | guvenilir (n>=50) |
| KOMBO_UZAMA1.0_HACIM | 598 | 49.00 | 1.44 | 0.231 | guvenilir (n>=50) |
| KOMBO_UZAMA0.75_YESILMUM | 551 | 50.27 | 1.55 | 0.285 | guvenilir (n>=50) |
| KOMBO_UZAMA1.0_YESILMUM_ADX40 | 403 | 52.11 | 1.61 | 0.308 | guvenilir (n>=50) |
| KOMBO_UZAMA1.5_PULLBACK1 | 310 | 45.81 | 1.29 | 0.145 | guvenilir (n>=50) |
| KOMBO_UZAMA1.5_TEPEDISI | 884 | 47.74 | 1.38 | 0.203 | guvenilir (n>=50) |
| KOMBO_PULLBACK1_ADX40 | 1477 | 44.96 | 1.22 | 0.118 | guvenilir (n>=50) |
| KOMBO_TUMU_GEVSEK | 291 | 45.70 | 1.24 | 0.130 | guvenilir (n>=50) |
| KOMBO_TUMU_SIKI | 167 | 47.90 | 1.36 | 0.191 | guvenilir (n>=50) |

## Ozet -- BASELINE'a gore PF degisimi (n>=20 varyantlar arasindan)

BASELINE: n=5027, PF=1.20, Win%=44.92

| Varyant | n | PF | BASELINE'a gore PF farki | Win Rate % |
|---|---|---|---|---|
| KOMBO_UZAMA1.0_YESILMUM_ADX40 | 403 | 1.61 | +0.41 | 52.11 |
| KOMBO_UZAMA1.0_YESILMUM | 583 | 1.55 | +0.35 | 50.26 |
| KOMBO_UZAMA0.75_YESILMUM | 551 | 1.55 | +0.35 | 50.27 |
| KOMBO_UZAMA1.0_ADX40 | 541 | 1.44 | +0.24 | 49.72 |
| KOMBO_UZAMA1.0_HACIM | 598 | 1.44 | +0.24 | 49.00 |
| ARTI_UZAMA_0.75 | 754 | 1.41 | +0.22 | 48.28 |
| ARTI_UZAMA_1.0 | 797 | 1.41 | +0.21 | 48.31 |
| ARTI_UZAMA_0.5 | 708 | 1.40 | +0.20 | 48.16 |
| KOMBO_UZAMA1.5_TEPEDISI | 884 | 1.38 | +0.18 | 47.74 |
| ARTI_UZAMA_2.0 | 1031 | 1.38 | +0.18 | 47.24 |
| ARTI_UZAMA_1.5 | 907 | 1.37 | +0.17 | 47.63 |
| KOMBO_TUMU_SIKI | 167 | 1.36 | +0.17 | 47.90 |
| KOMBO_UZAMA1.5_PULLBACK1 | 310 | 1.29 | +0.09 | 45.81 |
| ARTI_YESIL_MUM | 4145 | 1.27 | +0.07 | 46.01 |
| KOMBO_TUMU_GEVSEK | 291 | 1.24 | +0.04 | 45.70 |
| ARTI_ADX_TAVAN_50 | 4466 | 1.22 | +0.02 | 45.14 |
| ARTI_HACIM_ONAY | 4190 | 1.22 | +0.02 | 45.13 |
| ARTI_ADX_TAVAN_40 | 3725 | 1.22 | +0.02 | 45.26 |
| KOMBO_PULLBACK1_ADX40 | 1477 | 1.22 | +0.02 | 44.96 |
| ARTI_YENI_TEPE_DISI | 4873 | 1.20 | +0.01 | 44.74 |
| ARTI_RSI_60 | 4042 | 1.19 | -0.00 | 44.48 |
| ARTI_PULLBACK_3 | 2404 | 1.16 | -0.03 | 44.34 |
| ARTI_PULLBACK_2 | 2412 | 1.16 | -0.03 | 44.36 |
| ARTI_PULLBACK_1 | 2414 | 1.16 | -0.03 | 44.37 |
| ARTI_RSI_55 | 3251 | 1.15 | -0.05 | 43.40 |

## Ham Veri (BASELINE sinyallerinin teshis alanlari)

`C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\wavelet_trend_rider_optimizasyon_summary.csv`
