# 01 — The Intelligent Investor (Benjamin Graham, Rev. Ed. 1973 — Jason Zweig yorumlarıyla, 2003 basım)

## Meta

- **Kaynak:** `kitaplar/the-intelligent-investor-.pdf` (638 sayfa, taranmış/image-only PDF — JBIG2 sıkıştırmalı, metin katmanı YOK — OCR ile çıkarıldı: PyMuPDF `get_textpage_ocr`, Tesseract `C:\Program Files\Tesseract-OCR\tesseract.exe`, dpi=300, `language='eng'`).
- **Kullanıcı onayı (bu turdan önce):** (1) Jason Zweig'in her bölüm sonundaki "COMMENTARY" (Yorum) ekleri DAHİL edilecek — kaynak Graham'ın orijinal metninden AYRI işaretlenir ("Zweig commentary, s.X" notasyonuyla). (2) Kitap 7 ana kısma bölünerek işlenecek.
- **Bu dosyanın kapsamı — SADECE KISIM 1 (bu turda tamamlandı):**
  - Introduction: What This Book Expects to Accomplish (Graham, kitap s.1-11)
  - Commentary on the Introduction (Zweig, s.12-17)
  - Chapter 1: Investment versus Speculation (Graham, s.18-34)
  - Commentary on Chapter 1 (Zweig, s.35-46)
  - Chapter 2: The Investor and Inflation (Graham, s.47-57)
  - Commentary on Chapter 2 (Zweig, s.58-64)
  - Chapter 3: A Century of Stock-Market History (Graham, s.65-79)
  - Commentary on Chapter 3 (Zweig, s.80-87)
  - Chapter 4: General Portfolio Policy: The Defensive Investor (Graham, s.88-100)
  - Commentary on Chapter 4 (Zweig, s.101-111)
  - PDF sayfa aralığı: index 14-124. Sayfa dönüşümü: **kitap sayfası = PDF index − 13** (İçindekiler tablosuyla doğrulandı, önceki turda raporlandı).
- **Kalan kısımlar (henüz işlenmedi):** Ch.5-9 (Kısım 2?), Ch.10-13, Ch.14-15 (kitabın en yoğun sayısal eşik kaynağı — savunmacı/girişimci yatırımcı seçim kriterleri), Ch.16-20 + Postscript, 7 Appendix.
- **ID numaralandırması bu dosyada (kitapta) İLK turdur — İLKE-01, FORMÜL-01, BAYRAK-01'den başlar.** Sonraki kısımlarda KESİNTİSİZ devam edecek (Buffett kitabındaki [`02_buffett_finansal_tablolar.md`] yöntemiyle aynı).
- **OCR kalite notu:** Düz metin (paragraf) OCR'ı YÜKSEK güvenilirlikte. Kitaptaki çok-sütunlu SAYISAL TABLOLAR (Table 2-1, 2-2, 3-1, 3-2, 3-3) ve grafikler (Figure 1-1, 1-2, 2-1) OCR'da BÜYÜK ÖLÇÜDE OKUNAMAZ HALE GELDİ (rastgele sembol/harf dizileri) — bu tablolardaki HİÇBİR ham sayı bu dosyada KAYNAK OLARAK KULLANILMADI; sadece çevresindeki DÜZ METİNDE Graham'ın/Zweig'in AÇIKÇA SÖZEL/RAKAMSAL olarak tekrarladığı değerler alındı. İstisna: Figure 3-1 (P/E vs sonraki-10-yıl-getirisi tablosu) ve Figure 4-1 (tahvil türleri/getirileri tablosu) kısmen okunabildi, aşağıda kullanıldı ama satır bazında küçük OCR belirsizlikleri olabilir (işaretlendi).
- **Sayfa numarası OCR hataları:** Bu turda TESPİT EDİLMEDİ (önceki turdaki "529→929" tipi hatalar TOC sayfa numaralarında görülmüştü; bu kısımdaki (s.1-111) sayfa başlıkları küçük punto olsa da tutarlı okundu, TOC ile çapraz kontrol edildi, sapma bulunmadı).

---

## İlkeler

**Introduction (Graham):**

- **İLKE-01:** Kitabın temel tanımı: "Bir yatırım işlemi, kapsamlı bir analiz sonucunda anaparanın güvenliğini VE yeterli bir getiriyi vaat edendir; bu şartları taşımayan işlemler spekülatiftir." Kitabın TÜM sonraki politikaları bu ayrımın üzerine kuruludur. (s.1, ayrıntılı biçimde s.18'de tekrarlanır)
- **İLKE-02:** Kitap iki yatırımcı profiline hitap eder: **savunmacı** (defensive — güvenlik + çaba/uğraş özgürlüğü öncelikli) ve **girişimci** (enterprising — ekstra zaman/emek karşılığında ortalamanın üzerinde getiri arayan). Sonraki tüm politika önerileri bu ikili eksende ayrışır. (s.6-7)
- **İLKE-03:** Savunmacı yatırımcı için önerilen temel kısıtlama: hisseleri, maddi varlık (net aktif) değerinin çok üzerinde olmayan seviyelerden almakla sınırlamak — bu hem pratik hem PSİKOLOJİK bir gerekçeye dayanır: yatırımcının piyasanın keyfi dalgalanmalarına bağımlılığını azaltır. (s.9)
- **İLKE-04:** Yatırımcının başlıca sorunu — hatta baş düşmanı — genellikle KENDİSİDİR; teknik bilgi eksikliğinden çok davranışsal/psikolojik disiplin eksikliği sonucu belirler. (s.8)
- **İLKE-05:** Yatırımcıda "ÖLÇME/NİCELEME" alışkanlığı geliştirilmeli: hemen her menkul kıymetin bir fiyatı ucuz, başka bir fiyatı pahalı kılar; "hisseleri parfüm gibi değil, market alışverişi gibi" (fiyat-değer ilişkisini sürekli sorgulayarak) satın al. (s.9)

**Commentary on the Introduction (Zweig):**

- **İLKE-06:** %95 kayıp yaşayan bir yatırımın başa baş noktasına dönmesi için sonrasında **%1900 kazanç** gerekir — bu asimetri yüzünden Graham'ın "kayıptan kaçınma" vurgusu (Ch.6, 14, 20'de tekrarlanır) kitabın en kritik tekil ilkesidir. (s.12)
- **İLKE-07:** Graham'ın "zeki/akıllı" (intelligent) tanımı IQ veya eğitimle İLGİLİ DEĞİLDİR — sabır, disiplin, öğrenmeye açıklık ve duygularını kontrol edebilme gibi bir KARAKTER özelliğidir. Kanıt: LTCM'nin Nobel ödüllü kurucuları ve Isaac Newton, yüksek zekaya rağmen sürü psikolojisine kapılıp büyük kayıplar yaşamıştır. (s.13-14)
- **İLKE-08:** Hisseler fiyat YÜKSELDİKÇE daha RİSKLİ, fiyat DÜŞTÜKÇE daha AZ RİSKLİ hale gelir — çoğu yatırımcının hissettiğinin TAM TERSİ. Akıllı yatırımcı boğa piyasasından ÇEKİNMELİ, ayı piyasasını (harcama ihtiyacını karşılayacak nakit yeterliyse) MEMNUNİYETLE karşılamalıdır. (s.17)

**Chapter 1 — Investment versus Speculation (Graham):**

- **İLKE-09:** Graham'ın tanımının 3 eş-ağırlıklı unsuru (Zweig'in netleştirmesiyle): (1) hisseyi almadan önce şirketi VE işinin sağlamlığını KAPSAMLI analiz etmek; (2) ciddi kayba karşı BİLİNÇLİ koruma sağlamak; (3) "olağanüstü" değil "YETERLİ" bir performans hedeflemek. (s.35 — Zweig commentary)
- **İLKE-10:** Yatırımcı piyasa fiyatını YERLEŞİK değer standartlarıyla değerlendirir; spekülatör ise değer standardını PİYASA FİYATINA göre belirler — nedensellik yönü TERSTİR, ayrımın özü budur. (s.36 — Zweig commentary)
- **İLKE-11:** Pratik test: "Bu hissenin GÜNLÜK fiyatını hiç göremeseydim bile sahibi olmaktan rahat olur muydum?" — Evet ise yatırım, hayır ise muhtemelen spekülasyondur. (s.36 — Zweig commentary, Graham'ın 1972 Forbes röportajından alıntıyla)
- **İLKE-12:** Salt spekülasyon ne yasa dışı ne ahlaksızdır ve BİR MİKTARI kaçınılmazdır; ancak şu 3 durumda AKILSIZCA hale gelir: (a) yatırım yaptığını sanıp aslında spekülasyon yapmak, (b) gerekli bilgi/beceri olmadan CİDDİYETLE spekülasyon yapmak, (c) kaybetmeyi göze alamayacağından FAZLASINI riske atmak. (s.21)
- **İLKE-13:** MARJLA (borçla) işlem yapan HER profesyonel-olmayan yatırımcı, TANIM GEREĞİ spekülasyon yapıyor demektir — menkul kıymetin kalitesinden bağımsız olarak. (s.21)
- **İLKE-14:** "Kumar parası" (mad money) hesabı kuralları: yatırım hesabından KESİNLİKLE ayrı tutulmalı, boyutu KÜÇÜK olmalı ("ne kadar küçükse o kadar iyi"), piyasa yükselip kârlar arttığında hesaba YENİ PARA EKLENMEMELİ ("o zaman para ÇEKME zamanıdır"). (s.21-22)
- **İLKE-15:** Piyasayı yenmeye yarayan HER mekanik formül, kendini yok eden (azalan getiri yasasına benzer) bir SÜRECE tabidir — bir kez belgelenip/yaygınlaştıktan sonra rekabet o formülün getirisini aşındırır. Kanıt: Graham'ın kendi DJIA formülü 1949'dan sonra işlemez oldu; Dow Teorisi'nin başarısı 1934 sonrası ciddi biçimde zayıfladı. (s.33)
- **İLKE-16:** Girişimci yatırımcının pasif endeksleme yerine EKSTRA çaba harcamasının haklı gerekçesi olması için, beklenen ek getirinin buna DEĞMESİ gerekir — Graham'ın kendi eşiği: DJIA/endeks ortalamasına vergi öncesi yaklaşık **+5 puan** ekleyebilme beklentisi. (s.34)

**Commentary on Chapter 1 (Zweig):**

- **İLKE-17:** Aşırı yüksek portföy/hisse devir hızı (day-trading, <1 yıl ortalama elde tutma) spekülasyonun DAVRANIŞSAL imzasıdır. NYSE devir hızı 1973'te yıllık %20 (ort. 5 yıl elde tutma) iken 2002'de %105'e (ort. 11,4 ay) çıkmış; ortalama yatırım fonunun elde tutma süresi 1973'te ~3 yıldan 2002'de 10,9 aya düşmüştür. (s.37)
- **İLKE-18:** Geçmişte "işe yaramış" görünen nicel bir sistem/formül, Graham'ın 3 unsurlu yatırım tanımını karşılamadıkça GELECEK için HİÇBİR ŞEY kanıtlamaz — hem rastgele istatistiksel tesadüfe (veri kazıma — "Foolish Four", isim harfleri tekrarsız hisseler örneği) dayanan formüller HEM DE bir zamanlar gerçek olup sonradan yaygınlaşan edge'ler (Ocak Etkisi) FARKLI nedenlerle zamanla ERİR. (s.41-46)
- **İLKE-19:** "Kumar parası" hesabı toplam portföy servetinin **MAKSİMUM %10'u** ile sınırlandırılmalı, tamamen ayrı bir hesapta tutulmalı, yatırım hesabı/düşüncesiyle ASLA karıştırılmamalıdır. (s.46)

**Chapter 2 — The Investor and Inflation (Graham):**

- **İLKE-20:** Enflasyon ile hisse senedi kazançları/fiyatları arasında GÜVENİLİR bir KISA VADELİ korelasyon YOKTUR — örnek: 1966-1970'te yaşam maliyeti %22 arttı ama aynı dönemde hisse kazançları VE fiyatları GERİLEDİ. Enflasyonun hisseleri otomatik olarak yükselteceği varsayımı YANLIŞTIR. (s.51)
- **İLKE-21:** Enflasyon, hisse senedi değerlerini SADECE yatırılan sermaye üzerindeki KAZANÇ ORANINI yükseltirse artırabilir — Graham'ın 20 yıllık ABD verisine göre bu tarihsel olarak GERÇEKLEŞMEMİŞTİR (kazanç oranı enflasyona rağmen belirgin biçimde GERİLEMİŞTİR). (s.52)
- **İLKE-22:** Kurumsal sektörün TOPLAM BORÇ büyümesinin kâr büyümesine oranı SİSTEMİK bir uyarı göstergesi olarak izlenmelidir — Graham'ın 1950-1969 ABD verisi: kurumsal borç ~5 KAT artarken, vergi öncesi kâr sadece biraz fazla İKİYE katlanmıştır; bu, raporlanan "özkaynak kazanç oranının" giderek KALDIRAÇ kaynaklı hale geldiğini gösterir. (s.53)
- **İLKE-23:** Altın/koleksiyon eşyaları, sıradan yatırımcı için ENFLASYON KORUMASI olarak TARİHSEL OLARAK BAŞARISIZ olmuştur (Graham'ın verisi: altın 35 yılda sadece %35 arttı, hiçbir gelir getirmedi, saklama masrafı doğurdu — bir tasarruf hesabından bile KÖTÜ performans gösterdi). Graham "her şeye yatırım yaparak" enflasyona karşı korunma fikrine ŞÜPHEYLE yaklaşır. **[Not: Zweig'in yorumu bu görüşe AÇIKÇA KATILMAZ, aşağıda ayrı işaretlendi.]** (s.55)
- **İLKE-24:** Belirsizlik NEDENİYLE portföyün TAMAMI TEK bir varlık sınıfına (tüm-tahvil VEYA tüm-hisse) YATIRILMAMALIDIR — çeşitlendirilmiş hisse+tahvil karışımı, farklı enflasyon/deflasyon senaryolarına karşı KARŞILIKLI bir sigorta işlevi görür. (s.56-57)

**Commentary on Chapter 2 (Zweig):**

- **İLKE-25 ("Para Yanılsaması"):** Yatırımcılar getiriyi NOMİNAL (görünen sayı büyük mü) değişime göre değerlendirir, REEL (enflasyondan arındırılmış) değişime göre DEĞİL — bu davranışsal önyargı, aslında REEL KAYIP olan bir NOMİNAL KAZANCA sevinmeye yol açar. Yatırım başarısı her zaman enflasyon SONRASI ne kadar TUTABİLDİĞİNİZLE ölçülmelidir. (s.59)
- **İLKE-26:** Hisseler enflasyona karşı MÜKEMMEL değil, KUSURLU bir korumadır — tarihsel olarak 1926-2002 arası 64 adet 5-yıllık dönemin 50'sinde (%78'inde) hisseler enflasyonu yendi; yani yaklaşık HER 5 dönemden 1'İNDE BAŞARISIZ oldu. Hem DEFLASYON hem YÜKSEK enflasyon (>%6) hisse getirilerine ZARAR verir — ilişki DOĞRUSAL DEĞİLDİR, "ILIMLI enflasyon" hisseler için en elverişli bölgedir. (s.61-62)

