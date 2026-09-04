# Arbitraj Denetim v2 — Faz 2, Adım 4 / 2D (Doğrulama)

**Tarih:** 2026-09-04 · **Kapsam:** `discovery.py` v2'nin (Engle-Granger + Šidák +
Benjamini-Hochberg FDR + out-of-sample doğrulama) mevcut `config/pairs.yaml`'daki 606
çift üzerindeki etkisi + BIST evreninden sıfırdan yeniden keşif (`scripts/pair_denetim.py`).
Gerçek BIST önbellek verisiyle (588/648 sembol fiyatlanabilir, D1, 600 bar), network YOK.

## Özet

Faz 2 tanısının (`docs/TANI_VE_YOL_HARITASI_v2.md` bölüm 1.4) "606 → ~20-40" beklentisi
**KISMEN doğrulandı, kısmen aşıldı.** Mevcut 606 çiftin ham (düzeltmesiz) p<0.05 sayısı
**288'e** (yarısından fazlası eski testin kendi şişirmesinden kaynaklıydı), BH-FDR (q=0.05)
sonrası **141'e** düştü — bu, tanının beklentisinden BİLE daha az agresif bir azalma, tek
başına doğrulayıcı. Ama BİST evreninden **sıfırdan** (Šidák + FDR + out-of-sample ile) tam
rigorla yeniden keşfedilince sonuç **606 → 1**'e indi — tanının "20-40" hedefinin ÇOK
altında. Kök neden ayrıştırıldı (aşağıdaki "Elenme Sebebi Dağılımı"): **out-of-sample (OOS)
doğrulama TEK BAŞINA en agresif filtre** (17→1, %94 azalma) — FDR'den (222→17, %92 azalma)
bile daha sert. Bu, `discover_pairs()`'ın varsayılan `fdr_q=0.05` + `oos_split=0.5`
kombinasyonunun (ikisi AYNI ANDA, çarpımsal olarak) tanının kaynak tablosunun (yalnızca
FDR, OOS'suz) temsil ettiğinden ÇOK daha katı olduğu anlamına geliyor — bu, kullanıcıya
sunulup **KARARA BAĞLANDI** (aşağıdaki "KAPATILDI" bölümü): `oos_split=None`, **17 çift**,
`config/pairs.yaml` bu sonuçla YENİDEN üretildi.

## Yöntem

- Örneklem: BIST evreninden D1'de ≥200 bar önbelleği olan **588/648 sembol** (600 bar
  pencere).
- Adım 1 (mevcut listeyi yeniden doğrulama): `config/pairs.yaml`'daki 606 (y,x) çiftinin
  KAYITLI yönü `engle_granger_pvalue`'ya YENİDEN verildi (tek yön, Šidák YOK — bu adım
  "eski keşfin p-değeri ne kadar güvenilirdi" sorusuna yanıt arıyor, yeni bir keşif değil).
- Adım 2 (sıfırdan yeniden keşif): `discover_pairs(prices, sector_map=..., same_sector_
  only=True, economic_link_map=..., fdr_q=0.05, oos_split=0.5)` — `config/sectors_bist.yaml`
  (637 sembol, 44 sektör) + `config/economic_links.yaml` (5 grup) ile aynı-sektör +
  ekonomik-bağ kombinasyonları (**7334-7296 arası kombinasyon**, örneklem farkına göre
  değişiyor) tarandı.
- Elenme sebebi dağılımı: AYNI veri/parametrelerle `discover_pairs` 3 farklı ayarla
  (yalnızca düzeltilmiş test / +FDR / +FDR+OOS) tekrar koşuldu.

## 1 — Mevcut 606 çiftin yeniden doğrulaması

| Kriter | Hayatta kalan çift |
|---|---|
| Kayıtlı (2026-09-03 üretilen) liste, düzeltmesiz | 606 |
| Aynı çiftler, `engle_granger_pvalue` ile YENİDEN test (tek yön) | **288** |
| + Benjamini-Hochberg FDR (q=0.05, M=579 fiyatlanabilen çift) | **141** |

