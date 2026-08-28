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

## Görselleştirme (Faz 7)

`tlab plot --symbol TCELL --tf 1d --indicator structure.price_structure [--theme
auto|dark|light] [--last-n 300] [--out dosya.html|.png] [--open]` — tek bir
(sembol, tf, indikatör) grafiğini üretir (`tlab/viz/renderer.py`, hesap yapmaz,
yalnızca `IndicatorResult` primitiflerini çizer). Pair indikatörler için
`--symbol Y/X` (ör. `TCELL/ISCTR`). `.png` çıktısı `kaleido` gerektirir.

`tlab report --run latest --market bist [--generate-charts]` — EOD run'ı için
özet HTML raporu (`tlab/viz/report.py`): durum sayaçları, önceki run'a göre
yeni sinyal/durum geçişi/repaint alarmı, indikatör/tf sekmeleri, her sinyal
satırından tekil grafiğe link. Grafikler **lazy** üretilir (`ensure_chart()`,
yalnızca ilk tıklanışta/`--generate-charts` ile önceden); her biri
`include_plotlyjs="cdn"` kullanır (dosya başına ~3MB'lık plotly.js'i tekrar
gömmemek için).

### Referans görsel kontrol listesi

Faz 7 kabul kriteri, `images/`'teki 6 referans ekran görüntüsünün renderer ile
yeniden üretilebilir olmasıydı. Gerçek veriyle (`outputs/samples/`, TCELL/
ALARK/TCELL-ISCTR) üretilen sonuç, öğe öğe:

| Görsel | Öğe | Durum |
|---|---|---|
| 1 (pair, dark) | Normalize fiyat (Y mavi/X gri) | ✅ |
| 1 | Tutulan dönem gölgeleri (yeşil=Y, mavi=X) | ✅ (Faz 7'de bulunan gerçek bir hata düzeltildi — `add_vrect(row=...)`, o satıra ilk trace eklenmeden çağrılırsa Plotly sessizce hiçbir şey çizmiyordu) |
| 1 | Portföy vs Buy&Hold + başlangıç çizgisi | ✅ |
| 1 | Z-skoru + eşikler + AL kutulu etiketler | ✅ |
| 1 | Başlık formatı ("SİNYAL \| SEMBOL AL \| Z: a -> b \| tarih") | ✅ (yakın; kesme metni — "Y Ucuz -> Dönüş Onaylandı" — payload'da var ama başlığa join edilmedi, GAP) |
| 2 (price_structure, light) | Trendline (solid + "(Temas:N)" etiketli dashed uzatma) | ✅ |
| 2 | Direnç/Destek bölgeleri (sarı/mavi dolgu) + Konsolidasyon kutuları | ✅ |
| 2 | Hacim profili + Value Area (yeşil/mavi) + Gaussian eğri | ✅ |
| 2 | Hacim + MA paneli, MACD paneli + kesişim işaretleri | ✅ |
| 3 (swing_fib_abcd, light) | Swing çizgisi + HH/HL/LH/LL etiketleri (renkli) | ✅ |
| 3 | AB=CD hedef (D) seviyeleri, yön renkli (yeşil/kırmızı) | ⚠ KISMİ — referans C'den D'ye ÇAPRAZ bir izdüşüm çizgisi gösteriyor; renderer hesap yapmadığı için (Level yalnızca tek bir yatay fiyat taşır, C'nin fiyatını taşımaz) bunun yerine YATAY, C barından başlayıp tamamlanma/geçersizleşme barında biten bir seviye çiziliyor — aynı bilgi (hedef fiyat + yön), farklı geometri |
| 3 | "[TAMAM]" durum eki | ❌ GAP — Level etiketi yalnızca fiyatı taşıyor (`D (hedef): 106.75`); durum (`completed`/`invalidated`) ayrı bir Signal'de var ama etikete join edilmedi |
| 3 | Fibonacci retracement/extension seviyeleri (oran-renkli) | ✅ |
| 4 (metrik tablosu, dark) | Başlık/alt başlık + METRİK/DEĞER/DURUM tablosu, pozitif/negatif satır rengi | ✅ (`tlab/viz/table.py`, `outputs/samples/tcell_isctr_metrics_table.png`) |
| 5 (harmonik, light) | XAB/BCD üçgenleri (Polygon, yön renkli dolgu) | ✅ |
| 5 | X→B kesikli çizgi + sınırlı uzatma | ✅ (Faz 7'de bulunan gerçek bir hata düzeltildi — ham eğim son bara kadar projekte edilince kısa/dik bacaklarda fiyat ekseni gerçek dışı büyüyordu; uzatma artık bacağın kendi uzunluğunun en fazla 3 katıyla sınırlı) |
| 5 | PRZ üst/alt seviyeleri (dotted) | ✅ |
| 5 | "D: fiyat [DURUM]" kutulu etiket | ✅ (`scanner_indicator.py` zaten Türkçe durum etiketini metne gömüyor) |
| 5 | Ara Fibonacci merdiveni (0.382/0.618/0.786/1.272/1.618 çizgileri) | ❌ GAP — `HarmonicIndicator` bunları şu an Level olarak üretmiyor (yalnızca PRZ üst/alt); renderer hesap yapmadığı için eklenemedi, ileride indikatöre eklenebilir |
| 6 (EOD tarama listesi, dark metin) | Yeni sinyal / kategori bazlı liste (YENİ AL / DEVAM EDEN FIRSAT / BÖLGEYE YAKLAŞIYOR) | ⚠ KISMİ — `tlab report`, indikatör/tf sekmeleri + durum renkli tablo olarak üretiyor (bkz. yukarıdaki HTML rapor); pair'e özel 3 kademeli yakınlık kategorisi (`relative_momentum.py::_zone_state`, Faz 6'da zaten hesaplanıyor) rapora AYRI bir sekme/gruplama olarak YANSITILMADI — GAP, küçük bir takip işi |

Gerçek çok-yıllık veri, referans mockup'lardan daha YOĞUN görünebilir (ör.
TCELL/ALARK'ın onlarca ABC üçlüsü/harmonik adayı üretmesi) — bu bir render
hatası değil, `--last-n` ile daha dar bir pencereye (ör. 150-300 bar) veya
daha az volatil bir sembole odaklanarak azaltılabilir.
