# Harmonik Onay Kontrol Listesi -- Ablasyon Backtesti (RSI/MACD/Mum/Hacim)

Olusturulma: 2026-08-19 16:55 UTC

## Kapsam

Sembol: 657 · TF: 1D, 240 · Derinlik: 2.0 yil · Formasyon: ABCD/Gartley/Bat/Butterfly/Crab · Toplam PRZ olayi: 14152

## Yontem

Filtre esikleri (RSI 30/70, hacim 1.2x/0.85x, mum Pin Bar/Engulfing formal tanimlari) SABIT/literatur-kaynakli -- bu VERIDEN turetilmedi, dolayisiyla train/holdout ayrimina GEREK YOK (sizinti riski yok). `min_trades_trustworthy=100` altindaki hucreler SESSIZCE gizlenmez, `orneklem kucuk` etiketiyle GOSTERILIR.

## Sonuclar (formasyon x yon x tf, 6 varyant)

| Formasyon | Yon | TF | Varyant | n | Win Rate % | Profit Factor | Beklenti (R) | Guven |
|---|---|---|---|---|---|---|---|---|
| ABCD | LONG | 1D | BASELINE | 1346 | 43.02 | 1.21 | 0.104 | guvenilir n |
| ABCD | LONG | 1D | +RSI | 251 | 51.39 | 1.28 | 0.140 | guvenilir n |
| ABCD | LONG | 1D | +MACD | 187 | 52.94 | 0.99 | -0.012 | guvenilir n |
| ABCD | LONG | 1D | +Mum | 96 | 65.62 | 1.45 | 0.156 | orneklem kucuk |
| ABCD | LONG | 1D | +Hacim | 104 | 51.92 | 1.39 | 0.190 | guvenilir n |
| ABCD | LONG | 1D | +TUMU | 3 | 100.00 | sonsuz | 0.253 | orneklem COK kucuk |
| ABCD | LONG | 240 | BASELINE | 2132 | 35.08 | 0.83 | -0.175 | guvenilir n |
| ABCD | LONG | 240 | +RSI | 337 | 45.10 | 0.87 | -0.052 | guvenilir n |
| ABCD | LONG | 240 | +MACD | 350 | 43.14 | 0.78 | -0.119 | guvenilir n |
| ABCD | LONG | 240 | +Mum | 218 | 49.54 | 0.85 | -0.081 | guvenilir n |
| ABCD | LONG | 240 | +Hacim | 463 | 36.07 | 0.71 | -0.304 | guvenilir n |
| ABCD | LONG | 240 | +TUMU | 14 | 57.14 | 1.20 | 0.077 | orneklem kucuk |
| ABCD | SHORT | 1D | BASELINE | 1712 | 40.30 | 0.92 | -0.041 | guvenilir n |
| ABCD | SHORT | 1D | +RSI | 354 | 46.61 | 0.98 | -0.012 | guvenilir n |
| ABCD | SHORT | 1D | +MACD | 255 | 46.27 | 0.90 | -0.053 | guvenilir n |
| ABCD | SHORT | 1D | +Mum | 201 | 50.75 | 0.76 | -0.132 | guvenilir n |
| ABCD | SHORT | 1D | +Hacim | 209 | 39.23 | 0.69 | -0.276 | guvenilir n |
| ABCD | SHORT | 1D | +TUMU | 2 | 50.00 | 0.65 | -0.211 | orneklem COK kucuk |
| ABCD | SHORT | 240 | BASELINE | 2630 | 36.39 | 0.65 | -0.244 | guvenilir n |
| ABCD | SHORT | 240 | +RSI | 542 | 42.80 | 0.73 | -0.137 | guvenilir n |
| ABCD | SHORT | 240 | +MACD | 474 | 44.30 | 0.59 | -0.241 | guvenilir n |
| ABCD | SHORT | 240 | +Mum | 308 | 46.43 | 0.54 | -0.250 | guvenilir n |
| ABCD | SHORT | 240 | +Hacim | 460 | 40.22 | 0.75 | -0.113 | guvenilir n |
| ABCD | SHORT | 240 | +TUMU | 3 | 66.67 | 0.11 | -0.321 | orneklem COK kucuk |
| BAT | LONG | 1D | BASELINE | 166 | 37.95 | 0.66 | -0.238 | guvenilir n |
| BAT | LONG | 1D | +RSI | 7 | 42.86 | 0.43 | -0.345 | orneklem COK kucuk |
| BAT | LONG | 1D | +MACD | 36 | 52.78 | 1.24 | 0.093 | orneklem kucuk |
| BAT | LONG | 1D | +Mum | 20 | 55.00 | 0.42 | -0.270 | orneklem kucuk |
| BAT | LONG | 1D | +Hacim | 11 | 36.36 | 0.44 | -0.415 | orneklem kucuk |
| BAT | LONG | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| BAT | LONG | 240 | BASELINE | 352 | 36.65 | 0.86 | -0.086 | guvenilir n |
| BAT | LONG | 240 | +RSI | 25 | 52.00 | 1.75 | 0.276 | orneklem kucuk |
| BAT | LONG | 240 | +MACD | 82 | 42.68 | 0.97 | -0.021 | orneklem kucuk |
| BAT | LONG | 240 | +Mum | 51 | 45.10 | 0.50 | -0.227 | orneklem kucuk |
| BAT | LONG | 240 | +Hacim | 89 | 42.70 | 1.01 | -0.044 | orneklem kucuk |
| BAT | LONG | 240 | +TUMU | 3 | 66.67 | 83.40 | 1.418 | orneklem COK kucuk |
| BAT | SHORT | 1D | BASELINE | 239 | 39.75 | 0.84 | -4.669 | guvenilir n |
| BAT | SHORT | 1D | +RSI | 12 | 58.33 | 0.96 | -0.010 | orneklem kucuk |
| BAT | SHORT | 1D | +MACD | 38 | 47.37 | 0.63 | -0.177 | orneklem kucuk |
| BAT | SHORT | 1D | +Mum | 24 | 45.83 | 1.30 | 0.176 | orneklem kucuk |
| BAT | SHORT | 1D | +Hacim | 20 | 40.00 | 0.77 | -0.148 | orneklem kucuk |
| BAT | SHORT | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| BAT | SHORT | 240 | BASELINE | 358 | 38.83 | 0.85 | -0.112 | guvenilir n |
| BAT | SHORT | 240 | +RSI | 26 | 42.31 | 1.25 | 0.748 | orneklem kucuk |
| BAT | SHORT | 240 | +MACD | 66 | 45.45 | 0.74 | -0.072 | orneklem kucuk |
| BAT | SHORT | 240 | +Mum | 46 | 56.52 | 1.63 | 0.346 | orneklem kucuk |
| BAT | SHORT | 240 | +Hacim | 57 | 36.84 | 0.88 | -0.167 | orneklem kucuk |
| BAT | SHORT | 240 | +TUMU | 1 | 0.00 | 0.00 | -1.099 | orneklem COK kucuk |
| BUTTERFLY | LONG | 1D | BASELINE | 280 | 38.57 | 0.94 | -0.041 | guvenilir n |
| BUTTERFLY | LONG | 1D | +RSI | 12 | 41.67 | 0.80 | -0.102 | orneklem kucuk |
| BUTTERFLY | LONG | 1D | +MACD | 39 | 43.59 | 0.81 | -0.100 | orneklem kucuk |
| BUTTERFLY | LONG | 1D | +Mum | 17 | 70.59 | 3.21 | 0.565 | orneklem kucuk |
| BUTTERFLY | LONG | 1D | +Hacim | 25 | 40.00 | 0.36 | -0.396 | orneklem kucuk |
| BUTTERFLY | LONG | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| BUTTERFLY | LONG | 240 | BASELINE | 422 | 36.73 | 1.05 | 0.017 | guvenilir n |
| BUTTERFLY | LONG | 240 | +RSI | 28 | 35.71 | 0.84 | 0.004 | orneklem kucuk |
| BUTTERFLY | LONG | 240 | +MACD | 64 | 51.56 | 1.32 | 0.114 | orneklem kucuk |
| BUTTERFLY | LONG | 240 | +Mum | 44 | 56.82 | 1.69 | 0.269 | orneklem kucuk |
| BUTTERFLY | LONG | 240 | +Hacim | 91 | 45.05 | 1.43 | 0.325 | orneklem kucuk |
| BUTTERFLY | LONG | 240 | +TUMU | 4 | 50.00 | 0.63 | -0.218 | orneklem COK kucuk |
| BUTTERFLY | SHORT | 1D | BASELINE | 254 | 42.91 | 0.93 | -0.066 | guvenilir n |
| BUTTERFLY | SHORT | 1D | +RSI | 18 | 50.00 | 0.63 | -0.168 | orneklem kucuk |
| BUTTERFLY | SHORT | 1D | +MACD | 37 | 48.65 | 0.69 | -0.150 | orneklem kucuk |
| BUTTERFLY | SHORT | 1D | +Mum | 29 | 51.72 | 0.37 | -0.292 | orneklem kucuk |
| BUTTERFLY | SHORT | 1D | +Hacim | 16 | 50.00 | 1.03 | -0.054 | orneklem kucuk |
| BUTTERFLY | SHORT | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| BUTTERFLY | SHORT | 240 | BASELINE | 435 | 34.94 | 0.61 | -0.342 | guvenilir n |
| BUTTERFLY | SHORT | 240 | +RSI | 39 | 43.59 | 0.99 | -0.108 | orneklem kucuk |
| BUTTERFLY | SHORT | 240 | +MACD | 73 | 50.68 | 0.75 | -0.125 | orneklem kucuk |
| BUTTERFLY | SHORT | 240 | +Mum | 54 | 46.30 | 0.71 | -0.184 | orneklem kucuk |
| BUTTERFLY | SHORT | 240 | +Hacim | 68 | 30.88 | 0.74 | -0.295 | orneklem kucuk |
| BUTTERFLY | SHORT | 240 | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| CRAB | LONG | 1D | BASELINE | 98 | 46.94 | 1.55 | 0.293 | orneklem kucuk |
| CRAB | LONG | 1D | +RSI | 3 | 66.67 | 1.09 | 0.035 | orneklem COK kucuk |
| CRAB | LONG | 1D | +MACD | 15 | 53.33 | 1.34 | 0.153 | orneklem kucuk |
| CRAB | LONG | 1D | +Mum | 7 | 42.86 | 1.37 | 0.209 | orneklem COK kucuk |
| CRAB | LONG | 1D | +Hacim | 14 | 78.57 | 6.92 | 1.267 | orneklem kucuk |
| CRAB | LONG | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| CRAB | LONG | 240 | BASELINE | 191 | 35.08 | 0.77 | -0.214 | guvenilir n |
| CRAB | LONG | 240 | +RSI | 20 | 35.00 | 0.48 | -0.375 | orneklem kucuk |
| CRAB | LONG | 240 | +MACD | 45 | 46.67 | 0.87 | -0.059 | orneklem kucuk |
| CRAB | LONG | 240 | +Mum | 23 | 52.17 | 1.37 | 0.181 | orneklem kucuk |
| CRAB | LONG | 240 | +Hacim | 42 | 45.24 | 1.08 | -0.010 | orneklem kucuk |
| CRAB | LONG | 240 | +TUMU | 3 | 100.00 | sonsuz | 1.300 | orneklem COK kucuk |
| CRAB | SHORT | 1D | BASELINE | 201 | 35.82 | 0.53 | -0.323 | guvenilir n |
| CRAB | SHORT | 1D | +RSI | 20 | 45.00 | 0.87 | -0.073 | orneklem kucuk |
| CRAB | SHORT | 1D | +MACD | 30 | 40.00 | 0.39 | -0.368 | orneklem kucuk |
| CRAB | SHORT | 1D | +Mum | 23 | 30.43 | 0.48 | -0.307 | orneklem kucuk |
| CRAB | SHORT | 1D | +Hacim | 9 | 22.22 | 0.19 | -0.749 | orneklem COK kucuk |
| CRAB | SHORT | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| CRAB | SHORT | 240 | BASELINE | 311 | 33.76 | 0.75 | -0.371 | guvenilir n |
| CRAB | SHORT | 240 | +RSI | 27 | 48.15 | 0.83 | -0.079 | orneklem kucuk |
| CRAB | SHORT | 240 | +MACD | 49 | 51.02 | 1.31 | 0.211 | orneklem kucuk |
| CRAB | SHORT | 240 | +Mum | 34 | 50.00 | 0.64 | -0.196 | orneklem kucuk |
| CRAB | SHORT | 240 | +Hacim | 30 | 53.33 | 1.80 | 0.282 | orneklem kucuk |
| CRAB | SHORT | 240 | +TUMU | 1 | 0.00 | 0.00 | -1.075 | orneklem COK kucuk |
| GARTLEY | LONG | 1D | BASELINE | 292 | 42.81 | 1.21 | 0.124 | guvenilir n |
| GARTLEY | LONG | 1D | +RSI | 24 | 50.00 | 1.15 | 0.087 | orneklem kucuk |
| GARTLEY | LONG | 1D | +MACD | 49 | 42.86 | 0.73 | -0.138 | orneklem kucuk |
| GARTLEY | LONG | 1D | +Mum | 19 | 52.63 | 1.37 | 0.177 | orneklem kucuk |
| GARTLEY | LONG | 1D | +Hacim | 18 | 55.56 | 1.35 | 0.177 | orneklem kucuk |
| GARTLEY | LONG | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| GARTLEY | LONG | 240 | BASELINE | 493 | 37.32 | 0.81 | -0.189 | guvenilir n |
| GARTLEY | LONG | 240 | +RSI | 59 | 49.15 | 1.52 | 0.201 | orneklem kucuk |
| GARTLEY | LONG | 240 | +MACD | 100 | 46.00 | 1.04 | 0.050 | guvenilir n |
| GARTLEY | LONG | 240 | +Mum | 69 | 47.83 | 0.81 | -0.083 | orneklem kucuk |
| GARTLEY | LONG | 240 | +Hacim | 95 | 37.89 | 0.60 | -0.251 | orneklem kucuk |
| GARTLEY | LONG | 240 | +TUMU | 6 | 83.33 | 2.06 | 0.185 | orneklem COK kucuk |
| GARTLEY | SHORT | 1D | BASELINE | 279 | 41.58 | 0.83 | -0.129 | guvenilir n |
| GARTLEY | SHORT | 1D | +RSI | 20 | 60.00 | 0.79 | -0.082 | orneklem kucuk |
| GARTLEY | SHORT | 1D | +MACD | 54 | 50.00 | 0.83 | -0.149 | orneklem kucuk |
| GARTLEY | SHORT | 1D | +Mum | 30 | 46.67 | 0.87 | -0.055 | orneklem kucuk |
| GARTLEY | SHORT | 1D | +Hacim | 25 | 48.00 | 0.62 | -0.241 | orneklem kucuk |
| GARTLEY | SHORT | 1D | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |
| GARTLEY | SHORT | 240 | BASELINE | 418 | 38.52 | 0.58 | -0.382 | guvenilir n |
| GARTLEY | SHORT | 240 | +RSI | 44 | 52.27 | 0.81 | -0.092 | orneklem kucuk |
| GARTLEY | SHORT | 240 | +MACD | 87 | 42.53 | 0.57 | -0.301 | orneklem kucuk |
| GARTLEY | SHORT | 240 | +Mum | 49 | 44.90 | 0.39 | -0.301 | orneklem kucuk |
| GARTLEY | SHORT | 240 | +Hacim | 79 | 45.57 | 0.57 | -0.257 | orneklem kucuk |
| GARTLEY | SHORT | 240 | +TUMU | 0 | N/A | N/A | N/A | orneklem COK kucuk |

