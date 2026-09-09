# Fon Sistemi Planı (`tlab/funds/`)

**Tarih:** 2026-09-08
**Durum:** ⬜ **HİÇBİRİ KODLANMADI.** Bu bir plandır, rapor değil.

Kullanıcının sorusu: *"fonlarla ilgili çalışmalar için bir şey dedin mi
kaçırdım ben?"*

**Cevap: evet, ama kısaca.** `docs/KARAR_VE_YENIDEN_INSA.md` § 6 "Y6"
başlığında yedi maddelik bir sıra verdim. Kolay kaçar, çünkü 400 satırlık
bir belgenin sonundaydı. Bu dosya onu ayrı ve genişletilmiş hâliyle
tekrar veriyor.

---

## 0. Neden ayrı bir paket

Fon analizi, teknik analizle **aynı veri modelini paylaşmaz**. Teknik
taraf `(sembol, zaman) → OHLCV` üzerine kurulu; fon tarafı
`(fon, dönem) → portföy kompozisyonu` üzerine. İkisini aynı pakete
sıkıştırmak, `tlab/viz`'in başına geleni tekrarlar.

Bu yüzden: **`tlab/funds/` yeni ve bağımsız bir paket.** Teknik taraftan
YALNIZCA fiyat verisini (`tlab.data.store`) ve grafik katmanını
(`tlab.chart`) ödünç alır.

---

## 1. Aşamalar

Kullanıcının kendi yol haritası (2026-09-08) esas alındı, uygulanabilir
sıraya konuldu.

### F1 — Veri katmanı
`tlab/funds/data/`

| Kaynak | İçerik | Sıklık | Gecikme |
|---|---|---|---|
| TEFAS | fon fiyatı, toplam değer, pay sayısı | günlük | 1 gün |
| KAP | portföy dağılım bildirimleri (hisse bazında ağırlık) | aylık/üç aylık | dönem sonu + gün |
| Fiyat | hisse ve VİOP fiyatları | gün içi | 15 dk |

**En kritik tasarım kararı burada:** KAP dağılımı **aylık**, fiyat
**anlık**. Aradaki boşluk, tahminin hata payının ANA kaynağıdır. Bu
gecikme veri modelinde açıkça taşınmalı (`as_of` ve `position_date` AYRI
alanlar), çizimde açıkça gösterilmeli.

Referans panolarda bunun karşılığı var: **"VİOP VERİ GÜVENİ: ORTA"**
etiketi ve **"reconciliation katsayısı 0.7789"** — ikisi de "bu tahmin
şu kadar güvenilir" diyor. Aynısı bizde de olacak.

### F2 — Günlük getiri tahmini
`tlab/funds/estimate.py`

```
tahmini_getiri = Σ(ağırlık_i × günlük_getiri_i) × recon_katsayısı
                 + viop_katkısı
```

Çıktı, referans panodaki alanların birebir karşılığı:
- Hisse portföyü katkısı / VİOP katkısı / toplam
- Model kapsamı (%): KAP'taki hisselerin kaçının fiyatı bulunabildi
- Reconciliation katsayısı: geçmiş tahmin ile gerçekleşen fon getirisi
  arasındaki regresyon eğimi
- Veri güveni: yüksek / orta / düşük
- En çok katkı sağlayan ve kaybettiren N hisse

**Doğrulama zorunlu:** tahmin, ertesi gün açıklanan gerçek TEFAS fiyatıyla
karşılaştırılıp hata dağılımı biriktirilmeli. Doğrulanmamış bir tahmin
motoru yayına çıkmaz.

### F3 — Kurumsal pozisyon takibi
`tlab/funds/institutions.py`

Fon bazlı dağılımları **kurum** düzeyinde toplar: bir portföy yönetim
şirketinin tüm fonlarındaki toplam hisse pozisyonu. Zaman serisi olarak
tutulur ki artış/azalış görülebilsin.

### F4 — Kesişim taraması ⭐
`tlab/funds/crossover.py`

**Teknik tarafla fon tarafını birleştiren asıl kavşak budur** ve
kullanıcının kendi yol haritasında da öyle geçiyor: *"kurumların long
pozisyonda oldukları hisselerin yatay kanal/setup taramaları"*.

İş akışı: F3'ten kurumların biriktirdiği hisseler → `tlab.chart`
komposerlerine → o hisselerde hangi formasyon var.

**Bu iş için gereken teknik altyapı ZATEN HAZIR:** `range_box`,
`channel`, `boundary_pattern` komposerleri bitti. F4, mevcut tarayıcıyı
bir sembol listesiyle çağırmaktan ibaret.

### F5 — Risk
`tlab/funds/risk.py`

- **Yoğunlaşma:** fonun en büyük N pozisyonunun payı
- **Likidite riski:** pozisyonun kaç günlük ortalama hacme denk geldiği
  (burada `features/liquidity.py`'deki Corwin-Schultz spread'i doğrudan
  kullanılır — büyük pozisyonda fiyat kayması riski)
- **Zorunlu satış (forced-sale) senaryosu:** fondan %X çıkış olursa
  hangi hisselerde kaç günlük hacim satılması gerekir
- **Stres:** tarihsel şok senaryolarında portföy kaybı

### F6 — Portföy optimizasyonu
`tlab/funds/optimize.py`

Önce **Markowitz** (ortalama-varyans), sonra **Black-Litterman**.

Sıra önemli: Black-Litterman, Markowitz'in girdi hassasiyeti sorununa
çözüm olarak doğdu; önce sorunu yaşamadan çözümü kodlamak anlamsız.
Markowitz'in kovaryans tahmini için Ledoit-Wolf büzülmesi şart —
ham örneklem kovaryansı 400+ sembolde kullanılamaz.

### F7 — Fund Command Center
`web/frontend/app/fon/`

F1-F6'nın tek ekranda toplandığı yer. Bu, kod değil **ürün** işi;
öncekiler bitmeden başlanmaz.

---

## 2. Grafik tarafı

Fon panoları için iki yeni komposer gerekecek:

| Komposer | İçerik | Referans |
|---|---|---|
| `fund_daily` | günlük getiri tahmini panosu: KPI kartları + katkı/kayıp listeleri | kullanıcının paylaştığı iki pano |
| `fund_holdings` | dağılım (hisse/sektör), zaman içinde ağırlık değişimi | — |

Bunlar mum grafiği değil; `tlab/chart/frame.py` iskeletini kullanmazlar,
ama `tokens.py`'deki AYNI tema sistemine bağlanırlar ki üç tema (beyaz /
koyu / kâğıt) fon tarafında da geçerli olsun.

---

## 3. Sıraya nerede giriyor

Teknik taraf henüz bitmedi (frontend plotly.js'e geçmedi, `tlab/viz`
silinmedi). Fon işine **teknik taraf yayına çıkmadan** başlamak, iki
yarım ürünle sonuçlanır.

Önerilen sıra:
1. Teknik: adaptörler + frontend geçişi + `tlab/viz` silinmesi
2. Fon: F1 → F2 (burada bir kez durup tahminin doğruluğunu ölç)
3. F3 → F4 (kesişim — asıl değerin çıktığı yer)
4. F5 → F6 → F7

**F2'den sonra durup ölçmek şart.** Tahmin motoru tutmuyorsa üstüne
kurulan her şey çöker.
