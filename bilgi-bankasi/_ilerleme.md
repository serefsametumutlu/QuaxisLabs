# İlerleme Takibi — kitap-okuyucu

## Genel durum
| # | Kitap | Durum | Hedef dosya |
|---|---|---|---|
| 02 | Warren Buffett and the Interpretation of Financial Statements | **GELİR TABLOSU + BİLANÇO + ÖZKAYNAKLAR işlendi.** Kalan: Nakit Akış (Böl.50-52), Değerleme (Böl.53-57) | `bilgi-bankasi/02_buffett_finansal_tablolar.md` |

## Bölüm bazlı durum (02 — Buffett Finansal Tablolar)
| Ana kısım | Bölümler | PDF sayfa | Durum |
|---|---|---|---|
| Ön bilgi / Giriş | — | s.1-22 | İşlenmedi (TOC/giriş, çıkarım gerektirmiyor) |
| **Gelir Tablosu** | Böl.7-20 | s.45-88 | **TAMAMLANDI** — İLKE-01…14, FORMÜL-01…08, Eşik tablosu (19 satır), Kontrol listesi (10 madde), BAYRAK-01…10. Gözden geçirildi ve git'e commit/push edildi (bfca764). |
| **Bilanço** | Böl.21-42 | s.89-146 | **TAMAMLANDI** — İLKE-15…31 (17), FORMÜL-09…17 (9), Eşik tablosu (17 satır), Kontrol listesi (14 madde), BAYRAK-11…20 (10). Gözden geçirildi ve git'e commit/push edildi (821ddef). |
| **Özkaynaklar** | Böl.43-49 | s.147-165 | **TAMAMLANDI** — İLKE-32…43 (12 yeni), FORMÜL-18…23 (6 yeni), Eşik tablosu (10 satır), Kontrol listesi (10 madde), BAYRAK-21…27 (7 yeni). `02_buffett_finansal_tablolar.md` dosyasına "# ÖZKAYNAKLAR" başlığı altında EKLENDİ (önceki bölümler korunarak). ÖNEMLİ BULGU: kitabın en çok vurguladığı formül olan ROE zaten `calculator.Ratios.roe_annualized` olarak MEVCUT. |
| Nakit Akış Tablosu | Böl.50-52 | s.168-179 (tahmini; Böl.49 s.165'te bitiyor, s.166-167 bölüm-ayırıcı sayfa, Böl.50 s.168'de başlıyor — bu turda doğrulandı) | Bekliyor |
| Değerleme | Böl.53-57 | s.181-196 | Bekliyor |
| Ek (Appendix/Sözlük) | — | s.197-224 | Bekliyor (opsiyonel — çoğunlukla örnek tablo/terim sözlüğü, düşük öncelik) |

## Not: Bu PDF taranmış (image-only), metin katmanı yok
`kitaplar/WARREN BUFFETT AND THE INTERPRETATION OF FINANCIAL STATEMENTS.pdf` içinde gömülü metin katmanı YOK (her sayfa bir JPEG görüntüsü). `get_text()` boş dönüyor. Bölüm çıkarımı PyMuPDF'in `get_textpage_ocr()` fonksiyonu (Tesseract, `tessdata=C:/Program Files/Tesseract-OCR/tessdata`, `language='eng'`, `dpi=300`) ile yapılıyor. OCR kalitesi gövde metninde YÜKSEK güvenilir. Özkaynaklar turunda sayısal eşiklerde OCR belirsizliği YOKTU; tek düzeltme, s.162/s.164'teki iki ardışık bölüm başlığının OCR'da ikisinin de "CHAPTER 49" okunması (İçindekiler tablosuyla çapraz kontrol edilerek 48/49 olarak düzeltildi).

Toplam sayfa: 224 (PDF index). PDF sayfa ≈ kitap sayfası + 20 ofset (4 nokta doğrulandı: Böl.1 kitap s.3→PDF s.23, Böl.7 kitap s.25→PDF s.45, Böl.21 kitap s.69→PDF s.89, Böl.43 kitap s.126→PDF s.147).

