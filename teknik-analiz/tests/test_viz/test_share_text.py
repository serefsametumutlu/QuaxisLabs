"""`tlab/viz/share_text.py` için testler — `compute_structure_report`/
`compute_live` ve `generate_from_facts` her zaman MOCK'lanır (ağ çağrısı YOK,
gerçek Store/cache verisi gerektirmez). Amaç: `build_share_facts`'in birden
fazla gösterge/zaman diliminin olgu listesini doğru şekilde birleştirdiğini
ve hiç aday üretmeyen bir göstergenin bölümünü sessizce atladığını, ayrıca
`generate_share_text`'in bu birleşik listeyi AYNEN `quant_report.py`'nin
paylaşılan LLM çekirdeğine ilettiğini doğrulamak."""

from __future__ import annotations

from unittest.mock import patch

from tlab.viz.quant_report import QuantReport
from tlab.viz.share_text import (
    _SCAN_INDICATORS_4H,
    _section,
    build_share_facts,
    generate_share_text,
)


def test_section_returns_empty_list_for_no_lines() -> None:
    assert _section("Başlık", []) == []


def test_section_prefixes_title() -> None:
    assert _section("Yapı Raporu · 1D", ["a", "b"]) == ["[Yapı Raporu · 1D]", "a", "b"]


def test_build_share_facts_includes_intro_and_all_sections() -> None:
    with (
        patch("tlab.viz.share_text.compute_structure_report") as mock_structure,
        patch("tlab.viz.share_text.compute_live") as mock_live,
        patch("tlab.viz.share_text.build_summary_lines", return_value=["yapı olgusu"]),
        patch("tlab.viz.share_text.build_generic_summary_lines", return_value=["gösterge olgusu"]),
    ):
        mock_structure.return_value = (object(), object(), object())
        mock_live.return_value = (object(), object())
        facts = build_share_facts("TEST", "bist")

    assert "farklı gösterge" in facts[0]
    assert "[Yapı Raporu · 1D]" in facts
    assert "[Yapı Raporu · 4H]" in facts
    assert "yapı olgusu" in facts
    assert "gösterge olgusu" in facts
    for indicator in _SCAN_INDICATORS_4H:
        assert f"[{indicator} · 4H]" in facts
    # 2 TF x (1 başlık + 1 olgu) + 4 gösterge x (1 başlık + 1 olgu) + 1 giriş
    assert facts.count("yapı olgusu") == 2
    assert facts.count("gösterge olgusu") == len(_SCAN_INDICATORS_4H)


def test_build_share_facts_skips_section_when_indicator_raises() -> None:
    """Bir gösterge sembolde hiç aday/veri üretmezse (ValueError/
    FileNotFoundError) o bölüm sessizce atlanır -- LLM'e uydurma bir olgu
    verilmez."""
    with (
        patch(
            "tlab.viz.share_text.compute_structure_report",
            side_effect=ValueError("desteklenmiyor"),
        ),
        patch("tlab.viz.share_text.compute_live", side_effect=FileNotFoundError("veri yok")),
    ):
        facts = build_share_facts("TEST", "bist")

    assert len(facts) == 1  # yalnızca giriş cümlesi kaldı
    assert all("[" not in f for f in facts)


def test_build_share_facts_skips_indicator_when_df_is_none() -> None:
    with (
        patch(
            "tlab.viz.share_text.compute_structure_report",
            side_effect=ValueError("desteklenmiyor"),
        ),
        patch("tlab.viz.share_text.compute_live", return_value=(object(), None)),
    ):
        facts = build_share_facts("TEST", "bist")

    assert len(facts) == 1


def test_generate_share_text_passes_combined_facts_to_llm_core() -> None:
    fake_facts = ["giriş", "[Yapı Raporu · 1D]", "olgu"]
    fake_report = QuantReport(
        text="paylaşılabilir metin", used_ai=True, provider="gemini", note=None
    )
    with (
        patch(
            "tlab.viz.share_text.build_share_facts", return_value=fake_facts
        ) as mock_build,
        patch(
            "tlab.viz.share_text.generate_from_facts", return_value=fake_report
        ) as mock_generate,
    ):
        report = generate_share_text("TEST", "bist", api_key="fake-key")

    mock_build.assert_called_once_with("TEST", "bist")
    args, _ = mock_generate.call_args
    assert args[0] == fake_facts
    assert args[1] == "TEST"
    assert report is fake_report
