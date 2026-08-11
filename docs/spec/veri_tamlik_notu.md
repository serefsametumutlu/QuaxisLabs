# Veri Tamlık Notu — Faz 3a Spec Doğrulaması

## Amaç ve yöntem

Bu not, `docs/spec/spec_mercek_{deger,kalite,buyume,guvenlik}.md` ve
`docs/spec/spec_bilesik_skor.md` içinde işaretlenmiş TÜM "erişilemiyor /
veri yok / desteklenmiyor / VERİ EKSİK / hesaplanamıyor" bayraklarının
GERÇEK durumunu doğrular.

**Kaynaklar (kitap PDF/md dosyaları YENİDEN OKUNMADI, persona kısıtına
uyuldu):**
- `bilgi-bankasi/00_sentez.md` §3 (Metrik→Kod Çapraz Referans) ve §4
  (Konsolide Veri Eksiklikleri + Düşük-maliyetli kazanımlar listesi) —
  TEK kitap kaynağı.
- Statik kod okuması (Bash/kod çalıştırma YOK): `src/analysis/calculator.py`,
  `src/analysis/valuation.py`, `src/analysis/merton.py`,
  `src/analysis/trends.py`, `src/fetchers/isyatirim.py`,
  `src/fetchers/kap_financials.py`, `src/fetchers/sec_edgar.py`.

**Bu turda spec dosyaları DEĞİŞTİRİLMEDİ** — sadece bulgu + önerilen metin.

---

## Özet sayım

| Kategori | Sayı | Anlamı |
|---|---|---|
| **(A) YANLIŞ EKSİK** | 7 | Veri zaten mevcut/ucuz türetilebilir — spec metni GÜNCELLENMELİ (veya zaten doğruysa ONAYLANDI) |
| **(B) UCUZ AÇILABİLİR** | 8 (piyasaya göre kırılımlı — bkz. aşağıdaki asimetri notu) | 00_sentez §4'te somut kaynak/etiket var, spec'e yol-haritası notu eklenmeli |
| **(C) GERÇEK BLOKER** | 6 | Yeni mimari/araştırma gerektirir, spec olduğu gibi kalabilir (sadece §4 referansı eklenir) |

**En çarpıcı bulgu (bkz. §3 aşağıda): NASDAQ/BIST maliyet asimetrisi.**
00_sentez.md 3 kitabı da SADECE proje genelinde tek bir "VERİ EKSİK"
etiketiyle değerlendirmiş; kod incelemesi SG&A, Ar-Ge, Faiz Gideri, Hazine
Hissesi gibi kalemlerin **NASDAQ tarafında** (SEC EDGAR XBRL `us-gaap`
ad alanı, standart/evrensel taksonomi) çok DÜŞÜK maliyetle eklenebilir
olduğunu, **BIST tarafında** ise (KAP XBRL etiketi araştırması gerekir)
gerçekten daha maliyetli kaldığını gösteriyor — bu ayrım hiçbir spec
dosyasında şu an YOK, tek bir "VERİ EKSİK" etiketiyle HER İKİ piyasa
aynı kefeye konmuş.

---

## 1. DEĞER merceği (`spec_mercek_deger.md`)

