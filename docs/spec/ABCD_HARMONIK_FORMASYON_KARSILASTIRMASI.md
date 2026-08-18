# ABCD Harmonik Formasyon Karsilastirmasi

Olusturulma: 2026-08-18 09:05 UTC

## Kapsam

Bu rapor, `src/analysis/harmonic_presets.py`deki 5 formasyon on-ayarini (ABCD referans + Gartley/Bat/Butterfly/Crab) TAM BIST evreninde, LONG ve SHORT AYRI AYRI, TL grafiginde karsilastirir. **On-ayarlarin matematiksel gerekcesi/bilinen sinirlamalari** (CD/AB vs CD/BC donusumu, X noktasi/XD oraninin kontrol edilememesi) `src/analysis/harmonic_presets.py` modul dokumantasyonundadir -- burada TEKRARLANMAZ, okumadan sonuclari YORUMLAMAYIN.

## ⚠️ METODOLOJI UYARISI -- ONCE BU BOLUMU OKUYUN

Kucuk n'lerde sahte kesinlik riskine karsi (bkz. `docs/spec/spec_abcd_mimari_kararlar.md`, "Backtest metodolojisi"): `min_trades_show=30` altindaki hucreler ASLA gizlenmez -- "GUVENSIZ (n=X)" olarak acikca etiketlenip tabloda TUTULUR. "En iyi 10 kombinasyon" iddialari SADECE `min_trades_trustworthy=100` esigini gecen hucrelerden secilir. Secilen herhangi bir formasyon/yon/tf kombinasyonu, ayri bir out-of-sample donemde/sembol alt-kumesinde AYRICA dogrulanmalidir.

- Sembol sayisi: 657
- Zaman dilimleri: 1D, 240
- Para birimleri: TRY
- Formasyonlar: ABCD, GARTLEY, BAT, BUTTERFLY, CRAB
- Backtest derinligi: ~2.0 yil
- Yon: LONG ve SHORT AYRI AYRI backtest edildi. Formasyon: her formasyon KENDI ayri `run_grid` cagrisinda calisti (5 formasyon x 2 yon = 10 ayri cagri) -- `run_grid`in hucre-etiketleme sinirlamasi (`_params_label` BC/CD bantlarini icermez) nedeniyle formasyonlar AYNI cagriya karistirilamazdi, bkz. bu scriptin modul ust notu.

## Coklu-karsilastirma (Bonferroni-tipi) GLOBAL uyari

Bu karsilastirma toplamda **20 hucre** uretti (formasyon x yon x tf x para birimi -- 10 ayri `run_grid` cagrisinin TOPLAMI). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= **0.00250** (0.05/20). Asagidaki "en iyi" siralamayi bu global esige gore degerlendirin -- tek bir hucrenin one cikmasi 10 ayri deneyin en sansli sonucu olabilir, formasyon-basina/yon-basina hesaplanan alt uyarilar (asagida) bu global riski KUCUMSER.

<details>
<summary>Formasyon x yon basina ham grid_warning (referans)</summary>

- **ABCD / LONG:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **ABCD / SHORT:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **GARTLEY / LONG:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **GARTLEY / SHORT:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **BAT / LONG:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **BAT / SHORT:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **BUTTERFLY / LONG:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **BUTTERFLY / SHORT:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **CRAB / LONG:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.
- **CRAB / SHORT:** 2 hucre karsilastirildi (2 zaman dilimi x 1 para birimi x 1 parametre setinden). Bonferroni-tipi duzeltmeyle etkin anlamlilik esigi ~= 0.02500 (0.05/2) -- tek bir hucrenin 'en iyi' cikmasi sans eseri olabilir; secilen konfigurasyonu ayri bir out-of-sample donemde/sembol alt-kumesinde dogrulayin.

</details>

## En Iyi 10 Kombinasyon (SADECE GUVENILIR, n >= 100 hucrelerden)

