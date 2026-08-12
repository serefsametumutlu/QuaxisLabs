# QuaxisLabs Temel Analiz v2 — Yol Haritası

Her fazın sonunda "Bitti sayılma kriteri" var — kriter sağlanmadan sonraki faza geçme. Her fazın promptunu olduğu gibi kopyalayıp local Claude Code oturumuna (Sonnet) yapıştır. Fazlar sıralıdır; Faz 4 (tasarım) istersen Faz 2-3 ile paralel yürüyebilir.

---

## FAZ 0 — Kit kurulumu ve doğrulama (30 dk)

Elle yapılacaklar (aşağıdaki OKUBENI_ONCE.md'de adım adım). Sonra Claude Code'da:

```
quaxis-mimari skill'ini oku ve projeyi hızlıca gezerek skill'deki mimari haritanın güncel kod tabanıyla tutarlı olduğunu doğrula. Tutarsızlık/eksik görürsen skill dosyasını güncelle. Sonra .claude/agents altındaki 5 agent'ın ve .claude/skills altındaki 5 skill'in yüklendiğini listeleyerek teyit et. Son olarak pytest tests/ -q çalıştır ve mevcut test durumunu raporla — hiçbir kod değişikliği yapma.
```

**Bitti kriteri:** 5 agent + 5 skill görünüyor, testler yeşil, mimari skill doğrulanmış.

---

## FAZ 1 — Kitap bilgi çıkarımı (kitap başına 1 oturum önerilir)

PDF'ler `kitaplar/` içinde olmalı. Her kitap için ayrı oturum aç (bağlam taze kalır) ve şu promptu kitap numarasını değiştirerek kullan:

```
kitap-okuyucu agent'ını kullanarak kitaplar/damodaran-on-valuation.pdf dosyasını işle. kitap-bilgi-cikarma skill'indeki prosedürü ve çıktı şablonunu birebir uygula: önce içindekileri çıkar ve bölüm planını bana göster, onayımdan sonra bölüm bölüm ilerle, her bölüm sonunda _ilerleme.md'yi güncelle. Hiçbir sayısal eşiği, formülü, kontrol listesi maddesini veya kırmızı bayrağı atlama; tablolardaki ve vaka örneklerindeki sayılar da eşik kaynağıdır. Her formül için QuaxisLabs veri karşılığını (calculator.py / fetcher katmanı) mutlaka doldur. Kitap metnini kopyalama — damıt. Bittiğinde bilgi-bankasi/ dosyasının İlkeler/Formüller/Eşikler/Kırmızı bayraklar sayılarını özetle.
```

6 kitap bitince, yeni oturumda:

```
kitap-okuyucu agent'ı ile bilgi-bankasi/ altındaki 6 kitap dosyasını okuyup 00_sentez.md'yi üret: (1) yaklaşımların kesişim noktaları (hangi metrikleri birden çok yazar önemsiyor — bunlar yüksek ağırlık adayı), (2) çelişkiler (çözme, listele — mercek mimarisine girdi), (3) metrik → kitap/kod çapraz referans tablosu, (4) projede verisi henüz olmayan metriklerin tam listesi (kaynak önerileriyle). Sonunda temel-analiz-cercevesi skill'indeki 4 merceğe kaba bir bileşen dağılımı öner (sayı/eşik verme, sadece hangi İLKE/FORMÜL/BAYRAK hangi merceğe).
```

**Bitti kriteri:** 6 kitap dosyası + 00_sentez.md hazır; her formülde QuaxisLabs karşılığı dolu.

---

## FAZ 2 — Sektör altyapısı (evren + sınıflandırma)

```
sektor-siniflandirma ve quaxis-mimari skill'lerini uygula. Hedef: BİST ve NASDAQ hisse evrenlerini sektörel sınıflandırmayla DB'ye kazandırmak. Adımlar: (1) temel-analiz-uzmani agent'ı ile docs/spec/spec_sektor_evren.md yaz — ortak üst-sektör taksonomisi, KAP→sektör ve SIC→sektör eşleme tabloları, Company modeline eklenecek alanlar, tazelik/checkpoint kuralları; scripts/explore_kap_sektor.py ve sec_edgar.py'deki mevcut imkanları temel al, gerekirse canlı keşif scriptiyle doğrula. (2) Spec'i bana özetle, onayımı al. (3) kod-gelistirici agent'ı ile uygula: fetcher güncellemeleri, model alanları, scripts/refresh_universe.py (rate-limit'e saygılı, kaldığı yerden devam eden), testler. (4) Scripti çalıştırıp iki evrenin sektör dağılım özetini (sektör başına şirket sayısı tablosu) raporla. Mevcut 569 test yeşil kalacak.
```

**Bitti kriteri:** DB'de sektör etiketli iki evren var; sektör başına n sayıları raporlandı (Faz 3'teki n≥5 kuralı için kritik). ✅ **TAMAMLANDI (2026-08-11, commit `fdf242c`)** — BİST 643 şirket (tam, KAP), NASDAQ 4352 ticker keşfedildi / 1442 SIC ile zenginleştirildi (kademeli — `scripts/refresh_universe.py --market nasdaq --limit N` ile devam ettirilir, checkpoint DB'nin kendisi, 90 gün tazelik penceresi). Her iki piyasada her üst-sektörde n≥5 (istisna: BİST Sağlık/Enerji n=4 — Faz 3'te "yetersiz örneklem" uyarısı tetiklenecek). 1211/1211 test yeşil.

