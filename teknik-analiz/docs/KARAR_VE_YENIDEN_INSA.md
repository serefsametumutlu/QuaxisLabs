# Karar ve Yeniden İnşa Planı

**Tarih:** 2026-09-08
**Soru:** Yeni repo mu açalım, yoksa mevcudu toparlayabilir miyiz?
**Karar:** **Yeni repo AÇMIYORUZ. Motoru koruyoruz, görselleştirme katmanını
tamamen siliyoruz, yerine sıfırdan yeni bir paket koyuyoruz.**

Bu belge kararı gerekçesiyle veriyor, sonra yol haritasını.
Karar bana bırakıldı; aşağıdaki ölçümler ve bulgular kararın dayanağıdır.

---

## 0. Önce en önemli bulgu: şartname tersine döndü

`web/backend/routes/chart_png.py` dosyasının kendi yorumunda şu yazıyor:

> *"Kullanıcı geri bildirimi: grafik TradingView tarzı etkileşimli bir JS
> widget'ı DEĞİL, Python'ın ürettiği SABİT bir görsel gibi gelmeli —
> mumları/çizgileri 'biz kendimiz' çizmeli."*

Bütün görselleştirme mimarisi bu cümlenin üzerine kuruldu:
Python figürü üretir → `kaleido`/`resvg` ile PNG'ye basar → tarayıcı o PNG'yi
`<img>` olarak gösterir. `web/frontend/package.json`'da **hiçbir grafik
kütüphanesi yok**; `ChartImage.tsx` sadece bir resim etiketi.

Bugünkü istek bunun tam tersi:

> *"adam mouse imleci ile nereye giderse o noktada bilgiler geliyor bu hem
> hacim kısmında öyle hem grafik kısmında öyle bizde bu şekilde yapmalıyız"*

**Sunucuda üretilen bir PNG'de imleç takibi, crosshair, zaman aralığı
düğmesi olamaz.** Mevcut görselleştirme katmanı kötü yazıldığı için değil,
**artık geçersiz olan bir şartnameye göre doğru yazıldığı için** atılacak.
Bu ayrımı vurguluyorum çünkü "her şeyi silelim" hissi haklı, ama sebebi
"kod berbat" değil; sebep, hedefin değişmiş olması.

İkinci doğrulama: `önemli/` klasöründeki referans görsellerin **hepsi
Plotly çıktısı**. Kanıtlar: `HRcUk75bgAApv6n`'deki `3A / 6A / 1Y / Tümü`
düğmeleri Plotly'nin `rangeselector`'ı; `HRdEu6qaoAEaHIT`'teki beyaz
çerçeveli, mum rozetli hover kutusu Plotly'nin `hovermode="x unified"`
kutusu; `HRhIeAdbcAAL2_B`'deki sağ kenar fibo etiketleri `xref="x domain"`
anotasyonları. Yani hayran olduğun çıktıların altındaki kütüphane, **bizim
zaten kullandığımız kütüphane**. Fark, onların onu tarayıcıda canlı
çalıştırması, bizim resme dondurup göndermemiz.

---

## 1. Ölçüm: neyi atıyoruz, neyi tutuyoruz

| Katman | Satır | Dosya | Karar |
|---|---:|---:|---|
| `tlab/core` | 843 | 6 | **KAL** |
| `tlab/data` | 799 | 11 | **KAL** |
| `tlab/features` | 2 849 | 18 | **KAL** |
| `tlab/indicators` | 8 824 | 43 | **KAL** (düzeltilecek) |
| `tlab/scanner` | 1 579 | 6 | **KAL** (bir hata düzeltilecek) |
| `tlab/testing` | 555 | 4 | **KAL** |
| `tlab/viz` | **10 475** | **34** | **SİL** |
| `web/frontend` | ~1 100 | 20 | grafik parçası yeniden |
| `web/backend` | ~1 500 | 10 | 2 rota değişir |
| `tests` | 14 552 | 115 | viz testleri hariç **KAL** |