| # | Satır | Bayrak | Kategori | Kod doğrulaması | Önerilen metin |
|---|---|---|---|---|---|
| D1 | 44 | Kazanç Getirisi (E/P) "YOK, TÜRETİLEBİLİR" | **A (zaten doğru)** | `calculator.compute_valuation.pe_ratio` MEVCUT (`ValuationMetrics.pe_ratio`, satır 821) — `1/pe_ratio` tek satır. Spec zaten "YENİ (ucuz)" diyor, DOĞRULANDI. | Değişiklik gerekmiyor. |
| D2 | 47 | DPS / temettü verimi "YOK, VERİ EKSİK" | **B** | `isyatirim.py` ve `kap_financials.py` içinde `dividend`/`temettu`/`DPS` deseni için grep SIFIR sonuç — gerçekten yok. 00_sentez §4 madde 1 somut etiket veriyor. | "VERİ EKSİK (BİST: KAP XBRL `ifrs-full_DividendsPaid`/`ifrs-full_DividendPerShare` — Faz sonrası araştırma+fetcher gerekli, ORTA maliyet; NASDAQ: SEC EDGAR `us-gaap:CommonStockDividendsPerShareDeclared`/`us-gaap:PaymentsOfDividends` — standart taksonomi, `sec_edgar.py`'nin mevcut `STANDARD_ITEM_MAP_US_GAAP` desenine tek satır eklenerek DÜŞÜK maliyetle açılabilir, bkz. 00_sentez §4 öncelik #1)." |
| D3 | 208 | NASDAQ opsiyon/warrant seyreltme "VERİ EKSİK (çalışan opsiyon verisi yok)" | **C, ama NÜANS var** | `sec_edgar.py` satır 395'te `us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding` ZATEN pay sayısı alanı için YEDEK tag olarak kullanılıyor (ama sadece fallback, ayrı "seyreltme etkisi" alanı olarak İZOLE EDİLMEMİŞ). `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` (temel pay sayısı) HENÜZ haritada YOK. Bu ikisinin FARKI (diluted-basic) opsiyon/RSU seyreltme etkisinin KABA bir vekilidir — dipnot/metin okuma GEREKTİRMEZ, TAMAMEN yapısal XBRL verisidir. Bu, 00_sentez §4'ün 13 maddesinde HİÇ YOK — sentezde atlanmış bir kalem. | "VERİ EKSİK, ama TAM bloker değil: `us-gaap:WeightedAverageNumberOfSharesOutstandingBasic` eklenip mevcut diluted tag'iyle FARKI alınarak KABA bir seyreltme yüzdesi (NASDAQ-only) türetilebilir — bu 00_sentez §4'e henüz GİRMEMİŞ bir madde, sonraki turda §4'e 14. madde olarak EKLENMESİ önerilir. BİST tarafında (opsiyon bazlı ücretlendirme KAP'ta standart XBRL etiketiyle raporlanmıyor) TAM bloker olarak KALIR." |

---

## 2. KALİTE merceği (`spec_mercek_kalite.md`)

