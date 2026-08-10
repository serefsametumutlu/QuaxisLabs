# İlerleme Takibi — kitap-okuyucu

## Genel durum
| # | Kitap | Durum | Hedef dosya |
|---|---|---|---|
| 01 | The Intelligent Investor (Benjamin Graham, Rev. Ed. — Jason Zweig commentary) | **TAMAMLANDI** — Tüm kısımlar (Introduction + Ch.1-20 + Postscript + Appendix) işlendi. | `bilgi-bankasi/01_graham_akilli_yatirimci.md` |
| 02 | Warren Buffett and the Interpretation of Financial Statements | **TAMAMLANDI** — 5 ana kısım (Gelir Tablosu, Bilanço, Özkaynaklar, Nakit Akış Tablosu, Değerleme) + Appendix model şirket karşılaştırması işlendi. Terimler Sözlüğü bilinçli olarak atlandı (sadece tanım niteliğinde). | `bilgi-bankasi/02_buffett_finansal_tablolar.md` |
| 03 | Damodaran on Valuation, 2nd Ed. (Aswath Damodaran) | **DEVAM EDİYOR** — Kısım 1/9 (Ch.1-2) TAMAMLANDI, henüz commit edilmedi. Kısım 2-9 işlenmedi, sıradaki kısım için kullanıcı onayı bekleniyor. | `bilgi-bankasi/03_damodaran_degerleme.md` |

## Kitap geneli TOPLAM sayılar — 02 Buffett (dosya üzerinde script ile doğrulandı)
- İLKE: **61** (İLKE-01…61, kesintisiz, tekrarsız)
- FORMÜL: **35** (FORMÜL-01…35, kesintisiz, tekrarsız)
- EŞİK tablosu satırı: **67** (5 ana kısım toplamı: 22+17+10+6+12) + **9** appendix model şirket karşılaştırma satırı (ayrı, referans amaçlı) = **76** toplam
- KONTROL LİSTESİ maddesi: **54** (10+14+10+10+10)
- KIRMIZI BAYRAK: **36** (BAYRAK-01…36, kesintisiz, tekrarsız)

## Kitap geneli TOPLAM sayılar — 01 Graham (TÜMÜ TAMAMLANDI, script ile doğrulandı)
- İLKE: **152** (İLKE-01…152, kesintisiz, tekrarsız)
- FORMÜL: **36** (FORMÜL-01…36; FORMÜL-37-40 numaraları bilinçli boş — Kısım 5-7 bölümlerinde ayrı hesap gerektiren özgün formül bulunmadı)
- EŞİK tablosu satırı: **73** (Kısım1: 17 + Kısım2: 24 + Kısım3: 27 + Kısım4: 5)
- KONTROL LİSTESİ maddesi: **82** (Kısım1: 20 [A:6+B:6+C:4+D:4] + Kısım2: 21 [E:5+F:5+G:5+H:6] + Kısım3: 29 [I:6+J:5+K:4+L:7+M:7] + Kısım4: 12 [N:7+O:5])
- KIRMIZI BAYRAK: **45** (BAYRAK-01…45, kesintisiz, tekrarsız)
- Bu sayılar KİTABIN TÜMÜNE aittir. İçerik çıkarma tamamlanmıştır.