| Sira | Formasyon | Yon | TF | Para Birimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CRAB | LONG | 1D | TRY | 1401 | 63.45 | 1.46 | 0.131 | -0.70 |
| 2 | BAT | LONG | 1D | TRY | 1928 | 63.49 | 1.41 | 0.123 | -0.93 |
| 3 | BUTTERFLY | LONG | 1D | TRY | 1879 | 63.23 | 1.39 | 0.117 | -0.92 |
| 4 | ABCD | LONG | 1D | TRY | 205 | 65.37 | 1.35 | 0.097 | -0.33 |
| 5 | GARTLEY | LONG | 1D | TRY | 1810 | 63.09 | 1.34 | 0.103 | -0.89 |
| 6 | ABCD | LONG | 240 | TRY | 291 | 56.70 | 1.18 | 0.068 | -0.47 |
| 7 | CRAB | LONG | 240 | TRY | 2035 | 55.48 | 1.04 | 0.015 | -1.24 |
| 8 | BAT | LONG | 240 | TRY | 2631 | 55.15 | 0.98 | -0.005 | -1.58 |
| 9 | GARTLEY | LONG | 240 | TRY | 2459 | 54.94 | 0.97 | -0.009 | -1.51 |
| 10 | BUTTERFLY | LONG | 240 | TRY | 2536 | 54.85 | 0.95 | -0.018 | -1.54 |

## Formasyon Basina Detay

### ABCD

#### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 205 | 65.37 | 1.35 | 0.097 | -0.33 | GUVENILIR |
| 240 | 291 | 56.70 | 1.18 | 0.068 | -0.47 | GUVENILIR |

#### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 121 | 53.72 | 0.39 | -0.209 | -0.37 | GUVENILIR |
| 240 | 207 | 54.59 | 0.76 | -0.075 | -0.42 | GUVENILIR |

### GARTLEY

#### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1810 | 63.09 | 1.34 | 0.103 | -0.89 | GUVENILIR |
| 240 | 2459 | 54.94 | 0.97 | -0.009 | -1.51 | GUVENILIR |

#### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1004 | 58.76 | 0.67 | -0.126 | -0.68 | GUVENILIR |
| 240 | 1975 | 54.48 | 0.74 | -0.092 | -1.25 | GUVENILIR |

### BAT

#### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1928 | 63.49 | 1.41 | 0.123 | -0.93 | GUVENILIR |
| 240 | 2631 | 55.15 | 0.98 | -0.005 | -1.58 | GUVENILIR |

#### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1237 | 57.48 | 0.59 | -0.155 | -0.85 | GUVENILIR |
| 240 | 2427 | 53.28 | 0.72 | -0.105 | -1.50 | GUVENILIR |

### BUTTERFLY

#### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1879 | 63.23 | 1.39 | 0.117 | -0.92 | GUVENILIR |
| 240 | 2536 | 54.85 | 0.95 | -0.018 | -1.54 | GUVENILIR |

#### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1154 | 57.89 | 0.62 | -0.143 | -0.80 | GUVENILIR |
| 240 | 2269 | 53.33 | 0.72 | -0.099 | -1.41 | GUVENILIR |

### CRAB

#### LONG

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1401 | 63.45 | 1.46 | 0.131 | -0.70 | GUVENILIR |
| 240 | 2035 | 55.48 | 1.04 | 0.015 | -1.24 | GUVENILIR |

#### SHORT

| Zaman Dilimi | n_trades | Win Rate % | Profit Factor | Expectancy (R) | Ort. Max DD % | Guven |
|---|---|---|---|---|---|---|
| 1D | 1146 | 57.16 | 0.58 | -0.148 | -0.80 | GUVENILIR |
| 240 | 2124 | 52.40 | 0.69 | -0.119 | -1.40 | GUVENILIR |

## Ham Veri

Tum hucrelerin ham tablosu (5 formasyon x LONG+SHORT birlikte): `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\harmonic_karsilastirma_summary.csv`