Sıfırdan yeni repo, sağdaki "KAL" sütunundaki **15 449 satır motoru ve onu
koruyan ~12 000 satır testi** de çöpe atmak demek. O motorun içinde
yeniden üretilmesi haftalar sürecek şeyler var: tekrar-boyama (repaint)
testleri, pivot onay/kesinleşme zinciri, eşbütünleşme testleri, harmonik
geometri, Lo–Mamaysky–Wang ve Bulkowski formasyon kuralları.

Buna karşılık `tlab/viz` (10 475 satır) gerçekten atılmalı ve
**yamalanarak kurtarılmamalı**; gerekçesi bir sonraki başlık.

---

## 2. Görselleştirme neden yamayla düzelmez

### 2.1 Tek jenerik çizici, 24 strateji

`tlab/viz/renderer.py` tek başına **3 055 satır**. Her gösterge bir
`IndicatorResult` içinde jenerik primitif torbası (`Line`, `Box`,
`Marker`, `Polygon`) üretiyor; renderer hepsini aynı biçimde basıyor.

Senin "karma karışık", *"bizim sistemi ben bile anlamıyorum başkası nasıl
anlayacak"* şikâyetinin teknik karşılığı tam olarak budur. Referans
görsellerin **hiçbiri** jenerik bir çizicinin çıktısı değil:

- `HRihBa2WIAIZjP_` — sınır çizgisinin temasları `U1,U2,U3` / `L1,L2,L3`
  diye **numaralı dairelerle** işaretli.
- `HRhIeAdbcAAL2_B` — fibo merdiveni, her seviye kendi renginde, etiketi
  grafiğin **sağında**, `0.618: 185.00` biçiminde.
- `HRhMNlYbwAACrVs` — Three Drives'ta sadece **üç etiket** var, başka
  hiçbir şey yok.

Bunların ortak paydası yok; her biri o stratejiye **özel bestelenmiş**.
Jenerik bir primitif çizicisiyle bu çıktı üretilemez — üretilmeye
çalışıldığında tam da bizim aldığımız sonuç çıkar.

### 2.2 Kanıtlanmış yapısal hatalar

`docs/GORSEL_HATA_TESHISI.md`'de dosya:satır ile gösterildi ve bir kısmı
bu oturumda yeniden doğrulandı:

- **K1** `renderer.py:1488` — her `Line`, ilk ve son noktasına indirgeniyor
  (`ln.points[0], ln.points[-1]`). `ma_systems`'ın EMA serileri bu yüzden
  düz yatay çizgi oluyordu.
- **K2** alt panellerin y aralığı tüm geçmişten ölçekleniyor; MACD
  −40…+20 aralığında −5…+5 veri çiziliyor. RSI'ın etkilenmemesinin sebebi
  0–100 ile sınırlı olması — yani hatanın kendisinin kanıtı.
- **A3** `themes.py::_FILL_STYLE_COLOR` sözlüğünde `demand`/`supply`
  anahtarları **yok**; eksik ad **sessizce griye** düşüyor. `supply_demand`
  grafiğinde tek gri kutu çıkmasının, hiç yeşil talep bölgesi olmamasının
  sebebi bu.

Üçü de aynı kök kusurun belirtisi: **sözleşmesi zayıf, jenerik, sessizce
başarısız olan bir çizim katmanı.**

### 2.3 Eksik olan üçüncü şey: görsel kabul döngüsü

En önemlisi bu. Şimdiye kadar **hiç kimse çıktının resmine bakıp referansla
karşılaştırmadı.** 115 test dosyası vardı ama hepsi veri yapısı testiydi;
"bu grafik referansa benziyor mu" diye soran tek bir test yoktu. Bu yüzden
"düzeltildi" denen şeyler düzelmemiş görünebildi — kimse bakmıyordu.

Bu oturumda o döngüyü kurdum ve kullandım (bkz. § 4).

---

## 3. Karar