## Sonraki adım
Nakit Akış Tablosu ana kısmını (Böl.50-52, PDF s.168-179 tahmini) işle: aynı yöntemle OCR → `_tmp/` → İLKE (İLKE-44'ten devam) / FORMÜL (FORMÜL-24'ten devam) / EŞİK / KONTROL / BAYRAK (BAYRAK-28'den devam) çıkar → `02_buffett_finansal_tablolar.md`'ye "# NAKİT AKIŞ TABLOSU" başlığıyla ekle (mevcut içeriği EZME). ÖZELLİKLE KONTROL EDİLMELİ: Özkaynaklar turunda tespit edilen "Ödenen Temettü" ve "Hisse Geri Alım Harcaması" veri eksikliğinin bu bölümde (Finansman Faaliyetleri kısmı) karşılığı olup olmadığı — bkz. `02_buffett_finansal_tablolar.md` "Uygulama Notları — Özkaynaklar" §4.

## QuaxisLabs veri eksikleri (kümülatif — her turda güncellenir)
### Gelir Tablosu turundan:
- SG&A (Satış, Genel & İdari Giderler) standalone alan olarak `isyatirim.py` `STANDARD_ITEM_MAP_XI_29`'da YOK.
- Ar-Ge gideri standalone alan olarak YOK.
- Faiz Gideri, SADECE banka şeması (`STANDARD_ITEM_MAP_UFRS`) için var; sanayi/ticaret (`STANDARD_ITEM_MAP_XI_29`) şirketleri için YOK — kitabın en çok vurguladığı gösterge, en büyük veri açığı.
- Vergi Öncesi Kâr / Ödenen Vergi standalone alan olarak XI_29'da YOK (isimlendirme emsali `STANDARD_ITEM_MAP_FINANSMAN`'da var).
- 10 yıllık HBK/net kâr trend serisi YOK (`trends.py` en fazla 12 çeyrek/~3 yıl tutuyor).
- Amortisman/Brüt Kâr oranı: ham veri VAR (`depreciation_amortization`) ama oran `calculator.py`'de hesaplanmıyor — EN UCUZ eklenebilecek gösterge.

### Bilanço turundan:
- ROA (Net Kâr/Toplam Varlık): ham veri (`total_assets`, `net_income`) VAR, oran `calculator.py`'de HESAPLANMIYOR — EN UCUZ eklenebilecek gösterge.
- Uzun Vadeli Borç Geri Ödeme Süresi (LT Borç/Net Kâr): ham veri VAR, oran YOK.
- "Toplam Yükümlülükler/Özkaynak" (kitaptaki asıl Borç/Özkaynak tanımı): ham veri VAR ama HESAPLANMIYOR — mevcut `calculator.Ratios.debt_to_equity` alanı bunun YERİNE SADECE `financial_debt` (faizli borç) kullanıyor, TANIM FARKI var.
- Net Alacaklar/Brüt Satışlar oranı: ham veri VAR, oran YOK; `trade_receivables`'ın net mi brüt mü olduğu belirsiz.
- Kısa/Uzun Vadeli Borç oranı: sanayi şirketlerinde ham veri VAR oran YOK; bankalarda ham veri de YOK.
- Hazine Hissesi (treasury_stock): hem ham veri hem oran TAMAMEN EKSİK.
- Envanter, Şerefiye (Goodwill), Maddi Olmayan Duran Varlıklar, ayrı Uzun Vadeli Yatırım kırılımı: DÖRDÜ DE standalone alan olarak yok.

### Özkaynaklar turundan (bu tur):
- Dağıtılmamış Kârlar (retained_earnings): standalone alan olarak TAMAMEN EKSİK — kitabın "Warren'ın zenginleşme sırrı" dediği en önemli tek gösterge, ne ham veri ne oran mevcut. KAP XBRL tarafında `ifrs-full_RetainedEarnings` standart taksonomi etiketi olduğundan eklenmesi görece kolay olabilir.
- İmtiyazlı Hisse / Adi Hisse / Ödenmiş Sermaye Fazlası: standalone alt kalem olarak yok (sadece toplam `equity` var).
- Ödenen Temettü ve Hisse Geri Alım Harcaması: ne bilanço ne gelir tablosu şemasında var — muhtemelen Nakit Akış Tablosu'nda olmalı, SONRAKİ turda kontrol edilecek.
- Kaldıraç Spread'i (borç maliyeti vs getiri oranı): sanayi şirketleri için kavramsal karşılığı yok; bankalar için `BankRatios.net_interest_margin_current` KISMEN benzer ama birebir aynı formül değil.
- **POZİTİF BULGU (istisna):** ROE (Özkaynak Kârlılığı) — kitabın en çok vurguladığı formül — QuaxisLabs'ta ZATEN MEVCUT (`calculator.Ratios.roe_annualized`, `BankRatios.roe_annualized`). Ancak hazine-hissesi-düzeltmeli "arındırılmış ROE" versiyonu (treasury_stock eksikliği nedeniyle) hesaplanamıyor.
