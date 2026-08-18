# AB=CD Basari Faktoru Analizi

> Butun bulgular ILISKISEL dildedir, NEDENSELLIK iddia edilmez -- 'X ozelligi PRZ'yi dogrular' turu ifadeler YASAKTIR; sadece 'sonradan dogrulanan (vindicated) PRZ olaylarinda X ile birlikte gorulur, n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir. 'Kazanan/kaybeden' (pnl) DEGIL, 'PRZ dokunmasi sonradan gercek onayli bir formasyona mi donustu (vindicated=1) yoksa hicbir zaman onaylanmadi mi (false-start=0)' ikili sonucu test edilir -- bkz. docs/spec/ABCD_XABCD_V2_ARASTIRMASI.md.

- Toplam islem: 5344 (train=3741, holdout=1603, ozellik-hesaplanamadigi-icin-atlanan=0)
- Kronolojik split esigi (giris zamani): 2026-03-05 09:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| rsi14 | continuous | 529/3212 | 47.73 | 54.44 | 4.889e-17 | 4.25e-16 | 0.227 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| macd_hist_slope | continuous | 529/3212 | 0.2075 | -1.133 | 9.866e-05 | 0.0001425 | 0.106 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| volume_ratio | continuous | 529/3212 | 1.128 | 1.256 | 3.629e-10 | 5.896e-10 | 0.170 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| atr_norm_cd_speed | continuous | 529/3212 | 0.4393 | 0.4447 | 0.3036 | 0.3036 | 0.028 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| cd_ratio_dev | continuous | 0/0 *(GUCU YETERSIZ)* | N/A | N/A | N/A | N/A | N/A | gucu yetersiz (underpowered) -- etki YOK denemez, sadece orneklem kucuk |
| d_proximity_50bar | continuous | 529/3212 | 0.4295 | 0.565 | 1.31e-11 | 2.839e-11 | 0.183 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| cd_duration_bars | continuous | 529/3212 | 12.23 | 9.87 | 6.539e-17 | 4.25e-16 | -0.224 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| d_body_range_ratio | continuous | 528/3186 | 0.4449 | 0.5347 | 4.331e-12 | 1.126e-11 | 0.188 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| price_vs_sma200_pct | continuous | 353/2302 | 1.811 | 6.176 | 0.0004375 | 0.0005687 | 0.116 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| adx14 | continuous | 529/3210 | 22.86 | 24.11 | 0.007049 | 0.007636 | 0.073 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| bb_percent_b | continuous | 529/3212 | 0.4454 | 0.6436 | 5.411e-14 | 2.345e-13 | 0.204 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| macd_hist_sign | categorical | 529/3212 | -0.104 | 0.2067 | 2.675e-11 | 4.967e-11 | 0.109 (Cramer's V (chi2)) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| above_sma50 | categorical | 521/3157 | 0.4357 | 0.6044 | 6.965e-13 | 2.264e-12 | 0.118 (Cramer's V (chi2)) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| above_sma200 | categorical | 353/2302 | 0.5212 | 0.6056 | 0.003221 | 0.003806 | 0.057 (Cramer's V (chi2)) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |

## Lojistik regresyon (yorumlanabilir, standardize)

- Train'de HICBIR degeri olmadigi icin BASTAN cikarilan: cd_ratio_dev

- VIF>10 nedeniyle modelden cikarilan: rsi14 (VIF=17.7)

- Kullanilan ozellik sayisi: 12, n=2631

| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |
|---|---|---|---|---|---|
| const | -2.0430 | 0.0665 | -30.728 | 2.432e-207 | [-2.1734, -1.9127] |
| macd_hist_slope | 0.0254 | 0.0508 | 0.500 | 0.6168 | [-0.0742, 0.1251] |
| volume_ratio | -0.3949 | 0.0926 | -4.264 | 2.006e-05 | [-0.5764, -0.2134] |
| atr_norm_cd_speed | 0.4410 | 0.0760 | 5.805 | 6.425e-09 | [0.2921, 0.5899] |
| d_proximity_50bar | -0.0231 | 0.1325 | -0.174 | 0.8615 | [-0.2828, 0.2365] |
| cd_duration_bars | 0.4282 | 0.0652 | 6.572 | 4.955e-11 | [0.3005, 0.5560] |
| d_body_range_ratio | -0.2832 | 0.0586 | -4.830 | 1.364e-06 | [-0.3981, -0.1683] |
| price_vs_sma200_pct | -0.1918 | 0.0905 | -2.120 | 0.03397 | [-0.3691, -0.0145] |
| adx14 | -0.1112 | 0.0676 | -1.644 | 0.1001 | [-0.2437, 0.0213] |
| bb_percent_b | -0.4426 | 0.1853 | -2.388 | 0.01695 | [-0.8059, -0.0793] |
| macd_hist_sign | 0.0902 | 0.1342 | 0.672 | 0.5016 | [-0.1728, 0.3531] |
| above_sma50 | 0.1785 | 0.1513 | 1.180 | 0.2382 | [-0.1181, 0.4750] |
| above_sma200 | 0.0704 | 0.0797 | 0.883 | 0.3771 | [-0.0859, 0.2267] |

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.
