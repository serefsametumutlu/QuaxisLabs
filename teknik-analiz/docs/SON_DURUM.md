# Son Durum — Dosya Bazında

**Tarih:** 2026-09-09 (son güncelleme)
**Kapsam:** `tlab/chart` katmanının tamamı + yeni tespit ediciler + belgeler

Bu belge tek soruya cevap verir: **ne eklenecek, ne çıkarılacak, ne
silinecek.**

---

## 1. EKLENECEK — yeni dosyalar (hepsi ZIP'te)

### 1.1 Grafik altyapısı — `tlab/chart/`

| Dosya | İş |
|---|---|
| `__init__.py` | paket tanımı |
| `tokens.py` | 3 tema, **kapalı rol kümesi** (eksik ad `ValueError` atar) |
| `frame.py` | çok panelli iskelet, panel başına bağımsız y, ikincil eksen, sağ kenar etiket çakışma çözücü, birleşik hover, crosshair, 3A/6A/1Y/Tümü |
| `marks.py` | mum, hacim+MA, numaralı temas, fibo merdiveni, bölge bandı, sinyal kutusu, pivot üçgenleri, rejim gölgeleri |
| `contracts.py` | tipli komposer girdileri (`BoundaryPattern`, `XabcdPattern`, ...) |
| `fixtures.py` | deterministik sentetik veri — **yalnız test/demo** |

### 1.2 Komposerler — `tlab/chart/composers/`

| Dosya | Kapsadığı | Referans |
|---|---|---|
| `boundary_pattern.py` | üçgen, kama, genişleyen, kanal, kırılım (ortak iskelet) | `HRiOTwUbQAA9WKw`, `HRiPy4qbUAA1bKc` |
| `range_box.py` | yatay aralık | `HRjNKRZWAAAhfSy` |
| `channel.py` | paralel kanal | `HRiOTwUbQAA9WKw` |
| `fib_retracement.py` | fibo + altın bölge | `HRhIeAdbcAAL2_B` |
| `xabcd.py` | 8 harmonik okul + ABCD | `HRhIeAdbcAAL2_B`, `HRdEu6qaoAEaHIT` |
| `neckline.py` | çift dip/tepe + OBO/TOBO, **hologram + uç üçgenleri** | — |
| `pole_flag.py` | bayrak/flama | `HRaULXwaEAA60Z5` |
| `zones.py` | arz/talep | kullanıcının koyu temalı kutusu |
| `market_structure.py` | HH/LH/HL/LL + BOS/CHoCH | `ornek1.png` |
| `series_overlay.py` | MA sistemi / EWMAC | — |
| `pair.py` | çift + Pair Health | `HRcUk75bgAApv6n` |
| `liquidity.py` | Corwin–Schultz | `HRb_x7YWYAA750T` |
| `universe.py` | alpha/momentum dağılım + sıralama | — |
| `stats_table.py` | backtest istatistikleri | `HRt3uuwaEAAWAgK` |
| `quadrant_map.py` | **YENİ (PDF)** kalabalıklaşma / getiri-hacim / yabancı payı haritaları | PDF s.7, 8, 10 |
| `breadth.py` | **YENİ (PDF)** piyasa genişliği | PDF s.3 |
| `factor_heatmap.py` | **YENİ (PDF)** faktör sepetleri | PDF s.5 |

### 1.3 Yeni tespit ediciler ve özellikler

| Dosya | İş |
|---|---|
| `tlab/indicators/structure/range_box.py` | yatay aralık + numaralı temaslar |
| `tlab/indicators/structure/fib_retracement.py` | **baskın** swing seçimi (son küçük salınım değil) |
| `tlab/indicators/structure/zones_v2.py` | pivot çıpalı arz/talep, birleştirme, tazelik |
| `tlab/indicators/structure/market_structure_v2.py` | BOS/CHoCH + ayarlanabilir ATR swing süzgeci |
| `tlab/indicators/trend/channel.py` | CMT kuralına göre **paralel** kanal |
| `tlab/indicators/patterns/neckline_v2.py` | çift dip/tepe + OBO/TOBO, Bulkowski + LMW ölçütleri, **hologram** |
| `tlab/indicators/patterns/pole_flag.py` | direk + konsolidasyon + kırılım, `view_start` |
| `tlab/indicators/harmonics/adapter.py` | `Candidate` → `XabcdPattern` |
| `tlab/indicators/harmonics/three_drives_rules.py` | **fiyat + zaman + Fibonacci simetrisi**, `İZLE` durumu |
| `tlab/features/pair_health.py` | rolling korelasyon, beta stabilitesi, half-life |
| `tlab/features/liquidity.py` | Corwin–Schultz spread + sigma |

### 1.4 Belgeler — `docs/`

`KARAR_VE_YENIDEN_INSA.md`, `KOMPOSER_HARITASI.md`,
`ENTEGRASYON_DENETIMI.md`, `FON_SISTEMI_PLANI.md`,
`TERMINAL_DEVAM_PROMPTU.md`, `SON_DURUM.md` (bu dosya)

---

## 2. ÜZERİNE YAZILACAK — mevcut dosyalar

