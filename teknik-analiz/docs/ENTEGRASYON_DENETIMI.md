# Entegrasyon Denetimi

**Tarih:** 2026-09-08
**Soru:** *"sana ilk görsellerle birlikte verdiğim metinleri uyguladın mı,
önemli klasöründeki görsellerin hepsini tam entegre ettik mi?"*

Dürüst cevap: **çoğu evet, hepsi değil.** Aşağıda tek tek.

---

## A. Verdiğin metinler

| # | Metin | Durum | Nerede |
|---|---|---|---|
| 1 | **Pair Health** (korelasyon ≠ eşbütünleşme, rolling korelasyon, beta stabilitesi, half-life) | ✅ **KODLANDI** | `tlab/features/pair_health.py` |
| 2 | **Corwin–Schultz** (spread + sigma, dört hâlli okuma) | ✅ **KODLANDI** | `tlab/features/liquidity.py` |
| 3 | **CMT trend çizgisi / kanal kuralı** | ✅ **KODLANDI** | `tlab/indicators/trend/channel.py` |
| 4 | **Three Drives** (Fibonacci + AB=CD + fiyat ve zaman simetrisi) | ✅ **KODLANDI** | `tlab/indicators/harmonics/three_drives_rules.py` |
| 5 | **Fon analiz yol haritası** | 📋 **PLANLANDI, kodlanmadı** | `docs/FON_SISTEMI_PLANI.md` |

### 1. Pair Health — kodlandı
Senin ayrımın birebir uygulandı: eşbütünleşme çifti SEÇER, pair health o
çiftin BUGÜN işlenebilir olup olmadığına karar verir.

Dört ölçü: rolling korelasyon (30/60/90), korelasyon bozulması
(uzun − kısa), beta stabilitesi (beta'nın kendi std'si), half-life
(Ornstein–Uhlenbeck).

Uygularken bir tuzak buldum ve önledim: **rastgele yürüyüşte bile OU
regresyonu küçük negatif bir λ üretir** (Dickey-Fuller yanlılığı) ve sahte
bir yarı ömür çıkar. Bağımsız iki rastgele yürüyüşten kurulmuş sahte bir
çift, yalnızca yarı ömre bakıldığında testi geçiyordu. Bu yüzden
**korelasyonu birincil kapı** yaptım: senin *"bu çift hâlâ birlikte
hareket ediyor mu"* sorusuna cevap hayırsa çift işlenebilir değildir,
diğer ölçüler ne derse desin.

Doğrulandı: sağlıklı sentetik çift → `saglikli` (skor 1.00),
bağımsız iki rastgele yürüyüş → `bozulmus`.

### 2. Corwin–Schultz — kodlandı
Formül (β, γ, α, S) makaleye göre yazıldı, negatif iki-günlük değerler
Corwin'in kendi notundaki tavsiyeye uyarak sıfıra çekiliyor (atılmıyor).

Senin dört hâlli okuma tablon `assess()` içinde:

| Spread | Sigma | Okuma |
|---|---|---|
| düşük | düşük | Likidite iyi, piyasa sakin |
| düşük | yüksek | Tahta likit, hareket sert |
| **yüksek** | **düşük** | **Fiyat sakin görünüyor ama tahta incelmiş — gizli likidite riski** |
| yüksek | yüksek | En riskli yapı |

Grafiğin başlığında senin cümlen yazıyor: *"Yön göstergesi değildir —
işlem kalitesi ve likidite radarıdır."*

