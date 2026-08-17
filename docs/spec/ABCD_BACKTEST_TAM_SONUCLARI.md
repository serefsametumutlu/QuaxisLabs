# ABCD Backtest Arastirma Raporu

Olusturulma: 2026-08-17 20:51 UTC

## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN

Kucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "Backtest metodolojisi"): `min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak acikca etiketlenip tabloda TUTULUR. "En verimli kosul" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir. Secilen herhangi bir konfigurasyon, ayri bir out-of-sample donemde/sembol alt-kumesinde AYRICA dogrulanmalidir.

- Sembol sayisi: 657
- Zaman dilimleri: 60, 120, 240, 1D, 1W
- Para birimleri: TRY, USD
- Backtest derinligi: ~2.0 yil (60/120/240dk zaman dilimlerinde yfinance siniri nedeniyle fiilen ~2 yilla sinirli olabilir)
- Yon: LONG ve SHORT AYRI AYRI backtest edildi -- her biri kendi bagimsiz `run_grid` cagrisinda, kendi Bonferroni-tipi uyarisiyla.

### Grid boyutu / coklu-karsilastirma (Bonferroni-tipi) uyarisi

**LONG grid:** 10 hucre karsilastirildi (5 zaman dilimi x 2 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.00500 (0.05/10) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

**SHORT grid:** 10 hucre karsilastirildi (5 zaman dilimi x 2 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.00500 (0.05/10) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

## En Verimli 5 Kosul (SADECE GUVENILIR, n >= 100 hucrelerden)

| Sira | Yon | TF | Para Birimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % |
|---|---|---|---|---|---|---|---|---|
| 1 | LONG | 1D | TRY | 206 | 66.99 | 1.38 | 0.104 | -0.33 |
| 2 | LONG | 240 | TRY | 291 | 56.70 | 1.19 | 0.069 | -0.47 |
| 3 | LONG | 120 | TRY | 481 | 50.73 | 0.81 | -0.075 | -0.60 |
| 4 | SHORT | 240 | TRY | 207 | 54.59 | 0.76 | -0.077 | -0.42 |
| 5 | LONG | 60 | TRY | 864 | 45.83 | 0.75 | -0.101 | -0.82 |

## TRY Grafigi Sonuclari

### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 481 | 50.73 | 0.81 | -0.075 | -0.60 | GUVENILIR |
| 1D | 206 | 66.99 | 1.38 | 0.104 | -0.33 | GUVENILIR |
| 1W | 69 | 55.07 | 0.95 | -0.024 | -0.29 | DUSUK GUVEN (n=69) |
| 240 | 291 | 56.70 | 1.19 | 0.069 | -0.47 | GUVENILIR |
| 60 | 864 | 45.83 | 0.75 | -0.101 | -0.82 | GUVENILIR |

### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 402 | 50.50 | 0.61 | -0.131 | -0.50 | GUVENILIR |
| 1D | 120 | 54.17 | 0.39 | -0.211 | -0.37 | GUVENILIR |
| 1W | 36 | 63.89 | 0.46 | -0.180 | -0.34 | DUSUK GUVEN (n=36) |
| 240 | 207 | 54.59 | 0.76 | -0.077 | -0.42 | GUVENILIR |
| 60 | 654 | 46.33 | 0.67 | -0.114 | -0.60 | GUVENILIR |

## USD Grafigi Sonuclari

> **USD-payda grafiginde BAGIMSIZ tespit -- ayni sinyalin doviz-ayarlı hali DEGIL: to_usd() sonrasi detect() USD-payda serisinde YENIDEN calistirilir, pivotlar (A/B/C/D) TL serisinden FARKLI cikabilir.**

### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 259 | 22.78 | 0.10 | -0.329 | -1.66 | GUVENILIR |
| 1D | 13 | 30.77 | 0.14 | -0.300 | -0.49 | GUVENSIZ (n=13) |
| 1W | 81 | 50.62 | 0.65 | -0.119 | -0.47 | DUSUK GUVEN (n=81) |
| 240 | 10 | 20.00 | 0.01 | -0.462 | -0.71 | GUVENSIZ (n=10) |
| 60 | 400 | 14.75 | 0.05 | -0.458 | -2.34 | GUVENILIR |

### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 187 | 21.93 | 0.08 | -0.334 | -1.20 | GUVENILIR |
| 1D | 86 | 29.07 | 0.19 | -0.226 | -0.46 | DUSUK GUVEN (n=86) |
| 1W | 30 | 50.00 | 0.60 | -0.084 | -0.36 | DUSUK GUVEN (n=30) |
| 240 | 105 | 24.76 | 0.12 | -0.284 | -1.15 | GUVENILIR |
| 60 | 302 | 14.90 | 0.07 | -0.312 | -1.68 | GUVENILIR |

## Ham Veri

Tum hucrelerin ham tablosu (LONG+SHORT birlikte): `data\abcd_cache\backtest_full_summary.csv`
