# ABCD Formasyon Entegrasyonu — Mimari Kararlar (Faz 0)

Kaynak: `C:\Users\Samet\Desktop\abcd-project` (Pine v6 göstergesi +
Python portu). Hedef: bilanco-radar'a "Formasyonlar" adlı yeni, deneysel bir
Telegram özelliği olarak entegrasyon. Bu doküman, entegrasyon öncesi
çözülmesi zorunlu 4 mimari çatışmanın kararını ve `kod-gelistirici` +
`quant-uzmani` agent denetiminin sonucunu kayıt altına alır.

## Karar 1 — Modül izolasyonu (K2 çatışması)

`src/analysis/technical.py`'nin K2 kuralı ("Al/Sat/Tut sinyali ÜRETMEZ")
sadece o modülü bağlar, `src/analysis/` katmanının tamamını değil — ama bu
metinsel bir teknisliktir, ileride yanlış genellenebilir. Bu yüzden:

- Yeni, tamamen izole modül: `src/analysis/abcd_pattern.py`.
- Modül docstring'i AÇIKÇA şunu belirtir: *"Bu modül src/analysis/'in
  genel felsefesinden (skorsuz/sinyalsiz, bkz. technical.py K2) BİLİNÇLİ bir
  sapmadır — yönlü BUY/SELL sinyali + TP/SL üretir. Bu bir istisna, bir
  emsal DEĞİLDİR."*
- Kullanıcıya gösterilen her yerde (kart, mesaj) "bu deneysel bir sinyal
  üreticidir, temel/teknik-olgu skorlarından bağımsızdır" ayrımı net yapılır.

*(kod-gelistirici denetimi: onaylandı.)*

## Karar 2 — Decimal vs float sınırı

Proje geneli Decimal-only (Kural 2/3). `abcd_pattern.py` / `abcd_backtest.py`
/ `abcd_data.py` bu kuralın **kapsamı sınırlı, gerekçeli bir istisnasıdır**:

- Bu üç modül tamamen **float + pandas/numpy** kullanır — Pine parity
  zorunluluğu (abcd-project `CLAUDE.md` kural 1: TradingView'in float64
  aritmetiğiyle bar-bar eşleşme). Decimal'e çevirmek, zaten test edilmiş
  Pine-parity davranışından (RMA/ATR seed, strict pivot karşılaştırması)
  sessiz sapma riski taşır.
- Float değer **hiçbir zaman** Decimal tipli dataclass'lara, `scorer.py`'ye
  veya `calculator.py`'ye sızmaz. Decimal'e/string'e dönüşüm **sadece**
  render sınırında (`src/render/abcd_card.py` context builder) olur —
  `card.py`/`technical_card.py` ile aynı sınır ilkesi.
- Her üç modülün docstring'i bu istisnayı açıkça "quaxis-mimari Kural 3'e
  kapsamı sınırlı, gerekçeli bir istisna" olarak belgeler.

*(kod-gelistirici denetimi: onaylandı, şartla.)*

## Karar 3 — BIST veri katmanı

`src/fetchers/isyatirim.py::fetch_price_history` SADECE günlük bar döner ve
`open` her zaman `None`'dır (bkz. `price_history.py` modül notu) — ABCD'nin
ihtiyaç duyduğu 60/120/240dk intraday + gerçek açılış fiyatını hiç
sağlayamaz. Bu gerçek bir veri boşluğu, gereksiz tekrar değildir.

- Yeni, bağımsız veri katmanı: `src/fetchers/abcd_data.py` —
  abcd-project'in `abcd/data.py::YFinanceProvider`'ının taşınmış/adapte
  edilmiş hali. **Sadece yfinance** (proje sahibinin kararı — tvDatafeed'in
  git-bağımlılığı ve resmi olmayan API riski alınmıyor).
- Parquet cache: `data/abcd_cache/{symbol}_{tf}.parquet`.
- **Bilinen sınır (dokümante edilecek, blocker değil):** yfinance intraday
  (1h ve türevleri) ~730 günle sınırlı — 60/120/240dk zaman dilimlerinde
  backtest derinliği ~2 yılla sınırlı kalır; sadece 1D/1W tam derinlik alır.
  Kart/rapor metinlerinde bu sınır belirtilir.

