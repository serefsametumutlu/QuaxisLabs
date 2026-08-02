# Bilanco Radar

BIST hisseleri icin Telegram uzerinden calisan temel analiz botu. Kullanici bir
hisse kodu yazar; sistem son ceyreklik finansal tablolari ceker, YoY/QoQ
degisimlerini hesaplar, kural tabanli bir motorla 10 uzerinden skor uretir,
Gemini API ile kisa sozel yorum ekler ve son 3 aydaki onemli KAP
bildirimleriyle birlikte koyu temali bir PNG kart olarak Telegram'dan gonderir.

## Kurulum

```bash
cd bilanco-radar
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
copy .env.example .env        # ve API anahtarlarini gir
```

## Calistirma

```bash
python main.py
```

## Test

```bash
pytest tests/ -v
```

## Faz Durumu

- [x] **Faz 1** — Proje iskeleti, config.py, loglama (dosya + konsol), .env
      yonetimi, temel test altyapisi.
- [x] **Faz 2** — `src/fetchers/isyatirim.py`: MaliTablo uc noktasindan
      ceyreklik bilanco/gelir tablosu cekme, XI_29/UFRS/UFRS_K otomatik
      grup tespiti, kumulatif->ceyreklik turetme, standart kalem eslemesi
      (sadece XI_29 dogrulandi). Demo: `python scripts/demo_fetch.py THYAO`.
      `src/fetchers/kap.py`: KAP'in guncel (Next.js) API'sinden bildirim
      cekme (`api/search/combined` + `api/disclosure/members/byCriteria`),
      kural tabanli onem siniflandirmasi, `get_top_disclosures()`. Demo:
      `python scripts/demo_kap.py TAVHL`.