## Bölüm bazlı durum (01 — Graham Akıllı Yatırımcı) — Kısım 1-3/7 TAMAMLANDI
| Kısım | Bölümler | Kitap sayfa | İLKE | FORMÜL | Eşik satırı | Kontrol maddesi | BAYRAK | Durum |
|---|---|---|---|---|---|---|---|---|
| **Kısım 1** | Introduction + Comm. + Ch.1-4 + Comm.1-4 | s.1-111 | 01-38 (38) | 01-07 (7) | 17 | 20 (A/B/C/D) | 01-11 (11) | TAMAMLANDI, commit edildi (123e162) |
| **Kısım 2** | Ch.5-8 + Comm.5-8 | s.112-224 | 39-92 (54) | 08-17 (10) | 24 | 21 (E/F/G/H) | 12-23 (12) | TAMAMLANDI, commit edildi (5e40c43) |
| **Kısım 3** | Ch.9-13 + Comm.9-13 | s.226-346 | 93-137 (45) | 18-24 (7) | 27 | 29 (I/J/K/L/M) | 24-38 (15) | TAMAMLANDI, henüz commit edilmedi |
| **Kısım 4** | Ch.14-15 (savunmacı/girişimci seçim kriterleri) | s.347-446 | 138-159 (22) | 25-35,37-38 (13) | 16 | 15 (N/O/P) | 39-43 (5) | TAMAMLANDI, commit edildi (6a6b8e4, zenginleştirme sonrası ayrı commit) |
| **Kısım 5** | Ch.16-18 | s.447-541 | 160-175 (16) | 39 (1) | 2 | — | 44-48 (5) | TAMAMLANDI, commit edildi (6a6b8e4, zenginleştirme sonrası ayrı commit) |
| **Kısım 6** | Ch.19-20 + Postscript (Güvenlik Marjı) | s.542-596 | 176-190 (15) | 36 (1) | 4 | — | 49-51 (3) | TAMAMLANDI, commit edildi (6a6b8e4, zenginleştirme sonrası ayrı commit) |
| **Kısım 7** | Appendix 1-7 (Buffett'ın Superinvestors makalesi dahil) | s.571-638 | 191-195 (5) | — | 7 | — | 52 (1) | TAMAMLANDI, commit edildi (6a6b8e4, zenginleştirme sonrası ayrı commit) |

**Not (zenginleştirme turu):** Kısım 4-7 ilk turda (6a6b8e4) daha özet biçimde çıkarılmıştı (İLKE-138-152, 15 ilke). Aynı oturumda ham OCR metnine (`_tmp/ch14-20_raw.txt`) dönülerek "hiçbir eşiği atlama" talimatına daha sıkı uyan, çok daha ayrıntılı bir 2. tur yapıldı (İLKE-138-195, 58 ilke) — bu, kitabın en yoğun formül bölümü olduğu için gerekçelendirildi. 2. turun ham metin→markdown dönüşümünde bir dizi Türkçe karakter bozulması (kazanc→kazanç, büyme→büyüme, birkaç anlamsız kelime türü gibi) oluştu; bunlar sonraki oturumda tek tek tespit edilip düzeltildi. **Ders:** Bu tür yeniden-yazma turları TOKEN MALİYETİ YÜKSEK — bir kısmı zaten TAMAMLANDI işaretliyken tekrar işlemek zorunlu değilse YAPILMAMALI; ileride "zaten var, sadece eksik parçayı tamamla" yaklaşımı tercih edilmeli.

### Graham Kısım 2 — özel notlar
- Bu kısım kitabın İLK somut sayısal seçim kriterleri bloğu (Ch.5'in 4 kuralı: çeşitlendirme/büyüklük/temettü/fiyat tavanı; Ch.7'nin bargain/net-net testleri) — Ch.14-15'te (Kısım 4) muhtemelen genişletilip çapraz referans verilecek.
- "10+ yıllık kazanç/EPS serisi" veri açığı bu turda 4. kez tekrarlandı (FORMÜL-08/09/15, Kısım1 FORMÜL-05 ile aynı kök `trends.py` 12-çeyrek kısıtı) — artık kitaplar-arası bir örüntü, QuaxisLabs'ın EN YÜKSEK öncelikli yapısal eksikliği olarak değerlendirilmeli.
- İki düşük-maliyetli/yüksek-değerli kazanım netleşti: F/K sınıflandırması (Kısım1 FORMÜL-02) + PD/DD tavanı (Kısım2 FORMÜL-17, ≤1,33×) — ikisi de mevcut `pe_ratio`/`pb_ratio` alanlarına sadece eşik-etiketleme eklemekle yetiniyor, TEK bir PR'da birlikte eklenebilir.
- Temettü verisi eksikliği 3. kez farklı bağlamda doğrulandı (Ch.5 kuralı 3 + dividend-reinvestment örneği) — artık kitap genelinde en çok vurgulanan tekil eksik alan.
- NCAV/net-net formülü (Kısım1 FORMÜL-01, bu turda FORMÜL-12 olarak kesinleşti) önceliği Kısım1'deki "ORTA"dan yükseltilmeli — Ch.7'nin merkezi bargain kriteri olduğu teyit edildi.

### Graham Kısım 3 — özel notlar
- Bu kısımda kitabın en somut TEK formül kümesi bulundu: Ch.13'ün 7 savunmacı yatırımcı kriteri (FORMÜL-21/KONTROL M) — Ch.5'in 4 kuralıyla büyük örtüşme var ama 3 yeni nicel kriter ekliyor (10 yılda sıfır zarar, 10 yıllık HBK büyümesi ≥1/3, PD/DD≤1,5×). Kısım 4 (Ch.14-15) işlendiğinde bu listenin NİHAİ/olgun hali tekrar görülecek, tam çapraz referans o zaman yapılmalı.
- Graham'ın kitap İÇİNDE 2 FARKLI PD/DD eşiği kullandığı tespit edildi: Ch.8'de ≤1,33× (genel muhafazakar alım kılavuzu), Ch.13'te ≤1,5× (resmi 7-kriterlik liste parçası) — valuation.py'ye eklenirken bu fark belgelenmeli.
- "10+ yıllık kazanç serisi" veri açığı 5. kez tekrarlandı (FORMÜL-19/20/21 + önceki 4 tekrar) — artık QuaxisLabs'ın kesinleşmiş en yüksek öncelikli yapısal eksikliği.
- Faiz karşılama oranı (FORMÜL-18, sanayi şirketleri için en yüksek eşik 7x) — Buffett turunda en çok vurgulanan tekil veri açığının (faiz gideri, XI_29 şemasında yok) 3. kez farklı kitap/bağlamda ortaya çıkışı.
- Kazanç kalitesi/muhasebe manipülasyonu teması (Ch.12+Comm.12: pro forma kazanç, agresif gelir kaydı, sermaye-harcaması-yeniden-sınıflandırma, pensiyon varsayımı) QuaxisLabs'ın mevcut sayısal veri modeliyle DOĞRUDAN taranamaz — nitel/dipnot-okuma gerektirir; ileride bir metin-checklist olarak (kod değil) rapor formatına eklenebilir.
- Koordinatörün "gerçek şirket verisi vs hayali didaktik örnek" ayrımı bu turda net uygulandı: ALCOA (Ch.12) ve ELTRA/Emerson/Emery/Emhart + EMC/Expeditors/Exodus (Ch.13, Graham 1970 + Zweig 1999) GERÇEK NYSE/NASDAQ şirketleri olduğundan doğrudan eşik/örnek kaynağı sayıldı.

### Graham Kısım 1 — özel notlar
- QuaxisLabs kapsam tespiti: FORMÜL-06 (%50-%50 portföy dengeleme) gibi PORTFÖY-SEVİYESİ (çok varlık sınıflı hisse/tahvil/nakit tahsis) formülleri BİLİNÇLİ olarak KAPSAM DIŞI sayıldı — QuaxisLabs tekil BIST/NASDAQ/Crypto varlık analiz motorudur, portföy yönetimi yapmaz (Buffett turundaki "maliyet-üzerinden-getiri kapsam dışı" tespitiyle aynı mantık kategorisi).
- Tekrar eden veri açığı (3. kez tespit, artık kitap-ötesi bir örüntü): "10+ yıllık trend serisi" eksikliği — Buffett turunda HBK/net kâr trendi ve borç/kâr trendi için, bu turda Shiller CAPE (FORMÜL-05) ve kurumsal kaldıraç uyarısı (FORMÜL-07) için AYNI `trends.py` 12-çeyrek sınırı engel oluşturuyor.
- Temettü verisi eksikliği (Buffett turunda tespit edilmişti) bu turda FORMÜL-04 (beklenen getiri ayrıştırması) için de doğrulandı — iki kitap boyunca EN SIK tekrarlanan veri açığı.
- Zweig'in Graham'la AÇIKÇA ayrıştığı nadir nokta: altın/değerli maden enflasyon koruması olarak (İLKE-23 vs Uygulama Notu 8) — ileride `00_sentez.md` için not düşüldü.

## Bölüm bazlı durum (02 — Buffett Finansal Tablolar) — TÜMÜ TAMAMLANDI
| Ana kısım | Bölümler | PDF sayfa | İLKE | FORMÜL | Eşik satırı | Kontrol maddesi | BAYRAK | Commit |
|---|---|---|---|---|---|---|---|---|
| Ön bilgi / Giriş | — | s.1-22 | — | — | — | — | — | İşlenmedi (TOC/giriş, çıkarım gerektirmiyor) |
| **Gelir Tablosu** | Böl.7-20 | s.45-88 | 01-14 (14) | 01-08 (8) | 22 | 10 | 01-10 (10) | bfca764 |
| **Bilanço** | Böl.21-42 | s.89-146 | 15-31 (17) | 09-17 (9) | 17 | 14 | 11-20 (10) | 821ddef |
| **Özkaynaklar** | Böl.43-49 | s.147-165 | 32-43 (12) | 18-23 (6) | 10 | 10 | 21-27 (7) | 53f639d |
| **Nakit Akış Tablosu** | Böl.50-52 | s.168-179 | 44-51 (8) | 24-29 (6) | 6 | 10 | 28-32 (5) | 2460bcd |
| **Değerleme** | Böl.53-57 + Appendix (s.198-201) | s.182-196 | 52-61 (10) | 30-35 (6) | 12 + 9 (appendix) | 10 | 33-36 (4) | **bu turda tamamlandı, henüz commit edilmedi** |
| Terimler Sözlüğü | — | s.201-210 | — | — | — | — | — | Bilinçli olarak ATLANDI (sadece tanım niteliğinde, orijinal kural/eşik kaynağı DEĞİL) |
| Acknowledgments/Index | — | s.211-224 | — | — | — | — | — | İşlenmedi (gerek yok — teşekkür/dizin) |

## Not: Bu PDF taranmış (image-only), metin katmanı yok
`kitaplar/WARREN BUFFETT AND THE INTERPRETATION OF FINANCIAL STATEMENTS.pdf` içinde gömülü metin katmanı YOK. Bölüm çıkarımı PyMuPDF'in `get_textpage_ocr()` fonksiyonu (Tesseract, dpi=300, bazı sayfalarda dpi=450 ile tekrar) ile yapıldı. OCR kalitesi gövde metninde YÜKSEK güvenilir; kitap boyunca TEKRARLAYAN bir zaaf, küçük puntolu BÖLÜM NUMARALARININ (chapter heading rakamları) sık sık yanlış okunmasıydı — HER seferinde İçindekiler tablosuyla (ilk turda çıkarılan TOC) çapraz kontrol edilerek düzeltildi, gövde metninin (rakam/eşik içeren cümlelerin) güvenilirliğini ETKİLEMEDİ. Toplamda yalnızca 1 sayısal eşik kalıcı olarak belirsiz kaldı (Ford SG&A aralığı, Gelir Tablosu turu, s.59) ve appendix tablosunda 2 kalem aritmetik yoluyla türetildi (doğrudan OCR ile okunamadı, s.200/201).

Toplam sayfa: 224 (PDF index). PDF sayfa ≈ kitap sayfası + 20 ofset (4 nokta doğrulandı).

## Sonraki adım
Bu kitap (02) için ana içerik çıkarımı TAMAMLANDI. Olası sonraki adımlar (orkestratörün kararına bağlı):
1. `02_buffett_finansal_tablolar.md`'nin son (Değerleme) bölümünü gözden geçirip commit/push etmek.
2. Sıradaki kitaba geçmek (`kitaplar/` altında henüz işlenmemiş: `common-stocks-and-uncommon-profits.pdf`, `damodaran-on-valuation.pdf`, `Financial Shenanigans.pdf`, `One_Up_On_Wall_Street.pdf`, `the-intelligent-investor-.pdf`).
3. Bu noktada (2. kitap tamamlandığında veya tüm kitaplar bitince) `bilgi-bankasi/00_sentez.md` (kitaplar-arası kesişim/çelişki/çapraz-referans tablosu) oluşturmayı değerlendirmek — README.md'de tanımlı ama henüz oluşturulmadı, şu an SADECE 1 kitap bitti, sentez için erken.

## QuaxisLabs veri eksikleri (kümülatif, TÜM turlar tamamlandı — bu artık NİHAİ liste)
### Gelir Tablosu turundan:
- SG&A (Satış, Genel & İdari Giderler) standalone alan olarak `isyatirim.py` `STANDARD_ITEM_MAP_XI_29`'da YOK.
- Ar-Ge gideri standalone alan olarak YOK.
- Faiz Gideri, SADECE banka şeması (`STANDARD_ITEM_MAP_UFRS`) için var; sanayi/ticaret (`STANDARD_ITEM_MAP_XI_29`) şirketleri için YOK — kitabın en çok vurguladığı gösterge, en büyük veri açığı.
- Vergi Öncesi Kâr / Ödenen Vergi standalone alan olarak XI_29'da YOK (isimlendirme emsali `STANDARD_ITEM_MAP_FINANSMAN`'da var).
- 10 yıllık HBK/net kâr trend serisi YOK (`trends.py` en fazla 12 çeyrek/~3 yıl tutuyor).
- Amortisman/Brüt Kâr oranı: ham veri VAR (`depreciation_amortization`) ama oran `calculator.py`'de hesaplanmıyor — EN UCUZ eklenebilecek gösterge.

