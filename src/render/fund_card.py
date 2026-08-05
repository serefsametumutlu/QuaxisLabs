"""Faz 19: fon günlük getiri TAHMİNİ kartlarının context builder'ı --
`src.render.card`/`calendar_card` ile AYNI ilke: burada HİÇBİR sayı
HESAPLANMAZ, `src.bot.fund_pipeline.FundEstimateResult` (zaten
`src.analysis.fund_estimator.estimate_daily_return()` tarafından
hesaplanmış) sadece Türkçe biçimlendirilip görsel sınıflara (renk) eşlenir.

Referans görsel (kullanıcının paylaştığı bir üçüncü taraf ekran görüntüsü,
image.png) İKİ SÜTUNLU "en çok katkı sağlayan / en çok kaybettiren" +
altta büyük fon kodu/tahmini getiri düzenini kullanıyordu -- kullanıcı
BİREBİR AYNI olmasın diye AÇIKÇA istedi (kullanıcı: "tasarımı vs.
değiştirip daha geliştirebiliriz... içerik çalmış gibi görünmek
istemem"). Bu yüzden BURADA: QuaxisLabs marka dili (logo/masthead/
disclaimer -- card.py/calendar_card.py ile AYNI), "Quaxis Fon Tahmini"
başlığı, ayrı bir renk/tipografi sistemi (proje genelindeki dark
glassmorphism/monospace tema) kullanılır -- yapısal fikir (iki sütun +
büyük alt toplam) esinlenme düzeyinde kalır, piksel bazında KOPYA değildir.

🚨 BU KART DENEYSEL bir TAHMİN gösterir, gerçekleşmiş/açıklanmış fon
getirisi DEĞİLDİR (bkz. `src.analysis.fund_estimator` modül üst notundaki
geriye dönük doğrulama uyarısı -- MAE ilk turda 1,36 puan çıkmıştı, ikinci
turda hedef fonlarla yeniden ölçüldü, bkz. PROJE_HAFIZASI). Kart bu
uyarıyı HER ZAMAN açıkça gösterir (Kural 3/8) -- gizlenmez.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from src.analysis import fund_estimator
from src.bot.fund_pipeline import FundEstimateResult
from src.formatting import format_number_tr

_AY_ADLARI_TR: dict[int, str] = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}

_CONFIDENCE_LABELS = {
    "yüksek": "🟢 Yüksek Güven",
    "orta": "🟡 Orta Güven",
    "düşük": "🔴 Düşük Güven",
}

_TOP_N = 5  # referans görseldeki gibi en fazla 5+5 satır (bkz. modül üst notu)

_DISCLAIMER = (
    "Bu içerik yatırım tavsiyesi değildir; yatırım kararı için profesyonel danışmanlık alınmalıdır. "
    "Gösterilen rakam DENEYSEL bir TAHMİNDİR, fonun gerçekleşmiş/açıklanmış getirisi DEĞİLDİR."
)


def _turkish_date_label(d: date) -> str:
    return f"{d.day:02d} {_AY_ADLARI_TR[d.month]} {d.year}"


def _signed_percent(value: Decimal | None, decimals: int = 2) -> str:
    """Kullanıcının istediği '+0,79%'/'-0,20%' biçimi -- proje genelindeki
    `format_percent_tr` ('%3,2' -- % ÖNEKTE) İLE KASITLI OLARAK FARKLI,
    çünkü kullanıcı açıkça bu kartta işaretin/yüzdenin SONDA olmasını
    istedi (referans görselle aynı okuma yönü)."""
    if value is None:
        return "—"
    quant = Decimal(1).scaleb(-decimals)
    quantized = value.quantize(quant, rounding=ROUND_HALF_UP)
    sign = "+" if quantized > 0 else ("-" if quantized < 0 else "")
    return f"{sign}{format_number_tr(abs(quantized), decimals=decimals)}%"


def _return_color_class(value: Decimal | None) -> str:
    if value is None:
        return "neutral"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _contribution_row(c: fund_estimator.HoldingContribution) -> dict:
    return {
        "label": c.ticker or c.name,
        "name": c.name,
        "weight_display": f"%{format_number_tr(c.weight_pct, decimals=2)}",
        "return_display": _signed_percent(c.daily_return_pct),
        "return_color_class": _return_color_class(c.daily_return_pct),
        "contribution_display": _signed_percent(c.contribution_pct, decimals=2),
        "contribution_color_class": _return_color_class(c.contribution_pct),
    }


def build_fund_estimate_card_context(result: FundEstimateResult, now: datetime | None = None) -> dict:
    """`compute_fund_estimate()` sonucundan (BAŞARILI olduğu varsayılır --
    çağıran taraf `result.estimate is not None` kontrolünü ÖNCEDEN yapmalı,
    bkz. `src.bot.telegram_bot._gonder_fon_analiz`) tek fonluk detaylı kart
    context'ini üretir."""
    now = now or datetime.now()
    estimate = result.estimate
    assert estimate is not None  # cagiran taraf garanti eder (bkz. docstring)

    positive_contributions = sorted(
        (c for c in estimate.contributions if c.contribution_pct > 0), key=lambda c: -c.contribution_pct
    )[:_TOP_N]
    negative_contributions = sorted(
        (c for c in estimate.contributions if c.contribution_pct < 0), key=lambda c: c.contribution_pct
    )[:_TOP_N]

    interval_low, interval_high = estimate.confidence_interval

    return {
        "fund_code": estimate.fund_code,
        "fund_name": result.fund_name or estimate.fund_code,
        "date_label": _turkish_date_label(estimate.estimate_date),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "estimated_return_display": _signed_percent(estimate.estimated_return_pct, decimals=4),
        "estimated_return_color_class": _return_color_class(estimate.estimated_return_pct),
        "confidence_label": _CONFIDENCE_LABELS.get(estimate.confidence, estimate.confidence),
        "confidence_interval_display": (
            f"{_signed_percent(interval_low)} ile {_signed_percent(interval_high)} arası"
        ),
        "covered_weight_display": f"%{format_number_tr(estimate.covered_weight_pct, decimals=1)}",
        "staleness_days": estimate.portfolio_staleness_days,
        "uncovered_note": estimate.uncovered_note,
        "positive_contributions": [_contribution_row(c) for c in positive_contributions],
        "negative_contributions": [_contribution_row(c) for c in negative_contributions],
        "is_positive_empty": not positive_contributions,
        "is_negative_empty": not negative_contributions,
        "disclaimer": _DISCLAIMER,
    }


