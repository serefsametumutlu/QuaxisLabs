# SPEC: Veri Tamlığı Yol Haritası (Konsolide Envanter + Önceliklendirme)

## Amaç ve kapsam

**Ölçtüğü soru:** Bu spec bir SKORLAMA spec'i DEĞİLDİR — dashboard'un
metodoloji panelinde ve `docs/spec/spec_mercek_{deger,kalite,buyume,
guvenlik}.md` + `bilgi-bankasi/{01,02,03}_*.md` + `docs/spec/
veri_tamlik_notu.md` içinde dağınık biçimde işaretlenmiş TÜM "VERİ EKSİK"/
"KISMEN MEVCUT"/"kapsam dışı" kalemlerini TEK bir envanterde toplar, maliyet
ARTAN sırada önceliklendirir ve `kod-gelistirici`'ye devredilebilecek somut
bir "İlk Dalga" listesi çıkarır. **Kod içermez, eşik/formül tanımlamaz** —
sadece hangi kalemin, hangi maliyetle, hangi kaynaktan, hangi merceği/
piyasayı açacağının haritasıdır.

**Geçerli şirket türleri / piyasalar:** BİST + NASDAQ, `sanayi`/
`abd_sanayi` birincil; banka/sigorta/finansman/gyo notları ilgili
maddelerde ayrıca işaretlenir.

**ÖNEMLİ ÖN-NOT — güncellik durumu (2026-08-12 itibarıyla doğrulandı):**
Faz 3a'da yazılan 4 mercek spec'i + `spec_bilesik_skor.md` Faz 3b'de
**zaten kodlandı** (`src/analysis/lens_deger.py`, `lens_kalite.py`,
`lens_buyume.py`, `lens_guvenlik.py`, `lens_bilesik_skor.py` — kod
okumasıyla doğrulandı: `_skor_roa`, Merton↔`lens_guvenlik.py` köprüsü,
`_skor_toplam_yukumluluk_ozkaynak`, `_skor_nakit_kar_kalitesi` GİBİ
00_sentez §4'ün "düşük-maliyetli kazanımlar" listesindeki maddeler ARTIK
MEVCUT). Bu yüzden **bu spec'in tek doğru "şu an ne eksik" kaynağı**
`src/render/dashboard.py::PIYASA_SISTEMIK_EKSIK_BILESENLER` sözlüğüdür —
kod okumasıyla doğrulandı ki `lens_kalite.py`/`lens_deger.py` içinde SG&A/
Ar-Ge/temettü/hazine-hissesi/faiz-gideri için grep SIFIR sonuç verdi (yani
bu kalemler placeholder/None olarak bile denenmemiş, dashboard'un statik
uyarı listesi GÜNCEL). Bu spec, o statik listeyi (17 piyasa-satırı, aşağıda
~19 tekil kaleme deduplike edilir) kitap-seviyesi gerekçe/kaynak ile
zenginleştirir ve MEVCUT olmayan (henüz dashboard'a bile girmemiş) daha
derin/yapısal kalemleri (WACC/beta, sahiplik yapısı, çok-firma regresyon
altyapısı, dipnot okuma) EKLER.

**Kaynaklar (okundu, bu turda YENİDEN kod yazılmadı):**
1. `src/render/dashboard.py::PIYASA_SISTEMIK_EKSIK_BILESENLER` (satır
   91-133) — CANLI/güncel "hâlâ eksik" listesi, `tur` alanı taksonomisi
   (`yapisal`/`gecici`/`gecici_oncelikli`/`kismi`) AYNEN kullanılır.
2. `docs/spec/veri_tamlik_notu.md` (§1-7) — spec'lerin kod-doğrulamalı
   çapraz kontrolü, NASDAQ/BİST maliyet asimetrisi bulgusu.
3. `bilgi-bankasi/00_sentez.md` §3 (Metrik→Kod Çapraz Referans, ~32 satır)
   ve §4 (13 maddelik konsolide eksiklik + 10 maddelik düşük-maliyetli
   kazanım listesi) — üç kitabın TAM METNİ okunarak üretilmiş sentez.
4. `bilgi-bankasi/{01,02,03}_*.md` içindeki ham "VERİ EKSİK"/"KISMEN
   MEVCUT" satırları (grep ile tarandı: 01'de ~10, 02'de ~15, 03'te ~95+
   ayrı satır — kullanıcının belirttiği 159+22 rakamıyla tutarlı büyüklük
   mertebesinde) — BÜYÜK ÇOĞUNLUĞU 00_sentez §3-4'te ZATEN deduplike
   edilmiş birkaç kök nedene (DPS, 10-yıllık seri, interest_expense, Capex,
   WACC/beta, treasury_stock, SG&A/Ar-Ge, sahiplik yapısı, çok-firma
   regresyon altyapısı, dipnot okuma) indirgeniyor — bu spec o dedup
   işlemini TEKRAR YAPMAZ, 00_sentez'in kendisini kaynak alır (persona
   kural: "var olan maliyet notlarını yeniden icat etme").
5. `bilgi-bankasi/_ilerleme.md` — "geliştirme öncelik özeti (en ucuzdan en
   pahalıya)" bölümü (satır 126-137) ve Kısım 7 notundaki Devir Hızı/
   Amihud İlliquidity bulgusu (satır 187) — 00_sentez'e GİRMEMİŞ 1 ek
   ucuz kazanım.
6. `docs/spec/spec_mercek_{deger,kalite,buyume,guvenlik}.md` Girdiler
   tabloları — piyasa kırılımlı (BİST/NASDAQ) somut tag önerileri.
7. Statik kod doğrulaması (Bash/kod ÇALIŞTIRILMADI, sadece okundu):
   `src/fetchers/kap.py`, `src/fetchers/sec_edgar.py`, `src/analysis/
   lens_kalite.py`, `lens_deger.py`, `lens_guvenlik.py` — §5 (Faaliyet
   Raporu bölümü) ve ön-not için.

---

## Envanter tablosu (maliyet artan sırada, deduplike)

