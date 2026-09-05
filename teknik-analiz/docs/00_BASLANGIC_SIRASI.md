# Başlangıç Sırası — hangi promptu, hangi sırayla, hangi dosyadan

**Bu dosya bir kontrol listesidir.** Sonnet oturumunu açtığında bunu yanında tut; sırayla aşağı in, her adımın promptunu parantezde yazan dosyadan kopyala.

> **Kısayol:** Promptları tek tek kopyalayıp yapıştırmak istemiyorsan `docs/SONNET_PROMPTLARI.md`'deki **Prompt A**'yı gönder — Sonnet bu kılavuzu kendisi okuyup sırayı kendisi yürütür, sen yalnızca onay kapılarında karar verirsin.

**Belgeler ve işleri:**

| Dosya | Ne için |
|---|---|
| `docs/00_BASLANGIC_SIRASI.md` | **bu dosya** — sıra, onay kapıları, oturum hijyeni |
| `docs/SONNET_PROMPTLARI.md` | Sonnet'e gönderilecek **açılış ve devam promptları** |
| `docs/TANI_VE_YOL_HARITASI_v2.md` | Tanı + **Faz 0 … Faz 8 promptları** (kod/strateji tarafı) |
| `docs/STRATEJI_DENETIM_TAM.md` | 24 göstergenin tam denetimi — prompt YOK, **referans** belgesi |
| `docs/GORSEL_HATA_TESHISI.md` | ⚠️ **YENİ** — `error/` klasöründeki 10 hatalı çıktının tek tek incelenmesi; Faz 3.5 ve 4d'nin gerekçesi |
| `docs/SITE_TASARIM_YOL_HARITASI.md` | Site planı + **S1…S8 promptları** (arayüz tarafı) |
| `docs/design/grafik_stil_vitrini.html` | Tasarım şartnamesi — 19 grafiğin çalışan SVG üreteci |

---

## Sıfırıncı adım — oturumu açtığında ilk yapılacak

Sonnet oturumunu `teknik-analiz/` klasöründe aç ve **ilk mesaj olarak** şunu gönder (bu bir faz değil, ortamı doğrulama):

```
Bu depoda çalışacağız: QuaxisLabs / teknik-analiz.

Önce şu dört dosyayı OKU, sonra bana tek paragrafla durumu özetle —
kod YAZMA, değişiklik YAPMA:
1. CLAUDE.md (mimari + ilerleme durumu)
2. docs/00_BASLANGIC_SIRASI.md (yapılacak işlerin sırası)
3. docs/TANI_VE_YOL_HARITASI_v2.md (tanı bölümü, bölüm 1)
4. docs/STRATEJI_DENETIM_TAM.md (bölüm A — üç sistemik bulgu)

Sonra `pytest -q -m "not network"` çalıştır ve mevcut test durumunu raporla.
Kaç test yeşil, kırık var mı?
```

Bu adımın çıktısı iki şey söylemeli: **testler yeşil** (beklenen: 560) ve **Sonnet planı okumuş**. İkisi de tamamsa Adım 1'e geç.

---

## Sıra

Her satırda: **ne yapılacağı**, kaç oturum sürer, ve promptun **hangi dosyanın hangi bölümünde** olduğu.

### Bölüm 1 — Temel: sinyaller doğru olsun

| # | Adım | Oturum | Prompt nerede |
|---|---|---|---|
| **1** | **Faz 0** — Sinyal tazeliği + grafik skill/agent + golden test | 1 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 0`** |
| **2** | **Faz 0.5** — Sistemik düzeltmeler (pivot gürültüsü, TF ölçekleme, TF kapısı, hacim) | 1–2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 0.5`** |
| **3** | **Faz 1** — Klasik formasyon motoru v2 | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 1`** |
| **4** | **Faz 2** — İstatistiksel arbitraj v2 | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 2`** |

> **Adım 1 neden ilk:** tazelik filtresi bir günlük iş ama "sinyal kovalıyorum" iş akışının tamamını düzeltiyor. Ayrıca grafik skill'i + golden test, Adım 5-8'in ön koşulu — kurulmazsa görsel iş yine "olmadı" döngüsüne girer.
>
> **Adım 2 neden Adım 3'ten önce:** Faz 1'de eşikler kalibre edilecek. Pivot tanımı düzeltilmeden kalibre edilen her eşik, yanlış bir zigzag üstünde kalibre edilmiş olur ve Faz 0.5'ten sonra baştan yapılır.
>
> **Adım 3 ile 4 paralel yürütülebilir** — farklı dosyalara dokunuyorlar (`patterns/` vs `pairs/`). İki ayrı oturum aç. Ama ikisi de Adım 2'yi bekler.

