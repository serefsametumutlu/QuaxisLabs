---
name: grafik-tasarim-sistemi
description: teknik-analiz grafik/SVG çizim tasarım sistemi standartları — tasarım şartnamesi (docs/design/grafik_stil_vitrini.html), 3 tema, token kuralı, etiket yerleşimi ve ZORUNLU görsel doğrulama döngüsü. Renderer'a (tlab/viz/), göstergelerin çizim primitiflerine (Level/Line/Box/Polygon/Marker) veya herhangi bir grafik/PNG/SVG çıktısına dokunan her işte kullan.
---

# Grafik Tasarım Sistemi

Hedef: `docs/design/grafik_stil_vitrini.html`'deki 19 grafik türüne görsel olarak
**ayırt edilemeyecek** kadar yakın çıktı. Bu dosya bir ilham panosu DEĞİL — 19
`sceneXxx()` fonksiyonunun tamamının ÇALIŞTIĞI, satır satır referans alınacak
**çalıştırılabilir bir şartname**. "Artifact'e benziyor" demek yerine "bu dosyadaki
`sceneClassicPatterns()`'ı birebir çevir" diyeceğiz.

Kökeni: `docs/TANI_VE_YOL_HARITASI_v2.md` Bölüm 1.1 ve 1.6 — grafiklerin artifact'e
benzememesinin kök nedeni araç seçimi (Plotly) VE görsel doğrulama döngüsünün hiç
olmaması. Bu skill ikinci sorunu kapatır; birincisi Faz 3'ün (SVG motoru) işi.

## Tasarım referansı — nasıl okunur

`docs/design/grafik_stil_vitrini.html` içinde ara:
- `THEMES` sabiti — her temanın tam renk/tipografi token seti.
- `sceneXxx()` fonksiyonları — her biri bir grafik türünün TAM çizim mantığı
  (yerleşim, etiketleme, çakışma çözümü dahil).

Yeniden icat ETME — oku, birebir Python'a/SVG'ye çevir. Sapma gerekiyorsa (veri
gerçekçiliği, performans) sapmanın GEREKÇESİNİ yaz.

## Kullanılacak temalar — 3 tanesi, 5 değil

`THEMES`'te 5 tema var (classic/dark/editorial/saas/neon) ama kullanıcı kararı
gereği yalnızca **3'ü** kullanılacak:

| Artifact adı | tlab karşılığı (`tlab/viz/themes.py`) | Türkçe ad |
|---|---|---|
| `dark` | `DARK_TERMINAL` | Terminal Koyu |
| `classic` | `LIGHT_ANALYSIS` | Klasik Beyaz Rapor |
| `editorial` | `KAGIT_RAPORU` | Kağıt Rapor |

`saas` ve `neon` KAPSAM DIŞI — üretilmeyecek, referans alınmayacak.

## Token kuralı

Hardcoded renk **YASAK**. Her renk `tlab/viz/themes.py::Theme` alanından gelir.
Bu dosyadaki `DARK_TERMINAL`/`LIGHT_ANALYSIS`/`KAGIT_RAPORU` hex değerleri
artifact'in `THEMES`'i ile ZATEN eşleşecek şekilde kalibre edilmiş — bir
sapma görürsen artifact'i doğru kabul et ve `themes.py`'yi düzelt (tersini yapma).

## Tipografi

Sayısal her şey mono + `tabular-nums` (kolonlar/eksenler hizalanır). Türkçe
glifler (İ ı Ğ ğ Ş ş Ç ç Ö ö Ü ü) her üç temada render testinden geçmeli —
ekran görüntüsü al, GÖZLE doğrula (glif kutusu/tofu karakteri arama).

## Etiket yerleşimi sözleşmesi

- Hiçbir metin başka bir metinle ÇAKIŞMAZ.
- Mum bulutunun üstüne düşen bir etiket dışarı çıkarılır, noktaya ince bir
  **önder çizgiyle (leader line)** bağlanır (artifact `sceneClassicPatterns`
  satır ~695 civarındaki `KIRILIM`/`RETEST` kutuları örnek).
- Rozetler **hap (pill)** formunda: sabit yükseklik, sabit iç boşluk, yuvarlak
  köşe, dolgu + kontrast metin. Plotly'nin `bgcolor`'ı bunu vermiyordu — SVG
  motorunda kendi hap birincil bileşenin.
- Yalnızca EN GÜNCEL grup etiketlenir (declutter deseni `renderer.py`'den
  zaten biliniyor — `_declutter_levels`/`_latest_per_group`); şekil hep
  çizilir, metin çakışırsa gizlenir, asla üst üste yazılmaz.

## ZORUNLU görsel doğrulama döngüsü

Bu, bu skill'in TEK EN ÖNEMLİ kuralı — aylarca kaybedilen şey tam olarak bu
döngünün eksikliğiydi:

1. Değişiklik yap.
2. GERÇEK veriyle grafik üret (sentetik değil — gerçek `data/ohlcv/` önbelleği).
3. Çıktıyı **Read ile AÇ ve GÖR**. Bakmadan "tamamlandı" deme.
4. Gördüğün sorunları MADDE MADDE yaz (konumlandırma, çakışma, renk, tipografi,
   oran — her biri ayrı madde).
5. Düzelt, 2'ye dön.
6. **En az 3 iterasyon.**
7. **En az 3 veri durumu** ile tekrarla: bol sinyalli bir sembol, tek/hiç
   sinyalli bir sembol, çok uzun geçmişli bir sembol (çakışma stresi —
   onlarca eski Level/Line üst üste binen senaryo).

Çıktı her zaman `docs/design/iterasyon/` altına, iterasyon numarasıyla
adlandırılmış olarak kaydedilir (`01_ilk_deneme.png`, `02_etiket_duzeltmesi.png`,
...) — önce/sonra karşılaştırması bu dosyalardan yapılır.

## Golden (görsel gerileme) testi

`tests/test_viz/golden/` + `tests/test_viz/test_golden.py` — bu skill'in
ürettiği her değişiklik golden testi KIRMAMALI. Kırarsa ya kasıtlı bir tasarım
değişikliğidir (golden'ı `--update-golden` ile bilinçli güncelle, gerekçesini
yaz) ya da bir gerilemedir (düzelt). Sessizce `--update-golden` çalıştırıp
geçmeme — ikisini ayırt et.

## Katman sınırı

`tlab/viz/` HESAP YAPMAZ — yalnızca `IndicatorResult`'ın primitiflerini
(Level/Line/Box/Polygon/Marker/Signal) çizer. Yeni bir görsel öğe (ör. bir
"AKTİF" rozeti, bir köşe etiketi) gerekiyorsa ve gösterge bunu henüz
üretmiyorsa, bu bir **indikatör** eksikliğidir — `tlab/viz/`'e "hesap" ekleyerek
düzeltme, ilgili göstergeye primitif ekle.
