# CLAUDE.md

Bu dosya proje ilerledikçe güncellenir. Yeni bir oturuma başlarken önce bu dosyayı oku —
klasörü baştan taramaya gerek yok, "İlerleme Durumu" bölümü nerede kaldığımızı özetliyor.

## Proje Nedir

Python tabanlı teknik indikatör araştırma laboratuvarı (paket adı: `tlab`). Bilanço Radar
(temel analiz) projesinden bağımsız ama ileride onunla aynı app'te birleşecek — teknik +
temel analiz tek arayüzde.

Her indikatör:
- Python'da yazılır (Pine Script değil — TradingView'a taşınacaksa ileride ayrıca portlanır)
- Aynı standart arayüze uyar (`BaseIndicator` → `IndicatorResult`), böylece toplu tarama motoru hepsini aynı şekilde çağırabilir
- **4 saatlik ve Günlük** zaman dilimlerinde eş zamanlı taranır (tek bir tarama koşusunda tüm evren × tüm indikatörler × iki TF)
- Tekil hisse modu: bir sembol seçilip tek bir indikatör için detaylı görselleştirme alınabilir — o indikatörün ürettiği her seviye/çizim/etiket grafik üzerinde görünür olmalı (sadece sinyal metni değil, tam görsel kanıt)

## KRİTİK TASARIM İLKESİ: Repaint/Lookback Yasağı

Hiçbir indikatör pivot-onaylı, gecikmeli veya geriye-dönük bakan (lookahead) sinyal üretmeyecek.
Sinyal, o barda anlık olarak üretilmeli ve sonradan değişmemeli (non-repainting). Bu, Bilanço
Radar projesindeki teknik çalışmalarda tekrar tekrar vurgulanmış, ihlal edilemez bir kural.

Somut kural: bir sinyalin `bar_time`'daki değeri yalnızca `bar_time` ve öncesi verilerle
hesaplanır. Pivot tabanlı hesaplarda sinyal tarihi = pivotun ONAYLANDIĞI bar (pivot barının
kendisi değil) — `Signal.bar_time` ile `Signal.detected_at` bu yüzden ayrı tutulur. Yasak
desenler: `df.shift(-n)`, `rolling(center=True)`, `find_peaks`/`argrelextrema` sonucunu
doğrudan sinyal barına yazmak, açık (kapanmamış) barla sinyal üretmek. Her indikatör
`tlab/testing/repaint.py::repaint_test`'ten geçmeden "tamamlandı" sayılmaz; statik denetim
için `tlab/testing/lint_lookahead.py` da var (CLI: `tlab lint`).

## İlerleme Durumu

- **Faz 0 — İskelet**: TAMAMLANDI. `core/types.py` (Signal/Level/Line/Box/Polygon/Marker/
  IndicatorResult), `core/indicator.py` (BaseIndicator, Registry), `core/params.py`
  (BaseParams, params_hash), `testing/repaint.py`, `testing/lint_lookahead.py`.
- **Faz 1 — Veri katmanı**: TAMAMLANDI. `data/providers/` (yfinance+csv), `data/calendar.py`
  (BIST 4H hizalaması TradingView gözlemine göre 09:00/13:00/17:00), `data/resample.py`,
  `data/store.py` (parquet cache), `data/validate.py`. `config/universe_bist.txt`: 648 sembol.
- **Faz 2 — Özellik katmanı** (`tlab/features/`): TAMAMLANDI. `swings.py` (Pivot,
  find_pivots, alternate_pivots, label_structure, atr_zigzag), `fibonacci.py`
  (retracement/extension/projection_abcd/ratio/within), `trendlines.py`, `ranges.py`,
  `zones.py`, `volume_profile.py`, `stats.py` (zscore/log_spread/rolling_beta/rolling_corr/
  halflife/adf_pvalue), `ma.py`, `oscillators.py` (macd/rsi/stochastic), `volatility.py` (atr).
- **Faz 3 — Harmonik formasyon motoru** (`tlab/indicators/harmonics/`): TAMAMLANDI.
  Aşağıdaki "Harmonik Formasyon Tarayıcı" bölümüne bakın.