> **Yeni repo açmıyoruz.** Aynı repoda:
> 1. `tlab/viz/` **tamamen silinir** (10 475 satır).
> 2. Yerine `tlab/chart/` adında **yeni ve temiz** bir paket gelir.
> 3. Motor (`core/data/features/indicators/scanner`) **korunur**, içindeki
>    kanıtlanmış hatalar tek tek düzeltilir.
> 4. Frontend, PNG göstermeyi bırakır; **plotly.js** ile figürü canlı çizer.

**Neden yeni repo değil:** atılacak şey tek bir katman. Yeni repo, motoru
ve testleri de kaybettirir; kazandırdığı tek şey psikolojik temizlik olur.
O temizliği `tlab/viz` → `tlab/chart` geçişi zaten veriyor: yeni paketin
içinde eski koddan **tek satır** taşınmayacak.

**Fon sistemi ayrı bir konu:** `tlab/funds/` olarak **yeni ve bağımsız**
bir paket olarak açılır (§ 6). O gerçekten yeni bir ürün alanı.

---

## 4. Yeni mimari — ve çalışan kanıtı

Karar kâğıt üstünde kalmasın diye bu oturumda yeni paketin çekirdeğini
kurdum ve bir stratejiyi uçtan uca çalıştırdım.

```
tlab/chart/
  tokens.py       # 3 tema, KAPALI rol kümesi
  frame.py        # çok panelli iskelet, panel başına bağımsız y
  marks.py        # ortak işaretler (temas, fibo, bölge, sinyal kutusu)
  fixtures.py     # deterministik sentetik veri (yalnız test/demo)
  composers/      # STRATEJİYE ÖZEL besteleyiciler
    range_box.py
```

### 4.1 Sözleşme değişikliği: tipli sonuç → özel besteleyici

Eskiden: `gösterge → jenerik primitif torbası → tek renderer`.
Şimdi: `gösterge → TİPLİ sonuç (ör. RangeBox) → o tipe ait besteleyici`.

```python
@dataclass(frozen=True)
class RangeBox:
    support: float
    resistance: float
    upper_touches: tuple[RangeTouch, ...]
    lower_touches: tuple[RangeTouch, ...]
    ...
```

Besteleyici bu tipin alanlarını çizer. "Eksik stil adı griye düştü"
(A3) türü bir hata **artık mümkün değil**, çünkü jenerik yol yok.

### 4.2 Hatalar yapısal olarak imkânsız hâle getirildi

- **K1 olamaz:** `marks.line_series` x ve y'yi **tam dizi** olarak geçirir;
  iki uca indirgeyen bir kod yolu yok.
- **K2 olamaz:** `Panel.autorange()` y sınırını **yalnızca o panele verilen
  serilerden** hesaplar. Doğrulandı: fiyat `(8.8, 31.2)`, hacim
  `(940000, 2060000)`, RSI sabit `(0, 100)`.
- **A3 olamaz:** `tokens.role_color()` **kapalı** bir rol kümesi kullanır;
  bilinmeyen ad sessizce griye düşmek yerine `ValueError` atar.
  Doğrulandı: `role_color('light','demand')` → *"bilinmeyen rol 'demand'"*.

### 4.3 Görsel kabul döngüsü artık var

Yeni akış: `figür → HTML (plotly.js gömülü) → Playwright/Chromium ile
ekran görüntüsü → referansla karşılaştır → düzelt → tekrar`.

Bu döngüyü bu oturumda **dört tur** çalıştırdım. Her turda gerçek kusur
buldum:

| Tur | Bulunan kusur | Düzeltme |
|---|---|---|
| v1 | Sağ kenar etiketi kırpık | `margin_r` 96 → 132 |
| v1 | Bölge dolgusu fazla doygun | `fill_alpha_zone` 0.10 → 0.055 |
| v1 | RSI 30/70 kılavuzları görünmüyor | grid rengi → `text_muted` %35 |
| v2 | Temaslar çizginin üstünde değil | küme toleransı %2.5 → %1.2, seviye = küme ortalaması |
| v2 | `L5` etiketi sinyal kutusunun altında | etiket çakışma çözücü |
| v2 | RSI ilk barlarda 100'e vuruyor | ısınma barları çizilmiyor |
| v3 | Hover ham float basıyor (`62.2713`) | `yhoverformat=",.2f"` |