def build_fund_group_card_context(
    results: list[FundEstimateResult], title: str, now: datetime | None = None
) -> dict:
    """Birden fazla fonun SADECE tahmini getirisini gösteren özet kart
    context'i (Faz 19 GÖREV'indeki 2. ve 3. grup: 'öne çıkan fonlar' /
    'tüm liste'). Tahmin üretilemeyen fonlar AYRI bir bölümde ("veri yok")
    gösterilir -- Kural 3: sessizce atlanmaz, sebep her satırda görünür."""
    now = now or datetime.now()

    available = [r for r in results if r.estimate is not None]
    available.sort(key=lambda r: r.estimate.estimated_return_pct, reverse=True)  # en yuksekten en dusuge

    rows = [
        {
            "fund_code": r.fund_code,
            "fund_name": r.fund_name or r.fund_code,
            "return_display": _signed_percent(r.estimate.estimated_return_pct, decimals=4),
            "return_color_class": _return_color_class(r.estimate.estimated_return_pct),
            "confidence_label": _CONFIDENCE_LABELS.get(r.estimate.confidence, r.estimate.confidence),
        }
        for r in available
    ]
    unavailable_rows = [
        {"fund_code": r.fund_code, "fund_name": r.fund_name or r.fund_code, "reason": r.reason or "Tahmin üretilemedi."}
        for r in results
        if r.estimate is None
    ]

    return {
        "title": title,
        "date_label": _turkish_date_label(now.date()),
        "report_timestamp": now.strftime("%d.%m.%Y %H:%M"),
        "rows": rows,
        "unavailable_rows": unavailable_rows,
        "is_unavailable_empty": not unavailable_rows,
        "is_empty": not rows and not unavailable_rows,
        "disclaimer": _DISCLAIMER,
    }
