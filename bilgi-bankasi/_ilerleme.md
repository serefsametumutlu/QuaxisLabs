# İlerleme Takibi — kitap-okuyucu

## Genel durum
| # | Kitap | Durum | Hedef dosya |
|---|---|---|---|
| 02 | Warren Buffett and the Interpretation of Financial Statements | **GELİR TABLOSU (Böl.7-20) işlendi.** Kalan: Bilanço (Böl.21-42), Özkaynaklar (Böl.43-49), Nakit Akış (Böl.50-52), Değerleme (Böl.53-57) | `bilgi-bankasi/02_buffett_finansal_tablolar.md` |

## Bölüm bazlı durum (02 — Buffett Finansal Tablolar)
| Ana kısım | Bölümler | PDF sayfa | Durum |
|---|---|---|---|
| Ön bilgi / Giriş | — | s.1-22 | İşlenmedi (TOC/giriş, çıkarım gerektirmiyor) |
| **Gelir Tablosu** | Böl.7-20 | s.45-88 | **TAMAMLANDI** — İLKE (14), FORMÜL (8), Eşik tablosu (19 satır), Kontrol listesi (10 madde), Kırmızı Bayrak (10) çıkarıldı. `02_buffett_finansal_tablolar.md` dosyasına yazıldı. |
| Bilanço | Böl.21-42 | s.89-142 | Bekliyor |
| Özkaynaklar | Böl.43-49 | s.146-163 | Bekliyor |
| Nakit Akış Tablosu | Böl.50-52 | s.167-179 | Bekliyor |
| Değerleme | Böl.53-57 | s.181-196 | Bekliyor |
| Ek (Appendix/Sözlük) | — | s.197-224 | Bekliyor (opsiyonel — çoğunlukla örnek tablo/terim sözlüğü, düşük öncelik) |

## Not: Bu PDF taranmış (image-only), metin katmanı yok
`kitaplar/WARREN BUFFETT AND THE INTERPRETATION OF FINANCIAL STATEMENTS.pdf` içinde gömülü metin katmanı YOK (her sayfa bir JPEG görüntüsü). `get_text()` boş dönüyor. Bölüm çıkarımı PyMuPDF'in `get_textpage_ocr()` fonksiyonu (Tesseract, `tessdata=C:/Program Files/Tesseract-OCR/tessdata`, `language='eng'`, `dpi=300`) ile yapılıyor. OCR kalitesi gövde metninde YÜKSEK güvenilir; sadece küçük punto/tablo rakamlarında ara sıra hata var (bkz. `02_buffett_finansal_tablolar.md` "Uygulama Notları" §5-6 — Ford SG&A aralığı hâlâ belirsiz, s.59).

Toplam sayfa: 224 (PDF index). PDF sayfa ≈ kitap sayfası + 20 ofset (3 nokta doğrulandı: Böl.1 kitap s.3→PDF s.23, Böl.7 kitap s.25→PDF s.45, Böl.21 kitap s.69→PDF s.89).

## Sonraki adım
Bilanço ana kısmını (Böl.21-42, PDF s.89-142) işle: aynı yöntemle OCR → `_tmp/` → İLKE/FORMÜL/EŞİK/KONTROL/BAYRAK çıkar → `02_buffett_finansal_tablolar.md`'ye Bilanço bölümü olarak ekle (mevcut dosyayı EZME, yeni başlık altına EKLE).

## QuaxisLabs veri eksikleri (bu turda tespit edildi — gelecekte Bilanço/Nakit Akış turlarında da GÜNCELLENECEK)
- SG&A (Satış, Genel & İdari Giderler) standalone alan olarak `isyatirim.py` `STANDARD_ITEM_MAP_XI_29`'da YOK.
- Ar-Ge gideri standalone alan olarak YOK.
- Faiz Gideri, SADECE banka şeması (`STANDARD_ITEM_MAP_UFRS`) için var; sanayi/ticaret (`STANDARD_ITEM_MAP_XI_29`) şirketleri için YOK — kitabın en çok vurguladığı gösterge, en büyük veri açığı.
- Vergi Öncesi Kâr / Ödenen Vergi standalone alan olarak XI_29'da YOK (isimlendirme emsali `STANDARD_ITEM_MAP_FINANSMAN`'da var).
- 10 yıllık HBK/net kâr trend serisi YOK (`trends.py` en fazla 12 çeyrek/~3 yıl tutuyor).
- Amortisman/Brüt Kâr oranı: ham veri VAR (`depreciation_amortization`) ama oran `calculator.py`'de hesaplanmıyor — EN UCUZ eklenebilecek gösterge.
