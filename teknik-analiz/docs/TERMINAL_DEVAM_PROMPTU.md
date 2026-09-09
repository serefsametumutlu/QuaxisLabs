# Terminal oturumu — manuel adımlar ve devam prompt'u

**Tarih:** 2026-09-08

Bu belge iki bölüm: **(A)** senin elle yapacakların, **(B)** terminaldeki
Claude/Sonnet oturumuna yapıştıracağın prompt. A bitmeden B'yi verme.

---

## A. Senin elle yapacakların (5 dakika)

### A1. ZIP'i aç

`teknik-analiz-guncelleme-2.zip` dosyasını **`C:\Users\Samet\Desktop\Teknik Analiz`
klasörünün İÇİNE**, klasör yapısını koruyarak aç.

**Hiçbir klasörü silme.** ZIP'in içindeki yollar (`tlab/chart/...`,
`docs/...`) zaten doğru konumda; mevcut klasörlerin yanına ekleniyor.
İçindekilerin neredeyse tamamı **yeni dosya**; yalnızca
`docs/TANI_VE_YOL_HARITASI_v2.md` mevcut olanın üzerine yazıyor
(Windows "değiştirilsin mi?" diye soracak → Evet).

Açtıktan sonra şu dosyaların var olduğunu doğrula:

```
tlab\chart\frame.py
tlab\chart\composers\xabcd.py
tlab\indicators\trend\channel.py
docs\KARAR_VE_YENIDEN_INSA.md
```

### A2. Bağımlılıkları kur

Proje klasöründe bir terminal aç ve:

```
pip install plotly playwright pytest pytest-timeout hypothesis arch
python -m playwright install chromium
```

`arch` ve `hypothesis` şu an eksik olduğu için 15 test kırık —
kurunca düzelirler. `playwright` + `chromium`, **görsel kabul döngüsü**
için şart (grafiğin ekran görüntüsünü alıp referansla karşılaştırmak).

### A3. Doğrula

```
python -c "from tlab.chart.composers.xabcd import compose; print('kurulum tamam')"
python -m pytest tests -q
```

### A4. Commit et

```
git add .
git commit -m "teknik-analiz: yeni grafik katmani (tlab/chart) + 4 komposer"
git push origin main
```

---

## B. Terminal oturumuna yapıştıracağın prompt

> Aşağıdaki çizginin altındaki metnin tamamını kopyala.
> `cd "C:\Users\Samet\Desktop\Teknik Analiz"` yapıp `claude` komutuyla
> oturumu aç, sonra yapıştır.

---

Merhaba. QuaxisLabs teknik analiz projesinde çalışıyorsun. Bir önceki
oturumda mimari bir karar alındı ve yeni bir grafik katmanının çekirdeği
kuruldu. Senin işin bunu tamamlamak.

## 1. ÖNCE OKU (sırayla, tamamını)

1. `docs/KARAR_VE_YENIDEN_INSA.md` — kararın kendisi ve gerekçesi. **En
   önemli belge bu.**
2. `docs/ENTEGRASYON_DENETIMI.md` — kullanıcının verdiği metinlerin ve 11
   referans görselin hangisi uygulandı, hangisi eksik. **Neyin bitmediğini
   buradan öğren.**
3. `docs/KOMPOSER_HARITASI.md` — 27 göstergenin 10 komposere nasıl indiği.
4. `docs/GORSEL_HATA_TESHISI.md` — kullanıcının şikâyet ettiği 10 bozuk
   çıktının dosya:satır düzeyinde teşhisi.
5. `docs/FON_SISTEMI_PLANI.md` — fon tarafı (henüz kodlanmadı, sırası
   teknik taraf bittikten sonra).
6. `CLAUDE.md` — proje kuralları.

`docs/TANI_VE_YOL_HARITASI_v2.md`'yi de aç ama **Faz 3, 3.5 ve 4'ün
GEÇERSİZ** olduğunu bilerek: onlar "grafik sunucuda basılan sabit bir
görsel olmalı" şartnamesine göre yazılmıştı, şartname tersine döndü.
Belgenin başında bu uyarı var.

## 2. DURUM

Yeni grafik katmanı `tlab/chart/` altında. Çekirdek hazır ve çalışıyor:

- `tokens.py` — 3 tema, **kapalı rol kümesi** (bilinmeyen renk adı
  sessizce griye düşmez, `ValueError` atar)
- `frame.py` — çok panelli iskelet; **her panelin y aralığı yalnızca
  kendi serilerinden**; birleşik hover, crosshair, 3A/6A/1Y/Tümü
  düğmeleri; sağ kenar etiketleri için çakışma çözücü
- `marks.py` — mum, hacim+MA, numaralı temas noktaları, fibo merdiveni,
  bölge bandı, sinyal kutusu, pivot üçgenleri
- `contracts.py` — tipli komposer girdileri
- `fixtures.py` — deterministik sentetik veri (yalnız test/demo)

Biten komposerler (**12 tane, 24 göstergeyi kapsıyor**):
`range_box`, `fib_retracement`, `channel`, `xabcd`, `neckline`,
`pole_flag`, `zones`, `market_structure`, `series_overlay`, `pair`,
`liquidity`, `universe`.