---

## FAZ 3 — Temel Analiz v2 motoru (en büyük faz; 3 alt adım, ayrı oturumlar)

**3a — Spesifikasyon:**
```
temel-analiz-uzmani agent'ı ile, bilgi-bankasi/ (6 kitap + sentez) ve temel-analiz-cercevesi skill'ini temel alarak docs/spec/ altına 4 mercek spec'i yaz: spec_mercek_deger.md, spec_mercek_kalite.md, spec_mercek_buyume.md, spec_mercek_guvenlik.md + spec_bilesik_skor.md. Agent tanımındaki spec şablonuna birebir uy: her bileşen için formül, eşik, ağırlık, kitap referans kodu (örn. 02/FORMÜL-03), geçerli şirket türleri, sektör ayarlaması, kenar durumlar ve gerçek hisse örnekli test senaryoları. Mevcut Radar Skoru ve fundamental_screens.py bileşenlerinin v2'de nereye oturduğunu açıkça belirt (çöpe atma, yerleştir). Sektör-göreli her bileşende sektor-siniflandirma skill'indeki n≥5 ve mutlak taban/tavan kurallarını uygula. Bitince spec'leri bana mercek mercek özetle.
```

**3b — Quant denetimi:**
```
quant-uzmani agent'ı ile docs/spec/ altındaki 5 v2 spec'ini denetle: sayısal kararlılık, birim tutarlılığı, monotonluk, çift sayma (aynı ham verinin mercekler arası korelasyonu), küçük sektör davranışı, eksik veri yeniden dağıtımı. Bulguları docs/spec/quant_denetim_01.md'ye önem sırasıyla yaz. Sonra scripts/kalibrasyon_v2.py yaz ve çalıştır: DB'deki evrenden (Faz 2) çekilebilen tüm şirketler için önerilen eşiklerin metrik dağılımlarını ve her bandın kaç şirket kapsadığını raporla; skor dağılımı yığılma gösteriyorsa eşik revizyonu öner. KRİTİK bulgular spec'lere işlensin (temel-analiz-uzmani ile koordineli), sonra bana net bir "spec'ler kodlamaya hazır" onayı ver.
```

**3c — Kodlama:**
```
kod-gelistirici agent'ı ile onaylı v2 spec'lerini uygula. Yapı: src/analysis/ altında mercek modülleri + bileşik skor (saf matematik, I/O yok, Decimal, reasoning_tr, eksik bileşen orantısal yeniden dağıtım, sürekli enterpolasyon desenleri). Sektör istatistikleri için repository katmanına dönem bazlı cache. pipeline.py'ye v2 bayrakla entegrasyon — v1 davranışı değişmeyecek. Her mercek için spec'teki senaryolarla pytest testleri; docstring'lerde kitap referans kodları. Küçük artışlarla ilerle, her artışta pytest -x -q. Bitince demo scriptiyle THYAO ve AAPL için v2 sonucu üret, mercek mercek raporla ve README Faz Durumu'na kayıt ekle.
```

**Bitti kriteri:** THYAO + AAPL için 4 mercek + bileşik skor üretiliyor, tüm testler yeşil, her bileşen kitaba kadar izlenebilir.

---

## FAZ 4 — Kart tasarım devrimi

```
kart-tasarimcisi agent'ı ile kart-tasarim-sistemi skill'ini uygula. Adımlar: (1) Mevcut tüm şablonları incele, "yapay/jenerik" görünümün teşhisini docs/spec/tasarim_notlari.md'ye yaz. (2) templates/_design_tokens.css'i kur (renk katmanları, tipografi ölçeği, tabular-nums, spacing); font seçimini Playwright ortamında Türkçe gliflerle render ederek doğrula. (3) Ana bilanço kartını (card.html) yeni sistemle yeniden tasarla — v2 mercek profili için kompakt gösterim dahil; build_card_context() arayüzünü bozma. (4) scripts/demo_card.py ile en az 3 veri durumu (bol veri / N/A'lı / RİSKLİ rozet) için PNG üret, her PNG'yi görerek incele, en az 3 iterasyon yap. (5) Onayımdan sonra aynı token sistemini derin kart, teknik, takvim, IPO ve fon kartlarına yay. test_card*.py testleri yeşil kalacak; önce/sonra ekran görüntülerini docs/screenshots/ altına koy.
```

