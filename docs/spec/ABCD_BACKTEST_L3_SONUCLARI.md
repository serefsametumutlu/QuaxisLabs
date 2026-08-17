# ABCD Backtest Arastirma Raporu

Olusturulma: 2026-08-17 23:17 UTC

## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN

Kucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "Backtest metodolojisi"): `min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak acikca etiketlenip tabloda TUTULUR. "En verimli kosul" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir. Secilen herhangi bir konfigurasyon, ayri bir out-of-sample donemde/sembol alt-kumesinde AYRICA dogrulanmalidir.

- Sembol sayisi: 657
- Zaman dilimleri: 60, 120, 240, 1D, 1W
- Para birimleri: TRY
- Backtest derinligi: ~2.0 yil (60/120/240dk zaman dilimlerinde yfinance siniri nedeniyle fiilen ~2 yilla sinirli olabilir)
- Yon: LONG ve SHORT AYRI AYRI backtest edildi -- her biri kendi bagimsiz `run_grid` cagrisinda, kendi Bonferroni-tipi uyarisiyla.

### Grid boyutu / coklu-karsilastirma (Bonferroni-tipi) uyarisi

**LONG grid:** 5 hucre karsilastirildi (5 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.01000 (0.05/5) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

**SHORT grid:** 5 hucre karsilastirildi (5 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.01000 (0.05/5) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

## En Verimli 5 Kosul (SADECE GUVENILIR, n >= 100 hucrelerden)

| Sira | Yon | TF | Para Birimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % |
|---|---|---|---|---|---|---|---|---|
| 1 | LONG | 1W | TRY | 120 | 70.00 | 1.53 | 0.114 | -0.23 |
| 2 | LONG | 1D | TRY | 290 | 54.48 | 0.95 | -0.019 | -0.42 |
| 3 | LONG | 240 | TRY | 394 | 56.60 | 0.93 | -0.021 | -0.45 |
| 4 | LONG | 120 | TRY | 852 | 51.29 | 0.84 | -0.055 | -0.73 |
| 5 | SHORT | 120 | TRY | 594 | 49.49 | 0.82 | -0.034 | -0.51 |

## TRY Grafigi Sonuclari

### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 852 | 51.29 | 0.84 | -0.055 | -0.73 | GUVENILIR |
| 1D | 290 | 54.48 | 0.95 | -0.019 | -0.42 | GUVENILIR |
| 1W | 120 | 70.00 | 1.53 | 0.114 | -0.23 | GUVENILIR |
| 240 | 394 | 56.60 | 0.93 | -0.021 | -0.45 | GUVENILIR |
| 60 | 1340 | 47.84 | 0.69 | -0.113 | -1.04 | GUVENILIR |

### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 120 | 594 | 49.49 | 0.82 | -0.034 | -0.51 | GUVENILIR |
| 1D | 207 | 62.80 | 0.79 | -0.065 | -0.35 | GUVENILIR |
| 1W | 59 | 61.02 | 0.91 | -0.030 | -0.33 | DUSUK GUVEN (n=59) |
| 240 | 327 | 52.91 | 0.53 | -0.157 | -0.45 | GUVENILIR |
| 60 | 1047 | 42.31 | 0.53 | -0.159 | -0.80 | GUVENILIR |

## Ham Veri

Tum hucrelerin ham tablosu (LONG+SHORT birlikte): `data\abcd_cache\backtest_l3_summary.csv`