- [x] **Faz 3** — `src/db/models.py`: Company/FinancialPeriod/Disclosure/
      GeneratedCard SQLAlchemy modelleri (PostgreSQL'e gecise hazir,
      `create_engine_and_session()` ile izole engine uretilebilir).
      `src/db/repository.py`: upsert_financials (mukerrer satir OLUSTURMAZ,
      var olan degeri gunceller), get_financials, save_disclosures (url
      benzersizligiyle dedup), get_recent_disclosures, is_data_fresh
      (onbellek kontrolu), save_generated_card. `src/analysis/calculator.py`
      henuz yapilmadi. Test: `pytest tests/test_db.py` (13 test, izole
      SQLite dosyasiyla, gercek data/bilanco_radar.db'ye dokunmaz).
- [x] **Faz 4 (kismi)** — `src/analysis/calculator.py`: LLM'siz saf matematik
      motoru. YoY (gelir tablosu) / QoQ (bilanco) degisim bloklari, marjlar
      (brut/FAVOK/net + puan degisimi), net borc/FAVOK (TTM), cari oran,
      ROE (yillikandirilmis/TTM), borc/ozkaynak, son 5 ceyrek serisi, LLM
      icin yapilandirilmis bulgu listesi. Kenar durumlari: zarar<->kar
      gecisleri (yuzde yerine ozel etiket), sifira bolme, eksik donem
      verisi, banka/sigortada FAVOK otomatik gizlenir (amortisman verisi
      yoksa). `src/analysis/scorer.py` (puanlama motoru) henuz yapilmadi.
      Test: `pytest tests/test_calculator.py` (40 test, esik sinirlari
      dahil elle hesaplanmis degerlerle).
- [x] **Faz 4** — `src/analysis/scorer.py`: kural tabanli, agirlikli 0-10
      puanlama motoru (LLM yok, gerekce metinleri f-string ile uretilir).
      Sanayi/holding varsayilan sablonu (6 bilesen, agirlik toplami %100):
      Nakit Uretimi/FAVOK %25, Kaldirac (net borc/FAVOK) %20, Karlilik %15,
      Buyume %15, Degerleme (F/K + PD/DD) %20, Bilanco Kalitesi %5. Fiyat
      verisi verilmezse Degerleme bileseni atlanir ve agirligi kalan
      bilesenlere orantisal yeniden dagitilir (ayni mekanizma her turlu
      eksik veri icin gecerli). Toplam skora gore rozet: 8+ SAGLAM, 6-8
      DENGELI, 4-6 KARISIK, <4 RISKLI. Esikler/agirliklar tek bir CONFIG
      sozlugunde. Banka (`score_bank`) ve sigorta (`score_insurance`) icin
      basit iskelet sablonlar da eklendi (ROE + degerleme + sektore ozgu,
      henuz fetcher katmaninda olmayan metrikler icin opsiyonel parametreler).
      Demo: `python scripts/demo_score.py` (fiyatli/fiyatsiz iki senaryo,
      bileşen tablosu). Test: `pytest tests/test_scorer.py` (39 test, esik
      sinirlari ve agirlik yeniden dagitimi dahil).
- [x] **Faz 5** — `src/ai/commentary.py`: hazir hesaplanmis rakamlari sozel
      yoruma cevirir. NOT: proje ilk tasarimda Anthropic Claude API'yi
      hedefliyordu; kullanicinin acik tercihiyle bu modul **Google Gemini
      API**'sine yazildi (REST generateContent, responseSchema ile
      yapilandirilmis JSON cikti). `config.py`'de ANTHROPIC_API_KEY/
      CLAUDE_MODEL -> GEMINI_API_KEY/GEMINI_MODEL olarak degistirildi.
      LLM'e HICBIR ham finansal tablo verilmez, sadece calculator/scorer
      ciktisindaki onceden Turkce formatlanmis (format_number_tr /
      format_currency_short) degerler + onemli KAP basliklari gonderilir;
      istemde "verilen sayilarin disinda sayi uretme" kurali acik yazili.
      Hata/yedek mod: ag hatasi/429/5xx'te 2 kez yeniden dene (toplam 3
      deneme), kalici hatada (401/400) hemen birak; JSON parse basarisiz
      OLURSA VEYA yanitta supheli bir metin artefakti (canli Gemini
      yanitinda gozlemlendi: modelin kendi kendine Ingilizce bir "dusunme
      notunu" bir alanin icine sizdirmasi) tespit edilirse BIR KEZ
      duzeltme istemi; tumu basarisiz olursa LLM'siz sablon tabanli
      mekanik ozete (`Commentary.source="fallback"`) duser -- bu fonksiyon
      hicbir kosulda bos donmez/hata firlatmaz. Zarardan kara / kardan
      zarara gecis bulgulari hem LLM istem kurallarinda hem de yedek
      modun kendi onceliklendirme mantiginda her zaman one alinir.
      Demo: `python scripts/demo_commentary.py` (API anahtari yoksa yedek
      modu, varsa gercek Gemini cagrisini gosterir). Test:
      `pytest tests/test_commentary.py` (26 test; JSON guvenligi, retry
      sayaci, 401'de yeniden denenmeme, supheli-artefakt tespiti, yedek
      mod oncelik kurali dahil, httpx.post monkeypatch ile ag istegi
      gondermeden).
- [x] **Faz 6** — `src/render/templates/card.html` (Jinja2) + `src/render/card.py`
      (Playwright chromium, device_scale_factor=2 PNG). Koyu "terminal
      rontgen" estetigi: sistem monospace font yigini (Google Fonts agi
      YOK -- cevrimdisi guvenilir render icin), uc bant (ust/acilis/alt),
      gelir tablosu + bilanco tablosu (renkli degisim sutunu), saf CSS
      mini bar grafikler (negatif ceyrekler kirmizi, sifir cizgisinin
      altinda), artis/azalis sutunlari, 6 bilesenli radar skoru tablosu
      (kullanici geri bildirimiyle rozet metni/basslik seridi kaldirildi,
      sadece sayi + renk ile ifade ediliyor), KAP notu kutusu. Banka/
      sigorta modunda (show_ebitda=False) FAVOK satiri/grafigi acik bir
      kosullu blokla gizlenir. `build_card_context()` domain nesnelerini
      (AnalysisResult/ScoreResult/Commentary) HICBIR sayi hesaplamadan
      duz bir context dict'ine cevirir. Kesif sirasinda `format_number_tr`'i
      "%" onekiyle zincirleyen her yerde (card.py/commentary.py/scorer.py)
      tutarli negatif yuzde bicimi icin `src/formatting.py`'ye paylasilan
      `format_percent_tr()` eklendi (formatting.py'nin hic testi yoktu,
      o da yazildi). Demo: `python scripts/demo_card.py`. Test:
      `pytest tests/test_card.py` + `tests/test_formatting.py` (26+16
      test; biri gercek Playwright PNG uretimini dogrular).
