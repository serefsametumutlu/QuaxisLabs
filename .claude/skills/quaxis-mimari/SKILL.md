---
name: quaxis-mimari
description: QuaxisLabs (Bilanço Radar) projesinin mimari haritası, katman kuralları, veri kaynakları ve ihlal edilemez ilkeleri. Bu projede HERHANGİ bir kod okuma/yazma/planlama işine başlamadan önce kullan.
---

# QuaxisLabs Mimari Haritası

BİST + NASDAQ hisseleri için kural tabanlı temel analiz Telegram botu. Python, SQLAlchemy(SQLite), Jinja2+Playwright (PNG kart), python-telegram-bot, Gemini (sadece sözel yorum).

## İhlal edilemez anayasa
1. **LLM asla sayı üretmez.** Tüm yüzde/oran/puan deterministik Python (`Decimal`). Gemini'ye sadece hazır formatlanmış bulgu listesi gider; LLM çökse de sistem kural tabanlı yedek metinle kart üretir.
2. **Katman disiplini:** `src/analysis/*` saf matematik — I/O yapmaz, `src.fetchers`/`src.db` import etmez. `src/fetchers/*` sadece veri çeker. `src/bot/pipeline.py` orkestre eder. `src/render/*` sadece sunar; Jinja2 şablonları hesaplama/formatlama YAPMAZ (her değer hazır Türkçe string gelir).
3. **Eksik veri:** `None` yayılır, kartta "N/A"; kısmi TTM hesaplanmaz (4 çeyrek tam değilse `None`). Skor bileşeni verisi yoksa atlanır, ağırlığı kalanlara orantısal dağıtılır.
4. Her skor bileşeni `reasoning_tr` gerekçesi üretir; her eşik/ağırlık `SCORING_METHODOLOGY.md`'de kaynaklı gerekçeyle belgelenir.

## Katman haritası
- `src/fetchers/` — isyatirim.py (BİST mali tablolar; XI_29/UFRS/UFRS_K grup tespiti, itemCode eşlemeleri modül üst yorumunda), kap*.py (bildirimler, IPO, fon, finansallar), sec_edgar.py (ABD, herhangi bir ticker), yahoo_quote.py / tradingview_quote.py / stockanalysis.py (fiyat/çarpan), price_history.py, tefas.py (fonlar), pdf_ocr.py, earnings_calendar.py, company_logo.py
- `src/analysis/` — calculator.py (YoY/QoQ, marjlar, TTM, oranlar, değerleme; 1319 satır), scorer.py (7 bileşenli 0-10 Radar Skoru, CONFIG sözlüğü; `sanayi`/`abd_sanayi` şablonları kalibre, banka/sigorta iskelet), fundamental_screens.py (Greenblatt + Carlisle + Piotroski; SADECE XI_29 sanayi), valuation.py, technical.py (skorsuz/sinyalsiz), trends.py, ipo_assessment.py, fund_estimator.py
- `src/render/` — card.py + templates/*.html (bilanço kartı, derin kart, teknik, takvim, IPO, fon, teaser, fundamental_screens); Playwright ile ~2000px PNG
- `src/bot/` — telegram_bot.py (menü + serbest ticker, BİST/NASDAQ otomatik yönlendirme), pipeline.py (ana orkestrasyon, 1716 satır), ipo_pipeline.py, fund_pipeline.py
- `src/db/` — models.py (Company/FinancialPeriod/Disclosure/GeneratedCard), repository.py (upsert/dedup/tazelik)
- `scripts/` — explore_* (canlı API keşfi), demo_* (uçtan uca kart üretimi), kalibrasyon scriptleri
- `tests/` — 569 test; fixture tabanlı, gerçek Playwright render testleri dahil. Komut: `pytest tests/ -x -q`

## Bilinen sınırlar (geliştirme hedefleri)
- Sektör bilinci YOK: eşikler tüm sanayi için tek tip; sektörel gruplama/karşılaştırma yapılmıyor (SEC'den SIC kodu erişilebilir ama kullanılmıyor; BİST sektör bilgisi KAP/İş Yatırım'dan çekilebilir).
- Piyasa-geneli görünüm YOK: sistem hisse-bazlı; tüm-BİST/tüm-NASDAQ toplu tarama-dashboard yok.
- Banka/sigorta skor şablonları iskelet (NIM, SYR, prim büyümesi fetcher'da çekilmiyor).
- Kitap çerçevelerinden sadece Greenblatt/Carlisle/Piotroski kodlandı; Graham güvenlik marjı, Buffett kalite göstergeleri, Fisher 15 madde, Lynch kategorileri/PEG, Schilit kırmızı bayrakları, Damodaran anlatı+değerleme EKSİK.
- Kart tasarımında token sistemi yok (renk/boyut şablon içine gömülü).
- Peer karşılaştırma geçmişte "sahte kesinlik" nedeniyle kaldırıldı — sektör-göreli her yeni özellik örneklem büyüklüğünü görünür kılmalı (bkz. fundamental_screens.py üst notu).

## Çalıştırma
`python main.py` (bot) · `python scripts/demo_card.py THYAO` (kart) · `python scripts/demo_pipeline_us.py AAPL` (ABD) · `.env`: GEMINI_API_KEY, TELEGRAM_BOT_TOKEN
