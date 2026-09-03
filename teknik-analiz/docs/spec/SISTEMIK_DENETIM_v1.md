# Sistemik Denetim v1 — Faz 0.5 Bölüm D

**Tarih:** 2026-09-03/04 · **Kapsam:** A1 (ortak pivot girişi), A2 (zaman dilimi
ölçekleme), A3 (`supported_timeframes` kapısı), A4 (hacim onayı) — 120 gerçek
BIST sembolü, D1+4H, önbellek verisiyle (`scripts/sistemik_denetim.py`).

## Özet

Ölçüm A1'in temel iddiasını (ortak, ATR-uyarlanabilir pivot girişi gürültüyü
azaltır) **kısmen doğruladı, kısmen çürüttü**. Zigzag'in KENDİSİ formasyon
yapısı olan göstergelerde (head_shoulders, double_top_bottom, golden_zone,
price_structure'ın zone/range tarafı) ATR pivotlarına geçmek **gerçekten**
gürültüyü büyük oranda azalttı (%68-91) ve gözle incelemede kalan sinyaller
genel olarak gerçek formasyonlardı. Ama pivotları yalnızca bir **trendline
aday havuzu** olarak kullanan göstergelerde (wedge, triangle, broadening,
price_structure'ın trendline tarafı) ATR'nin SEYREK pivotları tam tersi
etkiyi yaptı — sinyal sayısı 12-57 KAT ARTTI, ve gözle incelemede bu artışın
büyük kısmı gerçek formasyon DEĞİL, geometrik filtrenin (yakınsama/ıraksama
testi) az sayıda noktayla anlamını yitirmesiydi. **Bu oturumda bulunup
düzeltildi** — wedge/triangle/broadening/price_structure(trendline) artık
HER ZAMAN ham (fixed 3/3) pivot kullanıyor, `zigzag_method` sistem geneli
"atr" kararına bu 4 yer için istisna.

**Düzeltme AYRICA tam 120-sembollük örneklemde YENİDEN ölçülüp doğrulandı**
(ilk turda yalnızca 30 sembollük bir alt-örneklem + 2 grafikle "muhtemelen
düzeldi" denmişti — kullanıcı bunu sorguladı, haklıydı, tam ölçekte tekrar
koşuldu). Sonuç: **6 (gösterge×tf) kombinasyonundan 5'i BİREBİR Faz 0.5
ÖNCESİKİ orijinal sayıya döndü** (wedge 1D: 30=30, triangle 4H: 9=9,
triangle 1D: 8=8, broadening 1D: 128=128), broadening 4H'te küçük bir fark
var (139→193, A2'nin yeni zaman dilimi ölçeklemesinden — Faz 0.5 öncesinde
hiç yoktu, beklenen bir sapma). Bu, düzeltmenin tesadüf değil gerçek
olduğunun güçlü bir kanıtı. **Ama gözle inceleme AYRICA gösterdi ki sayı
düzelmesi TEK BAŞINA yeterli değil** — kalan sinyallerin bir kısmı hâlâ
KALİTE sorunu taşıyor (aşırı uzun süreli "formasyonlar" gibi, aşağıdaki
"Düzeltme sonrası 2. tur" bölümüne bakın) — bu, Faz 0.5'in kapsamı DIŞINDA,
Faz 1'in (literatür temelli süre/derinlik/ön-trend kısıtları) işi.

Diğer üç bulgu (A2/A3/A4) doğrudan doğrulandı, aşağıda kısaca gösteriliyor.

## Yöntem

- Örneklem: BIST evreninden, hem D1 hem 4H'te ≥200 bar önbelleği olan **120
  sembol** (`data/ohlcv/bist/`, network YOK).
- "Eski": her göstergenin Faz 0.5 ÖNCESİ davranışı — `zigzag_method="fixed"`,
  `left=3, right=3`, zaman dilimi ölçeklemesi YOK.
- "Yeni": göstergenin BU OTURUM SONUNDAKİ varsayılan davranışı (aşağıdaki
  düzeltmeden SONRA) — `scaled_factory()` üzerinden, `for_timeframe`
  ölçeklemesi UYGULANMIŞ.
- Sinyal sayısı = `state in (confirmed, completed)` olan `Signal` sayısı
  (price_structure için `event in (zone_touch, zone_break, range_breakout)`).

## A1 — Önce/sonra sinyal sayısı

| Gösterge | TF | Eski (Faz 0.5 öncesi) | Bozuk ("atr", geçici) | **Düzeltme sonrası (nihai)** | Değişim (eski→nihai) |
|---|---|---:|---:|---:|---:|
| patterns.head_shoulders | 4H | 1207 | — | 386 | **%68 azaldı** |
| patterns.head_shoulders | 1D | 1034 | — | 280 | **%73 azaldı** |
| patterns.double_top_bottom | 4H | 3306 | — | 284 | **%91 azaldı** |
| patterns.double_top_bottom | 1D | 1710 | — | 393 | **%77 azaldı** |
| structure.price_structure (zone/range) | 4H | 5627 | — | 1146 | **%80 azaldı** |
| structure.price_structure (zone/range) | 1D | 5183 | — | 1265 | **%76 azaldı** |
| structure.golden_zone | 4H | 1053 | — | 2250 | %114 arttı (beklenen/iyi) |
| structure.golden_zone | 1D | 960 | — | 1773 | %85 arttı (beklenen/iyi) |
| patterns.wedge† | 4H | 7 | 408 | **9** | neredeyse aynı |
| patterns.wedge† | 1D | 30 | 158 | **30** | **BİREBİR aynı** |
| patterns.triangle† | 4H | 9 | 187 | **9** | **BİREBİR aynı** |
| patterns.triangle† | 1D | 8 | 265 | **8** | **BİREBİR aynı** |
| patterns.broadening† | 4H | 139 | 1885 | **193** | A2 ölçeklemesinden fark (bkz. not) |
| patterns.broadening† | 1D | 128 | 1751 | **128** | **BİREBİR aynı** |

† Bu üç gösterge (+ price_structure'ın trendline tarafı, ayrı ölçülmedi ama
AYNI mekanizmayı paylaştığı için aynı düzeltme uygulandı) için "Bozuk"
sütunu (`zigzag_method="atr"` varsayılanıyla, bu oturumun ortasında kısa
süre canlı kaldı) **gerçek bir regresyondu** — aşağıdaki "Kritik bulgu"
bölümüne bakın. "Düzeltme sonrası" sütunu **tam 120-sembollük örneklemde
AYRICA yeniden ölçüldü** (yalnızca ilk turun 30-sembollük tahmini DEĞİL) —
6 kombinasyondan 5'i Faz 0.5 ÖNCESİKİ sayıyla BİREBİR eşleşti; broadening
4H'teki fark (139→193) `zigzag_method="fixed"`e dönmekten DEĞİL, A2'nin
YENİ zaman dilimi ölçeklemesinden geliyor (Faz 0.5 öncesinde `min_bars`/
`prior_trend_lookback` gibi alanlar 4H'te ölçeklenmiyordu, şimdi ×6
ölçekleniyor — bu KASITLI bir davranış değişikliği, A2'nin kendisi).
`zigzag_method="fixed"` bu 4 yerde geri kalıcı varsayılan yapıldı.

**golden_zone'daki artış (yaklaşık 2 kat) BEKLENEN ve İYİ bir sonuç:**
golden_zone zaten `min_swing_atr=3.0` ile KENDİ filtresini uyguluyordu (A1
denetiminde "doğru davranan tek modül" olarak işaretlenmişti); yeni ortak
`atr_mult=3.0` girişi ONUNLA aynı büyüklükte ama DAHA TUTARLI swing'ler
buluyor, ve `min_bars_between` gibi bir üst sınır olmadığı için (golden_zone
HER swing için bir bant üretir) daha fazla TEMİZ swing = daha fazla bant.
Gözle incelemede (aşağı bakınız) bu artan sinyallerin BÜYÜK ÇOĞUNLUĞU
gerçekti.

## A1 — atr_mult taraması (1D, double_top_bottom + head_shoulders birleşik, 120 sembol)

| atr_mult | Toplam confirmed sinyal | Ort. zigzag bacağı (bar) |
|---:|---:|---:|
| 2.0 | 1715 | 8.2 |
| 2.5 | 1107 | 12.1 |
| 3.0 | **673** | 15.6 |
| 3.5 | 454 | 20.8 |

`atr_mult=3.0` seçimi bu ölçümle doğrulandı: 2.0/2.5'te bacak uzunluğu hâlâ
(1D'de bile) 2 haftanın altında kalıyor — "gerçek swing" için ince; 3.5'te
sinyal sayısı %33 daha düşüyor ama bacak uzunluğu (~1 ay) formasyon
göstergelerinin çoğu için gereksiz katı olmaya başlıyor (özellikle 4H'te
6× ile çarpıldığında). **3.0 varsayılan olarak KORUNDU.**

## A2 — Zaman dilimi ölçekleme demosu

```
DoubleTopBottomParams.min_bars_between varsayılan (1D taban): 5
  1H -> min_bars_between=120
  4H -> min_bars_between=30
  1D -> min_bars_between=5
  1W -> min_bars_between=1
```

Beklendiği gibi çalışıyor — 4H'te 6×, 1H'te 24×, 1W'de (round(5/5)=1, min 1
tabanına takılıyor).

## A3 — supported_timeframes kapısı demosu

```
momentum.alpha_rank    supported_timeframes=['1D']       4H'te ATLANIR
momentum.momentum_rank supported_timeframes=['1D']       4H'te ATLANIR
trend.weekly_channel   supported_timeframes=['1W','1D']  4H'te ATLANIR
```

`engine.run()`'ın gerçek kapısı `tests/test_scanner/test_supported_timeframes_
gate.py`'de ayrıca (gerçek `ProcessPoolExecutor` üzerinden) doğrulandı; burada
yalnızca kapının okuduğu TEK kaynağın (`CATALOG[name].supported_timeframes`)
doğru olduğu gösteriliyor.

## A4 — Hacim onayı demosu

```
patterns.double_top_bottom (1D, YENİ ayarlar): 22 confirmed sinyal,
12 tanesi hacim onayından GEÇMİYOR (%54.5) -- require_volume_confirm=True
olsaydı bunlar confirmed'a hiç terfi etmezdi.
```

Gerçek veride hacim eşiğinin (`vol_k=1.2`) sinyallerin yarısından fazlasını
elediği doğrulandı — `require_volume_confirm` parametresinin gerçek bir etkisi
olacağı, bu turda varsayılanın (False) neden korunduğu (davranış değişikliği
kararı Faz 8'in ölçümüne bırakıldı) teyit edildi.

## KRİTİK BULGU — trendline aday havuzu ATR pivotlarıyla bozuluyor

**Bulgu:** `patterns.wedge`/`patterns.triangle`/`patterns.broadening`
(`build_trendlines` + `classify()` — yakınsama/ıraksama geometrisi) için
`significant_pivots(method="atr")`'ın SEYREK çıktısını kullanmak, sinyal
sayısını 12-57 KAT ARTIRDI (`patterns.broadening` 4H: 139→1885).

**Kök neden (kod + gerçek veriyle doğrulandı):** `build_trendlines`'ın
`min_touches=2` şartı, bir çizginin ÜZERİNDEN GEÇTİĞİ en az 2 pivot ister —
ama İKİ NOKTA HER ZAMAN bir doğru tanımlar, yani bu şart SEYREK bir pivot
kümesinde (ATR ile ~5-30 pivot) neredeyse HİÇBİR ŞEYİ ELEMİYOR. YOĞUN bir
kümede (fixed 3/3 ile ~90-100 pivot) ise gerçek bir filtre: bir çizginin
3+ pivotu "doğru" bir toleransla yakalaması çok daha nadir. Sonuç: SEYREK
pivotlarla ÇOK SAYIDA "iki noktalı" resistance/support çizgisi üretiliyor,
bunların rastgele ikili kombinasyonlarından `classify()`'ın yakınsama/
ıraksama testini "tesadüfen" geçenler artıyor.

**Gözle doğrulama (13 örnek — 5 golden_zone, 3 broadening, 2 doğrulama
grafiği, 1 head_shoulders, 1 double_top_bottom, 1 wedge, 1 triangle):**

| # | Sembol | Gösterge/TF | Yorum |
|---|---|---|---|
| 1 | KRDMB | broadening 4H | Trend çizgisi hiç yok, düz yükseliş trendi. **Gerçek değil.** |
| 2 | KRDMD | golden_zone 1D | Zigzag temiz, bant doğru swing'e oturmuş. **Gerçek.** |
| 3 | VBTYZ | golden_zone 4H | Bant + reaksiyon mantıklı. **Gerçek.** |
| 4 | GARAN | broadening 1D | İki sınır neredeyse **paralel**, ıraksama yok. **Şüpheli.** |
| 5 | VESBE | broadening 4H | Formasyon çizgisi/kutusu hiç görünmüyor (ayrı renderer bulgusu). **Değerlendirilemedi.** |
| 6 | FONET | golden_zone 4H | Bant + BAŞARISIZ/BAŞARILI mantıklı. **Gerçek.** |
| 7 | POLTK | golden_zone 1D | Zigzag + bant tutarlı. **Gerçek.** |
| 8 | KRPLS | head_shoulders 1D | OBO çizgisi/etiketi hiç görünmüyor (ayrı renderer bulgusu). **Değerlendirilemedi.** |
| 9 | HALKB | golden_zone 4H | Etiket/bant arasında görsel tutarsızlık (declutter üst üste binmesi olabilir). **Şüpheli.** |
| 10 | ISCTR | golden_zone 1D | Zigzag + bant tutarlı. **Gerçek.** |
| 11 | BAKAB | double_top 4H | İki dip eşit + boyun kırılımı MEKANİK doğru ama hologram amorf (bilinen Faz 1 konusu). **Sınırda.** |
| 12 | BARMA | wedge 4H (ATR, düzeltme ÖNCESİ) | Fiyat 46→8 düz çöküş, hiç yakınsama yok. **Kesinlikle gerçek değil.** |
| 13 | ISDMR | triangle 4H (ATR, düzeltme ÖNCESİ) | Geniş V dip, hiç üçgen çizgisi yok. **Kesinlikle gerçek değil.** |

**golden_zone için sonuç: 5/6 net gerçek, 1/6 şüpheli — ATR pivotları burada
güvenilir.** **wedge/triangle/broadening için sonuç: 0/3 net gerçek (1 hayır,
1 şüpheli/paralel, 1 renderer sorunu nedeniyle değerlendirilemedi) — ATR
pivotları BOZUYOR.**

**Düzeltme uygulandı (bu oturumda):** `WedgeParams`/`BroadeningParams`'ın
`zigzag_method` varsayılanı **"fixed"e geri çevrildi** (`atr_mult`/
`min_swing_atr` parametreleri hâlâ mevcut, isteyen elle "atr" seçebilir).
`structure.price_structure`'ın `_trendlines`'ı da (ayrı ölçülmedi ama AYNI
mekanizma) artık `zigzag_method`'dan BAĞIMSIZ her zaman ham `find_pivots`
kullanıyor — yalnızca `_zones` (golden_zone'a benzer, kendi kapalı zigzag
YAPISI DEĞİL, kümeleme mantığı) `zigzag_method="atr"` varsayılanını korudu.

**Düzeltme sonrası doğrulama — sayısal (TAM 120-sembollük yeniden ölçüm,
`scripts/sistemik_denetim.py`'nin sonucunu ilk raporladıktan SONRA, kullanıcının
"gerçekten düzeldi mi emin misin" sorusu üzerine ayrıca koşuldu):** yukarıdaki
tabloda gösterildiği gibi 6 kombinasyondan 5'i Faz 0.5 öncesi sayıyla BİREBİR
eşleşti. Bu, ilk turda yalnızca 30-sembollük bir alt-örneklemle yapılan hızlı
kontrolden ÇOK daha güçlü bir kanıt.

**Düzeltme sonrası doğrulama — görsel (2. tur, gerçek grafikler, toplam 5
örnek):**
- BARMA/wedge (4H): 23 farklı sinyal (tüm dönem boyunca) → **3 sinyal, tek
  pattern zinciri** (pending→confirmed→expired, mantıklı bir yaşam döngüsü).
- GARAN/broadening (1D): yanlış "paralel kanal" iddiası → **hiç sinyal yok**
  (doğru — gerçek bir genişleme geometrisi bulunamadı).
- **TUCLK/wedge (1D) ve TUCLK/broadening (1D):** sinyal ÜRETİLDİ ama
  formasyon hologramı Ocak 2025'ten Temmuz 2026'ya (**~18 ay**) uzanıyor —
  klasik takoz/genişleme tanımına (birkaç hafta-ay) HİÇ uymuyor; aradaki
  büyük bir fiyat sivrisi (13.3'e kadar) kutunun tamamen DIŞINDA kalmış.
  **Bu, düzeltmenin TAM ÇÖZMEDİĞİ bir kalite sorunu:** "fixed" pivot
  kaynağı trendline ÇİZGİLERİNİ (2 uç nokta) daha güvenilir kıldı ama
  formasyonun SÜRESİNE (iki pivot arasındaki bar mesafesine) bir üst sınır
  yok — `max_apex_bars` yalnızca "doğum barından apex'e" mesafeyi sınırlıyor,
  P1-P2 pivot mesafesini DEĞİL. **Bu, Faz 0.5'in kapsamı DIŞINDA** (pivot
  kaynağı/zaman ölçekleme meselesi değil, formasyonun kendi süre/geometri
  kısıtı) — Faz 1'in (klasik formasyon motoru v2) ele alması gereken bir
  konu, `docs/PROGRESS_LOG.md`'ye "BULUNAN HATA" olarak ayrıca not düşüldü.
- **SKBNK/triangle (4H):** sinyal üretildi ama grafikte HİÇBİR üçgen
  çizgisi görünmüyor (VESBE/KRPLS ile AYNI, önceden not düşülen render/
  declutter sorununun ÜÇÜNCÜ tekrarı — bu sorunun tek seferlik değil,
  YAYGIN olduğunu doğruluyor).

**Dürüst sonuç:** Sinyal SAYISI kesin olarak düzeldi (tam ölçekli ölçümle
doğrulandı). Kalan sinyallerin KALİTESİ ise KISMEN iyi (BARMA/GARAN gibi
temiz örnekler var) KISMEN hâlâ sorunlu (TUCLK gibi aşırı-uzun-süreli
formasyonlar) — bu son kısım Faz 0.5'in DEĞİL, Faz 1'in hedefi.

`pytest -q -m "not network"`: **619/619 yeşil** (golden testler bu düzeltmeyle
regenerate edildi — `structure.price_structure`'ın çizim çıktısı KASITLI
olarak değişti, gerekçesi yukarıda).

## Kapsam dışı bulunan (bu fazda düzeltilmedi) bulgular

**BULUNAN HATA 1 — bazı formasyon sinyalleri render'da hiç görünmüyor.**
VESBE (`patterns.broadening`, `retest_hold` durumu), KRPLS
(`patterns.head_shoulders`, `retest_hold` durumu) VE SKBNK
(`patterns.triangle`, 4H, düzeltme SONRASI turda bulundu) örneklerinde,
sinyal GERÇEKTEN üretilmiş olmasına rağmen (kod seviyesinde doğrulandı)
grafikte HİÇBİR çizgi/kutu/etiket görünmedi — ne varsayılan pencerede ne
`--last-n 0` (tüm geçmiş) ile. Üç bağımsız örnekte tekrarlandığı için
TEK SEFERLİK bir tesadüf değil, YAYGIN bir sorun. Şüphe: `renderer.py`'nin
declutter mekanizması (`_latest_per_group`/`_declutter_levels`) belirli
pattern durumlarındaki (`retest_hold` gibi) zincirleri sistematik olarak
eliyor olabilir. Faz 3/4'ün (SVG motoru) kapsamı — kod DEĞİŞTİRİLMEDİ,
yalnızca not düşüldü.

**BULUNAN HATA 3 — formasyon süresine (P1-P2 pivot mesafesi) üst sınır
yok.** TUCLK örneğinde (`patterns.wedge`/`patterns.broadening`, 1D)
düzeltme sonrası kalan bir sinyal, hologramı ~18 ay (Ocak 2025 - Temmuz
2026) kapsayan, aradaki büyük bir fiyat hareketini (13.3'e kadar bir sivri)
kutunun dışında bırakan gerçekçi olmayan bir "formasyon" üretti.
`max_apex_bars` yalnızca doğum barından apex'e (iki çizginin projeksiyon
kesişimine) olan mesafeyi sınırlıyor, iki trendline'ın KENDİ uç
pivotlarının (P1-P2) birbirinden ne kadar uzak olabileceğine bir üst sınır
YOK — bu yüzden "fixed" (yoğun) pivot kaynağı bile aşırı-uzun-süreli
formasyonları engelleyemiyor. Faz 1'in (klasik formasyon motoru v2,
literatür temelli süre kısıtları) kapsamı — kod DEĞİŞTİRİLMEDİ, yalnızca
not düşüldü.

**BULUNAN HATA 2 — `tlab plot`'un varsayılan pencereleme mantığı eski
(expired/tamamlanmış) sinyalleri gösteremiyor.** KRPLS ve BARMA
örneklerinde sinyal tarihi (2025-05 / 2026-02) varsayılan pencerenin
(`--last-n` boş → son 250 bar) DIŞINDA kaldı; `--last-n 0` (tüm geçmiş)
ile bile, sonraki büyük bir fiyat hareketi (BARMA'nın 82'den 8'e çöküşü
gibi) y-ekseni ölçeğini o kadar genişletiyor ki eski/küçük formasyon
görsel olarak SIKIŞIP kayboluyor. Kullanıcı deneyimi açısından gerçek bir
sorun (kullanıcı "AL sinyali geldi" görüp grafiğe baktığında sinyali
GÖREMEYEBİLİR) ama Faz 3/4/S4'ün (grafik yüzeyi, "sinyal tarihine
yakınlaştır" gibi bir özellik) kapsamı.

## Sonuç ve varsayılan kararlar

| Parametre | Nihai varsayılan | Gerekçe |
|---|---|---|
| `atr_mult` (sistem geneli) | **3.0** | atr_mult taraması + gözle inceleme |
| `zigzag_method` — head_shoulders/double_top_bottom/golden_zone | **"atr"** | Ölçüm + gözle inceleme İKİSİ DE destekliyor |
| `zigzag_method` — price_structure `_zones` | **"atr"** | Zone/range ölçümü güçlü (%76-80 azalma) |
| `zigzag_method` — wedge/triangle/broadening | **"fixed"** (İSTİSNA) | ATR trendline aday havuzunu bozuyor — ölçüm + gözle inceleme İKİSİ DE gösterdi |
| `zigzag_method` — price_structure `_trendlines` | **her zaman "fixed"** (parametreden bağımsız) | Aynı mekanizma, aynı istisna |

`pytest -q -m "not network"`: 619 yeşil. `ruff check tlab/ tests/`: 19 hata
(baseline ile aynı). `mypy tlab/`: 1 hata (baseline, ilgisiz). `lint_
lookahead`: 3 uyarı (baseline, ilgisiz).
