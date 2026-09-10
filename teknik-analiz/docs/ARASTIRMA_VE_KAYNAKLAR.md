# Araştırma: kararlar + kaynak listesi

İki bölüm:
1. **Kod kararları** — bağlama sırasında karşıma çıkan, literatüre
   bakmadan veremeyeceğim kararlar ve bulduklarım.
2. **Kaynak listesi** — sistemin BUGÜNKÜ somut boşluklarına göre
   sıralanmış kitap/makale listesi. Her madde "bu bizde neyi düzeltir"
   ile birlikte.

**Dürüstlük notu:** aşağıdaki kaynakların çoğunu bu oturumda TAM METİN
olarak okumadım — arama sonuçları, yayıncı özetleri ve daha önce bu
projeye çıkarılmış notlar üzerinden değerlendirdim. Hangilerinin gerçekten
metin düzeyinde çıkarım yapılmış olduğu (Pesavento, Carver) ayrıca
işaretli. Bir kaynağı sisteme SOKMADAN önce ilgili bölümü gerçekten
okumak gerekir; kitapları gönderirsen `.claude/skills/kitap-bilgi-cikarma`
prosedürüyle işleriz.

---

## 1. Kod kararları

### 1.1 AB=CD'ye X uydurmalı mıyız? — HAYIR (uygulandı)

**Soru:** `structure.swing_fib_abcd` X'siz 3 noktalı (A,B,C→D) üretiyor,
`XabcdPattern` sözleşmesi ise `X,A,B,C` şart koşuyordu.

**Bulgu:** AB=CD, XABCD'nin eksik hâli değil — kendi başına bir formasyon.
5 noktalı harmonikler (Gartley/Bat/Crab/Butterfly/Shark/Cypher) 3/4
noktalı ABCD'yi **içerir**; ABCD daha temel yapı. Gartley'in özgün
formasyonuna Fibonacci oranlarını ilk uygulayan Pesavento'nun AB=CD'si de
X'sizdir.

**Karar:** sözleşme iki iskeleti de kabul ediyor; komposer X'liyi B'de
birleşen iki kanat, X'siziyi tek zikzak olarak çiziyor. Uydurma bir X
yanlış geometri üretirdi. **UYGULANDI.**

### 1.2 Bayrak/flama sınırları — KARAR BEKLİYOR

**Soru:** `patterns.flag_pennant` sonucu yalnızca `pole` çizgisi
veriyor; `PoleFlag` sözleşmesi `upper`/`lower` (bayrak sınırları) istiyor.

**Bulgu (Bulkowski, Encyclopedia of Chart Patterns 2e):** bayrak dört
bileşenli — dik direk, **paralel ya da paralele yakın trend çizgileriyle
sınırlı** küçük dikdörtgen konsolidasyon, konsolidasyon boyunca DÜŞEN
hacim, hacim teyitli kırılım. Bayrak kısmı günlük grafikte ~15 mumdan
kısa olmalı (kitaptaki "3 hafta" günlük hisse grafiğine göre).
Ölçüm kuralı: direk yüksekliği bayrağın tabanına eklenir.
Başarı: standart bayrakta %5 eşiğine ulaşma ~%56; ayı bayrağında ~%55,
tam ölçülü hedefe ulaşma %46. "High and tight flag" ayrı bir tür ve çok
daha yüksek (~%90).

