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

**DÜRÜST NOT -- model adları:** `DEFAULT_GEMINI_MODEL`/`DEFAULT_ANTHROPIC_
MODEL` bu kod yazılırken (2026-08-30) bilinen model kimlikleridir. LLM
sağlayıcılarının model adları zamanla değişir/kullanımdan kalkar -- gerçek
kullanımdan önce Google AI Studio'nun (Gemini) veya Anthropic Console'un
GÜNCEL model listesinden doğrulanmalı, gerekirse `--model` ile override
edilebilir.

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
from tlab.viz.report_text import build_summary_lines

Provider = Literal["gemini", "anthropic"]

DEFAULT_PROVIDER: Provider = "gemini"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_MAX_OUTPUT_TOKENS = 900

_SYSTEM_PROMPT = """\
Sen deneyimli bir kantitatif analist (quant) ve piyasa yorumcususun. Sana bir \
hissenin teknik analiz çıktıları -- zaten hesaplanmış, sana OLGU olarak \
verilen sayılar -- iletiliyor. Bu olgulardan, sosyal medyada (X/Twitter) \
paylaşılabilecek, samimi ama profesyonel bir Türkçe rapor metni yaz.

Kesin kurallar:
1. SANA VERİLEN olguların DIŞINDA hiçbir fiyat, seviye, yüzde veya tarih \
UYDURMA -- yalnızca verilenleri kullan, yorumla, bağlamlandır.
2. Bir yapay zeka gibi değil, gerçek bir insan-quant gibi yaz: doğal, akıcı, \
kendine güvenen ama abartısız bir üslup. Kalıp/şablon cümlelerden kaçın.
3. Teknik terimleri (POC, VAH/VAL, RSI, AB=CD, HVN, Fibonacci, MACD vb.) \
kullanırken KISACA ne anlama geldiğini parantez içinde veya cümle içinde \
açıkla -- konuya hakim olmayan biri de okuyunca anlamalı.
4. Kesinlikle "AL/SAT" tavsiyesi verme; yalnızca teknik görünümü anlat. \
Metnin SONUNA "Yalnızca teknik analizdir, yatırım tavsiyesi değildir." \
notunu ekle.
5. Uzunluk: yaklaşık 150-280 kelime. Kısa alt başlıklar kullanabilirsin \
ama zorunlu değil -- doğal bir anlatı da olabilir.
6. Türkçe yaz."""


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
    return (response.text or "").strip()


def _call_anthropic(user_message: str, api_key: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=_MAX_OUTPUT_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(
        block.text for block in message.content
        if isinstance(block, anthropic.types.TextBlock)
    ).strip()


_PROVIDERS: dict[Provider, tuple[tuple[str, ...], str, object]] = {
    "gemini": (("GEMINI_API_KEY", "GOOGLE_API_KEY"), DEFAULT_GEMINI_MODEL, _call_gemini),
    "anthropic": (("ANTHROPIC_API_KEY",), DEFAULT_ANTHROPIC_MODEL, _call_anthropic),
}


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
    if provider not in _PROVIDERS:
        raise ValueError(f"Bilinmeyen provider: {provider!r} (gemini|anthropic bekleniyor)")
    env_names, default_model, call = _PROVIDERS[provider]

    sym = symbol or ps_result.symbol or "?"
    facts = build_summary_lines(ps_result, sf_result, df)
    date_str = pd.Timestamp(df.index[-1]).strftime("%d.%m.%Y")
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
