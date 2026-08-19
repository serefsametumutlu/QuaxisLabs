# VRP Sektor Rotasyonu -- Tam BIST Backtest

Olusturulma: 2026-08-19 16:04 UTC

## Kapsam

Sembol sayisi: 657 · Sektor sayisi: 11 · Backtest derinligi: 3.0 yil · Benchmark: XU100.IS · Lider sektor sayisi: 2 · Sepet buyuklugu: 5 · Min sektor uyesi: 5 · Komisyon: %0.10/fill

## ⚠️ Yontem sinirlamalari (bkz. `src/analysis/vrp.py` modul ust notu)

IV, gercek piyasa-fiyatli implied volatilite DEGIL -- kendi GARCH(1,1) ileri-tahmin PROXY'miz (kullanici karari, 2026-08-19: paylasilan quant'in tam formulu/veri kaynagi elde YOK). VRP = IV_proxy - RV (ham fark, oran DEGIL).

⚠️ **13/36 ayda sepet TAMAMEN BOS kaldi** (VRP<0 sartini gecen aday bulunamadi) -- o aylarda portfoy getirisi 0 kabul edildi, GIZLENMEDI (bkz. asagidaki aylik tablo `n_realized=0` satirlari).

## Yorum -- dikkat edilmesi gereken noktalar

- **Kucuk orneklem**: N=36 ay (3 yil). Tek bir piyasa rejimi (2023-2026 BIST boga donemi agirlikli) -- farkli rejimlerde (uzun ayi, yuksek faiz) test EDILMEDI.
- **Ortalama/medyan ayrismasi**: ortalama alpha +2.67 puan/ay ama MEDYAN -0.90 puan/ay -- yani TIPIK bir ay benchmark'i YENMIYOR, sonuc birkac asiri buyuk ayin (en iyi 3 ay: 2025-07 (+59.1), 2025-06 (+32.1), 2025-04 (+22.2)) toplam alpha'nin %118'ini tasimasindan geliyor. Kazanma orani zaten %50'nin ALTINDA (%47.2).
- **Drawdown sepette benchmark'tan KOTU** (-24.4% vs -17.7%) -- yuksek getiri, daha yuksek oynaklik/kayip riskiyle GELIYOR, ucretsiz DEGIL.
- **Bos sepet aylarinda %0 getiri varsayimi**: gercekte nakit/repo getirisi olurdu, bu basitlestirme portfoyu (ve dolayisiyla benchmark karsilastirmasini) fiilen kotumser yonde ETKILER (nakit getirisi eklenseydi sepet sonucu biraz DAHA IYI gorunurdu).

## Ozet Sonuclar

| Metrik | VRP Sepet | Benchmark |
|---|---|---|
| Toplam getiri % | 242.7 | 72.0 |
| CAGR % | 50.8 | 19.8 |
| Maks. Drawdown % | -24.4 | -17.7 |
| Aylik Sharpe (yillıklandirilmis) | 1.00 | -- |
| Benchmark'i yendigi ay orani % | 47.2 | -- |
| Ort. aylik alpha (puan) | 2.67 | -- |
| Medyan aylik alpha (puan) | -0.90 | -- |
| Ay sayisi | 36 | -- |

## Aylik Detay