**Sonuç doğrulandı:** temas sapmaları direnç için ±0.58 (%0.9), destek
için ±0.07 (%0.13) — işaretler çizginin üstünde duruyor.

### 4.4 Etkileşim kanıtlandı

Playwright ile imleci fiyat panelinin üstüne götürdüm; DOM'dan okunan
hover içeriği:

```
Oct 4, 2024 | Fiyat: open: 62.27  high: 62.91  low: 61.57  close: 61.87 ▼ | U2: 62.91
```

artı iki `spikeline` (dikey + yatay crosshair). Yani senin istediğin
*"imleç nereye giderse o noktada bilgiler gelsin"* davranışı **çalışıyor**,
referans `HRdEu6qaoAEaHIT` görselindeki kutunun aynısı.

> Not: Bu oturumda Yahoo Finance kurumsal ağ politikasıyla kapalı (403),
> bu yüzden prototip **deterministik sentetik veriyle** çalıştı. Senin
> makinende gerçek BİST verisiyle aynı kod çalışır; fikstürler zaten
> projenin kendi `validate_ohlcv` denetiminden geçiyor.

---

## 5. Motordaki kanıtlanmış hatalar (bu oturumda bulundu)

Görsel iş dışında, motorda **kök nedeni bulunamamış** diye işaretlenmiş bir
bulguyu kapattım.

### 5.1 `repaint_alarm` — kök neden bulundu

`CLAUDE.md` ve `PROGRESS_LOG.md`, 1M+ "kaybolan sinyal" için
*"KÖK NEDEN BULUNAMADI, AYRI/DEDİKE bir oturum gerektiriyor"* diyordu.

**Kök neden:** `pattern_id`'ler **konumsal bar indeksinden** üretiliyor.

| Dosya | Satır | Üretim |
|---|---|---|
| `trend/breakouts.py` | 238 | `f"{break_type}_{origin_idx}_{confirmed_idx}"` |
| `harmonics/geometry.py` | 106 | `f"{zero_tag}_{x.bar_idx}_{a.bar_idx}_{b.bar_idx}_{c.bar_idx}"` |
| `structure/swing_fib_abcd.py` | 211 | `f"abcd_{a.bar_idx}_{b.bar_idx}_{c.bar_idx}"` |
| `patterns/double_top_bottom.py` | 250 | `f"{name}_{p1.bar_idx}_{neck.bar_idx}_{p2.bar_idx}"` |
| `patterns/head_shoulders.py` | 195 | `f"{kind}_{l1.bar_idx}_{head.bar_idx}_{l3.bar_idx}"` |
| `patterns/flag_pennant.py` | 186 | `f"flagpennant_{pole.t0_idx}_{pole.t1_idx}"` |
| `patterns/broadening.py` | 178 | `f"broadening_{u.p1.bar_idx}_..."` |
| `patterns/wedge.py` | 210 | `f"{mode}_{u.p1.bar_idx}_..."` |
| `patterns/breakout_fvg.py` | 270 | `f"breakoutfvg_{window_start}_{born_idx}"` |
| `structure/supply_demand.py` | 119 | `f"sd_{kind}_{zone.created_idx}_{i}"` |

`swings.py:70` — `bar_idx=i`, yüklenen çerçevenin başından sayılan konum.
`engine.py:294` — `lookback_bars: int = 600`; `_fetch_and_prepare` her
koşuda **son 600 barı** çekiyor.

Zincir: 02 Eylül → 04 Eylül arasında 2 yeni bar gelir → pencere 2 bar kayar
→ **aynı gerçek barın `bar_time`'ı değişmez ama `bar_idx`'i 2 azalır** →
`pattern_id` değişir → `diff()`'in anahtarı
`(symbol, tf, indicator, pattern_id, state, bar_time)` tutmaz →
o göstergenin **tüm** satırları "missing" sayılır → `has_repaint_alarm`
(`len(missing_signals) > 0`) yanar.

