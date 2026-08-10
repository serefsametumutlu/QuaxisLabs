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