- **K0 — Bilgi-işleme iskelesi**: TAMAMLANDI (2026-08-28, `bilanco-radar` repo commit
  `8eb4627`). Bilanço Radar'daki kitap-okuyucu/quant-uzmani/kod-gelistirici agentlarına
  teknik kol bölümleri eklendi; yeni agentlar `teknik-analiz-uzmani` (bilgi→spec) ve
  `strateji-kod-inceleyici` (kod denetim); yeni skiller `teknik-bilgi-cikarma` ve
  `tlab-mimari` (bu projeye de kopyalandı: `.claude/skills/tlab-mimari/SKILL.md`);
  `bilgi-bankasi/teknik/` ve `kitaplar/teknik/` iskeleti. **Fiziksel konum notu:** paylaşımlı
  agent/skill dosyaları `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\` içinde yaşıyor
  (bu projeyle aynı üst klasörde değil, ayrı bir yerel git deposu — remote: QuaxisLabs, ana
  dal `main`); bu proje ile fiziksel birleşme henüz yok, sadece push sırasında (bkz. Git/Push
  Prosedürü) tek repoda buluşuyorlar. Sırada K1 (Pesavento/TWYS çıkarımı, kitap kullanıcı
  tarafından `bilanco-radar/kitaplar/teknik/` altına eklenecek).
- **K1 — Pesavento (TWYS) çıkarımı**: TAMAMLANDI (2026-08-28, `bilanco-radar` repo commit
  `a4f71a7`). `bilgi-bankasi/teknik/10_pesavento_twys.md` — FORMASYON-01..07, ORAN-01..14,
  KURAL-01..35, PSK-01..07 + Faz 3 karşılaştırma tablosu (pesavento.py vs kitap).
- **K1-D — pesavento.py TWYS ile hizalama**: TAMAMLANDI (2026-08-28). Detaylar yukarıda
  "Harmonik Formasyon Tarayıcı" bölümünde.
- **EK-A — Three Drives paterni TWYS ile hizalama**: TAMAMLANDI (2026-08-28). Görev metni
  "Three Drives'ı pesavento.py'ye ekle" diyordu, ama patern zaten Faz 3'te AYRI bir ekol
  (`schools/three_drives.py`, "harmonic.three_drives") olarak eklenmişti — pesavento.py'nin
  kendi `patterns` sözlüğüne YİNELENMEDİ (iki ayrı "three_drives" implementasyonu aynı
  ekol içinde çelişki yaratırdı). Bunun yerine mevcut `three_drives.py`, K1'in
  FORMASYON-04 çıkarımıyla karşılaştırıldı: tek fark `abc` (ORAN-08) — A/C geri çekilmesi
  kitapta .382/.618/.786 kabul ediliyordu, kod yalnızca (.618,.786) kabul ediyordu; bant
  (.382-tol,.786+tol)'e genişletildi. `xab`(ORAN-07)/`d_components`/`invalidation`
  (geçersizlik madde 4) zaten uyumluydu, değişmedi. 1 yeni test. Toplam test 156→157.
- **K2 — 11 bölümlük strateji külliyatı incelemesi**: TAMAMLANDI (2026-08-28,
  `bilanco-radar` repo commit `5bc4896`). 11/11 bölüm, 38 STRAT-xx, 28 DISIPLIN-xx.
  Karar dağılımı: AL 18, PARK 6, ŞARTLI PARK 3, KAPSAM DIŞI 11. En kritik bulgu: ch9'da
  `fx_data[pair].iloc[0]`'a göre normalize eden gerçek bir lookahead (kaynağın kendi
  "güvenli" iddiasını çürütüyor) — ayrıca `repaint_test`'in "sol-kesme" (farklı miktarda
  geçmiş) duyarlılığını yakalamayabileceğine dair bir metodolojik not düşüldü, ileride
  ayrıca değerlendirilmeli. Çıktı: `bilgi-bankasi/teknik/kod/ch01..ch11_*.md` +
  `00_uygulanabilirlik_matrisi.md`.
- **Faz 4 — Yapı indikatörleri** (`tlab/indicators/structure/`): TAMAMLANDI (2026-08-28).
  `swing_fib_abcd.py::SwingFibABCD` ve `price_structure.py::PriceStructure`. Detaylar ve
  ÖNEMLİ SAPMALAR/tasarım kararları için aşağıdaki "Yapı İndikatörleri" bölümüne bakın —
  özellikle PriceStructure'ın generic `Registry.register()`'a KAYDOLMADIĞI (trendline
  "aday havuzu" + hacim profili pencere sorunu nedeniyle, bilinçli mimari karar).
  17 yeni test. Toplam test 157→174. TCELL 1D gerçek veri smoke testi başarılı
  (`outputs/debug/swing_fib_abcd_TCELL.json`, `price_structure_TCELL.json` — git dışı).
- **Faz 5 — Pair relatif momentum** (`tlab/indicators/pairs/`, `tlab/backtest/pairs_engine.py`):
  TAMAMLANDI (2026-08-28). Detaylar için aşağıdaki "Pair Trading (Faz 5)" bölümüne bakın —
  özellikle `BaseIndicator.compute`'un `context` parametresini kullanan İLK indikatör olması
  ve `repaint_test`/`Registry.register`'a context-farkındalıklı kesim eklenmesi (Faz 0'dan
  beri var olan ama Faz 3/4'te kullanılmamış bir mekanizma, geriye uyumlu genişletildi).
  20 yeni test. Toplam test 174→194. TCELL/ISCTR gerçek veri CLI smoke testi başarılı
  (`tlab pair --y TCELL --x ISCTR --tf 1d`); AKBNK/GARAN üzerinde gerçek-veri discovery
  denemesi dürüstçe SIFIR aday döndürdü (gerçek piyasa verisi her zaman eşikleri geçmez,
  bu beklenen/kabul edilebilir bir sonuç — uydurulmadı).
  Tam 648-sembol evren taraması ("binlerce ikili") HENÜZ YAPILMADI — bu, ayrı bir
  veri-önbellekleme ağırlıklı takip adımı (bkz. "Sıradaki Adımlar").
- **Faz 6 — Scanner engine, EOD, SQLite sonuç deposu** (`tlab/scanner/`): TAMAMLANDI
  (2026-08-28). Detaylar için aşağıdaki "Tarama Motoru (Faz 6)" bölümüne bakın —
  özellikle `tlab/indicators/bootstrap.py` (Registry'ye kayıt sorunu: `HarmonicIndicator`
  class-level `meta` taşımıyor, `Registry.register()` artık CLASS değil INSTANCE alıyor)
  ve `IndicatorResult.from_json()`'daki GERÇEK bir hatanın bulunup düzeltilmesi (fiyat-
  indeksli seriler — `vp_bins` vb. — JSON round-trip'te Timestamp olarak ayrıştırılmaya
  çalışılıp çöküyordu; hiçbir önceki test bunu YAKALAMAMIŞTI çünkü `to_json`/`from_json`
  hiç egzersiz edilmemişti). 12 yeni test. Toplam test 194→206. TCELL/ISCTR/AKBNK/GARAN/
  THYAO/SAHOL/KCHOL/EREGL/BIMAS/ASELS (10 sembol) üzerinde gerçek EOD akışı (veri
  güncelleme → tarama → SQLite kayıt → idempotentlik → rapor) uçtan uca test edildi.
  Performans: 10 sembol × 2 TF × 10 indikatör = 200 iş, 13,5s (önbellekten); en yavaş
  indikatör `structure.price_structure` (trendline'ların O(n²) aday üretimi nedeniyle
  diğerlerinden ~10-30× yavaş) — 100 sembol için tahmini seri süre ~6 dk (10 dk eşiğinin
  altında, ama bu KÜÇÜK örneklemden EKSTRAPOLASYONDUR, gerçek 100-sembol koşusu henüz
  yapılmadı — ilk veri indirme süresi de bu tahmine DAHİL DEĞİL).
- **Faz 7 — Görselleştirme + EOD HTML raporu** (`tlab/viz/`): TAMAMLANDI (2026-08-28).
  Detaylar için aşağıdaki "Görselleştirme (Faz 7)" bölümüne bakın — özellikle
  `IndicatorResult.series_layout` (yeni, opsiyonel alan) eklenmesi ve gerçek veriyle
  render ederken bulunan/düzeltilen 3 GERÇEK hata (fill-renk ters eşlemesi, pair
  modunda `add_vrect` sessiz no-op'u, harmonik `xb` çizgisinin sınırsız eğim
  projeksiyonu). README'de 6 referans görselin öğe-öğe kontrol listesi var
  (bazı öğeler kasıtlı GAP olarak işaretli — renderer hesap yapmama ilkesi
  gereği eklenemeyenler).
- **Faz 8A — Çoklu kırılım tarayıcısı** (`tlab/indicators/trend/breakouts.py::MultiBreakout`):
  TAMAMLANDI (2026-08-28). Detaylar için aşağıdaki "Çoklu Kırılım Tarayıcısı (Faz 8A)"
  bölümüne bakın. **Faz 2-EK'in TAMAMI değil, yalnızca Faz 8A'nın ihtiyaç duyduğu iki
  parçası** yazıldı: `volatility.py::bollinger()` ve YENİ `channels.py::regression_channel()`
  — `pivot_channel`/`frozen_channel_at`/`channel_position`, `patterns_geom.py`,
  `hs_pattern.py`, `zones_sd.py`, `xsec.py`, W1 zaman dilimi HÂLÂ YAPILMADI (bilinçli
  kapsam daraltması, kullanıcı özellikle "Faz 8A'yı yap" dedi). İki gerçek hata bulunup
  düzeltildi: `price_structure.py`'de trendline kırılım yönü (resistance/support)
  TERS eşlenmişti; `IndicatorResult.to_json()` `numpy.bool_` tipini serialize edemiyordu
  (ilk kez scanner'ın süreçler-arası JSON aktarımıyla ortaya çıktı — Faz 6'daki
  price-indexed-series hatasıyla AYNI kategori: hiçbir önceki test bu round-trip'i
  gerçek veriyle egzersiz etmemişti). `config/scans.yaml` + `tlab scan --preset` eklendi.
  8 yeni test (211→219).
- **Görselleştirme declutter düzeltmesi** (2026-08-28, Faz 8A'dan HEMEN SONRA, kullanıcı
  geri bildirimiyle): TAMAMLANDI. Detaylar "Görselleştirme (Faz 7)" bölümünün sonunda.
  Özet: gerçek çok-yıllık veride grafikler "curcuna" hâline geliyordu (onlarca eski
  fib/PRZ/trendline etiketi üst üste biniyordu) — `renderer.py`'ye `declutter=True`
  varsayılanı eklendi (yalnızca her stilin EN GÜNCEL örneği tam etiketlenir), `tlab
  plot`'un `--last-n` varsayılanı 250'ye düşürüldü, `--show-all` ile eski davranışa
  dönülebilir. 3 yeni test (219→222).
- **Görselleştirme kalite düzeltmesi** (2026-08-29, kullanıcı verdiği 2 referans ekran
  görüntüsüyle `outputs/samples/tcell_price_structure.png` ve `alark_harmonic_pesavento.png`
  karşılaştırılarak bulundu): TAMAMLANDI. Kullanıcı geri bildirimi: dışa aktarılan PNG'ler
  referanslara göre küçük/bulanık, harmonik köşe (X/A/B/C) hiç işaretlenmiyordu ve grafik
  metinleri (özellikle direnç/destek/POC/VAH/VAL kümelendiği "confluence" bölgelerinde)
  okunaksız üst üste biniyordu. Altı somut düzeltme:
  1. `_apply_layout`'a açık `width` (varsayılan 1600, pair modunda 1500) ve yükseklik
     tabanı büyütme (`600+180*n_sub`, eskiden `520+160*n_sub`) eklendi; `tlab plot`'un
     `.png` çıktısında `fig.write_image(..., scale=2)` — eskiden kaleido `width=`
     verilmeden ~700px'e düşüyordu, bu yüzden tüm örnek PNG'ler referanslara göre
     küçük/sıkışık görünüyordu.
  2. **Gerçek hata** — `_draw_lines`/`_draw_levels`, `Line.label`/`Level.label`'ı (ör.
     harmonik tarayıcının `f"{school}_{pattern}_{x_idx}_{a_idx}_{b_idx}_{c_idx}_prz_low"`
     gibi dahili eşleştirme kimliklerini) OLDUĞU GİBİ `text=` yapıyordu — grafikte çıplak
     "pesavento_g..." metni görünüyordu. Yeni `_display_text()`: bilinen bir son ek
     varsa (`_xb`→"X-B", `_xd_envelope`→"Hedef Zarfı", `_prz_low`→"PRZ Alt",
     `_prz_high`→"PRZ Üst") kısa Türkçe karşılığını, `_looks_like_raw_id()` (boşluksuz +
     ≥2 alt çizgi) ham-kimlik deseni eşleşirse `tr_style(style)`'ı kullanır; AKSİ HALDE
     `label` OLDUĞU GİBİ bırakılır — `price_structure.py`/`swing_fib_abcd.py`'nin ZATEN
     kısa/anlamlı etiketleri ("VAH"/"VAL" — ikisi de `style="value_area"`, yalnızca
     `label` ayırt eder —, "fib_0.618", "Direnç (Temas:6)") bu ayrım OLMASAYDI `style`e
     indirgenip bilgi kaybederdi (ilk taslakta tam bu regresyon yaşandı, düzeltildi).
  3. Etiket çakışması: `_draw_boxes`/`_draw_levels`/`_draw_lines` artık `_stagger_
     yshifts()` adlı ortak bir "cetvel" sezgisi kullanıyor — `price`e göre sıralı işlenir,
     her öğeye `base + n*step` (n=0,1,2,…, HEP aynı işarette tek yönde büyür) biçiminde bir
     `yshift` atanır; `n`, bu öğenin EKRAN konumunu (`price + offset/px_per_unit`,
     `px_per_unit` ana panelin tahmini piksel-yüksekliğinden hesaplanır) bir ÖNCEKİ
     öğeninkinden `_STAGGER_TRIGGER_PX` (18px) uzaklaştıracak kadar büyütülür — `n` HİÇBİR
     ZAMAN küçültülmez (aksi halde ekran konumları `price` sırasıyla tutarlı artmaz/azalmaz,
     bu da "yalnızca bir öncekiyle kıyasla" kontrolünü GEÇERSİZ kılardı — ilk taslaklarda
     tam bu yüzden ara sıra kaçırılan çakışmalar gözlendi, iteratif olarak düzeltildi).
     Kutu (Direnç/Destek Bölgesi, Konsolidasyon) ve Level (POC/VAH/VAL) etiketleri AYNI
     "confluence" bölgesinde toplandığı için TEK ortak merdivende (birleştirilmiş liste)
     fanlanıyor; çizgi-uzatma etiketleri (ör. "Direnç (Temas:6)") kendi AYRI, hep aşağı
     büyüyen şeridinde kalıyor (böylece iki kategori asla birbirinin şeridine düşmüyor).
  4. Harmonik X/A/B/C köşe noktalarına (`_draw_harmonic_vertices`, yeni) nokta + harf
     etiketi eklendi — eskiden yalnızca son "D: fiyat [DURUM]" kutusu vardı. D noktası
     BURADA tekrar etiketlenmiyor (zaten `_draw_markers`'ta var, `bcd` poligonunun 3.
     noktası da gerçek bir pivot değil, `prz.center`). Hangi adayların "en güncel"
     sayıldığı `_draw_markers`'daki `_MAX_HARMONIC_MARKERS` seçimiyle AYNI mantıkla
     (harmonik Marker'lar `pid` taşımadığı için `last_state` anahtarlarıyla ham marker
     listesinin indeks bazında eşleştiği gözlemine dayanarak) belirleniyor. **Gerçek hata**
     (ikinci bir tur): köşe etiketleri ilk taslakta üçgenin yön-renkli (yeşil/kırmızı)
     rengini kullanıyordu — X/B noktaları çoğu zaman yoğun bir mum kümesinin TAM ORTASINA
     denk geldiği için aynı renkteki metin neredeyse görünmezdi; `theme.text` (nötr) +
     hafif bir `bgcolor` "halo"suyla düzeltildi.
  5. Trendline uzatma çizgisi artık `theme.muted` + `with_alpha(...,0.6)` (soluk) ve
     `width=1.0` — eskiden çizginin kendi parlak rengini taşıyıp gerçek sinyal çizgisiyle
     görsel olarak yarışıyordu.
  6. Annotation font boyutları 9-10px'ten 10-12px'e çıkarıldı (daha büyük 1600px
     kanvasta eskisi sönük kalıyordu).
  Ayrıca `Level`'in x1=last_x'e sabitlenen etiketleri (ör. "Fib Geri Çekilme") tek-kolonlu
  (vp paneli olmayan) grafiklerde figürün sağ kenarına dayanıp KIRPILIYORDU — `_apply_
  layout`'un sağ marjini 50'den 110'a çıkarıldı. 4 örnek PNG (`outputs/samples/`)
  yeniden üretilip referanslarla karşılaştırıldı; `tests/test_viz/test_renderer.py`'ye
  2 yeni regresyon testi eklendi (`test_no_raw_internal_id_in_rendered_annotation_text`,
  `test_harmonic_vertices_labeled_for_recent_candidate`, gerçek bir Gartley adayı
  üreten `build_gartley_ohlcv` fixture'ıyla). 2 yeni test (222→224). `tlab/features/`
  ve `tlab/indicators/` (hesap katmanı) DOKUNULMADI — bu tamamen `tlab/viz/renderer.py` +
  `tlab/cli.py`'nin `write_image` çağrısı kapsamında bir render/stil düzeltmesiydi.
- **Görselleştirme "aracı kurum raporu" tasarım geçişi** (2026-08-29, bir önceki
  kalite-düzeltmesi maddesinin HEMEN ardından, ayrı bir görev olarak): TAMAMLANDI. Önceki
  madde grafikleri "işlevsel açıdan doğru ve okunur" hâle getirmişti; bu tur onları
  "tasarlanmış/markalı" görünüme taşıdı — `renderer.py`'de hiçbir teknik hesap eklenmedi
  (yalnızca stil/yerleşim), tüm renk kararları `themes.py`'de kaldı (tek doğru kaynak).
  1. **Palet revizyonu** (`themes.py`) — `_FIB_NEAREST`/`_LINE_STYLE_COLOR`/
     `_FILL_STYLE_COLOR` eskiden gri/kırmızı/sarı/yeşil/mavi/mor'u keyfi dağıtıyordu
     ("varsayılan grafik kütüphanesi gökkuşağı"). Yeni `Theme.accent` (TEK marka rengi —
     altın/hardal tonu, dark `#d4af37` / light `#9c6b0b`, kontrast için AYRI ayarlandı)
     yalnızca "en karara-değer" öğelere ayrıldı: fib altın bölgesi (%61.8/%78.6), POC,
     hacim-profili Gaussian eğrisi, masthead ayraç çizgisi, pair modunda BUGÜN ateşlenen
     canlı sinyal. Fib %100 → yüksek-kontrast nötr (`text`); geri kalan tüm fib
     basamakları/dashed/dotted/swing/value_area → `gray`/`muted`. `up`/`down` (mum
     renkleri) DEĞİŞMEDİ (yük taşıyan sözleşme). **Gerçek tutarsızlık bulundu**:
     `resistance` ÇİZGİSİ kırmızıyken `resistance_zone` KUTUSU sarıydı (ikisi aynı
     kavramı temsil etmesine rağmen eşleşmiyordu) — ikisi de artık `red`/`blue` ailesinde
     hizalı. Aynı kategori: pair modunda `y_holding` kutusu YEŞİL, Y çizgisinin kendisi
     MAVİYDİ (`x_holding` da benzer şekilde ters); artık `y_holding`→`blue`,
     `x_holding`→`gray`, `_render_pair`'deki gerçek çizgi renkleriyle EŞLEŞİYOR. Yeni
     `Theme` alanları: `page_bg` (dış "sayfa" zemini), `border` (kart/legend kenarlığı).
  2. **Masthead (üst şerit)** — eski tek satırlık `title=` kaldırıldı, yerine
     `_Header` dataclass + `_draw_header()` (paper-referanslı `add_annotation`'larla):
     satır 1 sol=sembol (büyük, kalın), sağ=son kapanış + bir-önceki-bara-göre %
     değişim (yön-renkli, ▲/▼) — bu SADECE biçimlendirme (ham OHLC üzerinde basit
     aritmetik, görev kısıtının açıkça izin verdiği tür), İNDİKATÖR hesabı DEĞİL; satır
     2 sol=kategori (`labels_tr.INDICATOR_CATEGORY_TR`) + formasyon/indikatör alt
     başlığı (`_build_subtitle`, eski `_build_generic_title`'ın sembolsüz hâli), sağ=
     üretim tarihi (bugün). İnce bir `accent` ayraç çizgisi masthead'i grafikten ayırır.
     Pair modu (`_pair_header`) AYNI 2-satırlık düzene katlandı (görev kısıtı: AYRI/
     yinelenen ikinci bir başlık EKLENMEMELİ) — sağ üstte Z-skoru geçişi, yalnızca
     BUGÜN yeni bir sinyal ateşlendiyse `accent` ile vurgulanıyor ("canlı sinyal").
  3. **Dipnot şeridi** — `_draw_footer()`: "Yalnızca teknik analiz amaçlıdır, yatırım
     tavsiyesi değildir — tlab", küçük/soluk, sayfa altında.
  4. **Kart/sayfa çerçevesi** — `paper_bgcolor=theme.page_bg` (dış sayfa) ile
     `plot_bgcolor=theme.bg` (iç "kart") ayrıştırıldı, `_draw_card_frame()` ince bir
     `theme.border` dikdörtgeniyle çizim alanını çerçeveliyor. Legend artık
     `bordercolor=theme.border` ile sınırlı bir kutu (eskiden tamamen saydam/kenarsız).
  5. **Gerçek hata (masthead konumlandırma)** — İlk taslak, masthead ofsetlerini SABİT
     paper-fraksiyonu olarak (`y=1.20` gibi) verdi; paper fraksiyonu TOPLAM figür
     yüksekliğine değil yalnızca ÇİZİM ALANI yüksekliğine (height-t-b) göre ölçeklendiği
     için, alt-panelli (hacim+MACD, 2 ekstra panel) uzun bir figürde aynı fraksiyon çok
     daha fazla piksele karşılık geliyor ve masthead'in sembol/fiyat satırı üst kenar
     boşluğunun TAMAMEN DIŞINA taşıp görünmez oluyordu (`tcell_price_structure.png`
     ilk taslakta yalnızca alt başlık satırı görünüyordu, üst satır yoktu). Düzeltme:
     `_HEADER_ROW1_PX` vb. artık SABİT PİKSEL ofseti olarak tanımlı,
     `_apply_layout` içinde `1 + px/plot_h` ile figüre özgü fraksiyona çevriliyor —
     masthead'in ekrandaki piksel konumu figür yüksekliğinden BAĞIMSIZ. İkinci bir
     benzer çakışma: pair modunun kendi `make_subplots(..., subplot_titles=(...))`
     başlığı ("1- Fiyat Yakınlığı...") masthead'in ayraç çizgisiyle ÇAKIŞIYORDU (Plotly
     alt-panel başlığını satırın domain tepesine, tam masthead'in indiği bölgeye
     yerleştiriyor) — `extra_top_px` parametresiyle (yalnızca pair modu, 44px) masthead
     bu başlığın üstüne itildi.
  6. **Görev metninde adı geçen 2 somut çakışma düzeltildi** — sağdaki hacim-profili
     paneli olan grafiklerde (`structure.price_structure`) "VAH" etiketi "Direnç
     Bölgesi" kutu etiketiyle ve "POC" etiketi "110" y-ekseni tik yazısıyla üst üste
     biniyordu. Kök neden: POC/VAH/VAL gibi `Level.end=None` olan seviyeler HER ZAMAN
     `x1=last_x`'e sabitlenir (`_draw_levels`) ve `xanchor="left"` ile SAĞA doğru
     büyüdükleri için komşu vp paneline ve onun y-ekseni tik yazısına taşıyordu; aynı
     şekilde sağ kenara yakın doğmuş bir Direnç/Destek Bölgesi kutusu da (`_draw_boxes`,
     `xanchor="left"`, `b.t0` sağ kenara yakınsa) aynı şekilde taşıyordu. Düzeltme: yeni
     `_right_edge_cutoff()` görünür pencerenin son %20'lik dilimini işaretler; bu
     dilimdeki box/level etiketleri `has_vp=True` iken otomatik `xanchor="right"`e
     çevrilir (KONUM aynı kalır, yalnızca metin SOLA büyür) — bu TEK değişiklik hem VAH/
     Direnç-Bölgesi çakışmasını hem POC/tik-yazısı çakışmasını çözdü (ikisi de aynı kök
     nedenin — panel dışına taşma — belirtisiydi).
  Doğrulama: 4 örnek PNG yeniden üretildi (`outputs/samples/tcell_price_structure.png`,
  `tcell_swing_fib_abcd.png`, `alark_harmonic_pesavento.png`, `tcell_isctr_pair.png`) ve
  gözle incelendi — VAH/POC çakışması gitti, masthead/dipnot/kart çerçevesi 4 grafikte
  tutarlı, pair modunda alt-panel başlığı ayraçla çakışmıyor. `test_no_raw_internal_id_
  in_rendered_annotation_text` testi, masthead'in `xref="paper"` alt başlığının MEŞRU
  olarak ekol adı içermesi ("Sistem: Carney") nedeniyle güncellendi — denetim artık
  yalnızca grafik-üzerindeki (Level/Line/Marker kaynaklı, `xref!="paper"`) annotation'ları
  kapsıyor (masthead metni ham dahili kimlik DEĞİL, kasıtlı Türkçe rapor metni). Yeni test
  eklenmedi (mevcut 224 test + 1 güncelleme), `pytest -q -m "not network"` yine 224 yeşil,
  `ruff check tlab/ tests/` `tlab/viz/`+`tests/test_viz/` içinde temiz (kalan 18 hata
  önceden var olan, ilgisiz `repaint.py`/`cli.py` satırları).
- **Pair grafiği (dark_terminal) — paylaşılan tasarımdan AYRI düzeltme** (2026-08-29,
  bir önceki "aracı kurum raporu tasarım geçişi" maddesinin HEMEN ardından): TAMAMLANDI.
  Kullanıcı, o geçişin `_render_pair`'e (Görsel 1, `pair.relative_momentum`) uyguladığı
  ortak masthead/tek-legend tasarımını `outputs/samples/tcell_isctr_pair.png`'i inceleyip
  AÇIKÇA REDDETTİ — yalnızca BU grafik için, verdiği bir referans ekran görüntüsüne
  (`images/Ekran görüntüsü 2026-08-26 203751.png`) yakın bir görünüm istedi. `light_analysis`
  tarafı (`_render_price_based` — yapı/harmonik panelleri) BİLİNÇLİ OLARAK dokunulmadı,
  kullanıcı ondan zaten memnundu. Değişiklik kapsamı: `renderer.py`'de yalnızca pair moduna
  özgü kod + `themes.py`'de yalnızca `DARK_TERMINAL` (bu tema salt pair modunda ve Görsel 4
  metrik tablosunda kullanılıyor, `light_analysis`'a dokunulmadı).
  1. **Ayrı masthead/kart çerçevesi** — pair modu artık `_apply_layout`/`_draw_header`/
     `_draw_card_frame`'i (jenerik/harmonik moduna ait, büyük 2-satırlı sol-sembol/sağ-değer
     masthead + kart çerçevesi) HİÇ ÇAĞIRMIYOR; kendi `_apply_pair_layout`/`_draw_pair_
     header`'ı var — küçük, sol-hizalı, kart çerçevesiz 2 satır (referansla birebir). Satır 1
     (renkli): `"{DURUM} | {SEMBOL} AL ({açıklama}) | Z: {önceki} → {şimdi} | {tarih}"` —
     `signal_today` varsa metni + yeşil, yoksa `last_state["zone_state"]`'in Türkçe karşılığı
     (`_ZONE_STATE_TR`) + nötr beyaz; `açıklama` "Y Ucuz -> Dönüş Onaylandı"/"X Ucuz -> Dönüş
     Onaylandı" — hangi tarafın tutulduğuna (`last_state["holding"]`) göre. Satır 2 (soluk
     gri): sabit strateji adı + çift + `net_pnl`/`return_pct`/`n_trades`'in biçimlendirilmesi
     (`"K/Z: +19.664 TL (%+19.7) | Geçiş: 11 kez"` biçiminde) — TÜMÜ zaten `last_state`'te
     hesaplı, YENİ bir indikatör hesabı YOK (eski tek satırlık başlık da aynı ilkeyle
     çalışıyordu).
  2. **Zemin** — `DARK_TERMINAL.bg` `#0e1116`'dan `#000000`'a (referans neredeyse saf siyah,
     eskiden `page_bg`'den belirgin ayrışan bir "kart" tonu vardı); `grid` de `#161a1f`'e
     karartıldı. `page_bg` zaten `#000000`'dı, değişmedi.
  3. **Panel başlıkları yeşil** — `make_subplots(subplot_titles=...)`'ın varsayılan gri
     rengi yerine `_style_pair_subplot_titles()` ile `theme.green` uygulanıyor (metne göre
     hedefleniyor, `make_subplots()`'tan hemen sonra, hesap YOK — salt stil).
  4. **Panel-başına 3 ayrı legend** — tek sağ-taraf legend YERİNE Plotly 5.15+'ın `legend`/
     `legend2`/`legend3` mekanizması (yüklü sürüm 7.0.0'da doğrulandı, gerçekten destekleniyor
     — fallback'e GEREK KALMADI). Her legend'ın y konumu `fig.layout.yaxis{,2,3}.domain`'den
     (make_subplots'ın row_heights/vertical_spacing'den hesapladığı GERÇEK domain, sabit bir
     kesir VARSAYILMADI) okunup o satırın sol-üst köşesine yerleştiriliyor. Panel 1: ISCTR(X)/
     TCELL(Y) çizgileri + 2 "Tutulan Dönemler" renk-karesi (shape/`add_vrect` legend'a
     kendiliğinden GİRMEDİĞİ için `_add_holding_legend_swatches()` ile verisiz — `x=[None]`
     — 2 ek `Scatter` eklendi). Panel 2: Buy&Hold/Portföy + "Başlangıç" (eskiden `add_hline`
     shape'iydi, legend'a giremiyordu — gerçek bir `Scatter` trace'e çevrildi, hem çizgiyi
     çiziyor hem legend'da görünüyor). Panel 3: Z-Skoru + 2 eşik çizgisi (etiketlerine artık
     `±k` değeri de ekleniyor, ör. "Aşırı Ucuz ISCTR Sınırı (+2.0)" — `upper`/`lower`
     serilerindeki ZATEN var olan sabit değerin biçimlendirilmesi, yeni hesap DEĞİL).
     **Bilinçli sapma:** referans ekran görüntüsü panel 3 legend'ında holding-swatch'ları da
     TEKRARLIYOR (görev metninin kendi kapsam tanımı panel 3'ü yalnızca "Z-Skoru + 2 eşik" ile
     sınırladı) — bu tekrar bilerek EKLENMEDİ, panel 1'de zaten var.
  5. **Tutulan-dönem gölge renkleri** — `_FILL_STYLE_COLOR`'da `y_holding`→`blue`/
     `x_holding`→`gray` (bir önceki tasarım geçişinin "gölge = kendi çizgi rengiyle eşleşsin"
     ilkesi) BİLİNÇLİ OLARAK `y_holding`→`green`/`x_holding`→`blue`'ya çevrildi — referans
     TCELL(Y) için doygun yeşil, ISCTR(X) için koyu mavi/gri-mavi kullanıyor, çizgi renkleriyle
     (Y=mavi çizgi, X=gri çizgi) KASITLI OLARAK eşleşmiyor; bu ayrım referansın kendi
     gölgeleme sözleşmesi, hizalama HATASI değil. Opaklık da `0.20`→`0.28` (saf siyah zemine
     karşı eskisi fazla soluktu).
  6. `_apply_layout`/`_draw_header`'daki artık kullanılmayan `extra_top_px` parametresi
     (yalnızca pair modunun eski `subplot_titles`/masthead çakışmasını çözmek içindi)
     kaldırıldı — pair modu artık bu fonksiyonları hiç çağırmıyor.
  Doğrulama: `outputs/samples/tcell_isctr_pair.png` yeniden üretildi (`tlab plot --symbol
  TCELL/ISCTR --indicator pair.relative_momentum --tf 1d --market bist`), referansla gözle
  karşılaştırıldı — zemin/başlık biçimi/panel-başına legend/yeşil panel başlıkları/tutulan-
  dönem renkleri artık yakın eşleşiyor; en belirgin kalan fark panel 1 legend'ının referansta
  2 sütunlu (bizde tek sütun, Plotly'nin otomatik legend yerleşimiyle basit bir yaklaşım —
  kabul edilebilir görüldü) olması. Yeni test EKLENMEDİ (renderer.py hâlâ salt stil/yerleşim,
  mevcut `tests/test_viz/test_renderer.py::test_pair_render_draws_holding_period_shading`
  hâlâ geçiyor); `pytest -q -m "not network"` 224/224 yeşil (test sayısı DEĞİŞMEDİ), `ruff
  check tlab/ tests/` `tlab/viz/` içinde temiz (kalan 18 hata öncekiyle AYNI, ilgisiz
  `cli.py`/`core/types.py`/`testing/*.py` satırları — bu görev onlara dokunmadı).
- **Pair strateji varsayılan pencere yeniden ayarlandı (2026-08-29).** Kullanıcı,
  referans bir ekran görüntüsündeki sinyal sayısının (TCELL/ISCTR, "Geçiş: 11 kez")
  kendi çıktımızla uyuşmadığını fark etti — önce zaman damgası kanıtıyla ("bu görsel
  hiç var olmamış olabilir" denendi) geçiştirilmeye çalışıldı, kullanıcı haklı olarak
  bunu reddetti ve gerçek bir hesaplama denetimi istedi. Denetim sonucu: **kod hatası
  YOK** (rolling_beta/log_spread/zscore/sinyal üretimi/backtest muhasebesi tek tek
  izlendi, lookahead/off-by-one yok; TCELL/ISCTR verisi 503 bar, boşluksuz). Fark,
  tamamen `window=90` (eski varsayılan) parametresinin z-skorunu aşırı yavaşlatmasından
  kaynaklanıyordu. Bunu doğrulamak için GERÇEK `discover_pairs`+`run_pair_backtest`
  üretim koduyla kapsamlı bir pencere taraması yapıldı: önce 24, sonra 48 sembollük
  (yfinance ile CANLI indirilen, `universe_bist.txt`'nin kendi Fintables kaynaklı
  sektör etiketleriyle gruplanan) evrende `discover_pairs` (sıkı eşik: corr≥0.7,
  adf<0.05, halflife 5-60 → 13 çift; gevşek eşik: corr≥0.5, adf<0.10, halflife 3-90
  → 28 çift) ile keşfedilen TÜM çiftlerde window∈{20,30,40,60,90} test edildi. Sonuç
  HER İKİ eşik rejiminde de tutarlıydı: `window=90` en az işlemi VE en düşük toplam
  PnL/kazanan-çift oranını üretiyordu (sıkı: 18 kapalı işlem/160.633 TL; gevşek: 38
  işlem/352.462 TL); `window=60` en yüksek profit factor'ü VE toplam PnL'i verdi (sıkı:
  PF 4,19/574.292 TL/12-13 çift kârlı; gevşek: PF 3,68/1.000.049 TL/22-28 çift kârlı).
  `window=40` de güçlüydü (en yüksek win rate, daha fazla işlem) ama kullanıcı `window=
  60`'ı seçti — gerekçe: en yüksek PF (daha "temiz" sinyal), keşfedilen çiftlerin
  tipik yarı ömrüne (~13-27 gün) göre pencere/yarı-ömür oranının kaba kurala (3-5x)
  daha yakın olması, ve stratejinin tek çift değil TÜM keşfedilen evrende eş zamanlı
  çalışacağı için çift-başına-seyrek-işlem endişesinin portföy seviyesinde önemsiz
  kalması. **`RelativeMomentumParams.window`/`beta_window`/`min_periods` varsayılanı
  90'dan 60'a değiştirildi** (`relative_momentum.py`, gerekçe kod içinde yorum olarak
  da belgelendi). `pytest -q -m "not network"` 224/224 yeşil (davranış değişikliği
  hiçbir testi bozmadı — testler kendi parametrelerini explicit veriyor). **DÜRÜST
  ÇEKİNCE**: bu bir İN-SAMPLE parametre seçimi (5 pencere değeri aynı ~2 yıllık
  veride denendi, walk-forward/out-of-sample doğrulama YAPILMADI) — backlog'daki
  "kointegrasyon çürüme izleyicisi" (madde 4) bu riski zamanla azaltacak. Yan ürün:
  `data/ohlcv/bist/` önbelleği 11'den 48 sembole çıkarıldı (bkz. aşağıdaki "Veri
  önbelleği genişletildi" notu) — bu GİT'E EKLENMEDİ (parquet, `.gitignore` kapsamında
  kalmalı, yalnızca lokal).
- **Veri önbelleği genişletildi + gerçek bir yfinance veri kalitesi hatası bulundu
  (2026-08-29).** Yukarıdaki pencere taraması için `data/ohlcv/bist/` 11 semboldan
  48'e çıkarıldı (`Store.update()` doğrudan çağrılarak, `tlab update-data` CLI'sinin
  aynı alt katmanı). Süreçte GERÇEK bir geçici veri sorunu bulundu: en güncel barın
  (dünün kapanışı) yfinance'ta `Close`/`Adj Close` alanı bazen NaN geliyor (Open/High/
  Low/Volume dolu) — Yahoo'nun kapanış fiyatını geç yayınlaması. `validate_ohlcv` bunu
  doğru şekilde reddediyor (kod hatası DEĞİL, doğru davranış); çözüm `Store.update()`'e
  `end` parametresi bir gün geriden verilerek yapıldı. Ayrıca AKSA ve ULKER için gerçek
  OHLC tutarsızlığı (`high >= max(open,close)` / `low <= min(open,close)` ihlali, tek
  bir barda) bulundu ve validasyon tarafından doğru şekilde reddedildi — bu iki sembol
  önbelleğe alınamadı, zorlanmadı.
- **Faz 2-EK — kalan özellikler + W1 zaman dilimi** (2026-08-29): TAMAMLANDI. Önceki
  oturum yalnızca Faz 8A'nın ihtiyacı kadarını (`volatility.bollinger`,
  `channels.regression_channel`) yazmıştı; bu oturumda master prompt'un 14. bölümündeki
  KALAN tüm parçalar tamamlandı — Faz 8B/8C/8D artık bloklanmıyor.
  1. **W1 haftalık zaman dilimi** — `Timeframe.W1` eklendi (`core/types.py`).
     `data/resample.py::resample_to_w1(df_1d, market, now=None, drop_open=True)`:
     hafta Pazartesi başlar, kapanış Cuma (tatilse `_last_trading_day_of_week` ile geriye
     tarayarak haftanın SON işlem gününe kayar — ör. 2026-03-20 Cuma Ramazan Bayramı
     tatiliyse hafta 19'da/arifede, yarım gün kapanışı 12:40'ta kapanmış sayılır); açık
     hafta `resample_to_4h` ile AYNI `is_closed` deseniyle varsayılan olarak düşer.
     `Store.update()` artık D1 güncellenince W1'i de otomatik türetiyor (H1→H4 türetimiyle
     birebir aynı desen). 5 yeni test (`test_resample.py`) + 1 (`test_store.py`).
  2. **`features/volatility.py`** — `realized_vol(close,n,annualize)` (log-getiri
     std'sinin rolling'i, varsayılan √252 yıllıklaştırma), `keltner(df,n,atr_period,k)`
     (EMA orta + ATR bantları), `vol_zscore(close,vol_window,zscore_window)` (realized_vol
     'un kendi rolling z-skoru — iki pencereli). `atr`/`bollinger` zaten vardı, dokunulmadı.
     11 yeni test.
  3. **`features/channels.py`** — `frozen_channel_at(df,t,n,k)`: regression_channel'ın t
     barındaki OLS fit'ini [t-n+1,t] uçlu iki noktalı bir çizgiye dondurur (Faz 8C
     weekly_channel'ın "sinyal barında donmuş kanal çizgisi" ihtiyacı için — t1 ucu
     regression_channel(df,n,k)'nin t'deki değeriyle BİREBİR eşleşecek şekilde
     doğrulandı). `pivot_channel(df,pivots,tol_atr,confirm_bars,atr_period,max_channels)`:
     iki onaylı swing low'dan alt çizgi + p1..p2 aralığındaki en yüksek high'a teğet
     paralel üst çizgi — `trendlines.build_trendlines` ile AYNI "aday havuzu + extend-only
     touches/broken_at" mimarisi, ofset created_idx'te SABİTLENİR. `pivot_channel_series`
     (Channel'ı mid/upper/lower pd.Series'e çevirir) + `channel_position(df,channel)`
     (0..1 kanal-içi konum, regression VE pivot kanalıyla AYNI arayüzle çalışır). 17 yeni
     test (trendlines.py testleriyle aynı elle-inşa senaryo deseni: dokunuş/kırılım/
     prefix-tutarlılık).
  4. **`features/patterns_geom.py`** (YENİ) — `converging_lines(upper,lower)`: iki
     Trendline'ın slope_ratio'su, apex (kesişim) noktası, yakınsama testi (gap
     created_idx'ten itibaren daralıyor VE apex ileride mi). `classify(conv,params,
     pole_range=None)`: 7 tür — falling_wedge/rising_wedge/sym_triangle/asc_triangle/
     desc_triangle/flag/pennant. **TASARIM KARARI**: flag/pennant saf geometriden
     (slope işaretleri + yakınsama) türetilemez — ikisi de "önceki keskin harekete (pole)
     göre KÜÇÜK konsolidasyon" gerektirir; bu yüzden `classify()` opsiyonel bir
     `pole_range` alır, yalnızca verilip desen küçükse sym_triangle→pennant,
     neredeyse-paralel-yakınsamayan→flag döner — pole_range yoksa bu ikisi hiç dönmez.
     18 yeni test.
  5. **`features/hs_pattern.py`** (YENİ) — `find_hs(pivots,kind,sym_tol,neck_slope_max)`:
     zaten alternatif bir zigzag üzerinde 5'li ardışık pencere (`l1,h1,head,h2,l3`) —
     TOBO (dip: low,high,low,high,low, head en düşük) / OBO (tepe: tersi, head en
     yüksek). Boyun h1↔h2 arasından geçer (~yatay şartı `neck_slope_max`, ortalama
     fiyata göre normalize), omuz simetrisi `sym_tol` baş derinliğine göre GÖRELİ.
     `created_idx = l3.confirmed_idx` (sağ omuz onay barı — non-repaint). `target`
     klasik ölçülü-hareket projeksiyonu. 10 yeni test + hypothesis subset özelliği
     (kesik pivot listesiyle bulunan paternler ⊆ tam listeyle bulunanlar).
  6. **`features/zones_sd.py`** (YENİ) — `find_bases(df,base_max,base_atr,atr_period)`:
     dar konsolidasyon adayları (üst üste binen uzunluklar bağımsız döner, seçim
     `make_sd_zones`'a bırakılır). `find_impulses(df,k,impulse_atr,atr_period)`: k barlık
     net hareket ATR'ye göre eşik üstünde VE en az k-1 bar aynı yönlü gövde. `make_sd_zones`:
     bir impulse, TAM olarak kendi t0_idx'inde biten bazlarla eşleşir (en uzun/olgun taban
     seçilir), bölge doğum barı `impulse.t1_idx`. `update_zones(zones,df,t)`: created_idx'ten
     t'ye kadar test(extend-only)/reaksiyon(ilk, bir kez)/kırılım(bir kez, öncelikli) —
     `ranges.py`/`zones.py` ile aynı mimari. `golden_zone(swing_start,swing_end,lo,hi)`:
     `fibonacci.retracement`'ın doğrudan kullanımı (yön ne olursa olsun simetrik) —
     **TASARIM NOTU**: master spec parametreleri `swing_low/swing_high` diye adlandırmıştı,
     burada `swing_start/swing_end`'e yeniden adlandırıldı çünkü "low/high" isimleri
     yalnızca yükseliş senaryosunda doğru anlam taşıyor (davranış AYNI, yalnızca isim
     netliği). 16 yeni test + hypothesis subset özelliği (make_sd_zones).
  7. **`features/xsec.py`** (YENİ) — `rolling_alpha_beta(returns_i,returns_m,window)`:
     trailing OLS (channels.regression_channel ile aynı "her t kendi penceresini fit
     eder" deseni), alpha/beta + alpha'nın t-istatistiği (klasik intercept SE formülü).
     `information_ratio`, `momentum_horizons(prices,horizons,skip)` (klasik "12-1", en
     güncel `skip` barı dışlar — yalnızca pozitif shift), `fip(returns,n)` (Frog-in-the-
     Pan tutarlılık ölçüsü), `rs_line(price,index)`, `rank_pct(dict[symbol,value])`
     (percentile rank, YÖN TERS ÇEVRİLDİ: en iyi performans = en KÜÇÜK rank_pct, Faz 8D'nin
     `rank_pct <= top_pct` filtre sözleşmesiyle uyumlu olsun diye). 16 yeni test.
  8. **Yan düzeltme**: `trendlines.py::Trendline.value_at`'in tip imzası `int`→`float`'a
     genişletildi (mypy hatası — `converging_lines`'ın apex_idx'i tam sayı olmak
     ZORUNDA değil, gerçek bir kesişim noktası).
  Doğrulama: 93 yeni test (224→317), `pytest -q -m "not network"` 317/317 yeşil,
  `ruff check tlab/ tests/` 18 hata (BASELINE İLE AYNI, ilgisiz önceden var olan satırlar
  — yeni dosyalarda SIFIR), `mypy tlab/` yeni dosyalarda temiz, `lint_lookahead` 2 uyarı
  (BASELINE İLE AYNI, ilgisiz — `kerkez_nenstar.py`/`relative_momentum.py`, bu görev
  onlara dokunmadı). GİT'E PUSH EDİLDİ (local `0f3cbb3` / gerçek repo `d5d272d`).
- **Faz 8C — golden zone, arz/talep, haftalık kanal** (2026-08-29): TAMAMLANDI.
  1. **`structure/golden_zone.py::GoldenZoneIndicator`** — en güncel onaylı swing'in
     (`swings.alternate_pivots`, `SwingFibABCD` ile AYNI "yalnızca finalized pivot"
     mimarisi — bu yüzden generic `Registry.register()`'a TEMİZ kaydolur, istisnaya
     GEREK YOK) 0.618-0.786 altın bölge bandı; bant A'nın (en güncel pivot)
     `finalized_idx`'inde doğar. **TASARIM KARARI**: spec'in "A onay barında"
     ifadesi `confirmed_idx` değil `finalized_idx` olarak yorumlandı (aksi halde
     A daha ekstrem bir pivotla iptal edilebileceği için bant sınırları
     SONRADAN değişirdi — gerçek bir repaint). Sinyaller: `golden_zone_touch`
     (bant içine giriş), `golden_zone_reaction` (bant üstüne dönüş mumu +
     `reaction_body_ratio` gövde şartı), `golden_zone_fail` (bant altına kapanış),
     `golden_zone_success` (swing high aşımı) — fail/success `done=True` ile o
     swing'in izlemesini kapatır. "Yeni swing onayı → eski bant end alır" kuralı
     Box/Level `end`'in bir SONRAKİ zigzag pivotunun (qualifying olsun olmasın)
     `finalized_idx`'ine sabitlenmesiyle uygulanır. 11 yeni test.
  2. **`structure/supply_demand.py::SupplyDemandIndicator`** — `zones_sd.py`'nin
     (find_bases/find_impulses/make_sd_zones/update_zones) ince sarmalayıcısı.
     Kalite = patlama gücü (impulse_strength/5.0'a kapatılır) × baz darlığı
     (yükseklik/(base_atr×ATR) oranının tersi) × tazelik (1.0/0.5) — üçü de
     0..1 olduğu için çarpım da 0..1 (normalizasyon sabitleri spec'te YOK,
     BreakoutParams'ın quality_score'undaki gibi makul varsayılanlarla
     belgeleniyor). Kırılan bölge (`flip=True`) TEK SEVİYELİ flip ile karşıt
     türe döner (bir flip bölgesi kendisi bir daha flip OLMAZ — spec'in
     zincirleme değil tek seferlik bir dönüşüm olarak yorumlandı). Yeni `sd_new`
     sinyali eklendi (spec'te YOKTU — bölgenin DOĞUŞ barını, `fresh=True` ile,
     ayrı bir olay olarak işaretler; `demand_taze` scan preset'inin "taze"
     filtresi için gerekli, çünkü `sd_test`/`sd_reaction`/`sd_broken` bir bölge
     zaten test EDİLDİKTEN sonra ateşlenir, tanım gereği artık fresh=False'tur).
     **BİLİNEN SINIRLAMA**: `make_sd_zones`'un `max_zones` kesmesi bir "aday
     havuzu" (`PriceStructure`/`MultiBreakout` ile AYNI istisna,
     `register_verified_elsewhere`) — bölgelerin KENDİ sınırları değişmez,
     yalnızca "top-12'de mi" sorusu zamanla değişebilir. 12 yeni test.
  3. **`trend/weekly_channel.py::ChannelIndicator`** — `method='regression'`
     (varsayılan, `channels.regression_channel`) veya `'pivot'`
     (`channels.pivot_channel`); `Timeframe.W1` VE `1D` destekler. Dokunuş/
     kırılım sayaçları (`bottom_touches`/`top_touches`) sırayla biriktirilir,
     `min_prev_touches` kadar dokunuş birikmeden sinyal ateşlenmez; `rsi_max`
     yalnızca dip dokunuşuna uygulanır (spec'in "kanal dibi" odağı — tepe
     dokunuşu RSI'dan bağımsız). **GERÇEK HATA bulundu ve düzeltildi**: ilk
     taslakta `channel_break_up`→"short"/`channel_break_down`→"long" (TERS)
     yazılmıştı — `trend.breakouts`'un KENDİ `channel_break_up/down` yön
     sözleşmesiyle (up→long, down→short) karşılaştırılıp düzeltildi.
     **BİLİNEN SINIRLAMA**: spec'in açıkça istediği "güncel kanal ayrı Line
     olarak" öğesi (`style="channel_current"`) KASITLI OLARAK her `compute()`
     çağrısında en son bara göre KAYAN bir overlay'dir — generic `repaint_test`
     bunu "aynı label, farklı points" mismatch sanır (gerçek bir repaint hatası
     DEĞİL). Bu yüzden `register_verified_elsewhere` kullanılır;
     `channel_frozen_*` çizgilerinin (geçmiş bir sinyal barında dondurulmuş,
     BİR DAHA DEĞİŞMEYEN) gerçek non-repaint'liği hedefli testlerle doğrulanır.
     12 yeni test.
  4. **CLI/scan altyapısı**: `tlab/cli.py::scan_cmd`'nin `tf_map`'ine `"w1"`
     eklendi (`tlab scan --preset kanal_dibi_hafta --tf w1` artık çalışıyor);
     `tlab/viz/live.py`'nin `_TF_MAP`'ine de aynı şekilde (`tlab plot --tf w1`).
     `_signal_passes_filter` GENELLEŞTİRİLDİ — eskiden yalnızca `break_types`
     vardı, şimdi `events`/`zone_kind`/`fresh` de destekleniyor (herhangi bir
     indikatörün payload'ıyla çalışır). `config/scans.yaml`'a 3 yeni preset:
     `golden_zone`, `demand_taze`, `kanal_dibi_hafta`. 8 yeni test
     (`tests/test_cli_scan_filter.py`, ilk kez bu dosyalar test edildi).
  5. **`tlab/indicators/bootstrap.py`**: 3 yeni katalog girdisi eklendi
     (`structure.golden_zone` generic register, `structure.supply_demand`/
     `trend.weekly_channel` `register_verified_elsewhere`).
  6. **`tlab/viz/themes.py`/`labels_tr.py`**: yeni stiller için renk/etiket
     eşlemeleri (`golden_zone`→accent altın, `golden_zone_alt`→yellow,
     `demand`→green, `supply`→red, `*_broken`→gray, `channel`→blue,
     `channel_current`→accent, `channel_frozen`→muted) — `renderer.py`'ye
     HİÇBİR kod değişikliği GEREKMEDİ (mevcut Box/Line/series_layout
     primitifleri zaten yeterliydi, bu tasarım kararının doğruluğunu
     GERÇEK veriyle render ederek doğruladı, bkz. aşağıdaki kabul testi).
  Kabul testi (gerçek TCELL verisiyle, yfinance): D1 2023-01-02→2026-08-27
  (914 bar) ve ondan türetilen W1 (191 bar) üzerinde üç indikatör de
  hatasız çalıştırıldı; TCELL `structure.golden_zone`, `structure.
  supply_demand`, `trend.weekly_channel` (W1) grafikleri `outputs/samples/`e
  render edildi (kaleido, PNG) ve gözle incelendi — altın bant/swing çizgisi/
  BAŞARILI-BAŞARISIZ-REAKSİYON etiketleri, yeşil/kırmızı/gri arz-talep
  kutuları, güncel-kanal(altın)/dondurulmuş-kanal(soluk gri) ayrımı VE alt
  panel osilatörü hepsi doğru görünüyor. **DÜRÜST NOT**: `tlab update-data`/
  `Store.update()` H1 fetch'i bu oturumda `yfinance`'ın "start date cannot be
  after end date" hatasına takıldı (provider/store katmanına, bu göreve
  AİT DEĞİL bir ortam/API tuhaflığı) — kabul testi bu yüzden Store'u
  bypass edip `YFinanceProvider.fetch()` + `resample_to_w1`'i DOĞRUDAN
  çağırarak yapıldı; `tlab scan --preset kanal_dibi_hafta --tf w1` komutunun
  uçtan uca (Store/engine üzerinden) gerçek bir evren taraması HENÜZ
  YAPILMADI — bu H1 fetch sorunu çözülünce (ayrı, ilgisiz bir takip işi)
  denenmeli. `pytest -q -m "not network"` 360/360 yeşil, `ruff check tlab/
  tests/` 18 hata (BASELINE İLE AYNI), `mypy tlab/` yeni dosyalarda temiz,
  `lint_lookahead` 2 uyarı (BASELINE İLE AYNI). GİT'E PUSH EDİLDİ (local
  `76225dc` / gerçek repo `b32a01d`).
- **Görselleştirme düzeltmesi — `trend.weekly_channel` "curcuna"sı (2026-08-30,
  Faz 8C'nin örnek grafiklerini kullanıcıyla birlikte gözden geçirirken
  bulundu):** TAMAMLANDI. `outputs/samples/tcell_weekly_channel.png` (1D,
  n=52) ve W1 karşılığı incelenirken görüldü: dar `n` penceresiyle çok-yıllık
  veride HER dip/tepe dokunuşu VE her kırılım kendi `channel_frozen` çizgi
  çiftini (alt+üst) üretiyordu — onlarca üst üste binen gri çizgi grafiği
  okunaksız kılıyordu. `_latest_per_group` (mevcut declutter mekanizması)
  bu stili yalnızca ETİKET düzeyinde kısıtlıyordu (harmonik/trendline
  stillerinde işe yarayan varsayım — "şekiller örtüşür, sadece metin
  gürültü yapar" — burada GEÇERSİZDİ, çünkü her frozen kanal FARKLI bir
  fiyat/eğimde). Düzeltme `tlab/viz/renderer.py`'ye yeni `_cap_frozen_
  channels()` — harmonik marker'ların `_MAX_HARMONIC_MARKERS` ile aynı
  kategoriden bir çözüm, ama ŞEKİL düzeyinde (yalnızca etiket değil):
  `declutter=True` iken `channel_frozen` stilindeki çizgiler sinyal barının
  zamanına göre sıralanıp yalnızca EN GÜNCEL `_MAX_FROZEN_CHANNELS=2` çifti
  tutulur, gerisi TAMAMEN elenir (diğer stiller etkilenmez). İndikatörün
  KENDİSİ (`weekly_channel.py`, sinyal/state hesabı) DOKUNULMADI — saf bir
  render/declutter düzeltmesi. 1 yeni hedefli test (`test_cap_frozen_
  channels_keeps_only_most_recent_pairs`, sentetik Line'larla — gerçek
  veriye gerek yok). `outputs/samples/tcell_weekly_channel.png` yeniden
  üretildi ve gözle karşılaştırıldı (öncesi: ~15+ örtüşen çizgi; sonrası: 2
  dondurulmuş + 1 güncel kanal, net). `pytest -q -m "not network"` 361/361
  yeşil, `ruff check` temiz, `mypy` bu dosyada yeni hata yok (mevcut
  1344. satırdaki BASELINE hatası ilgisiz). GİT'E PUSH EDİLDİ (bkz. commit
  hash'leri için `git log`).
- **Görselleştirme düzeltmesi — `structure.price_structure` etiket çakışması
  (2026-08-30, kullanıcı Faz8B onayı sonrası TCELL/THYAO/ASELS örneklerini
  gözden geçirirken bulundu, "aracı kurum raporu" kalitesine göre hâlâ
  karışık/bozuk olarak nitelendirdi):** TAMAMLANDI, GERÇEK bir mimari
  hata. Belirti: VAH/POC/Direnç Bölgesi/Destek Bölgesi/Direnç-Destek
  (Temas:N) etiketleri aynı "confluence" bölgesinde (destek/direnç/
  konsolidasyon/POC hep aynı gerçek seviyeyi temsil ettiği için fiyatça
  yakın olmaları BEKLENEN bir durum) üst üste binip harfler birbirine
  karışıyordu — TCELL'e özgü değildi, THYAO/ASELS'te de AYNI şekilde
  üretilebildi (bkz. ilgili görev/oturum notları). Kök neden: Box/Level
  etiketleri TEK bir birleşik "merdivende" (`_stagger_yshifts`, hep yukarı
  büyür) fanlanırken, trendline UZATMA etiketleri (`_draw_lines`) TAMAMEN
  AYRI, habersiz bir merdivende (hep aşağı büyür) hesaplanıyordu — iki
  merdivenin birbirinin "şeridine düşmeyeceği" varsayımı YANLIŞTI, çünkü
  bir direnç/destek ÇİZGİSİ projeksiyonu tanım gereği aynı direnç/destek
  BÖLGESİ'yle aynı fiyat civarında biter. Düzeltme (1. adım): `_stagger_
  yshifts` artık HER üç kaynağı (box/level/line-uzatma) TEK birleşik listede
  alır, her öğe KENDİ taban ofsetini (`+10` box/level, `-24` line) taşır;
  `_draw_lines` kendi ayrı merdivenini kurmak yerine `render()`'dan gelen
  PAYLAŞILAN sözlüğü kullanır (yeni `_line_extensions()` yardımcı fonksiyonu
  ile uzatma geometrisi TEK yerde hesaplanıp hem stagger listesine hem
  gerçek çizime beslenir — önceden iki kez hesaplanıyordu). **2. GERÇEK hata
  (1. düzeltme sırasında bulundu)**: `_stagger_yshifts` öğeleri SALT `price`e
  göre sıralıyordu — bu yalnızca TÜM öğeler AYNI işaretli taban taşıdığında
  ekran-konumu sırasıyla örtüşür; negatif tabanlı bir line-uzatma öğesi, raw
  price'ı daha BÜYÜK olsa bile n=0 ekran konumu daha KÜÇÜK olabiliyordu —
  bu da bitişik-öncekiyle-kıyasla kontrolünü YANLIŞ komşu çiftine
  uyguluyordu (gerçek çakışan çift hiç karşılaştırılmıyordu). ASELS gerçek
  verisiyle doğrulandı: VAL(341.88)/Destek-uzatma(344.5)/Destek-Bölgesi
  (347.63) üçlüsü ilk düzeltmeden SONRA bile üst üste biniyordu; sıralama
  anahtarı `price`den `price + base/px_per_unit` (n=0 ekran konumu) olarak
  değiştirilince düzeldi. Yeni regresyon testi (`test_stagger_yshifts_
  separates_mixed_direction_items_by_all_pairs`) hem YENİ kodun TÜM ikili
  mesafeleri karşıladığını hem de ESKİ (salt-price) sıralamanın AYNI
  senaryoda gerçekten başarısız olduğunu (elle doğrulanmış gerçekçi
  `px_per_unit≈1.55` ile) kanıtlıyor — sentetik ama ASELS'in gerçek
  sayılarından türetildi. **DÜRÜST NOT — kalan sınırlama**: algoritma hâlâ
  "tek geçişli açgözlü sezgi" (genel bir yerleşim çözücü değil); teorik
  olarak SIRALI işlenen bir NEGATİF-tabanlı öğe, kendisinden ÖNCE gelen
  pozitif-tabanlı bir öğeden ayrılmak için `n` artırıldığında YANLIŞ yöne
  (o öğeye doğru) kayabilir — bu, üç kategori de ayrı yönlerde büyürken
  nadir/uç bir sıralama durumunda hâlâ teorik bir artık risktir, gerçek
  veride şimdiye dek gözlenmedi, bulunursa aynı iteratif düzeltme deseniyle
  ele alınacak. `structure.swing_fib_abcd`/harmonik grafikler AYNI çizim
  yolunu (`_draw_boxes`/`_draw_levels`/`_draw_lines`) paylaştığı için bu
  düzeltmeden dolaylı olarak faydalanır (ayrıca test edilmedi, kod yolu
  ortak). `pytest -q -m "not network"` 362/362 yeşil (1 yeni test), `ruff
  check` temiz. `outputs/samples/{tcell,thyao,asels}_price_structure.png`
  yeniden üretildi, gözle karşılaştırıldı — üçünde de eski illegible
  üst-üste-binen metin artık ayrı okunur satırlara ayrıldı (ASELS'teki en
  yoğun 3'lü küme dahil); TCELL'in "Konsolidasyon" etiketi kırmızı
  trendline'ın GEÇTİĞİ pikselle görsel olarak kesişmeye devam ediyor (bu
  metin-metin çakışması DEĞİL, metin-çizgi kesişimi — AYRI, çözülmemiş bir
  görsel kusur, bilerek not edildi). **Görselleştirme genel değerlendirmesi
  hâlâ AÇIK**: kullanıcı `images/` klasöründeki referans ekran görüntülerini
  (aracı-kurum-tarzı hacim profili HVN vurgusu, RSI paneli, harmonik
  formasyonlarda dolgulu üçgen + swing HH/HL/LH/LL katmanı + renkli fib
  merdiveni) mevcut `outputs/samples/` çıktılarından BELİRGİN ÖLÇÜDE daha
  iyi buldu — bunlar TASARIM eksiklikleri (bug değil), henüz ELE ALINMADI,
  kullanıcıdan öncelik sırası bekleniyor.
  **Sırada**: kullanıcının görselleştirme önceliklendirmesi → sonra Faz 8B
  (wedge/head_shoulders/flag_pennant/double_top_bottom/broadening — artık
  `patterns_geom.py`/`hs_pattern.py` hazır) → Faz 8D (artık `xsec.py` hazır)
  → K3 → Faz 8E → Faz 10 → Faz 9.

Toplam 362 test yeşil (`pytest -q`, varsayılan olarak `-m "not network"` uygular),
ruff/mypy/lint_lookahead temiz (yeni kod kapsamında — repo genelindeki 18 ruff/2
lint_lookahead uyarısı önceden var olan, ilgisiz satırlardır).

## Repo Yapısı / Modül Haritası

```
tlab/
  core/          types.py (Signal/IndicatorResult/...), indicator.py (BaseIndicator/Registry), params.py
  data/          providers/, calendar.py, resample.py, store.py, validate.py, universe.py, settings.py
  features/      swings.py, fibonacci.py, trendlines.py, ranges.py, zones.py,
                 volume_profile.py, stats.py, ma.py, oscillators.py, volatility.py
  indicators/
    harmonics/   geometry.py, prz.py, state.py, scanner_indicator.py, schools/ (8 ekol)
    momentum/, pairs/, structure/, trend/   (henüz boş — gelecek fazlar)
  testing/       repaint.py, lint_lookahead.py, fixtures.py
  scanner/, viz/, backtest/   (henüz boş — gelecek fazlar)
  cli.py
