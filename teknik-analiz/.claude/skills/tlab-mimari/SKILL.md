---
name: tlab-mimari
description: teknik-analiz/tlab projesinin çekirdek mimarisi — katman ayrımı, IndicatorResult sözleşmesi, Signal(bar_time, detected_at, state), NON-REPAINT kuralları ve yasak API listesi, registry-repaint ilişkisi, mevcut faz durumu. teknik-analiz altında herhangi bir koda dokunmadan ÖNCE oku — agentların ve oturumların teknik işlerde İLK okuyacağı dosya.
---

# tlab Mimarisi

`teknik-analiz` (paket adı `tlab`) BIST/NASDAQ için Python tabanlı, non-repainting bir
teknik indikatör laboratuvarıdır. Bu skill, `teknik-analiz/README.md` ve `tlab/core/`
içindeki sözleşmenin damıtılmış halidir — kod değiştiğinde bu skill de güncellenmeli.
**Bu proje QuaxisLabs temel analiz koluyla (bilanco-radar) aynı repoda paralel yaşar ama
KENDİ anayasasına tabidir** — Decimal zorunluluğu, "LLM sayı üretmez" gibi temel analiz
kuralları burada GEÇERSİZDİR; bunun yerine aşağıdaki non-repaint sözleşmesi geçerlidir.

## NON-REPAINT sözleşmesi (müzakereye kapalı)

`signal(t)` değeri yalnızca `t` ve öncesindeki barların verisiyle hesaplanır, `t`
sonrasında ASLA değişmez. Üç mekanizmayla garanti altına alınır:

1. **Zaman damgası ayrımı** — `Signal` dataclass'ı iki zaman taşır:
   - `bar_time`: olayın/pivotun *ait olduğu* bar
   - `detected_at`: bilginin *fiilen elde edildiği* bar (`detected_at >= bar_time` zorunlu,
     `Signal.__post_init__` bunu doğrular ve ihlalde `OHLCVError` fırlatır)
   Pivot tabanlı hesaplarda sinyal tarihi = pivotun ONAYLANDIĞI bar, pivot barının kendisi
   değil (örn. `left=3, right=3` pivot penceresinde, pivot barı `i` ise `confirmed_idx = i+right`).
2. **Walk-forward eşitlik testi** (`tlab/testing/repaint.py::repaint_test`) — bir
   indikatör, tam seri ile farklı noktalarda kesilmiş serilerin ürettiği sonuçların
   `bar_time`/`detected_at`/`direction`/`state` ve payload'da birebir eşleştiğini
   doğrulamadan `Registry.register()`'a KABUL EDİLMEZ (bkz. aşağıda Registry).
3. **Statik lint** (`tlab/testing/lint_lookahead.py`, CLI: `tlab lint`) — yasak/riskli
   desenleri tarar.

**Yasak API'ler / desenler:**
- `df.shift(-n)` (negatif shift — ileri bakış)
- `rolling(center=True)`
- `scipy.signal.find_peaks` / `argrelextrema` sonucunu DOĞRUDAN sinyal barına yazmak
  (bulma barı ≠ onay barı; sonuç kullanılacaksa onay barına kaydırılmalı)
- Geleceğe bakan interpolasyon
- Açık (kapanmamış) bar üzerinden sinyal üretmek — `resample.py` kapalı olmayan barları
  `is_closed=False` işaretler ve varsayılan olarak düşürür

## Katman ayrımı (oklar tek yönlü, geriye import YOK)

```
data → features → indicators → scanner → results → viz
```

- `tlab/data/` — sağlayıcılar (yfinance/csv), takvim (BIST/NASDAQ seans saatleri), resample,
  parquet cache, validasyon. İndikatörler bu katmanı BİLMEZ (sadece OHLCV DataFrame alır).
- `tlab/features/` — SAF fonksiyonlar (swings, fibonacci, trendlines, ranges, zones,
  volume_profile, stats, ma, oscillators, volatility). Yan etkisi yok, df alır/Series-döner.
- `tlab/indicators/` — `BaseIndicator` alt sınıfları; features'ı birleştirip
  `IndicatorResult` üretir (harmonics/, structure/, pairs/, trend/, momentum/).
- `tlab/scanner/` — evren × timeframe × indikatör tarama motoru (henüz boş, Faz 6).
  İndikatörün İÇ yapısını bilmez, sadece `BaseIndicator.__call__` arayüzünü çağırır.
- `tlab/viz/` — Plotly render (henüz boş, Faz 7). HESAP YAPMAZ, yalnızca `IndicatorResult`
  içindeki primitifleri (Level/Line/Box/Polygon/Marker) çizer.

## Çekirdek tipler (`tlab/core/types.py`)

