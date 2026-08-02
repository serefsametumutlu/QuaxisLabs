"""src/bot/telegram_bot.py -- saf mantik testleri (ticker normalizasyonu,
hiz siniri). Telegram Update/Application nesnelerini gerektiren async
handler'lar (gercek bot API'sine bagimli) bu dosyanin kapsami disindadir;
uctan uca akis tests/test_pipeline.py ve scripts/demo_pipeline.py ile
dogrulanir.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.ai.commentary import Commentary
from src.bot import telegram_bot


# --- normalize_ticker_input -----------------------------------------------------


@pytest.mark.parametrize(
    "girdi,beklenen",
    [
        ("THYAO", "THYAO"),
        ("thyao", "THYAO"),
        ("$thyao", "THYAO"),
        ("#THYAO", "THYAO"),
        ("  thyao  ", "THYAO"),
        ("#$thyao", "THYAO"),
        ("bim", "BIM"),
    ],
)
def test_normalize_ticker_input_gecerli_kodlar(girdi, beklenen) -> None:
    assert telegram_bot.normalize_ticker_input(girdi) == beklenen


@pytest.mark.parametrize("girdi", ["ab", "abcdefg", "thy4o", "", "   ", "thy ao", "12345"])
def test_normalize_ticker_input_gecersiz_girdi_none_doner(girdi) -> None:
    assert telegram_bot.normalize_ticker_input(girdi) is None


# --- _check_rate_limit -----------------------------------------------------


@pytest.fixture(autouse=True)
def _temiz_rate_limit_durumu():
    telegram_bot._rate_limit_history.clear()
    yield
    telegram_bot._rate_limit_history.clear()


def test_check_rate_limit_ilk_uc_istek_izinli() -> None:
    user_id = 111
    assert telegram_bot._check_rate_limit(user_id) is True
    assert telegram_bot._check_rate_limit(user_id) is True
    assert telegram_bot._check_rate_limit(user_id) is True


def test_check_rate_limit_dorduncu_istek_reddedilir() -> None:
    user_id = 222
    for _ in range(3):
        telegram_bot._check_rate_limit(user_id)
    assert telegram_bot._check_rate_limit(user_id) is False


def test_check_rate_limit_kullanicilar_birbirinden_bagimsiz() -> None:
    for _ in range(3):
        telegram_bot._check_rate_limit(111)
    assert telegram_bot._check_rate_limit(222) is True


def test_check_rate_limit_pencere_disina_cikan_istekler_sayilmaz() -> None:
    user_id = 333
    # Gecmis, pencerenin (60s) disinda kalacak sekilde elle dolduruluyor.
    telegram_bot._rate_limit_history[user_id] = [0.0, 0.0, 0.0]
    assert telegram_bot._check_rate_limit(user_id) is True


# --- _bilanco_ozeti_metni -----------------------------------------------------


def _sahte_bilesen(name: str, score: Decimal | None, weight: str, reasoning: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, score=score, weight_nominal=Decimal(weight), reasoning_tr=reasoning)


def _sahte_sonuc(positives: list[str], negatives: list[str], summary: str = "Genel değerlendirme metni.") -> SimpleNamespace:
    yorum = Commentary(
        headline="BAŞLIK", summary=summary, positives=positives, negatives=negatives,
        kap_note=None, disclaimer_context=None, source="llm",
    )
    skor = SimpleNamespace(
        total_score=Decimal("8.5"),
        badge="SAĞLAM",
        components=[
            _sahte_bilesen("Kârlılık", Decimal("7.0"), "20", "Net marj güçlü."),
            _sahte_bilesen("Nakit Üretimi", None, "21", "FAVÖK hesaplanamadı."),
        ],
    )
    return SimpleNamespace(
        ticker="TESTAS",
        analysis=SimpleNamespace(latest_period=(2026, 3)),
        score=skor,
        commentary=yorum,
    )


def test_bilanco_ozeti_metni_basligi_ve_donemi_icerir() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["artış"], ["azalış"]))
    assert "#TESTAS · 1Ç26 Bilanço Özeti" in text


def test_bilanco_ozeti_metni_artislari_madde_isaretiyle_listeler() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["Hasılat arttı.", "Kâr arttı."], []))
    assert "📈 Artışlar:" in text
    assert "• Hasılat arttı." in text
    assert "• Kâr arttı." in text


def test_bilanco_ozeti_metni_azalislari_madde_isaretiyle_listeler() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], ["Nakit azaldı."]))
    assert "📉 Azalışlar:" in text
    assert "• Nakit azaldı." in text


def test_bilanco_ozeti_metni_genel_degerlendirmeyi_icerir() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], [], summary="Şirket sağlam görünüyor."))
    assert "Şirket sağlam görünüyor." in text


def test_bilanco_ozeti_metni_bos_listelerde_baslik_gostermez() -> None:
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc([], []))
    assert "📈 Artışlar:" not in text
    assert "📉 Azalışlar:" not in text


def test_bilanco_ozeti_metni_skor_ve_gerekceyi_icerir() -> None:
    """Kullanici istegi: gonderi metni (goruntuyle BIRLIKTE tek basina
    paylasilabilir olsun diye) skoru VE "neden bu skor" gerekcesini de
    icermeli -- kartta zaten gosterilen scorer.py bilesen gerekceleriyle
    AYNI kaynaktan."""
    text = telegram_bot._bilanco_ozeti_metni(_sahte_sonuc(["artış"], []))
    assert "🎯 Radar Skoru: 8,50/10 (SAĞLAM)" in text
    assert "Neden bu skor:" in text
    assert "• Kârlılık (%20 ağırlık) — 7,0/10: Net marj güçlü." in text
    assert "• Nakit Üretimi (%21 ağırlık) — N/A: FAVÖK hesaplanamadı." in text