- [x] **Faz 7** — `src/bot/pipeline.py` (yeni orkestrasyon katmani) +
      `src/bot/telegram_bot.py` (python-telegram-bot v21+, async) +
      `main.py`. pipeline.py, Is Yatirim'in ham itemCode'lu verisini
      calculator.py'nin bekledigi standart alanlara cevirip DB'ye o
      sekilde yazar (repository.py'nin "orkestrasyon kataminda yapilacak"
      notunun karsiligi); SADECE XI_29 (sanayi/ticaret) semasi destekleniyor
      -- banka/sigorta/araci kurum (UFRS/UFRS_K) icin acik bir "desteklenmiyor"
      mesaji doner (varsayimsal parser yazilmadi). En guncel donem henuz
      aciklanmamissa bir ceyrek geriye kayip dener, basarili olursa
      kullaniciya inline Evet/Hayir butonuyla onceki donemi sorar. Butun
      senkron/agir isler (fetch, Playwright) `asyncio.to_thread` ile
      sarilir. Kullanici basina dakikada 3 istek siniri + ayni kullanicinin
      isi bitmeden ikinci istek atamamasi (bellek-ici). Komutlar: /start,
      /son (son 5 kart -- NOT: kullanici bazinda degil, bot genelinde;
      GeneratedCard semasinda chat_id yok), /hakkinda. Canli THYAO ile
      uctan uca dogrulandi (gercek Is Yatirim + KAP verisi, gercek Gemini
      yorumu, gercek PNG). Demo: `python scripts/demo_pipeline.py THYAO`
      (Telegram'siz). Test: `pytest tests/test_pipeline.py` (16 test,
      izole tmp_path DB + sahte fetcher'larla) + `tests/test_telegram_bot.py`
      (18 test, ticker normalizasyonu + hiz siniri).
- [x] **Faz 7 (kullanici geri bildirimi sonrasi duzeltmeler)** —
      (1) **Donem tespiti kritik hata duzeltmesi**: canli TAVHL testinde
      sirket, `guess_last_periods()`'un 75 gunluk tutucu tahmininden cok
      daha erken 2. ceyregi acikladigi halde bot hala 1. ceyregi
      gosteriyordu -- tahmin sadece "asiri iyimser" durumu (henuz
      aciklanmamis donem istemek) ele aliyordu, "asiri kotumser" durumu
      (sirket zaten daha yenisini acikladi) hic kontrol etmiyordu.
      `pipeline._find_true_newest_period()` artik tahminin 1-2 ceyrek
      ILERISINI de (bitmis ceyreklerle sinirli) hafif bir problama
      istegiyle kontrol ediyor. Kesif sirasinda bir API tuhafligi da
      bulundu: TEK BASINA bir donem sorulunca (baska donem eklenmeden)
      uc nokta o donem hicbir grupta yoksa TAMAMEN BOS yanit donuyor,
      bu da fetch_financials'i yanlislikla "sirket bulunamadi" sandiriyor
      -- duzeltme, probe isteklerine dogru financial_group + birkac
      bilinen-dolu donemi de ekliyor. (2) **Canli fiyat eklendi**:
      `isyatirim.fetch_latest_price()` (kesfedilen/dogrulanan uc nokta:
      HisseTekil, startdate/enddate DD-MM-YYYY zorunlu, son eleman en
      guncel kapanis) -- supplementary veri, basarisiz olursa kart
      fiyatsiz uretilir. (3) **Kart yeniden tasarlandi**: kullanici
      geri bildirimiyle DIKEY'den YATAY tek-kare (1600px genislik,
      CSS Grid, Fintables tarzi paylasim karti referans alindi) duzene
      gecildi; "BİLANÇO RADAR" markasi kaldirilip ticker kod kendisi
      buyuk/kalin baslik yapildi; fiyat basligin saginda gosteriliyor;
      radar skoru sutunu kompakt (sadece bilesen adi + puan, uzun
      gerekce metni karttan kaldirildi, sadece kod icinde/loglarda kalir).
      Test: `pytest tests/test_pipeline.py` guncellendi (TAVHL senaryosunun
      regresyon testi dahil, 18 test).
