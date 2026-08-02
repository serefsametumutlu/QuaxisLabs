"""Onceden HESAPLANMIS rakamlari Google Gemini API ile sozel yoruma cevirir.

KESIN ILKE: Bu modul HICBIR sayi hesaplamaz ve LLM'e ham finansal tablo
GONDERMEZ. Yalnizca calculator.AnalysisResult'in bulgular listesi (Finding),
rasyolari ve ceyreklik serisi; scorer.ScoreResult'in bilesen skorlari +
gerekceleri (skor motoru bunlari zaten Turkce f-string ile uretir); ve
onemli KAP bildirim basliklari -- hepsi ONCEDEN src.formatting ile Turkce
formatlanmis string olarak -- istem metnine gomulur. Sistem istemi acikca
"verilen sayilarin disinda hicbir sayi uretme" talimatini icerir.

API saglayicisi: Google Gemini (REST generateContent, structured JSON
cikti). Not: proje ilk tasarimda Anthropic Claude API'yi hedefliyordu;
kullanicinin acik tercihiyle bu modul Gemini'ye yazildi. Sozlesme (Commentary
veri modeli, retry sayisi, JSON guvenligi, LLM'siz yedek mod) saglayicidan
bagimsizdir -- ileride Claude'a gecmek istenirse sadece _call_gemini_raw
fonksiyonu degistirilir.

Hata/yedek mod stratejisi:
  1. GEMINI_API_KEY tanimli degilse dogrudan LLM'siz yedek moda gecilir.
  2. Ag hatasi / zaman asimi / rate limit (HTTP 429, 5xx) -> 2 kez yeniden
     denenir (toplam 3 deneme). Kalici hatalarda (401, 400 vb.) hemen
     birakilir.
  3. Yanit gecerli JSON degilse (kod bloğu isaretleri temizlendikten sonra
     bile) VEYA alan degerlerinde supheli bir metin artefakti (canli
     gozlemlendi: modelin kendi kendine Ingilizce bir "dusunme notunu"
     bir alanin icine sizdirmasi, orn. "(Wait, ...)") tespit edilirse BIR
     KEZ "sadece gecerli JSON dondur" duzeltme istemi gonderilir.
  4. Yukaridakilerin tumu basarisiz olursa LLM'siz, bulgular listesinden
     sablonla uretilen mekanik bir ozete (Commentary.source="fallback")
     duser. Bu fonksiyon hicbir kosulda exception firlatmaz veya bos
     donmez.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

import config
from src.analysis import calculator, scorer
from src.fetchers import kap
from src.formatting import format_currency_short, format_number_tr, format_percent_tr

logger = logging.getLogger(__name__)

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


# --- Hata siniflari (modul ici, disariya sizmaz -- generate_commentary hep Commentary doner) ------------


class _RetryableLLMError(Exception):
    """Gecici hata (baglanti, zaman asimi, HTTP 429/5xx) -- yeniden denenebilir."""


class _NonRetryableLLMError(Exception):
    """Kalici hata (yetkilendirme, gecersiz istek, beklenmeyen yanit bicimi)."""


# --- Veri modeli -----------------------------------------------------


@dataclass(frozen=True)
class Commentary:
    headline: str
    summary: str
    positives: list[str]
    negatives: list[str]
    kap_note: str | None
    disclaimer_context: str | None
    source: str  # "llm" | "fallback" -- kart render katmani bunu gorup istege bagli kucuk bir not ekleyebilir


# --- Sistem istemi + JSON semasi -----------------------------------------------------

_SYSTEM_INSTRUCTION = """Sen bir BIST (Borsa Istanbul) temel analiz platformu icin calisan profesyonel bir \
finansal analistsin. Sana bir sirketin ONCEDEN HESAPLANMIS finansal degisim/oran/puanlama \
verileri ve varsa onemli KAP bildirim basliklari verilecek.

