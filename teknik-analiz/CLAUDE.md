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
- **Sırada**: K2 (11 bölümlük külliyat incelemesi, paralel) ve Faz 4 adayları "Sıradaki
  Adımlar" bölümünde.

Toplam 157 test yeşil (`pytest -m "not network"`), ruff/mypy/lint_lookahead temiz.

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