Kullanıcının verdiği metinlerden kodlananlar:
`features/pair_health.py` (Pair Health), `features/liquidity.py`
(Corwin-Schultz), `indicators/trend/channel.py` (CMT kanal kuralı).

Biten tespit ediciler (hepsi TİPLİ sonuç döndürür):
`structure/range_box.py`, `structure/fib_retracement.py`,
`structure/zones_v2.py`, `structure/market_structure_v2.py`,
`trend/channel.py`, `patterns/neckline_v2.py`, `patterns/pole_flag.py`,
`harmonics/adapter.py`.

## 3. SENİN İŞİN

İşin büyük kısmı artık komposer YAZMAK değil, mevcut göstergeleri
**adaptörle bağlamak**. Sıra:

**Ö1. Adaptörler (en yüksek kazanç).** `boundary_pattern` komposeri hazır
ve altı göstergeyi karşılayabiliyor; eksik olan her göstergenin
`contracts.BoundaryPattern` döndüren adaptörü. Bağlanacaklar:
`patterns.triangle`, `patterns.wedge`, `patterns.broadening`,
`trend.weekly_channel`, `trend.breakouts`. Örnek:
`tlab/chart/composers/channel.py` — 60 satır, hepsi bu.

Aynı şekilde `xabcd` komposerine 8 harmonik okulu ve
`structure.swing_fib_abcd`'yi bağla — adaptör iskeleti
`tlab/indicators/harmonics/adapter.py`'de hazır.

**Ö2. Eksik kalan parçalar.**
- `neckline`: OBO / ters OBO (`patterns.head_shoulders`). Bulkowski
  kuralı: boyun çizgisi YUKARI eğimliyse tetik, boyun çizgisi değil
  **sağ koltukaltı tepesinin** kapanışla aşılmasıdır.
- `zones`: `patterns.breakout_fvg` (3 mumluk boşluk).
- `series_overlay`: `trend.ewmac`.

**Ö3. Three Drives simetri kuralları.**
`önemli/HRhMNlYbwAACrVs.png` çizilebiliyor ama kullanıcının verdiği üç
şart kodlanmadı. `tlab/indicators/harmonics/three_drives_rules.py`
yaz ve `harmonic.three_drives`'a bağla:
- A ve C düzeltmeleri %61.8 / %78.6 civarında mı
- **fiyat simetrisi**: A→Drive2 ile C→Drive3 bacakları yakın büyüklükte mi
- **zaman simetrisi**: iki bacağın süresi yakın mı

Ve kullanıcının kuralı: *"Drive 3 oluştu diye doğrudan ters yönde işlem
açmak doğru değildir"* — sinyal `AL` değil **`İZLE`** olarak doğsun,
fiyat gerçekten tepki verince `AL`a dönsün.

**Ö4. `stats_table` komposeri.**
`önemli/HRt3uuwaEAAWAgK.png` — terminal tarzı istatistik tablosu
(Başlangıç Sermayesi, Net K/Z, Sharpe, Sortino, Max Drawdown, CAGR...).
Satırlar değere göre renklenir (pozitif yeşil, negatif kırmızı).
`önemli/` klasöründeki TEK hiç yapılmamış görsel budur.

**Ö5. Tema doğrulaması.**
12 komposer × 3 tema kombinasyonunun hepsi hatasız ÇALIŞIYOR ama yalnızca
ikisi (koyu/arz-talep, kâğıt/fibo) GÖZLE kontrol edildi. Kalan
komposerleri `dark` ve `paper` temalarında ekran görüntüsü alıp kontrol
et.

## 4. HER KOMPOSER İÇİN DEĞİŞMEYEN YÖNTEM

Bu yöntem pazarlık konusu değil. Önceki turda tam olarak bu eksik olduğu
için çıktılar bozuktu.

**a) Tipli sonuç.** Gösterge, jenerik `Line`/`Box`/`Marker` torbası
değil, `contracts.py`'deki gibi **alanları açık bir dataclass** döndürsün.
`__post_init__` içinde geçersiz durumu `ValueError` ile reddet.

**b) Ortak parçaları YENİDEN YAZMA.** `frame.py` ve `marks.py`'de olan
her şeyi kullan. Yeni bir işaret gerekiyorsa `marks.py`'ye ekle,
komposerin içine gömme.

**c) GÖRSEL KABUL DÖNGÜSÜ — atlanamaz.** Her komposer için:

```python
fig.write_html("out.html", include_plotlyjs=True, config={"displayModeBar": False})
```

sonra Playwright ile ekran görüntüsü al, **Read aracıyla görüntüye BAK**,
`önemli/` klasöründeki referansla karşılaştır, kusur bul, düzelt, tekrar
bak. Bu döngüyü en az 3 tur çevir. Örnek betik:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width":1640,"height":940}, device_scale_factor=2)
    pg.goto(pathlib.Path("out.html").resolve().as_uri())
    pg.wait_for_selector(".plot-container"); pg.wait_for_timeout(1800)
    pg.screenshot(path="out.png"); b.close()
