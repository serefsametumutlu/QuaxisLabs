# TEKNİK LAB — Teknik Analiz / İndikatör Laboratuvarı
## Proje Yol Haritası, Mimari Tasarım ve Aşamalı Uygulama Promptları

Tarih: 26.08.2026
Kapsam: BIST (öncelik) + NASDAQ, 4 saatlik ve Günlük zaman dilimleri, non-repainting tarama motoru
Kardeş proje: Bilanço Radar (temel analiz) — ileride tek uygulamada birleşecek

---

## 0. Bu belgeyi nasıl kullanmalısın

Belge üç katmandan oluşur:

1. **Bölüm 1–5:** Ne kuruyoruz, neden bu şekilde kuruyoruz (mimari kararlar ve gerekçeleri). Bunu bir kez dikkatle oku; her promptta bu kararlar tekrar geçer.
2. **Bölüm 6:** Verdiğin altı görselin tersine mühendisliği — her grafiğin arkasındaki matematik ve bunu non-repainting olarak nasıl yeniden kuracağımız.
3. **Bölüm 7–8:** Faz planı ve her faz için Claude Code (Sonnet) terminal promptları. Promptları **sırayla**, birini bitirip kabul kriterlerini doğrulamadan diğerine geçmeden ver. Her prompt, önceki fazın ürettiği dosyalara referans verir.

Promptların başındaki `PROJE BAĞLAMI` bloğunu her seferinde aynen kopyala; Sonnet'in oturumlar arası hafızası yoktur, tekrar okumalı.

---

## 1. Vizyon ve hedef sistem

Kurulacak sistem bir "indikatör tarayıcı" değil, **doğrulanabilir sinyal üreten bir araştırma altyapısı**dır. Beş temel yeteneği olacak:

| Yetenek | Açıklama |
|---|---|
| İndikatör kütüphanesi | Python'da, ortak arayüze uyan modüller. Her modül sinyal + görsel primitifler (çizgi, kutu, seviye, etiket) üretir. |
| Çoklu zaman dilimi tarama | Tüm evren, 4H ve 1D'de aynı koşuda taranır. Her sonuç (sembol, timeframe, indikatör, bar zamanı) ile anahtarlanır. |
| Gün sonu (EOD) koşusu | Seans kapanışından sonra veri güncelle → tara → sonuçları kalıcı yaz → rapor üret. Manuel de tetiklenebilir. |
| Tekil hisse görselleştirme | Bir sembol + bir indikatör seç, o indikatörün ürettiği her şey grafikte görünsün (Plotly, interaktif HTML). |
| Repaint yasağı ve kanıtı | Her indikatör otomatik "repaint testi"nden geçmeden tarayıcıya kayıt olamaz. |

İlk içerik hedefleri (senin görsellerine birebir karşılık gelen modüller):

- **Harmonik formasyonlar** — 7 ekol, izole kural setleri (Carney, Pesavento, Gilmore, Oglesbee/Cypher, Kerkez/Nen Star, Beck/Navarro 200, 5-0)
- **Swing yapısı + Fibonacci + AB=CD** (Görsel 3)
- **Fiyat yapısı: trend çizgileri, kırılımlar, temas sayısı, konsolidasyon kutuları, destek/direnç bölgeleri, hacim profili + Gaussian fit, hacim MA, osilatör** (Görsel 2)
- **İkili hisse relatif momentum / istatistiksel arbitraj (pair trading)** — Z-skoru, dönüş onayı, long-only geçiş, portföy backtest (Görsel 1 ve 4)
- **Kelebek / XABCD bearish-bullish tarama ekranı**, X→B trend çizgisi kırılımı, D noktası AKTİF/TAMAMLANDI durumu (Görsel 5 ve 6)
- **Rev.2 ile eklenenler (Bölüm 12):** Arbitraj volatilite harvesti, Alpha hisseleri, Momentum hisseleri, haftalık kanal dibi teması, düşeni kıran + çoklu kırılım tarayıcısı, Takoz, TOBO/OBO, Bayrak/Flama, Golden Zone, Demand/Supply Zone, "dip/dönüş haritası"
- Sonrasında: hareketli ortalama sistemleri ve senin özgün fikirlerin

---

## 2. Vazgeçilmez tasarım kuralları

### 2.1 Non-repainting sözleşmesi (müzakereye kapalı)

Tanım: `signal(t)` değeri, yalnızca `t` ve öncesindeki barların verisiyle hesaplanır ve `t` sonrasında hiçbir zaman değişmez.

Bunu bir cümleyle söylemek kolay, kodda kaçak yapmadan uygulamak zor. Sistemde üç mekanizmayla garanti altına alacağız:

**(a) Zaman damgası kuralı.** Bir sinyal, bilginin *elde edildiği* barın tarihini taşır; olayın *gerçekleştiği* barın değil. Örnek: 5 sağ bar onaylı bir swing high, tepe barında değil, onay barında (tepe + 5) "bilinir" hale gelir. Sinyal tarihi = onay barı. Grafikte tepe noktasına etiket koyabiliriz ama tarama kaydında `detected_at = onay barı`, `pivot_at = tepe barı` iki ayrı alan olarak tutulur.

**(b) Walk-forward eşitlik testi (otomatik).** Her indikatör için test altyapısı şunu yapar: Tam seriyi al, `T` uzunluğunda hesapla, sonuçları sakla. Sonra seriyi `t = T-1, T-2, ..., T-k` noktalarında kes, her kesikte yeniden hesapla. Kesik seride üretilen her sinyal, tam seride **aynı bar, aynı yön, aynı seviye** ile bulunmak zorundadır. Bir tanesi bile farklıysa indikatör "REPAINT" damgası yer ve registry'e kaydedilmez. Bu test CI'da her commit'te koşar.

**(c) Yasak API listesi.** İndikatör kodunda `df.shift(-n)`, `center=True` rolling, `argrelextrema` ile ortadan pivot alıp o barı sinyal barı yapma, `scipy.signal.find_peaks` sonucunu doğrudan sinyal barına yazma, geleceğe bakan interpolasyon **yasak**. Lint benzeri bir statik kontrol (`ast` ile) bunları arar ve test aşamasında hata verir.

Pivot tabanlı her şey (harmonikler dahil) şu şekilde çalışır:
- Pivotlar `left=N, right=M` parametresiyle onaylanır; pivot `i` barında oluşur, `i+M` barında "bilinir".
- Harmonik XABC yapısı, C pivotu onaylanınca **PENDING** olur ve D için PRZ (Potansiyel Dönüş Bölgesi) **ileriye projeksiyon** olarak hesaplanır.
- D noktası **pivot beklenmeden**, fiyat PRZ'ye canlı olarak girdiği barda **ACTIVE** olur (sinyal barı = PRZ'ye ilk giriş barı). Bu tam da Görsel 5'teki `D: 125.42 [AKTIF]` mantığıdır.
- Sonraki barlarda PRZ'den dönüş gerçekleşir ve X→B veya B→C trend çizgisi kırılırsa **CONFIRMED**; PRZ'nin ötesine tolerans dışı geçilirse **INVALIDATED**. Her durum geçişi kendi barında damgalanır, geriye yazılmaz.

### 2.2 Katman ayrımı

```
Veri  →  Özellik (swing, fib, pivot)  →  İndikatör  →  Tarayıcı  →  Depo  →  Görselleştirme / Rapor / (ileride) App
```

Her ok tek yönlüdür. İndikatörler veri kaynağını bilmez (sadece standart OHLCV DataFrame alır). Tarayıcı indikatörün iç yapısını bilmez (sadece `IndicatorResult` alır). Görselleştirme hesap yapmaz (sadece primitifleri çizer). Böylece arayüz kararını (Streamlit / web / masaüstü) gerçekten erteleyebiliyorsun: app ne olursa olsun depo + primitifleri okuyacak.

### 2.3 Deterministiklik

Aynı veri + aynı parametre = bit-bit aynı sonuç. Parametreler `dataclass` olarak açık; global durum yok; `random` yok. Sonuç kayıtları parametre hash'i taşır.

---

## 3. Depo yapısı

