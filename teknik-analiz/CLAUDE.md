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

**Tam faz-faz oturum notları (her fazın gerekçesi, bulunan gerçek hatalar, tasarım
kararları) artık `docs/PROGRESS_LOG.md`'de** — bu dosya CLAUDE.md'nin 150k karakter
sınırını aştığı için oraya taşındı (2026-09-02). Aşağıdaki liste yalnızca ÖZET; bir
fazın TAM detayına ihtiyaç varsa `docs/PROGRESS_LOG.md`'ye bak.

**Durum (2026-09-04): 619 test yeşil (`pytest -q -m "not network"`), ruff/mypy/
lint_lookahead temiz (baseline: 19 ruff / 1 mypy / 3 lint_lookahead — hepsi önceden
var olan/bilinen false-positive, ilgisiz satırlar). Faz 0-10 + K0-K3 (aşağıdaki liste)
TAMAMLANDI; proje artık YENİ, daha büyük bir denetim/yol haritası altında ilerliyor —
bkz. `docs/TANI_VE_YOL_HARITASI_v2.md` (tanı + Faz 0-8 promptları), `docs/
STRATEJI_DENETIM_TAM.md` (24 göstergenin tam denetimi), `docs/SITE_TASARIM_YOL_
HARITASI.md` (S1-S8 arayüz promptları), sıra `docs/00_BASLANGIC_SIRASI.md`'de
(16 adım). **Adım 1 / (yeni) Faz 0 TAMAMLANDI** (sinyal tazeliği — `bars_ago` +
`/scan` tazelik filtresi; `.claude/skills/grafik-tasarim-sistemi` + `.claude/
agents/grafik-tasarimcisi.md`; `tests/test_viz/test_golden.py` golden testi).
**Adım 2 / (yeni) Faz 0.5 TAMAMLANDI** (A1 ortak pivot girişi `significant_
pivots` + A2 zaman dilimi ölçekleme `for_timeframe`/`scaled_factory` + A3
`supported_timeframes` kapısı + A4 hacim onayı parametresi + D ölçüm/rapor —
120 gerçek BIST sembolüyle ölçüldü, `docs/spec/SISTEMIK_DENETIM_v1.md`; ölçüm
sırasında GERÇEK bir regresyon bulunup düzeltildi: wedge/triangle/broadening'de
ATR-seyrek pivotlar trendline aday havuzunu bozuyordu, `zigzag_method`
varsayılanı bu 3 gösterge + `price_structure`'ın trendline tarafı için
"fixed"e geri çevrildi) — detay `docs/PROGRESS_LOG.md`'nin 2026-09-03 ve
2026-09-03/04 girdilerinde. Adım 3 (Faz 1 — klasik formasyon motoru v2) onay
bekliyor.**

### Tamamlanan fazlar (özet)

- **Faz 0 — İskelet**: `core/types.py`, `core/indicator.py`, `core/params.py`,
  `testing/repaint.py`, `testing/lint_lookahead.py`.
- **Faz 1 — Veri katmanı**: `data/providers/`, `data/calendar.py` (BIST 4H hizalama),
  `data/resample.py`, `data/store.py` (parquet cache), `data/validate.py`.
  `config/universe_bist.txt`: 648 sembol.
- **Faz 2 — Özellik katmanı** (`tlab/features/`): swings, fibonacci, trendlines,
  ranges, zones, volume_profile, stats, ma, oscillators, volatility.
- **Faz 3 — Harmonik formasyon motoru**: 8 ekol, ortak geometri/PRZ/durum makinesi.
  Detay: aşağıdaki "Harmonik Formasyon Tarayıcı" bölümü.
- **K0/K1/K1-D/EK-A — Bilgi işleme + Pesavento (TWYS) çıkarımı**: `bilanco-radar`
  reposundaki bilgi-bankası + `pesavento.py`/`three_drives.py`'nin TWYS ile hizalanması.
- **K2 — 11 bölümlük strateji külliyatı incelemesi**: 38 STRAT-xx, 28 DISIPLIN-xx
  kataloglandı (`bilgi-bankasi/teknik/kod/`).
- **Faz 4 — Yapı indikatörleri**: `SwingFibABCD`, `PriceStructure`. Detay: aşağıdaki
  "Yapı İndikatörleri" bölümü.
- **Faz 5 — Pair relatif momentum**: `RelativeMomentumPair`, `discover_pairs`. Detay:
  aşağıdaki "Pair Trading" bölümü. Pencere varsayılanı `window=60` (gerçek veri
  taramasıyla seçildi — bkz. PROGRESS_LOG "Pair strateji varsayılan pencere").
- **Faz 6 — Tarama motoru**: `tlab/scanner/` (results.py/engine.py/eod.py),
  `bootstrap.py::CATALOG`. Detay: aşağıdaki "Tarama Motoru" bölümü.
- **Faz 7 — Görselleştirme + EOD HTML raporu**: `tlab/viz/`. Detay: aşağıdaki
  "Görselleştirme" bölümü. Birkaç ayrı düzeltme turu geçirdi (declutter, "aracı
  kurum raporu" tasarımı → sonra SADELEŞTİRİLDİ, harmonik tek-aday filtresi,
  panel çerçeveleri) — tam gerekçe PROGRESS_LOG'da.
