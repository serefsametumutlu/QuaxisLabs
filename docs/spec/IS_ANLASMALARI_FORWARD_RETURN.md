# BIST Yeni Is Anlasmalari -- Esik (>=%20) Forward-Return Validasyonu

## Metodoloji

- Olcum tarihi: 2025-12-31 kapanisi (entry) -> 126 islem gunu (~6 ay) SONRAKI kapanis (exit). SADECE 2025 yili (tek TAM gerceklesmis yil, forward-pencere bugune -- 2026-08-18 -- kadar TAMAMEN gerceklesmis).
- Toplam (ticker,2025) hucresi: 109, forward-return hesaplanan: 109 (0 atlandi -- fiyat verisi yetersiz).
- Esigi GECEN: n=11 · Esigi GECMEYEN: n=98

> **NEDENSELLIK YASAK:** bulgular ILISKISEL dildedir -- 'esigi gecmek getiriyi artirir' turu ifadeler KULLANILMAZ, sadece 'esigi gecen grupta forward-return farkli/ayni dagilimda, n=.., p=..' turu ifadeler kullanilir. n cok kucuk (134 sirketlik statik dokumun SADECE 2025 alt-kumesi) -- bu KESIN bir kanit DEGIL, bir ILK ISARETTIR.

## Sonuc

| Grup | n | Medyan Forward-Return % | Ortalama Forward-Return % | Pozitif Getiri Orani % |
|---|---|---|---|---|
| Esigi GECEN | 11 | 5.09 | 9.85 | 63.6 |
| Esigi GECMEYEN | 98 | 16.47 | 47.14 | 71.4 |

Mann-Whitney U testi: p = 0.5164 -- iki grup dagilimi arasinda ISTATISTIKSEL OLARAK ANLAMLI FARK bulunamadi (p>=0.05)

## Ham Veri

`C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\data\abcd_cache\is_anlasmalari_forward_return.csv`
