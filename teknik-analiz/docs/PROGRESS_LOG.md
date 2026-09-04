# Teknik Lab (tlab) — Detaylı İlerleme Günlüğü (Arşiv)

Bu dosya, CLAUDE.md'nin 150k karakter sınırını aşması nedeniyle oradan taşınan tam faz-faz oturum notlarını içerir. CLAUDE.md'deki "İlerleme Durumu" bölümü artık yalnızca bir özet — buradaki her madde o özetin genişletilmiş/orijinal hâli. Yeni oturumlar önce CLAUDE.md'yi okumalı, yalnızca belirli bir fazın TAM gerekçesine/tasarım kararına ihtiyaç duyulduğunda buraya bakmalı.

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
- **`structure.report` — birleşik "aracı kurum raporu" grafiği + Özet Raporu paneli
  (2026-08-30):** TAMAMLANDI. Kullanıcı, bir önceki oturumun kapattığı iki AçIK soruyu
  yanıtladı: (1) görsel işi Faz 8B'den ÖNCE yap, (2) `structure.price_structure` +
  `structure.swing_fib_abcd`'i AYRI grafikler olarak DEĞİL, `images/Ekran görüntüsü
  2026-08-29 165109.png` referansındaki gibi TEK bir grafikte BİRLEŞTİR ("birleştir").
  Ayrıca yeni bir referans (`images/quant_not.png` — Elliott dalga notu, koyu temalı
  net bir TABLO tasarımı) ve iki yeni gereksinim getirdi: arkaplan (şimdilik) BEYAZ
  kalsın ("sonra tekrar bakarız"), ve grafiğin SAĞINA, hissenin durumunu/hedeflerini
  özetleyen bir "Özet Raporu" metin paneli eklensin — `AskUserQuestion` ile İKİ karar
  netleştirildi: rapor metni **deterministik şablon** (LLM çağrısı YOK, zaten hesaplı
  değerlerin kural-tabanlı Türkçe cümlelere çevrilmesi) olacak, gerçek AI-yazımı
  ERTELENDİ (maliyet/non-determinizm/mimari sapma gerekçesiyle).
  1. **Mimari karar** — iki indikatör AYRI AYRI hesaplanmaya devam eder (`structure.
     price_structure`/`structure.swing_fib_abcd` DOKUNULMADI, tek istisna aşağıdaki RSI/
     HVN eki); BİRLEŞTİRME yalnızca VİZ katmanında olur — `tlab/viz/renderer.py::
     render_structure_report(ps_result, sf_result, df, ...)` iki HAZIR `IndicatorResult`'ı
     aynı paylaşılan çizim yardımcılarıyla (`_draw_boxes`/`_draw_levels`/`_draw_lines`/
     `_draw_markers`/`_stagger_yshifts`) TEK figürde çizer — hiçbir YENİ hesap viz'e
     sızmadı. `structure.report` gerçek bir Registry/CATALOG girdisi DEĞİL (`tlab/viz/
     live.py::STRUCTURE_REPORT_NAME` sabiti + `compute_structure_report`/`render_
     structure_report_live`), `tlab plot --indicator structure.report` bunu tetikler.
  2. **RSI paneli + HVN vurgusu** — `PriceStructure`'a EKLENDİ (doğru katman: bunlar
     gerçek hesap, viz'de OLAMAZDI): `features/oscillators.py::rsi()` (zaten vardı)
     `series["rsi_14"]` olarak sarmalandı, `series_layout["rsi"]` yeni alt panel;
     YENİ `features/volume_profile.py::find_hvn_nodes(volumes, top_n, min_ratio)` —
     saf histogram tepe-noktası tespiti (yerel maksimum + peak'in `min_ratio` katı),
     value area'dan BAĞIMSIZ (`vp_hvn` yeni fiyat-indeksli seri, 1.0/0.0). Bu ekleme
     `structure.price_structure`'ın STANDALONE grafiğine de otomatik yansır (RSI paneli
     + HVN yeşili artık HERKESTE var, yalnızca birleşik grafikte değil).
  3. **Fib merdiveni "gökkuşağı"na geri döndü** — `themes.py::_FIB_NEAREST`: 2026-08-29
     minimalist tek-gri paleti kullanıcı gerçek örneklerle kıyaslayınca fakir buldu;
     her basamak (0.236/0.382/0.5/1.0/1.272/1.618/2.0) artık ayrı bir Theme rengi
     taşıyor (YENİ renk EKLENMEDİ, mevcut alanlar yeniden dağıtıldı), yalnızca altın
     bölge (0.618/0.786→accent) korundu. `_level_display_text()` (renderer.py) fib
     etiketlerine referans gibi satır-içi "oran - fiyat" metni ekledi (ör.
     "0.618 - 105.80"), eskiden yalnızca "fib_0.618" görünüyordu.
  4. **Özet Raporu paneli** — YENİ `tlab/viz/report_text.py::build_summary_lines(ps,
     sf, df)`: POC/VAH/VAL konumu, RSI yorumu (aşırı alım/satım/nötr eşiği), son swing
     etiketi (HH/HL/LH/LL → Türkçe trend cümlesi), en yakın AÇIK AB=CD hedefi (yön +
     %mesafe), destek/direnç bölge konumu, son MACD kesişimi — HEPSİ zaten hesaplanmış
     `IndicatorResult` alanlarının if/else ile cümleye çevrilmesi (`_pair_header_lines`
     ile AYNI "biçimlendirme, yeni hesap değil" ilkesi), LLM çağrısı YOK. `renderer.py::
     _draw_summary_panel` bunu 3. kolonda (`rowspan=n_rows`, eksenleri gizli [0,1]x[0,1]
     bir "tuval") madde işaretli satırlar olarak çizer (`textwrap` ile satır kaydırma).
  5. **İKİ GERÇEK HATA bulundu ve düzeltildi (gerçek TCELL/THYAO/ASELS verisiyle
     birleşik grafiği render ederken — tek-indikatörlü grafiklerde YETERİNCE yoğun
     olmadığı için hiç tetiklenmemişti):**
     - **Etiketler masthead'e/kenar boşluğuna taşıyordu.** İki indikatörün Level'ları
       (POC/VAH/VAL/zone + AB=CD'nin `max_active_targets` kadar hedefi + fib merdiveni)
       BİRLEŞİNCE aynı dar fiyat bandında (`_stagger_yshifts`'in "n hiç küçülmez"
       zincir etkisiyle) TCELL'de 3 AB=CD hedef etiketi grafiğin ÜST kenar boşluğuna
       (masthead'in bile üstüne) taştı. İki aşamalı düzeltme: (a) `render_structure_
       report` artık AYNI ABC üçlüsünün BİRDEN FAZLA hedefinden yalnızca fiyata EN
       YAKINI ve fib merdiveninde yalnızca "altın bölge" (%61.8/%78.6) etiketlenir
       (`_draw_levels`'a YENİ `labeled: set[Level] | None` parametresi — şekil HER
       ZAMAN kalır, yalnızca metin kısıtlanır, bilgi kaybı YOK); (b) `_stagger_yshifts`'e
       YENİ `price_bounds` parametresi — SABİT bir piksel tavanı (`_STAGGER_MAX_
       OFFSET_PX`, yalnızca `price_bounds` verilmeyen testlerde YEDEK) YETERSİZDİ,
       çünkü aynı piksel bütçesi geniş-fiyat-aralıklı hisselerde (THYAO: 260-360) çok
       daha fazla fiyat birimine karşılık geliyordu. **İkinci bir gerçek hata (bu
       düzeltmeyi doğrularken bulundu):** THYAO'da VAH hâlâ masthead'in üstüne
       taşıyordu — paylaşılan `n` sayacı ÖNCEKİ öğelerden ZATEN yüksek gelmişti, TEK
       adımlık bir geri-sarım (`n -= 1`) sınırın İÇİNE dönmeye YETMİYORDU (377 → 375,
       hâlâ 360'lık sınırın dışında). Düzeltme: `n`, sınırın İÇİNE dönene (ya da 0'a)
       kadar bir `while` ile geri sarılıyor. Yeni regresyon testi (`test_stagger_
       yshifts_never_escapes_price_bounds`) hem yığılma+sınıra-yakın-öğe senaryosunu
       hem TEK-adımlık geri-sarımın YETERSİZ kaldığını doğruluyor.
     - **VP paneli legend'ı yanlış köşede.** Yeni HVN/Gaussian-Fit legend girdileri
       varsayılan (figürün sağ ÜST köşesi) konumda render edildi — ama birleşik
       grafikte sağ üst köşe artık vp panelinin DEĞİL, geniş "Özet Raporu" sütununun
       üstüne denk geliyordu (görsel bağlam kopuyordu). Düzeltme: `legend2` adlı AYRI
       bir Plotly legend grubu (`_add_hvn_legend_swatch`/`_draw_volume_profile`'ın
       yeni `legend_name` parametresi), `_position_vp_legend()` ile vp panelinin
       KENDİ `xaxis2.domain`/`yaxis2.domain`'inin hemen üstüne yerleştiriliyor
       (`_apply_pair_legends`'daki "sabit kesir varsayma, gerçek domain'i oku"
       ilkesiyle AYNI).
  6. **Masthead alt başlığı override edildi** — `_price_header(ps_result, df)`
     doğrudan kullanılınca alt başlık `ps_result.indicator`'dan ("Price Structure")
     türetiliyordu, birleşik görünümü YANSITMIYORDU; `dataclasses.replace()` ile
     yalnızca `subtitle` alanı "Fiyat Yapısı — Birleşik Rapor (Yapı + Swing/Fibonacci)"
     olarak değiştirildi, diğer alanlar (fiyat/değişim/tarih) AYNI `_price_header`
     biçimlendirmesinden geliyor.
  7. **`quant_not.png` referansı** — doğrudan bir formasyon/kural İÇERİĞİ DEĞİL
     (Elliott dalga notu, kapsam dışı), yalnızca "Özet Raporu"nun görsel dilini
     (koyu tablo, net başlık satırı, kısa madde metni) esinlemek için kullanıldı —
     rapor paneli KENDİ (beyaz/light_analysis) temasında, bu görselin renk paletini
     BİREBİR kopyalamadı.
  Doğrulama: `tlab plot --symbol {TCELL,THYAO,ASELS} --tf 1d --indicator
  structure.report --market bist --out outputs/samples/{sembol}_structure_report.png`
  gerçek veriyle render edildi, 3 sembolde de İTERATİF olarak gözden geçirildi (her
  düzeltme turu yeniden render + gözle kontrol) — üçünde de artık hiçbir etiket
  masthead'e/kenar boşluğuna taşmıyor, RSI/HVN/Özet Raporu panelleri doğru
  görünüyor. **DÜRÜST NOT — kalan sınırlama**: çok dar bir fiyat bandında (ör. THYAO'da
  350-360 aralığı, "Direnç Bölgesi"/VAH/POC üçlüsü) hâlâ HAFİF bir metin yakınlığı
  var — bu bir "yetersiz dikey alan" durumu (gerçek fiziksel sınır, algoritma
  hatası değil), flying-off-chart hatasının aksine grafiğin İÇİNDE kalıyor, kabul
  edilebilir görüldü. 8 yeni test (362→370): `find_hvn_nodes` (4), `PriceStructure`
  RSI/HVN/walk-forward-eşitlik genişletmesi (2 yeni + 1 güncelleme), `_stagger_
  yshifts` price_bounds regresyonu (1), `render_structure_report` duman testi (1).
  `pytest -q -m "not network"` 370/370 yeşil, `ruff check`/`mypy`/`lint_lookahead`
  değişen dosyalarda temiz (mevcut baseline uyarıları AYNI, ilgisiz). **Sırada**: Faz
  8B (wedge/head_shoulders/flag_pennant/double_top_bottom/broadening) — kullanıcı
  onayı zaten vardı, görsel iş bitti, şimdi başlanabilir → Faz 8D → K3 → Faz 8E →
  Faz 10 → Faz 9. Harmonik grafiklerin (Pesavento/Carney vb.) AYNI zenginleştirme
  turundan (renkli fib ladder zaten vardı, RSI/HVN o grafiklerde YOK) geçip
  geçmeyeceği HENÜZ karara bağlanmadı — ayrı bir kullanıcı kararı gerektirir.
- **"Özet Raporu" GÖRSELDEN ÇIKARILDI + gerçek LLM metni + hacim profili/panel
  çerçevesi düzeltmesi (2026-08-30, bir önceki maddenin HEMEN ardından, kullanıcı
  çıktıyı inceleyip geri bildirim verince):** TAMAMLANDI. Kullanıcı üç şey söyledi:
  (1) grafiğin İÇİNDEKİ deterministik "Özet Raporu" metnini sevmedi — "yapay zeka
  gibi değil bir quant gibi" yazılmış, samimi, X'te (Twitter) paylaşılabilecek
  SERBEST metin istedi, GÖRSELİN DIŞINDA ayrı bir çıktı olarak; (2) hacim profili
  (HVN+Gaussian Fit) paneli referansla (`images/Ekran görüntüsü 2026-08-26
  203900.png`) kıyaslanınca "çok cılız, kendi alanını doldurmuyor" bulundu; (3)
  genel ilke: görseller göze hoş gelmeli, metinler konuya hakim olmayan insanlar
  için de anlaşılır olmalı.
  1. **"Özet Raporu" paneli SİLİNDİ** — `render_structure_report` artık `_render_
     price_based` ile AYNI 2 kolonlu (mum+vp) düzeni kullanıyor (3. kolon/`rowspan`/
     `_draw_summary_panel` KALDIRILDI, genişlik `_DEFAULT_WIDTH`e döndü). Bir önceki
     maddenin `report_text.py::build_summary_lines()` SİLİNMEDİ — artık görselde
     DEĞİL, aşağıdaki LLM modülüne HAM GİRDİ olarak kullanılıyor.
  2. **YENİ `tlab/viz/quant_report.py::generate_quant_report()`** — gerçek bir
     Anthropic Claude API çağrısı (`anthropic` paketi `pyproject.toml`'a eklendi,
     model varsayılanı `claude-sonnet-5`, `ANTHROPIC_API_KEY` ortam değişkeninden
     okunur). Prompt tasarımı: `build_summary_lines()`'ın ürettiği olgu maddeleri
     LLM'e HAM VERİ olarak veriliyor + katı bir "bu olguların DIŞINDA hiçbir sayı/
     seviye UYDURMA" talimatı (halüsinasyon riskine karşı — tüm sayısal içerik
     ZATEN hesaplanmış `IndicatorResult`'lardan geliyor, LLM yalnızca SUNUMU
     üstleniyor, yeni bir "hesap" ORTAYA ÇIKMIYOR) + "bir yapay zeka gibi değil
     bir quant gibi, samimi, terimleri açıklayarak yaz, AL/SAT tavsiyesi verme"
     talimatları. API anahtarı yoksa ya da çağrı başarısız olursa (`except
     Exception` — harici bir API'ye bağımlılık, geniş yakalama kasıtlı) sessizce
     ÇÖKMEZ, deterministik madde listesine (`QuantReport.used_ai=False` + `note`)
     DÜŞER. 4 yeni test (`tests/test_viz/test_quant_report.py`) — `anthropic.
     Anthropic` HER ZAMAN mock'lanır, gerçek bir API çağrısı YAPILMAZ.
  3. **CLI**: YENİ `tlab quant-report --symbol X --tf 1d --market bist [--out]`
     (yalnızca metni üretir) + `tlab plot --indicator structure.report --with-
     report` (grafiğin YANINA aynı metni bir `.txt` olarak da yazar, stdout'a da
     basar). İkisi de `tlab/viz/live.py::compute_structure_report`'u paylaşır.
  4. **GERÇEK HATA — hacim profili paneli "kendi alanını doldurmuyordu"**: kök
     neden `PriceStructureParams.profile_window_bars` (60 bar, ~3 ay) varsayılan
     grafik yakınlaştırmasından (`renderer.py::_DEFAULT_LAST_N`, ~250 bar, ~1 yıl)
     ÇOK DAHA DAR bir pencereydi — sağdaki vp panelinin dikey ekseni ana panelin
     GÖRÜNÜR fiyat aralığıyla senkronize edildiği için (`_sync_price_yaxis`), dar
     pencereden gelen histogram panelin yalnızca küçük bir dilimine sıkışıp geri
     kalanı BOŞ kalıyordu. Düzeltme: varsayılan `profile_window_bars` 60→250 (viz
     katmanına SIKI bağlı değil — `price_structure.py` `renderer.py`'yi import
     ETMEZ, yalnızca aynı "tipik görünür pencere" varsayımını PAYLAŞAN bağımsız
     bir varsayılan; testler kendi `profile_window_bars=40`'ını EXPLICIT verdiği
     için etkilenmedi).
  5. **İkinci gerçek sorun — çubuklar arası boşluk "cılız" görünüme katkıdaydı**:
     `_draw_volume_profile`'ın `go.Bar` trace'i varsayılan `bargap`den dolayı ince/
     aralıklı çubuklar üretiyordu; artık her çubuğun `width`i (Plotly'nin yatay
     bar'larda y-yönü kalınlığı) bin merkezleri arası mesafeye EŞİTLENİYOR — bitişik,
     "dolu dolu" bir histogram (referansla aynı görünüm). Yeni regresyon testi
     (`test_volume_profile_bars_are_gapless`).
  6. **Panel-başına çerçeve** — kullanıcının "çerçevelerden çok uzak" ifadesi
     referans mockup'ın her alt paneli (mum+vp, hacim, MACD, RSI) KENDİ ince
     kenarlığıyla çizdiğini işaret ediyordu (eskiden yalnızca TÜM figürü saran TEK
     dış çerçeve vardı, `_draw_card_frame`). YENİ `_draw_panel_frames()` —
     `fig.select_xaxes()`/`plotly_name` son ekiyle HER eksen çiftinin (xaxis/
     yaxis, xaxis2/yaxis2, ...) domain'ini okuyup bir dikdörtgen çizer; panel
     sayısı/düzeni ÖNCEDEN bilinmez, doğrudan figürden introspect edilir — bu
     yüzden `_apply_layout`'u çağıran TÜM grafiklere (standalone `structure.
     price_structure`/`swing_fib_abcd`/harmonik dahil, yalnızca birleşik rapora
     DEĞİL) otomatik yansıdı. Yeni regresyon testi (`test_panel_frames_drawn_
     around_each_subplot`).
  7. **VP legend'ında GERÇEK bir konumlandırma hatası bulunup düzeltildi** (bu
     düzeltmeleri doğrularken, ASELS'te fark edildi): `_position_vp_legend`'in
     ilk taslağı `yanchor="bottom"` ile vp panelinin HEMEN ÜSTÜNE (`y1+0.015`)
     yerleştiriyordu — ama `yanchor="bottom"` bir legend kutusunun YUKARI doğru
     büyümesi demek, bu da onu masthead'in (sembol/fiyat satırı, ör. "404.00")
     TAM ÜSTÜNE bindiriyordu. Düzeltme: `yanchor="top"`, panelin KENDİ üst
     kenarının hemen ALTINA (panelin İÇİNE, hafif saydam arkaplanla okunur) —
     artık panel yüksekliğinden BAĞIMSIZ olarak asla masthead'e taşmaz.
  Doğrulama: TCELL/THYAO/ASELS `structure.report` grafikleri yeniden üretildi,
  `images/Ekran görüntüsü 2026-08-26 203900.png` referansıyla gözle karşılaştırıldı
  — vp paneli artık dolu/yoğun, HVN yeşili net, Gaussian eğrisi panelin tamamını
  kapsıyor, her panelin kendi çerçevesi var, legend doğru konumda. `tlab quant-
  report`/`tlab plot --with-report` API anahtarı OLMADAN test edildi (fallback
  yolu) — gerçek bir Anthropic API anahtarıyla uçtan uca deneme bu oturumda
  YAPILMADI (ortamda `ANTHROPIC_API_KEY` yok), yalnızca mock'lu testlerle
  doğrulandı; kullanıcı kendi anahtarıyla ilk gerçek denemeyi yapmalı. 6 yeni test
  (370→376). `pytest -q -m "not network"` 376/376 yeşil, `ruff check`/`mypy`
  değişen dosyalarda temiz (baseline AYNI). **DÜRÜST NOT**: `tlab scan`/EOD
  toplu tarama akışına (`tlab/scanner/eod.py`) otomatik quant-report üretimi
  HENÜZ ENTEGRE EDİLMEDİ — kullanıcının senaryosu ("taramadan sonra ASELS
  çıktı... görselle birlikte metin") bunu ima ediyor, ama çoklu-sinyal bir
  taramada HER sinyal için LLM çağrısı yapmak maliyet/gecikme açısından ayrı bir
  tasarım kararı gerektirir (ör. yalnızca YENİ sinyaller için çağrı) — bilinçli
  olarak bu oturumun kapsamı DIŞINDA bırakıldı, ayrı bir takip görevi.
- **LLM sağlayıcısı Gemini'ye geçirildi + vp paneli genişliği + harmonik fib
  merdiveni/durum rengi düzeltmesi (2026-08-30, aynı gün üçüncü tur):** TAMAMLANDI.
  Kullanıcı üç şey daha söyledi: (1) Anthropic (Claude) API'sini KULLANMAK
  İSTEMEDİ — "Claude haklarımın buraya gitmesini istemiyorum" (Claude Code/
  Claude.ai aboneliğinden AYRI, pay-per-token bir Anthropic Console hesabı
  gerektirse de, kullanıcı tüm kullanımını bilinçli olarak Anthropic ekosistemi
  DIŞINDA tutmak istedi) — Gemini veya Copilot'u sordu; (2) hacim profili
  panelinde Gaussian eğrisi "kendi alanının dışına taşıyor" gibi görünüyordu,
  panel sağa doğru biraz daha genişletilebilir dedi; (3) yalnızca Pesavento
  harmonik örnekleri vardı ve beğenmedi — sinyalin gelip gelmediği/hangi
  noktada geldiği/hedefin nerede olduğu (veya henüz gelmediyse olası D noktası)
  görünmüyordu, fibo çizgileri de yoktu.
  1. **Sağlayıcı Gemini'ye çevrildi** — değerlendirme: GitHub Copilot'un genel
     amaçlı, ucuz bir "kendi uygulamandan çağır" tarzı tamamlama API'si YOK
     (esas olarak editör/ajan entegrasyonları için), bu kullanım şekline uygun
     değil; Google Gemini'nin gerçekten ücretsiz bir kotası var ve Türkçe
     desteği iyi. `tlab/viz/quant_report.py` yeniden yazıldı: `Provider =
     Literal["gemini","anthropic"]`, varsayılan `"gemini"` (`google-genai`
     paketi, `GEMINI_API_KEY`/`GOOGLE_API_KEY`) — Anthropic yolu SİLİNMEDİ,
     yalnızca artık varsayılan DEĞİL (`provider="anthropic"` ile elle
     seçilebilir, `ANTHROPIC_API_KEY`). CLI'a `tlab quant-report`'a `--provider`/
     `--model` eklendi. **DÜRÜST NOT**: `DEFAULT_GEMINI_MODEL="gemini-2.5-flash"`
     bu kod yazılırken bilinen bir model kimliği — LLM sağlayıcılarının model
     adları zamanla değişir, gerçek kullanımdan önce Google AI Studio'nun
     GÜNCEL model listesinden doğrulanmalı (`--model` ile override edilebilir).
     6 test Gemini mock'una çevrildi + 2 yeni test (Anthropic'in hâlâ opsiyonel
     çalıştığını ve bilinmeyen sağlayıcının `ValueError` fırlattığını doğrular).
  2. **Hacim profili paneli genişletildi + sağ kenar payı eklendi** — `_VP_
     COLUMN_WIDTH` 0.18→0.24 (hem `_render_price_based` hem `render_structure_
     report`, TEK sabitte birleştirildi); `_draw_volume_profile` artık x-eksenini
     `[0, max(bar,gaussian)*1.12]` olarak AÇIKÇA ayarlıyor — eskiden Plotly'nin
     varsayılan autorange payı, bar VE Gaussian eğrisi AYNI tepe değerine
     (`amplitude = max(volumes)`) ulaştığı için yetersiz kalıyor, ikisi de
     panelin sağ ÇERÇEVESİNE bitişik duruyordu.
  3. **Harmonik grafiklere XA fib merdiveni eklendi** — `scanner_indicator.py`,
     her adayın XA bacağı için standart geri çekilme basamaklarını (0.382/0.5/
     0.618/0.786 — `fibonacci.retracement()`'ın doğrudan sarmalanması,
     `swing_fib_abcd.py::_fibonacci_levels` ile AYNI desen, YENİ bir hesap
     yöntemi DEĞİL) `Level` olarak yayınlıyor; PRZ bandının NEDEN o basamakta
     olduğunu görsel olarak gerekçelendiriyor. `style="fib_retracement"`
     olduğu için mevcut renkli/rainbow `_FIB_NEAREST` paletini VE `_declutter_
     levels`in "yalnızca en güncel aday" davranışını otomatik miras alıyor —
     renderer'da hiçbir yeni kod GEREKMEDİ. 1 yeni test (`test_xa_fib_ladder_
     present_for_known_candidate`).
  4. **GERÇEK HATA — harmonik marker rengi "sinyal geldi mi" sorusunu
     cevaplamıyordu**: eskiden `_draw_markers`'ın harmonik dalı yalnızca
     `"bearish" if state=="invalidated" else "bullish"` kullanıyordu — yani
     pending/active/confirmed'İN HEPSİ AYNI yeşili alıyordu, "sinyal fiilen
     geldi mi (confirmed) yoksa henüz mi (pending/active)" görsel olarak HİÇ
     ayırt edilemiyordu (kullanıcının tam olarak şikayet ettiği şey). Düzeltme:
     yeni `_HARMONIC_STATE_COLOR` sözlüğü — `confirmed`→`accent` (kalın/dolgulu
     kutu, projenin "en karara-değer" marka rengiyle), `active`→`orange`,
     `pending`→`gray`, `invalidated`/`expired`→`red`/`gray`. 1 yeni test
     (`test_harmonic_confirmed_marker_uses_accent_not_generic_bullish`).
  5. **`outputs/samples/`'daki TÜM eski (bu oturumdan önceki fazlarda üretilmiş)
     örnek görseller yeniden üretildi** — kullanıcı "structure report kısımları
     düzelmiş gibi fakat diğerleri aynı gibi" diye sordu; `tcell/thyao/asels_
     price_structure.png`, `tcell/thyao/asels_swing_fib_abcd.png`,
     `tcell/thyao/asels_harmonic_pesavento.png`, `alark_harmonic_pesavento.png`
     ve üç `_structure_report.png` TEKRAR render edildi — panel çerçeveleri/
     vp yoğunluğu/fib rengi düzeltmeleri PAYLAŞILAN kod yolundan (`_apply_
     layout`/`_draw_volume_profile`/`fib_color`) geldiği için hepsine otomatik
     yansıdı, ekstra kod GEREKMEDİ.
  **DÜRÜST NOT — kalan sınırlama (bilinçli olarak ERTELENDİ)**: bir harmonik
  adayın X noktası çok eskiyse ve o zamandan beri YENİ bir aday doğmadıysa
  (ör. `alark_harmonic_pesavento.png`), otomatik yakınlaştırma penceresi
  (`_harmonic_auto_window_start`) hâlâ candidate'ten BUGÜNE kadar uzanıyor —
  bu da grafiğin çoğunun boş/düz mum olduğu bir görünüm yaratabiliyor. Bu bir
  render HATASI değil (veri/parametre gerçeği: o ekol/toleransla daha yeni bir
  aday bulunamadı — grafik bunu DOĞRU yansıtıyor), ama görsel olarak israf —
  pencere sonu sezgisinin (candidate + sabit dolgu vs. bugüne kadar) ayrıca
  gözden geçirilmesi gerekebilir, kullanıcı zaman kısıtı nedeniyle bu turda
  ERTELENDİ ("çok zaman harcadık, Faz 8B'ye devam edelim").
  9 yeni test (378→380... bir önceki maddeyle birlikte 376→380).
  `pytest -q -m "not network"` 380/380 yeşil, `ruff check`/`mypy`/
  `lint_lookahead` değişen dosyalarda temiz (baseline AYNI) — harmonik repaint
  testleri (50/50, `tests/test_harmonics/`) YENİ fib Level'ların non-repaint
  güvenliğini de doğruladı (genel `repaint_test` zaten TÜM `IndicatorResult`
  alanlarını kapsıyor).
  ~~**Görsel iş burada KAPANDI**~~ — kullanıcı bir kontrol turu daha istedi
  (aşağıya bkz.), gerçek kapanış BİR SONRAKİ maddede.

- **Tam galeri üretimi + gerçek Gemini doğrulaması + `trend.breakouts`
  marker patlaması (GERÇEK hata) (2026-08-30, aynı gün dördüncü/son tur):**
  TAMAMLANDI. Kullanıcı, kapsamlı bir son kontrol turu istedi: `outputs/
  samples/` TAMAMEN silinip `outputs/galeri/` adında yeni bir klasöre HER
  indikatör/ekol için birer örnek görsel + gerçek (mock değil) Gemini API'siyle
  üretilmiş `.txt` rapor metinleri üretilsin — "yarım kalmasın, sonra tekrar
  uğraşmayalım" diyerek tek seferde eksiksiz bir inceleme turu istedi.
  1. **Gemini API anahtarı** — kullanıcı kendi `GEMINI_API_KEY`'ini TEKRAR
     İSTEMEK YERİNE `C:\Users\Samet\Desktop\Temel Analiz\bilanco-radar\.env`
     dosyasına bakılmasını söyledi (kendi AYRI projesinde zaten yapılandırmış).
     Oradan alınıp YALNIZCA render/quant-report komutlarına ortam değişkeni
     olarak geçirildi — hiçbir dosyaya/commit'e YAZILMADI. **Model adı da
     bilanco-radar'ın kendi `config.py` yorumundan öğrenilerek düzeltildi**:
     `DEFAULT_GEMINI_MODEL` `"gemini-2.5-flash"`den (ilk tahmin, sabit sürüm)
     `"gemini-flash-lite-latest"`e (Google'ın "-latest" takma adı, otomatik
     günceli takip eder) değiştirildi — bilanco-radar'ın AYNI anahtarla CANLI
     doğruladığı bilgiye göre `gemini-flash-latest`in günlük kotası çok hızlı
     tükeniyor, `flash-lite-latest` AYRI ve daha yüksek bir kotaya sahip.
  2. **Gerçek API çağrısıyla prompt kalitesi doğrulandı ve İKİ gerçek sorun
     bulunup düzeltildi** (`_call_gemini`'nin ürettiği metin ilk denemede
     incelendi): (a) SDK'nın "otomatik fonksiyon çağrısı" uyarısı zararsız
     (bilgilendirme amaçlı, hata değil); (b) model bazen düz-metin talimatına
     RAĞMEN yanıtı ```markdown kod bloğuna sarıyordu (kullanıcının bilanco-
     radar projesinde AYNI API'yle daha önce CANLI gözlemlenen bir davranış,
     `commentary.py::_clean_json_text`de zaten belgelenmiş) — YENİ `_strip_
     markdown_fence()` bunu hem Gemini hem Anthropic yollarında temizliyor;
     (c) **gerçek bir prompt hatası**: ilk üretilen metinler `**kalın**` gibi
     markdown biçimlendirmesi kullanıyordu, ama bu metin X/Twitter'da DÜZ
     METİN olarak paylaşılacak — orada yıldız işaretleri OLDUĞU GİBİ görünür,
     biçimlendirme OLARAK görünmez. `_SYSTEM_PROMPT`'a "DÜZ METİN yaz, markdown
     KULLANMA" kuralı eklendi, ikinci denemede doğrulandı (artık akıcı
     paragraflar, işaretleme yok). 2 yeni test (`test_strip_markdown_fence_*`).
     Üretilen ÖRNEK metinlerin (TCELL/THYAO/ASELS) kalitesi gözle incelendi —
     doğal/sıcak bir "quant sesi", olgu-dışı hiçbir sayı uydurulmamış, terimler
     (POC/RSI/MACD/AB=CD) açıklanarak kullanılmış, sona doğru zorunlu uyarı
     notu eklenmiş.
  3. **GERÇEK HATA — `trend.breakouts` (MultiBreakout) grafiği TAMAMEN
     OKUNMAZDI**: galeri için ilk kez ciddi bir gözle incelenince (Faz 8A'nın
     kendi kabul testi yalnızca "282 kırılım tespit edildi, hatasız çalıştı"
     diyordu, GÖRSEL olarak hiç kontrol edilmemişti) TCELL grafiğinde
     onlarca kırılım etiketi tamamen üst üste binip harfler okunmaz hâle
     gelmişti. Kök neden: `MultiBreakout` TÜM ~20 farklı kırılım türünü
     (channel_break_up, donchian_break_down, zone_touch, vb.) AYNI
     `Marker.kind="breakout"` altında yayınlıyor, generic `_draw_markers`
     dalının (`structure_label`/`harmonic_*`/`pair_signal` DIŞINDAKİ her şey)
     HİÇ declutter'ı yoktu — 2 yıllık veride 282 marker'ın HEPSİ kalıcı
     etiket alıyordu. Düzeltme: YENİ `_generic_marker_group_key()`,
     `Marker.text`e gömülü GERÇEK kategoriyi (`"Kırılım: ... | {break_type} |
     ..."`ın 2. bölümü) ayrıştırıp HER kategoriden yalnızca EN GÜNCEL örneği
     gösterir (`_MAX_GENERIC_MARKERS_PER_GROUP=1`). **Bilinçli olarak
     YALNIZCA `kind="breakout"`a uygulandı** (`_DECLUTTER_GENERIC_KINDS`) —
     `structure.golden_zone`/`structure.supply_demand`'ın "BAŞARILI"/
     "REAKSİYON" gibi generic marker'ları ZATEN az sayıda ve HER biri farklı
     bir swing/bölgeye ait bilgi taşıyor, bunlara aynı "yalnızca en güncel"
     kısıtlamasını uygulamak BİLGİ KAYBI olurdu (ilk taslakta tam bu hataya
     düşüldü — `golden_zone`'un "BAŞARILI" geçmişi 1'e indi — kapsam daraltılıp
     düzeltildi). 2 yeni test (bir tanesi TAM OLARAK bu ikinci hatayı da
     kilitliyor: `test_generic_non_breakout_markers_are_not_declutered`).
  4. **`harmonic.five_zero` — dürüst bir bulgu, DÜZELTİLMEDİ**: galeri için
     622 sembollük TÜM BIST evreninde (yerel parquet önbelleğinden, ağ
     çağrısı YOK, ~82 saniye) her ekolün en iyi örneğini bulan bir tarama
     betiği çalıştırıldı — carney/pesavento/gilmore/cypher/nenstar/
     navarro200/three_drives HEPSİ "confirmed" durumunda en az bir aday
     buldu (ör. pesavento→A1YEN, navarro200→ACSEL), ama **five_zero HİÇBİR
     sembolde HİÇBİR aday bulamadı** (varsayılan VE sıkılaştırılmış zigzag
     parametreleriyle iki kez denendi). Bu bir görselleştirme sorunu DEĞİL —
     `harmonic_five_zero_TCELL.png` doğru şekilde "eşleşen formasyon yok"
     gösteriyor. Kök neden ARAŞTIRILMADI (indikatör-mantığı işi, bu turun
     kapsamı DIŞINDA) — ya ekolün toleransları gerçek 2023-2026 BIST verisi
     için aşırı sıkı, ya da `five_zero.py`'de ayrıca incelenmesi gereken bir
     eşleşme hatası var. **Kullanıcıya açıkça bildirilmesi gereken bir
     bulgu**, sessizce geçiştirilmedi.
  5. **`outputs/samples/` TAMAMEN silindi, `outputs/galeri/` oluşturuldu**
     (ikisi de gitignored, git geçmişine hiçbir görsel/metin GİRMEDİ) — 19
     dosya: 8 harmonik ekol (her biri ayrı bir sembolde), `structure.report`
     (TCELL/THYAO/ASELS, artı üçü için Gemini `.txt` rapor), `trend.
     breakouts`/`structure.golden_zone`/`structure.supply_demand`/`trend.
     weekly_channel` (TCELL), `pair.relative_momentum` (TCELL/ISCTR).
  Doğrulama: `pytest -q -m "not network"` 384/384 yeşil (380→384, 4 yeni
  test), `ruff check`/`mypy`/`lint_lookahead` değişen dosyalarda temiz
  (baseline AYNI). **Kullanıcı şu an `outputs/galeri/`'yi TEK TEK inceliyor**
  — bulacağı noktalar bu turun DEVAMI olarak ele alınacak, henüz "kapanmış"
  SAYILMAMALI. İnceleme bitip son düzeltmeler de tamamlanınca **Faz 8B**'ye
  geçilecek.