config/          settings.yaml, holidays_tr.yaml, universe_bist.txt
tests/           her tlab/ modülüne karşılık gelen test dosyaları + test_harmonics/
```

## Harmonik Formasyon Tarayıcı (Faz 3 — TAMAMLANDI)

`tlab/indicators/harmonics/` — ortak geometri + PRZ + durum makinesi + 8 izole ekol.

**Mimari:**
- `geometry.py::generate_candidates(df, zigzag)` — kesinleşmiş zigzag'den ardışık 4'lü
  (X,A,B,C) pencereler + opsiyonel öncü `0` noktası (shark/five_zero/three_drives için).
  Aday, C pivotu KESİNLEŞTİĞİ barda doğar (`born_idx = c.finalized_idx`). Her aday
  `ab_xa`, `bc_ab` oranlarını ve `c_beyond_a`/`b_beyond_x` bayraklarını taşır.
- `prz.py::compute_prz` — PRZ'yi `fibonacci.extension()` üzerine kurulu tek bir bacak
  soyutlamasıyla (`_leg_price`) hesaplar: `intersection` (birden fazla bacağın kesişimi)
  veya `single_pm_tol` (tek bacak ± tolerans). D noktası, gerçekleşmeden ÖNCE bile X,A,B,C'den
  tamamen deterministik hesaplanabilir — bu yüzden "D (hedef)" çizgisi/level'ı candidate
  doğar doğmaz çizilir.
- `state.py::track_pattern` — PENDING → ACTIVE → CONFIRMED/INVALIDATED/EXPIRED durum
  makinesi. 4 `confirmation_policy`: `close_reversal`, `xb_break`, `pivot`, `school`.
  `require_extra_bar_on_warning`: CD-bacağı uyarı sinyalleri (gap/geniş bar) varsa +1 bar
  bekler (Ch.11 "warning signs" tekniği).
- `schools/base.py::PatternSpec` — her formasyonun oran aralıkları + `invalidation`
  (bacak_kodu, oran) — kendi D hedefinden BİR SONRAKİ standart orana göre hesaplanır (düz
  yüzde değil).
- `scanner_indicator.py::HarmonicIndicator(school, params)` — 8 ekolün ortak sarmalayıcısı,
  `harmonic.{school}` adıyla çalışır.

**8 Ekol** (`schools/`): `carney.py` (Gartley/Bat/Crab/Deep Crab/Butterfly/Shark, tol ±0.03,
intersection), `pesavento.py` (Gartley/Butterfly, tol ±0.05, single_pm_tol + AB=CD simetrisi
zorunlu), `gilmore.py` (Pesavento oranları + zaman oranı şartı, `time_window`),
`oglesbee_cypher.py` (C, A'yı aşar), `kerkez_nenstar.py` (C, A'yı aşar + EMA/MACD ek teyidi),
`beck_navarro200.py` (D = %200 XA), `five_zero.py` (6 noktalı, D = BC'nin %50'si),
`three_drives.py` (impulsif devam — `b_beyond_x_required=True`, kitaptan tam kural seti
çıkarılarak eklendi, 8. ekol).

**K1-D — pesavento.py TWYS ile hizalandı (2026-08-28):** `bilgi-bankasi/teknik/
10_pesavento_twys.md` (K1 çıkarımı) sonundaki karşılaştırma tablosundaki 3 FARKLI satır
düzeltildi: (1) `_AB_CD_RATIOS`'a **2.0** eklendi (ORAN-02: CD/AB simetrisi 1.0 veya
1.27-2.00+); (2) Butterfly `xab` (AB oranı) `(0.786±0.05)` dar bandından
`(0.332, 0.936)`'ya genişletildi (ORAN-05: kabul edilen küme {.382,.50,.618,.786});
(3) Butterfly `d_components`/`invalidation` `(1.27,1.618)`'den `(1.27,2.618)`'e genişledi
(ORAN-06: D hedefi 1.272/1.618/2.00/2.618, yalnızca 2.618 ötesi geçersiz — eskiden kod
gerçek Butterfly adaylarını 1.618'de false-negative olarak eliyordu). Ek: `HarmonicSchool`
base'e `suggested_levels()` hook'u eklendi (varsayılan `None`, ekoller override edebilir);
Pesavento Gartley/Butterfly için `Signal.payload`'a `suggested_entry`/`suggested_stop`/
`entry_note` alanları ekliyor (TWYS'teki giriş/stop tavsiyesi — yalnızca hesaplanabilir
kısım, "shaded" ince ayar/sabit-dolar stop gibi enstrüman-özel kısımlar `entry_note`
metninde PSK niteliğinde bırakıldı). `gilmore.py` BİLİNÇLİ OLARAK güncellenmedi — Gilmore
ayrı bir ekol (kendi sabitleri var, "ekoller birbirini import etmez"), hâlâ eski
(1.27,1.618) bandını kullanıyor; ileride ayrıca gözden geçirilebilir. 3 yeni test eklendi
(`tests/test_harmonics/test_schools.py`) — toplam test sayısı 153→156.

**Kaynak (Faz 3 kod yazılırken kullanıldı, telife dikkat):** Larry Pesavento & Leslie
Jouflas, *Trade What You See* — kullanıcının yerel/yasal kopyasından hedefli kural çıkarımı
yapıldı (metin/görsel reprodüksiyonu YOK, yalnızca oran/yapı kuralları kendi cümlelerimizle).
Kitap yalnızca AB=CD/Gartley/Butterfly/Three Drives'ı kapsıyor — Bat/Crab/Shark (Carney),
Cypher (Oglesbee), 5-0 (Duddella) farklı yazarlara ait, bu yüzden "ekoller birbirini import
etmez" mimari kararı bilinçli.

**Bilinen sınırlama:** `repaint_test`'in Line/Polygon diffing'i "var olma" kanıtı olarak
`points[0][0]`'ı (ör. X'in bar_time'ı) kullanır, oysa gerçek oluşum `candidate.born_idx`'te
(C kesinleştiğinde, X'ten çok sonra). Bu GERÇEK bir repaint hatası değil — trendlines.py/
zones.py'de de aynı desen var. Çözüm: testlerde `cut_points` yalnızca adayın doğduğu bardan
itibaren seçilir (bkz. `tests/test_harmonics/test_harmonics_repaint.py`). Signal nesneleri bu
sorundan etkilenmez (`detected_at` zaten doğru bar'ı taşır, tüm cut aralığında test edildi).

## Yapı İndikatörleri (Faz 4 — TAMAMLANDI)

`tlab/indicators/structure/` — iki bağımsız indikatör, `tlab/features/`'ı sarmalar,
kendi hesabı neredeyse yok.

**`swing_fib_abcd.py::SwingFibABCD`** — swing yapısı (HH/HL/LH/LL) + AB=CD hedef
projeksiyonu + Fibonacci retracement/extension. AB=CD burada **X'siz, 3 noktalı**
(A,B,C→D) — bu, harmonik motorun XABC'sinden farklı, kitaptaki (bilgi-bankasi/teknik/
10/FORMASYON-01) yapıyla birebir örtüşür. Durum makinesi: PENDING (C finalize) → ACTIVE
("yaklaşıyor", `near_pct`) → COMPLETED (hedefe `target_tol_atr*ATR` içinde) veya
INVALIDATED (yeni bir ABC üçlüsü doğunca — fiyat aşımı burada AYRI bir geçersizlik
nedeni DEĞİL, harmonik motordaki overshoot mantığı kapsam dışı). Her üçlü için
`abcd_ratios`'taki HER oran (max_active_targets'a kadar) ayrı bir hedef/sinyal zinciri
üretir; `harmonic_unit=|A-B|` payload'a yazılır.

**`price_structure.py::PriceStructure`** — trendlines + ranges + zones (destek/direnç,
kind'e göre iki ayrı çağrı: sarı direnç/mavi destek) + hacim profili + hacim/MACD
serileri. **BİLİNEN SINIRLAMA (kod DOĞRU, ama iki parça generic `repaint_test`/
`Registry.register()` kapsamı dışında — modülün kendi docstring'inde detaylı):**
1. Trendline Line/Signal'leri — `build_trendlines`'ın KENDİ docstring'inde zaten
   belgelenen "aday havuzu" deseni (df büyüdükçe hangi (p1,p2) çiftinin öne çıkacağı
   değişebilir); `Line.label`'daki "(Temas:N)" ve breakout sinyalinin `touches`
   payload'ı bu yüzden generic tüm-IndicatorResult repaint_test'i YANLIŞ ALARM olarak
   tetikler.
2. POC/VAH/VAL Level'leri — hacim profili `df.iloc[-window_bars:]` (dizinin SONUNA göre
   kayan pencere) kullanır; bu yüzden CANLI/GÜNCEL bir gösterge, kalıcı tarihsel kayıt
   DEĞİL. `poc_reclaim` bu yüzden Signal DEĞİL, `last_state["poc_reclaimed_last_bar"]`
   (yalnızca "şu an" bilgisi).
   
   Sonuç: `PriceStructure`, `Registry.register()`'a KAYDOLMAZ (arayüz uyumluluğu ayrıca
   doğrulanır); gerçekten non-repaint olan parçalar (range/zone kutuları+sinyalleri,
   macd/volume serileri) `tests/test_structure/test_price_structure.py`'de HEDEFLİ
   testlerle (extend-only + doğum barı + prefix-tutarlılık) doğrulanır.
   `SwingFibABCD` bu sorunu YAŞAMAZ (AB=CD hedefleri/fib seviyeleri finalize olduktan
   sonra bir daha büyüyen bir sayaç taşımaz) ve `Registry.register()`'a temiz kaydolur.

`vp_bins`/`vp_volumes`/`vp_gauss` series'leri FİYAT bin'leriyle indexlenir (zaman
DEĞİL) — renderer (Faz 7) bunları sağ panelde ayrı bir yatay histogram çizmeli.

## Pair Trading (Faz 5 — TAMAMLANDI)

`tlab/indicators/pairs/relative_momentum.py::RelativeMomentumPair` — long-only rölatif
momentum geçişi. **`context={"x": df_x}` alan İLK indikatör**: `df`=Y hissesi,
`context["x"]`=X hissesi. `spread = log(Y) − β·log(X)` (β: `rolling_ols` veya `one` —
tek seferlik, ilk `beta_window` bardan sabitlenmiş), `z = zscore(spread, window)` (hepsi
Faz 2'nin `tlab/features/stats.py`'sinden — bu modül tam bu amaçla, henüz kullanılmadan
yazılmıştı). Sinyal **dönüş onaylıdır**: eşiği ilk aşan bar değil, eşiğin İÇİNE geri
dönen bar (`z[t-1]<-k, z[t]>=-k` → "Y AL"). Durum: `holding` serisi (1.0=Y, 0.0=X, NaN=
henüz sinyal yok); geçiş barında `pairs_engine.py::run_pair_backtest` tüm sermayeyi
komisyonla diğer tarafa taşır.

**Mimari genişletme — `context` artık gerçekten kullanılıyor:**
- `tlab/testing/repaint.py::repaint_test` yeni `context` parametresi aldı: verilirse
  içindeki her DataFrame, `df` ile AYNI `cut_time`'da (TARİHE göre, pozisyona göre DEĞİL —
  iki serinin bar sayısı farklı olabilir) kesilir. Aksi halde context tam bırakılıp
  yalnızca `df` kesilseydi, indikatör context'teki GELECEK barları görebilirdi.
- `Registry.register()` yeni opsiyonel `sample_context` parametresi aldı (aynı sebeple).
- **Ama `RelativeMomentumPair`'in KENDİSİ bu genişlemeye muhtaç değil** — X verisini HER
  ZAMAN önce `df.index` (Y) ile inner-join edip (`common_idx`) SONRA kullanıyor, bu yüzden
  context'i kesmemek bu indikatörde fiilen fark yaratmıyor (test edilip doğrulandı, bkz.
  `test_uncut_context_gives_identical_result_here_by_construction`). Genişletme yine de
  GENEL bir güvenlik ağıdır — bu deseni takip etmeyecek gelecekteki context'li
  indikatörler için.

**Discovery (`discovery.py::discover_pairs`) — indikatör DEĞİL, statik bir tarama:**
corr + ADF eşbütünleşme + halflife eşiklerinden geçen çiftleri raporlar. Sektör filtresi
`config/sectors_bist.yaml`'dan (KASITLI OLARAK küçük/kısmi — yalnızca emin olunan ~25
sembol, "bilmediğin sektörü uydurma" ilkesi) `load_sector_map()` ile okunur; bir sembol
haritada yoksa `same_sector_only=True` iken otomatik dışlanır. **Bulgu:** Engle-Granger
regresyonu YÖN-BAĞIMLIDIR (Y~X ile X~Y sonlu örneklemde farklı ADF p-değeri verebilir) —
`discover_pairs` bu yüzden HER kombinasyon için iki yönü de dener, geçeni (ikisi de
geçerse daha düşük adf_p'liyi) raporlar.

**DISIPLIN-06/08 (bilgi-bankasi/teknik/kod/ch02_pairs_arbitraj.md, K2/STRAT-08):**
(1) discovery'nin çıktısı KALICI BİR ONAY DEĞİL, anlık bir tarama — çift seçimi ile
backtest AYNI pencereden yapılırsa seçim-lookahead oluşur, periyodik yeniden koşulmalı.
(2) β geçmişten, sinyal bugünden, işlem `execution` parametresine göre bugünün
kapanışından ya da yarının açılışından — üç zaman dilimi hiç karışmaz.

**Bilinmeyen/kapsam dışı bırakılanlar:** Tam Johansen/VECM (STRAT-10, çoklu-sembollü
kointegrasyon) — mevcut discovery yalnızca ikili Engle-Granger; ETF NAV arbitrajı
(STRAT-09) ve VIOP/opsiyon arbitrajı (ch3) — PARK, tlab'ın tek-sembol spot-veri
mimarisiyle uyuşmuyor. **648-sembol tam evren taraması henüz koşulmadı** — bu Faz 6'nın
(tarama motoru) doğal parçası olacak, şimdilik makine küçük örneklemde doğrulandı.

## Tarama Motoru (Faz 6 — TAMAMLANDI)

`tlab/scanner/` — üç modül: `results.py` (SQLite + JSON), `engine.py` (paralel tarama),
`eod.py` (gün sonu akışı). `tlab/indicators/bootstrap.py`, katalog + Registry köprüsü.

**`bootstrap.py::CATALOG`** — 11 indikatörün TEK doğru kaynağı (`tlab list-indicators`,
`tlab scan --indicators all`, `engine.run()` hepsi bunu kullanır). `populate_registry()`
her indikatörü ayrıca gerçek `Registry`'ye de kaydeder (repaint doğrulamasıyla — `harmonic.*`
ve `structure.swing_fib_abcd`/`pair.relative_momentum` için gerçek `repaint_test`,
`structure.price_structure` için Faz 4'ün belgelediği istisna yoluyla `register_verified_
elsewhere()`). **İKİ gerçek mimari sorun burada bulunup düzeltildi:**
1. `HarmonicIndicator`'ın `meta` niteliği yalnızca INSTANCE üzerinde (8 ekol tek sınıf
   paylaşıyor, `__init__`'te atanıyor) — `Registry.register()` eskiden bunu class-level
   bekliyordu. **Düzeltme:** `Registry.register()`/`register_verified_elsewhere()` artık
   SINIF değil ÖRNEK alıyor (`type(instance)` içeride saklanıyor, `get()` yine sınıf döner
   — geriye dönük uyumlu; mevcut çağıranlar — testler — örnek oluşturacak şekilde
   güncellendi).
2. `Registry.register()`'ın varsayılan `repaint_test` penceresi GERÇEK piyasa verisiyle
   (sürekli pivot aktivitesi) her zaman "aday havuzu" zamanlama sorununu (Faz 3/4'te
   belgelenen, GERÇEK bir repaint hatası OLMAYAN durum) tetikliyordu. **Düzeltme:**
   `bootstrap.py::_bootstrap_sample()` kısa gürültülü "kafa" + uzun DÜZ "kuyruk"lu sentetik
   veri üretir (aynı desen Faz 4/5'in registry testlerinde de kullanılmıştı).

**`results.py`** — SQLite şeması (`runs`/`signals`/`states`/`data_quality`) görev
metnindeki alan adlarıyla BİREBİR, DONUK (Bilanço Radar ile `symbol` join'i için).
`signals.pattern_id`: her indikatörün payload'ı farklı bir "hangi aday" anahtarı taşıdığı
için (`pattern_id`/`triple_id`/`event`) `_pattern_key()` bunları TEK alana normalize eder
— dokümante edilmiş, mükemmel olmayan bir uzlaşı (nadir çakışma = son yazan kazanır).
`diff(run_a, run_b)`: yeni sinyaller, durum geçişleri (chain=symbol+tf+indicator+
pattern_id bazında state kümesi karşılaştırması) VE **kaybolan sinyaller** — bu SIFIR
olmalı, olursa `has_repaint_alarm=True` ve `eod.py` bunu `logger.error` ile LOGLAR.

**`engine.run()`** — worker fonksiyonları (`_run_single_worker`/`_run_pair_worker`)
MODÜL SEVİYESİNDE (ProcessPoolExecutor picklable top-level çağrılabilir ister);
`IndicatorResult` süreçler arası HAM DATACLASS değil `to_json()` STRING'i olarak taşınır
(pandas Series pickling'e karşı en sağlam yol) — **bu tercih, aşağıdaki gerçek hatayı
ortaya çıkardı:**

**BULUNAN GERÇEK HATA — `IndicatorResult.from_json()`:** Hiçbir Faz 0-5 testi `to_json`/
`from_json` round-trip'ini hiç EGZERSİZ ETMEMİŞTİ (`repaint_test` Python nesnelerini
doğrudan karşılaştırır, JSON'a hiç uğramaz) — `structure.price_structure`'ın FİYAT-
indeksli `vp_bins`/`vp_volumes`/`vp_gauss` serileri (Faz 4 tasarımı, CLAUDE.md'de zaten
"zaman ekseni DEĞİL" diye işaretli) `from_json`'ın "her series zaman-indekslidir"
varsayımıyla çakışıp `pd.Timestamp("11.9366...")` gibi bir ValueError'a çarpıyordu. Bu,
`engine.py`'nin worker'ları GERÇEKTEN JSON round-trip yapana kadar (Faz 6'da, ilk kez)
YAKALANMADI. **Düzeltme:** `tlab/core/types.py::_series_from_json()` — bir series'in
index'ini önce Timestamp olarak ayrıştırmayı dener, başarısız olursa float index'e düşer.
5 yeni test (`tests/test_core_types.py`) — bu proje genelinde `IndicatorResult` JSON
round-trip'ini test eden İLK dosya.

**`eod.py::run_eod()`** — takvim kontrolü (tatil günü atla) → `Store.update()` (1H,1D;
4H türetilir) → veri kalitesi → `engine.run()` → `results.persist()` → `diff(önceki_run)`
→ JSON rapor (`outputs/reports/eod_{run_id}.json`) → `notify()` hook'u (boş fonksiyon,
Telegram sonra). Aynı gün ikinci koşu `force=False` iken `status: "skipped_existing"`
ile atlanır. Log: `outputs/logs/eod_{date}.log`.

**CLI:** `tlab scan|eod|signals|diff|list-indicators` (bkz. Komutlar). Zamanlama örnekleri
(cron/systemd timer/Windows Görev Zamanlayıcı) `README.md`'de.

**Performans notu:** `structure.price_structure` diğer indikatörlerden ~10-30× yavaş
(trendline aday üretimi O(n²) — tüm pivot çiftleri denenir). 100-sembol/2-TF/tüm-indikatör
taraması KÜÇÜK bir örneklemden (10 sembol) ekstrapole edildi (~6 dk, önbellekten okuma +
hesap — ilk indirme HARİÇ); gerçek tam-ölçek koşu ve olası `price_structure` optimizasyonu
(ör. `max_lines`'ı düşürmek veya aday üretimini erken kesmek) Faz 6 sonrası bir iyileştirme
adayı.

## Görselleştirme (Faz 7 — TAMAMLANDI)

`tlab/viz/` — `renderer.py` (HESAP YAPMAZ, yalnızca `IndicatorResult`
primitiflerini çizer), `themes.py` (`dark_terminal`/`light_analysis`, tüm
renkler tek yerden), `labels_tr.py` (Türkçe etiket sözlükleri), `table.py`
(Görsel 4 metrik tablosu), `report.py` (EOD HTML özet raporu + `ensure_chart()`
lazy grafik üretimi), `live.py` (CATALOG+Store+render ortak "sembolden canlı
grafiğe" kısayolu, `tlab plot` ve `report.py::ensure_chart` bunu paylaşır).

**`IndicatorResult.series_layout`** (yeni, opsiyonel alan, `core/types.py`):
`{panel_adı: [seri_adı, ...]}` — renderer'ın alt panelleri hangi serilerden
oluşturacağını belirtir (`structure.price_structure` şimdi `{"hacim":
["volume","volume_ma"], "macd": [...]}` döndürüyor). `vp_*` serileri bu
mekanizmaya DAHİL DEĞİL — fiyat-indeksli oldukları için ayrı, özel bir sağ
yan panele (hacim profili) gider.

**Faz 7'de gerçek veriyle render edilirken bulunup düzeltilen 3 GERÇEK hata**
(hiçbiri önceki fazlarda yakalanamazdı çünkü bu, projedeki İLK görsel/render
egzersiziydi):
1. **`themes.py::_FILL_STYLE_COLOR` ters eşleme** — `"bullish"` yeşil yerine
   kırmızıya, `"bearish"` kırmızı yerine yeşile haritalanıyordu (satır çizgisi
   rengiyle dolgu rengi ÇELİŞİYORDU — ör. yeşil çizgili bir boğa üçgeni kırmızı
   dolgulu görünüyordu). Düzeltildi.
2. **`add_vrect(row=...)` sessiz no-op'u** — Plotly (7.x), bir subplot'a İLK
   trace eklenmeden önce o satıra `add_shape`/`add_vrect` çağrılırsa şekli
   SESSİZCE hiç eklemiyor (hata fırlatmıyor). Pair modundaki tutulan-dönem
   gölgeleri (`_draw_holding_boxes`) bu yüzden hiç görünmüyordu — çağrı sırası,
   her satırın İLK trace'inden SONRAYA alınarak düzeltildi.
3. **Harmonik `xb` çizgisinin sınırsız eğim projeksiyonu** — `Line.extend_right`,
   kısa/dik bir bacağın (ör. birkaç barlık bir X→B) eğimini ham hâliyle
   grafiğin EN SON barına kadar projekte ediyordu; yıllarca eski/kısa bir
   harmonik aday için bu, fiyat eksenini gerçek dışı büyütüyordu (ör. 100
   TL'lik bir hisse için 700+ TL'lik bir projeksiyon). Düzeltme: uzatma artık
   bacağın KENDİ süresinin en fazla 3 katıyla sınırlı (`structure.price_
   structure`'ın uzun/yatık trendlerinde bu sınır zaten aşılmadığı için
   davranış değişmedi).

Ayrıca `structure.swing_fib_abcd`'de bir tasarım eksikliği bulunup düzeltildi:
D-hedef `Level`'leri hiçbir zaman `end` almıyordu (hep `None`) — bu yüzden
TAMAMLANMIŞ veya GEÇERSİZLEŞMİŞ eski hedefler bile grafiğin sonuna kadar
uzanıyor, gerçek çok-yıllık veride onlarca çakışan çizgi üst üste biniyordu.
Düzeltme: `end`, tamamlanma/geçersizleşme barına SABİTLENİYOR (ranges.py/
zones.py'deki `Box.t1` ile AYNI extend-only deseni — bkz. Faz 2/4 notları);
hâlâ açık (henüz sonraki üçlü doğmamış) bir hedef `end=None` kalır.

`fig.write_image()` (kaleido, `pyproject.toml`'a eklendi) ile PNG dışa aktarımı
`pd.Timestamp`/tz-aware `DatetimeIndex` içeren shape/annotation/trace x
değerlerinde çöküyordu (`fig.write_html`'in KENDİ JSON encoder'ı bunu
sorunsuz işlerken, kaleido'nun orjson tabanlı encoder'ı işlemiyor) —
`renderer.py::_x()`/`_xs()` ile TÜM x değerleri ISO8601 string'e çevrilerek
düzeltildi.

Kabul testi: TCELL `structure.price_structure`, TCELL `structure.
swing_fib_abcd`, ALARK `harmonic.pesavento`, TCELL/ISCTR `pair.
relative_momentum` gerçek veriyle render edildi, `outputs/samples/`'a PNG
olarak kaydedildi (kaleido). Referans-görsel öğe kontrol listesi (bazı
öğeler kasıtlı GAP) `README.md`'de.

**Declutter düzeltmesi (2026-08-28, kullanıcı geri bildirimiyle):** Kullanıcı
`outputs/samples/`'daki grafiklerin GERÇEK veriyle "curcuna" hâline geldiğini
bildirdi — onlarca eski/çözülmüş ABC üçlüsünün fib merdiveni, onlarca harmonik
adayın PRZ etiketi, onlarca trendline adayının "(Temas:N)" yazısı üst üste
binip neyin/nerede/nasıl bir sinyal olduğu ANLAŞILMAZ hâle geliyordu. Düzeltme
`renderer.py`'ye eklendi (`declutter: bool = True`, varsayılan AÇIK):
- `_declutter_levels()` — aynı `style`'daki Level'lar `start` bazında
  gruplanır, yalnızca EN GÜNCEL grup TUTULUR (fib merdiveni, harmonik PRZ,
  swing_fib_abcd D-hedefleri) — Level tek başına anlamsız olduğu için
  (hangi üçlüye ait olduğu bağlamı yoksa saf gürültü) TAMAMEN elenir.
- `_latest_per_group()` — Box (zone/range) ve Line (trendline/xb) için: ŞEKİL
  hep çizilir, yalnızca metin ETİKETİ o stilin EN GÜNCEL örneğine kısıtlanır.
- Harmonik Marker'lar (`D: fiyat [DURUM]` kutuları) en fazla son 3 ile
  sınırlandı.
`tlab plot`'un `--last-n` varsayılanı da 250'ye düşürüldü (`0`=tüm geçmiş);
`--show-all` ile eski (tam/gürültülü) davranışa dönülebilir. 3 yeni test
(219→222). Örnek PNG'ler yeniden üretildi ve kullanıcıya gönderildi.

## Çoklu Kırılım Tarayıcısı (Faz 8A — TAMAMLANDI)

`tlab/indicators/trend/breakouts.py::MultiBreakout` — TEK indikatör, ~20 kırılım
türü: `downtrend_break`/`uptrend_break` (trendline), `range_breakout_up/down`,
`zone_break_up/down`, `hh_break`/`ll_break` (swing pivot), `n_week_high_{26,52}`,
`ma_break_ema{50,200}_{up,down}`, `donchian_break_{up,down}_{20,55}`,
`bb_break_{up,down}`, `channel_break_{up,down}` — hepsi `confirm_bars` parametreli
(1=aynı bar, N=N ardışık bar) ve her biri için `retest_hold`/`false_break` takip
taraması (aynı `pattern_id` ile zincirlenir, ORİJİNAL kırılım kaydı asla değişmez).

**Mimari — iki ayrı kırılım tespit yolu:**
1. Trendline/range/zone kaynaklı: `tlab/features/`'ın KENDİ touches/broken_at
   mekanizması (aynı `PriceStructure`'daki gibi, RAW — alterne edilmemiş — pivotlarla).
2. Pivot(HH/LL)/MA/Donchian/Bollinger/kanal kaynaklı: TEK bir jenerik "seviye dizisi +
   confirm_bars" tarayıcısı (`_generic_break_events`) — `hh_break`/`ll_break` için
   her swing pivotu, KENDİSİNDEN SONRAKİ aynı-türden pivot doğana kadar "aktif" bir
   seviyedir (swing_fib_abcd'deki ABC üçlü zincir deseniyle AYNI mimari).

**Kalite skoru** (`quality_score`, görev metninin sabit ağırlıkları: hacim 0.30,
seviye yaşı 0.20, temas 0.20, gövde 0.15, mesafe 0.15) — normalizasyon sabitleri
görev metninde belirtilmediği için `BreakoutParams`'ta makul varsayılanlarla
(kod içinde gerekçelendirilmiş).

**Faz 2-EK'in TAMAMI YAZILMADI** — yalnızca Faz 8A'nın ihtiyaç duyduğu iki parça:
`volatility.py::bollinger()` (Bollinger + bandwidth) ve YENİ `tlab/features/
channels.py::regression_channel()` (rolling log-fiyat OLS kanalı). Faz 2-EK'in geri
kalanı (`pivot_channel`, `frozen_channel_at`, `channel_position`, `patterns_geom.py`,
`hs_pattern.py`, `zones_sd.py`, `xsec.py`, W1 zaman dilimi) HÂLÂ YAPILMADI — Faz
8B/8C/8D bunlara ihtiyaç duyacak, ayrı bir takip işi.

**İki gerçek hata bulunup düzeltildi (Faz 8A yazılırken):**
1. `price_structure.py::_trendlines`'da kırılım yönü TERS eşlenmişti (resistance
   kırılımı — close çizginin ÜSTÜNE kapanır — "short" olarak, support kırılımı
   "long" olarak damgalanıyordu; `build_trendlines`'ın kendi `beyond` tanımına göre
   doğrusu tam tersi). Hiçbir test `direction` alanını doğrulamıyordu — Faz 8A aynı
   `build_trendlines` primitifini kullanırken fark edildi. 1 regresyon testi eklendi.
2. `IndicatorResult.to_json()`, payload'da `numpy.bool_` (ör. `vol_ratio >= k`
   karşılaştırmasından) olduğunda `TypeError` fırlatıyordu — `tlab/core/types.py`'ye
   `np.bool_ -> bool` dönüşümü eklendi. Bu, Faz 6'daki price-indexed-series JSON
   hatasıyla AYNI KATEGORİ: hiçbir test bu round-trip'i gerçek veriyle (scanner'ın
   süreçler-arası JSON aktarımı) egzersiz etmemişti, `tlab scan --preset dusen_kiran`
   gerçek BIST verisiyle çalıştırılana kadar yakalanmadı.

**Registry:** `PriceStructure` ile AYNI istisna yolu (`register_verified_elsewhere`)
— trendline/zone "aday havuzu" + hh/ll'nin süperseded zamanlaması generic
`repaint_test`'in varsayımıyla uyuşmuyor; non-repaint sözleşmesi
`tests/test_trend/test_breakouts.py`'de hedefli testlerle (donchian/n_week_high
`.shift(1)` lookahead tuzağı regresyonu, `confirm_bars` semantiği, false_break'in
orijinal kaydı bozmadığını doğrulayan zincir bütünlüğü testi dahil) doğrulanır.

**CLI:** `config/scans.yaml` + `tlab scan --preset dusen_kiran` (yalnızca
`downtrend_break` sinyallerini filtreler — preset mekanizması genel, gelecekte
başka indikatör/filtre kombinasyonları için de kullanılabilir).

Gerçek veri smoke: TCELL 1D üzerinde 282 kırılım, görev metnindeki türlerin
neredeyse tamamı (downtrend_break/uptrend_break hariç — bu pencerede hiç
oluşmadı, parametre/veri bağımlı, hata değil) tetiklendi, hatasız çalıştı.

## Komutlar

```bash
# Testler (network işaretli olanlar hariç)
python -m pytest -q -m "not network"

