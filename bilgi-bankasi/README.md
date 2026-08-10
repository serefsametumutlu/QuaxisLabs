# bilgi-bankasi/

kitap-okuyucu agent'ının çıktı klasörü. Buraya elle dosya ekleme; agent şu dosyaları üretir:

- `01..06_*.md` — kitap başına yapılandırılmış çıkarım (İLKE/FORMÜL/BAYRAK kodlarıyla)
- `00_sentez.md` — tüm kitaplar bitince: kesişimler, çelişkiler, metrik→kitap çapraz referans tablosu
- `_ilerleme.md` — kaldığı yer takibi (oturum kesilirse devam için)
- `_tmp/` — geçici bölüm metinleri (iş bitince silinir)

Bu klasör, spec'lerin ve kodun atıf yaptığı kalıcı bilgi kaynağıdır — repoya dahil edilebilir (kitap metni içermez, damıtılmış bilgi içerir).