**Deneysel kanıt.** Aynı seriyi iki kez taradım; ikinci koşuda yalnızca
pencereyi 2 bar kaydırdım. Ortak zaman aralığında:

| gösterge | `pattern_id` dahil kayıp | `pattern_id` hariç kayıp |
|---|---:|---:|
| `patterns.broadening` | **126/126** | 0/7 |
| `structure.supply_demand` | **113/113** | 6/113 |
| `patterns.flag_pennant` | **33/33** | 0/33 |
| `harmonic.carney` | **18/18** | 2/18 |
| `harmonic.three_drives` | **10/10** | 0/10 |
| `structure.golden_zone` | 1/35 | 1/35 |
| `trend.weekly_channel` | 2/116 | 2/116 |
| `trend.ewmac` | 1/26 | 1/26 |

Ayrım tertemiz: `bar_idx` kullananlar %100'e yakın sahte kayıp veriyor,
kullanmayanlar vermiyor. Üretimdeki kırılımın en tepesinde
`trend.breakouts` (305 630) olması da bunu doğruluyor — o gösterge o
oturumda hiç değiştirilmemişti ama `pattern_id`'si `origin_idx` tabanlı.

**Düzeltme:** `pattern_id` **zaman damgasından** üretilmeli
(`f"{kind}_{p1.bar_time:%Y%m%d}_{p2.bar_time:%Y%m%d}"`), konumdan değil.
Zaman damgası pencere kaysa da değişmez. Bu, sinyal kimliğini kalıcı
kılar; "aynı formasyonu dün de görmüştüm" sorusunun cevabını verir.

### 5.2 `breakouts` kalite skoru 1.0'ı aşabiliyor

`trend/breakouts.py:207` `body_ratio = |c−o|/(hi−lo)`; 216–217'de
`0.15 * body_ratio` kırpılmadan toplanıyor. Diğer dört bileşen `min(...,1)`
ile kırpılmış, bu değil. Düzgün bir OHLC barında `body_ratio ≤ 1`, ama
`open` [low, high] dışına düşen bozuk bir barda aşar ve skor doğrulayıcısı
`ValueError` atarak o sembolün taramasını komple düşürür.

> Dürüstlük notu: bunu **kendi sentetik fikstürümde** tetikledim
> (`score ... 1.0671978341337092`), gerçek BİST verisinde tetiklendiğini
> **görmedim** — Yahoo erişimi kapalı olduğu için deneyemedim. Yine de
> `min(body_ratio, 1.0)` yazılmalı: bir kırpma eksikliği, tek bozuk barın
> tüm sembolü düşürmesine yol açacak kadar kırılgan.

### 5.3 `has_repaint_alarm` tanımı fazla kaba

`results.py:125` → `len(self.missing_signals) > 0`. Tek bir satırın
kayboluşu bile alarmı yakıyor. `diff()`'in anahtarında `state` de var;
bir formasyon `forming → confirmed` geçtiğinde eski `forming` satırı
zaten "missing" sayılır — bu **beklenen** bir durum, repaint değil.
Alarm, `chain_key` bazına (`symbol, tf, indicator, pattern_id`) taşınmalı
ve yalnızca **aynı `bar_time`'daki bir sinyalin değeri/yönü değiştiğinde**
yanmalı.

---

## 6. Yol haritası

Sıra bağlayıcı; her adım bir öncekinin çıktısına dayanıyor.

### Y0 — Kimlik ve alarm (motor) — *en önce*
`pattern_id` üreten 10 yeri zaman damgasına çevir. `has_repaint_alarm`'ı
`chain_key` bazına al. `body_ratio`'yu kırp. Bu yapılmadan hiçbir tarama
sonucu iki gün üst üste karşılaştırılamaz.

### Y1 — `tlab/chart` çekirdeği
`tokens/frame/marks` bu oturumda kuruldu ve çalışıyor. Eklenecek:
`legend.py` (referanslardaki yatay açıklama şeridi), `layout.py` (etiket
çakışma çözücü — `marks.boundary` içinde başladı, genelleştirilmeli),
`export.py` (aynı figürden PNG: Telegram/rapor için).

