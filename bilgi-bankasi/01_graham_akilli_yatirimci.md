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

---
---

# Kısım 3: Bölüm 9-13 (Chapter 9-13 + Commentary, kitap s.226-346, PDF index 239-359)

## İşlenen bölümler (bu ana kısım)
- Ch.9 Investing in Investment Funds (s.226-241)
- Commentary on Chapter 9 (s.242-256)
- Ch.10 The Investor and His Advisers (s.257-271)
- Commentary on Chapter 10 (s.272-279)
- Ch.11 Security Analysis for the Lay Investor: General Approach (s.280-301)
- Commentary on Chapter 11 (s.302-309)
- Ch.12 Things to Consider About Per-Share Earnings (s.310-321)
- Commentary on Chapter 12 (s.322-329)
- Ch.13 A Comparison of Four Listed Companies (s.330-338)
- Commentary on Chapter 13 (s.339-346)
- **Kalan kısımlar:** Kısım 4 Ch.14-15 (savunmacı/girişimci seçim kriterleri — kitabın en yoğun sayısal eşik kaynağı), Kısım 5 Ch.16-18, Kısım 6 Ch.19-20+Postscript, Kısım 7 Appendix 1-7.
- **ID numaralandırması Kısım 1-2'den KESİNTİSİZ devam eder:** İLKE-93'ten, FORMÜL-18'den, BAYRAK-24'ten başlar (Kısım 2'nin son numaraları: İLKE-92, FORMÜL-17, BAYRAK-23).
- **OCR notu:** Düz metin yüksek güvenilirlikte okundu. Table 9-1 (10 büyük fon performansı), Table 9-2 (Manhattan Fund portföyü — kısmen), Table 11-3 (kimya/petrol şirketleri karşılaştırması), Table 13-1 (4 şirket karşılaştırma özeti) ÇOK SÜTUNLU/OKUNAMAZ oldu — bunlardan HİÇBİR ham sayı kaynak alınmadı. İstisna: Table 9-3/9-4/9-5 (kapalı-uçlu fon iskonto verisi), Table 11-1 (tahvil kapsama oranları), Table 11-2 (Value Line DJIA tahmini — GERÇEK şirket verisi), Table 12-1 (ALCOA/Sears/DJIA büyüme oranı), Table 13-2 (4 şirket detaylı rasyo karşılaştırması) TAM OKUNABİLDİ ve DOĞRUDAN kullanıldı — bunlar didaktik/hayali örnekler DEĞİL, koordinatörün belirttiği gibi GERÇEK şirket verileridir, eşik kaynağı olarak KABUL EDİLDİ.
- **Bu kısımda 2 önemli GERÇEK vaka analizi bulundu ve doğrudan kullanıldı:** ALCOA'nın 1970 yıl-sonu kazanç raporu (Ch.12 — HBK'nın yönteme göre nasıl 2 katına kadar farklılaşabileceğinin canlı kanıtı) ve Graham'ın 4 şirket karşılaştırması + Zweig'in 1999 güncellemesi (Ch.13 — ELTRA/Emerson/Emery/Emhart 1970 ve EMC/Emerson/Expeditors/Exodus 1999, ikisi de gerçek NYSE/NASDAQ şirketleri).

---

## İlkeler

**Chapter 9 — Investing in Investment Funds (Graham):**

- **İLKE-93:** Yatırım fonu SEKTÖRÜ bir bütün olarak genel piyasayı kabaca TAKİP EDER (belirgin biçimde iyi ya da kötü değil) — çünkü fon yöneticileri KOLEKTİF olarak piyasadaki hisselerin öyle büyük bir kısmını yönetir ki, "piyasanın genelinde olan, fonların toplamına da (yaklaşık olarak) olmak ZORUNDADIR." Wiesenberger'in 10 büyük fonu 1961-1970'te S&P'yi YAKALADI, DJIA'yı GEÇTİ. (s.229-231)
- **İLKE-94:** 1960'ların "performans fonu" kültü — spekülatif, yüksek çarpanlı, temettü ÖDEMEYEN hisselere yoğunlaşarak olağanüstü KISA vadeli getiri kovalamak — kaçınılmaz olarak GEÇİCİ muhteşem kazançların ardından FELAKET kayıplar getirmiştir; "küçük fon boyutu" sürdürülen üstün performansla İLİŞKİLİDİR ama NEDEN değildir — büyük boyutun kendisi yapısal bir SÜRTÜNME yaratır. (s.232-237)
- **İLKE-95:** Kapalı-uçlu fonlar, AYNI yönetim becerisine sahip olsalar bile, SALT fiyatlama mekaniği yüzünden açık-uçlu (mutual) fonlardan YAPISAL olarak daha iyi bir alım fırsatı sunar — kapalı-uçlu paylar net aktif değerine göre İSKONTOLU (tarihsel ort. ~%9-14) işlem görürken açık-uçlu paylar PRİMLİ (~%9 satış yükü) satılır; AYNI kalitede bir kapalı-uçlu fonu iskontodan almak, yatırılan her dolar için ~1/5 DAHA FAZLA değer yakalar. (s.238-240)
- **İLKE-96:** "Dengeli" (balanced) fonlar (tek araçta tahvil+hisse karışımı), tipik yatırımcı için tahvil ve hisse bileşenlerini AYRI AYRI doğrudan edinmekten daha VERİMSİZDİR — dengeli fonların tahvil kısmı sadece ~%3,6-3,9 getiri sağlarken doğrudan tahvil alımından DAHA İYİ DEĞİLDİR, üstüne bir kat daha ücret eklenir. (s.241)

**Commentary on Chapter 9 (Zweig):**

- **İLKE-97:** Fon performansı KALICI (persistent) DEĞİLDİR — "Fon Performansı Hunisi" (Lipper verisi, Aralık 2002 geriye bakış): basit bir S&P500 endeks fonunu geçen fon yüzdesi zaman ufku UZADIKÇA hızla KÜÇÜLÜR: 1yıl %48,9, 3yıl %59,5, 5yıl %51,4, 10yıl %31,2, 15yıl %28,1, 20yıl SADECE %14,9 — ve bu rakam GERÇEK farkı BİLE OLDUĞUNDAN AZ gösterir çünkü tamamen KAPANMIŞ fonları hariç tutar. (s.248)
- **İLKE-98:** Bir fonun BAŞARISI, kendi GELECEKTEKİ başarısızlığının tohumlarını 5 yapısal mekanizmayla eker: (1) yıldız yöneticiler AVLANIR (rakip firmalarca kapılır), (2) "varlık filleşmesi" (asset elephantiasis) — giren para ya atıl nakit, ya mevcut pozisyonların AŞIRI büyütülmesi, ya da dikkatin ÇOK FAZLA yeni isme DAĞITILMASI zorunluluğu yaratır, (3) halka açılmadan önce "kuluçkalanan"/ücretsiz test edilen fonlar halka açıldığında EDGE'lerini kaybeder, (4) ölçekte YÜKSELEN işlem maliyetleri (tipik %1,5 işletme + %2 işlem gideriyle bir fonun maliyet SONRASI piyasayı YAKALAYABİLMESİ için maliyet ÖNCESİ piyasayı ~3,5 puan GEÇMESİ gerekir), (5) "sürü davranışı" — başarılı yöneticiler artık ŞİŞMAN ücret gelirini korumak için RİSK-KAÇAR/taklitçi hale gelir. (s.244-247)
- **İLKE-99:** Endeks fonlarının NEREDEYSE AŞILAMAZ yapısal avantajı, ultra-düşük maliyetten gelir (ort. %0,2 işletme + %0,1 işlem giderine karşı aktif fonun %1,5+%2'si) — %7 brüt piyasa getirisi varsayımıyla 20 yıllık ufukta bu maliyet farkı TEK BAŞINA $10.000'ı endeks fonunda ~$36.000'a, ortalama aktif fonda ise sadece ~$20.000'a çıkarır (~%45 fark SADECE maliyetten). (s.249)
- **İLKE-100:** Endeksi yenebilecek NADİR aktif fonları seçme kriterleri: yöneticiler fonun EN BÜYÜK hissedarları arasında olmalı; giderler DÜŞÜK olmalı; portföy referans endeksinden ANLAMLI ölçüde FARKLI görünmeli (gizli-endeksleme değil); fon daha önce yeni yatırımcılara KAPANMIŞ bir geçmişe sahip olmalı; fon AGRESİF reklam YAPMAMALI. Tarama SIRASI önemli — ÖNCE giderler (en ÖNGÖRÜLEBİLİR), SONRA risk (en kötü çeyrek kaybı toleransı + Morningstar notu), EN SON geçmiş performans (en AZ öngörücü). (s.250-252)
- **İLKE-101:** Bir fonu 1-3 yıllık göreli zayıf performans yüzünden ATEŞLEMEK genellikle YANLIŞTIR — Sequoia Fund ilk 29 yılının 12'sinde (%41'inde) S&P500'ün ALTINDA kaldı, yine de kümülatif %12.500 kazandı (endeks: %4.900); bir yönetici, tam olarak İŞE ALINDIĞI şeyi (geçici olarak MODA DIŞI kalan tutarlı bir stil) yaptığı için KOVULMAMALIDIR. GERÇEK satış sinyalleri: ani AÇIKLANAMAYAN strateji sapması, ARTAN giderler, aşırı işlemden kaynaklanan vergi faturaları, ANİDEN düzensiz getiriler. (s.253-254)

**Chapter 10 — The Investor and His Advisers (Graham):**

- **İLKE-102:** "Yatırım tavsiyesi" fikrinin özünde YERLEŞİK bir saflık vardır — başkasına "nasıl para kazanılır" diye sormanın sıradan işte GERÇEK bir karşılığı yoktur; profesyonel tavsiye HATALARDAN kaçınmaya yardım eder ama HİÇTEN kâr ÜRETMEZ. Danışmanın uygun rolü müşteriyi hatalardan korumak ve NORMAL/standart sonuçları GÜVENCE altına almaktır, ortalamanın ÜSTÜNDE getiri VAAT etmek değil. (s.257)
- **İLKE-103:** Bir müşteri temsilcisinin/simsarın komisyon-bazlı iş modeli, bireysel temsilcinin KİŞİSEL dürüstlüğünden BAĞIMSIZ olarak DAHA FAZLA aktivite/spekülasyonu TEŞVİK etmeye YAPISAL olarak eğilimlidir — yatırımcı, gerçek bir yatırımcı olarak (spekülatif "ipucu" istemediğini) AÇIKÇA ve TEKRAR TEKRAR belirtmelidir. (s.262-263)
- **İLKE-104:** Bir güvenlik analistinden alınan değer BÜYÜK ÖLÇÜDE yatırımcının KENDİ tutumuna/sorularına bağlıdır — "bu hisse YAKINDA yükselecek mi" sorulan bir analist kısa-vadeli piyasa-zamanlama düşüncesine ÇEKİLİR; "değer-odaklı" (fiyat-odaklı DEĞİL) bir müşteri tarafından görevlendirilen analist ÇOK DAHA FAYDALI bir çalışma sunabilir. (s.264-265)

**Commentary on Chapter 10 (Zweig):**

