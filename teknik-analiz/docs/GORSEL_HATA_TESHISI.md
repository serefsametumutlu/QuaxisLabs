# Görsel Hata Teşhisi — 10 hatalı çıktının tek tek incelenmesi

**Tarih:** 2026-09-05 · Yöntem: `error/` klasöründeki 10 PNG'nin **tamamı görüntü olarak açılıp incelendi**, her bulgu koda kadar izlendi, üç kök neden dosya:satır düzeyinde doğrulandı.

> **Önemli:** Önceki oturumda "düzeldi" işaretlenen maddelerin hiçbiri bu belgede kapalı sayılmıyor. Bir eksen hatasını düzeltmek, görselin istenen seviyeye geldiği anlamına gelmiyor — kullanıcı haklı.

---

## 0 · Özet: üç kod hatası, beş tasarım çöküşü, üç algoritma hatası

| # | Bulgu | Tip | Kaç görseli açıklıyor |
|---|---|---|---|
| **K1** | `renderer.py:1488` — her `Line` yalnızca **ilk ve son noktasıyla** çiziliyor | Kod, doğrulandı | ma_systems (tamamen), weekly_channel |
| **K2** | Alt panel y-ekseni **görünür pencereden değil, tüm geçmişten** ölçekleniyor | Kod, doğrulandı | price_structure, report, breakouts (hacim + MACD) |
| **K3** | AL/SAT işareti `pattern_signals[-1]`'e konuyor — tamamlanmış formasyonda bu **hedefe ulaşma barı** | Kod, doğrulandı | flag_pennant (birebir kullanıcının şikayeti) |
| **T1** | Etiketler koyu gri, koyu zeminde okunmuyor | Tasarım | golden_zone, supply_demand, breakouts, report, price_structure |
| **T2** | Panel boyutu tutarsız (486×400 ile 3500×2600 arası) | Tasarım | harmonic (rezil), diğerleri aşırı geniş |
| **T3** | Eski/bayat formasyona otomatik yakınlaştırma | Tasarım | harmonic (Nisan), flag_pennant (2025), double_top_bottom |
| **T4** | SÜRESİ DOLMUŞ / OLUŞUYOR formasyonlar tam sinyal muamelesi görüyor | Tasarım | BAKAB (iki panel de "SÜRESİ DOLDU"), AKBNK ("OLUŞUYOR") |
| **T5** | Etiket yığılması — çakışma çözücü yok | Tasarım | breakouts (6 etiket üst üste) |
| **A1** | Arz/talep bölgeleri **yanlış yöntemle** üretiliyor | Algoritma | supply_demand (0 talep bölgesi) |
| **A2** | Golden zone **yanlış swing'i** seçiyor | Algoritma | golden_zone (bölge tepede) |
| **A3** | Hologram gerçek fiyat yolunu izlemiyor, geometrik şablon | Algoritma/tasarım | AKBNK/BAKAB ("sahte, yapmacık" hissi) |

---

## 1 · Doğrulanmış kod hataları

### K1 — Her `Line` iki noktaya indirgeniyor

`tlab/viz/renderer.py:1488`:

```python
(t0, p0), (t1, p1) = ln.points[0], ln.points[-1]
...
go.Scatter(x=[_x(t0), _x(t1)], y=[p0, p1], mode="lines", ...)
```

Renderer, **her** `Line` primitifinin yalnızca ilk ve son noktasını alıp aralarına düz bir doğru çiziyor. Trendline (2 nokta) için doğru. Ama:

- `trend.ma_systems` her hareketli ortalamanın **tüm serisini** tek bir `Line` içinde taşıyor → EMA-8/21/55/200 birer **düz yatay çizgiye** çöküyor.
- `trend.weekly_channel`'ın `channel_current` çizgisi de aynı desende → o da düz.

**Kanıt:** `INTEM_trend.ma_systems_1d.png` — turuncu/mor/mavi çizgiler 235-325 aralığında dalgalanan fiyatın üstünde kusursuz düz. Gerçek bir EMA şeridi asla böyle görünmez. Kullanıcının *"ne olduğuna dair hiçbir şey anlamıyorum"* şikayeti tam olarak bu.