### Bilanço turundan:
- ROA (Net Kâr/Toplam Varlık): ham veri VAR, oran `calculator.py`'de HESAPLANMIYOR — EN UCUZ eklenebilecek gösterge.
- Uzun Vadeli Borç Geri Ödeme Süresi (LT Borç/Net Kâr): ham veri VAR, oran YOK.
- "Toplam Yükümlülükler/Özkaynak" (kitaptaki asıl Borç/Özkaynak tanımı): ham veri VAR ama HESAPLANMIYOR — mevcut `calculator.Ratios.debt_to_equity` alanı bunun YERİNE SADECE `financial_debt` (faizli borç) kullanıyor, TANIM FARKI var.
- Net Alacaklar/Brüt Satışlar oranı: ham veri VAR, oran YOK.
- Kısa/Uzun Vadeli Borç oranı: sanayi şirketlerinde ham veri VAR oran YOK; bankalarda ham veri de YOK.
- Hazine Hissesi (treasury_stock): hem ham veri hem oran TAMAMEN EKSİK.
- Envanter, Şerefiye (Goodwill), Maddi Olmayan Duran Varlıklar, ayrı Uzun Vadeli Yatırım kırılımı: DÖRDÜ DE standalone alan olarak yok.

### Özkaynaklar turundan:
- Dağıtılmamış Kârlar (retained_earnings): standalone alan olarak TAMAMEN EKSİK — "Warren'ın zenginleşme sırrı", ne ham veri ne oran mevcut.
- İmtiyazlı Hisse / Adi Hisse / Ödenmiş Sermaye Fazlası: standalone alt kalem olarak yok (sadece toplam `equity` var).
- **POZİTİF BULGU:** ROE (Özkaynak Kârlılığı) QuaxisLabs'ta ZATEN MEVCUT (`calculator.Ratios.roe_annualized`, `BankRatios.roe_annualized`). Ancak hazine-hissesi-düzeltmeli "arındırılmış ROE" versiyonu treasury_stock eksikliği nedeniyle hesaplanamıyor.

