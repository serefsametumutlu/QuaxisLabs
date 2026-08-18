# BIST Yeni İş Anlaşmaları -- Yıllık Hasılat Kıyaslaması Araştırması

Kaynak: `bist-yeni-is-anlasmalari-2025-2026.md` (statik dökümü, 134 hisse, 2025-01-01 – 2026-12-31 KAP bildirimleri).

## ⚠️ Metodoloji -- OKUMADAN sonuçları yorumlamayın

- **Yenileme sözleşmeleri hariç** -- "Sözleşme yenilenmesi" ifadesi geçen kayıtlar toplama katılmadı (15 kayıt).
- **Belirsiz (çoklu para birimi karışık toplam) tutarlar toplama katılmadı** -- her (şirket, yıl) hücresi için "kapsam %" (kaç anlaşmanın sayılabildiği) ayrıca gösterilir; düşük kapsamda gerçek toplam muhtemelen tablodakinden YÜKSEKTİR.
- **Döviz çevrimi anlaşma TARİHİNDEKİ tarihsel USDTRY/EURTRY/GBPTRY kapanışıyla** yapıldı -- güncel kur DEĞİL.
- **Önceki yıl hasılatı** DB'deki `revenue_cum` (yıl sonu, period=12) alanından -- bu veri şirkette yoksa (henüz açıklanmamış/DB'de yok) oran hesaplanamaz, `N/A` gösterilir (ASLA 0 varsayılmaz).
- Eşik: yeni iş toplamı ≥ önceki yıl hasılatının **%20 fazlası** (oran ≥ 1.20).

- Toplam kayıt: 1182 (yenileme hariç: 1167)
- Hasılat verisiyle kıyaslanabilen (ticker, yıl) hücresi: 202/203
- Eşiği geçen (ticker, yıl) hücresi: 13

## Eşiği Geçenler (oran ≥ 1.20)

| Ticker | Yıl | Yeni İş Toplamı (TL) | Önceki Yıl Hasılatı (TL) | Oran | Kapsam % | n anlaşma |
|---|---|---|---|---|---|---|
| TEHOL | 2025 | 837,894,583 | 40,408,959 | 20.74 | 100% | 2 |
| PAPIL | 2025 | 902,015,157 | 306,387,969 | 2.94 | 100% | 3 |
| FORTE | 2025 | 6,248,298,714 | 2,331,713,132 | 2.68 | 100% | 26 |
| ALTNY | 2026 | 8,494,918,203 | 3,697,439,737 | 2.30 | 100% | 13 |
| CVKMD | 2025 | 7,314,327,217 | 4,103,788,869 | 1.78 | 100% | 9 |
| PATEK | 2025 | 2,362,678,043 | 1,345,059,230 | 1.76 | 100% | 4 |
| ONRYT | 2025 | 1,640,344,519 | 936,766,419 | 1.75 | 100% | 7 |
| ONCSM | 2025 | 829,148,535 | 490,177,860 | 1.69 | 100% | 16 |
| ASELS | 2025 | 256,086,637,337 | 157,339,901,315 | 1.63 | 100% | 30 |
| ASTOR | 2026 | 56,127,359,835 | 38,834,019,873 | 1.45 | 100% | 11 |
| GLRMK | 2025 | 61,977,272,264 | 45,177,026,541 | 1.37 | 100% | 9 |
| SAYAS | 2025 | 2,666,767,085 | 2,195,314,938 | 1.21 | 100% | 19 |
| KONTR | 2025 | 15,593,511,303 | 12,968,588,429 | 1.20 | 100% | 12 |

## Tüm Hücreler (ham veri)

Ham tablo: `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\is_anlasmalari_yillik.csv`
