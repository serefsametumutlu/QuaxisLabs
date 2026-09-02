"""LLM tabanlı "quant" rapor metni — grafiğin YANINDA, ayrı bir metin çıktısı.

2026-08-30: kullanıcı, grafiğin içine gömülen deterministik "Özet Raporu"
panelini (bkz. `report_text.py`) beğenmedi — "bir yapay zeka gibi değil bir
quant gibi" yazılmış, samimi, X (Twitter) üzerinde paylaşılabilecek SERBEST
METİN istedi; ayrıca bu metin artık GÖRSELİN DIŞINDA, grafikle birlikte
sunulan ayrı bir çıktı.

**Sağlayıcı seçimi (2026-08-30, ikinci düzeltme):** kullanıcı Anthropic
(Claude) API'sini KULLANMAK İSTEMEDİ -- "Claude haklarımın buraya gitmesini
istemiyorum" (Claude Code/Claude.ai aboneliğiyle KARIŞTIRILMAMASI gereken,
ayrı/pay-per-token bir Anthropic Console hesabı gerektirse de, kullanıcı
bilinçli olarak tüm kullanımını Anthropic ekosistemi DIŞINDA tutmak istedi).
GitHub Copilot değerlendirildi ama Copilot'un genel amaçlı bir "kendi
uygulamandan çağır" tarzı ucuz/basit bir tamamlama API'si YOK (esas olarak
editör/ajan entegrasyonları için) -- bu kullanım şekline uygun değil.
Varsayılan sağlayıcı artık **Google Gemini** (`GEMINI_API_KEY`/
`GOOGLE_API_KEY` ortam değişkeni, gerçekten ücretsiz bir kotası var, Türkçe
desteği iyi). Anthropic YİNE DE bir seçenek olarak (`provider="anthropic"`)
BIRAKILDI -- kod SİLİNMEDİ, yalnızca artık varsayılan DEĞİL; kullanıcı
isterse elle geçebilir.

**Model seçimi:** `DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"` --
sabit bir sürüm DEĞİL, Google'ın "-latest" takma adı (model güncellendikçe
otomatik takip eder, elle güncelleme gerekmez). `gemini-flash-latest`
(lite OLMAYAN) YERİNE bilinçli olarak seçildi: kullanıcının kendi
`bilanco-radar` projesinde (AYNI API anahtarıyla, farklı bir uygulama)
CANLI doğrulandı -- `flash-latest`'in günlük kotası çok hızlı tükeniyor,
`flash-lite-latest` AYRI ve daha yüksek bir kotaya sahip (bkz. `bilanco-
radar/config.py` yorumu). Anthropic yolu için `DEFAULT_ANTHROPIC_MODEL`
bu kod yazılırken (2026-08-30) bilinen bir model kimliğidir -- LLM
sağlayıcılarının model adları zamanla değişir, gerekirse `--model` ile
override edilebilir.

Mimari: `report_text.build_summary_lines()` (deterministik, LLM'siz) zaten
hesaplanmış OLGULARI kısa Türkçe madde cümlelerine çeviriyor -- bu modül o
cümleleri LLM'e HAM GİRDİ olarak verir ("bu olguların DIŞINDA hiçbir sayı/
seviye UYDURMA" talimatıyla), LLM yalnızca bunları akıcı, açıklayıcı bir
anlatıya dökme işini yapar. Böylece "yeni bir indikatör hesabı" ortaya
çıkmaz -- tüm sayısal içerik ZATEN var olan `IndicatorResult`'lardan gelir,
LLM yalnızca sunumu (biçimlendirmeyi) üstlenir.

API anahtarı yoksa veya çağrı başarısız olursa deterministik madde listesine
(uyarı notuyla) DÜŞÜLÜR -- sessiz bir hata veya çökme YOK."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.report_text import (
    build_generic_summary_lines,
    build_pair_summary_lines,
    build_summary_lines,
)

Provider = Literal["gemini", "anthropic"]

DEFAULT_PROVIDER: Provider = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
# 2026-09-03: kullanıcı "şimdiye kadar olduğundan daha detaylı ve uzun rapor
# yazsın" dedi -- eski 900 token ~250-300 Türkçe kelimeyle sınırlıyordu
# (sistem promptunun eski 150-280 kelime hedefiyle tutarlıydı ama kullanıcı
# artık BUNU yetersiz buluyor). 2200 token, aşağıdaki 450-750 kelimelik yeni
# hedefe rahat yer bırakır.
_MAX_OUTPUT_TOKENS = 2200

_SYSTEM_PROMPT = """\
Sen borsada yıllarını geçirmiş, deneyimli bir kantitatif analistsin (quant) \
-- hem sayılara hem de piyasanın "hissine" hakim, X/Twitter'da finans \
çevresinde takip edilen, teknik konuları sıradan bir yatırımcının bile \
anlayacağı dilde anlatabilen biri gibisin. Sana bir hissenin/stratejinin \
teknik analiz çıktıları -- zaten hesaplanmış, sana OLGU olarak verilen \
sayılar -- iletiliyor. Bu olgulardan, X'te paylaşılabilecek, samimi ama \
otoriter bir Türkçe rapor metni yaz.