### Nakit Akış Tablosu turundan:
- **Capex (Yatırım Harcaması): TAMAMEN EKSİK** — Kitabın Capex/Net Kâr ≤%50/<%25 eşiği TAMAMEN hesaplanamıyor.
- **Ödenen Temettü, Hisse İhracı/Geri Alımı (Net), Borç İhracı/Geri Ödemesi (Net): ÜÇÜ DE TAMAMEN EKSİK.**
- Nakit akış tablosuna dair çekilen TEK kalem `operating_cash_flow` ("4C") — `calculator.Ratios`'ta YOK, sadece Piotroski F-Skoru'nda ikili kriter olarak kullanılıyor.
- Araştırma önerisi (doğrulanmadı): İş Yatırım "4D"/"4E" gibi kodlar olabilir; KAP XBRL'de `ifrs-full_PurchaseOfPropertyPlantAndEquipment`/`DividendsPaid`/`PaymentsForRepurchaseOfShares` standart etiketleri zaten var.

### Değerleme turundan (bu tur — SON bulgular):
- **POZİTİF BULGU (en önemlisi bu turda):** `src/analysis/valuation.py` zaten **Damodaran İstikrarlı Büyüme FCFE modeli** (Gordon büyüme formülü), **Benjamin Graham Sayısı** (F/K×PD/DD≤22,5) ve **Peter Lynch PEG Oranı** içeriyor — kitabın Böl.53-55'teki "equity bond"/tahvil-kapitalizasyonu/büyüme-projeksiyonu felsefesinin DAHA RİGÖRÖZ bir modern karşılığı zaten MEVCUT.
- `_RISK_FREE_RATE_PCT` (TRY %32, USD %4,3, statik/hardcoded) — kitabın "uzun vadeli tahvil oranı" kavramına en yakın mevcut veri noktası, ama CANLI piyasa verisi DEĞİL.
- Vergi Öncesi HBK (`income_before_tax`): Değerleme bölümünün equity-bond formülleri için de gerekli — bu, kitap genelinde ÜÇÜNCÜ kez farklı bir bölümde ortaya çıkan AYNI veri açığı (Gelir Tablosu FORMÜL-06, Değerleme FORMÜL-30/32) — EKLENMESİ için en güçlü gerekçeye sahip tekil alan.
- F/K≥40 mutlak satış eşiği `valuation.py`'de UYGULANMAMIŞ (sadece sektöre göreli kıyas var) — ham veri (`pe_ratio`) hazır olduğundan DÜŞÜK MALİYETLİ bir ekleme.
- Maliyet-üzerinden-getiri (yield on cost) ve elde-tutma-vs-satış-fırsat-maliyeti formülleri BİLİNÇLİ OLARAK "KAPSAM DIŞI" sayıldı (yatırımcıya özgü portföy/maliyet verisi gerektirir, şirket temel verisi değildir) — VERİ EKSİKLİĞİ değil, doğal bir sınır.

## QuaxisLabs geliştirme öncelik özeti (TÜM turlar, tek yerde toplanmış — en ucuzdan en pahalıya)
1. **ROA** ekle — ham veri hazır, tek satır kod (Bilanço).
2. **Amortisman/Brüt Kâr** oranı ekle — ham veri hazır, tek satır kod (Gelir Tablosu).
3. **F/K≥40 mutlak satış eşiği** uyarısı ekle — ham veri hazır (Değerleme).
4. **Uzun Vadeli Borç/Net Kâr** (geri ödeme süresi) ekle — ham veri hazır (Bilanço).
5. **"Toplam Yükümlülük/Özkaynak"** (kitap tanımıyla) ayrı bir alan olarak ekle — ham veri hazır, mevcut dar `debt_to_equity`'yi KORU (Bilanço).
6. **SG&A + Ar-Ge** alt kırılımını isyatirim.py haritasına ekle (kod numaraları yorumlarda zaten biliniyor) (Gelir Tablosu).
7. **income_before_tax** (Vergi Öncesi Kâr) alanını ekle — kitap genelinde 3 AYRI bölümde ihtiyaç duyulan EN YÜKSEK öncelikli tekil alan (Gelir Tablosu + Değerleme).
8. **Faiz Gideri** (sanayi/ticaret şirketleri için) — itemCode araştırması gerekiyor (Gelir Tablosu, en çok vurgulanan gösterge).
9. **Capex + Nakit Akış Finansman Faaliyetleri** (temettü/geri alım/borç) — İş Yatırım "4D"/"4E" araştırması VEYA KAP XBRL etiketleri (Nakit Akış, ikinci en çok vurgulanan gösterge).
10. **Dağıtılmamış Kârlar + Hazine Hissesi** — KAP XBRL standart etiketleri mevcut, isyatirim.py tarafı araştırılmalı (Özkaynaklar).
11. **Envanter, Şerefiye, Maddi Olmayan Duran Varlıklar** — düşük öncelik, ilgili ilkeler çoğunlukla nitel/çok-yıllı karşılaştırma gerektiriyor (Bilanço).