- **Faz 8A — Çoklu kırılım tarayıcısı**: `trend/breakouts.py::MultiBreakout`.
  Detay: aşağıdaki "Çoklu Kırılım Tarayıcısı" bölümü. **Galeriden çıkarıldı**
  (2026-08-30, görsel olarak okunaksız kaldı — "düzeltemiyorsak kaldıralım").
- **Faz 8B — Klasik grafik formasyonları** (`tlab/indicators/patterns/`): wedge/
  triangle, head_shoulders, flag_pennant, double_top_bottom, broadening. Ortak
  durum makinesi `tlab/core/pattern_state.py::track_breakout_pattern`. Görsel
  filtre: yalnızca confirmed/completed pattern çizilir (`_filter_confirmed_patterns`).
- **Faz 8C — Golden zone, arz/talep, haftalık kanal**: `structure/golden_zone.py`,
  `structure/supply_demand.py`, `trend/weekly_channel.py`. `Timeframe.W1` eklendi.
- **Faz 2-EK — Kalan özellikler + W1**: `resample_to_w1`, `volatility.py`
  (realized_vol/keltner/vol_zscore/garch11_forecast), `channels.py`
  (frozen_channel_at/pivot_channel), `patterns_geom.py`, `hs_pattern.py`,
  `zones_sd.py`, `xsec.py`.
- **Faz 8D — Evren-geneli momentum/trend**: YENİ `UniverseIndicator` ABC (`compute_
  universe`), `momentum/alpha_rank.py`, `momentum/momentum_rank.py`,
  `trend/ma_systems.py`, `trend/ewmac.py`. `tlab universe-plot` komutu.
  **Açık TODO**: EWMAC forecast_scalar hâlâ empirik/rolling — K3'ün doğruladığı
  sabit tabloya (2,8→10.6 ... 64,256→1.87) henüz geçirilmedi.
- **K3 — Carver (Systematic Trading) hedefli çıkarım**: `bilgi-bankasi/teknik/
  11_carver_systematic.md` + `docs/spec/tlab_10_portfolio.md` (Faz 10 spec taslağı).