### Y2 — Besteleyiciler
Her strateji için tipli sonuç + besteleyici. Sıra, referans görsellerin
kapsadığı sırayla:

1. `range_box` — **bitti** (v3, `önemli/HRjNKRZWAAAhfSy`)
2. `channel` — yükselen/alçalan kanal (`HRiOTwUbQAA9WKw`)
3. `triangle` — simetrik/alçalan üçgen (`HRiPy4qbUAA1bKc`, `HRihBa2WIAIZjP_`)
4. `flag_pennant` — bayrak/flama (`HRaULXwaEAA60Z5`)
5. `fib_retracement` — fibo merdiveni + altın bölge (`HRhIeAdbcAAL2_B`)
6. `harmonic` — XABCD dolgulu gövde + PRZ (`HRhIeAdbcAAL2_B`)
7. `three_drives` — üç itiş (`HRhMNlYbwAACrVs`)
8. `swing_abcd` — A-B-C + teorik/gerçek D (`HRdEu6qaoAEaHIT`)
9. `supply_demand` — sade bölge + sağ kenar etiketi
10. `market_structure` — HH/LH/HL/LL üçgenleri, BOS/CHoCH (`ornek1.png`)
11. `pair_health` — çift sağlığı paneli (`HRcUk75bgAApv6n`)
12. `liquidity` — Corwin-Schultz (`HRb_x7YWYAA750T`)
13. `stats_table` — terminal tablosu (`HRt3uuwaEAAWAgK`)

Her besteleyici **görsel kabul turundan** geçmeden bitmiş sayılmaz:
ekran görüntüsü alınacak, referansla yan yana konacak.

### Y3 — Frontend
`plotly.js-finance-dist-min` (350 kB gzip; candlestick+ohlc+bar+scatter
içerir). `ChartImage.tsx` → `<Chart/>`: `GET /api/chart.json` figürü döner,
`Plotly.newPlot` çizer. PNG rotası **kalır** (rapor/Telegram için) ve aynı
figürden beslenir — tek tanım, iki çıktı.

### Y4 — `tlab/viz` silinir
Y2 ve Y3 bittikten sonra, tek commit'te. Öncesinde değil.

### Y5 — Yeni bilgi bloklarının entegrasyonu

**Pair Health** (senin verdiğin metin). Mevcut `pair.*` göstergeleri
yalnızca eşbütünleşmeye bakıyor. Eklenecek dört ölçü:
rolling korelasyon (30/60/90 pencere), beta stabilitesi, half-life
(Ornstein–Uhlenbeck), ve bunları tek bir sağlık skorunda birleştirme.
Metnindeki ayrım doğru ve mimariye şöyle oturuyor: *eşbütünleşme* çifti
seçer (`config/pairs.yaml` üretimi), *pair health* o çiftin **bugün hâlâ
işlenebilir** olup olmadığına karar verir (tarama anında). Bu, `pairs.yaml`
içindeki 606 çiftin gürültü oranı sorununa da doğrudan çare: sağlık
filtresi, BH-FDR'ye ek ikinci bir elek olur.

**Corwin–Schultz** (senin verdiğin metin). Yeni modül
`tlab/features/liquidity.py`. Formül (doğrulandı):

```
β = [ln(H_t/L_t)]² + [ln(H_{t+1}/L_{t+1})]²
γ = [ln(H⁽²⁾/L⁽²⁾)]²          H⁽²⁾=max(H_t,H_{t+1}), L⁽²⁾=min(L_t,L_{t+1})
α = (√(2β) − √β)/(3 − 2√2) − √(γ/(3 − 2√2))
S = 2(e^α − 1)/(1 + e^α)
```

Negatif iki-günlük değerler, Corwin'in kendi notundaki tavsiyeye uyarak
**sıfıra çekilir** (atılmaz). σ formülü uygulamadan önce makaleden
doğrulanacak — ezberden yazmıyorum.