- **İLKE-105:** Profesyonel yardıma GERÇEKTEN ihtiyaç duyulduğunun işaretleri: portföy kaybının piyasanın KENDİ düşüşünü AŞMASI (Zweig'in eşiği: 2000-2002 ayı piyasasında >%40 kayıp, piyasa daha AZ kaybetmişken); kronik olarak dengesiz bütçe; GERÇEKTE çeşitlendirilmemiş ama ÇEŞİTLENDİRİLMİŞ GÖRÜNEN "kaotik" bir portföy (çok sayıda fon/hisse ama HEPSİ BİRLİKTE hareket ediyor); büyük yaşam geçişleri (serbest meslek, yaşlanan ebeveynler, üniversite masrafları). (s.273)
- **İLKE-106:** Danışman ücret tavanı: ücretler varlıkların yıllık %1'İNDEN FAZLASINI tüketiyorsa BAŞKA bir danışman ARANMALIDIR. (s.277)
- **İLKE-107:** Gerçekçi getiri beklentisi kontrolü: yatırımlarınızda yıllık ortalama %8-10 ÜZERİNDE bir getiri PROJEKSİYONU yapan HERHANGİ bir danışman GERÇEKÇİ DEĞİLDİR — mülakat sürecinde bir KIRMIZI BAYRAK olarak ele alınmalı. (s.277)
- **İLKE-108:** Herhangi bir danışmanı incelemek için somut durum tespiti (due diligence) listesi: danışmanın adı+firmasını "ceza/şikayet/dava/disiplin cezası/askıya alma" terimleriyle ÇEVRİMİÇİ ara; eyalet menkul kıymetler komisyoneri OFİSİNDEN disiplin kaydını sorgula; Form ADV'nin TAM kopyasını (bazı danışmanların ÇIKARDIĞI Disclosure Reporting Pages DAHİL) al; kimlik belgelerini (CFA/CFP/CPA) DOĞRUDAN sertifikasyon kurumundan ÇAPRAZ KONTROL et. (s.274-275)
- **İLKE-109:** Güvenilir bir danışman, sadece bir hisse-seçici DEĞİL, müşterinin KENDİ en kötü dürtülerine karşı YAPISAL bir savunma hattı işlevi görür — en iyi danışmanlar yazılı KAPSAMLI bir finansal plan, bir yatırım politikası bildirgesi ve bir varlık-tahsis planını müşteriyle BİRLİKTE (tek taraflı DAYATMADAN) oluşturur, VE müşteriyi de en az müşterinin danışmanı sorguladığı kadar SIKI sorgular. (s.278-279)

**Chapter 11 — Security Analysis for the Lay Investor: General Approach (Graham):**

- **İLKE-110:** Tahvil/imtiyazlı hisse güvenliği ÖNCELİKLE bir "kazanç KAPSAMA" (earnings coverage) oranıyla ölçülür — toplam sabit giderlerin (faiz, veya faiz+imtiyazlı temettü) kazançla KAÇ KEZ karşılandığı; HEM 7-yıllık ORTALAMA testi HEM alternatif "en kötü TEK yıl" testi kullanılır, İKİSİNDEN BİRİNİ geçmek YETERLİDİR. Minimum kapsama sektöre göre değişir: kamu hizmeti 4x(ort.)/3x(en kötü yıl), demiryolu 5x/4x, sanayi 7x/5x, perakende 5x/4x (vergi ÖNCESİ). (s.283-284)
- **İLKE-111:** Tarihsel kanıt bu kapsama-oranı testlerini GÜÇLÜ biçimde İLERİYE-DÖNÜK bir güvenlik göstergesi olarak DOĞRULAR — sonradan İFLAS eden HEMEN HEMEN HER demiryolu, iflastan YILLAR önce YETERSİZ kapsama göstermiştir (Penn Central'ın kapsaması 1970 çöküşünden 5 yıl ÖNCE, 1965'te ZATEN standardın ALTINDAYDI); standardı KARŞILAYAN HEMEN HEMEN HER demiryolu mali sıkıntıdan KAÇINMIŞTIR (tek kısmi istisna, New Haven Railroad, yeniden-yapılanma sonrası giderlerini sadece 1,1x karşıladı ve tekrar iflas etti). (s.286)
- **İLKE-112:** Kurumsal faiz ödemelerinin toplam VERGİ ÖNCESİ kârı TÜKETME HIZI sistemik bir uyarı göstergesidir — Graham'ın 1971 verisi: finansal-olmayan firmaların faiz ödemeleri 1963'ten 1970'e $9,8 milyardan $26,1 milyara çıkarak toplam vergi öncesi kârın %16'sından %29'una YÜKSELDİ (Ch.2'de işaretlenen "borç kârdan hızlı büyüyor" kalıbının AYNISI). (s.287)
- **İLKE-113:** Graham'ın basitleştirilmiş büyüme-hissesi değerleme formülü: **Değer = Güncel (Normal) Kazanç × (8,5 + 2 × Beklenen Yıllık Büyüme Oranı)**, büyüme oranı GELECEK 7-10 yıl için beklenen oran — daha karmaşık matematiksel modellerin bir YAKLAŞIKLAMASI olarak sunulur, ama BİLİNÇLİ bir uyarıyla: ÇOK YÜKSEK varsayılan büyüme oranlarında (≥%8/yıl) GÜVENİLİR DEĞİLDİR, formül matematiksel olarak KARARSIZ hale gelir (neredeyse SONSUZ değer İMA eder). (s.295-297)
- **İLKE-114:** Bir şirketin tarihsel büyüme oranını hesaplama kuralı: son 3 yılın kazanç ORTALAMASINI, TAM 10 yıl önceki KARŞILIK GELEN 3 yılın ortalamasıyla KIYASLA, sonra yıllıklandır (bileşiklendir) — ölçümün HER İKİ UCUNDAKİ tek-yıllık gürültüyü düzeltir. (s.319, Tablo 12-1 örneği)
- **İLKE-115:** Toplu/grup kazanç tahminleri (bir sektör veya endeks için) TEKİL şirket tahminlerinden DOĞASI GEREĞİ daha GÜVENİLİRDİR — Graham'ın kendi Value Line DJIA tahmin testi (1964 ortasında 1967-69 için yapılan, 1968 gerçek sonuçlarıyla kıyaslanan) TOPLAMDA makul doğrulukta çıktı, ÇOK SAYIDA tekil şirket tahmini "hedefi ıskalamış" olsa BİLE. (s.288-289)
- **İLKE-116:** "İki-parçalı değerleme" süreci tek bir birleşik değerlemeden ÜSTÜNDÜR: ÖNCE mekanik bir "geçmiş-performans değeri" hesapla (SADECE tarihsel kârlılık/istikrar/büyüme/mali duruma dayalı, geçmiş EĞİLİMİN devam ettiği varsayımıyla), SONRA AYRI olarak kıdemli analistin GELECEĞİN geçmişten NASIL farklılaşacağına dair yargısını EKLE — iki adımı BİRLEŞTİRMEK yerine GÖRÜNÜR/AYRI tutmak analistin ileriye-dönük varsayımlarını AÇIK ve DENETLENEBİLİR kılar. (s.299-301)

**Commentary on Chapter 11 (Zweig):**

- **İLKE-117:** Şirketin KENDİ raporlamasında taranacak kırmızı bayraklar: "seri satın alıcı" statüsü (yılda ort. >2-3 satın alma); "Başkalarının Parası"na (OPM) bağımlılık (nakit akış tablosunun faaliyet VS finansman satırlarını kontrol et — faaliyetten nakit SÜREKLİ negatifken finansmandan nakit SÜREKLİ pozitifse şirket kendi işinin ÜRETEMEDİĞİ nakde bağımlıdır); müşteri YOĞUNLAŞMASI (gelirin BÜYÜK kısmı tek/az sayıda müşteriden). (s.303-304)
- **İLKE-118:** Taranacak OLUMLU işaretler: dayanıklı bir rekabet "hendeği" (marka kimliği, pazar hakimiyeti, ölçek ekonomisi, benzersiz maddi-olmayan varlık, ikame direnci); 10 yıllık DÜZGÜN/istikrarlı gelir ve kazanç büyümesi (SON ZAMANLARDAKİ bir HIZLANMA değil) — sürdürülebilir uzun-vadeli büyüme oranı yaklaşık %10/yıl vergi ÖNCESİDİR (%6-7 vergi SONRASI); %15+ sürdürülen büyüme HEDEFİ koyan şirketler "SANRISAL"dır. (s.305)
- **İLKE-119:** "Sahip kazancı" (owner earnings: net kâr + amortisman − normal capex − opsiyon maliyeti/olağandışı kalem/pensiyon "geliri" düzeltmeleri), raporlanan net kârdan DAHA İYİ bir nakit-üretim ÖLÇÜSÜDÜR — hisse başı sahip kazancı son 10 yılda istikrarlı ort. ≥%6-7/yıl büyüyen bir şirket İSTİKRARLI bir nakit üreticisidir. (s.308)
- **İLKE-120:** Sermaye yapısı kuralı: uzun vadeli borç toplam sermayenin %50'sinin ALTINDA olmalı; "kazancın sabit giderleri karşılama oranı" tablosunu DOĞRUDAN kontrol et — kazancı faiz maliyetini KARŞILAMAYAN bir şirket ÖZÜNDE artık hissedarlarından ÇOK tahvil sahiplerine AİTTİR. (s.308-309)
- **İLKE-121:** Tekrarlayan hisse bölünmeleri VE rekor-yüksek fiyatlarda yapılan geri alımlar, YÖNETİMİN iş EKONOMİSİNDEN çok hissedar PSİKOLOJİSİNE hitap ettiğinin işaretidir — bölünme hisse-başı değerde HİÇBİR şey DEĞİŞTİRMEZ (2×$50 = 1×$100), ve hisse PAHALIYKEN (ucuz değil) yapılan geri alımlar şirket nakdini İSRAF eder, genellikle YÖNETİCİLERİN kendi opsiyonlarının değerini artırmak için ZAMANLANIR. (s.309)

**Chapter 12 — Things to Consider About Per-Share Earnings (Graham):**

- **İLKE-122:** TEK bir yılın hisse başı kazanç rakamını ASLA yüzeysel olarak KABUL ETME — AYNI şirketin AYNI çeyreği için TEK bir raporlanan HBK rakamı, kullanılan (birden fazla MEŞRU GÖRÜNEN) yönteme göre İKİ KATTAN FAZLA farklılaşabilir. Graham'ın CANLI ALCOA 1970 örneği: raporlanan rakamlar $4,19 ile $5,20 arasında değişti (primer/tam-seyreltilmiş, özel kalem dahil/hariç), AYNI çeyrekten F/K ~10x ile ~22x arası İMA edilebiliyordu. (s.310-312)
- **İLKE-123:** "Özel"/"tekrarlanmayan" kalemler DERİN şüpheyle karşılanmalı, ÖZELLİKLE tek bir "temizlik yapılan" kötü yılda KÜMELENDİKLERİNDE — bir şirket GELECEK beklenen kayıpları ÖNCEDEN, zaten yazılmış bir yıla yükleyebilir, böylece SONRAKİ yılları YAPAY olarak temiz tutar, hatta HENÜZ ÖDENMEMİŞ kayıplardan bir vergi KREDİSİ FAYDASI bile elde edebilir; ÇOK SAYIDA şirkette AYNI (durgunluk) yılında ANİ bir özel-kalem SALGINI görülmesine DİKKAT et. (s.312-315)
- **İLKE-124:** Tek yıllık rakam yerine ÇOK-YILLI ORTALAMA kazanç (7-10 yıl) kullanılmalı — bu, özel kalemleri/kredileri şirketin GERÇEK operasyonel tarihine DOĞAL olarak DAHİL eder, tek bir yılın karşılaştırılabilirliğini BOZMAK yerine. (s.319)
- **İLKE-125:** Amortisman yöntemi değişiklikleri (doğrusal vs hızlandırılmış), Ar-Ge muhasebeleştirme SEÇİMİ (gider vs kapitalize) ve envanter değerleme yöntemi (FIFO vs LIFO), ALTTAKİ işte GERÇEK bir DEĞİŞİKLİK OLMADAN raporlanan HBK büyümesini ÖNEMLİ ÖLÇÜDE ÇARPITABİLECEK EK muhasebe değişkenleridir — Graham'ın Trane Co. örneği: raporlanan ~%20'lik HBK "artışının" YARISI SADECE amortisman yöntemi değişikliğinden geldi, operasyonel iyileşmeden DEĞİL. (s.316)
- **İLKE-126:** Hisse değerlemesi "SADECE İSTİSNAİ durumlarda GERÇEKTEN güvenilirdir" — bu, Graham'ın TÜM formal güvenlik değerleme girişimi hakkındaki KENDİ AÇIK, kendini-sınırlayan uyarısıdır; akıllı yatırımcının GERÇEKÇİ hedefi genellikle sadece ödediği fiyat karşılığında MAKUL bir DEĞER aldığını DOĞRULAMAKTIR, "gerçek" değeri TAM olarak BELİRLEMEK değil. (s.318)

**Commentary on Chapter 12 (Zweig):**