```
teknik_lab/
├── pyproject.toml
├── README.md
├── config/
│   ├── settings.yaml            # veri kaynakları, evren dosyaları, saat dilimi, yollar
│   ├── universe_bist.txt        # semboller (BIST)
│   ├── universe_nasdaq.txt
│   └── pairs.yaml               # arbitraj çiftleri (TCELL-ISCTR, ...)
├── tlab/                        # ana paket
│   ├── core/
│   │   ├── types.py             # OHLCV şeması, Timeframe enum, Signal, Level, Line, Box, Label, IndicatorResult
│   │   ├── indicator.py         # BaseIndicator (soyut arayüz), IndicatorMeta, registry
│   │   ├── params.py            # parametre dataclass'ları ve hash
│   │   └── errors.py
│   ├── data/
│   │   ├── providers/           # yfinance, csv, (ileride) fintables, tradingview export
│   │   ├── store.py             # parquet cache: data/ohlcv/{market}/{symbol}/{tf}.parquet
│   │   ├── resample.py          # 1h→4h (BIST seans saatlerine hizalı), dolgular
│   │   └── calendar.py          # BIST / NASDAQ seans takvimi, tatiller
│   ├── features/                # indikatörlerin paylaştığı saf fonksiyonlar (non-repaint)
│   │   ├── swings.py            # onaylı pivotlar, HH/HL/LH/LL etiketleme (onay barı ile)
│   │   ├── fibonacci.py         # retracement, extension, projection
│   │   ├── trendlines.py        # iki pivotlu çizgi, temas sayısı, kırılım tespiti
│   │   ├── ranges.py            # konsolidasyon kutuları
│   │   ├── volume_profile.py    # fiyat-hacim histogramı, POC/VA, Gaussian fit
│   │   ├── zones.py             # destek/direnç bölgeleri (kümeleme)
│   │   ├── stats.py             # z-skor, hedge ratio, half-life, ADF
│   │   └── ma.py, oscillators.py
│   ├── indicators/
│   │   ├── harmonics/
│   │   │   ├── geometry.py      # XABCD aday üretimi (ortak)
│   │   │   ├── prz.py           # PRZ hesaplama (ortak)
│   │   │   ├── state.py         # PENDING/ACTIVE/CONFIRMED/INVALIDATED durum makinesi
│   │   │   ├── schools/
│   │   │   │   ├── base.py      # HarmonicSchool soyut sınıfı
│   │   │   │   ├── carney.py
│   │   │   │   ├── pesavento.py
│   │   │   │   ├── gilmore.py   # zaman harmonikleri
│   │   │   │   ├── oglesbee_cypher.py
│   │   │   │   ├── kerkez_nenstar.py
│   │   │   │   ├── beck_navarro200.py
│   │   │   │   └── five_zero.py
│   │   │   └── scanner_indicator.py   # HarmonicIndicator(school=...)
│   │   ├── structure/
│   │   │   ├── swing_fib_abcd.py       # Görsel 3
│   │   │   └── price_structure.py      # Görsel 2 (trendline, box, zone, profile)
│   │   ├── pairs/
│   │   │   └── relative_momentum.py    # Görsel 1 & 4
│   │   ├── trend/ (MA sistemleri, düşen trend kırılımı)
│   │   └── momentum/
│   ├── scanner/
│   │   ├── engine.py            # evren × timeframe × indikatör çarpımı, paralel koşu
│   │   ├── eod.py               # gün sonu akışı (update → scan → persist → report)
│   │   └── results.py           # SQLite/parquet sonuç deposu, sorgu API'si
│   ├── backtest/
│   │   ├── pairs_engine.py      # long-only geçiş backtest'i
│   │   └── metrics.py
│   ├── viz/
│   │   ├── renderer.py          # IndicatorResult → Plotly figure (primitif çizici)
│   │   ├── themes.py            # koyu tema (Görsel 1 stili) / açık tema (Görsel 2-6 stili)
│   │   └── report.py            # EOD HTML raporu
│   ├── testing/
│   │   ├── repaint.py           # walk-forward eşitlik testi
│   │   ├── lint_lookahead.py    # yasak API taraması
│   │   └── fixtures.py          # sentetik seriler (bilinen pivotlar, bilinen harmonikler)
│   └── cli.py                   # typer: update-data, scan, eod, plot, repaint-test, list
├── tests/
├── data/                        # git dışı
└── outputs/                     # tarama sonuçları, grafikler, raporlar (git dışı)
```

Bilanço Radar ile birleşme için kritik nokta: `tlab/scanner/results.py` içindeki sonuç şeması (`symbol, market, timeframe, indicator, params_hash, bar_time, detected_at, direction, state, score, payload_json`) ileride temel analiz skorlarıyla `symbol` üzerinden join edilecek. Bu şemayı Faz 1'de dondurup değiştirmemeye çalış.

---

## 4. Çekirdek arayüz (tüm indikatörlerin uyacağı sözleşme)

```python
# tlab/core/types.py (özet)
class Timeframe(str, Enum): H4 = "4H"; D1 = "1D"

@dataclass(frozen=True)
class Level:   price: float; label: str; style: str; start: datetime|None; end: datetime|None
@dataclass(frozen=True)
class Line:    points: list[tuple[datetime, float]]; label: str; style: str; extend_right: bool
@dataclass(frozen=True)
class Box:     t0: datetime; t1: datetime; low: float; high: float; label: str; style: str
@dataclass(frozen=True)
class Marker:  t: datetime; price: float; text: str; kind: str   # "pivot_high", "signal_buy", ...
@dataclass(frozen=True)
class Signal:
    bar_time: datetime        # sinyalin ait olduğu bar
    detected_at: datetime     # bilginin elde edildiği bar (>= bar_time; genelde eşit)
    direction: str            # "long" | "short" | "neutral"
    state: str                # "pending" | "active" | "confirmed" | "invalidated" | "completed"
    score: float              # 0..1, indikatörün kendi kalite ölçüsü
    payload: dict             # ekol adı, oranlar, PRZ sınırları, z-skor, vb.

@dataclass
class IndicatorResult:
    indicator: str; version: str; params_hash: str
    symbol: str; timeframe: Timeframe
    signals: list[Signal]
    levels: list[Level]; lines: list[Line]; boxes: list[Box]; markers: list[Marker]
    series: dict[str, pd.Series]      # alt panel serileri (z-skor, osilatör, ...)
    last_state: dict                  # taramada "bugün ne durumda" özeti

# tlab/core/indicator.py
class BaseIndicator(ABC):
    meta: IndicatorMeta   # name, version, supported_timeframes, category, description
    params: BaseParams
    @abstractmethod
    def compute(self, df: pd.DataFrame, context: dict|None = None) -> IndicatorResult: ...
    # df: DatetimeIndex (tz-aware), kolonlar open, high, low, close, volume — sıkı doğrulanır
    # context: pair indikatörleri için ikinci sembol DataFrame'i gibi ek girdi
```

`registry.register(indicator_cls)` yalnızca `repaint_test(indicator_cls)` geçtiyse kabul eder. Tarayıcı registry'den okur; registry dışında indikatör çalıştırılamaz.

---

## 5. Gün sonu (EOD) tarama akışı

```
[18:15 TR / seans sonrası]  (cron / manuel: tlab eod --market bist)
  1. calendar.is_trading_day(today)?  değilse çık
  2. data.update(universe, tfs=[1H,1D])         # artımlı; 1H çekilir, 4H resample edilir
  3. data.validate()                            # boşluk, sıfır hacim, split/temettü düzeltme kontrolü
  4. scanner.run(universe × [4H,1D] × registry)  # ProcessPool; her (sembol,tf) için tüm indikatörler
  5. results.persist(run_id, ...)               # idempotent: aynı gün yeniden koşarsa üzerine yazar
  6. results.diff(run_id, previous_run)         # YENİ sinyaller, durum değişimleri (pending→active vb.)
  7. viz.report(run_id)                         # outputs/reports/2026-08-26.html + JSON
  8. (isteğe bağlı) bildirim: Telegram/e-posta
```

Önemli kurgu kararları:

- **4H bar hizalaması BIST'e özel:** BIST seansı 10:00–18:00 (tek seans); 4H barlar 10:00–14:00 ve 14:00–18:00 olarak sabit hizalanır, UTC'ye göre kaymaz. NASDAQ için 09:30 hizalı 4H. Bunu `resample.py` market parametresiyle çözer.
- **"Son bar kapalı mı?" kontrolü:** EOD koşusunda son bar kapalıdır. Gün içi manuel koşuda son bar açıksa tarayıcı onu **dışlar** (`drop_open_bar=True`); açık barla sinyal üretmek repaint'in ta kendisidir.
- **Artımlı hesap değil, tam yeniden hesap:** İndikatörler her koşuda tüm seriyi (son N bar, örn. 600) yeniden hesaplar. Bu basit, deterministik ve repaint testiyle tutarlı. Performans ProcessPool ile çözülür (500 sembol × 2 tf × 15 indikatör dakikalar mertebesinde).
- **Sonuç deposu SQLite** (tek dosya, sorgulanabilir, Bilanço Radar ile join kolay) + ham `IndicatorResult` JSON'ları parquet/json olarak yanında.

---

## 6. Görsellerin tersine mühendisliği

Her görsel için: ne görüyoruz → hangi matematik → non-repaint olarak nasıl kurulur → hangi modül.

### 6.1 Görsel 1 + Görsel 4 — Long-only Relatif Momentum Geçişi (TCELL ↔ ISCTR)