---

## 03 — Damodaran on Valuation (Aswath Damodaran, 2nd Ed., 2006) — TOC çıkarıldı, PLAN AŞAMASINDA

### Kaynak
- `kitaplar/damodaran-on-valuation.pdf` — toplam **929 PDF sayfası**, metin katmanı VAR (OCR gerekmedi, `get_text()` doğrudan çalıştı).
- İçerik gövdesi: PDF s.15 (Chapter 1 başlığı) — PDF s.864 (Chapter 18 sonu). PDF s.865-929 Index.
- Kitabın kendi 3 ana bölümü: **Part One: Discounted Cash Flow Valuation** (Ch.2-6), **Part Two: Relative Valuation** (Ch.7-9), **Part Three: Loose Ends in Valuation** (Ch.10-18) — Ch.1 (Introduction) bu üçünün dışında, girişte.
- Sayfa dönüşümü (DOĞRULANMADI, sonraki turda teyit edilecek): kitap sayfası ≈ PDF index − 14 (Ch.1 PDF s.15 = kitap s.1 varsayımıyla).

### Bölüm Planı (9 KISIM — kullanıcı onayı bekleniyor)
| Kısım | İçerik (bölümler) | PDF sayfa aralığı | Yaklaşık sayfa | Beklenen odak / madde yoğunluğu tahmini |
|---|---|---|---|---|
| **Kısım 1** | Ch.1 Introduction to Valuation + Ch.2 Estimating Discount Rates | s.15-117 | ~103 | Değerleme felsefesi, önyargı/belirsizlik kaynakları, risk tanımı, Özkaynak Maliyeti (CAPM/Beta), Sermaye Maliyeti — yüksek formül yoğunluğu (CAPM, beta hesapları) |
| **Kısım 2** | Ch.3 Measuring Cash Flows + Ch.4 Forecasting Cash Flows | s.118-217 | ~100 | Nakit akışı kategorileri, kazanç normalleştirme, vergi etkisi, yeniden yatırım ihtiyacı, büyüme dönemi tahmini, terminal değer — yüksek formül yoğunluğu |
| **Kısım 3** | Ch.5 Equity DCF Models + Ch.6 Firm Valuation Models | s.218-305 | ~88 | Temettü İskonto Modeli, FCFE, FCFF, Sermaye Maliyeti/APV/Artık Getiri yaklaşımları — Part One'ın kapanışı, çekirdek DCF formülleri |
| **Kısım 4** | Ch.7 Relative Valuation: First Principles + Ch.8 Equity Multiples | s.306-385 | ~80 | Çarpan mantığı, standardizasyon, F/K ve türevleri, dağılım karakteristikleri |
| **Kısım 5** | Ch.9 Value Multiples + Ch.10 Cash/Cross Holdings/Other Assets (+App.10.1) | s.386-477 | ~92 | FD/FAVÖK ve türevleri; nakit/çapraz iştirak/finansal yatırım düzeltmeleri — Part Two kapanışı + Part Three başlangıcı |
| **Kısım 6** | Ch.11 Employee Equity Options + Ch.12 Value of Intangibles (+App.12.1 Option Pricing) | s.478-590 | ~113 | Opsiyon bazlı tazminat düzeltmesi, maddi olmayan varlık değerlemesi, opsiyon fiyatlama modelleri |
| **Kısım 7** | Ch.13 Value of Control + Ch.14 Value of Liquidity | s.591-705 | ~115 | Kontrol primi, likidite iskontosu — nitel+nicel karışık, sıkça eşik/yüzde içerir |
| **Kısım 8** | Ch.15 Value of Synergy + Ch.16 Value of Transparency (+App.16.1, 16.2) | s.706-795 | ~90 | Sinerji değerlemesi/yaygın hatalar, şeffaflık/karmaşıklık skorlama |
| **Kısım 9** | Ch.17 Cost of Distress + Ch.18 Closing Thoughts | s.796-864 | ~69 | Finansal sıkıntı maliyeti, model seçim rehberi ("10 Steps to Better Valuations" — kontrol listesi niteliğinde) |

**Toplam: 9 kısım, ~850 PDF sayfası içerik.** Graham (7 kısım/~625 kitap sayfası, ortalama ~89 sayfa/kısım) ile kıyasla bu kitap hem daha uzun hem formül yoğunluğu daha yüksek (DCF+çarpan+opsiyon fiyatlama modelleri) olduğundan 9 kısıma bölündü; ortalama kısım büyüklüğü (~94 PDF sayfası) Graham ile aynı bandın hafif üzerinde tutuldu.

