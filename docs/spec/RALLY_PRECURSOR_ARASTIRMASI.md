# Buyuk Yukselis Onculu Analizi -- Tam BIST Arastirmasi

Olusturulma: 2026-08-20 09:46 UTC

## Kapsam

Sembol: 657 · Derinlik: ~2000 bar (1D, ~8 yil) · Pivot lookback: 10 · Ileri-bakis penceresi: 120 bar · Buyuk yukselis esigi: %50.0

- Toplam aday (pivot dip): 16237
- Bunlardan BUYUK yukselisle baslayan (>=%50.0): 9321 (taban oran: %57.4)

## Motivasyon

Onceki yaklasim (Wavelet Trend Rider ablasyonu) DISARIDAN gelen bir stratejiyi FILTRELEYEREK sinyal kalitesini artirmaya calisti -- sonuc COK AZ sinyal, BUYUK yukselislerin cogu KACIRILDI. Bu arastirma TERSTEN gider: GERCEK buyuk yukselisleri (pivot dip -> sonraki N barda ulasilan en yuksek fiyat) objektif olarak BULUR, o dip anindaki (VE ONCESINDEKI, causal) teknik kosullari olcer, BUYUK yukselisle baslayanlarla BASLAMAYANLARI karsilastirir.

## Fibonacci Geri-Cekilme Bolgesi -- "Altin Oran" Sorusuna Dogrudan Cevap

Her dip, ONCEKI yukselis bacaginin (prior_low->prior_high) hangi Fibonacci bolgesinde olustu -- o bolgede BUYUK yukselis baslama orani ne?

| Fibonacci Bolgesi | n | Buyuk Yukselis Orani % |
|---|---|---|
| 0.000-0.382 | 1246 | 61.8 |
| 0.382-0.500 | 1186 | 58.5 |
| 0.500-0.618 | 1475 | 58.4 |
| 0.618-0.786 | 2278 | 57.9 |
| 0.786-1.000 | 2797 | 56.4 |
| >1.000 (X asildi) | 6418 | 56.6 |
| N/A (onceki bacak yok) | 837 | 55.7 |

## Istatistiksel Faktor Analizi (kronolojik split/FDR/holdout -- abcd_factor_analysis.py motoru)


> Butun bulgular ILISKISELDIR, NEDENSELLIK iddia edilmez -- 'X kosulu yukselise SEBEP OLUR/GARANTI EDER' turu ifadeler YASAKTIR; sadece 'buyuk yukselisle baslayan dipler ile baslamayanlar arasinda X ozelliginde ISTATISTIKSEL FARK var (n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi)' turu ifadeler kullanilir. Etiket = dipten sonraki N barda ulasilan en yuksek fiyatin dip'e gore yuzde artisi >= esik mi (gelecek verisi SADECE etikette kullanilir, ozellik cikariminda ASLA -- bkz. rally_precursor.py ust notu).

