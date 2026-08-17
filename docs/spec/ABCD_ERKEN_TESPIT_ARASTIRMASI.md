# AB=CD Erken Tespit Arastirmasi

Sembol sayisi: 657 | Zaman dilimleri: 1D, 240 | Gecmis derinligi: ~2.0 yil | GBM-null tohum: 42

> Bu rapor bir OLASILIK MODELI DEGILDIR -- ABC olusup C onaylandiktan sonra, belirli bir CD-ilerleme araliginda gozlemlenen tarihsel HAM FREKANS + Wilson %95 guven araligidir. Sonuclar, ayni pipeline'in gerceklesmis volatiliteye kalibre edilmis bir GBM (geometrik Brownian hareket) rastgele-yurus null serisiyle karsilastirmasiyla birlikte okunmalidir -- 'anlamli farkli' ETIKETLENMEYEN hucreler rastgele yurusten ayirt edilemez.


---

# tf=1D

- Veri bulunan sembol sayisi: 624
- T_max (timeout esigi, 560 onaylanmis sinyalin d_bar-c_bar dagiliminin p95'i): 23 bar
- Toplam ABC adayi: 28334 (basari=535, asiri-uzama=7484, reshuffle=18541, timeout(belirsiz)=1774)

> Null-hipotez karsilastirmasi: 12 hucre (gercek VE null'da n>=30 olan) test edildi, Bonferroni-tipi etkin anlamlilik esigi ~= 0.00417.

## Kova tablosu -- HAM frekans + Wilson %95 GA + null-karsilastirma

- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 0-20% araligindayken) D'ye ulasma sikligi: 160/21833 (%95 GA: 0.006-0.009) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 20-40% araligindayken) D'ye ulasma sikligi: 237/16998 (%95 GA: 0.012-0.016) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 40-60% araligindayken) D'ye ulasma sikligi: 549/17204 (%95 GA: 0.029-0.035) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 60-80% araligindayken) D'ye ulasma sikligi: 1044/13548 (%95 GA: 0.073-0.082) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 80-100% araligindayken) D'ye ulasma sikligi: 812/9642 (%95 GA: 0.079-0.090) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 100%+ araligindayken) D'ye ulasma sikligi: 23/13126 (%95 GA: 0.001-0.003) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 0-20% araligindayken) D'ye ulasma sikligi: 247/28523 (%95 GA: 0.008-0.010) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 20-40% araligindayken) D'ye ulasma sikligi: 344/18153 (%95 GA: 0.017-0.021) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 40-60% araligindayken) D'ye ulasma sikligi: 570/15020 (%95 GA: 0.035-0.041) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 60-80% araligindayken) D'ye ulasma sikligi: 671/11018 (%95 GA: 0.057-0.066) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 80-100% araligindayken) D'ye ulasma sikligi: 326/7611 (%95 GA: 0.039-0.048) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 100%+ araligindayken) D'ye ulasma sikligi: 2/10408 (%95 GA: 0.000-0.001) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.


| Yon | Kova | n_basari | n_toplam | oran | Wilson GA | Guven | null-karsilastirma | p |
|---|---|---|---|---|---|---|---|---|
| LONG | 0-20% | 160 | 21833 | 0.007 | [0.006, 0.009] | GUVENILIR | nulldan ayirt edilemiyor | 0.2874 |
| LONG | 20-40% | 237 | 16998 | 0.014 | [0.012, 0.016] | GUVENILIR | nulldan ayirt edilemiyor | 0.0052 |
| LONG | 40-60% | 549 | 17204 | 0.032 | [0.029, 0.035] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 60-80% | 1044 | 13548 | 0.077 | [0.073, 0.082] | GUVENILIR | nulldan ayirt edilemiyor | 0.0584 |
| LONG | 80-100% | 812 | 9642 | 0.084 | [0.079, 0.090] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 100%+ | 23 | 13126 | 0.002 | [0.001, 0.003] | GUVENILIR | nulldan ayirt edilemiyor | 0.0252 |
| SHORT | 0-20% | 247 | 28523 | 0.009 | [0.008, 0.010] | GUVENILIR | anlamli farkli | 0.0003 |
| SHORT | 20-40% | 344 | 18153 | 0.019 | [0.017, 0.021] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 40-60% | 570 | 15020 | 0.038 | [0.035, 0.041] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 60-80% | 671 | 11018 | 0.061 | [0.057, 0.066] | GUVENILIR | anlamli farkli | 0.0004 |
| SHORT | 80-100% | 326 | 7611 | 0.043 | [0.039, 0.048] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 100%+ | 2 | 10408 | 0.000 | [0.000, 0.001] | GUVENILIR | nulldan ayirt edilemiyor | 0.1120 |


