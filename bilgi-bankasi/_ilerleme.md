# İlerleme Takibi — kitap-okuyucu

## Genel durum
| # | Kitap | Durum | Hedef dosya |
|---|---|---|---|
| 02 | Warren Buffett and the Interpretation of Financial Statements | **GELİR TABLOSU + BİLANÇO işlendi.** Kalan: Özkaynaklar (Böl.43-49), Nakit Akış (Böl.50-52), Değerleme (Böl.53-57) | `bilgi-bankasi/02_buffett_finansal_tablolar.md` |

## Bölüm bazlı durum (02 — Buffett Finansal Tablolar)
| Ana kısım | Bölümler | PDF sayfa | Durum |
|---|---|---|---|
| Ön bilgi / Giriş | — | s.1-22 | İşlenmedi (TOC/giriş, çıkarım gerektirmiyor) |
| **Gelir Tablosu** | Böl.7-20 | s.45-88 | **TAMAMLANDI** — İLKE-01…14, FORMÜL-01…08, Eşik tablosu (19 satır), Kontrol listesi (10 madde), BAYRAK-01…10. Gözden geçirildi ve git'e commit/push edildi (bfca764). |
| **Bilanço** | Böl.21-42 | s.89-146 | **TAMAMLANDI** — İLKE-15…31 (17 yeni), FORMÜL-09…17 (9 yeni), Eşik tablosu (17 satır), Kontrol listesi (14 madde), BAYRAK-11…20 (10 yeni). `02_buffett_finansal_tablolar.md` dosyasına "# BİLANÇO" başlığı altında EKLENDİ (mevcut Gelir Tablosu bölümü korunarak). |
| Özkaynaklar | Böl.43-49 | s.146-163 | Bekliyor (not: Böl.43 PDF s.147'de başlıyor, Böl.42 s.146'da bitiyor — bu turda doğrulandı) |
| Nakit Akış Tablosu | Böl.50-52 | s.167-179 | Bekliyor |
| Değerleme | Böl.53-57 | s.181-196 | Bekliyor |
| Ek (Appendix/Sözlük) | — | s.197-224 | Bekliyor (opsiyonel — çoğunlukla örnek tablo/terim sözlüğü, düşük öncelik) |

## Not: Bu PDF taranmış (image-only), metin katmanı yok
`kitaplar/WARREN BUFFETT AND THE INTERPRETATION OF FINANCIAL STATEMENTS.pdf` içinde gömülü metin katmanı YOK (her sayfa bir JPEG görüntüsü). `get_text()` boş dönüyor. Bölüm çıkarımı PyMuPDF'in `get_textpage_ocr()` fonksiyonu (Tesseract, `tessdata=C:/Program Files/Tesseract-OCR/tessdata`, `language='eng'`, `dpi=300`) ile yapılıyor. OCR kalitesi gövde metninde YÜKSEK güvenilir; sadece küçük punto/tablo rakamlarında ara sıra hata var (bkz. `02_buffett_finansal_tablolar.md` "Uygulama Notları" bölümleri — Gelir Tablosu: Ford SG&A aralığı s.59 belirsiz; Bilanço: Ford'un hazine-hissesi-düzeltmeli borç tutarı s.146 belirsiz).

Toplam sayfa: 224 (PDF index). PDF sayfa ≈ kitap sayfası + 20 ofset (4 nokta doğrulandı: Böl.1 kitap s.3→PDF s.23, Böl.7 kitap s.25→PDF s.45, Böl.21 kitap s.69→PDF s.89, Böl.43 kitap s.126→PDF s.147, bu turda ayrıca doğrulandı).

## Sonraki adım
Özkaynaklar ana kısmını (Böl.43-49, PDF s.147-163) işle: aynı yöntemle OCR → `_tmp/` → İLKE (İLKE-32'den devam) / FORMÜL (FORMÜL-18'den devam) / EŞİK / KONTROL / BAYRAK (BAYRAK-21'den devam) çıkar → `02_buffett_finansal_tablolar.md`'ye "# ÖZKAYNAKLAR" başlığıyla ekle (mevcut içeriği EZME).

## QuaxisLabs veri eksikleri (kümülatif — her turda güncellenir)
### Gelir Tablosu turundan:
- SG&A (Satış, Genel & İdari Giderler) standalone alan olarak `isyatirim.py` `STANDARD_ITEM_MAP_XI_29`'da YOK.
- Ar-Ge gideri standalone alan olarak YOK.
- Faiz Gideri, SADECE banka şeması (`STANDARD_ITEM_MAP_UFRS`) için var; sanayi/ticaret (`STANDARD_ITEM_MAP_XI_29`) şirketleri için YOK — kitabın en çok vurguladığı gösterge, en büyük veri açığı.
- Vergi Öncesi Kâr / Ödenen Vergi standalone alan olarak XI_29'da YOK (isimlendirme emsali `STANDARD_ITEM_MAP_FINANSMAN`'da var).
- 10 yıllık HBK/net kâr trend serisi YOK (`trends.py` en fazla 12 çeyrek/~3 yıl tutuyor).
- Amortisman/Brüt Kâr oranı: ham veri VAR (`depreciation_amortization`) ama oran `calculator.py`'de hesaplanmıyor — EN UCUZ eklenebilecek gösterge.

### Bilanço turundan (bu tur):
- ROA (Net Kâr/Toplam Varlık): ham veri (`total_assets`, `net_income`) VAR, oran `calculator.py`'de HESAPLANMIYOR — EN UCUZ eklenebilecek gösterge (Amortisman/Brüt Kâr ile aynı kategori).
- Uzun Vadeli Borç Geri Ödeme Süresi (LT Borç/Net Kâr): ham veri VAR, oran YOK.
- "Toplam Yükümlülükler/Özkaynak" (kitaptaki asıl Borç/Özkaynak tanımı): ham veri (`short_term_liabilities`+`long_term_liabilities`, `equity`) VAR ama HESAPLANMIYOR — mevcut `calculator.Ratios.debt_to_equity` alanı bunun YERİNE SADECE `financial_debt` (faizli borç) kullanıyor, TANIM FARKI var, karıştırılmamalı.
- Net Alacaklar/Brüt Satışlar oranı: ham veri VAR, oran YOK; ayrıca `trade_receivables` alanının net mi brüt mü olduğu belirsiz.
- Kısa/Uzun Vadeli Borç oranı: sanayi şirketlerinde ham veri VAR ama oran YOK; bankalarda (asıl önerilen bağlam) ham veri de YOK (`STANDARD_ITEM_MAP_UFRS`'de kısa/uzun borç ayrımı yok).
- Hazine Hissesi (treasury_stock): hem ham veri hem oran TAMAMEN EKSİK — hem `isyatirim.py` hem `kap_financials.py`'de yok. Kitabın Borç/Özkaynak analizinde ASIL ÖNERDİĞİ düzeltme bu olduğundan önemli bir açık.
- Envanter, Şerefiye (Goodwill), Maddi Olmayan Duran Varlıklar, ayrı Uzun Vadeli Yatırım kırılımı: DÖRDÜ DE standalone alan olarak ne `isyatirim.py`'de ne `kap_financials.py`'de mevcut.