**Düzeltme:** `x=[_x(t) for t, _ in ln.points], y=[p for _, p in ln.points]`. Tek satır. Ama SVG motorunda da aynı kontrol yapılmalı — port sırasında bu hata taşınmış olabilir.

### K2 — Alt panel ekseni tüm geçmişten ölçekleniyor

`render()` docstring'i şöyle diyor: *"`last_n` yalnızca GÖRÜNÜR x-ekseni aralığını kısıtlar — hiçbir seri/primitif budanmaz."* Plotly'nin y-ekseni otomatik ölçeklemesi ise **trace'in tamamına** bakar, görünür x-penceresine değil.

Sonuç: INTEM'in tüm geçmişinde 600-700k'lık bir hacim çıtası varsa, görünür 250 barlık pencerede hacim 0-50k arasında olsa bile **eksen 0-700k'ya açılıyor** ve barlar panelin %7'sine sıkışıyor.

**Kanıt:**
- `INTEM_trend.breakouts_4h.png` — hacim ekseni 0–700k, barların hepsi tabanda düz bir şerit. Panel yüksekliğin **yarısını** kaplıyor ve hiçbir bilgi taşımıyor.
- `INTEM_structure.report_4h.png` / `price_structure_4h.png` — hacim 0–600k, MACD −40…+20 iken veri −5…+5.
- **RSI panelleri sorunsuz** — çünkü RSI doğası gereği 0-100 sınırlı. Bu, teşhisi kesinleştiriyor.

**Düzeltme:** `last_n` uygulandığında her alt panelin y-eksenini **görünür dilimden** hesaplayıp `fig.update_yaxes(range=..., row=i)` ile sabitle. SVG motorunda da aynı kural — orada eksen zaten elle hesaplanıyor, görünür pencereye göre hesaplandığından emin ol.

### K3 — AL işareti hedefe konuyor

`patterns/*.py` içindeki ortak desen:

```python
last_sig = pattern_signals[-1]
...
if last_sig.state in ("confirmed", "completed"):
    markers.append(Marker(t=last_sig.bar_time, ..., text="AL"))
```

`pattern_signals[-1]`, zincirin **en son olayı**. Tamamlanmış bir formasyonda bu "hedefe ulaşıldı" olayıdır. Yani **AL işareti girişe değil, çıkışa konuyor.**

**Kanıt:** `INTEM_patterns.flag_pennant_1d.png` — kırılım 4 Ağustos'ta (büyük yeşil mum, 202→207), ama `AL` etiketi 18 Ağustos'ta 218 seviyesinde, `BAYRAK [HEDEFE ULAŞTI]` rozetinin hemen altında. Kullanıcı birebir bunu yazmış: *"taa hedefe geldiği noktada al yazıyor."*

**Düzeltme:** AL/SAT işareti `event` alanı `*_confirmed` olan sinyalin barına konmalı. Ayrıca kullanıcının istediği üç ayrı işaret üretilmeli:

| Olay | İşaret | Nereye |
|---|---|---|
| Kırılım | `KIRILIM` (içi boş daire + önder çizgi) | kırılım barı |
| Onay (retest tuttu) | `ONAY` (içi dolu daire) | onay barı |
| Giriş | `AL` / `SAT` (dolgulu üçgen + kalın metin) | **onay barı** |
| Hedef | `HEDEF ✓` (rozet) | hedefe ulaşma barı |

Bu dört ayrım `docs/design/grafik_stil_vitrini.html`'in `sceneClassicPatterns` ve `sceneBreakoutFvg` sahnelerinde zaten var — kod onları üretmiyor.

---

## 2 · Tasarım çöküşleri

### T1 — Etiketler okunmuyor

`golden_zone`'daki `Altın Bölge`, `Alt Bölge`, `REAKSİYON`, `BAŞARILI`, `BAŞARISIZ`; `supply_demand`'daki `Arz (Kırık)`, `KIRILDI`, `REAKSİYON`; `report`'taki `Direnç Bölgesi`, `POC`, `VAL`, `Direnç (Temas:14)` — hepsi koyu gri (`theme.muted` ≈ `#6d7480`) koyu zemin (`#0d1015`) üstünde. Kontrast oranı ~2.4:1; WCAG AA için 4.5:1 gerekiyor.

`ornek1.png`'de tek bir soluk etiket yok: her etiket ya parlak renkli metin ya da dolgulu bir kutu içinde.