- Toplam islem: 16237 (train=11366, holdout=4871, ozellik-hesaplanamadigi-icin-atlanan=0)
- Kronolojik split esigi (giris zamani): 2025-01-28 00:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| rsi14 | continuous | 6905/4369 | 40.61 | 40.2 | 0.006169 | 0.01028 | -0.031 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| rsi_min_10 | continuous | 6905/4369 | 38.29 | 37.88 | 0.002102 | 0.004086 | -0.034 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| macd_hist_sign | categorical | 6955/4400 | -0.8286 | -0.7564 | 4.736e-10 | 1.658e-09 | 0.058 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| macd_hist_rising | categorical | 6955/4400 | 0.2068 | 0.2177 | 0.17 | 0.248 | 0.013 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| adx14 | continuous | 6785/4269 | 25.86 | 24.98 | 7.677e-05 | 0.0001956 | -0.045 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| adx_rising | categorical | 6721/4221 | 0.3724 | 0.371 | 0.8977 | 0.8977 | 0.001 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| bb_percent_b | continuous | 6861/4336 | 0.1893 | 0.1855 | 0.4726 | 0.5704 | -0.008 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| bb_width_pctrank | continuous | 6333/3832 | 0.4874 | 0.4626 | 2.033e-05 | 5.929e-05 | -0.050 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| vol_ratio_recent | continuous | 6959/4407 | 0.818 | 0.8155 | 0.6797 | 0.7244 | 0.005 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| dist_from_sma200_pct | continuous | 5113/3225 | 7.459 | 3.045 | 7.491e-15 | 5.244e-14 | -0.101 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| atr_pct_of_price | continuous | 6910/4366 | 6.4 | 5.601 | 1.236e-14 | 7.211e-14 | -0.086 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| fib_retracement | continuous | 6527/4061 | 1.047 | 1.124 | 0.0007123 | 0.001558 | 0.039 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| fib_dist_from_618 | continuous | 6527/4061 | 0.6114 | 0.6609 | 0.1164 | 0.1772 | 0.018 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| higher_low | categorical | 6644/4149 | 0.6049 | 0.5799 | 0.01063 | 0.01691 | 0.025 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| bars_since_prior_high | continuous | 6718/4236 | 19.59 | 19.33 | 0.3371 | 0.4537 | -0.011 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| momentum_signal_nearby | categorical | 6959/4407 | 0.04641 | 0.04992 | 0.4187 | 0.5427 | 0.008 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| harmonic_signal_nearby | categorical | 6959/4407 | 0.08018 | 0.0658 | 0.005015 | 0.008777 | 0.026 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| stoch_k | continuous | 6890/4360 | 19.25 | 18.57 | 0.001871 | 0.003852 | -0.035 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| williams_r | continuous | 6914/4371 | -80.51 | -81.01 | 0.4561 | 0.5701 | -0.008 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| cci20 | continuous | 6861/4336 | -117 | -117.3 | 0.6099 | 0.7115 | -0.006 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| pct_from_52w_low | continuous | 6955/4400 | 136.3 | 125.3 | 9.912e-18 | 8.673e-17 | -0.095 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| vol_climax_ratio | continuous | 6861/4339 | 0.9049 | 0.9221 | 1.314e-06 | 4.179e-06 | 0.054 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| vol_dryup_min_ratio | continuous | 6861/4339 | 0.4115 | 0.4685 | 1.311e-42 | 4.589e-41 | 0.153 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| gap_into_low_pct | continuous | 6959/4407 | -0.7381 | -0.4139 | 1.615e-12 | 7.065e-12 | 0.078 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| candle_pin_bar | categorical | 6959/4407 | 0.1013 | 0.1076 | 0.3016 | 0.4223 | 0.010 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| candle_engulfing | categorical | 6959/4407 | 0.06969 | 0.06853 | 0.8409 | 0.8656 | 0.002 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| rsi_bullish_divergence | categorical | 6519/4063 | 0.09081 | 0.1147 | 7.823e-05 | 0.0001956 | 0.038 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| atr_pctrank | continuous | 6464/3946 | 0.6156 | 0.5708 | 3.399e-11 | 1.322e-10 | -0.077 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| ma_ribbon_score | continuous | 6959/4407 | 1.961 | 1.727 | 1.869e-20 | 3.271e-19 | -0.098 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| dist_from_ema20_pct | continuous | 6959/4407 | -9.875 | -9.151 | 0.000125 | 0.0002917 | 0.043 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| demand_zone_proximity_atr | continuous | 999/667 | 7.976 | 10.27 | 3.76e-14 | 1.88e-13 | 0.219 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| in_demand_zone | categorical | 999/667 | 0.01602 | 0.01199 | 0.6418 | 0.7244 | 0.011 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| wavelet_momentum_nearby | categorical | 4760/3197 | 0.4162 | 0.4507 | 0.002449 | 0.004512 | 0.034 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| vcp_pattern_nearby | categorical | 6959/4407 | 0.0004311 | 0.0006807 | 0.683 | 0.7244 | 0.001 (Cramer's V (fisher_exact)) | train'de FDR (q<0.10) esigini gecmedi |
| vol_breakout_nearby | categorical | 6959/4407 | 0.4481 | 0.3628 | 3.109e-19 | 3.628e-18 | 0.084 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |

## Lojistik regresyon (yorumlanabilir, standardize)

_Model yakinsamadi/uygulanamadi: standardize edilmis (z-skor) ozellikler; kategorik ozellikler 0/1 kodlu._

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.


## Ham Veri

Her aday + ozellikler: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\rally_precursor_candidates.csv`