**Sütun tanımları:** *Kalem* = ham veri/oran kavramı (tekil, piyasa/
mercek tekrarları birleştirilmiş) · *Mercek(ler)* = hangi mercek(ler)in
Girdiler tablosunda geçiyor · *Piyasa* = BİST/NASDAQ/İkisi · *`tur`* =
`dashboard.py`'nin taksonomisi (sadece zaten dashboard'ta olan kalemlerde
dolu; YENİ ise "—") · *Maliyet* = kaynaklardaki NOTUN aktarımı (icat
edilmedi) · *Kaynak* = somut tag/yöntem · *Gerekçe* = kısa özet + kitap
kodu.

### GRUP 1 — UCUZ (tek standart tag ekleme veya sıfır yeni fetcher)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Veri kaynağı | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-01 | SG&A / Brüt Kâr | Kalite | NASDAQ | `gecici` | UCUZ | `us-gaap:SellingGeneralAndAdministrativeExpense` — standart, yaygın raporlanan US GAAP tag'i; `sec_edgar.py::STANDARD_ITEM_MAP_US_GAAP` desenine tek satır ekleme | 02/FORMÜL-02; BİST karşılığı GRUP 3'te (araştırma gerekli) |
| V-02 | Ar-Ge Gideri / Brüt Kâr | Kalite | NASDAQ | `gecici` | UCUZ | `us-gaap:ResearchAndDevelopmentExpense` — standart tag, AAPL/GOOGL/NVDA/META hepsi raporlar; teknoloji ağırlıklı NASDAQ evreninde ÖZELLİKLE değerli | 02/FORMÜL-03; BİST karşılığı GRUP 3'te |
| V-03 | Temettü / DPS / Payout | Değer, Büyüme | NASDAQ | `gecici` | UCUZ | `us-gaap:CommonStockDividendsPerShareDeclared` / `us-gaap:PaymentsOfDividends` — standart tag; **DEĞER (Kazanç Getirisi/güvenlik marjı) ile BÜYÜME (payout/tutma oranı) merceklerini AYNI ANDA açar** | 01/İLKE-39, FORMÜL-04; 02/Böl.45,50-52; 03/FORMÜL-80,81 — kitaplar arası EN SIK tekrarlanan tekil açık (7+ kez); BİST karşılığı GRUP 2'de |
| V-04 | Hazine Hissesi Düzeltmeli ROE / B-Ö | Kalite | NASDAQ | `gecici_oncelikli` | UCUZ-ORTA | `us-gaap:TreasuryStockValue` — NEREDEYSE EVRENSEL standart tag; spec'in KENDİ AAPL kenar-durum örneğini (düşük özkaynak tabanlı, yapay yüksek ROE) doğrudan çözer | 02/FORMÜL-17,21; dashboard'un KENDİ `tur` etiketi zaten "öncelikli" diyor — bkz. İlk Dalga #1 |
| V-05 | Devir Hızı (turnover) + Amihud İllikidite | (yeni — Güvenlik/likidite bonus adayı, henüz hiçbir mercek Girdiler tablosunda YOK) | BİST+NASDAQ | — | UCUZ (SIFIR yeni fetcher) | `technical.py`'nin GÜNLÜK hacim serisi + `calculator.py::market_cap` — İKİSİ de MEVCUT, sadece iki modül arasında köprü YOK | 03/Ch.14 (Likidite Değeri, halka açık hisseler için turnover-tabanlı proxy); `_ilerleme.md` satır 187: "kitap genelinde en düşük maliyetli somut bulgu" |
| V-06 | Net Alacaklar / Brüt Satışlar | (yeni — henüz hiçbir mercek Girdiler tablosunda YOK) | BİST+NASDAQ | — | UCUZ | `trade_receivables`/`revenue` — İKİSİ de `calculator.py`'de MEVCUT, oran hesaplanmıyor | 02/FORMÜL-11 — sektör-içi kıyas göstergesi, hangi merceğe (Kalite mi Güvenlik mi) ekleneceği spec-kararı gerektirir |
| V-07 | Vergi Öncesi Kâr (`income_before_tax`) — BİST XI_29 | (dolaylı: Değer'in Kazanç Getirisi vergi-öncesi varyantı, Kalite'nin efektif vergi oranı, Damodaran DCF vergi kalkanı) | BİST | — | UCUZ-ORTA | `STANDARD_ITEM_MAP_FINANSMAN`'da isimlendirme emsali ZATEN var (`pretax_profit`) — XI_29 (sanayi) şemasına TAŞINMASI gerekiyor, yeni kavram DEĞİL | 02/FORMÜL-06,09; 03'te 3+ ayrı bölümde (equity bond, efektif vergi oranı, WACC vergi kalkanı) tekrar ihtiyaç duyulan tekil alan (00_sentez §4 madde 6) |