**Bir açık nokta:** σ (sigma) formülü. Makalenin σ denklemi γ terimini de
içeren daha uzun bir biçimde verilir; ben β tabanlı yaklaşımı kullandım.
Bu **spread tahminini etkilemez** (α yalnızca β ve γ'dan gelir), ama σ'yı
ölçüt olarak kullanmadan önce makaleden birebir doğrulanmalı. Koda da bu
not düşüldü.

### 3. CMT kuralı — kodlandı
*"Düzgün trend çizgisi benzer büyüklükteki pivotları bağlar, kanal karşı
taraftaki pivottan geçen paralelle kurulur."*

`detect_channel` tam bunu yapar: dipler en küçük karelerle uydurulur, üst
bant **AYNI EĞİMLE** ötelenir. İki bağımsız çizgi uydurmak kanalı paralel
olmaktan çıkarırdı.

### 4. Three Drives — kodlandı
`tlab/indicators/harmonics/three_drives_rules.py`. Altı doğrulama:
A ve C düzeltmeleri (%61.8 / %78.6), Drive 2 ve Drive 3 uzantıları
(1.272 / 1.618), **fiyat simetrisi** (A→D2 ile C→D3 bacakları yakın
büyüklükte, AB=CD mantığı) ve **zaman simetrisi** (iki bacağın süresi
yakın).

Ve senin vurguladığın kural uygulandı: *"Drive 3 oluştu diye doğrudan
ters yönde işlem açmak doğru değildir"*. Sonuç `AL` değil **`İZLE`**
durumudur; `onaylandi`ya geçmesi için fiyatın Drive 3'ten sonra
GERÇEKTEN tepki vermesi gerekir.

Doğrulandı: simetrik sentetik formasyon → 6/6 geçti, `gecerli` +
`onaylandi`; kasten asimetrik olan → 1/6, `gecersiz`.

### 5. Fon — planlandı, kodlanmadı
`docs/FON_SISTEMI_PLANI.md`. Yedi aşama (F1 veri → F7 Command Center),
en kritik tasarım kararı işaretli: **KAP dağılımı aylık, fiyat anlık —
aradaki gecikme tahminin hata payının ana kaynağı ve panoda açıkça
gösterilmeli** (referans panodaki "VİOP VERİ GÜVENİ: ORTA" ve
"reconciliation katsayısı" tam olarak bunu yapıyor).

---

## B. `önemli/` klasöründeki 11 görsel

| Görsel | Ne gösteriyor | Durum |
|---|---|---|
| `HRaULXwaEAA60Z5` | bayrak/flama tarayıcı | ✅ `pole_flag` |
| `HRb_x7YWYAA750T` | Corwin-Schultz 3 panel | ✅ `liquidity` |
| `HRcUk75bgAApv6n` | çift + Pair Health 4 panel | ✅ `pair` (rejim gölgeleri + çift eksen dahil) |
| `HRdEu6qaoAEaHIT` | ABCD + hover kutusu | ✅ `xabcd` + birleşik hover |
| `HRhIeAdbcAAL2_B` | harmonik + fibo merdiveni | ✅ `xabcd` (iki kanat düzeltmesiyle) |
| `HRhMNlYbwAACrVs` | Three Drives | ✅ çizim + **simetri kuralları** |
| `HRiOTwUbQAA9WKw` | yükselen kanal raporu | ✅ `channel` |
| `HRiPy4qbUAA1bKc` | simetrik üçgen raporu | ⚠️ komposer hazır, **üçgen adaptörü yok** |
| `HRihBa2WIAIZjP_` | alçalan üçgen + U/L temasları | ⚠️ aynı — adaptör yok |
| `HRjNKRZWAAAhfSy` | yatay aralık + temaslar | ✅ `range_box` |
| `HRt3uuwaEAAWAgK` | terminal istatistik tablosu | ✅ `stats_table` |
| `ornek1.png` | HH/LH/HL/LL + BOS/CHoCH | ✅ `market_structure` |

**Tam entegre: 10/12. Kısmi: 2** (simetrik ve alçalan üçgen — komposer
hazır, yalnızca **adaptör** eksik). Hiç yapılmamış: **yok**.

Ayrıca kullanıcının 2026-09-09'da paylaştığı TOBO görseli de karşılandı:
dolgulu gövde, hologram, kutulu köşe etiketleri, KIRILIM + **RETEST**.

Eksiklerin ortak özelliği: hiçbiri yeni komposer gerektirmiyor. Üçgen
görselleri `boundary_pattern`'a **adaptör** yazmayı, Three Drives ise
mevcut göstergeye **doğrulama** eklemeyi bekliyor.

---

## C. Üç tema

**Test edildi: 12 komposer × 3 tema = 36 kombinasyon, hepsi hatasız
çalışıyor.** İkisine gözle de bakıldı:

- **Koyu:** arz/talep grafiği — senin paylaştığın koyu referansla aynı
  his (yeşil talep kutusu, sağda değerler).
- **Kâğıt:** fibo grafiği — sıcak krem zemin, soluk renkler, bütün
  etiketler okunur.

Bunu mümkün kılan tasarım: renk **anlamdan** türetiliyor
(`role_color(tema, rol)`), her komposerde tek tek yazılmıyor. Yeni bir
tema eklemek `tokens.py`'ye bir `Palette` eklemekten ibaret.

**Kalan risk:** `paper` ve `dark` temalarında yalnızca ikişer grafik gözle
kontrol edildi. Kalan komposerlerin bu iki temada gözle doğrulanması
terminal prompt'una madde olarak eklendi.
