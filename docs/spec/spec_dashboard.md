# SPEC: Piyasa Dashboard'u (Faz 5 — Toplu Tarama, Depolama, Tazelik, JSON Şeması)

Bu spec YOL_HARİTASI.md Faz 5'in **adım 1** çıktısıdır. Kapsam: `scripts/
tarama_toplu.py` (toplu tarama pipeline'ı), sonuçların DB'de saklanması
(yeni model kararı), tazelik/freshness politikası (`/piyasa` komutu dahil)
ve dashboard'a gömülecek JSON şeması. **HTML/CSS görsel tasarımı bu spec'in
KAPSAMI DIŞINDA** — o `kart-tasarim-sistemi` skill'i temel alan
kart-tasarımcısı'nın (Faz 5 adım 3) sorumluluğu; bu spec ona net bir VERİ
SÖZLEŞMESİ (JSON şeması + gruplama/etiketleme kuralları) teslim eder.

> **Durum (2026-08-12): KULLANICI ONAYI ALINDI, spec KODLAMAYA HAZIR.**
> Aşağıdaki 4 karar kullanıcı tarafından onaylanmıştır ve artık KESİNDİR
> (bkz. ilgili bölümlerde "(KESİN karar)" etiketi): (1) NASDAQ "tam evren"
> kapsamı `filer_category` tabanlı filtrelenmiş bir alt kümedir (§NASDAQ
> "tam evren" kapsamı), (2) `/piyasa` force-refresh YAPMAZ, sadece son
> `MarketScanResult`'ı render eder (§`/piyasa` komutu), (3) Tazelik
> penceresi v1'de TEK pencere, 7 gündür — ayrı fiyat/mali-tablo penceresi
> bilinçli olarak SONRAKİ bir faza ertelenmiştir (§Veri bağımlılığı),
> (4) BİST30/NASDAQ30 pilot evrenindeki ek 20+20 ticker bu oturumda
> WebSearch/WebFetch ile araştırılıp somutlaştırılmıştır (§çekirdek ticker
> kümesi). 5. madde (GYO'nun "sanayi" şablonuyla taranması) zaten
> bilgilendirme amaçlıydı, onay gerektirmiyordu.

---

## Amaç ve kapsam

**Ölçtüğü/ürettiği şey:** Tek bir batch job'ın (`scripts/tarama_toplu.py`)
DB'deki (Faz 2, `spec_sektor_evren.md`) BİST+NASDAQ evrenindeki HER şirket
için mevcut v2 çok-mercekli motoru (`src.bot.pipeline.
compute_multi_lens_score_for_ticker()`, Faz 3c'de zaten kodlanmış,
**DEĞİŞTİRİLMEZ**) çağırıp sonucu kalıcı, sorgulanabilir bir DB tablosunda
(`MarketScanResult`, YENİ) biriktirmesi + bu tablodan tek dosyalık bir HTML
dashboard'a (Faz 5 adım 3) gömülecek JSON'un ŞEMASI ve tazelik/gruplama
kurallarının tanımı.

**Geçerli şirket türleri:** `sanayi`, `abd_sanayi`, `banka`, `sigorta`,
`finansman` — `compute_multi_lens_score_for_ticker()`'ın zaten desteklediği
5 şablonun TAMAMI (bkz. `spec_bilesik_skor.md`). `sirket_turu="gyo"` şirketleri
(bkz. `spec_sektor_evren.md` §Şirket türü tanımı) BİST'te genelde
`financial_group="XI_29"` altında raporlandığından bu turda **şablon
`"sanayi"` ile taranır** (GYO'ya özel bir mercek/şablon henüz YOK — bilinen
bir sınırlama, bilgilendirme amaçlı, onay GEREKTİRMEZ; dashboard satırında
`sirket_turu="gyo"` AÇIKÇA görünür ki kullanıcı F/K, ROE gibi çarpanların
bir REIT için standart-dışı yorumlanması gerektiğini bilsin; bkz. Kenar
Durumlar).

**Piyasalar:** BİST + NASDAQ (Faz 2'de `Company` tablosuna kazandırılmış
evren: BİST 643 şirket TAM, NASDAQ 4352 ticker keşfedilmiş / bir kısmı SIC
ile zenginleştirilmiş — bkz. YOL_HARİTASI.md Faz 2 "Bitti kriteri" notu).
NASDAQ tarafında bu ham 4352 rakamının TAMAMI değil, filtrelenmiş bir alt
küme "tam evren" sayılır (bkz. §NASDAQ "tam evren" kapsamı, KESİN karar).

**Kapsam dışı (başka spec'lerin/fazların konusu):**
- Mercek/bileşik skor formülleri (`spec_mercek_*.md`, `spec_bilesik_skor.md`)
  — bu spec onları SADECE ÇAĞIRIR, yeniden TANIMLAMAZ.
- Sektör taksonomisi/evren doldurma (`spec_sektor_evren.md`, Faz 2'de
  TAMAMLANDI) — bu spec ön koşul olarak VARSAYAR (bu spec sadece KÜÇÜK,
  geriye-uyumlu bir alan eklemesi önerir, bkz. §NASDAQ "tam evren" kapsamı).
- Dashboard'un görsel tasarımı, renk skalası, tipografi (`kart-tasarim-
  sistemi` skill, kart-tasarımcısı Faz 5 adım 3).

---

## Girdiler

| Girdi | Kaynak | Durum |
|---|---|---|
| Evren listesi (ticker, market, ust_sektor, sirket_turu, financial_group, last_updated) | `Company` tablosu (`src/db/models.py`) | **MEVCUT** (Faz 2) |
| 4-mercek + bileşik skor hesaplama | `src.bot.pipeline.compute_multi_lens_score_for_ticker(ticker, market)` | **MEVCUT** (Faz 3c/3.1), DEĞİŞTİRİLMEZ |
| Ana çarpanlar (F/K, PD/DD, FD/FAVÖK, piyasa değeri, fiyat) | `compute_multi_lens_score_for_ticker()` içinde zaten hesaplanan `valuation_metrics` (`calculator.ValuationMetrics`/`BankValuationMetrics`/vb.) — **bu spec `MultiLensScoreResult`'a bu alanların da taşınmasını GEREKTİRİR** (bkz. Formüller-0, aşağıda) | **KISMEN MEVCUT** — hesaplanıyor ama `MultiLensScoreResult` dataclass'ı şu an SADECE `bilesik` taşıyor, `valuation_metrics` DIŞARI SIZMIYOR (bkz. `pipeline.py` satır 1538-1551) |
| Bilanço tarihi öncelik ipucu (opsiyonel, force-check tetikleyici) | `EarningsCalendar` tablosu (`Company.expected_date`, zaten MEVCUT, Faz 12) | **MEVCUT**, bu spec'te İLK KEZ tazelik kuyruğuna bağlanıyor |
| Sektör grupları için `n≥5` kuralı | `sektor-siniflandirma` skill madde 1, `lens_common.MIN_SECTOR_N=5` (mercek-içi kullanımla AYNI eşik, dashboard grup etiketlemesinde de TUTARLI kullanılır) | **MEVCUT sabit, YENİDEN kullanılır** |
| BİST/NASDAQ veri eksikliği haritası | `docs/spec/veri_tamlik_notu.md` §1-6 | **MEVCUT**, bu spec'te statik bir etiket tablosuna (`PIYASA_SISTEMIK_EKSIK_BILESENLER`) dönüştürülüyor (bkz. §Veri eksikliği görünürlüğü) |
| SEC filer-durumu kategorisi (`category` alanı, `submissions/CIK{cik}.json`) | `sec_edgar.py` — AYNI uç nokta zaten SIC için çekiliyor | **YENİ** (bu spec'te CANLI olarak WebSearch ile şema doğrulandı, bkz. §NASDAQ "tam evren" kapsamı) — SIFIR ek ağ isteği |

**YENİ girdi/altyapı ihtiyaçları (kodlama fazına açıkça bırakılır):**
- `src/db/repository.py`'ye: `upsert_market_scan_result()`,
  `get_market_scan_results()`, `get_scan_queue()` (bkz. §Formüller-1).
- `MultiLensScoreResult` dataclass'ına (`pipeline.py`) `valuation_metrics`
  alanının EKLENMESİ (genişletme, mevcut alanlar KORUNUR — persona kural 8)
  — aksi halde `tarama_toplu.py` her ticker için F/K/PD/DD/FD-FAVÖK'ü
  AYRICA hesaplamak zorunda kalır (kod tekrarı, katman ihlali).
- `sec_edgar.SicInfo`'ya `category: str | None` alanının EKLENMESİ +
  `Company.filer_category` YENİ sütunu (bkz. §NASDAQ "tam evren" kapsamı).

---

## Mimari karar 1: `scripts/tarama_toplu.py` (toplu tarama pipeline'ı)

`scripts/refresh_universe.py` (Faz 2) ile BİREBİR AYNI ilkeler — checkpoint
DB'nin kendisidir, ayrı bir dosya/kuyruk tablosu YOK; rate-limit'e saygı
mevcut fetcher içi mekanizmalardan (`config.HTTP_RATE_LIMIT_DELAY_SECONDS`,
retry-backoff) BAĞIMSIZ, ek bir PARTİLER-ARASI bekleme sabitiyle sağlanır
(`SEC_BULK_PACING_SECONDS` deseninin BİREBİR aynısı, aşağıda `SCAN_PACING_
SECONDS_*` adıyla).

**Kritik fark (refresh_universe.py'den):** `refresh_universe.py` TEK bir
ucuz bulk uç noktadan (`kap.fetch_sector_map()`, `company_tickers_exchange.
json`) veri çeker; `tarama_toplu.py` ise HER ticker için TAM bir
`compute_multi_lens_score_for_ticker()` çağrısı yapar — bu, İÇİNDE
potansiyel olarak (a) tam mali tablo fetch'i (İş Yatırım/KAP/SEC EDGAR
companyfacts), (b) 400 günlük OHLCV fiyat geçmişi (`price_history.
fetch_ohlcv` — **CANLI kod incelemesi doğruladı: DB önbelleği YOK, HER
çağrıda ağa gider**, bkz. Tazelik bölümü) İÇERİR. Bu yüzden `tarama_toplu.
py`'nin PER-COMPANY maliyeti `refresh_universe.py`'nin Adım 2'sinden
(sadece 1 SEC isteği) KATBEKAT yüksektir — tazelik penceresi ve kademeli
`--limit` tasarımı bunu MERKEZE alır (bkz. §Tazelik).

### Orkestrasyon adımları

```
1. --market (bist|nasdaq|all, varsayılan all) + --universe (tam|bist30|
   nasdaq30, varsayılan tam) + --limit (varsayılan: BİST 200, NASDAQ 150 --
   gerekçe aşağıda) + --dry-run bayraklarını ayrıştır.

