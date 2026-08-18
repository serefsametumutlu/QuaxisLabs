# AB=CD Basari Faktoru Analizi

> Momentum Confluence V2 -- kazanan/kaybeden ILISKISEL analizi. 'X ozelligi kazandirir' turu ifadeler YASAKTIR; sadece 'kazananlarda X ile birlikte gorulur, n=.., p=.., FDR q=.., holdout: dogrulandi/dogrulanmadi' turu ifadeler kullanilir.

- Toplam islem: 2588 (train=1812, holdout=776, ozellik-hesaplanamadigi-icin-atlanan=0)
- Kronolojik split esigi (giris zamani): 2026-02-26 13:00:00+03:00

## Tek-degiskenli testler (train, FDR-duzeltmeli; holdout dogrulama)

| Ozellik | Tur | n_win/n_loss (train) | Kazanan ort/oran | Kaybeden ort/oran | p (train) | FDR q | Etki buyuklugu | Holdout durumu |
|---|---|---|---|---|---|---|---|---|
| ema_spread_pct | continuous | 1036/776 | 0.3695 | 0.3846 | 0.08129 | 0.1364 | 0.048 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| volume_ratio | continuous | 1036/776 | 2.992 | 3.212 | 0.001073 | 0.005365 | 0.090 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| downward_streak_before_flip | continuous | 1036/776 | 5.221 | 5.845 | 7.111e-06 | 7.111e-05 | 0.122 (rank-biserial r) | muhtemelen sans (train'de FDR-anlamli, holdout'ta dogrulanmadi) |
| wt1_at_signal | continuous | 1036/776 | -17.53 | -19.04 | 0.03888 | 0.1166 | -0.057 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| rsi14 | continuous | 1036/776 | 57.57 | 57.84 | 0.4004 | 0.5005 | 0.023 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| adx14 | continuous | 1031/775 | 21.48 | 21.33 | 0.8795 | 0.8879 | 0.004 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| bb_percent_b | continuous | 1036/776 | 0.8627 | 0.8516 | 0.08184 | 0.1364 | -0.048 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| price_vs_sma50_pct | continuous | 1014/752 | 2.033 | 2.411 | 0.04662 | 0.1166 | 0.055 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| body_range_ratio | continuous | 1036/776 | 0.7224 | 0.7176 | 0.8879 | 0.8879 | -0.004 (rank-biserial r) | train'de FDR (q<0.10) esigini gecmedi |
| above_sma200 | categorical | 745/511 | 0.5597 | 0.6086 | 0.09576 | 0.1368 | 0.047 (Cramer's V (chi2)) | train'de FDR (q<0.10) esigini gecmedi |

## Lojistik regresyon (yorumlanabilir, standardize)

- Kullanilan ozellik sayisi: 10, n=1256

| Ozellik | Katsayi | Std.Hata | Wald z | p | %95 CI |
|---|---|---|---|---|---|
| const | 0.3859 | 0.0582 | 6.633 | 3.298e-11 | [0.2719, 0.4999] |
| ema_spread_pct | -0.0515 | 0.0661 | -0.779 | 0.4362 | [-0.1810, 0.0781] |
| volume_ratio | -0.0801 | 0.0692 | -1.157 | 0.2474 | [-0.2158, 0.0556] |
| downward_streak_before_flip | -0.0353 | 0.0695 | -0.508 | 0.6116 | [-0.1714, 0.1009] |
| wt1_at_signal | 0.2379 | 0.0869 | 2.739 | 0.006158 | [0.0677, 0.4082] |
| rsi14 | -0.1987 | 0.1212 | -1.640 | 0.1011 | [-0.4363, 0.0388] |
| adx14 | 0.0485 | 0.0629 | 0.771 | 0.4409 | [-0.0748, 0.1717] |
| bb_percent_b | 0.1952 | 0.0873 | 2.236 | 0.02534 | [0.0241, 0.3664] |
| price_vs_sma50_pct | -0.1002 | 0.0993 | -1.009 | 0.3129 | [-0.2949, 0.0944] |
| body_range_ratio | 0.0710 | 0.0651 | 1.090 | 0.2758 | [-0.0567, 0.1986] |
| above_sma200 | -0.0665 | 0.0644 | -1.032 | 0.3019 | [-0.1928, 0.0598] |

> **Not:** Tum bulgular iliskiseldir (association), nedensellik iddiasi ICERMEZ. 'Kazananlarda X ile birlikte gorulur' seklinde okunmalidir, 'X basariyi artirir' DEGIL.
