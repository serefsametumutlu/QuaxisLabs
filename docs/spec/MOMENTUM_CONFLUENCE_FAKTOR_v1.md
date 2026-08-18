# AB=CD Basari Faktoru Analizi

> Momentum Confluence V1 -- kazanan/kaybeden ILISKISEL analizi. 'X ozelligi kazandirir' turu ifadeler YASAKTIR; sadece 'kazananlarda X ile birlikte gorulur, n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir.

- Toplam islem: 8596 (train=6017, holdout=2579, ozellik-hesaplanamadigi-icin-atlanan=0)
- Kronolojik split esigi (giris zamani): 2026-03-05 13:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| ema_spread_pct | continuous | 3443/2574 | 0.4608 | 0.4644 | 0.4024 | 0.5628 | 0.013 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| volume_ratio | continuous | 3443/2574 | 2.741 | 2.874 | 0.003259 | 0.0286 | 0.044 (rank-biserial r) | holdout'ta dogrulandi (ayni yon, duzeltmesiz p<0.05) |
| downward_streak_before_flip | continuous | 3443/2574 | 6.688 | 6.824 | 0.006356 | 0.0286 | 0.041 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| wt1_at_signal | continuous | 0/0 *(GUCU YETERSIZ)* | N/A | N/A | N/A | N/A | N/A | gucu yetersiz (underpowered) -- etki YOK denemez, sadece orneklem kucuk |
| rsi14 | continuous | 3443/2574 | 54.99 | 55.25 | 0.1615 | 0.2907 | 0.021 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| adx14 | continuous | 3405/2548 | 23.09 | 22.93 | 0.857 | 0.857 | -0.003 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| bb_percent_b | continuous | 3443/2574 | 0.7541 | 0.7509 | 0.5582 | 0.628 | -0.009 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| price_vs_sma50_pct | continuous | 3354/2481 | 0.8659 | 1.018 | 0.04641 | 0.1392 | 0.030 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| body_range_ratio | continuous | 3406/2515 | 0.6641 | 0.6669 | 0.4377 | 0.5628 | 0.012 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| above_sma200 | categorical | 2520/1702 | 0.523 | 0.5517 | 0.0716 | 0.1611 | 0.028 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |

## Lojistik regresyon (yorumlanabilir, standardize)

- Train'de HICBIR degeri olmadigi icin BASTAN cikarilan: wt1_at_signal

- Kullanilan ozellik sayisi: 9, n=4157

| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |
|---|---|---|---|---|---|
| const | 0.4083 | 0.0318 | 12.858 | 7.801e-38 | [0.3460, 0.4705] |
| ema_spread_pct | 0.0098 | 0.0328 | 0.299 | 0.7647 | [-0.0544, 0.0741] |
| volume_ratio | -0.0736 | 0.0349 | -2.108 | 0.03501 | [-0.1421, -0.0052] |
| downward_streak_before_flip | -0.0724 | 0.0376 | -1.922 | 0.0546 | [-0.1462, 0.0014] |
| rsi14 | -0.1928 | 0.0843 | -2.288 | 0.02216 | [-0.3579, -0.0276] |
| adx14 | 0.0179 | 0.0338 | 0.529 | 0.5965 | [-0.0484, 0.0841] |
| bb_percent_b | 0.1392 | 0.0560 | 2.487 | 0.01288 | [0.0295, 0.2490] |
| price_vs_sma50_pct | 0.0663 | 0.0592 | 1.120 | 0.2629 | [-0.0498, 0.1824] |
| body_range_ratio | -0.0262 | 0.0347 | -0.756 | 0.4496 | [-0.0941, 0.0417] |
| above_sma200 | -0.0530 | 0.0360 | -1.475 | 0.1402 | [-0.1235, 0.0174] |

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.