---

# tf=240

- Veri bulunan sembol sayisi: 564
- T_max (timeout esigi, 854 onaylanmis sinyalin d_bar-c_bar dagiliminin p95'i): 26 bar
- Toplam ABC adayi: 45895 (basari=809, asiri-uzama=12136, reshuffle=30209, timeout(belirsiz)=2741)

> Null-hipotez karsilastirmasi: 12 hucre (gercek VE null'da n>=30 olan) test edildi, Bonferroni-tipi etkin anlamlilik esigi ~= 0.00417.

## Kova tablosu -- HAM frekans + Wilson %95 GA + null-karsilastirma

- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 0-20% araligindayken) D'ye ulasma sikligi: 352/44796 (%95 GA: 0.007-0.009) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 20-40% araligindayken) D'ye ulasma sikligi: 510/30987 (%95 GA: 0.015-0.018) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 40-60% araligindayken) D'ye ulasma sikligi: 1048/27572 (%95 GA: 0.036-0.040) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 60-80% araligindayken) D'ye ulasma sikligi: 1414/21848 (%95 GA: 0.062-0.068) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 80-100% araligindayken) D'ye ulasma sikligi: 1084/15552 (%95 GA: 0.066-0.074) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, LONG yonunde CD ilerlemesi 100%+ araligindayken) D'ye ulasma sikligi: 20/21893 (%95 GA: 0.001-0.001) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 0-20% araligindayken) D'ye ulasma sikligi: 408/50052 (%95 GA: 0.007-0.009) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 20-40% araligindayken) D'ye ulasma sikligi: 533/29371 (%95 GA: 0.017-0.020) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 40-60% araligindayken) D'ye ulasma sikligi: 892/24299 (%95 GA: 0.034-0.039) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 60-80% araligindayken) D'ye ulasma sikligi: 1014/18142 (%95 GA: 0.053-0.059) [GUVENILIR], null-karsilastirma: anlamli farkli.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 80-100% araligindayken) D'ye ulasma sikligi: 434/12778 (%95 GA: 0.031-0.037) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.
- Tarihsel bu asamada (ABC olusup C onaylandiktan sonra, SHORT yonunde CD ilerlemesi 100%+ araligindayken) D'ye ulasma sikligi: 14/18129 (%95 GA: 0.000-0.001) [GUVENILIR], null-karsilastirma: nulldan ayirt edilemiyor.


| Yon | Kova | n_basari | n_toplam | oran | Wilson GA | Guven | null-karsilastirma | p |
|---|---|---|---|---|---|---|---|---|
| LONG | 0-20% | 352 | 44796 | 0.008 | [0.007, 0.009] | GUVENILIR | nulldan ayirt edilemiyor | 0.1383 |
| LONG | 20-40% | 510 | 30987 | 0.016 | [0.015, 0.018] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 40-60% | 1048 | 27572 | 0.038 | [0.036, 0.040] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 60-80% | 1414 | 21848 | 0.065 | [0.062, 0.068] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 80-100% | 1084 | 15552 | 0.070 | [0.066, 0.074] | GUVENILIR | anlamli farkli | 0.0000 |
| LONG | 100%+ | 20 | 21893 | 0.001 | [0.001, 0.001] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 0-20% | 408 | 50052 | 0.008 | [0.007, 0.009] | GUVENILIR | nulldan ayirt edilemiyor | 0.2085 |
| SHORT | 20-40% | 533 | 29371 | 0.018 | [0.017, 0.020] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 40-60% | 892 | 24299 | 0.037 | [0.034, 0.039] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 60-80% | 1014 | 18142 | 0.056 | [0.053, 0.059] | GUVENILIR | anlamli farkli | 0.0000 |
| SHORT | 80-100% | 434 | 12778 | 0.034 | [0.031, 0.037] | GUVENILIR | nulldan ayirt edilemiyor | 0.2929 |
| SHORT | 100%+ | 14 | 18129 | 0.001 | [0.000, 0.001] | GUVENILIR | nulldan ayirt edilemiyor | 0.0130 |