2. Taranacak ticker listesini belirle:
   a. --universe bist30/nasdaq30 ise: scriptte STATİK, isimlendirilmiş bir
      liste (BIST30_PILOT / NASDAQ30_PILOT, bkz. aşağı) -- DB SORGUSU
      YAPILMAZ, doğrulama amaçlı SABİT küme, §NASDAQ kalite filtresine
      TABİ DEĞİL.
   b. --universe tam ise: get_scan_queue(session, market, stale_after_days,
      limit, priority_tickers) DB sorgusu (bkz. Formüller-1) -- SADECE
      ust_sektor/sirket_turu DOLU (Faz 2 tamamlanmış) satırlar aday olur;
      market="nasdaq" ise EK OLARAK §NASDAQ kalite filtresi (filer_category)
      uygulanır; `ust_sektor IS NULL` satırlar ATLANIR ama bir uyarı
      sayacına eklenir (bkz. Kenar durumlar -- "Sınıflandırılmamış" grubu
      SADECE zaten taranmış/DB'de skoru olan satırlar için dashboard'da
      gösterilir, YENİ tarama tetiklemez).

3. Her ticker için:
   a. try: sonuc = compute_multi_lens_score_for_ticker(ticker, market)
   b. except TickerNotFoundError: scan_status="veri_yok" (bkz. Kenar durumlar)
   c. except UnsupportedCompanyTypeError: scan_status="desteklenmiyor"
   d. except (isyatirim.CompanyNotFoundError, sec_edgar.CompanyNotFoundError,
      httpx.RequestError, ...): scan_status="hata", error_detail=str(exc)
      (transient -- LOG'lanır, script bir SONRAKİ ticker'a GEÇER, ÇÖKMEZ --
      mevcut _refresh_nasdaq_step1'in "tek satır hatası tüm batch'i
      durdurmaz" ilkesiyle AYNI).
   e. Başarılıysa: upsert_market_scan_result(session, ticker, ...alanlar...,
      scan_status="ok", computed_at=utcnow_naive())
   f. time.sleep(SCAN_PACING_SECONDS_BIST veya _NASDAQ) -- ticker'lar ARASI
      bekleme (fetcher-içi retry bekleme'DEN AYRI, bkz. Tazelik).

4. session.commit() HER PARTİ SONUNDA (mevcut desenle tutarlı, refresh_
   universe.py NASDAQ Adım 2 ile AYNI -- SIGINT/crash durumunda o ana kadar
   işlenenler ZATEN kalıcı).

5. Özet rapor: "N şirket tarandı (M başarılı, K hata, L desteklenmiyor, J
   veri_yok), kuyrukta X şirket kaldı (sonraki çalıştırmaya)."
```

### CLI örnekleri

```
python scripts/tarama_toplu.py --universe bist30              # küçük doğrulama, BİST
python scripts/tarama_toplu.py --universe nasdaq30             # küçük doğrulama, NASDAQ
python scripts/tarama_toplu.py --market bist                   # tam BİST evreni, 1 parti (limit=200)
python scripts/tarama_toplu.py --market nasdaq --limit 300      # NASDAQ, kademeli, filer_category filtreli
python scripts/tarama_toplu.py --market bist --dry-run          # sadece kuyruk boyutunu raporla, hesaplama YAPMA
python scripts/tarama_toplu.py --market nasdaq --dry-run        # filtrelenmiş "kaliteli" NASDAQ evreninin GERÇEK boyutunu ölç
```

### `--universe bist30` / `--universe nasdaq30` — ÇEKİRDEK ticker kümesi (ARAŞTIRILDI, KESİN)

**Veri gerçekliği notu (persona kural 7):** BİST30/Nasdaq-100 gibi endeks
üyelikleri bu projede CANLI/OTOMATİK bir kaynaktan DB'ye ÇEKİLMİYOR
(`Company.index_memberships` alanı `spec_sektor_evren.md`'de "Veri
Bağımlılığı" olarak işaretli, DOLDURULMUYOR). Bu yüzden `bist30`/`nasdaq30`
bayrakları **DB sorgusu değil, scriptte gömülü STATİK bir liste** kullanır.
Kullanıcı talebi üzerine bu turda liste **WebSearch/WebFetch ile ARAŞTIRILDI**
(aşağıdaki dipnotlarda kaynak+tarih belirtildi, persona kural 7: uydurma
yapılmadı) — amaç endeksin milisaniye hassasiyetinde güncel bileşimini
yakalamak DEĞİL (üç ayda bir yeniden dengelenen bir endeks için bu zaten
imkansız bir hedef), "uçtan uca doğrulama için yeterince çeşitli, gerçekçi
büyük/likit bir örneklem" sağlamaktır.

Çekirdek (projede HALİHAZIRDA `demo_v2_skor.py`/`spec_sektor_evren.md`'de
canlı doğrulanmış, 5 şablonun 5'ini de kapsayan 12 ticker — BİST 10+2,
NASDAQ 10):

```python
BIST_DOGRULANMIŞ_CEKIRDEK = [
    "THYAO", "ASELS", "TUPRS", "KCHOL", "AKBNK",  # AKBNK=banka (UFRS)
    "SISE", "BIMAS", "EREGL", "FROTO", "ENKAI",
    "ANSGR",  # sigorta (UFRS_K)
    "KTLEV",  # finansman (XI_29K)
]
NASDAQ_DOGRULANMIŞ_CEKIRDEK = [
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL",
    "AMZN", "META", "NFLX", "AMD", "PYPL",
]
```

**BİST ek 20 ticker (çekirdekle ÇAKIŞMAYAN, XU030/BIST30 bileşimi[^bist30]):**
```python
BIST30_EK_20 = [
    "AEFES", "ASTOR", "DSTKF", "EKGYO", "GARAN", "GUBRF", "ISCTR", "KRDMD",
    "MGROS", "PETKM", "PGSUS", "SAHOL", "SASA", "TAVHL", "TCELL", "TOASO",
    "TRALT", "TTKOM", "VAKBN", "YKBNK",
]
BIST30_PILOT = BIST_DOGRULANMIŞ_CEKIRDEK + BIST30_EK_20  # toplam 32 (10 çekirdek sanayi/banka + 2 sigorta/finansman çeşitliliği + 20 ek)
```

**NASDAQ ek 20 ticker (çekirdekle ÇAKIŞMAYAN, Nasdaq-100 ağırlık sırasına göre büyük/likit üyeler[^ndx]):**
```python
NASDAQ30_EK_20 = [
    "ADBE", "ADI", "ADP", "ADSK", "AMAT", "AMGN", "ASML", "AVGO", "BKNG",
    "CHTR", "CMCSA", "COST", "CRWD", "CSCO", "CSX", "DASH", "EA", "EXC",
    "FTNT", "GILD",
]
NASDAQ30_PILOT = NASDAQ_DOGRULANMIŞ_CEKIRDEK + NASDAQ30_EK_20  # toplam 30
```

[^bist30]: Kaynak: infoyatirim.com, "BIST 30 Hisseleri & XU030 Şirket
Listesi" (`https://infoyatirim.com/canli-borsa/xu030-bist-30-hisseleri`),
bu oturumda (2026-08-12) WebFetch ile çekildi; çapraz-referans olarak
mynet Finans (`finans.mynet.com/borsa/endeks/xu030-bist-30/`) AYNI
tarihte "11 Ağustos 2026 BIST-30 Endeksi" başlığıyla erişildi (tam liste
ORADA görüntülenemedi, sadece tarih teyidi için kullanıldı). infoyatirim
sayfasından 30 bileşenin TAMAMI okundu; 10'u mevcut çekirdekle ÇAKIŞTI
(AKBNK/ASELS/BIMAS/ENKAI/EREGL/FROTO/KCHOL/SISE/THYAO/TUPRS), kalan TAM
20'si yukarıda. **BİST30'un resmi seçim kriteri (Borsa İstanbul): fiili
dolaşımdaki payların piyasa değeri + günlük ortalama işlem hacmi, ÜÇ AYDA
BİR yeniden belirlenir** — bu liste bir ANLIK GÖRÜNTÜdür, periyodik
(örn. her çeyrek) yeniden doğrulanması ÖNERİLİR. `TRALT` (Türk Altın
İşletmeleri) nispeten yeni/az bilinen bir bileşendir — bir SONRAKİ
rebalans'ta listeden ÇIKABİLİR; kod-geliştirici bu ticker için DB'de
yeterli finansal geçmiş OLMADIĞINI görürse `scan_status="veri_yok"` ile
SESSİZCE atlanacağını, bunun script'i BOZMAYACAĞINI bilmelidir (bkz.
Kenar durumlar).

