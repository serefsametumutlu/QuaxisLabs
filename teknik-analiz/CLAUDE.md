# CLAUDE.md

Bu dosya taslaktır, proje ilerledikçe değişecektir. Şu an sadece iskelet + temel ilkeler var.

## Proje Nedir

Python tabanlı teknik indikatör araştırma laboratuvarı. Bilanço Radar (temel analiz) projesinden bağımsız ama ileride onunla aynı app'te birleşecek — teknik + temel analiz tek arayüzde.

Her indikatör:
- Python'da yazılır (Pine Script değil — TradingView'a taşınacaksa ileride ayrıca portlanır)
- Aynı standart arayüze uyar, böylece toplu tarama motoru hepsini aynı şekilde çağırabilir
- **4 saatlik ve Günlük** zaman dilimlerinde eş zamanlı taranır (tek bir tarama koşusunda tüm evren × tüm indikatörler × iki TF)
- Tekil hisse modu: bir sembol seçilip tek bir indikatör için detaylı görselleştirme alınabilir — o indikatörün ürettiği her seviye/çizim/etiket grafik üzerinde görünür olmalı (sadece sinyal metni değil, tam görsel kanıt)

## KRİTİK TASARIM İLKESİ: Repaint/Lookback Yasağı

Hiçbir indikatör pivot-onaylı, gecikmeli veya geriye-dönük bakan (lookahead) sinyal üretmeyecek. Sinyal, o barda anlık olarak üretilmeli ve sonradan değişmemeli (non-repainting). Bu, Bilanço Radar projesindeki teknik çalışmalarda (Harmonic, Wavelet Trend Rider, Rally Precursor vb.) tekrar tekrar vurgulanmış, ihlal edilemez bir kural — buraya da aynen taşınıyor.

## İlk Modül Hedefi: Çoklu-Ekol Harmonik Formasyon Tarayıcı

Klasik XABCD dışında farklı ekollerin kurallarını ayrı ayrı (veya seçilebilir modlar halinde) uygulayan bir harmonik tarayıcı planlanıyor. Referans ekoller:

- **Scott Carney** — PRZ (Potential Reversal Zone), Gartley/Bat/Crab/Shark, katı oran kuralları
- **Larry Pesavento** — klasik simetri, AB=CD
- **Bryce Gilmore** — zaman harmonikleri (Time Bars): XA/CD bacak bar sayıları arasında Fibonacci oranı arayışı, "ne zaman" boyutu
- **Darren Oglesbee — Cypher** — C noktası A'yı aşabilir (XA'nın 1.272–1.414 uzantısı), D noktası XC'nin %78.6 seviyesinde
- **Nenad Kerkez — Nen Star** — harmonik + pivot noktaları/MA/MACD hibriti, PRZ'nin haftalık/aylık pivot ile kesişimi
- **Ross Beck — Navarro 200** — Gartley'in D noktasında %200 Fibonacci uzantısı şartı
- **5-0 Formasyonu** — 6 noktalı (X-0-1-2-3-4), trend dönüşü teyidi, D noktası son bacağın %50 seviyesinde

Her ekol ayrı bir dedektör fonksiyonu/sınıfı olarak düşünülebilir; ortak nokta bulma altyapısı (swing/pivot tespiti) paylaşılabilir ama oran kuralları ekole göre izole tutulmalı.

Diğer indikatörler (yeni harmonik-dışı fikirler, "düşeni kıranlar" vb.) zamanla eklenecek — bu doküman o oranda genişleyecek.

## Gelecek Entegrasyonlar (henüz tasarlanmadı, sadece hedef notu)

- **TradingView masaüstü bağlantısı**: Kullanıcı bunu ayrıca kendi planlayacak (tv_health_check benzeri bir yaklaşım). Bu dosyada detay yok, tasarım kararları kullanıcıdan gelecek.
- **Fintables bağlantısı**: Ham temel veri + hazır analiz çekimi için ileride entegre edilecek. Detay/tasarım henüz yok.
- **Bilanço Radar ile birleşme**: Bu projenin çıktıları (sinyaller, taramalar) ile Bilanço Radar'daki `dashboard.html` temel analiz katmanı tek bir app'te buluşacak. Doğruluğu teyit edilmiş veriler iki proje arasında paylaşılabilir.

## Arayüz Kararı

Henüz verilmedi (Streamlit/masaüstü mü, web/HTML mi). Bilanço Radar ile ileride birleşeceği için bu karar ertelendi — indikatör/tarama motoru arayüzden bağımsız tasarlanmalı ki hangi arayüz seçilirse seçilsin çekirdek mantık değişmesin.

## Komutlar / Yapı

Henüz kod yok — ilk modül (harmonik tarayıcı) yazılınca burası güncellenecek.
