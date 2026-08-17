# ABCD Backtest Arastirma Raporu

Olusturulma: 2026-08-17 19:38 UTC

## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN

Kucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "Backtest metodolojisi"): `min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak acikca etiketlenip tabloda TUTULUR. "En verimli kosul" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir. Secilen herhangi bir konfigurasyon, ayri bir out-of-sample donemde/sembol alt-kumesinde AYRICA dogrulanmalidir.

- Sembol sayisi: 35
- Zaman dilimleri: 1D, 240
- Para birimleri: TRY, USD
- Backtest derinligi: ~2.0 yil (60/120/240dk zaman dilimlerinde yfinance siniri nedeniyle fiilen ~2 yilla sinirli olabilir)
- Yon: LONG ve SHORT AYRI AYRI backtest edildi -- her biri kendi bagimsiz `run_grid` cagrisinda, kendi Bonferroni-tipi uyarisiyla.

### Grid boyutu / coklu-karsilastirma (Bonferroni-tipi) uyarisi

**LONG grid:** 4 hucre karsilastirildi (2 zaman dilimi x 2 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.01250 (0.05/4) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

**SHORT grid:** 4 hucre karsilastirildi (2 zaman dilimi x 2 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.01250 (0.05/4) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

## En Verimli 5 Kosul (SADECE GUVENILIR, n >= 100 hucrelerden)

_Hicbir hucre `min_trades_trustworthy` esigini gecmedi -- "en verimli kosul" iddiasi YAPILAMAZ (kucuk n'de sahte kesinlik riski)._

## TRY Grafigi Sonuclari

### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 5 | 40.00 | 0.06 | -0.395 | -0.53 | GUVENSIZ (n=5) |
| 240 | 14 | 50.00 | 1.08 | 0.038 | -0.60 | GUVENSIZ (n=14) |

### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 9 | 55.56 | 0.31 | -0.318 | -0.59 | GUVENSIZ (n=9) |
| 240 | 16 | 37.50 | 0.27 | -0.367 | -0.57 | GUVENSIZ (n=16) |

## USD Grafigi Sonuclari

> **USD-payda grafiginde BAGIMSIZ tespit -- ayni sinyalin doviz-ayarlı hali DEGIL: to_usd() sonrasi detect() USD-payda serisinde YENIDEN calistirilir, pivotlar (A/B/C/D) TL serisinden FARKLI cikabilir.**

### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 13 | 30.77 | 0.14 | -0.300 | -0.49 | GUVENSIZ (n=13) |
| 240 | 10 | 20.00 | 0.01 | -0.462 | -0.71 | GUVENSIZ (n=10) |

### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 6 | 33.33 | 0.06 | -0.644 | -0.74 | GUVENSIZ (n=6) |
| 240 | 5 | 20.00 | 0.30 | -0.282 | -1.40 | GUVENSIZ (n=5) |

## Ham Veri

Tum hucrelerin ham tablosu (LONG+SHORT birlikte): `data\abcd_cache\backtest_pilot_summary.csv`
