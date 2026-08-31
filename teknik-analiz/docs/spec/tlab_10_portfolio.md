# SPEC: Faz 10 — Sinyalden Portföye (`tlab/portfolio/`, `tlab/backtest/metrics.py`)

**Durum:** TASLAK (K3'ün doğal çıktısı — henüz kodlanmadı, onay bekliyor). Bu spec, K3
(2026-08-31, `bilanco-radar/bilgi-bankasi/teknik/11_carver_systematic.md`) çıkarımının
Faz 10 kod fazına çevirisidir. Yazan: bu oturum (`teknik-analiz-uzmani` rolünü üstlenerek,
o agent'ın kesin kuralları takip edilerek — agent tanımı `bilanco-radar/.claude/agents/
teknik-analiz-uzmani.md`'de).

## Amaç ve kapsam

Bugüne kadarki TÜM tlab indikatörleri (`harmonic.*`, `structure.*`, `trend.*`,
`patterns.*`, `momentum.*`) TEK bir sembol için Signal/IndicatorResult üretir — hiçbiri
"bu sinyale göre KAÇ LOT/HİSSE alayım, sermayemin YÜZDE KAÇINI bu pozisyona ayırayım"
sorusuna cevap vermez. Faz 10, bu boşluğu Carver'ın (Systematic Trading, K3 çıkarımı)
forecast→volatilite hedefleme→pozisyon boyutlama→portföy zincirini tlab'a uyarlayarak
kapatır. Kapsam: (1) birden fazla kuralın forecast'ını TEK bir kombine forecast'a
indirgemek, (2) kombine forecast'ı GERÇEK pozisyon büyüklüğüne çevirmek (sermaye/risk
hedefine göre), (3) birden fazla enstrüman/kural arasında sermaye PAYLAŞTIRMAK
(handcrafting), (4) çeşitlendirme çarpanı + pozisyon eylemsizliği (inertia) ile nihai
işlem kararı üretmek, (5) bir stratejinin ciro/maliyet oranını "hız limiti" disiplinine
göre denetlemek.

**Kapsam DIŞI (bilinçli, bu taslakta):** carry kuralının TAM formülü, execution-mikroyapı
maliyet modellemesi (order book derinliği — tlab EOD/4H seviyesinde çalışıyor, gerçek
zamanlı emir defteri verisi YOK), sermaye büyüklüğüne göre portföy boyutu kararları
(Ch.12'nin "Trading with more or less capital" kısmı). Bunlar K3'ün kendi "Bilinçli
boşluklar" notunda da işaretli.

## Kaynak atıfları

Tüm parametre/formül/tablo atıfları `bilgi-bankasi/teknik/11/<KOD>` biçiminde (dosya:
`bilanco-radar/bilgi-bankasi/teknik/11_carver_systematic.md`):

- Forecast ölçek/scalar/capping: `11/KURAL-01`, `11/ORAN-01`, `11/DISIPLIN-01`
- Kombine forecast + diversification multiplier: `11/DISIPLIN-02`, `11/ORAN-02`,
  `11/ORAN-03`, `11/ORAN-04`
- Volatilite hedefleme + pozisyon boyutlama (tam formül zinciri): `11/DISIPLIN-03`,
  `11/DISIPLIN-04`, `11/ORAN-05`, `11/"FORMÜL ZİNCİRİ"` (Bölüm 2, adım 1-13)
- Handcrafting (ağırlıklandırma): `11/KURAL-05`, `11/ORAN-06`, `11/ORAN-07`,
  `11/DISIPLIN-05`, `11/DISIPLIN-06`, `11/DISIPLIN-07`, `11/DISIPLIN-08`
- Fitting disiplini + hız limiti (backtest metrikleri): `11/DISIPLIN-09..12`,
  `11/ORAN-08..10`, `11/PSK-01/02`

## Girdiler

- `tlab/features/oscillators.py`/`ma.py`'den DEĞİL, doğrudan HAM `df` (OHLCV) — price
  volatility hesabı için (`close.diff()` bazlı, `%` değil — bkz. Parametreler).
- Bir veya daha fazla indikatörün ürettiği HAM forecast serisi. **Önemli mimari not:**
  mevcut indikatörler (ör. `trend.ewmac`) "forecast" değil `Signal`/`series` üretir —
  Faz 10, bu indikatörlerin `series["ewmac_combined"]` gibi -20..+20 ölçekli serilerini
  DOĞRUDAN "forecast" olarak kabul edebilir (`trend.ewmac` zaten `11/ORAN-01`'in
  gerektirdiği ölçekte — bkz. Faz 8D). Diğer indikatörlerin (harmonik/patterns) `Signal.
  score` (0..1) alanı forecast'a ÇEVRİLMEZ — bunlar olay-tabanlı (event-based), Carver'ın
  SÜREKLİ forecast modeliyle doğrudan uyumsuz; bu spec yalnızca SÜREKLİ forecast üreten
  indikatörleri (şu an: `trend.ewmac`, ileride `trend.ma_systems` türevi bir forecast
  eklenebilir) kapsar.
- `tlab/features/stats.py::rolling_corr` (zaten var, Faz 2) — forecast/enstrüman
  korelasyon tahmini için.
- `bilgi-bankasi/teknik/11_carver_systematic.md`'deki rule-of-thumb tablolar (ORAN-04/06)
  — geri-test verisi yetersizken varsayılan korelasyon kaynağı; `config/carver_
  correlations.yaml` (YENİ, henüz yok) olarak tlab'a taşınmalı.

## Parametreler (modül modül)

### `tlab/portfolio/forecast.py::CombineForecastsParams(BaseParams)`
| Alan | Varsayılan | Kaynak |
|---|---|---|
| `target_abs_forecast` | 10.0 | `11/KURAL-01` |
| `cap` | 20.0 | `11/KURAL-01` |
| `max_diversification_multiplier` | 2.5 | `11/ORAN-02` |
| `correlation_window` | 120 | TASARIM KARARI (kaynak atfı YOK — K3 kitap-metni
  spesifik bir pencere vermiyor, `xsec.rolling_alpha_beta`'nın Faz 8D'de kullandığı
  orta-vadeli pencerelerle tutarlı bir varsayılan seçildi) |

### `tlab/portfolio/sizing.py::PositionSizingParams(BaseParams)`
| Alan | Varsayılan | Kaynak |
|---|---|---|
| `vol_window` | 25 | `11/ORAN-05` (basit hareketli ortalama) |
| `vol_ewma_span` | 36 | `11/ORAN-05` (eşdeğer EWMA — ikisinden biri seçilir,
  `vol_method` parametresiyle) |
| `annualization_sqrt_divisor` | 16.0 | `11/ORAN-05` (256 iş günü varsayımı) |
| `pct_vol_target` | TODO(kullanıcı) | `11/DISIPLIN-03` Tablo 25/26'dan, kullanıcının
  gerçekçi geriye-dönük Sharpe tahminine göre SEÇİLMELİ — sabit bir varsayılan
  UYDURULMADI |
| `trading_capital` | TODO(kullanıcı) | Hesap büyüklüğü, veri KAYNAĞI YOK |

### `tlab/portfolio/allocation.py::HandcraftParams(BaseParams)`
| Alan | Varsayılan | Kaynak |
|---|---|---|
| `recompute_frequency` | "quarterly" | TASARIM KARARI — K3 kitabı bir "her ne kadar sık
  isterseniz" notu dışında kesin bir frekans vermiyor; üç aylık, korelasyonun "zamanla
  çok değişmediği" gözlemiyle (`11/DISIPLIN-08`) tutarlı makul bir varsayılan |
| `correlation_source` | "rolling_backtest" \| "rule_of_thumb" | `11/KURAL-05` adım 1 |
| `sharpe_adjustment` | False | `11/DISIPLIN-07` — varsayılan KAPALI (kitap: "<10 yıl
  veriyle Sharpe farkına göre ayarlama YAPMA") |

### `tlab/portfolio/risk.py::PortfolioRiskParams(BaseParams)`
| Alan | Varsayılan | Kaynak |
|---|---|---|
| `max_diversification_multiplier` | 2.5 | `11/ORAN-02`/`ORAN-03` |
| `position_inertia_pct` | 0.10 | `11/"FORMÜL ZİNCİRİ"` adım 13 |

### `tlab/backtest/metrics.py` genişletmesi — `SpeedLimitParams(BaseParams)`
| Alan | Varsayılan | Kaynak |
|---|---|---|
| `cost_budget_fraction` | 1/3 | `11/DISIPLIN-12` |
| `realistic_precost_sr` | 0.40 (staunch) / 0.25 (semi-auto) | `11/ORAN-10` |

## Durum makinesi

Bu katman, önceki fazların indikatörlerinden FARKLI bir doğaya sahiptir: `forecast.py`/
`sizing.py`/`risk.py` HER BARDA yeniden hesaplanan SÜREKLİ bir zincirdir (klasik
non-repaint sözleşmesi geçerli — yalnızca t ve öncesi), ama `allocation.py` (handcrafting)
PERİYODİK (ör. üç ayda bir) yeniden hesaplanan, iki hesaplama ARASINDA SABİT kalan bir
ADIM FONKSİYONUDUR (piecewise-constant). Bu ikisinin KARIŞTIRILMAMASI kritik — aşağıdaki
durumlar tanımlanır:

- **`forecast.py`/`sizing.py`/`risk.py` (sürekli):** her bar `t` için: girdi forecast'lar
  (t ve öncesi) → kombine forecast(t) → pozisyon(t). Repaint testi: standart
  `tlab/testing/repaint.py::repaint_test` (walk-forward eşitlik) uygulanır — GERİYE
  BAKIŞ YOK.
- **`allocation.py` (periyodik, ADIM fonksiyonu):** ağırlıklar yalnızca
  `recompute_frequency` noktalarında YENİDEN hesaplanır (ör. her çeyrek başı) ve
  bir SONRAKİ recompute noktasına kadar SABİT kalır. **Non-repaint çevirisi:** bir
  `t` barındaki ağırlık, YALNIZCA en son GEÇMİŞ recompute noktasında (t'den önce veya
  t'de) hesaplanmış olan ağırlık olmalıdır — GELECEKTEKİ bir recompute'un ağırlığı asla
  geriye yazılmaz. Bu, `structure.golden_zone`'un "bant, bir SONRAKİ pivot doğana kadar
  sabit kalır" desenine BENZER bir "extend-only sabit değer" mantığıdır (Faz 8C).
  Repaint testi: STANDART `repaint_test` DOĞRUDAN uygulanamaz (ağırlıklar bir seri
  değil, ayrık zaman noktalarında üretilen bir sözlük dizisidir) — YENİ bir hedefli test
  deseni gerekir (bkz. Test fixture tarifi).

## Kabul kriterleri

1. `forecast.py::combine_forecasts()` çıktısı, tek bir kural verildiğinde (forecast_
   weights={rule: 1.0}) GİRDİ forecast'ın (scalar/cap zaten uygulanmış olduğu
   varsayılarak) AYNISINI döndürmeli (diversification multiplier=1.0, tek varlık).
2. `sizing.py::compute_subsystem_position()`, K3'ün Bölüm 2 örneğindeki (WTI ham petrol,
   £1.000.000 hedef, forecast=-6) SAYISAL değerlerle (volatility scalar=93.52,
   subsystem position=-56.11) elle inşa edilmiş bir fixture üzerinde TAM eşleşmeli
   (±1e-6 tolerans).
3. `allocation.py::handcraft_weights()`, K3'ün 3-varlık örneğindeki (US 20yıl bond/S&P
   500/NASDAQ, korelasyon 0.0/0.9/0.0 → Tablo 8 satır 6) ağırlıkları (%27/%46/%27,
   sonra grup-seviyesi çarpımla %50/%25/%25) TAM üretmeli.
4. `risk.py::diversification_multiplier()`, ORAN-03'ün kesin formülü (`1/sqrt(W·H·Wᵀ)`)
   ile Tablo 18'in yaklaşık değerleriyle (2 varlık, 0.5 korelasyon → 1.15) ±0.02
   toleransla eşleşmeli.
5. `repaint_test` (sürekli katman) 0 mismatch.
6. Periyodik `allocation.py` için YENİ `allocation_repaint_test` (aşağıda tarif
   edilen): bir `t` barındaki ağırlık, `t`'den SONRAKİ veri eklenip yeniden
   hesaplandığında DEĞİŞMEMELİ.

## Test fixture tarifi

**Pozitif (forecast.py):** iki EWMAC varyasyonunun (`ewmac_2_8`, `ewmac_4_16`) elle
üretilmiş, KISMEN korelasyonlu iki seri fixture'ı — `tests/testing/fixtures.py`
desenine uygun `make_trend`/`make_zigzag` yerine YENİ bir
`make_correlated_forecast_pair(corr, n)` yardımcı fonksiyonu (Faz 10'da eklenir).
Beklenen: diversification multiplier ORAN-03 formülüyle elle hesaplanan değere eşit.

**Negatif (forecast.py):** forecast_weights toplamı %100'den FARKLI verilirse
`ValueError` (KURAL-02'nin "ağırlıklar toplamı 100 olmalı" şartı).

**Pozitif (sizing.py):** K3 Bölüm 2 örneğinin BİREBİR sayısal fixture'ı (kabul
kriteri #2).

**Pozitif (allocation.py):** K3 Bölüm 3'ün 3-varlık VE 16-varlık (Tablo 10/11)
örneklerinin İKİSİ de fixture olarak kodlanmalı (çok seviyeli gruplamayı test etmek
için 16-varlık örneği ZORUNLU).

**Periyodik repaint testi (`allocation_repaint_test`, YENİ, `tlab/testing/`e eklenir):**
`universe_repaint_test`in (Faz 8D) AYNI "kesik ⊆ tam" mantığı, ama SERİ yerine
{recompute_tarihi: ağırlıklar} sözlüğü üzerinde: her kesim noktasında (yalnızca o ana
kadarki recompute noktaları hesaplanır) üretilen ağırlıklar, tam koşunun o ana kadar
ürettiği ağırlıklarla BİREBİR eşleşmeli.

## Görselleştirme sözleşmesi

Bu katman `IndicatorResult`/`Signal` ÜRETMEZ (bir tarama/sinyal indikatörü değil, bir
portföy hesap katmanı) — bu yüzden `tlab/viz/renderer.py`'ye YENİ bir çizim yolu
GEREKMEZ. Önerilen (opsiyonel, Faz 10'un kendisi kapsamında DEĞİL, ayrı bir görselleştirme
takip işi): `tlab/viz/universe_charts.py`'nin (Faz 8D) desenini izleyen YENİ bir
`render_portfolio_positions()` — enstrüman × pozisyon büyüklüğü çubuk grafiği, benzer
şekilde `IndicatorResult`+df yerine bir `dict[str, float]` (nihai portföy pozisyonları)
üzerinde çalışır.

## Kenar durumlar

- **Yetersiz geçmiş (korelasyon tahmini için):** `correlation_window` kadar veri yoksa
  `forecast.py`/`allocation.py` rule-of-thumb tablolara (ORAN-04/06) DÜŞMELİ, hata
  fırlatmamalı — Faz 8D'nin `min_history_bars` guard deseniyle TUTARLI (semboller
  sessizce evren-dışı bırakılmaz, YALNIZCA korelasyon kaynağı değişir).
- **Negatif korelasyon:** ORAN-03/07 formüllerine girmeden ÖNCE SIFIRA taban değeri
  verilmeli (K3'ün AÇIKÇA belirttiği şart, `11/ORAN-03`).
- **Tek enstrümanlı/tek kurallı portföy:** diversification multiplier=1.0, handcrafting
  ağırlığı=%100 — dejenere durum, özel kod dalı GEREKMEZ (formüller doğal olarak bu
  sonucu üretir).
- **VERİ BAĞIMLILIĞI — `trading_capital`/`pct_vol_target`:** bu ikisi tlab'ın hiçbir
  mevcut veri katmanında YOK (kullanıcının hesap büyüklüğü/risk toleransı — dışsal bir
  girdi). Faz 10 implementasyonu bunları `config/portfolio.yaml` (YENİ) üzerinden
  okumalı, koda GÖMÜLMEMELİ.
- **VERİ BAĞIMLILIĞI — `block_value`/enstrüman çarpanları:** BIST hisseleri için block
  value=1 (hisse başına, kaldıraçsız) basitleştirmesi YAPILABİLİR (Carver'ın örnekleri
  vadeli işlem sözleşmeleri için — tlab şu an yalnızca SPOT hisse/kripto verisiyle
  çalışıyor, `AxiQuant_Research_Lab`'ın vadeli işlem/kaldıraç mantığı BU projenin
  kapsamı DIŞINDA, ayrı bir proje).