# Tek modül
python -m pytest tests/test_harmonics/ -q

# Lint
python -m ruff check tlab/ tests/
python -m mypy tlab/
python -c "from pathlib import Path; from tlab.testing.lint_lookahead import lint_paths; [print(i) for i in lint_paths(Path('.'))]"
```

Ortamda bazen `hypothesis`/`ruff`/`mypy` eksik çıkabiliyor (sistem pip ortamı, izole venv değil)
— eksikse `pip install <paket>` ile kurup devam et.

## Git / Push Prosedürü (KRİTİK — her fazın sonunda uygulanır)

Ev dizini kökündeki (`C:\Users\Samet`) local git deposu, GERÇEK GitHub deposuyla
(`github.com/serefsametumutlu/QuaxisLabs`) ilişkisiz bir commit geçmişine sahip. Gerçek
reponun kökü bilanco-radar'ın içeriği; bu proje oraya `teknik-analiz/` alt klasörü olarak
push ediliyor. Normal `git add`/`git commit` bu projenin dosyalarıyla SINIRLI tutulmalı (ev
dizini deviyle 4GB+ başka içerik de paylaşıyor — asla `git add -A` kullanma, PDF'leri asla
ekleme).

Push adımları:
1. `cd C:\Users\Samet && git fetch origin main` (tam, `--depth=1` DEĞİL)
2. `git worktree add /tmp/<isim> origin/main`
3. `git archive <local-commit> -- "Desktop/Teknik Analiz" | tar -x --strip-components=2 -C /tmp/<isim>/teknik-analiz`
4. Worktree içinde: `git checkout -b <branch>`, ilgili dosyaları `git add`, commit
5. `git push origin <branch>:main` (fast-forward, force GEREKMEZ)
6. `git worktree remove /tmp/<isim> --force`

Bağlantı yavaşsa/kesilirse `GCM_INTERACTIVE=never GIT_TERMINAL_PROMPT=0` ortam değişkenleriyle
retry edilebilir.

## Sıradaki Adımlar / Backlog

Detaylı öneri raporu: **Medyan Rotasyon Notu** (artifact olarak yayınlandı, kullanıcıda linki
var). Özet:

1. **`tlab/features/robust_stats.py`** (bağımsız, düşük risk) — medyan/MAD tabanlı
   `rolling_median`, `mad`, `robust_zscore`, `median_bands`; `ma.py`'ye `median_ma()`.
   Gerekçe: mevcut göstergelerin hepsi ortalama/std tabanlı, tek bir uç değere karşı kırılgan.
2. **`tlab/sector/`** (yeni katman) — `config/sector_map.yaml` (sembol→sektör),
   `basket.py::sector_median_return()`, `rotation.py::rotation_score()`,
   `correlation.py::sector_correlation_matrix()`. Lider sektör sürekliliği için mevcut
   `stats.halflife()` doğrudan kullanılabilir.
3. **DuPont / ucuz hisse taraması / gelir mevsimselliği** — bu projenin KAPSAMI DIŞINDA,
   bilanco-radar'a ait (temel veri gerektiriyor, `src/fetchers/` zaten İş Yatırım MaliTablo +
   KAP'tan çekiyor). İki proje birbirini import etmez, ortak sinyal dosyasıyla bağlanır.
4. **Kointegrasyon çürüme (decay) izleyicisi** (`tlab/indicators/pairs/`) — kullanıcının
   takip ettiği bir kantçının notundan (2026-08-29): `discover_pairs` (Faz 5) kointegrasyonu
   yalnızca KEŞİF anında (ADF, tek seferlik) test ediyor; bir çift seçilip pozisyon
   açıldıktan SONRA spread'in kointegre KALDIĞI hiç yeniden doğrulanmıyor. Öneri: aktif
   tutulan bir çift için spread üzerinde ROLLING ADF p-değerini (ör. son 60-90 bar
   penceresi) z-skorun yanında ikinci bir canlı seri olarak takip et; p-değeri eşiği geri
   aşarsa (yapısal kırılma — M&A, mevzuat değişikliği, endeks yeniden dengeleme vb.)
   z-skor henüz dönmemiş olsa bile pozisyonu düzleştirme sinyali üret. Mevcut
   `RelativeMomentumPair`/`pairs_engine.py`'ye ek bir "cointegration_broken" durumu/guard'ı
   olarak eklenebilir — `discover_pairs`'in ADF/halflife makinesini AYNEN tekrar kullanır,
   yeni bir istatistiksel yöntem gerekmez.
5. **Beta-nötr eş zamanlı long/short pair modu** (`tlab/indicators/pairs/`,
   `tlab/backtest/pairs_engine.py`) — AYNI kaynaktan (2026-08-29): notun "piyasa riskinin
   izole edilmesi" argümanı (Y long + X short EŞ ZAMANLI, β ile hedge'lenmiş, piyasa
   yönünden bağımsız kâr) mevcut `RelativeMomentumPair`'e UYMUYOR — o motor sermayeyi Y↔X
   arasında ROTASYONEL taşıyor (her an tek varlıkta %100 long), yani her zaman piyasa
   beta'sına maruz kalıyor. Gerçek market-neutral istatistiksel arbitraj tlab'da HENÜZ YOK.
   Öneri: aynı `discover_pairs`/β kestirim altyapısını kullanan, AYRI bir yürütme modu
   (`pairs_engine.py`'de yeni bir mod, mevcut rotasyonel motoru DEĞİŞTİRMEDEN) — β oranıyla
   ölçeklenmiş simultane long/short, dolar veya beta-nötr boyutlandırma. Kullanıcı kararı
   bekleniyor: rotasyonel mod mu tek ürün olacak, yoksa iki mod da mı sunulacak — kod
   yazılmadı, yalnızca backlog notu.

Önerilen sıra: 1 → 2 (tlab içinde, tek fazda yapılabilir), 3 ayrı bir bilanco-radar
konuşması, 4/5 pair motoruna dokunan ayrı bir görev (kullanıcı hangisiyle başlanacağına
karar verecek). Faz 3'ü (harmonik) bloklamaz.

## Gelecek Entegrasyonlar (henüz tasarlanmadı, sadece hedef notu)

- **TradingView masaüstü bağlantısı**: Kullanıcı bunu ayrıca kendi planlayacak (tv_health_check benzeri bir yaklaşım). Bu dosyada detay yok, tasarım kararları kullanıcıdan gelecek.
- **Fintables bağlantısı**: Ham temel veri + hazır analiz çekimi için ileride entegre edilecek. Detay/tasarım henüz yok.
- **Bilanço Radar ile birleşme**: Bu projenin çıktıları (sinyaller, taramalar) ile Bilanço Radar'daki `dashboard.html` temel analiz katmanı tek bir app'te buluşacak. Doğruluğu teyit edilmiş veriler iki proje arasında paylaşılabilir.

## Arayüz Kararı

Henüz verilmedi (Streamlit/masaüstü mü, web/HTML mi). Bilanço Radar ile ileride birleşeceği için bu karar ertelendi — indikatör/tarama motoru arayüzden bağımsız tasarlanmalı ki hangi arayüz seçilirse seçilsin çekirdek mantık değişmesin.