Kullanımı senin tarifin gibi: yön göstergesi değil, **işlem kalitesi ve
likidite radarı**. Spread↓+Sigma↓ = rahat; Spread↑+Sigma↓ = *sakin görünen
ama incelmiş tahta* (en yanıltıcı hâl); Spread↑+Sigma↑ = en riskli.
Tarama sonucuna bir "işlem kalitesi" rozeti olarak eklenir.

**Three Drives** (senin verdiğin metin). Mevcut `harmonic.three_drives`
yalnızca üç ekstremi arıyor. Metnindeki üç şart eklenecek:
(a) A ve C düzeltmelerinin %61.8 / %78.6 civarı olması,
(b) **fiyat simetrisi** — A→Drive2 ile C→Drive3 bacaklarının yakın
büyüklükte olması (AB=CD mantığı),
(c) **zaman simetrisi** — iki bacağın süresinin yakın olması.
Ve senin vurguladığın kural: Drive 3 **kesin dönüş değil**, dönüş
ihtimalinin yoğunlaştığı bölge — sinyal "AL" değil "İZLE" olarak
doğacak, teyit gelince "AL"a dönecek.

**CMT trend çizgisi kuralı** (senin verdiğin metin). `_cluster`
fonksiyonunu zaten bu kurala göre yazdım: bir sınır çizgisi **benzer
büyüklükteki pivotları** bağlamalı. Kanal, karşı taraftaki pivottan
geçen paralelle kurulacak.

### Y6 — Fon sistemi (`tlab/funds/`) — ayrı ürün alanı
Senin verdiğin yol haritası aynen alınıyor, aşamalandırılmış hâli:

1. **Veri:** TEFAS fon fiyat/dağılım + KAP portföy bildirimleri; 15 dk
   gecikmeli hisse fiyatı.
2. **Günlük getiri tahmini:** referans görsellerdeki `V4` panosu —
   hisse portföyü katkısı + VİOP katkısı + reconciliation katsayısı,
   en çok katkı/kayıp veren hisseler.
3. **Kurumsal pozisyon takibi:** kurum bazlı long pozisyonlar.
4. **Kesişim taraması:** kurumların long olduğu hisselerde yatay
   kanal/setup taraması — **bu, teknik tarafla fon tarafını birleştiren
   asıl kavşak** ve `range_box` besteleyicisi buna hazır.
5. **Risk:** stres ve zorunlu satış (forced-sale) riski.
6. **Portföy optimizasyonu:** Markowitz, sonra Black–Litterman.
7. **Fund Command Center.**

Kritik uyarı: 2 ile 3 arasındaki fark büyük. Günlük getiri tahmini
"kapsam %100" varsayımıyla çalışır; KAP bildirimi aylık, TEFAS günlük.
Aradaki gecikme, tahminin hata payının ana kaynağıdır ve panoda
**açıkça gösterilmelidir** (referans görselde "VİOP VERİ GÜVENİ: ORTA"
etiketi tam olarak bunu yapıyor).

---

## 7. Şu an ne durumdayız

**Bitti:**
- Karar ve gerekçesi (bu belge)
- `repaint_alarm` kök nedeni — deneysel kanıtla
- `tlab/chart` çekirdeği: `tokens`, `frame`, `marks`, `fixtures`
- `range_box` tespit edicisi (tipli sonuç) + besteleyicisi
- Görsel kabul döngüsü (Playwright + Chromium) — dört tur çalıştırıldı
- Etkileşimli hover + crosshair kanıtlandı

**Kapanmadı — hiçbiri "düzeldi" sayılmıyor:**
`GORSEL_HATA_TESHISI.md`'deki K1/K2/K3, T1–T5, A1–A3 maddelerinin
hiçbirini kapalı işaretlemiyorum. Yeni mimaride bu hataların **yapısal
olarak imkânsız** olduğunu gösterdim; ama ilgili strateji için besteleyici
yazılıp ekran görüntüsü referansla karşılaştırılmadan hiçbiri kapanmaz.
