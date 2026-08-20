# Buyuk Yukselis Onculu Analizi -- Tam BIST Arastirmasi

Olusturulma: 2026-08-20 09:18 UTC

## Kapsam

Sembol: 657 · Derinlik: ~2000 bar (1D, ~8 yil) · Pivot lookback: 10 · Ileri-bakis penceresi: 120 bar · Buyuk yukselis esigi: %25.0

- Toplam aday (pivot dip): 16237
- Bunlardan BUYUK yukselisle baslayan (>=%25.0): 13736 (taban oran: %84.6)

## Motivasyon

Onceki yaklasim (Wavelet Trend Rider ablasyonu) DISARIDAN gelen bir stratejiyi FILTRELEYEREK sinyal kalitesini artirmaya calisti -- sonuc COK AZ sinyal, BUYUK yukselislerin cogu KACIRILDI. Bu arastirma TERSTEN gider: GERCEK buyuk yukselisleri (pivot dip -> sonraki N barda ulasilan en yuksek fiyat) objektif olarak BULUR, o dip anindaki (VE ONCESINDEKI, causal) teknik kosullari olcer, BUYUK yukselisle baslayanlarla BASLAMAYANLARI karsilastirir.

## Fibonacci Geri-Cekilme Bolgesi -- "Altin Oran" Sorusuna Dogrudan Cevap

Her dip, ONCEKI yukselis bacaginin (prior_low->prior_high) hangi Fibonacci bolgesinde olustu -- o bolgede BUYUK yukselis baslama orani ne?

| Fibonacci Bolgesi | n | Buyuk Yukselis Orani % |
|---|---|---|
| 0.000-0.382 | 1246 | 87.2 |
| 0.382-0.500 | 1186 | 85.2 |
| 0.500-0.618 | 1475 | 84.1 |
| 0.618-0.786 | 2278 | 85.6 |
| 0.786-1.000 | 2797 | 83.3 |
| >1.000 (X asildi) | 6418 | 84.3 |
| N/A (onceki bacak yok) | 837 | 84.6 |

## Istatistiksel Faktor Analizi (kronolojik split/FDR/holdout -- abcd_factor_analysis.py motoru)


> Butun bulgular ILISKISELDIR, NEDENSELLIK iddia edilmez -- 'X kosulu yukselise SEBEP OLUR/GARANTI EDER' turu ifadeler YASAKTIR; sadece 'buyuk yukselisle baslayan dipler ile baslamayanlar arasinda X ozelliginde ISTATISTIKSEL FARK var (n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi)' turu ifadeler kullanilir. Etiket = dipten sonraki N barda ulasilan en yuksek fiyatin dip'e gore yuzde artisi >= esik mi (gelecek verisi SADECE etikette kullanilir, ozellik cikariminda ASLA -- bkz. rally_precursor.py ust notu).

