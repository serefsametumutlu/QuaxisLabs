---
name: temel-analiz-cercevesi
description: QuaxisLabs Temel Analiz v2 mimarisi — çok-mercekli (Değer/Kalite/Büyüme/Güvenlik) skorlama, mercek-kitap eşlemesi ve tasarım ilkeleri. Yeni skorlama tasarımı, spec yazımı veya analiz motoru kodlaması yapılırken kullan.
---

# Temel Analiz v2 — Çok-Mercekli Mimari

Mevcut 7 bileşenli Radar Skoru korunur; üzerine 4 bağımsız "mercek" eklenir. Kitaplar çelişir (Graham ucuzluk ister, Fisher önemsemez) — çelişki çözülmez, ayrı mercek olur. Bileşik skor = merceklerin şeffaf ağırlıklı ortalaması; kartta mercekler ayrı görünür.

## Mercekler ve kitap kaynakları
| Mercek | Ölçtüğü | Ana kaynaklar | Örnek bileşenler |
|---|---|---|---|
| **DEĞER** | Fiyat ↔ değer farkı | Graham (01), Damodaran (03), mevcut Greenblatt/Carlisle | Güvenlik marjı, F/K·PD/DD kombinasyonu, kazanç getirisi, sektör-göreli çarpan konumu |
| **KALİTE** | Rekabet avantajı + kârlılık kalitesi | Buffett/Clark (02), Fisher (04) | Brüt marj seviyesi+istikrarı, SG&A disiplini, ROE kalıcılığı, faiz yükü, nakit dönüşümü |
| **BÜYÜME** | Büyümenin gücü ve sürdürülebilirliği | Fisher (04), Lynch (05) | Hasılat/kâr büyüme trendi, PEG, Lynch kategorisine göre beklenti kalibrasyonu, Ar-Ge yatırımı |
| **GÜVENLİK** | Muhasebe hilesi + bilanço riski | Schilit (06), Graham (01), mevcut Piotroski | Kırmızı bayrak sayacı (tahakkuk/nakit ayrışması, alacak-envanter/hasılat ayrışması, tek seferlik kalem bağımlılığı), kaldıraç, likidite |

Mercek içi bileşen listesi, formüller ve eşikler bilgi bankası çıkarımı bittikten SONRA `docs/spec/` altında tanımlanır — bu skill iskeleti verir, sayıları spec verir. Sayı uydurma.

## Tasarım ilkeleri
1. **İzlenebilirlik zinciri zorunlu:** her bileşen → `bilgi-bankasi` kimlik kodu (örn. `02/FORMÜL-03`) → spec dosyası → kod docstring → test. Kaynağı gösterilemeyen bileşen eklenemez.
2. **Şirket türü kapsamı:** her mercek bileşeninin geçerli şablonları tanımlı olmalı (sanayi/banka/sigorta/abd_sanayi). Banka için anlamsız metrik (envanter, FD/FAVÖK) o şablonda hiç görünmez.
3. **Sektör ayarlaması:** sektöre-göreli bileşenler `sektor-siniflandirma` skill'indeki normalizasyon kurallarına uyar; sektör verisi yetersizse (n<5) evrensel eşiğe düşer ve bu kartta belirtilir.
4. **Mevcut anayasa geçerli:** saf matematik, Decimal, None yayılımı, eksik bileşen orantısal yeniden dağıtımı, `reasoning_tr`, sürekli enterpolasyon (`_seviye_trend_skoru`/`_asymptote_to` desenleri).
5. **Geriye uyumluluk:** v1 Radar Skoru üretimi bozulmaz; v2 pipeline'da bayrakla açılır, kartta ikisi bir arada sunulabilir (geçiş dönemi).
6. **Nitel maddeler** (Fisher'ın yönetim kalitesi gibi ölçülemeyenler): skora GİRMEZ; Gemini yorum katmanına "değerlendirilecek nitel sorular" listesi olarak gider ve kartta soru/kontrol formatında sunulabilir — sayı üretilmez.
7. **Çift sayma denetimi:** aynı ham veri birden çok mercekte kullanılıyorsa (örn. ROE) quant-uzmani korelasyon notu düşer, bileşik ağırlıkta hesaba katılır.
8. **Rozet dili:** mevcut SAĞLAM/DENGELİ/KARIŞIK/RİSKLİ eşik geleneği (≥8/≥6/≥4) merceklere de uygulanır; kullanıcıya tek skor değil profil gösterilir ("Değer: 8,2 · Kalite: 4,1" bir hikaye anlatır).