**🚩 ONAY KAPISI — Adım 2 sonrası.** Sonnet `docs/spec/SISTEMIK_DENETIM_v1.md` üretecek: önce/sonra sinyal sayıları, `atr_mult` taraması, ve **10 grafiğin gözle incelenmiş yorumu**. Bunu sen okumadan Adım 3'e geçme. Bakılacak soru: *"sinyal sayısı düştü mü ve kalanlar gerçekten o formasyon mu?"*

**🚩 ONAY KAPISI — Adım 3 sonrası.** `docs/spec/FORMASYON_DENETIM_v2.md`. Aynı soru, formasyon bazında.

**🚩 ONAY KAPISI — Adım 4 sonrası.** `docs/spec/ARBITRAJ_DENETIM_v2.md`. Beklenen: **606 çift → 20–40 civarı**. Sayı hâlâ yüzlerdeyse bir şey yanlış gitmiştir.

---

### Bölüm 2 — Görsel: grafikler şartnameye otursun

| # | Adım | Oturum | Prompt nerede |
|---|---|---|---|
| **5** | **Faz 3** — SVG çizim motoru (çekirdek + tek kanıt sahnesi) | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 3`** |
| **5.5** | **Faz 3.5** — Renderer kritik hataları (K1/K2/K3) ⚠️ **YENİ** | 1 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 3.5`** |
| **6** | **Faz 4a** — harmonik, yapı raporu, swing/fib, golden zone, haftalık kanal, dönüş haritası | 1 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 4`** (prompt tek, `[4a için]` bölümünü kullan) |
| **7** | **Faz 4b** — klasik formasyonlar + yeni Breakout→FVG stratejisi | 1 | aynı prompt, **`[4b için]`** bölümü |
| **8** | **Faz 4c** — pair, vol harvest, alpha/momentum, EWMAC, MA sistemleri | 1 | aynı prompt, **`[4c için]`** bölümü |
| **8.5** | **Faz 4d** — SMC yapı katmanı: BOS/CHoCH, pivot üçgenleri, temas-sayılı trend, pivot-çıpalı arz/talep ⚠️ **YENİ** | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 4d`** |

> **Faz 4 promptu tektir**, içinde üç grup için ayrı notlar var. Her oturumda promptu yapıştır, sonuna *"Bu oturumda 4b grubunu yap"* diye ekle. Üç grubu tek oturumda yapma — 10. sahnede model ilk sahnenin kurallarını unutur.

**🚩 ONAY KAPISI — Adım 5.5 sonrası.** Üç renderer hatasının önce/sonra görüntülerini kendi gözünle karşılaştır. Özellikle `ma_systems`: MA çizgileri artık fiyatı takip ediyor mu, yoksa hâlâ düz mü?

**🚩 ONAY KAPISI — Adım 8.5 sonrası.** Kendi çıktımızı `ornek1.png` ile yan yana koy. Pivot üçgenleri, temas-sayılı trend çizgisi, kırmızı/yeşil arz-talep bölgeleri — öğe öğe eşleşiyor mu?

**🚩 ONAY KAPISI — Adım 5 sonrası, en önemlisi.** Sonnet tek bir sahneyi (çift tepe/dip) üç temada üretip `docs/design/iterasyon/` altına koyacak. **Bunları kendi gözünle şartnameyle (`grafik_stil_vitrini.html`) yan yana koy.** Ayırt edilemiyorsa Adım 6'ya geç; edilebiliyorsa aynı oturumda düzelttir. Bir tasarım hatasının 19 sahneye yayılması bu projedeki en pahalı hatadır.

---

### Bölüm 3 — Kalan strateji hataları ve evren

| # | Adım | Oturum | Prompt nerede |
|---|---|---|---|
| **9** | **Faz 5** — denetimde bulunan gösterge hatalarını düzelt (`five_zero`, `ewmac` tablosu, `momentum_rank` normalizasyonu, `price_structure` hızı, evren göstergelerinin `/chart` yükü) | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 5`** |
| **10** | **Faz 6** — BİST Evren Taraması sayfası (alpha dağılımı + momentum ısı haritası + sektör) | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 6`** |

> Adım 10'a başlarken `SITE_TASARIM_YOL_HARITASI.md` bölüm **S5**'teki iki eki (sektör rotasyon şeridi + piyasa genişliği) promptun sonuna madde olarak ekle.

---

### Bölüm 4 — Arayüz

