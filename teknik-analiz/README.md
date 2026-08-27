# Teknik Lab (tlab)

BIST ve NASDAQ hisseleri için Python tabanlı, **non-repainting** teknik
analiz / indikatör laboratuvarı. 4 saatlik ve Günlük zaman dilimlerinde
çoklu-indikatör tarama motoru; tekil hisse için tam görsel çıktı hedefler.
Kardeş proje **Bilanço Radar** (temel analiz) ile ileride tek uygulamada
birleşecek — bu yüzden çekirdek mantık arayüzden tamamen bağımsız tasarlanır.

## Non-repainting sözleşmesi (müzakereye kapalı)

`signal(t)` değeri yalnızca `t` ve öncesindeki barların verisiyle hesaplanır
ve `t` sonrasında hiçbir zaman değişmez. Bu üç mekanizmayla garanti altına
alınır:

1. **Zaman damgası kuralı** — bir sinyal, bilginin *elde edildiği* barın
   tarihini taşır (`detected_at`), olayın *gerçekleştiği* barın tarihini
   değil (`bar_time`). Pivot tabanlı hesaplarda sinyal tarihi = pivotun
   ONAYLANDIĞI bar, pivot barının kendisi değil.
2. **Walk-forward eşitlik testi** (`tlab/testing/repaint.py`) — her
   indikatör, tam seri ile farklı noktalarda kesilmiş serilerin ürettiği
   sonuçların birebir örtüştüğü otomatik testten geçmeden registry'ye
   kaydedilemez.
3. **Statik lint** (`tlab/testing/lint_lookahead.py`) — `df.shift(-n)`,
   `rolling(center=True)`, `argrelextrema`/`find_peaks` sonucunu doğrudan
   sinyal barına yazma gibi yasak/riskli desenleri arar.

Yasak API'ler: `df.shift(-n)`, `rolling(center=True)`, geleceğe bakan
interpolasyon, açık (kapanmamış) barla sinyal üretmek.

## Katman ayrımı

```
Veri → Özellik (swing, fib, pivot) → İndikatör → Tarayıcı → Depo → Görselleştirme
```

Her ok tek yönlü. İndikatörler veri kaynağını bilmez; tarayıcı indikatörün iç
yapısını bilmez; görselleştirme hesap yapmaz.

## Deterministiklik

Aynı veri + aynı parametre = bit-bit aynı sonuç. Parametreler frozen
dataclass; sonuç kayıtları `params_hash` taşır; global durum ve `random` yok.

## Dizin yapısı

```
tlab/
├── core/         # types.py (Signal, Level, Line, Box, Polygon, Marker,
│                 #   IndicatorResult), indicator.py (BaseIndicator, Registry),
│                 #   params.py, errors.py
├── data/         # sağlayıcılar, cache, resample, takvim (Faz 1)
├── features/     # swing, fibonacci, trendline, zone, volume profile (Faz 2)
├── indicators/
│   ├── harmonics/schools/   # Carney, Pesavento, Gilmore, Cypher, Nen Star,
│   │                        #   Navarro 200, 5-0 (Faz 3)
│   ├── structure/           # swing+fib+ABCD, fiyat yapısı (Faz 4)
│   ├── pairs/                # relatif momentum / arbitraj (Faz 5)
│   ├── trend/, momentum/     # MA sistemleri vb. (Faz 8+)
├── scanner/      # evren × timeframe × indikatör tarama motoru, EOD (Faz 6)
├── backtest/     # pair trading backtest motoru (Faz 5)
├── viz/          # Plotly renderer, temalar, EOD raporu (Faz 7)
└── testing/      # fixtures.py, repaint.py, lint_lookahead.py

tests/            # pytest testleri
config/           # settings.yaml, evren listeleri (Faz 1)
data/             # git dışı — parquet cache
outputs/          # git dışı — tarama sonuçları, raporlar
```

## Kod standardı

Python 3.11+, type hints zorunlu, pandas/numpy, `dataclass` (pydantic yok),
`ruff` + `mypy` temiz, `pytest`. Docstring'ler Türkçe, kod tanımlayıcıları
İngilizce. Kullanıcıya dönen etiket metinleri Türkçe (AKTİF, TAMAMLANDI,
Kırılım, Temas, Direnç, Destek).

## Geliştirme

```bash
pip install -e ".[dev]"
make test          # pytest -q
make lint           # ruff + statik lookahead denetimi
make typecheck       # mypy
make repaint-all     # lint + repaint testleri
```
