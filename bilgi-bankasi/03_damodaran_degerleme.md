# 03 — Damodaran on Valuation (Aswath Damodaran, 2nd Ed., 2006)

## Meta

- **Kaynak:** `kitaplar/damodaran-on-valuation.pdf` (929 PDF sayfası, metin katmanı VAR — OCR gerekmedi, doğrudan `get_text()`).
- **Kullanıcı onayı (bu turdan önce):** Kitap 9 ana kısma bölünerek işlenecek (bkz. `bilgi-bankasi/_ilerleme.md` — "03 — Damodaran on Valuation" bölümü, tam plan tablosu).
- **Bu dosyanın kapsamı — SADECE KISIM 1 (bu turda tamamlandı):**
  - Chapter 1: Introduction to Valuation (PDF s.15-49)
  - Chapter 2: Estimating Discount Rates (PDF s.50-117)
  - PDF sayfa aralığı: 15-117. Sayfa dönüşümü (doğrulanmadı, sonraki turda teyit edilecek): kitap sayfası ≈ PDF index − 14.
- **Kalan kısımlar (henüz işlenmedi):** Kısım 2-9 (Ch.3-18 + appendix'ler) — bkz. `_ilerleme.md`'deki tam plan.
- **ID numaralandırması bu kitapta İLK turdur** — İLKE-01, FORMÜL-01, BAYRAK-01'den başlar. Kitaplar arası ID alanı BAĞIMSIZDIR (bkz. SKILL.md kural 3 — global referans dosya öneki ile: `03/İLKE-01`).
- **Yatırım felsefesi (kitap geneli, Kısım 1'den):** Damodaran, DCF'i (içsel değer arayışı), göreli değerlemeyi (piyasanın ortalamada doğru fiyatladığı varsayımı) ve koşullu talep/opsiyon değerlemesini (DCF'in değerleyemediği optionality) BİRBİRİNİ DIŞLAMAYAN, farklı senaryolara uygun ARAÇLAR olarak sunar — "hangisi doğru" değil "hangisi bu varlık için doğru" sorusu merkezdedir. Analist önyargısının (bias), belirsizliğin ve model karmaşıklığının değerlemenin KENDİSİ kadar önemli üç güç olduğunu, "parsimoni ilkesi" (en basit yeterli modeli kullan) ile karmaşıklığın bilinçli sınırlandırılması gerektiğini vurgular.
- **Hedef şirket türü / kapsam dışı türler:** Kitap kamuya açık/özel TÜM şirket türlerini kapsar (Kısım 1'de genç/özel şirketler, gelişmekte olan piyasa şirketleri için özel düzeltmeler tanıtıldı — total beta, ülke risk primi/lambda). QuaxisLabs'ın kapsamı (BIST/NASDAQ/Crypto tekil varlık analiz motoru — portföy yönetimi YAPMAZ) ile büyük ölçüde örtüşüyor; kitaptaki M&A/kontrol primi/APV gibi kurumsal-finans-özel konular (sonraki kısımlarda gelecek) muhtemelen kısmen kapsam dışı olacak.
- **OCR kalite notu:** Bu PDF'te OCR YOK (metin katmanı var), bu yüzden Graham/Buffett kitaplarındaki OCR hata riski BURADA YOKTUR. Ancak kitaptaki formüller genellikle görsel/denklem olarak gömülü (LaTeX benzeri render) ve düz metin çıkarımında KAYBOLUYOR (`get_text()` formülün YERİNE boşluk/hiçbir şey bırakıyor, sadece formülü ÇEVRELEYEN metin ve değişken tanımları okunabiliyor) — bu yüzden formüllerin çoğu, kitaptaki DEĞİŞKEN TANIMLARI ve SONRAKİ SAYISAL ÖRNEKLERDEN (Illustration 2.1-2.8) TERS MÜHENDİSLİKLE yeniden inşa edildi, kitaptaki orijinal denklem gösteriminin BİREBİR KOPYASI DEĞİLDİR (telif kuralına zaten uygun — fikir kendi cümleleriyle damıtılıyor).

---

## İlkeler

**Chapter 1 — Introduction to Valuation:**

- **İLKE-01:** Sağlam yatırımın temel postülatı: bir yatırımcı bir varlık için GERÇEK DEĞERİNDEN fazla ödememelidir. "Değer bakanın gözündedir, başka biri daha yüksek fiyata alacaksa her fiyat haklıdır" argümanı YANLIŞTIR — bu, müzikal sandalyeler oyununa benzer ("müzik durduğunda nerede olacağım?" sorusuna cevap vermeden oynamak). (s.15-16)
- **İLKE-02:** Değerleme sürecinde genellikle İHMAL EDİLEN üç bileşen: analistlerin sürece getirdiği ÖNYARGI, kaçınılmaz BELİRSİZLİK ve modern teknolojinin getirdiği KARMAŞIKLIK. (s.15)
- **İLKE-03:** Önyargının 3 kaynağı: (1) hangi şirketin değerleneceği seçiminin KENDİSİ rastgele değildir (basın/uzman görüşü önceden algı oluşturur); (2) bilgi toplama sürecinde şirketin kendi (en iyi ışıkta sunulmuş) anlatımı + diğer analistlerin görüşleri + PİYASA FİYATININ KENDİSİ önyargı ekler; (3) kurumsal baskılar — Wall Street'te SATIŞ tavsiyesine kıyasla YAKLAŞIK 5 KAT fazla ALIM tavsiyesi verilir (yatırım bankacılığı ilişkileri, portföy yöneticisi baskısı). (s.17)
- **İLKE-04:** Önyargının 3 tezahür biçimi: (1) GİRDİ SEÇİMİNDE iyimser/kötümser varsayımlar; (2) "DEĞERLEME SONRASI KURCALAMA" (postvaluation tinkering) — beklenen sonuca ULAŞMAK için büyüme/risk varsayımlarını GERİYE DÖNÜK revize etmek; (3) değeri OLDUĞU GİBİ bırakıp farkı sinerji/stratejik gerekçe gibi NİTEL bir faktöre YÜKLEMEK (özellikle M&A'da yaygın). (s.18)
- **İLKE-05:** Önyargıyı azaltmanın 5 yolu (kurumsal ölçekte): kurumsal baskıları azalt, değerlemeyi ödül/ceza yapısından AYIR, değerleme TAMAMLANMADAN önce kamuya güçlü bir fiyat taahhüdü VERME (precommitment yapma), öz-farkındalık geliştir, ÖNYARGILARINI AÇIKÇA RAPORLA (Bayesçi istatistikteki "prior" açıklama disipliniyle aynı mantık). (s.19-20) [→ bkz. KONTROL LİSTESİ A]
- **İLKE-06:** Belirsizlik 3 kategoriye ayrılır: TAHMİN belirsizliği (girdiyi modele çevirirken yapılan hata — TEK analistin kontrol edebileceği kategori), ŞİRKETE ÖZGÜ belirsizlik (şirketin beklenenden çok daha iyi/kötü performans göstermesi), MAKROEKONOMİK belirsizlik (faiz oranı/ekonomi genelinde beklenmedik değişim). Olgun/döngüsel şirketlerde makro belirsizlik, genç/teknoloji şirketlerinde tahmin+şirkete özgü belirsizlik baskındır. (s.20-21)
- **İLKE-07:** Analistler MAKROEKONOMİK görüşlerini (örn. "faizler yükselecek") değerlemeye KATMAMALI, sadece ŞİRKETE ÖZGÜ bilgiye (büyüme süresi, büyüme hızı, artık getiri) odaklanmalıdır — aksi halde değerlemeyi kullanan kişi, sonucun ne kadarının şirket analizinden ne kadarının analistin makro görüşünden geldiğini AYIRT EDEMEZ. (s.23)
- **İLKE-08 ("Değerlemenin Getirisi"):** Değerlemenin FAYDASI, belirsizliğin EN YÜKSEK olduğu durumlarda EN YÜKSEKTİR — bir değerlemenin kalitesi HASSASİYETİYLE (precision) değil, DİĞER yatırımcıların tahminlerine göre GÖRECELİ hassasiyetiyle ölçülür. Olgun bir şirketi hassas değerlemek "daha iyi" bir değerleme YAPMAZ; asıl edge, belirsizliğe rağmen ısrar edip TAHMİN YAPMAKTAN gelir. (s.24)
- **İLKE-09 ("Parsimoni İlkesi"):** Bir varlığı üç girdiyle değerleyebiliyorsan BEŞ kullanma; üç yıllık nakit akışı tahmini yeterliyse ON yıl tahmin etmek "belaya davetiyedir." Karmaşıklığın 3 somut maliyeti: BİLGİ AŞIRI YÜKLENMESİ (garbage in, garbage out riski artar), "KARA KUTU SENDROMU" (analist artık modelin iç işleyişini anlamaz, özellikle TİCARİ/proprietary modellerde tehlikelidir), BÜYÜK/KÜÇÜK VARSAYIM AYRIMININ KAYBOLMASI (değeri 2 katına çıkaran bir marj varsayımı, değeri neredeyse etkilemeyen bir alacak/satış oranı varsayımıyla aynı "ağırlıkta" görünür hale gelir). (s.25-26) [→ BAYRAK-02]
- **İLKE-10:** 3 temel değerleme yaklaşımı VARDIR ve her biri farklı varsayımlarla farklı değer üretebilir: (1) İNDİRGENMİŞ NAKİT AKIŞI (DCF) — değer = beklenen nakit akışlarının bugünkü değeri; (2) GÖRELİ DEĞERLEME — karşılaştırılabilir varlıkların fiyatlaması; (3) KOŞULLU TALEP (opsiyon) DEĞERLEME — opsiyon fiyatlama modelleriyle optionality içeren varlıkları değerleme. (s.27)
- **İLKE-11:** DCF'in İKİ farklı riski VARDIR: DEFAULT RİSKİ (borç ödeme taahhüdünü yerine getirememe olasılığı — borcun maliyetini belirler) ve GETİRİ DEĞİŞKENLİĞİ RİSKİ (gerçekleşen getirinin beklenenden sapması — özkaynağın maliyetini belirler). Faiz gideri vergiden düşülebilir olduğundan borcun VERGİ SONRASI maliyeti daha düşüktür. (s.32)
- **İLKE-12:** "Devam eden işletme" (going concern) değerlemesi ile "varlık bazlı" değerleme AYRIMI: going concern hem MEVCUT varlıkları hem GELECEKTEKİ büyüme varlıklarını (Figure 1.1 — "varlıklar yerinde" + "büyüme varlıkları") değerler; varlık bazlı değerleme SADECE mevcut varlıkları tek tek değerleyip toplar — büyüme fırsatı yüksek şirketlerde varlık bazlı değerleme DAHA DÜŞÜK sonuç verir. Tasfiye değerlemesi, varlık bazlı değerlemenin "hemen satılmalı" varsayımlı özel bir durumudur (aciliyet indirimi içerir). (s.29-30)
- **İLKE-13:** Firma (enterprise) değerlemesi vs özkaynak değerlemesi AYRIMI: firma değerlemesi TÜM finansman kaynaklarının bileşik maliyetini (cost of capital/WACC) kullanarak "borç ödemeleri ÖNCESİ, yeniden yatırım SONRASI" serbest nakit akışını (FCFF) iskonto eder; özkaynak değerlemesi SADECE özkaynak maliyetini (cost of equity) kullanarak "borç ödemeleri SONRASI" serbest nakit akışını (FCFE) iskonto eder. DOĞRU yapıldığında ikisi de AYNI özkaynak değerini vermelidir (firma değerinden borç claim'lerini netleştirerek). (s.30-31)
- **İLKE-14:** Beklenen büyüme tahmininde 3 jenerik yöntem VARDIR ve yazar 3.'sünü ÖNERİR: (1) geçmiş büyüme oranı (geleceğe zayıf gösterge), (2) yönetim/analist tahminleri (önyargılıdır, İLKE-03'teki alım/satım tavsiyesi asimetrisiyle AYNI kök sorun), (3) TEMEL büyüme — özkaynak modelinde tutma oranı (retention ratio) × özkaynak getirisi (ROE); firma modelinde yeniden yatırım oranı × sermaye getirisi (ROC). Temel büyüme yönteminin avantajı: sonuç İÇSEL OLARAK TUTARLIDIR (yüksek büyüme varsayan şirket, bunun karşılığında daha fazla yeniden yatırım yapmak ZORUNDADIR). (s.34) [→ FORMÜL bağlantısı Kısım 2/3'te (Ch.3-4) detaylanacak]
- **İLKE-15:** DCF'in artıları: analiste işin sürdürülebilirliğini SORGULATIR (Buffett'ın "hisse değil iş satın alıyoruz" felsefesiyle uyumlu), DOĞASI GEREĞİ KONTRARYANDIR (fiyat orantısız yükselirse DCF "aşırı değerli" bulur). Eksileri: kötü analist elinde MANİPÜLE edilebilir, DAHA FAZLA veri/varsayım gerektirir, tüm bir sektörü/piyasayı "aşırı değerli" bulabilir (portföy yöneticisi için pratik açmaz yaratır — piyasa moduna DUYARLI bir alternatif aramaya iter). (s.35)
- **İLKE-16:** Göreli değerlemenin temeli: değer, karşılaştırılabilir varlıkların fiyatlamasından TÜRETİLİR, ortak bir değişkenle STANDARTLAŞTIRILARAK (kazanç/defter değeri/gelir bölünerek çarpan elde edilir). Hisse fiyatının kendisi ARBİTRERDİR (2:1 bölünme fiyatı yarıya indirir) — standartlaştırma bu keyfiliği ORTADAN KALDIRIR. (s.36)
- **İLKE-17:** Göreli değerlemenin 3 varyantı: DOĞRUDAN KIYAS (1-2 neredeyse özdeş şirket), EMSAL GRUP ORTALAMASI (sektör ortalama çarpanına göre ucuz/pahalı), FARKLAR İÇİN DÜZELTİLMİŞ EMSAL GRUP (PEG oranı gibi çarpan düzeltmesi VEYA istatistiksel regresyon ile büyüme/risk farkı kontrol edilir). (s.37)
- **İLKE-18:** Çarpanların kullanım kolaylığı AYNI ZAMANDA en büyük zaafıdır — DCF'te analist varsayımları AÇIKÇA belirtmek ZORUNDADIR, çarpanlarda bu varsayımlar genellikle İFADE EDİLMEDEN kalır (önyargılı analist emsal grubu seçerek sonucu manipüle edebilir); AYRICA emsal şirketlerin KENDİSİ piyasa tarafından yanlış fiyatlanmışsa (tüm sektör aşırı değerli), göreli değerleme bu hatayı DEVRALIR. (s.38)
- **İLKE-19:** Koşullu talep (opsiyon) değerleme, DCF'in DEĞER DÜŞÜK GÖSTERDİĞİ 3 durumda avantaj sağlar: (1) değeri neredeyse TAMAMEN optionality'den gelen varlıklar (tek umut vaat eden ilacı FDA onay sürecinde olan biyoteknoloji şirketi; ağır borçlu zarar eden şirketin özkaynağı — "derin out-of-the-money opsiyon" gibi); (2) ÖĞRENME/ESNEKLİK değeri yüksek varlıklar (doğal kaynak şirketleri — DCF'in sabit üretim takvimi varsayımı gerçekçi değildir); (3) opsiyon modelleri riski OLUMLU bir faktör olarak da ele alır (oynaklık arttıkça opsiyon değeri ARTAR — DCF'te risk HER ZAMAN değeri düşürür). (s.41)
- **İLKE-20:** Real-options argümanının KÖTÜYE KULLANIMI: öğrenmenin bir değeri olması için REKABETÇİ EXCLUSİVİTY (rakiplerin AYNI öğrenmeyi yapamaması) GEREKİR — rakipler de aynı bilgiye/tepkiye sahipse opsiyon primi eklemek HAKSIZ FİYATLAMAYA yol açar. Uzun vadeli, işlem görmeyen varlıklarda sabit oynaklık/temettü verimi varsayımları savunulması ZOR hale gelir. (s.42)
- **İLKE-21:** Değerlemenin rolü, yatırım felsefesine göre DEĞİŞİR: pasif yatırımcı için MİNİMAL, aktif yatırımcı için MERKEZİ. Fundamental analistler (değer VEYA büyüme yatırımcısı ayrımıyla) için MERKEZİ rol; teknik analistler (chartistler) için ÇEVRESEL rol; market timer'lar için BİREYSEL hisse değil PİYASA GENELİ değerlemesi. (s.42-45)
- **İLKE-22:** Aktivist yatırımcılar (Icahn, Kerkorian tarzı) için değerleme, "şirket BUGÜN ne değer" değil "YÖNETİM DEĞİŞİRSE ne değer olur" sorusuna cevap arar — kötü hisse performansının NE KADARI kötü yönetimden (düzeltilebilir), NE KADARI dış faktörlerden (düzeltilemez) geldiğini AYIRMAK gerekir. (s.45)
- **İLKE-23:** Satın alma (M&A) analizinde değerleme MERKEZİ rol oynar; 2 özel faktör dikkate alınmalı: SİNERJİ (birleşik firmanın tek başına yapamayacaklarını yapabilmesinden doğan DEĞER ARTIŞI) ve KONTROL DEĞERİ (yönetim değişikliği/yeniden yapılanmanın etkisi — özellikle DÜŞMANCA devralmalarda önemli). Hem hedef firma (teklifi reddetmek için) hem alıcı firma (fiyatı haklı çıkarmak için) YAPISAL ÖNYARGI baskısı altındadır. (s.45-46)
- **İLKE-24:** Değerleme, kurumsal finansın HER aşamasında rol oynar — girişim sermayesi/özel sermaye görüşmelerinde (ne kadar hisse karşılığında sermaye), halka arzda (teklif fiyatı), sonrasında yatırım/borçlanma/temettü kararlarında. "Değer artırma" (value enhancement) danışmanlık endüstrisinin (EVA, CFROI gibi ölçütler) merkez temasıdır. (s.46)
- **İLKE-25:** Hukuki/vergi amaçlı değerlemelerde (ortaklık ayrılığı, miras, boşanma) amaç genellikle "DOĞRU" değer DEĞİL, MAHKEMENİN KABUL EDECEĞİ değerdir — değerleme ilkeleri aynı kalsa da AMAÇ FARKLILAŞIR. (s.46-47)

**Chapter 2 — Estimating Discount Rates:**

- **İLKE-26 (Finansal risk tanımı):** Finansta risk, günlük dildeki "sadece kötü sonuç" tanımından FARKLIDIR — beklenenden HEM DÜŞÜK (downside) HEM YÜKSEK (upside) sapmayı kapsar (Çin'in "危机" — tehlike+fırsat sembolüyle özetlenir). Risk, MARJİNAL YATIRIMCININ (o an işlem yapması en olası yatırımcı, VARSAYILAN olarak İYİ ÇEŞİTLENDİRİLMİŞ) gözünden ölçülmelidir. (s.50-52)
- **İLKE-27:** Risk 2 kategoriye ayrılır: FİRMA-ÖZEL risk (proje riski, rekabet riski, sektör riski — bir/birkaç yatırımı etkiler) ve PAZAR (marketwide) riski (faiz oranı değişimi, ekonomi geneli — TÜM yatırımları etkiler). Çeşitlendirme firma-özel riski AZALTIR/SIFIRA YAKINSATIR (pozitif/negatif haberler ortalamada birbirini götürür) ama pazar riskini AZALTAMAZ (marketwide hareketler PORTFÖYDEKİ ÇOĞU varlığı AYNI YÖNDE etkiler). (s.53-55)
- **İLKE-28:** Risk-getiri modellerinin ORTAK 3 adımı: (1) riski gerçekleşen getirinin beklenenden SAPMASI olarak tanımla, (2) firma-özel riski pazar riskinden AYIR, (3) SADECE çeşitlendirilemeyen (pazar) riskin ÖDÜLLENDİRİLECEĞİNİ varsay (marjinal yatırımcı iyi çeşitlendirilmiş olduğundan). Modeller BU 3 adımda hemfikirdir, SADECE pazar riskini NASIL ÖLÇECEKLERİNDE ayrışırlar (CAPM/APM/çok faktörlü modeller). (s.52-56)
- **İLKE-29 (CAPM'in temeli):** CAPM'in 2 kısıtlayıcı varsayımı: İŞLEM MALİYETİ YOK ve YATIRIMCILARIN ÖZEL BİLGİYE ERİŞİMİ YOK — bu varsayımlar altında TÜM yatırımcılar "pazar portföyünü" (piyasadaki her varlığın market değeri ağırlıklı bileşimi) tutana kadar çeşitlendirmeye devam eder. Bir varlığın riski, bu pazar portföyüne EKLEDİĞİ risktir — kovaryans ile ölçülür, pazar varyansına BÖLÜNEREK STANDARTLAŞTIRILIR (= BETA). Pazar portföyünün betası = 1; riskiz varlığın betası = 0. (s.56-58)
- **İLKE-30:** APM (Arbitrage Pricing Model), CAPM'in kısıtlayıcı varsayımlarını GEVŞETİR — TEK bir pazar faktörü yerine ÇOKLU risk kaynağı ve her kaynağa göre farklı beta'ya izin verir (faktör analizi istatistiksel tekniğiyle). Çok faktörlü modeller, APM'in İSİMSİZ istatistiksel faktörlerini SPESİFİK makroekonomik değişkenlerle (Chen/Roll/Ross 1986: sanayi üretimi, default primi değişimi, getiri eğrisi kayması, beklenmeyen enflasyon, reel getiri oranı değişimi) DEĞİŞTİRİR — ekonomik sezgi kazandırır ama faktör seçim HATASI riski taşır (örn. 1970'lerde petrol fiyatı önemli faktörken 1980-90'larda ÖNEMİNİ YİTİRDİ). (s.58-59)
- **İLKE-31:** CAPM basitliği (TEK girdi: beta) nedeniyle PRATİKTE hala BASKIN modeldir; APM/çok faktörlü modeller GEÇMİŞ getirileri daha iyi açıklasa da, GELECEK beklenen getiriyi tahmin ederken FAZLA sayıda faktör/beta/prim tahmin etme hatası, kazanılan doğruluğu SİLEBİLİR. Yazarın tavsiyesi: aşırı tarihsel veri bağımlılığı OLMADAN, DİKKATLİ (judicious) CAPM kullanımı en etkili yaklaşımdır. (s.59-60)
- **İLKE-32 (Risksiz oranın 2 koşulu):** Bir varlığın risksiz sayılması için: (1) DEFAULT RİSKİ OLMAMALI (genellikle bir hükümet tarafından ihraç edilmeli — ama TÜM hükümetler default-free DEĞİLDİR); (2) REINVESTMENT BELİRSİZLİĞİ OLMAMALI (ara nakit akışı OLMAMALI — bu yüzden n-yıllık nakit akışı için risksiz oran, n-yıl vadeli SIFIR KUPONLU tahvil getirisi OLMALIDIR, kısa vadeli hazine bonosu bile DEĞİLDİR çünkü yeniden yatırım oranı belirsizdir). Pratik uzlaşma: çoğu para biriminde 10 yıllık devlet tahvili makul bir risksiz oran sunar. (s.61-62)
- **İLKE-33 (Tutarlılık ilkesi):** Risksiz oran, nakit akışlarının ÖLÇÜLDÜĞÜ para birimi VE terimlerle (nominal/reel) TUTARLI olmalıdır — şirketin domicile olduğu ülke DEĞİL, nakit akışının TAHMİN EDİLDİĞİ para birimi belirleyicidir (bir Meksika şirketi dolar cinsinden dolar risksiz oranıyla VEYA peso cinsinden peso risksiz oranıyla değerlenebilir). Yüksek/istikrarsız enflasyonda REEL terimlerle değerleme yapılır — bu durumda REEL risksiz oran gerekir (enflasyon-endeksli devlet tahvili YOKSA nominal orandan beklenen enflasyon ÇIKARILARAK tahmin edilir). (s.62-63)
- **İLKE-34:** Default-free hükümet OLMAYAN piyasalarda (gelişmekte olan piyasalar) 3 alternatif: (1) o piyasadaki en büyük/güvenli firmaların yerel para borçlanma oranını baz al, HAFİFÇE düşür (~1 puan, tipik yüksek dereceli kurumsal default spread); (2) uzun vadeli dolar forward kontratları VARSA faiz oranı paritesiyle yerel risksiz oranı türet; (3) yerel para devlet tahvili oranından, o ülkenin YEREL PARA kredi notuna karşılık gelen default spread'i ÇIKAR. (s.63)
- **İLKE-35 (Risk primi belirleyicileri):** Risk primi 2 değişkenin FONKSİYONUDUR: (1) yatırımcıların RİSK İŞTAHI (kısmen doğuştan, kısmen ekonomik refaha ve YAKIN GEÇMİŞ piyasa deneyimine bağlı — büyük düşüşlerden SONRA risk primi YÜKSELİR); (2) "ortalama riskli" yatırımın ALGILANAN riskliliği (bu algı ZAMANLA değişebilir). (s.64)
- **İLKE-36 (Anket primleri — GÜVENİLMEZ):** Anket bazlı risk primi tahminleri 3 nedenle NADİREN kullanılır: makul olma sınırı YOKTUR (risksiz orandan DÜŞÜK cevap bile verilebilir), AŞIRI oynaktır (son piyasa hareketine göre dramatik değişir), KISA VADELİDİR (en uzun anketler bile 1 yılı GEÇMEZ). (s.65)
- **İLKE-37 (Tarihsel prim tahmin sapmalarının 3 kaynağı):** (1) KULLANILAN ZAMAN ARALIĞI (1926'dan itibaren mi, son 10/20/50 yıl mı — kısa dönemler GÜNCEL ama YÜKSEK standart hatalı); (2) RİSKSİZ ENSTRÜMAN SEÇİMİ (Hazine BONOSU mu BONOSU mu — ABD'de getiri eğrisi TARİHSEL OLARAK yukarı eğimli olduğundan bono bazlı prim BONOdan BÜYÜKTÜR, ama tutarlılık ilkesi gereği UZUN VADELİ tahvil bazlı prim kullanılmalıdır); (3) ARİTMETİK vs GEOMETRİK ortalama (aritmetik tek-dönem tahmini için teorik olarak doğru ama getiriler ZAMANLA NEGATİF KORELELİYSE — ki ampirik kanıt BUNU gösteriyor — aritmetik ortalama primi ABARTIR; UZUN vadeli/çok dönemli kullanım için geometrik ortalama DAHA SAVUNULABİLİRDİR). (s.65-67)
- **İLKE-38 ("Hisseler her zaman kazanır" YANILGISI):** 17 ülkenin 1900-2001 verisine göre bazı piyasalarda (İspanya) hisse getirisi tahvil getirisini SADECE %1-3 aşarken bazılarında (Fransa) %4,6-7,1 aşmıştır — hisselerin UZUN VADEDE HER ZAMAN kazandığı iddiası TEHLİKELİDİR: eğer HER ZAMAN kazansaydı, uzun vadeli yatırımcı için RİSKSİZ olurdu (mantıksal çelişki). (s.68-69)
- **İLKE-39 (Ülke risk primi 2 soruya indirgenir):** (1) OLGUN bir piyasa için TABAN prim NEDİR? (yazar ABD'yi olgun piyasa kabul eder, %4,84 tarihsel geometrik primi kullanır); (2) BİREYSEL ülkeler için EK prim NASIL tahmin edilir? — 3 yöntemle: default spread, göreli standart sapma, ikisinin MELEZİ (bkz. FORMÜL-07/08/09). (s.69-73)
- **İLKE-40 (İma edilen (implied) risk primi):** Piyasanın DOĞRU FİYATLANDIĞI varsayılırsa, gözlemlenen endeks seviyesi + beklenen temettü verimi + beklenen büyümeden GERİYE DOĞRU çözülerek özkaynağın gerekli getirisi (dolayısıyla risk primi) TÜRETİLİR — TARİHSEL veriye VEYA ülke düzeltmesine GEREK DUYMAZ, herhangi bir piyasada kullanılabilir. Dezavantajı: kullanılan MODELİN (Gordon büyüme vb.) doğruluğuna ve girdilerin güvenilirliğine BAĞIMLIDIR. (s.73-74)
- **İLKE-41:** İma edilen risk primi TARİHSEL primden ÇOK DAHA OYNAKTIR ve NEREDEYSE HER ZAMAN tarihsel primden DÜŞÜK ölçülür (1960-2005 ortalaması ~%4, zirve 1978'de sadece %6,50) — enflasyon/faiz artışıyla BİRLİKTE yükselme eğilimindedir (sabit varsaymak yerine). Piyasa görüşü KATMADAN değerleme yapmak isteyen analist GÜNCEL ima edilen primi kullanmalıdır; farklı (örn. tarihsel %5) bir prim kullanmak, DOLAYLI olarak "piyasa X% aşırı değerli" görüşünü DEĞERLEMEYE KATMAK anlamına gelir. (s.75-76)
- **İLKE-42 (Beta tahmininin 3 yöntemi):** (1) TARİHSEL PİYASA BETASI — hisse getirilerini pazar endeksi getirilerine karşı regresyon; (2) TEMEL (fundamental/bottom-up) BETA — iş türü + faaliyet kaldıracı + finansal kaldıraçtan türetilir, fiyat geçmişi GEREKTİRMEZ; (3) MUHASEBE BETASI — muhasebe kazançlarının pazar kazançlarına regresyonu (ZAYIF yöntem — kazançlar DÜZLEŞTİRİLMİŞTİR, betaları 1'e YAKINSATIR; ayrıca amortisman/envanter yöntemi değişiklikleri gibi FAALİYET DIŞI etkenlerden BOZULUR; çeyreklik/yıllık veri AZ gözlem sağlar). (s.76-85)
- **İLKE-43 (Regresyon betasının 3 kritik kararı):** (1) TAHMİN DÖNEMİ uzunluğu (uzun=daha çok veri ama firma risk profili DEĞİŞMİŞ olabilir); (2) GETİRİ ARALIĞI (günlük/haftalık/aylık — günlük veri gözlemi ARTTIRIR ama "nontrading bias" (işlem görmeyen dönemlerde sıfır getiri kaydı) KÜÇÜK firmaların betasını AŞAĞI ÇEKER, haftalık/aylık veri bu önyargıyı AZALTIR); (3) PAZAR ENDEKSİ seçimi (marjinal yatırımcının portföyüne göre belirlenmeli — yerel yatırımcı için yerel endeks, küresel yatırımcı için küresel endeks; SADECE analiz edenin ülkesine göre endeks seçmek YANLIŞTIR). Regresyon betası GENİŞ standart hata TAŞIR (örnek: Disney betası 1.01, standart hata 0.20 → %67 güvenle 0.81-1.21 aralığı). (s.76-79)
- **İLKE-44 (Betanın 3 belirleyicisi):** (1) İŞ TÜRÜ — ekonomik koşullara duyarlı sektörler (otomotiv/konut, ihtiyari harcama ürünleri) YÜKSEK beta; döngüsel olmayan (gıda işleme/tütün, temel market ürünleri) DÜŞÜK beta; (2) FAALİYET KALDIRACI DERECESİ — sabit maliyet/toplam maliyet oranı YÜKSEKSE, gelirdeki değişim faaliyet kârında DAHA ORANTISIZ değişime yol açar → daha YÜKSEK beta (küçük firmalar hem niş ürün HEM yüksek faaliyet kaldıracı taşıdığından tipik olarak YÜKSEK betalıdır); (3) FİNANSAL KALDIRAÇ DERECESİ — borç arttıkça öz sermaye HBK değişkenliği ARTAR (sabit faiz ödemesi iyi zamanda HBK'yı büyütür, kötü zamanda düşürür) → beta ARTAR. (s.79-81)
- **İLKE-45 (Bottom-up/temel beta 3 avantajı):** (1) FİYAT GEÇMİŞİ GEREKTİRMEZ — halka arzlar, özel şirketler, bölünmemiş şirket birimleri için bile hesaplanabilir; (2) ÇOK SAYIDA regresyonun ORTALAMASI olduğundan TEK bir regresyondan DAHA HASSASTIR (standart hata ≈ ortalama std hata/√karşılaştırılabilir firma sayısı — örn. 100 firma × 0.25 std hata → 0.025 sonuç); (3) YAKIN ZAMANLI/GELECEKTEKİ iş karması ve finansal kaldıraç DEĞİŞİKLİKLERİNİ yansıtabilir (regresyon betası SADECE GEÇMİŞE bakar). (s.83)
- **İLKE-46 (Özel/kapalı şirketlerde beta yetersizdir):** Piyasa betası, marjinal yatırımcının İYİ ÇEŞİTLENDİRİLMİŞ olduğu varsayımına dayanır — ÖZEL şirket sahibi genellikle SERVETİNİN ÇOĞUNU o işe yatırmıştır, TOPLAM riski (sadece pazar riskini DEĞİL) önemser. 3 çözüm: (1) yakın zamanda halka açık bir şirkete SATILACAĞINI varsay (piyasa betası kullanılabilir); (2) çeşitlenmeme riski için cost of equity'e bir PRİM ekle; (3) BETAYI TOPLAM RİSKİ yansıtacak şekilde düzelt — "TOTAL BETA" = piyasa betası / √R² (regresyonun R²'si, riskin pazar-riski PAYINI ölçer). (s.86-87) [→ FORMÜL-13]
- **İLKE-47 (Küçük firma primi TEHLİKELİDİR):** CAPM küçük firmaların beklenen getirisini SİSTEMATİK OLARAK DÜŞÜK gösterme eğilimindedir; bu yüzden "küçük firma primi" (1926-2004 tarihsel farkı ~%3-3,5) EKLEME pratiği YAYGINDIR ama 3 nedenle TEHLİKELİDİR: (1) OYNAKTIR, 1980'lerde uzun süre KAYBOLMUŞTUR; (2) "küçük" tanımı ZAMANLA DEĞİŞİR ve prim çoğunlukla EN küçük alt-segmentten kaynaklanır; (3) SABİT bir düzeltme kullanmak, analisti o KÜÇÜK firmanın ÜRÜN/KALDIRAÇ özelliklerini DERİNLEMESİNE incelemekten ALIKOYAR. (s.86)
- **İLKE-48 (Ülke riski maruziyeti — cost of equity'e 3 dahil etme yöntemi):** (1) EN YAYGIN ama EN ETKİSİZ: ülke risk primini HER şirkete TAM OLARAK ekle (Rf + β×ABD primi + ülke primi) — TÜM şirketleri AYNI FIRÇAYLA boyar, gerçekte export-odaklı vs yerel-odaklı şirketler FARKLI maruziyete sahiptir; (2) DAHA MAKUL: ülke primini BETAYA ölçekle (Rf + β×(ABD primi+ülke primi)) — sadece beta zaten ülke riskini de YAKALIYORSA işe yarar; (3) EN GENEL: ülke riskini AYRI bir bileşen olarak ele al, maruziyeti (λ, lambda) AYRI tahmin et (Rf + β×ABD primi + λ×ülke primi) — export/yerel odaklı şirket farkını YAKALAR, ÇOKLU ülke maruziyetine de İZİN VERİR. (s.88-89) [→ FORMÜL-14]
- **İLKE-49 (Lambda (λ) tahmininin 3 yolu):** (1) firmanın bir pazardaki GELİR ORANININ, o pazardaki ORTALAMA firmanın gelir oranına GÖRE ÖLÇEKLENMESİ (örn. %35 Brezilya geliri / ortalama firmanın %70'i = λ 0,5); (2) üretim tesisi konumu + risk yönetimi ürünleri gibi DİĞER maruziyet unsurlarının dahil edilmesi; (3) firma hisse getirilerinin ÜLKE TAHVİLİ getirilerine REGRESYONU (beta tahminiyle AYNI mantık, farklı bağımsız değişken). (s.89-90)
- **İLKE-50 (İma edilen cost of equity):** Piyasa fiyatının DOĞRU olduğu varsayılırsa, mevcut fiyat + beklenen nakit akışlarından (temettü VEYA FCFE) İÇSEL GETİRİ ORANI (IRR) çözülerek cost of equity TÜRETİLİR. TEK bir firma için DAİRESEL bir sonuç verir ("her zaman doğru fiyatlı" çıkar) — ama bir SEKTÖRDEKİ TÜM firmalar için ORTALAMASI alınıp SEKTÖR cost of equity'si olarak kullanılabilir (TEK firma için pratik değeri YOKTUR). (s.92)
- **İLKE-51 (Fama-French proxy modeli):** 1963-1990 ABD verisinde gerçekleşen getiriler, DÜŞÜK PİYASA DEĞERİ ve YÜKSEK DEFTER/PİYASA ORANI ile GÜÇLÜ KORELELİDİR — Fama/French bu 2 özelliği DOLAYLI risk göstergesi (beta'nın ALTERNATİFİ) olarak önerir. Regresyon: küçük + yüksek defter/piyasa'lı firmalar TARİHSEL OLARAK DAHA YÜKSEK getiri sağlamıştır. (s.91-92)
- **İLKE-52 (Cost of capital = ağırlıklı ortalama, PİYASA DEĞERİ ile):** Cost of capital, TÜM finansman bileşenlerinin (borç+özkaynak+hibrit) MALİYETLERİNİN, KULLANIM ORANLARINA göre AĞIRLIKLANDIRILMIŞ ortalamasıdır. Ağırlıklar KESİNLİKLE PİYASA DEĞERİNE dayanmalıdır (defter değeri DEĞİL) — "adil fiyatta alıcı/satıcı arasında KAYITSIZLIK" ilkesi gereği (yeni fon PİYASA fiyatından toplanır). (s.93-95, 102)
- **İLKE-53 (Defter değeri ağırlıklarının 3 SAVUNULMASI ve ÇÜRÜTÜLMESİ):** (1) "Defter değeri daha az oynak/güvenilir" → YANLIŞ, bu OYNAKLIK EKSİKLİĞİ zayıflıktır, gerçek değer YENİ BİLGİYLE değişir, piyasa değeri gerçek değere DAHA YAKINDIR; (2) "Defter değeri daha MUHAFAZAKAR" → TERSİ DOĞRUDUR: ABD'de defter özkaynağı piyasa özkaynağından genelde DÜŞÜKTÜR, özkaynak maliyeti borç maliyetinden YÜKSEK olduğundan defter ağırlıklı hesap cost of capital'ı YAPAY OLARAK DÜŞÜRÜR (örnek hesap: piyasa ağırlıklı %14 vs defter ağırlıklı %12); (3) "Muhasebe getirisi defter bazlı hesaplandığından tutarlılık gerekir" → EKONOMİK OLARAK ANLAMSIZ, fonlar BAŞKA YERDE piyasa oranıyla değerlendirilebilirdi. (s.102-103) [→ BAYRAK-03]
- **İLKE-54 (Borca dahil edilmesi/edilmemesi gerekenler):** DAHİL: TÜM FAİZ TAŞIYAN yükümlülükler (kısa+uzun vadeli, banka+tahvil TEK BİR uzun vadeli maliyetle birleştirilmeli — AYRI kategoriler oluşturmak "kısa vadeli borç ucuzdur" gibi YANILTICI sonuçlara yol açar) VE TÜM KİRA TAAHHÜTLERİ (operating lease'ler dahi — bilançoda GÖRÜNMESE de vergi indirilebilir, ZORUNLU bir yükümlülüktür, ödenmezse İFLASA yol açabilir → PV'ye çevrilip borca EKLENMELİ). DAHİL EDİLMEMELİ: ticari borçlar/tedarikçi kredisi (işletme sermayesinin parçası), fonsuz emeklilik/sağlık yükümlülükleri, dava riskleri (bunlar cost of capital hesabında DEĞİL, firma değerinden özkaynağa geçişte AYRICA düşülür). (s.103-105) [→ FORMÜL-23, BAYRAK-05]
- **İLKE-55 (Kısa vadeli borçla uzun vadeli yatırım finanse etmenin YANILTICILIĞI):** Kısa vadeli oranlar genelde uzun vadeliden DÜŞÜKTÜR (normal yukarı eğimli getiri eğrisinde) — bu "daha ucuz borçlanma" gibi görünse de YANILTICIDIR: cost of capital, YATIRIMIN KENDİSİNİN aşması gereken engel oranıdır ve UZUN VADELİ borçlanma maliyetini yansıtmalıdır, çünkü kısa vadeli borçla finanse edilen uzun vadeli proje er ya da geç PİYASAYA DÖNÜP BORCU YENİLEMEK ZORUNDADIR. (s.103-104) [→ BAYRAK-04]
- **İLKE-56 (Finansman ağırlıkları zamanla değişebilir):** GENÇ firmalar genellikle TAMAMEN özkaynakla finanse edilir (borç taşıyacak nakit akışı YOKTUR) — büyüdükçe borç oranı SEKTÖR ORTALAMASINA doğru artması BEKLENMELİDİR. Olgun firmalar HEDEF borç oranına geçiş yaparken bu geçiş İLERİYE DÖNÜK modellenmelidir — cost of capital YIL BAZLI, DEĞİŞEN bir sayı olarak ele alınmalıdır, SABİT değil. (s.107-108)
- **İLKE-57 (Net borç kullanımının riski):** Borcu nakitle netleştirmek (net debt), HEM borcun HEM nakdin RİSKSİZ olduğu VE borcun vergi avantajının nakit üzerindeki vergiyle TAM DENGELENDİĞİ varsayımını TAŞIR — borç RİSKLİYSE veya nakit faizi borç faizinden ÇOK DÜŞÜKSE net borç kullanmak YANILTICIDIR. Nakit fazlası borcu AŞAN firmalarda NEGATİF net D/E oranı ortaya çıkabilir — bu durumda LEVERED beta UNLEVERED betadan DAHA DÜŞÜK çıkabilir (görünüşte tuhaf ama mantıklı: firma büyük nakit yastığıyla iş riskinin BİR KISMINI NÖTRLEMİŞTİR). (s.109-110)

---

## Formüller

- **FORMÜL-01 — DCF Temel Değer Formülü**
  - Formül: `Değer = Σ [E(CFt) / (1+r)^t]` (t=1'den n'e)
  - Değişkenler: `E(CFt)` = t döneminde beklenen nakit akışı; `r` = nakit akışının riskini yansıtan iskonto oranı; `n` = varlığın ömrü.
  - QuaxisLabs karşılığı: `src/analysis/valuation.py::compute_valuation_assessment()` içindeki Damodaran "İstikrarlı Büyüme FCFE" bloğu BU formülün TEK-AŞAMALI (Gordon büyüme) özel halini ZATEN uyguluyor (`equity_value = fcfe * (1 + g) / (r - g)`). ÇOK aşamalı/detaylı projeksiyonlu (Ch.3-5'te işlenecek) TAM versiyon YOK — capex/işletme sermayesi/detaylı büyüme projeksiyonu gerektirir, bu veriler hiçbir fetcher'da (VERİ EKSİK, bkz. Uygulama Notları).

- **FORMÜL-02 — Levered/Unlevered Beta (Hamada Denklemi)**
  - Formül: `β_Levered = β_Unlevered × [1 + (1-t) × (D/E)]`
  - Değişkenler: `β_Unlevered` = firmanın hiç borcu olmasaydı taşıyacağı ("varlık betası") risk; `t` = marjinal vergi oranı; `D/E` = piyasa değeri bazında borç/özkaynak oranı. (Borcun betası sıfır kabul edilmiştir; aksi halde `β_L = β_u[1+(1-t)D/E] - β_D(1-t)D/E`.)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — `β_Unlevered` girdisi bulunmuyor (bkz. FORMÜL-10 notu), D/E oranı `calculator.Ratios.debt_to_equity` üzerinden HESAPLANABİLİR ama sadece finansal borç/özkaynak (kitabın PİYASA DEĞERİ bazlı D/E tanımından farklı — özkaynak defter değeri kullanıyor, market cap DEĞİL). Uygulanamaz.

- **FORMÜL-03 — CAPM Beklenen Getiri**
  - Formül: `E(R) = Rf + β × (Risk Primi)`
  - Değişkenler: `Rf` = risksiz oran; `β` = piyasa betası; `Risk Primi` = ortalama riskli yatırımın risksiz orana göre fazladan beklenen getirisi.
  - QuaxisLabs karşılığı: `src/analysis/valuation.py::_RISK_FREE_RATE_PCT` + `_EQUITY_RISK_PREMIUM_PCT` + Damodaran bloğundaki `cost_of_equity_pct = risk_free_pct + equity_risk_premium_pct` SATIRI bu formülün **β=1 (piyasa ortalaması) VARSAYIMLI** özel halidir — modül içi yorum bunu AÇIKÇA belgeliyor ("gerçek beta için gereken endeks/kovaryans serisi hiçbir fetcher'da YOK"). Gerçek beta hesaplamak için `src/fetchers/price_history.py::fetch_ohlcv()` HİSSE fiyat geçmişi (400 gün) SAĞLIYOR ama karşılık gelen PAZAR ENDEKSİ (BIST100/S&P500) getiri serisini çeken bir fetcher YOK — kovaryans/regresyon bazlı GERÇEK CAPM beta şu an UYGULANAMAZ.

- **FORMÜL-04 — APM / Çok Faktörlü Model Beklenen Getiri**
  - Formül: `E(R) = Rf + Σ βj × (E(Rj) - Rf)` (j=1'den faktör sayısına)
  - Değişkenler: `βj` = j faktörüne göre beta; `E(Rj) - Rf` = j faktörünün risk primi.
  - QuaxisLabs karşılığı: **VERİ EKSİK** — makroekonomik faktör serileri (sanayi üretimi, enflasyon şoku, getiri eğrisi kayması vb.) hiçbir fetcher'da YOK, faktör analizi için tarihsel getiri VERİ TABANI da YOK. Uygulanamaz, ileride bile düşük öncelik (CAPM'in kendisi bile beta eksikliğinden uygulanamıyor).

- **FORMÜL-05 — İma Edilen (Implied) Özkaynak Risk Primi — Tek Aşamalı**
  - Formül: `Endeks Değeri = Beklenen Temettü(t+1) / (r - g)` → `r`'yi çöz → `İma Edilen Prim = r - Rf`
  - Değişkenler: Gordon büyüme modeli — `g` = uzun vadeli sabit büyüme oranı.
  - QuaxisLabs karşılığı: **VERİ EKSİK** — BIST100/S&P500 endeks düzeyi, endeks temettü verimi VE konsensüs kazanç büyüme tahmini serisi hiçbir fetcher'da YOK; bu makro bir piyasa girdisidir, tekil şirket fetcher'larıyla üretilemez.

- **FORMÜL-06 — İma Edilen Prim, Çok Aşamalı (2005 S&P 500 Örneği)**
  - Formül: `Endeks = Σ[CFt/(1+r)^t] (t=1..5, yüksek büyüme) + [CF6/(r-g_kararlı)]/(1+r)^5`
  - Değişkenler: yüksek büyüme dönemi (5 yıl, konsensüs kazanç büyümesi) + sonrasında kararlı büyüme (Hazine tahvil oranına eşitlenir).
  - QuaxisLabs karşılığı: Aynı VERİ EKSİKLİĞİ (FORMÜL-05) — endeks/piyasa seviyesi verisi yok. Not: bu iki-aşamalı YAPI, `valuation.py`'nin Damodaran bloğundaki `g_kullanılan = min(hasılat_büyümesi, risksiz_faiz)` mantığıyla KAVRAMSAL OLARAK AYNI İLKEYİ (sonsuz büyüme kısıtı) TEKİL ŞİRKET seviyesinde ZATEN uyguluyor — makro/endeks seviyesinde YOK.

- **FORMÜL-07 — Ülke Risk Primi: Default Spread Yöntemi**
  - Formül: `Ülke Toplam Özkaynak Primi = Olgun Piyasa Primi + Ülke Tahvili Default Spread'i`
  - Değişkenler: Ülke tahvili default spread'i = (o ülkenin dolar cinsi tahvil getirisi) − (ABD Hazine tahvili getirisi), kredi notu bazlı.
  - QuaxisLabs karşılığı: **VERİ EKSİK** — ülke kredi notu (S&P/Moody's/Fitch) ve ülke tahvili default spread'i hiçbir fetcher'da çekilmiyor; `valuation.py`'deki `_RISK_FREE_RATE_PCT`/`_EQUITY_RISK_PREMIUM_PCT` sabitleri (TRY %32/%8, USD %4,3/%4,6) bu formülün ÇIKTISINI ELLE/STATİK olarak temsil ediyor (bkz. modül içi not: "Graham'ın 22,5 sabiti gibi AÇIKÇA belgelenmiş, ELLE PERİYODİK GÜNCELLENMESİ GEREKEN makro varsayımlar").

- **FORMÜL-08 — Ülke Risk Primi: Göreli Standart Sapma Yöntemi**
  - Formül: `Ülke Toplam Primi = Olgun Piyasa Primi × (Ülke Özkaynak Std.Sapması / Olgun Piyasa Std.Sapması)`; `Ülke Riski (izole) = Ülke Toplam Primi - Olgun Piyasa Primi`
  - Değişkenler: haftalık getirilerden hesaplanan yıllıklandırılmış standart sapmalar (kitap örneğinde 2 yıllık haftalık veri).
  - QuaxisLabs karşılığı: **VERİ EKSİK** (endeks seviyesinde) — ancak İLGİNÇ bir paralel: `src/analysis/merton.py::annualized_equity_volatility()` fonksiyonu TEKİL HİSSE için GÜNLÜK kapanışlardan yıllıklandırılmış oynaklık hesaplıyor (aynı istatistiksel yöntem: log getiri std sapması × √252) — ENDEKS seviyesinde uygulanmıyor ama METODOLOJİ zaten kod tabanında MEVCUT, endeks fiyat serisi eklenirse KOLAYCA uyarlanabilir.

- **FORMÜL-09 — Ülke Risk Primi: Melez (Default Spread + Göreli St.Sapma) Yöntemi — EN GERÇEKÇİ kabul edilen**
  - Formül: `Ek Ülke Özkaynak Primi = Ülke Tahvili Default Spread'i × (Ülke Özkaynak Std.Sapması / Ülke Tahvili Std.Sapması)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — hem ülke tahvili default spread'i HEM ülke tahvili oynaklık serisi YOK.

- **FORMÜL-10 — Regresyon (Tarihsel Piyasa) Betası**
  - Formül: `Rj = a + b×Rm`; `b (beta) = Kovaryans(Rj, Rm) / Varyans(Rm)`
  - Değişkenler: `Rj` = hisse getirisi, `Rm` = pazar endeksi getirisi (aylık/haftalık periyotlarla, genellikle 2-5 yıl).
  - QuaxisLabs karşılığı: **VERİ EKSİK** — `price_history.fetch_ohlcv()` hisse fiyatı SAĞLIYOR (400 gün, günlük) ama karşılık gelen BIST100/XU100 veya S&P500 endeks getiri serisini çeken bir fetcher YOK; bu eklenirse regresyon HESAPLANABİLİR (günlük yerine haftalık/aylık resample gerekir — kitap günlük veriyi "nontrading bias" nedeniyle ÖNERMİYOR, bkz. İLKE-43).

- **FORMÜL-11 — Bottom-Up (Temel) Unlevered Beta**
  - Formül: `β_Unlevered(Firma) = Σ [wi × β_Unlevered,i]` (i = her iş kolu, wi = o iş kolunun firma değerindeki payı)
  - QuaxisLabs karşılığı: **VERİ EKSİK, YÜKSEK ARAŞTIRMA MALİYETLİ** — hem sektörel karşılaştırılabilir firma listesi + her birinin unlevered betası HEM segment bazlı gelir kırılımı gerektirir; QuaxisLabs'ta segment bazlı gelir verisi YOK, tek-sektörlü basit versiyon bile ilk önce FORMÜL-10'un (piyasa endeksi) çözülmesini gerektirir.

- **FORMÜL-12 — Ortalama Betanın Standart Hatası**
  - Formül: `Std.Hata(Ortalama Beta) ≈ Ortalama(Std.Hata_i) / √n` (n = karşılaştırılabilir firma sayısı)
  - QuaxisLabs karşılığı: Aynı ön koşul eksikliği (FORMÜL-10/11) nedeniyle UYGULANAMAZ.

- **FORMÜL-13 — Toplam (Total) Beta — Özel/Kapalı Şirketler İçin**
  - Formül: `β_Total = β_Piyasa / √R²`
  - Değişkenler: `R²` = regresyonun belirlilik katsayısı (riskin pazar-riski PAYI).
  - QuaxisLabs karşılığı: **VERİ EKSİK** (piyasa betası ön koşulu FORMÜL-10'a bağlı) — QuaxisLabs zaten HALKA AÇIK şirketleri kapsadığından (özel şirket değerlemesi kapsam dışı) bu formülün ÖNCELİĞİ DÜŞÜK.

- **FORMÜL-14 — Ülke Riski Maruziyetli Cost of Equity (3 Yaklaşım)**
  - Formül (en genel, λ ile): `Cost of Equity = Rf + β×(Olgun Piyasa Primi) + λ×(Ülke Risk Primi)`
  - QuaxisLabs karşılığı: **KISMEN VAR, FARKLI TASARIM** — `valuation.py`'nin Damodaran bloğu TRY/USD için AYRI, SABİT `_RISK_FREE_RATE_PCT`/`_EQUITY_RISK_PREMIUM_PCT` çiftleri kullanıyor (BIST şirketleri için TRY seti, NASDAQ için USD seti) — bu, kitabın "ülke primini TÜM şirketlere TAM ekleme" (İLKE-48, yöntem 1 — "EN ETKİSİZ" olarak nitelenen) yaklaşımına YAKINDIR, λ (lambda) ile ayrıştırma YAPILMIYOR (β=1 sabit varsayımı zaten λ farklılaştırmasını da imkânsız kılıyor).

- **FORMÜL-15 — İma Edilen (Implied) Cost of Equity — Tek Şirket**
  - Formül: `P0 = D1/(r-g)` → `r = D1/P0 + g` (temettü verimi + büyüme)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — temettü verisi (DPS) hiçbir fetcher'da YOK (Graham/Buffett turlarında da TEKRAR TEKRAR tespit edilen kümülatif eksiklik, bkz. `_ilerleme.md`).

- **FORMÜL-16 — Unlevered Cost of Equity**
  - Formül: `Cost of Equity(Unlevered) = Rf + β_Unlevered × Risk Primi`
  - QuaxisLabs karşılığı: β_Unlevered eksikliği nedeniyle UYGULANAMAZ (bkz. FORMÜL-02/10).

- **FORMÜL-17 — Sentetik Kredi Notu Bazlı Pretax Cost of Debt**
  - Formül: `Pretax Cost of Debt = Risksiz Oran + Default Spread(sentetik not)`; sentetik not, `Interest Coverage Ratio` bandına göre Tablo 2.4'ten (bkz. EŞİKLER) okunur.
  - QuaxisLabs karşılığı: **VERİ EKSİK — sanayi/ticaret (XI_29) şirketlerinde**, çünkü `interest_expense` SADECE banka şeması (`STANDARD_ITEM_MAP_UFRS`, itemCode "3B") için mevcut; XI_29 (sanayi) haritasında YOK (bu, `_ilerleme.md`'de Buffett turundan beri TEKRARLANAN, EN YÜKSEK öncelikli veri açığıdır — 3. kez farklı kitapta doğrulandı). NASDAQ tarafında da `sec_edgar.py::STANDARD_ITEM_MAP_US_GAAP`'ta `interest_expense`/`income_before_tax` tag'i YOK.

- **FORMÜL-18 — After-tax Cost of Debt**
  - Formül: `After-tax Cost of Debt = Pretax Cost of Debt × (1 - t)`
  - QuaxisLabs karşılığı: Pretax girdi eksikliği (FORMÜL-17) nedeniyle UYGULANAMAZ; marjinal vergi oranı `t` için de standart bir alan YOK (efektif vergi oranı türetilebilir ama `tax_provision`/`pretax_profit` çifti SADECE finansman şirketleri şemasında (`STANDARD_ITEM_MAP_FINANSMAN`) var, XI_29'da YOK).

- **FORMÜL-19 — Interest Coverage Ratio (Faiz Karşılama Oranı)**
  - Formül: `Interest Coverage Ratio = FVÖK (Faiz ve Vergi Öncesi Kâr) / Faiz Gideri`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (aynı `interest_expense` sorunu) — bu oran zaten Graham turunda da (Kısım 3, FORMÜL-18) TESPİT EDİLMİŞTİ, ÜÇÜNCÜ kez farklı kitapta karşımıza çıktı; XI_29'a interest_expense EKLENMESİ tek başına BU formülü VE FORMÜL-17/18'i birden ÇÖZER (yüksek kaldıraçlı, tekil eklenti önerisi).

- **FORMÜL-20 — Cost of Preferred Stock**
  - Formül: `Cost of Preferred Stock = Yıllık Preferred Temettü / Preferred Hisse Fiyatı`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — imtiyazlı hisse alt kırılımı Buffett turunda da (Özkaynaklar bölümü) TESPİT edilmiş eksiklikti; ayrıca BIST'te imtiyazlı hisse çok NADİR, düşük öncelik.

- **FORMÜL-21 — WACC (Ağırlıklı Ortalama Sermaye Maliyeti)**
  - Formül: `WACC = Cost of Equity × [E/(D+E)] + After-tax Cost of Debt × [D/(D+E)]` (+ preferred stock terimi varsa)
  - Değişkenler: `E`/`D` = özkaynak/borcun PİYASA DEĞERİ (defter değeri DEĞİL — bkz. İLKE-52/53).
  - QuaxisLabs karşılığı: **TAMAMEN YOK** — `valuation.py`'nin Damodaran bloğu SADECE `cost_of_equity`'yi kullanıyor (Gordon FCFE modeli), COST OF DEBT/WACC hiç HESAPLANMIYOR (modülün kendi üst notu bunu AÇIKÇA "Kural 3/4'e aykırı olur" diye GEREKÇELENDİRİYOR — capex/vergi gideri/işletme sermayesi girdileri YOK). `E` (market cap) `calculator.ValuationMetrics.market_cap`'ten HAZIR; `D` (piyasa değeri borç) YOK — sadece defter değeri `financial_debt` var (bono fiyatlama/vade yapısı bilgisi YOK, FORMÜL-22 uygulanamaz).

- **FORMÜL-22 — Defter Değeri Borcunu Piyasa Değerine Çevirme**
  - Formül: Defter borcunu KUPON BONO gibi ele al (kupon = toplam faiz gideri, vade = ağırlıklı ortalama vade), GÜNCEL pretax cost of debt ile ISKONTO ET → `PV(Bono) = Piyasa Değeri Borç`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — hem faiz gideri (XI_29'da yok) HEM borç vade yapısı kırılımı (kısa/uzun VAR ama detaylı vade takvimi YOK) eksik.

- **FORMÜL-23 — Operating Lease'i Borca Çevirme**
  - Formül: gelecek yıl kira taahhütlerini pretax cost of debt ile ISKONTO ET, TOPLA → "Kiraların Borç Değeri"; faaliyet kârı da BU tutar kadar YUKARI DÜZELTİLİR (kira gideri çıkarılıp amortisman+faiz eklenir).
  - QuaxisLabs karşılığı: **TAMAMEN YOK** — kira taahhütleri (operating lease commitment schedule) hiçbir fetcher'da çekilmiyor; BIST XI_29/UFRS şemalarında bu KALEM AYRI izlenmiyor. Düşük öncelik (BIST sanayi şirketlerinde ABD'ye göre daha az yaygın açıklama pratiği).

- **FORMÜL-24 — Net Borç (Damodaran'ın levered beta/D-E bağlamındaki kullanımı)**
  - Formül: `Net Borç = Toplam Finansal Borç - Nakit`
  - QuaxisLabs karşılığı: **VAR, FARKLI/DAHA GENİŞ TANIMLA** — `calculator.net_debt()` = `financial_debt - cash - financial_investments` (kitaptaki basit tanımdan farklı olarak `financial_investments` — kısa vadeli menkul kıymet/repo — de DÜŞÜLÜYOR, bkz. modül içi "TERA canlı hatası" notu). Kavramsal olarak UYUMLU, QuaxisLabs versiyonu DAHA KAPSAMLI.

---

## Eşikler

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| ABD tarihsel özkaynak risk primi (1928-2004, T-bond, geometrik ort.) | **%4,84** | Yazarın "en makul" kabul ettiği taban (olgun piyasa) primi; sonraki tüm ülke primi hesaplarında bu baz alınır | Ch.2, s.67-70 |
| ABD tarihsel prim aralığı (seçim kombinasyonlarına göre) | **%3,47 – %8,60** | Zaman aralığı × T-bill/T-bond × aritmetik/geometrik seçimine göre DEĞİŞİR | Ch.2, s.68 |
| İma edilen (implied) ABD özkaynak primi, Ocak 2006 | **%4,08** | Piyasanın (S&P 500) kendi fiyatından geriye çözülen prim; yazar BUNU tarihsel yerine ÖNERİR | Ch.2, s.75-76 |
| İma edilen prim, 1960-2005 ortalaması | **~%4** | Tarihsel primin HER ZAMAN ÜZERİNDE kaldığı görülür (zirve 1978'de %6,50) | Ch.2, s.75 |
| Küçük firma primi (1926-2004) | **%3 – %3,5** | TEHLİKELİ bir düzeltme (bkz. İLKE-47) — sabit kullanım ÖNERİLMEZ | Ch.2, s.86 |
| Brezilya ülke risk primi — default spread yöntemi | **%3,50** ek (toplam %8,34) | En DÜŞÜK/en BASİT tahmin | Ch.2, s.70-71 |
| Brezilya ülke risk primi — melez yöntem (EN GERÇEKÇİ kabul edilen) | **%4,67** ek (toplam **%9,51**) | Yazarın TERCİH ETTİĞİ yöntem | Ch.2, s.72-73 |
| S&P kredi notu — yatırım yapılabilir eşik | **BBB ve üzeri** | Altındaki notlar "yüksek getirili/spekülatif" (junk) kategori | Ch.2, s.96 |
| Getiri eğrisi "well-behaved" (normal) tanımı | Uzun vade, kısa vadeden **en fazla %2-3 yüksek** | Bu aralıkta yıl-bazlı risksiz oran farkının PV etkisi KÜÇÜK kabul edilir | Ch.2, dipnot 5 |
| Risksiz oran seçimi (pratik uzlaşma) | **10 yıllık devlet tahvili** | Çoğu para biriminde makul bir vade eşleştirme | Ch.2, s.61-62 |
| ABD 10 yıllık nominal vs enflasyon-endeksli tahvil farkı (2005 başı) | Nominal **%4,3** / Reel **%2,1** | Reel risksiz oran tahmini için kullanılabilir fark | Ch.2, s.62 |
| Emerging market'te büyük firma borçlanma oranından risksiz oran türetme indirimi | **~%1 puan** düşür | Tipik yüksek dereceli kurumsal default spread | Ch.2, dipnot 7 |
| Disney BBB+ default spread (2004) | **%1,25** | T-bond + bu spread = pretax cost of debt %5,25 | Ch.2, İllüstrasyon 2.5 |
| Disney cost of capital (2004, konsolide) | **%8,59** | Bölüm bazında %7,90 (parklar) – %8,93 (stüdyo) arasında değişir | Ch.2, İllüstrasyon 2.8 |
| Disney piyasa değeri D/(D+E) vs defter değeri D/(D+E) | **%21,02 vs %35,10** | Aynı firma için defter/piyasa ağırlık farkının BÜYÜKLÜĞÜNE somut örnek | Ch.2, İllüstrasyon 2.7 |
| Bottom-up beta örnek standart hata küçülmesi | 100 firma × 0,25 → **0,025** | `std.hata/√n` formülünün somut sonucu | Ch.2, s.83 |

**Tablo 2.4 — Interest Coverage Ratio → Sentetik Kredi Notu → Default Spread (2004, küçük sanayi şirketleri, S&P):**

| Faiz Karşılama Oranı | Sentetik Not | Tipik Default Spread |
|---|---|---|
| > 12,50 | AAA | %0,35 |
| 9,50 – 12,50 | AA | %0,50 |
| 7,50 – 9,50 | A+ | %0,70 |
| 6,00 – 7,50 | A | %0,85 |
| 4,50 – 6,00 | A− | %1,00 |
| 4,00 – 4,50 | BBB | %1,50 |
| 3,50 – 4,00 | BB+ | %2,00 |
| 3,00 – 3,50 | BB | %2,50 |
| 2,50 – 3,00 | B+ | %3,25 |
| 2,00 – 2,50 | B | %4,00 |
| 1,50 – 2,00 | B− | %6,00 |
| 1,25 – 1,50 | CCC | %8,00 |
| 0,80 – 1,25 | CC | %10,00 |
| 0,50 – 0,80 | C | %12,00 |
| < 0,50 | D | %20,00 |

(Not: Bu tablo İLK olarak Kısım 1'de tam biçimde geçiyor; sonraki kısımlarda GÜNCELLENMİŞ/genişletilmiş versiyonları görülürse çapraz referans verilecek.)

---

## Kontrol listeleri

**Kontrol Listesi A — Değerleme Önyargısını Azaltmanın 5 Yolu (Ch.1, s.19-20):**
1. Kurumsal baskıları AZALT (sat tavsiyesi veren analisti KORU — şirket/satış ekibi/portföy yöneticisi baskısından).
2. Değerleme SONUCUNU ödül/ceza yapısından AYIR (M&A analizini "deal yapma" motivasyonundan AYRI tut).
3. ÖNCEDEN kamuya güçlü bir fiyat taahhüdü VERME (precommitment yapma) — değerleme TAMAMLANMADAN pozisyon alma.
4. ÖZ-FARKINDALIK geliştir — girdi seçerken kendi önyargını AKTİF olarak SORGULA.
5. DÜRÜST RAPORLAMA — önyargılarını (varsa) AÇIKÇA BELİRT (Bayesçi "prior" açıklama disipliniyle aynı).

**Kontrol Listesi B — Bottom-Up Beta Hesaplama Prosedürü, 5 Adım (Ch.2, s.81-83):**
1. Firmanın hangi iş kolu/kollarında olduğunu BELİRLE (gelir/faaliyet kârı kırılımına göre).
2. Her iş kolu için karşılaştırılabilir HALKA AÇIK firmaların ORTALAMA unlevered betasını tahmin et (karşılaştırılabilir firma seçimi, TEK ortak endekse göre beta tahmini, "önce unlever sonra ortala" tercih edilir, basit ortalama TERCİH edilir, NAKİT etkisi arındırılır).
3. Her iş kolunun FİRMA DEĞERİNDEKİ payını (mümkünse gelir çarpanıyla türetilmiş) AĞIRLIK olarak kullanıp iş kolu betalarını TOPLA → bottom-up unlevered beta.
4. Firmanın GÜNCEL (piyasa değeri bazlı) borç/özkaynak oranını hesapla (yoksa hedef/sektör tipik oranı kullan).
5. Adım 3'teki unlevered beta ile Adım 4'teki kaldıracı BİRLEŞTİREREK LEVERED betayı hesapla (Hamada denklemi, FORMÜL-02).

**Kontrol Listesi C — Cost of Capital Hesabında Borca DAHİL Edilecek / EDİLMEYECEK Kalemler (Ch.2, s.103-105):**
- DAHİL: tüm faiz taşıyan kısa+uzun vadeli borç (TEK, uzun vadeli maliyetle birleştirilmiş); tüm operating+capital lease taahhütleri (PV'ye çevrilmiş).
- HARİÇ (cost of capital hesabından — ama firma değeri→özkaynak geçişinde AYRICA düşülür): ticari borçlar/tedarikçi kredisi (işletme sermayesi kalemi), fonsuz emeklilik/sağlık yükümlülükleri, potansiyel dava yükümlülükleri.

---

## Kırmızı bayraklar

- **BAYRAK-01 — "Değerleme Sonrası Kurcalama" (Postvaluation Tinkering):** Bir analiz, beklenen/istenen bir sonuca YAKINSAMAK için büyüme veya risk varsayımlarının GERİYE DÖNÜK revize edildiğine dair İZ taşıyorsa (örn. piyasa fiyatının ÜZERİNDE bir değer bulunca büyüme varsayımı YUKARI, riski AŞAĞI çekilmişse) — güvenilmezdir. Nasıl tespit edilir: AYNI analistin/kurumun BENZER şirketler için kullandığı varsayımların TUTARLILIĞINI (veya tutarsızlığını) karşılaştır. Gereken veri: birden fazla değerleme raporu/varsayım seti (QuaxisLabs kapsamı DIŞINDA — bu bir SÜREÇ/METODOLOJİ kontrolüdür, tekil şirket verisiyle tespit EDİLEMEZ). (Ch.1, s.18)
- **BAYRAK-02 — "Kara Kutu" Değerleme Modeli:** Model o kadar KARMAŞIK hale gelmiştir ki KULLANAN ANALİST BİLE iç işleyişi AÇIKLAYAMAZ ("model şirketi 30 dolardan değerledi" derken "BİZ değerledik" diyemiyor) — özellikle TİCARİ/proprietary modellerde (bir kısmı erişime KAPALI tutulur) risklidir. Nasıl tespit edilir: modeli kullanan kişiye "HANGİ TEK varsayım değişikliği sonucu EN ÇOK etkiler?" diye sor — cevaplayamıyorsa kara kutu belirtisidir. Gereken veri: modelin kendisi/varsayım dokümantasyonu (metodolojik kontrol, veri kalemi DEĞİL). (Ch.1, s.26)
- **BAYRAK-03 — Defter Değeri Ağırlıklı WACC Kullanımı:** Bir cost of capital hesaplaması PİYASA DEĞERİ yerine DEFTER DEĞERİ ağırlıkları kullanıyorsa, sonuç YAPAY OLARAK DÜŞÜK (dolayısıyla YAPAY OLARAK YÜKSEK bir "değer") üretir — çünkü ABD/gelişmiş piyasa şirketlerinde defter özkaynağı TİPİK OLARAK piyasa özkaynağından DÜŞÜKTÜR. Nasıl tespit edilir: hesaplamada kullanılan D/(D+E) oranının KAYNAĞINI (bilanço mu, piyasa değeri mi) sorgula. Gereken veri: piyasa değeri (fiyat×pay adedi, `compute_valuation.market_cap` üzerinden QuaxisLabs'ta ZATEN MEVCUT) vs bilanço özkaynağı (`equity`) karşılaştırması. (Ch.2, s.102-103)
- **BAYRAK-04 — Kısa Vadeli Borçla Uzun Vadeli Yatırımın "Ucuz" Gösterilmesi:** Bir firma/analist, düşük kısa vadeli faiz oranını kullanarak uzun vadeli bir projenin/firmanın maliyetini HESAPLIYORSA — bu YANILTICIDIR, çünkü kısa vadeli borç ER YA DA GEÇ yenilenmek (roll-over) ZORUNDADIR ve o zamanki oran BİLİNEMEZ. Nasıl tespit edilir: kullanılan borçlanma vadesinin YATIRIMIN/projenin vadesiyle EŞLEŞİP eşleşmediğini kontrol et. Gereken veri: borç vade yapısı (QuaxisLabs'ta sadece kısa/uzun vadeli borç TOPLAMLARI var, detaylı vade takvimi YOK — VERİ EKSİK). (Ch.2, s.103-104)
- **BAYRAK-05 — Operating Lease'lerin Bilanço Dışı Bırakılması:** Ağır operating lease kullanan bir firma (perakende, havayolu gibi sektörler), bilançoda GÖRÜNMEYEN ama VERGİ İNDİRİLEBİLİR + ZORUNLU (ödenmezse iflasa yol açabilen) bir yükümlülük TAŞIR — kaldıracı/gerçek borcu OLDUĞUNDAN DÜŞÜK GÖSTERİR. Nasıl tespit edilir: dipnotlardaki gelecek yıl kira taahhüt takvimini PV'ye çevirip raporlanan borca EKLE (bkz. FORMÜL-23), faaliyet kârını da buna göre DÜZELT. Gereken veri: gelecek kira taahhüt takvimi (VERİ EKSİK — hiçbir fetcher'da yok, dipnot kalemi). (Ch.2, s.104)
- **BAYRAK-06 — Çok Düşük Faiz Karşılama Oranı (Interest Coverage Ratio):** Faiz karşılama oranı **1,5'in ALTINA** (Tablo 2.4'te B− ve altı sentetik notlara denk gelir, default spread %6 ve üzeri) düşen bir firma YÜKSEK temerrüt riski taşır. Nasıl tespit edilir: FVÖK/Faiz Gideri oranını hesapla, Tablo 2.4 ile karşılaştır. Gereken veri: `interest_expense` — **VERİ EKSİK** (XI_29 sanayi şirketlerinde yok, sadece bankalarda var — bkz. FORMÜL-17/19). QuaxisLabs'ta BENZER amaçlı (ama farklı metodoloji ile) `src/analysis/merton.py` Merton mesafe-i temerrüt/EDF modeli ZATEN MEVCUT — o modül interest coverage yerine hisse fiyat oynaklığı + borç yüzü değerinden (Black-Scholes tersine mühendislik) temerrüt olasılığı türetiyor, bu formülün DOLAYLI bir İKAMESİ sayılabilir. (Ch.2, Tablo 2.4)
- **BAYRAK-07 — Zarar Eden Firmada Borcun "Vergi Kalkanı" Faydasının Sayılması:** Faiz gideri SADECE firma VERGİ ÖDÜYORSA (kâr ediyorsa) vergi avantajı sağlar — zarar eden bir firma için after-tax cost of debt hesaplarken TAM vergi oranını uygulamak (`t`) HATALIDIR, YIL BAZINDA firmanın o yıl kâr/zarar durumuna göre kademeli uygulanmalıdır. Nasıl tespit edilir: firmanın SON dönemki net kâr/zarar durumunu kontrol et — zarar varsa o dönem için vergi kalkanı sıfırlanmalı. Gereken veri: `net_income`/`pretax_profit` (net_income QuaxisLabs'ta ZATEN VAR; pretax_profit XI_29'da YOK). (Ch.2, s.105-106)

---

## Uygulama notları (koda dönüşüm için)

**Nicel (skorlanabilir, kısmen/tam VERİ VAR):**
- Interest Coverage Ratio → sentetik kredi notu → default spread eşlemesi (Tablo 2.4, FORMÜL-17/19): metodoloji BASİT ve doğrudan kodlanabilir, TEK engel `interest_expense` verisinin XI_29 (BIST sanayi) ve US_GAAP haritalarında EKSİK olması. Bankalarda (`STANDARD_ITEM_MAP_UFRS`) `interest_expense` ZATEN VAR — banka şirketleri için (farklı bir "faiz karşılama" yorumuyla, kredi/mevduat marjı bağlamında) kısmen denenebilir, ama kitabın senaryosu (sanayi şirketi borç maliyeti) tam olarak KARŞILANAMAZ.
- Piyasa değeri D/(D+E) ağırlığı ile "gerçek" WACC yönünde bir adım: `E` (market cap) HAZIR, `D`'nin defter değeri (`financial_debt`) HAZIR — TAM piyasa değeri borcu (FORMÜL-22, bono fiyatlama) olmadan bile, "defter borcu = piyasa borcu" BASİTLEŞTİRMESİYLE (kitabın kendisinin de "olgun şirketler için kötü bir varsayım değil" dediği kısayol, s.106) YAKLAŞIK bir WACC/BAYRAK-03 karşılaştırması KODLANABİLİR — ama cost of debt girdisi (FORMÜL-17/18) hâlâ eksik olduğundan TAM WACC yine de UYGULANAMAZ.
- Net Borç formülü (FORMÜL-24): ZATEN MEVCUT ve kitaptan DAHA KAPSAMLI (`calculator.net_debt()`).
- CAPM (β=1 sabit varsayımlı) cost of equity: ZATEN MEVCUT (`valuation.py` Damodaran bloğu) — Kısım 1'in asıl KATKISI, bu mevcut uygulamanın kitabın METODOLOJİSİNE göre HANGİ BASİTLEŞTİRMELERİ (β=1, λ=1 örtük, WACC yok sadece cost of equity) yaptığının AÇIKÇA BELGELENMESİDİR (yukarıdaki FORMÜL-03/14 notları).

**Nitel (LLM yorumuna uygun, veri gerektirmez veya sadece nitel değerlendirme):**
- Parsimoni ilkesi (İLKE-09) — bir değerleme/analiz raporunun GEREĞİNDEN KARMAŞIK olup olmadığı LLM'e sorulabilir bir "model karmaşıklığı" kontrolü olabilir.
- Önyargı kontrol listesi (Kontrol Listesi A) — analiz sürecinin KENDİSİNE dair bir meta-kontrol, sayısal veri gerektirmez.
- DCF vs Göreli Değerleme vs Opsiyon Değerleme seçimi (İLKE-10, 15-19) — şirketin YAŞAM EVRESİ/özelliklerine göre HANGİ yöntemin uygun olduğuna dair NİTEL rehberlik; Kısım 2-3'te (Ch.3-6) DAHA SOMUT hale gelecek.
- BAYRAK-01/02/04 (postvaluation tinkering, kara kutu, kısa/uzun vade uyumsuzluğu) — METODOLOJİK/süreç kontrolleridir, tekil şirket verisiyle DEĞİL, raporun/modelin KENDİSİNİN incelenmesiyle tespit edilir; bir LLM'e "bu değerleme raporunda X/Y/Z belirtisi var mı" diye SORULABİLİR ama otomatik SKORLANAMAZ.

**Veri eksikliği nedeniyle şimdilik UYGULANAMAZ (öncelik sırasına göre):**
1. **`interest_expense` (XI_29/sanayi şirketleri) + `income_before_tax`/`pretax_profit`** — Bu turun EN YÜKSEK öncelikli tekil bulgusu: kitaptaki cost of debt/interest coverage/vergi kalkanı formüllerinin (FORMÜL-17/18/19, BAYRAK-06/07) TAMAMI bu TEK veri açığına bağlı. Buffett + Graham turlarında da (farklı bağlamlarda) TESPİT edilmişti — artık DÖRDÜNCÜ kez, kitaplar-arası EN ISRARLI veri açığı olarak doğrulandı.
2. **Pazar endeksi (BIST100/XU100, S&P500) günlük/haftalık getiri serisi** — gerçek CAPM betası (FORMÜL-10) ve dolayısıyla bottom-up beta (FORMÜL-11), implied equity premium (FORMÜL-05/06) için gereklidir. `price_history.py` TEKİL hisse verisi çekiyor ama endeks verisi ÇEKMİYOR; bu eklenirse Merton modülündeki (`annualized_equity_volatility`) YÖNTEM doğrudan UYARLANABİLİR.
3. **Ülke kredi notu + ülke tahvili default spread'i** (S&P/Moody's/Fitch) — ülke risk primi (FORMÜL-07/08/09) için gerekli; QuaxisLabs şu an bunun yerine ELLE GÜNCELLENEN sabitler (`_RISK_FREE_RATE_PCT`/`_EQUITY_RISK_PREMIUM_PCT`) kullanıyor — kitabın YÖNTEMİNE göre bu sabitlerin NASIL türetilebileceğine dair bir YOL HARİTASI bu bölümde belgelendi (FORMÜL-07/09), otomatik veri çekimi henüz YOK.
4. **Kira taahhüt takvimi (operating lease schedule)** — FORMÜL-23/BAYRAK-05 için gerekli; BIST'te göreceli düşük öncelik (ABD'ye kıyasla daha az yaygın bir açıklama pratiği).
5. **Piyasa değeri borç (bono fiyatlama/vade yapısı)** — FORMÜL-22/tam WACC için gerekli; DÜŞÜK öncelik (defter değeri kısayolu kitabın kendisince de kabul edilebilir bulunuyor, olgun şirketler için).
6. **Temettü verisi (DPS)** — FORMÜL-15 (implied cost of equity) için gerekli; bu ARTIK BEŞİNCİ kez (Graham 3, Buffett 1, şimdi Damodaran) farklı kitapta tespit edilen KÜMÜLATİF EN SIK tekrarlanan veri açığı.

---

# KISIM 2 — Chapter 3-4: Measuring Cash Flows + Forecasting Cash Flows

**Kapsam:** Chapter 3: Measuring Cash Flows (PDF s.118-166), Chapter 4: Forecasting Cash Flows (PDF s.167-217). ID numaralandırması Kısım 1'in devamı (İLKE-58'den, FORMÜL-25'ten, BAYRAK-08'den başlar; kesintisiz).

## İlkeler (devam)

**Chapter 3 — Measuring Cash Flows:**

- **İLKE-58:** Nakit akışları 3 farklı eksende sınıflandırılabilir: (1) ÖZKAYNAĞA vs FİRMAYA (borç ödemeleri sonrası/öncesi); (2) NOMİNAL vs REEL (enflasyon içerip içermediği — para birimine göre değişir); (3) VERGİ ÖNCESİ vs SONRASI (kurumlar vergisi sonrası ama yatırımcı vergisi ÖNCESİ standart tanım). (s.118-119)
- **İLKE-59:** Güncellenmiş kazanç ("trailing 12-month"/TTM) kullanmak KRİTİKTİR — yıllık rapor birkaç ay ESKİ olabilir, özellikle HIZLA değişen (genç/yüksek büyüme) firmalarda son çeyreklik verilerle GÜNCELLENMEDEN değerleme yapmak DEĞER DÜŞÜK GÖSTERİR (Google örneği: 2005 ortası TTM geliri son 10-K'nın 2 KATINDAN FAZLA). Dezavantajı: bazı kalemler (opsiyon detayları gibi) SADECE yıllık raporda açıklanır, çeyreklik veriyle TUTARSIZLIK riski taşır. (s.120-121)
- **İLKE-60:** Muhasebe kazançlarının 2 EN YAYGIN yanlış sınıflandırması: (1) SERMAYE giderlerinin (R&D gibi) operasyonel gider sayılması — hem faaliyet kârını HEM özkaynak defter değerini DÜŞÜK gösterir; (2) FİNANSAL giderlerin (operating lease) operasyonel gider sayılması — SADECE faaliyet kârını etkiler, net kârı ETKİLEMEZ. (s.121-122)
- **İLKE-61:** R&D giderlerinin kapitalize EDİLMESİ GEREKİR — muhasebe standartları (belirsizlik gerekçesiyle) TAMAMEN gider yazılmasını zorunlu kılsa da, bu ARAŞTIRMANIN YARATTIĞI VARLIĞIN bilançoda GÖRÜNMEMESİNE ve sermaye/kârlılık oranlarının BOZULMASINA yol açar. Amortisman ömrü SEKTÖRE göre değişir (ilaç firması UZUN — onay süreci uzun; yazılım firması KISA — ürün hızlı ortaya çıkar). (s.122-123)
- **İLKE-62 ("Diğer" kapitalize edilebilir operasyonel giderler):** R&D'nin ötesinde, MARKA DEĞERİ yaratan reklam (Gillette/Coca-Cola), İNSAN SERMAYESİ yaratan eğitim/işe alım (danışmanlık firmaları), MÜŞTERİ EDİNİMİ yaratan SG&A (Amazon/AOL tipi e-tailer'lar) argümanla kapitalize edilebilir — ANCAK bu YALNIZCA faydanın BİRDEN FAZLA döneme YAYILDIĞINA dair SOMUT KANIT varsa savunulabilir; keyfi kullanım TEHLİKELİDİR. (s.126-127)
- **İLKE-63:** Operating lease borca çevrildikten SONRA faaliyet kârı 2 adımda düzeltilir: (1) kira gideri geri EKLENİR (finansal gider olduğu için); (2) kiralanan varlığın AMORTİSMANI DÜŞÜLÜR. Amortismanın borç anaparası geri ödemesine YAKLAŞIK EŞİT olduğu varsayılırsa, kısayol: sadece İMA EDİLEN FAİZ GİDERİ geri eklenir (tam düzeltmenin YAKLAŞIK karşılığı). (s.127-128)
- **İLKE-64 ("Yönetilen kazançlar" fenomeni):** 1990'larda Microsoft 40 çeyrekten 39'unda, Intel de BENZER şekilde analist tahminlerini AŞTI — piyasalar bu davranışı ÖĞRENİR ve "FISILDANAN KAZANÇLAR" (whispered earnings, resmi konsensüsün birkaç kuruş ÜZERİNDE, GAYRIRESMİ bir eşik) oluşturarak tepki verir; Intel 1997'de resmi tahmini AŞMASINA RAĞMEN fısıltı tahmininin ALTINDA kaldığı için hisse fiyatı %5 DÜŞTÜ. (s.129-130)
- **İLKE-65 (Kazanç yönetiminin 2 sebebi):** (1) Piyasaların İSTİKRARLI+beklenti-üstü kazançları ÖDÜLLENDİRDİĞİNE dair YAYGIN inanç; (2) YÖNETİCİ ÇIKARI — kazanç düştüğünde işten çıkarılma riski artar, tazminat genelde kâr HEDEFLERİNE BAĞLIDIR. (s.130)
- **İLKE-66 (4 tür olağanüstü/özel kalem, FARKLI muamele gerektirir):** (1) GERÇEKTEN tek seferlik (10 yılda 1 kez) → analiz DIŞI bırakılır; (2) DÜZENLİ ARALIKLARLA tekrarlayan (örn. her 3 yılda restructuring) → aslında "sıradan" gider, YILLIK ORTALAMAYA YAYILARAK dahil edilmeli; (3) HER YIL tekrarlayan ama OYNAK → çok yıllık ORTALAMA ile normalleştirilmeli; (4) İŞARET DEĞİŞTİREN (döviz kuru çevirisi gibi) → GÖZ ARDI edilmesi EN İHTİYATLI yaklaşımdır (zamanla TERSİNE döner). [→ KONTROL LİSTESİ D]
- **İLKE-67:** Şerefiye amortismanı ve "in-process R&D" write-off'ları NAKİT DIŞI ve genelde VERGİDEN DÜŞÜLEMEZ giderlerdir — kazanç tabanı olarak bu kalemler ÇIKARILMADAN ÖNCEKİ (pre-amortization/pre-writeoff) kazanca bakılmalıdır. Deng&Lev (1999) 389 firmada (1990-96), in-process R&D write-off'larının ORTALAMA alım fiyatının %72'sini oluşturduğunu ve alıcı firmanın kazancını akiziyondan SONRAKİ 4. çeyrekte ORTALAMA %22 ARTIRDIĞINI bulmuştur. (s.134) [→ BAYRAK-11]
- **İLKE-68 (Efektif vs marjinal vergi oranı ayrımı):** Efektif vergi oranı = ÖDENEN vergi/RAPORLANAN vergi öncesi kâr; marjinal vergi oranı = firmanın SON (veya bir sonraki) gelir dolarına uygulanan yasal orandır. ABD'de marjinal federal oran %35 (eyalet+yerel ile ~%40) iken 2005 ABD medyan EFEKTİF oranı SADECE ~%32'dir, bazı firmalarda %100'ü AŞAR veya NEGATİF çıkar. Farkın 4 nedeni: (1) raporlama vs vergi muhasebesi farklı standartlar KULLANIR (örn. düz-hat vs hızlandırılmış amortisman); (2) vergi KREDİLERİ; (3) vergi ERTELEME (gelecekte daha YÜKSEK efektif orana döner); (4) KADEMELİ (tiered) vergi yapısı. (s.135-137)
- **İLKE-69:** Değerlemede vergi oranı seçimi — SÜREKLİ (perpetuity) kullanılacaksa GÜVENLİ seçim MARJİNAL orandır (hiçbir düşük-efektif-oran nedeni SONSUZA dek SÜRMEZ); İLK yıl(lar) için EFEKTİF oran kullanılıp ZAMANLA marjinal orana YAKINSATILABİLİR; TERMİNAL DEĞER hesabında MUTLAKA marjinal oran kullanılmalıdır. (s.137-138)
- **İLKE-70 (Net operasyonel zarar - NOL etkisi):** Büyük NOL taşıyan firmalarda 2 yaklaşım VAR: (1) vergi oranını ZAMAN İÇİNDE SIFIRDAN marjinal orana KADEMELİ artır (hem faaliyet kârı HEM cost of capital hesaplamasında AYNI sıfır oranı kullanılmalı — İÇ TUTARLILIK); (2) firmayı NOL'siz değerleyip SONRA vergi tasarrufunun bugünkü değerini AYRICA ekle (limit: bu, tasarrufun GARANTİLİ+ANINDA olduğunu VARSAYAR, gerçekte kazanç belirsizliği taşır → DEĞERİ ABARTABİLİR). (s.140-141)
- **İLKE-71 (İşletme sermayesi tanımının DÜZELTİLMESİ):** Değerleme amaçlı "noncash işletme sermayesi" standart muhasebe tanımından FARKLIDIR — DÖNEN VARLIKLARDAN nakit/menkul kıymet ÇIKARILIR (adil getiri sağladığı için işletme sermayesi SAYILMAZ — İSTİSNA: banka sisteminin ZAYIF olduğu piyasalarda veya günlük operasyon için ZORUNLU büyük nakit tutuluyorsa dahil edilebilir) VE KISA VADELİ YÜKÜMLÜLÜKLERDEN faiz taşıyan borç (kısa vadeli borç + uzun vadeli borcun cari kısmı) ÇIKARILIR (cost of capital hesabında ZATEN sayıldığı için ÇİFT SAYIM önlenir). (s.150-151)
- **İLKE-72:** İşletme sermayesi değişimi TAHMİNİNDE HAM ($ tutarı) DEĞİL, GELİR YÜZDESİ ORANI tercih edilmelidir — yıldan yıla değişim AŞIRI OYNAKTIR (yalıtılmış bir baz yıl kullanma riski). (s.153-154) [→ KONTROL LİSTESİ G]
- **İLKE-73 (Negatif işletme sermayesi/değişimi):** Kısa vadede (3-5 yıl) VERİMLİLİK kazanımından kaynaklı NEGATİF DEĞİŞİM olağan olabilir ama SONSUZA DEK sürdürülemez (verimsizlik BİTER, ÖTESİ gelir/kâra ZARAR verir). NEGATİF (mutlak) işletme sermayesi (Wal-Mart/Dell tipi tedarikçi kredisi stratejisi) — HEM gerçek bir maliyet taşır (erken ödeme İNDİRİMİ kaybı) HEM derecelendirme kuruluşlarınca DEFAULT RİSKİ göstergesi sayılır; terminal değerde işletme sermayesi değişiminin SIFIRA yakınsatılması veya YUKARI dönmesi varsayılmalıdır. (s.155-157) [→ BAYRAK-12]
- **İLKE-74 (Temettü politikasının 3 kalıbı):** (1) Temettüler YAPIŞKANDIR — çoğu dönemde HBK sabit tutulur, artış AZALIŞTAN 5 KAT daha yaygındır; (2) temettüler KAZANCI TAKİP EDER, ÖNCÜLÜK ETMEZ (firma artışın SÜRDÜRÜLEBİLİRLİĞİNDEN emin olana kadar bekler); (3) hisse geri alımları GİDEREK temettünün ALTERNATİFİ haline gelmektedir (geri alımdan farklı olarak temettüyü KESMEK piyasa tarafından CEZALANDIRILIR, geri alım İSE herhangi bir yıl DURDURULABİLİR). (s.158-159)
- **İLKE-75 (FCFE'ye oranla dağıtım oranı):** Cash Returned/FCFE oranı 1'e YAKINSA firma ELİNDEKİNİN TAMAMINI dağıtıyor demektir; ÇOK ALTINDAYSA nakit biriktiriyor; ÇOK ÜZERİNDEYSE (mevcut nakitten VEYA yeni ihraçtan finanse ediyor) demektir. NYSE ortalaması (2004): **%60** — firmaların çoğu ÖDEYEBİLECEKLERİNDEN AZ dağıtır. (s.161-162)
- **İLKE-76 (Firmaların FCFE'den AZ dağıtmasının 5 nedeni):** (1) istikrar arzusu (temettü kesmekten KAÇINMA); (2) gelecek yatırım ihtiyacı (menkul kıymet ihracı MALİYETLİ, nakit TAMPON tutulur); (3) vergi faktörleri (2003 ÖNCESİ temettü sermaye kazancından DAHA YÜKSEK vergilendiriliyordu); (4) sinyal verme amaçlı KULLANIM (artış=olumlu, azalış=olumsuz sinyal, ampirik olarak DOĞRULANMIŞ); (5) yönetici çıkarı (imparatorluk kurma güdüsü, kâr düşüşünü GİZLEYECEK nakit YASTIĞI). [→ KONTROL LİSTESİ H] (s.162-164)

**Chapter 4 — Forecasting Cash Flows:**

- **İLKE-77 (Yüksek büyüme süresinin 3 belirleyicisi):** (1) FİRMA BÜYÜKLÜĞÜ — küçük firmalar (BÜYÜK bir pazarda) fazla getiriyi DAHA UZUN sürdürebilir, sadece MEVCUT pazar payına değil TOPLAM pazar büyüme potansiyeline de BAKILMALI; (2) MEVCUT büyüme oranı ve fazla getiri MOMENTUMU; (3) REKABET AVANTAJININ BÜYÜKLÜĞÜ VE SÜRDÜRÜLEBİLİRLİĞİ — EN KRİTİK belirleyici, giriş engelleri güçlüyse UZUN yüksek-büyüme dönemi savunulabilir, yönetim kalitesi de (Jack Welch/Roberto Goizueta örnekleri) rol oynar. (s.168-169) [→ KONTROL LİSTESİ I]
- **İLKE-78:** Yüksek büyüme, sadece firmayı BÜYÜTÜR — DEĞER YARATMASI için sermaye getirisinin sermaye MALİYETİNİ AŞMASI (fazla getiri) GEREKİR; bir firmanın 5-10 yıl yüksek büyüyeceğini varsaymak ZIMNEN o dönemde fazla getiri kazanacağını varsaymaktır — REKABETÇİ bir piyasada bu fazla getiriler ER YA DA GEÇ yeni rakiplerce EROZYONA UĞRAR. (dipnot 1, s.168)
- **İLKE-79 (Geçmiş büyüme hesaplama tuzakları):** Aritmetik ORTALAMA ile geometrik ORTALAMA sonuçları ÖZELLİKLE OYNAK kazançlarda BÜYÜK FARKLILAŞIR (geometrik DAHA DOĞRU gösterge — bileşik etkiyi yakalar); tahmin BAŞLANGIÇ/BİTİŞ noktası SEÇİMİ sonucu ÇARPITABİLİR (kötü yıldan iyi yıla ölçmek YAPAY yüksek büyüme gösterir); NEGATİF (veya sıfır) başlangıç kazancında YÜZDE BÜYÜME ORANI ANLAMSIZDIR — bu durumda geçmiş büyümeyi TAHMİNDE YOK SAYMAK daha DOĞRUDUR. (s.171-173)
- **İLKE-80 ("Higgledy Piggledy Growth" — Little 1960):** Bir dönemin kazanç büyüme oranı, BİR SONRAKİ dönemin büyüme oranıyla NEREDEYSE HİÇ ilişkili DEĞİLDİR (ardışık dönem korelasyonları SIK SIK NEGATİF, ortalama korelasyon ~0,02) — bu ilişki KÜÇÜK firmalarda DAHA DA ZAYIFTIR (oynaklık daha yüksek). Gelir büyümesi, kazanç büyümesinden DAHA İSTİKRARLI/ÖNGÖRÜLEBİLİRDİR (muhasebe seçimlerinin etkisi DAHA AZDIR). (s.173-175)
- **İLKE-81 (Firma büyüklüğünün büyüme üzerindeki etkisi):** Yüzdesel büyüme oranı FİRMA BÜYÜKLÜĞÜYLE TERS orantılı ZORLUK taşır ($10 milyon kazançlı firma için %50 büyüme, $500 milyon kazançlı firma için AYNI YÜZDEDEN ÇOK DAHA ZOR) — hızla büyümüş küçük firmaların GEÇMİŞ büyüme oranlarını GELECEĞE UZATMAK TEHLİKELİDİR; asıl test firmanın büyümeyi NASIL YÖNETTİĞİ (ölçeklenebilirlik) sorusudur. (s.175)
- **İLKE-82 (Yönetim tahminlerinin RİSKLERİ):** (1) Yönetim şirketin geleceği (ve kendi becerisi) konusunda TARAFSIZ OLAMAZ — tahminler genelde TEMENNİ LİSTESİ niteliğindedir; (2) yönetici tazminatı tahmini AŞMAYA BAĞLIYSA tahminleri BİLEREK DÜŞÜK tutma eğilimi doğar; (3) yönetim tahminleri İÇ TUTARSIZLIK içerebilir (örn. yeni sermaye harcaması OLMADAN 10 yıl %10 gelir büyümesi VARSAYMAK). Yönetim tahminleri TAMAMEN göz ardı EDİLMEMELİ ama FİZİBİLİTE ve İÇ TUTARLILIK kontrolünden GEÇİRİLMELİDİR. (s.176)
- **İLKE-83 (Analist tahminlerinin GÜÇ/ZAYIF yönleri):** Analistler GEÇMİŞ veriye EK olarak GÜNCEL bilgi, REKABETÇİ sinyal (bir telekom firmasının kötü raporu DİĞERLERİNİ etkiler) ve bazen ÖZEL bilgi kullanabilir — ama bu ÜSTÜNLÜK sadece KISA VADELİ (1-2 çeyrek ileri) tahminlerde AMPİRİK olarak DOĞRULANMIŞTIR; 3-5 YILLIK uzun vadeli tahminlerde üstünlük ÇOK KÜÇÜKTÜR ve geçmiş büyüme oranları HALA analist tahminlerinde BÜYÜK rol oynar. AYRICA analistler genelde HBK (EPS) tahmin eder — HBK büyümesi FAALİYET KÂRI büyümesinden FARKLIDIR (genelde YÜKSEKTİR), değerleme için AŞAĞI DÜZELTİLMELİDİR. (s.177-179)
- **İLKE-84 (Temel/fundamental büyüme — İÇSEL değişken):** En SAĞLAM büyüme tahmin yöntemi, büyümeyi firmanın YATIRIM POLİTİKASINA (ne kadar yeniden yatırım YAPTIĞI + bu yatırımların NE KADAR KALİTELİ olduğu) BAĞLI KILMAKTIR — bu, (1) İÇ TUTARLILIK sağlar (yüksek büyüme varsayan firma bunun KARŞILIĞINI yeniden yatırımla ÖDEMEK ZORUNDADIR) ve (2) firmaların DEĞER YARATMAK için NE YAPABİLECEĞİNE dair TEMEL bir çerçeve sunar. (s.179)
- **İLKE-85 (Marjinal ROE'nin bilgi değeri):** Standart ROE (net kâr/ÖNCEKİ YIL SONU özkaynak) hem ESKİ hem YENİ projelerin GETİRİSİNİ karıştırır — büyük firmalarda eski yatırımların AĞIRLIĞI nedeniyle YENİ yatırımlardaki KÖTÜLEŞME GECİKMELİ yansır. MARJİNAL ROE (Δnet kâr/Δönceki yıl özkaynağı) YENİ YATIRIMLARIN kalitesine dair DAHA DOĞRUDAN bir sinyal verir — Goldman Sachs 2005 örneğinde standart ROE %18,49 iken marjinal ROE ÇOK DAHA DÜŞÜK çıkmıştır (yeni yatırımların GETİRİSİNİN düştüğüne dair UYARI). (s.183-184)
- **İLKE-86 (Değişen ROE'nin büyümeye 2. bileşeni — "verimlilik kaynaklı büyüme"):** ROE SABİT değilse, büyümeye MEVCUT VARLIKLARIN getirisindeki İYİLEŞME/KÖTÜLEŞMEDEN gelen EK bir bileşen EKLENİR — $100M özkaynaklı, %10 ROE'li bir firma ROE'sini %11'e ÇIKARIRSA, HİÇ yeniden yatırım YAPMASA BİLE %10 kazanç büyümesi KAYDEDER. Bu, YENİ yatırımlardaki İYİLEŞMEDEN (normal temel büyüme) AYRIŞTIRILMALIDIR — SADECE mevcut varlıklardaki verimlilik ARTIŞINDAN kaynaklanır. AZALAN ROE'nin etkisi İSE ORANSIZ BÜYÜK bir büyüme DÜŞÜŞÜ yaratır. (s.184-186)
- **İLKE-87 (Sermaye getirisi/ROC ölçüm sorunları):** Defter değeri MEVCUT yatırımlardaki sermayeyi DOĞRU YANSITMAYABİLİR (tarihsel maliyet + amortisman KARARLARI yüzünden) — R&D/operating lease VARLIĞI kapitalize EDİLMEMİŞSE ROC YAPAY OLARAK ŞİŞER; ayrıca MEVCUT yatırımların getirisi, GELECEKTEKİ (marjinal) yatırımların getirisiyle AYNI OLMAYABİLİR — bu fark UZUN VADEDE (ileri yıllara gidildikçe) BÜYÜR. (s.188-189)
- **İLKE-88 (3 büyüme senaryosu):** (1) İSTİKRARLI ROC — büyüme = yeniden yatırım oranı × ROC (sabit); (2) ARTAN/DEĞİŞEN ROC — büyümeye VERİMLİLİK bileşeni EKLENİR (İLKE-86 ile AYNI mantık, firma seviyesinde); (3) NEGATİF ROC (zarar eden firmalar) — GELİRDEN başlanarak YUKARI DOĞRU tahmin yapılır: önce gelir büyümesi, sonra hedef faaliyet marjına YAKINSAMA, sonra satış/sermaye oranıyla yeniden yatırım tahmini. (s.186, 193)
- **İLKE-89 ("Değişen ROC" firma tipleri):** (1) DÜŞÜK ROC'lu firmalar VERİMLİLİK/marj İYİLEŞTİRDİKÇE — bu durumda KÜÇÜK ROC artışları (örn. %1'den %2'ye) BÜYÜME ORANINDA ORANTISIZ BÜYÜK sıçrama yaratır (kazanç 2 KATINA çıkar → %100 büyüme oranı); (2) YÜKSEK ROC'lu firmalar rekabet GİRİŞİYLE getirilerinin (hem YENİ HEM MEVCUT yatırımlarda) ERİMESİNİ BEKLEYENLER. (s.191-192)
- **İLKE-90 (Gelir büyümesi tahmininde 5 dikkat noktası):** (1) gelir arttıkça büyüme HIZI AZALIR ($2M'lik firma için 10 kat artış makul, $2B'lik firma için DEĞİL); (2) bileşik büyüme oranları GÖRÜNÜŞTE düşük olsa da UZUN VADEDE MASİF etki yaratır (yıllık %40 × 10 yıl = 40 KAT); (3) tahmin edilen $ geliri, PAZARIN TOPLAM BÜYÜKLÜĞÜNE göre MANTIK KONTROLÜ edilmeli (10 yıl sonra %90-100 pazar payı ÇIKIYORSA varsayım GÖZDEN GEÇİRİLMELİ); (4) gelir büyümesi VARSAYIMLARI faaliyet marjı VARSAYIMLARIYLA TUTARLI olmalı (agresif fiyatlama = yüksek büyüme AMA düşük marj); (5) rekabet yapısı/firmanın büyümeyi KALDIRMA kapasitesi hakkında SÜBJEKTİF yargı GEREKİR. (s.193-194) [→ KONTROL LİSTESİ J]
- **İLKE-91 (Satış/Sermaye Oranı):** Gelir büyümesini yeniden yatırım ihtiyacına BAĞLAYAN köprü oran — her 1$'lık YATIRILAN sermayenin NE KADAR gelir ÜRETTİĞİNİ ölçer. DÜŞÜK satış/sermaye oranı YATIRIM İHTİYACINI ARTIRIR (nakit akışını AZALTIR); YÜKSEK oran TERSİNİ yapar. Tahmin için hem FİRMANIN KENDİ geçmişine hem SEKTÖR ORTALAMASINA bakılır. (s.198)
- **İLKE-92 (Satış/sermaye oranı TUTARLILIK kontrolü):** Kullanılan satış/sermaye oranından TÜRETİLEN yıllık ROC'lar, HEM sektör ORTALAMASI HEM firmanın KENDİ sermaye MALİYETİYLE karşılaştırılarak SINANMALIDIR — örnek: %10 sermaye maliyetli, %15 sektör ortalamalı bir sektörde %40 ROC ÇIKMASI, yatırımın (satış/sermaye oranının) ÇOK DÜŞÜK/YETERSİZ TUTULDUĞUNU gösterir. (s.198-199)
- **İLKE-93 (Terminal değer — 3 yöntem, SADECE 1'İ TUTARLI):** (1) TASFİYE değeri (defter bazlı VEYA kazanç gücü bazlı) — firmanın SONLU ömrü olduğu senaryolar için; (2) ÇARPAN yaklaşımı — BASİT ama TEHLİKELİ: emsal firmalardan türetilen çarpan kullanılırsa, DCF ile GÖRELİ değerlemeyi TEHLİKELİ biçimde KARIŞTIRIR (artık "içsel değer" DEĞİL karma bir sonuçtur); (3) İSTİKRARLI BÜYÜME modeli — SADECE TUTARLI DCF yöntemidir (temelleri sağlamsa). (s.200-202)
- **İLKE-94 (İstikrarlı büyüme oranının SINIRI):** Hiçbir firma SONSUZA dek FAALİYET GÖSTERDİĞİ EKONOMİNİN büyüme oranından YÜKSEK büyüyemez (aksi halde SONSUZDA ekonominin TAMAMINI YUTAR — matematiksel imkânsızlık); firma SADECE YEREL değil ÇOKULUSLU/KÜRESEL çalışıyorsa sınır KÜRESEL ekonomi büyümesidir. PRATİK BASİT KURAL: istikrarlı büyüme oranı, DEĞERLEMEDE KULLANILAN RİSKSİZ ORANI AŞMAMALIDIR (risksiz oran = reel büyüme+enflasyon özdeşliğinden). (s.202-204)
- **İLKE-95 (İstikrarlı dönem firma karakteristiklerinin ZORUNLU DÜZELTMESİ):** Yüksek büyüme döneminden istikrarlı döneme geçerken 4 değişken TUTARLI hale GETİRİLMELİDİR: (1) BETA piyasa ortalamasına (1'e, en fazla 1,2'ye — ABD firmalarının 2/3'ü 0,8-1,2 bandında) YAKINSAMALI; (2) SERMAYE/ÖZKAYNAK GETİRİSİ (fazla getiri) SEKTÖR ORTALAMASINA yakınsamalı (TAMAMEN sıfırlanması ZORUNLU DEĞİL — rekabet avantajları BİRDEN yok OLMAZ, ama sonsuza dek YÜKSEK fazla getiri VARSAYIMI da GÜVENİLMEZ); (3) BORÇ ORANI olgun sektör firmaları seviyesine YÜKSELMELİ (kaldıraç kapasitesi büyüdükçe artar) — kredi notu/maliyet de BUNA GÖRE yeniden tahmin edilmeli; (4) YENİDEN YATIRIM/TUTMA ORANI, istikrarlı büyüme oranıyla İÇ TUTARLI olacak şekilde (g/ROE veya g/ROC formülüyle) TÜRETİLMELİDİR — RASTGELE bir sayı DEĞİL. [→ FORMÜL-49/50, KONTROL LİSTESİ K] (s.204-207)
- **İLKE-96 (Büyüme-değer İLİŞKİSİNİN matematiksel ispatı):** Sermaye getirisi SERMAYE MALİYETİNE EŞİTSE, istikrarlı büyüme oranını DEĞİŞTİRMENİN DEĞER ÜZERİNDE HİÇBİR ETKİSİ YOKTUR (terminal değer formülü matematiksel olarak SADELEŞİR — büyümenin YARATTIĞI EK nakit akışı, YARATTIĞI EK yeniden yatırım İHTİYACIYLA TAM DENGELENİR). Değer SADECE sermaye getirisi maliyetin ÜZERİNDEYSE büyümeyle ARTAR. Bu, "%0 büyüme varsayımının değeri DEĞİŞTİRMEDİĞİ" somut örnekle (Alloy Mills illüstrasyonu) DOĞRULANMIŞTIR. [→ BAYRAK-13] (s.207-209)
- **İLKE-97 (Geçiş modeli seçimi):** (1) 2 AŞAMALI (yüksek büyümeden İSTİKRARLIYA ANİ geçiş) — ORTA büyüme oranlı firmalar için uygun (geçiş DRAMATİK değilse); (2) 3 AŞAMALI (yüksek büyüme + KADEMELİ geçiş dönemi) — ÇOK yüksek büyümeli firmalar için, risk/getiri/yeniden-yatırım TÜMÜNÜN KADEMELİ değişimine izin verir; (3) N AŞAMALI (her yıl AYRI karakteristik) — GENÇ veya NEGATİF marjlı firmalar için EN UYGUN. Not: istikrarlı büyüme oranından DAHA DÜŞÜK bir "yüksek büyüme" dönemi de MÜMKÜNDÜR (örn. ilk 5 yıl %2, sonra %4'e YÜKSELME). (s.211-212)
- **İLKE-98 (3 nakit akışı tahmin yaklaşımı ve RİSKLERİ):** (1) BEKLENEN DEĞER — her dönem için TEK bir en iyi tahmin (iyi/kötü senaryoları ZIMNEN İÇEREN); riskleri: "en iyi durum"/"muhafazakâr" tahminlerin YANLIŞLIKLA beklenen değer YERİNE kullanılması, İFLAS OLASILIĞININ göz ardı edilmesi (going-concern VARSAYIMI), yönetimin GERÇEK ZAMANLI ÖĞRENME/UYUM YETENEĞİNİN modellenememesi (real-option eleştirisi). (2) SENARYO ANALİZİ — iyimser/kötümser aralık; RİSKİ: senaryolar SPEKTRUMUN UÇLARINI kapsıyorsa (en iyi/en kötü) sonuç aralığı O KADAR GENİŞ olur ki KARAR VERMEDE İŞE YARAMAZ (15$-70$ aralığı 40$'lık piyasa fiyatı için ANLAMSIZDIR). (3) SİMÜLASYON — her girdi için DAĞILIM tahmini + tekrarlı örnekleme; 2 YAYGIN YANLIŞ ANLAMA: simülasyon çıktısının OTOMATİK "risk ayarlı" olduğu sanılması (HALA risk ayarlı iskonto oranı GEREKİR) ve RİSKİN ÇİFT SAYILMASI (hem iskonto oranında hem "değerin düşük çıkma OLASILIĞI" ile AYRICA). (s.212-215)

## Formüller (devam)

- **FORMÜL-25 — FCFE (Serbest Nakit Akışı — Özkaynağa, TAM tanım)**
  - Formül: `FCFE = Net Kâr - Net Sermaye Harcaması - ΔNoncash İşletme Sermayesi + Net Borç İhracı (yeni borç - anapara ödemesi)`
  - QuaxisLabs karşılığı: **VERİ EKSİK (kısmen)** — `net_income` VAR; Net Sermaye Harcaması (Capex verisi YOK), ΔNoncash İşletme Sermayesi (ham `current_assets`/`short_term_liabilities` VAR ama "noncash" arındırılmış — nakit ve kısa vadeli faizli borç çıkarılmış — versiyonu HESAPLANMIYOR), Net Borç İhracı (borç ihraç/geri ödeme AYRI kalemler olarak YOK, sadece dönem-sonu STOK `financial_debt` VAR) — TAMAMI eksik. `valuation.py`'nin Damodaran bloğu bu YÜZDEN doğrudan bu formülü DEĞİL, basitleştirilmiş `FCFE = TTM_Net_Kâr × (1-reinvestment_rate)` kısayolunu kullanıyor (reinvestment_rate=g/ROE ÖZDEŞLİĞİNDEN türetilir, ham capex/wc/borç verisi GEREKTİRMEZ).

- **FORMÜL-26 — FCFE (Sabit Borç Oranı ile Basitleştirilmiş)**
  - Formül: `FCFE = Net Kâr - (1-δ) × (Net Sermaye Harcaması + ΔİşletmeSermayesi)` (δ = borçla finanse edilen oran, sabit hedef borç oranı varsayımıyla net borç ödemesi terimi elenir)
  - QuaxisLabs karşılığı: Aynı VERİ EKSİKLİĞİ (FORMÜL-25).

- **FORMÜL-27 — FCFF (Serbest Nakit Akışı — Firmaya)**
  - Formül: `FCFF = Faaliyet Kârı × (1-Vergi Oranı) - Net Sermaye Harcaması - ΔNoncash İşletme Sermayesi`
  - QuaxisLabs karşılığı: `operating_profit`/`ebitda` VAR; vergi oranı XI_29'da `income_before_tax`/`tax_provision` YOK (efektif oran hesaplanamaz, sadece STATİK varsayılan kullanılabilir); Net Sermaye Harcaması VE ΔNoncash İşletme Sermayesi (FORMÜL-25 ile AYNI eksiklik) — **VERİ EKSİK**.

- **FORMÜL-28 — R&D Kapitalizasyonu: Araştırma Varlığı Değeri**
  - Formül: `Araştırma Varlığı = Σ [(Amortismansız Kalan Oran)_i × R&D_(t-i)]` (i=0'dan amortisman ömrüne, düz-hat amortisman varsayımıyla)
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — R&D gideri standalone alan olarak isyatirim.py/sec_edgar.py'de YOK (bu, Buffett turundan beri KÜMÜLATİF olarak tekrarlanan bir eksiklik).

- **FORMÜL-29 — R&D Kapitalizasyonu Sonrası Düzeltilmiş Faaliyet Kârı**
  - Formül: `Düzeltilmiş Faaliyet Kârı = Raporlanan Faaliyet Kârı + Bu Yılki R&D Gideri - Araştırma Varlığının Bu Yılki Amortismanı`
  - QuaxisLabs karşılığı: R&D verisi eksikliği (FORMÜL-28) nedeniyle **UYGULANAMAZ**.

- **FORMÜL-30 — R&D Expensing'in Ekstra Vergi Avantajı**
  - Formül: `Ekstra Vergi Avantajı = (R&D Gideri - Araştırma Varlığı Amortismanı) × Vergi Oranı`
  - QuaxisLabs karşılığı: R&D + vergi oranı İKİLİ eksiklik (FORMÜL-17/18, FORMÜL-28) — **UYGULANAMAZ**.

- **FORMÜL-31 — Operating Lease Sonrası Düzeltilmiş Faaliyet Kârı (kısayol/yaklaşık versiyon)**
  - Formül: `Düzeltilmiş Faaliyet Kârı ≈ Raporlanan Faaliyet Kârı + İma Edilen Faiz Gideri (Kira Borcu Değeri × Pretax Cost of Debt)`
  - QuaxisLabs karşılığı: Kira taahhüt takvimi eksikliği (bkz. Kısım 1 FORMÜL-23) — **VERİ EKSİK**.

- **FORMÜL-32 — Efektif Vergi Oranı**
  - Formül: `Efektif Vergi Oranı = Ödenen/Tahakkuk Eden Vergi ÷ Raporlanan Vergi Öncesi Kâr`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — `income_before_tax`/`tax_provision` XI_29'da YOK (sadece `STANDARD_ITEM_MAP_FINANSMAN`, finansman şirketleri şemasında var); bu Kısım 1'de de (FORMÜL-18 bağlamında) tespit edilen AYNI kök eksiklik, artık İKİNCİ kez bu kitapta doğrulandı.

- **FORMÜL-33 — Noncash İşletme Sermayesi (Değerleme-Amaçlı Düzeltilmiş Tanım)**
  - Formül: `Noncash İşletme Sermayesi = (Dönen Varlıklar - Nakit ve Menkul Kıymetler) - (Kısa Vadeli Yükümlülükler - Kısa Vadeli Faizli Borç)`
  - QuaxisLabs karşılığı: **KISMEN VAR** — `current_assets`, `short_term_liabilities`, `cash` ham alanları HAZIR; ancak `calculator.py`'de bu "noncash" DÜZELTİLMİŞ oran HESAPLANMIYOR (mevcut `current_ratio` = `current_assets/short_term_liabilities`, HAM/düzeltilmemiş tanım kullanıyor). `fundamental_screens.py`'nin Greenblatt bloğundaki `net_working_capital = current_assets - short_term_liabilities` da AYNI HAM tanımı kullanıyor (nakit/kısa-vadeli-borç arındırması YOK) — DÜŞÜK MALİYETLİ bir potansiyel iyileştirme: nakit zaten `cash` alanından ÇIKARILABİLİR, kısa vadeli faizli borç için `short_term_financial_debt` (itemCode "2AA") ZATEN mevcut.

- **FORMÜL-34 — Temettü Verimi**
  - Formül: `Temettü Verimi = Hisse Başı Temettü (DPS) ÷ Piyasa Fiyatı`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — DPS/temettü verisi hiçbir fetcher'da YOK (kitaplar arası EN SIK tekrarlanan açık, bkz. Kısım 1 sonu).

- **FORMÜL-35 — Nakit Getirisi/FCFE Oranı (Cash Returned to FCFE Ratio)**
  - Formül: `Oran = (Ödenen Temettü + Hisse Geri Alımı) ÷ FCFE`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — hem pay (temettü + geri alım verisi YOK) hem payda (FCFE, FORMÜL-25 eksikliği) eksik.

- **FORMÜL-36 — Aritmetik Ortalama Büyüme Oranı**
  - Formül: `Aritmetik Ortalama = (1/n) × Σ gt` (gt = her yılın büyüme oranı)
  - QuaxisLabs karşılığı: **VERİ EKSİK (yapısal)** — `trends.py`'nin 12-çeyrek/~3 yıllık penceresi kitabın önerdiği 5-10 yıllık geçmiş kazanç serisini SAĞLAMIYOR; bu, Graham/Buffett turlarında da TEKRARLANAN "10+ yıllık trend serisi yok" yapısal eksikliğinin YİNE karşımıza çıkışı.

- **FORMÜL-37 — Geometrik Ortalama Büyüme Oranı**
  - Formül: `Geometrik Ortalama = (Kazanç_bugün / Kazanç_(bugün-n)) ^ (1/n) - 1`
  - QuaxisLabs karşılığı: Aynı yapısal eksiklik (FORMÜL-36).

- **FORMÜL-38 — HBK Büyüme Oranı (Temel, Tutma Oranı × ROE)**
  - Formül: `g = b × ROE` (b = tutma oranı = 1 - temettü dağıtım oranı)
  - QuaxisLabs karşılığı: **KISMEN VAR** — `roe_annualized` HAZIR; tutma oranı (b) DPS/temettü eksikliği nedeniyle HESAPLANAMIYOR — `valuation.py`'nin Damodaran bloğundaki `reinvestment_rate = g/ROE` özdeşliği aslında BU formülün TERSİNE ÇEVRİLMİŞ (g biliniyormuş gibi varsayılıp b geriye çözülen) bir versiyonudur, kitabın kendi yönünde (b'den g'ye) DOĞRUDAN UYGULANAMIYOR.

- **FORMÜL-39 — Net Kâr Büyüme Oranı (Genişletilmiş, Yeni Hisse İhracını da Kapsar)**
  - Formül: `g(Net Kâr) = Özkaynak Yeniden Yatırım Oranı × ROE`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — Özkaynak Yeniden Yatırım Oranı (FORMÜL-40) eksikliğine bağlı.

- **FORMÜL-40 — Özkaynak Yeniden Yatırım Oranı**
  - Formül: `Oran = (Net Sermaye Harcaması + ΔNoncash İşletme Sermayesi - Net Borç İhracı) ÷ Net Kâr`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** (Capex + net borç ihracı verisi yok).

- **FORMÜL-41 — ROE (Kaldıraç Ayrıştırmalı)**
  - Formül: `ROE = ROC + (D/E) × (ROC - Vergi Sonrası Ortalama Faiz Oranı)`
  - QuaxisLabs karşılığı: `roe_annualized` DOĞRUDAN VAR (bu ayrıştırılmış türetimi GEREKTİRMEDEN); D/E hesaplanabilir ama vergi sonrası faiz oranı (`interest_expense` eksikliği, Kısım 1 FORMÜL-17/18) nedeniyle bu AYRIŞTIRILMIŞ formül UYGULANAMAZ — mevcut ROE zaten DOĞRUDAN hesaplı olduğundan pratik ÖNEM DÜŞÜK.

- **FORMÜL-42 — Marjinal ROE**
  - Formül: `Marjinal ROE = ΔNet Kâr(bu yıl) ÷ ΔÖzkaynak Defter Değeri(önceki yıl)`
  - QuaxisLabs karşılığı: **VAR (ucuz eklenti)** — `net_income` ve `equity` her ikisi de ÇOK dönemli (TTM/YoY/QoQ) olarak MEVCUT; bu oran `calculator.py`'ye tek satırlık bir HESAPLAMA olarak EKLENEBİLİR — hiçbir yeni ham veri GEREKTİRMEZ, standart ROE'nin (`roe_annualized`) YANINDA "yeni yatırım kalitesi" sinyali sağlar.

- **FORMÜL-43 — Verimlilik Kaynaklı Ek Büyüme**
  - Formül: `Ek Büyüme = (ROE_t - ROE_(t-1)) ÷ ROE_(t-1)`
  - QuaxisLabs karşılığı: **VAR (ucuz eklenti)** — `roe_annualized`'in YoY serisi (zaten `trends.py`'de İZLENEBİLİR aralıkta, en az 4-5 çeyrek) üzerinden DOĞRUDAN hesaplanabilir.

- **FORMÜL-44 — Faaliyet Kârı Büyüme Oranı (İstikrarlı ROC Senaryosu)**
  - Formül: `g = Yeniden Yatırım Oranı × ROC`
  - QuaxisLabs karşılığı: **KISMEN VAR/PARALEL** — `fundamental_screens.py`'nin Greenblatt bloğu (`return_on_capital_pct = EBIT / (Net Çalışma Sermayesi + Maddi Duran Varlık)`) KAVRAMSAL OLARAK Damodaran'ın ROC tanımına (vergi ÖNCESİ versiyon, after-tax DEĞİL) YAKINDIR — Yeniden Yatırım Oranı (FORMÜL-45) eksikliği nedeniyle `g` YİNE DE doğrudan TÜRETİLEMİYOR, ama ROC bileşeni HAZIR bir başlangıç noktası sunuyor.

- **FORMÜL-45 — Yeniden Yatırım Oranı (Firma, Reinvestment Rate)**
  - Formül: `Oran = (Net Sermaye Harcaması + ΔNoncash İşletme Sermayesi) ÷ Vergi Sonrası Faaliyet Kârı`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** (Capex verisi yok) — `valuation.py`'nin Damodaran bloğundaki `reinvestment_rate = g/ROE` kısayolu TAM OLARAK bu formülün YERİNE (ham capex olmadan) İKAME olarak tasarlanmıştır.

- **FORMÜL-46 — Satış/Sermaye Oranıyla Yeniden Yatırım Tahmini**
  - Formül: `Yıllık Yeniden Yatırım = ΔGelir ($) ÷ Satış-Sermaye Oranı`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — Satış/Sermaye oranı hesaplamak için TOPLAM sermaye (borç+özkaynak, veya invested capital) VE gelir GEREKİR; `total_assets`/`equity`/`financial_debt` VAR ama bu oranı DOĞRUDAN hesaplayan bir alan `calculator.py`'de YOK — DÜŞÜK MALİYETLİ bir eklenti adayı (ham veri ÇOĞU zaten mevcut, sadece bir oran hesaplaması eksik).

- **FORMÜL-47 — İstikrarlı Dönem Terminal Değer (Özkaynak)**
  - Formül: `Terminal Değer(Özkaynak) = CF_equity,(n+1) ÷ (Cost of Equity_n - g_n)`
  - QuaxisLabs karşılığı: `valuation.py`'nin Damodaran bloğundaki `equity_value = fcfe * (1 + g_pct/100) / ((cost_of_equity_pct - g_pct)/100)` satırı BU formülün (SADECE tek aşamalı, "n=0" — yani BAŞTAN istikrarlı büyüme kabul edilen) ÖZEL HALİDİR — ZATEN MEVCUT ve UYGULANIYOR (Kısım 1'de de not edildi).

- **FORMÜL-48 — İstikrarlı Dönem Terminal Değer (Firma)**
  - Formül: `Terminal Değer(Firma) = FCFF_(n+1) ÷ (WACC_n - g_n)`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — WACC hiç hesaplanmıyor (Kısım 1 FORMÜL-21), FCFF de (FORMÜL-27) eksik veriye bağlı.

- **FORMÜL-49 — İstikrarlı Dönem Tutma Oranı (Özdeşlikten Türetilmiş)**
  - Formül: `b_n = g_n ÷ ROE_n`
  - QuaxisLabs karşılığı: **VAR, ZATEN UYGULANIYOR** — `valuation.py`'nin `reinvestment_rate = g_pct / roe_pct` satırı BİREBİR bu formüldür (kitabın "istikrarlı dönemde tutma oranı büyüme oranına ve ROE'ye göre TÜRETİLMELİDİR, rastgele seçilmemelidir" ilkesinin — İLKE-95 — QuaxisLabs'taki ZATEN DOĞRU uygulamasıdır).

- **FORMÜL-50 — İstikrarlı Dönem Yeniden Yatırım Oranı (Firma)**
  - Formül: `Yeniden Yatırım Oranı_n = g_n ÷ ROC_n`
  - QuaxisLabs karşılığı: FORMÜL-49'un FİRMA-seviyesi (ROE yerine ROC) karşılığı — QuaxisLabs SADECE ÖZKAYNAK versiyonunu (FORMÜL-49) uyguluyor, FİRMA/FCFF versiyonu WACC eksikliği nedeniyle **UYGULANMIYOR**.

- **FORMÜL-51 — Tasfiye Değeri (2 Yöntem)**
  - Formül: (Defter bazlı) `Tasfiye Değeri = Defter Değeri × (1+enflasyon)^yıl`; (Kazanç gücü bazlı) `Tasfiye Değeri = Σ [Beklenen Nakit Akışı_t ÷ (1+r)^t]` (tasfiye SONRASI kalan ömür için)
  - QuaxisLabs karşılığı: **UYGULANMIYOR/KAPSAM DIŞI** — QuaxisLabs bir "going concern" (devam eden işletme) tarayıcısıdır, tasfiye senaryosu ÜRETMEZ; defter değeri versiyonu için `equity`/`total_assets` teorik olarak KULLANILABİLİR ama bu senaryo şu an ÜRÜN KAPSAMI DIŞINDA.

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| Cisco R&D amortisman ömrü (2005 örneği) | **5 yıl** | Yazılım/teknoloji firmaları için tipik varsayım (ilaç firmalarında DAHA UZUN) | Ch.3, s.123-124 |
| Cisco R&D gideri (FY2005) → Araştırma Varlığı Değeri | $3.320M → **$9,918M** (araştırma varlığı) | Kapitalize edilmiş R&D'nin bilanço/kârlılık etkisine somut örnek | Ch.3, s.124-125 |
| Target operating lease borç değeri eklenmesi | $9.538M (konvansiyonel borç) → **$11.243M** (+ $1.704,82M kira borcu) | Kısım 1 FORMÜL-23'ün somut uygulama örneği | Ch.3, s.128-129 |
| ABD medyan efektif vergi oranı (Ocak 2005) | **~%32** | Bazı firmalarda %100'ü aşan veya negatif efektif oranlar GÖZLENDİ | Ch.3, s.135 |
| ABD marjinal federal + eyalet/yerel kurumsal vergi oranı | **~%40** (federal %35 + ~%5) | Terminal value hesaplarında KULLANILMASI gereken oran | Ch.3, s.135-136 |
| Sirius Satellite Radio — NOL sonrası ilk vergi ödeme yılı oranı | **%28,05** (yıl 9), sonra **%35** (yıl 10+, marjinal) | NOL'lü genç firmalarda kademeli vergi oranı artışına somut örnek | Ch.3, s.141-142 |
| NYSE ortalama temettü/FCFE oranı (2004) | **%60** | Firmaların ÇOĞU ödeyebileceğinden AZ dağıtıyor | Ch.3, s.161-162 |
| ABD medyan/ortalama temettü verimi (Ocak 2005) | Medyan **~%2**, ortalama **%2,4** | SADECE temettü ödeyen hisseler arasında | Ch.3, s.157-158 |
| Temettü artış:kesinti oranı | En az **5:1** | Temettülerin "yapışkanlığının" ampirik kanıtı | Ch.3, s.162-163 |
| Little (1960) — ardışık dönem kazanç büyümesi korelasyonu | **~0,02** (ortalama) | "Higgledy piggledy growth" — geçmiş büyüme geleceği ÇOK ZAYIF öngörür | Ch.4, s.173-174 |
| Stable-period beta kuralı (pratik) | **≤ 1,2** (ABD firmalarının 2/3'ü 0,8-1,2 bandında) | İstikrarlı dönem beta TAVANI | Ch.4, s.204-205, dipnot 12 |
| İstikrarlı büyüme oranı TAVANI (pratik kural) | **≤ Risksiz Oran** | Coca-Cola örneği: nominal ABD$ %4 / reel %2 (2006 başı) | Ch.4, s.203-204 |
| Titan Cement — 5 yıllık (2000-2004) ROC/yeniden yatırım aralığı | ROC ort. **~%20** (2002-04); yeniden yatırım oranı **%17,48 – %72,01** | Yeniden yatırım oranının YILDAN YILA AŞIRI oynaklığına somut örnek | Ch.4, s.190-191 |
| Goldman Sachs — istikrarlı dönem varsayımları (illüstrasyon) | Beta **1,00**, ROE **%12**, payout **%66,67**, cost of equity **%8,5** | Yüksek büyümeden istikrarlı büyümeye geçiş varsayım seti örneği | Ch.4, s.209-210 |
| Sirius Radio — hedef istikrarlı faaliyet marjı | **%20** (sektör ortalaması) | Negatif ROC senaryosunda "yukarı yakınsama" hedefi somut örneği | Ch.4, s.196-197 |

## Kontrol listeleri (devam)

**Kontrol Listesi D — 4 Tür Olağanüstü/Özel Kalem ve Muamele Yöntemi (Ch.3, s.132-134):**
1. GERÇEKTEN tek seferlik → tamamen ÇIKAR (gelir/gider hesaplamasından).
2. DÜZENLİ ARALIKLARLA tekrarlayan (örn. her 3 yılda 1 restructuring) → YILLIK ORTALAMAYA YAY, "olağanüstü" SAYMA.
3. HER YIL tekrarlayan ama OYNAK → çok yıllık ORTALAMA ile NORMALLEŞTİR.
4. İŞARET DEĞİŞTİREN (örn. döviz kuru çevirisi) → GÖZ ARDI ET (zamanla TERSİNE döneceği varsayımıyla).

**Kontrol Listesi E — Kazanç Yönetimi Teknikleri (Ch.3, s.131-132 — kırmızı bayrak tespiti için TEMEL liste):**
1. İleriye dönük PLANLAMA (yatırım/varlık satışı zamanlamasıyla kazancı DÜZLEŞTİRME — ZARARSIZ sayılabilir).
2. GELİR TANIMA zamanlaması (MUHAFAZAKAR gösterip SONRAKİ döneme SAKLAMA — Microsoft Windows 95 örneği).
3. ÇEYREK SONUNDA erken gelir kaydı (ürün SEVKİYATI + gelir kaydı — MicroStrategy örneği). [→ BAYRAK-09]
4. Operasyonel giderlerin SERMAYE gideri gibi GÖSTERİLMESİ (AOL CD maliyeti örneği).
5. Büyük RESTRUCTURING/write-off (SONRAKİ çeyreklerin kazancını YAPAY ARTIRIR — IBM örneği). [→ BAYRAK-10]
6. REZERV kullanımı (iyi yıllarda MUHAFAZAKAR karşılık ayırıp kötü yıllarda BOZMA).
7. YATIRIM GELİRİ realizasyonu (defter değeri DÜŞÜK yatırımları SATIP kâr YAZMA — Intel örneği).

**Kontrol Listesi F — Çok Uluslu Firmalarda Marjinal Vergi Oranı, 3 Yaklaşım (Ch.3, s.136-137):**
1. Ülke gelirlerine göre AĞIRLIKLI ORTALAMA marjinal oran (dezavantaj: ağırlıklar ZAMANLA değişir).
2. ANA ÜLKE (incorporation) marjinal oranı (varsayım: yabancı kazanç ER YA DA GEÇ REPATRIATE edilir).
3. Her ülkenin gelirini AYRI TUTUP kendi marjinal oranını UYGULAMA — EN GÜVENLİ/DOĞRU yaklaşım.

**Kontrol Listesi G — Noncash İşletme Sermayesi Değişimi Tahmin Yöntemleri, 5 Seçenek (Ch.3, s.154-156):**
1. Ham $ değişimi + kazanç büyüme oranıyla BÜYÜT (EN AZ GÜVENİLİR — aşırı oynak).
2. Son yıl "%gelir" oranı × gelecek gelir DEĞİŞİMİ (DAHA İYİ, ama tek yıla BAĞIMLI).
3. MARJİNAL %gelir oranı (Δİşletme Sermayesi/ΔGelir, son yıl) — İŞ KARMASI DEĞİŞEN firmalar için uygun.
4. ÇOK YILLIK ORTALAMA "%gelir" oranı — yıldan yıla dalgalanmayı SMOOTH eder.
5. SEKTÖR ORTALAMASI "%gelir" oranı — çok OYNAK/ÖNGÖRÜLEMEZ geçmişi olan veya çok KÜÇÜK firmalar için EN UYGUN.

**Kontrol Listesi H — Firmaların FCFE'den Az Temettü Dağıtmasının 5 Nedeni (Ch.3, s.162-164):**
1. İstikrar arzusu (temettü KESİNTİSİNDEN kaçınma).
2. Gelecek yatırım ihtiyacı (ihraç MALİYETİ nedeniyle nakit TAMPONU tutma).
3. Vergi faktörleri (temettü/sermaye kazancı vergi FARKI, özellikle aile şirketlerinde).
4. Sinyal verme (artış=olumlu, kesinti=olumsuz piyasa TEPKİSİ).
5. Yönetici çıkarı (imparatorluk kurma güdüsü, kâr düşüşünü GİZLEYECEK nakit yastığı).

**Kontrol Listesi I — Yüksek Büyüme Süresini Belirleyen 3 Faktör (Ch.4, s.169):**
1. Firma büyüklüğü (KÜÇÜK firma + BÜYÜK toplam pazar = UZUN potansiyel yüksek büyüme).
2. Mevcut büyüme oranı VE fazla getiri MOMENTUMU.
3. Rekabet avantajının BÜYÜKLÜĞÜ ve SÜRDÜRÜLEBİLİRLİĞİ (EN KRİTİK faktör — giriş engelleri + yönetim kalitesi).

**Kontrol Listesi J — Gelir Büyümesi Tahmininde 5 Dikkat Noktası (Ch.4, s.193-194):**
1. Büyüme hızı, GELİR ARTTIKÇA azalır (büyüklük kısıtı).
2. Bileşik büyüme oranları GÖRÜNÜŞTE düşük olsa da UZUN VADEDE MASİF etki yaratır.
3. Tahmin edilen $ geliri PAZAR BÜYÜKLÜĞÜYLE mantık kontrolünden GEÇİRİLMELİ (aşırı pazar payı = ALARM).
4. Gelir büyümesi VARSAYIMLARI, faaliyet MARJI varsayımlarıyla TUTARLI olmalı.
5. Rekabet yapısı + firmanın büyümeyi KALDIRMA kapasitesi hakkında SÜBJEKTİF yargı ZORUNLUDUR.

**Kontrol Listesi K — İstikrarlı Döneme Geçişte Düzeltilmesi ZORUNLU 4 Değişken (Ch.4, s.204-207):**
1. BETA → piyasa ortalamasına (≤1,2) yakınsat.
2. FAZLA GETİRİ (ROC/ROE - maliyet) → sektör ortalamasına yakınsat (SIFIRLAMA ZORUNLU DEĞİL).
3. BORÇ ORANI → olgun sektör firmaları seviyesine YÜKSELT, kredi notu/maliyeti YENİDEN tahmin et.
4. YENİDEN YATIRIM/TUTMA ORANI → g/ROC veya g/ROE ÖZDEŞLİĞİNDEN TÜRET (rastgele SEÇME).

## Kırmızı bayraklar (devam)

- **BAYRAK-08 — "Fısıldanan Kazançlar" (Whispered Earnings) Aşımı Kırılganlığı:** Bir firma ÇOK SAYIDA ardışık çeyrekte (Microsoft: 40'ta 39, Intel BENZER) analist konsensüsünü İSTİKRARLI biçimde AŞIYORSA, piyasa RESMİ konsensüsün ÜZERİNDE GAYRIRESMİ bir "fısıltı" beklentisi OLUŞTURUR — firma resmi tahmini AŞSA BİLE fısıltının ALTINDA kalırsa hisse fiyatı DÜŞEBİLİR (Intel 1997: $2,10 EPS, konsensüs $2,06 AŞILDI ama fısıltı $2,15'ti, hisse %5 DÜŞTÜ). Nasıl tespit edilir: firmanın SON 8-12 çeyreklik "beklenti aşma" ORANINI ve TUTARLILIĞINI incele — aşırı istikrarlı/mükemmel aşım kaydı, doğal İŞ OYNAKLIĞIYLA TUTARSIZDIR. Gereken veri: çeyreklik analist konsensüs + gerçekleşen EPS SERİSİ (VERİ EKSİK — QuaxisLabs analist tahmini ÇEKMİYOR). (Ch.3, s.129-130)
- **BAYRAK-09 — Çeyrek Sonu Erken Gelir Kaydı (Revenue Front-Loading):** Zayıf bir çeyreğin SON GÜNLERİNDE dağıtıcı/perakendeciye ürün SEVK EDİP geliri o çeyreğe KAYDETMEK (MicroStrategy 1999 örneği: son 4 günde açıklanan anlaşmalar çeyreğin geliri olarak kaydedildi). Nasıl tespit edilir: büyük anlaşma açıklamalarının çeyrek SONUNA YIĞILIP yığılmadığını, SONRAKİ çeyreklerde BENZER büyüklükte iptal/iade OLUP OLMADIĞINI incele. Gereken veri: çeyrek İÇİ (aylık) gelir dağılımı + anlaşma AÇIKLAMA tarihleri (VERİ EKSİK). (Ch.3, s.130-131)
- **BAYRAK-10 — Restructuring/Write-off Sonrası Yapay Kazanç Sıçraması:** Büyük bir restructuring charge/write-off SONRASI (özellikle amortisman gideri/varlık tabanının KÜÇÜLTÜLMESİYLE) SONRAKİ dönemlerin kazancı YAPAY OLARAK ARTAR (IBM 1996 örneği: eski tesisleri silerek amortisman/gelir oranını %7'den %5'e düşürdü — tek başına vergi öncesi kârın %18'i kadar bir etki). Nasıl tespit edilir: BÜYÜK bir restructuring charge SONRASINDA amortisman/gelir ORANINDA ANİ bir düşüş var mı KONTROL ET. Gereken veri: restructuring charge tutarı + amortisman gideri SERİSİ (amortisman ham veri KISMEN VAR — `depreciation_amortization`, restructuring charge AYRI kalem olarak YOK). (Ch.3, s.132)
- **BAYRAK-11 — Akiziyon Sonrası "In-Process R&D" Write-off ile Kazanç Şişirme:** Bir akiziyon SONRASI büyük bir "devam eden R&D" write-off'u yapılması, SONRAKİ çeyreklerin (özellikle 4. çeyreğin) kazancını AKİZİYONUN GERÇEK MALİYETİNİ YANSITMADAN ARTIRIR (Deng&Lev 1999: 389 firma örnekleminde ORTALAMA %72 write-off oranı, sonraki 4. çeyrekte %22 kazanç artışı). Nasıl tespit edilir: büyük bir akiziyon TARİHİNİN HEMEN SONRASINDAKİ çeyreklerde OLAĞANDIŞI kazanç sıçraması var mı KONTROL ET. Gereken veri: akiziyon takvimi/tutarı + goodwill amortisman kalemi (VERİ EKSİK — QuaxisLabs akiziyon geçmişi ÇEKMİYOR). (Ch.3, s.134)
- **BAYRAK-12 — Giderek Daha Negatif Hale Gelen (Noncash) İşletme Sermayesi:** İşletme sermayesinin (veya değişiminin) SÜREKLİ/GİDEREK daha negatif hale gelmesi — kısa vadede "verimlilik" gibi görünse de (Wal-Mart/Dell tarzı tedarikçi kredisi stratejisi) GERÇEK bir maliyet TAŞIR (erken ödeme indirimi kaybı) VE derecelendirme kuruluşlarınca DEFAULT RİSKİ göstergesi SAYILIR — SONSUZA dek SÜRDÜRÜLEMEZ. Nasıl tespit edilir: noncash işletme sermayesi/gelir oranının ÇOK YILLIK TRENDİNİ izle — sürekli DÜŞÜŞ (daha negatife gidiş) bir uyarı sinyalidir. Gereken veri: `current_assets`/`short_term_liabilities`/`cash` QuaxisLabs'ta VAR ama "noncash" arındırılmış oran HESAPLANMIYOR (FORMÜL-33) — DÜŞÜK MALİYETLİ potansiyel eklenti. (Ch.3, s.155-157)
- **BAYRAK-13 — İstikrarlı Dönemde Sermaye Getirisinin Sermaye Maliyetinin ÇOK ÜZERİNDE Varsayılması:** Bir DCF modelinde İSTİKRARLI (terminal) dönem için ROC/ROE'nin sermaye/özkaynak MALİYETİNİN AŞIRI ÜZERİNDE (kalıcı fazla getiri) varsayılması, TEORİK OLARAK SÜRDÜRÜLEMEZ bir durumdur (rekabet fazla getiriyi ER YA DA GEÇ eritir) ve terminal değeri (dolayısıyla toplam değeri) YAPAY OLARAK ŞİŞİRMENİN EN YAYGIN yöntemlerinden biridir. Nasıl tespit edilir: modeldeki istikrarlı dönem ROC/ROE'sini SEKTÖR ORTALAMASI ve firmanın KENDİ sermaye/özkaynak MALİYETİYLE karşılaştır — kalıcı/büyük fark ŞÜPHE UYANDIRMALI. Gereken veri: uzun vadeli (terminal) varsayım seti — bu METODOLOJİK bir kontrol, QuaxisLabs'ın MEVCUT tekil-dönem verisiyle DOĞRUDAN taranamaz (bir DCF MODELİNİN kendisi incelenmelidir). (Ch.4, s.191-192, 207-209)

## Uygulama notları (devam)

**Nicel (skorlanabilir, düşük maliyetli eklenti adayları — bu Kısımda TESPİT edildi):**
- **Marjinal ROE** (FORMÜL-42, `ΔNet Kâr/Δönceki-yıl-Özkaynak`) — SIFIR yeni ham veri gerektirir, mevcut `net_income`/`equity` serilerinden HESAPLANABİLİR; standart ROE'nin YANINDA "yeni yatırım kalitesi" sinyali sunar.
- **Verimlilik Kaynaklı Ek Büyüme** (FORMÜL-43, `ΔROE/ROE_(t-1)`) — aynı şekilde SIFIR yeni veri, mevcut `roe_annualized` serisinden.
- **Noncash İşletme Sermayesi** (FORMÜL-33/BAYRAK-12) — nakit VE kısa vadeli faizli borcun (`short_term_financial_debt`, itemCode "2AA" ZATEN mevcut) mevcut `current_assets`/`short_term_liabilities`'ten ÇIKARILMASI — DÜŞÜK maliyetli, `fundamental_screens.py`'nin HAM `net_working_capital`'ini İYİLEŞTİREBİLİR.
- **Satış/Sermaye Oranı** (FORMÜL-46) — `total_assets`/`equity`/`financial_debt` üzerinden invested capital TÜRETİLEBİLİR, TEK bir oran hesaplaması eksik.

**Nitel (LLM yorumuna uygun):**
- Kazanç yönetimi teknikleri (Kontrol Listesi E, BAYRAK-08/09/10/11) — bunların ÇOĞU dipnot/haber/anlaşma DUYURUSU okuması gerektirir, sayısal tarama YERİNE bir LLM'in şirket haberlerini/açıklamalarını TARAYIP "bu bulgu VAR MI" diye SORULMASINA uygun.
- Yüksek büyüme süresi tahmini (Kontrol Listesi I) VE terminal değer/istikrarlı büyüme geçişi VARSAYIMLARININ TUTARLILIĞI (Kontrol Listesi K, BAYRAK-13) — NİTEL/YARGISAL bir değerlendirmedir, bir LLM'in "bu şirketin rekabet avantajı NE KADAR SÜRDÜRÜLEBİLİR" sorusuna YANIT ÜRETMESİNE uygun ama OTOMATİK SKORLANAMAZ.
- Gelir büyümesi/pazar payı mantık kontrolü (Kontrol Listesi J, madde 3) — LLM'e "bu büyüme oranı X yıl sonra firmayı pazarın %Y'sine getirir, bu MAKUL MÜ" diye SORULABİLİR.

**Veri eksikliği nedeniyle UYGULANAMAZ (öncelik sırasına göre, bu Kısımda EKLENEN/PEKİŞTİRİLEN):**
1. **Capex (Sermaye Harcaması) — TEKRAR (4. kez, Buffett + Kısım 1 + şimdi 2 kez bu Kısımda) doğrulandı** — FCFE/FCFF/yeniden yatırım oranı/Özkaynak Yeniden Yatırım Oranı formüllerinin (FORMÜL-25/26/27/40/45) TÜMÜNÜN ORTAK ENGELİ. QuaxisLabs'ın "TAMAMEN EKSİK" olarak zaten işaretlediği alan — bu Kısım bunun NE KADAR ÇOK formülü BLOKE ettiğini SOMUTLAŞTIRDI.
2. **R&D gideri — TEKRAR (3. kez) doğrulandı** — FORMÜL-28/29/30 (kapitalizasyon zinciri) bu tek veriye bağlı.
3. **Temettü + Hisse Geri Alımı — TEKRAR (6. kez, kitaplar arası EN SIK) doğrulandı** — FORMÜL-34/35, tutma oranı (FORMÜL-38) hesaplarının TAMAMI için gerekli.
4. **income_before_tax/tax_provision (XI_29) — TEKRAR (2. kez bu kitapta) doğrulandı** — FORMÜL-27/32'nin ortak engeli; efektif vergi oranı hesaplanamadığı için Ch.3'ün "vergi oranı seçimi" (İLKE-68/69/70) metodolojisi TAMAMEN teorik kalıyor.
5. **10+ yıllık geçmiş kazanç serisi — TEKRAR (6. kez, artık kitaplar-ötesi EN ISRARLI yapısal eksiklik) doğrulandı** — aritmetik/geometrik büyüme oranı hesaplarının (FORMÜL-36/37) ortak engeli; `trends.py`'nin 12-çeyrek penceresi bu bölümdeki hiçbir çok-yıllı büyüme formülü için YETERLİ DEĞİL.
6. **Net Borç İhracı/Geri Ödemesi (ayrı kalemler)** — Özkaynak Yeniden Yatırım Oranı (FORMÜL-40) için gerekli, sadece dönem-sonu STOK `financial_debt` VAR, AKIŞ (ihraç/ödeme) YOK.