**Görülen:** Üç panel. (1) İki hissenin 100'e normalize fiyatı + hangi dönemde hangisinin tutulduğu gölgeli. (2) Portföy değeri: strateji (yeşil) vs 50/50 al-tut (gri), başlangıç 100.000 TL, net +19.664 TL, 11 geçiş. (3) Z-skoru, ±2 eşikleri, eşiği aşıp geri dönünce "AL" etiketi (dönüş onayı). Başlıkta `Z: -2.010 → -1.877`, yani önceki gün eşiğin altındaydı, bugün eşiğin içine döndü → "YENİ AL SİNYALİ".

**Matematik:**
- `spread_t = log(P_Y,t) − β·log(P_X,t)` — β en basit halde 1 (log-oran), gelişmiş halde rolling OLS hedge ratio.
- `z_t = (spread_t − mean(spread, w)) / std(spread, w)`; `w` tipik 60–120 gün. Rolling → doğal olarak non-repaint.
- **Dönüş onaylı kural:** `z_{t-1} < −k` ve `z_t ≥ −k` → Y ucuz ve toparlıyor → **Y'ye geç** (TCELL AL). `z_{t-1} > +k` ve `z_t ≤ +k` → **X'e geç** (ISCTR AL). Long-only: her an tam olarak bir hisse tutuluyor. Görselde k = 2.0.
- Backtest: geçiş barının kapanışında (veya ertesi açılışta — parametre) tüm portföy diğer hisseye geçer; komisyon parametre; al-tut kıyası 50/50 başlangıçtan.
- Ön kontrol (raporda göster, kural değil): eşbütünleşme (Engle-Granger/ADF), spread half-life, korelasyon.

**Non-repaint notu:** Rolling pencere ileriye bakmaz; sinyal `t` barında `z_{t-1}` ve `z_t` ile kesinleşir. Dikkat edilecek tek tuzak: pencereyi tüm seri üzerinden "expanding" değil, sabit rolling tutmak ve `min_periods` altında sinyal üretmemek.

**Modül:** `indicators/pairs/relative_momentum.py` + `backtest/pairs_engine.py`. Tarama modu: `pairs.yaml`'daki tüm çiftler + isteğe bağlı otomatik çift keşfi (aynı sektör, korelasyon > 0.7, ADF p < 0.05).

### 6.2 Görsel 2 — Fiyat Yapısı Paneli (trend çizgileri, kutular, bölgeler, hacim profili, osilatör)

**Görülen:**
- Turuncu: tepeden (HH) inen uzun vadeli direnç trend çizgisi, `Kırılım 2026-05-08 (Temas:3)` — 3 temastan sonra yukarı kırılmış.
- Kırmızı kesikli: LH'lerden inen ikinci direnç, `Direnç (Temas:6)`, hâlâ aktif.
- Gri kesikli kutular: konsolidasyon (range) bölgeleri; birbirini izleyen, bazen örtüşen.
- Sarı ve mavi bantlar: direnç ve destek bölgeleri (pivot kümeleri).
- Mavi kesikli yatay: en son referans seviyesi; sarı düz: hacim profili POC'u.
- Sağda: fiyat-hacim histogramı, yeşil = değer alanı (VA), sarı Gaussian fit.
- Alt: hacim + hacim MA; en altta MACD tarzı osilatör, histogram ve sinyal okları.
- HH/HL/LH/LL etiketleri.

**Matematik ve non-repaint kurgusu:**
- **Pivotlar:** `swings.py`, `left=L, right=R` onay. Etiket (HH/HL/LH/LL) onay barında.
- **Trend çizgileri:** İki onaylı pivot high'dan geçen çizgi; sonraki barlarda `high` çizgiye `tol` (ATR × katsayı) içinde yaklaşırsa "temas" sayılır (temas sayımı barın kendi anında). **Kırılım:** kapanış çizginin üstünde + (opsiyonel) bir sonraki bar da üstünde → kırılım sinyali kırılım barında. Çizgi, kırıldıktan sonra da grafikte kalır (Görsel 2'de olduğu gibi) ama durumu `broken` olur.
- **Konsolidasyon kutuları:** Son N barın `high−low` aralığı ATR'ye göre dar ve fiyat bu aralıkta kalıyorsa kutu açılır; kutu **yalnızca sola doğru büyüyerek** değil, **ileriye doğru** uzar: kutu `t0`'da tespit edilir ve fiyat çıkana kadar her barda `t1 = t` güncellenir. Kutu sınırları belirlendikten sonra değişmez (repaint yok); kutudan çıkış = breakout sinyali.
- **Destek/direnç bölgeleri:** Onaylı pivotların fiyat kümeleri (DBSCAN/yoğunluk, ATR bant genişliği). Bölge, kümedeki k'inci pivot onaylanınca doğar; sonra sadece temas sayısı artar.
- **Hacim profili:** Seçilen pencere (örn. son 250 bar) için fiyat kovalarına hacim dağılımı; POC = en yoğun kova; VA = %70. Gaussian fit `scipy.optimize.curve_fit` ile. Profil bir "seviye üretici"dir; POC/VAH/VAL `Level` olarak çıkar. Pencere sabit ve geriye dönük olduğu için non-repaint.
- **Osilatör:** MACD (12,26,9) veya ikili EMA farkı; histogram; sinyal markerları kesişim barında.

