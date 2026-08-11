# 00 — Kitaplar Arası Sentez (Bilgi Bankası)

> **DURUM: PROVİZYONEL (3/6 kitap).** Bu sentez sadece Graham (01), Buffett/Clark (02) ve Damodaran (03) ile üretildi. Fisher (04 — Sıradan Hisseler Sıradışı Karlar) ve Lynch (05 — Borsada Tek Başına) kullanıcı kararıyla ŞİMDİLİK ERTELENDİ; Schilit (06 — Finansal Aldatmacalar) de işlenmedi. Sonuç:
> - **BÜYÜME merceğinin BİRİNCİL kaynakları (04+05) TAMAMEN eksik.** Mevcut 3 kitaptan bu merceğe düşen malzeme çok azdır (esas olarak Damodaran'ın büyüme-DCF formülleri ve Graham'ın büyüme hissesi şüpheciliği — bkz. §5). **Fisher/Lynch eklenmeden BÜYÜME mercek spec'i Faz 3'te ZAYIF temellenecektir.**
> - **GÜVENLİK merceğinin BİRİNCİL kaynağı (06 — muhasebe hilesi tespiti) TAMAMEN eksik.** Mevcut GÜVENLİK adayları sadece Graham'ın kırmızı bayrakları + genel kaldıraç/likidite ilkeleriyle sınırlı; tahakkuk/nakit ayrışması, kazanç yönetimi teknikleri gibi asıl HİLE TESPİTİ kapsanmıyor.
> - **DEĞER** (Graham+Damodaran) ve **KALİTE** (Buffett, kısmen Graham) merceği görece İYİ temellenmiş durumda.
> - **04/05/06 eklendiğinde bu dosyanın §5 (mercek dağılımı) ve §2 (çelişkiler) bölümleri MUTLAKA REVİZE EDİLMELİDİR** — yeni kitaplar hem yeni kesişim/çelişki hem yeni GÜVENLİK/BÜYÜME kodları getirecektir.

Kaynaklar: `bilgi-bankasi/01_graham_akilli_yatirimci.md` (İLKE-01…195, FORMÜL-01…36 [37-40 bilinçli boş], BAYRAK-01…52), `bilgi-bankasi/02_buffett_finansal_tablolar.md` (İLKE-01…61, FORMÜL-01…35, BAYRAK-01…36), `bilgi-bankasi/03_damodaran_degerleme.md` (İLKE-01…469, FORMÜL-01…178, BAYRAK-01…83).

---

## 1. Kesişim Noktaları

Aşağıdaki metrik/kavram kümeleri EN AZ iki kitap tarafından bağımsız olarak vurgulanıyor — QuaxisLabs bileşik skorunda yüksek ağırlık ADAYI olarak işaretlenmelidir.