### Beklenen madde yoğunluğu (kaba tahmin, doğrulanmadı)
Kitap büyük ölçüde NİCEL/formül ağırlıklı (Graham/Buffett'a göre daha az kontrol listesi/kırmızı bayrak, çok daha fazla FORMÜL). Kısım başına kabaca 10-20 formül, 15-25 ilke, 5-15 eşik satırı beklenir; kontrol listesi yoğunlukla sadece Kısım 9'da (Ch.18 "Ten Steps to Better Valuations") belirgin olacaktır.

### Durum
TOC ve bölüm sınırları PyMuPDF `get_text()` ile doğrudan (OCR'sız) çıkarıldı, tüm 18 bölüm başlığı + Part sınırları + appendix'ler PDF içinde regex ile bulunup sayfa numaralarıyla doğrulandı. Kullanıcı 9 kısımlık planı onayladı.

### Bölüm bazlı durum — Kısım 1-3/9 TAMAMLANDI (Part One / Discounted Cash Flow Valuation KISMI'nın TAMAMI bitti) — **KULLANICI TALEBİYLE BU NOKTADA DURDURULDU (token/kota kaygısı)**
| Kısım | Bölümler | PDF sayfa | İLKE | FORMÜL | Eşik satırı | Kontrol maddesi | BAYRAK | Durum |
|---|---|---|---|---|---|---|---|---|
| **Kısım 1** | Ch.1 Introduction to Valuation + Ch.2 Estimating Discount Rates | s.15-117 | 01-57 (57) | 01-24 (24) | 15 + Tablo 2.4 (15 satır kredi notu bandı) | 13 (A:5+B:5+C:3) | 01-07 (7) | TAMAMLANDI, commit `2cbf155` |
| **Kısım 2** | Ch.3 Measuring Cash Flows + Ch.4 Forecasting Cash Flows | s.118-217 | 58-98 (41) | 25-51 (27) | 15 | 8 (D-K) | 08-13 (6) | TAMAMLANDI, commit `a0a1277` |
| **Kısım 3** | Ch.5 Equity DCF Models + Ch.6 Firm Valuation Models | s.218-305 | 99-144 (46) | 52-72 (21) | 12 + Tablo 6.2 (14 satır kredi notu/temerrüt oranı) | 5 (L-P) | 14-18 (5) | TAMAMLANDI, bu turda commit edilecek |
| **Kısım 4** | Ch.7 Relative Valuation: First Principles + Ch.8 Equity Multiples | s.306-385 | 145-186 (42) | 73-87 (15) | 25 | 4 (Q-T) | 19-27 (9) | TAMAMLANDI, commit 62d8f06 |
| **Kısım 5** | Ch.9 Value Multiples + Ch.10 Cash, Cross Holdings, and Other Assets (+App.10.1) | s.386-477 | 187-236 (50) | 88-104 (17) | 26 | 4 (U-X) | 28-34 (7) | TAMAMLANDI, bu turda commit edilecek |
| **Kısım 6-9** | Ch.11-18 + appendix'ler | s.478-864 | — | — | — | — | — | **İŞLENMEDİ. Sıradaki adım: Kısım 6 = Ch.11 Employee Equity Options + Ch.12 Value of Intangibles (+App.12.1 Option Pricing), PDF s.478-590. İLKE-237'den, FORMÜL-105'ten, BAYRAK-35'ten, Kontrol Listesi Y'den devam edilecek.** |

**Kitap geneli TOPLAM sayılar (Kısım 1-5, script ile doğrulandı, kesintisiz/tekrarsız):** İLKE **236** (01-236), FORMÜL **104** (01-104), BAYRAK **34** (01-34), EŞİK toplam **93** satır (15+15+12+25+26) + 2 ayrı kredi-notu-bandı tablosu (Tablo 2.4: 15 satır, Tablo 6.2: 14 satır), KONTROL LİSTESİ **34** madde (A-X, 24 liste).

### Kısım 5 — özel notlar
- Bu Kısımla **Part Two: Relative Valuation** (Ch.7-9) BİTTİ ve **Part Three: Loose Ends in Valuation**'ın İLK bölümü (Ch.10) işlendi — kitabın en yoğun kısımlarından biri (50 İLKE, 92 sayfa), çünkü Ch.10 (Cash/Cross Holdings) hem kavramsal derinlik hem çok sayıda somut illüstrasyon içeriyor.
- **Bu Kısmın EN ÖNEMLİ kod-seviyesi bulgusu, kitaplar arası bugüne kadarki EN SOMUT/EN NET kod hatası tespiti (BAYRAK-28/29):** `calculator.compute_valuation()` çapraz iştirak/azınlık payı düzeltmesi HİÇ YAPMIYOR. İki ayrı somut sonuç: (1) `enterprise_value = market_cap(ana ortaklık payı) + net_debt(TAM konsolide)` — çoğunluk-iştirakli BIST holding şirketlerinde FD/FAVÖK/FD/Satış'ı SİSTEMATİK OLARAK DÜŞÜK gösterir; (2) `pb_ratio = market_cap(ana ortaklık) / equity(TOPLAM, azınlık payı DAHİL — isyatirim.py kod "2N")` — AÇIK bir kapsam uyuşmazlığı, P/BV'yi SİSTEMATİK OLARAK DÜŞÜK gösterir. Kıyasla `pe_ratio` bu sorunu TAŞIMIYOR (hem market_cap hem net_income "3Z" ana-ortaklık-payı bazlı, TUTARLI) — bu üçlü kıyas (pe_ratio doğru, pb_ratio/enterprise_value yanlış) doğrudan koda bakılarak DOĞRULANDI.
- İkinci büyük yapısal bulgu: sektör/piyasa regresyonu (Kısım 4'te ilk tespit edilen "çok-firma karşılaştırma altyapısı yok" eksikliği) BURADA FD çarpanları için de AYNEN GEÇERLİ (FORMÜL-97) — artık İKİ Kısımda (4 ve 5) doğrulanan, kitaplar-arası YENİ bir eksiklik KATEGORİSİ olarak kesinleşti.
- "FD/FAVÖK<7x=ucuz" ve benzeri SABİT sayısal eşik kurallarının (İLKE-197/BAYRAK-30) zaman/sektöre göre KAYAN dağılımlarla ÇÜRÜTÜLMESİ — Kısım 4'teki "ortalamaya göre ucuz" yanılgısıyla (BAYRAK-20) AYNI kök sorunun FD çarpanlarındaki YANSIMASI.
- Vergi oranı (İLKE-209/BAYRAK-31) ve kaldıraç/faiz karşılama (BAYRAK-32) farklarının FD çarpanlarını NE KADAR BÜYÜK saptırabileceği somut örneklerle (Yule Catto: %12,1 ucuz → %20,5 pahalı, TEK değişken eklenince) gösterildi — `income_before_tax`/`interest_expense` eksikliklerinin (Kısım 1/3'ten beri bilinen) PRATİK SONUÇLARI bu Kısımda DAHA SOMUT hale geldi.

### Kısım 4 — özel notlar
- Bu Kısım **Part Two: Relative Valuation**'ın İLK iki bölümünü (Ch.7-8) kapsıyor — Part One (DCF) 3 Kısımda (144 İLKE) bitmişti, Part Two DAHA AZ formül YOĞUNLUĞUNA sahip (15 formül/80 sayfa vs Part One'ın ortalama ~24/103) ama ÇOK DAHA FAZLA sayısal İLLÜSTRASYON/vaka örneği (8 ayrı İllüstrasyon, 25 eşik satırı) içeriyor — kitabın kendi "somut örnek" ağırlığı DCF'ten göreli değerlemeye kaydıkça arttı.
- **Bu Kısmın EN ÖNEMLİ kod-seviyesi bulgusu (BAYRAK-19):** `calculator.ValuationMetrics.price_to_operating_profit` (`market_cap / ttm_operating_profit`) Damodaran'ın "tutarsız tanımlı çarpan" testine (pay=özkaynak, payda=firma-geneli) TAKILIYOR — TAM OLARAK kitabın uyardığı Price/EBITDA hatasının bir varyantı. Düzeltme ÇOK DÜŞÜK maliyetli (`enterprise_value` zaten mevcut, sadece formül değişikliği).
- **Pozitif bulgu:** `ev_revenue` (FD/Hasılat) ZATEN Damodaran'ın "tutarlı" (VS) gelir çarpanı tanımıyla birebir örtüşüyor — QuaxisLabs tesadüfen DOĞRU versiyonu (P/S değil) kullanmış.
- **YENİ eksiklik TÜRÜ tespit edildi (önceki "tekil veri eksik" örüntüsünden farklı):** Sektör/piyasa regresyonu (FORMÜL-82/83/85, agregatif P/E dahil) QuaxisLabs'ın TEKİL varlık analiz mimarisiyle YAPISAL OLARAK UYUŞMUYOR — beta/DPS gibi veri açıkları giderilse BİLE, çoklu-firma cross-sectional istatistik ALTYAPISI (evren-çapında persentil/regresyon) hiç YOK. Bu, kitaplar arası "veri eksik" temasından AYRI, bir "ÖZELLİK/mimari eksikliği" kategorisi olarak ilk kez netleşti.
- PEG oranının büyüme bazı (FORMÜL-74) — kitap NET KÂR/HBK büyümesi ister, QuaxisLabs `revenue_growth_yoy_pct` kullanıyor — TANIM SAPMASI, kök neden yine çok-yıllı kazanç serisi eksikliği (8. tekrar, artık kitaplar-arası EN SIK tekrarlanan tema kesinleşti: DPS + çok-yıllı EPS/net kâr serisi).
- ROE-cost of equity farkı (BAYRAK-25) üzerinden P/BV yorumlama — HER İKİ girdi de (roe_annualized, β=1 basitleştirmeli ke) ZATEN MEVCUT, DÜŞÜK maliyetli bir tutarlılık rozeti önerisi olarak işaretlendi.

**Kısım 1 — özel notlar:**
- Bu PDF'te metin katmanı VAR (Graham/Buffett'ın aksine OCR GEREKMEDİ) — ama kitaptaki formüller çoğunlukla görsel/denklem render olarak gömülü ve `get_text()` ile KAYBOLUYOR; formüllerin çoğu ÇEVRELEYEN metin + değişken tanımları + Illustration 2.1-2.8'deki sayısal örneklerden TERS MÜHENDİSLİKLE yeniden inşa edildi (kitaptaki orijinal denklem gösteriminin birebir kopyası değil — zaten telif kuralına uygun).
- **Bu turun EN YÜKSEK öncelikli tekil bulgusu:** `interest_expense` (faiz gideri) XI_29 (BIST sanayi) şemasında YOK — bu, Graham (Kısım 3) ve Buffett (Gelir Tablosu) turlarından sonra ARTIK 3. kez, farklı bir kitapta/bağlamda (bu kez cost of debt/interest coverage ratio/sentetik kredi notu formülleri, FORMÜL-17/18/19) doğrulandı. XI_29'a bu alanın eklenmesi TEK BAŞINA 3 formülü (+2 kırmızı bayrağı, BAYRAK-06/07) birden çözer.
- **Temettü verisi (DPS) eksikliği** ARTIK 5. kez (Graham 3, Buffett 1, şimdi Damodaran) farklı kitapta tekrarlanan KÜMÜLATİF en sık veri açığı olarak doğrulandı (FORMÜL-15, implied cost of equity).
- **Pazar endeksi (BIST100/S&P500) getiri serisi hiç çekilmiyor** — gerçek CAPM betası (regresyon) ve bottom-up beta bu yüzden UYGULANAMIYOR; `valuation.py`'nin mevcut Damodaran FCFE bloğu β=1 (piyasa ortalaması) sabit varsayımıyla çalışıyor, bu Kısım 1'de AÇIKÇA belgelendi.
- **Pozitif bulgu:** `src/analysis/valuation.py` (Damodaran İstikrarlı Büyüme FCFE modeli) ve `src/analysis/merton.py` (Merton temerrüt modeli) kitabın Ch.1-2'deki kavramlarının (Gordon büyüme DCF, CAPM cost of equity, default riski) KISMİ/basitleştirilmiş uygulamalarını ZATEN İÇERİYOR — Kısım 1'in QuaxisLabs karşılığı notları bu MEVCUT kodun kitabın TAM metodolojisine göre hangi kısayolları (β=1, WACC yok, ülke primi λ ayrıştırması yok) aldığını belgeledi.
- Net Borç formülü (`calculator.net_debt()`) kitaptaki basit tanımdan (borç−nakit) DAHA KAPSAMLI (borç−nakit−finansal yatırımlar) — kitaba göre değil, QuaxisLabs'a göre GÜNCEL/doğru kabul edildi.

### Kısım 2 — özel notlar
- Capex (sermaye harcaması) eksikliğinin bu Kısımdaki ETKİSİ SOMUTLAŞTI: FCFE/FCFF/Özkaynak+Firma Yeniden Yatırım Oranı formüllerinin (FORMÜL-25/26/27/40/45) TAMAMI bu tek veriye bağlı — artık 4. kez (Buffett + Kısım 1 + bu Kısımda 2 ayrı formül grubu) doğrulandı, QuaxisLabs'ın en yüksek hacimli tekil veri açığı.
- **Yeni ucuz eklenti adayları tespit edildi:** Marjinal ROE (`ΔNet Kâr/Δönceki-yıl-özkaynak`) ve "verimlilik kaynaklı büyüme" (`ΔROE/ROE_(t-1)`) — SIFIR yeni ham veri gerektirir, mevcut `net_income`/`equity`/`roe_annualized` serilerinden DOĞRUDAN türetilebilir.
- `fundamental_screens.py` (Faz 21, Greenblatt/Carlisle/Piotroski) dosyasının üst notunda dikkat çekici bir ifade bulundu: "eski 'Değerleme Analizi' panelindeki ... Aswath Damodaran modeli ... TAMAMEN kaldırıldı" — ANCAK kod incelemesi `valuation.py::compute_valuation_assessment()` (Damodaran FCFE bloğu dahil) hâlâ `card.py`/`deep_card.py` tarafından AKTİF olarak import edildiğini gösterdi. Bu muhtemelen İKİ AYRI panelin (eski "Değerleme Analizi" vs yeni Faz 21 "Değerleme" ekranı) KARIŞTIRILMAMASI gereken bir nüans — Kısım 1'deki bulgular (valuation.py'nin Damodaran bloğu MEVCUT) GEÇERLİLİĞİNİ KORUYOR, ama bu çelişki `00_sentez.md` aşamasında (veya bir orkestratör turunda) NET netleştirilmeli.
- Noncash İşletme Sermayesi (nakit + kısa vadeli faizli borç arındırılmış) DÜŞÜK maliyetli bir potansiyel iyileştirme olarak işaretlendi — `fundamental_screens.py`'nin HAM `net_working_capital`'i bu düzeltmeyi henüz YAPMIYOR.
- Temettü/DPS eksikliği bu kitapta 2. kez (Kısım 1 + Kısım 2), kitaplar arası TOPLAM 6. kez doğrulandı — artık QuaxisLabs'ın en SIK tekrarlanan tekil veri açığı olarak KESİNLEŞTİ.

### Kısım 3 — özel notlar
- Part One (Discounted Cash Flow Valuation, Ch.1-6)'ın TAMAMI bu kısımla BİTTİ. En önemli YAPISAL sonuç: **QuaxisLabs'ın mevcut Damodaran değerleme modeli (`valuation.py`) SADECE özkaynak/FCFE (tek-aşamalı, β=1 varsayımlı) tarafını kapsıyor — firma-seviyesi (FCFF/WACC/APV/EVA) DEĞERLEME AİLESİNİN TAMAMI (Ch.6'nın konusu) şu an ürün kapsamı DIŞINDA**, çünkü WACC hiç hesaplanmıyor ve bu tek eksiklik Kısım 3'teki 7 formülün (FORMÜL-63/64/66-72) TAMAMINI bloke ediyor.
- DDM ailesi (Gordon/2-aşamalı/H-modeli/3-aşamalı) TAMAMEN DPS eksikliğine bağlı — bu, kitaplar arası ARTIK 6. kez doğrulanan en sık tekrarlanan veri açığı.
- Tek somut düşük-maliyetli bulgu: BAYRAK-18 (EVA'da defter-değeri cost-of-capital kullanımı tespiti) için gereken `market_cap` (piyasa değeri) ve `equity` (defter değeri) ikisi de ZATEN QuaxisLabs'ta mevcut — ama EVA'nın kendisi WACC eksikliği nedeniyle uygulanamıyor, bu sadece YAN bir sinyal olurdu.

### Kısım 1-3 DURDURULDU notu (ESKİ, artık kapandı) — kullanıcı token/kota kaygısı nedeniyle
Kısım 1-3 TAMAMLANDI ve commit edildi (Part One / Discounted Cash Flow Valuation'ın TAMAMI). Bu oturumda Kısım 4-5 TAMAMLANDI (bkz. yukarı "Kısım 4 — özel notlar" ve "Kısım 5 — özel notlar") ve devamında Kısım 6 işlenmeye devam ediliyor (kullanıcı talimatı: bu oturumda Kısım 4-5-6 sırayla işlenip Kısım 6 sonunda DURULACAK, Kısım 7-9 YENİ bir oturuma bırakılacak). Sıradaki adım: Kısım 6 = Ch.11 Employee Equity Options + Ch.12 Value of Intangibles (+App.12.1 Option Pricing), PDF s.478-590 — ID numaralandırması İLKE-237'den, FORMÜL-105'ten, BAYRAK-35'ten, Kontrol Listesi Y'den DEVAM edecek (kesintisiz). Her kısım kendi standardında BİR KEZ işlenip commit edilmeli, tekrar açılıp genişletilmemeli (zenginleştirme turu YOK — Graham dersi). Kısım 9 sonunda (gelecek oturum) tüm kitap için tutarlılık taraması (script ile İLKE/FORMÜL/BAYRAK numaralarının kesintisiz/tekrarsız doğrulanması) + `_ilerleme.md`'ye kitap geneli TOPLAM sayılar bloğu + final rapor yapılmalı.