| # | Adım | Oturum | Prompt nerede |
|---|---|---|---|
| **11** | **S1 + S2** — Tasarım sistemi (13 bileşen, 3 tema) + uygulama kabuğu (paketler, komut paleti) | 2 | `SITE_TASARIM_YOL_HARITASI.md` → **`### 4.1`** |
| **12** | **S3 + S4** — Tarama ve grafik yüzeyi | 2 | `SITE_TASARIM_YOL_HARITASI.md` → **`### 4.2`** |

> **`TANI_VE_YOL_HARITASI_v2.md`'deki Faz 7'yi ATLA.** Site belgesi onun yerini alıyor — Faz 7 "3 temayı tutarlı kıl + hız" idi, S1–S4 aynı işi daha eksiksiz yapıyor. Faz 7'nin performans maddeleri Adım 15'e (S8) taşındı.
>
> **Adım 11 erken başlayabilir** — SVG motorunu beklemez, sadece kabuğu düzenler. İstersen Bölüm 2 ile paralel yürüt. Ama **Adım 12, Adım 8'i bekler** (inline SVG ve satır-üzeri önizleme buna bağlı).

---

### Bölüm 5 — Kanıt ve kapanış

| # | Adım | Oturum | Prompt nerede |
|---|---|---|---|
| **13** | **Faz 8** — Sinyal doğrulama harness'ı: bu stratejilerin ileriye dönük getirisi var mı | 2 | `TANI_VE_YOL_HARITASI_v2.md` → **`## FAZ 8`** |
| **14** | **S6** — Alarm ve bildirim | 1–2 | `SITE_TASARIM_YOL_HARITASI.md` → **`### 4.3`** |
| **15** | **S8** — Performans, erişilebilirlik, mobil | 1–2 | `SITE_TASARIM_YOL_HARITASI.md` → **`### 4.4`** |
| **16** | **S7** — Pazarlama sitesi | ayrı iş | prompt **yok** — bkz. `SITE_TASARIM_YOL_HARITASI.md` **`### 4.5`** |

> **Adım 16 için neden prompt yok:** içeriğinin yarısı senin iş kararların (fiyat kademeleri, ücretsiz katmanın sınırı, marka sesi) ve en güçlü bölümü Adım 13'ün gerçek ölçümünü bekliyor. Sırası gelince konuşup o zaman yazarız.

---

## Toplam

**18 adım, kabaca 25–31 oturum.** Bölüm 1 (adım 1–4) en kritik kısım: sinyaller doğru olmadan geri kalanı vitrin işi.

Acele bir yol istersen: **adım 1 → 2 → 3 → 4** yap, dur, sistemin ürettiği sinyallere bir hafta bak. Doğru sinyal geliyorsa gerisi rahat gelir; hâlâ gelmiyorsa görsel işe girmeden önce sebebini bulmak gerekir.

---

## Her prompt için değişmeyen kural

Her promptun başına `TANI_VE_YOL_HARITASI_v2.md`'deki **ORTAK BAĞLAM** bloğunu yapıştır (belgede `## 2 · YOL HARİTASI`'nın hemen altında, "Her promptun başına yapıştırılacak ortak blok" başlığı). O blok non-repaint yasağını, katman ayrımını, "560 test yeşil kalacak" kuralını ve "sihirli sayı yasak" ilkesini taşıyor. Atlarsan Sonnet bunları bilmez.

---

## Oturum hijyeni

- **Bir faz yarıda kalırsa** yeni oturumda: *"CLAUDE.md ve docs/PROGRESS_LOG.md'yi oku, Faz X'te nerede kaldığımızı tespit et ve kaldığın yerden devam et."*
- **Her fazın sonunda** `pytest -q -m "not network"` + `tlab lint` + CLAUDE.md güncellemesi. Sonnet bunları atlamaya çalışırsa kabul etme — bir sonraki oturumun bağlamı buna bağlı.
- **Onay kapılarını atlama.** Dört tane var (adım 2, 3, 4, 5 sonrası) ve dördü de bilinçli konuldu.
- **Bağlam şişince yeni oturum aç.** Skill dosyaları, `docs/spec/` ve `docs/PROGRESS_LOG.md` kalıcı hafızandır; sohbet geçmişi değil.
- **Model seçimi:** tasarım/mimari kararların yoğun olduğu adımlar (2, 4, 5, ve 6'nın ilk sahnesi) daha güçlü bir modelde; mekanik port adımları (7, 8) Sonnet'te yeterli. Kural: *ilk örneği güçlü modelde yaz, kalanını Sonnet'e port ettir.*