**Chapter 3 — A Century of Stock-Market History (Graham):**

- **İLKE-27:** Piyasanın "çok yüksek" olup olmadığı ASLA sadece MUTLAK fiyat seviyesine bakılarak değerlendirilmemelidir — Graham'ın yöntemi her zaman GÖRELİDİR: hisse senedi kazanç getirisini (E/P) VE temettü getirisini, kaliteli tahvillerin getirisiyle KIYASLAYARAK değerlendirir. Bir piyasa mutlak F/K'ye göre "tarihsel olarak ucuz" görünse bile, tahvil-getiri kıyaslaması olumsuzsa CAZİP OLMAYABİLİR. (s.77-78)
- **İLKE-28:** Piyasa RİSKLİ/PAHALI değerlendirildiğinde Graham'ın önerdiği ÖNCELİK SIRASI: (1) menkul kıymet almak/tutmak için BORÇLANMAYI (marj) durdur; (2) hisselere ayrılan fon ORANINI artırma; (3) gerekirse hisse tutarını portföyün EN FAZLA %50'sine indir. (s.75)

**Commentary on Chapter 3 (Zweig):**

- **İLKE-29:** "Hisseler uzun vadede HER ZAMAN kazandırır" iddiası ciddi bir HAYATTA KALMA ÖNYARGISI (survivorship bias) taşır — 1871 öncesi endeksler sadece HAYATTA KALAN 7 kadar hisseyi izlerken, o dönemde YÜZLERCE şirket iflas edip kayıttan DÜŞÜLMÜŞTÜR; düzeltilmiş tahminler tarihsel hisse getiri avantajını yılda yaklaşık 1-2 puan AZALTIR. "Hisseler uzun vadede her zaman kazanır" iddiasına ŞÜPHEYLE yaklaşılmalıdır. (s.82)
- **İLKE-30:** Beklenen gelecek hisse getirisi 3 toplamsal bileşene AYRIŞTIRILABİLİR: (1) REEL kazanç büyümesi, (2) enflasyon, (3) spekülatif/duygusal (P/E'deki) değişim. Graham/Zweig'in 2003 başı örneği: %1,5-2 (reel büyüme) + %2,4 (enflasyon) + %1,9 (temettü getirisi) ≈ **%5,8-6,3** beklenen nominal getiri. (s.85 — bkz. FORMÜL-04)
- **İLKE-31:** Piyasa değerleme seviyeleri uzun vadede ORTALAMAYA DÖNÜŞ eğilimindedir ama GENİŞ bir DAĞILIMLA — bugünkünle benzer bir Shiller F/K (~20-23) seviyesinden başlayan tarihsel dönemlerde sonraki-10-yıl getirileri kabaca %0 ile %9 arasında değişmiş, ortalaması ~%6 olmuştur; belirli bir değerleme seviyesi hiçbir SONUCU GARANTİLEMEZ, sadece OLASILIKLARI kaydırır. (s.86-87)

**Chapter 4 — General Portfolio Policy: The Defensive Investor (Graham):**

- **İLKE-32:** Yatırımcının HEDEFLEMESİ gereken getiri, göze aldığı RİSK miktarına değil, işine ayırmaya istekli/muktedir olduğu AKILLI ÇABA miktarına bağlı olmalıdır — daha fazla risk almak, karşılığında daha fazla analitik çaba harcamadan daha yüksek getiriyi HAK ETTİRMEZ. (s.88)
- **İLKE-33:** Savunmacı yatırımcının hisse/tahvil dağılımı HİÇBİR ZAMAN %25-%75 bandının DIŞINA çıkmamalı; en basit varsayılan %50-%50'dir, sapma yaklaşık ±5 puana ulaştığında bu orta noktaya YENİDEN DENGELENİR. (s.89-90)
- **İLKE-34:** Mekanik bir formül/dengeleme politikasının değeri, "kanıtlanmış OPTİMAL" olmasından değil, BASİT, YÖN OLARAK doğru olmasından ve — en önemlisi — yatırımcının piyasa tehlikeli hale geldikçe GİDEREK DAHA FAZLA hisseye çekilmesini YAPISAL olarak ENGELLEMESİNDEN gelir. (s.91)
- **İLKE-35:** "Gerçekten iyi" bir imtiyazlı hisse (preferred stock), yatırım FORMU KÖTÜ olmasına RAĞMEN iyidir (Graham'a göre imtiyazlı hisse yapısı içsel olarak zayıftır) — sahibi ne tahvil sahibinin yasal alacak hakkına NE DE adi hissedarın kâr artışından pay alma potansiyeline sahiptir. İmtiyazlı hisse SADECE PAZARLIKLI (ucuz) fiyattan alınmalı, yoksa HİÇ alınmamalıdır. (s.98)

**Commentary on Chapter 4 (Zweig):**

- **İLKE-36:** "100'den yaşınızı çıkarın, kalanı hisseye yatırın" kuralını AÇIKÇA REDDET — Graham'ın kendi tahsis rehberliği hiçbir yerde YAŞA atıfta bulunmaz; risk kapasitesi somut yaşam koşullarına (bakmakla yükümlü olunanlar, iş/gelir istikrarı, acil nakit rezervi, yaklaşan büyük harcamalar) bağlıdır, doğum tarihine DEĞİL. (s.102-103)
- **İLKE-37:** Yaş veya risk toleransından BAĞIMSIZ olarak HERKES bir miktar minimum nakit/tahvil tamponu bulundurmalıdır — çünkü öngörülemeyen kişisel acil durumlar (işten çıkarılma, boşanma, sakatlık) likidite ihtiyacını "40 yıl sonra değil, 40 dakika sonra" doğurabilir. (s.103)
- **İLKE-38:** Hedef hisse/tahvil yüzdeleri belirlendikten sonra SADECE yaşam koşulları değiştiğinde DEĞİŞTİRİLMELİDİR — piyasa yükseldiği için hisse ALMAYIN, düştüğü için SATMAYIN; piyasa haberine tepki vermek yerine SABİT, önceden belirlenmiş bir takvimde (örn. yılda 2 kez, sabit tarihlerde) yeniden dengeleyin. (s.104)

---

## Formüller

| # | Formül | QuaxisLabs karşılığı |
|---|---|---|
| **FORMÜL-01** Net İşletme Sermayesi (NCAV) "pazarlık hissesi" testi: Piyasa Fiyatı < Net Cari Varlıklar (Dönen Varlıklar − TÜM Yükümlülükler), sabit varlıklar (tesis/ekipman) hiç sayılmadan (s.33-34) | **KISMEN MEVCUT / TÜRETİLEBİLİR.** `src/analysis/calculator.py`'de `current_assets` (ham veri, satır 676-677) ve `equity`/`total_assets` (satır 670, 689) mevcut; `total_liabilities = total_assets − equity` olarak TÜRETİLEBİLİR. Ancak NCAV/hisse başına net-net değeri ve bunun `market_cap` (`valuation.py`) ile kıyaslanan "NCAV'ın altında mı" sinyali `calculator.py`/`valuation.py`'de DOĞRUDAN HESAPLANMIYOR — ham veri hazır, formül eklenmesi ORTA maliyetli (3 alanın birleştirilmesi + piyasa değeriyle kıyas). |
| **FORMÜL-02** P/E (F/K) sınıflandırması: <10 ucuz, 10-20 makul, >20 pahalı (Zweig footnote) (s.70) | **KISMEN MEVCUT.** `calculator.py` `pe_ratio` (satır 821, 851 — `_safe_div(market_cap, r.ttm_net_income)`) ZATEN hesaplanıyor. Ancak bu 3'lü ucuz/makul/pahalı BANT sınıflandırması `valuation.py`'de UYGULANMAMIŞ (sadece Graham 22,5 çarpanı [`graham_multiple`] ve Lynch PEG oranı var — ham F/K için basit eşik etiketi yok). Ham veri hazır, eklenmesi DÜŞÜK maliyetli. |
| **FORMÜL-03** Kazanç Getirisi (E/P = 1/F-K) ile yüksek dereceli tahvil getirisi kıyaslaması — piyasanın göreli ucuzluk/pahalılık testi (s.77-78) | **KISMEN MEVCUT.** E/P, mevcut `pe_ratio`'nun tersi alınarak TÜRETİLEBİLİR. Tahvil getirisi karşılığı: `valuation.py` `_RISK_FREE_RATE_PCT` (TRY ~%32, USD ~%4,3 — STATİK/hardcoded sabit) — Buffett turunda da tespit edilen aynı veri açığı: en yakın karşılık ama CANLI piyasa verisi DEĞİL. |
| **FORMÜL-04** Beklenen Hisse Getirisi = Reel Kazanç Büyümesi + Enflasyon + Temettü Getirisi (Gordon-denklemi tarzı ayrıştırma); Graham/Zweig 2003 örneği: %1,5-2 + %2,4 + %1,9 ≈ %5,8-6,3 (s.85) | **VERİ EKSİK.** Temettü getirisi alanı QuaxisLabs'ta HİÇ YOK (Buffett turunda da tespit edilen aynı eksiklik — bkz. `_ilerleme.md` "Özkaynaklar turundan"). Enflasyon oranı harici makro veri olarak sistemde YOK. Reel kazanç büyümesi `trends.py`'de KISMEN mevcut (12 çeyrek/~3 yıl, NOMİNAL — enflasyondan arındırılmamış). |
| **FORMÜL-05** Shiller CAPE (Devresel/Enflasyon-Düzeltmeli F/K) = Fiyat / Son 10 Yılın Ortalama REEL Kazancı; >20 tarihsel olarak zayıf, <10 güçlü sonraki-10-yıl getirisiyle ilişkili (s.85-86) | **VERİ EKSİK.** `calculator.py`'nin `pe_ratio`'su SADECE TTM (son 12 ay) net kâra dayanır (`ttm_net_income`); 10 yıllık ortalama/enflasyon-düzeltmeli kazanç serisi HİÇBİR YERDE YOK (`trends.py` 12 çeyrek sınırıyla sınırlı) — kitap genelinde (ve Buffett turunda da) tekrar eden "uzun-vadeli kazanç serisi" veri açığının Değerleme alanındaki YENİ bir tezahürü. |
| **FORMÜL-06** %50-%50 Portföy Dengeleme Kuralı: hisse oranı ~%55'e çıkınca portföyün 1/11'i satılıp tahvile aktarılır; ~%45'e düşünce tahvilin 1/11'i hisseye aktarılır (s.90) | **KAPSAM DIŞI.** QuaxisLabs tekil hisse/kripto ANALİZ motorudur (bkz. proje `CLAUDE.md`: "30 asset backtesting/research system"); portföy-seviyesinde hisse/tahvil/nakit TAHSİSİ ve dengeleme mantığı sistemin kapsamında YOK — bu, tekil şirket temel-analiz verisi değil, YATIRIMCIYA ÖZGÜ portföy politikasıdır (Buffett turunda "maliyet-üzerinden-getiri" için verilen gerekçeyle AYNI mantık). |
| **FORMÜL-07** Kurumsal Sektör Kaldıraç Uyarısı: N-yıllık dönemde Toplam Borç Artışı ÷ Vergi Öncesi Kâr Artışı (Graham örneği: ~5x borç artışı vs ~2x kâr artışı, 1950-1969) (s.53) | **KISMEN MEVCUT (tekil şirket bazında).** `financial_debt` (ham veri, `calculator.py` satır 673-674) ve net kâr alanları mevcut; ancak ÇOK-DÖNEMLİ (10-20 yıllık) trend serisi YOK (`trends.py` 12 çeyrek sınırı) — kitap genelinde (Buffett turunda da) 3. kez ortaya çıkan AYNI "uzun-vadeli trend" veri açığı. |

---

## Eşikler (tablo)

| Gösterge | Eşik / Aralık | Yorum | Kaynak | Sayfa |
|---|---|---|---|---|
| Kayıp toparlama matematiği | %95 kayıp → başa dönmek için %1900 kazanç gerekir | Katastrofik kayıptan kaçınma, kazanç kovalamaktan çok daha önemlidir | Zweig, Comm.Intro | s.12 |
| "Kumar parası" (mad money) hesabı | Toplam servetin **MAKSİMUM %10'u** | Ayrı hesapta tutulmalı, kârdan sonra hesaba yeni para EKLENMEMELİ | Zweig, Comm.1 | s.46 |
| Marj (borçla) kullanımı | Herhangi bir oran | Kullanan nonprofesyonel yatırımcı TANIM GEREĞİ spekülasyon yapıyor sayılır | Graham, Ch.1 | s.21 |
| F/K (P/E) sınıflandırması | <10 | Düşük/ucuz | Zweig footnote, Ch.3 | s.70 |
| F/K (P/E) sınıflandırması | 10-20 | Makul/ orta | Zweig footnote, Ch.3 | s.70 |
| F/K (P/E) sınıflandırması | >20 | Pahalı | Zweig footnote, Ch.3 | s.70 |
| Shiller CAPE (10 yıllık reel kazanç bazlı F/K) | >20 | Tarihsel olarak sonraki dönemde ZAYIF getiriyle ilişkili | Zweig, Comm.3 | s.85-86 |
| Shiller CAPE | <10 | Tarihsel olarak sonraki dönemde GÜÇLÜ getiriyle ilişkili | Zweig, Comm.3 | s.85-86 |
| Shiller CAPE — 18 tarihsel gözlemin ortalaması (Figure 3-1) | Ort. F/K 20,8 → ort. sonraki-10-yıl getirisi %6,0 | Değerleme seviyesi olasılıkları kaydırır, sonucu GARANTİLEMEZ | Graham/Zweig veri tablosu, Comm.3 | s.86-87 |
| Savunmacı yatırımcı hisse/tahvil dağılımı | Min %25 — Maks %75 (hisse), tersi tahvil için | Bu bandın DIŞINA çıkılmamalı | Graham, Ch.1 & Ch.4 | s.22-23, s.89-90 |
| Varsayılan dengeleme oranı | %50-%50, ±~5 puan sapmada yeniden dengele | En basit "tüm amaçlı" program | Graham, Ch.4 | s.89-90 |
| Girişimci yatırımcının ekstra-çaba eşiği | DJIA/endeks ortalamasına ~+%5 (vergi öncesi) ekleyebilme beklentisi | Bu olmadan aktif seçim EMEĞE değmez | Graham, Ch.1 | s.34 |
| Piyasa riskli değerlendirildiğinde savunma sırası | (1) marjla alım DURDUR, (2) hisse oranını ARTIRMA, (3) gerekirse hisseyi portföyün MAKS %50'sine İNDİR | Graham'ın 1964 politika sırası, 1972'de de GEÇERLİ kabul edildi | Graham, Ch.3 | s.75, s.79 |
| Hisselerin enflasyonu yenme oranı (1926-2002, 64 adet 5-yıllık dönem) | 50/64 dönem (%78) | Hisseler ENFLASYONA KARŞI GARANTİLİ bir koruma DEĞİLDİR — ~%22 dönemde başarısız | Zweig, Comm.2 | s.61-62 |
| Yüksek enflasyon (>%6) yıllarında hisse getirisi | 14 yılın 8'inde KAYIP, ortalama getiri sadece %2,6 | Yüksek enflasyon hisseler için de KÖTÜDÜR (doğrusal olmayan ilişki) | Zweig, Comm.2 | s.61 |
| Tahvil kredi notu eşiği (savunmacı yatırımcı için belediye/eyalet tahvili) | SADECE en yüksek 3 not: Aaa (AAA), Aa (AA), A | Bunun altı savunmacı yatırımcı için yetersiz güvenlik | Graham, Ch.4 | s.95 |
| Bireysel tahvil çeşitlendirmesi için minimum (ABD, 2003 bağlamı) | ≥$100.000 sermaye VE ≥10 farklı tahvil (Hazine tahvilleri hariç) | Altındaki tutarlar için tahvil FONU tercih edilmeli | Zweig, Comm.4 | s.110 |
| "%100 hisse portföyü" uygunluk testi | Aşağıdaki 6 kriterin TAMAMI karşılanmalı (bkz. Kontrol Listesi B) | 6/6 karşılanmıyorsa TÜM parayı hisseye yatırmak UYGUNSUZ | Zweig, Comm.4 | s.105 |

---

## Kontrol Listeleri

**KONTROL A — "Spekülasyon mu, Yatırım mı?" testi (Ch.1 + Comm.1, 6 madde):**
1. Şirketi ve iş modelinin sağlamlığını GERÇEKTEN temelden analiz ettim mi (yoksa sadece fiyat hareketine mi bakıyorum)?
2. Anaparaya yönelik ciddi kayıp riskine karşı BİLİNÇLİ bir koruma (güvenlik marjı) var mı?
3. Beklentim "olağanüstü" değil "YETERLİ" bir getiri mi?
4. Bu hisseyi günlük fiyatını hiç GÖREMESEM bile sahiplenmeye razı mıyım?
5. Bu alımı MARJLA (borçla) mı yapıyorum? (Evetse: tanım gereği spekülasyon.)
6. Bu işlem "spekülasyon hesabımdan" mı yoksa "yatırım hesabımdan" mı yapılıyor — ikisi birbirine KARIŞIYOR mu?

**KONTROL B — "%100 Hisse Portföyüne Uygun muyum?" (Zweig, Comm.4, s.105, 6 madde — TÜMÜ karşılanmalı):**
1. Ailemin EN AZ 1 yıllık giderini nakit olarak ayırdım mı?
2. Önümde en az 20 yıl DÜZENLİ yatırım yapacağım bir süre var mı?
3. Önceki (2000 sonrası) ayı piyasasını ATLATTIM mı?
4. O ayı piyasasında hisse SATMADIM mı?
5. O ayı piyasasında EK alım YAPTIM mı?
6. Ch.8'deki davranışsal kontrol planını okuyup UYGULADIM mı?

**KONTROL C — Enflasyon Karşısında Portföy Kontrolü (Ch.2 + Comm.2, 4 madde):**
1. Portföyümün TAMAMI tek bir varlık sınıfında mı (tüm-hisse ya da tüm-tahvil)? (OLMAMALI)
2. Getirimi NOMİNAL mi yoksa enflasyon sonrası REEL olarak mı ölçüyorum ("para yanılsaması" kontrolü)?
3. Enflasyona karşı modern araçlardan (enflasyon-korumalı tahvil, GYO) pay ayırdım mı?
4. Altın/değerli maden payını (varsa) toplam varlığın küçük bir yüzdesiyle sınırladım mı?

**KONTROL D — Piyasa Seviyesi Değerlendirme Kontrolü (Ch.3 + Comm.3, 4 madde):**
1. Sadece F/K'ye mi bakıyorum, yoksa hisse kazanç getirisini (E/P) VE temettü getirisini tahvil getirisiyle de KIYASLADIM mı?
2. Kullandığım "tarihsel ortalama getiri" verisi SURVIVORSHIP BIAS içeriyor mu (özellikle erken dönem/pre-1871 veriler)?
3. Piyasanın Shiller CAPE'i (varsa) tarihsel bantların NERESİNDE (>20 pahalı, <10 ucuz bölge)?
4. Piyasa riskli görünüyorsa sırayla uyguluyor muyum: (a) marjla almayı BIRAK, (b) hisse oranını ARTIRMA, (c) gerekirse hisseyi portföyün MAKS %50'sine İNDİR?

---

## Kırmızı Bayraklar

- **BAYRAK-01:** Portföyün TAMAMININ veya neredeyse tamamının, "hisseler HER ZAMAN kazandırır" tezine dayanarak %100 hisseye ayrılması (özellikle kısa yatırım ufku olan bireyler için). (Graham, Intro, s.6, dipnot)
- **BAYRAK-02:** Marjla (borçla) hisse alımı — bu, TANIM GEREĞİ spekülasyondur, "yatırım" DEĞİLDİR. (Graham, Ch.1, s.21)
- **BAYRAK-03:** Yakın zamanda ÇOK yüksek getiri sağlamış bir fon yöneticisinin/stratejinin, bu getiriyi 10-20 yıl SÜRDÜRECEĞİNİ iddia etmesi (örn. "yıllık %50, sonraki 20 yıl %35" vaadi) — kısa dönem performansın ABARTILI ekstrapolasyonu. (Zweig, Comm.Intro, s.15-16)
- **BAYRAK-04:** "Piyasa artık eskisi gibi çalışmıyor, eski oranlar/formüller (Graham-Dodd dahil) artık GEÇERSİZ" iddiaları — her balon döneminde (1999-2000 örneği) TEKRARLANAN bir kalıp. (Zweig, Comm.Intro, s.16)
- **BAYRAK-05:** Yayınlanmış/popülerleşmiş HERHANGİ bir "garantili piyasa yenme formülü" (Ocak Etkisi, "What Works on Wall Street", "Foolish Four") — yayınlanmasının ARDINDAN kısa sürede performansı ÇÖKER. (Zweig, Comm.1, s.41-45)
- **BAYRAK-06:** Aşırı yüksek portföy devir hızı / kısa ortalama elde tutma süresi (<1 yıl) — spekülasyonun DAVRANIŞSAL imzası. (Zweig, Comm.1, s.37)
- **BAYRAK-07:** Yüksek enflasyon dönemlerinde (>%6) hisse senedine güvenerek AGRESİF pozisyon almak — tarihsel olarak bu dönemlerin ÇOĞUNDA hisseler de kötü performans göstermiştir. (Zweig, Comm.2, s.61)
- **BAYRAK-08:** Kurumsal sektör toplam borcunun, kâr büyümesinden ÇOK daha hızlı büyümesi (borç/kâr makasının açılması) — raporlanan "kazanç oranının" giderek KALDIRAÇ kaynaklı hale gelme riski. (Graham, Ch.2, s.53)
- **BAYRAK-09:** "Yaşınız neyse 100'den çıkarın, kalanı hisseye koyun" gibi YAŞA dayalı mekanik tahsis kurallarına körü körüne güvenmek — kişisel gelir/gider/iş güvencesi durumunu hiç SORGULAMAMAK. (Zweig, Comm.4, s.102-103)
- **BAYRAK-10:** Piyasa yükseldiği için hisse oranını ARTIRMAK veya düştüğü için AZALTMAK (önceden belirlenmiş hedef tahsisi TERK etmek) — disiplinli dengeleme yerine piyasa haberine TEPKİ vermek. (Zweig, Comm.4, s.104)
- **BAYRAK-11:** Piyasa CAPE/uzun-vadeli F/K bandının tarihsel "pahalı" bölgesinde (>20) olmasına RAĞMEN "bu sefer farklı" varsayımıyla temkinsiz pozisyon büyütmek. (Zweig, Comm.3, s.86-87)

---

## Uygulama Notları

1. **Bu kısmın (Introduction + Ch.1-4) formüllerinin BÜYÜK kısmı DEĞERLEME/PORTFÖY-TAHSİSİ ağırlıklıdır, tekil şirket temel-analiz eşiği DEĞİL** — bu, Buffett kitabından (finansal tablo kalemi ağırlıklı) YAPISAL bir fark. Kısım 4 (Ch.14-15, savunmacı/girişimci seçim kriterleri) kitabın asıl "tekil hisse seçim eşiği" yoğun bölümü olacak — bu kısımda (Kısım 1) beklenen düşük yoğunluk NORMALDİR (talimatta da öngörülmüştü).
2. **QuaxisLabs kapsam sınırı netleşti:** FORMÜL-06 (50-50 portföy dengeleme) gibi PORTFÖY-SEVİYESİ hisse/tahvil/nakit tahsis mantığı QuaxisLabs'ın kapsamı DIŞINDADIR — sistem tekil BIST/NASDAQ/Crypto varlık ANALİZİ yapar, çok-varlık-sınıflı portföy yönetimi YAPMAZ. Bu, Buffett turundaki "maliyet-üzerinden-getiri kapsam dışı" tespitiyle AYNI mantık kategorisidir.
3. **Tekrar eden veri açığı (3. kez tespit):** "Uzun-vadeli (10+ yıl) trend serisi" eksikliği (Buffett turunda HBK/net kâr trendi ve borç/kâr trendi için, şimdi Shiller CAPE [FORMÜL-05] ve kurumsal kaldıraç uyarısı [FORMÜL-07] için) — `trends.py`'nin 12 çeyrek (~3 yıl) sınırı bu kitaptaki HER "tarihsel seri" temelli formülü ENGELLİYOR. Bu, iki kitap boyunca en sık tekrarlanan tekil kısıtlama haline geldi.
4. **Tekrar eden veri açığı (temettü):** Temettü getirisi/tutarı alanı YOK — Buffett turunda "Dağıtılmamış Kârlar" bağlamında tespit edilmişti, bu turda FORMÜL-04 (beklenen getiri ayrıştırması) için de aynı eksiklik ENGEL oluşturuyor. Öncelik listesine EK gerekçe olarak eklenmeli.
5. **F/K sınıflandırması (FORMÜL-02) EN UCUZ kazanım:** Ham veri (`pe_ratio`) zaten hesaplanıyor, sadece <10/10-20/>20 bant etiketleme mantığının `valuation.py`'ye eklenmesi yeterli — Buffett turundaki "amortisman/brüt kâr" ile AYNI düşük-maliyet kategorisinde.
6. **NCAV/net-net formülü (FORMÜL-01) ORTA öncelikli:** Ham veri (current_assets, total_assets, equity) TAMAMEN hazır; sadece türetme mantığı ve piyasa değeriyle kıyaslama eksik. Graham'ın klasik "bargain issue" kriteri olduğundan (Ch.1, Ch.7, Ch.15'te tekrar edecek), ileride Kısım 4 işlendiğinde bu formülün ÖNEMİ artabilir — o zaman yeniden değerlendirilmeli.
7. **Tarihsel/dönem-özel sayılar (1972, 2002-2003 tahvil getirileri, ABD vergi dilimleri) DOĞRUDAN eşik olarak KULLANILMAMALIDIR** — sadece METODOLOJİ örneği olarak (örn. "kazanç getirisini tahvil getirisiyle kıyasla" ilkesi HALA geçerli, ama "%7,19 Aaa tahvil getirisi" 1972'ye özgü bir veri noktasıdır, günümüz TR/US piyasasına doğrudan taşınamaz).
8. **Zweig'in Graham'la AÇIKÇA AYRIŞTIĞI tek nokta bu kısımda:** Altın/değerli maden konusunda (İLKE-23) — Graham altını başarısız enflasyon koruması olarak görürken, Zweig (Peter Bernstein/William Bernstein referanslarıyla) toplam varlığın %2-5'i kadar küçük bir GYO/değerli-maden fonu payını MAKUL bulur. Bu, "Graham'ın orijinal görüşü" ile "Zweig'in 2003 güncellemesi" arasındaki nadir AÇIK ÇELİŞKİ örneğidir — ileride `00_sentez.md` için not düşüldü.
9. **OCR ile ilgili tek belirsizlik:** Figure 3-1 tablosundaki birkaç satırda (1905, 1961, 1962) ondalık noktası/işaret belirsizliği var (örn. "19.6 «5.0", "22.0 OI") — bu satırlar EŞİK tablosunda TEK TEK kullanılmadı, sadece ORTALAMA (20,8 / %6,0) genel eğilim göstergesi olarak alındı, bu da metinde AÇIKÇA "Averages" satırı olarak okunduğundan güvenilir kabul edildi.

---
---

# Kısım 2: Bölüm 5-8 (Chapter 5-8 + Commentary, kitap s.112-224, PDF index 125-238)

## İşlenen bölümler (bu ana kısım)
- Ch.5 The Defensive Investor and Common Stocks (s.112-123)
- Commentary on Chapter 5 (s.124-131)
- Ch.6 Portfolio Policy for the Enterprising Investor: Negative Approach (s.133-144)
- Commentary on Chapter 6 (s.145-154)
- Ch.7 Portfolio Policy for the Enterprising Investor: The Positive Side (s.155-178)
- Commentary on Chapter 7 (s.179-187)
- Ch.8 The Investor and Market Fluctuations (s.188-212)
- Commentary on Chapter 8 (s.213-225, "Yatırımcı Sahiplik Sözleşmesi" ile biter)
- **Kalan kısımlar:** Kısım 3 Ch.9-13, Kısım 4 Ch.14-15, Kısım 5 Ch.16-18, Kısım 6 Ch.19-20+Postscript, Kısım 7 Appendix 1-7.
- **ID numaralandırması Kısım 1'den KESİNTİSİZ devam eder:** İLKE-39'dan, FORMÜL-08'den, BAYRAK-12'den başlar (Kısım 1'in son numaraları: İLKE-38, FORMÜL-07, BAYRAK-11).
- **OCR notu:** Düz metin yüksek güvenilirlikte okundu. Table 2-1/2-2/7-1/7-2(kısmen)/7-3(kısmen)/8-1, Figure 1-1/1-2/6-1/6-2/7-1/7-2/8-1 (çok sütunlu sayısal tablo/grafikler) BÜYÜK ÖLÇÜDE OKUNAMAZ oldu — bunlardan HİÇBİR ham sayı doğrudan kaynak alınmadı. İstisna: Table 7-2 (düşük/yüksek çarpanlı DJIA hisseleri karşılaştırması) ve Table 7-4 (net-net hisse deneyi, 1957-1959) DOĞRUDAN OKUNABİLDİ ve aşağıda kullanıldı; Table 7-3 (Chrysler EPS/fiyat) kısmen okunabildi ama tek tek satır verisi (özellikle 1958/1968 rakamları) kaynak olarak KULLANILMADI, sadece çevresindeki düz metinde tekrarlanan "P/E döngüsel şirketlerde ters yönlü hareket eder" ilkesi alındı.
- **Bu kısım kitabın "ilk somut sayısal seçim kriterleri" bölümüdür (koordinatörün işaret ettiği gibi):** Ch.5'in 4 kuralı ve Ch.7'nin bargain/net-net testleri, Ch.14-15'te (Kısım 4) daha da detaylandırılacak olan çerçevenin TEMELİDİR — bu kısımdaki eşikler muhtemelen Kısım 4'te yeniden atıfta bulunulacak/genişletilecek.

---

## İlkeler

**Chapter 5 — The Defensive Investor and Common Stocks (Graham):**

- **İLKE-39:** Temettüler, hisse senedi yatırımının uzun vadeli asıl SERVET YARATMA motorudur, sadece fiyat artışı değil — Zweig'in örneği: 1900'de ABD hisselerine yatırılan $1, tüm temettüler HARCANIRSA 2000'de $198'e; tüm temettüler YENİDEN YATIRILIRSA $16.797'ye ulaşır (Dimson/Marsh/Staunton verisi). (s.112-113, Zweig dipnotu)
- **İLKE-40:** Savunmacı yatırımcının adi hisse bileşeni için 4 ZORUNLU seçim kuralı: (1) yeterli ama aşırıya kaçmayan çeşitlendirme (min 10, maks ~30 hisse), (2) her şirket büyük/önde gelen/muhafazakar finanse edilmiş olmalı, (3) uzun ve KESİNTİSİZ temettü ödeme geçmişi, (4) fiyatın çok-yıllı ortalama kazanca göre bir tavanı aşmaması. (s.114)
- **İLKE-41:** Bu 4. kural (fiyat tavanı), "büyüme hissesi" kategorisinin NEREDEYSE TAMAMINI dışlar — yüksek güncel F/K, beklenen geleceğin fiyata ZATEN dahil edilmiş (hatta fazla ödenmiş) olması anlamına gelir; olağanüstü hızlı büyüme SONSUZA dek süremez ve şirket büyüdükçe kendi büyüme oranını TEKRARLAMASI zorlaşır. (s.115-116)
- **İLKE-42:** En iyi büyüme hissesi bile (örn. IBM), UZUN VADELİ büyüme beklentisinde HİÇBİR değişiklik olmadan, birkaç ay içinde piyasa fiyatının %50'sini kaybedebilir — bu kayıp, işin kendisindeki değil, piyasanın o işe biçtiği PRİMDEKİ güven kaybını yansıtır. (s.116)
- **İLKE-43:** "Risk" kavramı salt fiyat DALGALANMASIYLA eşitlenmemelidir — gerçek risk sadece şu 3 durumda vardır: (a) zorunlu satıştan kaynaklanan GERÇEKLEŞMİŞ kayıp, (b) şirketin temel durumunda CİDDİ bozulma, (c) içsel değere göre AŞIRI fiyat ödemek. İyi seçilmiş, çeşitlendirilmiş bir hisse grubu, ara dönemde fiyatı dalgalansa bile, makul bir sürede tatmin edici getiri sağlıyorsa "güvenli" kanıtlanmış demektir. (s.121-122)
- **İLKE-44:** Menkul kıymet seçimi yatırımcının FİNANSAL KAYNAKLARINA değil, BİLGİ/DENEYİM/MİZAÇINA bağlı olmalıdır — Graham 3 farklı profille (dul kadın, orta kariyerli doktor, genç tasarrufçu) bunu gösterir: hepsi, bilinçli olarak girişimci yatırımcı olmayı SEÇMEDİKÇE AYNI savunmacı çerçeveye döner. (s.119-121)
- **İLKE-45:** Dolar-maliyet ortalaması (dollar-cost averaging), yatırımcının alım ZAMANLAMASI yapma dürtüsünü ORTADAN KALDIRDIĞI için güçlü bir tarihsel geçmişe sahiptir — Tomlinson'ın 23 adet iç içe geçen 10 yıllık DJIA alım dönemi (1929-1952 başlangıçlı) çalışmasında HER TEK dönem, dönem sonunda VEYA sonraki 5 yıl içinde KÂRLI çıkmış, ortalama gösterge kâr (temettüler hariç) %21,5 olmuştur. (s.118)

**Commentary on Chapter 5 (Zweig):**

- **İLKE-46:** "Bildiğini al" (Peter Lynch'in ünlü kuralı) SADECE onun tamamlayıcı ilkesiyle BİRLİKTE geçerlidir: hisseyi almadan önce finansal tabloları inceleyip iş değerini TAHMİN etmek — çoğu yatırımcı Lynch'i anarken bu İKİNCİ, ZORUNLU adımı ATLAR. (s.125-126)
- **İLKE-47:** Aşinalık tehlikeli bir aşırı özgüven ("home bias") yaratır — bir konuya daha aşina olmak, o konu hakkında ne kadar bildiğinizi ABARTMA eğiliminizi AZALTMAZ (Fischhoff araştırması); somut kanıt: bireysel yatırımcılar yerel telefon şirketi hissesinde diğer TÜM telefon şirketlerinin toplamının 3 KATI kadar pozisyon tutar; 401(k) sahiplerinin ortalama %25-30'u kendi İŞVERENİNİN hissesindedir. (s.126-127)
- **İLKE-48:** Otomatikleştirilmiş ("otopilot") bir portföy yürüten savunmacı bir yatırımcı, yılda İKİDEN fazla işlem yapıyorsa veya yatırımlarına ayda toplam 1-2 saatten FAZLA zaman harcıyorsa, bir şeyler YANLIŞ gidiyor demektir — internetin kolaylığı savunmacı yatırımcıyı aktif tacire DÖNÜŞTÜRMEMELİDİR. (s.129)
- **İLKE-49:** Bir çöküş BOYUNCA disiplinli, DÜZENLİ alım (tek seferlik büyük bir alım değil) sonucu kökten değiştirir — Ibbotson verisi: Eylül 1929 zirvesinde S&P 500'e yatırılan $12.000, 10 yıl sonra sadece $7.223'e düşmüştür; ama $100 başlangıç + AYNI on yıl boyunca her ay $100 eklemek, Büyük Buhran'ın TAMAMINDAN geçmesine rağmen $15.571'e ULAŞMIŞTIR. (s.130-131)

**Chapter 6 — Portfolio Policy for the Enterprising Investor: Negative Approach (Graham):**

- **İLKE-50:** Girişimci yatırımcının kural kitabı çoğunlukla NEGATİFTİR (bir "yapma" listesi): yüksek dereceli imtiyazlı hisseleri kurumsal alıcılara bırak; düşük dereceli tahvil/imtiyazlı hisseden GERÇEK bir pazarlık fiyatı OLMADIKÇA UZAK dur; yabancı devlet tahvilinden UZAK dur; TÜM yeni ihraçlara karşı TEDBİRLİ ol. (s.133-134)
- **İLKE-51:** İkinci-sınıf bir tahvil/imtiyazlı hisseyi PARİNE YAKIN (100'e yakın) fiyattan, sadece 1-2 puan ekstra getiri için almak "kötü iş"tir — anaparanın kaybı RİSKİNİ küçük bir gelir kazancı için kabul etmiş olursunuz; AYNI ihraç büyük bir İSKONTOYLA (örn. 70) alınırsa, riski dengeleyecek gerçek bir sermaye artışı POTANSİYELİ sunar. (s.137)
- **İLKE-52:** İkinci-sınıf üst-düzey menkul kıymetler 2 ÇELİŞKİLİ özelliği AYNI ANDA taşır: kötü piyasalarda NEREDEYSE HEPSİ ciddi fiyat düşüşü yaşar, ama BÜYÜK bir kısmı koşullar iyileştiğinde TAM olarak toparlanır (yıllarca ödenmemiş kümülatif imtiyazlı temettüler bile sonunda ödenebilir) — PAR fiyattan alım, dengeleyici yükseliş potansiyeli OLMADAN sadece düşüş riskini kilitler. (s.137)
- **İLKE-53:** TÜM yeni ihraçlar (IPO) 2 yapısal nedenle FAZLADAN şüpheyi hak eder: (1) arkalarında olağandışı güçlü SATIŞ baskısı vardır, (2) doğaları gereği koşulların SATICI (ihraççı/aracı kurum) için en elverişli olduğu zamanda satılırlar — bu MEKANİK olarak alıcı için DAHA AZ elverişli demektir. (s.139)
- **İLKE-54:** Küçük, belirsiz şirketlerin düşük-kaliteli IPO dalgasının, köklü ORTA-ölçekli şirketlerin geçerli fiyat seviyesinin ÜZERİNE çıkması, bir boğa piyasasının SONUNA yaklaşıldığının en GÜVENİLİR erken uyarı işaretlerinden biridir. (s.142)
- **İLKE-55:** Yabancı devlet tahvilleri, sakin zamanlarda getiri ne kadar cazip görünürse görünsün, kötü bir yatırım geçmişine sahiptir — çünkü sorun çıktığında alıcının alacağını zorla tahsil edecek YASAL veya PRATİK bir mekanizması YOKTUR. (s.138)

**Commentary on Chapter 6 (Zweig):**

- **İLKE-56:** Yüksek getirili ("junk") tahviller artık Graham döneminde olduğu kadar kategorik biçimde uygunsuz DEĞİLDİR — 130'dan fazla yatırım fonu artık ucuz çeşitlendirme sağlıyor (temerrüt riskini azaltıyor, TAMAMEN ortadan kaldırmıyor); ancak yüksek getirili İMTİYAZLI HİSSE için bu ucuz çeşitlendirme seçeneği hâlâ YOK, dolayısıyla Graham'ın ORİJİNAL itirazı BU kalemde geçerliliğini KORUYOR. Junk-bond fonu tahsisi, ancak ek gelire ihtiyaç duyan VE dalgalanmaya tahammül edebilen emeklilerin portföyünde KÜÇÜK, isteğe bağlı bir bileşen olmalıdır. (s.145-147)
- **İLKE-57:** Kısa vadeli alım-satım maliyetleri yıkıcı biçimde birikir: %4-8 gidiş-dönüş işlem maliyeti + uzun-vadeli sermaye kazancı yerine olağan gelir vergisi oranına tabi olma birleşince, TEK bir gidiş-dönüş işlemde BAŞA BAŞ gelmek için ~%10 kazanç gerekebilir. (s.149)
- **İLKE-58:** Ampirik kanıt (Barber & Odean, 66.000 aracı kurum hesabı, 1991-1996) işlem sıklığının NET yatırımcı getirisiyle TERS orantılı olduğunu doğrular: maliyet ÖNCESİ incelenen yatırımcılar piyasayı hafifçe geçmişken, en aktif işlem yapanlar (aylık >%20 devir) maliyet SONRASI piyasanın YILDA 6,4 puan ALTINDA kalmış; en sabırlı yatırımcılar (aylık %0,2 devir) maliyet sonrası bile piyasayı hafifçe geçmeye devam etmiştir. (s.149-150)
- **İLKE-59:** IPO yatırımı sıradan yatırımcı için SİSTEMATİK olarak zayıf performans gösterir — nedeni kazananların YOKLUĞU değil, (a) en büyük ilk-gün kazançlarının çoğunun halka açılmadan ÖNCE hisse alabilen kurumsal/içeriden yatırımcılar tarafından yakalanması, (b) IPO'yu ilk halka açık KAPANIŞ fiyatından alıp yıllarca tutmanın (1980-2001 ortalaması) piyasayı YILDA 23 puandan FAZLA geride bırakmasıdır. (s.151-152)

**Chapter 7 — Portfolio Policy for the Enterprising Investor: The Positive Side (Graham):**

- **İLKE-60:** F/K oranı, TEK bir yılın rakamına değil ÇOK-YILLI (Graham 7 yıl kullanır) ORTALAMA kazanca göre hesaplanmalıdır — HENÜZ KAZANILMAMIŞ "gelecek yıl kazancı" tahminine dayanarak değerleme yapmak (Wall Street'in yaygın pratiği), Graham/Zweig'e göre temelden SAKAT bir yöntemdir. (s.159)
- **İLKE-61:** Profesyonel yönetilen, büyümeye ODAKLANMIŞ yatırım fonları TARİHSEL olarak genel piyasayı YENMEMİŞTİR — Wiesenberger verisi: 120 "büyüme fonu" 1961-1970 on yılında ortalama %108 kazanç sağlarken S&P bileşik %105, DJIA %83 kazandı (neredeyse fark YOK); en zayıf 2 yılda (1969-70) fonların ÇOĞU her iki endeksten de KÖTÜ performans gösterdi. Profesyoneller bile büyüme hissesi seçiminde endeksi yenemiyorsa, sıradan yatırımcının bunu tek başına başarması BEKLENMEMELİDİR. (s.158-159)
- **İLKE-62:** "Nispeten gözden düşmüş büyük şirket" yaklaşımı — bir endeksin (örn. DJIA) en düşük F/K'li hisselerini alıp belirli bir süre elde tutmak — güçlü (ama kusursuz olmayan) bir tarihsel geçmişe sahiptir; işe yaramasının nedeni büyük şirketlerin (a) geçici sıkıntıdan kurtulacak sermaye/yönetim kaynağına sahip olması ve (b) iyileşme gösterildiğinde piyasanın makul hızda TEPKİ vermesidir. (s.163)
- **İLKE-63:** Düşük F/K çarpanı, DÖNGÜSEL/dalgalı kazançlı şirketler için TEK BAŞINA güvenilir bir pazarlık sinyali DEĞİLDİR — bu tür şirketler tam olarak EN KÖTÜ yıllarında (kazanç sıfıra yakınken, küçük bir kâr bile şişirilmiş bir F/K üretir) YÜKSEK çarpanla, EN İYİ yıllarında DÜŞÜK çarpanla satılır; tarama, fiyatın ÇOK-YILLI ortalama kazanca göre de düşük olmasını GEREKTİRMELİDİR. (s.165)
- **İLKE-64:** Gerçek bir "pazarlık" (bargain) menkul kıymeti, takdir edilen/gösterge DEĞERİN piyasa fiyatından EN AZ %50 FAZLA olmasını gerektirir — daha küçük bir fark Graham'ın çıtasını KARŞILAMAZ. (s.166)
- **İLKE-65:** Pazarlık fırsatları 2 geniş kaynaktan doğar: (1) GEÇİCİ olabilecek hayal kırıklığı yaratan güncel sonuçlar, (2) temel işle İLGİSİZ uzun süreli piyasa ilgisizliği/gözden düşme — ama HİÇBİRİ TEK BAŞINA alım için yeterli gerekçe DEĞİLDİR; yatırımcı ayrıca en az on yıllık İSTİKRARLI kazanç kanıtı (ZARAR yılı OLMAMALI) artı yeterli büyüklük/finansal güç ARAMALIDIR. (s.167-168)
- **İLKE-66:** En kolay tanımlanabilir pazarlık türü, şirketin NET İŞLETME SERMAYESİNİN (dönen varlıklar eksi imtiyazlı hisse ve uzun vadeli borç DAHİL TÜM yükümlülükler) ALTINDA satılan bir hissedir — alıcı sabit varlıklar veya şerefiye için HİÇBİR ŞEY ödemez. Graham'ın 1957 testinde 85 böyle "net-net" hisse, 2 yıl elde tutulduğunda toplamda %75 kazandı (S&P 425 Sanayi endeksi %50), HİÇBİR hisse ÖNEMLİ kayıp göstermedi. (s.169-170)
- **İLKE-67:** Küçük/"ikincil" (secondary) şirketler, yatırımcıların büyük/önde gelen isimlere yönelik tercihi nedeniyle SİSTEMATİK olarak DEĞERİNİN ALTINDA fiyatlanır — ama bu düzen SADECE gerçek bir indirimle (takdir değerinin ≤2/3'ü) alınırsa kârlı sömürülebilir, ASLA "tam" iş değerinden değil; girişimci yatırımcı bu yanlış fiyatlamadan 5 AYRI mekanizmayla kazanır: göreli yüksek temettü getirisi, fiyata göre önemli yeniden-yatırılan kazanç, boğa piyasalarının düşük fiyatlı hisseleri kayırması, durgun piyasalarda bile sürekli fiyat düzeltmesi, ve şirkete özgü düzeltici olaylar (yeni yönetim, birleşme). (s.170-173)
- **İLKE-68:** Savunmacı ile girişimci yatırımcı rolleri arasında GERÇEK bir "orta yol" YOKTUR — "yarım işadamı" olmaya çalışmak, yatırımcıya normal iş kârının "yarısını" HAK ETTİRMEZ; yatırımcı bir yolu BİLİNÇLİ olarak seçmeli ve o yolun TAM disiplinine bağlı kalmalıdır, ikisi arasında sürüklenmemelidir. (s.175-176)
- **İLKE-69:** Savunmacı yatırımcı ikincil (secondary) adi hisselerden FİYATTAN BAĞIMSIZ olarak KAÇINMALIDIR; girişimci yatırımcı bunları alabilir ama SADECE pazarlık fiyatından — asla sadece "adil" iş değerini yansıtan fiyattan, çünkü finansal tarih tam-değerden alınan ikincil hisselerin ortalama olarak tatmin edici sonuç VERMEDİĞİNİ gösterir. (s.176-177)
- **İLKE-70:** Özel durumlar/birleşme-arbitrajı ("workout") işlemleri, elverişli dönemlerde çekici, düşük riskli getiriler (tarihsel olarak ~%20+/yıl) sunabilir ama olağandışı uzmanlık/mizaç gerektirir ve daha fazla sermaye AYNI fırsatların peşine düştükçe GİDEREK daha az kârlı hale gelmiştir — sıradan girişimci yatırımcı için ANA akım bir öneri DEĞİLDİR. (s.174, Ch.1 s.33 ile çapraz referans)

**Commentary on Chapter 7 (Zweig):**

- **İLKE-71:** "En kötü günlerden kaçınarak" muazzam getiri gösteren piyasa-zamanlama çalışmaları istatistiksel bir YANILSAMADIR — HANGİ günlerin en kötü olacağını ÖNCEDEN kimse bilemez. Profesyonel piyasa-zamanlama bültenlerinin bile EN İYİ ondalık dilimi (Duke üniversitesi çalışması, 1991-1995) yıllık %12,6 getiri sağlarken, basit endeks fonu al-ve-tut stratejisi %16,4 getirdi. (s.179-180)
- **İLKE-72:** Büyüme hisseleri F/K oranı 25-30x'in ÇOK ÜZERİNE çıktığında TEHLİKELİ hale gelir — çünkü yüksek büyüme oranlarını uzun süre SÜRDÜRMEK aşırı NADİRDİR: Fortune 500'ün en büyük 150 şirketinden (1960-1999) sadece 8'i kazancını 2 TAM ONYIL boyunca yıllık ≥%15 büyütebildi; büyük ABD şirketlerinin sadece %10'u kazancını 5 yıl üst üste ≥%20 büyütebildi, 10 yıl için sadece %3'ü, 15 yıl üst üste için HİÇBİRİ. (s.181)
- **İLKE-73:** Büyük şirketler ORTALAMADAN DAHA HIZLI kazanç büyütmez — 1951-1998 dönemini kapsayan akademik bir çalışma, 10 yıllık dönemler genelinde net kazancın yıllık ortalama %9,7 büyüdüğünü, ama EN BÜYÜK %20'lik şirket diliminde bunun sadece %9,3 olduğunu (yani DAHA DÜŞÜK) buldu — "büyük ve köklü şirketler yüksek oranda büyümeye devam eder" varsayımını doğrudan ÇÜRÜTÜR. (s.183)
- **İLKE-74:** Yoğunlaşma ("tüm yumurtaları tek sepete koymak") EN ÇOK serveti YARATIR ama AYNI ZAMANDA en büyük finansal FELAKETLERİ de yaratır — 1982 Forbes 400 listesindeki en zenginlerin sadece %16'sı (400'de 64) 20 yıl sonra (2002) hâlâ listedeydi, oysa listede kalmak için piyasa ortalamasının (%13,2/yıl) çok ALTINDA, sadece %4,5/yıl yeterliydi; listeden düşenler serveti YARATAN TEK sektöre/şirkete aşırı yoğunlaşmayı SÜRDÜRDÜLER. (s.185)
- **İLKE-75:** Pratik pazarlık-avcılığı yöntemi (Zweig'in Graham'ın net-net metodunu güncellemesi): 52-haftalık yeni-dip listelerini tara, dönen varlıklar eksi TÜM yükümlülükleri (imtiyazlı hisse + uzun vadeli borç dahil) hesapla ve piyasa değeriyle KIYASLA — bu rakamın ALTINDA/EŞİT fiyatlanan bir hisse, piyasanın operasyonel İŞİ neredeyse SIFIR ya da NEGATİF değerlediği anlamına gelir. (s.186)
- **İLKE-76:** Kendi ülkene yoğunlaşmak (home-country concentration) KENDİ BAŞINA telafisiz bir risktir — yaşadığı, çalıştığı ve maaş aldığı ülkede yatırımcı ZATEN çok katmanlı bir yerel bahis yapmaktadır; hisse portföyünün ÜÇTE BİRİNE kadarını yabancı piyasalara (gelişmekte olan piyasalar dahil) ayırmak, ana piyasanın uzun süre kötü performans göstermesi riskine karşı MANTIKLI bir çeşitlendirmedir. (s.187)

**Chapter 8 — The Investor and Market Fluctuations (Graham):**

- **İLKE-77:** Piyasa dalgalanmalarından kazanmanın 2 yolu vardır: ZAMANLAMA (piyasanın gelecekteki yönünü TAHMİN etmeye çalışmak) ve FİYATLAMA (adil değerin ALTINDA alıp ÜSTÜNDE satmak). Graham NET biçimde belirtir: zamanlamaya/tahmine ağırlık veren bir yatırımcı SONUNDA bir SPEKÜLATÖR haline gelir ve spekülatörün sonuçlarını alır; fiyatlama, GERÇEK yatırımla UYUMLU TEK yaklaşımdır. (s.189)
- **İLKE-78:** GENİŞ popülerlik kazanan HERHANGİ bir tahmin/işlem formülü, TAM DA o popülerlik NEDENİYLE güvenilirliğini KAYBETME eğilimindedir — Ch.1'de görülen AYNI kendini-yok-eden mekanizma; Dow Teorisi'nin kendi kaydı bunu DOĞRUDAN doğrular: 1897-1938 arası neredeyse KESİNTİSİZ başarı (1929 zirvesini 306'da doğru sattı, 1933 dibine [84] kadar takipçilerini dışarıda tuttu), ama SONRAKİ ~30 yıl boyunca basit al-ve-tut DJIA stratejisi teoriyi GEÇTİ. (s.191-192)
- **İLKE-79:** Bir şirketin işi NE KADAR İYİ ve başarılıysa, hissesinin fiyatı O KADAR ÇOK piyasanın DEĞİŞKEN ruh haline bağımlı hale gelir (defter değeri üzerindeki büyük primin bilançoda daha az "çapası" olur) — bu, PARADOKSAL biçimde, YÜKSEK-kaliteli işlerin genellikle SIRADAN işlerden DAHA SPEKÜLATİF/DALGALI hisseler ürettiği anlamına gelir. (s.198-199)
- **İLKE-80:** Muhafazakar yatırımcı için pratik bir ÇAPA: alımları, maddi varlık (defter) değerinin YAKLAŞIK ÜÇTE BİRİNDEN fazla PRİM taşımayan hisselerde YOĞUNLAŞTIR — bu, piyasanın ruh halinden BAĞIMSIZ, bilanço-temelli bir TABAN sağlar; ama tek başına yeterli DEĞİLDİR, tatmin edici bir kazanç/fiyat oranı, güçlü mali yapı ve makul kazanç istikrarıyla BİRLİKTE aranmalıdır. (s.199-200)
- **İLKE-81:** "Bay Piyasa" (Mr. Market) alegorisi — Zweig'e göre kitabın EN ÖNEMLİ tek kavramı: manik-depresif bir iş ortağınız her gün gelip payınızı almayı VEYA size ek pay satmayı teklif eder, fiyatı ruh haline göre makul ile saçma arasında değişir; akıllı yatırımcı SADECE kendi çıkarına hizmet ettiğinde onunla işlem yapmakta ÖZGÜRDÜR, diğer zamanlarda onu TAMAMEN görmezden gelebilir — teklifleri SİZİN kolaylığınız içindir, TALİMAT değildir. (s.204-205)
- **İLKE-82:** Gerçek yatırımcı NEREDEYSE HİÇBİR ZAMAN satmaya ZORLANMAZ ve diğer tüm zamanlarda güncel fiyat teklifini GÖRMEZDEN GELMEKTE özgürdür — "haksız piyasa düşüşlerinden PANİKLENEN veya HAKSIZ YERE endişelenen" bir yatırımcı, kendi TEMEL AVANTAJINI (zorunlu satışa maruz kalmama) tersine çevirip bir DEZAVANTAJA dönüştürür. (s.203)
- **İLKE-83:** Boğa piyasaları tarihsel olarak 5 tanınabilir uyarı özelliğini AYNI ANDA taşır: (1) tarihsel olarak yüksek fiyat seviyesi, (2) yüksek F/K oranları, (3) tahvil getirisine göre DÜŞÜK temettü getirisi, (4) yoğun marjla spekülasyon, (5) çok sayıda DÜŞÜK kaliteli yeni adi hisse ihracı. (s.193)
- **İLKE-84:** Teknik olarak "güvenli" (temerrüde düşmeyen) uzun vadeli bir tahvil bile, SADECE piyasa faiz oranlarındaki değişiklikten kaynaklanan BÜYÜK fiyat dalgalanmaları yaşayabilir — bu, kredi/temerrüt riskinden FARKLI bir risktir ve en yüksek dereceli ihraçlarda bile geçerlidir; vade UZADIKÇA dalgalanma BÜYÜR. (s.207-208)
- **İLKE-85:** İş kalitesi ile borsa DAVRANIŞI AYNI eksen DEĞİLDİR — bir şirketin operasyonel performansı finansal tablolardan değerlendirilir; hissesinin DALGALANMASI o performansın ÜZERİNE binen DEĞİŞKEN kalabalık psikolojisini yansıtır. Bu ikisini KARIŞTIRMAK (fiyat düşüşünü iş bozulmasının KANITI, fiyat yükselişini iş iyileşmesinin KANITI sanmak) tüm bölümün DÜZELTMEYE çalıştığı TEMEL hatadır. (s.194-196, Özet s.205-206)

**Commentary on Chapter 8 (Zweig):**

- **İLKE-86:** Inktomi Corp vaka analizi Bay Piyasa'nın TAM genliğini gösterir: Mart 2000 zirvesinde $25 milyar değerlenmiş (yıllık gelirinin 250 katı) — şirket TARİHİNDE HİÇBİR ZAMAN kâr etmemişken; 30 ay sonra $40 milyonun ALTINDA değerlendi (gelirinin 0,35 katı) — oysa ALTTAKİ İŞİN geliri bu süreçte ARTMIŞTI. Sadece piyasanın RUH HALİ değişmişti. Yahoo!, şirketi sonrasında bir önceki fiyatın yaklaşık 7 KATINA satın aldı. (s.214)
- **İLKE-87:** Toplu yatırımcı davranışı fiyatla AYNI YÖNDE hareket eder, TERSİ değil — ortalama 401(k) katkı oranı 1999'da (boğa piyasası zirvesi) %8,6 iken, 2002'de (ayı piyasası dibi) %7'ye DÜŞTÜ — çoğu insanın pahalıyken DAHA FAZLA, ucuzken DAHA AZ aldığının doğrudan davranışsal kanıtıdır — Graham'ın önerdiğinin TAM TERSİ. (s.215)
- **İLKE-88:** Akıllı yatırımcı enerjisini SADECE GERÇEKTEN KONTROL EDİLEBİLİR olana odaklamalıdır: işlem/aracılık maliyetleri, fon sahiplik maliyetleri, kendi getiri beklentilerinin GERÇEKÇİLİĞİ, pozisyon büyüklüğü/çeşitlendirme/dengeleme riski, vergi zamanlaması (≥1 yıl, tercihen ≥5 yıl elde tutmak) ve HEPSİNDEN ÖNEMLİSİ kendi DAVRANIŞI — piyasanın bir sonraki hareketi hakkında HİÇBİR ŞEY kontrol edilemez, o yönde harcanan çaba büyük ölçüde BOŞADIR. (s.219)
- **İLKE-89:** Kayıp-karşıtlığı (loss aversion) nörolojik olarak ASİMETRİKTİR: eşit büyüklükteki bir finansal kaybın ACISI (Kahneman/Tversky), eşdeğer bir kazancın HAZZINDAN 2 KATTAN FAZLA yoğundur — bu asimetri, piyasa diplerinde PANİK-SATIŞIN kök davranışsal NEDENİDİR. (s.221)
- **İLKE-90:** Yüzde-çerçeveleme disiplini: büyük görünen MUTLAK bir piyasa hareketi başlığını ("Dow 700 puan düştü") tepki vermeden ÖNCE YÜZDEYE çevir — Dow 8.000 seviyesindeyken 700 puanlık düşüş sadece %1,2'dir, sıradan bir günlük sıcaklık değişimiyle KIYASLANABİLİR; yüzde bağlamı OLMADAN verilen puan-toplamı başlıkları RUTİN bir panik kaynağıdır. (s.221)
- **İLKE-91:** Yatırımları DAHA SIK izlemek DAHA İYİ değil DAHA KÖTÜ sonuç üretir — kontrollü bir çalışma (Paul Andreassen), hisseleri hakkında SIK haber güncellemesi alan yatırımcıların, HİÇ güncelleme almayanlara göre AYNI dönemde sadece YARISI kadar getiri elde ettiğini bulmuştur. (s.223)
- **İLKE-92:** Yazılı, imzalı, ÖNCEDEN TAAHHÜT EDİLMİŞ bir yatırım planı ("Yatırım Sahipliği Sözleşmesi") — sabit aylık dolar-maliyet-ortalaması tutarı, isimlendirilmiş fonlar, minimum 10 yıllık elde tutma taahhüdü VE SADECE gerçek acil durumlar/önceden planlanmış büyük harcamalar için İSTİSNA — bölümün belgelediği TAM DA o "pahalıyken al/ucuzken sat" dürtülerine karşı DAVRANIŞSAL bir ÖN-TAAHHÜT mekanizması olarak işlev görür. (s.225)

---

## Formüller

| # | Formül | QuaxisLabs karşılığı |
|---|---|---|
| **FORMÜL-08** Savunmacı Yatırımcı Fiyat Tavanı: Fiyat ≤ 25× (son 7 yıl ort. kazanç) VE Fiyat ≤ 20× (son 12 ay kazanç) (s.114-115) | **KISMEN MEVCUT/TÜRETİLEBİLİR.** TTM bazlı `pe_ratio` (`calculator.py`, satır 821/851) zaten hesaplanıyor — bu FORMÜL'ün "≤20× TTM" ayağı doğrudan uygulanabilir. Ancak "≤25× son-7-yıl-ortalama" ayağı için gereken çok-yıllı EPS serisi YOK (`trends.py` 12 çeyrek/~3 yıl sınırlı) — Kısım 1'de FORMÜL-05'te tespit edilenle AYNI kök veri açığı, 4. tekrar. |
| **FORMÜL-09** Büyüme Hissesi Eşiği (Rule of 72): EPS'nin 10 yılda 2 katına çıkması ≈ yıllık bileşik %7,1 büyüme (s.114-115) | **KISMEN MEVCUT.** Rule-of-72 basit aritmetik (kod gerekmez); ama yıllık EPS büyüme oranını hesaplamak için gereken çok-yıllı EPS serisi YOK (aynı `trends.py` kısıtı — FORMÜL-08 ile AYNI açık). |
| **FORMÜL-10** Muhafazakar Finansman Testi: Adi Hisse (defter değeri) ≥ %50 Toplam Sermayelendirme (sanayi şirketi) veya ≥ %30 (demiryolu/kamu hizmeti) (s.122) | **KISMEN MEVCUT/TÜRETİLEBİLİR.** `equity` ve `financial_debt` (`calculator.py`) mevcut; Toplam Sermayelendirme ≈ `equity + financial_debt` (imtiyazlı hisse alt kalemi hariç, o alan sistemde YOK) olarak yaklaşık TÜRETİLEBİLİR — doğrudan hesaplanmıyor, ORTA maliyetli ekleme. |
| **FORMÜL-11** "Büyük Şirket" Eşiği (Zweig güncellemesi, 2003 ABD): Piyasa değeri ≥ $10 milyar (s.123, Zweig dipnotu) | **MEVCUT (eşik hariç).** `market_cap` zaten hesaplanıyor (`valuation.py`, `price * share_capital`) — sadece mutlak dolar eşiği ETİKETİ eklenmemiş; ABD-spesifik eşik BIST/kripto evrenine DOĞRUDAN taşınamaz, yerel kalibrasyon (TL/USD bazında) gerekir. |
| **FORMÜL-12** Net İşletme Sermayesi / "Net-Net" Bargain Testi: Piyasa Değeri < (Dönen Varlıklar − Toplam Yükümlülükler [imtiyazlı hisse + uzun vadeli borç DAHİL]) — Kısım 1 FORMÜL-01'in Ch.7'de KESİN tanımı (s.169-170, Zweig güncel yöntemi s.186) | **KISMEN MEVCUT/TÜRETİLEBİLİR — Kısım 1 FORMÜL-01 ile AYNI durum.** Bu turda kesin tanım TEYİT edildi: imtiyazlı hisse de yükümlülük sayılmalı, ama bu alt kalem QuaxisLabs'ta ayrı bir alan olarak YOK (sadece toplam `equity` var) — hafif ek belirsizlik. |
| **FORMÜL-13** Düşük-Çarpanlı DJIA Stratejisi ("Dogs of the Dow" öncülü): Endeksin en düşük F/K'li 6-10 hissesini yıllık olarak al/elde tut/yeniden seç (s.163-164) | **KAPSAM DIŞI (portföy-seviyesi endeks-içi rotasyon stratejisi)** — Kısım 1 FORMÜL-06 ile AYNI mantık kategorisi, QuaxisLabs tekil varlık analiz motoru kapsamı DIŞINDA. Ancak ALT bileşeni (tekil hisse F/K sıralaması) ham veri olarak (`pe_ratio`) zaten MEVCUT — bir tarama/filtre özelliği olarak ayrıca değerlendirilebilir. |
| **FORMÜL-14** Gerçek "Pazarlık" (Bargain) Eşiği: Takdir Edilen Değer ≥ Piyasa Fiyatının 1,5 katı (%50+ marj) (s.166) | **KISMEN MEVCUT/TÜRETİLEBİLİR.** `graham_fair_value_price` (`valuation.py`, Graham Sayısı yöntemiyle: F/K×PD/DD≤22,5) ZATEN hesaplanıyor; bu makul değerin güncel fiyatın ≥1,5 katı olup OLMADIĞINI etiketleyen ek bir "derin pazarlık" rozeti eklenebilir — ham veri hazır, DÜŞÜK maliyetli. |
| **FORMÜL-15** Döngüsel Kazanç Kırılganlık Testi: F/K'yi TEK yıllık kazanca göre değil, EN AZ 10 yıllık kazanç serisine göre (sıfır-zarar-yılı koşuluyla) hesapla (s.167-168) | **VERİ EKSİK.** Yine 10+ yıllık kazanç serisi sorunu — kitap boyunca (2 kitap toplamda) tekrar eden AYNI kök kısıt, bu turda 4. kez ortaya çıktı. |
| **FORMÜL-16** İşlem Maliyeti Başabaş Eşiği: Gidiş-dönüş işlem maliyeti (%4-8) + normal-gelir vergi farkı nedeniyle kısa vadeli alım-satımda başabaş için gereken minimum kazanç ≈ %10 (s.149, Zweig) | **KAPSAM DIŞI (zaten AYRI bir altyapı olarak MEVCUT).** QuaxisLabs bir backtesting motoru olarak ZATEN TCA (transaction cost analysis) parametrelerine sahiptir (`TCAParams` dataclass, `DEFAULT_TCA` dict — bkz. proje `CLAUDE.md`); bu formül, o mevcut altyapının KAVRAMSAL karşılığıdır, yeni bir veri alanı GEREKTİRMEZ. |
| **FORMÜL-17** Muhafazakar Alım Ölçütü (Ch.8): Fiyat ≤ Defter Değeri (Maddi Varlık Değeri) × 1,33 (yaklaşık %33 prim tavanı) (s.199-200) | **MEVCUT/TÜRETİLEBİLİR.** `pb_ratio` (`calculator.py`, piyasa değeri/güncel özkaynak) ZATEN hesaplanıyor — sadece ≤1,33 eşik ETİKETLEME mantığının `valuation.py`'ye eklenmesi gerekiyor; ham veri TAMAMEN hazır, F/K sınıflandırması (FORMÜL-02) ile AYNI düşük-maliyet kategorisinde. |

---

## Eşikler (tablo)

| Gösterge | Eşik / Aralık | Yorum | Kaynak | Sayfa |
|---|---|---|---|---|
| Çeşitlendirme (savunmacı yatırımcı) | Min 10 — Maks ~30 hisse | Yeterli ama aşırıya kaçmayan çeşitlendirme | Graham, Ch.5 | s.114 |
| Temettü geçmişi (Graham orijinal, 1972) | En az 1950'den beri KESİNTİSİZ | Savunmacı yatırımcı için zorunlu kural | Graham, Ch.5 | s.114-115 |
| Temettü geçmişi (Zweig güncel, 2003) | En az 10 yıl kesintisiz, tercihen 20 yıl | S&P500'de 2002 sonu itibariyle 255 şirket bu standardı karşılıyordu | Zweig, Ch.5 fn | s.115 |
| Fiyat/Kazanç sınırı (savunmacı) | ≤25× son 7 yıl ort. kazanç VE ≤20× son 12 ay kazanç | Büyüme hisselerinin ÇOĞUNU dışlar | Graham, Ch.5 | s.114-115 |
| Büyüme hissesi tanımı | EPS 10 yılda 2 katına (~%7,1/yıl bileşik) | Rule of 72 uygulaması | Graham, Ch.5 | s.114-115 |
| Muhafazakar finansman (sanayi şirketi) | Adi hisse (defter) ≥ toplam sermayenin %50'si | Konservatif kabul edilme eşiği | Graham, Ch.5 | s.122 |
| Muhafazakar finansman (demiryolu/kamu hizmeti) | Adi hisse (defter) ≥ toplam sermayenin %30'u | Sektöre özgü daha düşük eşik | Graham, Ch.5 | s.122 |
| "Büyük" şirket eşiği (1972) | $50 milyon varlık VEYA ciro | Dönem-özel, güncellenmeli | Graham, Ch.5 | s.123 |
| "Büyük" şirket eşiği (2003, Zweig) | Piyasa değeri ≥ $10 milyar | ~300 ABD hissesi bu bandı karşılıyordu | Zweig, Ch.5 fn | s.123 |
| Gerçek pazarlık eşiği | Takdir değeri ≥ piyasa fiyatının 1,5 katı | Graham'ın "true bargain" çıtası | Graham, Ch.7 | s.166 |
| Muhafazakar alım tavanı (defter değeri primi) | Fiyat ≤ defter değerinin ~1,33 katı | Bilanço-temelli bağımsız bir taban sağlar | Graham, Ch.8 | s.199-200 |
| Büyüme hissesi tehlike bölgesi | P/E > 25-30× | Sürdürülemez büyüme varsayımı riski | Zweig, Comm.7 | s.181 |
| %15+ kazanç büyümesini 20 yıl sürdürme oranı | Fortune 500'ün en büyük 150'sinde sadece 8/150 (%5,3) | 1960-1999 dönemi | Zweig, Comm.7 | s.181 |
| %20+ kazanç büyümesini 5/10/15 yıl sürdürme oranı | Büyük ABD şirketlerinin %10 / %3 / %0'ı | 5 on yıllık dönem verisi (Sanford Bernstein) | Zweig, Comm.7 | s.181 |
| İkincil (secondary) hisse alım eşiği (girişimci yatırımcı) | ≤ takdir değerinin 2/3'ü | Asla "tam" değerden alınmamalı | Graham, Ch.7 | s.176-177 |
| İkinci-sınıf tahvil/imtiyazlı hisse indirim eşiği | Parin en az %30 ALTI (yüksek kuponlu ihraçlarda) | Bargain kabul edilme koşulu | Graham, Ch.6 | s.133 |
| İşlem maliyeti başabaş eşiği (day-trading) | Gidiş-dönüş ~%10 gerekli kazanç | Maliyet+vergi birleşimi | Zweig, Comm.6 | s.149 |
| Junk bond tarihsel temerrüt oranı | 1978'den beri yıllık ortalama %4,4 | Buna rağmen net getiri %10,5/yıl (10yıllık Hazine: %8,6) | Zweig, Comm.6 | s.146-147 |
| Yabancı hisse tahsis önerisi | Portföyün ≤1/3'ü | Ana ülke riskine karşı çeşitlendirme | Zweig, Comm.7 | s.187 |
| Piyasa çevrimi tarihsel normu (1897-1949, 10 tam çevrim) | Yükseliş +%44 ila +%500 (çoğu %50-100); düşüş -%24 ila -%89 (çoğu %40-50) | Bir çevrimin tipik genliği | Graham, Ch.8 | s.192 |
| Beklenen dalgalanma normu (5 yıllık ufuk) | Elde tutulan hisselerin çoğu dipten ≥%50 yükseliş VE zirveden ≥%33 düşüş yaşar | "Yatırımcı" sayılmanın ön koşulu (Zweig) | Zweig, Ch.8 fn | s.196 |
| Kayıp-kazanç asimetrisi | Eşit büyüklükte kaybın acısı, kazancın hazzından >2 kat yoğun | Kahneman/Tversky bulgusu, panik-satışın kökeni | Zweig, Comm.8 | s.221 |
| Yüzde-çerçeveleme örneği | "Dow 700 puan düştü" = Dow 8.000'de sadece %1,2 | Mutlak sayı başlıkları yanıltıcı | Zweig, Comm.8 | s.221 |
| Vergi zararı mahsubu (ABD, 2003) | Gerçekleşen zararlar yıllık $3.000'a kadar olağan gelirden düşülebilir | Dönem/ülke-özel, TR'ye doğrudan taşınamaz | Zweig, Comm.8 | s.224 |

---

## Kontrol Listeleri

**KONTROL E — Savunmacı Yatırımcı Hisse Seçim Kontrolü (Ch.5, 5 madde):**
1. Portföyümde en az 10, en fazla ~30 farklı hisse var mı (yeterli ama aşırı olmayan çeşitlendirme)?
2. Seçtiğim her şirket büyük, önde gelen VE muhafazakar finanse edilmiş mi (adi hisse defter değeri toplam sermayenin ≥%50'si [sanayi] / ≥%30'u [demiryolu-kamu hizmeti])?
3. Her şirketin uzun, KESİNTİSİZ temettü ödeme geçmişi var mı (en az 10, tercihen 20 yıl)?
4. Fiyat, son 7 yıl ortalama kazancın 25 katını VE son 12 ay kazancın 20 katını AŞMIYOR mu?
5. Bu kriterler "büyüme hissesi" kategorisinin çoğunu ELEDİ mi — bu BİLİNÇLİ bir dışlama mı, yoksa yanlışlıkla mı oldu?

**KONTROL F — Girişimci Yatırımcı "Negatif Kurallar" Kontrolü (Ch.6, 5 madde):**
1. Yüksek dereceli imtiyazlı hisseyi kurumsal alıcılara mı bırakıyorum (kendim almıyor muyum)?
2. Aldığım ikinci-sınıf tahvil/imtiyazlı hisse gerçek bir İNDİRİMLE mi (parin en az %30 altı), yoksa yalnızca yüksek getiri için mi ("işadamı yatırımı" tuzağı)?
3. Yabancı devlet tahvili alırken, getiri ne kadar cazip olursa olsun bu kategoriden UZAK duruyor muyum?
4. Yeni bir halka arza (IPO) girerken hem satış baskısını HEM DE ihraççı lehine fiyatlama koşulunu göz önünde bulunduruyor muyum?
5. Piyasada küçük/belirsiz şirketlerin IPO'ları köklü orta-ölçekli şirketlerden PAHALI fiyatlanıyor mu (boğa piyasası sonu sinyali)?

**KONTROL G — Bargain/Pazarlık Hissesi Tespit Kontrolü (Ch.7, 5 madde):**
1. Takdir ettiğim değer, piyasa fiyatının en az 1,5 katı mı (gerçek pazarlık eşiği)?
2. Şirketin son 10+ yılda ZARAR yılı YOK mu (kazanç istikrarı testi)?
3. Düşük F/K'nin, döngüsel bir şirketin en İYİ yılında mı yoksa yapısal olarak ucuz bir şirkette mi ortaya çıktığını ayırt ettim mi?
4. Bu ikincil/gözden düşmüş bir şirketse, takdir değerinin EN FAZLA 2/3'ü fiyattan mı alıyorum (tam değerden ASLA)?
5. Net İşletme Sermayesi (dönen varlıklar − TÜM yükümlülükler) piyasa değerinden BÜYÜK mü ("net-net" testi)?

**KONTROL H — Mr. Market Davranışsal Disiplin Kontrolü (Ch.8 + Comm.8, 6 madde):**
1. Bugün Mr. Market ile işlem yapmam KENDİ çıkarıma mı hizmet ediyor, yoksa onun teklifine mi tepki veriyorum?
2. Portföyümü ne sıklıkla kontrol ediyorum — bu sıklık bana FAYDA mı, yoksa fazladan kaygı mı sağlıyor (sık kontrol = düşük getiri kanıtı)?
3. Piyasa haberindeki büyük "puan" düşüşünü YÜZDEYE çevirdim mi (mutlak sayı beni yanıltıyor mu)?
4. Elimdeki hisseyi SADECE fiyatı düştüğü için satmayı, SADECE yükseldiği için almayı düşünüyor muyum?
5. Kontrol edebileceğim şeylere (maliyet, vergi zamanlaması, risk boyutu, kendi davranışım) mi odaklanıyorum, yoksa piyasanın bir sonraki hareketini TAHMİN etmeye mi çalışıyorum?
6. Yazılı, imzalı bir yatırım taahhüdüm (otomatik aylık tutar + minimum 10 yıl elde tutma + istisnalar) var mı?

---

## Kırmızı Bayraklar

- **BAYRAK-12:** Gerçek anlamda "büyük, önde gelen, muhafazakar finanse edilmiş, kesintisiz temettü ödeyen" olmayan bir hisseyi "savunmacı" bir portföye dahil etmek. (Ch.5, s.114)
- **BAYRAK-13:** "İşadamı yatırımı" tuzağı — sadece 1-2 puan ekstra yıllık gelir için, anaparanın önemli bir kısmının kaybedilmesi RİSKİNİ kabul etmek. (Ch.6, s.136-137)
- **BAYRAK-14:** Yabancı devlet tahvili almak — getiri ne kadar cazip görünürse görünsün, sorun çıktığında yasal tahsil mekanizması YOKTUR. (Ch.6, s.138)
- **BAYRAK-15:** Yeni halka arz (IPO) dalgasının hızlanması, küçük/belirsiz şirketlerin fiyatlarının köklü orta-ölçekli şirketlerin ÜZERİNE çıkması — boğa piyasasının sonuna yaklaşıldığının GÜVENİLİR bir işareti. (Ch.6, s.142)
- **BAYRAK-16:** Bir şirket yönetiminin "büyüme oranımızı sürdürebileceğiz, hatta hızlandırabileceğiz" iddiasını çok yüksek bir F/K (>80-120×) ile birleştirmesi — Nortel/Cisco 2000 örnekleri, sonrasında iş çöktü. (Comm.7, s.184)
- **BAYRAK-17:** Portföyün TAMAMININ tek bir sektöre/şirkete (kendi işvereniniz dahil) yoğunlaştırılması — Forbes 400 örneği: 1982 listesindeki 400 kişiden sadece 64'ü (%16) 2002'de hâlâ listede, hepsi de TEK sektöre aşırı yoğunlaşma yüzünden düştü. (Comm.7, s.185)
- **BAYRAK-18:** Aylık portföy devir oranı %20'yi aşan aşırı aktif alım-satım — bu davranış tarihsel olarak piyasa getirisinin altında kalmayla (-6,4 puan/yıl) doğrudan ilişkilidir. (Comm.6, s.149-150)
- **BAYRAK-19:** IPO'yu ilk halka arz FİYATINDAN değil, halka açıldıktan SONRAKİ (genellikle çok daha yüksek) kapanış fiyatından almak — VA Linux örneği: $30 arz fiyatı, gün içi $320 zirve, 3 yıl sonra $1,19. (Comm.6, s.151-153)
- **BAYRAK-20:** Bir formülün/stratejinin (Dow Teorisi, formül-yatırım planları) YAYGINLAŞMASINDAN HEMEN SONRA performansının bozulması — popülerlik arttıkça güvenilirlik azalır kalıbının Ch.8'de ÜÇÜNCÜ kez doğrulanması. (Ch.8, s.191-195)
- **BAYRAK-21:** Piyasa fiyatındaki geçici bir düşüşü, şirketin İÇSEL DEĞERİNDE bir düşüş olarak yanlış yorumlayıp panikle satmak — Mr. Market'in teklifini KENDİ yargınızın yerine koymak. (Ch.8, s.203-205)
- **BAYRAK-22:** Portföyü günde birden çok kez kontrol etmek — ampirik kanıt (Andreassen çalışması) bunun getiriyi YARIYA düşürdüğünü gösteriyor. (Comm.8, s.223)
- **BAYRAK-23:** Boğa piyasasında (fiyatlar pahalıyken) katkı/alım oranını ARTIRMAK, ayı piyasasında (fiyatlar ucuzken) AZALTMAK — 401(k) katkı oranı verisi (1999: %8,6 → 2002: %7) bu tam tersi-mantıklı davranışın YAYGIN olduğunu kanıtlıyor. (Comm.8, s.215)

---

## Uygulama Notları

1. **Bu kısım kitabın İLK somut sayısal seçim kriterleri bloğudur** (koordinatörün öngördüğü gibi) — Ch.5'in 4 kuralı ve Ch.7'nin bargain/net-net testleri, Ch.14-15'te (Kısım 4) muhtemelen YENİDEN ele alınıp GENİŞLETİLECEK; bu kısımdaki FORMÜL-08/12/14/15 numaralı kalemler o turda ÇAPRAZ REFERANSLA güncellenmeli.
2. **En sık tekrarlanan veri açığı (4. tekrar, artık kitaplar-arası bir ÖRÜNTÜ):** "10+ yıllık kazanç/EPS serisi" eksikliği — hem savunmacı yatırımcının fiyat tavanı (FORMÜL-08) hem büyüme oranı hesaplaması (FORMÜL-09) hem döngüsel kazanç testi (FORMÜL-15) hem de Kısım 1'in Shiller CAPE'i (FORMÜL-05) AYNI `trends.py` 12-çeyrek sınırına TAKILIYOR. Bu artık QuaxisLabs'ın EN YÜKSEK öncelikli YAPISAL eksikliği olarak değerlendirilmeli (tekil alan eklemekten farklı, `trends.py`'nin veri tutma ufkunun GENİŞLETİLMESİNİ gerektirir).
3. **İki DÜŞÜK maliyetli, YÜKSEK değerli kazanım bu turda netleşti:** (a) F/K sınıflandırması (Kısım1 FORMÜL-02, <10/10-20/>20) VE (b) PD/DD tavanı (bu tur FORMÜL-17, ≤1,33×) — HER İKİSİ de mevcut `pe_ratio`/`pb_ratio` alanlarına sadece bir eşik-etiketleme katmanı eklemekle YETİNİYOR, sıfır yeni veri çekme gerektiriyor. Bu ikisi TEK bir PR'da BİRLİKTE eklenebilir.
4. **QuaxisLabs kapsam sınırı bu turda 2 KEZ daha doğrulandı:** FORMÜL-13 (Dogs of the Dow tarzı endeks-içi rotasyon) ve — kısmen — FORMÜL-06'nın (Kısım1, %50-50 dengeleme) mantığıyla AYNI kategori: bunlar PORTFÖY-seviyesi/çok-varlıklı stratejilerdir, QuaxisLabs'ın TEKİL varlık analiz kapsamının DIŞINDADIR. FORMÜL-16 (işlem maliyeti başabaş eşiği) ise TERSİ bir durum: zaten AYRI bir modülde (`TCAParams`/`DEFAULT_TCA`) karşılığı VAR, bu nedenle YENİ bir ekleme GEREKTİRMİYOR — sadece kavramsal doğrulama olarak not düşüldü.
5. **Temettü verisi eksikliği** (Kısım 1'den beri bilinen açık) bu turda YENİ bir bağlamda ortaya çıktı: Ch.5'in 3. kuralı (kesintisiz temettü geçmişi, min 10-20 yıl) ve Ch.5'in dividend-reinvestment-getiri örneği (İLKE-39) — TEMETTÜ ekseni artık kitap genelinde (3. kez, farklı bölümlerde) EN ÇOK vurgulanan TEKİL eksik alan konumuna yükseldi.
6. **NCAV/net-net formülü artık YÜKSEK öncelikli:** Kısım 1'de "ORTA öncelikli" olarak not düşülmüştü; bu turda Ch.7'nin merkezi bargain kriteri olduğu (İLKE-64, 66) VE Zweig'in kendi pratik tarama yönteminde (İLKE-75) doğrudan kullanıldığı TEYİT edildi — Kısım 4 (Ch.14-15) işlendiğinde bu formülün öncelik SIRASI yeniden değerlendirilmeli, muhtemelen YÜKSELECEK.
7. **Tarihsel/dönem-özel sayılar** (1972 tahvil oranları, 2002-2003 fon getirileri, ABD Forbes 400/vergi eşikleri) yine DOĞRUDAN eşik olarak KULLANILMADI — sadece METODOLOJİ/büyüklük-mertebesi (order-of-magnitude) referansı olarak değerlendirildi.
8. **OCR ile ilgili not:** Bu turda TEK bir kalıcı belirsizlik kaldı — Table 7-3 (Chrysler EPS/fiyat, 1952-1970) satır-bazlı rakamları (özellikle 1958 "L 44?" ve 1968 "24.92°"/"H 294°" değerleri) net OKUNAMADI; bu tablo hiçbir EŞİK/FORMÜL kaynağı olarak KULLANILMADI, sadece "döngüsel şirketlerde düşük F/K en kötü yılda değil en iyi yılda görülür" ilkesinin (İLKE-63) DESTEKLEYİCİ örneği olarak metinsel biçimde anıldı — rakamsal teyit GEREKMEDİĞİ için "(OCR belirsiz)" işareti bir EŞİK satırına YANSITILMADI.
