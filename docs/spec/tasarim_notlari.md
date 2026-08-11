# Tasarım Notları -- Kart Tasarım Sistemi (Faz: Görsel Kimlik v2)

Bu dosya `kart-tasarim-sistemi` skill'i kapsamında yapılan teşhis, alınan
tasarım kararları ve önce/sonra karşılaştırmalarının kaydıdır (skill
zorunluluğu: "karar ve önce/sonra notu `docs/spec/tasarim_notlari.md`'ye
işlenir").

## 1. Teşhis -- kartlar neden "AI üretmiş jenerik şablon" gibi duruyordu

`src/render/templates/` altındaki 9 şablon (`card.html`, `deep_card.html`,
`calendar_card.html`, `ipo_card.html`, `teaser_card.html`,
`technical_card.html`, `fund_card.html`, `fund_group_card.html`,
`fundamental_screens_card.html`) incelendi. Somut bulgular:

1. **Tek font, ayrım yok.** Her şablon `:root` bloğunda AYNI font-family
   zincirini kullanıyor: `"Cascadia Code", "Cascadia Mono", Consolas, ...
   monospace`. Başlıklar, gövde metni, tablo hücreleri, sayılar -- HEPSİ
   monospace. Monospace, TERMİNAL hissi verir ama okuma hızını düşürür ve
   "tek font = jenerik" izlenimini güçlendirir. Profesyonel finans
   panelleri (Bloomberg, Koyfin) başlık/gövde için grotesk bir sans-serif,
   SADECE sayısal veri için mono kullanır.
2. **Ham Tailwind renkleri, 9 kopyası.** Her şablon kendi `:root` bloğunda
   `--positive: #22c55e; --negative: #ef4444; --accent: #f59e0b;` üçlüsünü
   BİREBİR kopyalamış (98 hex-kod tekrarı, 9 dosyada). Bunlar Tailwind'in
   varsayılan `green-500`/`red-500`/`amber-500` paletidir -- doygunluğu
   yüksek, "template.css" hissi veren, hiçbir markaya özgü olmayan renkler.
   Tek kaynak (token dosyası) yokluğu, bir rengi değiştirmek için 9 dosyayı
   ayrı ayrı düzeltmeyi gerektiriyordu (bakım riski + tutarsızlık riski).
3. **Hiyerarşi yok -- her panel eşit ağırlıkta.** `card.html`'de GELİR
   TABLOSU, BİLANÇO, ÇEYREKLİK SERİ, ARTIŞ/AZALIŞ, BİLANÇO SKORU bölümleri
   AYNI çerçeve + AYNI panel rengi + AYNI başlık büyüklüğüyle çiziliyordu.
   "3 saniyede okunacak tek mesaj" (skor+rozet) diğer tüm kutularla GÖRSEL
   AĞIRLIK yarışına giriyordu -- göz nereye bakacağını bilmiyor.
4. **Kahraman metrik yok.** Skor rakamı (`.score-big`, 60px) ile tablo
   hücreleri (`.data-table td`, 19px) arasındaki oran ~3:1 -- oysa
   "3 saniyede okunur" bir kahraman metrik için bu oran genelde 4-5:1+
   olmalı, ayrıca skor rakamı SADECE font-boyutuyla değil, ayrı bir
   yüzey/zemin katmanıyla da öne çıkmalı (mevcut tasarımda skor kutusu
   diğer `.table-section`/`.mini-chart-block` ile AYNI `var(--panel)`
   zeminini paylaşıyordu -- görsel olarak "bir kutu daha").
5. **Eşit aralıklı, ızgara hissi.** `.score-list` 3 sütunlu SABİT grid,
   `.charts-row` 3 eşit sütun, `.movers-section` 2 eşit sütun -- ritim
   YOK, her şey aynı genişlikte kutucuklara bölünmüş. Boşluk sistemi
   (4px tabanlı ölçek) hiç yoktu; padding/gap değerleri (`24px`, `18px`,
   `16px 20px`, `9px 4px` gibi) HER kural için ayrı ayrı, elle seçilmiş
   sayılardı -- tutarlı bir ritim üretmiyordu.
6. **Jenerik dark-mode griliği.** Tüm zeminler tek bir `--bg`/`--panel`
   ikilisinden (neredeyse aynı ton, `rgba(255,255,255,0.02)` opaklık farkı)
   türetiliyordu -- 3 katmanlı bir derinlik (zemin/panel/öne çıkan panel)
   yoktu, bu da kartı "tek düz koyu kutu" gibi gösteriyordu.
7. **Rozet/ikon dili tutarsız ama önemsiz bir sorun değil:** `movers-col
   li::before` içerik olarak ham `"✓"`/`"!"` karakteri kullanıyor (emoji
   değil ama yine de "check/warning ikonu" klişesi) -- marka kimliğine
   özgü bir işaretleyici değil.
8. **Marka imzası zayıf.** QuaxisLabs logosu/marka rengi (`#2dd4bf`)
   SADECE masthead'de bir kez görünüyor, kartın geri kalanında hiçbir
   izi yok (aksan çizgisi, köşe dili, vb. markaya özgü değil, jenerik
   amber `#f59e0b`).

**Sonuç:** Sorun "kötü CSS" değil, **tek bir tasarım sistemi kaynağının
olmaması**. Her şablon kendi `:root`'unu kopyalayıp yapıştırmış, bu da
"AI'ya her şablonu ayrı ayrı ürettirmiş gibi" bir izlenim yaratıyor.

## 2. Tasarım kararları (`_design_tokens.css`)

Bu oturumda SADECE `card.html` (ana bilanço kartı) yeni token sistemine
taşındı (görev kapsamı, adım 5 -- diğer 8 şablon -- KULLANICI ONAYI
BEKLİYOR). Ama token dosyasının kendisi TÜM şablonları kapsayacak şekilde
tasarlandı.

- **Zemin katmanları (4):** `--bg-canvas` (en koyu, body) →
  `--bg-surface` (kart gövdesi) → `--bg-surface-raised` (öne çıkan panel --
  SADECE skor bölümü ve üst bant kullanır) → `--bg-surface-sunken` (içe
  çökük, tablo başlığı zemini). Eskiden TEK bir `--panel` opaklığı vardı;
  şimdi skor bölümü GERÇEKTEN farklı bir zeminde durduğu için göze "öncelik
  burada" sinyalini veriyor.
- **Mürekkep hiyerarşisi (3 seviye):** `--ink-primary` (başlık/kahraman),
  `--ink-secondary` (gövde/tablo), `--ink-tertiary` (caption/dipnot).
- **Semantik renkler, doygunluğu kısılmış:** `--clr-positive: #45b481`
  (Tailwind `#22c55e`'den daha az doygun, koyu zeminde göz yormuyor),
  `--clr-negative: #d9635c` (Tailwind `#ef4444`'ten daha "tuğla" tonu,
  alarm/neon hissi azaltıldı), `--clr-neutral: #8b93a3`,
  `--clr-warning: #d3a24d`. Her birinin bir de `-soft` (rgba, %14 opaklık)
  versiyonu var -- rozet/etiket arka planı için (çerçeve/gölge yerine
  RENKLİ ZEMİN ile ayrım -- Tufte ilkesi: süsleme değil bilgi).
- **Marka:** `--brand-gold: #c9a54a` (eski `#f59e0b`'den daha az doygun,
  "gold/antik" hissi -- kahraman skor, üst şerit aksanı, DENGELİ rozetinde
  kullanılır) + `--brand-teal: #3fc7ba` (SADECE masthead'de, ikinci marka
  rengi olarak kalır -- değiştirilmedi, kullanıcı zaten bunu marka rengi
  olarak tanıyor).
- **Tipografi:** `--font-sans: "Inter", "Segoe UI", ...` (başlık/gövde),
  `--font-mono: "JetBrains Mono", "Cascadia Code", Consolas, ...` (SADECE
  sayısal veri). Ölçek: `--text-display` (58px, kahraman skor) →
  `--text-h1` (46px, ticker) → `--text-h2` (21px, bölüm başlığı) →
  `--text-h3` (17px) → `--text-body-lg`/`--text-body` (18px/15px) →
  `--text-caption`/`--text-micro` (13px/11.5px). `.q-num` yardımcı sınıfı
  `font-variant-numeric: tabular-nums` + `font-feature-settings: "tnum" 1`
  zorunlu kılar -- tüm tutar/yüzde/oran hücreleri bunu kullanır.
- **Font kaynağı:** Sistemde Inter/IBM Plex/JetBrains Mono kurulu OLMADIĞI
  doğrulandı (`C:\Windows\Fonts` taraması -- sadece Cascadia/Consolas/Segoe
  var). Playwright `page.set_content()` `base_url` desteklemediği için
  (doğrulandı: `inspect.signature` ile parametre yok) harici `<link>`/
  `@font-face url()` dosya yolu ÇALIŞMAZ -- bu yüzden Inter + JetBrains Mono
  (Google Fonts, SIL Open Font License) latin+latin-ext alt kümeleri
  (Türkçe İ/ı/ğ/ş/ö/ü/ç karakterleri latin-ext aralığında) base64 olarak
  `_design_tokens.css` içine GÖMÜLDÜ (~1,1MB, sadece render-time'da
  kullanılır, kullanıcıya gitmez). Render sonucu `docs/screenshots/
  font_test_turkce_glif.png`'de GÖRSEL olarak doğrulandı: İstanbul/İğdır
  (noktalı/noktasız İ-I ayrımı), Şırnak, Öğrenci, Üzüm, Çiçek -- hiçbir
  glif fallback/tofu kutusu göstermedi, hem Inter hem JetBrains Mono
  doğru render etti.
- **Boşluk:** 4px tabanlı `--space-1..9` (4/8/12/16/20/24/32/40/48px).
  Var olan "elle seçilmiş" padding değerleri bu ölçeğe yuvarlandı.
- **Köşe/çizgi:** `--radius-sm/md/lg/pill` (6/10/14/999px),
  `--accent-bar-w: 3px` (imza ince aksan çizgisi -- üst bant ve
  section-title'ların SOL kenarında tutarlı bir "QuaxisLabs" işareti).

## 3. `card.html` -- ne değişti

- **Kahraman hiyerarşi:** BİLANÇO SKORU bölümü artık `--bg-surface-raised`
  zemininde, `--brand-gold` üst aksan çizgisiyle, rakam `--text-display`
  (58px, eskisi 60px'ten çok farklı değil ama artık Inter/gold ile daha
  belirgin) + rozet chip'i (renkli `-soft` zemin + `-strong` metin rengi,
  eskiden sadece metin rengiydi). Skor bileşenleri (Değer/Kalite/Büyüme/
  Güvenlik -- v2 mercek profili VARSA) skor rakamının hemen altında TEK
  satırlık kompakt bir şerit olarak eklendi (segment bar, SKILL.md
  "4 mercek tek satırda okunur" kuralı) -- v1 bileşen listesi (Nakit
  Üretimi/Kaldıraç/ROE/vb.) üçüncül katman olarak ALTTA, daha küçük
  puntoyla kalmaya devam ediyor.
- **İkincil katman:** GELİR TABLOSU/BİLANÇO tabloları artık
  `--bg-surface` zemininde (skor bölümünden daha sönük), başlıkları
  `--text-h2` + `--accent-bar-w` sol çizgi ile ama DOLGU rengi YOK (eskiden
  amber arka planlı chip'ti -- her başlık aynı vurguyu taşıyınca vurgu
  kaybediyordu, şimdi SADECE skor başlığı dolgulu chip, diğerleri çizgi).
- **Üçüncül katman:** ÇEYREKLİK SERİ / ARTIŞ-AZALIŞ bölümleri en sönük
  zeminde (`--bg-surface`, `--border-subtle`), tipografi `--text-caption`/
  `--text-body` ölçeğinde.
- **Tipografi ayrımı:** Başlıklar/etiketler/gövde `--font-sans` (Inter),
  SADECE tutar/yüzde/oran/dönem rakamı hücreleri `--font-mono` +
  `.q-num` (JetBrains Mono, tabular-nums).
- **build_card_context() SÖZLEŞMESİ KORUNDU:** hiçbir mevcut anahtar
  kaldırılmadı/yeniden adlandırılmadı. TEK ek: `mercek_profili` adında
  YENİ, opsiyonel keyword-only parametre (varsayılan `None`) eklendi --
  context'e `mercek_rows` (liste, boşsa `[]`) anahtarı üretir. `None`
  geçildiğinde (mevcut TÜM çağıranlar hâlâ `None` geçiyor) şablon bu
  bölümü tamamen gizler -- v1 davranışı hiçbir çağrıda değişmedi (mevcut
  1200+ test yeşil kaldı, aşağıya bkz.). Bu, "v2 mercek profili İÇİN
  kompakt bir gösterim ekle" talimatının, `build_card_context()`
  imzasını/dönen alan adlarını BOZMADAN karşılanma şeklidir.
- **Python tarafı için AYRI ÖNERİ (bu oturumda YAPILMADI):** `src/bot/
  pipeline.py::run_pipeline()` şu an v1 `ScoreResult`'ı kullanıyor, v2
  `MultiLensScoreResult`'ı ÜRETMİYOR/GEÇİRMİYOR. Kartta mercek şeridinin
  GERÇEK verilerle görünmesi için `run_pipeline()`'ın (veya ayrı bir
  bayrakla) `compute_multi_lens_score_for_ticker()` sonucunu
  `build_card_context(..., mercek_profili=bilesik)` şeklinde geçmesi
  gerekir -- bu, pipeline orkestrasyonuna dokunduğu için KULLANICI KARARI
  gerektiren AYRI bir iş kalemidir (bu oturumun kapsamı: sadece SUNUM,
  hesaplama/orkestrasyon değil).

## 4. Doğrulama döngüsü -- 3 iterasyon (GERÇEKLEŞEN, canlı PNG'lerle)

Demo verisi: `scripts/demo_card.py` (TESTAS, bol veri/tam skor) + iki YENİ
demo script'i -- `scripts/demo_card_na.py` (amortisman + fiyat verisi HİÇ
yok → FAVÖK/Kaldıraç/Değerleme "N/A", cevaplanan ağırlık toplamı %50 eşiğinin
altında kalıp **YETERSİZ VERİ** rozetini de doğrular) ve `scripts/
demo_card_riskli.py` (daralan hasılat, derinleşen zarar, yüksek kaldıraç →
total_score 2,10, **RİSKLİ** rozeti). Her ikisi de gerçek `build_card_context()`
+ `render_card()` çağırır, sahte HTML DEĞİL. PNG'ler `docs/screenshots/`
altına `card_v2_iterN_*` adlarıyla kaydedildi.

