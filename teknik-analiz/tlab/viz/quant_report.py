"""LLM tabanlı "quant" rapor metni — grafiğin YANINDA, ayrı bir metin çıktısı.

2026-08-30: kullanıcı, grafiğin içine gömülen deterministik "Özet Raporu"
panelini (bkz. `report_text.py`) beğenmedi — "bir yapay zeka gibi değil bir
quant gibi" yazılmış, samimi, X (Twitter) üzerinde paylaşılabilecek SERBEST
METİN istedi; ayrıca bu metin artık GÖRSELİN DIŞINDA, grafikle birlikte
sunulan ayrı bir çıktı.

Mimari: `report_text.build_summary_lines()` (deterministik, LLM'siz) zaten
hesaplanmış OLGULARI kısa Türkçe madde cümlelerine çeviriyor — bu modül o
cümleleri LLM'e HAM GİRDİ olarak verir ("bu olguların DIŞINDA hiçbir sayı/
seviye UYDURMA" talimatıyla), LLM yalnızca bunları akıcı, açıklayıcı bir
anlatıya dökme işini yapar. Böylece "yeni bir indikatör hesabı" ortaya
çıkmaz — tüm sayısal içerik ZATEN var olan `IndicatorResult`'lardan gelir,
LLM yalnızca sunumu (biçimlendirmeyi) üstlenir.

API anahtarı yoksa veya çağrı başarısız olursa deterministik madde listesine
(uyarı notuyla) DÜŞÜLÜR — sessiz bir hata veya çökme YOK."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pandas as pd

from tlab.core.types import IndicatorResult
from tlab.viz.report_text import build_summary_lines

DEFAULT_MODEL = "claude-sonnet-5"
_MAX_TOKENS = 900

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
    `used_ai`: gerçek bir LLM çağrısıyla mı üretildi. `note`: `used_ai=False`
    iken NEDEN (eksik API anahtarı / API hatası) -- arayüz bunu kullanıcıya
    göstermeli, sessizce yutulmamalı."""

    text: str
    used_ai: bool
    note: str | None = None


def _fallback(facts: list[str], note: str) -> QuantReport:
    return QuantReport(text="\n".join(f"- {f}" for f in facts), used_ai=False, note=note)


def _build_user_message(symbol: str, date_str: str, facts: list[str]) -> str:
    facts_block = "\n".join(f"- {f}" for f in facts)
    return f"Sembol: {symbol}\nTarih: {date_str}\n\nOlgular:\n{facts_block}"


def generate_quant_report(
    ps_result: IndicatorResult,
    sf_result: IndicatorResult,
    df: pd.DataFrame,
    *,
    symbol: str | None = None,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
) -> QuantReport:
    """`ps_result`/`sf_result`: `structure.price_structure`/`structure.
    swing_fib_abcd`'in HAZIR çıktısı (bu fonksiyon hiçbir yeni hesap
    yapmaz). `api_key`: verilmezse `ANTHROPIC_API_KEY` ortam değişkeninden
    okunur. Anahtar yoksa ya da API çağrısı başarısız olursa deterministik
    madde listesine düşer (bkz. modül docstring'i)."""
    sym = symbol or ps_result.symbol or "?"
    facts = build_summary_lines(ps_result, sf_result, df)
    date_str = pd.Timestamp(df.index[-1]).strftime("%d.%m.%Y")

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return _fallback(
            facts, "ANTHROPIC_API_KEY tanımlı değil -- deterministik özet metnine düşüldü."
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key)
        message = client.messages.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_message(sym, date_str, facts)}],
        )
        text = "".join(
            block.text for block in message.content
            if isinstance(block, anthropic.types.TextBlock)
        ).strip()
        if not text:
            return _fallback(facts, "LLM boş yanıt döndü -- deterministik özet metnine düşüldü.")
        return QuantReport(text=text, used_ai=True)
    except Exception as exc:
        return _fallback(facts, f"LLM çağrısı başarısız ({exc}) -- deterministik özete düşüldü.")
