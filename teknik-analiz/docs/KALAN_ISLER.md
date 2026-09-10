# Kalan İşler — Aşama B ve sonrası

**Durum (2026-09-10):** 27 göstergenin **16'sı** `tlab/chart`'a bağlı
(etkileşimli Plotly), **11'i** hâlâ eski sabit-PNG yolunda. Eski yol
KIRIK DEĞİL — sadece hover/PNG düğmesi/yeni tema sistemi yok.

Bu belge Sonnet'in terminalde devam edebilmesi için yazıldı. Her madde
"ne yapılacak + nasıl doğrulanacak" içerir.

---

## 0. Önce oku

Bağlama işi TEK bir desene indirgendi. Yeni bir gösterge eklemek için
**yalnızca iki şey** gerekir:

1. Bir **adaptör**: `IndicatorResult` → tipli sözleşme.
   *Hesap YAPMAZ.* Tarayıcının zaten ürettiği `lines`/`levels`/`boxes`/
   `markers`/`polygons`/`last_state`/`series` alanlarını okur.
2. `web/backend/routes/chart_json.py::_SUPPORTED`'e **tek satır**:
   `"gösterge.adı": (adaptör_fn, komposer_fn)`.

Frontend'e DOKUNULMAZ. `/api/catalog` her göstergeye `interactive`
alanını `_SUPPORTED`'ten türetiyor; eskiden `page.tsx`'te elle tutulan
ikinci bir liste vardı ve sessizce kayıyordu — kaldırıldı.

**Mevcut adaptörler örnek alınmalı:**

| dosya | kapsadığı | sözleşme |
|---|---|---|
| `tlab/indicators/patterns/boundary_adapter.py` | triangle, wedge, broadening | `BoundaryPattern` |
| `tlab/indicators/harmonics/adapter.py` | 8 harmonik okul | `XabcdPattern` |
| `tlab/indicators/patterns/neckline_adapter.py` | head_shoulders, double_top_bottom | `NecklinePattern` |
| `tlab/indicators/trend/chart_adapter.py` | ma_systems, ewmac | `SeriesOverlay` |
| `tlab/indicators/structure/chart_adapter.py` | supply_demand | `list[Zone]` |

### Bu turda tekrar tekrar yakalanan 4 tuzak — yenisini yazarken kontrol et

1. **Anahtar uyuşmazlığı.** `last_state` anahtarı ile sinyal
   `payload["pattern_id"]` AYNI OLMAYABİLİR (harmonikte
   `{okul}_{formasyon}_{aday}` vs sadece `{aday}`; head_shoulders `kind`
   kullanırken double_top_bottom `pattern` kullanıyor). Eşleşmezse
   `bars_ago` sessizce `None` kalır ve grafikte "Sinyal yaşı" hiç
   görünmez. **Her zaman bir örnek basıp anahtarları GÖZLE karşılaştır.**
2. **Birim tuzağı.** `depth` gibi payload alanları mutlak FİYAT olabilir,
   oran değil. Ayrıca sözleşmedeki `depth_pct` adı yanıltıcı — oraya
   KESİR konuyor, komposer 100 ile çarpıyor. Grafikte "%1451" görürsen
   bu.
3. **Sözleşme alan varsayımı.** Rota `getattr(pat, "bars_ago", None)`
   kullanır çünkü `list[Zone]` gibi sonuçlarda o alan yok. Yeni bir
   sözleşme tipi eklersen rotanın bu varsayımını kontrol et.
4. **Çift çizim.** Bir nokta hem `points` içinde hem ayrı alanda
   geliyorsa (ör. `actual_d`) komposer onu iki kez çizebilir.

### Doğrulama döngüsü (ATLAMA)

Bu projede hataların ÇOĞU yalnızca ekran görüntüsüne bakınca bulundu.