[^ndx]: Kaynak: topforeignstocks.com, "The Complete List of Constituents
of the NASDAQ-100 Index" (`https://topforeignstocks.com/indices/the-
complete-list-of-constituents-of-the-nasdaq-100-index/`), bu oturumda
(2026-08-12) WebFetch ile çekildi; sayfa başlığına göre "1 Şubat 2026"
itibarıyla bileşim listeliyordu (101 sembol, birkaç şirketin çift hisse
sınıfı [örn. GOOGL/GOOG] nedeniyle 102 satır). Çekirdekle ÇAKIŞANLAR
(AMD/GOOGL/GOOG/AMZN/AAPL — GOOG da GOOGL'ın ikinci hisse sınıfı olduğu
için AYRICA elendi) çıkarıldıktan sonra kalan adaylardan büyük/likit,
farklı sektörleri (yarı iletken, yazılım, sağlık, telekom/medya, tüketici)
temsil eden 20 isim seçildi. Nasdaq-100 da yıllık (Aralık) + ad-hoc
yeniden dengeleme YAPAR, periyodik doğrulama ÖNERİLİR.

---

### NASDAQ "tam evren" kapsamı — filtrelenmiş kaliteli alt küme (KESİN karar)

**Karar: `--universe tam --market nasdaq`, ham `company_tickers_exchange.
json` dökümündeki ~4352 ticker'ın TAMAMINI DEĞİL, SEC'in KENDİ resmi
filer-durumu sınıflandırmasına göre "Large accelerated filer" veya
"Accelerated filer" kategorisindeki bir ALT KÜMEYİ tarar.** Ham 4352 rakamı
büyük olasılıkla SPAC'lar, kabuk şirketler, çok küçük/yeni halka arzlar ve
XBRL raporlamayan yabancı özel ihraççılar İÇERİR — bunları TARAMAK hem
rate-limit bütçesini İSRAF eder hem de dashboard'u "veri_yok"/"hata"
satırlarıyla DOLDURUR (sinyal/gürültü oranını BOZAR, kullanıcının "tüm
NASDAQ'ı görmek" beklentisini AslındaGürültüyleTatmin eder).

**Somut kriter — YENİ, ucuz bir alan (`Company.filer_category`):** SEC'in
`submissions/CIK{cik}.json` uç noktası (BU AYNI çağrı zaten Faz 2 NASDAQ
Adım 2'de `sic`/`sicDescription` için kullanılıyor, `sec_edgar.
fetch_sic_info()`) **AYNI yanıt gövdesinde** dokümante edilmiş bir
`category` alanı da taşır (bu oturumda WebSearch ile CANLI doğrulandı —
SEC'in resmi submissions şeması top-level alanları: `cik, entityType, sic,
sicDescription, insiderTransactionForOwnerExists,
insiderTransactionForIssuerExists, name, tickers, exchanges, ein,
description, website, investorWebsite, category, fiscalYearEnd,
stateOfIncorporation, ..., filings`; `category` değerleri "Large
accelerated filer", "Accelerated filer", "Non-accelerated filer" gibi
SEC'in KENDİ düzenleyici filer-durumu etiketleridir). **Bu alan SIFIR EK
AĞ İSTEĞİYLE** (aynı submissions payload'ının BAŞKA bir alanı okunarak)
elde edilebilir — `data.sec.gov/submissions/CIK...json`'a genel amaçlı
WebFetch ile bu oturumda erişim SEC'in User-Agent politikası nedeniyle
403 ile REDDEDİLDİ (kimliksiz istemci) — projenin KENDİ `sec_edgar.py`
istemcisi (açıklayıcı `USER_AGENT` sabitiyle) bu kısıtlamaya TABİ DEĞİLDİR,
kod-geliştirici gerçek bir CIK ile şemayı YENİDEN canlı doğrulamalıdır.

**Uygulama (kodlama fazına bırakılan somut adımlar):**
1. `sec_edgar.SicInfo` dataclass'ına `category: str | None` alanı EKLENİR
   (genişletme, mevcut `sic`/`sic_description` alanları KORUNUR);
   `fetch_sic_info()` aynı JSON'dan bu alanı da parse eder.
2. `Company` modeline YENİ bir sütun: `filer_category: Mapped[str | None]
   = mapped_column(String(60))` (`spec_sektor_evren.md`'nin ALTER TABLE
   deseniyle BİREBİR aynı idempotent migration, `_migrate_add_filer_
   category_column`) — bu, `spec_sektor_evren.md`'ye KÜÇÜK, geriye-uyumlu
   bir EK'tir (persona kural 8, sadece NASDAQ satırlarında dolar, BİST'te
   None kalır — BİST'te bu kavram YOK).
3. `refresh_universe.py`'nin NASDAQ Adım 2'si (`_refresh_nasdaq_step2`)
   bu alanı da `upsert_sector_taxonomy()` çağrısına EKLER.
4. **Tek seferlik backfill:** Faz 2'de ZATEN zenginleştirilmiş (sic_code
   dolu) ama bu alan henüz YOKKEN işlenmiş satırlar için `filer_category
   IS NULL AND sic_code IS NOT NULL` koşulu `_next_batch()`'e (refresh_
   universe.py) GEÇİCİ bir ek koşul olarak eklenir (90 günlük tazelik
   penceresinden BAĞIMSIZ, sadece BU alan boşsa yeniden-dene) — bir
   SONRAKİ `refresh_universe.py --market nasdaq` çalıştırmasında OTOMATİK
   tamamlanır, `tarama_toplu.py`'nin AYRI bir şey yapması GEREKMEZ.
5. `get_scan_queue()` (bu spec, Formüller-1), `market="NASDAQ"` VE
   `universe="tam"` olduğunda EK bir koşul uygular:
   ```python
   kategori = func.lower(Company.filer_category)
   nasdaq_kalite_filtresi = and_(
       Company.filer_category.is_not(None),
       kategori.like("%accelerated filer%"),
       kategori.not_like("%non-accelerated%"),  # alt-dizgi tuzagi: "non-accelerated filer" de "accelerated filer" ICERIR, ONCE elenmeli
   )
   ```
   `--universe bist30/nasdaq30` (statik pilot liste) bu filtreye TABİ
   DEĞİLDİR (zaten elle seçilmiş, büyük/likit isimler).

**Eşik gerekçesi (dolar rakamı UYDURULMADI):** Bu spec, "Accelerated
filer"in SEC'in kendi tanımındaki halka açık kısım eşiğinin (tarihsel
olarak yaklaşık 75 milyon USD, ama 2026 itibarıyla SEC'in filer-durumu
çerçevesini sadeleştirme teklifinin GÜNDEMDE olduğu bu oturumda
WebSearch'te görüldü) HANGİ TAM DOLAR rakamına karşılık geldiğini KENDİSİ
hesaplamıyor — sadece SEC'in KENDİ ürettiği, düzenleme değiştikçe OTOMATİK
senkron kalan `category` ETİKETİNİ okur. Bu, "sahte kesinlik yasak"
ilkesiyle EN UYUMLU yaklaşımdır (projenin kendi bir dolar-eşiği İCAT
ETMESİ yerine SEC'in yetkili sınıflandırmasına GÜVENİR).

**Bilinen sınırlama:** Yabancı özel ihraççılar (20-F dosyalayanlar, örn.
ADR'ler) `category` alanında FARKLI/boş bir değer taşıyabilir — bu
durumda filtre GÜVENLİ TARAFTA hata yapar (`is_not(None)` + `like` koşulu
onları DIŞLAR) — bu TASARIM GEREĞİ kabul edilebilir bir daralmadır
(dashboard'un "kaliteli NASDAQ alt kümesi" hedefiyle ÇELİŞMEZ, ADR'lerin
İLERİDE ayrı bir kural ile EKLENMESİ mümkündür, bu spec'in kapsamı
DIŞINDA).

**Gerçek boyut:** Filtrelenmiş evrenin KESİN büyüklüğü bu spec'te TAHMİN
EDİLMEZ (SEC genelinde büyük+hızlandırılmış filer sayısı halka açık
istatistiklere göre birkaç bin mertebesindedir, NASDAQ'ın payı bunun bir
KISMIdır) — kod-geliştirici `--dry-run` ile GERÇEK sayıyı ölçüp
raporlamalıdır (bkz. yukarıdaki CLI örnekleri).

---

## Mimari karar 2: DB modeli — `MarketScanResult` (YENİ tablo, `GeneratedCard` GENİŞLETİLMEDİ)

### Karar

**YENİ bir model (`MarketScanResult`) eklenir; `GeneratedCard`
DEĞİŞTİRİLMEZ.**

### Gerekçe (neden `GeneratedCard` genişletilmedi)

`GeneratedCard` semantik olarak **append-only bir OLAY GÜNLÜĞÜ**dür: her
`/son` PNG üretiminde YENİ bir satır eklenir (`save_generated_card`, AUTOINCREMENT
`id`, `created_at` HER ZAMAN "şimdi"), `get_score_history()`/`get_recent_
cards()` bu günlüğü ZAMAN SIRASIYLA okur, `ticker` başına BİRDEN FAZLA
satır NORMALDİR (kasıtlı tasarım, kullanıcı geçmişini gösterir). `score`
alanı tek bir `float` (v1'in TEK sayısı).

Dashboard'ın ihtiyacı ise TAM TERSİ bir erişim deseni: **her ticker için
SADECE EN GÜNCEL anlık görüntü** (upsert, `ticker` BENZERSİZ anahtar),
TÜM evren üzerinde TOPLU okunabilir ("BİST + NASDAQ'taki HER şirketin
GÜNCEL skorunu getir" -- `GeneratedCard`'da bu sorgu `MAX(created_at) GROUP
BY ticker` gerektirir, indekslenemez şekilde pahalıdır), 4 mercek + bileşik
+ çarpanlar + sektör + tazelik zaman damgası GİBİ ~20 alan (v2'ye özgü,
`GeneratedCard`'da YOK). `GeneratedCard`'a bu ~20 nullable sütunu eklemek
HEM iki FARKLI ERİŞİM DESENİNİ (log vs. cache) TEK tabloda karıştırır HEM
DE `GeneratedCard`'ın var olan tüketicilerini (`/son` komutu, `get_recent_
cards`) ANLAMSIZ NULL sütunlarla kirletir. Bu, `SectorMetricCache`'in
KENDİ modül yorumunda zaten uyguladığı ayrımla AYNI ilke: "farklı ERİŞİM
DESENİ = farklı tablo" (persona kural 8: genişlet ama ÇÖPE ATMA -- burada
"genişletmek" YANLIŞ tabloyu genişletmek olurdu, DOĞRU genişleme YENİ bir
kardeş tablo eklemektir).

### Şema

```python
class MarketScanResult(Base):
    """Faz 5 (docs/spec/spec_dashboard.md): BİST/NASDAQ evrenindeki bir
    şirketin EN GÜNCEL v2 çok-mercekli tarama SONUCUNUN anlık görüntüsü --
    `ticker` BENZERSİZ (upsert, GeneratedCard'ın append-only OLAY
    GÜNLÜĞÜNDEN KASITLI OLARAK FARKLI bir erişim deseni, bkz. spec §Mimari
    karar 2). scripts/tarama_toplu.py TARAFINDAN YAZILIR, src/render/
    dashboard.py TARAFINDAN TOPLU okunur; hesaplama BURADA YAPILMAZ (saf
    CRUD/cache, quaxis-mimari anayasa)."""

    __tablename__ = "market_scan_result"

    ticker: Mapped[str] = mapped_column(ForeignKey("company.ticker"), primary_key=True)
    market: Mapped[str] = mapped_column(String(10))               # "BIST" | "NASDAQ"
    company_name: Mapped[str | None] = mapped_column(String(255)) # denormalize -- JOIN'siz dashboard sorgusu icin
    ust_sektor: Mapped[str | None] = mapped_column(String(40))    # tarama anindaki KOPYA (Company degisirse dashboard bir SONRAKI taramada yakalar)
    sirket_turu: Mapped[str | None] = mapped_column(String(20))
    template: Mapped[str | None] = mapped_column(String(20))      # "sanayi" | "abd_sanayi" | "banka" | "sigorta" | "finansman"
    year: Mapped[int | None]
    period: Mapped[int | None]                                    # (year, period) = analysis.latest_period

    scan_status: Mapped[str] = mapped_column(String(20))          # "ok" | "hata" | "desteklenmiyor" | "veri_yok"
    error_detail: Mapped[str | None] = mapped_column(String(500))

    # --- 4 mercek (düz sütunlar -- SIRALANABİLİR tablo gereksinimi,
    #     kart-tasarim-sistemi skill: "sıralanabilir tablo (mercek
    #     skorları...)" -- JSON blob icinde saklansaydi SQL ORDER BY
    #     yapılamazdı) ---
    deger_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    deger_badge: Mapped[str | None] = mapped_column(String(20))
    deger_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    kalite_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    kalite_badge: Mapped[str | None] = mapped_column(String(20))
    kalite_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    buyume_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    buyume_badge: Mapped[str | None] = mapped_column(String(20))
    buyume_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    guvenlik_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    guvenlik_badge: Mapped[str | None] = mapped_column(String(20))
    guvenlik_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    bilesik_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    bilesik_badge: Mapped[str | None] = mapped_column(String(20))
    bilesik_data_coverage_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # YENİ agregasyon, bkz. Formüller-0
    dahil_edilen_mercekler: Mapped[list | None] = mapped_column(JSON)  # bkz. BilesikSkorSonucu.dahil_edilen_mercekler

    # --- Ana çarpanlar (mevcut ValuationMetrics ailesinden, bkz. Girdiler) ---
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    pb_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    ev_ebitda: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    currency: Mapped[str | None] = mapped_column(String(10))      # "TRY" | "USD"

    # --- Opsiyonel drill-down (Faz 5 ZORUNLU DEĞİL, ucuz oldugu icin
    #     simdiden acilir -- CommentaryCache.positives ile AYNI JSON-on-
    #     SQLite deseni) ---
    mercekler_detay: Mapped[dict | None] = mapped_column(JSON)    # {"değer": [ComponentScore alanları...], ...}

    computed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)     # bu SATIRIN en son ne zaman hesaplandigi (SCAN tazelik anchor'i)
    financial_data_as_of: Mapped[datetime | None] = mapped_column(DateTime)           # Company.last_updated'in tarama anındaki KOPYASI (bkz. Tazelik)
