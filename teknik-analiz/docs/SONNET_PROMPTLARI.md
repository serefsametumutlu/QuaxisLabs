# Sonnet'e Gönderilecek Promptlar

İki prompt var. **A** yalnızca ilk oturumda, **B** sonraki her oturumda.

Amaç: her fazın promptunu tek tek kopyalayıp yapıştırmak zorunda kalmamak. Sonnet kılavuzu (`docs/00_BASLANGIC_SIRASI.md`) kendisi okuyup sırayı kendisi yürütür; sen yalnızca onay kapılarında karar verirsin ve oturum dolunca yenisini açarsın.

---

## PROMPT A — İlk oturum (bir kez)

```
QuaxisLabs / teknik-analiz deposunda çalışacağız.

Bu proje için hazırlanmış bir tanı raporu, bir denetim raporu ve 16 adımlık
bir yol haritası var. Bu haritayı BAŞTAN SONA SEN yürüteceksin. Ben sana
adım adım prompt YAPIŞTIRMAYACAĞIM — her adımın promptu aşağıda adı geçen
dosyaların İÇİNDE; onları sen açacak, ilgili bölümü sen okuyacak ve o
adımı sen uygulayacaksın. "Bana X fazının promptunu yapıştır" DEME; git,
dosyadan oku.

════════════════════════════════════════════════════════════
1) ÖNCE BU BEŞ DOSYAYI OKU — sırayla, tamamını, atlamadan
════════════════════════════════════════════════════════════

  1. CLAUDE.md
     Mimari harita + ilerleme durumu. Non-repaint yasağı burada tanımlı.

  2. docs/00_BASLANGIC_SIRASI.md          ← BU SENİN ANA KILAVUZUN
     16 adımın sırası, her adımın promptunun hangi dosyada olduğu,
     dört onay kapısı, oturum hijyeni kuralları.

  3. docs/TANI_VE_YOL_HARITASI_v2.md
     Bölüm 1 = tanı (altı kök neden, kanıtlarıyla).
     "## FAZ 0" … "## FAZ 8" başlıkları = uygulanacak promptlar.
     "### Her promptun başına yapıştırılacak ortak blok" = müzakereye
     kapalı kurallar. Her faza başlarken bu bloğu kendine hatırlat.

  4. docs/STRATEJI_DENETIM_TAM.md
     24 göstergenin tam denetimi. Prompt YOK, referans belgesi.
     Bölüm A = üç sistemik bulgu (Faz 0.5'in gerekçesi).
     Bölüm B = gösterge gösterge bulgular (Faz 1 ve Faz 5'in girdisi).
     Bölüm C = görsel boşluklar (Faz 4'ün girdisi).

  5. docs/SITE_TASARIM_YOL_HARITASI.md
     Arayüz tarafı. "### 4.1" … "### 4.4" başlıkları = S1…S8 promptları.

════════════════════════════════════════════════════════════
2) DOSYA ENVANTERİ — okuduktan HEMEN SONRA bunu kontrol et
════════════════════════════════════════════════════════════

Şu dosyaların var olup olmadığını kontrol et ve bana RAPORLA:

  docs/00_BASLANGIC_SIRASI.md
  docs/TANI_VE_YOL_HARITASI_v2.md
  docs/STRATEJI_DENETIM_TAM.md
  docs/SITE_TASARIM_YOL_HARITASI.md
  docs/design/grafik_stil_vitrini.html      ← KRİTİK, aşağıya bak
  scripts/pivot_yogunluk_olcumu.py
  scripts/arbitraj_montecarlo.py
  scripts/arbitraj_fdr_kontrol.py

`docs/design/grafik_stil_vitrini.html` YOKSA bunu bana BÜYÜK HARFLE bildir
ve Adım 5'e (Faz 3) GELMEDEN önce mutlaka istememi hatırlat. O dosya 19
grafik türünün ÇALIŞAN SVG üretecidir; Faz 3 ve Faz 4 promptlarının
tamamı onun içindeki `sceneXxx()` fonksiyonlarını satır satır referans
alıyor. O dosya olmadan görsel fazlar YAPILAMAZ — tahminle doldurmaya
ÇALIŞMA, dur ve iste.

Eksik `scripts/*.py` dosyaları Faz 0.5 ve Faz 2'de atıf alıyor; yoksa
o fazlara gelince bana söyle.

════════════════════════════════════════════════════════════
3) NASIL ÇALIŞACAKSIN
════════════════════════════════════════════════════════════

- Adımları `docs/00_BASLANGIC_SIRASI.md`'deki SIRAYLA yürüt. Sıra atlamak
  yok; "bunu sonra yaparız" yok.
- Her adıma başlarken bana TEK SATIRLA söyle: "Adım N — <ad> başlıyorum,
  promptu <dosya> → <başlık>'tan okudum." Sonra çalış.
- Bir adım bitince: ne yaptığını ÖZETLE, test sonucunu ver, ve
  "Adım N+1'e geçeyim mi?" diye SOR. Onayımı almadan sonraki adıma GEÇME.
- ONAY KAPILARI (Adım 2, 3, 4 ve 5 sonrası) — kılavuzda işaretli. O
  noktalarda üreteceğin rapor dosyasını bana özetle ve AÇIKÇA onay iste.
  Özellikle Adım 5'te: ürettiğin grafiği `docs/design/iterasyon/` altına
  koy, bana yolunu ver, ben şartnameyle karşılaştırıp onaylayacağım.
- Bir adım birden fazla oturum sürüyorsa (Faz 1, 2, 3, 5 gibi) oturum
  sonunda `docs/PROGRESS_LOG.md`'ye nerede kaldığını YAZ.

════════════════════════════════════════════════════════════
4) MÜZAKEREYE KAPALI KURALLAR
════════════════════════════════════════════════════════════

Bunlar TANI_VE_YOL_HARITASI_v2.md'deki "ortak blok"un özeti; tam hâlini
oradan oku ve her fazda uygula.

1. NON-REPAINTING. Bir sinyalin t barındaki değeri yalnızca t ve öncesi
   veriyle hesaplanır, sonradan DEĞİŞMEZ. Yasak: df.shift(-n),
   rolling(center=True), find_peaks/argrelextrema sonucunu doğrudan sinyal
   barına yazmak, kapanmamış barla sinyal üretmek. Her indikatör
   tlab/testing/repaint.py::repaint_test'ten geçmeden "tamam" sayılmaz.
2. KATMAN AYRIMI: data → features → indicators → scanner → results → viz.
   Oklar tek yönlü. viz KATMANI HESAP YAPMAZ.
3. Mevcut 560 test yeşil kalacak (`pytest -q -m "not network"`). Kırılan
   her test ya düzeltilir ya da NEDEN geçersiz olduğu yazılı gerekçeyle
   güncellenir. Sessizce silme/skip etme YOK.
4. SİHİRLİ SAYI YASAK. Her eşik ya bir Params dataclass'ında varsayılan
   olarak yaşar ya da kaynağı (kitap/makale/ölçüm) docstring'de yazılıdır.
5. Kapsam dışı GERÇEK bir hata bulursan DÜZELTME — docs/PROGRESS_LOG.md'ye
   "BULUNAN HATA" başlığıyla yaz ve bana bildir.
6. Her fazın sonunda CLAUDE.md "İlerleme Durumu" özetini ve
   docs/PROGRESS_LOG.md'yi güncelle.
7. GÖRSEL İŞLERDE: ürettiğin grafiği Read ile AÇ ve GÖR, gördüğün
   sorunları MADDE MADDE yaz, düzelt, tekrarla — EN AZ 3 İTERASYON.
   Bakmadan "tamamlandı" deme. Bu projede aylarca kaybedilen şey tam
   olarak buydu.

════════════════════════════════════════════════════════════
5) OTURUM YÖNETİMİ
════════════════════════════════════════════════════════════

Bağlamın dolmaya başladığını hissettiğinde (uzun fazların ortasında olur)
YENİ İŞE BAŞLAMA. Şunu yap:
  a) `docs/PROGRESS_LOG.md`'ye durumu yaz: hangi adımdayız, ne bitti, ne
     kaldı, sıradaki somut iş ne.
  b) CLAUDE.md'yi güncelle.
  c) Bana "bağlam doldu, yeni oturum aç" de ve dur.
Ben yeni oturumda kısa bir devam promptu göndereceğim; sen PROGRESS_LOG'dan
kaldığın yeri bulup devam edeceksin.

════════════════════════════════════════════════════════════
6) ŞİMDİ NE YAPACAKSIN
════════════════════════════════════════════════════════════

Bu mesaja cevap olarak SADECE şunları yap — kod YAZMA, dosya DEĞİŞTİRME:

  1. Yukarıdaki beş dosyayı oku.
  2. Dosya envanterini kontrol et, eksikleri raporla.
  3. `pytest -q -m "not network"` çalıştır, sonucu raporla (beklenen: 560
     test yeşil).
  4. Bana ŞU DÖRDÜNÜ tek mesajda ver:
     - Projenin şu anki durumu (2-3 cümle)
     - Üç sistemik bulgunun (A1/A2/A3) ne olduğu, kendi cümlelerinle
       (planı gerçekten okuduğunu böyle göreceğim)
     - Eksik dosyalar listesi
     - Test durumu
  5. Sonunda sor: "Adım 1 (Faz 0) ile başlayayım mı?"

Bu mesajda başka hiçbir şey yapma.
```

---

## PROMPT B — Sonraki her oturum (kısa)

```
QuaxisLabs / teknik-analiz'de kaldığımız yerden devam ediyoruz.

Şunları oku: CLAUDE.md, docs/PROGRESS_LOG.md, docs/00_BASLANGIC_SIRASI.md.

Sonra bana söyle:
- Hangi adımdayız, ne bitti, sırada ne var?
- Testler yeşil mi? (`pytest -q -m "not network"`)

Kurallar önceki oturumdakiyle aynı: adım promptlarını dosyalardan kendin
oku (Faz X → docs/TANI_VE_YOL_HARITASI_v2.md, S-adımları →
docs/SITE_TASARIM_YOL_HARITASI.md), non-repaint yasağı ve katman ayrımı
geçerli, görsel işlerde ürettiğini Read ile açıp GÖR ve en az 3 iterasyon
yap, onay kapılarında dur ve bana sor.

Durumu raporla ve devam etmek için onayımı bekle.
```

---

## Notlar

- **Onay kapıları senin işin.** Dört tane var (Adım 2, 3, 4, 5 sonrası). Sonnet oralarda duracak; sen raporu okuyup karar vereceksin. Özellikle **Adım 5** kritik: tek bir grafiği `docs/design/grafik_stil_vitrini.html` ile yan yana koyup "ayırt edilemiyor mu?" sorusuna kendin cevap ver. Ayırt edilebiliyorsa aynı oturumda düzelttir — o hatanın 19 sahneye yayılması bu projedeki en pahalı hatadır.
- **Model seçimi.** Adım 2, 4, 5 ve 6'nın ilk sahnesi tasarım/mimari kararı yoğun — mümkünse daha güçlü bir modelde yaptır. Adım 7 ve 8 mekanik port, Sonnet fazlasıyla yeterli.
- **Acele edersen:** Adım 1→2→3→4'ü yap, dur, bir hafta sinyallere bak. Doğru sinyal geliyorsa gerisi rahat gelir.