KESIN KURALLAR:
1. SANA VERILEN SAYILARIN DISINDA HICBIR SAYI URETME, HESAPLAMA YAPMA. Yeni bir yuzde, \
oran, tutar veya toplam TURETME; sadece verilen sayilari OLDUGU GIBI (yuzde isareti, \
virgullu ondalik formatiyla) aktar.
2. Yatirim tavsiyesi VERME; "al", "sat", "tut", hedef fiyat, potansiyel getiri gibi \
ifadeler KULLANMA.
3. Abartili/sansasyonel dilden kacin; profesyonel bir analist uslubu kullan. Emoji kullanma.
4. Tum metin TURKCE olacak.
5. "Zarardan kara gecti" veya "kara karsin zarar acikladi" gibi ozel gecis etiketleri \
varsa, bunlari ozette ve baslikta ONCELIKLENDIR -- bunlar en onemli sinyaldir.
6. Yalniz asagidaki JSON semasina uyan gecerli JSON dondur; baska hicbir aciklama, \
markdown kod blogu isareti veya ek metin EKLEME.
7. Alan degerlerinin ICINE kendi kendine not, taslak duzeltmesi, Ingilizce meta-yorum \
veya parantez ici ic ses YAZMA (orn. "(Wait, ...)", "(let me reconsider)" gibi ifadeler \
KESINLIKLE YASAK). Her alan sadece nihai, temiz, yayina hazir Turkce metni icermeli.
8. "YoY", "QoQ", "MoM" gibi Ingilizce finansal kisaltmalari KULLANMA; bunlarin yerine \
"yillik bazda", "ceyreklik bazda" gibi Turkce ifadeler kullan.
9. Turkce'ye ozgu harfleri (ı, ğ, ü, ş, ö, ç ve buyukleri İ, Ğ, Ü, Ş, Ö, Ç) HER ZAMAN \
DOGRU kullan -- "yillik" degil "yıllık", "artis" degil "artış", "sirket" degil "şirket", \
"ozkaynak" degil "özkaynak" yaz. ASCII'ye indirgenmis (Turkce harf ATLANMIS) kelimeler \
KESINLIKLE YASAK.

