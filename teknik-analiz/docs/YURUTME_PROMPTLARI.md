# Yürütme Promptları — A'dan H'ye

**Tarih:** 2026-09-10
**Kullanım:** Her aşama için altındaki bloğun TAMAMINI kopyalayıp
terminaldeki Claude/Sonnet oturumuna yapıştır. Aşamalar SIRALIDIR;
öncekini bitirmeden sonrakine geçme.

---

## 🔴 SİTEDE DOĞRU GÖRÜNTÜYE NE ZAMAN ULAŞIRSIN?

**Aşama A'nın sonunda — ilk göstergede.**

Bugünkü durum: `tlab/chart` altında 21 komposer var ama **hiçbir web
rotası onları çağırmıyor**. Site hâlâ `tlab/viz`'in ürettiği sabit PNG'yi
gösteriyor. Ölçüm: `grep -rn "tlab.chart" web/` → **0 sonuç.**

| Aşama | Sitede ne görürsün |
|---|---|
| **A** | **`patterns.triangle`** doğru görünür — hover, crosshair, zaman düğmeleri çalışır |
| **B** | Kalan 19 gösterge de doğru görünür |
| C | Yoğun temaslı grafiklerde etiketler okunur olur |
| D | Uzun periyotlarda kaybolan sinyaller geri gelir |
| F | Eski `tlab/viz` silinir, tek çizim yolu kalır |

Yani **A bittiğinde ilk doğru grafiği görürsün, B bittiğinde hepsini.**

---

## Her prompta yapıştırılacak ORTAK BLOK

> Aşağıdaki metni her aşama prompt'unun BAŞINA ekle.

```
## Değişmeyen kurallar (her aşamada geçerli)

- **Tekrar-boyama yasağı.** Bir sinyalin `bar_time`'daki değeri yalnızca
  o bar ve öncesindeki veriyi kullanır. `df.shift(-n)`,
  `rolling(center=True)` yasak; `find_peaks`/`argrelextrema` sonucunu
  doğrudan sinyal barına yazmak yasak.
- **Katman ayrımı.** `data → features → indicators → scanner → results →
  chart`. Tek yönlü. **Grafik katmanı HESAP YAPMAZ.**
- **Sihirli sayı yok.** Her eşik adlandırılmış bir parametre olsun.
- **Testleri kırma.** Şu an 914 yeşil.
- Her aşama sonunda `pytest`, `ruff`, `mypy` çalıştır ve **commit + push et.**
- Bir şey belirsizse DUR ve sor. Tahmin edip devam etme.
- Kapsam dışı bir hata görürsen düzeltme, `docs/PROGRESS_LOG.md`'ye yaz.
```

---

# AŞAMA A — Dikey dilim: tek gösterge uçtan uca

**Amaç:** `tlab/chart`'ı ilk kez ürüne bağlamak. Tek gösterge
(`patterns.triangle`) tarayıcıda etkileşimli olarak görünsün.

**Neden önce bu:** 19 adaptörü yazıp sonra frontend'e geçersen,
adaptörleri KANITLANMAMIŞ bir sözleşmeye göre yazmış olursun. Önce boru
hattını uçtan uca çalıştır, sözleşme kanıtlansın.