### 1.1 F/K (P/E) disiplini — 3 kitap ortak
- **01:** İLKE-27 (piyasa geneli göreli F/K), İLKE-60-64 (çok-yıllı ortalama kazançla F/K), İLKE-140-141 (AA tahvil bazlı dinamik F/K tavanı), FORMÜL-02 (<10/10-20/>20 sınıflandırma), FORMÜL-08/31 (savunmacı F/K tavanı, ≤15×/≤20×), FORMÜL-21/32 (Graham Sayısı, F/K×PD/DD≤22,5).
- **02:** FORMÜL-34 (F/K≥40 satış eşiği, equity-bond bağlamında).
- **03:** FORMÜL-73 (P/E 3 varyant), FORMÜL-74 (PEG), İLKE-197 ("FD/FAVÖK<7x=ucuz" kuralının çürütülmesiyle AYNI mantık F/K'ya da uygulanır), BAYRAK-20/21/23 (medyan-ortalama çarpıklığı, negatif-kazanç örneklem-dışı-bırakma, PEG doğrusallık ihlali).
- **QuaxisLabs:** `calculator.ValuationMetrics.pe_ratio` MEVCUT (TTM); Graham'ın <10/10-20/>20 bant etiketi ve Damodaran'ın "medyana göre kıyasla, ortalamaya göre değil" uyarısı henüz UYGULANMAMIŞ.

### 1.2 PD/DD (P/B) disiplini — 3 kitap ortak
- **01:** İLKE-80 (≤1,33× — Ch.8 genel kural), İLKE-133 (≤1,5× — Ch.13/14 resmi 7-kriter listesi parçası), FORMÜL-17/32.
- **02:** İLKE-23 (dayanıklı avantajlı şirketler NADİREN defter değeri altında satılır — "ömür boyu fırsat"), Böl.30 eşik tablosu.
- **03:** FORMÜL-75 (P/BV tanımı), İLKE-199/203 (ROE-cost of equity farkının P/BV belirleyicisi), BAYRAK-25 (ROE kontrolsüz P/BV kıyası riski).
- **QuaxisLabs:** `pb_ratio` MEVCUT ve tanım olarak TUTARLI; Graham'ın eşiği + Damodaran'ın "ROE-ke farkı olmadan yorumlama" uyarısı birlikte bir "PD/DD rozeti" olarak eklenebilir.

### 1.3 ROE — Buffett + Damodaran ortak (Graham dolaylı)
- **02:** FORMÜL-22 (Böl.47-48'in merkezi formülü, MEVCUT), İLKE-40-41 (yüksek ROE = dayanıklı avantaj, ama negatif özkaynak/anormal ROE'de "güçlü net kâr geçmişi var mı" testi ZORUNLU).
- **03:** İLKE-203 (FD/Sermaye'nin ROC-kc belirleyicisi, P/BV'deki ROE-ke ile PARALEL), BAYRAK-25.
- **QuaxisLabs:** `roe_annualized` ZATEN MEVCUT — kitaplar arası EN OLGUN kesişim, doğrudan skorlanabilir.

### 1.4 Kazanç Getirisi (E/P) vs tahvil faizi — Graham + Damodaran ortak, Buffett'ın "equity bond" kavramıyla 3. varyant
- **01:** İLKE-27 (piyasa geneli), FORMÜL-03 (E/P vs AA tahvil), FORMÜL-36 (Güvenlik Marjı kazanç getirisi testi — kitabın merkezi formülü).
- **02:** İLKE-52-57 (Equity Bond — vergi öncesi kazanç/fiyat, uzun vadeli tahvil oranıyla kapitalizasyon).
- **03:** İLKE-40-41 (ima edilen risk primi — piyasa fiyatından geriye çözülen r), FORMÜL-84 (E/P = 1/P-E).
- **QuaxisLabs:** `pe_ratio` tersine çevrilebilir; `_RISK_FREE_RATE_PCT` (statik) mevcut ama CANLI veri değil. Üçü de AYNI kök veriye (kazanç/fiyat oranı ile risksiz getiri kıyası) dayanıyor — TEK bir "kazanç getirisi vs risksiz oran" bileşeni üç kitaptan da meşruiyet alıyor.

### 1.5 Borç/Özkaynak ve kaldıraç disiplini — 3 kitap ortak
- **01:** İLKE-22 (kurumsal sektör kaldıraç uyarısı), FORMÜL-27/33/34/38 (savunmacı/girişimci borç kriterleri), Ch.11 kapsama oranları (FORMÜL-18).
- **02:** İLKE-28-31 (LT borç <%50 sermaye), FORMÜL-16/17 (Toplam Yükümlülük/Özkaynak vs Hazine-Hissesi-Düzeltmeli), Böl.42 eşik tablosu.
- **03:** İLKE-53-57 (WACC ağırlıkları, borç tanımı), FORMÜL-02 (Hamada — levered/unlevered beta), İLKE-207/209 (risk/vergi etkisiyle kaldıraç-çarpan ilişkisi).
- **QuaxisLabs:** `calculator.Ratios.debt_to_equity` MEVCUT ama SADECE finansal (faizli) borç/özkaynak — kitaplardaki "Toplam Yükümlülük/Özkaynak" tanımından FARKLI (bkz. §2.3).

### 1.6 Faiz karşılama oranı / faiz gideri — 3 kitap ortak, EN SIK TEKRARLANAN VERİ AÇIĞIYLA BİRLEŞİK
- **01:** FORMÜL-18 (sektöre göre 4x-7x kapsama eşikleri), İLKE-112.
- **02:** FORMÜL-05 (Faiz Gideri/Faaliyet Kârı — kitabın en çok vurguladığı gösterge), BAYRAK-06.
- **03:** Tablo 2.4 (sentetik kredi notu, interest coverage bazlı), BAYRAK-82.
- **QuaxisLabs:** `interest_expense` sanayi/ticaret (XI_29) şirketleri için HİÇBİR fetcher'da (isyatirim.py, kap_financials.py) YOK — bkz. §4, en yüksek öncelikli tekil açık.

### 1.7 Kazanç istikrarı / çok-yıllı kazanç serisi — 3 kitap ortak, KİTAPLAR ARASI EN ÇOK TEKRARLANAN YAPISAL KISIT
- **01:** FORMÜL-05 (Shiller CAPE), FORMÜL-08/09/15/19/20/21/28/30 (7+ ayrı formülde 10 yıllık EPS serisi gerekiyor).
- **02:** FORMÜL-08 (10 yıllık HBK trendi), İLKE-11/14.
- **03:** İLKE-14 (temel büyüme = tutma oranı × ROE — çok-yıllı olmasa da BÜYÜME TAHMİNİNİN kendisi bu veriye muhtaç), FORMÜL-80/81 (DDM ailesi).
- **QuaxisLabs:** `trends.py` en fazla 12 çeyrek (~3 yıl) tutuyor — bu tek yapısal sınır, üç kitaptaki TOPLAM 15+ formülü bloke ediyor (bkz. §4, öncelik #2).

### 1.8 Temettü / DPS — 3 kitap ortak, EN SIK TEKİL VERİ AÇIĞI
- **01:** İLKE-39 (temettü = servet yaratma motoru), Ch.5 kural 3 (20 yıl kesintisiz), FORMÜL-04.
- **02:** Böl.45 ("Warren'ın zenginleşme sırrı" — dağıtılmamış kâr), Böl.50-52 (nakit akış finansman faaliyetleri).
- **03:** FORMÜL-80/81 (DDM ailesinin girdisi — payout oranı), İLKE-215.
- **QuaxisLabs:** DPS/temettü tutarı hiçbir fetcher'da YOK — bkz. §4, öncelik #1.

### 1.9 Cari Oran / likidite — Graham + Buffett ortak (Damodaran dolaylı, sıkıntı bağlamında)
- **01:** FORMÜL-26/33 (≥2,0 sanayi, ≥1,5 girişimci).
- **02:** FORMÜL-12 (MEVCUT), İLKE-20 (**ÇELİŞKİLİ** — bkz. §2.4).
- **03:** Ch.17 Sıkıntı Maliyeti bölümünde likidite dolaylı olarak (borç/nakit yeterliliği) ele alınıyor, doğrudan bir "cari oran" formülü YOK.
- **QuaxisLabs:** `current_ratio` MEVCUT.

### 1.10 ROIC/ROC/Yatırılan Sermaye Getirisi — Graham(Zweig) + Damodaran ortak
- **01:** FORMÜL-37 (ROIC, Davis/Zweig tanımı, ≥%10 çekici).
- **03:** İLKE-201/203/208 (ROC-cost of capital farkı, FD/Sermaye çarpanının belirleyicisi).
- **QuaxisLabs:** VERİ EKSİK (Capex, opsiyon maliyeti eksikliği nedeniyle) — ama `roe_annualized`+`operating_cash_flow` kaba bir vekil olabilir.

### 1.11 Muhasebe/kazanç kalitesi şüpheciliği — Graham + Damodaran ortak (Schilit henüz yok — bkz. üstteki PROVİZYONEL not)
- **01:** Ch.12+Comm.12 (pro forma kazanç, agresif gelir kaydı, sermaye-harcaması-yeniden-sınıflandırma, pensiyon varsayımı — KONTROL L, BAYRAK 31-35).
- **03:** İLKE-03/04 (analist önyargısı), BAYRAK-77 (sübjektif sıkıntı-iskontosu gerekçesi).
- **Ortak yapısal not:** İkisi de "dipnot/metin okuma" gerektiriyor; QuaxisLabs'ta HİÇBİR fetcher metin/dipnot çekmiyor — Damodaran'da bu açık TEK BAŞINA 4 farklı bölümde (Kısım 6/8a/8b/9) tekrarlandı (bkz. §4, öncelik #10).

### 1.12 Büyüklük / şirket ölçeği eşiği — sadece Graham (tek kitap, not düşülür)
- **01:** FORMÜL-11/25 (satış/varlık/piyasa değeri eşiği) — Buffett/Damodaran'da doğrudan karşılığı YOK, ileride Fisher/Lynch ile kesişebilir.

---

## 2. Çelişkiler (ÇÖZÜLMEDEN listelendi — mercek mimarisine girdi)

### 2.1 Sabit ucuzluk eşikleri vs "ortalamaya göre ucuz" yanılgısı
Graham'ın F/K<15, PD/DD≤1,5×, Graham Sayısı≤22,5 gibi SABİT sayısal tavanları (01/FORMÜL-02,17,21,31,32) doğrudan Damodaran'ın iki bağımsız eleştirisiyle GERİLİM içindedir:
- **BAYRAK-20** (03) — çarpan dağılımları HER ZAMAN pozitif çarpıktır, "ortalamanın altı=ucuz" yargısı sistematik olarak fazla sayıda firmayı ucuz gösterir; medyan kullanılmalı.
- **İLKE-197/BAYRAK-30** (03) — "FD/FAVÖK<7x=ucuz" pratik kuralı ABD'de ~1.500 firmanın bu eşiğin altında işlem görmesiyle ÇÜRÜTÜLÜR; sabit eşikler zaman/sektöre göre KAYAR.
Graham'ın kendisi de mekanik formüllerin "kendini yok eden" (İLKE-15/78) doğasını kabul eder — ama yine de SABİT sayısal eşikler önerir (44 yıllık deneyim argümanı, İLKE-187). Bu, kitabın KENDİ İÇİNDE de hafif bir gerilim taşır. **Mercek etkisi:** DEĞER merceğinde hem "mutlak eşik" (Graham) hem "sektör/zaman-göreli konum" (Damodaran) bileşenleri AYRI AYRI sunulmalı, biri diğerinin yerine geçmemeli.

### 2.2 Graham'ın KENDİ İÇİNDE 2 farklı PD/DD eşiği
01/İLKE-80 (Ch.8, ≤1,33× — genel muhafazakar alım kılavuzu) vs 01/İLKE-133 (Ch.13/14, ≤1,5× — resmi 7-kriterlik savunmacı liste). Bu iki eşik AYNI kitapta, farklı bağlamlarda tanıtılıyor — `01_graham_akilli_yatirimci.md`'nin Kısım 2/3/4 Uygulama Notları'nda AÇIKÇA işaretlenmiş bir iç-tutarsızlık (bilinçli fark, iki farklı KULLANIM BAĞLAMI). `valuation.py`'ye eklenirken İKİSİ AYRI etiketle sunulmalı.

### 2.3 "Borç/Özkaynak" tanım farkı — üç kitap arasında ima edilen ölçüm farkı
- **02** (Buffett) TAM tanımı önerir: Toplam Yükümlülükler/Özkaynak (ticari borç+tahakkuk+ertelenmiş vergi DAHİL).
- **01** (Graham) çoğunlukla "uzun vadeli borç ≤ net cari varlıklar" gibi DAR/yapısal bir kriter kullanır (FORMÜL-27).
- **03** (Damodaran) WACC bağlamında SADECE faiz taşıyan borç+kira taahhütlerini sayar, ticari borcu HARİÇ tutar (İLKE-54) — cost of capital hesabı için "Toplam Yükümlülük" tanımı YANLIŞ olur.
QuaxisLabs'ın mevcut `debt_to_equity` alanı (SADECE `financial_debt`) aslında Damodaran'ın WACC tanımına EN YAKIN olanıdır, ama Buffett'ın "gerçek" borç/özkaynak dediği (ve raporlarda kullanıcıya öyle sunulabilecek) tanımdan FARKLIDIR. **Üç farklı "borç/özkaynak" kavramı var, hepsi meşru, farklı SORULARA cevap veriyor** — tek bir alanla karıştırılmamalı.

### 2.4 Cari Oran yorumu — doğrudan çelişki
01/FORMÜL-26 Graham'ın SABİT eşiği (Cari Oran ≥2,0 sanayi şirketi için ZORUNLU) DOĞRUDAN 02/İLKE-20 ile çelişir: Buffett/Clark, dayanıklı rekabet avantajlı BİRÇOK şirketin (Moody's 0,64, Coca-Cola 0,95, P&G 0,82) Cari Oran<1 ile çalıştığını, klasik "cari oran<1=kötü" kuralının dayanıklı-avantaj TESPİTİ için "NEREDEYSE İŞLEVSİZ" olduğunu savunur — güçlü/istikrarlı kazanç gücü düşük likidite yastığı ihtiyacını ortadan kaldırır. **Bu, mercek mimarisinde DEĞER/GÜVENLİK mercekleri için AYRI yorumlanmalı**: Graham'ın eşiği GÜVENLİK/muhafazakarlık sinyali olarak, Buffett'ın istisnası KALİTE bağlamında (kazanç gücü güçlüyse likidite tamponu önemsizleşir) ele alınabilir.

### 2.5 Buffett'ın "sonsuza dek tut" felsefesi vs Graham'ın sürekli ucuzluk arayışı
02/İLKE-53 AÇIKÇA belirtir: Warren'ın modeli Graham tarzı değer yatırımcılığından "KÖKTEN FARKLI"dır — Graham'cılar sadece fiyat<içsel değer midir diye bakar, birkaç yıldan fazla tutmayı düşünmez; Warren 20+ yıllık ufuklarla kazancın BÜYÜME HIZINA odaklanır. 02/İLKE-58 bunu netleştirir: "dayanıklı rekabet avantajlı şirketler NADİREN Graham tarzı 'ucuz' fiyatlardan işlem görür" — yani KATI Graham disiplinini izleyen bir yatırımcı Buffett'ın en sevdiği şirketleri NEREDEYSE HİÇ satın alamaz. **Bu, DEĞER ile KALİTE merceklerinin NEDEN ayrı tutulması gerektiğinin en net kanıtı** (bkz. `temel-analiz-cercevesi` skill'inin çift-sayma denetimi ilkesi).

### 2.6 Temettü politikası görüş ayrılığı
01 (Graham, Ch.19): Kazancın %60-75'ini temettü olarak dağıtan şirket TERCİH edilmeli (İLKE-178) — yönetimin akılsızca harcama riskini azaltır; 20 yıl kesintisiz temettü savunmacı yatırımcı için ZORUNLU kriter. 02 (Buffett, Böl.52): Warren temettüyü SEVMEZ (İLKE-50) — hissedar temettüyü aldığı anda vergi öder; hisse geri alımı "vergisiz zenginleştirme" yöntemi olarak TERCİH edilir. **Doğrudan politika çelişkisi** — Graham temettüyü güvenlik/disiplin sinyali sayar, Buffett'ta vergi-verimliliği argümanıyla geri alım ÜSTÜN tutulur.

### 2.7 Nakit biriktirme yorumu
01 (Graham/Zweig, Ch.18, İLKE-175): Fazla nakit biriktirip hissedara İADE ETMEYEN yönetim (Microsoft 2003, $43 milyar örneği) özkaynak verimliliğini DÜŞÜRÜR, "bu fazla nakit dış hissedara nadiren fayda sağlar." 02 (Buffett, İLKE-17): "Nakit kraldır" — bol nakit+az borç HER ZAMAN zor zamanlarda avantaj sağlayan olumlu bir sinyal. **Nüans farkı:** Buffett'ın vurgusu KRİZ DAYANIKLILIĞI (GÜVENLİK ekseni), Graham/Zweig'in eleştirisi SERMAYE VERİMLİLİĞİ (DEĞER/KALİTE ekseni) — aynı ham veri (nakit pozisyonu) iki farklı mercekte ZIT işaretlerle yorumlanabilir; bu, `temel-analiz-cercevesi`'nin "çift sayma denetimi" ilkesinin somut bir test vakasıdır.

### 2.8 Büyüme hisselerine yaklaşım
01 (Graham): Savunmacı yatırımcı için büyüme hisseleri fiyat tavanıyla NEREDEYSE TAMAMEN dışlanır (İLKE-41); girişimci yatırımcı bile büyüme hisselerine "dikkatli yaklaşmalı" (İLKE-152); F/K>25-30× "tehlikeli" (İLKE-72, Zweig). 03 (Damodaran): Büyüme, DCF'in merkezi girdisidir; "temel büyüme" yöntemiyle (tutma oranı×ROE) İÇSEL OLARAK TUTARLI biçimde MODELLENEBİLİR (İLKE-14) — büyümeden KAÇINMAK değil, büyümeyi DOĞRU FİYATLAMAK önerilir. **Bu, Fisher/Lynch eklendiğinde BÜYÜME merceğinin en çok genişleyeceği eksendir** — şu an sadece Damodaran'ın metodolojik çerçevesi ve Graham'ın şüpheciliği var, "büyüme kalitesi nasıl tanınır" (Fisher'ın asıl konusu) EKSİK.

