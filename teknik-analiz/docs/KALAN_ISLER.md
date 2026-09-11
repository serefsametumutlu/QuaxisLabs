# Kalan İşler — Aşama B sonrası

**Durum (2026-09-11):** 27 göstergenin **27'si** `tlab/chart`'a bağlı.
989 test yeşil. Aşağıdakiler bağlama işi DEĞİL — sistemin doğruluğu ve
olgunluğu için kalanlar.

---

## 0. Sonnet için: çalışma kuralları

Bu turlarda hataların **çoğu yalnızca ekran görüntüsüne bakınca**
bulundu; kod okuyarak değil. Aynı döngüyü sürdür:

```bash
PYTHONPATH=. python3 scripts/grafik_cek.py THYAO patterns.triangle
```
Sonra **görüntüye BAK**. Sayılar makul mü, etiketler çakışıyor mu,
çizgiler fiyatla ilişkili mi.

### Tekrar tekrar yakalanan 5 tuzak

1. **Birim tuzağı (3 kez yakalandı).** `depth_pct`, `pole_pct`,
   `width_pct` — adları "yüzde" diyor ama komposer `* 100` yapıyor,
   yani sözleşme **kesir** istiyor. Grafikte "%421", "%1451", "%734"
   gördüysen bu. **Yeni bir `*_pct` alanı doldururken komposerin ne
   yaptığına BAK.**
2. **Anahtar uyuşmazlığı.** `last_state` anahtarı ile sinyal
   `payload["pattern_id"]` aynı olmayabilir (harmonikte
   `{okul}_{formasyon}_{aday}`, sinyalde ikisi ayrı alan). Eşleşmezse
   `bars_ago` sessizce `None` kalır.
3. **Alan adı ≠ anlam.** `weekly_channel`'ın `last_state["slope"]`i
   kanalın eğimi değil, orta çizginin son haftalık farkı.
   `swing_fib_abcd`'nin `last_label`i durum değil, swing etiketi.
   **Bir alanı kullanmadan önce nasıl hesaplandığına bak.**
4. **Sabit indeks.** `pat.points[3]` gibi konuma dayalı erişim iskelet
   değişince patlar — **etikete göre** ara.
5. **Ölçek çakışması.** Baz-100 normalize seriler ham mumlarla aynı
   panele konmaz.

---

## 1. ÖLÇÜM — en büyük açık (öncelik 1)

27 gösterge tarıyoruz ve **hiçbirinin ileriye dönük getirisi
ölçülmedi**. Grafiklerin güzelliğinden çok daha önemli.

- **1.1 `slope_ratio_range` düzeltmesinin etkisi ölçülmedi.**
  Yükselen/alçalan üçgen artık üretiliyor (önce SIFIRDI) → sinyal
  sayısı ARTACAK. `tlab eod --market bist` koşup önce/sonra sayımını
  karşılaştır. Beklenmedik patlama olursa
  `wedge.py::_FLAT_SIDED_SHAPES` muafiyeti gözden geçirilmeli.
- **1.2 İleriye dönük getiri doğrulaması (Aşama E).** Her gösterge ×
  her durum için: sinyalden sonraki N barda getiri dağılımı, koşulsuz
  dağılıma karşı. Yöntem: Lo-Mamaysky-Wang (2000) — koşullu vs
  koşulsuz dağılım karşılaştırması.
- **1.3 Çoklu test düzeltmesi.** `discovery.py`de Benjamini-Hochberg
  zaten var; aynı disiplin GÖSTERGE seçimine uygulanmalı. Deflated
  Sharpe (Bailey & López de Prado 2014) + permütasyon testi (Aronson).
- **1.4 `trend.breakouts` kalite skoru kalibre edilmedi.** Ağırlıklar
  (hacim 0.30 / yaş 0.20 / temas 0.20 / gövde 0.15 / mesafe 0.15)
  görev metninden geldi, ÖLÇÜLMEDİ. Artık grafik bu skora göre TEK
  kırılım seçiyor — yanlışsa yanlış kırılımı gösteriyoruz.
- **1.5 `repaint_alarm`** `pattern_id` düzeltmesinden sonra %100'den
  %0-4'e düştü ama sıfırlanmadı.

## 2. TESPİT EDİCİ kök nedenleri (öncelik 2)

- **2.1 `wedge.py` orantısız sınır çiftleri ÜRETİYOR.** Adaptör eliyor
  (`_MIN_SPAN_BARS=15`), ama asıl düzeltme `build_trendlines`'ın aday
  eşleştirmesinde: CMT kuralı — bir trend çizgisi BENZER BÜYÜKLÜKTEKİ
  pivotları birleştirir. Tarayıcı genelini etkiler.
- **2.2 `golden_zone`: hangi swing güncel bölgeyi tanımlar?** Gösterge
  EN YENİ diyor, adaptör EN BASKIN. İki farklı cevap = tespit tarafında
  belirsizlik. Kalıcı çözüm `structure/golden_zone.py`'de.
- **2.3 "High and tight flag" ayrı tür olarak ayrılmalı.** Bulkowski:
  standart bayrakta hedefe ulaşma ~%56, HTF'de ~%90. Birlikte
  raporlamak istatistiği bozuyor.
- **2.4 `broadening` hologramı yanıltıcı** (kod doğru, çizim değil) —
  ham pivotları birleştirdiği için kama gibi görünebiliyor.
- **2.5 `harmonic.five_zero`** kök nedeni kapatıldı ama gerçek evrende
  aday sayısı hâlâ ölçülmedi.

## 3. FİKSTÜR kırılganlığı (öncelik 3)

Bayrak fikstüründe n=100/105/110/120/130 denendi, **yalnızca 120**
çizilebilir aday verdi. Bu, tespit edicilerin gerçek veride ne sıklıkta
tetiklediğine dair bir uyarı. `tlab eod` sonrası gösterge başına aday
sayısı çıkarılmalı; sıfıra yakın olanlar ya çok dar ya bozuk.

## 4. DOĞRULANMAMIŞ olanlar

- **Gerçek BIST verisiyle HİÇBİRİ doğrulanmadı** (bu ortamda yfinance/
  stooq/İş Yatırım hepsi 403). Tümü deterministik sentetik fikstürle,
  ama rotanın AYNI kod yolundan.
- **Frontend `tsc --noEmit` / `npm run build` çalıştırılmadı**
  (node_modules yok). Değişiklikler küçük ve tip güvenli ama
  DERLENDİĞİ doğrulanmadı.
- **3 tema (dark/classic/editorial)** rota testinde render ediliyor
  ama GÖZLE yalnızca dark incelendi.

## 5. Bilinen küçük eksikler

- `zones` ve `pair` komposerlerine odak (`focus`) uygulanmadı —
  zaman aralığı tanımlı bir "formasyon" olmadığı için BİLİNÇLİ.
- `price_structure` hacim profili yan paneli çizilmiyor (`vp_*`
  serileri FİYAT-indeksli, ayrı panel ister).
- `weekly_channel` temas KONUMLARI gösterge tarafından dışa
  açılmıyor (yalnızca sayı) — çizgide temas dairesi yok.
- `alpha_rank` alfa t-istatistiği seri olarak değil, son değer olarak
  gösteriliyor (`SeriesOverlay` tek alt panel destekliyor).
