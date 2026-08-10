---
name: kitap-bilgi-cikarma
description: kitaplar/ klasöründeki yatırım kitabı PDF'lerinden ilke/formül/eşik/kontrol listesi/kırmızı bayrak çıkarma prosedürü ve bilgi-bankasi/ çıktı standardı. Kitap okuma, bilgi çıkarma veya bilgi bankası işlerinde kullan.
---

# Kitap Bilgi Çıkarma Prosedürü

Hedef: 6 kitabın uygulanabilir bilgisini `bilgi-bankasi/` altına, koda dönüştürülebilir yapılandırılmış markdown olarak çıkarmak. İşi `kitap-okuyucu` agent'ı yapar; bu skill standartları tanımlar.

## Kitap listesi ve beklenen odaklar
| Dosya adı standardı | Kitap | Ana çıkarım odağı |
|---|---|---|
| `01_graham_akilli_yatirimci.md` | Akıllı Yatırımcı — Graham | Güvenlik marjı, savunmacı/girişimci yatırımcı kriterleri, Bay Piyasa, sayısal seçim eşikleri (cari oran, kazanç istikrarı, temettü geçmişi, F/K×PD/DD çarpımı) |
| `02_buffett_finansal_tablolar.md` | W. Buffett ve Finansal Tabloların Yorumlanması — M. Buffett & Clark | Kalem kalem "dayanıklı rekabet avantajı" göstergeleri: brüt marj, SG&A/brüt kâr, Ar-Ge, faiz gideri/faaliyet kârı, net marj, sermaye harcaması/net kâr eşikleri |
| `03_damodaran_degerleme.md` | Değerleme İçin Küçük Kitap — Damodaran | İçsel değer (DCF mantığı), göreli değerleme çarpanları ve hangi çarpanın nerede kullanılacağı, şirket yaşam evresine göre değerleme, anlatı-sayı bağlantısı |
| `04_fisher_siradan_hisseler.md` | Sıradan Hisseler Sıradışı Karlar — Fisher | 15 madde kontrol listesi (tam liste), scuttlebutt yöntemi, ne zaman satılır/satılmaz, nitel→nicel çevrilebilir vekil metrikler (Ar-Ge/hasılat, marj trendi) |
| `05_lynch_borsada_tek_basina.md` | Borsada Tek Başına — Lynch | 6 hisse kategorisi ve her birinin ayrı değerlendirme kuralları, PEG, envanter/hasılat sinyali, bilanço kontrolleri, "iki dakika tahkiyesi" |
| `06_schilit_finansal_aldatmacalar.md` | Finansal Aldatmacalar — Schilit | TÜM hile kategorileri (kazanç manipülasyonu, nakit akışı oyunları, anahtar metrik oyunları) + her biri için tespit tekniği ve gereken bilanço kalemi |

## Çıktı şablonu (her kitap dosyası)
`Meta → İlkeler (İLKE-xx) → Formüller (FORMÜL-xx, QuaxisLabs veri karşılığıyla) → Eşikler (tablo) → Kontrol listeleri → Kırmızı bayraklar (BAYRAK-xx, tespit yöntemi + gereken veri) → Uygulama notları (nicel/nitel/uygulanamaz üçlü ayrımı)` — detaylı format kitap-okuyucu agent tanımında.

## Zorunlu kurallar
1. Kitap metni AYNEN kopyalanmaz — fikir/formül/eşik kendi cümlelerle, Türkçe, kural formatında damıtılır.
2. Her FORMÜL için "QuaxisLabs karşılığı" doldurulur: veri `calculator.py`/fetcher'larda var mı, yoksa hangi kaynaktan çekilebilir.
3. Kimlik kodları (İLKE-xx/FORMÜL-xx/BAYRAK-xx) kitap içinde benzersizdir ve dosya öneki ile küresel referans olur (örn. `06/BAYRAK-04`) — spec'ler ve kod docstring'leri bu kodlarla atıf yapar (izlenebilirlik zinciri: kitap → bilgi bankası → spec → kod → test).
4. İlerleme `bilgi-bankasi/_ilerleme.md`'de tutulur; oturum kesilirse kaldığı bölümden devam edilir.
5. Tüm kitaplar bitince `00_sentez.md` yazılır: yaklaşımların kesişimleri, çelişkileri (çözülmez — mercek mimarisine girdi olur), metrik → kitap çapraz referans tablosu.
