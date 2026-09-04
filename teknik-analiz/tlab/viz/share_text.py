""""Paylaşım metni" — bir sembolü BİRDEN FAZLA göstergeyle (yapı raporu,
harmonik, golden zone, arz-talep, çift tepe/dip) tek seferde tarayıp,
`quant_report.py`nin AYNI "insan/quant sesi" LLM çekirdeğiyle X'te
paylaşılabilir TEK bir metin üreten üst-seviye fonksiyon.

2026-09-04 kullanıcı isteği: dashboard'daki mevcut "yapay zeka rapor"u
(`quant_report.py::generate_indicator_report`/`generate_quant_report`) BİR
göstergenin GRAFİĞİNİ zaten açmış olmayı gerektiriyor -- kullanıcı bunun
YERİNE yalnızca bir SEMBOL adı girip, sistemin O AN o sembol için ürettiği
ÇOKLU-gösterge taramasından tek bir paylaşılabilir metin isteyen, AYRI bir
akış istedi (bkz. INTEM için bu oturumda ELLE yapılan analiz -- bu modül o
iş akışını ÜRÜNLEŞTİRİYOR).

Mimari: her göstergenin OLGU listesi `report_text.py`nin ZATEN var olan
`build_summary_lines`/`build_generic_summary_lines`inden gelir (YENİ bir
hesap YOK) -- yalnızca birden fazla göstergenin olgu listesi BİRLEŞTİRİLİP
`quant_report.py::generate_from_facts` (AYNI LLM çekirdeği, AYNI anti-
yapay-zeka-sesi `SYSTEM_PROMPT`) ile tek bir metne dökülüyor."""

from __future__ import annotations

from tlab.viz.live import compute_live, compute_structure_report
from tlab.viz.quant_report import DEFAULT_PROVIDER, Provider, QuantReport, generate_from_facts
from tlab.viz.report_text import build_generic_summary_lines, build_summary_lines

# Faz 4a'nın harmonic.carney'iyle AYNI tarih -- burada yalnızca Carney
# taranıyor (8 ekolün TAMAMINI taramak yavaş VE facts listesini gereksiz
# şişirir; Carney en geniş formasyon kümesini kapsayan ekol, bkz. carney.py
# docstring'i). Kullanıcı ileride başka bir ekol/gösterge isterse
# `_SCAN_INDICATORS_4H`e eklemek yeterli.
_SCAN_INDICATORS_4H: tuple[str, ...] = (
    "harmonic.carney",
    "structure.golden_zone",
    "structure.supply_demand",
    "patterns.double_top_bottom",
)


def _section(title: str, lines: list[str]) -> list[str]:
    if not lines:
        return []
    return [f"[{title}]"] + lines


def build_share_facts(symbol: str, market: str = "bist") -> list[str]:
    """Sembolü tarayıp TEK bir birleşik olgu listesi döner -- `tlab plot`/
    web'in tek-gösterge akışından FARKLI olarak burada BİRDEN FAZLA
    göstergenin sonucu art arda toplanır. Bir gösterge sembolde hiç aday/
    sinyal üretmezse (ör. o an aktif bir harmonik yoksa) o bölüm sessizce
    ATLANIR -- LLM'e "böyle bir şey yok" diye uydurma bir olgu verilmez."""
    facts: list[str] = [
        "Bu olgular BİRDEN FAZLA farklı göstergeden (yapı raporu, harmonik, "
        "golden zone, arz-talep bölgeleri, çift tepe/dip) geliyor -- hepsini "
        "TEK bir sembolün farklı açılardan görünümü olarak birlikte yorumla."
    ]

    for tf in ("1D", "4H"):
        try:
            ps_result, sf_result, df = compute_structure_report(symbol, tf, market)
        except (ValueError, FileNotFoundError):
            continue
        lines = build_summary_lines(ps_result, sf_result, df)
        facts += _section(f"Yapı Raporu · {tf}", lines)

    for indicator in _SCAN_INDICATORS_4H:
        try:
            result, df = compute_live(indicator, symbol, "4H", market)
        except (ValueError, FileNotFoundError):
            continue
        if df is None:
            continue
        lines = build_generic_summary_lines(result, df)
        facts += _section(f"{indicator} · 4H", lines)

    return facts


def generate_share_text(
    symbol: str, market: str = "bist", *,
    provider: Provider = DEFAULT_PROVIDER, api_key: str | None = None, model: str | None = None,
) -> QuantReport:
    """`build_share_facts`i toplayıp `quant_report.py`nin AYNI LLM
    çekirdeğiyle (insan/quant sesi, X'te paylaşılabilir) tek bir metne
    dökülmüş hâlini döner. API anahtarı yoksa/çağrı başarısız olursa AYNI
    (deterministik madde listesine düşen) davranış -- `QuantReport.note`da
    açıklanır, sessiz hata YOK."""
    facts = build_share_facts(symbol, market)
    return generate_from_facts(facts, symbol, "bugün", provider, api_key, model)