**Modül:** `indicators/structure/price_structure.py` (feature'ları birleştirir). Tarama çıktıları: `trendline_break_up/down`, `box_breakout`, `zone_touch`, `poc_reclaim`, `osc_cross`.

### 6.3 Görsel 3 — Swing Yapısı, Fibonacci ve AB=CD (Düşüş)

**Görülen:** HH/HL/LH/LL etiketli swinglerin ardışık bağlandığı yapı (kırmızı düz çizgi: X→A ayağı); yeşil AB=CD (yükseliş) ve kırmızı AB=CD (düşüş) desenleri; D hedefleri (`D (hedef): 106.75 [TAMAM]`, `D (hedef): 96.30`, `93.70`); sağda son düşüş ayağının Fibonacci retracement'ı (0.236…2.0 uzatılmış seviyeler); başlıkta `Harmonik sayı: 13.99 TL` — büyük olasılıkla AB ayağının mutlak uzunluğu (harmonik birim).

**Matematik:**
- Onaylı swingler → ardışık A,B,C; `CD = AB` (1.0) projeksiyonu, alternatifler 1.27 ve 1.618 (Pesavento). BC, AB'nin 0.382–0.886 retracement'ı olmalı.
- D hedefi C onaylandığında ileriye projeksiyon olarak yazılır (`Level`, `pending`). Fiyat hedefe `tol` içinde ulaştığı barda `TAMAM` (completed). Fiyat hedefe ulaşmadan yeni bir C pivotu oluşursa `invalidated`.
- Fibonacci: son onaylı swing (X→A) üzerine retracement + extension; seviyeler A onaylanınca çizilir ve sabit kalır. Yeni swing onaylanınca **yeni** bir Fibonacci seti eklenir (eskisi silinmez; `end` tarihi konur).
- "Harmonik sayı" = |A−B| (TL); hedef D = C ∓ harmonik sayı.

**Modül:** `indicators/structure/swing_fib_abcd.py`. Tarama çıktıları: `abcd_target_reached`, `abcd_pending_near` (fiyat hedefe %x yakın), `fib_level_touch`.

### 6.4 Görsel 5 — ALARK Kelebek (Bearish, Pesavento) [AKTİF]

**Görülen:** X (HH), A (dip HL), B (LH), C (HL), D projeksiyonu 125.42 `[AKTIF]`; kırmızı gölgeli XAB ve BCD üçgenleri; Fibonacci seviyeleri yatay; X→B trend çizgisi (mavi kesikli) ve `Kırılım: YUKARI yönde, 2026-07-20` — yani fiyat X→B çizgisini yukarı kırdı, bu Pesavento'da D'ye yolculuğun teyidi; "Tarama eşleşmesi".

**Kural seti (Pesavento Butterfly, bearish):** B = 0.786 XA; C = 0.382–0.886 AB; D = 1.27–1.618 XA uzantısı **ve** 1.618–2.24 BC. PRZ bu iki projeksiyonun kesişim bandı. `AKTİF` = fiyat PRZ'nin alt sınırına ilk temas barı. X→B çizgisi kırılım tarihi ayrıca damgalanır.

Bu görsel, harmonik durum makinesinin (`PENDING → ACTIVE → CONFIRMED/INVALIDATED`) doğrudan karşılığıdır.

### 6.5 Görsel 6 — Bullish XABCD [TAMAMLANDI], D: 6.15

**Görülen:** X (HL), A (tepe), B (dip), C (LH), D dibi `[TAMAMLANDI]`; yeşil gölgeli; Fibonacci seviyeleri; X→B'yi yukarı kesen mavi kesikli çizgi (X→B kırılım referansı). Oranlara bakınca B ≈ 0.786 XA, D ≈ 1.27–1.618 XA → Butterfly/Gartley aile boyutları; ekol tarama sonucu etiketlenecek.

`TAMAMLANDI` = fiyat PRZ'ye girdi **ve** PRZ'den dönüş onayı geldi (dönüş barı kapanışı PRZ üstünde + X→B çizgisi kırıldı ya da onaylı pivot low oluştu). Durum `confirmed`/`completed`.

### 6.6 Ortak çıkarımlar (tüm görseller)

1. **Her şey onaylı swing'lerden türüyor.** `features/swings.py` bu projenin temel taşıdır; ilk yazılacak ve en çok test edilecek dosya.
2. **Her indikatör "ileriye projeksiyon + durum" üretir.** Hedef seviyeler önceden yazılır, fiyat oraya gelince durum değişir. Bu, non-repaint ve "görsel kanıt" ihtiyacını aynı anda karşılar.
3. **Grafik primitifleri sınırlı ve yeterli:** Level, Line, Box, Marker, alt panel Series, gölgeli poligon (harmonik üçgenler için `Polygon` primitifi ekleyeceğiz). Görsellerdeki her öğe bu altı primitifle çizilebilir.
4. **Etiket sözlüğü Türkçe:** AKTİF, TAMAMLANDI, TAMAM, Kırılım, Temas, Direnç, Destek, Hedef — `viz/labels_tr.py` tek yerden.

---

## 7. Harmonik ekollerin kod mimarisinde izolasyonu

Ortak olan tek şey **geometri**: onaylı swing'lerden X,A,B,C adayları üretmek ve PRZ'yi hesaplamak için yardımcı fonksiyonlar. Ekole özgü olan **kurallar**: hangi oranlar, hangi tolerans, hangi ek şart, hangi zaman şartı.

```python
class HarmonicSchool(ABC):
    name: str                                   # "carney", "pesavento", ...
    patterns: dict[str, PatternSpec]            # "gartley": PatternSpec(xab=(0.618,0.618), abc=(0.382,0.886), bcd=(1.27,1.618), xad=(0.786,0.786))
    tolerance: float                            # oran toleransı (Carney sıkı, Pesavento gevşek)
    def candidate_ok(self, x,a,b,c) -> list[PatternMatch]   # oran kontrolü + ekol ek kuralları
    def prz(self, match) -> PRZ                 # ekole göre PRZ (Carney: XA+BC+AB=CD kesişimi; Pesavento: tek seviye ± tolerans)
    def extra_confirmation(self, df, match, t) -> bool      # Nen Star: MA/MACD; Cypher: C > A şartı; Navarro: 2.0 XA
    def time_window(self, match) -> tuple|None  # Gilmore: D'nin beklendiği bar aralığı
```

Ekol dosyaları birbirini import etmez. `HarmonicIndicator(school="carney")` tek indikatör sınıfıdır; ekol bir parametredir; registry'de 7 ayrı kayıt görünür (`harmonic.carney`, `harmonic.cypher`, ...). Böylece bir ekolü değiştirmek diğerlerinin repaint testini etkilemez.

Ekol özet kuralları (Faz 3 promptunda tam tablo var):

| Ekol | Ayırt edici kural |
|---|---|
| Carney | Gartley 0.618/0.786, Bat 0.382–0.5/0.886, Crab 1.618 XA, Shark 0.886–1.13 / 1.618–2.24; PRZ = 3 projeksiyonun kesişimi; Terminal bar; tolerans dar |
| Pesavento | AB=CD simetri (1.0, 1.27, 1.618 alternatifleri), Butterfly 0.786/1.27–1.618, oran toleransı ±%5; X→B kırılım teyidi |
| Gilmore | Fiyat oranı + **zaman** oranı: CD süresi / AB süresi ≈ 1.0, 1.618; XA süresi ile XD süresi; D için zaman penceresi |
| Oglesbee Cypher | C, A'yı aşar: C = 1.272–1.414 XA; B = 0.382–0.618 XA; D = 0.786 **XC**; |
| Kerkez Nen Star | B = 0.382–0.618, C = 1.272–1.414 XA (A'yı aşar), D = 1.272 XA ve 1.618–2.0 BC; ek teyit: D'de MA(20/50) ve MACD uyumu |
| Beck Navarro 200 | D = 2.0 XA (**%200 uzantı** şart), B = 0.382–0.618, C = 1.272–1.618 AB |
| 5-0 | X-0-1-2-3-4: 0→1 = 1.13–1.618 X→0 dönüşü; 2→3 = 1.618–2.24; 4 = 0.5 retracement (0.5 esas, AB=CD karşılığı); trend dönüş teyidi |

---

## 8. Faz planı ve öncelik sırası

| Faz | Başlık | Çıktı | Kabul kriteri |
|---|---|---|---|
| 0 | İskelet + çekirdek tipler + repaint test altyapısı | paket, `types.py`, `indicator.py`, `testing/repaint.py`, `lint_lookahead.py`, sentetik fixture'lar, CI | Sahte bir "repaint eden" indikatör testte FAIL, dürüst olan PASS |
| 1 | Veri katmanı | yfinance + CSV provider, parquet cache, BIST 4H resample, takvim, validasyon, `tlab update-data` | 10 sembol 1H/1D/4H çekilip doğrulanıyor; 4H barlar 10:00/14:00 hizalı |
| 2 | Özellik katmanı | swings, fibonacci, trendlines, ranges, zones, volume_profile, stats, ma, oscillators | Her feature için repaint testi + birim test; sentetik seride bilinen pivotlar yakalanıyor |
| 3 | Harmonik motor (7 ekol) | geometry, prz, state machine, 7 school, `HarmonicIndicator` | Sentetik Gartley/Butterfly/Cypher fixture'ları doğru ekolde eşleşiyor; durum geçişleri doğru barda; repaint PASS |
| 4 | Yapı indikatörleri | `swing_fib_abcd`, `price_structure` (Görsel 2, 3) | Gerçek TCELL verisinde Görsel 2/3'e benzer çıktı; sinyaller listeleniyor |
| 5 | Pair arbitraj | `relative_momentum`, `pairs_engine` backtest, çift keşfi (Görsel 1, 4) | TCELL–ISCTR koşusu 3 panel + metrik tablosu üretiyor |
| 6 | Tarayıcı + EOD + sonuç deposu | engine, eod, results, diff, CLI | 500 sembol × 2 tf tam koşu < 10 dk; ikinci koşu idempotent; diff doğru |
| 7 | Görselleştirme + rapor | renderer (koyu/açık tema), polygon, alt paneller, EOD HTML raporu | 6 görselin her biri birebir yeniden üretiliyor |
| 8 | Trend/MA/momentum modülleri + genişleme (Rev.2: Faz 8A–8E'ye bölündü, bkz. Bölüm 12) | MA sistemleri, düşen trend kırılımı, momentum ekranı, kalite skoru | Registry'de ≥ 15 indikatör, hepsi repaint PASS |
| 9 | Entegrasyon hazırlığı | JSON/REST veya paket API; Bilanço Radar join şeması; TradingView/Fintables köprü noktaları | App'siz, saf API ile tüm işlevlere erişim |

**Neden bu sıra?** Repaint test altyapısı (Faz 0) her şeyden önce; yoksa Faz 2–3'te yine ihlal edilir. Veri (Faz 1) olmadan hiçbir şey gerçek veride denenemez. Harmonik motor (Faz 3) en riskli ve en istediğin modül; feature katmanı sağlamken yapılır. Tarayıcı ve görselleştirme (6–7), 2–3 indikatör hazır olunca anlamlı olur.

Zaman tahmini (Claude Code ile, senin doğrulama süren dahil): Faz 0–1: 2–3 gün, Faz 2: 3–4 gün, Faz 3: 5–7 gün, Faz 4–5: 4–5 gün, Faz 6–7: 4–5 gün, Faz 8–9: açık uçlu.

---

## 9. Claude Code (Sonnet) promptları

### Nasıl kullanılır
- Terminalde proje kökünde `claude` başlat. Her prompt için önce **PROJE BAĞLAMI** bloğunu, sonra faz promptunu yapıştır.
- Faz bitince `pytest -q` ve `tlab repaint-test --all` koş; hepsi geçmeden sonraki faza geçme.
- Sonnet bir kuralı esnetmeye çalışırsa ("basitlik için pivot barını sinyal barı yapıyorum") **kabul etme**; promptta yazan kuralı hatırlat.
- Her faz sonunda `git commit` iste; prompt bunu içeriyor.

---

### PROJE BAĞLAMI (her promptun başına aynen yapıştır)

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

Çalışma tarzı: Önce planını madde madde yaz, onay al, sonra kodla. Her dosyayı yazdıktan sonra
ilgili testi koş. Faz sonunda özet + git commit.
```

---

### FAZ 0 — İskelet, çekirdek tipler, repaint test altyapısı

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

### FAZ 1 — Veri katmanı

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

### FAZ 2 — Özellik katmanı (features)

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

### FAZ 3 — Harmonik motor (7 ekol)

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

### FAZ 4 — Yapı indikatörleri (Görsel 2 ve 3)

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

### FAZ 5 — İkili hisse relatif momentum / arbitraj (Görsel 1 ve 4)

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

### FAZ 6 — Tarama motoru, EOD akışı, sonuç deposu

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

### FAZ 7 — Görselleştirme ve rapor

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

### FAZ 8 — Trend / MA / momentum modülleri ve genişleme

```
FAZ 8 GÖREVİ — Ek indikatör modülleri (trend, ortalamalar, düşen trend kırılımı, momentum) ve
kalite skorlaması

Aynı sözleşme, aynı repaint şartı. Her biri ayrı dosya, registry'ye kaydolur, tlab plot ile tam
görsel üretir.
1) trend/ma_systems.py — EMA/SMA çoklu sistem (8/21/55/200), golden/death cross, fiyat-MA
   ilişkisi durumu (last_state: "above_all", ...), MA bant genişliği (sıkışma → genişleme sinyali).
2) trend/downtrend_break.py — "düşeni kıran": Faz 2 trendlines ile LH'lerden inen çizginin
   yukarı kırılımı + hacim teyidi (hacim > volume_ma × k) + yapı etiketi HL'ye dönmüş olması.
   Skor: temas sayısı, çizgi süresi, hacim oranı.
3) momentum/momentum_rank.py — evren-geneli relatif momentum (3/6/12 bar-ay getirileri, RS
   sıralaması; sektöre göre normalize — sektör dosyası Faz 5'ten). Bu "cross-sectional" bir
   indikatördür: scanner'a "universe-level" kategori ekle (tek koşuda tüm evren birlikte hesaplanır).
4) momentum/rsi_divergence.py — RSI uyumsuzluğu ONAYLI pivotlarla (fiyat LL, RSI HL; pivot
   onay barında sinyal). Klasik repaint tuzağı; testini özellikle yaz.
