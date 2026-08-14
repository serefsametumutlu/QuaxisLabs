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

**>>> BU ÖN-NOT ARTIK KISMEN ESKİMİŞ — bkz. aşağıdaki "EK: 2026-08-14
durum güncellemesi" bölümü. `PIYASA_SISTEMIK_EKSIK_BILESENLER` (satır
96-138) BİST/SG&A-Ar-Ge/Faiz Gideri satırları için ARTIK YANLIŞ (XI_29
sanayi için veri MEVCUT ve skora BAĞLI, sadece dashboard metni
güncellenmedi) — kod-gelistirici'ye devredilecek somut, ucuz bir metin
düzeltmesi görevi aşağıda V-32 olarak tanımlanır. <<<**

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

## Envanter tablosu (maliyet artan sırade, deduplike)

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
| V-01 | SG&A / Brüt Kâr | Kalite | NASDAQ | ~~`gecici`~~ **BİTTİ (İlk Dalga)** | UCUZ | `us-gaap:SellingGeneralAndAdministrativeExpense` | 02/FORMÜL-02; BİST XI_29 tarafı da 2026-08-14'te BİTTİ (bkz. EK bölümü) |
| V-02 | Ar-Ge Gideri / Brüt Kâr | Kalite | NASDAQ | ~~`gecici`~~ **BİTTİ (İlk Dalga)** | UCUZ | `us-gaap:ResearchAndDevelopmentExpense` | 02/FORMÜL-03; BİST XI_29 tarafı da 2026-08-14'te BİTTİ |
| V-03 | Temettü / DPS / Payout | Değer, Büyüme | NASDAQ | ~~`gecici`~~ **BİTTİ (İlk Dalga)** | UCUZ | `us-gaap:CommonStockDividendsPerShareDeclared` / `us-gaap:PaymentsOfDividends` | 01/İLKE-39, FORMÜL-04; 02/Böl.45,50-52; 03/FORMÜL-80,81 — `payout_ratio_pct` `calculator.py`'de doğrulandı, `lens_buyume.py`/`lens_kalite.py`'de kullanılıyor |
| V-04 | Hazine Hissesi Düzeltmeli ROE / B-Ö | Kalite | NASDAQ | ~~`gecici_oncelikli`~~ **BİTTİ (İlk Dalga)** | UCUZ-ORTA | `us-gaap:TreasuryStockValue` | 02/FORMÜL-17,21 — `lens_kalite.py::_skor_roe()` içinde `treasury_stock` parametresiyle canlı doğrulandı (satır 108-117) |
| V-05 | Devir Hızı (turnover) + Amihud İllikidite | (yeni — Güvenlik/likidite bonus adayı) | BİST+NASDAQ | — | UCUZ (SIFIR yeni fetcher) | `technical.py`'nin GÜNLÜK hacim serisi + `calculator.py::market_cap` | 03/Ch.14; `_ilerleme.md` satır 187 — **HÂLÂ AÇIK, kodlanmadı, İlk Dalga'nın DIŞINDA kaldı** |
| V-06 | Net Alacaklar / Brüt Satışlar | (yeni) | BİST+NASDAQ | — | UCUZ | `trade_receivables`/`revenue` — İKİSİ de MEVCUT, oran hesaplanmıyor | 02/FORMÜL-11 — **HÂLÂ AÇIK** |
| V-07 | Vergi Öncesi Kâr (`pretax_profit`) — BİST XI_29 | (dolaylı) | BİST | — | ~~UCUZ-ORTA~~ **BİTTİ** | `isyatirim.py` `STANDARD_ITEM_MAP_XI_29["pretax_profit"]="3I"` CANLI doğrulandı (THYAO/BIMAS) | 02/FORMÜL-06,09 |