## Ozet -- her (formasyon,yon,tf) icin EN YUKSEK PF veren filtre varyanti

(SADECE `n>=10` olan hucreler arasindan -- kucuk orneklemli 'sanslı' sonuclar burada elenir, ama yukaridaki tam tabloda hala GORUNUR. `Guven` sutunu bu ozet tablo icin de GIZLENMEZ.)

| Formasyon | Yon | TF | En iyi varyant | Profit Factor | n | Guven |
|---|---|---|---|---|---|---|
| CRAB | LONG | 1D | +Hacim | 6.92 | 14 | orneklem kucuk |
| BUTTERFLY | LONG | 1D | +Mum | 3.21 | 17 | orneklem kucuk |
| CRAB | SHORT | 240 | +Hacim | 1.80 | 30 | orneklem kucuk |
| BAT | LONG | 240 | +RSI | 1.75 | 25 | orneklem kucuk |
| BUTTERFLY | LONG | 240 | +Mum | 1.69 | 44 | orneklem kucuk |
| BAT | SHORT | 240 | +Mum | 1.63 | 46 | orneklem kucuk |
| GARTLEY | LONG | 240 | +RSI | 1.52 | 59 | orneklem kucuk |
| ABCD | LONG | 1D | +Mum | 1.45 | 96 | orneklem kucuk |
| GARTLEY | LONG | 1D | +Mum | 1.37 | 19 | orneklem kucuk |
| CRAB | LONG | 240 | +Mum | 1.37 | 23 | orneklem kucuk |
| BAT | SHORT | 1D | +Mum | 1.30 | 24 | orneklem kucuk |
| BAT | LONG | 1D | +MACD | 1.24 | 36 | orneklem kucuk |
| ABCD | LONG | 240 | +TUMU | 1.20 | 14 | orneklem kucuk |
| BUTTERFLY | SHORT | 1D | +Hacim | 1.03 | 16 | orneklem kucuk |
| BUTTERFLY | SHORT | 240 | +RSI | 0.99 | 39 | orneklem kucuk |
| ABCD | SHORT | 1D | +RSI | 0.98 | 354 | guvenilir n |
| GARTLEY | SHORT | 1D | +Mum | 0.87 | 30 | orneklem kucuk |
| CRAB | SHORT | 1D | +RSI | 0.87 | 20 | orneklem kucuk |
| GARTLEY | SHORT | 240 | +RSI | 0.81 | 44 | orneklem kucuk |
| ABCD | SHORT | 240 | +Hacim | 0.75 | 460 | guvenilir n |

## Bulgular

- **Hangi filtre en sik kazaniyor**: +Mum: 8x, +RSI: 6x, +Hacim: 4x, +MACD: 1x, +TUMU: 1x (kac (formasyon,yon,tf) hucresinde 'en iyi varyant' oldugu).

- **Guvenilir (n>=100) VE karli (PF>=1.10) hucre sayisi**: 0/20 -- geri kalanlarin cogu KUCUK ORNEKLEM (n<100), yuksek PF'leri sansa bagli OLABILIR, GIZLENMEDI ama temkinli okunmali.

- **SHORT sinyaller genelde LONG'dan zayif**: en iyi SHORT hucrelerin cogu PF<1.0 (kârsız) kaliyor, en guvenilir/buyuk orneklemli iki hucre (ABCD SHORT 1D n=354, ABCD SHORT 240 n=460) EN IYI filtreyle bile PF<1.0 -- ABCD SHORT bu veri setinde GENEL OLARAK karli DEGIL, filtre bunu KURTARMIYOR.

## Ham Veri

Olay basina RSI/MACD/Mum/Hacim bayraklari: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\harmonic_confirmation_events.csv`