| Donem | Lider Sektorler | Sepet (n_gerceklesen) | Sepet % | Bench % | Alpha (puan) |
|---|---|---|---|---|---|
| 2023-08 | (yok) | (bos) (0) | 0.00 | 3.33 | -3.33 |
| 2023-09 | (yok) | (bos) (0) | 0.00 | 5.35 | -5.35 |
| 2023-10 | Teknoloji, Sağlık | (bos) (0) | 0.00 | -11.29 | +11.29 |
| 2023-11 | Finans, Sağlık | (bos) (0) | 0.00 | 6.61 | -6.61 |
| 2023-12 | Teknoloji, Finans | (bos) (0) | 0.00 | -5.01 | +5.01 |
| 2024-01 | İletişim, Sağlık | (bos) (0) | 0.00 | 13.40 | -13.40 |
| 2024-02 | İletişim, Teknoloji | (bos) (0) | 0.00 | 5.22 | -5.22 |
| 2024-03 | Teknoloji, İletişim | (bos) (0) | 0.00 | 0.66 | -0.66 |
| 2024-04 | Finans, İletişim | (bos) (0) | 0.00 | 11.48 | -11.48 |
| 2024-05 | Finans, İletişim | (bos) (0) | 0.00 | 3.41 | -3.41 |
| 2024-06 | Finans, Gayrimenkul/GYO | (bos) (0) | 0.00 | -2.02 | +2.02 |
| 2024-07 | İletişim, Gayrimenkul/GYO | (bos) (0) | 0.00 | 4.40 | -4.40 |
| 2024-08 | Teknoloji, Sağlık | (bos) (0) | 0.00 | -6.37 | +6.37 |
| 2024-09 | Sağlık, Gayrimenkul/GYO | IDGYO, ANGEN, TRILC, ONCSM, DAPGM (5) | -14.89 | -7.51 | -7.39 |
| 2024-10 | Gayrimenkul/GYO, İletişim | DZGYO, DGGYO, ZRGYO, AVGYO, DAPGM (5) | 9.61 | -4.99 | +14.59 |
| 2024-11 | Sanayi, Tüketici (Döngüsel) | SKTAS, ETILR, FORMT, BRKO, GZNMI (5) | 9.58 | 8.96 | +0.62 |
| 2024-12 | Gayrimenkul/GYO, Sağlık | IHLGM, AVGYO, RYGYO, TSGYO, EKGYO (5) | -2.22 | 2.89 | -5.11 |
| 2025-01 | Kamu Hizmetleri, Sanayi | GSDDE, SNICA, YAYLA, BIGTK, RYSAS (5) | -6.19 | -1.88 | -4.31 |
| 2025-02 | İletişim, Sağlık | RTALB, ANGEN (2) | -6.56 | 1.40 | -7.96 |
| 2025-03 | Tüketici (Temel), Kamu Hizmetleri | TUKAS, KNFRT, KRVGD, AHGAZ, TATEN (5) | -5.05 | -3.91 | -1.14 |
| 2025-04 | Finans, Tüketici (Döngüsel) | TRHOL, DAGI, ICUGS, SUNTK, ETILR (5) | 18.45 | -3.74 | +22.19 |
| 2025-05 | Tüketici (Temel), İletişim | AVOD, DMRGD, ERSU, OZSUB, BESLR (5) | -0.15 | -1.73 | +1.58 |
| 2025-06 | İletişim, Gayrimenkul/GYO | EDIP, BEGYO, ADESE, KZBGY, MRGYO (5) | 44.01 | 11.89 | +32.12 |
| 2025-07 | Gayrimenkul/GYO, Finans | ADESE, KGYO, PEKGY, OZGYO, INFO (5) | 65.68 | 6.61 | +59.07 |
| 2025-08 | Sağlık, İletişim | EGEPO, ECILC, KRONT, IHAAS (4) | 18.22 | 4.96 | +13.26 |
| 2025-09 | Gayrimenkul/GYO, Tüketici (Döngüsel) | SKTAS, ETILR, AHSGY, AVTUR, AVGYO (5) | 8.25 | -0.53 | +8.78 |
| 2025-10 | İletişim, Tüketici (Temel) | AVOD, CEMZY, PENGD, SELVA, BIGCH (5) | 7.11 | -1.42 | +8.53 |
| 2025-11 | Kamu Hizmetleri, Finans | HEDEF, GRNYO, QNBTR, TEHOL, CRDFA (5) | -9.11 | 0.51 | -9.62 |
| 2025-12 | Finans, Ana Metaller ve Madencilik | BMSTL, ERCB, COSMO, OYYAT, VERUS (5) | 17.16 | 3.44 | +13.72 |
| 2026-01 | Teknoloji, Sağlık | SKYLP, GENIL, LINK, EDATA, SELEC (5) | 6.43 | 18.46 | -12.03 |
| 2026-02 | İletişim, Tüketici (Temel) | SELVA, SEGMN, DCTTR, BYDNR, AVOD (5) | -5.57 | -2.02 | -3.55 |
| 2026-03 | İletişim, Kamu Hizmetleri | IHAAS, AKFYE, MOGAN, CONSE, GWIND (5) | 17.38 | -3.06 | +20.44 |
| 2026-04 | Finans, Kamu Hizmetleri | MARKA, CATES, KLNMA, VKFYO, RALYH (5) | 12.21 | 11.07 | +1.14 |
| 2026-05 | Sanayi, Teknoloji | KONTR, EDATA, BORLS, GLRMK, DOGUB (5) | -16.65 | -4.63 | -12.01 |
| 2026-06 | Teknoloji, Sanayi | GSDDE, ANELE, PKART, PRKAB, PASEU (5) | -3.70 | 4.72 | -8.42 |
| 2026-07 | Finans, Gayrimenkul/GYO | DGGYO, OSTIM, BLCYT, PAGYO, ISGYO (5) | -5.87 | -6.55 | +0.68 |

## Ham Veri

Aylik CSV: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\vrp_sektor_rotasyon_aylik.csv`