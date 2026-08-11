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

---

# KISIM 3 — Chapter 5-6: Equity Discounted Cash Flow Models + Firm Valuation Models

**Kapsam:** Chapter 5: Equity Discounted Cash Flow Models (PDF s.218-260), Chapter 6: Firm Valuation Models (PDF s.261-305) — Part One (Discounted Cash Flow Valuation)'ın SON iki bölümü. ID numaralandırması kesintisiz devam eder (İLKE-99'dan, FORMÜL-52'den, BAYRAK-14'ten, Kontrol Listesi L'den).

## İlkeler (devam)

**Chapter 5 — Equity Discounted Cash Flow Models:**

- **İLKE-99 (DDM'in temel prensibi):** Bir hissenin değeri, SONSUZA dek beklenen temettülerin bugünkü değeridir — elde tutma dönemi SONUNDAKİ beklenen fiyat da ZATEN o noktadan SONRAKİ temettülerin bugünkü değerinden TÜRER, bu yüzden model "fiyat" terimini İÇERMEDEN doğrudan temettülere indirgenebilir. (s.218-219)
- **İLKE-100 (Gordon Büyüme Modelinin 2 kritik uyarısı):** (1) Temettü büyüme oranı SONSUZA dek sürdüğü için firmanın DİĞER TÜM operasyonel ölçütleri (gelir, kazanç) de AYNI oranda büyümek ZORUNDADIR — aksi halde payout oranı SIFIRA veya SONSUZA yakınsar (istikrarsız durum); (2) "istikrarlı büyüme oranı" konusunda analistler ENFLASYON BEKLENTİSİ farkı, firmanın EKONOMİDEN DAHA YAVAŞ büyüme SEÇENEĞİ, ve BİRKAÇ yıllık üstün büyümeyi PRİM olarak EKLEME (max +%0,25-0,5, DAHA FAZLASI için 2/3 aşamalı modele geçilmeli) nedenleriyle YİNE DE FARKLI sonuçlara ULAŞABİLİR. (s.220-221)
- **İLKE-101:** Gordon modeli, ORTALAMA büyümesi istikrarlıya YAKIN olan DÖNGÜSEL firmalar için de KULLANILABİLİR (kazanç oynak olsa bile) — çünkü (a) temettüler kazançlardan DAHA DÜZ (smoothed) seyreder, (b) ortalama büyüme kullanmanın matematiksel etkisi KÜÇÜKTÜR. (s.221)
- **İLKE-102 (2 aşamalı DDM):** Patent koruması VEYA güçlü giriş engelleri gibi BELİRLİ/ÖNGÖRÜLEBİLİR bir "üstün büyüme SONU" olan firmalar için uygundur. İstikrarlı dönem payout oranı, İÇ TUTARLILIK için `1 - g/ROE` özdeşliğinden TÜRETİLMELİDİR (rastgele SEÇİLMEMELİ) — YÜKSEK büyüme firmasının beta'sı 2 olabilir ama İSTİKRARLI dönemde 0,8-1,2 bandına YAKINSAMALIDIR (Ch.4 kuralının TEKRARI). (s.222-223)
- **İLKE-103 (İma edilen büyüme oranı — "implied growth rate"):** Mevcut piyasa fiyatına ULAŞMAK için gereken büyüme oranı, İKİ şekilde YORUMLANABİLİR: (1) GÜVENLİK MARJI göstergesi (Goldman Sachs örneği: gerçek büyüme, analistin %16,82 baz senaryosundan HAYLI DÜŞÜK olsa bile hisse HALA ucuz kalabilir çünkü piyasa fiyatı sadece %2,6 büyüme İMA EDER); (2) analistin modelde EKSİK bıraktığı bir unsurun (örn. yatırım bankası kazançlarının DÖNGÜSELLİĞİ) İPUCU. (s.225-226)
- **İLKE-104 (H Modeli):** İki aşamalı modelin AKSİNE büyüme oranı ANİDEN DEĞİL DOĞRUSAL OLARAK (linear) yüksek başlangıç oranından (ga) istikrarlı orana (gn) 2H yıl İÇİNDE AZALIR. İKİ SINIRLAMASI VAR: (1) sapmalar (özellikle BÜYÜK sapmalar) KATI doğrusal yapıdan değeri BOZAR; (2) payout oranının HER İKİ AŞAMADA SABİT tutulması İÇSEL TUTARSIZLIK yaratır (büyüme DÜŞTÜKÇE payout genelde ARTAR) — bu yüzden DÜŞÜK/SIFIR temettülü firmalar için UYGUNSUZDUR. (s.226-228)
- **İLKE-105 (3 aşamalı DDM):** EN GENEL model — payout oranına HİÇBİR kısıt KOYMAZ, yüksek büyüme + geçiş + istikrarlı büyüme 3 AYRI aşamayı ayrı ayrı MODELLER. PRATİKTE, hem büyümesi HEM DE payout/riskinin ZAMAN İÇİNDE değişmesi beklenen (%25'i AŞAN "çok yüksek" büyümeli, kitabın kaba kuralına göre — istikrarlı büyüme %6-8 iken) firmalar için EN UYGUN modeldir. (s.228-230, dipnot 4)
- **İLKE-106 (DDM'in 3 gücü):** (1) Temettü, firmadan gelen TEK "ELLE TUTULUR" nakit akışıdır (FCFE tahminleri her zaman TAHMİN olarak KALIR — yatırımcı Microsoft'un nakit bakiyesinden PAY TALEP EDEMEZ); (2) DAHA AZ VARSAYIM gerektirir (capex/amortisman/işletme sermayesi TAHMİN edilmez, sadece geçmiş temettü + büyüme oranı); (3) yöneticiler temettüyü OYNAK kazançlarla bile SÜRDÜRÜLEBİLİR seviyede tutmaya ÇALIŞIR — bu yüzden temettü bazlı değerleme ZAMAN İÇİNDE DAHA AZ OYNAKTIR. (s.232)
- **İLKE-107 (DDM'in 2 zaafı):** (1) FCFE'DEN AZ dağıtan firmalarda (nakit biriktiren) — model bu nakdi/değerini GÖZ ARDI EDER, DEĞERİ DÜŞÜK GÖSTERİR; (2) FCFE'DEN ÇOK dağıtan firmalarda (borç/yeni hisse ile finanse edilen temettü) — dış finansmanın SONSUZA DEK SÜRDÜRÜLEBİLECEĞİNİ ZIMNEN varsayarak DEĞERİ ABARTIR. (s.232-233)
- **İLKE-108 (DDM'in 3 UYGUN kullanım senaryosu):** (1) FCFE'yi AŞAN temettü ödeyen firmalarda TABAN/MUHAFAZAKAR değer sağlar (dağıtılmayan nakdin KÖTÜ yatırımlara/akiziyona harcanacağı varsayımıyla); (2) FCFE'yi ORTALAMA OLARAK dağıtan İSTİKRARLI/OLGUN firmalarda (özellikle eskiden düzenlenmiş telefon/elektrik şirketleri) GERÇEKÇİ tahmin verir; (3) capex/işletme sermayesi tahmininin ZOR/ANLAMSIZ olduğu sektörlerde (banka, yatırım bankası, sigorta — işletme sermayesi kavramı bu şirketlerde ANLAMSIZDIR VE düzenleyici sermaye oranları defter özkaynağına DAYANIR) TEK UYGULANABİLİR yöntemdir. [→ KONTROL LİSTESİ L] (s.233-234)
- **İLKE-109 (Genişletilmiş DDM — hisse geri alımı dahil):** ABD'de 2000'lerin başından itibaren hisse geri alımı ile dağıtılan nakit, KONVANSİYONEL temettüyü AŞMIŞTIR — "modifiye payout oranı" ((temettü+geri alım)/net kâr) TEK YIL yerine 4-5 YILLIK ORTALAMA olarak hesaplanmalıdır (geri alımlar temettü GİBİ düzleştirilmiş DEĞİLDİR, bir yıl $3 milyar geri alıp SONRAKİ 3 yıl HİÇ yapmayabilir). (s.234-235)
- **İLKE-110:** Hisse geri alımı özkaynak DEFTER DEĞERİNİ düşürerek ROE'yi YAPAY OLARAK ARTIRABİLİR — bu YÜKSELTİLMİŞ ROE, YENİ yatırımların MARJİNAL getirisi olarak KULLANILIRSA firma değeri ABARTILIR; DÜZELTME: son yıllardaki geri alımları defter özkaynağına GERİ EKLEYİP ROE'yi YENİDEN hesaplamak DAHA MAKUL bir sonuç verir. (s.235-236)
- **İLKE-111:** DDM, TEK bir şirket için OLDUĞU KADAR bir SEKTÖRE veya TÜM PİYASAYA da uygulanabilir — piyasa fiyatı toplam piyasa değeriyle, beta piyasanın KENDİSİ için 1 İLE (ihtiyaç YOK), sektör için SEKTÖR BETASI ile değiştirilir; TÜM firmaların BİRLEŞİK kazanç büyümesinin EKONOMİDEN uzun süre HIZLI OLAMAYACAĞI konusunda EK dikkat gerekir. (s.237)
- **İLKE-112 (FCFE modelinin temel prensibi):** FCFE'yi kullanmak, temettü YERİNE nakdi koymaktan FAZLASIDIR — FCFE'nin TAMAMEN dağıtıldığı ZIMNEN varsayılır, bunun 2 SONUCU vardır: (1) firma içinde GELECEKTE HİÇBİR nakit BİRİKMEZ; (2) beklenen büyüme, SADECE faaliyet varlıklarından gelen gelirin büyümesini YANSITIR (nakit/menkul kıymet GELİRİNİN büyümesini DEĞİL). (s.239)
- **İLKE-113:** FCFE modeli, halka açık bir şirketin hissedarını ÖZEL bir işletmenin sahibi GİBİ ele alır — bu, GÜÇLÜ bir KURUMSAL YÖNETİM sisteminin VARLIĞINI ZIMNEN varsayar: yöneticiler FCFE'yi dağıtmaya ZORLANAMASA bile, hissedarlar dağıtılmayan nakdin İSRAF EDİLMEMESİ için BASKI yapabildiği varsayılır. (s.239-240)
- **İLKE-114:** FCFE modelinde tutarlılık İÇİN 2 kritik değişiklik gerekir: standart TUTMA ORANI (retention ratio) yerine ÖZKAYNAK YENİDEN YATIRIM ORANI (equity reinvestment rate — net kârın NE KADARININ firmaya geri yatırıldığını ölçer, dağıtılmayan HERŞEYİN otomatik yeniden yatırıldığı varsayımı YERİNE); standart ROE yerine NONCASH (nakit dışı) ROE (nakit/menkul kıymet gelirinin VE defter değerinin ARINDIRILMIŞ hali) — model içinde ARTIK nakit BİRİKMEDİĞİ için. (s.240)
- **İLKE-115 (Sabit büyüme FCFE modeli — Gordon'un FCFE karşılığı):** Gordon modeliyle AYNI kısıtlara TABİDİR (istikrarlı büyüme ≤ ekonomi büyümesi, beta ~1). İstikrarlı dönem reinvestment tahmininde 2 yol: SEKTÖR ortalama capex/amortisman oranı KULLAN, VEYA `g/ROE` özdeşliğinden TÜRET. Firma istikrarlı VE FCFE'sini TAM dağıtıyorsa, sonuç Gordon modeliyle AYNI ÇIKAR. (s.241-242)
- **İLKE-116 (2 aşamalı FCFE modeli):** Terminal value hesabındaki reinvestment/beta/borç oranı İSTİKRARLI dönem karakteristikleriyle TUTARLI olmalıdır — YÜKSEK büyüme fazında capex, amortismanı BÜYÜK ÖLÇÜDE AŞABİLİR ama İSTİKRARLI fazda bu FARK DARALMALIDIR. (s.243-244)
- **İLKE-117 (E Modeli — 3 aşamalı FCFE):** Yüksek büyüme + geçiş + istikrarlı büyüme 3 aşaması İÇİN tasarlanmıştır — ÖZELLİKLE yakın gelecekte NEGATİF FCFE beklenen (agresif yeniden yatırım yapan) GENÇ/yüksek-büyüme firmaları için EN GERÇEKÇİ sonuçları verir: negatif nakit akışlarının bugünkü değeri, DOLAYLI olarak büyümeyi finanse etmek için gelecekte İHRAÇ EDİLECEK yeni hisselerin SEYRELME (dilution) etkisini de YAKALAR. (s.246-248)
- **İLKE-118 (FCFE'nin DDM'ye göre 2 avantajı):** (1) yönetimin temettü POLİTİKASINA BAĞIMLI DEĞİLDİR — "potansiyel temettüyü" (ne DAĞITILABİLECEĞİNİ) kullanır; (2) NEGATİF DEĞER alabilir (temettü ASLA negatif OLAMAZ) — yüksek yeniden yatırım ihtiyacı olan büyüme firmaları için GERÇEKÇİ bir özellik, bu firmaların GELECEKTE yeni hisse ihraç edeceğini modele DOLAYLI olarak dahil eder. (s.250-251)
- **İLKE-119 ("Yaygın Hata" — FCFE modelinde çift sayım):** FCFE'yi iskonto EDİP AYRICA firma içindeki nakit BİRİKİMİNİ ayrıca değere EKLEMEK bir ÇİFT SAYIM hatasıdır — FCFE modeli ZATEN TÜM nakdin dağıtıldığını (birikmediğini) VARSAYAR. [→ BAYRAK-15] (s.251)
- **İLKE-120 (FCFE modelinin sınırı):** Capex/amortisman/işletme sermayesi/net borç akışlarının tahmini İMKÂNSIZ/ANLAMSIZ olduğu durumlarda (finansal hizmetler firmaları, güvenilmez finansal bilgi) FCFE modeli KULLANILAMAZ — DDM'ye GERİ DÖNÜLMELİDİR. (s.252)
- **İLKE-121 (FCFE ve DDM ne zaman EŞİTLENİR):** (1) temettü=FCFE İSE (basit); (2) FCFE>temettü AMA fazla nakit ADİL FİYATLI (Net Bugünkü Değeri SIFIR) varlıklara YATIRILIYORSA — bu durumda DDM'de nakit BİRİKİMİNİN AYRICA TAKİP EDİLİP değere EKLENMESİ GEREKİR (aksi halde DDM SADECE bir "alt sınır" olarak kalır, cash TAMAMEN İSRAF EDİLMİŞ GİBİ VARSAYILMIŞ olur). [→ KONTROL LİSTESİ M] (s.252-253)
- **İLKE-122 (FCFE ve DDM ne zaman FARKLILAŞIR):** FCFE>temettü VE fazla nakit DÜŞÜK GETİRİLİ/NEGATİF NPV yatırımlara (KÖTÜ akiziyonlar) HARCANIYORSA FCFE değeri DAHA YÜKSEK çıkar; TEMETTÜ FCFE'Yİ AŞIYORSA firma yeni hisse/borç İHRAÇ ETMEK ZORUNDA kalır, bu 3 OLUMSUZ sonuçtan BİRİNE yol açar: hisse ihraç MALİYETİ, AŞIRI kaldıraç, veya sermaye KISITLAMASI nedeniyle İYİ PROJELERİN REDDEDİLMESİ. (s.253-254)
- **İLKE-123 (FCFE-DDM farkının anlamı):** İki modelin farkı, "KONTROL DEĞERİ"NİN bir bileşeni olarak yorumlanabilir — düşmanca bir devralmada alıcı, temettü POLİTİKASINI DEĞİŞTİRİP FCFE'yi YAKALAYABİLİR. Kurumsal kontrol PİYASASININ AÇIK olduğu (devralma OLASILIĞI yüksek) durumlarda FCFE değeri, KAPALI olduğu durumlarda DDM değeri DAHA UYGUN KIYASLAMA (benchmark) noktasıdır. (s.254-255)
- **İLKE-124 (Hisse başı vs toplam/aggregate değerleme):** Hisse başı yaklaşım BASİTTİR (veri daha erişilebilir) ama TOPLAM değerleme 2 nedenle TERCİH EDİLİR: (1) faaliyet varlıkları/nakit AYRIMI net kârdan BAŞLAYINCA DAHA KOLAY yapılır; (2) opsiyon/warrant/dönüştürülebilir tahvil VARKEN "kaç hisse" sorusu TARTIŞMALIDIR — EN SAĞLAM yöntem opsiyonları AYRI bir opsiyon fiyatlama modeliyle DEĞERLEYİP toplam özkaynak değerinden ÇIKARMAK, kalan tutarı GERÇEK (seyreltilmemiş) hisse sayısına BÖLMEKTİR. (s.258-259)

**Chapter 6 — Firm Valuation Models:**

- **İLKE-125 (Cost of Capital yaklaşımının temel prensibi):** FCFF, WACC ile İSKONTO EDİLİR — borcun VERGİ FAYDASI (vergi SONRASI maliyette) VE borcun getirdiği EK RİSK (daha yüksek beta/maliyette) HER İKİSİ DE cost of capital İÇİNE ZATEN GÖMÜLÜDÜR. Borç verenler ile özkaynak sahipleri, firmaya sermaye SAĞLAYAN "ORTAKLAR" olarak görülür — fark SADECE nakit akışı ÖNCELİĞİNDEDİR (borç veren SABİT/öncelikli, özkaynak sahibi ARTIK/sonraki talep sahibidir). (s.261-262)
- **İLKE-126 (İstikrarlı büyüme FCFF modelinde tutarlılık):** Reinvestment oranı İSTİKRARLI büyüme oranı VE sürdürülebilir ROC'tan TÜRETİLMELİDİR (İLKE-95'in FIRMA versiyonu); işletme sermayesi DEĞİŞİMİ SONSUZA DEK NEGATİF olamaz (İLKE-73'ün firma seviyesindeki TEKRARI — kısa vadede kabul edilebilir ama TERMİNAL değerde SIFIRLANMALI/pozitife dönmeli); beta 0,8-1,2 bandına yakınsamalı. (s.262-263)
- **İLKE-127 (Faaliyet Varlığı Değerinden Özkaynak Değerine Geçiş — 6+6 kalem):** EKLENECEK: nakit ve menkul kıymetler, azınlık pay YATIRIMLARININ değeri (başka şirketlerdeki), ATIL/kullanılmayan varlıklar. ÇIKARILACAK: faizli borç, operating lease taahhütlerinin PV'si, KONSOLİDE edilen iştiraklerdeki AZINLIK PAYLARI (parent şirket %50+ hissedarsa konsolide edilir ama azınlık payı ÇIKARILMALI), fonsuz emeklilik/sağlık yükümlülükleri, beklenen dava ÖDEMELERİ. [→ KONTROL LİSTESİ N] (s.265-267)
- **İLKE-128 ("Ne kadar detay?" — Ch.1'in parsimoni ilkesinin firma değerlemesindeki somut uygulaması):** Faaliyet MARJLARI istikrarlıysa doğrudan FAALİYET KÂRINDAN başlamak YETERLİDİR; marjlar DEĞİŞKENSE (özellikle marjı hedef değere YAKINSAYAN genç firmalarda) GELİRDEN başlayıp YIL YIL marj projeksiyonu yapmak GEREKİR — daha fazla detay SADECE, o detayı TAHMİN ETMEK için YETERLİ BİLGİ varsa DEĞER KATAR. (s.275)
- **İLKE-129 (Cost of Capital yaklaşımının 3 sınırlaması):** (1) FCFE, insanların DOĞAL olarak düşündüğü (borç ödemesi SONRASI) nakit akışına DAHA SEZGİSELDİR; (2) FCFF'nin BORÇ-ÖNCESİ odağı SAĞ KALIM sorunlarını GİZLEYEBİLİR (FCFF pozitifken FCFE, büyük borç yükü nedeniyle AŞIRI NEGATİF olabilir — firma yeni fon BULAMAZSA batabilir, FCFF bunu ASLA GÖSTERMEZ); (3) SABİT borç ORANI varsayımı GERÇEKÇİ OLMAYABİLİR — büyüyen bir firma hedef orana ULAŞMAK için MASİF miktarda borç ihraç etmek ZORUNDA kalabilir, defter borç oranı FIRLAYIP KOVENANT tetikleyebilir. [→ BAYRAK-16] (s.278)
- **İLKE-130 (Firma vs özkaynak değerlemesi — TEORİDE eşit, PRATİKTE 3 KOŞUL gerektirir):** DEĞERLER teoride EŞİT olmalıdır AMA pratikte YAKINSAMA İÇİN 3 varsayım GEREKİR: (1) cost of capital hesabında kullanılan borç/özkaynak DEĞERLERİ, VARILAN sonuçtaki değerlerle EŞİT olmalı (DAİRESELLİK uyarısı — piyasa fiyatı yanlışsa iki yöntem UYUŞMAZ); (2) olağanüstü/nakit-dışı bir kalem OLMAMALI; (3) faiz gideri = pretax cost of debt × PİYASA DEĞERİ borç OLMALI (eski, DÜŞÜK faizli borç varsa İKİ yöntem SAPAR). (s.279-280)
- **İLKE-131 (APV — Adjusted Present Value — yaklaşımının 3 adımı):** (1) BORÇSUZ (unlevered) firma değeri (unlevered cost of equity ile iskonto); (2) borcun yarattığı VERGİ TASARRUFUNUN bugünkü değeri (perpetuite varsayımıyla `t×D`); (3) beklenen İFLAS MALİYETİNİN bugünkü değeri (temerrüt olasılığı × iflas maliyeti). [→ KONTROL LİSTESİ O] (s.280-282)
- **İLKE-132 (İflas olasılığı tahmininin 2 yolu):** (1) her borç seviyesinde SENTETİK kredi notu tahmin edip AMPİRİK temerrüt oranı tablolarını (Altman&Kishore gibi) KULLANMAK; (2) firmanın GÖZLEMLENEBİLİR karakteristiklerine dayalı probit/istatistiksel bir MODEL kullanmak. (s.282)
- **İLKE-133 (İflas maliyeti — YÜKSEK belirsizlik taşıyan bir girdi):** DOĞRUDAN maliyetler (hukuki/idari) GENELDE KÜÇÜK (Warner 1977, demiryolu iflasları çalışması: ~%5, firma değerine ORANLA); DOLAYLI maliyetler (müşteri/tedarikçi güveni kaybı, operasyonel BOZULMA) firma değerinin %25-30'una KADAR çıkabileceği SPEKÜLE edilir (Shapiro&Titman — DOĞRUDAN kanıt SUNMAZLAR); Altman (1984) 1980-82 arası batan 7 firmada ORTALAMA %15 tahmin etmiştir. Bu belirsizlik, APV yaklaşımının EN BÜYÜK PRATİK zaafıdır. (s.282-283)
- **İLKE-134 (Cost of Capital vs APV — farklılık nedenleri):** (1) İFLAS MALİYETİNİN ele alınışı FARKLIDIR — APV, DOLAYLI iflas maliyetlerini AYRI/ESNEK bir şekilde MODELLEYEBİLİR, Cost of Capital yaklaşımı BUNLARI SADECE pretax cost of debt/levered beta İÇİNE DOLAYLI/EKSİK biçimde GÖMER; (2) APV vergi faydasını SADECE MEVCUT $-borç ÜZERİNDEN hesaplar, Cost of Capital yaklaşımı İSE (sabit borç ORANI varsayımı nedeniyle) GELECEKTEKİ borç İHRAÇLARININ vergi faydasını da BUGÜNKÜ değere DAHİL EDER. (s.284-285)
- **İLKE-135 (APV'nin YAYGIN metodolojik hatası):** İflas maliyeti TAHMİN EDİLEMEDİĞİNDE (yaygın durum), analistler bunu genelde TAMAMEN İHMAL EDER — bu, SİSTEMATİK olarak "OPTİMAL borç oranı %100'DÜR" gibi GERÇEKÇİ OLMAYAN bir sonuca YOL AÇAR (sadece vergi FAYDASI sayılıp İFLAS MALİYETİ SAYILMAZSA borç HER ZAMAN "ucuz" görünür). [→ BAYRAK-17] (s.301-302)
- **İLKE-136 (Artık Getiri/EVA modelleri — Ch.4'ün mantıksal DEVAMI):** Ch.4'te kurulan "büyüme, SADECE fazla getiriyle BİRLİKTE değer yaratır" ilkesinin DOĞRUDAN UYGULAMASIDIR — EVA, Yatırılan Sermaye × (ROC - Cost of Capital) olarak TANIMLANIR, firma DEĞERİNİ mevcut+gelecek "fazla getiri"nin toplamı olarak İFADE EDER. (s.285-286)
- **İLKE-137 (EVA hesabında yatırılan sermaye tahmini):** Piyasa değeri, GELECEK büyümeyi de İÇERDİĞİNDEN, "SADECE mevcut varlıklara yatırılan sermaye" için DEFTER DEĞERİ bir PROXY olarak KULLANILIR — ANCAK DCF'teki AYNI 3 düzeltme (operating lease KAPİTALİZASYONU, R&D KAPİTALİZASYONU, tek seferlik/kozmetik kalemlerin ARINDIRILMASI) EVA hesabı için de MUTLAKA GEREKLİDİR — aksi halde defter değeri "DÜZELTİLEMEYECEK KADAR BOZUK" olabilir (bu durumda sermaye SIFIRDAN, varlık BAZLI tahmin edilmelidir). (s.286-287)
- **İLKE-138 (EVA hesabında cost of capital — MUTLAKA piyasa değeri ağırlıklı):** Sermaye İÇİN defter değeri, cost of capital İÇİN piyasa değeri kullanmak ÇELİŞKİLİ DEĞİLDİR — firma, PİYASA DEĞERİ cost of capital'ını AŞMAK ZORUNDADIR (fonlar BAŞKA YERDE piyasa oranıyla değerlendirilebilirdi). DEFTER DEĞERİ cost of capital kullanmak, cost of capital'ı SİSTEMATİK OLARAK DÜŞÜK gösterir (ÖZELLİKLE yüksek kaldıraçlı firmalarda DAHA FAZLA) — bu da EVA'yı YAPAY OLARAK ŞİŞİRİR. [→ BAYRAK-18] (s.287)
- **İLKE-139 (Firma Değeri = Sermaye + EVA'ların BD'si — DCF ile MATEMATİKSEL eşdeğerlik):** Firma değeri, Yatırılan Sermaye + Mevcut Varlıkların EVA'sının bugünkü değeri + Gelecek Yatırımların EVA'sının bugünkü değeri OLARAK yazılabilir — DOĞRU koşullar sağlandığında standart DCF (FCFF/WACC) ile TAM AYNI sonucu VERİR (kitapta Titan Cement örneğiyle SAYISAL olarak DOĞRULANMIŞTIR). (s.287-288, 290-292)
- **İLKE-140 (EVA-DCF eşdeğerliğinin 4 KOŞULU):** (1) DCF'te kullanılan düzeltilmiş faaliyet kârı İLE EVA'da kullanılan AYNI olmalı; (2) büyüme oranı FUNDAMENTALS'tan (reinvestment×ROC) türetilmiş olmalı, EGZOJEN bir sayı OLMAMALI; (3) yatırılan sermaye HER DÖNEM reinvestment EKLENEREK güncellenmeli; (4) terminal değer varsayımları (ÖZELLİKLE sermaye getirisi=sermaye maliyeti ÖZEL durumunda) TUTARLI olmalı. Bu 4 koşuldan HERHANGİ BİRİ İHLAL edilirse İKİ yöntem FARKLI sonuç VERİR. (s.292-293)
- **İLKE-141 (Modigliani-Miller 1958 teoremi ve UZANTILARI):** VERGİSİZ/temerrüzSÜZ/agency-maliyetSİZ bir dünyada firma DEĞERİ finansman KARIŞIMINDAN BAĞIMSIZDIR — borcun UCUZLUĞU, özkaynağın ARTAN riskiyle (ve YÜKSELEN cost of equity'siyle) TAM DENGELENİR, cost of capital SABİT KALIR. MM'nin SONRAKİ makalesi VERGİYİ eklediğinde optimal borç oranı %100'e (AŞIRI uç) KAYAR; İFLAS RİSKİ de eklenince bir TRADE-OFF (denge noktası) OLUŞUR. (s.293)
- **İLKE-142 (Sermaye yapısının değere etkisi — KARIŞIK ampirik kanıt):** BORÇ oranı ile değerleme ÇARPANLARI arasında KESİTSEL (farklı firmalar arası) KORELASYON ZAYIFTIR (bu MM görüşünü DESTEKLER) AMA kaldıraç ARTIRAN EYLEMLER (borçla finanse edilen hisse GERİ ALIMI) genelde firma DEĞERİNİ ARTIRIR (bu, kaldıracın ETKİSİ OLDUĞUNU DESTEKLER) — sonuç KESİN DEĞİLDİR. (s.293-294)
- **İLKE-143 (Optimal sermaye yapısı — 2 eşdeğer yöntem):** (1) COST OF CAPITAL yaklaşımı — WACC'ı MİNİMİZE eden borç ORANINI bul (bu, firma değerini MAKSİMİZE eder, ÇÜNKÜ nakit akışları SABİT tutulup SADECE iskonto oranı DEĞİŞTİRİLİR); (2) APV yaklaşımı — levered firma değerini DOĞRUDAN MAKSİMİZE eden $-BORÇ tutarını bul. AYNI varsayımlarla İKİSİ de AYNI (Titan Cement örneğinde HER İKİSİ de ~%40 optimal borç oranı) sonucu VERİR. [→ KONTROL LİSTESİ P] (s.294-301)
- **İLKE-144 (Sermaye yapısı analizinde MEVCUT borcun da YENİDEN FİYATLANMASI GEREKİR):** Her borç seviyesinde MEVCUT (eski) borcun da YENİ orana karşılık gelen FAİZ oranıyla REFİNANSE edildiği VARSAYILMALIDIR — bu (a) koruyucu "put" opsiyonu olan eski borç sahiplerinin GERÇEK davranışını YANSITIR, (b) "SERVET TRANSFERİ" (wealth expropriation — borç ARTINCA eski, düşük-faizli borç sahiplerinin KAYBI) etkisini ENGELLER. Ayrıca, borç seviyesi YÜKSELDİKÇE FAİZ GİDERİ FVÖK'ü AŞARSA vergi ORANI (kalan vergi kalkanı payına göre) AŞAĞI DÜZELTİLMELİDİR — tam vergi avantajı ARTIK GEÇERLİ DEĞİLDİR. (s.296-298)

## Formüller (devam)

- **FORMÜL-52 — Temettü İskonto Modeli (Genel, Sonsuz Ufuk)**
  - Formül: `P0 = Σ [DPSt / (1+ke)^t]` (t=1'den sonsuza)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — DPS eksikliği (kümülatif, kitaplar arası en sık tekrarlanan açık) nedeniyle UYGULANAMAZ.

- **FORMÜL-53 — Gordon Büyüme Modeli**
  - Formül: `P0 = DPS1 / (ke - g)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (DPS) — ANCAK yapısal olarak `valuation.py`'nin Damodaran FCFE bloğundaki `equity_value = fcfe * (1+g) / (ke-g)` satırıyla BİREBİR AYNI matematiksel İSKELETİ (Gordon büyüme formülü) paylaşır, SADECE `DPS` yerine `FCFE` kullanılmıştır — bu KISIM 1'de not edilen FORMÜL-47'nin (istikrarlı dönem terminal değer) DAHA GENEL/kök halidir.

- **FORMÜL-54 — İstikrarlı Dönem Payout Oranı (Türetilmiş)**
  - Formül: `Payout_n = 1 - (g_n / ROE_n)`
  - QuaxisLabs karşılığı: `roe_annualized` VAR; `g_n` (istikrarlı büyüme) `valuation.py`'de zaten `min(hasılat büyümesi, risksiz faiz, ROE×0.9)` olarak TANIMLI — payout oranının KENDİSİ (temettü dağıtımı GÖSTERİMİ için) hesaplanmıyor ama `reinvestment_rate = g/ROE` satırı MATEMATİKSEL OLARAK `1-payout` ile AYNI ÖZDEŞLİKTİR (Kısım 1 FORMÜL-49 ile AYNI formül, BURADA DDM bağlamında YENİDEN karşımıza çıktı).

- **FORMÜL-55 — İki Aşamalı Temettü İskonto Modeli**
  - Formül: `P0 = Σ[DPSt/(1+ke,hg)^t] (t=1..n) + Pn/(1+ke,hg)^n`, `Pn = DPSn+1/(ke,st - gn)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (DPS).

- **FORMÜL-56 — H Modeli (Doğrusal Azalan Büyüme)**
  - Formül: `P0 = [DPS0×(1+gn)]/(ke-gn) + [DPS0×H×(ga-gn)]/(ke-gn)` (H = geçiş süresinin yarısı, 2H = toplam geçiş yılı)
  - QuaxisLabs karşılığı: **VERİ EKSİK** (DPS).

- **FORMÜL-57 — Üç Aşamalı Temettü İskonto Modeli (Genel Form)**
  - Formül: yüksek büyüme (EPSt×Πa iskonto edilir, ke,hg ile) + geçiş (değişen EPSt×Πt, kümülatif ke ile) + istikrarlı terminal değer (Pn2, ke,st ile)
  - QuaxisLabs karşılığı: **VERİ EKSİK** (DPS + çok-yıllı EPS serisi).

- **FORMÜL-58 — Modifiye Payout Oranı (Hisse Geri Alımı Dahil)**
  - Formül: `Modifiye Payout = (Temettü + Hisse Geri Alımı) / Net Kâr` (4-5 yıllık ORTALAMA önerilir)
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — hem temettü HEM geri alım verisi YOK.

- **FORMÜL-59 — FCFE (Sabit Borç Oranı Kısayolu, Kısım 2 FORMÜL-26'nın DDM bağlamındaki paraleli)**
  - Formül: `FCFE = Net Kâr - (1-δ)×(Capex-Amortisman) - (1-δ)×ΔNoncash İşletme Sermayesi` (δ=borçla finanse edilen oran)
  - QuaxisLabs karşılığı: Kısım 2'deki AYNI VERİ EKSİKLİĞİ (Capex).

- **FORMÜL-60 — Sabit (İstikrarlı) Büyüme FCFE Modeli**
  - Formül: `P0 = FCFE1 / (ke - gn)`
  - QuaxisLabs karşılığı: `valuation.py`'nin Damodaran bloğuyla YAPISAL OLARAK ÖZDEŞ (bkz. FORMÜL-53 notu) — ZATEN UYGULANIYOR (basitleştirilmiş `reinvestment_rate=g/ROE` girdisiyle).

- **FORMÜL-61 — İki Aşamalı FCFE Modeli**
  - Formül: `P0 = Σ[FCFEt/(1+ke,hg)^t] (t=1..n) + Pn/(1+ke,hg)^n`, `Pn = FCFE_n+1/(ke,st-gn)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (çok-dönemli Capex/WC projeksiyonu YOK) — mevcut Damodaran modeli SADECE tek-aşamalı (Kısım 1) versiyona sahip, ÇOK-AŞAMALI (yüksek büyüme+istikrarlı) GENİŞLETME şu an YOK.

- **FORMÜL-62 — E Modeli (Üç Aşamalı FCFE, Genel Form)**
  - Formül: yüksek büyüme + geçiş + istikrarlı terminal değer FCFE ile (FORMÜL-57'nin FCFE karşılığı)
  - QuaxisLabs karşılığı: **VERİ EKSİK** (aynı kök nedenler — Capex/WC çok-dönemli projeksiyon).

- **FORMÜL-63 — İstikrarlı Büyüme FCFF Modeli (Firma Değeri)**
  - Formül: `Firma Değeri = FCFF1 / (WACC - gn)`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — WACC hiç hesaplanmıyor (Kısım 1 FORMÜL-21), FCFF de (Kısım 2 FORMÜL-27) eksik veriye bağlı; QuaxisLabs'ın Damodaran modeli SADECE özkaynak (FCFE) tarafını uyguluyor, FİRMA (FCFF/WACC) tarafı HİÇ YOK.

- **FORMÜL-64 — Genel FCFF Modeli (n Dönem + Terminal Değer)**
  - Formül: `Firma Değeri = Σ[FCFFt/(1+WACC)^t] (t=1..n) + [FCFFn+1/(WACC-gn)]/(1+WACC)^n`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** (aynı kök nedenler — FORMÜL-63).

- **FORMÜL-65 — Faaliyet Varlığı Değerinden Özkaynak Değerine Geçiş (Tablo 6.1)**
  - Formül: `Özkaynak Değeri = Faaliyet Varlığı Değeri + Nakit/Menkul Kıymet + Azınlık Yatırımları + Atıl Varlıklar - Faizli Borç - Kira Taahhütleri PV'si - Azınlık Payları(konsolide) - Fonsuz Emeklilik/Sağlık - Beklenen Dava Ödemeleri`
  - QuaxisLabs karşılığı: **KISMEN VAR** — `cash`, `financial_debt` HAZIR; azınlık payı yatırımları, atıl varlıklar, kira taahhüt PV'si, fonsuz emeklilik/dava yükümlülükleri hiçbiri STANDALONE alan olarak YOK (Buffett turunda da kısmen tespit edilen eksiklikler) — Faaliyet Varlığı Değerinin KENDİSİ zaten hesaplanamadığından (FORMÜL-63/64 eksikliği) bu geçiş formülü ŞU AN PRATİK ÖNEM TAŞIMIYOR.

- **FORMÜL-66 — APV: Borçsuz (Unlevered) Firma Değeri**
  - Formül: `Değer(Unlevered) = FCFF0×(1+g) / (ρu - g)` (ρu = unlevered cost of equity)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — `ρu` için unlevered beta gerekir (Kısım 1 FORMÜL-02/10 eksikliği), FCFF de (Kısım 2 FORMÜL-27) eksik.

- **FORMÜL-67 — APV: Borcun Vergi Tasarrufunun Bugünkü Değeri (Perpetuite)**
  - Formül: `Vergi Tasarrufu BD = t × D` (t = marjinal vergi oranı, D = mevcut $ borç)
  - QuaxisLabs karşılığı: `financial_debt` HAZIR; marjinal vergi oranı (`t`) XI_29'da YOK (Kısım 1 FORMÜL-18'in AYNI eksikliği) — bu, formüldeki İKİ girdiden BİRİNİN eksik olduğu, GÖRECELİ olarak DÜŞÜK maliyetli bir formül (borç zaten VAR, sadece marjinal vergi oranı SABİT bir ülke/sektör varsayımıyla DOLDURULABİLİR — kesin ideal değil ama BASİT bir yaklaşık uygulanabilir).

- **FORMÜL-68 — APV: Beklenen İflas Maliyetinin Bugünkü Değeri**
  - Formül: `İflas Maliyeti BD = πa × BC` (πa = ek borçla temerrüt olasılığı, BC = iflas maliyetinin BD'si, genelde firma değerinin bir yüzdesi olarak varsayılır)
  - QuaxisLabs karşılığı: **VERİ EKSİK/METODOLOJİK ZORLUK** — `πa` için sentetik kredi notu GEREKİR (interest coverage ratio, Kısım 1 FORMÜL-17/19 eksikliği); `BC` İSE hiçbir veriden TÜRETİLEMEZ, ELLE bir varsayım (kitap örneği: firma değerinin %30'u) GEREKTİRİR — bu KISIM 1'deki `merton.py` (Distance-to-Default/EDF) modeliyle KAVRAMSAL OLARAK YAKINDIR ama Merton modeli İFLAS MALİYETİNİ değil, SADECE temerrüt olasılığını tahmin eder; BC HİÇBİR modülde YOK.

- **FORMÜL-69 — Levered Firma Değeri (APV Toplamı)**
  - Formül: `Levered Değer = Unlevered Değer + Vergi Faydası BD'si - Beklenen İflas Maliyeti BD'si`
  - QuaxisLabs karşılığı: Alt bileşenlerin (FORMÜL-66/67/68) TÜMÜ eksik veriye BAĞLI — **UYGULANAMAZ**.

- **FORMÜL-70 — EVA (Economic Value Added)**
  - Formül: `EVA = (ROC - WACC) × Yatırılan Sermaye`
  - QuaxisLabs karşılığı: **KISMEN VAR/PARALEL** — `fundamental_screens.py`'nin Greenblatt `return_on_capital_pct` (EBIT/(NWC+Net Sabit Varlık)) ROC bileşenine YAKIN bir başlangıç noktası sunuyor (Kısım 2 FORMÜL-44 notuyla AYNI); WACC hiç YOK (Kısım 1 FORMÜL-21) — formül TAMAMEN UYGULANAMAZ ama YARISI (ROC) MEVCUT.

- **FORMÜL-71 — Firma Değeri (EVA/Artık Getiri Yaklaşımı)**
  - Formül: `Firma Değeri = Yatırılan Sermaye + Σ PV(EVAt, mevcut varlıklar) + Σ PV(EVA, gelecek yatırımlar)`
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** (WACC + çok-dönemli reinvestment projeksiyonu eksikliği).

- **FORMÜL-72 — Optimal Sermaye Yapısı (Cost of Capital Yöntemi)**
  - Formül: `Optimal D/(D+E) = argmin[WACC(D/(D+E))]` (her borç seviyesinde levered beta + sentetik kredi notu bazlı cost of debt yeniden hesaplanarak)
  - QuaxisLabs karşılığı: **TAMAMEN VERİ EKSİK** — hem levered/unlevered beta (Kısım 1) hem sentetik kredi notu (interest_expense eksikliği) hem WACC'ın KENDİSİ eksik; bu, kitabın EN VERİ-YOĞUN metodolojilerinden biridir ve QuaxisLabs'ın MEVCUT veri modeliyle EN UZAK olduğu formül grubudur.

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| JPMorgan Chase (Kasım 2005) — Gordon modeli girdileri | Payout **%65,38**, ROE **%11,16**, beta **0,8**, cost of equity **%7,7** | Tahmini değer piyasa fiyatına ($38) ÇOK YAKIN çıkan somut illüstrasyon | Ch.5, s.221-222 |
| Goldman Sachs (Kasım 2005) — 2 aşamalı DDM ima edilen büyüme | Baz senaryo **%16,82** vs piyasa fiyatını AÇIKLAYAN **%2,6** | "İma edilen büyüme oranı" kavramına (İLKE-103) somut örnek | Ch.5, s.225-226 |
| "Çok yüksek büyüme" tanımı (pratik kural) | **>%25** (istikrarlı büyüme %6-8 iken) | 3 aşamalı DDM/E Modeli uygunluk eşiği | Ch.5, dipnot 4 |
| ABD büyük/olgun firmalarda ortalama payout oranı | **~%60** | Gordon modeli/DDM'in "istikrarlı firma" varsayımına referans değer | Ch.5, dipnot 1 |
| ExxonMobil FCFE modeli — normalize edilmiş girdiler | Noncash ROE **%21,88**, reinvestment **%16,98**, ima edilen büyüme **%3,71** | Döngüsel emtia şirketinde kâr NORMALLEŞTİRME somut örneği | Ch.5, s.242-243 |
| Toyota 2 aşamalı FCFE — girdiler | Noncash ROE **%16,55**, equity reinvestment **%64,4%**, büyüme **%10,66** | Yüksek reinvestment oranına somut örnek | Ch.5, s.244-245 |
| Titan Cement — yüksek/istikrarlı dönem ROC karşılaştırması | ROC **%19,25** (yüksek büyüme) → **%6,57** (istikrarlı, =cost of capital) | Fazla getirinin istikrarlı dönemde EROZYONUNA somut örnek | Ch.6, s.267-268, 290-292 |
| Titan Cement — optimal borç oranı (HEM Cost of Capital HEM APV yöntemiyle) | **~%40** | İki BAĞIMSIZ yöntemin AYNI sonuca ULAŞTIĞINI DOĞRULAYAN somut örnek | Ch.6, s.298-301 |
| Doğrudan iflas maliyeti (Warner 1977, demiryolu iflasları) | **~%5** (firma değerine oranla) | APV'nin BC girdisi için tarihsel referans NOKTASI | Ch.6, s.283 |
| Dolaylı iflas maliyeti (Shapiro&Titman SPEKÜLASYONU) | **%25-30** (firma değerine oranla) | DOĞRUDAN kanıt YOK, sadece SPEKÜLASYON olarak belirtilmiş | Ch.6, s.283 |
| İflas maliyeti (Altman 1984, 7 firma, 1980-82) | **~%15** (ortalama) | APV illüstrasyonlarında (Titan Cement) KULLANILAN somut referans | Ch.6, s.283, 300 |
| SAP — sentetik kredi notu / default spread | **AAA** / **%0,35** | Düşük kaldıraçlı büyük teknoloji firmasına somut örnek | Ch.6, s.273 |

**Tablo 6.2 — Altman & Kishore (2000): Kredi Notuna Göre 10 Yıllık Kümülatif Temerrüt Oranı:**

| Kredi Notu | Temerrüt Oranı |
|---|---|
| AAA | %0,01 |
| AA | %0,28 |
| A+ | %0,40 |
| A | %0,53 |
| A− | %1,41 |
| BBB | %2,30 |
| BB | %12,20 |
| B+ | %19,28 |
| B | %26,36 |
| B− | %32,50 |
| CCC | %46,61 |
| CC | %65,00 |
| C | %80,00 |
| D | %100,00 |

(APV yaklaşımının `πa` — temerrüt olasılığı — girdisi için, Kısım 1'deki Tablo 2.4'ün — interest coverage → sentetik not — DOĞAL DEVAMI/uygulaması.)

## Kontrol listeleri (devam)

**Kontrol Listesi L — DDM'in 3 Uygun Kullanım Senaryosu (Ch.5, s.233-234):**
1. FCFE'yi AŞAN temettü ödeyen firmalarda TABAN/muhafazakâr değer sağlar.
2. FCFE'yi ORTALAMA OLARAK dağıtan istikrarlı/olgun firmalarda (eski düzenlenmiş utility'ler örneği) GERÇEKÇİ tahmin verir.
3. Nakit akışı tahmininin ZOR/ANLAMSIZ olduğu sektörlerde (banka/yatırım bankası/sigorta) TEK UYGULANABİLİR yöntemdir.

**Kontrol Listesi M — FCFE/DDM Yakınsama ve Ayrışma Koşulları (Ch.5, s.252-254):**
- EŞİTLENİR EĞER: (a) temettü=FCFE İSE, VEYA (b) FCFE>temettü AMA fazla nakit ADİL FİYATLI (NPV=0) varlıklara yatırılıyorsa (NOT: bu durumda DDM'de nakit BİRİKİMİNİN AYRICA İZLENİP değere EKLENMESİ GEREKİR).
- FARKLILAŞIR EĞER: (a) fazla nakit DÜŞÜK GETİRİLİ/kötü akiziyonlara harcanıyorsa (FCFE > DDM), VEYA (b) temettü FCFE'yi AŞIYORSA (ihraç maliyeti/aşırı kaldıraç/sermaye kısıtlaması riskleri doğar).

**Kontrol Listesi N — Faaliyet Varlığı Değerinden Özkaynak Değerine Geçiş (Tablo 6.1, Ch.6, s.265-267):**
- EKLE: Nakit ve menkul kıymetler + Azınlık pay yatırımlarının değeri + Atıl/kullanılmayan varlıklar.
- ÇIKAR: Faizli borç + Operating lease taahhütlerinin PV'si + Konsolide edilen iştiraklerdeki azınlık payları + Fonsuz emeklilik/sağlık yükümlülükleri + Beklenen dava ödemeleri.

**Kontrol Listesi O — APV Yaklaşımının 3 Adımı (Ch.6, s.280-282):**
1. Borçsuz (unlevered) firma değerini HESAPLA (unlevered cost of equity ile iskonto).
2. Borcun VERGİ TASARRUFUNUN bugünkü değerini EKLE (`t×D`, perpetuite varsayımıyla).
3. Beklenen İFLAS MALİYETİNİN bugünkü değerini ÇIKAR (`πa×BC`).

**Kontrol Listesi P — Optimal Sermaye Yapısı Tahmini, Cost of Capital Yöntemi Adımları (Ch.6, s.294-296):**
1. Her borç ORANI seviyesinde levered betayı (Hamada denklemiyle) yeniden HESAPLA → cost of equity.
2. Her borç ORANI seviyesinde $-borç/faiz giderini TAHMİN ET, sentetik kredi notunu (interest coverage ratio ile) TÜRET → pretax cost of debt.
3. Faiz gideri FVÖK'ü AŞARSA vergi oranını (kalan vergi kalkanı payına göre) DÜZELT → after-tax cost of debt.
4. Her seviyede WACC'ı HESAPLA — WACC'IN EN DÜŞÜK olduğu borç oranı OPTİMALDİR.

## Kırmızı bayraklar (devam)

- **BAYRAK-14 — DDM'de Büyük/Artan Nakit Biriktiren Firmaların Sistematik Olarak Düşük Değerlenmesi:** DDM, temettü DIŞINDAKİ tüm nakit akışlarını (ve firma içinde biriken nakdi) TAMAMEN GÖZ ARDI EDER — modifiye payout oranı ((temettü+geri alım)/net kâr) SÜREKLİ ÇOK DÜŞÜK (örn. <%40) VE nakit bakiyesi HER YIL BÜYÜYORSA, DDM sonucu sadece bir "TABAN/ALT SINIR" değer olarak OKUNMALIDIR, GERÇEK değer OLARAK DEĞİL. Nasıl tespit edilir: modifiye payout oranı TRENDİNİ VE nakit bakiyesi BÜYÜME oranını izle. Gereken veri: temettü+geri alım (VERİ EKSİK), `cash` (mevcut, TREND takibi için YETERLİ). (Ch.5, s.232-233)
- **BAYRAK-15 — FCFE Modelinde Çift Sayım Hatası:** FCFE'yi iskonto EDİP AYRICA firma içindeki nakit BİRİKİMİNİ de değere EKLEMEK — FCFE modeli ZATEN TÜM nakdin dağıtıldığını (BİRİKMEDİĞİNİ) varsayar, bu yüzden AYRICA "nakit birikimi" eklemek ÇİFTE sayımdır. Nasıl tespit edilir: bir DCF/FCFE modelinde HEM "FCFE'nin bugünkü değeri" HEM "gelecekteki nakit bakiyesinin bugünkü değeri" AYRI AYRI toplama EKLENİYOR MU kontrol et. Gereken veri: METODOLOJİK bir kontrol, veri gerektirmez — modelin KENDİSİ incelenmelidir. (Ch.5, s.251)
- **BAYRAK-16 — Sabit Borç Oranı Varsayımının Büyüyen Firmayı Aşırı Borçlanmaya Zorlaması:** Cost of Capital yaklaşımında SABİT bir hedef borç ORANI (örn. %30) varsayılırsa, HIZLA büyüyen bir firma bu ORANI KORUMAK için GİDEREK ARTAN miktarda YENİ borç İHRAÇ ETMEK zorunda kalır — bu, DEFTER borç oranını KOVENANT tetikleyecek/İFLAS riskini ARTIRACAK seviyelere FIRLATABİLİR, ki modeldeki SABİT oran varsayımı bu RİSKİ GİZLER. Nasıl tespit edilir: modelin ima ettiği YILLIK $-borç ihracını, firmanın MEVCUT büyüklüğüyle KIYASLA — orantısız büyükse ŞÜPHELEN. Gereken veri: çok-yıllı büyüme + borç oranı VARSAYIM SETİ (METODOLOJİK kontrol). (Ch.6, s.278)
- **BAYRAK-17 — APV'de İflas Maliyetinin İhmal Edilmesi:** Analistler İFLAS MALİYETİNİ (BC) tahmin EDEMEDİKLERİNDE genelde bunu TAMAMEN İHMAL EDİP SADECE vergi FAYDASINI hesaba KATARLAR — bu SİSTEMATİK OLARAK "OPTİMAL borç oranı %100'DÜR" gibi GERÇEKÇİ OLMAYAN bir sonuca YOL AÇAR. Nasıl tespit edilir: bir APV analizinde "beklenen iflas maliyeti" AYRI, AÇIK bir SATIR olarak VAR MI kontrol et — YOKSA veya SIFIR olarak bırakılmışsa şüphelen. Gereken veri: METODOLOJİK kontrol. (Ch.6, s.301-302)
- **BAYRAK-18 — EVA Hesabında Defter Değeri Cost of Capital Kullanımı:** Yatırılan sermaye İÇİN defter değeri KABUL EDİLEBİLİR bir proxy iken, COST OF CAPITAL için de DEFTER değeri (piyasa değeri YERİNE) kullanmak cost of capital'ı SİSTEMATİK OLARAK DÜŞÜK gösterir (ÖZELLİKLE yüksek kaldıraçlı firmalarda DAHA BÜYÜK sapmayla) — bu da hesaplanan EVA'yı YAPAY OLARAK ŞİŞİRİR ("şirket aslında olduğundan DAHA DEĞER YARATIYOR" YANILSAMASI). Nasıl tespit edilir: EVA/artık getiri raporlarında kullanılan "cost of capital" ağırlıklarının PİYASA DEĞERİ mi DEFTER değeri mi OLDUĞUNU kontrol et. Gereken veri: `market_cap` (piyasa değeri, MEVCUT) vs `equity` (defter değeri, MEVCUT) — bu iki alan ZATEN QuaxisLabs'ta VAR, karşılaştırma KOLAYLIKLA yapılabilir. (Ch.6, s.287)

## Uygulama notları (devam)

**Nicel (skorlanabilir):**
- Bu Kısımda TESPİT EDİLEN tek somut DÜŞÜK-MALİYETLİ potansiyel eklenti: **BAYRAK-18 tespiti için `market_cap` vs `equity` (defter değeri) ORANI** — her ikisi de ZATEN QuaxisLabs'ta MEVCUT (`compute_valuation().market_cap`, `balance_sheet.equity`), TEK bir oran hesaplaması EVA-tarzı bir "defter/piyasa kaldıraç sapması" UYARISI üretebilir (ama EVA'nın KENDİSİ WACC eksikliği nedeniyle UYGULANAMIYOR — bu, YAN ürün bir sinyal olurdu, ANA formül DEĞİL).
- Bu Kısımdaki formüllerin BÜYÜK ÇOĞUNLUĞU (FORMÜL-52-72, TOPLAM 21 formül) DPS, Capex, WACC, unlevered beta, marjinal vergi oranı gibi Kısım 1-2'de ZATEN "VERİ EKSİK" olarak İŞARETLENMİŞ kalemlere BAĞLIDIR — bu Kısım YENİ bir veri açığı KEŞFETMEDİ, MEVCUT açıkların (özellikle WACC/marjinal vergi/DPS) DAHA FAZLA formülü BLOKE ETTİĞİNİ DOĞRULADI.

**Nitel (LLM yorumuna uygun):**
- "İma edilen büyüme oranı" (implied growth rate, İLKE-103) hesabı — piyasa fiyatına ULAŞMAK için gereken büyümeyi TERSİNE ÇÖZMEK, MEVCUT `pe_ratio`/büyüme verisiyle YAKLAŞIK olarak KODLANABİLİR (Graham/PEG mantığına BENZER bir "ima edilen" gösterge) — bu, hâlâ İYİ bir NİCEL aday, sadece BURADA nitel olarak İŞARETLENDİ çünkü DDM/Gordon-özel formülasyonu DPS gerektiriyor; basitleştirilmiş bir F/K-bazlı versiyonu (mevcut Graham/PEG rozetleriyle AYNI mantıkta) DÜŞÜNÜLEBİLİR.
- APV/Cost of Capital yaklaşımlarının HANGİSİNİN "daha uygun" olduğu (İLKE-134) — LLM'e "bu firmanın borç yapısı NE KADAR İSTİKRARLI/değişken" diye SORULABİLECEK bir NİTEL değerlendirme.
- BAYRAK-16/17 (metodolojik hatalar) — bir DCF/APV MODELİNİN kendisinin (varsayım seti) LLM tarafından İNCELENMESİNİ gerektirir, sayısal tarama İLE tespit EDİLEMEZ.

**Veri eksikliği nedeniyle UYGULANAMAZ (bu Kısımda PEKİŞTİRİLEN, YENİ bulgu YOK):**
- Bu Kısım, Kısım 1-2'de TESPİT edilen TÜM ana veri açıklarının (DPS, Capex, WACC/unlevered beta, marjinal vergi oranı/interest_expense) Part One'ın (DCF Valuation) SON iki bölümünde de AYNI ŞİDDETTE devam ettiğini DOĞRULADI — özellikle **WACC'ın HİÇ hesaplanmaması**, bu Kısımdaki FORMÜL-63/64/66-72 (7 formül) gibi FİRMA-seviyesi (FCFF-bazlı) modellerin TAMAMININ ortak, TEK engelidir. Bu, Part One (Ch.2-6) BOYUNCA tekrarlanan bulguya dayanarak: **QuaxisLabs'ın Damodaran değerleme modeli SADECE özkaynak (FCFE, tek-aşamalı) tarafını kapsıyor; firma-seviyesi (FCFF/WACC/APV/EVA) DEĞERLEME AİLESİNİN TAMAMI şu an ürün kapsamı DIŞINDA** — bu, Part One sonunda netleşen EN ÖNEMLİ YAPISAL gözlemdir.

---

# KISIM 4 — Chapter 7-8: Relative Valuation: First Principles + Equity Multiples

**Kapsam:** Chapter 7: Relative Valuation: First Principles (PDF s.306-335), Chapter 8: Equity Multiples (PDF s.336-385). Bu Kısımla birlikte **Part Two: Relative Valuation**'ın İLK iki bölümü işlenmiş olur (Ch.9 Kısım 5'te devam edecek). ID numaralandırması Kısım 1-3'ün devamı (İLKE-145'ten, FORMÜL-73'ten, BAYRAK-19'dan, Kontrol Listesi Q'dan başlar; kesintisiz).

## İlkeler (devam)

**Chapter 7 — Relative Valuation: First Principles:**

- **İLKE-145:** Göreli değerlemenin 3 temel adımı: (1) piyasada fiyatlanan KARŞILAŞTIRILABİLİR varlıkları bul, (2) piyasa fiyatlarını ORTAK bir değişkene (kazanç/defter değeri/gelir) bölerek STANDARTLAŞTIR, (3) kalan farklar için DÜZELT. DCF'te "içsel değer" arayışı vardır; göreli değerlemede sadece "piyasa benzer varlıkları nasıl fiyatlıyor" sorusu vardır. (s.306-307)
- **İLKE-146 (DCF-göreli değerleme felsefi ayrımı):** DCF, piyasanın HATA yapabileceğini VE bu hataların SEKTÖR/PİYASA GENELİNDE bile olabileceğini varsayar; göreli değerleme, piyasanın BİREYSEL hisselerde hata yapsa da ORTALAMADA doğru fiyatladığını varsayar. Piyasa ortalamada doğruysa iki yöntem YAKINSAR; piyasa sistematik olarak bir sektörü/piyasayı yanlış fiyatlıyorsa AYRIŞIR. (s.307-308, 334)
- **İLKE-147 (Göreli değerlemenin yaygınlığı):** 2001'de 550 sell-side araştırma raporu üzerine yapılan çalışmada göreli değerlemeler DCF'i ~10:1 oranında GEÇTİ; DCF, M&A/kurumsal finansta daha yaygın görünse de TERMİNAL DEĞER genelde bir ÇARPANLA hesaplandığından, birçok "DCF" aslında GİZLİ bir göreli değerlemedir. (s.308)
- **İLKE-148 (Popülerlik nedenleri):** Göreli değerleme (1) daha AZ zaman/kaynak gerektirir, (2) SATIŞI daha kolaydır (kısa sunumlara uyar), (3) SAVUNMASI daha kolaydır (varsayımların sorumluluğu PİYASAYA yüklenir, DCF'in uzun açık varsayım listesi eleştiriye daha açıktır), (4) piyasanın GÜNCEL MODUNU yakalar (fon yöneticileri GÖRECELİ performansa göre değerlendirildiğinden, tüm sektör aşırı değerliyken bile sektör-içi "ucuz" hisse aramak RASYONELDİR onlar için). (s.309-310)
- **İLKE-149:** Göreli değerlemenin güçlü yanları AYNI ZAMANDA zayıf yanlarıdır: kolaylık → risk/büyüme/nakit akışı farklarının İHMAL EDİLMESİYLE sonuçlanabilir; piyasa modunu yakalama → sektör GENELİ aşırı/düşük değerliyken bu HATAYI DEVRALIR; şeffaflık eksikliği → varsayımlar İFADE EDİLMEDEN kaldığından MANİPÜLASYONA çok daha açıktır (emsal grup seçimiyle HEMEN HEMEN HER değer haklı çıkarılabilir). (s.310)
- **İLKE-150 (Standartlaştırma değişkenleri):** Değerler kazanca (P/E türevleri), defter/yenileme değerine (P/BV, Tobin's Q), gelire (P/S, FD/Satış) veya SEKTÖRE ÖZGÜ ölçülere (internet: site ziyareti başına; kablo: abone başına) göre standartlaştırılabilir. Sektöre özgü çarpanlar İKİ nedenle TEHLİKELİDİR: başka sektörlerle/piyasa geneliyle KIYASLANAMAZLAR (çapa yoktur, "yüksek/düşük/tipik" hissi oluşmaz) VE temel değişkenlerle (gelir/kâra dönüşüm) İLİŞKİLENDİRİLMELERİ ÇOK ZORDUR. (s.311-313)
- **İLKE-151 (Çarpan kullanmanın 4 temel adımı):** (1) TANIM testleri — tutarlılık + uniformite; (2) TANIMLAYICI testler — çapraz kesit dağılımı (piyasa genelinde, SADECE sektörde değil); (3) ANALİTİK testler — belirleyici değişkenler + bunların çarpanla İLİŞKİSİ; (4) UYGULAMA testleri — doğru karşılaştırılabilir firma seçimi + kalan farklar için düzeltme. [→ KONTROL LİSTESİ Q] (s.313-314)
- **İLKE-152 (Tutarlılık testi):** Bir çarpanın PAYI özkaynak değeriyse (fiyat/piyasa değeri özkaynak) PAYDASI da özkaynak ölçüsü (HBK/net kâr/defter özkaynağı) OLMALIDIR; pay firma değeriyse (FD) payda da firma ölçüsü (FVÖK/FAVÖK/yatırılan sermaye) OLMALIDIR. P/E ve FD/FAVÖK TUTARLIDIR; Fiyat/FAVÖK (pay özkaynak, payda firma-geneli) TUTARSIZDIR — "her firma için AYNI şekilde hesaplandığı için sorun yok" savunması YANLIŞTIR, borçlu firmalar bu çarpanda SAHTE OLARAK ucuz görünür. [→ BAYRAK-19] (s.314-315)
- **İLKE-153 (Uniformite testi):** Karşılaştırılan TÜM firmalarda AYNI çarpan varyantı (current/trailing/forward P/E) kullanılmalıdır — farklı mali yıl sonu tarihleri bile TUTARSIZLIK yaratabilir (biri Temmuz-Haziran, diğeri Ocak-Aralık kazancıyla bölünürse); farklı muhasebe standardı/agresiflik seviyesi de (aynı standart altında bile) karşılaştırmayı BOZAR — agresif muhasebe kullanan firmalar earnings çarpanlarında SAHTE OLARAK ucuz görünür. (s.315-316)
- **İLKE-154 (Ortalama vs medyan):** Çarpan dağılımları HER ZAMAN pozitif çarpıktır (alt sınır sıfır, üst sınır yok) — bu yüzden ORTALAMA HER ZAMAN medyandan yüksektir (Ocak 2005: medyan P/E 23, ortalama P/E 48) ve medyan TİPİK firmayı DAHA İYİ temsil eder. Normal dağılım varsayımından türeyen "ortalama±2 std sapma dışına nadiren düşülür" kuralı çarpanlarda GEÇERSİZDİR — binlerce firma bu aralığın DIŞINDA kalır. (s.317-319)
- **İLKE-155 (Aykırı değer/veri kaynağı farkı):** Çarpanlar yukarı yönde SINIRSIZDIR (500x, 2000x mümkündür), bu da ORTALAMALARI temsili OLMAKTAN çıkarır; veri sağlayıcıları aykırı değerleri FARKLI şekillerde ele alır (bazıları atar, bazıları bir tavana SINIRLAR) — Kasım 2005'te S&P 500 ortalama P/E'si kaynağa göre 16,5 (Yahoo) ile 24,2 (Morningstar) arasında DEĞİŞTİ. (s.319)
- **İLKE-156 (Negatif kazanç örneklem dışı bırakma yanlılığı):** Negatif HBK'lı firmalarda P/E HESAPLANAMADIĞINDAN örneklemden DÜŞER — bu, kalan (kârlı) firmaların ortalama P/E'sini YUKARI YANLAR. 3 çözüm: (1) yanlılığı BİLEREK ortalamayı aşağı düzelt, (2) AGREGATİF P/E kullan (ΣPiyasa Değeri/ΣNet Kâr, zarar edenler DAHİL), (3) HER firma için hesaplanabilen TERSİNİ (kazanç verimi, E/P) kullan. (s.319-321)
- **İLKE-157 (Zamanla değişen çarpanlar):** Çarpanlar zamanla DEĞİŞİR — kısmen TEMEL değişkenlerden (faiz oranı, ekonomik büyüme), kısmen PİYASA RİSK ALGISI değişiminden (resesyonlarda risk iştahı düşer, çarpanlar daralır). Sonuç: çapraz-ZAMAN çarpan kıyasları TEHLİKELİDİR; göreli değerlemelerin "raf ömrü" KISADIR (bir hisse bugün ucuz görünüp birkaç ay içinde bu değerlendirme DEĞİŞEBİLİR) — İçsel (DCF) değerlemeler DAHA İSTİKRARLIDIR. (s.321-322)
- **İLKE-158 (Analitik testler — belirleyiciler):** Her çarpan (kazanç/defter/gelir) TIPKI DCF gibi AYNI 3 değişkenin (nakit akışı üretme kapasitesi, büyüme, risk) FONKSİYONUDUR — bu, basit bir istikrarlı büyüme temettü iskonto modelinden HER çarpan TÜRETİLEREK gösterilebilir. [→ FORMÜL-80] (s.322-324)
- **İLKE-159 (Doğrusallık varsayımı riski):** Birçok değerleme analizi çarpan-temel değişken ilişkisinin DOĞRUSAL olduğunu VARSAYAR (PEG oranı bunun en somut örneğidir — P/E'nin büyümeyle DOĞRUSAL arttığını varsayar) — ama DCF türetimi (her değişkeni sabit tutup diğerini değiştirerek) gösterir ki değerlemede DOĞRUSAL ilişkiler NADİRDİR. (s.324-325)
- **İLKE-160 (Companion variable/eşlik değişkeni):** Her çarpanı en iyi açıklayan, DİĞERLERİNDEN baskın TEK bir değişken vardır (P/E için büyüme, P/BV için ROE, P/S için net marj) — bu değişken, benzer firmalar arasında FARKLARI en iyi açıklayan değişken olarak İSTATİSTİKSEL/SEZGİSEL olarak belirlenir; doğru çarpan kullanımı EN AZ bu değişkenin kontrol edilmesini gerektirir. (s.325-326)
- **İLKE-161 (Karşılaştırılabilir firma tanımı):** Karşılaştırılabilir firma, RİSK/BÜYÜME/NAKİT AKIŞI PROFİLİ benzer olan firmadır — SEKTÖR AİDİYETİ DEĞİL (bir telekom firması, risk/büyüme/nakit akışı özdeşse bir yazılım firmasıyla KIYASLANABİLİR). Sektör bazlı seçim, "aynı sektördeki firmaların risk/büyüme/nakit akışı BENZER olduğu" örtük varsayımını taşır — dar sektör tanımı AZ örnek verir, geniş tanım ÇEŞİTLİLİĞİ artırır (trade-off). (s.325-327)
- **İLKE-162 (Farkları kontrol etmenin 3 yolu):** (1) SÜBJEKTİF düzeltme — analistin yargısıyla farkı AÇIKLAMA (genelde önyargıyı DOĞRULAYAN tahmin haline gelir); (2) MODİFİYE çarpan (PEG gibi) — TEK companion değişken için basit bölme düzeltmesi (İKİ örtük varsayım taşır: diğer TÜM değişkenlerde EŞİTLİK VE ilişkinin DOĞRUSAL olması); (3) İSTATİSTİKSEL teknik (regresyon) — ÇOKLU değişkene ve doğrusal olmayan ilişkiye izin verir, ilişkinin GÜCÜNÜ (t-istatistik/R²) ölçer. [→ KONTROL LİSTESİ R] (s.327-329)
- **İLKE-163 (Sektör regresyonu):** Regresyon değişken SEÇİMİ TEORİ bazlı olmalıdır — R²'yi artıran HER değişken değil, SADECE DCF'ten türeyen TEMEL değişkenler (büyüme/risk/payout) kullanılmalıdır; amaç TÜM fiyatlama farkını açıklamak değil, SADECE temellerle açıklanabilen kısmı ayıklamaktır. Sektör TANIMI dar tutulursa örneklem küçülür (regresyon güvenilirliği düşer), geniş tutulursa farklılık artar ama regresyon BU FARKI kontrol edebilir. (s.329-331)
- **İLKE-164 (Piyasa geneli regresyonu):** Sektör tanımını GEVŞETİP TÜM piyasayı karşılaştırılabilir kabul etmenin 3 avantajı: (1) piyasa verisine dayalı, SAYISAL büyüme/risk etkisi ölçümü sağlar; (2) az sayıda firma barındıran dar sektörlerde bile ANLAMLI kıyas sağlar; (3) bir sektörün TAMAMININ aşırı/düşük değerli olup olmadığını tespit edebilir (sektör-içi kıyas bunu YAPAMAZ). (s.331-332)
- **İLKE-165 (İstatistiksel tekniklerin sınırları):** (1) çarpanlar NORMAL DAĞILMADIĞINDAN standart regresyon varsayımları ihlal EDİLİR (küçük örneklemde aykırı değer etkisi BÜYÜR); (2) bağımsız değişkenler (büyüme/risk/payout) BİRBİRİYLE KORELELİDİR (yüksek büyüme→yüksek risk→düşük payout birlikte hareket eder) — bu ÇOKLU DOĞRUSAL BAĞLANTI yaratır, katsayı İŞARETİ bile TERS çıkabilir; (3) regresyon ZAMANLA ESKİR (bir yılın regresyonu ertesi yıl geçersiz olabilir); (4) R² NADİREN %70'i AŞAR, sıkça %30-35'e DÜŞER — düşük R², tahmin ARALIĞININ genişlediği anlamına gelir, YÖNTEMİN geçersizliği DEĞİL. (s.332-333)
- **İLKE-166:** DCF ile göreli değerleme SIKÇA farklı sonuç verir, hatta biri "ucuz" derken diğeri "pahalı" diyebilir — bu, İKİ FARKLI piyasa etkinliği varsayımından kaynaklanır (İLKE-146); bir hisse DCF'te pahalı ama emsal grubu TAMAMEN aşırı fiyatlıysa göreli değerlemede ucuz çıkabilir (tersi de geçerli). (s.334)

**Chapter 8 — Equity Multiples:**

- **İLKE-167 (Özkaynak değeri ölçüm kararları):** Özkaynak çarpanlarında piyasa değeri özkaynağının ÖLÇÜMÜNDE 3 karar VARDIR: (1) pay başı mı TOPLAM (piyasa değeri) mi? (birden çok hisse SINIFI VEYA seyreltilebilir menkul kıymet [opsiyon/dönüştürülebilir/warrant] varsa İKİSİ AYRIŞIR); (2) NAKİT-DAHİL mi NAKİT-HARİÇ mi? (nakit AĞIRLIKLI firmalarda faaliyet varlıklarının GERÇEK piyasa değerini BOZAR); (3) OPSİYON-KATKILI mı? (yönetici/çalışan opsiyonu + warrant + dönüştürülebilir tahvil ikinci bir özkaynak İDDİASI yaratır, TOPLAM özkaynak değeri market cap + opsiyon DEĞERİ olmalıdır — çoğu analist bu düzeltmeyi YAPMAZ). (s.336-338)
- **İLKE-168 (Ölçek değişkeni tutarlılığı — Tablo 8.1/8.2):** Seçilen özkaynak değeri ölçüsüne EŞLEŞEN kazanç/defter değeri ölçüsü kullanılmalıdır: pay fiyatı↔HBK; toplam piyasa değeri↔opsiyon-giderleştirme SONRASI net kâr; nakit-hariç özkaynak↔net kâr MİNÜS nakitten gelen vergi-sonrası faiz geliri; opsiyon-katkılı özkaynak↔opsiyon-giderleştirme ÖNCESİ net kâr. AYNI mantık defter değeri (Tablo 8.2) için de geçerlidir. (s.338-340)
- **İLKE-169 (Birincil vs tam seyreltilmiş HBK ikilemi):** Birincil (primary) HBK, opsiyon YÜKÜNÜ TAMAMEN görmezden gelir (opsiyon-ağır firmaları YAPAY OLARAK ucuz gösterir); TAM seyreltilmiş HBK, opsiyon SAYISININ yeterli bir ölçü olduğunu VARSAYAR (derin kârdaki UZUN vadeli opsiyonla yakın-para KISA vadeli opsiyonu AYNI CEZAYLA cezalandırır — oysa öncekinin özkaynak değerine etkisi ÇOK DAHA BÜYÜKTÜR); opsiyon-katkılı özkaynak yaklaşımı opsiyonların SAYISI değil DEĞERİNİ kullandığından KAVRAMSAL OLARAK ÜSTÜNDÜR. (s.338-339)
- **İLKE-170 (Şerefiye/goodwill sorunu — P/BV karşılaştırmalarında):** İÇTEN büyüyen (organik) firmalar büyüme varlıklarının değerini bilançoya YAZMAZ; SATIN ALMA yoluyla büyüyen firmalar ödediği piyasa değeri ile hedefin defter değeri ARASINDAKİ farkı ŞEREFİYE olarak YAZAR — bu, satın-alma-ağırlıklı firmaların P/BV oranının YAPAY OLARAK DÜŞÜK (daha "cazip") görünmesine yol açar. Şerefiye; büyüme varlığı primi + KONTROL değeri + SİNERJİ + FAZLA ÖDEME karışımı olduğundan KUSURLU bir vekildir. (s.339-340)
- **İLKE-171 (P/S'nin tanımsal tutarsızlığı ve tarihsel "kaçış" nedeni):** Fiyat/Satış oranı TANIM OLARAK TUTARSIZDIR (pay özkaynak değeri, payda TÜM firmaya ait gelir) ama YAYGIN kullanılır; bu tutarsızlık teknoloji (düşük/sıfır borç, firma değeri≈özkaynak değeri) ve perakende (tarihsel olarak HOMOJEN operating-lease kaldıracı) sektörlerinde TARİHSEL OLARAK az zarar vermiştir — ama teknoloji firmaları BÜYÜK/DEĞİŞKEN nakit tutmaya, perakendeciler kiralama YERİNE mülk SATIN ALMAYA başladıkça bu VARSAYIM ÇÖKER; düşük-nakitli/yüksek-kaldıraçlı firmalar bu çarpanda YAPAY OLARAK ucuz görünmeye başlar. (s.340-341)
- **İLKE-172 (Dağılım karakteristikleri, ABD Ocak 2006):** P/E, PEG, P/BV, P/S HEPSİ pozitif çarpıktır; negatif kazançlı/negatif defter değerli firmalar örneklemden DÜŞER — 7.123 firmalık evrende P/E için sadece 4.179 firma HESAPLANABİLİR (yaklaşık 3.000 firma negatif kazançla dışarıda), P/BV için 1.467 firma NEGATİF defter değeriyle dışarıda kalır. P/S, geliri NEREDEYSE HİÇ negatif olmayan firmalarda hesaplanabildiğinden EN AZ örneklem kaybı yaşayan çarpandır. (s.341-348)
- **İLKE-173 (Sabit büyüme çarpan denklemleri):** İstikrarlı büyüme temettü iskonto modelinden P/E, P/BV, P/S ve Değer/FCFF çarpanları TÜRETİLEBİLİR — HEPSİNİN ortak belirleyicisi büyüme+risk(ke)+payout'tur; P/BV'ye EK olarak ROE, P/S'ye EK olarak net kâr marjı eklenir (Tablo 8.5/7.3). [→ FORMÜL-80] (s.348-349)
- **İLKE-174 (Yüksek büyüme/iki aşamalı çarpanlar):** İki aşamalı (yüksek büyüme+istikrarlı) modelden türetilen çarpanlar AYNI belirleyicilere sahiptir, SADECE girdiler İKİ dönem için AYRI tahmin edilir; payout yerine FCFE/Net Kâr ("potansiyel payout") kullanılabilir — bu NEGATİF olabilir (net kârdan FAZLA yeniden yatırım), ki bu durum firmanın yüksek büyüme döneminde YENİ ÖZKAYNAK ihraç ETMEK zorunda kalacağını (dolayısıyla SEYRELME bekleneceğini) ima eder ve P/E'yi BUGÜNDEN AŞAĞI ÇEKER. [→ FORMÜL-81] (s.349-351)
- **İLKE-175 (Büyüme etkisi ve PEG'in U-şekli):** PEG DIŞINDAKİ TÜM çarpanlar büyümeyle MONOTONİK olarak ARTAR. PEG ise BEKLENMEDİK biçimde U-ŞEKLİNDEDİR: önce büyümeyle DÜŞER, yaklaşık %24-26 büyümede DİPTE (~1,35) yapar, sonrasında TEKRAR YÜKSELİR. Bu, PEG'in doğrusallık varsayımının ÇÖKTÜĞÜNÜN kanıtıdır (doğrusallık olsaydı %0 büyümede PEG=0 olması gerekirdi, gerçekte OLMAZ) — düşük büyümeli firmalar PEG bazında SİSTEMATİK OLARAK "pahalı" görünür. (s.353-355) [→ BAYRAK-23]
- **İLKE-176 (PEG'in yön tutarsızlığı):** %4 vs %15 büyüme kıyasında PEG düşük-büyüme firmasını CEZALANDIRIR (yüksek büyüme "ucuz" görünür); ama %30 vs %40 büyüme kıyasında (dip noktasının SAĞINDA) PEG TERSİNE yüksek-büyüme firmasını CEZALANDIRABİLİR — hangi yönde yanlılık oluşacağı KARŞILAŞTIRILAN büyüme SEVİYESİNE bağlıdır, tek bir kuralla ÖNCEDEN belirlenemez. (s.354-355)
- **İLKE-177 (Faiz oranı-büyüme etkileşimi):** Büyümenin DEĞERİ gelecekte gerçekleşeceğinden, faiz oranları DÜŞÜKKEN büyüme beklentisindeki bir DEĞİŞİM çarpanlar (özellikle P/E) üzerinde ÇOK DAHA BÜYÜK etki yaratır; bu yüzden DÜŞÜK faiz ortamında kazanç sürprizlerine (pozitif VEYA negatif) fiyat tepkisinin de DAHA BÜYÜK olması BEKLENİR. (s.355-356)
- **İLKE-178 (Büyüme süresi etkisi):** Büyüme HIZI sabit tutulup SÜRESİ (3 yıldan 8 yıla) uzatıldığında TÜM çarpanlar YÜKSELİR — rekabet avantajının BÜYÜKLÜĞÜ/SÜRDÜRÜLEBİLİRLİĞİ (Ch.4 bağlantısı) büyüme süresinin ana belirleyicisidir; güçlü/sürdürülebilir rekabet konumundaki firmalar AYNI büyüme oranında bile ZAYIF konumdaki firmalardan DAHA YÜKSEK çarpanlarla işlem görmelidir. (s.356-357)
- **İLKE-179 (Risk etkisi):** Beta (dolayısıyla cost of equity) arttıkça TÜM çarpanlar AZALIR (örnek: cost of equity %9→%15 olduğunda P/E'nin 25,38'den 9,14'e DÜŞMESİ). Riski KONTROL ETMEDEN sektör-içi çarpan kıyası YAPISAL OLARAK riskli firmaları "ucuz", güvenli firmaları "pahalı" gösterir. Çok riskli/genç firmalarda RİSKİ AZALTMANIN özkaynak değerine katkısı genelde BÜYÜMEYİ ARTIRMAKTAN DAHA BÜYÜKTÜR. [→ BAYRAK-24] (s.357-358)
- **İLKE-180 (Yatırım kalitesi/ROE etkisi):** AYNI büyüme oranı FARKLI ROE-tutma oranı KOMBİNASYONLARIYLA elde edilebilir (örnek: %18 büyüme için ROE %20↔tutma %90; ROE %30↔tutma %60; ROE %15↔tutma %120 [YENİ özkaynak ihracı GEREKİR]). ROE ARTTIKÇA TÜM çarpanlar YÜKSELİR; ROE cost of equity'NİN ALTINA düşerse BÜYÜME DEĞER YOK ETMEYE başlar (çarpanlar büyümeyle YÜKSELMEK yerine DÜŞMEYE döner) — "her büyüme eşit değildir" ilkesinin NİCEL kanıtıdır. [→ BAYRAK-25] (s.358-360)
- **İLKE-181 (Net marj etkisi — P/S'nin companion variable'ı):** AYNI gelir büyümesini üreten DÜŞÜK marj/yüksek hacim (indirim perakendeciliği) İLE yüksek marj/düşük hacim stratejileri FARKLI P/S değerini HAK EDER; net marjı İHMAL EDEN bir P/S kıyası düşük-marjlı firmaları YAPAY OLARAK ucuz gösterir. (s.360-361)
- **İLKE-182 (Sistematik yanlılık haritası, Tablo 8.11):** Sektör-içi kıyasta HANGİ değişken ihmal edilirse HANGİ firma tipinin "ucuz" göründüğü ÖNGÖRÜLEBİLİR bir haritadır: büyüme ihmali→düşük-büyüme "ucuz" (P/E,P/BV,P/S) FAKAT yüksek-büyüme "ucuz" (PEG); büyüme SÜRESİ ihmali→zayıf rekabet avantajlı "ucuz"; risk ihmali→riskli firma "ucuz"; ROE ihmali→düşük-ROE "ucuz" (P/BV); net marj ihmali→düşük-marj "ucuz" (P/S). Bu tablo, bir analistin HANGİ değişkeni ÖRTÜK olarak ihmal ettiğini TERS MÜHENDİSLİKLE tespit etmenin bir ARACIDIR. [→ KONTROL LİSTESİ T] (s.361-362)
- **İLKE-183 (Sektör regresyonu uygulaması, İllüstrasyon 7.2/8.2-8.5):** Regresyon, sübjektif ortalama-kıyasından DAHA GÜÇLÜDÜR çünkü GÜVEN ARALIĞI verir ve aşırı/hafif sapmayı SAYISAL olarak sıralar — somut örnekler: yazılım sektöründe (n≈42 firma) büyüme katsayısı +1,77/1% büyüme; Adobe %1,93 hafif ucuz; RSA Security en UCUZ (%59,86 düşük değerli); Ceridian en PAHALI (%92,05 aşırı değerli). (s.363-366)
- **İLKE-184 (Piyasa geneli regresyonu sonuçları, Ocak 2006):** P/E~büyüme+beta+payout (n=2.163): büyüme katsayısı +1,131/1%, beta katsayısı −0,92/1,0 birim, payout katsayısı +0,07/1%; R² DÜŞÜK (P/E "gürültülü"dür). P/BV~ROE+payout+beta+büyüme: R²=%55,6, ROE katsayısı +0,176/1%. P/S~büyüme+payout+beta+net marj: R²=%58,4, n=1.877; beta katsayısının İŞARETİ bazı yıllarda (2003-2004) TERS çıkmıştır (çoklu doğrusal bağlantı — yüksek büyüme+yüksek beta birlikte hareket ettiğinden beta, büyümenin de VEKİLİ haline gelir). (s.372-377)
- **İLKE-185 (Çapraz zaman kıyası):** Çarpanı SADECE tarihsel ORTALAMASIYLA kıyaslamak yerine, O DÖNEMİN geçerli TEMELLERİNE (faiz oranı, risk primi, ROE, payout) göre TAHMİN EDİLEN çarpanla kıyaslamak gerekir — S&P 500 örneğinde (1960-2005) kazanç verimi (E/P) ile T-bond oranı arasında GÜÇLÜ pozitif korelasyon (0,69) vardır; ham "P/E tarihsel ortalamanın üstünde=pahalı" yargısı FAİZ ORANI düştüyse YANLIŞ olabilir. [→ BAYRAK-22] (s.377-379)
- **İLKE-186 (Çapraz ülke kıyası):** Sadece P/E seviyesine bakarak ülkeler arası "ucuz/pahalı" yargısına varmak (örn. "Japonya %45 P/E ile pahalı, Rusya/Venezuela tek haneli P/E ile ucuz") YANILTICIDIR — faiz oranı, büyüme beklentisi, risk primi VE yatırım verimliliği (ROE) ülkeler arası SİSTEMATİK OLARAK farklıdır; bu değişkenler kontrol edildikten SONRA (regresyon ARTIĞI) ortaya çıkan sapma DAHA anlamlıdır. [→ BAYRAK-27] (s.380-383)

---

## Formüller (devam)

- **FORMÜL-73 — Fiyat/Kazanç (P/E) Oranı, 3 Varyant**
  - Formül: `P/E = Fiyat / HBK` — current (son mali yıl HBK), trailing (son 4 çeyrek TTM HBK), forward (gelecek yıl beklenen HBK).
  - Değişkenler: pay her zaman GÜNCEL/ORTALAMA fiyat; payda varyanta göre değişir.
  - QuaxisLabs karşılığı: `calculator.ValuationMetrics.pe_ratio` (`market_cap / r.ttm_net_income`) MEVCUT ve **trailing (TTM)** varyanta karşılık gelir; current (son mali yıl) ve forward (analist tahmini) varyantları YOK — forward P/E zaten VERİ EKSİK (konsensüs kazanç tahmini hiçbir fetcher'da yok).

- **FORMÜL-74 — PEG Oranı**
  - Formül: `PEG = P/E / (Beklenen HBK Büyüme Oranı × 100)`
  - Değişkenler: P/E ile AYNI kazanç bazına dayalı büyüme kullanılmalı (current P/E↔current growth, trailing P/E↔trailing growth); forward P/E ASLA kullanılmamalı (çifte büyüme sayımı riski, örnek: HBK $1→$2'ye [x2] sıçrayıp sonra %4 büyürse 5 yıllık ima edilen büyüme %18,53 çıkar, forward P/E'yi BUNUNLA bölmek büyümeyi İKİ KEZ saymak olur).
  - QuaxisLabs karşılığı: `valuation.py::peg_ratio` (`own_pe / growth_rate_pct`) MEVCUT — ANCAK `growth_rate_pct` girdisi olarak `calculator.Ratios.revenue_growth_yoy_pct` (HASILAT büyümesi) kullanılıyor; kitabın tutarlılık kuralına göre P/E'nin (net kâr bazlı) kazanç büyümesiyle EŞLEŞMESİ gerekir, revenue büyümesi TANIMSAL bir SAPMADIR (marj sabit değilse gelir büyümesi≠kâr büyümesi) — kök neden yine çok-yıllı HBK/net kâr büyüme serisi eksikliği (bkz. Uygulama Notları).

- **FORMÜL-75 — Fiyat/Defter Değeri (P/BV) Oranı**
  - Formül: `P/BV = Piyasa Değeri Özkaynak / Defter Değeri Özkaynak`
  - QuaxisLabs karşılığı: `calculator.ValuationMetrics.pb_ratio` (`market_cap / equity_current`) MEVCUT ve TANIM OLARAK TUTARLI (özkaynak/özkaynak).

- **FORMÜL-76 — Firma Değeri/Satış (VS), Tutarlı Gelir Çarpanı**
  - Formül: `FD/Satış = Firma Değeri (net nakit) / Hasılat`
  - QuaxisLabs karşılığı: `calculator.ValuationMetrics.ev_revenue` (`enterprise_value / r.ttm_revenue`) MEVCUT — kitabın "TUTARLI" (numerator/denominator ikisi de firma-geneli) gelir çarpanı tanımıyla BİREBİR ÖRTÜŞÜYOR (**pozitif bulgu**: QuaxisLabs zaten P/S DEĞİL, doğru VS versiyonunu kullanıyor).

- **FORMÜL-77 — Fiyat/Satış (P/S) Oranı, Tanımsal Olarak Tutarsız ama Yaygın**
  - Formül: `P/S = Piyasa Değeri Özkaynak / Hasılat`
  - QuaxisLabs karşılığı: DOĞRUDAN alan YOK ama `market_cap` ve `r.ttm_revenue` ZATEN mevcut olduğundan tek satırla eklenebilir (DÜŞÜK maliyetli) — ancak kitabın kendi tutarlılık testine göre FORMÜL-76 (FD/Satış, zaten mevcut) DAHA DOĞRU versiyondur; P/S'in EKLENMESİ sadece "piyasada en çok kullanılan format" gerekçesiyle DÜŞÜNÜLEBİLİR, öncelik DÜŞÜK.

- **FORMÜL-78 — Firma Değeri/FAVÖK (EV/EBITDA)**
  - Formül: `FD/FAVÖK = Firma Değeri / FAVÖK`
  - QuaxisLabs karşılığı: `calculator.ValuationMetrics.ev_ebitda` MEVCUT.

- **FORMÜL-79 — Fiyat/FAVÖK (Price/EBITDA), Tanımsal Olarak Tutarsız**
  - Formül: `Fiyat/FAVÖK = Piyasa Değeri Özkaynak / FAVÖK`
  - QuaxisLabs karşılığı: bu ÖZEL tutarsız varyant `calculator.py`'de UYGULANMIYOR (iyi) — ANCAK `ValuationMetrics.price_to_operating_profit` (`market_cap / r.ttm_operating_profit`) AYNI TUTARSIZLIK TÜRÜNÜ (pay özkaynak, payda firma-geneli esas faaliyet kârı) TAŞIYOR — bkz. BAYRAK-19, bu Kısmın EN ÖNEMLİ kod-seviyesi bulgusu.

- **FORMÜL-80 — Sabit Büyüme Çarpan Denklemleri (DDM Türetimi)**
  - Formül: `P/E = payout×(1+g)/(ke-g)`; `P/BV = ROE×payout×(1+g)/(ke-g)`; `P/S = net_marj×payout×(1+g)/(ke-g)`; `Değer/FCFF = (1+g)/(kc-g)`
  - Değişkenler: `payout`=temettü dağıtım oranı (veya FCFE/Net Kâr, "potansiyel payout"), `g`=istikrarlı büyüme, `ke`=özkaynak maliyeti, `ROE`=özkaynak getirisi, `net_marj`=net kâr/hasılat, `kc`=sermaye maliyeti (WACC).
  - QuaxisLabs karşılığı: `net_margin_current` VE `roe_annualized` MEVCUT; `payout`/DPS **VERİ EKSİK** (kitaplar arası ARTIK 7. kez tekrarlanan en sık açık); `ke`, `valuation.py`'de β=1 basitleştirmesiyle MEVCUT; `kc`(WACC) **TAMAMEN EKSİK** (Kısım 1 FORMÜL-21).

- **FORMÜL-81 — İki Aşamalı (Yüksek Büyüme) Çarpan Denklemleri**
  - Formül: yüksek büyüme dönemi (n yıl, `payout_hg`,`g_hg`,`ke_hg`) + istikrarlı dönem (`payout_st`,`gn`,`ke_st`) parametreleriyle P/E, PEG, P/BV, P/S TÜRETİLİR (İllüstrasyon 8.1: örnek girdilerle P/E=25,38, PEG=1,41, P/S=2,54x).
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çok dönemli büyüme/payout PROJEKSİYONU YOK (Kısım 1-3'te TEKRAR tespit edilen AYNI yapısal eksiklik: DPS + çok-yıllı büyüme serisi).

- **FORMÜL-82 — Sektör/Piyasa Regresyonu (Çarpan ~ Temel Değişkenler)**
  - Formül: `Çarpan = a + b1×Büyüme + b2×Risk(β) + b3×Payout (+ companion değişken)`
  - QuaxisLabs karşılığı: **YAPISAL OLARAK UYGULANAMAZ** — hem beta hem payout VERİ EKSİK, hem de QuaxisLabs TEKİL varlık analiz motorudur; bir SEKTÖR/PİYASA regresyonu ÇOKLU firma cross-sectional veri seti + istatistik (OLS regresyon) ALTYAPISI gerektirir, bu şu an HİÇBİR modülde YOK — bu, önceki kısımlardaki "VERİ EKSİK" bulgularından FARKLI bir eksiklik TÜRÜDÜR (tekil veri değil, ÇOK-FİRMA KARŞILAŞTIRMA ÖZELLİĞİ eksikliği).

- **FORMÜL-83 — Regresyon Bazlı Aşırı/Düşük Değer Yüzdesi**
  - Formül: `%Sapma = (Gerçek Çarpan - Tahmin Edilen Çarpan) / Tahmin Edilen Çarpan`
  - QuaxisLabs karşılığı: FORMÜL-82'nin regresyon altyapısı eksikliğine BAĞLI, **UYGULANAMAZ**.

- **FORMÜL-84 — Kazanç Verimi (Earnings Yield, E/P)**
  - Formül: `E/P = HBK / Fiyat = 1 / (P/E)`
  - QuaxisLabs karşılığı: `pe_ratio` MEVCUT olduğundan basit TERS ÇEVİRME ile hesaplanabilir (**DÜŞÜK maliyetli eklenti**) — Damodaran'ın negatif-kazanç örneklem-dışı-bırakma yanlılığına (İLKE-156) karşı önerdiği ÇÖZÜMLERDEN biri; negatif net kârlı şirketlerde bile ANLAMLI (negatif) bir değer üretir, oysa `pe_ratio` böyle şirketlerde `None` döner.

- **FORMÜL-85 — Agregatif P/E (Evren Seviyesi, Zarar Edenler Dahil)**
  - Formül: `Agregatif P/E = Σ Piyasa Değeri_i / Σ Net Kâr_i` (i = evrendeki TÜM firmalar, zarar edenler DAHİL)
  - QuaxisLabs karşılığı: **UYGULANAMAZ (mimari eksiklik)** — sektör/evren AGREGASYON altyapısı YOK (tekil varlık motoru); FORMÜL-82 ile AYNI kök eksiklik türü.

- **FORMÜL-86 — Nakit-Hariç (Net) Piyasa Özkaynağı ve Eşleşen Kazanç**
  - Formül: `Net MV Özkaynak = Piyasa Değeri Özkaynak - Nakit ve Benzerleri`; eşleşen kazanç: `Net Kâr - (1-vergi oranı)×Nakit Faiz Geliri`
  - QuaxisLabs karşılığı: **KISMEN UYGULANABİLİR** — `cash` VE `market_cap` MEVCUT (basit çıkarma, DÜŞÜK maliyetli); nakit faiz gelirinin AYRIŞTIRILMASI (gelir tablosunda standalone alan olarak) YOK, bu yüzden BASİT bir yaklaşık (kazancı OLDUĞU GİBİ bırakıp sadece payı nakitten arındırmak) uygulanabilir, TAM doğru değil.

- **FORMÜL-87 — Opsiyon-Katkılı Özkaynak Değeri**
  - Formül: `Opsiyon-Katkılı MV = Piyasa Değeri Özkaynak + Yönetici/Çalışan Opsiyonlarının Tahmini Değeri`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çalışan/yönetici opsiyon programı verisi hiçbir fetcher'da YOK; bu konu Ch.11'de (Kısım 6, "Employee Equity Options") GENİŞLEYECEK, burada İLK kez işaretlendi.

---

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| Sell-side araştırma raporlarında göreli:DCF oranı (2001, 550 rapor) | **~10:1** | Göreli değerlemenin PRATİKTEKİ EZİCİ baskınlığının somut kanıtı | Ch.7, s.308 |
| P/E dağılımı, ABD Ocak 2005 | Medyan **23** vs Ortalama **48** | Pozitif çarpıklığın somut örneği — medyan kıyası önerilir | Ch.7, s.317-318 |
| "Normal dağılım" 2-std-sapma aralığı (Ocak 2005, ort. 48,12) | **40,74 – 55,5** | Binlerce firma bu aralığın DIŞINDA — normal dağılım varsayımı çarpanlarda GEÇERSİZ | Ch.7, s.318-319 |
| S&P 500 ortalama P/E, veri kaynağına göre (Kasım 2005) | Yahoo **%16,5** vs Morningstar **%24,2** | Aykırı değer işleme farkının SOMUT kanıtı | Ch.7, s.319-320 |
| P/E hesaplanabilen firma oranı (ABD evreni, Ocak 2006) | **4.179 / 7.123** (~%59) | Negatif kazanç örneklem-dışı-bırakma yanlılığının BÜYÜKLÜĞÜ | Ch.8, s.342-343 |
| PEG oranı, tüm firmalar vs teknoloji (Ocak 2006) | Ortalama **2,64** vs **2,54**; Medyan **1,70** vs **1,66** | PEG'de de aynı ortalama>medyan çarpıklığı | Ch.8, Tablo 8.4 |
| P/BV dağılımı, ABD Ocak 2006 | Ortalama **5,33** vs Medyan **2,32** | 1.467/7.123 firma NEGATİF defter değeriyle örneklem dışı | Ch.8, s.346-347 |
| Yüksek büyüme firma örneği (İllüstrasyon 8.1) — girdiler | ROE **%20**, payout **%10** (tutma **%90**), g(5y) **%18**, β **1,0**, ke **%9** | Sonuç: P/E **25,38**, PEG **1,41**, P/S **2,54x** — çarpan türetiminin uçtan uca somut uygulaması | Ch.8, s.352-353 |
| Büyüme oranı P/E'ye etkisi (aynı örnek, g:%18→%8) | P/E **25,38 → 16,38** | Büyüme etkisinin büyüklüğü — PEG DIŞINDA tüm çarpanlar büyümeyle monotonik artar | Ch.8, Tablo 8.6 |
| PEG'in "dip" noktası | g **%24-26** iken PEG **~1,35** (minimum) | PEG'in doğrusallık varsayımının SOMUT olarak çöktüğü nokta | Ch.8, s.354-355 |
| Riskin P/E'ye etkisi (aynı temel örnek, ke:%9→%15) | P/E **25,38 → 9,14** | Risk etkisinin büyüklüğü, büyüme etkisiyle KIYASLANABİLİR | Ch.8, Tablo 8.8, s.357-358 |
| Yazılım sektörü P/E~büyüme regresyonu (Ocak 2006) | Katsayı **+1,77**/1% büyüme | Sektör regresyonunun somut uygulaması | Ch.8, İllüstrasyon 8.2 |
| Yazılım sektöründe en ucuz/en pahalı (regresyon artığı) | RSA Security **-%59,86** (ucuz) / Ceridian **+%92,05** (pahalı) | Regresyon tabanlı göreli değer sıralamasının uç örnekleri | Ch.8, s.365-366 |
| Yarı iletken PEG karşılaştırması (Ocak 2006) | TSMC ADR **0,32** (en ucuz) / Intersil **4,00** (en pahalı) / sektör ort. **1,64** | PEG'in doğrusal-olmayan (ln-büyüme regresyonlu) düzeltilmiş kullanım örneği | Ch.8, İllüstrasyon 8.3 |
| Intel PEG değerlendirmesi (regresyon artığı) | PEG **1,22** vs tahmin → **~%33** düşük değerli | Ham PEG (sektör ort. altı) İLE regresyon-düzeltilmiş sonucun TUTARLILIK örneği | Ch.8, s.368 |
| ABD bankaları P/BV~ROE regresyonu (Ocak 2006) | R² **%65,32** | ROE'nin P/BV'nin en güçlü companion variable'ı olduğunun kanıtı | Ch.8, İllüstrasyon 8.4 |
| Banka örneğinde en ucuz/en pahalı (regresyon artığı) | Popular Inc. **~-%30** (ucuz) / State Street **+%33,41** (pahalı) | | Ch.8, s.369-370 |
| Özel perakende (Coach) P/S~net marj örneği | Net marj **%21,41**, gerçekleşen P/S **7,19** (tahminin ÜSTÜNDE) | Net marj kontrol edilmeden P/S kıyasının nasıl yanlış sonuç vereceğinin somut örneği | Ch.8, İllüstrasyon 8.5 |
| Piyasa geneli P/E regresyonu (Ocak 2006, n=2.163) | Büyüme **+1,131**/1%, Beta **-0,92**/1,0, Payout **+0,07**/1% | Piyasa-geneli regresyonun somut katsayıları | Ch.8, s.372-373 |
| Piyasa geneli P/BV regresyonu | R² **%55,6**, ROE katsayısı **+0,176**/1% | P/BV regresyonlarının P/E'den DAHA GÜÇLÜ (yüksek R²) olduğunun kanıtı | Ch.8, s.375-376 |
| Piyasa geneli P/S regresyonu | R² **%58,4**, n=1.877 | | Ch.8, s.376-377 |
| S&P 500 E/P ~ T-bond korelasyonu (1960-2005) | **0,69** | Faiz oranı-çarpan ilişkisinin uzun dönemli somut kanıtı | Ch.8, İllüstrasyon 8.6 |
| E/P regresyonu (1960-2005) | T-bond **+0,7437%** E/P /1%; getiri eğrisi eğimi **-0,3274%** E/P /1% | | Ch.8, s.379 |
| S&P 500 P/E, erken 2006 | **18,27x** — regresyon tahminine göre "neredeyse doğru fiyatlı" | Zamanlar-arası fundamentale-göre-düzeltilmiş kıyas örneği | Ch.8, s.379 |
| Çapraz ülke P/E (Ocak 2006, ham) | Japonya **45,01** (en yüksek) / Rusya, Venezuela tek haneli (en düşük) | Ham kıyasın (kontrolsüz) YANILTICI görünümü | Ch.8, İllüstrasyon 8.8 |
| Çapraz ülke P/E regresyonu (uzun vadeli faiz+eğim+GOP dummy) | R² **%24,7**, uzun vadeli faiz katsayısı **+0,68**/1% | Brezilya en PAHALI, Venezuela en UCUZ (regresyon SONRASI) — ham sıralamadan FARKLI sonuç | Ch.8, s.382-383 |
| Relative valuation regresyonlarında tipik R² aralığı | Nadiren **>%70**, sıkça **%30-35** | Düşük R²'nin YÖNTEM geçersizliği değil, GENİŞ tahmin aralığı anlamına geldiği uyarısı | Ch.7, s.333 |

## Kontrol listeleri (devam)

**Kontrol Listesi Q — Çarpan Kullanımının 4 Temel Adımı (Ch.7, s.313-334):**
1. **Tanım Testi:** Pay/payda TUTARLI mı (özkaynak-özkaynak VEYA firma-firma)? TÜM karşılaştırılan firmalarda AYNI varyant (current/trailing/forward) ve AYNI muhasebe standardı kullanılıyor mu?
2. **Tanımlayıcı Test:** Çarpanın PİYASA GENELİNDEKİ (sadece sektör değil) dağılımı (ortalama/medyan/persentil) biliniyor mu? Aykırı değer/veri kaynağı farkı hesaba KATILDI mı?
3. **Analitik Test:** Çarpanı belirleyen temel değişkenler (büyüme/risk/payout + companion variable) VE bunların çarpanla İLİŞKİSİ (doğrusal mı değil mi) BİLİNİYOR mu?
4. **Uygulama Testi:** Karşılaştırılabilir firmalar RİSK/BÜYÜME/NAKİT AKIŞI benzerliğiyle mi seçildi (sadece sektör aidiyeti DEĞİL)? Kalan farklar için düzeltme YAPILDI mı?

**Kontrol Listesi R — Farkları Kontrol Etmenin 3 Yolu (Ch.7, s.327-333):**
1. **Sübjektif düzeltme** — ortalamadan sapmayı analistin YARGISIYLA açıklama (YÜKSEK önyargı/tahmin hatası riski).
2. **Modifiye çarpan** (PEG gibi) — TEK companion değişken için DOĞRUSAL varsayımlı bölme düzeltmesi (İKİ örtük varsayım: diğer TÜM değişkenlerde EŞİTLİK + doğrusallık).
3. **İstatistiksel teknik** (sektör/piyasa regresyonu) — ÇOKLU değişken + ilişki GÜCÜ ölçümü + güven aralığı sağlar; çoklu doğrusal bağlantı/zamanla eskime risklerine DİKKAT.

**Kontrol Listesi S — Özkaynak Değeri Ölçüm Kararları (Ch.8, s.336-338):**
1. Pay başı mı TOPLAM (piyasa değeri) mi? (çoklu hisse sınıfı/seyreltme farkına DİKKAT)
2. NAKİT-dahil mi NAKİT-hariç mi? (nakit-ağır firmalarda faaliyet varlığı değerini BOZAR)
3. Opsiyon-katkılı mı? (yönetici opsiyonu/warrant/dönüştürülebilir tahvil genelde İHMAL EDİLİR)
Her seçimin EŞLEŞEN bir kazanç/defter değeri ölçüsü VARDIR (Tablo 8.1/8.2) — TUTARSIZ eşleştirme YANLIŞ sonuç verir.

**Kontrol Listesi T — Sektör-İçi Çarpan Kıyasında İhmal Edilmemesi Gereken Değişkenler (Tablo 8.11 sentezi, Ch.8, s.361-362):**
- Büyüme (ihmal → düşük büyüme "ucuz" [P/E,P/BV,P/S] VEYA yüksek büyüme "ucuz" [PEG] görünür)
- Büyüme SÜRESİ (ihmal → zayıf rekabet avantajlı firmalar "ucuz" görünür)
- Risk/beta (ihmal → riskli firmalar "ucuz" görünür)
- ROE (ihmal → düşük ROE'li firmalar P/BV'de "ucuz" görünür)
- Net marj (ihmal → düşük marjlı firmalar P/S'de "ucuz" görünür)

## Kırmızı bayraklar (devam)

- **BAYRAK-19 — Tutarsız Tanımlı Çarpan Kullanımı (Price/EBITDA Tipi Hata):** Pay ÖZKAYNAK değeri, payda FİRMA-geneli kazanç ölçüsü olduğunda, YÜKSEK BORÇLU firmalar SİSTEMATİK OLARAK "ucuz" görünür (aslında pahalı/adil fiyatlı olabilir) — "her firma için aynı hesaplandığı için sorun yok" savunması YANLIŞTIR. Nasıl tespit edilir: pay/payda TANIM tutarlılığını (özkaynak-özkaynak mı, firma-firma mı) kontrol et. **QuaxisLabs bağlamında somut bulgu:** `calculator.ValuationMetrics.price_to_operating_profit` (`market_cap / ttm_operating_profit`) TAM OLARAK bu hatayı taşıyor — pay özkaynak (`market_cap`), payda firma-geneli (esas faaliyet kârı, faiz ÖNCESİ) — yüksek borçlu şirketler bu metrikte YAPAY OLARAK ucuz görünecektir; TUTARLI alternatif `enterprise_value / ttm_operating_profit` olurdu. Gereken veri: `enterprise_value` ZATEN mevcut, sadece formül DEĞİŞİKLİĞİ gerekir. (Ch.7, s.314-315)
- **BAYRAK-20 — Ortalamaya Göre "Ucuz/Pahalı" Yargısı (Medyan Yerine):** Çarpan dağılımları HER ZAMAN pozitif çarpıktır — ortalama HER ZAMAN medyandan yüksektir; "sektör ortalamasının altında=ucuz" yargısı SİSTEMATİK OLARAK aşırı sayıda firmayı "ucuz" gösterir. Nasıl tespit edilir: karşılaştırma MEDYAN'a göre mi yoksa ORTALAMAYA göre mi yapılıyor kontrol et. Gereken veri: sektör/evren çapında çarpan DAĞILIMI (QuaxisLabs'ta evren-çapında persentil/medyan hesaplama ALTYAPISI YOK — bkz. Uygulama Notları). (Ch.7, s.317-318)
- **BAYRAK-21 — Negatif Kazanç/Defter Değeri Örneklem-Dışı-Bırakma Yanlılığı:** P/E veya P/BV ortalaması hesaplanırken zarar eden/negatif özkaynaklı firmalar örneklemden DÜŞER, bu da KALAN örneklemin ortalamasını YUKARI yanlar. Nasıl tespit edilir: kullanılan ortalamanın KAÇ firma üzerinden hesaplandığı ile evrendeki TOPLAM firma sayısı KIYASLANMALI (büyük fark = yanlılık riski). Gereken veri: evren-çapında pozitif/negatif kazanç FİRMA SAYISI (mimari eksiklik). (Ch.7, s.319-321)
- **BAYRAK-22 — Çapraz Zaman Kıyasında Temel Değişim İhmali:** Bir çarpanı SADECE geçmiş ortalamasıyla kıyaslayıp "tarihsel ortalamanın üstünde=pahalı" sonucuna varmak faiz oranı/risk primi/ROE/payout DEĞİŞİMİNİ göz ardı eder. Nasıl tespit edilir: kıyas TEMEL DEĞİŞKENLERE göre TAHMİN EDİLEN çarpanla mı yapılıyor, yoksa HAM tarihsel ortalamayla mı? Gereken veri: çok-yıllı faiz oranı/ROE/payout serisi (KISMEN mevcut, DPS eksik). (Ch.8, s.377-379)
- **BAYRAK-23 — PEG Oranının Doğrusallık Varsayımı İhlali:** PEG, düşük büyüme (%0'a yakın) firmaları SİSTEMATİK OLARAK "pahalı" gösterir (gerçek ilişki U-şeklindedir, ~%24-26 büyümede diplenir). Nasıl tespit edilir: PEG'e dayalı sıralama yapılırken karşılaştırılan firmaların büyüme SEVİYESİ (dipin hangi tarafında) kontrol edilmeli; forward P/E'nin PEG'de KULLANILMAMASI (çifte sayım riski) ayrıca doğrulanmalı. Gereken veri: `growth_rate_pct` (QuaxisLabs'ta MEVCUT ama FORMÜL-74'te not edilen tanım sapmasıyla). (Ch.8, s.353-355)
- **BAYRAK-24 — Riski Kontrol Etmeden Sektör-İçi Çarpan Kıyası:** Beta/kaldıraç farkını göz ardı eden bir P/E veya PEG kıyası, riskli firmaları SİSTEMATİK OLARAK "ucuz" gösterir. Nasıl tespit edilir: kıyaslanan firmaların beta/borç oranı FARKI kontrol edilmeli. Gereken veri: beta **VERİ EKSİK** (Kısım 1), borç oranı (`debt_to_equity`) MEVCUT — kısmi tespit MÜMKÜN. (Ch.8, s.357-358)
- **BAYRAK-25 — ROE'yi Kontrol Etmeden P/BV Kıyası:** Düşük ROE'li (özellikle ROE<cost of equity) firmalar P/BV'de SİSTEMATİK OLARAK "ucuz" görünür, ama bu genelde DEĞER YARATMAMANIN doğal sonucudur, FIRSAT DEĞİLDİR. Nasıl tespit edilir: ROE-cost of equity FARKI (fazla getiri) HESAPLANMADAN P/BV yorumlanmamalı. Gereken veri: `roe_annualized` MEVCUT, `ke` (β=1 basitleştirmeli) `valuation.py`'de MEVCUT — bu bayrak DÜŞÜK maliyetle TESPİT EDİLEBİLİR. (Ch.8, s.358-360)
- **BAYRAK-26 — Sektöre Özgü Çarpanların Çapa Eksikliği:** "Hit başına değer"/"abone başına değer" gibi sektöre özgü çarpanlar çapraz sektör/piyasa referans NOKTASI sunmadığından yatırımcıları normalde kabul ETMEYECEKLERİ aşırı fiyatlara razı edebilir. Nasıl tespit edilir: kullanılan çarpanın TÜM piyasada hesaplanabilir olup OLMADIĞI kontrol edilmeli. Gereken veri: METODOLOJİK kontrol, veri gerektirmez. (Ch.7, s.312-313)
- **BAYRAK-27 — Çapraz Ülke P/E Kıyasında Makro Fark İhmali:** Sadece P/E seviyesine bakarak "X ülkesi pahalı, Y ülkesi ucuz" yargısına varmak ülkeler arası faiz oranı/büyüme/risk primi FARKINI yok sayar (somut örnek: Japonya ham P/E'de en pahalı ama regresyon SONRASI Brezilya en pahalı çıkar). Nasıl tespit edilir: kıyas faiz oranı+risk+büyüme KONTROLÜ SONRASI (regresyon artığı) sapmaya mı dayanıyor, yoksa HAM P/E seviyesine mi? Gereken veri: METODOLOJİK kontrol + ülke-düzeyi makro veri (QuaxisLabs kapsamı DIŞINDA — tekil şirket motoru). (Ch.8, s.380-383)

## Uygulama notları (devam)

**Nicel (skorlanabilir):**
- **Kazanç Verimi (E/P, FORMÜL-84)** — `pe_ratio`'nun basit TERSİ, tek satır kod, DÜŞÜK maliyetli; negatif kazançlı şirketlerde bile anlamlı SIRALAMA sağlar.
- **Fiyat/Satış (P/S, FORMÜL-77)** — `market_cap`/`ttm_revenue`, tek satır kod; ama zaten TUTARLI alternatifi (`ev_revenue`) MEVCUT olduğundan öncelik DÜŞÜK.
- **Nakit-hariç (net) piyasa değeri özkaynak (FORMÜL-86)** — `market_cap - cash`, tek satır kod; nakit-ağır şirketlerde (özellikle teknoloji benzeri BIST/NASDAQ şirketleri) çarpanları daha ANLAMLI hale getirir.
- **BAYRAK-19 kod düzeltmesi** — `price_to_operating_profit` alanının TANIM OLARAK TUTARSIZ olduğu tespit edildi; ya `enterprise_value / ttm_operating_profit` (FD/EFK) olarak DEĞİŞTİRİLMELİ ya da mevcut isim/dokümantasyonuna "tutarsız tanım, SADECE referans amaçlı" notu EKLENMELİ — bu Kısmın EN somut, EN düşük maliyetli kod-kalitesi bulgusudur.
- **BAYRAK-25 (ROE-ke farkı üzerinden P/BV yorumlama)** — `roe_annualized` ve `valuation.py`'nin β=1 basitleştirmeli `cost_of_equity_pct`'i ZATEN mevcut olduğundan, "fazla getiri" (ROE-ke) işareti `pb_ratio` ile BİRLİKTE gösterilerek DÜŞÜK maliyetli bir tutarlılık kontrolü (rozet) üretilebilir.

**Nitel (LLM yorumuna uygun):**
- Companion variable çerçevesi (İLKE-160) — LLM'e "bu firma, çarpanının companion değişkeninde (büyüme/ROE/net marj) sektöre göre NASIL konumlanıyor" diye SORULABİLECEK bir değerlendirme çerçevesi.
- Sektöre özgü çarpan riski (BAYRAK-26) — LLM'in "bu firma standart-dışı bir metrikle mi savunuluyor" diye bir şüphecilik notu üretmesi.
- Çapraz zaman/ülke kıyası uyarıları (BAYRAK-22/27) — rapor şablonuna eklenebilecek bir "bu kıyas temel değişken FARKLARINI hesaba kattı mı" dikkat notu.
- Şerefiye/goodwill kirliliği (İLKE-170) — satın-alma-ağırlıklı büyüyen şirketlerin P/BV'sinin neden YANILTICI ucuz görünebileceğine dair LLM'e verilebilecek NİTEL bir uyarı.

**Veri eksikliği / mimari eksiklik nedeniyle UYGULANAMAZ:**
- **PEG'in doğru büyüme bazı (FORMÜL-74)** — kitaba göre EPS/net kâr büyümesi gerekirken QuaxisLabs REVENUE büyümesi kullanıyor; kök neden yine çok-yıllı HBK/net kâr büyüme serisi eksikliği (kitaplar arası 8. tekrar).
- **Sektör/piyasa regresyonu (FORMÜL-82/83/85) — YENİ TÜR eksiklik:** Bu Kısımda İLK KEZ netleşen bulgu, önceki "tekil veri EKSİK" örüntüsünden FARKLIDIR — QuaxisLabs'ın TEKİL varlık analiz mimarisi, ÇOK-FİRMA cross-sectional karşılaştırma/regresyon/persentil ALTYAPISINI hiç İÇERMİYOR. Beta/DPS gibi veri açıkları giderilse BİLE, bu formül grubu (sektör regresyonu, agregatif P/E, evren-çapında persentil) YENİ bir MİMARİ bileşen (çoklu-şirket istatistik motoru) gerektirir — bu, ürünün BIST/NASDAQ/Crypto evrenini TOPLU analiz eden bir modül eklemesi durumunda değerlendirilebilecek, uzun vadeli bir ÖZELLİK boşluğudur.
- **İki aşamalı çarpan modelleri (FORMÜL-81)** — DPS/çok-yıllı büyüme eksikliğine bağlı.
- **Opsiyon-katkılı özkaynak (FORMÜL-87)** — çalışan opsiyon verisi YOK; bu konu Kısım 6'da (Ch.11 Employee Equity Options) GENİŞLEYECEK.

---

# KISIM 5 — Chapter 9-10: Value Multiples + Cash, Cross Holdings, and Other Assets

**Kapsam:** Chapter 9: Value Multiples (PDF s.386-421), Chapter 10: Cash, Cross Holdings, and Other Assets + Appendix 10.1 (PDF s.422-477). Bu Kısımla **Part Two: Relative Valuation** BİTER ve **Part Three: Loose Ends in Valuation**'ın İLK bölümü işlenir. ID numaralandırması Kısım 1-4'ün devamı (İLKE-187'den, FORMÜL-88'den, BAYRAK-28'den, Kontrol Listesi U'dan başlar; kesintisiz).

## İlkeler (devam)

**Chapter 9 — Value Multiples:**

- **İLKE-187:** DCF'te özkaynaktan firmaya geçişte kaldıraç esnekliği kazanıldığı gibi, FİRMA DEĞERİ çarpanları da farklı borç oranlı şirketleri kıyaslarken ÖZKAYNAK çarpanlarından DAHA KOLAY çalışılır — bu Kısmın temel gerekçesidir. (s.386)
- **İLKE-188 (Firma değeri ölçümünde ek kararlar):** Özkaynak değerindeki 2 karara (nakit, opsiyon — Kısım 4 İLKE-167) EK olarak firma değerinde 2 YENİ karar gerekir: ÇAPRAZ İŞTİRAKLERİN NASIL ele alınacağı VE BORCA NELERİN dahil edileceği. (s.386-387)
- **İLKE-189 (İsraf edilen/edilmeyen nakit ayrımı):** Enterprise Value = Firma Değeri − Nakit; ama "hangi nakdin" netleştirileceği tartışmalıdır — bazı analistler faaliyet/fazla (excess) nakit AYRIMI yapar, DAHA DOĞRUSU İSE İSRAF EDİLEN (piyasa-altı getirili) İLE İSRAF EDİLMEYEN (adil piyasa getirili) nakit ayrımıdır; SADECE israf edilmeyen nakit netleştirilmelidir kavramsal olarak (Ch.10'da detaylanır). (s.387)
- **İLKE-190 (Çapraz iştiraklerde 2 yaygın hata):** (1) azınlık payının SADECE özkaynak kısmını sayıp borç/nakdini SAYMAMAK — TUTARSIZLIK (iştirakin özkaynağının %5'i sayılıyorsa borç/nakdinin de %5'i sayılmalı VEYA HİÇ sayılmamalı); (2) çoğunluk iştiraklerinde bilanço "azınlık payı" (DEFTER değeri) kalemini doğrudan FD'ye eklemek — azınlık payının PİYASA değeri defter değerinden GENELDE FARKLIDIR, bu yüzden defter-değeri-eklemek YANLIŞTIR. [→ BAYRAK-28] (s.387-389)
- **İLKE-191 (Konsolide değer, iki eşdeğer yol):** (a) TAM formül — azınlık payların net borç PAYINI + çoğunluk payların TAM özkaynak değerini ana şirket FD'sine eklemek; (b) DAHA KOLAY yöntem — İŞTİRAKSİZ (parent-only) firma değerini hesaplamak (konsolide FD'den azınlık holding'lerin piyasa değerini VE çoğunluk holding'lerin hem piyasa değerini hem konsolide borç/nakdini ÇIKARARAK). (s.389)
- **İLKE-192 (Borç tanımı — FD hesabında):** Cost of capital hesabındaki DAR tanımdan (sadece faizli borç+kira) FARKLI olarak, firma değeri hesabında diğer potansiyel yükümlülükler (fonsuz emeklilik/sağlık vb.) de dahil edilmelidir; PİYASA değeri (tahmini olsa bile) DEFTER değerinden HER ZAMAN TERCİH EDİLİR. (s.389-390)
- **İLKE-193 (Ölçek değişkeni tutarlılığı, Tablo 9.1):** Kazanç ölçüsü FAVÖK, FVÖK VEYA vergi-sonrası FVÖK olabilir — HEPSİ nakit/azınlık gelirinden ÖNCEKİ ölçülerdir; SADECE ana şirket (konsolide OLMAYAN) kazancı kullanılıyorsa değer ölçüsü de SADECE ana şirketi yansıtmalı (nakit+TÜM çapraz iştirakler netleştirilmeli); KONSOLİDE kazançla çalışılıyorsa nakit+azınlık netleştirilir ama TAM çoğunluk payı DAHİL edilir. (s.391-392)
- **İLKE-194 (Defter değeri tutarlılığı, Tablo 9.2):** Piyasa değeri ölçüsüne (firma değeri/enterprise value) EŞLEŞEN defter değeri ölçüsü kullanılmalıdır — TOPLAM VARLIK defter değeri HİÇBİR firma/FD ölçüsüyle EŞLEŞMEZ, sadece TAHMİNİ PİYASA DEĞERİ TOPLAM VARLIKLA eşleştirilebilir. (s.392-393)
- **İLKE-195 (Gelir çarpanı tutarlılığı):** P/S TUTARSIZ olduğundan (Kısım 4 İLKE-171), FD/Satış DAHA TUTARLI versiyondur; çapraz iştirakler BURADA da bozucu etki yapar — azınlık geliri NETLEŞTİRİLMELİ ama azınlık PAYI da firma değerinden ÇIKARILMALI (TUTARLI kalması için). (s.393)
- **İLKE-196:** Aktivite değişkenleri (abone başına, ziyaretçi başına vb.) İÇİN en mantıklı pay ölçüsü Enterprise Value'dur (Kısım 4'teki sektöre özgü çarpan uyarısı — İLKE-150 — BURADA da geçerlidir). (s.393-394)
- **İLKE-197 ("FD/FAVÖK<7x=ucuz" kuralının çürütülmesi):** FD/FAVÖK, FD/FVÖK, FD/vergi-sonrası-FVÖK dağılımları da (Kısım 4'teki gibi) pozitif çarpıktır (ortalama>medyan); yaygın "FD/FAVÖK 7x'in altındaysa ucuz" pratik kuralı, ABD'de yaklaşık **1.500** firmanın bu eşiğin ALTINDA işlem görmesiyle ÇÜRÜTÜLÜR — sabit sayısal eşiklerin dağılımın ZAMAN/SEKTÖRE göre kaymasını göz ardı ettiğinin somut kanıtı. [→ BAYRAK-30] (s.394-396)
- **İLKE-198 (FAVÖK çarpanlarının örneklem avantajı):** Negatif FAVÖK'lü firma SAYISI, negatif HBK'lı firma sayısından ÇOK DAHA AZDIR (özellikle amortismanın büyük gider kalemi olduğu telekom/kablo/hücresel sektörlerde) — bu yüzden FAVÖK çarpanları P/E'den DAHA AZ örneklem-dışı-bırakma yanlılığı (Kısım 4 İLKE-156) taşır. (s.396)
- **İLKE-199 (Değer/Defter Sermayesi'nin P/BV'ye üstünlüğü):** Defter sermayesi (borç+özkaynak) NEGATİF ÖZKAYNAKLI firmalarda BİLE genelde POZİTİFTİR — Değer/Defter Sermayesi P/BV'nin aksine örneklem KAYBI yaşamaz; TEK İSTİSNA: nakit defter sermayesini AŞARSA "yatırılan sermaye" (nakit netleştirilmiş) NEGATİF olabilir. (s.396-397)
- **İLKE-200 (FD/Satış vs P/S yapısal farkı):** FD/Satış çoğu firmada P/S'DEN YAPISAL OLARAK YÜKSEKTİR (borç nakitten fazla olduğunda); teknoloji gibi nakit-ağır/düşük-borçlu sektörlerde İSE TERSİ (FD/Satış<P/S) görülür. Piyasa geneli medyan FD/Satış Ocak 2006'da **1,58**'dir. (s.397-398)
- **İLKE-201 (FD çarpanlarının belirleyicileri):** DCF'in temel değişkenleriyle (büyüme, sermaye maliyeti, yeniden yatırım oranı) AYNI mantıkla türetilir; EV/EBIT VE EV/EBIT(1-t) büyüme ARTTIKÇA / sermaye maliyeti AZALDIKÇA / yeniden yatırım oranı AZALDIKÇA (=sermaye getirisi ARTTIKÇA) ARTAR. [→ FORMÜL-92] (s.398-399)
- **İLKE-202 (Amortisman/vergi etkisi — FAVÖK çarpanına):** AYNI büyüme/risk/yeniden-yatırım koşullarında YÜKSEK amortismanlı firmalar DAHA DÜŞÜK FAVÖK çarpanında işlem GÖRMELİDİR; YÜKSEK vergi oranlı firmalar da DAHA DÜŞÜK FAVÖK/FVÖK (VERGİ ÖNCESİ ölçü) çarpanında işlem GÖRMELİDİR — bu etki VERGİ SONRASI ölçülerden (EV/EBIT(1-t)) DAHA BÜYÜKTÜR. [→ BAYRAK-31] (s.399-400)
- **İLKE-203 (FD/Defter Sermayesi'nin belirleyicisi):** FAZLA GETİRİ (ROC − sermaye maliyeti) VE büyüme; fazla getiri POZİTİFSE çarpan 1'İN ÜSTÜNDE, NEGATİFSE 1'İN ALTINDA olmalıdır — P/BV'deki ROE-ke ilişkisiyle (Kısım 4 İLKE-180) BİREBİR PARALEL. (s.400-401)
- **İLKE-204:** FD/Satış'ın belirleyicisi büyüme + sermaye maliyeti (TERS yönlü) + VERGİ SONRASI faaliyet marjıdır — P/S'nin net marj belirleyicisiyle (Kısım 4 İLKE-181) PARALELDİR. (s.401)
- **İLKE-205:** Yüksek büyüme (iki aşamalı) firma değeri çarpanları AYNI belirleyicilere sahiptir, SADECE girdiler İKİ dönem (yüksek büyüme+istikrarlı) için AYRI tahmin edilir — Kısım 4'teki (Ch.8) yaklaşımla PARALEL. (s.401-403)
- **İLKE-206 (Büyüme etkisi, somut örnek):** TÜM FD çarpanları büyümeyle ARTAR (İllüstrasyon 9.2: FD/FAVÖK, g=%0'da **4,7**'den g=%20'de **11,13**'e çıkar); büyüme farkını KONTROL ETMEDEN sektör-içi FD çarpanı kıyası DÜŞÜK-büyüme firmaları "ucuz", YÜKSEK-büyüme firmaları "pahalı" gösterme yanlılığı taşır — büyüme SÜRESİ etkisi de (Kısım 4 İLKE-178'deki gibi) AYNI yönde çalışır. (s.403-404)
- **İLKE-207 (Risk etkisi, 2 kanaldan):** Risk hem cost of equity HEM cost of debt ÜZERİNDEN cost of capital'ı etkiler; olgun/düşük-riskli firmalar DÜŞÜK maliyetle borçlanıp DÜŞÜK cost of capital elde eder, riskli firmalar HEM yüksek cost of equity HEM yüksek cost of debt taşır (İllüstrasyon 9.2: kc=%6'da FD/FAVÖK=**23x**, kc=%15'te=**3,5x**). 3 sonuç: (1) riskli işkolundaki firmalar (AYNI sektörde bile) DAHA DÜŞÜK FD çarpanında işlem görmeli; (2) optimal kaldıraçtan SAPMA cost of capital'ı DOLAYLI etkiler; (3) gelişmekte olan piyasa firmaları gelişmiş piyasa emsallerine göre DAHA YÜKSEK cost of capital nedeniyle DAHA DÜŞÜK FD çarpanında işlem görmelidir (OTOMATİK "ucuz" DEĞİLDİR). (s.404-405)
- **İLKE-208 (Yatırım kalitesi etkisi):** Sermaye getirisi (ROC) ARTTIKÇA (aynı büyüme için gereken yeniden yatırım AZALDIĞINDAN) TÜM FD çarpanları ARTAR; FD/Yatırılan-Sermaye ÖZELLİKLE FAZLA GETİRİYE (ROC-kc) duyarlıdır — fazla getiri pozitifse çarpan>1, negatifse çarpan<1. (s.405-408)
- **İLKE-209 (Vergi oranı etkisi, orantısız büyüklük):** Vergi oranı ARTTIKÇA TÜM FD çarpanları AZALIR, ama VERGİ-ÖNCESİ ölçülerdeki (FAVÖK, FVÖK) etki VERGİ-SONRASI ölçüden (EBIT(1-t)) ORANTISIZ BÜYÜKTÜR (somut örnek: vergi %20→%40 iken FD/FAVÖK **11,52→7,04** [-%39], FD/EBIT(1-t) **17,29→14,09** [-%18,5]) — yüksek vergi oranlı ülkelerdeki firmalar (Almanya >%38 vs İrlanda %12) VERGİ-ÖNCESİ çarpanlarda SİSTEMATİK OLARAK ucuz görünür, bu YANILTICIDIR. [→ BAYRAK-31] (s.408-409)
- **İLKE-210 (Sektör içi kıyasın 3 yolu — Ch.7 ile paralel):** Sübjektif değerlendirme; MATRİS yaklaşımı (çarpanı companion değişkene karşı ÇİZEREK dört bölgeye ayırma — sağ-alt=ucuz [yüksek fazla getiri+düşük çarpan], sol-üst=pahalı); regresyon. (s.410-411)
- **İLKE-211 (FD regresyonlarının R² üstünlüğü):** FD/faaliyet-kârı regresyonlarının R²'si, GENELDE özkaynak kazanç çarpanı (P/E) regresyonlarından DAHA YÜKSEKTİR — faaliyet temellerinin (kazanç kalitesi/muhasebe farklılıklarından bağımsız) çarpanları açıklama gücü DAHA BÜYÜKTÜR. (s.416)
- **İLKE-212 (FD/Sermaye vs P/BV seçim kriteri):** YÜKSEK/DEĞİŞKEN kaldıraçlı firmalarda FD/Sermaye (+eşlik eden ROC) DAHA İSTİKRARLI VE GÜVENİLİR bir görece değer ölçüsü sunar (P/BV'nin ROE'si kaldıraçla YAPAY OLARAK ŞİŞER/ÇÖKER); FD/Sermaye AYRICA negatif özkaynaklı firmalarda BİLE hesaplanabilir (İLKE-199 ile bağlantılı). (s.417)
- **İLKE-213 (İleri/forward çarpanlar):** GENÇ (bugün az gelir, hızlı büyüyen) VE SIKINTILI (bugün zarar eden) firmalarda BUGÜNKÜ rakamlar yerine GELECEKTEKİ (örn. 5 yıl sonraki) rakamlara dayalı çarpan kullanmak DAHA ANLAMLI OLABİLİR — 3 yöntem: (a) karşılaştırılabilir firmaların BUGÜNKÜ ortalama çarpanını gelecekteki değere uygulayıp BUGÜNE İskonto etmek; (b) karşılaştırılabilir firmaların KENDİ gelecekteki gelirine göre hesaplanmış BUGÜNKÜ-değer/gelecek-gelir çarpanını kullanmak; (c) regresyonla marj/büyüme/risk FARKLARINI da düzeltmek. (s.418-420)
- **İLKE-214 (İleri çarpan kullanımının 3 tuzağı):** (1) BEKLENEN (olasılıkla ağırlıklı) değerler kullanılmalı, EN İYİ SENARYO DEĞİL (başarısızlık olasılığı hesaba katılmalı); (2) ÇİFTE BÜYÜME SAYIMINDAN KAÇINILMALI (gelecekteki değer ZATEN büyümeyi yansıtıyorsa, AYRICA yüksek-büyüme gerekçesiyle şişirilmiş bir çarpan kullanmak çifte sayımdır); (3) BUGÜNE İNDİRGENMELİ (gelecek değer UYGUN bir iskonto oranıyla bugüne çevrilmeli) — girişim sermayecilerinin "çıkış çarpanı" yöntemi (tipik hedef getiri %25-35, başarısızlık olasılığını YANSITAN) bu 3 kuralın BİR VARYANTIDIR. [→ FORMÜL-99] (s.420)

**Chapter 10 — Cash, Cross Holdings, and Other Assets:**

- **İLKE-215 (Nakit tutma nedenleri):** Keynes'in 3 bireysel motifinin (işlem, ihtiyat, spekülasyon) kurumsal genişletmesi + 1 ek: İŞLEM/OPERASYONEL motif (nakit-yoğun vs kredi-yoğun iş, küçük-çok/büyük-az işlem, bankacılık sistemi gelişmişliği); İHTİYAT motifi (ekonomi/faaliyet oynaklığı, rekabet yoğunluğu, finansal kaldıraç); GELECEKTEKİ SERMAYE YATIRIMI motifi (yatırım ihtiyacının büyüklüğü/belirsizliği, sermaye piyasasına erişim, yatırımlar hakkında bilgi asimetrisi — Ar-Ge yoğun firmalar DAHA FAZLA nakit tutar); STRATEJİK motif (fırsatçı kullanım, özellikle sermaye piyasası KAPALI gelişmekte olan piyasalarda DEĞERLİ); YÖNETİM ÇIKARLARI (zayıf kurumsal yönetim/yüksek içeriden pay sahipliği → "imparatorluk kurma" güdüsüyle nakit biriktirme — nakit biriktiren firmalar ORTALAMADA daha ZAYIF faaliyet performansı raporlar). (s.425-429)
- **İLKE-216 (Nakit tutarının 3 ölçeği):** Firma değerinin yüzdesi, defter varlık değerinin yüzdesi, hasılatın yüzdesi olarak ölçülebilir — HER ÜÇÜ de sektörler arası BÜYÜK farklılık gösterir. (s.429-431)
- **İLKE-217 (Nakit sınıflandırmasının 2 çerçevesi):** (a) YAYGIN ama ZAYIF çerçeve — FAALİYET nakdi vs FAZLA (excess) nakit (3 tahmin yöntemi: kural-of-thumb [%2 hasılat], sektör ortalaması, cross-sectional regresyon); (b) DAHA DOĞRU çerçeve — İSRAF EDİLEN (piyasa-altı getirili) vs İSRAF EDİLMEYEN (adil piyasa getirili) nakit — DEĞERLEME açısından anlamlı olan ayrım BUDUR, çünkü adil getirili nakit SIFIR NPV yatırımıdır (değeri etkilemez); faaliyet/fazla ayrımı DEĞER açısından ANLAMSIZDIR. (s.431-433)
- **İLKE-218 (DCF'te nakdin ele alınışı — konsolide vs ayrı):** KONSOLİDE (nakit dahil TEK model) yaklaşım 2 ZORLUK taşır: (1) sermaye maliyeti/beta SÜREKLİ nakit AĞIRLIĞINA göre yeniden ayarlanmalı (nakdin betası SIFIR kabul edilir, ağırlıklı ortalama unlevered beta gerekir); (2) firma büyüdükçe faaliyet/nakit gelir oranı DEĞİŞTİĞİNDEN girdiler SÜREKLİ güncellenmeli. AYRI değerleme (nakdi faaliyet varlıklarından AYIRIP AYRI değerlemek, SONRA toplamak) DAHA GÜVENİLİRDİR — İKİ hata riskini azaltır: ÇİFTE SAYIM (nakit gelirini nakit akışına dahil edip AYRICA nakdi geri eklemek) ve YANLIŞ SAYIM (nakit gelirine YANLIŞ [riskli] iskonto oranı uygulamak). [→ KONTROL LİSTESİ W] (s.433-436)
- **İLKE-219 (Konsolide yaklaşımın somut hata büyüklüğü):** Riskiz nakit gelirini faaliyet varlıklarına uygun YÜKSEK bir iskonto oranıyla (örn. %11) iskonto etmek 1 milyar dolarlık nakdi 800 milyon dolara İNDİRGER — İllüstrasyon 10.1'de DOĞRU değer $1.400mn iken HATALI konsolide yaklaşım $1.290mn verir ($110mn KAYIP; nakit $200mn yerine $90mn değerlenir). (s.436-437)
- **İLKE-220 (Brüt borç vs net borç yaklaşımı):** İKİ yaklaşım FARKLI özkaynak değeri ÜRETEBİLİR çünkü nakdi finanse eden VARSAYILAN kaynak farklıdır (brüt: nakit+borç AYNI oranda finanse edilir; net: nakit TAMAMEN riskiz borçla finanse edilmiş SAYILIR) — bu, sermaye maliyetinde kullanılan vergi-öncesi borç maliyetini VE vergi avantajını FARKLI etkiler; fark VERGİ ORANI VE TEMERRÜT RİSKİ arttıkça BÜYÜR. Yazarın TERCİHİ: BRÜT borç yaklaşımı + nakdi AYRI varlık olarak tutmak. [→ FORMÜL-101] (s.437-443)
- **İLKE-221 (Nakdin iskontolandığı 2 durum):** Genel kural: nakit 1 dolar=1 dolar değerindedir, prim/iskonto uygulanmaz. İSTİSNA 2 durumda: (1) nakit PİYASA-ALTI getiriyle yatırılmışsa (küçük işletme/bazı gelişmekte olan piyasa erişim kısıtları); (2) YÖNETİME GÜVENSİZLİK varsa (geçmişte kötü yatırım/satın alma kaydı olan yönetim, büyük nakit bakiyesini KÖTÜ yatırımlara/devralmalara HARCAMA olasılığını ARTIRIR — piyasa BUNU ÖNCEDEN İskontolar; iskonto en BÜYÜK, az yatırım fırsatı+kötü yönetimli firmalarda, en KÜÇÜK/YOK, çok fırsat+iyi yönetimli firmalarda GÖRÜLÜR). [→ KONTROL LİSTESİ X] (s.443-445)
- **İLKE-222 (Ampirik nakit değerleme kanıtı):** Piyasanın nakde biçtiği değer FARKLI ÇALIŞMALARDA farklı bulunmuştur — Pinkowitz&Williamson (2002): ~yüzdeğerinde (büyük std hatayla, büyüme firmalarında DAHA YÜKSEK); zayıf-pay-sahibi-korumalı gelişmekte olan piyasalarda $0,65/$1; Schwetzler&Reimund (2004, Almanya): medyan-üstü nakit tutan firmalar DAHA YÜKSEK değerlenir; Faulkender&Wang (2004): marjinal nakit değeri $0,96 (nakit VE borç ARTTIKÇA marjinal değer AZALIR; temettü-ödeyen firmalarda DAHA DÜŞÜK [vergi dezavantajı]; sermaye-kısıtlı/yüksek-yatırım-fırsatlı firmalarda DAHA YÜKSEK). Japonya'da medyan nakit tutarı Almanya/ABD medyanının **2,5 katı** (banka gücü hipotezi). (s.449-451)
- **İLKE-223 (Göreli değerlemede nakit sorunu — özkaynak çarpanları):** Nakit VE faaliyet varlıkları FARKLI getiri/risk profiline sahip olduğundan, P/E ORANI nakit bakiyesinin BÜYÜKLÜĞÜNÜN bir FONKSİYONU haline gelir; DÜŞÜK/ORTA büyümeli sektörlerde YÜKSEK nakitli firmalar DAHA YÜKSEK P/E'de işlem görür (nakit RİSKSİZ olduğundan DAHA YÜKSEK çarpanı hak eder) ama bu OTOMATİK "pahalı" DEMEK DEĞİLDİR; YÜKSEK büyümeli sektörlerde İSE faaliyet varlığının çarpanı nakit çarpanını AŞTIĞINDA, yüksek nakit DÜŞÜK P/E'ye yol açar. ÇÖZÜM: nakit-hariç özkaynak/nakit-hariç kazançla hesaplanan P/E kullanmak. [→ BAYRAK-34] (s.446-447)
- **İLKE-224 (P/BV'de paralel sorun):** Nakit genelde DEFTER değerine YAKIN işlem görür (P/BV≈1), faaliyet varlıkları İSE DEFTER değerinden ÖNEMLİ ÖLÇÜDE SAPABİLİR; nakit AĞIRLIĞI arttıkça firma P/BV'si "1"E doğru ÇEKİLİR — ÇÖZÜM AYNIDIR: hem piyasa hem defter değerinden nakdi NETLEŞTİRMEK. (s.447-448)
- **İLKE-225 (FD çarpanlarında nakit — 2 dikkat noktası):** FD çarpanlarında nakit sorunu DAHA AZ (analistler genelde nakdi ZATEN netleştiriyor) ama 2 dikkat noktası VAR: (1) MEVSİMSEL nakit dalgalanması — yıl-sonu bakiyesi yerine YIL ORTALAMASI kullanılmalı, aksi halde YAPAY OLARAK düşük FD çarpanı ("ucuz" yanılgısı) oluşabilir; (2) FD/Sermaye hesabında nakit HEM piyasa HEM defter tarafında netleştirilmeli. [→ BAYRAK-33] (s.448-449)
- **İLKE-226 (Elden çıkarma/divestiture tuzağı):** Yıl SONUNDA yapılan bir varlık satışı, faaliyet varlıklarını BÜYÜK bir nakit bakiyesiyle DEĞİŞTİRİR ama geçmiş dönem FAVÖK/faaliyet kârı HALA satılan varlığın kazancını İÇERİR — bu, çarpanı YAPAY OLARAK DÜŞÜK gösterir; çözüm: satılan varlığın kazanç KATKISINI ÇIKARMAK VEYA bu katkıyı İÇERMEYEN ileriye dönük bir rakam kullanmak. [→ BAYRAK-33] (s.449)
- **İLKE-227 (Finansal yatırım tutma nedenleri):** DAHA YÜKSEK GETİRİ arayışı (ama ADİL-riskli getiri DEĞER-NÖTRDÜR, DAHA DEĞERLİ YAPMAZ); DEĞERSİZ (undervalued) menkul kıymet ARAYIŞI (POZİTİF NPV — Berkshire Hathaway örneği: 1999 2Ç'de $69 milyar finansal yatırım, $12,4mlr Coca-Cola dahil); STRATEJİK yatırım (Microsoft'un 1990'larda 14+ firmaya yaptığı stratejik yatırımlar — ürün/servis etkisi + rakip ittifaklarını ÖNLEME); İŞ GEREĞİ yatırımlar (banka/sigorta şirketlerinde HAMMADDE niteliğinde, DİĞER kategorilerle KIYASLANAMAZ). (s.451-454)
- **İLKE-228 (Menkul kıymet değerleme yöntemleri):** 3 seçenek: (a) GÜNCEL piyasa değerini DOĞRUDAN eklemek (BASİT, ÇOK sayıda holding'de PRATİK — Microsoft örneği: $23,798mlr nakit+kısa vadeli yatırım + $17,726mlr riskli menkul kıymet TOPLAM operasyonel varlık değerine EKLENİR); (b) sermaye kazancı vergisini NETLEŞTİRİLMİŞ piyasa değeri (TASFİYE bazlı değerleme için EN UYGUN); (c) ihraç eden firmanın KENDİSİNİ değerleyip payı türetmek (EN ZOR, AZ ama BÜYÜK holding'lerde EN UYGUN). (s.454-457)
- **İLKE-229 (Menkul kıymet primi/iskontosu):** GENEL KURAL: prim/iskonto EKLENMEMELİDİR (piyasa değeri OLDUĞU GİBİ eklenir). İSTİSNA: kapalı-uçlu YATIRIM FONLARI gibi "finansal varlık alıp satmayı İŞ MODELİ" edinen firmalar — bunlarda TUTARLI FAZLA/EKSİK GETİRİ varsa (net varlık değerine göre) prim/iskonto UYGULANABİLİR (İllüstrasyon 10.6: Pierce Regan Asia fonu, beklenen yıllık -%2 az-performans → net varlıklara göre **%16,67** İSKONTO, sonsuza dek devam varsayımıyla). [→ FORMÜL-103] (s.456-457)
- **İLKE-230 (Çapraz iştirak muhasebe kategorileri):** AZINLIK PASİF (<%20 sahiplik): defter DEĞERİ (elde-tutulacak), PİYASA değeri (satışa hazır — kazanç/kayıp ÖZKAYNAKTA, gelir tablosunda DEĞİL), PİYASA değeri (ticaret amaçlı — kazanç/kayıp GELİR TABLOSUNDA); AZINLIK AKTİF (%20-50): ÖZKAYNAK YÖNTEMİ (orantılı net kâr/zararla MALİYET ayarlanır, temettü MALİYETİ AZALTIR, piyasa değeri SADECE elden çıkarmada dikkate alınır); ÇOĞUNLUK AKTİF (>%50): TAM KONSOLİDASYON (iştirakin TÜM varlık/yükümlülükleri birleştirilir, dışarıdaki payın DEFTER değeri "azınlık payı" olarak pasifte GÖSTERİLİR). (s.457-459)
- **İLKE-231 (DCF'te çapraz iştirak):** EN DOĞRU yöntem HER holding'i AYRI değerleyip ORANTISAL payı ANA ŞİRKETİN özkaynağına EKLEMEKTİR (konsolide gelir tablosu kullanılıyorsa ÖNCE iştirakin gelir/varlık/borcu ANA ŞİRKETTEN AYRIŞTIRILMALI, aksi halde ÇİFT SAYIM oluşur); konsolide FİRMAYI TEK MODEL olarak değerlemek YANLIŞ SONUÇ verebilir çünkü ana şirket ve iştirakler FARKLI sermaye maliyeti/büyüme/yeniden yatırım PROFİLİNE sahip olabilir. (s.459-460)
- **İLKE-232 (Tam bilgi ortamında 3 adım):** (1) çoğunluk iştirak varsa ANA ŞİRKETİ AYRIŞTIRIP standalone değerle; (2) HER iştiraki BAĞIMSIZ firma gibi (kendi risk/büyüme/nakit akışı VARSAYIMLARIYLA) değerle; (3) HER iştirakin ORANTISAL özkaynak payını ANA ŞİRKETİN özkaynağına EKLE. [→ KONTROL LİSTESİ V] (s.460-461)
- **İLKE-233 (Kısmi bilgi ortamında pratik alternatifler):** Halka açık iştirakler için PİYASA DEĞERİNİ KULLAN (piyasa hatasını DEVRALMA riski taşır ama zaman-verimlidir); özel iştirakler için SEKTÖR DEFTER-DEĞERİ ÇARPANINI iştirakin defter değerine UYGULA (SON ÇARE olarak SADECE muhasebesel maliyet DEĞERİNİ kullanmaktan İYİDİR). (s.464-465)
- **İLKE-234 (Göreli değerlemede çapraz iştirak — özkaynak çarpanları):** AZINLIK PASİF holding'lerde SADECE temettü gelir tablosuna GİRDİĞİNDEN (çoğu firma kazancından AZ temettü dağıttığından) P/E SİSTEMATİK OLARAK YUKARI YANLAR (piyasa değeri holding'i YANSITIR ama net kâr YANSITMAZ); AZINLIK AKTİF/ÇOĞUNLUK holding'lerde İSE net kâr orantısal payı YANSITTIĞINDAN sorun AZDIR ama KARŞILAŞTIRILABİLİR FİRMA bulma ZORLAŞIR (iştirak BÜYÜK VE farklı temellere sahipse). (s.465)
- **İLKE-235 (Göreli değerlemede çapraz iştirak — FD çarpanları):** AZINLIK holding'lerde faaliyet ölçüleri (hasılat/FVÖK/FAVÖK) İŞTİRAKİ YANSITMAZ ama piyasa değeri (özkaynak fiyatı ÜZERİNDEN) YANSITIR → FD çarpanları YUKARI YANLAR; ÇOĞUNLUK holding'lerde (TAM konsolidasyon) TERS problem oluşur — payda (FAVÖK) İŞTİRAKİN %100'ÜNÜ İÇERİR ama pay (özkaynak değeri) SADECE sahip olunan %'Yİ yansıtır; "AZINLIK PAYINI (defter değeri) FD'ye EKLEMEK" YAYGIN ama YANLIŞ düzeltmedir (defter değeri≠piyasa değeri) — DOĞRU düzeltme azınlığın PİYASA DEĞERİNİ eklemek VEYA (DAHA temiz) SADECE ana şirketin (iştiraksiz) FD/FAVÖK'ünü hesaplamaktır. [→ BAYRAK-28] (s.465-467)
- **İLKE-236 (Diğer faaliyet-dışı varlıklar):** KULLANILMAYAN varlıklar (nakit akışı ÜRETMEYEN ama piyasa değeri OLAN, örn. gelişmemiş arazi) DCF'TE SİSTEMATİK OLARAK GÖZ ARDI EDİLİR (bilinçli envanter+ayrı değerleme gerektirir, bilgi AÇIĞI en büyük ENGELDİR); FAZLA FONLU EMEKLİLİK PLANLARI için muhafazakâr kural: geri alım maliyeti/vergisi ÇOK YÜKSEK varsayılır (dokunulmaz); ALTERNATİF: vergi-sonrası fazlayı EKLEMEK (örn. %50 vergi→fazlanın YARISINI ekle) VEYA GELECEKTEKİ katkı payı AZALIŞINI nakit akışına YANSITMAK (DAHA PRATİK); ORTAK GİRİŞİM yatırımları muhasebe yöntemine (özkaynak/orantısal-konsolidasyon/tam-konsolidasyon) göre çapraz-iştirak MANTIĞIYLA AYNI şekilde ele alınmalıdır. (s.467-469)

---

## Formüller (devam)

- **FORMÜL-88 — Firma Değeri / Enterprise Value (Temel Tanım)**
  - Formül: `Firma Değeri = Piyasa Değeri Özkaynak + Piyasa Değeri Borç`; `Enterprise Value = Firma Değeri - Nakit ve Benzerleri (İsraf Edilmeyen)`
  - QuaxisLabs karşılığı: `calculator.ValuationMetrics.enterprise_value` (`market_cap + net_debt`) MEVCUT — israf edilen/edilmeyen nakit AYRIMI yapılmıyor (TÜM nakit netleştiriliyor, kabul edilebilir bir basitleştirme).

- **FORMÜL-89 — Azınlık Paylı Konsolide Değer (Tam Formül)**
  - Formül: `Konsolide Değer = Ana Şirket FD + Σ πj×(Net Borç_j) [azınlık payları] + Σ (Özkaynak Değeri_k) [çoğunluk payları]`
  - Değişkenler: `πj`=azınlık holding'deki sahiplik oranı, `j`=azınlık holdingler, `k`=çoğunluk (tam konsolide) holdingler.
  - QuaxisLabs karşılığı: **UYGULANMIYOR** — bkz. BAYRAK-28, en önemli kod-seviyesi bulgu bu Kısımda.

- **FORMÜL-90 — İştiraksiz (Parent-Only) Firma Değeri**
  - Formül: `İştiraksiz FD = Konsolide FD - Σ(Azınlık Holding Piyasa Değeri) - Σ(Çoğunluk Holding Piyasa Değeri + Konsolide Borç_k - Konsolide Nakit_k)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çapraz iştirak (bağlı ortaklık/iştirak) listesi VE her birinin piyasa değeri hiçbir fetcher'da YOK; bu, BIST holding yapılarının (Koç, Sabancı, Doğuş gibi çok-iştirakli gruplar) DOĞRU değerlenmesi için YAPISAL bir eksikliktir.

- **FORMÜL-91 — Değer/Defter Sermayesi (Nakit Dahil/Hariç)**
  - Formül: `Değer/Defter Sermayesi = Firma Değeri / (Özkaynak Defter Değeri + Borç Defter Değeri)`; `Enterprise Value/Yatırılan Sermaye = Enterprise Value / (Özkaynak+Borç Defter Değeri - Nakit)`
  - QuaxisLabs karşılığı: `equity` VE `financial_debt` MEVCUT (basit toplamla Değer/Defter Sermayesi TÜRETİLEBİLİR, DÜŞÜK maliyetli); "Yatırılan Sermaye" (nakit netleştirilmiş) standalone alan olarak `calculator.py`'de YOK ama `net_debt()` mantığıyla PARALEL türetilebilir.

- **FORMÜL-92 — EV/EBIT ve EV/EBIT(1-t), Sabit Büyüme**
  - Formül: `EV/EBIT = (1-RIR)×(1+g)/(kc-g)`; `EV/[EBIT×(1-t)] = (1-RIR)×(1+g)/(kc-g)` (RIR=yeniden yatırım oranı, t=vergi oranı)
  - QuaxisLabs karşılığı: `ttm_operating_profit` MEVCUT; `RIR` (Capex eksikliğine bağlı) VE `kc` (WACC, Kısım 1 FORMÜL-21) **VERİ EKSİK**.

- **FORMÜL-93 — EV/FAVÖK, Sabit Büyüme (Amortisman Düzeltmeli)**
  - Formül: `EV/FAVÖK = [(1-RIR)×(1+g) - (Amortisman/FVÖK)×((1+g)-RIR×(1+g))] / (kc-g)` (basitleştirilmiş form; amortisman payı çarpanı AŞAĞI çeker)
  - QuaxisLabs karşılığı: `ttm_ebitda` MEVCUT; RIR/kc AYNI eksiklikler.

- **FORMÜL-94 — FD/Defter Sermayesi = f(Fazla Getiri, Büyüme)**
  - Formül: `FD/Defter Sermayesi = 1 + [(ROC-kc)×(1+g)] / [(kc-g)×(kc bazlı katsayı)]` (fazla getiri pozitifse çarpan>1)
  - QuaxisLabs karşılığı: `fundamental_screens.py::return_on_capital_pct` (Greenblatt ROC) YAKLAŞIK bir başlangıç noktası; `kc` **VERİ EKSİK**.

- **FORMÜL-95 — FD/Satış, Sabit Büyüme**
  - Formül: `FD/Satış = [Vergi-Sonrası Faaliyet Marjı × (1-RIR) × (1+g)] / (kc-g)`
  - QuaxisLabs karşılığı: `net_margin_current` (net kâr marjı) ANALOG olarak var ama VERGİ-SONRASI FAALİYET marjı (`ttm_operating_profit×(1-t)/revenue`) standalone HESAPLANMIYOR — `ttm_operating_profit` ve `ttm_revenue` MEVCUT, `t` (efektif vergi oranı) **VERİ EKSİK** (`income_before_tax`/`tax_provision`, kitaplar arası tekrar eden açık).

- **FORMÜL-96 — Yüksek Büyüme (2 Aşamalı) FD Çarpanları**
  - Formül: yüksek büyüme dönemi (RIR_hg, g_hg, kc_hg) + istikrarlı dönem (RIR_st, gn, kc_st) parametreleriyle EV/FAVÖK, EV/FVÖK, FD/Sermaye, FD/Satış TÜRETİLİR (İllüstrasyon 9.2 somut örneği: ROC %15, ilk-5-yıl reinvestment %60→g=%9, istikrarlı reinvestment %26,67→g=%4, kc=%10).
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çok dönemli büyüme/yeniden yatırım projeksiyonu YOK (Kısım 1-4'te tekrar tespit edilen AYNI yapısal eksiklik).

- **FORMÜL-97 — Sektör/Piyasa Regresyonu (FD Çarpanları)**
  - Formül: `FD Çarpanı = a + b1×büyüme + b2×vergi oranı + b3×yeniden yatırım oranı (+ROC/faiz karşılama oranı)`
  - QuaxisLabs karşılığı: **YAPISAL OLARAK UYGULANAMAZ** — Kısım 4 FORMÜL-82'deki AYNI mimari eksiklik (çok-firma cross-sectional istatistik altyapısı YOK).

- **FORMÜL-98 — İleri (Forward) Çarpan, 3 Yöntem**
  - Formül: (a) `Değer_bugün = [Ortalama Çarpan_bugün × Gelecek-Yıl-n Rakamı] / (1+r)^n`; (b) benzer ama karşılaştırılabilir firmaların KENDİ gelecek rakamına göre hesaplanmış çarpan; (c) regresyon-düzeltilmiş versiyon.
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çok yıllı ileri projeksiyon (gelir/kâr tahmini) YOK.

- **FORMÜL-99 — Girişim Sermayesi Çıkış Çarpanı Yöntemi**
  - Formül: `Bugünkü Değer = [Çıkış Yılı Kazancı × Çıkış Çarpanı] / (1+Hedef Getiri)^n` (Hedef Getiri tipik %25-35)
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — QuaxisLabs halka açık BIST/NASDAQ/Crypto varlıklarını analiz eder; girişim sermayesi/özel şirket değerleme senaryosu ürün kapsamı DIŞINDA.

- **FORMÜL-100 — Nakit-Hariç (Net Operating) P/E ve P/BV**
  - Formül: `Nakit-Hariç P/E = (Piyasa Değeri Özkaynak - Nakit) / (Net Kâr - Nakit-Sonrası Faiz Geliri)`; `Nakit-Hariç P/BV = (Piyasa Değeri - Nakit) / (Defter Değeri - Nakit)`
  - QuaxisLabs karşılığı: Kısım 4 FORMÜL-86 ile AYNI (tekrar referans) — `cash`, `market_cap`, `equity` MEVCUT, DÜŞÜK maliyetli.

- **FORMÜL-101 — Brüt Borç vs Net Borç Yaklaşımı (Sermaye Maliyeti Ayrışması)**
  - Formül: net borç yaklaşımında nakti finanse eden borç RİSKİZ kabul edilir, KALAN borcun (operasyonel varlıkları finanse eden) vergi-öncesi maliyeti YUKARI AYARLANIR: `Kalan Borç Maliyeti = (Toplam Faiz - Nakit×Riskiz Oran) / (Toplam Borç - Nakit)`
  - QuaxisLabs karşılığı: `calculator._net_debt()` (`financial_debt - cash - financial_investments`) NET BORÇ yaklaşımını KULLANIYOR — kitap yazarının TERCİHİ (BRÜT borç + ayrı nakit) İLE FARKLI metodolojik seçim; WACC hiç hesaplanmadığından bu fark şu an PRATİK SONUÇ DOĞURMUYOR ama WACC eklenirse (Kısım 1 FORMÜL-21) BELGELENMELİDİR.

- **FORMÜL-102 — Nakit İskonto (Piyasa-Altı Getiri)**
  - Formül: `Nakit Değeri = Nakit Geliri / Piyasa Faiz Oranı` (gerçekleşen düşük getiri, adil getiri yerine kullanılır)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — nakit faiz geliri standalone alan olarak YOK (gelir tablosunda ayrıştırılmamış); piyasa faiz oranı proxy'si (`valuation.py::_RISK_FREE_RATE_PCT`) MEVCUT.

- **FORMÜL-103 — Kapalı-Uçlu Fon İskonto/Primi**
  - Formül: `İskonto% ≈ (Piyasa Getirisi - Beklenen Fon Getirisi) / (Sermaye Maliyeti - Piyasa Getirisi)` (sonsuz devam varsayımlı basitleştirilmiş form)
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — QuaxisLabs hisse senedi analiz motorudur; `src/fetchers/tefas.py` (TEFAS fon verisi) fetcher'ı VAR ama bu formülle DOĞRUDAN entegre DEĞİL — kapalı-uçlu fon/yatırım ortaklığı değerlemesi ayrı bir ürün kapsamı sorusu olarak İŞARETLENDİ.

- **FORMÜL-104 — Fazla Fonlu Emeklilik Planı Değer Katkısı**
  - Formül: `Değer Katkısı = (1 - Vergi Oranı) × (Emeklilik Varlığı - Emeklilik Yükümlülüğü)`
  - QuaxisLabs karşılığı: **VERİ EKSİK/DÜŞÜK ÖNCELİK** — Türkiye'de ABD-tarzı tanımlı-fayda emeklilik planı verisi hiçbir fetcher'da YOK (kıdem tazminatı karşılığı benzer ama farklı bir muhasebe kavramıdır); BIST evreninde pratik önemi DÜŞÜK.

---

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| "FD/FAVÖK<7x=ucuz" kuralı, ABD evreni | **~1.500 firma** bu eşiğin ALTINDA (Ocak 2006) | Sabit eşik kuralının anlamsızlığının somut kanıtı | Ch.9, s.395-396 |
| Değer/Defter Sermayesi vs EV/Yatırılan Sermaye medyanı (Ocak 2006) | **1,83** vs **2,06** | İkisi de aynı dönemki P/BV medyanından (Kısım 4: 2,32) DÜŞÜK | Ch.9, s.396-397 |
| EV/Satış medyanı, piyasa geneli (Ocak 2006) | **1,58** (üst desil >15, alt desil <0,25) | FD/Satış'ın P/S'den yapısal olarak YÜKSEK olma eğilimi | Ch.9, s.397-398 |
| Büyümenin FD/FAVÖK'e etkisi (İllüstrasyon 9.2, g:%0→%20) | **4,7x → 11,13x** | Büyüme etkisinin büyüklüğü | Ch.9, Tablo 9.4 |
| Sermaye maliyetinin FD/FAVÖK'e etkisi (aynı örnek, kc:%6→%15) | **23x → 3,5x** | Risk etkisinin büyüklüğü, büyüme etkisiyle KIYASLANABİLİR | Ch.9, Tablo 9.5 |
| Vergi oranının FD çarpanlarına ORANTISIZ etkisi (%20→%40) | FD/FAVÖK **11,52→7,04** (-%39) vs FD/EBIT(1-t) **17,29→14,09** (-%18,5) | Vergi-öncesi çarpanların vergi farkına DAHA DUYARLI olduğunun kanıtı | Ch.9, Tablo 9.8 |
| Ülkeler arası kurumlar vergisi farkı örneği | Almanya **>%38** vs İrlanda **%12** | Çapraz ülke FD/FAVÖK kıyasının vergi kontrolü olmadan YANILTICI olacağının somut örneği | Ch.9, s.409 |
| Avrupa kozmetik sektörü — EV/Sermaye~ROC eşiği | Sektör ort. EV/Sermaye **3,52**, ort. ROC **%15,02** | Basit tarama testi: düşük EV/Sermaye + yüksek ROC = ucuz | Ch.9, İllüstrasyon 9.4 |
| Kozmetik sektörü — en yüksek/en düşük ROC | Beiersdorf ROC **%31,17** (EV/Sermaye 8,96) / Jacques Bogart ROC **%2,19** (EV/Sermaye 0,93) | ROC-çarpan ilişkisinin uç noktaları | Ch.9, s.413-414 |
| Kozmetik sektörü — regresyon tahmini sapma | Sarantis **~-%55** (ucuz), Christian Dior **~-%43** (ucuz) | Marj regresyonuyla düzeltilmiş görece değer örneği | Ch.9, s.414 |
| Özel kimyasal sektörü — Yule Catto, basit vs kaldıraç-düzeltmeli regresyon | Basit: **-%12,1** (ucuz) → kaldıraç eklenince: **+%20,5** (pahalı) | Kaldıracı ihmal etmenin sonucu TERSİNE ÇEVİREBİLECEĞİNİN somut kanıtı | Ch.9, İllüstrasyon 9.5 |
| Kaldıraç-düzeltmeli regresyonun R²'si | **%84,68** | Faiz karşılama oranı eklenince açıklama gücünün BÜYÜK artışı | Ch.9, s.416 |
| Piyasa geneli EV/FAVÖK regresyonu (Ocak 2006) | R² **%50,9** | EV/EBIT regresyonlarıyla KIYASLANABİLİR | Ch.9, s.416-417 |
| Piyasa geneli EV/Sermaye~ROC regresyonu | R² **%57,3** | P/BV~ROE (Kısım 4: %55,6) ile KIYASLANABİLİR seviyede | Ch.9, s.417 |
| Piyasa geneli EV/Satış regresyonu | Marj katsayısı **+0,855**/1% | | Ch.9, s.417-418 |
| Nakit/firma değeri medyanı, ABD (Ocak 2005) | **%6,07** (>300 firma >%50) | Nakit yoğunluğunun büyük çeşitliliği | Ch.10, s.429 |
| Nakit/defter varlık medyanı | **%7,14** | | Ch.10, s.429 |
| Nakit/hasılat medyanı | **%3,38** (bazı genç firmalarda >%100) | | Ch.10, s.429 |
| Operasyonel nakit "kural of thumb" | Hasılatın **%2**'si (kaynağı belirsiz) | Kaba/farklılaştırmayan bir kural örneği | Ch.10, s.432 |
| Konsolide yaklaşımda hatalı iskonto (İllüstrasyon 10.1) | Doğru değer **$1.400mn** vs hatalı konsolide **$1.290mn** (-$110mn) | Nakde yanlış iskonto oranı uygulamanın somut zarar büyüklüğü | Ch.10, s.436-437 |
| Piyasa-altı getirili nakit iskontosu (İllüstrasyon 10.3) | Nakit getirisi **%3** vs riskiz **%4,5** → değer **$200mn→$133,33mn** | | Ch.10, s.443-444 |
| Kötü-yönetim iskontosu (İllüstrasyon 10.4) | %30 olasılıkla $50mn fazla ödeme riski → nakit **$200mn→$185mn** | | Ch.10, s.444-445 |
| Ampirik nakit değeri (Faulkender&Wang 2004) | Marjinal **$0,96** / $1 | | Ch.10, s.450 |
| Ampirik nakit değeri, zayıf pay sahibi korumalı gelişmekte olan piyasa | **$0,65** / $1 | | Ch.10, s.450 |
| Japonya vs Almanya/ABD medyan nakit tutarı | **~2,5x** daha fazla | Banka gücü hipotezinin somut kanıtı | Ch.10, s.450 |
| Kapalı-uçlu fon iskonto örneği (Pierce Regan Asia, İllüstrasyon 10.6) | Beklenen -%2/yıl az-performans → **%16,67** iskonto | | Ch.10, s.456-457 |
| Microsoft nakit+menkul kıymet toplamı (Haziran 2000) | Nakit/kısa vadeli **$23,798mlr** + riskli menkul kıymet **$17,726mlr** | Büyük ölçekli finansal yatırım örneği | Ch.10, İllüstrasyon 10.5 |

## Kontrol listeleri (devam)

**Kontrol Listesi U — Firma/FD Değeri Ölçüm Kararları (Ch.9, s.386-390, Kısım 4 Kontrol Listesi S'e 2 EK karar):**
1. Nakit-dahil mi nakit-hariç mi? (`Enterprise Value = Firma Değeri - Nakit`)
2. Çapraz iştirakler nasıl ele alınacak? (azınlık: piyasa değeri payı eklenmeli/borç-nakit orantısal dahil edilmeli VEYA TAMAMEN netleştirilmeli; çoğunluk: azınlık payının PİYASA değeri — DEFTER değeri DEĞİL — dikkate alınmalı)
3. Borca ne dahil edilecek? (faizli borç+kira taahhütleri+diğer potansiyel yükümlülükler; piyasa değeri defter değerine TERCİH edilir)
4. Opsiyonlar dahil mi? (Kısım 4 Kontrol Listesi S ile PARALEL)

**Kontrol Listesi V — Çapraz İştirak Değerlemesinin 3 Adımı, Tam Bilgi Ortamı (Ch.10, s.460-461):**
1. Çoğunluk iştirak varsa ANA ŞİRKETİ AYRIŞTIR, standalone değerle.
2. HER iştiraki (azınlık dahil) BAĞIMSIZ firma gibi kendi varsayımlarıyla değerle.
3. Her iştirakin ORANTISAL özkaynak payını ANA ŞİRKETİN özkaynak değerine EKLE.

**Kontrol Listesi W — Nakit Değerlemesinde Kaçınılması Gereken 2 Hata (Ch.10, Tablo 10.1, s.445-446):**
1. **ÇİFTE SAYIM** — nakit gelirini nakit akışlarına dahil edip AYRICA nakdi sona geri eklemek.
2. **YANLIŞ SAYIM** — nakit gelirine (riskiz) faaliyet varlıklarına uygun (riskli) bir iskonto oranı uygulamak; brüt/net borç yaklaşımlarında borç maliyetini nakit-finansman varsayımına göre AYARLAMAMAK.

**Kontrol Listesi X — Nakdin İskontolanacağı 2 Koşul (Ch.10, s.443-445):**
1. Nakit PİYASA-ALTI getiriyle yatırılmış (küçük işletme/bazı gelişmekte olan piyasa kısıtları).
2. Yönetime GÜVENSİZLİK (geçmiş kötü yatırım/satın alma kaydı → piyasa gelecekteki kötü kullanım olasılığını İskontolar).

## Kırmızı bayraklar (devam)

- **BAYRAK-28 — Azınlık Payı Defter Değerinin Firma Değerine Eklenmesi (Yaygın ama Yanlış Düzeltme):** Çoğunluk iştiraki TAM konsolide eden firmalarda, dışarıdaki payın (azınlık payı) SADECE DEFTER değerini FD'ye eklemek YANLIŞTIR — azınlık payının PİYASA değeri defter değerinden GENELDE FARKLIDIR. Nasıl tespit edilir: FD hesabında "azınlık payı" kalemi kullanılıyorsa DEFTER mi PİYASA değeri mi olduğu kontrol edilmeli. **QuaxisLabs bağlamında EN ÖNEMLİ somut bulgu:** `calculator.compute_valuation()` HİÇBİR azınlık payı düzeltmesi YAPMIYOR — `enterprise_value = market_cap + net_debt` formülünde `market_cap` SADECE ana şirketin (parent-only) piyasa değerini yansıtırken `net_debt` KONSOLİDE bilançodan (çoğunluk iştiraklerin borç/nakdinin %100'ü dahil) geliyor — azınlığın hiçbir piyasa/defter katkısı EKLENMİYOR. Bu, önemli-azınlık-paylı konsolide BIST holding şirketlerinde `enterprise_value`, `ev_ebitda`, `ev_revenue`'yu SİSTEMATİK OLARAK DÜŞÜK gösterir (yapay "ucuz" görünüm). Gereken veri: iştirak listesi + sahiplik oranı + iştirak piyasa değeri (**VERİ EKSİK**). (Ch.9-10, s.387-389, 465-467)
- **BAYRAK-29 — Özkaynak Piyasa/Defter Değeri Kapsam Uyuşmazlığı (P/BV'de Azınlık Kirliliği):** Pay (piyasa değeri) SADECE ana şirket hissedarlarının payını yansıtırken payda (defter değeri) AZINLIK PAYINI DA içeren "toplam özkaynak" olduğunda P/BV YAPAY OLARAK DÜŞÜK çıkar. Nasıl tespit edilir: P/BV'nin payı/paydası AYNI sahiplik KAPSAMINI mı yansıtıyor kontrol et. **QuaxisLabs bağlamında somut bulgu:** `calculator.ValuationMetrics.pb_ratio = market_cap / equity_current` — `equity` alanı `isyatirim.py`'de AÇIKÇA "Özkaynaklar (toplam, **azınlık payı dahil**)" olarak tanımlı (kod "2N") — TAM OLARAK bu bayrağın tarif ettiği kapsam uyuşmazlığı. Önemli azınlık paylı şirketlerde `pb_ratio` SİSTEMATİK OLARAK DÜŞÜK (yanıltıcı ucuz) çıkar. **Kıyaslama notu (pozitif):** `pe_ratio` BU sorunu TAŞIMIYOR çünkü hem `market_cap` HEM `net_income` (kod "3Z", "Ana Ortaklığa Ait Net Dönem Kârı") parent-only'dir — tutarlı. Gereken veri: azınlık payı (defter VE piyasa değeri) standalone alan olarak XI_29'da YOK; en azından bu tutarsızlık dokümante edilmeli. (Ch.9, s.388-389)
- **BAYRAK-30 — "FD/FAVÖK<7x=Ucuz" Kuralının Anlamsızlığı:** ABD evreninde ~1.500 firma bu eşiğin ALTINDA işlem görüyor — sabit sayısal eşik kurallarının çarpan DAĞILIMININ zaman/sektöre göre KAYDIĞINI göz ardı ettiğinin somut kanıtı. Nasıl tespit edilir: kullanılan "ucuz" eşiğinin GÜNCEL piyasa/sektör dağılımına göre ne kadar TİPİK/ATİPİK olduğu kontrol edilmeli. Gereken veri: evren-çapında EV/FAVÖK dağılımı (Kısım 4'teki AYNI mimari eksiklik — evren-çapında persentil altyapısı YOK). (Ch.9, s.395-396)
- **BAYRAK-31 — Vergi Oranı Farkını Kontrol Etmeden FD/FAVÖK Kıyası:** Vergi-ÖNCESİ çarpanlar vergi oranı FARKLARINDAN vergi-SONRASI çarpanlardan ORANTISIZ BÜYÜK etkilenir (somut örnek: vergi %20→%40'ta FD/FAVÖK %39 düşer, FD/EBIT(1-t) SADECE %18,5 düşer) — yüksek vergi oranlı ülke/şirketler FD/FAVÖK bazında SİSTEMATİK OLARAK "ucuz" görünür. Nasıl tespit edilir: karşılaştırılan firmaların efektif vergi oranı farkı kontrol edilmeli. Gereken veri: efektif vergi oranı (`income_before_tax`/`tax_provision` eksikliği, kitaplar arası tekrarlanan aynı açık). (Ch.9, s.408-409)
- **BAYRAK-32 — Kaldıracı Kontrol Etmeden FD/Satış Kıyası:** İllüstrasyon 9.5'te (Yule Catto) faiz karşılama oranı regresyona EKLENMEDEN "az değerli (%12,1)" sonucu, EKLENDİKTEN SONRA "aşırı değerli (%20,5)" sonucuna DÖNÜŞMÜŞTÜR — ihmal edilen TEK bir (kaldıraç) değişkenin sonucu TERS ÇEVİREBİLECEĞİNİN somut kanıtı. Nasıl tespit edilir: sektör içi FD çarpanı kıyaslarında finansal kaldıraç/faiz karşılama farkı KONTROL EDİLDİ Mİ kontrol et. Gereken veri: faiz karşılama oranı (`interest_expense` eksikliği, Kısım 1/3'ten beri tekrarlanan açık). (Ch.9, s.415-416)
- **BAYRAK-33 — Mevsimsel/Elden-Çıkarma Kaynaklı Nakit-FD Bozulması:** Yıl-sonu nakit ŞİŞKİNLİĞİ (mevsimsel) VEYA yıl-sonu varlık satışı (divestiture) sonrası nakit artışı, EN GÜNCEL bilanço nakdiyle hesaplanan FD'yi YAPAY OLARAK DÜŞÜRÜR (geçmiş FAVÖK hâlâ satılan/mevsimsel varlığın katkısını İÇERDİĞİNDEN) — "ucuz" görünümü YARATABİLİR. Nasıl tespit edilir: kullanılan nakit bakiyesinin YILLIK ORTALAMA mı yoksa dönem-sonu ANLIK değer mi olduğu VE son dönemde büyük bir elden çıkarma OLUP OLMADIĞI kontrol edilmeli. Gereken veri: METODOLOJİK kontrol + çeyreklik nakit serisi (KISMEN mevcut, `trends.py` sınırlı pencere). (Ch.10, s.448-449)
- **BAYRAK-34 — Nakit-Zengin Firmalarda Ham P/E veya P/BV Kıyası:** Nakit ve faaliyet varlıkları FARKLI risk/getiri profiline sahip olduğundan, ham (nakit-arındırılmamış) P/E veya P/BV kıyası nakit AĞIRLIĞI farklı firmaları YANLIŞ sıralar. Nasıl tespit edilir: karşılaştırılan firmaların nakit/piyasa değeri oranları BENZER Mİ kontrol edilmeli; benzer değilse nakit-hariç (net) çarpanlar TERCİH EDİLMELİ. Gereken veri: `cash`, `market_cap`, `equity` MEVCUT — bu bayrak DÜŞÜK maliyetle tespit EDİLEBİLİR (Kısım 4 FORMÜL-86 ile bağlantılı). (Ch.10, s.446-448)

## Uygulama notları (devam)

**Nicel (skorlanabilir):**
- **BAYRAK-29 (pb_ratio azınlık kirliliği) — bu Kısmın EN somut, EN kolay doğrulanabilir bulgusu:** `pb_ratio`'nun tutarsızlığı en azından DOKÜMANTASYON/uyarı notu olarak EKLENEBİLİR (düşük maliyetli); TAM düzeltme (azınlık payı ayrıştırma) VERİ EKSİKLİĞİNE bağlı (yüksek maliyetli).
- **Nakit-hariç P/E, P/BV (FORMÜL-100, Kısım 4 FORMÜL-86 tekrarı)** — `cash`, `market_cap`, `equity` MEVCUT, tek satır kod.
- **BAYRAK-34 nakit-ağırlık farkı rozeti** — `cash/market_cap` oranı tek satır kod, sektör-içi kıyas için bir "nakit ağırlığı farkı" UYARISI üretebilir; DÜŞÜK maliyetli.

**Nitel (LLM yorumuna uygun):**
- Mevsimsel/divestiture nakit bozulması uyarısı (BAYRAK-33) — LLM'e "son çeyrekte olağandışı büyük bir varlık satışı/nakit artışı var mı" diye SORULABİLECEK bir kontrol.
- Yönetime güvensizlik/kötü nakit kullanımı riski (İLKE-221) — LLM'e "bu yönetimin geçmiş sermaye tahsis (satın alma/yatırım) kaydı nasıl" diye SORULABİLECEK NİTEL bir değerlendirme; büyük/artan nakit bakiyesi + zayıf yatırım geçmişi kombinasyonu bir UYARI sinyali olabilir.
- Vergi oranı/kaldıraç farkını kontrol etme uyarıları (BAYRAK-31/32) — rapor şablonuna eklenebilecek dikkat notları, özellikle YABANCI (NASDAQ) emsal kıyaslarında.

**Veri eksikliği / mimari eksiklik nedeniyle UYGULANAMAZ:**
- **Çapraz iştirak tam değerlemesi (FORMÜL-89/90, İLKE-230-235) — bu Kısmın EN BÜYÜK yapısal boşluğu:** iştirak listesi/sahiplik oranı/piyasa değeri verisi TAMAMEN YOK; bu, BIST'te YAYGIN olan holding yapıları (birçok BIST30 şirketi çok sayıda iştirake sahiptir) için ÖZELLİKLE ÖNEMLİ — hem BAYRAK-28 hem BAYRAK-29'un KÖK NEDENİ.
- **WACC/yeniden-yatırım-oranına bağlı FD çarpan formülleri (FORMÜL-92-96)** — Kısım 1-4'teki AYNI kök eksiklik (WACC, Capex).
- **Sektör/piyasa regresyonu (FORMÜL-97)** — Kısım 4'teki AYNI mimari eksiklik (çok-firma karşılaştırma altyapısı YOK).
- **Girişim sermayesi çıkış çarpanı (FORMÜL-99)** — KAPSAM DIŞI (QuaxisLabs özel şirket/girişim sermayesi değerlemesi yapmaz).
- **Fazla fonlu emeklilik planı (FORMÜL-104)** — Türkiye bağlamında düşük ilgi/veri yok.
- **Kapalı-uçlu fon iskonto (FORMÜL-103)** — ürün kapsamı sorusu (TEFAS fonları QuaxisLabs'ın hisse-senedi-odaklı kapsamının DIŞINDA, `tefas.py` fetcher'ı VAR ama bu formülle ENTEGRE DEĞİL).

---

# KISIM 6 — Chapter 11-12: Employee Equity Options and Compensation + The Value of Intangibles (+App.12.1 Option Pricing Models)

**Kapsam:** Chapter 11: Employee Equity Options and Compensation (PDF s.478-528), Chapter 12: The Value of Intangibles + Appendix 12.1: Option Pricing Models (PDF s.528-590). **Bu kullanıcı talimatıyla belirlenmiş oturumun SON kısmıdır** — Kısım 6 bitince DUR, final rapor gönderilecek, Kısım 7-9 YENİ bir oturuma bırakılacak. ID numaralandırması Kısım 1-5'in devamı (İLKE-237'den, FORMÜL-105'ten, BAYRAK-35'ten, Kontrol Listesi Y'den başlar; kesintisiz).

## İlkeler (devam)

**Chapter 11 — Employee Equity Options and Compensation:**

- **İLKE-237 (Özkaynak bazlı tazminatın 3 formu ve 4 sürükleyicisi):** (1) doğrudan hisse hibesi, (2) kısıtlı hisse (belirli süre elden çıkarılamaz/talep edilemez), (3) çalışan opsiyonu (belirli fiyattan hisse alma HAKKI). 4 sürükleyici: hissedar-yönetici çıkar UYUMU (temsil maliyetini azaltma — Jensen&Meckling 1976), nakit KITLIĞI (özellikle 1990'ların genç teknoloji firmaları), çalışan TUTMA (vesting/hak ediş süresi koşulu), muhasebe/vergi AVANTAJI (eski kurallar opsiyonu HARCAMA göstermeden yüksek kâr raporlamaya İZİN veriyordu). (s.478-480)
- **İLKE-238 (Opsiyon örtüsünün [overhang] büyüklüğü):** IRRC 2003 verisi: 1.500 firmalık örneklemde ortalama opsiyon örtüsü **%17** (önceki yıl %15,7), medyan **%16,3** (önceki yıl %14,8); S&P 500'de bile **%16,4**; firmaların ~%90'ında BİR MİKTAR örtü var; **%4,6**'sında (67 firma) örtü **>%40** (önceki yıllarda %3,6/%3'ten ARTIŞ). FAS 123R'nin (2006'dan zorunlu giderleştirme) İLANI 2004'te örtüde İLK DÜŞÜŞE yol açtı. (s.481-482)
- **İLKE-239 (Kimler opsiyon kullanır — 3 belirleyici):** Teknoloji sektörü EN YÜKSEK örtüye sahip (**%24,4**, 2003, önceki yıl %20,8); enerji/kamu hizmeti sektörü EN DÜŞÜK (**<%8**). 3 açıklayıcı faktör: (1) firmanın YAŞI/büyüme potansiyeli (genç=daha fazla opsiyon, nakit kısıtı), (2) RİSKLİLİK (opsiyonlar riskle DEĞER KAZANIR, çoğu menkul kıymetin AKSİNE — piyasa riski FAZLA algılarsa opsiyon çalışan için DAHA DA cazip görünür), (3) piyasa DEĞERLEMESİ (yüksek F/K'lı firmalar opsiyon kullanımından DAHA BÜYÜK vergi avantajı elde eder). (s.482-484)
- **İLKE-240 (Yaşam döngüsü örüntüsü):** Opsiyon hibesi (hisse yüzdesi olarak) genç/riskli/yüksek-değerlemeli firmalarda EN YÜKSEK, büyüme durulup nakit akışı iyileşip değerleme normalleştikçe AZALIR — Cisco örneği: 1995-1997'de >%5 → 2002-2005'te ~%3. (s.484)
- **İLKE-241 (Opsiyon hibesi özellikleri):** Tipik olarak hibe ANINDA para-başabaş (at-the-money) fiyatlanır; UZUN vadeli (10 yıl tipik norm hibe anında); VESTING (hak ediş — genelde belirli süre firmada KALMA) koşuluyla kısıtlanır; TİCARETİ YAPILAMAZ (likit değil); işten ayrılmada VEYA M&A'da ZORUNLU kullanım tetiklenir. (s.485-486)
- **İLKE-242 (Eski [APB 25] muhasebe — 2 hatalı varsayım):** (1) "İçsel değer = kullanım değeri" — çoğu opsiyon PARA-BAŞABAŞ hibe edildiğinden hibe anında DEĞERSİZ sayılır; (2) "gider SADECE kullanım tarihinde tanınır" (hibe tarihinde DEĞİL). Vergi de AYNI mantığı izler: hibede vergi sonucu YOK, kullanımda (fiyat-kullanım farkı) İNDİRİLEBİLİR gider. Bu, genç/riskli firmaların milyonlarca dolarlık opsiyon hibesini SIFIR gider göstererek dağıtmasına İZİN VERDİ. (s.486-487)
- **İLKE-243 (Giderleştirmeye karşı 6 argüman ve karşı-argümanlar):** (1) "belirsiz, gider değil" → firma/çalışan HİBE ANINDA değer olduğuna İNANIYOR, tahmin dahi olsa KAYDEDİLMELİ; (2) "modeller kesin değil" → HATALI tahmin, kullanım-değeri=sıfır varsayımından HER ZAMAN DAHA İYİDİR; (3) "kazanç değişkenliği artar" → bu GERÇEĞİ yansıtır (opsiyon kullanmak bir SEÇİMDİR, kısıtlı hisse/nakit KULLANILABİLİR); (4) "genç firmalar çalışan bulamaz" → temelsiz, iş modeli opsiyon muhasebesine BAĞIMLI firma zaten SORUNLUDUR; (5) "nakit-dışı gider, değeri etkilemez" → YANLIŞ, opsiyon PİYASAYA satılıp nakde çevrilseydi gider SAYILIRDI; (6) "bilgi ZATEN açıklanıyor, giderleştirme formalite" → EN GÜÇLÜ argüman, ama çoğu yatırımcı HALA muhasebe kâr rakamına ANKORLANIYOR. (s.487-489)
- **İLKE-244 (Yeni kurallar — FAS 123R 2003, IFRS 2 2004):** Hibede opsiyon FİYATLAMA MODELİYLE değerlenip GİDERLEŞTİRİLMELİ, beklenen FESİH oranına göre AYARLANMALI, VESTING süresine YAYILMALI, gerçekleşen fesih oranı FARKLIYSA yeniden tahmin EDİLMELİ, kullanım koşulu (örn. fiyat yeniden belirleme) DEĞİŞİRSE değer değişimi TANINMALI. Uluslararası fark KÜÇÜK (IFRS 2 özel/halka açık ayrımı YAPMAZ, ertelenmiş vergi varlığı tanıma ZAMANLAMASI farklı). (s.489-491)
- **İLKE-245 (Opsiyonların değere 3 seviyeli etkisi):** (1) KAZANÇ etkisi (cari yıl hibesi gider — Bear Stearns 2004: S&P 500 ort. **-%8** net kâr, NASDAQ-100 ort. **-%25**; teknoloji sektörü kümülatif **$15,43 milyar** = düzeltilmemiş net kârın **%34**'ü); (2) SEYRELME etkisi (biriken TÜM açık opsiyonların olasılıklı gelecek hisse artışı — kısmi/tam seyreltilmiş hisse sayıları bu olasılığı DOĞRU YANSITMAZ, KABA bir vekildir); (3) GELECEK KAZANÇ etkisi (devam eden gelecekteki hibeler gelecek faaliyet gelirini/nakit akışını AZALTIR — çoğu analist BUNU İHMAL EDER veya cari gelire ÖRTÜK olarak dahil eder). (s.491-494)
- **İLKE-246 (Mevcut opsiyonları DCF'e dahil etmenin 4 yöntemi, KALİTE SIRASIYLA):** (1) TAM SEYRELTİLMİŞ hisse (EN ZAYIF — TÜM opsiyonları [para-içi/dışı ayrımı olmadan] sayar, kullanım GELİRİNİ ve ZAMAN PRİMİNİ yok sayar); (2) gelecek kullanım TAHMİNİ (İMPRATİK/DAİRESEL — gelecek fiyat tahmini gerektirir); (3) TREASURY STOCK yaklaşımı (kullanım geliri eklenir ama zaman primi/vesting HALA yok, DEĞERİ ABARTMA eğilimi); (4) OPSİYON ADİL DEĞER yaklaşımı (EN DOĞRU — opsiyonlar fiyatlama modeliyle değerlenip özkaynak değerinden DÜŞÜLÜR, BİRİNCİL hisseye bölünür). [→ FORMÜL-105/106/107, KONTROL LİSTESİ Y] (s.494-498)
- **İLKE-247 (Çalışan opsiyonu değerlemesinde 5 ölçüm sorunu):** VESTING (henüz hak edilmemiş, HİÇ hak edilmeyebilir); LİKİT OLMAMA (ERKEN kullanıma yol açar — 262.931 opsiyon kullanımı incelemesinde [1996-2003] **%92,3**'ü ERKEN kullanılmış, ortalama vesting'den **2,69 yıl** sonra/vadeden **4,71 yıl** ÖNCE [10 yıllık opsiyon ORTALAMA 5,29 yılda kullanılıyor]; riskli firma çalışanları **~1,5 yıl DAHA ERKEN** kullanıyor); HANGİ FİYAT (piyasa fiyatı mı tahmini DEĞER mi — DAİRESEL sorun, TREASURY STOCK yaklaşımından başlayıp İTERASYONLA çözülür); VERGİ (kullanımda indirim — 3 yöntemle modele DAHİL edilebilir); HALKA AÇIK OLMAYAN firmalar (fiyat/varyans GÖZLEMLENEMEZ, treasury stock VEYA benzer halka açık firma varyansı kullanılır). [→ KONTROL LİSTESİ Z] (s.498-502)
- **İLKE-248 (Opsiyon fiyatlama modeli seçimi):** Black-Scholes UYARLAMALARI (seyreltmeyi fiyata gömme, vadeyi ERKEN kullanım için KISALTMA [tipik olarak YARIYA], vesting olasılığıyla ÇARPMA); BİNOM modeller (erken kullanım/vesting'i DOĞAL olarak ele alır, DAHA VERİ-YOĞUN); Monte Carlo (EN ESNEK, EN veri-yoğun); PİYASA-BAZLI (Cisco'nun ESOR önerisi SEC tarafından 2005'te REDDEDİLDİ). Ampirik olarak (Ammann&Seiz 2003): BEKLENEN (stated DEĞİL) vade kullanıldığında modeller BENZER değer verir — MODEL SEÇİMİNDEN ÇOK VADE VARSAYIMI önemlidir. (s.502-506)
- **İLKE-249 (Opsiyonların göreli değerlemeye etkisi):** BİRİNCİL HBK ile P/E, YÜKSEK-örtülü firmaları SİSTEMATİK OLARAK "ucuz" gösterir (fiyat seyreltmeyi yansıtır, HBK yansıtmaz); TAM SEYRELTİLMİŞ HBK AŞIRI DÜZELTİR (para-dışı/para-içi opsiyonu EŞİT cezalandırır). TEK doğru çözüm: opsiyonları ADİL DEĞERLE değerleyip piyasa değerine EKLEMEK, AGREGE (opsiyon-giderleştirilmiş) net kâra BÖLMEK — AYNI mantık P/BV için de GEÇERLİDİR. [→ BAYRAK-35/36] (s.507-509)
- **İLKE-250 (Piyasa opsiyonları DOĞRU fiyatlıyor mu — 3 ampirik bulgu):** (1) HİBE'ye fiyat tepkisi — negatif tepki KANITI YOK (normal tazminat maliyeti, nötr haber); (2) KULLANIM'a fiyat tepkisi — Garvey&Milbourn (2002): kullanım-kaynaklı seyrelmeye NEGATİF tepki VAR (piyasanın örtüyü TAM fiyatlamadığının KANITI, VEYA kullanımın kendisi "içeriden [insider] hisse aşırı değerli" SİNYALİ olabilir); (3) piyasa değeri vs örtü — Li&Wong (2004): yüksek-örtülü firmalarda piyasa fiyatı **~%6 DÜŞÜK**, opsiyon düzeltmesi piyasa fiyatına DAHA YAKIN sonuç verir (piyasanın örtüyü KABACA da olsa fiyatladığının kanıtı). 2002-2003'te GÖNÜLLÜ giderleştirmeye geçen firmalarda GİDERLEŞTİRMENİN KENDİSİ fiyat tepkisi YARATMADI (piyasa ZATEN önceden fiyatlamıştı). (s.513-515)
- **İLKE-251 (Gelecek opsiyon hibelerinin değere etkisi):** 2 kanaldan: terminal-yıl DEĞERİNİ seyreltme VEYA gelecek FAALİYET GELİRİNİ tazminat gideri olarak AZALTMA. 2 pratik yöntem: (a) gelecek opsiyon değerini HASILAT/faaliyet-geliri YÜZDESİ olarak tahmin edip (firmanın KENDİ geçmişi + OLGUN emsal ortalamasına DOĞRU AZALAN bir varsayımla) operasyonel/SERMAYE gideri olarak modelle; (b) beklenen seyrelmeyi DOĞRUDAN modelle. ÇİFTE SAYIMDAN KAÇIN — AYNI hibeler için HEM gider AYARLAMASI HEM seyrelme AYARLAMASI YAPMA. [→ BAYRAK-40] (s.509-513)
- **İLKE-252 (Opsiyon-ağırlıklı tazminatın kurumsal POLİTİKALARA etkisi):** YATIRIM politikası (opsiyon değeri OYNAKLIKLA ARTAR → yöneticiler DAHA RİSKLİ [düşük-NPV bile olsa] yatırımlara EĞİLİMLİ olabilir, "ortak hissedarlar opsiyon sahibi yöneticileri SÜBVANSE EDER"); FİNANSMAN politikası (teorik olarak DAHA FAZLA borç beklenir ama Graham/Lang/Shackelford 2004 AMPİRİK OLARAK TERSİNİ bulur — opsiyon kullanım vergi tasarrufu borcun vergi kalkanının YERİNE geçer, borç ORANI DÜŞÜK çıkar); TEMETTÜ politikası (DAHA AZ temettü [temettü opsiyon değerini DÜŞÜRÜR] DAHA FAZLA geri alım — Fenn&Liang 2001, Kahle 2004 AMPİRİK olarak DOĞRULAR; piyasa BU geri alımlara DAHA AZ olumlu tepki verir, motivasyonu FARK ETTİĞİNİN kanıtı). (s.515-517)
- **İLKE-253 (Kısıtlı hissenin YENİDEN yükselişi):** FAS 123R sonrası TREND — Mercer Mayıs 2004 anketi: firmaların ~**2/3**'ü özkaynak tazminat programını DEĞİŞTİRDİ; **%22**'si opsiyon-bazlı tazminatı **≥%40** AZALTTI; opsiyonu DEĞİŞTİRENLERİN **%36**'sı EN ÇOK kısıtlı hisseyi TERCİH ETTİ. Amazon örneği: opsiyon hibesi **46,2mn(2001)→3,045mn(2002)→226K(2003)**; kısıtlı hisse **~0(2001)→2,9645mn(2002)→2,1mn(2003)**. Opsiyonun genç/riskli/yüksek-büyümeli firmalarda BASKIN kalması BEKLENİR, kısıtlı hisseye geçiş firma OLGUNLAŞTIKÇA HIZLANIR. (s.517-518)
- **İLKE-254 (Kısıtlı hisse özellikleri):** 2 kısıt: İSTİHDAM (ayrılırsa hisse FESHEDİLİR) ve TİCARET (kısıtlama süresi bitene kadar SATILAMAZ) — bu KOŞULLAR kısıtlı hisseyi kısıtsız hisseden DAHA DÜŞÜK değerli kılar. Varyantlar: "phantom stock" (hayali hisse, vesting'de GERÇEK hisseye dönüşür — DEĞERLEME açısından kısıtlı hisseyle NEREDEYSE ÖZDEŞ), "stock bonus" planları (FAALİYET HEDEFİNE [gelir 2 katı, %20 net kâr büyümesi vb.] KOŞULLU hibe). (s.518-519)
- **İLKE-255 (Kısıtlı hisse muhasebesi):** Hibe değeri tazminat MALİYETİ olarak VESTING süresine YAYILIR (opsiyonlarla AYNI mantık); değerleme HEM fesih olasılığını HEM likit-olmama iskontosunu (gözlemlenen piyasa fiyatından) hesaba KATABİLİR — FASB, iskontonun ANALİST YARGISINA bırakıldığını AÇIKÇA belirtir. (s.519-520)
- **İLKE-256 (Kısıtlı hisse likit-olmama iskontosunun 3 belirleyicisi):** (1) KISITLAMA SÜRESİNİN uzunluğu (uzun=büyük iskonto; YATIRIMCILARA satılan kısıtlı hisse işlemlerinde tipik **%20-30** iskonto GÖZLEMLENİR); (2) HEDGE/BORÇLANMA kısıtları (sıkı=büyük iskonto); (3) hisse OYNAKLIĞI (yüksek=büyük iskonto, likit-olmama maliyeti oynaklıkla BÜYÜR). Detaylı iskonto tahmini Ch.16'da (Kısım 8) GENİŞLEYECEK. [→ KONTROL LİSTESİ BB] (s.520)
- **İLKE-257 (Kısıtlı hisseyi DCF'e dahil etme):** Opsiyonlarla AYNI 3-seviyeli çerçeve (geçmiş ihraçlar=örtü; cari yıl ihracı=tazminat gideri; gelecek ihraçlar=gelecek gider) ama DAHA BASİT çünkü DAİRESELLİK/model-seçimi TARTIŞMASI YOK — tek gerçek soru İSKONTONUN BÜYÜKLÜĞÜDÜR. (s.521-522)
- **İLKE-258 (Kısıtlı hisseyi göreli değerlemeye dahil etme):** Muhasebeciler genelde hisse sayısına EKLERKEN, kısıtlı hisse NORMAL hisseyle AYNI birim fiyattan sayılırsa piyasa değeri (ve TÜM çarpanlar) YUKARI YANLAR (kısıtlı hisse GERÇEKTE daha düşük değerlidir); ETKİ opsiyonlardan KÜÇÜKTÜR (kısıtlı hisse örtüsü genelde DAHA KÜÇÜK, iskonto DEĞİŞKENLİĞİ opsiyon değer değişkenliğinden AZ). [→ BAYRAK-41] (s.522-523)

**Chapter 12 — The Value of Intangibles:**

- **İLKE-259 (Maddi olmayan varlıkların artan önemi):** Muhasebe SİSTEMATİK OLARAK ya küçümser ya TAMAMEN göz ardı eder; marka değeri TEK BAŞINA birçok tüketici ürünü firmasında değerin YARISINDAN FAZLASINI açıklayabilir; değerleme başarısızlığı HEM muhasebe oranlarını (ROE/ROC) HEM piyasa çarpanlarını (P/E, EV/EBITDA) BOZAR. Nakamura (Philadelphia Fed) 3 BAĞIMSIZ ölçüm yöntemiyle (muhasebe yatırım tahmini, yaratıcı işgücü ücretleri, marj iyileşmesi atfı) 2000 ABD ekonomisinde **>$1 TRİLYON** yıllık yatırım, **>$6 TRİLYON** kapitalize değer TAHMİN ETTİ. Lev&Zarowin: kazanç-hisse fiyatı KORELASYONU zamanla ZAYIFLADI, kısmen maddi-olmayan-varlık muhasebesizliğine ATFEDİLDİ. (s.528-530)
- **İLKE-260 (3 katmanlı maddi olmayan varlık taksonomisi):** (1) BAĞIMSIZ, nakit-akışı-üreten (tek ürün/hat — patent, telif hakkı, marka tescili, lisans, franchise) → STANDART DCF YETERLİDİR; (2) FİRMA-GENELİ nakit-akışı-üreten (fayda TÜM işe yayılır — marka, insan sermayesi) → İZOLASYON teknikleri GEREKİR (yatırılan sermaye, DCF-karşılaştırma, göreli değerleme); (3) POTANSİYEL gelecek nakit akışı (OPSİYON özellikleri — geliştirilmemiş patent, doğal kaynak rezervi, genişleme/terk esnekliği) → OPSİYON FİYATLAMA modelleri GEREKİR, standart DCF DEĞERİ DÜŞÜK GÖSTERİR. (s.530) [→ KONTROL LİSTESİ AA]
- **İLKE-261 (Ticari marka/telif hakkı/lisans):** Değer EXCLUSIVE haktan doğan FAZLA GETİRİDEN gelir; DCF (SINIRLI ömür, hak SÜRESİ dolduğundan TERMİNAL DEĞER YOKTUR) VEYA göreli değerleme (benzer varlıkların GEÇMİŞ satış fiyatlarına dayalı çarpan) ile değerlenir. 2 özgün tahmin sorunu: SINIRLI hak süresi (sonsuzluk YOK) ve beklenen İHLAL (violation) MALİYETİ (yasal/izleme maliyeti + tespit-edilemeyen ihlallerden kaybedilen gelir). (s.530-531)
- **İLKE-262 (Franchise):** Değer DOĞRUDAN FAZLA GETİRİ kapasitesine bağlıdır, 3 kaynaktan: MARKA değeri (fiyatlama gücü + franchisor'ın reklam desteği), ÜRÜN/HİZMET UZMANLIĞI (franchisor'ın teknik/operasyonel bilgisi), YASAL TEKEL (münhasır bölgesel hak — NYC taksi plakası örneği). 3 ÖZEL RİSK: franchisor'ın SORUNLARI franchisee'ye SIÇRAR (itibar bulaşması); PAZARLIK GÜCÜ asimetrisi (franchisor >> tek franchisee, KOLEKTİF pazarlıkla azaltılabilir); SEYRELME riski (yakında YENİ bir rakip franchise açılırsa değer DÜŞER). (s.531-534)
- **İLKE-263 (Firma-geneli maddi olmayan varlıkların 3 değerleme yaklaşımı):** YATIRILAN SERMAYE (tarihsel harcamayı kapitalize+itfa et — EN AZ SÜBJEKTİF ama piyasa değeriyle EŞLEŞMEYEBİLİR, bir MALİYET ölçüsüdür DEĞER ölçüsü DEĞİL); DCF İZOLASYONU (varlığa atfedilebilir ARTAN nakit akışını AYIR, AYRI iskonto et); GÖRELİ değerleme (varlığı OLAN firmanın piyasa fiyatlamasını OLMAYAN benzeriyle KARŞILAŞTIR). (s.534-535)
- **İLKE-264 (Marka değeri — tarihi maliyet yaklaşımı mekaniği):** (1) itfa SÜRESİ belirle (tüketici markaları için 20+ yıl); (2) o kadar yıl GERİYE dönük marka-ilişkili harcamayı (genelde reklam giderinin BİR PAYI, örn. %50) TOPLA; (3) DOĞRUSAL itfa et, İTFA EDİLMEMİŞ kısım = marka değeri (Coca-Cola 2004 tahmini: **$26,15 milyar** nominal, enflasyon-düzeltmeli **~$40 milyar**). ELEŞTİRİ: bu YATIRIMI ölçer, DEĞERİ ÖLÇMEZ — firmalar milyarlarca harcayıp SIFIR marka değeri elde edebilir, ya da AZ harcamayla (doğru zaman/yer) BÜYÜK marka değeri kurabilir. [→ FORMÜL-111] (s.535-537)
- **İLKE-265 (Marka değeri — DCF/jenerik firma yaklaşımı):** GERÇEK bir "jenerik ikiz" bulmak GENELDE İMKANSIZDIR (marka firmaları SEKTÖRE HAKİMDİR); 3 yaklaşım: JENERİK FAALİYET MARJI ikamesi (marka gücü=fiyatlama gücü varsayımı — marj değişimi ROC→büyüme ZİNCİRİYLE YAYILIR, KÜÇÜK marj değişimi BÜYÜK değer değişimine dönüşür), JENERİK SERMAYE GETİRİSİ (ROC) ikamesi (HEM marj HEM devir hızı kanalını YAKALAR), JENERİK FAZLA GETİRİ (ROC-kc) ikamesi (EN KAPSAMLI — marka VE jenerik firma için FARKLI sermaye maliyeti de İZİN VERİR, marka firmaları genelde DAHA DÜŞÜK riskli/DAHA FAZLA borç kapasiteli olabilir). 2 ORTAK varsayım: erişilebilir jenerik firma VAR ve marka TEK açıklayıcı FARKTIR (aksi halde sonuç TÜM rekabet avantajlarının KONSOLİDE değeridir). [→ FORMÜL-112] (s.537-539)
- **İLKE-266 (Marka değeri — fazla getiri kısayolu, jenerik firma YOKKEN):** Firmanın TÜM fazla getirisini (ROC-kc) markaya ATFET; marka değeri = tahmini firma değeri - yatırılan sermaye defter değeri (Ch.6'nın fazla-getiri modeli mantığı). Jenerik firma YAKLAŞIMIYLA AYNI sonucu verir SADECE jenerik firma SIFIR fazla getiri kazanıyorsa. SINIRLAMA: fazla getiri TÜM rekabet avantajlarından gelir, SADECE markadan DEĞİL; yatırılan sermaye MUHASEBE MANİPÜLASYONUNA açıktır. [→ FORMÜL-113] (s.539-540)
- **İLKE-267 (Marka değeri — göreli değerleme):** (a) jenerik-firma ÇARPAN FARKI yöntemi (marka değeri = [marka firması çarpanı - jenerik çarpan] × marka firmasının ÖLÇEK değişkeni — FARKLI ölçek tabanları [satış/FAVÖK/sermaye] ÇOK FARKLI marka-değeri tahminleri üretir, Coca-Cola/Cott örneğiyle SOMUTLAŞTIRILDI); (b) çapraz-kesit REGRESYON (DOĞRUDAN marka-gücü dummy değişkeni VEYA VEKİL değişken [faaliyet marjı] ile) — R² TİPİK OLARAK DÜŞÜK, tahminde BÜYÜK standart hata anlamına gelir. [→ FORMÜL-114/115, BAYRAK-37] (s.543-546)
- **İLKE-268 (Marka değerleme uyarıları):** TEK vs ÇOKLU marka portföyü (P&G gibi çoklu-marka firmalarda SADECE KONSOLİDE bir portföy değeri elde edilir, marka-BAŞINA DEĞİL); TEK vs ÇOKLU ürün hattı (IBM gibi çok-segmentli firmalarda SEGMENT-SEVİYESİNDE değerleme GEREKİR, marka değeri segmentler arası EŞİT OLMAYABİLİR); DİĞER rekabet avantajlarıyla İÇ İÇE GEÇME (marka değerlemesi TEK ürün/TEK rekabet-avantajlı firmalarda EN TEMİZ, aksi halde GİDEREK KARMAŞIKLAŞIR — Fernandez 2001 TÜM marka değerleme yaklaşımlarını ELEŞTİRİR, yazar da AYNI FİKİRDE). (s.546-547)
- **İLKE-269 (İnsan sermayesi):** Markayla ANALOG 4 yaklaşım (tarihi maliyet — işe alım/eğitim/yan hak giderleri; DCF-jenerik karşılaştırma; fazla getiri atfı; göreli değerleme) AMA marka'dan FARKLI KRİTİK bir uyarıyla: insan sermayesi firma tarafından SADECE "KİRALANIR" (çalışan REKABETÇİ bir teklifle AYRILABİLİR) — insan sermayesinden doğan fazla getirinin TAMAMEN ÇALIŞANLARA (tazminat yoluyla) gidip firma ÖZKAYNAK DEĞERİNE HİÇ YANSIMAMASI TAMAMEN OLASIDIR. En ilgili alan: danışmanlık/yatırım bankacılığı/bilgi-yoğun firmalar. (s.547-548)
- **İLKE-270 (Şerefiye [goodwill] — GERÇEK bir varlık DEĞİL):** Şerefiye bir MUHASEBE DENGE KALEMİDİR (satın alma FİYATI − hedefin defter değeri), gerçek bir varlık DEĞİLDİR. EN İYİMSER yorum "satın alınan büyüme varlıklarının değeri"dir ama bu SADECE (a) satın almada ADİL fiyat ödendiyse VE (b) hedefin defter değeri VARLIKLARIN-YERİNDE değerini YANSITIYORSA geçerlidir (İKİSİ de CESUR varsayım). GERÇEK bileşim = (defter değeri YANLIŞ-ÖLÇÜMÜ) + (satın almada FAZLA/AZ ÖDEME). İDEAL (nadiren uygulanan) çözüm: şerefiyeyi "AKILLI" (haklı büyüme-varlığı primi, ROC hesabında yatırılan sermayeden HARİÇ TUTULMALI çünkü HENÜZ YAPILMAMIŞ yatırımdan operasyonel gelir BEKLEMEK HAKSIZLIK olur) ve "APTAL" (fazla ödeme, sermayeye DAHİL EDİLMELİ, ROC'yi DÜŞÜRÜR) bileşenlere AYIRMAK. [→ BAYRAK-38] (s.548-549)
- **İLKE-271 (Geliştirilmemiş patent = ÇAĞRI OPSİYONU):** Firma, TİCARİLEŞTİRME beklenen nakit akışlarının BD'si (V) geliştirme MALİYETİNİN BD'sini (I) AŞARSA geliştirir; AŞMAZSA HİÇBİR EK MALİYET olmadan patenti RAFA KALDIRABİLİR — bu ASİMETRİK payoff (max(V-I,0)) TAM OLARAK bir çağrı opsiyonu YAPISIDIR. [→ FORMÜL-116] (s.549-550)
- **İLKE-272 (Patent opsiyonunda "gecikme maliyeti"):** Patent KORUMASININ KENDİSİ SINIRLI bir yasal ömre sahip olduğundan, ticarileştirmeyi GECİKTİRMENİN HER YILI firmaya BİR YIL patent-korumalı FAZLA GETİRİ dönemine MAL OLUR (gecikme maliyeti ≈ 1/kalan-patent-yılı — TEMETTÜ VERİMİNE ANALOG); bu, patent opsiyonlarını TEMETTÜ-ÖDEYEN çağrı opsiyonu gibi davrandırır — AŞIRI gecikme, zaman priminin varlığına RAĞMEN DEĞER YIKICI olabilir. [→ FORMÜL-117] (s.550-552)
- **İLKE-273 (Patentli firmanın değeri — 3 bileşen):** (1) ZATEN ticarileşmiş ürünlerin DCF değeri; (2) sahip OLUNAN ama geliştirilmemiş patentlerin OPSİYON değeri; (3) GELECEKTEKİ Ar-Ge'den doğacak yeni patentlerin BEKLENEN değeri (beklenen Ar-Ge maliyeti = beklenen üretilen değere EŞİTSE SIFIR, KANITLANMIŞ değer-yaratan araştırma geçmişi olan firmalarda [Cisco, Pfizer] POZİTİF). Standart DCF, bileşen 2-3'ü BEKLENEN BÜYÜME oranına ÖRTÜK olarak GÖMER; AÇIK opsiyon-bazlı yaklaşım SADECE AZ SAYIDA, BÜYÜK patenti olan KÜÇÜK firmalarda (örn. tek-ilaçlı biyoteknoloji) PRATİKTİR — Cisco/Pfizer gibi YÜZLERCE patentli büyük firmalarda bilgi GEREKSİNİMİ İMPRATİKTİR, geleneksel DCF PRAGMATİK seçimdir. (s.552-553)
- **İLKE-274 (Doğal kaynak rezervi = ÇAĞRI OPSİYONU, 5 girdi):** Payoff = max(rezerv değeri[V] - geliştirme maliyeti[X], 0). 5 girdi: (1) rezerv MİKTARI × (fiyat-değişken maliyet) = dayanak varlık değeri; (2) geliştirme maliyeti = kullanım fiyatı; (3) opsiyon ÖMRÜ = kira/imtiyaz süresi VEYA kapasite-bazlı tükenme süresi; (4) VARYANS = ÇOĞUNLUKLA kaynak FİYATI oynaklığından (rezerv miktarı tahmini genelde fiyat tahmininden DAHA KESİNDİR); (5) "gecikme maliyeti" = para-içi olduktan sonraki net üretim geliri/rezerv-değeri oranı (temettü verimi ANALOĞU) + GELİŞTİRME GECİKMESİ iskontosu (karar-ile-ilk-nakit-akışı arası süre, İLK yılların nakit akışını ÇIKARMAK gibi ele alınır). [→ FORMÜL-118] (s.554-557)
- **İLKE-275 (Tüm firma rezervlerinin değerlenmesi — pratik kısayol):** TEORİK OLARAK her rezerv AYRI bir opsiyon olarak değerlenmeli (opsiyon-PORTFÖYÜ), ama büyük çok-rezervli firmalarda (petrol devleri) veri KISITI PRATİK bir kısayola ZORLAR: TÜM geliştirilmemiş rezervleri TEK bir AGREGE opsiyon olarak değerlemek — bu SİSTEMATİK OLARAK DEĞERİ DÜŞÜK GÖSTERİR (bir PORTFÖY üzerine opsiyon, opsiyonların PORTFÖYÜNDEN DAHA AZ değerlidir, çünkü kusurlu-korelasyonlu varlıkları TOPLAMAK varyansı DÜŞÜRÜR) ama yine de FAYDALI bir perspektif sunar. Geliştirme HIZI (verimlilik) firma-seviyesi bir DEĞER SÜRÜCÜSÜ haline gelir — daha HIZLI geliştirebilen firmaların geliştirilmemiş rezervleri, DİĞER her şey eşitken, DAHA DEĞERLİDİR. (s.557-559)
- **İLKE-276 ("Esneklik değeri" — DCF eleştirisi):** Standart (beklenen-nakit-akışı) DCF, ANLAMLI genişleme OPSİYONALİTESİ (yukarı esneklik) VEYA terk OPSİYONALİTESİ (aşağı KORUMA) olan firmalarda değeri DÜŞÜK GÖSTEREBİLİR, çünkü SADECE TEK bir beklenen yolu yakalar, YENİ bilgiye TEPKİ VEREBİLME değerini YAKALAMAZ. (s.560)
- **İLKE-277 (Genişleme opsiyonu — yapı ve 3 testli değerlilik kontrolü):** İLK (genelde negatif-NPV) proje, İKİNCİ (daha büyük) bir yatırım YAPMA HAKKINI (yükümlülüğü DEĞİL) yaratır; İKİNCİ proje DAYANAK varlıktır (S=2. projenin beklenen nakit akışı BD'si, X=2. projenin maliyeti, ömür=İÇSEL olarak belirlenen karar UFKU — patentlerin AKSİNE DIŞSAL bir vade YOKTUR). Opsiyonun GERÇEK değere sahip olup OLMADIĞINI test eden 3 soru: (1) İLK yatırım İKİNCİ için GERÇEK bir ÖN KOŞUL MU (patent/rezerv=EVET; pazar-keşif yatırımı=DAHA ZAYIF bağlantı [AmBev örneği]; sadece "ayak izi" için yapılan SATIN ALMALAR=EN ZAYIF bağlantı); (2) firmanın İKİNCİ yatırıma EXCLUSİVE (veya belirgin AVANTAJLI) erişimi VAR MI, yoksa BAŞARI rakipleri mi ÇEKER (AmBev'in Guaraná'sında EXCLUSİVİTE YOK — Coca-Cola/Pepsi TAKLİT edebilir, bu opsiyon değerini SIFIRA yaklaştırabilir); (3) ortaya çıkan rekabet avantajı NE KADAR SÜRDÜRÜLEBİLİR (sektör rekabet YOĞUNLUĞU + avantajın DOĞASI — KIT/SINIRLI kaynaklar İLK-HAMLE/teknoloji avantajından DAHA UZUN sürer). [→ FORMÜL-119, KONTROL LİSTESİ AA] (s.560-567)
- **İLKE-278 (Reel opsiyon KÖTÜYE KULLANIMI uyarısı):** "Stratejik opsiyon"/"sinerji" argümanları TARİHSEL OLARAK AŞIRI satın alma primlerini VE negatif-NPV yatırımları SAYISAL DEĞERLEME OLMADAN savunmak için KULLANILMIŞTIR; Damodaran'ın standardı: reel opsiyon MANTIĞINI kullanan yönetici bunu SAYISAL OLARAK değerleyip EKONOMİK FAYDA>MALİYET olduğunu GÖSTERMEK ZORUNDADIR — "tahmin etmemek" GEÇERLİ bir mazeret DEĞİLDİR, kaba bir tahmin BİLE hiç tahmin olmamasından İYİDİR. [→ BAYRAK-39] (s.564-565)
- **İLKE-279 (Firma-seviyesinde genişleme opsiyonu gömme):** Küçük, YÜKSEK büyümeli, BÜYÜK/gelişen pazardaki firmalarda saf-DCF üzerine bir PRİM teorik olarak SAVUNULABİLİR; EN DEĞERLİ OYNAK/YÜKSEK-getirili işlerde (biyoteknoloji, yazılım), EN AZ DEĞERLİ İSTİKRARLI/DÜŞÜK-getirili işlerde (konut, kamu hizmeti, otomotiv). KRİTİK disiplin: DCF büyüme oranı ZATEN başarı-koşullu genişlemeyi (ÖRTÜK olarak) YANSITIYORSA, AYRICA bir genişleme-opsiyonu değeri EKLEMEK ÇİFT SAYIMDIR. (s.567-570)
- **İLKE-280 (Terk etme opsiyonu — PUT yapısı):** V=devam etmenin BD'si, L=tasfiye/terk DEĞERİ; sahibi HER karar noktasında max(devam, terk) SEÇER — L, TAM OLARAK bir put'un KULLANIM FİYATI gibi bir TABAN sağlar. Firma-seviyesi sonuç: AYNI beklenen DCF özelliklerine (nakit akışı, sermaye maliyeti, ROC, büyüme) sahip İKİ firma, biri SİSTEMATİK OLARAK "çıkış kapısı" (kısa-vadeli sözleşme, sendika ANLAŞMASI YOK, KİRALAMA satın-almaya TERCİH) kurmuşsa FARKLI GERÇEK değere sahip olabilir — ESNEK firma DAHA YÜKSEK değer HAK EDER, saf DCF bunu YAKALAMAZ. Gelir KALİTESİ uzantısı: kolay-çıkış çok-yıllı sözleşmelerle müşteri KAZANAN bir firma YÜKSEK gelir büyümesi GÖSTEREBİLİR ama müşterilere VERİLEN terk opsiyonu için DEĞER-İSKONTOLANMALIDIR. (s.570-572)
- **İLKE-281 (DCF vs reel opsiyon UZLAŞMASI):** İki yöntem DOĞRU uygulandığında AYNI değere YAKINSAMALIDIR; fark METODOLOJİDEN DEĞİL, İSKONTO ORANI varsayımından doğar — karar ağaçları TİPİK OLARAK TEK bir sabit sermaye maliyeti kullanır, oysa PAZAR RİSKİ MARUZİYETİ (dolayısıyla doğru iskonto oranı) HER düğümde DEĞİŞEBİLİR; opsiyon-fiyatlama/replikasyon-portföyü yaklaşımı bunu YAPISAL OLARAK doğru ele alır ve SÜREKLİ (ayrık DEĞİL) dağılımlara GENİŞLETMESİ DAHA KOLAYDIR. (s.572-573)

**Appendix 12.1 — Option Pricing Models:**

- **İLKE-282 (Opsiyon payoff ASİMETRİSİ):** Opsiyon sahibinin MAKSİMUM kaybı ÖDENEN PRİMLE SINIRLIDIR, YUKARI YÖNLÜ getiri (çağrı) TEORİK OLARAK SINIRSIZ veya (put) kullanım fiyatıyla SINIRLIDIR — bu ASİMETRİ, YÜKSEK varyansın NEDEN opsiyon değerini ARTTIRDIĞINI (dayanak varlığın KENDİ değerine etkisinin TERSİ) açıklar; İSTİSNA: ÇOK DERİN para-içi çağrı opsiyonları (dayanak varlığa NEREDEYSE ÖZDEŞLEŞTİĞİNDEN) YÜKSEK varyanstan DEĞER KAYBEDEBİLİR. (s.573-576)
- **İLKE-283 (6 belirleyici ve YÖNLERİ, Tablo A12.1):** Dayanak varlık değeri (çağrı+, put−); kullanım fiyatı (çağrı−, put+); VARYANS (İKİSİ DE +, her ikisi de BÜYÜK fiyat sıçramalarından FAYDALANIR); vadeye kalan süre (İKİSİ DE +, daha fazla süre=DAHA FAZLA olumlu sıçrama şansı); faiz oranı (çağrı+, put− — kullanım fiyatının BD'si etkisinden); dayanak varlığın temettüsü (çağrı−, put+ — temettü dayanak DEĞERİNİ DÜŞÜRÜR; AYRICA para-içi çağrılar için bir "kullanımı GECİKTİRME MALİYETİ"dir, ÇÜNKÜ kullanmak SONRAKİ temettüyü YAKALAR). (s.575-577)
- **İLKE-284 (Amerikan vs Avrupa tipi kullanım):** Erken kullanım ÇOĞUNLUKLA SUBOPTIMALDİR (opsiyonu SATMAK, KALAN zaman primi nedeniyle kullanmaktan DAHA DEĞERLİDİR); 2 İSTİSNA: (a) dayanak varlık BÜYÜK temettü ÖDÜYORSA (ex-dividend ÖNCESİ kullanım, kaybedilen zaman priminden BÜYÜK temettü YAKALAR); (b) faiz oranları YÜKSEKKEN dayanak varlık + DERİN para-içi PUT birlikte TUTULUYORSA (erken kullanım, kullanım gelirinden FAİZ KAZANMAYI HIZLANDIRIR). (s.577-578)

---

## Formüller (devam)

- **FORMÜL-105 — Tam Seyreltilmiş Yaklaşım (Değer/Hisse, Naif)**
  - Formül: `Değer/Hisse = Özkaynak Değeri (DCF) / (Birincil Hisse + TÜM Açık Opsiyon Sayısı)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çalışan opsiyon sayısı/kullanım fiyatı hiçbir fetcher'da YOK; ayrıca `valuation.py`'nin DCF-türetilmiş özkaynak değeri hiçbir seyreltilmiş hisse sayısıyla İLİŞKİLENDİRİLMİYOR.

- **FORMÜL-106 — Treasury Stock Yaklaşımı**
  - Formül: `Değer/Hisse = [Özkaynak Değeri + (Opsiyon Sayısı × Ortalama Kullanım Fiyatı)] / Tam Seyreltilmiş Hisse`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (aynı kök neden).

- **FORMÜL-107 — Opsiyon Adil Değer Yaklaşımı (Önerilen, En Doğru)**
  - Formül: `Değer/Hisse = [Özkaynak Değeri - Opsiyonların Adil Değeri (vergi sonrası)] / Birincil Hisse`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (aynı kök neden).

- **FORMÜL-108 — Vergi-Ayarlı Opsiyon Değeri (3 Yöntem)**
  - Formül: (a) düşük tahmin dönemi vergi oranıyla FCFF hesabı; (b) `(Fiyat - Kullanım Fiyatı) × Vergi Oranı`; (c) `Opsiyon Adil Değeri × (1 - Vergi Oranı)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** (opsiyon verisi yok, ayrıca marjinal vergi oranı da Kısım 1'den beri VERİ EKSİK).

- **FORMÜL-109 — Opsiyon-Ayarlı P/E ve P/BV**
  - Formül: `Ayarlı P/E = [Piyasa Değeri + Opsiyonların Adil Değeri] / [Net Kâr (opsiyon gideri düşülmüş, agrege)]`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — ANCAK bu formül grubunun BIST kapsamındaki PRATİK ÖNEMİ DÜŞÜKTÜR (Türkiye'de yaygın/geniş-tabanlı çalışan opsiyon programları NASDAQ'a göre ÇOK DAHA NADİR — kültürel/vergisel farklar); NASDAQ kapsamı için TEORİK önem DAHA YÜKSEK ama veri YİNE eksik.

- **FORMÜL-110 — Kısıtlı Hisse (Restricted Stock) Değeri**
  - Formül: `Kısıtlı Hisse Değeri = Piyasa Fiyatı × (1 - Likit-Olmama İskontosu) × (1 - Fesih/Ayrılma Olasılığı)`
  - QuaxisLabs karşılığı: **VERİ EKSİK** — kısıtlı hisse programı verisi hiçbir fetcher'da YOK.

- **FORMÜL-111 — Marka Değeri, Tarihi Maliyet Yaklaşımı**
  - Formül: `Marka Değeri = Σ [Yıllık Reklam/Pazarlama Harcaması × Marka-İlişkili Pay% × (İtfa Edilmemiş Kısım Oranı)]` (doğrusal itfa, N yıllık amortisman süresi üzerinden)
  - QuaxisLabs karşılığı: **VERİ EKSİK** — çok-yıllı (20+ yıl) reklam/pazarlama gideri STANDALONE alan olarak YOK (hem tek-yıllık kırılım hem uzun tarihçe eksik — SG&A alt kırılımı Buffett turunda da tespit edilen açık).

- **FORMÜL-112 — Marka Değeri, Jenerik Firma Karşılaştırması (3 Varyant)**
  - Formül: Firma değerini SIRASIYLA (a) faaliyet marjı, (b) sermaye getirisi (ROC), (c) fazla getiri (ROC-kc) jenerik firma değerleriyle DEĞİŞTİREREK yeniden hesapla; fark = marka değeri.
  - QuaxisLabs karşılığı: **KISMEN VAR/PARALEL** — `valuation.py`'nin Damodaran FCFE bloğu YAPISAL olarak bu "girdi değiştir, yeniden hesapla" mantığını DESTEKLEYEBİLİR, ama otomatik bir "marka değeri" ÇIKTISI YOK; jenerik (marka-siz) karşılaştırma firması SEÇİMİ tamamen ANALİST-seviyesi manuel bir iştir.

- **FORMÜL-113 — Marka Değeri, Fazla Getiri Kısayolu (Jenerik Firma Yokken)**
  - Formül: `Marka Değeri = Tahmini Firma Değeri - Yatırılan Sermaye Defter Değeri` (TÜM fazla getiri markaya atfedilirse)
  - QuaxisLabs karşılığı: `equity`+`financial_debt` (yatırılan sermaye YAKLAŞIĞI) MEVCUT; "tahmini firma değeri" WACC eksikliğine bağlı (Kısım 1) — KISMEN uygulanabilir SADECE FCFE-bazlı (özkaynak) versiyonuyla.

- **FORMÜL-114 — Marka Değeri, Göreli Değerleme (Çarpan Farkı)**
  - Formül: `Marka Değeri = (Marka Firması Çarpanı - Jenerik Firma Çarpanı) × Marka Firmasının Ölçek Değişkeni`
  - QuaxisLabs karşılığı: `ev_revenue`, `ev_ebitda` MEVCUT — jenerik KARŞILAŞTIRMA firması seçimi MANUEL, ama HESABIN KENDİSİ düşük maliyetlidir.

- **FORMÜL-115 — Marka Değeri, Regresyon (Dummy/Vekil Değişken)**
  - Formül: `Çarpan = a + b×(Marka Dummy VEYA Faaliyet Marjı) + diğer temel değişkenler`
  - QuaxisLabs karşılığı: Kısım 4/5'teki AYNI mimari eksiklik (çok-firma cross-sectional regresyon altyapısı YOK) — **UYGULANAMAZ**.

- **FORMÜL-116 — Patent/Ar-Ge Opsiyonu (Basit Çağrı Opsiyonu Payoff)**
  - Formül: `Patent Değeri = max(V - I, 0)` → Black-Scholes ile TAM değerleme (V=ticarileştirme nakit akışlarının BD'si, I=geliştirme maliyetinin BD'si)
  - QuaxisLabs karşılığı: **KAPSAM DIŞI/VERİ EKSİK** — patent-seviyesi değerleme, TEK-varlık/proje odaklı bir yöntemdir; QuaxisLabs'ın ŞİRKET-GENELİ temel analiz veri modeli patent-seviyesi bilgi (V, I girdileri) TOPLAMIYOR — biyoteknoloji/ilaç şirketlerinde İSTİSNAİ olarak ilgili olabilir ama otomatik pipeline'a UYGUN DEĞİL.

- **FORMÜL-117 — Gecikme Maliyeti (Patent Opsiyonu, Temettü Analoğu)**
  - Formül: `Gecikme Maliyeti Oranı ≈ 1 / Kalan Patent Yılı`
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** (FORMÜL-116 ile aynı kök).

- **FORMÜL-118 — Doğal Kaynak Rezervi Opsiyonu**
  - Formül: `Rezerv Değeri = max(V - X, 0)` → Black-Scholes (V=Rezerv Miktarı × Katkı Payı [fiyat-değişken maliyet], X=Geliştirme Maliyeti)
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — rezerv-seviyesi jeolojik/mühendislik verisi (rezerv miktarı, geliştirme maliyeti) hiçbir fetcher'da YOK VE muhtemelen BİLİNÇLİ olarak kapsam dışı bırakılmalı — bu, hisse senedi temel analiz motorunun DOĞAL sınırının ÖTESİNDE, sektöre özel mühendislik verisi gerektirir (BIST'teki enerji/madencilik şirketleri için bile).

- **FORMÜL-119 — Genişleme Opsiyonu (Expansion Option)**
  - Formül: `Genişleme Değeri = max(V₂ - X₂, 0)` → Black-Scholes/Binom (V₂=2. projenin BD'si, X₂=2. projenin maliyeti, T=içsel karar ufku)
  - QuaxisLabs karşılığı: **VERİ EKSİK/METODOLOJİK** — 2. proje senaryosu VE onun oynaklığı için PROJE-SEVİYESİ (şirket-geneli DEĞİL) veri/varsayım gerektirir, QuaxisLabs'ın standart OTOMATİK pipeline'ında YOK — analist-seviyesi İSTİSNAİ bir uygulama olabilir ama OTOMATİK SKORLANAMAZ.

- **FORMÜL-120 — Terk Etme Opsiyonu (Abandonment Option, Put Yapısı)**
  - Formül: `Terk Değeri = max(L - V, 0)` → Black-Scholes PUT (L=tasfiye/terk değeri, V=devam etme değeri)
  - QuaxisLabs karşılığı: **VERİ EKSİK/METODOLOJİK** (FORMÜL-119 ile AYNI kök — proje-seviyesi veri gerektirir).

- **FORMÜL-121 — Black-Scholes Çağrı Opsiyonu Temel Formülü**
  - Formül: `C = S×N(d1) - K×e^(-rt)×N(d2)`; `d1 = [ln(S/K) + (r+σ²/2)t] / (σ√t)`; `d2 = d1 - σ√t`
  - Değişkenler: `S`=dayanak varlık değeri, `K`=kullanım fiyatı, `t`=vade, `r`=risksiz oran, `σ²`=ln(değer) varyansı, `N()`=standart normal kümülatif dağılım.
  - QuaxisLabs karşılığı: **KISMEN VAR — bu Kısmın EN İLGİNÇ mimari bulgusu.** `src/analysis/merton.py::compute_merton_dd_edf()` (`distance_to_default = (ln(asset_value/D) + (r-0.5×asset_vol²)×T) / (asset_vol×√T)`) YAPISAL OLARAK AYNI Black-Scholes-Merton `d1/d2` ÇERÇEVESİNİ kullanıyor (özkaynağı, VARLIK DEĞERİ üzerine bir çağrı opsiyonu olarak modelleyen Merton temerrüt modeli) — bu Kısımdaki TÜM opsiyon uygulamaları (patent/doğal kaynak/genişleme/terk) AYNI matematiksel MOTORU (Black-Scholes) paylaşıyor, QuaxisLabs'ta bu MOTOR ZATEN VAR (farklı bir bağlamda, temerrüt olasılığı için) — TEORİK OLARAK yeniden kullanılabilir bir bileşendir, ama HER opsiyon TÜRÜ için gereken GİRDİ verisi (V, X, σ, T) HİÇBİRİ MEVCUT DEĞİL.

- **FORMÜL-122 — Put-Call Paritesi**
  - Formül: `P = C - S + K×e^(-rt)`
  - QuaxisLabs karşılığı: FORMÜL-121 ile AYNI motor notu — girdi eksikliği nedeniyle DOĞRUDAN UYGULANAMAZ ama `merton.py`'nin matematiksel ALTYAPISIYLA KAVRAMSAL OLARAK uyumlu.

- **FORMÜL-123 — Temettü/Seyreltme Düzeltmeli Black-Scholes (Warrant/Çalışan Opsiyonu)**
  - Formül: `S_ayarlı = (S×n_s + W×n_w) / (n_s + n_w)` (n_s=hisse sayısı, W=warrant/opsiyon değeri, n_w=warrant/opsiyon sayısı — seyreltme düzeltmesi)
  - QuaxisLabs karşılığı: **VERİ EKSİK** (opsiyon/warrant sayısı ve değeri hiçbir fetcher'da YOK).

---

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| ABD opsiyon örtüsü (overhang), IRRC 2003 | Ortalama **%17** (medyan %16,3), S&P 500'de **%16,4** | Opsiyon-bazlı tazminatın YAYGINLIĞININ somut ölçüsü | Ch.11, s.481-482 |
| Yüksek-örtülü (>%40) firma oranı, 2001→2003 | **%3 → %3,6 → %4,6** | Trend ARTIŞI, FAS 123R öncesi zirve | Ch.11, s.481-482 |
| Teknoloji sektörü vs enerji/kamu hizmeti örtüsü (2003) | **%24,4** vs **<%8** | Sektörel farkın büyüklüğü | Ch.11, s.482 |
| Opsiyon giderleştirmesinin net kâra etkisi (Bear Stearns 2004) | S&P 500 ort. **-%8**, NASDAQ-100 ort. **-%25** | Giderleştirmenin BÜYÜKLÜK farkı, teknoloji-ağırlıklı endekslerde ÇOK DAHA BÜYÜK | Ch.11, s.492 |
| Teknoloji sektörü kümülatif opsiyon gideri (2004) | **$15,43 milyar** = düzeltilmemiş net kârın **%34**'ü | | Ch.11, s.492 |
| Cisco/Google değer/hisse — yöntem karşılaştırması (İllüstrasyon 11.1-11.3) | Cisco: Birincil **$10,12** → Tam seyreltilmiş **$8,28** → Treasury stock **$12,82** → Opsiyon-adil-değer **$9,80/$10,07** (iterasyonlu) | 4 yöntemin AYNI şirkette ÜRETTİĞİ FARKLI sonuçların somut kanıtı | Ch.11, s.495-507 |
| Erken opsiyon kullanımı oranı (262.931 kullanım, 1996-2003) | **%92,3**'ü erken kullanılmış | Likit-olmamanın kullanım DAVRANIŞINA etkisinin BÜYÜKLÜĞÜ | Ch.11, s.499-500 |
| Ortalama erken kullanım zamanlaması | Vesting'den **2,69 yıl** sonra, vadeden **4,71 yıl** önce (10 yıllık opsiyon ~**5,29 yılda** kullanılır) | | Ch.11, s.500 |
| Riskli firma çalışanlarının erken kullanım farkı | **~1,5 yıl** daha erken | | Ch.11, s.500 |
| Cisco'nun opsiyon kullanımından vergi indirimi (2000) | **$2,5 milyar** (faaliyet kârı $2,67 milyara neredeyse EŞİT) | Vergi avantajının BÜYÜKLÜĞÜNÜN somut örneği | Ch.11, s.501 |
| Piyasa değeri vs opsiyon örtüsü ilişkisi (Li&Wong 2004) | Yüksek-örtülü firmalarda fiyat **~%6 DÜŞÜK** | Piyasanın örtüyü KABACA fiyatladığının kanıtı | Ch.11, s.514 |
| Kısıtlı hisse likit-olmama iskontosu (piyasa işlemleri) | **%20-30** | Kısıtlı hisse değerleme için REFERANS aralık | Ch.11, s.520 |
| Mercer Mayıs 2004 anketi — özkaynak tazminat değişimi | Firmaların **~%67**'si program DEĞİŞTİRDİ; **%22**'si opsiyonu **≥%40** AZALTTI; DEĞİŞTİRENLERİN **%36**'sı kısıtlı hisseyi TERCİH ETTİ | | Ch.11, s.518 |
| Amazon opsiyon hibesi, 2001→2003 | **46,2mn → 3,045mn → 226K** | Opsiyondan kısıtlı hisseye GEÇİŞİN somut/dramatik örneği | Ch.11, s.518 |
| S&P 500 firmalarının gönüllü giderleştirme oranı (Şubat 2004) | **276/500 firma** (piyasa değerinin **%41**'i) | | Ch.11, s.489 |
| Küresel maddi olmayan varlık yatırımı/kapitalize değeri (2000, ABD, Nakamura) | Yatırım **>$1 trilyon**, kapitalize değer **>$6 trilyon** | Maddi olmayan varlıkların EKONOMİ-GENELİ büyüklüğü | Ch.12, s.529 |
| Coca-Cola marka değeri, tarihi maliyet yaklaşımı | **$26,15 milyar** nominal / **~$40 milyar** enflasyon-düzeltmeli | | Ch.12, İllüstrasyon 12.2 |
| Coca-Cola marka değeri, yaklaşıma göre ARALIK (İllüstrasyon 12.3) | Faaliyet marjı yaklaşımı **EN YÜKSEK (~$64mlr)** — ROC yaklaşımı **EN DÜŞÜK (~$50mlr)** | AYNI şirket için YÖNTEME göre BÜYÜK fark | Ch.12, s.542-543 |
| Coca-Cola vs Cott — EV çarpanları (İllüstrasyon 12.4) | EV/Satış **4,49 vs 0,77**; EV/FAVÖK **12,71 vs 6,81**; EV/Sermaye **6,01 vs 1,63** | Marka priminin çarpan bazında BÜYÜKLÜĞÜ, metriğe göre DEĞİŞKENLİK | Ch.12, s.544-545 |
| EV/Satış~faaliyet marjı regresyonu (içecek sektörü) | Katsayı **+0,1328**/1% marj | Coca-Cola/Cott marj farkına (%25,94 vs %8,80) UYGULANDIĞINDA marka değeri tahmini | Ch.12, s.545-546 |
| Avonex patent opsiyonu (İllüstrasyon 12.5) | NPV **$547mn** vs OPSİYON değeri **$907mn** (zaman primi $360mn) | Opsiyon değerinin NPV'yi NE KADAR AŞABİLECEĞİNİN somut kanıtı | Ch.12, s.550-551 |
| Gulf Oil rezerv değerlemesi (İllüstrasyon 12.7, 1984) | DCF **$12mlr** vs opsiyon değeri (Black-Scholes) ÇOK DAHA YÜKSEK; hisse **$70**'te AŞIRI DEĞERLİ bulundu | Doğal kaynak opsiyon değerlemesinin somut M&A uygulaması | Ch.12, s.558-560 |
| AmBev/Guaraná genişleme opsiyonu (İllüstrasyon 12.8) | İlk yatırım NPV **-$100mn**, genişleme opsiyonu değeri **$203mn** (net: yatırım YAPILMALI) | Negatif-NPV ilk yatırımın opsiyon değeriyle NASIL haklı çıkabileceğinin somut örneği | Ch.12, s.562-564 |
| AmBev opsiyonu, PV TAVANLI (rekabet varsayımıyla) | Değer **$203mn → $142mn**'e DÜŞER | Exclusivite eksikliğinin (rakip taklidi) değeri NE KADAR AŞINDIRDIĞI | Ch.12, s.567 |
| Rediff.com genişleme opsiyonu (İllüstrasyon 12.9) | DCF değeri **$474mn** + opsiyon değeri **$155mn** = TOPLAM firma değeri | | Ch.12, s.568-569 |
| Airbus/Lear terk opsiyonu (İllüstrasyon 12.10) | İlk yatırım NPV **-$20mn**, PUT opsiyonu değeri bunu AŞARAK ortak girişimi CAZİP hale getiriyor | Terk opsiyonunun negatif-NPV projeyi NASIL kabul edilebilir yaptığının somut örneği | Ch.12, s.570-571 |

## Kontrol listeleri (devam)

**Kontrol Listesi Y — Opsiyonları DCF Değerine Dahil Etmenin 4 Yöntemi, KALİTE SIRASI (Ch.11, s.494-498):**
1. Tam seyreltilmiş hisse — EN ZAYIF (kullanım GELİRİNİ ve ZAMAN PRİMİNİ yok sayar, TÜM opsiyonları AYRIM GÖZETMEDEN sayar).
2. Gelecek kullanım tahmini — İMPRATİK (DAİRESEL/gelecek piyasa fiyatı tahmini gerektirir).
3. Treasury stock yaklaşımı — kullanım geliri EKLENİR ama zaman primi/vesting HALA yok, DEĞERİ ABARTMA eğilimi.
4. Opsiyon adil değer yaklaşımı — EN DOĞRU (opsiyonlar fiyatlama modeliyle değerlenip özkaynaktan DÜŞÜLÜR).

**Kontrol Listesi Z — Çalışan Opsiyonu Değerlemesinde 5 Ölçüm Sorunu (Ch.11, s.498-502):**
1. VESTING (henüz hak edilmemiş olma/HİÇ hak edilmeme olasılığı).
2. LİKİT OLMAMA (erken kullanıma yol açar — model VADESİ kısaltılmalı, TİPİK OLARAK YARIYA).
3. HANGİ HİSSE FİYATI kullanılacak (piyasa fiyatı mı tahmini DEĞER mi — DAİRESEL, İTERASYONLA çözülür).
4. VERGİ (kullanımda vergi indirimi — 3 yöntemle modele DAHİL edilebilir).
5. HALKA AÇIK OLMAYAN firmalar (fiyat/varyans GÖZLEMLENEMEZ — treasury stock VEYA benzer halka açık firma varyansı kullanılır).

**Kontrol Listesi AA — Genişleme Opsiyonunun Değerli Olma Testi, 3 Soru (Ch.12, s.564-567):**
1. İlk yatırım, ikinci (genişleme) yatırım için GERÇEK bir ÖN KOŞUL MU (yoksa sadece gevşek bir bağlantı mı)?
2. Firmanın ikinci yatırıma EXCLUSİVE (veya en azından belirgin AVANTAJLI) erişimi VAR MI, yoksa rakipler KOLAYCA TAKLİT edebilir mi?
3. Ortaya çıkacak rekabet avantajı NE KADAR SÜRDÜRÜLEBİLİR (sektör rekabet YOĞUNLUĞU + avantajın DOĞASI — kıt kaynak vs ilk-hamle/teknoloji)?

**Kontrol Listesi BB — Kısıtlı Hisse (Restricted Stock) İskonto Belirleyicileri, 3 Faktör (Ch.11, s.520):**
1. Likit olmama PERİYODUNUN uzunluğu (uzun=büyük iskonto).
2. Hedge/borçlanma KISITLARI (sıkı=büyük iskonto).
3. Hisse OYNAKLIĞI (yüksek=büyük iskonto).

## Kırmızı bayraklar (devam)

- **BAYRAK-35 — Birincil (Primary) HBK ile P/E Hesaplama:** Fiyat ZATEN opsiyon seyreltmesini yansıtırken (piyasa fiyatı DÜŞÜKTÜR), payda (birincil HBK) potansiyel seyrelmeyi YANSITMAZ — bu, YÜKSEK opsiyon örtüsü olan firmaları SİSTEMATİK OLARAK "ucuz" gösterir. Opsiyon giderleştirmesine geçilse BİLE bu yanlılık KAYBOLMAZ (SADECE payda değişir, PAY'daki fiyat-seyreltme etkisi HALA vardır). Nasıl tespit edilir: P/E hesabında kullanılan HBK'nın birincil mi tam-seyreltilmiş mi olduğu VE opsiyon adil değerinin piyasa değerine EKLENİP eklenmediği kontrol edilmeli. Gereken veri: çalışan opsiyon sayısı+kullanım fiyatı+adil değeri — **VERİ EKSİK** (QuaxisLabs bağlamında NOT: BIST'te bu programlar NADIR olduğundan pratik önemi DÜŞÜK, NASDAQ kapsamında DAHA İLGİLİ). (Ch.11, s.507-508)
- **BAYRAK-36 — Tam Seyreltilmiş HBK'nın TÜM Opsiyonları Eşit Cezalandırması:** Tam seyreltilmiş HBK, 3 hafta sonra vadesi dolacak DERİN para-dışı opsiyonla, 5 yıl vadeli DERİN para-içi opsiyonu AYNI (bir hisse) birimle CEZALANDIRIR — oysa değere etkileri ÇOK FARKLIDIR; bu, ÇOK opsiyonu olan ama BÜYÜK ÇOĞUNLUĞU para-DIŞI firmaları GEREĞİNDEN FAZLA cezalandırıp YAPAY OLARAK "pahalı" gösterebilir. Nasıl tespit edilir: kullanılan seyreltilmiş hisse sayısının SADECE opsiyon SAYISINI mı yoksa opsiyonların DEĞERİNİ mi yansıttığı kontrol edilmeli. (Ch.11, s.507)
- **BAYRAK-37 — Marka Değerinde Metrik Seçimine Göre Aşırı Değişken Sonuç:** Aynı marka firması için farklı ölçek değişkenleri (Satış/FAVÖK/Sermaye) kullanmak GENİŞ ARALIKTA farklı marka değeri tahminleri üretir (somut örnek: Coca-Cola/Cott kıyasında Satış-bazlı EV çarpanı farkı EBITDA-bazlı farktan BELİRGİN ÖLÇÜDE geniştir) — TEK bir metriğe DAYALI marka değeri iddiası ŞÜPHEYLE karşılanmalı. Nasıl tespit edilir: birden fazla ölçek değişkeniyle çapraz KONTROL yapılıp YAPILMADIĞI sorgulanmalı. (Ch.12, s.544-545)
- **BAYRAK-38 — Şerefiyenin (Goodwill) "Akıllı" ve "Aptal" Bileşenlerinin Ayrıştırılmaması:** Şerefiye rakamının TAMAMI (fazla-ödeme dahil) sermaye getirisi (ROC) hesabına DAHİL edilirse, GERÇEKTE kötü bir satın alma yapmış firmanın ROC'si YAPAY OLARAK DÜŞÜK, buna KARŞILIK organik büyüyen (şerefiyesi az) bir rakip firma YAPAY OLARAK YÜKSEK ROC'lü görünür — bu, iki firmanın YATIRIM KALİTESİ kıyasını BOZAR. Nasıl tespit edilir: ROC hesabında kullanılan "yatırılan sermaye"nin şerefiyeyi İÇERİP içermediği VE şerefiyenin büyük kısmının SATIN ALMA-ağırlıklı büyüme mi yoksa organik mi olduğu kontrol edilmeli. Gereken veri: goodwill standalone alan olarak (Buffett turunda da tespit edilmişti, bkz. `_ilerleme.md` Bilanço bölümü) QuaxisLabs'ta HALA YOK. (Ch.12, s.548-549)
- **BAYRAK-39 — Genişleme/Sinerji Opsiyonunun Nitel Gerekçeyle (Sayısal Değerleme Olmadan) Kullanılması:** Yöneticiler, YÜKSEK satın alma primlerini VEYA negatif-NPV yatırımları "stratejik opsiyon"/"sinerji" gerekçesiyle SAVUNURLARSA ama BU opsiyonu SAYISAL OLARAK değerlemezlerse, bu KIRMIZI BAYRAKTIR — "opsiyon değeri > maliyet" iddiası KANITLANMAMIŞ bir varsayımdır. Nasıl tespit edilir: bir satın alma/yatırım gerekçesinde "opsiyonalite"/"sinerji" TERİMİ geçiyor MU, geçiyorsa BUNUN İÇİN AYRI bir SAYISAL değerleme SUNULMUŞ MU kontrol et. Gereken veri: METODOLOJİK kontrol (yönetim SUNUMU/gerekçe metninin incelenmesi — LLM'e UYGUN nitel bir görev). (Ch.12, s.564-565)
- **BAYRAK-40 — Çift Sayım: Hem Gelecek Opsiyon Giderini Hem Seyreltmeyi AYNI ANDA Modelleme:** Gelecekteki opsiyon ihraçlarının hem OPERASYONEL GİDER olarak DÜŞÜLMESİ hem AYRICA hisse sayısının SEYRELTİLMİŞ varsayılması AYNI maliyetin İKİ KEZ sayılmasıdır. Nasıl tespit edilir: bir DCF modelinde gelecek opsiyon ihraçlarının hem gider satırı hem hisse-sayısı-artışı olarak AYRI AYRI modellenip modellenmediği kontrol edilmeli. Gereken veri: METODOLOJİK kontrol. (Ch.11, s.512-513)
- **BAYRAK-41 — Kısıtlı Hisse Sayısının İskontosuz Piyasa Değerine Dahil Edilmesi:** Kısıtlı hisseler NORMAL hisselerle AYNI birim fiyattan (piyasa fiyatı) çarpılıp piyasa değerine EKLENİRSE, kısıtlı hissenin GERÇEKTE daha DÜŞÜK (likit-olmama iskontolu) değerde olması nedeniyle piyasa değeri VE TÜM çarpanlar YUKARI YANLAR. Nasıl tespit edilir: piyasa değeri hesabında kısıtlı hisse ÖRTÜSÜNÜN önemli olup OLMADIĞI VE iskontolu hesaplanıp HESAPLANMADIĞI kontrol edilmeli. (Ch.11, s.522-523)

## Uygulama notları (devam)

**Nicel (skorlanabilir):**
- Bu Kısımda TESPİT EDİLEN düşük-maliyetli tek somut eklenti adayı YOK — Ch.11'in TÜMÜ çalışan opsiyonu VERİSİNE (QuaxisLabs'ta HİÇ TOPLANMIYOR), Ch.12'nin option-pricing kısmı PROJE-SEVİYESİ veriye (yapısal olarak QuaxisLabs'ın şirket-geneli veri modeliyle UYUMSUZ) bağlıdır.
- **BAYRAK-38 (goodwill akıllı/aptal ayrımı)** — goodwill standalone alanı EKLENİRSE (Buffett turundan beri BİLİNEN bir açık) bu bayrak DÜŞÜK ek maliyetle uygulanabilir hale gelir; şu an TEK BAŞINA goodwill VERİSİ bile YOK.
- **FORMÜL-121 mimari notu** — `merton.py`'nin Black-Scholes-Merton çerçevesi, gelecekte opsiyon-bazlı bir özellik EKLENİRSE (örn. yüksek büyümeli/patentli bir NASDAQ şirketinde genişleme opsiyonu) YENİDEN KULLANILABİLECEK bir matematiksel ÇEKİRDEKTİR — bu, KOD-MİMARİSİ seviyesinde bir gözlem, HEMEN uygulanabilir bir özellik DEĞİL.

**Nitel (LLM yorumuna uygun):**
- **BAYRAK-39 (nitel opsiyon/sinerji gerekçesi taraması)** — bu Kısmın EN UYGULANABİLİR nitel bulgusu: bir şirketin yönetim sunumlarında/faaliyet raporlarında "stratejik opsiyon", "sinerji", "gelecek potansiyel" gibi TERİMLERİN sayısal bir değerleme İLE DESTEKLENİP DESTEKLENMEDİĞİ LLM'e SORULABİLİR bir tarama görevidir — özellikle satın alma/büyük yatırım açıklamalarında.
- İnsan sermayesinin "kiralık" doğası (İLKE-269) — danışmanlık/finans-benzeri BIST şirketlerinde (aracı kurumlar, GYO yönetim şirketleri) anahtar personel BAĞIMLILIĞI riski LLM'e SORULABİLİR bir nitel değerlendirme.
- Terk/esneklik opsiyonu (İLKE-280) — bir şirketin sözleşme yapısının (kısa vs uzun vadeli, kiralama vs mülkiyet) LLM tarafından dipnotlardan OKUNARAK "esneklik" açısından NİTEL bir puanlama/yorum ÜRETİLEBİLİR.
- Marka entanglement uyarısı (İLKE-268) — çok-ürünlü/çok-markalı BIST holding şirketlerinde (örn. gıda/perakende grupları) marka değeri iddialarının GÜVENİLİRLİĞİNE dair LLM'e verilebilecek bir ŞÜPHECİLİK notu.

**Veri eksikliği / kapsam dışı nedeniyle UYGULANAMAZ:**
- **Ch.11'in TAMAMI (çalışan opsiyonu değerlemesi, FORMÜL-105-110)** — çalışan opsiyon programı verisi (sayı, kullanım fiyatı, vesting, adil değer) hiçbir fetcher'da YOK; BIST'te bu tür GENİŞ-TABANLI opsiyon programları NASDAQ'a göre ÇOK DAHA NADIR olduğundan pratik ÖNCELİK DÜŞÜK — ANCAK NASDAQ kapsamındaki 10 şirket (AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META, NFLX, AMD, PYPL) için bu KESİNLİKLE İLGİLİDİR ve veri (10-K/DEF14A dosyalarından) TEORİK OLARAK ÇEKİLEBİLİR — `sec_edgar.py` fetcher'ının GENİŞLETİLMESİ gerekir.
- **Marka/insan sermayesi tarihi maliyet+DCF yaklaşımları (FORMÜL-111-113)** — çok-yıllı reklam/Ar-Ge gideri serisi VE jenerik karşılaştırma firması seçimi MANUEL/analist-seviyesi işler; OTOMATİK skorlanamaz.
- **Sektör/piyasa regresyonu (FORMÜL-115)** — Kısım 4-5'teki AYNI mimari eksiklik.
- **YENİ bir "kapsam dışı" KATEGORİSİ netleşti — proje/varlık-seviyesi opsiyon değerlemesi (FORMÜL-116-120):** Patent, doğal kaynak rezervi, genişleme ve terk opsiyonlarının HEPSİ TEK bir proje/varlığın (şirketin TAMAMI değil) risk/nakit akışı VARSAYIMLARINI gerektirir — bu, QuaxisLabs'ın "şirket-geneli temel veri → skorlama" mimarisiyle YAPISAL OLARAK UYUŞMAYAN, İSTİSNAİ/analist-müdahaleli bir değerleme TÜRÜDÜR. Sektör/piyasa regresyonu (Kısım 4-5) "çok-firma karşılaştırma" eksikliğiyken, BU "tek-proje-derinlik" eksikliğidir — kitaplar arası ÜÇÜNCÜ FARKLI mimari eksiklik KATEGORİSİ olarak (VERİ eksikliği, ÇOK-FİRMA karşılaştırma eksikliği, TEK-PROJE derinlik eksikliği) netleşti.

---

# KISIM 7 — Chapter 13-14: The Value of Control + The Value of Liquidity

**Kapsam:** Chapter 13: The Value of Control (PDF s.591-645), Chapter 14: The Value of Liquidity (PDF s.646-705). ID numaralandırması Kısım 1-6'nın devamı (İLKE-285'ten, FORMÜL-124'ten, BAYRAK-42'den, Kontrol Listesi CC'den başlar; kesintisiz).

## İlkeler (devam)

**Chapter 13 — The Value of Control:**

- **İLKE-285 (Kontrol değerinin tanımı):** Kontrol değeri = firmanın OPTİMAL yönetilmiş değeri (Va) ile MEVCUT/status quo yönetimle değeri (Vb) arasındaki FARKTIR. Bu fark firma zaten optimal yönetiliyorsa SIFIR, kötü yönetiliyorsa BÜYÜK olabilir. (s.591-592)
- **İLKE-286 (Firma değerinin 5 belirleyicisi):** Mevcut varlıklardan nakit akışı (vergi+yeniden yatırım SONRASI, borç ödemesi ÖNCESİ), olağanüstü büyüme dönemindeki büyüme oranı, olağanüstü büyüme döneminin UZUNLUĞU, sermaye maliyeti, nakit/çapraz iştirak/faaliyet-dışı varlıklar. Bu 5 girdi Ch.1-6'daki DCF çerçevesinin AYNEN TEKRARIDIR — kontrol değerlemesi YENİ bir metodoloji DEĞİL, AYNI DCF'in status-quo/optimal İKİ FARKLI varsayım setiyle İKİ KEZ çalıştırılmasıdır. (s.592-594)
- **İLKE-287 (Mevcut varlıklardan değer artırmanın 4 kanalı):** (1) VARLIK YENİDEN KONUŞLANDIRMA (kötü performans gösteren varlıkları elden çıkar/daha yüksek değerli kullanıma taşı); (2) FAALİYET VERİMLİLİĞİ artırma (aşırı istihdamı azalt, eski ekipmanı yenile, düşük maliyetli bölgeye taşı); (3) VERGİ YÜKÜ azaltma (yasal sınırlar içinde); (4) SERMAYE BAKIMI/işletme sermayesi yatırımlarını azaltma (sektör ortalamasının üzerindeki envanter seviyelerini düşürme). (s.595-596)
- **İLKE-288 (Büyüme artırmanın 2 kanalı):** YENİ YATIRIMLARLA (yeniden yatırım oranı × sermaye getirisi — getiri sermaye maliyetinin ÜZERİNDEYSE değer artar, ALTINDAYSA yeniden yatırım oranını artırmak DEĞERİ DÜŞÜRÜR) veya MEVCUT VARLIKLARI daha verimli yöneterek (bu kanalın etkisi HER ZAMAN tek anlamlı OLUMLUDUR). Hangi kanal DAHA ÖNCELİKLİ firma tipine bağlıdır: olgun/düşük-getirili firmalarda mevcut-varlık-verimliliği DAHA HIZLI sonuç verir; küçük/az-varlıklı firmalarda yeni yatırım ŞARTTIR. (s.596-597)
- **İLKE-289 (Yüksek büyüme dönemini uzatma):** Hiçbir firma REKABETÇİ bir piyasada SINIRSIZ süre fazla getiri kazanamaz — yüksek büyüme+fazla getiri varsayımı ZIMNEN giriş engellerinin VARLIĞINI gerektirir. Değer artırmanın bir yolu MEVCUT giriş engellerini GÜÇLENDİRMEK veya YENİ rekabet avantajları YARATMAKTIR. (s.597-598)
- **İLKE-290 (Sermaye maliyetini düşürmenin 4 yolu):** (1) ürün/hizmetleri DAHA AZ isteğe bağlı (discretionary) hale getirme; (2) FAALİYET KALDIRACINI azaltma (sabit maliyet oranını düşürme); (3) FİNANSMAN KARIŞIMINI değiştirme (borç HER ZAMAN özkaynaktan UCUZDUR ama artan borç HEM borç HEM özkaynak maliyetini YÜKSELTİR — OPTİMAL borç oranı sermaye maliyetinin MİNİMİZE edildiği noktadır); (4) FİNANSMANI VARLIKLARLA EŞLEŞTİRME (kısa vadeli borçla uzun vadeli varlık finanse etmek, para birimi/faiz tipi uyuşmazlığı — TÜMÜ default riskini/sermaye maliyetini YÜKSELTİR). (s.598-599)
- **İLKE-291 (Faaliyet-dışı varlık yönetimi):** Nakit/menkul kıymet ve çapraz iştirak tutmanın KONVANSİYONEL varsayımı NÖTRDÜR — ama (a) piyasa-altı getiriyle tutuluyorsa VEYA (b) yönetimin KÖTÜYE KULLANMA (kötü satın alma) OLASILIĞI VARSA piyasa BUNA İSKONTO uygular; bu durumda temettü/geri alım yoluyla nakdi İADE ETMEK değeri ARTIRIR. Çapraz iştirak/holding YAPISI benzer bir "konglomera iskontosu" taşıyabilir — bölünme/elden çıkarma bu değeri AÇIĞA ÇIKARABİLİR. [→ FORMÜL-124, BAYRAK-53] (s.599-601)
- **İLKE-292 (Değişen yönetimin değeri):** Optimal Değer − Status Quo Değer formülüyle YAZILIR; kötü yönetilen firmada BÜYÜK, zaten optimal yönetilen firmada SIFIRDIR. Değer artırma YOLU firmaya göre değişir: varlık yönetimi kötüyse verimlilik artışından, finansman politikası kötüyse sermaye maliyeti düşüşünden gelir. (s.601) [→ FORMÜL-125]
- **İLKE-293 (Yönetim değişikliğinin 4 mekanizması):** (1) AKTİVİST kurumsal yatırımcı baskısı (hissedar önerileri — çoğunluk desteği NADİREN alır, düşük başarı oranı); (2) VEKALET (proxy) MÜCADELESİ (kötü yönetilen firmalarda DAHA SIK, somut politika değişikliğine yol açar); (3) ZORUNLU CEO DEĞİŞİKLİĞİ (küçük/dışarıdan-üyeli kurullarda, CEO≠başkan firmalarda DAHA SIK); (4) DÜŞMANCA DEVRALMA (en ETKİLİ ama en NADİR mekanizma). (s.609-612)
- **İLKE-294 (Yönetim değişikliğini ZORLAŞTIRAN kurumsal engeller):** SERMAYE KISITLARI (gelişmiş tahvil/kredi piyasası OLMAYAN ekonomilerde düşmanca devralma NADİRdir; büyük piyasa değerli firmalar sermaye kısıtından DAHA FAZLA korunur); DEVLET KISITLAMALARI (Pennsylvania 1989 yasası örneği — oy hakkı eşiği, çoklu paydaş değerlendirmesi, kâr iade zorunluluğu); ATALET/ÇIKAR ÇATIŞMASI (kurumsal yatırımcıların ÇOĞU pasiftir, hisse SATAR, yönetime KARŞI OY vermez). (s.612-614)
- **İLKE-295 (Firma-özel engeller):** KURUMSAL TÜZÜK DEĞİŞİKLİKLERİ (staggered board, süper çoğunluk şartı — ampirik kanıt KARIŞIKTIR); FARKLI OY HAKKI SINIFLARI (Latin Amerika/Avrupa'da YAYGIN); KURUMSAL HOLDİNG YAPILARI (piramit — X, Y'nin %50'sine sahip, Y de Z'yi kontrol eder; ÇAPRAZ İŞTİRAK — %50'DEN AZ'la TAM kontrol sağlar, Japon keiretsu/Kore chaebol örnekleri); BÜYÜK HİSSEDAR/YÖNETİCİ (kurucu-CEO'nun büyük hisse payı düşmanca devralmayı ETKİSİZ kılar). (s.614-617)
- **İLKE-296 (Yönetim değişikliği olasılığını KAYDIRAN 3 faktör):** kurumsal yönetişim KURALLARININ zamanla değişmesi; AKTİVİST YATIRIMCILARIN piyasaya girişi; İYİ TANITILMIŞ bir düşmanca devralma/CEO görevden alma OLAYININ tüm piyasadaki algıyı DEĞİŞTİRMESİ (bulaşıcı etki — bir sektördeki devralma, AYNI sektördeki DİĞER firmaların fiyatını da ETKİLER). (s.617-618)
- **İLKE-297 (Kontrol priminin 4 çıkarımı):** kontrol değeri FİRMADAN FİRMAYA DEĞİŞİR; SABİT bir kural-of-thumb OLAMAZ ("kontrol her zaman değerin %20-30'udur" iddiası YANLIŞTIR); kontrol primi firmanın KÖTÜ PERFORMANS NEDENİNE göre değişir (yönetim hatasıysa YÜKSEK, dışsal faktörse [emtia fiyatı vb.] DÜŞÜK olmalı); kontrol primi yönetim değişikliğinin NE KADAR KOLAY yapılabileceğinin fonksiyonudur (finansman karışımı değişikliği HIZLI, fabrika modernizasyonu YAVAŞTIR). (s.620-621) [→ BAYRAK-42]
- **İLKE-298 (Düşmanca devralmalarda kontrol priminin 3 adımlı değerlemesi):** (1) STATUS QUO değerleme; (2) YENİDEN YAPILANDIRILMIŞ değerleme (alıcının planladığı değişikliklerle); (3) FARKIN (kontrol değeri) NE KADARININ satın alma fiyatına YANSITILACAĞININ belirlenmesi (TAMAMINI ödemek, TÜM kontrol değerini hedef hissedarlarına VERİR). (s.620)
- **İLKE-299 (Kontrol vs sinerji ayrımı — KESİN):** Kontrol değeri sinerjiyle KARIŞTIRILMAMALIDIR — sinerji İKİ ayrı tüzel kişiliğin (alıcı+hedef) VARLIĞINI gerektirir ve BİRLEŞİK firmaya avantaj olarak tahakkuk eder; kontrol İSE TAMAMEN hedef firmada bulunur ve alıcı firma GEREKTİRMEZ. Bir birleşmede sinerji varsa, bu kontrol değerine EK olarak gelir, YERİNE GEÇMEZ. (s.620)
- **İLKE-300 (Kontrol değerinin ampirik kanıtı — 3 kategori):** (1) düşmanca devralmalarda ödenen PRİMLER (ABD'de 1980-1990'larda %20-30 — ama bu prim kontrol+sinerji+FAZLA ÖDEMENİN karışımıdır, TEK BAŞINA kontrolü YANSITMAZ); (2) HEDEF FİRMA ÖZELLİKLERİ (düşmanca devralma hedefleri sektörden %2,2 DÜŞÜK ROE, piyasadan %4 DÜŞÜK getiri, sadece %6,5 içeriden sahiplik taşır); (3) DEVRALMA SONRASI eylemler (%60'ında büyük elden çıkarma, 19 devralmanın 17'sinde yönetim değişikliği — YAYGIN İNANCIN aksine varlık soygunu NADİRDİR). (s.621-624)
- **İLKE-301 (Piyasa fiyatları zaten beklenen kontrol değerini İÇERİR):** Halka açık her firmanın hisse fiyatı, yönetimin değişme OLASILIĞI × değişimin YARATACAĞI değer = beklenen kontrol değerini ZATEN yansıtır. SONUÇ: piyasa fiyatı ÜZERİNE prim ödemek FAZLA ÖDEMEYE yol açabilir — piyasa zaten %90 yönetim değişikliği olasılığı fiyatlıyorsa, ek bir "kötü yönetiliyor" primi ödemek ÇİFTE SAYIMDIR. [→ BAYRAK-43] (s.624-625)
- **İLKE-302 (Kötü kurumsal yönetişim = düşük fiyat):** Kurumsal yönetişimin ÖZÜ, hissedarlara kötü yöneticileri DEĞİŞTİRME GÜCÜ vermesidir — bu güç GÜÇLÜYSE piyasa YÜKSEK beklenen kontrol değeri fiyatlar, ZAYIFSA DÜŞÜK. Gompers/Ishi/Metrick (2003): en zayıf hissedar gücüne sahip hisseler en güçlü olanlardan yıllık %8,4 DAHA AZ getiri sağlamış; yönetişim endeksindeki her %1'lik kötüleşme Tobin's Q'yu %2,4 DÜŞÜRMÜŞ. (s.627-628)
- **İLKE-303 (Oy hakkı primi = beklenen kontrol değerinin PAYLAŞIMI):** Oysuz hisse SADECE status quo değeri yansıtır (kontrol değişikliğinde söz hakkı YOKTUR); oylu hisse ise beklenen kontrol değerini de İÇERİR. (s.629-630) [→ FORMÜL-126]
- **İLKE-304 (Oy hakkı primi — 4 çıkarım):** yönetim değişikliği OLASILIĞI SIFIRSA (tüm oylu hisseler insider'da) fark SIFIRA yakınsar; kötü yönetilen firmalarda prim İYİ yönetilenden DAHA BÜYÜKTÜR; oylu hisse SAYISI AZALDIKÇA BİREYSEL prim ARTAR (ama bu genelde İÇERİDEN sahipliğin de yoğunlaşmasıyla DENGELENİR); halka açık (float) oylu hisse ORANI ARTTIKÇA prim ARTAR. (s.630-632)
- **İLKE-305 (Oy hakkı primi ampirik bulguları — ülkeye göre BÜYÜK FARK):** ABD'de KÜÇÜK (%5-10, bazı dönemlerde İSKONTOLU — oylu hissenin GÖRECELİ İLLİKİDİTESİ nedeniyle), Latin Amerika/İsrail/İtalya'da ÇOK DAHA BÜYÜK — Nenova (2000, 18 ülke): fark BÜYÜK ÖLÇÜDE hukuki koruma GÜÇLÜLÜĞÜYLE açıklanır. Yasal reformlar DOĞRUDAN etki eder (İtalya/Brezilya örnekleri). (s.632-633)
- **İLKE-306 (Özel şirket değerlemesinde kontrol):** Tek-sahipli özel şirkette düşmanca devralma MÜMKÜN DEĞİLDİR — kontrol değeri SADECE şirket kısmen/tamamen SATILDIĞINDA konu olur. Çoklu ortaklı özel şirketlerde ÇOĞUNLUK payı AZINLIK payına göre PRİMLİDİR. (s.634)
- **İLKE-307 (Azınlık iskontosu/kontrol primi çerçevesi):** %51 payı SATIN ALAN, optimal DEĞERİN %51'ini ödemeye HAZIR olmalı; %49 (azınlık, kontrolsüz) payı ALAN, SADECE status quo DEĞERİN %49'unu ödemeye HAZIR olmalı — oy hakkındaki KÜÇÜK bir fark BÜYÜK bir değer farkına yol açabilir. (s.634-635) [→ FORMÜL-127]
- **İLKE-308 (Kontrol %51 GEREKTİRMEZ):** Dağınık sahiplikli çoklu-yatırımcılı bir özel firmada %35 gibi DÜŞÜK bir payla dahi ETKİN kontrol mümkündür — azınlık iskontosu, sahiplik payının ÇOK DAHA KÜÇÜK bir yüzdesine düşene kadar MATERYALLEŞMEYEBİLİR. Halka açık, geniş dağılımlı firmalarda kontrol DAHA DA KÜÇÜK payla mümkün olabilir. (s.636)
- **İLKE-309 (Özel sermaye/risk sermayesi yatırımcısının kontrol payı):** Bir hisse payının DEĞERİ, sahibine firmanın YÖNETİLME BİÇİMİNDE SÖZ HAKKI verip VERMEDİĞİNE bağlıdır — aktif VC/PE yatırımcıları kontrol değerini KENDİ payına DAHİL eder; pasif özel sermaye yatırımcıları payını DAHA DÜŞÜK değerlemelidir. (s.636)
- **İLKE-310 (Azınlık iskontosu ampirik büyüklüğü):** Pratikte %15-20 çoğunluk primi/eşdeğer azınlık iskontosu YAYGINDIR; Harouna/Sarin/Shapiro (2001): azınlık işlemler piyasa-odaklı ekonomilerde (İngiltere/ABD) çoğunluk işlemlerine göre %20-30 İSKONTOLUDUR, banka-odaklı ekonomilerde (Almanya/Japonya/Fransa/İtalya) DAHA KÜÇÜKTÜR; büyük blok işlemleri (%50'nin ALTINDA bile) %10'un ÜZERİNDE prim taşır, blok BÜYÜDÜKÇE prim ARTAR. (s.637)

**Chapter 14 — The Value of Liquidity:**

- **İLKE-311 (İlliкiditenin maliyeti = "buyer's remorse"):** Her varlık, YETERİNCE düşük bir fiyat kabul edilirse SATILABİLİR — varlıklar likit/likit-olmayan İKİLİ kategoriye AYRILMAMALI, bir İLLİKİDİTE SÜREKLİLİĞİ (continuum) üzerinde değerlendirilmelidir. Maliyet, ağır işlem gören halka açık hissede KÜÇÜK, özel işletmede EN BÜYÜKTÜR; reel varlıklarda finansal varlıklardan DAHA YÜKSEKTİR. (s.646)
- **İLKE-312 (İşlem maliyetinin 3 gizli bileşeni — komisyon HARİCİNDE):** (1) ALIŞ-SATIŞ FARKI (bid-ask spread); (2) FİYAT ETKİSİ (büyük işlem fiyatı KENDİ ALEYHİNE hareket ettirir); (3) BEKLEME FIRSAT MALİYETİ (Treynor) — sabırlı işlem yapmak ilk ikisini AZALTIR ama bekleme SIRASINDA kârlı fırsatlar KAYBEDİLEBİLİR. (s.646-647)
- **İLKE-313 (Alış-satış farkının 3 nedeni):** STOK MALİYETİ (piyasa yapıcısı istenmeyen envanter pozisyonuna karşı korunur), İŞLEM MALİYETİ (evrak/ücret — sabit maliyet payı DÜŞÜK fiyatlı hisselerde YÜZDE olarak DAHA YÜKSEKTİR), TERS SEÇİM PROBLEMİ (piyasa yapıcısı BİLGİLİ yatırımcıyla İŞLEM yapma RİSKİNE karşı spread'i GENİŞLETİR). (s.647-649)
- **İLKE-314 (Alış-satış farkının büyüklüğü büyük ölçüde DEĞİŞİR):** Ortalama NYSE spread'i (1996) görünüşte küçüktür ama YÜZDE olarak küçük-piyasa-değerli hisselerde çok DAHA BÜYÜK, büyük-piyasa-değerli hisselerde çok DAHA KÜÇÜKTÜR; işlem hacmi DÜŞÜK hisselerde spread YÜKSEK, NASDAQ'ta NYSE'den DAHA YÜKSEKTİR. [→ EŞİK tablosu] (s.649-651)
- **İLKE-315 (Spread'in belirleyicileri):** Spread (yüzde olarak) fiyat SEVİYESİ, işlem HACMİ ve piyasa yapıcısı SAYISIYLA NEGATİF; OYNAKLIKLA POZİTİF korelelidir. FİRMALAR bilgi açıklama KALİTESİNİ artırarak spread'i AZALTABİLİR. Büyük işlemler spread'i GENİŞLETİR (bilgi içerme olasılığı yüksektir). (s.651-653)
- **İLKE-316 (Piyasa mikroyapısı spread'i etkiler):** NASDAQ'ta spread'ler, AYNI hacim/fiyat kontrolüne RAĞMEN, NYSE'den TARİHSEL OLARAK DAHA YÜKSEK bulunmuştur — kısmen dealer İŞBİRLİĞİ, kısmen YAPISAL farklar (limit emirlerinin spread'e yansıtılıp yansıtılmaması). Ondalık fiyatlamaya GEÇİŞ küçük/az-likit hisselerde spread'i AZALTTI, likit hisselerde BELİRGİN ETKİ YAPMADI. (s.652-653)
- **İLKE-317 (Fiyat etkisinin 2 nedeni):** PİYASA TAM LİKİT DEĞİLDİR (büyük işlem GEÇİCİ dengesizlik yaratır, likidite geri dönünce TERSİNE DÖNER) ve BİLGİSELDİR (büyük işlem BİLGİ SAHİBİ bir yatırımcının işlemi OLABİLECEĞİ algısı yaratır — bu etki GENELDE KALICIDIR). (s.653-654)
- **İLKE-318 (Fiyat etkisinin büyüklüğü ve belirleyicileri):** Büyük borsa-tabanlı blok işlemlerinde fiyat DAKİKALAR içinde AYARLANIR ama KÜÇÜK/AZ-likit hisselerde etki DAHA BÜYÜK ve düzeltme DAHA YAVAŞTIR; blok ALIMLARINDA fiyat genelde YÜKSEK KALIR, blok SATIŞLARINDA fiyat GERİ SIÇRAR (asimetri); fiyat etkisi büyük piyasa değerli firmalarda MUTLAK işlem BÜYÜKLÜĞÜNE göre KÜÇÜK ama YÜZDE büyüklüğe göre DAHA BÜYÜKTÜR; önceki çeyrekte yüksek hacimli/pozitif momentum'lu ve yüksek kurumsal sahiplikli firmalarda DAHA KÜÇÜKTÜR. (s.654-657)
- **İLKE-319 (Bekleme fırsat maliyetinin 4 belirleyicisi):** ÖZEL bilgiye DAYALI stratejilerde KAMUYA açık bilgiye göre DAHA YÜKSEK; AKTİF bilgi arayışı OLAN piyasalarda DAHA YÜKSEK; KISA VADELİ stratejilerde UZUN VADELİDEN DAHA YÜKSEK; MOMENTUM stratejilerinde KONTRARYAN stratejilerden DAHA YÜKSEK. (s.657-658)
- **İLKE-320 (Nontraded varlıklarda işlem maliyeti DAHA YÜKSEKTİR):** Emtia (standart birim) EN DÜŞÜK; gayrimenkulde komisyon %5-6; sanat eserinde %15-20'ye kadar (AZ aracı, standart-olmayan ürün). Özel işletme SATIŞ maliyeti EN YÜKSEK/PROHİBİTİFTİR — bu KÜÇÜK özel şirket paylarına da YANSIR (VC/PE yatırımcıları illikiditeyi fiyatlamalıdır). (s.659-660)
- **İLKE-321 (İlliкidite teorisinin 3 yaklaşımı):** (1) DEĞER İSKONTOSU — varlık değeri, GELECEKTEKİ işlem maliyetlerinin bugünkü DEĞERİ kadar AZALTILIR; (2) İSKONTO ORANI AYARLAMASI — gerekli getiri illikidite için AYARLANIR; (3) OPSİYON OLARAK DEĞERLEME — illikidite kaybı, varlığı EN YÜKSEK fiyattayken satamama OPSİYONU olarak modellenir. ÜÇÜ DE illikid varlığın likit muadilinden DAHA DÜŞÜK fiyatlanması SONUCUNA varır. (s.660)
- **İLKE-322 (İlliкidite iskontosu tutma süresine BAĞLIDIR):** Vayanos (1998) — yatırımcılar İŞLEM maliyeti ARTTIKÇA tutma sürelerini AYARLAR, bu yüzden Amihud-Mendelson'un TAHMİN ettiğinden DAHA KÜÇÜK bir fiyat etkisi ortaya çıkabilir. Genel sonuç: AYNI işlem maliyeti için iskonto, UZUN vadeli yatırımcılarda KISA vadelilerden DAHA KÜÇÜKTÜR. (s.660-661)
- **İLKE-323 (Likidite riski sistematik/kovaryans temellidir):** Acharya&Pedersen (2005) — bir varlığın NE KADAR illikid olduğu DEĞİL, NE ZAMAN illikid olduğu ÖNEMLİDİR — piyasa GENELİ illikidken illikid olan bir varlık (genelde düşen piyasa/resesyonla ÇAKIŞIR) DAHA YÜKSEK beklenen getiri gerektirir. Pastor&Stambaugh (2003): piyasa likiditesine DUYARLI hisseler, DUYARSIZ olanlardan belirgin ÖLÇÜDE DAHA YÜKSEK getiri sağlamıştır. [→ EŞİK tablosu] (s.661-662)
- **İLKE-324 (Ampirik proxy'ler — spread/devir hızı getiriyi AÇIKLAR):** Amihud&Mendelson (1989), Datar/Naik/Radcliffe (1998), Amihud (2002) — spread/devir hızı/fiyat-değişimi-hacim ORANI (illikidite ölçütleri) TUTARLI biçimde getiriyle İLİŞKİLİDİR: illikid hisseler DAHA YÜKSEK beklenen getiri sağlar. [→ FORMÜL-129/130] (s.662-663)
- **İLKE-325 (İlliкidite bir OPSİYON olarak — üst sınır):** Longstaff (1995) — MÜKEMMEL zamanlamaya sahip bir yatırımcının look-back opsiyonu, illikidite değerinin ÜST SINIRINI verir; gerçek yatırımcılar mükemmel zamanlama YAPAMAYACAĞINDAN gerçek illikidite maliyeti bu ÜST SINIRDAN DAHA DÜŞÜKTÜR. İlliкidite maliyeti, YÜKSEK OYNAKLIKLI varlıklarda ve UZUN kısıtlama sürelerinde DAHA BÜYÜKTÜR. [→ FORMÜL-131] (s.664-665)
- **İLKE-326 (Tahvil piyasasında likidite primi RİSKLİLİKLE ARTAR):** Hazine bonosu/tahvili arasında bile likidite farkı FİYATLANIR; kurumsal tahvillerde spread ARTAR — SPEKÜLATİF dereceli tahvillerde likidite YATIRIM dereceliye göre ÇOK DAHA ÖNEMLİDİR. [→ EŞİK tablosu] (s.666-667)
- **İLKE-327 (Hisse senedi piyasasında likidite risk priminin ZAMANLA DEĞİŞİMİ):** Jones (2002) — Dow Jones hisselerinde 1900-2000 işlem maliyetleri BUGÜN 1990'ların BAŞINDAN DAHA DÜŞÜKTÜR, bu KISMEN düşen özkaynak risk priminin AÇIKLAYICISI olabilir; spread genişlemesi/devir hızı düşüşü GELECEKTEKİ yüksek getirinin habercisidir. (s.667-668)
- **İLKE-328 (Kontrollü işlem farkları — EN GÜVENİLİR kanıt kaynağı):** AYNI şirketin farklı likiditede paylarını KIYASLAMAK (kısıtlı hisse vs serbest hisse, halka arz öncesi vs sonrası fiyat, aynı şirketin farklı sınıf hisseleri) diğer FAKTÖRLERİ (boyut, risk) sabit tutarak SADECE likidite etkisini İZOLE eder. (s.668-669)
- **İLKE-329 (Kısıtlı hisse iskontosu — YAYGIN ama SORUNLU kanıt tabanı):** Restricted stock çalışmaları %25-35 aralığında bir iskonto RAPORLAR (küçük/az-sağlıklı firmalarda ve büyük bloklarda DAHA BÜYÜK) — ama KÜÇÜK örneklem, seçim ÖNYARGISI ve HİZMET BEDELİ karıştırma sorunları TAŞIR. TESCİLLİ ile TESCİLSİZ özel yerleştirme KIYASI (SADECE ikincisinde likidite kısıtı VARDIR) DAHA TEMİZ bir tahmin sağlar — diğer faktörler kontrol edildiğinde saf illikidite iskontosu ÇOK DAHA KÜÇÜK (~%7-10) çıkar. [→ EŞİK tablosu] (s.669-671)
- **İLKE-330 (IPO-öncesi işlem fiyatı kıyası — BÜYÜK ama ŞÜPHEYLE karşılanmalı):** IPO öncesi işlem fiyatlarına göre %32-75 arasında raporlanan iskontolar, YAZAR tarafından SAF likidite iskontosundan ÇOK, BAŞKA faktörleri (bilgi asimetrisi, IPO fiyatlama süreci) YANSITTIĞI ŞEKLİNDE YORUMLANIR — BU KADAR BÜYÜK bir iskontonun rasyonel bir yatırımcı tarafından KABULÜ mantık DIŞI görünür. (s.671-672)
- **İLKE-331 (Aynı şirketin farklı hisse sınıfları — likidite+bilgi karışımı):** Çin RIS (kısıtlı kurumsal) vs adi hisse kıyası EN YÜKSEK gözlenen iskontoyu (küçük/oynak firmalarda DAHA BÜYÜK) verir; A/B hisse sınıfı farkı İSE KISMEN likidite, BÜYÜK ÖLÇÜDE bilgi ASİMETRİSİNE atfedilir — TEK bir fiyat farkının "SAF likidite" olarak yorumlanması genellikle HATALIDIR. (s.672-673)
- **İLKE-332 (Özel sermaye/VC illikidite primi — SAF illikidite DEĞİL):** Özel sermaye yatırımcılarının halka açık piyasaya göre fazla getirisi, HEM illikiditeyi HEM çeşitlendirilmeme (nondiversification) primini HEM kontrol primini İÇEREN bir KARIŞIMDIR, SADECE likidite DEĞİLDİR — erken/geç aşama VC yatırımlarında iskonto BÜYÜKLÜĞÜ ÇOK FARKLIDIR (erken aşama ÇOK DAHA YÜKSEK). [→ EŞİK tablosu] (s.673-674)
- **İLKE-333 (Sabit iskonto pratiğinin ZAYIFLIĞI ve firma-özel 5 belirleyici):** SABİT bir illikidite iskontosu (VEYA dar bir "analist takdirine" bırakılmış ARALIK) kullanmak YAYGIN pratiktir ama TEORİK/AMPİRİK olarak firma-özel belirleyicileri GÖZ ARDI eder — 5 belirleyici: (1) firmanın SAHİP OLDUĞU varlıkların LİKİDİTESİ; (2) finansal SAĞLIK/nakit akışı; (3) GELECEKTE halka açılma OLASILIĞI; (4) FİRMA BÜYÜKLÜĞÜ; (5) KONTROL bileşeni (%51 payı %49'dan DAHA LİKİTTİR — kontrol VE likidite BİRBİRİYLE İÇ İÇE GEÇMİŞTİR). [→ KONTROL LİSTESİ EE] (s.675-678)
- **İLKE-334 (Firma-özel iskonto regresyonları — Silber/Bajaj):** Kısıtlı hisse/özel yerleştirme iskontosu; GELİR ARTTIKÇA AZALIR, blok oranı AZALDIKÇA AZALIR, kâr POZİTİFSE DAHA DÜŞÜKTÜR, DISTRESS (Altman Z düşükse) ARTAR. Regresyonların R²'si ORTA düzeydedir (%30-40) — geniş standart hata TAŞIR ama YİNE DE SABİT iskonto varsayımını REDDETMEK için YETERLİDİR. [→ FORMÜL-132/133] (s.678-681)
- **İLKE-335 (Sentetik alış-satış farkı yöntemi):** Halka açık hisselerin alış-satış farkı (gelir, kârlılık, nakit oranı, işlem hacmi FONKSİYONU olarak) regresyona TABİ tutulup, ÖZEL firma için işlem hacmi SIFIRA ayarlanarak bir "sentetik spread" TÜRETİLİR — bu, kısıtlı hisse/özel yerleştirme çalışmalarındaki KÜÇÜK örneklem sorununu AŞMAK için MÜMKÜN OLAN EN GENİŞ örneklemi kullanır. [→ FORMÜL-134] (s.681-682)
- **İLKE-336 (Opsiyon-bazlı iskonto — kavramsal KUSURLAR):** İlliкiditeyi bir PUT opsiyonu olarak modellemek İKİ temel HATA taşır: (1) likidite BUGÜNKÜ fiyattan satma HAKKI vermez, GÜNCEL PİYASA fiyatından satma HAKKI VERİR; (2) opsiyon fiyatlama modelleri SÜREKLİ fiyat hareketi/arbitraj VARSAYAR — illikid varlıklar için bu ZAYIF bir varsayımdır. Daha MAKUL bir alternatif: belirli bir kâr eşiği üzerinde satma DİSİPLİNİNİ engelleme OLASILIĞI × bu koşulun opsiyon değeri. [→ FORMÜL-135] (s.682-685)
- **İLKE-337 (İskonto oranı ayarlaması — 3 pratik yöntem):** (1) SABİT bir illikidite primi (küçük-firma priminin BİR KISMI veya VC-getiri FARKINA dayalı) TÜM illikid varlıklara EKLENİR — çifte-sayım RİSKİ VARDIR; (2) FİRMA-ÖZEL likidite betası (piyasa likiditesine DUYARLILIK); (3) GÖZLENEN illikidite priminin firma ÖZELLİKLERİYLE İLİŞKİLENDİRİLMESİ. (s.685-687)
- **İLKE-338 (QMDM modeli — 3 KAVRAMSAL SORUN):** Mercer'in Nicel Pazarlanabilirlik İskonto Modeli (QMDM), iskonto oranını ayarlayıp NAKİT AKIŞLARININ ÖDENMEYEN kısmını "ISKARTAYA ÇIKMIŞ" varsayarak DEĞERİ hesaplar — (1) eğer nakit GERÇEKTEN israf ediliyorsa, BAŞLANGIÇ değeri zaten DÜŞÜK hesaplanmalıydı (dairesel hata); (2) hesaplanan iskonto HEM KONTROL HEM likidite etkisinin KARIŞIMIDIR, ayrıştırılmamıştır; (3) iskonto ORANINA eklenecek PRİMİN büyüklüğü YİNE kısıtlı hisse çalışmalarından TÜRETİLMEK ZORUNDADIR — modelin İDDİA ETTİĞİ "nicel kesinlik" YANILTICIDIR. [→ FORMÜL-136] (s.687-688)
- **İLKE-339 (Küçük iskonto oranı ayarlaması → BÜYÜK değer iskontosu):** İskonto oranına eklenen KÜÇÜK bir prim, TUTMA SÜRESİNİN UZUNLUĞUNA bağlı olarak ORANTISIZ BÜYÜK bir değer iskontosuna dönüşür — SONSUZA (perpetuite) uygulandığında, SINIRLI bir döneme uygulanmasından ÇOK DAHA BÜYÜK bir iskonto ortaya çıkar. Bu, iskonto oranı yöntemiyle DOĞRUDAN değer-iskontosu yöntemi arasında SEÇİM yaparken dikkatli olunması gerektiğinin somut kanıtıdır. [→ EŞİK tablosu] (s.688-689)
- **İLKE-340 (Göreli değerlemede illikiditeyi ele almanın 2 yolu):** (1) BENZER LİKİDİTEDEKİ (özel şirket işlemleri) karşılaştırılabilir kullanmak — özel şirket satın almaları HALKA AÇIK emsallerden BELİRGİN ÖLÇÜDE DÜŞÜK çarpanla gerçekleşir (defter değeri çarpanı HARİÇ); (2) HALKA AÇIK emsal çarpanını illikidite iskontosuyla AYARLAMAK, YA DA çarpanı firmanın devir hızı gibi TEMEL değişkenlere REGRESE edip özel firma için devir hızını SIFIRA ayarlayarak DOĞRUDAN illikidite-ayarlı bir çarpan TÜRETMEK. [→ FORMÜL-137] (s.689-692)
- **İLKE-341 (İlliкiditenin kurumsal finans sonuçları):** İlliкidite/kontrol TRADE-OFF'U halka açılma KARARINI belirler (halka açık = LİKİDİTE ama AZ kontrol; özel = KONTROL ama AZ likidite); halka arz "sıcak/soğuk" DÖNGÜLERİ piyasa-geneli illikidite priminin ZAMANLA DEĞİŞTİĞİNİN kanıtıdır; illikid MENKUL KIYMET ihraç eden firmalar DAHA YÜKSEK sermaye/ihraç maliyeti taşır ve UZUN VADELİ negatif-nakit-akışlı projelere DAHA İSTEKSİZ yatırım yapar; VARLIK likiditesi YÜKSEK firmalar DAHA FAZLA borçlanabilir ve temettü/yatırım politikasında DAHA ESNEKTİR. (s.693-696)

## Formüller (devam)

- **FORMÜL-124 — Kötüye Kullanım Riskiyle Ayarlanmış Nakit Değeri**
  - Formül: `Ayarlanmış Nakit Değeri = Nakit Bakiyesi − (Kötüye Kullanım Olasılığı × Beklenen Fazla Ödeme Tutarı)`
  - Değişkenler: kitap örneği — $2 milyar nakit, %25 kötüye kullanım (satın almada fazla ödeme) olasılığı, $500mn beklenen fazla ödeme → ayarlanmış değer $1,875 milyar.
  - QuaxisLabs karşılığı: **VERİ EKSİK (sübjektif girdi)** — `cash`/`financial_investments` ham verisi `calculator.py`'de MEVCUT ama "kötüye kullanım olasılığı" analist-seviyesi sübjektif bir varsayımdır, hiçbir fetcher'dan TÜRETİLEMEZ. Düşük öncelik.

- **FORMÜL-125 — Değişen Yönetimin Değeri (Kontrol Değeri Temel Formülü)**
  - Formül: `Kontrol Değeri = Va (Optimal Değer) − Vb (Status Quo Değer)`
  - QuaxisLabs karşılığı: **METODOLOJİK EKSİK** — kavramsal olarak `valuation.py`'nin DCF çıktısını FARKLI varsayım setleriyle (farklı borç oranı, farklı yeniden yatırım oranı) İKİ KEZ çalıştırmayı gerektirir; motor MEVCUT ama (a) "optimal financing" senaryosu WACC/optimal-borç-oranı hesaplanmadığından (Kısım 1 FORMÜL-21 eksikliği) KURULAMAZ, (b) "optimal yönetim" senaryosu (reinvestment/ROC varsayımı) ANALİST-seviyesi bir karardır, OTOMATİK ÜRETİLEMEZ. Motor tek-senaryolu, karşı-olgusal (counterfactual) yeniden-çalıştırma YETENEĞİ YOK.

- **FORMÜL-126 — Oylu/Oysuz Hisse Fiyat Farkı (Kontrol Primi)**
  - Formül: `V_oysuz = Vb / (nv+nnv)`; `V_oylu = Vb/(nv+nnv) + π×(Va−Vb)/nv`
  - Değişkenler: `nv`=oylu hisse sayısı, `nnv`=oysuz hisse sayısı, `π`=yönetim değişikliği olasılığı.
  - QuaxisLabs karşılığı: **VERİ EKSİK/KAPSAM DIŞI** — hisse sınıfı (oylu/oysuz) ayrımı, sahiplik yapısı verisi HİÇBİR fetcher'da YOK. BIST'te bazı holding şirketlerinde A/B grubu hisse yapıları mevcuttur ama QuaxisLabs bu ayrımı ÇEKMİYOR.

- **FORMÜL-127 — Azınlık İskontosu / Çoğunluk Kontrol Primi**
  - Formül: `Çoğunluk Payı Değeri = %Pay × Va`; `Azınlık Payı Değeri = %Pay × Vb`; `Azınlık İskontosu = fark`
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — FORMÜL-125'in AYNI kök eksikliği (status quo/optimal ikili senaryo yok) + sahiplik yüzdesi verisi yok; QuaxisLabs tekil HALKA AÇIK varlık analiz motorudur, M&A/özel şirket değerleme DANIŞMANLIĞI yapmaz.

- **FORMÜL-128 — Piyasa Fiyatından İma Edilen Yönetim Değişikliği Olasılığı**
  - Formül: `Piyasa Fiyatı/Hisse = π×(Optimal Değer/Hisse) + (1−π)×(Status Quo Değer/Hisse)` → π çözülür
  - QuaxisLabs karşılığı: **UYGULANAMAZ** — `valuation.py` çıktısı (tek-senaryolu FCFE değeri) zaten piyasa fiyatıyla KIYASLANIYOR (değerleme sapması etiketlemesi için) ama iki-senaryolu (status quo/optimal) çıktı olmadığından π HESAPLANAMAZ.

- **FORMÜL-129 — Amihud İlliкidite Oranı**
  - Formül: `İlliкidite Oranı = |Günlük Fiyat Değişimi| / Günlük İşlem Hacmi`
  - QuaxisLabs karşılığı: **KISMEN VAR, DÜŞÜK MALİYETLİ** — `src/analysis/technical.py`'nin `TechnicalSnapshot` sınıfı (`avg_volume_20`, `last_volume`, `volume_ratio_pct`) zaten fiyat+hacim serisini TAŞIYOR; Amihud oranının KENDİSİ hesaplanmıyor ama mevcut OHLCV verisinden YENİ FETCHER GEREKMEDEN türetilebilir.

- **FORMÜL-130 — Devir Hızı (Turnover Ratio)**
  - Formül: `Devir Hızı = Günlük TL İşlem Hacmi / Piyasa Değeri Özkaynak (market_cap)`
  - QuaxisLabs karşılığı: **BU KISIMIN EN DÜŞÜK MALİYETLİ somut bulgusu.** `src/fetchers/isyatirim.py` GÜNLÜK TL hacmini ÇEKİYOR, `src/analysis/calculator.py::market_cap = price × share_capital` (satır 838) ZATEN HESAPLIYOR — ikisi FARKLI modüllerde (technical.py vs calculator.py) ayrı ayrı MEVCUT, sadece BİRLEŞTİRİLMEMİŞ. `turnover_ratio_pct = daily_volume_try / market_cap` TEK SATIR kodla eklenebilecek somut bir likidite proxy'sidir.

- **FORMÜL-131 — Longstaff Look-Back Opsiyonu (İlliкidite Değeri Üst Sınırı)**
  - Formül: mükemmel-zamanlamalı yatırımcının, kısıtlama dönemindeki MAKSİMUM fiyattan satabilme opsiyonunun (look-back option) değeri — Black-Scholes çerçevesinin bir varyantı.
  - QuaxisLabs karşılığı: **VERİ EKSİK/METODOLOJİK** — kavramsal olarak `src/analysis/merton.py`'nin Black-Scholes-Merton çerçevesiyle (Kısım 6 FORMÜL-121 notu) UYUMLU ama tutma süresi/oynaklık varsayımı SÜBJEKTİF; ayrıca ÖZEL şirket bağlamı için tasarlanmıştır — QuaxisLabs'ın 30 varlığı (BIST/NASDAQ/Crypto) hepsi zaten HALKA AÇIK/borsa işlem gören varlıklardır, pratik ÖNCELİK DÜŞÜK.

- **FORMÜL-132 — Silber Kısıtlı Hisse İskonto Regresyonu**
  - Formül: `RPRS = f(REV, RBRT, DERN, DCUST)`; `İlliкidite İskontosu = 1 − RPRS`
  - Değişkenler: `REV`=özel firma geliri, `RBRT`=kısıtlı blok/toplam hisse oranı, `DERN`=kâr dummy'si, `DCUST`=müşteri-ilişkisi dummy'si.
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — özel şirket/kısıtlı hisse değerlemesi, QuaxisLabs'ın halka açık şirket analiz kapsamı DIŞINDA.

- **FORMÜL-133 — Bajaj Özel Yerleştirme İskonto Regresyonu**
  - Formül: `DISC = f(SHISS, Z, DREG, SDEV)`
  - Değişkenler: `SHISS`=özel yerleştirme/toplam hisse oranı, `Z`=Altman Z-Skoru, `DREG`=tescil dummy'si, `SDEV`=getiri standart sapması.
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** (FORMÜL-132 ile AYNI kök).

- **FORMÜL-134 — Sentetik Alış-Satış Farkı Regresyonu**
  - Formül: `Spread(%) = f(Gelir, Kâr Dummy, Nakit/Firma Değeri, İşlem Hacmi)`; özel firma için İşlem Hacmi=0 girilerek sentetik spread TÜRETİLİR.
  - QuaxisLabs karşılığı: **KISMEN İLGİLİ** — gerçek bid-ask spread verisi (order book) YOK ama TÜRETİLEBİLİR PROXY (FORMÜL-130 devir hızı) MEVCUT; regresyonun kendisi evren-çapında CROSS-SECTIONAL istatistik altyapısı gerektirir (Kısım 4-5'teki BİLİNEN eksiklik).

- **FORMÜL-135 — Opsiyon-Bazlı İlliкidite İskontosu**
  - Formül: `İlliкidite Değeri = Put Opsiyon Değeri(K=Alım Fiyatı×(1+eşik), T=kısıtlama süresi) × P(Fiyat Artışı > eşik, T süresinde)`
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — özel şirket bağlamı; QuaxisLabs'ın kapsadığı varlıkların TAMAMI zaten halka açık/LİKİT olduğundan bu formül GEREKSİZDİR.

- **FORMÜL-136 — QMDM (Nicel Pazarlanabilirlik İskonto Modeli)**
  - Formül: `Değer = Σ[CF_t × Ödeme Oranı / (1+r_ayarlı)^t] + TV/(1+r_ayarlı)^n`, `r_ayarlı = r + illikidite primi`
  - QuaxisLabs karşılığı: **KAPSAM DIŞI** — özel şirket değerleme aracı, QuaxisLabs'ın halka açık hisse odağıyla UYUMSUZ.

- **FORMÜL-137 — İlliкidite-Ayarlı Göreli Değerleme Regresyonu**
  - Formül: `EV/Satış = a + b×Faaliyet Marjı + c×Devir Hızı`; özel firma için Devir Hızı=0.
  - QuaxisLabs karşılığı: Kısım 4-5'teki AYNI mimari eksiklik (çok-firma cross-sectional regresyon altyapısı YOK) — ama `market_cap`+hacim verisi (FORMÜL-130) MEVCUT olduğundan, GELECEKTE bu regresyonun (sektör-içi marj~çarpan) bir versiyonu için GİRDİ HAZIRDIR.

## Eşikler (devam)

| Metrik | Eşik / Değer | Yorum | Kaynak bölüm |
|---|---|---|---|
| SAP: status quo vs optimal (30% borç oranı) değer/hisse | 106,12€ → 118,50€ (kontrol değeri 12,4€ = değerin ~%12'si) | Kontrol değerinin İYİ yönetilen (muhafazakâr ama sağlam) bir firmada dahi anlamlı olabileceğinin kanıtı | Ch.13, İllüstrasyon 13.1 |
| Blockbuster: status quo vs restructured değer/hisse | $5,13 → $12,47 | KÖTÜ yönetilen firmada kontrol değerinin BÜYÜKLÜĞÜ (~%143 artış) | Ch.13, İllüstrasyon 13.2 |
| Blockbuster: piyasa fiyatından ima edilen π (Icahn öncesi/sonrası) | %41,8 → %59,5 | Aktivist yatırımcı müdahalesinin piyasanın ima ettiği yönetim-değişikliği olasılığını NASIL yükselttiğinin somut kanıtı | Ch.13, İllüstrasyon 13.4 |
| Nintendo: status quo değer/hisse vs piyasa fiyatı | 12.115 yen vs 11.300 yen (~%8 yüksek) → restructured 14.107 yen (+%18,5) | Büyük nakit bakiyesine (firma değerinin ~%45'i) piyasa iskontosu uyguladığının kanıtı | Ch.13, İllüstrasyon 13.3 |
| Düşmanca devralma hedefi profili (Bhide 1989) | Sektöre göre ROE **-%2,2**, piyasaya göre getiri **-%4**, içeriden sahiplik **%6,5** | Hedef firma profilinin somut istatistiksel imzası | Ch.13, s.622-623 |
| Devralma sonrası elden çıkarma / yönetim değişikliği oranı | 19 devralmanın **17**'sinde yönetim değişikliği (7'sinde TÜM ekip); **~%60**'ında büyük elden çıkarma | "Varlık soygunu" popüler algısının ÇÜRÜTÜLMESİ | Ch.13, s.623-624 |
| ABD'de ortalama devralma primi (1980-1990'lar) | **%20-30** | Kontrol+sinerji+fazla ödemenin KARIŞIMI, TEK BAŞINA kontrolü YANSITMAZ | Ch.13, s.621 |
| Pennsylvania 1989 antitakeover yasası — fiyat etkisi | İlk gün **-%1,58**, tüm süreçte **-%6,9**, toplam piyasa değeri kaybı **$4 milyar** | Devlet düzenlemesinin beklenen kontrol değeri üzerindeki DOĞRUDAN etkisi | Ch.13, s.626 |
| Zayıf vs güçlü yönetişimli hisse getiri farkı (Gompers/Ishi/Metrick 2003) | Yıllık **-%8,4** | Kurumsal yönetişimin fiyata YANSIMASININ büyüklüğü | Ch.13, s.627-628 |
| Yönetişim endeksi/Tobin's Q ilişkisi | Her **%1** kötüleşme → Tobin's Q **-%2,4** | | Ch.13, s.628 |
| Oy hakkı primi — ABD/İngiltere/Kanada | **%5-10** | Küçük ama TUTARLI bir prim | Ch.13, s.632 |
| Oy hakkı primi — Latin Amerika / İsrail / İtalya | **%50-100** / **%75** / **%80** | Zayıf azınlık koruması olan ülkelerde ÇOK DAHA BÜYÜK prim | Ch.13, s.632 |
| İtalya mandatory-bid (1992) / yönetişim reformu (1997) etkisi | Prim **+%2** / **-%7** | Yasal reformun DOĞRUDAN prim etkisi | Ch.13, s.633 |
| Brezilya azınlık koruması değişikliği (1997/1999) | Prim **2 katına çıktı**, sonra TERSİNE DÖNDÜ | | Ch.13, s.633 |
| Embraer: oylu/oysuz hisse primi (İllüstrasyon 13.5, π=%20 varsayımıyla) | **%10,4** | Oy hakkı sınıfı primi hesabının somut uygulaması | Ch.13, s.633-634 |
| Embraer: oylu vs oysuz hisse işlem oranı | Oylu **%19**, oysuz **%90** işlem görüyor | Likidite farkının primi KISMEN dengeleyebileceği | Ch.13, s.634 |
| Özel şirket işlemlerinde pratik çoğunluk primi | **%15-20** | Pratisyen kuralı-of-thumb (kitap bunun KEYFİLİĞİNİ eleştirir) | Ch.13, s.637 |
| Azınlık işlem iskontosu (Harouna/Sarin/Shapiro 2001, 9.566 işlem) | Piyasa-odaklı ekonomilerde **%20-30**, banka-odaklı ekonomilerde DAHA KÜÇÜK | Sınıflandırma eşiği: azınlık=işlem öncesi/sonrası <%30, çoğunluk=öncesi<%30→sonrası>%50 | Ch.13, s.637 |
| Büyük blok işlem primi (Barclay&Holderness / İtalya) | ABD **>%10**; İtalya ort. **%27** (>%10 blok: %31, <%10 blok: %24) | Çoğunluk eşiğinin (%50) ALTINDA bile prim varlığının kanıtı | Ch.13, s.637 |
| Kristin Kandy: status quo vs optimal özkaynak değeri | $1,6mn → $2,0mn; %51 pay=$1,02mn vs %49 pay=$0,784mn | Küçük özel şirket ölçeğinde azınlık iskontosunun somut hesabı | Ch.13, İllüstrasyon 13.6 |
| NYSE ortalama alış-satış farkı (1996) | **$0,23** (ort. fiyat $40-50) | Mutlak rakam KÜÇÜK görünür ama yüzdesel etki büyük | Ch.14, s.649 |
| Spread, piyasa değerine göre (Loeb 1983) | Küçük-cap **%6,55** vs büyük-cap **%0,52** | Boyut farkının spread üzerindeki BÜYÜKLÜĞÜ | Ch.14, s.649-650 |
| Spread, işlem hacmine göre (Huang&Stoll 1987) | En üst %20 hacim **%0,62** vs en alt %20 hacim **%2,06** | | Ch.14, s.650 |
| NASDAQ ortalama spread (Kothare&Laux 1995, 1992 verisi) | **~%6** | NYSE'den BELİRGİN ÖLÇÜDE yüksek | Ch.14, s.650 |
| Hazine bonosu tipik spread | **<%0,1** | En likit varlık sınıfı referansı | Ch.14, s.651 |
| Fiyat etkisi (Breen/Hodrick/Korajczyk 2000) | 5 dakikada %0,1 devir hızı artışı → NYSE/AMEX **%2,65**, NASDAQ **%1,85** fiyat etkisi | | Ch.14, s.656-657 |
| Spread'deki %1 artışın getiriye etkisi (Amihud&Mendelson 1989) | Yıllık **+%0,24 ila %0,26** | Likidite risk priminin DOĞRUDAN ölçümü | Ch.14, s.662-663 |
| Devir hızı ~ getiri ilişkisi (Datar/Naik/Radcliffe 1998) | En illikid (10. persentil) vs en likit (90. persentil) yıllık **+%3,25**; her %1 devir hızı artışı → **-%0,54** getiri | | Ch.14, s.663 |
| İlliкidite risk primi (Acharya&Pedersen 2005) | Yıllık **~%1,1** daha yüksek risk primi, **%80**'i piyasa-illikidite kovaryansıyla açıklanır | | Ch.14, s.661-662 |
| Piyasa likiditesine duyarlılık primi (Pastor&Stambaugh 2003) | Yıllık **~%7,5** daha yüksek getiri (34 yıl, faktör-ayarlı) | | Ch.14, s.662 |
| Hazine tahvili/bonosu likidite farkı | **%0,37-0,43** yıllık (tartışmalı — vergi farkıyla açıklanabilir) | En LİKİT varlık sınıfında bile ölçülebilir bir fark | Ch.14, s.666 |
| Kurumsal tahvil spread-getiri ilişkisi (Chen/Lesmond/Wei 2005) | Yatırım dereceli: %1 işlem maliyeti artışı → **+%0,21** getiri; spekülatif dereceli: **+%0,82** | Riskli tahvillerde likiditenin ÇOK DAHA ÖNEMLİ olduğunun kanıtı | Ch.14, s.666-667 |
| Kısıtlı hisse iskontosu (Maher 1976 / Silber 1991 / Johnson 1999) | **%35,43 ort.** / **%33,75 medyan** / **%20** | Zamanla küçülen tahmin — örneklem/metodoloji eleştirisinin sonucu | Ch.14, s.669-670 |
| Tescilli vs tescilsiz özel yerleştirme iskonto farkı (net illikidite) | Wruck **%17,6/%10,4**; Hertzel&Smith **%13,5**; Bajaj vd. (kontrollü) **%7,23** | Diğer faktörler kontrol edildikçe SAF illikidite iskontosu KÜÇÜLÜYOR | Ch.14, s.670-671 |
| IPO-öncesi işlem fiyatı iskontosu | Emory (1997) **~%45**; Williamette (2002) **%32-75** | Yazarın "mantık dışı büyük" olarak nitelediği aralık | Ch.14, s.671-672 |
| Çin RIS (kısıtlı kurumsal hisse) iskontosu | Açık artırma **%78**, özel yerleştirme **%86** | En YÜKSEK gözlenen illikidite iskontosu | Ch.14, s.672-673 |
| Nontraded kur opsiyonu iskontosu (Brenner/Eldor/Hauser 2001) | **~%21** | Türev varlıklarda da illikidite fiyatlanıyor | Ch.14, s.673 |
| Özel sermaye fazla getirisi (Ljungquist&Richardson 2003) | Yıllık **%5-8** fazla getiri, 10 yılda **~%24** risk-ayarlı ek değer | Kontrol+çeşitlendirilmeme+likidite karışımı | Ch.14, s.673-674 |
| VC iskontosu, yatırım aşamasına göre (Das/Jagannathan/Sarin 2002) | Geç aşama **%11**, erken aşama **%80**'e kadar | Aşamaya göre AŞIRI FARKLI iskonto — SABİT VC-primi varsayımının çürütülmesi | Ch.14, s.674 |
| Kristin Kandy: illikidite iskontosu — yöntem kıyası (İllüstrasyon 14.1) | Sabit (kısıtlı hisse) **%25**; tescilli-fark **%15**; Silber-ayarlı **%17,17**; sentetik spread **%12,65**; opsiyon-bazlı **%8,67** | AYNI şirket için yöntemler arası **~3 KAT** fark | Ch.14, s.684 |
| QMDM örneği (İllüstrasyon, r=%9, g=%4, 5 yıl, %60 ödeme) | Ayarsız değer $20 → likidite-ayarlı $16,13 (iskonto **%19,35**) | | Ch.14, s.687-688 |
| İskonto oranı yöntemi — 5 yıl vs sonsuz uygulama farkı (Kristin Kandy) | %4 prim: 5 yıl **-%15,78** vs sonsuz **-%31,77**; %2 prim: 5 yıl **-%7,66** vs sonsuz **-%17,66** | Küçük oran artışının UZUN vadede ORANTISIZ büyük iskontoya dönüşmesi | Ch.14, s.688-689 |
| Özel vs halka açık şirket satın alma çarpanı farkı (Koeplin/Sarin/Shapiro 2000) | **%20-30** düşük (yerel), **%40-50** düşük (yabancı özel firma) — defter değeri çarpanı HARİÇ | | Ch.14, s.689-690 |
| Kristin Kandy: göreli değerleme (illikidite-ayarlı regresyon) sonucu | EV/Satış **0,835** → değer **$2,51mn** (DCF tahminlerinden YÜKSEK) | Yöntemler arası büyük SAPMA örneği | Ch.14, İllüstrasyon 14.3 |

## Kontrol listeleri (devam)

**Kontrol Listesi CC — Firma Değerini Artırmanın 5 Ana Kanalı (Ch.13, s.594-601):**
1. Mevcut varlıklardan nakit akışını artır (varlık yeniden konuşlandırma, faaliyet verimliliği, vergi yükü azaltma, işletme sermayesi optimizasyonu).
2. Beklenen büyümeyi artır (yeni yatırımın ORANI/KALİTESİ VEYA mevcut varlık verimliliği).
3. Yüksek büyüme dönemini uzat (giriş engellerini güçlendir / yeni rekabet avantajı yarat).
4. Sermaye maliyetini düşür (ürün riskini azalt, faaliyet kaldıracını azalt, finansman karışımını optimize et, finansmanı varlıklarla eşleştir).
5. Faaliyet-dışı varlıkları (nakit, çapraz iştirak, emeklilik fonu) yönet.

**Kontrol Listesi DD — Yönetim Değişikliği Olasılığını Artıran Firma Özellikleri (Ch.13, s.618-619):**
1. Zayıf hisse fiyatı/kazanç performansı (emsal gruba göre).
2. Küçük, dışarıdan-ağırlıklı yönetim kurulu (CEO≠başkan).
3. Yüksek kurumsal / düşük içeriden sahiplik oranı.
4. Rekabetçi (yoğun) sektör yapısı.
5. Düşük PD/DD çarpanı + düşük sermaye getirisi (hostile devralma hedefi profili).
6. Sermaye piyasalarına yeni sermaye ihtiyacı için BAĞIMLILIK.

**Kontrol Listesi EE — Özel Şirket İlliкidite İskontosunu Belirleyen 5 Faktör (Ch.14, s.677-678):**
1. Firmanın sahip olduğu varlıkların likiditesi.
2. Finansal sağlık/nakit akışı durumu.
3. Gelecekte halka açılma olasılığı.
4. Firma büyüklüğü (yüzde olarak DAHA BÜYÜK firmalarda DAHA KÜÇÜK iskonto).
5. Kontrol bileşeni (pay büyüklüğü — çoğunluk payı azınlıktan DAHA LİKİTTİR).

**Kontrol Listesi FF — İlliкiditeyi Değerlemeye Dahil Etmenin 4 Yöntemi (Ch.14, s.675-692):**
1. Sabit iskonto (kısıtlı hisse çalışmalarına dayalı, analist takdiriyle ayarlanmış — EN ZAYIF, seçim önyargısı taşır).
2. Firma-özel iskonto (Silber/Bajaj tipi regresyon — gelir/sağlık/büyüklüğe göre ayarlı).
3. İskonto oranı ayarlaması (sabit prim / firma-özel likidite betası / gözlenen prim-özellik ilişkisi).
4. Göreli değerleme (a) benzer likiditedeki karşılaştırılabilir kullanımı, (b) çarpanı devir hızı gibi temel değişkenlere regrese edip özel firma için sıfırlama.

## Kırmızı bayraklar (devam)

- **BAYRAK-42 — Sabit/Kural-of-Thumb Kontrol Primi Kullanımı:** "Kontrol her zaman değerin %20-30'udur" tipi bir SABİT yüzde kullanmak, kontrol priminin firmanın YÖNETİM KALİTESİNE göre BÜYÜK ÖLÇÜDE DEĞİŞTİĞİ gerçeğini GÖZ ARDI eder. Nasıl tespit edilir: kullanılan kontrol priminin firma-özel status-quo/optimal değer FARKINDAN mı yoksa SEKTÖR/piyasa ORTALAMASINDAN mı türetildiği kontrol edilmeli. Gereken veri: status quo ve optimal senaryo değerleri (Kısım 1 WACC eksikliğine bağlı, VERİ EKSİK). (Ch.13, s.620-621)
- **BAYRAK-43 — Piyasa Fiyatı Zaten İçerdiği Kontrol Beklentisi Üzerine Ek Prim Ödenmesi (Çifte Sayım):** Piyasa fiyatı zaten YÜKSEK bir yönetim-değişikliği olasılığını fiyatlıyorsa, "kötü yönetiliyor" gerekçesiyle EK bir prim ödemek fazla ödemeye yol açar. Nasıl tespit edilir: teklif fiyatı gerekçesinde piyasa fiyatının ZATEN ne ölçüde kontrol beklentisi içerdiği SORGULANIYOR MU kontrol edilmeli. Gereken veri: iki-senaryolu (status quo/optimal) değerleme (VERİ EKSİK, aynı kök). (Ch.13, s.624-625)
- **BAYRAK-44 — Kontrol Değeri ile Sinerjinin KARIŞTIRILMASI:** Bir birleşmede ödenen TEK bir prim rakamının içine hem kontrol hem sinerji sızdırılmış olabilir — bu ikisi FARKLI kaynaklardan gelir (kontrol TEK firmada var olabilir, sinerji İKİ firma GEREKTİRİR) ve AYRIŞTIRILMADAN raporlanan bir prim YANILTICIDIR. Nasıl tespit edilir: birleşme gerekçesinde "kontrol" ve "sinerji" bileşenlerinin AYRI AYRI SAYISALLAŞTIRILIP SAYISALLAŞTIRILMADIĞI kontrol edilmeli. (Ch.13, s.620)
- **BAYRAK-45 — Yönetim Kalitesi Analiz Edilmeden Sabit Kontrol/Azınlık İskontosu Uygulanması:** Kötü yönetilen ile iyi yönetilen firma AYNI yüzde iskonto/primle DEĞERLENİRSE, iyi yönetilen firmalarda kontrol değerinin SIFIRA YAKIN olması gerektiği gerçeği GÖZ ARDI EDİLMİŞ olur. Nasıl tespit edilir: iskonto/prim oranının firmanın SERMAYE GETİRİSİ/sermaye maliyeti FARKINA göre AYARLANIP AYARLANMADIĞI kontrol edilmeli. Gereken veri: `roe_annualized` MEVCUT, cost of capital (WACC) **VERİ EKSİK**. (Ch.13, s.620-621)
- **BAYRAK-46 — Kısıtlı Hisse Çalışmalarına Dayalı Sabit %20-35 İlliкidite İskontosu:** Bu iskonto, KÜÇÜK örneklem, seçim önyargısı (kısıtlı hisse ihraç eden firmalar zaten küçük/riskli) ve hizmet-bedeli karıştırma sorunları taşır — kontrollü kıyaslar (tescilli vs tescilsiz) GERÇEK likidite etkisinin ÇOK DAHA KÜÇÜK (~%7-17) olduğunu gösterir. Nasıl tespit edilir: kullanılan iskontonun kontrollü (tescilli-vs-tescilsiz) mi yoksa HAM kısıtlı-hisse çalışmasından mı geldiği kontrol edilmeli. (Ch.14, s.669-671)
- **BAYRAK-47 — QMDM/Opsiyon-Bazlı Modellerin Kontrol ve Likidite Etkisini AYRIŞTIRMAMASI:** Bu modellerin hesapladığı "illikidite iskontosu" genellikle KONTROL kaybının etkisini de İÇİNDE BARINDIRIR (nakit akışının ödenmeyen kısmının "israf" varsayılması KONTROLE bağlıdır) — TEK bir iskonto rakamının SADECE likiditeye atfedilmesi YANILTICIDIR. Nasıl tespit edilir: iskonto hesabının kontrol/yönetim-gücü varsayımlarından BAĞIMSIZ olup OLMADIĞI kontrol edilmeli. (Ch.14, s.687-688)
- **BAYRAK-48 — Düşük İşlem Hacimli Hissede Standart (Büyük-Cap) İskonto Oranı Kullanılması:** Az-likit/küçük-cap hisseler İÇİN likidite risk primi (yıllık ~%1-3,25 arası, ampirik çalışmalara göre) EKLENMEDEN standart cost-of-equity kullanmak DEĞERİ SİSTEMATİK OLARAK YÜKSEK GÖSTERİR. Nasıl tespit edilir: hissenin devir hızı/işlem hacminin piyasa/sektör ORTALAMASINA göre NASIL konumlandığı kontrol edilmeli. Gereken veri: **FORMÜL-130 (devir hızı) — DÜŞÜK MALİYETLE eklenebilir, `isyatirim.py` hacim + `calculator.py` market_cap ZATEN mevcut.** (Ch.14, s.661-663)
- **BAYRAK-49 — İllikid Hissede Kısa-Vadeli/Yüksek-Devir Stratejisi Uygulanması:** Bekleme fırsat maliyeti KISA vadeli/yüksek-devir stratejilerde EN YÜKSEKTİR — az-likit bir hissede bu tür bir strateji, spread+fiyat-etkisi maliyetlerinin GETİRİYİ AŞINDIRMASINA yol açabilir. Nasıl tespit edilir: önerilen tutma süresinin hissenin devir hızıyla TUTARLI olup OLMADIĞI kontrol edilmeli. Gereken veri: FORMÜL-130 (devir hızı). (Ch.14, s.657-658, 694-695)
- **BAYRAK-50 — Özel Sermaye/VC Getiri Rakamlarının SADECE İlliкiditeye Atfedilmesi:** Özel sermaye yatırımcılarının fazla getirisi HEM illikidite HEM çeşitlendirilmeme (nondiversification) HEM kontrol priminin KARIŞIMIDIR — bu farkın TAMAMININ "likidite primi" olarak nitelenmesi ABARTILI bir tahmin üretir. Nasıl tespit edilir: kullanılan illikidite primi kaynağının (VC-getiri farkı gibi) BAŞKA risk faktörlerinden ARINDIRILIP arındırılmadığı sorgulanmalı. (Ch.14, s.673-674, 685-686)
- **BAYRAK-51 — GEÇİCİ Fiyat Etkisinin KALICI Fiyat Hareketi Olarak Yanlış Yorumlanması:** Büyük blok işlemler sonrası fiyat hareketinin bir kısmı likidite-kaynaklı ve GEÇİCİDİR (birkaç gün içinde tersine döner), bir kısmı BİLGİSEL ve KALICIDIR — bu ikisi AYRIŞTIRILMADAN tek bir "fiyat sinyali" olarak yorumlanması YANILTICI olabilir, özellikle az-likit hisselerde ("overshoot" etkisi). Nasıl tespit edilir: büyük hacimli bir hareketin SONRASINDAKİ günlerde kısmen/tamamen tersine dönüp DÖNMEDİĞİ izlenmeli. (Ch.14, s.654-656)
- **BAYRAK-52 — Oy Hakkı Fiyat Farkının SADECE Kontrolle Açıklanması:** Oylu/oysuz hisse fiyat farkı bazen TEMETTÜ önceliği, DAĞITIM farkı veya LİKİDİTE farkı (Embraer örneğinde oysuz hisseler HEM daha yüksek temettü HEM daha yüksek likidite taşıyor, primi KISMEN DENGELİYOR) gibi DENGELEYİCİ faktörlerden de etkilenir — farkın TAMAMININ kontrol primi olarak yorumlanması YANLIŞ OLABİLİR. Nasıl tespit edilir: hisse sınıfları arasındaki temettü/likidite farkının AYRI AYRI kontrol edilip edilmediği sorgulanmalı. (Ch.13, s.629-634)
- **BAYRAK-53 — Konglomera/Çapraz İştirak Yapısındaki Firmanın Piyasa Değerinin İçerideki Değerin Toplamına Eşit Varsayılması:** Çeşitli/ilgisiz iş kollarına sahip holding yapıları genellikle bir "konglomera iskontosu" (kitapta %5-10 aralığı belirtilir) taşır — sum-of-the-parts (parçaların toplamı) değerlemesi bu iskontoyu GÖZ ARDI ederse şirketi SİSTEMATİK OLARAK ucuz gösterebilir (VEYA iskonto GERÇEKTEN varsa bölünme/elden çıkarma fırsatını KAÇIRABİLİR). Nasıl tespit edilir: çok-iş-kollu bir holding şirketinin piyasa değeri, alt-iştiraklerin AYRI AYRI tahmini değerlerinin TOPLAMIYLA kıyaslanmalı. Gereken veri: segment/iştirak bazlı ayrıştırılmış değerleme — QuaxisLabs'ta segment-bazlı veri YOK (Kısım 6'da da tespit edilen eksiklik). (Ch.13, s.599-601)

## Uygulama notları (devam)

**Nicel (skorlanabilir):**
- **Devir Hızı / Turnover Ratio (FORMÜL-130) — bu Kısmın EN DÜŞÜK MALİYETLİ somut bulgusu.** `isyatirim.py`'nin ZATEN çektiği günlük TL hacmi ile `calculator.py`'nin ZATEN hesapladığı `market_cap` BİRLEŞTİRİLEREK (`turnover_ratio_pct = daily_volume_try / market_cap`) YENİ bir fetcher GEREKMEDEN eklenebilir — hem BAYRAK-48/49'un otomatik tespiti hem sektör-içi likidite karşılaştırması için TEMEL girdi olur.
- **Amihud İlliкidite Oranı (FORMÜL-129)** — `technical.py`'nin `TechnicalSnapshot` sınıfındaki mevcut fiyat+hacim serisinden (`avg_volume_20`, `last_volume`) DÜŞÜK maliyetle türetilebilir; iki likidite proxy'si (turnover + Amihud) BİRLİKTE bir "likidite skoru" olarak dashboard'a eklenebilir.
- Bu iki proxy, teknik analiz modülünde (`technical.py`) zaten VAR olan verinin TEMEL ANALİZ tarafına (`calculator.py`/skorlama) HİÇ AKTARILMADIĞINI ortaya çıkardı — modüller-arası entegrasyon eksikliği, YENİ veri GEREKTİRMEYEN düşük-maliyetli bir kazanım.

**Nitel (LLM yorumuna uygun):**
- **Yönetişim kalitesi taraması (BAYRAK-45 ile ilişkili)** — yönetim kurulu yapısı (bağımsız üye oranı, CEO=başkan mı), sahiplik yoğunluğu gibi bilgiler KAP dipnotları/faaliyet raporlarından LLM'e SORULABİLİR; QuaxisLabs'ta hiçbir yapılandırılmış alan olarak YOK.
- **Konglomera iskontosu taraması (BAYRAK-53)** — çok-iş-kollu BIST holding şirketlerinde (örn. çeşitlendirilmiş sanayi/finans grupları) piyasa değerinin alt-iştiraklerin toplamından NE KADAR SAPTIĞI, LLM'e verilebilecek bir nitel tarama görevidir (kesin sum-of-the-parts hesabı olmasa da yönlü bir yorum üretilebilir).
- **Oy hakkı yapısı/hisse sınıfı taraması (BAYRAK-52)** — A/B grubu hisse yapısı olan BIST şirketlerinde dipnotlardan bu bilginin ÇIKARILMASI ve fiyat farkının ne kadarının temettü/likidite ile açıklanabileceğinin LLM'e sorulması.

**Veri eksikliği / kapsam dışı nedeniyle UYGULANAMAZ:**
- **Ch.13'ün BÜYÜK ÇOĞUNLUĞU (kontrol primi/azınlık iskontosu, FORMÜL-125-127, 131-133, 135-136)** — sahiplik yapısı/hisse sınıfı verisi TAMAMEN YOK ve M&A/özel şirket değerleme QuaxisLabs'ın kapsamı DIŞINDA (tekil BIST/NASDAQ/Crypto VARLIK analiz motoru, kurumsal finans danışmanlığı YAPMAZ).
- **Kısıtlı hisse/özel yerleştirme/QMDM (FORMÜL-132/133/136)** — özel şirket değerleme aracı, kapsam dışı.
- **Sentetik spread/illikidite-ayarlı göreli değerleme regresyonları (FORMÜL-134/137)** — Kısım 4-5'teki BİLİNEN "çok-firma cross-sectional regresyon altyapısı yok" eksikliği; ancak turnover-ratio verisi (FORMÜL-130) EKLENİRSE bu regresyonların bir versiyonu için GİRDİ HAZIR OLACAKTIR.
- **Optimal/status-quo çift-senaryo değerleme (FORMÜL-125-128'in ORTAK KÖKÜ)** — `valuation.py` TEK-senaryolu çalışıyor, "karşı-olgusal" (counterfactual) yeniden-çalıştırma yeteneği YOK; WACC eksikliği (Kısım 1'den beri bilinen) burada "optimal financing" senaryosunu da ENGELLEYEREK kümülatif etkisini GENİŞLETTİ.