```

**Migration notu:** Bu YENİ bir tablo -- `Base.metadata.create_all()`
otomatik oluşturur, `_migrate_add_*` tarzı bir ALTER TABLE fonksiyonu
GEREKMEZ (mevcut tabloya sütun eklemiyoruz).

**Şema çakışması kontrolü:** `market_scan_result.ticker`,
`company.ticker`'a FK'dir ama `Company` satırı SİLİNMEZ hiçbir akışta (bkz.
mevcut kod tabanı) -- FK bütünlüğü riski YOK.

---

## Formüller

### Formüller-0: `bilesik_data_coverage_pct` (YENİ agregasyon)

`lens_bilesik_skor.BilesikSkorSonucu`'nun KENDİSİ bir `data_coverage_pct`
alanı TAŞIMAZ (sadece `data_sufficient: bool` -- bkz. `src/analysis/
lens_bilesik_skor.py` satır 60-71) -- dashboard'un "bu skor verinin ne
kadarına dayanıyor" tek-sayı özetine ihtiyacı var. Bu, YENİ, ince bir saf
matematik fonksiyonu olarak **`src/analysis/lens_bilesik_skor.py`'YE
EKLENİR** (mevcut `BilesikSkorSonucu`/`hesapla_bilesik_skor` DEĞİŞTİRİLMEZ,
sadece bunları TÜKETEN yeni bir fonksiyon eklenir -- persona kural 8):

```python
def hesapla_veri_kapsam_ozeti(bilesik: BilesikSkorSonucu) -> Decimal | None:
    """Σ(lens_i.data_coverage_pct * MERCEK_AGIRLIKLARI[i]) / Σ(MERCEK_AGIRLIKLARI[i])
    -- SADECE kavramsal olarak VAR OLAN (None OLMAYAN) mercekler uzerinden,
    NOMINAL agirliklarla (data_sufficient esigiyle YENIDEN dagitilmis
    EFEKTIF agirliklarla DEGIL -- bu, bilesik_skor'un kendi hesaplamasindan
    KASITLI olarak FARKLI bir soru sorar: "genel olarak ne kadar veriye
    dayaniyoruz", "skora kac mercek katildi" DEGIL).

    Tum mercekler None ise (kavramsal olarak hic uygulanamiyor -- COK
    NADIR) None doner (dashboard '-' gosterir)."""
    mercekler = {
        "değer": bilesik.mercekler.deger, "kalite": bilesik.mercekler.kalite,
        "güvenlik": bilesik.mercekler.guvenlik, "büyüme": bilesik.mercekler.buyume,
    }
    mevcut = {isim: s for isim, s in mercekler.items() if s is not None}
    if not mevcut:
        return None
    toplam_agirlik = sum(MERCEK_AGIRLIKLARI[isim] for isim in mevcut)
    toplam_katki = sum(s.data_coverage_pct * MERCEK_AGIRLIKLARI[isim] for isim, s in mevcut.items())
    return _clamp(toplam_katki / toplam_agirlik, Decimal(0), Decimal(100))
```

### Formüller-1: Tarama kuyruğu sorgusu (`get_scan_queue`, `src/db/repository.py`)

```python
def get_scan_queue(session, market: str, stale_after_days: int, limit: int,
                    priority_tickers: set[str] | None = None) -> list[Company]:
    """MarketScanResult'i Company'ye LEFT JOIN eder -- aday satirlar:
      (a) MarketScanResult HIC YOK (hic taranmamis) VEYA
      (b) MarketScanResult.computed_at simdiden `stale_after_days` gunden
          eski VEYA
      (c) ticker `priority_tickers` icinde (bilanço-tarihi yaklaşan/geçmiş
          şirketler icin FORCE -- bkz. Tazelik §Öncelik kuyruğu)
    ONKOSUL: Company.market == market AND Company.ust_sektor IS NOT NULL
    (Faz 2 tamamlanmamis satirlar ATLANIR, bkz. Kenar durumlar).
    market="NASDAQ" ise EK ONKOSUL: §NASDAQ kalite filtresi (filer_category
    tabanli, bkz. Mimari karar 1 "NASDAQ 'tam evren' kapsamı" bolumu).
    Siralama: hic taranmamis (`computed_at IS NULL`) ONCE, sonra en eski
    `computed_at` -- _next_batch (refresh_universe.py) ile AYNI ilke
    (`order_by(computed_at.asc().nullsfirst())`). `limit` uygulanir."""