579/606 çift fiyatlanabildi (27'si önbellekte veri eksikliğinden atlandı). **Ham p<0.05
sayısının 606'dan 288'e düşmesi TEK BAŞINA** eski `adf_pvalue` (tahmin edilmiş kalıntıya
uygulanan ham ADF) kullanımının GERÇEKTEN ~%53 oranında yanlış-pozitif ürettiğinin doğrudan
kanıtı — Faz 2 tanısının Monte Carlo bulgusuyla (ham ADF nominal %5 yerine %14-18 reddediyor)
TUTARLI.

## 2 — Sıfırdan yeniden keşif (BIST evreni, tam rigor)

`discover_pairs` v2, `fdr_q=0.05, oos_split=0.5` (fonksiyonun YENİ varsayılanları) ile
sıfırdan koşulduğunda **606 → 1** çift buldu: **PEKGY/EYGYO** (ikisi de Gayrimenkul/GYO
sektöründe — corr=0.903, p_adjusted=0.00019, halflife=11.7 bar, beta=2.78, hem in-sample
hem out-of-sample'da p<0.01).

### Elenme Sebebi Dağılımı (aynı veri, kademeli olarak sıkılaştırılan ayarlar)

| Aşama | Hayatta kalan çift | Azalma |
|---|---:|---:|
| Ham (eski, düzeltmesiz) kombinasyon taraması (referans: 606 kayıtlı) | 606 | — |
| **A)** Düzeltilmiş test (Engle-Granger + Šidák) + corr/halflife eşikleri, FDR/OOS YOK | 222 | — |
| **B)** A + Benjamini-Hochberg FDR (q=0.05, M≈7334) | 17 | A'dan **%92** |
| **C)** B + out-of-sample doğrulama (oos_split=0.5) — **discover_pairs'in GERÇEK varsayılanı** | **1** | B'den **%94** |

**Okuma:** Faz 2 tanısının kaynak tablosundaki "606→36" rakamı YALNIZCA FDR düzeltmesini
(bu tablonun B satırına en yakın, M farkı yüzünden birebir eşleşmiyor ama aynı mertebe —
17 vs 36) temsil ediyordu, OOS'u DEĞİL. `discover_pairs()`'ın kod olarak sevk edilen
varsayılanı (`fdr_q=0.05` VE `oos_split=0.5` AYNI ANDA) tanının kaynak tablosunun temsil
ettiğinden ÇOK daha katı bir birleşik filtre — **bu, 2B'de bilinçli bir tasarım kararıydı
(DISIPLIN-06'nın "seçim ile doğrulama aynı pencerede olmasın" ilkesini koda gömmek) ama
sonucu (1 çift) 2B yazılırken sayısal olarak ÖLÇÜLMEMİŞTİ.**

## KAPATILDI (2026-09-04, aynı gün) — Karar verildi: Seçenek 2 (`oos_split=None`)

Kullanıcıya 3 seçenek + 17 çiftin tam listesi (sembol/sektör/corr/p/halflife/beta) +
gerçek backtest örnekleri (AKBNK/VAKBN, ADGYO/PEKGY, FONET/EDATA, IZMDC/ISDMR —
`mode="mean_reversion"`, gerçek BIST verisiyle) sunuldu. **Karar: Seçenek 2** —
`oos_split=None` (yalnızca FDR), **17 çift**. Gerekçe (kullanıcı diyaloğundan):
sayı olarak tanının "20-40" hedefine daha yakın; OOS'un getirdiği ek güvenlik,
1 çiftlik bir sisteme indirgenmesini haklı çıkaracak kadar değerli görülmedi.

`config/pairs.yaml` bu kararla YENİDEN üretildi (17 çift, `scripts/pair_denetim.py`
`main()`'in varsayılanı da `FDR_Q=0.05, OOS_SPLIT=None` olarak güncellendi — ileride
betik tekrar çalıştırılırsa AYNI kararı üretir; `oos_split=0.5` ile tam rigor ölçmek
isteyen biri bu iki sabiti elle değiştirebilir). Backtest örnekleri karışık bir tablo
gösterdi (FONET/EDATA %12 kâr/%78 kazanma oranı, ADGYO/PEKGY −%25 zarar/%44 kazanma
oranı) — bu, OOS'suz seçilen çiftlerin bazılarının GERÇEKTEN zayıf çıkabileceğinin
somut kanıtı; kullanıcı bunu bilerek 17 çiftlik listeyi seçti.

**Mimari netlik notu (kullanıcı sorusu üzerine belgelenen):** `config/pairs.yaml`
SABİT bir liste — `tlab/scanner/engine.py::run()` yalnızca bu dosyadaki çiftler için
iş açar (`for y_sym, x_sym in pairs or []`), evrenin geri kalanına pair göstergeleri
için HİÇ bakılmaz. Listedeki olmayan bir çift (ör. TOASO/FROTO, ASELS/SDTTR,
TCELL/TTKOM — üçü de kontrol edildi, hiçbiri corr/kointegrasyon eşiklerini
geçmiyor) asla otomatik sinyal üretmez; listenin genişlemesi yalnızca `pair_
denetim.py`'nin elle/periyodik olarak yeniden çalıştırılmasıyla olur.

---

## (ARŞİV) Orijinal "Karar Gerektiren Bulgu" — artık KAPATILDI, aşağıdaki bölüm
## tarihsel referans için bırakıldı

## Karar Gerektiren Bulgu — OOS + FDR birleşimi 606 çifti 1'e indirdi

`discover_pairs()`'ın şu anki varsayılanlarıyla (`fdr_q=0.05, oos_split=0.5`) üretilen
`config/pairs.yaml`, `pair.relative_momentum`/`pair.vol_harvest` göstergeleri için
**yalnızca 1 alım-satılabilir çift** sunuyor — bu, sistemi fiilen tek bir çifte
daraltıyor. Kod DOĞRU çalışıyor (OOS gerçekten DISIPLIN-06'nın seçim-lookahead riskini
kapatıyor), ama pratik sonuç aşırı seyrek. 3 seçenek (kullanıcı kararı bekliyor):

1. **Mevcut varsayılanı (fdr_q=0.05 + oos_split=0.5) koru** — en istatistiksel olarak
   sıkı/güvenilir, ama şu anki BIST evreninde fiilen "1 çiftlik bir sistem" demek.
   `LOOKBACK_BARS` (şu an 600, OOS yarıları ~300 bar) artırılırsa (daha uzun geçmiş
   önbelleğe alınırsa) OOS'un istatistiksel gücü artabilir, daha fazla çift hayatta
   kalabilir — ÖLÇÜLMEDİ, ayrı bir deney gerektirir.
2. **Varsayılanı `oos_split=None`'a çek** (yalnızca FDR, OOS'u opsiyonel/elle çalıştırılan
   bir doğrulama adımına indir) — B satırına döner (**17 çift**), tanının "20-40"
   hedefine ÇOK daha yakın, DISIPLIN-06 riski `oos_split=0.5` AÇIKÇA verilerek elle
   hâlâ kullanılabilir (mekanizma silinmiyor, yalnızca varsayılan değişiyor).
