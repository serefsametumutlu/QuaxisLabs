# Railway'e Deploy (bot 7/24 çalışsın, PC/terminal açık olmasın)

Bot bir Docker container'ı olarak Railway üzerinde sürekli çalışır; sen sadece
Telegram'dan hisse kodu yazarsın, hiçbir şeyin açık olması gerekmez.

## 1. Railway hesabı ve proje

1. https://railway.app adresinde GitHub hesabınla giriş yap.
2. "New Project" → "Deploy from GitHub repo" → `serefsametumutlu/QuaxisLabs`
   reponu seç.
3. Railway repoyu tarayıp kökte birden fazla proje bulabilir — servisin
   **Root Directory**'sini `bilanco-radar` olarak ayarla (Service → Settings →
   Source → Root Directory). Repodaki `Dockerfile`'ı otomatik algılayıp onunla
   build eder (bkz. `bilanco-radar/Dockerfile`, bu oturumda eklendi).

## 2. Ortam değişkenleri (Variables sekmesi)

Zorunlu (`.env` dosyandaki değerlerin AYNISINI buraya gir, `.env` repoya
gitmiyor):

- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`

Opsiyonel (`config.py`'de zaten makul varsayılanları var, dokunmana gerek yok):
`LOG_LEVEL`, `HTTP_TIMEOUT_SECONDS`, `HTTP_MAX_RETRIES`,
`HTTP_RATE_LIMIT_DELAY_SECONDS`, `KAP_LOOKBACK_DAYS`, `GEMINI_MODEL`,
`GEMINI_TIMEOUT_SECONDS`, `DATABASE_URL`.

## 3. Kalıcı disk (Volume) — ATLAMA, yoksa her deploy'da veritabanı sıfırlanır

Service → Settings → Volumes → "New Volume":
- Mount path: `/app/data`

Bu, SQLite veritabanını (analiz geçmişi, `/son` komutu, önbellekler) ve
üretilen kart PNG'lerini kalıcı tutar. Volume olmadan da bot ÇALIŞIR ama her
yeniden başlatmada (Railway zaman zaman container'ı yeniden başlatabilir)
`data/` klasörü sıfırdan oluşur.

## 4. Deploy ve doğrulama

Railway push'ta otomatik build+deploy eder. Deploy loglarında şunu görmelisin:

```
Bilanço Radar botu başlatılıyor (polling)...
```

Sonra Telegram'dan bota `/start` veya doğrudan bir hisse kodu (örn. `THYAO`)
yaz — PC'nde hiçbir şey açık olmadan kartı alman gerekiyor.

## Notlar

- Bot **polling** modunda çalışıyor (webhook değil) — Railway'de HTTP portu
  açmaya gerek YOK, sürekli çalışan bir worker process olarak deploy olur.
- `main.py` artık ağ kesintilerinde sınırsız yeniden dener (`bootstrap_retries=-1`,
  bkz. `src/bot/telegram_bot.py`) — Railway'in kendi ağı zaten stabil olduğu
  için bu asıl olarak container ilk ayağa kalkarken küçük bir gecikmeye karşı
  bir güvenlik önlemi.
- Yerel bilgisayarında `python main.py` ile AYNI ANDA botu Railway'de de
  çalıştırma — aynı `TELEGRAM_BOT_TOKEN` ile iki süreç birden `getUpdates`
  yaparsa Telegram "409 Conflict" döner ve mesajlar rastgele iki sürece
  dağılır (bkz. `_acquire_single_instance_lock` docstring'i, `telegram_bot.py`).
  Railway'e taşıdıktan sonra yerelde artık botu başlatma.
