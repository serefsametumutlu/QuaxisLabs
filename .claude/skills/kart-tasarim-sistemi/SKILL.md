---
name: kart-tasarim-sistemi
description: QuaxisLabs kartları ve dashboard için görsel tasarım sistemi standartları — token'lar, tipografi, hiyerarşi, render kısıtları ve doğrulama döngüsü. Herhangi bir kart şablonu (templates/*.html), tasarım veya dashboard işinde kullan.
---

# Kart Tasarım Sistemi

Hedef estetik: Bloomberg/Koyfin yoğunluğu + kurumsal araştırma raporu ciddiyeti. "Jenerik AI dark-mode kartı" görünümünden kaçınılacak belirtiler: ham Tailwind renkleri (#22c55e/#ef4444), her panelin eşit görsel ağırlığı, tek font, kahraman metrik yokluğu, eşit aralıklı kutu ızgarası.

## Token sistemi (tek kaynak: `templates/_design_tokens.css`)
- **Renk:** 3 katmanlı arka plan (zemin/panel/vurgulu panel), 3 seviyeli mürekkep (birincil/ikincil/sönük), semantik set (pozitif/negatif/nötr/uyarı — doygunluğu kısılmış, koyu zeminde WCAG-okunur), 1 marka aksanı. Şablonlarda hardcoded renk YASAK — sadece `var(--...)`.
- **Tipografi:** Inter veya IBM Plex Sans (başlık/gövde) + JetBrains Mono veya IBM Plex Mono (sayısal veri). Sayılarda `font-variant-numeric: tabular-nums` ZORUNLU (kolonlar hizalanır). Ölçek: display(skor) → h1 → h2 → body → caption; Türkçe glifler (İıĞğŞş) render testinden geçmeli.
- **Boşluk:** 4px tabanlı ölçek; ayrım öncelikle boşluk+tipografiyle, çerçeve/gölge en aza.

## Hiyerarşi kuralı
Her kartın 3 saniyelik tek mesajı olmalı: skor+rozet kahramandır (en büyük, tek aksan); mercek profili ikincil; tablolar üçüncül. Mercek profili için kompakt yatay bar/segment gösterimi tercih edilir (4 mercek tek satırda okunur).

## Render kısıtları
- Playwright → PNG, ~2000px genişlik, statik CSS (JS/animasyon yok). Fontlar sistemde kurulu olmalı veya base64 gömülmeli; render sonrası PNG'de fallback font kontrol edilir.
- Telegram küçük ekran gerçeği: en küçük metin efektif ~%1 kart genişliğinden ince olmasın; kritik bilgi kenarlardan uzak.
- Şablon sözleşmesi: şablon hesaplamaz/formatlamaz, tüm değerler context'ten hazır string; `build_card_context()` arayüzü korunur.

## Doğrulama döngüsü (zorunlu)
1. Değişiklik → ilgili `scripts/demo_*.py` ile gerçek PNG üret → PNG'yi Read ile AÇ ve GÖR → sorunları listele → düzelt. En az 3 iterasyon.
2. En az 3 farklı veri durumuyla test: bol veri (THYAO tipi), N/A'lı eksik veri, negatif değerli/RİSKLİ rozet — tasarım üçünde de dökülmemeli.
3. `pytest tests/test_card*.py` yeşil kalmalı; karar ve önce/sonra notu `docs/spec/tasarim_notlari.md`'ye işlenir.

## Dashboard (piyasa görünümü) standartları
Tek dosya HTML (bağımsız açılır, sunucu istemez): BİST/NASDAQ sekmeleri → sektör grupları (katlanabilir) → sıralanabilir tablo (ticker, ad, mercek skorları, bileşik, rozet, temel çarpanlar) → skor renk skalası token'lardan → istemci-içi arama/filtre (vanilla JS serbest — dashboard PNG değil, tarayıcıda açılır). Veri Python tarafından JSON olarak gömülür; HTML hesaplama yapmaz, sıralama/filtre saf sunum işlemidir.