```bash
PYTHONPATH=. python3 scripts/shot_indicator.py "cikti_adi|gosterge.adi|fikstur"
```
(betik yoksa `docs/` içindeki örnekten türet; Chromium
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`)

Sonra **görüntüye BAK**. Sayıların makul olduğunu, etiketlerin
çakışmadığını, çizgilerin fiyatla ilişkili olduğunu gözle doğrula.

---

## 1. Kalan 11 gösterge

Zorluk sırasına göre. Her birinin fikstürü MEVCUT (biri hariç).

### Kolay — sözleşme ve komposer hazır

**1.1 `trend.weekly_channel` → `Channel` / `composers/channel.py`**
- Veri: `hs`, `flag`, `imp`, `chan`, `range`, `db`, `tri` fikstürlerinin
  HEPSİ 4 aday üretiyor.
- Kaynak: `result.lines` (134 çizgi! `channel_*` etiketlileri filtrele),
  `result.series["channel_position"]` alt panel için.
- Dikkat: 134 çizginin çoğu `channel_frozen_*` (tarihsel dondurulmuş
  kanallar). `tlab/viz/svg/scenes/weekly_channel.py` bunları BİLİNÇLİ
  çizmiyordu — "okunamaz kalabalık". Aynısını yap: yalnızca GÜNCEL kanal.

**1.2 `structure.golden_zone` → `FibRetracement` / `composers/fib_retracement.py`**
- Veri: tüm fikstürlerde 5 aday.
- Kaynak: `boxes` (`golden_zone`, `golden_zone_alt` stilleri —
  etiketlerde 0.618/0.786 fiyatları YAZILI), `levels` (`fib_*`),
  `last_state["band_low"]`/`["band_high"]`.
- Dikkat: 9 ayrı swing'in fib merdiveni geliyor. Yalnızca EN GÜNCEL
  swing çizilmeli (`tlab/viz/renderer.py::_declutter_levels` aynı kuralı
  uyguluyordu).

**1.3 `patterns.flag_pennant` → `PoleFlag` / `composers/pole_flag.py`**
- Veri: `flag`(2), `imp`(3), `range`(1), `db`(3).
- Kaynak: direk + bayrak sınırları `lines`ta, `last_state`te durum.
- Dikkat: `PoleFlag.view_start` alanı var — grafik direği TAM göstermeli
  (Faz 4b'de bu bir kez düzeltilmişti).

**1.4 `structure.swing_fib_abcd` → `XabcdPattern` / `composers/xabcd.py`**
- Veri: tüm fikstürlerde 3 aday.
- Kaynak: `levels` (123 tane! D-hedefleri + fib), `lines` (17), `markers`.
- Dikkat: bu ABCD **X'siz** (3 noktalı A,B,C→D). Ama `XabcdPattern.
  __post_init__` `points[:4] == ["X","A","B","C"]` ŞART koşuyor.
  Ya sözleşmeye X'siz varyant eklenmeli ya da ayrı bir sözleşme.
  **Karar gerekiyor — sessizce X uydurma.**

### Orta

**1.5 `structure.price_structure` → `MarketStructure` / `composers/market_structure.py`**
- Veri: tüm fikstürlerde 5 aday.
- Kaynak: `lines` (trendler, `touches`/`direction`/`broken` alanları
  DOLU), `boxes`, `levels` (POC/VAH/VAL), `series` (volume, macd).
- Dikkat: `vp_bins`/`vp_volumes`/`vp_gauss` serileri FİYAT-indeksli,
  zaman değil — ayrı bir yan panel ister, normal seri gibi çizilirse
  patlar.

**1.6 `trend.breakouts` → sözleşme KARARI gerekiyor**
- Veri: tüm fikstürlerde 3 aday, ama 233 sinyal / 126 marker / 110 level.
- ~20 farklı kırılım türü var (trendline, range, zone, HH/LL, MA,
  Donchian, Bollinger, kanal). Hepsini tek grafikte çizmek okunamaz —
  Faz 8A'da bu gösterge tam bu yüzden galeriden ÇIKARILMIŞTI.
- **Önce karar: hangi kırılım türü gösterilecek?** Muhtemelen "en güncel
  1-2 kırılım + retest" yeterli.

**1.7 `patterns.breakout_fvg`**
- **Mevcut fikstürlerin HİÇBİRİNDE aday üretmiyor.** Önce
  `tlab/chart/fixtures.py`'ye bir FVG fikstürü gerekiyor
  (konsolidasyon → kırılım → fair value gap → retest → onay).
  Fikstür olmadan doğrulanamaz, doğrulanmadan yazma.

### Rota değişikliği gerektiren

**1.8 / 1.9 `pair.relative_momentum`, `pair.vol_harvest`**
- `compute_live` pair modunda **`df=None`** döndürüyor (pair grafiği tek
  sembolün mumlarını çizmez, spread/z-skor çizer).
- Rota şu an `if df is None: raise HTTPException(422)` diyor.
- Gerekli: rotaya pair dalı + `composers/pair.py` (mevcut) +
  `symbol` "Y/X" biçiminde parse.
- Komposer HAZIR, iş rotada.

### Yavaş / ayrı düşünülmeli

**1.10 / 1.11 `momentum.alpha_rank`, `momentum.momentum_rank`**
- `needs_universe=True` — TEK sembolün grafiği için bile TÜM evren
  (648 sembol) hesaplanıyor. `tlab universe-plot` zaten bu maliyeti
  taşıyordu ve YAVAŞ.
- Web isteğinde bu kabul edilemez → **önbellek gerekiyor** (ör. günlük
  tarama sonucundan okuma).
- Komposerler hazır: `universe.py`, `quadrant_map.py`,
  `factor_heatmap.py`, `breadth.py`.

---

## 2. Doğrulanamamış / açık kalan noktalar

**2.1 Gerçek BIST verisiyle hiçbir şey doğrulanmadı.**
Bu ortamda yfinance kurum ağ politikasıyla ENGELLİ (403). TÜM doğrulama
`tlab/chart/fixtures.py`'nin deterministik sentetik serileriyle yapıldı.
Aynı kod yolu (`compute_live` → adaptör → komposer) çalıştırıldı ama
gerçek veriyle son kontrol SENDE.

**2.2 `slope_ratio_range` düzeltmesinin tarayıcı geneline etkisi ölçülmedi.**
Yükselen/alçalan üçgen artık üretiliyor (önce SIFIRDI) → toplam sinyal
sayısı ARTACAK. `tlab eod --market bist` koşup önce/sonra sayımı
karşılaştır. Beklenmedik bir patlama olursa `_FLAT_SIDED_SHAPES`
muafiyeti gözden geçirilmeli.

**2.3 Frontend `tsc --noEmit` çalıştırılmadı** (`node_modules` yok,
`npm install` ağ gerektiriyor). Değişiklik iki satır ve tip güvenli ama
DERLENDİĞİ doğrulanmadı. `npm run build` ilk işin olsun.

**2.4 Kök neden hâlâ açık: `wedge.py` orantısız sınır çiftleri ÜRETİYOR.**
Adaptör bunları eliyor (`_MIN_SPAN_BARS`), ama asıl düzeltme
`build_trendlines`'ın aday eşleştirmesinde olmalı (CMT kuralı: bir trend
çizgisi BENZER BÜYÜKLÜKTEKİ pivotları birleştirir). Tarayıcı genelini
etkiler, ayrı bir iş.

**2.5 Grafik penceresi.** Formasyon bazen grafiğin küçük bir köşesinde
kalıyor (tüm geçmiş çiziliyor). CLAUDE.md'deki "BULUNAN HATA 2" ile aynı
konu. Referans görsellerde grafik formasyona yakınlaşıyor. Genel bir
"sinyal tarihine odaklan" kuralı TÜM komposerlere eklenmeli.

**2.6 `repaint_alarm`** — `pattern_id` düzeltmesinden sonra %100'den
%0-4'e düştü ama sıfırlanmadı. Ayrı bir tur gerekebilir.

---

## 3. Senin manuel yapman gerekenler

```bash
git pull
# backend'i ELLE yeniden başlat -- bu projede WatchFiles yeni router'ı
# defalarca yüklemedi, kaybedilen saatlerin bir kısmı bu yüzden
cd teknik-analiz && uvicorn web.backend.main:app --reload --port 8000

cd web/frontend && npm run build   # 2.3'teki doğrulama
npm run dev
```

Kontrol listesi (`/chart` sayfası):
- 16 gösterge etkileşimli gelmeli (hover, zaman düğmeleri, sağ üstte PNG)
- Temas dairesi OLMAMALI, yalnızca kırılımda AL/SAT
- "sinyal yok" görürsen bu DOĞRU olabilir: sinyal 60 bardan eski.
  `?max_bars_ago=200` ile genişlet ya da `chart_json.py`'de varsayılanı
  değiştir.
- Kalan 11 gösterge eski PNG olarak gelmeli (kırık değil)

Sonra: `tlab eod --market bist` → 2.2'deki önce/sonra sayımı.