| # | Satır | Bayrak | Kategori | Kod doğrulaması | Önerilen metin |
|---|---|---|---|---|---|
| K1 | 36 | ROA "YOK, TÜRETİLEBİLİR" | **A (zaten doğru)** | `net_income` (period data) ve `total_assets` (`BalanceSheetSummary.total_assets`) İKİSİ de MEVCUT, `Ratios`'a ROA alanı YOK — spec doğru. | Değişiklik gerekmiyor. |
| K2 | 37 | Amortisman/Brüt Kâr "YOK, ucuz" | **A (zaten doğru)** | `depreciation_amortization` alanı (`isyatirim.py` "4B", `kap_financials.py` `_DEPRECIATION_TAG`) VE `gross_profit` İKİSİ de MEVCUT — spec doğru. | Değişiklik gerekmiyor. |
| K3 | 38 | SG&A/Brüt Kâr "VERİ EKSİK" | **C (BİST) / B (NASDAQ)** | `Selling`/`Administrative` deseni HİÇBİR fetcher dosyasında YOK (isyatirim.py, kap_financials.py, sec_edgar.py — üçünde de SIFIR sonuç). **00_sentez §3/§4'te bu kalem için AYRI bir madde YOK** (sadece §3 tablosunda "VERİ EKSİK" yazıyor, §4'ün 13 maddesine hiç GİRMEMİŞ). | "VERİ EKSİK. NASDAQ: `us-gaap:SellingGeneralAndAdministrativeExpense` standart, yaygın raporlanan bir US GAAP kavramıdır — `sec_edgar.py`'nin mevcut `STANDARD_ITEM_MAP_US_GAAP` desenine (aday tag listesi) DÜŞÜK maliyetle eklenebilir. BİST: KAP XBRL karşılığı henüz ARAŞTIRILMADI (00_sentez §4'e YENİ madde olarak eklenmesi önerilir), YÜKSEK maliyetli kalır." |
| K4 | 39 | Ar-Ge/Brüt Kâr "VERİ EKSİK" | **C (BİST) / B (NASDAQ)** | Aynı grep taraması — `ResearchAndDevelopment` deseni HİÇBİR fetcher'da YOK. Aynı 00_sentez boşluğu (§4'te madde YOK). | "VERİ EKSİK. NASDAQ: `us-gaap:ResearchAndDevelopmentExpense` — teknoloji ağırlıklı NASDAQ evreninde (AAPL/GOOGL/NVDA/META hepsi standart raporlar) ÖZELLİKLE değerli, DÜŞÜK maliyetle eklenebilir. BİST: araştırma gerekli (00_sentez §4'e YENİ madde), YÜKSEK maliyetli kalır." |
| K5 | 40 | Faiz Gideri/Faaliyet Kârı "VERİ EKSİK (sanayi)" | **C (BİST), B (NASDAQ)** | `isyatirim.py`: `interest_expense` SADECE `STANDARD_ITEM_MAP_UFRS` (banka) içinde ("3B") — `STANDARD_ITEM_MAP_XI_29` (sanayi) içinde YOK, doğrulandı. `kap_financials.py`: `interest_expense`="kap-fr_InterestExpenses" SADECE `STANDARD_ITEM_MAP_KAP_UFRS_INCOME` (banka) içinde, `STANDARD_ITEM_MAP_KAP_XI_29_INCOME` içinde YOK. `sec_edgar.py`: `InterestExpense` deseni HİÇ YOK. 00_sentez §4 madde 3 kısmi yol gösteriyor ("KAP Finansman Giderleri alt kalem taraması", ama kendisi de "araştırma gerektirir" diyor — TAM somut değil). | "VERİ EKSİK — kitaplar arası EN SIK tekrarlanan açık. BİST: 00_sentez §4 öncelik #3'teki 'KAP bildirim sayfası Finansman Giderleri alt kalem taraması' yolu HENÜZ doğrulanmış bir XBRL etiketi İÇERMİYOR — YÜKSEK maliyetli araştırma gerekli, gerçek bloker olarak KALIR. NASDAQ: `us-gaap:InterestExpense` (bazı şirketlerde net faiz gideri/geliri birleşik raporlanabilir, dikkat gerekir ama) standart bir tag'dir — `sec_edgar.py`'ye eklenmesi ORTA-DÜŞÜK maliyetlidir, Merton köprüsünden BAĞIMSIZ, AYRI bir NASDAQ hızlı kazanım olarak işaretlenmeli." |
| K6 | 45 | Hazine Hissesi Düzeltmeli ROE (`treasury_stock` YOK) | **C (BİST), B (NASDAQ) — YÜKSEK ETKİLİ** | `treasury_stock`/`TreasuryStock` deseni hiçbir fetcher'da yok. `sec_edgar.py`'de YOK ama `us-gaap:TreasuryStockValue`/`TreasuryStockCommonShares` ABD şirketlerinde NEREDEYSE EVRENSEL standart tag'lerdir (Apple dahil — spec'in KENDİ Kenar Durumlar bölümü satır 162-168'de AAPL'ın "düşük özkaynak tabanlı, hazine hissesi düzeltmeli ROE verisi eksik" örneğini AÇIKÇA veriyor). 00_sentez §4 madde 8 sadece "KAP/isyatirim... araştırması" diyor, NASDAQ'ı hiç AYIRMIYOR. | "VERİ EKSİK. NASDAQ: `us-gaap:TreasuryStockValue` standart ve YAYGIN raporlanan bir tag'dir — spec'in kendi AAPL örneğini (Kenar Durumlar) doğrudan ÇÖZEBİLECEK, DÜŞÜK-ORTA maliyetli bir kazanımdır; `sec_edgar.py`'ye eklenmesi ÖNCELİKLENDİRİLMELİDİR (00_sentez §4 madde 8'in NASDAQ'a özel bir alt-maddesi olarak eklenmesi önerilir). BİST: hazine hissesi bilanço alt kalemi olarak nadiren AYRI raporlanır, araştırma gerekli, YÜKSEK maliyetli kalır." |

---

## 3. GÜVENLİK merceği (`spec_mercek_guvenlik.md`)

| # | Satır | Bayrak | Kategori | Kod doğrulaması | Önerilen metin |
|---|---|---|---|---|---|
| G1 | 47 | Faiz Karşılama Oranı "VERİ EKSİK" | **C (BİST) / B (NASDAQ)** | K5 ile AYNI kök neden (`interest_expense`). | K5'teki gerekçe/metin AYNEN uygulanır (spec zaten "kitaplar arası EN SIK" notunu taşıyor, sadece NASDAQ ayrımı EKLENMELİ). |
| G2 | 48 | Kredi Notu/Temerrüt Olasılığı (harici) "VERİ EKSİK" | **C (doğrulandı, değişiklik gerekmiyor)** | Harici derecelendirme API entegrasyonu hiçbir fetcher'da YOK — 00_sentez §4 madde 12 (Fitch/S&P/Moody's, "YÜKSEK, harici veri kaynağı") ile TUTARLI. Spec zaten Merton EDF'yi "sentetik vekil" olarak doğru sunuyor. | Sadece "(bkz. 00_sentez §4 öncelik #12)" çapraz referansı eklenebilir, içerik DEĞİŞMEZ. |

