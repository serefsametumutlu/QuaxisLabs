---
name: sektor-siniflandirma
description: BİST ve NASDAQ hisselerinin sektörel sınıflandırması, evren (universe) yönetimi ve sektör-içi normalizasyon kuralları. Sektör gruplama, evren çekme, sektör-göreli skorlama veya dashboard işlerinde kullan.
---

# Sektör Sınıflandırma ve Evren Yönetimi

## Ortak sektör taksonomisi
İki piyasa TEK ortak üst-sektör setine eşlenir ki kart ve dashboard tutarlı olsun. Önerilen üst set (GICS'ten sadeleştirilmiş 11 grup): Enerji, Ana Metaller ve Madencilik, Sanayi, Tüketici (Döngüsel), Tüketici (Temel), Sağlık, Finans, Teknoloji, İletişim, Kamu Hizmetleri, Gayrimenkul/GYO. Her hisse: `ust_sektor` (ortak) + `alt_sektor` (kaynak sistemin ham etiketi) + `sirket_turu` (sanayi/banka/sigorta/gyo — skor şablonu seçimi için, sektörden AYRI kavram).

## Veri kaynakları
- **BİST:** KAP şirket listesi + sektör bilgisi (`scripts/explore_kap_sektor.py` mevcut — oradan başla) ve/veya İş Yatırım şirket listesi. Endeks üyelikleri (BIST100/30) ayrıca etiketlenebilir.
- **NASDAQ/ABD:** SEC EDGAR `company_tickers.json` (tüm ticker evreni) + submissions API'sindeki SIC kodu → SIC-üst-sektör eşleme tablosu (statik dict, modülde belgeli). Alternatif zenginleştirme: stockanalysis.com fetcher'ı zaten mevcut.
- Eşlemeler `src/fetchers/` katmanında; SIC→sektör ve KAP→sektör çeviri tabloları elle denetlenebilir statik sözlük olarak tutulur (sürprizsiz, test edilebilir).

## Evren (universe) yönetimi
- `db/models.py`'deki Company tablosuna sektör alanları eklenir (migration notu ile); evren çekimi `scripts/refresh_universe.py` tarzı bir scriptle periyodik yenilenir, sonuç DB'de cache'lenir (mevcut `is_data_fresh` deseni).
- NASDAQ evreni büyük (binlerce ticker) — toplu tarama işlerinde rate-limit'e saygılı, kaldığı yerden devam edebilen (checkpoint) toplu çekim tasarla; tek seferde tüm evreni canlı çekmeye çalışma, kademeli doldur.
- Kapsam netliği: "NASDAQ" ile kastedilen NASDAQ-listeli hisseler mi, tüm ABD mi — kullanıcıyla netleştirilmedikçe NASDAQ-listeli varsay; filtre SEC verisindeki exchange alanından yapılır.

## Sektör-içi normalizasyon (quant kuralları)
1. `n >= 5` şirket yoksa sektör karşılaştırması DEVRE DIŞI → evrensel eşikler kullanılır ve çıktıda "sektör karşılaştırması için yetersiz örneklem (n=X)" görünür. Sahte kesinlik yasak (proje geçmişindeki peer-karşılaştırma kaldırma kararının nedeni).
2. Sektör istatistikleri robust hesaplanır: medyan + MAD (veya winsorize edilmiş persentiller); uç değerler %5-%95 bandında kırpılır.
3. Sektör-göreli puan TEK BAŞINA kullanılmaz — mutlak taban/tavanla harmanlanır ("kötü sektörün en iyisi" mutlak yüksek puan alamaz). Harman oranı spec'te gerekçelendirilir.
4. Sektör istatistikleri DB'de dönem bazlı cache'lenir (her kart üretiminde tüm evreni yeniden hesaplamak yok); tazelik kuralı tanımlanır.
5. Banka/sigorta kendi şirket-türü grubu içinde karşılaştırılır, asla sanayi havuzuyla değil.
