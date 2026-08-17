# AB=CD Basari Faktoru Analizi -- Tum Para Birimleri

Sembol sayisi: 657 | Zaman dilimleri: 60, 120, 240, 1D | Para birimleri: TRY (HER BIRI AYRI analiz edildi -- bkz. `abcd_factor_analysis.py` 'Kapsam siniri' notu) | Gecmis derinligi: ~2.0 yil


---

# TRY

# AB=CD Basari Faktoru Analizi

> Butun bulgular ILISKISEL dildedir, NEDENSELLIK iddia edilmez -- 'X ozelligi basariyi artirir' turu ifadeler YASAKTIR; sadece 'kazananlarda X ile birlikte gorulur, n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir.

- Toplam islem: 3219 (train=2253, holdout=966, ozellik-hesaplanamadigi-icin-atlanan=0)
- Kronolojik split esigi (giris zamani): 2026-02-11 13:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| rsi14 | continuous | 1125/1128 | 49.06 | 49.21 | 0.7774 | 0.9386 | 0.007 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| macd_hist_slope | continuous | 1125/1128 | 0.01567 | 0.04992 | 0.01808 | 0.2531 | -0.058 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| volume_ratio | continuous | 1125/1128 | 1.143 | 1.145 | 0.3518 | 0.8035 | 0.023 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| atr_norm_cd_speed | continuous | 1125/1128 | 0.6054 | 0.6121 | 0.9352 | 0.9386 | 0.002 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| cd_ratio_dev | continuous | 1125/1128 | 0.02409 | 0.02414 | 0.9069 | 0.9386 | 0.003 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| d_proximity_50bar | continuous | 1125/1128 | 0.4351 | 0.4537 | 0.2869 | 0.8035 | 0.026 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| cd_duration_bars | continuous | 1125/1128 | 13.1 | 12.47 | 0.2184 | 0.8035 | -0.030 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| d_body_range_ratio | continuous | 1107/1109 | 0.4025 | 0.3947 | 0.534 | 0.8306 | -0.015 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| price_vs_sma200_pct | continuous | 960/967 | 2.18 | 2.195 | 0.2748 | 0.8035 | 0.029 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| adx14 | continuous | 1124/1128 | 25.54 | 25.67 | 0.9386 | 0.9386 | 0.002 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| bb_percent_b | continuous | 1125/1128 | 0.4844 | 0.4833 | 0.9018 | 0.9386 | -0.003 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| macd_hist_sign | categorical | 1125/1128 | 0.008 | 0.04078 | 0.4617 | 0.808 | 0.016 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| above_sma50 | categorical | 1112/1117 | 0.4469 | 0.4655 | 0.4017 | 0.8035 | 0.018 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |
| above_sma200 | categorical | 960/967 | 0.4875 | 0.5109 | 0.3272 | 0.8035 | 0.022 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |

## Lojistik regresyon (yorumlanabilir, standardize)

- Kullanilan ozellik sayisi: 14, n=1893

| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |
|---|---|---|---|---|---|
| const | -0.0073 | 0.0461 | -0.159 | 0.8738 | [-0.0977, 0.0830] |
| rsi14 | -0.0690 | 0.1403 | -0.492 | 0.623 | [-0.3439, 0.2060] |
| macd_hist_slope | -0.0385 | 0.0474 | -0.811 | 0.4172 | [-0.1314, 0.0545] |
| volume_ratio | -0.0032 | 0.0537 | -0.059 | 0.9527 | [-0.1084, 0.1020] |
| atr_norm_cd_speed | 0.0277 | 0.0622 | 0.446 | 0.6557 | [-0.0942, 0.1497] |
| cd_ratio_dev | -0.0081 | 0.0463 | -0.174 | 0.8617 | [-0.0988, 0.0827] |
| d_proximity_50bar | 0.0157 | 0.1210 | 0.130 | 0.8965 | [-0.2215, 0.2530] |
| cd_duration_bars | 0.0612 | 0.0573 | 1.069 | 0.2853 | [-0.0511, 0.1736] |
| d_body_range_ratio | 0.0464 | 0.0463 | 1.001 | 0.3168 | [-0.0444, 0.1371] |
| price_vs_sma200_pct | 0.0366 | 0.0603 | 0.607 | 0.5441 | [-0.0816, 0.1548] |
| adx14 | 0.0002 | 0.0512 | 0.003 | 0.9976 | [-0.1002, 0.1005] |
| bb_percent_b | 0.2259 | 0.1266 | 1.785 | 0.07425 | [-0.0221, 0.4740] |
| macd_hist_sign | -0.1274 | 0.0628 | -2.027 | 0.04268 | [-0.2505, -0.0042] |
| above_sma50 | -0.1181 | 0.1076 | -1.097 | 0.2725 | [-0.3291, 0.0929] |
| above_sma200 | -0.0800 | 0.0637 | -1.255 | 0.2094 | [-0.2049, 0.0449] |

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.