*(kod-gelistirici denetimi: onaylandı.)*

## Karar 4 — Yeni bağımlılıklar

`requirements.txt`'e eklenir (projenin mevcut alt-sınır `>=` stiliyle):

```
pandas>=2.0
numpy>=1.26
pyarrow>=15
yfinance>=0.2
```

Sadece yukarıdaki 3 yeni modülde kullanılır; projenin geri kalanı etkilenmez.

*(kod-gelistirici denetimi: onaylandı.)*

## Sembol evreni

abcd-project'in kendi `abcd/universe.py`'si (tradingview-screener paketine,
yani BAŞKA bir resmi olmayan API'ye bağımlı — Karar 3'ün ilkesiyle çelişir)
**kullanılmaz**. Bunun yerine mevcut `src/db/repository.py`'deki
`Company.market == "BIST"` sorgusu (satır ~568) kullanılır.

*(kod-gelistirici canlı doğrulaması: DB'de 657 BIST şirketi, 615'inde
`last_updated` dolu (en yeni: 2026-08-14), plain ticker formatı — `.IS`
soneki yok — `YFinanceProvider._yf_symbol`'ın eklediği `.IS` ile uyumlu.
Ölü/işlem görmeyen birkaç ticker olası ama scanner'ın per-symbol hata
toleransı (`errors` dict) bunu zaten sessizce eler, blocker değil.)*

## Backtest metodolojisi — quant-uzmani denetiminin sonucu

abcd-project'in `backtest.py` motoru (event-driven, R-multiple bazlı
expectancy/profit-factor, look-ahead önleyici `fill_ref`/`_already_beyond_at_signal_close`)
temel olarak sağlam, ama kullanıcının istediği büyük grid (5 tf × 2 yön ×
2 para birimi = 20+ hücre, parametre taraması eklenirse yüzlerce) için
**iki ek disiplin zorunlu**:

1. **Çoklu karşılaştırma / overfitting riski.** `min_trades=30` eşiği rapor/
   karar amaçlı kullanım için YETERSİZ (R-multiple dağılımları çarpık, n=30'da
   1-2 aykırı işlem expectancy'i domine edebilir; havuzlanan işlemler de
   ortak rejim dönemlerinde korelasyonlu, efektif n daha küçüktür).
   → **`abcd_backtest.py`/`scripts/abcd_research.py`'de:** rapor/"en
   verimli koşul" iddiaları için eşik ≥100 işleme çıkarılır; 30 sadece
   "hücreyi hiç gösterme" alt sınırı olarak kalır. Grid boyutuna göre
   Bonferroni-tipi düzeltme uygulanır. Seçilen en iyi konfigürasyon ayrı bir
   out-of-sample dönemde/sembol alt-kümesinde doğrulanır.
   Her rapor satırında `n_trades`, `profit_factor`/`expectancy_r` ile AYNI
   hücrede zorunlu gösterilir — bu projenin kendi `spec_kapsam_cezali_skor.md`
   /`quant_denetim_01.md`'deki "küçük n'de sahte kesinlik" disiplininin
   (MIN_SECTOR_N, kapsam cezası) doğrudan devamıdır. Eşik altı hücreler
   ASLA sessizce atılmaz/gizlenmez, "GÜVENSİZ (n=12)" gibi açıkça etiketlenir.

2. **TL vs USD ayrımının gerçek anlamı.** `to_usd()` fiyatları USDTRY'ye
   böldükten SONRA `detect()` yeniden çağrılıyor → pivotlar (A/B/C/D) TL ve
   USD serilerinde FARKLI çıkabilir. Bu, **aynı sinyalin döviz-ayarlı
   getirisi DEĞİL, USD-payda grafiğinde tespit edilen BAĞIMSIZ bir sinyal
   kümesidir**. Rapor/kart metinlerinde bu açıkça "USD-payda grafiğinde
   bağımsız tespit" olarak etiketlenir, "aynı sinyalin enflasyondan
   arındırılmış hali" gibi yanıltıcı ifade KULLANILMAZ.

## Sonuç

4 mimari karar + sembol evreni kararı onaylandı (şartlarıyla). Backtest
fazı (Faz 3/7) yukarıdaki 2 ek disiplinle genişletilecek. Faz 1'e (veri
katmanı) geçiliyor.