Kesin kurallar:
1. SANA VERİLEN olguların DIŞINDA hiçbir fiyat, seviye, yüzde veya tarih \
UYDURMA -- yalnızca verilenleri kullan, yorumla, bağlamlandır. Verilen HER \
olguyu (özellikle sinyal geçmişi, z-skor, getiri/drawdown gibi istatistik \
alanları varsa) metne dahil etmeye çalış, hiçbirini görmezden gelme.
2. Bir yapay zeka gibi değil, gerçek bir insan-quant gibi yaz: doğal, akıcı, \
kendine güvenen ama abartısız bir üslup. Kalıp/şablon cümlelerden ("gördüğümüz \
üzere", "sonuç olarak" gibi klişelerden) kaçın; gerçek biri konuşuyormuş gibi, \
akışı olan bir anlatı kur -- neden bu seviyenin/oranın önemli olduğunu, bir \
sonraki adımda ne izleneceğini de kendi yorumunla açıkla.
3. Teknik terimleri (POC, VAH/VAL, RSI, AB=CD, HVN, Fibonacci, z-skor, \
kointegrasyon, halflife, MACD vb.) kullanırken KISACA ne anlama geldiğini \
parantez içinde veya cümle içinde açıkla -- konuya hakim olmayan biri de \
okuyunca anlamalı. Bunu her terimde otomatik/şablon gibi değil, doğal bir \
açıklama cümlesi olarak yap.
4. Kesinlikle "AL/SAT" tavsiyesi verme; yalnızca teknik görünümü anlat. \
Metnin SONUNA "Yalnızca teknik analizdir, yatırım tavsiyesi değildir." \
notunu ekle.
5. Uzunluk: yaklaşık 450-750 kelime -- önceki kısa özet metinlerden BELİRGİN \
şekilde daha detaylı ve uzun olmalı. Tek bir kısa paragraf YETERSİZ; en az \
3-5 doğal paragraf kullan (giriş/genel görünüm, detaylı teknik okuma, \
istatistik/performans bağlamı varsa ayrı bir paragraf, kapanış/özet).
6. DÜZ METİN yaz -- markdown biçimlendirmesi KULLANMA (**kalın**, *madde \
işareti*, # başlık gibi işaretler YASAK). Bu metin X/Twitter'da OLDUĞU GİBİ \
paylaşılacak; markdown işaretleri orada düz yıldız/diyez karakteri olarak \
görünür, biçimlendirme OLARAK görünmez. Vurgu için kelime seçimini kullan, \
işaretleme değil. Paragrafları BOŞ SATIRLA ayır.
7. Türkçe yaz."""


@dataclass(frozen=True)
class QuantReport:
    """`text`: nihai rapor metni (LLM ile ya da fallback ile üretilmiş).
    `used_ai`: gerçek bir LLM çağrısıyla mı üretildi. `provider`: `used_ai`
    iken hangi sağlayıcı kullanıldı. `note`: `used_ai=False` iken NEDEN
    (eksik API anahtarı / API hatası) -- arayüz bunu kullanıcıya
    göstermeli, sessizce yutulmamalı."""

    text: str
    used_ai: bool
    provider: Provider | None = None
    note: str | None = None


def _fallback(facts: list[str], note: str) -> QuantReport:
    return QuantReport(text="\n".join(f"- {f}" for f in facts), used_ai=False, note=note)


def _build_user_message(symbol: str, date_str: str, facts: list[str]) -> str:
    facts_block = "\n".join(f"- {f}" for f in facts)
    return f"Sembol: {symbol}\nTarih: {date_str}\n\nOlgular:\n{facts_block}"


def _strip_markdown_fence(text: str) -> str:
    """Model, `_SYSTEM_PROMPT`'un düz metin talimatına RAĞMEN yanıtı bir
    ```markdown kod bloğuna sarabiliyor (kullanıcının `bilanco-radar`
    projesinde AYNI API'yle canlı gözlemlenen bir davranış, bkz. `commentary.
    py::_clean_json_text`) -- burada aynı savunma tekrarlanır."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[: -3]
    return stripped.strip()


def _call_gemini(user_message: str, api_key: str, model: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT, max_output_tokens=_MAX_OUTPUT_TOKENS,
        ),
    )
    return _strip_markdown_fence(response.text or "")


def _call_anthropic(user_message: str, api_key: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=_MAX_OUTPUT_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    text = "".join(
        block.text for block in message.content
        if isinstance(block, anthropic.types.TextBlock)
    )
    return _strip_markdown_fence(text)


_PROVIDERS: dict[Provider, tuple[tuple[str, ...], str, object]] = {
    "gemini": (("GEMINI_API_KEY", "GOOGLE_API_KEY"), DEFAULT_GEMINI_MODEL, _call_gemini),
    "anthropic": (("ANTHROPIC_API_KEY",), DEFAULT_ANTHROPIC_MODEL, _call_anthropic),
}


def _generate_from_facts(
    facts: list[str], sym: str, date_str: str, provider: Provider,
    api_key: str | None, model: str | None,
) -> QuantReport:
    """`generate_quant_report`/`generate_indicator_report`'un PAYLAŞTIĞI
    LLM-çağrısı çekirdeği -- ikisi de yalnızca farklı bir `build_*_summary_
    lines()` ile olgu listesi ürettikten sonra buraya düşer."""
    if provider not in _PROVIDERS:
        raise ValueError(f"Bilinmeyen provider: {provider!r} (gemini|anthropic bekleniyor)")
    env_names, default_model, call = _PROVIDERS[provider]
    user_message = _build_user_message(sym, date_str, facts)

    key = api_key or next((os.environ[n] for n in env_names if os.environ.get(n)), None)
    if not key:
        env_list = "/".join(env_names)
        return _fallback(
            facts, f"{env_list} tanımlı değil -- deterministik özet metnine düşüldü."
        )

    try:
        text = call(user_message, key, model or default_model)  # type: ignore[operator]
        if not text:
            return _fallback(facts, "LLM boş yanıt döndü -- deterministik özet metnine düşüldü.")
        return QuantReport(text=text, used_ai=True, provider=provider)
    except Exception as exc:
        return _fallback(facts, f"LLM çağrısı başarısız ({exc}) -- deterministik özete düşüldü.")


def generate_quant_report(
    ps_result: IndicatorResult,
    sf_result: IndicatorResult,
    df: pd.DataFrame,
    *,
    symbol: str | None = None,
    provider: Provider = DEFAULT_PROVIDER,
    api_key: str | None = None,
    model: str | None = None,
) -> QuantReport:
    """`ps_result`/`sf_result`: `structure.price_structure`/`structure.
    swing_fib_abcd`'in HAZIR çıktısı (bu fonksiyon hiçbir yeni hesap
    yapmaz). `api_key`: verilmezse sağlayıcının kendi ortam değişkeninden
    (Gemini için `GEMINI_API_KEY`/`GOOGLE_API_KEY`, Anthropic için
    `ANTHROPIC_API_KEY`) okunur. Anahtar yoksa ya da API çağrısı başarısız
    olursa deterministik madde listesine düşer (bkz. modül docstring'i)."""
    sym = symbol or ps_result.symbol or "?"
    facts = build_summary_lines(ps_result, sf_result, df)
    date_str = pd.Timestamp(df.index[-1]).strftime("%d.%m.%Y")
    return _generate_from_facts(facts, sym, date_str, provider, api_key, model)


def generate_indicator_report(
    result: IndicatorResult,
    df: pd.DataFrame,
    *,
    symbol: str | None = None,
    provider: Provider = DEFAULT_PROVIDER,
    api_key: str | None = None,
    model: str | None = None,
) -> QuantReport:
    """2026-09-02: `structure.report` DIŞINDAKİ herhangi bir gösterge için
    genel amaçlı AI rapor yolu -- `report_text.build_generic_summary_lines()`
    (o göstergeye özel bir olgu-çıkarıcı YAZMADAN, her `IndicatorResult`'ın
    ortak alanlarından üretilen dürüst/genel olgular) + AYNI LLM çekirdeği
    (`_generate_from_facts`). `generate_quant_report`'un `structure.report`e
    özel zengin yolu bu fonksiyonla DEĞİŞTİRİLMEDİ, ayrı kalmaya devam
    ediyor -- dashboard hangi göstergenin seçili olduğuna göre ikisinden
    birini çağırır (bkz. `tlab/dashboard.py::_render_ai_report_button`)."""
    sym = symbol or result.symbol or "?"
    facts = build_generic_summary_lines(result, df)
    date_str = pd.Timestamp(df.index[-1]).strftime("%d.%m.%Y")
    return _generate_from_facts(facts, sym, date_str, provider, api_key, model)


def generate_pair_report(
    result: IndicatorResult,
    *,
    symbol: str | None = None,
    provider: Provider = DEFAULT_PROVIDER,
    api_key: str | None = None,
    model: str | None = None,
) -> QuantReport:
    """2026-09-03: `pair.relative_momentum`/`pair.vol_harvest` için AI rapor
    yolu -- kullanıcı "pair göstergeleri için yapay zeka desteklenmiyor"
    bildirdi. Kök neden: bu ikisi `compute_live()`'da tekil bir OHLCV `df`
    DÖNDÜRMÜYOR (pair modunda anlamı yok, bkz. `live.py`), `generate_
    indicator_report`'un `df["close"]` bağımlılığına uymuyordu. Burada `df`
    YOK -- tarih referansı olarak `result.series['z']`'nin (varsa) ya da
    son sinyalin `bar_time`'ı kullanılır."""
    sym = symbol or result.symbol or "?"
    facts = build_pair_summary_lines(result)
    date_source = result.series.get("z")
    if date_source is not None and len(date_source):
        date_str = pd.Timestamp(date_source.index[-1]).strftime("%d.%m.%Y")
    elif result.signals:
        date_str = pd.Timestamp(
            max(result.signals, key=lambda s: s.detected_at).bar_time
        ).strftime("%d.%m.%Y")
    else:
        date_str = "bugün"
    return _generate_from_facts(facts, sym, date_str, provider, api_key, model)