- **İLKE-127:** GERÇEK nakit maliyetlerini (opsiyon üzerindeki bordro vergisi, birleşme gideri, gerçek yatırım zararı) DIŞLAYAN "pro forma" kazanç rakamları akıllı yatırımcı tarafından basitçe GÖRMEZDEN GELİNMELİDİR — birden fazla GERÇEK 1999-2001 örneği (InfoSpace, BEA Systems, JDS Uniphase) şirketlerin yüzlerce milyon dolarlık GERÇEK maliyeti dışlayarak hayali-olarak-pembe bir "sanki" kazanç rakamı sunduğunu gösteriyor. (s.322-323)
- **İLKE-128:** Agresif gelir-kayıt (revenue recognition) değişiklikleri (geliri nakit GERÇEKTEN alınmadan ÖNCE tanımak — Qwest'in 1999'daki rehber-geliri değişikliği net kâra $240M/~%20 EKLEDİ SADECE muhasebe değişikliğinden) genellikle ÇOK DAHA BÜYÜK alttaki sorunların GÖRÜNEN ucu ucudur — Qwest sonradan $2,2 milyar FAZLA-beyan edilmiş geliri YENİDEN düzenledi, hissesi ~%90 DÜŞTÜ. (s.323-324)
- **İLKE-129:** Normal FAALİYET giderini SERMAYE harcaması olarak yeniden SINIFLANDIRMAK (Global Crossing'in 1999'da ağ inşaat maliyetleriyle yaptığı gibi), HARCANAN GERÇEK NAKİTTE HİÇBİR değişiklik OLMADAN raporlanan net kârı VE toplam varlıkları AYNI ANDA ŞİŞİRİR — hangi maliyetleri "kapitalize ettiğini" ANİDEN değiştiren bir şirket, NEDEN ve NE değiştiğinin YAKINDAN incelenmesini HAK EDER. (s.324-326)
- **İLKE-130:** Çeyrekten çeyreğe TEKRARLANAN bir "özel kalem" (envanter değer düşüklüğü gibi) ARTIK GERÇEKTEN "tekrarlanmayan" DEĞİLDİR — Micron Technology ilk "olağandışı" kaydından SONRA 7 ARDIŞIK mali çeyrekte envanter değer düşüklüğü kaydetti; yatırımcılar KRONİK olarak tekrarlayan "özel" kalemleri İZLEMELİDİR. (s.326-327)
- **İLKE-131:** Pensiyon-planı muhasebe VARSAYIMLARI raporlanan net kârı ÖNEMLİ ÖLÇÜDE ŞİŞİREBİLİR — şirketin "net pensiyon faydasının" net kârın ~%5'ini AŞMASI, veya plan varlıkları üzerinde VARSAYILAN uzun-vadeli getiri oranının ~%6,5'in (2003 bağlamı) ÜZERİNDE olması VEYA gerçek piyasa getirileri DÜŞERKEN YÜKSELTİLMESİ kırmızı bayraktır (SBC Communications 2001'de varsayımını %8,5'ten %9,5'e YÜKSELTTİ, oysa fonu O YIL GERÇEKTE %6,9 KAYBETTİ; aynı yıl Berkshire Hathaway kendi varsayımını %8,3'ten %6,5'e TEMKİNLİ biçimde DÜŞÜRDÜ). (s.327)
- **İLKE-132:** Pratik kazanç-kalitesi okuma yöntemi: bir şirketin yıllık raporunu TERSTEN oku (önce dipnotlar/arka kısım) — şirketin bulmanızı İSTEMEDİĞİ sorunlar genellikle ORADA gömülüdür; HER ZAMAN "önemli muhasebe politikaları özeti" dipnotunu oku ve bunu YAKIN bir rakibin EŞDEĞER dipnotuyla KIYASLA (görece agresiflik ölçüsü olarak). (s.328-329)

**Chapter 13 — A Comparison of Four Listed Companies (Graham):**

- **İLKE-133:** Graham'ın savunmacı yatırımcının BİREYSEL hisse seçimi için 7 SOMUT istatistiksel gerekliliği (Ch.5-12 boyunca inşa edilenin AÇIK/BİRLEŞTİRİLMİŞ özeti): (1) yeterli BÜYÜKLÜK, (2) yeterince GÜÇLÜ mali durum, (3) en az 20 yıl KESİNTİSİZ temettü, (4) son 10 yılda HİÇ kazanç ZARARI YOK, (5) 10 yıllık hisse başı kazanç büyümesi en az 1/3, (6) fiyat net aktif (defter) değerinin en fazla 1,5 KATI, (7) fiyat son 3 yıl ortalama kazancın en fazla 15 KATI. (s.337-338)
- **İLKE-134:** Aksi halde KARŞILAŞTIRILABİLİR şirketler arasında GÜNCEL F/K oranı, GERÇEK operasyonel performans veya mali durumdan ÇOK DAHA GENİŞ bir ARALIKTA değişebilir (Graham'ın kendi 4-şirket örneğinde: AYNI 1968-1970 ortalama-kazanç bazında 9,7x'ten 45x'e) — geniş bir F/K farkı, otomatik olarak yüksek-momentumlu ismi TERCİH etmek için değil, NEDENİNİ ARAŞTIRMAK için bir SİNYALDİR. (s.332-336)
- **İLKE-135:** "Değer-tipi" (düşük çarpanlı) yatırımları "cazibe-tipi" (yüksek çarpanlı) yatırımlara TERCİH etmek, SALT aritmetik kadar YATIRIMCI MİZACI/felsefesi meselesidir — Graham AÇIKÇA ucuz çiftin PAHALI çifti herhangi bir KISA dönemde geçeceğini TAHMİN ETMEZ, çünkü piyasa momentumu ALTTAKİ değer farkından BAĞIMSIZ olarak yüksek-çarpanlı isimler için SÜREBİLİR. (s.338)

**Commentary on Chapter 13 (Zweig):**

- **İLKE-136:** GERÇEK bir 1999 dört-hisse karşılaştırması (Emerson Electric / EMC / Expeditors International / Exodus Communications) Graham'ın Ch.13 dersini GÜNCEL veriyle GÖSTERİR: Emerson (F/K 17,7x, 42 ARDIŞIK yıl artan kazanç, 43 ARDIŞIK yıl artan temettü) dördün EN UCUZ ve EN İSTİKRARLI olanıydı ama 1999'da "SIKICI" görünüyordu; Exodus (F/K ANLAMSIZ — şirket $242M gelire karşı $130M ZARAR ediyordu, $2,6 milyar BORÇLA) EN HEYECAN VERİCİ olanıydı, kısmen tekrarlanan hisse bölünmelerinin yarattığı "daha fazla hisse = daha fazla servet" YANILSAMASI sayesinde. 2002 sonu itibariyle: Emerson %4'ten AZ düştü, Expeditors ~%51 YÜKSELDİ, EMC %88 DÜŞTÜ, Exodus İFLAS ETTİ (hisse değeri sıfıra yakın). (s.339-346)
- **İLKE-137:** Hisse bölünmeleri (stock split) HİÇBİR ekonomik değer YARATMAZ (2 hisse $50'den = 1 hisse $100'den) ama duyuru ÜZERİNE hisse fiyatını GÜVENİLİR biçimde YUKARI hareket ettirir — yatırımcı psikolojisinin (daha "fazla" hisseye sahip olmaktan zengin HİSSETMEK) aritmetiğin ÜZERİNE ÇIKMASININ saf bir kanıtı; Zweig, tekrarlayan ve yoğun biçimde REKLAMI yapılan hisse bölünmelerini, yönetimin iş temellerine ODAKLANMAK yerine sofistike-OLMAYAN hissedar PSİKOLOJİSİNE hitap ettiğinin (ve bunu SÖMÜRDÜĞÜNÜN) bir işareti olarak DEĞERLENDİRİR. (s.344)

---

## Formüller

| # | Formül | QuaxisLabs karşılığı |
|---|---|---|
| **FORMÜL-18** Bono/İmtiyazlı Hisse Kazanç Kapsama Oranı (Table 11-1): sektöre göre minimum ort.-7-yıl / en-kötü-yıl eşikleri — Kamu hizmeti 4x/3x, Demiryolu 5x/4x, Sanayi 7x/5x, Perakende 5x/4x (vergi öncesi) (s.283-284) | **KAPSAM DIŞI (doğrudan) / DOLAYLI olarak ilişkili.** QuaxisLabs tahvil değil HİSSE analiz motorudur; ancak "faiz karşılama oranı" kavramı hisse tarafında borç-yükü göstergesi olarak faydalıdır. `financial_debt` (`calculator.py`) mevcut ama FAİZ GİDERİ (interest_expense) sanayi/ticaret şirketleri için EKSİK — Kısım 1'de tespit edilen (Buffett turu FORMÜL-05 ile AYNI) veri açığının 5. tekrarı. |
| **FORMÜL-19** Graham Büyüme Hissesi Değerleme Formülü: **Değer = Güncel (Normal) Kazanç × (8,5 + 2 × Beklenen Yıllık Büyüme Oranı %)**, büyüme oranı gelecek 7-10 yıl için; ≥%8/yıl büyümede GÜVENİLMEZ (s.295-297) | **VERİ EKSİK / KISMEN TÜRETİLEBİLİR.** `graham_multiple`/`graham_fair_value_price` (`valuation.py`) FARKLI bir Graham formülüdür (F/K×PD/DD≤22,5 — kitabın Ch.20'sinde ortaya çıkacak DAHA GEÇ/basitleştirilmiş model). BU formül (8,5+2g) `valuation.py`'de HİÇ YOK. Güncel kazanç (`ttm_net_income`) mevcut; büyüme oranı (g) tahmini için çok-yıllı kazanç serisi GEREKİR (yine `trends.py` 12-çeyrek kısıtı). |
| **FORMÜL-20** Büyüme Oranı Hesaplama Yöntemi: son 3 yılın ortalaması ÷ 10 yıl önceki karşılık gelen 3 yılın ortalaması, yıllıklandırılmış/bileşik (s.319, Tablo 12-1: ALCOA %9,0/yıl, Sears %8,7/yıl, DJIA %5,7/yıl) | **VERİ EKSİK.** Yine 10 yıllık kazanç serisi sorunu — kitap boyunca (2 kitap toplamında) 5. tekrar eden AYNI kök kısıt. |
| **FORMÜL-21** Graham'ın 7 Savunmacı Yatırımcı Kriteri (Ch.13 özet listesi): (1) yeterli büyüklük, (2) yeterli mali güç, (3) ≥20 yıl kesintisiz temettü, (4) son 10 yılda zarar YOK, (5) 10 yıllık HBK büyümesi ≥1/3, (6) fiyat ≤1,5× net aktif değeri, (7) fiyat ≤15× son 3 yıl ort. kazanç (s.337-338) | **KISMEN MEVCUT/TÜRETİLEBİLİR.** (1) `market_cap` MEVCUT (mutlak eşik tanımlanmalı, bkz Kısım2 FORMÜL-11); (2) `current_ratio`/`debt_to_equity` MEVCUT; (3)-(5) TAMAMEN VERİ EKSİK (temettü + 10 yıllık HBK serisi — tekrarlayan açık); (6) `pb_ratio` MEVCUT ama BURADAKİ eşik (1,5×) Kısım2 FORMÜL-17'deki (Ch.8, 1,33×) ile FARKLI — Graham'ın KENDİSİ kitap içinde 2 FARKLI PD/DD eşiği kullanıyor, bu ayrım not düşülmeli; (7) `pe_ratio` (TTM, 3-yıl-ort. DEĞİL) KISMEN karşılık verir. |
| **FORMÜL-22** Fon Gider Oranı Tavanları (Zweig, 2003): Tahvil %0,75, ABD büyük/orta hisse %1,0, Junk bond %1,0, ABD küçük hisse %1,25, Yabancı hisse %1,50 (s.251-252) | **KAPSAM DIŞI.** Fon SEÇİMİ, QuaxisLabs'ın tekil hisse/kripto analiz kapsamı DIŞINDA. |
| **FORMÜL-23** Danışman Ücret Tavanı = Varlıkların yıllık %1'inden FAZLASI kabul edilemez (s.277) | **KAPSAM DIŞI.** Danışmanlık ücreti değerlendirmesi sistemin kapsamı DIŞINDA. |
| **FORMÜL-24** Kapalı-Uçlu Fon İskonto Stratejisi = %9 primli açık-uçlu yerine %10-15 iskontolu kapalı-uçlu fon al → yatırılan her dolar için ~1/5 DAHA FAZLA değer (s.238-240) | **KAPSAM DIŞI.** Fon seçimi/portföy-seviyesi strateji — Kısım1 FORMÜL-06, Kısım2 FORMÜL-13 ile AYNI kapsam-dışı kategorisi. |

---

## Eşikler (tablo)

| Gösterge | Eşik / Aralık | Yorum | Kaynak | Sayfa |
|---|---|---|---|---|
| Açık-uçlu (mutual) fon satış yükü | Tipik ~%9 prim (asset value üzerine) | Alım maliyeti | Graham, Ch.9 | s.238-239 |
| Kapalı-uçlu fon iskontosu | Tipik %10-15 | Aynı kalite için DAHA AZ ödeme fırsatı | Graham, Ch.9 | s.238-239 |
| Fon performans devamlılığı (Lipper, Aralık 2002) | Endeksi geçen fon oranı: 1yıl %48,9 → 20yıl %14,9 | Zaman ufku uzadıkça hızla düşer, gerçek fark BU rakamdan bile BÜYÜK | Zweig, Comm.9 | s.248 |
| Aktif fon maliyet-öncesi başabaş eşiği | ~%1,5 işletme + ~%2 işlem maliyeti → piyasayı maliyet ÖNCESİ ~3,5 puan geçmek gerekir | Sadece maliyet SONRASI eşitlenmek için | Zweig, Comm.9 | s.246-247 |
| Endeks vs aktif fon 20-yıllık getiri farkı (%7 piyasa getirisi varsayımı) | $10.000 → ~$36.000 (endeks) vs ~$20.000 (ort. aktif) | ~%45 fark SADECE maliyetten | Zweig, Comm.9 | s.249 |
| Fon gider oranı tavanları (kategoriye göre) | Tahvil %0,75 / Büyük-orta hisse %1,0 / Junk bond %1,0 / Küçük hisse %1,25 / Yabancı hisse %1,50 | Bunun üzerinde başka fon aranmalı | Zweig, Comm.9 | s.251-252 |
| Danışman ücret tavanı | Varlıkların yıllık %1'i | Aşan durumda başka danışman ara | Zweig, Comm.10 | s.277 |
| Gerçekçi getiri beklentisi tavanı | Yıllık ort. %8-10 üzeri GERÇEKÇİ DEĞİL | Danışman mülakatı kırmızı bayrağı | Zweig, Comm.10 | s.277 |
| "Ciddi kayıp" eşiği (danışman ihtiyacı sinyali) | 2000-2002 döneminde portföyün >%40 kaybı | Piyasanın kendisinden DAHA KÖTÜ performans | Zweig, Comm.10 | s.273 |
| Tahvil/imtiyazlı hisse kapsama oranı (kamu hizmeti) | 4x (ort. 7 yıl) / 3x (en kötü yıl) | Vergi öncesi | Graham, Ch.11 | s.283-284 |
| Tahvil/imtiyazlı hisse kapsama oranı (demiryolu) | 5x / 4x | Vergi öncesi | Graham, Ch.11 | s.283-284 |
| Tahvil/imtiyazlı hisse kapsama oranı (sanayi) | 7x / 5x | Vergi öncesi, en YÜKSEK eşik | Graham, Ch.11 | s.283-284 |
| Tahvil/imtiyazlı hisse kapsama oranı (perakende) | 5x / 4x | Vergi öncesi | Graham, Ch.11 | s.283-284 |
| Kurumsal faiz yükü sistemik uyarı verisi (1963→1970) | Faiz ödemeleri toplam vergi öncesi kârın %16'sından %29'una çıktı | Sistemik kaldıraç uyarısı | Graham, Ch.11 | s.287 |
| Graham büyüme formülü güvenilirlik sınırı | Beklenen büyüme ≥%8/yıl → formül matematiksel olarak KARARSIZ | Sonsuza yakınsayan değer riski | Graham, Ch.11 | s.295-296 |
| Sürdürülebilir uzun-vadeli büyüme oranı (Zweig) | ~%10/yıl vergi öncesi (%6-7 vergi sonrası) MAKUL; ≥%15/yıl "sanrısal" | Ampirik araştırma bulgusu | Zweig, Comm.11 | s.305 |
| Owner earnings büyüme eşiği | Hisse başı owner earnings'in 10 yılda istikrarlı ort. ≥%6-7/yıl büyümesi | İstikrarlı nakit üretici işareti | Zweig, Comm.11 | s.308 |
| Sermaye yapısı eşiği | Uzun vadeli borç < toplam sermayenin %50'si | Aşırı kaldıraç uyarısı | Zweig, Comm.11 | s.308 |
| Ar-Ge harcaması sektörel örnekler (2002) | P&G ~%4 net satış, 3M ~%6,5, J&J ~%10,9 | Sektöre göre kalibrasyon referansı | Zweig, Comm.11 | s.305 |
| Pensiyon "net fayda" uyarı eşiği | Net kârın >%5'i pensiyon kazancından geliyorsa dikkat; varsayılan getiri >%6,5 (2003) mantıksız | Kazanç kalitesi kırmızı bayrağı | Zweig, Comm.12 | s.327 |
| Serial-acquirer uyarı eşiği | Yılda ortalama >2-3 satın alma | Potansiyel sorun işareti | Zweig, Comm.11 | s.303 |
| ALCOA vaka analizi (1970) | Aynı çeyrek HBK'sı yönteme göre $4,19-$5,20 arası (F/K 10x-22x arası) | Tek-yıl/tek-yöntem HBK'ya güvenmemenin canlı kanıtı | Graham, Ch.12 | s.310-312 |
| Trane Co. vaka analizi (1970) | Raporlanan %20 HBK artışının YARISI sadece amortisman yöntemi değişikliğinden | Muhasebe-kaynaklı büyüme yanılsaması | Graham, Ch.12 | s.316 |
| Emerson Electric (1999, GERÇEK şirket) | F/K 17,7x; 42 yıl kesintisiz kazanç artışı; 43 yıl kesintisiz temettü artışı | Dördün en ucuz/istikrarlısı, ama "sıkıcı" görünüyordu | Zweig, Comm.13 | s.341 |
| EMC Corp (1999, GERÇEK şirket) | F/K 103x; raporlanan büyüme %24 ama satın alma-hariç GERÇEK büyüme sadece %3,6 | Görünür büyümenin M&A kaynaklı optik etkisi | Zweig, Comm.13 | s.341-342 |
| Exodus Communications (1999, GERÇEK şirket) | $242M gelire karşı $130M zarar, $2,6 milyar borç | 2001'de iflas etti | Zweig, Comm.13 | s.344-345 |
| Emery Air Freight (Graham'ın 1970 örneği, GERÇEK şirket) | F/K ~40-60x | 1972-1999 arası enflasyon-düzeltmeli %72,8 değer kaybı | Graham/Zweig, Ch.13/Comm.13 | s.336-337 |

---

## Kontrol Listeleri

**KONTROL I — Yatırım Fonu Seçim Kontrolü (Ch.9 + Comm.9, 6 madde):**
1. Fon giderleri kategori tavanlarının (tahvil %0,75, büyük hisse %1,0, küçük hisse %1,25, yabancı %1,50) ALTINDA mı?
2. Fon yöneticileri fonun kendisinin BÜYÜK hissedarları mı?
3. Fonun portföyü, karşılaştırıldığı endeksten belirgin biçimde FARKLI mı (gizli-endeksleme değil mi)?
4. Fon daha önce yeni yatırımcılara KAPANMIŞ mı (büyüklük disiplini işareti)?
5. Geçmiş performansı SON sırada mı değerlendiriyorum (gider → risk → geçmiş performans sırası)?
6. Fonu sadece 1-3 yıllık zayıf performans yüzünden satmayı mı düşünüyorum (yanlış sinyal olabilir) — yoksa strateji sapması/gider artışı/anormal getiri gibi GERÇEK bir kırmızı bayrak mı var?

**KONTROL J — Yatırım Danışmanı Değerlendirme Kontrolü (Ch.10 + Comm.10, 5 madde):**
1. Danışmanın adını+firmasını "şikayet/dava/disiplin cezası" terimleriyle aradım mı?
2. Eyalet menkul kıymetler komisyonundan disiplin kaydını sorguladım mı?
3. Form ADV'nin TAM kopyasını (Disclosure Reporting Pages dahil) aldım mı?
4. Ücret, varlıkların yıllık %1'ini AŞIYOR mu?
5. Danışman yıllık %8-10 üzeri getiri VAAT ediyor mu (gerçekçi değil sinyali)?

**KONTROL K — Bono/Kapsama Oranı Güvenlik Kontrolü (Ch.11, 4 madde):**
1. Şirketin sektörüne uygun MİNİMUM kapsama oranını (ort. 7-yıl VEYA en-kötü-yıl testi) karşılıyor mu?
2. Kurumsal faiz yükü, toplam vergi öncesi kâra oranla YILLAR içinde ARTIYOR mu (sistemik uyarı)?
3. Şirket büyüklüğü, sektöre uygun minimum ölçek eşiğini karşılıyor mu?
4. Adi hisse (junior stock) piyasa değeri, borcun toplamına göre yeterli bir "yastık" sağlıyor mu?

**KONTROL L — Kazanç Kalitesi Muhasebe Kontrolü (Ch.12 + Comm.12, 7 madde):**
1. Raporlanan HBK'nın hangi VARYANTINI (primer/seyreltilmiş, özel kalemler dahil/hariç) kullanıyorum, neden?
2. Bu dönemde/sektörde "özel kalemler" salgını var mı (çoklu şirket AYNI kötü yılda temizlik yapıyor mu)?
3. Tek yıl yerine 7-10 yıllık ORTALAMA kazancı mı kullanıyorum?
4. Amortisman yöntemi, Ar-Ge muhasebesi veya envanter yöntemi (FIFO/LIFO) SON ZAMANLARDA değişti mi?
5. "Pro forma" kazanç rakamı GERÇEK nakit maliyetleri (opsiyon vergisi, birleşme gideri) DIŞLIYOR mu?
6. Gelir kayıt yöntemi (revenue recognition) yakın zamanda değişti mi, bu değişiklik kazancı NASIL etkiledi?
7. Normal faaliyet gideri, SERMAYE harcaması olarak yeniden SINIFLANDIRILDI mı (Global Crossing tipi)?

**KONTROL M — Graham'ın 7 Savunmacı Yatırımcı Kriteri (Ch.13, doğrudan liste, 7 madde):**
1. Yeterli büyüklük var mı?
2. Yeterince güçlü mali durum var mı?
3. En az 20 yıl kesintisiz temettü ödemesi var mı?
4. Son 10 yılda hiç zarar yılı YOK mu?
5. Son 10 yılda hisse başı kazanç en az 1/3 oranında büyümüş mü?
6. Fiyat, net aktif değerin 1,5 katını AŞMIYOR mu?
7. Fiyat, son 3 yıl ortalama kazancın 15 katını AŞMIYOR mu?

---

## Kırmızı Bayraklar

- **BAYRAK-24:** "Performans fonu" cazibesine kapılmak — kısa dönemde olağanüstü getiri sağlayan, spekülatif/temettü ÖDEMEYEN hisselere yoğunlaşan bir fon; büyük ölçekte SÜRDÜRÜLEMEZ risk düzeyi. (Ch.9, s.232-233)
- **BAYRAK-25:** Açık-uçlu (mutual) fonu ~%9 PRİMLE satın alırken AYNI kalitede bir kapalı-uçlu fonun %10-15 İSKONTOYLA mevcut olması — mekanik olarak DAHA AZ değer için DAHA FAZLA ödemek. (Ch.9, s.238-239)
- **BAYRAK-26:** SADECE geçmiş getirisine bakarak fon seçmek — endeksi geçen fon oranı zaman ufku UZADIKÇA hızla düşer (20 yılda sadece %14,9). (Comm.9, s.248)
- **BAYRAK-27:** Bir fonu, geçmişi İYİ olduğu (yıldız yönetici) için seçmek — "varlık filleşmesi" ve "sürü davranışı" başarılı fonların GELECEK performansını sistematik olarak aşındırır. (Comm.9, s.245-247)
- **BAYRAK-28:** Bir fonu SADECE 1-3 yıllık zayıf göreli performans yüzünden satmak — Sequoia Fund örneği bunun genellikle YANLIŞ bir tepki olduğunu gösterir. (Comm.9, s.253-254)
- **BAYRAK-29:** "Bu fırsat kaçmaz", "garantili", "riski yok" gibi baskı dili kullanan bir danışman/satıcı ile çalışmak. (Comm.10, s.275)
- **BAYRAK-30:** Bir danışmanın Form ADV'sinin Disclosure Reporting Pages'ini VERMEMESİ veya vermekte İSTEKSİZ olması. (Comm.10, s.274-275)
- **BAYRAK-31:** Aynı raporlama döneminde ÇOK SAYIDA şirketin AYNI ANDA "özel kalem" temizliği yapması — sektör-çapında bir muhasebe manipülasyonu sinyali. (Ch.12, s.314-315)
- **BAYRAK-32:** "Pro forma" kazanç raporlaması — GERÇEK, NAKİT maliyetleri (opsiyon vergisi, birleşme gideri, yatırım zararı) dışlayarak "olsaydı" bir kazanç rakamı sunmak. (Comm.12, s.322-323)
- **BAYRAK-33:** Bir muhasebe kaleminin (stok değer düşüklüğü, "özel gider") "OLAĞANDIŞI/TEKRARLANMAYAN" etiketiyle ART ARDA birden fazla çeyrek/yıl TEKRARLANMASI. (Comm.12, s.326-327)
- **BAYRAK-34:** Pensiyon fonu VARSAYILAN getiri oranının, gerçek piyasa getirileri DÜŞERKEN YÜKSELTİLMESİ (SBC örneği: varsayım artırılırken fon GERÇEKTE kaybetti). (Comm.12, s.327)
- **BAYRAK-35:** Normal FAALİYET giderinin SERMAYE harcaması olarak yeniden sınıflandırılması yoluyla raporlanan net kârın/varlıkların şişirilmesi (Global Crossing örneği). (Comm.12, s.324-326)
- **BAYRAK-36:** Şirketin TEK bir müşteriye (veya küçük bir gruba) gelirinin BÜYÜK KISMI için bağımlı olması — Sycamore Networks örneği: gelirin %100'ü tek müşteriden, o müşteri iflas etti. (Comm.11, s.304)
- **BAYRAK-37:** Tekrarlayan hisse bölünmelerini BAŞARI göstergesi gibi kutlamak/pazarlamak — matematiksel olarak SIFIR değer yaratır, sadece psikolojik yanılsama. (Comm.13, s.344)
- **BAYRAK-38:** Yıllık ortalama %15+ kazanç büyümesi HEDEFİ koyan/vaat eden bir şirket yönetimi — bu oran uzun vadede istatistiksel olarak "sanrısal" kabul edilir. (Comm.11, s.305)

---

## Uygulama Notları

1. **Bu kısım, "GERÇEK şirket verisi vs hayali didaktik örnek" ayrımının Buffett turundan beri en NET test edildiği bölümdür** — koordinatörün talimatına uygun olarak Ch.12'nin ALCOA vaka analizi ve Ch.13'ün 4-şirket karşılaştırması (hem Graham'ın 1970 versiyonu hem Zweig'in 1999 güncellemesi) GERÇEK NYSE/NASDAQ şirketleri olduğundan doğrudan eşik/örnek KAYNAĞI olarak KULLANILDI — Bölüm 7'deki didaktik örnek gelir tablosu (Buffett kitabı) ile AYNI kategoriye SOKULMADI.
2. **"10+ yıllık kazanç serisi" veri açığı 5. KEZ tekrarlandı** (FORMÜL-18/19/20/21 + Kısım1 FORMÜL-05 + Kısım2 FORMÜL-08/09/15) — bu artık QuaxisLabs'ın EN YÜKSEK öncelikli YAPISAL eksikliği kesinleşti; hem Buffett hem Graham kitabının SAYISIZ formülü AYNI `trends.py` 12-çeyrek sınırına takılıyor.
3. **Graham'ın KENDİSİ kitap içinde İKİ FARKLI PD/DD (fiyat/defter değeri) eşiği kullanıyor** — Ch.8'de "≤1,33×" (İLKE-80/Kısım2 FORMÜL-17), Ch.13'te "≤1,5×" (İLKE-133/FORMÜL-21). Bu, kitabın KENDİ İÇİNDE bir tutarsızlık DEĞİL — Ch.8'in ölçütü GENEL bir "muhafazakar alım" kılavuzu, Ch.13/14'ün 1,5× ölçütü SAVUNMACI yatırımcının 7-KRİTERLİK RESMİ listesinin PARÇASI. İkisi ayrı ayrı `valuation.py`'ye eklenirken bu FARK açıkça belgelenmeli (hangi bağlamda hangi eşik kullanılıyor).
4. **Ch.13'ün 7-kriterlik listesi (FORMÜL-21/KONTROL M), kitabın ŞİMDİYE KADAR en YOĞUN TEK formül kümesi** — Ch.5'in 4 kuralı (Kısım2) ile BÜYÜK ÖRTÜŞME var (büyüklük, mali güç, temettü, fiyat/kazanç) ama Ch.13 listesi 3 YENİ nicel kriter EKLİYOR: (4) 10 yılda sıfır zarar yılı, (5) 10 yıllık HBK büyümesi ≥1/3, (6) PD/DD≤1,5×. Kısım 4 (Ch.14-15) işlendiğinde bu liste muhtemelen NİHAİ/en OLGUN haliyle tekrar görülecek — o zaman TAM çapraz referans tablosu oluşturulmalı.
5. **QuaxisLabs kapsam sınırı 3 KEZ daha doğrulandı bu turda:** fon seçimi (FORMÜL-22/24), danışmanlık ücreti (FORMÜL-23), tahvil kapsama oranı (FORMÜL-18, dolaylı ilişkili ama doğrudan uygulanamaz) — hepsi Kısım1/2'deki "portföy-seviyesi kapsam dışı" kategorisiyle TUTARLI.
6. **Kazanç kalitesi/muhasebe manipülasyonu teması (Ch.12+Comm.12) bu kitapta İLK KEZ bu YOĞUNLUKTA ortaya çıktı** — pro forma kazanç, agresif gelir kaydı, sermaye-harcaması-olarak-yeniden-sınıflandırma, pensiyon varsayımı manipülasyonu gibi kalemler QuaxisLabs'ın MEVCUT veri modelinde (isyatirim.py/kap_financials.py standart alan haritaları) DOĞRUDAN taranamaz — bunlar NİTEL/dipnot-okuma gerektiren analiz türleridir, sayısal alan eklemekle ÇÖZÜLEMEZ; ileride bir "kazanç kalitesi kontrol listesi" (bu turdaki KONTROL L) QuaxisLabs raporlarına METİN/checklist formatında eklenebilir (kod değil, kullanıcı rehberliği olarak).
7. **Faiz karşılama oranı (FORMÜL-18) sanayi/ticaret şirketleri için EN YÜKSEK eşiği (7x) taşıyor** — bu, Buffett turunda ZATEN en çok vurgulanan tekil veri açığı (faiz gideri, sanayi şirketleri için XI_29 şemasında YOK) olarak tespit edilen kalemin 3. kez farklı bir kitapta/bağlamda ortaya çıkışı — öncelik listesinde YUKARI taşınmalı.
8. **OCR ile ilgili not:** Bu turda kalıcı bir sayısal belirsizlik YOK. Table 9-1, Table 9-2 (Manhattan Fund portföyü), Table 11-3 (kimya/petrol karşılaştırması), Table 13-1 (4 şirket özet) çok-sütunlu OKUNAMAZ tablolardı ama HİÇBİRİNDEN ham sayı kullanılmadı — sadece çevresindeki DÜZ METİNDE (Table 9-1 için "Manhattan Fund 1967 +%38,6 vs S&P +%11", Table 13-1/13-2 için Table 13-2'nin TAM okunabilen kısmı) AÇIKÇA tekrarlanan rakamlar alındı.

--

---

## Kısım 4: Ch.14-15 + Commentary (s.347-446)

**Chapter 14 — Stock Selection for the Defensive Investor (Graham):**

- **İLKE-138:** Savunmacı yatırımcının hisse seçim yaklaşımı iki farklı yöntemin birini benimseyebilir: (1) maliyet ve çaba minimumlaştırılmış endeks portföyü (DJIA veya geniş endeks), ya da (2) Graham'ın 7 nicel kriteri uygulanarak özenle seçilmiş hisseler. Her iki yol da makul sonuçlar verir; ortadaki hiçbir yol veremez. (s.347)
- **İLKE-139:** Graham'ın savunmacı yatırımcı için 7 kriterin “genel yorumu”: Bu kriterler iki karşıt yönde birden eleme yapar — küçük/zayıf/zararlı/temettüsüz şirketleri soldan, aşırı yüksek çarpanla işlem gören popüler şirketleri sağdan dışlar. Bu, eleman bir birim bırakmak için TASARLANMIŞ bir listedir. (s.349)
- **İLKE-140:** Savunmacı portföyün kazanç/fiyat oranı (E/P = F/K'ın tersi) en az AA kaliteli tahvil faizine eşit veya yüksek olmalıdır. 1970 başı örneği: AA tahvil %7,5 → maksimum F/K = 13,3. (s.350; Zweig 2003 notu: AA tahvil %4,6 → maksimum F/K = 21,7)
- **İLKE-141:** Bir portföyün ortalama çarpan hedefi: maksimum F/K sınırın yaklaşık %20 altı — Graham 15x sınırında ortalama 12-13x hedefler. Zweig 2003 güncellemesi: 17x sınırında ortalama 14x hedef. (s.350)
- **İLKE-142:** Düşük çarpanlı hisseler (düşük F/K) kural olarak "süperşirketlerin" değil, az beğenilen/ıskalanmış ikincil şirketlerin özelliğidir; ancak bu şirketlerin hisseleri de 7-kritere göre sertifiye edilerek satın alınabilir — Graham bunu "ortalama bir F/K portföyü" hedefinin doğal sonuçu olarak görür. (s.350-351)
- **İLKE-143:** Kamu hizmetleri (public utility) şirketleri için finansal güç kriteri farklıdır: borcuşen toplamı hisse senedişlerinin (defter değeriyle) iki katını AŞAMAMALIDIR. Sanayi şirketlerindeki "Borcu ≤ net cari varlıklar" kuralı burada geçerli değildir. (s.348)
- **İLKE-144:** Savunmacı yatırımcı portföyü: minimum 10, maksimum 30 hisse. Alt sınır çeşitlilik gerektiriyor, üst sınır analiz kapasitesini aşıyor — her iki üst işletim serbest bırakılamaz. (s.351)

**Commentary on Chapter 14 (Zweig):**

- **İLKE-145:** “Ev yanılması” (home bias) — Yatırımcılar tanıdıkları şirketleri (işyeri, yerel şirket, sık alınan ürlin üreticisi) fazla ağırlıklı tutarlar. Tanışıklık, kaliteyi veya ucuzluğu kanıtlamaz; çeşitlilikı yok eder. (s.382-383)
- **İLKE-146:** Zweig'ın Graham kriterlerine 2003 güncellemesi: Büyüklük eşiği $100M satış yerine piyasa değeri ≥2 milyar dolar; P/E tavanı 3 yıllık ortalamaya dayalı 15x iken AA tahvil bazlı 17x'ın altı olarak güncellendi (2003 koşullarında). (s.376-377)
- **İLKE-147:** Şerefiye (goodwill) muhasebesi: Büyük şerefiye bakıyesi iki kaynaktan doğar — (1) şirket satın almış ve varlık değerinin çok üstüne ödemiş, ya da (2) kendi hissesi defter değerinin çok üstünde işlem görüyor. Her iki durum da defter değerinin değerleme için güvenilirliğini azaltır. (s.388-390)
- **İLKE-148:** “Sürekli alıcı” (serial acquirer) şirket: yılda birden fazla satın alma yapan şirket, organik büyyme yerine muhasebe konsolidasyon etkileriyle kazanç büyüyormuş gibi görünebilir — her satın alma değerleme çarpanlarının ve riskin arttığı anlamına gelir. (s.384-386)
- **İLKE-149:** Hisse senedi opsiyon dağıtımı kabul edilebilir sınır: toplam hisselerin yaklaşık %3'ü (Zweig'in örnek aldığı en iyi uygulama). Bu eşiğin üstünde opsiyon dağıtımı mevcut hissedarları seyreltir. (s.400)
- **İLKE-150:** Kazanç bastırılmış ya da piyasanın gözden düşürdüğü şirketlerde fiyat düşüklüğü, gelecekteki algı değişimi yüksek getiri potansiyeli yaratır. “52 hafta dibi listesi” ve aşırı gözden düşmüş sektörler bir başlangıç noktası olarak kullanılabilir. (s.381-382)

**Chapter 15 — Stock Selection for the Enterprising Investor (Graham):**

- **İLKE-151:** Girişimci yatırımcının üstün getiri sağlayabileceği üç alan: (1) daha düşük F/K ile satılan ikincil/ünlenmemiş şirketler (bargain issues), (2) özel durumlar (special situations — birleşme, yeniden yapılandırma), (3) net cari varlık (net-net) fiyatlarının altındaki hisseler. Girişimci yatırımcı bu alanlara odaklanmalı, bu alanların dışında savunmacı gibi hareket etmelidir. (s.375-376)
- **İLKE-152:** Büyüme hisselerine (growth stocks) girişimci yatırımcı bile dikkatli yaklaşmalıdır — çünkü geleceğe yönelik iyimser tahmin hatası iç değeri aşında kalmaz, aşırı ödenen prim nedeniyle kayba dönüşür. (s.375)
- **İLKE-153:** Girişimci yatırımcının temel bargain testi: şirketin hissesi net cari varlıkların (işletme sermayesi) altında işlem görüyor mu? Eğer evet, ve şirket uzun vadeli borcu işletme sermayesini aşmıyorsa, bu hisse "kelepir” kategorisine girer — Graham'ın kendi portföyünde bu tür hisseler sürekli yer almıştır. (s.390-392)
- **İLKE-154:** Girişimci yatırımcının kelepir kriterleri (bargain issue, Graham'dan): (1) cari oran ≥1,5; (2) toplam borcu ≤ net cari varlıkların %110'u; (3) son 5 yılda zarar yok; (4) bugün temettü ödeniyor; (5) kazanç 5 yıl öncekinden yüksek; (6) fiyat net maddi varlıkların %120'sinden az. (s.391-392)
- **İLKE-155:** Özel durum (special situation) yatırımı: birleşme-satın alma arbitrajı, iflas reorganizasyonu, spin-off. Graham bu alanı girişimci yatırımcı için uygun görür; ancak her işlemin kendine özgü analizi gerektirir, sistematik bir tarama stratejisi yoktur. (s.393-394)

**Commentary on Chapter 15 (Zweig):**

- **İLKE-156:** Girişimci yatırımcı bireysel hisse seçimini portföyünün en fazla %10'u ile sınırlandırmalıdır; geri kalanı düşük maliyetli endeks fonu olmalıdır. Hisse seçimi denemesi en az 1 yıl hayali alım-satım ile test edilmeli, sonra S&P 500 endeks fonu ile kıyaslanmalıdır. (s.396-397)
- **İLKE-157:** Fiyat çöktüğünde ilgilenmek — profesyonel değer yatırımcıları (Tweedy Browne, Oakmark, FPA Capital, Torray Fund) 52 hafta dibindeki listeden başlar — modası geçmiş, sevilmeyen sektörler yüksek getiri potansiyeli taşır. (s.397)
- **İLKE-158:** Finansal tabloların anlaşılabilirliği yönetim kalitesinin vekili: Tablolar sade ve anlaşılır mı? “Olağandışı”/“tekrarlanmayan” kalemler gerçekten tek seferlik mi yoksa tekrar tekrar mı çıkıyor? Yöneticiler şirket hakkında mı konuşuyor, yoksa hisse fiyatı hakkında mı? (s.400, Torray)
- **İLKE-159:** “60 cent dollar” eşiği (Longleaf/Mason Hawkins): içsel değerin %60'ına veya daha altına işlem gören şirket hisseleri Güvenlik Marjı sağlar. Bu, “net-net” ile aynı felsefe, modern bir ölçüm pratikte farklı ölçeklidir. (s.399)

### Kısım 4 Formüller

- **FORMÜL-25:** Savunmacı Büyüklük Eşiği
  - Formül: Yıllık satışlar ≥ $100 milyon (sanayi) veya Toplam Varlıklar ≥ $50 milyon (kamu hizmetleri)
  - Zweig güncellemesi (2003): Piyasa değeri ≥ $2 milyar
  - QuaxisLabs karşılığı: `income_statement.sales` var; `market_cap` var — eşik etiketi eklenebilir

- **FORMÜL-26:** Savunmacı Cari Oran Kriteri (Sanayi)
  - Formül: Dönen Varlıklar ÷ Kısa Vadeli Yükmlülükler ≥ 2,0
  - QuaxisLabs karşılığı: `calculator.Ratios.current_ratio` MEVCUT

- **FORMÜL-27:** Savunmacı Borcu Işletme Sermayesi Kriteri
  - Formül: Uzun vadeli borcu ≤ Net cari varlıklar (Net working capital = Dönen varlıklar − Kısa vadeli yükmlülükler)
  - Kamu hizmetleri alternatifi: Toplam borcu ≤ 2 × Hisse senedi özkaynağı (defter değeri)
  - QuaxisLabs karşılığı: `long_term_debt` var, `working_capital` hesaplanabiliyor — oran eklenmeli

- **FORMÜL-28:** Savunmacı Kazanç İstikrarı
  - Formül: Son 10 yılın tamamında pozitif net kazanç (sıfır zarar yılı)
  - QuaxisLabs karşılığı: VERİ EKSİK — `trends.py` 10 yıllık seri tutmuyor

- **FORMÜL-29:** Savunmacı Temettü Kriteri
  - Formül: Son 20 yıl boyunca kesintisiz temettü ödemesi
  - QuaxisLabs karşılığı: VERİ EKSİK — temettü geçmişi verisi yok

- **FORMÜL-30:** Savunmacı Kazanç Büyüme Kriteri
  - Formül: HBK (Hisse Başı Kazanç) son 10 yılda en az %33 (1/3) artmış olmalı (başlangıç ve son 3 yıllık ortalamalar kullanılarak)
  - QuaxisLabs karşılığı: VERİ EKSİK — 10 yıllık EPS serisi yok

- **FORMÜL-31:** Savunmacı F/K Tavanı
  - Formül: Fiyat ≤ 15 × son 3 yıllık ortalama kazanç
  - Geçerli AA tahvil bazlı güncel hesaplama: P/E_max = 100 ÷ AA_tahvil_faiz_yuzdesi (2003: 100/4,6 = 21,7)
  - QuaxisLabs karşılığı: `pe_ratio` var; eşik etiketi eklenebilir

- **FORMÜL-32:** Graham Çarpan Kuralı (Graham Number)
  - Formül: F/K × PD/DD ≤ 22,5 (15×1,5 = 22,5; 9×2,5 = 22,5 — farklı kombinasyonlar geçerli)
  - Bireysel PD/DD tavanı: ≤1,5× defter değeri (bu Ch.14'ın resmi kriteri; Ch.8'ın ≤1,33× genel kuralından farklı — bkz. Kısım 2/3 notu)
  - QuaxisLabs karşılığı: `src/analysis/valuation.py` içinde `graham_number` ZATEN MEVCUT

- **FORMÜL-33:** Girişimci Cari Oran Kriteri
  - Formül: Dönen Varlıklar ÷ Kısa Vadeli Yükmlülükler ≥ 1,5
  - QuaxisLabs karşılığı: `current_ratio` var; savunmacı eşiğinden farklı etiketle eklenebilir

- **FORMÜL-34:** Girişimci Borcu Kriteri
  - Formül: Toplam borcu ≤ %110 × Net cari varlıklar (Net working capital)
  - QuaxisLabs karşılığı: ham veri var, oran eklenmeli

- **FORMÜL-35:** Girişimci Fiyat Kriteri
  - Formül: Hisse fiyatı ≤ %120 × Net maddi varlıklar (net tangible assets = Toplam varlıklar − maddi olmayan duran varlıklar − şerefiye)
  - QuaxisLabs karşılığı: VERİ EKSİK — goodwill ve intangible ayrı alan yok (bkz. Kısım 3 veri eksik notu)

- **FORMÜL-37:** ROIC (Yatırılan Sermaye Getirisi) — Davis/Zweig tanımı
  - Formül: ROIC = Sahip Kazancı (Owner Earnings) ÷ Yatırılan Sermaye (Invested Capital)
  - Sahip Kazancı = Faaliyet kârı + amortisman + şerefiye amortismanları − federal gelir vergi (ortalama oran) − hisse senedi opsiyonu maliyeti − zorunlu (maintenance) capex − sürdürülemez emeklilik fonu getirisi (2003’de >%6,5 olan kısım)
  - Yatırılan Sermaye = Toplam varlıklar − nakit − kısa vadeli yatırımlar − faizsiz cari yükmlülükler + geçmiş muhasebe şarzları (yatırılan sermayeyi azaltan)
  - Eşik: ROIC ≥ %10 çekici; %6-7 güçlü marka/geçici bulut varsa kabul edilebilir
  - QuaxisLabs karşılığı: VERİ EKSİK — capex, opsiyon maliyeti, emeklilik varsayımı ve goodwill amortismanı eksik

- **FORMÜL-38:** Kamu Hizmetleri Borcu Kriteri (savunmacı)
  - Formül: Toplam borcu ≤ 2 × Hisse senedi özkaynağı (defter değeri)
  - QuaxisLabs karşılığı: `equity` ve `total_debt` var; oran hesaplanabiliyor

### Kısım 4 Eşikler

| Metrik | Eşik | Yorum | Kaynak Bölüm |
|---|---|---|---|
| Sanayi satış büyüklüğü (savunmacı) | ≥$100M | Mutlak minimum; Zweig 2003: piyasa değeri ≥2B$ | Graham, Ch.14 |
| Kamu hizmetleri varlık büyüklüğü (savunmacı) | ≥$50M toplam varlık | Sanayi büyüklükeşiğinden farklı ölçüt | Graham, Ch.14 |
| Sanayi cari oran (savunmacı) | ≥2,0 | En yaygın Graham eşiği | Graham, Ch.14 |
| Kamu hizmetleri borcu/özkaynak (savunmacı) | ≤2,0× | Sanayi’nin net cari varlık kuralının alternatifi | Graham, Ch.14 |
| Cari oran (girişimci) | ≥1,5 | Savunmacıdan esnek | Graham, Ch.15 |
| Girişimci borcu/net cari varlıklar | ≤%110 | Savunmacının (%100) esnetilmiş hali | Graham, Ch.15 |
| F/K tavanı (savunmacı — sabit) | ≤15× 3yıl ort. | Graham'ın temel eşiği | Graham, Ch.14 |
| F/K tavanı (AA tahvil bazlı) | 100 ÷ AA_faiz_% | Dinamik eşik; 1970: 13,3×; 2003: 21,7× | Graham Ch.14, Zweig notu |
| Graham Çarpanı (F/K × PD/DD) | ≤22,5 | Her ikisi de eşik içindeyse tamam; biri içinde diğeri eşiği aşırsa toplam ≤22,5 aranır | Graham, Ch.14 |
| PD/DD tavanı (savunmacı — 6. kriter) | ≤1,5× | Ch.14'ın resmi kriteri (Ch.8'ın ≤1,33× genel kuralından farklı) | Graham, Ch.14 |
| Girişimci fiyat / net maddi varlıklar | ≤%120 | 1,2× maddi defter değeri | Graham, Ch.15 |
| ROIC (Zweig) | ≥%10 çekici; %6-7 kabul | Güçlü marka/geçici bulut var ise | Zweig, Comm.15 |
| Hisse opsiyon seyreltmesi | ≤%3 toplam hisse | Davis Funds en iyi uygulama eşiği | Zweig, Comm.15 |
| Bireysel hisse seçim oranı (girişimci) | ≤%10 portföy | Geri kalanı endeks fonu | Zweig, Comm.15 |
| Portföy hisse adedi (savunmacı) | 10-30 hisse | Alt: çeşitlilik; üst: analiz kapasitesi | Graham, Ch.14 |
| “60-cent dollar” eşiği (girişimci) | Fiyat ≤ içsel değerin %60’ı | Longleaf/Hawkins Güvenlik Marjı testi | Zweig, Comm.15 |

### Kontrol Listeleri (Kısım 4)

**KONTROL N — Graham'ın 7 Savunmacı Yatırımcı Kriteri (Ch.14 — NiHai Liste):**
1. Büyüklük: Yıllık satışlar ≥ $100M (sanayi) veya toplam varlıklar ≥ $50M (kamu hizmetleri)
2. Finansal Güç: Cari oran ≥2,0 (sanayi) VE uzun vadeli borcu ≤ net cari varlıklar; kamu hizmetleri: borcu ≤2× özkaynak
3. Kazanç İstikrarı: Son 10 yılın tamamında pozitif EPS (sıfır zarar yılı)
4. Temettü Geçmişi: Son 20 yıl boyunca kesintisiz temettü ödemesi
5. Kazanç Büyümesi: HBK son 10 yılda en az %33 artmış (3yıllık ortalama baş/son)
6. Ilimli F/K: Fiyat ≤ 15 × son 3 yıl ortalama kazanç (veya E/P ≥ AA tahvil faizi)
7. Ilimli PD/DD: PD/DD ≤1,5× VE F/K × PD/DD ≤22,5

**KONTROL O — Graham'ın Girişimci Yatırımcı Kriterleri (Ch.15 — 5 madde):**
1. Finansal Durum: Cari oran ≥1,5 VE toplam borcu ≤ %110 net cari varlıklar
2. Kazanç İstikrarı: Son 5 yılda zarar yok
3. Temettü: Bugün aktif temettü ödemesi var
4. Kazanç Trendi: Bugünkü kazanç, 5 yıl önceki kazancın üstünde
5. Fiyat: Net maddi varlıkların %120'sinden az (1,2× maddi defter değeri altı)

**KONTROL P — Yönetim Kalitesi Kontrolü (Zweig, Comm.15 — 4 test):**
1. Finansal tablolar anlaşılır ve sade mi (opasifikasyon yok)?
2. "Tekrarlanmayan" kalemler gerçekten tek seferlik mi (birden fazla çeyrek/yıl tekrarlamıyor mu)?
3. Yöneticiler şirket hakkında mı konuşuyor, yoksa hisse fiyatı hakkında mı?
4. Yöneticiler şirkette anlamlı miktarda hisse sahibi mi (opsiyon değil, nakit alım)?

### Kırmızı Bayraklar (Kısım 4)

- **BAYRAK-39:** Analist konsensüsü “iforward kazanç” tahmini üzerinden değerleme — Wall Street analisti tahminleri sistematik olarak aşırı iyimserdir; Graham'ın tüm kriterleri gerçekleşmiş/görülmüş kazanç üzerinden çalışır. (Zweig, Comm.14)
- **BAYRAK-40:** Bir şirketin şerefiyesinin (goodwill) defter değerinin önemli bir kısmını oluşturması — bu, ya varlık değerinin çok üstüne alım yapıldığının ya da hissenin uzun süredir aşırı primli işlem gördüğünün işareti; her ikisi de defter değerini değerterleme aracı olarak saptırır. (Zweig, Comm.14)
- **BAYRAK-41:** Seri alıcı (serial acquirer) şirket — yılda birden fazla şirket satın alma organik büyüme değil konsolidasyon etkileriyle büyüme anlamına gelir; her satın alma riskleri ve değierlemesi ayrı analiz ister. (Zweig, Comm.14)
- **BAYRAK-42:** Hisse senedi opsiyonu seyreltmesi >%3 — yönetim mevcut hissedarların aleyhine opsiyon dağıtıyor demektir; hisse başı kazanç hesaplamaları seyreltilmiş (diluted) bazında değerlendirilmeli. (Zweig, Comm.15)
- **BAYRAK-43:** EPS/net karda düşme olmaksızın opsiyonların artması — opsiyon maliyeti hesaba katılmadan raporlanan kazanç şişirilmiş görünüyor olabilir; ROIC hesabında opsiyonların nakit maliyeti düşlmeli. (Zweig, Comm.15)

---

## Kısım 5: Ch.16-18 + Commentary (s.447-541)

**Chapter 16 — Convertible Issues and Warrants (Graham):**

- **İLKE-160:** Dönüştürülebilir tahvil/imtiyazlı hisse hem için her iki taraf için de mükemmel yönünde pazarlanır (yatırımcıya koruma + yukarı yön katılım, ihraccıya düşük faizle finansman). Ancak bu dengeli görünüş kural olarak bir tarafın diğerini subsıdize etmesi anlamına gelir — yatırımcı dönüştürme hakkı karşılığında kalite veya getiriden fedakarlık eder. (s.447-448)
- **İLKE-161:** Dönüştürülebilir tahvil kuralları: (1) Dönüştürme fiyatı, ihracında hisse fiyatının tipik olarak %15-20 üstünde belirlenir; (2) Dönüştürme priminin çok yüksek olması hisse senedinin yükseliş potansiyelini azaltır; (3) Dönüştürme hakkı zaten vade bitimindeş değimine de tutunulabilir. (s.449-451)
- **İLKE-162:** “Dönüştürülebilir tahvili asla dönüştürme” (Graham'dan pratik kural): Tahvili hisse senedine dönüştürmek, aşağı yönlü korumayı tamamen kaybedip salt hisse riskine geçmek anlamına gelir; hisse senedi isteniyorsa doğrudan alınmalıdır. (s.454-455)
- **İLKE-163:** Hisse senedi alım varantları (stock-option warrants) ince havadan yaratılmış finansal araçlardır; içsel ekonomik değerleri yoktur. Varant sahipleri ne faiz/temettü alır ne de oy hakkına sahiptir; sadece speklatif değer taşırlar ve bunu da şirketin hissesi yükselmeli varsayımıyla. (s.457-458)
- **İLKE-164:** Dönüştürülebilir menkul kıymet ihracı boomları, boğa piyasalarının zirvesine yakın dönemlerde yoğunlaşır — bu, piyasanın üst seviyelerine işaret eden önemli bir kontrerian göstergedir. (s.460)

**Commentary on Chapter 16 (Zweig):**

- **İLKE-165:** Dönüştürülebilir tahvil yatırımında temel test: Tahvil özelliklerine göre (faiz + kalite) cazip mı? Evet ise ön planda düzenleyici tahvil olarak, dönüştürme hakkı bonus olarak düşün. "Dönüştürme cazip olduğunda tahvilin kalitesi daha kötü olur" Zweig'ın pratik özeti. (s.469-470)

**Chapter 17 — Four Extremely Instructive Cases (Graham):**

- **İLKE-166:** Ling-Temco-Vought (LTV) vakası: Aşırı agresif finansal kaldıraç ve konglomera yapısıyla hızlı büyen bir şirket, dış koyu kötüleşince çökebilir. Kaldıraç büyüklüğü, çökün de hızını ve derinliğini artırır. (s.480-485)
- **İLKE-167:** NVF Corp./Sharon Steel vakası: Satın alma ödemelerini kamufle etmek için muhasebe uygulamalarının istismarı (prim üzerinde satın alınan tahvillerin iskontosunun “kazanç” olarak raporlanması) ciddi kırmızı bayrak oluşturur. (s.485-490)
- **İLKE-168:** Penn Central vakası: Tüm zararların ve maliyetlerin aynı yıla yığılması (“Big Bath” muhasebesi), ardından gelen yıllarda suni kârlılık illüzyonu yaratır. Kamu kuruluşu olması düzenleyici korumanın var olduğu algısı oluşturursa, yatırımcı temel analizi atlar. (s.459-462)
- **İLKE-169:** Halka arz edilen şirketlerde fiyat/defter değeri oranı ilk günden itibaren kritik bir değerleme ölçüttür; IPO fıyatları çoğunlukla aşırı yüksektir. (s.463-466, AAA Enterprises vakası)

**Commentary on Chapter 17 (Zweig):**

- **İLKE-170:** "Büyüme” hikayesi anlatılırken şirketin mevcut işinin kalitesi ve sürdürülebilirliği incelenmezse, o büyüme ya varlık tahrip eden yatırımlarla ya da muhasebe maharetleriyle geliyordur. Şirketin neden para kazandığına, nasıl yenilemeye devam edeceğine odaklan. (s.494-497)
- **İLKE-171:** Karmaşık finansal yapı (holding şirketi altında çok katmanlı şirket) analiş zorluğunu artırır; şeffaflık eksikliği kural olarak yatırımcı için dezavantajdır. (s.494-497)

**Chapter 18 — A Comparison of Eight Pairs of Companies (Graham):**

- **İLKE-172:** Graham'ın 8 şirket çifti analizi genel dersi: Aynı sektörden iki şirket arasında buyuk fiyat-değer farkı neredeyse her zaman yatay piyasada sürülemez. Ucuz taraf ortalamaya dönerken pahalı taraf aşağı düçer. (s.509-521)
- **İLKE-173:** Şirketin kazanç getirisi (earnings yield = 1/PE) her zaman tahvil faizleriyle kıyaslanmalı; eğer kazanç getirisi tahvil faizinden düşük ise hisse senedi (risk primi hesaba katıldığında) yeterli güvenlik marjı taşımıyor demektir. (s.521-529)

**Commentary on Chapter 18 (Zweig):**

- **İLKE-174:** CMGI vs CGI vakası (1999-2002): CMGI çök yüksek F/K ile yyıldız; CGI <10 F/K ve %4+ temettü getirisıyle gözden düşmüştü. 2001-2002'de CMGI $28'dan $0,74'e, CGI ise $20'dan $11'e düştü. Fiyat/değer ayrımı korundu. (s.530-535)
- **İLKE-175:** Fazla nakit biriktiren ve bunu hissedarlara iade etmeyen şirket (Microsoft 2003: $43 milyar nakit rezervi) özkaynak verimliliğini düşürüyor demektir. Graham'a göre:“Bu fazla nakit dış hissedarına nadiren fayda sağlar.” (s.532-535)

### Kısım 5 Formüller

- **FORMÜL-39:** Dönüştürülebilir Tahvil Kazanç Getirisi Testi
  - Formül: Dönüştürülebilir tahvilin kazanç getirisi (YTM) ≥ Benzer kalite düz tahvil getirisi + Değer marjı. Aksi halde dönüştürme hakkı için çok fazla ödeniyor demektir.
  - QuaxisLabs karşılığı: KAPSAM DIŞI — QuaxisLabs tahvil analizi yapmıyor

### Kısım 5 Eşikler

| Metrik | Eşik | Yorum | Kaynak Bölüm |
|---|---|---|---|
| Dönüştürme premi (konvertibl tahvil) | Tipik %15-20 üstünde belirlenir | Bu primin çok yüksek olması hisse senedi katilimini azaltır | Graham, Ch.16 |
| Kazanç getirisi (E/P) vs tahvil faizi | E/P ≥ tahvil faizi | Aksi halde hisse yeterli Güvenlik Marjı taşımıyor | Graham, Ch.18 |

### Kırmızı Bayraklar (Kısım 5)

- **BAYRAK-44:** Dönüştürülebilir menkul kıymet ihracında patlama — bu, boğa piyasası zirvesine yakınılıyor işareti; böyle dönemlerde ihracı yapılan dönüştürülebilir tahviller genellikle kalite ve getiri olarak yetersizdir. (Ch.16, s.460)
- **BAYRAK-45:** “Big Bath” muhasebesi — şirketin kötü bir yılda gelecekteki olası tüm zararları ve maliyetleri tek yıla yığması; ardından gelen yıllarda suni kârlılık yarattığı için analistler onu "temizlendi, düzeldi" olarak görür. (Ch.17, s.462)
- **BAYRAK-46:** Muhasebe kazancını şişiren satın alma: İskontoyla geri alınan tahvillerin prim kısmını “kazanç” olarak raporlamak (NVF/Sharon Steel), veya konsolidasyonun yarattığı çift sayımın örtübas edilmesi. (Ch.17, s.485-490)
- **BAYRAK-47:** Aşırı nakit birikimini dağıtmayan yönetim: fazla nakit özkaynak verimliliğini (ROE) düşürür ve çoğu zaman düşük getirili projelere harcanır. (Zweig, Comm.18)
- **BAYRAK-48:** Çok katmanlı konglomera/holding yapısı — yönetimin kendi yönetimini denetlediği, dış hissedara şeffaflığın en aşından olduğu yapı (LTV vakası). (Ch.17, s.480-485)

---

## Kısım 6: Ch.19-20 + Postscript + Commentary (s.542-596)

**Chapter 19 — Shareholders and Managements: Dividend Policy (Graham):**

- **İLKE-176:** Hissedarlar aktif/sorgulayan bir rol üstlenmelidir — şirket yönetiminin performansını sorgulamak ve düşük getiri dönemlerinde temettü artırımı veya karsam hisse geri alımı talep etmek hakları arasındadır. (s.542-544)
- **İLKE-177:** Yeniden yatırım (retained earnings) haklı gösterilmesi için: Yeniden yatırılan her birim kazanç gelecekte en az bir birim piyasa değeri yaratmalıdır; bu koşul sağlanmazsa kazanç dağıtılmalıdır. (s.544-546)
- **İLKE-178:** Graham'ın temettü dağıtım politikası: Kazancının %60-75'ini temettü olarak ödeyen şirket, yöneticilerin akılsızca harcama riski taşıyan nakitı azaltır; bu oran tercih edilmelidir. (s.545-546)
- **İLKE-179:** Hisse geri alımı (buyback) yalnizca hisse fiyatı gerçek değerinden UCUZ olduğunda hissedara değer katar; zirve fıyatlarında geri alım yapmak şirket sermayesinin israfıdır. (s.546-548)
- **İLKE-180:** Arnott & Asness araştırması (Zweig): Düşük temettü ödeyen şirketlerde gelecek 10 yıllık kazanç büyümesi ortalama 3,9 puan daha düşük çıkmıştır — yüksek temettü düşük temettüden ortalama 3,9 puan fazla kazanç büyümesi üretiyor. Temettü ödemek, yöneticilerin elinden nakitı çıkarıp israfı engeller. (Zweig, Comm.19)
- **İLKE-181:** Nissim & Ziv (Columbia) araştırması: Temettü artırımı yapan şirketler, sonraki 4 yılda hem daha iyi hisse performansı hem de daha yüksek kârlılık gösteriyor. Temettü artırımı, yönetimin geleceğe güven işareti olarak değerlendirilebilir. (Zweig, Comm.19)

**Commentary on Chapter 19 (Zweig):**

- **İLKE-182:** Hisse geri alım programında kırmızı bayrak: Hisse fiyatı historik yükseklerdeyken “hissedar değeri artırıyoruz” söylemiyle buyback yapan yönetim — bu kararlar sıklıkla CEO'ıların kendi opsiyonlarının değerini korumak için yapılır. (s.559-562)
- **İLKE-183:** Hissedarın şirket yönetimiyle ilgili kaldıraçları: (1) Düşük performanslı yöneticileri oy hakkını kullanarak reddetmek; (2) birikim fonlarında shareholder-friendly yönetim talep etmek; (3) düşük gider oranlı fonları tercih ederek elini güçlendirmek. (s.557-568)

**Chapter 20 — “Margin of Safety” as the Central Concept (Graham):**

- **İLKE-184 (KİTABIN MERKEZİ KAVRAMI):** GÜVENLİK MARJI = ödenen fiyat ile hissenin gerçek değeri (intrinsic value) arasındaki olumlu fark. Bu fark büyük olduğunda: (a) tahmin hatalarına karşı tampon var, (b) aşağı risk sınırlı, (c) yukarı potansiyel orantısız büyük. (s.512-514)
- **İLKE-185:** Büyüme hisselerinde Güvenlik Marjı çok daha zordur: Tahmin hatası yüksek büyüme varsayımını çürttüğünde hisse aşırı değerlidir hem de güvenlik tampon unu yitirmiştir — çift olumsuz etki. Sabit varlık değerli şirketlerde marj daha kolay sağlanabilir. (s.513-515)
- **İLKE-186:** Güvenlik Marjı ve çeşitlilik: Bireysel bir hissede marj yanlış hesaplanabilir, ama 20-30 hisseden oluşan istatistiksel olarak yeterli bir portföyde bu hataların telafisi güvenlik marjını daha güvenilir kılar — sigorta poliesi analy mantigi. (s.515-516)
- **İLKE-187:** Matematiksel karmaşıklık uyarısı — Graham'dan: “44 yıllık Wall Street deneyimimde hisse değerlemelerinde basit aritmetik veya en temel cebir ötesine geçen güvenilir bir hesaplama hiç görmedim. Kalkülüs veya yüksek cebir devreye girince, bu spekülasyona teöri görünümü verme girisimi olarak değerlendir.” (s.570-571)
- **İLKE-188:** Güvenlik marjı her tür hisse için farklı uygulanır: (1) Kalkınmış/tahvil benzeri hisseler için: kazanç getirisi > tahvil faizi, (2) Büyüme hisseleri için: tahmin edilen büyüme gerçekleşmese bile makul değer olan fiyat ödenmeli, (3) Bargain hisseleri için: net-net veya defter değerinin altı doğrudan önemli bir güvenlik marjı sağlar. (s.516-518)

**Commentary on Chapter 20 (Zweig):**

- **İLKE-189:** Güvenlik Marjı ile yönetim kalitesi arasındaki ilişki: Kötü yönetim bile düşük fiyatta alınabilir (yeter ki fiyat kötü yönetimi de fiyatlamış olsun); ama Graham tercihan iyi yönetimli ve ucuz şirkette hem fiyat hem kalite avantajını bir arada istedi. (s.521-524)
- **İLKE-190:** Nasıl daha zenginleşiyorsunuz? Kural bir, asla para kaybetme. Kural iki, kural bir'i unutma (Buffett). Güvenlik Marjı bu ikinci kuralı uygulamanın önündeki disiplindir. (s.524-526)

### Kısım 6 Formüller

- **FORMÜL-36:** Güvenlik Marjı Kazanç Getirisi Testi (hisse senedi)
  - Formül: Kazanç Getirisi (EPS / Fiyat = 1/F/K) >> Yüksek kaliteli tahvil getirisi
  - Aşırı minimal sınır: E/P ≥ AA tahvil faizi (bu şart sağlanmadan hisse satın alma)
  - Tercihli hedef: E/P tahvil faizinden anlamlı ölçüde yüksek (örneğin %2-3 prim)
  - QuaxisLabs karşılığı: `1/pe_ratio − risk_free_rate` hesaplanabilir; `_RISK_FREE_RATE_PCT` mevcut ama canli veri değil

### Kısım 6 Eşikler

| Metrik | Eşik | Yorum | Kaynak Bölüm |
|---|---|---|---|
| Kazanç dağıtım oranı (payout ratio) | %60-75 önerilen | Yöneticilerin elinden nakiti çıkarır | Graham, Ch.19 |
| Arnott & Asness temettü etkisi | Yüksek temettü → +3,9 puan 10y kazanç büyümesi | Akademik destek | Zweig, Comm.19 |
| Buyback kıstası | Sadece hisse gerçek değerden ucuzsa | Piyasa zirvesinde geri alım israf | Graham/Zweig, Ch.19 |
| Güvenlik Marjı testi | E/P ≥ AA tahvil faizi | Minimum; tercihen anlamlı prim | Graham, Ch.20 |

### Kırmızı Bayraklar (Kısım 6)

- **BAYRAK-49:** Hisse fiyatı zirvedeyken “hissedar değeri yaratıyoruz” söylemiyle buyback programı açıklanması — genellikle CEO'ıların kendi opsiyonlarının değerini korumak için yapılır. (Zweig, Comm.19)
- **BAYRAK-50:** Yönetime yüksek kazanç büyümesi vadeden ama özkaynak getirisini (ROE) ve temettü ödemelerini azaltan şirket — “yeniden yatırım” aslında varlık tahribi olabilir. (Graham, Ch.19)
- **BAYRAK-51:** Valasyonda yüksek matematik (diferansiyel denklem, kompleks stokastik model) kullanılması — Graham'ın uyarısı: karmaşıklık, spekülasyona bilimsel görünüm verir ama kesinlik yaratmaz; basit aritmetik ile bulunamayan Güvenlik Marjı spekülasyona dönüşmüştür. (Graham, Ch.20)

---

## Kısım 7: Appendix 1-7 + Final Kontrol (s.571-638)

**Appendix 1 — The Superinvestors of Graham-and-Doddsville (Warren Buffett, 1984):**

- **İLKE-191:** Piyasa etkinliği (EMH) teorisi, Graham-ve-Doddsville'ın değer yatırımcılarının uzun vadeli sistemli başarısıyla çürutülmüştür: Buffett, Munger, Ruane, Schloss, Knapp ve diğer Graham okul mezunları 20+ yıl süreyle S&P 500'ü geçti. Aynı entelektel kaynaktan gelen 9 farklı portföy bir arada anlamlı bir örntü oluşturuyor, bu tesadüf olamaz. (Appendix 1, s.537-558)
- **İLKE-192:** Buffett'in özeti: Değer yatırımının özü = bir işin değerinin çok altında ödemek. “Fiyat nedir biliyorsunuz, değer ne olduğunu araştırmanız gerekiyor.” (Appendix 1, s.537)
- **İLKE-193:** Graham-Newman Corp. 1936-1956 arası yıllık ortalama %20+ getiri sağladı (piyasa verisi ile örtlü). Buffett Partnership 1957-1969 yıllık ortalama ~%29,5 (Dow vs ~%7,4). Walter Schloss 1955-1983 28 yıl yıllık %21,3 (S&P: %8,4). Bu veriler tek seferlik değil; yatay, kükmlü ve tekrar eden bir performans süreklemesidir. (Appendix 1, Tablolar)
- **İLKE-194:** Sektörel çeşitlilik olmaksızın (kimi deniz taşımacılığında, kimi sigortada, kimi tekstilde) çok farklı alanlarda bu aynı metodolojinin işlemesi, sonucun sektöre özel olmadığını gösteriyor. Yatırım metodolojisinin üstünlüğü kalıcı ve genel. (Appendix 1)

**Appendix 2-7 (Notlar ve Istatistiksel veriler):**

- **İLKE-195:** Appendix 2 (S&P hisse geçmiş verileri 1871-1970): Uzun dönemde reel hisse getirisi çok değişken; tek bir 20 yıllık dönem bile çok düşük ya da çok yüksek getiri üretebilir. Uzun vadeli ortalama güvenilirliği, kısa vadeli tahmin gücünden çok daha yüksek. (s.559-565)

### Kısım 7 Eşikler (Appendix 1 — Graham mezunları performansı)

| Yatırımcı | Dönem | Yıllık Getiri | Referans endeks | Kaynak |
|---|---|---|---|---|
| Walter Schloss | 1955-1983 (28 yıl) | %21,3 | S&P %8,4 | Appendix 1 |
| Tom Knapp (Tweedy Browne) | 1968-1983 | %20,0 | S&P %7 | Appendix 1 |
| Warren Buffett Partnership | 1957-1969 | ~%29,5 | Dow ~%7,4 | Appendix 1 |
| Bill Ruane (Sequoia Fund) | 1970-1984 | %18,2 | S&P %10,0 | Appendix 1 |
| Charlie Munger | 1962-1975 | %19,8 | Dow %5,0 | Appendix 1 |
| Rick Guerin | 1965-1983 | %32,9 | S&P %7,8 | Appendix 1 |

### Kırmızı Bayraklar (Kısım 7)

- **BAYRAK-52:** Uzun vadeli değer yatırımcılarının performansını “tesadüf” ile açıklamaya çalışmak — 9 bağımsız yatırımcı, aynı metodoloji, 20+ yıl, farklı sektörler: bu istatistiksel tesadüf olamaz. (Buffett, Appendix 1)

---

## Kısım 4-7 Uygulama Notları

1. **Ch.14'ın 7 Kriteri KiTABIN nİHAI SAVUNMACI SÉÇİM LİSTESİDİR** (KONTROL N) — Ch.5'ın 4 kuralı ve Ch.13'ın 7 kriteri ile büyük örtüşme var ama Ch.14 en olgun, en nicel ve en çapraz referanslı versiyondur. QuaxisLabs'ın açık veri boşlukları: (1) 10+ yıllık EPS serisi, (2) temettü geçmişi, (3) net maddi varlıklar (şerefiye/maddi olmayan eksik). Bu üç boşluk 7 kriterin 3'ünün uygulanmasını engeller.
2. **ROIC (FORMÜL-37 — Zweig/Davis) QuaxisLabs'ın en önemli eksik ratio’su**: Capex (zorunlu), opsiyon maliyeti, emeklilik varsayımı düzeltmeleri gerektiriyor — bunların hiçbiri mevcut veri modelinde yok. Kısa vadeli alternatif: mevcut `roe_annualized` + `operating_cash_flow` kombinasyonu kaba bir vekil olarak kullanılabilir.
3. **Graham'ın ÜS SÜRECİ KAVRAMSAL UYARISI**: Değerleme ne kadar matematik-yoğun olursa, sonuç o kadar spekülatiftir. Basit aritmetik (F/K, PD/DD, E/P vs tahvil faizi) 44 yıllık Wall Street deneyiminde tek güvenilir araç olarak kanıtlanmıştır — bu, QuaxisLabs'ın oran-tabana dayalı basit skoring yaklaşımının kitap felsefesiyle uyumlu olduğunun teyididir.
4. **Appendix 1 (Superinvestors) Graham yatırım felsefesinin en güçlü ampirik kanıtıdır**: EMH'ye karşı en kuvvetli argüman, teorik değil, gerçek portföy performans verileridir. Bu veriler (Schloss: 28y/+21,3%, Buffett Partnership: 13y/+29,5%, vb.) QuaxisLabs'in değer-odaklı skoring mimarisi için teorik meşruiyet sağlar.
5. **Temettü politikası (Ch.19): %60-75 payout eşiği ve buyback krit** QuaxisLabs kapsamındadır (payout_ratio hesaplanabilir) ama buyback analizi için hisse geri alım miktarı verisi eksik.

**BİLGİ ÇIKARMA SÜRECİ TAMAMLANDI.** (01_graham_akilli_yatirimci.md tüm bölümleriyle işlenmiştir.)