### GRUP 2 — ORTA (yeni fetcher alanı, tag/yöntem BİLİNİYOR ama entegrasyon gerekiyor)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Veri kaynağı | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-08 | Faiz Gideri / Faaliyet Kârı (`interest_expense`) | Kalite, Güvenlik | NASDAQ | `gecici` | ORTA-DÜŞÜK | `us-gaap:InterestExpense` — standart tag (bazı şirketlerde net faiz gideri/geliri birleşik raporlanabilir, dikkat gerekir) | 01/FORMÜL-18; 02/FORMÜL-05 (kitabın EN ÇOK vurguladığı gösterge); 03/Tablo 2.4 — kitaplar arası EN SIK tekrarlanan açık (6+ kez); BİST karşılığı GRUP 3'te (en yüksek öncelikli GERÇEK bloker) |
| V-09 | Capex (Yatırım Harcaması) / Net Kâr | Büyüme | NASDAQ | `gecici` | ORTA-DÜŞÜK | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` — standart tag | 02/FORMÜL-25,28 (kitabın 2. en çok vurguladığı gösterge); 03'te reinvestment rate ailesinin TAMAMININ girdisi |
| V-10 | Capex (Yatırım Harcaması) / Net Kâr | Büyüme | BİST | `gecici` | ORTA | KAP XBRL `ifrs-full_PurchaseOfPropertyPlantAndEquipment` — somut etiket önerisi var, canlı doğrulama + fetcher entegrasyonu gerekiyor | Aynı kaynak, BİST tarafı henüz KODLANMADI (00_sentez §4 madde 4) |
| V-11 | Temettü / DPS / Payout | Değer, Büyüme | BİST | `yapisal` (dashboard'da) | ORTA | KAP XBRL `ifrs-full_DividendsPaid` / `ifrs-full_DividendPerShare` — Faz sonrası araştırma+fetcher gerekir | 00_sentez §4 madde 1; dashboard `tur=yapisal` diyor ama somut tag zaten önerilmiş — "yapısal" etiketi burada "henüz kodlanmadı" anlamında, "asla açılamaz" DEĞİL (bkz. §Metodoloji notu aşağı) |
| V-12 | Ödenen Temettü + Nakit Akışı Finansman Faaliyetleri (hisse ihracı/geri alımı net, borç ihracı/geri ödemesi net) | (yeni — Değer/Büyüme'nin DPS ile birlikte genişleyeceği alan) | BİST+NASDAQ | — | ORTA | KAP XBRL `ifrs-full_PaymentsForRepurchaseOfShares` ve ilgili finansman faaliyeti etiketleri; NASDAQ tarafı `us-gaap:PaymentsOfDividends`/`PaymentsForRepurchaseOfCommonStock` (standart) | 02/Böl.50-52 — "kesin cevap bu turda verildi: hiçbiri yok" (00_sentez §4 madde 7) |
| V-13 | NASDAQ Opsiyon/Warrant Seyreltme (kaba vekil) | Değer | NASDAQ | `kismi` | ORTA | `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` EKLENİP mevcut (`sec_edgar.py` satır 395) `WeightedAverageNumberOfDilutedSharesOutstanding` ile FARKI alınarak KABA bir seyreltme yüzdesi türetilir — dipnot okuma GEREKTİRMEZ | 03/İLKE-167-169; `docs/spec/veri_tamlik_notu.md` D3 — 00_sentez §4'e henüz GİRMEMİŞ bir madde, bu spec'le resmileştirilir |

### GRUP 3 — PAHALI (YÜKSEK maliyet — araştırma + yeni fetcher/mimari gerektirir)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Veri kaynağı | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-14 | SG&A / Brüt Kâr, Ar-Ge / Brüt Kâr | Kalite | BİST | `yapisal` | YÜKSEK | KAP XBRL karşılığı ARAŞTIRILMADI (üç fetcher dosyasında grep ile SIFIR sonuç doğrulandı) | 02/FORMÜL-02,03; 00_sentez'e YENİ madde önerisi (§4'te yok) |
| V-15 | Faiz Gideri / Faaliyet Kârı, Faiz Karşılama Oranı (`interest_expense` XI_29) | Kalite, Güvenlik | BİST | `yapisal` | YÜKSEK | `isyatirim.py` `STANDARD_ITEM_MAP_UFRS` (banka) VE `kap_financials.py` `STANDARD_ITEM_KAP_UFRS_INCOME` (banka) İKİSİNDE de VAR ama XI_29 (sanayi) haritasında YOK — **`kap_financials.py` (YENİ XBRL fetcher) içinde BİLE 6. kez doğrulanan, hâlâ çözülmemiş bir açık** — muhtemelen TFRS ara-dönem raporlama pratiğinin kendisinden kaynaklanıyor (araştırma gerekli) | 01/FORMÜL-18; 02/FORMÜL-05; 03/Tablo 2.4 — kitaplar arası kesinleşmiş EN SIK tekil açık |
| V-16 | Hazine Hissesi (`treasury_stock`) | Kalite | BİST | `yapisal` | YÜKSEK | Bilanço alt kalemi olarak nadiren AYRI raporlanır — araştırma gerekli | 02/FORMÜL-17,21 |
| V-17 | Greenblatt Kazanç Getirisi (EBIT/FD) + Carlisle Acquirer's Multiple | Değer | NASDAQ | `yapisal` | YÜKSEK | `fundamental_screens.py` SADECE BİST XI_29 sanayi için çağrılıyor (`pipeline.py`: `not is_us and financial_group=='XI_29'`) — US GAAP/SEC EDGAR karşılığı için AYRI bir keşif turu (EBIT tanımı, enterprise value bileşenleri NASDAQ formatında doğrulanmalı) | Greenblatt, Sihirli Formül (kitap-bilgi-bankası dışı) |
| V-18 | Greenblatt ROC (EBIT/Yatırılan Sermaye) | Kalite | NASDAQ | `yapisal` | YÜKSEK | Aynı BİST-only kısıt (V-17 ile AYNI kök neden) | Greenblatt, Sihirli Formül |
| V-19 | WACC / gerçek Beta / kaldıraçsız Beta / piyasa endeksi (BIST100, S&P500) getiri serisi | Değer (Damodaran modelinin β=1 basitleştirmesini gerçek beta ile değiştirir) | BİST+NASDAQ | — | YÜKSEK (yeni fetcher + istatistik altyapısı) | `price_history.py`'nin hisse tarafı ZATEN hazır, ENDEKS tarafı eksik; `merton.py::annualized_equity_volatility()` metodolojisi (log getiri std sapması × √252) ENDEKS serisine KOLAYCA uyarlanabilir (kod-seviyesi paralel zaten var) | 03/İLKE-42-51, FORMÜL-02,10-13 — 00_sentez §4 madde 5; FCFF/APV/EVA/CAPM ailesinin TAMAMINI bloke ediyor |
| V-20 | Kredi Notu / Temerrüt Olasılığı (harici derecelendirme) | Güvenlik | BİST+NASDAQ | `yapisal` | YÜKSEK (harici veri kaynağı) | Fitch/S&P/Moody's API entegrasyonu YOK — Merton EDF (`merton.py`, ARTIK `lens_guvenlik.py`'ye BAĞLI) sentetik bir vekil sunuyor ama BİREBİR yerine geçmez | 03/Tablo 2.4,6.2,17.1; 00_sentez §4 madde 12 |
| V-21 | 10+ Yıllık Kazanç/Hasılat/EPS Trend Serisi | Değer, Büyüme, (dolaylı: Kalite'nin brüt marj TUTARLILIK testi, Güvenlik'in Piotroski çok-yıllı kriterleri) | BİST+NASDAQ | `yapisal` | YÜKSEK (mimari — yeni fetcher DEĞİL, `trends.py`'nin veri tutma ufkunun genişletilmesi) | `trends.py::MAX_TREND_PERIODS=12` (~3 yıl) sabiti — kod ile doğrulandı | Kitaplar arası EN SIK tekrarlanan (15+ formülü bloke eden) TEK yapısal kısıt; 00_sentez §4 madde 2 — **EN YÜKSEK ETKİ/maliyet oranı** |
| V-22 | Sahiplik Yapısı / Yönetişim (oy hakkı sınıfı, içeriden sahiplik %, float, YK bağımsızlığı) | (yeni veri sınıfı — hiçbir mevcut merceğin Girdiler tablosunda YOK, en yakın: Güvenlik'in kontrol/opaklık riski) | BİST+NASDAQ | — | YÜKSEK | NASDAQ: SEC EDGAR DEF14A/10-K'dan KISMEN çekilebilir (henüz denenmedi); BİST: KAP pay sahipliği bildirimleri araştırılmalı | 03/Ch.13 (Kontrol Değeri), Ch.16 (Şeffaflık) — TÜM bir veri SINIFI eksik, tekil alan değil; 00_sentez §4 madde 10 |

### GRUP 4 — YAPISAL/İMKANSIZ veya NİTEL (muhtemelen HİÇBİR ZAMAN tam otomatik sayısal skora dönüşmeyecek)

> Bu grup için mimari kural 1 (LLM asla sayı üretmez) ve QuaxisLabs'ın
> "geriye-dönük/tanımlayıcı tarayıcı, ileriye-dönük projeksiyon motoru
> DEĞİL" ilkesi (bkz. `spec_mercek_buyume.md` Kapsam dışı) GEÇERLİDİR —
> bu kalemler ya SAYISAL bir skora HİÇ dönüşmemeli (checklist/metin
> formatı, bkz. §Faaliyet Raporu bölümü) ya da ürün kapsamının DIŞINDA
> kalmalıdır (M&A danışmanlığı, portföy yönetimi, tekil-proje değerleme).

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Kategori | Gerekçe |
|---|---|---|---|---|---|---|
| V-23 | Muhasebe Kalitesi / Kazanç Manipülasyonu (dipnot/metin okuma) | Güvenlik (Schilit birincil kaynağı henüz İŞLENMEDİ) | BİST+NASDAQ | — | NİTEL — ayrı mimari (bkz. §5) | 01/Ch.12+Comm.12, KONTROL L; 03/İLKE-03,04, BAYRAK-77 — 4+ bağımsız bölümde (Kısım 6/8a/8b/9) tekrarlanan tema; 00_sentez §4 madde 9 |
| V-24 | Çok-Firma Cross-Sectional/Sektör Regresyon Altyapısı (persentil, medyan, OLS) | Değer (sektör-göreli konum kalitesini artırır) | BİST+NASDAQ | — | YAPISAL/ÜRÜN ÖZELLİĞİ (çok yüksek) | 03/Kısım 4-5,9 — VERİ değil MİMARİ eksikliği, `sektor-siniflandirma` skill ile birleştirilebilecek uzun-vadeli backlog; 00_sentez §4 madde 11 |
| V-25 | Envanter, Şerefiye (Goodwill), Maddi Olmayan Duran Varlık, ayrı LT Yatırım kırılımı | Kalite (dolaylı — Ch.17 muhasebe manipülasyonu) | BİST+NASDAQ | — | DÜŞÜK ÖNCELİK, kısmen NİTEL | 02 — 4 alan standalone eksik; 01 — dolaylı; ilgili ilkeler çoğunlukla nitel/çok-yıllı karşılaştırma gerektiriyor; 00_sentez §4 madde 13 |
| V-26 | Çapraz İştirak/Azınlık Payı Piyasa Değeri Listesi (BİST holding yapıları — Koç, Sabancı, Doğuş tipi) | Değer (BAYRAK-28/29 azınlık kirliliği düzeltmesi) | BİST | — | YAPISAL (yüksek) | 03/Kısım 5 — konsolide holding yapılarının DOĞRU değerlenmesi için gerekli, veri sınıfı TAMAMEN eksik |
| V-27 | Ülke Kredi Notu / Opaklık Endeksi (makro) | (dolaylı — risksiz faiz/risk primi kalitesini artırır) | BİST+NASDAQ | — | YAPISAL (makro, çok yüksek) | 03 — ülke tahvili default spread'i + opaklık endeksi hiç YOK; `_RISK_FREE_RATE_PCT` zaten statik sabitle bu boşluğu KABACA dolduruyor |
| V-28 | Segment Bazlı Gelir Kırılımı | (Damodaran sektör-ağırlıklı beta hesabı için) | BİST+NASDAQ | — | YAPISAL (yüksek) | 03 — bottom-up beta için gerekli, QuaxisLabs'ta hiç YOK |
| V-29 | Çalışan Opsiyonu/Kısıtlı Hisse Tam Black-Scholes Değerlemesi (opsiyon sayısı, kullanım fiyatı, vade) | Değer (V-13'ün kaba vekilinin TAM/dipnot-düzeyi versiyonu) | NASDAQ (BİST'te pratik önemi düşük) | — | NİTEL/dipnot okuma gerektirir | 03/Ch.11 — Türkiye'de yaygın opsiyon programı NADİR, NASDAQ'ta TEORİK önem yüksek ama SEC 10-K/DEF14A dipnot metni gerekli |
| V-30 | Tobin's Q (yenileme maliyeti bazlı) | (dolaylı — Değer'in PD/DD alternatifi) | BİST+NASDAQ | — | YAPISAL/İMKANSIZ | 03 — yenileme maliyeti verisi hiçbir kaynakta YOK, `pb_ratio` defter değeri kullanıyor |
| V-31 | Patent-Seviyesi/Gerçek Opsiyon (2. proje senaryosu) Değerleme, İki-Firma M&A/Sinerji Değerleme, Kontrol Primi | (Damodaran Ch.11-15) | — | — | KAPSAM DIŞI | 03 — proje-seviyesi/iki-firma birleştirme akışı, QuaxisLabs'ın "tekil halka açık varlık" mimarisiyle YAPISAL OLARAK uyuşmuyor (M&A danışmanlığı değil) |

---

## Çift-sayma / tekrar kontrolü notu

Aşağıdaki ham veri kalemleri birden fazla kaynakta/mercekte/piyasada
göründüğü için TEK satıra birleştirildi (kaynak satır sayısı parantez
içinde):

- **DPS/Temettü/Payout** (V-03, V-11): DEĞER (`spec_mercek_deger.md` D2)
  VE BÜYÜME (`spec_mercek_buyume.md` B2) merceklerinin İKİSİNDE de
  Girdiler tablosunda geçiyor + kitaplar arası 7+ ayrı bağlamda (Graham
  Ch.5 kural 3/Shiller CAPE/Güvenlik Marjı/7-kriter listesi, Buffett
  Özkaynaklar/Nakit Akış, Damodaran DDM ailesinin TAMAMI) tekrarlanıyor —
  BİST/NASDAQ olarak İKİ satıra (V-03 ucuz/NASDAQ, V-11 orta/BİST)
  bölündü, aynı ham veri (`DividendsPaid`/`DividendPerShare` ailesi).
- **SG&A + Ar-Ge** (V-01/V-02 NASDAQ, V-14 BİST): KALİTE merceğinin
  İKİ AYRI bileşeni (farklı formüller, `02/FORMÜL-02` vs `FORMÜL-03`) ama
  AYNI kök sorun (gelir tablosu alt-kırılımı yok) — piyasa+bileşen
  kırılımıyla 3 satıra ayrıldı, tek bir "gelir tablosu alt-kırılımı"
  fetcher görevi olarak BİRLİKTE ele alınabilir (aynı KAP/SEC keşif turu).
- **`interest_expense`** (V-08 NASDAQ, V-15 BİST): KALİTE'nin "Faiz
  Gideri/Faaliyet Kârı" bileşeni VE GÜVENLİK'in "Faiz Karşılama Oranı"
  bileşeni AYNI ham veriyi kullanır (`spec_mercek_kalite.md` K5 = `spec_
  mercek_guvenlik.md` G1, kaynak notu AYNEN paylaşılıyor) — TEK satırda
  BİRLEŞTİRİLDİ, iki mercekte de "aynı kazanım" olarak işaretlenmeli.
- **Capex** (V-09 NASDAQ, V-10 BİST): SADECE BÜYÜME merceğinde ama İKİ
  piyasada AYRI tag/maliyet — piyasa kırılımıyla 2 satıra ayrıldı.
- **Greenblatt ailesi** (V-17 Kazanç Getirisi+Acquirer's Multiple, V-18
  ROC): AYNI kök kısıt (`fundamental_screens.py` BİST-only çağrı), İKİ
  AYRI mercekte (Değer/Kalite) İKİ AYRI bileşen olarak kaldı — çift sayma
  DEĞİL (farklı formüller), ama TEK bir NASDAQ-genişletme görevi olarak
  BİRLİKTE kodlanabilir.
- **10+ yıllık trend serisi** (V-21): DEĞER'in (Damodaran çok-yıllı
  büyüme), BÜYÜME'nin (temel/marjinal büyüme kalitesi) VE dolaylı olarak
  GÜVENLİK'in (Piotroski'nin bazı YoY kriterleri zaten 1 yıllık pencereyle
  ÇALIŞIYOR, ama Graham'ın 10-yıllık istikrarlı-kazanç testleri ÇALIŞMIYOR)
  ORTAK kök nedeni — TEK satırda tutuldu, `trends.py` mimari değişikliği
  TEK yerde yapılırsa 15+ formülü BİRDEN açar.
- **WACC/Beta** (V-19): Sadece DEĞER merceğinde doğrudan (Damodaran DCF)
  ama Damodaran kitabının kendi içinde 6+ farklı bölümde (Kısım 1/3/5/6/
  7/9) tekrar tekrar bloke edici bulunuyor — TEK satırda tutuldu.

---

## İlk Dalga önerisi (en ucuz + en yüksek etkili, kod-gelistirici'ye devredilebilir)

Aşağıdaki 9 görev, GRUP 1-2'den seçildi (ucuz/orta maliyet + birden fazla
mercek/piyasa/bileşeni AYNI ANDA açan veya dashboard'un KENDİ öncelik
etiketiyle işaretlenmiş kalemler). Her görev tek başına, küçük, test
edilebilir bir PR olacak büyüklüktedir.

1. **V-04 — NASDAQ Hazine Hissesi Düzeltmeli ROE.** `sec_edgar.py::
   STANDARD_ITEM_MAP_US_GAAP`'a `us-gaap:TreasuryStockValue` ekle →
   `lens_kalite.py`'ye hazine-hissesi-düzeltmeli ROE bileşeni ekle.
   **Neden ilk:** dashboard'un KENDİ `tur="gecici_oncelikli"` etiketiyle
   işaretlenmiş TEK kalem — spec'in kendi AAPL kenar-durum örneğini
   doğrudan çözer.
2. **V-01 — NASDAQ SG&A/Brüt Kâr.** `us-gaap:SellingGeneralAndAdministrativeExpense`
   ekle → `lens_kalite.py`'ye bileşen ekle (eşik tablosu spec'te zaten
   HAZIR: `<%30` fantastik, `%30-80` mümkün, `~%100+` kırmızı bayrak).
3. **V-02 — NASDAQ Ar-Ge/Brüt Kâr.** `us-gaap:ResearchAndDevelopmentExpense`
   ekle (eşik tablosu HAZIR: `%0` en iyi, `~%30` kırılgan) — 2 ve 3 AYNI
   fetcher keşif turunda birlikte yapılabilir (aynı gelir tablosu
   bölümü).
4. **V-03 — NASDAQ Temettü/DPS/Payout.** `us-gaap:CommonStockDividendsPerShareDeclared`
   ekle → DEĞER'in Kazanç Getirisi/Güvenlik Marjı bileşenini VE BÜYÜME'nin
   payout/tutma-oranı bileşenini AYNI ANDA açar (tek fetcher işiyle
   2 mercek).
5. **V-08 — NASDAQ Faiz Gideri/Faaliyet Kârı + Faiz Karşılama Oranı.**
   `us-gaap:InterestExpense` ekle → KALİTE (`spec_mercek_kalite.md` K5)
   VE GÜVENLİK (`spec_mercek_guvenlik.md` G1) merceklerini AYNI ANDA açar
   — dashboard'daki İKİ AYRI satırı (kalite+güvenlik NASDAQ) TEK fetcher
   görevi kapatır.
6. **V-09 — NASDAQ Capex/Net Kâr.** `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment`
   ekle → BÜYÜME merceğinin "yeniden yatırım kalitesi" bileşenini açar.
7. **V-07 — BİST `income_before_tax` (XI_29).** Mevcut `STANDARD_ITEM_MAP_FINANSMAN`
   isimlendirme emsalini XI_29 şemasına taşı — YENİ kavram değil, mevcut
   desenin genişletilmesi; 3 ayrı bağlamda (efektif vergi oranı, Değer'in
   vergi-öncesi kazanç getirisi, gelecekteki WACC vergi kalkanı) yeniden
   kullanılabilir.
8. **V-05 — Devir Hızı (turnover)/Amihud İlliklidite köprüsü.** SIFIR
   yeni fetcher — `technical.py`'nin mevcut hacim serisini `calculator.py`
   ile birleştir; hangi merceğe (Güvenlik/likidite bonusu önerilir)
   ekleneceği küçük bir spec-eki gerektirir ama veri TAMAMEN hazır.
9. **V-10 — BİST Capex/Net Kâr.** KAP XBRL `ifrs-full_PurchaseOfPropertyPlantAndEquipment`
   canlı doğrulama + `kap_financials.py`'ye ekleme — V-09 ile birlikte
   BÜYÜME merceğinin Capex bileşenini HER İKİ piyasada da açar (piyasa
   kapsamı simetrik hale gelir).

**Bilinçli olarak İlk Dalga'ya ALINMAYAN ama yakın-ucuz adaylar:** V-06
(Net Alacaklar/Brüt Satışlar — hangi mercekte yaşayacağı henüz
KARARLAŞTIRILMADI, önce küçük bir spec-eki gerekir), V-13 (NASDAQ opsiyon
seyreltme — ORTA maliyet, V-01/02/03/08/09 tamamlandıktan sonraki
dalgaya bırakılması önerilir), V-11/V-12 (BİST DPS/finansman
faaliyetleri — KAP XBRL araştırması NASDAQ turundan SONRA, aynı desenin
BİST'e uyarlanması daha verimli olur).

---

## Faaliyet Raporu / Dipnot Araştırması (yapısal olarak FARKLI yaklaşım)

### Neden ayrı bir bölüm

Kullanıcının "kâr nereden geliyor" (Ar-Ge mi, faiz mi, tek seferlik kalem
mi) sorusu — ve genel olarak V-23 (Muhasebe Kalitesi/Manipülasyon,
Schilit-tipi sinyaller) — **sayısal bir eşik/formülle ÇÖZÜLEMEZ.** Bu
kalemler ham metin (faaliyet raporu anlatı bölümü, dipnotlar, MD&A)
okuma + YARGI gerektirir. Proje mimarisinin GLOBAL DİREKTİFİ ("LLM asla
sayı üretmez") ve `temel-analiz-cercevesi` skill madde 6 (nitel sorular
Gemini yorum katmanına AYRI bir "kontrol listesi" olarak gider) burada
DOĞRUDAN uygulanır: **bu bölümün nihai çıktısı bir SKOR DEĞİL, bir
CHECKLİST + YORUM metnidir** — GÜVENLİK merceğinin sayısal skoruna
KARIŞTIRILMAZ, ayrı bir "Nitel Bulgular" kart bölümü olarak sunulur.

### Somut fizibilite değerlendirmesi (kod okumasıyla doğrulandı)

**BİST/KAP tarafı — KISMEN ALTYAPI ZATEN VAR:**
- `src/fetchers/kap.py::fetch_disclosures()` / `fetch_all_disclosures()`
  ZATEN şirket bildirimlerini (`title`=şirketin yazdığı serbest metin,
  `category`=KAP resmi taksonomi konusu) çekiyor — "Faaliyet Raporu"/
  "Yıllık Rapor" kategorisindeki bildirimler bu ARAÇLA filtrelenebilir.
- `kap.py::fetch_disclosure_attachment_pdf()` ZATEN bir bildirimin İLK
  ekli PDF'ini indiriyor (Faz 20'de halka arz izahnamesi keşfi için
  kullanılmış, AYNI mekanizma) — faaliyet raporu PDF'i muhtemelen AYNI
  yolla indirilebilir, YENİ bir ağ-erişim mekanizması GEREKMEZ.
- **Eksik olan:** (a) doğru bildirimi (kategori/başlık eşleşmesi ile
  "Faaliyet Raporu") bulma mantığı, (b) PDF'ten metin çıkarma — `kitap-
  okuyucu` prosedüründe (bkz. `.claude/skills/kitap-bilgi-cikarma/`)
  KULLANILAN PyMuPDF `get_text()`/OCR (`get_textpage_ocr()`) yöntemi
  AYNEN uyarlanabilir (aynı araç ailesi, farklı girdi), (c) çıkarılan
  metni + bir checklist'i LLM'e (Gemini yorum katmanı) besleyen bir
  orkestrasyon adımı.
- **Kaba maliyet:** ORTA — ağ erişimi/PDF indirme MEVCUT, metin çıkarma
  yöntemi KANITLANMIŞ (3 kitap zaten bu yöntemle işlendi), asıl iş
  kategori-eşleştirme + orkestrasyon + checklist tasarımıdır.

**NASDAQ/SEC tarafı — TAMAMEN YENİ FETCHER GEREKİYOR:**
- `src/fetchers/sec_edgar.py` şu an SADECE yapılandırılmış XBRL
  `companyfacts` uç noktasını (`data.sec.gov/api/xbrl/companyfacts/...`)
  VE `submissions` (SIC kodu) uç noktasını çekiyor — grep ile doğrulandı,
  10-K/10-Q GÖVDE METNİ (MD&A — Item 7, "Management's Discussion and
  Analysis") çeken HİÇBİR fonksiyon YOK.
- SEC EDGAR'ın kendisi ücretsiz, kamuya açık bir "Full Text Search" API'si
  (`efts.sec.gov`) VE ham dosyalama arşivi (`sec.gov/Archives/edgar/data/
  {cik}/{accession}/...`) sağlıyor — teknik olarak ERİŞİLEBİLİR ama
  QuaxisLabs'ta bu turda YENİ bir fetcher modülü (`sec_edgar_filings.py`
  gibi) yazılması GEREKİR, mevcut `companyfacts` deseninin YENİDEN
  KULLANILAMAYACAĞI bir alan (farklı uç nokta, farklı ayrıştırma —
  HTML/metin, JSON DEĞİL).
- **Kaba maliyet:** ORTA-YÜKSEK — erişim engeli YOK (ücretsiz/genel), ama
  hiçbir mevcut kod deseni yeniden kullanılamıyor, sıfırdan fetcher +
  HTML-temizleme + bölüm-tespiti (Item 7'yi dosyanın geri kalanından
  ayırma) gerekiyor.

### Önerilen somut ilk adım

1. **BİST önce (daha düşük maliyet):** `kap.py`'ye `fetch_disclosures()`
   sonuçlarını `category`/`title` alanlarında "faaliyet raporu"/"yıllık
   rapor" anahtar kelimeleriyle filtreleyen KÜÇÜK bir yardımcı fonksiyon
   + `fetch_disclosure_attachment_pdf()`'i BAĞLAYAN bir keşif scripti
   (tek bir örnek şirkette, ör. THYAO, elle doğrulama) — bu, YENİ bir
   mimari bileşen DEĞİL, MEVCUT iki fonksiyonun (`fetch_disclosures` +
   `fetch_disclosure_attachment_pdf`) BİRLEŞTİRİLMESİDİR.
2. **Checklist tasarımı (kod DEĞİL, spec/prompt işi — bu ajanın ileride
   yapacağı bir sonraki görev):** "kâr nereden geliyor" sorusunu somut
   alt-sorulara ayıran bir kontrol listesi — ör. "faaliyet kârı artışı
   temel iş hacmi artışından mı, tek seferlik bir kalemden mi (varlık
   satışı, dava tazminatı, kur farkı geliri) kaynaklanıyor?", "Ar-Ge
   giderindeki değişim ürün yatırımını mı yoksa muhasebe sınıflandırma
   değişikliğini mi yansıtıyor?", Graham Ch.12 KONTROL L maddeleri (pro
   forma kazanç, agresif gelir kaydı, sermaye-harcaması-yeniden-
   sınıflandırma) BİREBİR bu checklist'in başlangıç iskeletidir.
3. **NASDAQ ikinci dalgaya bırakılır** — SEC tam-metin fetcher'ı BİST
   deneyiminden (hangi checklist soruları ANLAMLI çıktı verdi) SONRA
   tasarlanırsa, gereksiz yeniden-iş riski azalır.
4. **Schilit (06) kitabı işlendiğinde** bu bölüm KÖKTEN GENİŞLER — V-23
   şu an SADECE Graham/Damodaran'ın NİTEL uyarılarına dayanıyor,
   Schilit'in SİSTEMATİK tahakkuk/nakit ayrışması, alacak-envanter/
   hasılat büyüme ayrışması gibi YARI-SAYISAL teknikleri eklendiğinde
   bu checklist'in bir KISMI (TAMAMI değil) sayısal bir "kırmızı bayrak
   sayacına" (GÜVENLİK merceğine, ayrı bir bileşen olarak) YÜKSELTİLEBİLİR
   — ama METİN OKUMA gerektiren kısım (yönetim anlatısı, MD&A yorumu)
   HER ZAMAN nitel kalacaktır.

---

## Kısa özet — envanter büyüklüğü

- **31 tekil (deduplike) kalem** (V-01…V-31) — 3 kitabın ham "VERİ EKSİK/
  KISMEN MEVCUT" satırlarının (159+22=181, üç kitap TAM METNİ okunarak
  00_sentez'de ZATEN deduplike edilmişti), dashboard'un canlı 17 piyasa-
  satırlık uyarı listesinin, `veri_tamlik_notu.md`'nin 16 çapraz-doğrulama
  bulgusunun VE 4 mercek spec'inin Girdiler tablolarının TEK bir haritada
  birleştirilmiş hali.
- **7 UCUZ, 6 ORTA, 9 PAHALI, 9 YAPISAL/NİTEL/kapsam-dışı.**
- **İlk Dalga: 9 somut görev** (madde 1-9 yukarıda) — TAMAMI mevcut
  fetcher desenlerinin (`STANDARD_ITEM_MAP_US_GAAP` aday-tag listesi)
  GENİŞLETİLMESİ, hiçbiri yeni mimari GEREKTİRMİYOR.
- **Faaliyet raporu/dipnot okuma tamamen ayrı bir iz** — sayısal skora
  ASLA tam dönüşmeyecek (mimari kural 1), BİST tarafı KISMEN mevcut
  altyapıyla (ORTA maliyet) başlatılabilir, NASDAQ tarafı YENİ fetcher
  gerektirir (ORTA-YÜKSEK maliyet) ve BİST deneyiminden SONRAYA
  bırakılması önerilir.

---

## Spec-eki: GRUP 2 (ORTA) İkinci Dalga — V-10/V-11/V-12/V-13 uygulama notu

**Kod-geliştirici devir notu (2026-08-12, kod-gelistirici ajanı tarafından
eklendi):** V-08/V-09 (NASDAQ, İlk Dalga'da BİTTİ) İNCELENDİĞİNDE ortaya
çıkan gerçek: bu iki kalem `calculator.Ratios`'a SADECE bilgi amaçlı (ham
oran) eklendi, HİÇBİR mercek bileşenine (lens_kalite.py/lens_buyume.py)
BAĞLANMADI — sebep KENDİ kod yorumunda AÇIKÇA yazılı: ilgili mercek
spec'lerinin (`spec_mercek_buyume.md` §Eşikler ve ağırlıklar) ağırlık
tablosu ZATEN %100 dağıtılmış, yeni bir bileşen için ağırlık İCAT ETMEK
persona kuralını (Global Direktif: "spec'te olmayan eşik/ağırlık uydurma")
İHLAL ederdi. **Bu ikinci dalga (V-10/V-11/V-12/V-13) AYNI deseni izler**
— tüm yeni alanlar `calculator.Ratios`'a bilgi amaçlı eklendi, HİÇBİR yeni
skorlanan (ağırlık taşıyan) mercek bileşeni OLUŞTURULMADI.

**V-10 (BİST Capex) — kaynak KARARI değişti:** Spec'in önerdiği KAP XBRL
etiketi (`ifrs-full_PurchaseOfPropertyPlantAndEquipment...`) CANLI
doğrulandı (TATGD/BORSK/TUPRS KAP sayfaları) AMA `kap_financials.py`
SADECE en güncel TEK çeyreği "tazelik yaması" olarak çeker (bkz. o modülün
kendi docstring'i) — TTM (`_trailing_12m_from_cumulative`, en az 3 kümülatif
veri noktası gerektirir) bu yolla ÇALIŞMAZDI. Bunun yerine `isyatirim.py`
(birincil TOPLU 8-çeyrek kaynağı) içinde CANLI keşfedilen bir itemCode
kullanıldı: `"4CAI"` = "Sabit Sermaye Yatırımları" / "Capital Expenditures
(CapEx)" (bkz. `data/exploration/thyao_items_readable.txt` satır 132) —
V-07'nin (`pretax_profit`) AYNI "isyatirim.py'ye ekle" deseni. Alan adı
BİLEREK NASDAQ ile AYNI ("capex") tutuldu ki `calculator.py`'nin PİYASA-
BAĞIMSIZ `ttm_capex`/`capex_to_net_income_pct` rasyosu HİÇBİR ek kod
GEREKMEDEN BİST için de çalışsın.

**V-11 (BİST DPS/Payout) — kapsam küçültüldü:** 3 canlı KAP sayfası (TATGD/
BORSK/TUPRS) taranarak doğrulandı ki BİST'te HİÇBİR XI_29 şirketinde
hisse-başına (per-share) bir DPS XBRL etiketi YOK (`veri_tamlik_notu.md`
bulgusuyla TUTARLI) — bu GERÇEK bir yapısal kısıt olarak KALIR. Bunun
yerine `isyatirim.py` "4CBB" ("Temettü Ödemeleri") — TOPLAM nakit temettü
ödemesi — kullanıldı; Graham'ın "%60-75 payout" ilkesi (01/İLKE-178) için
`payout_ratio_pct = dividends_paid_ttm/net_income_ttm` hisse-başına kırılım
GEREKTİRMEZ. Alan adı ("dividends_paid") NASDAQ ile ORTAK tutuldu (V-12 ile
BİRLEŞTİ, bkz. aşağı) — DPS-per-share'in kendisi (BİST) hâlâ AÇIK, gelecek
bir turda ayrıca ele alınmalı.

**V-12 — küçük karar (görev talimatı gereği belgelenir):** "Ödenen Temettü +
Finansman Faaliyetleri" kaleminin hangi mercek bileşenine bağlanacağı
sorusu için — bu turda bilgi amaçlı (skorsuz) bırakıldığı için bir ağırlık
kararı GEREKMEDİ, ama kalemin KANONİK gelecekteki evi olarak **Güvenlik
merceği** (V-04'ün hazine hissesi düzeltmeli ROE mantığıyla AYNI ruh —
sermaye tahsisi disiplini sinyali, Buffett Böl.50-52/İLKE-50) seçildi;
**Değer** merceği (buyback verimi) ikincil aday olarak not düşülür.
Gerekçe: hazine hissesi (V-04) ZATEN mevcut bir bileşenin (ROE) GİRDİSİNİ
düzeltiyor, ağırlık İCAT ETMİYOR — net temettü/buyback/borç verisi de
benzer şekilde GELECEKTE mevcut bir Güvenlik bileşeninin (ör. Kaldıraç
trendi) girdisini zenginleştirebilir, YENİ bir ağırlık gerektirmeden. Kapsam
notu: BİST'te hisse geri alımı (buyback) için standart bir itemCode/XBRL
etiketi 3 canlı şirkette de BULUNAMADI (sadece "Finansal Borçlardaki
Değişim" — "4CBA" — net bir rakam olarak mevcut) — bu GERÇEK bir bloker
olarak kalır, NASDAQ tarafında ise `us-gaap:PaymentsForRepurchaseOfCommonStock`
CANLI (AAPL) doğrulandı ve eklendi.

**V-13 — dipnot okuma GEREKMEDİ, task talimatıyla TUTARLI:** `us-gaap:
WeightedAverageNumberOfSharesOutstandingBasic` eklendi, mevcut
`WeightedAverageNumberOfDilutedSharesOutstanding` ile FARKI
`calculator.Ratios.diluted_dilution_pct` olarak AYRI bir alan adı altında
(mevcut `shares_outstanding` zincirini BOZMADAN) hesaplanıyor.