### GRUP 2 — ORTA (yeni fetcher alanı, tag/yöntem BİLİNİYOR ama entegrasyon gerekiyor)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Veri kaynağı | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-08 | Faiz Gideri / Faaliyet Kârı (`interest_expense`) | Kalite, Güvenlik | NASDAQ | ~~`gecici`~~ **BİTTİ** | ORTA-DÜŞÜK | `us-gaap:InterestExpense` | 01/FORMÜL-18; 02/FORMÜL-05; 03/Tablo 2.4 — `lens_kalite.py` (satır 282) VE `lens_guvenlik.py::_skor_faiz_karsilama` (satır 213) İKİSİNDE de skora bağlı. BİST XI_29 tarafı da 2026-08-14'te BİTTİ (bkz. EK) — **UYARI: `lens_guvenlik.py` satır 24-27'nin kendi docstring'i hâlâ "BİST'te HER ZAMAN None döner" diyor, bu METİN ARTIK YANLIŞ (bkz. V-32)** |
| V-09 | Capex (Yatırım Harcaması) / Net Kâr | Büyüme | NASDAQ | ~~`gecici`~~ **BİTTİ** | ORTA-DÜŞÜK | `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` | 02/FORMÜL-25,28 — `capex_to_net_income_pct` `lens_buyume.py`'de skora bağlı |
| V-10 | Capex (Yatırım Harcaması) / Net Kâr | Büyüme | BİST | ~~`gecici`~~ **BİTTİ** (kaynak DEĞİŞTİ, bkz. Spec-eki altta) | ORTA | `isyatirim.py` itemCode `"4CAI"` ("Sabit Sermaye Yatırımları") | Aynı `capex_to_net_income_pct` alanı, piyasa-bağımsız çalışıyor |
| V-11 | Temettü / DPS / Payout (TOPLAM, hisse-başı DEĞİL) | Değer, Büyüme | BİST | ~~`yapisal`~~ **KISMEN BİTTİ** (kapsam küçültüldü, bkz. Spec-eki) | ORTA | `isyatirim.py` itemCode `"4CBB"` ("Temettü Ödemeleri") — `payout_ratio_pct` bunu kullanır. **Hisse-başı DPS (Kazanç Getirisi/temettü verimi formülünün payı) HÂLÂ AÇIK** — KAP'ta 3 canlı şirkette (TATGD/BORSK/TUPRS) per-share XBRL etiketi BULUNAMADI, GERÇEK yapısal kısıt olarak KALIYOR | 00_sentez §4 madde 1 |
| V-12 | Ödenen Temettü + Nakit Akışı Finansman Faaliyetleri (buyback net, borç net) | (Güvenlik'e aday, bkz. Spec-eki) | BİST+NASDAQ | — | ORTA | KAP: `isyatirim.py` `"4CBA"` (Finansal Borçlardaki Değişim, net) MEVCUT ama BİST'te buyback nakit akış kalemi 3 şirkette de BULUNAMADI (GERÇEK bloker); NASDAQ: `us-gaap:PaymentsForRepurchaseOfCommonStock` CANLI (AAPL) eklendi | 02/Böl.50-52 — **hâlâ HİÇBİR skorlanan mercek bileşenine BAĞLANMADI (sadece bilgi amaçlı `Ratios` alanı)** |
| V-13 | NASDAQ Opsiyon/Warrant Seyreltme (kaba vekil) | Değer | NASDAQ | ~~`kismi`~~ **VERİ BİTTİ, SKORA BAĞLANMADI** | ORTA | `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` eklendi, `diluted_dilution_pct` hesaplanıyor | 03/İLKE-167-169 — **`calculator.Ratios.diluted_dilution_pct` HİÇBİR `lens_deger.py` bileşenine bağlı DEĞİL (grep ile doğrulandı: sadece calculator.py'de tanım/atama var), ağırlık tablosu dolu olduğu için bilinçli olarak informational bırakıldı** |

### GRUP 3 — PAHALI (YÜKSEK maliyet — araştırma + yeni fetcher/mimari gerektirir)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Veri kaynağı | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-14 | SG&A / Brüt Kâr, Ar-Ge / Brüt Kâr | Kalite | BİST | ~~`yapisal`~~ **BİTTİ (XI_29 sanayi), KALICI BOŞLUK (banka/sigorta/finansman)** | ~~YÜKSEK~~ → BİTTİ | `isyatirim.py` XI_29 haritası: `sga_expense`("3DA"+"3DB"), `research_development_expense`("3DC") — 2026-08-14 CANLI eklendi (THYAO doğrulandı) | 02/FORMÜL-02,03 — UFRS(banka)/UFRS_K(sigorta)/FINANSMAN şemalarında "brüt kâr"/"SG&A" KAVRAMSAL OLARAK YOK (banka gelir tablosu yapısı temelden farklı) — bu **kapsam-dışı KALICI boşluk**, "araştırılmadı" değil "uygulanamaz" |
| V-15 | Faiz Gideri / Faaliyet Kârı, Faiz Karşılama Oranı (`interest_expense` XI_29) | Kalite, Güvenlik | BİST | ~~`yapisal`~~ **BİTTİ (XI_29 sanayi)**, banka zaten VARDI (UFRS "3B"), **sigorta ARAŞTIRILDI/KALICI BOŞLUK, finansman ARAŞTIRILDI/veri var-skorlanmadı (bkz. EK bölümü, 2026-08-14 ikinci tur)** | ~~YÜKSEK~~ → BİTTİ (sanayi) | `isyatirim.py` XI_29: `interest_expense`="4BB" ("Finansman Giderleri") — 2026-08-14 CANLI eklendi, `3HC` (Esas Faaliyet Dışı Finansal Giderler) ile çapraz doğrulandı | 01/FORMÜL-18; 02/FORMÜL-05; 03/Tablo 2.4 — **UFRS_K (sigorta): ANSGR'nin TAM gelir tablosu (409 kalem) tarandı, borçlanma/finansman maliyeti niteliğinde AYRI bir kalem YOK (en yakın "3MA — Yatırım Yönetim Giderleri, Faiz Dahil" yatırım portföyü yönetim gideridir, borç faizi DEĞİL) — KAVRAMSAL OLARAK YOK, kalıcı boşluk. FINANSMAN (XI_29K): "A3AE — Finansman Giderleri" (KTLEV ile CANLI doğrulandı, gerçek negatif değer) GENUINE bir analog, ama skora bağlamak `hesapla_guvenlik_mercegi_finans`'ın (banka/sigorta/finansman ORTAK, tek-bileşenli %100 Özkaynak/Aktif) yeni bir ağırlık payı İCAT ETMESİNİ gerektirirdi — YAPILMADI, bilgi amaçlı bırakıldı (V-12/V-13 ile AYNI karar deseni)** |
| V-16 | Hazine Hissesi (`treasury_stock`) | Kalite | BİST | `yapisal` | YÜKSEK | Bilanço alt kalemi olarak nadiren AYRI raporlanır — **2026-08-14 turunda ARAŞTIRILDI, BULUNAMADI, KALICI BOŞLUK olarak kapatıldı** (bkz. EK bölümündeki V-16 araştırma notu) | 02/FORMÜL-17,21 |
| V-17 | Greenblatt Kazanç Getirisi (EBIT/FD) + Carlisle Acquirer's Multiple | Değer | NASDAQ | `yapisal` | YÜKSEK | `fundamental_screens.py` HÂLÂ SADECE `not is_us and financial_group=='XI_29'` koşuluyla çağrılıyor (`pipeline.py` satır 1809, 2026-08-14'te DEĞİŞMEDİ, canlı doğrulandı) | Greenblatt, Sihirli Formül — **HÂLÂ AÇIK, en yüksek etkili tekil NASDAQ boşluğu (Değer merceğinin %10 ağırlıklı bileşeni NASDAQ'ta hiç hesaplanmıyor)** |
| V-18 | Greenblatt ROC (EBIT/Yatırılan Sermaye) | Kalite | NASDAQ | `yapisal` | YÜKSEK | Aynı BİST-only kısıt (V-17 ile AYNI kök neden) — **HÂLÂ AÇIK** | Greenblatt, Sihirli Formül |
| V-19 | WACC / gerçek Beta / kaldıraçsız Beta / piyasa endeksi getiri serisi | Değer | BİST+NASDAQ | — | YÜKSEK | `price_history.py` hisse tarafı hazır, endeks tarafı eksik — **HÂLÂ AÇIK** | 03/İLKE-42-51 |
| V-20 | Kredi Notu / Temerrüt Olasılığı (harici) | Güvenlik | BİST+NASDAQ | `yapisal` | YÜKSEK | Fitch/S&P/Moody's API YOK — **HÂLÂ AÇIK**, Merton EDF sentetik vekil olarak devam ediyor | 03/Tablo 2.4,6.2,17.1 |
| V-21 | 10+ Yıllık Kazanç/Hasılat/EPS Trend Serisi | Değer, Büyüme | BİST+NASDAQ | `yapisal` | YÜKSEK (mimari) | `trends.py::MAX_TREND_PERIODS=12` (~3 yıl) — **HÂLÂ AÇIK, DEĞİŞMEDİ** | Kitaplar arası EN SIK tekrarlanan (15+ formülü bloke eden) TEK yapısal kısıt |
| V-22 | Sahiplik Yapısı / Yönetişim | (yeni veri sınıfı) | BİST+NASDAQ | — | YÜKSEK | **HÂLÂ AÇIK** | 03/Ch.13,16 |

### GRUP 4 — YAPISAL/İMKANSIZ veya NİTEL (2026-08-14'te DEĞİŞMEDİ, aynen geçerli)

V-23 ... V-31 — bkz. orijinal envanter altta (Faaliyet Raporu/dipnot
okuma, sum-of-parts NAV, Tobin's Q, vb.) — bu turda hiçbiri araştırılmadı,
statüleri AYNEN korunur.

---

## EK: 2026-08-14 durum güncellemesi (77abde8 + 4a8b7ed sonrası)

### Bugün YAPILAN 2 düzeltmenin envanter üzerindeki etkisi

**Commit `77abde8`** — `isyatirim.py::STANDARD_ITEM_MAP_XI_29`'a üç yeni
ham alan eklendi: `sga_expense` ("3DA"+"3DB" toplamı), `research_
development_expense` ("3DC"), `interest_expense` ("4BB"). Bu, V-01/V-02/
V-08'in BİST XI_29 (sanayi) yarısını (daha önce V-14/V-15 olarak GRUP
3/PAHALI'ya işaretlenmişti) **KAPATTI**. Kod doğrulaması (bu turda
yapıldı): `calculator.py` satır 795-797'de bu üç ham alandan
`sga_to_gross_profit_pct`/`rd_to_gross_profit_pct`/`interest_expense_
to_operating_profit_pct` PİYASA-BAĞIMSIZ formülleri ZATEN hesaplanıyordu
(daha önceden NASDAQ girdisiyle çalışıyordu) — bu formüller `lens_
kalite.py` satır 280-282'de VE `lens_guvenlik.py::_skor_faiz_karsilama`
satır 213'te DOĞRUDAN skora bağlı olduğu için, **BİST XI_29 sanayi
şirketleri için 2026-08-14'ten itibaren bu 3 bileşen GERÇEK bir skor
üretiyor** (önceden None/N/A idi).

**Kapsam sınırı (önemli, yanlış anlaşılmamalı):** Bu düzeltme SADECE
XI_29 (sanayi/ticaret) şemasını kapsıyor. `STANDARD_ITEM_MAP_UFRS`
(banka), `STANDARD_ITEM_MAP_UFRS_K` (sigorta), `STANDARD_ITEM_MAP_
FINANSMAN` (finansman şirketleri), `STANDARD_ITEM_MAP_UFRS_KATILIM`
(katılım bankası) şemalarında `sga_expense`/`research_development_
expense` alanları YOK ve muhtemelen **HİÇ OLMAYACAK** — banka/sigorta
gelir tablosu yapısı "brüt kâr" kavramını içermiyor (Greenblatt/Schilit
tarzı metriklerin banka/sigortaya uygulanamayacağı ilkesiyle TUTARLI, bu
persona kuralı burada da geçerli). `interest_expense` banka şemasında
zaten VARDI ("3B", faiz gelir/gider bankanın ANA iş kolu olduğu için
kavramsal olarak farklı bir anlam taşır — "Faiz Karşılama Oranı" kavramı
bankaya doğrudan uygulanamaz, KALICI kapsam-dışı sayılmalı). Sigorta
(UFRS_K) ve finansman (FINANSMAN) şemalarında `interest_expense` HÂLÂ
eşlenmedi — bu GERÇEK bir açık (araştırma önerilir, düşük öncelik, çünkü
BİST evreninde sigorta/finansman şirket sayısı azınlıkta).

**Commit `4a8b7ed`** — `SectorMetricCache`'e tazelik/geçersizleştirme
kuralı eklendi. Bu, bir VERİ EKSİKLİĞİ değil bir VERİ BOZULMASI
(staleness) bug'ıydı — "Sektöre Göreli Konum" bileşeninin girdisi (ham
metrik verisi) her zaman mevcuttu, ama önbellek eskimiş/yanlış "yetersiz
örneklem" sonucunu KALICI olarak döndürüyordu. Bu düzeltme envanterdeki
hiçbir V-xx maddesini DOĞRUDAN kapatmıyor (yeni bir ham veri kalemi
eklenmedi) ama **N/A görünüm sayısını dolaylı olarak azaltır** — bazı
ince-sektör/dönem kombinasyonlarında gerçekte yeterli peer VARKEN
yanlışlıkla N/A gösterilen "Sektöre Göreli Konum" kartları artık doğru
sonucu gösterecek. Kullanıcının "boş alan görmek istemiyorum" talebiyle
DOĞRUDAN ilgili ama envanterin dışında, ayrı bir bug-sınıfı.

### V-32 (YENİ) — Dashboard'un statik uyarı metni ARTIK YANLIŞ (UCUZ, metin-only düzeltme)

| # | Kalem | Mercek(ler) | Piyasa | `tur` | Maliyet | Kaynak | Gerekçe |
|---|---|---|---|---|---|---|---|
| V-32 | `PIYASA_SISTEMIK_EKSIK_BILESENLER["BIST"]` satır 98-99 ("SG&A / Ar-Ge oranı", `tur="yapisal"`, "KAP XBRL'de standart etiketlenmemiş") VE satır 102-103 ("Faiz Karşılama Oranı", `tur="yapisal"`, "KAP alt-kalem araştırması henüz yapılmadı") | Kalite, Güvenlik | BİST | `yapisal` (YANLIŞ, güncellenmeli) | ÇOK UCUZ (metin düzenleme, YENİ veri/fetcher/formül GEREKMİYOR) | `src/render/dashboard.py` satır 96-138 | Kod okumasıyla DOĞRULANDI: bu iki satır artık YANLIŞ bilgi veriyor — XI_29 sanayi şirketleri için veri MEVCUT ve skora BAĞLI (bkz. yukarıdaki "Bugün YAPILAN" bölümü). Kullanıcı ORGE gibi bir XI_29 sanayi hissesinde bu bileşenlerin ARTIK dolu olduğunu görecek ama dashboard'un metodoloji/uyarı paneli hâlâ "sistemik eksik" diyecek — bu GÜVEN kaybına yol açar (spec'in "Her eşik ve ağırlık için gerekçe zorunlu" ilkesiyle aynı ruhta, kullanıcıya YANLIŞ gerekçe sunulmamalı). **Önerilen düzeltme metni:** `tur` değeri `"kismi"` yapılsın, `aciklama` şu şekilde güncellensin: "BİST XI_29 (sanayi/ticaret) şirketlerinde 2026-08-14'ten itibaren MEVCUT ve skora dahil; banka/sigorta/finansman şirketlerinde bu kavram (brüt kâr/SG&A ayrımı) yapısal olarak uygulanamaz." Aynı düzeltme "Faiz Karşılama Oranı" satırı için de: "XI_29 sanayi'de mevcut (2026-08-14); banka için kavram farklı anlam taşır (uygulanamaz), sigorta/finansman şemalarında henüz eşlenmedi." **Bu, İlk Dalga'nın EN UCUZ ve EN YÜKSEK ACİLİYETLİ maddesidir — kullanıcı yanlış bilgilendirilmemeli.** |

