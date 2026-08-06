"""Faz 5 teslim kriteri: JSON guvenligi, retry/yedek mod davranisi ve
LLM'siz mekanik ozetin elle dogrulanmis testleri. Gercek Gemini API'sine
AG ISTEGI GONDERILMEZ -- httpx.post monkeypatch ile sahtelenir.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import httpx
import pytest
from tenacity import wait_fixed

import config
from src.ai import commentary
from src.analysis import calculator, scorer
from src.fetchers import kap


# --- _clean_json_text / _parse_json_response -----------------------------------------------------


def test_clean_json_text_kod_blogu_isaretlerini_temizler() -> None:
    ham = '```json\n{"a": 1}\n```'
    assert commentary._clean_json_text(ham) == '{"a": 1}'


def test_clean_json_text_isaretsiz_metni_degistirmez() -> None:
    assert commentary._clean_json_text('{"a": 1}') == '{"a": 1}'


def test_parse_json_response_gecerli_json_sozluk_doner() -> None:
    assert commentary._parse_json_response('{"headline": "X"}') == {"headline": "X"}


def test_parse_json_response_gecersiz_json_none_doner() -> None:
    assert commentary._parse_json_response("bu json degil {{{") is None


# --- _contains_suspicious_artifact -----------------------------------------------------
# Canli bir Gemini yanitinda gozlemlenen gercek bir hata: model kap_note
# alaninin icine "————(Wait, ...)————" turunde kendi kendine bir Ingilizce
# dusunme notu sizdirmisti. Bu testler o sinifin tespit edildigini kilitler.


def test_contains_suspicious_artifact_tire_dizisini_yakalar() -> None:
    data = {"kap_note": "Şirket açıklama yapmıştır.————(Wait, let me reconsider)————"}
    assert commentary._contains_suspicious_artifact(data) is True


def test_contains_suspicious_artifact_ingilizce_ic_ses_kelimesini_yakalar() -> None:
    data = {"summary": "Hmm, actually the revenue figure needs reconsideration."}
    assert commentary._contains_suspicious_artifact(data) is True


def test_contains_suspicious_artifact_liste_alanlarini_da_kontrol_eder() -> None:
    data = {"positives": ["Hasılat %20 arttı", "wait, is this right?"]}
    assert commentary._contains_suspicious_artifact(data) is True


def test_contains_suspicious_artifact_temiz_veride_false() -> None:
    data = {
        "headline": "KÂR GÜÇLÜ ARTTI",
        "summary": "Hasılat yıllık %20,0 arttı.",
        "positives": ["FAVÖK %30,2 güçlü artış gösterdi."],
        "negatives": [],
        "kap_note": None,
    }
    assert commentary._contains_suspicious_artifact(data) is False


# --- ASCII'ye indirgenmis Turkce tespiti (canli TERA hatasinin regresyon testi) -----------------------------------------------------


def test_contains_suspicious_artifact_ascii_indirgenmis_turkceyi_yakalar() -> None:
    # canli hata: model "Satışlar yıllık bazda" yerine "Satislar yillik bazda" uretti.
    data = {"positives": ["Satislar yillik bazda %149,7 artarak 112,7 mr ₺ oldu."]}
    assert commentary._contains_suspicious_artifact(data) is True


@pytest.mark.parametrize(
    "bozuk_kelime",
    ["yillik", "ceyreklik", "artisla", "azalisla", "ozkaynaklari", "sirketin", "donemde", "borclar", "gerceklesti"],
)
def test_contains_suspicious_artifact_ascii_kok_kelimeleri_tek_tek_yakalar(bozuk_kelime) -> None:
    data = {"summary": f"Bu cumlede {bozuk_kelime} kelimesi geciyor."}
    assert commentary._contains_suspicious_artifact(data) is True


def test_contains_suspicious_artifact_doğru_turkce_yanlis_pozitif_uretmez() -> None:
    data = {
        "summary": "Şirketin özkaynakları çeyreklik bazda %53,4 artarak 92,4 mr ₺ oldu, "
        "borçlar geriledi, gerçekleşen büyüme güçlüydü."
    }
    assert commentary._contains_suspicious_artifact(data) is False


# --- ASCII'ye indirgenmiş Türkçe -- teknik görünüm kelime dağarcığı (Faz 15.1, CANLI hata) ------


def test_contains_suspicious_artifact_teknik_ascii_indirgenmis_turkceyi_yakalar() -> None:
    """CANLI hata (2026-08-06, `scripts/demo_teknik.py THYAO`): gerçek bir
    Gemini yanıtının `summary` alanı 'RSI 45,3 degeriyle notr bolgede yer
    alirken MACD negatif alandadir...' gibi ASCII'ye indirgenmiş kelimeler
    içeriyordu -- eski regex (sadece bilanço kökleri) bunu HİÇ
    YAKALAMAMIŞTI. Bu, o canlı yanıtın regresyon testidir.

    NOT: `headline` alanı şema gereği HER ZAMAN BÜYÜK HARF -- regex
    KASITLI OLARAK case-sensitive/küçük-harf (bkz. modül üst notu, ı/i
    case-folding hatası) olduğu için büyük harfli metin bu kontrolün
    KAPSAMI DIŞINDADIR (fundamental `headline` alanı için de aynı sınır
    zaten geçerliydi) -- bu yüzden test normal cümle (küçük harf)
    bağlamındaki `summary` alanını kullanır, gerçek canlı hatayla BİREBİR."""
    data = {"summary": "RSI 45,3 degeriyle notr bolgede yer alirken MACD negatif alandadir."}
    assert commentary._contains_suspicious_artifact(data) is True


@pytest.mark.parametrize(
    "bozuk_kelime",
    ["uzerinde", "altinda", "notr", "gosterge", "degeriyle", "surduruyor", "yuzde", "kesisimi", "onemli", "degisim", "degiskendir"],
)
def test_contains_suspicious_artifact_teknik_ascii_kok_kelimeleri_tek_tek_yakalar(bozuk_kelime) -> None:
    data = {"summary": f"Bu cümlede {bozuk_kelime} kelimesi geçiyor."}
    assert commentary._contains_suspicious_artifact(data) is True


def test_contains_suspicious_artifact_teknik_dogru_turkce_yanlis_pozitif_uretmez() -> None:
    data = {
        "summary": "Fiyat SMA200 üzerinde ve RSI nötr bölgede, gösterge değerleri birbiriyle "
        "uyumlu bir görünüm sürdürüyor; yüzde bazında önemli bir kesişim gözlenmedi, "
        "değişim ve değişken oynaklık normal seyrediyor."
    }
    assert commentary._contains_suspicious_artifact(data) is False


# --- _commentary_from_json -----------------------------------------------------


def test_commentary_from_json_zorunlu_alan_eksikse_hata_firlatir() -> None:
    with pytest.raises(commentary._NonRetryableLLMError):
        commentary._commentary_from_json({"summary": "x"}, source="llm")


def test_commentary_from_json_dogru_alanlari_esler_ve_4_madde_ile_sinirlar() -> None:
    data = {
        "headline": "BAŞLIK",
        "hook": "Kanca cümlesi.",
        "summary": "Özet metni.",
        "positives": ["a", "b", "c", "d", "e"],
        "negatives": [],
        "kap_note": None,
        "disclaimer_context": None,
    }
    result = commentary._commentary_from_json(data, source="llm")
    assert result.headline == "BAŞLIK"
    assert len(result.positives) == 4  # 5. madde kirpildi
    assert result.negatives == []
    assert result.kap_note is None
    assert result.source == "llm"


# --- Istem metni insasi: sadece formatlanmis degerler -----------------------------------------------------


def test_format_finding_zarardan_kara_gecti_yuzde_gostermez() -> None:
    f = calculator.Finding(
        field="net_income", label_tr="Net Dönem Kârı", comparison="YoY",
        current=Decimal("50"), previous=Decimal("-30"), percent_change=None,
        direction="artis", change_label=calculator.ChangeLabel.ZARARDAN_KARA_GECTI,
    )
    satir = commentary._format_finding(f)
    assert "zarardan kâra geçti" in satir
    assert "%" not in satir.split("->")[1]  # yuzde uretilmemis, sadece etiket var


def test_format_finding_normal_degisimde_yuzde_ve_etiket_birlikte() -> None:
    f = calculator.Finding(
        field="revenue", label_tr="Hasılat", comparison="YoY",
        current=Decimal("1200"), previous=Decimal("1000"), percent_change=Decimal("20"),
        direction="artis", change_label=calculator.ChangeLabel.ARTIS,
    )
    satir = commentary._format_finding(f)
    assert "%20" in satir
    assert "artış" in satir


def test_build_user_prompt_onemli_kap_yoksa_not_ekler(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    prompt = commentary._build_user_prompt(analiz, skor, [])
    assert "Önemli bildirim yok." in prompt


def test_build_user_prompt_onemli_kap_varsa_basligi_icerir(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    bildirim = kap.Disclosure(
        date=datetime(2026, 7, 1), title="Kuveyt Terminal 2 İhalesi", category="İhale Süreci / Sonucu",
        summary="Kuveyt Terminal 2 İhalesi", url="https://kap.org.tr/x", importance=kap.IMPORTANCE_HIGH,
        is_late=False, disclosure_index=1, stock_codes="TESTAS",
    )
    prompt = commentary._build_user_prompt(analiz, skor, [bildirim])
    assert "Kuveyt Terminal 2 İhalesi" in prompt


def test_build_user_prompt_annual_only_donem_ve_seri_etiketleri_yillik_olur() -> None:
    """B21 -- NVO/TSM/SHEL/BABA gibi annual-only ADR'lerde Dönem/bulgu/seri
    basliklarinda VE bizzat veri satirlarinda 'çeyrek' kelimesi GECMEMELI
    (SADECE, modelin kendi genel dunya bilgisinden 'dördüncü çeyreğinde'
    gibi UYDURMA bir ifade EKLEMESINI onlemek icin YAZILAN, kelimeyi
    ISIMLENDIRMEK ZORUNDA olan acik yasaklama cumlesi haric -- bkz.
    commentary.py _build_user_prompt ici not, CANLI GOZLEMLENDI bu oturumda:
    sadece veriden kelimeyi cikarmak YETERSIZ kalmisti, acik talimat gerekti)."""
    financials = {
        (2025, 12): _donem(309064, 250276, 127658, 14666, 102434, 26464, 5000, 542902, 130958, 194047, 172500, 370400),
        (2024, 12): _donem(290403, 245900, 128300, 14000, 100988, 24000, 4800, 520000, 128000, 180000, 165000, 355000),
        (2023, 12): _donem(270000, 220000, 120000, 13000, 95000, 22000, 4600, 500000, 125000, 170000, 160000, 340000),
        (2022, 12): _donem(260000, 210000, 115000, 12500, 90000, 20000, 4400, 480000, 120000, 160000, 155000, 325000),
    }
    analiz = calculator.analyze_us("NVO", financials)
    assert analiz.is_annual_only is True
    skor = scorer.score_industrial_us(analiz)
    prompt = commentary._build_user_prompt(analiz, skor, [])

    assert "Dönem: FY2025" in prompt
    assert "## Hesaplanmış Değişim Bulguları (Yıllık, tam yıl karşılaştırması)" in prompt
    assert "## Yıllık Seri (Trend)" in prompt
    assert "son 4 yıl" in prompt

    uyari_paragrafi = (
        "ÖNEMLİ: Bu şirket SADECE YILLIK finansal tablo (20-F, yabancı özel "
        "ihraççı) yayınlar, herhangi bir çeyreklik (Ç1/Ç2/Ç3/Ç4) verisi YOKTUR. "
        "Özetinde/başlığında/maddelerinde 'çeyrek', 'çeyreklik' veya 'Ç1-Ç4' gibi "
        "HİÇBİR ifade KULLANMA -- aşağıdaki tüm rakamlar TAM YIL (FY) rakamlarıdır, "
        "sadece 'yıllık bazda'/'FYyy' de."
    )
    assert uyari_paragrafi in prompt  # acik yasaklama talimati bizzat GEREKLI (kelimeyi ISIMLENDIRMEK zorunda)
    # Bulgu (finding) satirlarinin HICBIRI "(Çeyreklik)" DEMEMELI -- QoQ
    # tipi bulgular (bilanco kalemleri) icin "(Bilanço)" kullanilmali (bkz.
    # _format_finding ici not). NOT: scorer.py'nin bagimsiz ureттigi puan
    # gerekce metinleri (orn. "TTM icin 4 çeyrek eksik") bu testin/duzeltmenin
    # KAPSAMI DISINDA -- ayri bir modul, ayri bir iyilestirme konusu.
    bulgu_bolumu = prompt.split("## Rasyolar")[0]
    assert "(Çeyreklik)" not in bulgu_bolumu
    assert "(Bilanço)" in bulgu_bolumu


def test_build_user_prompt_normal_sirkette_ceyrek_kelimesi_kullanmaya_devam_eder(saglikli_analiz_ve_skor) -> None:
    """Regresyon kilidi: is_annual_only=False (normal BIST/AAPL tipi
    sirketler) icin eski davranis (Dönem: yil/Çn, "çeyrek" kelimesi
    kullanimi) DEGISMEMELI."""
    analiz, skor = saglikli_analiz_ve_skor
    prompt = commentary._build_user_prompt(analiz, skor, [])
    assert "çeyrek" in prompt.lower()
    assert "SADECE YILLIK" not in prompt


# --- Fixture: gercekci AnalysisResult + ScoreResult -----------------------------------------------------

_LATEST = (2026, 3)
_YOY_PRIOR = (2025, 3)
_QOQ_PRIOR = (2025, 12)
_TTM_3 = (2025, 9)
_TTM_4 = (2025, 6)


def _donem(revenue, gross, op, dep, net, cash, tr, assets, debt, equity, ca, stl) -> dict:
    # "_cum" (kumulatif/YTD) alanlari bu testlerde KASITLI OLARAK ceyreklik
    # alanla ayni deger tasir -- bkz. test_calculator.py::_sample_financials notu.
    return {
        "revenue": Decimal(revenue), "revenue_cum": Decimal(revenue),
        "gross_profit": Decimal(gross), "gross_profit_cum": Decimal(gross),
        "operating_profit": Decimal(op), "operating_profit_cum": Decimal(op),
        "depreciation_amortization": Decimal(dep), "depreciation_amortization_cum": Decimal(dep),
        "net_income": Decimal(net), "net_income_cum": Decimal(net), "cash": Decimal(cash),
        "trade_receivables": Decimal(tr), "total_assets": Decimal(assets), "financial_debt": Decimal(debt),
        "equity": Decimal(equity), "current_assets": Decimal(ca), "short_term_liabilities": Decimal(stl),
    }


@pytest.fixture()
def saglikli_analiz_ve_skor():
    financials = {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _QOQ_PRIOR: _donem(1100, 460, 320, 58, 230, 380, 140, 4800, 620, 2850, 1700, 880),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, 180, 300, 130, 4500, 700, 2600, 1600, 850),
        _TTM_3: _donem(1050, 430, 280, 56, 200, 320, 135, 4600, 680, 2700, 1650, 860),
        _TTM_4: _donem(980, 390, 250, 54, 175, 290, 125, 4400, 690, 2550, 1580, 840),
    }
    analiz = calculator.analyze("TESTAS", financials)
    skor = scorer.score_industrial(analiz)
    return analiz, skor


@pytest.fixture()
def zarar_gecisli_analiz_ve_skor():
    """Net kar YoY zarardan kara gecen bir senaryo -- fallback'in ozel
    etiketi (yuzde uretmeden) dogru aktardigini dogrulamak icin."""
    financials = {
        _LATEST: _donem(1200, 500, 350, 60, 260, 400, 150, 5000, 600, 3000, 1800, 900),
        _YOY_PRIOR: _donem(1000, 400, 260, 55, -80, 300, 130, 4500, 700, 2600, 1600, 850),
    }
    analiz = calculator.analyze("ZARARAS", financials)
    skor = scorer.score_industrial(analiz)
    return analiz, skor


# --- _fallback_commentary -----------------------------------------------------


def test_fallback_commentary_source_alani_fallback(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    yorum = commentary._fallback_commentary(analiz, skor, [])
    assert yorum.source == "fallback"
    assert yorum.summary
    assert yorum.headline


def test_fallback_commentary_hook_ilk_iki_bulgudan_kurulur(saglikli_analiz_ve_skor) -> None:
    """Faz 16.4: 'hook' alanı X/Twitter thread'inin ilk gönderisi için --
    LLM'siz modda YENİ bir cümle UYDURULMAZ, ZATEN var olan ilk 2 öncelikli
    bulgu (_fallback_sentence/_oncelik_anahtari ile AYNI sıralama) yeniden
    kullanılır."""
    analiz, skor = saglikli_analiz_ve_skor
    anlamli = [f for f in analiz.findings if f.change_label != calculator.ChangeLabel.VERI_YOK]
    beklenen_ilk_iki = sorted(anlamli, key=commentary._oncelik_anahtari)[:2]
    beklenen_hook = " ".join(commentary._fallback_sentence(f) for f in beklenen_ilk_iki)

    yorum = commentary._fallback_commentary(analiz, skor, [])
    assert yorum.hook == beklenen_hook


def test_fallback_commentary_pozitif_bulgular_positives_listesinde(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    yorum = commentary._fallback_commentary(analiz, skor, [])
    # Satislar YoY %20 artis -- pozitif bulgu olarak gecmeli.
    assert any("Satışlar" in p and "%20" in p for p in yorum.positives)


def test_fallback_commentary_zarardan_kara_gecis_yuzde_uretmeden_aktarilir(zarar_gecisli_analiz_ve_skor) -> None:
    analiz, skor = zarar_gecisli_analiz_ve_skor
    yorum = commentary._fallback_commentary(analiz, skor, [])
    net_kar_cumlesi = next(p for p in yorum.positives if "Net Dönem Kârı" in p)
    assert "zarardan kâra geçti" in net_kar_cumlesi
    assert "%" not in net_kar_cumlesi


def test_fallback_commentary_onemli_kap_varsa_not_uretir(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    bildirim = kap.Disclosure(
        date=datetime(2026, 7, 1), title="Önemli Sözleşme İmzalandı", category="Özel Durum",
        summary="Önemli Sözleşme İmzalandı", url="https://kap.org.tr/x", importance=kap.IMPORTANCE_HIGH,
        is_late=False, disclosure_index=1, stock_codes="TESTAS",
    )
    yorum = commentary._fallback_commentary(analiz, skor, [bildirim])
    assert yorum.kap_note is not None
    assert "Önemli Sözleşme İmzalandı" in yorum.kap_note


def test_fallback_commentary_kap_yoksa_not_none(saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    yorum = commentary._fallback_commentary(analiz, skor, [])
    assert yorum.kap_note is None


# --- generate_commentary: API anahtari yok -> dogrudan yedek mod -----------------------------------------------------


def test_generate_commentary_api_anahtari_yoksa_yedek_moda_duser(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert yorum.source == "fallback"
    assert yorum.headline
    assert yorum.summary


# --- generate_commentary: Gemini cagrisi sahtelenerek (monkeypatch) -----------------------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int, json_data: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> dict:
        return self._json_data


def _gemini_ok_payload(json_text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": json_text}]}}]}


def test_generate_commentary_basarili_llm_yanitini_dogrudan_kullanir(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    gecerli_json = (
        '{"headline": "KÂR GÜÇLÜ ARTTI", "hook": "Hasılat %20 arttı!", "summary": "Hasılat %20 arttı.", '
        '"positives": ["Hasılat %20 arttı"], "negatives": [], "kap_note": null, "disclaimer_context": null}'
    )
    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        return _FakeResponse(200, _gemini_ok_payload(gecerli_json))

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert call_count["n"] == 1
    assert yorum.source == "llm"
    assert yorum.headline == "KÂR GÜÇLÜ ARTTI"


def test_generate_commentary_bozuk_jsonda_duzeltme_istegi_gonderir_ve_basarili_olur(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    gecerli_json = '{"headline": "BAŞLIK", "hook": "Kanca.", "summary": "Özet.", "positives": [], "negatives": [], "kap_note": null, "disclaimer_context": null}'
    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _FakeResponse(200, _gemini_ok_payload("bu gecerli json degil {{{"))
        return _FakeResponse(200, _gemini_ok_payload(gecerli_json))

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert call_count["n"] == 2  # ilk deneme + JSON duzeltme istegi
    assert yorum.source == "llm"
    assert yorum.headline == "BAŞLIK"


def test_generate_commentary_supheli_artefaktta_duzeltme_ister_ve_temizlenirse_kullanir(monkeypatch, saglikli_analiz_ve_skor) -> None:
    # Canli gozlemlenen gercek hatanin regresyon testi: kap_note icine
    # sizan "(Wait, ...)" turu bir ic-ses artefakti tespit edilip BIR KEZ
    # duzeltme istegi gonderilmeli; ikinci yanit temizse kullanilmali.
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    supheli_json = (
        '{"headline": "BAŞLIK", "hook": "Kanca.", "summary": "Özet.", "positives": [], "negatives": [], '
        '"kap_note": "Şirket açıklama yaptı.————(Wait, let me reconsider this)————", "disclaimer_context": null}'
    )
    temiz_json = (
        '{"headline": "BAŞLIK", "hook": "Kanca.", "summary": "Özet.", "positives": [], "negatives": [], '
        '"kap_note": "Şirket açıklama yaptı.", "disclaimer_context": null}'
    )
    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        payload = supheli_json if call_count["n"] == 1 else temiz_json
        return _FakeResponse(200, _gemini_ok_payload(payload))

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert call_count["n"] == 2
    assert yorum.source == "llm"
    assert yorum.kap_note == "Şirket açıklama yaptı."
    assert "Wait" not in yorum.kap_note


def test_generate_commentary_duzeltmeden_sonra_da_supheliyse_yedek_moda_duser(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    supheli_json = (
        '{"headline": "BAŞLIK", "summary": "Özet.", "positives": [], "negatives": [], '
        '"kap_note": "————(Wait, hmm)————", "disclaimer_context": null}'
    )
    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        return _FakeResponse(200, _gemini_ok_payload(supheli_json))

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert call_count["n"] == 2  # ilk deneme + duzeltme istegi, sonra pes edildi
    assert yorum.source == "fallback"


def test_generate_commentary_kalici_401_hatasinda_yeniden_denemeden_yedek_moda_duser(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "gecersiz-anahtar")

    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        return _FakeResponse(401, text="yetkisiz")

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert call_count["n"] == 1  # kalici hata -- yeniden DENENMEDI
    assert yorum.source == "fallback"


def test_generate_commentary_kalici_ag_hatasinda_yeniden_deneyip_sonunda_yedek_moda_duser(monkeypatch, saglikli_analiz_ve_skor) -> None:
    analiz, skor = saglikli_analiz_ve_skor
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    # @retry'nin wait_fixed'i decorator uygulanirken (import aninda) config'ten okunmus
    # oldugu icin config'i sonradan degistirmenin etkisi yok; testi yavaslatmamak icin
    # zaten olusturulmus retry nesnesinin wait stratejisini dogrudan degistiriyoruz.
    monkeypatch.setattr(commentary._call_gemini_raw.retry, "wait", wait_fixed(0.01))

    call_count = {"n": 0}

    def fake_post(url, params=None, json=None, timeout=None):
        call_count["n"] += 1
        raise httpx.ConnectTimeout("zaman aşımı")

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary(analiz, skor, [])

    assert yorum.source == "fallback"
    assert call_count["n"] == 3  # 1 ilk deneme + 2 yeniden deneme (spec geregi)


# --- Teknik Görünüm yorumu (Faz 15.1, 2026-08-06) -----------------------------------


@pytest.fixture
def teknik_commentary_inputs() -> dict:
    """`technical_card.build_commentary_inputs()` çıktısıyla AYNI şekil --
    gerçek bir TechnicalSnapshot/Playwright gerektirmeden (Kural 11)."""
    return {
        "ticker": "THYAO",
        "price_display": "314,00 ₺",
        "indicator_groups": [
            {
                "title": "Trend",
                "rows": [
                    {"label": "SMA 200", "value_display": "270,00 ₺", "note_display": None, "note_class": None},
                    {"label": "ADX (14) — Trend Gücü", "value_display": "30,0", "note_display": "Güçlü Trend", "note_class": "extreme"},
                    {"label": "SMA50/200 Kesişimi", "value_display": "Altın Kesişim (Golden Cross)", "note_display": None, "note_class": "positive"},
                ],
            },
            {
                "title": "Momentum",
                "rows": [
                    {"label": "RSI (14)", "value_display": "75,0", "note_display": "Aşırı Alım Bölgesi", "note_class": "extreme"},
                ],
            },
        ],
        "week52_bar": {"has_data": True, "low_display": "230,00 ₺", "high_display": "340,00 ₺", "position_display": "%76,4"},
        "volume_strip": {"has_data": True, "last_volume_display": "18.000.000.000", "avg_volume_display": "15.000.000.000", "ratio_display": "%120,0"},
    }


def test_build_user_prompt_technical_al_sat_kelimeleri_gecmez(teknik_commentary_inputs) -> None:
    """İstem metninin KENDİSİ (LLM'e giden veri) yanlışlıkla 'al'/'sat'
    gibi bir tavsiye kelimesi İÇERMEMELİ -- sadece hazır etiket/sayılar."""
    prompt = commentary._build_user_prompt_technical(teknik_commentary_inputs)

    assert "THYAO" in prompt
    assert "Aşırı Alım Bölgesi" in prompt
    assert "Güçlü Trend" in prompt
    for yasakli in (" al ", " sat ", " tut ", "AL/SAT"):
        assert yasakli.lower() not in prompt.lower()


def test_sistem_instruction_technical_al_sat_yasagi_icerir() -> None:
    """K2 (Al/Sat/Tut sinyali üretilmez) kuralının teknik sistem isteminde
    de AÇIKÇA yer aldığını doğrular -- bu bir metin özelliği testi değil,
    projenin en kritik uyum kuralının regresyona karşı KİLİDİDİR."""
    assert "al" in commentary._SYSTEM_INSTRUCTION_TECHNICAL.lower()
    assert "yatirim tavsiyesi" in commentary._SYSTEM_INSTRUCTION_TECHNICAL.lower().replace("ı", "i")
    assert "hedef fiyat" in commentary._SYSTEM_INSTRUCTION_TECHNICAL.lower()


def test_fallback_commentary_technical_notlu_satirlardan_cumle_kurar(teknik_commentary_inputs) -> None:
    """'extreme' sınıfı (RSI/ADX bölge etiketi) YÖN BELİRTMEZ -- sadece
    özet anlatımına girer. 'positive'/'negative' (Golden/Death Cross gibi
    KESİN yönü olan olgular) ayrıca positives/negatives listelerine girer."""
    yorum = commentary._fallback_commentary_technical(teknik_commentary_inputs)

    assert yorum.source == "fallback"
    assert yorum.headline
    assert "Aşırı Alım Bölgesi" in yorum.summary
    assert "Güçlü Trend" in yorum.summary
    assert any("Altın Kesişim" in p for p in yorum.positives)
    assert yorum.negatives == []  # bu fixture'da "negative" sınıflı satır yok


def test_fallback_commentary_technical_notsuz_satirlarla_notr_ozet_doner() -> None:
    inputs = {
        "ticker": "THYAO",
        "price_display": "314,00 ₺",
        "indicator_groups": [
            {"title": "Trend", "rows": [{"label": "SMA 200", "value_display": "270,00 ₺", "note_display": None, "note_class": None}]}
        ],
        "week52_bar": {"has_data": False},
        "volume_strip": {"has_data": False},
    }
    yorum = commentary._fallback_commentary_technical(inputs)
    assert yorum.summary == "Göstergeler nötr/olağan aralıklarda seyrediyor."
    assert yorum.positives == []
    assert yorum.negatives == []


def test_generate_commentary_technical_api_anahtari_yoksa_yedek_moda_duser(monkeypatch, teknik_commentary_inputs) -> None:
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")

    yorum = commentary.generate_commentary_technical(teknik_commentary_inputs)

    assert yorum.source == "fallback"


def test_generate_commentary_technical_basarili_llm_yaniti_ayri_sistem_istemiyle_cagirir(monkeypatch, teknik_commentary_inputs) -> None:
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")

    gecerli_json = (
        '{"headline": "YUKARI EĞİLİMLİ", "hook": "Fiyat SMA200 üzerinde.", "summary": "Fiyat SMA200 üzerinde.", '
        '"positives": ["Güçlü trend"], "negatives": ["Aşırı alım bölgesi"], "kap_note": null, "disclaimer_context": null}'
    )
    captured = {}

    def fake_post(url, params=None, json=None, timeout=None):
        captured["system_instruction"] = json["systemInstruction"]["parts"][0]["text"]
        return _FakeResponse(200, _gemini_ok_payload(gecerli_json))

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary_technical(teknik_commentary_inputs)

    assert yorum.source == "llm"
    assert yorum.headline == "YUKARI EĞİLİMLİ"
    # AYRI sistem istemi (fundamental promptu DEGIL) kullanildigini dogrula:
    assert captured["system_instruction"] == commentary._SYSTEM_INSTRUCTION_TECHNICAL
    assert captured["system_instruction"] != commentary._SYSTEM_INSTRUCTION


def test_generate_commentary_technical_api_hatasinda_yedek_moda_duser(monkeypatch, teknik_commentary_inputs) -> None:
    monkeypatch.setattr(config, "GEMINI_API_KEY", "gecersiz-anahtar")

    def fake_post(url, params=None, json=None, timeout=None):
        return _FakeResponse(401, text="yetkisiz")

    monkeypatch.setattr(httpx, "post", fake_post)

    yorum = commentary.generate_commentary_technical(teknik_commentary_inputs)

    assert yorum.source == "fallback"