- **İterasyon 1** (`card_v2_iter1_*.png`): İlk token geçişi. PNG'leri
  inceleyince 2 somut sorun bulundu: (a) GELİR TABLOSU/BİLANÇO'daki
  "Değişim" sütunu HEM yüzde ("%20,0") HEM metin geçiş etiketi ("veri
  yok", "zarardan kâra geçti") taşıyor ama tüm `<td>`'ler koşulsuz
  `var(--font-mono)` kullanıyordu -- Türkçe metin etiketleri monospace'te
  "terminal hatası" gibi göze batıyordu. (b) `demo_card_na.py`/
  `demo_card_riskli.py`'nin ilk taslağı ölçeksiz (TL yerine ham "300",
  "700") rakamlar kullanıyordu -- F/K gibi oranlar "-2.133.333,33" gibi
  saçma değerler üretti (tasarım hatası DEĞİL, demo veri ölçek hatası).
- **İterasyon 2** (`card_v2_iter2_*.png`): (a) Yeni `.data-table
  td.change-cell` sınıfı eklendi -- SADECE Değişim sütunu `var(--font-sans)`
  kullanır, current/comparison sütunları `var(--font-mono)` kalır (karma
  dil/sayı içeriğine göre font ayrımı). (b) Demo script'lerine `_SCALE =
  1_000_000` çarpanı eklendi (bkz. `demo_card.py`'deki aynı desen) --
  F/K/PD-DD artık "-2,13"/"1,65" gibi gerçekçi değerler gösterdi. PNG'lerde
  doğrulandı: "veri yok"/"kâra karşın zarar açıkladı" artık okunaklı
  sans-serif, tutarlar hâlâ hizalı tabular mono.
- **İterasyon 3** (`card_v2_iter3_*_FINAL.png` + `card_v2_iter3_mercek_
  profili_FINAL.png`): v2 mercek şeridini GERÇEKTEN render edip (manuel
  `MercekProfili` ile, bkz. doğrulama script'i) incelerken hiyerarşi
  ihlali bulundu: mercek isim/rakamı (`--text-caption`/`--text-h3`) ÜÇÜNCÜL
  katmandaki (BİLEŞEN KIRILIMI) isim/rakamdan (`--text-body-lg`/`--text-h3`)
  KÜÇÜK/EŞİT görünüyordu -- ikincil katman, üçüncül katmandan görsel olarak
  daha önemsiz duruyordu. Düzeltme: `.lens-name` → `--text-body-lg` + 
  `--ink-primary`, `.lens-score` → `--text-h2` (bileşen rakamından BÜYÜK),
  `.lens-track` yüksekliği 6px → 8px. Sonuç: kahraman (58px) > mercek
  (21px) > bileşen (17px) sıralaması PNG'de görsel olarak doğrulandı.
  Aynı turda bank/insurance/financing/US context'lerinin `mercek_rows`
  anahtarı OLMADAN (Jinja `{% if mercek_rows %}` -- Undefined güvenle
  falsy) hâlâ hatasız render ettiği `render_html()` ile ayrıca test edildi.
  Bu iterasyon nihai kabul edildi.

## 5. Test durumu

`pytest tests/test_card.py tests/test_card_us.py` her iterasyondan sonra
çalıştırıldı -- final durum: **tümü yeşil** (bkz. oturum sonu raporu).