**En yüksek öncelikli bulgu (bu turda YENİDEN doğrulandı):** `merton.py`
içindeki `compute_merton_dd_edf()` fonksiyonu `src/` genelinde SADECE
kendi tanım satırında (satır 84) geçiyor — grep ile `src/` ağacının
TAMAMI tarandı, BAŞKA HİÇBİR modülde çağrılmıyor. Spec'in BAYRAK-79/80
iddiası (SIFIR yeni veri, sadece orkestrasyon eksik) **TAM DOĞRULANDI** —
kategori **A**, spec zaten doğru, herhangi bir metin değişikliği
GEREKMİYOR (kodlama fazına doğrudan devredilebilir).

---

## 4. BÜYÜME merceği (`spec_mercek_buyume.md`)

| # | Satır | Bayrak | Kategori | Kod doğrulaması | Önerilen metin |
|---|---|---|---|---|---|
| B1 | 52 | 10+ yıllık kazanç/hasılat serisi "VERİ EKSİK" | **C (doğrulandı)** | `trends.py` satır 42: `MAX_TREND_PERIODS = 12` — sabit, doğrulandı. 00_sentez §4 madde 2 ile TUTARLI. | Değişiklik gerekmiyor, spec zaten madde 2'yi doğru cite ediyor. |
| B2 | 53 | DPS/payout oranı "VERİ EKSİK" | **B** | D2 ile AYNI kök neden (temettü verisi). | D2'deki metin AYNEN uygulanır (NASDAQ/BİST ayrımıyla). |
| B3 | 54 | Capex/Ar-Ge "VERİ EKSİK" | **Capex: B (HER İKİ piyasa) — Ar-Ge: C(BİST)/B(NASDAQ)** | Capex: `PurchaseOfPropertyPlantAndEquipment`/`PaymentsToAcquirePropertyPlantAndEquipment` deseni hiçbir fetcher'da yok ama 00_sentez §4 madde 4 SOMUT bir KAP tag veriyor (`ifrs-full_PurchaseOfPropertyPlantAndEquipment`, maliyet ORTA); NASDAQ karşılığı `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` da standart bir tag'dir (henüz haritada yok ama eklenmesi ORTA-DÜŞÜK maliyetli). Ar-Ge: K4 ile AYNI. | "Capex: VERİ EKSİK ama İKİ piyasada da SOMUT kaynak var — BİST: KAP XBRL `ifrs-full_PurchaseOfPropertyPlantAndEquipment` (00_sentez §4 öncelik #4, ORTA maliyet); NASDAQ: `us-gaap:PaymentsToAcquirePropertyPlantAndEquipment` (ORTA-DÜŞÜK maliyet, standart tag). Ar-Ge: K4'teki metin AYNEN uygulanır." |
| B4 | 55 | Satış/Sermaye oranı "VERİ EKSİK (tam invested capital tanımı yok)" | **A (yanlış etiketlenmiş)** | `total_assets`, `equity`, `financial_debt` ÜÇÜ de `calculator.py`'de (BalanceSheetSummary/Ratios) MEVCUT ve doğrulandı — spec'in kendisi zaten "KISMEN türetilebilir" diyor, bu VERİ EKSİKLİĞİ değil bir TANIM/METODOLOJİ kararıdır (hangi bileşenler "yatırılmış sermaye" sayılacak). 00_sentez §1.10 AYNI mantığı ROIC için zaten uyguluyor ("kaba bir vekil olabilir"). | "VERİ MEVCUT, sadece 'yatırılmış sermaye'nin KESİN/textbook tanımı (opsiyon maliyeti, kira taahhütleri dahil Damodaran tanımı) için EK veri gerekir. `(equity+financial_debt)` ile KABA bir yatırılmış-sermaye vekili HEMEN türetilebilir (00_sentez §1.10'daki ROIC kaba-vekil mantığıyla AYNI ilke) — bu bileşen 'VERİ EKSİK' yerine 'YENİ (ucuz, yaklaşık tanımla)' olarak YENİDEN ETİKETLENMELİDİR." |

---

## 5. BİLEŞİK SKOR (`spec_bilesik_skor.md`)