```
AŞAMA A — tlab/chart'ı ürüne bağla (dikey dilim)

## Bağlam

`tlab/chart` altında 21 komposer ve 14 tespit edici var, hepsi test
edilmiş. Ama HİÇBİRİ web'e bağlı değil:

    grep -rn "tlab.chart" web/     → 0 sonuç

Bütün grafik rotaları (`web/backend/routes/chart.py`, `chart_png.py`,
`chart_svg.py`, `report.py`) hâlâ `tlab.viz`'i çağırıyor. Frontend'de
plotly yok, `ChartImage.tsx` sunucudan gelen PNG'yi `<img>` olarak
gösteriyor.

Bu aşamada TEK bir göstergeyi uçtan uca bağlayacaksın. Diğerlerine
DOKUNMA — sözleşme kanıtlanınca Aşama B'de topluca yapacağız.

## Önce oku

1. `docs/KARAR_VE_YENIDEN_INSA.md` — neden bu mimariye geçtik
2. `tlab/chart/frame.py` — `ChartFrame.finish()` bir `go.Figure` döndürür
3. `tlab/chart/composers/converging.py` ve
   `tlab/indicators/patterns/boundary_adapter.py` — mevcut adaptör deseni
4. `web/backend/routes/chart_png.py` — mevcut rota deseni
5. `web/frontend/components/chart/ChartImage.tsx` — değiştireceğin bileşen

## Yapılacaklar

### A1. Backend: yeni JSON rotası

`web/backend/routes/chart_json.py` oluştur:

- `GET /api/chart.json?symbol=&tf=&indicator=&market=&theme=`
- Şimdilik YALNIZCA `patterns.triangle` desteklesin; başka gösterge
  gelirse `422` ve açık bir mesaj döndür ("bu gösterge henüz
  tlab/chart'a bağlanmadı").
- Akış: veriyi `Store` ile çek → `patterns.triangle` göstergesini
  çalıştır → `boundary_adapter` ile `BoundaryPattern`e çevir →
  `tlab.chart.composers.triangle.compose(...)` → `fig.to_plotly_json()`
  döndür.
- Tema eşlemesi `chart_png.py`'dekinin AYNISI:
  `{"dark":"dark","classic":"light","editorial":"paper"}`.
- `web/backend/main.py`'ye `app.include_router(chart_json.router,
  prefix="/api")` ekle.

**Dikkat:** `fig.to_plotly_json()` numpy dizileri içerebilir; FastAPI
bunu serileştiremez. `plotly.io.to_json(fig)` kullanıp `Response(
content=..., media_type="application/json")` döndürmek daha güvenli.
Hangi yolu seçersen seç, gerçek bir istekle DOĞRULA.

### A2. Frontend: plotly.js bileşeni

- `cd web/frontend && npm install plotly.js-finance-dist-min`
  (350 kB gzip; candlestick + ohlc + bar + scatter içerir — tam plotly
  1 MB'ın üzerinde, gereksiz.)
- `web/frontend/components/chart/ChartPlotly.tsx` oluştur:
  - `/api/chart.json`'dan figürü çeker
  - `Plotly.newPlot(el, fig.data, fig.layout, {displayModeBar:false,
    responsive:true})` ile çizer
  - Sembol/gösterge/tema değişince `Plotly.react(...)` ile GÜNCELLER
    (yeniden `newPlot` etme — zoom durumu sıfırlanır)
  - `useEffect` temizliğinde `Plotly.purge(el)` çağır
  - Yükleniyor / hata durumları `ChartImage.tsx`'teki gibi
- `web/frontend/app/chart/page.tsx`: `indicator === "patterns.triangle"`
  ise `ChartPlotly`, DEĞİLSE eski `ChartImage`. Böylece hiçbir şey
  bozulmaz.

**Dikkat:** `plotly.js-finance-dist-min` bir Node modülü değil, tarayıcı
paketi. Next.js'te SSR sırasında `window` arayacağı için
`dynamic(() => import(...), { ssr: false })` ile yükle.

### A3. Doğrula — bu adım atlanamaz

1. Backend'i başlat: `uvicorn web.backend.main:app --reload`
2. Frontend'i başlat: `cd web/frontend && npm run dev`
3. `http://localhost:3000/chart?indicator=patterns.triangle` aç
4. **Gözle kontrol et:**
   - Mumlar çiziliyor mu?
   - **İmleci grafiğin üstüne götür** — tek kutuda tarih + OHLC + o
     bardaki gösterge değerleri geliyor mu?
   - Dikey ve yatay crosshair var mı?
   - Sağ üstteki `3A / 6A / 1Y / Tümü` düğmeleri çalışıyor mu?
   - Tema değiştir (koyu/beyaz/kâğıt) — üçünde de okunur mu?
5. Playwright ile ekran görüntüsü al ve **Read aracıyla GÖRÜNTÜYE BAK.**

**Görüntüye bakmadan "bitti" deme.** Testin geçmesi yetmez.

## Kabul ölçütü

- `/api/chart.json?indicator=patterns.triangle` geçerli bir Plotly
  figürü döndürüyor
- Tarayıcıda hover + crosshair + zaman düğmeleri ÇALIŞIYOR
- Diğer göstergeler eski PNG yoluyla ESKİSİ GİBİ çalışmaya devam ediyor
- `pytest` yeşil, `ruff`/`mypy` yeni kodda temiz

## Bana ne rapor et

Ekran görüntüsü + hover kutusunun içeriği + hangi dosyaları ekledin.
```

---

# AŞAMA E — Sinyal kalitesi doğrulaması

**Amaç:** Hangi göstergeler gerçekten işe yarıyor? Bunu B'DEN ÖNCE
bilmek gerekiyor — işe yaramayan bir göstergeye adaptör yazmak boşa
emek.

```
AŞAMA E — İleri getiri doğrulaması (Faz 8)

## Bağlam

27 gösterge, 21 komposer var ama şu soru HİÇ SORULMADI: bu sinyaller
gerçekten para kazandırıyor mu? Güzel görünen ama işe yaramayan bir
sistem riski gerçek.

