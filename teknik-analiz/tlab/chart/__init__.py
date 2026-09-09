"""Grafik katmanı — `tlab/viz`'in yerini alır.

Ayrım: `tlab/viz` TEK jenerik çizici üzerinden 24 göstergeyi çiziyordu;
burada her stratejinin KENDİ besteleyicisi var ve gösterge TİPLİ bir sonuç
döndürür. Gerekçe ve ölçümler: `docs/KARAR_VE_YENIDEN_INSA.md`.

Kural değişmedi: bu katman HESAP YAPMAZ. Hesap `features`/`indicators`
katmanında biter; buraya yalnızca hazır değer gelir.
"""