```

### Formüller-2: Öncelik kümesi (`priority_tickers`)

```python
cutoff_gecmis = utcnow_naive() - timedelta(days=3)
cutoff_gelecek = utcnow_naive() + timedelta(days=3)
priority_tickers = {
    row.ticker for row in session.execute(
        select(EarningsCalendar.ticker).where(
            EarningsCalendar.market == market,
            EarningsCalendar.expected_date.between(cutoff_gecmis.date(), cutoff_gelecek.date()),
        )
    ).scalars()
}
# Gerekce: bilanço tarihi ±3 gun penceresindeki sirketler icin 7 gunluk
# standart pencereyi BEKLEMEDEN zorla yeniden tara -- YENİ ceyrek dashboard'a
# EN FAZLA birkaç gun ICINDE yansir (mevcut Faz 12 takvim altyapisinin
# DOGAL bir tuketicisi, YENI veri kaynagi GEREKTIRMEZ).
```

---

## Eşikler ve ağırlıklar (tazelik pencereleri + rate-limit sabitleri)

| Sabit | Değer | Gerekçe |
|---|---|---|
| `SCAN_STALE_AFTER_DAYS` | **7 gün (v1, KESİN — kullanıcı onayladı)** | 90 gün, `spec_sektor_evren.md`'deki `SECTOR_STALE_AFTER_DAYS`'in (sektör/SIC TAKSONOMİSİ, YILDA belki 1 değişir) kavramıdır, mali tablo/skor VERİSİYLE KARIŞTIRILMAMALI. Çeyreklik raporlama takvimi: BİST'te KAP bildirim SON tarihi konsolide ~10 hafta/konsolide-olmayan ~9 hafta (çeyrek sonundan), ABD'de büyük filer'lar için 10-Q son tarihi 40-45 gün — ama şirketler bu PENCERE İÇİNDE HERHANGİ bir günde raporlayabilir (deadline'a YIĞILMA olsa da). 90 günlük bir tazelik, YENİ açıklanmış bir çeyreğin dashboard'da EN FAZLA 3 AY gecikmeyle görünmesi anlamına gelir — bir "piyasa dashboard'u" için KABUL EDİLEMEZ derecede eski. 7 gün: haftalık bir batch kadansı, YENİ bir çeyreğin dashboard'a EN FAZLA 1 hafta gecikmeyle yansımasını garanti eder, günlük tarama kadar AĞ-yoğun DEĞİLDİR. Fiyat/mali-tablo için AYRI pencere fikri BİLİNÇLİ olarak sonraki bir faza ERTELENDİ (bkz. §Veri bağımlılığı). |
| `SCAN_STALE_AFTER_DAYS_UNSUPPORTED` | **90 gün** | `scan_status in ("desteklenmiyor","veri_yok")` satırlar için — bir şirketin `financial_group`'u/veri kaynağı HAFTADA BİR yeniden denense bile SONUÇ DEĞİŞMEZ (kod desteği eklenmeden), bu yüzden bu iki durumda `spec_sektor_evren.md`'nin 90-günlük "nadiren değişen özellik" mantığı UYGULANIR (`sic_code`/`sirket_turu` ile AYNI istikrar sınıfı) — kuyruk gereksiz yere ISRARLA aynı başarısız ticker'ları DENEMEZ (refresh_universe.py'nin 404 kalıcı-işaretleme ilkesiyle AYNI). |
| `SCAN_PACING_SECONDS_BIST` | **0,3 sn** | İş Yatırım/KAP'ın DOKÜMANLI bir "istek/sn" limiti YOK (kod incelemesi, `isyatirim.py`/`kap_financials.py`) ama mevcut fetcher'lar zaten `config.HTTP_RATE_LIMIT_DELAY_SECONDS=1.0` retry-backoff'u VE (isyatirim.py satır 737/769'da GÖZLEMLENEN) çok-dönemli fetch İÇİ kendi bekleme mantığını taşıyor — `tarama_toplu.py`'nin EKSTRA ticker'lar-ARASI bekleme SABİTİ TEMKİNLİ/küçük tutulur (tam 643 BİST şirketi × 0,3 sn ≈ 3,2 dk EK gecikme, kabul edilebilir), amaç TEK bir IP'den kısa sürede yüzlerce SIRALI istek göndermenin (fetcher içi retry'lara EK olarak) sunucu tarafında ŞÜPHELİ/bloklanabilir bir örüntü OLUŞTURMASINI önlemek. |
| `SCAN_PACING_SECONDS_NASDAQ` | **0,15 sn** | SEC'in DOKÜMANLI limiti **10 istek/sn/IP** (`sec_edgar.py` modül notu, satır 13) — `SEC_BULK_PACING_SECONDS=0.12` (refresh_universe.py, Faz 2, SADECE `submissions` uç noktası için) İLE AYNI mertebede ama HAFİF YÜKSELTİLDİ (0,12→0,15) çünkü `compute_multi_lens_score_for_ticker()` NASDAQ için TEK bir `submissions` isteği DEĞİL, `companyfacts` (büyük XBRL payload) + fiyat geçmişi (Yahoo/`sec_edgar.fetch_price_history`) GİBİ BİRDEN FAZLA ardışık istek tetikler — aynı 10 istek/sn tavanına yaklaşırken EK bir güvenlik payı bırakılır. |
| `DEFAULT_LIMIT_BIST` | **200** | BİST evreni küçük (643) — 200'lük partiler 4 çalıştırmada TAMAMLANIR, `SCAN_PACING_SECONDS_BIST` ile 200×~birkaç-sn (mali tablo+fiyat fetch dahil, kaba tahmin) MAKUL bir cron penceresine (dakikalar) sığar. |
| `DEFAULT_LIMIT_NASDAQ` | **150** | NASDAQ per-company maliyeti (XBRL companyfacts + fiyat) BİST'ten yüksek — refresh_universe.py'nin `DEFAULT_NASDAQ_LIMIT=500` (SADECE SIC lookup, TEK istek) İLE KARIŞTIRILMAMALI. **Güncelleme (KESİN karar sonrası):** `--universe tam` artık ham ~4352 ticker DEĞİL, `filer_category` filtresinden geçmiş "kaliteli" bir alt küme tarar (bkz. §NASDAQ "tam evren" kapsamı) — bu, ilk-tur tam-taramanın süresini ÖNEMLİ ÖLÇÜDE kısaltır. Kesin gün sayısı `--dry-run` ile ÖLÇÜLMELİ (burada rakam UYDURULMADI); `150/gün` yine de TEMKİNLİ bir varsayılan olarak KORUNUR (filtrelenmiş evrenin gerçek büyüklüğü bilinmeden önce güvenli bir alt sınır). |

---

## Tazelik ve freshness politikası (KAPSAMLI)

### Katman 1 — Taksonomi tazeliği (Faz 2, DEĞİŞMEDİ)
`Company.sector_updated_at`, `SECTOR_STALE_AFTER_DAYS=90`
(`refresh_universe.py`) — `tarama_toplu.py`'nin ÖN KOŞULUDUR (bir ticker
`ust_sektor IS NULL` ise taranmaz, bkz. `get_scan_queue`), bu spec'in
KENDİSİ bu katmana DOKUNMAZ. `Company.filer_category` (YENİ, bkz. §NASDAQ
"tam evren" kapsamı) da BU katmanın bir parçasıdır — SIC ile AYNI
zenginleştirme adımında, AYNI 90 günlük pencerede tazelenir.

### Katman 2 — Ham finansal veri tazeliği (mevcut, DEĞİŞMEDİ)
`Company.last_updated`, `is_data_fresh(max_age_hours=12)`
(`_ensure_financials_cached`, `pipeline.py`) — `compute_multi_lens_score_
for_ticker()`'ın İÇİNDE, `tarama_toplu.py`'nin KONTROL ETMEDİĞİ bir
katman. **Kritik gözlem:** 12 saat, `tarama_toplu.py`'nin 7 GÜNLÜK Katman-3
penceresinden ÇOK DAHA KISA — pratik sonucu: `tarama_toplu.py` bir
ticker'ı 7 günde bir ELE ALDIĞINDA (Katman 3), Katman 2 HER SEFERİNDE
"bayat" bulacak (7 gün ≫ 12 saat) ve GERÇEK bir ağ fetch'i TETİKLENECEKTİR
— bu KASITLI ve DOĞRUdur: haftalık tarama dendiğinde veri GERÇEKTEN
tazelenir, "sahte tazelik" (eski veriyi yeniden imzalamak) OLUŞMAZ.

**Fiyat/OHLCV — AYRI BİR GÖZLEM (yeni bulgu, bu spec'te belgeleniyor):**
`price_history.fetch_ohlcv()` (kod incelemesi doğruladı) **HİÇBİR
freshness kontrolüne TABİ DEĞİL** — `compute_multi_lens_score_for_ticker()`
her çağrıldığında (Katman 2 "taze" bulsa BİLE) 400 günlük OHLCV'yi YENİDEN
ağdan çeker. Bu, mevcut kod tabanının (Faz 5'TEN ÖNCE var olan) bilinen bir
sınırlamasıdır — `tarama_toplu.py` bunu DÜZELTMEZ (kapsam dışı), ama
SONUCU AÇIKÇA üstlenir: `tarama_toplu.py`'nin 7 günlük döngüsünde HER
taranan ticker fiyat verisini o AN itibarıyla güncel çeker (fiyat AÇISINDAN
`MarketScanResult.computed_at` = fiyatın da tazelik damgasıdır, AYRI bir
`price_as_of` alanı GEREKMEZ çünkü ikisi ATOMIK olarak AYNI ANDA
hesaplanıyor).

### Katman 3 — Scan (batch skor) tazeliği (YENİ, bu spec'in sahipliğinde)
`MarketScanResult.computed_at`, `SCAN_STALE_AFTER_DAYS=7` (bkz. yukarıdaki
tablo) — `get_scan_queue()` bu alana bakar. **Tek-pencereli tasarım v1
için KESİN bir karardır (kullanıcı onayladı, 2026-08-12):** kullanıcının
orijinal önerisindeki "mali tablo İÇİN ayrı, fiyat/çarpan İÇİN ayrı"
ayrımının RUHU BİLİNÇLİ olarak SONRAKİ bir faza ERTELENDİ — bu ayrım
`compute_multi_lens_score_for_ticker()` fonksiyonunun ATOMIK doğası
nedeniyle (fiyat VE mali tablo TEK bir çağrıda BİRLİKTE üretiliyor, ayrı
ayrı güncellenemiyor) bu fazda UYGULANAMAZ — uygulanması
`compute_multi_lens_score_for_ticker()`'ın İKİYE bölünmesini (mali-tablo-
bağımlı skor hesaplama + hafif "sadece fiyat/çarpan güncelle" geçişi)
gerektirir, bu **Faz 5 kapsamının DIŞINDA bırakılan, açıkça işaretlenmiş
bir gelecek iyileştirmedir** (bkz. §Veri bağımlılığı). Bunun yerine: **tek
bir 7 günlük pencere** hem skoru HEM fiyatı/çarpanları BİRLİKTE tazeler —
BİST için ucuz (7 gün ≪ pratik sınır), NASDAQ için hem kademeli `--limit`
HEM `filer_category` filtresiyle (bkz. §NASDAQ "tam evren" kapsamı) zaten
TAMPONLANMIŞ.

### `/piyasa` komutu — freshness ile etkileşim (KESİN karar — kullanıcı onayladı)

**Karar: `/piyasa` YENİ bir tarama TETİKLEMEZ — SADECE mevcut `MarketScanResult`
anlık görüntüsünden dashboard.html'i YENİDEN ÜRETİR (render), ağa GİTMEZ.**
Bu, açık bir karardan KESİN bir tasarım kararına GEÇMİŞTİR (2026-08-12,
kullanıcı onayı) — aşağıdaki gerekçeler DEĞİŞMEDEN geçerlidir.

Gerekçe:
1. **Zamanlama uyumsuzluğu:** Tam bir tarama (Katman 3, tüm evren) dakikalar
   (BİST) ile GÜNLER (NASDAQ, rate-limit nedeniyle) arasında sürer —
   Telegram bot'unun bir komuta SANİYELER içinde yanıt vermesi beklenir
   (mevcut `/temel`/`/teknik` komutları bile ~20 sn ile ZATEN kullanıcı
   sabrının sınırında, kod içi mesajlardan görülüyor: "🔍 ... analiz
   ediliyor... (~20 sn)"). Tüm evreni SENKRON taramak bu modeli TAMAMEN
   BOZAR.
2. **Eş-zamanlılık riski:** `tarama_toplu.py` zaten ZAMANLANMIŞ (cron)
   çalışıyorken bir kullanıcının `/piyasa` ile AYNI ANDA tam bir tarama
   TETİKLEMESİ aynı DB satırlarına ÇAKIŞAN yazımlara (veya en kötü
   ihtimalle rate-limit ihlaline, iki eşzamanlı SEC EDGAR taramasının
   BİRLEŞİK istek hızının 10/sn'yi AŞMASINA) yol açabilir.
3. Bu tasarım, mevcut projede **AYNI PRENSİBİN** zaten var olan bir
   örneğidir: `refresh_universe.py`/`refresh_sector_cache.py`/`refresh_
   takvim_cache.py` "AYRI, zamanlanmış bir süreç, ana pipeline'ı BLOKE
   ETMEZ" ilkesiyle çalışır (quaxis-mimari skill madde altındaki bilinen
   desen) — `tarama_toplu.py` de operatör tarafından ELLE veya cron İLE
   tetiklenir, BOTA BAĞLANMAZ.

**Somut davranış:**
```
/piyasa komutu:
  1. src.render.dashboard.generate_dashboard_html() cagirir (YENI, Faz 5
     adim 3 -- render katmani, HESAPLAMA YAPMAZ, sadece MarketScanResult'i
     OKUR + JSON'a gomer + Jinja2 ile HTML uretir).
  2. Uretilen output/dashboard.html'i Telegram'a `send_document` ile
     GONDERIR (PNG kart DEGIL, dosya eki).
  3. Mesaj govdesinde ACIKCA bir "Son guncelleme: {en eski Katman-3
     computed_at, market bazinda}" damgasi GOSTERILIR -- orn. "BIST verisi
     3 saat once, NASDAQ verisi 2 gun once tarandi" (get_last_scan_
     generated_at(), market bazinda MIN(computed_at) -- EN GUNCEL DEGIL EN
     ESKI taranani gosterir, cunku dashboard'daki EN BAYAT satir budur,
     kullaniciyi YANILTMAMAK icin "en iyimser" degil "en kotumser" zaman
     damgasi tercih edilir).
  4. HAFIF bir DEBOUNCE (ZORUNLU DEGIL, oneri): son 5 dakika icinde
     baska bir /piyasa cagrisi HTML'i ZATEN urettiyse, DISK'teki dosya
     TEKRAR gonderilir (Playwright/agir islem YOK burada -- salt HTML,
     maliyet ZATEN dusuk, debounce sadece gereksiz tekrar disk yazimini
     onler, KRITIK degildir).
