"""`tlab/viz/quant_report.py` için testler — gerçek bir API çağrısı YAPILMAZ
(ağ testleri varsayılan olarak dışlanır, bkz. `pyproject.toml`); `google.
genai.Client`/`anthropic.Anthropic` her zaman MOCK'lanır. Varsayılan
sağlayıcı Gemini'dir (kullanıcı Anthropic API kullanımını istemedi, bkz.
`quant_report.py` modül docstring'i) — testler önce Gemini yolunu (varsayılan
+ hata + başarı), sonra Anthropic'in HÂLÂ opsiyonel bir sağlayıcı olarak
çalıştığını doğrular."""

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
    """Test ortamında yanlışlıkla gerçek bir API anahtarı set edilmiş olsa
    bile testler her zaman `api_key` parametresini AÇIKÇA kontrol eder — bu
    fixture ilgili ortam değişkenlerini testler süresince temizler."""
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _results():
    df = make_trend(n=200, slope=0.1, noise=1.0)
    ps = PriceStructure(PriceStructureParams())(df)
    ps.symbol = "TEST"
    sf = SwingFibABCD(SwingFibABCDParams())(df)
    sf.symbol = "TEST"
    return ps, sf, df


# --- Gemini (varsayılan sağlayıcı) ------------------------------------------


def test_falls_back_to_deterministic_summary_without_api_key() -> None:
    ps, sf, df = _results()
    report = generate_quant_report(ps, sf, df, symbol="TEST", api_key=None)
    assert report.used_ai is False
    assert report.note is not None and "GEMINI_API_KEY" in report.note
    assert "Son Kapanış" in report.text  # report_text.build_summary_lines'ın ilk maddesi


def test_falls_back_when_gemini_call_raises() -> None:
    ps, sf, df = _results()
    with patch("google.genai.Client") as mock_cls:
        mock_cls.return_value.models.generate_content.side_effect = RuntimeError("bağlantı hatası")
        report = generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
    assert report.used_ai is False
    assert report.note is not None and "başarısız" in report.note
    assert "Son Kapanış" in report.text


def test_uses_gemini_text_when_call_succeeds() -> None:
    ps, sf, df = _results()
    fake_text = "TEST hissesi için samimi bir quant yorumu burada olurdu."
    mock_response = MagicMock()
    mock_response.text = fake_text
    with patch("google.genai.Client") as mock_cls:
        mock_cls.return_value.models.generate_content.return_value = mock_response
        report = generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
    assert report.used_ai is True
    assert report.provider == "gemini"
    assert report.note is None
    assert report.text == fake_text


def test_no_hallucinated_price_instruction_passed_to_gemini() -> None:
    """Prompt'un OLGULARDAN başka sayı uydurmama talimatını taşıdığını
    doğrular (regresyon: prompt kazayla silinirse/kısaltılırsa fark edilsin)."""
    ps, sf, df = _results()
    mock_response = MagicMock()
    mock_response.text = "ok"
    with patch("google.genai.Client") as mock_cls:
        mock_cls.return_value.models.generate_content.return_value = mock_response
        generate_quant_report(ps, sf, df, symbol="TEST", api_key="fake-key")
        _, kwargs = mock_cls.return_value.models.generate_content.call_args
    assert "UYDURMA" in kwargs["config"].system_instruction
    assert "Son Kapanış" in kwargs["contents"]


# --- Anthropic (opsiyonel, artık VARSAYILAN DEĞİL) --------------------------


def test_anthropic_still_works_as_explicit_opt_in() -> None:
    ps, sf, df = _results()
    fake_text = "Anthropic üzerinden üretilmiş bir metin."
    mock_message = MagicMock()
    mock_message.content = [anthropic.types.TextBlock(type="text", text=fake_text)]
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = mock_message
        report = generate_quant_report(
            ps, sf, df, symbol="TEST", provider="anthropic", api_key="fake-key"
        )
    assert report.used_ai is True
    assert report.provider == "anthropic"
    assert report.text == fake_text


def test_unknown_provider_raises() -> None:
    ps, sf, df = _results()
    with pytest.raises(ValueError, match="Bilinmeyen provider"):
        generate_quant_report(ps, sf, df, symbol="TEST", provider="openai")  # type: ignore[arg-type]
