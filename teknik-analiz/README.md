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

## Gün Sonu (EOD) Zamanlaması

`tlab eod --market bist` her gün BIST kapanışından (18:00 Europe/Istanbul) sonra,
tercihen **18:15**'te (kapanış sonrası veri sağlayıcı gecikmesi için tampon)
koşulmalıdır. `run_eod()` kendi takvim kontrolünü yapar (hafta sonu/resmi tatil
günlerinde otomatik atlanır) — zamanlayıcı yalnızca "her gün 18:15'te dene" kadar
basit olabilir.

### Linux/macOS — cron

```cron
# crontab -e
15 18 * * 1-5 cd /path/to/teknik-analiz && TZ=Europe/Istanbul .venv/bin/tlab eod --market bist >> outputs/logs/cron.log 2>&1
```

### Linux — systemd timer

```ini
# /etc/systemd/system/tlab-eod.service
[Unit]
Description=tlab EOD tarama

[Service]
Type=oneshot
WorkingDirectory=/path/to/teknik-analiz
Environment=TZ=Europe/Istanbul
ExecStart=/path/to/teknik-analiz/.venv/bin/tlab eod --market bist
```

```ini
# /etc/systemd/system/tlab-eod.timer
[Unit]
Description=tlab EOD günlük tetikleyici

[Timer]
OnCalendar=Mon..Fri 18:15 Europe/Istanbul
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now tlab-eod.timer
```

### Windows — Görev Zamanlayıcı (Task Scheduler)

```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\teknik-analiz\.venv\Scripts\tlab.exe" `
    -Argument "eod --market bist" -WorkingDirectory "C:\path\to\teknik-analiz"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 18:15
Register-ScheduledTask -TaskName "tlab-eod-bist" -Action $action -Trigger $trigger `
    -Description "tlab gun sonu (EOD) taramasi"
```

(GUI eşdeğeri: Görev Zamanlayıcı → Temel Görev Oluştur → Haftalık, Pzt-Cum 18:15 →
Program Başlat → yukarıdaki `tlab.exe` yolu + `eod --market bist` argümanı.)

Aynı gün ikinci bir tetikleme (ör. zamanlayıcı çakışması) `run_eod()` tarafından
otomatik atlanır (`status: "skipped_existing"`) — `--force` verilmedikçe.