- **Faz 8E — Vol harvest, dönüş haritası, güvenli filtreler**: `pair/vol_harvest.py`
  (sürekli ağırlıklı, ADF/halflife'a göre duraklama), `scanner/confluence.py::
  build_reversal_map` (yalnızca destek/dip tarafı — direnç/tepe tarafı KAPSAM DIŞI),
  `scanner/filter_expr.py` (eval() kullanmayan güvenli AST ifade değerlendirici).
- **Faz 10 — Sinyalden Portföye**: `tlab/portfolio/` (risk.py/forecast.py/sizing.py/
  allocation.py::handcraft_weights), `tlab/backtest/metrics.py` (fitting disiplini,
  hız limiti). **Açık boşluk**: 16-varlıklı Tablo 10/11 handcraft kabul kriteri
  K3 kaynağında yok, test edilemedi (kod genel/N≥4 durumu için doğrulandı).
- **Faz 8B sonrası — görsel düzeltme + Streamlit tarama panosu**: `tlab/
  dashboard.py` (YENİ) — `tlab dashboard` komutu, sinyal tablosu + tıklanabilir
  grafik + "Bugünü Tara" butonu. Gerçek `IndicatorResult.from_json()` hatası
  (Timestamp/fiyat-indeksli seri ayrımı) bulunup düzeltildi.

### Kaldığı yer / hâlâ açık noktalar

- **Roadmap (ESKİ, 2026-08-31 döneminden — YENİ roadmap için aşağıya bak):**
  Faz 0-8E, K0-K3, Faz 10 TAMAMLANDI. "Sırada Faz 9" notu bu eski sıraya
  aitti; proje 2026-09-03'ten beri `docs/00_BASLANGIC_SIRASI.md`'deki YENİ
  16-adımlık denetim/yol haritasını izliyor (bkz. dosyanın en üstündeki
  "Durum" satırı) — Faz 9 bu yeni sırada YOK, eski roadmap'in bir parçası
  olarak askıda kaldı, yeniden ele alınmadan önce netleştirilmeli.
- **Faz 0.5'te (Adım 2) bulunan, HENÜZ KAPATILMAMIŞ 3 gerçek hata**
  (`docs/spec/SISTEMIK_DENETIM_v1.md`'de tam detay, `docs/PROGRESS_LOG.md`'nin
  2026-09-03/04 girdilerinde bulunma anı) — kasıtlı olarak o fazın kapsamı
  dışında bırakıldı, AMA unutulmasın diye burada da işaretli:
  - **BULUNAN HATA 1** — bazı formasyon sinyalleri (`retest_hold` durumu,
    3 bağımsız örnekte doğrulandı: VESBE/broadening, KRPLS/head_shoulders,
    SKBNK/triangle) grafikte HİÇ görünmüyor (renderer/declutter şüphesi).
    **Hedef: Faz 3/4 (SVG çizim motoru) — o faza başlarken ÖNCE bu bulguyu
    tekrar oku.**
  - **BULUNAN HATA 2** — `tlab plot`'un varsayılan pencereleme mantığı eski/
    expired sinyalleri gösteremiyor (sinyal tarihi pencerenin dışında
    kalıyor ya da sonraki büyük bir fiyat hareketi y-eksenini genişletip
    eski formasyonu görsel olarak sıkıştırıyor). **Hedef: Faz 3/4/S4
    (grafik yüzeyi) — "sinyal tarihine yakınlaştır" gibi bir çözüm
    değerlendirilmeli.**
  - **BULUNAN HATA 3** — `wedge`/`triangle`/`broadening` formasyonlarının
    süresine (P1-P2 pivot mesafesine) hiç üst sınır yok; `max_apex_bars`
    yalnızca doğum-apex mesafesini sınırlıyor. Gerçek veride (TUCLK) ~18 ay
    süren gerçekçi olmayan bir "formasyon" üretti. **Hedef: Adım 3 / Faz 1
    (klasik formasyon motoru v2) — bu fazın KAPSAMINA DAHİL EDİLDİ (aynı
    fazın `double_top_bottom.min_bars_between` gibi literatür-temelli
    süre/derinlik kısıtlarıyla AYNI iş, ayrı bir faz gerektirmiyor).**
- **`harmonic.five_zero`**: 622 sembollük tam BIST evreninde HİÇBİR aday bulamadı
  (iki farklı parametre setiyle de) — kök neden araştırılmadı, ayrı bir takip işi.
- **Dashboard**: "Bugünü Tara" `run_eod()`'u SENKRON çağırıyor (büyük evrende
  dakikalar sürebilir); gerçek otomatik günlük zamanlama hâlâ OS görev
  zamanlayıcısı (cron/Windows Görev Zamanlayıcı, `tlab eod`) gerektiriyor.
- **Backlog**: kullanıcı kararı bekleyen 5 madde (robust_stats, sektör rotasyonu,
  DuPont [bilanco-radar kapsamı], kointegrasyon çürüme izleyici, beta-nötr pair
  modu) — bkz. aşağıdaki "Sıradaki Adımlar / Backlog" bölümü.
- **Arayüz kararı henüz verilmedi** (Streamlit/masaüstü mü, web/HTML mi) —
  Bilanço Radar ile ileride birleşeceği için bilinçli olarak ertelendi.
- **TradingView masaüstü / Fintables / Bilanço Radar birleşmesi**: henüz
  tasarlanmadı, yalnızca hedef notu (aşağıdaki "Gelecek Entegrasyonlar").

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
docs/spec/       tlab_NN_*.md — teknik-analiz-uzmani'nin (bilanco-radar agent'ı)
                 ürettiği spec taslakları (K3'ten sonra: tlab_10_portfolio.md)
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

**Roadmap durumu (2026-08-31, güncellendi):** Faz 8B, Faz 8D ve **K3 TAMAMLANDI**
(aynı gün, Faz 8D'nin hemen ardından). K3 — Carver ("Systematic Trading") kitap
çıkarımı, kullanıcı kararıyla HEDEFLİ (kitabın tamamı değil, master prompt madde
1-6'nın istediği ~180 sayfa: forecast/scalar/capping, vol targeting, position sizing,
handcrafting, fitting disiplini, EWMAC, hız limiti) — çıktı `bilanco-radar/bilgi-
bankasi/teknik/11_carver_systematic.md` (KURAL-01/05, ORAN-01..10, DISIPLIN-01..12,
PSK-01/02) + bu projede **YENİ** `docs/spec/tlab_10_portfolio.md` (Faz 10'un
`tlab/portfolio/{forecast,sizing,allocation,risk}.py` + `backtest/metrics.py`
genişletmesi için TASLAK spec — henüz KOD YAZILMADI, bu bir spec dokümanı). Gerçek
bulgu: `trend.ewmac`'in (Faz 8D) forecast scalar'ı empirik/rolling hesaplıyordu çünkü
K3 henüz yapılmamıştı; K3'ün ORAN-01'i kitaptan DOĞRULANMIŞ sabit tabloyu (EWMAC 2,8→
10.6 ... 64,256→1.87) verdi — bu tablonun `ewmac.py`'ye ENTEGRASYONU (sabit-tablo
seçeneği) bu oturumda YAPILMADI, Faz 10'un/ayrı bir takip işinin parçası olarak
bırakıldı (K3 bir BİLGİ görevi, `ewmac.py`'ye dokunmadı). Roadmap sırasına göre
sıradaki resmi adım **Faz 8E** (vol harvest + GARCH) → Faz 10 (K3 spec onayı ön
koşuluydu, artık spec TASLAĞI var — kullanıcı onayı gerekiyor) → Faz 9. Aşağıdaki
backlog listesi (1-5) bu roadmap'ten BAĞIMSIZ, ayrı bir kullanıcı kararı bekleyen
öneriler.

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