### T2 — Panel boyutu tutarsız

| Çıktı | Boyut | Sonuç |
|---|---|---|
| `harmonic.carney` | **486×400** | Mumlar okunmuyor, yazılar bulanık |
| `golden_zone`, `supply_demand`, `breakouts` | 3500×1200–1560 | Aşırı geniş (2.9:1), mumlar iğne gibi |
| `report` | 3500×2600 | Alt paneller boş alanla dolu |

`harmonic` sahnesi artifact'in **twoUp** (yan yana iki panel) ölçüsünü tek panel için kullanıyor. Tek bir standart gerekiyor: **1600×900 (16:9) tek panel**, alt panel başına +180px.

### T3 — Eski formasyona otomatik yakınlaştırma

`harmonic.carney` çıktısı Nisan–Mayıs aralığını gösteriyor; bugün Eylül. `flag_pennant` Temmuz–Ağustos **2025**. Kullanıcı: *"güncel yakın bir sinyal yoksa göstermesin hiçbir şey."*

Bu, TANI belgesindeki **Faz 0 tazelik filtresinin** grafik tarafındaki karşılığı — orada tarama tablosu için planlanmıştı, grafik için de gerekiyor: son N barda oluşmamış formasyon çizilmesin, panel "Son N mumda bu göstergeden sinyal yok" mesajı göstersin.

### T4 — Ölü formasyonlar canlı sinyal gibi çiziliyor

`BAKAB` görselinin **iki paneli de** `SÜRESİ DOLDU` rozeti taşıyor; `AKBNK` `OLUŞUYOR` diyor (boyun kırılmamış). Üçü de tam hologram + hedef çizgisi + giriş işareti ile, canlı bir sinyalden ayırt edilemeyecek şekilde çiziliyor.

`AKBNK`'ta bu ayrıca **eksen felaketine** yol açıyor: onaylanmamış bir formasyonun hedefi (37.9) mum aralığının (60–85) çok altında olduğu için eksen 40–85'e açılıyor ve mumlar panelin üst %40'ına sıkışıyor. **Hedef çizgisi, formasyon onaylanana kadar çizilmemeli.**

### T5 — Etiket yığılması

`INTEM_trend.breakouts_4h.png`'de sağ alt köşede altı etiket üst üste: `ma_break_ema50_down`, `downtrend_break adayı`, `İlk break`, `donchian_break_down_20`, `donchian_break_down_55`, `Kırılım (Aşağı)`. Tek bir kelime okunmuyor. Ayrıca `Kırılım (Aşağı)` üç kez, `Kırılım (Yukarı)` iki kez tekrar ediyor.

TANI belgesindeki **Faz 3'ün `layout.py` çakışma çözücüsü** tam olarak bunun için planlanmıştı — ama `trend.breakouts` henüz SVG'ye portlanmadı, hâlâ Plotly'nin çözücüsüz annotation motorunda.

---

## 3 · Algoritma hataları

### A1 — Arz/talep bölgeleri yanlış yöntemle üretiliyor

**Şu anki yöntem** (`features/zones_sd.py`): *rally-base-drop* — dar bir konsolidasyon (`base_max=5` bar, `base_atr=0.6`) + ardından gelen patlama (`impulse_atr=2.0`). Bu **geçerli** bir yöntem ama:

- `INTEM` çıktısında **tek bir arz bölgesi** (251–253, 2 puanlık bant) ve **sıfır talep bölgesi** üretti.
- Bölge grinin tonlarında çizildi — `_FILL_STYLE_COLOR` sözlüğünde `demand`/`supply`/`demand_broken`/`supply_broken` **anahtarları yok**, gri varsayılana düşüyor. Kullanıcı açıkça kırmızı/yeşil istedi.

**Kullanıcının tarif ettiği yöntem** (*"her hissenin dip ve tepelerine göre"*) ve `ornek1/ornek2`'nin kullandığı yöntem **pivot-çıpalı**:

1. **Çıpa**: swing yüksek → arz bölgesi; swing düşük → talep bölgesi.
2. **Sınırlar**: dış kenar swing'in ekstremi; iç kenar çevredeki mumların ortalama fitil/gövde boyundan türetilir — böylece bölge gerçek tepki alanını kapsar, ince bir çizgi değil.
3. **Kümeleme**: birbirine yakın pivotlar tek bir bölgede birleşir.
4. **Güç = temas sayısı.** Fiyatın tekrar ziyaret ettiği bölge güçlenir. `ornek1`'deki `TEST EDİLDİ` ve `TEMAS: 5` bu.
5. **ATR doğrulaması**: pivottan uzaklaşan hareket ATR katını aşmalı — aksi halde bölge gerçek değil.
6. **Yükseklik tavanı**: ~2.5–3.0 ATR.
7. **Tazelik durumu**: `TAZE` (hiç test edilmemiş) / `TEST EDİLDİ` / `KIRILDI`.

**Öneri:** iki yöntem de kalsın, **pivot-çıpalı olan birincil** olsun; rally-base-drop ikincil bir doğrulayıcı olarak kullanılsın (ikisi de aynı bölgeyi işaret ediyorsa güç skoru artsın).

Kaynaklar: [swing-çıpalı bölge tespiti + temas skorlaması](https://www.tradingview.com/script/ZUAYemgd-Supply-and-Demand-Zones-Flux-Charts/) · [rally-base-drop tanımı](https://www.luxalgo.com/library/indicator/rally-base-drop-signals/) · [order block anatomisi](https://liquidityfinder.com/news/anatomy-of-a-valid-order-block-in-smart-money-concepts-67221)

### A2 — Golden zone yanlış swing'i seçiyor

`INTEM_structure.golden_zone_4h.png`'de bölge 261.75–267 arasında, yani fiyat aralığının (235–270) **tepesinde**. Kullanıcı: *"golden zone mumların tepki alıp yükseliş yapabildiği bir noktayken en tepede resmedilmesi tamamen bir rezillik."*

**Matematik aslında doğru**: seçilen swing son düşüş bacağı (270 → 253); onun %61.8–%78.6 geri çekilmesi gerçekten 263.5–266.4 civarına düşüyor. **Seçim yanlış**: motor `min_swing_atr=3.0` filtresinden geçen **en güncel** swing'i alıyor, ve 17 puanlık bu küçük bacak filtreyi geçiyor. Görsel olarak baskın yapı ise 235 → 270 yükselişi.

**Düzeltme üç parçalı:**
1. Swing seçimi "en güncel" değil **"en anlamlı"** olsun — bacak büyüklüğü (ATR katı) × süre × yapısal önem (HH/LL kırılımı içeriyor mu) ile skorlanıp en yüksek skorlu seçilsin. `min_swing_atr` 3.0'dan belirgin yükseltilmeli (ölçülerek).
2. **Fibonacci merdiveni çizilsin** — kullanıcı açıkça istedi: *"fibo da çizilmeli ve fiyatlar fibo değerleri yazılmalı."* 0.236/0.382/0.5/0.618/0.786 seviyeleri, her biri `0.618 · 263.76` biçiminde **hem oran hem fiyat** etiketiyle. Bu format `structure.report`'ta **zaten doğru uygulanmış** (`0.786 - 266.61`) — golden_zone'a taşınacak.
3. Altın bölge (0.618–0.786) merdiven üstünde **vurgulu bant** olarak işaretlensin; `Alt Bölge` (0.5–0.618) ikincil tonla. Şu anki `0.5 - 261.75` etiketi hangi bandın hangisi olduğunu söylemiyor.

### A3 — Hologram gerçek fiyatı izlemiyor

`AKBNK`/`BAKAB`'daki mavi dolgu, tepe–boyun–tepe noktalarını birleştiren **geometrik bir çokgen**. Mumların üstüne yapıştırılmış bir şablon gibi duruyor — kullanıcının *"sahte ve canlı olmayan yapmacık görseller"* ifadesi tam olarak bu izlenimi tarif ediyor.

`ornek1/ornek2`'de hologram diye bir şey **yok**. Yapı şöyle işaretleniyor:
- Pivot noktalarına **küçük renkli üçgen + kısa metin** (`HH`, `HL`, `LH`, `LL`) — dolgu yok, birleştirici çizgi yok.
- Kırılan seviyeden **kesikli yatay çizgi** (`BOS↑`, `CHoCH↓`).
- Kullanıcı bunu birebir söylemiş: *"bizim gibi oradan oraya çizgi götürmüyor, tepelerine ve diplerine küçük üçgenle ve yazıyla resmetmiş, çok sade ve güzel."*

**Öneri:** dolgulu hologramı formasyon sahnelerinde **çok daha düşük opaklığa** indir (0.06–0.08) ve asıl anlatımı pivot işaretleri + boyun çizgisi + kırılım/onay/giriş işaretleri taşısın.

---

## 4 · `ornek1.png` standardı — görsel sözleşme

Kullanıcı bunu birebir istedi. Somut maddeler:

| Öğe | Nasıl |
|---|---|
| **Yapı etiketleri** | `HH`/`LH` altın üçgen (aşağı bakan, pivotun üstünde) · `HL`/`LL` camgöbeği üçgen (yukarı bakan, pivotun altında) + 9-10px metin. **Birleştirici zigzag çizgisi YOK.** |
| **Trend çizgisi** | Noktalı (dotted), kalın (2px), doygun renk (düşen: mor/magenta, yükselen: yeşil). Etiket: `DÜŞEN TREND \| TARİHSEL/KIRILMIŞ \| TEMAS: 5` — **yön + durum + temas sayısı**. |
| **Arz bölgesi** | Kırmızı dolgu (opaklık ~0.12) + kırmızı kenarlık + içinde kesikli orta çizgi. Etiket **sağ kenar boşluğunda, çizim alanının DIŞINDA**: `SUPPLY / ARZ` üstte, `41.80 - 42.70` altta. |
| **Talep bölgesi** | Aynısı yeşil. Durum etiketi: `DEMAND / TEST EDİLDİ` veya `DEMAND / TAZE` veya `DEMAND / TOPLAMA`. |
| **BOS / CHoCH** | Kırılan pivottan **kesikli yatay çizgi** + küçük etiket (`BOS↑` yeşil, `CHoCH↓` kırmızı). Aktif olan `/ AKTİF` eki alır. |
| **Hareketli ortalama** | **Tek** bir mor/lavanta çizgi, 2px, fiyatı takip eden. Dört MA'lık şerit değil. |
| **Etiket yerleşimi** | Fiyat bölgesi etiketleri sağ kenar boşluğunda; grafik içi etiketler çakışmıyor. |
| **Kontrast** | Hiçbir etiket soluk değil. Her metin ya parlak renkli ya dolgulu kutuda. |

**Kritik mimari not:** Bu listedeki `BOS`, `CHoCH`, temas-sayılı trend çizgisi ve pivot üçgenleri **tlab'da hiç yok**. `swings.py::label_structure` HH/HL/LH/LL üretiyor ama BOS/CHoCH üretmiyor; `trendlines.build_trendlines` temas sayısını hesaplıyor ama `Line.label` içine gömüyor, ayrı bir alan olarak taşımıyor. Yani bu, "renderer'ı düzelt" işi değil — **indikatör katmanına yeni primitif üretimi eklemek** gerekiyor.

---

## 5 · Sıradaki iş — TANI planına eklenecekler

Mevcut plandaki fazlar geçerli ama **üç yeni iş** eklenmeli ve **sıra değişmeli**:

**YENİ Faz 3.5 — Renderer kritik hataları (Faz 4'ten ÖNCE, 1 oturum).**
K1 + K2 + K3. Üçü de küçük, üçü de birden fazla görseli düzeltiyor, ve Faz 4'te SVG'ye portlanan her sahne bu hataları miras alacağı için önce kapatılmalı.

**YENİ Faz 4d — SMC yapı katmanı (Faz 4c'den sonra, 2 oturum).**
`ornek1.png` standardının indikatör tarafı: pivot üçgenleri, BOS/CHoCH tespiti, temas-sayılı trend çizgisi, pivot-çıpalı arz/talep. Bu **yeni indikatör mantığı**, sahne portu değil.

**Faz 5'e eklenecek**: A2 (golden zone swing seçimi + fib merdiveni) ve A1 (arz/talep yöntemi).

**Faz 0'ın tazelik filtresi grafiğe de uygulanacak** (T3) — tarama tablosu için planlanmıştı, grafik penceresi için de gerekiyor.

**Panel boyutu standardı** (T2) Faz 3'ün `scale.py`'sine bir sabit olarak girmeli: tek panel 1600×900, alt panel başına +180.
