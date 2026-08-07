# Değerleme Ekranı — Metodoloji

Faz 21. Sadece BİST XI_29 (sanayi/ticaret) şirketleri için çalışır; banka/sigorta/katılım bankası/NASDAQ desteklenmez (Greenblatt'ın kendi metodolojisi bu şirket tiplerini bilinçli dışlar — farklı sermaye yapıları FD/EBIT çarpanını anlamsız kılar). Hiçbiri sektör/peer karşılaştırması kullanmaz; hepsi şirketin kendi verisinden hesaplanır.

Sadece **Graham** somut bir TL hedef fiyat üretir. Diğer üçü (Greenblatt, Carlisle, Piotroski) fiyat hedefi vermez — bunlar "ucuz mu / kaliteli mi" diyen çarpan ve puanlama araçlarıdır, orijinal tasarımlarında da adil fiyat iddiası yoktur.

---

## 1. Benjamin Graham Ölçütü

**Kaynak:** *The Intelligent Investor* (1949)

**Formül:**
```
Graham Çarpanı = F/K × PD/DD
Graham Sayısı (Adil Değer) = Mevcut Fiyat × √(22,5 / Graham Çarpanı)
```

**Ölçüt:**
| Graham Çarpanı | Yorum |
|---|---|
| ≤ 22,5 | Ucuz |
| > 22,5 | Pahalı |

Tek yöntem burada **TL cinsinden bir adil değer/hedef fiyat** verir; mevcut fiyatla karşılaştırılıp %yukarı/aşağı potansiyel gösterilir.

---

## 2. Joel Greenblatt — Sihirli Formül

**Kaynak:** *The Little Book That Beats the Market* (2005)

**Formül (iki ayrı yüzde, fiyat hedefi YOK):**
```
Kazanç Getirisi (Earnings Yield) = EBIT / Kurumsal Değer (FD)
Sermaye Getirisi (Return on Capital) = EBIT / (Net Çalışma Sermayesi + Maddi Duran Varlıklar)
```

**Ölçüt:**
| Kazanç Getirisi | Yorum | Sermaye Getirisi | Yorum |
|---|---|---|---|
| ≥ %12 | Yüksek (ucuz) | ≥ %25 | Yüksek (kaliteli) |
| %6 – %12 | Orta | %10 – %25 | Orta |
| ≤ %6 | Düşük (pahalı) | ≤ %10 | Düşük (zayıf iş) |

İkisi birden "Yüksek" ise ideal: hem ucuz hem kaliteli. Sadece kazanç getirisi yüksekse "ucuz ama vasat iş" olabilir.

---

## 3. Tobias Carlisle — Acquirer's Multiple

**Kaynak:** *Deep Value* / *The Acquirer's Multiple* (2014/2017) — Greenblatt'ın kazanç getirisinin tek çarpanlı sadeleştirilmiş hali.

**Formül:**
```
Acquirer's Multiple = Kurumsal Değer (FD) / EBIT
```

**Ölçüt (düşük = ucuz):**
| Çarpan | Yorum |
|---|---|
| ≤ 8 | Ucuz |
| 8 – 15 | Makul |
| ≥ 15 | Pahalı |

---

## 4. Joseph Piotroski — F-Skoru

**Kaynak:** *Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers* (2000)

Fiyat/ucuzluk DEĞİL, **finansal sağlık/kalite** ölçer — Graham/Greenblatt/Carlisle'ın "ucuz ama çürük şirket" tuzağına düşmesini önlemek için tamamlayıcı bir kontrol listesidir. 9 maddelik ikili (evet/hayır) checklist:

1. ROA (Aktif Kârlılığı) pozitif
2. Faaliyet Nakit Akışı pozitif
3. ROA geçen yıla göre arttı
4. Nakit Akışı, Net Kâr'dan yüksek (kazanç kalitesi/tahakkuk kontrolü)
5. Uzun vadeli kaldıraç (borç/aktif) azaldı
6. Cari oran arttı (likidite iyileşti)
7. Pay sulanması yok (yeni hisse ihracı yok)
8. Brüt kâr marjı arttı
9. Aktif devir hızı arttı (verimlilik)

**Ölçüt (kaç kriter sağlandı / kaç kriter değerlendirilebildi):**
| Oran | Yorum |
|---|---|
| ≥ %85 (≈ 8-9 / 9) | Güçlü |
| %30 – %85 (≈ 3-7 / 9) | Orta |
| ≤ %30 (≈ 0-2 / 9) | Zayıf |

Not: bazı kriterler için yeterli geçmiş dönem verisi yoksa (örn. 2 yıl öncesine ait dönem hiç yayınlanmamışsa) o kriter puanlamadan tamamen çıkarılır — "6/9" yerine "5/7" gibi dürüst bir kısmi skor gösterilir. Değerlendirilen kriter sayısı 5'in altındaysa "Güçlü/Orta/Zayıf" yorumu hiç yapılmaz (çok az veriyle yargı verilmez).

---

## Pratik Okuma

- Graham + Carlisle **ucuz** diyor **ve** Piotroski **7+/9** ise → güçlü sinyal (ucuz + sağlıklı).
- Ucuz görünüp Piotroski düşükse (3 ve altı) → dikkat, "değer tuzağı" olabilir.
- Yöntemler birbiriyle çelişebilir — bu da başlı başına anlamlı bir bilgidir, tek bir "doğru" sinyale sıkıştırılmaz.

*(Hiçbiri "al/sat" tavsiyesi değildir; klasik değer yatırımcılığı literatüründeki bağımsız merceklerdir.)*
