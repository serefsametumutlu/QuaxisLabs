"""Faz 13: "Yaklaşan Bilanço Tarihleri" takvim kartı context builder'ı.

src/render/card.py'deki build_*_card_context() fonksiyonlarıyla AYNI ilkeye
uyar: burada HİÇBİR sayı/tarih HESAPLANMAZ -- src.fetchers.earnings_calendar
zaten hesaplanmış (yaklaşım 1/2/3 birleştirilmiş) EarningsDate listesini
verir, bu modül SADECE görsel gruplama (tarihe göre) + Türkçe biçimlendirme
+ rozet/lejant eşlemesi yapar.

KAPSAM KARARI (kullanıcıyla netleştirildi, 2026-08-02): kart SADECE
CONFIDENCE_KESIN ve CONFIDENCE_TAHMINI seviyelerini gösterir.
CONFIDENCE_SON_TARIH (SPK yasal son bildirim tarihi -- şirket HENÜZ hiçbir
şey açıklamamış, sadece yasal tavan) BİLEREK DIŞLANIR: fetch_upcoming_bist
taranan HER ticker için resolve_bist_earnings_date() legal_deadline() ile
HER ZAMAN bir tarih üretebildiğinden (hiçbir zaman None dönmez, bkz.
earnings_calendar.py modül notu), son_tarih dahil edilseydi pratikte
taranan tüm evren (BIST100 yaklaşımı) tek bir kartta listelenir, kart
kalabalıklaşır ve "yasal tavan" ile "gerçek beklenti" arasındaki fark
kullanıcıya kaybolurdu. Sadece kesin/tahmini göstermek listeyi kısa ve
"gerçekten yakında açıklanacak" şirketlerle sınırlı tutar -- bu yüzden
lejant de SADECE bu iki rozeti açıklar (üçüncü, hiç görünmeyen bir rozet
için lejant maddesi eklemek kafa karıştırırdı).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime

from src.fetchers import company_logo
from src.fetchers.earnings_calendar import CONFIDENCE_KESIN, CONFIDENCE_TAHMINI, EarningsDate

_DEFAULT_CONFIDENCE_LEVELS: frozenset[str] = frozenset({CONFIDENCE_KESIN, CONFIDENCE_TAHMINI})

# CANLI hata (kullanıcı raporu, 2026-08-02): NASDAQ için fetch_upcoming_nasdaq()
# api.nasdaq.com'un döndürdüğü TÜM piyasayı (NASDAQ-100 ile SINIRLI değil, binlerce
# küçük şirket dahil) tarıyor -- 10 günlük bir pencerede 2287 kayıt döndü. Chromium
# bu kadar satırı içeren #calendar-card elementinin ekran görüntüsünü ALAMADI
# ("Page.captureScreenshot: Unable to capture screenshot" -- elementin piksel
# yüksekliği CDP'nin/GPU dokusunun kapasitesini aştı). `max_rows` bu yüzden
# ZORUNLU bir güvenlik tavanı -- kartın "hızlı taranabilir bookmark" amacına da
# uygun (200+ satırlık bir liste zaten okunabilir bir ürün DEĞİLDİR).
_DEFAULT_MAX_ROWS = 60

# CANLI hata (kullanıcı raporu, 2026-08-02, İKİNCİ bir çökme): max_rows=60 ile
# bile 57 satır/16 gün grubu içeren BİR kart Telegram'a `send_photo` ile
# gönderilirken `telegram.error.BadRequest: Photo_invalid_dimensions` ile
# REDDEDİLDİ -- kart 2400x8924 piksele ULAŞMIŞTI (Telegram'ın "fotoğraf" olarak
# kabul ettiği sınır: genişlik+yükseklik <= 10000). SADECE satır SAYISINI
# sınırlamak yeterli DEĞİL -- ayni satır sayısı GÜN GRUBU sayısına göre çok
# FARKLI yükseklik üretebilir (her satır ayrı bir günse, grup başlığı/kenarlık
# maliyeti kat kat artar). Bu yüzden GERÇEK piksel yüksekliğini ÖNCEDEN tahmin
# eden bir bütçe kullanılır -- card.py'deki _build_chart()'ın eksen pikselini
# CSS'le BİREBİR eşleştirme deseniyle AYNI ilke (bkz. o modülün üst notu).
#
# Sabitler, calendar_card.html'e (bkz. .top-band/.day-group/.company-row/
# .legend/.bottom-band kuralları) KARŞI kontrollü render'larla KALİBRE EDİLDİ
# (device_scale_factor=2 DAHİL, gerçek piksel):
#   (10 satır, 1 grup)  -> 1986px   (50 satır, 1 grup)  -> 5906px
#   (10 satır, 10 grup) -> 3444px   (50 satır, 25 grup) -> 9794px
# Bu 4 nokta TAM olarak dogrusal bir modele oturuyor:
#   yukseklik_px = 844 + 98*satir_sayisi + 162*gun_grubu_sayisi
# (844 = sabit ust bant+lejant+footer+bosluklar; 98 = satir basina; 162 = gun
# grubu basina -- baslik+kenarlik+ic dolgu). CANLI 57-satir/16-grup kartla
# CAPRAZ DOGRULANDI: formul 9022px tahmin etti, gercek 8924px olcum -- <%2 fark.
_CALENDAR_FIXED_HEIGHT_PX = 844
_CALENDAR_PER_ROW_PX = 98
_CALENDAR_PER_GROUP_PX = 162
_CARD_PHYSICAL_WIDTH_PX = 2400  # 1200 CSS px * render_card'in device_scale_factor=2 sabiti
_TELEGRAM_MAX_PHOTO_DIMENSION_SUM = 10000  # Telegram sendPhoto siniri (CANLI dogrulandi: "Photo_invalid_dimensions")
_HEIGHT_SAFETY_MARGIN_PX = 400  # logo/"BUGUN" rozeti gibi kucuk boyut varyasyonlarina + tahmin hatasina tampon
_MAX_CALENDAR_HEIGHT_PX = _TELEGRAM_MAX_PHOTO_DIMENSION_SUM - _CARD_PHYSICAL_WIDTH_PX - _HEIGHT_SAFETY_MARGIN_PX


def _predicted_height_px(rows: int, groups: int) -> int:
    return _CALENDAR_FIXED_HEIGHT_PX + _CALENDAR_PER_ROW_PX * rows + _CALENDAR_PER_GROUP_PX * groups

_AY_ADLARI_TR: dict[int, str] = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}
_GUN_ADLARI_TR: dict[int, str] = {
    0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar",
}

_BADGE_META: dict[str, dict[str, str]] = {
    CONFIDENCE_KESIN: {"label": "KESİN", "css_class": "kesin"},
    CONFIDENCE_TAHMINI: {"label": "TAHMİNİ", "css_class": "tahmini"},
}

_LEGEND_ITEMS: list[dict[str, str]] = [
    {"css_class": "kesin", "label": "KESİN", "description": "şirketin kendi KAP “Finansal Takvim” bildirimi"},
    {"css_class": "tahmini", "label": "TAHMİNİ", "description": "şirketin geçmiş çeyreklerdeki yayın davranışının medyanı"},
]

_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}


def _turkish_date_label(d: date) -> str:
    return f"{d.day:02d} {_AY_ADLARI_TR[d.month]} {d.year} · {_GUN_ADLARI_TR[d.weekday()]}"


def _quarter_label(period: tuple[int, int]) -> str:
    year, quarter = period
    return f"{quarter // 3}Ç{year % 100:02d}"


def _dominant_period_label(entries: list[EarningsDate]) -> str | None:
    """Karttaki başlıkta gösterilecek TEK bir dönem etiketi (örn. "2Ç26
    Dönemi") -- listelenen şirketlerin BÜYÜK ÇOĞUNLUĞU aynı takvim
    çeyreğini hedeflediği için (rolling 30 günlük pencerede neredeyse
    hepsi aynı "sıradaki çeyrek"i açıklar) en sık geçen `period` değeri
    alınır. Azınlıkta kalan farklı-dönemli şirketler (örn. mali yılı
    kayık bir şirket) satırlarında ayrıca gösterilmez -- bu SADECE
    başlıktaki yönlendirici bir etiket, kesin bir filtre değildir."""
    if not entries:
        return None
    counts = Counter(e.period for e in entries)
    most_common_period, _ = counts.most_common(1)[0]
    return _quarter_label(most_common_period)


def _company_logo_or_none(ticker: str, market: str) -> str | None:
    try:
        return company_logo.fetch_logo_data_uri(ticker, market=market)
    except Exception:
        return None


def build_calendar_context(
    entries: list[EarningsDate],
    market: str,
    *,
    days_ahead: int = 30,
    confidence_levels: frozenset[str] = _DEFAULT_CONFIDENCE_LEVELS,
    now: datetime | None = None,
    max_rows: int = _DEFAULT_MAX_ROWS,
) -> dict:
    """`entries`: src.fetchers.earnings_calendar.fetch_upcoming_bist()/
    fetch_upcoming_nasdaq() çıktısı (ya da repository.get_upcoming_earnings()
    satırlarından üretilmiş EarningsDate listesi) -- ÖNCEDEN hesaplanmış,
    burada hiçbir tarih/güven seviyesi mantığı TEKRAR ÜRETİLMEZ.

    `max_rows`: gösterilecek TOPLAM satır (şirket) tavanı -- bkz. `_DEFAULT_MAX_ROWS`
    yorumu (CANLI hata: NASDAQ'ta 2287 kayıt Chromium'un ekran görüntüsü alma
    kapasitesini aştı). BUNUNLA BİRLİKTE, GERÇEK piksel yüksekliği de (bkz.
    `_predicted_height_px()`, kalibre edilmiş sabitlerle) AYRI bir bütçe olarak
    izlenir -- İKİNCİ bir CANLI hata: max_rows=60 ile bile 57 satır/16 gün grubu
    içeren bir kart 2400x8924 piksele ulaştı ve Telegram `send_photo` bunu
    `Photo_invalid_dimensions` ile REDDETTİ (Telegram sınırı: genişlik+yükseklik
    <= 10000). Satır sayısı TEK BAŞINA yeterli bir tavan DEĞİLDİR çünkü AYNI satır
    sayısı gün grubu sayısına göre ÇOK FARKLI yükseklik üretebilir. Her iki bütçeden
    (satır sayısı, piksel yüksekliği) HANGİSİ önce dolarsa ORADA kesilir. Tavan
    aşılırsa gün grupları en yeni tarihten başlayarak doldurulur, tavana denk gelen
    günün İÇİNDE bile kalan kısım kesilir (bir sonraki günün TAMAMI hiç eklenmez) --
    `truncated_count` kalan (gösterilmeyen) satır sayısını, `is_truncated` bunun >0
    olup olmadığını taşır; şablon bir uyarı notu gösterir. `build_calendar_share_text()`
    de AYNI (kesilmiş) `day_groups`'u kullanır -- metin de sınırsız BÜYÜYEMEZ
    (Telegram mesaj uzunluğu sınırı).

    Dönen dict, calendar_card.html'in beklediği TAMAMEN ÖNCEDEN
    biçimlendirilmiş bir şemadır (bkz. modül üst notu -- render katmanı
    hesaplama yapmaz, sadece filtreler/gruplar/biçimlendirir)."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)

    filtered = sorted((e for e in entries if e.confidence in confidence_levels), key=lambda e: (e.expected_date, e.ticker))
    total_candidates = len(filtered)

    today = now.date()
    by_date: dict[date, list[EarningsDate]] = defaultdict(list)
    for e in filtered:
        by_date[e.expected_date].append(e)

    day_groups = []
    shown_rows = 0
    shown_groups = 0
    for day in sorted(by_date):
        day_entries_all = by_date[day]
        candidate_groups = shown_groups + 1

        # ONCE bu GUNUN TAMAMINI eklemeyi dene -- hem satir-sayisi tavanina
        # (max_rows) hem GERCEK piksel yuksekligi butcesine (_MAX_CALENDAR_HEIGHT_PX)
        # UYUYORSA oldugu gibi eklenir.
        candidate_rows = shown_rows + len(day_entries_all)
        if candidate_rows <= max_rows and _predicted_height_px(candidate_rows, candidate_groups) <= _MAX_CALENDAR_HEIGHT_PX:
            day_entries = day_entries_all
        else:
            # Bu gun TAMAMEN sigmiyor -- iki butceden HANGISI daha dar ise ona
            # gore KISMEN sigdirilir (kalan satirlar bir SONRAKI cagriya/paylasima
            # birakilir, gun grubunun KENDISI yine de gosterilir -- bos bir gun
            # grubu gostermek yerine).
            rows_budget_by_count = max_rows - shown_rows
            remaining_height = _MAX_CALENDAR_HEIGHT_PX - _CALENDAR_FIXED_HEIGHT_PX - _CALENDAR_PER_ROW_PX * shown_rows - _CALENDAR_PER_GROUP_PX * candidate_groups
            rows_budget_by_height = remaining_height // _CALENDAR_PER_ROW_PX if remaining_height > 0 else 0
            rows_that_fit = max(0, min(rows_budget_by_count, rows_budget_by_height, len(day_entries_all)))

            if rows_that_fit == 0:
                break  # bu ve (tarihe gore sirali) sonraki TUM gunler icin butce kalmadi
            day_entries = day_entries_all[:rows_that_fit]

        rows = []
        for e in day_entries:
            badge = _BADGE_META[e.confidence]
            rows.append(
                {
                    "ticker": e.ticker,
                    "company_name": e.company_name,
                    "logo_data_uri": _company_logo_or_none(e.ticker, market),
                    "badge_label": badge["label"],
                    "badge_class": badge["css_class"],
                }
            )
        day_groups.append({"date_label": _turkish_date_label(day), "is_today": day == today, "rows": rows})
        shown_rows += len(day_entries)
        shown_groups += 1

        if len(day_entries) < len(day_entries_all):
            break  # bu gun KISMEN sigdirildi -- butce tukendi, sonraki gunlere gecme

    truncated_count = total_candidates - shown_rows
    period_label = _dominant_period_label(filtered)

    if market == "NASDAQ":
        data_sources_note = "NASDAQ takvim API"
    else:
        data_sources_note = "KAP Finansal Takvim bildirimi, geçmiş yayın medyanı"

    return {
        "market": market,
        "market_label": market_label,
        "period_label": f"{period_label} Dönemi" if period_label else None,
        "days_ahead": days_ahead,
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "day_groups": day_groups,
        "is_empty": total_candidates == 0,
        "truncated_count": truncated_count,
        "is_truncated": truncated_count > 0,
        "legend_items": _LEGEND_ITEMS,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


def build_calendar_share_text(context: dict) -> str:
    """build_calendar_context()'in ürettiği context'ten, X/Telegram'da
    doğrudan kopyala-yapıştır paylaşılabilecek düz metin listesini üretir
    (bkz. X_BUYUME_RAPORU.md Bölüm 3, kalıp ⑤ "Yaklaşan takvim" -- aynı
    "gün gün liste + kaydet çağrısı" biçimi, ama tek haftayla SINIRLI
    olmayan bir pencerede tarih belirsizliğini önlemek için gün adı
    kısaltması yerine TAM tarih kullanılır).

    Bu fonksiyon YENİDEN HESAPLAMA yapmaz -- context zaten
    build_calendar_context() tarafından üretilmiş, burada sadece farklı
    bir (düz metin) sunuma çevrilir; kartla AYNI kaynak (bkz.
    card.py/telegram_bot.py'deki "kartla aynı kaynak" ilkesi)."""
    if context["is_empty"]:
        return (
            f"📅 Yaklaşan Bilanço Tarihleri · {context['market_label']}\n\n"
            "Bu aralıkta kesin/tahmini bir bilanço tarihi bulunamadı.\n\n"
            f"{context['disclaimer']}"
        )

    lines = [f"📅 Yaklaşan Bilanço Tarihleri · {context['market_label']}", ""]
    for group in context["day_groups"]:
        gun_etiketi = group["date_label"] + (" (BUGÜN)" if group["is_today"] else "")
        tickers = ", ".join(f"${row['ticker']}" for row in group["rows"])
        lines.append(f"{gun_etiketi}: {tickers}")

    if context["is_truncated"]:
        lines.append("")
        lines.append(f"(+{context['truncated_count']} kayıt daha var, okunabilirlik için kısaltıldı)")

    lines.append("")
    lines.append(f"Kaydet, önümüzdeki {context['days_ahead']} gün boyunca elinin altında olsun.")
    lines.append("")
    lines.append(context["disclaimer"])
    return "\n".join(lines)