Bu aşama bir BACKTEST DEĞİL — portföy, komisyon, pozisyon boyutu yok.
Tek soru: "sinyal geldikten sonraki N barda fiyat ne yaptı, bu
rastgeleden farklı mı?"

## Yapılacaklar

### E1. `tlab/validation/forward.py`

Her `(gösterge, yön)` çifti için:

- Tarayıcı sonuçlarından `state="confirmed"` sinyalleri al
- Her sinyal için `bar_time`'dan sonraki N barlık getiriyi hesapla
  (N = 5, 10, 20, 60 — parametre)
- **Yön düzeltmesi:** short sinyallerde getirinin işaretini çevir, ki
  "sinyal yönünde kazanç" tek bir sayı olsun
- Dağılımı çıkar: ortalama, medyan, kazanma oranı, standart sapma

### E2. Rastgeleye karşı test

Aynı sembolde, aynı sayıda, RASTGELE seçilmiş barlardan aynı ölçümü
yap. 1000 tekrar. Gerçek sinyallerin ortalaması bu dağılımın neresinde?

Bu, "sinyal işe yarıyor" iddiasının TEK dürüst testidir. Sadece
"ortalama getiri pozitif" demek yeterli değil — yükselen bir piyasada
RASTGELE bir bar bile pozitif getirir.

### E3. Çoklu test düzeltmesi

27 göstergeyi test ediyorsun; şansa biri "anlamlı" çıkar.
**Benjamini-Hochberg FDR** uygula (`q=0.10`). Bu proje bu düzeltmeyi
`config/pairs.yaml` üretiminde zaten kullanıyor, aynı yaklaşımı kullan.

### E4. Rapor

`docs/SINYAL_KALITESI.md` — gösterge başına tablo:

| gösterge | sinyal | 20-bar ort. | kazanma % | rastgele p | FDR sonrası |
|---|---|---|---|---|---|

Ve açık bir sonuç: hangi göstergeler anlamlı, hangileri değil.

## ÖNEMLİ — bulguyu yumuşatma

Bir gösterge işe yaramıyorsa **açıkça yaz.** Bu aşamanın değeri tam
olarak kötü haberi erken vermesinde. "Umut verici" gibi ifadeler kullanma;
sayıyı ve kararı yaz.

## Kabul ölçütü

- `docs/SINYAL_KALITESI.md` 27 göstergeyi de kapsıyor
- Her satırda rastgeleye karşı p-değeri var
- FDR uygulanmış
- Sonuç bölümünde "şu göstergeler anlamlı değil" listesi var
```

---

# AŞAMA B — Kalan 19 göstergeyi bağla

```
AŞAMA B — Kalan göstergelerin adaptörleri

## Bağlam

Aşama A'da boru hattı kanıtlandı, Aşama E'de hangi göstergelerin
anlamlı olduğu ölçüldü. Şimdi kalanları bağlıyoruz.

**Şu an bağlı olan (8):** harmonic.carney, harmonic.gilmore,
momentum.alpha_rank, momentum.momentum_rank, patterns.broadening,
patterns.triangle, patterns.wedge, structure.swing_fib_abcd

**Bağlı OLMAYAN (19):** harmonic.cypher, harmonic.five_zero,
harmonic.navarro200, harmonic.nenstar, harmonic.pesavento,
harmonic.three_drives, pair.relative_momentum, pair.vol_harvest,
patterns.breakout_fvg, patterns.double_top_bottom,
patterns.flag_pennant, patterns.head_shoulders, structure.golden_zone,
structure.price_structure, structure.supply_demand, trend.breakouts,
trend.ewmac, trend.ma_systems, trend.weekly_channel

## Öncelik

Aşama E'de **anlamlı çıkan** göstergelerle başla. Anlamsız çıkanları en
sona bırak, hatta bana sor — belki hiç bağlamayız.

## Desen

Her adaptör `tlab/indicators/patterns/boundary_adapter.py` veya
`tlab/indicators/harmonics/adapter.py` desenini izler: göstergenin
`IndicatorResult`'ını ilgili TİPLİ sözleşmeye çevirir. Yeni geometri
HESAPLAMA — gösterge zaten hesaplamış, sen sadece çeviriyorsun.

Gruplar ve hedef komposerler:

| Gösterge | Komposer | Sözleşme |
|---|---|---|
| trend.weekly_channel, trend.breakouts | `boundary_pattern` | `BoundaryPattern` |
| 6 harmonik okul | `xabcd` | `XabcdPattern` |
| double_top_bottom, head_shoulders | `neckline` | `NecklinePattern` |
| flag_pennant | `pole_flag` | — |
| supply_demand, breakout_fvg | `zones` | `Zone` listesi |
| price_structure | `market_structure` | `MarketStructure` |
| ma_systems, ewmac | `series_overlay` | `SeriesOverlay` |
| golden_zone | `fib_retracement` | `FibRetracement` |
| pair.* | `pair` | `PairView` |

## Her adaptör için

1. Adaptörü yaz
2. `chart_json.py`'deki desteklenen gösterge listesine ekle
3. **Gerçek BİST verisiyle** çalıştır, Playwright ekran görüntüsü al,
   **GÖRÜNTÜYE BAK**
4. Test yaz
5. Commit + push

Toplu commit yapma — her gösterge grubu ayrı commit.

## Bitince

`chart_json.py`'deki "henüz bağlanmadı" 422'si artık hiçbir gösterge
için tetiklenmemeli. `page.tsx`'teki `indicator === "patterns.triangle"`
koşulunu kaldır, TÜM göstergeler `ChartPlotly` kullansın.
```

---

# AŞAMA C — Ortak etiket çakışma çözücüsü

```
AŞAMA C — marks.py'ye gerçek etiket çakışma çözücüsü

## Bulgu

`tlab/chart/marks.py::boundary()` içindeki mevcut çözücü (satır ~139)
YALNIZCA İKİ DURUMLU: etiketi "center" ile "right" arasında
değiştiriyor. Yoğun kümelerde (gerçek veride TUCLK'te 14 temas)
yetersiz — etiketler üst üste biniyor.

Bu, `boundary()` kullanan TÜM komposerleri etkiliyor:
`range_box`, `channel`, `converging`, `triangle`, `wedge`,
`broadening`, `boundary_pattern`.

## Yapılacak

`tlab/chart/frame.py::_emit_edge_labels()` içinde ÇALIŞAN bir çözücü
zaten var: etiketleri piksel uzayına çevirip birbirinden itiyor,
çok satırlı etiketlerin yüksekliğini hesaba katıyor. **Aynı mantığı x
eksenine uyarla** ve `marks.py`'de ortak bir yardımcıya taşı.

Gereksinimler:
- Etiket noktanın kendisini gizlememeli (işaret yerinde kalır, YALNIZCA
  metin kayar)
- Çok yoğun kümede etiketleri seyreltmek meşru bir çözüm: her N'inci
  temas etiketlensin, ama İŞARET hepsinde kalsın (hover'da hepsi
  okunabilir olur)
- Hangi eşikten sonra seyreltileceği PARAMETRE olsun

## Doğrulama

Gerçek TUCLK verisiyle (14 temaslı) ekran görüntüsü al ve GÖRÜNTÜYE BAK.
Öncesi/sonrası karşılaştır.
```

---

# AŞAMA D — Gösterge başına lookback

```
AŞAMA D — Sabit 600-bar penceresini kaldır

## Bulgu

`tlab/scanner/engine.py:294` → `lookback_bars: int = 600`, TÜM
göstergeler ve TÜM periyotlar için sabit.

`docs/PROGRESS_LOG.md`'deki 2026-09-10 girdisi bunun sonucunu
belgeliyor: `trend.breakouts`, `structure.supply_demand`,
`structure.swing_fib_abcd`'nin bazı olayları, pencere önden kırpıldığında
HİÇ ÜRETİLMİYOR.

Sebep açık: `weekly_channel` haftalık barlarda 600 bar ≈ 11 yıl ister,
`flag_pennant` 4 saatlikte 600 bar ≈ 4 ay fazlasıyla yeter. Tek bir sayı
ikisine birden uymuyor.

## Yapılacak

1. Her göstergenin `meta`'sına (veya `IndicatorSpec`'e) `min_bars`
   alanı ekle — o göstergenin anlamlı çalışması için gereken en az bar.
2. `engine.run()` `lookback_bars`'ı sabit almak yerine
   `max(min_bars_of_indicator, taban)` olarak hesaplasın.
3. Periyoda göre ölçekle: aynı takvim süresi 1S'de 4H'ye göre 4 kat bar
   demek.
4. Değişiklikten sonra `tlab eod --market bist` çalıştır ve
   `PROGRESS_LOG`'daki bulgunun kapandığını DOĞRULA.

## Dikkat

`lookback_bars`'ı büyütmek bellek ve süre maliyeti demek. Tam evren
taraması bir önceki denemede bellek yetersizliğinden ölmüştü. Önce
küçük bir sembol kümesiyle ölç, sonra tam taramaya geç.
```

---

# AŞAMA F — `tlab/viz` silinmesi

```
AŞAMA F — Eski görselleştirme katmanını sil