- Toplam islem: 15811 (train=11068, holdout=4743, ozellik-hesaplanamadigi-icin-atlanan=426)
- Kronolojik split esigi (giris zamani): 2025-02-10 00:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| rsi14 | continuous | 9456/1612 | 40.67 | 40.33 | 0.0482 | 0.1024 | -0.031 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| rsi_min_10 | continuous | 9456/1612 | 38.32 | 38.21 | 0.3278 | 0.4286 | -0.015 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| macd_hist_sign | categorical | 9452/1606 | -0.8142 | -0.7472 | 3.547e-05 | 0.0001206 | 0.039 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| macd_hist_rising | categorical | 9452/1606 | 0.2066 | 0.1943 | 0.2711 | 0.3841 | 0.010 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| adx14 | continuous | 9423/1602 | 25.81 | 23.95 | 4.414e-10 | 2.501e-09 | -0.097 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| adx_rising | categorical | 9378/1595 | 0.3734 | 0.3498 | 0.07582 | 0.1432 | 0.017 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| bb_percent_b | continuous | 9451/1610 | 0.1889 | 0.1823 | 0.3948 | 0.4474 | -0.013 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| bb_width_pctrank | continuous | 8798/1479 | 0.4824 | 0.4405 | 2.025e-07 | 8.607e-07 | -0.084 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| vol_ratio_recent | continuous | 9456/1612 | 0.8183 | 0.7989 | 0.6197 | 0.6372 | -0.008 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| dist_from_sma200_pct | continuous | 7167/1280 | 6.535 | -0.2001 | 2.271e-19 | 1.931e-18 | -0.158 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| atr_pct_of_price | continuous | 9452/1606 | 6.27 | 5.26 | 2.598e-35 | 4.416e-34 | -0.193 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| fib_retracement | continuous | 9153/1549 | 1.073 | 1.085 | 0.002458 | 0.00597 | 0.048 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| fib_dist_from_618 | continuous | 9153/1549 | 0.6378 | 0.5751 | 0.6372 | 0.6372 | 0.007 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| higher_low | categorical | 9456/1612 | 0.588 | 0.5651 | 0.09037 | 0.1536 | 0.016 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| bars_since_prior_high | continuous | 9456/1612 | 19.63 | 18.39 | 7.169e-05 | 0.0002031 | -0.062 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| momentum_signal_nearby | categorical | 9456/1612 | 0.04843 | 0.0428 | 0.3586 | 0.4354 | 0.009 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| harmonic_signal_nearby | categorical | 9456/1612 | 0.07857 | 0.06886 | 0.1934 | 0.2988 | 0.012 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |

## Lojistik regresyon (yorumlanabilir, standardize)

- VIF>10 nedeniyle modelden cikarilan: fib_retracement (VIF=27.2), rsi14 (VIF=17.3)

- Kullanilan ozellik sayisi: 15, n=8388

| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |
|---|---|---|---|---|---|
| const | 1.8985 | 0.0363 | 52.305 | 0 | [1.8274, 1.9697] |
| rsi_min_10 | -0.0004 | 0.0690 | -0.006 | 0.995 | [-0.1356, 0.1347] |
| macd_hist_sign | -0.0800 | 0.0328 | -2.437 | 0.01482 | [-0.1444, -0.0157] |
| macd_hist_rising | 0.0093 | 0.0356 | 0.260 | 0.7948 | [-0.0605, 0.0790] |
| adx14 | 0.0298 | 0.0372 | 0.800 | 0.4239 | [-0.0432, 0.1027] |
| adx_rising | 0.0798 | 0.0376 | 2.121 | 0.03391 | [0.0061, 0.1536] |
| bb_percent_b | 0.0790 | 0.0500 | 1.581 | 0.1139 | [-0.0190, 0.1770] |
| bb_width_pctrank | 0.0093 | 0.0400 | 0.232 | 0.8169 | [-0.0691, 0.0876] |
| vol_ratio_recent | 0.0469 | 0.0399 | 1.177 | 0.2393 | [-0.0312, 0.1251] |
| dist_from_sma200_pct | 0.1563 | 0.0489 | 3.196 | 0.001392 | [0.0604, 0.2521] |
| atr_pct_of_price | 4.3983 | 0.4515 | 9.741 | 2.01e-22 | [3.5134, 5.2833] |
| fib_dist_from_618 | 0.0415 | 0.0671 | 0.618 | 0.5364 | [-0.0900, 0.1730] |
| higher_low | 0.0198 | 0.0407 | 0.486 | 0.6271 | [-0.0600, 0.0995] |
| bars_since_prior_high | 0.1018 | 0.0349 | 2.913 | 0.003578 | [0.0333, 0.1703] |
| momentum_signal_nearby | 0.0746 | 0.0322 | 2.319 | 0.02042 | [0.0115, 0.1378] |
| harmonic_signal_nearby | 0.0322 | 0.0329 | 0.979 | 0.3278 | [-0.0323, 0.0966] |

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.


## Ham Veri

Her aday + ozellikler: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\rally_precursor_candidates.csv`