### 2.9 Matematiksel karmaşıklık felsefesi (kısmi çelişki, kısmen örtüşme)
01 (Graham, İLKE-187/BAYRAK-51): "44 yıllık deneyimde basit aritmetik/temel cebir ötesine geçen güvenilir bir hesaplama görmedim" — karmaşıklık spekülasyona bilimsel görünüm verir. 03 (Damodaran, İLKE-08-09, NN-2): Parsimoni ilkesi ("üç girdiyle değerleyebiliyorsan beş kullanma") BENZER bir sadelik tercihini savunur, AMA Damodaran aynı zamanda CAPM/APM/regresyon/opsiyon-fiyatlama gibi Graham'ın reddettiği araçları METODİK biçimde KULLANIR ve ÖNERİR. **Kısmi örtüşme, kısmi gerilim:** ikisi de aşırı karmaşıklığa karşı ama Damodaran'ın "yeterli" karmaşıklık eşiği Graham'dan belirgin biçimde YÜKSEKTİR.

---

## 3. Metrik → Kitap/Kod Çapraz Referans Tablosu

| Metrik | 01 Graham | 02 Buffett | 03 Damodaran | QuaxisLabs kod karşılığı | Durum |
|---|---|---|---|---|---|
| F/K (P/E) | İLKE-27,60-64,140-141; FORMÜL-02,08,31 | FORMÜL-34 (≥40 satış eşiği) | FORMÜL-73; İLKE-197; BAYRAK-20,21,23 | `calculator.ValuationMetrics.pe_ratio` | MEVCUT (TTM); bant/medyan etiketleme YOK |
| PEG Oranı | — | — | FORMÜL-74; BAYRAK-23 | `valuation.py::peg_ratio` | MEVCUT ama büyüme bazı revenue (kitaba göre net kâr/HBK olmalı) — TANIM SAPMASI |
| PD/DD (P/B) | İLKE-80,133; FORMÜL-17,32 | İLKE-23; Böl.30 | FORMÜL-75; İLKE-199,203; BAYRAK-25 | `calculator.ValuationMetrics.pb_ratio` | MEVCUT, tanım tutarlı |
| Graham Sayısı (F/K×PD/DD) | FORMÜL-21,32 | — | (dolaylı — çarpan tutarlılık testleriyle ilişkili) | `valuation.py::graham_number`/`graham_fair_value_price` | MEVCUT |
| ROE | (dolaylı) | FORMÜL-22; İLKE-40,41 | İLKE-203; BAYRAK-25 | `calculator.Ratios.roe_annualized` | MEVCUT |
| ROA | — | FORMÜL-13; İLKE-26 | — | — | HESAPLANMIYOR (ham veri hazır — EN UCUZ kazanım) |
| ROIC/ROC | FORMÜL-37 | — | İLKE-201,203,208 | — | VERİ EKSİK (Capex, opsiyon maliyeti gerekli) |
| Cari Oran | FORMÜL-26,33 | FORMÜL-12; İLKE-20 (ÇELİŞKİLİ) | (dolaylı, sıkıntı bağlamı) | `calculator.Ratios.current_ratio` | MEVCUT |
| Borç/Özkaynak (dar, finansal borç) | FORMÜL-27,34,38 | FORMÜL-16 (dar/geniş ayrımı) | İLKE-54 (WACC borç tanımı — dar) | `calculator.Ratios.debt_to_equity` | MEVCUT (sadece `financial_debt`) |
| Borç/Özkaynak (geniş, Toplam Yükümlülük) | (Ch.5-14 dolaylı) | FORMÜL-16 (asıl kitap tanımı) | — | — | HESAPLANMIYOR — ham veri (`short_term_liabilities`+`long_term_liabilities`) hazır |
| Hazine-Hissesi-Düzeltmeli B/Ö | — | FORMÜL-17,21 | — | — | VERİ EKSİK (`treasury_stock` yok) |
| Faiz Karşılama Oranı | FORMÜL-18 | FORMÜL-05 | Tablo 2.4 (sentetik kredi notu) | — | VERİ EKSİK (`interest_expense` XI_29'da yok — kitaplar arası EN ÇOK tekrarlanan tekil açık) |
| Kazanç Getirisi (E/P) vs risksiz oran | FORMÜL-03,36 (Güvenlik Marjı) | İLKE-52-57 (Equity Bond) | FORMÜL-84; İLKE-40,41 (ima edilen prim) | `1/pe_ratio` (türetilebilir) | KISMEN — `_RISK_FREE_RATE_PCT` statik/hardcoded, CANLI değil |
| Temettü / DPS | İLKE-39; FORMÜL-04 | Böl.45,50-52 | FORMÜL-80,81 (DDM ailesi) | — | TAMAMEN EKSİK — kitaplar arası EN SIK tekil açık |
| Payout Oranı | İLKE-178 (%60-75 önerisi) | İLKE-50 (geri alım tercihi) | FORMÜL-80,81 | — | VERİ EKSİK (temettü verisine bağımlı) |
| Capex / Net Kâr | (dolaylı, FORMÜL-37 ROIC) | FORMÜL-25,28; İLKE-46-49 | (Reinvestment Rate ailesinin girdisi) | — | TAMAMEN EKSİK — kitaplar arası 4+ tekrar |
| 10+ Yıllık Kazanç/EPS Serisi | FORMÜL-05,08,09,15,19,20,21,28,30 | FORMÜL-08; İLKE-11,14 | İLKE-14 (temel büyüme girdisi) | — | `trends.py` 12 çeyrek (~3 yıl) sınırlı — EN YÜKSEK öncelikli YAPISAL kısıt |
| WACC / Cost of Capital | — | (dolaylı) | İLKE-52-57; FORMÜL-02,03,14 | `valuation.py` (β=1 basitleştirmeli cost_of_equity) | KISMEN — gerçek beta/WACC hiç YOK |
| Beta (piyasa/temel) | — | — | FORMÜL-02,10-13; İLKE-42-51 | — | VERİ EKSİK (endeks getiri serisi fetcher'ı yok) |
| FD/FAVÖK (EV/EBITDA) | — | — | FORMÜL-78; İLKE-197; BAYRAK-30 | `calculator.ValuationMetrics.ev_ebitda` | MEVCUT |
| FD/Satış (EV/Revenue) | — | — | FORMÜL-76; İLKE-195,200 | `calculator.ValuationMetrics.ev_revenue` | MEVCUT, TANIM olarak DOĞRU (VS versiyonu) |
| Fiyat/Faaliyet Kârı (tutarsız çarpan) | — | — | BAYRAK-19 | `calculator.ValuationMetrics.price_to_operating_profit` | MEVCUT AMA TANIM HATASI (pay özkaynak, payda firma-geneli) |
| NCAV / Net-Net Bargain Testi | FORMÜL-01,12,14,66,75 | — | (varlık-bazlı değerleme kavramı, İLKE-12) | — | KISMEN TÜRETİLEBİLİR (ham veri hazır, formül eklenmemiş) |
| Brüt Kâr Marjı | (dolaylı) | FORMÜL-01; İLKE-02,03 | (dolaylı, marj-çarpan ilişkisi) | `calculator.Ratios.gross_margin_current` | MEVCUT |
| SG&A / Brüt Kâr | — | FORMÜL-02 | — | — | VERİ EKSİK (`sga_expenses` XI_29'da standalone yok) |
| Ar-Ge / Brüt Kâr | — | FORMÜL-03 | (İLKE-19 real-options bağlamında dolaylı) | — | VERİ EKSİK |
| Amortisman / Brüt Kâr | — | FORMÜL-04 | (İLKE-202, FAVÖK çarpanı belirleyicisi) | — | HESAPLANMIYOR (ham veri hazır — EN UCUZ kazanım) |
| Net Kâr Marjı | (dolaylı) | FORMÜL-07; İLKE-13 | (FD/Satış belirleyicisi, İLKE-204) | `calculator.Ratios.net_margin_current` | MEVCUT |
| Şerefiye (Goodwill) | (dolaylı, Ch.17 muhasebe manipülasyonu) | İLKE-22,23; BAYRAK-40 (Zweig) | İLKE-170 (P/BV kirliliği) | — | TAMAMEN EKSİK |
| Vergi Öncesi Kâr (income_before_tax) | (dolaylı) | FORMÜL-06,09 | (WACC/APV vergi kalkanı girdisi) | — | VERİ EKSİK — 3 kitapta 3+ kez ayrı bağlamda tekrarlandı |
| Nakit Pozisyonu Yorumu | İLKE-175 (fazla nakit=verimsizlik) | İLKE-16,17 (nakit kraldır) | İLKE-215-217 (nakit motifleri, israf/israf-değil ayrımı) | `calculator.BalanceSheetSummary.cash` | MEVCUT ham veri, YORUM ÇELİŞKİLİ (bkz. §2.7) |
| Muhasebe Kalitesi/Kazanç Manipülasyonu | Ch.12+Comm.12; KONTROL L; BAYRAK-31-35 | BAYRAK-07 (vergi tutarlılık kontrolü) | İLKE-03,04; BAYRAK-77 | — | NİTEL — dipnot/metin fetcher'ı YOK (kitaplar arası 4+ tekrar) |
| Kredi Notu / Temerrüt Olasılığı | (dolaylı, tahvil kapsama oranları) | — | Tablo 17.1,2.4; BAYRAK-81 | `src/analysis/merton.py::compute_merton_dd_edf()` | Merton MODELİ VAR ama HİÇBİR modüle BAĞLI DEĞİL (BAYRAK-79/80) |

**Not (kitaplar arası tutarsızlık uyarısı):** 02 dosyası bazı formüller için "MEVCUT" derken (örn. ROE, Cari Oran, Brüt/Net Marj), 01 ve 03 dosyaları AYNI alanlara SADECE dolaylı/kısmi atıfta bulunuyor — bu bir ÇELİŞKİ değil, kitapların odak farkının (Buffett = tekil şirket kalite göstergeleri, Graham/Damodaran = daha geniş piyasa/değerleme çerçevesi) doğal sonucu. `debt_to_equity` alanı ETRAFINDA (§2.3) GERÇEK bir tanım tutarsızlığı var — bu, spec aşamasında AYRI alanlarla (dar/geniş) çözülmeli, tek alan yeniden tanımlanarak DEĞİL (geriye dönük uyumluluk bozulur).

---

## 4. Konsolide Veri Eksiklikleri (öncelik sırasıyla, en çok tekrarlanan + en ucuz üstte)

Üç kitabın "QuaxisLabs veri eksiklikleri" / "Uygulanamaz" bölümlerinin KONSOLİDASYONU. Tekrar sayıları üç kitabın kendi içindeki VE kitaplar arası toplam gözlemi yansıtır (yaklaşık, `_ilerleme.md`'deki ayrıntılı sayımlarla tutarlı).

| # | Eksik veri/özellik | Kaç kez / hangi bağlamlarda tekrarlandı | Kaynak önerisi | Maliyet |
|---|---|---|---|---|
| 1 | **Temettü / DPS / payout oranı** | EN SIK — 01'de 5+ kez (Ch.5 kural 3, Shiller CAPE, Güvenlik Marjı, 7-kriter listesi, işadamı yatırımı), 02'de 2 kez (Özkaynaklar, Nakit Akış), 03'te DDM ailesinin (FORMÜL-80/81) TAMAMINDA tekrar tekrar | isyatirim.py'de temettü itemCode araştırması; KAP XBRL `ifrs-full_DividendsPaid`/`ifrs-full_DividendPerShare` standart etiketleri | ORTA (yeni fetcher alanı) |
| 2 | **10+ yıllık kazanç/EPS/net kâr trend serisi** (`trends.py` 12 çeyrek sınırı) | 01'de 9+ kez (neredeyse her nicel formülde), 02'de 2 kez, 03'te büyüme tahmini (İLKE-14) için temel — TOPLAM en yüksek tekrar sayısı, TEK yapısal kısıt | `trends.py`'nin veri tutma ufkunun genişletilmesi (mimari değişiklik — yeni fetcher değil, mevcut serinin UZUN dönem saklanması) | YÜKSEK (mimari) ama EN YÜKSEK ETKİ |
| 3 | **interest_expense (sanayi/ticaret, XI_29)** | 01'de 3 kez (Ch.3/Ch.11/Ch.13), 02'de kitabın en çok vurguladığı gösterge, 03'te 6 kez (Kısım 1/3/5/6/7/9) — `kap_financials.py` (YENİ XBRL fetcher) içinde BİLE sadece banka şemasında var | KAP bildirim sayfasında "Finansman Giderleri" alt kalem taraması; muhtemelen TFRS interim raporlama pratiğinin kendisinden kaynaklanan bir sınır (araştırma gerektirir) | YÜKSEK (araştırma + fetcher) |
| 4 | **Capex (Yatırım Harcaması)** | 02'de kitabın en çok vurguladığı ikinci gösterge (Capex/Net Kâr ≤%50/<%25), 01'de dolaylı (ROIC, FORMÜL-37), 03'te reinvestment rate ailesinin (Kısım 2-3) TAMAMINDA temel girdi | KAP XBRL `ifrs-full_PurchaseOfPropertyPlantAndEquipment` | ORTA |
| 5 | **WACC / gerçek beta / kaldıraçsız beta** | SADECE 03'te ama 6 kez farklı bağlamda (Kısım 1/3/5/6/7/9) — FCFF/APV/EVA ailesinin TAMAMINI bloke ediyor | Pazar endeksi (BIST100/S&P500) günlük/haftalık getiri serisini çeken YENİ bir fetcher — `price_history.py`'nin hisse tarafı zaten hazır, sadece ENDEKS tarafı eksik | YÜKSEK (yeni fetcher + istatistik) |
| 6 | **income_before_tax (Vergi Öncesi Kâr)** | 01'de dolaylı, 02'de 3 kez (Gelir Tablosu, Değerleme×2), 03'te WACC vergi kalkanı hesaplarında dolaylı | `STANDARD_ITEM_MAP_FINANSMAN`'da isimlendirme emsali zaten var (`pretax_profit`); XI_29'a taşınması gerekiyor | DÜŞÜK-ORTA |
| 7 | **Ödenen Temettü + Nakit Akışı Finansman Faaliyetleri (Hisse İhracı/Geri Alımı Net, Borç İhracı/Geri Ödemesi Net)** | 02'de 2 kez (Özkaynaklar, Nakit Akış — "kesin cevap" bu turda verildi: hiçbiri yok), 01'de dolaylı (buyback disiplini) | KAP XBRL `ifrs-full_PaymentsForRepurchaseOfShares`/ilgili finansman faaliyeti etiketleri | ORTA |
| 8 | **Treasury Stock (Hazine Hissesi)** | 02'de 3 kez (Bilanço, Özkaynaklar×2 — düzeltmeli B/Ö ve düzeltmeli ROE ikisi de bloke) | KAP/isyatirim bilanço özkaynak alt kalemi araştırması | ORTA |
| 9 | **Dipnot/metin fetcher'ı (nitel muhasebe kalitesi/anlatı taraması)** | 03'te 4 kez BAĞIMSIZ ortaya çıktı (Kısım 6 opsiyon/sinerji gerekçesi, Kısım 8a M&A açıklaması, Kısım 8b şeffaflık taraması, Kısım 9 sıkıntı-iskontosu gerekçesi), 01'de Ch.12 kazanç kalitesi (KONTROL L) NİTEL olarak AYNI ihtiyacı işaret ediyor | LLM-tabanlı dipnot/metin okuma modülü (kod DEĞİL, ayrı bir mimari bileşen — Gemini yorum katmanına "değerlendirilecek nitel sorular" olarak beslenebilir, bkz. `temel-analiz-cercevesi` madde 6) | YÜKSEK (yeni mimari bileşen) |
| 10 | **Sahiplik yapısı / yönetişim / çapraz-sahiplik verisi** (oy hakkı sınıfı, içeriden sahiplik %, float, yönetim kurulu bağımsızlığı) | SADECE 03'te ama 2 kez (Kısım 7 Ch.13 kontrol değeri, Kısım 8b Ch.16 şeffaflık) — TÜM bir veri SINIFI eksik, tekil alan değil | SEC EDGAR (NASDAQ 10 hissesi için DEF14A/10-K) kısmen ÇEKİLEBİLİR; BIST için KAP'ta pay sahipliği bildirimleri araştırılmalı | YÜKSEK |
| 11 | **Çok-firma cross-sectional/sektör regresyon altyapısı** (persentil, medyan, regresyon) | SADECE 03'te ama 3 kez (Kısım 4-5 relative valuation regresyonları, Kısım 9 agregatif P/E) — VERİ değil, MİMARİ/ÖZELLİK eksikliği | Yeni bir "evren-çapında toplu tarama" modülü (mevcut `sektor-siniflandirma` skill'iyle birleştirilebilir) — Faz kapsamı DIŞINDA olabilir, uzun vadeli backlog | ÇOK YÜKSEK (yeni ürün özelliği) |
| 12 | **Kredi Notu (bond/issuer rating)** | SADECE 03'te ama 3 kez (Kısım 1 Tablo 2.4, Kısım 3 Tablo 6.2, Kısım 9 Tablo 17.1) | Harici kredi derecelendirme API'si (Fitch/S&P/Moody's) VEYA Merton EDF'den türetilmiş "sentetik kredi notu" (interest_expense eksikliği bunu da bloke ediyor) | YÜKSEK (harici veri kaynağı) |
| 13 | **Envanter/Şerefiye/Maddi Olmayan Duran Varlık/ayrı Uzun Vadeli Yatırım kırılımı** | 02'de 4 alan standalone eksik (Bilanço), 01'de Ch.17'de dolaylı (goodwill/muhasebe manipülasyonu) | KAP bilanço alt kalem araştırması | DÜŞÜK ÖNCELİK (çoğunlukla nitel/çok-yıllı karşılaştırma gerektiriyor) |

### Düşük maliyetli, YÜKSEK değerli kazanımlar (veri EKSİK değil, sadece FORMÜL/ETİKET eksik — üç kitaptan da doğrulandı)
Bunlar §4'ün ana tablosundan AYRI tutuldu çünkü "eksik veri" değil, MEVCUT veriyle tek satır kodla eklenebilecek bileşenlerdir:
1. **ROA** (Net Kâr/Toplam Varlık) — ham veri hazır, `calculator.Ratios`'a hiç eklenmemiş (02).
2. **Amortisman/Brüt Kâr oranı** — ham veri (`depreciation_amortization`) hazır (02).
3. **F/K sınıflandırma bandı** (<10/10-20/>20) — `pe_ratio` hazır (01).
4. **PD/DD tavan etiketleri** (≤1,33× VE ≤1,5×, iki AYRI bağlamla) — `pb_ratio` hazır (01, bkz. §2.2).
5. **Kazanç Verimi (E/P)** — `pe_ratio`'nun tersi, negatif kazançlı şirketlerde bile anlamlı (03).
6. **Uzun Vadeli Borç/Net Kâr** (geri ödeme süresi) — ham veri hazır (02).
7. **"Toplam Yükümlülük/Özkaynak"** (Buffett'ın geniş tanımı, mevcut dar `debt_to_equity`'nin YANINA ayrı alan) — ham veri hazır (02, bkz. §2.3).
8. **`price_to_operating_profit` formül düzeltmesi** (BAYRAK-19) — TANIM HATASI, `enterprise_value/ttm_operating_profit` olarak DEĞİŞTİRİLMELİ (03).
9. **Merton↔valuation.py köprüsü** (BAYRAK-79/80) — SIFIR yeni veri, `compute_merton_dd_edf()` HİÇBİR modülden çağrılmıyor; kitap genelinde tespit edilen EN DÜŞÜK maliyetli/EN YÜKSEK etkili mimari bulgu (03).
10. **F/K≥40 mutlak satış eşiği** — ham veri hazır, sadece sektöre-göreli kıyas var, mutlak eşik YOK (02).

---

## 5. 4 Merceğe Kaba Bileşen Dağılımı

> **UYARI:** Bu dağılım SADECE hangi kod hangi merceğe UYGUN DÜŞÜYOR sorusuna cevap verir — sayı/eşik/ağırlık VERİLMEMİŞTİR (Faz 3 spec işi). BÜYÜME ve GÜVENLİK sütunları, üstteki PROVİZYONEL nottaki gerekçelerle ZAYIF/EKSİK olarak okunmalıdır.

### DEĞER (Fiyat ↔ değer farkı) — GÖRECE İYİ TEMELLENMİŞ
- **01:** İLKE-27,60-70,133-159 (bargain/NCAV/net-net/7-kriter/güvenlik marjı ailesinin TAMAMI); FORMÜL-01,02,03,12,14,17,19,21,31,32,34,36.
- **02:** İLKE-52-61 (equity bond, tahvil-kapitalizasyonu); FORMÜL-30-35 (Değerleme bölümünün TAMAMI).
- **03:** İLKE-10-25 (DCF vs relative vs opsiyon felsefesi), İLKE-26-57 (Kısım 1, CAPM/WACC/risk primi — DEĞER'in ALTYAPISI); FORMÜL-01,73-87 (relative valuation ailesinin TAMAMI); FORMÜL-52-72 (DCF/FCFE/FCFF ailesi, Kısım 3).
- **Mevcut kod bağlantısı:** `valuation.py` (Damodaran FCFE, Graham Sayısı, Lynch PEG), `calculator.ValuationMetrics` (pe/pb/ev_ebitda/ev_revenue).

### KALİTE (Rekabet avantajı + kârlılık kalitesi) — GÖRECE İYİ TEMELLENMİŞ
- **02:** Kitabın NEREDEYSE TAMAMI — İLKE-01-51 (Gelir Tablosu/Bilanço/Özkaynaklar rekabet avantajı göstergeleri); FORMÜL-01-24 (brüt marj, SG&A, Ar-Ge, faiz gideri, ROE, capex disiplinleri).
- **01:** Ch.11-13 (kazanç kalitesi, İLKE-110-137, KONTROL L); FORMÜL-37 (ROIC).
- **03:** İLKE-201-213 (ROC-cost of capital farkı, yatırım kalitesi etkisi — Kısım 5); dolaylı olarak marj/ROE'nin çarpan belirleyicisi rolü (İLKE-203/208).
- **Mevcut kod bağlantısı:** `calculator.Ratios` (gross_margin, net_margin, roe_annualized) — bu mercek MEVCUT kod tabanıyla EN ÇOK örtüşen mercek.

### BÜYÜME (Büyümenin gücü ve sürdürülebilirliği) — **ÇOK ZAYIF TEMELLENMİŞ (Fisher/Lynch eksik)**
- **03:** İLKE-14 (temel büyüme = tutma oranı×ROE), FORMÜL-80/81 (DDM ailesi büyüme girdisi), İLKE-201-213 (FD çarpanlarının büyüme belirleyicisi) — METODOLOJİK çerçeve var ama "büyüme KALİTESİ nasıl tanınır" (Ar-Ge verimliliği, pazar payı genişlemesi, yönetim vizyonu) tamamen Fisher'ın konusu, henüz YOK.
- **01:** İLKE-41,72-74,152 (büyüme hisselerine ŞÜPHECİ yaklaşım — bir "karşı-ağırlık" olarak faydalı ama BÜYÜMEYİ ÖLÇME yöntemi sunmuyor); FORMÜL-09,20 (büyüme oranı hesaplama YÖNTEMİ, ama VERİ EKSİK).
- **02:** Dolaylı — kitap büyümeyi DEĞİL, MEVCUT kârlılığın DAYANIKLILIĞINI ölçer (KALİTE'ye daha yakın).
- **Sonuç:** Bu merceğin Faz 3 spec'i şu an SADECE Damodaran'ın DCF-büyüme formülleriyle ve Graham'ın şüphecilik çerçevesiyle inşa edilebilir — **PEG oranı (mevcut) ve büyüme oranı hesaplaması (VERİ EKSİK) DIŞINDA somut bir bileşen kümesi YOK.**

### GÜVENLİK (Muhasebe hilesi + bilanço riski) — **ORTA-ZAYIF TEMELLENMİŞ (Schilit eksik)**
- **01:** BAYRAK-01-52'nin BÜYÜK KISMI (spekülasyon/davranışsal riskler HARİÇ, doğrudan bilanço/muhasebe riskleri: BAYRAK-06,07,08,31-35,40,44-48); İLKE-184-190 (Güvenlik Marjı merkezi kavramı); FORMÜL-18 (kapsama oranları), FORMÜL-27,33,34,38 (borç kriterleri); Ch.12 kazanç kalitesi (KONTROL L).
- **02:** Bilanço bölümünün TAMAMI (borç/likidite/kaldıraç göstergeleri, BAYRAK-11-20); Böl.49 (kaldıraç oyunları).
- **03:** Ch.17 Sıkıntı Maliyeti (Kısım 9, İLKE-408-469, FORMÜL-160-178, BAYRAK-72-83) — Merton EDF/temerrüt olasılığı çerçevesi; Tablo 2.4/17.1 (sentetik kredi notu).
- **Mevcut kod bağlantısı:** Piotroski F-Skoru (`fundamental_screens.py`, MEVCUT), `merton.py` (MEVCUT ama BAĞLANMAMIŞ — bkz. §4 düşük-maliyetli kazanımlar #9).
- **Kritik eksik:** Üç kitabın HİÇBİRİ Schilit'in asıl konusu olan SİSTEMATİK muhasebe hilesi TESPİT TEKNİKLERİNİ (tahakkuk/nakit ayrışması oranı, alacak-envanter/hasılat büyüme ayrışması oranı, agresif gelir kaydı desenleri, tek-seferlik-kalem BAĞIMLILIĞI ölçümü) içermiyor — mevcut malzeme NİTEL uyarılar (Graham Ch.12, Damodaran BAYRAK-77) düzeyinde kalıyor, SİSTEMATİK bir "kırmızı bayrak sayacı" için Schilit ZORUNLU.

---

## 6. Kısa Özet Tablosu — Mercek Sağlamlığı

| Mercek | Kaynak zenginliği (3/6 kitapla) | Ana kod bağlantısı | Faz 3 spec hazırlık durumu |
|---|---|---|---|
| DEĞER | GÜÇLÜ (Graham+Damodaran, kısmen Buffett) | `valuation.py`, `calculator.ValuationMetrics` | Hazır, veri açıklarıyla (DPS, WACC/beta) sınırlı |
| KALİTE | GÜÇLÜ (Buffett birincil, kısmen Graham/Damodaran) | `calculator.Ratios` | Hazır, veri açıklarıyla (SG&A, Ar-Ge, interest_expense, Capex) sınırlı |
| BÜYÜME | ÇOK ZAYIF (Fisher/Lynch YOK) | (kısmen `valuation.py::peg_ratio`) | Fisher+Lynch OLMADAN spec YAZILMAMALI |
| GÜVENLİK | ORTA-ZAYIF (Schilit YOK) | `fundamental_screens.py` (Piotroski), `merton.py` (bağlı değil) | Schilit OLMADAN sadece kaldıraç/likidite alt-kümesi yazılabilir, hile tespiti EKSİK kalır |

---

**Üretim notu:** Bu dosya `kitap-okuyucu` prosedürü (bkz. `.claude/skills/kitap-bilgi-cikarma/SKILL.md`) ve `temel-analiz-cercevesi`/`quaxis-mimari` skill'lerindeki çerçeveye göre, üç tamamlanmış kitap dosyasının (`01`, `02`, `03`) TAM METNİ okunarak üretilmiştir — kitap metni birebir alıntılanmamış, üç kaynağın kendi damıtılmış İLKE/FORMÜL/BAYRAK kodları SENTEZLENMİŞTİR.