| # | Satır | Bayrak | Kategori | Kod doğrulaması | Önerilen metin |
|---|---|---|---|---|---|
| S1 | 123 | "bankada VERİ EKSİK bir yer tutucuya [Büyüme merceği]" | **A (yanlış etiketlenmiş)** | `calculator.py`: `BankBalanceSheetSummary.loans`/`.deposits` VE `BankQuarterlySeriesPoint.loans` (çok-dönemli seri) ZATEN MEVCUT (satır 880-882, 928-932) — YoY kredi/mevduat büyümesi `classify_change(loans_current, loans_yoy_prior)` ile TEK SATIRLA türetilebilir, ham veri EKSİK DEĞİL, sadece scorer'a bağlanmamış bir HESAPLAMA eksik. | "Banka Büyüme bileşeni VERİ EKSİK DEĞİL — `calculator.BankRatios`'a henüz eklenmemiş ama `loans`/`deposits` alanları (ÇOK-dönemli, `BankQuarterlySeriesPoint` içinde) zaten MEVCUT. YENİ (ucuz): kredi/mevduat YoY büyümesi mevcut `classify_change()` mekanizmasıyla türetilir, banka Büyüme merceği bu turda 'YETERSİZ VERİ' yerine GERÇEK bir skor üretebilir." |
| S2 | 165-166 | Halka arz 1. çeyrek "Büyüme YoY veri yok" / Piotroski None | Bilgilendirici (kenar durum), YENİDEN kategorize gerekmiyor | Doğru davranış açıklaması — gerçek bir yapısal kısıt (önceki dönem karşılaştırması matematiksel olarak imkânsız), veri eksikliği DEĞİL. | Değişiklik gerekmiyor. |

---

## 6. Piyasa asimetrisi bulgusu — NASDAQ ucuz, BİST pahalı (00_sentez'e eklenecek yeni içgörü)

Kod incelemesi, 00_sentez.md §4'ün HENÜZ yakalamadığı sistematik bir
örüntü ortaya çıkardı: `sec_edgar.py`'nin `STANDARD_ITEM_MAP_US_GAAP`
mimarisi (alan başına ADAY TAG LİSTESİ, ilk eşleşen kullanılır) zaten
KANITLANMIŞ ve GENİŞLETİLEBİLİR bir desendir; ABD GAAP taksonomisi
(`us-gaap:*`) SG&A, Ar-Ge, Faiz Gideri, Hazine Hissesi, Temettü, Capex
için EVRENSEL/standart tag'ler sağlar — bunların BİST (KAP XBRL)
karşılıkları ise proje boyunca defalarca "canlı doğrulama gerektirir"
notuyla işaretlenmiş (TERA net borç örneği, TOASO FAVÖK örneği gibi).

**Sonuç:** Aynı "VERİ EKSİK" etiketi altında toplanan 5 kalemin (SG&A,
Ar-Ge, Faiz Gideri, Treasury Stock, kısmen Temettü) NASDAQ tarafında
kategori **B** (düşük-orta maliyetli, standart tag ekleme), BİST
tarafında kategori **C**'ye YAKIN (araştırma + doğrulama gerektiren,
daha yüksek maliyetli) olduğu görülüyor. Bir sonraki spec revizyon
turunda bu ayrımın HER İKİ mercek spec'inde (Kalite, Değer, Güvenlik,
Büyüme) "Sektör ayarlaması" değil "Piyasa ayarlaması" alt-başlığı
altında AÇIKÇA yapılması ve 00_sentez §4'e bu 5 kalem için NASDAQ-özel
alt-satırlar eklenmesi önerilir.

---

## 7. Bir sonraki tur için not

Bu bulgular, paralel çalışan `quant-uzmani`'nin KRİTİK bulgularıyla
BİRLİKTE, spec dosyalarına şu şekilde işlenmelidir (bu turda
UYGULANMADI):
1. A kategorisi (D1, K1, K2, G-Merton, B4, S1) → spec metni "VERİ EKSİK"den çıkarılıp doğru kaynağa bağlanır.
2. B kategorisi (D2/B2, K3/K4/K5/K6'nın NASDAQ yarısı, B3-Capex) → "Faz X'te [somut kaynak] ile açılabilir" yol haritası notuna çevrilir, piyasa ayrımı (BİST/NASDAQ) EKLENİR.
3. C kategorisi (D3, K3/K4/K5/K6'nın BİST yarısı, G2, B1) → olduğu gibi kalır, sadece 00_sentez §4 madde numarası referansı eklenir; SG&A/Ar-Ge/Faiz Gideri (BİST) için §4'e YENİ madde (14) önerilir.