3. **`oos_split`'i daha gevşek tut** (ör. 0.7 — in-sample'a daha büyük pay, out-of-sample
   penceresi hâlâ var ama daha kısa/az kısıtlayıcı) — A ile C arası bir denge, ÖLÇÜLMEDİ.

**Bu doğrulama turunda `config/pairs.yaml` GERÇEKTEN 1 çiftle (varsayılan ayarlarla)
yeniden üretildi** (eski 606'lık liste `config/pairs_v1_deprecated.yaml`'a taşındı) —
kullanıcı kararına göre 2. ya da 3. seçenekle yeniden üretilebilir.

## Sektör Dağılımı

Tek hayatta kalan çift (PEKGY/EYGYO) — %100 Gayrimenkul. Örneklem büyüklüğü (N=1)
nedeniyle anlamlı bir dağılım YOK; seçenek 2/3 uygulanırsa (17 çift) bu bölüm yeniden
üretilecek.

## Kâr/Zarar Karşılaştırması — YAPILMADI (kapsam dışı bırakıldı)

Görev metni "mean_reversion modunda hayatta kalan çiftlerle backtest metrikleri vs eski
rotasyonel mod" istiyordu — **N=1 çiftle** (PEKGY/EYGYO) istatistiksel olarak anlamlı bir
karşılaştırma YAPILAMAZ (tek bir örneklem). Kullanıcı yukarıdaki karardan sonra (17 ya da
daha fazla çiftle) bu adım AYRI bir turda tamamlanmalı.

## "Arbitraj" vs "İstatistiksel Arbitraj" — Arayüz Metni

`tlab/viz/labels_tr.py::INDICATOR_CATEGORY_TR["pair"]` "Pair (Rölatif Momentum)"'dan
"İstatistiksel Arbitraj"a çevrildi (Faz 2, 2E — TAMAMLANDI). Gerçek (risksiz) arbitrajın
(nakit-vadeli, put-call paritesi, dönüştürülebilir tahvil) tlab'ın tek-sembol spot-veri
mimarisiyle uyuşmadığı ve kapsam dışı olduğu notu CLAUDE.md'de zaten mevcuttu (K2
STRAT-09/ch3, "PARK").

## Sonraki Adım

**Faz 2 TAMAMEN BİTTİ.** 2A/2B/2C/2E kod değişiklikleri + 2D doğrulaması + karar
(`oos_split=None`, 17 çift) TAMAMLANDI, `config/pairs.yaml` güncel. Kâr/zarar
karşılaştırması (mean_reversion vs rotasyonel, tüm 17 çiftle) ve OOS'un daha uzun bir
`LOOKBACK_BARS` ile yeniden denenmesi (Seçenek 1/3'ün gelecekte tekrar değerlendirilmesi
için) AYRI, isteğe bağlı bir takip işi olarak backlog'da bırakıldı — Faz 2'nin BİTTİ
kriterini bloke ETMİYOR. Sırada: **Adım 5 — Faz 3 (SVG çizim motoru)**.
