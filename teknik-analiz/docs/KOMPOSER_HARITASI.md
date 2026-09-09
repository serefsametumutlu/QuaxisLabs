# Komposer Haritası — 27 göstergenin tamamı

**Tarih:** 2026-09-08
**Bağlam:** `docs/KARAR_VE_YENIDEN_INSA.md`

Kullanıcı isteği: *"sadece bu görsellerini gösterdiğin kısmı değil diğer
tüm stratejilerin grafikleri içinde aynı düzenlemeleri istiyorum hepsi
eksiksiz tamamı için"*.

## Anahtar tespit: 27 gösterge = 10 komposer

27 gösterge var ama **27 ayrı grafik tasarımı yok**. Referans görselleri
inceleyince şu çıkıyor: aynı grafik iskeleti farklı formasyonlara
uygulanmış. `HRiOTwUbQAA9WKw` (yükselen kanal) ile `HRiPy4qbUAA1bKc`
(simetrik üçgen) **birebir aynı şablon**; yalnızca sınır çizgilerinin
geometrisi ve vurgu rengi farklı.

Dolayısıyla iş, arketip başına bir komposer yazmak:

| # | Komposer | Kapsadığı göstergeler | Referans görsel | Durum |
|---|---|---|---|---|
| 1 | `boundary_pattern` | `patterns.triangle`, `patterns.wedge`, `patterns.broadening`, `trend.weekly_channel`, `trend.breakouts` | `HRiOTwUbQAA9WKw`, `HRiPy4qbUAA1bKc`, `HRihBa2WIAIZjP_` | ✅ komposer hazır — **adaptörler eksik** |
| 1a | `range_box` | yatay aralık | `HRjNKRZWAAAhfSy` | ✅ **bitti** |
| 1b | `channel` | paralel kanal (CMT kuralı) | `HRiOTwUbQAA9WKw` | ✅ **bitti** |
| 2 | `fib_retracement` | `structure.golden_zone` | `HRhIeAdbcAAL2_B` | ✅ **bitti** |
| 3 | `xabcd` | `harmonic.*` (8), `structure.swing_fib_abcd` | `HRhIeAdbcAAL2_B`, `HRdEu6qaoAEaHIT` | ✅ **bitti** (9 gösterge) |
| 4 | `neckline` | `patterns.double_top_bottom`, `patterns.head_shoulders` | kullanıcının TOBO görseli | ✅ **bitti** — çift dip/tepe + OBO/TOBO, dolgulu gövde, hologram, kutulu etiketler, KIRILIM + RETEST |
| 5 | `pole_flag` | `patterns.flag_pennant` | `HRaULXwaEAA60Z5` | ✅ **bitti** |
| 6 | `zones` | `structure.supply_demand`, `patterns.breakout_fvg` | kullanıcının koyu temalı talep kutusu | ✅ arz/talep **bitti**, FVG eksik |
| 7 | `market_structure` | `structure.price_structure` + BOS/CHoCH | `ornek1.png` | ✅ **bitti** |
| 8 | `series_overlay` | `trend.ma_systems`, `trend.ewmac` | `HRiOTwUbQAA9WKw` | ✅ MA sistemi **bitti**, EWMAC eksik |
| 9 | `pair` | `pair.relative_momentum`, `pair.vol_harvest` + Pair Health | `HRcUk75bgAApv6n` | ✅ **bitti** (rejim gölgeleri + çift eksen) |
| 10 | `universe` | `momentum.alpha_rank`, `momentum.momentum_rank` | — (Faz 6) | ✅ **bitti** |
| 11 | `liquidity` | Corwin–Schultz (yeni) | `HRb_x7YWYAA750T` | ✅ **bitti** |
| 12 | `stats_table` | backtest istatistikleri | `HRt3uuwaEAAWAgK` | ✅ **bitti** |
| 13 | `quadrant_map` | kalabalıklaşma / getiri-hacim / yabancı payı | PDF s.7, 8, 10 | ✅ **bitti** |
| 14 | `breadth` | piyasa genişliği (A-D + MA50 üzeri %) | PDF s.3 | ✅ **bitti** |
| 15 | `factor_heatmap` | faktör sepetleri farkı | PDF s.5 | ✅ **bitti** |

**Kapsam:** 27 göstergenin 24'ü için komposer var; ayrıca PDF'ten çıkan 3 evren aracı. Kalan işin çoğu
komposer YAZMAK değil, mevcut göstergeleri tipli sonuç döndürecek şekilde
**adaptörle bağlamak**.

Ek olarak, gösterge değil ama grafik gereken iki yeni konu:
`liquidity` (Corwin–Schultz, `HRb_x7YWYAA750T`) ve `fund_daily`
(fon getiri tahmini panosu, kullanıcının paylaştığı iki pano görseli).

---

## Her komposerin ortak sözleşmesi

Aşağıdakiler `tlab/chart/frame.py` ve `marks.py`'de **bir kez** yazıldı;
her komposer bunları kullanır, yeniden yazmaz:

1. **Panel iskeleti** — fiyat + alt paneller, paylaşılan x, panel başına
   bağımsız y (`Panel.autorange`).
2. **Etkileşim** — `hovermode="x unified"`, crosshair, `3A/6A/1Y/Tümü`.
3. **Sağ kenar etiketleri** — `cf.edge_label()`, çakışma çözücülü.
4. **Numaralı temas noktaları** — `marks.boundary(touches=[...])`.
5. **Sinyal kutusu** — `marks.signal_box()`, dikey bağlayıcılı.
6. **Bölge bandı** — `marks.zone_band()`, sağ kenarda `AD / alt – üst`.
7. **Fibo merdiveni** — `marks.fib_ladder()`.
8. **Pivot üçgenleri** — `marks.pivot_markers()`, zigzag ÇİZMEZ.

## Her komposer için değişmeyen kabul kriteri

Bir komposer, şu üçü olmadan **bitmiş sayılmaz**:

1. Göstergenin **tipli** bir sonuç döndürmesi (jenerik primitif torbası
   değil) — eksik alanın sessizce boş çizilmesi imkânsız olsun.
2. **Ekran görüntüsü alınıp** referans görselle yan yana konması.
3. Sinyal yoksa **hiçbir şey çizmemesi** — kullanıcı kuralı:
   *"güncel yakın bir sinyal yoksa göstermesin hiçbir şey"*.

## Sinyal tazeliği (tüm komposerler için ortak)

Kullanıcının 1 numaralı kuralı: *"son mumunda o sinyali göreceğim veya
lookback varsa son 3 mumda olan sinyalleri göreceğim"*. Bu, komposer
seviyesinde değil **tarayıcı** seviyesinde uygulanır
(`scanner/results.py::latest_signals(max_bars_ago=...)`), ama her
komposerin başlık şeridinde **sinyalin yaşı bar cinsinden** yazacak.
