"""Faz 13: "Yaklaşan Bilanço Tarihleri" takvim kartı context builder'ı.

src/render/card.py'deki build_*_card_context() fonksiyonlarıyla AYNI ilkeye
uyar: burada HİÇBİR sayı/tarih HESAPLANMAZ -- src.fetchers.earnings_calendar
zaten hesaplanmış (yaklaşım 1/2/3 birleştirilmiş) EarningsDate listesini
verir, bu modül SADECE görsel gruplama (tarihe göre, güven seviyesine göre)
+ Türkçe biçimlendirme yapar.

TASARIM (kullanıcıyla birlikte 2026-08-02'de netleştirildi, İKİ AYRI geri
bildirim turu sonrası):
1. KAPSAM: kart SADECE CONFIDENCE_KESIN ve CONFIDENCE_TAHMINI seviyelerini
   gösterir. CONFIDENCE_SON_TARIH (SPK yasal son bildirim tarihi -- şirket
   HENÜZ hiçbir şey açıklamamış, sadece yasal tavan) BİLEREK DIŞLANIR:
   fetch_upcoming_bist taranan HER ticker için legal_deadline() ile HER
   ZAMAN bir tarih üretebildiğinden, son_tarih dahil edilseydi taranan TÜM
   evren listelenir, kart kalabalıklaşırdı.
2. İKİ KATMAN: kullanıcı kartı "bilanço tarihleri KESİNLEŞEN şirketler" diye
   paylaşacağını belirtti -- bu yüzden KESİN ve TAHMİNİ artık AYRI, görsel
   olarak belirgin şekilde farklı iki bölümde gösteriliyor (kesin üstte
   büyük/vurgulu, tahmini altta küçük/soluk) -- rozet yerine BÖLÜM başına
   tek bir açıklama yeterli, her satırda tekrar tekrar rozet YOK.
3. YAN YANA "CHIP" DÜZENİ: kullanıcı geri bildirimi -- alt alta (bir şirket
   bir satır) düzen çok yer kaplıyordu (57 satır/16 gün grubu Telegram'ın
   fotoğraf boyut sınırını aşıp `Photo_invalid_dimensions` hatası verdi,
   bkz. 06_BILINEN_SORUNLAR.md §A33). Şirketler artık HER GÜN İÇİNDE yan
   yana (logo+ticker, şirket adı OLMADAN -- referans tweet'lerdeki gibi
   sade #TICKER listesi) "chip" olarak diziliyor, satır kırılımı (wrap)
   sayesinde aynı alan içine ÇOK DAHA FAZLA şirket sığıyor.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from src.fetchers import company_logo
from src.fetchers.earnings_calendar import CONFIDENCE_KESIN, CONFIDENCE_TAHMINI, EarningsDate

_AY_ADLARI_TR: dict[int, str] = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}
_GUN_ADLARI_TR: dict[int, str] = {
    0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar",
}
_MARKET_LABELS: dict[str, str] = {"BIST": "BİST", "NASDAQ": "NASDAQ"}

# Chip'ler calendar_card.html'de SABİT genişlikte (.chip{width:...}) --
# böylece bir satıra kaç chip sığacağı, TICKER METNİNİN gerçek render
# genişliğine BAĞLI OLMADAN (BIST/NASDAQ ticker'ları hep kısa, 1-6 harf)
# ÖNCEDEN, KESİN olarak hesaplanabilir -- bkz. _wrap_line_count(). Kullanıcı
# geri bildirimi (2026-08-02): iki katman (kesin/tahmini) artık BİREBİR AYNI
# chip boyutunu kullanıyor (bkz. calendar_card.html .chip kuralı) -- bu
# yüzden satır başına chip sayısı da AYNI.
_KESIN_CHIPS_PER_ROW = 10
_TAHMINI_CHIPS_PER_ROW = 10

# CANLI hata (kullanıcı raporu, 2026-08-02): eski "bir şirket bir satır"
# tasarımında 57 satır/16 gün grubu 2400x8924 piksele ulaşıp Telegram'ın
# `send_photo` boyut sınırını (genişlik+yükseklik <= 10000) AŞMIŞTI. Yeni
# "yan yana chip" tasarımı ÇOK daha kompakt (aynı 67 kayıt artık ~4000px
# civarında kalıyor, CANLI ölçüldü) ama YİNE DE bir güvenlik tavanı gerekir
# (örn. NASDAQ'ın binlerce şirketlik ham verisi için, bkz. §A31). Kontrollü
# render'larla kalibre edildi: yükseklik_px = FIXED + gün_sayısı*DAY_LABEL_PX
# + satır(wrap)_sayısı*LINE_PX (device_scale_factor=2 dahil, gerçek piksel).
_FIXED_OVERHEAD_PX = 1180  # ust bant + iki bolum basligi + footer + araliklar
_DAY_LABEL_PX = 56  # her gunun tarih etiketi (ust bosluk dahil)
_CHIP_LINE_PX = 68  # bir chip SATIRININ (wrap edilmis) yuksekligi
_CARD_PHYSICAL_WIDTH_PX = 2400  # 1200 CSS px * render_card'in device_scale_factor=2 sabiti
_TELEGRAM_MAX_PHOTO_DIMENSION_SUM = 10_000  # Telegram sendPhoto siniri (CANLI dogrulandi: "Photo_invalid_dimensions")
_HEIGHT_SAFETY_MARGIN_PX = 500
_MAX_CALENDAR_HEIGHT_PX = _TELEGRAM_MAX_PHOTO_DIMENSION_SUM - _CARD_PHYSICAL_WIDTH_PX - _HEIGHT_SAFETY_MARGIN_PX

_DEFAULT_MAX_ROWS = 150  # tier basina toplam sirket tavani (chip tasarimi cok kompakt oldugu icin daha yuksek olabilir)


def _wrap_line_count(chip_count: int, chips_per_row: int) -> int:
    """`chip_count` chip, `chips_per_row` genişliğinde bir satıra sığdırılırsa
    KAÇ satıra (wrap) ihtiyaç duyulur -- yukarı yuvarlama (ceil), harici
    kütüphane olmadan tam sayı bölmesiyle."""
    if chip_count <= 0:
        return 0
    return -(-chip_count // chips_per_row)


def _turkish_date_label(d: date) -> str:
    return f"{d.day:02d} {_AY_ADLARI_TR[d.month]} {d.year} · {_GUN_ADLARI_TR[d.weekday()]}"


def _quarter_label(period: tuple[int, int]) -> str:
    year, quarter = period
    return f"{quarter // 3}Ç{year % 100:02d}"


def _dominant_period_label(entries: list[EarningsDate]) -> str | None:
    """Karttaki başlıkta gösterilecek TEK bir dönem etiketi (örn. "2Ç26
    Dönemi") -- listelenen şirketlerin BÜYÜK ÇOĞUNLUĞU aynı takvim
    çeyreğini hedeflediği için en sık geçen `period` değeri alınır."""
    if not entries:
        return None
    counts: dict[tuple[int, int], int] = {}
    for e in entries:
        counts[e.period] = counts.get(e.period, 0) + 1
    return _quarter_label(max(counts, key=lambda p: counts[p]))


def _company_logo_or_none(ticker: str, market: str) -> str | None:
    try:
        return company_logo.fetch_logo_data_uri(ticker, market=market)
    except Exception:
        return None


def _build_tier_day_groups(
    entries: list[EarningsDate],
    market: str,
    today: date,
    chips_per_row: int,
    max_rows: int,
    remaining_height_budget_px: list[int],
) -> tuple[list[dict], int]:
    """Tek bir güven katmanı (kesin YA DA tahmini) için tarihe göre gruplanmış
    chip satırlarını üretir. `remaining_height_budget_px` TEK elemanlı bir
    liste olarak geçirilir (mutable "by reference" -- iki katman ARDIŞIK
    olarak aynı toplam piksel bütçesini paylaşır, kesin katmanı önce
    doldurulur, kalan bütçe tahmini katmanına aktarılır).

    Döner: (day_groups, kesilen_sirket_sayisi)."""
    by_date: dict[date, list[EarningsDate]] = defaultdict(list)
    for e in entries:
        by_date[e.expected_date].append(e)

    day_groups: list[dict] = []
    shown = 0
    for day in sorted(by_date):
        day_entries_all = by_date[day]
        if shown >= max_rows or remaining_height_budget_px[0] <= _DAY_LABEL_PX:
            break

        day_entries = day_entries_all[: max_rows - shown]
        # Bu gunun TAMAMI/KISMI sigar mi -- chip SATIRI (wrap) bazinda hesapla.
        while day_entries:
            lines_needed = _wrap_line_count(len(day_entries), chips_per_row)
            cost = _DAY_LABEL_PX + lines_needed * _CHIP_LINE_PX
            if cost <= remaining_height_budget_px[0]:
                break
            day_entries = day_entries[:-1]  # butceye sigana kadar SONDAN kirp

        if not day_entries:
            break

        rows = [
            {"ticker": e.ticker, "company_name": e.company_name, "logo_data_uri": _company_logo_or_none(e.ticker, market)}
            for e in day_entries
        ]
        day_groups.append(
            {
                "date_label": _turkish_date_label(day),
                "date_short": day.strftime("%d.%m.%Y"),
                "is_today": day == today,
                "rows": rows,
            }
        )

        shown += len(day_entries)
        lines_needed = _wrap_line_count(len(day_entries), chips_per_row)
        remaining_height_budget_px[0] -= _DAY_LABEL_PX + lines_needed * _CHIP_LINE_PX

        if len(day_entries) < len(day_entries_all):
            break  # bu gun KISMEN sigdirildi -- butce/tavan tukendi

    truncated_count = len(entries) - shown
    return day_groups, truncated_count


def build_calendar_context(
    entries: list[EarningsDate],
    market: str,
    *,
    days_ahead: int = 30,
    now: datetime | None = None,
    max_rows: int = _DEFAULT_MAX_ROWS,
) -> dict:
    """`entries`: src.fetchers.earnings_calendar.fetch_upcoming_bist()/
    fetch_upcoming_nasdaq() çıktısı (ya da repository.get_upcoming_earnings()
    satırlarından üretilmiş EarningsDate listesi) -- ÖNCEDEN hesaplanmış,
    burada hiçbir tarih/güven seviyesi mantığı TEKRAR ÜRETİLMEZ.

    Dönen dict İKİ AYRI katman taşır: `kesin_day_groups`/`tahmini_day_groups`
    (bkz. modül üst notu). Her ikisi de AYNI toplam piksel yükseklik
    bütçesini (`_MAX_CALENDAR_HEIGHT_PX`) paylaşır -- kesin katmanı ÖNCE
    doldurulur (kullanıcı önceliği: kesin tarihler HİÇBİR ZAMAN kesilmemeli
    -- pratikte kesin sayısı zaten az olduğu için bu nadiren devreye girer),
    kalan bütçe tahmini katmanına aktarılır.

    Dönen dict, calendar_card.html'in beklediği TAMAMEN ÖNCEDEN
    biçimlendirilmiş bir şemadır (render katmanı hesaplama yapmaz, sadece
    filtreler/gruplar/biçimlendirir)."""
    now = now or datetime.now()
    market_label = _MARKET_LABELS.get(market, market)
    today = now.date()

    kesin_entries = sorted((e for e in entries if e.confidence == CONFIDENCE_KESIN), key=lambda e: (e.expected_date, e.ticker))
    tahmini_entries = sorted((e for e in entries if e.confidence == CONFIDENCE_TAHMINI), key=lambda e: (e.expected_date, e.ticker))

    height_budget = [_MAX_CALENDAR_HEIGHT_PX]
    kesin_day_groups, kesin_truncated = _build_tier_day_groups(
        kesin_entries, market, today, _KESIN_CHIPS_PER_ROW, max_rows, height_budget
    )
    tahmini_day_groups, tahmini_truncated = _build_tier_day_groups(
        tahmini_entries, market, today, _TAHMINI_CHIPS_PER_ROW, max_rows, height_budget
    )

    period_label = _dominant_period_label(kesin_entries or tahmini_entries)

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
        "kesin_day_groups": kesin_day_groups,
        "is_kesin_empty": not kesin_day_groups,
        "kesin_truncated_count": kesin_truncated,
        "tahmini_day_groups": tahmini_day_groups,
        "is_tahmini_empty": not tahmini_day_groups,
        "tahmini_truncated_count": tahmini_truncated,
        "is_empty": not kesin_day_groups and not tahmini_day_groups,
        "data_sources_note": data_sources_note,
        "disclaimer": "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır.",
    }


def _share_text_tier_lines(day_groups: list[dict]) -> list[str]:
    lines = []
    for group in day_groups:
        # Paylasim metni referans tweet'lerdeki "GG.AA.YYYY - #TICK, #TICK"
        # kalibina UYAR (bkz. modul ust notu) -- gorsel karttaki daha okunakli
        # "03 Agustos 2026 . Pazartesi" basligindan FARKLI olarak burada KISA/
        # kopyala-yapistir dostu tarih (`date_short`) kullanilir.
        gun_bugun = " (BUGÜN)" if group["is_today"] else ""
        tickers = ", ".join(f"#{row['ticker']}" for row in group["rows"])
        lines.append(f"{group['date_short']}{gun_bugun} - {tickers}")
    return lines


def build_calendar_share_text(context: dict) -> str:
    """build_calendar_context()'in ürettiği context'ten, X/Telegram'da
    doğrudan kopyala-yapıştır paylaşılabilecek düz metin listesini üretir.
    Format kullanıcının referans gösterdiği gerçek X paylaşımlarıyla AYNI:
    "GG.AA.YYYY - #TICK, #TICK" (gün adı/rozet YOK, sade).

    Bu fonksiyon YENİDEN HESAPLAMA yapmaz -- context zaten
    build_calendar_context() tarafından üretilmiş, burada sadece farklı
    bir (düz metin) sunuma çevrilir; kartla AYNI kaynak."""
    if context["is_empty"]:
        return (
            f"📅 Yaklaşan Bilanço Tarihleri · {context['market_label']}\n\n"
            "Bu aralıkta kesin/tahmini bir bilanço tarihi bulunamadı.\n\n"
            f"{context['disclaimer']}"
        )

    lines = [f"📅 Yaklaşan Bilanço Tarihleri · {context['market_label']}", ""]

    if not context["is_kesin_empty"]:
        lines.append("✅ KESİNLEŞEN TARİHLER")
        lines.extend(_share_text_tier_lines(context["kesin_day_groups"]))
        if context["kesin_truncated_count"]:
            lines.append(f"(+{context['kesin_truncated_count']} kesinleşmiş kayıt daha var)")
        lines.append("")

    if not context["is_tahmini_empty"]:
        lines.append("〰️ TAHMİNİ TARİHLER (henüz kesinleşmedi)")
        lines.extend(_share_text_tier_lines(context["tahmini_day_groups"]))
        if context["tahmini_truncated_count"]:
            lines.append(f"(+{context['tahmini_truncated_count']} tahmini kayıt daha var)")
        lines.append("")

    lines.append(f"Kaydet, önümüzdeki {context['days_ahead']} gün boyunca elinin altında olsun.")
    lines.append("")
    lines.append(context["disclaimer"])
    return "\n".join(lines)
