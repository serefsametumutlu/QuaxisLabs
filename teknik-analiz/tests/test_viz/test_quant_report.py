"""`tlab/viz/quant_report.py` için testler — gerçek bir API çağrısı YAPILMAZ
(ağ testleri varsayılan olarak dışlanır, bkz. `pyproject.toml`); `anthropic.
Anthropic` her zaman MOCK'lanır. Üç yol doğrulanır: API anahtarı yok
(fallback), API çağrısı başarısız (fallback), API çağrısı başarılı (LLM
metni aynen döner)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import anthropic
import pytest

from tlab.indicators.structure.price_structure import PriceStructure, PriceStructureParams
from tlab.indicators.structure.swing_fib_abcd import SwingFibABCD, SwingFibABCDParams
from tlab.testing.fixtures import make_trend
from tlab.viz.quant_report import generate_quant_report


@pytest.fixture(autouse=True)
def _no_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test ortamında yanlışlıkla gerçek bir `ANTHROPIC_API_KEY` set edilmiş
    olsa bile testler her zaman `api_key` parametresini AÇIKÇA kontrol eder —
    bu fixture ortam değişkenini testler süresince temizler."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _results():
    df = make_trend(n=200, slope=0.1, noise=1.0)
    ps = PriceStructure(PriceStructureParams())(df)
    ps.symbol = "TEST"
    sf = SwingFibABCD(SwingFibABCDParams())(df)
    sf.symbol = "TEST"
    return ps, sf, df


def test_falls_back_to_deterministic_summary_without_api_key() -> None:
    ps, sf, df = _results()
    report = generate_quant_report(ps, sf, df, symbol="TEST", api_key=None)
    assert report.used_ai is False
    assert report.note is not None and "ANTHROPIC_API_KEY" in report.note
    assert "Son Kapanış" in report.text  # report_text.build_summary_lines'ın ilk maddesi


def test_falls_back_when_api_call_raises() -> None:
    ps, sf, df = _results()
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = RuntimeError("bağlantı hatası")
        report = generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
    assert report.used_ai is False
    assert report.note is not None and "başarısız" in report.note
    assert "Son Kapanış" in report.text


def test_uses_llm_text_when_call_succeeds() -> None:
    ps, sf, df = _results()
    fake_text = "TEST hissesi için samimi bir quant yorumu burada olurdu."
    mock_message = MagicMock()
    mock_message.content = [anthropic.types.TextBlock(type="text", text=fake_text)]
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = mock_message
        report = generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
    assert report.used_ai is True
    assert report.note is None
    assert report.text == fake_text


def test_no_hallucinated_price_instruction_passed_to_llm() -> None:
    """Prompt'un OLGULARDAN başka sayı uydurmama talimatını taşıdığını
    doğrular (regresyon: prompt kazayla silinirse/kısaltılırsa fark edilsin)."""
    ps, sf, df = _results()
    mock_message = MagicMock()
    mock_message.content = [anthropic.types.TextBlock(type="text", text="ok")]
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = mock_message
        generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
        _, kwargs = mock_cls.return_value.messages.create.call_args
    assert "UYDURMA" in kwargs["system"]
    assert "Son Kapanış" in kwargs["messages"][0]["content"]