```

**Görüntüye bakmadan bir komposeri "bitti" sayma.** Testin geçmesi
yeterli değil — mevcut golden testleri figür JSON'unu karşılaştırıyor,
görüntüyü değil; görseller bozukken de geçiyorlardı.

**d) Sinyal yoksa hiçbir şey çizme.** Kullanıcının kuralı: *"güncel yakın
bir sinyal yoksa göstermesin hiçbir şey"*. Tespit edici `None` döndürsün.

**e) Sinyal, formasyonun TAMAMLANDIĞI yerde doğar, hedefe varışta değil.**
Kullanıcının en sert şikâyeti buydu: *"kırılımda ve onayda sinyal vermesi
gerekiyordu... fakat taa hedefe geldiği noktada al yazıyor"*.

**f) Sinyalin yaşı başlıkta yazsın** (`Sinyal yaşı: N bar`).

## 5. AYRI VE ÖNCELİKLİ BİR İŞ: `pattern_id` kimlik hatası

Bu, komposerlerden **bağımsız** ve daha acil. Kök nedeni bulundu ve
`docs/KARAR_VE_YENIDEN_INSA.md` § 5.1'de deneysel kanıtıyla yazılı.

Özet: `pattern_id`'ler **konumsal bar indeksinden** üretiliyor. Tarayıcı
her koşuda son 600 barı çekiyor (`engine.py:294`). İki yeni bar gelince
pencere kayıyor, `bar_time` değişmiyor ama `bar_idx` azalıyor,
`pattern_id` değişiyor, o göstergenin **tüm** satırları "kayboldu"
sayılıyor ve `repaint_alarm` yanıyor.

Düzeltilecek 10 yer:

| Dosya | Satır |
|---|---|
| `tlab/indicators/trend/breakouts.py` | 238 |
| `tlab/indicators/harmonics/geometry.py` | 106 |
| `tlab/indicators/structure/swing_fib_abcd.py` | 211 |
| `tlab/indicators/patterns/double_top_bottom.py` | 250 |
| `tlab/indicators/patterns/head_shoulders.py` | 195 |
| `tlab/indicators/patterns/flag_pennant.py` | 186 |
| `tlab/indicators/patterns/broadening.py` | 178 |
| `tlab/indicators/patterns/wedge.py` | 210 |
| `tlab/indicators/patterns/breakout_fvg.py` | 270 |
| `tlab/indicators/structure/supply_demand.py` | 119 |

Hepsinde `bar_idx` yerine **zaman damgası** kullan:
`f"{kind}_{p1.bar_time:%Y%m%d}_{p2.bar_time:%Y%m%d}"`.

Ayrıca:
- `tlab/scanner/results.py:125` — `has_repaint_alarm` şu an
  `len(missing_signals) > 0`. Bu fazla kaba: `diff()`'in anahtarında
  `state` de var, bir formasyon `forming → confirmed` geçtiğinde eski
  satır zaten "missing" sayılıyor. Alarmı `chain_key`
  (`symbol, tf, indicator, pattern_id`) bazına taşı ve yalnızca **aynı
  `bar_time`'daki bir sinyalin değeri/yönü değiştiğinde** yansın.
- `tlab/indicators/trend/breakouts.py:216` — `body_ratio` kırpılmamış,
  skor 1.0'ı aşabiliyor ve doğrulayıcı `ValueError` atarak o sembolün
  taramasını komple düşürüyor. `min(body_ratio, 1.0)` yap.

Düzelttikten sonra `tlab eod --market bist` çalıştır ve `repaint_alarm`'ın
söndüğünü doğrula.

## 6. KURALLAR (ihlal edilemez)

- **Tekrar-boyama yasağı.** Bir sinyalin `bar_time`'daki değeri yalnızca
  o bar ve öncesindeki veriyi kullanır. `df.shift(-n)`,
  `rolling(center=True)` yasak; `find_peaks`/`argrelextrema` sonucunu
  doğrudan sinyal barına yazmak yasak.
- **Katman ayrımı.** `data → features → indicators → scanner → results →
  chart`. Tek yönlü. **Grafik katmanı HESAP YAPMAZ.**
- **Sihirli sayı yok.** Her eşik adlandırılmış bir parametre olsun.
- Testleri kırma. Şu an 878 geçiyor, 15 kalıyor (eksik bağımlılıklardan;
  `pip install arch hypothesis` sonrası düzelmeli).
- `tlab/viz/` klasörüne **DOKUNMA**. Silinecek ama komposerler ve
  frontend geçişi bitmeden değil.

## 7. ÇALIŞMA DÜZENİ

Her komposeri bitirdiğinde **commit et ve push et**. Tek büyük commit
yapma. Commit mesajında hangi göstergeleri kapsadığını ve görsel kabul
turunda ne bulup düzelttiğini yaz.

Bir şey belirsizse dur ve sor. Tahmin edip devam etme.

Başlarken bana şunu söyle: hangi dosyaları okudun, `pytest` kaç test
geçti, ve ilk hangi komposeri yazacaksın.