**Bitti kriteri:** Tüm kartlar token sisteminde, 3 veri durumunda da profesyonel, testler yeşil.

---

## FAZ 5 — Piyasa dashboard'u (tüm hisseler, sektörel)

```
Hedef: tüm BİST + NASDAQ evrenini sektörel gruplanmış tek dosyalık HTML dashboard'da görmek. (1) temel-analiz-uzmani ile docs/spec/spec_dashboard.md yaz: toplu tarama pipeline'ı (evrenden şirketleri çekip v2 skorlarını hesaplayan, checkpoint'li, rate-limit'e saygılı batch job — scripts/tarama_toplu.py), sonuçların DB'de saklanması, dashboard'a gömülecek JSON şeması. (2) kod-gelistirici ile batch job'ı yaz; önce küçük bir alt kümeyle (BIST30 + 30 büyük NASDAQ) uçtan uca doğrula, sonra tam evrene aç. (3) kart-tasarimcisi ile dashboard HTML'ini kart-tasarim-sistemi skill'indeki standartlarla üret: BİST/NASDAQ sekmeleri, katlanabilir sektör grupları, sıralanabilir tablo (mercek skorları + bileşik + rozet + ana çarpanlar), arama/filtre, skor renk skalası, sektör n<5 uyarıları görünür. Çıktı: output/dashboard.html — tarayıcıda çift tıkla açılır, sunucu istemez. Telegram botuna /piyasa komutu ekle: dashboard'u yeniden üretip dosya olarak gönderir.
```

**Bitti kriteri:** dashboard.html iki piyasayı sektörel gösteriyor; /piyasa komutu çalışıyor. ✅ **TAMAMLANDI (2026-08-12, commit'ler `341748d`→`bd28e76`)** — spec_dashboard.md onaylı (MarketScanResult tablosu, 7 günlük tazelik, NASDAQ filer_category filtresi, /piyasa force-refresh yapmaz kararı); scripts/tarama_toplu.py yazıldı, pilot evrende (32 BİST + 30 NASDAQ) uçtan uca doğrulandı (62/62 başarılı, 0 hata); output/dashboard.html kart-tasarim-sistemi token sistemiyle 3 iterasyonda üretildi; /piyasa komutu botta çalışıyor. **`--universe full` (tam evren taraması) HENÜZ çalıştırılmadı** — kullanıcı onayı bekliyor, sonraki oturumda tetiklenebilir. 1343 test yeşil.

---

## FAZ 6 — Telegram v2 kartları + kalibrasyon + kapanış

```
(1) kod-gelistirici ile Telegram akışını v2'ye bağla: hisse sorgusunda yeni tasarımlı kart v2 mercek profiliyle gelsin; /menu'ye v2/karşılaştırma seçenekleri; Gemini yorum katmanına mercek bulguları + Fisher/Lynch nitel soru listesi (sayı ürettirme — mevcut commentary sözleşmesi). (2) quant-uzmani ile son kalibrasyon: tam evren taramasından skor dağılımlarını çıkar, rozet eşiklerinin (SAĞLAM/DENGELİ/KARIŞIK/RİSKLİ) piyasa gerçekliğiyle uyumunu raporla, gerekirse spec+kod güncellemesi öner. (3) SCORING_METHODOLOGY.md'yi v2 için genişlet (her mercek, kitap referanslarıyla). (4) pytest tam koşusu + 5 BİST ve 5 NASDAQ hissesiyle uçtan uca duman testi; README Faz Durumu güncellemesi.
```

**Bitti kriteri:** Bot üretimde v2 çalışıyor, metodoloji belgeli, testler yeşil.

---

## Oturum hijyeni (tüm fazlar için)
- Uzun fazlarda bağlam şişince yeni oturum aç; agent'lar/skill'ler ve `docs/spec/` + `bilgi-bankasi/_ilerleme.md` kalıcı hafızandır.
- Bir faz promptu yarıda kaldıysa yeni oturumda: "quaxis-mimari skill'ini oku, docs/spec ve _ilerleme.md'den durumu tespit et, Faz X'e kaldığı yerden devam et" de.
- Onay kapıları (spec özetleri, tasarım iterasyonları) bilinçli konuldu — atlama; en pahalı hata yanlış spec'in kodlanmasıdır.