5) Kalite skoru: tlab/scanner/quality.py — her sinyale ortak 0..1 "confluence" skoru:
   aynı sembolde aynı yönde başka indikatör sinyali var mı (harmonik + trendline break + zone),
   4H ve 1D uyumu. Sadece raporlama; sinyal üretmez.
6) Registry'de ≥ 15 indikatör; hepsi repaint PASS; tlab scan tam koşu süresi raporu.
git commit: "faz8: trend/ma/momentum modülleri".
```

---

### FAZ 9 — Entegrasyon hazırlığı (Bilanço Radar, TradingView, Fintables)

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
6) Dokümantasyon: docs/ARCHITECTURE.md (katmanlar, non-repaint sözleşmesi, ekol tabloları),
   docs/ADDING_AN_INDICATOR.md (adım adım: dosya, params, compute, testler, repaint, register,
   plot), docs/EOD.md.
git commit: "faz9: api ve entegrasyon iskeleti".
```

---

## 10. Riskler ve dikkat noktaları

1. **Veri kaynağı BIST 1H:** yfinance 1H'de ~730 gün geçmiş verir ve kalite dalgalıdır. Cache'i günlük artımlı büyüterek kendi tarihçeni oluştur; ileride Fintables/TradingView export'una geçiş provider katmanı sayesinde ağrısız olur. 4H'i asla üçüncü partiden hazır alma — kendi hizalamanla üret.
2. **Split/temettü düzeltmesi:** Harmonik oranlar düzeltilmemiş seride bozulur. `adjusted=True` varsayılan; ama düzeltme geçmişe yansıdığında eski sinyallerin seviyeleri değişir (bu repaint değil, veri revizyonudur). `results.diff` bunu "data revision" olarak ayrı raporlasın; `payload`'a `adj_factor` yaz.
3. **Pivot parametreleri:** `right` büyüdükçe sinyal gecikir ama gürültü azalır. 1D için `left=right=5`, 4H için `left=right=8` başlangıç; ekol bazında ayarlanabilir. Bunu "gecikme maliyeti" olarak kabul ediyoruz; bedeli ödemeden non-repaint olmaz.
4. **Harmonik aday patlaması:** Gevşek toleransla yüzlerce aday çıkar. `max_candidates_per_bar`, skor eşiği ve "en iyi PRZ" seçimiyle sınırla; raporda ekol başına ilk N.
5. **Pair trading kayması:** Görseldeki +%19.7 in-sample'dır. Parametre (window, k) optimizasyonu yapmadan önce out-of-sample bölme ekle; aksi halde aşırı uyum.
6. **Sonnet ile çalışırken:** Faz 2 ve 3'te "onay barı" kuralını sulandırma eğilimi olur. Her PR'da `tlab repaint-test --all` çıktısını iste; geçmiyorsa kodu kabul etme.

---

## 11. İlk üç günde yapılacaklar (kısa liste)

1. Repo aç, PROJE BAĞLAMI + FAZ 0 promptunu ver, CheatingIndicator'ın FAIL ettiğini kendi gözünle gör.
2. FAZ 1: TCELL, ISCTR, ALARK, THYAO, ASELS verisini çek; 4H barların 10:00/14:00 hizasını parquet'te kontrol et.
3. FAZ 2'ye başla; `swings.py` bitince property testinin (kesik seri pivotları ⊆ tam seri pivotları) geçtiğini doğrula. Bu test geçiyorsa projenin temeli sağlamdır.

---

# REVİZYON 2 — Ek tarama modülleri (Bölüm 12–13)

> Bu bölüm ilk raporun üzerine eklenmiştir. Mimari, sözleşme ve repaint kuralları değişmedi; yeni modüller aynı `IndicatorResult` arayüzüne ve aynı repaint testine tabidir. Faz 8 bu bölümde 8A–8E olarak genişletildi ve her biri için ayrı prompt verildi.
>
> **X hesabı notu:** `x.com/The_Tansu_` hesabına otomatik erişim X tarafından engelleniyor (robots + JS zorunluluğu), arama motorlarında da içerik indekslenmemiş; bu yüzden oradaki formülleri doğrudan inceleyemedim. Aşağıdaki modüller senin sıraladığın başlıklara ve bu alanların yerleşik tanımlarına göre kuruldu. Hesaptan belirli paylaşımların ekran görüntüsünü ya da metnini gönderirsen, ilgili formülleri birebir bu şemaya oturturum (Bölüm 12.13'te bunun için hazır bir "formül aktarma şablonu" var).

---

## 12. Yeni modüllerin tasarımı

Her modül için aynı beş başlık: **Tanım → Non-repaint kurgusu → Görsel primitifler → Tarama çıktıları / last_state → Dosya**.

Ortak yeni feature'lar (Faz 2'ye eklenecek, `tlab/features/`):
- `channels.py` — paralel kanal (regresyon veya iki pivot + paralel), haftalık kanal
- `patterns_geom.py` — üçgen/takoz/bayrak için "yakınsayan iki trend çizgisi" geometrisi (trendlines.py üzerine)
- `hs_pattern.py` — omuz-baş-omuz geometrisi (5 pivot + boyun çizgisi)
- `zones_sd.py` — demand/supply bölgeleri (baz mumlar + patlama), golden zone (fib 0.618–0.786 bandı)
- `volatility.py` — ATR, realized vol, Bollinger genişliği, Keltner, vol z-skoru
- `xsec.py` — evren-geneli (cross-sectional) hesaplar: alpha, beta, RS, sıralama, yüzdelik

`Timeframe` enum'una **W1 (haftalık)** eklenir; haftalık barlar 1D'den resample edilir (BIST: Pazartesi–Cuma, hafta kapanışı Cuma; açık hafta düşürülür).

### 12.1 Arbitraj Volatilite Harvesti (pair'in gelişmiş modu)

**Tanım.** Faz 5'teki relatif momentum çifti, spread'in ortalamaya dönüşünü tek bir eşikle yakalıyordu. "Volatilite harvesti", aynı çiftte spread'in salınımını **kademeli** olarak hasat eder: spread z-skoru uzaklaştıkça pozisyon ağırlığı ters yönde artırılır (grid/scale-in), ortalamaya dönüşte kademeli hasat edilir. Long-only versiyonda: iki hisse arasındaki ağırlık (w_Y, 1−w_Y) z-skorunun fonksiyonudur; her yeniden dengeleme, "ucuzu al pahalıyı sat" olarak volatiliteden getiri toplar (rebalancing premium).

