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
- **OTURUM DURDU BURADA (2026-08-28) — kullanıcı isteğiyle.** Kullanıcı declutter
  düzeltmesinden sonra "kalanlara daha sonra devam ederiz" dedi — Faz 8B/8C/8D/8E ve
  K3'e HENÜZ BAŞLANMADI, kod/tasarım kararı yok. Yeni oturumda kaldığımız yer:
  **Sırada**: Faz 8B (formasyonlar — çift tepe/dip, broadening, TWYS ekleri; Faz 2-EK'in
  `patterns_geom.py`/`hs_pattern.py`'sine ihtiyaç duyar, henüz yazılmadı), Faz 8C
  (bölgeler — golden zone/S-D/kanal; `zones_sd.py`ye ihtiyaç duyar), Faz 8D
  (cross-sectional — KAMA/EWMAC, Carver'ın ilk kuralı; `xsec.py`ye ihtiyaç duyar), Faz 8E
  (vol harvest — GARCH), K3 (Carver kitap çıkarımı, Faz 10 spec'i için ön koşul).
  Hangisiyle devam edileceğine kullanıcı karar verecek — 648-sembol/tüm-çift tam evren
  taraması da hâlâ "Sıradaki Adımlar" bölümünde bekliyor.

Toplam 206 test yeşil (`pytest -q`, varsayılan olarak `-m "not network"` uygular),
ruff/mypy/lint_lookahead temiz.

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

Önerilen sıra: 1 → 2 (tlab içinde, tek fazda yapılabilir), 3 ayrı bir bilanco-radar
konuşması. Faz 3'ü (harmonik) bloklamaz.

## Gelecek Entegrasyonlar (henüz tasarlanmadı, sadece hedef notu)

- **TradingView masaüstü bağlantısı**: Kullanıcı bunu ayrıca kendi planlayacak (tv_health_check benzeri bir yaklaşım). Bu dosyada detay yok, tasarım kararları kullanıcıdan gelecek.
- **Fintables bağlantısı**: Ham temel veri + hazır analiz çekimi için ileride entegre edilecek. Detay/tasarım henüz yok.
- **Bilanço Radar ile birleşme**: Bu projenin çıktıları (sinyaller, taramalar) ile Bilanço Radar'daki `dashboard.html` temel analiz katmanı tek bir app'te buluşacak. Doğruluğu teyit edilmiş veriler iki proje arasında paylaşılabilir.

## Arayüz Kararı

Henüz verilmedi (Streamlit/masaüstü mü, web/HTML mi). Bilanço Radar ile ileride birleşeceği için bu karar ertelendi — indikatör/tarama motoru arayüzden bağımsız tasarlanmalı ki hangi arayüz seçilirse seçilsin çekirdek mantık değişmesin.