**Öneri:** sınırlar konsolidasyonun tepe/diplerine oturtulmuş **paralel**
bir kanal olmalı (`features/channels.py::regression_channel` ya da
`trend/channel.py`'nin CMT kuralı zaten bunu yapıyor). Bu bir TESPİT
eklemesi — adaptörde değil, `flag_pennant.py`'de yapılmalı.
Ayrıca "high and tight flag" AYRI bir tür olarak ayrılmalı; birlikte
raporlanınca istatistik yanıltıcı oluyor.

### 1.3 `trend.breakouts` — hangi kırılım çizilecek? — KARAR BEKLİYOR

233 sinyal / 126 işaret / ~20 kırılım türü. Faz 8A'da bu gösterge tam
bu yüzden galeriden çıkarılmıştı ("düzeltemiyorsak kaldıralım").

**Öneri:** kırılımları çizmek yerine **skorlayıp en iyisini** çizmek.
`quality_score` zaten var (hacim 0.30 / seviye yaşı 0.20 / temas 0.20 /
gövde 0.15 / mesafe 0.15). En yüksek skorlu 1-2 güncel kırılım + retest.
Ama asıl soru bu ağırlıkların KALİBRE olup olmadığı — Faz 5 madde B
("breakouts skor dağılımı") hâlâ açık.

### 1.4 Golden zone: hangi swing? — GEÇİCİ ÇÖZÜM, kalıcısı gösterge tarafında

Gösterge EN YENİ swing'i "güncel" sayıyor; adaptör EN BASKIN olanı
seçiyor (görsel doğrulamada son swing 6 barlık minik bir düzeltmeydi ve
bölge anlamsız kalıyordu). İki farklı cevap = tespit tarafında bir
belirsizlik. Kalıcı çözüm `structure/golden_zone.py`'de.

---

## 2. Kaynak listesi

Sıralama: **bu sistemdeki somut boşluğa göre**, popülerliğe göre değil.

### Öncelik 1 — Ölçüm ve yanlılık (en büyük boşluğumuz)

Bugün 27 gösterge × 648 sembol × 2 zaman dilimi tarıyoruz ve
**hiçbir göstergenin ileriye dönük getirisi ölçülmedi**. Bu, projenin en
büyük açığı; grafiklerin güzelliğinden çok daha önemli.

1. **David Aronson — *Evidence-Based Technical Analysis* (2006)**
   → **Bizde neyi düzeltir:** veri madenciliği yanlılığı. Aronson,
   sinyal keşfinde çoklu test sorununu ciddiye alan ilk kaynaklardan.
   White's Reality Check ve Monte Carlo permütasyon yöntemlerini,
   ayrıca bunların hangi durumlarda ÇÖKTÜĞÜNÜ anlatıyor.
   → **Somut uygulama:** `tlab/backtest/`e permütasyon testi; bir
   gösterge "çalışıyor" denmeden önce rastgele-etiket dağılımına karşı
   sınanmalı. `discovery.py`de Benjamini-Hochberg zaten var — aynı
   disiplin GÖSTERGE seçimine de uygulanmalı.

2. **Bailey & López de Prado — *The Deflated Sharpe Ratio* (2014)** +
   **López de Prado — *Advances in Financial Machine Learning* (2018)**
   → **Bizde neyi düzeltir:** kaç deneme yaptığımızı hesaba katmadan
   Sharpe raporlamak. Deneme sayısı arttıkça saf gürültüden beklenen
   maksimum Sharpe öngörülebilir biçimde yükseliyor.
   → **Somut uygulama:** parametre ızgaralarımız (ör. pair için
   243 kombinasyon) DSR ile düzeltilmeli. `stop_k`/`max_hold_bars`
   seçimimiz şu an ham OOS medyanına dayanıyor — DSR bunu ya doğrular
   ya çürütür. AFML'in "purged/embargoed cross-validation"ı da
   zaman serisinde sızıntıyı önlemek için doğrudan işimize yarar.

3. **Lo, Mamaysky & Wang — *Foundations of Technical Analysis*
   (Journal of Finance, 2000)**
   → **Bizde neyi düzeltir:** formasyonların ölçülebilir tanımı.
   Çekirdek (kernel) regresyonla otomatik formasyon tanıma öneriyor ve
   1962-1996 ABD hisselerinde koşullu getiri dağılımını koşulsuza karşı
   test ediyor; bazı göstergelerin ek bilgi taşıdığını buluyorlar.
   → **Somut uygulama:** bizim pivot tabanlı tespitimizin yanına ikinci
   bir "bu gerçekten formasyon mu" ölçütü. Ayrıca çift tepede
   kullandığımız ≥22 işlem günü ayrımı bu makaleden geliyor.
   *(Zaten kullanıyoruz, ama makalenin metodolojisi bir doğrulama
   çerçevesi olarak da alınabilir.)*

### Öncelik 2 — Formasyon istatistikleri

4. **Thomas Bulkowski — *Encyclopedia of Chart Patterns* (2e/3e)**
   → **Bizde neyi düzeltir:** her formasyonun kabul ölçütleri ve
   gerçekleşme oranları. Zaten kısmen kullanıyoruz (kama ≥5 temas,
   çift dip ~%4 yakınlık, eğimli boyunda sağ koltukaltı kuralı), ama
   sistematik değil — 6 formasyonun HEPSİ için eşikler kitaptan
   çıkarılıp `pattern_context.py`ye tek yerden konmalı.
   → Özellikle: bayrak/flama (1.2), yükselen-alçalan üçgen hedefleri,
   "throwback/pullback" oranları (retest mantığımız buna dayanıyor).

5. **Bulkowski — *Trading Classic Chart Patterns***
   → Skorlama sistemi var (formasyonu 1-10 arası puanlama). Bizim
   `quality_score`umuzun (1.3) kalibrasyonu için doğrudan referans.

### Öncelik 3 — Sistem/portföy tarafı

6. **Robert Carver — *Systematic Trading*** — *(bu projeye ZATEN metin
   düzeyinde çıkarıldı: `bilgi-bankasi/teknik/11_carver_systematic.md`)*
   → Açık kalan: forecast scalar sabit tablosu `ewmac.py`ye girdi ama
   16 varlıklı handcraft kabul kriteri test edilemedi.

7. **Carver — *Advanced Futures Trading Strategies* (2023)**
   → **Bizde neyi düzeltir:** Carver'ın ilk kitabının üstüne ~30
   somut strateji + her birinin ölçülmüş performansı. Bizim gösterge
   portföyümüzü "hangileri birbirini tekrar ediyor" açısından
   düzenlemek için.

8. **Ernest Chan — *Quantitative Trading* / *Algorithmic Trading***
   → **Bizde neyi düzeltir:** pair/mean-reversion tarafı. Bizde
   Engle-Granger + halflife var; Chan'de Johansen/VECM (STRAT-10 olarak
   kapsam dışı bırakmıştık) ve Kalman filtresiyle DEĞİŞEN beta var.
   `coint_monitor.py`nin (kointegrasyon çürümesi) doğal devamı.