**Matematik.**
- `z_t` Faz 5 ile aynı (rolling, non-repaint).
- Ağırlık fonksiyonu: `w_Y(z) = clip(0.5 − z·s, w_min, w_max)` — s = eğim (örn. 0.15/σ), band = ±3σ'da w_min/w_max'a doyar. Alternatif: kademeli grid (z ∈ {±1, ±1.5, ±2, ±2.5} eşiklerinde ±%12.5 adım).
- Yeniden dengeleme tetiği: `|w_target − w_current| > rebalance_band` (örn. %5) → o barın kapanışında işlem. Bu, işlem sayısını kontrol eder ve komisyon maliyetini sınırlar.
- Harvest ölçümü: `harvest_t = portföy_t − (w_Y0·Y_t + (1−w_Y0)·X_t)` (statik başlangıç ağırlıklı al-tut'a göre fazla getiri). Bu fark, "volatiliteden hasat edilen" kısmın tanımıdır; raporda ayrı seri.
- Vol rejimi filtresi (opsiyonel): spread realized vol'ü kendi rolling ortalamasının altındaysa (spread "ölü"), rebalans adımı küçültülür.
- Risk: eşbütünleşme bozulursa (rolling ADF p > 0.10 veya half-life > max) modül `paused` durumuna geçer — o barda sinyal.

**Non-repaint.** Tüm girdiler rolling; işlem kararı kapanış barında; hedef ağırlık `t`'de `z_t` ile kesin.

**Görsel.** Görsel 1'in 3 paneline **4. panel** eklenir: w_Y zaman serisi (adım grafiği) + rebalans markerları; 2. panelde "harvest" serisi (portföy − statik al-tut) ayrıca; başlıkta "Hasat: +X TL (%y) | Rebalans: n".

**Çıktılar.** Signals: `rebalance` (yön, eski→yeni ağırlık), `paused/resumed`. last_state: z, w_current, w_target, harvest_pnl, n_rebalance, adf_p, halflife.

**Dosya.** `indicators/pairs/vol_harvest.py` (RelativeMomentumPair'in yanında; ortak `features/stats.py`), backtest: `backtest/pairs_engine.py`'ye `mode="weights"` eklenir.

### 12.2 Alpha Hisseleri (cross-sectional)

**Tanım.** Endekse (XU100 / NASDAQ100) göre **anormal getiri** üreten hisseler: Jensen alfası + risk-ayarlı fazla getiri. "Alpha hissesi" = alfası pozitif, istatistiksel olarak anlamlı ve son dönemde kalıcı.

**Matematik.**
- Rolling OLS: `r_i,t = α + β·r_m,t + ε`, pencere 60/120/250 gün (üç ufuk). `α` yıllıklandırılır, `t-stat(α)` hesaplanır.
- Bilgi oranı: `IR = mean(ε)/std(ε)·√252`.
- Kalıcılık: son 3 pencerede alfa işareti aynı mı (`alpha_persistence`).
- Skor (0..1): `rank(α_ann)·0.4 + rank(t_stat)·0.3 + rank(IR)·0.2 + persistence·0.1` — evren içinde yüzdelik.
- Filtreler: min likidite (ortalama TL hacim), min gün sayısı.

**Non-repaint.** Rolling regresyon, `t`'de yalnızca geçmiş; sıralama evren-geneli ama o barın verileriyle (cross-sectional hesap "universe-level" kategori — Faz 8 promptunda tanımlı).

**Görsel.** Tekil hisse: üst panel hisse vs endeks normalize; 2. panel rolling α (yıllık) ve ±t-stat bandı; 3. panel β; 4. panel kümülatif ε (alfa eğrisi). Evren görünümü: α–β saçılım (x=β, y=α, boyut=likidite), sağ üst çeyrek vurgulu.

**Çıktılar.** `alpha_entry` (skor eşiği aşıldı, ilk bar), `alpha_exit`. last_state: α_60/120/250, t_stat, IR, β, rank, persistence.

**Dosya.** `indicators/momentum/alpha_rank.py` + `features/xsec.py`.

### 12.3 Momentum Hisseleri (cross-sectional)

**Tanım.** Akademik momentum (12-1: son 12 ay getirisi son 1 ay hariç), kısa vadeli momentum (1/3/6 ay), göreli güç (RS = hisse/endeks oranının eğimi), trend kalitesi (fiyat > MA50 > MA200, MA eğimleri) ve "momentum kalitesi" (Frog-in-the-Pan: pozitif gün yüzdesi — düzgün ilerleyen momentum, sıçramalı olandan üstündür).

**Matematik.**
- `mom_12_1 = P_{t-21}/P_{t-252} − 1`; `mom_1/3/6` benzer.
- `RS_slope`: log(P/Endeks) üzerine 60 barlık regresyon eğimi, t-stat.
- `FIP = sign(mom)·(%neg_days − %pos_days)` (düşük = iyi).
- `trend_score`: kapanış > EMA20 > EMA50 > EMA200 ve EMA eğimleri pozitif → 0..4.
- Vol-ayarlı momentum: `mom / realized_vol`.
- Skor: yüzdelik kombinasyonu; evrende ilk %10 = "Momentum hissesi".

**Görsel.** Üst: fiyat + EMA20/50/200; 2. panel RS çizgisi + eğim regresyonu; 3. panel momentum ufukları çubuk (1/3/6/12-1); 4. panel FIP. Evren: momentum ısı haritası (sektör × ufuk).

**Çıktılar.** `momentum_top_entry/exit`, `rs_breakout` (RS yeni 52 hafta zirvesi — fiyattan önce sinyal verir). last_state: tüm ölçüler + rank.

**Dosya.** `indicators/momentum/momentum_rank.py` (Faz 8'deki yer tutucunun tam tanımı).

### 12.4 Haftalık kanal dibine temas eden hisse taraması

**Tanım.** Haftalık grafikte fiyatın uzun vadeli yükselen (veya yatay) kanalın alt bandına teması: "kanal dibi" alım bölgesi.

**Kanal tanımı (iki yöntem, parametre):**
1. **Regresyon kanalı:** son N haftanın (52/104/156) log-fiyat regresyonu; bantlar = ±k·std(residual) (k=2) veya ±max sapma. Kanal her barda son N barla yeniden hesaplanır → her hafta kanal biraz değişir. **Repaint tuzağı:** "kanal dibine temas" sinyali, o haftanın kanalıyla o haftada üretilir ve kaydedilir; kanalın sonraki haftalarda kayması sinyali değiştirmez (grafikte "o günkü kanal" çizilir; `Line.points` sinyal barında dondurulur, `extend_right=False`). Görselde iki kanal gösterilir: sinyal anındaki (soluk) ve güncel (belirgin).
2. **Pivot kanalı:** onaylı iki haftalık swing low'dan geçen alt çizgi + en yüksek swing high'dan paralel üst çizgi (Faz 2 trendlines mantığı; sabit, extend-only). Repaint yok, gecikme var.

**Temas kuralı.** `low_t ≤ alt_bant_t·(1+tol)` ve `close_t > alt_bant_t` (bant tutmuş) → `channel_bottom_touch`; kapanış bant altında → `channel_break_down`. Ek kalite: kanal eğimi pozitif (yükselen kanal), önceki temas sayısı ≥2, RSI(14 haftalık) < 40.

**Görsel.** Haftalık mumlar; kanal (üst/orta/alt); önceki temas noktaları marker; temas barı "KANAL DİBİ" etiketi; alt panel: fiyatın kanal içindeki konumu %0–100 (osilatör).

**Çıktılar.** `channel_bottom_touch`, `channel_top_touch`, `channel_break_down/up`. last_state: kanal konumu %, eğim, temas sayısı, "dipte mi?" (konum < %15).

**Dosya.** `indicators/trend/weekly_channel.py` + `features/channels.py`. Zaman dilimi: W1 (ayrıca 1D'de 250 barlık kanal olarak da kayıtlı: `daily_channel`).

### 12.5 Düşeni kıran + Çoklu kırılım tarayıcısı ("farklı kırılımları gösteren tarama")

Tek bir "kırılım" indikatörü değil, **kırılım türleri sözlüğü** ve her türü ayrı damgalayan bir tarayıcı. Hepsi Faz 2 trendlines/ranges/zones/channels üzerine:

| Kırılım türü | Tanım | Teyit |
|---|---|---|
| `downtrend_break` (düşeni kıran) | LH'lerden inen direnç çizgisinin yukarı kırılımı | kapanış > çizgi, `confirm_bars`, hacim > vol_ma·k, yapı HL'ye döndü |
| `uptrend_break` | HL'lerden çıkan destek çizgisinin aşağı kırılımı | simetrik |
| `range_breakout_up/down` | Konsolidasyon kutusundan çıkış | kapanış kutu dışı + kutu yüksekliği ATR'ye göre |
| `zone_break` | Destek/direnç bölgesi kırılımı | kapanış bölge dışı |
| `hh_break` / `ll_break` | Son onaylı swing high üzerinde kapanış (yapı kırılımı, BOS) | kapanış > son pivot high |
| `n_week_high` | 52/26 haftalık zirve kırılımı | kapanış > rolling max (kapalı barlar) |
| `ma_break` | EMA50/200 üzerinde kapanış (aşağıdan) | k bar üstünde |
| `channel_break` | Kanal üst/alt bant kırılımı | 12.4 |
| `pattern_break` | Takoz/bayrak/TOBO boyun çizgisi kırılımı | 12.6–12.8 |
| `retest_hold` | Kırılan seviyeye geri test + tutma | kırılım sonrası low seviyeye tol içinde döner ve kapanış üstte kalır |
| `false_break` | Kırılım sonrası k bar içinde geri dönüş | kapanış tekrar seviye altında (bilgi amaçlı, non-repaint: geri dönüş barında damgalanır; orijinal kırılım kaydı silinmez) |

**Kırılım kalite skoru** (ortak): hacim oranı, kırılım mumu gövde oranı, seviyenin yaşı (bar), temas sayısı, ATR'ye göre kırılım mesafesi, 4H–1D uyumu. `false_break` sonradan işaretlense de ilk kırılım sinyali geçmişte kalır — "sinyal doğruydu ama başarısız oldu" olarak raporlanır.

**Görsel.** Kırılan seviye/çizgi (kırık gösterimi), kırılım mumu vurgusu, hacim paneli, "Kırılım: YUKARI | Tür: düşeni kıran | Hacim ×2.1" etiketi, retest bölgesi kutusu.

**Dosya.** `indicators/trend/breakouts.py` (tüm türleri tek `IndicatorResult`'ta, payload `break_type` ile; taramada tür filtresi). `downtrend_break.py` Faz 8 taslağındaki modül bunun içine katlanır.

### 12.6 Takoz (Wedge) — yükselen/alçalan

**Tanım.** İki **aynı yöne eğimli ve yakınsayan** trend çizgisi: alçalan takoz (her iki çizgi aşağı, üst daha dik → genelde yukarı kırar), yükselen takoz (her iki yukarı, alt daha dik → genelde aşağı kırar).

**Geometri (non-repaint).** Onaylı pivotlardan üst çizgi (≥2 LH veya HH) ve alt çizgi (≥2 LL veya HL); şartlar: aynı işaretli eğimler, eğim oranı `0.3 < |m_alt/m_üst| < 1` (alçalan) / tersi (yükselen), yakınsama (çizgiler ileride kesişir, apex uzaklığı `< max_bars`), her çizgide ≥2 temas, en az 4 pivot toplam, süre `≥ min_bars`. Formasyon, **4. pivot onaylandığı barda** doğar (`pending`); kırılım = kapanış üst çizgi üstü (alçalan) / alt çizgi altı (yükselen) + hacim → `confirmed`; apex'e %80 yaklaşıldı ve kırılım yok → `expired`. Hedef: takozun en geniş yerinin yüksekliği kadar (Level `hedef`).

**Görsel.** İki çizgi (kesişime doğru uzatılmış, kesikli), pivot markerları, kırılım barı, hedef seviyesi, apex işareti.

**Dosya.** `indicators/patterns/wedge.py` + `features/patterns_geom.py` (üçgenler için de aynı geometri: simetrik/yükselen/alçalan üçgen bonus olarak).

### 12.7 TOBO (Ters Omuz-Baş-Omuz) ve OBO

**Geometri.** TOBO: ardışık onaylı pivotlar `L1 (sol omuz) – H1 – L2 (baş, en düşük) – H2 – L3 (sağ omuz)`; şartlar: `L2 < L1 ve L2 < L3`, omuzlar simetrik (`|L1−L3| < sym_tol·(H−L2)`), boyun çizgisi = H1→H2 doğrusu (eğim sınırlı), sağ omuz süresi sol omzun 0.5–2 katı. OBO simetrik.

**Durumlar.** Sağ omuz (L3) pivotu **onaylandığı** barda `pending` (boyun çizgisi çizilir, hedef = boyun − (boyun−baş) projeksiyonu). Kapanış boyun üstü (+confirm, +hacim) → `confirmed` ("TOBO ONAY" — X'teki "Tobo formasyon onayı almış hisseler" taramasının karşılığı). Retest → `retest_hold`. Boyun kırılmadan L3 altına kapanış → `invalidated`. Hedefe ulaşma → `target_reached`.

**Görsel.** Omuz/baş etiketleri, boyun çizgisi (extend_right), hedef seviyesi, kırılım ve retest markerları, hacim paneli (idealde sağ omuzda düşen, kırılımda artan hacim — payload'da `volume_profile_ok`).

**Dosya.** `indicators/patterns/head_shoulders.py` + `features/hs_pattern.py`.

### 12.8 Bayrak ve Flama

**Tanım.** Sert hareket (direk) + kısa, ters yönlü/dar konsolidasyon (bayrak: paralel kanal; flama: küçük simetrik üçgen) + direk yönünde kırılım.

**Kurallar (non-repaint).** Direk: `k` bar içinde `≥ pole_atr·ATR` veya `≥ pole_pct` hareket (rolling, o barda bilinir). Konsolidasyon: direkten sonra `min..max` bar, aralık `< flag_atr·ATR`, geri çekilme direğin `< %50`'si; bayrakta hafif ters eğimli iki paralel çizgi (küçük pivotlarla veya kutu ile), flamada yakınsayan çizgiler. Pattern, konsolidasyon `min_bars`'a ulaştığında `pending`; kapanış konsolidasyon üst sınırını (bullish) hacimle geçince `confirmed`; hedef = direk uzunluğu (ölçülü hareket). `max_bars` aşılırsa `expired`.

**Görsel.** Direk (kalın ok/çizgi), bayrak kanalı/flama üçgeni, kırılım barı, hedef seviyesi, "BAYRAK" / "FLAMA" etiketi.

**Dosya.** `indicators/patterns/flag_pennant.py`.

### 12.9 Golden Zone

**Tanım.** Son anlamlı swing'in Fibonacci **0.618–0.786** (opsiyonel 0.5–0.618 "OTE" varyantı) geri çekilme bandı. Yükselen trendde fiyat bu banda gelip tutunuyorsa (dönüş mumu / yapı korunmuş) alım bölgesi.

**Kural (non-repaint).** Son onaylı swing low→swing high (Faz 2 swings; A onaylanınca band çizilir, sabit). `low_t` bant içine girdi → `golden_zone_touch` (bar t); `close_t` bant üstünde ve dönüş mumu (gövde > %50 aralık, yön yukarı) → `golden_zone_reaction`; kapanış bant altı → `golden_zone_fail`; sonraki barlarda swing high aşılırsa `golden_zone_success`. Yeni swing onaylanınca yeni bant, eski bant `end` alır.

**Görsel.** Gölgeli altın bant (0.618–0.786), 0.5 çizgisi, swing çizgisi, temas/dönüş markerları, "GOLDEN ZONE: 0.618=107.2 / 0.786=104.9" etiketi.

**Dosya.** `indicators/structure/golden_zone.py` (Faz 4 swing_fib ile aynı feature'ları kullanır).

### 12.10 Demand / Supply Zone

**Tanım.** Kurumsal emir bölgeleri: bir "baz" (dar, 1–5 mum konsolidasyonu) sonrasında güçlü patlama (impulsive move). Demand = baz sonrası yukarı patlama (RBR: rally-base-rally, DBR: drop-base-rally); Supply = aşağı patlama (RBD, DBD). Bölge = baz mumlarının gövde/fitil sınırları.

**Kural (non-repaint).** Baz: `n ≤ base_max` ardışık mum, her biri `range < base_atr·ATR`. Patlama: bazdan sonraki `k` mumda hareket `≥ impulse_atr·ATR` ve kapanış bazdan uzak. **Bölge, patlama koşulu sağlandığı barda doğar** (o bar = `detected_at`), sınırları baz mumlarından sabitlenir (`Box`, extend_right). Kalite: patlama gücü, bazın darlığı, "taze" (henüz test edilmemiş) olma. Fiyat bölgeye geri döner: `zone_test` (ilk temas — "fresh" bayrağı düşer), dönüş mumu → `zone_reaction`, kapanış bölge dışına ters yönde → `zone_broken` (bölge "flip" olabilir: kırılan demand → supply).

**Görsel.** Yeşil (demand) / kırmızı (supply) kutular sağa uzatılmış, üstünde "DEMAND (taze) | güç 3.1 ATR" etiketi, test markerları, kırılan bölge soluk/çizgili.

**Çıktılar.** `sd_zone_created`, `sd_zone_test`, `sd_zone_reaction`, `sd_zone_broken`. last_state: en yakın demand/supply bölgesi ve uzaklık (ATR cinsinden), fiyat şu an bir bölgede mi.

**Dosya.** `indicators/structure/supply_demand.py` + `features/zones_sd.py`.

### 12.11 "Hisse dibe geldi mi? Nereden dönüş vermiş?" — Dönüş Haritası (kompozit görünüm)

Bu ayrı bir indikatör değil; **bir sembol için tüm bölge/seviye üreticilerin tek grafikte birleştirildiği** bir görünüm ve bir **confluence skoru**dur.

- Girdi: aynı sembol için `supply_demand`, `golden_zone`, `price_structure` (S/R bölgeleri, POC/VA), `weekly_channel` (alt bant), `harmonic.*` (aktif PRZ'ler), `swing_fib_abcd` (D hedefleri) sonuçları (hepsi zaten results.db'de).
- Hesap (`scanner/confluence.py`): fiyat ekseni ATR/10 kovalara bölünür; her kovaya, o kovayı kapsayan her seviye/bölge için ağırlıklı puan eklenir (bölge tazeliği, zaman dilimi ağırlığı W1 > 1D > 4H, kaynak güvenilirliği). Sonuç: **destek yoğunluk profili** (fiyata karşı puan).
- "Dibe geldi mi?" = fiyat, en yoğun destek kümesinin içinde/ATR·0.5 mesafesinde ve son bar dönüş mumu / yapı LL→HL'ye dönmedi mi kontrolü. Çıktı: `bottom_probability` (0..1, sadece sıralama amaçlı — olasılık iddiası değil).
- "Nereden dönüş vermiş?" = son onaylı swing low'un hangi bölge/seviyeye denk geldiği (geriye dönük **açıklama**, sinyal değil; `detected_at` = swing onay barı; payload'da "dönüş kaynağı: haftalık kanal dibi + demand bölgesi (taze) + 0.618").
- Bu görünüm, taramada "confluence ≥ 3 kaynak ve fiyat destekte" filtresiyle bir liste üretir: **"Dipte olası hisseler"**.

**Görsel.** Fiyat + tüm bölgeler katmanlı (opaklık = ağırlık), sağ kenarda destek yoğunluk profili (hacim profili ile aynı panelde ayrı renk), son dönüş noktası açıklama kutusu.

**Dosya.** `scanner/confluence.py` + `viz/renderer.py`'ye `mode="reversal_map"`. Bölüm 8'deki `quality.py` bunun genel hali olur.

### 12.12 Tarama presetleri (config/scans.yaml)

Kullanıcı tarafı için hazır tarama tanımları — hangi indikatör, hangi tf, hangi filtre. Her preset EOD raporunda bir sekme:

```yaml
dusen_kiran:       {indicator: breakouts, tf: [1D, 4H], filter: "break_type == 'downtrend_break' and volume_ratio > 1.5"}
tobo_onay:         {indicator: head_shoulders, tf: [1D], filter: "state == 'confirmed' and pattern == 'tobo'"}
kanal_dibi_hafta:  {indicator: weekly_channel, tf: [W1], filter: "signal == 'channel_bottom_touch'"}
golden_zone:       {indicator: golden_zone, tf: [1D, 4H], filter: "signal in ('golden_zone_touch','golden_zone_reaction')"}
demand_taze:       {indicator: supply_demand, tf: [1D], filter: "kind == 'demand' and fresh and distance_atr < 0.5"}
harmonik_aktif:    {indicator: "harmonic.*", tf: [1D, 4H], filter: "state == 'active'"}
alpha_top:         {indicator: alpha_rank, tf: [1D], filter: "rank_pct <= 10"}
momentum_top:      {indicator: momentum_rank, tf: [1D], filter: "rank_pct <= 10"}
dipte_olasi:       {indicator: confluence, tf: [1D], filter: "n_sources >= 3 and bottom_probability > 0.6"}
takoz_bayrak:      {indicator: [wedge, flag_pennant], tf: [1D, 4H], filter: "state in ('pending','confirmed')"}
arbitraj:          {indicator: [relative_momentum_pair, vol_harvest], tf: [1D], filter: "signal_today is not None"}
```

### 12.13 X hesabındaki formülleri aktarma şablonu

Hesaptan bir paylaşımı eklemek istediğinde bana (veya doğrudan Sonnet'e) şu şablonla ver; sistem bunu ek indikatör olarak alır:

```
ADI: ...
KAYNAK: (tweet linki / ekran görüntüsü)
ZAMAN DİLİMİ: 4H / 1D / W1
GİRDİLER: (fiyat, hacim, endeks, başka indikatör)
FORMÜL / KURAL: (adım adım; pivot kullanıyorsa left/right; eşikler)
SİNYAL: hangi barda, hangi koşulla
GRAFİKTE GÖRÜNMESİ GEREKENLER: çizgi/kutu/seviye/etiket listesi
TARAMA FİLTRESİ: (opsiyonel)
```

Ben bunu "non-repaint" olarak yeniden ifade eder (pivot barı → onay barı çevirisi dahil), Bölüm 12 formatına oturtur ve Faz 8 promptuna eklerim.

---

## 13. Revize faz planı ve ek promptlar

Faz 0–7 aynen kalır; iki küçük ek:
- **Faz 1'e ek:** `Timeframe.W1` ve haftalık resample (1D → W1, Cuma kapanışlı, açık hafta düşürülür).
- **Faz 2'ye ek:** `channels.py`, `patterns_geom.py`, `hs_pattern.py`, `zones_sd.py`, `volatility.py`, `xsec.py` (aşağıdaki FAZ 2-EK promptu).

Faz 8 beşe bölünür:

| Faz | Kapsam | Kabul |
|---|---|---|
| 8A | Kırılım tarayıcısı (11 tür) + düşeni kıran | Her tür için sentetik fixture; repaint PASS; TCELL'de trendline kırılım tarihi Görsel 2 ile uyumlu |
| 8B | Formasyonlar: Takoz, TOBO/OBO, Bayrak/Flama (+ üçgenler) | Sentetik fixture'larda doğru durum geçişleri; gerçek veride ≥1 TOBO onayı bulunuyor |
| 8C | Bölgeler: Golden Zone, Demand/Supply, Haftalık kanal | Bölgeler extend-only; kanal sinyali dondurulmuş kanalla; W1 çalışıyor |
| 8D | Cross-sectional: Alpha, Momentum, MA sistemleri | universe-level kategori scanner'da; rank testleri |
| 8E | Vol harvest arbitraj + Dönüş haritası (confluence) + tarama presetleri | 4 panelli harvest grafiği; reversal_map görünümü; scans.yaml EOD raporunda sekmeler |

---

### FAZ 2-EK — Yeni feature'lar

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

### FAZ 8A — Kırılım tarayıcısı (düşeni kıran + 11 kırılım türü)

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
config/scans.yaml'a 'dusen_kiran' presetini ekle; tlab scan --preset dusen_kiran çalışsın.
git commit: "faz8a: kırılım tarayıcısı".
```

---

### FAZ 8B — Formasyonlar: Takoz, TOBO/OBO, Bayrak/Flama

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
6) scans.yaml: tobo_onay, takoz_bayrak presetleri. Gerçek veri smoke: evren 1D'de ≥1 TOBO
   confirmed bul, tlab plot ile grafiğini üret.
git commit: "faz8b: takoz, tobo/obo, bayrak/flama".
```

---

### FAZ 8C — Bölgeler: Golden Zone, Demand/Supply, Haftalık kanal

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

### FAZ 8D — Cross-sectional: Alpha, Momentum, MA sistemleri

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
5) Testler: xsec fonksiyonları sentetik evrende (bilinen alfa/momentum ile üretilmiş 20
   sembol) doğru sıralama; universe-level repaint testi (evren sözlüğünün her df'si aynı cut'ta
   kesilir; rank'lar kesik ⊆ tam).
6) scans.yaml: alpha_top, momentum_top. tlab scan --preset momentum_top.
git commit: "faz8d: alpha, momentum, ma sistemleri".
```

---

### FAZ 8E — Volatilite Harvesti, Dönüş Haritası (confluence), presetler

```
FAZ 8E GÖREVİ — vol_harvest.py, confluence.py, scans.yaml entegrasyonu, EOD sekmeleri

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

## 14. Revizyon sonrası öncelik önerisi

Faz 0–3 (altyapı + harmonik) → Faz 4 (yapı) → Faz 5 (pair) → Faz 6–7 (tarama/görsel) → **8A kırılımlar → 8C bölgeler → 8B formasyonlar → 8D cross-sectional → 8E harvest+confluence** → Faz 9. Gerekçe: kırılım ve bölge modülleri hem en çok tarama presetini besler hem de confluence'ın hammaddesidir; formasyonlar ve cross-sectional modüller onların üzerine gelir.
