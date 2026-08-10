# kitaplar/

6 kitabın PDF'lerini BU klasöre koy. Önerilen dosya adları (Türkçe karakter ve boşluk kullanma):

```
01_graham_akilli_yatirimci.pdf
02_buffett_finansal_tablolar.pdf
03_damodaran_degerleme.pdf
04_fisher_siradan_hisseler.pdf
05_lynch_borsada_tek_basina.pdf
06_schilit_finansal_aldatmacalar.pdf
```

Notlar:
- PDF'ler metin tabanlı olmalı. Taranmış (görüntü) PDF ise projedeki OCR altyapısı (PyMuPDF + pytesseract, `src/fetchers/pdf_ocr.py`) kullanılabilir — kitap-okuyucu agent'a "bu PDF taranmış, OCR ile ilerle" de.
- Bu klasör kişisel kullanımındır; `.gitignore`'a `kitaplar/*.pdf` eklemeyi unutma (telifli içerik repoya gitmesin).