JSON semasi:
{
  "headline": "en fazla 8 kelime, BUYUK HARF, carpici ama abartisiz tek cumlelik baslik",
  "summary": "3-5 cumlelik acilis paragrafi, en onemli 2-3 gelismeyi sayilarla anlatir",
  "positives": ["en fazla 4 madde, her biri sayi icermeli"],
  "negatives": ["en fazla 4 madde, her biri sayi icermeli"],
  "kap_note": "onemli KAP bildirimi varsa 1-2 cumlelik not, yoksa null",
  "disclaimer_context": null
}"""

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "headline": {"type": "STRING"},
        "summary": {"type": "STRING"},
        "positives": {"type": "ARRAY", "items": {"type": "STRING"}},
        "negatives": {"type": "ARRAY", "items": {"type": "STRING"}},
        "kap_note": {"type": "STRING", "nullable": True},
        "disclaimer_context": {"type": "STRING", "nullable": True},
    },
    "required": ["headline", "summary", "positives", "negatives"],
}

_JSON_FIX_INSTRUCTION = (
    "Onceki yanitin gecerli JSON olarak ayristirilamadi. SADECE gecerli JSON dondur; "
    "aciklama, kod blogu isareti veya JSON disinda hicbir metin ekleme."
)


# --- Istem metni insasi (SADECE onceden hesaplanmis, formatlanmis degerler) ------------


def _format_finding(f: calculator.Finding, currency_symbol: str = "₺") -> str:
    # CANLI GOZLEMLENDI (kullanici raporu): istem metnine "(YoY)"/"(QoQ)" gibi
    # Ingilizce kisaltmalar gomulunce, LLM bunlari ARA SIRA kendi Turkce
    # ciktisina (artislar/azalislar maddelerine) DA sizdiriyordu. Bu yuzden
    # istem metninde de TURKCE karsiligi ("Yillik"/"Ceyreklik") kullanilir --
    # kok neden (LLM'in gordugu terim) duzeltilir, sadece cikti temizlenmez.
    donem_tr = "Yıllık" if f.comparison == "YoY" else "Çeyreklik"
    mevcut = format_currency_short(f.current, symbol=currency_symbol) if f.current is not None else "-"
    onceki = format_currency_short(f.previous, symbol=currency_symbol) if f.previous is not None else "-"
    if f.percent_change is not None:
        degisim = f"{format_percent_tr(f.percent_change)} {f.change_label}"
    else:
        degisim = f.change_label
    return f"- {f.label_tr} ({donem_tr}): güncel {mevcut}, önceki {onceki} -> {degisim}"


def _format_ratios(r: calculator.Ratios) -> list[str]:
    def pct(v):
        return format_percent_tr(v) if v is not None else "veri yok"

    def pts(v):
        return f"{format_number_tr(v, decimals=1)} puan" if v is not None else "veri yok"

    def mult(v):
        return f"{format_number_tr(v, decimals=2)}x" if v is not None else "veri yok"

    return [
        f"- Brüt kâr marjı: güncel {pct(r.gross_margin_current)} (önceki yıl {pct(r.gross_margin_prior_year)}, "
        f"değişim {pts(r.gross_margin_change_points)})",
        f"- FAVÖK marjı: güncel {pct(r.ebitda_margin_current)} (önceki yıl {pct(r.ebitda_margin_prior_year)}, "
        f"değişim {pts(r.ebitda_margin_change_points)})",
        f"- Net kâr marjı: güncel {pct(r.net_margin_current)} (önceki yıl {pct(r.net_margin_prior_year)}, "
        f"değişim {pts(r.net_margin_change_points)})",
        f"- Net borç/FAVÖK (TTM): {mult(r.net_debt_to_ebitda)}",
        f"- Cari oran: {mult(r.current_ratio)}",
        f"- Özkaynak kârlılığı (yıllıklandırılmış): {pct(r.roe_annualized)}",
        f"- Borç/özkaynak: {mult(r.debt_to_equity)}",
    ]


def _format_quarterly_series(series: list[calculator.QuarterlySeriesPoint], currency_symbol: str = "₺") -> list[str]:
    if not series:
        return []

    def seri(getter):
        return " -> ".join(
            format_currency_short(getter(p), symbol=currency_symbol) if getter(p) is not None else "-" for p in series
        )

    return [
        f"- Satışlar (son {len(series)} çeyrek, eskiden yeniye): {seri(lambda p: p.revenue)}",
        f"- FAVÖK (son {len(series)} çeyrek): {seri(lambda p: p.ebitda)}",
        f"- Net Kâr (son {len(series)} çeyrek): {seri(lambda p: p.net_income)}",
    ]


def _format_score(score: scorer.ScoreResult) -> list[str]:
    lines = [f"Toplam puan: {format_number_tr(score.total_score, decimals=1)} / 10 -- Rozet: {score.badge}"]
    for c in score.components:
        if c.score is None:
            lines.append(f"- {c.name}: veri yok ({c.reasoning_tr})")
        else:
            lines.append(
                f"- {c.name}: {format_number_tr(c.score, decimals=1)}/10 "
                f"(ağırlık %{format_number_tr(c.weight_effective, decimals=0)}) -- {c.reasoning_tr}"
            )
    return lines


def _format_disclosures(disclosures: list[kap.Disclosure], limit: int = 5) -> list[str]:
    onemli = [d for d in disclosures if d.importance == kap.IMPORTANCE_HIGH][:limit]
    return [f"- {d.date.strftime('%d.%m.%Y')} [{d.category}] {d.title}" for d in onemli]


def _format_ratios_bank(r: calculator.BankRatios) -> list[str]:
    def pct(v):
        return format_percent_tr(v) if v is not None else "veri yok"

    return [
        f"- Net faiz marjı (TTM net faiz geliri / güncel toplam varlık, YAKLAŞIK): {pct(r.net_interest_margin_current)}",
        f"- Net kâr marjı (net kâr / faiz geliri): {pct(r.net_margin_current)}",
        f"- Özkaynak kârlılığı (yıllıklandırılmış): {pct(r.roe_annualized)}",
    ]


def _format_quarterly_series_bank(series: list[calculator.BankQuarterlySeriesPoint]) -> list[str]:
    if not series:
        return []

    def seri(getter):
        return " -> ".join(format_currency_short(getter(p)) if getter(p) is not None else "-" for p in series)

    return [
        f"- Net Faiz Geliri (son {len(series)} çeyrek, eskiden yeniye): {seri(lambda p: p.net_interest_income)}",
        f"- Net Kâr (son {len(series)} çeyrek): {seri(lambda p: p.net_income)}",
        f"- Krediler (son {len(series)} çeyrek): {seri(lambda p: p.loans)}",
    ]


def _build_user_prompt_bank(
    analysis: calculator.BankAnalysisResult, score: scorer.ScoreResult, disclosures: list[kap.Disclosure]
) -> str:
    period_str = f"{analysis.latest_period[0]}/Ç{analysis.latest_period[1] // 3}"
    parts = [f"Hisse: {analysis.ticker} (BANKA)  Dönem: {period_str}", "", "## Hesaplanmış Değişim Bulguları (Yıllık/Çeyreklik)"]
    parts += [_format_finding(f) for f in analysis.findings]

    parts += ["", "## Rasyolar"]
    parts += _format_ratios_bank(analysis.ratios)

    seri_lines = _format_quarterly_series_bank(analysis.quarterly_series)
    if seri_lines:
        parts += ["", "## Çeyreklik Seri (Trend)"] + seri_lines

    parts += ["", "## Puanlama"]
    parts += _format_score(score)

    disclosure_lines = _format_disclosures(disclosures)
    parts += ["", "## Önemli KAP Bildirimleri (son dönem)"]
    parts += disclosure_lines if disclosure_lines else ["(Önemli bildirim yok.)"]

    return "\n".join(parts)


def _format_ratios_insurance(r: calculator.InsuranceRatios) -> list[str]:
    def pct(v):
        return format_percent_tr(v) if v is not None else "veri yok"

    return [
        f"- Teknik denge marjı (teknik denge / teknik gelir): {pct(r.technical_balance_margin_current)}",
        f"- Prim üretimi yıllık büyümesi: {pct(r.premium_growth_yoy_pct)}",
        f"- Özkaynak kârlılığı (yıllıklandırılmış): {pct(r.roe_annualized)}",
    ]


def _format_quarterly_series_insurance(series: list[calculator.InsuranceQuarterlySeriesPoint]) -> list[str]:
    if not series:
        return []

    def seri(getter):
        return " -> ".join(format_currency_short(getter(p)) if getter(p) is not None else "-" for p in series)

    return [
        f"- Prim Üretimi (son {len(series)} çeyrek, eskiden yeniye): {seri(lambda p: p.gross_written_premiums)}",
        f"- Teknik Denge (son {len(series)} çeyrek): {seri(lambda p: p.technical_balance)}",
        f"- Net Kâr (son {len(series)} çeyrek): {seri(lambda p: p.net_income)}",
    ]


def _build_user_prompt_insurance(
    analysis: calculator.InsuranceAnalysisResult, score: scorer.ScoreResult, disclosures: list[kap.Disclosure]
) -> str:
    period_str = f"{analysis.latest_period[0]}/Ç{analysis.latest_period[1] // 3}"
    parts = [f"Hisse: {analysis.ticker} (SİGORTA)  Dönem: {period_str}", "", "## Hesaplanmış Değişim Bulguları (Yıllık/Çeyreklik)"]
    parts += [_format_finding(f) for f in analysis.findings]

    parts += ["", "## Rasyolar"]
    parts += _format_ratios_insurance(analysis.ratios)

    seri_lines = _format_quarterly_series_insurance(analysis.quarterly_series)
    if seri_lines:
        parts += ["", "## Çeyreklik Seri (Trend)"] + seri_lines

    parts += ["", "## Puanlama"]
    parts += _format_score(score)

    disclosure_lines = _format_disclosures(disclosures)
    parts += ["", "## Önemli KAP Bildirimleri (son dönem)"]
    parts += disclosure_lines if disclosure_lines else ["(Önemli bildirim yok.)"]

    return "\n".join(parts)


def _build_user_prompt(analysis: calculator.AnalysisResult, score: scorer.ScoreResult, disclosures: list[kap.Disclosure]) -> str:
    # Faz 10 (NASDAQ/ABD): analysis.currency ("TRY"|"USD", bkz.
    # calculator.AnalysisResult.currency) LLM'e gonderilen ozet metnindeki
    # para birimi sembolunu belirler -- aksi halde ABD sirketleri icin
    # (analyze_us()) Gemini'ye YANLISLIKLA "₺" iceren rakamlar gonderilir,
    # LLM bunu kendi Turkce ozetine SIZDIRABILIR (bkz. _format_finding ust
    # notundaki "sizma" hatasi ile AYNI risk sinifi).
    currency_symbol = "$" if analysis.currency == "USD" else "₺"
    period_str = f"{analysis.latest_period[0]}/Ç{analysis.latest_period[1] // 3}"
    parts = [f"Hisse: {analysis.ticker}  Dönem: {period_str}", "", "## Hesaplanmış Değişim Bulguları (Yıllık/Çeyreklik)"]
    parts += [_format_finding(f, currency_symbol) for f in analysis.findings]

    parts += ["", "## Rasyolar"]
    parts += _format_ratios(analysis.ratios)

    seri_lines = _format_quarterly_series(analysis.quarterly_series, currency_symbol)
    if seri_lines:
        parts += ["", "## Çeyreklik Seri (Trend)"] + seri_lines

    parts += ["", "## Puanlama"]
    parts += _format_score(score)

    disclosure_lines = _format_disclosures(disclosures)
    parts += ["", "## Önemli KAP Bildirimleri (son dönem)"]
    parts += disclosure_lines if disclosure_lines else ["(Önemli bildirim yok.)"]

    return "\n".join(parts)


# --- Gemini HTTP katmani -----------------------------------------------------


@retry(
    reraise=True,
    stop=stop_after_attempt(3),  # 1 ilk deneme + 2 yeniden deneme
    wait=wait_fixed(config.HTTP_RATE_LIMIT_DELAY_SECONDS),
    retry=retry_if_exception_type(_RetryableLLMError),
)
def _call_gemini_raw(contents: list[dict]) -> str:
    """Tek bir Gemini generateContent cagrisi yapar, yanit metnini (JSON string
    olmasi beklenir) doner. Ag/zaman asimi/429/5xx hatalarinda _RetryableLLMError
    firlatir (tenacity bunu yakalayip yeniden dener); diger hatalarda
    _NonRetryableLLMError firlatir (yeniden denenmez)."""
    url = f"{_GEMINI_BASE_URL}/{config.GEMINI_MODEL}:generateContent"
    body = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": _SYSTEM_INSTRUCTION}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": _RESPONSE_SCHEMA,
            "temperature": 0.4,
        },
    }

    try:
        response = httpx.post(
            url,
            params={"key": config.GEMINI_API_KEY},
            json=body,
            timeout=config.GEMINI_TIMEOUT_SECONDS,
        )
    except httpx.RequestError as exc:
        logger.warning("Gemini istegi basarisiz (bağlantı/zaman aşımı), yeniden denenecek: %s", exc)
        raise _RetryableLLMError(str(exc)) from exc

    if response.status_code == 429 or response.status_code >= 500:
        logger.warning("Gemini geçici hata döndürdü (HTTP %s), yeniden denenecek.", response.status_code)
        raise _RetryableLLMError(f"HTTP {response.status_code}")
    if response.status_code != 200:
        raise _NonRetryableLLMError(
            f"Gemini beklenmeyen HTTP durum kodu döndürdü: {response.status_code} - {response.text[:300]}"
        )

    payload = response.json()
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise _NonRetryableLLMError(f"Gemini yanıtı beklenmeyen biçimde: {payload}") from exc


def _clean_json_text(text: str) -> str:
    """Model bazen (responseSchema'ya ragmen) markdown kod blogu isaretleri
    ekleyebilir; bunlari temizler."""
    return _CODE_FENCE_RE.sub("", text).strip()


def _parse_json_response(text: str) -> dict | None:
    try:
        return json.loads(_clean_json_text(text))
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Gemini yanıtı geçerli JSON değil: %s", exc)
        return None


# Canli bir Gemini yanitinda gozlemlendi: model kap_note alaninin icine
# "————(Wait, Turkish characters inside JSON string are valid UTF-8, ...)————"
# turunde kendi kendine bir Ingilizce dusunme notu sizdirmisti. Bu kaliplar
# mesru Turkce finansal metinde pratikte hic gecmez (dusuk yanlis pozitif
# riski): 3+ ardisik tire/em-dash, ya da Ingilizce ic-ses kelimeleri.
#
# AYRICA canli gozlemlendi (kullanici raporu, TERA): model bazen Turkce
# harfleri (ı/ğ/ü/ş/ö/ç) ATLAYIP ASCII'ye indirgenmis kelimeler uretiyor
# ("Satislar yillik bazda" -- "Satışlar yıllık bazda" yerine). Asagidaki
# liste, dogru yaziminda MUTLAKA bir Turkce harf tasiyan VE bu projenin
# bilanco/finansal rapor baglaminda sik gecen kok kelimelerin ASCII'ye
# indirgenmis halidir -- baska hicbir mesru Turkce kelimeyle CAKISMAYACAK
# sekilde secildi (dusuk yanlis pozitif riski, "kari"/"kar" gibi belirsiz
# kokler KASITLI olarak listeye ALINMADI).
#
# ONEMLI: bu regex re.IGNORECASE KULLANMAZ -- CANLI DOGRULANAN Python
# gotcha'si: re.IGNORECASE, Unicode kural katlama (case folding) nedeniyle
# Turkce noktasiz 'ı' harfini ASCII 'i' ile ESLESTIRIYOR (re.search(r"i",
# "ı", re.IGNORECASE) -> MATCH!) -- bu da IGNORECASE ile doğru yazılmış
# "yıllık" gibi kelimelerin YANLIŞLIKLA "yillik" deseniyle eslesmesine
# (yanlis pozitif) yol aciyordu. Kucuk harfli kok + kucuk harfli devami
# (\w*, Unicode-farkinda) yeterli -- gercek LLM ciktisi normal cumle
# icinde kucuk harfle gecer.
_ASCII_DEGRADED_TR_RE = re.compile(
    r"\b(yillik|ceyreklik|artis\w*|azalis\w*|dusus\w*|ozkaynak\w*|sirket\w*|donem\w*|"
    r"guclu\b|duzey\w*|varlik\w*|borc\w*|gercek\w*|yukselis\w*|buyume\w*|olcek\w*)\b"
)

_SUSPICIOUS_ARTIFACT_RE = re.compile(r"-{3,}|—{2,}|\bwait\b|\bhmm\b|\blet'?s\b", re.IGNORECASE)


def _contains_suspicious_artifact(data: dict) -> bool:
    """data icindeki tum string/list-of-string alanlarda supheli bir metin
    artefakti (bkz. _SUSPICIOUS_ARTIFACT_RE) VEYA ASCII'ye indirgenmis
    Turkce (bkz. _ASCII_DEGRADED_TR_RE) var mi kontrol eder. Iki regex AYRI
    tutulur (birlestirilemez) -- ikincisi re.IGNORECASE KULLANMAMALI (bkz.
    kendi docstring'i, ı/i case-folding hatasi)."""
    for value in data.values():
        candidates = value if isinstance(value, list) else [value]
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            if _SUSPICIOUS_ARTIFACT_RE.search(candidate) or _ASCII_DEGRADED_TR_RE.search(candidate):
                return True
    return False


def _commentary_from_json(data: dict, source: str) -> Commentary:
    headline = str(data.get("headline") or "").strip()
    summary = str(data.get("summary") or "").strip()
    if not headline or not summary:
        raise _NonRetryableLLMError("Gemini yanıtı zorunlu alanları (headline/summary) içermiyor.")

    positives = [str(x).strip() for x in (data.get("positives") or []) if str(x).strip()][:4]
    negatives = [str(x).strip() for x in (data.get("negatives") or []) if str(x).strip()][:4]
    kap_note_raw = data.get("kap_note")
    kap_note = str(kap_note_raw).strip() if kap_note_raw else None
    disclaimer_raw = data.get("disclaimer_context")
    disclaimer_context = str(disclaimer_raw).strip() if disclaimer_raw else None

    return Commentary(
        headline=headline,
        summary=summary,
        positives=positives,
        negatives=negatives,
        kap_note=kap_note,
        disclaimer_context=disclaimer_context,
        source=source,
    )


def _call_llm_and_parse(user_prompt: str) -> Commentary:
    """Gemini'yi cagirir, JSON'u ayristirir; parse basarisiz olursa VEYA
    icerik supheli bir artefakt tasiyorsa (bkz. _contains_suspicious_artifact)
    BIR KEZ duzeltme istemi gonderir. Herhangi bir asamada kalici hata
    olursa exception firlatir (cagiran taraf yedek moda duser)."""
    contents = [{"role": "user", "parts": [{"text": user_prompt}]}]
    raw_text = _call_gemini_raw(contents)

    data = _parse_json_response(raw_text)
    if data is None or _contains_suspicious_artifact(data):
        if data is None:
            logger.warning("Gemini yanıtı parse edilemedi, düzeltme isteği gönderiliyor.")
        else:
            logger.warning("Gemini yanıtında şüpheli bir metin artefaktı tespit edildi, düzeltme isteği gönderiliyor.")
        contents = [
            {"role": "user", "parts": [{"text": user_prompt}]},
            {"role": "model", "parts": [{"text": raw_text}]},
            {"role": "user", "parts": [{"text": _JSON_FIX_INSTRUCTION}]},
        ]
        raw_text = _call_gemini_raw(contents)
        data = _parse_json_response(raw_text)
        if data is not None and _contains_suspicious_artifact(data):
            logger.warning("Düzeltme isteğinden sonra da şüpheli artefakt sürüyor, yanıta güvenilmeyecek.")
            data = None

    if data is None:
        raise _NonRetryableLLMError("Gemini yanıtı düzeltme isteğinden sonra da geçerli/temiz JSON'a çevrilemedi.")

    return _commentary_from_json(data, source="llm")


# --- LLM'siz yedek mod -----------------------------------------------------


_OZEL_GECIS_ETIKETLERI = (calculator.ChangeLabel.ZARARDAN_KARA_GECTI, calculator.ChangeLabel.KARA_KARSIN_ZARAR)


def _fallback_sentence(f: calculator.Finding) -> str:
    donem = "yıllık" if f.comparison == "YoY" else "çeyreklik"
    if f.percent_change is not None:
        return f"{f.label_tr} {donem} %{format_number_tr(abs(f.percent_change), decimals=1)} {f.change_label}."
    return f"{f.label_tr} {f.change_label}."


def _oncelik_anahtari(f: calculator.Finding) -> int:
    """Zarardan kara / kardan zarara gecis bulgularini 0 (en onde), digerlerini
    1 dondurur. sorted() kararli oldugu icin ayni gruptaki sira korunur --
    boylece 4 maddelik sinirlarda ozel gecis etiketleri asla kirpilmaz."""
    return 0 if f.change_label in _OZEL_GECIS_ETIKETLERI else 1


def _fallback_commentary(analysis: calculator.AnalysisResult, score: scorer.ScoreResult, disclosures: list[kap.Disclosure]) -> Commentary:
    """LLM'siz, tamamen sablon tabanli mekanik ozet. calculator.AnalysisResult'in
    findings listesindeki hazir yuzde/etiketlerden cumle kurar; hicbir sayi
    hesaplamaz, sadece bicimlendirir. Zarardan kara / kardan zarara gecis
    bulgulari -- LLM istemindeki 5. kural ile ayni ilkeyle -- her zaman
    onceliklendirilir (bkz. _oncelik_anahtari)."""
    anlamli_bulgular = [f for f in analysis.findings if f.change_label != calculator.ChangeLabel.VERI_YOK]
    oncelikli_sirali = sorted(anlamli_bulgular, key=_oncelik_anahtari)

    summary = " ".join(_fallback_sentence(f) for f in oncelikli_sirali[:4])
    if not summary:
        summary = "Bu dönem için yeterli karşılaştırma verisi bulunmuyor."

    positives = [_fallback_sentence(f) for f in oncelikli_sirali if f.direction == "artis"][:4]
    negatives = [_fallback_sentence(f) for f in oncelikli_sirali if f.direction == "azalis"][:4]

    onemli_kap = [d for d in disclosures if d.importance == kap.IMPORTANCE_HIGH]
    kap_note = (
        f"Son dönemde {len(onemli_kap)} önemli KAP bildirimi bulunuyor; en yenisi: {onemli_kap[0].title}."
        if onemli_kap
        else None
    )

    headline = f"PUAN {format_number_tr(score.total_score, decimals=1)}/10 -- {score.badge}"

    return Commentary(
        headline=headline,
        summary=summary,
        positives=positives,
        negatives=negatives,
        kap_note=kap_note,
        disclaimer_context=None,
        source="fallback",
    )


# --- Ana giris noktasi -----------------------------------------------------


def generate_commentary(
    analysis: calculator.AnalysisResult,
    score: scorer.ScoreResult,
    disclosures: list[kap.Disclosure],
) -> Commentary:
    """calculator/scorer'in hazir sayilarindan Gemini API ile sozel yorum
    uretir. GEMINI_API_KEY tanimli degilse veya API cagrisi (retry'lardan
    sonra da) basarisiz olursa, HICBIR ISTISNA FIRLATMADAN LLM'siz sablon
    tabanli yedek moda duser -- bu fonksiyon her zaman bir Commentary doner.
    """
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY tanımlı değil, LLM'siz yedek moda geçildi.")
        return _fallback_commentary(analysis, score, disclosures)

    user_prompt = _build_user_prompt(analysis, score, disclosures)
    try:
        return _call_llm_and_parse(user_prompt)
    except Exception as exc:  # Gemini/ag/parse hatalarinin tumu -- bot asla bos donmemeli
        logger.warning("LLM yorum üretimi başarısız (%s), LLM'siz yedek moda geçiliyor.", exc)
        return _fallback_commentary(analysis, score, disclosures)


def generate_commentary_bank(
    analysis: calculator.BankAnalysisResult,
    score: scorer.ScoreResult,
    disclosures: list[kap.Disclosure],
) -> Commentary:
    """generate_commentary()'nin banka (UFRS) karsiligi -- ayni saglamlik
    garantisi (LLM'siz yedek moda dusme) gecerlidir. _fallback_commentary
    SADECE analysis.findings kullanir (Finding, sektore gore DEGISMEZ,
    calculator.BankAnalysisResult'ta da ayni tiptedir) -- bu yuzden yedek
    mod fonksiyonu DEGISTIRILMEDEN yeniden kullanilir; sadece LLM istem
    metni (_build_user_prompt_bank, banka rasyolari/seri) farklidir."""
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY tanımlı değil, LLM'siz yedek moda geçildi.")
        return _fallback_commentary(analysis, score, disclosures)

    user_prompt = _build_user_prompt_bank(analysis, score, disclosures)
    try:
        return _call_llm_and_parse(user_prompt)
    except Exception as exc:
        logger.warning("LLM yorum üretimi başarısız (%s), LLM'siz yedek moda geçiliyor.", exc)
        return _fallback_commentary(analysis, score, disclosures)


def generate_commentary_insurance(
    analysis: calculator.InsuranceAnalysisResult,
    score: scorer.ScoreResult,
    disclosures: list[kap.Disclosure],
) -> Commentary:
    """generate_commentary()'nin sigorta (UFRS_K) karsiligi -- ayni saglamlik
    garantisi gecerlidir; _fallback_commentary SADECE analysis.findings
    kullandigi icin (sektorden BAGIMSIZ) degistirilmeden yeniden kullanilir."""
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY tanımlı değil, LLM'siz yedek moda geçildi.")
        return _fallback_commentary(analysis, score, disclosures)

    user_prompt = _build_user_prompt_insurance(analysis, score, disclosures)
    try:
        return _call_llm_and_parse(user_prompt)
    except Exception as exc:
        logger.warning("LLM yorum üretimi başarısız (%s), LLM'siz yedek moda geçiliyor.", exc)
        return _fallback_commentary(analysis, score, disclosures)