### Öncelik 4 — Mikroyapı / uygulanabilirlik

9. **Corwin & Schultz (2012) — "A Simple Way to Estimate Bid-Ask
   Spreads from Daily High and Low Prices"** *(formülü zaten
   `features/liquidity.py`de)*
   → Açık: bu spread tahmini henüz SİNYAL FİLTRESİ olarak
   kullanılmıyor. BIST'in küçük sermayeli hisselerinde bir sinyalin
   teorik getirisi spread'in altındaysa o sinyal işe yaramaz.

10. **Bouchaud, Bonart, Donier, Gould — *Trades, Quotes and Prices*
    (2018)**
    → **Bizde neyi düzeltir:** işlem maliyeti ve piyasa etkisi
    modellemesi. Backtest'lerimiz sabit komisyon varsayıyor; gerçekte
    BIST'te likidite hisseye göre 100 kat değişiyor.

### Öncelik 5 — Türkiye'ye özel

11. **BIST/gelişmekte olan piyasalar üzerine akademik çalışmalar** —
    isim veremeyeceğim kadar dağınık bir literatür; ama ARANMASI
    gereken üç konu: (a) BIST'te momentum/değer primi var mı,
    (b) enflasyon muhasebesinin bilanço oranlarına etkisi (Bilanço
    Radar tarafı için kritik), (c) endeks yeniden dengeleme (rebalance)
    takvimine bağlı fiyat etkisi — bizim `coint_monitor`ün yapısal
    kırılma uyarısıyla doğrudan ilgili.

---

## 3. Sana önerim

Kitap gönderme sırası olarak:
1. **Aronson** — en büyük açığımızı (ölçüm yok) kapatır
2. **Bulkowski Encyclopedia** — 6 formasyonun eşiklerini tek yerden verir
3. **López de Prado AFML** — çoklu test + zaman serisi CV
4. **Carver Advanced Futures** — gösterge portföyünü seyreltmek için

İlk üçü sistemin "doğru mu çalışıyor" sorusunu cevaplar; dördüncüsü
"fazlalık ne" sorusunu. Grafik/görsel tarafına artık kitap gerekmiyor —
oradaki eksikler ölçümle değil, referans görsellerle kapanıyor.