### V-33 (YENİ) — `lens_guvenlik.py`/`lens_kalite.py` docstring'leri de eskidi (aynı kök neden, aynı ucuz düzeltme)

`lens_guvenlik.py` satır 24-27 ("Faiz Karşılama Oranı BİST'te HER ZAMAN
`None` döner... BİST XI_29 haritasında hiç çekilmiyor") VE `lens_
kalite.py` satır 38 civarındaki eşdeğer not — ikisi de aynı 2026-08-14
öncesi durumu anlatıyor, artık YANLIŞ. Kod DAVRANIŞI zaten doğru
çalışıyor (formüller `Ratios`'tan okuyor, veri geldiğinde otomatik
skorlanıyor) — sadece modül docstring'leri (yorum, çalışan koda etki
etmez) güncel değil. **Maliyet: ÇOK UCUZ, sıfır risk (yorum satırı).**
Öncelik V-32'den DÜŞÜK (kullanıcıya görünmüyor, sadece geliştirici
belgesi) ama aynı PR'da yapılması VERİMLİ olur.

### V-16 (2026-08-14 ikinci tur) — Hazine Hissesi araştırması: BULUNAMADI, KALICI BOŞLUK

`isyatirim.py`'nin XI_29 (sanayi/ticaret) standardize kalem sözlüğü
`data/exploration/thyao_items_readable.txt` içinde EKSİKSİZ (147 satır,
başlıktan sonuna) taranarak doğrulandı: "hazine hissesi" / "geri alınan
paylar" / "treasury" anlamına gelen AYRI bir bilanço alt kalemi YOK.
En yakın aday `2OC` ("Karşılıklı İştirak Sermayesi Düzeltmesi (-)" /
"Adjustments to Share Capital") — ama bu KAVRAMSAL OLARAK FARKLI bir
kalem: TMS/TFRS'te "karşılıklı iştirak" ana ortaklık ile bağlı
ortaklıklar arasındaki ÇAPRAZ (reciprocal) hisse sahipliğinin
konsolidasyonda elenmesini ifade eder, şirketin KENDİ hisselerini
piyasadan GERİ ALMASI (treasury stock/buyback) ile AYNI şey DEĞİLDİR.
Bu ikisini birbirine karıştırıp `2OC`'yi `treasury_stock` olarak
bağlamak Kural 8'i ("emin olunmayan bir kalemi varsayımsal DOLDURMA")
İHLAL ederdi — YAPILMADI.

Çapraz doğrulama: `data/exploration/` altındaki TÜM XI_29/UFRS kaynaklı
dosyalarda (JSON + readable) "hazine" kelimesi için grep SIFIR sonuç
verdi; aynı grep NASDAQ `companyfacts` dosyalarında (AAPL/ASTS/JPM/MSFT/
NVDA) "treasury" için ÇOKLU sonuç verdi — bu, aramanın YÖNTEMSEL olarak
çalıştığını (BİST'te gerçekten yok, arama hatası değil) doğrular.

**Sonuç:** V-16 GERÇEK bir kalıcı boşluk olarak kapatıldı (`_skor_roe()`
BİST için `treasury_stock=None` ile çağrılmaya devam eder, davranış
DEĞİŞMEDİ) — banka/sigorta gibi "kavramsal olarak yok" değil, "veri
BİST'in standart raporlama setinde AYRI satır olarak bulunmuyor" türü bir
yapısal kısıt (Is Yatırım'ın özet tablosu KAP'ın TAM XBRL taksonomisinin
bir alt kümesidir; KAP dipnot/özkaynak değişim tablosu düzeyinde teorik
olarak bulunabilir ama bu Faaliyet Raporu/dipnot okuma sınıfına girer,
bkz. aşağıdaki ayrı bölüm — YÜKSEK maliyet, bu turun kapsamı dışı).

### V-15 (2026-08-14 ikinci tur) — Sigorta/Finansman `interest_expense` araştırması

**Sigorta (UFRS_K) — KALICI BOŞLUK:** ANSGR'nin CANLI çekilen TAM gelir
tablosu (`data/exploration/ANSGR_UFRS_K_get_20260730_195513.json`, 409
kalem, `3*` önekli TÜM gelir tablosu satırları tek tek okundu) tarandı.
Sigorta şirketlerinin (hayat-dışı) gelir tablosu "Teknik Bölüm" (prim/
hasar) ve "Yatırım Gelirleri/Giderleri" olmak üzere İKİ ayrı bölümden
oluşur — borçlanma/finansman maliyeti niteliğinde AYRI bir "Finansman
Giderleri" satırı YOK. En yakın görünen kalem `3MA` ("Yatırım Yönetim
Giderleri – Faiz Dahil (-)", ANSGR'de -43,3mn TL) yatırım PORTFÖYÜNÜN
yönetim gideridir (bir varlık yönetim maliyeti), şirketin KENDİ borcunun
faizi DEĞİLDİR — kavramsal olarak `interest_expense`'ten TAMAMEN FARKLI
(Kural 3/8: emin olunmayan bir eşleme UYDURULMADI). Sigorta şirketlerinin
sermaye yapısı esasen teknik karşılıklara (poliçe sahiplerine olan
yükümlülük, "float") dayanır, sanayi/bankadaki gibi maddi bir finansal
borç yükü GENELDE YOKTUR — "Faiz Karşılama Oranı" kavramı burada
YAPISAL OLARAK uygulanamaz (banka için V-15'in EK bölümünde daha önce
belirlenen "kavram farklı anlam taşır" ilkesiyle AYNI ruhta, ama burada
daha da kesin: karşılık gelen bir kalem BASİTÇE YOK). **Kod DEĞİŞTİRİLMEDİ,
kalıcı boşluk olarak kapatıldı.**

**Finansman (XI_29K/FINANSMAN) — veri VAR, skora bağlanmadı (bilinçli karar):**
KTLEV'in CANLI verisiyle (`data/exploration/KTLEV_XI_29K_raw_2026Q1.json`)
doğrulandı: `A3AE` = "IV. Finansman Giderleri (-)" (gerçek, sıfır-olmayan
negatif değer: -22.177.137 TL) VE `A3AH` = "VII. Net Faaliyet K/Z"
(4.763.274.586 TL) — bu ikisi GENUINE bir analog çift oluşturur (finansman
şirketleri işlerini borçlanarak fonluyor, "Finansman Giderleri" tam
anlamıyla sanayinin `interest_expense`'iyle AYNI kavram — bankadaki
"faiz ana iş kolu" istisnasının AKSİNE, finansman şirketi için borçlanma
maliyeti GERÇEK bir kaldıraç yüküdür). `isyatirim.py`'nin
`STANDARD_ITEM_MAP_FINANSMAN` sözlüğüne bu alan (`financing_expenses`
adıyla) zaten EKLİ ve `calculator.py`'nin Derin Kart trend bulgularında
("Finansman Giderleri" YoY satırı) kullanılıyor. **Bilinçli olarak
SKORA BAĞLANMADI**: `pipeline.py::hesapla_guvenlik_mercegi_finans`
banka/sigorta/finansman şablonlarının ÜÇÜNÜN de PAYLAŞTIĞI TEK bir
fonksiyon (şu an %100 ağırlıklı tek bileşen: Özkaynak/Aktif Oranı) —
buraya bir "Faiz Karşılama"/"Finansman Gideri Yükü" bileşeni eklemek YENİ
bir ağırlık payı İCAT ETMEYİ gerektirirdi (ör. %70/%30 gibi) ve bu paylaşımlı
fonksiyon üzerinden banka/sigortaya da (kavramsal olarak uygulanamadıkları
halde) sızma riski taşırdı — Global Direktif'in "spec'te olmayan
eşik/ağırlık uydurma" yasağını İHLAL ederdi. **Karar: V-12/V-13 ile AYNI
desen — veri zaten kısmen mevcut (informational, Derin Kart trend
satırında görünür), skorlanan bir bileşene bağlanması AYRI bir
`spec_yeni_bilesenler_agirliklandirma.md`-tarzı ağırlık kararı turu
gerektirir, bu turun kapsamı dışında bırakıldı.** Kod DEĞİŞTİRİLMEDİ.

### İlk Dalga öncelik sırası (GÜNCEL, 2026-08-14)

1. **V-32 — dashboard.py statik uyarı metni düzeltmesi.** En ucuz, en
   yüksek kullanıcı-güveni etkisi (kullanıcı ORGE'de veriyi görüyor ama
   panel "eksik" diyor — TUTARSIZLIK).
2. **V-33 — lens_guvenlik.py/lens_kalite.py docstring güncellemesi.**
   Aynı PR'da, geliştirici belgesi.
3. **V-16 — BİST Hazine Hissesi araştırması.** GRUP 3'te kalan tek
   "araştırılmamış, muhtemelen açılabilir" KALİTE kalemi (banka/sigorta
   gibi kavramsal olarak imkânsız DEĞİL — sadece nadiren ayrı raporlanan
   bir bilanço alt kalemi).
4. **V-15 (sigorta/finansman interest_expense) VE V-14 benzeri diğer
   XI_29-dışı şema genişletmeleri.** DÜŞÜK öncelik (küçük evren), ama
   AYNI teknik (mevcut desenin başka bir şemaya taşınması) — ucuz.
5. **V-17/V-18 — NASDAQ Greenblatt/Carlisle/ROC.** En yüksek etkili KALAN
   NASDAQ boşluğu (Değer merceğinin skorlanan bir bileşeni NASDAQ'ta HİÇ
   çalışmıyor) — orta-yüksek maliyet (EBIT/FD/yatırılan sermaye
   tanımlarının US GAAP formatında doğrulanması gerekir), ama İlk
   Dalga'nın NASDAQ tarafını BİST ile SİMETRİK hale getirir.
6. **V-05/V-06 — Devir Hızı/Amihud + Net Alacaklar oranı.** Sıfır yeni
   fetcher, ama hangi merceğe bağlanacağı küçük bir spec-eki gerektirir.
7. **V-12 — Ödenen Temettü + Finansman Faaliyetleri'nin bir Güvenlik
   bileşenine bağlanması.** Veri ZATEN var (informational), sadece ağırlık
   kararı gerekiyor (spec-eki).

### Kalıcı boşluk olarak KABUL EDİLECEKLER (bu turda netleşti)

- **Banka (UFRS)/Sigorta (UFRS_K)/Finansman şemalarında SG&A/Ar-Ge/Brüt
  Kâr kavramı** — Greenblatt/Schilit tarzı metriklerin doğası gereği
  uygulanamaz, "veri eksik" DEĞİL "kavram yok" (persona kural 5 ile
  TUTARLI, spesifikasyonlarda zaten "geçerli şirket türleri: sanayi" diye
  işaretli).
- **BİST hisse-başı DPS (per-share)** — KAP'ta 3 bağımsız şirkette XBRL
  etiketi aranıp bulunamadı; TOPLAM temettü ödemesi (payout oranı için
  yeterli) mevcut ama Kazanç Getirisi/temettü verimi formülünün payı
  (hisse-başı bazlı) için AYRI bir kaynak gerekir — GERÇEK yapısal kısıt.
- **BİST hisse geri alım (buyback) nakit akış kalemi** — 3 canlı KAP
  sayfasında da bulunamadı, GERÇEK bloker.
- **BİST Hazine Hissesi (`treasury_stock`, V-16)** — `isyatirim.py`
  XI_29 standardize kalem setinde (147 satır tam tarandı) AYRI bir
  bilanço alt kalemi olarak YOK; en yakın görünen `2OC` kavramsal olarak
  FARKLI (karşılıklı iştirak eleme, treasury stock DEĞİL) — 2026-08-14
  ikinci turunda araştırıldı, kod DEĞİŞTİRİLMEDİ, kalıcı boşluk.
- **Sigorta (UFRS_K) `interest_expense`/Faiz Karşılama Oranı (V-15)** —
  ANSGR'nin TAM gelir tablosu (409 kalem) tarandı, borçlanma maliyeti
  niteliğinde AYRI bir kalem YOK (en yakın `3MA` yatırım portföyü yönetim
  gideridir, borç faizi DEĞİL) — 2026-08-14 ikinci turunda araştırıldı,
  kod DEĞİŞTİRİLMEDİ, kalıcı boşluk (Finansman/XI_29K için durum FARKLI —
  veri VAR ama bilinçli olarak skora bağlanmadı, bkz. EK bölümü).
- **10+ yıllık trend serisi, WACC/Beta, kredi notu, sahiplik yapısı** —
  önceki turlarda zaten "yapısal/pahalı" olarak sınıflandırılmıştı,
  2026-08-14'te DEĞİŞMEDİ, aynı sınıflandırma GEÇERLİ.

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
  AYNI kök sorun (gelir tablosu alt-kırılımı yok — 2026-08-14'te BİST
  XI_29 için ÇÖZÜLDÜ) — piyasa+bileşen kırılımıyla 3 satıra ayrıldı.
- **`interest_expense`** (V-08 NASDAQ, V-15 BİST): KALİTE'nin "Faiz
  Gideri/Faaliyet Kârı" bileşeni VE GÜVENLİK'in "Faiz Karşılama Oranı"
  bileşeni AYNI ham veriyi kullanır (`spec_mercek_kalite.md` K5 = `spec_
  mercek_guvenlik.md` G1, kaynak notu AYNEN paylaşılıyor) — TEK satırda
  BİRLEŞTİRİLDİ, iki mercekte de "aynı kazanım" olarak işaretlenmeli —
  2026-08-14'te İKİSİ de BİST XI_29 sanayi için AÇILDI.
- **Capex** (V-09 NASDAQ, V-10 BİST): SADECE BÜYÜME merceğinde ama İKİ
  piyasada AYRI tag/maliyet — piyasa kırılımıyla 2 satıra ayrıldı, İKİSİ
  de BİTTİ.
- **Greenblatt ailesi** (V-17 Kazanç Getirisi+Acquirer's Multiple, V-18
  ROC): AYNI kök kısıt (`fundamental_screens.py` BİST-only çağrı, 2026-
  08-14'te DEĞİŞMEDİ), İKİ AYRI mercekte (Değer/Kalite) İKİ AYRI bileşen
  olarak kaldı — çift sayma DEĞİL (farklı formüller), ama TEK bir
  NASDAQ-genişletme görevi olarak BİRLİKTE kodlanabilir.
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

## İlk Dalga önerisi (ORİJİNAL, 2026-08-12 — 9 görevin TAMAMI BİTTİ)

Aşağıdaki 9 görev, GRUP 1-2'den seçilmişti — **TAMAMI 2026-08-12/14
arasında TAMAMLANDI** (bkz. yukarıdaki EK bölümü + Spec-eki altta).
Bu liste TARİHSEL REFERANS olarak korunur, yeni öncelik sırası için
yukarıdaki "İlk Dalga öncelik sırası (GÜNCEL, 2026-08-14)" bölümüne
bakılmalıdır.

1. V-04 — NASDAQ Hazine Hissesi Düzeltmeli ROE. **BİTTİ.**
2. V-01 — NASDAQ SG&A/Brüt Kâr. **BİTTİ.**
3. V-02 — NASDAQ Ar-Ge/Brüt Kâr. **BİTTİ.**
4. V-03 — NASDAQ Temettü/DPS/Payout. **BİTTİ.**
5. V-08 — NASDAQ Faiz Gideri/Faaliyet Kârı + Faiz Karşılama Oranı. **BİTTİ.**
6. V-09 — NASDAQ Capex/Net Kâr. **BİTTİ.**
7. V-07 — BİST `income_before_tax`/`pretax_profit` (XI_29). **BİTTİ.**
8. V-05 — Devir Hızı (turnover)/Amihud İlliklidite köprüsü. **HÂLÂ AÇIK**
   (İlk Dalga'ya dahil edilmişti ama kod taramasında BULUNAMADI — bu
   madde yanlışlıkla "bitti" sayılmamalı, bir sonraki tura taşınmalı).
9. V-10 — BİST Capex/Net Kâr. **BİTTİ** (kaynak `isyatirim.py` "4CAI"
   olarak değişti, bkz. Spec-eki).

**Bilinçli olarak İlk Dalga'ya ALINMAYAN ama yakın-ucuz adaylar:** V-06,
V-13 (NASDAQ opsiyon seyreltme — veri BİTTİ ama skora BAĞLANMADI),
V-11/V-12 (BİST DPS/finansman faaliyetleri — KISMEN BİTTİ, kapsam
küçültüldü).

---

## Faaliyet Raporu / Dipnot Araştırması (yapısal olarak FARKLI yaklaşım)

Bu bölüm 2026-08-12'de yazıldığı gibi AYNEN geçerlidir, 2026-08-14'te
dokunulmadı — bkz. aşağıdaki "Neden ayrı bir bölüm" / "Somut fizibilite
değerlendirmesi" / "Önerilen somut ilk adım" alt bölümleri (orijinal
metin korunuyor).

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
  ZATEN şirket bildirimlerini çekiyor.
- `kap.py::fetch_disclosure_attachment_pdf()` ZATEN bir bildirimin İLK
  ekli PDF'ini indiriyor.
- Eksik: (a) doğru bildirimi bulma mantığı, (b) PDF'ten metin çıkarma,
  (c) orkestrasyon.
- **Kaba maliyet:** ORTA.

**NASDAQ/SEC tarafı — TAMAMEN YENİ FETCHER GEREKİYOR:**
- `src/fetchers/sec_edgar.py` şu an SADECE yapılandırılmış XBRL çekiyor,
  10-K/10-Q gövde metni (MD&A) çeken fonksiyon YOK.
- **Kaba maliyet:** ORTA-YÜKSEK.

### Önerilen somut ilk adım

1. BİST önce (daha düşük maliyet).
2. Checklist tasarımı (kod DEĞİL, spec/prompt işi).
3. NASDAQ ikinci dalgaya bırakılır.
4. Schilit (06) kitabı işlendiğinde bu bölüm KÖKTEN GENİŞLER.

---

## Kısa özet — envanter büyüklüğü (2026-08-14 GÜNCEL)

- **33 tekil (deduplike) kalem** (V-01…V-33, V-32/V-33 bu turda EKLENDİ).
- **Durum dağılımı (2026-08-14 itibarıyla):** 12 BİTTİ (V-01, V-02, V-03,
  V-04, V-07, V-08, V-09, V-10, V-14, V-15 [kısmi, XI_29], NASDAQ Capex/
  SG&A/Ar-Ge/Faiz Gideri/Treasury dahil), 2 KISMEN BİTTİ (V-11 kapsam
  küçültülmüş, V-13 veri var skor yok), 2 YENİ ve UCUZ (V-32/V-33, metin
  düzeltmesi), geri kalan ~17 madde HÂLÂ AÇIK (V-05,V-06,V-12,V-16,V-17,
  V-18,V-19,V-20,V-21,V-22,V-23...V-31).
- **En acil görev artık YENİ veri ÇEKMEK DEĞİL** — `dashboard.py`'nin
  KENDİ statik uyarı metninin (V-32) bugünkü koddan GERİDE kalmış olması,
  kullanıcıya sistemin aslında sahip olduğu veriyi "eksik" diye
  göstermesi. Bu, veri boşluğu envanterinden AYRI bir "belge senkron"
  sorunu sınıfıdır ve gelecekte her veri-tamlığı PR'ının SON adımı olarak
  "dashboard.py uyarı metnini güncelle" kontrolü standart hale
  getirilmelidir (süreç önerisi, kod-gelistirici'ye).
- **7 UCUZ (kalan), 4 ORTA (kalan), 9 PAHALI (kalan), 9 YAPISAL/NİTEL/
  kapsam-dışı** (GRUP 4 değişmedi).

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

**NOT (2026-08-14 doğrulaması):** Bu not artık V-09/V-10 (Capex) için
KISMEN GEÇERSİZ — `capex_to_net_income_pct` ve `payout_ratio_pct` bu
turda `lens_buyume.py`/`lens_kalite.py` içinde GERÇEKTEN skora bağlı
bulundu (kod okumasıyla doğrulandı, bkz. GRUP 1/2 tabloları üstte). Bu,
2026-08-12 ile 2026-08-14 arasında AYRI bir kod-gelistirici turunda
ağırlık tablosunun genişletildiğini gösteriyor (muhtemelen `docs/spec/
spec_yeni_bilesenler_agirliklandirma.md` — bu spec dosyası bu turda
AYRINTILI OKUNMADI, bir sonraki turda çapraz kontrol edilmeli). Sadece
**V-12 (net finansman faaliyetleri) VE V-13 (opsiyon seyreltme)** hâlâ
"bilgi amaçlı, skora bağlanmadı" durumunda KALDI.

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
GEREKMEZ. Alan adı ("dividends_paid") NASDAQ ile ORTAK tutuldu (V-12 ile
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
olarak kalır, NASDAQ tarafında ise `us-gaap:PaymentsForRepurchaseOfShares`
CANLI (AAPL) doğrulandı ve eklendi.

**V-13 — dipnot okuma GEREKMEDİ, task talimatıyla TUTARLI:** `us-gaap:
WeightedAverageNumberOfSharesOutstandingBasic` eklendi, mevcut
`WeightedAverageNumberOfDilutedSharesOutstanding` ile FARKI
`calculator.Ratios.diluted_dilution_pct` olarak AYRI bir alan adı altında
(mevcut `shares_outstanding` zincirini BOZMADAN) hesaplanıyor.

---

## EK: 2026-08-14 üçüncü tur — "4BB" kapsam düzeltmesi (isim düzeltmesi, PDF-okuma yoluna GİDİLMEDİ)

**Bulgu (bu turda CANLI doğrulandı, ORGE 2026 Q2 verisiyle):** V-04/V-15
turunda (77abde8) BİST XI_29 (sanayi) şirketleri için `interest_expense`
alanı İş Yatırım MaliTablo itemCode **"4BB" ("Finansman Giderleri")**
olarak eklenmiş ve "Faiz Gideri/Faaliyet Kârı" (KALİTE) + "Faiz Karşılama
Oranı" (GÜVENLİK) bileşenlerine bağlanmıştı. Bu turda ortaya çıktı ki
"4BB" aslında **TOPLAM "Finansman Giderleri"dir** (faiz + kur farkı zararı
+ diğer finansman kalemleri BİRLİKTE) — dar anlamda "Faiz ve Komisyon
Gideri" DEĞİLDİR.

**Kanıt:** ORGE'nin KAP denetim raporundaki gerçek "Faiz Gideri (Finansman
Giderleri İçindeki Faiz ve Komisyon Kalemi)" **10.948.770 TL** iken,
sistemin çektiği "4BB" değeri **873.786.105 TL** — yaklaşık **80 KAT
fazla** (ORGE'nin büyük kur farkı zararları var). İş Yatırım'ın
yapılandırılmış API'sinde bu dar "faiz+komisyon" kırılımı HİÇ YOK
("3CAD" = "Faiz, Ücret, Prim, Komisyon ve Diğer Giderler (-)" itemCode'u
denendi, ORGE'de HER dönemde sabit 0 dönüyor — şirket bu satırı hiç
doldurmamış). KAP dipnotlarında (PDF, denetim raporu) bu kırılım var ama
İş Yatırım'ın özet API'sinde yok — 600+ BİST hissesi için PDF/dipnot okuma
ölçeklenebilir DEĞİL.

**Alınan karar (kullanıcı onayıyla):** PDF-okuma yoluna GİDİLMEDİ. Formül/
eşik/ağırlık DEĞİŞTİRİLMEDİ (hâlâ anlamlı bir "toplam finansman yükü
karşılama" göstergesi) — SADECE bileşen adı ve açıklama metni dürüstçe
güncellendi: "Faiz Gideri/Faaliyet Kârı" → **"Finansman Gideri/Faaliyet
Kârı"** (KALİTE, `lens_kalite.py`), "Faiz Karşılama Oranı" →
**"Finansman Gideri Karşılama Oranı"** (GÜVENLİK, `lens_guvenlik.py`),
kur farkı dahil olduğu her iki mercekte de `reasoning_tr` metninde
netleştirildi. Python identifier'ları (`interest_expense`,
`interest_expense_to_operating_profit_pct`) DEĞİŞMEDİ — sadece kullanıcıya
görünen metinler (bileşen adı string'leri, `reasoning_tr`, dashboard uyarı
metni `PIYASA_SISTEMIK_EKSIK_BILESENLER`) güncellendi.

**NASDAQ tarafı ETKİLENMEDİ:** `sec_edgar.py`'de `us-gaap:InterestExpense`
gerçekten dar/net "faiz gideri"dir, geniş "finansman gideri" değildir —
sorun SADECE BİST (XI_29, ve muhtemelen banka/finansman şemalarındaki
benzer alanlar, henüz eşlenmedi) tarafında geçerlidir.

**Değişen dosyalar:** `src/analysis/lens_guvenlik.py`, `src/analysis/
lens_kalite.py`, `src/render/dashboard.py::PIYASA_SISTEMIK_EKSIK_
BILESENLER`, `tests/test_lens_guvenlik.py`, `tests/test_lens_kalite.py`
(string güncellemeleri). `docs/spec/spec_mercek_guvenlik.md`,
`spec_mercek_kalite.md`, `spec_yeni_bilesenler_agirliklandirma.md`,
`veri_tamlik_notu.md` BİLEREK dokunulmadı (tarihsel karar kayıtları).