- [x] **Faz 8 (degerleme carpanlari + kart okunurlugu)** —
      (1) **Piyasa degeri artik gercekten hesaplaniyor**: `isyatirim.py`'ye
      odenmis sermaye (itemCode `2OA`) eklendi, `pipeline.py` bunu
      `_STOCK_FIELDS`'e ekleyip fiyatla birlikte `calculator.compute_valuation()`'a
      veriyor. Onceden Degerleme bileseni (agirlik %20) fiyat/sermaye hic
      pipeline'a verilmedigi icin HER ZAMAN atlaniyordu -- artik F/K ve
      PD/DD gercek veriyle hesaplanip `scorer.score_industrial()`'a
      besleniyor. (2) **Yeni carpanlar**: `Ratios`'a `net_debt`,
      `ttm_ebitda`, `ttm_revenue`, `ttm_operating_profit`, `ttm_net_income`
      eklendi; yeni `calculator.ValuationMetrics` + `compute_valuation()`
      Piyasa Degeri, Net Borc, F/K, PD/DD, FD/FAVOK, FD/Hasilat, PD/EFK
      hesaplar (BIST'te nominal pay degeri 1 TL oldugu icin sermaye = pay
      adedi varsayimiyla). Kart ustune yeni bir DEGERLEME bolumu eklendi.
      (3) **Kart okunurlugu**: bolum baslik fontlari buyutuldu/kalinlastirildi
      (arka plan vurgusuyla artik kaybolmuyor), gelir tablosu/bilanco
      bolumlerine tam cerceve + daha buyuk tablo fontu eklendi, RADAR SKORU
      panelinde her bilesenin **nominal agirligi** ve kisa gerekcesi artik
      gorunur (kullanicinin "hangi konuya ne kadar puan verdigimiz net
      olmali" talebi). Agirlik/esik gerekceleri `SCORING_METHODOLOGY.md`'de
      belgelendi. Test: `pytest tests/` (243 test, 8 yeni: compute_valuation
      + kart bicimlendirme).
- [x] **Faz 9 (NASDAQ/ABD veri katmani)** — SADECE veri katmani (analiz/kart
      Faz 10'da). `src/fetchers/sec_edgar.py`: SEC EDGAR companyfacts
      uc noktasindan (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`,
      API anahtari gerekmez) NASDAQ/ABD sirketlerinin ceyreklik finansal
      verisini ceker. AAPL (urun sirketi), NVDA (takvim yiliyla ORTUSMEYEN
      mali yil -- Ocak sonu biter) VE JPM (banka, XI_29/UFRS ayrimindaki
      gibi FARKLI kalem seti) ile CANLI dogrulandi (bkz.
      `data/exploration/{AAPL,NVDA,JPM}_ozet_*.txt`). **Kesifte bulunan
      canli hata**: SEC'in `fy`/`fp` alanlari fact'in KENDI donemine gore
      degil, ICINDE GECTIGI dosyalamaya (10-Q/10-K) gore atanmis -- bir
      ceyregin bilancosu HEM "bu ceyrek sonu" HEM "onceki mali yil sonu"
      (karsilastirma) kolonunu AYNI (fy,fp) etiketiyle tasiyabiliyor;
      `_select_best_fact()` bunu 'en buyuk end tarihi' kurallyla ayirt
      eder (regresyon testi: `test_aapl_ardisik_ceyreklerde_bilanco_degeri_TEKRARLANMAZ`).
      Kumulatif->ceyreklik turetme `isyatirim.quarterly_value_from_cumulative`
      ile AYNI ilkeyle (`quarterly_value_from_cumulative_us_gaap`) yapildi.
      `models.Company`'ye `market` sutunu ("BIST"/"NASDAQ", ALTER TABLE ile
      geriye donuk migrate edilir, gercek DB kopyasiyla canli test edildi) +
      `financial_group="US_GAAP"` eklendi; ticker cakisma riski (fetcher
      seviyesinde degil) `repository.TickerMarketConflictError` ile
      SESSIZCE EZMEK yerine REDDEDILEREK ele alindi (bkz. sinif docstring'i --
      composite PK'ye GECILMEDI, olgun BIST kod yolunun kapsam disi riskli
      refactoru olurdu). `pipeline._standardize_to_records_us_gaap()`
      DB'ye XI_29 ile AYNI alan adlariyla yazar. Fiyat: yfinance yerine
      onun da kullandigi ayni genel query1.finance.yahoo.com uc noktasina
      dogrudan httpx ile gidiliyor (stooq CSV CANLI denendi, artik JS
      bot-dogrulamasi donduruyor, REDDEDILDI). Demo:
      `python scripts/demo_fetch_us.py AAPL`. Test: `pytest tests/` (399
      test, 23 yeni: test_sec_edgar.py + test_pipeline.py/test_db.py ek).
- [x] **Faz 10 (NASDAQ/ABD analiz -> skor -> kart hattı)** — Faz 9'un veri
      katmanı analiz/skor/kart'a bağlandı. `calculator.analyze_us()`:
      `analyze()` ile TAMAMEN AYNI `_build_analysis_result()` çekirdeğini
      kullanır (KOPYALANMADI), sadece `currency='USD'` farklıdır (yeni
      `AnalysisResult.currency` alanı, varsayılan `'TRY'` — 399 BIST testi
      ETKİLENMEDİ). FAVÖK: US GAAP'te BIST'teki dar/geniş faaliyet kârı
      ayrımı YOK — `OperatingIncomeLoss + D&A` kullanıldı (CANLI doğrulandı:
      AAPL FY2024 = $134,66 mr, kamuya açık FAVÖK rakamıyla birebir eşleşti);
      `pipeline._standardize_to_records_us_gaap()` bu yüzden
      `operating_profit_ebitda_base`'i `operating_profit` ile AYNI yazar,
      `calculator.ebitda()` hiçbir değişiklik gerektirmeden çalışır. Enflasyon:
      BIST tarafında da reel büyüme düzeltmesi zaten UYGULANMIYOR (bilinen
      sınır B6) — ABD için bu doğru davranış (TÜFE ~%2-4, TL'ye kıyasla
      önemsiz), ek mantık EKLENMEDİ. `scorer.CONFIG['abd_sanayi']`: aynı 7
      bileşen/ağırlık (%100), SADECE değerleme (F/K ucuz 12/makul 20/pahalı
      30/tavan 50, PD/DD ucuz 1,5/makul 3/pahalı 6/tavan 12 — S&P 500 CANLI
      araştırıldı, GuruFocus/Multpl/MacroMicro) ve büyüme (güçlü eşik %15→%10,
      taban −20→−15 — enflasyon farkı) eşikleri kalibre edildi; kaldıraç AYNEN
      korundu (Moody's/S&P kaldıraç bantları evrensel). Gerekçeler:
      `SCORING_METHODOLOGY.md`. `card.build_us_card_context()`:
      `build_card_context()`'in `_line_item_row`/`_build_chart`/
      `_valuation_context` gibi TÜM yardımcılarını `currency_symbol="$"` ile
      ÇAĞIRIR — `card.html` şablonuna HİÇBİR satır EKLENMEDİ (`sector_template:
      "abd"` zaten var olan `{% else %}` — sanayi şeklindeki — dala düşüyor,
      canlı doğrulandı: şablonda hiçbir yerde "₺" hardcode edilmemiş). Mali
      dönem takvim çeyreği yerine "FYyy Çn" (örn. "FY26 Ç3") gösterilir —
      NVDA gibi mali yılı takvim yılıyla örtüşmeyen şirketlerde "1Ç27" gibi
      bir etiket YANLIŞ (uydurma) takvim izlenimi verirdi.
      `commentary.py`: Gemini'ye gönderilen istem metnindeki para birimi
      sembolü artık `analysis.currency`'den okunuyor (CANLI hata bulundu:
      ÖNCEDEN `format_currency_short()` HER YERDE varsayılan "₺" kullanıyordu
      — ABD kartları için Gemini'ye YANLIŞ para birimli rakamlar
      gönderiliyordu, LLM bunu kendi Türkçe özetine SIZDIRABİLİRDİ).
      `run_pipeline(ticker, market="BIST"|"NASDAQ")`: NASDAQ dalında KAP/8-K
      YOK (kapsam dışı, `disclosures_db` her zaman boş liste), İş Yatırım'a
      özgü ileri-probe (`_has_newer_period_available`) SADECE BIST için
      çağrılır (SEC EDGAR zaten her seferinde gerçek en yeni dönemi bulur).
      **CANLI HATA bulundu ve düzeltildi** (`repository.upsert_financials`):
      brand-new bir NASDAQ ticker'ı ilk kez yazılırken Company satırı ÖNCE
      varsayılan `market="BIST"` ile oluşuyor, HEMEN ARDINDAN gelen
      `set_company_info(market="NASDAQ")` bununla ÇAKIŞIYOR ve HER TEK yeni
      NASDAQ ticker'ında `TickerMarketConflictError` fırlatıyordu —
      `upsert_financials(..., market=...)` parametresi eklenerek satır
      BAŞTAN doğru market'le oluşturulacak şekilde düzeltildi. Demo:
      `python scripts/demo_pipeline_us.py AAPL` — AAPL/NVDA/INTC (zarar
      açıklayan şirket, TTM net zarar) ile CANLI uçtan uca doğrulandı;
      üretilen F/K değerleri stockanalysis.com ile karşılaştırıldı (AAPL
      34,97 vs 35,44 — %1,3 fark; NVDA 30,44 vs 30,74 — %1,0 fark; INTC'nin
      TTM net zararı $-11,29 mr, stockanalysis.com'un belirttiği $11,29 mr
      zararla BİREBİR eşleşti) — ikisi de %5 eşiğinin ALTINDA. Test:
      `pytest tests/` (418 test, 19 yeni: test_calculator_us.py +
      test_scorer_us.py + test_card_us.py, hiçbir regresyon yok).
- [x] **Faz 10.1 (veri doğruluğu düzeltmeleri — kullanıcı raporu, 2026-08-02)** —
      Kullanıcı AAPL kartını sosyal medyada paylaşılan gerçek "Q3'26 earnings
      highlights" ile karşılaştırdı ve GELİR TABLOSU'ndaki rakamların (Satışlar
      $364,4 mr) gerçek çeyreklik rakamla ($109,42 mr) UYUŞMADIĞINI bildirdi.
      **Kök neden**: `analyze_us()` BIST'in KÜMÜLATİF (9 aylık YTD) gösterim
      konvansiyonunu miras almıştı — BIST'te doğru (Fintables/Matriks
      konvansiyonu) ama ABD earnings-raporlama kültüründe SADECE tek çeyreklik
      rakam "headline" sayılır. Çeyreklik türetme MATEMATİĞİ zaten baştan
      DOĞRUYDU ($109,417 mr — kullanıcının kaynağıyla 3 kuruş farkla eşleşti);
      sorun SADECE hangi rakamın öne çıkarıldığıydı. **Düzeltme**:
      `_build_analysis_result(..., use_cumulative_display=False)` — `analyze_us()`
      artık GELİR TABLOSU/bulgu listesinde TEK ÇEYREKLİK rakam gösterir,
      `analyze()` (BIST) DEĞİŞMEDİ. **Ek doğrulamalar**: MSFT (Q4, ANNUAL-9AY
      türetme yolu) — $90,01 mr hasılat/$35,77 mr net kâr/$40,6 mr esas
      faaliyet kârı, web araştırmasıyla BİREBİR eşleşti; Alphabet'in
      "$112,1 mr net kâr" gibi olağandışı görünen bir rakamının GERÇEK
      olduğu (tek seferlik $98 mr gerçekleşmemiş yatırım kazancı) canlı
      araştırmayla doğrulandı — VERİ HATASI değildi. **10 resmi NASDAQ
      hissesinin (AAPL/TSLA/NVDA/MSFT/GOOGL/AMZN/META/NFLX/AMD/PYPL) TAMAMI**
      canlı tarandı: hepsinde hasılat/net kâr/toplam varlık/pay adedi doğru
      geliyor; 5'inde (GOOGL/AMZN/META/NFLX/PYPL) "Brüt Kâr" N/A (bu
      şirketlerin XBRL verisinde GrossProfit tag'i güncel dönemde YOK —
      kod hatası değil, bilinen veri sınırı, bkz. `06_BILINEN_SORUNLAR.md`
      B13). **Ayrıca**: META'da Piyasa Değeri/F-K/PD-DD hiç hesaplanamıyordu
      (hem `dei:EntityCommonStockSharesOutstanding` hem `us-gaap:CommonStockSharesOutstanding`
      META'da YOK) — üçüncül yedek (`WeightedAverageNumberOfDilutedSharesOutstanding`,
      dönem ortalaması) eklendi, macrotrends.net ile BİREBİR eşleşti. Şirket
      logoları da düzeltildi: `company_logo.py` TradingView aramasını HER ZAMAN
      "BIST:" öneki ile yapıyordu, bu yüzden hiçbir NASDAQ kartında logo
      görünmüyordu — `market="NASDAQ"` için "NASDAQ:" sonra "NYSE:" fallback
      eklendi (JPM SADECE NYSE ile bulunuyor).
      **Devam eden düzeltmeler (kullanıcı yeniden istedi — "diğer 5 hissedeki
      brüt kârı da türetip doğrula")**: GOOGL/AMZN/META/NFLX'te "Brüt Kâr"ın
      HER ZAMAN N/A çıktığı bulundu (bu 4 şirket "GrossProfit" tag'ini güncel
      dönemde hiç kullanmıyor) — `gross_profit_us_gaap()` eklendi: doğrudan
      tag yoksa Hasılat − Maliyet (`CostOfRevenue`/`CostOfGoodsAndServicesSold`)
      türetir, stockanalysis.com ile BİREBİR doğrulandı (GOOGL $73,853mr,
      AMZN $104,828mr, NFLX $6,523mr). PYPL'de hiçbir maliyet tag'i yok, N/A
      doğru kalıyor. Ayrıca **kritik bir çeyreklik-türetme hatası** bulundu:
      GOOGL 2025 Ç1→Ç2 arasında XBRL etiketini değiştirmiş
      (`RevenueFromContractWithCustomer...` → `Revenues`) — eski kod iki
      dönemi AYNI tek etikette aradığı için "Satışlar (karşılaştırma)"
      satırı sessizce "veri yok" gösteriyordu; `quarterly_standardized_value_us_gaap()`
      artık her dönemi ayrı ayrı (tüm aday etiketleri deneyerek) çözüp SONRA
      çıkarıyor, etiket değişikliğine dayanıklı. Test: `pytest tests/`
      (432 test, 14 yeni, hiçbir regresyon yok).
- [x] **Faz 11 (buton menü arayüzü, 2026-08-02)** — Bot düz-metin-ticker'dan
      butonlu menüye taşındı: `/start`/`/menu` → 📊 Bilanço Analizi (🇹🇷 BİST /
      🇺🇸 NASDAQ) → 📅 Yaklaşan Bilanço Tarihleri (Faz 12/13 için iskelet,
      şimdilik "yakında" mesajı) → 🕘 Son Kartlar → ℹ️ Hakkında, her alt menüde
      "⬅️ Geri". Menü mantığı yeni `src/bot/menu.py` (123 satır) modülüne
      çıkarıldı: navigasyon TAMAMEN `callback_data` içine gömülü (örn.
      `"menu:analiz:nasdaq"`, hepsi 64 byte sınırının altında) — süreç yeniden
      başlasa bile butonlar çalışır. SADECE "hisse kodu bekleniyor" durumu
      `context.user_data["bekleyen_islem"]` içinde TTL'li (10 dk) tutulur;
      süresi dolarsa `handle_ticker_message` sessizce varsayılan BİST akışına
      döner. **Geriye uyumluluk KORUNDU**: kullanıcı menüye hiç girmeden
      doğrudan "THYAO" yazarsa aynen eskisi gibi çalışır (varsayılan market
      BİST, `normalize_ticker_input()` ikinci bir `market` parametresi aldı
      ama varsayılanı `"BIST"`). NASDAQ ticker doğrulaması ayrı bir regex
      (`^[A-Z]{1,5}(\.[A-Z])?$`) ile eklendi — BRK.B gibi sınıf ekli
      sembolleri destekler. `run_pipeline(..., market=...)` artık Telegram
      botundan da NASDAQ ile çağrılabiliyor (Faz 10'dan beri motor hazırdı,
      bota hiç bağlanmamıştı). Menü mesajları her tıklamada `edit_message_text`
      ile güncellenir, yeni mesaj atılmaz. **NASDAQ kapsamı doğrulandı**:
      SEC EDGAR fetcher `company_tickers.json` üzerinden CIK'i ARAR — sabit
      10 hisseyle SINIRLI DEĞİL, herhangi bir SEC'e kayıtlı ticker çalışır
      (canlı doğrulandı: `COST`, önceden test edilen 10 hissenin DIŞINDA,
      `scripts/demo_pipeline_us.py COST` ile uçtan uca başarılı). Bilinen
      sınır DEĞİŞMEDİ: bankalar/sigortalar için "revenue" gibi bazı kalemler
      N/A kalabilir (US GAAP şeması sadece sanayi/ürün şirketleri için
      doğrulanmış, bkz. `06_BILINEN_SORUNLAR.md` B11). Test:
      `pytest tests/` (485 test, 53 yeni — `tests/test_menu.py` + genişletilmiş
      `tests/test_telegram_bot.py`, hiçbir regresyon yok). Canlı doğrulama:
      `python main.py` ile bot başlatıldı, Telegram `getMyCommands` ile
      `/menu` komutunun kayıtlı olduğu doğrulandı.
- [x] **Faz 11.1 (MSFT FAVÖK eksikliği düzeltmesi — kullanıcı raporu, 2026-08-02)** —
      Kullanıcı MSFT kartında GELİR TABLOSU'nun 5 yerine 4 metrik gösterdiğini
      bildirdi (FAVÖK satırı tamamen kayboluyordu, tablo görsel olarak eksik/
      dengesiz görünüyordu). **Kök neden**: MSFT, AAPL/NVDA/JPM'nin kullandığı
      birleşik D&A tag'lerinin (`DepreciationDepletionAndAmortization`/
      `DepreciationAmortizationAndAccretionNet`) HİÇBİRİNİ raporlamıyor —
      amortismanı `Depreciation` (maddi duran varlık) + `AmortizationOfIntangibleAssets`
      (maddi olmayan duran varlık) olarak İKİ AYRI XBRL satırında tutuyor.
      **Düzeltme**: `sec_edgar.depreciation_amortization_us_gaap()`/
      `quarterly_depreciation_amortization_us_gaap()` eklendi — `gross_profit_us_gaap()`
      ile AYNI desen (birleşik tag öncelikli, yoksa iki bileşen TOPLANIR, sadece
      biri varsa None). CANLI DOĞRULANDI (web araması, gurufocus.com): MSFT
      FY26 Ç3 hesaplanan D&A $10,1mr, dış kaynağın raporladığı $10.167mr ile
      %1'in ALTINDA farkla eşleşti; kart yeniden render edildi, FAVÖK satırı
      artık görünüyor. Ayrıca kullanıcının "tüm NASDAQ hisseleri render
      edilebiliyor mu" sorusu için `COST` (önceden test edilmemiş) ve `ADBE`
      canlı test edildi — ikisi de 5/5 metrikle uçtan uca başarılı. Test:
      `pytest tests/` (488 test, 3 yeni — `tests/test_sec_edgar.py`, hiçbir
      regresyon yok).
- [x] **Faz 11.2 ("SKHY bulunamadı" mesaj netliği + AAPL logo araştırması, 2026-08-02)** —
      Kullanıcı "SKHY" (SK hynix) arattığında bot "bulamadım" diyordu; kök neden SK
      hynix'in SEC'te KAYITLI olması ama ABD GAAP/XBRL raporlamayan yabancı bir özel
      ihraççı olması (gerçek bir veri sınırı, kod hatası değil) — eski mesaj bunu
      "yazım hatası" gibi gösteriyordu. `pipeline.FinancialDataNotFoundError`
      eklendi (`TickerNotFoundError`'dan ayrı), bot artık sebebi açıkça belirten
      bir mesaj gösteriyor. AAPL logo şikayeti CANLI olarak reprodüklenemedi —
      hem doğrudan hem tam pipeline testinde logo doğru geldi; muhtemelen
      TradingView arama uç noktasının geçici bir hatasıydı (tasarım gereği
      kalıcı önbelleğe yazılmaz, kendiliğinden düzelir), bu yüzden kod
      değişikliği yapılmadı. Test: `pytest tests/` (491 test, 3 yeni —
      `tests/test_pipeline.py`, hiçbir regresyon yok).
- [x] **Faz 12 (Yaklaşan Bilanço Tarihleri — VERİ katmanı, 2026-08-02)** — BİST için
      "hangi şirket ne zaman bilanço açıklayacak" sorusuna cevap veren tek bir resmi
      API yok — üç yaklaşım araştırılıp (hepsi canlı doğrulandı) güven seviyesine göre
      birleştirildi: (1) KAP **"Finansal Takvim"** bildirimi — kesin ama opsiyonel
      (TAVHL/ASELS yayınlıyor, THYAO yayınlamıyor); (2) geçmiş **"Finansal Rapor"**
      yayın tarihlerinin medyanı — tahmini (THYAO ~37 gün, TAVHL ~27,5 gün, ASELS
      ~35,5 gün, dönem sonundan); (3) **SPK II-14.1 Tebliği** yasal son tarih — her
      zaman hesaplanabilir fallback (yıllık 60/70 gün, ara dönem 30/40+10 gün,
      resmi tatil kayması dahil). NASDAQ için üç aday karşılaştırıldı (Finnhub API
      anahtarı istiyor, Yahoo artık "crumb" oturum tokenı istiyor) —
      **`api.nasdaq.com/api/calendar/earnings`** seçildi (kayıtsız, günlük tüm
      piyasayı tek istekte döndürüyor). Yeni `src/fetchers/earnings_calendar.py`
      (490 satır) + `earnings_calendar` DB tablosu (`repository.upsert_earnings_calendar()`/
      `get_upcoming_earnings()`/`is_earnings_calendar_fresh()`). **Görsel/bot
      entegrasyonu bu fazın KAPSAMI DIŞINDA** (görev talimatı gereği — Faz 13'ün
      konusu; menü hâlâ "yakında eklenecek" gösteriyor). Demo:
      `python scripts/demo_takvim.py bist|nasdaq`. Test: `pytest tests/`
      (537 test, 46 yeni — `tests/test_earnings_calendar.py` + `tests/test_db.py`
      genişletmesi, hiçbir regresyon yok).
- [x] **Faz 13 (Takvim kartı görseli + bot entegrasyonu, 2026-08-02)** — Faz 12'deki
      takvim verisi paylaşılabilir bir PNG'ye ve bota bağlandı.
      **Render altyapısı genelleştirildi**: `card.render_card()`/`render_html()`
      artık `template_name`/`screenshot_selector` parametreleri alıyor (varsayılan
      `"card.html"`/`"#card"` ile TÜM mevcut çağrılar değişmeden çalışır) — bu,
      Faz 14/16/19'un da tabanı. Yeni `src/render/templates/calendar_card.html` +
      `src/render/calendar_card.py::build_calendar_context()`: 1200px sabit
      genişlik, yükseklik TAMAMEN içeriğe göre doğal oluşuyor (sabit bir
      min-height YOK — az kayıtla kart kısa kalır, boş alanla uzatılmaz; çok
      kayıtla doğal olarak büyür). **Kapsam kararı (kullanıcıyla netleştirildi)**:
      kart SADECE `kesin`+`tahmini` güven seviyelerini gösterir, `son_tarih`
      (SPK yasal fallback — taranan HER şirket için her zaman hesaplanabilir)
      BİLEREK dışlanır, yoksa kart pratikte taranan tüm evreni listeler ve
      "gerçek beklenti" ile "yasal tavan" arasındaki fark kaybolurdu. Tarihe
      göre gün gün gruplama, bugün amber sol bordürle vurgulanır, güven rozeti
      (kesin=yeşil dolu, tahmini=amber çerçeveli) + lejant. Yeni orkestrasyon
      (`src/bot/pipeline.py::refresh_earnings_calendar()`/`get_cached_earnings_calendar()`/
      `is_earnings_calendar_fresh()`): BIST100 yaklaşımı ticker başına 1-4 KAP
      isteği gerektirdiği için birkaç dakika sürebiliyor — bu yüzden **Telegram
      botu bunu ASLA senkron tetiklemez**, sadece DB önbelleğini okur; önbellek
      ayrı bir zamanlanmış script'le (`scripts/refresh_takvim_cache.py`, cron/Görev
      Zamanlayıcı ile günde 1-2 kez) doldurulur. `/takvim` komutu + `menu:takvim:bist/nasdaq`
      artık gerçek görsel + kopyala-yapıştır metni (X_BUYUME_RAPORU.md kalıp ⑤
      biçiminde) gönderiyor. Demo: `python scripts/demo_takvim_karti.py bist|nasdaq`.
      Test: `pytest tests/` (555 test, 18 yeni — `tests/test_calendar_card.py` +
      `tests/test_pipeline_takvim.py`, hiçbir regresyon yok).

## Dizin Yapisi

```
bilanco-radar/
├── .env.example
├── requirements.txt
├── config.py                # Ayarlar, sabitler, loglama kurulumu
├── main.py                  # Giris noktasi
├── data/                    # SQLite dosyasi + loglar + onbellek
├── src/
│   ├── fetchers/             # isyatirim.py, kap.py, sec_edgar.py (NASDAQ), earnings_calendar.py (takvim)
│   ├── db/                   # models.py, repository.py
│   ├── analysis/              # calculator.py, scorer.py
│   ├── ai/                    # commentary.py
│   ├── render/                 # templates/, card.py, calendar_card.py (takvim kartı)
│   └── bot/                    # pipeline.py (orkestrasyon), telegram_bot.py, menu.py (buton menü)
└── tests/
```

## Onemli Kurallar

- Sayisal hesaplamalar (yuzde degisim, rasyo, puan) LLM'e yaptirilmaz; Claude
  API sadece hazir hesaplanmis rakamlari sozel olarak yorumlar.
- Turkce sayi formati: binlik ayraci nokta, ondalik virgul (orn. 54.189.705.323).
- Para birimleri milyar/milyon TL olarak kisaltilir (orn. 54,2 mr ₺).
