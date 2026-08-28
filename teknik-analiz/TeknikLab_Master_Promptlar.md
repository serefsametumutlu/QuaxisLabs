# TEKNİK LAB — Birleşik Prompt Sırası (Master)
## Faz 0'dan Faz 10'a: kod fazları + kaynak/agent görevleri, tek sırada

Tarih: 28.08.2026 | Durum: Faz 0–3 TAMAMLANDI, K0/K1/K1-D/EK-A TAMAMLANDI, sırada K2 veya Faz 4 (CLAUDE.md'ye işlendi)

## Kullanım
1. Her prompttan önce aşağıdaki **PROJE BAĞLAMI** bloğunu aynen yapıştır (K0–K3 bilgi
   görevlerinde gerekmez; onlar repo kökünde, kod fazları teknik-analiz/ içinde çalışır).
2. Sıra aşağıdaki tablodur. ✅ = bitti (referans için duruyor), ▶ = şu an, ⏳ = sırada.
3. Bir faz bitmeden diğerine geçme: `pytest -q` + `tlab repaint-test --all` + `tlab lint`
   yeşil olmalı; CLAUDE.md güncellenmiş olmalı.
4. Sonnet onay-barı kuralını esnetmeye çalışırsa kabul etme; PROJE BAĞLAMI'ndaki kuralı hatırlat.

| # | Görev | Tür | Durum / Not |
|---|---|---|---|
| 1 | FAZ 0 — iskelet + repaint altyapısı | kod | ✅ |
| 2 | FAZ 1 — veri katmanı | kod | ✅ |
| 3 | FAZ 2 — özellik katmanı | kod | ✅ |
| 4 | FAZ 3 — harmonik motor (8 ekol) | kod | ✅ |
| 5 | K0 — agent/skill/bilgi-bankası iskelesi | bilgi | ✅ (bilanco-radar 8eb4627) |
| 6 | K1 — Pesavento (TWYS) çıkarımı | bilgi | ✅ (bilanco-radar a4f71a7) |
| 7 | K1-D — pesavento.py'yi kitapla hizala | kod | ✅ |
| 8 | EK-A — Three Drives paterni | kod | ✅ (three_drives.py hizalandı, pesavento.py'ye yinelenmedi) |
| 9 | K2 — 11 bölümlük külliyat incelemesi | bilgi | ⏳ paralel yürüyebilir |
| 10 | FAZ 4 — yapı indikatörleri | kod | |
| 11 | FAZ 5 — pair relatif momentum | kod | |
| 12 | FAZ 6 — tarama motoru + EOD | kod | |
| 13 | FAZ 7 — görselleştirme + rapor | kod | |
| 14 | FAZ 2-EK — yeni feature'lar + W1 | kod | Faz 8 ön koşulu |
| 15 | FAZ 8A — kırılım tarayıcısı (+Donchian/BB) | kod | ch1 ekleri içinde |
| 16 | FAZ 8C — bölgeler (golden/S-D/kanal) | kod | |
| 17 | FAZ 8B — formasyonlar (+çift tepe/dip, broadening) | kod | TWYS ekleri içinde |
| 18 | FAZ 8D — cross-sectional (+KAMA, EWMAC) | kod | Carver'ın ilk kuralı burada |
| 19 | K3 — Carver çıkarımı + Faz 10 spec | bilgi | Faz 8 sırasında paralel |
| 20 | FAZ 8E — vol harvest (+GARCH) + dönüş haritası | kod | |
| 21 | FAZ 10 — sinyalden portföye (Carver+ch10+ch11) | kod | K3 spec onayı ön koşul |
| 22 | FAZ 9 — API + entegrasyonlar (+PEAD köprüsü) | kod | |

---

## PROJE BAĞLAMI (kod fazlarının başına aynen yapıştır)

```
PROJE BAĞLAMI — TEKNİK LAB

Bu repo, BIST ve NASDAQ hisseleri için Python tabanlı bir teknik analiz / indikatör laboratuvarıdır.
Amaç: ortak arayüze uyan indikatör modülleri, 4H + 1D çoklu zaman dilimi tarama motoru, gün sonu
(EOD) otomatik tarama, tekil hisse için Plotly ile tam görsel çıktı. İleride "Bilanço Radar" adlı
temel analiz projesiyle tek app'te birleşecek; bu yüzden çekirdek mantık arayüzden tamamen bağımsız
tasarlanır (Streamlit/web/masaüstü kararı verilmedi).

MÜZAKEREYE KAPALI KURALLAR:
1. NON-REPAINTING: Bir sinyalin t barındaki değeri yalnızca t ve öncesi verilerle hesaplanır ve
   sonradan asla değişmez. Pivot tabanlı hesaplarda sinyal tarihi = pivotun ONAYLANDIĞI bar
   (pivot barı değil). Signal nesnesinde bar_time ve detected_at ayrı tutulur.
   Yasak: df.shift(-n), rolling(center=True), find_peaks/argrelextrema sonucunu doğrudan sinyal
   barına yazmak, geleceğe bakan interpolasyon, açık (kapanmamış) barla sinyal üretmek.
   Her indikatör tlab/testing/repaint.py içindeki walk-forward eşitlik testinden geçmeden
   registry'ye kaydedilemez.
2. KATMAN AYRIMI: data → features → indicators → scanner → results → viz. Oklar tek yönlü.
   İndikatörler veri kaynağını bilmez; viz hesap yapmaz; scanner indikatör içini bilmez.
3. DETERMİNİSTİK: Aynı veri + aynı parametre = aynı sonuç. Parametreler frozen dataclass,
   params_hash ile sonuçlara işlenir. Global durum ve random yok.
4. TÜM ÇIKTILAR GÖRSELLEŞTİRİLEBİLİR: Her indikatör IndicatorResult döner: signals, levels,
   lines, boxes, polygons, markers, series (alt panel). "Sinyal var/yok" metni yeterli değildir.
5. KOD STANDARDI: Python 3.11+, type hints zorunlu, pandas/numpy, pydantic yok (dataclass),
   ruff + mypy temiz, pytest. Docstring'ler Türkçe, kod tanımlayıcıları İngilizce.
   Kullanıcıya dönen etiket metinleri Türkçe (AKTİF, TAMAMLANDI, Kırılım, Temas, Direnç, Destek).
6. Bir şey belirsizse tahmin edip ilerlemek yerine önce soru sor; ama tasarım kararı gerektiren
   noktalarda önce kendi önerini gerekçesiyle sun, onay bekle.

REPO VE ÇALIŞMA DİZİNİ: QuaxisLabs reposu; teknik proje teknik-analiz/ klasöründedir
(paket: teknik-analiz/tlab). Tüm komutlar (pytest, tlab ...) teknik-analiz/ içinde koşulur.
K0 sonrası .claude/skills/tlab-mimari/SKILL.md mevcuttur; işe başlamadan onu ve CLAUDE.md'yi oku.
CLAUDE.md KURALI: Her faz sonunda CLAUDE.md güncellenir: tamamlanan faz, eklenen modüller,
registry'deki indikatörler, değişen sözleşme/karar ve bir sonraki fazın ön koşulları.
BİLGİ BANKASI ATIFLARI: Kaynaklardan gelen her kural/oran/formül için kod docstring'inde
bilgi-bankasi/teknik/<dosya>/<KOD-xx> atıfı bulunur (örn. 10/ORAN-04). İlgili çıkarım henüz
yoksa "# TODO(bilgi-bankasi): ..." bırakılır, uydurulmaz.

Çalışma tarzı: Önce planını madde madde yaz, onay al, sonra kodla. Her dosyayı yazdıktan sonra
ilgili testi koş. Faz sonunda özet + git commit.
```

---

## 1 · FAZ 0
> **Durum:** ✅ TAMAMLANDI — referans

```
FAZ 0 GÖREVİ — Proje iskeleti, çekirdek sözleşme ve repaint test altyapısı

Hedef: Diğer tüm fazların üzerine inşa edileceği paket iskeletini, indikatör sözleşmesini ve
repaint/lookahead denetim altyapısını kur. Bu fazda hiçbir gerçek indikatör YAZILMAYACAK;
sadece altyapı ve onu doğrulayan sahte indikatörler.

1) Paket iskeleti
   - pyproject.toml (paket adı tlab, Python>=3.11, bağımlılıklar: pandas, numpy, scipy,
     pyarrow, plotly, typer, pyyaml, statsmodels, yfinance; dev: pytest, ruff, mypy, hypothesis)
   - Şu dizinleri boş __init__ ile oluştur: tlab/core, tlab/data, tlab/features,
     tlab/indicators/{harmonics/schools,structure,pairs,trend,momentum}, tlab/scanner,
     tlab/backtest, tlab/viz, tlab/testing, tests/, config/, data/ (gitignore), outputs/ (gitignore)
   - README.md: kuralları (özellikle non-repaint sözleşmesini) ve dizin yapısını yaz.

2) tlab/core/types.py
   - Timeframe(str, Enum): H4="4H", D1="1D" (ileride H1, W1 eklenebilir şekilde)
   - Frozen dataclass'lar: Level, Line, Box, Polygon, Marker, Signal, IndicatorMeta,
     IndicatorResult (alanlar: indicator, version, params_hash, symbol, timeframe, signals,
     levels, lines, boxes, polygons, markers, series: dict[str, pd.Series], last_state: dict)
   - Signal: bar_time, detected_at (>= bar_time zorunlu, __post_init__'te doğrula), direction
     Literal["long","short","neutral"], state Literal["pending","active","confirmed",
     "invalidated","completed"], score float 0..1, payload dict
   - IndicatorResult.to_json()/from_json() (Series'ler {timestamp: value} olarak)
   - validate_ohlcv(df): tz-aware DatetimeIndex, monoton artan, tekrarsız; kolonlar open, high,
     low, close, volume; high>=max(open,close), low<=min(open,close); NaN yok. Hata: OHLCVError.

3) tlab/core/params.py: BaseParams (frozen dataclass) + params_hash(params) -> str (sha1 of
   sorted json). tlab/core/errors.py.

4) tlab/core/indicator.py
   - BaseIndicator(ABC): meta: IndicatorMeta, params; abstract compute(df, context=None)
     -> IndicatorResult; __call__ önce validate_ohlcv çağırır, sonra compute, sonra sonucu doğrular
     (tüm bar_time'lar df.index içinde, detected_at >= bar_time, detected_at <= df.index[-1]).
   - Registry: register(cls) yalnızca repaint testi PASS ise ekler (tlab.testing.repaint
     içinden çağır); get(name), list(category=None). Registry'e kaydedilmemiş indikatörü
     scanner çalıştıramayacak (bunu Faz 6'da kullanacağız; şimdilik arayüzü yaz).

5) tlab/testing/fixtures.py — Sentetik OHLCV üreticiler (deterministik, seed parametreli):
   - make_trend(n, slope, noise), make_zigzag(n, pivots=[(bar, price), ...]) — verilen pivot
     noktalarını kesin olarak içeren, aralarda lineer + küçük gürültülü seri
   - make_harmonic(pattern_ratios, bullish: bool) — verilen XA, AB/XA, BC/AB, CD/BC oranlarıyla
     X,A,B,C,D barlarını üreten seri (Faz 3'te kullanılacak)
   - Hepsi 4H ve 1D için tz-aware (Europe/Istanbul) index üretebilsin.

6) tlab/testing/repaint.py — WALK-FORWARD EŞİTLİK TESTİ
   - repaint_test(indicator, df, cut_points: list[int] | None = None, tail: int = 60) -> RepaintReport
   - Algoritma: full = indicator(df). Her cut in cut_points (varsayılan: son tail barın her biri)
     için partial = indicator(df.iloc[:cut]). partial içindeki her Signal, full içinde
     (bar_time, detected_at, direction, state) tam eşleşmeli ve payload içindeki sayısal alanlar
     1e-9 toleransla eşit olmalı. Ayrıca partial'daki Level/Line/Box/Polygon'lar (start/t0 tarihi
     cut'tan önce olanlar) full'de birebir bulunmalı (kutuların t1'i büyüyebilir; bunu ayrıca
     "extend-only" kuralı olarak kontrol et: t1 azalamaz, low/high değişemez).
   - RepaintReport: passed: bool, mismatches: list[str] (okunabilir), stats.
   - Performans: indikatör compute'u pahalıysa cut_points seyreltilebilir (stride parametresi).

7) tlab/testing/lint_lookahead.py — Statik denetim
   - ast ile tlab/features ve tlab/indicators altındaki tüm .py dosyalarını tara; şunları bul:
     .shift(negatif literal), rolling(... center=True ...), .iloc[i+ ...] deseni riskli olarak
     uyar (raporla), scipy.signal.find_peaks / argrelextrema import'u (uyarı: "sonucu sinyal
     barına yazma"), df.index[-1] dışına datetime üretimi (best-effort). Çıktı: liste; hata varsa
     exit code 1.

8) Kanıt testleri (tests/test_repaint_infra.py):
   - HonestIndicator: basit SMA kesişimi (rolling, sadece geçmiş) → repaint_test PASS olmalı.
   - CheatingIndicator: argrelextrema ile pivot bulup pivot barına sinyal yazan → FAIL olmalı ve
     mismatch mesajı hangi barın sonradan ortaya çıktığını göstermeli.
   - CenteredIndicator: rolling(center=True) → hem repaint FAIL hem lint uyarısı.
   - Registry: CheatingIndicator.register çağrısı RegistryError fırlatmalı.

9) tlab/cli.py (typer): şimdilik "tlab repaint-test <module:Class>" ve "tlab lint" komutları.
   Makefile veya justfile: test, lint, typecheck, repaint-all.

10) GitHub Actions veya en azından pre-commit config: ruff, mypy, pytest, lint_lookahead.

Kabul kriteri: pytest tümü geçiyor; CheatingIndicator/CenteredIndicator testleri FAIL'i doğru
raporluyor; ruff+mypy temiz. Sonunda dosya listesi ve kısa özet ver, git commit at:
"faz0: iskelet, çekirdek tipler, repaint test altyapısı".
```

---

## 2 · FAZ 1
> **Durum:** ✅ TAMAMLANDI — referans

```
FAZ 1 GÖREVİ — Veri katmanı (sağlayıcılar, cache, BIST'e özel 4H resample, takvim, validasyon)

Bağlam: Faz 0'daki validate_ohlcv ve tipler mevcut. Bu fazda indikatörlerin tüketeceği standart
OHLCV verisini güvenilir şekilde üreten katmanı kuruyoruz. Veri kalitesi hatası = yanlış sinyal;
bu yüzden validasyon sıkı olacak.

1) tlab/data/providers/base.py: DataProvider(ABC) — fetch(symbol, market, timeframe, start, end)
   -> pd.DataFrame (validate_ohlcv'den geçmiş, tz-aware; BIST için Europe/Istanbul, NASDAQ için
   America/New_York). Sembol kuralı: BIST sembolleri "TCELL" olarak tutulur, provider'a giderken
   "TCELL.IS" eki provider içinde eklenir; NASDAQ "AAPL".
2) providers/yfinance_provider.py: 1H ve 1D indirir (1H için yfinance'in ~730 gün limiti var;
   bunu belgele ve artımlı çekimle cache'i büyüt). Ayarlanmış kapanış (auto_adjust) politikasını
   settings.yaml'da parametre yap; varsayılan: adjusted=True, ancak raw close'u da "close_raw"
   kolonu olarak sakla.
3) providers/csv_provider.py: kullanıcı CSV/parquet klasöründen okur (ileride TradingView export
   ve Fintables için köprü). Kolon eşleme (date/time/open/... büyük-küçük harf ve Türkçe
   başlık toleranslı) settings ile.
4) tlab/data/calendar.py: BIST seans 10:00–18:00 (tek seans, 12:30–13:30 arası ara YOK —
   doğrula, gerekirse parametreleştir), resmi tatiller listesi config/holidays_tr.yaml
   (2025–2027'yi doldur; Ramazan/Kurban bayramları için tarihleri açıkça yaz). NASDAQ 09:30–16:00,
   pandas_market_calendars kullanma (bağımlılık istemiyoruz), basit statik liste yeterli.
   Fonksiyonlar: is_trading_day, last_closed_session(now), session_bounds(date).
5) tlab/data/resample.py: resample_to_4h(df_1h, market)
   - BIST: 4H barlar seans başlangıcına hizalı: [10:00–14:00), [14:00–18:00]. İkinci bar 4 saat
     içeriyor mu, seans 18:00'de mi bitiyor — takvimden al. Gün dışına taşan bar OLMAYACAK.
   - NASDAQ: [09:30–13:30), [13:30–16:00] (ikinci bar 2.5 saat; bunu belgele; alternatif olarak
     "6.5h/2" eşit bölme parametresi).
   - Kısmi barlar (o gün henüz kapanmamış) "is_closed=False" olarak işaretlenir; varsayılan olarak
     DÜŞÜRÜLÜR. Açık bar asla indikatöre gitmez.
   - Kural: resample ASLA ileri bakan hizalama yapmaz (label='left', closed='left' mantığı; tek
     tek doğrula).
6) tlab/data/store.py: parquet cache data/ohlcv/{market}/{symbol}/{tf}.parquet; update(symbol,
   tf) artımlı (son bar tarihinden itibaren çek, örtüşen 5 barı yeniden yaz), get(symbol, tf,
   last_n=None). 4H her zaman 1H'den türetilir, ayrı parquet'e yazılır ve 1H güncellenince
   yeniden üretilir.
7) tlab/data/validate.py: boşluk tespiti (takvime göre eksik seans), sıfır/negatif hacim,
   aşırı gap (|log return| > 0.5 → split şüphesi uyarısı), tekrar eden timestamp, tz hatası.
   Rapor: DataQualityReport (warnings/errors). Errors olan sembol tarama dışı bırakılır ve loglanır.
8) config/settings.yaml, config/universe_bist.txt (BIST100'ü doldur: gerçek sembol listesini
   yaz), config/universe_nasdaq.txt (NASDAQ100). Sembol dosyaları satır başına bir sembol, #
   ile yorum.
9) CLI: tlab update-data --market bist --tf 1h,1d [--symbols TCELL,ISCTR] [--all];
   tlab data-quality --market bist. Loglama: rich veya logging, ilerleme çubuğu.
10) Testler: resample için sentetik 1H seri → 4H barların 10:00/14:00 hizalandığını, açık barın
    düşürüldüğünü, hiçbir 4H barın 1H barlarının zaman aralığı dışında veri taşımadığını doğrula.
    calendar için tatil/hafta sonu testleri. store için artımlı güncelleme idempotentliği.
    yfinance testleri network gerektirdiğinden @pytest.mark.network ile işaretle, varsayılan
    dışı.

Kabul kriteri: tlab update-data --symbols TCELL,ISCTR,ALARK,THYAO,ASELS --tf 1h,1d çalışır;
data/ohlcv/bist/TCELL/{1H,1D,4H}.parquet oluşur; tlab data-quality temiz; testler geçer.
git commit: "faz1: veri katmanı".
```

---

## 3 · FAZ 2
> **Durum:** ✅ TAMAMLANDI — referans

```
FAZ 2 GÖREVİ — Non-repainting özellik katmanı (swings, fibonacci, trendlines, ranges, zones,
volume profile, stats, ma, oscillators)

Bu katman tüm indikatörlerin paylaştığı SAF fonksiyonlardan oluşur. Her fonksiyon df alır,
Series/DataFrame veya küçük dataclass listeleri döner, yan etkisi yoktur. Her fonksiyon için
hem birim test hem de repaint testi (fonksiyonu sarmalayan mini indikatörle) yazılacak.
Bu katmanın en kritik dosyası swings.py'dir; onunla başla ve onu tamamen bitirmeden diğerine geçme.

1) tlab/features/swings.py
   - Pivot dataclass: bar_idx, bar_time, price, kind ("high"/"low"), confirmed_idx,
     confirmed_time, label ("HH","HL","LH","LL", None)
   - find_pivots(df, left: int, right: int) -> list[Pivot]
     Kural: bar i pivot high ise high[i] > high[i-left..i-1] ve high[i] >= high[i+1..i+right]
     (eşitlik politikası parametre: strict/nonstrict). Pivot ANCAK i+right barında bilinir;
     confirmed_idx = i+right. Serinin son `right` barında pivot ARANMAZ (henüz onaylanamaz).
   - alternate_pivots(pivots): ardışık iki high arasında en yüksek olan kalır, iki low arasında
     en düşük — zigzag. DİKKAT: Alternasyon kararı da onay barına göre verilir: Bir high pivotu
     "daha yüksek bir high" tarafından iptal ediliyorsa, iptal, yeni high'ın onay barında olur.
     Zigzag serisinin her noktası için "hangi barda kesinleşti" bilgisini taşı (finalized_idx).
     Bunu repaint testinin en zor yakalayacağı yer olarak gör ve testini özellikle yaz.
   - label_structure(zigzag): HH/HL/LH/LL etiketleri; etiket önceki aynı türden pivotla
     kıyaslanarak, kesinleşme barında verilir.
   - Alternatif algoritma: atr_zigzag(df, atr_mult) — ATR tabanlı ters dönüş eşiği ile zigzag;
     dönüş, fiyat eşik kadar ters yöne gittiği BARDA onaylanır. Her iki yöntem de aynı Pivot
     arayüzünü döner.
2) tlab/features/fibonacci.py
   - retracement(p0, p1, levels=(0.236,0.382,0.5,0.618,0.786,0.886,1.0)) -> dict
   - extension(p0, p1, levels=(1.0,1.272,1.414,1.618,2.0,2.24,2.618))
   - projection_abcd(a,b,c, ratios=(1.0,1.272,1.618)) -> D adayları
   - ratio(a,b,c) yardımcıları ve within(x, lo, hi, tol) tolerans fonksiyonu (mutlak/oransal)
3) tlab/features/trendlines.py
   - Trendline dataclass: p1, p2 (Pivot), slope, intercept (index tabanlı), kind (resistance
     / support), touches: list[int], broken_at: int|None, created_idx (p2.confirmed_idx)
   - build_trendlines(df, pivots, kind, min_touches=2, tol_atr=0.3, max_lines=…): aynı türden
     pivot çiftlerinden çizgi; çizgi oluştuğu bardan (p2 onayı) itibaren her barda:
     temas = high (veya low) çizgiye tol içinde ve kapanış çizgiyi geçmemiş; kırılım = kapanış
     çizginin ötesinde (confirm_bars parametresiyle 1 veya 2 bar). Hepsi ileriye doğru, bar bar.
   - Çizgi seçim kriteri (çok fazla çizgi olmasın): en çok temaslı, en uzun süreli, henüz
     kırılmamış olanlar öncelikli; parametre.
4) tlab/features/ranges.py — Konsolidasyon kutuları
   - detect_ranges(df, min_bars, atr_mult, breakout_confirm): Son min_bars barın (high-low)
     aralığı < atr_mult × ATR ise kutu AÇILIR (t0 = pencerenin başı, tespit barı = t0+min_bars;
     kutu sınırları pencerenin high/low'u ile SABİTLENİR). Sonra her barda fiyat kutu içindeyse
     t1 = t; kapanış kutu dışına çıkarsa breakout (yön ile) ve kutu kapanır. Kutu sınırları
     kapanana kadar değişmez (extend-only).
5) tlab/features/zones.py — Destek/direnç bölgeleri
   - Onaylı pivotların fiyatlarını ATR tabanlı bant genişliği ile kümele (basit 1D
     kümeleme, sklearn yok). Bölge, kümeye k'inci pivot katıldığı barda doğar (k=min_pivots);
     merkez/kalınlık o anda sabitlenir, sonra sadece touches artar. Kırılım = kapanış bölge
     dışında + confirm.
6) tlab/features/volume_profile.py
   - profile(df_window, bins) -> price_bins, volumes; poc, value_area(0.70); gaussian_fit
     (scipy curve_fit; yakınsamazsa None). Pencere sabit ve geriye dönüktür.
7) tlab/features/stats.py — zscore(series, window), log_spread(y, x, beta), rolling_beta(y,x,
   window) (OLS), halflife(spread), adf_pvalue(spread) (statsmodels), rolling_corr.
8) tlab/features/ma.py — sma, ema, wma, hull; crossovers (kesişim barı). oscillators.py — macd,
   rsi, stochastic; histogram; cross signals.
9) Testler:
   - swings: make_zigzag ile bilinen pivotlar tam o barlarda, confirmed_idx = idx+right; son
     `right` barda pivot yok; alternasyon iptalinin finalized_idx'i doğru.
   - Her feature için mini sarmalayıcı indikatörle repaint_test PASS (tests/test_features_repaint.py).
   - hypothesis ile rastgele serilerde: find_pivots(df[:n]) ⊆ find_pivots(df) (onaylı pivotlar
     asla kaybolmaz, sadece eklenir) — bu, non-repaint'in matematiksel ifadesidir; property test
     olarak yaz.
   - lint_lookahead tlab/features üzerinde temiz.

Kabul kriteri: tüm testler + property testleri geçer; tlab lint temiz. git commit:
"faz2: özellik katmanı".
```

---

## 4 · FAZ 3
> **Durum:** ▶ DEVAM EDİYOR — verilen prompt, referans

```
FAZ 3 GÖREVİ — Çoklu-ekol harmonik formasyon motoru (non-repainting, durum makineli)

Bu projenin ana modülü. Ortak geometri + ekol başına izole kural seti + durum makinesi.
Referans görseller: (a) ALARK Bearish Butterfly, D: 125.42 [AKTİF], X→B çizgisi 2026-07-20'de
yukarı kırıldı; (b) Bullish XABCD, D: 6.15 [TAMAMLANDI]. Bu ikisi birebir üretilebilmeli.

MİMARİ
1) tlab/indicators/harmonics/geometry.py
   - Faz 2 swings.alternate_pivots çıktısından ardışık 4 pivot (X,A,B,C) adayları üretir.
     Aday ANCAK C pivotu kesinleştiği barda (C.finalized_idx) doğar. Aynı X,A,B ile birden fazla
     C adayı olabilir (C güncellenirse yeni aday, eski aday invalidated).
   - Her aday için oranlar: ab_xa, bc_ab, (D için) cd_bc ve xd_xa (D bilinmediği için bunlar
     projeksiyon). Zaman uzunlukları: bars_xa, bars_ab, bars_bc.
2) tlab/indicators/harmonics/prz.py
   - PRZ dataclass: low, high, center, components: dict (hangi projeksiyondan geldiği: xa_ext,
     bc_ext, abcd, xc_ret ...), created_idx.
   - compute_prz(match, method): "intersection" (Carney: bileşenlerin kesişim/yoğunluk bandı),
     "single_pm_tol" (Pesavento: tek seviye ± tolerans), "custom" (ekol fonksiyonu).
3) tlab/indicators/harmonics/state.py — DURUM MAKİNESİ (her geçiş kendi barında, geriye yazım yok)
   - PENDING: C kesinleşti, PRZ hesaplandı, fiyat henüz PRZ'ye ulaşmadı.
   - ACTIVE: fiyat (bearish için high, bullish için low) PRZ'ye ilk temas ettiği bar. Signal
     üretilir: bar_time = detected_at = bu bar. Etiket "AKTİF".
   - CONFIRMED (etiket "TAMAMLANDI"): ACTIVE sonrası, dönüş teyidi. Teyit politikası parametre:
     "close_reversal" (kapanış PRZ'nin ters tarafında + reversal_bars kadar bar), "xb_break"
     (X→B trend çizgisi kırılımı — Pesavento), "pivot" (D pivotu onaylandığında; en yavaş ama
     yine non-repaint çünkü onay barında damgalanır), "school" (ekolün extra_confirmation'ı).
   - INVALIDATED: fiyat PRZ'nin ötesine max_overshoot (XA'nın %x'i) kadar geçerse ya da
     PENDING'de yeni bir C oluşup yapı bozulursa. Damga = ihlal barı.
   - EXPIRED: Gilmore zaman penceresi aşılırsa (sadece gilmore ekolü).
   - Aynı formasyon için bütün geçmiş durumlar Signal listesinde kalır (pending→active→confirmed
     üç ayrı Signal, aynı pattern_id payload'ı ile). Tarama "bugün ne durumda" için last_state.
4) tlab/indicators/harmonics/schools/base.py
   class HarmonicSchool(ABC):
     name; patterns: dict[str, PatternSpec]; tolerance
     def match(self, cand) -> list[PatternMatch]      # oran + ek kurallar
     def prz(self, match) -> PRZ
     def extra_confirmation(self, df, match, t) -> bool  # varsayılan True
     def time_window(self, match) -> tuple[int,int] | None  # varsayılan None
   PatternSpec: xab (lo,hi), abc (lo,hi), bcd (lo,hi), xad (lo,hi), extra: dict
   Ekoller birbirini import ETMEZ.
5) schools/ — her ekol ayrı dosya, kurallar:
   carney.py — tolerance 0.03 (oransal). gartley: B 0.618, C 0.382–0.886, D 1.13–1.618 BC ve
     0.786 XA. bat: B 0.382–0.50, C 0.382–0.886, D 1.618–2.618 BC ve 0.886 XA. crab: B 0.382–
     0.618, C 0.382–0.886, D 2.24–3.618 BC ve 1.618 XA. deep_crab: B 0.886, D 1.618 XA. butterfly:
     B 0.786, D 1.618–2.24 BC ve 1.27 XA. shark: (0,X,A,B,C): C 1.13–1.618 AB uzantısı, D 0.886–
     1.13 X0 (0'ın 0.886 retrace veya 1.13 uzantısı) ve 1.618–2.24 BC. PRZ = intersection.
   pesavento.py — tolerance 0.05. butterfly: B 0.786 XA, C 0.382–0.886 AB, D 1.27–1.618 XA ve
     AB=CD (1.0 / 1.27 / 1.618). gartley 0.618/0.786. Ek: AB=CD simetrisi zorunlu (CD/AB ∈
     {1.0,1.27,1.618} ± tol). PRZ = single_pm_tol. extra_confirmation: X→B trend çizgisi kırılımı
     (trendlines.py ile; kırılım barı payload'a "xb_break_at" olarak yazılır — görselde
     "Kırılım: YUKARI yönde, 2026-07-20").
   gilmore.py — Pesavento oranlarını taban al; ek olarak ZAMAN oranları: bars_cd / bars_ab ∈
     {1.0, 1.272, 1.618} ± tol_time ve bars_xd / bars_xa ∈ {0.618, 1.0, 1.618}. time_window():
     D'nin beklendiği bar aralığı (C'den itibaren). Fiyat PRZ'ye zaman penceresi DIŞINDA gelirse
     ACTIVE olmaz (payload'a "outside_time_window"); pencere kapanırsa EXPIRED. Görselde zaman
     penceresi dikey bant (Box) olarak çizilecek.
   oglesbee_cypher.py — B 0.382–0.618 XA; C 1.272–1.414 XA (C, A'yı AŞAR — geometry'de bunu
     mümkün kılan aday üretimi: klasik XABCD'de C, A'yı aşamaz; burada aşmalı; bunun için aday
     üretici "allow_c_beyond_a" parametresi alır); D 0.786 XC retracement. PRZ = 0.786 XC ± tol.
   kerkez_nenstar.py — B 0.382–0.618 XA; C 1.272–1.414 XA (A'yı aşar); D 1.272 XA ve 1.618–
     2.0 BC kesişimi. extra_confirmation: D barında EMA(20) ile EMA(50) ilişkisi trend yönüyle
     uyumlu ve MACD histogramı dönüş yönünde (aynı barda hesaplanan değerler; ileri bakmaz).
   beck_navarro200.py — B 0.382–0.618 XA; C 1.272–1.618 AB; D = 2.0 XA (%200) ± tol. PRZ dar
     (± tolerance/2). Ek: CD, AB=CD'nin 1.27 veya 1.618 uzantısı olmalı.
   five_zero.py — 5-0: noktalar 0,X,A,B,C,D: X-A dönüşü 1.13–1.618 (A, 0→X hareketinin
     1.13–1.618 uzantısı), A-B 1.618–2.24 XA uzantısı, C-D = 0.50 BC retracement (kesin 0.5 ±
     tol) ve AB=CD karşılığı (CD ≈ AB). Trend dönüş teyidi: D'de önceki trendin son swing
     yapısı kırılmış olmalı (structure label değişimi). 6 noktalı aday üretici gerekir — geometry
     bunu destekler (n_points parametresi).
6) tlab/indicators/harmonics/scanner_indicator.py
   - HarmonicIndicator(school: str, params: HarmonicParams(left, right, zigzag_method,
     confirmation_policy, max_overshoot, lookback_bars, allow_overlapping)) 
   - compute(): pivotlar → adaylar → school.match → PRZ → durum makinesi bar bar ilerletilir →
     IndicatorResult: polygons (XAB ve BCD üçgenleri gölgeli; bullish yeşil/bearish kırmızı),
     lines (X-A-B-C-D zigzag; X→B kesikli), levels (PRZ low/high, Fibonacci seviyeleri: XA
     retracement seti), markers (X,A,B,C,D etiketleri + "D: 125.42 [AKTİF]" / "[TAMAMLANDI]"),
     boxes (gilmore zaman penceresi), signals (durum geçişleri), last_state.
   - Registry'e 7 ayrı isimle kaydet: harmonic.carney, harmonic.pesavento, harmonic.gilmore,
     harmonic.cypher, harmonic.nenstar, harmonic.navarro200, harmonic.five_zero.
   - Skor (0..1): oran sapmalarının ortalaması (düşük = iyi), PRZ darlığı, ekol ek teyidi.
7) Testler (tests/test_harmonics/):
   - fixtures.make_harmonic ile her ekol için ≥1 pozitif fixture (doğru ekol eşleşir, yanlış
     ekoller eşleşmez veya düşük skor) ve ≥1 negatif fixture (oranlar tolerans dışı → eşleşme yok).
   - Durum geçişleri: fixture'ı D'ye kadar kes → last_state pending; PRZ'ye ilk temas barına kadar
     kes → active ve Signal.bar_time tam o bar; dönüş sonrası → confirmed. Her kesitte
     repaint_test PASS.
   - Cypher fixture'ında C > A olduğunu ve klasik (carney) tarafından reddedildiğini doğrula.
   - Gilmore: PRZ'ye zaman penceresi dışında gelen fixture → active olmamalı.
   - 7 ekol için repaint_test PASS (tests/test_harmonics_repaint.py); lint temiz.
   - Gerçek veri smoke testi (network mark): ALARK 1D son 300 bar, pesavento → en az bir
     butterfly adayı ve X→B kırılım tarihi payload'da.

Önce planı ve PatternSpec tablolarını yaz, onayımı al, sonra kodla. Kabul: yukarıdaki testler.
git commit: "faz3: harmonik motor, 7 ekol".
```

---

## 5 · K0
> **Durum:** ✅ TAMAMLANDI (2026-08-28, bilanco-radar commit 8eb4627) — referans

```
GÖREV K0 — Teknik kol bilgi-işleme iskelesi

Repo: QuaxisLabs. Bilanço Radar'daki bilgi sindirme sistemi (kitap-okuyucu agent,
kitap-bilgi-cikarma skill, bilgi-bankasi/ standardı, İLKE/FORMÜL/BAYRAK kodları ve
izlenebilirlik zinciri) teknik-analiz koluna genişletilecek. Önce mevcut dosyaları OKU:
.claude/agents/kitap-okuyucu.md, .claude/agents/quant-uzmani.md,
.claude/skills/kitap-bilgi-cikarma/SKILL.md, bilgi-bankasi/README.md,
teknik-analiz/README.md (tlab sözleşmesi). Stili ve standartları birebir koru.

1) Klasörler: kitaplar/teknik/ (iki PDF buraya taşınacak — ben koyacağım, sen README yaz:
   dosya adı standardı + telif notu: kitap metni repoya girmez, sadece damıtılmış bilgi),
   bilgi-bankasi/teknik/ ve bilgi-bankasi/teknik/kod/ (README'ler: çıktı standardı aşağıda).
2) bilgi-bankasi/teknik/ çıktı standardı (README'ye yaz):
   - Kitap dosyaları: 10_pesavento_twys.md, 11_carver_systematic.md
   - Kod türleri: KURAL-xx (uygulanabilir kural), ORAN-xx (sayısal oran/eşik + tolerans),
     FORMASYON-xx (patern tanımı: noktalar, oranlar, geçerlilik, geçersizlik, hedef, stop),
     DISIPLIN-xx (metodoloji kuralı), PSK-xx (istisna/psikoloji notu), STRAT-xx (kod bölümü
     stratejisi)
   - Her FORMASYON-xx'te ZORUNLU alan "Non-repaint çevirisi": yazarın tarifindeki her
     pivot/tepe/dip için "hangi barda bilinir" ifadesi (onay barı kuralı; tlab sözleşmesi).
   - Her STRAT-xx'te ZORUNLU üçlü: tlab uyum maliyeti (S/M/L), lookahead riski (satır
     referansıyla), BIST/EOD uygulanabilirliği (AL/PARK/DIŞI + gerekçe).
   - Küresel referans: bilgi-bankasi/teknik/10/FORMASYON-03 biçimi; spec ve kod docstring'leri
     bu kodlarla atıf yapar. _ilerleme.md aynı mantıkla.
3) Yeni agent .claude/agents/teknik-analiz-uzmani.md: bilgi-bankasi/teknik/ → docs/spec/
   tlab_NN_*.md spec yazarı. temel-analiz-uzmani.md'nin yapısını şablon al; sorumluluklar:
   çıkarımları tlab modül spec'ine çevirme (parametre tablosu, durum makinesi, kabul
   kriterleri, test fixture tarifi), çelişki yönetimi (kaynaklar çelişirse ikisini de
   parametre olarak spec'e koy), kod YAZMAZ. tools: Read, Write, Glob, Grep. model: sonnet.
4) Yeni agent .claude/agents/strateji-kod-inceleyici.md: uploads'taki chapter*.md kod
   bölümlerini inceleyen uzman. Sorumluluklar: her strateji sınıfını STRAT-xx olarak damıt
   (kod kopyalama — özü yaz), lookahead/repaint taraması (shift(-), tüm-seri istatistiği,
   cumsum tabanlı bakış, iloc[0]'a göre normalize gibi kalıpları satır referansıyla işaretle),
   tlab hedef modülü ve uyum maliyeti, 00_uygulanabilirlik_matrisi.md üretimi.
   tools: Read, Write, Bash, Glob, Grep. model: sonnet.
5) Mevcut agent güncellemeleri (dosyaları düzenle, mevcut içeriği bozmadan bölüm ekle):
   - kitap-okuyucu.md: "## Teknik kitap modu" bölümü: kod türleri KURAL/ORAN/FORMASYON/
     DISIPLIN/PSK; formasyon sayfaları şekil ağırlıklıysa sayfayı PyMuPDF ile PNG'ye render
     edip görsel incele (pdftotext şekilleri kaçırır); çıktılar bilgi-bankasi/teknik/.
   - quant-uzmani.md: "## Teknik-analiz (tlab) denetim görevleri" bölümü: (a) repaint
     denetçiliği — her tlab değişikliğinde cd teknik-analiz && pytest -q && tlab repaint-test
     --all && tlab lint çalıştır, kod okuyarak onay-barı kuralı ihlali ara; (b) backtest
     disiplini — in-sample sonuç sunumlarını işaretle, out-of-sample/walk-forward iste,
     turnover ve maliyet raporu iste (Carver çıkarımı geldikçe DISIPLIN-xx kodlarına atıf).
   - kod-gelistirici.md: teknik-analiz/ altında çalışırken tlab-mimari skill'ini okuma
     zorunluluğu notu.
6) Yeni skill .claude/skills/teknik-bilgi-cikarma/SKILL.md: yukarıdaki standardın skill
   hali + kitap odak tablosu: TWYS (AB=CD, Gartley 222, Butterfly, Three Drives, retracement
   girişleri, klasik formasyonlar, trend günleri, risk yönetimi) ve Carver (forecast ölçeği,
   vol targeting, pozisyon boyutlama, forecast/instrument ağırlıkları, diversification
   multiplier, fitting/overfitting, EWMAC, maliyet-hız).
7) Yeni skill .claude/skills/tlab-mimari/SKILL.md: teknik-analiz/README ve tlab/core'dan
   damıt: katman ayrımı, IndicatorResult sözleşmesi, Signal(bar_time, detected_at, state),
   NON-REPAINT kuralları ve yasak API listesi, registry-repaint ilişkisi, mevcut faz durumu
   tablosu (0-2 tamam, 3 devam). Agentların teknik işlerde İLK okuyacağı dosya.
8) bilgi-bankasi/teknik/_ilerleme.md başlangıç hali. Hiçbir Python koduna DOKUNMA.
git commit: "k0: teknik kol bilgi-işleme iskelesi (agentlar, skiller, bilgi bankası)".
```

---

## 6 · K1
> **Durum:** ⏳ ŞİMDİ, K0'dan hemen sonra, ÖNCELİKLİ (repo kökünde)

```
GÖREV K1 — Trade What You See (Pesavento & Jouflas 2007) bilgi çıkarımı

kitap-okuyucu agent'ını teknik modda kullan. Girdi: kitaplar/teknik/Trade_What_You_See_...
.pdf. Çıktı: bilgi-bankasi/teknik/10_pesavento_twys.md (+ _ilerleme.md güncel).

Sıra ÖNEMLİ — Faz 3'te pesavento.py şu an kodlanıyor; önce ekol bölümleri:
1) ÖNCE: AB=CD, Gartley "222", Butterfly, Three Drives bölümleri. Her biri için FORMASYON-xx:
   nokta tanımları, yazarın verdiği KESİN oranlar ve kabul ettiği alternatifler (ORAN-xx;
   örn. AB=CD'de CD/AB için hangi değerler, BC retracement bandı, Butterfly'da B=0.786
   ne kadar katı, hangi taşmalar geçersiz kılar), giriş taktiği (PRZ'de nasıl girilir),
   stop yerleşimi, hedefler, yazarın "bu desen şu durumda çalışmaz" istisnaları (PSK-xx).
   Şekil ağırlıklı sayfaları PNG render ederek incele; oranları şekil altyazılarından da
   doğrula. Her formasyona Non-repaint çevirisi yaz.
2) SONRA sırayla: Fibonacci retracement girişleri (golden zone karşılığı — 0.618/0.786
   kuralları, başarısızlık kriterleri), klasik formasyonlar bölümü (Double Top/Bottom,
   H&S, Broadening — her biri FORMASYON-xx), Trend Days bölümü (KURAL-xx; PARK etiketiyle),
   Opening Price Retracement (PARK), risk/emir yönetimi bölümleri (KURAL-xx).
3) Bittiğinde dosya sonuna "Faz 3 karşılaştırma tablosu" ekle: teknik-analiz/tlab/
   indicators/harmonics/schools/pesavento.py'daki mevcut PatternSpec değerleri ile kitaptan
   çıkan ORAN-xx değerlerini yan yana koy; FARKLI olan her satırı işaretle ve önerilen
   düzeltmeyi yaz. (Kodu düzeltme — sadece tablo; düzeltme ayrı görev.)
Kurallar: kitap metni aynen kopyalanmaz; damıtılmış Türkçe kural formatı; bölüm bitince
_ilerleme.md güncelle; bağlam taşarsa kaldığın yerden devam edilebilir olmalı.
git commit: "k1: TWYS bilgi çıkarımı (pesavento ekolü birincil kaynak)".
```

Sonrasında kısa bir düzeltme görevi: *"10_pesavento_twys.md sonundaki karşılaştırma tablosundaki farkları pesavento.py'ye uygula; her değişen değerin yanına `# bilgi-bankasi/teknik/10/ORAN-xx` atıfı koy; testleri ve repaint-test'i koş."*

---

## 7 · K1-D — pesavento.py'yi kitapla hizalama (Faz 3 ve K1 bitince)

```
GÖREV K1-D — Pesavento okulunun birincil kaynakla hizalanması
[PROJE BAĞLAMI bloğunu yapıştır]

bilgi-bankasi/teknik/10_pesavento_twys.md sonundaki "Faz 3 karşılaştırma tablosu"nu oku.
FARKLI işaretli her satır için schools/pesavento.py'deki PatternSpec/tolerans değerini
kitaptan çıkan ORAN-xx değeriyle değiştir; her değişikliğin yanına
# bilgi-bankasi/teknik/10/ORAN-xx atıfı koy. Kural farkı test fixture'larını etkiliyorsa
fixture'ları da kitap değerlerine göre güncelle (fixture'lar spesifikasyondur; kitap esastır).
Ek: kitaptaki giriş/stop tavsiyelerini Signal.payload'a öneri alanları olarak ekle
(suggested_stop, suggested_entry — hesaplanabilir olanlar; hesaplanamayanlar PSK notu).
pytest + repaint-test --all + lint yeşil. CLAUDE.md güncelle.
git commit: "k1-d: pesavento okulu TWYS ile hizalandı".
```


---

## 8 · EK-A — Three Drives paterni

```
[PROJE BAĞLAMI bloğunu yapıştır]
[PROJE BAĞLAMI bloğunu yapıştır]
bilgi-bankasi/teknik/10_pesavento_twys.md'deki Three Drives FORMASYON'unu schools/
pesavento.py'ye ekle: 3 itiş + 2 düzeltme; itişler arası fiyat simetrisi (1.27/1.618
uzantıları) ve ZAMAN simetrisi (itiş süreleri ~eşit, tolerans ORAN-xx'ten); 3. itişin
tamamlanma bölgesi PRZ olarak; durum makinesi aynen (pending: 2. itiş onayı + 3. itiş
projeksiyonu; active: PRZ temas; confirmed/invalidated). Sentetik fixture + repaint PASS.
Docstring'e ORAN/FORMASYON atıfları. git commit: "ek-a: three drives (twys)".
CLAUDE.md güncelle.
```

---

## 9 · K2 — Külliyat incelemesi (paralel yürüyebilir)

```
GÖREV K2 — 11 bölümlük strateji külliyatının incelenmesi ve uygulanabilirlik matrisi

strateji-kod-inceleyici agent'ını kullan. Girdi: kitaplar/teknik/chapters/chapter1.md ...
chapter11.md. Çıktı: bilgi-bankasi/teknik/kod/ch01_trend.md ... ch11_performans.md +
00_uygulanabilirlik_matrisi.md.

Her bölüm için:
1) Her strateji sınıfı/fonksiyonu → STRAT-xx: 3-5 cümle öz (girdi, hesap, sinyal kuralı),
   parametreler, hangi piyasa varsayımları.
2) Lookahead/repaint taraması — satır referansıyla; özellikle şu kalıplar: negatif shift,
   tüm-seri mean/std ile normalizasyon, iloc[0]'a göre kümülatif kıyas (ch9 PPP'deki gibi
   başlangıç-bağımlılık), rolling(center=True), gelecek pencere metriğiyle sinyal, backtest'te
   aynı bar kapanışında hem sinyal hem işlem varsayımı. Yazarın kendi uyarılarını da kaydet
   (örn. ch8'de realized_vol'ün trailing olması şartı, ch10'daki shift(1) disiplini) —
   bunlar bizim non-repaint sözleşmemizin doğrulamasıdır, DISIPLIN-xx olarak da işaretle.
3) tlab kararı: AL / PARK / KAPSAM DIŞI + hedef modül + uyum maliyeti (S/M/L) + gerekçe.
   Ön kararlarım (katılmıyorsan gerekçeyle itiraz et): ch1 AL (KAMA→features/ma, Donchian+
   Bollinger→8A kırılım türleri), ch2 AL (VECM/Johansen→pairs/discovery), ch3 PARK (VIOP),
   ch4 DIŞI, ch5 ŞARTLI PARK (purged CV şartıyla Faz 11 adayı), ch6 AL (PEAD→Faz 9
   Bilanço Radar köprüsü; multi-factor→temel tarafla ortak), ch7 KISMİ (GARCH AL, IV/VRP
   PARK), ch8 DIŞI (şimdilik), ch9 DIŞI (vol rejim fikri dipnot), ch10 AL (Faz 10),
   ch11 AL (backtest/metrics genişletme).
4) 00_uygulanabilirlik_matrisi.md: tüm STRAT'lar tek tablo (STRAT, bölüm, karar, hedef
   modül, maliyet, lookahead notu, hangi fazda). Kod kopyalanmaz; uyarlama her zaman tlab
   sözleşmesiyle yeniden yazımdır.
git commit: "k2: strateji külliyatı incelemesi ve uygulanabilirlik matrisi".
```

---

## 10 · FAZ 4

```
FAZ 4 GÖREVİ — Fiyat yapısı indikatörleri: swing_fib_abcd ve price_structure

Referans görseller: (Görsel 3) TCELL Swing Yapısı, Fibonacci ve AB=CD (Düşüş), "Harmonik sayı:
13.99 TL", D hedefleri [TAMAM]; (Görsel 2) trend çizgileri (Kırılım 2026-05-08 Temas:3; Direnç
Temas:6), konsolidasyon kutuları, sarı direnç / mavi destek bantları, hacim profili + Gaussian fit,
hacim + MA, MACD tarzı osilatör.

1) tlab/indicators/structure/swing_fib_abcd.py — SwingFibABCD
   Params: left, right, zigzag_method, abcd_ratios=(1.0,1.272,1.618), bc_retrace=(0.382,0.886),
   target_tol_atr, fib_levels (retracement+extension), max_active_targets.
   compute():
   - swings + label_structure → lines: ardışık swing çizgisi (X→A kırmızı düz), markers: HH/HL/
     LH/LL.
   - Her kesinleşen C için AB=CD projeksiyonları (yeşil yükseliş, kırmızı düşüş) → Level "D
     (hedef): 106.75" state pending; fiyat tol içinde ulaşınca "[TAMAM]" completed (o barda
     Signal); yeni C oluşursa eski pending invalidated.
   - Son kesinleşen swing üzerine Fibonacci retracement + extension seviyeleri (levels; start =
     kesinleşme barı; yeni swing gelince eski setin end'i konur, yeni set eklenir).
   - payload'a harmonic_unit = |A−B| ("Harmonik sayı: 13.99 TL" olarak başlıkta gösterilecek).
   - Sinyaller: abcd_target_reached, abcd_pending_near (fiyat hedefe < near_pct), fib_touch
     (0.618/0.786 gibi seçili seviyelere temas barı).
2) tlab/indicators/structure/price_structure.py — PriceStructure
   Params: pivot left/right, trendline (min_touches, tol_atr, confirm_bars, max_lines), range
   (min_bars, atr_mult), zone (band_atr, min_pivots), profile (window_bars, bins, va_pct),
   volume_ma, macd (12,26,9).
   compute():
   - trendlines: aktif ve kırılmış çizgiler (Line; label "Direnç (Temas:6)" / "Kırılım
     2026-05-08 (Temas:3)"); kırılım Signal'i kırılım barında.
   - ranges: Box'lar (gri kesikli); breakout Signal'i.
   - zones: Box'lar (sarı direnç, mavi destek; t1 = son bar, extend_right); zone_touch /
     zone_break Signal.
   - volume profile: levels POC (sarı düz), VAH/VAL; series "vp_bins"/"vp_volumes"/"vp_gauss"
     (renderer sağ panelde çizecek); poc_reclaim Signal.
   - series: volume, volume_ma, macd, macd_signal, macd_hist; osc cross markers.
   - last_state: aktif çizgi sayısı, açık kutu var mı, fiyat hangi bölgede, POC'a uzaklık.
3) İki indikatör registry'ye kaydolur; repaint_test PASS şart. Özellikle ranges (extend-only)
   ve zones (doğum barı) için kesit testleri yaz.
4) Gerçek veri smoke: TCELL 1D → SwingFibABCD çıktısında D hedefleri ve harmonic_unit; TCELL
   1D → PriceStructure'da en az 2 trendline ve 1 kutu. Sonuçları outputs/debug/*.json'a yaz
   (Faz 7'de çizeceğiz).
git commit: "faz4: yapı indikatörleri".
```

---

## 11 · FAZ 5

```
FAZ 5 GÖREVİ — Pair trading: long-only relatif momentum geçişi + backtest + çift keşfi

Referans: TCELL ↔ ISCTR. Z: -2.010 → -1.877 (Y ucuz → dönüş onaylandı) → "TCELL AL".
Başlangıç 100.000 TL, güncel 119.664 TL, +19.66%, 11 geçiş. 3 panel: normalize fiyatlar +
tutulan dönem gölgesi; portföy vs 50/50 al-tut; Z-skoru ±2 eşik ve AL etiketleri.

1) tlab/indicators/pairs/relative_momentum.py — RelativeMomentumPair
   Bu indikatör context={"x": df_x} ile ikinci sembolü alır; df = Y (TCELL), context x = ISCTR.
   Params: window (varsayılan 90), threshold k=2.0, beta_method ("one" | "rolling_ols"),
   beta_window, min_periods, execution ("close" | "next_open"), commission_bps, start_capital,
   initial_holding ("y" | "x" | "none_until_signal").
   Hesap: spread = log(Y) − β·log(X); z = (spread − rolling_mean)/rolling_std.
   Sinyal (dönüş onaylı): z[t-1] < −k and z[t] >= −k → long Y ("TCELL AL"); z[t-1] > +k and
   z[t] <= +k → long X ("ISCTR AL"). Sadece kapalı barlarla; min_periods öncesi sinyal yok.
   İki serinin index'i inner join ile hizalanır; eksik günler (bir hisse işlem görmemiş) düşürülür
   ve raporlanır.
   Çıktı: series {y_norm, x_norm, z, upper=+k, lower=−k, portfolio, buyhold_5050, holding
   (0/1)}; boxes: tutulan dönemler (Y için yeşilimsi, X için mavimsi gölge — Görsel 1 paneli 1
   ve 3); markers: "TCELL AL"/"ISCTR AL" z eğrisi üzerinde; signals: her geçiş; last_state:
   {z_today, z_yesterday, holding, signal_today: "YENİ AL SİNYALİ"|None, portfolio_value,
   net_pnl, return_pct, n_trades}.
   Ön istatistikler payload'a: corr, adf_pvalue, halflife, beta.
2) tlab/backtest/pairs_engine.py — long-only geçiş backtest'i (indikatör içinden çağrılır ama
   bağımsız da kullanılabilir). Geçiş barında tüm sermaye diğer hisseye; komisyon; al-tut 50/50
   eşit TL. Metrikler: net pnl, getiri, geçiş sayısı, max drawdown, kazanan geçiş oranı, ortalama
   tutma süresi. Metrik tablosu Görsel 4 formatında (Baslangic Sermayesi, Guncel Portfoy, Net
   Kar/Zarar, Getiri Orani, Gecis Sayisi, Son Gun Z, Onceki Gun Z, Sinyal).
3) Çift evreni: config/pairs.yaml (elle) + tlab/indicators/pairs/discovery.py: verilen sembol
   listesinde (varsayılan aynı sektör — sektör eşlemesini config/sectors_bist.yaml'a koy; bilmediğin
   sektörleri boş bırak, uydurma) tüm çiftler için corr > corr_min, adf_p < 0.05, halflife ∈
   [5, 60] filtresi → aday çift listesi (rapor).
4) Scanner uyumu: pair indikatörleri "pair" kategorisiyle registry'ye kaydolur; scanner'da
   (Faz 6) evren = çift listesi olacak; şimdilik CLI: tlab pair --y TCELL --x ISCTR --tf 1d
   → last_state ve metrik tablosunu konsola yazar, IndicatorResult JSON'unu outputs/'a kaydeder.
5) Testler: sentetik eşbütünleşik iki seri (ortak random walk + bağımsız gürültü; seed) →
   sinyaller beklenen barlarda; repaint_test PASS (context'li indikatör için repaint.py'yi
   context'i de kesecek şekilde genişlet: df ve context aynı cut'ta kesilir); backtest muhasebe
   testi (sermaye korunumu, komisyon).
git commit: "faz5: pair relatif momentum ve backtest".
```

---

## 12 · FAZ 6

```
FAZ 6 GÖREVİ — Scanner engine, gün sonu (EOD) akışı, SQLite sonuç deposu, diff ve CLI

1) tlab/scanner/results.py — SQLite (outputs/results.db) + JSON payload klasörü.
   Tablolar:
   runs(run_id, started_at, finished_at, market, timeframes, universe_size, indicators_json,
        git_sha, status)
   signals(run_id, symbol, market, timeframe, indicator, params_hash, bar_time, detected_at,
           direction, state, score, pattern_id, payload_json)  — PK (run_id, symbol, timeframe,
           indicator, pattern_id, state, bar_time)
   states(run_id, symbol, timeframe, indicator, last_state_json)
   data_quality(run_id, symbol, timeframe, status, report_json)
   BU ŞEMA DONUK: Bilanço Radar ile symbol üzerinden join edilecek; alan adlarını değiştirme.
   API: persist(run_id, results), query(...) filtreli, latest_run(market), diff(run_a, run_b)
   → yeni sinyaller, durum değişimleri (pending→active, active→confirmed, →invalidated),
   kaybolan sinyaller (olmaması gerekir; olursa repaint alarmı olarak logla!).
2) tlab/scanner/engine.py — run(universe, timeframes, indicator_names, lookback_bars=600,
   workers=cpu-1, drop_open_bar=True). Her (symbol, tf) için store.get → validate → registry'deki
   her indikatör → IndicatorResult. Pair kategorisi için evren = pairs listesi. Hata izolasyonu:
   bir indikatörün patlaması diğerlerini durdurmaz; hata results'a "error" durumu ile yazılır.
   ProcessPoolExecutor; ilerleme çubuğu; süre ölçümü indikatör başına.
3) tlab/scanner/eod.py — run_eod(market, date=None, force=False):
   takvim kontrolü → update-data (1H,1D; 4H türetilir) → data quality → engine.run → persist →
   diff(previous) → report (Faz 7'de gerçek HTML; şimdilik JSON + konsol özeti) → bildirim
   hook'u (boş fonksiyon; Telegram sonra). Aynı gün ikinci koşu: run_id aynı tarihli, önceki
   üzerine yazılır (force) veya atlanır. Log dosyası outputs/logs/eod_{date}.log.
4) tlab/cli.py komutları: tlab scan --market bist --tf 4h,1d --indicators all|liste --symbols;
   tlab eod --market bist [--date] [--force]; tlab signals --run latest --state active
   --indicator harmonic.* --tf 1d (tablo); tlab diff --a run1 --b run2; tlab list-indicators.
5) Zamanlama: README'ye cron/systemd timer örneği (18:15 Europe/Istanbul, hafta içi) ve Windows
   Görev Zamanlayıcı örneği.
6) Testler: küçük evren (5 sembol) uçtan uca; idempotentlik (aynı veriyle iki koşu → signals
   tablosu birebir aynı); diff testi (ikinci koşuda bir bar eklendiğinde sadece yeni sinyaller
   diff'te); "kaybolan sinyal" repaint alarmı testi (sahte sonuç enjekte ederek).
7) Performans: 100 sembol × 2 tf × tüm indikatörler süresini ölç, raporla; > 10 dk ise
   profiling ile en yavaş indikatörü göster.
git commit: "faz6: tarama motoru ve EOD".
```

---

## 13 · FAZ 7

```
FAZ 7 GÖREVİ — Plotly renderer (tam görsel kanıt), temalar, EOD HTML raporu

Hedef: 6 referans görselin her biri renderer ile yeniden üretilebilmeli. Renderer HESAP YAPMAZ;
yalnızca IndicatorResult primitiflerini çizer.

1) tlab/viz/renderer.py — render(result: IndicatorResult, df, theme, panels=auto) -> go.Figure
   - Ana panel: mum grafiği; Level (yatay kesikli, etiket sağda), Line (çoklu nokta, style:
     solid/dash/dot, extend_right ise son bardan sağa uzat), Box (gri kesikli konsolidasyon;
     sarı/mavi dolgulu bölge; yeşil/mavi tutma dönemi gölgesi), Polygon (yarı saydam üçgen —
     harmonik), Marker (pivot etiketleri HH/HL/LH/LL; "D: 125.42 [AKTİF]" gibi kutulu
     annotation; AL/SAT işaretleri).
   - Alt paneller: series sözlüğündeki serileri panel gruplarına göre (metadata: result.
     series_layout = {"volume": ["volume","volume_ma"], "macd": [...], "z": ["z","upper",
     "lower"]}) çiz; histogramlar için bar tipi.
   - Sağ yan panel: "vp_*" serileri varsa yatay hacim profili + VA yeşil + Gaussian sarı eğri
     (Görsel 2).
   - Pair modu: 3 satırlı düzen (normalize fiyatlar+gölge, portföy vs al-tut, z-skoru+eşik+
     etiketler) — Görsel 1. Başlık formatı: "YENİ AL SİNYALİ | TCELL AL (Y Ucuz -> Dönüş
     Onaylandı) | Z: -2.010 -> -1.877 | 26.08.2026".
   - Harmonik modu: Görsel 5/6 düzeni (Fibonacci yatayları, üçgen gölgeler, X→B kesikli,
     D etiketi).
   - Türkçe etiket sözlüğü tlab/viz/labels_tr.py.
2) tlab/viz/themes.py — "dark_terminal" (Görsel 1: siyah zemin, yeşil/turuncu) ve "light_
   analysis" (Görsel 2–6: beyaz zemin, kırmızı/yeşil mum). Renkler tek yerden.
3) tlab/viz/table.py — Görsel 4 formatında metrik tablosu (Plotly table veya HTML).
4) tlab/viz/report.py — EOD HTML raporu: özet (yeni sinyaller, durum değişimleri, indikatör
   başına sayılar), sekmeler (indikatör/tf), her sinyal satırından tekil grafiğe link (grafik
   lazy üretilir: outputs/charts/{run_id}/{symbol}_{tf}_{indicator}.html). Tek dosya, harici
   CDN plotly.js ile (dosya boyutu için).
5) CLI: tlab plot --symbol TCELL --tf 1d --indicator harmonic.pesavento [--theme] [--last-n
   300] [--open]; tlab report --run latest.
6) Kabul: TCELL 1d price_structure, TCELL 1d swing_fib_abcd, ALARK 1d harmonic.pesavento, TCELL
   -ISCTR pair grafiklerini üret; ekran görüntülerini outputs/samples/'a kaydet (kaleido ile png).
   Referans görsellerdeki her öğenin karşılığı var mı kontrol listesi olarak README'ye yaz.
git commit: "faz7: görselleştirme ve rapor".
```

---

## 14 · FAZ 2-EK
> Faz 8 ön koşulu

```
FAZ 2-EK GÖREVİ — Ek özellikler: channels, patterns_geom, hs_pattern, zones_sd, volatility, xsec
(+ Faz 1'e W1 haftalık zaman dilimi)

Önce Faz 1'e dokun: Timeframe.W1 ekle; tlab/data/resample.py'ye resample_to_w1(df_1d, market):
hafta = Pzt–Cum, kapanış Cuma (tatilse son işlem günü); henüz bitmemiş hafta is_closed=False ve
varsayılan düşürülür. Store: W1 parquet 1D'den türetilir. Test: hafta hizası, açık hafta düşme.

Sonra tlab/features/ altına, hepsi non-repaint ve saf:
1) volatility.py — atr(n), realized_vol(n), bollinger(n,k) + bandwidth, keltner, vol_zscore.
2) channels.py
   - regression_channel(df, n, k): her bar t için son n bar üzerinden log-fiyat OLS; orta, üst, alt
     (±k·std resid). Çıktı DataFrame (t bazlı, o barın kanalı). Ayrıca frozen_channel_at(t):
     sinyal anındaki kanalı Line olarak dondurmak için yardımcı (points = [t-n, t] uçları).
   - pivot_channel(df, pivots): iki onaylı swing low'dan alt çizgi + paralel üst (en yüksek high'a
     teğet). extend-only; Faz 2 trendlines ile aynı temas/kırılım mekanizması.
   - channel_position(df, channel): fiyatın kanal içi konumu 0..1.
3) patterns_geom.py — converging_lines(upper: Trendline, lower: Trendline): eğim işaretleri, eğim
   oranı, apex bar/fiyat, yakınsama testi; classify(): 'falling_wedge','rising_wedge',
   'sym_triangle','asc_triangle','desc_triangle','flag','pennant' (parametre tablosu ile).
   Her sınıflandırma, ilgili son pivotun ONAY barında verilir.
4) hs_pattern.py — find_hs(pivots, kind='tobo'|'obo', sym_tol, neck_slope_max): 5 ardışık
   alternatif pivot penceresi; sağ omuz onay barında HSPattern(l1,h1,head,h2,l3, neckline,
   target, created_idx) döner. neckline_value_at(t).
5) zones_sd.py — find_bases(df, base_max, base_atr) → baz aralıkları; find_impulses(df, k,
   impulse_atr) → patlama; make_sd_zones(...) → SDZone(kind, low, high, created_idx, base_bars,
   impulse_strength, fresh=True). update_zones(zones, df, t): test/reaction/broken geçişleri bar
   bar (extend-only; sınırlar sabit). golden_zone(swing_low, swing_high, lo=0.618, hi=0.786).
6) xsec.py — evren-geneli: rolling_alpha_beta(returns_i, returns_m, window) (OLS, t-stat),
   information_ratio, momentum_horizons(prices, [21,63,126,252], skip=21), fip(returns, n),
   rs_line(price, index), rank_pct(dict[symbol, value]). Girdi: {symbol: Series} sözlüğü.
7) Testler: her fonksiyon için birim + mini sarmalayıcı ile repaint testi; hypothesis ile
   "kesik seri sonuçları ⊆ tam seri sonuçları" özelliği (find_hs, make_sd_zones, converging_lines
   için). lint temiz.
git commit: "faz2-ek: kanal, formasyon geometrisi, OBO/TOBO, S/D bölgeleri, volatilite, xsec".
```

---

## 15 · FAZ 8A
> ch1 ekleri (Donchian/BB) dahil

```
FAZ 8A GÖREVİ — tlab/indicators/trend/breakouts.py: çoklu kırılım tarayıcısı

Tek indikatör, çok tür. Her Signal payload'ında break_type, level_value, level_age_bars,
touches, volume_ratio, body_ratio, distance_atr, quality_score, retest_state.
Türler (Bölüm 12.5 tablosu): downtrend_break, uptrend_break, range_breakout_up/down,
zone_break_up/down, hh_break, ll_break, n_week_high (26/52), ma_break (EMA50/200),
channel_break_up/down (regression veya pivot kanalı, parametre), retest_hold, false_break.
Kurallar:
- Her tür yalnızca KAPANIŞ ile ve kendi barında; confirm_bars parametresi (1 = aynı bar,
  2 = ertesi bar kapanışı da üstte → sinyal 2. barda damgalanır; detected_at buna göre).
- Hacim teyidi: volume > volume_ma(20)·vol_k (varsayılan 1.5) → payload volume_ok; sinyal
  hacim teyidi olmadan da üretilir ama quality_score düşer (tarama filtresi kullanıcıya kalır).
- downtrend_break için ek: yapı etiketi son pivotta HL olmalı (label_structure) — payload
  structure_ok.
- retest_hold: kırılımdan sonra max_retest_bars içinde low, seviyeye tol_atr içinde döner ve
  kapanış seviyenin üstünde kalır → o barda Signal (kırılım pattern_id'sine bağlı).
- false_break: kırılımdan sonra k bar içinde kapanış seviye altına dönerse o barda Signal;
  ORİJİNAL kırılım kaydı asla silinmez veya değiştirilmez (repaint testi bunu doğrular).
- Quality score: ağırlıklı toplam (hacim 0.3, seviye yaşı 0.2, temas 0.2, gövde 0.15,
  mesafe 0.15) → 0..1.
Görsel: kırılan seviye/çizgi "broken" stiliyle, kırılım mumu vurgusu, retest kutusu, etiket
"Kırılım: YUKARI | düşeni kıran | Temas:3 | Hacim ×2.1"; alt panel hacim + vol_ma.
Testler: her tür için sentetik fixture (make_zigzag + eklenen hacim), false_break sonrası
orijinal sinyalin korunduğunu doğrulayan repaint testi, confirm_bars=2'de detected_at'in
ikinci bar olduğu testi. Gerçek veri smoke: TCELL 1D'de 2026-05 civarında downtrend_break.
Külliyat ekleri (ch1 — bilgi-bankasi/teknik/kod/ch01, K2 bittiyse STRAT atıfı yap):
- donchian_break_up/down: N-bar Donchian kanalı (N=20 ve 55 ayrı kayıt); kapanış kanal
  dışında; kanal rolling max/min SADECE kapalı geçmiş barlardan (bugünün barı hariç —
  klasik lookahead tuzağı, testini yaz).
- bb_break_up/down: Bollinger(20,2) bandı dışı kapanış; ek filtre: bandwidth son N barın
  alt yüzdeliğinde (sıkışma sonrası kırılım kalitesi payload'a).
config/scans.yaml'a 'dusen_kiran' presetini ekle; tlab scan --preset dusen_kiran çalışsın.
git commit: "faz8a: kırılım tarayıcısı".
```

---

## 16 · FAZ 8C

```
FAZ 8C GÖREVİ — golden_zone.py, supply_demand.py, weekly_channel.py

1) tlab/indicators/structure/golden_zone.py — GoldenZoneIndicator(left/right, band=(0.618,0.786),
   alt_band=(0.5,0.618) opsiyonel, reaction_body_ratio=0.5, min_swing_atr).
   Son onaylı swing (low→high yükselişte; high→low düşüşte, simetrik) A onay barında bant Box
   (start = onay barı, extend_right). Signals: golden_zone_touch (low bant içinde), golden_
   zone_reaction (kapanış bant üstü + dönüş mumu), golden_zone_fail (kapanış bant altı),
   golden_zone_success (swing high aşıldı). Yeni swing onayı → eski bant end alır, yeni bant.
   last_state: bant sınırları, fiyat bant içinde mi, uzaklık (ATR), son reaksiyon tarihi.
   Görsel: altın gölgeli bant, 0.5 çizgisi, swing çizgisi, markerlar, etiket "GOLDEN ZONE
   0.618=107.2 / 0.786=104.9".
2) tlab/indicators/structure/supply_demand.py — SupplyDemandIndicator(base_max=5, base_atr=0.6,
   impulse_bars=3, impulse_atr=2.0, max_zones=12, flip=True).
   zones_sd ile bölgeler; doğum = patlama barı; test/reaction/broken geçişleri; fresh bayrağı
   ilk testte düşer; broken demand → supply flip (yeni pattern_id). Kalite = patlama gücü ×
   baz darlığı × tazelik. last_state: en yakın demand/supply, fiyat bölgede mi, distance_atr.
   Görsel: yeşil/kırmızı kutular sağa uzatılmış, etiket "DEMAND (taze) | 3.1 ATR", test
   markerları, broken bölgeler soluk.
3) tlab/indicators/trend/weekly_channel.py — ChannelIndicator(method 'regression'|'pivot',
   n=52|104|156, k=2.0, touch_tol, min_prev_touches=2, rsi_max=40; supported: W1 ve 1D).
   regression: temas sinyali o barın kanalıyla; kanal Line sinyal barında DONDURULUR
   (extend_right=False) ve ayrıca güncel kanal ayrı Line olarak (soluk vs belirgin). pivot:
   extend-only. Signals: channel_bottom_touch ("KANAL DİBİ"), channel_top_touch,
   channel_break_down/up. last_state: position_pct, slope, touches, at_bottom (pos < 15%).
   Alt panel: channel_position osilatörü.
4) Repaint testleri: bant/bölge sınırlarının sabit kaldığı, dondurulmuş kanalın değişmediği
   (regression kanalının kaymasına rağmen sinyal barındaki Line points birebir aynı).
5) scans.yaml: golden_zone, demand_taze, kanal_dibi_hafta. tlab scan --preset kanal_dibi_hafta
   --tf w1 çalışsın. Smoke: evren W1'de kanal dibi listesi; TCELL 1D golden zone grafiği.
git commit: "faz8c: golden zone, demand/supply, haftalık kanal".
```

---

## 17 · FAZ 8B
> TWYS ekleri (çift tepe/dip, broadening) dahil

```
FAZ 8B GÖREVİ — tlab/indicators/patterns/{wedge.py, head_shoulders.py, flag_pennant.py}

Ortak durum makinesi (harmonics/state.py'yi genelleştir → tlab/core/pattern_state.py):
PENDING → CONFIRMED (kırılım) → RETEST_HOLD / TARGET_REACHED; PENDING → INVALIDATED /
EXPIRED. Her geçiş kendi barında. Her pattern bir pattern_id taşır; tüm geçişler Signal listesinde.

1) wedge.py — WedgeIndicator(params: pivot left/right, min_pivots=4, min_bars, max_apex_bars,
   slope_ratio (0.3..1), tol_atr, confirm_bars, vol_k). patterns_geom.converging_lines ile
   falling_wedge / rising_wedge (+ bonus: sym/asc/desc triangle, ayrı pattern adıyla).
   PENDING: 4. pivot onay barında; CONFIRMED: kapanış çizgi dışı + confirm; hedef = max
   yükseklik projeksiyonu (Level "Hedef"); EXPIRED: apex'e %80.
   Görsel: iki çizgi apex'e kadar kesikli uzatılmış, pivotlar, apex marker, hedef, etiket
   "ALÇALAN TAKOZ [ONAY]".
2) head_shoulders.py — HeadShouldersIndicator(kind: 'tobo'|'obo'|'both', sym_tol, neck_slope_max,
   shoulder_time_ratio (0.5,2.0), confirm_bars, vol_k, target_mode 'measured').
   PENDING sağ omuz onay barında; CONFIRMED boyun kapanış kırılımı ("TOBO ONAY"); RETEST_HOLD;
   TARGET_REACHED; INVALIDATED (sağ omuz altına kapanış). payload: omuz/baş fiyat-tarihleri,
   boyun eğimi, simetri, volume_profile_ok (sağ omuzda hacim düşük, kırılımda yüksek).
   Görsel: SOL OMUZ / BAŞ / SAĞ OMUZ etiketleri, boyun çizgisi extend_right, hedef, kırılım ve
   retest markerları, hacim paneli.
3) flag_pennant.py — FlagPennantIndicator(pole_bars, pole_atr, flag_min_bars, flag_max_bars,
   flag_atr, max_retrace=0.5, confirm_bars, vol_k). Direk tespiti rolling; konsolidasyon
   flag_min_bars'a ulaşınca PENDING (kanal veya üçgen sınıflaması ile "BAYRAK"/"FLAMA");
   CONFIRMED direk yönünde kırılım; hedef = direk uzunluğu; EXPIRED flag_max_bars.
   Görsel: direk çizgisi, bayrak kanalı / flama üçgeni, kırılım, hedef.
4) Registry: wedge, triangle (bonus), head_shoulders, flag_pennant. Repaint PASS zorunlu; pattern
   sınırlarının (çizgi/boyun) pending'de sabitlendiğini test et.
5) Sentetik fixture'lar: make_zigzag ile ideal TOBO/OBO/takoz/bayrak; negatif fixture'lar
   (simetri bozuk TOBO reddi, ıraksayan çizgiler takoz değil).
6) TWYS ekleri (bilgi-bankasi/teknik/10 FORMASYON atıflarıyla; K1 çıktısındaki kuralları esas al):
   patterns/double_top_bottom.py — DoubleTopBottom(eq_tol (iki tepe/dip eşitlik toleransı,
   ORAN'dan), min_bars_between, confirm_bars, vol_k): iki onaylı pivot high (top) / low
   (bottom) + aradaki çukur/tepe = boyun; PENDING ikinci pivot onay barında; CONFIRMED boyun
   kapanış kırılımı; hedef = derinlik projeksiyonu; retest; invalidated (ikinci tepenin
   üstüne kapanış). patterns/broadening.py — Broadening: patterns_geom'a diverging_lines
   ekle (ıraksayan üst+alt çizgi, ≥4 pivot, her çizgide ≥2 temas); genişleyen formasyon
   top/bottom; kırılım ve durumlar aynı makine.
7) scans.yaml: tobo_onay, cift_tepe_dip, takoz_bayrak presetleri. Gerçek veri smoke: evren 1D'de ≥1 TOBO
   confirmed bul, tlab plot ile grafiğini üret.
git commit: "faz8b: takoz, tobo/obo, bayrak/flama".
```

---

## 18 · FAZ 8D
> KAMA + Carver EWMAC dahil

```
FAZ 8D GÖREVİ — alpha_rank.py, momentum_rank.py, ma_systems.py + scanner "universe-level"

1) Scanner: IndicatorMeta.category'ye "universe" değeri; engine, universe indikatörlerini
   (sembol sembol değil) tüm evrenin {symbol: df} sözlüğü + endeks df'si (context) ile TEK
   çağrıda çalıştırır; sonuç sembol başına IndicatorResult'a ayrıştırılır (rank payload'ı ile).
   Endeks verisi: XU100 ve NDX (data katmanına ekle; yfinance sembolleri XU100.IS, ^NDX).
2) tlab/indicators/momentum/alpha_rank.py — AlphaRank(windows=(60,120,250), min_liquidity_try,
   top_pct=10). rolling_alpha_beta → α_ann, t_stat, IR, β, persistence; skor ve rank_pct.
   Signals: alpha_entry (rank_pct ≤ top_pct'e ilk giriş barı), alpha_exit. Görsel tekil: 4 panel
   (hisse vs endeks, α+t-stat bandı, β, kümülatif ε). Görsel evren: α–β saçılım (renderer'a
   scatter modu; series "xsec_alpha","xsec_beta","xsec_liq").
3) tlab/indicators/momentum/momentum_rank.py — MomentumRank(horizons=(21,63,126,252), skip=21,
   fip_n=126, vol_adjust=True, top_pct=10). momentum_horizons, rs_line + eğim t-stat, FIP,
   trend_score (close>EMA20>EMA50>EMA200 + eğimler), vol-ayarlı mom; skor; rank. Signals:
   momentum_top_entry/exit, rs_breakout (RS 52h zirve). Görsel: fiyat+EMA'lar, RS+regresyon,
   ufuk çubukları, FIP. Evren: sektör × ufuk ısı haritası (series olarak; renderer heatmap).
4) tlab/indicators/trend/ma_systems.py — MASystems(periods=(8,21,55,200), type ema): kesişimler,
   sıralama durumu ("above_all", "bull_stack"...), MA bant genişliği sıkışma→genişleme.
5) Kaynak ekleri:
   - features/ma.py'ye KAMA (Kaufman adaptive MA; efficiency ratio penceresi, fast/slow SC)
     — ch1 STRAT atfı; ma_systems'a kama seçeneği.
   - trend/ewmac.py — Carver EWMAC kuralı: ewmac(fast, slow) = EMA_f − EMA_s, vol
     normalizasyonu (fiyat vol'üne böl), forecast scalar ile −20..+20 ölçeğine; parametre
     çiftleri ve scalar değerleri bilgi-bankasi/teknik/11 FORMÜL atıflarıyla (K3 bitmediyse
     Carver standart çiftlerini kullan ve TODO bırak). Çıktı: series["ewmac_f_s"] forecast
     serileri + işaret değişim sinyalleri. Bu, Faz 10 forecast katmanının ilk gerçek üreticisi.
6) Testler: xsec fonksiyonları sentetik evrende (bilinen alfa/momentum ile üretilmiş 20
   sembol) doğru sıralama; universe-level repaint testi (evren sözlüğünün her df'si aynı cut'ta
   kesilir; rank'lar kesik ⊆ tam).
7) scans.yaml: alpha_top, momentum_top. tlab scan --preset momentum_top.
CLAUDE.md güncelle. git commit: "faz8d: alpha, momentum, ma sistemleri".
```

---

## 19 · K3 — Carver çıkarımı + Faz 10 spec (Faz 8 sırasında paralel)

```
GÖREV K3 — Systematic Trading (Carver 2015) bilgi çıkarımı → Faz 10 hammaddesi

kitap-okuyucu agent'ı, teknik mod. Girdi: kitaplar/teknik/Systematic_Trading_...pdf.
Çıktı: bilgi-bankasi/teknik/11_carver_systematic.md.

Odak sırası (kitabın tamamını tara ama şunları FORMÜL-xx olarak hesaplanabilir çıkar):
1) Forecast kavramı: −20..+20 ölçeği, ortalama mutlak forecast 10, forecast scalar
   hesabı, capping. Bizim Signal.score (0..1) → forecast çevirisi için öneri notu.
2) Volatilite hedefleme: yıllık cash vol target, instrument risk (fiyat vol ölçümü),
   pozisyon = f(sermaye, target, instrument risk, forecast) zinciri — TL cinsinden lot
   örneğiyle.
3) Forecast ağırlıkları + forecast diversification multiplier; instrument weights +
   instrument diversification multiplier; korelasyon temelli ağırlık ("handcrafting"
   yöntemi dahil — tablolarıyla).
4) Fitting bölümü → DISIPLIN-xx serisi: overfitting kaynakları, ideas-first ilkesi,
   in-sample/out-of-sample, kaç parametre/ne kadar veri, "expert fitting" tablosu.
5) EWMAC kuralı (parametre çiftleri, scalar'ları) ve carry — ORAN/FORMÜL olarak.
6) Ulaşılabilir Sharpe beklentileri, hız/turnover-maliyet ilişkisi, speed limit —
   DISIPLIN-xx.
7) Dosya sonuna "Faz 10 spec taslağı için girdi listesi": teknik-analiz-uzmani'nın
   spec yazarken kullanacağı FORMÜL/DISIPLIN kodlarının haritası.
Ardından teknik-analiz-uzmani ile docs/spec/tlab_10_portfolio.md taslağını yazdır:
tlab/portfolio/{forecast.py, sizing.py, allocation.py, risk.py} + backtest/metrics.py
genişletmesi (ch11 StrategyEvaluator çerçevesi + ch10 vol targeting/drawdown kontrolü,
hepsi shift(1)/kapalı-bar disipliniyle), parametre tabloları, kabul kriterleri.
git commit: "k3: Carver çıkarımı + Faz 10 spec taslağı".
```

---

## 20 · FAZ 8E
> GARCH eki dahil

```
FAZ 8E GÖREVİ — vol_harvest.py, confluence.py, scans.yaml entegrasyonu, EOD sekmeleri

0) features/volatility.py'ye garch11_forecast(returns, window, refit_stride) — arch paketi;
   her noktada YALNIZCA geçmiş pencereyle fit (refit maliyetliyse stride ile seyrelt, aradaki
   barlarda son fit parametreleriyle koşullu vol); repaint testi zorunlu. vol_harvest'in
   vol_regime_filter'ı ve Faz 10 sizing bu tahmini kullanabilir (parametre: "ewma"|"garch").
   STRAT atfı: bilgi-bankasi/teknik/kod/ch07.
1) tlab/indicators/pairs/vol_harvest.py — VolHarvestPair(window, weight_fn 'linear'|'grid',
   slope=0.15, w_min=0.1, w_max=0.9, grid_levels=(1,1.5,2,2.5), grid_step=0.125,
   rebalance_band=0.05, vol_regime_filter=True, adf_pause_p=0.10, halflife_max=60,
   commission_bps, start_capital).
   z (Faz 5 ile ortak), w_target(z), rebalans tetiği, işlem kapanışta; harvest serisi =
   portföy − statik başlangıç ağırlıklı al-tut; paused/resumed durumları. backtest/pairs_engine
   .py'ye mode="weights" ekle (kesirli ağırlık, komisyon, muhasebe testi).
   Görsel: Görsel 1'in 3 paneli + 4. panel w_Y adım grafiği ve rebalans markerları; 2. panelde
   harvest serisi; başlık "Hasat: +X TL (%y) | Rebalans: n | Durum: aktif/paused".
   Metrik tablosu (Görsel 4 formatı) + harvest satırları.
2) tlab/scanner/confluence.py — build_reversal_map(symbol, tf, run_id): results.db'den
   supply_demand, golden_zone, price_structure (zones, POC/VAH/VAL), weekly_channel (alt bant,
   W1'den 1D'ye taşınır), harmonic.* (active PRZ), swing_fib_abcd (pending D) seviyelerini çek;
   fiyat ekseni ATR/10 kovalara böl; ağırlıklar (kaynak tipi, tazelik, tf: W1 1.5 / 1D 1.0 /
   4H 0.6); destek yoğunluk profili; bottom_probability (yalnızca sıralama amaçlı, 0..1);
   "dönüş kaynağı" açıklaması: son onaylı swing low'un hangi kaynaklara denk geldiği (detected_at
   = swing onay barı). Çıktı IndicatorResult (indicator="confluence") → results.db'ye yazılır.
   Görsel: renderer mode="reversal_map": katmanlı bölgeler (opaklık = ağırlık), sağ panelde
   destek yoğunluk profili, dönüş açıklama kutusu, "DİPTE OLASI: 0.72 | 4 kaynak" etiketi.
3) config/scans.yaml tam liste (Bölüm 12.12) + tlab scan --preset <ad>; preset filtreleri
   payload/last_state üzerinde güvenli bir ifade değerlendirici ile (eval YOK; basit
   karşılaştırma dilbilgisi yaz veya pandas.query kullan).
4) EOD raporu: her preset ayrı sekme; her satırda tekil grafiğe link; "Dipte olası" sekmesi
   reversal_map grafiklerine link.
5) Testler: harvest muhasebe (ağırlık toplamı 1, sermaye korunumu), rebalans band testi,
   paused geçişi; confluence'ta ağırlık toplamları ve kova hizası; preset filtre dilbilgisi.
6) Performans ölçümü: tam evren × (4H,1D,W1) × tüm registry; 15 dk üstündeyse en yavaş 3
   indikatörü profil et.
git commit: "faz8e: vol harvest, dönüş haritası, tarama presetleri".
```

---

## 21 · FAZ 10 — Sinyalden Portföye (K3 spec onayı ön koşul)

```
FAZ 10 GÖREVİ — tlab/portfolio: forecast, boyutlama, birleşim, risk + metrics genişletmesi
[PROJE BAĞLAMI bloğunu yapıştır] + docs/spec/tlab_10_portfolio.md'yi OKU ve ona uy.

1) portfolio/forecast.py — score_to_forecast(signals, method) → −20..+20; indikatör başına
   forecast scalar kalibrasyonu (geçmiş dağılımdan, rolling, non-repaint); capping.
   (FORMÜL atıfları: bilgi-bankasi/teknik/11/...)
2) portfolio/combine.py — aynı sembolde çoklu indikatör forecast'lerinin ağırlıklı
   birleşimi + forecast diversification multiplier (korelasyon rolling pencereden);
   Faz 8E confluence ile ilişkiyi belgele: confluence = seviye-uzamsal kanıt,
   combine = forecast-zamansal birleşim; ikisi ayrı kalır.
3) portfolio/sizing.py — vol targeting pozisyonu: sermaye, yıllık hedef vol, instrument
   risk (EWMA vol), forecast → önerilen lot (BIST lot=1 tam sayı, min emir tutarı
   parametre); turnover tahmini.
4) portfolio/risk.py — ch10 uyarlaması (yeniden yazım): vol targeting overlay, rejim
   çarpanları (girdi: bizim indikatörlerimizden — endeks EMA200 altı, endeks ATR yüzdelik;
   VIX yok), drawdown kontrolü. HEPSİ shift(1)/kapalı-bar disipliniyle; repaint testi
   overlay'ler için de (seri sarmalayıcıyla) yazılır.
5) backtest/metrics.py genişletme — ch11 çerçevesi: Sharpe (rf parametre), Calmar,
   skew/kurtosis, DD derinlik+süre (açık episod dahil), win rate, profit factor,
   alpha/beta/TE/IR (endekse göre), rolling metrikler. pairs_engine ve gelecekteki tüm
   backtestler bunu kullanır.
6) CLI: tlab portfolio --run latest → EOD sinyallerinden forecast+boyut önerisi tablosu
   (rapora sekme). UYARI metni sabit: öneri niteliğinde, yatırım tavsiyesi değildir.
7) Testler: forecast ölçek özellikleri (ortalama |f|≈10 kalibrasyonu sentetikte),
   multiplier sınırları, sizing muhasebesi, overlay'lerde shift(1) doğrulaması (bir barlık
   kayma testi: t günü çarpanı t+1 getirisine uygulanıyor), metrics bilinen-değer testleri.
git commit: "faz10: sinyalden portföye (forecast, sizing, birleşim, risk, metrics)".
```

---

## 22 · FAZ 9 — API + entegrasyonlar (PEAD dahil, en son)

```
FAZ 9 GÖREVİ — Arayüzden bağımsız API yüzeyi ve dış entegrasyon köprü noktaları

1) tlab/api.py — saf Python API (ileride Streamlit/FastAPI/masaüstü bunu çağıracak):
   list_indicators(), scan(...), get_signals(filters), get_result(symbol, tf, indicator, run),
   plot(...)-> Figure|HTML, pair(...). Hiçbir CLI/print yok; sadece nesne döner.
2) İsteğe bağlı ince FastAPI katmanı (tlab/server.py): aynı fonksiyonları JSON/HTML olarak
   sunar; Bilanço Radar'ın HTML dashboard'u bunu iframe/fetch ile tüketebilir.
3) Bilanço Radar birleşme şeması: tlab/integration/bilanco_radar.py — Bilanço Radar skor
   tablosunu (kolonlarını sen vereceksin; şimdilik symbol, market, score, sector, updated_at
   varsay) results.db'deki signals ile symbol üzerinden join eden "combined_view" fonksiyonu
   ve örnek sorgu: "temel skor > 70 ve son EOD'de aktif harmonik veya trendline break".
4) TradingView köprüsü (sadece tasarım + iskelet): tlab/integration/tradingview.py — (a)
   TradingView CSV export'unu csv_provider ile okuma (kolon eşlemesi), (b) IndicatorResult'ı
   Pine Script "plot/label/box" çıktısına dönüştüren export (bizim hesabımızı TV grafiğinde
   overlay olarak görmek için: seviyeler/çizgiler statik Pine kodu olarak üretilir). Gerçek
   masaüstü otomasyonu bu fazın dışı.
5) Fintables köprüsü (iskelet): tlab/integration/fintables.py — provider arayüzü + kimlik
   doğrulama placeholder; gerçek uç noktalar sonra.
6) tlab/integration/pead.py — Bilanço Sonrası Sürüklenme (PEAD) köprüsü (ch6 STRAT atfı):
   Girdi: Bilanço Radar KAP bilanço takvimi (kesinleşen tarihler + duyuru zamanı) ve bilanço
   skoru değişimi. Olay barı = duyuru SONRASI ilk seans (duyuru seans içindeyse aynı gün
   kapanışı, sonrasıysa ertesi gün — duyuru zaman damgasıyla, non-repaint). Sürpriz vekili:
   skor değişimi ve/veya net kâr YoY sapması (temel-analiz-uzmani ile ortak spec:
   docs/spec/pead_ortak.md). Sinyal: olay+1 barında sürpriz yönünde, N bar tutma; CAR ölçümü
   backtest/metrics ile. Tarama: "bilanço sonrası izleme listesi" preseti.
7) Dokümantasyon: docs/ARCHITECTURE.md (katmanlar, non-repaint sözleşmesi, ekol tabloları),
   docs/ADDING_AN_INDICATOR.md (adım adım: dosya, params, compute, testler, repaint, register,
   plot), docs/EOD.md.
CLAUDE.md güncelle (proje tamamlanma durumu). git commit: "faz9: api ve entegrasyon iskeleti".
```


---

## Kapanış kontrol listesi (tüm sıra bittiğinde)
1. `tlab list-indicators` → registry'de tüm modüller, hepsi repaint PASS.
2. `tlab eod --market bist` uçtan uca; rapor tüm preset sekmeleriyle açılıyor.
3. CLAUDE.md, bilgi-bankasi/teknik/_ilerleme.md ve docs/spec güncel; her kaynak-kaynaklı
   kural kodda atıflı (izlenebilirlik zinciri: kitap → bilgi bankası → spec → kod → test).
4. Görsel doğrulama: 6 referans görselin yeniden üretimi outputs/samples/ altında.