- `Timeframe(str, Enum)`: `H1="1H"` (yalnızca veri katmanı içi), `H4="4H"`, `D1="1D"`
  (indikatörler yalnızca H4/D1 kabul eder)
- `Signal` (frozen): `bar_time, detected_at, direction: Literal["long","short","neutral"],
  state: Literal["pending","active","confirmed","invalidated","completed","expired"],
  score: float (0..1), payload: dict`
- Görsel primitifler (hepsi frozen): `Level(price, label, style, start?, end?)`,
  `Line(points, label, style, extend_right)`, `Box(t0, t1, low, high, label, style)`,
  `Polygon(points, label, style)`, `Marker(t, price, text, kind)`
- `IndicatorResult`: `indicator, version, params_hash, symbol, timeframe, signals, levels,
  lines, boxes, polygons, markers, series: dict[str, pd.Series], last_state: dict`.
  `to_json()`/`from_json()` mevcut. **"Sinyal var/yok" metni YETERLİ DEĞİL** — her
  indikatör görsel kanıt (levels/lines/boxes/polygons/markers) üretmek zorundadır.
- `validate_ohlcv(df)`: tz-aware `DatetimeIndex`, monoton artan, tekrarsız; kolonlar
  open/high/low/close/volume; `high >= max(open,close)`, `low <= min(open,close)`; NaN yok.
  İhlalde `OHLCVError`.

## BaseIndicator / Registry (`tlab/core/indicator.py`)

- `BaseIndicator.__call__(df, context)` sırası: `validate_ohlcv(df)` → `compute(df, context)`
  → sonuç doğrulama: her `signal.bar_time` `df.index` içinde olmalı, `detected_at >=
  bar_time`, `detected_at <= df.index[-1]` (son bardan sonrası = geleceğe bakış şüphesi,
  `ValueError`).
- `Registry.register(indicator_cls, sample_df)`: `sample_df` üzerinde `repaint_test`
  çalıştırır; `report.passed` değilse `RegistryError` fırlatır ve KAYDETMEZ. Registry'e
  kayıtlı olmayan indikatörü scanner çalıştıramaz (Faz 6). **Yani: repaint testinden
  geçmeyen bir indikatör mimari olarak var olamaz, sessizce "riskli ama çalışıyor" durumu
  yoktur.**
- Parametreler `tlab/core/params.py::BaseParams` (frozen dataclass) + `params_hash()`
  (sıralı JSON'un sha1'i) — sonuçlara işlenir, aynı veri+parametre = bit-bit aynı sonuç
  (deterministiklik; global durum/`random` yasak).

## Mevcut faz durumu (özet — tam liste `TeknikLab_Master_Promptlar.md`'de)

| Faz | Durum | İçerik |
|---|---|---|
| 0 | ✅ | İskelet, çekirdek tipler, repaint test altyapısı |
| 1 | ✅ | Veri katmanı (providers, calendar, resample, store, validate) |
| 2 | ✅ | Özellik katmanı (swings, fibonacci, trendlines, ranges, zones, volume_profile, stats, ma, oscillators, volatility) |
| 3 | ✅ | Harmonik formasyon motoru — 8 ekol (carney, pesavento, gilmore, oglesbee_cypher, kerkez_nenstar, beck_navarro200, five_zero, three_drives) |
| 4+ | ⏳ | Yapı indikatörleri, pair momentum, tarama motoru, görselleştirme, vb. — sırayla `TeknikLab_Master_Promptlar.md` |

Bilgi-işleme kolu (K0-K3, paralel) çıktıları `bilgi-bankasi/teknik/` altında; spec'ler
`teknik-analiz/docs/spec/tlab_NN_*.md` altında (bkz. `teknik-analiz-uzmani` agent).

## Komutlar

```bash
cd teknik-analiz
python -m pytest -q -m "not network"
python -m ruff check tlab/ tests/
python -m mypy tlab/
tlab repaint-test <modul:SinifAdi> --data <parquet/csv>   # tek indikatör, walk-forward
tlab lint --root .                                         # statik lookahead denetimi
```

**Not:** `cli.py`'de şu an `repaint-test` TEK bir indikatörü hedefler (`--data` zorunlu);
"tüm registry'yi tek komutla tara" (`--all`) henüz YOK — bazı görev metinlerinde
(`quant-uzmani` agent'ının denetim komutu gibi) `tlab repaint-test --all` geçebilir, bu
Faz 6 (tarama motoru) sonrası eklenmesi planlanan bir kısayoldur. O zamana kadar gerçek
denetim `python -m pytest -q` (tüm `tests/test_*_repaint.py` dosyalarını çalıştırır) +
`tlab lint` ikilisidir.
