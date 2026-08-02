# Radar Skoru Metodolojisi

Bu doküman `src/analysis/scorer.py` içindeki `CONFIG` sözlüğünün **neden** bu
ağırlıklarla ve eşiklerle kurulduğunu açıklar. Kod zaten her bileşen için
`reasoning_tr` ile gerekçe üretiyor ve artık kart üzerinde de (RADAR SKORU
panelinde, her satırın altında) gösteriliyor; bu dosya ise ağırlıkların
**kaynağını** (hangi kabul görmüş analiz çerçevesinden geldiğini) belgeliyor.

## Genel yaklaşım

Skor, 0-10 arası **kural tabanlı, ağırlıklı bir bileşik puandır** (LLM
üretmez — bkz. `scorer.py` modül docstring'i). Şirket türüne göre 3 ayrı
şablon vardır; sadece **sanayi/holding** şablonu gerçek veriyle tam
kalibre edilmiştir (banka/sigorta şablonları iskelet, ileride gerçek
sektörel verilerle kalibre edilecek).

Bir bileşenin verisi yoksa (örn. fiyat çekilemedi) o bileşen **atlanır** ve
ağırlığı kalan bileşenlere **orantısal olarak** yeniden dağıtılır — toplam
efektif ağırlık her zaman %100'e tamamlanır, hiçbir zaman sıfıra bölünmez.
Kart bunu göstermek için her satırın yanında **nominal ağırlığı**
(`CONFIG`'deki sabit tasarım ağırlığı — hangi bileşenin ne kadar önemli
sayıldığı) gösterir; o dönem hangi bileşenlerin fiilen hesaba katıldığı ise
`reasoning_tr` metninde ("bileşen atlandı" ifadesiyle) açıkça yazılıdır.

## Sanayi / Holding şablonu (7 bileşen, toplam %100)

| Bileşen | Ağırlık | Girdi | Neden bu ağırlık? |
|---|---|---|---|
| **Nakit Üretimi (FAVÖK marjı)** | %21 | FAVÖK marjı seviyesi + YoY yönü | Faaliyet nakit üretme kapasitesi, borç servisi ve yeniden yatırım gücünün en güçlü tek göstergesidir; kâr kalitesi (muhasebe kârından çok nakit üretimi) fundamental tarama çerçevelerinde (Piotroski F-Score'un kâr kalitesi bacağı) genelde en ağır basan kalemdir. Trend'e duyarlıdır: marj yüksek olsa bile YoY bozuluyorsa skor 0-4 aralığına düşürülür — "bugün iyi, yarın kötüleşiyor" durumunu cezalandırır. |
| **Kaldıraç (Net Borç/FAVÖK, TTM)** | %17 | `net_debt / ttm_ebitda` | Kredi derecelendirme kuruluşlarının (Moody's, S&P) temel kaldıraç metriğidir: <2.5x yatırım yapılabilir/sağlıklı, >4x spekülatif kabul edilir. Eşikler bu sektör pratiğine göre kalibre edildi (çok iyi <1x, iyi <2.5x, orta <4x, tavan 8x'te skor 0'a sabitlenir). Net nakit pozisyonunda (negatif oran) otomatik 10 puan. |
| **Özkaynak Kârlılığı (ROE, TTM)** | %15 | `ttm_net_income / equity_current` | Graham'ın güvenlik marjı hariç neredeyse tüm efsanevi yatırımcı çerçevelerinin (Buffett/Munger'ın "ekonomik hendek" testi, Lynch'in GARP yaklaşımı, O'Neil'in CAN SLIM "C/A" büyüme+karlılık kombosu, Piotroski F-Score'un ROA bacağının özkaynak karşılığı) ORTAK vurgusu — yönetimin elindeki sermayeyi ne kadar verimli büyüttüğünü ölçer. Veri zaten `calculator.Ratios.roe_annualized` içinde hesaplıydı (banka/sigorta şablonlarında kullanılıyordu) ama sanayi şablonunda eksikti; hiçbir yeni veri çekimi gerektirmeden eklendi. Eşik banka şablonundakinden (güçlü ≥%20) düşük tutuldu (güçlü ≥%15, orta ≥%10, tavan %25) — sanayi/holding şirketlerinde özkaynak kârlılığı bankalara göre yapısal olarak daha düşük seyreder. |
| **Değerleme (F/K + PD/DD)** | %17 | Piyasa değeri, TTM net kâr, güncel özkaynak (dışarıdan fiyat + sermaye ile hesaplanır) | Klasik Graham tarzı "ucuzluk" taraması: düşük F/K + düşük PD/DD ⇒ ucuz. Eşikler BIST sanayi ortalamalarına göre kalibre edildi (F/K: ucuz <8, makul <15, pahalı <25, tavan 40; PD/DD: ucuz <1, makul <2.5, pahalı <5, tavan 8). Negatif F/K veya PD/DD (zarar/negatif özkaynak) "değerlendirme dışı" sayılır, yanlış pozitif üretmez. |
| **Kârlılık (Net Marj)** | %13 | Net marj seviyesi + YoY yönü | Nihai kârlılık; FAVÖK marjının "faiz/vergi/amortisman sonrası" tamamlayıcısı. Aynı seviye+trend mantığıyla puanlanır. |
| **Büyüme (Hasılat YoY)** | %13 | Hasılat YoY değişimi, istenirse enflasyondan arındırılmış | Yüksek enflasyon ortamında (Türkiye) nominal büyüme yanıltıcı olabileceği için enflasyon verilmişse **reel** büyüme kullanılır — bu, sadece TL değer kaybından kaynaklanan "sahte büyüme" görüntüsünü engeller. Taban -%20'de (güçlü daralma) skor 0'a sabitlenir. |
| **Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık)** | %4 | Cari oran, özkaynak/toplam varlık oranı | İkincil bir doğrulama sinyali (birincil risk zaten Kaldıraç bileşeninde ölçülüyor); bu yüzden en düşük ağırlık. Cari oran ≥1.5 iyi, ≥1 orta; özkaynak/varlık ≥%40 iyi, ≥%25 orta. |

**Toplam skora göre rozet eşikleri:** ≥8 SAĞLAM, ≥6 DENGELİ, ≥4 KARIŞIK, <4 RİSKLİ
(sol-kapalı aralıklar — sınır değer üstteki rozete dahildir).

## NASDAQ/ABD Sanayi şablonu (`abd_sanayi`, Faz 10)

`score_industrial_us()` **aynı 7 bileşeni, aynı ağırlıklarla** (toplam yine
%100) kullanır — `score_industrial(..., template="abd_sanayi")`'nin ince bir
sarmalayıcısıdır, kod KOPYALANMADI (bkz. `scorer.py` modül içi not). Tek fark
`CONFIG["abd_sanayi"]` altındaki **eşik değerleridir**; her biri ayrı ayrı
gerekçelendirildi:

| Bileşen | `sanayi` (BIST) eşikleri | `abd_sanayi` eşikleri | Değişti mi? Neden? |
|---|---|---|---|
| Nakit Üretimi (FAVÖK marjı) | güçlü ≥20, orta ≥10, tavan 30 | **AYNI** | FAVÖK marjı kalitesi operasyonel bir gösterge, para biriminden/piyasadan bağımsızdır. |
| Kaldıraç (Net Borç/FAVÖK) | çok iyi <1, iyi <2.5, orta <4, tavan 8 | **AYNI** | Moody's/S&P'nin kaldıraç bantları (yatırım yapılabilir <2.5x, spekülatif >4x) **ülke/para birimi ayrımı yapmadan** uygulanan evrensel kredi analizi pratiğidir. |
| Kârlılık (Net Marj) | güçlü ≥15, orta ≥5, tavan 25 | **AYNI** | Net marj kalitesi de piyasadan bağımsız bir operasyonel göstergedir. |
| Özkaynak Kârlılığı (ROE) | güçlü ≥15, orta ≥10, tavan 25 | **AYNI** | Graham/Buffett/Munger/Lynch/O'Neil ölçütleri evrensel kabul edilir. **Bilinen sınır:** sermaye-hafif/agresif hisse geri alımı yapan ABD teknoloji şirketlerinde (örn. AAPL, canlı doğrulandı: ROE %119,9) özkaynak tabanı yapay şekilde küçülmüş olabilir — bu "aşırı kârlılık" değil "düşük özkaynak tabanı" anlamına gelir, tek başına yorumlanmamalı. |
| Büyüme (Hasılat YoY) | güçlü ≥15, orta ≥0, tavan 30, taban −20 | güçlü ≥**10**, orta ≥0, tavan **25**, taban **−15** | `sanayi` şablonunda **nominal TRY** büyümesi kullanılır ve Türkiye'nin yüksek (bazı yıllarda %40-60+) enflasyonunu zımnen içerir — "güçlü" %15 nominal büyüme reel terimde çok düşük/negatif olabilir. `analyze_us()` nominal **USD** büyümesi kullanır (ABD TÜFE tipik %2-4, TL'ye kıyasla önemsiz) — nominal USD büyüme zaten pratikte reel büyümeye yakındır, bu yüzden esikler enflasyon kaynaklı yapay şişirme OLMADAN gerçek performansı yansıtsın diye BIST'tekinden düşük tutuldu. |
| Değerleme (F/K + PD/DD) | ucuz F/K <8, makul <15, pahalı <25, tavan 40; ucuz PD/DD <1, makul <2.5, pahalı <5, tavan 8 | ucuz F/K <**12**, makul <**20**, pahalı <**30**, tavan **50**; ucuz PD/DD <**1,5**, makul <**3**, pahalı <**6**, tavan **12** | **CANLI araştırıldı** (2026-08, kaynaklar aşağıda). S&P 500 trailing F/K ~25 (tarihsel ortalama ~19,7-25,4; 1871'den beri medyan ~18,0), PD/DD ~5,9-6,0 (tarihsel medyan ~2,9). BIST'in "ucuz F/K <8" eşiği ABD piyasasında neredeyse hiçbir sağlıklı büyük şirkette görülmez — yapısal olarak daha düşük sermaye maliyeti + daha yüksek büyüme beklentisi çarpanları sistematik olarak yukarı çeker. Eşikler ABD piyasa medyan/ortalamalarına göre yukarı kaydırıldı. |
| Bilanço Kalitesi (Cari Oran + Özkaynak/Varlık) | cari oran iyi ≥1.5, orta ≥1; özkaynak/varlık iyi ≥%40, orta ≥%25 | **AYNI** | Muhasebe rasyoları, para biriminden/piyasadan bağımsızdır. |

**Değerleme eşikleri kaynakları** (2026-08-02 canlı arama):
- [S&P 500 PE Ratio — GuruFocus](https://www.gurufocus.com/economic_indicators/57/sp-500-pe-ratio) (trailing ~25,18, Temmuz 2026; tarihsel ortalama ~25,38)
- [S&P 500 P/E Ratio — Real CPI](https://www.realcpi.org/s-p-500-pe-ratio/) (1871'den beri medyan ~18,03)
- [S&P 500 Price to Book Value — GuruFocus](https://www.gurufocus.com/economic_indicators/4240/sp-500-price-to-book-value) (~5,44, Ocak 2026)
- [US - S&P 500 - PB Ratio — MacroMicro](https://en.macromicro.me/series/6938/us-sp500-pb-ratio) (~5,94-6,01)
- [S&P 500 Price to Book Value — Multpl](https://www.multpl.com/s-p-500-price-to-book) (tarihsel medyan ~2,89)

### Neden ikili (1/0) değil, sürekli (0-10) puanlama?

Piotroski F-Score gibi klasik akademik modeller her kriteri katı bir
1 (geçti) / 0 (kaldı) eşiğiyle puanlar — bu, on binlerce hisseyi hızlı
taramak için pratik olsa da sınırda kalan şirketleri (örn. ROE %14.9,
eşik %15) acımasızca eler. Bu projedeki `_seviye_trend_skoru` /
`_asymptote_to` fonksiyonları bunun yerine **sürekli enterpolasyon**
kullanır: eşiğin hemen altı/üstü yumuşak geçer, eşiğin çok ötesindeki
değerler (örn. FAVÖK marjı %70) de sabit tavanda kalmak yerine 10'a
**asimptotik olarak yaklaşır** (asla eşitlenmez) — böylece "eşiği
zar zor geçen" ile "eşiği ezip geçen" şirket aynı puanı almaz.

## Piyasa değeri / çarpan hesapları (kart üstündeki DEĞERLEME kutuları)

BIST'te nominal pay değeri 1 TL olduğu için **ödenmiş sermaye (TL) = toplam
pay adedi** varsayımı kullanılır (piyasa katılımcılarının da kullandığı
standart kısayol):

- **Piyasa Değeri** = Fiyat × Sermaye
- **Net Borç** = Finansal Borçlar − Nakit ve Benzerleri (güncel dönem)
- **Firma Değeri (FD)** = Piyasa Değeri + Net Borç
- **F/K** = Piyasa Değeri / TTM Net Kâr (ana ortaklık payı, son 4 çeyrek toplamı)
- **PD/DD** = Piyasa Değeri / Güncel Özkaynak
- **FD/FAVÖK** = FD / TTM FAVÖK
- **FD/Hasılat** = FD / TTM Hasılat
- **PD/EFK** = Piyasa Değeri / TTM Esas Faaliyet Kârı

TTM (son 12 ay) toplamları, ilgili 4 çeyreğin **tamamı** mevcut değilse
hesaplanmaz (kısmi TTM yanıltıcı olacağı için `None` döner, kartta Fintables
konvansiyonuyla tutarlı şekilde "N/A" gösterilir) — bkz.
`calculator._trailing_4q_sum()` ve `card._money_or_na`/`_ratio_or_na`.

## Bilinen sınırlar / sonraki adımlar

- Banka/sigorta şablonları (`score_bank`, `score_insurance`) iskelet
  durumda; net faiz marjı, sermaye yeterlilik oranı, prim büyümesi gibi
  sektöre özgü kalemler fetcher katmanında henüz çekilmiyor.
- Eşikler (F/K, PD/DD, kaldıraç vb.) BIST sanayi/holding ortalamalarına göre
  **manuel** kalibre edildi; gerçek portföy/backtest verisiyle periyodik
  olarak gözden geçirilmesi önerilir.