```

**Force-refresh yolu (operatör-only, bot-DIŞI):** Bir yönetici tam/kısmi
tazeleme istiyorsa `python scripts/tarama_toplu.py [--market ...]`'i
ELLE/cron ile çalıştırır — bu, bot komutlarının HİÇBİRİNİN network-ağır
toplu işler TETİKLEMEMESİ (mevcut proje genelindeki `refresh_*.py`
scriptleri hiçbiri botTan çağrılmıyor) ilkesiyle TUTARLIDIR. **Kapsam
netliği (bilgi amaçlı not, KESİN kararın bir parçası DEĞİL, ayrı bir
gelecek konusu):** İleride "belirli bir ticker'ı /piyasa'dan BAĞIMSIZ
olarak `/degerleme`/`/temel` gibi ANLIK yeniden hesapla" isteği gelirse bu
MEVCUT tekil-ticker akışlarıyla (12 saatlik Katman-2 tazelik) ZATEN
karşılanıyor — `/piyasa`'nın kapsamı SADECE ÇOK-şirketli toplu görünümdür,
bu spec tekil ticker akışına DOKUNMAZ.

---

## Dashboard'a gömülecek JSON şeması

**Üretim sorumluluğu:** `src/render/dashboard.py::build_dashboard_data()`
(YENİ, Faz 5 adım 3, kart-tasarımcısı/kod-geliştirici) — `MarketScanResult`
satırlarını okur, aşağıdaki şemaya SERİLEŞTİRİR (render katmanı SADECE
OKUMA+GRUPLAMA yapar, HESAPLAMA yapmaz — `kart-tasarim-sistemi` skill:
"HTML hesaplama yapmaz, sıralama/filtre saf sunum işlemidir", gruplama da
AYNI ilkeye tabi saf-agregasyon işlemidir).

```jsonc
{
  "meta": {
    "generated_at": "2026-08-12T14:03:00Z",     // dashboard.html'in URETIM ani
    "bist_last_scan_at": "2026-08-12T09:11:00Z", // MIN(computed_at) BIST icinde (en kotumser, bkz. Tazelik)
    "nasdaq_last_scan_at": "2026-08-10T22:40:00Z",
    "bist_company_count": 643,
    "nasdaq_company_count": 187,                  // O ANA KADAR taranmis sayisi (nasdaq_universe_total'in TAMAMI DEGIL, bkz. Kenar durumlar)
    "nasdaq_universe_total": null                  // FİLTRELENMİŞ ("kaliteli", filer_category tabanlı) NASDAQ hedef evren toplami -- KESIN sayi `--dry-run` ile OLCULUP buraya yazilir (bu spec'te SAYI UYDURULMADI, bkz. §NASDAQ "tam evren" kapsamı); kodlama fazina kadar `null` kabul edilebilir
  },
  "markets": {
    "BIST": {
      "sectors": [
        {
          "ust_sektor": "Sanayi",
          "sirket_turu_kirilimi": {"sanayi": 38, "gyo": 4},  // ayni ust_sektor icinde sirket_turu dagilimi (GYO gibi farkli-sablonlu satirlarin FARK EDILEBILMESI icin)
          "n": 42,
          "yetersiz_ornek": false,               // n>=MIN_SECTOR_N(5)
          "companies": [ { /* satir semasi asagida */ } ]
        },
        {
          "ust_sektor": "Sağlık",
          "n": 4,
          "yetersiz_ornek": true,                 // n<5 -- sektor-siniflandirma skill madde 1
          "companies": [ /* ... */ ]
        },
        {
          "ust_sektor": "Sınıflandırılmamış",      // ust_sektor IS NULL (Kenar durumlar)
          "n": 2,
          "yetersiz_ornek": null,                  // n<5 kurali BU grup icin ANLAMSIZ (karsilastirma amacli degil)
          "companies": [ /* ... */ ]
        }
      ]
    },
    "NASDAQ": { "sectors": [ /* ayni sema */ ] }
  }
}
```

**Satır (şirket) şeması:**
```jsonc
{
  "ticker": "THYAO",
  "company_name": "Türk Hava Yolları A.O.",
  "market": "BIST",
  "ust_sektor": "Sanayi",
  "sirket_turu": "sanayi",
  "template": "sanayi",
  "period": [2026, 6],
  "scan_status": "ok",                 // "ok" | "hata" | "desteklenmiyor" | "veri_yok"
  "computed_at": "2026-08-12T09:11:00Z",
  "mercekler": {
    "deger":    {"score": 7.2, "badge": "SAĞLAM",  "data_coverage_pct": 88.0},
    "kalite":   {"score": 6.8, "badge": "DENGELİ",  "data_coverage_pct": 100.0},
    "buyume":   {"score": 5.1, "badge": "KARIŞIK",  "data_coverage_pct": 62.0},
    "guvenlik": {"score": 7.9, "badge": "SAĞLAM",  "data_coverage_pct": 100.0}
  },
  "bilesik": {
    "score": 6.9,
    "badge": "DENGELİ",
    "data_coverage_pct": 87.5,          // hesapla_veri_kapsam_ozeti() (Formüller-0)
    "dahil_edilen_mercekler": ["değer", "kalite", "güvenlik", "büyüme"]
  },
  "carpanlar": {
    "price": 305.50, "market_cap": 428500000000,
    "pe_ratio": 6.8, "pb_ratio": 2.1, "ev_ebitda": 4.3, "currency": "TRY"
  },
  "veri_uyarilari": [
    // PIYASA_SISTEMIK_EKSIK_BILESENLER statik tablosundan (asagi bkz.),
    // template+market'e gore ONCEDEN belirlenmis, ETIKETLI uyarilar --
    // company-SPESIFIK DEGIL, TUM ayni-sablon+ayni-piyasa satirlarinda
    // AYNI liste gorunur (bkz. Veri eksikligi gorunurlugu)
    {"mercek": "kalite", "bilesen": "SG&A/Ar-Ge/Faiz Gideri", "tur": "yapisal", "aciklama": "BİST'te bu kalemler KAP XBRL'de standart etiketlenmemiş, sistemik eksik"},
    {"mercek": "değer", "bilesen": "Temettü Verimi", "tur": "yapisal", "aciklama": "BİST'te DPS verisi henüz çekilmiyor"}
  ]
}
```

**Hatalı/desteklenmeyen satır örneği (`scan_status != "ok"`):**
```jsonc
{
  "ticker": "XYZCO", "market": "NASDAQ", "ust_sektor": "Teknoloji",
  "scan_status": "veri_yok", "computed_at": "2026-08-05T03:11:00Z",
  "mercekler": null, "bilesik": null, "carpanlar": null, "veri_uyarilari": []
}
```

---

## Veri eksikliği görünürlüğü (BİST/NASDAQ asimetri haritası)

`docs/spec/veri_tamlik_notu.md` §1-6'daki bulgular, dashboard'un
`veri_uyarilari` alanını besleyen **statik, market+template bazlı bir
etiket tablosuna** dönüştürülür (`src/render/dashboard.py` içinde sabit
sözlük, `PIYASA_SISTEMIK_EKSIK_BILESENLER` — company-spesifik DEĞİL, bu
yüzden `MarketScanResult`'a YAZILMAZ, render ANINDA `template`+`market`e
göre EKLENİR):

| Mercek bileşeni | BİST durumu | NASDAQ durumu | Dashboard etiketi |
|---|---|---|---|
| Kalite: SG&A/Brüt Kâr, Ar-Ge/Brüt Kâr | **YAPISAL eksik** (kategori C — KAP XBRL etiketi araştırılmadı, YÜKSEK maliyet) | **GEÇİCİ eksik** (kategori B — `us-gaap:SellingGeneralAndAdministrativeExpense`/`ResearchAndDevelopmentExpense` standart, DÜŞÜK maliyetle açılabilir ama HENÜZ kodlanmadı) | BİST: "yapısal" (kırmızı/kalıcı ton) — NASDAQ: "geçici" (turuncu/yakında-kapanabilir ton) |
| Kalite: Hazine Hissesi Düzeltmeli ROE | **YAPISAL eksik** (nadiren ayrı raporlanır) | **GEÇİCİ eksik** (`us-gaap:TreasuryStockValue` neredeyse evrensel, ÖNCELİKLENDİRİLMESİ ÖNERİLEN bir kazanım — spec'in kendi AAPL örneği bunu doğrudan çözer) | BİST: "yapısal" — NASDAQ: "geçici (öncelikli)" |
| Güvenlik: Faiz Karşılama Oranı | **YAPISAL eksik** (kitaplar arası EN SIK tekrarlanan açık, KAP alt-kalem araştırması gerekli) | **GEÇİCİ eksik** (`us-gaap:InterestExpense` standart tag, ORTA-DÜŞÜK maliyet) | BİST: "yapısal" — NASDAQ: "geçici" |
| Değer/Büyüme: Temettü Verimi / DPS-Payout | **YAPISAL eksik** (KAP XBRL etiketi araştırılmadı, ORTA maliyet) | **GEÇİCİ eksik** (`us-gaap:CommonStockDividendsPerShareDeclared` standart, DÜŞÜK maliyet) | BİST: "yapısal" — NASDAQ: "geçici" |
| Büyüme: Capex oranı | **GEÇİCİ eksik** (KAP `ifrs-full_PurchaseOfPropertyPlantAndEquipment`, ORTA maliyet — İKİ piyasada da somut kaynak var) | **GEÇİCİ eksik** (`us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`, ORTA-DÜŞÜK maliyet) | Her iki piyasa: "geçici" |
| Değer: NASDAQ opsiyon/warrant seyreltme | Uygulanamaz (BİST'te bu kavram YOK) | **YAPISAL/kısmi-C** (kaba vekil türetilebilir ama dipnot düzeyi tam veri YOK) | Sadece NASDAQ satırlarında: "kısmi" |
| Büyüme: 10+ yıllık trend serisi | **YAPISAL eksik** (`MAX_TREND_PERIODS=12`, ~3 yıl) | **YAPISAL eksik** (AYNI kısıt, piyasa-bağımsız) | Her iki piyasa: "yapısal (mimari kısıt)" |
| Güvenlik: Kredi notu/harici temerrüt olasılığı | **YAPISAL eksik** (harici API entegrasyonu yok) | **YAPISAL eksik** (AYNI) | Her iki piyasa: "yapısal (harici veri kaynağı gerekir)" |

**Kart-tasarımcısına devir notu (Faz 5 adım 3 girdisi):** Yukarıdaki tablo
üç ETİKET türü üretir — `"yapisal"` (uzun-vadeli, muhtemelen HİÇ
kapanmayacak — UI'da SÖNÜK/kalıcı bir uyarı ikonu ÖNERİLİR), `"gecici"`
(kısa-orta vadede kod eklenirse kapanabilir — UI'da "yakında" imalı bir ton
ÖNERİLİR), `"gecici (oncelikli)"` (Treasury Stock/NASDAQ gibi ÖZELLİKLE
düşük-maliyetli, öncelik sırası YÜKSEK — UI'da BELKİ farklı vurgulanabilir).
**Bu üç tonun TAM görsel karşılığı (renk/ikon) kart-tasarımcısının kararıdır**
— bu spec sadece VERİYİ ve ANLAM AYRIMINI sağlar (veri_tamlik_notu.md'nin
"NASDAQ ucuz, BİST pahalı" asimetri bulgusunun kaybolmadan UI'ya
TAŞINMASI, kullanıcının kritik isteği).

**Şirket-spesifik (tekil) eksik veri ile KARIŞTIRILMAMASI:** Yukarıdaki
tablo PİYASA-GENELİ, sistemik eksiklikleri kapsar. Tek bir şirketin O
DÖNEME özgü eksik verisi (örn. yalnızca bir çeyrek raporunda bir kalem
eksik) `mercekler.{mercek}.data_coverage_pct` alanı ÜZERİNDEN zaten
görünür — bu satır bazlı sayı, `veri_uyarilari`'ndaki PİYASA-geneli
etiketlerden AYRI bir sinyaldir, ikisi dashboard'da FARKLI görsel
katmanlarda sunulmalıdır (kart-tasarımcısı kararı).

---

## Sektör ayarlaması

`sektor-siniflandirma` skill madde 1 (n≥5) dashboard GRUPLAMA seviyesinde
BİREBİR uygulanır — `src/render/dashboard.py::build_dashboard_data()`
her `(market, ust_sektor)` grubu için `n = len(companies)` sayar (BURADA
`SectorMetricCache`'e GİTMEZ — o tablo mercek-İÇİ z-skoru için farklı bir
`(ust_sektor, sirket_turu)` kırılımı taşır, dashboard'un GRUP SAYISI ise
SADECE o an DB'de `MarketScanResult` satırı OLAN şirketlerin ham sayımıdır,
AYRI bir hesaplama). `n<5` ise `yetersiz_ornek=true` — kart-tasarımcısı bu
grubun BAŞLIĞINDA "sektör karşılaştırması için yetersiz örneklem (n=X)"
notu GÖSTERMELİDİR (skill'in AYNEN istediği metin).

`"Sınıflandırılmamış"` sözde-grubu (bkz. JSON şeması) BU KURALA TABİ
DEĞİLDİR (`yetersiz_ornek: null`) — zaten sektör KARŞILAŞTIRMASI amaçlı bir
grup değil, sadece "henüz sınıflandırılamamış ama TARANMIŞ" şirketlerin
toplama kutusudur.

---

## Kenar durumlar

- **`ust_sektor IS NULL` (Faz 2 taksonomisi henüz o ticker'ı işlememiş):**
  `get_scan_queue()` bu satırı ADAY LİSTESİNE ALMAZ (yeni tarama
  TETİKLEMEZ) — ama eğer `MarketScanResult`'ta ESKİDEN kaydedilmiş bir
  satır varsa (örn. taksonomi sonradan `NULL`'a döndüyse — pratikte
  OLMAMASI gereken ama teorik bir durum) dashboard bunu `"Sınıflandırılmamış"`
  grubunda GÖSTERMEYE DEVAM EDER (Kural 3: var olan veri SİLİNMEZ/gizlenmez,
  sadece doğru gruba düşer).
- **`Company.filer_category IS NULL` (NASDAQ, henüz zenginleştirilmemiş
  VEYA SEC'te kategori boş):** `get_scan_queue(market="NASDAQ",
  universe="tam", ...)` bu satırı GÜVENLİ TARAFTA DIŞLAR (bkz. §NASDAQ
  "tam evren" kapsamı) — ama `--universe nasdaq30` (pilot, sabit liste)
  bu satırı YİNE DE tarar (filtre SADECE `--universe tam` içindir).
- **`scan_status="hata"` (transient ağ hatası):** Satır `MarketScanResult`'ta
  bir ÖNCEKİ BAŞARILI taramanın skorlarıyla KALIR (upsert SADECE
  `scan_status`/`error_detail`/`computed_at` günceller, `deger_score` vb.
  alanlar EZİLMEZ) — dashboard "eski ama gerçek" bir skor gösterir,
  SESSİZCE boş satır GÖSTERMEZ (Kural 3: yanlış rakamdan İYİDİR ilkesinin
  BURADAKİ karşılığı: BOŞ göstermek de bir tür "yanlış" izlenimdir, en son
  BİLİNEN gerçek değer daha DOĞRU bir varsayılandır) — `computed_at`
  GÜNCELLENMEZ bu durumda (henüz gerçek bir yeniden-hesaplama OLMADI),
  SADECE `last_attempt_at` benzeri bir iç log alanı (opsiyonel,
  `error_detail` zaten bunu taşır) güncellenir. **Netleştirme:** İlk kez
  taranan bir ticker `"hata"` alırsa (önceki başarılı kayıt YOK) tüm skor
  alanları `NULL` kalır, dashboard `"hata"` rozeti + boş mercek profili
  gösterir.
- **`scan_status="desteklenmiyor"` (`UnsupportedCompanyTypeError`):**
  Örn. `financial_group` 5 desteklenen türün dışında yeni/nadir bir KAP
  sınıflandırması ise — dashboard satırı GÖSTERİLİR ama mercekler `null`,
  `veri_uyarilari`'na `{"tur": "desteklenmiyor", "aciklama": "..."}` eklenir
  (SESSİZCE ATLANMAZ, kullanıcı O ŞİRKETİN var olduğunu ama henüz
  skorlanamadığını GÖRÜR).
- **GYO şirketleri (`sirket_turu="gyo"`, `template="sanayi"`):** Skor
  ÜRETİLİR ama `veri_uyarilari`'na sabit bir not eklenir: "Bu şirket bir
  GYO — F/K, ROE gibi standart sanayi çarpanları bir REIT için doğrudan
  KARŞILAŞTIRILABİLİR olmayabilir (NAV/portföy değeri bazlı özel bir
  değerleme çerçevesi bu mimaride HENÜZ YOK)." — dürüstlük, gizlenmez
  (bilgi amaçlı bir sınırlama, onay GEREKTİRMEDİ).
- **Banka/sigorta Büyüme merceği geçici "YETERSİZ VERİ" (bkz. `spec_
  bilesik_skor.md` Kenar durumlar — `BankRatios`'a YoY kredi/mevduat
  büyüme alanı henüz eklenmemişse):** `mercekler.buyume = null` (ya da
  `{"score": null, "badge": "YETERSİZ VERİ", ...}`), `bilesik` YİNE DE
  ÜRETİLİR (3 mercek üzerinden, ağırlık yeniden dağıtılmış) — dashboard
  bu satırı ATLAMAZ.
- **Aynı ticker'ın BİST/NASDAQ çakışması:** `MarketScanResult.ticker` TEK
  PK'dır — `TickerMarketConflictError` zaten `Company` seviyesinde
  ÖNLENDİĞİ için (Faz 2) bu tabloda AYRICA bir çakışma riski YOK (bir
  ticker'ın SADECE bir `Company.market` değeri olabilir).
- **`--universe bist30`/`nasdaq30` ile taranan ama Faz-2 evreninde
  OLMAYAN bir ticker (teorik, ÇEKİRDEK liste her zaman DB'de mevcut
  olduğundan pratikte OLMAZ):** `compute_multi_lens_score_for_ticker()`
  KENDİSİ zaten `_get_or_create_company` ile Company satırını yoksa
  OLUŞTURUR (mevcut davranış) — `tarama_toplu.py` bunun ÜZERİNE bir şey
  EKLEMEZ, mevcut idempotent davranışa GÜVENİR.
- **`--universe bist30/nasdaq30`'daki bir ticker'ın (örn. `TRALT`) DB'de
  yetersiz finansal geçmişi/kısa halka arz sonrası ilk çeyreği olması:**
  `compute_multi_lens_score_for_ticker()` mevcut kenar-durum davranışını
  (bkz. `spec_bilesik_skor.md` "Halka arzın 1. çeyreği" senaryosu) AYNEN
  izler — `scan_status="ok"` ama Büyüme merceği/Piotroski KISMİ/`null`
  olabilir; `tarama_toplu.py` bunu ÖZEL olarak ELE ALMAZ, mevcut mercek
  davranışına GÜVENİR.
- **NASDAQ evreninin (filtrelenmiş "kaliteli" hedef) TAMAMI henüz
  taranmamışken dashboard üretilirse:** `meta.nasdaq_company_count`
  (taranmış) ile `meta.nasdaq_universe_total` (filtrelenmiş hedef toplam,
  `--dry-run` ile ölçülüp doldurulur) ARASINDAKİ FARK JSON'da AÇIKÇA
  taşınır (bkz. Şema) — kart-tasarımcısı bunu "NASDAQ evreninin %X'i şu
  ana kadar tarandı" gibi bir İLERLEME göstergesine çevirebilir, sahte bir
  "TAM evren" izlenimi VERİLMEZ.

---

## Test senaryoları

1. **`get_scan_queue` sıralama/filtreleme:** `ust_sektor IS NULL` satırlar
   HARİÇ tutulur; `MarketScanResult` hiç YOK olan satırlar (hiç taranmamış)
   `computed_at` 8 gün önce taranmış satırlardan ÖNCE gelir (ikisi de
   kuyrukta, ama "hiç taranmamış" her zaman EN öncelikli); `computed_at`
   3 gün önce (7 günden TAZE) olan satırlar kuyruğa GİRMEZ; `limit`
   parametresine uyulur.
2. **Öncelik kümesi (`priority_tickers`):** `EarningsCalendar.expected_date`
   bugünden 2 gün SONRA olan bir ticker, `computed_at` 2 gün önce (7
   günden TAZE) olsa BİLE kuyruğa GİRER (force-check).
3. **`hesapla_veri_kapsam_ozeti`:** THYAO benzeri (4 mercek de dolu,
   coverage'lar sırasıyla 88/100/62/100) girdide ağırlıklı ortalama
   ELLE hesaplanan değere `Decimal("0.01")` toleransla EŞİT çıkar. Banka
   (AKBNK, Büyüme=None) girdisinde sadece 3 mercek üzerinden hesaplanır
   (Büyüme PAYDAYA/PAYA GİRMEZ).
4. **`tarama_toplu.py --universe bist30` uçtan uca (gerçek ağ, ~dakikalar):**
   THYAO/ASELS/AKBNK/ANSGR/KTLEV dahil 32 ÇEKİRDEK+EK ticker için
   `MarketScanResult` satırları `scan_status="ok"` ile oluşur (birkaçının
   `TRALT` gibi `veri_yok` dönmesi KABUL EDİLEBİLİR, bkz. Kenar durumlar),
   `bilesik_score` `[0,10]` aralığında, `dahil_edilen_mercekler` boş DEĞİL.
5. **`scan_status="hata"` sonrası eski skor KORUNUR:** Bir ticker için ÖNCE
   başarılı bir tarama simüle edilir (`deger_score=7.2` ile satır
   yaratılır), sonra `compute_multi_lens_score_for_ticker` bir
   `httpx.RequestError` FIRLATACAK şekilde mock'lanır, upsert çağrılır —
   sonuç: `scan_status="hata"`, `deger_score` HÂLÂ `7.2` (EZİLMEDİ).
6. **Dashboard JSON — n<5 uyarı bayrağı:** 4 şirketlik bir `(BIST, "Sağlık")`
   grubu `build_dashboard_data()`'ya verildiğinde çıktı JSON'unda
   `yetersiz_ornek: true` VE `n: 4` görülür; 5. bir şirket eklendiğinde
   `yetersiz_ornek: false`'a DÖNER (sınır testi).
7. **GYO uyarı notu:** `sirket_turu="gyo"` bir satırın `veri_uyarilari`
   listesinde GYO notunun VAR olduğu, `sirket_turu="sanayi"` bir satırda
   BU notun HİÇ görünmediği doğrulanır.
8. **`/piyasa` komutu ağa GİTMEZ:** `generate_dashboard_html()` çağrısı
   sırasında `compute_multi_lens_score_for_ticker`/fetcher modüllerinin
   HİÇBİRİNİN çağrılmadığı (mock/patch ile) doğrulanır — SADECE
   `get_market_scan_results()` (DB okuma) çağrılır.
9. **`SCAN_STALE_AFTER_DAYS_UNSUPPORTED` ayrımı:** `scan_status="desteklenmiyor"`
   bir satır 10 gün önce işlenmişse (7 günden eski AMA 90 günden taze)
   `get_scan_queue()`'nun STANDART (7 gün) çağrısında kuyruğa GİRMEDİĞİ
   — sadece 90-günlük özel sorguda (veya `stale_after_days=90` parametresiyle
   çağrıldığında) göründüğü doğrulanır.
10. **NASDAQ `filer_category` kalite filtresi:** `filer_category="Non-
    accelerated filer"` olan bir `Company`, `get_scan_queue(market=
    "NASDAQ", universe="tam", ...)` sonucuna GİRMEZ ("non-accelerated"
    alt-dizgi tuzağı test edilir — "accelerated filer" alt dizgisini
    İÇERDİĞİ İÇİN naif bir `LIKE '%accelerated filer%'` filtresi bunu
    YANLIŞLIKLA dahil ederdi); `filer_category="Large accelerated filer"`
    olan bir `Company` GİRER; `filer_category=None` (henüz
    zenginleştirilmemiş) olan GİRMEZ (güvenli taraf); `--universe
    nasdaq30` (pilot) çağrısı bu filtreden BAĞIMSIZ olarak sabit listedeki
    TÜM ticker'ları `filer_category` değerine BAKMAKSIZIN getirir.

---

## Veri bağımlılığı (bu fazda AÇIK bırakılan, gelecek iyileştirme notları)

- **Fiyat/çarpan ile mali-tablo skorlarının AYRI tazelik pencereleriyle
  güncellenmesi (kullanıcı bu turda ONAYLADI: v1 TEK pencere ile devam,
  bu madde SONRAKİ bir faza ERTELENDİ, artık açık bir "onay bekleyen"
  karar DEĞİL, bilinçli bir kapsam sınırıdır):**
  `compute_multi_lens_score_for_ticker()`'ın İKİYE bölünmesini gerektirir
  (ağır: tam mercek hesaplama vs. hafif: sadece fiyat+çarpan yeniden-çek)
  — Faz 5 KAPSAMI DIŞINDA, gelecekte `SCAN_STALE_AFTER_DAYS` yerine
  `SCAN_STALE_AFTER_DAYS_SCORE` (örn. 7) + `SCAN_STALE_AFTER_DAYS_PRICE`
  (örn. 1) ikilisi ile YENİDEN TASARLANABİLİR.
- **NASDAQ "tam evren" tanımının daraltılması — ÇÖZÜLDÜ (kullanıcı
  onayladı, 2026-08-12):** Bu madde ARTIK açık DEĞİL — bkz. §NASDAQ "tam
  evren" kapsamı (KESİN karar, `filer_category` tabanlı filtre). Geriye
  kalan TEK şey kodlama fazına bırakılan somut implementasyon adımlarıdır
  (yeni `Company.filer_category` sütunu + migration + `sec_edgar.
  SicInfo` genişletmesi + tek seferlik backfill kuyruğu, hepsi §NASDAQ
  "tam evren" kapsamı bölümünde adım adım tanımlı).
- **`bist30`/`nasdaq30` 20+20 ek ticker'ın araştırılması — ÇÖZÜLDÜ
  (kullanıcı talebiyle bu oturumda WebSearch/WebFetch ile yapıldı):**
  Bkz. §çekirdek ticker kümesi (dipnotlar[^bist30][^ndx] kaynak+tarih
  taşır). Kalan TEK açık nokta ARTIK bir onay konusu DEĞİL, sadece bir
  BAKIM notudur: BİST30 üç ayda bir, Nasdaq-100 yıllık+ad-hoc yeniden
  dengelendiği için bu statik listelerin PERİYODİK olarak (örn. her
  çeyrek) yeniden gözden geçirilmesi ÖNERİLİR — pilot doğrulama amaçlı
  olduğundan (üretim skorlamasını ETKİLEMEZ) bu KRİTİK değildir.
- **`price_history.fetch_ohlcv()`'nin DB önbelleksiz olması:** Bu spec'in
  KEŞFETTİĞİ ama DÜZELTMEDİĞİ bir mevcut-kod sınırlaması — Faz 5'in
  7-günlük Katman-3 penceresi bu maliyeti DOLAYLI olarak sınırlar (fiyat
  SADECE tarama anında çekilir, ara sıklıkta DEĞİL) ama tekil-ticker
  interaktif akışlarında (`/temel`, `/degerleme`) HÂLÂ her çağrıda ağa
  gidiyor olması AYRI bir performans/maliyet konusu (bu spec'in kapsamı
  DIŞINDA, ileride bir DB fiyat önbelleği eklenmesi önerilebilir).
