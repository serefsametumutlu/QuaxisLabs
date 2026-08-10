# QuaxisLabs Upgrade Kit — Kurulum Rehberi

Bu kit, projene Claude Code agent'ları, skill'leri ve faz faz yol haritası ekler. Kurulum 10 dakika.

## 1. Kiti projeye kopyala

Zip'i aç ve içeriği proje kök dizinine (main.py'nin olduğu klasöre) kopyala. Sonuç şöyle olmalı:

```
QuaxisLabs/
├── main.py, src/, tests/, ...        (mevcut proje — dokunulmadı)
├── .claude/
│   ├── agents/                        (5 agent)
│   │   ├── kitap-okuyucu.md
│   │   ├── temel-analiz-uzmani.md
│   │   ├── quant-uzmani.md
│   │   ├── kart-tasarimcisi.md
│   │   └── kod-gelistirici.md
│   └── skills/                        (5 skill)
│       ├── quaxis-mimari/SKILL.md
│       ├── kitap-bilgi-cikarma/SKILL.md
│       ├── temel-analiz-cercevesi/SKILL.md
│       ├── sektor-siniflandirma/SKILL.md
│       └── kart-tasarim-sistemi/SKILL.md
├── kitaplar/                          (PDF'leri buraya atacaksın)
├── bilgi-bankasi/                     (agent çıktıları buraya gelecek)
├── OKUBENI_ONCE.md
└── YOL_HARITASI.md
```

Projende zaten bir `.claude/` klasörü varsa içerikleri birleştir (üzerine yazma, ekle).

## 2. Kitap PDF'lerini yükle

6 PDF'i `kitaplar/` klasörüne, `kitaplar/README.md`'deki dosya adlarıyla (01_graham... 06_schilit...) koy. Türkçe karakter ve boşluk kullanma. Telif nedeniyle repoya gitmesinler:

```bash
echo "kitaplar/*.pdf" >> .gitignore
echo "bilgi-bankasi/_tmp/" >> .gitignore
```

## 3. Claude Code'u başlat ve doğrula

```bash
cd QuaxisLabs
claude
```

İçeride `/agents` yazarak 5 agent'ın listelendiğini gör. Skill'ler `.claude/skills/` altından otomatik keşfedilir. Sonra YOL_HARITASI.md'deki **Faz 0 promptunu** yapıştır — Claude mimari skill'i güncel kodla doğrular ve test durumunu raporlar.

## 4. Sistem nasıl çalışıyor (özet)

- **Skill'ler = kalıcı bilgi.** Sonnet her oturumda projeyi sıfırdan keşfetmek yerine mimari kuralları, tasarım standartlarını ve prosedürleri skill'lerden okur.
- **Agent'lar = uzman roller.** Her biri kendi disiplinine kilitli: kitap-okuyucu bilgi çıkarır, temel-analiz-uzmani spec yazar (kod yazmaz), quant-uzmani matematiği denetler ve kalibre eder, kart-tasarimcisi görsel kimliği kurar, kod-gelistirici spec'i mimari anayasaya uyarak koda çevirir. Bu ayrım bilinçli: "sayıyı uzman belirler, kodu geliştirici yazar" zinciri, eşiklerin havadan uydurulmasını engeller.
- **İzlenebilirlik zinciri:** kitap → bilgi-bankasi (İLKE/FORMÜL/BAYRAK kodları) → docs/spec → kod docstring → test. Her skorun kaynağı kitaba kadar sürülebilir.
- **Sen = onay makamı.** Yol haritasındaki onay kapılarında (spec özetleri, tasarım iterasyonları) karar senindir.

## 5. Sıra

FAZ 0 (kurulum doğrulama) → FAZ 1 (6 kitabın çıkarımı — kitap başına 1 oturum) → FAZ 2 (sektör evreni) → FAZ 3 (v2 motoru: spec → quant denetimi → kod) → FAZ 4 (kart tasarımı — istersen 2-3 ile paralel) → FAZ 5 (piyasa dashboard'u) → FAZ 6 (Telegram entegrasyonu + kalibrasyon). Her fazın hazır promptu ve "bitti sayılma kriteri" YOL_HARITASI.md'de.

## Pratik notlar

- Kitap okuma oturumları uzundur; her kitaba ayrı oturum aç. Kesilirse `bilgi-bankasi/_ilerleme.md` sayesinde kaldığı yerden devam eder.
- NASDAQ tam evren taraması saatler sürebilir (rate-limit); Faz 5 batch job'ı checkpoint'lidir, gece çalıştırıp sabah devam ettirebilirsin.
- Üretilen kartlar ve dashboard yatırım tavsiyesi değildir — projenin mevcut uyarı ilkesi tüm yeni çıktılarda da korunur.
