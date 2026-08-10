# İlerleme Takibi — kitap-okuyucu

## Genel durum
| # | Kitap | Durum | Hedef dosya |
|---|---|---|---|
| 02 | Warren Buffett and the Interpretation of Financial Statements | **GELİR TABLOSU + BİLANÇO + ÖZKAYNAKLAR + NAKİT AKIŞ TABLOSU işlendi.** Kalan: Değerleme (Böl.53-57) | `bilgi-bankasi/02_buffett_finansal_tablolar.md` |

## Bölüm bazlı durum (02 — Buffett Finansal Tablolar)
| Ana kısım | Bölümler | PDF sayfa | Durum |
|---|---|---|---|
| Ön bilgi / Giriş | — | s.1-22 | İşlenmedi (TOC/giriş, çıkarım gerektirmiyor) |
| **Gelir Tablosu** | Böl.7-20 | s.45-88 | **TAMAMLANDI** — İLKE-01…14, FORMÜL-01…08, Eşik tablosu (19 satır), Kontrol listesi (10 madde), BAYRAK-01…10. Commit/push edildi (bfca764). |
| **Bilanço** | Böl.21-42 | s.89-146 | **TAMAMLANDI** — İLKE-15…31 (17), FORMÜL-09…17 (9), Eşik tablosu (17 satır), Kontrol listesi (14 madde), BAYRAK-11…20 (10). Commit/push edildi (821ddef). |
| **Özkaynaklar** | Böl.43-49 | s.147-165 | **TAMAMLANDI** — İLKE-32…43 (12), FORMÜL-18…23 (6), Eşik tablosu (10 satır), Kontrol listesi (10 madde), BAYRAK-21…27 (7). Commit/push edildi (53f639d). ÖNEMLİ BULGU: ROE zaten `calculator.Ratios.roe_annualized` olarak MEVCUT. |
| **Nakit Akış Tablosu** | Böl.50-52 | s.168-179 | **TAMAMLANDI** — İLKE-44…51 (8 yeni), FORMÜL-24…29 (6 yeni), Eşik tablosu (6 satır), Kontrol listesi (10 madde), BAYRAK-28…32 (5 yeni). `02_buffett_finansal_tablolar.md` dosyasına "# NAKİT AKIŞ TABLOSU" başlığı altında EKLENDİ. KESİN BULGU: Ödenen Temettü/Hisse Geri Alımı/Capex/Borç İhracı — dördü de QuaxisLabs veri modelinde TAMAMEN EKSİK (Özkaynaklar turunda ertelenen soru netleşti). |
| Değerleme | Böl.53-57 | s.182-196 (tahmini; Böl.52 s.179'da bitiyor, s.180-181 bölüm-ayırıcı sayfa, Böl.53 s.182'de başlıyor — bu turda doğrulandı) | Bekliyor |
| Ek (Appendix/Sözlük) | — | s.197-224 | Bekliyor (opsiyonel — çoğunlukla örnek tablo/terim sözlüğü, düşük öncelik) |

## Not: Bu PDF taranmış (image-only), metin katmanı yok
`kitaplar/WARREN BUFFETT AND THE INTERPRETATION OF FINANCIAL STATEMENTS.pdf` içinde gömülü metin katmanı YOK (her sayfa bir JPEG görüntüsü). `get_text()` boş dönüyor. Bölüm çıkarımı PyMuPDF'in `get_textpage_ocr()` fonksiyonu (Tesseract, `tessdata=C:/Program Files/Tesseract-OCR/tessdata`, `language='eng'`, `dpi=300`) ile yapılıyor. OCR kalitesi gövde metninde YÜKSEK güvenilir. Nakit Akış turunda sayısal eşiklerde OCR belirsizliği YOKTU; TEK dikkat çeken nokta Ch50/Ch52 arasındaki "Issuance (Retirement) of Stock, Net" kaleminin Finansman mı Yatırım mı Faaliyetleri altında olduğuna dair bir OCR/tutarlılık şüphesi (s.179) — Ch50'nin kendi tablosu esas alınarak Finansman Faaliyetleri olarak çözüldü (bkz. `02_buffett_finansal_tablolar.md` "Nakit Akış Tablosu" OCR notu).

Toplam sayfa: 224 (PDF index). PDF sayfa ≈ kitap sayfası + 20 ofset (4 nokta doğrulandı: Böl.1 kitap s.3→PDF s.23, Böl.7 kitap s.25→PDF s.45, Böl.21 kitap s.69→PDF s.89, Böl.43 kitap s.126→PDF s.147).

## Sonraki adım
Değerleme ana kısmını (Böl.53-57, PDF s.182-196 tahmini) işle: aynı yöntemle OCR → `_tmp/` → İLKE (İLKE-52'den devam) / FORMÜL (FORMÜL-30'dan devam) / EŞİK / KONTROL / BAYRAK (BAYRAK-33'ten devam) çıkar → `02_buffett_finansal_tablolar.md`'ye "# DEĞERLEME" başlığıyla ekle (mevcut içeriği EZME). Bu, kitabın SON ana içerik kısmı — bittiğinde Appendix/Sözlük (opsiyonel, düşük öncelik) dışında kitap tamamlanmış olacak; muhtemelen bu noktada `00_sentez.md` (kitaplar-arası sentez) ihtiyacı da gündeme gelebilir (henüz bu kitap tek başına bitmedi, sentez şimdilik erken).

## QuaxisLabs veri eksikleri (kümülatif — her turda güncellenir)
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

### Nakit Akış Tablosu turundan (bu tur — KESİNLEŞEN bulgular):
- **Capex (Yatırım Harcaması): TAMAMEN EKSİK** — `isyatirim.py`, `kap_financials.py`, `pipeline.py` üçü de tarandı, hiçbirinde yok. Kitabın bu bölümde en çok vurguladığı gösterge (Capex/Net Kâr ≤%50/<%25 eşiği) TAMAMEN hesaplanamıyor.
- **Ödenen Temettü: TAMAMEN EKSİK** — Özkaynaklar turunda ertelenen soru netleşti: ne bilanço/gelir tablosu ne de nakit akış şemasında var.
- **Hisse İhracı/Geri Alımı (Net): TAMAMEN EKSİK** — aynı şekilde hiçbir şemada yok (treasury_stock eksikliğiyle birlikte, hisse geri alımına dair QuaxisLabs'ta HİÇBİR veri izi bulunmuyor).
- **Borç İhracı/Geri Ödemesi (Net): TAMAMEN EKSİK.**
- Nakit akış tablosuna dair İş Yatırım şemasında ÇEKİLEN TEK kalem: `operating_cash_flow` ("4C") — ama bu da `calculator.Ratios`'ta YOK, sadece `fundamental_screens.py`'de Piotroski F-Skoru'nun ikili kriterinde kullanılıyor. Düşük maliyetli öneri: operating_cash_flow/revenue veya operating_cash_flow/net_income gibi bir "nakit kalite" oranı ham veriden hemen türetilebilir.
- Araştırma önerisi (doğrulanmadı, varsayım): İş Yatırım itemCode'larında "4B"(amortisman)/"4C"(faaliyet NA) sıralamasının devamında "4D"/"4E" gibi kodlarla yatırım/finansman faaliyetleri bulunabilir; KAP XBRL tarafında `ifrs-full_PurchaseOfPropertyPlantAndEquipment`, `ifrs-full_DividendsPaid`, `ifrs-full_PaymentsForRepurchaseOfShares` gibi standart etiketler zaten var, `kap_financials.py`'ye eklenmesi görece kolay olabilir.