| Dosya | Değişiklik |
|---|---|
| `docs/TANI_VE_YOL_HARITASI_v2.md` | Faz 3, 3.5, 4 **GEÇERSİZ** işaretlendi (şartname tersine döndü); Faz 4d kısmen geçerli notu |
| `docs/KOMPOSER_HARITASI.md` | güncel kapsam tablosu |
| `docs/ENTEGRASYON_DENETIMI.md` | güncel bilanço |
| `docs/TERMINAL_DEVAM_PROMPTU.md` | güncel görev listesi |

Bunların dışında **hiçbir mevcut dosyaya dokunulmadı.**

---

## 3. SİLİNECEK — ama **ŞİMDİ DEĞİL**

### `tlab/viz/` — 10 475 satır, 34 dosya

**Silme koşulu:** aşağıdaki ikisi bitmeden silinmez.

1. `boundary_pattern` ve `xabcd` komposerlerine kalan göstergelerin
   adaptörleri yazılmış olmalı.
2. `web/frontend` plotly.js'e geçmiş olmalı.

Şu an `web/backend/routes/chart_png.py` ve `chart_svg.py` hâlâ
`tlab/viz`'i çağırıyor. Önce silinirse site çalışmaz.

**Silme sırası:**
```
1. web/frontend: ChartImage.tsx -> Chart.tsx (plotly.js)
2. web/backend: chart.json rotası ekle, chart_png -> tlab.chart'tan besle
3. tests/test_viz/ sil
4. tlab/viz/ sil
5. pyproject.toml: kaleido/resvg_py bağımlılıklarını kaldır
```

### Silinmeyecekler (yanlış anlaşılmasın)

- `tlab/indicators/patterns/double_top_bottom.py`, `head_shoulders.py`,
  `flag_pennant.py`, `wedge.py`, `broadening.py`, `triangle.py`,
  `breakout_fvg.py`, `structure/supply_demand.py`,
  `structure/price_structure.py`, `structure/golden_zone.py`
  → **KALIYOR.** Yeni `*_v2` dosyaları bunların yerine geçmedi; tarayıcı
  hâlâ eskileri çağırıyor. Geçiş, adaptörler yazıldıktan sonra ayrı bir
  iş olarak yapılacak.
- `tlab/features/hs_pattern.py` → kalıyor; `neckline_v2` bağımsız yazıldı.

---

## 4. Kapsam tablosu

| | Sayı |
|---|---|
| Komposer | **17** |
| Kapsanan gösterge | 27'nin **24**'ü |
| Referans görsel (`önemli/` + `ornek1.png`) | 12'nin **11**'i tam, 1'i kısmi |
| Kullanıcının verdiği metin | 5'in **4**'ü kodlandı, 1'i planlandı (fon) |
| PDF'ten çıkarılan yeni araç | **3** komposer (PDF'in 5 görselini karşılıyor) |

**Kalan tek kısmi görsel:** `HRiPy4qbUAA1bKc` / `HRihBa2WIAIZjP_`
(simetrik ve alçalan üçgen) — komposer hazır, **adaptör** eksik.

---

## 5. Testler ve ZIP doğrulaması

**878 geçiyor, 15 kalıyor.** Aynı 15 hata temiz `main`'de de kalıyor
(eksik `arch` ve `hypothesis` modülleri, bir bayat golden JSON).
Eklenen kod **gerileme yaratmadı.**

### ZIP gerçekten sınandı

Paket, "eksik dosya var mı, patlar mı" sorusuna cevap olsun diye
**temiz bir `main` kopyasına açılıp orada sınandı**:

| Denetim | Sonuç |
|---|---|
| Modül import | **33 / 33** |
| Test paketi | **878 geçti** (aynı 15 önceden var olan hata) |
| Komposer uçtan uca | **10 / 10** (tespit edici → komposer → figür) |

Yani ZIP kendi kendine yeter: eksik import, eksik dosya veya yarım
bırakılmış kod yok.

---

## 6. Bu turda düzeltilen görsel hatalar

Kullanıcının bildirdiği ve **resme bakılarak** doğrulanan hatalar:

| Bildirim | Kök neden | Düzeltme |
|---|---|---|
| *"2 üçgen ve hologram ile resmedilmiyordu"* | hologram hiç yoktu | uçlar arası GERÇEK kapanış yolu + uç üçgenleri |
| *"yarım üçgen olarak getiriyorsun"* | iskelet yalnızca 3 ucu bağlıyor, **koltukaltları atlanıyordu** | iskelet TÜM pivotlardan geçiyor |
| *"hologram omuz kısımlarında yarım geliyor"* | gövde uç pivotlardan başlatılıyordu | gövde artık fiyatın **boyun çizgisini kestiği** yerden başlar |
| *"omuzların dış kısımlarında da trend çizgisi olsa"* | iskelet uçlarda kesiliyordu | dış kanatlar eklendi |
| *"kırılım çizgisi yamuk duruyor"* | eğimli boyun sağa uzatılınca fiyattan kaçıyor, işaretler ters tarafta kalıyordu | boyun formasyon içinde kaldı; **TETİK ayrı ve YATAY** çizgi |
| *"köşeler xabcd gibi düzeltilmedi"* | düz metin etiketler, dolgusuz gövde | dolgulu poligon + **kutulu rozet** etiketler |