- **Harmonik/structure.report KAPSAMLI düzeltme turu (2026-08-30, beşinci/son
  tur, kullanıcının galeriyi inceleyip verdiği DETAYLI geri bildirim
  üzerine):** TAMAMLANDI. Kullanıcı 3 ek referans ekran görüntüsünü
  (203913/203956/204024 — swing_fib_abcd + iki harmonik örneği) "detaylıca
  analiz et" diyerek verdi ve şunları istedi: harmonikler tamamen yetersizdi
  (hedef/durum belirsiz, ACSEL'de "saçma bir çizim ekrana sığmamış", A1YEN'de
  "dokundukları noktada hiçbir şey yazmıyor", fibo desenin üzerinde değildi);
  structure.report'ta son mumlar görünmüyordu, HH/HL/LH/LL çok yoğundu, alt
  panellerin "hangisi ne" olduğu belirsizdi, tarih eksikti; breakouts hâlâ
  karmaşıktı ("düzeltemiyorsak kaldıralım"); golden_zone/supply_demand'ın
  structure report'a girip girmeyeceği soruldu; pair için tek örnek yetersizdi.
  1. **GERÇEK HATA (en kritik) — harmonik Y-ekseni, adayın KENDİ geometrisini
     hesaba katmıyordu**: ACSEL/Navarro200 örneğinde BCD üçgeni (D hedefi
     görünür mum aralığının ÇOK altında) ekranın dışına taşıp kesiliyor, "D:
     ... [GEÇERSİZ]" etiketi de görünmez bir y-koordinatına yerleşip
     ALAKASIZ bir noktadaymış gibi GÖRÜNÜYORDU (aslında yalnızca çizim
     alanının dışındaydı). Kök neden: `_sync_price_yaxis` yalnızca GÖRÜNÜR
     MUMLARIN yüksek/düşüğünü kullanıyordu, Polygon/Level (PRZ, D hedefi)
     fiyatlarını HİÇ hesaba katmıyordu. Düzeltme: YENİ `_harmonic_price_
     bounds()` — görünür pencereye düşen TÜM polygon noktaları + level
     fiyatlarını da y-aralığına dahil eder; `_sync_price_yaxis`'e opsiyonel
     `bounds` parametresi eklendi. 1 yeni test (`test_harmonic_price_bounds_
     includes_offscreen_polygon_points`).
  2. **GERÇEK HATA — harmonik pencere BİTİŞİ hep veri setinin gerçek son
     barıydı**: ALARK gibi eski (yeni aday doğmamış) adaylarda grafiğin
     çoğu boş/düz mumdan oluşuyordu (referans mockup'lar formasyonu HER
     ZAMAN ekranın büyük bölümünü doldurur). YENİ `_resolve_window_end()` +
     `_recent_harmonic_time_range()` (start/end resolver'ların PAYLAŞTIĞI
     tek kaynak) — pencere artık adayın `born_time`'ından `_HARMONIC_END_
     PAD_BARS` (60 bar) ötesine kısıtlanıyor (gerçekten daha yeni veri
     varsa davranış DEĞİŞMEZ). `scanner_indicator.py`'deki PRZ/fib Level'ları
     da AYNI ufka (`_LEVEL_END_PAD_BARS=60`, `Level.end` artık `None` değil)
     bağlandı — aksi halde etiketleri yeni daralan pencerenin dışında
     kalıp görünmez olurdu ("fibo/PRZ desenin üzerinde olmalı" şikayetinin
     kök nedeni). 2 yeni test.
  3. **GERÇEK HATA — harmonik marker/panel-başlığı sorunları yol boyunca
     bulunup düzeltildi**: yukarıdaki iki düzeltmeyi TCELL/ACSEL/A1YEN
     örnekleriyle doğrularken `_draw_panel_titles`'ın eksen numaralandırma
     hatası (aşağıda #6) da bu turda bulundu ve düzeltildi.
  4. **Genel yakınlaştırma sıkılaştırıldı**: `_DEFAULT_LAST_N` 250→150,
     `_DEFAULT_WIDTH` 1600→1750 — referans ekran görüntüleri mumları
     bizden belirgin ölçüde daha "şişman"/net gösteriyordu ("son mumları
     görmek neredeyse imkansız"). Bu, HEM `structure.report` HEM standalone
     `structure.price_structure`/`swing_fib_abcd` için geçerli (paylaşılan
     sabitler).
  5. **`trend.breakouts` galeriden ÇIKARILDI**: kullanıcı "düzeltemiyorsak
     kaldıralım" dedi; bir önceki turun kategori-bazlı declutter düzeltmesi
     yeterli bulunmadı (hâlâ "aşırı kötü, ne olduğu belli değil"). Standalone
     gösterim GALERİDEN kaldırıldı (indikatörün kendisi/CLI'sı SİLİNMEDİ,
     tarama için hâlâ kullanılabilir) — daha iyi bir görsel tasarım
     (ör. yalnızca son N güne ait kırılımlar) ayrı bir takip işi.
  6. **GERÇEK HATA — panel başlıkları YANLIŞ eksene çiziliyordu**: YENİ
     `_draw_panel_titles()` ("Hacim"/"MACD"/"RSI" gibi alt panel başlıkları
     — kullanıcı: "hangisi ne belli değil") ilk taslakta `row` numarasını
     DOĞRUDAN eksen sonekiyle eşleştiriyordu; ama vp paneli varken 1. satır
     TEK DEĞİL İKİ eksen tüketir (yaxis+yaxis2), bu yüzden "Hacim" (2.
     satır) başlığı yanlışlıkla vp panelinin (row=1,col=2) ÜSTÜNE
     çiziliyordu. Düzeltme: `n_cols` parametresi eklenip gerçek eksen
     numarası (`n_cols + (row-1)`) hesaplanıyor. 1 yeni test (`test_panel_
     titles_land_on_correct_axis_when_vp_panel_present`).
  7. **`structure.report`'ta ana panel tarihi eksikti**: eskiden yalnızca EN
     ALTTAKİ satır tarih gösteriyordu — ama ana panel (zoom'lanmış) ile alt
     panel grubu (tam geçmiş) FARKLI x-aralıklarına sahip olduğu için ana
     panel HİÇBİR ZAMAN tarih ALAMIYORDU. Artık hem row=1 hem en alttaki
     satır kendi tarihini gösteriyor.
  8. **golden_zone/supply_demand BİRLEŞTİRME denendi, GERİ ALINDI**:
     `render_structure_report`'a opsiyonel `gz_result`/`sd_result`
     parametreleri eklendi (KOD OLARAK duruyor, ileride farklı bir declutter
     stratejisiyle denenebilir) ve `render_structure_report_live`'da
     denendi — ama gerçek TCELL verisiyle render edilince `structure.price_
     structure`'ın ZATEN yoğun bölge/trend/swing etiketleriyle BİRLEŞİNCE
     ana paneli DAHA DA kalabalıklaştırdığı görüldü (dürüstçe test edilip
     REDDEDİLDİ, kör kabul edilmedi). Karar: `render_structure_report_live`
     bu parametreleri GEÇMİYOR, `structure.golden_zone`/`structure.supply_
     demand` kendi ayrı, temiz grafiklerinde kalıyor. Bunun yerine bu ikisi
     için masthead'e KISA bir açıklama eklendi (YENİ `_INDICATOR_EXPLAIN_TR`
     sözlüğü, `trend.weekly_channel`'ı da kapsıyor) — "neden ayrı ve ne
     ifade ediyor belli değil" şikayetini görsel karmaşıklık EKLEMEDEN
     çözer.
  9. **Pair için 2 yeni örnek** — `discover_pairs` gerçek 22 sembollük bir
     alt evrende (BIST bankaları + sanayi) çalıştırılıp GARAN/YKBNK
     (corr=0.91, klasik banka çifti) ve ASELS/TOASO eklendi; TCELL/ISCTR
     zaten vardı.
  Doğrulama: TÜM `outputs/galeri/` yeniden üretildi (harmonikler artık
  formasyonu ekranın büyük bölümüne yayıyor, D hedefleri kendi noktalarında,
  fib merdiveni desenin üzerinde; structure.report'ta mumlar net, tarih
  her iki uçta, panel başlıkları doğru yerde). 4 yeni test (384→388).
  `pytest -q -m "not network"` 388/388 yeşil, `ruff check`/`mypy`/
  `lint_lookahead` değişen dosyalarda temiz (baseline AYNI).
  **Görsel iş burada GERÇEKTEN kapandı** (kullanıcı onayı bekleniyor, ama
  bu turun kapsamındaki TÜM somut şikayetler ele alındı) — sıradaki oturum
  **Faz 8B** ile başlamalı.
- **Faz 8B — Klasik grafik formasyonları** (`tlab/indicators/patterns/`,
  2026-08-30): TAMAMLANDI. 5 indikatör: `wedge.py::WedgeIndicator`
  (`patterns.wedge` + bonus `patterns.triangle`, TEK sınıf/iki katalog
  girdisi — `HarmonicIndicator`'ın instance-level `meta` deseniyle AYNI),
  `head_shoulders.py::HeadShouldersIndicator` (`patterns.head_shoulders`,
  TOBO/OBO), `flag_pennant.py::FlagPennantIndicator` (`patterns.
  flag_pennant`), `double_top_bottom.py::DoubleTopBottomIndicator`
  (`patterns.double_top_bottom`, K1 TWYS eki), `broadening.py::
  BroadeningIndicator` (`patterns.broadening`).
  1. **Ortak durum makinesi** — `tlab/core/pattern_state.py::
     track_breakout_pattern` (`harmonics/state.py::track_pattern`'in
     XABCD'den bağımsız genelleştirilmesi): PENDING -> CONFIRMED (kırılım)
     -> RETEST_HOLD/TARGET_REACHED; PENDING -> INVALIDATED/EXPIRED.
     `SignalState`'in yalnızca 6 sabit değeri olduğu için (retest_hold/
     target_reached AYRI bir state DEĞİL) `golden_zone.py`'nin ZATEN
     kullandığı desenle `payload["event"]="{pattern_name}_{suffix}"`
     üzerinden ayrım yapılır (pending->pending, confirmed VE retest_hold->
     confirmed, target_reached->completed). `PatternTrackingConfig.
     invalidation_check`/`break_line` callable'lar sayesinde 5 farklı
     formasyonun tamamen farklı geometrisine (sabit çizgi/eğik çizgi/OLS
     kanalı) uyarlanabiliyor. `marker_text()`/`level_end_from_signals()`
     de paylaşılan yardımcılar — 5 modülün hepsi aynı Türkçe durum
     etiketlerini ve "açık/kapalı Level" mantığını taşır. 24 yeni test
     (`tests/test_pattern_state.py`) 5 ucu (confirmed/retest_hold/
     target_reached/invalidated/expired) + confirm_bars semantiği +
     born_idx ofseti + extra_payload birleşimini sentetik dizilerle doğrular.
  2. **`patterns_geom.py::diverging_lines`** (YENİ) — `converging_lines`'ın
     tersi (broadening/megafon için): apex/slope_ratio YOK, yalnızca
     created_idx'te gap pozitif VE zamanla büyüyor mu. 5 yeni test.
  3. **`wedge.py`** — `trendlines.build_trendlines`'ın resistance/support
     aday havuzundan her (upper,lower) çiftini `converging_lines`/
     `classify`'a verir; falling_wedge/asc_triangle->long (break_line=üst),
     rising_wedge/desc_triangle->short (break_line=alt), sym_triangle
     YÖNSÜZ (her iki yön bağımsız izlenir). Ek filtreler: `min_pivots`,
     `min_bars`, `max_apex_bars` (+ EXPIRED eşiği = apex mesafesinin %80'i),
     `slope_ratio_range`. Aday havuzu zamanlaması (`price_structure`/
     `trend.breakouts` ile AYNI sorun) nedeniyle `register_verified_
     elsewhere` kullanır. 15 yeni test (11 birim — `_normalized_ratio`/
     `_passes_shape_filters`/`_direction_candidates` saf fonksiyonlar
     doğrudan test edildi — + gerçekçi/gürültülü veride sözleşme testi).
  4. **`head_shoulders.py`** — `hs_pattern.py::find_hs`'in sarmalayıcısı,
     `swings.alternate_pivots` (yalnızca kesinleşmiş pivotlar) kullandığı
     için generic `Registry.register()`'a TEMİZ kaydolur. **GERÇEK hata
     bulundu**: PENDING doğum barı olarak `HSPattern.created_idx`
     (=`l3.confirmed_idx`) KULLANILMADI — doğrusu `hs.l3.finalized_idx`
     (`GoldenZoneIndicator`'ın "A onay barında DEĞİL finalized_idx'inde
     doğar" kararıyla AYNI gerekçe: l3, `confirmed_idx` ile `finalized_idx`
     arasında hâlâ daha ekstrem bir pivotla değiştirilebilir — `created_idx`
     kullanmak walk-forward'da gerçek bir repaint olurdu). Elle inşa edilmiş,
     gerçek `find_pivots`/`alternate_pivots`/`find_hs` çalıştırılarak
     doğrulanmış bir TOBO senaryosuyla hem bu düzeltme hem `repaint_test`
     PASS'i kilitlendi. 7 yeni test.
  5. **`flag_pennant.py`** — direk tespiti `zones_sd.py::find_impulses`'in
     DOĞRUDAN yeniden kullanımı (Faz 8C'de zaten vardı, yeni hesap YOK);
     konsolidasyon kanalı `trendlines`'ın pivot aday havuzuyla DEĞİL, direk
     sonrası SABİT `flag_min_bars` pencereye numpy OLS fit edilerek kurulur
     (born barında dondurulur, `weekly_channel`'ın `channel_frozen_*`
     felsefesiyle aynı) — bu yüzden `register_verified_elsewhere` kullanır
     (aday havuzu YOK ama "dondurulmuş overlay" istisnası). Bayrak/flama
     ayrımı basit bir geometrik sezgi (kitap referansı YOK, docstring'de
     belirtildi). 3 yeni test (elle inşa edilmiş direk+bayrak senaryosu dahil).
  6. **`double_top_bottom.py`** (K1 TWYS eki) — `alternate_pivots`
     zigzag'inden aynı türden ardışık (p1,p2) + aralarındaki TEK zıt-türde
     "boyun" pivotu; `p2.finalized_idx`'te PENDING doğar (AYNI GoldenZone/
     HeadShoulders gerekçesi). Generic `Registry.register()`'a TEMİZ
     kaydolur. Elle inşa edilmiş, gerçek pivot/zigzag çalıştırılarak
     doğrulanmış bir çift-dip senaryosuyla 7 yeni test + `repaint_test` PASS.
  7. **`broadening.py`** — `wedge.py` ile AYNI aday havuzu mimarisi, tek
     fark `diverging_lines` (apex YOK). Yön YOKSUZ (sym_triangle gibi HER
     İKİ yön bağımsız izlenir); `top`/`bottom` etiketi YALNIZCA açıklayıcı
     bir bağlamsal sezgi (`prior_trend_lookback` bar önceki kapanışa göre
     önceki trend yönü) — sinyal üretimini ETKİLEMEZ, TASARIM KARARI olarak
     belgelendi. `register_verified_elsewhere` kullanır. 3 yeni test.
  8. **Registry/CLI** — `bootstrap.py::CATALOG`'a 6 yeni girdi
     (`patterns.wedge`/`triangle`/`head_shoulders`/`flag_pennant`/
     `double_top_bottom`/`broadening`), yeni `"patterns"` kategorisi.
     `config/scans.yaml`'a 3 yeni preset: `tobo_onay`, `cift_tepe_dip`,
     `takoz_bayrak`.
  Gerçek veri smoke: yerel BIST parquet önbelleğinden (ilk 80 sembol
  taranarak) HER 5 formasyon için en az bir GERÇEK "confirmed" örneği
  bulundu (BAKAB: TOBO+OBO+bayrak/flama; BRSAN: takoz; BARMA: genişleyen
  formasyon). BAKAB'ın `patterns.head_shoulders` grafiği `tlab plot`
  ile üretildi (`outputs/galeri/patterns_head_shoulders_BAKAB.png`,
  gitignored) — SOL OMUZ/BAŞ/SAĞ OMUZ etiketleri, boyun çizgisi, hedef
  seviyesi ve TOBO/OBO [ONAY/GEÇERSİZ/HEDEFE ULAŞTI] markerları doğru
  görünüyor (birden fazla ardışık formasyon aynı grafikte üst üste
  bindiği için görsel yoğunluk var — bu turun kapsamı görsel cila DEĞİL,
  mantık doğruluğu; declutter gerekirse ayrı bir takip işi).
  51 yeni test (388→439). `pytest -q -m "not network"` 439/439 yeşil,
  `ruff check`/`mypy` yeni dosyalarda temiz, `lint_lookahead` 2 uyarı
  (BASELINE İLE AYNI, ilgisiz). GİT'E COMMIT/PUSH EDİLDİ (bkz. `git log`).
- **Faz 8B görsel düzeltmesi + gerçek `IndicatorResult.from_json()` hatası +
  Streamlit tarama panosu** (2026-08-30, Faz 8B'nin HEMEN ardından, kullanıcı
  BAKAB grafiğini inceleyip "hâlâ karışık, sadece gerçek OBO/TOBO noktaları
  gösterilmeli, harmonikler gibi net çizilmeli" dedikten sonra — AYNI mesajda
  "artık bir ekran görmek, orada tarama yapmak, sinyal gelen hisseleri
  listeleyip grafiğiyle görmek istiyorum" talebi de geldi, İKİSİ de bu turda
  ele alındı, sıradaki fazlardan (8D) ÖNCE):
  1. **Görsel düzeltme** — `renderer.py::_filter_confirmed_patterns()`
     (YENİ): `patterns.*` indikatörleri için yalnızca `last_state`'i
     confirmed/completed olan pattern_id'lerin Box/Line/Level/Marker'ları
     çizilir; pending/invalidated/expired denemeler TAMAMEN elenir
     (`declutter=True` iken, `--show-all` ile eski davranışa dönülebilir).
     Eşleştirme Marker'larda `kind` üzerinden (outcome marker'lar zaten
     `"pattern_{state}"` taşıyor); Line/Box/Level'larda `label`in
     `pattern_id` (ya da wedge/broadening'in yönsüz `pattern_key`'i) ile
     eşleşmesi üzerinden. Vertex marker'lar (SOL OMUZ/BAŞ/SAĞ OMUZ, çift
     tepe/dip "1"/"2") artık `kind="pattern_vertex:{pattern_id}"` taşıyor
     (filtre için) VE harmonik X/A/B/C vertex'leriyle AYNI halo'lu
     (bgcolor) düz-metin stilini kullanıyor (`_draw_markers`'a yeni dal).
     Outcome marker'lar (`pattern_confirmed`→accent, `pattern_completed`→
     yeşil) harmonik `confirmed` durumuyla AYNI kalın/kutulu/ok'lu
     muameleyi alıyor. `themes.py`/`labels_tr.py`'ye yeni stil eşlemeleri
     (`pattern_boundary`→muted, `pattern_target`→accent, `pattern_pole`→
     turuncu + Türkçe karşılıkları "Sınır/Boyun"/"Hedef"/"Direk") — eskiden
     ham `style` adı ("pattern_boundary") çıplak metin olarak sızıyordu.
     2 yeni test (`tests/test_viz/test_renderer.py`). Doğrulama: BAKAB'ın
     `patterns.head_shoulders` grafiği yeniden üretildi — artık yalnızca
     2 TOBO (tamamlandı) + 1 OBO (retest tuttu) + 1 OBO (tamamlandı) net
     görünüyor, eskiden ekranı dolduran ~6+ geçersiz/beklemede deneme gitti.
  2. **GERÇEK hata — `IndicatorResult.from_json()`** (bu turda, Streamlit
     panosuna GERÇEK bir tarama sonucu doldururken, `ProcessPoolExecutor`
     üzerinden 80 sembol/tüm indikatörler çalıştırılırken tetiklendi):
     `_series_from_json`'ın eski sürümü fiyat-indeksli mi zaman-indeksli mi
     kararını yalnızca serinin İLK anahtarının `pd.Timestamp` olarak
     ayrıştırılıp ayrıştırılamadığına bakarak veriyordu. Ama `pd.Timestamp`
     son derece esnek: bir fiyat değerinin string hâli (ör. `"2026.5"`)
     RASTLANTISAL olarak geçerli bir tarihe (`"2026-05-01"`) ayrıştırılabilir
     — serinin İLK anahtarı böyle "yanlışlıkla" geçince fonksiyon TÜM
     anahtarları Timestamp sanıp, aynı (fiyat-indeksli) serideki BAŞKA bir
     anahtarda (`"4749.375"`, ayrıştırılamıyor) yakalanmamış bir
     `DateParseError`le çöküyordu. Faz 6'nın kendi testi (`vp_bins` için
     `[10.5, 11.93..., 13.2]`) bu senaryoyu YAKALAMAMIŞTI çünkü o
     fixture'daki HİÇBİR anahtar (ilk dahil) rastlantısal olarak
     ayrıştırılmıyordu. Düzeltme: karar artık içerik sezgisi YERİNE serinin
     ADI kullanılıyor (`vp_` öneki — zaten `IndicatorResult.series_layout`
     docstring'inde dokümante edilmiş TEK doğru sözleşme, `_series_from_json`
     artık `name` parametresi alıyor). 1 yeni regresyon testi
     (`tests/test_core_types.py`, `[2026.5, 4749.375]` anahtarlarıyla —
     gerçek hatayı BİREBİR yeniden üretir). **Bu hata Faz 8B'ye özgü
     DEĞİL** — `structure.price_structure`'ın `vp_*` serilerini taşıyan HER
     tarama, tesadüfen bu şansız anahtar kombinasyonuna denk gelirse aynı
     şekilde çökerdi; yalnızca bu turda GERÇEK çoklu-sembol bir tarama ilk
     kez tetikledi (önceki tüm testler/registry bootstrap'ı küçük/sentetik
     veriyle çalışıyordu).
  3. **`tlab/dashboard.py` (YENİ) — Streamlit tarama panosu**: `tlab
     dashboard` (yeni CLI komutu, `streamlit run` sarmalayıcısı) ile açılır.
     Tek sayfa: kenar çubuğunda piyasa seçimi + "🔄 Bugünü Tara" butonu
     (`run_eod()`'u doğrudan çağırır, `force` checkbox'ıyla yeniden
     koşulabilir) + run seçici (`ResultsStore.list_runs`) + kategori/durum/
     yön filtreleri; ana alanda metrik kartları (tarama tarihi, taranan
     sembol, aktif sinyal, `ResultsStore.diff()`'ten yeni sinyal sayısı) +
     REPAINT ALARM banner'ı (varsa) + tıklanabilir bir sinyal tablosu
     (`st.dataframe(..., on_select="rerun")`) — bir satıra tıklayınca ALTINDA
     `render_live()` ile o sinyalin grafiği açılır. Ayrıca "Hızlı bakış"
     bölümü (sinyal listesinden bağımsız, herhangi bir sembol/indikatör/tf
     için grafik). **Mimari kararlar**: (a) `signals` tablosu her durum
     geçişini AYRI satır tutar (non-repaint geçmiş) — pano her (sembol, tf,
     indikatör, pattern_id) zinciri için yalnızca EN GÜNCEL satırı gösterir
     (`_rows_to_frame`, `detected_at`e göre `drop_duplicates`); "tüm
     geçmiş" hâlâ `tlab signals` CLI'sında. (b) varsayılan filtre yalnızca
     confirmed/completed gösterir (görsel düzeltmedeki AYNI ilke, "gerçek
     sinyal" ile "henüz/artık değil" ayrımı) — "Tüm durumları göster" ile
     açılabilir. (c) `ResultsStore` (sqlite3) HER script koşusunda TAZE
     açılıp kapanır, `st.cache_resource` KULLANILMAZ — Streamlit'in çoklu-
     oturum modeli sqlite bağlantılarını thread'ler arası paylaşmayı
     yasaklıyor, yerel/tek-kullanıcı ölçekte açma/kapama maliyeti ihmal
     edilebilir. `pyproject.toml`'a `streamlit` bağımlılığı eklendi. 3 yeni
     test (`tests/test_dashboard.py`, `streamlit.testing.v1.AppTest` ile —
     izole `tmp_path`'te sahte bir `ResultsStore` dolduruluyor, kullanıcının
     GERÇEK `outputs/results.db`'sine HİÇ dokunulmuyor). **DÜRÜST NOT**:
     "Bugünü Tara" `run_eod()`'u SENKRON çağırır (tam evren veri güncellemesi
     dahil — büyük evrende dakikalar sürebilir, buton bu süre boyunca
     Streamlit'i bloklar, kabul edilebilir görüldü çünkü günde bir kez
     manuel tetiklenen bir işlem); GERÇEK otomatik ("her gün kapanışta
     kendiliğinden") zamanlama hâlâ İşletim sistemi görev zamanlayıcısı
     (Windows Görev Zamanlayıcı/cron, `tlab eod` komutunu çağıracak şekilde
     — README.md'de örnek var) gerektirir, bu oturumun kapsamı DIŞINDA
     (panoyla birlikte KULLANILMASI ÖNERİLEN, ayrı bir kurulum adımı).
  6 yeni test (439→445: 2 görsel + 1 from_json regresyonu + 3 dashboard).
  `pytest -q -m "not network"` 445/445 yeşil, `ruff check`/`mypy` yeni
  dosyalarda temiz (repo geneli hâlâ 18 ruff/2 lint_lookahead, BASELINE
  İLE AYNI). Gerçek doğrulama: yerel önbellekten 80 BIST sembolü/context-
  gerektirmeyen TÜM indikatörlerle (harmonik×8, structure×4, trend×2,
  patterns×6 — 1D) gerçek bir tarama koşulup `outputs/results.db`'ye
  bugünün run'ı olarak yazıldı (1600 sonuç, 160 hata — çoğu veri eksikliği/
  kısa seri, `from_json` hatası DEĞİL, düzeltmeden SONRA hiç çökme
  olmadı) — pano bu gerçek run üzerinde de gözle doğrulandı.

- **Görselleştirme — "aracı kurum raporu" tasarımının GERİ ALINMASI +
  harmonik çoklu-aday temizliği (2026-08-31, kullanıcının "şu ana kadar
  incelediğim tüm görseller rezalet... hevesim kaçtı" geri bildirimine
  yanıt):** TAMAMLANDI. Kök neden teşhisi: önceki oturumların "aracı kurum
  raporu" masthead/kart-çerçevesi/dipnot tasarımı (2026-08-29) kullanıcının
  KENDİ referans ekran görüntülerinden (`images/`) DEĞİL, hayali bir
  "kurumsal broker" estetiğinden esinlenmişti — kullanıcı bu turda `images/`
  klasöründeki TÜM görselleri (10 dosya: harmonik/swing-fib/pair/tablo/kitap
  örneği) tek tek incelettirip "bunlarla birebir aynı olacak şekilde
  güncelle, karmaşıklık istemiyorum artık" dedi. Referans görsellerin ORTAK
  dili: BEYAZ zemin, TEK satırlık düz metin başlık (sağ-hizalı fiyat/değişim
  bloğu YOK, accent ayraç çizgisi YOK, dipnot YOK, dış "kart" çerçevesi YOK),
  her harmonik grafiğin TAM OLARAK TEK bir üçgen çifti (XAB+BCD) göstermesi.
  1. **Masthead sadeleştirmesi** (`renderer.py`) — `_Header` artık yalnızca
     `symbol`/`subtitle` taşır (eski `value_str`/`change_str`/
     `change_positive`/`highlighted`/`date_str` alanları SİLİNDİ);
     `_draw_header` TEK satırlık `"{sembol} - {açıklama}"` yazıyor.
     `_draw_card_frame` (tüm figürü saran dış çerçeve) TAMAMEN SİLİNDİ;
     `_draw_footer` (dipnot şeridi) jenerik/harmonik `_apply_layout`'tan
     ARTIK ÇAĞRILMIYOR (fonksiyonun kendisi pair modu için hâlâ duruyor —
     kullanıcı pair grafiğini zaten AYRI bir turda onaylamıştı, dokunulmadı).
     `_MARGIN_T` 112→56, `_MARGIN_B` 60→40 (daha az şerit alanı gerekiyor).
     `_last_close_change`/`_category_tr` artık kullanılmadığı için SİLİNDİ
     (görev metninin "emin olduğun şeyi tamamen sil" ilkesi). `_draw_panel_
     frames` (her alt panelin KENDİ ince çerçevesi) KORUNDU — referans
     165109 bunu açıkça gösteriyor.
  2. **GERÇEK hata — harmonik grafikler TEK bir aday YERİNE onlarca üst
     üste binen üçgen gösteriyordu**: `_draw_polygons` hiçbir filtre
     UYGULAMADAN `result.polygons`taki HER adayın üçgenini çiziyordu
     (yalnızca köşe etiketleri/D kutusu `_MAX_HARMONIC_MARKERS=3` ile
     kısıtlıydı, üçgen ŞEKİLLERİNİN KENDİSİ değil) — bu, kullanıcının "şu
     ana kadar incelediğim tüm görseller rezalet" değerlendirmesinin en
     somut kanıtıydı (ACSEL/Navarro200 örneğinde önceki oturumda not
     edilen "saçma bir çizim ekrana sığmamış" şikayetinin kök nedeni de
     BUYDU). Yeni `_filter_harmonic_result()` (patterns.*'ın `_filter_
     confirmed_patterns`'ıyla AYNI mimari desen) `declutter=True` iken
     `_render_price_based`'in İLK adımında TEK GEÇERLİ (aktif/tamamlanmış,
     `_HARMONIC_VISIBLE_STATES`) VE en güncel adayın polygon/level/line/
     marker'ları DIŞINDA HER ŞEYİ TAMAMEN BUDAR (beklemede/geçersiz/süresi
     dolmuş bir deneme artık üçgen dahil HİÇ ÇİZİLMEZ — eskiden yalnızca
     D-kutusu/köşe etiketi kısıtlıydı, PRZ/fib/X-B ÇİZGİLERİ hiç
     filtrelenmiyordu). `_MAX_HARMONIC_MARKERS` 3→1. `_draw_polygons`/
     `_draw_harmonic_vertices` artık kendi başlarına HİÇBİR seçim yapmıyor
     (yalnızca `result`te ne kaldıysa çiziyor) — seçim TEK bir yerde.
  3. **İKİNCİ gerçek hata (yukarıdaki düzeltmeyi A1YEN/Pesavento gerçek
     verisiyle doğrularken bulundu) — başlık YANLIŞ adayı tarif ediyordu**:
     `_build_subtitle`, `result.last_state`in SON dict girdisini (`next(
     reversed(...))`) kullanıyordu — bu, FİİLEN ÇİZİLEN aday ile AYNI olmak
     ZORUNDA değildi (en son eklenen aday geçersiz çıkıp filtre bir ÖNCEKİ,
     hâlâ geçerli adayı seçtiğinde). Sonuç: grafik "D: 2.5392 [TAMAMLANDI]"
     net bir üçgen gösterirken başlık "[GEÇERSİZ]" diyordu — kullanıcının
     TAM OLARAK şikayet ettiği "indikatörde ne olduğunu başında yazmasa
     anlamayacağım" sorununun BİREBİR kanıtı. Düzeltme: yeni `_shown_
     harmonic_pid()` pid'i `last_state`ten DEĞİL, FİİLEN çizilen (filtrelenmiş)
     `result.polygons`tan türetir; `_build_subtitle` artık bunu kullanıyor.
     Ayrıca eşleşme SAYISI ("— N eşleşme") kaldırıldı (referans görsellerin
     hiçbiri saymıyor, "— Tarama eşleşmesi" ile değiştirildi).
  4. **Alt başlık metinleri referansa yakınlaştırıldı** — `_INDICATOR_
     EXPLAIN_TR`e `structure.swing_fib_abcd`→"Swing Yapısı, Fibonacci ve
     AB=CD Analizi" (referans 203913 ile birebir), `structure.
     price_structure`→"Fiyat Yapısı — Destek/Direnç, Trend Çizgileri, Hacim
     Profili", ve 6 `patterns.*` indikatörü için Türkçe formasyon adları
     eklendi (eskiden İngilizce sınıf adının title-case'i sızıyordu, ör.
     "BAKAB - Head Shoulders").
  5. `render_structure_report`'un masthead override'ı da aynı sadeleştirmeyi
     miras aldı (`_category_tr` çağrısı kaldırıldı, "Birleşik Rapor (Yapı +
     Swing/Fibonacci)" artık kategori öneki OLMADAN).
  Doğrulama: `outputs/galeri/`'deki TÜM tekil-sembol görseller (8 harmonik
  ekolü + 3 pair + 6 structure/trend/patterns) yeniden üretildi, İKİ tur
  (A1YEN/Pesavento, ACSEL/Navarro200, TCELL/swing_fib_abcd, TCELL+ASELS+
  THYAO/structure.report, BAKAB/head_shoulders) gözle TEK TEK karşılaştırıldı
  — hepsinde artık tek satırlık düz başlık, dış çerçeve/dipnot yok, harmonik
  grafiklerde TEK bir net üçgen çifti + doğru durum etiketi var. 1 test
  güncellendi (`test_panel_frames_drawn_around_each_subplot`, kart çerçevesi
  kaldırıldığı için beklenen sayı `n_axis_pairs+1`'den `n_axis_pairs`'e
  düştü) — yeni test EKLENMEDİ (bu tur saf bir tasarım/declutter düzeltmesi,
  davranış sözleşmesi zaten mevcut testlerle örtüşüyor). `pytest -q -m "not
  network"` 445/445 yeşil, `ruff check tlab/ tests/` 18 hata (BASELINE İLE
  AYNI). **DÜRÜST NOT — kaldığı yer**: (a) çok dar bir fiyat bandında
  (`structure.report`'ta "confluence" bölgeleri, ör. TCELL Ağustos 2026)
  hâlâ HAFİF metin yakınlığı var — bu, önceki oturumların "tek geçişli
  açgözlü sezgi" sınırlamasının aynısı, bugün ELE ALINMADI; (b) harmonik
  pencere sonu hâlâ `born_time + 60 bar` sabit payı kullanıyor — bazı
  örneklerde (A1YEN/Pesavento) pattern tamamlandıktan sonra hâlâ epey boş
  alan kalıyor, referans kadar sıkı değil, ayrı bir ince ayar konusu;
  (c) ACSEL/Navarro200'de "PRZ Üst"/"PRZ Alt" etiketleri grafiğin üst kenar
  boşluğuna hafif taşıyor (y-ekseni autorange, harmonik `bounds` hesabına
  PRZ Level'ları dahil edilmemiş olabilir) — küçük bir kalan kusur, bugünün
  kapsamı DIŞINDA bırakıldı. Kullanıcı galeriyi tekrar incelemeli.
- **Faz 8D — alpha_rank, momentum_rank, ma_systems, ewmac + "universe" kategorisi**
  (2026-08-31): TAMAMLANDI. Kullanıcının verdiği görev metni master prompt'un 14.
  bölümünden alıntıydı (bu proje, önceki oturumda bir "master prompt" referans
  ediyordu ama tam metni repoda yoktu — bu oturumda kullanıcı ilgili bölümü
  doğrudan yapıştırdı).
  1. **YENİ mimari — `UniverseIndicator`** (`tlab/core/indicator.py`): `alpha_rank`/
     `momentum_rank`'ın `rank_pct`'i TANIM GEREĞİ tüm evrenin AYNI bardaki
     skorlarını BİRLİKTE görmeyi gerektirdiği için `BaseIndicator.compute(df,
     context)`'in tekil-sembol imzasına UYMAZ — `BaseIndicator`'dan TÜREMEYEN
     kardeş bir ABC eklendi: `compute_universe({sembol: df}, index_df) ->
     {sembol: IndicatorResult}`. Ortak doğrulama mantığı (`_validate_indicator_
     result`) iki sınıf arasında paylaşılacak şekilde serbest fonksiyona
     çıkarıldı. `IndicatorSpec`'e `needs_universe: bool` eklendi (`needs_context`
     ile AYNI desen); `scanner/engine.py::run()`'a ÜÇÜNCÜ bir iş kuyruğu
     (`jobs_universe`) eklendi — evren sembol-sembol PARÇALANMAZ, her (indikatör,
     tf) için TEK bir `ProcessPoolExecutor` işi (`_run_universe_worker`) tüm
     evren + endeksi çeker, indikatörü BİR KEZ çağırır, dönen `{sembol:
     IndicatorResult}`'ı `_universe_result_to_runs()` ile motorun geri kalanının
     (ResultsStore/diff/dashboard) beklediği DÜZ `IndicatorRunResult` listesine
     açar — bu satırdan SONRASI hiçbir yerde universe/tekil ayrımı GEREKMEDİ
     (persist/diff/CLI `scan`/`eod` sıfır değişiklikle çalıştı).
  2. **Endeks verisi** (`tlab/data/universe.py::BENCHMARK_SYMBOL`) — XU100
     (BIST) / ^NDX (NASDAQ). Provider/Store'a HİÇBİR özel kod EKLENMEDİ: endeks
     sıradan bir sembol gibi `to_provider_symbol()`'dan geçip (XU100->XU100.IS)
     aynı parquet cache mekanizmasıyla saklanıyor.
  3. **`tlab/indicators/momentum/alpha_rank.py::AlphaRank`** — her sembol için
     `xsec.rolling_alpha_beta`'yı `windows=(60,120,250)` her birinde çalıştırır;
     sıralama skoru = pencereler arası ORTALAMA t_stat (TASARIM KARARI: ölçek-
     bağımsız olduğu için alpha_ann'dan daha uygun birleştirme — master prompt
     tam formül vermiyordu). `persistence` = 1-|fip(aktif_getiri,window)| (`fip`
     Faz 2-EK'te TAM BU AMAÇLA yazılmıştı, docstring'i zaten işaret ediyordu).
     Likidite filtresi (`min_liquidity_try`) ZAMANA GÖRE DEĞİŞİR (rolling
     ortalama ciro eşiğin altındaysa o BARDA skor NaN'a çevrilip o barın
     sıralamasından çıkar) — sabit/tek seferlik bir filtre DEĞİL. Cross-sectional
     `rank_pct`: tüm sembollerin skor serileri `pd.concat({sembol: seri}, axis=1)`
     ile TEK matriste toplanır (ilk taslak `score_df[sembol] = ...` döngüsüyle
     sütun sütun dolduruyordu — 648 sembollük GERÇEK evrende pandas
     "highly fragmented DataFrame" performans uyarısı verdi, `pd.concat`'e
     çevrilip düzeltildi), her SATIR için `pandas.rank(axis=1, ascending=False,
     pct=True)` (xsec.rank_pct'in AYNI "en iyi->en küçük pct" yönü, vektörize
     hâli). Sinyaller: `alpha_entry`/`alpha_exit` (rank_pct top_pct eşiğine
     giriş/çıkış). Tekil görsel: 4 panel (hisse-vs-endeks normalize, α_yıllık+
     t-istatistiği+±2 anlamlılık bandı, β, kümülatif artık getiri ε) — YENİ
     renderer kodu GEREKMEDİ, `IndicatorResult.series_layout` (Faz 7'den beri
     var olan mekanizma) doğrudan kullanıldı.
  4. **`tlab/indicators/momentum/momentum_rank.py::MomentumRank`** — `xsec.
     momentum_horizons` (12-1 tarzı, `skip` ile son barı dışlar) + vol-ayarlı
     momentum (`realized_vol*sqrt(ufuk)`'a bölünür — TASARIM KARARI, kaba bir
     "Sharpe benzeri" normalizasyon) + `_rolling_trend_tstat` (YENİ, bu modülde
     — `rolling_alpha_beta`'nın AYNI kapalı-form OLS formülleri ama y=RS,
     x=bar_indeksi; zamana karşı rolling eğim+t-istatistiği) + `fip` (getiri
     tutarlılığı) + `trend_score` (close/EMA20/EMA50/EMA200 sıralaması + eğim
     işaretleri, 5 koşulun ortalaması). Skor = vol-ayarlı momentum ortalaması +
     trend_score - |fip| (TASARIM KARARI, basit toplam — master prompt ağırlık
     vermiyordu). Sinyaller: `momentum_top_entry`/`_exit` (AYNI rank_pct
     deseni) + `rs_breakout` (RS'nin ÖNCEKİ `rs_breakout_window` barın KESİN
     üstüne çıkması — bugünün barı hariç trailing maksimuma göre, gerçek "yeni
     zirve"). `momentum_heatmap_data()`: sektör × ufuk ortalama HAM momentum
     matrisi (`config/sectors_bist.yaml`'dan, salt biçimlendirme — yeni hesap
     yok), `tlab/viz/universe_charts.py::render_momentum_heatmap` bunu ısı
     haritasına çevirir.
  5. **`tlab/indicators/trend/ma_systems.py::MASystems`** — periyotlar
     (varsayılan 8/21/55/200, `ema`/`sma`/`kama`/`hull` seçilebilir) arası
     ardışık kesişim (`ma.crossovers`), "ribbon" sıralama durumu (`bull_stack`/
     `bear_stack`/`mixed` — close + tüm MA'ların göreli sırası), bant genişliği
     (max-min MA farkı/close) kendi rolling `quantile`'ının ALTINA düşünce
     `is_squeeze`, oradan ÇIKIŞ `squeeze_expansion` sinyali üretir. **GERÇEK
     hata (yazarken)**: `_stack_state`'te `zip(values, values[1:], strict=True)`
     — `strict=True` bu ikili (pairwise) karşılaştırma deseninde YANLIŞ (iki
     liste TANIM GEREĞİ farklı uzunlukta, `ValueError` fırlatıyordu); `strict=
     False`'a düzeltildi. **Kayıt istisnası**: her MA'nın TAM (büyüyen) serisi
     tek bir `Line` overlay'i olarak taşınıyor (`weekly_channel`'ın
     `channel_current`'ıyla AYNI kategori — generic `repaint_test`'in
     `(points,label)` tam-eşitliği bunu yanlış alarm sanıyor); `register_
     verified_elsewhere` kullanılır, sinyallerin GERÇEK non-repaint'liği
     hedefli bir testle (her kesim noktasında üretilen sinyaller = tam koşunun
     o ana kadarki sinyalleri) ayrıca doğrulanır.
  6. **`tlab/indicators/trend/ewmac.py::EWMACIndicator`** — Carver'ın (Systematic
     Trading) standart geometrik çift kümesi (2,8)/(4,16)/(8,32)/(16,64)/
     (32,128)/(64,256) — bu kısım kamuya açık/genel bilgi. **DÜRÜST NOT/TODO**:
     `forecast_scalar` kitaptan (bilgi-bankasi/teknik/11 — K3, HENÜZ
     ÇIKARILMADI, bu oturumda kontrol edildi, dosya yok) doğrulanmış SABİT
     değerler yerine EMPİRİK olarak (trailing `abs(vol_adj_ewmac)` ortalamasının
     tersi × hedef 10) hesaplanıyor — görev metninin AÇIKÇA verdiği "K3
     bitmediyse Carver standart çiftlerini kullan ve TODO bırak" talimatına
     göre; memorized/tahmini sabit sayılar (ör. belirli bir forecast scalar
     tablosu) BİLEREK kullanılmadı (doğrulanamayan "kitaptan" rakam uydurma
     riski). `series["ewmac_combined"]` (Faz 10 forecast katmanının İLK gerçek
     üreticisi) sıfırı kestiğinde `ewmac_bullish`/`ewmac_bearish` sinyali.
  7. **`tlab/features/ma.py::kama()`** — Kaufman Adaptive MA (verimlilik oranı +
     hızlı/yavaş smoothing constant, özyinelemeli ama yalnızca t-1 ve öncesini
     kullanır). `ma_systems.py`'nin `ma_type="kama"` seçeneği bunu kullanır.
  8. **CLI/Registry/scans.yaml** — `tlab list-indicators` artık "(evren-geneli)"
     etiketini gösteriyor; YENİ `tlab universe-plot --indicator momentum.
     alpha_rank|momentum_rank` (α-β saçılımı / sektör×ufuk ısı haritası,
     `tlab/viz/universe_charts.py`, YENİ dosya — `renderer.py`'ye dokunulmadı,
     bu evren-geneli görseller `IndicatorResult`+df yerine `{sembol:
     IndicatorResult}` sözlüğü üzerinde çalıştığı için AYRI bir modül).
     `populate_registry()`: universe indikatörleri `register_verified_elsewhere`
     ile kaydolur (repaint_test'in `compute(df,context)` imzasıyla UYUMSUZ);
     GERÇEK non-repaint sözleşmesi YENİ `tlab/testing/repaint.py::
     universe_repaint_test()` ile (evrenin HER df'i + endeks AYNI cut_time'da
     kesilir, kesik ⊆ tam) doğrulanır. `config/scans.yaml`'a `alpha_top`/
     `momentum_top` preset'leri eklendi.
  9. **GERÇEK HATA — `tlab plot` universe indikatörlerini render EDEMİYORDU**
     (gerçek veriyle ilk denemede bulundu): `viz/live.py::compute_live()`
     tüm katalog indikatörlerinin `instance(df)` (tekil `BaseIndicator`
     çağrısı) ile çalıştığını varsayıyordu — `UniverseIndicator.__call__()`
     FARKLI bir imza istediği için `TypeError` fırlatıyordu. Düzeltme:
     `compute_live()`'a `spec.needs_universe` dalı eklendi — TEK bir sembolün
     "tekil" grafiği bile evrenin TAMAMININ (configured universe + endeks)
     hesaplanmasını gerektiriyor (rank_pct'in doğası gereği), sonuçtan yalnızca
     istenen sembol seçilip standart `render()`'a veriliyor. **DÜRÜST NOT**:
     bu yüzden `tlab plot --indicator momentum.*` diğer TÜM indikatörlerden
     ÇOK daha yavaş (648 sembollük gerçek BIST evreninde ~22-30s) — `tlab
     universe-plot` zaten AYNI maliyeti taşıyordu, burada yalnızca tek sembol
     seçiliyor; tekrarlı/interaktif kullanım için önbellekleme YAPILMADI
     (ayrı bir olası iyileştirme).
  10. **GERÇEK HATA — α-β saçılımında 500+ sembol etiketi üst üste biniyordu**
      (584 sembollük gerçek evrenle ilk render'da görüldü, `outputs/samples/
      alpha_scatter_bist.png` gözle incelendi): TÜM sembollere metin etiketi
      eklemek yoğun bir merkez kümesinde okunaksız oluyordu. Düzeltme: iki
      ayrı Scatter trace'i — evrenin geri kalanı ETİKETSİZ nokta bulutu
      (hover'da tam bilgi kalır), yalnızca `top_pct` içindeki (altın) semboller
      etiketlenir.
  11. **Testler** — 29 yeni (445→474): `tests/test_ma.py` (+2, KAMA), `tests/
      test_momentum/` (YENİ paket: `fixtures.py` — 20 sembollük, BİLİNEN
      alfa/momentum gradyanlı sentetik evren üreticisi; `test_alpha_rank.py`/
      `test_momentum_rank.py` — Spearman korelasyonuyla sıralama doğruluğu
      + likidite filtresi + `compute_universe`'in evrenin ALT KÜMESİ döndürme
      sözleşmesi; `test_universe_repaint.py` — `universe_repaint_test` ile),
      `tests/test_trend/test_ma_systems.py`/`test_ewmac.py`, `tests/
      test_universe_indicator.py` (`UniverseIndicator` ABC sözleşmesi, sahte
      bir `_EchoIndicator` ile), `tests/test_scanner/test_engine_universe.py`
      (`_run_universe_worker`/`_universe_result_to_runs`, `_fetch_and_prepare`
      monkeypatch'lenerek — gerçek ağ/cache GEREKMEZ), `tests/test_viz/
      test_universe_charts.py`, `tests/test_scanner/test_bootstrap.py`
      (+2, yeni kategori/needs_universe kontrolü).
  12. **GERÇEK VERİYLE UÇTAN UCA DOĞRULAMA** (bu oturumda, sentetik testlerin
      ÖTESİNDE): XU100 (D1) ilk kez indirilip cache'lendi (`tlab update-data
      --market bist --symbols XU100 --tf 1d` — **not**: `--tf 1h` yfinance'ın
      "60m veri yalnızca son ~730 gün" kısıtına takıldı, önceki oturumlarda
      da gözlenen AYNI sağlayıcı kısıtı, bu göreve AİT DEĞİL). 60 sembollük
      bir alt evrende `tlab scan --indicators momentum.alpha_rank,momentum.
      momentum_rank,trend.ma_systems,trend.ewmac` (122 iş, 234 sonuç, 0 HATA)
      ve `--preset alpha_top`/`momentum_top` (57 sonuç, 0 hata, filtre gerçek
      sinyal sayıları üretti) çalıştırıldı. `tlab plot` ile EREGL için 4
      indikatörün TEKİL grafiği (`outputs/samples/{alpha_rank,momentum_rank,
      ma_systems,ewmac}_EREGL.png`) ve `tlab universe-plot` ile TAM 584-648
      sembollük gerçek evrende α-β saçılımı + sektör×ufuk ısı haritası
      üretilip GÖZLE incelendi — hepsi görsel olarak tutarlı/anlamlı (ör.
      EREGL β≈1.0-1.1, pozitif kümülatif ε, EWMAC forecast trend yönüyle
      uyumlu, DemirÇelik sektörü 252 günlük ufukta güçlü pozitif momentum).
      Bu, projedeki İLK universe-level indikatör turunda gerçek veriyle
      doğrulama yapılan oturum (önceki fazların çoğu gerçek veri smoke testini
      ZATEN standart pratik olarak uyguluyordu, burada da aynı disiplin
      korundu).
  **DÜRÜST NOT — bilinen sınırlamalar**: (a) skor birleştirme formülleri
  (alpha_rank: ortalama t_stat; momentum_rank: vol_adj_mom+trend_score-|fip|)
  master prompt'ta VERİLMEMİŞ TASARIM KARARLARI, geriye-dönük optimize
  EDİLMEDİ; (b) `min_liquidity_try` varsayılanı (5M TL) gerçek BIST ciro
  dağılımına göre doğrulanmadı, spec'ten olduğu gibi taşındı; (c) EMA overlay
  renkleri yalnızca varsayılan periyotlar (8/21/55/200) için ayrı renk taşıyor,
  `momentum_rank`'ın kendi EMA'ları (20/50/200) kısmen bu kümeye denk
  DÜŞMEDİĞİ için (20/50) aynı gri fallback'i paylaşıyor — küçük bir görsel
  ayırt edilebilirlik kaybı, bilinçli kabul edildi; (d) EWMAC forecast
  scalar'ı K3 (Carver kitap çıkarımı) tamamlanınca sabit tabloya geçirilmeli.
  `pytest -q -m "not network"` 474/474 yeşil, `ruff check tlab/ tests/` 18
  hata (BASELINE İLE AYNI, yeni dosyalarda SIFIR), `mypy tlab/` 2 hata
  (BASELINE İLE AYNI, `renderer.py`/`dashboard.py` — bu göreve AİT DEĞİL),
  `lint_lookahead` 2 uyarı (BASELINE İLE AYNI).

- **Faz 8E — Sürekli ağırlıklı oynaklık hasadı, dönüş haritası (confluence),
  güvenli tarama filtreleri** (2026-08-31): TAMAMLANDI. Master prompt'un
  "Bölüm 12.12"sine (tam `scans.yaml` preset kataloğu) atıf yapıyordu ama bu
  bölüm/doküman repo'da HİÇBİR YERDE bulunamadı (`git ls-tree -r origin/main`
  ile doğrulandı) — Faz 8A'da AYNI türde eksik bir referansla karşılaşıldığında
  izlenen emsal takip edildi: mühendislik takdiriyle makul bir alt küme
  üretilip her tasarım kararı kod içinde "TASARIM KARARI" olarak belgelendi.
  1. **`features/volatility.py::garch11_forecast(returns, window=252,
     refit_stride=21, annualize=True)`** — `arch` paketiyle GARCH(1,1)
     volatilite tahmini, GARCH `refit_stride` deseninde (Faz 6/8A'nın
     `check_stride` mantığıyla AYNI performans gerekçesi): her `refit_stride`
     barda [t-window+1,t] penceresiyle yeniden fit edilir, aradaki barlarda
     son (ω,α,β) ile σ² İLERİ sarılır (yalnızca t-1'deki bilgi kullanır,
     non-repaint). Getiriler MLE kararlılığı için ×100 ölçeklenir. Fit
     ıraksarsa (`except Exception`) o pencere NaN kalır — uydurma değere
     DÜŞÜLMEZ. THYAO gerçek verisiyle doğrulandı (~%29-30 yıllıklaştırılmış
     vol, makul). 4 yeni test.
  2. **`pair.vol_harvest` (`tlab/indicators/pairs/vol_harvest.py::
     VolHarvestPair`)** — `RelativeMomentumPair` (Faz 5) ile AYNI Z-skor
     makinesini paylaşır ama sinyal İKİLİ DEĞİL: Z-skora göre SÜREKLİ bir
     hedef ağırlık `w_target(z)` üretir (`weight_fn="linear"`: `0.5-slope·z`
     `w_min`/`w_max`'a kırpılır; `"grid"`: `grid_levels` eşiklerinde basamaklı
     `math.copysign` adımlaması) ve yalnızca `rebalance_band` aşıldığında
     rebalans eder. "Hasat" (harvest) = aktif rebalans edilen portföyün, HİÇ
     rebalans edilmeyen statik bir al-tut'a göre FAZLASI. **Duraklama (pause)
     mekanizması — backlog'daki "kointegrasyon çürüme izleyicisi" notunun
     (madde 4, 2026-08-29) doğal karşılığı**: rolling ADF p-değeri
     `adf_pause_p`'yi aşarsa VEYA rolling halflife `halflife_max`'ı aşarsa
     VEYA (opsiyonel) oynaklık rejimi aşırı uçtaysa (`vol_regime_filter`,
     `vol_zscore`) hedef ağırlık SON değerinde DONDURULUR; kontrol HER barda
     değil `check_stride` barda bir yapılır (ADF testi ucuz değil). `tlab/
     backtest/pairs_engine.py::run_pair_backtest_weighted` — yeni sürekli-
     ağırlıklı motor, `shares_y`/`shares_x` takip eder, drift `rebalance_band`ı
     aşınca EXACT hedefe rebalans eder, komisyonu yalnızca TİCARET EDİLEN
     değer üzerinden uygular.
  3. **GERÇEK HATA bulundu ve düzeltildi (kayıt-anı repaint testiyle
     yakalandı, tam da bu altyapının tasarlandığı senaryo)**: pause/resume
     Signal payload'ları `adf_p_last`/`hl_last` module-döngü değişkenlerini
     TÜM hesap biterken taşıdıkları SON değerle okuyordu — olay barı `t`'deki
     GERÇEK değeri değil, serinin en son `check_stride` kontrolündeki değeri
     yazıyordu (kısmi/tam koşu karşılaştırıldığında `populate_registry()`
     erken barlarda gerçek bir mismatch bastı). Düzeltme: `pause_reason:
     dict[int, str]` → `dict[int, tuple[str, float, float]]`, olayın
     GERÇEKLEŞTİĞİ ANDA `(reason, adf_p_last, hl_last)` olarak yakalanıp
     sinyal döngüsünde bu anlık değerler kullanılıyor. Ayrıca `math.isinf`
     kontrolü eklendi (halflife mean-reversion olmayan spread'lerde `inf`
     olabilir, JSON'a yazılamaz — `None`'a çevrilir).
  4. **Görsel yeniden kullanım** — `_render_pair`/`_pair_header_lines`
     (Faz 5 için yazıldı) `VolHarvestPair`e uyumlu `last_state` alias'ları
     eklenerek (`holding`/`signal_today`/`zone_state`/`n_trades`/
     `buyhold_5050`) ÜCRETSİZ yeniden kullanıldı; yeni
     `_STRATEGY_NAME_TR_BY_INDICATOR` sözlüğü doğru strateji adını
     (`result.indicator`e göre) seçiyor — ilk taslakta hardcoded
     `_STRATEGY_NAME_TR` sabiti YANLIŞ strateji adı/geçiş sayısı/Z-skor
     gösteriyordu, gerçek TCELL/ISCTR render'ıyla bulunup düzeltildi.
     **DÜRÜST NOT (ERTELENDİ)**: görev metninin istediği 4. panel (w_Y adım
     grafiği + rebalans markerları) HENÜZ ÇİZİLMEDİ — altta yatan veri
     (`w_target`/`w_actual`/`harvest_rebalance` marker'ları)
     `IndicatorResult`'ta HAZIR duruyor, ayrı bir görsel geliştirme turunda
     eklenebilir; mevcut 3 panel (fiyat/portföy/Z-skor) `_render_pair`'den
     ÜCRETSİZ miras alınıyor.
  5. **`tlab/scanner/confluence.py::build_reversal_map`** — YENİ bir
     mimari kategori: `tlab/indicators/`de DEĞİL, girdisi ham OHLCV değil
     ZATEN HESAPLANMIŞ birden fazla `IndicatorResult` (structure.
     supply_demand/golden_zone/price_structure, trend.weekly_channel,
     harmonic.*, structure.swing_fib_abcd) — bu yüzden `BaseIndicator`
     sözleşmesine UYMAZ, `scanner/` altında yaşayan bir "post-processing"
     katmanı. **Kapsam (bilinçli): yalnızca DESTEK/DİP tarafı** — görev
     metninin `bottom_probability`/"DİPTE OLASI" adlandırması bunu
     doğruluyor, direnç/tepe tarafı bu turun DIŞINDA (simetrik "TEPEDE
     OLASI" haritası ileride aynı iskeletle eklenebilir). Ağırlıklandırma =
     kaynak_türü_temel_ağırlığı (`_SOURCE_BASE_WEIGHT`/`_HARMONIC_BASE_
     WEIGHT` — TASARIM KARARI, görev metni sayısal değer vermiyor, dar/
     keskin bölgeler EN YÜKSEK, istatistiksel referans seviyeleri EN
     DÜŞÜK) × tazelik (`2^(-yaş_gün/45)`, EWMA/EWMAC'ın üstel çürüme
     deseniyle TUTARLI) × tf_ağırlığı (W1=1.5/1D=1.0/4H=0.6, görev
     metninin sabit çarpanları). Aday fiyatları ATR-bazlı bucket'lara
     (`bucket_atr_fraction`) toplanıp yoğunluk profili (`price_structure.
     py`'nin `vp_bins`/`vp_volumes` price-indexed konvansiyonuyla BİREBİR
     aynı) çıkarılır; `bottom_probability = 1-exp(-yoğunluk/ölçek)` en son
     ONAYLI (`finalized_idx`, GoldenZone/HeadShoulders ile AYNI non-repaint
     gerekçe) swing low'un bucket'ında hesaplanır. `tlab/viz/renderer.py::
     render_reversal_map` — katmanlı bölge kutuları (opaklık=ağırlık,
     genel `_draw_boxes` KULLANILMAZ çünkü o sabit opaklık varsayar) + sağ
     panelde yoğunluk histogramı + "DİPTE OLASI: X | N kaynak" etiketi.
     THYAO gerçek verisiyle render edilip gözle doğrulandı.
  6. **`tlab/scanner/filter_expr.py`** — `eval()` KULLANMADAN güvenli AST
     tabanlı ifade değerlendirici (görev metninin açık isteği): yalnızca
     `Compare`/`BoolOp`/`UnaryOp(Not)`/`Name`/`Constant`/`Tuple`/`List`
     düğümlerine izin verir, `Call`/`Attribute`/atama/comprehension/lambda
     dahil HER ŞEY reddedilir (`__import__`, `.bit_length()`, `.__class__`
     ile test edildi). `tlab/cli.py::_signal_passes_filter`e `expr` dalı
     eklendi (`signal.payload`+`score`+`direction`+`state` namespace'i).
     `config/scans.yaml`'a 3 yeni preset: `hasat_duraklatildi`/
     `hasat_devam` (`pair.vol_harvest`, `--pairs` mekanizmasıyla — diğer
     pair preset'leriyle AYNI), `dipte_olasi` (`indicators: ["confluence"]`
     + `expr: "bottom_probability >= 0.5 and n_sources >= 3"` — `expr`
     alanının GERÇEK kullanım örneği).
  7. **`tlab eod --build-reversal-maps`** — `run_eod()`'a `build_
     reversal_maps: bool = False` parametresi + `_build_confluence_runs()`
     (universe'i gezip her sembol için `build_reversal_map_from_run()`
     çağırır, per-symbol try/except ile hata izolasyonu — kod tabanının
     GENEL desenine uygun) eklendi. **GERÇEK EKSİK bulunup düzeltildi**: bu
     parametre `run_eod()`'a eklenmişti ama `tlab/cli.py::eod_cmd`'ye
     KARŞILIK GELEN `--build-reversal-maps` CLI bayrağı hiç YAZILMAMIŞTI —
     `config/scans.yaml`'ın kendi yorumu `tlab eod --build-reversal-maps`den
     bahsediyordu ama komut fiilen ÇALIŞMAZDI (mypy/ruff/pytest bunu
     yakalamaz, yalnızca elle `--help` denemesiyle fark edildi). Düzeltildi,
     `PYTHONIOENCODING=utf-8 python -m tlab.cli eod --help` ile bayrağın
     göründüğü doğrulandı.
  8. **`ResultsStore` — geri okuma yolu**: `read_result(run_id, symbol, tf,
     indicator)` (JSON'dan TAM `IndicatorResult` geri okur, yoksa `None`)
     ve `list_symbol_indicators(run_id, tf=None)` — confluence.py'nin
     `results.db`'den ZATEN hesaplanmış indikatör sonuçlarını okuma
     ihtiyacı için (Faz 6'nın `persist()`/`query()`'sinin eksik kalan
     karşılığı — o zamana kadar hiçbir tüketici tam sonuç geri okumaya
     ihtiyaç duymamıştı).
  9. **Testler** — 32 yeni (474→506): `test_volatility.py` (+4, GARCH),
     `test_pairs/test_pairs_engine.py` (+4, ağırlıklı motor: aktif ağırlık
     hep [0,1], bant-içi rebalans yok, bant-aşımı tetikler, hiç rebalans
     olmazsa hasat sıfır), `test_pairs/test_vol_harvest.py` (+6),
     `test_scanner/test_confluence.py` (+7, destek-only filtre/kırık
     bölge dışlama/geçersiz harmonik dışlama/ağırlık toplamı/gerçek swing
     low tespiti + gerçek TCELL/ISCTR uçtan uca smoke), `test_filter_expr.py`
     (+11, parametrized tehlikeli-ifade reddi dahil), `test_scanner/
     test_engine_and_results.py`/`test_bootstrap.py` (mevcut testlere
     `read_result`/`list_symbol_indicators`/`pair.vol_harvest` katalog
     doğrulaması eklendi).
  10. **Gerçek veri doğrulaması** — `_build_confluence_runs` gerçek
      `outputs/results.db`nin en güncel çalışmasına (`bist_2026-08-28`)
      karşı TCELL/ISCTR/AKBNK/GARAN için elle çalıştırıldı, 4/4 sembol
      hatasız `confluence` sonucu üretti.
  **DÜRÜST NOT — ERTELENEN kalemler (bilinçli, kayıt altında)**:
  (a) Görev metninin 4. maddesindeki EOD rapor sekmeleri (preset başına
  grafik linki, "Dipte olası" sekmesi reversal_map grafiklerine bağlı) —
  `tlab/viz/report.py`ye HİÇ dokunulmadı, ayrı bir takip işi;
  (b) tam evren × (4H,1D,W1) × tüm registry performans ölçümü (madde 6) —
  bu ölçekte bir koşu (622 sembol × 3 TF × ~20 indikatör) saatler
  sürebilir, bu oturumun bütçesine SIĞMADI; küçük ölçekli (4 sembol)
  gerçek-veri doğrulaması yapıldı ama tam-ölçek ekstrapolasyon YOK —
  Faz 6/8A/8D'nin de aynı şekilde "küçük örneklemden ekstrapolasyon"
  ilkesini izlediği emsal not edilerek ertelendi; (c) confluence'ın
  direnç/tepe tarafı ("TEPEDE OLASI") kapsam dışı bırakıldı (madde 5'te
  açıklandı). `pytest -q -m "not network"` 506/506 yeşil, `ruff check
  tlab/ tests/` 18 hata (BASELINE İLE AYNI, yeni dosyalarda SIFIR),
  `mypy tlab/` 2 hata (BASELINE İLE AYNI — `renderer.py::_pair_header_
  lines`/`dashboard.py`, bu göreve AİT DEĞİL), `lint_lookahead` 3 uyarı
  (BASELINE 2 + `vol_harvest.py:174` — AYNI bilinen false-positive
  kategorisi, `.iloc[window_start:t+1]` geriye-bakan pencere sonu `t+1`
  ifadesi lint'in `.iloc[i+...]` sezgisini tetikliyor, `relative_
  momentum.py:163`/`kerkez_nenstar.py:34` ile AYNI kök neden — GERÇEK bir
  lookahead DEĞİL).

- **Faz 10 — Sinyalden Portföye** (`tlab/portfolio/`, `tlab/backtest/metrics.py`,
  2026-09-01): TAMAMLANDI. K3'ün (`bilgi-bankasi/teknik/11_carver_systematic.md`)
  ve kendi spec taslağının (`docs/spec/tlab_10_portfolio.md`, K3'ün hemen ardından
  yazılmıştı) doğrudan koda çevirisi — Carver'ın forecast→volatilite hedefleme→
  pozisyon boyutlama→handcrafting zincirini tlab'a uyarlar. Bu katman ÖNCEKİ
  fazların indikatörlerinden FARKLI bir doğaya sahiptir: `IndicatorResult`/
  `Signal` ÜRETMEZ (tarama/sinyal katmanı değil, zaten üretilmiş forecast/
  sinyal serilerini GERÇEK pozisyon büyüklüğüne çeviren bir HESAP katmanı).
  1. **`tlab/portfolio/risk.py`** — `diversification_multiplier(weights,
     corr_matrix, max_multiplier=2.5)`: 11/ORAN-03'ün KESİN formülü
     (`1/sqrt(W·H·Wᵀ)`), negatif korelasyon hesap ÖNCESİ sıfıra taban değeri
     (kitabın açık şartı), sonuç tavana (varsayılan 2.5, 11/ORAN-02) kırpılır.
     Bu fonksiyon HEM `forecast.py`'nin forecast diversification multiplier'ı
     HEM `risk.py`'nin kendi instrument diversification multiplier'ı için
     PAYLAŞILAN tek kaynak (11/ORAN-03: "aynı formül, girdi matrisi değişir").
     `round_target_position` (İLK ve TEK yuvarlama noktası, adım 12),
     `apply_position_inertia` (hedefin `inertia_pct` — varsayılan %10 —
     içindeyse işlem YOK, adım 13), `portfolio_instrument_position` (saf
     çarpım, adım 11).
  2. **`tlab/portfolio/forecast.py::combine_forecasts`** — 11/DISIPLIN-02
     zinciri: ağırlıklı ortalama → rolling korelasyondan (yalnızca t ve
     öncesi, `correlation_window` varsayılan 120 — TASARIM KARARI, kaynak
     atfı yok) diversification multiplier → `[-cap,+cap]` (varsayılan ±20)
     kırpma. Tek kural verildiğinde (`forecast_weights={rule:1.0}`)
     çeşitlendirme HİÇ hesaplanmadan (tanım gereği 1.0) girdinin AYNISını
     döndürür — kabul kriteri #1. `forecast_weights` toplamı ≠1.0 ise
     `ValueError` (KURAL-02).
  3. **`tlab/portfolio/sizing.py`** — FORMÜL ZİNCİRİ adım 1-8 (11/DISIPLIN-
     03/04, ORAN-05): `price_volatility` (**FİYAT PUANI cinsinden**,
     `close.diff()` bazlı, YÜZDE DEĞİL — Faz 10 spec'in "Girdiler" bölümünün
     açık kararı, `features/volatility.py::realized_vol`'dan KASITLI OLARAK
     farklı birim, block_value ile çarpılıp para birimi riskine çevrilecek
     şekilde) → `instrument_currency_volatility` → `instrument_value_
     volatility` → `annualised_cash_vol_target`/`daily_cash_vol_target`
     (÷16, 256 iş günü varsayımı) → `compute_volatility_scalar` →
     `compute_subsystem_position`. `load_portfolio_config()` — yeni
     `config/portfolio.yaml`'dan `pct_vol_target`/`trading_capital` okur
     (kullanıcının hesap büyüklüğü/risk toleransı — tlab'ın hiçbir mevcut
     veri katmanında YOK, kod içine GÖMÜLMEDİ); ikisi de `null` bırakılmışsa
     (repo'daki varsayılan durum) AÇIK bir `ValueError` fırlatır, sessizce
     fabrika varsayımına DÜŞÜLMEZ.
  4. **`tlab/portfolio/allocation.py::handcraft_weights`** — 11/KURAL-05
     (Markowitz optimizasyonunun küçük-tahmin-hatası kırılganlığından
     kaçınan, korelasyona göre GRUPLANMIŞ + Tablo 8'in — 11/ORAN-07 —
     grup-ağırlık kurallarını uygulayan yöntem). N=1: %100. N=2: %50/%50
     (korelasyondan BAĞIMSIZ). N=3: tabloya (7 somut satır) en yakın satır
     — **permütasyon-farkında** (`_lookup_3asset_weights`, üç varlığın
     olası TÜM 6 A/B/C-rol eşleşmesini deneyip en yakın satırı bulur, çünkü
     tablo rolleri sembol SIRASINDAN bağımsız değil — B her zaman "ortadaki"
     varlık). N≥4 eşit-korelasyonlu: eşit ağırlık; N≥4 farklı-korelasyonlu:
     otomatik gruplama YOK (kitap algoritma vermiyor), `groups` parametresiyle
     elle alt-gruplanmalı → `ValueError`. İç içe `groups` (`[["Bond"],
     ["SP500","Nasdaq"]]` gibi) özyinelemeli çözülür, grup-arası korelasyon
     TÜM çapraz-grup varlık çiftlerinin ORTALAMASI (TASARIM KARARI, kitap
     kesin yöntem vermiyor — tek-elemanlı gruplarda TAM olarak ham
     korelasyona indirgendiği için flat/gruplu çağrılar TUTARLI).
     `periodic_handcraft_schedule` — üç aylık (varsayılan, TASARIM KARARI)
     gibi PERİYODİK/adım-fonksiyonu yeniden hesaplama, her noktada YALNIZCA
     trailing `correlation_window` kadar geçmişle (non-repaint); `weights_at`
     — "extend-only sabit değer" okuma (`structure.golden_zone`'un bant
     deseniyle AYNI ilke, Faz 8C). `apply_sharpe_adjustment` (11/DISIPLIN-07,
     varsayılan KAPALI) çarpanları PARAMETRE olarak alır — **Tablo 12'nin
     (s.86) kendi sayısal değerleri K3'ün hedefli çıkarımına DAHİL EDİLMEDİ**,
     bu fonksiyon SABİT/uydurma bir tablo TAŞIMAZ.
  5. **`tlab/backtest/metrics.py`** (YENİ dosya) — fitting disiplini + hız
     limiti, kod SEVİYESİNDE bir sinyal DEĞİL, backtest SONUÇLARINI
     değerlendiren araçlar. `ACHIEVABLE_SHARPE_REFERENCE` (11/ORAN-10),
     `MIN_SHARPE_THRESHOLD`+`min_sharpe_threshold()` (11/ORAN-08, Tablo 4 —
     tablo dışına taşan (kural_sayısı,yıl) çiftleri EN BÜYÜK tanımlı hücreye
     düşer), `PESSIMISM_FACTOR` (11/DISIPLIN-08, Tablo 14). `speed_limit_
     check()` (11/DISIPLIN-12) — maliyet bütçesi = gerçekçi ön-maliyet
     Sharpe'ın 1/3'ü; **kitabın kendi Euro Stoxx örneğiyle KASITLI bir
     sayısal fark var** (görüntülenen 2-ondalık yuvarlanmış `0.13/0.002=65`
     round-trip diyor, TAM kesirle `1/3×0.40=0.1333.../0.002≈66.67` —
     fonksiyon TAM formülü uygular, kitabın kendi yuvarlama zincirinin
     ARTEFAKTINI DEĞİL, testte bu fark açıkça belgelendi).
  6. **`tlab/testing/repaint.py::allocation_repaint_test`** (YENİ) —
     `universe_repaint_test`in (Faz 8D) AYNI "kesik ⊆ tam" mantığı ama bir
     SERİ yerine `{recompute_tarihi: ağırlıklar}` sözlüğü üzerinde; periyodik
     `allocation.py` çıktısının GERÇEK non-repaint sözleşmesini doğrular
     (kabul kriteri #6).
  7. **DÜRÜST BOŞLUK — 16-varlıklı Tablo 10/11 kabul kriteri KARŞILANAMADI**:
     spec taslağının kabul kriteri #3 "16-varlık (Tablo 10/11) örneğinin de
     fixture olarak kodlanmasını" istiyordu, ama bu tablolar K3'ün hedefli
     çıkarımına HİÇ DAHİL EDİLMEMİŞ (`bilgi-bankasi/teknik/11_carver_
     systematic.md`'de yalnızca Tablo 8/12/14 var) — Faz 8A/8E'deki AYNI
     "eksik dış referans" emsaliyle, 16-varlıklı senaryo TEST EDİLMEDİ;
     genel özyinelemeli algoritma yalnızca DOĞRULANABİLİR (Tablo 8, 7 satırın
     TAMAMI) örneklerle test edildi. Bu, kod EKSİKLİĞİ değil VERİ eksikliği —
     algoritmanın kendisi (N≥4 eşit-korelasyon + iç içe `groups`) genel ve
     test edilmiş durumda.
  8. **Gerçek veri doğrulaması** (TCELL/ISCTR/AKBNK, yerel önbellek):
     `trend.ewmac`'in gerçek `series["ewmac_combined"]` serilerinden iki
     farklı çift (2,8 / 4,16) `combine_forecasts`'a verildi — sonuç hep
     `[-20,20]` içinde kaldı; `price_volatility` TCELL'de ~1.5-2.0 TL/gün
     (makul); gerçek 250 barlık TCELL/ISCTR/AKBNK getiri korelasyon
     matrisiyle (`ISCTR-AKBNK`≈0.82 yüksek, `TCELL` diğerleriyle ~0.52-0.53
     daha düşük korelasyonlu) `handcraft_weights` TCELL'e %42, ISCTR/AKBNK'a
     %29/%29 verdi — sezgiyle TUTARLI (daha az korele olan TCELL daha
     yüksek ağırlık aldı, birbirine yüksek korele bankalar payı paylaştı).
  9. **Testler** — 54 yeni: `tests/test_portfolio/` (YENİ paket —
     `test_risk.py` 12, `test_forecast.py` 5, `test_sizing.py` 8,
     `test_allocation.py` 15), `tests/test_backtest/` (YENİ paket —
     `test_metrics.py` 7), artı `allocation_repaint_test`in kendisi
     `test_allocation.py`'de bir kabul-kriteri testinde egzersiz edildi.
  `pytest -q -m "not network"` 560/560 yeşil (506→560), `ruff check tlab/
  tests/` 18 hata (BASELINE İLE AYNI, yeni dosyalarda SIFIR), `mypy tlab/`
  2 hata (BASELINE İLE AYNI, `renderer.py`/`dashboard.py` — bu göreve AİT
  DEĞİL), `lint_lookahead` 3 uyarı (BASELINE İLE AYNI, yeni dosyalarda
  SIFIR). Roadmap: Faz 8B ✓ → Faz 8D ✓ → K3 ✓ → Faz 8E ✓ → **Faz 10 ✓** →
  sırada **Faz 9**.

Toplam 560 test yeşil (`pytest -q`, varsayılan olarak `-m "not network"` uygular),
ruff/mypy/lint_lookahead temiz (yeni kod kapsamında — repo genelindeki 18 ruff/2
mypy/3 lint_lookahead uyarısı önceden var olan ya da bilinen false-positive,
ilgisiz satırlardır).

---

## 2026-09-03 — Adım 1 / FAZ 0: Sinyal tazeliği + tasarım doğrulama altyapısı

**Tetikleyici:** `docs/TANI_VE_YOL_HARITASI_v2.md` + `docs/STRATEJI_DENETIM_TAM.md`
tanı/denetim raporları ve 16 adımlık `docs/00_BASLANGIC_SIRASI.md` yol haritası
kullanıcı tarafından onaylandı; bu oturum haritayı BAŞTAN uyguluyor, Adım 1 (Faz 0)
ile başladı. Önce `arch` paketi eksikti (`test_garch11_forecast_*`, 4 test) — kuruldu,
573→577 yeşil (ortam eksikliği, kod hatası değil).

**İş 1 — Sinyal tazeliği:**
`scanner/engine.py::_add_bars_ago(result, df)` (YENİ) — İŞ 1'in metninde önerilen
İKİ seçenekten "daha basit ve KESİN doğru" olanı seçildi: ayrı bir `bars` tablosu +
takvimden geri hesaplama YERİNE, indikatör zaten kendi çağrıldığı `df.index`'i
bildiği için, `_run_single_worker`/`_run_pair_worker` (df_y ile — `RelativeMomentumPair`
"df=Y" mimari notuyla tutarlı)/`_run_universe_worker` (sembol başına kendi df'i)
her sinyalin `payload["bars_ago"]`'sını run anında YAZAR (`Signal.payload` frozen
dataclass'ın mutasyona açık tek alanı — yeniden oluşturmaya gerek yok).
`results.py`: `signals` tablosuna yeni `bars_ago INTEGER` kolonu (şema DONUK
sözleşmesi alan EKLEMEYE izin veriyor) + eski DB dosyaları için `_migrate_bars_ago_
column()` tek seferlik `ALTER TABLE`; `persist()` payload'dan okuyup kolona yazıyor;
`latest_signals(..., max_bars_ago=None)` YENİ parametre — `None`=eski davranış,
verilirse yalnızca zincirin GÜNCEL satırının `bars_ago <= N` VE `NOT NULL` (migrasyon
öncesi/yaşı bilinmeyen satırlar `max_bars_ago` verildiğinde DIŞLANIR — sessizce taze
sayılmıyorlar). `web/backend/routes/scan.py::list_signals` yeni `max_bars_ago: int|None=3`
query param + yanıta `bars_ago` alanı. Frontend (`web/frontend/app/scan/page.tsx`):
"Tazelik" seçici (Son 1/3/10 mum/Tümü, varsayılan 3 — "Tümü" backend'e büyük sayı
gönderiyor, HTTP query'de `None` taşınamadığı için), "Yaş" kolonu, sayfa-içi
`bars_ago` artan sıralama (backend `detected_at DESC` sıralamasını KORUYOR — bu,
tazelik sırasıyla BİREBİR aynı değil, o yüzden client-side ayrıca sıralanıyor),
tazelik-farkında dürüst boş durum metni. 7 yeni test (`tests/test_scanner/
test_bars_ago.py`) — `_add_bars_ago` hesabı (son bar=0, N bar geride=N, boş df/
sinyalsiz no-op), `persist()` kolon yazımı, `max_bars_ago=None`/filtreli/NULL-dışlama.

**İş 2 — Grafik tasarım skill'i + agent'ı:**
`.claude/skills/grafik-tasarim-sistemi/SKILL.md` + `.claude/agents/grafik-
tasarimcisi.md` (YENİ) — `bilanco-radar/.claude/{skills/kart-tasarim-sistemi,
agents/kart-tasarimcisi.md}` örnek alınarak grafik/SVG alanına uyarlandı. İçerik:
`docs/design/grafik_stil_vitrini.html`'in "ilham panosu değil çalıştırılabilir
şartname" statüsü, kullanılacak 3 tema (dark→DARK_TERMINAL, classic→LIGHT_ANALYSIS,
editorial→KAGIT_RAPORU — saas/neon KAPSAM DIŞI), token/etiket-yerleşimi kuralları,
ve ZORUNLU görsel doğrulama döngüsü (değişiklik→gerçek veriyle üret→Read ile
AÇ VE GÖR→madde madde yaz→düzelt, en az 3 iterasyon + en az 3 veri durumu,
`docs/design/iterasyon/`'a kaydedilir).

**İş 3 — Golden (görsel gerileme) testi:**
`tests/conftest.py` (YENİ, proje kökünde İLK conftest) — `--update-golden` bayrağı.
`tests/test_viz/test_golden.py` (YENİ) — 3 gösterge (`structure.price_structure`
dark, `structure.swing_fib_abcd` light, `harmonic.carney` light — Gartley,
`build_gartley_ohlcv()` fixture'ı `test_renderer.py`'den ödünç) sabit sentetik/
deterministik veri üzerinde render edilip `fig.to_dict()`'in kararlı (yuvarlanmış,
sıralanmış) JSON'ıyla `tests/test_viz/golden/*.json`'a karşılaştırılıyor.
Karşılaştırma mantığı `normalize_figure()` fonksiyonunda İZOLE edildi (görev
metninin notu: Faz 3'te SVG motorüne geçilince yalnızca bu fonksiyon SVG metni
döndürecek şekilde değişecek, geri kalanı aynı kalacak).
**Yol boyunca bulunan gerçek bir test-izolasyon hatası (bu görevin kapsamında,
kendim düzelttim — PROGRESS_LOG'a not düşülmesi gereken "kapsam dışı" bir hata
DEĞİL):** golden testleri TEK BAŞINA yeşildi ama tam `pytest -q -m "not network"`
koşusunda BAŞARISIZ oluyordu — sebep `fig.to_dict()`'in `layout.template`'i
(Plotly'nin ~50 iz tipi için SÜREÇ genelinde paylaşılan `pio.templates.default`'tan
gelen, bizim ÇİZMEDİĞİMİZ genel varsayılan stil) gömmesi; bu ambient global,
test SIRASINA göre farklı değerler taşıyabiliyor. Düzeltme: `normalize_figure()`
`layout.template`'i karşılaştırmadan ÖNCE atıyor (bizim çizdiğimiz hiçbir şeyi
yansıtmıyor, yalnızca kütüphane/ortam gürültüsü).

**Test durumu:** `pytest -q -m "not network"` **587/587 yeşil** (577→587, +10:
7 bars_ago + 3 golden). `ruff check tlab/ tests/` 19 hata (BASELINE İLE AYNI —
`git stash` ile doğrulandı, benim değişikliklerimden ÖNCE de 19'du; CLAUDE.md'deki
"18" notu hafif eski/drift, yeni dosyalarda SIFIR). `mypy tlab/` 1 hata (BASELINE,
`renderer.py:2790`, bu göreve AİT DEĞİL — düzeltirken KENDİ eklediğim 1 mypy hatasını
(`results.py`, `list[str]+list[int]` union tipi) `params`/`params_states`/
`params_bars_ago`'yu `list[object]` olarak açıkça tipleyerek AYRICA düzelttim).
`lint_lookahead` 3 uyarı (BASELINE İLE AYNI, ilgisiz satırlar).

**Sırada:** Adım 1 tamamlandı, onay bekleniyor. Onay gelirse Adım 2 (Faz 0.5 —
sistemik düzeltmeler: `significant_pivots()`, `for_timeframe()`, `supported_
timeframes` kapısı, hacim onayı parametresi) başlayacak.

---

## 2026-09-03/04 — Adım 2 / FAZ 0.5: Sistemik düzeltmeler (A1-A4 + D)

Kullanıcı onayı üzerine Adım 2 başlatıldı, A1→A2→A3→A4→D sırasıyla TAMAMLANDI.
Her alt-adım sonunda ayrı push yapıldı (kullanıcı "düzenli commit/push"
istedi) — commit'ler: `9e084c7` (A1), `c3621d8` (A2+A3+A4), ve bu girdinin
sonundaki (D + wedge/broadening/triangle düzeltmesi).

**A1 — Ortak pivot girişi:** `tlab/features/swings.py::significant_pivots(df,
method="atr"|"fixed", ...)` — `method="atr"` → `alternate_pivots(atr_zigzag(...))`;
`method="fixed"` → `min_swing_atr` verilmezse `alternate_pivots(find_pivots(...))`,
verilirse `_reduce_with_min_swing` (golden_zone'un ÖNCEDEN kendi içinde
uyguladığı swing-büyüklüğü filtresinin taşınmış hâli — RAW `find_pivots`
çıktısı üzerinde çalışır, `alternate_pivots`'un KENDİSİYLE AYNI "yalnızca
ileri, pending serbestçe güncellenir, commit edilen asla geri alınmaz"
deseniyle non-repaint). **Yol boyunca bir repaint hatası yazıp KENDİ hypothesis
testimle yakalayıp düzelttim:** ilk taslak `_reduce_with_min_swing`
`kept[-1]`'i SONRADAN gelen daha ekstrem bir pivotla değiştiriyordu — bu,
partial/full df'ler arasında committed bir pivotun KAYBOLMASINA (gerçek
repaint) yol açıyordu; `test_significant_pivots_fixed_min_swing_prefix_is_
non_repainting` (hypothesis, 30 örnek) bunu yakaladı, algoritma "pending
serbestçe güncellenir, commit ASLA geri alınmaz" prensibine göre yeniden
yazıldı.

7 gösterge buna bağlandı: `head_shoulders`/`double_top_bottom`/`golden_zone`
(zigzag DOĞRUDAN formasyon yapısı) + `wedge`/`triangle`/`broadening`/
`price_structure` (pivot yalnızca trendline aday havuzu — bkz. aşağıdaki
KRİTİK bulgu, bu ayrımın NEDEN önemli olduğu buradan çıktı).
`harmonic.*`/`structure.swing_fib_abcd` zaten kendi `zigzag_method`'unu
sunuyordu, yalnızca varsayılanları "fixed"ten "atr"ye çevrildi (`atr_mult`
kasıtlı olarak KENDİ değerinde — 2.0 — bırakıldı, sistemin ortak 3.0'ı
DEĞİL).

**A2 — Zaman dilimi ölçekleme:** `tlab/core/params.py::BaseParams.for_
timeframe(tf)` — `_BAR_FIELDS: ClassVar[frozenset[str]]` alt sınıflarca
bildirilir (dataclass field SAYILMAZ), 1D taban, 4H×6/1H×24/W1÷5,
`round`+`max(1,...)`. `double_top_bottom`/`wedge`/`broadening`/
`price_structure`/`flag_pennant`'a takvimsel bar-alanları işaretlendi
(`left`/`right`/`confirm_bars`/`atr_period`/MA pencereleri BİLİNÇLİ OLARAK
dışarıda — TA'nın evrensel kısaltmaları ya da sinyal mekaniği, takvimsel
süre DEĞİL; `weekly_channel.n=52` de dışarıda — W1-native bir sabit, D1
tabanına göre ölçeklemek YANLIŞ olurdu). `scanner/engine.py` +
`viz/live.py` artık TEK bir ortak `tlab/indicators/bootstrap.py::
scaled_factory(name, tf)`'den geçiyor (tarama ve `/chart` AYNI ölçekli
parametreleri kullanır garantisi).

**A3 — supported_timeframes kapısı:** `IndicatorSpec.supported_timeframes`
(`build_catalog()`'un SONUNDA her indikatörü bir kez kurup KENDİ meta'sından
otomatik dolduruluyor — iki kez elle yazılıp drift etme riski YOK).
`engine.run()`'da (gösterge,tf) çifti desteklenmiyorsa iş HİÇ AÇILMAZ,
`ScanRun.skipped_unsupported`'a yazılır + loglanır. `viz/live.py` aynı kapıyı
net bir `ValueError` ile uyguluyor. `run_eod`'un varsayılan `timeframes`'ine
`"w1"` eklendi (`Store.update()` zaten her EOD koşusunda W1'i 1D'den otomatik
türetip yazıyordu — ekstra veri adımı gerekmedi). Web: `/api/catalog`
`supported_timeframes` döndürüyor, `/chart` sayfasının TF seçicisi artık
seçili göstergenin desteklemediği zaman dilimlerini devre dışı gösteriyor +
otomatik destekli bir TF'e geçiyor.

**A4 — Hacim onayı:** 5 formasyon modülüne (`double_top_bottom`/
`head_shoulders`/`wedge`/`broadening`/`flag_pennant`) `require_volume_
confirm: bool = False` — `True` iken hacim onayı geçmeyen aday `confirmed`'a
TERFİ ETMİYOR (`invalidated` OLMUYOR, yalnızca o event `pattern_signals`
listesinden çıkarılıyor — pending gibi diğer sinyaller ETKİLENMİYOR).
`config/scans.yaml`'a `hacim_onayli` preset'i — indikatör parametrelerine
DOKUNMADAN, mevcut `filter.expr` mekanizmasıyla (`volume_ok == True or
volume_profile_ok == True` — iki modül grubu farklı payload anahtarı
kullandığı için `or`, `filter_expr.py` eksik anahtarı None/False sayıyor).

**D — Ölçüm ve rapor (`scripts/sistemik_denetim.py`, 120 gerçek BIST
sembolü):** Tam rapor `docs/spec/SISTEMIK_DENETIM_v1.md`'de. Özet:

1. head_shoulders/double_top_bottom/golden_zone/price_structure(zone/range)
   için A1 ÇALIŞTI — sinyal sayısı %68-91 azaldı (golden_zone İKİ KAT ARTTI
   ama bu BEKLENEN/İYİ bir sonuç — kendi filtresi zaten vardı, ortak giriş
   onu DAHA TUTARLI hale getirdi).
2. **BULUNAN GERÇEK HATA (bu oturumda bulunup DÜZELTİLDİ — kapsam dışı
   DEĞİL, A1'in kendi kabul testi):** wedge/triangle/broadening için A1
   TAM TERSİ etki yaptı — sinyal sayısı 12-57 KAT ARTTI (broadening 4H:
   139→1885). Kök neden: `build_trendlines`'ın `min_touches=2` şartı SEYREK
   (ATR) pivotlarda neredeyse HİÇBİR ŞEYİ ELEMİYOR (iki nokta her zaman bir
   doğru tanımlar) — YOĞUN (fixed 3/3) pivotlarda gerçek bir filtre. Gözle
   inceleme (13 örnek) bunu doğruladı: golden_zone 5/6 gerçek, wedge/
   triangle/broadening 0/3 net gerçek (BARMA: düz bir çöküş trendi "takoz"
   olarak, ISDMR: geniş bir V dip "üçgen" olarak yanlış sınıflanmıştı).
   **Düzeltme:** `WedgeParams`/`BroadeningParams`'ın `zigzag_method`
   varsayılanı "fixed"e GERİ ÇEVRİLDİ (A1'in genel "atr" kararına bu 2
   dosya için istisna); `price_structure`'ın `_trendlines`'ı da (ayrı
   ölçülmedi ama AYNI mekanizma) artık `zigzag_method`'dan BAĞIMSIZ HER
   ZAMAN ham `find_pivots` kullanıyor (yalnızca `_zones` "atr" varsayılanını
   korudu — kümeleme mantığı farklı, o ölçümde İYİ sonuç vermişti).
   Düzeltme sonrası 2. tur gözle doğrulama: BARMA 23 sinyal→3 sinyal (tek
   mantıklı pending→confirmed→expired zinciri), GARAN'daki yanlış "paralel
   kanal" iddiası tamamen kayboldu. Golden testler (price_structure çizim
   çıktısı KASITLI değişti) regenerate edildi.
3. atr_mult=3.0 taramayla DOĞRULANDI (2.0/2.5 çok gevşek, 3.5 gereksiz katı).
4. A2/A3/A4 gerçek veriyle demo edildi, hepsi beklendiği gibi çalıştı.

**BULUNAN HATA (kapsam dışı, DÜZELTİLMEDİ, yalnızca not düşüldü):**
(1) Bazı formasyon sinyalleri (`retest_hold` durumundaki VESBE/KRPLS
örnekleri) render'da HİÇ görünmüyor — muhtemelen declutter mekanizması bu
durumun çizgilerini sistematik eliyor, Faz 3/4'ün (SVG motoru) kapsamı.
(2) `tlab plot`'un varsayılan pencereleme mantığı eski/expired sinyalleri
gösteremiyor (sinyal tarihi pencerenin dışında kalıyor, ya da sonraki büyük
bir fiyat hareketi y-eksenini o kadar genişletiyor ki eski formasyon görsel
olarak sıkışıp kayboluyor) — Faz 3/4/S4'ün kapsamı.

**Test durumu:** `pytest -q -m "not network"` **619/619 yeşil** (587→619,
+32: A1 testleri (significant_pivots + repaint hypothesis) + A2 testleri
(`for_timeframe` + `scaled_factory`) + A3 testleri (gate + `viz/live`) + A4
testleri (require_volume_confirm + preset expr)). `ruff check tlab/ tests/`
19 hata (BASELINE İLE AYNI, `git stash` ile doğrulandı — yeni kodda SIFIR).
`mypy tlab/` 1 hata (BASELINE, `renderer.py:2790`, ilgisiz). `lint_lookahead`
3 uyarı (BASELINE İLE AYNI).

**Sırada:** Adım 2 (Faz 0.5) TAMAMLANDI, onay bekleniyor. Onay gelirse
Adım 3'e (Faz 1 — klasik formasyon motoru v2, literatür düzeltmeleri:
`min_bars_between=22`, ön-trend şartı, hologram M/W silueti, OBO/TOBO neck
slope düzeltmesi) geçilecek.

**2026-09-04 EK — kullanıcı "gerçekten düzeldi mi emin misin" diye sorguladı,
haklıydı (ilk rapor yalnızca 30-sembollük bir alt-örneklem + 2 grafikle
"muhtemelen düzeldi" diyordu):** wedge/triangle/broadening için TAM 120
sembolde yeniden ölçüm yapıldı. Sonuç: 6 (gösterge×tf) kombinasyonundan 5'i
Faz 0.5 ÖNCESİKİ orijinal sayıyla BİREBİR eşleşti (wedge 1D: 30=30,
triangle 4H: 9=9, triangle 1D: 8=8, broadening 1D: 128=128; broadening
4H'te küçük fark 139→193, A2'nin YENİ zaman ölçeklemesinden — beklenen).
**Sayısal düzelme artık tam ölçekte doğrulandı.** Ek görsel inceleme (3 yeni
grafik: TUCLK×2, SKBNK) 2 YENİ kapsam-dışı bulgu daha ortaya çıkardı —
**BULUNAN HATA 3:** formasyon süresine (P1-P2 pivot mesafesi) hiç üst sınır
yok, TUCLK'de ~18 aylık gerçekçi olmayan bir "formasyon" üretildi
(`max_apex_bars` yalnızca doğum-apex mesafesini sınırlıyor) — Faz 1'in işi.
SKBNK, render'da hiç görünmeyen sinyal sorununun (BULUNAN HATA 1) ÜÇÜNCÜ
tekrarı, artık "yaygın" olarak işaretlendi. `docs/spec/SISTEMIK_DENETIM_
v1.md` bu doğrulanmış sayılar ve yeni bulgularla güncellendi (kod
DEĞİŞMEDİ, yalnızca rapor genişletildi + 2 yeni "kapsam dışı" not).

## Faz 1 — Klasik formasyon motoru v2 (Adım 3, `docs/TANI_VE_YOL_HARITASI_v2.md`)

Kullanıcı onayıyla başladı (2026-09-04). Amaç: `docs/STRATEJI_DENETIM_TAM.md`'nin
tespit ettiği literatür-uyumsuzluklarını (Bulkowski/klasik formasyon kaynaklarına göre)
`patterns/*.py` modüllerine işlemek — eski değerler ya çok gevşekti (hiçbir şeyi
elemiyordu) ya da hiç yoktu.

**1A — `tlab/features/pattern_context.py` (YENİ, paylaşılan bağlam kontrolleri):**
TAMAMLANDI. Üç saf/non-repaint fonksiyon: `rolling_trend_tstat` (kapalı-form rolling
OLS eğim+t; `momentum_rank.py`'nin ZATEN sahip olduğu aynı formülün TAŞINMIŞ hâli —
kod tekrarı giderildi), `prior_trend` (formasyon başlangıcından geriye `lookback` bar
bakıp yön+anlamlılık kontrolü — Bulkowski: çift dip/OBO/TOBO düşen bir trendden,
çift tepe/OBO yükselen bir trendden SONRA gelmeli), `pattern_depth_ok` (derinlik HEM
fiyat-yüzdesi HEM ATR-katı eşiğini AYNI ANDA geçmeli — ZOREN 4H örneğinde yalnızca
yüzde ölçütü kullanılsaydı gürültüden ayırt edilemezdi). 15 birim testi
(`tests/test_pattern_context.py`).

**1B — `patterns/double_top_bottom.py`:** TAMAMLANDI. `eq_tol` 0.02→0.015,
`min_bars_between` 5→22 (Bulkowski: en az ~1 ay), YENİ `max_bars_between` (0=sınırsız,
kasıtlı `_BAR_FIELDS` DIŞINDA — sentinel değer zaman dilimi ölçeklemesiyle 0→1'e
dönüşmesin diye), YENİ `min_rise_between_pct` (iki dip arası boyun yüksekliği),
`prior_trend`/`pattern_depth_ok` entegrasyonu, hacim kontrolü `breakout_volume_ok`'a
taşındı. Hologram, gerçek kapanış-yolu (11 nokta, amorf leke) yerine 5 köşeli M/W
silueti oldu. Test dosyası: küçük el-yapımı fixture (24 bar) yeni sıkı filtrelerle
sıfır aday üretiyordu — `_params()` fixture-kalibreli gevşek değerlere çekildi
(mekanik testler için), YENİ filtrelerin GERÇEKTEN elediğini kanıtlayan 8 ayrı negatif
test eklendi (`_base_kwargs()` + tek-parametre-sıkılaştırma deseni). 19/19 yeşil.

**1C — `patterns/head_shoulders.py` + `features/hs_pattern.py`:** TAMAMLANDI
(2026-09-04). `hs_pattern.py::find_hs`: eski `neck_slope_max` (BAR BAŞINA eğim, SABİT
eşik) YANLIŞ normalizeydi — 40 barlık bir formasyonda boyun TOPLAMDA %40 eğilebiliyordu,
fiilen hiçbir şeyi elemiyordu (bkz. STRATEJI_DENETIM_TAM.md). Yeni `neck_total_slope_max`
(varsayılan 0.15, TOPLAM/normalize eğim) ile değiştirildi; eski parametre isim uyumluluğu
için imzada duruyor ama `del`'leniyor (DEPRECATED). `head_shoulders.py`: `prior_trend`
(TOBO düşüşten, OBO yükselişten sonra) + `pattern_depth_ok` (min_depth_pct=0.04,
min_depth_atr=2.5 — çift dipten yüksek, OBO/TOBO daha büyük bir yapı olduğu için)
eklendi. **GERÇEK bir ikinci bug bulunup düzeltildi:** boyun çizgisi YUKARI eğimli
olduğunda (neckline_slope>0) eski kod hep `neckline_value_at(t)`'yi (zamanla SÜREKLİ
büyüyen bir eşik) kırılım tetikleyicisi olarak kullanıyordu — böyle formasyonlar
fiilen HİÇ tetiklenemiyordu (klasik kural: yukarı eğimli boyunda kırılım SAĞ
KOLTUKALTI/h2 seviyesinin aşılmasıdır, sabit bir seviye). Düzeltme: `break_rule =
"right_armpit" if neckline_slope>0 else "neckline"`, `_break_line` buna göre `h2.price`
(sabit) ya da `neckline_value_at(t)` (eğik) döner. Ayrıca hacim kuralı TAMAMLANDI:
eskiden yalnızca "kırılım hacmi sağ omuzdan büyük mü" (`breakout_volume_ok`)
bakılıyordu, şimdi Bulkowski'nin "hacim sol omuz/baş'ta en yüksek, sağ omuzda AZALMIŞ
olmalı" deseni de (`volume_declining_pattern`) ayrı ölçülüp `volume_profile_ok =
breakout_volume_ok and volume_declining_pattern` olarak birleştiriliyor (yalnızca
`require_volume_confirm=True` iken filtre olarak kullanılıyor, A4 deseniyle AYNI).
Test dosyası AYNI "sıkı filtreler küçük fixture'ı sıfırlıyor" deseniyle kırıldı (7/11
FAILED) — `_params()`'a `prior_trend_lookback=3` eklenerek düzeltildi (l1.bar_idx=2
olduğu için `prior_trend`'in penceresi `lookback<=3` olmadan hiç SIĞMIYOR — ampirik
doğrulama: lookback=3 → t=-116.6, defaults min_depth_pct/atr fixture'ın depth=29'unu
zaten rahatça geçiyor, gevşetmeye gerek kalmadı). 6 YENİ negatif filtre testi
(`_base_kwargs()` deseni) + `hs_pattern.py`'nin kendi test dosyasına 2 YENİ
`neck_total_slope_max` testi + **1 YENİ bilinçli-inşa edilmiş regresyon testi**
(`test_right_armpit_break_rule_used_when_neckline_slopes_upward`): h2'yi 117→130'a
çıkaran (yukarı eğimli boyun) özel bir fixture, kırılım barında kapanış (133) `h2.price`
(130)'u AŞIYOR ama o bardaki EKSTRAPOLE boyun değerini (141.56) AŞMIYOR — yani eski
(buggy) "hep neckline_value_at" mantığı bu formasyonu O BARDA hiç onaylamazdı, test bunu
sayısal olarak kilitliyor. `tests/test_patterns/test_head_shoulders.py` 11→29,
`tests/test_hs_pattern.py` +2. Tüm yeni/değişen dosyalar ruff+mypy temiz.

**BULUNAN HATA 3'ün kapanışı (2026-09-04, 1C'nin hemen ardından):** wedge/triangle/
broadening'in kendi `max_apex_bars`'ı yalnızca doğum-apex mesafesini sınırlıyordu,
P1-P2 pivot mesafesini DEĞİL — `double_top_bottom.py`'nin `max_bars_between`'iyle AYNI
mekanizma (`WedgeParams.max_bars` — hem wedge hem triangle modu kapsar,
`BroadeningParams.max_bars`) eklendi, `_passes_shape_filters`/`compute()`'a
`span > max_bars` kontrolü olarak bağlandı. **KASITLI OLARAK 0=sınırsız** (double_
top_bottom'un `max_bars_between`'iyle AYNI karar — `min_bars_between=22` gibi
literatür-doğrulanmış bir varsayılan DEĞİL, çünkü doğru eşik henüz ÖLÇÜLMEDİ; bu
1D'nin işi). 4 yeni test: `test_wedge.py::test_passes_shape_filters_rejects_span_
too_long`/`..._max_bars_zero_means_unlimited` (whitebox, `_passes_shape_filters`
doğrudan çağrılıyor — mevcut "kabul edilen" geometri fixture'ı, span=28, `max_bars=10`
ile reddediliyor), `test_broadening.py::test_max_bars_filters_out_too_long_spans`
(mevcut `test_both_directions_tracked_when_pattern_found` fixture'ı — 64 hologramın
`max_bars=1` ile SIFIRA indiği ampirik olarak doğrulandı)/`..._max_bars_zero_means_
unlimited`. Tüm 4 patterns/*.py dosyası artık BULUNAN HATA 3'e karşı en azından
opt-in bir savunmaya sahip.

**1D — DOĞRULAMA (2026-09-04, TAMAMLANDI):** `scripts/formasyon_denetim.py`
(YENİ) 120 gerçek BIST sembolünde (D1+4H) eski/yeni parametreleri karşılaştırdı
+ indikatörlere opsiyonel `context={"elim": {}}` sayaç mekanizması eklendi
(`_bump()` — double_top_bottom/head_shoulders/wedge/broadening'in HEPSİNDE,
varsayılan `context=None` davranışı DEĞİŞTİRMİYOR) + 10 rastgele confirmed
sinyal `tlab plot`'un kullandığı AYNI `render()` ile PNG'ye render edilip
`Read` ile TEK TEK açılıp incelendi. Tam sonuç `docs/spec/FORMASYON_DENETIM_
v2.md`'de. **Özet:**
- double_top_bottom 1D: 298→70 (%76.5 azalma) — SAĞLIKLI. head_shoulders 1D:
  204→141 (%30.9), 4H: 126→102 (%19.0) — ikisi de makul, en büyük eleyici
  YENİ filtreler değil `shoulder_time_ratio` (önceden var olan) çıktı.
- **KARAR GEREKTİREN GERÇEK BULGU:** double_top_bottom 4H: 125→**0** (%100).
  `min_bars_between=22`'nin (LMW, "en az 1 ay") `for_timeframe` ile 4H'e
  ×6=132 bara ölçeklenmesi TEK BAŞINA 4172 adayın TAMAMINI eliyor — double
  top/dip'in 4H'te doğası gereği çok daha kısa sürede oluştuğu (günler,
  haftalar değil) gerçeğini takvimsel ölçekleme yok sayıyor. 4 çözüm
  seçeneği raporda — Adım 4 onayından ÖNCE kullanıcı kararı gerekiyor.
- BULUNAN HATA 3 span taraması: max_bars=60→9, 90→30, 120→36, 180→62,
  250→92, sınırsız→166 confirmed (wedge+triangle+broadening, D1) — kademeli,
  tek net eşik yok; SKBNK/triangle'da 8+ aylık bir direnç çizgisinin gerçek
  apeksin son birkaç haftaya sıkıştığı GÖRSEL olarak doğrulandı, gerçek bir
  varsayılan gerekebilir ama hangi sayı olduğu ayrı bir tur gerektiriyor.
- Görsel inceleme (10/10 açıldı): ISCTR/head_shoulders TEXTBOOK kalitede bir
  OBO (sol omuz/baş/sağ omuz/boyun/kırılım/hedef hepsi net) — Faz 1 sonrası
  kalan sinyallerin GERÇEK kalitesine güçlü kanıt. 1/10 (GEDİK) render'da
  hiç görünmedi (BULUNAN HATA 1'in 3. yeni örneği, BARMA/ISBTR'yle birlikte).
- **3 YENİ, kapsam dışı bulgu** (hepsi CLAUDE.md'nin "Kaldığı yer" bölümüne
  işlendi, Faz 1'de DÜZELTİLMEDİ): (1) `renderer.py::_resolve_window_end`
  (satır 480) `last_n` parametresini hiç almıyor — `patterns.*`/`harmonic.*`
  için pencere bitişi HER ZAMAN "en son geçerli örüntü"ye göre hesaplanıyor,
  `last_n` açıkça verilse bile; en son örüntü `last_n`'in ima ettiği
  pencereden eskiyse TERS (start>end) bir x-ekseni aralığı oluşuyor — ISCTR
  `patterns.head_shoulders` 4H'te GERÇEKTEN gözlemlenip teşhis edildi. (2)
  `patterns.broadening`'in hologram poligonu (ham pivot noktalarını
  birleştirdiği için) created_idx'e doğru YAKINSAYAN bir kama gibi
  görünüyor — `patterns_geom.py::diverging_lines` (satır 140-151) kod
  incelemesiyle MATEMATİKSEL OLARAK doğru bulundu (created_idx SONRASI ileri
  yönde ıraksamayı test ediyor), bu yüzden bu bir SINIFLANDIRMA hatası değil,
  bir ANLATIM/görsel netlik sorunu (BARMA/ODINE/IZMDC/ISBTR'nin HEPSİNDE
  gözlemlendi). (3) ISBTR sembolünün 4H önbellek verisi 400.000-680.000 TL
  aralığında — BIST için gerçekçi değil, veri kalitesi şüphesi.
- Yöntem notu: `compute_live()` TAM geçmişi çekiyor (ölçüm betiğinin
  `last_n=600`'ü ile UYUŞMUYOR) — bu, ISCTR'de render'ın sayımdaki TOBO
  yerine farklı bir OBO göstermesine yol açtı (görsel örnekler AYNI 600-bar
  df ile yeniden render edilerek düzeltildi, ama genel `tlab plot` iş akışı
  hâlâ bu kırılganlığı taşıyor).

**Adım 3 sonrası onay kapısı — KAPANDI (2026-09-04, aynı gün):** Kullanıcı
4 seçeneği (raporda listelenen) değerlendirip en avantajlısının uygulanmasını
istedi. Daha derin araştırma GERÇEK kök nedeni buldu (4 seçeneğin hiçbiri
tam doğru çerçeve değildi):

1. **`tlab/core/params.py::_TF_BAR_SCALE` düzeltmesi (SİSTEMİK):** eski
   1H=24/4H=6 katsayıları "gün 24 saat sürekli işlem görür" varsayımına
   dayanıyordu. BIST seansı 10:00-18:00 (8 saat); `data/resample.py`'nin
   09:00/13:00/17:00 hizalamasıyla GERÇEK ISCTR verisinde ölçülen bar/gün:
   1H=9, 4H=3 (mode). Düzeltildi: 1H=9.0, 4H=3.0. Bu, double_top_bottom'un
   YANI SIRA `prior_trend_lookback` gibi HER `_BAR_FIELDS` alanını doğru
   kalibre etti — tek bir göstergeye özel değil, sistemik bir düzeltme.
2. **`DoubleTopBottomParams.min_bars_between`'in `_BAR_FIELDS`'ten
   ÇIKARILMASI (özel):** #1'in düzeltmesiyle bile (132→66 bar 4H'te) HÂLÂ
   sıfıra yakın sinyal vardı (30 sembolde 0/20). Derin ölçüm: ATR-zigzag'de
   eşleşen p1→p2 pivot aralığı BAR SAYISI olarak zaman diliminden NEREDEYSE
   BAĞIMSIZ (120 sembol, medyan: 1D=27.5 bar, 4H=29 bar — ALMOST AYNI).
   Mekanik açıklama: ATR kendisi bar granülaritesine göre ölçekleniyor
   (4H'teki bir ATR birimi 1D'dekinden küçük), "3×ATR'lik bir tersine
   dönüş" biriktirmek bu yüzden HER İKİ zaman diliminde kabaca AYNI SAYIDA
   bar alıyor — ATR-zigzag pivot mesafeleri kendi doğasında zaman-dilimi-
   DEĞİŞMEZ (self-similar). Takvimsel ölçekleme bu alan için YANLIŞ modeldi.
   `min_bars_between` `_BAR_FIELDS`'ten çıkarıldı (artık HİÇBİR TF'de
   ölçeklenmiyor, her zaman ham 22) — `prior_trend_lookback` (kapanış
   fiyatı OLS penceresi, GERÇEKTEN takvimsel) hâlâ ölçekleniyor.

**Sonuç (120 sembol, TAM yeniden ölçüm):** double_top_bottom 1D DEĞİŞMEDİ
(298→70, sorun zaten yoktu); 4H **497→72 (%85.5 azalma)** — D1'in %76.5'ine
yakın, SAĞLIKLI, gösterge artık 4H'te fiilen devre dışı DEĞİL. ("Eski"
sayı 4H'te 125'ten 497'ye çıktı çünkü "eski" yeniden-inşası da artık
`min_bars_between=5`'i hiç ölçeklemiyor — tutarlılık için gerekli bir
yan etki.) wedge/broadening/head_shoulders bu düzeltmeden ETKİLENMEDİ
(`min_bars`/`max_apex_bars` zaten p95'in çok altında kalıyordu — zeroing
riski yoktu).

Değişen dosyalar: `tlab/core/params.py` (_TF_BAR_SCALE), `tlab/indicators/
patterns/double_top_bottom.py` (_BAR_FIELDS + uzun gerekçe yorumu),
`tests/test_core_params.py`, `tests/test_scanner/test_timeframe_scaling.py`,
`tests/test_scanner/test_bootstrap.py` (3 test dosyası yeni katsayılara +
min_bars_between'in artık ölçeklenmediğine göre güncellendi). 656 test
yeşil (655→656, +1 yeni regresyon testi), ruff/mypy/lint_lookahead baseline
ile birebir. `docs/spec/FORMASYON_DENETIM_v2.md`'ye "KAPATILDI" bölümü
eklendi (orijinal 4-seçenekli analiz ARŞİV olarak dosyada kalıyor).

**Faz 1 TAMAMEN BİTTİ.**

## Faz 2 — İstatistiksel arbitraj v2 (Adım 4, `docs/TANI_VE_YOL_HARITASI_v2.md` `## FAZ 2`)

Kullanıcı onayıyla başladı (2026-09-04). Amaç: "arbitraj çok fazla sinyal veriyor"
şikayetinin GERÇEK kökü (ham ADF'nin tahmin edilmiş kalıntıya yanlış uygulanması +
düzeltmesiz çoklu-test, bkz. tanı bölüm 1.4) — 606 sahte çifti ~20-40 gerçeğe indirmek
+ rotasyonel motorun yanına gerçek bir market-neutral mod eklemek.

**2A — `tlab/features/stats.py` (YENİ fonksiyonlar):** TAMAMLANDI.
`engle_granger_pvalue` (statsmodels `coint`, MacKinnon kritik değerleri — `adf_pvalue`'nun
"TAHMİN EDİLMİŞ kalıntıya UYGULAMA" uyarısıyla belgelendi), `ols_spread` (intercept'li TEK
OLS, tanının (e) bulgusu: eski `log_spread` alpha'yı hiç çıkarmıyordu), `benjamini_hochberg`
(standart BH-FDR, elle hesaplanmış klasik bir örnekle doğrulandı). 24 yeni test
(`tests/test_stats.py`).

**2B — `tlab/indicators/pairs/discovery.py` v2:** TAMAMLANDI. `adf_pvalue`→
`engle_granger_pvalue`; iki yönün minimumuna Šidák düzeltmesi (`p_cift=1-(1-min(p1,p2))^2`);
YENİ `fdr_q=0.05` (TÜM denenen kombinasyon sayısı `n_tests` üzerinden BH-FDR — Faz 2
tanısının referans M'siyle AYNI yöntem, corr/halflife eşiklerinden BAĞIMSIZ hesaplanır);
YENİ `oos_split=0.5` (seçim ilk yarıda, kointegrasyon ikinci yarıda YENİDEN test edilir —
DISIPLIN-06'nın fiili çözümü); YENİ `economic_link_map` (+ `config/economic_links.yaml`,
5 grup — KCHOL/Sabancı/Şişecam/EREGL-KRDMD/TUPRS-PETKM). `same_sector_only=False` (tüm
evren) artık `fdr_q` ZORUNLU kılıyor (`ValueError`) — "SEKTÖR MU TÜM EVREN Mİ" kararı
(Do & Faff 2010 + 24x çoklu-test yükü farkı) docstring'e işlendi. `PairCandidate`'e
`p_raw`/`p_adjusted`/`n_tests`/`fdr_passed`/`adf_p_is`/`adf_p_oos` eklendi. 14 test.

**2C — Pair motoru v2:** TAMAMLANDI. `tlab/backtest/pairs_engine.py::
run_pair_backtest_market_neutral` (YENİ) — beta-ölçekli EŞ ZAMANLI long/short muhasebesi
(`MarketNeutralTrade`/`MarketNeutralBacktestResult`); GERÇEK bir muhasebe hatası bulunup
düzeltildi (ilk taslak, pozisyon KAPANDIĞINDA yalnızca gerçekleşen PnL'i nakite ekleyip
YATIRILAN ANAPARAYI unutuyordu — fiyat giriş seviyesine dönüp PnL=0 olduğunda bile portföy
0'a düşüyordu; `position_gross` takibiyle düzeltildi, regresyon testiyle kilitlendi).
`tlab/indicators/pairs/relative_momentum.py::RelativeMomentumParams.mode="mean_reversion"`
(YENİ, "rotational" varsayılanı BİREBİR korunuyor — `_compute_rotational`/`_compute_mean_
reversion` olarak ikiye ayrıldı) — `exit_k`/`stop_k`/`max_hold_bars`/`lockout_until_reentry`
ile gerçek bir nakit/flat hâli olan istatistiksel arbitraj (referans: awesome-quant-ai
chapter2). YENİ `tlab/indicators/pairs/coint_monitor.py` (CLAUDE.md backlog madde 4) —
rolling Engle-Granger p-değeri izleyicisi, `RelativeMomentumParams.coint_monitor_window`
(opsiyonel, varsayılan `None`=kapalı) ile mean_reversion moduna "mr_cointegration_broken"
zorunlu-çıkış olarak bağlandı. 22 + 17 + 6 test (relative_momentum/pairs_engine/coint_monitor).

**2E — Arayüz adlandırması:** TAMAMLANDI. `tlab/viz/labels_tr.py`'de `INDICATOR_CATEGORY_TR
["pair"]` "Pair (Rölatif Momentum)"→"İstatistiksel Arbitraj". Gerçek (risksiz) arbitrajın
kapsam dışı olduğu notu CLAUDE.md'de zaten mevcuttu (K2 STRAT-09/ch3, "PARK").

**Test durumu:** 702/702 yeşil (655→702, Faz 1 sonrasından +47), `ruff check tlab/ tests/`
19 hata (BASELINE İLE AYNI), `mypy tlab/` 1 hata (BASELINE). `lint_lookahead` 3→**5**
(YENİ 2'si `coint_monitor.py`'nin `.iloc[t-window+1:t+1]` pencere dilimlemesi — mevcut 3
baseline false-positive'iyle AYNI kalıp, geriye-bakan/non-repaint, `rolling_beta`/pattern_
context.py'nin ZATEN kullandığı desen, LA004'ün naif regex'i yakalıyor).

**Sırada — 2D (doğrulama):** `scripts/pair_denetim.py` (YENİ) yazıldı, çalıştırılıyor —
mevcut 606 çifti `engle_granger_pvalue` ile yeniden doğrular + `discover_pairs` v2'yi
(coint+Šidák+FDR+OOS) sıfırdan koşup `config/pairs.yaml`'ı yeniden üretir (eskisi
`config/pairs_v1_deprecated.yaml`'a taşınır) + `docs/spec/ARBITRAJ_DENETIM_v2.md` yazar.
**İlk sonuç (606 eski çiftin yeniden doğrulaması TAMAMLANDI):** 606 çiftten yalnızca 288'i
hâlâ ham p<0.05 (yarısından fazlası zaten ESKİ testin kendi şişirmesinden kaynaklıydı),
BH-FDR (q=0.05, M=579 fiyatlanabilen çift) geçen yalnızca **141** — tanının "606→20-40"
beklentisinden BİLE daha az agresif ama AYNI yönde güçlü bir doğrulama. `discover_pairs`
v2'nin sıfırdan taraması (7334 aynı-sektör+ekonomik-bağ kombinasyonu)
TAMAMLANDI (`docs/spec/ARBITRAJ_DENETIM_v2.md` yazıldı).

**KARAR GEREKTİREN GERÇEK BULGU:** sıfırdan keşif `fdr_q=0.05` + `oos_split=0.5`'in
(discover_pairs()'ın KOD OLARAK sevk edilen varsayılanları, AYNI ANDA) BİRLEŞİK etkisiyle
606 çifti yalnızca **1**'e indirdi (PEKGY/EYGYO, Gayrimenkul). Elenme sebebi ayrıştırıldı
(aynı 7334-kombinasyonluk veri, kademeli sıkılaştırma): düzeltilmiş test (coint+Šidák+
corr/halflife) → **222**; + BH-FDR (q=0.05) → **17** (A'dan %92 azalma); + OOS (oos_
split=0.5) → **1** (B'den %94 azalma). **OOS, FDR'den bile daha agresif bir filtre** —
Faz 2 tanısının kaynak tablosundaki "606→36" rakamı yalnızca FDR'yi temsil ediyordu
(B satırına yakın, 17 vs 36, aynı mertebe), OOS'u DEĞİL; `discover_pairs()`'ın ikisini
BİRDEN varsayılan yapması 2B'de bilinçli bir tasarım kararıydı (DISIPLIN-06'yı koda
gömmek) ama SONUCU (1 çift) o an ÖLÇÜLMEMİŞTİ. `config/pairs.yaml` bu 1 çiftlik sonuçla
YENİDEN ÜRETİLDİ (eski liste `config/pairs_v1_deprecated.yaml`'a taşındı). 3 seçenek
raporda: (1) mevcut en-katı ayarı koru (1 çift, ama `LOOKBACK_BARS` artırılırsa OOS'un
gücü artabilir, ÖLÇÜLMEDİ), (2) `oos_split=None`'a çek (yalnızca FDR, **17 çift** —
tanının hedefine ÇOK daha yakın, OOS mekanizması SİLİNMİYOR, elle hâlâ kullanılabilir),
(3) `oos_split`'i gevşet (ör. 0.7, ÖLÇÜLMEDİ). Kâr/zarar karşılaştırması (mean_reversion
vs rotasyonel) N=1 çiftle istatistiksel olarak ANLAMSIZ olduğu için AYRI bir tura
bırakıldı (kullanıcı kararından sonra, ≥17 çiftle yapılmalı).

**Adım 4 sonrası onay kapısı — KAPANDI (2026-09-04, aynı gün):** `docs/spec/
ARBITRAJ_DENETIM_v2.md`'nin özeti + 17 çiftin tam listesi (sembol/sektör/corr/p/
halflife/beta) + 4 çiftin (AKBNK/VAKBN, ADGYO/PEKGY, FONET/EDATA, IZMDC/ISDMR)
gerçek `mode="mean_reversion"` backtest sonuçları (gerçek BIST verisiyle, işlem
bazında tarih/getiri) kullanıcıya sunuldu. Kullanıcı ayrıca "config/pairs.yaml sabit
bir liste mi, listede olmayan çiftler (TOASO/FROTO, ASELS/SDTTR örnek verdi) hiç
sinyal veremez mi" sorusunu sordu — kod incelenip (`tlab/scanner/engine.py::run()`,
`for y_sym, x_sym in pairs or []`) NET cevap verildi: EVET, sabit liste, listede
olmayan çift ASLA otomatik sinyal üretmez (3 örnek de test edildi, hiçbiri corr/
kointegrasyon eşiğini geçmiyor: ASELS/SDTTR corr=0.15, TOASO/FROTO corr=0.48/p~0.9,
TCELL/TTKOM corr=0.75 ama p~0.3-0.5 — "korelasyon kointegrasyon değildir" örneği).

**KARAR: Seçenek 2 — `oos_split=None`, 17 çift.** Gerekçe: sayı tanının "20-40"
hedefine daha yakın; backtest örnekleri karışık olsa da (FONET/EDATA +%12/%78
kazanma, ADGYO/PEKGY −%25/%44 kazanma) kullanıcı bunu bilerek seçti. Uygulandı:
`config/pairs.yaml` 17 çiftle YENİDEN üretildi (başlık metni `oos_split=None`'ı
doğru yansıtacak şekilde elle düzeltildi — `_write_pairs_yaml` eskiden HER ZAMAN
"oos_split=0.5" yazıyordu, artık gerçek `fdr_q`/`oos_split` değerlerini parametre
olarak alıp dinamik yazıyor). `scripts/pair_denetim.py::main()`'in varsayılanı da
(`FDR_Q=0.05, OOS_SPLIT=None`) bu kararı yansıtacak şekilde güncellendi — ileride
betik tekrar çalıştırılırsa AYNI kararı üretir. `docs/spec/ARBITRAJ_DENETIM_v2.md`
"KAPATILDI" bölümüyle güncellendi (orijinal analiz ARŞİV olarak kalıyor).

**Faz 2 EK — 116 çift denemesi + mean_reversion parametre optimizasyonu
(2026-09-04, aynı gün):** Kullanıcı "sadece 17 çifte mi bağlı kalacağız,
TOASO/FROTO gibi çiftleri kaçırır mıyız" diye sordu. Mimari netleştirildi:
`config/pairs.yaml` SABİT bir liste, `tlab/scanner/engine.py::run()` yalnızca
bu dosyadaki çiftler için iş açar — TOASO/FROTO zaten aynı-sektör
kombinasyonuna dahildi (test edildi: corr=0.48, p≈0.9 — gerçekten kointegre
DEĞİL, kaçırılmış bir fırsat değil). Kullanıcı eşikleri gevşetip (corr≥0.5,
adf_max=0.10, fdr_q=0.10) **116 çiftlik** bir liste üretmemi istedi — 17'nin
tamamı bu 116'nın içinde. Aynı zamanda tüm-evren (`same_sector_only=False`,
209.628 kombinasyon) bir tarama başlatıldı ama kullanıcı bunun çok
süreceğini fark edip DURDURDU (`TaskStop`) — 116 çiftin `mode="mean_
reversion"` ile GERÇEK backtest'ini istedi. **Sonuç: 116 çift, 17'den
DAHA İYİ DEĞİL** — 59/116 (%51) kârlı, medyan getiri +%0.28 (17'nin
medyanı +%0.13'e çok yakın), ortalama getiri (+%11.89) yalnızca TEK bir
aykırı değerden (RGYAS/KGYO, +%1017 — muhtemelen ISBTR'dekiyle AYNI türde
bir veri anomalisi, RGYAS'ın AKSGY ile başka bir çiftte AYNI dönemde −%20
vermesiyle doğrulandı) şişmişti. Kullanıcı kendi kriterine göre ("kötü
sonuç verirse mevcut duruma dön") **17 çiftte kalmaya karar verdi.**

Ardından kullanıcı `mean_reversion` parametrelerini (window/k/exit_k/
stop_k/max_hold_bars) backtest ile optimize etmemi istedi. **Metodoloji
(overfitting'e karşı):** 17 çiftin ~600 barlık verisi %60/%40 in-sample/
out-of-sample olarak bölündü (rolling istatistiklerin "soğumaması" için
TAM seriye göre hesaplanıp işlemler GİRİŞ tarihine göre IS/OOS'a
ayrıldı — cold-start artefaktı yok), 243 kombinasyon (`window`∈{20,40,60},
`k`∈{1.5,2.0,2.5}, `exit_k`∈{0.25,0.5,0.75}, `stop_k`∈{2.5,3.0,4.0},
`max_hold_bars`∈{20,40,60}) TÜM 17 çift için IS'te ve OOS'te ayrı ayrı
skorlandı. **Bulgu:** IS'te en iyi 15 kombinasyonun ÇOĞU OOS'ta kazanma
oranı %50'nin ALTINA düşüyordu (klasik aşırı-uyum) — ama `stop_k=4.0`
(eski varsayılan 3.0'dan gevşek), BİRÇOK farklı `window`/`k`/`exit_k`
kombinasyonunda TUTARLI şekilde OOS performansını iyileştiriyordu (tek
"şanslı hücre" değil). `window`/`k` SABİT tutulup (rotasyonel modun da
PAYLAŞTIĞI alanlar, 2026-08-29'da AYRI bir kararla kalibre edilmişti,
Faz 2 2C'nin "rotasyonel motoru bozma" ilkesi) yalnızca mean_reversion'a
ÖZGÜ alanlar (exit_k/stop_k/max_hold_bars) taranınca: **stop_k 3.0→4.0,
max_hold_bars 30→40** (exit_k=0.5 zaten en iyisiydi, değişmedi) OOS
kazanma oranını %53.2→%53.5, medyan getiriyi 0→+%0.86'ya çıkardı (n=43
OOS işlem). `RelativeMomentumParams`'ın bu iki varsayılanı GÜNCELLENDİ
(kilitleyen test: `test_mean_reversion_default_stop_k_and_max_hold_bars_
tuned`). **Dürüst not:** bu KÜÇÜK bir edge (kazanma oranı %50'den yalnızca
birkaç puan yukarıda) — 17 çift/~2.4 yıllık veriyle istatistiksel güç
sınırlı, "büyük bir kâr formülü bulundu" denemez.

**Faz 2 TAMAMEN BİTTİ.** Sırada: **Adım 5 — Faz 3 (SVG çizim motoru)**,
`docs/TANI_VE_YOL_HARITASI_v2.md`'nin `## FAZ 3` bölümü.

## 2026-09-04 — Adım 5 / Faz 3 (SVG çizim motoru — çekirdek)

**Amaç:** Grafiklerin `docs/design/grafik_stil_vitrini.html` artifact'ine
benzememesinin kök nedenini (Plotly'nin etiket-çakışma çözücüsü/önder-
çizgili kutu/hap rozet/sahneye özel yerleşim eksikliği) ortadan kaldırmak
— saf SVG üreten YENİ bir motor (`tlab/viz/svg/`). Bu faz hiçbir sahne
çizmedi (Faz 4'ün işi), yalnızca motoru + TEK kanıt sahnesini kurdu.

**Referans dosyasının bulunması — kendi başına bir problem.** `docs/
design/grafik_stil_vitrini.html`in yerel kopyası (`docs/design/`e daha
önceki bir oturumda kaydedilmiş) 5 dev satırlık, 158k+ token'lık bir
dosyaydı; Read/Grep başarısız oldu. Python ile incelenince bu dosyanın
gerçek artifact İÇERİĞİ DEĞİL, Claude.ai Artifacts görüntüleyicisinin DIŞ
çerçeve-kabuğu (frame-runtime bootstrap JS) olduğu anlaşıldı — gerçek
sahne kodu bir iframe'e dinamik yükleniyor, tarayıcının "Kaynağı
Görüntüle"si bunu hiç yakalamamış. Dosyanın içindeki bir HTML yorumundan
(`saved from url=...`) artifact'in kendi `claude.ai/code/artifact/...`
URL'i çıkarılıp `Artifact(action="read")` ile YENİDEN okundu — bu, kaydı
kullanıcı-sahipli bir artifact olarak doğruladı ve gerçek 1975 satırlık
HTML'i yerel bir dosyaya kaydetti. O dosya BAŞTAN SONA okunarak (aracın
"görüntülenmiş sayılması" için zorunlu koşul) gerçek altyapı kodu
(`seeded`/`svgLine`/`svgRect`/`svgPoly`/`svgText`/`svgCircle`/`pill`/
`makeChart`/`drawCandles`/`niceTicks`/`priceLabels`/`xLabels`/
`glowFilterDefs`/`THEMES` — 5 tema: classic/dark/editorial/saas/neon) ve
`sceneDoubleTopBottom` (satır 764-844) bulundu.

**3A — Modül yapısı.** `tlab/viz/svg/{prim,scale,candles,axes,layout,
theme}.py` + `scenes/{base,double_top_bottom}.py` + `__init__.py::
render_svg`. `prim.py`nin string üreteçleri (svg_line/rect/poly/text/
circle/pill) artifact'in JS fonksiyonlarının birebir Python karşılığı —
XML kaçışı (`escape_xml`, 5 karakter) burada JS'ten DAHA titiz (JS yalnızca
`&`/`<` kaçırıyordu). `scale.py::Chart`in X ekseni BAR-İNDEKSLİDİR (zaman
değil) — bu, hafta sonu/seans dışı boşlukları otomatik olarak GÖSTERMEZ
hâle getiriyor (mevcut Plotly `renderer.py`'nin `rangebreaks` ile elle
çözdüğü sorunun bar-indeksli eksende DOĞAL çözümü). `theme.py::SVGTheme` —
`tlab/viz/themes.py::Theme`nin (Plotly dönemi) YAKLAŞIK eşlemesi yerine
artifact'in kendi hex değerleri temel alındı; TESPİT EDİLEN FARK: `Theme.
muted` artifact'in `neckline` alanıyla YALNIZCA editorial'da tam eşleşiyor,
classic/dark'ta birkaç hex birimi farklı — spec'in talimatına uyularak
artifact DOĞRU KABUL EDİLDİ (yeni, bağımsız bir `SVGTheme` yazıldı).

**3B — `layout.py::resolve_collisions` (motorun asıl YENİ katkısı).**
Artifact'te YOK olan, Plotly'de de YOK olan bir yetenek: genel amaçlı
etiket-çakışma çözücü. Mevcut `renderer.py::_stagger_yshifts`/
`_declutter_levels`in ilkel hâliydi — onlar BİLGİ SİLEREK (yalnızca en
güncel grubu göster) çözüyordu; bu motor "yerini bul, sığmıyorsa
öncelikle ele (drop)" ilkesiyle çalışır: `LabelBox` listesi önceliğe göre
sıralanır, her biri tercih sırasına göre (above/below/right/left) denenir,
çakışırsa dikey/yatay adımlarla itilir (`max_push` sınırına kadar), hâlâ
sığmazsa DROP edilir (`CollisionResult.dropped` — sessizce kaybolmaz).
`leader_line` çapa noktasından kutunun en yakın kenarına ince bir çizgi
çizer (yalnızca `needs_leader=True` iken). 4 saf-fonksiyon testi spec'in
BİREBİR istediği 4 senaryoyu doğruluyor (iki üst üste kutu ayrışması,
sınıra taşan kutunun içeri çekilmesi, 50-kutu-tek-noktada düşük-öncelik
drop, determinizm).

**3C — Tek sahnelik kanıt: `patterns.double_top_bottom`.** Artifact'in
`sceneDoubleTopBottom`i UYDURMA pivotlarla, sahneye özel el-ayarlı
ofsetlerle çiziyordu. Port edilen versiyon gerçek `IndicatorResult`tan
okur (`_group_patterns`: `Level.label`deki `{pattern_id}_neckline`/
`_target` son ekleri, `Polygon.label`deki `_hologram`, `Marker.kind`deki
`pattern_vertex:`/`pattern_entry_` önekleri, `Signal.payload["pattern_id"]`
üzerinden gruplanır — yön `target.price < neckline.price` karşılaştırmasıyla
SAF SAYISAL türetilir, string eşleştirme YOK). **TÜM değişken-konumlu
etiketler** (boyun yazısı, kırılım, onay, hedef metni, hedef rozeti,
AL/SAT) `resolve_collisions`e verilir — artifact'in aksine hiçbiri elle
konumlanmaz.

Pencere seçimi CLAUDE.md'nin "Faz 0.5'te bulunan, henüz kapatılmamış"
listesindeki **BULUNAN HATA 2**yi (`tail(last_n)` sabit penceresi eski
sinyalleri kadraj dışına atıyordu) bu sahne için KAPATIYOR: sabit "son N
bar" yerine formasyonun p1 pivotundan son sinyaline kadar SIĞACAK bir
pencere seçilir (`_pattern_window`).

**Zorunlu doğrulama döngüsü — 4 iterasyon (istenen ≥3), GERÇEK BIST
verisiyle, PNG'ler her seferinde GÖRÜLEREK:**
1. BAKAB/classic: baseline çalışıyor ama hedef rozeti (elle konumlanmış,
   collision havuzuna girmemiş) panel kenarını taşıyor; retest ("Onay:
   Test Tuttu") hiç çizilmiyor.
2. BAKAB/classic: rozet `resolve_collisions`e taşındı (kenar taşması
   düzeldi); retest marker eklendi; "1"/"2" rozet dikey ofseti yön-tutarlı
   hâle getirildi.
3. BAKAB/dark+editorial, CELHA/classic (tek sinyal — single-panel yolu):
   3 tema da doğrulandı (glow/renk/font birebir); TUCLK/classic (3 aday,
   çoklu durum) ile **GERÇEK bir hata bulundu** — GEÇERSİZLEŞMİŞ bir
   aday hâlâ "ONAY" rozeti taşıyordu (durum, yalnızca `completed` sinyaline
   bakılıp geri kalan her durumda koşulsuz "ONAY" yazan saf hâliyle
   yanıltıcıydı).
4. TUCLK/classic: durum rozeti artık `result.signals`daki GERÇEK
   breakout/retest/completed/invalidated/expired olaylarından türetiliyor
   (`tlab/core/pattern_state.py::SUFFIX_LABEL_TR` ile aynı sözlük);
   GEÇERSİZ/SÜRESİ DOLDU'da hedef çizgisi/metni artık ÇİZİLMİYOR.

**Bilinen sınırlama:** proje önbelleğindeki (`data/ohlcv/bist/`) TÜM
semboller ~506 barlık (yfinance varsayılan derinliği) bir pencereye sahip
— spec'in istediği "çok uzun geçmişli sembol" senaryosu GERÇEK anlamda
test edilemedi; TUCLK'nin 3 eş-zamanlı aday/durum çeşitliliği en yakın
makul vekil olarak kullanıldı, dürüstçe not edildi.

**Performans (BAKAB, 20 tekrar ortalaması):** SVG metin üretimi 21.0ms
(Plotly figure kurulumu 37.6ms'e göre ~%45 daha hızlı), SVG+`resvg_py`
PNG rasterleştirme 142.5ms — Plotly+kaleido'nun (ısındıktan sonra bile)
1880.6ms'ine göre **~13x daha hızlı**, headless Chromium alt-süreç
bağımlılığı da YOK.

**3D — Entegrasyon.** `tlab/viz/live.py::render_live`e `engine:
Literal["svg","plotly"]` parametresi eklendi. **Varsayılan BİLİNÇLİ OLARAK
`"plotly"` kaldı** (spec'in önerdiği "svg" DEĞİL) — 3 mevcut çağıran
(`tlab/cli.py::plot`, `tlab/dashboard.py`, `tlab/viz/report.py::
ensure_chart`) hâlâ koşulsuz `go.Figure` API'sine (`.write_image`/
`.write_html`/Streamlit) bağımlı; varsayılanı `svg` yapmak TEK bir
portlanmış gösterge (`patterns.double_top_bottom`) için bu üçünü SESSİZCE
kırardı. `@overload` ile tiplendi (engine="svg" verilmeden çağıranlar
mypy'de hâlâ saf `go.Figure` görür — bu ikilik gerçek bir mypy hatası
üretiyordu, `@overload` ile düzeltildi). YENİ `web/backend/routes/
chart_svg.py` (`GET /api/chart.svg -> image/svg+xml`, portlanmamış bir
gösterge 422 döner, sessizce Plotly'e düşmez). `chart_png.py` artık
`render_live(engine="svg")` çağırıyor — SVG sahnesi olan göstergeler için
PNG `resvg_py` ile rasterleştirilir (kaleido'ya hiç uğramaz), portlanmamış
göstergeler eski Plotly+kaleido yoluna otomatik düşer. Her iki route
`TestClient` ile uçtan uca doğrulandı (200/image-content-type + 422
unsupported-indicator senaryoları).

**Test:** 34 yeni birim testi (`tests/test_viz/test_svg/`) + 1 yeni
golden test (`svg_double_top_bottom_classic.svg`, mevcut `test_golden.py`
makinesini `ext="svg"` ile paylaşıyor) = 35 yeni, **738 test yeşil**
(703→738). ruff (baseline 19, DEĞİŞMEDİ — 33 yeni E501/tip hatası bulunup
satır-sarma ile temizlendi), mypy (baseline 1, DEĞİŞMEDİ — `render_live`nin
union dönüş tipi 4 yeni hata üretmişti, `@overload` + iki değişken-adı
çakışması düzeltmesiyle giderildi). lint_lookahead 5 uyarı VAR ama HİÇBİRİ
bu fazın dosyalarında değil (CLAUDE.md'nin "3" rakamı `coint_monitor.py`nin
önceki bir oturumda eklenmesinden beri güncellenmemiş bir belge hatası,
ayrıca not edildi).

**Faz 3 TAMAMLANDI** — detay + tam bitti-kriteri karşılaştırması `docs/
spec/FAZ3_SVG_MOTORU.md`de. Bu, roadmap'in dört onay kapısından biri
("Faz 3'ün ilk sahnesi... sana gösterilmeden bir sonraki adıma
geçilmemeli") — kullanıcı onayı BEKLENİYOR, Faz 4'e (kalan 18 sahnenin
portu, 3 oturuma bölünecek) henüz geçilmedi.

## 2026-09-04 (aynı gün, Faz 3'ten SONRA) — `mean_reversion` stop_k/max_hold_bars İKİNCİ TUR revizyonu

Kullanıcı, daha önce (bugünün Faz 2 bölümünde) `outputs/reports/
param_grid_results.json`a kaydedilen 243-kombinasyonluk IS/OOS parametre
taramasının SONUCUNU yeniden, daha titiz bir aşırı-uyum (overfitting)
kontrolüyle analiz etmemi istedi (arka planda çalıştırdığı bir görev
kimliğiyle sordu, o görev bu oturumun kendi görev listesinde bulunamadı —
ama sonuç dosyası zaten TAM ve diskteydi, doğrudan ondan analiz edildi).

**Analiz:** IS kazanma oranına göre en iyi 15 kombinasyonun **8'i** OOS'ta
kazanma oranı %50'nin altına düşüyordu (bazıları %40'a kadar) — klasik
aşırı-uyum. İlk turda seçilen mevcut varsayılan (`stop_k=4.0, max_hold_
bars=40`) bu düşüşten kaçan az sayıdaki adaydan biriydi (OOS win %53.5),
ama `window=60,k=2.0,exit_k=0.5` sabit tutulup yalnızca `stop_k`/`max_hold_
bars` alt-tablosuna bakılınca `stop_k=3.0`'ın test edilen HER ÜÇ `max_hold_
bars` değerinde de (20/40/60) `stop_k=4.0`'ı OOS medyan getiride sistematik
olarak geçtiği görüldü (~1.58-1.65% vs ~0.39-0.86%) — tek şanslı hücre
değil, tutarlı bir kalıp. Ayrıca ızgaranın TAMAMI üzerinden (diğer 4
parametre ortalanarak) hesaplanan MARJİNAL etki de aynı yönü doğruladı:
`stop_k=3.0`'ın ortalama OOS medyanı (+0.105) `stop_k=4.0`'ınkinden
(−0.075) daha iyi, kazanma oranları pratikte eşit (~46.4 vs ~46.2) —
yani ilk turun "4.0 daha iyi" sonucu IS'e göre seçilmiş bir yanılsamaydı,
OOS'a göre DEĞİL.

**Sonuç/karşılaştırma tablosu kullanıcıya sunuldu**, `stop_k=3.0 + max_
hold_bars=60` (ızgaranın TÜMÜNDEKİ en yüksek OOS medyan getiri, +1.65%,
OOS kazanma %55.6) önerildi — `stop_k=3.0 + max_hold_bars=40` (neredeyse
eşit, +1.58%) alternatif olarak not edildi. Dürüst uyarı da eklendi: OOS
hücre başına ~43-59 işlem var, %53-56 aralığındaki fark tek başına
istatistiksel kesinlik taşımaz; güveni artıran şey üç farklı `max_hold_
bars` değerinde ve ızgara-geneli marjinal ortalamada AYNI yönün
tekrarlanmasıydı.

**Kullanıcı onayladı** ("tamam onaylıyorum"). Uygulanan değişiklik:
`RelativeMomentumParams.stop_k` 4.0→**3.0**, `max_hold_bars` 40→**60**
(`tlab/indicators/pairs/relative_momentum.py`, docstring GENİŞLETİLEREK
her iki turun gerekçesi de korundu — ilk turun "neden 4.0" mantığı SİLİNMEDİ,
"ikinci tur neden 3.0'a geri döndü" ile birlikte anlatıldı). Kilitleyen
test (`tests/test_pairs/test_relative_momentum.py::
test_mean_reversion_default_stop_k_and_max_hold_bars_tuned`) yeni
değerlere ve yeni gerekçeye göre GÜNCELLENDİ. `window=60`/`k=2.0` yine
DEĞİŞMEDİ (rotasyonel modla paylaşılan alanlar, 2026-08-29 kararı).
738 test yeşil, ruff/mypy baseline'ları DEĞİŞMEDİ.

**Not (aynı parametrenin ikinci kez gidip gelmesi):** bu, `stop_k`'nin
AYNI oturum içinde 3.0→4.0→3.0 şeklinde iki kez değişmesi demek — kasıtlı
bir kararsızlık değil, İKİNCİ analizin İLK analizin gözden kaçırdığı bir
IS/OOS ayrışmasını (seçim kriterinin OOS yerine IS'e dayanması) düzeltmesi.
İleride bu alan tekrar gözden geçirilirse, her iki turun da gerekçesi
kodda ve bu günlükte duruyor.

## 2026-09-04 (aynı gün) — Faz 3 vitrini geri bildirimi: hologram üçgen düzeltmesi (5. iterasyon)

Kullanıcı, `docs/spec/FAZ3_SVG_MOTORU.md`nin galeri artifact'ini inceledikten
sonra kendi TradingView referansını (`TOBO.png`, ters omuz-baş-omuz
formasyonu) paylaşıp `patterns.double_top_bottom` hologramının "yarım
üçgen gibi" durduğunu belirtti — boyun çizgisinin başladığı yerden tekrar
oraya gelene kadar devam etmesi gerektiğini söyledi.

**Kök neden bulundu:** hologramın 5 noktalı M/W silüetinde dış köşeler
(boyun_sol/boyun_sağ) uç noktayla (p1/p2) AYNI zaman damgasını
paylaşıyordu (Faz 1, 1B'nin bilinçli "dikey direk" tasarımı) — bu, üçgenin
bir kenarını DİKEY, diğerini EĞİK bırakıyordu, tam da kullanıcının tarif
ettiği asimetrik görünüm.

**Düzeltme:** `tlab/indicators/patterns/double_top_bottom.py`nin hologram
noktaları artık dış köşeleri p1↔boyun / boyun↔p2 arasındaki (zaten bilinen)
bar mesafesini dışa AYNALAYARAK hesaplıyor — iki kenar da eğik, simetrik
tam üçgen (TradingView referansıyla aynı dil). Bu mesafe yalnızca
p1/neckline_pivot/p2'ye bağlı olduğu için (hepsi born_idx anında zaten
bilinir) repaint riski YOK. `tlab/viz/svg/scenes/double_top_bottom.py`nin
`_pattern_window`ı da hologramın yeni (daha geniş) uzamını HER ZAMAN
kapsayacak şekilde güncellendi (aksi hâlde dış köşe pencere dışında kalıp
`bar_index` KeyError fırlatabilirdi).

Kilitleyen test (`test_hologram_polygon_is_five_point_mw_silhouette`)
yeni geometriye göre güncellendi, golden SVG referansı yeniden üretildi
(`--update-golden`). Gerçek BIST verisiyle (BAKAB, TUCLK) 3 temada yeniden
render edilip GÖRÜLEREK doğrulandı (5. iterasyon, `docs/design/iterasyon/
iter5_*`). 738 test yeşil, ruff/mypy baseline'ları DEĞİŞMEDİ. Galeri
artifact'i güncellendi (aynı URL, `docs/spec/FAZ3_SVG_MOTORU.md`nin
iterasyon tablosuna 5. satır eklendi).

Aynı mesajda kullanıcı iki konu daha sordu: (1) CELHA örneğinde "kırılımdan
2 mum sonra hedef geldiği hâlde retest bekleniyor" izlenimi — gerçek
sinyal zaman çizelgesi kontrol edildi, `track_breakout_pattern` (`tlab/
core/pattern_state.py`) hedef kontrolünü retest'ten ÖNCE yapıyor ve hemen
`break` ediyor (kod zaten doğru), CELHA'nın GÜNCEL verisinde pattern
aslında hedefe hiç ulaşmadan (46 gün sonra retest, 8 gün sonra süresi
dolarak) EXPIRED olmuş — kullanıcının tarif ettiğiyle uyuşmuyor, muhtemelen
daha eski/önbellek bir görünüme bakılmış; kod değişikliği YAPILMADI, yalnızca
açıklandı. (2) "17 çift yetersiz, bir sinyal kaçırırız" endişesi (GARAN/
AKBNK örnek olarak verildi, kullanıcı sonra "spesifik çift değil, genel
endişe" diye netleştirdi) — mimari olarak `config/pairs.yaml`nin "KALICI
BİR ONAY DEĞİL, periyodik yeniden koşulmalı" (docstring'in kendi notu)
olduğu hatırlatıldı; somut öneri (henüz UYGULANMADI, kullanıcı onayı
bekliyor): `pair_denetim.py`nin zamanlanmış/periyodik çalıştırılması
(ör. aylık cron/Windows Görev Zamanlayıcı) — whole-universe CANLI tarama
DEĞİL (Faz 2'de 116-çift deneyiyle zaten test edilip reddedildi), yeni
cointegre olan bir çiftin listeye düzenli aralıklarla eklenmesini sağlayan
bir OPERASYONEL çözüm.

## 2026-09-04 (aynı gün) — Web: "Çift Listesini Yenile" butonu + kapsamlı INTEM taraması

Kullanıcı zamanlanmış cron yerine web arayüzünde, her arbitraj taramasından
ÖNCE elle basabileceği bir buton istedi. `scripts/pair_denetim.py`nin
`discover_pairs` + `config/pairs.yaml` yazma mantığı (`_write_pairs_yaml`,
`_load_all_close_prices`) YENİ `tlab/indicators/pairs/refresh.py`ye
taşındı (`write_pairs_yaml`/`load_all_close_prices`/`refresh_pairs_yaml`) —
CLI betiği artık bu paylaşılan modülü import ediyor, mantık iki yerde ayrı
yazılmıyor. YENİ `web/backend/routes/pairs_refresh.py` (`POST /api/pairs/
refresh`, `GET /api/pairs/refresh/status`) `scan_trigger.py`nin AYNI
thread+iş-durum deseniyle arka planda `refresh_pairs_yaml()`i çalıştırır.
Frontend'de (`web/frontend/app/scan/page.tsx`) kategori "pair" seçiliyken
görünen "Çift Listesini Yenile" butonu eklendi (5sn polling, `scan/page.tsx`
zaten kullandığı `startScan`/`fetchScanStatus` desenini paylaşıyor).
3 yeni test (`tests/test_pairs/test_refresh.py`, `write_pairs_yaml`in saf
yazma/round-trip davranışı), TypeScript `tsc --noEmit` temiz, endpoint
`TestClient` ile uçtan uca duman testiyle doğrulandı (arka plan iş kuyruğa
alınıp `running`e geçti — tam bir keşif koşusu dakikalarca sürdüğü için
GERÇEK bir tamamlanma beklenmedi, `config/pairs.yaml`nin dokunulmadığı
`git status` ile doğrulandı). 741 test yeşil, ruff/mypy baseline'ları
DEĞİŞMEDİ.

**Ayrıca aynı oturumda** kullanıcının canlı bir INTEM (BIST) pozisyonu için
altı göstergeyle (harmonik, yapı raporu, swing/fibonacci, golden zone,
arz-talep, çift dip) tam bir tarama istendi ve bir artifact galerisi olarak
sunuldu (kalıcı kod değişikliği YOK, tek seferlik analiz). Kullanıcının
kendi TradingView'da işaretlediği Bat XABCD noktaları (X=31 Tem düşük,
A=13 Ağu yüksek, B=20 Ağu düşük, C=24 Ağu yüksek) Carney'nin Bat kuralıyla
elle hesaplandı — oranlar geçerli (XAB=0,482, ABC=0,868) ve D bölgesi
(237,96-240,08) fiyatın aynı sabah dokunduğu (239,70) seviyeyle TAM
örtüştü; sistemin otomatik taraması bunu C pivotunun (24 Ağustos zirvesi)
kendi zigzag mantığında henüz "kesinleşmemiş" olması yüzünden henüz aday
olarak üretmemişti (birkaç bar gecikme, geçersizlik DEĞİL). Bu, kod
tabanında kalıcı bir değişiklik gerektirmedi — bulgu kullanıcıya doğrudan
sunuldu.

## 2026-09-04 (aynı gün) — Adım 6 / Faz 4a başladı: `harmonic` sahnesi portlandı

Kullanıcı Faz 4'e (kalan 18 sahnenin portu) devam kararı verdi. Roadmap'in
kendi notu ("Bu fazı 3 oturuma böl — tek oturumda bağlam şişer") uyarınca
bu oturumda 4a grubunun (harmonic/report/swingfib/goldensupply/weekly/
reversal_map) TAMAMI değil, en yüksek sürekliliğe sahip TEK sahne
(`harmonic` — aynı oturumda INTEM'in Bat analiziyle doğrudan bağlantılı)
tam titizlikle portlandı; kalan 5 sahne sıradaki oturum(lar)a bırakıldı.

**`tlab/viz/svg/scenes/harmonic.py`** — `HarmonicIndicator`'ın 8 ekolünün
(carney/pesavento/gilmore/cypher/nenstar/navarro200/five_zero/three_drives)
TAMAMI için TEK, ekol-agnostik sahne. `scanner_indicator.py::compute()`nin
her adayı TEK bir döngüde işleyip `polygons`/`levels`/`markers`e HER ZAMAN
sabit sayıda öğe eklediği (2 polygon, 2 level [prz_low/high], 1 marker)
gerçeğine dayanan POZİSYONEL eşleştirme ile marker (yalnızca `harmonic_
{state}` taşır, pattern_id İÇERMEZ) doğru adaya bağlanıyor.

**4 iterasyon, gerçek veriyle (BAKAB confirmed, TUCLK pending — İKİ farklı
durum dalı da GERÇEK sinyalle test edildi), 3 temada GÖRÜLEREK:**
1. Baseline çalıştı ama D rozeti (pill) PRZ etiketiyle üst üste bindi —
   PRZ dar bir fiyat bandı olduğu için D genelde TAM içine dokunuyor,
   ikisi de elle konumlanmıştı.
2. Rozet + PRZ etiketi `resolve_collisions`e taşındı — kenar taşması
   düzeldi ama bu kez D'nin küçük harf etiketi ("D") ile büyük rozet AYNI
   "D noktasının hemen altı" bölgesini paylaşıp üst üste bindi.
3. D'nin küçük etiketi "above" yönüne çevrildi (rozet "below" kalıyor) —
   kısmen düzeldi ama PRZ etiketiyle D etiketi bu kez BAŞKA bir noktada
   çakıştı (ikisi de bağımsız elle konumlanmıştı, koordine değillerdi).
4. KÖKTEN çözüm: X/A/B/C/D'nin BEŞİ de (yalnızca D değil) PRZ etiketi ve
   rozetle AYNI `resolve_collisions` havuzuna alındı — artık hiçbir
   değişken-konumlu öğe elle yerleştirilmiyor (Faz 3'ün double_top_bottom
   sahnesiyle AYNI ilke). Bu, 5. iterasyonda (yalnızca ruff/mypy
   satır-sarma, davranış DEĞİŞMEDİ, görsel olarak doğrulandı) son hâlini aldı.

8 yeni test (`tests/test_viz/test_svg/test_harmonic_scene.py` — CONFIRMED
ve ACTIVE/pending dallarının İKİSİ de gerçek `build_gartley_ohlcv`
fixture'ının seri KESİLEREK türetilmiş hâliyle test ediliyor) + 1 yeni
golden test. `tests/test_viz/test_svg/test_double_top_bottom_scene.py`nin
`supports("harmonic.carney") is False` / unported-indicator testleri artık
YANLIŞ varsayım taşıdığı için güncellendi (harmonic ARTIK portlandı --
unported testi `structure.golden_zone`ye çevrildi). `tlab/viz/svg/prim.py`ye
YENİ `outline_pill()` eklendi (artifact'in `outlinePill`i, "AKTİF" rozeti
için). 750 test yeşil (741→750), ruff/mypy baseline'ları DEĞİŞMEDİ.

**Sırada:** Faz 4a'nın kalan 5 sahnesi (report/swingfib/goldensupply/
weekly/reversal_map) — ayrı oturum(lar)da.

## 2026-09-04 (aynı gün) — Web: "Paylaşım Metni" — çoklu-gösterge X paylaşım metni üreticisi

Kullanıcı, dashboard'daki mevcut "Yapay Zeka Raporu" butonundan (BİR
göstergenin ZATEN açık olduğu grafiğe bağlı) BİLİNÇLİ OLARAK AYRI bir akış
istedi: yalnızca bir sembol adı yazıp, sistemin O AN o sembol için ürettiği
ÇOKLU-gösterge (yapı raporu 1D+4H, harmonik-Carney/golden zone/arz-talep/
çift tepe-dip 4H) taramasından X'te paylaşılabilir TEK bir metin üretmesini
istedi — bu, aynı oturumda INTEM için ELLE yapılan analiz+paylaşım metni
iş akışının ÜRÜNLEŞTİRİLMESİ. Sağlayıcı Gemini (kullanıcı onayı), ses
"yapay zeka değil bir insan/quant tarafından yazılmış gibi ama anlaşılır" —
`quant_report.py`nin defalarca elle ayarlanmış anti-yapay-zeka-sesi
`_SYSTEM_PROMPT`ı ve LLM çağrı çekirdeği (`_generate_from_facts`) BURADA
YENİDEN YAZILMADI, dosya sonunda `generate_from_facts`/`SYSTEM_PROMPT`
adlarıyla dışa açılıp AYNEN paylaşıldı.

**Yeni dosyalar:** `tlab/viz/share_text.py` (`build_share_facts()` — her
göstergenin OLGU listesini `report_text.py`nin ZATEN var olan
`build_summary_lines`/`build_generic_summary_lines`inden toplar, bir
gösterge aday/veri üretmezse o bölüm SESSİZCE atlanır; `generate_share_text()`
— birleşik olguları `generate_from_facts`e iletir), `web/backend/routes/
share_text.py` (`GET /api/share-text?symbol=...&market=...`, `report.py`
ile AYNI `_ensure_gemini_key()` bootstrap deseni — bilanco-radar'ın `.env`'i),
`web/frontend/app/share/page.tsx` (sembol girişi + "Paylaşım Metni Oluştur"
butonu + kopyala düğmesi, `AiReportPanel`in stilini paylaşır), Sidebar'a
"Paylaşım Metni" linki eklendi.

6 yeni test (`tests/test_viz/test_share_text.py` — `compute_structure_report`/
`compute_live`/`generate_from_facts` MOCK'lanır, ağ çağrısı YOK; olgu
birleştirme + göstergenin ValueError/FileNotFoundError/`df=None` durumunda
sessizce atlanması + `generate_share_text`in birleşik listeyi AYNEN LLM
çekirdeğine ilettiği doğrulandı). 756 test yeşil (750→756), ruff/mypy/
lint_lookahead baseline'ları DEĞİŞMEDİ. Frontend: `npx eslint`/`tsc --noEmit`/
`next build` üçü de temiz, `/share` rotası derlendi.

Gerçek Gemini çağrısı `TestClient` ile uçtan uca (INTEM, gerçek bilanco-radar
anahtarıyla) iki kez denendi — ikisinde de `503 UNAVAILABLE` ("high demand",
geçici bir Gemini-taraflı kesinti) alındı, bu da doğru şekilde deterministik
fallback'e (`used_ai=False`, açık bir `note`) düştü. Anahtar bulma +
fallback yolu böylece uçtan uca doğrulandı; **kullanıcı arayüzden "Oluştur"a
basınca `Not Found` hatası aldı** (aşağıdaki bölüme bak) — bu düzeltildikten
sonra hem `/api/share-text` hem `/api/report` gerçek bir Gemini yanıtıyla
(`used_ai=True`) BAŞARIYLA doğrulandı (THYAO 4H harmonic.carney).

## 2026-09-04 (aynı gün) — Faz 4a devam: `report` sahnesi portlandı (2/6)

`tlab/viz/svg/scenes/report.py` — `structure.report`in (price_structure +
swing_fib_abcd birleşimi) SVG portu, artifact'in `sceneReport`ine (satır
~492-568) referansla: ana panel (mumlar + tek DİRENÇ trend çizgisi [solid +
sağa dashed projeksiyon] + tek DESTEK BÖLGESİ kutusu + VAH/POC/VAL seviyeleri
+ son birkaç HH/HL/LH/LL swing etiketi), sağda DİKEY hacim profili paneli
(HVN barları farklı renkte + Gauss eğrisi), altta RSI(14) paneli. `SceneOut.
side` alanı Faz 3'te tanımlanmış ama HİÇ kullanılmıyordu — `svg/__init__.py::
_wrap_svg`'e side-panel yerleşimi (sol yığının SAĞINA, üstten hizalı) bu
sahnede EKLENDİ.

**Mimari:** `structure.report` gerçek bir CATALOG göstergesi değil, iki ayrı
sonucun birleşimi (bkz. Faz 7 notları) — bu birleştirme daha önce YALNIZCA
`web/backend/routes/chart.py`de vardı, buraya (`tlab/viz/live.py::
compute_structure_report_merged`) TAŞINDI ve `chart.py` da bunu ÇAĞIRIR hâle
getirildi (TEK doğru kaynak — DRY, davranış DEĞİŞMEDİ). `render_live`nin
`STRUCTURE_REPORT_NAME` dalı artık `engine="svg"` + `svg_supports(...)` iken
bu birleşik sonucu `render_svg`e verir, aksi hâlde eskisi gibi Plotly'e düşer.

**THYAO 1D/4H gerçek verisiyle 5 iterasyon, 3 temada GÖRÜLEREK — 3 GERÇEK
hata bulunup düzeltildi:**
1. İlk denemede hiçbir direnç çizgisi HİÇ görünmüyordu — `_latest_line`
   yalnızca pencere İÇİNDE son temas edilmiş çizgileri kabul ediyordu, ama
   `extend_right=True` olan kırılmamış trend çizgileri genelde ESKİ (pencere
   dışı) bir son temasa sahip (bugüne kadar PROJEKTE edilerek uzanıyorlar).
2. Bu düzeltilince (en çok temas edilen kırılmamış çizgiyi seç) çizgi YİNE
   görünmüyordu — seçilen çizgi 4 barlık kısa/dik bir bacaktan geliyordu,
   kendi eğimiyle ~450 bar sonrasına (bugüne) projekte edilince fiyat 563
   TL gibi ekran dışı bir değere savruluyordu (renderer.py'nin Faz 7'de
   bulduğu AYNI "sınırsız eğim" sorunu, farklı bir kaynaktan GERİ GELMİŞ).
   Düzeltme: `renderer.py::Line`nin AYNI 3x-bacak-süresi kuralı burada da
   uygulandı (`_PROJECTION_CAP=3`) — hem ADAY SEÇİMİNDE (yalnızca projeksi-
   yonu pencereye ULAŞABİLEN çizgiler aday sayılır) hem ÇİZİMDE (dashed
   segment 3x'te KESİLİR, panelin sağ kenarına değil).
3. "Destek Bölgesi" kutusu neredeyse GÖRÜNMEZ (sıfır yükseklikli) çiziliyordu
   — kök neden `_zones()`'ün KENDİ sözleşmesiydi: `t1`, kırılmamış bir
   bölge için df'in SON barına eşit, ama `_track_zones()` kırılma taramasını
   `formed_idx`in KENDİSİNDEN (aynı bardan) başlatıyor — THYAO'da denenen
   TÜM 8 bölge aynı barda "kırılmış" çıktı (t0==t1). Bu `_zones()`'ün
   kendisinde bir hata OLABİLİR (ayrı bir takip konusu, kapsam dışı
   bırakıldı) ama MY sahne kodu bunu hiç KONTROL ETMİYORDU — `_active_box`
   artık yalnızca `t1 >= pencerenin son barı` (hâlâ aktif) olan bölgeleri
   kabul ediyor. **NOT: 10 büyük BIST sembolünde (AKBNK/GARAN/ASELS/SISE/
   KCHOL/TUPRS/BIMAS/EREGL/FROTO/ENKAI) taranıp HİÇBİRİNDE aktif bir bölge
   bulunamadı** — `zone_breakout_confirm=1` varsayılanıyla bölgelerin
   PRATİKTE neredeyse hiç "aktif" kalmıyor olması muhtemel, `_zones()`'ün
   kendisi ayrıca incelenmeli (kod DEĞİŞTİRİLMEDİ, yalnızca gözlemlendi).
4. (Küçük, 4. iterasyonda) 4H'te x-ekseni 5 eşit-aralıklı tik aynı ayı
   ("Tem '26") iki kez üretiyordu — `_pick_x_ticks` artık ardışık AYNI
   metni atlıyor.

10 yeni test (`tests/test_viz/test_svg/test_report_scene.py` — yukarıdaki
2. ve 3. bulguları sentetik `Line`/`Box` fixture'larıyla kilitleyen 4 hedefli
regresyon testi dahil) + 1 yeni golden test. 770 test yeşil (759→770), ruff/
mypy/lint_lookahead baseline'ları DEĞİŞMEDİ. Detay: `docs/design/iterasyon/
iter{1..5}_report_THYAO_*`.

**Sırada:** Faz 4a'nın kalan 4 sahnesi (swingfib/goldensupply/weekly/
reversal_map).

## 2026-09-04 (aynı gün) — GERÇEK HATA: `IndicatorResult.timeframe` HER indikatörde sabit "D1"

Kullanıcı "Paylaşım Metni Oluştur"a basınca **404 Not Found** aldı — kök
neden, `web/backend/main.py`'ye `share_text` router'ı önceki oturumda
eklendiği ANDA çalışan `uvicorn --reload` süreci onu hiç YÜKLEMEMİŞTİ
(WatchFiles bu oturumda İKİ KEZ dosya değişikliğini "algılayıp" reload
başlattığını LOGLADI ama yeni bir worker süreci HİÇ SPAWN ETMEDİ — `netstat`
eski PID'i LISTENING gösterirken `tasklist` o PID'in artık var OLMADIĞINI
gösterdi, güvenilmez bir Windows/WatchFiles etkileşimi). Düzeltme: eski
süreç ağacı elle `taskkill`lendi, backend TEMİZ yeniden başlatıldı —
kod tarafında değişiklik GEREKMEDİ, yalnızca dev-server hijyeni.

**Bu teşhis sırasında AYRI, çok daha geniş kapsamlı GERÇEK bir hata
bulundu:** `IndicatorResult` üreten 18 dosyanın TAMAMI (istisnasız —
`harmonic.*`, `structure.golden_zone/supply_demand/price_structure/
swing_fib_abcd`, `patterns.*` [wedge/broadening/double_top_bottom/
flag_pennant/head_shoulders], `trend.*` [breakouts/ewmac/ma_systems/
weekly_channel], `momentum.*` [alpha_rank/momentum_rank], `pair.*`
[relative_momentum/vol_harvest]) kendi `compute()`'unda `timeframe=
Timeframe.D1`'i SABİT yazıyordu — çünkü `BaseParams`/`for_timeframe()`
yalnızca `_BAR_FIELDS`'i ölçekler, tf'nin KENDİSİNİ hiçbir params alanında
SAKLAMAZ; indikatörün kendisi hangi tf'de çalıştığını asla BİLEMEZ.

**Etki, ilk göründüğünden BÜYÜKTÜ** — yalnızca `report_text.py`'nin "Zaman
Dilimi: ..." metnini değil, `renderer.py::_rangebreaks_for`'un GECE/hafta-
sonu boşluğu gizleme mantığını da (yalnızca `Timeframe.H1`/`H4` iken
devreye girer) SESSİZCE devre dışı bırakıyordu — yani TÜM 1H/4H
grafiklerde mum gövdeleri, 2026-08-30'da BİR KEZ bulunup düzeltilen o
sorunun ta kendisiyle, gerçekte olduğundan daha sıkışık görünüyordu
(farklı bir kaynaktan geri gelmiş hâli — o düzeltme `_rangebreaks_for`'un
KENDİSİNDEydi, ama besleyen `result.timeframe` hiç DOĞRU olmamış).

**Düzeltme** (`tlab/viz/live.py`) — 18 dosyayı TEK TEK değiştirmek yerine
(mekanik ama riskli, `BaseParams`/`params_hash`'e dokunmayı gerektirirdi),
`result.symbol = symbol`'la AYNI ZATEN VAR OLAN desen kullanıldı: compute()
kendi tf'sini bilemediği için, onu BİLEN TEK çağıran nokta (`compute_live`/
`compute_structure_report`) sonradan atıyor. 5 atama noktası: `compute_live`
içinde pair/universe/tekil üç dal + `compute_structure_report`'un ps/sf
sonuçları. Bu TEK nokta hem `report.py` (mevcut "Yapay Zeka Raporu") hem
YENİ `share_text.py` hem `render_live`→`renderer.py` (rangebreaks) hem
`chart.py`/`chart_png.py`/`chart_svg.py`'yi KAPSAR — tarayıcı/DB tarafı
(`scanner/engine.py`) ETKİLENMEDİ, çünkü o zaten kendi `timeframe_value`'sunu
`result.timeframe`'den BAĞIMSIZ, döngünün kendi değişkeninden yazıyordu.

Doğrulama: 756 test hâlâ yeşil, ruff/mypy baseline'ları DEĞİŞMEDİ; canlı
sunucuda THYAO 4H `/api/share-text` çıktısı "Zaman Dilimi: 1D" → "4H"
olarak düzeldi, `/api/chart.png` THYAO 4H'te hatasız render etti (rangebreaks
regresyonu yok).

## 2026-09-04 (aynı gün) — Faz 4a devam: `swing_fib_abcd` sahnesi portlandı (3/6)

Kullanıcı iki oturum önce Faz 4a'nın kalan 5 sahnesini onayladı ("harmonic"
ve "report" önceki oturumlarda bitmişti); bu oturum önce `docs/SONNET_
PROMPTLARI.md`, gerçek vitrin kaynağı (`grafik_stil_vitrini_files/saved_
resource.html` — ANA `grafik_stil_vitrini.html` yalnızca Claude.ai Artifacts
görüntüleyicisinin dış çerçevesi, gerçek sahne kodu BU alt dosyada, bkz.
Faz 3 girdisi), `report.py`/`harmonic.py` (port deseni referansı) ve 5
hedef indikatörün (`swing_fib_abcd`/`golden_zone`/`supply_demand`/
`weekly_channel`/`confluence::build_reversal_map`) TAM kaynağı okunarak
hazırlık yapıldı — kod YAZILMADI, yalnızca okuma (kullanıcının "hazırda
bekle" isteği üzerine, session limiti yenilenene kadar).

**`tlab/viz/svg/scenes/swing_fib_abcd.py`** — `structure.swing_fib_abcd`
sahnesi: mum + swing zigzag zinciri + HH/HL/LH/LL etiketleri (report.py'nin
AYNI `resolve_collisions` deseni, ayrı ayrı yazıldı — sahneler birbirini
import etmez) + EN GÜNCEL üçlünün AB=CD D-hedef seviyeleri (yatay çizgi,
bullish=yeşil/bearish=kırmızı) + EN YENİ bacağın Fibonacci retracement/
uzatım merdiveni (0.618/0.786 altın vurgu).

**Referans: `sceneSwingFib`** (saved_resource.html satır 643-677).
BİLİNÇLİ sapma: artifact'in D-hedefi UYDURMA bir eğik ("A-B eğimiyle
projekte edilmiş") çizgiydi — gerçek `Level` YATAY bir fiyat seviyesidir
(`price`, `start`=C barı, `end`=None [açık] veya tamamlanma/geçersizleşme
barı), `report.py`nin VAH/POC/VAL desenine daha yakın çizildi.

**1. iterasyonda (THYAO 1D classic) GERÇEK bir hata bulundu:** D-hedef
fiyatları (3 farklı oran — 1.0/1.272/1.618) y-ekseni `pad_range`
hesabına dahil edilince en agresif oran (1.618, ~244 TL, güncel fiyatın
~%20 altı) ekranın "doğal" mum aralığının çok dışına düşüp TÜM mumları
ekranın küçük bir üst şeridine sıkıştırıyordu (350-250 TL'lik doğal
aralık 360-230'a genişleyip grafiğin alt üçte biri boş kalıyordu).
**Düzeltme:** D-hedef fiyatları y-ekseni hesabından ÇIKARILDI; yalnızca
ekranın doğal aralığına (mum+swing+fib merdiveni) düşen hedefler çizilir,
range dışına düşenler SESSİZCE atlanır (`test_out_of_range_target_is_
silently_skipped` bunu kilitler). 2. iterasyonda (THYAO 1D classic)
düzeltme doğrulandı — en agresif hedef ekrandan kayboldu, mumlar doğal
aralığına döndü, kalan 2 hedef (LL swing'in hemen altında, semantik
olarak doğru bir "potansiyel destek" konumunda) okunaklı kaldı. 3.
iterasyonda (THYAO 1D dark + BAKAB 1D editorial) YENİ bir hata
bulunmadı — dark temada iyi kontrast, editorial'da D-hedefleri doğal
şekilde range dışına düşüp sessizce gizlendi (fib merdiveni tek başına
okunaklı kaldı).

9 yeni test (`tests/test_viz/test_svg/test_swing_fib_abcd_scene.py` —
`_latest_targets`/`_fib_ladder`'ın gruplama mantığı + yukarıdaki GERÇEK
hatayı kilitleyen sentetik `Level` regresyonu + 3 temada well-formed SVG
dahil), 779 test yeşil (770→779), ruff/mypy/lint_lookahead baseline'ları
DEĞİŞMEDİ. Detay: `docs/design/iterasyon/iter{1..3}_swing_fib_abcd_*`.

**Sırada:** Faz 4a'nın kalan 3 sahnesi (goldensupply/weekly/
reversal_map). Not: `live.py::render_live`'ın kendi docstring'i
(2026-08-30 "deneme + geri alma" notu) `structure.golden_zone`/
`structure.supply_demand`'ın BİLİNÇLİ olarak AYRI, birleştirilmemiş
grafikler olarak kalmaya devam ettiğini söylüyor — bu yüzden "goldensupply"
tek bir birleşik sahne DEĞİL, `report.py` gibi bir "merge" YAPILMADAN iki
AYRI sahne dosyası (`structure.golden_zone`/`structure.supply_demand`)
olarak portlanacak (vitrinin `sceneGoldenSupply`'ı iki farklı sembolü yan
yana gösteren bir DEMO, gerçek port için mimari referans değil). `reversal_
map` için de: `confluence.py::build_reversal_map` CATALOG göstergesi değil,
çoklu-kaynak post-processing fonksiyonu — sahne öncesi `live.py`ye
`compute_reversal_map` benzeri bir köprü eklenmesi gerekecek.

## 2026-09-04 (aynı gün) — Faz 4a devam: `golden_zone` + `supply_demand` sahneleri portlandı (4/6, 5/6)

Önceki girdide not edildiği gibi vitrinin `sceneGoldenSupply`si iki farklı
sembolü yan yana gösteren bir DEMO'ydu — gerçek port `structure.golden_zone`
ve `structure.supply_demand` için İKİ AYRI sahne dosyası olarak yapıldı
(`live.py::render_structure_report_live`'ın 2026-08-30 "geri alma" kararı
gereği).

**`tlab/viz/svg/scenes/golden_zone.py`** — mum + EN GÜNCEL swing'in altın
bölge (0.618–0.786) + alt bant (0.5–0.618) + 0.5 fib çizgisi + REAKSİYON/
BAŞARILI/BAŞARISIZ işaretleri. 1. iterasyonda (THYAO) GERÇEK bir hata
bulundu: `Marker` kendi `swing_id`sini taşımaz, yalnızca ZAMAN aralığına
göre filtrelemek eski/çakışan bir swing'in işaretini de aktif bölgeye
karıştırıyordu — düzeltme: en büyük `swing_id`ye sahip sinyallerin
bar_time'larına göre eşleştirme. 4. iterasyonda (THYAO dark) İKİNCİ bir
hata bulundu: "ALTIN BÖLGE" etiketi ile bölge dışına taşan bir marker
etiketi (downtrend'de "BAŞARISIZ" bölgenin üst kenarını kırar) üst üste
biniyordu — düzeltme: bölge etiketi artık kutunun İÇİNE konuyor, marker
etiketleri fiyatın kutuya göre konumuna göre yön değiştiriyor. 5 iterasyon
(THYAO classic/dark, BAKAB editorial), 8 yeni test.

**`tlab/viz/svg/scenes/supply_demand.py`** — mum + en yakın (indikatörün
KENDİ `last_state["nearest_demand"/"nearest_supply"]` seçimi, ATR-normalize)
açık arz/talep bölgesi + en fazla 2 yakın zamanda kırılmış bölge (kesikli
çerçeve, referans için) + REAKSİYON/KIRILDI işaretleri. 1. iterasyonda
(THYAO) ÜÇ gerçek sorun bulundu: (1) bölge fiyatları y-ekseni hesabına
dahil edilince mumlar sıkışıyordu — swing_fib_abcd'nin AYNI dersi
uygulandı (eksen yalnızca mum aralığından, bölge ekranın doğal aralığına
düşmüyorsa çizilmez); (2) sağ kenara çok yakın doğan bir bölgenin etiketi
panel dışına taşıp kırpılıyordu ("ARZ BÖLGESİ..." yalnızca "A" olarak
görünüyordu) — etiket artık yetersiz alanda sağa hizalanıyor; (3) hangi
bölgeye ait olduğu belirsiz "yetim" işaretler (y-ekseni dışına düşüp hiç
çizilmemiş bir bölgeye ait) görünüyordu — artık yalnızca ÇİZİLEN
bölgelerin zaman aralığına düşen işaretler gösteriliyor. Ayrı bir tasarım
gerginliği de fark edildi ve çözüldü: THYAO'nun tek açık talep bölgesi
güncel fiyattan 3.1 ATR uzaktaydı, TÜM açık bölgeleri çizmek yerine
yalnızca indikatörün kendi "en yakın" seçimi çizilerek golden_zone/
report'un "tek odak" ilkesiyle hizalandı (bu belirli THYAO örneğinde tek
aday zaten oydu, eksen geniş kalması GERÇEK veri — 150 barlık pencerede
tek bir derin dip barı var — düzeltilecek bir hata değil, kabul edildi).
3 iterasyon (THYAO classic/dark, BAKAB editorial — BAKAB'da hiç açık
bölge yoktu, sahne zarifçe yalnızca mumları gösterdi), 9 yeni test.

**Yan bulgu:** `test_double_top_bottom_scene.py`'nin iki testi (`supports`/
`render_svg raises`) "henüz portlanmamış indikatör" örneği olarak
`structure.golden_zone`'u kullanıyordu — bu artık YANLIŞ (portlandı),
`trend.weekly_channel`e güncellendi (bu YENİ örneğin de bir sonraki
oturumda aynı şekilde bayatlayacağı, o zaman tekrar güncelleneceği not
edildi — HER Faz 4a sahnesi eklendiğinde bu deseni hatırla).

Toplam 17 yeni test (8+9), 796 test yeşil (779→796 — ruff/mypy/lint_
lookahead baseline'ları DEĞİŞMEDİ. Detay: `docs/design/iterasyon/
iter{1..5}_golden_zone_*`, `iter{1..3}_supply_demand_*`.

**Sırada:** Faz 4a'nın kalan 2 sahnesi (weekly/reversal_map).