## Ön koşul

Aşama A ve B BİTMİŞ olmalı. `chart_json.py` tüm göstergeleri
destekliyor ve frontend hepsinde `ChartPlotly` kullanıyor olmalı.
Bu koşul sağlanmadan silme — site çalışmaz.

## Sıra (bu sırayı bozma)

1. `web/backend/routes/chart_png.py` — `tlab.viz.live` yerine
   `tlab.chart` figürünü kaleido ile PNG'ye bassın. PNG rotası KALIYOR
   (Telegram/rapor için gerekli), yalnızca kaynağı değişiyor.
2. `web/backend/routes/chart_svg.py` — sil. `tlab/chart` SVG üretmiyor,
   PNG yeterli.
3. `web/backend/routes/chart.py`, `report.py`, `catalog.py`,
   `guide.py` — `tlab.viz` importlarını temizle. `labels_tr.py` hâlâ
   gerekiyorsa `tlab/chart/labels_tr.py`'ye TAŞI (silme).
4. `tests/test_viz/` sil
5. `tlab/viz/` sil
6. `pyproject.toml` — `resvg_py` bağımlılığını kaldır. `kaleido`
   KALIYOR (PNG için).

## Her adımdan sonra

`pytest` çalıştır ve siteyi elle aç. Bir şey bozulursa DUR.
```

---

# AŞAMA G — Üç temanın gözle doğrulanması

```
AŞAMA G — 21 komposer x 3 tema görsel denetimi

## Bulgu

21 komposerin hepsi üç temada da HATASIZ ÇALIŞIYOR (çalıştırma testi
yapıldı), ama yalnızca 2'sine koyu/kâğıt temada GÖZLE bakıldı.
"Çalışıyor" ile "iyi görünüyor" aynı şey değil.

## Yapılacak

Her komposer x her tema (63 kombinasyon) için:
1. Gerçek BİST verisiyle figür üret
2. Playwright ile ekran görüntüsü al
3. **Read aracıyla GÖRÜNTÜYE BAK**
4. Bulduğun kusuru `docs/TEMA_DENETIMI.md`'ye yaz

Özellikle ara:
- Okunmayan etiket (zeminle aynı tonda kalan metin)
- Bölge dolgularının mumları örtmesi
- Sağ kenar etiketlerinin kırpılması
- Kâğıt temasında yeterli kontrast olmaması

Bulduğun her kusuru `tokens.py`'de DÜZELT — komposerlerde tek tek
değil. Renk anlamdan türetiliyor (`role_color`), düzeltme merkezî olmalı.
```

---

# AŞAMA H — Fon sistemi

```
AŞAMA H — tlab/funds/ F1 ve F2

## Bağlam

Tam plan: `docs/FON_SISTEMI_PLANI.md`. Bu aşamada YALNIZCA F1 (veri) ve
F2 (günlük getiri tahmini) yapılacak.

## F1 — Veri katmanı

`tlab/funds/data/`: TEFAS fon fiyatı + KAP portföy dağılımı + 15 dk
gecikmeli hisse fiyatı.

**En kritik tasarım kararı:** KAP dağılımı AYLIK, fiyat ANLIK. Aradaki
gecikme tahminin hata payının ANA kaynağı. Veri modelinde `as_of` ve
`position_date` AYRI alanlar olmalı — birleştirme.

## F2 — Günlük getiri tahmini

`tlab/funds/estimate.py`:

    tahmini_getiri = Σ(ağırlık_i × günlük_getiri_i) × recon_katsayısı
                     + viop_katkısı

Çıktı alanları (kullanıcının paylaştığı pano görsellerinden):
hisse portföyü katkısı, VİOP katkısı, toplam, model kapsamı %,
reconciliation katsayısı, veri güveni (yüksek/orta/düşük), en çok
katkı sağlayan ve kaybettiren N hisse.

## F2'DEN SONRA DUR

Tahmini ertesi gün açıklanan GERÇEK TEFAS fiyatıyla karşılaştır, hata
dağılımını biriktir ve bana raporla. Tahmin motoru tutmuyorsa üstüne
kurulan her şey çöker — F3'e geçmeden önce bunu bilmemiz gerekiyor.
```

---

## Sırayı özetle

```
A (dikey dilim)  →  E (doğrulama)  →  B (19 adaptör)  →  C (etiketler)
   ↓                                                        ↓
site'de İLK doğru grafik                          D (lookback)
                                                            ↓
                                            F (viz sil) → G (tema) → H (fon)
```

**A bittiğinde ilk doğru grafiği görürsün. B bittiğinde hepsini.**
